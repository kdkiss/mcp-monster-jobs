#!/usr/bin/env python3
"""
Session management for storing and retrieving search results
"""

import sys
import os
import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("session-manager")

try:
    from job_details_models import SearchSession
except ImportError as e:
    logger.error(f"Failed to import job_details_models: {e}")
    raise

class SessionManager:
    """Manages search sessions for follow-up questions"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, SearchSession] = {}
        self.session_timeout = session_timeout
        logger.info(f"SessionManager initialized with timeout: {session_timeout}s")
    
    def create_session(self, results: List[Dict[str, str]], search_terms: List[str] = None, zip_code: str = "40210", radius: int = 5) -> str:
        """
        Create a new search session
        
        Args:
            search_terms: List of search terms used
            zip_code: ZIP code used for search
            radius: Search radius in km
            results: List of job results
            
        Returns:
            Session ID for the new session
        """
        session_id = str(uuid.uuid4())
        
        try:
            session = SearchSession(
                session_id=session_id,
                search_terms=search_terms or [],
                zip_code=zip_code,
                radius=radius,
                results=results,
                timestamp=datetime.now()
            )
            
            self.sessions[session_id] = session
            self._cleanup_expired_sessions()
            
            logger.info(f"Created new session {session_id[:8]}... with {len(results)} results")
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SearchSession]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SearchSession object or None if not found/expired
        """
        if not session_id:
            logger.warning("Attempted to get session with empty session_id")
            return None
            
        if session_id not in self.sessions:
            logger.debug(f"Session {session_id[:8]}... not found")
            return None
        
        session = self.sessions[session_id]
        if session.is_expired(self.session_timeout):
            del self.sessions[session_id]
            logger.info(f"Session {session_id[:8]}... expired and removed")
            return None
        
        logger.debug(f"Retrieved session {session_id[:8]}...")
        return session
    
    def find_job_in_session(self, session_id: str, job_query: str) -> Optional[Dict[str, str]]:
        """
        Find a specific job in a session based on user query
        
        Args:
            session_id: The session ID
            job_query: User's job query (e.g., "AML Specialist")
            
        Returns:
            Job dictionary or None if not found
        """
        if not session_id or not job_query:
            logger.warning("Invalid parameters for find_job_in_session")
            return None
            
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id[:8]}... not found or expired")
            return None
        
        # Normalize query for matching
        query_lower = job_query.lower().strip()
        logger.debug(f"Searching for job matching: {query_lower}")
        
        # Try exact title match first
        for job in session.results:
            if query_lower in job.get('title', '').lower():
                logger.debug(f"Found job by title match: {job.get('title', '')}")
                return job
        
        # Try company match
        for job in session.results:
            if query_lower in job.get('company', '').lower():
                logger.debug(f"Found job by company match: {job.get('company', '')}")
                return job
        
        # Try partial title match
        query_words = query_lower.split()
        for job in session.results:
            title_words = job.get('title', '').lower().split()
            if any(word in title_words for word in query_words):
                logger.debug(f"Found job by partial match: {job.get('title', '')}")
                return job
        
        logger.debug(f"No job found matching: {job_query}")
        return None
    
    def get_recent_session(self) -> Optional[SearchSession]:
        """
        Get the most recent active session
        
        Returns:
            Most recent SearchSession or None if no active sessions
        """
        self._cleanup_expired_sessions()
        
        if not self.sessions:
            logger.debug("No active sessions found")
            return None
        
        # Return the most recent session
        recent_session = max(self.sessions.values(), key=lambda s: s.timestamp)
        logger.debug(f"Returning most recent session: {recent_session.session_id[:8]}...")
        return recent_session
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.debug(f"Cleaned up expired session: {session_id[:8]}...")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        Get a human-readable summary of a session
        
        Args:
            session_id: The session ID
            
        Returns:
            Summary string or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Cannot get summary for session {session_id[:8]}... - not found")
            return None
        
        try:
            summary = f"Search Session: {session.session_id[:8]}...\n"
            summary += f"Search Terms: {', '.join(session.search_terms)}\n"
            summary += f"Location: {session.zip_code} (±{session.radius}km)\n"
            summary += f"Results: {len(session.results)} jobs found\n"
            summary += f"Search Time: {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            logger.debug(f"Generated summary for session {session_id[:8]}...")
            return summary
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            return None
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        self._cleanup_expired_sessions()
        session_ids = list(self.sessions.keys())
        logger.debug(f"Listed {len(session_ids)} active sessions")
        return session_ids

# Global session manager instance
session_manager = SessionManager()