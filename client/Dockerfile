# syntax=docker/dockerfile:1

# ---- Base deps ----------------------------------------------------------
FROM node:22-slim AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc,required=false \
    npm ci

# ---- Development --------------------------------------------------------
FROM node:22-slim AS development

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---- Build --------------------------------------------------------------
FROM deps AS build

COPY . .
RUN npm run build

# ---- Production (static files served by nginx) --------------------------
FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
