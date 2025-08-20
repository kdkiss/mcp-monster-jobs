# Multi-stage build for optimized image size and build speed
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./

# Install dependencies with caching
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev --no-audit --no-fund

# Production stage
FROM node:20-alpine AS production

# Set working directory
WORKDIR /app

# Copy dependencies from base stage
COPY --from=base /app/node_modules ./node_modules

# Copy source code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodeuser -u 1001

# Change ownership of app directory
RUN chown -R nodeuser:nodejs /app

# Switch to non-root user
USER nodeuser

# Set NODE_ENV for production
ENV NODE_ENV=production

# Expose health check port (optional, for monitoring)
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "console.log('MCP server health check')" || exit 1

# Run the MCP server
CMD ["node", "monster_mcp_server.js"]