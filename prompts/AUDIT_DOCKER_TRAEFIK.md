# Docker Compose v2 + Traefik v3 Technical Audit

> Reviewer: Docker/Traefik Specialist
> Date: 2026-02-14
> Scope: BUILD3_PRD.md (primary), BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_TECH_DOCKER_TRAEFIK.md

---

## 1. Context7 Research Summary

### Docker Compose v2

Queried `/docker/compose` and `/docker/awesome-compose` for: depends_on conditions, healthcheck syntax, named volumes, network config, environment variables, resource limits, restart policies, port mapping.

**Key confirmed facts:**
- `depends_on` supports 3 conditions: `service_started` (default), `service_healthy`, `service_completed_successfully`
- Healthcheck fields: `test`, `interval`, `timeout`, `retries`, `start_period`, `start_interval` (all confirmed)
- `docker compose` (v2 plugin) is correct; `docker-compose` (v1 standalone) is deprecated
- `version` key in compose files is obsolete in modern Compose
- `deploy.resources` works in non-Swarm mode with Compose v2
- Named volumes, bind mounts, and tmpfs all supported
- Environment variables: `${VAR:-default}` (use default if unset/empty), `${VAR-default}` (use default if unset)

### Traefik v3

Queried `/websites/doc_traefik_io_traefik` for: Docker provider labels, routing rules, middleware, entrypoints, dashboard, healthcheck, static configuration.

**Key confirmed facts:**
- Label format: `traefik.http.routers.<NAME>.rule=Host(\`example.com\`)` (backtick syntax)
- `PathPrefix(\`/path\`)` uses backticks in v3 (same as v2)
- `HostRegexp` in v3 uses pure regex (no `{name:...}` capture groups like v2)
- `exposedByDefault: false` is the recommended security setting
- `--ping=true` must be enabled for `traefik healthcheck --ping` to work
- StripPrefix middleware: `traefik.http.middlewares.<NAME>.stripprefix.prefixes=/path`
- Dashboard: `api.dashboard: true` enables, `api.insecure: false` for production
- Static config accepts both camelCase (`entryPoints`) and lowercase (`entrypoints`) in YAML

---

## 2. Build 3 PRD Findings

### 2.1 Docker Compose v2 Claims

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| `depends_on` with `condition: service_healthy` | Line 25, REQ-015 | CORRECT | Matches Docker Compose v2 spec exactly |
| Healthcheck: test, interval, timeout, retries, start_period | REQ-015 | CORRECT | All fields valid; `start_interval` omitted (optional, fine) |
| PostgreSQL healthcheck: `pg_isready` | REQ-015 | CORRECT | Standard pattern for postgres containers |
| Redis healthcheck: `redis-cli ping` | REQ-015 | CORRECT | Standard pattern for redis containers |
| Named volumes for PostgreSQL | REQ-015 | CORRECT | Standard persistence pattern |
| frontend/backend network separation | REQ-015 | CORRECT | Bridge networks with isolation |
| `docker compose` (v2, no hyphen) | TECH-008 | CORRECT | v1 `docker-compose` is deprecated |
| `docker compose -p {project_name} -f {file} up -d` | REQ-017 | CORRECT | Valid v2 CLI syntax |
| `docker compose ps --format json` | REQ-017 | CORRECT | Valid command, outputs JSON per service |
| `docker compose port {service} {port}` | REQ-017 | CORRECT | Returns `IP:PORT` mapping |
| Subprocess stdout/stderr capture | TECH-009 | CORRECT | Best practice for error diagnostics |
| docker-py 7.x+ with `docker.from_env()` | Line 27 | CORRECT | Standard Python Docker SDK pattern |
| `asyncio.create_subprocess_exec` for compose | REQ-017 | CORRECT | Proper async subprocess pattern |
| postgres:16-alpine image | REQ-015 | CORRECT | Stable LTS version |
| redis:7-alpine image | REQ-015 | CORRECT | Current stable version |

### 2.2 Traefik v3 Claims

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| `traefik:v3.6` image | Line 24, REQ-015 | CORRECT | Current v3 stable release |
| `traefik.enable=true` label | REQ-016 | CORRECT | Standard enable label |
| `traefik.http.routers.{service}.rule=PathPrefix(\`{path}\`)` | REQ-016 | CORRECT | v3 backtick syntax |
| `traefik.http.services.{service}.loadbalancer.server.port={port}` | REQ-016 | CORRECT | Backend port specification |
| `traefik.http.middlewares.{service}-strip.stripprefix.prefixes={path}` | REQ-016 | CORRECT | StripPrefix middleware |
| `traefik.http.routers.{service}.middlewares={service}-strip` | REQ-016 | CORRECT | Middleware reference on router |
| Static config: `providers.docker` + `exposedByDefault: false` | REQ-016 | CORRECT | Recommended security setting |
| Static config: `entrypoints.web` + `address: ":80"` | REQ-016 | CORRECT | Both camelCase and lowercase accepted |
| Healthcheck: `traefik healthcheck --ping` | REQ-015 | PARTIAL | See Issue #1 below |
| Dashboard disabled by default | SEC-003 | CORRECT | `--api.dashboard=false` |
| Docker socket read-only mount | SEC-004 | CORRECT | `:/var/run/docker.sock:ro` |
| Backtick syntax for PathPrefix in Python | TECH-010 | CORRECT | Backticks work directly in Python strings |
| No v2-only syntax used | All | CORRECT | No `lbswarm`, no `{name:...}` HostRegexp, no `ruleSyntax` |
| Ports 80 and 8080 for Traefik | REQ-015 | CORRECT | 80=web traffic, 8080=dashboard/API |

---

## 3. Issues Found

### ISSUE-1: Traefik Healthcheck Requires `--ping=true` [MEDIUM]

**Location:** REQ-015 (Build 3 PRD Line 164)

**Problem:** REQ-015 specifies Traefik healthcheck as `traefik healthcheck --ping`, but does not mandate that `--ping=true` be set in the Traefik service configuration (command flags or static config). Without `--ping=true`, the `/ping` endpoint is not enabled, and the healthcheck command will fail with an error.

**Evidence:** The tech research file (Section 2.8, Line 778) correctly includes `"--ping=true"` in the Traefik command list. But the PRD requirement text only says "health check using `traefik healthcheck --ping`" without mentioning the prerequisite.

**Fix:** Add to REQ-015 or create a new TECH requirement:

```
Traefik service must include `--ping=true` in its command configuration
to enable the ping endpoint required by the healthcheck command.
```

Or amend REQ-015 to say:
```
health check using `traefik healthcheck --ping` (requires --ping=true in Traefik command)
```

**Impact:** Without this fix, the ComposeGenerator could produce a Traefik service where the healthcheck always fails, causing `depends_on: { traefik: { condition: service_healthy } }` to block indefinitely.

---

### ISSUE-2: `docker compose ps --format json` Output Variability [LOW]

**Location:** REQ-017 (Build 3 PRD Line 168)

**Problem:** REQ-017 says `wait_for_healthy` polls `docker compose ps --format json`. Different Docker Compose versions output JSON differently:
- Older v2 versions: one JSON object per line (NDJSON/JSONL)
- Newer v2 versions: can output a JSON array
- The `Health` field name may vary between versions

**Fix:** Not strictly a PRD issue, but the implementation should handle both formats. Consider adding a note to REQ-017 or TECH requirements:

```
Docker Compose JSON output parsing must handle both single-object-per-line (JSONL)
and JSON array formats for compatibility across Compose v2 versions.
```

**Impact:** Low. Most current Compose v2 versions use consistent output.

---

### ISSUE-3: Tech Research Uses `aiohttp` but PRD Specifies `httpx` [LOW]

**Location:** BUILD3_TECH_DOCKER_TRAEFIK.md Section 5.3 (Line 1417)

**Problem:** The tech research async example uses `aiohttp.ClientSession` for async health checking, but the Build 3 PRD technology stack (Line 19) specifies `httpx 0.28.x+` as the async HTTP client. The PRD requirements (TECH-014, TECH-017) correctly mandate `httpx.AsyncClient`.

**Fix:** Update the tech research file Section 5.3 to use `httpx.AsyncClient` instead of `aiohttp`:

```python
async with httpx.AsyncClient(timeout=5.0) as client:
    response = await client.get(url)
    if response.status_code == 200:
        return True
```

**Impact:** Low. The tech research is a reference document, not executable code. The PRD requirements correctly specify httpx.

---

### ISSUE-4: TECH-010 Backtick Note Slightly Misleading [INFO]

**Location:** TECH-010 (Build 3 PRD Line 183)

**Problem:** TECH-010 says "In Python, use string concatenation or raw strings to produce backtick characters." This implies backticks need special handling in Python, when they actually don't -- backticks are regular characters in Python strings with no special meaning.

A simple f-string works:
```python
f"traefik.http.routers.{service}.rule=PathPrefix(`{path_prefix}`)"
```

**Fix:** Optional. Could clarify to:
```
Backtick characters have no special meaning in Python strings and can be used directly
in f-strings, regular strings, or raw strings.
```

**Impact:** None. The note is technically not wrong, just potentially confusing.

---

## 4. Build 1 PRD Docker Findings

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| 3 services: architect (8001), contract-engine (8002), codebase-intel (8003) | INT-002 | CORRECT | Valid port assignments |
| Healthcheck: `python urllib.request.urlopen` | INT-002, TECH-030 | CORRECT | No curl in slim images |
| `depends_on` with `condition: service_healthy` | INT-002 | CORRECT | Docker Compose v2 syntax |
| Named volumes: architect-data, contract-data, intel-data | INT-002 | CORRECT | Standard persistence |
| Bridge network: super-team-net | INT-002 | CORRECT | Custom bridge network |
| `restart: unless-stopped` | INT-002 | CORRECT | Valid restart policy |
| python:3.12-slim base image | INT-003 | CORRECT | Standard slim Python image |
| Non-root user (appuser) | INT-003 | CORRECT | Docker security best practice |
| EXPOSE 8000 | INT-003 | CORRECT | Documentation port |
| CMD uvicorn format | INT-003 | CORRECT | ASGI server startup |
| Service names = hostnames in env vars | WIRE-022 | CORRECT | Docker DNS resolution behavior |
| Copy src/shared/ in each Dockerfile | WIRE-023 | CORRECT | Multi-package Python apps |
| ChromaDB pre-download in Dockerfile | TECH-023 | CORRECT | Avoids runtime download |

**No issues found in Build 1 Docker references.**

---

## 5. Build 2 PRD Docker Findings

Build 2 contains **zero** Docker or Traefik references. This is expected -- Build 2 focuses on the Builder Fleet (agent-team), which runs as Python processes, not Docker containers.

---

## 6. Tech Research File Assessment

The `BUILD3_TECH_DOCKER_TRAEFIK.md` file is comprehensive and technically accurate. Key strengths:

- Correct `depends_on` conditions with all 3 variants documented
- All 6 healthcheck fields documented with per-service examples
- Complete Traefik v3 label reference (routers, services, middlewares)
- Correct `--ping=true` requirement for Traefik healthcheck
- Proper `exposedByDefault: false` recommendation
- Complete middleware reference (StripPrefix, RateLimit, CORS, Headers, ForwardAuth, Chain)
- Multi-service Docker Compose example matches Traefik v3 best practices
- Docker socket read-only mount included
- Python subprocess and docker-py patterns both documented
- Compatibility notes are accurate (no `version` key needed, v2 plugin syntax)

**One issue:** Section 5.3 uses `aiohttp` instead of `httpx` (see Issue #3 above).

---

## 7. Verification Checklist

### Docker Compose v2

- [x] `depends_on` with `condition: service_healthy` syntax -- VERIFIED
- [x] `healthcheck` fields: test, interval, timeout, retries, start_period, start_interval -- VERIFIED (start_interval optional)
- [x] Volume syntax: named volumes, bind mounts, tmpfs -- VERIFIED
- [x] Network configuration: bridge, custom networks -- VERIFIED
- [x] Environment variable syntax: `${VAR:-default}` vs `${VAR-default}` -- VERIFIED
- [x] Multi-stage build references -- VERIFIED (tech research)
- [x] Resource limits syntax (deploy.resources) -- VERIFIED (tech research)
- [x] Restart policies -- VERIFIED
- [x] Port mapping format -- VERIFIED
- [x] docker-py Python SDK: `docker.from_env()`, container lifecycle methods -- VERIFIED

### Traefik v3

- [x] Docker provider labels format: `traefik.http.routers.NAME.rule=...` -- VERIFIED
- [x] Routing rules: `Host()`, `PathPrefix()`, `Headers()` -- v3 syntax VERIFIED
- [x] Middleware configuration via labels -- VERIFIED
- [x] Entry points configuration -- VERIFIED
- [x] TLS/SSL configuration -- VERIFIED (tech research, not used in PRD core)
- [x] Dashboard enable/disable -- VERIFIED
- [x] Health check integration -- VERIFIED (with Issue #1 caveat)
- [x] Load balancing configuration -- VERIFIED
- [x] v2 vs v3 syntax differences -- VERIFIED (no v2-only syntax found)

---

## 8. Summary

| Severity | Count | Details |
|----------|-------|---------|
| CRITICAL | 0 | -- |
| HIGH | 0 | -- |
| MEDIUM | 1 | ISSUE-1: Missing --ping=true for Traefik healthcheck |
| LOW | 2 | ISSUE-2: JSON output format, ISSUE-3: aiohttp vs httpx in tech research |
| INFO | 1 | ISSUE-4: TECH-010 backtick note clarity |

**Overall Verdict: PASS with 1 MEDIUM fix recommended**

The Docker Compose v2 and Traefik v3 usage across all three Build PRDs is technically accurate. The tech research reference file is comprehensive and well-sourced. The single MEDIUM issue (missing `--ping=true` prerequisite for Traefik healthcheck) should be addressed to prevent healthcheck failures in generated compose files. All other Docker and Traefik patterns, labels, configurations, and Python integration code are correct and follow current best practices.
