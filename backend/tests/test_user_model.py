import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password, verify_password
from app.models.user import User


def make_user(email="a@example.com", nickname="alice", password="password1"):
    return User(email=email, password_hash=hash_password(password), nickname=nickname)


def test_can_save_users_with_different_email_and_nickname(db):
    db.add_all([make_user("a@example.com", "alice"), make_user("b@example.com", "bob_2")])
    db.commit()
    assert db.scalar(select(User).where(User.nickname == "alice")).email == "a@example.com"
    assert len(db.scalars(select(User)).all()) == 2


def test_created_at_is_saved_automatically(db):
    user = make_user()
    db.add(user)
    db.commit()
    assert user.created_at is not None


def test_duplicate_email_is_rejected(db):
    db.add(make_user("a@example.com", "alice"))
    db.commit()
    db.add(make_user("a@example.com", "bobby"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_email_is_lowercased_so_case_variants_are_duplicates(db):
    first = make_user("Alice@Example.com", "alice")
    assert first.email == "alice@example.com"
    db.add(first)
    db.commit()
    db.add(make_user("ALICE@example.COM", "bobby"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_nickname_is_rejected(db):
    db.add(make_user("a@example.com", "alice"))
    db.commit()
    db.add(make_user("b@example.com", "alice"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("nickname", ["ab", "a" * 20, "홍길동", "user_01", "가나다라마바사아자차카타파하가나다라마바"])
def test_valid_nicknames_are_accepted(nickname):
    assert make_user(nickname=nickname).nickname == nickname


@pytest.mark.parametrize(
    "nickname",
    ["", "a", "a" * 21, "has space", "a-b", "a.b", "a@b", "😀😀", "한 글"],
)
def test_invalid_nicknames_are_rejected(nickname):
    with pytest.raises(ValueError):
        make_user(nickname=nickname)


def test_nickname_surrounding_spaces_are_trimmed():
    assert make_user(nickname="  alice  ").nickname == "alice"


def test_nickname_length_is_also_checked_by_the_database(db):
    # 모델 검사를 거치지 않고 직접 넣어도 데이터베이스가 막아야 한다.
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO users (email, password_hash, nickname, created_at) "
                "VALUES ('x@example.com', 'h', 'a', CURRENT_TIMESTAMP)"
            )
        )


def test_password_plain_text_is_not_stored(db):
    db.add(make_user(password="my-secret-pw"))
    db.commit()
    stored = db.execute(text("SELECT password_hash FROM users")).scalar_one()
    assert "my-secret-pw" not in stored
    assert stored.startswith("$argon2")
    assert verify_password("my-secret-pw", stored)
    assert not verify_password("wrong-password", stored)


def test_verify_password_returns_false_for_garbage_hash():
    assert verify_password("anything", "not-a-hash") is False


def test_data_survives_reconnecting(engine):
    first = sessionmaker(bind=engine)()
    first.add(make_user())
    first.commit()
    first.close()
    engine.dispose()  # 연결을 모두 끊고 다시 여는 것은 서버를 껐다 켜는 것과 같다.
    second = sessionmaker(bind=engine)()
    assert second.scalar(select(User).where(User.email == "a@example.com")) is not None
    second.close()


def test_foreign_keys_are_enabled_on_sqlite(engine):
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    assert "users" in inspect(engine).get_table_names()
