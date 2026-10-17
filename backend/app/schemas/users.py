"""El perfil público del usuario y lo que se puede cambiar desde `/me`."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.services.profile import Outcome


class UserOut(BaseModel):
    # from_attributes: se arma desde el objeto del ORM sin pasar por un dict a mano.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nick: str
    is_guest: bool
    created_at: datetime
    last_seen_at: datetime


class AuthOut(BaseModel):
    """Usuario y pase juntos: lo devuelven el alta de invitado y el cambio de nick."""

    user: UserOut
    token: str


class NickUpdate(BaseModel):
    # Las reglas viven en `security/nicks.py`; acá solo viaja el texto crudo.
    nick: str


class BestMarksOut(BaseModel):
    # Los dos máximos del perfil, no la posición: el ranking tiene su endpoint.
    all_time: int | None = None
    week: int | None = None


class ArcadeRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    score: int
    correct_count: int
    longest_streak: int
    max_difficulty: int
    ended_at: datetime


class MatchSummaryOut(BaseModel):
    id: uuid.UUID
    ended_at: datetime
    opponent_nick: str
    my_score: int
    opponent_score: int
    result: Outcome


class ProfileOut(UserOut):
    """`GET /me`: el usuario tal cual, más lo acordado para la pantalla de perfil."""

    best: BestMarksOut
    arcade_runs: list[ArcadeRunOut]
    matches: list[MatchSummaryOut]
