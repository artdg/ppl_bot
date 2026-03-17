from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode

from bot.config import bot_settings
from bot.handlers import setup_routers


async def main() -> None:
    logging.basicConfig(level=getattr(logging, bot_settings.log_level, logging.INFO))

    bot = Bot(token=bot_settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    for r in setup_routers():
        dp.include_router(r)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())