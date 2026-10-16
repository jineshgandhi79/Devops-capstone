# ==========================================
# Stage 1: Build the React application
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy package manifests first for optimal layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and compile the production bundle
COPY . .
RUN npm run build

# ==========================================
# Stage 2: Serve static assets with unprivileged Nginx
# ==========================================
FROM nginxinc/nginx-unprivileged:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
