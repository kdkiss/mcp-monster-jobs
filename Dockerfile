FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Expose any necessary ports (MCP servers typically communicate via stdio)
# No ports needed for stdio-based MCP servers

# Set user to non-root
USER node

# Run the MCP server
CMD ["node", "monster_mcp_server.js"]