import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.helpers import register_and_login, two_users

KINDS = ["studies", "errors"]


def make_record(client, kind, is_public=True):
    body = {"title": "공개 기록", "content": "내용", "is_public": is_public}
    r = client.post(f"/api/{kind}", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def set_public(client, kind, record_id, is_public):
    body = {"title": "공개 기록", "content": "내용", "is_public": is_public}
    assert client.put(f"/api/{kind}/{record_id}", json=body).status_code == 200


def like(client, kind, record_id):
    return client.put(f"/api/{kind}/{record_id}/like")


def unlike(client, kind, record_id):
    return client.delete(f"/api/{kind}/{record_id}/like")


def state(client, kind, record_id):
    r = client.get(f"/api/{kind}/{record_id}/like")
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def three(make_client):
    alice, bobby = two_users(make_client)
    carol = register_and_login(make_client(), "carol@example.com", "carol")
    return alice, bobby, carol


def test_requires_login(client):
    for method in ("get", "put", "delete"):
        assert getattr(client, method)("/api/studies/1/like").status_code == 401


@pytest.mark.parametrize("kind", KINDS)
def test_initial_state_is_zero_and_not_liked(three, kind):
    alice, bobby, _ = three
    record_id = make_record(alice, kind)
    assert state(bobby, kind, record_id) == {"liked": False, "like_count": 0}


@pytest.mark.parametrize("kind", KINDS)
def test_like_then_cancel(three, kind):
    alice, bobby, _ = three
    record_id = make_record(alice, kind)
    assert like(bobby, kind, record_id).json() == {"liked": True, "like_count": 1}
    assert state(bobby, kind, record_id) == {"liked": True, "like_count": 1}
    assert unlike(bobby, kind, record_id).json() == {"liked": False, "like_count": 0}
    assert state(bobby, kind, record_id) == {"liked": False, "like_count": 0}


@pytest.mark.parametrize("kind", KINDS)
def test_same_user_cannot_like_twice(three, kind):
    alice, bobby, _ = three
    record_id = make_record(alice, kind)
    like(bobby, kind, record_id)
    again = like(bobby, kind, record_id)
    assert again.status_code == 200
    assert again.json() == {"liked": True, "like_count": 1}  # 두 번 눌러도 1개


def test_cancelling_twice_is_harmless(three):
    alice, bobby, _ = three
    record_id = make_record(alice, "studies")
    like(bobby, "studies", record_id)
    unlike(bobby, "studies", record_id)
    assert unlike(bobby, "studies", record_id).json() == {"liked": False, "like_count": 0}


def test_cancelling_without_liking_is_harmless(three):
    alice, bobby, _ = three
    record_id = make_record(alice, "studies")
    assert unlike(bobby, "studies", record_id).json() == {"liked": False, "like_count": 0}


@pytest.mark.parametrize("kind", KINDS)
def test_count_adds_up_across_users_and_each_sees_own_state(three, kind):
    alice, bobby, carol = three
    record_id = make_record(alice, kind)
    like(bobby, kind, record_id)
    like(carol, kind, record_id)
    assert state(alice, kind, record_id) == {"liked": False, "like_count": 2}
    assert state(bobby, kind, record_id) == {"liked": True, "like_count": 2}
    assert state(carol, kind, record_id) == {"liked": True, "like_count": 2}


def test_cancelling_only_removes_my_like(three):
    alice, bobby, carol = three
    record_id = make_record(alice, "studies")
    like(bobby, "studies", record_id)
    like(carol, "studies", record_id)
    unlike(bobby, "studies", record_id)
    assert state(carol, "studies", record_id) == {"liked": True, "like_count": 1}


def test_likes_on_different_records_are_independent(three):
    alice, bobby, _ = three
    first, second = make_record(alice, "studies"), make_record(alice, "studies")
    like(bobby, "studies", first)
    assert state(bobby, "studies", second) == {"liked": False, "like_count": 0}


def test_study_and_error_with_same_id_do_not_mix(three):
    alice, bobby, _ = three
    study_id, error_id = make_record(alice, "studies"), make_record(alice, "errors")
    assert study_id == error_id == 1
    like(bobby, "studies", study_id)
    assert state(bobby, "errors", error_id) == {"liked": False, "like_count": 0}


def test_record_author_may_like_own_public_record(three):
    alice, _, _ = three
    record_id = make_record(alice, "studies")
    assert like(alice, "studies", record_id).json() == {"liked": True, "like_count": 1}


# ---------- 할 일에는 좋아요가 없다 ----------


def test_todos_have_no_like_endpoints(three):
    alice, bobby, _ = three
    todo_id = alice.post("/api/todos", json={"title": "공개 할 일", "is_public": True}).json()["id"]
    for method in ("get", "put", "delete"):
        assert getattr(bobby, method)(f"/api/todos/{todo_id}/like").status_code == 404


# ---------- 비공개 기록 ----------


@pytest.mark.parametrize("kind", KINDS)
def test_cannot_like_or_read_likes_of_private_record(three, kind):
    alice, bobby, _ = three
    record_id = make_record(alice, kind, is_public=False)
    for fn in (like, unlike):
        assert fn(bobby, kind, record_id).status_code == 404
    assert bobby.get(f"/api/{kind}/{record_id}/like").status_code == 404
    assert like(alice, kind, record_id).status_code == 404  # 작성자도 비공개 기록에는 누를 수 없다.


def test_missing_record(three):
    _, bobby, _ = three
    assert like(bobby, "studies", 9999).status_code == 404


@pytest.mark.parametrize("kind", KINDS)
def test_making_record_private_hides_likes_and_public_again_restores_them(three, kind):
    alice, bobby, carol = three
    record_id = make_record(alice, kind)
    like(bobby, kind, record_id)
    like(carol, kind, record_id)

    set_public(alice, kind, record_id, False)
    for client in (alice, bobby, carol):
        assert client.get(f"/api/{kind}/{record_id}/like").status_code == 404
    assert unlike(bobby, kind, record_id).status_code == 404  # 숨겨진 동안은 취소도 못 한다.

    set_public(alice, kind, record_id, True)
    assert state(bobby, kind, record_id) == {"liked": True, "like_count": 2}  # 그대로 돌아온다.


def test_hidden_likes_are_kept_in_database(three, engine):
    alice, bobby, _ = three
    record_id = make_record(alice, "studies")
    like(bobby, "studies", record_id)
    set_public(alice, "studies", record_id, False)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM likes")).scalar_one() == 1


# ---------- 데이터베이스 제약 ----------


def test_deleting_record_removes_its_likes(three, engine):
    alice, bobby, _ = three
    record_id = make_record(alice, "studies")
    like(bobby, "studies", record_id)
    alice.delete(f"/api/studies/{record_id}")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM likes")).scalar_one() == 0


def test_database_blocks_duplicate_like_even_if_code_is_bypassed(three, engine):
    alice, bobby, _ = three
    record_id = make_record(alice, "studies")
    like(bobby, "studies", record_id)
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text("INSERT INTO likes (user_id, study_id, created_at) VALUES (2, :s, CURRENT_TIMESTAMP)"), {"s": record_id}
        )


def test_database_blocks_duplicate_like_on_error_records(three, engine):
    alice, bobby, _ = three
    record_id = make_record(alice, "errors")
    like(bobby, "errors", record_id)
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text("INSERT INTO likes (user_id, error_id, created_at) VALUES (2, :e, CURRENT_TIMESTAMP)"), {"e": record_id}
        )


def test_database_rejects_like_pointing_at_both_or_neither(three, engine):
    alice, _, _ = three
    study_id, error_id = make_record(alice, "studies"), make_record(alice, "errors")
    for s, e in [(study_id, error_id), (None, None)]:
        with engine.begin() as connection, pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO likes (user_id, study_id, error_id, created_at) VALUES (1, :s, :e, CURRENT_TIMESTAMP)"),
                {"s": s, "e": e},
            )
