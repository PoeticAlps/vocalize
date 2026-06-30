"""Write transcription results to various output formats."""

from __future__ import annotations

import json
from pathlib import Path

from vocalize.types import TranscriptionResult


def to_plain_text(result: TranscriptionResult) -> str:
    """Plain text — one line per segment, no timestamps."""
    return result.full_text


def to_srt(result: TranscriptionResult) -> str:
    """SubRip (.srt) subtitle format."""
    lines: list[str] = []
    for idx, seg in enumerate(result.segments, start=1):
        lines.append(str(idx))
        lines.append(
            f"{_fmt_time(seg.start)} --> {_fmt_time(seg.end)}"
        )
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def to_json(result: TranscriptionResult) -> str:
    """Structured JSON with all metadata and segments."""
    data = {
        "source": result.source,
        "language": result.language,
        "model_size": result.model_size,
        "duration_seconds": result.duration,
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
            }
            for s in result.segments
        ],
        "full_text": result.full_text,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


FORMATTERS = {
    "txt": to_plain_text,
    "srt": to_srt,
    "json": to_json,
}


def write(result: TranscriptionResult, output: str | Path, fmt: str) -> Path:
    """Render *result* to *output* path using the given *fmt*.

    *fmt* is inferred from the output extension when it doesn't match a
    known formatter.
    """
    out = Path(output)
    inferred = out.suffix.lower().lstrip(".")
    fmt = fmt if fmt in FORMATTERS else inferred
    if fmt not in FORMATTERS:
        fmt = "txt"

    text = FORMATTERS[fmt](result)
    out.write_text(text, encoding="utf-8")
    return out


def _fmt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS,mmm for SRT."""
    s = int(seconds)
    ms = int(round((seconds - s) * 1000))
    if ms >= 1000:                        # float rounding guard
        ms = 999
    h, remainder = divmod(s, 3600)
    m, sec = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
