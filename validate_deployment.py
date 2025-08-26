#!/usr/bin/env python3
"""
Comprehensive deployment validation for Monster Jobs MCP Server
This script validates all essential functionality for Smithery deployment.
"""

import requests
import json
import time
import sys
import os

def validate_basic_connectivity(base_url):
    """Test basic server connectivity."""
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✓ Basic connectivity: OK")
            return True
        else:
            print(f"✗ Basic connectivity failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Basic connectivity failed: {e}")
        return False

def validate_readiness(base_url):
    """Test readiness probe."""
    try:
        response = requests.get(f"{base_url}/ready", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ready':
                print("✓ Readiness probe: OK")
                return True
            else:
                print(f"✗ Readiness probe failed: unexpected response {data}")
                return False
        else:
            print(f"✗ Readiness probe failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Readiness probe failed: {e}")
        return False

def validate_health_check(base_url):
    """Test health check endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✓ Health check: OK")
                return True
            else:
                print(f"✗ Health check failed: unexpected response {data}")
                return False
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def validate_mcp_initialization(base_url):
    """Test MCP initialization."""
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
        response = requests.post(f"{base_url}/mcp", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "serverInfo" in data["result"]:
                print("✓ MCP initialization: OK")
                return True
            else:
                print(f"✗ MCP initialization failed: unexpected response {data}")
                return False
        else:
            print(f"✗ MCP initialization failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP initialization failed: {e}")
        return False

def validate_tools_discovery(base_url):
    """Test tools discovery."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        response = requests.post(f"{base_url}/mcp", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                if len(tools) > 0 and any(tool.get("name") == "search_jobs" for tool in tools):
                    print(f"✓ Tools discovery: OK ({len(tools)} tools found)")
                    return True
                else:
                    print(f"✗ Tools discovery failed: no search_jobs tool found")
                    return False
            else:
                print(f"✗ Tools discovery failed: unexpected response {data}")
                return False
        else:
            print(f"✗ Tools discovery failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Tools discovery failed: {e}")
        return False

def validate_ping(base_url):
    """Test ping endpoint."""
    try:
        response = requests.get(f"{base_url}/ping", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'pong':
                print("✓ Ping endpoint: OK")
                return True
            else:
                print(f"✗ Ping endpoint failed: unexpected response {data}")
                return False
        else:
            print(f"✗ Ping endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ping endpoint failed: {e}")
        return False

def validate_scan_endpoint(base_url):
    """Test MCP scan endpoint."""
    try:
        response = requests.get(f"{base_url}/mcp/scan", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "capabilities" in data and "tools" in data["capabilities"]:
                tools = data["capabilities"]["tools"].get("available", [])
                if any(tool.get("name") == "search_jobs" for tool in tools):
                    print("✓ MCP scan endpoint: OK")
                    return True
                else:
                    print(f"✗ MCP scan endpoint failed: search_jobs tool not found")
                    return False
            else:
                print(f"✗ MCP scan endpoint failed: missing capabilities")
                return False
        else:
            print(f"✗ MCP scan endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP scan endpoint failed: {e}")
        return False
    """Test MCP configuration endpoint."""
    try:
        response = requests.get(f"{base_url}/.well-known/mcp-config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "mcpServers" in data:
                print("✓ MCP configuration: OK")
                return True
            else:
                print(f"✗ MCP configuration failed: unexpected response {data}")
                return False
        else:
            print(f"✗ MCP configuration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP configuration failed: {e}")
        return False

def validate_mcp_config(base_url):
    """Test MCP configuration endpoint."""
    try:
        response = requests.get(f"{base_url}/.well-known/mcp-config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "mcpServers" in data:
                print("✓ MCP configuration: OK")
                return True
            else:
                print(f"✗ MCP configuration failed: unexpected response {data}")
                return False
        else:
            print(f"✗ MCP configuration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP configuration failed: {e}")
        return False

def run_comprehensive_validation(base_url):
    """Run all validation tests."""
    print(f"Running comprehensive validation for: {base_url}")
    print("=" * 60)
    
    tests = [
        ("Basic Connectivity", validate_basic_connectivity),
        ("Ping Endpoint", validate_ping),
        ("Readiness Probe", validate_readiness),
        ("Health Check", validate_health_check),
        ("MCP Scan Endpoint", validate_scan_endpoint),
        ("MCP Initialization", validate_mcp_initialization),
        ("Tools Discovery", validate_tools_discovery),
        ("MCP Configuration", validate_mcp_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func(base_url):
            passed += 1
        else:
            # Add some debug info for failed tests
            try:
                response = requests.get(f"{base_url}/", timeout=5)
                print(f"  Debug: Server responded with {response.status_code}")
            except:
                print(f"  Debug: Server appears to be unreachable")
    
    print("\n" + "=" * 60)
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Server is ready for deployment.")
        return True
    else:
        print("✗ Some tests failed. Server may not be ready for deployment.")
        return False

if __name__ == "__main__":
    # Default to localhost, but allow override via environment variable or argument
    base_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:8081')
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("Monster Jobs MCP Server - Deployment Validation")
    print(f"Target URL: {base_url}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = run_comprehensive_validation(base_url)
    sys.exit(0 if success else 1)