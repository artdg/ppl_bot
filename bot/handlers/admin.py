from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api_client import ApiClient
from bot.config import bot_settings
from bot.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter(bot_settings.admin_ids))

api = ApiClient(base_url=bot_settings.api_base_url, internal_token=bot_settings.internal_api_token)


class AddMatchStates(StatesGroup):
    waiting_for_team1 = State()
    waiting_for_team2 = State()
    waiting_for_start_time = State()


@router.message(F.text == "/addmatch")
async def addmatch_start(message: Message, state: FSMContext) -> None:
    await message.answer("Введите название первой команды:")
    await state.set_state(AddMatchStates.waiting_for_team1)


@router.message(AddMatchStates.waiting_for_team1)
async def addmatch_team1(message: Message, state: FSMContext) -> None:
    await state.update_data(team1=message.text.strip())
    await message.answer("Введите название второй команды:")
    await state.set_state(AddMatchStates.waiting_for_team2)


@router.message(AddMatchStates.waiting_for_team2)
async def addmatch_team2(message: Message, state: FSMContext) -> None:
    await state.update_data(team2=message.text.strip())
    await message.answer("Введите дату/время начала (YYYY-MM-DD HH:MM). После старта переведи матч в live командой /setlive.")
    await state.set_state(AddMatchStates.waiting_for_start_time)


@router.message(AddMatchStates.waiting_for_start_time)
async def addmatch_start_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        start_time = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Введи в формате YYYY-MM-DD HH:MM.")
        return

    match = await api.admin_create_match(
        team1=data["team1"],
        team2=data["team2"],
        start_time_iso=start_time.isoformat(),
    )
    await message.answer(f"Матч создан: #{match['id']} {match['team1']} vs {match['team2']} (scheduled).")
    await state.clear()


@router.message(F.text == "/setlive")
async def setlive_cmd(message: Message) -> None:
    matches = await api.list_matches(status="scheduled")
    if not matches:
        await message.answer("Нет матчей в статусе scheduled.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"#{m['id']} {m['team1']} vs {m['team2']}", callback_data=f"setlive:{m['id']}")]
            for m in matches
        ]
    )
    await message.answer("Выбери матч для перевода в live:", reply_markup=kb)


@router.callback_query(F.data.startswith("setlive:"))
async def setlive_cb(callback: CallbackQuery) -> None:
    match_id = int(callback.data.split(":")[1])
    match = await api.admin_set_live(match_id=match_id)
    await callback.message.edit_text(f"Матч #{match['id']} переведён в live.")
    await callback.answer()


@router.message(F.text == "/finishmatch")
async def finishmatch_cmd(message: Message) -> None:
    matches = await api.list_matches(status="live")
    if not matches:
        await message.answer("Нет матчей в статусе live.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"#{m['id']} {m['team1']} vs {m['team2']}",
                    callback_data=f"finish_select:{m['id']}",
                )
            ]
            for m in matches
        ]
    )
    await message.answer("Выбери матч для завершения:", reply_markup=kb)


@router.callback_query(F.data.startswith("finish_select:"))
async def finish_select_cb(callback: CallbackQuery) -> None:
    match_id = int(callback.data.split(":")[1])
    matches = await api.list_matches(status=None)
    match = next((m for m in matches if int(m["id"]) == match_id), None)
    if not match:
        await callback.message.answer("Матч не найден.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=match["team1"], callback_data=f"finish:{match_id}:{match['team1']}"),
                InlineKeyboardButton(text=match["team2"], callback_data=f"finish:{match_id}:{match['team2']}"),
            ]
        ]
    )
    await callback.message.edit_text(f"Победитель матча #{match_id}?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("finish:"))
async def finish_cb(callback: CallbackQuery) -> None:
    _, match_id_str, winner_team = callback.data.split(":", 2)
    match_id = int(match_id_str)
    res = await api.admin_finish_match(match_id=match_id, winner_team=winner_team)
    await callback.message.edit_text(
        f"Матч #{res['match']['id']} завершён. Победитель: {res['match']['winner']}. "
        f"Обновлено пользователей: {res['updated_users']}."
    )
    await callback.answer()


@router.message(F.text == "/cancel")
async def cancel_cmd(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        await state.clear()
        await message.answer("Действие отменено.")
    else:
        await message.answer("Нет активного действия.")

