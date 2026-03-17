from __future__ import annotations

from pydantic import BaseModel


class MeOut(BaseModel):
    id: int
    username: str | None
    balance: float

