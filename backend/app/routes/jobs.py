from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import Job, JobStatus, Segment
from app.queue import cancel_key, get_arq_pool

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobOut(BaseModel):
    id: UUID
    filename: str
    size_bytes: int
    status: JobStatus
    progress_pct: float
    language: str | None
    detected_language: str | None
    model: str
    duration_seconds: float | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class SegmentOut(BaseModel):
    idx: int
    start: float
    end: float
    text: str


class JobDetail(JobOut):
    segments: list[SegmentOut]


@router.get("", response_model=list[JobOut])
def list_jobs(session: Session = Depends(get_session)) -> list[JobOut]:
    rows = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    return [JobOut.model_validate(j, from_attributes=True) for j in rows]


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: UUID, session: Session = Depends(get_session)) -> JobDetail:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    segments = session.exec(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.idx)
    ).all()
    data = JobOut.model_validate(job, from_attributes=True).model_dump()
    data["segments"] = [
        SegmentOut(idx=s.idx, start=s.start, end=s.end, text=s.text) for s in segments
    ]
    return JobDetail(**data)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: UUID, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    if job.status not in (JobStatus.queued, JobStatus.processing):
        raise HTTPException(409, f"Job em estado {job.status.value}")
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis.set(cancel_key(str(job_id)), "1", ex=3600)
    finally:
        await redis.aclose()
    return {"ok": True}


@router.delete("/{job_id}")
def delete_job(job_id: UUID, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    if job.status in (JobStatus.queued, JobStatus.processing):
        raise HTTPException(409, "Cancele antes de excluir")
    if job.file_path:
        try:
            from pathlib import Path
            p = Path(job.file_path)
            if p.exists():
                p.unlink()
        except OSError:
            pass
    session.delete(job)
    return {"ok": True}


class CreateJobIn(BaseModel):
    filename: str
    upload_id: str
    file_path: str
    size_bytes: int = 0
    language: str | None = None
    model: str | None = None


@router.post("", response_model=JobOut)
async def create_job(payload: CreateJobIn, session: Session = Depends(get_session)) -> JobOut:
    job = Job(
        filename=payload.filename,
        upload_id=payload.upload_id,
        file_path=payload.file_path,
        size_bytes=payload.size_bytes,
        language=payload.language or None,
        model=payload.model or settings.WHISPER_MODEL,
    )
    session.add(job)
    session.flush()
    session.refresh(job)

    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("transcribe_job", str(job.id))
    finally:
        await pool.aclose()
    return JobOut.model_validate(job, from_attributes=True)
