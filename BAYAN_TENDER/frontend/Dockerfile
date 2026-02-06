# =============================================================================
# Bayan UI - Multi-stage Dockerfile for Angular 18
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

# Build argument for API URL
ARG API_URL=http://localhost:5000

# Install Angular CLI globally
RUN npm install -g @angular/cli@18

# Copy package files for layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build the Angular application for production
RUN npm run build -- --configuration=production

# -----------------------------------------------------------------------------
# Stage 2: Runtime with Nginx
# -----------------------------------------------------------------------------
FROM nginx:alpine AS runtime

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx configuration
RUN rm -rf /usr/share/nginx/html/*
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# Copy built application from build stage
COPY --from=build /app/dist/bayan-ui/browser /usr/share/nginx/html

# Create non-root user for security (nginx runs as nginx user by default)
RUN chown -R nginx:nginx /usr/share/nginx/html
RUN chown -R nginx:nginx /var/cache/nginx
RUN chown -R nginx:nginx /var/log/nginx
RUN touch /var/run/nginx.pid && chown nginx:nginx /var/run/nginx.pid

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
