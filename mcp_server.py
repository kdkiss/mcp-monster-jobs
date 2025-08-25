"""
MCP (Model Context Protocol) server implementation for Monster Jobs.
This module implements the JSON-RPC 2.0 protocol required by MCP.
"""

import json
import re
import requests
import time
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, Blueprint
from urllib.parse import quote, urljoin

# Import MCP for decorator usage
try:
    from mcp import MCP, mcp
except ImportError:
    # Fallback if MCP library is not available
    mcp = None
    MCP = None


def parse_query(query: str) -> Tuple[str, str, int]:
    """Parse the user query to extract job title, location, and distance."""
    # Default values
    job_title = ""
    location = ""
    distance = 5

    # Remove common words and extract meaningful parts
    query_lower = query.lower()

    # Extract distance if specified
    distance_match = re.search(r'within\s+(\d+)\s+miles?', query_lower)
    if distance_match:
        distance = int(distance_match.group(1))
        query_lower = re.sub(r'within\s+\d+\s+miles?', '', query_lower)

    # Extract location if "near" is present
    near_match = re.search(r'near\s+([^,]+)', query_lower)
    if near_match:
        location = near_match.group(1).strip()
        query_lower = re.sub(r'near\s+[^,]+', '', query_lower)

    # Extract job title (remaining text after removing location and distance)
    job_title = re.sub(r'\s+', ' ', query_lower.strip())
    job_title = re.sub(r'\b(jobs?|job)\b', '', job_title).strip()

    return job_title, location, distance


def construct_search_url(job_title: str, location: str, distance: int) -> str:
    """Construct the Monster.com search URL."""
    base_url = "https://www.monster.com/jobs/search"
    params = []

    if job_title:
        params.append(f"q={quote(job_title)}")
    if location:
        params.append(f"where={quote(location)}")
    if distance:
        params.append(f"rd={distance}")

    params.append("page=1")
    params.append("so=m.h.sh")

    return f"{base_url}?{'&'.join(params)}"


def scrape_monster_jobs(search_url: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Scrape job listings from Monster.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the job cards container
        jobs_container = soup.select_one('#card-scroll-container')
        if not jobs_container:
            return []

        # Find all job cards
        job_cards = jobs_container.select('div.job-search-results-style__JobCardWrap-sc-30547e5b-4')

        jobs = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                # Extract job title and link
                title_element = card.select_one('a[data-testid="jobTitle"]')
                if not title_element:
                    continue

                title = title_element.get_text(strip=True)
                relative_link = title_element.get('href', '')
                job_link = urljoin('https://www.monster.com', relative_link) if relative_link else ''

                # Extract company name
                company_element = card.select_one('span[data-testid="company"]')
                company = company_element.get_text(strip=True) if company_element else 'Company not specified'

                # Extract location
                location_element = card.select_one('span[data-testid="jobDetailLocation"]')
                location = location_element.get_text(strip=True) if location_element else 'Location not specified'

                # For now, use a simple summary instead of fetching from detail page
                summary = f"Position available in {location}. Click the link for full job details and requirements."

                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'summary': summary,
                    'link': job_link
                })

                # Add a small delay to be respectful to the server
                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing job card {i}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Error scraping Monster jobs: {str(e)}")
        return []

# MCP Tool using decorator
if mcp:
    @mcp.tool()
    def search_monster_jobs(query: str, max_jobs: int = 10) -> str:
        """Search for job listings on Monster.com using natural language queries.

        Args:
            query: Natural language job search query (e.g., 'hr admin jobs near winnetka within 5 miles')
            max_jobs: Maximum number of jobs to return (default: 10)

        Returns:
            JSON string containing job search results
        """
        try:
            # Parse the query
            job_title, location, distance = parse_query(query)

            # Construct search URL
            search_url = construct_search_url(job_title, location, distance)

            # Scrape jobs
            jobs = scrape_monster_jobs(search_url, max_jobs)

            # Format response
            result = {
                "query": query,
                "parsed": {
                    "job_title": job_title,
                    "location": location,
                    "distance": distance
                },
                "search_url": search_url,
                "jobs": jobs,
                "total_found": len(jobs)
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Job search failed: {str(e)}",
                "query": query
            })


class MCPServer:
    """MCP Server implementation for Monster Jobs."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "search_monster_jobs",
                "description": "Search for job listings on Monster.com using natural language queries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language job search query (e.g., 'hr admin jobs near winnetka within 5 miles')"
                        },
                        "max_jobs": {
                            "type": "integer",
                            "description": "Maximum number of jobs to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        self.resources = [
            {
                "uri": "monster://jobs/search",
                "name": "Monster Jobs Search",
                "description": "Access to Monster.com job search functionality",
                "mimeType": "application/json"
            }
        ]
    
    def handle_jsonrpc_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC 2.0 requests."""
        try:
            # Validate JSON-RPC 2.0 format
            if not isinstance(data, dict):
                return self._error_response(None, -32700, "Parse error")
            
            jsonrpc = data.get("jsonrpc")
            method = data.get("method")
            request_id = data.get("id")
            
            if jsonrpc != "2.0":
                return self._error_response(request_id, -32600, "Invalid Request")
            
            if not method:
                return self._error_response(request_id, -32600, "Invalid Request")
            
            # Route to appropriate handler
            if method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                params = data.get("params", {})
                return self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return self._handle_resources_list(request_id)
            elif method == "resources/read":
                params = data.get("params", {})
                return self._handle_resources_read(request_id, params)
            else:
                return self._error_response(request_id, -32601, "Method not found")
                
        except Exception as e:
            return self._error_response(request_id, -32603, f"Internal error: {str(e)}")
    
    def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.tools
            }
        }
    
    def _handle_tools_call(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name != "search_monster_jobs":
                return self._error_response(request_id, -32602, "Invalid tool name")
            
            # Extract parameters
            query = arguments.get("query")
            if not query:
                return self._error_response(request_id, -32602, "Missing required parameter: query")
            
            max_jobs = arguments.get("max_jobs", 10)
            
            # Execute job search
            job_title, location, distance = parse_query(query)
            search_url = construct_search_url(job_title, location, distance)
            jobs = scrape_monster_jobs(search_url, max_jobs)
            
            # Format response
            result = {
                "query": query,
                "parsed": {
                    "job_title": job_title,
                    "location": location,
                    "distance": distance
                },
                "search_url": search_url,
                "jobs": jobs,
                "total_found": len(jobs)
            }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            return self._error_response(request_id, -32603, f"Tool execution error: {str(e)}")
    
    def _handle_resources_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.resources
            }
        }
    
    def _handle_resources_read(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        try:
            uri = params.get("uri")
            
            if uri != "monster://jobs/search":
                return self._error_response(request_id, -32602, "Invalid resource URI")
            
            # Return information about the job search resource
            content = {
                "description": "Monster.com job search functionality",
                "capabilities": [
                    "Natural language query parsing",
                    "Job title, location, and distance extraction",
                    "Web scraping of Monster.com job listings",
                    "Structured job data return"
                ],
                "usage": "Use the search_monster_jobs tool to search for jobs",
                "example_query": "hr admin jobs near winnetka within 5 miles"
            }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            return self._error_response(request_id, -32603, f"Resource read error: {str(e)}")
    
    def _error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


# Global MCP server instance
mcp_server = MCPServer()


def create_mcp_blueprint():
    """Create Flask blueprint for MCP endpoints."""
    from flask import Blueprint
    
    mcp_bp = Blueprint('mcp', __name__)
    
    @mcp_bp.route('/mcp', methods=['POST'])
    def handle_mcp_request():
        """Handle MCP JSON-RPC requests."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }), 400
            
            response = mcp_server.handle_jsonrpc_request(data)
            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }), 500
    
    @mcp_bp.route('/mcp/health', methods=['GET'])
    def mcp_health():
        """MCP server health check."""
        return jsonify({
            "status": "healthy",
            "service": "Monster Jobs MCP Server",
            "protocol": "JSON-RPC 2.0",
            "tools": len(mcp_server.tools),
            "resources": len(mcp_server.resources)
        })
    
    return mcp_bp

