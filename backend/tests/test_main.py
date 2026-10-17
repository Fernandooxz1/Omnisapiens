"""La raíz de la API: una respuesta de verdad, no un texto de prueba (H-18)."""

import httpx


async def test_the_root_reports_the_name_and_version(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"name": "Omnisapiens API", "version": "0.1"}
