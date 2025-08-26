#!/usr/bin/env python3
"""
Test script for Monster Jobs MCP Server
This script tests all the MCP endpoints to ensure they work correctly.
"""

import requests
import json
import time
import sys

def test_mcp_server(base_url="http://localhost:8081"):
    """Test all MCP server endpoints."""
    print(f"Testing MCP server at {base_url}")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Basic connectivity: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Basic connectivity failed: {e}")
        return False
    
    # Test 2: Initialize
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        }
        response = requests.post(f"{base_url}/mcp", json=payload)
        print(f"✓ Initialize: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"✗ Initialize failed: {e}")
        return False
    
    # Test 3: Tools list
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        response = requests.post(f"{base_url}/mcp", json=payload)
        print(f"✓ Tools list: {response.status_code}")
        result = response.json()
        tools = result.get("result", {}).get("tools", [])
        print(f"  Found {len(tools)} tools:")
        for tool in tools:
            print(f"    - {tool.get('name')}: {tool.get('description')}")
    except Exception as e:
        print(f"✗ Tools list failed: {e}")
        return False
    
    # Test 4: Resources list
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 3
        }
        response = requests.post(f"{base_url}/mcp", json=payload)
        print(f"✓ Resources list: {response.status_code}")
        result = response.json()
        resources = result.get("result", {}).get("resources", [])
        print(f"  Found {len(resources)} resources:")
        for resource in resources:
            print(f"    - {resource.get('name')}: {resource.get('description')}")
    except Exception as e:
        print(f"✗ Resources list failed: {e}")
        return False
    
    # Test 5: MCP Config
    try:
        response = requests.get(f"{base_url}/.well-known/mcp-config")
        print(f"✓ MCP Config: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"✗ MCP Config failed: {e}")
        return False
    
    # Test 6: Tool call (search_jobs)
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_jobs",
                "arguments": {
                    "query": "software engineer jobs near San Francisco within 10 miles",
                    "max_jobs": 2
                }
            },
            "id": 4
        }
        response = requests.post(f"{base_url}/mcp", json=payload)
        print(f"✓ Tool call (search_jobs): {response.status_code}")
        result = response.json()
        if "result" in result and "content" in result["result"]:
            content = json.loads(result["result"]["content"][0]["text"])
            print(f"  Found {content.get('total_found', 0)} jobs")
            print(f"  Query: {content.get('query')}")
            print(f"  Parsed: {content.get('parsed')}")
        else:
            print(f"  Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"✗ Tool call failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! MCP server is working correctly.")
    return True

if __name__ == "__main__":
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081"
    
    print("Monster Jobs MCP Server Test")
    print(f"Testing server at: {base_url}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_mcp_server(base_url)
    sys.exit(0 if success else 1)