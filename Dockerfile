# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation and optimization
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8081
ENV HOST=0.0.0.0

# Install system dependencies (minimal set)
RUN apk add --no-cache curl && \
    apk cache clean

# Install dependencies first (for better caching)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy source code and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Set up environment
ENV PATH="/app/.venv/bin:$PATH"

# Health check with faster intervals for deployment
HEALTHCHECK --interval=30s --timeout=10s --retries=2 --start-period=10s \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose port and run
EXPOSE 8081
CMD ["python", "src/main.py"]