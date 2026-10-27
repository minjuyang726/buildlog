from pydantic import BaseModel, field_validator

from app.models.common import clean_required
from app.models.study import CONTENT_MAX, TITLE_MAX
from app.schemas.common import UtcDatetime


class StudyIn(BaseModel):
    """공부 기록을 만들거나 수정할 때 보내는 내용."""

    title: str
    content: str
    is_public: bool = False  # 공개 여부를 고르지 않으면 비공개

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return clean_required(value, "제목", TITLE_MAX)

    @field_validator("content")
    @classmethod
    def _content(cls, value: str) -> str:
        return clean_required(value, "내용", CONTENT_MAX)


class StudyOut(BaseModel):
    id: int
    title: str
    content: str
    is_public: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime | None
    author_nickname: str
    is_mine: bool


class StudyListItem(BaseModel):
    id: int
    title: str
    preview: str
    is_public: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime | None


class StudyList(BaseModel):
    items: list[StudyListItem]
