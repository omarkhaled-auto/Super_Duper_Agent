# =============================================================================
# Bayan API - Multi-stage Dockerfile for .NET 8
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /src

# Copy solution and project files for layer caching
COPY *.sln .
COPY Bayan.Domain/*.csproj ./Bayan.Domain/
COPY Bayan.Application/*.csproj ./Bayan.Application/
COPY Bayan.Infrastructure/*.csproj ./Bayan.Infrastructure/
COPY Bayan.API/*.csproj ./Bayan.API/

# Restore dependencies (API project only, skipping Tests which is excluded by .dockerignore)
RUN dotnet restore Bayan.API/Bayan.API.csproj

# Copy source code
COPY . .

# Build the application
RUN dotnet build Bayan.API/Bayan.API.csproj -c Release --no-restore

# Publish the application
RUN dotnet publish Bayan.API/Bayan.API.csproj -c Release -o /app/publish --no-build

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS runtime
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl icu-libs

# Set environment variables
ENV ASPNETCORE_URLS=http://+:80
ENV ASPNETCORE_ENVIRONMENT=Production
ENV DOTNET_RUNNING_IN_CONTAINER=true
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false

# Create non-root user for security
RUN addgroup -S bayangroup && adduser -S bayanuser -G bayangroup
USER bayanuser

# Copy published application
COPY --from=build --chown=bayanuser:bayangroup /app/publish .

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Entry point
ENTRYPOINT ["dotnet", "Bayan.API.dll"]
