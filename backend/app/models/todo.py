from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, false
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.common import clean_required, utcnow

TITLE_MAX = 100


class Todo(Base):
    """할 일"""

    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint(f"length(title) BETWEEN 1 AND {TITLE_MAX}", name="ck_todos_title_length"),
        # 완료 상태일 때만 완료 시각이 있어야 한다.
        CheckConstraint(
            "(is_done AND completed_at IS NOT NULL) OR (NOT is_done AND completed_at IS NULL)",
            name="ck_todos_completed_at_matches_state",
        ),
        Index("ix_todos_user_created", "user_id", "created_at"),
        Index("ix_todos_public_created", "is_public", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(TITLE_MAX))
    # 새 할 일은 미완료·비공개로 시작한다.
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @validates("title")
    def _check_title(self, _key: str, value: str) -> str:
        return clean_required(value, "제목", TITLE_MAX)

    def mark_done(self) -> None:
        """완료로 체크한다. 완료 날짜·시간을 자동으로 저장한다."""
        if not self.is_done:
            self.is_done = True
            self.completed_at = utcnow()

    def mark_undone(self) -> None:
        """완료를 취소한다. 완료 날짜·시간을 지운다."""
        self.is_done = False
        self.completed_at = None
