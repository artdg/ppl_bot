from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import current_user_dep
from app.models import User
from app.schemas.user import MeOut

router = APIRouter()


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(current_user_dep)) -> MeOut:
    return MeOut(id=user.id, username=user.username, balance=float(user.balance))

