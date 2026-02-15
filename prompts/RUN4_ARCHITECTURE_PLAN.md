# Run 4 Architecture Plan: End-to-End Wiring, Verification, and Audit

> **Author**: Architecture Planner Agent
> **Date**: 2026-02-15
> **Purpose**: Complete architecture blueprint for Run 4 — the final phase that wires 3 independently-built systems together, verifies end-to-end operation, applies fix passes, and produces the final audit report.
> **Inputs**: RUN4_TECH_MCP_WIRING.md, RUN4_TECH_DOCKER_ORCHESTRATION.md, RUN4_TECH_E2E_VERIFICATION.md, RUN4_TECH_AUDIT_SCORING.md, RUN4_CROSS_BUILD_INTERFACES.md, BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md, BUILD3_ARCHITECTURE_PLAN.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md

---

## Table of Contents

1. [Run 4 Overview and Success Criteria](#1-run-4-overview-and-success-criteria)
2. [3-Service Sample Application Specification](#2-3-service-sample-application-specification)
3. [Milestone Structure (6 Milestones)](#3-milestone-structure-6-milestones)
4. [Verification Test Matrix](#4-verification-test-matrix)
5. [Fix Pass Methodology](#5-fix-pass-methodology)
6. [Audit Scoring Rubric](#6-audit-scoring-rubric)
7. [State Persistence for Resume](#7-state-persistence-for-resume)
8. [Docker Compose Topology](#8-docker-compose-topology)
9. [Risk Assessment and Mitigations](#9-risk-assessment-and-mitigations)

---

## 1. Run 4 Overview and Success Criteria

### 1.1 What Run 4 Does

Run 4 is NOT a build. It is a verification and integration run that:
1. Takes the outputs of Build 1 (3 MCP servers), Build 2 (upgraded agent-team), and Build 3 (Super Orchestrator + Integrator + Quality Gate)
2. Wires them together in a single Docker Compose environment
3. Feeds a 3-service sample PRD through the complete pipeline
4. Catalogs every defect discovered during wiring
5. Applies fix passes until convergence
6. Produces an honest audit report (SUPER_TEAM_AUDIT_REPORT.md)

### 1.2 Success Criteria

| ID | Criterion | Type | Pass Condition |
|---|---|---|---|
| SC-01 | Complete pipeline runs end-to-end without human intervention | Binary | Pipeline reaches "complete" state |
| SC-02 | 3-service test app deploys | Binary | All 3 services show "healthy" in `docker compose ps` |
| SC-03 | All health checks pass | Binary | HTTP 200 on `/health` for all services |
| SC-04 | Integration tests pass | Binary | `integration_report.overall_health != "failed"` |
| SC-05 | Contract violations are detected and reported | Binary | Planted violation appears in QUALITY_GATE_REPORT.md |
| SC-06 | Codebase Intelligence indexes generated code | Binary | `index_stats.total_symbols > 0` after builder completes |
| SC-07 | Codebase Intelligence responds to MCP queries | Binary | `find_definition("User")` returns file/line result |
| SC-08 | Total time under 6 hours for 3-service app | Graduated | GREEN: <6h, YELLOW: 6-10h, RED: >10h |

### 1.3 Estimated Budget

| Phase | Estimated Cost | Time |
|---|---|---|
| M1: Test Infrastructure | $2-5 | 30-60 min |
| M2: Build 1->2 Wiring | $3-8 | 45-90 min |
| M3: Build 2->3 Wiring | $3-8 | 45-90 min |
| M4: End-to-End Pipeline | $15-25 | 2-4 hours |
| M5: Fix Pass | $10-15 | 1-2 hours |
| M6: Audit Report | $3-5 | 30-60 min |
| **Total** | **$36-66** | **5-9 hours** |

---

## 2. 3-Service Sample Application Specification

### 2.1 Application: TaskTracker

A minimal task/order tracking system with authentication, order management, and notification delivery. Designed to exercise every integration point in the Super Agent Team pipeline.

**Why this specific app:**
- 3 services exercises parallel builder execution
- Auth tokens exercise cross-service authentication contracts
- Order state machine exercises stateful event-driven contracts (AsyncAPI)
- Notification consumer exercises event subscription and data flow tracing
- Simple enough to build in <4 hours, complex enough to expose integration bugs

### 2.2 Service Architecture

```
+-----------------+     +------------------+     +----------------------+
| auth-service    |---->|  order-service    |---->| notification-service |
| (Python/FastAPI)|     |  (Python/FastAPI) |     |   (Python/FastAPI)   |
|                 |     |                   |     |                      |
| POST /register  |     | POST /orders      |     | POST /notify         |
| POST /login     |     | GET  /orders/:id  |     | GET  /notifications  |
| GET  /users/me  |     | PUT  /orders/:id  |     |                      |
| GET  /health    |     | GET  /health      |     | GET  /health         |
+-----------------+     +------------------+     +----------------------+
        |                       |                          ^
        |    JWT validation     |    OrderCreated event    |
        +-----------------------+--------------------------+
```

### 2.3 Entities

| Entity | Service | Fields |
|---|---|---|
| User | auth-service | id (UUID), email (string), password_hash (string), created_at (datetime) |
| Order | order-service | id (UUID), user_id (UUID), status (enum: pending/confirmed/shipped/delivered/cancelled), items (list[dict]), total (decimal), created_at (datetime) |
| Notification | notification-service | id (UUID), user_id (UUID), type (enum: email/sms), message (string), sent_at (datetime), order_id (UUID) |

### 2.4 Contracts

| Contract ID | Type | Provider | Consumer | Endpoints/Channels |
|---|---|---|---|---|
| auth-api | OpenAPI 3.1 | auth-service | order-service | POST /register, POST /login, GET /users/me |
| order-api | OpenAPI 3.1 | order-service | notification-service | POST /orders, GET /orders/:id, PUT /orders/:id |
| order-events | AsyncAPI 3.0 | order-service | notification-service | OrderCreated, OrderShipped channels |

### 2.5 Order State Machine

```
pending --(confirm)--> confirmed --(ship)--> shipped --(deliver)--> delivered
    |                      |                     |
    +------(cancel)--------+-------(cancel)------+-------> cancelled
```

### 2.6 Cross-Service Data Flows

| # | Flow | Source | Destination | Data Shape |
|---|---|---|---|---|
| DF-1 | User registers | Client | auth-service | `{email, password}` -> `{id, email, created_at}` |
| DF-2 | User logs in | Client | auth-service | `{email, password}` -> `{access_token, refresh_token}` |
| DF-3 | Create order (JWT) | Client | order-service | `{items, total}` + JWT -> `{id, status, items, total}` |
| DF-4 | Order created event | order-service | notification-service | `{order_id, user_id, items, total}` |
| DF-5 | Send notification | notification-service | (mock) | `{user_id, type, message}` |

### 2.7 Sample PRD File

Path: `tests/run4/fixtures/sample_prd.md`

The PRD will contain ~300 lines covering:
- Project overview (TaskTracker)
- 3 service definitions with endpoints, entities, and technology choices
- Cross-service contracts (explicitly defining JWT validation flow and event schemas)
- Non-functional requirements (health endpoints, structured logging, no hardcoded secrets)
- All services use Python + FastAPI + PostgreSQL

### 2.8 Expected Contract Artifacts

Path: `tests/run4/fixtures/`

| File | Contents |
|---|---|
| `sample_openapi_auth.yaml` | OpenAPI 3.1 spec for auth-service (3 endpoints) |
| `sample_openapi_order.yaml` | OpenAPI 3.1 spec for order-service (3 endpoints) |
| `sample_asyncapi_order.yaml` | AsyncAPI 3.0 spec for order-events (2 channels) |
| `sample_pact_auth.json` | Pact V4 contract: order-service consuming auth-service |

---

## 3. Milestone Structure (6 Milestones)

### Milestone 1: Test Infrastructure + Fixtures

**ID**: run4-m1
**Dependencies**: None
**Duration**: 30-60 minutes
**Purpose**: Establish the test framework, sample app fixtures, mock MCP servers, Run4Config, Run4State persistence, and shared test utilities that all subsequent milestones depend on.

#### Requirements

**R4-M1-001: Run4Config dataclass**

```python
@dataclass
class Run4Config:
    # Paths
    build1_project_root: Path          # Path to Build 1 super-team/ directory
    build2_project_root: Path          # Path to Build 2 agent-team/ directory
    build3_project_root: Path          # Path to Build 3 super-team/ directory
    output_dir: Path = Path(".run4")   # Run 4 output directory

    # Docker
    compose_project_name: str = "super-team-run4"
    docker_compose_files: list[str] = field(default_factory=lambda: [
        "docker-compose.infra.yml",
        "docker-compose.build1.yml",
        "docker-compose.traefik.yml",
    ])

    # Verification
    health_check_timeout_s: int = 120
    health_check_interval_s: float = 3.0
    required_consecutive_healthy: int = 2

    # MCP
    mcp_startup_timeout_ms: int = 30000
    mcp_tool_timeout_ms: int = 60000
    mcp_first_start_timeout_ms: int = 120000  # ChromaDB first download

    # Builders
    max_concurrent_builders: int = 3
    builder_timeout_s: int = 1800
    builder_depth: str = "thorough"

    # Fix passes
    max_fix_passes: int = 5
    fix_effectiveness_floor: float = 0.30     # Stop if below this for 2 passes
    regression_rate_ceiling: float = 0.25     # Stop if above this for 2 passes

    # Budget
    budget_limit: float | None = None

    # Sample app
    sample_prd_path: Path = Path("tests/run4/fixtures/sample_prd.md")
```

**R4-M1-002: Run4State dataclass**

```python
@dataclass
class Run4State:
    run_id: str = ""                                    # UUID
    started_at: str = ""                                # ISO-8601
    updated_at: str = ""                                # ISO-8601
    current_milestone: int = 0                          # 1-6
    current_phase: str = "not_started"                  # Phase within milestone
    completed_milestones: list[int] = field(default_factory=list)
    milestone_artifacts: dict[str, Any] = field(default_factory=dict)

    # M2 results
    mcp_health: dict[str, dict] = field(default_factory=dict)    # server_name -> health_result
    mcp_tool_results: dict[str, dict] = field(default_factory=dict)
    b1_b2_wiring_passed: bool = False

    # M3 results
    builder_invocation_passed: bool = False
    state_json_parsing_passed: bool = False
    config_generation_passed: bool = False
    b2_b3_wiring_passed: bool = False

    # M4 results
    pipeline_completed: bool = False
    services_deployed: list[str] = field(default_factory=list)
    services_healthy: list[str] = field(default_factory=list)
    integration_report: dict = field(default_factory=dict)
    quality_gate_report: dict = field(default_factory=dict)

    # M5 results
    defect_catalog: list[dict] = field(default_factory=list)     # FINDING-xxx entries
    fix_passes: list[dict] = field(default_factory=dict)         # Per-pass metrics
    total_fix_passes: int = 0
    convergence_score: float = 0.0

    # M6 results
    audit_report_path: str = ""
    per_system_scores: dict[str, float] = field(default_factory=dict)
    integration_score: float = 0.0
    aggregate_score: float = 0.0

    # Cost tracking
    total_cost: float = 0.0
    phase_costs: dict[str, float] = field(default_factory=dict)

    # Persistence
    schema_version: int = 1

    def save(self, directory: Path) -> None:
        """Atomic save to JSON — write .tmp then rename."""
        ...

    @classmethod
    def load(cls, directory: Path) -> "Run4State | None":
        """Load from JSON, return None if missing/invalid."""
        ...
```

**R4-M1-003: Sample app fixture files**

Create the following in `tests/run4/fixtures/`:
- `sample_prd.md` — 3-service TaskTracker PRD (Section 2.7)
- `sample_openapi_auth.yaml` — Auth service OpenAPI 3.1 spec
- `sample_openapi_order.yaml` — Order service OpenAPI 3.1 spec
- `sample_asyncapi_order.yaml` — Order events AsyncAPI 3.0 spec
- `sample_pact_auth.json` — Pact V4 contract for auth -> order

**R4-M1-004: Mock MCP server for unit testing**

```python
@pytest.fixture
def mock_mcp_session():
    """Create a mock MCP ClientSession for unit testing."""
    session = AsyncMock()
    session.call_tool = AsyncMock()
    session.list_tools = AsyncMock()
    session.initialize = AsyncMock()
    return session

def make_mcp_result(data: dict, is_error: bool = False):
    """Create a mock MCP tool result."""
    result = MagicMock()
    result.isError = is_error
    content = MagicMock()
    content.text = json.dumps(data)
    result.content = [content]
    return result
```

**R4-M1-005: Shared test utilities**

```python
# Health polling utility
async def poll_until_healthy(
    service_urls: dict[str, str],
    timeout_s: float = 120.0,
    interval_s: float = 3.0,
    required_consecutive: int = 2,
) -> dict[str, HealthCheckResult]:
    ...

# MCP health check utility
async def check_mcp_health(
    server_params: StdioServerParameters,
    timeout: float = 30.0,
) -> dict:
    ...

# Builder state parser
def parse_builder_state(output_dir: Path) -> dict:
    ...

# Result comparison for regression detection
def detect_regressions(
    before: dict[str, list[str]],
    after: dict[str, list[str]],
) -> list[str]:
    ...
```

**R4-M1-006: conftest.py with session-scoped fixtures**

```python
@pytest.fixture(scope="session")
def run4_config() -> Run4Config:
    ...

@pytest.fixture(scope="session")
def sample_prd_text() -> str:
    ...

@pytest.fixture(scope="session")
def build1_root(run4_config) -> Path:
    ...

@pytest.fixture(scope="session")
def contract_engine_params(build1_root, tmp_path_factory) -> StdioServerParameters:
    ...

@pytest.fixture(scope="session")
def architect_params(build1_root, tmp_path_factory) -> StdioServerParameters:
    ...

@pytest.fixture(scope="session")
def codebase_intel_params(build1_root, tmp_path_factory) -> StdioServerParameters:
    ...
```

**R4-M1-007: Test directory structure**

```
tests/run4/
    conftest.py
    test_m2_mcp_wiring.py
    test_m2_client_wrappers.py
    test_m3_builder_invocation.py
    test_m3_config_generation.py
    test_m4_pipeline_e2e.py
    test_m4_health_checks.py
    test_m4_contract_compliance.py
    test_m5_fix_pass.py
    test_m6_audit.py
    test_regression.py
    fixtures/
        sample_prd.md
        sample_openapi_auth.yaml
        sample_openapi_order.yaml
        sample_asyncapi_order.yaml
        sample_pact_auth.json
```

---

### Milestone 2: Build 1 -> Build 2 Wiring Verification

**ID**: run4-m2
**Dependencies**: run4-m1
**Duration**: 45-90 minutes
**Purpose**: Verify that every MCP tool exposed by Build 1's 3 servers is callable from Build 2's client wrappers. Test session lifecycle, error recovery, and fallback paths.

#### Requirements

**R4-M2-001: MCP handshake tests (3 servers)**

For each of {Architect, Contract Engine, Codebase Intelligence}:
1. Spawn via `StdioServerParameters` with correct `cwd` and `env`
2. Call `session.initialize()` — verify capabilities include `tools`
3. Call `session.list_tools()` — verify correct tool count (4, 9, 7)
4. Verify all tool names match expected set exactly (20 total, zero collisions)

**R4-M2-002: MCP tool roundtrip tests (20 tools)**

For each of the 20 MCP tools across 3 servers:
1. Call with valid parameters — verify non-error response
2. Call with invalid parameter types — verify `isError` response (no crash)
3. Call with only required parameters (using defaults) — verify defaults work
4. Parse response into expected schema — verify field presence and types

Tool-specific valid test inputs:

| Tool | Valid Input | Expected Response |
|---|---|---|
| `decompose` | `{prd_text: sample_prd_text}` | Dict with `service_map`, `domain_model` keys |
| `get_service_map` | (none) | Dict or None |
| `get_contracts_for_service` | `{service_name: "auth-service"}` | List of dicts |
| `get_domain_model` | (none) | Dict or None |
| `validate_spec` | `{spec: valid_openapi, type: "openapi"}` | `{valid: true}` |
| `create_contract` | `{service_name: "test", type: "openapi", version: "1.0", spec: {...}}` | Dict with `id`, `status` |
| `get_contract` | `{contract_id: "..."}` | ContractEntry dict or None |
| `validate_endpoint` | `{service_name: "auth", method: "GET", path: "/users/me", response_body: {...}}` | `{valid: bool, violations: [...]}` |
| `generate_tests` | `{contract_id: "..."}` | Non-empty string |
| `check_breaking_changes` | `{contract_id: "...", new_spec: {...}}` | List |
| `mark_implemented` | `{contract_id: "...", service_name: "auth", evidence_path: "src/main.py"}` | Dict with `marked` key |
| `get_unimplemented_contracts` | `{service_name: ""}` | List |
| `list_contracts` | `{}` | Paginated list |
| `find_definition` | `{symbol: "ConnectionPool"}` | Location dict or None |
| `find_callers` | `{symbol: "ConnectionPool"}` | List |
| `find_dependencies` | `{file_path: "src/shared/db/connection.py"}` | Imports dict |
| `search_semantic` | `{query: "database connection"}` | List of results |
| `get_service_interface` | `{service_name: "architect"}` | Interface dict |
| `check_dead_code` | `{}` | List |
| `register_artifact` | `{file_path: "test_file.py", service_name: "test"}` | Stats dict |

**R4-M2-003: Build 2 client wrapper tests**

For each Build 2 MCP client class:
1. `ContractEngineClient` — all 6 methods return correct dataclass with mocked session
2. `CodebaseIntelligenceClient` — all 7 methods return correct dataclass with mocked session
3. `ArchitectClient` — all 4 methods return correct types with mocked session
4. All methods return safe defaults on MCP error (never raise)
5. All methods retry 3 times on transient errors with exponential backoff

**R4-M2-004: Session lifecycle tests**

1. Open session, make 10 sequential calls, close — verify all succeed
2. Open session, kill server process, verify client detects broken pipe
3. Open session, timeout on slow tool call — verify `TimeoutError` propagation
4. Open 3 sessions simultaneously (one per server) — verify no resource conflicts
5. Close session, open new session — verify new session has full database access

**R4-M2-005: Error recovery tests**

1. Kill server mid-call — client reconnects on next call (new session)
2. Feed malformed JSON to tool — `isError` returned, no crash
3. Call non-existent tool name — error response, no crash
4. Server process exits with non-zero — client detects and logs

**R4-M2-006: Fallback path tests**

1. Contract Engine MCP unavailable — Build 2 falls back to `run_api_contract_scan()` from quality_checks.py
2. Codebase Intelligence MCP unavailable — Build 2 falls back to `generate_codebase_map()` from codebase_map.py
3. Architect MCP unavailable — standard PRD decomposition proceeds

**R4-M2-007: Latency benchmarks**

Measure round-trip time for each tool call. Record in M2 artifacts:
- Median, p95, p99 latency per tool
- Session startup time per server
- Acceptable threshold: < 5s per tool call, < 30s startup (120s for Codebase Intel first start)

**R4-M2-008: Cross-server verification**

1. Architect's `get_contracts_for_service` internally calls Contract Engine via HTTP — verify this works when both MCP servers are running
2. Requires Contract Engine FastAPI to also be running (Docker or direct) — this is the hidden dependency

---

### Milestone 3: Build 2 -> Build 3 Wiring Verification

**ID**: run4-m3
**Dependencies**: run4-m1
**Duration**: 45-90 minutes
**Purpose**: Verify that Build 3's Super Orchestrator can invoke Build 2 Builders as subprocesses, parse their output, generate valid configs, and feed fix instructions.

#### Requirements

**R4-M3-001: Builder subprocess invocation**

1. Build 3 calls `python -m agent_team --cwd {dir} --depth {depth}` via `asyncio.create_subprocess_exec`
2. Builder process starts, runs, and exits with code 0
3. `{dir}/.agent-team/STATE.json` is written with `summary` dict
4. Process stdout/stderr captured and parseable

**R4-M3-002: STATE.json parsing (cross-build contract)**

The critical cross-build contract: Build 2's `RunState.to_dict()` writes `summary`, Build 3's `run_parallel_builders()` reads it.

Verify all fields present and correctly typed:

| Field | Path | Type | Required |
|---|---|---|---|
| success | `summary.success` | bool | YES |
| test_passed | `summary.test_passed` | int | YES |
| test_total | `summary.test_total` | int | YES |
| convergence_ratio | `summary.convergence_ratio` | float | YES |
| total_cost | `total_cost` | float | YES |
| health | `health` | str | YES |
| completed_phases | `completed_phases` | list[str] | YES |

**R4-M3-003: Config generation test**

Build 3's `generate_builder_config()` produces a `config.yaml` that Build 2's `_dict_to_config()` can parse:

1. Generate config with all depth levels (quick, standard, thorough, exhaustive)
2. Pass generated YAML to `_dict_to_config()` — verify no parsing errors
3. Verify generated fields: `depth`, `milestone.enabled`, `e2e_testing.enabled`, `post_orchestration_scans` keys
4. Verify `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]` (Build 2's v6.0 return type)

**R4-M3-004: Parallel builder isolation**

1. Launch 3 builders simultaneously with `asyncio.Semaphore(3)`
2. Each builder writes to its own directory — verify no cross-contamination
3. All 3 complete (or timeout) — collect `BuilderResult` per service
4. Semaphore prevents 4th builder from starting until one completes

**R4-M3-005: Fix pass invocation**

1. Write `FIX_INSTRUCTIONS.md` to builder directory with categorized violations
2. Invoke `python -m agent_team --cwd {dir} --depth quick`
3. Verify builder reads FIX_INSTRUCTIONS.md and processes it
4. Parse updated STATE.json after fix pass — verify cost field updated

**R4-M3-006: Agent Teams fallback**

When `config.agent_teams.enabled` is True but Claude CLI unavailable:
1. `create_execution_backend()` returns `CLIBackend` with logged warning
2. Pipeline continues with subprocess mode
3. When `fallback_to_cli` is False — `RuntimeError` raised

---

### Milestone 4: End-to-End Pipeline Test

**ID**: run4-m4
**Dependencies**: run4-m2, run4-m3
**Duration**: 2-4 hours
**Purpose**: Feed the 3-service sample PRD through the COMPLETE pipeline — Architect -> Contract Registration -> 3 Parallel Builders -> Docker Deployment -> Integration Tests -> Quality Gate. All with real subprocesses; Docker via Testcontainers.

#### Requirements

**R4-M4-001: Phase 1 — Build 1 service health**

Start all Build 1 services (via Docker Compose or direct):
1. Architect API responds on :8001 with `/api/health` -> 200
2. Contract Engine API responds on :8002 with `/api/health` -> 200
3. Codebase Intelligence API responds on :8003 with `/api/health` -> 200
4. Gate: ALL 3 must be healthy before proceeding

**R4-M4-002: Phase 2 — MCP tool smoke tests**

1. Architect MCP: `decompose` tool callable with sample PRD
2. Contract Engine MCP: at least `validate_spec` and `get_contract` tools callable
3. Codebase Intelligence MCP: at least `find_definition` and `register_artifact` tools callable
4. Gate: ALL smoke tests pass (already verified in M2, but re-checked in context)

**R4-M4-003: Phase 3 — Architect decomposition**

1. Feed sample PRD to Architect via `super-orchestrator run --prd sample_prd.md` or direct MCP call
2. Receive `ServiceMap` with 3 services (auth-service, order-service, notification-service)
3. Receive `DomainModel` with entities (User, Order, Notification)
4. Receive `ContractStubs` (at least auth-api, order-api contract definitions)
5. Gate: Valid ServiceMap with >= 3 services AND DomainModel with >= 3 entities

**R4-M4-004: Phase 4 — Contract registration**

1. Register contract stubs with Contract Engine via `create_contract()` MCP calls
2. Validate all contracts with `validate_spec()` — all return `{valid: true}`
3. Verify retrieval with `list_contracts()` — all 3+ contracts present
4. Gate: ALL contracts registered AND valid

**R4-M4-005: Phase 5 — Parallel builder execution**

1. Launch 3 Builder subprocesses (one per service from ServiceMap)
2. Each Builder runs the full agent-team pipeline with contract-aware config
3. Each Builder writes STATE.json with `summary` dict
4. Collect `BuilderResult` per service
5. Gate: >= 2 of 3 builders succeed (partial success acceptable)

**R4-M4-006: Phase 6 — Integration + Deployment**

1. Build 3's `ComposeGenerator` generates `docker-compose.generated.yml` from builder outputs
2. `DockerOrchestrator` runs `docker compose up -d` with merged compose files
3. Health check all services (Build 1 + generated) via `ServiceDiscovery.wait_all_healthy()`
4. Run contract compliance (Schemathesis against live services, if service has OpenAPI spec)
5. Run cross-service integration tests (flow tests: register -> login -> create order -> notification)
6. Gate: All services healthy AND > 70% contract compliance

**R4-M4-007: Phase 7 — Quality Gate**

1. Layer 1 (per-service): Evaluate `BuilderResult` per service (test pass rate, convergence)
2. Layer 2 (contract compliance): Evaluate `IntegrationReport` contract test results
3. Layer 3 (system-level): Run security, CORS, logging, secrets, Docker, health scans
4. Layer 4 (adversarial): Dead events, dead contracts, orphan services, naming consistency
5. Gate: `overall_verdict != "failed"`

**R4-M4-008: Planted violation detection**

Include a deliberate violation in the test setup:
- One service missing `/health` endpoint (HEALTH-001)
- One endpoint returning a field not in the OpenAPI contract (SCHEMA-001)
- One `print()` statement instead of logger (LOG-001)
- Verify all 3 appear in the Quality Gate report

---

### Milestone 5: Fix Pass + Defect Remediation

**ID**: run4-m5
**Dependencies**: run4-m4
**Duration**: 1-2 hours
**Purpose**: Catalog all defects from M2-M4, classify by priority, apply fix passes, track convergence, and verify no regressions.

#### Requirements

**R4-M5-001: Issue cataloging**

Scan all M2-M4 results and produce a defect catalog:

```python
@dataclass
class Finding:
    finding_id: str          # FINDING-001, FINDING-002, etc.
    priority: str            # P0, P1, P2, P3
    system: str              # Build 1, Build 2, Build 3, Integration
    component: str           # Specific module or function
    evidence: str            # Exact reproduction or test output
    recommendation: str      # Specific fix action
    resolution: str = ""     # FIXED, OPEN, WONTFIX
    fix_pass_number: int = 0 # Which pass fixed it
    fix_verification: str = "" # Test ID confirming fix
```

**R4-M5-002: Priority classification**

Apply decision tree (from RUN4_TECH_AUDIT_SCORING.md Section 3.2):

| Priority | Criteria | Action |
|---|---|---|
| P0 | System cannot start/deploy, blocks everything | Must fix before proceeding |
| P1 | Primary use case fails, no workaround | Must fix in current pass |
| P2 | Secondary feature broken | Fix if time permits |
| P3 | Cosmetic/performance/docs | Document only |

**R4-M5-003: Fix pass execution**

For each fix pass (up to `config.max_fix_passes`):

1. **Discover**: Run all scans, collect all violations
2. **Classify**: Apply P0-P3 classification
3. **Generate fix**: Write `FIX_INSTRUCTIONS.md` targeting P0 first, then P1
4. **Apply**: Invoke builder in quick mode OR direct file edit for infrastructure fixes
5. **Verify**: Re-run the specific scan that found the violation
6. **Regress**: Run full scan set, compare before/after snapshots

**R4-M5-004: Fix pass metrics tracking**

Per pass, track:

| Metric | Formula |
|---|---|
| Fix effectiveness | fixes_resolved / fixes_attempted |
| Regression rate | new_violations_after_fix / total_fixes_applied |
| New defect discovery rate | new_defects_this_pass |
| Score delta | score_after - score_before |

**R4-M5-005: Convergence criteria (when to stop)**

**Hard stop (any one triggers):**
- P0 count = 0 AND P1 count = 0
- `max_fix_passes` reached
- Budget exhausted
- Fix effectiveness < 30% for 2 consecutive passes
- Regression rate > 25% for 2 consecutive passes

**Soft convergence (declare "good enough"):**
- P0 count = 0
- P1 count <= 2 (with documented workarounds)
- New defect discovery rate < 3 per pass for 2 consecutive passes
- Aggregate score >= 70

**R4-M5-006: Regression detection**

After each fix pass:
1. Save violation snapshot (all scan codes + file paths)
2. Apply fixes
3. Run full scan
4. Compare: any violation that was fixed but reappeared = REGRESSION
5. Any test that was passing but now fails = REGRESSION
6. Regressions count against fix effectiveness

---

### Milestone 6: Audit Report + Final Verification

**ID**: run4-m6
**Dependencies**: run4-m5
**Duration**: 30-60 minutes
**Purpose**: Compute per-system and aggregate scores, generate the final SUPER_TEAM_AUDIT_REPORT.md, and produce all appendices.

#### Requirements

**R4-M6-001: Per-system scoring**

Compute scores for Build 1, Build 2, Build 3 using the rubric in Section 6.

**R4-M6-002: Integration scoring**

Compute integration score based on MCP connectivity, data flow integrity, contract fidelity, and pipeline completion (Section 6.2).

**R4-M6-003: Aggregate score**

```
aggregate = (build1_score * 0.30) + (build2_score * 0.25) + (build3_score * 0.25)
          + (integration_score * 0.20)
```

**R4-M6-004: SUPER_TEAM_AUDIT_REPORT.md generation**

Write to `.super-orchestrator/SUPER_TEAM_AUDIT_REPORT.md` with structure:

1. Executive Summary (scores, verdict, fix pass count, defect totals)
2. Methodology (coverage + risk-based hybrid)
3. Per-System Assessment (Build 1, Build 2, Build 3)
4. Integration Assessment (MCP, data flows, dark corners)
5. Fix Pass History (per-pass metrics, convergence chart)
6. Gap Analysis (RTM summary, untested paths, known limitations)
7. Appendices (A: RTM, B: Violations, C: Test results, D: Cost breakdown)

**R4-M6-005: Requirements Traceability Matrix (RTM)**

For each REQ-xxx across all 3 Build PRDs:
- Implementation file(s)
- Test ID(s)
- Test status (PASS/FAIL/UNTESTED)
- Verification status (Verified/Gap)

**R4-M6-006: Interface Coverage Matrix**

For each of the 20 MCP tools:
- Valid request tested (YES/NO)
- Error request tested (YES/NO)
- Response parseable (YES/NO)
- Status (GREEN/YELLOW/RED)

Target: 100% valid request coverage, >= 80% error coverage.

**R4-M6-007: Data Flow Path Coverage**

For each of the 10 primary data flows and 7 error paths:
- Tested (YES/NO)
- Status
- Evidence (test ID or trace)

**R4-M6-008: Dark corners catalog**

Explicitly test and document:
- MCP server startup race condition (3 servers starting simultaneously)
- Docker network DNS resolution (service-to-service by hostname)
- Concurrent builder file conflicts (2 builders targeting same CI index)
- State machine resume after crash (kill pipeline mid-build, resume)
- Large PRD handling (if time permits)

**R4-M6-009: Cost breakdown**

| Phase | Cost | Duration |
|---|---|---|
| M1: Infrastructure | $X.XX | Nm |
| M2: B1->B2 Wiring | $X.XX | Nm |
| M3: B2->B3 Wiring | $X.XX | Nm |
| M4: E2E Pipeline | $X.XX | Nm |
| M5: Fix Passes | $X.XX | Nm |
| M6: Audit | $X.XX | Nm |
| **Total** | **$X.XX** | **Nh Nm** |

---

## 4. Verification Test Matrix

### 4.1 Run 4 Success Criteria Tests

| ID | Test | Assertion | Phase | Priority |
|---|---|---|---|---|
| SC-01 | `test_full_pipeline_no_intervention` | Pipeline reaches "complete" state | M4 | P0 |
| SC-02 | `test_app_deployment` | 3 services in `docker compose ps` | M4 | P0 |
| SC-03 | `test_health_checks` | HTTP 200 on /health for all services | M4 | P0 |
| SC-04 | `test_integration_tests` | `overall_health != "failed"` | M4 | P0 |
| SC-05 | `test_contract_violation_detection` | Planted violation in report | M4 | P0 |
| SC-06 | `test_codebase_indexing` | `total_symbols > 0` | M4 | P0 |
| SC-07 | `test_mcp_queries` | `find_definition("User")` returns result | M2 | P0 |
| SC-08 | `test_pipeline_duration` | `total_duration < 21600` (6h) | M4 | P1 |

### 4.2 Build 1 Verification Tests

| ID | Test | Expected | Priority |
|---|---|---|---|
| B1-01 | `test_build1_deploy` | All 3 services in compose | P0 |
| B1-02 | `test_build1_health` | HTTP 200 on /api/health x3 | P0 |
| B1-03 | `test_architect_decompose` | ServiceMap with >= 1 service | P0 |
| B1-04 | `test_contract_validation` | `validate_spec()` -> `{valid: true}` | P0 |
| B1-05 | `test_contract_test_gen` | Non-empty test code string | P1 |
| B1-06 | `test_codebase_indexing_perf` | < 60s for 50K LOC | P2 |
| B1-07 | `test_mcp_tool_responses` | 20 tools return non-error | P0 |
| B1-08 | `test_dead_code_detection` | Planted dead code found | P1 |
| B1-09 | `test_mcp_handshake_architect` | Capabilities include `tools` | P0 |
| B1-10 | `test_mcp_handshake_contract` | Capabilities include `tools` | P0 |
| B1-11 | `test_mcp_handshake_codebase` | Capabilities include `tools` | P0 |
| B1-12 | `test_tool_count_architect` | Exactly 4 tools | P0 |
| B1-13 | `test_tool_count_contract` | Exactly 9 tools | P0 |
| B1-14 | `test_tool_count_codebase` | Exactly 7 tools | P0 |
| B1-15 | `test_invalid_tool_input` | `isError = True`, no crash | P0 |
| B1-16 | `test_nonexistent_tool` | Error response, no crash | P1 |
| B1-17 | `test_server_crash_recovery` | Client detects, recovers | P0 |
| B1-18 | `test_multi_server_simultaneous` | No resource conflicts | P0 |
| B1-19 | `test_architect_cross_ref` | get_contracts_for_service returns data | P1 |
| B1-20 | `test_inter_container_dns` | Architect reaches Contract Engine by hostname | P1 |

### 4.3 Build 2 Verification Tests

| ID | Test | Expected | Priority |
|---|---|---|---|
| B2-01 | `test_contract_client_all_methods` | All 6 return correct types | P0 |
| B2-02 | `test_codebase_client_all_methods` | All 7 return correct types | P0 |
| B2-03 | `test_mcp_safe_defaults` | All methods return safe defaults on error | P0 |
| B2-04 | `test_contract_scan_detection` | Planted violation found | P0 |
| B2-05 | `test_parallel_builders` | Both complete, no conflicts | P1 |
| B2-06 | `test_artifact_registration` | `register_artifact()` -> indexed=True | P1 |
| B2-07 | `test_fallback_contract_engine` | Static scan runs when MCP unavailable | P0 |
| B2-08 | `test_fallback_codebase_intel` | Static map generated when MCP unavailable | P0 |
| B2-09 | `test_backward_compat` | All B2 features disabled = v14.0 behavior | P1 |
| B2-10 | `test_retry_exponential_backoff` | 3 retries with 1s, 2s, 4s delays | P1 |

### 4.4 Build 3 Verification Tests

| ID | Test | Expected | Priority |
|---|---|---|---|
| B3-01 | `test_pipeline_e2e` | All phases complete | P0 |
| B3-02 | `test_deploy_and_health` | 3/3 healthy | P0 |
| B3-03 | `test_schemathesis_violations` | Contract violations detected | P1 |
| B3-04 | `test_gate_layer_order` | L1 before L2 before L3 before L4 | P0 |
| B3-05 | `test_cli_commands` | All commands registered | P1 |
| B3-06 | `test_compose_generation` | Valid docker-compose.yml produced | P0 |
| B3-07 | `test_traefik_routing` | PathPrefix labels route correctly | P1 |
| B3-08 | `test_state_persistence` | Save/load roundtrip preserves all fields | P0 |
| B3-09 | `test_graceful_shutdown` | State saved on SIGINT | P1 |
| B3-10 | `test_budget_tracking` | Cost accumulated across phases | P2 |

### 4.5 Cross-Build Integration Tests

| ID | Test | Builds | Priority |
|---|---|---|---|
| X-01 | `test_mcp_b1_to_b2_contract_engine` | B1, B2 | P0 |
| X-02 | `test_mcp_b1_to_b2_codebase_intel` | B1, B2 | P0 |
| X-03 | `test_mcp_b1_to_b3_architect` | B1, B3 | P0 |
| X-04 | `test_subprocess_b3_to_b2` | B2, B3 | P0 |
| X-05 | `test_state_json_contract` | B2, B3 | P0 |
| X-06 | `test_config_generation_compat` | B2, B3 | P0 |
| X-07 | `test_fix_instructions_consumed` | B2, B3 | P1 |
| X-08 | `test_docker_compose_merge` | B1, B3 | P1 |
| X-09 | `test_quality_gate_l1_builder_result` | B2, B3 | P1 |
| X-10 | `test_quality_gate_l3_generated_code` | B2, B3 | P1 |

### 4.6 Summary

| Category | Total Tests | P0 | P1 | P2 |
|---|---|---|---|---|
| Success Criteria (SC) | 8 | 7 | 1 | 0 |
| Build 1 (B1) | 20 | 14 | 5 | 1 |
| Build 2 (B2) | 10 | 6 | 4 | 0 |
| Build 3 (B3) | 10 | 5 | 4 | 1 |
| Cross-Build (X) | 10 | 6 | 4 | 0 |
| **Total** | **58** | **38** | **18** | **2** |

---

## 5. Fix Pass Methodology

### 5.1 Fix Pass Procedure

```
1. DISCOVER
   Run all scans (mock data, UI compliance, API contract, database, E2E quality,
   deployment, asset, MCP tool health, contract compliance)
   Output: Violation list with {code, severity, file, line, message}

2. CLASSIFY
   For each violation, apply decision tree:
   - System cannot start? -> P0
   - Primary use case fails, no workaround? -> P0
   - Primary use case fails, workaround exists? -> P1
   - Secondary feature fails, affects integration? -> P1
   - Secondary feature fails, no integration impact? -> P2
   - Cosmetic/performance/docs? -> P3

3. GENERATE FIX
   Write FIX_INSTRUCTIONS.md with:
   - P0 fixes first (MUST FIX)
   - P1 fixes second (SHOULD FIX)
   - P2 fixes only if P0+P1 count < 5
   - Never include P3

4. APPLY
   - Infrastructure fixes (Docker, Traefik, compose): direct file edit
   - Build 1 code fixes: direct edit in Build 1 project
   - Build 2 code fixes: invoke builder in quick mode
   - Build 3 code fixes: direct edit in Build 3 project

5. VERIFY
   Re-run the specific scan that found each targeted violation
   Record: fixed / not fixed / new issue introduced

6. REGRESS
   Run full scan set, compare before/after
   Flag any violation that was previously absent = regression
   Flag any previously-passing test that now fails = regression
```

### 5.2 Fix Effectiveness Tracking

| Fix Pass | Targeted | Resolved | Failed | Regressions | Effectiveness | Score Delta |
|---|---|---|---|---|---|---|
| 1 | ? | ? | ? | ? | ?% | +? |
| 2 | ? | ? | ? | ? | ?% | +? |
| ... | | | | | | |

### 5.3 Convergence Formula

```
convergence = 1.0 - (remaining_p0 * 0.4 + remaining_p1 * 0.3 + remaining_p2 * 0.1) / initial_total_weighted
```

When convergence >= 0.85, declare "converged enough."

---

## 6. Audit Scoring Rubric

### 6.1 Per-System Scoring (Build 1, Build 2, Build 3)

Each system scored out of 100:

| Category | Weight | Metric | Scoring |
|---|---|---|---|
| **Functional Completeness** | 30% | REQ-xxx pass rate | Linear: 0% = 0, 100% = 30 |
| **Test Health** | 20% | Test pass rate | Linear: 0% = 0, 100% = 20 |
| **Contract Compliance** | 20% | Schema validation pass rate | Linear: 0% = 0, 100% = 20 |
| **Code Quality** | 15% | Violation density (per KLOC) | Inverse: 0 = 15, > 10 = 0 |
| **Docker Health** | 10% | Health check pass rate | Linear: 0% = 0, 100% = 10 |
| **Documentation** | 5% | Required artifacts present | Binary per artifact |

**Formula:**
```
system_score = (req_pass_rate * 30) + (test_pass_rate * 20) + (contract_pass_rate * 20)
             + (max(0, 15 - violation_density * 1.5)) + (health_check_rate * 10)
             + (artifacts_present / artifacts_required * 5)
```

### 6.2 Integration Scoring

| Category | Weight | Metric |
|---|---|---|
| **MCP Connectivity** | 25% | MCP tools responding correctly (binary per tool) |
| **Data Flow Integrity** | 25% | End-to-end flows completing (pass/fail per flow) |
| **Contract Fidelity** | 25% | Cross-build contract violations (inverse) |
| **Pipeline Completion** | 25% | Super Orchestrator phases completing (% done) |

**Formula:**
```
integration_score = (mcp_tools_ok / mcp_tools_total * 25)
                  + (flows_passing / flows_total * 25)
                  + (max(0, 25 - cross_build_violations * 2.5))
                  + (phases_complete / phases_total * 25)
```

### 6.3 Aggregate Score

```
aggregate = (build1_score * 0.30) + (build2_score * 0.25) + (build3_score * 0.25)
          + (integration_score * 0.20)
```

**Weights rationale:**
- Build 1 gets 30% — foundation everything depends on
- Build 2 and Build 3 get 25% each — equally critical but independent
- Integration gets 20% — the "glue" quality

### 6.4 Traffic Light Classification

| Color | Score Range | Meaning | Action |
|---|---|---|---|
| **GREEN** | 80-100 | Production-ready or close | Document gaps, ship |
| **YELLOW** | 50-79 | Works but significant gaps | One more fix pass recommended |
| **RED** | 0-49 | Critical failures | Targeted rework needed |

### 6.5 "Good Enough" Thresholds

| Criterion | Minimum Acceptable | Target | Stretch |
|---|---|---|---|
| Per-system score | 60 (YELLOW) | 80 (GREEN) | 90 |
| Integration score | 50 | 75 | 90 |
| Aggregate score | 65 | 80 | 90 |
| P0 remaining | 0 (hard) | 0 | 0 |
| P1 remaining | <= 3 | 0 | 0 |
| Test pass rate | >= 85% | >= 95% | 100% |
| MCP tool coverage | >= 90% | 100% | 100% + errors |
| Fix convergence | >= 0.70 | >= 0.85 | >= 0.95 |

---

## 7. State Persistence for Resume

### 7.1 Run4State JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["run_id", "schema_version", "current_milestone", "current_phase"],
  "properties": {
    "run_id": { "type": "string", "format": "uuid" },
    "schema_version": { "type": "integer", "const": 1 },
    "started_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "current_milestone": { "type": "integer", "minimum": 0, "maximum": 6 },
    "current_phase": { "type": "string" },
    "completed_milestones": {
      "type": "array",
      "items": { "type": "integer" }
    },
    "milestone_artifacts": {
      "type": "object",
      "additionalProperties": true
    },
    "mcp_health": {
      "type": "object",
      "properties": {
        "architect": { "$ref": "#/definitions/health_result" },
        "contract-engine": { "$ref": "#/definitions/health_result" },
        "codebase-intelligence": { "$ref": "#/definitions/health_result" }
      }
    },
    "mcp_tool_results": { "type": "object" },
    "b1_b2_wiring_passed": { "type": "boolean" },
    "builder_invocation_passed": { "type": "boolean" },
    "state_json_parsing_passed": { "type": "boolean" },
    "config_generation_passed": { "type": "boolean" },
    "b2_b3_wiring_passed": { "type": "boolean" },
    "pipeline_completed": { "type": "boolean" },
    "services_deployed": {
      "type": "array",
      "items": { "type": "string" }
    },
    "services_healthy": {
      "type": "array",
      "items": { "type": "string" }
    },
    "integration_report": { "type": "object" },
    "quality_gate_report": { "type": "object" },
    "defect_catalog": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["finding_id", "priority", "system", "component"],
        "properties": {
          "finding_id": { "type": "string", "pattern": "^FINDING-\\d{3}$" },
          "priority": { "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
          "system": { "type": "string" },
          "component": { "type": "string" },
          "evidence": { "type": "string" },
          "recommendation": { "type": "string" },
          "resolution": { "type": "string", "enum": ["", "FIXED", "OPEN", "WONTFIX"] },
          "fix_pass_number": { "type": "integer" },
          "fix_verification": { "type": "string" }
        }
      }
    },
    "fix_passes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "pass_number": { "type": "integer" },
          "targeted": { "type": "integer" },
          "resolved": { "type": "integer" },
          "failed": { "type": "integer" },
          "regressions": { "type": "integer" },
          "effectiveness": { "type": "number" },
          "score_before": { "type": "number" },
          "score_after": { "type": "number" },
          "cost": { "type": "number" }
        }
      }
    },
    "total_fix_passes": { "type": "integer" },
    "convergence_score": { "type": "number" },
    "audit_report_path": { "type": "string" },
    "per_system_scores": {
      "type": "object",
      "properties": {
        "build1": { "type": "number" },
        "build2": { "type": "number" },
        "build3": { "type": "number" }
      }
    },
    "integration_score": { "type": "number" },
    "aggregate_score": { "type": "number" },
    "total_cost": { "type": "number" },
    "phase_costs": { "type": "object" }
  },
  "definitions": {
    "health_result": {
      "type": "object",
      "properties": {
        "status": { "type": "string", "enum": ["healthy", "unhealthy"] },
        "tools_count": { "type": "integer" },
        "tool_names": { "type": "array", "items": { "type": "string" } },
        "error": { "type": "string" }
      }
    }
  }
}
```

### 7.2 Checkpoint Strategy

State is saved after:
1. Each milestone completion (milestone_artifacts updated, completed_milestones appended)
2. Each fix pass completion (fix_passes appended, scores updated)
3. Each phase within a milestone (current_phase updated)
4. Emergency save on SIGINT/SIGTERM (interrupted flag set)

### 7.3 Resume Logic

```python
def resume_run4(config: Run4Config) -> None:
    state = Run4State.load(config.output_dir)
    if state is None:
        # Fresh start
        state = Run4State(run_id=str(uuid4()), started_at=now_iso())
        start_milestone = 1
    else:
        start_milestone = state.current_milestone
        if state.current_milestone in state.completed_milestones:
            start_milestone = state.current_milestone + 1

    milestones = [
        (1, run_m1_infrastructure),
        (2, run_m2_b1_b2_wiring),
        (3, run_m3_b2_b3_wiring),
        (4, run_m4_e2e_pipeline),
        (5, run_m5_fix_pass),
        (6, run_m6_audit),
    ]

    for milestone_num, executor in milestones:
        if milestone_num < start_milestone:
            continue
        state.current_milestone = milestone_num
        state.save(config.output_dir)
        try:
            executor(state, config)
            state.completed_milestones.append(milestone_num)
            state.save(config.output_dir)
        except Exception:
            state.save(config.output_dir)
            raise
```

### 7.4 State File Location

```
.run4/
    RUN4_STATE.json          # Main state file
    RUN4_STATE.json.tmp      # Atomic write temp file
    m2_mcp_results.json      # Detailed M2 tool results
    m4_builder_outputs/      # Builder output directories
        auth-service/
        order-service/
        notification-service/
    m5_fix_snapshots/        # Pre/post fix violation snapshots
        fix_pass_1_before.json
        fix_pass_1_after.json
    SUPER_TEAM_AUDIT_REPORT.md
```

---

## 8. Docker Compose Topology

### 8.1 Full-System Network Architecture

```
                         HOST (Port 80, 8080)
                              |
                    +-------- | ----------+
                    |     FRONTEND NET    |
                    |                     |
                    |  +--------------+   |
                    |  |   TRAEFIK    |   |
                    |  |  (gateway)   |   |
                    |  +--+---+---+---+   |
                    |     |   |   |       |
                    |  +--+   |   +--+    |
                    |  |arch| | |c-e|    |
                    |  +--+-+ | +-+--+    |
                    |     |   |   |       |
                    |  +--+   |   +--+    |
                    |  |cbi|  | |auth|   |
                    |  +--+-+ | +-+--+    |
                    |     |   |   |       |
                    |  +--+-+ |  ++--+    |
                    |  |ord|  |  |ntf|    |
                    |  +--+-+ |  +-+--+   |
                    +----+----+----+------+
                         |    |    |
                    +----+----+----+------+
                    |     BACKEND NET     |
                    |  (internal: true)   |
                    |                     |
                    |  +--------------+   |
                    |  |  POSTGRES    |   |
                    |  |  (5432)      |   |
                    |  +--------------+   |
                    |  +--------------+   |
                    |  |    REDIS     |   |
                    |  |  (6379)      |   |
                    |  +--------------+   |
                    +---------------------+
```

**Legend:**
- arch = architect (Build 1)
- c-e = contract-engine (Build 1)
- cbi = codebase-intelligence (Build 1)
- auth = auth-service (generated by Build 2)
- ord = order-service (generated by Build 2)
- ntf = notification-service (generated by Build 2)

### 8.2 Compose File Structure

```
docker/
    docker-compose.infra.yml        # Tier 0: postgres, redis
    docker-compose.build1.yml       # Tier 1: architect, contract-engine, codebase-intel
    docker-compose.traefik.yml      # Tier 2: Traefik gateway
    docker-compose.generated.yml    # Tier 3: Generated services (by ComposeGenerator)
    docker-compose.run4.yml         # Run 4: cross-build wiring overrides
    docker-compose.test.yml         # Test: ephemeral volumes, random ports
    traefik/
        traefik.yml                 # Static Traefik config
```

### 8.3 docker-compose.infra.yml

```yaml
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

### 8.4 docker-compose.build1.yml

```yaml
services:
  architect:
    build:
      context: ../src/architect
      dockerfile: ../../docker/architect/Dockerfile
    environment:
      DATABASE_PATH: /data/architect.db
      CONTRACT_ENGINE_URL: http://contract-engine:8000
      CODEBASE_INTEL_URL: http://codebase-intelligence:8000
      LOG_LEVEL: ${LOG_LEVEL:-info}
    volumes:
      - architect-data:/data
    depends_on:
      contract-engine:
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
      context: ../src/contract_engine
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
      context: ../src/codebase_intelligence
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
      contract-engine:
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

### 8.5 docker-compose.traefik.yml

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

### 8.6 docker-compose.run4.yml (Cross-Build Wiring)

```yaml
services:
  architect:
    environment:
      LOG_LEVEL: debug
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

### 8.7 Startup Command

```bash
docker compose \
  -p super-team-run4 \
  -f docker/docker-compose.infra.yml \
  -f docker/docker-compose.build1.yml \
  -f docker/docker-compose.generated.yml \
  -f docker/docker-compose.traefik.yml \
  -f docker/docker-compose.run4.yml \
  up -d --wait
```

### 8.8 Resource Budget

| Component | RAM | CPU |
|---|---|---|
| 3 Build 1 services | 512M + 512M + 1G = 2G | 2.0 cores |
| Postgres + Redis | 512M + 128M = 640M | 0.5 cores |
| Traefik | 128M | 0.25 cores |
| 3 generated services | 3 x 512M = 1.5G | 1.5 cores |
| **Total** | **~4.3G** | **~4.25 cores** |

### 8.9 Health Check Cascade (Dependency Order)

```
Tier 0: postgres, redis
    |
    v (service_healthy)
Tier 1: contract-engine
    |
    v (service_healthy)
Tier 2: architect, codebase-intelligence
    |
    v (service_healthy)
Tier 3: generated services (auth, order, notification)
    |
    v (service_healthy)
Tier 4: traefik
```

### 8.10 Port Assignments

| Service | Internal Port | External Port | Protocol |
|---|---|---|---|
| architect | 8000 | 8001 | HTTP |
| contract-engine | 8000 | 8002 | HTTP |
| codebase-intelligence | 8000 | 8003 | HTTP |
| postgres | 5432 | 5432 | TCP |
| redis | 6379 | 6379 | TCP |
| traefik (HTTP) | 80 | 80 | HTTP |
| traefik (API) | 8080 | 8080 | HTTP |
| auth-service | 8080 | dynamic | HTTP |
| order-service | 8080 | dynamic | HTTP |
| notification-service | 8080 | dynamic | HTTP |

---

## 9. Risk Assessment and Mitigations

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| ChromaDB first-download timeout | Medium | Codebase Intelligence MCP fails to start | Set `mcp_first_start_timeout_ms: 120000`, or pre-download in Docker build |
| Architect HTTP call to Contract Engine fails | Medium | `get_contracts_for_service` returns empty | Ensure Docker Compose is up before MCP testing; Contract Engine FastAPI must be running |
| SQLite WAL lock contention | Low | Concurrent reads/writes between FastAPI and MCP | WAL mode handles this; verify with load test |
| Windows process management | Medium | Orphan MCP server processes | Use `process.terminate()` + `process.kill()` with timeout in cleanup |
| MCP SDK version mismatch | Low | Protocol incompatibility | Pin `mcp>=1.25,<2` in both Build 1 and Build 2 |
| Nested asyncio.run() | High | RuntimeError when Build 3 calls Build 2 | Use `asyncio.create_subprocess_exec` for builder invocation (subprocess isolation) |
| Docker Compose v1 vs v2 | Medium | `docker-compose` not found | Use `docker compose` (v2 syntax), document requirement |
| Builder timeout on large PRD | Medium | 30-minute default may not suffice | Configure `builder_timeout_s: 3600` for initial runs, tune down |

### 9.2 Schedule Risks

| Risk | Mitigation |
|---|---|
| Build 1/2/3 not complete when Run 4 starts | Run 4 M1 (infrastructure) can proceed independently; M2+ needs outputs |
| Fix passes take longer than expected | Time-box last fix pass; downgrade remaining P1s after 3 attempts |
| Docker environment not available | Fall back to subprocess-only testing (skip Docker-dependent tests) |

### 9.3 Quality Risks

| Risk | Mitigation |
|---|---|
| False GREEN (audit reports everything passing but edge cases untested) | Require dark corner testing (Section 4.4); cap score at 85 if dark corners untested |
| Fix pass introduces more regressions than it fixes | Track regression rate; stop if > 25% for 2 consecutive passes |
| Test fixtures don't exercise real integration patterns | Use a realistic 3-service app (not trivial hello-world) |
| Planted violations too easy to detect (don't test real scanner coverage) | Include subtle violations: e.g., optional field present but wrong type, not just missing field |

### 9.4 Decision Points

| Decision | Trigger | Options |
|---|---|---|
| Skip Docker testing | Docker not available on CI | Run subprocess tests only, document gap |
| Reduce builder parallelism | OOM on test machine | Set `max_concurrent_builders: 1` |
| Extend fix passes | Convergence score < 0.70 after 3 passes | Increase `max_fix_passes` to 7 |
| Declare remaining gaps | P1 defect survives 3 fix attempts | Downgrade to P2, document workaround |
| Skip adversarial layer | Layer 4 scanner has > 50% false positive rate | Set `layer4_enabled: false`, document |
