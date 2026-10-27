from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.common import clean_required, utcnow

CONTENT_MAX = 500


class Comment(Base):
    """공개된 공부 기록 또는 오류 기록에 다는 댓글. 할 일에는 달 수 없다."""

    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(f"length(content) BETWEEN 1 AND {CONTENT_MAX}", name="ck_comments_content_length"),
        # 공부 기록과 오류 기록 중 정확히 하나만 가리켜야 한다.
        CheckConstraint(
            "(study_id IS NOT NULL AND error_id IS NULL) OR (study_id IS NULL AND error_id IS NOT NULL)",
            name="ck_comments_exactly_one_target",
        ),
        Index("ix_comments_study_created", "study_id", "created_at"),
        Index("ix_comments_error_created", "error_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    study_id: Mapped[int | None] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"), default=None)
    error_id: Mapped[int | None] = mapped_column(ForeignKey("error_records.id", ondelete="CASCADE"), default=None)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @validates("content")
    def _check_content(self, _key: str, value: str) -> str:
        return clean_required(value, "댓글", CONTENT_MAX)
