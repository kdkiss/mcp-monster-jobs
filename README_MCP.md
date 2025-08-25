# Monster Jobs MCP Server - Conversion Documentation

## Overview

This repository has been successfully converted from a standard Flask REST API to a proper Model Context Protocol (MCP) server that can be deployed on Smithery. The conversion addresses the original deployment error:

```
Error type: not_mcp_server
Reason: The repository implements a standard RESTful Flask API (/api/search, /api/health) without any JSON-RPC endpoints or MCP transport (tools/list, tools/call, resources/list, etc.). It does not implement the Model Context Protocol specification, so it cannot be deployed as an MCP server.
```

## What Was Changed

### 1. Added MCP Server Implementation (`src/mcp_server.py`)

- **JSON-RPC 2.0 Protocol**: Implemented proper JSON-RPC 2.0 message handling
- **MCP Methods**: Added required MCP endpoints:
  - `tools/list` - Lists available tools
  - `tools/call` - Executes tool functions
  - `resources/list` - Lists available resources
  - `resources/read` - Reads resource content

### 2. Tool Definition

The server now exposes one MCP tool:

```json
{
  "name": "search_monster_jobs",
  "description": "Search for job listings on Monster.com using natural language queries",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language job search query (e.g., 'hr admin jobs near winnetka within 5 miles')"
      },
      "max_jobs": {
        "type": "integer",
        "description": "Maximum number of jobs to return (default: 10)",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

### 3. Resource Definition

The server exposes one MCP resource:

```json
{
  "uri": "monster://jobs/search",
  "name": "Monster Jobs Search",
  "description": "Access to Monster.com job search functionality",
  "mimeType": "application/json"
}
```

### 4. Updated Flask Application (`src/main.py`)

- Added MCP blueprint registration
- Enabled CORS for cross-origin requests
- Made port configurable via environment variable

### 5. Smithery Configuration (`smithery.yaml`)

Created proper Smithery configuration:

```yaml
runtime: "container"
startCommand:
  type: "http"
  configSchema:
    type: "object"
    properties:
      max_jobs:
        type: "integer"
        title: "Maximum Jobs"
        description: "Maximum number of jobs to return per search (default: 10)"
        default: 10
        minimum: 1
        maximum: 50
    required: []
  exampleConfig:
    max_jobs: 10
build:
  dockerfile: "Dockerfile"
  dockerBuildPath: "."
env:
  FLASK_ENV: "production"
  PYTHONPATH: "/app"
```

### 6. Updated Dockerfile

- Updated health check to use MCP endpoint: `/mcp/health`

## MCP Endpoints

The server now provides the following MCP endpoints:

### Health Check
- **GET** `/mcp/health` - Returns server status and MCP information

### MCP Protocol
- **POST** `/mcp` - Main MCP JSON-RPC 2.0 endpoint

## Testing

A comprehensive test script (`test_mcp.py`) has been created to verify all MCP functionality:

```bash
python test_mcp.py [base_url]
```

The test script verifies:
1. Health endpoint functionality
2. `tools/list` method
3. `resources/list` method
4. `tools/call` method (job search)
5. `resources/read` method

## Usage Examples

### Tools/List Request
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

### Tools/Call Request
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_monster_jobs",
    "arguments": {
      "query": "software engineer jobs near san francisco within 10 miles",
      "max_jobs": 5
    }
  }
}
```

### Resources/List Request
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/list"
}
```

### Resources/Read Request
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/read",
  "params": {
    "uri": "monster://jobs/search"
  }
}
```

## Deployment on Smithery

The server is now ready for deployment on Smithery:

1. **Push to Repository**: Ensure all changes are committed to your Git repository
2. **Smithery Configuration**: The `smithery.yaml` file is properly configured
3. **Docker Support**: The Dockerfile builds a proper container
4. **MCP Compliance**: All required MCP methods are implemented

## Backward Compatibility

The original REST API endpoints are still available:
- **POST** `/api/search` - Original job search endpoint
- **GET** `/api/health` - Original health check

This ensures existing integrations continue to work while adding MCP support.

## Dependencies

The server requires the following Python packages (already in `requirements.txt`):
- Flask
- flask-cors
- flask-sqlalchemy
- beautifulsoup4
- requests
- sqlalchemy

## Local Development

To run the server locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python src/main.py

# Test MCP functionality
python test_mcp.py
```

The server will start on port 5000 by default, or use the `PORT` environment variable.

## Security Considerations

- The server implements proper JSON-RPC 2.0 error handling
- Input validation is performed on all MCP requests
- CORS is enabled for cross-origin requests
- The server runs as a non-root user in the Docker container

## Next Steps

1. Deploy to Smithery using the provided configuration
2. Test the deployed server using MCP clients
3. Monitor performance and adjust `max_jobs` configuration as needed
4. Consider adding additional tools or resources based on user needs

