from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.error_record import ErrorRecord
from app.models.study import Study
from app.models.todo import Todo
from app.models.user import User
from app.schemas.public import PublicItem, PublicKind, PublicList
from app.services.auth import get_current_user
from app.services.permissions import escape_like

router = APIRouter(prefix="/api/public", tags=["public"])

PREVIEW_LENGTH = 100


def _matches(columns, keyword: str):
    pattern = f"%{escape_like(keyword)}%"
    return or_(*[column.ilike(pattern, escape="\\") for column in columns])


def _public_rows(db: Session, model, keyword: str, search_columns):
    """공개로 설정된 기록만 가져온다. 비공개 기록은 이 조건 때문에 어디서도 섞이지 않는다."""
    query = select(model, User.nickname).join(User, User.id == model.user_id).where(model.is_public.is_(True))
    if keyword:
        query = query.where(_matches(search_columns, keyword))
    return db.execute(query).all()


@router.get("", response_model=PublicList)
def list_public(
    kind: PublicKind = Query(default="all"),
    q: str = Query(default="", max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """다른 사용자도 볼 수 있게 공개된 기록을 최근 작성순으로 보여준다.

    검색 대상: 공부 기록은 제목·내용, 할 일은 제목, 오류 기록은 오류 제목·오류 내용·해결 방법.
    """
    keyword = q.strip()
    items: list[PublicItem] = []

    if kind in ("all", "study"):
        for study, nickname in _public_rows(db, Study, keyword, [Study.title, Study.content]):
            items.append(
                PublicItem(
                    kind="study",
                    id=study.id,
                    title=study.title,
                    preview=study.content[:PREVIEW_LENGTH],
                    author_nickname=nickname,
                    is_mine=study.user_id == user.id,
                    created_at=study.created_at,
                )
            )
    if kind in ("all", "todo"):
        for todo, nickname in _public_rows(db, Todo, keyword, [Todo.title]):
            items.append(
                PublicItem(
                    kind="todo",
                    id=todo.id,
                    title=todo.title,
                    preview=None,
                    author_nickname=nickname,
                    is_mine=todo.user_id == user.id,
                    created_at=todo.created_at,
                    is_done=todo.is_done,
                )
            )
    if kind in ("all", "error"):
        for record, nickname in _public_rows(
            db, ErrorRecord, keyword, [ErrorRecord.title, ErrorRecord.content, ErrorRecord.solution]
        ):
            items.append(
                PublicItem(
                    kind="error",
                    id=record.id,
                    title=record.title,
                    preview=record.content[:PREVIEW_LENGTH],
                    author_nickname=nickname,
                    is_mine=record.user_id == user.id,
                    created_at=record.created_at,
                    is_resolved=record.is_resolved,
                )
            )

    # 세 종류를 합쳐서 최근에 작성한 기록부터 보여준다.
    items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
    return PublicList(items=items)
