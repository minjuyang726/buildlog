import re
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base

NICKNAME_PATTERN = re.compile(r"^[가-힣A-Za-z0-9_]{2,20}$")


def normalize_email(email: str) -> str:
    """이메일은 앞뒤 공백을 지우고 소문자로 바꿔 같은 주소로 취급한다."""
    return email.strip().lower()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(nickname) BETWEEN 2 AND 20", name="ck_users_nickname_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @validates("email")
    def _normalize_email(self, _key: str, value: str) -> str:
        return normalize_email(value)

    @validates("nickname")
    def _check_nickname(self, _key: str, value: str) -> str:
        value = value.strip()
        if not NICKNAME_PATTERN.match(value):
            raise ValueError("닉네임은 2~20자의 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.")
        return value
