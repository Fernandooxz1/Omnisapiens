"""El ranking de cada modo: la tabla y la posición del jugador.

Es público, como la tabla que se mira al terminar una partida. `/me` sí pide
token, porque la posición es "la tuya". Un modo sin ranking responde 404: el
cliente lo oculta usando `GET /modes`.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.game.modes import get as get_mode
from app.schemas.leaderboard import (
    LeaderboardEntry,
    LeaderboardOut,
    MyRanksOut,
    RankOut,
)
from app.services import leaderboard
from app.services.leaderboard import Period

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

# Compatibilidad hasta que el frontend migre a `/leaderboard/trivia_arcade`.
MODE_ALIASES = {"arcade": "trivia_arcade"}


def _ranked_mode(mode: str) -> str:
    resolved = MODE_ALIASES.get(mode, mode)
    try:
        game_mode = get_mode(resolved)
    except KeyError:
        raise ApiError(
            404, "MODE_WITHOUT_RANKING", "Ese modo no tiene ranking."
        ) from None
    if game_mode.ranking is None:
        raise ApiError(404, "MODE_WITHOUT_RANKING", "Ese modo no tiene ranking.")
    return resolved


@router.get("/{mode}/me")
async def my_mode_ranks(
    mode: str, usuario: CurrentUserDep, session: SessionDep
) -> MyRanksOut:
    ranked = _ranked_mode(mode)
    global_ = await leaderboard.rank(
        session, mode=ranked, user_id=usuario.id, period=Period.ALL
    )
    weekly = await leaderboard.rank(
        session, mode=ranked, user_id=usuario.id, period=Period.WEEK
    )
    return MyRanksOut(global_=_rank(global_), week=_rank(weekly))


@router.get("/{mode}")
async def mode_leaderboard(
    mode: str,
    session: SessionDep,
    period: Period = Period.ALL,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> LeaderboardOut:
    ranked = _ranked_mode(mode)
    filas = await leaderboard.entries(session, mode=ranked, period=period, limit=limit)
    return LeaderboardOut(
        period=period,
        entries=[
            LeaderboardEntry(
                position=posicion,
                nick=fila.nick,
                score=fila.score,
                achieved_at=fila.achieved_at,
            )
            for posicion, fila in enumerate(filas, start=1)
        ],
    )


def _rank(rank: leaderboard.Rank | None) -> RankOut:
    if rank is None:
        return RankOut()
    return RankOut(rank=rank.position, score=rank.score, achieved_at=rank.achieved_at)
