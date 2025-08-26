#!/usr/bin/env python3
"""
Debug script to simulate scanning and identify serialization issues
"""

import json
import requests
import sys
import time

def test_endpoint_safe(url, method='GET', data=None):
    """Test an endpoint and safely handle any response."""
    try:
        print(f"\\n--- Testing {url} ({method}) ---")
        
        if method == 'GET':
            response = requests.get(url, timeout=5)
        else:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Try to get JSON response
        try:
            json_data = response.json()
            print(f"JSON Response: {json.dumps(json_data, indent=2)[:500]}...")
            
            # Test if response can be serialized again
            try:
                json.dumps(json_data)
                print("✓ JSON serialization test passed")
            except Exception as ser_error:
                print(f"✗ JSON serialization test failed: {ser_error}")
                return False
                
        except json.JSONDecodeError:
            print(f"Raw Response: {response.text[:200]}...")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def simulate_smithery_scan():
    """Simulate what Smithery might be doing during scanning."""
    base_url = "http://localhost:8081"
    
    print("=== Simulating Smithery Scanning Process ===")
    
    # Test basic connectivity
    print("\\n1. Basic Connectivity Tests")
    test_endpoint_safe(f"{base_url}/")
    test_endpoint_safe(f"{base_url}/health")
    test_endpoint_safe(f"{base_url}/ping")
    test_endpoint_safe(f"{base_url}/ready")
    
    # Test MCP endpoints
    print("\\n2. MCP Endpoint Tests")
    test_endpoint_safe(f"{base_url}/.well-known/mcp-config")
    test_endpoint_safe(f"{base_url}/mcp/capabilities")
    test_endpoint_safe(f"{base_url}/mcp/server-info")
    test_endpoint_safe(f"{base_url}/smithery")
    test_endpoint_safe(f"{base_url}/scan")
    test_endpoint_safe(f"{base_url}/mcp/scan")
    test_endpoint_safe(f"{base_url}/test-config")
    
    # Test MCP protocol
    print("\\n3. MCP Protocol Tests")
    
    # Initialize
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
        "id": 1
    }
    test_endpoint_safe(f"{base_url}/mcp", 'POST', init_request)
    
    # Tools list
    tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    test_endpoint_safe(f"{base_url}/mcp", 'POST', tools_request)
    
    # Resources list
    resources_request = {
        "jsonrpc": "2.0",
        "method": "resources/list",
        "params": {},
        "id": 3
    }
    test_endpoint_safe(f"{base_url}/mcp", 'POST', resources_request)
    
    # Test some potential edge cases
    print("\\n4. Edge Case Tests")
    test_endpoint_safe(f"{base_url}/unknown-endpoint")
    
    # Empty JSON-RPC request
    empty_request = {}
    test_endpoint_safe(f"{base_url}/mcp", 'POST', empty_request)
    
    # Invalid JSON-RPC request
    invalid_request = {"invalid": "request"}
    test_endpoint_safe(f"{base_url}/mcp", 'POST', invalid_request)
    
    print("\\n=== Scan Simulation Complete ===")

if __name__ == '__main__':
    print("Starting debug scan simulation...")
    time.sleep(1)  # Give server time to be ready
    simulate_smithery_scan()