"""El estado puro de una sala y sus transiciones.

Una sala es una máquina de estados: lobby, partida, desempate, ventana de
reconexión y revancha. Acá vive **solo la lógica**: no hay sockets, ni base, ni
`time.time()`, ni `asyncio`. Cada transición recibe el instante (`now_ms`) y lo ya
cargado (la pregunta, el id del match) y devuelve el estado nuevo más los mensajes
a mandar. El reloj, el lock y la entrega son del `RoomStore` (`room_manager.py`),
igual que `services/questions.py` decide y `question_bank.py` toca la base.

Dos decisiones se ven en los tipos:

- El estado es inmutable y cada transición devuelve un estado nuevo. No hay
  mutación compartida que pueda quedar a medias.
- Los mensajes salen **por jugador** (`dict[user_id, mensajes]`), porque casi
  todos son asimétricos: `room_state` lleva `you`, y `round_result`/`match_end`
  cambian según de qué lado se miren. Un "broadcast" sería la mitad de la historia.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from app.game import protocols
from app.game.answers import Answer, ServedQuestion
from app.game.constants import CHOICES
from app.game.errors import InvalidTransition
from app.game.match_engine import (
    MatchConfig,
    MatchState,
    MatchStatus,
    Player,
    RoundRecord,
    abandon,
    next_round,
    resolve_round,
    void,
)
from app.services.question_bank import LoadedQuestion


class RoomStatus(StrEnum):
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
class RoomState:
    code: str
    config: MatchConfig
    host_id: str
    seats: tuple[Seat | None, Seat | None] = (None, None)
    status: RoomStatus = RoomStatus.WAITING
    match_id: str | None = None
    match: MatchState | None = None
    round: RoundInFlight | None = None
    grace_deadline_ms: int | None = None
    rematch_requests: frozenset[Player] = frozenset()

    def __post_init__(self) -> None:
        if (self.match_id is None) != (self.match is None):
            raise ValueError("match_id y match van juntos")
        if self.status is RoomStatus.PLAYING and self.match is None:
            raise ValueError("una sala jugando necesita partida")
        if self.round is not None and self.status is not RoomStatus.PLAYING:
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
            self.status is RoomStatus.PLAYING
            and self.round is None
            and self.grace_deadline_ms is None
            and _both_connected(self)
        )


# Mensajes indexados por a quién van. Un `dict` y no una lista con destinatario:
# el receptor único y los dos se resuelven igual, y el no sentado (un error) también.
Effects = dict[str, tuple[protocols.Message, ...]]
Transition = tuple[RoomState, Effects]


def join(state: RoomState, *, user_id: str, nick: str, now_ms: int) -> Transition:
    """Sienta a un jugador, o lo reconecta si ya tenía silla."""
    slot = _slot_for(state, user_id)
    idx = _index(slot)
    current = state.seats[idx]
    if current is not None and current.user_id != user_id:
        return state, {user_id: (_error("ROOM_FULL", "La sala ya está completa"),)}

    room = replace(state, seats=_with_seat(state.seats, idx, Seat(user_id, nick)))

    # Volvió el que faltaba y ya están los dos: se reanuda el reloj de la ronda.
    if (
        room.status is RoomStatus.PLAYING
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


def sync(state: RoomState, *, user_id: str, now_ms: int) -> Transition:
    """Reenvía el estado completo al que manda `hello` (entrada o resincronización)."""
    slot = state.player_of(user_id)
    if slot is None:
        return state, {user_id: (_error("NOT_IN_ROOM", "No estás en esta sala"),)}
    return state, {user_id: _state_effects(state, slot, now_ms)}


def start(state: RoomState, *, user_id: str, match_id: str) -> Transition:
    if state.player_of(user_id) is not Player.A:
        return state, {
            user_id: (_error("NOT_HOST", "Solo el host arranca la partida"),)
        }
    if state.status is not RoomStatus.WAITING:
        # Con la sala en `playing` ya arrancó; en `finished`, el único camino a otra
        # partida es la revancha (los dos de acuerdo). Dejar `start` acá abría un
        # atajo que salteaba ese acuerdo.
        return state, {user_id: (_error("ALREADY_PLAYING", "La partida ya arrancó"),)}
    if not _full(state) or not _both_connected(state):
        return state, {user_id: (_error("NOT_READY", "Hacen falta dos jugadores"),)}

    room, message = _new_match(state, match_id)
    return room, _broadcast(room, message)


def _new_match(
    state: RoomState, match_id: str
) -> tuple[RoomState, protocols.MatchStart]:
    """La partida nueva: el bloque que comparten el arranque y la revancha."""
    room = replace(
        state,
        status=RoomStatus.PLAYING,
        match=MatchState(config=state.config),
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


def serve(state: RoomState, *, question: LoadedQuestion, now_ms: int) -> Transition:
    """Sirve la próxima pregunta. El caller ya la eligió y cargó (eso es I/O)."""
    if state.status is not RoomStatus.PLAYING:
        raise InvalidTransition("no se sirve una pregunta fuera de una partida")
    if state.round is not None:
        raise InvalidTransition("ya hay una ronda en curso")
    if state.grace_deadline_ms is not None or not _both_connected(state):
        raise InvalidTransition("no se sirve con un jugador ausente")

    assert state.match is not None  # el __post_init__ lo garantiza con status PLAYING
    served = next_round(
        state.match,
        question_id=question.question.id,
        difficulty=question.question.difficulty,
        now_ms=now_ms,
    )
    room = replace(state, round=RoundInFlight(served=served, question=question))
    return room, _broadcast(room, _round_start(served, question))


def answer(
    state: RoomState, *, user_id: str, round_index: int, choice: int, now_ms: int
) -> Transition:
    slot = state.player_of(user_id)
    if slot is None or state.status is not RoomStatus.PLAYING or state.round is None:
        return state, {
            user_id: (_error("NOT_PLAYING", "No hay una ronda para contestar"),)
        }

    round_ = state.round
    if round_index != round_.served.round_index:
        return state, {user_id: (_error("ROUND_MISMATCH", "Esa ronda ya pasó"),)}

    idx = _index(slot)
    if round_.answers[idx] is not None:
        # Repetir la respuesta no cambia nada: el cliente puede reenviarla al reconectar.
        return state, {}
    if choice not in CHOICES:
        return state, {user_id: (_error("BAD_CHOICE", "Opción fuera de rango"),)}

    # La ventana la juzga `settle` (en el motor), no acá: una sola definición de qué cuenta.
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
    state: RoomState, *, user_id: str, now_ms: int, grace_seconds: int
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

    if room.status is RoomStatus.WAITING:
        return room, _states(room)

    if room.status is RoomStatus.FINISHED:
        # La revancha no prosperó: la sala queda disponible otra vez, con el mismo código.
        room = replace(
            room,
            status=RoomStatus.WAITING,
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


def expire(state: RoomState, *, now_ms: int) -> Transition:
    """Lo que dispara el reloj solo: fin de ronda o fin de la ventana de gracia."""
    if state.status is not RoomStatus.PLAYING:
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


def rematch(state: RoomState, *, user_id: str, match_id: str) -> Transition:
    slot = state.player_of(user_id)
    if slot is None or state.status is not RoomStatus.FINISHED:
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


def _resolve(state: RoomState, round_: RoundInFlight) -> Transition:
    assert state.match is not None
    resolved = resolve_round(
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
        room = replace(room, status=RoomStatus.FINISHED)
        effects = _merge(effects, _match_end(room, reason="completed"))
    return room, effects


def _abandon(state: RoomState, *, gone: Player) -> Transition:
    assert state.match is not None
    room = replace(
        state,
        status=RoomStatus.FINISHED,
        match=abandon(state.match, gone=gone),
        round=None,
        grace_deadline_ms=None,
    )
    return room, _match_end(room, reason="abandoned")


def _void(state: RoomState) -> Transition:
    assert state.match is not None
    room = replace(
        state,
        status=RoomStatus.FINISHED,
        match=void(state.match),
        round=None,
        grace_deadline_ms=None,
    )
    return room, _match_end(room, reason="abandoned")


def _resume(state: RoomState, now_ms: int) -> RoomState:
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


def _match_end(room: RoomState, *, reason: str) -> Effects:
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


def _room_state(state: RoomState, player: Player) -> protocols.RoomState:
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
    state: RoomState, slot: Player, now_ms: int
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


def _states(state: RoomState) -> Effects:
    """El estado completo, armado para cada silla: `you` cambia según quién mira."""
    effects: Effects = {}
    for idx, seat in enumerate(state.seats):
        if seat is None:
            continue
        player = Player.A if idx == 0 else Player.B
        effects[seat.user_id] = (_room_state(state, player),)
    return effects


def _broadcast(state: RoomState, message: protocols.Message) -> Effects:
    return {seat.user_id: (message,) for seat in state.seats if seat is not None}


def _error(code: str, message: str) -> protocols.Error:
    return protocols.Error(code=code, message=message)


def _merge(*maps: Effects) -> Effects:
    merged: Effects = {}
    for mapa in maps:
        for user_id, messages in mapa.items():
            merged[user_id] = merged.get(user_id, ()) + messages
    return merged


def _both_connected(state: RoomState) -> bool:
    return all(seat is not None and seat.connected for seat in state.seats)


def _full(state: RoomState) -> bool:
    return all(seat is not None for seat in state.seats)


def _seconds_left(state: RoomState, now_ms: int) -> int:
    assert state.grace_deadline_ms is not None
    return max(0, state.grace_deadline_ms - now_ms + 999) // 1000


def _slot_for(state: RoomState, user_id: str) -> Player:
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
