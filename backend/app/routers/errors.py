from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import FieldErrors
from app.db.session import get_db
from app.models.common import utcnow
from app.models.error_record import ErrorRecord
from app.models.user import User
from app.schemas.error_record import SOLUTION_REQUIRED, ErrorFilter, ErrorIn, ErrorList, ErrorListItem, ErrorOut
from app.services.auth import get_current_user
from app.services.permissions import escape_like, get_owned, get_visible

router = APIRouter(prefix="/api/errors", tags=["errors"])

PREVIEW_LENGTH = 100


def to_out(record: ErrorRecord, db: Session, user: User) -> ErrorOut:
    author = user if record.user_id == user.id else db.get(User, record.user_id)
    return ErrorOut(
        id=record.id,
        title=record.title,
        content=record.content,
        solution=record.solution,
        is_resolved=record.is_resolved,
        is_public=record.is_public,
        created_at=record.created_at,
        updated_at=record.updated_at,
        resolved_at=record.resolved_at,
        author_nickname=author.nickname,
        is_mine=record.user_id == user.id,
    )


def apply_state(record: ErrorRecord, data: ErrorIn) -> None:
    """해결 여부를 반영한다. 해결 방법 없이는 해결 상태로 바꿀 수 없다.

    미해결로 되돌릴 때 해결 방법은 그대로 두고 해결 날짜·시간만 지운다.
    """
    if data.is_resolved and not data.solution:
        raise FieldErrors(422, {"solution": SOLUTION_REQUIRED})
    record.solution = data.solution
    if data.is_resolved:
        record.mark_resolved()
    else:
        record.mark_unresolved()


@router.post("", response_model=ErrorOut, status_code=status.HTTP_201_CREATED)
def create_error(data: ErrorIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = ErrorRecord(user_id=user.id, title=data.title, content=data.content, is_public=data.is_public)
    apply_state(record, data)
    db.add(record)
    db.commit()
    return to_out(record, db, user)


@router.get("", response_model=ErrorList)
def list_my_errors(
    filter: ErrorFilter = Query(default="all"),
    q: str = Query(default="", max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 오류 기록 목록. 최근에 작성한 기록부터, 해결 상태 필터와 제목·오류 내용 검색을 지원한다."""
    query = select(ErrorRecord).where(ErrorRecord.user_id == user.id)
    if filter == "unresolved":
        query = query.where(ErrorRecord.is_resolved.is_(False))
    elif filter == "resolved":
        query = query.where(ErrorRecord.is_resolved.is_(True))
    keyword = q.strip()
    if keyword:
        pattern = f"%{escape_like(keyword)}%"
        query = query.where(
            or_(ErrorRecord.title.ilike(pattern, escape="\\"), ErrorRecord.content.ilike(pattern, escape="\\"))
        )
    records = db.scalars(query.order_by(ErrorRecord.created_at.desc(), ErrorRecord.id.desc())).all()
    return ErrorList(
        items=[
            ErrorListItem(
                id=r.id,
                title=r.title,
                preview=r.content[:PREVIEW_LENGTH],
                is_resolved=r.is_resolved,
                is_public=r.is_public,
                created_at=r.created_at,
                updated_at=r.updated_at,
                resolved_at=r.resolved_at,
            )
            for r in records
        ]
    )


@router.get("/{error_id}", response_model=ErrorOut)
def read_error(error_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_out(get_visible(db, ErrorRecord, error_id, user), db, user)


@router.put("/{error_id}", response_model=ErrorOut)
def update_error(
    error_id: int,
    data: ErrorIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_owned(db, ErrorRecord, error_id, user)
    apply_state(record, data)  # 실패하면 아래 값을 바꾸기 전에 거절된다.
    record.title = data.title
    record.content = data.content
    record.is_public = data.is_public
    record.updated_at = utcnow()
    db.commit()
    return to_out(record, db, user)


@router.delete("/{error_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_error(error_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    record = get_owned(db, ErrorRecord, error_id, user)
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
