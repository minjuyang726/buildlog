"""여러 테스트 파일에서 함께 쓰는 도우미."""


def register_and_login(client, email="alice@example.com", nickname="alice", password="password1"):
    """가입하고 로그인한 상태로 만든다. 같은 client로 이후 요청을 보내면 그 사용자의 요청이 된다."""
    response = client.post("/api/auth/signup", json={"email": email, "password": password, "nickname": nickname})
    assert response.status_code == 201, response.text
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return client


def two_users(make_client):
    """서로 다른 두 사용자(alice, bobby)를 돌려준다."""
    alice = register_and_login(make_client(), "alice@example.com", "alice")
    bobby = register_and_login(make_client(), "bobby@example.com", "bobby")
    return alice, bobby
