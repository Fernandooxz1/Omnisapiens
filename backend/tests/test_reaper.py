"""El barrendero: lo que quedó abierto de una partida que ya no existe.

Los barridos se prueban con una hora fija: el barrendero recibe `now` para no
depender del reloj real.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GameSession, Room
from app.runtime.live import Live, LiveRooms
from app.services.reaper import sweep

from .factories import game_session, room, user

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


async def _status(session: AsyncSession, model: type, pk: object) -> str:
    valor = await session.scalar(select(model.status).where(model.id == pk))
    assert isinstance(valor, str)
    return valor


async def test_the_sweeper_expires_only_waiting_rooms_past_their_deadline(
    session: AsyncSession,
) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()

    vencida = room(ana.id, expires_at=NOW - timedelta(seconds=1))
    fresca = room(ana.id, expires_at=NOW + timedelta(minutes=5))
    # Un partida en curso también puede tener `expires_at` viejo (H-04).
    en_partida = room(ana.id, status="playing", expires_at=NOW - timedelta(hours=1))
    session.add_all([vencida, fresca, en_partida])
    await session.flush()

    resultado = await sweep(session, now=NOW)

    assert resultado.expired_rooms == 1
    assert await _status(session, Room, vencida.id) == "expired"
    assert await _status(session, Room, fresca.id) == "waiting"
    assert await _status(session, Room, en_partida.id) == "playing"


async def test_the_sweeper_invalidates_sessions_a_dead_process_left_playing(
    session: AsyncSession,
) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()

    vieja = game_session(owner_user_id=ana.id, started_at=NOW - timedelta(minutes=30))
    fresca = game_session(owner_user_id=ana.id, started_at=NOW - timedelta(minutes=5))
    # Una sala esperando no la toca este barrido.
    esperando = room(ana.id, expires_at=NOW + timedelta(minutes=5))
    session.add_all([vieja, fresca, esperando])
    await session.flush()

    resultado = await sweep(session, now=NOW, stale_after=timedelta(minutes=15))

    assert resultado.invalidated_sessions == 1
    assert await _status(session, GameSession, vieja.id) == "invalid"
    assert await _status(session, GameSession, fresca.id) == "playing"
    assert await _status(session, Room, esperando.id) == "waiting"

    ended = await session.scalar(
        select(GameSession.ended_at).where(GameSession.id == vieja.id)
    )
    assert ended == NOW


async def test_the_sweep_is_idempotent(session: AsyncSession) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()
    session.add(room(ana.id, expires_at=NOW - timedelta(minutes=1)))
    session.add(
        game_session(owner_user_id=ana.id, started_at=NOW - timedelta(minutes=30))
    )
    await session.flush()

    primera = await sweep(session, now=NOW)
    segunda = await sweep(session, now=NOW)

    assert (primera.expired_rooms, primera.invalidated_sessions) == (1, 1)
    assert (segunda.expired_rooms, segunda.invalidated_sessions) == (0, 0)


async def test_the_sweeper_leaves_what_the_process_reports_live(
    session: AsyncSession,
) -> None:
    """En régimen, una fila vieja puede tener un socket del otro lado.

    El barrido periódico recibe lo vivo en memoria y lo excluye; el siguiente
    barrido, sin nada vivo (proceso muerto), sí las cierra.
    """
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()

    sala_viva = room(ana.id, expires_at=NOW - timedelta(minutes=1))
    sesion_viva = game_session(
        owner_user_id=ana.id, started_at=NOW - timedelta(minutes=30)
    )
    session.add_all([sala_viva, sesion_viva])
    await session.flush()

    live = Live(
        rooms=LiveRooms(room_ids=frozenset({sala_viva.id})),
        sessions=frozenset({sesion_viva.id}),
    )
    primero = await sweep(session, now=NOW, live=live)

    assert (primero.expired_rooms, primero.invalidated_sessions) == (0, 0)
    assert await _status(session, Room, sala_viva.id) == "waiting"
    assert await _status(session, GameSession, sesion_viva.id) == "playing"

    segundo = await sweep(session, now=NOW)

    assert (segundo.expired_rooms, segundo.invalidated_sessions) == (1, 1)
