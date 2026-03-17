from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Float, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MatchStatus(str, Enum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team1: Mapped[str] = mapped_column(String, nullable=False)
    team2: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    status: Mapped[MatchStatus] = mapped_column(SAEnum(MatchStatus, name="match_status"), default=MatchStatus.scheduled)
    winner: Mapped[str | None] = mapped_column(String, nullable=True)

    coef_team1: Mapped[float] = mapped_column(Float, default=2.0)
    coef_team2: Mapped[float] = mapped_column(Float, default=2.0)

