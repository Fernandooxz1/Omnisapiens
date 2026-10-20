"""El banco de preguntas: candidatas, la pregunta sin su respuesta y las vistas."""

import uuid
from datetime import UTC, datetime, timedelta
from random import Random

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models import ContentItem, ContentSolution
from app.services.question_bank import (
    SEEN_MAX,
    SEEN_TTL,
    LoadedQuestion,
    RoundQuestion,
    candidates,
    load,
    remember_seen,
    seen_ids,
    shuffle_options,
)
from app.services.questions import select

from .constraints import acepta
from .factories import content_item, quiz_content


async def _registrar(
    session: AsyncSession, *pares: tuple[ContentItem, ContentSolution]
) -> None:
    await acepta(session, *(fila for par in pares for fila in par))


async def banco_publicado(session: AsyncSession) -> list[ContentItem]:
    """Una pregunta publicada por categoría y dificultad: la grilla completa.

    Sin la grilla, una selección de dificultad 5 en `science` cae en el `FALLBACK`
    y el test de las 7 rondas no probaría lo que dice probar.
    """
    pares = [
        quiz_content(category=categoria, difficulty=dificultad, status="published")
        for categoria in CATEGORIES
        for dificultad in range(DIFFICULTY_MIN, DIFFICULTY_MAX + 1)
    ]
    await _registrar(session, *pares)
    return [item for item, _ in pares]


async def test_only_published_questions_are_candidates(
    session: AsyncSession,
) -> None:
    await _registrar(
        session,
        quiz_content(category="geography", status="published"),
        quiz_content(category="geography", status="draft"),
        quiz_content(category="history", status="archived"),
    )

    candidatas = await candidates(session)

    assert len(candidatas) == 1
    assert candidatas[0].category == "geography"


async def test_only_quiz_content_is_candidate(session: AsyncSession) -> None:
    publicada, _ = quiz_content(status="published")
    # Un ítem de otro kind no se sirve como pregunta de trivia.
    otro = content_item(kind="rosco", status="published")
    await acepta(session, publicada, otro)

    assert [candidata.question_id for candidata in await candidates(session)] == [
        str(publicada.id)
    ]


async def test_the_candidate_carries_only_what_is_needed_to_choose(
    session: AsyncSession,
) -> None:
    publicada, solucion = quiz_content(
        category="science", difficulty=4, status="published"
    )
    await _registrar(session, (publicada, solucion))

    (candidata,) = await candidates(session)

    assert candidata.question_id == str(publicada.id)
    assert candidata.difficulty == 4
    # La respuesta no viaja en la candidata: el selector no tiene por qué verla.
    assert not hasattr(candidata, "correct_index")


async def test_the_public_question_does_not_carry_the_answer(
    session: AsyncSession,
) -> None:
    publicada, solucion = quiz_content(correct_index=2, status="published")
    await acepta(session, publicada, solucion)

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
    publicada, solucion = quiz_content(status="published")
    await acepta(session, publicada, solucion)

    cargada = await load(session, str(publicada.id))

    assert cargada is not None
    assert isinstance(cargada.question, RoundQuestion)
    assert cargada.question.prompt == "¿Cuál es el río más largo?"
    assert cargada.question.options == ["Paraná", "Amazonas", "Orinoco", "Magdalena"]
    assert cargada.question.category == "geography"
    assert cargada.question.difficulty == publicada.difficulty


async def test_the_public_question_carries_media_and_explanation(
    session: AsyncSession,
) -> None:
    publicada, solucion = quiz_content(
        status="published",
        explanation="El Amazonas.",
        media_type="image",
        media_url="https://x/rio.png",
    )
    await acepta(session, publicada, solucion)

    cargada = await load(session, str(publicada.id))

    assert cargada is not None
    assert cargada.question.media_type == "image"
    assert cargada.question.media_url == "https://x/rio.png"
    assert cargada.question.explanation == "El Amazonas."


async def test_loading_a_question_that_is_not_there_returns_nothing(
    session: AsyncSession,
) -> None:
    assert await load(session, str(uuid.uuid4())) is None


async def test_a_question_archived_mid_match_is_still_loadable(
    session: AsyncSession,
) -> None:
    # El filtro de publicadas vive en `candidates()`: archivar no puede romper una
    # partida que ya la eligió.
    archivada, solucion = quiz_content(status="archived")
    await acepta(session, archivada, solucion)

    assert await load(session, str(archivada.id)) is not None


async def test_an_item_without_a_solution_is_not_served(session: AsyncSession) -> None:
    item = content_item(status="published")
    await acepta(session, item)

    assert await load(session, str(item.id)) is None


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


async def test_candidates_can_filter_the_difficulty_in_the_query(
    session: AsyncSession,
) -> None:
    await banco_publicado(session)

    candidatas = await candidates(session, low=4, high=5)

    assert candidatas
    assert {candidata.difficulty for candidata in candidatas} == {4, 5}


def _cargada(*, correct_index: int = 1) -> LoadedQuestion:
    return LoadedQuestion(
        question=RoundQuestion(
            id="q",
            prompt="¿Cuál es el río más largo?",
            options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            category="geography",
            difficulty=1,
        ),
        correct_index=correct_index,
    )


def test_shuffle_options_moves_the_answer_with_its_text() -> None:
    original = _cargada(correct_index=1)  # "Amazonas"

    for seed in range(20):
        barajada = shuffle_options(original, Random(seed))

        assert sorted(barajada.question.options) == sorted(original.question.options)
        assert barajada.question.options[barajada.correct_index] == "Amazonas"


def test_shuffle_options_remaps_the_solution_with_the_public_payload() -> None:
    original = LoadedQuestion(
        question=RoundQuestion(
            id="q",
            prompt="¿Cuál es el río más largo?",
            options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            category="geography",
            difficulty=1,
        ),
        correct_index=1,
        public={
            "v": 1,
            "prompt": "¿Cuál es el río más largo?",
            "options": [
                "Paraná",
                "Amazonas",
                "Orinoco",
                "Magdalena",
            ],
        },
        solution={"v": 1, "correct_index": 1, "explanation": None},
    )

    for seed in range(20):
        barajada = shuffle_options(original, Random(seed))

        assert barajada.solution["correct_index"] == barajada.correct_index
        assert (
            barajada.public["options"][barajada.correct_index]  # type: ignore[index]
            == "Amazonas"
        )


def test_shuffle_options_breaks_the_position_bias() -> None:
    original = _cargada(correct_index=1)
    posiciones = {
        shuffle_options(original, Random(seed)).correct_index for seed in range(40)
    }

    # La semilla tiene la correcta en B el 48 % de las veces; barajando, el
    # índice correcto tiene que repartirse y no quedar siempre en el mismo lugar.
    assert posiciones == {0, 1, 2, 3}


def test_shuffle_options_does_not_mutate_the_loaded_question() -> None:
    original = _cargada()

    shuffle_options(original, Random(1))

    assert original.question.options == ["Paraná", "Amazonas", "Orinoco", "Magdalena"]
    assert original.correct_index == 1
