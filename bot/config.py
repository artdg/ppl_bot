from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    log_level: str = "INFO"

    api_base_url: str = "http://api:8000"
    internal_api_token: str = "change-me"

    webapp_url: str = "http://localhost:5173"
    admins: str = ""

    @property
    def admin_ids(self) -> set[int]:
        out: set[int] = set()
        for part in self.admins.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.add(int(part))
            except ValueError:
                continue
        return out


bot_settings = BotSettings()

