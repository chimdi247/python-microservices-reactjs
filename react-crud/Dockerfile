# Stage 1: Build static assets
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Create React App inlines REACT_APP_* variables at build time, so they
# must be provided as build args (see docker-compose.yml's `client` service).
ARG REACT_APP_ADMIN_API_URL=http://localhost:8000
ARG REACT_APP_MAIN_API_URL=http://localhost:8001
ENV REACT_APP_ADMIN_API_URL=$REACT_APP_ADMIN_API_URL
ENV REACT_APP_MAIN_API_URL=$REACT_APP_MAIN_API_URL

RUN npm run build

# Stage 2: Serve static assets with Nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
