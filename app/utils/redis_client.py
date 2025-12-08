from redis import asyncio as aioredis
from typing import AsyncGenerator

REDIS_URL = "redis://localhost:6379/0" 
redis_client: aioredis.Redis = None  

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield redis_client
    finally:
        pass