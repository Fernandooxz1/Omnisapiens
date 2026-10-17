"""El banco de preguntas: candidatas, la pregunta sin su respuesta y las vistas."""

import uuid
from datetime import UTC, datetime, timedelta
from random import Random

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models import Question
from app.services.question_bank import (
    SEEN_MAX,
    SEEN_TTL,
    RoundQuestion,
    candidates,
    load,
    remember_seen,
    seen_ids,
)
from app.services.questions import select

from .constraints import acepta
from .factories import question


async def banco_publicado(session: AsyncSession) -> list[Question]:
    """Una pregunta publicada por categoría y dificultad: la grilla completa.

    Sin la grilla, una selección de dificultad 5 en `science` cae en el `FALLBACK`
    y el test de las 7 rondas no probaría lo que dice probar.
    """
    preguntas = [
        question(category=categoria, difficulty=dificultad, status="published")
        for categoria in CATEGORIES
        for dificultad in range(DIFFICULTY_MIN, DIFFICULTY_MAX + 1)
    ]
    await acepta(session, *preguntas)
    return preguntas


async def test_only_published_questions_are_candidates(
    session: AsyncSession,
) -> None:
    await acepta(
        session,
        question(category="geography", status="published"),
        question(category="geography", status="draft"),
        question(category="history", status="archived"),
    )

    candidatas = await candidates(session)

    assert len(candidatas) == 1
    assert candidatas[0].category == "geography"


async def test_the_candidate_carries_only_what_is_needed_to_choose(
    session: AsyncSession,
) -> None:
    publicada = question(category="science", difficulty=4, status="published")
    await acepta(session, publicada)

    (candidata,) = await candidates(session)

    assert candidata.question_id == str(publicada.id)
    assert candidata.difficulty == 4
    # La respuesta no viaja en la candidata: el selector no tiene por qué verla.
    assert not hasattr(candidata, "correct_index")


async def test_the_public_question_does_not_carry_the_answer(
    session: AsyncSession,
) -> None:
    publicada = question(correct_index=2, status="published")
    await acepta(session, publicada)

    cargada = await load(session, str(publicada.id))

    assert cargada is not None
    assert cargada.correct_index == 2
    # El tipo que va al cliente no tiene dónde guardarla. Esto no es cosmético:
    # si el campo existe, tarde o temprano alguien serializa el objeto entero.
    assert not hasattr(cargada.question, "correct_index")
    assert set(vars(cargada.question)) == {
        "id",
        "prompt",
        "options",
        "category",
        "difficulty",
        "explanation",
        "media_type",
        "media_url",
    }


async def test_the_public_question_carries_what_the_table_shows(
    session: AsyncSession,
) -> None:
    publicada = question(status="published")
    await acepta(session, publicada)

    cargada = await load(session, str(publicada.id))

    assert cargada is not None
    assert isinstance(cargada.question, RoundQuestion)
    assert cargada.question.prompt == publicada.prompt
    assert cargada.question.options == publicada.options


async def test_loading_a_question_that_is_not_there_returns_nothing(
    session: AsyncSession,
) -> None:
    assert await load(session, str(uuid.uuid4())) is None


async def test_a_question_archived_mid_match_is_still_loadable(
    session: AsyncSession,
) -> None:
    # El filtro de publicadas vive en `candidates()`: archivar no puede romper una
    # partida que ya la eligió.
    archivada = question(status="archived")
    await acepta(session, archivada)

    assert await load(session, str(archivada.id)) is not None


async def test_seven_rounds_never_repeat_a_question(session: AsyncSession) -> None:
    await banco_publicado(session)
    candidatas = await candidates(session)
    rng = Random(20261017)
    vistas: set[str] = set()
    elegidas: list[str] = []

    for ronda in range(7):
        # La dificultad por ronda del plan (§9.2), calculada fuera del banco.
        objetivo = min(1 + ronda // 2, 5)
        seleccion = select(
            candidatas,
            category=rng.choice(list(CATEGORIES)),
            difficulty=objetivo,
            rng=rng,
            excluded=vistas,
        )
        elegidas.append(seleccion.question_id)
        vistas.add(seleccion.question_id)

    assert len(set(elegidas)) == 7


async def test_a_seen_question_is_remembered(redis: Redis) -> None:
    jugador = uuid.uuid4()

    await remember_seen(redis, jugador, "una-pregunta")

    assert await seen_ids(redis, jugador) == {"una-pregunta"}


async def test_the_memory_of_what_was_seen_expires(redis: Redis) -> None:
    jugador = uuid.uuid4()

    await remember_seen(redis, jugador, "una-pregunta")

    segundos = await redis.ttl(f"arcade:seen:{jugador}")
    assert 0 < segundos <= SEEN_TTL.total_seconds()


async def test_only_the_last_fifty_questions_are_remembered(redis: Redis) -> None:
    jugador = uuid.uuid4()
    arranque = datetime.now(UTC)

    for numero in range(SEEN_MAX + 1):
        await remember_seen(
            redis,
            jugador,
            f"pregunta-{numero}",
            now=arranque + timedelta(seconds=numero),
        )

    vistas = await seen_ids(redis, jugador)
    assert len(vistas) == SEEN_MAX
    # La primera es la que se cae: el conjunto está ordenado por cuándo se vio.
    assert "pregunta-0" not in vistas
    assert f"pregunta-{SEEN_MAX}" in vistas


async def test_what_one_player_saw_does_not_follow_another(redis: Redis) -> None:
    ana, beto = uuid.uuid4(), uuid.uuid4()
    await remember_seen(redis, ana, "una-pregunta")

    assert await seen_ids(redis, beto) == set()


class RedisQueNoContesta(Redis):
    """Redis caído: contesta con el error de conexión, como en la vida real."""

    async def zrange(self, *args: object, **kwargs: object) -> list[str]:
        raise RedisConnectionError("no hay Redis")

    async def zadd(self, *args: object, **kwargs: object) -> int:
        raise RedisConnectionError("no hay Redis")

    async def zremrangebyrank(self, *args: object, **kwargs: object) -> int:
        raise RedisConnectionError("no hay Redis")

    async def expire(self, *args: object, **kwargs: object) -> bool:
        raise RedisConnectionError("no hay Redis")


async def test_with_redis_down_the_game_goes_on_without_history() -> None:
    caido = RedisQueNoContesta()
    jugador = uuid.uuid4()

    # Ni leer ni anotar levantan: la partida arranca y lo peor es repetir una pregunta.
    assert await seen_ids(caido, jugador) == set()
    await remember_seen(caido, jugador, "una-pregunta")


async def test_redis_really_is_answering(redis: Redis) -> None:
    # Sin esto, los tests de arriba podrían estar pasando por el camino de
    # degradación y no por el camino real, y nadie se enteraría.
    assert await redis.ping() is True
