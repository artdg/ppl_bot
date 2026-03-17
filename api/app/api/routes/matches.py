from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session_dep, internal_token_dep
from app.models import MatchStatus
from app.schemas.match import MatchCreateIn, MatchOut
from app.services.matches import create_match, list_matches, set_match_live

router = APIRouter()


@router.get("/matches", response_model=list[MatchOut])
async def get_matches(
    match_status: MatchStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(db_session_dep),
) -> list[MatchOut]:
    matches = await list_matches(session, status=match_status)
    return [
        MatchOut(
            id=m.id,
            team1=m.team1,
            team2=m.team2,
            start_time=m.start_time,
            status=m.status,
            winner=m.winner,
            coef_team1=float(m.coef_team1),
            coef_team2=float(m.coef_team2),
        )
        for m in matches
    ]


@router.post("/internal/admin/matches", dependencies=[Depends(internal_token_dep)], response_model=MatchOut)
async def internal_create_match(payload: MatchCreateIn, session: AsyncSession = Depends(db_session_dep)) -> MatchOut:
    match = await create_match(session, team1=payload.team1, team2=payload.team2, start_time=payload.start_time)
    await session.commit()
    await session.refresh(match)
    return MatchOut(
        id=match.id,
        team1=match.team1,
        team2=match.team2,
        start_time=match.start_time,
        status=match.status,
        winner=match.winner,
        coef_team1=float(match.coef_team1),
        coef_team2=float(match.coef_team2),
    )


@router.post("/internal/admin/matches/{match_id}/live", dependencies=[Depends(internal_token_dep)], response_model=MatchOut)
async def internal_set_live(match_id: int, session: AsyncSession = Depends(db_session_dep)) -> MatchOut:
    try:
        match = await set_match_live(session, match_id=match_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found") from e
    await session.commit()
    await session.refresh(match)
    return MatchOut(
        id=match.id,
        team1=match.team1,
        team2=match.team2,
        start_time=match.start_time,
        status=match.status,
        winner=match.winner,
        coef_team1=float(match.coef_team1),
        coef_team2=float(match.coef_team2),
    )

