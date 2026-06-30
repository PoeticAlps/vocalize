"""Web UI entry point — launches the FastAPI server."""

from __future__ import annotations

import argparse
import sys

from vocalize.web_server import launch


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="vocalize-web",
        description="Launch the Vocalize web panel.",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Server port (default: 8080)"
    )
    args = parser.parse_args()
    launch(port=args.port)


if __name__ == "__main__":
    main()
