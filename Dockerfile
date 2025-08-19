# Use the recommended Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Install git so we can install the mcp dependency from github
# apk add --no-cache is the alpine equivalent of apt-get install -y
RUN apk add --no-cache git

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt using uv
RUN uv pip install --no-cache -r requirements.txt

# Copy the rest of the application's code to the container
COPY . .

# Run monster_server.py when the container launches
CMD ["python", "monster_server.py"]
