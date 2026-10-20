"""Lo que este proceso tiene vivo, para que el barrendero no mate lo que se juega.

El barrido periódico corre en el mismo proceso que las salas y las partidas, pero
la base no sabe nada de las conexiones. Sin esta vista:

- una sala `waiting` con dos personas conectadas y `expires_at` viejo se marcaría
  `expired` mientras la partida espera para arrancar;
- una partida viva de más de `stale_match_minutes` se anularía en pleno juego;
- una partida de arcade legítima y larga se marcaría `invalid` a mitad.

Con las sesiones genéricas pasa lo mismo: una sesión `playing` con un socket del
otro lado no se puede invalidar a mitad de partida.

Es de un solo proceso a propósito, igual que `InMemorySessionStore`: el día que
haya más instancias, cada barrido solo ve lo suyo y este registro se muda a
Redis con el resto del estado vivo.
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveRooms:
    """Las salas con jugadores conectados y las partidas que están jugándose.

    `room_ids` incluye salas en cualquier estado con presencia; `match_ids` solo
    las que tienen una partida `playing`, que es lo que el barrido anula.
    """

    room_ids: frozenset[uuid.UUID] = frozenset()
    match_ids: frozenset[uuid.UUID] = frozenset()


@dataclass(frozen=True)
class Live:
    """Todo lo vivo del proceso, en una sola pieza para el barrido."""

    rooms: LiveRooms = LiveRooms()
    arcade_runs: frozenset[uuid.UUID] = frozenset()
    # Sesiones genéricas (`game_sessions`) con socket abierto. Las llena el
    # `SessionStore` en la fase 4.1; hasta entonces queda vacío.
    sessions: frozenset[uuid.UUID] = frozenset()


class LiveArcadeRuns:
    """Las partidas con socket abierto. El handler las anota y las suelta.

    No guarda la conexión ni el estado: solo el id, que es lo que el `UPDATE` del
    barrendero necesita para no incluir.
    """

    def __init__(self) -> None:
        self._ids: set[uuid.UUID] = set()

    def add(self, run_id: uuid.UUID) -> None:
        self._ids.add(run_id)

    def discard(self, run_id: uuid.UUID) -> None:
        """Idempotente: cierra el socket y el fin de la partida se pisan sin drama."""
        self._ids.discard(run_id)

    def ids(self) -> frozenset[uuid.UUID]:
        return frozenset(self._ids)


live_arcade_runs = LiveArcadeRuns()
