import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from redis.asyncio import Redis
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.db import session_scope
from app.models import Job, JobStatus
from app.queue import channel_for

router = APIRouter(tags=["stream"])


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: UUID):
    with session_scope() as s:
        job = s.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        terminal = job.status in (JobStatus.done, JobStatus.failed, JobStatus.cancelled)

    async def event_gen():
        # Snapshot inicial
        with session_scope() as s:
            job = s.get(Job, job_id)
            if job:
                yield {
                    "event": "snapshot",
                    "data": json.dumps(
                        {
                            "status": job.status.value,
                            "progress_pct": job.progress_pct,
                            "duration_seconds": job.duration_seconds,
                            "detected_language": job.detected_language,
                        }
                    ),
                }

        if terminal:
            yield {"event": "done", "data": "{}"}
            return

        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis.pubsub()
        try:
            await pubsub.subscribe(channel_for(str(job_id)))
            while True:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=15.0
                )
                if msg is None:
                    # heartbeat
                    yield {"event": "ping", "data": ""}
                    continue
                data = msg.get("data") or "{}"
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    payload = {"raw": data}
                evt = payload.pop("event", "message")
                yield {"event": evt, "data": json.dumps(payload)}
                if evt in ("done", "failed", "cancelled"):
                    break
        finally:
            await pubsub.unsubscribe(channel_for(str(job_id)))
            await pubsub.aclose()
            await redis.aclose()

    return EventSourceResponse(event_gen())
