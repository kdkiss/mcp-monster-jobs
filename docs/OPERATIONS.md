# Monster Jobs MCP Server - Operations Guide

## Overview

This guide covers the operational aspects of running and monitoring the Monster Jobs MCP Server in production environments.

## Environment Variables

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8081` | Port on which the server listens |
| `HOST` | `0.0.0.0` | Host address to bind to |

### Setting Environment Variables

```bash
# Docker container
docker run -e PORT=8081 -e HOST=0.0.0.0 monster-jobs-mcp-server

# Smithery deployment (automatically configured)
# PORT and HOST are set in smithery.yaml
```

## Health Checks

### Docker Health Check

The container includes an integrated health check:

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --retries=2 --start-period=5s \
    CMD curl -f http://localhost:8081/health || exit 1
```

### Manual Health Check

```bash
curl -f http://localhost:8081/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "monster-jobs-mcp-server",
  "version": "1.0.0"
}
```

### Readiness Check

```bash
curl -f http://localhost:8081/ready
```

Expected response:
```json
{
  "status": "ready",
  "service": "monster-jobs-mcp-server"
}
```

## Logging

### Current Configuration

The server is configured for minimal logging to optimize deployment speed:

```python
# In src/main.py
logging.getLogger('werkzeug').setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)
```

### Enabling Debug Logging

For development or troubleshooting, enable debug logging by modifying the logging configuration:

```python
# Temporary debug logging
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

### Log Levels

- `ERROR`: Only errors and critical issues
- `WARN`: Warnings and errors
- `INFO`: General information (default for production)
- `DEBUG`: Detailed debugging information

### Log Format

Logs are output in standard Flask/Werkzeug format:

```
[2025-01-27 10:30:45,123] INFO in main: Starting server on 0.0.0.0:8081
[2025-01-27 10:30:46,456] ERROR in werkzeug: 404 Not Found: /unknown-endpoint
```

## Monitoring

### Key Metrics to Monitor

1. **Response Times**: Track `/health` and `/mcp` endpoint response times
2. **Error Rates**: Monitor 4xx and 5xx response codes
3. **Container Health**: Docker health check status
4. **Memory Usage**: Container memory consumption
5. **CPU Usage**: Container CPU utilization

### MCP Protocol Monitoring

Monitor JSON-RPC request/response patterns:

```bash
# Monitor MCP requests
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
```

## Deployment

### Smithery Deployment

The server is configured for Smithery platform deployment:

```yaml
# smithery.yaml
runtime: "container"
build:
  dockerfile: "Dockerfile"  # Uses full server with all endpoints
  dockerBuildPath: "."
startCommand:
  type: "http"
testConfig:
  tests:
    connectivity:
      - name: "health_check"
        endpoint: "/health"
        method: "GET"
        expectedStatus: 200
    mcp_protocol:
      - name: "mcp_initialize"
        endpoint: "/mcp"
        method: "POST"
        expectedStatus: 200
```

### Local Development

For local development and testing:

```bash
# Install dependencies
uv sync

# Run the server
python src/main.py

# Or with custom environment
PORT=3000 HOST=127.0.0.1 python src/main.py
```

### Production Deployment

For production deployments with enhanced robustness:

```bash
# Using waitress WSGI server (already in dependencies)
waitress-serve --port=8081 --host=0.0.0.0 src.main:app
```

## Troubleshooting

### Common Issues

#### 1. Scan Fails During Deployment

**Symptom**: Smithery reports "Scan failed" or "capabilities may not be indexed"

**Solution**:
- Verify all endpoints are responding:
  ```bash
  curl http://localhost:8081/health
  curl http://localhost:8081/.well-known/mcp-config
  curl http://localhost:8081/scan
  ```
- Check that Dockerfile is being used (not Dockerfile.emergency)

#### 2. Port Already in Use

**Symptom**: Server fails to start with "address already in use"

**Solution**:
```bash
# Find process using port 8081
lsof -i :8081

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8082 python src/main.py
```

#### 3. JSON-RPC Parse Errors

**Symptom**: MCP requests return parse errors

**Solution**:
- Validate JSON-RPC request format
- Check Content-Type header is `application/json`
- Ensure request body is valid JSON

#### 4. Container Health Check Fails

**Symptom**: Docker reports unhealthy container

**Solution**:
```bash
# Test health endpoint directly
docker exec <container_id> curl -f http://localhost:8081/health

# Check container logs
docker logs <container_id>

# Verify port binding
docker ps
```

### Debug Mode

Enable debug mode for detailed error information:

```python
# In src/main.py, temporarily change:
app.run(host=host, port=port, debug=True, threaded=True,
        use_reloader=False, processes=1)
```

**Warning**: Debug mode should never be used in production.

## Performance Tuning

### Current Optimizations

1. **Bytecode Compilation**: Enabled via `UV_COMPILE_BYTECODE=1`
2. **Optimized Linking**: `UV_LINK_MODE=copy`
3. **No Bytecode Write**: `PYTHONDONTWRITEBYTECODE=1`
4. **Threaded Server**: `threaded=True` for concurrent requests

### Memory Optimization

The Alpine Linux base image and minimal dependencies keep memory usage low:

- Base image size: ~50MB
- Python dependencies: ~20MB additional
- Typical runtime memory: <100MB

### Scaling Considerations

For high-traffic deployments:

1. **Load Balancer**: Place behind a load balancer
2. **Rate Limiting**: Implement rate limiting middleware
3. **Caching**: Add response caching for frequently accessed data
4. **Horizontal Scaling**: Deploy multiple container instances

## Security Checklist

### Pre-Deployment

- [ ] Environment variables set correctly
- [ ] No debug mode enabled
- [ ] Logging level appropriate for environment
- [ ] All health checks passing
- [ ] MCP endpoints responding correctly

### Runtime

- [ ] Monitor for unusual error rates
- [ ] Regular log review
- [ ] Container resource limits set
- [ ] Network security policies applied

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration files
tar -czf backup-$(date +%Y%m%d).tar.gz \
  smithery.yaml \
  Dockerfile \
  pyproject.toml \
  src/main.py
```

### Log Retention

```bash
# Container logs
docker logs <container_id> > logs-$(date +%Y%m%d).log

# Application logs (if external logging configured)
# Logs are typically captured by container runtime
```

## Support

### Getting Help

1. Check the health endpoints
2. Review container logs
3. Validate MCP protocol compliance
4. Test with the debug scan script

### Useful Commands

```bash
# Quick health check
curl -s http://localhost:8081/health | jq .

# Test all endpoints
for endpoint in / /health /ready /ping /.well-known/mcp-config /scan; do
  echo "Testing $endpoint..."
  curl -s http://localhost:8081$endpoint | head -5
done

# Monitor requests
docker stats <container_id>

# View logs
docker logs -f <container_id>