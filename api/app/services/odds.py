from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Bet, Match


@dataclass(frozen=True)
class OddsConfig:
    margin: float = 0.05
    min_coef: float = 1.20
    max_coef: float = 5.00
    default_coef: float = 2.00
    base: float = 30.0


def compute_odds(
    sum_team1: float, sum_team2: float, *, cfg: OddsConfig | None = None
) -> tuple[float, float]:
    cfg = cfg or OddsConfig()
    total = sum_team1 + sum_team2
    if total > 0:
        adjusted_sum_team1 = sum_team1 + cfg.base
        adjusted_sum_team2 = sum_team2 + cfg.base
        adjusted_total = adjusted_sum_team1 + adjusted_sum_team2

        raw_coef1 = adjusted_total / adjusted_sum_team1
        raw_coef2 = adjusted_total / adjusted_sum_team2

        coef1 = raw_coef1 * (1 - cfg.margin)
        coef2 = raw_coef2 * (1 - cfg.margin)

        coef1 = max(cfg.min_coef, min(cfg.max_coef, coef1))
        coef2 = max(cfg.min_coef, min(cfg.max_coef, coef2))
    else:
        coef1 = coef2 = cfg.default_coef
    return (round(float(coef1), 2), round(float(coef2), 2))


async def recalc_match_odds(
    session: AsyncSession, match_id: int, *, cfg: OddsConfig | None = None
) -> Match:
    cfg = cfg or OddsConfig()
    match = await session.get(Match, match_id)
    if match is None:
        raise ValueError("Match not found")

    result = await session.execute(select(Bet).where(Bet.match_id == match_id))
    bets = result.scalars().all()

    sum_team1 = sum(b.amount for b in bets if b.team == match.team1)
    sum_team2 = sum(b.amount for b in bets if b.team == match.team2)
    coef1, coef2 = compute_odds(float(sum_team1), float(sum_team2), cfg=cfg)
    match.coef_team1 = coef1
    match.coef_team2 = coef2
    session.add(match)
    return match

