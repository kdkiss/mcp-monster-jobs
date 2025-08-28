from __future__ import annotations

"""Smithery-compliant MCP HTTP server implementation.

This module houses the network-facing server that accepts natural-language job
search commands, translates them into :class:`~job_scraper_server.models.Query`
objects via the :pymod:`job_scraper_server.parser` component, delegates the
actual data retrieval to :pymod:`job_scraper_server.scraper`, and finally
returns a compact JSON list of job objects.

The server is now an HTTP server, expecting POST requests with the command
in the body.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import json
import logging
from typing import Type

from . import config
from .models import Job
from .parser import parse_command, CommandParseError
from .scraper import scrape_jobs

__all__ = ["start_server", "MCPHttpRequestHandler", "ThreadedHTTPServer"]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("job_scraper_server")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# HTTP Server Implementation
# ---------------------------------------------------------------------------


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Enable concurrent requests by mixing in ThreadingMixIn."""
    allow_reuse_address = True


class MCPHttpRequestHandler(BaseHTTPRequestHandler):
    """Handle a single Smithery MCP request via HTTP POST."""

    def do_GET(self):
        """Handle GET requests, typically for health checks."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')


    def do_POST(self):
        """Handle POST requests. The command is expected in the request body."""
        client_ip, client_port = self.client_address

        content_length = int(self.headers.get('Content-Length', 0))
        if not content_length:
            self._send_json_error("Bad Request: Content-Length header is missing or zero.", status_code=400)
            return

        try:
            raw_body = self.rfile.read(content_length)
            command = raw_body.decode('utf-8').strip()
        except Exception as e:
            self._send_json_error(f"Bad Request: Could not read or decode request body. {e}", status_code=400)
            return

        logger.info("%s:%s → %s", client_ip, client_port, command)

        try:
            query = parse_command(command)
        except CommandParseError as exc:
            self._send_json_error(str(exc), status_code=400)
            return

        try:
            jobs = scrape_jobs(query)
        except Exception as exc:
            logger.exception("Scraper failure for %s:%s – %s", client_ip, client_port, exc)
            self._send_json_error(f"Scraper error: {exc}", status_code=500)
            return

        payload = [job.to_dict() for job in jobs]
        self._send_json_response(payload)

    def _send_json_response(self, payload, status_code=200):
        """Send a JSON payload with a given status code."""
        try:
            response_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        except Exception as e:
            if not self.wfile.closed:
                logger.exception("Failed to serialize or send response: %s", e)
                if not self.headers_sent:
                    self._send_json_error("Internal server error during response creation.", 500)

    def _send_json_error(self, message: str, status_code: int = 400):
        """Send a JSON error payload."""
        try:
            error_payload = {"error": message}
            response_bytes = json.dumps(error_payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        except Exception as e:
            if not self.wfile.closed:
                logger.exception("Failed to send JSON error response: %s", e)

    def log_message(self, format, *args):
        """Override to log to our logger instead of stderr to maintain consistency."""
        logger.info(format, *args)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_server(host: str | None = None, port: int | None = None, handler_cls: Type[BaseHTTPRequestHandler] | None = None) -> None:
    """Start the MCP HTTP server and block forever."""
    host = host or config.DEFAULT_HOST
    port = port or config.DEFAULT_PORT
    handler_cls = handler_cls or MCPHttpRequestHandler

    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, handler_cls)

    sa = httpd.socket.getsockname()
    logger.info("MCP job-scraper HTTP server listening on http://%s:%s", sa[0], sa[1])

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received – shutting down…")
    finally:
        httpd.server_close()
        logger.info("Server on http://%s:%s terminated", sa[0], sa[1])
