"""La sesión solo en vivo: entrega, reloj, vencimientos y cierre.

El contenido lo inyecta el test: así una sesión entera corre sin base ni Redis y
lo único que se mira es el store. `FakeClock` mueve la hora a mano y la tarea de
vencimiento resuelve la ronda cuando el test la despierta.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from random import Random
from typing import Any

import pytest

from app.game import protocols
from app.game.arcade_engine import ARCADE_RULES
from app.game.solo_engine import SoloRules, SoloRun
from app.runtime.session_store import (
    FinishHandler,
    InMemorySessionStore,
    NextQuestion,
)
from app.services.question_bank import LoadedQuestion, RoundQuestion

from .clock import FakeClock


def loaded(
    qid: str = "q-0",
    *,
    difficulty: int = 1,
    correct_index: int = 1,
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

    def __init__(self, *questions: LoadedQuestion, repeat: bool = False) -> None:
        self._questions = list(questions)
        self._repeat = repeat
        self._index = 0
        self.calls: list[tuple[SoloRun, frozenset[str]]] = []

    async def __call__(self, run: SoloRun, seen: frozenset[str]) -> NextQuestion | None:
        self.calls.append((run, seen))
        if self._index >= len(self._questions):
            if not self._repeat or not self._questions:
                return None
            question = self._questions[-1]
        else:
            question = self._questions[self._index]
            self._index += 1
        return NextQuestion(question, repeated=question.question.id in seen)


@dataclass
class Harness:
    store: InMemorySessionStore
    clock: FakeClock


@dataclass
class Abierta:
    session_id: str
    owner_id: uuid.UUID
    outbox: asyncio.Queue[protocols.Message]
    questions: Questions


@pytest.fixture
async def h() -> AsyncIterator[Harness]:
    clock = FakeClock()
    store = InMemorySessionStore(
        reveal_seconds=0.0,
        now_ms=clock.now_ms,
        sleep=clock.sleep,
        rng=Random(7),
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
    session_id: str | None = None,
    outbox: asyncio.Queue[protocols.Message] | None = None,
    repeat: bool = False,
    rules: SoloRules = ARCADE_RULES,
    on_finish: FinishHandler | None = None,
) -> Abierta:
    sid = session_id or str(uuid.uuid4())
    owner = uuid.uuid4()
    source = Questions(*questions, repeat=repeat)
    salida = outbox or asyncio.Queue()
    abierta = await h.store.open(
        session_id=sid,
        owner_id=owner,
        outbox=salida,
        rules=rules,
        next_item=source,
        on_finish=on_finish,
    )
    assert abierta is True
    return Abierta(session_id=sid, owner_id=owner, outbox=salida, questions=source)


async def correr(h: Harness, ms: int = 0) -> None:
    """Mueve el reloj y le da tiempo real a la tarea de vencimientos ya servir."""
    h.clock.advance(ms)
    for _ in range(10):
        await asyncio.sleep(0.02)


def correcta(h: Harness, abierta: Abierta) -> int:
    estado = h.store.sessions()[abierta.session_id].state
    assert estado.round is not None
    return estado.round.question.correct_index


async def test_open_registers_the_session_and_serves_the_first_question(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded())

    mensajes = drain(abierta.outbox)
    arranque = uno(mensajes, protocols.ArcadeStart)
    assert arranque == protocols.ArcadeStart(
        run_id=abierta.session_id, lives=3, seconds=20
    )
    pregunta = uno(mensajes, protocols.ArcadeQuestion)
    assert pregunta.round == 0
    assert pregunta.prompt == "¿Cuál es el río más largo?"
    assert pregunta.category == "geography"
    assert pregunta.difficulty == 1
    assert pregunta.seconds == 20
    assert pregunta.ends_at == h.clock.now_ms() + 20_000
    assert (pregunta.score, pregunta.lives, pregunta.streak) == (0, 3, 0)

    assert h.store.live() == {uuid.UUID(abierta.session_id)}
    vista = h.store.sessions()[abierta.session_id]
    assert vista.owner_id == abierta.owner_id
    assert vista.state.seen == frozenset({"q-0"})
    assert vista.records == ()
    assert abierta.questions.calls[0][0].round_index == 0
    assert abierta.questions.calls[0][1] == frozenset()


async def test_a_correct_answer_scores_and_serves_the_next_question(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    choice = correcta(h, abierta)
    drain(abierta.outbox)
    h.clock.advance(1_000)

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=choice)

    mensajes = drain(abierta.outbox)
    resultado = uno(mensajes, protocols.ArcadeResult)
    assert resultado.round == 0
    assert resultado.correct_index == choice
    assert resultado.explanation == "Porque sí."
    assert resultado.you.correct is True
    assert (resultado.score, resultado.lives, resultado.streak) == (148, 3, 1)

    siguiente = uno(mensajes, protocols.ArcadeQuestion)
    assert siguiente.round == 1
    assert siguiente.score == 148

    vista = h.store.sessions()[abierta.session_id]
    assert vista.state.run.score == 148
    assert vista.state.seen == frozenset({"q-0", "q-1"})
    assert len(vista.records) == 1
    assert vista.records[0].correct is True


async def test_a_wrong_answer_loses_a_life_and_resets_the_streak(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    choice = (correcta(h, abierta) + 1) % 4
    drain(abierta.outbox)

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=choice)

    resultado = uno(drain(abierta.outbox), protocols.ArcadeResult)
    assert resultado.you.correct is False
    assert resultado.you.points == 0
    vista = h.store.sessions()[abierta.session_id]
    assert vista.state.run.lives == 2
    assert vista.state.run.streak == 0
    assert vista.state.run.score == 0


async def test_expiry_resolves_the_round_as_missing_and_serves_the_next(
    h: Harness,
) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    drain(abierta.outbox)

    await correr(h, 20_000)

    mensajes = drain(abierta.outbox)
    resultado = uno(mensajes, protocols.ArcadeResult)
    assert resultado.you.choice is None
    assert resultado.you.correct is False
    assert resultado.you.ms == 20_000
    assert resultado.lives == 2
    assert uno(mensajes, protocols.ArcadeQuestion).round == 1


async def test_three_misses_finish_the_session_and_release_it(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"), loaded("q-2"))
    drain(abierta.outbox)

    for ronda in range(3):
        await correr(h, 20_000)
        mensajes = drain(abierta.outbox)
        if ronda < 2:
            assert uno(mensajes, protocols.ArcadeQuestion).round == ronda + 1

    fin = uno(mensajes, protocols.ArcadeEnd)
    assert fin.score == 0
    assert fin.correct_count == 0
    assert fin.longest_streak == 0
    assert h.store.live() == frozenset()

    vista = h.store.sessions()[abierta.session_id]
    assert vista.state.finished is True
    assert len(vista.records) == 3


async def test_the_finish_handler_completes_the_end_before_it_is_delivered(
    h: Harness,
) -> None:
    llamadas: list[tuple[str, int]] = []

    async def cerrar(
        state: Any, records: tuple[Any, ...], end: protocols.ArcadeEnd
    ) -> protocols.ArcadeEnd:
        llamadas.append((state.session_id, len(records)))
        return replace(
            end,
            rank_global=2,
            personal_best=state.run.score,
            is_new_best=True,
        )

    abierta = await abrir(
        h, loaded("q-0"), loaded("q-1"), loaded("q-2"), on_finish=cerrar
    )
    drain(abierta.outbox)

    for _ in range(3):
        await correr(h, 20_000)
        mensajes = drain(abierta.outbox)

    fin = uno(mensajes, protocols.ArcadeEnd)
    assert llamadas == [(abierta.session_id, 3)]
    # El cierre del borde corre antes de entregar: el cliente ve la posición.
    assert (fin.rank_global, fin.personal_best, fin.is_new_best) == (2, 0, True)


async def test_close_is_idempotent_and_drops_the_session(h: Harness) -> None:
    abierta = await abrir(h, loaded())
    drain(abierta.outbox)

    await h.store.close(session_id=abierta.session_id)
    await h.store.close(session_id=abierta.session_id)

    assert h.store.live() == frozenset()
    assert h.store.sessions() == {}

    # La tarea de vencimiento ya no está: el reloj no resucita la sesión.
    await correr(h, 60_000)
    assert drain(abierta.outbox) == []


async def test_submitting_after_close_is_a_noop(h: Harness) -> None:
    abierta = await abrir(h, loaded())
    drain(abierta.outbox)
    await h.store.close(session_id=abierta.session_id)

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=0)

    assert drain(abierta.outbox) == []


async def test_open_twice_does_not_restart_the_session(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"))
    drain(abierta.outbox)

    otra = await h.store.open(
        session_id=abierta.session_id,
        owner_id=abierta.owner_id,
        outbox=abierta.outbox,
        rules=ARCADE_RULES,
        next_item=abierta.questions,
    )

    assert otra is False
    assert drain(abierta.outbox) == []
    assert len(h.store.sessions()) == 1


async def test_an_outbox_full_drops_the_oldest_message(h: Harness) -> None:
    abierta = await abrir(h, loaded(), outbox=asyncio.Queue(maxsize=1))

    mensajes = drain(abierta.outbox)
    assert [mensaje.type for mensaje in mensajes] == ["arcade_question"]
    assert h.store.sessions()[abierta.session_id].state.run.score == 0


async def test_without_questions_the_session_warns_and_waits(h: Harness) -> None:
    abierta = await abrir(h)

    mensajes = drain(abierta.outbox)
    assert uno(mensajes, protocols.ArcadeStart) is not None
    error = uno(mensajes, protocols.Error)
    assert error.code == "NO_QUESTIONS"
    assert h.store.sessions()[abierta.session_id].state.needs_next_question is True
    assert len(h.store.live()) == 1


async def test_a_bad_round_or_choice_is_rejected(h: Harness) -> None:
    abierta = await abrir(h, loaded())
    drain(abierta.outbox)

    await h.store.submit(session_id=abierta.session_id, round_index=4, choice=0)
    assert uno(drain(abierta.outbox), protocols.Error).code == "ROUND_MISMATCH"

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=9)
    assert uno(drain(abierta.outbox), protocols.Error).code == "BAD_CHOICE"


async def test_answering_after_the_end_is_rejected(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"), loaded("q-2"))
    for _ in range(3):
        await correr(h, 20_000)
    drain(abierta.outbox)

    await h.store.submit(session_id=abierta.session_id, round_index=3, choice=0)

    assert uno(drain(abierta.outbox), protocols.Error).code == "NOT_PLAYING"


async def test_a_one_life_session_finishes_on_the_answer(h: Harness) -> None:
    reglas = SoloRules(
        lives=1,
        difficulty_tiers=(0,),
        seconds_start=20,
        seconds_floor=20,
        seconds_step_every=10,
        streak_bonus_step=0,
        streak_bonus_max=0,
    )
    abierta = await abrir(h, loaded("q-0"), loaded("q-1"), rules=reglas)
    choice = (correcta(h, abierta) + 1) % 4
    drain(abierta.outbox)

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=choice)

    mensajes = drain(abierta.outbox)
    assert uno(mensajes, protocols.ArcadeResult).lives == 0
    assert uno(mensajes, protocols.ArcadeEnd) is not None
    assert h.store.live() == frozenset()

    # La tarea de vencimiento arranca con la sesión ya terminada y se retira.
    await correr(h, 60_000)
    assert drain(abierta.outbox) == []


async def test_a_failing_source_does_not_leave_a_zombie_session(h: Harness) -> None:
    async def rota(run: SoloRun, seen: frozenset[str]) -> NextQuestion | None:
        raise RuntimeError("la base no contestó")

    with pytest.raises(RuntimeError, match="no contestó"):
        await h.store.open(
            session_id=str(uuid.uuid4()),
            owner_id=uuid.uuid4(),
            outbox=asyncio.Queue(),
            rules=ARCADE_RULES,
            next_item=rota,
        )

    assert h.store.sessions() == {}
    assert h.store.live() == frozenset()


async def test_a_repeated_item_is_served_only_with_permission(h: Harness) -> None:
    abierta = await abrir(h, loaded("q-0"), repeat=True)
    choice = correcta(h, abierta)
    drain(abierta.outbox)

    await h.store.submit(session_id=abierta.session_id, round_index=0, choice=choice)

    pregunta = uno(drain(abierta.outbox), protocols.ArcadeQuestion)
    assert pregunta.round == 1
    vista = h.store.sessions()[abierta.session_id]
    assert vista.state.round is not None
    assert vista.state.round.served.question_id == "q-0"
