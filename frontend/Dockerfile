# KicMPi RAG — frontend (multi-stage: Vite build → nginx)
# See PLAN_WEBAPP_V1.md §4.2: nginx serves the SPA and proxies /api → backend.

# ── build stage ───────────────────────────────────────────────────────────────
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# ── serve stage ───────────────────────────────────────────────────────────────
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
