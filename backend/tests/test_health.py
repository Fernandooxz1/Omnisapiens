"""`/health`: 200 cuando las dos piezas contestan, 503 cuando falta alguna."""

from fastapi import Response
from redis.exceptions import RedisError

from app.api.routers import health as health_module


class _EngineCaido:
    def connect(self) -> None:
        raise OSError("sin base")


class _RedisCaido:
    async def ping(self) -> None:
        raise RedisError("sin redis")


async def test_health_is_200_when_db_and_redis_answer() -> None:
    respuesta = Response()

    cuerpo = await health_module.health(respuesta)

    assert respuesta.status_code == 200
    assert cuerpo == {"api": "ok", "db": "ok", "redis": "ok"}


async def test_health_is_503_when_the_db_is_down(monkeypatch) -> None:
    monkeypatch.setattr(health_module, "engine", _EngineCaido())
    respuesta = Response()

    cuerpo = await health_module.health(respuesta)

    assert respuesta.status_code == 503
    assert cuerpo["db"] == "error"


async def test_health_is_503_when_redis_is_down(monkeypatch) -> None:
    monkeypatch.setattr(health_module, "redis_client", _RedisCaido())
    respuesta = Response()

    cuerpo = await health_module.health(respuesta)

    assert respuesta.status_code == 503
    assert cuerpo["redis"] == "error"
