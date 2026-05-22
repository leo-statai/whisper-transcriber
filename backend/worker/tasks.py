from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from uuid import UUID

from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.config import settings
from app.db import init_db, session_scope
from app.models import Job, JobStatus, Segment, utc_now
from app.queue import cancel_key, channel_for


CANCELLED = "__cancelled__"


async def _publish(redis: Redis, channel: str, payload: dict) -> None:
    await redis.publish(channel, json.dumps(payload))


def _extract_audio(src: Path, dst: Path) -> None:
    """ffmpeg: extrai/normaliza para WAV mono 16 kHz s16le."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(src),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        "-loglevel", "error",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg falhou ({proc.returncode}): {proc.stderr.decode(errors='replace')[:400]}"
        )


def _probe_duration(src: Path) -> float | None:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(src),
    ]
    try:
        out = subprocess.check_output(cmd).decode().strip()
        return float(out)
    except Exception:
        return None


async def transcribe_job(ctx: dict, job_id: str) -> str:
    """Job ARQ que transcreve um arquivo. Roda no container worker (GPU)."""
    from faster_whisper import WhisperModel

    redis: Redis = ctx["redis_pub"]
    model: WhisperModel = ctx["model"]

    channel = channel_for(job_id)
    job_uuid = UUID(job_id)

    with session_scope() as s:
        job = s.get(Job, job_uuid)
        if not job:
            return "missing"
        if not job.file_path:
            job.status = JobStatus.failed
            job.error = "Arquivo não encontrado"
            return "no-file"
        src_path = Path(job.file_path)
        job.status = JobStatus.processing
        job.started_at = utc_now()
        chosen_model = job.model or settings.WHISPER_MODEL
        chosen_language = (job.language or settings.WHISPER_LANGUAGE) or None
        s.add(job)

    await _publish(redis, channel, {"event": "status", "status": "processing"})

    audio_path = src_path.with_suffix(".16k.wav")
    try:
        await asyncio.to_thread(_extract_audio, src_path, audio_path)

        duration = await asyncio.to_thread(_probe_duration, audio_path)
        if duration:
            with session_scope() as s:
                job = s.get(Job, job_uuid)
                if job:
                    job.duration_seconds = duration
                    s.add(job)
            await _publish(redis, channel, {"event": "duration", "seconds": duration})

        def _run_transcription():
            return model.transcribe(
                str(audio_path),
                language=chosen_language,
                vad_filter=settings.WHISPER_VAD_FILTER,
                beam_size=settings.WHISPER_BEAM_SIZE,
            )

        segments_iter, info = await asyncio.to_thread(_run_transcription)

        with session_scope() as s:
            job = s.get(Job, job_uuid)
            if job:
                job.detected_language = info.language
                s.add(job)
        await _publish(
            redis,
            channel,
            {"event": "language", "language": info.language, "probability": info.language_probability},
        )

        idx = 0
        last_pct = -1.0
        for seg in segments_iter:
            # Cancelamento cooperativo
            if await redis.get(cancel_key(job_id)):
                with session_scope() as s:
                    job = s.get(Job, job_uuid)
                    if job:
                        job.status = JobStatus.cancelled
                        job.finished_at = utc_now()
                        s.add(job)
                await _publish(redis, channel, {"event": "cancelled"})
                await redis.delete(cancel_key(job_id))
                return CANCELLED

            with session_scope() as s:
                s.add(
                    Segment(
                        job_id=job_uuid,
                        idx=idx,
                        start=float(seg.start),
                        end=float(seg.end),
                        text=seg.text.strip(),
                        avg_logprob=float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                    )
                )

            await _publish(
                redis,
                channel,
                {
                    "event": "segment",
                    "idx": idx,
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "text": seg.text.strip(),
                },
            )

            if duration:
                pct = min(100.0, (float(seg.end) / duration) * 100.0)
                if pct - last_pct >= 1.0:
                    last_pct = pct
                    with session_scope() as s:
                        job = s.get(Job, job_uuid)
                        if job:
                            job.progress_pct = pct
                            s.add(job)
                    await _publish(redis, channel, {"event": "progress", "pct": pct})

            idx += 1

        with session_scope() as s:
            job = s.get(Job, job_uuid)
            if job:
                job.status = JobStatus.done
                job.progress_pct = 100.0
                job.finished_at = utc_now()
                s.add(job)
        await _publish(redis, channel, {"event": "done"})
        return "done"

    except Exception as exc:
        with session_scope() as s:
            job = s.get(Job, job_uuid)
            if job:
                job.status = JobStatus.failed
                job.error = str(exc)[:500]
                job.finished_at = utc_now()
                s.add(job)
        await _publish(redis, channel, {"event": "failed", "error": str(exc)[:500]})
        raise

    finally:
        try:
            if audio_path.exists():
                audio_path.unlink()
        except OSError:
            pass


async def startup(ctx: dict) -> None:
    from faster_whisper import WhisperModel

    init_db()

    device = "cuda"
    compute_type = settings.WHISPER_COMPUTE_TYPE
    model_name = settings.WHISPER_MODEL

    print(f"[worker] Carregando modelo {model_name} ({device}, {compute_type})…")
    ctx["model"] = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        download_root=str(settings.MODELS_DIR),
    )
    ctx["redis_pub"] = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    print("[worker] Modelo pronto.")


async def shutdown(ctx: dict) -> None:
    redis = ctx.get("redis_pub")
    if redis:
        await redis.aclose()


class WorkerSettings:
    functions = [transcribe_job]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = settings.WORKER_CONCURRENCY
    job_timeout = 60 * 60 * 24  # 24 h
    keep_result = 60 * 60
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
