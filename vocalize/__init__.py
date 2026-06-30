"""vocalize — extract speech from videos locally."""

from vocalize.audio import extract_audio
from vocalize.output import write
from vocalize.pipeline import run_pipeline
from vocalize.transcriber import transcribe
from vocalize.types import Segment, TranscriptionResult

__all__ = [
    "extract_audio",
    "transcribe",
    "write",
    "run_pipeline",
    "Segment",
    "TranscriptionResult",
]

__version__ = "0.1.0"
