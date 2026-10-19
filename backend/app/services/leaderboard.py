"""El ranking por modo: el mejor puntaje de cada jugador, en Postgres.

Solo compiten sesiones `finished` con `owner_user_id` (o sea, modos solo): el
versus no tiene dueño y queda afuera. Los dos índices parciales de
`game_sessions` (`(mode, score DESC, ended_at)` y `(mode, owner_user_id,
score DESC)`) existen justamente para estas consultas.

Una consulta por lista y otra por posición, las dos con `DISTINCT ON` para
quedarse con la mejor sesión de cada jugador. El desempate (§4.3) es el
`ended_at` de esa mejor sesión: quien alcanzó ese puntaje primero va primero.

`run_summary` sigue leyendo `arcade_runs` mientras el arcade en vivo no escriba
sesiones genéricas: es el único consumidor del camino viejo y lo reemplaza la
tarea 4.2.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from app.game.arcade_engine import RunStatus
from app.models import ArcadeRun, GameSession, User

# La semana del ranking corta el lunes a las 00:00 de Buenos Aires (2026-10-17).
RANKING_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")

# Hasta la fase 6 (registro de modos) la lista vive acá; después sale de
# `GameMode.ranking`.
RANKED_MODES = {"trivia_arcade"}


class Period(StrEnum):
    ALL = "all"
    WEEK = "week"


@dataclass(frozen=True)
class Entry:
    user_id: uuid.UUID
    nick: str
    score: int
    achieved_at: datetime


@dataclass(frozen=True)
class Rank:
    position: int
    score: int
    achieved_at: datetime


@dataclass(frozen=True)
class RunSummary:
    """Lo que completa el `arcade_end`. Nada es obligatorio: sin ranking, `None`."""

    rank_global: int | None
    rank_weekly: int | None
    personal_best: int | None
    is_new_best: bool


def week_start(now: datetime | None = None) -> datetime:
    """El lunes 00:00 de la semana que contiene `now`, en horario argentino."""
    local = (now or datetime.now(UTC)).astimezone(RANKING_TIMEZONE)
    monday = local.date() - timedelta(days=local.weekday())
    return datetime.combine(monday, time.min, tzinfo=RANKING_TIMEZONE)


def _since(period: Period, now: datetime | None) -> datetime | None:
    return week_start(now) if period is Period.WEEK else None


def _best_sessions(mode: str, since: datetime | None) -> Subquery:
    """La mejor sesión de cada jugador; con el mismo puntaje, la más temprana.

    `DISTINCT ON (users.id)` obliga a que el `ORDER BY` arranque por esa columna;
    después el puntaje y la fecha son los que eligen *qué* fila se queda.
    """
    conditions = [
        GameSession.mode == mode,
        GameSession.status == "finished",
        GameSession.owner_user_id.is_not(None),
        GameSession.ended_at.is_not(None),
        User.deleted_at.is_(None),
    ]
    if since is not None:
        conditions.append(GameSession.ended_at >= since)
    return (
        select(
            User.id.label("user_id"),
            User.nick,
            GameSession.score,
            GameSession.ended_at.label("achieved_at"),
        )
        .join(GameSession, GameSession.owner_user_id == User.id)
        .where(*conditions)
        .ext(distinct_on(User.id))
        .order_by(User.id, GameSession.score.desc(), GameSession.ended_at.asc())
        .subquery()
    )


async def entries(
    session: AsyncSession,
    *,
    mode: str,
    period: Period = Period.ALL,
    limit: int = 50,
    now: datetime | None = None,
) -> list[Entry]:
    """La tabla del ranking de un modo, de mejor a peor."""
    best = _best_sessions(mode, _since(period, now))
    filas = await session.execute(
        select(best.c.user_id, best.c.nick, best.c.score, best.c.achieved_at)
        # `user_id` desempata el caso raro de puntaje y fecha idénticos: así la
        # posición no baila entre dos pedidos.
        .order_by(best.c.score.desc(), best.c.achieved_at.asc(), best.c.user_id.asc())
        .limit(limit)
    )
    return [
        Entry(
            user_id=user_id,
            nick=nick,
            score=score,
            achieved_at=achieved_at,
        )
        for user_id, nick, score, achieved_at in filas
    ]


async def rank(
    session: AsyncSession,
    *,
    mode: str,
    user_id: uuid.UUID,
    period: Period = Period.ALL,
    now: datetime | None = None,
) -> Rank | None:
    """La posición del jugador, o `None` si todavía no tiene sesiones válidas."""
    best = _best_sessions(mode, _since(period, now))
    ranked = select(
        best.c.user_id,
        best.c.score,
        best.c.achieved_at,
        func.row_number()
        .over(
            order_by=(
                best.c.score.desc(),
                best.c.achieved_at.asc(),
                best.c.user_id.asc(),
            )
        )
        .label("position"),
    ).subquery()
    fila = (
        await session.execute(
            select(ranked.c.position, ranked.c.score, ranked.c.achieved_at).where(
                ranked.c.user_id == user_id
            )
        )
    ).one_or_none()
    if fila is None:
        return None
    return Rank(position=fila.position, score=fila.score, achieved_at=fila.achieved_at)


def _legacy_best_runs(since: datetime | None) -> Subquery:
    """La mejor corrida de cada jugador en `arcade_runs` (camino viejo, hasta 4.2)."""
    conditions = [
        ArcadeRun.status == RunStatus.FINISHED.value,
        User.deleted_at.is_(None),
    ]
    if since is not None:
        conditions.append(ArcadeRun.ended_at >= since)
    return (
        select(
            User.id.label("user_id"),
            User.nick,
            ArcadeRun.score,
            ArcadeRun.ended_at.label("achieved_at"),
        )
        .join(ArcadeRun, ArcadeRun.user_id == User.id)
        .where(*conditions)
        .ext(distinct_on(User.id))
        .order_by(User.id, ArcadeRun.score.desc(), ArcadeRun.ended_at.asc())
        .subquery()
    )


async def _legacy_rank(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    period: Period = Period.ALL,
    now: datetime | None = None,
) -> Rank | None:
    """La posición del jugador en `arcade_runs`, mientras el arcade siga ahí."""
    best = _legacy_best_runs(_since(period, now))
    ranked = select(
        best.c.user_id,
        best.c.score,
        best.c.achieved_at,
        func.row_number()
        .over(
            order_by=(
                best.c.score.desc(),
                best.c.achieved_at.asc(),
                best.c.user_id.asc(),
            )
        )
        .label("position"),
    ).subquery()
    fila = (
        await session.execute(
            select(ranked.c.position, ranked.c.score, ranked.c.achieved_at).where(
                ranked.c.user_id == user_id
            )
        )
    ).one_or_none()
    if fila is None:
        return None
    return Rank(position=fila.position, score=fila.score, achieved_at=fila.achieved_at)


async def run_summary(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
    score: int,
    now: datetime | None = None,
) -> RunSummary:
    """Las posiciones y la mejor marca para el `arcade_end`.

    La corrida ya está cerrada y commiteada: el ranking la ve. La mejor marca
    anterior se mira sin la corrida actual para poder distinguir "nuevo récord"
    de "empaté mi récord".

    Sigue sobre `arcade_runs` porque el arcade en vivo todavía escribe ahí; la
    tarea 4.2 lo cambia a `game_sessions` junto con el resto del port.
    """
    previous = await session.scalar(
        select(func.max(ArcadeRun.score)).where(
            ArcadeRun.user_id == user_id,
            ArcadeRun.status == RunStatus.FINISHED.value,
            ArcadeRun.id != run_id,
        )
    )
    global_ = await _legacy_rank(session, user_id=user_id, period=Period.ALL, now=now)
    weekly = await _legacy_rank(session, user_id=user_id, period=Period.WEEK, now=now)
    return RunSummary(
        rank_global=global_.position if global_ is not None else None,
        rank_weekly=weekly.position if weekly is not None else None,
        personal_best=max(score, previous or 0),
        is_new_best=previous is None or score > previous,
    )
