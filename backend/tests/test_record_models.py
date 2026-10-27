import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.error_record import ErrorRecord
from app.models.study import Study
from app.models.todo import Todo
from app.models.user import User


@pytest.fixture
def user(db):
    u = User(email="a@example.com", password_hash=hash_password("password1"), nickname="alice")
    db.add(u)
    db.commit()
    return u


def save(db, obj):
    db.add(obj)
    db.commit()
    return obj


# ---------- 공통: 저장하고 다시 읽기, 기본 상태 ----------


def test_study_is_saved_with_defaults(db, user):
    study = save(db, Study(user_id=user.id, title="파이썬 복습", content="for문 정리"))
    saved = db.get(Study, study.id)
    assert (saved.title, saved.content) == ("파이썬 복습", "for문 정리")
    assert saved.is_public is False  # 기본 비공개
    assert saved.created_at is not None  # 작성 날짜·시간 자동 저장
    assert saved.updated_at is None  # 수정한 적이 없으면 비어 있음


def test_todo_is_saved_with_defaults(db, user):
    todo = save(db, Todo(user_id=user.id, title="저장 버튼 만들기"))
    saved = db.get(Todo, todo.id)
    assert saved.is_done is False  # 새 할 일은 미완료
    assert saved.is_public is False  # 기본 비공개
    assert saved.completed_at is None
    assert saved.created_at is not None


def test_error_record_is_saved_with_defaults(db, user):
    record = save(db, ErrorRecord(user_id=user.id, title="ModuleNotFoundError", content="No module named x"))
    saved = db.get(ErrorRecord, record.id)
    assert saved.is_resolved is False  # 새 오류는 미해결
    assert saved.is_public is False  # 기본 비공개
    assert saved.solution is None  # 해결 방법은 비워 둘 수 있음
    assert saved.resolved_at is None


# ---------- 글자 수 조건 (입력 검사) ----------


@pytest.mark.parametrize("model,fields", [(Study, {"content": "내용"}), (Todo, {}), (ErrorRecord, {"content": "내용"})])
@pytest.mark.parametrize("length,ok", [(1, True), (100, True), (0, False), (101, False)])
def test_title_length_boundaries(model, fields, length, ok):
    if ok:
        assert len(model(user_id=1, title="가" * length, **fields).title) == length
    else:
        with pytest.raises(ValueError):
            model(user_id=1, title="가" * length, **fields)


@pytest.mark.parametrize("model", [Study, Todo, ErrorRecord])
def test_title_with_only_spaces_is_empty(model):
    extra = {} if model is Todo else {"content": "내용"}
    with pytest.raises(ValueError):
        model(user_id=1, title="    ", **extra)


@pytest.mark.parametrize("model", [Study, Todo, ErrorRecord])
def test_title_surrounding_spaces_are_trimmed_but_inner_spaces_stay(model):
    extra = {} if model is Todo else {"content": "내용"}
    assert model(user_id=1, title="  저장  버튼  ", **extra).title == "저장  버튼"


@pytest.mark.parametrize("model,title", [(Study, "제목"), (ErrorRecord, "오류")])
@pytest.mark.parametrize("length,ok", [(1, True), (5000, True), (0, False), (5001, False)])
def test_content_length_boundaries(model, title, length, ok):
    if ok:
        assert len(model(user_id=1, title=title, content="a" * length).content) == length
    else:
        with pytest.raises(ValueError):
            model(user_id=1, title=title, content="a" * length)


def test_content_with_only_spaces_is_empty():
    with pytest.raises(ValueError):
        Study(user_id=1, title="제목", content="   \n  ")


@pytest.mark.parametrize("length,ok", [(1, True), (5000, True), (5001, False)])
def test_solution_length_boundaries(length, ok):
    if ok:
        assert len(ErrorRecord(user_id=1, title="t", content="c", solution="a" * length).solution) == length
    else:
        with pytest.raises(ValueError):
            ErrorRecord(user_id=1, title="t", content="c", solution="a" * length)


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_empty_solution_is_stored_as_empty(empty):
    assert ErrorRecord(user_id=1, title="t", content="c", solution=empty).solution is None


# ---------- 할 일: 완료 / 취소 ----------


def test_todo_mark_done_sets_completed_time(db, user):
    todo = save(db, Todo(user_id=user.id, title="할 일"))
    todo.mark_done()
    db.commit()
    saved = db.get(Todo, todo.id)
    assert saved.is_done is True
    assert saved.completed_at is not None


def test_todo_mark_undone_clears_completed_time(db, user):
    todo = save(db, Todo(user_id=user.id, title="할 일"))
    todo.mark_done()
    db.commit()
    todo.mark_undone()
    db.commit()
    saved = db.get(Todo, todo.id)
    assert saved.is_done is False
    assert saved.completed_at is None


def test_marking_done_twice_keeps_first_completed_time(db, user):
    todo = save(db, Todo(user_id=user.id, title="할 일"))
    todo.mark_done()
    first = todo.completed_at
    todo.mark_done()
    assert todo.completed_at == first


# ---------- 오류 기록: 해결 / 미해결 ----------


def test_error_cannot_be_resolved_without_solution():
    record = ErrorRecord(user_id=1, title="t", content="c")
    with pytest.raises(ValueError):
        record.mark_resolved()
    with pytest.raises(ValueError):
        record.mark_resolved("   ")
    assert not record.is_resolved


def test_error_mark_resolved_saves_solution_and_resolved_time(db, user):
    record = save(db, ErrorRecord(user_id=user.id, title="t", content="c"))
    record.mark_resolved("패키지를 설치했다")
    db.commit()
    saved = db.get(ErrorRecord, record.id)
    assert saved.is_resolved is True
    assert saved.solution == "패키지를 설치했다"
    assert saved.resolved_at is not None


def test_error_can_be_resolved_with_solution_written_earlier(db, user):
    record = save(db, ErrorRecord(user_id=user.id, title="t", content="c", solution="미리 적은 방법"))
    record.mark_resolved()
    db.commit()
    assert db.get(ErrorRecord, record.id).is_resolved is True


def test_error_mark_unresolved_keeps_solution_and_clears_resolved_time(db, user):
    record = save(db, ErrorRecord(user_id=user.id, title="t", content="c"))
    record.mark_resolved("해결 방법")
    db.commit()
    record.mark_unresolved()
    db.commit()
    saved = db.get(ErrorRecord, record.id)
    assert saved.is_resolved is False
    assert saved.solution == "해결 방법"  # 해결 방법은 유지
    assert saved.resolved_at is None  # 해결 날짜·시간만 지움


# ---------- 데이터베이스가 직접 막는 규칙 (모델 검사를 거치지 않는 경우) ----------

NOW = "'2026-01-01 00:00:00'"


def raw(db, sql):
    db.execute(text(sql))
    db.commit()


def test_db_rejects_overlong_title(db, user):
    with pytest.raises(IntegrityError):
        raw(db, f"INSERT INTO studies (user_id, title, content, created_at) VALUES ({user.id}, '{'a' * 101}', 'c', {NOW})")


def test_db_rejects_empty_content(db, user):
    with pytest.raises(IntegrityError):
        raw(db, f"INSERT INTO studies (user_id, title, content, created_at) VALUES ({user.id}, 't', '', {NOW})")


def test_db_rejects_done_todo_without_completed_time(db, user):
    with pytest.raises(IntegrityError):
        raw(db, f"INSERT INTO todos (user_id, title, is_done, created_at) VALUES ({user.id}, 't', 1, {NOW})")


def test_db_rejects_undone_todo_with_completed_time(db, user):
    with pytest.raises(IntegrityError):
        raw(db, f"INSERT INTO todos (user_id, title, is_done, completed_at, created_at) VALUES ({user.id}, 't', 0, {NOW}, {NOW})")


def test_db_rejects_resolved_error_without_solution(db, user):
    with pytest.raises(IntegrityError):
        raw(
            db,
            "INSERT INTO error_records (user_id, title, content, is_resolved, resolved_at, created_at) "
            f"VALUES ({user.id}, 't', 'c', 1, {NOW}, {NOW})",
        )


def test_db_rejects_resolved_error_without_resolved_time(db, user):
    with pytest.raises(IntegrityError):
        raw(
            db,
            "INSERT INTO error_records (user_id, title, content, solution, is_resolved, created_at) "
            f"VALUES ({user.id}, 't', 'c', 's', 1, {NOW})",
        )


def test_db_rejects_empty_string_solution(db, user):
    with pytest.raises(IntegrityError):
        raw(
            db,
            "INSERT INTO error_records (user_id, title, content, solution, created_at) "
            f"VALUES ({user.id}, 't', 'c', '', {NOW})",
        )


# ---------- 작성자 연결 ----------


@pytest.mark.parametrize("model,extra", [(Study, {"content": "c"}), (Todo, {}), (ErrorRecord, {"content": "c"})])
def test_record_must_belong_to_existing_user(db, model, extra):
    db.add(model(user_id=9999, title="t", **extra))
    with pytest.raises(IntegrityError):
        db.commit()


def test_record_requires_an_author(db):
    db.add(Study(title="t", content="c"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_user_removes_their_records(db, user):
    save(db, Study(user_id=user.id, title="t", content="c"))
    save(db, Todo(user_id=user.id, title="t"))
    save(db, ErrorRecord(user_id=user.id, title="t", content="c"))
    db.delete(user)
    db.commit()
    for model in (Study, Todo, ErrorRecord):
        assert db.scalars(select(model)).all() == []


def test_records_of_different_users_stay_separate(db, user):
    other = save(db, User(email="b@example.com", password_hash="h", nickname="bobby"))
    save(db, Study(user_id=user.id, title="내 것", content="c"))
    save(db, Study(user_id=other.id, title="남의 것", content="c"))
    mine = db.scalars(select(Study).where(Study.user_id == user.id)).all()
    assert [s.title for s in mine] == ["내 것"]


# ---------- 다시 연결해도 데이터가 남아 있음 ----------


def test_records_survive_reconnecting(engine, user):
    session = sessionmaker(bind=engine)()
    save(session, Study(user_id=user.id, title="공부", content="내용"))
    save(session, Todo(user_id=user.id, title="할 일"))
    save(session, ErrorRecord(user_id=user.id, title="오류", content="내용"))
    session.close()
    engine.dispose()
    again = sessionmaker(bind=engine)()
    assert again.scalar(select(Study.title)) == "공부"
    assert again.scalar(select(Todo.title)) == "할 일"
    assert again.scalar(select(ErrorRecord.title)) == "오류"
    again.close()
