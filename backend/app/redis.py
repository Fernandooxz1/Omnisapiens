import redis.asyncio as redis

from app.config import settings

# decode_responses: sin esto las claves y valores vuelven como bytes.
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
