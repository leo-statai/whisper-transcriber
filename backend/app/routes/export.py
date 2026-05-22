from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlmodel import Session, select

from app.db import get_session
from app.exporters import docx_exp, json_exp, srt, txt, vtt
from app.models import Job, Segment

router = APIRouter(tags=["export"])


@router.get("/jobs/{job_id}/export")
def export_job(
    job_id: UUID,
    format: str = Query(..., pattern="^(srt|vtt|txt|json|docx)$"),
    session: Session = Depends(get_session),
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    segments = session.exec(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.idx)
    ).all()
    base = (job.filename or "transcricao").rsplit(".", 1)[0] or "transcricao"

    if format == "srt":
        body = srt.render(segments).encode("utf-8")
        media = "application/x-subrip"
        ext = "srt"
    elif format == "vtt":
        body = vtt.render(segments).encode("utf-8")
        media = "text/vtt"
        ext = "vtt"
    elif format == "txt":
        body = txt.render(segments).encode("utf-8")
        media = "text/plain; charset=utf-8"
        ext = "txt"
    elif format == "json":
        body = json_exp.render(job, segments).encode("utf-8")
        media = "application/json"
        ext = "json"
    elif format == "docx":
        body = docx_exp.render(job, segments)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        raise HTTPException(400, "Formato inválido")

    headers = {"Content-Disposition": f'attachment; filename="{base}.{ext}"'}
    return Response(content=body, media_type=media, headers=headers)
