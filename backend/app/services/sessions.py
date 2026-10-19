"""Las escrituras de una sesión: el arranque y los tres cierres.

Mismo reparto que `arcade_runs.py`: el motor puro decide qué pasó y este módulo
lo guarda. La sesión la pone el borde (el WebSocket) y acá se commitea a mano:
el handler no corre en un pedido HTTP que cierre la transacción.

Tres decisiones que se ven en las firmas:

- El servicio no lee relojes: `started_at` y `ended_at` llegan decididos. Así
  el barrido, el motor y los tests escriben con el instante que ya usaron para
  juzgar, y no con uno nuevo que podría caer del otro lado de una ventana.
- El cierre es atómico: resumen, ítems e intentos van en la misma transacción.
  Una sesión `finished` sin su historial no existe.
- Cerrar dos veces no duplica nada: si la fila ya no está `playing`, la llamada
  vuelve sin escribir. El primer cierre gana; el segundo no inventa un estado.
"""

import logging
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models import GameParticipant, GameSession, SessionAttempt, SessionItem
from app.models.session import PARTICIPANT_OUTCOMES, SESSION_STATUSES

logger = logging.getLogger(__name__)

# `playing` no cierra nada: es el estado que el arranque escribe.
CLOSING_STATUSES = tuple(status for status in SESSION_STATUSES if status != "playing")


@dataclass(frozen=True)
class Participant:
    """Una silla ocupada al arrancar: quién juega y en qué asiento."""

    seat: int
    user_id: uuid.UUID

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError(f"seat negativo: {self.seat}")


@dataclass(frozen=True)
class ParticipantResult:
    """Cómo terminó una silla. `outcome` nulo es una partida sin resultado."""

    seat: int
    score: int = 0
    outcome: str | None = None

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError(f"seat negativo: {self.seat}")
        if self.score < 0:
            raise ValueError(f"score negativo: {self.score}")
        if self.outcome is not None and self.outcome not in PARTICIPANT_OUTCOMES:
            raise ValueError(f"outcome desconocido: {self.outcome}")


@dataclass(frozen=True)
class SessionState:
    """El resumen que el motor ya calculó. El servicio solo lo proyecta."""

    ended_at: datetime
    status: str = "finished"
    score: int = 0
    correct_count: int = 0
    longest_streak: int = 0
    max_difficulty: int = DIFFICULTY_MIN

    def __post_init__(self) -> None:
        if self.status not in CLOSING_STATUSES:
            raise ValueError(f"status de cierre desconocido: {self.status}")
        if self.score < 0 or self.correct_count < 0:
            raise ValueError("los contadores no pueden ser negativos")
        if not 0 <= self.longest_streak <= self.correct_count:
            raise ValueError("longest_streak debe estar entre 0 y correct_count")
        if not DIFFICULTY_MIN <= self.max_difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"max_difficulty fuera de rango: {self.max_difficulty}")


@dataclass(frozen=True)
class ItemRecord:
    """Un ítem servido, con la solución congelada al momento de servirlo.

    `solution` es lo que después permite auditar la respuesta aunque el
    contenido se archive: no se recalcula desde `content_id`.
    """

    item_key: str
    position: int
    difficulty: int
    seconds: int
    served_at: datetime
    solution: Mapping[str, object]
    content_id: uuid.UUID | None = None
    deadline_at: datetime | None = None
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.item_key:
            raise ValueError("item_key vacío")
        if self.position < 0:
            raise ValueError(f"position negativa: {self.position}")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")
        if self.seconds <= 0:
            raise ValueError(f"seconds debe ser positivo: {self.seconds}")


@dataclass(frozen=True)
class AttemptRecord:
    """Una respuesta ya juzgada. Apunta al ítem por `item_key`, no por id.

    El id del ítem lo genera el servicio al insertarlo; el motor no tiene por
    qué conocerlo. `items` y `attempts` viajan juntos para que la referencia no
    pueda quedar colgada.
    """

    item_key: str
    attempt_seq: int
    submitted_at: datetime
    submission: Mapping[str, object]
    correct: bool
    elapsed_ms: int
    points: int
    seat: int = 0
    rejected: str | None = None

    def __post_init__(self) -> None:
        if not self.item_key:
            raise ValueError("item_key vacío")
        if self.attempt_seq < 0:
            raise ValueError(f"attempt_seq negativo: {self.attempt_seq}")
        if self.seat < 0:
            raise ValueError(f"seat negativo: {self.seat}")
        if self.elapsed_ms < 0:
            raise ValueError(f"elapsed_ms negativo: {self.elapsed_ms}")
        if self.points < 0:
            raise ValueError(f"points negativos: {self.points}")


async def start_session(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    mode: str,
    content_kind: str,
    play_format: str,
    ruleset_version: int,
    config: Mapping[str, object],
    started_at: datetime,
    owner_user_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
    participants: Sequence[Participant] = (),
) -> None:
    """Escribe la sesión en `playing` con sus sillas y sin commit del borde."""
    session.add(
        GameSession(
            id=session_id,
            mode=mode,
            content_kind=content_kind,
            play_format=play_format,
            ruleset_version=ruleset_version,
            status="playing",
            config=dict(config),
            owner_user_id=owner_user_id,
            room_id=room_id,
            started_at=started_at,
        )
    )
    # Sin `relationship()` entre los modelos el flush no deduce que la silla
    # depende de la sesión: el flush intermedio fija el orden y sigue siendo
    # una sola transacción.
    await session.flush()
    session.add_all(
        GameParticipant(session_id=session_id, seat=seat.seat, user_id=seat.user_id)
        for seat in participants
    )
    await session.commit()


async def finish_session(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    state: SessionState,
    items: Sequence[ItemRecord],
    attempts: Sequence[AttemptRecord],
    participants: Sequence[ParticipantResult] = (),
) -> None:
    """Cierra la sesión y guarda su historial en una sola transacción."""
    row = await _playing_row(session, session_id)
    if row is None:
        return

    _check_records(items, attempts)

    row.status = state.status
    row.score = state.score
    row.correct_count = state.correct_count
    row.longest_streak = state.longest_streak
    row.max_difficulty = state.max_difficulty
    row.ended_at = state.ended_at

    item_rows, item_ids = _item_rows(session_id, items)
    session.add_all(item_rows)
    # Los modelos no declaran `relationship()`: el flush no deduce que el
    # intento depende del ítem y los insertaría en cualquier orden. Un flush
    # intermedio dentro de la misma transacción fija el orden sin partir el
    # cierre en dos commits.
    await session.flush()
    session.add_all(_attempt_rows(item_ids, attempts))
    await _apply_participant_results(session, session_id, participants)
    await session.commit()


async def abandon_session(
    session: AsyncSession, *, session_id: uuid.UUID, ended_at: datetime
) -> None:
    """Cierra sin final: el jugador se fue o la partida no se terminó."""
    await _close_without_history(
        session, session_id=session_id, status="abandoned", ended_at=ended_at
    )


async def invalidate_session(
    session: AsyncSession, *, session_id: uuid.UUID, ended_at: datetime
) -> None:
    """Saca de circulación una sesión que el barrido encontró huérfana."""
    await _close_without_history(
        session, session_id=session_id, status="invalid", ended_at=ended_at
    )


async def _close_without_history(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    status: str,
    ended_at: datetime,
) -> None:
    row = await _playing_row(session, session_id)
    if row is None:
        return

    row.status = status
    row.ended_at = ended_at
    await session.commit()


async def _playing_row(
    session: AsyncSession, session_id: uuid.UUID
) -> GameSession | None:
    """La fila que todavía se puede cerrar, o `None` si no hay nada que hacer.

    `FOR UPDATE` serializa dos cierres concurrentes del mismo proceso o de dos
    réplicas. Si la fila no existe el cierre se pierde, pero el jugador ya vio
    su final: el barrido no puede inventarla.
    """
    row = await session.get(GameSession, session_id, with_for_update=True)
    if row is None:
        logger.warning("la sesión %s no estaba en la base", session_id)
        return None
    if row.status != "playing":
        logger.info("la sesión %s ya estaba cerrada como %s", session_id, row.status)
        return None
    return row


def _check_records(
    items: Sequence[ItemRecord], attempts: Sequence[AttemptRecord]
) -> None:
    """Adelanta lo que la base también rechaza, para fallar antes del commit."""
    keys = [item.item_key for item in items]
    if len(set(keys)) != len(keys):
        raise ValueError("item_key duplicado en la misma sesión")

    known = set(keys)
    unknown = next((a.item_key for a in attempts if a.item_key not in known), None)
    if unknown is not None:
        raise ValueError(f"intento sin ítem en la misma sesión: {unknown}")

    sequences = [(a.item_key, a.seat, a.attempt_seq) for a in attempts]
    if len(set(sequences)) != len(sequences):
        raise ValueError("attempt_seq duplicado para el mismo ítem y silla")


def _item_rows(
    session_id: uuid.UUID, items: Sequence[ItemRecord]
) -> tuple[list[SessionItem], dict[str, uuid.UUID]]:
    rows: list[SessionItem] = []
    ids: dict[str, uuid.UUID] = {}
    for item in items:
        item_id = uuid.uuid4()
        ids[item.item_key] = item_id
        rows.append(
            SessionItem(
                id=item_id,
                session_id=session_id,
                item_key=item.item_key,
                position=item.position,
                content_id=item.content_id,
                difficulty=item.difficulty,
                seconds=item.seconds,
                served_at=item.served_at,
                deadline_at=item.deadline_at,
                closed_at=item.closed_at,
                solution_snapshot=dict(item.solution),
            )
        )
    return rows, ids


def _attempt_rows(
    item_ids: Mapping[str, uuid.UUID], attempts: Sequence[AttemptRecord]
) -> list[SessionAttempt]:
    return [
        SessionAttempt(
            id=uuid.uuid4(),
            item_id=item_ids[attempt.item_key],
            attempt_seq=attempt.attempt_seq,
            seat=attempt.seat,
            submitted_at=attempt.submitted_at,
            submission=dict(attempt.submission),
            correct=attempt.correct,
            elapsed_ms=attempt.elapsed_ms,
            points=attempt.points,
            rejected=attempt.rejected,
        )
        for attempt in attempts
    ]


async def _apply_participant_results(
    session: AsyncSession,
    session_id: uuid.UUID,
    participants: Sequence[ParticipantResult],
) -> None:
    """Las sillas ya existen: se pisan con el resultado del motor.

    Un `merge` podría crear la silla que el arranque nunca abrió; acá se busca
    la fila y se actualiza, y una silla desconocida es un error del llamador.
    """
    if not participants:
        return

    rows = await session.scalars(
        select(GameParticipant).where(GameParticipant.session_id == session_id)
    )
    by_seat = {row.seat: row for row in rows}
    for result in participants:
        row = by_seat.get(result.seat)
        if row is None:
            raise ValueError(f"la silla {result.seat} no jugó esta sesión")
        row.score = result.score
        row.outcome = result.outcome
