FROM zenika/alpine-chrome:with-node

WORKDIR /app

COPY monster_package_json.json package.json

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

RUN npm install --production --no-optional

COPY monster_mcp_server.js monster_mcp_server.js

CMD ["node", "monster_mcp_server.js"]