"""El ranking HTTP contra la API y la base reales.

Se siembran sesiones `finished` con `started_at`/`ended_at` explícitos: la base
exige que el cierre no sea anterior al arranque, y acá el tiempo es dato del
test, no el reloj real. El ranking solo mira sesiones con dueño (modos solo).
"""

from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GameSession, User
from app.security.tokens import create_guest_token
from app.services.leaderboard import week_start

from .factories import game_session, user


def _auth(usuario: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_guest_token(usuario.id, usuario.nick)}"}


def _finished(
    usuario: User,
    *,
    score: int,
    ended_at: datetime,
    mode: str = "trivia_arcade",
    status: str = "finished",
    owner: bool = True,
) -> GameSession:
    return game_session(
        mode=mode,
        play_format="versus" if mode == "trivia_versus" else "arcade",
        status=status,
        owner_user_id=usuario.id if owner else None,
        score=score,
        started_at=ended_at - timedelta(minutes=1),
        ended_at=ended_at,
    )


async def _jugador(session: AsyncSession, nick: str, **overrides: object) -> User:
    fila = user(nick=nick, **overrides)
    session.add(fila)
    await session.flush()
    return fila


async def test_the_global_leaderboard_orders_by_best_score(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro")
    ahora = datetime.now(UTC)

    session.add_all(
        [
            _finished(ana, score=300, ended_at=ahora - timedelta(hours=3)),
            _finished(ana, score=900, ended_at=ahora - timedelta(hours=2)),
            _finished(beto, score=500, ended_at=ahora - timedelta(hours=4)),
            _finished(caro, score=100, ended_at=ahora - timedelta(hours=5)),
            _finished(caro, score=400, ended_at=ahora - timedelta(hours=1)),
        ]
    )
    await session.flush()

    respuesta = await client.get("/leaderboard/trivia_arcade")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["period"] == "all"
    assert [
        (fila["position"], fila["nick"], fila["score"]) for fila in cuerpo["entries"]
    ] == [
        (1, "ana", 900),
        (2, "beto", 500),
        (3, "caro", 400),
    ]


async def test_a_tie_goes_to_who_reached_the_score_first(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro")
    ahora = datetime.now(UTC)

    session.add_all(
        [
            # Ana llegó a 500 antes que Beto; el 400 posterior de Ana no cuenta.
            _finished(ana, score=500, ended_at=ahora - timedelta(hours=5)),
            _finished(ana, score=400, ended_at=ahora - timedelta(hours=4)),
            _finished(beto, score=500, ended_at=ahora - timedelta(hours=3)),
            _finished(caro, score=600, ended_at=ahora - timedelta(hours=2)),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/leaderboard/trivia_arcade")).json()

    assert [fila["nick"] for fila in cuerpo["entries"]] == ["caro", "ana", "beto"]
    assert [fila["score"] for fila in cuerpo["entries"]] == [600, 500, 500]


async def test_the_weekly_leaderboard_only_counts_sessions_since_monday(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro")
    lunes = week_start(datetime.now(UTC))

    session.add_all(
        [
            # Domingo 23:59:59 local: todavía es la semana pasada.
            _finished(ana, score=900, ended_at=lunes - timedelta(seconds=1)),
            _finished(ana, score=300, ended_at=lunes + timedelta(hours=1)),
            _finished(beto, score=500, ended_at=lunes - timedelta(hours=1)),
            _finished(caro, score=400, ended_at=lunes + timedelta(hours=2)),
        ]
    )
    await session.flush()

    global_ = (await client.get("/leaderboard/trivia_arcade?period=all")).json()
    semanal = (await client.get("/leaderboard/trivia_arcade?period=week")).json()

    assert [(f["nick"], f["score"]) for f in global_["entries"]] == [
        ("ana", 900),
        ("beto", 500),
        ("caro", 400),
    ]
    assert semanal["period"] == "week"
    assert [(f["nick"], f["score"]) for f in semanal["entries"]] == [
        ("caro", 400),
        ("ana", 300),
    ]


async def test_only_finished_solo_sessions_of_live_users_are_ranked(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro", deleted_at=datetime.now(UTC))
    dani = await _jugador(session, "dani")
    ahora = datetime.now(UTC)

    session.add_all(
        [
            _finished(ana, score=500, ended_at=ahora),
            # Una sesión marcada como tramposa no entra al ranking.
            _finished(beto, score=900, ended_at=ahora, status="invalid"),
            # El borrado lógico saca al jugador de la tabla...
            _finished(caro, score=900, ended_at=ahora),
            # ...una sesión en curso tampoco es una marca...
            game_session(
                owner_user_id=dani.id,
                score=900,
                started_at=ahora,
            ),
            # ...y sin dueño (versus) no hay a quién rankear.
            _finished(dani, score=900, ended_at=ahora, owner=False),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/leaderboard/trivia_arcade")).json()

    assert [(f["nick"], f["score"]) for f in cuerpo["entries"]] == [("ana", 500)]


async def test_the_limit_caps_the_table(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro")
    ahora = datetime.now(UTC)
    session.add_all(
        [
            _finished(ana, score=900, ended_at=ahora),
            _finished(beto, score=800, ended_at=ahora),
            _finished(caro, score=700, ended_at=ahora),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/leaderboard/trivia_arcade?limit=2")).json()

    assert [f["nick"] for f in cuerpo["entries"]] == ["ana", "beto"]


async def test_a_bad_period_or_limit_is_a_validation_error(
    client: httpx.AsyncClient,
) -> None:
    for consulta in ("period=month", "limit=0", "limit=101"):
        respuesta = await client.get(f"/leaderboard/trivia_arcade?{consulta}")
        assert respuesta.status_code == 422, consulta
        assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_mode_without_ranking_is_a_404(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    ahora = datetime.now(UTC)
    session.add(
        _finished(
            ana,
            score=900,
            ended_at=ahora,
            mode="trivia_versus",
        )
    )
    await session.flush()

    for ruta in ("/leaderboard/trivia_versus", "/leaderboard/rosco_solo"):
        respuesta = await client.get(ruta)
        assert respuesta.status_code == 404, ruta
        assert respuesta.json()["error"]["code"] == "MODE_WITHOUT_RANKING"

    propia = await client.get("/leaderboard/trivia_versus/me", headers=_auth(ana))
    assert propia.status_code == 404
    assert propia.json()["error"]["code"] == "MODE_WITHOUT_RANKING"


async def test_arcade_is_an_alias_of_trivia_arcade(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    ahora = datetime.now(UTC)
    session.add(_finished(ana, score=900, ended_at=ahora))
    await session.flush()

    alias = await client.get("/leaderboard/arcade")
    canonico = await client.get("/leaderboard/trivia_arcade")

    assert alias.status_code == 200
    assert alias.json() == canonico.json()


async def test_my_ranks_returns_the_position_in_both_periods(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    ahora = datetime.now(UTC)
    session.add_all(
        [
            _finished(ana, score=900, ended_at=ahora),
            _finished(beto, score=500, ended_at=ahora),
        ]
    )
    await session.flush()

    respuesta = await client.get("/leaderboard/trivia_arcade/me", headers=_auth(ana))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["global"]["rank"] == 1
    assert cuerpo["global"]["score"] == 900
    assert cuerpo["week"]["rank"] == 1
    assert cuerpo["week"]["score"] == 900


async def test_my_ranks_without_sessions_is_empty_in_both_periods(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")

    cuerpo = (
        await client.get("/leaderboard/trivia_arcade/me", headers=_auth(ana))
    ).json()

    assert cuerpo["global"] == {"rank": None, "score": None, "achieved_at": None}
    assert cuerpo["week"] == {"rank": None, "score": None, "achieved_at": None}


async def test_my_ranks_requires_a_token(client: httpx.AsyncClient) -> None:
    respuesta = await client.get("/leaderboard/trivia_arcade/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTH_REQUIRED"
