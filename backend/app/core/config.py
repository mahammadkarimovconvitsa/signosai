from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    database_url: str
    test_database_url: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    first_admin_email: str = "admin@signos.local"
    first_admin_password: str = "change-me-admin-password"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    agent_timeout_seconds: int = 10

    rate_limit_auth_per_minute: int = 10
    rate_limit_ingestion_per_minute: int = 60
    rate_limit_admin_per_minute: int = 20

    alarm_worker_poll_seconds: float = 5.0
    sse_poll_seconds: float = 2.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
