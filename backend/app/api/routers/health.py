from fastapi import APIRouter
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    db_status = "ok"
    redis_status = "ok"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
    except (OSError, SQLAlchemyError):
        db_status = "error"

    try:
        await redis_client.ping()
    except (OSError, RedisError):
        redis_status = "error"

    return {"api": "ok", "db": db_status, "redis": redis_status}
