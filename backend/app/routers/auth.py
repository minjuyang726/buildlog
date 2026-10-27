from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import FieldErrors
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, NicknameUpdateRequest, SignupRequest, UserOut
from app.services.auth import COOKIE_NAME, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_TAKEN = "이미 가입된 이메일입니다. 다른 이메일을 입력해 주세요."
NICKNAME_TAKEN = "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요."
LOGIN_FAILED = "로그인 정보가 맞지 않습니다."

# 없는 이메일로 로그인을 시도할 때도 비밀번호 확인과 비슷한 시간이 걸리게 하기 위한 값
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def _conflict(errors: dict[str, str]) -> FieldErrors:
    return FieldErrors(status.HTTP_409_CONFLICT, errors)


def _taken_errors(db: Session, email: str | None, nickname: str, own_id: int | None = None) -> dict[str, str]:
    errors: dict[str, str] = {}
    if email is not None and db.scalar(select(User.id).where(User.email == email)) is not None:
        errors["email"] = EMAIL_TAKEN
    owner = db.scalar(select(User.id).where(User.nickname == nickname))
    if owner is not None and owner != own_id:
        errors["nickname"] = NICKNAME_TAKEN
    return errors


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)) -> User:
    errors = _taken_errors(db, data.email, data.nickname)
    if errors:
        raise _conflict(errors)
    user = User(email=data.email, password_hash=hash_password(data.password), nickname=data.nickname)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 거의 동시에 같은 값으로 가입한 경우를 위한 마지막 방어선
        db.rollback()
        raise _conflict(_taken_errors(db, data.email, data.nickname) or {"email": EMAIL_TAKEN})
    return user


@router.post("/login", response_model=UserOut)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == data.email))
    password_ok = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_FAILED)
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,  # 화면의 스크립트가 읽을 수 없게 한다.
        samesite="lax",
        secure=settings.app_env != "development",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, httponly=True, samesite="lax", secure=settings.app_env != "development")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me/nickname", response_model=UserOut)
def change_nickname(
    data: NicknameUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    errors = _taken_errors(db, None, data.nickname, own_id=user.id)
    if errors:
        raise _conflict(errors)
    user.nickname = data.nickname
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflict({"nickname": NICKNAME_TAKEN})
    return user
