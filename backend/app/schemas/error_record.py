from typing import Literal

from pydantic import BaseModel, field_validator

from app.models.common import clean_optional, clean_required
from app.models.error_record import CONTENT_MAX, SOLUTION_MAX, TITLE_MAX
from app.schemas.common import UtcDatetime

# 목록 보기: 전체 / 미해결 / 해결
ErrorFilter = Literal["all", "unresolved", "resolved"]

SOLUTION_REQUIRED = "해결 방법을 입력해야 해결 상태로 바꿀 수 있습니다."


class ErrorIn(BaseModel):
    """오류 기록을 만들거나 수정할 때 보내는 내용."""

    title: str
    content: str
    solution: str | None = None  # 해결 전에는 비워 둘 수 있다.
    is_resolved: bool = False
    is_public: bool = False

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return clean_required(value, "오류 제목", TITLE_MAX)

    @field_validator("content")
    @classmethod
    def _content(cls, value: str) -> str:
        return clean_required(value, "오류 내용", CONTENT_MAX)

    @field_validator("solution")
    @classmethod
    def _solution(cls, value: str | None) -> str | None:
        # 공백만 입력하면 비운 것으로 본다. 입력했다면 1~5,000자여야 한다.
        return clean_optional(value, "해결 방법", SOLUTION_MAX)


class ErrorOut(BaseModel):
    id: int
    title: str
    content: str
    solution: str | None
    is_resolved: bool
    is_public: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime | None
    resolved_at: UtcDatetime | None
    author_nickname: str
    is_mine: bool


class ErrorListItem(BaseModel):
    id: int
    title: str
    preview: str
    is_resolved: bool
    is_public: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime | None
    resolved_at: UtcDatetime | None


class ErrorList(BaseModel):
    items: list[ErrorListItem]
