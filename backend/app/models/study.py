from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.common import clean_required, utcnow

TITLE_MAX = 100
CONTENT_MAX = 5000


class Study(Base):
    """공부 기록"""

    __tablename__ = "studies"
    __table_args__ = (
        CheckConstraint(f"length(title) BETWEEN 1 AND {TITLE_MAX}", name="ck_studies_title_length"),
        CheckConstraint(f"length(content) BETWEEN 1 AND {CONTENT_MAX}", name="ck_studies_content_length"),
        Index("ix_studies_user_created", "user_id", "created_at"),
        Index("ix_studies_public_created", "is_public", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(TITLE_MAX))
    content: Mapped[str] = mapped_column(Text)
    # 새 기록은 비공개로 시작한다.
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # 내용을 수정했을 때만 저장한다. 수정한 적이 없으면 비어 있다.
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @validates("title")
    def _check_title(self, _key: str, value: str) -> str:
        return clean_required(value, "제목", TITLE_MAX)

    @validates("content")
    def _check_content(self, _key: str, value: str) -> str:
        return clean_required(value, "내용", CONTENT_MAX)
