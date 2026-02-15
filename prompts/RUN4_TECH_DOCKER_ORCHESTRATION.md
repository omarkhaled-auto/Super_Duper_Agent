# Run 4 Tech Research: Docker Compose Orchestration for 6+ Services

> **Purpose**: Exhaustive Docker Compose reference for Run 4's end-to-end wiring of all Super Agent Team services
> **Scope**: Multi-file compose merging, inter-container DNS, health check cascading, volume sharing, Traefik integration, Testcontainers for pytest
> **Sources**: Docker Compose v2 docs (Context7), Testcontainers Python 4.x docs (Context7), BUILD1_PRD.md, BUILD3_PRD.md, BUILD3_ARCHITECTURE_PLAN.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md

---

## Table of Contents

1. [Service Inventory](#1-service-inventory)
2. [Docker Compose Multi-File Merging](#2-docker-compose-multi-file-merging)
3. [Inter-Container DNS Resolution](#3-inter-container-dns-resolution)
4. [Health Check Cascading](#4-health-check-cascading)
5. [Volume Sharing Across Compose Files](#5-volume-sharing-across-compose-files)
6. [6+ Service Orchestration Patterns](#6-six-service-orchestration-patterns)
7. [Traefik Integration](#7-traefik-integration)
8. [Testing Infrastructure with Testcontainers](#8-testing-infrastructure-with-testcontainers)
9. [Recommended Run 4 Docker Topology](#9-recommended-run-4-docker-topology)
10. [Complete Compose File Templates](#10-complete-compose-file-templates)

---

## 1. Service Inventory

### All Services Across 3 Builds

| Service | Build | Port | Health Endpoint | Database | Network Membership |
|---------|-------|------|-----------------|----------|-------------------|
| **architect** | Build 1 | 8001 (internal 8000) | `/api/health` | SQLite (architect.db) | backend, frontend |
| **contract-engine** | Build 1 | 8002 (internal 8000) | `/api/health` | SQLite (contracts.db) | backend, frontend |
| **codebase-intelligence** | Build 1 | 8003 (internal 8000) | `/api/health` | SQLite (symbols.db) + ChromaDB | backend, frontend |
| **postgres** | Shared | 5432 | pg_isready | PostgreSQL 16 | backend |
| **redis** | Shared | 6379 | redis-cli ping | Redis 7 | backend |
| **traefik** | Build 3 | 80, 8080 | traefik healthcheck --ping | N/A | frontend |
| **migrations** | Build 3 | N/A (one-shot) | N/A | N/A | backend |
| **generated-service-N** | Build 2 output | 8080+ (varies) | `/health` | Depends on service | backend, frontend |

### Service Count by Phase

- **Build 1 standalone**: 3 services + health checks (no external DB, uses SQLite)
- **Build 3 standalone**: Traefik + Postgres + Redis + migrations = 4 infrastructure services
- **Run 4 combined**: 3 (Build 1) + 4 (Build 3 infra) + N (generated services) = **7 + N services**
- **Typical Run 4**: 10-14 services total (3 foundation + 4 infra + 3-7 generated)

---

## 2. Docker Compose Multi-File Merging

### 2.1 The `-f` Flag Pattern

Docker Compose v2 merges multiple compose files using the `-f` flag. Later files override earlier ones. Services with the same name are merged; new services are appended.

```bash
# Merge base + override
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Merge base + test environment
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d

# Three-file merge for Run 4
docker compose \
  -f docker-compose.build1.yml \
  -f docker-compose.generated.yml \
  -f docker-compose.run4.yml \
  up -d
```

### 2.2 Merge Semantics

When two compose files define the same service, the rules are:

| Field Type | Merge Behavior |
|-----------|----------------|
| **Scalar** (image, command) | Later file wins (overrides) |
| **Mapping** (environment, labels) | Deep merge (keys from both, later wins on conflict) |
| **Sequence** (ports, volumes, depends_on) | Concatenated (appended, not replaced) |
| **build context** | Later file wins entirely |

**Example — Base file (`docker-compose.build1.yml`):**

```yaml
services:
  architect:
    build:
      context: ./src/architect
      dockerfile: Dockerfile
    environment:
      DATABASE_PATH: /data/architect.db
      LOG_LEVEL: info
    networks:
      - super-team-net
    volumes:
      - architect-data:/data
```

**Override file (`docker-compose.run4.yml`):**

```yaml
services:
  architect:
    environment:
      LOG_LEVEL: debug                    # Overrides 'info'
      CONTRACT_ENGINE_URL: http://contract-engine:8000  # Added
    depends_on:
      contract-engine:
        condition: service_healthy        # Appended
    networks:
      - frontend                          # Appended to existing networks
```

**Result after merge**: architect has `LOG_LEVEL=debug`, both `DATABASE_PATH` and `CONTRACT_ENGINE_URL`, networks `super-team-net` AND `frontend`, depends_on `contract-engine`.

### 2.3 The `COMPOSE_FILE` Environment Variable

Instead of `-f` flags, set `COMPOSE_FILE` to auto-merge:

```bash
# Colon-separated on Linux/macOS, semicolon on Windows
export COMPOSE_FILE="docker-compose.build1.yml:docker-compose.generated.yml:docker-compose.run4.yml"
docker compose up -d
```

### 2.4 The `extends` Directive (Compose v2.24+)

Services can extend definitions from other files:

```yaml
# docker-compose.run4.yml
services:
  architect:
    extends:
      file: docker-compose.build1.yml
      service: architect
    # Additional overrides
    depends_on:
      postgres:
        condition: service_healthy
```

**Limitation**: `extends` does not support `depends_on`, `volumes_from`, or `links` from the extended service. For Run 4, multi-file merge with `-f` is more predictable.

### 2.5 Recommended File Structure for Run 4

```
super-team/
  docker/
    docker-compose.build1.yml        # Build 1: architect, contract-engine, codebase-intel
    docker-compose.infra.yml         # Shared: postgres, redis
    docker-compose.generated.yml     # Build 3 generates: N application services
    docker-compose.traefik.yml       # Build 3: Traefik gateway
    docker-compose.run4.yml          # Run 4: overrides, cross-build wiring, test config
    docker-compose.test.yml          # Test-only: port mappings, ephemeral volumes
    traefik/
      traefik.yml                    # Static Traefik config
```

**Run 4 production:**
```bash
docker compose \
  -p super-team \
  -f docker/docker-compose.infra.yml \
  -f docker/docker-compose.build1.yml \
  -f docker/docker-compose.generated.yml \
  -f docker/docker-compose.traefik.yml \
  -f docker/docker-compose.run4.yml \
  up -d
```

**Run 4 testing:**
```bash
docker compose \
  -p super-team-test \
  -f docker/docker-compose.infra.yml \
  -f docker/docker-compose.build1.yml \
  -f docker/docker-compose.generated.yml \
  -f docker/docker-compose.traefik.yml \
  -f docker/docker-compose.test.yml \
  up -d
```

---

## 3. Inter-Container DNS Resolution

### 3.1 Default Docker Compose Networking

Docker Compose v2 creates a default bridge network named `{project_name}_default`. All services on the same network can resolve each other by **service name** as hostname.

```
Service Name in YAML  →  DNS Hostname
─────────────────────────────────────
architect             →  architect
contract-engine       →  contract-engine
codebase-intelligence →  codebase-intelligence  (NOTE: hyphens are valid)
postgres              →  postgres
redis                 →  redis
traefik               →  traefik
```

### 3.2 Service-to-Service Communication URLs

Based on Build 1's config defaults (from `src/shared/config.py`):

```python
# Build 1 service configs use these default URLs
CONTRACT_ENGINE_URL = "http://contract-engine:8000"   # Internal port
CODEBASE_INTEL_URL = "http://codebase-intel:8000"      # Internal port
```

**Important**: Build 1 services listen on port `8000` internally (uvicorn default) but are mapped to `8001/8002/8003` on the host. Inter-container traffic uses the **internal** port.

### 3.3 Custom Network Topology

Run 4 needs network isolation between:
- **frontend**: Traefik + application services (HTTP-facing)
- **backend**: Application services + databases (data tier)

```
                     ┌─────────────────────────────┐
                     │       frontend network       │
                     │                              │
                     │  traefik ──── architect       │
                     │         ──── contract-engine  │
                     │         ──── codebase-intel   │
                     │         ──── auth-service     │
                     │         ──── orders-service   │
                     └───────────┬──────────────────┘
                                 │
                     ┌───────────┴──────────────────┐
                     │       backend network         │
                     │                               │
                     │  postgres ──── architect       │
                     │           ──── contract-engine │
                     │           ──── auth-service    │
                     │  redis    ──── orders-service  │
                     │  codebase-intel (ChromaDB)     │
                     └───────────────────────────────┘
```

**Key rule**: Traefik is **only** on the frontend network. Postgres/Redis are **only** on the backend network. Application services span both.

```yaml
networks:
  frontend:
    driver: bridge
    name: super-team-frontend
  backend:
    driver: bridge
    name: super-team-backend
    internal: true   # No external access — only inter-container
```

### 3.4 Cross-Network Communication

Services on different networks **cannot** communicate directly. This is intentional — Traefik should not access databases, and databases should not be exposed externally.

If a service needs to talk to another service on a different network, both must share at least one network:

```yaml
services:
  # Architect needs both: Traefik (frontend) and Postgres (backend)
  architect:
    networks:
      - frontend   # Traefik can route to it
      - backend    # Can reach postgres
```

### 3.5 DNS Resolution with Multiple Networks

When a service is on multiple networks, DNS resolution uses the first matching network. For service-to-service calls, the DNS name resolves to the IP on the shared network.

```
architect → contract-engine   # Resolves via backend network (both are on it)
traefik   → architect         # Resolves via frontend network (both are on it)
traefik   → postgres          # FAILS — no shared network
```

### 3.6 Build 1 Specifics: SQLite Volume Paths

Build 1 uses SQLite (not Postgres) for its internal databases. Each service has its own database file:

```yaml
services:
  architect:
    volumes:
      - architect-data:/data
    environment:
      DATABASE_PATH: /data/architect.db

  contract-engine:
    volumes:
      - contract-data:/data
    environment:
      DATABASE_PATH: /data/contracts.db

  codebase-intelligence:
    volumes:
      - intel-data:/data
      - chroma-data:/data/chroma
    environment:
      DATABASE_PATH: /data/symbols.db
      CHROMA_PATH: /data/chroma
      GRAPH_PATH: /data/graph.json
```

---

## 4. Health Check Cascading

### 4.1 `depends_on` with `condition: service_healthy`

Docker Compose v2 supports three conditions:

| Condition | Behavior |
|-----------|----------|
| `service_started` | Default. Starts after container launches (may not be ready). |
| `service_healthy` | Starts after health check passes. Requires `healthcheck` on dependency. |
| `service_completed_successfully` | Starts after one-shot container exits with code 0. |

```yaml
services:
  migrations:
    build: ./migrations
    depends_on:
      postgres:
        condition: service_healthy
    # One-shot: runs and exits

  architect:
    depends_on:
      postgres:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
```

### 4.2 Health Check Configuration Parameters

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
  interval: 10s       # Time between checks
  timeout: 5s         # Max time per check
  retries: 3          # Failures before "unhealthy"
  start_period: 30s   # Grace period (failures don't count)
```

**Best practices per service type:**

| Service Type | Health Check | start_period | interval | retries |
|-------------|-------------|-------------|----------|---------|
| PostgreSQL | `pg_isready -U $USER -d $DB` | 30s | 10s | 5 |
| Redis | `redis-cli ping \| grep PONG` | 10s | 10s | 3 |
| FastAPI (Python) | `curl -f http://localhost:PORT/api/health` or `python -c "import urllib.request; urllib.request.urlopen('http://localhost:PORT/api/health')"` | 30s | 15s | 3 |
| Traefik | `traefik healthcheck --ping` (requires `--ping=true`) | 15s | 10s | 3 |
| Node.js | `curl -f http://localhost:PORT/health` | 20s | 15s | 3 |
| Migrations | N/A (one-shot) | N/A | N/A | N/A |

### 4.3 Cascading Dependency Chain

Run 4's dependency graph:

```
                    postgres
                   /    |    \
                  /     |     \
          migrations    |      redis
              |         |        |
              v         v        v
          architect  contract-engine  codebase-intelligence
              \         |         /           |
               \        |        /            |
                v       v       v             v
                  traefik              generated-services
                                   (depend on architect + contract-engine)
```

**Expressed in compose:**

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s

  redis:
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s

  migrations:
    depends_on:
      postgres:
        condition: service_healthy

  architect:
    depends_on:
      postgres:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s

  contract-engine:
    depends_on:
      postgres:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s

  codebase-intelligence:
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 5          # ChromaDB model download may take longer
      start_period: 60s   # Extra time for embedding model init

  traefik:
    depends_on:
      architect:
        condition: service_healthy
      contract-engine:
        condition: service_healthy
      codebase-intelligence:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

  # Generated services depend on Build 1 being healthy
  auth-service:
    depends_on:
      postgres:
        condition: service_healthy
      contract-engine:
        condition: service_healthy
```

### 4.4 Startup Order Guarantees

Docker Compose guarantees:
1. Dependencies start **before** dependents
2. With `service_healthy`, the dependent waits until the health check passes
3. With `service_completed_successfully`, the dependent waits until exit code 0

Docker Compose does NOT guarantee:
- That a service is **fully initialized** just because its health check passed once (transient health)
- That services start in a **fixed order** within the same dependency tier

### 4.5 Using `curl` vs `python` for Health Checks

Build 1 uses `python:3.12-slim` as the base image, which does NOT include `curl`. Use Python's stdlib instead:

```yaml
# WRONG — curl not available in python:3.12-slim
test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]

# CORRECT — use Python stdlib
test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
```

For Node.js services that include `curl` or `wget`, use those directly.

---

## 5. Volume Sharing Across Compose Files

### 5.1 Named Volumes vs Bind Mounts

| Type | Syntax | Persistence | Cross-Container | Use Case |
|------|--------|-------------|-----------------|----------|
| **Named volume** | `volume-name:/path` | Persists across restarts | Yes (same volume name) | Database data, indexes |
| **Bind mount** | `./host/path:/container/path` | Host filesystem | Yes (same host path) | Source code, config files |
| **tmpfs** | `tmpfs: /path` | Memory only | No | Temp data, secrets |

### 5.2 Named Volumes for Build 1 Services

```yaml
volumes:
  # Build 1 data
  architect-data:
    name: super-team-architect-data
  contract-data:
    name: super-team-contract-data
  intel-data:
    name: super-team-intel-data
  chroma-data:
    name: super-team-chroma-data

  # Shared infrastructure
  pgdata:
    name: super-team-pgdata

  # Shared artifact directory (Run 4)
  shared-artifacts:
    name: super-team-artifacts
```

### 5.3 Contract Registry Data Sharing

The contract registry is the critical shared data between Build 1 (Contract Engine stores contracts) and Build 2/3 (services read contracts). Two approaches:

**Approach A — HTTP API (Recommended):**
Services query the Contract Engine via its REST API at `http://contract-engine:8000/api/contracts`. No volume sharing needed.

**Approach B — Shared Volume (Fallback):**
If MCP or HTTP is unavailable, share the SQLite database file:

```yaml
services:
  contract-engine:
    volumes:
      - contract-data:/data
    environment:
      DATABASE_PATH: /data/contracts.db

  # Generated service reads contracts via shared volume
  auth-service:
    volumes:
      - contract-data:/contracts:ro    # Read-only access
```

**Warning**: SQLite with WAL mode supports concurrent readers but only ONE writer. If both Contract Engine and a generated service write to the same file, you get `database is locked` errors. Use read-only mount (`:ro`) for consumers.

### 5.4 Codebase Intelligence Index Sharing

The Codebase Intelligence service maintains three data stores:
1. **symbols.db** (SQLite) — symbol table
2. **chroma/** (ChromaDB) — vector embeddings
3. **graph.json** (NetworkX) — dependency graph

```yaml
services:
  codebase-intelligence:
    volumes:
      - intel-data:/data
      - chroma-data:/data/chroma
    environment:
      DATABASE_PATH: /data/symbols.db
      CHROMA_PATH: /data/chroma
      GRAPH_PATH: /data/graph.json
```

For Run 4, generated services query Codebase Intelligence via MCP or HTTP, not via shared volumes.

### 5.5 Artifact Directory Patterns

Run 4 needs a shared directory for build artifacts, generated code, and reports:

```yaml
services:
  # Super Orchestrator writes artifacts
  super-orchestrator:
    volumes:
      - shared-artifacts:/artifacts
      - ./output:/output                # Host-accessible output

  # Generated services are built from artifact directories
  auth-service:
    build:
      context: /artifacts/auth-service   # Built from shared artifacts
```

### 5.6 Volume Declarations Across Compose Files

Named volumes must be declared in the top-level `volumes:` section. When merging files, volume declarations are merged (same name = same volume):

```yaml
# docker-compose.build1.yml
volumes:
  architect-data:
  contract-data:
  intel-data:

# docker-compose.run4.yml
volumes:
  architect-data:     # Same volume — merged, not duplicated
  pgdata:             # New volume — appended
  shared-artifacts:   # New volume — appended
```

---

## 6. Six+ Service Orchestration Patterns

### 6.1 Startup Ordering for Complex Dependency Graphs

For 10+ services, use a tiered startup approach:

```
Tier 0 (Infrastructure):  postgres, redis
Tier 1 (Migrations):      migrations (service_completed_successfully)
Tier 2 (Foundation):      architect, contract-engine, codebase-intelligence
Tier 3 (Gateway):         traefik
Tier 4 (Application):     auth-service, orders-service, notifications-service, ...
```

Each tier waits for the previous tier's health checks to pass before starting.

### 6.2 Resource Limits and Allocation

For parallel services, set memory and CPU limits to prevent OOM:

```yaml
services:
  architect:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
          cpus: "0.25"

  codebase-intelligence:
    deploy:
      resources:
        limits:
          memory: 1G          # ChromaDB + embedding model needs more RAM
          cpus: "1.0"
        reservations:
          memory: 512M

  postgres:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    # Shared memory for PostgreSQL
    shm_size: "256mb"
```

**Total resource budget for Run 4** (conservative):
- 3 Build 1 services: 512M + 512M + 1G = 2G RAM
- Postgres + Redis: 512M + 128M = 640M RAM
- Traefik: 128M RAM
- N generated services: N * 512M RAM
- **Total**: ~3G base + N * 512M

### 6.3 Log Aggregation Across Services

Use Docker Compose logging configuration for consistent log collection:

```yaml
# Apply to all services via x-logging anchor
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    tag: "{{.Name}}"

services:
  architect:
    logging: *default-logging

  contract-engine:
    logging: *default-logging
```

**Viewing logs from all services:**

```bash
# All services
docker compose -p super-team logs -f

# Specific services
docker compose -p super-team logs -f architect contract-engine

# Last 100 lines with timestamps
docker compose -p super-team logs --tail=100 -t

# Filter by service
docker compose -p super-team logs -f --since="5m" architect
```

### 6.4 Graceful Shutdown Sequencing

Docker Compose stops services in reverse dependency order. For Run 4:

1. Generated services stop first (no dependents)
2. Traefik stops (dependents already stopped)
3. Build 1 services stop (architect, contract-engine, codebase-intelligence)
4. Migrations container is already exited
5. Postgres and Redis stop last

Configure `stop_grace_period` for clean shutdown:

```yaml
services:
  architect:
    stop_grace_period: 10s     # FastAPI needs time to finish requests

  postgres:
    stop_grace_period: 30s     # PostgreSQL needs time to flush WAL

  codebase-intelligence:
    stop_grace_period: 15s     # ChromaDB needs time to persist
```

### 6.5 Docker Compose `ps` and Status Monitoring

```bash
# JSON output for programmatic parsing (used by DockerOrchestrator)
docker compose -p super-team ps --format json

# Check service health status
docker compose -p super-team ps --filter "status=running"

# Get mapped port
docker compose -p super-team port architect 8000
```

### 6.6 Parallel Service Startup

Docker Compose v2 starts independent services in parallel by default. The `COMPOSE_PARALLEL_LIMIT` environment variable controls maximum parallelism:

```bash
# Limit to 4 parallel container starts (useful on resource-constrained machines)
export COMPOSE_PARALLEL_LIMIT=4
docker compose up -d
```

---

## 7. Traefik Integration

### 7.1 Traefik v3 Docker Provider Auto-Discovery

Traefik automatically discovers Docker containers via labels. No manual routing configuration needed.

**Static configuration (`traefik.yml`):**

```yaml
# traefik/traefik.yml
api:
  dashboard: false         # Disable dashboard in production

entryPoints:
  web:
    address: ":80"

providers:
  docker:
    exposedByDefault: false  # Only route services with traefik.enable=true
    network: super-team-frontend  # Use frontend network for routing

ping:
  entryPoint: web          # Enable health check endpoint
```

### 7.2 Service Labels for Routing

Each service declares its routing rules via Docker labels:

```yaml
services:
  architect:
    labels:
      # Enable Traefik routing
      - "traefik.enable=true"

      # Router: match requests to /api/architect/*
      - "traefik.http.routers.architect.rule=PathPrefix(`/api/architect`)"
      - "traefik.http.routers.architect.entrypoints=web"

      # Service: forward to port 8000 inside the container
      - "traefik.http.services.architect.loadbalancer.server.port=8000"

      # Middleware: strip the prefix before forwarding
      - "traefik.http.middlewares.architect-strip.stripprefix.prefixes=/api/architect"
      - "traefik.http.routers.architect.middlewares=architect-strip"
```

**Note**: Traefik v3 uses backtick syntax for `PathPrefix` rules: `` PathPrefix(`/api/architect`) ``. In Python code, use string concatenation or raw strings to produce backticks.

### 7.3 Run 4 Routing Table

| Path Prefix | Service | Internal Port | Description |
|-------------|---------|---------------|-------------|
| `/api/architect` | architect | 8000 | PRD decomposition |
| `/api/contracts` | contract-engine | 8000 | Contract registry |
| `/api/codebase` | codebase-intelligence | 8000 | Code index queries |
| `/api/auth` | auth-service | 8080 | Authentication (generated) |
| `/api/orders` | orders-service | 8080 | Order management (generated) |
| `/api/notifications` | notifications-service | 8080 | Notifications (generated) |

### 7.4 Health Check Routing

Traefik automatically removes unhealthy services from its routing pool. Combined with Docker health checks:

```yaml
services:
  auth-service:
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth.rule=PathPrefix(`/api/auth`)"
      - "traefik.http.services.auth.loadbalancer.server.port=8080"
      - "traefik.http.services.auth.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.auth.loadbalancer.healthcheck.interval=10s"
```

### 7.5 Service-to-Service Through Traefik

For Run 4, inter-service calls can go through Traefik (via `http://traefik/api/service-name`) or directly (via `http://service-name:port`). **Direct is recommended** for internal calls to avoid extra latency:

```python
# Direct service-to-service (recommended for internal calls)
CONTRACT_ENGINE_URL = "http://contract-engine:8000"

# Through Traefik (use for external/gateway access only)
# http://traefik/api/contracts
```

### 7.6 Traefik Compose Service Definition

```yaml
services:
  traefik:
    image: traefik:v3.6
    command:
      - "--api.dashboard=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedByDefault=false"
      - "--providers.docker.network=super-team-frontend"
      - "--entrypoints.web.address=:80"
      - "--ping=true"
    ports:
      - "80:80"
      - "8080:8080"           # Traefik API port (for debugging)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    networks:
      - frontend
    restart: unless-stopped
```

---

## 8. Testing Infrastructure with Testcontainers

### 8.1 Testcontainers Python — DockerCompose Class

Testcontainers 4.x provides a `DockerCompose` class that manages compose stacks from pytest:

```python
from testcontainers.compose import DockerCompose
import requests

def test_full_stack():
    compose = DockerCompose(
        context="./docker",
        compose_file_name="docker-compose.yml",
        pull=True,
        build=True
    )

    with compose:
        # Services start, health checks run
        host = compose.get_service_host("architect", 8000)
        port = compose.get_service_port("architect", 8000)

        response = requests.get(f"http://{host}:{port}/api/health")
        assert response.status_code == 200

        # Execute command inside container
        stdout, stderr, exit_code = compose.exec_in_container(
            service_name="postgres",
            command=["psql", "-U", "superteam", "-c", "SELECT 1"]
        )
        assert exit_code == 0
```

### 8.2 Multiple Compose Files

```python
from testcontainers.compose import DockerCompose

compose = DockerCompose(
    context="./docker",
    compose_file_name=[
        "docker-compose.infra.yml",
        "docker-compose.build1.yml",
        "docker-compose.generated.yml",
        "docker-compose.test.yml"
    ]
)
```

### 8.3 Wait Strategies for Complex Services

```python
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy, LogMessageWaitStrategy

compose = DockerCompose(
    context="./docker",
    compose_file_name="docker-compose.yml"
)

with compose.waiting_for({
    "postgres": LogMessageWaitStrategy("database system is ready"),
    "redis": LogMessageWaitStrategy("Ready to accept connections"),
    "architect": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
    "contract-engine": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
    "codebase-intelligence": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
    "traefik": HttpWaitStrategy(80).for_status_code(200).for_path("/ping"),
}):
    # All services are healthy — run tests
    web_host = compose.get_service_host("traefik", 80)
    web_port = compose.get_service_port("traefik", 80)

    # Test through gateway
    response = requests.get(f"http://{web_host}:{web_port}/api/architect/health")
    assert response.status_code == 200
```

### 8.4 Pytest Fixture Pattern

```python
import pytest
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy, LogMessageWaitStrategy

@pytest.fixture(scope="session")
def compose_stack():
    """Start the full compose stack once for all tests."""
    compose = DockerCompose(
        context="./docker",
        compose_file_name=[
            "docker-compose.infra.yml",
            "docker-compose.build1.yml",
            "docker-compose.generated.yml",
            "docker-compose.test.yml"
        ],
        pull=True,
        build=True
    )

    with compose.waiting_for({
        "postgres": LogMessageWaitStrategy("database system is ready"),
        "architect": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
        "contract-engine": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
    }) as stack:
        yield stack

@pytest.fixture(scope="session")
def architect_url(compose_stack):
    """Get the architect service URL."""
    host = compose_stack.get_service_host("architect", 8000)
    port = compose_stack.get_service_port("architect", 8000)
    return f"http://{host}:{port}"

@pytest.fixture(scope="session")
def contract_engine_url(compose_stack):
    """Get the contract engine service URL."""
    host = compose_stack.get_service_host("contract-engine", 8000)
    port = compose_stack.get_service_port("contract-engine", 8000)
    return f"http://{host}:{port}"


# Usage in tests
def test_architect_health(architect_url):
    response = requests.get(f"{architect_url}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_decompose_prd(architect_url):
    prd_text = open("sample_data/sample_prd.md").read()
    response = requests.post(
        f"{architect_url}/api/decompose",
        json={"prd_text": prd_text}
    )
    assert response.status_code == 201
    result = response.json()
    assert "service_map" in result
    assert len(result["service_map"]["services"]) >= 2
```

### 8.5 Port Mapping for Test Access

Testcontainers maps container ports to random host ports to avoid conflicts:

```python
# Container exposes 8000, mapped to random host port
host = compose.get_service_host("architect", 8000)  # "localhost" or "127.0.0.1"
port = compose.get_service_port("architect", 8000)   # Random port like 55432

# Use the mapped port for test HTTP calls
url = f"http://{host}:{port}/api/health"
```

### 8.6 Cleanup and Isolation Between Test Runs

```python
@pytest.fixture(scope="session", autouse=True)
def cleanup_compose():
    """Ensure compose stack is cleaned up even on test failure."""
    yield
    # DockerCompose context manager handles cleanup automatically
    # But for extra safety:
    import subprocess
    subprocess.run(
        ["docker", "compose", "-p", "super-team-test", "down", "-v", "--remove-orphans"],
        capture_output=True
    )

@pytest.fixture(autouse=True)
def reset_database(compose_stack):
    """Reset database between tests for isolation."""
    yield
    # Clean up test data
    compose_stack.exec_in_container(
        service_name="postgres",
        command=["psql", "-U", "superteam", "-d", "superteam", "-c",
                "TRUNCATE users, orders, notifications CASCADE"]
    )
```

### 8.7 DockerOrchestrator Integration

Build 3's `DockerOrchestrator` class uses `docker compose` subprocess calls (not Testcontainers). For Run 4 tests, wrap it:

```python
class DockerOrchestrator:
    """Manages Docker Compose lifecycle."""

    def __init__(self, compose_file: Path, project_name: str = "super-team"):
        self.compose_file = compose_file
        self.project_name = project_name

    async def start_services(self) -> dict[str, ServiceInfo]:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "-p", self.project_name,
            "-f", str(self.compose_file),
            "up", "-d",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise IntegrationFailureError(f"docker compose up failed: {stderr.decode()}")
        return await self._discover_services()

    async def wait_for_healthy(self, services: list[str], timeout: int = 120) -> dict[str, bool]:
        """Poll docker compose ps --format json until all healthy or timeout."""
        deadline = asyncio.get_event_loop().time() + timeout
        results = {s: False for s in services}

        while asyncio.get_event_loop().time() < deadline:
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose",
                "-p", self.project_name,
                "-f", str(self.compose_file),
                "ps", "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            # Parse JSON, update results
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                info = json.loads(line)
                name = info.get("Service", "")
                health = info.get("Health", "")
                if name in results and health == "healthy":
                    results[name] = True

            if all(results.values()):
                return results

            await asyncio.sleep(5)  # NOT time.sleep(5)

        return results
```

---

## 9. Recommended Run 4 Docker Topology

### 9.1 Network Architecture

```
                         HOST (Port 80)
                              |
                    ┌─────────┴──────────┐
                    │     FRONTEND NET    │
                    │                     │
                    │  ┌──────────────┐   │
                    │  │   TRAEFIK    │   │
                    │  │  (gateway)   │   │
                    │  └──┬───┬───┬───┘   │
                    │     │   │   │       │
                    │  ┌──┴─┐ │ ┌─┴──┐   │
                    │  │arch│ │ │c-e │   │
                    │  │itct│ │ │ngin│   │
                    │  └──┬─┘ │ └─┬──┘   │
                    │     │   │   │       │
                    │  ┌──┴─┐ │ ┌─┴──┐   │
                    │  │code│ │ │auth│   │
                    │  │base│ │ │svc │   │
                    │  └──┬─┘ │ └─┬──┘   │
                    └─────┼───┼───┼──────┘
                          │   │   │
                    ┌─────┼───┼───┼──────┐
                    │     │   │   │       │
                    │  BACKEND NET        │
                    │  (internal: true)   │
                    │                     │
                    │  ┌──────────────┐   │
                    │  │  POSTGRES    │   │
                    │  │  (5432)      │   │
                    │  └──────────────┘   │
                    │  ┌──────────────┐   │
                    │  │    REDIS     │   │
                    │  │  (6379)      │   │
                    │  └──────────────┘   │
                    └────────────────────┘
```

### 9.2 File Organization

```
docker/
  docker-compose.infra.yml        # Tier 0: postgres, redis, migrations
  docker-compose.build1.yml       # Tier 1: architect, contract-engine, codebase-intel
  docker-compose.traefik.yml      # Tier 2: Traefik gateway
  docker-compose.generated.yml    # Tier 3: Generated by ComposeGenerator per-build
  docker-compose.run4.yml         # Run 4: Cross-build wiring overrides
  docker-compose.test.yml         # Test: ephemeral, random ports, volume cleanup
  traefik/
    traefik.yml                   # Static Traefik config
```

### 9.3 Startup Sequence

1. `docker compose -f infra.yml up -d` — Start postgres, redis
2. Wait for postgres `service_healthy`, redis `service_healthy`
3. `docker compose -f infra.yml -f build1.yml up -d` — Start Build 1 services
4. Wait for architect, contract-engine, codebase-intelligence `service_healthy`
5. `docker compose -f infra.yml -f build1.yml -f generated.yml up -d` — Start generated services
6. Wait for generated services `service_healthy`
7. `docker compose -f infra.yml -f build1.yml -f generated.yml -f traefik.yml up -d` — Start gateway
8. Wait for traefik `service_healthy`
9. Run 4 verification begins

**In practice**, use the full merge command — Docker Compose handles the ordering via `depends_on`:

```bash
docker compose \
  -p super-team \
  -f docker/docker-compose.infra.yml \
  -f docker/docker-compose.build1.yml \
  -f docker/docker-compose.generated.yml \
  -f docker/docker-compose.traefik.yml \
  -f docker/docker-compose.run4.yml \
  up -d --wait
```

The `--wait` flag blocks until all services with health checks are healthy.

### 9.4 Critical Configuration Points

| Config | Value | Rationale |
|--------|-------|-----------|
| Project name | `super-team` | Consistent across all commands |
| Backend network | `internal: true` | Databases not accessible from host |
| Docker socket | Read-only (`:ro`) | Traefik needs Docker events but not write access |
| Restart policy | `unless-stopped` | Auto-restart on crash, not on manual stop |
| Log driver | `json-file` with 10M max | Prevent disk fill from verbose services |
| `stop_grace_period` | 10-30s per service | Allow clean shutdown |

---

## 10. Complete Compose File Templates

### 10.1 `docker-compose.infra.yml`

```yaml
# Infrastructure services shared across all builds
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-superteam}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-superteam_secret}
      POSTGRES_DB: ${DB_NAME:-superteam}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    networks:
      - backend
    restart: unless-stopped
    shm_size: "256mb"
    deploy:
      resources:
        limits:
          memory: 512M

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M

volumes:
  pgdata:
    name: super-team-pgdata

networks:
  backend:
    name: super-team-backend
    driver: bridge
  frontend:
    name: super-team-frontend
    driver: bridge
```

### 10.2 `docker-compose.build1.yml`

```yaml
# Build 1: Architect + Contract Engine + Codebase Intelligence
services:
  architect:
    build:
      context: ./src/architect
      dockerfile: ../../docker/architect/Dockerfile
    environment:
      DATABASE_PATH: /data/architect.db
      CONTRACT_ENGINE_URL: http://contract-engine:8000
      CODEBASE_INTEL_URL: http://codebase-intelligence:8000
      LOG_LEVEL: ${LOG_LEVEL:-info}
    volumes:
      - architect-data:/data
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - frontend
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  contract-engine:
    build:
      context: ./src/contract_engine
      dockerfile: ../../docker/contract_engine/Dockerfile
    environment:
      DATABASE_PATH: /data/contracts.db
      LOG_LEVEL: ${LOG_LEVEL:-info}
    volumes:
      - contract-data:/data
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - frontend
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  codebase-intelligence:
    build:
      context: ./src/codebase_intelligence
      dockerfile: ../../docker/codebase_intelligence/Dockerfile
    environment:
      DATABASE_PATH: /data/symbols.db
      CHROMA_PATH: /data/chroma
      GRAPH_PATH: /data/graph.json
      CONTRACT_ENGINE_URL: http://contract-engine:8000
      LOG_LEVEL: ${LOG_LEVEL:-info}
    volumes:
      - intel-data:/data
      - chroma-data:/data/chroma
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\""]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 60s
    networks:
      - frontend
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G

volumes:
  architect-data:
    name: super-team-architect-data
  contract-data:
    name: super-team-contract-data
  intel-data:
    name: super-team-intel-data
  chroma-data:
    name: super-team-chroma-data
```

### 10.3 `docker-compose.traefik.yml`

```yaml
# API Gateway
services:
  traefik:
    image: traefik:v3.6
    command:
      - "--api.dashboard=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedByDefault=false"
      - "--providers.docker.network=super-team-frontend"
      - "--entrypoints.web.address=:80"
      - "--ping=true"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      architect:
        condition: service_healthy
      contract-engine:
        condition: service_healthy
      codebase-intelligence:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    networks:
      - frontend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M
```

### 10.4 `docker-compose.test.yml`

```yaml
# Test overrides — ephemeral, random ports, no persistence
services:
  postgres:
    ports:
      - "5432"       # Random host port
    volumes:
      - pgdata-test:/var/lib/postgresql/data

  architect:
    ports:
      - "8001"       # Random host port
    volumes:
      - architect-data-test:/data

  contract-engine:
    ports:
      - "8002"       # Random host port
    volumes:
      - contract-data-test:/data

  codebase-intelligence:
    ports:
      - "8003"       # Random host port
    volumes:
      - intel-data-test:/data
      - chroma-data-test:/data/chroma

  traefik:
    ports:
      - "80"         # Random host port
      - "8080"       # Random host port

volumes:
  pgdata-test:
  architect-data-test:
  contract-data-test:
  intel-data-test:
  chroma-data-test:
```

### 10.5 `docker-compose.run4.yml` (Cross-Build Wiring)

```yaml
# Run 4 overrides: cross-build environment variables, debug logging
services:
  architect:
    environment:
      LOG_LEVEL: debug
      CONTRACT_ENGINE_URL: http://contract-engine:8000
      CODEBASE_INTEL_URL: http://codebase-intelligence:8000
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.architect.rule=PathPrefix(`/api/architect`)"
      - "traefik.http.services.architect.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.architect-strip.stripprefix.prefixes=/api/architect"
      - "traefik.http.routers.architect.middlewares=architect-strip"

  contract-engine:
    environment:
      LOG_LEVEL: debug
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.contracts.rule=PathPrefix(`/api/contracts`)"
      - "traefik.http.services.contracts.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.contracts-strip.stripprefix.prefixes=/api/contracts"
      - "traefik.http.routers.contracts.middlewares=contracts-strip"

  codebase-intelligence:
    environment:
      LOG_LEVEL: debug
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.codebase.rule=PathPrefix(`/api/codebase`)"
      - "traefik.http.services.codebase.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.codebase-strip.stripprefix.prefixes=/api/codebase"
      - "traefik.http.routers.codebase.middlewares=codebase-strip"
```

---

## Appendix A: Quick Reference Commands

```bash
# Start full stack
docker compose -p super-team \
  -f docker/docker-compose.infra.yml \
  -f docker/docker-compose.build1.yml \
  -f docker/docker-compose.traefik.yml \
  up -d --wait

# Check all service health
docker compose -p super-team ps

# View logs for specific service
docker compose -p super-team logs -f architect --tail=50

# Execute command in container
docker compose -p super-team exec postgres psql -U superteam -d superteam -c "SELECT 1"

# Get mapped port
docker compose -p super-team port architect 8000

# Stop and cleanup (preserve volumes)
docker compose -p super-team down

# Stop and cleanup (remove volumes too)
docker compose -p super-team down -v --remove-orphans

# Rebuild single service
docker compose -p super-team up -d --build architect

# Scale a service (for load testing)
docker compose -p super-team up -d --scale auth-service=3
```

## Appendix B: Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Service can't resolve hostname | Services on different networks | Add shared network to both services |
| `database is locked` | Multiple writers to SQLite | Use `:ro` mount for consumers, or switch to Postgres |
| Health check fails immediately | `start_period` too short | Increase `start_period` (especially for ChromaDB: 60s) |
| Port conflict on host | Fixed port mapping | Use random ports (just specify container port, e.g., `"8000"`) |
| `traefik healthcheck --ping` fails | `--ping=true` not in command | Add `--ping=true` to Traefik command |
| Container restarts in loop | OOM killed | Increase `deploy.resources.limits.memory` |
| `docker compose` not found | Docker Compose v1 installed | Install Docker Compose v2 (comes with Docker Desktop) |
| ENV var not interpolated | Missing `$$` for shell vars | Use `$${VAR}` inside health check commands |
