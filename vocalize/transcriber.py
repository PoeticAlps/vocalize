"""Transcribe an audio file with faster-whisper."""

from __future__ import annotations

import torch
from faster_whisper import WhisperModel
from pathlib import Path

from vocalize.types import Segment


def _pick_device() -> str:
    """Return the best available device string."""
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _pick_compute_type(device: str) -> str:
    if device == "cuda":
        return "float16"
    if device == "mps":
        return "int8"
    return "int8"


def transcribe(
    audio_path: str | Path,
    model_size: str = "base",
    device: str | None = None,
    language: str | None = None,
    beam_size: int = 5,
) -> tuple[list[Segment], str]:
    """Run Whisper transcription and return (segments, detected_language).

    Parameters
    ----------
    audio_path : path to a WAV/MP3/FLAC file
    model_size  : Whisper model size — tiny, base, small, medium, large-v3, etc.
    device      : "cpu", "cuda", or "mps" (auto-detected when None)
    language    : ISO-639-1 code, e.g. "zh", "en". None = auto-detect.
    beam_size   : decoding beam width (higher = slower, more accurate).
    """
    audio = str(Path(audio_path).resolve())

    dev = device or _pick_device()
    compute_type = _pick_compute_type(dev)

    model = WhisperModel(model_size, device=dev, compute_type=compute_type)

    segments_iter, info = model.transcribe(
        audio,
        language=language,
        beam_size=beam_size,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        ),
    )

    segments: list[Segment] = []
    for seg in segments_iter:
        segments.append(
            Segment(
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=seg.text.strip(),
            )
        )

    detected_lang = info.language or "unknown"
    return segments, detected_lang
