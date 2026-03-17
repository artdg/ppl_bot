from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BetCreateIn(BaseModel):
    match_id: int
    team: str
    amount: float = Field(gt=0)


class BetOut(BaseModel):
    id: int
    match_id: int
    team: str
    amount: float
    coef: float
    created_at: datetime | None = None


class BetWithMatchOut(BaseModel):
    id: int
    match_id: int
    team: str
    amount: float
    coef: float
    match_team1: str
    match_team2: str
    match_start_time: datetime
    match_status: str
    match_winner: str | None

