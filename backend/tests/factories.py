"""Una fila válida por tabla, con overrides.

Un test de constraints tiene que romper una sola cosa: `question(difficulty=0)`
se lee mejor que seis campos sueltos y deja a la vista qué es lo que la base
debe rechazar.

Dos detalles que importan:

- El `id` se genera acá, no se deja al `default=uuid4` de la columna (que corre
  en el INSERT). Así una fila puede apuntar a su padre antes de que ninguno de
  los dos esté en la base: `match(player_a_id=ana.id)`.
- Los valores únicos (nick, code, content_hash, round_index) salen de un
  correlativo del proceso, así dos filas del mismo test no chocan por
  accidente. La sonda de shell que esto reemplaza ya se había comido ese
  problema: reusaba el hash y el "rechaza" pasaba por duplicado.
"""

import itertools
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.game.constants import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from app.models import (
    ArcadeAnswer,
    ArcadeRun,
    ContentItem,
    ContentSolution,
    Match,
    MatchRound,
    Question,
    Room,
    User,
)

_correlativo = itertools.count(1)


def _n() -> int:
    return next(_correlativo)


def _hash() -> str:
    return f"{_n():064x}"


def _codigo() -> str:
    n = _n()
    letras = []
    for _ in range(ROOM_CODE_LENGTH):
        letras.append(ROOM_CODE_ALPHABET[n % len(ROOM_CODE_ALPHABET)])
        n //= len(ROOM_CODE_ALPHABET)
    return "".join(reversed(letras))


def user(**overrides: Any) -> User:
    return User(**({"id": uuid.uuid4(), "nick": f"jugador{_n()}"} | overrides))


def question(**overrides: Any) -> Question:
    return Question(
        **(
            {
                "id": uuid.uuid4(),
                "category": "geography",
                "difficulty": 2,
                "prompt": "¿Cuál es el río más largo?",
                "options": ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
                "correct_index": 1,
                "content_hash": _hash(),
            }
            | overrides
        )
    )


def content_item(**overrides: Any) -> ContentItem:
    return ContentItem(
        **(
            {
                "id": uuid.uuid4(),
                "kind": "quiz",
                "schema_version": 1,
                "difficulty": 2,
                "categories": ["geography"],
                "payload": {
                    "v": 1,
                    "prompt": "¿Cuál es el río más largo?",
                    "options": ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
                },
                "content_hash": _hash(),
            }
            | overrides
        )
    )


def content_solution(content_id: uuid.UUID, **overrides: Any) -> ContentSolution:
    return ContentSolution(
        **(
            {
                "content_id": content_id,
                "payload": {"v": 1, "correct_index": 1},
            }
            | overrides
        )
    )


def room(host_user_id: uuid.UUID, **overrides: Any) -> Room:
    """Necesita el id del host ya existente: `host_user_id` es FK obligatoria."""
    return Room(
        **(
            {
                "id": uuid.uuid4(),
                "host_user_id": host_user_id,
                "code": _codigo(),
                "config": {"rounds": 7, "seconds": 20},
                "expires_at": datetime.now(UTC) + timedelta(hours=1),
            }
            | overrides
        )
    )


def match(player_a_id: uuid.UUID, player_b_id: uuid.UUID, **overrides: Any) -> Match:
    """Necesita los ids de dos jugadores ya existentes: son FK obligatorias."""
    return Match(
        **(
            {
                "id": uuid.uuid4(),
                "player_a_id": player_a_id,
                "player_b_id": player_b_id,
                "config": {"rounds": 7, "seconds": 20},
            }
            | overrides
        )
    )


def match_round(match_id: uuid.UUID, **overrides: Any) -> MatchRound:
    return MatchRound(
        **(
            {
                "id": uuid.uuid4(),
                "match_id": match_id,
                "round_index": _n(),
                "difficulty": 2,
                "seconds": 20,
                "correct_index": 1,
                # Los valores por defecto son una ronda coherente: A acierta, B no.
                "a_choice": 1,
                "b_choice": 0,
                "a_ms": 3_000,
                "b_ms": 9_000,
                "a_correct": True,
                "b_correct": False,
                "a_points": 145,
                "b_points": 0,
            }
            | overrides
        )
    )


def arcade_run(user_id: uuid.UUID, **overrides: Any) -> ArcadeRun:
    return ArcadeRun(**({"id": uuid.uuid4(), "user_id": user_id} | overrides))


def arcade_answer(run_id: uuid.UUID, **overrides: Any) -> ArcadeAnswer:
    return ArcadeAnswer(
        **(
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "round_index": _n(),
                "difficulty": 3,
                "seconds": 20,
                "correct_index": 1,
                # Ronda coherente: contestó bien y rápido.
                "chosen_index": 1,
                "is_correct": True,
                "ms": 4_200,
                "points": 180,
            }
            | overrides
        )
    )
