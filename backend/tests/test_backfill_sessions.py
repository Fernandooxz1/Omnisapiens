"""El backfill de las tablas viejas de arcade y versus a las tablas de sesión.

Contra Postgres real: lo que se prueba es la reconstrucción fila a fila, la
secuencia de ítems y que correrlo dos veces no duplique nada.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    GameParticipant,
    GameSession,
    SessionAttempt,
    SessionItem,
)
from app.services.session_backfill import backfill_sessions

from .constraints import acepta
from .factories import (
    arcade_answer,
    arcade_run,
    match,
    match_round,
    quiz_content,
    user,
)

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


async def _count(session: AsyncSession, model: Any) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


async def _items(session: AsyncSession, session_id: Any) -> list[SessionItem]:
    return list(
        (
            await session.scalars(
                select(SessionItem)
                .where(SessionItem.session_id == session_id)
                .order_by(SessionItem.position)
            )
        ).all()
    )


async def _attempts(session: AsyncSession, session_id: Any) -> list[SessionAttempt]:
    return list(
        (
            await session.scalars(
                select(SessionAttempt)
                .join(SessionItem, SessionAttempt.item_id == SessionItem.id)
                .where(SessionItem.session_id == session_id)
                .order_by(SessionItem.position, SessionAttempt.seat)
            )
        ).all()
    )


# ------------------------------------------------------------------ arcade


async def test_an_arcade_run_becomes_a_finished_session(
    session: AsyncSession,
) -> None:
    ana = user()
    first, first_solution = quiz_content(correct_index=1)
    second, second_solution = quiz_content(correct_index=2)
    run = arcade_run(
        ana.id,
        status="finished",
        score=325,
        correct_count=2,
        longest_streak=2,
        max_difficulty=3,
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=25),
    )
    answers = (
        arcade_answer(
            run.id,
            round_index=0,
            question_id=first.id,
            difficulty=1,
            seconds=20,
            correct_index=1,
            chosen_index=1,
            is_correct=True,
            ms=3_000,
            points=180,
        ),
        arcade_answer(
            run.id,
            round_index=1,
            question_id=second.id,
            difficulty=3,
            seconds=15,
            correct_index=2,
            chosen_index=0,
            is_correct=False,
            ms=5_000,
            points=0,
        ),
    )
    await acepta(
        session,
        ana,
        first,
        first_solution,
        second,
        second_solution,
        run,
        *answers,
    )

    report = await backfill_sessions(session)

    assert (report.read, report.created, report.existing) == (1, 1, 0)
    assert report.skipped == []

    row = await session.get(GameSession, run.id)
    assert row is not None
    assert (row.mode, row.play_format, row.content_kind) == (
        "trivia_arcade",
        "arcade",
        "quiz",
    )
    assert row.ruleset_version == 1
    assert row.config == {}
    assert row.owner_user_id == ana.id
    assert row.room_id is None
    assert (row.status, row.score, row.correct_count) == ("finished", 325, 2)
    assert (row.longest_streak, row.max_difficulty) == (2, 3)
    assert (row.started_at, row.ended_at) == (
        NOW,
        NOW + timedelta(seconds=25),
    )

    items = await _items(session, run.id)
    assert [(item.item_key, item.position) for item in items] == [("0", 0), ("1", 1)]
    assert items[0].content_id == first.id
    assert items[0].difficulty == 1
    assert items[0].seconds == 20
    # Los tiempos viejos no existen: se reconstruyen contiguos desde el arranque.
    assert items[0].served_at == NOW
    assert items[0].deadline_at == NOW + timedelta(seconds=20)
    assert items[0].closed_at == NOW + timedelta(seconds=3)
    assert items[1].served_at == NOW + timedelta(seconds=3)
    assert items[0].solution_snapshot == {"v": 1, "correct_index": 1}
    assert items[1].solution_snapshot == {"v": 1, "correct_index": 2}

    attempts = await _attempts(session, run.id)
    assert [(a.seat, a.correct, a.points) for a in attempts] == [
        (0, True, 180),
        (0, False, 0),
    ]
    assert attempts[0].submission == {"type": "choice", "index": 1}
    assert attempts[0].elapsed_ms == 3_000
    assert attempts[0].submitted_at == NOW + timedelta(seconds=3)


async def test_an_arcade_timeout_keeps_its_attempt_without_a_choice(
    session: AsyncSession,
) -> None:
    ana = user()
    question, solution = quiz_content()
    run = arcade_run(
        ana.id,
        status="finished",
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=20),
    )
    answer = arcade_answer(
        run.id,
        round_index=0,
        question_id=question.id,
        seconds=20,
        chosen_index=None,
        is_correct=False,
        ms=20_000,
        points=0,
    )
    await acepta(session, ana, question, solution, run, answer)

    await backfill_sessions(session)

    attempt = (await _attempts(session, run.id))[0]
    assert attempt.submission == {}
    assert (attempt.correct, attempt.elapsed_ms) == (False, 20_000)
    assert attempt.submitted_at == NOW + timedelta(seconds=20)


# ------------------------------------------------------------------ versus


async def test_a_match_becomes_a_versus_session_with_both_seats(
    session: AsyncSession,
) -> None:
    ana, beto = user(), user()
    first, first_solution = quiz_content(correct_index=1)
    second, second_solution = quiz_content(correct_index=2)
    partida = match(
        ana.id,
        beto.id,
        status="finished",
        config={"rounds": 7, "seconds": 20},
        score_a=180,
        score_b=145,
        winner_id=ana.id,
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=40),
    )
    rounds = (
        match_round(
            partida.id,
            round_index=0,
            question_id=first.id,
            difficulty=2,
            seconds=20,
            correct_index=1,
            a_choice=1,
            b_choice=0,
            a_ms=3_000,
            b_ms=9_000,
            a_correct=True,
            b_correct=False,
            a_points=180,
            b_points=0,
        ),
        match_round(
            partida.id,
            round_index=1,
            question_id=second.id,
            difficulty=3,
            seconds=20,
            correct_index=2,
            a_choice=0,
            b_choice=2,
            a_ms=5_000,
            b_ms=6_000,
            a_correct=False,
            b_correct=True,
            a_points=0,
            b_points=145,
        ),
    )
    await acepta(
        session,
        ana,
        beto,
        first,
        first_solution,
        second,
        second_solution,
        partida,
        *rounds,
    )

    report = await backfill_sessions(session)

    assert (report.read, report.created, report.existing) == (1, 1, 0)
    row = await session.get(GameSession, partida.id)
    assert row is not None
    assert (row.mode, row.play_format, row.content_kind) == (
        "trivia_versus",
        "versus",
        "quiz",
    )
    assert row.config == {"rounds": 7, "seconds": 20}
    assert row.owner_user_id is None
    assert row.status == "finished"
    assert (row.score, row.correct_count, row.longest_streak) == (180, 2, 1)
    assert row.max_difficulty == 3

    seats = (
        await session.execute(
            select(
                GameParticipant.seat,
                GameParticipant.user_id,
                GameParticipant.score,
                GameParticipant.outcome,
            )
            .where(GameParticipant.session_id == partida.id)
            .order_by(GameParticipant.seat)
        )
    ).all()
    assert seats == [(0, ana.id, 180, "win"), (1, beto.id, 145, "lose")]

    items = await _items(session, partida.id)
    assert [item.item_key for item in items] == ["0", "1"]
    assert items[0].served_at == NOW
    assert items[0].closed_at == NOW + timedelta(seconds=9)
    assert items[1].served_at == NOW + timedelta(seconds=9)

    attempts = await _attempts(session, partida.id)
    assert [(a.seat, a.correct, a.points) for a in attempts] == [
        (0, True, 180),
        (1, False, 0),
        (0, False, 0),
        (1, True, 145),
    ]
    assert attempts[1].submission == {"type": "choice", "index": 0}
    assert attempts[1].submitted_at == NOW + timedelta(seconds=9)


async def test_a_draw_has_no_winner(session: AsyncSession) -> None:
    ana, beto = user(), user()
    question, solution = quiz_content()
    partida = match(
        ana.id,
        beto.id,
        status="finished",
        score_a=100,
        score_b=100,
        winner_id=None,
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=20),
    )
    ronda = match_round(
        partida.id,
        round_index=0,
        question_id=question.id,
        a_choice=1,
        b_choice=1,
        a_ms=3_000,
        b_ms=3_000,
        a_correct=True,
        b_correct=True,
        a_points=100,
        b_points=100,
    )
    await acepta(session, ana, beto, question, solution, partida, ronda)

    await backfill_sessions(session)

    seats = (
        (
            await session.execute(
                select(GameParticipant.outcome)
                .where(GameParticipant.session_id == partida.id)
                .order_by(GameParticipant.seat)
            )
        )
        .scalars()
        .all()
    )
    assert list(seats) == ["draw", "draw"]


async def test_an_abandoned_match_without_an_end_gets_one(
    session: AsyncSession,
) -> None:
    ana, beto = user(), user()
    question, solution = quiz_content()
    partida = match(
        ana.id,
        beto.id,
        status="abandoned",
        started_at=NOW,
        ended_at=None,
    )
    ronda = match_round(
        partida.id,
        round_index=0,
        question_id=question.id,
        a_choice=1,
        b_choice=None,
        a_ms=3_000,
        b_ms=None,
        a_correct=True,
        b_correct=False,
        a_points=145,
        b_points=0,
    )
    await acepta(session, ana, beto, question, solution, partida, ronda)

    await backfill_sessions(session)

    row = await session.get(GameSession, partida.id)
    assert row is not None
    assert row.status == "abandoned"
    assert row.ended_at is not None
    assert row.ended_at >= row.started_at
    outcomes = (
        (
            await session.execute(
                select(GameParticipant.outcome)
                .where(GameParticipant.session_id == partida.id)
                .order_by(GameParticipant.seat)
            )
        )
        .scalars()
        .all()
    )
    assert list(outcomes) == ["abandoned", "abandoned"]
    # La silla que no respondió conserva la ventana entera como tiempo.
    attempts = await _attempts(session, partida.id)
    assert attempts[1].submission == {}
    assert attempts[1].elapsed_ms == 20_000


# ------------------------------------------------------------- idempotencia


async def test_running_it_twice_does_not_duplicate_anything(
    session: AsyncSession,
) -> None:
    ana, beto = user(), user()
    question, solution = quiz_content()
    run = arcade_run(
        ana.id,
        status="finished",
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=10),
    )
    answer = arcade_answer(run.id, round_index=0, question_id=question.id, ms=2_000)
    partida = match(
        ana.id,
        beto.id,
        status="finished",
        started_at=NOW,
        ended_at=NOW + timedelta(seconds=20),
    )
    ronda = match_round(partida.id, round_index=0, question_id=question.id)
    await acepta(
        session,
        ana,
        beto,
        question,
        solution,
        run,
        answer,
        partida,
        ronda,
    )

    first = await backfill_sessions(session)
    second = await backfill_sessions(session)

    assert (first.read, first.created, first.existing) == (2, 2, 0)
    assert (second.read, second.created, second.existing) == (2, 0, 2)
    assert await _count(session, GameSession) == 2
    assert await _count(session, SessionItem) == 2
    # Arcade: 1 intento; versus: 2 sillas en la única ronda.
    assert await _count(session, SessionAttempt) == 3


async def test_sessions_still_playing_are_skipped(session: AsyncSession) -> None:
    ana, beto = user(), user()
    run = arcade_run(ana.id, status="playing")
    partida = match(ana.id, beto.id, status="playing")
    await acepta(session, ana, beto, run, partida)

    report = await backfill_sessions(session)

    assert (report.read, report.created, report.existing) == (2, 0, 0)
    assert [item.session_id for item in report.skipped] == [run.id, partida.id]
    assert await _count(session, GameSession) == 0
