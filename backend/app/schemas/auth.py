"""Entrada y salida del alta de invitado."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GuestRequest(BaseModel):
    # Sin reglas de nick acá: las de verdad viven en `security/nicks.py`, son las
    # mismas para el alta y para el `PATCH /me`, y tienen su propio código de error.
    nick: str | None = None


class UserOut(BaseModel):
    # from_attributes: se arma desde el objeto del ORM sin pasar por un dict a mano.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nick: str
    is_guest: bool
    created_at: datetime


class GuestResponse(BaseModel):
    user: UserOut
    token: str
