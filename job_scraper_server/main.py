from __future__ import annotations
"""CLI entry-point for the Smithery-compliant job-scraper server.

Usage (default host/port from :pymod:`job_scraper_server.config`)::

    python -m job_scraper_server.main

or explicitly specify a bind address/port::

    python -m job_scraper_server.main --host 127.0.0.1 --port 9000

The module is intentionally kept *tiny* – all heavy-lifting is delegated to
:meth:`job_scraper_server.server.start_server` so that the CLI stays
maintenance-free and easy to reason about.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from . import config
from .server import start_server

__all__ = ["main"]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:  # pragma: no cover – trivial
    """Return a fully-configured :class:`argparse.ArgumentParser`."""

    parser = argparse.ArgumentParser(
        prog="job-scraper-server",
        description="Start the Smithery MCP job-scraper TCP server.",
    )

    parser.add_argument(
        "--host",
        metavar="ADDR",
        default=config.DEFAULT_HOST,
        help=f"Bind address (default: {config.DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        metavar="N",
        type=int,
        default=config.DEFAULT_PORT,
        help=f"TCP port (default: {config.DEFAULT_PORT})",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Python logging level (default: INFO)",
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------


def main(argv: List[str] | None = None) -> None:
    """Parse CLI args then hand over execution to :pyfunc:`server.start_server`."""

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Configure root logger *before* the server spins up so that child loggers
    # inherit the chosen level.
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    # Pass sys.argv[1:] so that *argparse* does not see the script name.
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        # Graceful shutdown is already handled inside *start_server* but catching
        # here avoids the generic Python stack-trace on Ctrl-C when running as a
        # stand-alone script.
        pass
