from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from dataclasses import dataclass

from app.core.config import get_settings


class TelegramInitDataError(Exception):
    pass


@dataclass(frozen=True)
class TelegramUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None


def _build_check_string(params: dict[str, str]) -> str:
    items = [(k, v) for k, v in params.items() if k != "hash"]
    items.sort(key=lambda kv: kv[0])
    return "\n".join(f"{k}={v}" for k, v in items)


def validate_init_data(init_data: str, *, max_age_seconds: int = 60 * 60) -> TelegramUser:
    """
    Validate Telegram WebApp initData (https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app).
    Returns TelegramUser extracted from initData.
    """
    if not init_data:
        raise TelegramInitDataError("Missing initData")

    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.get("hash")
    if not received_hash:
        raise TelegramInitDataError("Missing initData hash")

    auth_date = parsed.get("auth_date")
    if not auth_date:
        raise TelegramInitDataError("Missing auth_date")

    try:
        auth_date_int = int(auth_date)
    except ValueError as e:
        raise TelegramInitDataError("Invalid auth_date") from e

    now = int(time.time())
    if now - auth_date_int > max_age_seconds:
        raise TelegramInitDataError("initData expired")

    settings = get_settings()
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode("utf-8"), hashlib.sha256).digest()
    check_string = _build_check_string(parsed)
    calculated_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramInitDataError("Bad initData signature")

    user_raw = parsed.get("user")
    if not user_raw:
        raise TelegramInitDataError("Missing user payload")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as e:
        raise TelegramInitDataError("Invalid user json") from e

    try:
        user_id = int(user["id"])
    except Exception as e:  # noqa: BLE001
        raise TelegramInitDataError("Invalid user id") from e

    return TelegramUser(
        id=user_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
    )

