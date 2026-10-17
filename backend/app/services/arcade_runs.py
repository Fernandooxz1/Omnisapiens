"""Las dos escrituras de una corrida arcade: el arranque y el cierre con sus rondas.

Mismo reparto que `runtime/room_manager.py`: la máquina pura decide qué pasó y
este módulo lo guarda. La sesión la pone el borde (el WebSocket) y acá se
commitea a mano: el handler no corre en un pedido HTTP que cierre la transacción.

Dos decisiones que se ven en las firmas:

- La corrida nace `playing` y sin `ended_at`, para que el barrendero tenga qué
  cerrar si el proceso muere en el medio.
- Las rondas viajan recién al cerrar: `RoundRecord` no vive en el estado puro
  (el estado quedaría enorme), y escribirlas todas en la misma transacción que
  el cierre evita una corrida `finished` sin su historial.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.game.arcade_engine import ArcadeRun as RunState
from app.game.arcade_engine import RoundRecord, RunStatus
from app.models import ArcadeAnswer, ArcadeRun

logger = logging.getLogger(__name__)


async def start_run(
    session: AsyncSession, *, run_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Escribe la fila en `playing`. Sin commit acá no habría fila antes del cierre."""
    session.add(ArcadeRun(id=run_id, user_id=user_id, status=RunStatus.PLAYING.value))
    await session.commit()


async def finish_run(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    run: RunState,
    records: tuple[RoundRecord, ...],
) -> None:
    """Cierra la corrida y guarda sus rondas en una sola transacción."""
    if not run.finished:
        raise ValueError("no se puede cerrar una corrida que sigue jugando")

    # `get` puede devolver la fila que `start_run` dejó en el identity map: es la
    # misma y ya tiene lo que el cierre necesita pisar.
    corrida = await session.get(ArcadeRun, run_id)
    if corrida is None:
        # Sin fila no hay padre para las respuestas: el cierre se pierde, pero el
        # jugador ya vio su final. El barrido no puede inventarla.
        logger.warning("la corrida %s no estaba en la base", run_id)
        return

    corrida.status = run.status.value
    corrida.score = run.score
    corrida.correct_count = run.correct_count
    corrida.longest_streak = run.longest_streak
    corrida.max_difficulty = run.max_difficulty
    corrida.ended_at = datetime.now(UTC)
    session.add_all(_answer_rows(run_id, records))
    await session.commit()


def _answer_rows(
    run_id: uuid.UUID, records: tuple[RoundRecord, ...]
) -> list[ArcadeAnswer]:
    """Los nombres espejan `RoundRecord`, sin traducir (igual que `match_rounds`)."""
    return [
        ArcadeAnswer(
            id=uuid.uuid4(),
            run_id=run_id,
            round_index=record.round_index,
            question_id=uuid.UUID(record.question_id),
            difficulty=record.difficulty,
            seconds=record.seconds,
            correct_index=record.correct_index,
            chosen_index=record.choice,
            is_correct=record.correct,
            ms=record.elapsed_ms,
            points=record.points,
            rejected=record.rejected.value if record.rejected is not None else None,
        )
        for record in records
    ]
