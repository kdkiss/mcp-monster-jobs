#!/usr/bin/env python3
"""
Simple test to verify MCP server functionality
"""

import asyncio
from mcp.server.fastmcp import FastMCP

# Create a minimal MCP server for testing
mcp = FastMCP("test-server")

@mcp.tool()
async def test_tool() -> str:
    """Simple test tool"""
    return "Server is working!"

if __name__ == "__main__":
    mcp.run()