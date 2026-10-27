import os

# 실제 .env 없이도 테스트가 돌도록, 앱을 불러오기 전에 테스트용 값을 먼저 정한다.
os.environ["SECRET_KEY"] = "test-only-secret-key-for-automated-tests-0123456789"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
# 테스트가 개발용 데이터 파일을 건드리지 않도록 임시 위치로 바꿔 둔다.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import get_db, make_engine  # noqa: E402
from app.main import app  # noqa: E402


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


@pytest.fixture
def client(engine):
    """테스트용 임시 데이터베이스에 연결된 서버 요청 도구."""
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_client(engine):
    """같은 데이터베이스를 쓰는 서로 다른 사용자(브라우저)를 여러 명 만들 때 쓴다."""
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    clients = []

    def _make():
        test_client = TestClient(app)
        clients.append(test_client)
        return test_client

    yield _make
    for c in clients:
        c.close()
    app.dependency_overrides.clear()
