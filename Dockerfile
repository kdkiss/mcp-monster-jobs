FROM node:18-alpine

RUN apk add --no-cache chromium

WORKDIR /app

COPY monster_package_json.json package.json

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

RUN npm install --production

COPY monster_mcp_server.js index.js

CMD ["npm", "start"]