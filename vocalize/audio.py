"""Extract audio from a video file as 16 kHz mono WAV."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


_FFMPEG_FALLBACKS: list[str] = [
    # Common install locations on Windows
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*\bin\ffmpeg.exe"
    ),
    # Known TRAE / Marvis bundled copy
    os.path.expandvars(
        r"%APPDATA%\TRAE SOLO CN\ModularData\ai-agent\vm\tools\app\ffmpeg\ffmpeg.exe"
    ),
]


def _find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    for path in _FFMPEG_FALLBACKS:
        p = Path(path)
        if p.exists():
            return str(p)
    raise RuntimeError(
        "ffmpeg not found. Install from https://ffmpeg.org/ or add it to PATH."
    )


def extract_audio(
    video_path: str | Path,
    sample_rate: int = 16000,
) -> Path:
    """Extract audio track from *video_path* and return a path to a temp WAV.

    The file lives in the system temp dir and should be deleted by the caller
    once transcription is done.
    """
    video = Path(video_path).resolve()
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    ffmpeg = _find_ffmpeg()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    wav_path = Path(tmp.name)

    cmd = [
        ffmpeg,
        "-y",                   # overwrite
        "-i", str(video),
        "-vn",                  # no video
        "-ac", "1",             # mono
        "-ar", str(sample_rate),
        "-f", "wav",
        "-acodec", "pcm_s16le",
        str(wav_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        wav_path.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")

    return wav_path
