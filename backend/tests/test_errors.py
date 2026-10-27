import pytest

from tests.helpers import register_and_login, two_users

BASE = {"title": "ModuleNotFoundError", "content": "No module named 'requests'"}


def create(client, **overrides):
    return client.post("/api/errors", json={**BASE, **overrides})


def items(client, **params):
    response = client.get("/api/errors", params=params)
    assert response.status_code == 200
    return response.json()["items"]


def titles(client, **params):
    return [i["title"] for i in items(client, **params)]


def update(client, error_id, **overrides):
    return client.put(f"/api/errors/{error_id}", json={**BASE, **overrides})


@pytest.fixture
def me(client):
    return register_and_login(client)


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/errors"),
        ("get", "/api/errors"),
        ("get", "/api/errors/1"),
        ("put", "/api/errors/1"),
        ("delete", "/api/errors/1"),
    ],
)
def test_every_endpoint_requires_login(client, method, path):
    response = getattr(client, method)(path, **({"json": BASE} if method in ("post", "put") else {}))
    assert response.status_code == 401


# ---------- 만들기 ----------


def test_create_unresolved_without_solution(me):
    response = create(me)
    assert response.status_code == 201
    body = response.json()
    assert (body["is_resolved"], body["is_public"]) == (False, False)
    assert body["solution"] is None and body["resolved_at"] is None
    assert body["created_at"].endswith("Z") and body["updated_at"] is None
    assert body["author_nickname"] == "alice" and body["is_mine"] is True


def test_create_with_solution_but_unresolved_keeps_it(me):
    body = create(me, solution="pip install requests").json()
    assert body["solution"] == "pip install requests" and body["is_resolved"] is False


def test_create_directly_as_resolved_needs_solution(me):
    response = create(me, is_resolved=True)
    assert response.status_code == 422
    assert response.json()["errors"]["solution"] == "해결 방법을 입력해야 해결 상태로 바꿀 수 있습니다."
    assert items(me) == []


def test_create_directly_as_resolved_with_solution(me):
    body = create(me, is_resolved=True, solution="설치함").json()
    assert body["is_resolved"] is True and body["resolved_at"].endswith("Z")


@pytest.mark.parametrize("length,ok", [(1, True), (100, True), (0, False), (101, False)])
def test_title_length_boundaries(me, length, ok):
    response = create(me, title="가" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.json()["errors"]["title"] == "오류 제목은 1자 이상 100자 이하로 입력해 주세요."


@pytest.mark.parametrize("length,ok", [(1, True), (5000, True), (0, False), (5001, False)])
def test_content_length_boundaries(me, length, ok):
    response = create(me, content="a" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.json()["errors"]["content"] == "오류 내용은 1자 이상 5,000자 이하로 입력해 주세요."


@pytest.mark.parametrize("length,ok", [(1, True), (5000, True), (5001, False)])
def test_solution_length_boundaries(me, length, ok):
    response = create(me, solution="a" * length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert "해결 방법" in response.json()["errors"]["solution"]


@pytest.mark.parametrize("empty", [None, "", "   \n "])
def test_empty_solution_is_stored_as_empty(me, empty):
    assert create(me, solution=empty).json()["solution"] is None


def test_trims_outer_spaces_and_keeps_inner_spaces(me):
    body = create(me, title="  오류   제목  ", content="  첫줄\n둘째   줄  ", solution="  방법 1  ").json()
    assert (body["title"], body["content"], body["solution"]) == ("오류   제목", "첫줄\n둘째   줄", "방법 1")


@pytest.mark.parametrize("field", ["title", "content"])
def test_whitespace_only_required_fields_are_rejected(me, field):
    assert create(me, **{field: "    "}).status_code == 422


# ---------- 목록·필터·검색 ----------


def test_list_newest_first(me):
    for t in ["첫째", "둘째", "셋째"]:
        create(me, title=t)
    assert titles(me) == ["셋째", "둘째", "첫째"]


def test_filters(me):
    open_id = create(me, title="미해결 오류").json()["id"]
    create(me, title="해결한 오류", solution="고침", is_resolved=True)
    assert open_id
    assert titles(me, filter="all") == ["해결한 오류", "미해결 오류"]
    assert titles(me, filter="unresolved") == ["미해결 오류"]
    assert titles(me, filter="resolved") == ["해결한 오류"]


def test_unknown_filter_is_rejected(me):
    assert me.get("/api/errors", params={"filter": "x"}).status_code == 422


def test_search_by_title_and_content_only(me):
    create(me, title="Import 오류", content="requests가 없다", solution="pip로 설치")
    create(me, title="다른 오류", content="관계 없음")
    assert titles(me, q="import") == ["Import 오류"]  # 대소문자 무시
    assert titles(me, q="requests") == ["Import 오류"]  # 오류 내용
    assert titles(me, q="pip") == []  # 내 오류 검색은 해결 방법을 보지 않는다
    assert len(titles(me, q="  ")) == 2


def test_search_combines_with_filter(me):
    create(me, title="파이썬 오류 A")
    create(me, title="파이썬 오류 B", solution="해결", is_resolved=True)
    assert titles(me, q="파이썬", filter="resolved") == ["파이썬 오류 B"]
    assert titles(me, q="파이썬", filter="unresolved") == ["파이썬 오류 A"]


def test_search_treats_wildcards_as_plain_characters(me):
    create(me, title="100% 실패")
    create(me, title="일반 오류")
    assert titles(me, q="%") == ["100% 실패"]


def test_list_and_search_never_include_other_users_records(make_client):
    alice, bobby = two_users(make_client)
    create(bobby, title="공유 오류 공개", is_public=True)
    create(bobby, title="공유 오류 비공개")
    create(alice, title="공유 오류 내 것")
    assert titles(alice) == ["공유 오류 내 것"]
    assert titles(alice, q="공유 오류") == ["공유 오류 내 것"]


# ---------- 해결 처리 / 되돌리기 ----------


def test_resolving_requires_solution_and_saves_resolved_time(me):
    error_id = create(me).json()["id"]
    assert update(me, error_id, is_resolved=True).status_code == 422
    assert update(me, error_id, is_resolved=True, solution="   ").status_code == 422
    assert me.get(f"/api/errors/{error_id}").json()["is_resolved"] is False

    body = update(me, error_id, is_resolved=True, solution="pip install requests").json()
    assert body["is_resolved"] is True
    assert body["solution"] == "pip install requests"
    assert body["resolved_at"].endswith("Z")
    assert body["updated_at"] is not None


def test_unresolving_keeps_solution_and_clears_resolved_time(me):
    error_id = create(me, solution="방법", is_resolved=True).json()["id"]
    body = update(me, error_id, solution="방법", is_resolved=False).json()
    assert body["is_resolved"] is False
    assert body["solution"] == "방법"
    assert body["resolved_at"] is None


def test_editing_a_resolved_error_keeps_original_resolved_time(me):
    created = create(me, solution="방법", is_resolved=True).json()
    body = update(me, created["id"], title="제목 수정", solution="더 나은 방법", is_resolved=True).json()
    assert body["resolved_at"] == created["resolved_at"]
    assert body["solution"] == "더 나은 방법"


def test_resolved_error_cannot_lose_its_solution(me):
    error_id = create(me, solution="방법", is_resolved=True).json()["id"]
    assert update(me, error_id, solution="", is_resolved=True).status_code == 422
    assert me.get(f"/api/errors/{error_id}").json()["solution"] == "방법"


def test_resolve_then_unresolve_then_resolve_again(me):
    error_id = create(me).json()["id"]
    first = update(me, error_id, solution="방법", is_resolved=True).json()["resolved_at"]
    update(me, error_id, solution="방법", is_resolved=False)
    second = update(me, error_id, solution="방법", is_resolved=True).json()["resolved_at"]
    assert first and second


# ---------- 읽기 / 수정 / 삭제 권한 ----------


def test_update_applies_rules_and_failure_changes_nothing(me):
    error_id = create(me, title="그대로", solution="방법").json()["id"]
    for bad in [{"title": ""}, {"title": "가" * 101}, {"content": ""}, {"content": "a" * 5001}, {"solution": "a" * 5001}]:
        assert update(me, error_id, **bad).status_code == 422
    saved = me.get(f"/api/errors/{error_id}").json()
    # 실패한 수정은 제목·해결 방법·수정 시각 모두 바꾸지 않는다.
    assert (saved["title"], saved["solution"], saved["updated_at"]) == ("그대로", "방법", None)


def test_update_sets_updated_time_and_keeps_created_time(me):
    created = create(me).json()
    body = update(me, created["id"], title="새 제목", is_public=True).json()
    assert body["title"] == "새 제목" and body["is_public"] is True
    assert body["updated_at"] is not None and body["created_at"] == created["created_at"]


def test_other_user_visibility_and_permissions(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice, title="비공개").json()["id"]
    public_id = create(alice, title="공개", is_public=True).json()["id"]

    assert bobby.get(f"/api/errors/{private_id}").status_code == 404
    seen = bobby.get(f"/api/errors/{public_id}").json()
    assert seen["author_nickname"] == "alice" and seen["is_mine"] is False

    assert update(bobby, private_id, title="해킹").status_code == 404
    assert update(bobby, public_id, title="해킹").status_code == 403
    assert bobby.delete(f"/api/errors/{private_id}").status_code == 404
    assert bobby.delete(f"/api/errors/{public_id}").status_code == 403
    assert sorted(titles(alice)) == ["공개", "비공개"]


def test_other_user_cannot_resolve_my_error(make_client):
    alice, bobby = two_users(make_client)
    public_id = create(alice, is_public=True).json()["id"]
    assert update(bobby, public_id, solution="방법", is_resolved=True).status_code == 403
    assert alice.get(f"/api/errors/{public_id}").json()["is_resolved"] is False


def test_making_private_hides_from_others_again(make_client):
    alice, bobby = two_users(make_client)
    error_id = create(alice, is_public=True).json()["id"]
    assert bobby.get(f"/api/errors/{error_id}").status_code == 200
    update(alice, error_id, is_public=False)
    assert bobby.get(f"/api/errors/{error_id}").status_code == 404


def test_delete(me):
    error_id = create(me).json()["id"]
    assert me.delete(f"/api/errors/{error_id}").status_code == 204
    assert me.get(f"/api/errors/{error_id}").status_code == 404
    assert items(me) == []
    assert me.delete(f"/api/errors/{error_id}").status_code == 404
