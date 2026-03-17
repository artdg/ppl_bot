from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.user import router as user_router


def setup_routers() -> list[Router]:
    return [user_router, admin_router]

