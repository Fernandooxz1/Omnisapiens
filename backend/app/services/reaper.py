"""El barrendero: cierra lo que nadie más cierra.

Tres barridos, los tres idempotentes y en bloque:

- Salas `waiting` con `expires_at` vencido → `expired`. El filtro de `status` es
  el que importa (H-04): una sala `playing` puede tener `expires_at` viejo, y
  marcarla `expired` mataría una partida viva.
- Partidas `playing` más viejas que `stale_match_minutes` → `void` con `ended_at`.
  La fila se escribe al arrancar la partida; si el proceso muere en el medio,
  nadie más la cierra.
- Corridas de arcade `playing` más viejas que lo mismo → `invalid` con `ended_at`.
  Una corrida cortada a la mitad no compite en el ranking, y `invalid` es el
  estado que el esquema declara justamente para sacarla de circulación.

Corre al arrancar la API y es best-effort: una base que no contesta no impide
levantar el servidor, y el barrido se reintenta en el próximo arranque. Al
arrancar no puede haber una corrida viva, así que cualquier `playing` es de un
proceso que ya no está.

Ojo el día que el barrido pase a ser periódico: una corrida de arcade legítima
puede durar más que una partida 1v1, y hay que coordinarlo con las conexiones
vivas (igual que la sala `waiting` con jugadores).
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.game.arcade_engine import RunStatus
from app.game.match_engine import MatchStatus
from app.models import ArcadeRun, Match, Room
from app.models.arcade import INVALID_STATUS
from app.runtime.room import RoomStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SweepResult:
    expired_rooms: int
    voided_matches: int
    invalidated_runs: int


async def sweep(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    stale_after: timedelta | None = None,
) -> SweepResult:
    """Marca lo vencido. Commitea: no corre dentro de un pedido (como el manager)."""
    now = now or datetime.now(UTC)
    stale_after = stale_after or timedelta(minutes=settings.stale_match_minutes)

    expired = (
        (
            await session.execute(
                update(Room)
                .where(Room.status == RoomStatus.WAITING.value, Room.expires_at < now)
                .values(status=RoomStatus.EXPIRED.value)
                .returning(Room.id)
            )
        )
        .scalars()
        .all()
    )
    voided = (
        (
            await session.execute(
                update(Match)
                .where(
                    Match.status == MatchStatus.PLAYING.value,
                    Match.started_at < now - stale_after,
                )
                .values(status=MatchStatus.VOID.value, ended_at=now)
                .returning(Match.id)
            )
        )
        .scalars()
        .all()
    )
    invalidated = (
        (
            await session.execute(
                update(ArcadeRun)
                .where(
                    ArcadeRun.status == RunStatus.PLAYING.value,
                    ArcadeRun.started_at < now - stale_after,
                )
                .values(status=INVALID_STATUS, ended_at=now)
                .returning(ArcadeRun.id)
            )
        )
        .scalars()
        .all()
    )
    await session.commit()

    return SweepResult(
        expired_rooms=len(expired),
        voided_matches=len(voided),
        invalidated_runs=len(invalidated),
    )
