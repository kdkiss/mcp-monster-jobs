FROM node:18-alpine
WORKDIR /app
COPY package.json package.json
RUN npm install
COPY monster_mcp_server.js .
CMD ["node", "monster_mcp_server.js"]