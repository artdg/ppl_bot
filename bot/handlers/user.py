from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.api_client import ApiClient
from bot.config import bot_settings
from bot.keyboards import webapp_keyboard

router = Router()
api = ApiClient(base_url=bot_settings.api_base_url, internal_token=bot_settings.internal_api_token)


@router.message(F.text == "/start")
async def start_cmd(message: Message) -> None:
    await api.upsert_user(user_id=message.from_user.id, username=message.from_user.username)
    await message.answer(
        "Добро пожаловать в PPL Bets.\n\nОткрывай Web App, чтобы смотреть матчи и делать ставки.",
        reply_markup=webapp_keyboard(bot_settings.webapp_url),
    )


@router.message(F.text == "/balance")
async def balance_cmd(message: Message) -> None:
    try:
        user = await api.get_user(user_id=message.from_user.id)
    except Exception:  # noqa: BLE001
        await message.answer("Не смог получить баланс. Попробуй позже или отправь /start.")
        return
    await message.answer(f"Твой баланс: {user['balance']:.2f} PPL coins.")


@router.message(F.text == "/matches")
async def matches_cmd(message: Message) -> None:
    matches = await api.list_matches(status=None)
    if not matches:
        await message.answer("Матчей пока нет.")
        return

    lines: list[str] = ["Матчи:\n"]
    for m in matches:
        lines.append(
            f"#{m['id']} {m['team1']} vs {m['team2']}\n"
            f"Старт: {m['start_time']}\n"
            f"Статус: {m['status']}\n"
            f"Коэф: {m['team1']} {m['coef_team1']:.2f} | {m['team2']} {m['coef_team2']:.2f}\n"
        )
    await message.answer("\n".join(lines), reply_markup=webapp_keyboard(bot_settings.webapp_url))


@router.message(F.text.in_({"/bet", "/mybets"}))
async def redirect_to_webapp(message: Message) -> None:
    await message.answer("Эти действия доступны в Web App.", reply_markup=webapp_keyboard(bot_settings.webapp_url))

