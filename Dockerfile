# Use a more stable Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies with better error handling
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=60 -r requirements.txt || \
    (echo "Failed to install dependencies" && exit 1)

# Copy application code
COPY . .

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python monster_server.py --health || exit 1

# Run the server
CMD ["python", "monster_server.py"]
