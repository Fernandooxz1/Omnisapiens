"""El armado común de las salas en vivo: store, reloj falso y base compartida.

No es un módulo de tests (no empieza con `test_`): lo importan `test_room_ws` y
`ws_fixtures` para que los escenarios y los tests del borde usen el mismo reloj,
el mismo `Random` y la misma sesión de base que el resto de la suite.
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass
from random import Random

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.versus_engine import VersusConfig
from app.models import Room, User
from app.runtime.session_store import InMemorySessionStore
from app.ws.room_ws import RoomRuntime, SessionFactory

from .clock import FakeClock
from .factories import quiz_content, room, user


@dataclass
class Harness:
    store: InMemorySessionStore
    clock: FakeClock
    runtime: RoomRuntime
    session_factory: SessionFactory


@asynccontextmanager
async def _compartida(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """El store usa la sesión del test a propósito.

    Sus `commit()` se vuelven SAVEPOINTs y el rollback del final deshace lo que
    escribió, igual que la fixture `client` con los endpoints. Sin esto, los
    tests del borde ensuciarían `trivia_test`.
    """
    yield session


@pytest.fixture
async def abrir(session: AsyncSession) -> AsyncIterator[Callable[..., Harness]]:
    abiertos: list[InMemorySessionStore] = []

    def _abrir(
        *,
        grace: int = 20,
        seed: int = 7,
        reveal: float = 0.0,
        session_factory: SessionFactory | None = None,
        shuffle_served_options: bool = False,
    ) -> Harness:
        clock = FakeClock()

        async def despierto() -> None:
            return None

        def dormir(seconds: float) -> Coroutine[object, object, None]:
            # El test no espera en tiempo real: cuando la pausa pedida es la de
            # revelación, adelanta el reloj. Es sincrónica a propósito: el reloj
            # falso calcula el vencimiento al llamar, no al ejecutar la corrutina.
            if reveal and seconds == reveal:
                clock.advance(int(reveal * 1000))
                return despierto()
            return clock.sleep(seconds)

        rng = Random(seed)
        fabrica = session_factory or (lambda: _compartida(session))
        store = InMemorySessionStore(
            reveal_seconds=reveal,
            grace_seconds=grace,
            now_ms=clock.now_ms,
            sleep=dormir,
            rng=rng,
            shuffle_served_options=shuffle_served_options,
        )
        abiertos.append(store)
        return Harness(
            store=store,
            clock=clock,
            runtime=RoomRuntime(now_ms=clock.now_ms, rng=rng),
            session_factory=fabrica,
        )

    yield _abrir
    for store in abiertos:
        await store.close()


async def sala_armada(
    session: AsyncSession,
    abrir: Callable[..., Harness],
    *,
    grace: int = 20,
    rounds: int = 3,
    seconds: int = 10,
    reveal: float = 0.0,
    dificultades: tuple[int, ...] = (1, 2, 3, 4, 5),
    session_factory: SessionFactory | None = None,
    shuffle_served_options: bool = False,
) -> tuple[Harness, User, User, Room]:
    """Dos jugadores, la fila de la sala y el banco que se le pida."""
    h = abrir(
        grace=grace,
        reveal=reveal,
        session_factory=session_factory,
        shuffle_served_options=shuffle_served_options,
    )
    ana, beto = user(nick="ana"), user(nick="beto")
    # Dos flushes: sin `relationship()` el ORM no deduce que `rooms` va después
    # de `users` (el mismo problema que ya está anotado en el plan).
    session.add_all([ana, beto])
    await session.flush()

    fila = room(ana.id, config={"rounds": rounds, "seconds": seconds})
    session.add(fila)
    for dificultad in dificultades:
        session.add_all(
            quiz_content(
                category="geography", difficulty=dificultad, status="published"
            )
        )
    await session.flush()
    return h, ana, beto, fila


def config(fila: Room) -> VersusConfig:
    return VersusConfig(**fila.config)


async def correr(h: Harness, ms: int = 0) -> None:
    """Mueve el reloj y le da tiempo real a la tarea de vencimientos y a su I/O."""
    h.clock.advance(ms)
    for _ in range(10):
        await asyncio.sleep(0.02)
