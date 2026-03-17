from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db_session
from app.core.security import TelegramInitDataError, TelegramUser, validate_init_data
from app.models import User


async def db_session_dep() -> AsyncIterator[AsyncSession]:
    async for s in get_db_session():
        yield s


async def current_user_dep(
    session: AsyncSession = Depends(db_session_dep),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_debug_user_id: str | None = Header(default=None, alias="X-Debug-User-Id"),
) -> User:
    settings = get_settings()
    if settings.allow_debug_auth and x_debug_user_id:
        try:
            user_id = int(x_debug_user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Bad X-Debug-User-Id"
            ) from e
        telegram_user = TelegramUser(id=user_id, username=None, first_name=None, last_name=None)
    else:
        try:
            telegram_user = validate_init_data(x_telegram_init_data or "")
        except TelegramInitDataError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    result = await session.execute(select(User).where(User.id == telegram_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=telegram_user.id, username=telegram_user.username, balance=100.0)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # keep username fresh (optional, but nice)
        if telegram_user.username and user.username != telegram_user.username:
            user.username = telegram_user.username
            await session.commit()
            await session.refresh(user)
    return user


def internal_token_dep(x_internal_token: str | None = Header(default=None, alias="X-Internal-Token")) -> None:
    settings = get_settings()
    if not x_internal_token or x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad internal token")

