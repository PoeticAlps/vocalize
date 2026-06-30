"""Transcribe video → text.  One function, one CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vocalize.output import FORMATTERS
from vocalize.pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vocalize",
        description="Extract speech from videos and transcribe to text.",
    )
    p.add_argument("video", help="path to the video file")
    p.add_argument(
        "-m", "--model",
        default="base",
        choices=["tiny", "tiny.en", "base", "base.en", "small",
                 "small.en", "medium", "medium.en", "large-v3"],
        help="Whisper model size (default: base)",
    )
    p.add_argument(
        "-l", "--language",
        default=None,
        help="ISO-639-1 language code (e.g. zh, en). Auto-detect if omitted.",
    )
    p.add_argument(
        "-d", "--device",
        default=None,
        choices=["cpu", "cuda", "mps"],
        help="Compute device (auto-detected if omitted).",
    )
    p.add_argument(
        "-f", "--format",
        default="txt",
        choices=sorted(FORMATTERS.keys()),
        help="Output format (default: txt)",
    )
    p.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path. Defaults to <video_stem>.<fmt> when fmt is not txt.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Default output path: same folder, same stem, chosen extension
    output = args.output
    if output is None and args.format != "txt":
        default_name = Path(args.video).stem + "." + args.format
        output = str(Path(args.video).with_name(default_name))

    try:
        run_pipeline(
            args.video,
            model_size=args.model,
            language=args.language,
            device=args.device,
            fmt=args.format,
            output=output,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
