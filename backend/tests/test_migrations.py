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


def test_downgrade_and_upgrade_again_work(db_url):
    config = alembic_config(db_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert "users" not in table_names(db_url)
    command.upgrade(config, "head")
    assert "users" in table_names(db_url)
