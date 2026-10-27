from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.common import clean_optional, clean_required, utcnow

TITLE_MAX = 100
CONTENT_MAX = 5000
SOLUTION_MAX = 5000


class ErrorRecord(Base):
    """오류 기록"""

    __tablename__ = "error_records"
    __table_args__ = (
        CheckConstraint(f"length(title) BETWEEN 1 AND {TITLE_MAX}", name="ck_error_records_title_length"),
        CheckConstraint(f"length(content) BETWEEN 1 AND {CONTENT_MAX}", name="ck_error_records_content_length"),
        # 해결 방법은 비워 둘 수 있지만, 입력했다면 1~5,000자여야 한다.
        CheckConstraint(
            f"solution IS NULL OR length(solution) BETWEEN 1 AND {SOLUTION_MAX}",
            name="ck_error_records_solution_length",
        ),
        # 해결 상태로 저장하려면 해결 방법이 반드시 있어야 한다.
        CheckConstraint(
            "(NOT is_resolved) OR (solution IS NOT NULL)",
            name="ck_error_records_resolved_needs_solution",
        ),
        # 해결 상태일 때만 해결 시각이 있어야 한다.
        CheckConstraint(
            "(is_resolved AND resolved_at IS NOT NULL) OR (NOT is_resolved AND resolved_at IS NULL)",
            name="ck_error_records_resolved_at_matches_state",
        ),
        Index("ix_error_records_user_created", "user_id", "created_at"),
        Index("ix_error_records_public_created", "is_public", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(TITLE_MAX))
    content: Mapped[str] = mapped_column(Text)
    solution: Mapped[str | None] = mapped_column(Text, default=None)
    # 새 오류는 미해결·비공개로 시작한다.
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @validates("title")
    def _check_title(self, _key: str, value: str) -> str:
        return clean_required(value, "오류 제목", TITLE_MAX)

    @validates("content")
    def _check_content(self, _key: str, value: str) -> str:
        return clean_required(value, "오류 내용", CONTENT_MAX)

    @validates("solution")
    def _check_solution(self, _key: str, value: str | None) -> str | None:
        return clean_optional(value, "해결 방법", SOLUTION_MAX)

    def mark_resolved(self, solution: str | None = None) -> None:
        """해결 상태로 바꾼다. 해결 방법이 없으면 바꿀 수 없다. 해결 날짜·시간을 자동으로 저장한다."""
        if solution is not None:
            self.solution = solution
        if not self.solution:
            raise ValueError("해결 방법을 입력해야 해결 상태로 바꿀 수 있습니다.")
        if not self.is_resolved:
            self.is_resolved = True
            self.resolved_at = utcnow()

    def mark_unresolved(self) -> None:
        """미해결로 되돌린다. 해결 방법은 유지하고 해결 날짜·시간만 지운다."""
        self.is_resolved = False
        self.resolved_at = None
