"""`arcade_runs` y `arcade_answers`: la partida sola y sus rondas."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ArcadeAnswer, ArcadeRun, ContentItem, User

from .constraints import acepta, rechaza
from .factories import arcade_answer, arcade_run, quiz_content, user

HACE_UNA_HORA = datetime.now(UTC) - timedelta(hours=1)


class Escenario(NamedTuple):
    ana: User
    pregunta: ContentItem
    corrida: ArcadeRun


async def escenario(session: AsyncSession) -> Escenario:
    ana = user()
    pregunta, solucion = quiz_content()
    corrida = arcade_run(ana.id)
    await acepta(session, ana, pregunta, solucion, corrida)
    return Escenario(ana, pregunta, corrida)


# ---------------------------------------------------------------- arcade_runs


async def test_a_run_is_accepted(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await acepta(session, arcade_run(ana.id))


async def test_a_run_of_a_missing_user_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, arcade_run(uuid.uuid4()), motivo="fk_arcade_runs_user_id")


async def test_an_unknown_run_status_is_rejected(session: AsyncSession) -> None:
    # `abandoned` es de las partidas 1v1, no del arcade.
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, status="abandoned", ended_at=datetime.now(UTC)),
        motivo="ck_arcade_runs_status_known",
    )


async def test_a_negative_score_is_rejected(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, score=-1),
        motivo="ck_arcade_runs_counters_not_negative",
    )


async def test_a_streak_longer_than_the_hits_is_rejected(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(
            ana.id,
            score=100,
            correct_count=2,
            longest_streak=3,
            status="finished",
            ended_at=datetime.now(UTC),
        ),
        motivo="ck_arcade_runs_streak_within_corrects",
    )


async def test_difficulty_0_in_a_run_is_rejected(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, max_difficulty=0),
        motivo="ck_arcade_runs_difficulty_range",
    )


async def test_a_playing_run_with_an_end_date_is_rejected(
    session: AsyncSession,
) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, status="playing", ended_at=datetime.now(UTC)),
        motivo="ck_arcade_runs_ending_matches_status",
    )


async def test_a_finished_run_without_an_end_date_is_rejected(
    session: AsyncSession,
) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, status="finished"),
        motivo="ck_arcade_runs_ending_matches_status",
    )


async def test_a_run_that_ends_before_it_starts_is_rejected(
    session: AsyncSession,
) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        arcade_run(ana.id, status="finished", ended_at=HACE_UNA_HORA),
        motivo="ck_arcade_runs_ends_after_start",
    )


async def test_a_finished_run_is_accepted(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await acepta(
        session,
        arcade_run(
            ana.id,
            score=250,
            correct_count=3,
            longest_streak=2,
            max_difficulty=2,
            status="finished",
            ended_at=datetime.now(UTC),
        ),
    )


async def test_an_invalidated_run_is_accepted(session: AsyncSession) -> None:
    # `invalid` es lo que saca una partida del ranking sin borrarla.
    ana = user()
    await acepta(session, ana)

    await acepta(
        session,
        arcade_run(ana.id, status="invalid", ended_at=datetime.now(UTC)),
    )


async def test_defaults_of_a_new_run(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)
    corrida = arcade_run(ana.id)

    await acepta(session, corrida)

    assert corrida.score == 0
    assert corrida.correct_count == 0
    assert corrida.longest_streak == 0
    assert corrida.max_difficulty == 1
    assert corrida.status == "playing"
    assert corrida.ended_at is None
    assert corrida.started_at is not None


# ------------------------------------------------------------- arcade_answers


async def test_an_answer_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(session, arcade_answer(esc.corrida.id, question_id=esc.pregunta.id))


async def test_a_repeated_round_index_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, arcade_answer(esc.corrida.id, round_index=0))

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, round_index=0),
        motivo="uq_arcade_answers_run_id_round_index",
    )


async def test_an_answer_where_nobody_answered_is_accepted(
    session: AsyncSession,
) -> None:
    # `ms` nunca es nulo: cuando no hay respuesta, mide la ventana agotada.
    esc = await escenario(session)

    await acepta(
        session,
        arcade_answer(
            esc.corrida.id, chosen_index=None, is_correct=False, ms=18_000, points=0
        ),
    )


async def test_an_answer_out_of_the_window_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(
        session,
        arcade_answer(
            esc.corrida.id,
            seconds=16,
            chosen_index=None,
            is_correct=False,
            ms=16_000,
            points=0,
            rejected="outside_window",
        ),
    )


async def test_a_negative_round_index_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, round_index=-1),
        motivo="ck_arcade_answers_round_index_not_negative",
    )


async def test_difficulty_6_in_an_answer_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, difficulty=6),
        motivo="ck_arcade_answers_difficulty_range",
    )


async def test_an_answer_of_0_seconds_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        # `ms` en 0 para que la única regla violada sea la de los segundos.
        arcade_answer(esc.corrida.id, seconds=0, ms=0),
        motivo="ck_arcade_answers_seconds_positive",
    )


async def test_correct_index_4_in_an_answer_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(
            esc.corrida.id, correct_index=4, chosen_index=None, is_correct=False
        ),
        motivo="ck_arcade_answers_correct_index_choice",
    )


async def test_chosen_index_4_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, chosen_index=4, is_correct=False),
        motivo="ck_arcade_answers_chosen_in_range",
    )


async def test_a_hit_with_another_option_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, chosen_index=2, is_correct=True),
        motivo="ck_arcade_answers_correctness_from_choice",
    )


async def test_a_hit_without_answering_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, chosen_index=None, is_correct=True),
        motivo="ck_arcade_answers_correctness_from_choice",
    )


async def test_a_miss_with_the_correct_option_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, chosen_index=1, is_correct=False),
        motivo="ck_arcade_answers_correctness_from_choice",
    )


async def test_a_rejection_with_a_stored_choice_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, chosen_index=1, rejected="outside_window"),
        motivo="ck_arcade_answers_rejected_without_choice",
    )


async def test_an_unknown_reject_reason_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(
            esc.corrida.id,
            chosen_index=None,
            is_correct=False,
            rejected="trampa",
        ),
        motivo="ck_arcade_answers_rejection_known",
    )


async def test_a_negative_measured_time_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, ms=-1),
        motivo="ck_arcade_answers_ms_within_window",
    )


async def test_a_measured_time_beyond_the_window_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, ms=20_001),
        motivo="ck_arcade_answers_ms_within_window",
    )


async def test_a_measured_time_right_at_the_window_is_accepted(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await acepta(session, arcade_answer(esc.corrida.id, ms=20_000, points=100))


async def test_negative_points_are_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(esc.corrida.id, points=-5),
        motivo="ck_arcade_answers_points_not_negative",
    )


async def test_an_answer_of_a_missing_run_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        arcade_answer(uuid.uuid4(), question_id=esc.pregunta.id),
        motivo="fk_arcade_answers_run_id",
    )


async def test_deleting_a_question_leaves_the_answer_standing(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    respuesta = arcade_answer(esc.corrida.id, question_id=esc.pregunta.id)
    await acepta(session, respuesta)

    await session.delete(esc.pregunta)
    await session.commit()
    await session.refresh(respuesta)

    assert respuesta.question_id is None


async def test_deleting_a_run_deletes_its_answers(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, arcade_answer(esc.corrida.id), arcade_answer(esc.corrida.id))

    await session.delete(esc.corrida)
    await session.commit()

    quedan = await session.scalar(
        select(func.count())
        .select_from(ArcadeAnswer)
        .where(ArcadeAnswer.run_id == esc.corrida.id)
    )
    assert quedan == 0
