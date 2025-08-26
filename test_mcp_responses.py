#!/usr/bin/env python3
"""
Test script to verify MCP server responses
"""

import json
import requests
import sys

def test_endpoint(url, method='GET', data=None, description=''):
    """Test an endpoint and return the response."""
    try:
        print(f"\n--- Testing {description} ---")
        print(f"URL: {url}")
        print(f"Method: {method}")
        
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            return True, response_json
        except json.JSONDecodeError:
            print(f"Response (raw): {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)

def main():
    base_url = "http://localhost:8081"
    
    # Test basic endpoints
    test_endpoint(f"{base_url}/", description="Root endpoint")
    test_endpoint(f"{base_url}/health", description="Health check")
    test_endpoint(f"{base_url}/status", description="Status check")
    test_endpoint(f"{base_url}/ping", description="Ping")
    test_endpoint(f"{base_url}/ready", description="Ready check")
    
    # Test MCP-specific endpoints
    test_endpoint(f"{base_url}/mcp/capabilities", description="MCP capabilities")
    test_endpoint(f"{base_url}/mcp/server-info", description="MCP server info")
    test_endpoint(f"{base_url}/mcp/scan", description="MCP scan GET")
    test_endpoint(f"{base_url}/.well-known/mcp-config", description="MCP config")
    test_endpoint(f"{base_url}/smithery", description="Smithery info")
    
    # Test MCP JSON-RPC endpoints
    initialize_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        },
        "id": 1
    }
    
    tools_list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    resources_list_request = {
        "jsonrpc": "2.0",
        "method": "resources/list",
        "params": {},
        "id": 3
    }
    
    test_endpoint(f"{base_url}/mcp", 'POST', initialize_request, "MCP Initialize")
    test_endpoint(f"{base_url}/mcp", 'POST', tools_list_request, "MCP Tools List")
    test_endpoint(f"{base_url}/mcp", 'POST', resources_list_request, "MCP Resources List")
    
    print("\n--- Test Complete ---")

if __name__ == '__main__':
    main()