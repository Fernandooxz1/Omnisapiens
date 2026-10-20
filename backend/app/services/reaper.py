"""El barrendero: cierra lo que nadie más cierra.

Dos barridos, los dos idempotentes y en bloque:

- Salas `waiting` con `expires_at` vencido → `expired`. El filtro de `status` es
  el que importa (H-04): una sala `playing` puede tener `expires_at` viejo, y
  marcarla `expired` mataría una partida viva.
- Sesiones genéricas `playing` más viejas que `stale_match_minutes` → `invalid`
  con `ended_at`. Vale para cualquier modo: si el proceso murió, la fila abierta
  no puede volver.

Corre al arrancar la API y después cada `reaper_interval_seconds`. Al arrancar
no puede haber nada vivo en este proceso, así que cualquier fila abierta es de un
proceso que ya no está. En régimen, en cambio, hay salas con gente y sesiones
jugándose: por eso el barrido recibe `live`, lo que este proceso tiene en memoria
(`runtime/live.py`), y lo excluye. Sin eso, una sala `waiting` con dos personas
conectadas se expiraría y una sesión larga se invalidaría a mitad.

El barrido es best-effort: una base que no contesta no impide levantar el
servidor, y el siguiente intervalo lo reintenta.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.game.versus_engine import VersusStatus
from app.models import GameSession, Room
from app.runtime.live import Live

logger = logging.getLogger(__name__)

# Al arrancar no hay nada vivo en el proceso: el barrido inicial usa este valor.
NOTHING_LIVE = Live()

# Estado que saca de circulación una sesión sospechosa: el ranking solo mira
# las `finished`.
INVALID_STATUS = "invalid"


@dataclass(frozen=True)
class SweepResult:
    expired_rooms: int
    invalidated_sessions: int


async def sweep(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    stale_after: timedelta | None = None,
    live: Live = NOTHING_LIVE,
) -> SweepResult:
    """Marca lo vencido. Commitea: no corre dentro de un pedido (como el manager).

    `live` viene del proceso, no de la base: es lo único que distingue una fila
    `playing` abandonada de una que tiene un socket abierto del otro lado.
    """
    now = now or datetime.now(UTC)
    stale_after = stale_after or timedelta(minutes=settings.stale_match_minutes)

    salas_vencidas = [
        Room.status == VersusStatus.WAITING.value,
        Room.expires_at < now,
    ]
    if live.rooms.room_ids:
        salas_vencidas.append(Room.id.not_in(live.rooms.room_ids))

    sesiones_viejas = [
        GameSession.status == "playing",
        GameSession.started_at < now - stale_after,
    ]
    if live.sessions:
        sesiones_viejas.append(GameSession.id.not_in(live.sessions))

    expired = (
        (
            await session.execute(
                update(Room)
                .where(*salas_vencidas)
                .values(status=VersusStatus.EXPIRED.value)
                .returning(Room.id)
            )
        )
        .scalars()
        .all()
    )
    sessions_invalidated = (
        (
            await session.execute(
                update(GameSession)
                .where(*sesiones_viejas)
                .values(status=INVALID_STATUS, ended_at=now)
                .returning(GameSession.id)
            )
        )
        .scalars()
        .all()
    )
    await session.commit()

    return SweepResult(
        expired_rooms=len(expired),
        invalidated_sessions=len(sessions_invalidated),
    )
