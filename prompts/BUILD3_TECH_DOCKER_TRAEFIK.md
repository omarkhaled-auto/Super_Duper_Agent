# Build 3 Technology Research: Docker Compose v2 + Traefik v3 + Service Orchestration

> Research Date: 2026-02-14
> Sources: Docker official docs, Traefik v3.6 official docs, Context7

---

## 1. Docker Compose v2 — Complete Reference

### 1.1 `depends_on` with Health Check Conditions

Docker Compose v2 supports three dependency conditions:

| Condition | Description |
|-----------|-------------|
| `service_started` | Wait until the service container is started (default) |
| `service_healthy` | Wait until the service passes its healthcheck |
| `service_completed_successfully` | Wait until the service exits with code 0 |

**Source**: https://docs.docker.com/compose/how-tos/startup-order/

```yaml
services:
  web:
    build: .
    depends_on:
      db:
        condition: service_healthy
        restart: true          # restart web if db restarts
      redis:
        condition: service_started
      migrations:
        condition: service_completed_successfully
  redis:
    image: redis:7-alpine
  db:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
  migrations:
    image: myapp-migrations
    depends_on:
      db:
        condition: service_healthy
```

Key behaviors:
- Compose creates services in dependency order (`db` and `redis` before `web`)
- Compose removes services in reverse dependency order (`web` before `db` and `redis`)
- `restart: true` on `depends_on` ensures dependent restarts when dependency restarts

### 1.2 Healthcheck Configuration

**Source**: https://docs.docker.com/reference/compose-file/services/#healthcheck

```yaml
healthcheck:
  test: ["CMD-SHELL", "command"]  # or ["CMD", "executable", "arg1"]
  interval: 30s        # time between checks (default: 30s)
  timeout: 30s         # max time for a single check (default: 30s)
  retries: 3           # consecutive failures to be unhealthy (default: 3)
  start_period: 0s     # grace period before counting failures (default: 0s)
  start_interval: 5s   # time between checks during start_period (default: 5s)
```

**Health check commands by service type**:

```yaml
# PostgreSQL
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 30s

# MySQL / MariaDB
healthcheck:
  test: ["CMD-SHELL", "mysqladmin ping -h localhost -u root -p$${MYSQL_ROOT_PASSWORD}"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 30s

# Redis
healthcheck:
  test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 10s

# MongoDB
healthcheck:
  test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 20s

# Web API (curl)
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 30s

# Web API (wget — for alpine images without curl)
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 30s

# RabbitMQ
healthcheck:
  test: ["CMD-SHELL", "rabbitmq-diagnostics check_port_connectivity"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 30s

# Traefik
healthcheck:
  test: ["CMD-SHELL", "traefik healthcheck --ping"]
  interval: 10s
  timeout: 5s
  retries: 3

# Disable inherited healthcheck
healthcheck:
  disable: true
```

### 1.3 Named Volumes

**Source**: https://docs.docker.com/reference/compose-file/volumes/

```yaml
services:
  db:
    image: postgres:18
    volumes:
      - pgdata:/var/lib/postgresql/data        # named volume
      - ./init.sql:/docker-entrypoint-initdb.d/ # bind mount
      - type: volume                             # long syntax
        source: pgdata
        target: /var/lib/postgresql/data
        volume:
          nocopy: true

volumes:
  pgdata:                          # default driver (local)
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/on/host

  shared-data:
    name: my_shared_data           # custom volume name
    external: false                # created by compose (default)

  existing-volume:
    external: true                 # must pre-exist, not managed by compose
    name: pre_existing_volume_name
```

### 1.4 Bridge Network Configuration (Custom Networks)

**Source**: https://docs.docker.com/compose/how-tos/networking/

By default, Compose creates a single bridge network named `{project}_default`. All containers join it and are discoverable by service name via DNS.

```yaml
services:
  proxy:
    build: ./proxy
    networks:
      - frontend
  app:
    build: ./app
    networks:
      - frontend
      - backend
  db:
    image: postgres:18
    networks:
      - backend

networks:
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.host_binding_ipv4: "127.0.0.1"
  backend:
    driver: bridge
    internal: true              # no external access

  # Custom name
  proxy-net:
    name: traefik_proxy_network
    driver: bridge

  # External (pre-existing)
  shared:
    name: my-shared-network
    external: true
```

**DNS resolution between containers**: Containers on the same network can reach each other by service name. Example: service `app` can connect to `db:5432` directly.

### 1.5 Environment Variable Handling

**Source**: https://docs.docker.com/reference/compose-file/services/#environment

```yaml
services:
  app:
    image: myapp

    # Inline key-value pairs
    environment:
      NODE_ENV: production
      DATABASE_URL: "postgres://user:pass@db:5432/mydb"
      API_KEY: ${API_KEY}                 # from host environment
      DEBUG: ${DEBUG:-false}              # with default

    # From env file(s)
    env_file:
      - .env                              # always loaded
      - path: .env.local                  # optional
        required: false
      - path: .env.${ENVIRONMENT}.local   # variable interpolation
        required: false

    # env_file format:
    # KEY=value
    # KEY="value with spaces"
    # KEY='literal $dollar'
    # # comment lines
    # empty lines ignored
```

### 1.6 Multi-Stage Docker Builds

**Source**: https://docs.docker.com/reference/compose-file/services/#build

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production              # multi-stage target
      args:
        NODE_VERSION: "20"
        BUILD_DATE: ${BUILD_DATE}
      cache_from:
        - myregistry/myapp:cache
      platforms:
        - linux/amd64
        - linux/arm64
    image: myapp:latest               # tag the built image
```

Example Dockerfile with multi-stage build:

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "dist/main.js"]
```

### 1.7 Resource Limits (Memory, CPU)

**Source**: https://docs.docker.com/reference/compose-file/deploy/#resources

```yaml
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          cpus: '0.50'          # max 50% of one CPU core
          memory: 512M          # max 512 MB RAM
          pids: 100             # max 100 processes
        reservations:
          cpus: '0.25'          # guaranteed 25% CPU
          memory: 128M          # guaranteed 128 MB RAM
          devices:
            - capabilities: ["gpu"]
              count: 1
```

### 1.8 Restart Policies

**Source**: https://docs.docker.com/reference/compose-file/services/#restart

```yaml
services:
  # Simple restart policy (service-level)
  app:
    image: myapp
    restart: "no"              # never restart (default)
    restart: always            # always restart
    restart: on-failure        # only on non-zero exit code
    restart: on-failure:5      # max 5 restart attempts
    restart: unless-stopped    # always, unless manually stopped

  # Deploy restart policy (more options)
  app:
    image: myapp
    deploy:
      restart_policy:
        condition: on-failure       # none | on-failure | any (default)
        delay: 5s                   # wait between restart attempts
        max_attempts: 3             # max failed attempts
        window: 120s                # time window to evaluate success
```

### 1.9 Port Mapping Patterns

```yaml
services:
  app:
    ports:
      # Short syntax
      - "3000:3000"                  # HOST:CONTAINER
      - "8080:80"                    # map host 8080 to container 80
      - "127.0.0.1:3000:3000"       # bind to localhost only
      - "3000"                       # expose container port, random host port
      - "3000-3005:3000-3005"        # port range

      # Long syntax
      - target: 80                   # container port
        published: "8080"            # host port
        protocol: tcp               # tcp or udp
        host_ip: 127.0.0.1          # bind IP
        mode: host                   # host or ingress (swarm)
```

---

## 2. Traefik v3 — Complete Reference

### 2.1 Docker Provider (Automatic Service Discovery)

**Source**: https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/

Traefik automatically discovers Docker containers via labels on the Docker socket.

**Configuration Options**:

| Option | Default | Description |
|--------|---------|-------------|
| `providers.docker.endpoint` | `unix:///var/run/docker.sock` | Docker API endpoint |
| `providers.docker.exposedByDefault` | `true` | Auto-expose all containers |
| `providers.docker.network` | `""` | Default Docker network for connections |
| `providers.docker.defaultRule` | `` Host(`{{ normalize .Name }}`) `` | Default routing rule |
| `providers.docker.watch` | `true` | Watch for Docker events |
| `providers.docker.constraints` | `""` | Expression to filter containers |
| `providers.docker.allowEmptyServices` | `false` | Create LBs even for unhealthy containers |

**Enabling the Docker provider**:

```yaml
# traefik.yml (static configuration)
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false       # require explicit traefik.enable=true
    network: proxy                # default network for all containers
    watch: true
```

Or via CLI flags:

```bash
--providers.docker=true
--providers.docker.exposedByDefault=false
--providers.docker.network=proxy
```

### 2.2 Routing Rules

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/http/routing/rules-and-priority/

```yaml
# Docker labels format
labels:
  # Host-based routing
  - "traefik.http.routers.myapp.rule=Host(`api.example.com`)"

  # Path-based routing
  - "traefik.http.routers.myapp.rule=PathPrefix(`/api`)"

  # Combined rules
  - "traefik.http.routers.myapp.rule=Host(`example.com`) && PathPrefix(`/api`)"

  # Host with regex (v3 syntax)
  - "traefik.http.routers.myapp.rule=HostRegexp(`[a-z]+\\.example\\.com`)"

  # Method matching
  - "traefik.http.routers.myapp.rule=Host(`example.com`) && Method(`GET`, `POST`)"

  # Header matching
  - "traefik.http.routers.myapp.rule=Host(`example.com`) && HeadersRegexp(`X-Custom`, `value.*`)"

  # Query parameter matching
  - "traefik.http.routers.myapp.rule=Host(`example.com`) && Query(`token`, `{value:.+}`)"
```

**Available rule matchers** (Traefik v3):
- `Host(domain)` — match by hostname
- `HostRegexp(regexp)` — match by hostname regex
- `PathPrefix(path)` — match by URL path prefix
- `Path(path)` — match exact URL path
- `Method(methods...)` — match by HTTP method
- `Headers(key, value)` — match by header
- `HeadersRegexp(key, regexp)` — match by header regex
- `Query(key, value)` — match by query parameter
- `ClientIP(range)` — match by client IP/CIDR

### 2.3 Load Balancing Configuration

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/#services

```yaml
labels:
  # Specify backend port
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"

  # Specify backend scheme (default: http)
  - "traefik.http.services.myapp.loadbalancer.server.scheme=http"

  # Pass host header to backend
  - "traefik.http.services.myapp.loadbalancer.passhostheader=true"

  # Sticky sessions
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie=true"
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie.name=my_sticky_cookie"
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie.secure=true"
  - "traefik.http.services.myapp.loadbalancer.sticky.cookie.httponly=true"

  # Response forwarding
  - "traefik.http.services.myapp.loadbalancer.responseforwarding.flushinterval=100ms"
```

**Traefik-level health checking** (load balancer health, separate from Docker healthcheck):

```yaml
labels:
  - "traefik.http.services.myapp.loadbalancer.healthcheck.path=/health"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.interval=10s"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.timeout=5s"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.scheme=http"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.port=8080"
  - "traefik.http.services.myapp.loadbalancer.healthcheck.followredirects=true"
```

### 2.4 Middleware — Complete Docker Labels Reference

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/overview/

**Available HTTP Middlewares**:

| Middleware | Purpose | Area |
|-----------|---------|------|
| AddPrefix | Adds a path prefix | Path Modifier |
| BasicAuth | Basic Authentication | Security |
| Buffering | Buffers request/response | Request Lifecycle |
| Chain | Combines middlewares | Misc |
| CircuitBreaker | Prevents calling unhealthy services | Request Lifecycle |
| Compress | Compresses response | Content Modifier |
| DigestAuth | Digest Authentication | Security |
| Errors | Custom error pages | Request Lifecycle |
| ForwardAuth | Delegates Authentication | Security |
| GrpcWeb | gRPC-Web to HTTP/2 gRPC | Request |
| Headers | Adds/updates headers | Security |
| IPAllowList | Limits client IPs | Security |
| InFlightReq | Limits concurrent connections | Security |
| PassTLSClientCert | Client certs in header | Security |
| RateLimit | Limits call frequency | Security |
| RedirectScheme | Redirects by scheme | Request Lifecycle |
| RedirectRegex | Redirects by regex | Request Lifecycle |
| ReplacePath | Changes request path | Path Modifier |
| ReplacePathRegex | Changes path by regex | Path Modifier |
| Retry | Auto-retry on error | Request Lifecycle |
| StripPrefix | Removes path prefix | Path Modifier |
| StripPrefixRegex | Removes path prefix by regex | Path Modifier |

#### 2.4.1 StripPrefix Middleware

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/stripprefix/

```yaml
labels:
  # Declare the middleware
  - "traefik.http.middlewares.api-strip.stripprefix.prefixes=/api/v1"
  # Reference it on the router
  - "traefik.http.routers.backend.middlewares=api-strip"
```

Multiple prefixes:
```yaml
labels:
  - "traefik.http.middlewares.multi-strip.stripprefix.prefixes=/api,/v1"
```

#### 2.4.2 RateLimit Middleware

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/ratelimit/

Based on token bucket algorithm: `average` / `period` = rate, `burst` = bucket size.

```yaml
labels:
  # 100 requests/second, burst of 200
  - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.period=1s"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.burst=200"

  # Rate limit per source IP
  - "traefik.http.middlewares.api-ratelimit.ratelimit.sourcecriterion.requestheadername=X-Forwarded-For"

  # Apply to router
  - "traefik.http.routers.backend.middlewares=api-ratelimit"
```

| Option | Default | Description |
|--------|---------|-------------|
| `average` | 0 | Requests per period (0 = no limit) |
| `period` | 1s | Time period for average |
| `burst` | 1 | Max simultaneous requests |
| `sourceCriterion.requestHost` | false | Group by request host |
| `sourceCriterion.requestHeaderName` | "" | Group by header value |
| `sourceCriterion.ipStrategy.depth` | 0 | X-Forwarded-For depth |

#### 2.4.3 CORS Headers Middleware

**Source**: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/headers/#cors-headers

```yaml
labels:
  # CORS configuration
  - "traefik.http.middlewares.cors.headers.accesscontrolallowmethods=GET,OPTIONS,PUT,POST,DELETE"
  - "traefik.http.middlewares.cors.headers.accesscontrolallowheaders=Content-Type,Authorization,X-Requested-With"
  - "traefik.http.middlewares.cors.headers.accesscontrolalloworiginlist=http://localhost:4200,https://app.example.com"
  - "traefik.http.middlewares.cors.headers.accesscontrolmaxage=3600"
  - "traefik.http.middlewares.cors.headers.accesscontrolallowcredentials=true"
  - "traefik.http.middlewares.cors.headers.accesscontrolexposeheaders=X-Custom-Header"
  - "traefik.http.middlewares.cors.headers.addvaryheader=true"

  # Apply to router
  - "traefik.http.routers.backend.middlewares=cors"
```

| Option | Default | Description |
|--------|---------|-------------|
| `accessControlAllowCredentials` | false | Allow credentials |
| `accessControlAllowHeaders` | [] | Allowed request headers |
| `accessControlAllowMethods` | [] | Allowed HTTP methods |
| `accessControlAllowOriginList` | [] | Allowed origins |
| `accessControlAllowOriginListRegex` | [] | Allowed origins (regex) |
| `accessControlExposeHeaders` | [] | Headers exposed to browser |
| `accessControlMaxAge` | 0 | Preflight cache (seconds) |
| `addVaryHeader` | false | Add Vary: Origin header |

#### 2.4.4 Custom Headers Middleware

```yaml
labels:
  # Custom request headers
  - "traefik.http.middlewares.security-headers.headers.customrequestheaders.X-Forwarded-Proto=https"

  # Custom response headers
  - "traefik.http.middlewares.security-headers.headers.customresponseheaders.X-Frame-Options=DENY"
  - "traefik.http.middlewares.security-headers.headers.customresponseheaders.X-Content-Type-Options=nosniff"

  # Remove a header (set empty value)
  - "traefik.http.middlewares.security-headers.headers.customresponseheaders.Server="

  # Security headers shortcuts
  - "traefik.http.middlewares.security-headers.headers.framedeny=true"
  - "traefik.http.middlewares.security-headers.headers.contenttypenosniff=true"
  - "traefik.http.middlewares.security-headers.headers.browserxssfilter=true"
  - "traefik.http.middlewares.security-headers.headers.contentsecuritypolicy=default-src 'self'"
  - "traefik.http.middlewares.security-headers.headers.referrerpolicy=strict-origin-when-cross-origin"
  - "traefik.http.middlewares.security-headers.headers.permissionspolicy=camera=(), microphone=()"

  # HSTS
  - "traefik.http.middlewares.security-headers.headers.stsseconds=31536000"
  - "traefik.http.middlewares.security-headers.headers.stsincludesubdomains=true"
  - "traefik.http.middlewares.security-headers.headers.stspreload=true"
  - "traefik.http.middlewares.security-headers.headers.forcestsheader=true"
```

#### 2.4.5 ForwardAuth Middleware

```yaml
labels:
  - "traefik.http.middlewares.auth-forward.forwardauth.address=http://auth-service:4181"
  - "traefik.http.middlewares.auth-forward.forwardauth.trustforwardheader=true"
  - "traefik.http.middlewares.auth-forward.forwardauth.authresponseheaders=X-User-Id,X-User-Email"
```

#### 2.4.6 Middleware Chains

```yaml
labels:
  # Declare individual middlewares
  - "traefik.http.middlewares.api-strip.stripprefix.prefixes=/api"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.api-cors.headers.accesscontrolalloworiginlist=*"

  # Chain them on the router (comma-separated)
  - "traefik.http.routers.backend.middlewares=api-strip,api-ratelimit,api-cors"
```

### 2.5 SSL/TLS Configuration

```yaml
# traefik.yml — static configuration
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme.json
      httpChallenge:
        entryPoint: web
      # OR
      tlsChallenge: {}
      # OR
      dnsChallenge:
        provider: cloudflare
```

Docker labels for TLS:

```yaml
labels:
  - "traefik.http.routers.myapp.tls=true"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  - "traefik.http.routers.myapp.tls.domains[0].main=example.com"
  - "traefik.http.routers.myapp.tls.domains[0].sans=*.example.com"
```

**Development (self-signed)**:

```yaml
# traefik.yml
tls:
  stores:
    default:
      defaultGeneratedCert:
        resolver: letsencrypt
        domain:
          main: "localhost"
```

### 2.6 Dashboard Configuration

**Source**: https://doc.traefik.io/traefik/getting-started/quick-start/

```yaml
# traefik.yml — development only
api:
  insecure: true        # exposes dashboard on :8080 without auth
  dashboard: true       # enable dashboard (default when api is enabled)

# Production — use secure access
api:
  dashboard: true
  insecure: false
```

For production, use a router with BasicAuth:

```yaml
labels:
  - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))"
  - "traefik.http.routers.dashboard.service=api@internal"
  - "traefik.http.routers.dashboard.tls=true"
  - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
  - "traefik.http.routers.dashboard.middlewares=dashboard-auth"
  - "traefik.http.middlewares.dashboard-auth.basicauth.users=admin:$$apr1$$..."
```

### 2.7 Entry Points Configuration

```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
  custom:
    address: ":8443"
  metrics:
    address: ":9090"
```

Docker labels to assign entry points:

```yaml
labels:
  - "traefik.http.routers.myapp.entrypoints=web,websecure"
```

### 2.8 Docker Compose Integration — Complete Traefik Service

**Source**: https://doc.traefik.io/traefik/getting-started/quick-start/

```yaml
# docker-compose.yml — Traefik service definition
services:
  traefik:
    image: traefik:v3.6
    container_name: traefik
    restart: unless-stopped
    command:
      # API & Dashboard
      - "--api.insecure=true"
      - "--api.dashboard=true"
      # Docker provider
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=proxy"
      # Entry points
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      # HTTP -> HTTPS redirect
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      # Let's Encrypt
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/etc/traefik/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      # Logging
      - "--log.level=INFO"
      - "--accesslog=true"
      # Ping (for healthcheck)
      - "--ping=true"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"    # Dashboard (remove in production)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certs:/etc/traefik
    networks:
      - proxy
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

networks:
  proxy:
    name: traefik_proxy
    driver: bridge

volumes:
  traefik-certs:
```

### 2.9 Specific Provider Options

```yaml
labels:
  # Enable/disable container discovery
  - "traefik.enable=true"

  # Specify which Docker network Traefik should use for this container
  - "traefik.docker.network=proxy"

  # Allow non-running containers (returns 503 instead of 404)
  - "traefik.docker.allownonrunning=true"
```

---

## 3. Complete Multi-Service Docker Compose Example

This example demonstrates all features together — a full-stack app with Traefik gateway:

```yaml
# docker-compose.yml
services:
  # ========== API GATEWAY ==========
  traefik:
    image: traefik:v3.6
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=proxy"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--ping=true"
      - "--log.level=INFO"
      - "--accesslog=true"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - proxy
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 256M

  # ========== DATABASE ==========
  postgres:
    image: postgres:16-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-appuser}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
      POSTGRES_DB: ${DB_NAME:-appdb}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  # ========== CACHE ==========
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          memory: 256M

  # ========== DATABASE MIGRATIONS ==========
  migrations:
    build:
      context: ./backend
      target: migrations
    container_name: migrations
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: "postgres://${DB_USER:-appuser}:${DB_PASSWORD:-secret}@postgres:5432/${DB_NAME:-appdb}"
    networks:
      - backend
    restart: "no"  # run once and exit

  # ========== BACKEND API ==========
  backend:
    build:
      context: ./backend
      target: production
    container_name: backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      DATABASE_URL: "postgres://${DB_USER:-appuser}:${DB_PASSWORD:-secret}@postgres:5432/${DB_NAME:-appdb}"
      REDIS_URL: "redis://redis:6379"
      PORT: "3000"
    env_file:
      - .env
      - path: .env.local
        required: false
    networks:
      - proxy
      - backend
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    labels:
      # Enable Traefik
      - "traefik.enable=true"
      - "traefik.docker.network=traefik_proxy"
      # Router: API routes
      - "traefik.http.routers.backend.rule=Host(`api.localhost`) || (Host(`localhost`) && PathPrefix(`/api`))"
      - "traefik.http.routers.backend.entrypoints=web"
      # Service port
      - "traefik.http.services.backend.loadbalancer.server.port=3000"
      # Middleware: strip /api prefix
      - "traefik.http.middlewares.api-strip.stripprefix.prefixes=/api"
      # Middleware: rate limiting (100 req/s, burst 200)
      - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
      - "traefik.http.middlewares.api-ratelimit.ratelimit.burst=200"
      # Middleware: CORS
      - "traefik.http.middlewares.api-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS"
      - "traefik.http.middlewares.api-cors.headers.accesscontrolallowheaders=Content-Type,Authorization"
      - "traefik.http.middlewares.api-cors.headers.accesscontrolalloworiginlist=http://localhost:4200,http://localhost:3000"
      - "traefik.http.middlewares.api-cors.headers.accesscontrolmaxage=3600"
      - "traefik.http.middlewares.api-cors.headers.addvaryheader=true"
      # Chain middlewares
      - "traefik.http.routers.backend.middlewares=api-strip,api-ratelimit,api-cors"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

  # ========== FRONTEND ==========
  frontend:
    build:
      context: ./frontend
      target: production
    container_name: frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - proxy
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 15s
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik_proxy"
      - "traefik.http.routers.frontend.rule=Host(`localhost`)"
      - "traefik.http.routers.frontend.entrypoints=web"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
      - "traefik.http.routers.frontend.priority=1"
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 256M

# ========== NETWORKS ==========
networks:
  proxy:
    name: traefik_proxy
    driver: bridge
  backend:
    name: app_backend
    driver: bridge
    internal: true    # no external access

# ========== VOLUMES ==========
volumes:
  pgdata:
    name: app_pgdata
  redis-data:
    name: app_redis_data
```

---

## 4. Service Orchestration Patterns

### 4.1 Init Containers / Migration Services Pattern

Use `service_completed_successfully` for one-shot initialization:

```yaml
services:
  # Run once, exit with 0 on success
  db-migrate:
    image: myapp:latest
    command: ["npm", "run", "db:migrate"]
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"
    networks:
      - backend

  db-seed:
    image: myapp:latest
    command: ["npm", "run", "db:seed"]
    depends_on:
      db-migrate:
        condition: service_completed_successfully
    restart: "no"
    networks:
      - backend

  # Main app waits for both
  app:
    image: myapp:latest
    depends_on:
      db-seed:
        condition: service_completed_successfully
    restart: unless-stopped
```

### 4.2 Service Dependency Ordering

Full dependency chain example:

```
postgres (healthcheck: pg_isready)
    |
    v
redis (healthcheck: redis-cli ping)
    |
    v
migrations (service_completed_successfully)
    |
    v
backend (healthcheck: curl /health)
    |
    v
frontend (healthcheck: curl /)
    |
    v
traefik (routes traffic to all)
```

### 4.3 Graceful Shutdown (SIGTERM Handling)

```yaml
services:
  app:
    image: myapp
    stop_signal: SIGTERM         # default, sends SIGTERM
    stop_grace_period: 30s       # time to wait before SIGKILL (default: 10s)
```

Python SIGTERM handler:

```python
import signal
import sys

def graceful_shutdown(signum, frame):
    """Handle SIGTERM for graceful shutdown."""
    print("Received SIGTERM, shutting down gracefully...")
    # Close database connections
    # Finish processing current requests
    # Flush logs
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
```

### 4.4 Log Aggregation Patterns

```yaml
services:
  app:
    image: myapp
    logging:
      driver: "json-file"
      options:
        max-size: "10m"        # max log file size
        max-file: "3"          # max number of log files
        tag: "{{.Name}}"       # tag with container name

  # Alternative: syslog driver
  app-syslog:
    image: myapp
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logserver:514"
        tag: "myapp"
```

### 4.5 Container Networking (DNS Resolution)

**Source**: https://docs.docker.com/compose/how-tos/networking/

Key rules:
1. By default, all services join a `{project}_default` network
2. Services are reachable by their **service name** (not container name)
3. Custom networks provide isolation: only services on the same network can communicate
4. Service names resolve via Docker's embedded DNS server
5. Use `CONTAINER_PORT` for inter-service communication, not `HOST_PORT`

```yaml
# Service 'backend' connects to 'postgres' at postgres:5432
# Service 'backend' connects to 'redis' at redis:6379
# External access uses published HOST_PORT
```

### 4.6 Health Check Best Practices Per Service Type

| Service Type | Check Method | Interval | Timeout | Retries | Start Period |
|-------------|--------------|----------|---------|---------|--------------|
| Database (PostgreSQL) | `pg_isready` | 10s | 10s | 5 | 30s |
| Database (MySQL) | `mysqladmin ping` | 10s | 10s | 5 | 30s |
| Cache (Redis) | `redis-cli ping` | 10s | 5s | 3 | 10s |
| Message Broker (RabbitMQ) | `rabbitmq-diagnostics` | 10s | 10s | 5 | 30s |
| Web API | `curl/wget /health` | 15s | 5s | 3 | 30s |
| Static Frontend | `curl/wget /` | 15s | 5s | 3 | 15s |
| API Gateway (Traefik) | `traefik healthcheck --ping` | 10s | 5s | 3 | 5s |
| Worker/Consumer | Custom script | 30s | 10s | 3 | 30s |

---

## 5. Python Patterns for Docker Interaction

### 5.1 subprocess — Docker Compose Control

```python
import subprocess
import shutil
from pathlib import Path
from typing import Optional


def _find_docker_compose() -> str:
    """Find docker compose command (v2 plugin or standalone)."""
    # Try docker compose (v2 plugin)
    result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        return "docker compose"

    # Fallback to docker-compose (standalone)
    if shutil.which("docker-compose"):
        return "docker-compose"

    raise RuntimeError("Docker Compose not found")


def docker_compose_up(
    compose_file: Path,
    project_name: str,
    services: Optional[list[str]] = None,
    build: bool = False,
    detach: bool = True,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    """Start Docker Compose services."""
    cmd_prefix = _find_docker_compose()
    cmd = f"{cmd_prefix} -f {compose_file} -p {project_name} up"

    if build:
        cmd += " --build"
    if detach:
        cmd += " -d"
    if services:
        cmd += " " + " ".join(services)

    return subprocess.run(
        cmd.split(),
        capture_output=True, text=True,
        timeout=timeout,
        cwd=compose_file.parent,
    )


def docker_compose_down(
    compose_file: Path,
    project_name: str,
    volumes: bool = False,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Stop and remove Docker Compose services."""
    cmd_prefix = _find_docker_compose()
    cmd = f"{cmd_prefix} -f {compose_file} -p {project_name} down"

    if volumes:
        cmd += " -v"  # remove named volumes

    return subprocess.run(
        cmd.split(),
        capture_output=True, text=True,
        timeout=timeout,
        cwd=compose_file.parent,
    )


def wait_for_healthy(
    compose_file: Path,
    project_name: str,
    service: str,
    timeout: int = 120,
    poll_interval: int = 5,
) -> bool:
    """Wait for a service to become healthy."""
    import time

    cmd_prefix = _find_docker_compose()
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        result = subprocess.run(
            f"{cmd_prefix} -f {compose_file} -p {project_name} ps --format json {service}".split(),
            capture_output=True, text=True,
            timeout=30,
            cwd=compose_file.parent,
        )
        if result.returncode == 0 and '"healthy"' in result.stdout.lower():
            return True
        time.sleep(poll_interval)

    return False


def get_service_logs(
    compose_file: Path,
    project_name: str,
    service: str,
    tail: int = 100,
) -> str:
    """Get logs for a specific service."""
    cmd_prefix = _find_docker_compose()
    result = subprocess.run(
        f"{cmd_prefix} -f {compose_file} -p {project_name} logs --tail {tail} {service}".split(),
        capture_output=True, text=True,
        timeout=30,
        cwd=compose_file.parent,
    )
    return result.stdout
```

### 5.2 Docker SDK for Python (docker-py)

```python
import docker
from docker.errors import NotFound, APIError


def create_docker_client() -> docker.DockerClient:
    """Create Docker client from environment."""
    return docker.from_env()


def check_container_health(client: docker.DockerClient, container_name: str) -> str:
    """Check container health status."""
    try:
        container = client.containers.get(container_name)
        state = container.attrs.get("State", {})
        health = state.get("Health", {})
        return health.get("Status", "unknown")  # healthy, unhealthy, starting, none
    except NotFound:
        return "not_found"
    except APIError as e:
        return f"error: {e}"


def wait_all_healthy(
    client: docker.DockerClient,
    containers: list[str],
    timeout: int = 120,
    poll_interval: int = 5,
) -> dict[str, bool]:
    """Wait for multiple containers to become healthy."""
    import time

    results = {name: False for name in containers}
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        all_healthy = True
        for name in containers:
            if results[name]:
                continue
            status = check_container_health(client, name)
            if status == "healthy":
                results[name] = True
            else:
                all_healthy = False

        if all_healthy:
            break
        time.sleep(poll_interval)

    return results


def get_container_port(
    client: docker.DockerClient,
    container_name: str,
    internal_port: int,
) -> Optional[int]:
    """Get the mapped host port for a container's internal port."""
    try:
        container = client.containers.get(container_name)
        port_key = f"{internal_port}/tcp"
        bindings = container.ports.get(port_key, [])
        if bindings:
            return int(bindings[0]["HostPort"])
    except (NotFound, KeyError, IndexError, ValueError):
        pass
    return None
```

### 5.3 Async Docker Compose Control

```python
import asyncio
from pathlib import Path


async def async_docker_compose_up(
    compose_file: Path,
    project_name: str,
    timeout: int = 120,
) -> tuple[int, str, str]:
    """Async docker compose up."""
    proc = await asyncio.create_subprocess_exec(
        "docker", "compose",
        "-f", str(compose_file),
        "-p", project_name,
        "up", "-d", "--build",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(compose_file.parent),
    )

    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, stdout.decode(), stderr.decode()


async def async_wait_for_url(
    url: str,
    timeout: int = 120,
    poll_interval: float = 2.0,
) -> bool:
    """Wait for a URL to respond with 200."""
    import aiohttp

    deadline = asyncio.get_event_loop().time() + timeout

    async with aiohttp.ClientSession() as session:
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            await asyncio.sleep(poll_interval)

    return False
```

---

## 6. Version Numbers and Compatibility Notes

| Component | Version | Release Date | Notes |
|-----------|---------|--------------|-------|
| Docker Compose | v2.x (latest: 2.32+) | 2024-2025 | Plugin mode (`docker compose`), not standalone |
| Traefik | v3.6.x | 2025 | Latest v3 stable, Docker provider built-in |
| Docker Engine | 27.x | 2025 | Required for Compose v2 features |
| Compose Spec | 3.x / Compose Spec | 2024+ | No version key needed in modern compose files |

**Key compatibility notes**:
1. Docker Compose v2 is a Docker CLI plugin (use `docker compose`, not `docker-compose`)
2. The `version` key in compose files is **obsolete** — no longer needed
3. `depends_on.condition` requires Compose v2.0+
4. `service_completed_successfully` requires Compose v2.1+
5. `deploy.resources` works in non-Swarm mode with Compose v2
6. Traefik v3 requires Docker socket access (mount `/var/run/docker.sock`)
7. Traefik v3 `ruleSyntax` option is deprecated — use v3 syntax directly
8. `exposedByDefault: false` is recommended for security

---

## 7. Quick Reference — All Docker Label Formats for Traefik

```yaml
# ===== ROUTER =====
traefik.enable=true
traefik.http.routers.<NAME>.rule=Host(`example.com`)
traefik.http.routers.<NAME>.entrypoints=web,websecure
traefik.http.routers.<NAME>.middlewares=mw1,mw2
traefik.http.routers.<NAME>.service=svc-name
traefik.http.routers.<NAME>.tls=true
traefik.http.routers.<NAME>.tls.certresolver=letsencrypt
traefik.http.routers.<NAME>.priority=42

# ===== SERVICE =====
traefik.http.services.<NAME>.loadbalancer.server.port=8080
traefik.http.services.<NAME>.loadbalancer.server.scheme=http
traefik.http.services.<NAME>.loadbalancer.passhostheader=true
traefik.http.services.<NAME>.loadbalancer.healthcheck.path=/health
traefik.http.services.<NAME>.loadbalancer.healthcheck.interval=10s
traefik.http.services.<NAME>.loadbalancer.sticky.cookie=true

# ===== MIDDLEWARE: StripPrefix =====
traefik.http.middlewares.<NAME>.stripprefix.prefixes=/api

# ===== MIDDLEWARE: RateLimit =====
traefik.http.middlewares.<NAME>.ratelimit.average=100
traefik.http.middlewares.<NAME>.ratelimit.period=1s
traefik.http.middlewares.<NAME>.ratelimit.burst=200

# ===== MIDDLEWARE: Headers (CORS) =====
traefik.http.middlewares.<NAME>.headers.accesscontrolallowmethods=GET,POST,OPTIONS
traefik.http.middlewares.<NAME>.headers.accesscontrolallowheaders=Content-Type,Authorization
traefik.http.middlewares.<NAME>.headers.accesscontrolalloworiginlist=http://localhost:3000
traefik.http.middlewares.<NAME>.headers.accesscontrolmaxage=3600
traefik.http.middlewares.<NAME>.headers.addvaryheader=true

# ===== MIDDLEWARE: Headers (Security) =====
traefik.http.middlewares.<NAME>.headers.framedeny=true
traefik.http.middlewares.<NAME>.headers.contenttypenosniff=true
traefik.http.middlewares.<NAME>.headers.browserxssfilter=true
traefik.http.middlewares.<NAME>.headers.stsseconds=31536000
traefik.http.middlewares.<NAME>.headers.stsincludesubdomains=true

# ===== MIDDLEWARE: BasicAuth =====
traefik.http.middlewares.<NAME>.basicauth.users=user:$$apr1$$hash

# ===== MIDDLEWARE: ForwardAuth =====
traefik.http.middlewares.<NAME>.forwardauth.address=http://auth:4181
traefik.http.middlewares.<NAME>.forwardauth.trustforwardheader=true

# ===== MIDDLEWARE: RedirectScheme =====
traefik.http.middlewares.<NAME>.redirectscheme.scheme=https
traefik.http.middlewares.<NAME>.redirectscheme.permanent=true

# ===== MIDDLEWARE: CircuitBreaker =====
traefik.http.middlewares.<NAME>.circuitbreaker.expression=LatencyAtQuantileMS(50.0) > 100

# ===== MIDDLEWARE: Retry =====
traefik.http.middlewares.<NAME>.retry.attempts=4
traefik.http.middlewares.<NAME>.retry.initialinterval=100ms

# ===== MIDDLEWARE: Compress =====
traefik.http.middlewares.<NAME>.compress=true

# ===== PROVIDER OPTIONS =====
traefik.docker.network=proxy
```

---

## Sources

1. Docker Compose — Startup Order: https://docs.docker.com/compose/how-tos/startup-order/
2. Docker Compose — Services Reference: https://docs.docker.com/reference/compose-file/services/
3. Docker Compose — Deploy Specification: https://docs.docker.com/reference/compose-file/deploy/
4. Docker Compose — Networking: https://docs.docker.com/compose/how-tos/networking/
5. Traefik — Quick Start: https://doc.traefik.io/traefik/getting-started/quick-start/
6. Traefik — Docker Provider: https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/
7. Traefik — Docker Routing Labels: https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/
8. Traefik — Middleware Overview: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/overview/
9. Traefik — Headers Middleware: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/headers/
10. Traefik — RateLimit Middleware: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/ratelimit/
11. Traefik — StripPrefix Middleware: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/stripprefix/
12. Docker SDK for Python: https://docker-py.readthedocs.io/en/stable/
