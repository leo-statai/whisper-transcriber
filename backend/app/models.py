from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    filename: str
    upload_id: str | None = Field(default=None, index=True)
    file_path: str | None = None
    size_bytes: int = 0
    duration_seconds: float | None = None
    status: JobStatus = Field(default=JobStatus.queued, index=True)
    progress_pct: float = 0.0
    language: str | None = None
    detected_language: str | None = None
    model: str = "large-v3"
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now, index=True)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    segments: list["Segment"] = Relationship(
        back_populates="job",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Segment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: UUID = Field(foreign_key="job.id", index=True)
    idx: int
    start: float
    end: float
    text: str
    avg_logprob: float | None = None

    job: Job | None = Relationship(back_populates="segments")
