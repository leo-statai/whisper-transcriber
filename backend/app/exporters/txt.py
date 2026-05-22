from typing import Iterable


def render(segments: Iterable) -> str:
    return "\n".join(seg.text.strip() for seg in segments if seg.text.strip())
