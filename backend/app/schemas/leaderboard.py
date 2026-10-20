"""Entrada y salida del ranking del arcade."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.leaderboard import Period


class LeaderboardEntry(BaseModel):
    position: int
    nick: str
    score: int
    achieved_at: datetime


class LeaderboardOut(BaseModel):
    period: Period
    entries: list[LeaderboardEntry]


class RankOut(BaseModel):
    # Los tres van juntos: sin partidas en el período no hay posición ni marca.
    rank: int | None = None
    score: int | None = None
    achieved_at: datetime | None = None


class MyRanksOut(BaseModel):
    # `global` es palabra reservada en Python: el alias de serialización lo
    # devuelve al JSON que promete el plan sin renombrar el campo del modelo.
    global_: RankOut = Field(serialization_alias="global")
    week: RankOut
