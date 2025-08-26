#!/usr/bin/env python3
"""
Deployment Timeout Isolation Test
Tests minimal server to isolate timeout causes
"""

import subprocess
import requests
import time
import sys
import os

def test_minimal_server():
    """Test the minimal server for deployment timeout issues."""
    print("🔬 Testing Minimal Server for Timeout Isolation")
    print("=" * 50)
    
    # Start minimal server
    print("1. Starting minimal server...")
    env = os.environ.copy()
    env['PORT'] = '8081'
    env['HOST'] = '0.0.0.0'
    env['PYTHONUNBUFFERED'] = '1'
    
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "src/main_minimal.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Give server time to start
        time.sleep(2)
        print("   ✅ Minimal server started")
        
        # Test critical scanning endpoints with timing
        base_url = "http://localhost:8081"
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
            ("/smithery", "Smithery info"),
            ("/", "Root endpoint")
        ]
        
        print("\\n2. Testing endpoint response times...")
        max_time = 0
        failures = 0
        
        for endpoint, description in critical_endpoints:
            try:
                start = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                response_time = (time.time() - start) * 1000
                
                max_time = max(max_time, response_time)
                
                if response.status_code == 200:
                    if response_time < 50:
                        print(f"   ⚡ {description:20} - {response_time:6.1f}ms ✅")
                    elif response_time < 200:
                        print(f"   🟡 {description:20} - {response_time:6.1f}ms OK")
                    else:
                        print(f"   🔴 {description:20} - {response_time:6.1f}ms SLOW")
                        failures += 1
                else:
                    print(f"   ❌ {description:20} - HTTP {response.status_code}")
                    failures += 1
                    
            except requests.exceptions.Timeout:
                print(f"   ❌ {description:20} - TIMEOUT")
                failures += 1
            except Exception as e:
                print(f"   ❌ {description:20} - ERROR: {e}")
                failures += 1
        
        print(f"\\n3. Results Summary:")
        print(f"   Endpoints tested: {len(critical_endpoints)}")
        print(f"   Failures: {failures}")
        print(f"   Max response time: {max_time:.1f}ms")
        
        if failures == 0 and max_time < 500:
            print(f"\\n🎉 SUCCESS: Minimal server ultra-fast!")
            print(f"   - All endpoints working")
            print(f"   - Response times under 500ms")
            print(f"   - Ready for deployment testing")
            return True
        else:
            print(f"\\n⚠️  ISSUES with minimal server:")
            if failures > 0:
                print(f"   - {failures} endpoint failures")
            if max_time >= 500:
                print(f"   - Slow responses ({max_time:.1f}ms)")
            return False
            
    except Exception as e:
        print(f"❌ Minimal server test failed: {e}")
        return False
    
    finally:
        # Clean up process
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

def test_full_server():
    """Test the full server for comparison."""
    print("\\n🔍 Testing Full Server for Comparison")
    print("=" * 40)
    
    # Start full server
    print("1. Starting full server...")
    env = os.environ.copy()
    env['PORT'] = '8082'  # Different port
    env['HOST'] = '0.0.0.0'
    env['PYTHONUNBUFFERED'] = '1'
    
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Give server time to start
        time.sleep(3)
        print("   ✅ Full server started")
        
        # Test scanning endpoints
        base_url = "http://localhost:8082"
        scan_endpoints = [
            ("/health", "Health check"),
            ("/scan", "Universal scan"),
            ("/mcp/scan", "MCP scan"),
            ("/mcp/capabilities", "MCP capabilities")
        ]
        
        print("\\n2. Testing scanning endpoints...")
        max_time = 0
        failures = 0
        
        for endpoint, description in scan_endpoints:
            try:
                start = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                response_time = (time.time() - start) * 1000
                
                max_time = max(max_time, response_time)
                
                if response.status_code == 200:
                    if response_time < 100:
                        print(f"   ⚡ {description:20} - {response_time:6.1f}ms ✅")
                    elif response_time < 500:
                        print(f"   🟡 {description:20} - {response_time:6.1f}ms OK")
                    else:
                        print(f"   🔴 {description:20} - {response_time:6.1f}ms SLOW")
                        failures += 1
                else:
                    print(f"   ❌ {description:20} - HTTP {response.status_code}")
                    failures += 1
                    
            except requests.exceptions.Timeout:
                print(f"   ❌ {description:20} - TIMEOUT")
                failures += 1
            except Exception as e:
                print(f"   ❌ {description:20} - ERROR: {e}")
                failures += 1
        
        print(f"\\n3. Full Server Results:")
        print(f"   Failures: {failures}")
        print(f"   Max response time: {max_time:.1f}ms")
        
        return failures == 0 and max_time < 1000
            
    except Exception as e:
        print(f"❌ Full server test failed: {e}")
        return False
    
    finally:
        # Clean up process
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

def main():
    """Run timeout isolation tests."""
    print("🔬 DEPLOYMENT TIMEOUT ISOLATION TEST")
    print("=" * 60)
    
    minimal_success = test_minimal_server()
    full_success = test_full_server()
    
    print("\\n📊 FINAL ANALYSIS:")
    print("=" * 30)
    
    if minimal_success and full_success:
        print("✅ BOTH servers working - timeout issue likely external")
        print("   - Try deployment with current configuration")
        print("   - Issue may be in Smithery scanning process")
    elif minimal_success and not full_success:
        print("⚠️  FULL server has issues - use minimal for testing")
        print("   - Full server has performance problems")
        print("   - Deploy with minimal server first")
    elif not minimal_success:
        print("❌ FUNDAMENTAL server issues detected")
        print("   - Basic Flask setup has problems")
        print("   - Check Python environment and dependencies")
    
    sys.exit(0 if minimal_success else 1)

if __name__ == '__main__':
    main()