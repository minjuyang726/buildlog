from logging.config import fileConfig

from alembic import context
from app.core.config import settings
from app.db.base import Base
from app.db.session import make_engine, resolve_database_url
import app.models  # noqa: F401  (모든 테이블을 Base에 등록)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_url() -> str:
    # 테스트처럼 직접 주소를 넘긴 경우를 우선하고, 없으면 .env의 DATABASE_URL을 쓴다.
    return resolve_database_url(config.get_main_option("sqlalchemy.url") or settings.database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = make_engine(get_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite는 테이블 변경 기능이 제한적이라 변경 시 테이블을 새로 만드는 방식을 쓴다.
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
