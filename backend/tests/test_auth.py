from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User

VALID = {"email": "alice@example.com", "password": "password1", "nickname": "alice"}


def signup(client, **overrides):
    return client.post("/api/auth/signup", json={**VALID, **overrides})


def login(client, email="alice@example.com", password="password1"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------- 회원가입 ----------


def test_signup_success_returns_user_without_password(client):
    response = signup(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["nickname"] == "alice"
    assert "password" not in body and "password_hash" not in body


def test_signup_does_not_log_in(client):
    signup(client)
    assert client.get("/api/auth/me").status_code == 401


def test_signup_can_then_log_in(client):
    signup(client)
    assert login(client).status_code == 200


def test_signup_stores_encrypted_password(client, engine):
    signup(client, password="my-secret-pw")
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT password_hash FROM users")).scalar_one()
    assert "my-secret-pw" not in stored


def test_signup_trims_and_lowercases_email(client):
    response = signup(client, email="  Alice@Example.COM  ")
    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


def test_signup_trims_nickname(client):
    assert signup(client, nickname="  alice  ").json()["nickname"] == "alice"


def test_signup_duplicate_email_is_rejected(client):
    signup(client)
    response = signup(client, nickname="bobby")
    assert response.status_code == 409
    assert set(response.json()["errors"]) == {"email"}


def test_signup_duplicate_email_ignores_case(client):
    signup(client)
    response = signup(client, email="ALICE@EXAMPLE.COM", nickname="bobby")
    assert response.status_code == 409
    assert "email" in response.json()["errors"]


def test_signup_duplicate_nickname_is_rejected(client):
    signup(client)
    response = signup(client, email="bob@example.com")
    assert response.status_code == 409
    assert set(response.json()["errors"]) == {"nickname"}


def test_signup_reports_both_duplicates(client):
    signup(client)
    response = signup(client)
    assert response.status_code == 409
    assert set(response.json()["errors"]) == {"email", "nickname"}


@pytest.mark.parametrize("email", ["", "abc", "a@b", "a@", "@example.com", "a b@example.com", "   "])
def test_signup_rejects_bad_email(client, email):
    response = signup(client, email=email)
    assert response.status_code == 422
    assert "email" in response.json()["errors"]


@pytest.mark.parametrize("length,ok", [(7, False), (8, True), (64, True), (65, False), (0, False)])
def test_signup_password_length_boundaries(client, length, ok):
    response = signup(client, password="p" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.status_code == 422
        assert "password" in response.json()["errors"]


def test_signup_password_is_kept_exactly_as_typed(client):
    # 앞뒤 공백도 비밀번호의 일부다.
    assert signup(client, password="  spaced  ").status_code == 201
    assert login(client, password="  spaced  ").status_code == 200
    assert login(client, password="spaced").status_code == 401


@pytest.mark.parametrize("length,ok", [(1, False), (2, True), (20, True), (21, False)])
def test_signup_nickname_length_boundaries(client, length, ok):
    response = signup(client, nickname="n" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert "nickname" in response.json()["errors"]


@pytest.mark.parametrize("nickname", ["has space", "a-b", "a.b", "a@b", "😀😀", "   ", ""])
def test_signup_rejects_bad_nickname_characters(client, nickname):
    response = signup(client, nickname=nickname)
    assert response.status_code == 422
    assert "nickname" in response.json()["errors"]


@pytest.mark.parametrize("nickname", ["홍길동", "user_01", "한글English123_"])
def test_signup_accepts_korean_english_digits_underscore(client, nickname):
    assert signup(client, nickname=nickname).status_code == 201


def test_signup_missing_fields(client):
    response = client.post("/api/auth/signup", json={})
    assert response.status_code == 422
    assert set(response.json()["errors"]) == {"email", "password", "nickname"}


def test_signup_error_messages_are_in_korean(client):
    errors = signup(client, password="short", nickname="x", email="bad").json()["errors"]
    assert "8자 이상 64자 이하" in errors["password"]
    assert "2~20자" in errors["nickname"]
    assert "이메일" in errors["email"]


# ---------- 로그인 ----------


def test_login_success_sets_cookie_and_returns_user(client):
    signup(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["nickname"] == "alice"
    assert client.get("/api/auth/me").json()["email"] == "alice@example.com"


def test_login_cookie_is_not_readable_by_scripts(client):
    signup(client)
    header = login(client).headers["set-cookie"].lower()
    assert "httponly" in header
    assert "samesite=lax" in header


def test_login_email_is_case_insensitive(client):
    signup(client)
    assert login(client, email="ALICE@Example.com").status_code == 200


def test_login_wrong_password_is_rejected(client):
    signup(client)
    response = login(client, password="wrong-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "로그인 정보가 맞지 않습니다."
    assert "set-cookie" not in response.headers


def test_login_unknown_email_gives_same_message(client):
    signup(client)
    response = login(client, email="nobody@example.com")
    assert response.status_code == 401
    assert response.json()["detail"] == "로그인 정보가 맞지 않습니다."


def test_login_failure_does_not_log_in(client):
    signup(client)
    login(client, password="wrong-password")
    assert client.get("/api/auth/me").status_code == 401


# ---------- 로그아웃 ----------


def test_logout_ends_login(client):
    signup(client)
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_logout_then_login_again(client):
    signup(client)
    login(client)
    client.post("/api/auth/logout")
    assert login(client).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_logout_without_login_is_harmless(client):
    assert client.post("/api/auth/logout").status_code == 204


# ---------- 로그인한 사용자만 접근 ----------


def test_me_requires_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "로그인이 필요합니다."


def test_tampered_token_is_rejected(client):
    signup(client)
    token = create_access_token(1)
    client.cookies.set("access_token", token[:-3] + "abc")
    assert client.get("/api/auth/me").status_code == 401


def test_token_signed_with_other_key_is_rejected(client):
    signup(client)
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "another-secret-key-another-secret-key-1234",
        algorithm="HS256",
    )
    client.cookies.set("access_token", forged)
    assert client.get("/api/auth/me").status_code == 401


def test_expired_token_is_rejected(client):
    signup(client)
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
        settings.secret_key,
        algorithm="HS256",
    )
    client.cookies.set("access_token", expired)
    assert client.get("/api/auth/me").status_code == 401


def test_token_of_missing_user_is_rejected(client):
    client.cookies.set("access_token", create_access_token(9999))
    assert client.get("/api/auth/me").status_code == 401


# ---------- 닉네임 변경 ----------


def test_change_nickname_success(client):
    signup(client)
    login(client)
    response = client.patch("/api/auth/me/nickname", json={"nickname": "새닉네임"})
    assert response.status_code == 200
    assert response.json()["nickname"] == "새닉네임"
    assert client.get("/api/auth/me").json()["nickname"] == "새닉네임"


def test_change_nickname_requires_login(client):
    response = client.patch("/api/auth/me/nickname", json={"nickname": "newname"})
    assert response.status_code == 401


def test_change_nickname_to_own_current_nickname_is_ok(client):
    signup(client)
    login(client)
    assert client.patch("/api/auth/me/nickname", json={"nickname": "alice"}).status_code == 200


def test_change_nickname_to_taken_nickname_is_rejected(make_client):
    a, b = make_client(), make_client()
    signup(a)
    signup(b, email="bob@example.com", nickname="bobby")
    login(a)
    response = a.patch("/api/auth/me/nickname", json={"nickname": "bobby"})
    assert response.status_code == 409
    assert "nickname" in response.json()["errors"]
    assert a.get("/api/auth/me").json()["nickname"] == "alice"


@pytest.mark.parametrize("nickname", ["a", "a" * 21, "has space", "a-b", ""])
def test_change_nickname_applies_same_rules_as_signup(client, nickname):
    signup(client)
    login(client)
    response = client.patch("/api/auth/me/nickname", json={"nickname": nickname})
    assert response.status_code == 422
    assert "nickname" in response.json()["errors"]
    assert client.get("/api/auth/me").json()["nickname"] == "alice"


def test_changing_own_nickname_never_changes_other_users(make_client, engine):
    a, b = make_client(), make_client()
    signup(a)
    signup(b, email="bob@example.com", nickname="bobby")
    login(a)
    a.patch("/api/auth/me/nickname", json={"nickname": "alice2"})
    with sessionmaker(bind=engine)() as session:
        names = {u.email: u.nickname for u in session.scalars(select(User))}
    assert names == {"alice@example.com": "alice2", "bob@example.com": "bobby"}


def test_each_user_only_sees_own_account(make_client):
    a, b = make_client(), make_client()
    signup(a)
    signup(b, email="bob@example.com", nickname="bobby")
    login(a)
    login(b, email="bob@example.com")
    assert a.get("/api/auth/me").json()["nickname"] == "alice"
    assert b.get("/api/auth/me").json()["nickname"] == "bobby"
