import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.helpers import register_and_login, two_users


def post_record(client, kind, is_public=True):
    if kind == "study":
        r = client.post("/api/studies", json={"title": "기록", "content": "내용", "is_public": is_public})
    elif kind == "todo":
        r = client.post("/api/todos", json={"title": "기록", "is_public": is_public})
    else:
        r = client.post("/api/errors", json={"title": "기록", "content": "내용", "is_public": is_public})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def post_comment(client, kind, record_id):
    path = "studies" if kind == "study" else "errors"
    r = client.post(f"/api/{path}/{record_id}/comments", json={"content": "댓글"})
    assert r.status_code == 201
    return r.json()["id"]


def report(client, target_type, target_id, reason="부적절한 내용입니다"):
    return client.post("/api/reports", json={"target_type": target_type, "target_id": target_id, "reason": reason})


def count(engine, sql="SELECT count(*) FROM reports"):
    with engine.connect() as connection:
        return connection.execute(text(sql)).scalar_one()


@pytest.fixture
def pair(make_client):
    return two_users(make_client)  # alice(작성자), bobby(신고자)


def test_requires_login(client):
    assert report(client, "study", 1).status_code == 401


# ---------- 신고하기 ----------


@pytest.mark.parametrize("kind", ["study", "todo", "error"])
def test_can_report_public_records_of_every_kind(pair, engine, kind):
    alice, bobby = pair
    record_id = post_record(alice, kind)
    response = report(bobby, kind, record_id)
    assert response.status_code == 201
    assert response.json() == {"message": "신고가 접수되었습니다."}
    assert count(engine) == 1


@pytest.mark.parametrize("kind", ["study", "error"])
def test_can_report_comments(pair, engine, kind):
    alice, bobby = pair
    record_id = post_record(alice, kind)
    comment_id = post_comment(alice, kind, record_id)
    assert report(bobby, "comment", comment_id).status_code == 201
    assert count(engine) == 1


def test_report_stores_reporter_target_and_reason(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id, "  욕설이 있습니다  ")
    with engine.connect() as connection:
        row = connection.execute(text("SELECT reporter_id, study_id, todo_id, error_id, comment_id, reason, created_at FROM reports")).one()
    assert (row.reporter_id, row.study_id, row.todo_id, row.error_id, row.comment_id) == (2, record_id, None, None, None)
    assert row.reason == "욕설이 있습니다"  # 앞뒤 공백 제거
    assert row.created_at is not None


# ---------- 신고 이유 ----------


@pytest.mark.parametrize("length,ok", [(1, True), (500, True), (0, False), (501, False)])
def test_reason_length_boundaries(pair, engine, length, ok):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    response = report(bobby, "study", record_id, "가" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.status_code == 422
        assert response.json()["errors"]["reason"] == "신고 이유는 1자 이상 500자 이하로 입력해 주세요."
    assert count(engine) == (1 if ok else 0)


def test_whitespace_only_reason_is_empty(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    assert report(bobby, "study", record_id, "     \n ").status_code == 422
    assert count(engine) == 0


def test_missing_fields(pair):
    _, bobby = pair
    assert bobby.post("/api/reports", json={}).status_code == 422
    assert report(bobby, "other", 1).status_code == 422


# ---------- 중복 신고 ----------


def test_cannot_report_same_target_twice(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id)
    again = report(bobby, "study", record_id, "다른 이유로 다시")
    assert again.status_code == 409
    assert again.json()["errors"]["target"] == "이미 신고한 대상입니다."
    assert count(engine) == 1


def test_different_users_can_report_same_target(make_client, engine):
    alice, bobby = two_users(make_client)
    carol = register_and_login(make_client(), "carol@example.com", "carol")
    record_id = post_record(alice, "error")
    assert report(bobby, "error", record_id).status_code == 201
    assert report(carol, "error", record_id).status_code == 201
    assert count(engine) == 2


def test_same_user_can_report_different_targets(pair, engine):
    alice, bobby = pair
    study_id, todo_id = post_record(alice, "study"), post_record(alice, "todo")
    assert report(bobby, "study", study_id).status_code == 201
    assert report(bobby, "todo", todo_id).status_code == 201
    assert count(engine) == 2


def test_same_numeric_id_of_different_kinds_are_different_targets(pair, engine):
    alice, bobby = pair
    study_id, todo_id, error_id = (post_record(alice, k) for k in ("study", "todo", "error"))
    assert study_id == todo_id == error_id == 1
    for kind in ("study", "todo", "error"):
        assert report(bobby, kind, 1).status_code == 201
    assert count(engine) == 3


def test_database_blocks_duplicates_even_if_code_is_bypassed(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id)
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text("INSERT INTO reports (reporter_id, study_id, reason, created_at) VALUES (2, :s, 'x', CURRENT_TIMESTAMP)"),
            {"s": record_id},
        )


# ---------- 신고할 수 없는 대상 ----------


@pytest.mark.parametrize("kind", ["study", "todo", "error"])
def test_cannot_report_private_records(pair, engine, kind):
    alice, bobby = pair
    record_id = post_record(alice, kind, is_public=False)
    assert report(bobby, kind, record_id).status_code == 404
    assert count(engine) == 0


def test_cannot_report_comment_on_private_record(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    comment_id = post_comment(alice, "study", record_id)
    alice.put(f"/api/studies/{record_id}", json={"title": "기록", "content": "내용", "is_public": False})
    assert report(bobby, "comment", comment_id).status_code == 404
    assert count(engine) == 0


@pytest.mark.parametrize("kind", ["study", "todo", "error", "comment"])
def test_cannot_report_missing_target(pair, kind):
    _, bobby = pair
    assert report(bobby, kind, 9999).status_code == 404


def test_database_rejects_report_without_or_with_multiple_targets(pair, engine):
    alice, _ = pair
    study_id, todo_id = post_record(alice, "study"), post_record(alice, "todo")
    for s, t in [(None, None), (study_id, todo_id)]:
        with engine.begin() as connection, pytest.raises(IntegrityError):
            connection.execute(
                text("INSERT INTO reports (reporter_id, study_id, todo_id, reason, created_at) VALUES (1, :s, :t, 'x', CURRENT_TIMESTAMP)"),
                {"s": s, "t": t},
            )


# ---------- 자동 삭제 없음, 신고 내용 비공개 ----------


def test_report_does_not_delete_or_hide_the_target(pair):
    alice, bobby = pair
    study_id = post_record(alice, "study")
    todo_id = post_record(alice, "todo")
    comment_id = post_comment(alice, "study", study_id)
    for kind, target in (("study", study_id), ("todo", todo_id), ("comment", comment_id)):
        report(bobby, kind, target)
    assert bobby.get(f"/api/studies/{study_id}").status_code == 200
    assert bobby.get(f"/api/todos/{todo_id}").status_code == 200
    assert [c["id"] for c in bobby.get(f"/api/studies/{study_id}/comments").json()["items"]] == [comment_id]
    assert len(bobby.get("/api/public").json()["items"]) == 2


def test_report_survives_when_target_becomes_private(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id)
    alice.put(f"/api/studies/{record_id}", json={"title": "기록", "content": "내용", "is_public": False})
    assert count(engine) == 1  # 신고 기록은 그대로 남아 운영자가 확인할 수 있다.


def test_no_endpoint_returns_report_data(pair):
    """일반 사용자는 신고 목록과 내용을 어떤 경로로도 볼 수 없다."""
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id, "비밀 신고 이유")
    for client in (alice, bobby):
        for path in ("/api/reports", "/api/reports/1", "/api/admin/reports", "/api/reports/mine"):
            assert client.get(path).status_code in (404, 405)
        for method in ("put", "patch", "delete"):
            assert getattr(client, method)("/api/reports/1").status_code in (404, 405)


def test_report_content_never_leaks_through_other_responses(pair):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id, "아무도 보면 안 되는 이유")
    responses = [
        alice.get(f"/api/studies/{record_id}"),
        alice.get("/api/studies"),
        alice.get("/api/public"),
        bobby.get(f"/api/studies/{record_id}"),
        bobby.get("/api/public"),
    ]
    for response in responses:
        assert "아무도 보면 안 되는 이유" not in response.text


def test_deleting_target_removes_its_report(pair, engine):
    alice, bobby = pair
    record_id = post_record(alice, "study")
    report(bobby, "study", record_id)
    alice.delete(f"/api/studies/{record_id}")
    assert count(engine) == 0
