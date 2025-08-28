from __future__ import annotations

"""Smithery-compliant MCP TCP server implementation.

This module houses the network-facing server that accepts natural-language job
search commands, translates them into :class:`~job_scraper_server.models.Query`
objects via the :pymod:`job_scraper_server.parser` component, delegates the
actual data retrieval to :pymod:`job_scraper_server.scraper`, and finally
returns a compact JSON list of job objects.

The server follows the **Smithery Message Command Protocol (MCP)** which in its
simplest form is just *one* newline-terminated UTF-8 string per request and *one*
newline-terminated UTF-8 response.  All responses **must** be valid JSON so that
clients can reliably decode them.  Error conditions are reported using a JSON
object of the following shape::

    {"error": "human readable message"}\n
Successful responses are JSON arrays where every element is a mapping matching
:pyclass:`job_scraper_server.models.Job.to_dict`.

The implementation purposefully avoids heavyweight frameworks – the whole server
is fewer than ~100 LoC while gracefully handling multiple concurrent client
connections using the standard-library :pymod:`socketserver` helpers.
"""

from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler
import json
import logging
import socket
from typing import Tuple, Type

from . import config
from .models import Job
from .parser import parse_command, CommandParseError
from .scraper import scrape_jobs

__all__ = ["start_server", "MCPRequestHandler", "ThreadedTCPServer"]

# ---------------------------------------------------------------------------
# Logging setup – keep it extremely small to avoid another dependency.
# ---------------------------------------------------------------------------

logger = logging.getLogger("job_scraper_server")
if not logger.handlers:
    # Default to INFO if the root logger has no explicit level yet.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# socketserver plumbing
# ---------------------------------------------------------------------------


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    """Nothing special – we merely flip on :class:`~socketserver.ThreadingMixIn`."""

    # Allow quick restart on the same port by re-using the address.
    allow_reuse_address: bool = True


class MCPRequestHandler(StreamRequestHandler):
    """Handle a single Smithery MCP request on a blocking thread."""

    # Slight read-limit sanitizer so a rogue client cannot exhaust memory.
    _MAX_LINE_LENGTH: int = 4096  # bytes

    def handle(self) -> None:  # noqa: D401 – imperative mood acceptable in handlers.
        client: Tuple[str, int] = self.client_address
        logger.debug("Connection from %s:%s", *client)

        try:
            raw = self.rfile.readline(self._MAX_LINE_LENGTH)
        except Exception as exc:  # pragma: no cover – network failures
            logger.warning("Failed to read from %s:%s – %s", *client, exc)
            return

        if not raw:
            # Client closed connection without sending anything.
            logger.debug("Client %s:%s disconnected before sending data", *client)
            return

        try:
            command = raw.decode("utf-8", errors="ignore").strip()
        except UnicodeDecodeError:
            self._write_json_error("invalid UTF-8 bytes received")
            return

        logger.info("%s:%s → %s", *client, command)

        try:
            query = parse_command(command)
        except CommandParseError as exc:
            self._write_json_error(str(exc))
            return

        try:
            jobs = scrape_jobs(query)
        except Exception as exc:  # pragma: no cover – network issues, scraper bugs
            logger.exception("Scraper failure for %s:%s – %s", *client, exc)
            self._write_json_error("scraper error: " + str(exc))
            return

        # Convert dataclass objects to dicts so they are JSON-serialisable.
        payload = [job.to_dict() if isinstance(job, Job) else job for job in jobs]
        try:
            response_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"
        except (TypeError, ValueError) as exc:  # pragma: no cover – should never happen
            logger.exception("Failed to serialise response for %s:%s – %s", *client, exc)
            self._write_json_error("internal serialisation error")
            return

        try:
            self.wfile.write(response_bytes)
        except (BrokenPipeError, ConnectionResetError):
            logger.debug("Client %s:%s disconnected while sending response", *client)
        else:
            logger.debug("Sent %d bytes to %s:%s", len(response_bytes), *client)

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------

    def _write_json_error(self, message: str) -> None:
        """Send an *error* JSON payload and swallow socket errors."""
        err = json.dumps({"error": message}, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            self.wfile.write(err)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client vanished – nothing we can do.


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_server(host: str | None = None, port: int | None = None, handler_cls: Type[StreamRequestHandler] | None = None) -> None:
    """Start the MCP TCP server and block forever.

    This helper is used by the :pymod:`job_scraper_server.main` CLI entry-point
    but can also be called programmatically.  It blocks the current thread until
    interrupted via *Ctrl-C* or :pyexc:`KeyboardInterrupt`.
    """
    host = host or config.DEFAULT_HOST
    port = port or config.DEFAULT_PORT
    handler_cls = handler_cls or MCPRequestHandler

    # Ensure we pick an appropriate socket backlog.  128 is the current Linux
    # default since kernel 5.4 so this is merely explicit.
    backlog = 128

    # Set TCPServer.request_queue_size via subclass attribute after instantiation
    # to avoid subclassing for one constant.
    server: TCPServer = ThreadedTCPServer((host, port), handler_cls)
    server.request_queue_size = backlog  # type: ignore[attr-defined]

    sa = server.socket.getsockname()
    logger.info("MCP job-scraper server listening on %s:%s", sa[0], sa[1])

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received – shutting down…")
    finally:
        # Shut down all worker threads then close the listening socket.
        server.shutdown()
        server.server_close()
        logger.info("Server on %s:%s terminated", sa[0], sa[1])
