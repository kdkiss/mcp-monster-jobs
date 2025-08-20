FROM node:18-alpine

WORKDIR /app

COPY monster_package_json.json package.json

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

RUN apk add --no-cache chromium && npm ci --only=production

COPY monster_mcp_server.js .

CMD ["node", "monster_mcp_server.js"]