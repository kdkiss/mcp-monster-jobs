#!/usr/bin/env python3
"""
Data models for detailed job information in the Monster MCP server
"""

import logging
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger("job-details-models")

@dataclass
class JobDetails:
    """Simplified job details structure"""
    title: str
    company: str
    location: str
    description: str
    job_url: str

@dataclass
class SearchSession:
    """Session management for search results"""
    session_id: str
    search_terms: List[str]
    zip_code: str
    radius: int
    results: List[Dict[str, str]]
    timestamp: datetime
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session has expired"""
        if not isinstance(self.timestamp, datetime):
            logger.warning("Invalid timestamp type in session")
            return True
            
        try:
            elapsed = (datetime.now() - self.timestamp).total_seconds()
            is_expired = elapsed > timeout_seconds
            if is_expired:
                logger.debug(f"Session expired: {elapsed}s > {timeout_seconds}s")
            return is_expired
        except Exception as e:
            logger.error(f"Error checking session expiration: {e}")
            return True