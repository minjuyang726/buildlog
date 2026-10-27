from typing import Literal

from pydantic import BaseModel, field_validator

from app.models.common import clean_required
from app.models.todo import TITLE_MAX
from app.schemas.common import UtcDatetime

# 목록 보기: 전체 / 남은 일 / 완료한 일
TodoFilter = Literal["all", "open", "done"]


class TodoIn(BaseModel):
    """할 일을 만들거나 수정할 때 보내는 내용."""

    title: str
    is_public: bool = False  # 공개 여부를 고르지 않으면 비공개

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return clean_required(value, "제목", TITLE_MAX)


class TodoDoneIn(BaseModel):
    is_done: bool


class TodoOut(BaseModel):
    id: int
    title: str
    is_done: bool
    is_public: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime | None
    completed_at: UtcDatetime | None
    author_nickname: str
    is_mine: bool


class TodoList(BaseModel):
    items: list[TodoOut]
