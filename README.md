# MCP Monster Jobs Server

This is a Smithery-compatible MCP server for searching and retrieving job listings from Monster.com.

## Features

- Search for jobs with query, location, and radius filters.
- Get detailed information for a specific job.
- Lightweight implementation using `fetch` and `cheerio`.

## Prerequisites

- Node.js >= 18.0.0
- Docker

## Running Locally

1.  Install dependencies:
    ```sh
    npm install
    ```

2.  Run the server:
    ```sh
    node monster_mcp_server.js
    ```

## Building and Running with Docker

1.  Build the Docker image:
    ```sh
    docker build -t mcp-monster-jobs .
    ```

2.  Run the Docker container:
    ```sh
    docker run -i --rm mcp-monster-jobs
    ```

## Smithery Integration

This server is packaged for use with [Smithery](https://smithery.dev/).

1.  Build the Smithery package:
    ```sh
    smithery build
    ```

2.  Install the package:
    ```sh
    smithery install <path-to-package.tar.gz>
    ```

3.  Run the server via Smithery:
    ```sh
    smithery run mcp-monster-jobs