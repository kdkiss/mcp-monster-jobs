#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple-test")

@mcp.tool()
async def test() -> str:
    return "working"

if __name__ == "__main__":
    mcp.run()