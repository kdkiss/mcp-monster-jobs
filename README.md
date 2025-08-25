# Monster Jobs MCP Server

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-ready **Model Context Protocol (MCP)** server that enables AI assistants to search and retrieve job listings from Monster.com using natural language queries.

## 🌟 Key Features

- **🤖 MCP Integration**: Full Model Context Protocol support for seamless AI assistant integration
- **🔍 Natural Language Search**: Parse complex queries like "software engineer jobs near San Francisco within 10 miles"
- **⚡ High Performance**: Optimized with uv package manager and Alpine Linux base image
- **🔒 Production Ready**: Comprehensive error handling and structured responses
- **📊 Dual API Support**: Both MCP protocol and traditional REST endpoints
- **🐳 Containerized**: Docker deployment with optimized multi-stage builds

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [MCP Integration](#-mcp-integration)
- [API Reference](#-api-reference)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)

## 🚀 Quick Start

### Using with MCP Clients

```python
# Example MCP tool usage
import requests

# Search for jobs using the MCP server
response = requests.post("http://localhost:5000/tools/call", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search_jobs",
        "arguments": {
            "query": "software engineer jobs near San Francisco within 10 miles",
            "max_jobs": 5
        }
    }
})
```

### Using REST API

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "data scientist jobs near New York within 15 miles"}'
```

## 🤖 MCP Integration

### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_jobs` | Search Monster.com jobs using natural language | `query`, `max_jobs` |

### Tool Schema

```json
{
  "name": "search_jobs",
  "description": "Search for jobs on Monster.com based on a natural language query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language query describing the job search"
      },
      "max_jobs": {
        "type": "integer",
        "description": "Maximum number of jobs to return (default: 10)"
      }
    },
    "required": ["query"]
  }
}
```

## 📖 API Reference

### MCP Endpoints

#### `POST /mcp`
Initialize MCP connection and get server capabilities.

#### `POST /tools/list`
List available tools.

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "search_jobs",
        "description": "Search for jobs on Monster.com based on a natural language query",
        "inputSchema": { "...": "..." }
      }
    ]
  },
  "id": 1
}
```

#### `POST /tools/call`
Execute a tool with given parameters.

#### `POST /resources/list`
List available resources.

### REST Endpoints

#### `POST /search`
Search for jobs using natural language query.

**Request:**
```json
{
  "query": "software engineer jobs near San Francisco within 10 miles",
  "max_jobs": 10
}
```

**Response:**
```json
{
  "query": "software engineer jobs near San Francisco within 10 miles",
  "parsed": {
    "job_title": "software engineer",
    "location": "San Francisco",
    "distance": 10
  },
  "search_url": "https://www.monster.com/jobs/search?q=software%20engineer&where=San%20Francisco&rd=10&page=1&so=m.h.sh",
  "jobs": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "summary": "Position available in San Francisco, CA. Click the link for full job details.",
      "link": "https://www.monster.com/job/..."
    }
  ],
  "total_found": 1
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Monster Jobs MCP Server"
}
```

## 💡 Usage Examples

### Natural Language Queries

The server intelligently parses various natural language query formats:

```bash
# Location-based searches
"software engineer jobs near San Francisco within 10 miles"
"marketing manager jobs near Chicago within 15 miles"
"data analyst jobs near New York within 20 miles"

# Title-focused searches
"hr admin jobs near winnetka within 5 miles"
"senior developer jobs near Austin within 25 miles"
"product manager jobs near Seattle within 15 miles"

# Flexible formatting
"jobs as a nurse near Boston within 30 miles"
"find me accounting positions near Denver within 20 miles"
```

### Advanced Query Patterns

```bash
# Specific job titles
"senior software engineer jobs near San Francisco"
"junior marketing coordinator jobs near New York"

# Distance variations
"developer jobs near Chicago within 5 miles"
"analyst jobs near Boston within 50 miles"

# Location variations
"engineer jobs in downtown Seattle within 10 miles"
"manager jobs near Silicon Valley within 15 miles"
```

## 🛠️ Installation

### Prerequisites

- **Python 3.12+**
- **uv** package manager ([install uv](https://github.com/astral-sh/uv))

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd monster-jobs-mcp-server

# Install dependencies using uv
uv sync

# Start the development server
uv run python src/main.py
```

The server will start on `http://localhost:5000`

### Docker Deployment

```bash
# Build the container
docker build -t monster-jobs-mcp .

# Run the container
docker run -p 5000:5000 monster-jobs-mcp
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `HOST` | `0.0.0.0` | Server host binding |

### Smithery Configuration

The `smithery.yaml` file contains deployment configuration:

```yaml
runtime: "container"
build:
  dockerfile: "Dockerfile"
  dockerBuildPath: "."
startCommand:
  type: "http"
```

## 🔧 Development

### Project Structure

```
├── src/
│   ├── main.py           # Main MCP server application
│   └── test_mcp.py       # MCP server tests
├── pyproject.toml        # Project dependencies and configuration
├── uv.lock              # Dependency lock file
├── Dockerfile           # Container build configuration
├── smithery.yaml        # Smithery deployment configuration
└── README.md           # This file
```

### Running Tests

```bash
# Run MCP server tests
uv run python src/test_mcp.py
```

### Development Dependencies

```bash
# Install development dependencies
uv sync --dev
```

## 🚀 Deployment

### Smithery MCP Deployment

1. **Connect to Smithery**: Ensure your repository is connected to Smithery
2. **Configure Build**: The `smithery.yaml` handles automatic deployment
3. **Deploy**: Push to your main branch to trigger deployment
4. **Verify**: Check that MCP tools are discoverable

### Manual Deployment

```bash
# Using Docker
docker build -t monster-jobs-mcp .
docker run -p 5000:5000 monster-jobs-mcp

# Using uv directly
uv sync
uv run python src/main.py
```

### Production Considerations

- **Rate Limiting**: Implement request rate limiting for production use
- **Caching**: Add caching layer for improved performance
- **Monitoring**: Implement proper logging and monitoring
- **Security**: Use HTTPS in production environments

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  MCP Server      │────│  Monster.com    │
│                 │    │                  │    │                 │
│ • AI Assistants │    │ • Query Parser   │    │ • Job Listings  │
│ • Tools         │    │ • URL Builder    │    │ • Search API    │
│ • Resources     │    │ • Web Scraper    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Processing Pipeline

1. **Query Analysis**: Natural language processing to extract job parameters
2. **URL Construction**: Build Monster.com search URLs with proper parameters
3. **Web Scraping**: Extract job data using BeautifulSoup and CSS selectors
4. **Data Structuring**: Format results into MCP-compliant response format
5. **Error Handling**: Comprehensive error handling with graceful degradation

### MCP Protocol Implementation

- **Server Capabilities**: Tools and resources discovery
- **Tool Execution**: JSON-RPC 2.0 compliant tool calling
- **Resource Listing**: Available resources enumeration
- **Error Handling**: Standardized MCP error responses

## ⚠️ Important Notes

### Limitations

- **Rate Limiting**: Monster.com may block requests exceeding rate limits
- **Geographic Variation**: Results may vary by server location
- **Dynamic Content**: Some listings may require JavaScript rendering
- **Selector Stability**: HTML structure changes may break scraping

### Ethical Considerations

- **Respectful Scraping**: Includes delays and proper headers
- **Terms Compliance**: Users must comply with Monster.com's terms
- **Educational Use**: Designed for learning and demonstration
- **Production Alternatives**: Consider official APIs for production use

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/monster-jobs-mcp-server.git
cd monster-jobs-mcp-server

# Install development dependencies
uv sync --dev

# Run tests
uv run python src/test_mcp.py

# Start development server
uv run python src/main.py
```

### Code Standards

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations for better code clarity
- **Documentation**: Update README and docstrings for changes
- **Testing**: Add tests for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Troubleshooting

**Server won't start:**
- Check Python 3.12+ installation
- Verify port 5000 is available
- Review logs for error messages

**MCP scanning fails:**
- Ensure server is running on correct port
- Check MCP endpoint responses
- Verify JSON-RPC 2.0 compliance

**No job results:**
- Test Monster.com accessibility
- Check query format
- Review server logs for scraping errors

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-username/monster-jobs-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/monster-jobs-mcp-server/discussions)
- **Documentation**: Check this README and inline code documentation

## ⚖️ Disclaimer

This software is provided for educational and demonstration purposes only. Users are responsible for complying with Monster.com's terms of service and applicable laws. The authors are not responsible for any violations or legal issues that may arise from using this software.

---

<div align="center">

**Built with ❤️ for the MCP ecosystem**

[⭐ Star us on GitHub](https://github.com/your-username/monster-jobs-mcp-server) •
[📖 Documentation](https://github.com/your-username/monster-jobs-mcp-server#readme) •
[🐛 Report Issues](https://github.com/your-username/monster-jobs-mcp-server/issues)

</div>

