# Monster Jobs MCP Server

A Smithery MCP (Model Context Protocol) server for retrieving job listings from Monster.com with natural language search queries.

## Overview

This MCP server provides a simple API endpoint that allows users to search for jobs using natural language queries like "hr admin jobs near winnetka within 5 miles". The server parses the query to extract job title, location, and distance parameters, then attempts to scrape job listings from Monster.com.

## Features

- **Natural Language Query Parsing**: Automatically extracts job title, location, and distance from user queries
- **Flexible Search Parameters**: Supports various query formats and distance specifications
- **JSON API Response**: Returns structured job data including title, company, location, summary, and job links
- **Web Interface**: Includes a user-friendly web interface for testing and demonstration
- **Health Check Endpoint**: Provides server status monitoring

## API Endpoints

### POST /api/search

Search for jobs based on a natural language query.

**Request Body:**
```json
{
  "query": "hr admin jobs near winnetka within 5 miles",
  "max_jobs": 10
}
```

**Response:**
```json
{
  "query": "hr admin jobs near winnetka within 5 miles",
  "parsed": {
    "job_title": "hr admin",
    "location": "winnetka",
    "distance": 5
  },
  "search_url": "https://www.monster.com/jobs/search?q=hr%20admin&where=winnetka&rd=5&page=1&so=m.h.sh",
  "jobs": [
    {
      "title": "Human Resources Administrator",
      "company": "ABC Corporation",
      "location": "Winnetka, CA",
      "summary": "Position available in Winnetka, CA. Click the link for full job details and requirements.",
      "link": "https://www.monster.com/job-openings/..."
    }
  ],
  "total_found": 1
}
```

### GET /api/health

Health check endpoint that returns server status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Monster Jobs MCP Server"
}
```

## Query Format Examples

The server supports various natural language query formats:

- `"hr admin jobs near winnetka within 5 miles"`
- `"software engineer jobs near san francisco within 10 miles"`
- `"marketing manager jobs near chicago within 15 miles"`
- `"data analyst jobs near new york within 20 miles"`

## Installation and Setup

### Prerequisites

- Python 3.11+
- pip (Python package manager)

### Local Development

1. Clone or download the project files
2. Navigate to the project directory:
   ```bash
   cd monster_jobs_mcp
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

5. Start the development server:
   ```bash
   python src/main.py
   ```

6. Access the web interface at `http://localhost:5000`

### Dependencies

The server requires the following Python packages:

- Flask: Web framework for the API server
- BeautifulSoup4: HTML parsing for web scraping
- Requests: HTTP client for making web requests
- SQLAlchemy: Database ORM (included in template)

## Technical Architecture

### Web Scraping Logic

The server uses the following approach to scrape Monster.com:

1. **Query Parsing**: Uses regular expressions to extract job title, location, and distance from natural language queries
2. **URL Construction**: Builds Monster.com search URLs with appropriate parameters
3. **HTML Fetching**: Uses the requests library with proper User-Agent headers
4. **Content Parsing**: Employs BeautifulSoup to extract job information using CSS selectors

### CSS Selectors Used

Based on the provided Monster.com structure:

- **Search Results Container**: `#card-scroll-container`
- **Job Cards**: `div.job-search-results-style__JobCardWrap-sc-30547e5b-4`
- **Job Title**: `a[data-testid="jobTitle"]`
- **Company Name**: `span[data-testid="company"]`
- **Job Location**: `span[data-testid="jobDetailLocation"]`

## Limitations and Considerations

### Anti-Bot Protection

Monster.com implements various anti-bot measures that may prevent successful scraping:

- **CAPTCHA Challenges**: The site may present verification challenges for automated requests
- **Rate Limiting**: Excessive requests may result in temporary IP blocking
- **Dynamic Content**: Some job listings may be loaded via JavaScript, making them inaccessible to basic scraping

### Legal and Ethical Considerations

- **Terms of Service**: Web scraping may violate Monster.com's terms of service
- **Rate Limiting**: The server includes delays between requests to be respectful to Monster.com's servers
- **Alternative Approaches**: Consider using official APIs or job aggregation services for production use

### Reliability

- **Selector Changes**: Monster.com may change their HTML structure, breaking the scraping logic
- **Geographic Limitations**: Search results may vary based on the server's geographic location
- **Data Accuracy**: Scraped data may not always be complete or up-to-date

## Error Handling

The server implements comprehensive error handling:

- **Invalid Queries**: Returns appropriate error messages for malformed requests
- **Network Errors**: Handles connection timeouts and HTTP errors gracefully
- **Parsing Errors**: Continues processing even if individual job cards fail to parse
- **Empty Results**: Returns structured responses even when no jobs are found

## Deployment Options

### Local Deployment

The server can be run locally for development and testing purposes using the built-in Flask development server.

### Production Deployment

For production use, consider:

- **WSGI Server**: Use Gunicorn or uWSGI instead of the Flask development server
- **Reverse Proxy**: Deploy behind Nginx or Apache for better performance
- **Docker**: Containerize the application for easier deployment
- **Environment Variables**: Use environment variables for configuration

### Smithery MCP Integration

This server is designed to be compatible with the Smithery MCP ecosystem, allowing it to be easily integrated with AI agents and other applications that support the Model Context Protocol.

## Contributing

When contributing to this project:

1. Ensure all dependencies are listed in `requirements.txt`
2. Follow Python PEP 8 style guidelines
3. Add appropriate error handling for new features
4. Update documentation for any API changes
5. Test thoroughly with various query formats

## License

This project is provided as-is for educational and demonstration purposes. Please ensure compliance with Monster.com's terms of service and applicable laws when using this software.

## Support

For issues or questions:

1. Check the server logs for error messages
2. Verify that Monster.com is accessible from your network
3. Test with different query formats
4. Consider rate limiting if experiencing connection issues

## Disclaimer

This software is provided for educational purposes only. The authors are not responsible for any violations of terms of service or other legal issues that may arise from using this software. Users should ensure compliance with all applicable laws and website terms of service before using this tool.

