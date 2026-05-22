from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.REDIS_URL)


async def get_arq_pool():
    return await create_pool(_redis_settings())


def channel_for(job_id) -> str:
    return f"job:{job_id}:events"


def cancel_key(job_id) -> str:
    return f"job:{job_id}:cancel"
