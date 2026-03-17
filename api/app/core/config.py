from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

    # Telegram
    bot_token: str
    webapp_url: str = "http://localhost:5173"

    # Database
    db_user: str
    db_pass: str
    db_host: str
    db_port: int = 5432
    db_name: str
    db_echo: bool = False

    # Internal auth between bot<->api
    internal_api_token: str = "change-me"

    # Dev helper (do not enable in production)
    allow_debug_auth: bool = False

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

