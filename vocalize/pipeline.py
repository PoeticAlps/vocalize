"""Pipeline: wire audio extraction → transcription → output."""

from __future__ import annotations

import time
from pathlib import Path

from vocalize.audio import extract_audio
from vocalize.output import FORMATTERS, write
from vocalize.transcriber import transcribe
from vocalize.types import TranscriptionResult


def run_pipeline(
    video_path: str | Path,
    *,
    model_size: str = "base",
    language: str | None = None,
    device: str | None = None,
    fmt: str = "txt",
    output: str | Path | None = None,
) -> TranscriptionResult:
    """Full pipeline: extract audio → transcribe → write output.

    Returns the result object regardless of whether output is written.
    """
    video = Path(video_path)
    t0 = time.monotonic()
    print(f"[1/3] Extracting audio from {video.name} ...")
    wav = extract_audio(video)
    try:
        print(f"[2/3] Transcribing ({model_size} model) ...")
        segments, lang = transcribe(
            wav, model_size=model_size, device=device, language=language
        )
        result = TranscriptionResult(
            source=str(video),
            language=lang,
            model_size=model_size,
            segments=segments,
        )
        elapsed = time.monotonic() - t0
        print(
            f"        -> {len(segments)} segments, "
            f"{result.duration:.1f}s audio, lang={lang}, "
            f"{elapsed:.1f}s elapsed"
        )

        if output is not None:
            out_path = write(result, output, fmt)
            print(f"[3/3] Saved -> {out_path}")
        else:
            formatter = FORMATTERS.get(fmt, FORMATTERS["txt"])
            print(f"[3/3] {fmt.upper()} output (stdout):")
            print(formatter(result))

        return result
    finally:
        wav.unlink(missing_ok=True)
