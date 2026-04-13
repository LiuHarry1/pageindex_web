# Build from the repository root:
#   docker build -f web/frontend/Dockerfile .
#
# Use bookworm (glibc): Vite 8 / LightningCSS prebuilds are reliable on linux/amd64+arm64.
# If this file is saved with CRLF on Windows, RUN lines break (npm sees "ci\r"); keep LF — see .gitattributes.

FROM node:22-alpine AS build

WORKDIR /app

COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY web/frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY web/frontend/nginx.conf /etc/nginx/templates/default.conf.template

ENV API_URL=http://backend:8008

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
