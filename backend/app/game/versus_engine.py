"""Motor puro del versus: partida, sillas, gracia y revancha.

El motor no conoce sockets, base ni relojes reales. Cada transición recibe el
instante (`now_ms`) y devuelve el estado nuevo más los mensajes a mandar, ya
separados **por jugador**: casi todos son asimétricos (`room_state` lleva `you`,
`round_result`/`match_end` cambian según de qué lado se miren). Un "broadcast"
sería la mitad de la historia.

Hay dos niveles a propósito:

- `MatchState` es la partida: el historial de rondas es la única fuente de
  verdad, así que marcador y contadores no pueden desincronizarse.
- `VersusState` es la sala con sillas: lobby, conexión, gracia, pausa del reloj
  y revancha. La partida vive adentro y solo existe mientras se juega.

`VersusEngine` es la fachada de las reglas de la partida; `InMemorySessionStore`
es quien aplica el reloj, los locks y la entrega.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from app.game import protocols
from app.game.answers import Answer, RejectReason, ServedQuestion, settle
from app.game.constants import CHOICES, ONLINE_ROUNDS_OPTIONS, ONLINE_SECONDS_OPTIONS
from app.game.errors import InvalidTransition
from app.game.scoring import round_points
from app.services.question_bank import LoadedQuestion

# (última ronda del tramo, dificultad mínima, dificultad máxima)
_DIFFICULTY_BY_ROUND = ((1, 1, 2), (3, 2, 3), (5, 3, 4))
_TIEBREAK_DIFFICULTY = (4, 5)
# Sin tope, dos jugadores igualados podían jugar rondas de desempate para siempre
# (H-24). Agotadas estas, la partida termina en empate: es el resultado honesto.
MAX_TIEBREAK_ROUNDS = 3


class Player(StrEnum):
    A = "a"
    B = "b"


class MatchStatus(StrEnum):
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"
    VOID = "void"


@dataclass(frozen=True)
class VersusConfig:
    rounds: int
    seconds: int

    def __post_init__(self) -> None:
        if self.rounds not in ONLINE_ROUNDS_OPTIONS:
            raise ValueError(f"rounds no permitido: {self.rounds}")
        if self.seconds not in ONLINE_SECONDS_OPTIONS:
            raise ValueError(f"seconds no permitido: {self.seconds}")


@dataclass(frozen=True)
class RoundRecord:
    round_index: int
    question_id: str
    difficulty: int
    seconds: int
    correct_index: int
    a_choice: int | None
    b_choice: int | None
    a_ms: int | None
    b_ms: int | None
    a_correct: bool
    b_correct: bool
    a_points: int
    b_points: int
    a_rejected: RejectReason | None
    b_rejected: RejectReason | None


@dataclass(frozen=True)
class MatchState:
    """El historial de rondas es la única fuente de verdad: marcador y contadores
    se derivan de él, así que no pueden desincronizarse."""

    config: VersusConfig
    rounds: tuple[RoundRecord, ...] = ()
    status: MatchStatus = MatchStatus.PLAYING
    winner: Player | None = None

    def __post_init__(self) -> None:
        if tuple(record.round_index for record in self.rounds) != tuple(
            range(len(self.rounds))
        ):
            raise ValueError("las rondas deben ser consecutivas desde 0")

        if self.status is MatchStatus.PLAYING:
            if self.winner is not None:
                raise ValueError("una partida en curso no tiene ganador")
            if self.in_tiebreak and self.score_a != self.score_b:
                raise ValueError(
                    "con las rondas agotadas y marcador distinto, debe estar terminada"
                )
        elif self.status is MatchStatus.VOID:
            if self.winner is not None:
                raise ValueError("una partida anulada no tiene ganador")
        elif self.status is MatchStatus.ABANDONED:
            if self.winner is None:
                raise ValueError("una partida abandonada necesita ganador")
        elif self.winner is None:
            # Un FINISHED sin ganador sólo puede ser el empate tras agotar el
            # tope de desempates (H-24). Antes de eso se sigue jugando.
            empate_en_el_tope = (
                self.score_a == self.score_b
                and self.round_index >= self.config.rounds + MAX_TIEBREAK_ROUNDS
            )
            if not empate_en_el_tope:
                raise ValueError("una partida terminada sin ganador no es un empate")

    @property
    def score_a(self) -> int:
        return sum(record.a_points for record in self.rounds)

    @property
    def score_b(self) -> int:
        return sum(record.b_points for record in self.rounds)

    @property
    def round_index(self) -> int:
        return len(self.rounds)

    @property
    def in_tiebreak(self) -> bool:
        return self.round_index >= self.config.rounds

    @property
    def seconds_per_round(self) -> int:
        return self.config.seconds // 2 if self.in_tiebreak else self.config.seconds


@dataclass(frozen=True)
class Resolved:
    record: RoundRecord
    state: MatchState


def difficulty_range(state: MatchState) -> tuple[int, int]:
    if state.in_tiebreak:
        return _TIEBREAK_DIFFICULTY

    for last_round, low, high in _DIFFICULTY_BY_ROUND:
        if state.round_index <= last_round:
            return low, high
    return _TIEBREAK_DIFFICULTY


def next_round(
    state: MatchState, *, question_id: str, difficulty: int, now_ms: int
) -> ServedQuestion:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("la partida no está en curso: no hay ronda siguiente")

    low, high = difficulty_range(state)
    if not low <= difficulty <= high:
        raise ValueError(f"dificultad {difficulty} fuera del tramo {low}-{high}")

    return ServedQuestion(
        round_index=state.round_index,
        question_id=question_id,
        difficulty=difficulty,
        seconds=state.seconds_per_round,
        served_at_ms=now_ms,
    )


def resolve_round(
    state: MatchState,
    served: ServedQuestion,
    *,
    correct_index: int,
    a: Answer | None,
    b: Answer | None,
) -> Resolved:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition(
            "la partida no está en curso: no hay ronda que resolver"
        )
    if served.round_index != state.round_index:
        raise InvalidTransition(
            f"se resolvió la ronda {served.round_index} estando en la "
            f"{state.round_index}"
        )
    if correct_index not in CHOICES:
        raise ValueError(f"correct_index fuera de rango: {correct_index}")

    a_settled = settle(served, a, correct_index=correct_index)
    b_settled = settle(served, b, correct_index=correct_index)

    a_points = round_points(
        correct=a_settled.correct,
        elapsed_ms=a_settled.elapsed_ms,
        total_seconds=served.seconds,
    )
    b_points = round_points(
        correct=b_settled.correct,
        elapsed_ms=b_settled.elapsed_ms,
        total_seconds=served.seconds,
    )

    record = RoundRecord(
        round_index=served.round_index,
        question_id=served.question_id,
        difficulty=served.difficulty,
        seconds=served.seconds,
        correct_index=correct_index,
        a_choice=a_settled.answer.choice if a_settled.answer is not None else None,
        b_choice=b_settled.answer.choice if b_settled.answer is not None else None,
        a_ms=a_settled.elapsed_ms if a_settled.answer is not None else None,
        b_ms=b_settled.elapsed_ms if b_settled.answer is not None else None,
        a_correct=a_settled.correct,
        b_correct=b_settled.correct,
        a_points=a_points,
        b_points=b_points,
        a_rejected=a_settled.rejected,
        b_rejected=b_settled.rejected,
    )

    rounds = (*state.rounds, record)
    score_a = state.score_a + a_points
    score_b = state.score_b + b_points

    # Termina cuando hay ganador o cuando se agotó el tope de desempates: en ese
    # caso queda empatada, en vez de seguir sirviendo rondas para siempre (H-24).
    decided = len(rounds) >= state.config.rounds and (
        score_a != score_b or len(rounds) >= state.config.rounds + MAX_TIEBREAK_ROUNDS
    )
    winner = None
    if decided and score_a != score_b:
        winner = Player.A if score_a > score_b else Player.B

    next_state = replace(
        state,
        rounds=rounds,
        status=MatchStatus.FINISHED if decided else MatchStatus.PLAYING,
        winner=winner,
    )
    return Resolved(record=record, state=next_state)


def abandon(state: MatchState, *, gone: Player) -> MatchState:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("solo se puede abandonar una partida en curso")

    winner = Player.B if gone is Player.A else Player.A
    return replace(state, status=MatchStatus.ABANDONED, winner=winner)


def void(state: MatchState) -> MatchState:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("solo se puede anular una partida en curso")

    return replace(state, status=MatchStatus.VOID, winner=None)


@dataclass(frozen=True)
class VersusEngine:
    """Las reglas de una partida versus, sin salas ni mensajes.

    La fachada existe para que el store y el futuro registro de modos hablen de
    un motor, no de un paquete de funciones sueltas.
    """

    config: VersusConfig

    def start(self) -> MatchState:
        return MatchState(config=self.config)

    def difficulty_range(self, match: MatchState) -> tuple[int, int]:
        return difficulty_range(match)

    def next_round(
        self, match: MatchState, *, question_id: str, difficulty: int, now_ms: int
    ) -> ServedQuestion:
        return next_round(
            match, question_id=question_id, difficulty=difficulty, now_ms=now_ms
        )

    def resolve(
        self,
        match: MatchState,
        served: ServedQuestion,
        *,
        correct_index: int,
        a: Answer | None,
        b: Answer | None,
    ) -> Resolved:
        return resolve_round(match, served, correct_index=correct_index, a=a, b=b)

    def abandon(self, match: MatchState, *, gone: Player) -> MatchState:
        return abandon(match, gone=gone)

    def void(self, match: MatchState) -> MatchState:
        return void(match)


class VersusStatus(StrEnum):
    """Los mismos estados que `rooms.status` en la base.

    `expired` lo escribe el barrendero sobre la fila de Postgres; la sala viva no
    se "vence a sí misma": si nadie juega, se la lleva el timeout de inactividad.
    """

    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Seat:
    """Un jugador sentado, con o sin conexión.

    La silla sobrevive a la desconexión (para poder reconectar). El host siempre
    se sienta en `A`.
    """

    user_id: str
    nick: str
    connected: bool = True


@dataclass(frozen=True)
class RoundInFlight:
    """La ronda servida y aún sin resolver.

    `paused_since_ms` es el instante en que se pausó el reloj por una desconexión,
    y es `None` mientras corre. Guardar el momento de la pausa es lo que permite
    correr la ventana al reanudar, en vez de regalar o robar segundos.
    """

    served: ServedQuestion
    question: LoadedQuestion
    answers: tuple[Answer | None, Answer | None] = (None, None)
    paused_since_ms: int | None = None


@dataclass(frozen=True)
class VersusState:
    code: str
    config: VersusConfig
    host_id: str
    seats: tuple[Seat | None, Seat | None] = (None, None)
    status: VersusStatus = VersusStatus.WAITING
    match_id: str | None = None
    match: MatchState | None = None
    round: RoundInFlight | None = None
    grace_deadline_ms: int | None = None
    rematch_requests: frozenset[Player] = frozenset()

    def __post_init__(self) -> None:
        if (self.match_id is None) != (self.match is None):
            raise ValueError("match_id y match van juntos")
        if self.status is VersusStatus.PLAYING and self.match is None:
            raise ValueError("una sala jugando necesita partida")
        if self.round is not None and self.status is not VersusStatus.PLAYING:
            raise ValueError("solo hay ronda en curso dentro de una partida")

    def player_of(self, user_id: str) -> Player | None:
        for idx, seat in enumerate(self.seats):
            if seat is not None and seat.user_id == user_id:
                return Player.A if idx == 0 else Player.B
        return None

    @property
    def ready_for_rematch(self) -> bool:
        return len(self.rematch_requests) == 2

    @property
    def needs_next_round(self) -> bool:
        """El caller debe elegir y servir la próxima pregunta."""
        return (
            self.status is VersusStatus.PLAYING
            and self.round is None
            and self.grace_deadline_ms is None
            and _both_connected(self)
        )


# Mensajes indexados por a quién van. Un `dict` y no una lista con destinatario:
# el receptor único y los dos se resuelven igual, y el no sentado (un error) también.
Effects = dict[str, tuple[protocols.Message, ...]]
Transition = tuple[VersusState, Effects]


def join(state: VersusState, *, user_id: str, nick: str, now_ms: int) -> Transition:
    """Sienta a un jugador, o lo reconecta si ya tenía silla."""
    slot = _slot_for(state, user_id)
    idx = _index(slot)
    current = state.seats[idx]
    if current is not None and current.user_id != user_id:
        return state, {user_id: (_error("ROOM_FULL", "La sala ya está completa"),)}

    room = replace(state, seats=_with_seat(state.seats, idx, Seat(user_id, nick)))

    # Volvió el que faltaba y ya están los dos: se reanuda el reloj de la ronda.
    if (
        room.status is VersusStatus.PLAYING
        and room.grace_deadline_ms is not None
        and _both_connected(room)
    ):
        room = _resume(room, now_ms)
        effects: Effects = {user_id: _state_effects(room, slot, now_ms)}
        other_seat = room.seats[_index(_other(slot))]
        if other_seat is not None:
            effects[other_seat.user_id] = (protocols.OpponentReturned(),)
        return room, effects

    return room, _states(room)


def sync(state: VersusState, *, user_id: str, now_ms: int) -> Transition:
    """Reenvía el estado completo al que manda `hello` (entrada o resincronización)."""
    slot = state.player_of(user_id)
    if slot is None:
        return state, {user_id: (_error("NOT_IN_ROOM", "No estás en esta sala"),)}
    return state, {user_id: _state_effects(state, slot, now_ms)}


def start(state: VersusState, *, user_id: str, match_id: str) -> Transition:
    if state.player_of(user_id) is not Player.A:
        return state, {
            user_id: (_error("NOT_HOST", "Solo el host arranca la partida"),)
        }
    if state.status is not VersusStatus.WAITING:
        # Con la sala en `playing` ya arrancó; en `finished`, el único camino a otra
        # partida es la revancha (los dos de acuerdo). Dejar `start` acá abría un
        # atajo que salteaba ese acuerdo.
        return state, {user_id: (_error("ALREADY_PLAYING", "La partida ya arrancó"),)}
    if not _full(state) or not _both_connected(state):
        return state, {user_id: (_error("NOT_READY", "Hacen falta dos jugadores"),)}

    room, message = _new_match(state, match_id)
    return room, _broadcast(room, message)


def _new_match(
    state: VersusState, match_id: str
) -> tuple[VersusState, protocols.MatchStart]:
    """La partida nueva: el bloque que comparten el arranque y la revancha."""
    room = replace(
        state,
        status=VersusStatus.PLAYING,
        match=VersusEngine(state.config).start(),
        match_id=match_id,
        round=None,
        grace_deadline_ms=None,
        rematch_requests=frozenset(),
    )
    message = protocols.MatchStart(
        match_id=match_id,
        config={"rounds": state.config.rounds, "seconds": state.config.seconds},
        rounds_total=state.config.rounds,
    )
    return room, message


def serve(state: VersusState, *, question: LoadedQuestion, now_ms: int) -> Transition:
    """Sirve la próxima pregunta. El caller ya la eligió y cargó (eso es I/O)."""
    if state.status is not VersusStatus.PLAYING:
        raise InvalidTransition("no se sirve una pregunta fuera de una partida")
    if state.round is not None:
        raise InvalidTransition("ya hay una ronda en curso")
    if state.grace_deadline_ms is not None or not _both_connected(state):
        raise InvalidTransition("no se sirve con un jugador ausente")

    assert state.match is not None  # el __post_init__ lo garantiza con status PLAYING
    served = VersusEngine(state.config).next_round(
        state.match,
        question_id=question.question.id,
        difficulty=question.question.difficulty,
        now_ms=now_ms,
    )
    room = replace(state, round=RoundInFlight(served=served, question=question))
    return room, _broadcast(room, _round_start(served, question))


def answer(
    state: VersusState, *, user_id: str, round_index: int, choice: int, now_ms: int
) -> Transition:
    slot = state.player_of(user_id)
    if slot is None or state.status is not VersusStatus.PLAYING or state.round is None:
        return state, {
            user_id: (_error("NOT_PLAYING", "No hay una ronda para contestar"),)
        }

    round_ = state.round
    if round_index != round_.served.round_index:
        return state, {user_id: (_error("ROUND_MISMATCH", "Esa ronda ya pasó"),)}

    idx = _index(slot)
    if round_.answers[idx] is not None:
        # Repetir la respuesta es idempotente: el cliente puede reenviarla.
        return state, {}
    if choice not in CHOICES:
        return state, {user_id: (_error("BAD_CHOICE", "Opción fuera de rango"),)}

    # La ventana la juzga `settle`: una sola definición de qué cuenta.
    answers = _with_answer(
        round_.answers,
        idx,
        Answer(round_index=round_index, choice=choice, answered_at_ms=now_ms),
    )
    round_ = replace(round_, answers=answers)
    room = replace(state, round=round_)

    if all(answer_ is not None for answer_ in answers):
        return _resolve(room, round_)

    other_seat = room.seats[_index(_other(slot))]
    if other_seat is None:
        return room, {}
    return room, {other_seat.user_id: (protocols.OpponentAnswered(round=round_index),)}


def disconnect(
    state: VersusState, *, user_id: str, now_ms: int, grace_seconds: int
) -> Transition:
    slot = state.player_of(user_id)
    if slot is None:
        return state, {}

    idx = _index(slot)
    seat = state.seats[idx]
    assert seat is not None
    room = replace(
        state, seats=_with_seat(state.seats, idx, replace(seat, connected=False))
    )

    if room.status is VersusStatus.WAITING:
        return room, _states(room)

    if room.status is VersusStatus.FINISHED:
        # La revancha no prosperó: la sala vuelve a estar disponible.
        room = replace(
            room,
            status=VersusStatus.WAITING,
            match=None,
            match_id=None,
            round=None,
            rematch_requests=frozenset(),
            grace_deadline_ms=None,
        )
        return room, _states(room)

    if room.round is not None and room.round.paused_since_ms is None:
        room = replace(room, round=replace(room.round, paused_since_ms=now_ms))
    # El primer ausente fija la ventana; si después se va el otro, manda la primera.
    if room.grace_deadline_ms is None:
        room = replace(room, grace_deadline_ms=now_ms + grace_seconds * 1000)

    other_seat = room.seats[_index(_other(slot))]
    if other_seat is None:
        return room, {}
    return room, {
        other_seat.user_id: (
            protocols.ReconnectPending(seconds_left=_seconds_left(room, now_ms)),
        )
    }


def expire(state: VersusState, *, now_ms: int) -> Transition:
    """Lo que dispara el reloj solo: fin de ronda o fin de la ventana de gracia."""
    if state.status is not VersusStatus.PLAYING:
        return state, {}

    if state.grace_deadline_ms is not None:
        if now_ms < state.grace_deadline_ms:
            return state, {}
        gone = [
            Player.A if idx == 0 else Player.B
            for idx, seat in enumerate(state.seats)
            if seat is None or not seat.connected
        ]
        if len(gone) == 2:
            return _void(state)
        return _abandon(state, gone=gone[0])

    if state.round is not None and now_ms >= state.round.served.ends_at_ms:
        return _resolve(state, state.round)
    return state, {}


def rematch(state: VersusState, *, user_id: str, match_id: str) -> Transition:
    slot = state.player_of(user_id)
    if slot is None or state.status is not VersusStatus.FINISHED:
        return state, {
            user_id: (_error("REMATCH_UNAVAILABLE", "No hay partida que revanchar"),)
        }

    room = replace(state, rematch_requests=state.rematch_requests | {slot})
    if room.ready_for_rematch:
        # El segundo pedido arranca la partida nueva: el que esperaba ya no
        # espera, así que los dos reciben el `match_start` y no un aviso.
        room, message = _new_match(room, match_id)
        return room, _broadcast(room, message)

    other_seat = room.seats[_index(_other(slot))]
    if other_seat is None:
        return room, {}
    return room, {other_seat.user_id: (protocols.RematchWaiting(),)}


def _resolve(state: VersusState, round_: RoundInFlight) -> Transition:
    assert state.match is not None
    resolved = VersusEngine(state.config).resolve(
        state.match,
        round_.served,
        correct_index=round_.question.correct_index,
        a=round_.answers[0],
        b=round_.answers[1],
    )
    room = replace(state, match=resolved.state, round=None)

    explanation = round_.question.question.explanation
    effects: Effects = {}
    for player in (Player.A, Player.B):
        seat = room.seats[_index(player)]
        if seat is not None:
            effects[seat.user_id] = (
                _round_result(resolved.state, resolved.record, player, explanation),
            )

    if resolved.state.status is not MatchStatus.PLAYING:
        room = replace(room, status=VersusStatus.FINISHED)
        effects = _merge(effects, _match_end(room, reason="completed"))
    return room, effects


def _abandon(state: VersusState, *, gone: Player) -> Transition:
    assert state.match is not None
    room = replace(
        state,
        status=VersusStatus.FINISHED,
        match=VersusEngine(state.config).abandon(state.match, gone=gone),
        round=None,
        grace_deadline_ms=None,
    )
    return room, _match_end(room, reason="abandoned")


def _void(state: VersusState) -> Transition:
    assert state.match is not None
    room = replace(
        state,
        status=VersusStatus.FINISHED,
        match=VersusEngine(state.config).void(state.match),
        round=None,
        grace_deadline_ms=None,
    )
    return room, _match_end(room, reason="abandoned")


def _resume(state: VersusState, now_ms: int) -> VersusState:
    """Corre la ventana de la ronda por el tiempo que estuvo en pausa.

    Se mueve todo (el arranque y las respuestas ya recibidas) por el mismo hueco:
    el tiempo medido de quien ya contestó no cambia y el reloj no "gasta" pausa.
    """
    round_ = state.round
    if round_ is None or round_.paused_since_ms is None:
        return replace(state, grace_deadline_ms=None)

    gap = now_ms - round_.paused_since_ms
    served = replace(round_.served, served_at_ms=round_.served.served_at_ms + gap)
    answers = (
        _shift(round_.answers[0], gap),
        _shift(round_.answers[1], gap),
    )
    return replace(
        state,
        grace_deadline_ms=None,
        round=replace(round_, served=served, answers=answers, paused_since_ms=None),
    )


def _shift(answer_: Answer | None, gap: int) -> Answer | None:
    if answer_ is None:
        return None
    return replace(answer_, answered_at_ms=answer_.answered_at_ms + gap)


def _round_start(
    served: ServedQuestion, question: LoadedQuestion
) -> protocols.RoundStart:
    # Sin `correct_index`: el dataclass del mensaje no tiene dónde guardarlo.
    return protocols.RoundStart(
        round=served.round_index,
        question_id=question.question.id,
        prompt=question.question.prompt,
        options=list(question.question.options),
        category=question.question.category,
        difficulty=question.question.difficulty,
        ends_at=served.ends_at_ms,
        total_seconds=served.seconds,
    )


def _round_result(
    match: MatchState, record: RoundRecord, player: Player, explanation: str | None
) -> protocols.RoundResult:
    if player is Player.A:
        you = protocols.RoundChoice(
            choice=record.a_choice,
            ms=record.a_ms,
            points=record.a_points,
            correct=record.a_correct,
        )
        opponent = protocols.RoundChoice(
            choice=record.b_choice,
            ms=record.b_ms,
            points=record.b_points,
            correct=record.b_correct,
        )
        scores = protocols.Scores(you=match.score_a, opponent=match.score_b)
    else:
        you = protocols.RoundChoice(
            choice=record.b_choice,
            ms=record.b_ms,
            points=record.b_points,
            correct=record.b_correct,
        )
        opponent = protocols.RoundChoice(
            choice=record.a_choice,
            ms=record.a_ms,
            points=record.a_points,
            correct=record.a_correct,
        )
        scores = protocols.Scores(you=match.score_b, opponent=match.score_a)
    return protocols.RoundResult(
        round=record.round_index,
        correct_index=record.correct_index,
        explanation=explanation,
        you=you,
        opponent=opponent,
        scores=scores,
    )


def _match_end(room: VersusState, *, reason: str) -> Effects:
    assert room.match is not None
    match = room.match
    effects: Effects = {}
    for player in (Player.A, Player.B):
        seat = room.seats[_index(player)]
        if seat is None:
            continue
        if match.winner is None:
            winner = "tie"
        else:
            winner = "you" if match.winner is player else "opponent"
        if player is Player.A:
            scores = protocols.Scores(you=match.score_a, opponent=match.score_b)
        else:
            scores = protocols.Scores(you=match.score_b, opponent=match.score_a)
        # Las rondas viejas no guardan enunciado: el resumen va sin explicación.
        rounds = [_round_result(match, record, player, None) for record in match.rounds]
        effects[seat.user_id] = (
            protocols.MatchEnd(
                winner=winner, scores=scores, rounds=rounds, reason=reason
            ),
        )
    return effects


def _room_state(state: VersusState, player: Player) -> protocols.RoomState:
    seat = state.seats[_index(player)]
    assert seat is not None
    return protocols.RoomState(
        code=state.code,
        status=state.status.value,
        config={"rounds": state.config.rounds, "seconds": state.config.seconds},
        you=protocols.PlayerView(id=seat.user_id, nick=seat.nick),
        players=[
            protocols.PlayerView(id=other.user_id, nick=other.nick)
            for other in state.seats
            if other is not None
        ],
        match_id=state.match_id,
    )


def _state_effects(
    state: VersusState, slot: Player, now_ms: int
) -> tuple[protocols.Message, ...]:
    messages: list[protocols.Message] = [_room_state(state, slot)]
    if state.round is not None:
        # Al reconectar hay que repintar la ronda en curso con su `ends_at` ya corrido.
        messages.append(_round_start(state.round.served, state.round.question))
    if state.grace_deadline_ms is not None:
        messages.append(
            protocols.ReconnectPending(seconds_left=_seconds_left(state, now_ms))
        )
    return tuple(messages)


def _states(state: VersusState) -> Effects:
    """El estado completo, armado para cada silla: `you` cambia según quién mira."""
    effects: Effects = {}
    for idx, seat in enumerate(state.seats):
        if seat is None:
            continue
        player = Player.A if idx == 0 else Player.B
        effects[seat.user_id] = (_room_state(state, player),)
    return effects


def _broadcast(state: VersusState, message: protocols.Message) -> Effects:
    return {seat.user_id: (message,) for seat in state.seats if seat is not None}


def _error(code: str, message: str) -> protocols.Error:
    return protocols.Error(code=code, message=message)


def _merge(*maps: Effects) -> Effects:
    merged: Effects = {}
    for mapa in maps:
        for user_id, messages in mapa.items():
            merged[user_id] = merged.get(user_id, ()) + messages
    return merged


def _both_connected(state: VersusState) -> bool:
    return all(seat is not None and seat.connected for seat in state.seats)


def _full(state: VersusState) -> bool:
    return all(seat is not None for seat in state.seats)


def _seconds_left(state: VersusState, now_ms: int) -> int:
    assert state.grace_deadline_ms is not None
    return max(0, state.grace_deadline_ms - now_ms + 999) // 1000


def _slot_for(state: VersusState, user_id: str) -> Player:
    return Player.A if user_id == state.host_id else Player.B


def _index(player: Player) -> int:
    return 0 if player is Player.A else 1


def _other(player: Player) -> Player:
    return Player.B if player is Player.A else Player.A


def _with_seat(
    seats: tuple[Seat | None, Seat | None], idx: int, seat: Seat
) -> tuple[Seat | None, Seat | None]:
    first, second = seats
    return (seat, second) if idx == 0 else (first, seat)


def _with_answer(
    answers: tuple[Answer | None, Answer | None], idx: int, answer_: Answer
) -> tuple[Answer | None, Answer | None]:
    first, second = answers
    return (answer_, second) if idx == 0 else (first, answer_)
