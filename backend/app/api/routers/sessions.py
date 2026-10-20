"""Sesiones: crear una partida solo y devolver su socket.

La sesión se crea acá y se juega en `WS /ws/session/{id}`. El catálogo manda:
el modo tiene que existir, ser solo y validar su propia configuración. El
cliente no inventa ni el id ni las reglas.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, ValidationError

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.api.rate_limit import session_rate_limit
from app.game.modes import GameMode, Players
from app.game.modes import get as get_mode
from app.services import sessions

router = APIRouter(prefix="/sessions", tags=["sessions"])

Clock = Callable[[], datetime]


def get_clock() -> Clock:
    """El instante de arranque; el test lo reemplaza por su reloj falso."""
    return lambda: datetime.now(UTC)


ClockDep = Annotated[Clock, Depends(get_clock)]


class SessionCreate(BaseModel):
    mode: str
    config: dict[str, Any] = Field(default_factory=dict)


class SessionOut(BaseModel):
    session_id: str
    ws_url: str


@router.post("", status_code=201, dependencies=[Depends(session_rate_limit)])
async def new_session(
    body: SessionCreate,
    usuario: CurrentUserDep,
    session: SessionDep,
    now: ClockDep,
) -> SessionOut:
    mode = _mode(body.mode)
    config = _config(mode, body.config)

    session_id = uuid.uuid4()
    await sessions.start_session(
        session,
        session_id=session_id,
        mode=mode.code,
        content_kind=mode.content_kind,
        play_format=mode.play_format,
        ruleset_version=mode.ruleset_version,
        config=config,
        started_at=now(),
        owner_user_id=usuario.id,
    )
    return SessionOut(
        session_id=str(session_id),
        # Ruta del proceso: el cliente le pone el host y el esquema que ya usa.
        ws_url=f"/ws/session/{session_id}",
    )


def _mode(code: str) -> GameMode:
    try:
        return get_mode(code)
    except KeyError:
        raise ApiError(
            404, "MODE_NOT_FOUND", f"No hay un modo registrado con el código {code!r}."
        ) from None


def _config(mode: GameMode, raw: dict[str, Any]) -> dict[str, Any]:
    if mode.players is not Players.SOLO or mode.solo_rules is None:
        raise ApiError(
            422,
            "MODE_NOT_SOLO",
            f"El modo {mode.code!r} no se juega en una sesión solo.",
        )
    try:
        return mode.config_schema.model_validate(raw).model_dump()
    except ValidationError as exc:
        detalle = "; ".join(
            f"{'.'.join(str(parte) for parte in error['loc'])}: {error['msg']}"
            if error["loc"]
            else error["msg"]
            for error in exc.errors()
        )
        raise ApiError(
            422,
            "INVALID_CONFIG",
            detalle or f"La configuración de {mode.code!r} no es válida.",
        ) from None


__all__ = ["Clock", "SessionCreate", "SessionOut", "get_clock", "router"]
