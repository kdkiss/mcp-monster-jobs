FROM node:18-alpine
WORKDIR /app
COPY monster_package_json.json package.json
RUN npm install
COPY monster_mcp_server.js .
CMD ["node", "monster_mcp_server.js"]