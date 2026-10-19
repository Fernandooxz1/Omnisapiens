"""Fixtures compartidas por los tests de transcripts y de fuga.

Los escenarios necesitan las mismas dos preparaciones que ya usan los tests de
cada WebSocket. Se copian acá con nombres propios (`arcade_*`, `room_*`) para
poder pedirlas en el mismo módulo sin que las fixture se pisen.
"""

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from random import Random

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.game.match_engine import MatchConfig
from app.main import app
from app.models import Room, User
from app.runtime.session_store import InMemorySessionStore
from app.security.tokens import create_guest_token
from app.ws.arcade_ws import (
    ArcadeRuntime,
    get_arcade_redis,
    get_arcade_runtime,
    get_session_store,
)
from app.ws.room_ws import get_room_store

from . import test_room_manager
from .clock import FakeClock
from .factories import quiz_content, room, user
from .test_room_manager import Harness
from .ws_client import WebSocketClient

abrir = test_room_manager.abrir


@dataclass(frozen=True)
class ArcadeApi:
    session: AsyncSession
    redis: Redis
    user: User
    clock: FakeClock
    runtime: ArcadeRuntime
    store: InMemorySessionStore


@pytest.fixture
async def arcade_api(
    session: AsyncSession, redis: Redis, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[ArcadeApi]:
    usuario = user(nick="ana")
    session.add(usuario)
    await session.flush()

    clock = FakeClock()
    # La pausa de revelación no aporta al transcript: el reloj no se mueve sola.
    monkeypatch.setattr(settings, "reveal_seconds", 0.0)

    async def despierto() -> None:
        return None

    def dormir(seconds: float) -> Coroutine[object, object, None]:
        if settings.reveal_seconds and seconds == settings.reveal_seconds:
            clock.advance(int(seconds * 1000))
            return despierto()
        return clock.sleep(seconds)

    runtime = ArcadeRuntime(now_ms=clock.now_ms, rng=Random(7))
    store = InMemorySessionStore(now_ms=clock.now_ms, sleep=dormir, rng=runtime.rng)

    async def _sesion() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_arcade_runtime] = lambda: runtime
    app.dependency_overrides[get_arcade_redis] = lambda: redis
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        yield ArcadeApi(
            session=session,
            redis=redis,
            user=usuario,
            clock=clock,
            runtime=runtime,
            store=store,
        )
    finally:
        await store.close()
        app.dependency_overrides.clear()


@pytest.fixture
def arcade_connect(arcade_api: ArcadeApi) -> Callable[[User], WebSocketClient]:
    def _connect(usuario: User) -> WebSocketClient:
        token = create_guest_token(usuario.id, usuario.nick)
        return WebSocketClient(app, "/ws/arcade", query=f"token={token}")

    return _connect


@dataclass(frozen=True)
class RoomApi:
    harness: Harness
    session: AsyncSession
    host: User
    guest: User
    room: Room


@pytest.fixture
async def room_api(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> AsyncIterator[RoomApi]:
    # Preguntas con ids fijos: el selector ordena por id y con UUIDs aleatorios
    # el golden cambiaría de contenido en cada corrida.
    harness = abrir()
    ana, beto = user(nick="ana"), user(nick="beto")
    session.add_all([ana, beto])
    await session.flush()

    fila = room(ana.id, config={"rounds": 3, "seconds": 10})
    session.add(fila)
    for dificultad in (1, 2, 3, 4, 5):
        session.add_all(
            quiz_content(
                id=uuid.UUID(int=dificultad),
                category="geography",
                difficulty=dificultad,
                status="published",
                prompt=f"pregunta {dificultad}",
            )
        )
    await session.flush()
    await harness.store.open(
        code=fila.code,
        room_id=str(fila.id),
        config=MatchConfig(rounds=3, seconds=10),
        host_id=str(ana.id),
    )

    async def _sesion() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_room_store] = lambda: harness.store
    try:
        yield RoomApi(harness=harness, session=session, host=ana, guest=beto, room=fila)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def room_connect(room_api: RoomApi) -> Callable[..., WebSocketClient]:
    def _connect(quien: User, *, code: str | None = None) -> WebSocketClient:
        token = create_guest_token(quien.id, quien.nick)
        return WebSocketClient(
            app, f"/ws/room/{code or room_api.room.code}", query=f"token={token}"
        )

    return _connect
