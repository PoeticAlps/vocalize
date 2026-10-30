"""Transcribe an audio file with faster-whisper.

设备判定基于 ctranslate2(faster-whisper 的直接依赖,必然存在),
不依赖 torch —— CTranslate2 走自己的推理后端,只支持 cpu / cuda。
"""

from __future__ import annotations

import threading
from pathlib import Path

import ctranslate2
from faster_whisper import WhisperModel

from vocalize.types import Segment


def _pick_device() -> str:
    """Return the best available device string: "cuda" or "cpu".

    CTranslate2 不支持 Apple 的 mps,不要返回 mps。
    """
    if ctranslate2.get_cuda_device_count() > 0:
        return "cuda"
    return "cpu"


def _pick_compute_type(device: str) -> str:
    if device == "cuda":
        return "float16"
    return "int8"


# ── WhisperModel 模块级缓存(Web 场景避免每次上传重新加载模型)──────────
# 键为 (model_size, device, compute_type):同机同参数只加载一次。
_MODEL_CACHE: dict[tuple[str, str, str], WhisperModel] = {}
_MODEL_LOCK = threading.Lock()


def _get_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    key = (model_size, device, compute_type)
    with _MODEL_LOCK:
        model = _MODEL_CACHE.get(key)
        if model is None:
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            _MODEL_CACHE[key] = model
        return model


def transcribe(
    audio_path: str | Path,
    model_size: str = "base",
    device: str | None = None,
    language: str | None = None,
    beam_size: int = 5,
    progress_cb=None,
) -> tuple[list[Segment], str]:
    """Run Whisper transcription and return (segments, detected_language).

    Parameters
    ----------
    audio_path : path to a WAV/MP3/FLAC file
    model_size  : Whisper model size — tiny, base, small, medium, large-v3, etc.
    device      : "cpu" or "cuda" (auto-detected when None)
    language    : ISO-639-1 code, e.g. "zh", "en". None = auto-detect.
    beam_size   : decoding beam width (higher = slower, more accurate).
    progress_cb : optional callable(float) — segment 迭代时按 0.0~1.0 汇报
                  已转写进度(以 seg.end / 音频总时长估算)。
    """
    audio = str(Path(audio_path).resolve())

    dev = device or _pick_device()
    compute_type = _pick_compute_type(dev)

    model = _get_model(model_size, dev, compute_type)

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
    total_duration = float(getattr(info, "duration", 0.0) or 0.0)
    for seg in segments_iter:
        segments.append(
            Segment(
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=seg.text.strip(),
            )
        )
        if progress_cb is not None and total_duration > 0:
            progress_cb(min(seg.end / total_duration, 1.0))

    detected_lang = info.language or "unknown"
    return segments, detected_lang
