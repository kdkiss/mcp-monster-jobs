from __future__ import annotations

"""Web-scraping logic for Monster.com job search results.

The public HTML structure of Monster changes fairly frequently.  The parser
implemented here therefore takes a *best-effort* approach utilising multiple
CSS selectors to locate the same logical pieces of information (title,
company, description/snippet, job link).  When a selector no longer matches it
will simply be skipped; the scraper will continue trying alternative patterns
so that minor redesigns do not immediately break the service.

The scraper is intentionally lightweight – no Selenium/Playwright, only
`requests` + `BeautifulSoup`.  This keeps the dependency footprint small and
avoids the need for a browser runtime in typical server environments.  Anti-
bot counter-measures on Monster are limited for low-throughput access.  In
practice IP rotation or headless Chrome may be required for large-scale
scraping – those concerns are outside the scope of this demo implementation.
"""

from dataclasses import asdict
import time
import logging
import random
from typing import List, Iterable
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag

from . import config
from .models import Job, Query

__all__ = [
    "ScraperError",
    "build_search_url",
    "scrape_jobs",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ScraperError(RuntimeError):
    """Raised when the scraper cannot obtain or parse results."""


# ---------------------------------------------------------------------------
# URL construction helpers
# ---------------------------------------------------------------------------

def _keywords_to_query_param(keywords: List[str]) -> str:
    """Join keyword list with '+' after individual URL encoding."""
    return "+".join(quote_plus(k) for k in keywords)


def build_search_url(query: Query) -> str:
    """Return a Monster.com job-search URL constructed from *query*.

    The URL format is reverse-engineered from interactive use on
    monster.com/jobs/search – the important query parameters are:

    q       – keywords (+ delimited)
    where   – location string (comma or dash separated acceptable)
    radius  – integer miles (Monster supports 5 .. 100)
    """

    keywords_param = _keywords_to_query_param(query.keywords)
    location_param = quote_plus(query.location)
    radius_param = str(query.radius)

    # Base already ends with '/'; we only append the query string
    return (
        f"{config.MONSTER_BASE_URL}?q={keywords_param}"
        f"&where={location_param}&radius={radius_param}"
    )


# ---------------------------------------------------------------------------
# Low-level HTTP fetching with retry/backoff
# ---------------------------------------------------------------------------

def _http_get(url: str) -> str:
    """GET *url* returning decoded text, with retry/back-off according to config."""

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=config.random_headers(),
                timeout=config.REQUEST_TIMEOUT,
            )
            if response.status_code >= 400:
                raise ScraperError(
                    f"Monster returned HTTP {response.status_code} for GET {url}"
                )
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text
        except (requests.RequestException, ScraperError) as exc:
            if attempt >= config.MAX_RETRIES:
                raise ScraperError("Failed to fetch Monster search page") from exc

            backoff = config.RETRY_BACKOFF_BASE * attempt * random.random()
            logger.debug(
                "HTTP GET failed (attempt %s/%s): %s – retrying in %.1fs",
                attempt,
                config.MAX_RETRIES,
                exc,
                backoff,
            )
            time.sleep(backoff)

    # unreached – loop either returns or raises


# ---------------------------------------------------------------------------
# HTML parsing helpers – since we do not control Monster markup keep it robust
# ---------------------------------------------------------------------------

_TITLE_SELECTORS = [
    "h2.title a",  # Common desktop layout
    "h2.card-title a",  # Alternative card
]
_COMPANY_SELECTORS = [
    "div.company span.name",
    "div.company",
    "p.company",
]
_SNIPPET_SELECTORS = [
    "div.summary",
    "div.job-snippet",
    "p.summary",
]
_JOB_CARD_SELECTORS = [
    "section.card-content",  # main desktop
    "div.flex-row",  # fallback
]


def _extract_first_text(elem: Tag | None) -> str | None:
    if elem is None:
        return None
    text = elem.get_text(strip=True)
    return text or None


def _parse_job_card(card: Tag) -> Job | None:
    """Parse a BeautifulSoup *card* element into a Job dataclass.

    Returns None if mandatory information (title+link) cannot be located.
    """

    title = link = None
    for sel in _TITLE_SELECTORS:
        anchor = card.select_one(sel)
        if anchor and anchor.get_text(strip=True):
            title = anchor.get_text(strip=True)
            link = anchor.get("href")
            break

    if not title or not link:
        # mandatory fields missing – skip card
        return None

    company = None
    for sel in _COMPANY_SELECTORS:
        val = _extract_first_text(card.select_one(sel))
        if val:
            company = val
            break

    description = None
    for sel in _SNIPPET_SELECTORS:
        val = _extract_first_text(card.select_one(sel))
        if val:
            description = val
            break

    return Job(title=title, company=company, description=description, link=link)


# ---------------------------------------------------------------------------
# Public scraper API
# ---------------------------------------------------------------------------

def scrape_jobs(query: Query, *, max_results: int | None = None) -> List[Job]:
    """Scrape Monster.com for *query* returning a list of `Job`.

    Parameters
    ----------
    query : Query
        Normalised query object (keywords, location, radius)
    max_results : int | None, optional
        Optional limit to stop parsing after N results.  `None` returns all
        jobs found on the initial result page.
    """

    url = build_search_url(query)
    logger.debug("Fetching Monster search page: %s", url)
    html = _http_get(url)

    soup = BeautifulSoup(html, "lxml")

    cards: Iterable[Tag] = []
    for sel in _JOB_CARD_SELECTORS:
        found = soup.select(sel)
        if found:
            cards = found
            break

    jobs: List[Job] = []
    for card in cards:
        job = _parse_job_card(card)
        if job:
            jobs.append(job)
            if max_results is not None and len(jobs) >= max_results:
                break

    return jobs
