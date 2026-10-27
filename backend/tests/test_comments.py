import pytest
from sqlalchemy import text

from tests.helpers import register_and_login, two_users

KINDS = [("studies", "공부 기록"), ("errors", "오류 기록")]


def make_record(client, kind, title="공개 기록", **extra):
    if kind == "studies":
        r = client.post("/api/studies", json={"title": title, "content": "내용", "is_public": True, **extra})
    else:
        r = client.post("/api/errors", json={"title": title, "content": "내용", "is_public": True, **extra})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def set_public(client, kind, record_id, is_public):
    if kind == "studies":
        body = {"title": "공개 기록", "content": "내용", "is_public": is_public}
    else:
        body = {"title": "공개 기록", "content": "내용", "is_public": is_public}
    assert client.put(f"/api/{kind}/{record_id}", json=body).status_code == 200


def comment(client, kind, record_id, content="좋은 글이네요"):
    return client.post(f"/api/{kind}/{record_id}/comments", json={"content": content})


def comments(client, kind, record_id):
    r = client.get(f"/api/{kind}/{record_id}/comments")
    assert r.status_code == 200
    return r.json()["items"]


@pytest.fixture
def three(make_client):
    """alice(기록 작성자), bobby(댓글 작성자), carol(제3자)"""
    alice, bobby = two_users(make_client)
    carol = register_and_login(make_client(), "carol@example.com", "carol")
    return alice, bobby, carol


def test_requires_login(client):
    for method, path in [("get", "/api/studies/1/comments"), ("post", "/api/studies/1/comments"),
                         ("put", "/api/comments/1"), ("delete", "/api/comments/1")]:
        kwargs = {"json": {"content": "x"}} if method in ("post", "put") else {}
        assert getattr(client, method)(path, **kwargs).status_code == 401


# ---------- 작성 ----------


@pytest.mark.parametrize("kind,_", KINDS)
def test_write_and_read_comment_on_public_record(three, kind, _):
    alice, bobby, _carol = three
    record_id = make_record(alice, kind)
    response = comment(bobby, kind, record_id)
    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "좋은 글이네요"
    assert body["author_nickname"] == "bobby" and body["is_mine"] is True
    assert body["updated_at"] is None and body["created_at"].endswith("Z")
    # 다른 사람도 같은 댓글을 본다.
    assert [c["content"] for c in comments(alice, kind, record_id)] == ["좋은 글이네요"]


@pytest.mark.parametrize("kind,_", KINDS)
def test_record_author_can_also_comment_on_own_public_record(three, kind, _):
    alice, _bobby, _carol = three
    record_id = make_record(alice, kind)
    assert comment(alice, kind, record_id).status_code == 201


@pytest.mark.parametrize("kind,_", KINDS)
@pytest.mark.parametrize("length,ok", [(1, True), (500, True), (0, False), (501, False)])
def test_comment_length_boundaries(three, kind, _, length, ok):
    alice, bobby, _carol = three
    record_id = make_record(alice, kind)
    response = comment(bobby, kind, record_id, "가" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.json()["errors"]["content"] == "댓글은 1자 이상 500자 이하로 입력해 주세요."
        assert comments(alice, kind, record_id) == []


def test_comment_trims_outer_spaces_and_rejects_whitespace_only(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    assert comment(bobby, "studies", record_id, "  안녕   하세요  ").json()["content"] == "안녕   하세요"
    assert comment(bobby, "studies", record_id, "   \n ").status_code == 422
    assert len(comments(alice, "studies", record_id)) == 1


def test_missing_content_field(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    assert bobby.post(f"/api/studies/{record_id}/comments", json={}).status_code == 422


def test_comments_are_oldest_first(three):
    alice, bobby, carol = three
    record_id = make_record(alice, "studies")
    for who, text_ in [(bobby, "첫째"), (carol, "둘째"), (bobby, "셋째")]:
        comment(who, "studies", record_id, text_)
    assert [c["content"] for c in comments(alice, "studies", record_id)] == ["첫째", "둘째", "셋째"]


def test_replies_are_not_supported(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    # 댓글에 다는 답글 경로는 없다.
    assert bobby.post(f"/api/comments/{comment_id}/comments", json={"content": "답글"}).status_code in (404, 405)
    assert "parent_id" not in comments(alice, "studies", record_id)[0]


# ---------- 할 일에는 댓글이 없다 ----------


def test_todos_have_no_comment_endpoints(three):
    alice, bobby, _carol = three
    todo_id = alice.post("/api/todos", json={"title": "공개 할 일", "is_public": True}).json()["id"]
    assert bobby.get(f"/api/todos/{todo_id}/comments").status_code == 404
    assert bobby.post(f"/api/todos/{todo_id}/comments", json={"content": "x"}).status_code == 404


# ---------- 비공개 기록의 댓글 ----------


@pytest.mark.parametrize("kind,_", KINDS)
def test_cannot_comment_or_read_on_private_record(three, kind, _):
    alice, bobby, _carol = three
    record_id = make_record(alice, kind, is_public=False)
    assert comment(bobby, kind, record_id).status_code == 404
    assert bobby.get(f"/api/{kind}/{record_id}/comments").status_code == 404
    assert comment(alice, kind, record_id).status_code == 404  # 비공개 기록에는 작성자도 댓글을 달 수 없다.


def test_comment_on_missing_record(three):
    _alice, bobby, _carol = three
    assert comment(bobby, "studies", 9999).status_code == 404


@pytest.mark.parametrize("kind,_", KINDS)
def test_making_record_private_hides_comments_and_public_again_restores_them(three, kind, _):
    alice, bobby, _carol = three
    record_id = make_record(alice, kind)
    comment_id = comment(bobby, kind, record_id).json()["id"]

    set_public(alice, kind, record_id, False)
    assert bobby.get(f"/api/{kind}/{record_id}/comments").status_code == 404
    assert alice.get(f"/api/{kind}/{record_id}/comments").status_code == 404
    # 숨겨진 댓글은 수정·삭제도 할 수 없다.
    assert bobby.put(f"/api/comments/{comment_id}", json={"content": "수정"}).status_code == 404
    assert bobby.delete(f"/api/comments/{comment_id}").status_code == 404
    assert alice.delete(f"/api/comments/{comment_id}").status_code == 404

    set_public(alice, kind, record_id, True)
    restored = comments(bobby, kind, record_id)
    assert [c["content"] for c in restored] == ["좋은 글이네요"]  # 지워지지 않고 그대로 돌아온다.


def test_hidden_comments_are_kept_in_the_database(three, engine):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment(bobby, "studies", record_id)
    set_public(alice, "studies", record_id, False)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM comments")).scalar_one() == 1


# ---------- 수정 ----------


def test_author_can_edit_own_comment(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    response = bobby.put(f"/api/comments/{comment_id}", json={"content": "  고친 댓글  "})
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "고친 댓글" and body["updated_at"] is not None
    assert comments(alice, "studies", record_id)[0]["content"] == "고친 댓글"


def test_edit_applies_same_length_rules_and_failure_changes_nothing(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id, "원래 댓글").json()["id"]
    for bad in ["", "   ", "가" * 501]:
        assert bobby.put(f"/api/comments/{comment_id}", json={"content": bad}).status_code == 422
    saved = comments(bobby, "studies", record_id)[0]
    assert saved["content"] == "원래 댓글" and saved["updated_at"] is None


def test_nobody_else_can_edit_a_comment_not_even_the_record_author(three):
    alice, bobby, carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    assert carol.put(f"/api/comments/{comment_id}", json={"content": "해킹"}).status_code == 403
    assert alice.put(f"/api/comments/{comment_id}", json={"content": "해킹"}).status_code == 403
    assert comments(bobby, "studies", record_id)[0]["content"] == "좋은 글이네요"


def test_edit_missing_comment(three):
    _alice, bobby, _carol = three
    assert bobby.put("/api/comments/9999", json={"content": "x"}).status_code == 404


# ---------- 삭제 ----------


def test_comment_author_can_delete_own_comment(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    assert bobby.delete(f"/api/comments/{comment_id}").status_code == 204
    assert comments(alice, "studies", record_id) == []


def test_record_author_can_delete_comments_on_own_record(three):
    alice, bobby, _carol = three
    record_id = make_record(alice, "errors")
    comment_id = comment(bobby, "errors", record_id).json()["id"]
    assert alice.delete(f"/api/comments/{comment_id}").status_code == 204
    assert comments(bobby, "errors", record_id) == []


def test_third_party_cannot_delete_comment(three):
    alice, bobby, carol = three
    record_id = make_record(alice, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    assert carol.delete(f"/api/comments/{comment_id}").status_code == 403
    assert len(comments(alice, "studies", record_id)) == 1


def test_record_author_cannot_delete_comments_on_someone_elses_record(three):
    alice, bobby, carol = three
    record_id = make_record(carol, "studies")
    comment_id = comment(bobby, "studies", record_id).json()["id"]
    assert alice.delete(f"/api/comments/{comment_id}").status_code == 403


def test_can_delete_flag_matches_permissions(three):
    alice, bobby, carol = three
    record_id = make_record(alice, "studies")
    comment(bobby, "studies", record_id)
    seen = {name: comments(client, "studies", record_id)[0]["can_delete"] for name, client in
            [("alice", alice), ("bobby", bobby), ("carol", carol)]}
    assert seen == {"alice": True, "bobby": True, "carol": False}


def test_delete_missing_comment(three):
    _alice, bobby, _carol = three
    assert bobby.delete("/api/comments/9999").status_code == 404


def test_deleting_the_record_removes_its_comments(three, engine):
    alice, bobby, _carol = three
    record_id = make_record(alice, "studies")
    comment(bobby, "studies", record_id)
    alice.delete(f"/api/studies/{record_id}")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM comments")).scalar_one() == 0


def test_database_rejects_comment_pointing_at_both_or_neither(three, engine):
    alice, _bobby, _carol = three
    record_id = make_record(alice, "studies")
    error_id = make_record(alice, "errors")
    from sqlalchemy.exc import IntegrityError

    for study_id, err_id in [(record_id, error_id), (None, None)]:
        with engine.begin() as connection, pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO comments (user_id, study_id, error_id, content, created_at) VALUES (1, :s, :e, 'x', CURRENT_TIMESTAMP)"),
                {"s": study_id, "e": err_id},
            )
