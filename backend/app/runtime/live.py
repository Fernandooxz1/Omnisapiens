"""Lo que este proceso tiene vivo, para que el barrendero no mate lo que se juega.

El barrido periódico corre en el mismo proceso que las salas y las partidas, pero
la base no sabe nada de las conexiones. Sin esta vista:

- una sala `waiting` con dos personas conectadas y `expires_at` viejo se marcaría
  `expired` mientras la partida espera para arrancar;
- una sesión `playing` con un socket del otro lado se invalidaría a mitad.

Es de un solo proceso a propósito, igual que `InMemorySessionStore`: el día que
haya más instancias, cada barrido solo ve lo suyo y este registro se muda a
Redis con el resto del estado vivo.
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveRooms:
    """Las salas con jugadores conectados, en cualquier estado."""

    room_ids: frozenset[uuid.UUID] = frozenset()


@dataclass(frozen=True)
class Live:
    """Todo lo vivo del proceso, en una sola pieza para el barrido."""

    rooms: LiveRooms = LiveRooms()
    # Sesiones (`game_sessions`) con socket abierto, sean solo o versus. Las
    # llena el `SessionStore`.
    sessions: frozenset[uuid.UUID] = frozenset()
