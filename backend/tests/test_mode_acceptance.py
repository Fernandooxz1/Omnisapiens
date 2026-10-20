"""El criterio de terminado del refactor: un modo nuevo no toca código compartido.

El modo de prueba es un duplicado del arcade con otro `code`: reusa el
`ContentKind` de quiz, las reglas y la progresión, y solo se suma a la entrada
del registro. Si el borde necesitara una rama por modo, este test no pasaría.
"""

from dataclasses import replace
from typing import Any

import pytest
from sqlalchemy import select

from app.game.modes import TRIVIA_ARCADE, registry
from app.models import ContentItem, GameSession

from . import ws_fixtures
from .factories import quiz_content

session_api = ws_fixtures.session_api
session_connect = ws_fixtures.session_connect

PROBE = "trivia_quiz_probe"


@pytest.fixture
def probe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un quiz duplicado en el registro, sin tocar los modos de producción.

    `monkeypatch.setitem` deshace el alta al terminar: el catálogo del proceso
    vuelve a tener exactamente los dos modos reales.
    """
    monkeypatch.setitem(
        registry._modes,
        PROBE,
        replace(TRIVIA_ARCADE, code=PROBE, name="Quiz de prueba"),
    )


async def sembrar(api: Any) -> list[ContentItem]:
    pares = [
        quiz_content(
            category="geography",
            difficulty=1,
            status="published",
            prompt=f"pregunta {indice}",
            options=["correcta", "a", "b", "c"],
            correct_index=0,
        )
        for indice in range(3)
    ]
    api.session.add_all([fila for par in pares for fila in par])
    await api.session.flush()
    return [item for item, _ in pares]


async def test_a_new_mode_plays_through_the_generic_session(
    session_api: Any, session_connect: Any, probe_mode: None
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create(mode=PROBE)

    catalogo = (await session_api.http.get("/modes")).json()
    assert PROBE in [modo["code"] for modo in catalogo]

    async with session_connect(session_id) as socket:
        inicio = await socket.until("session_start")
        assert inicio["d"]["mode"] == PROBE
        assert inicio["d"]["lives"] == 3

        item = await socket.until("item_start")
        assert item["d"]["payload"]["prompt"]
        opciones = item["d"]["payload"]["options"]
        await socket.send(
            {"t": "answer", "d": {"round": 0, "choice": opciones.index("correcta")}}
        )
        resultado = await socket.until("item_result")
        assert resultado["d"]["correct"] is True
        assert resultado["d"]["points"] > 0

        siguiente = await socket.until("item_start")
        assert siguiente["d"]["position"] == 1

    fila = await session_api.session.scalar(
        select(GameSession).where(GameSession.id == session_id)
    )
    assert fila is not None
    assert fila.mode == PROBE
    assert fila.content_kind == "quiz"
