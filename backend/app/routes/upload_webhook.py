from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.config import settings
from app.db import session_scope
from app.models import Job
from app.queue import get_arq_pool

router = APIRouter(tags=["tus"])


class TusdEvent(BaseModel):
    """Subconjunto do payload do tusd que nos interessa."""
    Type: str | None = None
    Event: dict | None = None


@router.post("/tus/hook")
async def tus_hook(req: Request, hook_name: str | None = Header(default=None)):
    """Recebe o evento post-finish do tusd e enfileira um Job."""
    body = await req.json()
    event_type = hook_name or body.get("Type") or ""
    if event_type and event_type != "post-finish":
        return {"ignored": True, "type": event_type}

    upload = (body.get("Event") or {}).get("Upload") or {}
    upload_id = upload.get("ID")
    storage = upload.get("Storage") or {}
    file_path = storage.get("Path")
    size_bytes = int(upload.get("Size") or 0)
    meta = upload.get("MetaData") or {}
    filename = meta.get("filename") or meta.get("name") or (upload_id or "upload")
    language = meta.get("language") or None

    if not upload_id or not file_path:
        raise HTTPException(400, "Payload tus inválido")

    # tusd escreve no disco; o backend monta o mesmo volume em /data/uploads.
    # Path vem como /srv/tusd-data/<id>.bin — converter para nosso mount.
    storage_path = Path(file_path)
    local_path = settings.UPLOAD_DIR / storage_path.name

    with session_scope() as s:
        job = Job(
            filename=filename,
            upload_id=upload_id,
            file_path=str(local_path),
            size_bytes=size_bytes,
            language=language,
            model=settings.WHISPER_MODEL,
        )
        s.add(job)
        s.flush()
        s.refresh(job)
        job_id = str(job.id)

    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("transcribe_job", job_id)
    finally:
        await pool.aclose()

    return {"ok": True, "job_id": job_id}
