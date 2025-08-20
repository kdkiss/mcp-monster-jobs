FROM node:18-slim
WORKDIR /app
COPY monster_package_json.json package.json
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
RUN npm install --production
COPY monster_mcp_server.js .
CMD ["node", "monster_mcp_server.js"]