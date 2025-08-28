"""Configuration constants used across the Smithery-compliant job-scraper server.

Having a single dedicated module for tunables avoids hard-coding numbers and
magic strings in the business-logic layers (scraper, TCP server, etc.) while
keeping the overall dependency graph simple (no dynamic settings objects).

Only **static** values that are safe to import at module import-time should live
here. Anything that might require I/O (reading .env, making network calls, …)
should be deferred to runtime logic in the respective component.
"""
from __future__ import annotations

import os
import random
from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Network & server settings
# ---------------------------------------------------------------------------

# Host/port the MCP TCP server binds to when launched via ``python -m main``
DEFAULT_HOST: str = os.getenv("JOB_SCRAPER_HOST", "0.0.0.0")
DEFAULT_PORT: int = int(os.getenv("JOB_SCRAPER_PORT", "5555"))

# Socket recv buffer size (bytes)
RECV_BUFFER: int = 4096

# ---------------------------------------------------------------------------
# HTTP client settings for the Monster.com scraper
# ---------------------------------------------------------------------------

# Base URL for Monster search result pages
MONSTER_BASE_URL: str = "https://www.monster.com/jobs/search/"

# Request timeout in seconds for the *entire* HTTP request (connect + read)
REQUEST_TIMEOUT: int = 15

# Maximum number of retries for transient network failures
MAX_RETRIES: int = 3

# Seconds to wait between retries – implemented as incremental back-off: the
# actual delay will be ``RETRY_BACKOFF_BASE * attempt``
RETRY_BACKOFF_BASE: float = 1.2

# ---------------------------------------------------------------------------
# User-Agent pool – basic set of common desktop browsers. This helps reduce the
# likelihood of being blocked by Monster's anti-bot measures. For serious
# production use you would rotate a much larger pool and possibly proxy IPs.
# ---------------------------------------------------------------------------
_USER_AGENTS: List[str] = [
    # Chrome – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    # Firefox – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    # Edge – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
    # Chrome – macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    # Safari – macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.5 Safari/605.1.15",
]


def random_headers() -> Dict[str, Any]:
    """Return HTTP headers with a randomly chosen *desktop* User-Agent string.

    Keeping the function in *config* avoids importing *requests* in this module
    while still providing a single source of truth for header construction.
    """

    return {
        "User-Agent": random.choice(_USER_AGENTS),
        # Identity headers make the request appear more like a real browser.
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
