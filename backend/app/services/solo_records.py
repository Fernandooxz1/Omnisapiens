"""Traduce el historial del motor solo a las filas de `sessions`.

El arcade viejo y el canal canónico persisten el mismo `RoundRecord`: cambia el
protocolo del cliente, no el historial. El servicio de sesiones sigue siendo el
único que escribe; acá solo se arma lo que va a escribir.
"""

import uuid

from app.game.solo_engine import RoundRecord
from app.services import sessions
from app.ws.common import to_datetime

SOLUTION_VERSION = 1


def submission(choice: int | None) -> dict[str, object]:
    """La respuesta del quiz; una omisión no inventa una opción."""
    if choice is None:
        return {}
    return {"type": "choice", "index": choice}


def item_records(records: tuple[RoundRecord, ...]) -> list[sessions.ItemRecord]:
    return [
        sessions.ItemRecord(
            item_key=str(record.round_index),
            position=record.round_index,
            content_id=uuid.UUID(record.question_id),
            difficulty=record.difficulty,
            seconds=record.seconds,
            served_at=to_datetime(record.served_at_ms),
            deadline_at=to_datetime(record.served_at_ms + record.seconds * 1000),
            closed_at=to_datetime(record.served_at_ms + record.elapsed_ms),
            solution={
                "v": SOLUTION_VERSION,
                "correct_index": record.correct_index,
            },
        )
        for record in records
    ]


def attempt_records(records: tuple[RoundRecord, ...]) -> list[sessions.AttemptRecord]:
    return [
        sessions.AttemptRecord(
            item_key=str(record.round_index),
            attempt_seq=0,
            submitted_at=to_datetime(record.served_at_ms + record.elapsed_ms),
            submission=submission(record.choice),
            correct=record.correct,
            elapsed_ms=record.elapsed_ms,
            points=record.points,
            rejected=record.rejected.value if record.rejected is not None else None,
        )
        for record in records
    ]


__all__ = ["SOLUTION_VERSION", "attempt_records", "item_records", "submission"]
