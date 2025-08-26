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

# JSON response helper
def safe_jsonify(data, status_code=200):
    """Safely serialize data to JSON response with error handling."""
    try:
        # Test serialization first
        json.dumps(data)
        response = jsonify(data)
        response.status_code = status_code
        return response
    except Exception as e:
        print(f"[JSON] Serialization error: {e}")
        error_response = {
            "error": "JSON serialization failed",
            "message": str(e),
            "type": "SerializationError"
        }
        response = jsonify(error_response)
        response.status_code = 500
        return response

# Create Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/mcp*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/tools/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/resources/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]},
    r"/.well-known/*": {"origins": "*", "methods": ["GET", "OPTIONS"]}
})

# Add error handling wrapper for all routes
@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler to ensure proper JSON responses."""
    print(f"[ERROR] Unhandled exception: {e}")
    import traceback
    traceback.print_exc()
    
    # Return JSON error response
    return jsonify({
        "error": "Internal server error",
        "message": str(e),
        "type": type(e).__name__,
        "status": "error"
    }), 500

# Add basic request logging for debugging
@app.before_request
def log_request():
    # Minimal logging for production deployment - only log critical endpoints
    if request.path in ['/health', '/ready', '/ping', '/status']:
        return  # Skip logging for health checks to reduce noise
    if request.path.startswith('/mcp') or request.path.startswith('/scan'):
        print(f"[MCP] {request.method} {request.path}")

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

def get_server_config():
    """Get server configuration from environment or query parameters."""
    config = {
        'max_jobs': int(request.args.get('maxJobs', os.environ.get('MAX_JOBS', 10))),
        'timeout': int(request.args.get('timeout', os.environ.get('TIMEOUT', 15)))
    }
    
    # Validate configuration values
    config['max_jobs'] = max(1, min(50, config['max_jobs']))
    config['timeout'] = max(5, min(30, config['timeout']))
    
    return config

def scrape_monster_jobs(search_url: str, max_jobs: int = 10, timeout: int = 15) -> List[Dict[str, str]]:
    """Scrape job listings from Monster.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=timeout)
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
        # Support both old and new protocol versions
        client_version = params.get("protocolVersion", "2024-11-05")
        supported_versions = ["2024-11-05", "2025-06-18"]
        
        # Use the client's version if it's supported, otherwise use our default
        protocol_version = client_version if client_version in supported_versions else "2024-11-05"
        
        return {
            "protocolVersion": protocol_version,
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
        return {"tools": self.tools}

    def handle_resources_list(self) -> Dict[str, Any]:
        """Handle resources/list request."""
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
        print(f"[MCP] Initialization completed, params: {params}")
        # This is a notification, no response needed
        pass

    def _search_jobs_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search_jobs tool."""
        query = args.get("query", "")
        max_jobs = args.get("max_jobs", 10)

        if not query:
            return {"error": "Query parameter is required"}

        try:
            # Get server configuration
            config = get_server_config()
            
            # Use config values if not specified in tool args
            if max_jobs == 10:  # Default value, use config
                max_jobs = config['max_jobs']
            
            job_title, location, distance = parse_query(query)
            search_url = construct_search_url(job_title, location, distance)
            jobs = scrape_monster_jobs(search_url, max_jobs, config['timeout'])

            return {
                "query": query,
                "parsed": {
                    "job_title": job_title,
                    "location": location,
                    "distance": distance
                },
                "search_url": search_url,
                "jobs": jobs,
                "total_found": len(jobs),
                "config": config
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

# Initialize MCP server
mcp_server = MonsterJobsMCPServer()

def handle_mcp_request():
    """Handle MCP JSON-RPC requests with improved error handling and timeouts."""
    try:
        # Set a reasonable timeout for request processing
        start_time = time.time()
        
        # Handle empty request body
        if request.content_length == 0:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error: Empty request body"}, "id": None}), 400
        
        data = request.get_json(force=True)

        if not data:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error: No JSON data received"}, "id": None}), 400
        
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request: Missing or invalid jsonrpc version"}, "id": data.get("id")}), 400

        method = data.get("method")
        if not method:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request: Missing method"}, "id": data.get("id")}), 400
        
        params = data.get("params", {})
        req_id = data.get("id")

        # Handle all MCP methods on the /mcp endpoint
        result = None
        try:
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
        except Exception as method_error:
            print(f"[MCP] Method execution error: {method_error}")
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Method execution error: {str(method_error)}"}, "id": req_id}), 500

        # Check for timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > 25:  # 25 second timeout
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Request timeout"}, "id": req_id}), 504

        # Ensure result is JSON serializable
        try:
            json.dumps(result)
        except TypeError as e:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Result serialization error: {str(e)}"}, "id": req_id}), 500

        response_data = {"jsonrpc": "2.0", "result": result, "id": req_id}
        return jsonify(response_data)

    except json.JSONDecodeError as e:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {str(e)}"}, "id": None}), 400
    except Exception as e:
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
        },
        "serverInfo": {
            "name": "monster-jobs-mcp-server",
            "version": "1.0.0",
            "description": "MCP server for searching jobs on Monster.com",
            "capabilities": {
                "tools": ["search_jobs"],
                "resources": ["monster://jobs/search"]
            }
        },
        "endpoints": {
            "main": "/mcp",
            "health": "/health",
            "status": "/status",
            "ping": "/ping"
        }
    }
    return jsonify(config)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for basic connectivity testing."""
    try:
        return jsonify({
            "name": "Monster Jobs MCP Server",
            "version": "1.0.0",
            "description": "A Model Context Protocol server for searching jobs on Monster.com",
            "protocol": "mcp",
            "protocolVersion": "2024-11-05",
            "transport": "http", 
            "mcp_endpoints": [
                "/mcp",
                "/initialize", 
                "/tools/list",
                "/tools/call",
                "/resources/list",
                "/.well-known/mcp-config",
                "/mcp/scan",
                "/mcp/capabilities"
            ],
            "utility_endpoints": [
                "/health",
                "/ready", 
                "/ping",
                "/status",
                "/scan",
                "/smithery"
            ],
            "capabilities": {
                "tools": ["search_jobs"],
                "resources": ["monster://jobs/search"]
            },
            "status": "ready",
            "healthy": True,
            "scannable": True,
            "testable": True,
            "deployment": {
                "platform": "smithery",
                "ready": True
            }
        })
    except Exception as e:
        print(f"[ROOT] Error: {e}")
        return jsonify({
            "error": "Root endpoint error",
            "message": str(e)
        }), 500

@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize endpoint for MCP compatibility."""
    return handle_mcp_request()

@app.route('/mcp/server-info', methods=['GET'])
def mcp_server_info():
    """Return basic MCP server information."""
    try:
        info = {
            "name": "monster-jobs-mcp-server",
            "version": "1.0.0",
            "description": "MCP server for searching jobs on Monster.com",
            "protocol": "mcp",
            "protocolVersion": "2024-11-05",
            "transport": "http",
            "status": "ready",
            "healthy": True
        }
        return jsonify(info)
    except Exception as e:
        print(f"[SERVER-INFO] Error: {e}")
        return jsonify({
            "error": "Failed to get server info",
            "message": str(e)
        }), 500

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

@app.route('/mcp/scan', methods=['GET', 'POST'])
def mcp_scan():
    """Ultra-fast scanning endpoint for deployment validation."""
    # Immediate response without any processing delays
    if request.method == 'GET':
        return jsonify({
            "name": "monster-jobs-mcp-server",
            "version": "1.0.0",
            "status": "ready",
            "healthy": True,
            "scannable": True,
            "protocol": "mcp",
            "transport": "http",
            "capabilities": {
                "tools": {
                    "available": True,
                    "count": 1
                },
                "resources": {
                    "available": True,
                    "count": 1
                }
            },
            "endpoints": {
                "main": "/mcp",
                "health": "/health",
                "config": "/.well-known/mcp-config"
            },
            "testConfig": {
                "available": True,
                "configFile": ".smithery-test.yaml"
            }
        })
    else:
        # Handle POST as JSON-RPC with minimal processing
        return handle_mcp_request()

@app.route('/metadata', methods=['GET'])
def metadata():
    """Return server metadata including test configuration information."""
    try:
        metadata_info = {
            "server": {
                "name": "monster-jobs-mcp-server",
                "version": "1.0.0",
                "description": "MCP server for searching jobs on Monster.com",
                "protocol": "mcp",
                "protocolVersion": "2025-06-18"
            },
            "testing": {
                "configFiles": [
                    ".smithery-test.yaml",
                    "test.yaml",
                    "test-config.yaml"
                ],
                "configEndpoints": [
                    "/test-config",
                    "/.smithery-test",
                    "/metadata"
                ],
                "testableEndpoints": [
                    "/health",
                    "/ping",
                    "/ready",
                    "/status",
                    "/mcp",
                    "/.well-known/mcp-config",
                    "/mcp/capabilities",
                    "/smithery"
                ]
            },
            "scanning": {
                "supported": True,
                "endpoints": [
                    "/mcp/scan",
                    "/scan",
                    "/mcp/capabilities",
                    "/smithery"
                ],
                "timeout": 30,
                "format": "json"
            },
            "capabilities": {
                "tools": ["search_jobs"],
                "resources": ["monster://jobs/search"],
                "protocols": ["mcp", "jsonrpc", "rest"]
            }
        }
        return jsonify(metadata_info)
    except Exception as e:
        print(f"[METADATA] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/.smithery-test', methods=['GET'])
def smithery_test_config():
    """Return Smithery-specific test configuration."""
    try:
        config = {
            "version": "1.0",
            "name": "monster-jobs-mcp-server",
            "description": "Test configuration for Monster Jobs MCP Server",
            "tests": [
                {
                    "name": "health_check",
                    "type": "http",
                    "endpoint": "/health",
                    "method": "GET",
                    "expected": {
                        "status": 200,
                        "response": {
                            "status": "healthy",
                            "service": "Monster Jobs MCP Server",
                            "version": "1.0.0"
                        }
                    }
                },
                {
                    "name": "mcp_initialize",
                    "type": "jsonrpc",
                    "endpoint": "/mcp",
                    "method": "POST",
                    "payload": {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
                        "id": 1
                    },
                    "expected": {
                        "status": 200,
                        "response": {
                            "jsonrpc": "2.0",
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "serverInfo": {
                                    "name": "monster-jobs-mcp-server"
                                }
                            }
                        }
                    }
                }
            ],
            "scan_config": {
                "timeout": 30,
                "retry_attempts": 3,
                "endpoints": ["/mcp/scan", "/mcp/capabilities", "/.well-known/mcp-config"]
            }
        }
        return jsonify(config)
    except Exception as e:
        print(f"[SMITHERY-TEST] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-config', methods=['GET'])
def test_config():
    """Return test configuration for scanning tools."""
    try:
        config = {
            "tests": {
                "connectivity": [
                    {
                        "name": "health_check",
                        "endpoint": "/health",
                        "method": "GET",
                        "expectedStatus": 200,
                        "expectedResponse": {"status": "healthy"}
                    },
                    {
                        "name": "ping_test",
                        "endpoint": "/ping",
                        "method": "GET",
                        "expectedStatus": 200,
                        "expectedResponse": {"status": "pong"}
                    },
                    {
                        "name": "ready_check",
                        "endpoint": "/ready",
                        "method": "GET",
                        "expectedStatus": 200,
                        "expectedResponse": {"status": "ready"}
                    }
                ],
                "mcp_protocol": [
                    {
                        "name": "mcp_initialize",
                        "endpoint": "/mcp",
                        "method": "POST",
                        "contentType": "application/json",
                        "payload": {
                            "jsonrpc": "2.0",
                            "method": "initialize",
                            "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
                            "id": 1
                        },
                        "expectedStatus": 200
                    },
                    {
                        "name": "tools_list",
                        "endpoint": "/mcp",
                        "method": "POST",
                        "contentType": "application/json",
                        "payload": {
                            "jsonrpc": "2.0",
                            "method": "tools/list",
                            "params": {},
                            "id": 2
                        },
                        "expectedStatus": 200
                    }
                ],
                "service_discovery": [
                    {
                        "name": "mcp_config",
                        "endpoint": "/.well-known/mcp-config",
                        "method": "GET",
                        "expectedStatus": 200
                    },
                    {
                        "name": "capabilities_scan",
                        "endpoint": "/mcp/capabilities",
                        "method": "GET",
                        "expectedStatus": 200
                    }
                ]
            },
            "scanning": {
                "timeout": 30,
                "retryAttempts": 3,
                "retryDelay": 2,
                "validateJson": True,
                "checkProtocolCompliance": True,
                "primaryEndpoint": "/mcp/scan",
                "fallbackEndpoints": ["/mcp/capabilities", "/smithery", "/.well-known/mcp-config"]
            }
        }
        return jsonify(config)
    except Exception as e:
        print(f"[TEST-CONFIG] Error: {e}")
        return jsonify({
            "error": "Failed to get test configuration",
            "message": str(e)
        }), 500

@app.route('/scan', methods=['GET', 'POST'])
def universal_scan():
    """Ultra-fast universal scanning endpoint."""
    # Immediate response - no try/catch to avoid any delays
    return jsonify({
        "server": {
            "name": "monster-jobs-mcp-server",
            "version": "1.0.0",
            "status": "ready",
            "healthy": True,
            "type": "mcp-server",
            "scannable": True
        },
        "protocol": {
            "name": "mcp",
            "version": "2024-11-05",
            "transport": "http"
        },
        "capabilities": {
            "tools": {"available": True, "count": 1},
            "resources": {"available": True, "count": 1}
        },
        "endpoints": {
            "main": "/mcp",
            "health": "/health",
            "scan": "/scan"
        },
        "testConfig": {
            "available": True,
            "configFile": ".smithery-test.yaml"
        },
        "deployment": {
            "platform": "smithery",
            "ready": True
        }
    })

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    """Return MCP server capabilities for scanning."""
    try:
        print("[CAPABILITIES] MCP capabilities request received")
        
        capabilities = {
            "protocolVersion": "2025-06-18",
            "serverInfo": {
                "name": "monster-jobs-mcp-server",
                "version": "1.0.0",
                "description": "MCP server for searching jobs on Monster.com"
            },
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
            "tools": [
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
            ],
            "resources": [
                {
                    "uri": "monster://jobs/search",
                    "name": "Monster Jobs Search",
                    "description": "Search jobs on Monster.com",
                    "mimeType": "application/json"
                }
            ]
        }
        
        # Validate JSON serialization
        json.dumps(capabilities)
        print("[CAPABILITIES] Successfully prepared capabilities response")
        
        return jsonify(capabilities)
        
    except Exception as e:
        print(f"[CAPABILITIES] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": "Failed to retrieve capabilities",
            "message": str(e),
            "status": "error"
        }), 500

@app.route('/smithery', methods=['GET'])
def smithery_info():
    """Smithery-specific endpoint providing comprehensive server information."""
    return jsonify({
        "name": "monster-jobs-mcp-server",
        "version": "1.0.0",
        "description": "Search job listings on Monster.com using natural language queries",
        "type": "mcp-server",
        "protocol": "mcp",
        "transport": "http",
        "port": 8081,
        "status": "ready",
        "capabilities": {
            "tools": [
                {
                    "name": "search_jobs",
                    "description": "Search for jobs on Monster.com based on a natural language query",
                    "type": "function"
                }
            ],
            "resources": [
                {
                    "uri": "monster://jobs/search",
                    "name": "Monster Jobs Search",
                    "type": "search"
                }
            ]
        },
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "status": "/status",
            "ping": "/ping",
            "root": "/"
        },
        "testable": True,
        "production_ready": True
    })

@app.route('/status', methods=['GET'])
def status():
    """Simple status endpoint for quick server validation."""
    return jsonify({'status': 'ok', 'service': 'monster-jobs-mcp-server', 'ready': True}), 200

@app.route('/ping', methods=['GET'])
def ping():
    """Quick ping endpoint for connectivity testing."""
    return jsonify({'status': 'pong'}), 200

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
        'version': '1.0.0'
    }), 200

# Catch-all route for unknown paths (should be last)
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path):
    """Catch-all endpoint for unknown routes to help with scanning."""
    try:
        # Return information about available endpoints
        return jsonify({
            "error": "Endpoint not found",
            "path": path,
            "method": request.method,
            "available_endpoints": {
                "mcp": ["/mcp", "/mcp/capabilities", "/mcp/scan", "/mcp/server-info"],
                "discovery": ["/.well-known/mcp-config", "/smithery"],
                "health": ["/health", "/ping", "/ready", "/status"],
                "testing": ["/test-config", "/scan"]
            },
            "suggestion": "Check available endpoints above"
        }), 404
    except Exception as e:
        return jsonify({
            "error": "Catch-all endpoint error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8081))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"[STARTUP] Starting Monster Jobs MCP Server on {host}:{port}")
        
        # Use Waitress for production deployment with optimized settings
        try:
            from waitress import serve
            print(f"[STARTUP] Using Waitress WSGI server")
            # Optimized Waitress configuration for fast startup
            serve(
                app, 
                host=host, 
                port=port, 
                threads=4,
                connection_limit=100,
                cleanup_interval=10,
                channel_timeout=30,
                log_socket_errors=False,  # Reduce logging noise
                ident=None  # Remove server identification header
            )
        except ImportError:
            print(f"[STARTUP] Using Flask development server")
            # Optimized Flask configuration for deployment
            app.run(
                host=host, 
                port=port, 
                debug=False, 
                threaded=True, 
                use_reloader=False,
                processes=1,
                load_dotenv=False  # Skip .env loading for faster startup
            )
        
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        # Don't print full traceback in production to avoid timeout issues
        sys.exit(1)
