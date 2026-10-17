"""Entrada y salida de las salas."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.game.constants import ONLINE_ROUNDS_OPTIONS, ONLINE_SECONDS_OPTIONS


class RoomCreate(BaseModel):
    rounds: int = 5
    seconds: int = 20

    @field_validator("rounds")
    @classmethod
    def _rounds_permitidos(cls, valor: int) -> int:
        if valor not in ONLINE_ROUNDS_OPTIONS:
            raise ValueError(f"debe ser uno de {ONLINE_ROUNDS_OPTIONS}")
        return valor

    @field_validator("seconds")
    @classmethod
    def _segundos_permitidos(cls, valor: int) -> int:
        if valor not in ONLINE_SECONDS_OPTIONS:
            raise ValueError(f"debe ser uno de {ONLINE_SECONDS_OPTIONS}")
        return valor


class RoomOut(BaseModel):
    code: str
    config: dict[str, int]


class RoomPreview(RoomOut):
    status: str
    host_nick: str | None
    expires_at: datetime
