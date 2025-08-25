#!/usr/bin/env python3
"""
Test script for Monster Jobs MCP server.
"""

import json
import requests
import sys

def test_mcp_server(base_url="http://localhost:5000"):
    """Test the MCP server endpoints."""
    
    print(f"Testing MCP server at {base_url}")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Test 2: Tools list
    print("\n2. Testing tools/list...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        response = requests.post(f"{base_url}/tools/list", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and "tools" in result["result"]:
                print("✓ Tools list passed")
                print(f"  Found {len(result['result']['tools'])} tools")
                for tool in result['result']['tools']:
                    print(f"    - {tool['name']}: {tool['description']}")
            else:
                print(f"✗ Tools list failed: Invalid response format")
                print(f"  Response: {result}")
                return False
        else:
            print(f"✗ Tools list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Tools list failed: {e}")
        return False
    
    # Test 3: Resources list
    print("\n3. Testing resources/list...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list"
        }
        response = requests.post(f"{base_url}/resources/list", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and "resources" in result["result"]:
                print("✓ Resources list passed")
                print(f"  Found {len(result['result']['resources'])} resources")
                for resource in result['result']['resources']:
                    print(f"    - {resource['name']}: {resource['description']}")
            else:
                print(f"✗ Resources list failed: Invalid response format")
                print(f"  Response: {result}")
                return False
        else:
            print(f"✗ Resources list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Resources list failed: {e}")
        return False
    
    # Test 4: Tool call (job search)
    print("\n4. Testing tools/call (job search)...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_jobs",
                "arguments": {
                    "query": "software engineer jobs near san francisco within 10 miles",
                    "max_jobs": 3
                }
            }
        }
        response = requests.post(f"{base_url}/tools/call", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and "content" in result["result"]:
                print("✓ Tool call passed")
                content = json.loads(result["result"]["content"][0]["text"])
                print(f"  Query: {content['query']}")
                print(f"  Parsed: {content['parsed']}")
                print(f"  Found {content['total_found']} jobs")
                if content['jobs']:
                    print("  Sample job:")
                    job = content['jobs'][0]
                    print(f"    Title: {job['title']}")
                    print(f"    Company: {job['company']}")
                    print(f"    Location: {job['location']}")
            else:
                print(f"✗ Tool call failed: Invalid response format")
                print(f"  Response: {result}")
                return False
        else:
            print(f"✗ Tool call failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Tool call failed: {e}")
        return False
    
    # Test 5: Test regular REST endpoint
    print("\n5. Testing regular REST endpoint...")
    try:
        payload = {
            "query": "test software engineer jobs",
            "max_jobs": 2
        }
        response = requests.post(f"{base_url}/search", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✓ REST endpoint passed")
            print(f"  Query: {result['query']}")
            print(f"  Found {result['total_found']} jobs")
            if result['jobs']:
                job = result['jobs'][0]
                print(f"  Sample job: {job['title']} at {job['company']}")
        else:
            print(f"✗ REST endpoint failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ REST endpoint failed: {e}")
        return False
    
    print("\n🎉 All MCP tests passed!")
    return True

if __name__ == "__main__":
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    success = test_mcp_server(base_url)
    sys.exit(0 if success else 1)

