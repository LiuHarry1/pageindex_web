# Build from the repository root:
#   docker build -f web/frontend/Dockerfile .

FROM node:22-alpine AS build

WORKDIR /app

COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci

COPY web/frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY web/frontend/nginx.conf /etc/nginx/templates/default.conf.template

ENV API_URL=http://backend:8008

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
