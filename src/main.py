#!/usr/bin/env python3
"""
Monster Jobs MCP Server
A Model Context Protocol server for searching jobs on Monster.com
"""

import os
import re
import requests
import time
import json
import signal
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from typing import List, Dict, Tuple, Any

# Create Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/mcp*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/tools/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/resources/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/.well-known/*": {"origins": "*", "methods": ["GET", "OPTIONS"]}
})

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print('\nReceived signal, shutting down gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def parse_query(query: str) -> Tuple[str, str, int]:
    """Parse the user query to extract job title, location, and distance."""
    job_title = ""
    location = ""
    distance = 5

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

    # Extract job title
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

def scrape_monster_jobs(search_url: str, max_jobs: int = 10) -> List[Dict[str, str]]:
    """Scrape job listings from Monster.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        jobs_container = soup.select_one('#card-scroll-container')
        if not jobs_container:
            return []

        job_cards = jobs_container.select('div.job-search-results-style__JobCardWrap-sc-30547e5b-4')

        jobs = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                title_element = card.select_one('a[data-testid="jobTitle"]')
                if not title_element:
                    continue

                title = title_element.get_text(strip=True)
                relative_link = title_element.get('href', '')
                job_link = urljoin('https://www.monster.com', relative_link) if relative_link else ''

                company_element = card.select_one('span[data-testid="company"]')
                company = company_element.get_text(strip=True) if company_element else 'Company not specified'

                location_element = card.select_one('span[data-testid="jobDetailLocation"]')
                location = location_element.get_text(strip=True) if location_element else 'Location not specified'

                summary = f"Position available in {location}. Click the link for full job details and requirements."

                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'summary': summary,
                    'link': job_link
                })

                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing job card {i}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Error scraping Monster jobs: {str(e)}")
        return []

# MCP Server Implementation
class MonsterJobsMCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "search_jobs",
                "description": "Search for jobs on Monster.com based on a natural language query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query describing the job search (e.g., 'software engineer jobs near New York within 25 miles')"
                        },
                        "max_jobs": {
                            "type": "integer",
                            "description": "Maximum number of jobs to return (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
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
                "description": "Search jobs on Monster.com",
                "mimeType": "application/json"
            }
        ]

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        print(f"MCP Initialize called with params: {params}")  # Debug logging
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "listChanged": True
                },
                "prompts": {},
                "logging": {}
            },
            "serverInfo": {
                "name": "monster-jobs-mcp-server",
                "version": "1.0.0",
                "description": "MCP server for searching jobs on Monster.com"
            },
            "instructions": "This server provides job search capabilities for Monster.com. Use the search_jobs tool to find job listings based on natural language queries."
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        print("MCP Debug - tools/list called")  # Debug logging
        return {"tools": self.tools}

    def handle_resources_list(self) -> Dict[str, Any]:
        """Handle resources/list request."""
        print("MCP Debug - resources/list called")  # Debug logging
        return {"resources": self.resources}

    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        print(f"MCP Debug - tools/call params: {params}")  # Debug logging

        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "search_jobs":
            try:
                result = self._search_jobs_tool(tool_args)
                print(f"MCP Debug - tool result: {result}")  # Debug logging
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            except Exception as e:
                print(f"MCP Debug - tool error: {e}")  # Debug logging
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing tool: {str(e)}"
                        }
                    ],
                    "isError": True
                }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ],
                "isError": True
            }

    def handle_notifications_initialized(self, params: Dict[str, Any]) -> None:
        """Handle notifications/initialized request."""
        print("MCP Debug - notifications/initialized called")  # Debug logging
        # This is a notification, no response needed
        pass

    def _search_jobs_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search_jobs tool."""
        query = args.get("query", "")
        max_jobs = args.get("max_jobs", 10)

        if not query:
            return {"error": "Query parameter is required"}

        try:
            job_title, location, distance = parse_query(query)
            search_url = construct_search_url(job_title, location, distance)
            jobs = scrape_monster_jobs(search_url, max_jobs)

            return {
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
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

# Initialize MCP server
mcp_server = MonsterJobsMCPServer()

def handle_mcp_request():
    """Handle MCP JSON-RPC requests."""
    try:
        data = request.get_json(force=True)
        print(f"MCP Debug - Request data: {data}")  # Debug logging

        if not data:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error: No JSON data received"}, "id": None}), 400
        
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request: Missing or invalid jsonrpc version"}, "id": data.get("id")}), 400

        method = data.get("method")
        if not method:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request: Missing method"}, "id": data.get("id")}), 400
        
        params = data.get("params", {})
        req_id = data.get("id")

        print(f"MCP Debug - Method: {method}, Params: {params}")  # Debug logging

        # Handle all MCP methods on the /mcp endpoint
        if method == "initialize":
            result = mcp_server.handle_initialize(params)
        elif method == "notifications/initialized":
            # This is a notification, no response needed
            mcp_server.handle_notifications_initialized(params)
            return "", 204  # No content response for notifications
        elif method == "tools/list":
            result = mcp_server.handle_tools_list()
        elif method == "tools/call":
            result = mcp_server.handle_tools_call(params)
        elif method == "resources/list":
            result = mcp_server.handle_resources_list()
        else:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": req_id}), 404

        response_data = {"jsonrpc": "2.0", "result": result, "id": req_id}
        print(f"MCP Debug - Response: {response_data}")  # Debug logging
        return jsonify(response_data)

    except json.JSONDecodeError as e:
        print(f"MCP Debug - JSON decode error: {e}")  # Debug logging
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {str(e)}"}, "id": None}), 400
    except Exception as e:
        print(f"MCP Debug - Internal error: {e}")  # Debug logging
        error_id = data.get("id") if 'data' in locals() and data else None
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {str(e)}"}, "id": error_id}), 500

@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """MCP JSON-RPC endpoint."""
    return handle_mcp_request()

@app.route('/tools/list', methods=['POST'])
def tools_list():
    """List available tools."""
    return handle_mcp_request()

@app.route('/tools/call', methods=['POST'])
def tools_call():
    """Call a tool."""
    return handle_mcp_request()

@app.route('/resources/list', methods=['POST'])
def resources_list():
    """List available resources."""
    return handle_mcp_request()

@app.route('/jsonrpc', methods=['POST'])
def jsonrpc_endpoint():
    """Alternative JSON-RPC endpoint for MCP compatibility."""
    return handle_mcp_request()

@app.route('/.well-known/mcp-config', methods=['GET'])
def mcp_config():
    """MCP configuration endpoint for service discovery."""
    print("MCP Config endpoint called")  # Debug logging

    # Get the actual host from the request
    host = request.host_url.rstrip('/')
    config = {
        "mcpServers": {
            "monster-jobs": {
                "command": "python",
                "args": ["src/main.py"],
                "env": {
                    "PORT": "8081"
                },
                "transport": {
                    "type": "http",
                    "host": "localhost",
                    "port": 8081
                }
            }
        }
    }
    print(f"MCP Config response: {config}")  # Debug logging
    return jsonify(config)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for basic connectivity testing."""
    return jsonify({
        "name": "Monster Jobs MCP Server",
        "version": "1.0.0",
        "description": "A Model Context Protocol server for searching jobs on Monster.com",
        "mcp_endpoints": [
            "/mcp",
            "/initialize", 
            "/tools/list",
            "/tools/call",
            "/resources/list",
            "/.well-known/mcp-config"
        ],
        "status": "ready"
    })

@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize endpoint for MCP compatibility."""
    return handle_mcp_request()

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify server is responding."""
    return jsonify({
        "status": "ok",
        "message": "MCP server is running",
        "endpoints": [
            "/mcp",
            "/tools/list",
            "/tools/call",
            "/resources/list",
            "/.well-known/mcp-config",
            "/health"
        ]
    })

@app.route('/search', methods=['POST'])
def search_jobs():
    """Search for jobs on Monster.com based on user query."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter is required'}), 400

        query = data['query']
        max_jobs = data.get('max_jobs', 10)

        job_title, location, distance = parse_query(query)
        search_url = construct_search_url(job_title, location, distance)
        jobs = scrape_monster_jobs(search_url, max_jobs)

        return jsonify({
            'query': query,
            'parsed': {
                'job_title': job_title,
                'location': location,
                'distance': distance
            },
            'search_url': search_url,
            'jobs': jobs,
            'total_found': len(jobs)
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/ready', methods=['GET'])
def readiness_probe():
    """Readiness probe endpoint for container orchestration."""
    return jsonify({'status': 'ready'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy', 
        'service': 'Monster Jobs MCP Server',
        'version': '1.0.0',
        'mcp_enabled': True,
        'endpoints': {
            'mcp': '/mcp',
            'initialize': '/initialize',
            'tools_list': '/tools/list',
            'tools_call': '/tools/call', 
            'resources_list': '/resources/list',
            'config': '/.well-known/mcp-config'
        },
        'timestamp': time.time()
    })

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8081))  # Default to 8081 for Smithery
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"Starting MCP server on {host}:{port}")  # Debug logging
        print(f"Environment variables:")
        print(f"  PORT: {os.environ.get('PORT', 'not set')}")
        print(f"  HOST: {os.environ.get('HOST', 'not set')}")
        print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
        
        print("MCP server endpoints available:")
        print(f"  - /mcp (MCP JSON-RPC)")
        print(f"  - /tools/list (List tools)")
        print(f"  - /tools/call (Call tools)")
        print(f"  - /resources/list (List resources)")
        print(f"  - /.well-known/mcp-config (MCP configuration)")
        print(f"  - /health (Health check)")
        
        # Test basic Flask app functionality
        print("Testing Flask app configuration...")
        with app.app_context():
            print("✓ Flask app context initialized successfully")
        
        print(f"Starting Flask server...")
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except Exception as e:
        print(f"ERROR: Failed to start MCP server: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
