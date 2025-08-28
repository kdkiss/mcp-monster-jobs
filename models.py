"""Typed data models for the Smithery-compliant job-scraper server.

Keeping the models in a dedicated module keeps type definitions
and (de)serialisation helpers centralised and avoids circular imports
between the parser, scraper and TCP server layers.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json


@dataclass(slots=True)
class Job:
    """Representation of a single job posting scraped from Monster.com."""

    title: str
    company: Optional[str]
    description: Optional[str]
    link: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert the job instance to a plain serialisable dict."""
        return asdict(self)

    def to_json(self) -> str:
        """Render the job instance as a compact JSON string. Mainly useful for tests."""
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False)


@dataclass(slots=True)
class Query:
    """Normalised representation of a natural-language job search query.

    Parameters
    ----------
    keywords:
        A list of search keywords, e.g. ["fraud", "analyst"].  In practice this
        will be joined by the scraper layer with "+" to build the Monster.com
        query string.
    location:
        Human readable location string compatible with Monster's search URL
        structure, e.g. "winnetka, ca" or zip-code "91306".
    radius:
        Search radius in *miles* (Monster accepts 5, 10, 15… up to 100).
    """

    keywords: List[str]
    location: str
    radius: int = 10  # miles

    def __post_init__(self) -> None:
        if not self.keywords:
            raise ValueError("Query.keywords cannot be empty")
        if self.radius <= 0:
            raise ValueError("Query.radius must be positive")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keywords": " ".join(self.keywords),
            "location": self.location,
            "radius": self.radius,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False)
