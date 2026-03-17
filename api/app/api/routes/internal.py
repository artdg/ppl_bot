from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session_dep, internal_token_dep
from app.models import Match, User
from app.schemas.match import MatchOut
from app.services.matches import finish_match

router = APIRouter()


class UpsertUserIn(BaseModel):
    user_id: int
    username: str | None = None


@router.post("/internal/users/upsert", dependencies=[Depends(internal_token_dep)])
async def internal_upsert_user(payload: UpsertUserIn, session: AsyncSession = Depends(db_session_dep)) -> dict:
    result = await session.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=payload.user_id, username=payload.username, balance=100.0)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        if payload.username and user.username != payload.username:
            user.username = payload.username
            await session.commit()
            await session.refresh(user)
    return {"id": user.id, "username": user.username, "balance": float(user.balance)}


@router.get("/internal/users/{user_id}", dependencies=[Depends(internal_token_dep)])
async def internal_get_user(user_id: int, session: AsyncSession = Depends(db_session_dep)) -> dict:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"id": user.id, "username": user.username, "balance": float(user.balance)}


@router.post("/internal/admin/matches/{match_id}/finish", dependencies=[Depends(internal_token_dep)])
async def internal_finish_match(
    match_id: int,
    winner_team: str,
    session: AsyncSession = Depends(db_session_dep),
) -> dict:
    try:
        async with session.begin():
            result = await finish_match(session, match_id=match_id, winner_team=winner_team)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    match = await session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    return {
        "match": MatchOut(
            id=match.id,
            team1=match.team1,
            team2=match.team2,
            start_time=match.start_time,
            status=match.status,
            winner=match.winner,
            coef_team1=float(match.coef_team1),
            coef_team2=float(match.coef_team2),
        ),
        "updated_users": result.updated_users,
    }

