"""Las sesiones versus en vivo: sillas, entrega, gracia, pausa y revancha.

El contenido lo inyecta el test: una partida entera corre sin base ni Redis.
`FakeClock` mueve la hora a mano y la tarea de vencimiento resuelve la ronda o
cierra la gracia cuando el test la despierta.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from random import Random

import pytest

from app.game import protocols
from app.game.versus_engine import (
    MatchStatus,
    VersusConfig,
    VersusState,
    VersusStatus,
)
from app.runtime.session_store import InMemorySessionStore
from app.services.question_bank import LoadedQuestion, RoundQuestion

from .clock import FakeClock

HOST = "host-user"
GUEST = "guest-user"
CODE = "K7M2QP"
M1 = "11111111-1111-4111-8111-111111111111"
M2 = "22222222-2222-4222-8222-222222222222"


def loaded(
    qid: str,
    *,
    difficulty: int = 1,
    correct_index: int = 0,
    explanation: str | None = "Porque sí.",
) -> LoadedQuestion:
    return LoadedQuestion(
        question=RoundQuestion(
            id=qid,
            prompt="¿Cuál es el río más largo?",
            options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            category="geography",
            difficulty=difficulty,
            explanation=explanation,
        ),
        correct_index=correct_index,
    )


class Questions:
    """La fuente de ítems: entrega en orden y recuerda lo que le pidieron."""

    def __init__(self, *questions: LoadedQuestion) -> None:
        self._questions = list(questions)
        self._index = 0
        self.calls: list[VersusState] = []

    async def __call__(self, state: VersusState) -> LoadedQuestion | None:
        self.calls.append(state)
        if self._index >= len(self._questions):
            return None
        question = self._questions[self._index]
        self._index += 1
        return question


@dataclass
class Harness:
    store: InMemorySessionStore
    clock: FakeClock


@dataclass
class Abierta:
    code: str
    room_id: str
    host_outbox: asyncio.Queue[protocols.Message]
    guest_outbox: asyncio.Queue[protocols.Message]
    questions: Questions


@pytest.fixture
async def h() -> AsyncIterator[Harness]:
    clock = FakeClock()
    store = InMemorySessionStore(
        reveal_seconds=0.0,
        grace_seconds=20,
        now_ms=clock.now_ms,
        sleep=clock.sleep,
        rng=Random(7),
        shuffle_served_options=False,
    )
    yield Harness(store=store, clock=clock)
    await store.close()


def drain(outbox: asyncio.Queue[protocols.Message]) -> list[protocols.Message]:
    mensajes: list[protocols.Message] = []
    while not outbox.empty():
        mensajes.append(outbox.get_nowait())
    return mensajes


def uno(mensajes: list[protocols.Message], tipo: type) -> protocols.Message:
    encontrados = [mensaje for mensaje in mensajes if isinstance(mensaje, tipo)]
    assert len(encontrados) == 1, mensajes
    return encontrados[0]


async def abrir(
    h: Harness,
    *questions: LoadedQuestion,
    rounds: int = 3,
    seconds: int = 20,
) -> Abierta:
    source = Questions(*questions)
    room_id = str(uuid.uuid4())
    await h.store.open_versus(
        code=CODE,
        room_id=room_id,
        config=VersusConfig(rounds=rounds, seconds=seconds),
        host_id=HOST,
        next_item=source,
    )
    host_outbox: asyncio.Queue[protocols.Message] = asyncio.Queue()
    guest_outbox: asyncio.Queue[protocols.Message] = asyncio.Queue()
    await h.store.join(code=CODE, user_id=HOST, nick="ana", outbox=host_outbox)
    await h.store.join(code=CODE, user_id=GUEST, nick="beto", outbox=guest_outbox)
    return Abierta(
        code=CODE,
        room_id=room_id,
        host_outbox=host_outbox,
        guest_outbox=guest_outbox,
        questions=source,
    )


def estado(h: Harness, abierta: Abierta) -> VersusState:
    return h.store.versus_sessions()[abierta.code].state


async def arrancar(h: Harness, abierta: Abierta, *, match_id: str = M1) -> None:
    assert (
        await h.store.start(code=abierta.code, user_id=HOST, match_id=match_id)
        == match_id
    )


async def correr(h: Harness, ms: int = 0) -> None:
    """Mueve el reloj y le da tiempo real a la tarea de vencimientos."""
    h.clock.advance(ms)
    for _ in range(10):
        await asyncio.sleep(0.02)


async def jugar_ronda(
    h: Harness,
    abierta: Abierta,
    *,
    a_choice: int = 0,
    b_choice: int = 1,
) -> None:
    state = estado(h, abierta)
    assert state.round is not None
    ronda = state.round.served.round_index
    await h.store.answer(
        code=abierta.code, user_id=HOST, round_index=ronda, choice=a_choice
    )
    await h.store.answer(
        code=abierta.code, user_id=GUEST, round_index=ronda, choice=b_choice
    )


async def test_two_players_are_seated_and_start_serves_the_first_round(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"))

    assert h.store.player_count(CODE) == 2
    assert h.store.seated(code=CODE, user_id=HOST)
    assert h.store.seated(code=CODE, user_id=GUEST)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await arrancar(h, abierta)

    state = estado(h, abierta)
    assert state.status is VersusStatus.PLAYING
    assert state.match is not None
    assert state.match.round_index == 0
    assert state.round is not None
    assert state.round.served.ends_at_ms == h.clock.now_ms() + 20_000

    host = drain(abierta.host_outbox)
    assert uno(host, protocols.MatchStart).match_id == M1
    assert uno(host, protocols.RoundStart).round == 0

    guest = drain(abierta.guest_outbox)
    assert uno(guest, protocols.MatchStart) is not None
    assert uno(guest, protocols.RoundStart) is not None


async def test_a_complete_match_runs_against_the_store(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"), loaded("q-2", difficulty=2))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await jugar_ronda(h, abierta)
    host = drain(abierta.host_outbox)
    guest = drain(abierta.guest_outbox)
    assert uno(host, protocols.RoundResult).scores.you == 150
    assert uno(guest, protocols.OpponentAnswered).round == 0

    await jugar_ronda(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await jugar_ronda(h, abierta)

    host = drain(abierta.host_outbox)
    guest = drain(abierta.guest_outbox)
    fin_host = uno(host, protocols.MatchEnd)
    fin_guest = uno(guest, protocols.MatchEnd)
    assert fin_host.winner == "you"
    assert fin_guest.winner == "opponent"
    assert fin_host.reason == "completed"
    assert fin_host.scores == protocols.Scores(you=450, opponent=0)
    assert len(fin_host.rounds) == 3

    state = estado(h, abierta)
    assert state.status is VersusStatus.FINISHED
    assert state.match is not None
    assert state.match.status is MatchStatus.FINISHED
    assert state.match.winner is not None
    assert h.store.live() == frozenset()


async def test_missing_the_grace_abandons_the_match(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await h.store.disconnect(
        code=abierta.code, user_id=GUEST, outbox=abierta.guest_outbox
    )
    host = drain(abierta.host_outbox)
    assert uno(host, protocols.ReconnectPending).seconds_left == 20
    state = estado(h, abierta)
    assert state.round is not None
    assert state.round.paused_since_ms == h.clock.now_ms()
    assert state.grace_deadline_ms == h.clock.now_ms() + 20_000

    await correr(h, 20_000)

    host = drain(abierta.host_outbox)
    fin = uno(host, protocols.MatchEnd)
    assert fin.reason == "abandoned"
    assert fin.winner == "you"
    state = estado(h, abierta)
    assert state.status is VersusStatus.FINISHED
    assert state.match is not None
    assert state.match.status is MatchStatus.ABANDONED
    assert h.store.player_count(CODE) == 1


async def test_both_gone_is_a_void_match(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await h.store.disconnect(
        code=abierta.code, user_id=HOST, outbox=abierta.host_outbox
    )
    # El aviso de gracia va a la silla que sigue conectada.
    assert uno(drain(abierta.guest_outbox), protocols.ReconnectPending) is not None
    await h.store.disconnect(
        code=abierta.code, user_id=GUEST, outbox=abierta.guest_outbox
    )

    await correr(h, 20_000)

    state = estado(h, abierta)
    assert state.status is VersusStatus.FINISHED
    assert state.match is not None
    assert state.match.status is MatchStatus.VOID
    assert drain(abierta.host_outbox) == []
    assert drain(abierta.guest_outbox) == []


async def test_a_reconnect_resumes_the_clock_and_paints_the_round(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)
    h.clock.advance(1_000)
    await h.store.answer(code=abierta.code, user_id=HOST, round_index=0, choice=0)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await h.store.disconnect(
        code=abierta.code, user_id=GUEST, outbox=abierta.guest_outbox
    )
    drain(abierta.host_outbox)
    h.clock.advance(4_000)

    nueva: asyncio.Queue[protocols.Message] = asyncio.Queue()
    await h.store.reconnect(code=abierta.code, user_id=GUEST, nick="beto", outbox=nueva)

    host = drain(abierta.host_outbox)
    assert uno(host, protocols.OpponentReturned) is not None
    vuelta = drain(nueva)
    assert uno(vuelta, protocols.RoomState).status == "playing"
    ronda = uno(vuelta, protocols.RoundStart)
    assert ronda.round == 0
    # Los 4 s de pausa corren todo: el reloj no regala ni roba segundos.
    assert ronda.ends_at == h.clock.now_ms() + 19_000
    state = estado(h, abierta)
    assert state.round is not None
    assert state.round.paused_since_ms is None
    assert state.grace_deadline_ms is None
    assert state.round.served.served_at_ms == h.clock.now_ms() - 1_000


async def test_the_clock_resolves_an_unanswered_round_and_serves_the_next(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await correr(h, 20_000)

    for outbox in (abierta.host_outbox, abierta.guest_outbox):
        mensajes = drain(outbox)
        resultado = uno(mensajes, protocols.RoundResult)
        assert resultado.you.choice is None
        assert resultado.you.correct is False
        assert uno(mensajes, protocols.RoundStart).round == 1

    state = estado(h, abierta)
    assert state.match is not None
    assert state.match.round_index == 1
    assert state.round is not None
    assert state.round.served.round_index == 1


async def test_a_rematch_needs_both_and_starts_a_fresh_match(h: Harness) -> None:
    abierta = await abrir(
        h,
        loaded("q-0"),
        loaded("q-1"),
        loaded("q-2", difficulty=2),
        loaded("q-3"),
    )
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)
    for _ in range(3):
        await jugar_ronda(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    assert await h.store.rematch(code=abierta.code, user_id=HOST, match_id=M2) is None
    assert uno(drain(abierta.guest_outbox), protocols.RematchWaiting) is not None
    assert estado(h, abierta).status is VersusStatus.FINISHED

    assert await h.store.rematch(code=abierta.code, user_id=GUEST, match_id=M2) == M2
    host = drain(abierta.host_outbox)
    guest = drain(abierta.guest_outbox)
    assert uno(host, protocols.MatchStart).match_id == M2
    assert uno(guest, protocols.MatchStart).match_id == M2
    assert uno(host, protocols.RoundStart).round == 0

    state = estado(h, abierta)
    assert state.status is VersusStatus.PLAYING
    assert state.match_id == M2
    assert state.match is not None
    assert state.match.rounds == ()
    assert h.store.live() == frozenset({uuid.UUID(M2)})


async def test_without_questions_the_match_warns_and_waits(h: Harness) -> None:
    abierta = await abrir(h)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    assert await h.store.start(code=abierta.code, user_id=HOST, match_id=M1) == M1

    for outbox in (abierta.host_outbox, abierta.guest_outbox):
        error = uno(drain(outbox), protocols.Error)
        assert error.code == "NO_QUESTIONS"
    state = estado(h, abierta)
    assert state.match is not None
    assert state.status is VersusStatus.PLAYING
    assert state.needs_next_round is True


async def test_a_third_player_is_rejected_and_not_seated(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"))
    tercera: asyncio.Queue[protocols.Message] = asyncio.Queue()

    await h.store.join(code=abierta.code, user_id="otro", nick="caro", outbox=tercera)

    assert uno(drain(tercera), protocols.Error).code == "ROOM_FULL"
    assert h.store.seated(code=abierta.code, user_id="otro") is False
    assert h.store.player_count(CODE) == 2


async def test_reconnect_without_a_seat_is_rejected(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"))
    intruso: asyncio.Queue[protocols.Message] = asyncio.Queue()

    await h.store.reconnect(
        code=abierta.code, user_id="otro", nick="caro", outbox=intruso
    )

    assert uno(drain(intruso), protocols.Error).code == "NOT_IN_ROOM"


async def test_an_old_socket_cannot_unseat_the_reconnected_player(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"))
    await h.store.disconnect(
        code=abierta.code, user_id=GUEST, outbox=abierta.guest_outbox
    )
    nueva: asyncio.Queue[protocols.Message] = asyncio.Queue()
    await h.store.reconnect(code=abierta.code, user_id=GUEST, nick="beto", outbox=nueva)

    # El socket viejo cierra tarde: la silla ya es de la conexión nueva.
    await h.store.disconnect(
        code=abierta.code, user_id=GUEST, outbox=abierta.guest_outbox
    )

    assert h.store.player_count(CODE) == 2
    assert estado(h, abierta).grace_deadline_ms is None


async def test_close_drops_a_room_and_its_clock(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"))
    await arrancar(h, abierta)
    drain(abierta.host_outbox)
    drain(abierta.guest_outbox)

    await h.store.close(code=abierta.code)
    await h.store.close(code=abierta.code)

    assert h.store.room_count() == 0
    assert h.store.versus_sessions() == {}
    await correr(h, 60_000)
    assert drain(abierta.host_outbox) == []
