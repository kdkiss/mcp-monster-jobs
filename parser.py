"""Command parser translating Smithery MCP natural-language commands into
Query objects understood by the scraper layer.

Example accepted commands::

    get fraud jobs near winnetka, ca within 5 miles\n
    get software engineer jobs near 91306 within 15 miles\n
    get data scientist jobs near chicago, il\n
The grammar is intentionally simple – it is NOT a fully-fledged NLP solution.
Instead we rely on a couple of deterministic regular-expression captures that
cover the limited command variations required by the reproduction plan.

If the client command cannot be parsed, :class:`CommandParseError` will be
raised which should be converted to a JSON error at the TCP-server layer.
"""
from __future__ import annotations

import re
import string
from typing import List

from .models import Query

__all__ = [
    "CommandParseError",
    "parse_command",
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CommandParseError(ValueError):
    """Raised when a natural-language search command cannot be understood."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_RADIUS_RE = re.compile(r"within\s+(\d+)\s*miles?", re.IGNORECASE)
_NEAR_RE = re.compile(r"\s+near\s+", re.IGNORECASE)
# We allow both "job" and "jobs" so we strip either suffix when extracting
_JOBS_SUFFIX_RE = re.compile(r"\s+jobs?$", re.IGNORECASE)

# Legal set of punctuation chars we will simply strip (replace with space) to
# simplify tokenisation. We keep commas because they are useful inside the
# *location* part ("winnetka, ca").
_TO_STRIP = "".join(ch for ch in string.punctuation if ch != ",")
_TRANS_TABLE = str.maketrans({ch: " " for ch in _TO_STRIP})


def _normalise_whitespace(text: str) -> str:
    """Collapse repeated whitespace to single spaces and trim."""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_command(command: str) -> Query:
    """Parse a Smithery MCP *command* string and return a :class:`~models.Query`.

    Parameters
    ----------
    command:
        The raw command bytes decoded to *str*, **including** any accidental
        leading/trailing whitespace or newline.  Parsing is case-insensitive.

    Returns
    -------
    Query
        Normalised query object.

    Raises
    ------
    CommandParseError
        If the command is syntactically invalid.
    """
    if not command:
        raise CommandParseError("empty command")

    # Lower case and remove undesired punctuation for simpler regexes.
    cmd = command.lower().translate(_TRANS_TABLE)
    cmd = _normalise_whitespace(cmd)

    # Ensure the command starts with the expected verb.
    if not cmd.startswith("get "):
        raise CommandParseError("command must start with 'get'")

    # 1. Extract optional radius ("within <n> miles").
    radius = 10  # default fallback in miles
    radius_match = _RADIUS_RE.search(cmd)
    if radius_match:
        radius = int(radius_match.group(1))
        # Remove that fragment from the command so it does not interfere
        cmd = _RADIUS_RE.sub("", cmd)
        cmd = _normalise_whitespace(cmd)

    # 2. Split around " near " to separate keyword part from location part.
    near_split = _NEAR_RE.split(cmd, maxsplit=1)
    if len(near_split) != 2:
        raise CommandParseError("missing 'near <location>' segment")

    keywords_part, location_part = near_split[0], near_split[1]

    # Remove leading verb again ("get ") from keywords_part.
    if keywords_part.startswith("get "):
        keywords_part = keywords_part[4:]
    keywords_part = _JOBS_SUFFIX_RE.sub("", keywords_part)
    keywords_part = _normalise_whitespace(keywords_part)

    if not keywords_part:
        raise CommandParseError("no search keywords found")

    if not location_part:
        raise CommandParseError("no location specified after 'near'")

    # Extract list of keyword tokens (split on whitespace)
    keywords: List[str] = keywords_part.split()
    location: str = location_part.strip()

    try:
        query = Query(keywords=keywords, location=location, radius=radius)
    except ValueError as exc:
        # Re-raise as CommandParseError so callers have a single error type.
        raise CommandParseError(str(exc)) from exc

    return query
