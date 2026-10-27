from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import ROOT_DIR, settings

SQLITE_PREFIX = "sqlite:///"


def resolve_database_url(url: str) -> str:
    """SQLite 파일 경로가 상대 경로이면 프로젝트 루트 기준으로 바꾼다.

    어느 폴더에서 서버나 마이그레이션을 실행해도 같은 파일을 쓰게 하기 위해서다.
    """
    if url.startswith(SQLITE_PREFIX):
        path = url[len(SQLITE_PREFIX) :]
        if path and path != ":memory:" and not Path(path).is_absolute():
            return f"{SQLITE_PREFIX}{(ROOT_DIR / path).as_posix()}"
    return url


def make_engine(url: str) -> Engine:
    url = resolve_database_url(url)
    if url.startswith(SQLITE_PREFIX):
        path = url[len(SQLITE_PREFIX) :]
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, connect_args={"check_same_thread": False})

        # SQLite는 기본적으로 테이블 사이의 연결(외래 키)을 검사하지 않으므로 켠다.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """요청 하나마다 데이터베이스 세션을 열고, 끝나면 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
