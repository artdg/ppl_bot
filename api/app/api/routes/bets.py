from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_dep, db_session_dep
from app.models import User
from app.schemas.bet import BetCreateIn, BetOut, BetWithMatchOut
from app.services.bets import (
    InsufficientBalanceError,
    MatchNotAvailableError,
    create_bet,
    list_user_bets_with_match,
)

router = APIRouter()


@router.post("/bets", response_model=BetOut)
async def place_bet(
    payload: BetCreateIn,
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(db_session_dep),
) -> BetOut:
    try:
        async with session.begin():
            result = await create_bet(
                session,
                user_id=user.id,
                match_id=payload.match_id,
                team=payload.team,
                amount=float(payload.amount),
            )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except MatchNotAvailableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    bet = result.bet
    return BetOut(
        id=bet.id,
        match_id=bet.match_id,
        team=bet.team,
        amount=float(bet.amount),
        coef=float(bet.coef),
        created_at=bet.created_at,
    )


@router.get("/bets/mine", response_model=list[BetWithMatchOut])
async def my_bets(
    user: User = Depends(current_user_dep),
    session: AsyncSession = Depends(db_session_dep),
) -> list[BetWithMatchOut]:
    rows = await list_user_bets_with_match(session, user_id=user.id)
    return [BetWithMatchOut(**r) for r in rows]

