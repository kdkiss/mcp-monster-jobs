# Smithery-Compliant MCP Job-Scraper Server

A minimal **Smithery-compliant MCP (Message Command Protocol)** TCP server that accepts natural-language job queries such as

```
get fraud jobs near winnetka, ca within 5 miles
```

It live-scrapes Monster.com and returns a **compact JSON** list for every matching job containing:

* `title` – job title
* `company` – employer name
* `snippet` – short description / bullet preview
* `link` – direct URL to the posting on Monster

The project purpose is to demonstrate how a lightweight “plain-socket” server can be built to satisfy the Smithery **MCP** specification without relying on heavyweight HTTP frameworks.

---

## Table of Contents
1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Protocol](#protocol)
4. [Configuration](#configuration)
5. [Development](#development)
6. [Testing](#testing)
7. [Project Structure](#project-structure)

---

## Features
• Natural-language command parsing (keywords, location & radius)

• Live web-scraping of Monster.com using rotating desktop User-Agents

• Lightweight, dependency-free MCP server over raw TCP (no HTTP)

• Resilient: basic retry logic, graceful error handling, newline-delimited JSON responses

## Quick Start

```bash
# 1. Obtain sources and enter project
$ git clone <repo-url> && cd job_scraper_server

# 2. Create Python 3.11 virtual-env & install dependencies
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt

# 3. Launch the server on default host/port (0.0.0.0:5555)
$ python -m job_scraper_server.main

# 4. Issue a query from another terminal (nc = netcat)
$ echo 'get fraud jobs near winnetka, ca within 5 miles\n' | nc localhost 5555
```

The server will respond with one **single-line** JSON payload terminated by `\n`, e.g.

```json
[{"title":"Fraud Investigator","company":"ACME Corp","snippet":"Investigate suspicious activity…","link":"https://www.monster.com/jobid=123"}]
```

If the parser fails or no jobs are found, an error object is returned:

```json
{"error":"no results"}
```

## Protocol
Smithery MCP is a **simple, bidirectional, newline-terminated text protocol**.

Client → Server
```
<command>\n
```

Server → Client
```
<compact-json>\n
```

Supported command grammar (case-insensitive):
```
get <keywords> jobs near <city>[, <state>] within <radius> miles
```
If any element is omitted the server falls back to the defaults configured in `config.py` (e.g. radius 10 mi, location "Los Angeles, CA").

## Configuration
All tunables live in **`job_scraper_server/config.py`** and can be overridden by environment variables (.env supported via `python-dotenv`). Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_HOST` | 0.0.0.0 | Interface to bind socket |
| `SERVER_PORT` | 5555 | TCP port |
| `SCRAPER_TIMEOUT` | 10 | Seconds per HTTP request |
| `DEFAULT_LOCATION` | Los Angeles, CA | Used when parser cannot determine location |
| `DEFAULT_RADIUS` | 10 | Search radius in miles |

## Development

```bash
# Run unit tests (optional)
$ pytest -q

# Lint (if flake8/ruff installed)
$ ruff job_scraper_server
```

Key modules:
* **models.py** – Typed data classes (`Job`, `Query`)
* **scraper.py** – Monster HTML parsing and fetching
* **parser.py** – Natural-language → `Query`
* **server.py** – Blocking TCP event loop
* **main.py** – CLI entry point

## Testing
During development you can interact with the socket server using tools like `nc`, `telnet`, or the provided tiny Python snippet:

```python
import socket, json
cmd = "get data engineer jobs near portland, or within 15 miles\n"
with socket.create_connection(("localhost", 5555)) as sock:
    sock.sendall(cmd.encode())
    resp = sock.recv(65536).decode().strip()
print(json.loads(resp))
```

---

## Project Structure
```
job_scraper_server/
├── main.py          # CLI entry point
├── server.py        # Core TCP server
├── parser.py        # Command → Query
├── scraper.py       # Monster web-scraper
├── models.py        # Data classes
├── config.py        # Settings / user-agents
├── requirements.txt # Python dependencies
└── README.md        # You are here
```

---

### License
MIT © 2025
