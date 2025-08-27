# Monster Jobs MCP Server - Architecture

## Overview

The Monster Jobs MCP Server is a lightweight Flask application that provides Model Context Protocol (MCP) functionality for searching jobs on Monster.com. The server is designed for deployment on the Smithery platform and includes comprehensive health checks and scanning endpoints for reliable deployment validation.

## System Architecture

```mermaid
flowchart TD
  A[Smithery Scanner] -->|HTTP :8081| B[Container: monster-jobs-mcp]
  B --> C[Flask App: main]
  C -->|GET| C1[/health, /ready, /status]
  C -->|GET| C2[/.well-known/mcp-config]
  C -->|GET| C3[/scan, /mcp/scan, /mcp/capabilities]
  C -->|POST JSON-RPC| C4[/mcp: initialize, tools/list, resources/list]
  C -.->|Logs/Health| D[Docker HEALTHCHECK /health]
```

## Technology Stack

### Core Technologies
- **Web Framework**: Flask 3.1.1 - Lightweight, proven web framework
- **Runtime**: Python 3.12 with uv package manager
- **Base Image**: Alpine Linux via ghcr.io/astral-sh/uv:python3.12-alpine
- **Container Engine**: Docker with optimized health checks

### Dependencies
- `beautifulsoup4==4.13.4` - HTML parsing for job search functionality
- `flask==3.1.1` - Web framework
- `flask-cors==6.0.0` - Cross-origin resource sharing
- `requests==2.32.5` - HTTP client for job search API calls
- `typing-extensions>=4.0.0` - Type annotations
- `waitress>=3.0.0` - Production WSGI server (ready for future use)

## Deployment Configuration

### Docker Configuration
- **Base Image**: `ghcr.io/astral-sh/uv:python3.12-alpine`
- **Port**: 8081 (configurable via PORT environment variable)
- **Host**: 0.0.0.0 (configurable via HOST environment variable)
- **Health Check**: Integrated curl probe to `/health` endpoint
- **Optimization**: Bytecode compilation and optimized linking enabled

### Smithery Deployment
- **Runtime**: Container
- **Dockerfile**: Uses production-ready Dockerfile with full server implementation
- **Build Path**: Root directory
- **Start Command**: HTTP on port 8081

## Security Considerations

### Input Validation
- JSON-RPC request parsing with error handling
- Query parameter clamping (maxJobs: 1-50, timeout: 5-30 seconds)
- Method validation for supported MCP operations

### Operational Security
- Minimal attack surface with focused endpoint set
- No database dependencies reducing data exposure
- Containerized deployment with isolated runtime

## Monitoring and Observability

### Health Checks
- **Docker Health Check**: Automated curl probe to `/health`
- **Readiness Probe**: `/ready` endpoint for deployment readiness
- **Status Endpoint**: `/status` for detailed service information

### Logging
- Werkzeug and Flask logs suppressed for deployment speed
- Configurable log levels for development vs production
- JSON-RPC request/response logging capabilities

## Scalability Considerations

### Performance Optimizations
- Ultra-minimal Flask application design
- Bytecode compilation enabled
- Optimized dependency caching via uv
- Threaded Flask server for concurrent requests

### Resource Usage
- Alpine Linux base for minimal footprint
- Single-process container design
- No background services or workers

## Error Handling

### Application Errors
- Global error handler for unexpected exceptions
- JSON-RPC specific error responses
- Consistent error format across all endpoints

### Deployment Errors
- Graceful startup failure handling
- Environment variable validation
- Port binding error management

## Future Extensions

### Planned Enhancements
- Waitress WSGI server integration for production robustness
- Rate limiting via Flask-Limiter
- Enhanced input validation and content length limits
- Request ID tracking for distributed tracing

### Monitoring Additions
- Structured JSON logging
- Metrics collection endpoints
- Health check response time monitoring

## File Structure

```
/
├── src/
│   ├── main.py                 # Main Flask application
│   └── main_emergency.py       # Minimal fallback server
├── docs/
│   ├── ARCHITECTURE.md         # This file
│   ├── API.md                  # API specifications
│   └── OPERATIONS.md           # Operations guide
├── Dockerfile                  # Production container
├── Dockerfile.emergency        # Minimal container (fallback)
├── smithery.yaml              # Smithery deployment config
├── pyproject.toml             # Python dependencies
└── requirements.txt           # Additional dependencies