FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --production
COPY smithery.yaml monster_mcp_server.js ./
CMD ["node", "monster_mcp_server.js"]