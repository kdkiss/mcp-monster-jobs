#!/usr/bin/env python3
"""
Startup validation for deployment optimization
"""

import time
import subprocess
import requests
import sys
import os

def test_local_startup():
    """Test local server startup time and responsiveness."""
    print("🚀 Testing optimized server startup...")
    
    # Record startup time
    start_time = time.time()
    
    try:
        # Start server process
        print("1. Starting server process...")
        env = os.environ.copy()
        env['PORT'] = '8081'
        env['HOST'] = '0.0.0.0'
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Give server time to start
        time.sleep(3)
        
        startup_time = time.time() - start_time
        print(f"   ✅ Server started in {startup_time:.2f} seconds")
        
        # Test critical endpoints
        base_url = "http://localhost:8081"
        critical_endpoints = [
            ("/health", "Health check"),
            ("/ping", "Ping test"),
            ("/ready", "Readiness probe"),
            ("/status", "Status check")
        ]
        
        for endpoint, description in critical_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ {description} - OK ({response.status_code})")
                else:
                    print(f"   ❌ {description} - Failed ({response.status_code})")
            except Exception as e:
                print(f"   ❌ {description} - Error: {e}")
        
        # Test MCP endpoints
        mcp_endpoints = [
            ("/.well-known/mcp-config", "MCP config"),
            ("/mcp/capabilities", "MCP capabilities"),
            ("/scan", "Scan endpoint")
        ]
        
        for endpoint, description in mcp_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                if response.status_code == 200:
                    print(f"   ✅ {description} - OK ({response.status_code})")
                else:
                    print(f"   ⚠️  {description} - Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ {description} - Error: {e}")
        
        total_time = time.time() - start_time
        print(f"\n📊 Total validation time: {total_time:.2f} seconds")
        
        if total_time < 10:
            print("🎉 Server startup optimized for deployment!")
            return True
        else:
            print("⚠️  Server startup might be too slow for deployment")
            return False
    
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        return False
    
    finally:
        # Clean up process
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass

def main():
    """Run startup validation."""
    print("⚡ Startup Optimization Validation")
    print("=" * 40)
    
    success = test_local_startup()
    
    if success:
        print("\n✅ Ready for optimized deployment!")
        sys.exit(0)
    else:
        print("\n⚠️  May need further optimization")
        sys.exit(1)

if __name__ == '__main__':
    main()