# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install system dependencies if needed
RUN apk add --no-cache curl

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables for production
ENV PORT=8081
ENV HOST=0.0.0.0
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Add health check using curl instead of Python to avoid import issues
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8081/ready || exit 1

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Expose port
EXPOSE 8081

# Run the application directly using the venv Python
CMD ["python", "src/main.py"]