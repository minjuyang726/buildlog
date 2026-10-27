from alembic import op


def enable_row_level_security(*table_names: str) -> None:
    """Supabase(PostgreSQL)에서만 테이블의 외부 직접 접근을 막는다.

    Row Level Security를 켜고 접근 허용 규칙을 만들지 않으면, Supabase가 기본으로 제공하는
    공개 통로(공개 키)로는 데이터를 읽을 수 없고 서버(FastAPI)만 접근할 수 있다.
    SQLite에서는 아무 일도 하지 않는다. 새 테이블을 만드는 마이그레이션마다 호출한다.
    """
    if op.get_bind().dialect.name != "postgresql":
        return
    for name in table_names:
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
