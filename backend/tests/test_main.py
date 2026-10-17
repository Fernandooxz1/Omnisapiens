"""La raíz de la API y los límites del borde."""

import asyncio

import httpx
import pytest

from app import main
from app.api.limits import MAX_BODY_BYTES


async def test_the_root_reports_the_name_and_version(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"name": "Omnisapiens API", "version": "0.1"}


async def test_a_body_over_the_limit_is_rejected_before_parsing(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post("/auth/guest", content=b"x" * (MAX_BODY_BYTES + 1))

    assert respuesta.status_code == 413
    assert respuesta.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


async def test_the_reaper_loop_repeats_until_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas = 0

    async def _contar() -> None:
        nonlocal llamadas
        llamadas += 1

    monkeypatch.setattr(main, "_sweep_once", _contar)
    tarea = asyncio.create_task(main._reap_forever(0.01))

    for _ in range(200):
        await asyncio.sleep(0.005)
        if llamadas >= 2:
            break
    tarea.cancel()
    with pytest.raises(asyncio.CancelledError):
        await tarea

    assert llamadas >= 2


async def test_the_reaper_loop_survives_a_failed_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intentos = 0

    async def _falla_una_vez() -> None:
        nonlocal intentos
        intentos += 1
        if intentos == 1:
            raise RuntimeError("la base no contesta")

    monkeypatch.setattr(main, "_sweep_once", _falla_una_vez)
    tarea = asyncio.create_task(main._reap_forever(0.01))

    for _ in range(200):
        await asyncio.sleep(0.005)
        if intentos >= 2:
            break
    tarea.cancel()
    with pytest.raises(asyncio.CancelledError):
        await tarea

    # El error del primero no mató la task: el segundo barrido corrió.
    assert intentos >= 2
