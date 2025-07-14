import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import BaseFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from db.models import engine, Base, User, async_session, Match, Bet
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, selectinload
from sqlalchemy import BigInteger, String, select, Float, DateTime
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()

ADMINS = {463768684}

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMINS

admin_filter = AdminFilter()

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    user, created = await User.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username or "Unknown"
    )

    if created:
        await message.answer("Привет! Ты зарегистрирован в системе для ставок на турниры PPL!")
    else:
        await message.answer("С возвращением! Ты уже в системе.")

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    logging.basicConfig(level=logging.INFO)
    await on_startup()
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

@dp.message(F.text == "/balance")
async def balance_cmd(message: Message):
    async with async_session() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("Ты не зарегистрирован, отправь /start для регистрации.")
        return

    await message.answer(f"Твой баланс: {user.balance:.2f} PPL coins.")

@dp.message(F.text == "/matches")
async def show_matches(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Match).where(Match.status != "Завершён")
        )
        matches = result.scalars().all()

    if not matches:
        await message.answer("Нет активных матчей.")
        return

    text = "Активные матчи:\n\n"
    for match in matches:
        text += (
            f"ID: {match.id}\n"
            f"{match.team1} vs {match.team2}\n"
            f"{match.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"Коэф: {match.team1} - {match.coef_team1:.2f}, {match.team2} - {match.coef_team2:.2f}\n\n"
        )

    await message.answer(text)

class AddMatchStates(StatesGroup):
    waiting_for_team1 = State()
    waiting_for_team2 = State()
    waiting_for_start_time = State()

@dp.message(admin_filter, F.text == "/addmatch")
async def addmatch_start(message: Message, state: FSMContext):
    await message.answer("Введите название первой команды:")
    await state.set_state(AddMatchStates.waiting_for_team1)

@dp.message(admin_filter, AddMatchStates.waiting_for_team1)
async def process_team1(message: Message, state: FSMContext):
    await state.update_data(team1=message.text)
    await message.answer("Введите название второй команды:")
    await state.set_state(AddMatchStates.waiting_for_team2)

@dp.message(admin_filter, AddMatchStates.waiting_for_team2)
async def process_team2(message: Message, state: FSMContext):
    await state.update_data(team2=message.text)
    await message.answer("Введите дату и время начала матча в формате YYYY-MM-DD HH:MM:")
    await state.set_state(AddMatchStates.waiting_for_start_time)

@dp.message(admin_filter, AddMatchStates.waiting_for_start_time)
async def process_start_time(message: Message, state: FSMContext):
    data = await state.get_data()
    team1 = data['team1']
    team2 = data['team2']

    try:
        start_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Попробуйте снова в формате YYYY-MM-DD HH:MM")
        return

    async with async_session() as session:
        match = Match(team1=team1, team2=team2, start_time=start_time)
        session.add(match)
        await session.commit()

    await message.answer(f"Матч {team1} vs {team2} успешно добавлен на {start_time.strftime('%Y-%m-%d %H:%M')}!")
    await state.clear()

class BetStates(StatesGroup):
    choosing_match = State()
    choosing_team = State()
    entering_amount = State()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message(F.text == "/bet")
async def start_bet(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Match).where(Match.status == "В процессе"))
        matches = result.scalars().all()

    if not matches:
        await message.answer("Нет доступных матчей.")
        return

    text = "Выбери матч (введи номер):\n"
    for i, match in enumerate(matches, 1):
        text += f"{i}. {match.team1} vs {match.team2} ({match.start_time.strftime('%Y-%m-%d %H:%M')})\n"

    await state.set_state(BetStates.choosing_match)
    await state.update_data(matches=matches)
    await message.answer(text)


@dp.message(BetStates.choosing_match)
async def choose_match(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Действие отменено.")
        return

    data = await state.get_data()
    matches = data.get("matches", [])

    try:
        idx = int(message.text) - 1
        if idx < 0 or idx >= len(matches):
            raise IndexError
    except (ValueError, IndexError):
        await message.answer("Неверный номер матча. Попробуй еще раз.")
        return

    match = matches[idx]
    await state.update_data(match=match, match_id=match.id)
    await state.set_state(BetStates.choosing_team)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=match.team1, callback_data=f"choose_team:{match.team1}")],
        [InlineKeyboardButton(text=match.team2, callback_data=f"choose_team:{match.team2}")],
    ])

    await message.answer("Выбери команду для ставки:", reply_markup=kb)


@dp.callback_query(F.data.startswith("choose_team:"))
async def team_selected(callback: CallbackQuery, state: FSMContext):
    chosen_team = callback.data.split("choose_team:")[1]
    await state.update_data(team=chosen_team)

    await callback.message.edit_reply_markup()
    await state.set_state(BetStates.entering_amount)
    await callback.message.answer(f"Вы выбрали: {chosen_team}\nВведите сумму ставки:")

async def recalc_odds(match_id: int, session):
    match = await session.get(Match, match_id)
    result = await session.execute(
        select(Bet).where(Bet.match_id == match_id)
    )
    bets = result.scalars().all()

    sum_team1 = sum(b.amount for b in bets if b.team == match.team1)
    sum_team2 = sum(b.amount for b in bets if b.team == match.team2)
    total = sum_team1 + sum_team2

    margin = 0.05
    min_coef = 1.20
    max_coef = 5.00
    default_coef = 2.00

    base = 30

    if total > 0:
        adjusted_sum_team1 = sum_team1 + base
        adjusted_sum_team2 = sum_team2 + base
        adjusted_total = adjusted_sum_team1 + adjusted_sum_team2

        raw_coef1 = adjusted_total / adjusted_sum_team1
        raw_coef2 = adjusted_total / adjusted_sum_team2

        coef1 = raw_coef1 * (1 - margin)
        coef2 = raw_coef2 * (1 - margin)

        coef1 = max(min_coef, min(max_coef, coef1))
        coef2 = max(min_coef, min(max_coef, coef2))
    else:
        coef1 = coef2 = default_coef

    match.coef_team1 = round(coef1, 2)
    match.coef_team2 = round(coef2, 2)

    session.add(match)

@dp.message(BetStates.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Неверная сумма. Введи положительное число.")
        return

    data = await state.get_data()

    async with async_session() as session:
        async with session.begin():
            user = await session.get(User, message.from_user.id, with_for_update=True)
            if not user or (user.balance is None or user.balance < amount):
                await message.answer("Недостаточно средств.")
                await state.clear()
                return

            match = await session.get(Match, data["match_id"])
            selected_team = data["team"]

            if selected_team == match.team1:
                coef = match.coef_team1
            else:
                coef = match.coef_team2

            user.balance -= amount
            bet = Bet(
                user_id=message.from_user.id,
                match_id=match.id,
                team=selected_team,
                amount=amount,
                coef=coef
            )
            session.add(bet)

            await recalc_odds(match.id, session)

        await session.commit()

    await message.answer(f"Ставка {amount}₽ на {selected_team} успешно принята по коэффициенту {coef:.2f}!")
    await state.clear()

async def create_bet(user_id, match_id, team, amount, session):
    match = await session.get(Match, match_id)

    if team == match.team1:
        coef = match.coef_team1
    else:
        coef = match.coef_team2

    bet = Bet(user_id=user_id, match_id=match_id, team=team, amount=amount, coef=coef)
    session.add(bet)
    await session.commit()

@dp.message(F.text == "/mybets")
async def my_bets_handler(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Bet)
            .where(Bet.user_id == message.from_user.id)
            .options(selectinload(Bet.match))
        )
        bets = result.scalars().all()

    if not bets:
        await message.answer("У тебя пока нет ставок.")
        return

    text = "Твои ставки:\n\n"
    for bet in bets:
        match = bet.match
        match_info = f"{match.team1} vs {match.team2} ({match.start_time.strftime('%Y-%m-%d %H:%M')})"

        coef = bet.coef

        status = "В процессе"
        if match.winner:
            if bet.team == match.winner:
                status = "выиграл"
            else:
                status = "проиграл"

        text += (
            f"Матч: {match_info}\n"
            f"Ставка: на {bet.team} (коэф: {coef:.2f})\n"
            f"Сумма: {bet.amount}₽\n"
            f"Статус: {status}\n\n"
        )

    await message.answer(text)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message(admin_filter, F.text == "/finishmatch")
async def finishmatch_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Match).where(Match.status == "В процессе"))
        matches = result.scalars().all()

    if not matches:
        await message.answer("Нет матчей со статусом 'В процессе'.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])  # Создаём с пустым списком

    for match in matches:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{match.id}: {match.team1} vs {match.team2}",
                callback_data=f"finishmatch_select:{match.id}"
            )
        ])

    await message.answer("Выбери матч для завершения:", reply_markup=kb)

@dp.callback_query(F.data.startswith("finishmatch_select:"))
async def finishmatch_choose_winner(callback: CallbackQuery):
    match_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        match = await session.get(Match, match_id)

    if not match:
        await callback.message.answer("Матч не найден.")
        await callback.answer()
        return

    if match.status == "Завершён":
        await callback.message.answer("Этот матч уже завершён.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[  # Передаём сразу список списков
        [
            InlineKeyboardButton(text=match.team1, callback_data=f"finishmatch_winner:{match_id}:{match.team1}"),
            InlineKeyboardButton(text=match.team2, callback_data=f"finishmatch_winner:{match_id}:{match.team2}")
        ]
    ])

    await callback.message.edit_text(
        f"Выбери победителя матча #{match.id}:\n{match.team1} vs {match.team2}",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("finishmatch_winner:"))
async def finishmatch_finalize(callback: CallbackQuery):
    _, match_id_str, winner_team = callback.data.split(":", 2)
    match_id = int(match_id_str)

    async with async_session() as session:
        # Получаем матч
        match = await session.get(Match, match_id)

        if not match:
            await callback.message.answer("Матч не найден.")
            await callback.answer()
            return

        if match.status == "Завершён":
            await callback.message.answer("Этот матч уже завершён.")
            await callback.answer()
            return

        if winner_team not in [match.team1, match.team2]:
            await callback.message.answer(f"Победитель должен быть '{match.team1}' или '{match.team2}'.")
            await callback.answer()
            return

        match.winner = winner_team
        match.status = "Завершён"
        await session.commit()

        result = await session.execute(select(Bet).where(Bet.match_id == match.id))
        bets = result.scalars().all()

        updated_users = set()

        for bet in bets:
            if bet.team == winner_team:
                win_amount = bet.amount * bet.coef

                user = await session.get(User, bet.user_id)
                if user:
                    user.balance += win_amount
                    updated_users.add(user.id)

        await session.commit()

    await callback.message.edit_text(
        f"Матч #{match.id} завершён.\nПобедитель: {winner_team}\nБалансы обновлены: {len(updated_users)} пользователей."
    )
    await callback.answer()

@dp.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("Действие отменено.")
    else:
        await message.answer("Нет активного действия.")

if __name__ == "__main__":
    asyncio.run(main())