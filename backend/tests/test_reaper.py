"""El barrendero: lo que quedó abierto de una corrida que ya no existe.

Los dos barridos se prueban con una hora fija: el barrendero recibe `now` para no
depender del reloj real.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Match, Room
from app.services.reaper import sweep

from .factories import match, room, user

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


async def test_the_sweeper_voids_matches_a_dead_process_left_playing(
    session: AsyncSession,
) -> None:
    ana, beto = user(nick="ana"), user(nick="beto")
    session.add_all([ana, beto])
    await session.flush()

    vieja = match(ana.id, beto.id, started_at=NOW - timedelta(minutes=30))
    fresca = match(ana.id, beto.id, started_at=NOW - timedelta(minutes=5))
    session.add_all([vieja, fresca])
    await session.flush()

    resultado = await sweep(session, now=NOW, stale_after=timedelta(minutes=15))

    assert resultado.voided_matches == 1
    assert await _status(session, Match, vieja.id) == "void"
    assert await _status(session, Match, fresca.id) == "playing"

    ended = await session.scalar(select(Match.ended_at).where(Match.id == vieja.id))
    winner = await session.scalar(select(Match.winner_id).where(Match.id == vieja.id))
    assert ended == NOW
    assert winner is None


async def test_the_sweep_is_idempotent(session: AsyncSession) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()
    session.add(room(ana.id, expires_at=NOW - timedelta(minutes=1)))
    await session.flush()

    primera = await sweep(session, now=NOW)
    segunda = await sweep(session, now=NOW)

    assert (primera.expired_rooms, primera.voided_matches) == (1, 0)
    assert (segunda.expired_rooms, segunda.voided_matches) == (0, 0)
