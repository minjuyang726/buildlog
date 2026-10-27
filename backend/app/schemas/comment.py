from pydantic import BaseModel, field_validator

from app.models.comment import CONTENT_MAX
from app.models.common import clean_required
from app.schemas.common import UtcDatetime


class CommentIn(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def _content(cls, value: str) -> str:
        return clean_required(value, "댓글", CONTENT_MAX)


class CommentOut(BaseModel):
    id: int
    content: str
    author_nickname: str
    is_mine: bool
    can_delete: bool  # 내 댓글이거나, 내 기록에 달린 댓글이면 삭제할 수 있다.
    created_at: UtcDatetime
    updated_at: UtcDatetime | None


class CommentList(BaseModel):
    items: list[CommentOut]
