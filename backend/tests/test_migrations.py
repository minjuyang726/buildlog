from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db.session import make_engine

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def table_names(url: str) -> set[str]:
    engine = make_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_upgrade_creates_users_table(db_url):
    command.upgrade(alembic_config(db_url), "head")
    assert "users" in table_names(db_url)


def test_migration_matches_model_columns(db_url):
    command.upgrade(alembic_config(db_url), "head")
    engine = make_engine(db_url)
    try:
        columns = {c["name"] for c in inspect(engine).get_columns("users")}
    finally:
        engine.dispose()
    assert columns == {"id", "email", "password_hash", "nickname", "created_at"}


def test_upgrade_creates_all_tables(db_url):
    command.upgrade(alembic_config(db_url), "head")
    assert table_names(db_url) >= {"users", "studies", "todos", "error_records", "alembic_version"}


def test_model_tables_match_migrated_tables(tmp_path, engine):
    """모델에 적은 테이블·칸과 마이그레이션 결과가 서로 같아야 한다."""
    migrated_url = f"sqlite:///{(tmp_path / 'migrated.sqlite3').as_posix()}"
    command.upgrade(alembic_config(migrated_url), "head")
    migrated = make_engine(migrated_url)
    try:
        for table in ("users", "studies", "todos", "error_records"):
            from_migration = {c["name"] for c in inspect(migrated).get_columns(table)}
            from_models = {c["name"] for c in inspect(engine).get_columns(table)}
            assert from_migration == from_models, table
    finally:
        migrated.dispose()


def test_downgrade_and_upgrade_again_work(db_url):
    config = alembic_config(db_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert table_names(db_url) == {"alembic_version"}
    command.upgrade(config, "head")
    assert {"users", "studies", "todos", "error_records"} <= table_names(db_url)
