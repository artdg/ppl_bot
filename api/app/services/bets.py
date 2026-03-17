from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Bet, Match, MatchStatus, User
from app.services.odds import recalc_match_odds


class InsufficientBalanceError(Exception):
    pass


class MatchNotAvailableError(Exception):
    pass


@dataclass(frozen=True)
class CreateBetResult:
    bet: Bet
    new_balance: float


async def create_bet(session: AsyncSession, *, user_id: int, match_id: int, team: str, amount: float) -> CreateBetResult:
    if amount <= 0:
        raise ValueError("amount must be positive")

    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        user = User(id=user_id, username=None, balance=100.0)
        session.add(user)
        await session.flush()

    match = await session.get(Match, match_id, with_for_update=True)
    if match is None:
        raise ValueError("Match not found")
    if match.status != MatchStatus.live:
        raise MatchNotAvailableError("Match is not available for betting")
    if team not in (match.team1, match.team2):
        raise ValueError("team must be one of match teams")

    if user.balance is None or user.balance < amount:
        raise InsufficientBalanceError("Insufficient balance")

    coef = match.coef_team1 if team == match.team1 else match.coef_team2
    user.balance -= amount

    bet = Bet(user_id=user_id, match_id=match_id, team=team, amount=amount, coef=coef)
    session.add(bet)

    await recalc_match_odds(session, match_id)
    await session.flush()
    return CreateBetResult(bet=bet, new_balance=float(user.balance))


async def list_user_bets_with_match(session: AsyncSession, *, user_id: int) -> list[dict]:
    result = await session.execute(
        select(Bet, Match)
        .join(Match, Bet.match_id == Match.id)
        .where(Bet.user_id == user_id)
        .order_by(Bet.id.desc())
    )
    rows = result.all()
    out: list[dict] = []
    for bet, match in rows:
        out.append(
            {
                "id": bet.id,
                "match_id": bet.match_id,
                "team": bet.team,
                "amount": bet.amount,
                "coef": bet.coef,
                "match_team1": match.team1,
                "match_team2": match.team2,
                "match_start_time": match.start_time,
                "match_status": match.status.value,
                "match_winner": match.winner,
            }
        )
    return out

