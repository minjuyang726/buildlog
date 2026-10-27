from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.common import clean_required, utcnow

REASON_MAX = 500


class Report(Base):
    """공개 기록(공부 기록, 할 일, 오류 기록) 또는 댓글에 대한 신고.

    신고 내용은 운영자가 확인할 수 있도록 저장만 한다. 일반 사용자에게는 어떤 경로로도 보여주지 않고,
    신고만으로 기록이나 댓글을 자동으로 지우지 않는다.
    """

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(f"length(reason) BETWEEN 1 AND {REASON_MAX}", name="ck_reports_reason_length"),
        # 신고 대상은 네 가지 중 정확히 하나여야 한다.
        CheckConstraint(
            "(CASE WHEN study_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN todo_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN error_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN comment_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_reports_exactly_one_target",
        ),
        # 한 사용자는 같은 대상을 한 번만 신고할 수 있다.
        UniqueConstraint("reporter_id", "study_id", name="uq_reports_reporter_study"),
        UniqueConstraint("reporter_id", "todo_id", name="uq_reports_reporter_todo"),
        UniqueConstraint("reporter_id", "error_id", name="uq_reports_reporter_error"),
        UniqueConstraint("reporter_id", "comment_id", name="uq_reports_reporter_comment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    study_id: Mapped[int | None] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"), default=None)
    todo_id: Mapped[int | None] = mapped_column(ForeignKey("todos.id", ondelete="CASCADE"), default=None)
    error_id: Mapped[int | None] = mapped_column(ForeignKey("error_records.id", ondelete="CASCADE"), default=None)
    comment_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), default=None)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @validates("reason")
    def _check_reason(self, _key: str, value: str) -> str:
        return clean_required(value, "신고 이유", REASON_MAX)
