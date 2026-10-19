"""El banco de preguntas: de dónde salen las candidatas y qué se vio ya.

`services/questions.py` decide *cuál* pregunta va y no sabe de dónde vienen: es
puro. Acá está el otro extremo, el que sí toca Postgres y Redis, así el selector
se sigue probando sin levantar nada.

Desde 2.4 el banco lee el contenido genérico (`content_items` con `kind='quiz'`
y su fila en `content_solutions`), no la tabla vieja. La forma que ve el resto
del juego no cambia:

- `RoundQuestion` es lo que viaja al cliente y **no tiene** `correct_index`: el
  tipo no tiene dónde guardarlo, así que no hay descuido que lo filtre. La
  respuesta vive en `LoadedQuestion`, del lado del servidor.
- Los ids son texto, como en el selector: la conversión a `uuid` pasa una sola
  vez, en el borde de la base.
"""

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from random import Random
from typing import cast

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES
from app.game.modes.quiz import QUIZ, QuizCandidatesConfig, QuizPayload, QuizSolution
from app.models import ContentItem, ContentSolution
from app.services.questions import Candidate

# Historial del arcade: las últimas 50 que vio un jugador, y se olvida a las 24 h.
# No es la verdad del juego, es una memoria: si se pierde, se repite una pregunta.
SEEN_KEY = "arcade:seen:{user_id}"
SEEN_MAX = 50
SEEN_TTL = timedelta(hours=24)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoundQuestion:
    """La pregunta tal como la ve el jugador."""

    id: str
    prompt: str
    options: list[str]
    category: str
    difficulty: int
    explanation: str | None = None
    media_type: str = "none"
    media_url: str | None = None


@dataclass(frozen=True)
class LoadedQuestion:
    """La pregunta y, aparte, su respuesta: lo que el motor necesita y nadie más."""

    question: RoundQuestion
    correct_index: int


def shuffle_options(loaded: LoadedQuestion, rng: Random) -> LoadedQuestion:
    """Baraja las opciones y remapea el índice correcto (H-25).

    La correcta está en B en el 48 % de la semilla y las opciones no se mezclaban
    al servir: "tocar siempre la segunda" acertaba casi la mitad. Se barajan los
    **índices** y no los textos, así un banco con opciones repetidas no desplaza
    la respuesta. La pregunta guardada no se toca: vuelve una copia con la lista
    y el índice nuevos, y ese índice es el que viaja al motor y a `match_rounds`.
    """
    opciones = loaded.question.options
    if len(opciones) < 2:
        return loaded
    orden = list(range(len(opciones)))
    rng.shuffle(orden)
    return replace(
        loaded,
        question=replace(loaded.question, options=[opciones[i] for i in orden]),
        correct_index=orden.index(loaded.correct_index),
    )


def _primary_category(categories: Sequence[str]) -> str | None:
    """La primera categoría conocida del ítem.

    El selector todavía elige por una sola categoría y `Candidate` la valida
    contra la lista del juego. Un ítem sin ninguna categoría conocida no se
    puede ofrecer: se saltea en vez de romper la partida entera.
    """
    return next((category for category in categories if category in CATEGORIES), None)


async def candidates(
    session: AsyncSession,
    *,
    low: int | None = None,
    high: int | None = None,
) -> list[Candidate]:
    """Los ítems de quiz publicados, con lo mínimo para elegir.

    El filtro de dificultad puede bajar a la consulta (`low`/`high`): con el banco
    grande, traer todo y filtrar en memoria en cada ronda y por sala era el riesgo
    de escala de H-13. Sin rango, trae todas (lo que usan los tests y la CLI).
    """
    refs = await QUIZ.candidates(
        session, config=QuizCandidatesConfig(low=low, high=high)
    )
    candidatas: list[Candidate] = []
    for ref in refs:
        category = _primary_category(ref.categories)
        if category is None:
            logger.warning(
                "el contenido %s no tiene una categoría conocida: no se sirve",
                ref.content_id,
            )
            continue
        candidatas.append(
            Candidate(
                question_id=ref.content_id,
                category=category,
                difficulty=ref.difficulty,
            )
        )
    return candidatas


async def load(session: AsyncSession, question_id: str) -> LoadedQuestion | None:
    """Trae una pregunta por id, con o sin `status = published`.

    El filtro de publicadas vive en `candidates()` y no acá: una partida en curso
    no se puede romper porque alguien archive la pregunta en el medio. Los ids que
    llegan hasta acá salen de una selección, no de afuera.
    """
    content_id = uuid.UUID(question_id)
    item = await session.get(ContentItem, content_id)
    if item is None or item.kind != QUIZ.code:
        return None
    category = _primary_category(item.categories)
    if category is None:
        return None
    solution = await session.get(ContentSolution, content_id)
    if solution is None:
        return None

    public = QuizPayload.model_validate(item.payload)
    answer = QuizSolution.model_validate(solution.payload)
    return LoadedQuestion(
        question=RoundQuestion(
            id=str(item.id),
            prompt=public.prompt,
            options=list(public.options),
            category=category,
            difficulty=item.difficulty,
            explanation=answer.explanation,
            media_type=item.media_type,
            media_url=item.media_url,
        ),
        correct_index=answer.correct_index,
    )


def _seen_key(user_id: uuid.UUID) -> str:
    return SEEN_KEY.format(user_id=user_id)


async def seen_ids(redis: Redis, user_id: uuid.UUID) -> set[str]:
    """Qué preguntas vio este jugador, para no repetírselas.

    Si Redis no contesta, devuelve vacío y la partida arranca igual: lo peor que
    puede pasar es que se repita una pregunta, y eso es mucho mejor que no jugar.
    """
    try:
        # `cast`: los tipos de redis-py devuelven un union porque no saben si el
        # cliente decodifica. Los dos clientes del proyecto usan
        # `decode_responses=True` y sin `withscores`, así que son textos.
        vistas = await redis.zrange(_seen_key(user_id), 0, -1)
        return set(cast("list[str]", vistas))
    except (RedisError, OSError) as exc:
        logger.warning("Redis no contestó leyendo vistas (%s): sigo sin historial", exc)
        return set()


async def remember_seen(
    redis: Redis,
    user_id: uuid.UUID,
    question_id: str,
    *,
    now: datetime | None = None,
) -> None:
    """Anota una pregunta vista y tira las más viejas si pasó de `SEEN_MAX`.

    El conjunto ordenado guarda `cuándo` como puntaje: eso es lo que permite
    quedarse con las últimas 50 sin llevar la cuenta aparte.
    """
    clave = _seen_key(user_id)
    visto = (now or datetime.now(UTC)).timestamp()
    try:
        await redis.zadd(clave, {question_id: visto})
        await redis.zremrangebyrank(clave, 0, -SEEN_MAX - 1)
        await redis.expire(clave, SEEN_TTL)
    except (RedisError, OSError) as exc:
        logger.warning("Redis no contestó anotando la vista (%s): sigo jugando", exc)
