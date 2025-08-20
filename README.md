# Monster Jobs MCP Server

<div align="center">

[![Smithery](https://img.shields.io/badge/Smithery-Compatible-blue)](https://smithery.ai)
[![NPM Version](https://img.shields.io/npm/v/mcp-monster-jobs)](https://www.npmjs.com/package/mcp-monster-jobs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Issues](https://img.shields.io/github/issues/kdkiss/mcp-monster-jobs)](https://github.com/kdkiss/mcp-monster-jobs/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/kdkiss/mcp-monster-jobs/pulls)

</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/kdkiss/mcp-monster-jobs/main/assets/logo.png" alt="Monster Jobs MCP Logo" width="200"/>
</p>

## 📋 Overview

A production-ready Model Context Protocol (MCP) server for searching and retrieving job listings from Monster.com. This server provides comprehensive job search functionality with advanced filtering options, enabling AI assistants to access real-time job market data.

**Key Capabilities:**
- **Search Jobs**: Find jobs based on query, location, and filters
- **Get Job Details**: Retrieve detailed information for specific job listings

## ✨ Features

- 🔍 **Advanced job search** with location and radius filtering
- 📅 **Recency filters** (today, last 2 days, last week, last 2 weeks)
- 💰 **Salary information** extraction
- 📝 **Detailed job descriptions** and requirements
- 🏢 **Company information** retrieval
- 🌐 **Direct job listing URLs** for applications
- 💾 **Smart caching** for efficient detail retrieval
- 🔄 **Rate limiting** and error handling
- 🎯 **Production-ready** with robust error handling

## 🚀 Quick Start

### Prerequisites

- Node.js 16.x or higher
- npm or yarn
- Internet connection for API access

### Installation Options

#### From Smithery (Recommended)

Install directly from the Smithery registry:

```bash
npx @smithery/cli install monster-jobs
```

#### From NPM

```bash
npm install -g mcp-monster-jobs
```

#### Manual Installation

```bash
# Clone the repository
git clone https://github.com/kdkiss/mcp-monster-jobs.git
cd mcp-monster-jobs

# Install dependencies
npm install

# Make the script executable (Linux/Mac)
chmod +x index.js
```

## 💻 Usage

### Running the Server

```bash
# Start the server
npm start

# Or run directly
node index.js

# Development mode with debugging
npm run dev
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port to run the server on | `3000` |
| `CACHE_TTL` | Cache time-to-live in seconds | `3600` |
| `DEBUG` | Enable debug logging | `false` |

### MCP Client Configuration

#### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "monster-jobs": {
      "command": "mcp-monster-jobs"
    }
  }
}
```

#### Other MCP Clients

```json
{
  "mcpServers": {
    "monster-jobs": {
      "command": "node",
      "args": ["/path/to/mcp-monster-jobs/index.js"],
      "env": {}
    }
  }
}
```

## 🛠️ API Tools

### 1. search_monster_jobs

Search for jobs on Monster.com with various filters.

**Parameters:**
- `query` (required): Job search query (e.g., "business analyst", "software engineer")
- `location` (required): Location to search (e.g., "Los Angeles, CA", "Winnetka, IL")
- `radius` (optional): Search radius in miles (default: 5)
- `recency` (optional): Job posting recency ("today", "last+2+days", "last+week", "last+2+weeks")
- `limit` (optional): Maximum results to return (default: 10)

**Example:**
```javascript
search_monster_jobs({
  "query": "business analyst",
  "location": "Winnetka, IL",
  "radius": 5,
  "limit": 10
})
```

**Response includes:**
- Job number (for reference)
- Job title
- Company name
- Location
- Salary (if available)
- Posting recency
- Short description

### 2. get_job_details

Get detailed information for a specific job from search results.

**Parameters:**
- `job_number` (optional): The job number from search results (1-based index)
- `job_id` (optional): Direct job ID if available

**Example:**
```javascript
get_job_details({
  "job_number": 1
})
```

**Response includes:**
- Complete job description
- Requirements and qualifications
- Salary and benefits information
- Company details
- Job type and employment information
- Direct application URL

## 📊 Example Usage Flow

1. **Search for jobs:**
   ```javascript
   search_monster_jobs({
     "query": "business analyst",
     "location": "Winnetka, IL",
     "radius": 5,
     "limit": 10
   })
   ```

2. **Get details for a specific job:**
   ```javascript
   get_job_details({
     "job_number": 1
   })
   ```

## 🏗️ Architecture

### Technical Components

- **Web Scraping**: Uses Puppeteer for reliable web scraping
- **Caching**: Implements smart caching for search results
- **Error Handling**: Comprehensive error handling and recovery
- **Rate Limiting**: Respectful scraping with proper delays
- **Modularity**: Clean, maintainable code structure

### System Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│  MCP Client ├────►  MCP Server ├────►  Monster.com│
│             │    │             │    │             │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                   ┌──────▼──────┐
                   │             │
                   │    Cache    │
                   │             │
                   └─────────────┘
```

## 🔧 Technical Details

### Dependencies
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `puppeteer`: Headless Chrome automation
- `node-cache`: In-memory caching system
- `express`: HTTP server framework (for standalone mode)

### Browser Configuration
- Headless mode for production
- Custom user agent to avoid detection
- Sandbox disabled for Docker compatibility
- Network idle waiting for dynamic content

### Selectors Used
- Search container: `#card-scroll-container`
- Job cards: `.job-search-results-style__JobCardWrap-sc-30547e5b-4`
- Job details: Various data-testid selectors for reliable extraction

## 🛡️ Error Handling

The server includes comprehensive error handling for:
- Network timeouts and failures
- Missing DOM elements
- Invalid search parameters
- Browser launch failures
- Cache misses

Error responses follow the MCP protocol specification with appropriate error codes and descriptive messages.

## ⚡ Performance Considerations

- **Caching**: Search results are cached to avoid repeated requests
- **Batch Processing**: Efficient DOM queries for multiple job cards
- **Memory Management**: Automatic cleanup of old cache entries
- **Browser Reuse**: Proper browser lifecycle management
- **Connection Pooling**: Reuse of network connections

## 🔒 Security

- User agent rotation to avoid detection
- No sensitive data storage
- Sandbox-safe browser configuration
- Input validation and sanitization
- Rate limiting to respect service terms

## ⚠️ Limitations

- Requires an active internet connection
- Dependent on Monster.com's DOM structure
- Rate limited by Monster.com's servers
- Chrome/Chromium dependency via Puppeteer
- May be affected by Monster.com's anti-scraping measures

## 🤝 Contributing

We welcome contributions to improve the Monster Jobs MCP Server!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`npm test`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- [Create an issue](https://github.com/kdkiss/mcp-monster-jobs/issues/new) on GitHub
- Check [existing issues](https://github.com/kdkiss/mcp-monster-jobs/issues) for solutions
- Review Monster.com's robots.txt and terms of service

## 📝 Changelog

### v1.0.0
- Initial release
- Job search functionality
- Job detail retrieval
- Caching system
- Error handling
- Production-ready features

## 📂 Repository Structure

```
mcp-monster-jobs/
├── .github/
│   └── workflows/           # CI/CD workflows
├── assets/                  # Images and static files
├── src/
│   ├── api/                 # API endpoints
│   ├── scrapers/            # Web scraping modules
│   ├── utils/               # Utility functions
│   └── index.js             # Main entry point
├── tests/                   # Test suite
├── .gitignore               # Git ignore file
├── Dockerfile               # Docker configuration
├── LICENSE                  # MIT License
├── README.md                # This file
├── package.json             # NPM package config
└── smithery.yaml            # Smithery configuration
```

## 🔗 Links

- **GitHub:** [https://github.com/kdkiss/mcp-monster-jobs](https://github.com/kdkiss/mcp-monster-jobs)
- **NPM:** [https://www.npmjs.com/package/mcp-monster-jobs](https://www.npmjs.com/package/mcp-monster-jobs)
- **Smithery:** [https://smithery.ai/packages/monster-jobs](https://smithery.ai/packages/monster-jobs)
- **Issues:** [https://github.com/kdkiss/mcp-monster-jobs/issues](https://github.com/kdkiss/mcp-monster-jobs/issues)

## 👥 Authors

- **kdkiss** - *Initial work* - [GitHub Profile](https://github.com/kdkiss)

## 🙏 Acknowledgments

- Monster.com for providing job listing data
- The MCP community for protocol standards
- Contributors who have helped improve this project