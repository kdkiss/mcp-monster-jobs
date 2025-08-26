#!/usr/bin/env python3
"""
Ultra-fast deployment scanning test
Tests that all endpoints respond within milliseconds
"""

import requests
import time
import sys

def test_instant_responses(base_url="http://localhost:8081"):
    """Test that all scanning endpoints respond instantly."""
    print("⚡ Testing ultra-fast endpoint responses...")
    
    # Critical scanning endpoints that must respond instantly
    critical_endpoints = [
        ("/health", "Health check"),
        ("/ping", "Ping test"),  
        ("/ready", "Readiness probe"),
        ("/status", "Status check"),
        ("/scan", "Universal scan"),
        ("/mcp/scan", "MCP scan"),
        ("/mcp/capabilities", "MCP capabilities"),
        ("/.well-known/mcp-config", "MCP config"),
        ("/test-config", "Test config"),
        ("/.smithery-test", "Smithery test config"),
        ("/smithery", "Smithery info")
    ]
    
    total_failures = 0
    max_response_time = 0
    
    for endpoint, description in critical_endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=1)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            max_response_time = max(max_response_time, response_time)
            
            if response.status_code == 200:
                if response_time < 100:  # Sub-100ms for ultra-fast
                    print(f"   ⚡ {description} - {response_time:.1f}ms ✅")
                elif response_time < 500:  # Acceptable for deployment
                    print(f"   ⚡ {description} - {response_time:.1f}ms ✅")
                else:
                    print(f"   ⚠️  {description} - {response_time:.1f}ms (SLOW)")
                    total_failures += 1
            else:
                print(f"   ❌ {description} - HTTP {response.status_code}")
                total_failures += 1
                
        except requests.exceptions.Timeout:
            print(f"   ❌ {description} - TIMEOUT (>1000ms)")
            total_failures += 1
        except Exception as e:
            print(f"   ❌ {description} - ERROR: {e}")
            total_failures += 1
    
    print(f"\n📊 Results:")
    print(f"   Endpoints tested: {len(critical_endpoints)}")
    print(f"   Failures: {total_failures}")
    print(f"   Max response time: {max_response_time:.1f}ms")
    
    if total_failures == 0 and max_response_time < 1000:
        print(f"\n🚀 SUCCESS: All endpoints ultra-fast!")
        print(f"   Ready for deployment scanning ✅")
        return True
    else:
        print(f"\n⚠️  ISSUES DETECTED:")
        if total_failures > 0:
            print(f"   - {total_failures} endpoints failed")
        if max_response_time >= 1000:
            print(f"   - Slow responses detected ({max_response_time:.1f}ms)")
        return False

def main():
    """Run ultra-fast response test."""
    print("⚡ Ultra-Fast Scanning Response Test")
    print("=" * 40)
    
    success = test_instant_responses()
    
    if success:
        print("\n✅ DEPLOYMENT READY!")
        print("All scanning endpoints respond instantly.")
        sys.exit(0)
    else:
        print("\n❌ OPTIMIZATION NEEDED")
        print("Some endpoints are too slow for deployment scanning.")
        sys.exit(1)

if __name__ == '__main__':
    main()