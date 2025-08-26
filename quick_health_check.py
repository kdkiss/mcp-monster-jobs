#!/usr/bin/env python3
"""
Minimal health check for MCP server deployment
"""

import requests
import json
import sys

def quick_health_check(base_url="http://localhost:8081"):
    """Quick health check for essential endpoints."""
    try:
        # Test basic health
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test MCP config
        response = requests.get(f"{base_url}/.well-known/mcp-config", timeout=10)
        if response.status_code == 200:
            print("✅ MCP config accessible")
        else:
            print(f"❌ MCP config failed: {response.status_code}")
            return False
        
        # Test MCP initialize
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
            "id": 1
        }
        response = requests.post(f"{base_url}/mcp", json=init_request, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                print("✅ MCP initialize working")
            else:
                print("❌ MCP initialize failed: no result")
                return False
        else:
            print(f"❌ MCP initialize failed: {response.status_code}")
            return False
        
        print("🎉 All essential checks passed!")
        return True
        
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == '__main__':
    success = quick_health_check()
    sys.exit(0 if success else 1)