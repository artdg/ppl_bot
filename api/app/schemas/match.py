from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.match import MatchStatus


class MatchOut(BaseModel):
    id: int
    team1: str
    team2: str
    start_time: datetime
    status: MatchStatus
    winner: str | None
    coef_team1: float
    coef_team2: float


class MatchCreateIn(BaseModel):
    team1: str
    team2: str
    start_time: datetime

