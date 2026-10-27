from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트(buildlog/)의 .env 파일을 읽는다.
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    # 데이터베이스 파일 위치는 Phase 3에서 확정한다.
    database_url: str = "sqlite:///database/buildlog.test.sqlite3"
    secret_key: str
    # 쉼표로 구분한 화면 주소 목록
    cors_origins: str = "http://localhost:5173"
    # 로그인 상태를 유지하는 시간(분). 기본 7일
    access_token_expire_minutes: int = 60 * 24 * 7

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
