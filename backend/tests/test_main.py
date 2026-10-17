"""La raíz de la API y los límites del borde."""

import httpx

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
