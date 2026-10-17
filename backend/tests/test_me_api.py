"""`/me` contra la API real y la base real del test."""

import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ArcadeRun, Match, User
from app.security.tokens import create_guest_token, read_guest_token
from app.services.leaderboard import week_start

from .factories import arcade_run, match, user


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _as(usuario: User) -> dict[str, str]:
    return _auth(create_guest_token(usuario.id, usuario.nick))


async def _jugador(session: AsyncSession, nick: str, **overrides: object) -> User:
    fila = user(nick=nick, **overrides)
    session.add(fila)
    await session.flush()
    return fila


def _finished(
    usuario: User, *, score: int, ended_at: datetime, status: str = "finished"
) -> ArcadeRun:
    return arcade_run(
        usuario.id,
        score=score,
        correct_count=5,
        longest_streak=3,
        status=status,
        started_at=ended_at - timedelta(minutes=1),
        ended_at=ended_at,
    )


def _duel(
    a: User,
    b: User,
    *,
    ended_at: datetime,
    score_a: int,
    score_b: int,
    winner: User | None,
    status: str = "finished",
) -> Match:
    return match(
        a.id,
        b.id,
        status=status,
        score_a=score_a,
        score_b=score_b,
        winner_id=None if winner is None else winner.id,
        started_at=ended_at - timedelta(minutes=5),
        ended_at=ended_at,
    )


async def _guest(client: httpx.AsyncClient, nick: str | None = None) -> dict:
    cuerpo = {} if nick is None else {"nick": nick}
    return (await client.post("/auth/guest", json=cuerpo)).json()


async def test_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.get("/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_the_token_identifies_the_user(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.get("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == alta["user"]["id"]
    assert respuesta.json()["nick"] == "ana"


async def test_reading_the_profile_refreshes_last_seen(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    usuario.last_seen_at = datetime.now(UTC) - timedelta(minutes=5)
    await session.flush()
    antes = usuario.last_seen_at

    await client.get("/me", headers=_auth(alta["token"]))
    await session.refresh(usuario)

    assert usuario.last_seen_at > antes


async def test_a_recent_read_does_not_write_again(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    usuario.last_seen_at = datetime.now(UTC) - timedelta(seconds=10)
    await session.flush()
    antes = usuario.last_seen_at

    await client.get("/me", headers=_auth(alta["token"]))
    await session.refresh(usuario)

    assert usuario.last_seen_at == antes


async def test_patch_changes_the_nick(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "  ana  maría "}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["nick"] == "ana maría"
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    assert usuario.nick == "ana maría"


async def test_patch_returns_a_token_that_carries_the_new_nick(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "beto"}, headers=_auth(alta["token"])
    )

    assert read_guest_token(respuesta.json()["token"]).nick == "beto"


async def test_patch_rejects_a_nick_already_in_use(client: httpx.AsyncClient) -> None:
    await _guest(client, "ana")
    beto = await _guest(client, "beto")

    respuesta = await client.patch(
        "/me", json={"nick": "ana"}, headers=_auth(beto["token"])
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "NICK_TAKEN"


async def test_patch_rejects_a_nick_that_only_differs_in_case(
    client: httpx.AsyncClient,
) -> None:
    await _guest(client, "Ana")
    beto = await _guest(client, "beto")

    respuesta = await client.patch(
        "/me", json={"nick": "ANA"}, headers=_auth(beto["token"])
    )

    assert respuesta.status_code == 409


async def test_patch_rejects_a_forbidden_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "puto"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_FORBIDDEN"


async def test_patch_rejects_a_nick_that_is_too_long(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "a" * 17}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_LENGTH"


async def test_patch_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.patch("/me", json={"nick": "ana"})

    assert respuesta.status_code == 401


async def test_patch_can_keep_the_same_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "ana"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 200


async def test_delete_marks_the_user_as_deleted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.delete("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 204
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    assert usuario.deleted_at is not None


async def test_after_delete_the_token_is_no_longer_valid(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")
    await client.delete("/me", headers=_auth(alta["token"]))

    respuesta = await client.get("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 401


async def test_delete_frees_the_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")
    await client.delete("/me", headers=_auth(alta["token"]))

    respuesta = await client.post("/auth/guest", json={"nick": "ana"})

    assert respuesta.status_code == 201


async def test_delete_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.delete("/me")

    assert respuesta.status_code == 401


async def test_without_runs_the_marks_and_history_are_empty(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")

    cuerpo = (await client.get("/me", headers=_auth(alta["token"]))).json()

    assert cuerpo["best"] == {"all_time": None, "week": None}
    assert cuerpo["arcade_runs"] == []
    assert cuerpo["matches"] == []


async def test_best_marks_are_the_maximum_of_all_time_and_this_week(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    ahora = datetime.now(UTC)
    lunes = week_start(ahora)
    session.add_all(
        [
            # La mejor de siempre es de la semana pasada: no cuenta para `week`.
            _finished(ana, score=900, ended_at=lunes - timedelta(seconds=1)),
            _finished(ana, score=400, ended_at=lunes),
            _finished(ana, score=700, ended_at=ahora),
            # Ni una en curso ni una invalidada son marcas.
            arcade_run(ana.id, score=9_999, started_at=ahora),
            _finished(ana, score=8_888, ended_at=ahora, status="invalid"),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/me", headers=_as(ana))).json()

    assert cuerpo["best"] == {"all_time": 900, "week": 700}


async def test_arcade_history_is_the_latest_ten_finished_runs_of_the_player(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    ahora = datetime.now(UTC)
    session.add_all(
        [
            _finished(ana, score=100 + i, ended_at=ahora - timedelta(minutes=i))
            for i in range(12)
        ]
    )
    session.add_all(
        [
            _finished(ana, score=9_000, ended_at=ahora, status="invalid"),
            arcade_run(ana.id, score=9_001, started_at=ahora),
            _finished(beto, score=9_002, ended_at=ahora),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/me", headers=_as(ana))).json()

    # Las diez más nuevas, de la más reciente a la más vieja, y sin lo ajeno.
    assert [corrida["score"] for corrida in cuerpo["arcade_runs"]] == [
        100 + i for i in range(10)
    ]
    primera = cuerpo["arcade_runs"][0]
    assert (
        primera["score"],
        primera["correct_count"],
        primera["longest_streak"],
        primera["max_difficulty"],
    ) == (100, 5, 3, 1)


async def test_match_history_shows_the_rival_and_the_result_from_my_side(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _jugador(session, "ana")
    beto = await _jugador(session, "beto")
    caro = await _jugador(session, "caro")
    ahora = datetime.now(UTC)
    session.add_all(
        [
            _duel(
                ana,
                beto,
                ended_at=ahora - timedelta(hours=1),
                score_a=700,
                score_b=500,
                winner=ana,
            ),
            # Ana es la jugadora B: el `CASE` tiene que dar vuelta los puntajes.
            _duel(
                beto,
                ana,
                ended_at=ahora,
                score_a=300,
                score_b=600,
                winner=ana,
            ),
            # Terminada sin ganador: empate.
            _duel(
                caro,
                ana,
                ended_at=ahora - timedelta(hours=2),
                score_a=450,
                score_b=450,
                winner=None,
            ),
            # Abandonada y una ajena: las dos quedan afuera.
            _duel(
                ana,
                beto,
                ended_at=ahora - timedelta(hours=3),
                score_a=100,
                score_b=100,
                winner=None,
                status="abandoned",
            ),
            _duel(
                beto,
                caro,
                ended_at=ahora - timedelta(hours=4),
                score_a=800,
                score_b=200,
                winner=beto,
            ),
        ]
    )
    await session.flush()

    cuerpo = (await client.get("/me", headers=_as(ana))).json()

    assert [
        (
            partida["opponent_nick"],
            partida["my_score"],
            partida["opponent_score"],
            partida["result"],
        )
        for partida in cuerpo["matches"]
    ] == [
        ("beto", 600, 300, "win"),
        ("beto", 700, 500, "win"),
        ("caro", 450, 450, "draw"),
    ]
