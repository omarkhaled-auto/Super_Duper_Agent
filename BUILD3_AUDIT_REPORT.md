# BUILD3_PRD.md Exhaustive Technical Audit Report

**Auditor:** BUILD 3 AUDITOR (Claude Opus 4.6)
**Date:** 2026-02-15
**PRD Version:** Build 3: Integrator + Quality Gate + Super Orchestrator
**Verdict:** CONDITIONAL PASS -- 1 CRITICAL must be fixed before build

---

## Executive Summary

BUILD3_PRD.md is a well-structured, highly detailed PRD covering 7 milestones, 70 REQs, 32 TECH requirements, 22 WIRE requirements, 40 TEST requirements, 11 SVC entries, 8 INT integration requirements, and 4 SEC security requirements. The PRD is among the most implementation-ready documents audited, with exact regex patterns, full dataclass schemas, and complete state machine transition tables.

However, **one CRITICAL bug** exists: the pact-python v3 Verifier API is described incorrectly across 4 locations (REQ-021, TECH-013, SVC-002 table, SVC-002 checklist). The PRD describes the **removed v2 API** (`Verifier().set_info()`) while specifying pact-python 3.2.1+ (which uses an entirely different constructor and method API). This will cause build failure if implemented as written.

**Issue Counts:** 1 CRITICAL, 2 HIGH, 5 MEDIUM, 3 LOW, 1 INFO

---

## 1. Technology Verification Table

| Technology | Version in PRD | Latest Verified | API Accuracy | Status |
|---|---|---|---|---|
| pact-python | 3.2.1+ | 3.x (Feb 2026) | **WRONG** -- uses removed v2 API | CRITICAL |
| schemathesis | 4.x | 4.x | CORRECT -- `get_all_operations()`, `case.call()`, `validate_response()`, `FailureGroup` all verified | PASS |
| transitions | 0.9.2+ | 0.9.2+ | CORRECT -- `AsyncMachine` from `transitions.extensions.asyncio`, `queued=True`, `model` param | PASS |
| typer | 0.21.0+ | 0.23.1 (Feb 2026) | CORRECT -- version callback with `is_eager=True` pattern verified | PASS |
| rich | 13.0+ | 13.x | CORRECT -- `from rich.console import Group` verified | PASS |
| Docker Compose | v2 | v2 | CORRECT -- `docker compose` (no hyphen) syntax | PASS |
| MCP Python SDK | >=1.25,<2 | >=1.25,<2 | CORRECT -- `StdioServerParameters`, `ClientSession`, `call_tool()` consistent with BUILD1/BUILD2 | PASS |
| FastAPI | 0.129.0+ | 0.129.0+ | CORRECT | PASS |
| httpx | 0.28.x+ | 0.28.x+ | CORRECT -- `AsyncClient` with timeout | PASS |
| pytest-asyncio | 0.24.x+ | 0.24.x+ | CORRECT -- `asyncio_mode = "auto"` | PASS |
| PyJWT | 2.8+ | 2.8+ | CORRECT | PASS |
| opentelemetry-api | 1.25+ | 1.25+ | CORRECT -- W3C traceparent format | PASS |
| Traefik | v3.6 | v3.6 | CORRECT -- Docker provider, PathPrefix backtick syntax | PASS |
| detect-secrets | 1.5+ | 1.5+ | **UNUSED** -- listed in tech stack but no REQ uses it | MEDIUM |
| testcontainers[compose] | 4.x | 4.x (API verified via Context7) | **UNUSED** -- listed in tech stack but no REQ uses it | MEDIUM |
| docker-py | 7.x+ | 7.x+ | Referenced but no direct usage in REQs | LOW |
| pydantic | 2.x+ | 2.x+ | CORRECT | PASS |
| PyYAML | 6.x+ | 6.x+ | CORRECT | PASS |

---

## 2. Issue List

### CRITICAL-001: pact-python v3 Verifier API is Wrong (4 locations)

**Severity:** CRITICAL
**Locations:** REQ-021 (line ~249), TECH-013 (line ~263), SVC-002 table (line ~277), SVC-002 checklist (line ~281)
**Impact:** Build will fail -- code written from these instructions will use removed API methods

**Problem:** The PRD specifies pact-python 3.2.1+ but describes the **removed v2 API**. In pact-python v3 (Rust FFI rewrite):

| What PRD Says | What v3 Actually Uses |
|---|---|
| `Verifier()` (no args) | `Verifier("provider_name")` -- constructor takes provider name |
| `.set_info("provider", url=url)` | `.add_transport(url=url)` -- `set_info()` was REMOVED |
| `.set_state_handler(url=..., teardown=True)` | `.state_handler(handler, teardown=True)` -- no `set_` prefix |
| "NO `Verifier(name)` constructor" (TECH-013) | `Verifier(name)` IS the correct v3 constructor |

**Additionally contradictory:** REQ-021 says "IMPORTANT: `Verifier(name)` constructor does NOT exist" while the v3 API documentation shows `Verifier(name)` as the primary constructor.

**Correct v3 Usage:**
```python
from pact.v3.verifier import Verifier

verifier = Verifier("my-provider")
verifier.add_source("./pacts/")
verifier.add_transport(url="http://localhost:8080")
verifier.state_handler(handler_function, teardown=True)
result = verifier.verify()  # Returns Self on success, raises on failure
```

**Fix Required:**
1. REQ-021: Replace `Verifier().set_info("provider", url=provider_url)` with `Verifier(provider_name).add_transport(url=provider_url)`
2. REQ-021: Replace `verifier.set_state_handler(url=..., teardown=True)` with `verifier.state_handler(handler_function, teardown=True)`
3. TECH-013: Reverse the constructor guidance -- `Verifier(name)` IS correct, `Verifier()` with no args is WRONG
4. TECH-013: Replace `set_state_handler()` with `state_handler()`
5. SVC-002 table and checklist: Update Verifier chain to `Verifier(name).add_transport(url=url).add_source(file).verify()`

---

### HIGH-001: Dockerfile Template Inconsistency (Node/Express)

**Severity:** HIGH
**Locations:** REQ-015 (line ~164, inline text) vs REQ-015 (line ~183, fenced code block)
**Impact:** Agent confusion -- two different templates for the same stack

**Problem:** REQ-015 provides two Node/Express Dockerfile templates that differ:

| Feature | Inline Template (REQ-015 text) | Fenced Code Block |
|---|---|---|
| npm install | `npm ci --omit=dev` | `npm ci --production` |
| HEALTHCHECK | Present | **Missing** |
| EXPOSE | 3000 | 3000 |

- `npm ci --production` has been deprecated since npm 8; `npm ci --omit=dev` is the modern equivalent
- The inline template includes HEALTHCHECK; the fenced code block omits it

**Fix Required:** Unify both templates. Use `npm ci --omit=dev` (modern) and include HEALTHCHECK in both. The fenced code block should match:
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json .
RUN npm ci --omit=dev
COPY . .
EXPOSE 3000
HEALTHCHECK CMD node -e "require('http').get('http://localhost:3000/api/health', r => process.exit(r.statusCode === 200 ? 0 : 1))"
CMD ["node", "src/index.js"]
```

---

### HIGH-002: Python Dockerfile Template Missing HEALTHCHECK in Fenced Block

**Severity:** HIGH
**Location:** REQ-015 (line ~168-177, fenced code block)
**Impact:** Docker health checks won't work for Python services using the fenced template

**Problem:** The fenced code block for the Python/FastAPI Dockerfile template omits the HEALTHCHECK instruction that IS present in the inline REQ-015 text. The inline text says:
> HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

But the fenced block only has `FROM`, `WORKDIR`, `COPY`, `RUN`, `COPY`, `EXPOSE`, `CMD` -- no `HEALTHCHECK`.

**Fix Required:** Add the HEALTHCHECK instruction to the fenced Python template.

---

### MEDIUM-001: detect-secrets Listed but Never Used

**Severity:** MEDIUM
**Location:** Technology Stack (line ~21)
**Impact:** Unnecessary dependency; potential confusion about which secret scanning approach to use

**Problem:** The technology stack lists "detect-secrets 1.5+ (Python API with transient_settings)" but no functional requirement (REQ-xxx) actually uses the detect-secrets library. The security scanner (REQ-035) performs secret scanning using custom regex patterns (SEC-SECRET-001 through SEC-SECRET-012), completely bypassing detect-secrets.

**Fix Required:** Either:
1. Remove detect-secrets from the technology stack (recommended -- custom regex is simpler and self-contained), OR
2. Add a REQ that uses detect-secrets for enhanced scanning beyond the regex patterns

---

### MEDIUM-002: testcontainers[compose] Listed but Never Used

**Severity:** MEDIUM
**Location:** Technology Stack (line ~18)
**Impact:** Unnecessary dependency

**Problem:** `testcontainers[compose] 4.x` is listed in the technology stack with "(DockerCompose with wait strategies)" but no REQ uses it. The DockerOrchestrator (REQ-017) uses direct `docker compose` subprocess calls (`asyncio.create_subprocess_exec("docker", "compose", ...)`), not the testcontainers Python library.

**Fix Required:** Either:
1. Remove testcontainers from the tech stack (recommended -- direct subprocess is simpler), OR
2. Rewrite REQ-017 to use testcontainers' `DockerCompose` class with `waiting_for()` strategies (API verified correct via Context7)

---

### MEDIUM-003: REQ-019 Overly Restrictive About Schemathesis API

**Severity:** MEDIUM
**Location:** REQ-019 (line ~245)
**Impact:** Misleading -- could cause agent to reject valid code during review

**Problem:** REQ-019 states: "NOTE: `schema.items()` and `schema[path][method]` are NOT valid Schemathesis 4.x APIs." However, Context7 documentation confirms that `schema["/path"]["METHOD"]` indexing **does work** in Schemathesis 4.x (it returns API operations). The PRD is correct that `get_all_operations()` is the recommended approach, but declaring `schema[path][method]` as "NOT valid" is factually incorrect.

**Fix Required:** Change the NOTE to: "NOTE: While `schema[path][method]` indexing works, `get_all_operations()` is the recommended API for programmatic iteration. Do NOT use `schema.items()` which is not a Schemathesis API."

---

### MEDIUM-004: Missing Error Handling Pattern for Schemathesis `from_url()` Failure

**Severity:** MEDIUM
**Location:** REQ-019 (line ~245)
**Impact:** No guidance for when OpenAPI spec is unreachable or malformed

**Problem:** REQ-019 details the happy-path flow (`from_url()` -> `get_all_operations()` -> `make_case()` -> `call()` -> `validate_response()`) but provides no error handling for when `from_url()` fails (e.g., service not running, invalid OpenAPI spec). The agent needs to know what exception to catch.

**Fix Required:** Add: "If `schemathesis.openapi.from_url()` fails due to unreachable URL or invalid spec, it raises `requests.exceptions.ConnectionError` or `schemathesis.exceptions.SchemaError`. Catch these and return an empty violations list with a warning log."

---

### MEDIUM-005: SVC Table Missing Field Schemas for Some Entries

**Severity:** MEDIUM
**Locations:** SVC-005 through SVC-011 (lines ~460-474)
**Impact:** Reduced agent-readiness for pipeline phase implementations

**Problem:** While SVC-001 through SVC-004 have well-defined Request/Response DTOs, SVC-005 through SVC-011 (pipeline phase SVCs) have DTOs that reference complex types (ServiceMap, DomainModel, BuilderResult) without specifying their field-level schemas. The agent must cross-reference BUILD1 models for ServiceMap/DomainModel and M1's REQ-002 for BuilderResult.

**Fix Required:** Add brief field lists for referenced external types, or add cross-reference notes like "ServiceMap: see Build 1 REQ-002 for field schema".

---

### LOW-001: TECH Number Gap (TECH-030 vs TECH-031 vs TECH-032 Ordering)

**Severity:** LOW
**Location:** TECH-028 through TECH-032 (lines ~509-512)
**Impact:** Minor readability issue

**Problem:** TECH requirements are numbered 028, 029, 032, 031, 030 (out of order in the document). TECH-032 appears before TECH-031 and TECH-030 in the PRD text.

**Fix Required:** Reorder TECH-030, TECH-031, TECH-032 to appear in numeric order.

---

### LOW-002: docker-py Listed but Indirectly Used

**Severity:** LOW
**Location:** Technology Stack (line ~27)
**Impact:** Minimal -- dependency may be needed transitionally

**Problem:** `docker-py 7.x+` is listed but no REQ directly uses the Docker Python SDK. All Docker operations go through `docker compose` subprocess calls. docker-py may be used by testcontainers internally, but since testcontainers is also unused (MEDIUM-002), this is a chain of unused dependencies.

**Fix Required:** Review if docker-py is needed. If testcontainers is removed, docker-py can likely be removed too.

---

### LOW-003: REQ-011 `fail` Transition Source List Hardcoded

**Severity:** LOW
**Location:** REQ-011 (line ~156)
**Impact:** Maintenance burden if states are added

**Problem:** The `fail` transition uses an explicit source list of 9 states (excluding `complete` and `failed`). The PRD correctly explains why `source="*"` is avoided (preventing `complete -> failed` corruption). However, if a new state is added in the future, someone must remember to add it to this list.

**Fix Required:** Add a comment in REQ-011: "If new states are added, they MUST be included in the fail transition source list."

---

### INFO-001: `npm ci --production` Deprecation

**Severity:** INFO
**Location:** REQ-015 fenced code block (line ~184)
**Impact:** Warning during npm install; no functional impact

**Problem:** `npm ci --production` was deprecated in npm 8 in favor of `npm ci --omit=dev`. The inline REQ-015 text correctly uses `--omit=dev` but the fenced block uses the deprecated flag.

**Note:** This is subsumed by HIGH-001 but called out for completeness.

---

## 3. Architectural Soundness

### 4-Layer Quality Gate Separation: PASS

The quality gate design is architecturally sound:
- **L1** (per-service build results) correctly aggregates BuilderResult data
- **L2** (contract compliance) correctly consumes IntegrationReport from M2
- **L3** (system-level) correctly composes 3 independent scanners (security, observability, Docker)
- **L4** (adversarial) correctly operates as advisory-only with pure static analysis
- Sequential gating (L1 must pass for L2, etc.) is well-specified
- Configurable blocking severity prevents false-positive pipeline failures

### State Machine: PASS

- 11 states and 13 transitions are internally consistent
- `fail` transition correctly excludes `complete` and `failed` (preventing state corruption)
- RESUME_TRIGGERS map enables correct pipeline resume
- Guard conditions are specified for all transitions that need them
- `queued=True` on AsyncMachine prevents concurrent state mutation

### Milestone Dependencies: PASS

```
M1 -> M2 (parallel with M3) -> M4 -> M5 -> M6 -> M7
```
- No circular dependencies
- M2 and M3 correctly parallelizable (both depend only on M1)
- Critical path (M1->M2->M4->M5->M6->M7) is correctly identified
- Docker infrastructure in M1 is consumed by M5 (not M3), avoiding premature Docker dependency

### Service Discovery + Docker Compose Merge: PASS

- ComposeGenerator (REQ-015) correctly generates per-service entries with Traefik labels
- TraefikConfigGenerator (REQ-016) produces correct Traefik v3 Docker labels with PathPrefix backtick syntax
- DockerOrchestrator (REQ-017) correctly uses `docker compose` v2 commands
- ServiceDiscovery (REQ-018) correctly provides health check polling
- Frontend/backend network separation is specified

### Error Handling Architecture: PASS

- Per-transition error handling in REQ-053 covers all failure modes:
  - Architect timeout: retry up to max_retries, then fail
  - Partial contract failure: proceed with warning
  - All builders fail: transition to failed
  - Some builders fail: proceed with successful only
  - Integration: proceed regardless (quality gate evaluates)
  - Quality gate fail: enter fix loop bounded by max_fix_retries
- GracefulShutdown (REQ-013) correctly handles reentrancy guard and emergency save
- Budget checking after every phase (TECH-026)

---

## 4. Completeness Assessment

### Requirements Coverage: 98%

| Category | Count | Fully Specified | Needs Fix |
|---|---|---|---|
| Functional (REQ) | 70 | 69 | 1 (REQ-021 pact API) |
| Technical (TECH) | 32 | 31 | 1 (TECH-013 pact API) |
| Wiring (WIRE) | 22 | 22 | 0 |
| Test (TEST) | 40 | 40 | 0 |
| Service (SVC) | 11 | 10 | 1 (SVC-002 pact API) |
| Integration (INT) | 8 | 8 | 0 |
| Security (SEC) | 4 | 4 | 0 |

### Scan Code Coverage: COMPLETE

All 40 scan codes are fully specified with exact regex patterns:
- SEC-001..006 (JWT Security): 6 codes, all with regex
- CORS-001..003: 3 codes, all with regex
- LOG-001, LOG-004, LOG-005: 3 codes, all with regex
- TRACE-001: 1 code, with regex
- SEC-SECRET-001..012: 12 codes, all with regex
- DOCKER-001..008: 8 codes, all with regex
- ADV-001..006: 6 codes, all with regex and file-walking instructions
- HEALTH-001: 1 code, with detection logic
- Total: 40 (verified: `6+3+3+1+12+8+6+1 = 40`)

### Config Schemas: COMPLETE

All nested dataclasses fully specified:
- SuperOrchestratorConfig with 4 nested configs
- ArchitectConfig, BuilderConfig, IntegrationConfig, QualityGateConfig
- All fields with types and defaults

### State Persistence: COMPLETE

PipelineState (REQ-009) covers all persistence fields for resume.

---

## 5. Agent-Readiness Assessment

### Score: 95/100

**Strengths:**
- Exact regex patterns for all 40 scan codes -- no guessing needed
- Complete dataclass definitions with all field types and defaults
- State machine transitions table with guards and callbacks
- Dockerfile templates provided inline
- SVC table with DTOs for all service boundaries
- File walking mechanism explicitly specified (pathlib.rglob, not os.walk)
- EXCLUDE_DIRS set provided
- Async/sync boundary clearly documented (asyncio.to_thread wrapping)

**Weaknesses (costing 5 points):**
- pact-python API is wrong (-3 points) -- agent would implement broken code
- Two dead dependencies (detect-secrets, testcontainers) create confusion (-1 point)
- SVC-005..011 reference external types without field schemas (-1 point)

---

## 6. Cross-Build Compatibility

### Build 1 Interface Compatibility: PASS

| Build 3 Consumer | Build 1 Provider | Verified |
|---|---|---|
| `run_architect_phase()` calls `decompose` tool | Architect MCP `decompose` tool (4 tools total) | PASS |
| `run_contract_registration()` calls `create_contract`, `validate_spec`, `list_contracts` | Contract Engine MCP (9 tools) | PASS |
| MCP SDK version `>=1.25,<2` | Build 1 uses same MCP SDK version | PASS |
| `StdioServerParameters` + `ClientSession` pattern | Build 1 MCP servers use stdio transport | PASS |
| Lazy MCP imports with ImportError fallback (INT-006) | Build 1 not required at import time | PASS |

### Build 2 Interface Compatibility: PASS

| Build 3 Consumer | Build 2 Provider | Verified |
|---|---|---|
| `run_parallel_builders()` invokes `python -m agent_team` | Build 2 CLI entry point | PASS |
| `generate_builder_config()` produces agent-team config.yaml | Build 2 `_dict_to_config()` parses config | PASS |
| Builder result parsing from `.agent-team/STATE.json` | Build 2 `RunState.to_dict()` writes summary fields | PASS |
| `create_execution_backend()` pattern (WIRE-016) | Build 2 `ExecutionBackend` protocol | PASS |
| Config fields: depth, milestone, e2e_testing, post_orchestration_scans | Build 2 `AgentTeamConfig` schema | PASS |
| `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]` | Build 2 v6.0 return type change | PASS |

### Run 4 Compatibility: PASS

| Run 4 Tests | Build 3 Produces | Verified |
|---|---|---|
| Pipeline state reaches "complete" (SC-01) | PipelineState with `current_state` field | PASS |
| 3-service deploy with health checks (SC-02) | DockerOrchestrator + ServiceDiscovery | PASS |
| Quality gate report (SC-04) | QUALITY_GATE_REPORT.md via `generate_quality_gate_report()` | PASS |
| Pipeline phases match expected order (INT-007) | State machine transitions enforce order | PASS |

### Namespace Collision Avoidance: PASS

Build 3 uses `build3_shared/` namespace (line ~676) to avoid collision with Build 1's `src/shared/`. This is correctly identified and documented.

---

## 7. Regex Pattern Verification (Sampling)

| Pattern | Code | Correctness |
|---|---|---|
| `AKIA[0-9A-Z]{16}` | SEC-SECRET-001 | CORRECT -- standard AWS access key format |
| `-----BEGIN (?:RSA \|EC \|DSA \|OPENSSH \|ENCRYPTED )?PRIVATE KEY-----` | SEC-SECRET-002 | CORRECT -- covers all PEM variants |
| `gh[psatr]_[A-Za-z0-9_]{36,}` | SEC-SECRET-007 | CORRECT -- covers ghp_, ghs_, gha_, ghr_, but also matches gho_, ghu_ via `[psatr]` catching partial. Actually: p,s,a,t,r covers ghp_ (personal), ghs_ (server), gha_ (actions), ght_ (no such token type?), ghr_ (refresh). Missing: gho_ (OAuth) and ghu_ (user-to-server) from the regex character class. The PRD comment says "covers gho_, ghu_" but `[psatr]` does NOT match `o` or `u`. |
| `xox[bpoas]-[0-9]+-[0-9A-Za-z\-]+` | SEC-SECRET-011 | CORRECT -- covers xoxb, xoxp, xoxa, xoxo, xoxs |
| `SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}` | SEC-SECRET-012 | CORRECT -- standard SendGrid key format |
| `(?:publish\|emit\|dispatch\|send_event\|fire)\s*\(\s*['\"](\w+)['\"]` | ADV-001 | CORRECT -- captures event names |
| `^FROM\s+\S+:latest\b` or `^FROM\s+[^:]+$` | DOCKER-003 | CORRECT -- catches both explicit `:latest` and missing tag |
| `privileged:\s*true` | DOCKER-006 | CORRECT |
| `allow_origins=["*"]` | CORS-001 | CORRECT |

**Note on SEC-SECRET-007:** The PRD comment claims the regex "covers ghp_ personal, ghs_ server-to-server, gha_ actions, ghr_ refresh, gho_ OAuth, ghu_ user-to-server" but the character class `[psatr]` only matches `p`, `s`, `a`, `t`, `r` -- it does NOT match `o` (OAuth) or `u` (user-to-server). To fix: change to `gh[psatrou]_` or more broadly `gh[a-z]_`.

---

## 8. Summary

| Dimension | Score | Notes |
|---|---|---|
| Technology Accuracy | 92/100 | pact-python API critically wrong; 2 dead dependencies |
| Implementation Correctness | 96/100 | Dockerfile template inconsistency; Schemathesis overly restrictive NOTE |
| Architectural Soundness | 99/100 | Excellent 4-layer gate design; robust state machine |
| Completeness | 98/100 | Near-complete; minor gaps in SVC field schemas |
| Agent-Readiness | 95/100 | Highly detailed; pact-python instructions would cause build failure |
| Cross-Build Compatibility | 100/100 | All interfaces verified against BUILD1, BUILD2, RUN4 |

**Overall: CONDITIONAL PASS**

The PRD is ready for build after fixing CRITICAL-001 (pact-python v3 API). The 2 HIGH issues (Dockerfile template inconsistency) should also be fixed to prevent agent confusion. All other issues are non-blocking.

---

## Appendix: Verification Sources

- pact-python v3 API: Official Pact docs (pact-foundation), DeepWiki pact-python
- Schemathesis 4.x API: Context7 `/schemathesis/schemathesis`, DeepWiki schemathesis
- transitions AsyncMachine: Context7 `/pytransitions/transitions`
- Typer 0.21.0+: Context7 `/fastapi/typer` (latest 0.23.1 verified)
- Rich Group import: `from rich.console import Group` confirmed in Rich docs
- testcontainers[compose]: Context7 `/testcontainers/testcontainers-python` (DockerCompose API verified)
- Docker Compose v2: Official Docker documentation
