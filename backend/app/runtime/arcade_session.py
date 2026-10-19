"""El estado puro de una corrida arcade y sus transiciones.

Espejo de `runtime/room.py` para un solo jugador: acá no hay sockets, ni base,
ni `time.time()`, ni `asyncio`. Cada transición recibe el instante (`now_ms`), la
pregunta ya cargada (eso es I/O) y, al servir, el `rng` con el que se barajan las
opciones. El reloj, la entrega y la persistencia son del borde.

Dos diferencias con la sala que se ven en los tipos:

- Los efectos son una tupla y no `dict[user_id, mensajes]`: hay un solo
  destinatario, dirigirlos sería ceremonia.
- La transición devuelve también el `RoundRecord`. `SoloEngine` no guarda
  historial a propósito; el estado se queda chico y el borde acumula las rondas
  para persistirlas al cerrar.
"""

from dataclasses import dataclass, field, replace
from random import Random

from app.game import protocols
from app.game.answers import Answer, ServedQuestion
from app.game.arcade_engine import ARCADE_ENGINE, ArcadeRun, RoundRecord
from app.game.constants import CHOICES
from app.game.errors import InvalidTransition
from app.services.question_bank import LoadedQuestion, shuffle_options

Effects = tuple[protocols.Message, ...]


@dataclass(frozen=True)
class RoundInFlight:
    """La ronda servida y aún sin resolver."""

    served: ServedQuestion
    question: LoadedQuestion


@dataclass(frozen=True)
class ArcadeState:
    run_id: str
    run: ArcadeRun = field(default_factory=ArcadeRun)
    round: RoundInFlight | None = None
    # El motor no lleva historial: sin esto, una corrida larga podría repetir
    # preguntas del mismo banco.
    seen: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id vacío")
        if self.run.finished and self.round is not None:
            raise ValueError("una corrida terminada no tiene ronda en vuelo")
        if self.round is not None:
            if self.round.served.round_index != self.run.round_index:
                raise ValueError("la ronda en vuelo no es la del motor")
            if self.round.served.question_id not in self.seen:
                raise ValueError("la ronda en vuelo no está en las vistas")

    @property
    def finished(self) -> bool:
        return self.run.finished

    @property
    def needs_next_question(self) -> bool:
        """El caller tiene que elegir y cargar la próxima pregunta."""
        return not self.finished and self.round is None


@dataclass(frozen=True)
class Transition:
    state: ArcadeState
    effects: Effects = ()
    record: RoundRecord | None = None


def start(run_id: str) -> Transition:
    """Crea la corrida en memoria. La fila `playing` la escribe el borde."""
    state = ArcadeState(run_id=run_id)
    return Transition(
        state,
        (
            protocols.ArcadeStart(
                run_id=run_id,
                lives=state.run.lives,
                seconds=ARCADE_ENGINE.rules.seconds_for(state.run.correct_count),
            ),
        ),
    )


def serve(
    state: ArcadeState,
    *,
    question: LoadedQuestion,
    now_ms: int,
    rng: Random,
    allow_repeat: bool = False,
) -> Transition:
    """Sirve la próxima pregunta. El caller ya la eligió y cargó (eso es I/O).

    `allow_repeat` es la excepción de §9.4: si el pool se quedó sin preguntas
    nuevas, se repite una y se sigue jugando, con la advertencia en el log del
    llamador. Sin ese permiso explícito, repetir es un error de programación.
    """
    if state.finished:
        raise InvalidTransition("la corrida terminó: no hay pregunta siguiente")
    if state.round is not None:
        raise InvalidTransition("ya hay una ronda en curso")
    if question.question.id in state.seen and not allow_repeat:
        raise InvalidTransition("la pregunta ya salió en esta corrida")

    # Se baraja acá, en el último paso puro antes de servir: si dependiera del
    # llamador, olvidarlo le devolvería al cliente la respuesta en la posición
    # original (H-25).
    shuffled = shuffle_options(question, rng)
    served = ARCADE_ENGINE.next_question(
        state.run, question_id=shuffled.question.id, now_ms=now_ms
    )
    session = replace(
        state,
        round=RoundInFlight(served=served, question=shuffled),
        seen=state.seen | {shuffled.question.id},
    )
    return Transition(session, (_question_message(session, served, shuffled),))


def answer(
    state: ArcadeState, *, round_index: int, choice: int, now_ms: int
) -> Transition:
    round_ = state.round
    if round_ is None or state.finished:
        return _error(state, "NOT_PLAYING", "No hay una ronda para contestar")
    if round_index != round_.served.round_index:
        return _error(state, "ROUND_MISMATCH", "Esa ronda ya pasó")
    if choice not in CHOICES:
        return _error(state, "BAD_CHOICE", "Opción fuera de rango")

    answer_ = Answer(round_index=round_index, choice=choice, answered_at_ms=now_ms)
    return _resolve(state, round_, answer_)


def expire(state: ArcadeState, *, now_ms: int) -> Transition:
    """La ventana se agotó: la ronda se resuelve como no contestada."""
    round_ = state.round
    if round_ is None or now_ms < round_.served.ends_at_ms:
        return Transition(state)
    return _resolve(state, round_, None)


def _resolve(
    state: ArcadeState, round_: RoundInFlight, answer_: Answer | None
) -> Transition:
    resolved = ARCADE_ENGINE.resolve(
        state.run,
        round_.served,
        correct_index=round_.question.correct_index,
        answer=answer_,
    )
    session = replace(state, run=resolved.run, round=None)
    effects: list[protocols.Message] = [
        _result_message(resolved.run, resolved.record, round_.question)
    ]
    if resolved.run.finished:
        effects.append(_end_message(session))
    return Transition(session, tuple(effects), resolved.record)


def _question_message(
    state: ArcadeState, served: ServedQuestion, question: LoadedQuestion
) -> protocols.ArcadeQuestion:
    return protocols.ArcadeQuestion(
        round=served.round_index,
        prompt=question.question.prompt,
        options=list(question.question.options),
        category=question.question.category,
        difficulty=served.difficulty,
        seconds=served.seconds,
        ends_at=served.ends_at_ms,
        score=state.run.score,
        lives=state.run.lives,
        streak=state.run.streak,
        correct_count=state.run.correct_count,
    )


def _result_message(
    run: ArcadeRun, record: RoundRecord, question: LoadedQuestion
) -> protocols.ArcadeResult:
    return protocols.ArcadeResult(
        round=record.round_index,
        correct_index=record.correct_index,
        explanation=question.question.explanation,
        you=protocols.RoundChoice(
            choice=record.choice,
            ms=record.elapsed_ms,
            points=record.points,
            correct=record.correct,
        ),
        score=run.score,
        lives=run.lives,
        streak=run.streak,
        correct_count=run.correct_count,
    )


def _end_message(state: ArcadeState) -> protocols.ArcadeEnd:
    # El ranking es I/O: la máquina pura deja las posiciones nulas y el borde las
    # completa después de cerrar la fila.
    return protocols.ArcadeEnd(
        run_id=state.run_id,
        score=state.run.score,
        correct_count=state.run.correct_count,
        max_difficulty=state.run.max_difficulty,
        longest_streak=state.run.longest_streak,
        rank_global=None,
        rank_weekly=None,
        personal_best=None,
        is_new_best=False,
    )


def _error(state: ArcadeState, code: str, message: str) -> Transition:
    return Transition(state, (protocols.Error(code=code, message=message),))
