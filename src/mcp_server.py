"""
MCP (Model Context Protocol) server implementation for Monster Jobs.
This module implements the JSON-RPC 2.0 protocol required by MCP.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify
from src.routes.monster_jobs import parse_query, construct_search_url, scrape_monster_jobs


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

