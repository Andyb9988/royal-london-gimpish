import json

from redis.asyncio import Redis

from app.core.config import settings


async def enqueue_job(job_id: str, job_type: str, *, queue: str = "jobs") -> None:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        payload = json.dumps({"job_id": job_id, "job_type": job_type})
        await redis.rpush(queue, payload)
    finally:
        await redis.aclose()


__all__ = ["enqueue_job"]
