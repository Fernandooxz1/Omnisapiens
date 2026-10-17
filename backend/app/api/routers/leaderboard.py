"""El ranking del arcade: la tabla y la posición del jugador.

Es público, como la tabla que se mira al terminar una corrida. `/me` sí pide
token, porque la posición es "la tuya".
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.schemas.leaderboard import (
    LeaderboardEntry,
    LeaderboardOut,
    MyRanksOut,
    RankOut,
)
from app.services import leaderboard
from app.services.leaderboard import Period

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/arcade")
async def arcade_leaderboard(
    session: SessionDep,
    period: Period = Period.ALL,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> LeaderboardOut:
    filas = await leaderboard.entries(session, period=period, limit=limit)
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


@router.get("/arcade/me")
async def my_arcade_ranks(usuario: CurrentUserDep, session: SessionDep) -> MyRanksOut:
    global_ = await leaderboard.rank(session, user_id=usuario.id, period=Period.ALL)
    weekly = await leaderboard.rank(session, user_id=usuario.id, period=Period.WEEK)
    return MyRanksOut(global_=_rank(global_), week=_rank(weekly))


def _rank(rank: leaderboard.Rank | None) -> RankOut:
    if rank is None:
        return RankOut()
    return RankOut(rank=rank.position, score=rank.score, achieved_at=rank.achieved_at)
