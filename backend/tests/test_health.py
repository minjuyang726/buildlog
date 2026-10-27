from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_frontend_origin():
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_other_origin():
    response = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_api_docs_are_open_only_in_development():
    from app.main import create_app

    development = TestClient(create_app("development"))
    assert development.get("/docs").status_code == 200
    assert development.get("/openapi.json").status_code == 200

    production = TestClient(create_app("production"))
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert production.get(path).status_code == 404
    assert production.get("/api/health").status_code == 200  # 서버 자체는 정상 동작


def test_every_feature_router_is_registered():
    from app.main import create_app

    paths = set(create_app("production").openapi()["paths"])
    expected = {
        "/api/auth/signup", "/api/studies", "/api/todos", "/api/errors", "/api/public",
        "/api/comments/{comment_id}", "/api/studies/{record_id}/like", "/api/reports",
    }
    assert expected <= paths
