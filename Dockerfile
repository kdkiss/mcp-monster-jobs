FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project config
COPY pyproject.toml .

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ .

# Start the server
CMD ["uv", "run", "python", "main.py"]