"""El catálogo de modos: la fuente de verdad del menú del cliente.

Lo que el jugador puede elegir y cómo se configura sale de acá. Agregar un modo
es registrarlo en `app.game.modes`; el endpoint no tiene una lista propia.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.game.modes import all as all_modes
from app.game.modes.base import GameMode

router = APIRouter(tags=["modes"])


class ModeOut(BaseModel):
    code: str
    name: str
    content_kind: str
    play_format: str
    players: str
    input: str
    media: list[str]
    ranking: bool
    config_schema: dict[str, Any]


@router.get("/modes")
async def list_modes() -> list[ModeOut]:
    return [_mode_out(mode) for mode in all_modes()]


def _mode_out(mode: GameMode) -> ModeOut:
    return ModeOut(
        code=mode.code,
        name=mode.name,
        content_kind=mode.content_kind,
        play_format=mode.play_format,
        players=mode.players.value,
        input=mode.input,
        media=list(mode.media),
        ranking=mode.ranking is not None,
        config_schema=mode.config_schema.model_json_schema(),
    )


__all__ = ["ModeOut", "router"]
