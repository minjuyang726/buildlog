import os

# 실제 .env 없이도 테스트가 돌도록, 앱을 불러오기 전에 테스트용 값을 먼저 정한다.
os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
# 테스트가 개발용 데이터 파일을 건드리지 않도록 임시 위치로 바꿔 둔다.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import make_engine  # noqa: E402


@pytest.fixture
def db_url(tmp_path):
    """테스트마다 새로 만들어지는 임시 SQLite 파일 주소."""
    return f"sqlite:///{(tmp_path / 'test.sqlite3').as_posix()}"


@pytest.fixture
def engine(db_url):
    engine = make_engine(db_url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
