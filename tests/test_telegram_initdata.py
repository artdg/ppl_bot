import pytest


def test_validate_init_data_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "dummy:token")
    monkeypatch.setenv("DB_USER", "x")
    monkeypatch.setenv("DB_PASS", "x")
    monkeypatch.setenv("DB_HOST", "x")
    monkeypatch.setenv("DB_NAME", "x")

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.security import TelegramInitDataError, validate_init_data

    with pytest.raises(TelegramInitDataError):
        validate_init_data("")

