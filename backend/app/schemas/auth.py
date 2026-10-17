"""Entrada del alta de invitado."""

from pydantic import BaseModel


class GuestRequest(BaseModel):
    # Sin reglas de nick acá: las de verdad viven en `security/nicks.py`, son las
    # mismas para el alta y para el `PATCH /me`, y tienen su propio código de error.
    nick: str | None = None
