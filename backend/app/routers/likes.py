from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.error_record import ErrorRecord
from app.models.like import Like
from app.models.study import Study
from app.models.user import User
from app.routers.comments import get_public_parent
from app.services.auth import get_current_user

# 좋아요는 공개된 공부 기록과 오류 기록에만 누를 수 있다. 할 일에는 좋아요 경로 자체가 없다.
router = APIRouter(tags=["likes"])


class LikeState(BaseModel):
    liked: bool  # 내가 좋아요를 눌렀는지
    like_count: int  # 전체 좋아요 수


def _target(model, record_id: int):
    column = Like.study_id if model is Study else Like.error_id
    return column == record_id


def _state(db: Session, model, record_id: int, user: User) -> LikeState:
    count = db.scalar(select(func.count()).select_from(Like).where(_target(model, record_id)))
    mine = db.scalar(select(Like.id).where(_target(model, record_id), Like.user_id == user.id))
    return LikeState(liked=mine is not None, like_count=count or 0)


def _register(prefix: str, model) -> None:
    field = "study_id" if model is Study else "error_id"

    @router.get(f"/api/{prefix}/{{record_id}}/like", response_model=LikeState, name=f"get_{prefix}_like")
    def get_like(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        get_public_parent(db, model, record_id)  # 비공개 기록의 좋아요는 숨겨진다.
        return _state(db, model, record_id, user)

    @router.put(f"/api/{prefix}/{{record_id}}/like", response_model=LikeState, name=f"add_{prefix}_like")
    def add_like(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """좋아요를 누른다. 이미 눌렀다면 그대로 둔다. (같은 사용자의 중복 저장은 불가능)"""
        get_public_parent(db, model, record_id)
        already = db.scalar(select(Like.id).where(_target(model, record_id), Like.user_id == user.id))
        if already is None:
            db.add(Like(user_id=user.id, **{field: record_id}))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()  # 거의 동시에 눌러서 이미 저장된 경우
        return _state(db, model, record_id, user)

    @router.delete(f"/api/{prefix}/{{record_id}}/like", response_model=LikeState, name=f"remove_{prefix}_like")
    def remove_like(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """내 좋아요를 취소한다. 남의 좋아요는 건드리지 않는다."""
        get_public_parent(db, model, record_id)
        mine = db.scalar(select(Like).where(_target(model, record_id), Like.user_id == user.id))
        if mine is not None:
            db.delete(mine)
            db.commit()
        return _state(db, model, record_id, user)


_register("studies", Study)
_register("errors", ErrorRecord)
