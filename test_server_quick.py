#!/usr/bin/env python3
"""
Quick server test for MCP deployment validation
"""

import requests
import json
import time
import sys

def test_server_quick(base_url="http://localhost:8081"):
    """Quick test of essential server functions."""
    tests_passed = 0
    total_tests = 5
    
    print("🔍 Running quick server tests...")
    
    try:
        # Test 1: Health check
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            tests_passed += 1
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
        
        # Test 2: MCP config
        print("2. Testing MCP config endpoint...")
        response = requests.get(f"{base_url}/.well-known/mcp-config", timeout=5)
        if response.status_code == 200:
            print("   ✅ MCP config accessible")
            tests_passed += 1
        else:
            print(f"   ❌ MCP config failed: {response.status_code}")
        
        # Test 3: Scan endpoint
        print("3. Testing scan endpoint...")
        response = requests.get(f"{base_url}/scan", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "server" in data and data["server"]["name"] == "monster-jobs-mcp-server":
                print("   ✅ Scan endpoint working")
                tests_passed += 1
            else:
                print("   ❌ Scan endpoint invalid response")
        else:
            print(f"   ❌ Scan endpoint failed: {response.status_code}")
        
        # Test 4: MCP capabilities
        print("4. Testing MCP capabilities...")
        response = requests.get(f"{base_url}/mcp/capabilities", timeout=5)
        if response.status_code == 200:
            print("   ✅ MCP capabilities working")
            tests_passed += 1
        else:
            print(f"   ❌ MCP capabilities failed: {response.status_code}")
        
        # Test 5: Test config endpoint
        print("5. Testing test config endpoint...")
        response = requests.get(f"{base_url}/test-config", timeout=5)
        if response.status_code == 200:
            print("   ✅ Test config available")
            tests_passed += 1
        else:
            print(f"   ❌ Test config failed: {response.status_code}")
        
        print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed >= 4:
            print("🎉 Server is ready for deployment!")
            return True
        else:
            print("⚠️  Server may have issues, but might still deploy")
            return tests_passed >= 3
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        return False

if __name__ == '__main__':
    success = test_server_quick()
    sys.exit(0 if success else 1)