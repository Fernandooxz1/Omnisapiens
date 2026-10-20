"""Backfill de `arcade_runs`/`matches` a las tablas genéricas de sesión.

Es un comando de mantenimiento, no una migración: las tablas viejas quedan de
solo lectura hasta la fase 10. La sesión conserva el UUID de la partida
original, así que correr el backfill dos veces no duplica nada y el `id` es la
última red.

Las tablas viejas no guardan el instante de cada ronda, solo el `started_at` y
los milisegundos de cada respuesta. Los ítems se reconstruyen en forma
contigua desde el arranque: lo que se muestra después de una respuesta empieza
cuando esa respuesta se cerró. Es la única lectura posible de esos datos y deja
la secuencia y los puntajes idénticos.

Una fila `playing` se salta: el camino en vivo la sigue escribiendo y no hay
cierre que reconstruir. El comando se puede correr con partidas en curso.
"""

import uuid
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ArcadeAnswer,
    ArcadeRun,
    ContentItem,
    GameParticipant,
    GameSession,
    Match,
    MatchRound,
    SessionAttempt,
    SessionItem,
)

ARCADE_MODE = "trivia_arcade"
VERSUS_MODE = "trivia_versus"
CONTENT_KIND = "quiz"
RULESET_VERSION = 1
SOLUTION_VERSION = 1


@dataclass(frozen=True)
class SkippedSession:
    session_id: uuid.UUID
    reason: str


@dataclass(frozen=True)
class BackfillReport:
    read: int
    created: int
    existing: int
    skipped: list[SkippedSession] = field(default_factory=list)


def _choice(index: int | None) -> dict[str, object]:
    """La submission del quiz; una omisión no inventa una opción."""
    if index is None:
        return {}
    return {"type": "choice", "index": index}


def _window_ms(seconds: int) -> int:
    return seconds * 1000


def _content_id(
    question_id: uuid.UUID | None, known: set[uuid.UUID]
) -> uuid.UUID | None:
    """La FK vieja es `NOT VALID`: un id sin copiar en `content_items` va nulo.

    La `solution_snapshot` ya deja la fila auditable, así que perder el vínculo
    con el contenido huérfano no cuesta nada y no obliga a correr
    `backfill-content` antes que este comando.
    """
    return question_id if question_id in known else None


def _submitted_at(served_at: datetime, elapsed_ms: int) -> datetime:
    return served_at + timedelta(milliseconds=elapsed_ms)


def _effective_end(
    ended_at: datetime | None, started_at: datetime, last_closed: datetime
) -> datetime:
    """La sesión cerrada necesita un final aunque la tabla vieja no lo traiga."""
    if ended_at is not None:
        return ended_at
    return max(last_closed, started_at)


def _attempt(
    *,
    item_id: uuid.UUID,
    seat: int,
    served_at: datetime,
    choice: int | None,
    elapsed_ms: int,
    correct: bool,
    points: int,
    rejected: str | None,
) -> SessionAttempt:
    return SessionAttempt(
        id=uuid.uuid4(),
        item_id=item_id,
        attempt_seq=0,
        seat=seat,
        submitted_at=_submitted_at(served_at, elapsed_ms),
        submission=_choice(choice),
        correct=correct,
        elapsed_ms=elapsed_ms,
        points=points,
        rejected=rejected,
    )


def _arcade_history(
    run: ArcadeRun, answers: Sequence[ArcadeAnswer], known: set[uuid.UUID]
) -> tuple[list[SessionItem], list[SessionAttempt], datetime]:
    items: list[SessionItem] = []
    attempts: list[SessionAttempt] = []
    cursor = run.started_at

    for answer in answers:
        served_at = cursor
        submitted_at = _submitted_at(served_at, answer.ms)
        item_id = uuid.uuid4()
        items.append(
            SessionItem(
                id=item_id,
                session_id=run.id,
                item_key=str(answer.round_index),
                position=answer.round_index,
                content_id=_content_id(answer.question_id, known),
                difficulty=answer.difficulty,
                seconds=answer.seconds,
                served_at=served_at,
                deadline_at=served_at + timedelta(seconds=answer.seconds),
                closed_at=submitted_at,
                solution_snapshot={
                    "v": SOLUTION_VERSION,
                    "correct_index": answer.correct_index,
                },
            )
        )
        attempts.append(
            _attempt(
                item_id=item_id,
                seat=0,
                served_at=served_at,
                choice=answer.chosen_index,
                elapsed_ms=answer.ms,
                correct=answer.is_correct,
                points=answer.points,
                rejected=answer.rejected,
            )
        )
        cursor = submitted_at

    return items, attempts, cursor


def _versus_outcome(match: Match) -> tuple[str, str]:
    if match.status == "finished":
        if match.winner_id is None:
            return "draw", "draw"
        if match.winner_id == match.player_a_id:
            return "win", "lose"
        return "lose", "win"
    if match.status == "abandoned":
        return "abandoned", "abandoned"
    return "void", "void"


def _longest_streak(flags: Iterable[bool]) -> int:
    best = current = 0
    for correct in flags:
        current = current + 1 if correct else 0
        best = max(best, current)
    return best


def _versus_history(
    match: Match, rounds: Sequence[MatchRound], known: set[uuid.UUID]
) -> tuple[list[SessionItem], list[SessionAttempt], datetime]:
    items: list[SessionItem] = []
    attempts: list[SessionAttempt] = []
    cursor = match.started_at
    a_corrects: list[bool] = []
    b_corrects: list[bool] = []

    for rnd in rounds:
        served_at = cursor
        # Sin respuesta, la ronda consumió la ventana entera: es lo que mide el motor.
        a_elapsed = rnd.a_ms if rnd.a_ms is not None else _window_ms(rnd.seconds)
        b_elapsed = rnd.b_ms if rnd.b_ms is not None else _window_ms(rnd.seconds)
        closed_at = _submitted_at(served_at, max(a_elapsed, b_elapsed))
        item_id = uuid.uuid4()
        items.append(
            SessionItem(
                id=item_id,
                session_id=match.id,
                item_key=str(rnd.round_index),
                position=rnd.round_index,
                content_id=_content_id(rnd.question_id, known),
                difficulty=rnd.difficulty,
                seconds=rnd.seconds,
                served_at=served_at,
                deadline_at=served_at + timedelta(seconds=rnd.seconds),
                closed_at=closed_at,
                solution_snapshot={
                    "v": SOLUTION_VERSION,
                    "correct_index": rnd.correct_index,
                },
            )
        )
        attempts.append(
            _attempt(
                item_id=item_id,
                seat=0,
                served_at=served_at,
                choice=rnd.a_choice,
                elapsed_ms=a_elapsed,
                correct=rnd.a_correct,
                points=rnd.a_points,
                rejected=rnd.a_rejected,
            )
        )
        attempts.append(
            _attempt(
                item_id=item_id,
                seat=1,
                served_at=served_at,
                choice=rnd.b_choice,
                elapsed_ms=b_elapsed,
                correct=rnd.b_correct,
                points=rnd.b_points,
                rejected=rnd.b_rejected,
            )
        )
        a_corrects.append(rnd.a_correct)
        b_corrects.append(rnd.b_correct)
        cursor = closed_at

    return items, attempts, cursor


async def _write_arcade(
    session: AsyncSession,
    run: ArcadeRun,
    answers: Sequence[ArcadeAnswer],
    known: set[uuid.UUID],
) -> None:
    items, attempts, last_closed = _arcade_history(run, answers, known)
    session.add(
        GameSession(
            id=run.id,
            mode=ARCADE_MODE,
            content_kind=CONTENT_KIND,
            play_format="arcade",
            ruleset_version=RULESET_VERSION,
            status=run.status,
            # La partida vieja no tenía configuración: las reglas son las fijas
            # de `ruleset_version`.
            config={},
            owner_user_id=run.user_id,
            score=run.score,
            correct_count=run.correct_count,
            longest_streak=run.longest_streak,
            max_difficulty=run.max_difficulty,
            started_at=run.started_at,
            ended_at=_effective_end(run.ended_at, run.started_at, last_closed),
        )
    )
    # Sin `relationship()` el flush intermedio fija el orden padre → ítem → intento.
    await session.flush()
    session.add_all(items)
    await session.flush()
    session.add_all(attempts)


async def _write_versus(
    session: AsyncSession,
    match: Match,
    rounds: Sequence[MatchRound],
    known: set[uuid.UUID],
) -> None:
    items, attempts, last_closed = _versus_history(match, rounds, known)
    outcome_a, outcome_b = _versus_outcome(match)
    correct_count = sum(1 for attempt in attempts if attempt.correct)
    longest_streak = max(
        _longest_streak(rnd.a_correct for rnd in rounds),
        _longest_streak(rnd.b_correct for rnd in rounds),
    )
    session.add(
        GameSession(
            id=match.id,
            mode=VERSUS_MODE,
            content_kind=CONTENT_KIND,
            play_format="versus",
            ruleset_version=RULESET_VERSION,
            status=match.status,
            config=dict(match.config),
            room_id=match.room_id,
            score=max(match.score_a, match.score_b),
            correct_count=correct_count,
            longest_streak=longest_streak,
            max_difficulty=max((rnd.difficulty for rnd in rounds), default=1),
            started_at=match.started_at,
            ended_at=_effective_end(match.ended_at, match.started_at, last_closed),
        )
    )
    await session.flush()
    session.add_all(
        (
            GameParticipant(
                session_id=match.id,
                seat=0,
                user_id=match.player_a_id,
                score=match.score_a,
                outcome=outcome_a,
            ),
            GameParticipant(
                session_id=match.id,
                seat=1,
                user_id=match.player_b_id,
                score=match.score_b,
                outcome=outcome_b,
            ),
        )
    )
    await session.flush()
    session.add_all(items)
    await session.flush()
    session.add_all(attempts)


def _group[RowT](rows: Iterable[RowT], key: str) -> dict[uuid.UUID, list[RowT]]:
    grouped: dict[uuid.UUID, list[RowT]] = defaultdict(list)
    for row in rows:
        grouped[getattr(row, key)].append(row)
    return dict(grouped)


async def backfill_sessions(session: AsyncSession) -> BackfillReport:
    """Copia las partidas viejas a `game_sessions` y sus hijos.

    No borra ni modifica las tablas viejas. Un id ya presente en
    `game_sessions` se cuenta como existente y no se vuelve a escribir.
    """
    existing_ids: set[uuid.UUID] = set(
        (await session.scalars(select(GameSession.id))).all()
    )
    known_content: set[uuid.UUID] = set(
        (await session.scalars(select(ContentItem.id))).all()
    )
    read = created = existing_count = 0
    skipped: list[SkippedSession] = []

    runs = (await session.scalars(select(ArcadeRun).order_by(ArcadeRun.id))).all()
    answers = _group(
        (
            await session.scalars(
                select(ArcadeAnswer).order_by(
                    ArcadeAnswer.run_id, ArcadeAnswer.round_index
                )
            )
        ).all(),
        "run_id",
    )
    for run in runs:
        read += 1
        if run.status == "playing":
            skipped.append(SkippedSession(run.id, "la partida sigue jugando"))
            continue
        if run.id in existing_ids:
            existing_count += 1
            continue
        await _write_arcade(session, run, answers.get(run.id, []), known_content)
        existing_ids.add(run.id)
        created += 1

    matches = (await session.scalars(select(Match).order_by(Match.id))).all()
    rounds = _group(
        (
            await session.scalars(
                select(MatchRound).order_by(MatchRound.match_id, MatchRound.round_index)
            )
        ).all(),
        "match_id",
    )
    for match in matches:
        read += 1
        if match.status == "playing":
            skipped.append(SkippedSession(match.id, "la partida sigue jugando"))
            continue
        if match.id in existing_ids:
            existing_count += 1
            continue
        await _write_versus(session, match, rounds.get(match.id, []), known_content)
        existing_ids.add(match.id)
        created += 1

    return BackfillReport(
        read=read,
        created=created,
        existing=existing_count,
        skipped=skipped,
    )
