#!/usr/bin/env python3
"""
Data models for detailed job information in the Monster MCP server
"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

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
        return (datetime.now() - self.timestamp).total_seconds() > timeout_seconds