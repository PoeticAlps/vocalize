"""Shared types for vocalize."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Segment:
    """One transcribed speech segment."""
    start: float  # seconds
    end: float    # seconds
    text: str = ""


@dataclass(frozen=True)
class TranscriptionResult:
    """Full output of a transcription job."""
    source: str          # original video path
    language: str        # detected or specified language code
    model_size: str      # whisper model used
    segments: list[Segment] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(s.text for s in self.segments)

    @property
    def duration(self) -> float:
        if not self.segments:
            return 0.0
        return self.segments[-1].end
