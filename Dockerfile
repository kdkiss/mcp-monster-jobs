FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including git for MCP SDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=60 -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python monster_server.py --health || exit 1

# Run the server
CMD ["python", "monster_server.py"]