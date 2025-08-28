from __future__ import annotations
"""Top-level package for the Smithery-compliant Monster.com job-scraper server.

Exposes the most frequently used public symbols so that external code can do::

    from job_scraper_server import scrape_jobs, start_server

without having to know the exact internal module structure.
"""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

# Re-export convenience API --------------------------------------------------

_scraper: ModuleType = import_module("job_scraper_server.scraper")
_server: ModuleType = import_module("job_scraper_server.server")

scrape_jobs = _scraper.scrape_jobs  # noqa: F401
build_search_url = _scraper.build_search_url  # noqa: F401
ScraperError = _scraper.ScraperError  # noqa: F401

start_server = _server.start_server  # noqa: F401

# Clean-up internal names from the public namespace
if not TYPE_CHECKING:
    del import_module, ModuleType, _scraper, _server, TYPE_CHECKING
