from __future__ import annotations

"""Smithery-compliant MCP HTTP server implementation.

This module houses the network-facing server that implements the MCP 'tools'
capability. It understands JSON-RPC 2.0 and provides two methods:
- tools/list: To discover the `search_jobs` tool.
- tools/call: To execute a job search.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import json
import logging
from typing import Any, Dict, Type

from . import config
from .models import Job, Query
from .scraper import scrape_jobs

__all__ = ["start_server", "MCPHttpRequestHandler", "ThreadedHTTPServer"]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("job_scraper_server")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------------
# MCP Tool Definition
# ---------------------------------------------------------------------------

SEARCH_JOBS_TOOL = {
    "name": "search_jobs",
    "title": "Job Search",
    "description": "Searches for jobs on Monster.com based on keywords, location, and radius.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "The job keywords to search for (e.g., 'python developer')."
            },
            "location": {
                "type": "string",
                "description": "The city and state to search in (e.g., 'Austin, TX')."
            },
            "radius": {
                "type": "integer",
                "description": "The search radius in miles.",
                "default": 10
            }
        },
        "required": ["keywords", "location"]
    }
}


# ---------------------------------------------------------------------------
# HTTP Server Implementation
# ---------------------------------------------------------------------------


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Enable concurrent requests by mixing in ThreadingMixIn."""
    allow_reuse_address = True


class MCPHttpRequestHandler(BaseHTTPRequestHandler):
    """Handles MCP JSON-RPC requests."""

    def do_GET(self):
        """Handle GET requests, typically for health checks."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def do_POST(self):
        """Handle POST requests containing JSON-RPC commands."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if not content_length:
                self._send_json_rpc_error(-32700, "Parse error", "Missing Content-Length", None)
                return

            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body)

            request_id = data.get("id")
            if data.get("jsonrpc") != "2.0" or "method" not in data:
                self._send_json_rpc_error(-32600, "Invalid Request", "Not a valid JSON-RPC 2.0 request", request_id)
                return

            method = data["method"]
            params = data.get("params", {})

            if method == "tools/list":
                self._handle_tools_list(request_id)
            elif method == "tools/call":
                self._handle_tools_call(request_id, params)
            else:
                self._send_json_rpc_error(-32601, "Method not found", f"The method '{method}' does not exist.", request_id)

        except json.JSONDecodeError:
            self._send_json_rpc_error(-32700, "Parse error", "Invalid JSON was received by the server.", None)
        except Exception as e:
            logger.exception("An unexpected error occurred while processing the request.")
            self._send_json_rpc_error(-32603, "Internal error", str(e), data.get("id"))

    def _handle_tools_list(self, request_id):
        """Handle the tools/list request."""
        result = {
            "tools": [SEARCH_JOBS_TOOL],
        }
        self._send_json_rpc_response(result, request_id)

    def _handle_tools_call(self, request_id, params):
        """Handle the tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name != "search_jobs":
            self._send_json_rpc_error(-32602, "Invalid params", f"Unknown tool name: {tool_name}", request_id)
            return

        try:
            query = Query(
                keywords=arguments.get("keywords"),
                location=arguments.get("location"),
                radius=arguments.get("radius", 10)
            )
        except KeyError as e:
            self._send_json_rpc_error(-32602, "Invalid params", f"Missing required argument: {e}", request_id)
            return

        try:
            jobs = scrape_jobs(query)
            content = [{"type": "text", "text": f"{job.title} at {job.company}\n{job.snippet}\n{job.link}\n"} for job in jobs]
            if not content:
                content = [{"type": "text", "text": "No jobs found matching your criteria."}]

            result = {
                "content": content,
                "isError": False
            }
            self._send_json_rpc_response(result, request_id)

        except Exception as e:
            logger.exception("Scraper failed during tools/call execution.")
            result = {
                "content": [{"type": "text", "text": f"An error occurred while scraping jobs: {e}"}],
                "isError": True
            }
            self._send_json_rpc_response(result, request_id)

    def _send_json_rpc_response(self, result, request_id):
        """Sends a successful JSON-RPC response."""
        response_payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        self._send_response(200, response_payload)

    def _send_json_rpc_error(self, code, message, data, request_id):
        """Sends a JSON-RPC error response."""
        response_payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
                "data": data
            }
        }
        self._send_response(200, response_payload) # JSON-RPC errors usually use 200 OK for transport

    def _send_response(self, status_code, payload):
        """Helper to send a JSON response."""
        try:
            response_bytes = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        except Exception as e:
            logger.exception("Failed to send response: %s", e)

    def log_message(self, format, *args):
        """Override to log to our logger instead of stderr."""
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
