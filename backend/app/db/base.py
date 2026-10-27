from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 저장 데이터(테이블)의 공통 부모."""
