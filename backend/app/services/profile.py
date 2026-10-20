"""Lo que el perfil muestra además del usuario: sus marcas y su historial.

Las tres consultas son de lectura y van separadas porque responden a preguntas
distintas: el máximo aparece en el encabezado, y las dos listas tienen formas
que no comparten columnas. Mezclarlas en una timeline obligaría a inventar un
`type` y campos opcionales para ahorrar una vuelta a la base.

Solo entra lo `finished`. Una corrida cortada o una partida anulada no es una
marca ni un resultado: mostrarlas en el perfil sería ruido.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.solo_engine import RunStatus
from app.game.versus_engine import MatchStatus
from app.models import ArcadeRun, Match, User
from app.services.leaderboard import week_start

# Tope fijo: el perfil es un resumen, no un archivo. Un parámetro de paginación
# acá sería contrato nuevo para algo que el MVP no necesita.
HISTORY_LIMIT = 10


class Outcome(StrEnum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


@dataclass(frozen=True)
class BestMarks:
    """Los dos máximos del arcade. `None` mientras no haya corridas válidas."""

    all_time: int | None
    week: int | None


@dataclass(frozen=True)
class MatchSummary:
    id: uuid.UUID
    ended_at: datetime
    opponent_nick: str
    my_score: int
    opponent_score: int
    result: Outcome


async def best_marks(
    session: AsyncSession, *, user_id: uuid.UUID, now: datetime | None = None
) -> BestMarks:
    """Los dos máximos en una sola pasada: `FILTER` evita la segunda consulta.

    La semana se corta con el mismo `week_start` del ranking (lunes 00:00 de
    Buenos Aires), así la marca y la posición semanal no pueden discrepar.
    """
    marca = func.max(ArcadeRun.score)
    fila = (
        await session.execute(
            select(
                marca.label("all_time"),
                marca.filter(ArcadeRun.ended_at >= week_start(now)).label("week"),
            ).where(
                ArcadeRun.user_id == user_id,
                ArcadeRun.status == RunStatus.FINISHED.value,
            )
        )
    ).one()
    return BestMarks(all_time=fila.all_time, week=fila.week)


async def recent_runs(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = HISTORY_LIMIT
) -> list[ArcadeRun]:
    """Las últimas corridas, de la más nueva a la más vieja."""
    return list(
        (
            await session.scalars(
                select(ArcadeRun)
                .where(
                    ArcadeRun.user_id == user_id,
                    ArcadeRun.status == RunStatus.FINISHED.value,
                )
                .order_by(ArcadeRun.ended_at.desc(), ArcadeRun.id.desc())
                .limit(limit)
            )
        ).all()
    )


async def recent_matches(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = HISTORY_LIMIT
) -> list[MatchSummary]:
    """Las últimas partidas 1v1, ya puestas desde el punto de vista del jugador.

    `matches` no tiene "mis puntos" y "los del otro" (A3.4): el lado depende de
    la columna. Los `CASE` traducen una sola vez y el `JOIN` trae el nick rival
    sin una consulta por fila.
    """
    i_am_a = Match.player_a_id == user_id
    opponent_id = case((i_am_a, Match.player_b_id), else_=Match.player_a_id)
    my_score = case((i_am_a, Match.score_a), else_=Match.score_b)
    their_score = case((i_am_a, Match.score_b), else_=Match.score_a)

    filas = await session.execute(
        select(
            Match.id,
            Match.ended_at,
            Match.winner_id,
            my_score.label("my_score"),
            their_score.label("opponent_score"),
            User.nick.label("opponent_nick"),
        )
        .join(User, User.id == opponent_id)
        .where(
            or_(i_am_a, Match.player_b_id == user_id),
            Match.status == MatchStatus.FINISHED.value,
        )
        .order_by(Match.ended_at.desc(), Match.id.desc())
        .limit(limit)
    )
    return [
        MatchSummary(
            id=fila.id,
            ended_at=fila.ended_at,
            opponent_nick=fila.opponent_nick,
            my_score=fila.my_score,
            opponent_score=fila.opponent_score,
            result=_outcome(fila.winner_id, user_id),
        )
        for fila in filas
    ]


def _outcome(winner_id: uuid.UUID | None, user_id: uuid.UUID) -> Outcome:
    # Una partida terminada sin ganador es empate: el motor deja `winner` en
    # `None` cuando los puntajes coinciden.
    if winner_id is None:
        return Outcome.DRAW
    return Outcome.WIN if winner_id == user_id else Outcome.LOSS
