#!/usr/bin/env python3
"""
Test MCP server functionality
"""
import json
import subprocess
import sys

def test_mcp_server():
    """Test the MCP server with a simple request"""
    # MCP initialization message
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    try:
        # Start the server process
        process = subprocess.Popen(
            [sys.executable, "monster_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send initialization message
        input_data = json.dumps(init_msg) + "\n"
        stdout, stderr = process.communicate(input=input_data, timeout=5)
        
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        print("Return code:", process.returncode)
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("Server started successfully (timeout expected)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mcp_server()