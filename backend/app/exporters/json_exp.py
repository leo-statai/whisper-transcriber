import json
from typing import Iterable


def render(job, segments: Iterable) -> str:
    payload = {
        "id": str(job.id),
        "filename": job.filename,
        "duration_seconds": job.duration_seconds,
        "language": job.detected_language or job.language,
        "model": job.model,
        "segments": [
            {
                "idx": s.idx,
                "start": s.start,
                "end": s.end,
                "text": s.text,
            }
            for s in segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
