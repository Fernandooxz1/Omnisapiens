"""El estado vivo de la sala: lock, entrega, vencimientos y las dos escrituras.

El reloj es del test: `FakeClock.sleep` no duerme, espera a que el test mueva la
hora. Así una partida entera por vencimientos corre en milisegundos y no hay que
esperar los 10 s reales de cada ronda.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from random import Random

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.match_engine import MatchConfig
from app.game.protocols import (
    Error,
    MatchEnd,
    MatchStart,
    OpponentReturned,
    ReconnectPending,
    RematchWaiting,
    RoundResult,
    RoundStart,
)
from app.game.protocols import RoomState as RoomStateMessage
from app.models import Match, MatchRound, Question, Room, User
from app.runtime.room_manager import InMemoryRoomStore, Outbox

from .factories import question, room, user


class FakeClock:
    """Reloj que el test mueve a mano.

    `sleep` registra el vencimiento y se queda ahí: el tiempo no pasa solo. El
    test avanza la hora y despierta a los que ya vencieron.
    """

    def __init__(self, start: int = 1_000_000) -> None:
        self.ms = start
        self._durmiendo: list[tuple[int, asyncio.Future[None]]] = []

    def now_ms(self) -> int:
        return self.ms

    async def sleep(self, seconds: float) -> None:
        vence = self.ms + int(seconds * 1000)
        futuro: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._durmiendo.append((vence, futuro))
        try:
            await futuro
        finally:
            self._durmiendo = [(d, f) for d, f in self._durmiendo if f is not futuro]

    def advance(self, ms: int) -> None:
        self.ms += ms
        for vence, futuro in self._durmiendo:
            if vence <= self.ms and not futuro.done():
                futuro.set_result(None)


@dataclass
class Harness:
    store: InMemoryRoomStore
    clock: FakeClock


@asynccontextmanager
async def _compartida(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """El manager usa la sesión del test a propósito.

    Sus `commit()` se vuelven SAVEPOINTs y el rollback del final deshace lo que
    escribió, igual que la fixture `client` con los endpoints. Sin esto, los
    tests de la partida ensuciarían `trivia_test`.
    """
    yield session


@pytest.fixture
async def abrir(session: AsyncSession) -> AsyncIterator[Callable[..., Harness]]:
    abiertos: list[InMemoryRoomStore] = []

    def _abrir(
        *,
        grace: int = 20,
        seed: int = 7,
        session_factory: (
            Callable[[], AbstractAsyncContextManager[AsyncSession]] | None
        ) = None,
        shuffle_served_options: bool = False,
    ) -> Harness:
        clock = FakeClock()
        store = InMemoryRoomStore(
            session_factory=session_factory or (lambda: _compartida(session)),
            grace_seconds=grace,
            now_ms=clock.now_ms,
            sleep=clock.sleep,
            rng=Random(seed),
            shuffle_served_options=shuffle_served_options,
        )
        abiertos.append(store)
        return Harness(store=store, clock=clock)

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
    dificultades: tuple[int, ...] = (1, 2, 3, 4, 5),
    session_factory: (
        Callable[[], AbstractAsyncContextManager[AsyncSession]] | None
    ) = None,
    shuffle_served_options: bool = False,
) -> tuple[Harness, User, User, Room]:
    """Dos jugadores, la fila de la sala y el banco que se le pida."""
    h = abrir(
        grace=grace,
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
        session.add(
            question(category="geography", difficulty=dificultad, status="published")
        )
    await session.flush()
    await h.store.open(
        code=fila.code,
        room_id=str(fila.id),
        config=MatchConfig(rounds=rounds, seconds=seconds),
        host_id=str(ana.id),
    )
    return h, ana, beto, fila


async def sentar(
    h: Harness, fila: Room, ana: User, beto: User
) -> tuple[Outbox, Outbox]:
    a_out, b_out = Outbox(), Outbox()
    await h.store.join(code=fila.code, user_id=str(ana.id), nick="ana", outbox=a_out)
    await h.store.join(code=fila.code, user_id=str(beto.id), nick="beto", outbox=b_out)
    # El del segundo `join` también cambia el estado del primero: se limpia todo
    # lo del lobby para que cada test mire solo lo que provoca.
    drain(a_out)
    drain(b_out)
    return a_out, b_out


def drain(outbox: Outbox) -> list:
    """Lo que llegó a la cola y nadie leyó todavía."""
    mensajes = []
    while not outbox.empty():
        mensajes.append(outbox.get_nowait())
    return mensajes


def uno(mensajes: list, tipo: type):
    """El único mensaje de ese tipo: cualquier otro tipo se delata acá."""
    encontrados = [mensaje for mensaje in mensajes if isinstance(mensaje, tipo)]
    assert len(encontrados) == 1, mensajes
    return encontrados[0]


async def correr(h: Harness, ms: int = 0) -> None:
    """Mueve el reloj y le da tiempo real a la tarea de vencimientos y a su I/O."""
    h.clock.advance(ms)
    for _ in range(10):
        await asyncio.sleep(0.02)


async def jugar_ronda(
    h: Harness, fila: Room, ana: User, beto: User, ronda: int
) -> None:
    """Ana acierta (la semilla tiene el `correct_index` en 1) y Beto no."""
    await h.store.answer(
        code=fila.code, user_id=str(ana.id), round_index=ronda, choice=1
    )
    await h.store.answer(
        code=fila.code, user_id=str(beto.id), round_index=ronda, choice=0
    )


async def test_join_sits_the_two_players_and_the_third_is_rejected(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)

    a_out, b_out = Outbox(), Outbox()
    await h.store.join(code=fila.code, user_id=str(ana.id), nick="ana", outbox=a_out)
    await h.store.join(code=fila.code, user_id=str(beto.id), nick="beto", outbox=b_out)

    assert h.store.player_count(fila.code) == 2
    # Ana recibe dos: el de su propia entrada y el que avisa que entró Beto.
    estados = [m for m in drain(a_out) if isinstance(m, RoomStateMessage)]
    assert len(estados) == 2
    assert estados[-1].you.id == str(ana.id)
    assert [jugador.id for jugador in estados[-1].players] == [
        str(ana.id),
        str(beto.id),
    ]
    assert estados[-1].status == "waiting"
    assert uno(drain(b_out), RoomStateMessage).you.nick == "beto"

    caro = user(nick="caro")
    session.add(caro)
    await session.flush()
    c_out = Outbox()
    await h.store.join(code=fila.code, user_id=str(caro.id), nick="caro", outbox=c_out)

    assert uno(drain(c_out), Error).code == "ROOM_FULL"
    assert h.store.player_count(fila.code) == 2


async def test_a_full_outbox_does_not_block_the_room(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-13: un cliente que no lee no puede frenar la sala ni crecer sin tope."""
    h, ana, beto, fila = await sala_armada(session, abrir)
    apretado: Outbox = asyncio.Queue(maxsize=1)
    await h.store.join(code=fila.code, user_id=str(ana.id), nick="ana", outbox=apretado)
    assert apretado.qsize() == 1

    # La entrada de Beto le manda otro estado a Ana: se descarta el viejo.
    await h.store.join(
        code=fila.code, user_id=str(beto.id), nick="beto", outbox=Outbox()
    )

    assert apretado.qsize() == 1


async def test_the_host_starts_and_the_match_row_is_written(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)

    await h.store.start(code=fila.code, user_id=str(ana.id))

    a_msgs = drain(a_out)
    arranque = uno(a_msgs, MatchStart)
    ronda = uno(a_msgs, RoundStart)
    assert arranque.rounds_total == 3
    assert uno(drain(b_out), MatchStart).match_id == arranque.match_id

    assert ronda.round == 0
    assert ronda.total_seconds == 10
    # La respuesta correcta no viaja al cliente: el tipo no tiene dónde guardarla.
    assert not hasattr(ronda, "correct_index")

    partida = await session.scalar(select(Match))
    assert partida is not None
    assert str(partida.id) == arranque.match_id
    assert partida.room_id == fila.id
    assert partida.player_a_id == ana.id
    assert partida.player_b_id == beto.id
    assert partida.config == {"rounds": 3, "seconds": 10}
    assert partida.status == "playing"
    assert partida.ended_at is None


async def test_serving_shuffles_the_options_and_the_correct_one_moves(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-25: la respuesta correcta no puede quedar siempre en la misma letra."""
    h, ana, beto, fila = await sala_armada(session, abrir, shuffle_served_options=True)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    ronda = uno(drain(a_out), RoundStart)
    drain(b_out)

    # La pregunta servida está en la base; su respuesta es el texto, no la letra.
    pregunta = await session.get(Question, uuid.UUID(ronda.question_id))
    assert pregunta is not None
    correcta = pregunta.options[pregunta.correct_index]
    eleccion = ronda.options.index(correcta)

    # Con esta semilla la mezcla cambió el orden: si dejara de barajar, el índice
    # correcto volvería a ser el de la base.
    assert ronda.options != pregunta.options
    assert eleccion != pregunta.correct_index

    # Ana contesta el índice ya remapeado: el motor tiene que darla por correcta.
    await h.store.answer(
        code=fila.code, user_id=str(ana.id), round_index=0, choice=eleccion
    )
    await h.store.answer(
        code=fila.code, user_id=str(beto.id), round_index=0, choice=(eleccion + 1) % 4
    )

    assert uno(drain(a_out), RoundResult).you.correct is True


async def test_only_the_host_starts(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)

    await h.store.start(code=fila.code, user_id=str(beto.id))

    assert uno(drain(b_out), Error).code == "NOT_HOST"
    assert await session.scalar(select(Match)) is None
    assert drain(a_out) == []


async def test_the_match_ends_and_the_rounds_are_written(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_out)

    for ronda in range(3):
        await jugar_ronda(h, fila, ana, beto, ronda)

    fin = uno(drain(a_out), MatchEnd)
    assert fin.reason == "completed"
    assert fin.winner == "you"
    assert fin.scores.you > 0
    assert fin.scores.opponent == 0
    assert uno(drain(b_out), MatchEnd).winner == "opponent"

    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "finished"
    assert partida.winner_id == ana.id
    assert partida.score_a == fin.scores.you
    assert partida.score_b == 0
    assert partida.ended_at is not None

    rondas = (await session.scalars(select(MatchRound))).all()
    assert sorted(ronda.round_index for ronda in rondas) == [0, 1, 2]
    assert all(ronda.match_id == partida.id for ronda in rondas)
    assert all(ronda.a_correct and not ronda.b_correct for ronda in rondas)
    assert all(ronda.a_points > 0 and ronda.b_points == 0 for ronda in rondas)
    assert all(
        ronda.a_rejected is None and ronda.b_rejected is None for ronda in rondas
    )


async def test_the_clock_expires_a_round_and_serves_the_next_one(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    primera = uno(drain(a_out), RoundStart)
    drain(b_out)

    # Solo contesta Ana: la ronda la cierra el reloj, no la segunda respuesta.
    await h.store.answer(code=fila.code, user_id=str(ana.id), round_index=0, choice=1)
    await correr(h, primera.total_seconds * 1000)

    a_msgs = drain(a_out)
    resultado = uno(a_msgs, RoundResult)
    assert resultado.round == 0
    assert resultado.you.correct
    assert not resultado.opponent.correct
    assert resultado.scores.you > 0
    assert uno(a_msgs, RoundStart).round == 1
    assert uno(drain(b_out), RoundResult).you.correct is False


async def test_the_clock_retries_and_survives_a_transient_database_error(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-02: un error de base al vencer no puede dejar la sala sin reloj."""
    caer = {"armado": False}

    @asynccontextmanager
    async def fabrica() -> AsyncIterator[AsyncSession]:
        if caer["armado"]:
            caer["armado"] = False
            raise RuntimeError("la base se cayó")
        yield session

    h, ana, beto, fila = await sala_armada(session, abrir, session_factory=fabrica)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_out)

    # Ana contesta y el reloj cierra cada ronda. La última ronda cierra la partida:
    # ahí falla la sesión, una sola vez.
    for ronda in range(3):
        await h.store.answer(
            code=fila.code, user_id=str(ana.id), round_index=ronda, choice=1
        )
        caer["armado"] = ronda == 2
        await correr(h, 10_000)
    await correr(h, 1_000)  # el reintento duerme el backoff, en el reloj falso

    fin = uno(drain(a_out), MatchEnd)
    assert fin.reason == "completed"
    assert fin.winner == "you"
    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "finished"


async def test_the_clock_gives_up_and_warns_after_repeated_database_errors(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """Si la base no vuelve, la sala corta con aviso en vez de quedar muda."""
    caidos = {"restantes": 0}

    @asynccontextmanager
    async def fabrica() -> AsyncIterator[AsyncSession]:
        if caidos["restantes"] > 0:
            caidos["restantes"] -= 1
            raise RuntimeError("la base se cayó")
        yield session

    h, ana, beto, fila = await sala_armada(session, abrir, session_factory=fabrica)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_out)

    for ronda in range(3):
        await h.store.answer(
            code=fila.code, user_id=str(ana.id), round_index=ronda, choice=1
        )
        caidos["restantes"] = 5 if ronda == 2 else 0
        await correr(h, 10_000)
    for _ in range(4):  # cada reintento espera el backoff
        await correr(h, 1_000)

    assert uno(drain(a_out), Error).code == "ROOM_CLOCK_DOWN"
    assert uno(drain(b_out), Error).code == "ROOM_CLOCK_DOWN"
    # La fila quedó abierta a propósito: la cierra el barrendero, no el reloj.
    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "playing"


async def test_the_clock_retries_a_next_round_that_failed_to_load(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """El error puede caer al elegir la próxima pregunta, no al cerrar la partida."""
    caer = {"armado": False}

    @asynccontextmanager
    async def fabrica() -> AsyncIterator[AsyncSession]:
        if caer["armado"]:
            caer["armado"] = False
            raise RuntimeError("la base se cayó")
        yield session

    h, ana, beto, fila = await sala_armada(session, abrir, session_factory=fabrica)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_out)

    # Ana contesta la ronda 0; el reloj la resuelve pero falla al cargar la 1.
    await h.store.answer(code=fila.code, user_id=str(ana.id), round_index=0, choice=1)
    caer["armado"] = True
    await correr(h, 10_000)
    await correr(h, 1_000)  # el reintento del reloj sirve la ronda pendiente

    a_msgs = drain(a_out)
    resultado = uno(a_msgs, RoundResult)
    assert resultado.round == 0
    assert resultado.you.correct
    assert uno(a_msgs, RoundStart).round == 1
    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "playing"


async def test_a_disconnect_opens_the_grace_and_the_clock_abandons(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_out)

    await h.store.disconnect(code=fila.code, user_id=str(beto.id), outbox=b_out)

    assert uno(drain(a_out), ReconnectPending).seconds_left == 20
    assert h.store.player_count(fila.code) == 1

    await correr(h, 20_000)

    fin = uno(drain(a_out), MatchEnd)
    assert fin.reason == "abandoned"
    assert fin.winner == "you"
    assert fin.rounds == []  # no se resolvió ninguna ronda
    # Al que se fue se le soltó la cola: no acumula mensajes que nadie va a leer.
    assert drain(b_out) == []
    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "abandoned"
    assert partida.winner_id == ana.id
    assert (await session.scalars(select(MatchRound))).all() == []


async def test_reconnecting_within_the_grace_resumes_the_round(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    original = uno(drain(a_out), RoundStart)
    drain(b_out)

    await h.store.disconnect(code=fila.code, user_id=str(beto.id), outbox=b_out)
    uno(drain(a_out), ReconnectPending)

    # Vuelve con un socket nuevo, dentro de la ventana: la ronda corre la pausa.
    h.clock.advance(5_000)
    b_nuevo = Outbox()
    await h.store.join(
        code=fila.code, user_id=str(beto.id), nick="beto", outbox=b_nuevo
    )

    assert isinstance(uno(drain(a_out), OpponentReturned), OpponentReturned)
    reanudada = uno(drain(b_nuevo), RoundStart)
    assert reanudada.round == 0
    assert reanudada.ends_at == original.ends_at + 5_000
    assert h.store.player_count(fila.code) == 2

    # Y la partida sigue: la ronda se puede cerrar con las dos respuestas.
    await jugar_ronda(h, fila, ana, beto, 0)
    assert uno(drain(a_out), RoundResult).round == 0


async def test_the_old_socket_closing_late_does_not_abandon_the_reconnected_player(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-01: un corte silencioso deja al socket viejo vivo hasta el timeout.

    El cliente reconecta antes de que el servidor note el corte. Cuando el socket
    viejo por fin cierra (su `finally` corre con el `outbox` que usó), no puede
    desmontar la silla nueva: la partida sigue en pie.
    """
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_viejo = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    drain(a_out)
    drain(b_viejo)

    # Reconecta con socket nuevo: el server todavía no notó el corte del viejo.
    b_nuevo = Outbox()
    await h.store.join(
        code=fila.code, user_id=str(beto.id), nick="beto", outbox=b_nuevo
    )
    assert h.store.player_count(fila.code) == 2
    drain(a_out)
    drain(b_nuevo)

    # Recién ahora el socket viejo pasa por su `finally`.
    await h.store.disconnect(code=fila.code, user_id=str(beto.id), outbox=b_viejo)

    # La silla nueva sigue en pie y la gracia no se abrió.
    assert h.store.player_count(fila.code) == 2
    assert [m for m in drain(a_out) if isinstance(m, ReconnectPending)] == []

    await correr(h, 20_000)

    assert [m for m in drain(a_out) if isinstance(m, MatchEnd)] == []
    partida = await session.scalar(select(Match))
    assert partida is not None
    assert partida.status == "playing"


async def test_the_rematch_starts_and_writes_a_new_match(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.start(code=fila.code, user_id=str(ana.id))
    for ronda in range(3):
        await jugar_ronda(h, fila, ana, beto, ronda)
    primera = await session.scalar(select(Match))
    assert primera is not None
    drain(a_out)
    drain(b_out)

    await h.store.rematch(code=fila.code, user_id=str(ana.id))
    assert isinstance(uno(drain(b_out), RematchWaiting), RematchWaiting)
    assert drain(a_out) == []

    await h.store.rematch(code=fila.code, user_id=str(beto.id))

    a_msgs = drain(a_out)
    arranque = uno(a_msgs, MatchStart)
    assert arranque.match_id != str(primera.id)
    assert uno(a_msgs, RoundStart).round == 0
    assert uno(drain(b_out), MatchStart).match_id == arranque.match_id

    partidas = (await session.scalars(select(Match))).all()
    assert len(partidas) == 2
    nueva = next(partida for partida in partidas if partida.id != primera.id)
    assert str(nueva.id) == arranque.match_id
    assert nueva.status == "playing"
    assert nueva.ended_at is None
    assert primera.status == "finished"


async def test_the_room_row_follows_the_match_lifecycle(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-04: la fila de `rooms` no puede quedarse en `waiting` toda la vida."""
    h, ana, beto, fila = await sala_armada(session, abrir)
    lobby_expira = fila.expires_at
    a_out, _ = await sentar(h, fila, ana, beto)

    await h.store.start(code=fila.code, user_id=str(ana.id))
    await session.refresh(fila)
    assert fila.status == "playing"
    # El vencimiento pasa a ser el techo de la partida, no el del lobby.
    assert fila.expires_at < lobby_expira

    for ronda in range(3):
        await jugar_ronda(h, fila, ana, beto, ronda)
    await session.refresh(fila)
    assert fila.status == "finished"

    # Se va uno de la sala terminada: vuelve al lobby y la fila lo refleja.
    await h.store.disconnect(code=fila.code, user_id=str(ana.id), outbox=a_out)
    await session.refresh(fila)
    assert fila.status == "waiting"


async def test_a_dead_room_is_evicted_when_another_one_opens(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    """H-03: una sala sin conexiones ni partida no vive para siempre en `_rooms`."""
    h, ana, beto, fila = await sala_armada(session, abrir)
    a_out, b_out = await sentar(h, fila, ana, beto)
    await h.store.disconnect(code=fila.code, user_id=str(ana.id), outbox=a_out)
    await h.store.disconnect(code=fila.code, user_id=str(beto.id), outbox=b_out)
    assert h.store.room_count() == 1

    # Sin nadie conectado, al vencer el idle la sala es desalojable.
    await correr(h, 600_000)
    otra = room(ana.id, config={"rounds": 3, "seconds": 10})
    session.add(otra)
    await session.flush()
    await h.store.open(
        code=otra.code,
        room_id=str(otra.id),
        config=MatchConfig(rounds=3, seconds=10),
        host_id=str(ana.id),
    )

    assert h.store.room_count() == 1
    assert h.store.player_count(fila.code) == 0


async def test_without_a_question_for_the_round_the_room_reports_it(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h, ana, beto, fila = await sala_armada(session, abrir, dificultades=())
    a_out, b_out = await sentar(h, fila, ana, beto)

    await h.store.start(code=fila.code, user_id=str(ana.id))

    a_msgs = drain(a_out)
    assert isinstance(uno(a_msgs, MatchStart), MatchStart)
    assert uno(a_msgs, Error).code == "NO_QUESTIONS"
    assert uno(drain(b_out), Error).code == "NO_QUESTIONS"
    # La partida quedó abierta en la base: la cierra el barrendero, no el vacío.
    assert (await session.scalar(select(Match))).status == "playing"


async def test_a_question_out_of_the_rounds_range_is_not_served(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    # La ronda 0 pide dificultad 1-2: una pregunta de 5 no entra, y servirla
    # reventaría el `next_round` del motor.
    h, ana, beto, fila = await sala_armada(session, abrir, dificultades=(5,))
    a_out, b_out = await sentar(h, fila, ana, beto)

    await h.store.start(code=fila.code, user_id=str(ana.id))

    a_msgs = drain(a_out)
    assert uno(a_msgs, Error).code == "NO_QUESTIONS"
    assert [m for m in a_msgs if isinstance(m, RoundStart)] == []
    assert uno(drain(b_out), Error).code == "NO_QUESTIONS"


async def test_an_unknown_room_is_ignored(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> None:
    h = abrir()
    ajeno = Outbox()

    await h.store.join(
        code="ZZZZZZ", user_id=str(uuid.uuid4()), nick="ana", outbox=ajeno
    )
    await h.store.start(code="ZZZZZZ", user_id="x")
    await h.store.answer(code="ZZZZZZ", user_id="x", round_index=0, choice=1)
    await h.store.disconnect(code="ZZZZZZ", user_id="x", outbox=ajeno)
    await h.store.rematch(code="ZZZZZZ", user_id="x")
    await h.store.sync(code="ZZZZZZ", user_id="x")

    assert h.store.player_count("ZZZZZZ") == 0
    assert drain(ajeno) == []
    assert (await session.scalars(select(Match))).all() == []
