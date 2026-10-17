"""Entrada del alta de invitado."""

from pydantic import BaseModel, Field

from app.security.nicks import NICK_MAX_LENGTH


class GuestRequest(BaseModel):
    # La regla de nick vive en `security/nicks.py` (misma para el alta y el PATCH).
    # Acá va un tope generoso sólo para no procesar un nick absurdo (H-15): el
    # límite real (16) lo sigue aplicando `clean_nick` con su código NICK_LENGTH.
    nick: str | None = Field(default=None, max_length=NICK_MAX_LENGTH * 4)
