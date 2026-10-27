from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import utcnow


class Like(Base):
    """공개된 공부 기록 또는 오류 기록에 누른 좋아요. 할 일에는 누를 수 없다."""

    __tablename__ = "likes"
    __table_args__ = (
        # 공부 기록과 오류 기록 중 정확히 하나만 가리켜야 한다.
        CheckConstraint(
            "(study_id IS NOT NULL AND error_id IS NULL) OR (study_id IS NULL AND error_id IS NOT NULL)",
            name="ck_likes_exactly_one_target",
        ),
        # 한 사용자는 같은 기록에 좋아요를 한 번만 누를 수 있다.
        UniqueConstraint("user_id", "study_id", name="uq_likes_user_study"),
        UniqueConstraint("user_id", "error_id", name="uq_likes_user_error"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    study_id: Mapped[int | None] = mapped_column(ForeignKey("studies.id", ondelete="CASCADE"), default=None)
    error_id: Mapped[int | None] = mapped_column(ForeignKey("error_records.id", ondelete="CASCADE"), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
