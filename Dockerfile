# Use Python 3.11 slim image for smaller container size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=false

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Create database directory and ensure proper permissions
RUN mkdir -p src/database && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for smithery.com compatibility
EXPOSE 5000

# Set the startup command
CMD ["python", "src/main.py"]