from redis import asyncio as aioredis
from typing import AsyncGenerator
from app.config import settings

redis_client: aioredis.Redis = None  

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield redis_client
    finally:
        pass

async def check_redis_health() -> bool:
    """Health check for Redis connectivity"""
    try:
        if redis_client is None:
            temp_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        else:
            temp_client = redis_client
        
        await temp_client.ping()
        return True
    except Exception:
        return False
