"""Rate limiting por IP en Redis: corta el abuso y degrada si Redis no está (H-09)."""

import httpx
import pytest
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.api import rate_limit


class _RedisCaido:
    async def incr(self, clave: str) -> int:
        raise RedisError("sin redis")


async def test_guest_creation_is_limited_per_ip(
    client: httpx.AsyncClient, redis: Redis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", redis)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_guest_per_minute", 1)

    primera = await client.post("/auth/guest", json={"nick": "ana"})
    segunda = await client.post("/auth/guest", json={"nick": "beto"})

    assert primera.status_code == 201
    assert segunda.status_code == 429
    assert segunda.json()["error"]["code"] == "RATE_LIMITED"


async def test_the_room_preview_is_limited_per_ip(
    client: httpx.AsyncClient, redis: Redis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", redis)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_room_per_minute", 1)

    primera = await client.get("/rooms/ZZZZZZ")
    segunda = await client.get("/rooms/ZZZZZZ")

    assert primera.status_code == 404
    assert segunda.status_code == 429


async def test_without_redis_the_request_goes_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", _RedisCaido())

    await rate_limit.enforce("1.2.3.4", bucket="guest", limit=1)
