# Smithery Test Configuration for Monster Jobs MCP Server

## Basic Connectivity Tests
- GET /ping (should return 200 with status: pong)
- GET /health (should return 200 with status: healthy)
- GET / (should return 200 with server info)

## MCP Protocol Tests
- GET /.well-known/mcp-config (should return 200 with MCP configuration)
- POST /mcp with initialize method (should return 200 with server capabilities)
- POST /mcp with tools/list method (should return 200 with available tools)

## Expected Tool
- search_jobs: Search for jobs on Monster.com based on natural language query

## Server Details
- Name: monster-jobs-mcp-server
- Version: 1.0.0
- Protocol: MCP (Model Context Protocol)
- Transport: HTTP on port 8081