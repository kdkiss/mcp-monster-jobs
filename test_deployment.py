#!/usr/bin/env python3
"""
Deployment test script for Monster Jobs MCP Server
This script simulates container startup and validates basic functionality.
"""

import os
import sys
import time
import subprocess
import requests
import signal
from threading import Thread

def test_container_startup():
    """Test container-style startup."""
    print("Testing container-style startup...")
    
    # Set environment variables like Smithery would
    os.environ['PORT'] = '8081'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['FLASK_ENV'] = 'production'
    
    # Start the server in a subprocess
    server_process = None
    try:
        print("Starting server subprocess...")
        server_process = subprocess.Popen([
            sys.executable, 'src/main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Test readiness probe
        try:
            response = requests.get('http://localhost:8081/ready', timeout=5)
            print(f"✓ Readiness probe: {response.status_code}")
            if response.status_code != 200:
                print(f"✗ Readiness probe failed: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Readiness probe failed: {e}")
            return False
        
        # Test health check
        try:
            response = requests.get('http://localhost:8081/health', timeout=5)
            print(f"✓ Health check: {response.status_code}")
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
        
        # Test MCP endpoints
        try:
            response = requests.post('http://localhost:8081/mcp', 
                json={"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1},
                timeout=5)
            print(f"✓ MCP initialize: {response.status_code}")
        except Exception as e:
            print(f"✗ MCP initialize failed: {e}")
            return False
        
        print("✓ All deployment tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Server startup failed: {e}")
        return False
    
    finally:
        if server_process:
            print("Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
            
            # Print server output for debugging
            stdout, stderr = server_process.communicate(timeout=1)
            if stdout:
                print("Server stdout:")
                print(stdout)
            if stderr:
                print("Server stderr:")
                print(stderr)

if __name__ == "__main__":
    print("Monster Jobs MCP Server - Deployment Test")
    print("=" * 50)
    
    success = test_container_startup()
    sys.exit(0 if success else 1)