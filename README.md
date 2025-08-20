# Monster Jobs MCP Server

[![Smithery](https://img.shields.io/badge/Smithery-Compatible-blue)](https://smithery.ai)
[![NPM Version](https://img.shields.io/npm/v/mcp-monster-jobs)](https://www.npmjs.com/package/mcp-monster-jobs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Model Context Protocol (MCP) server for searching and retrieving job listings from Monster.com. This server provides comprehensive job search functionality with advanced filtering options.

1. **Search Jobs**: Find jobs based on query, location, and filters
2. **Get Job Details**: Retrieve detailed information for specific job listings

## Features

- 🔍 Advanced job search with location and radius filtering
- 📅 Recency filters (today, last 2 days, last week, last 2 weeks)
- 💰 Salary information extraction
- 📝 Detailed job descriptions and requirements
- 🏢 Company information
- 🌐 Direct job listing URLs
- 💾 Smart caching for efficient detail retrieval
- 🔄 Rate limiting and error handling
- 🎯 Production-ready with proper error handling

## Installation

### From Smithery (Recommended)

Install directly from the Smithery registry:

```bash
npx @smithery/cli install monster-jobs
```

### From NPM

```bash
npm install -g mcp-monster-jobs
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/kdkiss/mcp-monster-jobs.git
cd mcp-monster-jobs

# Install dependencies
npm install

# Make the script executable (Linux/Mac)
chmod +x index.js
```

## Usage

### Running the Server

```bash
# Start the server
npm start

# Or run directly
node index.js

# Development mode with debugging
npm run dev
```

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

## Tools

### 1. search_monster_jobs

Search for jobs on Monster.com with various filters.

**Parameters:**
- `query` (required): Job search query (e.g., "business analyst", "software engineer")
- `location` (required): Location to search (e.g., "Los Angeles, CA", "Winnetka, IL")
- `radius` (optional): Search radius in miles (default: 5)
- `recency` (optional): Job posting recency ("today", "last+2+days", "last+week", "last+2+weeks")
- `limit` (optional): Maximum results to return (default: 10)

**Example:**
```
Get me jobs for business admin near Winnetka within 5 miles
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
```
Get me details for job number 1
```

**Response includes:**
- Complete job description
- Requirements and qualifications
- Salary and benefits information
- Company details
- Job type and employment information
- Direct application URL

## Example Usage Flow

1. **Search for jobs:**
   ```
   search_monster_jobs({
     "query": "business analyst",
     "location": "Winnetka, IL",
     "radius": 5,
     "limit": 10
   })
   ```

2. **Get details for a specific job:**
   ```
   get_job_details({
     "job_number": 1
   })
   ```

## Architecture

- **Web Scraping**: Uses Puppeteer for reliable web scraping
- **Caching**: Implements smart caching for search results
- **Error Handling**: Comprehensive error handling and recovery
- **Rate Limiting**: Respectful scraping with proper delays
- **Modularity**: Clean, maintainable code structure

## Technical Details

### Dependencies
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `puppeteer`: Headless Chrome automation

### Browser Configuration
- Headless mode for production
- Custom user agent to avoid detection
- Sandbox disabled for Docker compatibility
- Network idle waiting for dynamic content

### Selectors Used
- Search container: `#card-scroll-container`
- Job cards: `.job-search-results-style__JobCardWrap-sc-30547e5b-4`
- Job details: Various data-testid selectors for reliable extraction

## Error Handling

The server includes comprehensive error handling for:
- Network timeouts and failures
- Missing DOM elements
- Invalid search parameters
- Browser launch failures
- Cache misses

## Performance Considerations

- **Caching**: Search results are cached to avoid repeated requests
- **Batch Processing**: Efficient DOM queries for multiple job cards
- **Memory Management**: Automatic cleanup of old cache entries
- **Browser Reuse**: Proper browser lifecycle management

## Security

- User agent rotation to avoid detection
- No sensitive data storage
- Sandbox-safe browser configuration
- Input validation and sanitization

## Limitations

- Requires an active internet connection
- Dependent on Monster.com's DOM structure
- Rate limited by Monster.com's servers
- Chrome/Chromium dependency via Puppeteer

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing issues for solutions
- Review Monster.com's robots.txt and terms of service

## Changelog

### v1.0.0
- Initial release
- Job search functionality
- Job detail retrieval
- Caching system
- Error handling
- Production-ready features