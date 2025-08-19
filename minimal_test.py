#!/usr/bin/env python3
"""
Minimal MCP server test without external dependencies
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-server")

@mcp.tool()
async def hello() -> str:
    """Test tool"""
    return "Hello from MCP server!"

if __name__ == "__main__":
    mcp.run()