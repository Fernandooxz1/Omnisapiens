"""Lo que el perfil muestra además del usuario: sus marcas y su historial.

Las tres consultas son de lectura y van separadas porque responden a preguntas
distintas: el máximo aparece en el encabezado, y las dos listas tienen formas
que no comparten columnas. Mezclarlas en una timeline obligaría a inventar un
`type` y campos opcionales para ahorrar una vuelta a la base.

Desde la fase 10 leen `game_sessions`/`game_participants`: el arcade es una
sesión con dueño y el versus una sesión con dos sillas. Solo entra lo `finished`.
Una partida cortada o anulada no es una marca ni un resultado: mostrarlas en el
perfil sería ruido.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models import GameParticipant, GameSession, User
from app.services.leaderboard import ARCADE_MODE, week_start

# Tope fijo: el perfil es un resumen, no un archivo. Un parámetro de paginación
# acá sería contrato nuevo para algo que el MVP no necesita.
HISTORY_LIMIT = 10

VERSUS_FORMAT = "versus"
FINISHED = "finished"


class Outcome(StrEnum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


@dataclass(frozen=True)
class BestMarks:
    """Los dos máximos del arcade. `None` mientras no haya partidas válidas."""

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
    marca = func.max(GameSession.score)
    fila = (
        await session.execute(
            select(
                marca.label("all_time"),
                marca.filter(GameSession.ended_at >= week_start(now)).label("week"),
            ).where(
                GameSession.owner_user_id == user_id,
                GameSession.mode == ARCADE_MODE,
                GameSession.status == FINISHED,
            )
        )
    ).one()
    return BestMarks(all_time=fila.all_time, week=fila.week)


async def recent_runs(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = HISTORY_LIMIT
) -> list[GameSession]:
    """Las últimas partidas de arcade, de la más nueva a la más vieja."""
    return list(
        (
            await session.scalars(
                select(GameSession)
                .where(
                    GameSession.owner_user_id == user_id,
                    GameSession.mode == ARCADE_MODE,
                    GameSession.status == FINISHED,
                )
                .order_by(GameSession.ended_at.desc(), GameSession.id.desc())
                .limit(limit)
            )
        ).all()
    )


async def recent_matches(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = HISTORY_LIMIT
) -> list[MatchSummary]:
    """Las últimas partidas 1v1, ya puestas desde el punto de vista del jugador.

    Cada silla es una fila de `game_participants`: el `JOIN` con la silla rival
    trae el puntaje y el nick sin una consulta por partida.
    """
    mia = aliased(GameParticipant)
    rival = aliased(GameParticipant)
    rival_user = aliased(User)

    filas = await session.execute(
        select(
            GameSession.id,
            GameSession.ended_at,
            mia.score.label("my_score"),
            rival.score.label("opponent_score"),
            mia.outcome,
            rival_user.nick.label("opponent_nick"),
        )
        .join(mia, mia.session_id == GameSession.id)
        .join(
            rival,
            (rival.session_id == GameSession.id) & (rival.user_id != user_id),
        )
        .join(rival_user, rival_user.id == rival.user_id)
        .where(
            mia.user_id == user_id,
            GameSession.play_format == VERSUS_FORMAT,
            GameSession.status == FINISHED,
        )
        .order_by(GameSession.ended_at.desc(), GameSession.id.desc())
        .limit(limit)
    )
    return [
        MatchSummary(
            id=fila.id,
            ended_at=fila.ended_at,
            opponent_nick=fila.opponent_nick,
            my_score=fila.my_score,
            opponent_score=fila.opponent_score,
            result=_outcome(fila.outcome),
        )
        for fila in filas
    ]


def _outcome(outcome: str | None) -> Outcome:
    # El motor cierra una partida terminada como win/lose/draw; el `None` solo
    # puede venir de una fila escrita a mano, y mostrarla como empate es lo menos
    # engañoso.
    if outcome == Outcome.WIN.value:
        return Outcome.WIN
    if outcome == Outcome.LOSS.value:
        return Outcome.LOSS
    return Outcome.DRAW
