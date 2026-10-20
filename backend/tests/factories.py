"""Una fila válida por tabla, con overrides.

Un test de constraints tiene que romper una sola cosa: `question(difficulty=0)`
se lee mejor que seis campos sueltos y deja a la vista qué es lo que la base
debe rechazar.

Dos detalles que importan:

- El `id` se genera acá, no se deja al `default=uuid4` de la columna (que corre
  en el INSERT). Así una fila puede apuntar a su padre antes de que ninguno de
  los dos esté en la base: `match(player_a_id=ana.id)`.
- Los valores únicos (nick, code, content_hash, item_key) salen de un
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
    ContentItem,
    ContentSolution,
    GameParticipant,
    GameSession,
    Room,
    SessionAttempt,
    SessionItem,
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


def quiz_content(
    *,
    id: uuid.UUID | None = None,
    category: str = "geography",
    difficulty: int = 2,
    prompt: str = "¿Cuál es el río más largo?",
    options: list[str] | None = None,
    correct_index: int = 1,
    explanation: str | None = None,
    status: str = "draft",
    media_type: str = "none",
    media_url: str | None = None,
    **overrides: Any,
) -> tuple[ContentItem, ContentSolution]:
    """Un ítem de quiz con su solución: las dos filas que sirve el banco.

    Se devuelven juntas porque el juego no puede servir un ítem sin solución:
    separarlas dejaba la mitad de los tests armando el mismo par a mano.
    """
    item = content_item(
        id=id or uuid.uuid4(),
        difficulty=difficulty,
        status=status,
        categories=[category],
        payload={
            "v": 1,
            "prompt": prompt,
            "options": options or ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            "media": {"type": media_type, "url": media_url},
        },
        media_type=media_type,
        media_url=media_url,
        **overrides,
    )
    solution = content_solution(
        item.id,
        payload={"v": 1, "correct_index": correct_index, "explanation": explanation},
    )
    return item, solution


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


def game_session(**overrides: Any) -> GameSession:
    return GameSession(
        **(
            {
                "id": uuid.uuid4(),
                "mode": "trivia_arcade",
                "content_kind": "quiz",
                "play_format": "arcade",
                "ruleset_version": 1,
                "config": {"lives": 3},
            }
            | overrides
        )
    )


def game_participant(
    session_id: uuid.UUID, user_id: uuid.UUID, **overrides: Any
) -> GameParticipant:
    return GameParticipant(
        **(
            {
                "session_id": session_id,
                "seat": 0,
                "user_id": user_id,
            }
            | overrides
        )
    )


def session_item(session_id: uuid.UUID, **overrides: Any) -> SessionItem:
    ahora = datetime.now(UTC)
    return SessionItem(
        **(
            {
                "id": uuid.uuid4(),
                "session_id": session_id,
                "item_key": str(_n()),
                "position": _n(),
                "difficulty": 2,
                "seconds": 20,
                "served_at": ahora,
                "deadline_at": ahora + timedelta(seconds=20),
                "solution_snapshot": {"v": 1, "correct_index": 1},
            }
            | overrides
        )
    )


def session_attempt(item_id: uuid.UUID, **overrides: Any) -> SessionAttempt:
    return SessionAttempt(
        **(
            {
                "id": uuid.uuid4(),
                "item_id": item_id,
                "attempt_seq": _n(),
                "seat": 0,
                "submitted_at": datetime.now(UTC),
                "submission": {"type": "choice", "index": 1},
                "correct": True,
                "elapsed_ms": 3_000,
                "points": 145,
            }
            | overrides
        )
    )
