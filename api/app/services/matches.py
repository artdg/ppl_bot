from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Bet, Match, MatchStatus, User
from app.services.odds import recalc_match_odds


@dataclass(frozen=True)
class FinishMatchResult:
    updated_users: int


async def create_match(session: AsyncSession, *, team1: str, team2: str, start_time: datetime) -> Match:
    match = Match(team1=team1, team2=team2, start_time=start_time, status=MatchStatus.scheduled)
    session.add(match)
    await session.flush()
    return match


async def list_matches(session: AsyncSession, *, status: MatchStatus | None = None) -> list[Match]:
    stmt = select(Match).order_by(Match.start_time.asc())
    if status is not None:
        stmt = stmt.where(Match.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def set_match_live(session: AsyncSession, *, match_id: int) -> Match:
    match = await session.get(Match, match_id, with_for_update=True)
    if match is None:
        raise ValueError("Match not found")
    match.status = MatchStatus.live
    session.add(match)
    await recalc_match_odds(session, match_id)
    return match


async def finish_match(session: AsyncSession, *, match_id: int, winner_team: str) -> FinishMatchResult:
    match = await session.get(Match, match_id, with_for_update=True)
    if match is None:
        raise ValueError("Match not found")
    if match.status == MatchStatus.finished:
        return FinishMatchResult(updated_users=0)
    if winner_team not in (match.team1, match.team2):
        raise ValueError("Winner must be one of match teams")

    match.winner = winner_team
    match.status = MatchStatus.finished
    session.add(match)
    await session.flush()

    result = await session.execute(select(Bet).where(Bet.match_id == match_id))
    bets = result.scalars().all()

    updated_user_ids: set[int] = set()
    for bet in bets:
        if bet.team != winner_team:
            continue
        win_amount = float(bet.amount) * float(bet.coef)
        user = await session.get(User, bet.user_id, with_for_update=True)
        if user is None:
            continue
        user.balance += win_amount
        session.add(user)
        updated_user_ids.add(user.id)

    return FinishMatchResult(updated_users=len(updated_user_ids))

