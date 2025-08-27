# Monster Jobs MCP Server - API Reference

## Overview

The Monster Jobs MCP Server provides a REST API for health checking, MCP protocol communication, and deployment scanning. All endpoints return JSON responses.

## Base URL

```
http://localhost:8081
```

## Authentication

No authentication is required for any endpoints.

## Health and Status Endpoints

### GET /health

Returns the health status of the server.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "monster-jobs-mcp-server",
  "version": "1.0.0"
}
```

### GET /ready

Returns the readiness status of the server for deployment.

**Response (200 OK):**
```json
{
  "status": "ready",
  "service": "monster-jobs-mcp-server"
}
```

### GET /status

Returns detailed status information.

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "monster-jobs-mcp-server",
  "ready": true
}
```

### GET /ping

Simple ping endpoint for connectivity testing.

**Response (200 OK):**
```json
{
  "status": "pong"
}
```

## MCP Configuration Endpoints

### GET /.well-known/mcp-config

Returns MCP server configuration information.

**Response (200 OK):**
```json
{
  "mcpServers": {
    "monster-jobs": {
      "command": "python",
      "args": ["src/main.py"],
      "env": {
        "PORT": "8081"
      },
      "transport": {
        "type": "http",
        "host": "localhost",
        "port": 8081
      }
    }
  },
  "serverInfo": {
    "name": "monster-jobs-mcp-server",
    "version": "1.0.0",
    "description": "MCP server for searching jobs on Monster.com"
  }
}
```

### GET /mcp/capabilities

Returns MCP protocol capabilities.

**Response (200 OK):**
```json
{
  "protocolVersion": "2024-11-05",
  "serverInfo": {
    "name": "monster-jobs-mcp-server",
    "version": "1.0.0",
    "description": "MCP server for searching jobs on Monster.com"
  },
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "listChanged": true
    }
  }
}
```

## Scanning Endpoints

### GET /scan

Returns comprehensive server scanning information.

**Response (200 OK):**
```json
{
  "server": {
    "name": "monster-jobs-mcp-server",
    "version": "1.0.0",
    "status": "ready",
    "healthy": true,
    "scannable": true
  },
  "protocol": {
    "name": "mcp",
    "version": "2024-11-05",
    "transport": "http"
  },
  "capabilities": {
    "tools": {
      "available": true,
      "count": 1
    },
    "resources": {
      "available": true,
      "count": 1
    }
  },
  "endpoints": {
    "main": "/mcp",
    "health": "/health",
    "scan": "/scan"
  },
  "deployment": {
    "platform": "smithery",
    "ready": true
  }
}
```

### GET /mcp/scan

Returns MCP-specific scanning information.

**Response (200 OK):**
```json
{
  "name": "monster-jobs-mcp-server",
  "version": "1.0.0",
  "status": "ready",
  "healthy": true,
  "scannable": true,
  "protocol": "mcp",
  "transport": "http",
  "capabilities": {
    "tools": {
      "available": true,
      "count": 1
    },
    "resources": {
      "available": true,
      "count": 1
    }
  },
  "endpoints": {
    "main": "/mcp",
    "health": "/health",
    "config": "/.well-known/mcp-config"
  }
}
```

### GET /test-config

Returns test configuration for automated testing.

**Response (200 OK):**
```json
{
  "tests": {
    "connectivity": [
      {
        "name": "health_check",
        "endpoint": "/health",
        "method": "GET",
        "expectedStatus": 200
      }
    ],
    "mcp_protocol": [
      {
        "name": "mcp_initialize",
        "endpoint": "/mcp",
        "method": "POST",
        "expectedStatus": 200
      }
    ]
  }
}
```

### GET /.smithery-test

Returns Smithery-specific test configuration.

**Response (200 OK):**
```json
{
  "version": "1.0",
  "name": "monster-jobs-mcp-server",
  "tests": [
    {
      "name": "health_check",
      "type": "http",
      "endpoint": "/health",
      "method": "GET"
    }
  ]
}
```

## MCP Protocol Endpoints

### POST /mcp

Main MCP JSON-RPC endpoint supporting the following methods:

#### Method: initialize

Initializes the MCP connection.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  },
  "id": 1
}
```

**Response (200 OK):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "monster-jobs-mcp-server",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {
        "listChanged": true
      },
      "resources": {
        "listChanged": true
      }
    }
  },
  "id": 1
}
```

#### Method: tools/list

Lists available MCP tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

**Response (200 OK):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "search_jobs",
        "description": "Search for jobs on Monster.com",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Job search query"
            }
          },
          "required": ["query"]
        }
      }
    ]
  },
  "id": 2
}
```

#### Method: resources/list

Lists available MCP resources.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "params": {},
  "id": 3
}
```

**Response (200 OK):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "resources": [
      {
        "uri": "monster://jobs/search",
        "name": "Monster Jobs Search",
        "description": "Search jobs on Monster.com",
        "mimeType": "application/json"
      }
    ]
  },
  "id": 3
}
```

#### Error Responses

**Unknown Method (404 Not Found):**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found"
  },
  "id": null
}
```

**Parse Error (400 Bad Request):**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32700,
    "message": "Parse error"
  },
  "id": null
}
```

## Root Endpoint

### GET /

Returns basic server information.

**Response (200 OK):**
```json
{
  "name": "Monster Jobs MCP Server",
  "version": "1.0.0",
  "protocol": "mcp",
  "status": "ready",
  "healthy": true,
  "deployment": {
    "platform": "smithery",
    "ready": true
  }
}
```

## Error Handling

All endpoints include global error handling that returns:

**Response (500 Internal Server Error):**
```json
{
  "error": "Internal server error",
  "status": "error"
}
```

## Content Types

- **Request**: `application/json` (for POST endpoints)
- **Response**: `application/json` (all endpoints)

## Rate Limiting

Currently no rate limiting is implemented. For production deployments, consider adding rate limiting via Flask-Limiter or similar middleware.

## Versioning

API version is included in the server version field. Breaking changes will increment the major version number.