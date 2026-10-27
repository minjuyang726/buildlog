import pytest

from tests.helpers import register_and_login, two_users

VALID = {"title": "파이썬 복습", "content": "for문과 while문을 정리했다."}


def create(client, **overrides):
    return client.post("/api/studies", json={**VALID, **overrides})


def titles(client, **params):
    response = client.get("/api/studies", params=params)
    assert response.status_code == 200
    return [item["title"] for item in response.json()["items"]]


@pytest.fixture
def me(client):
    return register_and_login(client)


# ---------- 로그인 필요 ----------


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/studies"),
        ("get", "/api/studies"),
        ("get", "/api/studies/1"),
        ("put", "/api/studies/1"),
        ("delete", "/api/studies/1"),
    ],
)
def test_every_endpoint_requires_login(client, method, path):
    response = getattr(client, method)(path, **({"json": VALID} if method in ("post", "put") else {}))
    assert response.status_code == 401


# ---------- 만들기 ----------


def test_create_saves_study_as_private_by_default(me):
    response = create(me)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "파이썬 복습"
    assert body["is_public"] is False
    assert body["is_mine"] is True
    assert body["author_nickname"] == "alice"
    assert body["created_at"].endswith("Z")  # 작성 날짜·시간이 자동으로 저장됨 (UTC 표시)
    assert body["updated_at"] is None


def test_create_can_be_public(me):
    assert create(me, is_public=True).json()["is_public"] is True


@pytest.mark.parametrize("title_length,content_length,ok", [(1, 1, True), (100, 5000, True), (0, 1, False), (101, 1, False), (1, 0, False), (1, 5001, False)])
def test_create_length_boundaries(me, title_length, content_length, ok):
    response = create(me, title="가" * title_length, content="나" * content_length)
    assert (response.status_code == 201) is ok
    if not ok:
        assert response.status_code == 422
        assert titles(me) == []  # 저장되지 않음


def test_create_error_messages_name_the_field(me):
    errors = create(me, title="", content="x" * 5001).json()["errors"]
    assert errors["title"] == "제목은 1자 이상 100자 이하로 입력해 주세요."
    assert errors["content"] == "내용은 1자 이상 5,000자 이하로 입력해 주세요."


def test_create_trims_outer_spaces_and_keeps_inner_spacing(me):
    body = create(me, title="  제목   입니다  ", content="\n  첫째 줄\n\n둘째   줄  \n").json()
    assert body["title"] == "제목   입니다"
    assert body["content"] == "첫째 줄\n\n둘째   줄"


@pytest.mark.parametrize("field", ["title", "content"])
def test_create_rejects_whitespace_only(me, field):
    assert create(me, **{field: "   \n  "}).status_code == 422


def test_create_missing_fields(me):
    response = me.post("/api/studies", json={})
    assert response.status_code == 422
    assert set(response.json()["errors"]) == {"title", "content"}


# ---------- 목록 ----------


def test_list_shows_newest_first(me):
    for title in ["첫째", "둘째", "셋째"]:
        create(me, title=title)
    assert titles(me) == ["셋째", "둘째", "첫째"]


def test_list_item_has_preview_and_flags(me):
    create(me, content="가" * 300, is_public=True)
    item = me.get("/api/studies").json()["items"][0]
    assert item["preview"] == "가" * 100
    assert item["is_public"] is True


def test_list_is_empty_for_new_user(me):
    assert titles(me) == []


def test_list_only_contains_my_studies(make_client):
    alice, bobby = two_users(make_client)
    create(alice, title="앨리스 것", is_public=True)
    create(bobby, title="바비 것", is_public=True)
    assert titles(alice) == ["앨리스 것"]
    assert titles(bobby) == ["바비 것"]


# ---------- 검색 ----------


def test_search_finds_by_title_and_by_content(me):
    create(me, title="파이썬 기초", content="변수")
    create(me, title="자바스크립트", content="파이썬과 비교")
    create(me, title="알고리즘", content="정렬")
    assert titles(me, q="파이썬") == ["자바스크립트", "파이썬 기초"]
    assert titles(me, q="변수") == ["파이썬 기초"]
    assert titles(me, q="알고리즘") == ["알고리즘"]


def test_search_is_case_insensitive(me):
    create(me, title="Python Basics", content="x")
    assert titles(me, q="python") == ["Python Basics"]
    assert titles(me, q="BASICS") == ["Python Basics"]


def test_search_with_no_match_returns_empty_list(me):
    create(me)
    assert titles(me, q="없는단어") == []


@pytest.mark.parametrize("q", ["", "   "])
def test_empty_search_returns_everything(me, q):
    create(me, title="하나")
    create(me, title="둘")
    assert len(titles(me, q=q)) == 2


def test_search_trims_spaces(me):
    create(me, title="파이썬")
    assert titles(me, q="  파이썬  ") == ["파이썬"]


def test_search_treats_percent_and_underscore_as_plain_characters(me):
    create(me, title="진도 100% 완료")
    create(me, title="변수_이름")
    create(me, title="아무거나")
    assert titles(me, q="%") == ["진도 100% 완료"]
    assert titles(me, q="_") == ["변수_이름"]


def test_search_never_returns_other_users_studies(make_client):
    alice, bobby = two_users(make_client)
    create(bobby, title="공유 키워드 공개", is_public=True)
    create(bobby, title="공유 키워드 비공개")
    create(alice, title="공유 키워드 내 것")
    assert titles(alice, q="공유 키워드") == ["공유 키워드 내 것"]


# ---------- 읽기 ----------


def test_read_own_study(me):
    study_id = create(me, is_public=False).json()["id"]
    response = me.get(f"/api/studies/{study_id}")
    assert response.status_code == 200
    assert response.json()["content"] == VALID["content"]


def test_read_missing_study(me):
    assert me.get("/api/studies/9999").status_code == 404


def test_other_user_cannot_read_private_study(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice).json()["id"]
    response = bobby.get(f"/api/studies/{study_id}")
    assert response.status_code == 404
    # 없는 기록과 똑같이 응답해서 존재 여부도 알 수 없다.
    assert response.json() == bobby.get("/api/studies/9999").json()


def test_other_user_can_read_public_study(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice, is_public=True).json()["id"]
    body = bobby.get(f"/api/studies/{study_id}").json()
    assert body["title"] == VALID["title"]
    assert body["author_nickname"] == "alice"
    assert body["is_mine"] is False


def test_making_it_private_again_hides_it_from_others(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice, is_public=True).json()["id"]
    assert bobby.get(f"/api/studies/{study_id}").status_code == 200
    alice.put(f"/api/studies/{study_id}", json={**VALID, "is_public": False})
    assert bobby.get(f"/api/studies/{study_id}").status_code == 404
    alice.put(f"/api/studies/{study_id}", json={**VALID, "is_public": True})
    assert bobby.get(f"/api/studies/{study_id}").status_code == 200


def test_public_study_shows_current_nickname_after_change(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice, is_public=True).json()["id"]
    alice.patch("/api/auth/me/nickname", json={"nickname": "앨리스2"})
    assert bobby.get(f"/api/studies/{study_id}").json()["author_nickname"] == "앨리스2"


# ---------- 수정 ----------


def test_update_changes_fields_and_sets_updated_time(me):
    created = create(me).json()
    response = me.put(f"/api/studies/{created['id']}", json={"title": "새 제목", "content": "새 내용", "is_public": True})
    assert response.status_code == 200
    body = response.json()
    assert (body["title"], body["content"], body["is_public"]) == ("새 제목", "새 내용", True)
    assert body["updated_at"] is not None and body["updated_at"].endswith("Z")
    assert body["created_at"] == created["created_at"]  # 작성 시각은 그대로


def test_update_applies_same_length_rules(me):
    study_id = create(me).json()["id"]
    for bad in [{"title": ""}, {"title": "가" * 101}, {"content": ""}, {"content": "가" * 5001}, {"title": "   "}]:
        response = me.put(f"/api/studies/{study_id}", json={**VALID, **bad})
        assert response.status_code == 422
    # 실패한 수정은 기존 기록을 바꾸지 않는다.
    saved = me.get(f"/api/studies/{study_id}").json()
    assert (saved["title"], saved["content"], saved["updated_at"]) == (VALID["title"], VALID["content"], None)


def test_update_missing_study(me):
    assert me.put("/api/studies/9999", json=VALID).status_code == 404


def test_other_user_cannot_update_private_study(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice).json()["id"]
    assert bobby.put(f"/api/studies/{study_id}", json={**VALID, "title": "해킹"}).status_code == 404
    assert alice.get(f"/api/studies/{study_id}").json()["title"] == VALID["title"]


def test_other_user_cannot_update_public_study(make_client):
    alice, bobby = two_users(make_client)
    study_id = create(alice, is_public=True).json()["id"]
    response = bobby.put(f"/api/studies/{study_id}", json={**VALID, "title": "해킹"})
    assert response.status_code == 403
    assert alice.get(f"/api/studies/{study_id}").json()["title"] == VALID["title"]


# ---------- 삭제 ----------


def test_delete_removes_study(me):
    study_id = create(me).json()["id"]
    assert me.delete(f"/api/studies/{study_id}").status_code == 204
    assert me.get(f"/api/studies/{study_id}").status_code == 404
    assert titles(me) == []


def test_delete_missing_study(me):
    assert me.delete("/api/studies/9999").status_code == 404


def test_other_user_cannot_delete_private_or_public_study(make_client):
    alice, bobby = two_users(make_client)
    private_id = create(alice).json()["id"]
    public_id = create(alice, title="공개", is_public=True).json()["id"]
    assert bobby.delete(f"/api/studies/{private_id}").status_code == 404
    assert bobby.delete(f"/api/studies/{public_id}").status_code == 403
    assert sorted(titles(alice)) == sorted([VALID["title"], "공개"])
