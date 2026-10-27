import pytest

from tests.helpers import register_and_login, two_users


def create(client, title="저장 버튼 만들기", **extra):
    return client.post("/api/todos", json={"title": title, **extra})


def items(client, **params):
    response = client.get("/api/todos", params=params)
    assert response.status_code == 200
    return response.json()["items"]


def titles(client, **params):
    return [i["title"] for i in items(client, **params)]


@pytest.fixture
def me(client):
    return register_and_login(client)


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/todos"),
        ("get", "/api/todos"),
        ("get", "/api/todos/1"),
        ("put", "/api/todos/1"),
        ("put", "/api/todos/1/done"),
        ("delete", "/api/todos/1"),
    ],
)
def test_every_endpoint_requires_login(client, method, path):
    body = {"title": "t", "is_done": True}
    response = getattr(client, method)(path, **({"json": body} if method in ("post", "put") else {}))
    assert response.status_code == 401


# ---------- 만들기 ----------


def test_create_is_private_and_not_done_by_default(me):
    response = create(me)
    assert response.status_code == 201
    body = response.json()
    assert (body["is_done"], body["is_public"]) == (False, False)
    assert body["completed_at"] is None and body["updated_at"] is None
    assert body["is_mine"] is True and body["author_nickname"] == "alice"


def test_create_can_be_public(me):
    assert create(me, is_public=True).json()["is_public"] is True


@pytest.mark.parametrize("length,ok", [(1, True), (100, True), (0, False), (101, False)])
def test_create_title_length_boundaries(me, length, ok):
    response = create(me, "가" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.json()["errors"]["title"] == "제목은 1자 이상 100자 이하로 입력해 주세요."
        assert items(me) == []


def test_create_trims_outer_spaces_and_keeps_inner_spaces(me):
    assert create(me, "  파이썬   복습하기  ").json()["title"] == "파이썬   복습하기"


def test_create_rejects_whitespace_only_title(me):
    assert create(me, "     ").status_code == 422


def test_create_ignores_state_fields_sent_by_client(me):
    body = create(me, is_done=True, completed_at="2020-01-01T00:00:00Z").json()
    assert body["is_done"] is False and body["completed_at"] is None


# ---------- 목록 정렬 ----------


def test_list_puts_open_first_then_newest_first(me):
    ids = {name: create(me, name).json()["id"] for name in ["첫째", "둘째", "셋째", "넷째"]}
    me.put(f"/api/todos/{ids['둘째']}/done", json={"is_done": True})
    me.put(f"/api/todos/{ids['넷째']}/done", json={"is_done": True})
    # 미완료(최신순) → 완료(최신순)
    assert titles(me) == ["셋째", "첫째", "넷째", "둘째"]


def test_list_filters(me):
    a = create(me, "남은 일").json()["id"]
    b = create(me, "끝낸 일").json()["id"]
    me.put(f"/api/todos/{b}/done", json={"is_done": True})
    assert titles(me, filter="all") == ["남은 일", "끝낸 일"]
    assert titles(me) == ["남은 일", "끝낸 일"]  # 기본값은 전체
    assert titles(me, filter="open") == ["남은 일"]
    assert titles(me, filter="done") == ["끝낸 일"]
    assert a != b


def test_list_rejects_unknown_filter(me):
    assert me.get("/api/todos", params={"filter": "nonsense"}).status_code == 422


def test_list_only_contains_my_todos(make_client):
    alice, bobby = two_users(make_client)
    create(alice, "앨리스", is_public=True)
    create(bobby, "바비", is_public=True)
    assert titles(alice) == ["앨리스"]
    assert titles(bobby) == ["바비"]


def test_my_todos_cannot_be_searched(me):
    create(me, "파이썬")
    create(me, "자바")
    # 내 할 일 검색은 첫 버전에 없다. 검색어를 보내도 무시하고 전체를 돌려준다.
    assert sorted(titles(me, q="파이썬")) == ["자바", "파이썬"]


# ---------- 완료 체크 / 취소 ----------


def test_marking_done_saves_completed_time(me):
    todo = create(me).json()
    response = me.put(f"/api/todos/{todo['id']}/done", json={"is_done": True})
    assert response.status_code == 200
    body = response.json()
    assert body["is_done"] is True
    assert body["completed_at"] is not None and body["completed_at"].endswith("Z")
    assert body["updated_at"] is None  # 완료 체크는 '수정'이 아니다


def test_canceling_done_clears_completed_time(me):
    todo = create(me).json()
    me.put(f"/api/todos/{todo['id']}/done", json={"is_done": True})
    body = me.put(f"/api/todos/{todo['id']}/done", json={"is_done": False}).json()
    assert body["is_done"] is False and body["completed_at"] is None


def test_checking_done_twice_keeps_first_completed_time(me):
    todo = create(me).json()
    first = me.put(f"/api/todos/{todo['id']}/done", json={"is_done": True}).json()["completed_at"]
    second = me.put(f"/api/todos/{todo['id']}/done", json={"is_done": True}).json()["completed_at"]
    assert first == second


def test_done_requires_boolean(me):
    todo = create(me).json()
    assert me.put(f"/api/todos/{todo['id']}/done", json={}).status_code == 422


def test_done_on_missing_todo(me):
    assert me.put("/api/todos/9999/done", json={"is_done": True}).status_code == 404


def test_other_user_cannot_change_done_state(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice, "비공개").json()["id"]
    public_id = create(alice, "공개", is_public=True).json()["id"]
    assert bobby.put(f"/api/todos/{private_id}/done", json={"is_done": True}).status_code == 404
    assert bobby.put(f"/api/todos/{public_id}/done", json={"is_done": True}).status_code == 403
    assert [i["is_done"] for i in items(alice)] == [False, False]


# ---------- 읽기 ----------


def test_other_user_can_read_public_but_not_private_todo(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice, "비공개").json()["id"]
    public_id = create(alice, "공개", is_public=True).json()["id"]
    assert bobby.get(f"/api/todos/{private_id}").status_code == 404
    body = bobby.get(f"/api/todos/{public_id}").json()
    assert body["title"] == "공개" and body["is_mine"] is False and body["author_nickname"] == "alice"


# ---------- 수정 ----------


def test_update_changes_title_and_visibility_and_sets_updated_time(me):
    todo = create(me, "원래 제목").json()
    body = me.put(f"/api/todos/{todo['id']}", json={"title": "새 제목", "is_public": True}).json()
    assert (body["title"], body["is_public"]) == ("새 제목", True)
    assert body["updated_at"] is not None


def test_update_keeps_done_state(me):
    todo = create(me).json()
    me.put(f"/api/todos/{todo['id']}/done", json={"is_done": True})
    body = me.put(f"/api/todos/{todo['id']}", json={"title": "바뀐 제목"}).json()
    assert body["is_done"] is True and body["completed_at"] is not None


def test_update_applies_title_rules_and_failure_changes_nothing(me):
    todo = create(me, "그대로").json()
    for bad in ["", "   ", "가" * 101]:
        assert me.put(f"/api/todos/{todo['id']}", json={"title": bad}).status_code == 422
    saved = me.get(f"/api/todos/{todo['id']}").json()
    assert saved["title"] == "그대로" and saved["updated_at"] is None


def test_other_user_cannot_update_todo(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice, "비공개").json()["id"]
    public_id = create(alice, "공개", is_public=True).json()["id"]
    assert bobby.put(f"/api/todos/{private_id}", json={"title": "해킹"}).status_code == 404
    assert bobby.put(f"/api/todos/{public_id}", json={"title": "해킹"}).status_code == 403
    assert sorted(titles(alice)) == ["공개", "비공개"]


def test_making_todo_private_hides_it_from_others(make_client):
    alice, bobby = two_users(make_client)
    todo_id = create(alice, "토글", is_public=True).json()["id"]
    assert bobby.get(f"/api/todos/{todo_id}").status_code == 200
    alice.put(f"/api/todos/{todo_id}", json={"title": "토글", "is_public": False})
    assert bobby.get(f"/api/todos/{todo_id}").status_code == 404


# ---------- 삭제 ----------


def test_delete_removes_todo(me):
    todo_id = create(me).json()["id"]
    assert me.delete(f"/api/todos/{todo_id}").status_code == 204
    assert items(me) == []
    assert me.delete(f"/api/todos/{todo_id}").status_code == 404


def test_other_user_cannot_delete_todo(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice, "비공개").json()["id"]
    public_id = create(alice, "공개", is_public=True).json()["id"]
    assert bobby.delete(f"/api/todos/{private_id}").status_code == 404
    assert bobby.delete(f"/api/todos/{public_id}").status_code == 403
    assert len(items(alice)) == 2
