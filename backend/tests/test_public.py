import pytest

from tests.helpers import register_and_login, two_users


def study(client, title, content="내용", **extra):
    r = client.post("/api/studies", json={"title": title, "content": content, **extra})
    assert r.status_code == 201
    return r.json()


def todo(client, title, **extra):
    r = client.post("/api/todos", json={"title": title, **extra})
    assert r.status_code == 201
    return r.json()


def error(client, title, content="오류 내용", **extra):
    r = client.post("/api/errors", json={"title": title, "content": content, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def public(client, **params):
    response = client.get("/api/public", params=params)
    assert response.status_code == 200
    return response.json()["items"]


def titles(client, **params):
    return [i["title"] for i in public(client, **params)]


@pytest.fixture
def pair(make_client):
    return two_users(make_client)  # (alice, bobby)


def test_requires_login(client):
    assert client.get("/api/public").status_code == 401


# ---------- 비공개 기록은 절대 섞이지 않는다 ----------


def test_private_records_never_appear(pair):
    alice, bobby = pair
    study(alice, "비공개 공부")
    todo(alice, "비공개 할 일")
    error(alice, "비공개 오류", solution="비공개 방법")
    assert public(bobby) == []
    assert public(alice) == []  # 내 비공개 기록도 공개 화면에는 나오지 않는다.


def test_private_records_never_appear_in_search(pair):
    alice, bobby = pair
    study(alice, "비밀 공부", content="키워드")
    todo(alice, "비밀 키워드 할 일")
    error(alice, "비밀 오류", content="키워드", solution="키워드")
    study(alice, "공개 공부", content="키워드", is_public=True)
    assert titles(bobby, q="키워드") == ["공개 공부"]
    for kind in ("study", "todo", "error"):
        assert all("비밀" not in t for t in titles(bobby, kind=kind, q="키워드"))


def test_private_record_does_not_appear_even_with_wildcard_search(pair):
    alice, bobby = pair
    study(alice, "비공개")
    study(alice, "공개", is_public=True)
    assert titles(bobby, q="%") == []
    assert titles(bobby, q="_") == []


def test_all_three_kinds_appear_when_public(pair):
    alice, bobby = pair
    study(alice, "공개 공부", is_public=True)
    todo(alice, "공개 할 일", is_public=True)
    error(alice, "공개 오류", is_public=True)
    kinds = {i["kind"] for i in public(bobby)}
    assert kinds == {"study", "todo", "error"}


def test_making_private_removes_it_immediately(pair):
    alice, bobby = pair
    record = study(alice, "토글", is_public=True)
    assert titles(bobby) == ["토글"]
    alice.put(f"/api/studies/{record['id']}", json={"title": "토글", "content": "내용", "is_public": False})
    assert titles(bobby) == []
    alice.put(f"/api/studies/{record['id']}", json={"title": "토글", "content": "내용", "is_public": True})
    assert titles(bobby) == ["토글"]


def test_deleted_record_disappears(pair):
    alice, bobby = pair
    record = todo(alice, "지울 것", is_public=True)
    alice.delete(f"/api/todos/{record['id']}")
    assert public(bobby) == []


# ---------- 목록 ----------


def test_newest_first_across_kinds(pair):
    alice, bobby = pair
    study(alice, "1번 공부", is_public=True)
    todo(bobby, "2번 할 일", is_public=True)
    error(alice, "3번 오류", is_public=True)
    study(bobby, "4번 공부", is_public=True)
    assert titles(alice) == ["4번 공부", "3번 오류", "2번 할 일", "1번 공부"]


def test_kind_filter(pair):
    alice, bobby = pair
    study(alice, "공부", is_public=True)
    todo(alice, "할 일", is_public=True)
    error(alice, "오류", is_public=True)
    assert titles(bobby, kind="study") == ["공부"]
    assert titles(bobby, kind="todo") == ["할 일"]
    assert titles(bobby, kind="error") == ["오류"]
    assert len(titles(bobby, kind="all")) == 3


def test_unknown_kind_is_rejected(pair):
    assert pair[0].get("/api/public", params={"kind": "other"}).status_code == 422


def test_item_fields(pair):
    alice, bobby = pair
    study(alice, "공부", content="가" * 300, is_public=True)
    t = todo(alice, "할 일", is_public=True)
    alice.put(f"/api/todos/{t['id']}/done", json={"is_done": True})
    error(alice, "오류", content="오류 내용", solution="방법", is_resolved=True, is_public=True)
    by_kind = {i["kind"]: i for i in public(bobby)}
    assert by_kind["study"]["preview"] == "가" * 100
    assert by_kind["study"]["author_nickname"] == "alice" and by_kind["study"]["is_mine"] is False
    assert by_kind["todo"]["is_done"] is True and by_kind["todo"]["preview"] is None
    assert by_kind["error"]["is_resolved"] is True and by_kind["error"]["preview"] == "오류 내용"
    assert by_kind["study"]["created_at"].endswith("Z")


def test_my_own_public_records_are_marked_as_mine(pair):
    alice, bobby = pair
    study(alice, "내 공개 기록", is_public=True)
    assert public(alice)[0]["is_mine"] is True
    assert public(bobby)[0]["is_mine"] is False


def test_author_nickname_is_current_nickname(pair):
    alice, bobby = pair
    study(alice, "공부", is_public=True)
    alice.patch("/api/auth/me/nickname", json={"nickname": "앨리스2"})
    assert public(bobby)[0]["author_nickname"] == "앨리스2"


# ---------- 검색 대상 필드 ----------


def test_study_search_covers_title_and_content(pair):
    alice, bobby = pair
    study(alice, "파이썬 기초", content="변수", is_public=True)
    study(alice, "자바", content="파이썬과 비교", is_public=True)
    study(alice, "무관", content="없음", is_public=True)
    assert sorted(titles(bobby, kind="study", q="파이썬")) == ["자바", "파이썬 기초"]


def test_todo_search_covers_title_only(pair):
    alice, bobby = pair
    todo(alice, "파이썬 복습", is_public=True)
    todo(alice, "자바 복습", is_public=True)
    assert titles(bobby, kind="todo", q="파이썬") == ["파이썬 복습"]


def test_error_search_covers_title_content_and_solution(pair):
    alice, bobby = pair
    error(alice, "제목에 키워드", is_public=True)
    error(alice, "다른 오류", content="내용에 키워드", is_public=True)
    error(alice, "또 다른 오류", solution="해결 방법에 키워드", is_public=True)
    error(alice, "무관한 오류", is_public=True)
    assert sorted(titles(bobby, kind="error", q="키워드")) == ["다른 오류", "또 다른 오류", "제목에 키워드"]


def test_search_in_all_view_spans_kinds(pair):
    alice, bobby = pair
    study(alice, "파이썬 공부", is_public=True)
    todo(alice, "파이썬 할 일", is_public=True)
    error(alice, "파이썬 오류", is_public=True)
    study(alice, "자바 공부", is_public=True)
    assert sorted(titles(bobby, q="파이썬")) == ["파이썬 공부", "파이썬 오류", "파이썬 할 일"]


def test_search_is_case_insensitive_and_trimmed(pair):
    alice, bobby = pair
    study(alice, "Python Basics", is_public=True)
    assert titles(bobby, q="  python ") == ["Python Basics"]


@pytest.mark.parametrize("q", ["", "   "])
def test_empty_search_returns_everything(pair, q):
    alice, bobby = pair
    study(alice, "하나", is_public=True)
    todo(alice, "둘", is_public=True)
    assert len(titles(bobby, q=q)) == 2


def test_wildcards_in_search_are_plain_characters(pair):
    alice, bobby = pair
    study(alice, "진도 100%", is_public=True)
    study(alice, "일반", is_public=True)
    assert titles(bobby, q="%") == ["진도 100%"]


def test_search_with_no_match(pair):
    alice, bobby = pair
    study(alice, "공부", is_public=True)
    assert public(bobby, q="없는단어") == []


# ---------- 읽기만 가능, 수정·삭제 불가 ----------


def test_public_items_can_be_read_but_not_changed_by_others(pair):
    alice, bobby = pair
    s = study(alice, "공개 공부", is_public=True)
    e = error(alice, "공개 오류", is_public=True)
    assert bobby.get(f"/api/studies/{s['id']}").status_code == 200
    assert bobby.get(f"/api/errors/{e['id']}").status_code == 200
    assert bobby.delete(f"/api/studies/{s['id']}").status_code == 403
    assert bobby.delete(f"/api/errors/{e['id']}").status_code == 403


def test_public_screen_has_no_write_endpoints(pair):
    alice, _ = pair
    for method in ("post", "put", "patch", "delete"):
        assert getattr(alice, method)("/api/public").status_code == 405
