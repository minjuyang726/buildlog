from typing import Literal

from pydantic import BaseModel

from app.schemas.common import UtcDatetime

# 공개 기록 화면의 보기: 전체 / 공부 기록 / 할 일 / 오류 기록
PublicKind = Literal["all", "study", "todo", "error"]


class PublicItem(BaseModel):
    kind: Literal["study", "todo", "error"]
    id: int
    title: str
    preview: str | None  # 공부 기록·오류 기록의 내용 앞부분 (할 일은 없음)
    author_nickname: str
    is_mine: bool
    created_at: UtcDatetime
    is_done: bool | None = None  # 할 일일 때만
    is_resolved: bool | None = None  # 오류 기록일 때만


class PublicList(BaseModel):
    items: list[PublicItem]
