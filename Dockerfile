# Use lightweight Python image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the MCP Monster job search server
ENTRYPOINT ["python", "monster_server.py"]

