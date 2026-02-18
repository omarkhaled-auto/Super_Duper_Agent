# Run 4: End-to-End Integration, Verification & Audit

> **Version**: 1.0
> **Date**: 2026-02-15
> **Type**: Verification + Remediation Run (NOT a build)
> **Estimated LOC**: ~5K (fixes, test infrastructure, audit tooling)
> **Estimated Cost**: $36-66
> **Estimated Duration**: 5-9 hours
> **Input**: Build 1 (Architect + Contract Engine + Codebase Intelligence), Build 2 (Builder Fleet v14.0), Build 3 (Integrator + Quality Gate + Super Orchestrator)
> **Output**: SUPER_TEAM_AUDIT_REPORT.md + verified end-to-end pipeline

---

## Project Overview

Run 4 wires the three independently-built systems of the Super Agent Team together, verifies every integration point, catalogs every defect, applies convergence-based fix passes, and produces the final audit report.

### The Three Systems Being Wired

| System | Build | Components | Interface Type |
|--------|-------|------------|---------------|
| Foundation Services | Build 1 | Architect MCP (4 tools), Contract Engine MCP (9 tools), Codebase Intelligence MCP (7 tools) | MCP stdio, HTTP REST |
| Builder Fleet | Build 2 | agent-team v14.0 with ContractEngineClient, CodebaseIntelligenceClient, ArchitectClient, Agent Teams backend | MCP clients, subprocess CLI |
| Orchestration Layer | Build 3 | Super Orchestrator (state machine), Integrator (Docker Compose), Quality Gate (4 layers), CLI | Subprocess, Docker, HTTP |

### Success Criteria

| ID | Criterion | Type | Pass Condition |
|---|---|---|---|
| SC-01 | Complete pipeline runs end-to-end without human intervention | Binary | Pipeline state reaches "complete" |
| SC-02 | 3-service test app deploys with all health checks passing | Binary | All 3 services "healthy" in `docker compose ps` |
| SC-03 | Integration tests pass | Binary | `integration_report.overall_health != "failed"` |
| SC-04 | Contract violations are detected and reported | Binary | Planted violation appears in QUALITY_GATE_REPORT.md |
| SC-05 | Codebase Intelligence indexes generated code | Binary | `index_stats.total_symbols > 0` after builder completes |
| SC-06 | Codebase Intelligence responds to MCP queries | Binary | `find_definition("User")` returns file/line result |
| SC-07 | Total time under 6 hours for 3-service app | Graduated | GREEN: <6h, YELLOW: 6-10h, RED: >10h |

### 3-Service Test Application: TaskTracker

A minimal task/order tracking system exercising all integration points:

- **auth-service** (Python/FastAPI): POST /register, POST /login, GET /users/me, GET /health
- **order-service** (Python/FastAPI): POST /orders, GET /orders/:id, PUT /orders/:id, GET /health — validates JWT from auth-service
- **notification-service** (Python/FastAPI): POST /notify, GET /notifications, GET /health — consumes OrderCreated/OrderShipped events

**Contracts**: auth-api (OpenAPI 3.1), order-api (OpenAPI 3.1), order-events (AsyncAPI 3.0)

**Data Flows**:
1. User registers → auth-service → {id, email, created_at}
2. User logs in → auth-service → {access_token, refresh_token}
3. Create order (JWT) → order-service → {id, status, items, total}
4. Order created event → notification-service → {order_id, user_id, items, total}
5. Send notification → notification-service → {user_id, type, message}

---

## Technology Stack

| Component | Choice | Justification |
|-----------|--------|---------------|
| Test Framework | pytest + pytest-asyncio | Standard Python testing, async support for MCP/HTTP |
| HTTP Client | httpx (async) | Multi-service health polling, integration tests |
| Docker Testing | Testcontainers (Python) | Compose management from pytest, cleanup, port mapping |
| MCP Client | mcp SDK (Python, >=1.25) | Native MCP stdio transport for tool calls |
| Contract Testing | Schemathesis + Pact | Property-based OpenAPI testing + consumer-driven contracts |
| Process Management | asyncio.create_subprocess_exec | Builder subprocess invocation with timeout |
| State Persistence | JSON (atomic write via tmp+rename) | Resume support, crash recovery |
| API Gateway | Traefik v3.6 | Docker auto-discovery, PathPrefix routing |
| Database | PostgreSQL 16 | Shared DB for generated services |
| Cache | Redis 7 | Optional cache layer |

---

## Config.yaml Template

> **Note**: The `run4:` section below contains Run4-specific configuration fields that are NOT part of the standard `AgentTeamConfig` schema. These fields are intentionally outside AgentTeamConfig — they will be parsed by Run4's own `Run4Config` dataclass (REQ-001). The agent-team builder only uses the `depth`, `milestone`, `post_orchestration_scans`, and `e2e_testing` sections. `_dict_to_config()` silently ignores unknown top-level keys.

```yaml
depth: thorough

run4:
  build1_project_root: "C:/Projects/super-team"
  build2_project_root: "C:/Projects/agent-team-v15"
  build3_project_root: "C:/Projects/super-team"
  output_dir: ".run4"
  compose_project_name: "super-team-run4"
  docker_compose_files:
    - "docker/docker-compose.infra.yml"
    - "docker/docker-compose.build1.yml"
    - "docker/docker-compose.traefik.yml"
  health_check_timeout_s: 120
  health_check_interval_s: 3.0
  mcp_startup_timeout_ms: 30000
  mcp_tool_timeout_ms: 60000
  mcp_first_start_timeout_ms: 120000
  max_concurrent_builders: 3
  builder_timeout_s: 1800
  builder_depth: "thorough"
  max_fix_passes: 5
  fix_effectiveness_floor: 0.30
  regression_rate_ceiling: 0.25
  max_budget_usd: 100.0
  sample_prd_path: "tests/run4/fixtures/sample_prd.md"

milestone:
  enabled: true
  health_gate: true
  review_recovery_retries: 2

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false
  api_contract_scan: true

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 3
```

---

## Milestone Structure

## Milestone 1: Test Infrastructure + Fixtures

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Establish the test framework, sample app fixtures, mock MCP servers, Run4Config, Run4State persistence, and shared test utilities that all subsequent milestones depend on.

### Requirements

- [ ] REQ-001: Create Run4Config dataclass with all configuration fields (build paths, Docker settings, MCP timeouts, builder settings, fix pass limits, max_budget_usd: float = 100.0) (review_cycles: 0)
- [ ] REQ-002: Create Run4State dataclass with milestone tracking, MCP health results, builder results, defect catalog, fix pass metrics, audit scores, cost tracking, and schema_version field (review_cycles: 0)
- [ ] REQ-003: Implement Run4State.save() with atomic write (write .tmp then os.replace) and Run4State.load() with schema_version validation (review_cycles: 0)
- [ ] REQ-004: Create sample TaskTracker PRD at tests/run4/fixtures/sample_prd.md — 3-service app with auth-service, order-service, notification-service, all Python/FastAPI (review_cycles: 0)
- [ ] REQ-005: Create sample OpenAPI 3.1 spec for auth-service at tests/run4/fixtures/sample_openapi_auth.yaml — 3 endpoints (register, login, users/me) with full request/response schemas (review_cycles: 0)
- [ ] REQ-006: Create sample OpenAPI 3.1 spec for order-service at tests/run4/fixtures/sample_openapi_order.yaml — 3 endpoints (create, get, update) with JWT auth header and full schemas (review_cycles: 0)
- [ ] REQ-007: Create sample AsyncAPI 3.0 spec for order events at tests/run4/fixtures/sample_asyncapi_order.yaml — OrderCreated and OrderShipped channels with payload schemas (review_cycles: 0)
- [ ] REQ-008: Create sample Pact V4 contract at tests/run4/fixtures/sample_pact_auth.json — order-service consuming auth-service login endpoint (review_cycles: 0)

- [ ] TECH-001: Run4Config must validate all paths exist at initialization; raise ValueError with specific missing path (review_cycles: 0)
- [ ] TECH-002: Run4State JSON schema must include the Finding dataclass with these 10 fields: finding_id (FINDING-NNN pattern), priority (P0-P3), system (Build 1/Build 2/Build 3/Integration), component (specific module/function), evidence (exact reproduction or test output), recommendation (specific fix action), resolution (FIXED/OPEN/WONTFIX), fix_pass_number (int), fix_verification (test ID confirming fix), created_at (ISO 8601 timestamp). The canonical schema definition is REQ-029 in this PRD. (review_cycles: 0)
- [ ] TECH-003: All fixture YAML files must pass validation: OpenAPI specs via openapi-spec-validator, AsyncAPI specs via structural validation against AsyncAPI 3.0 schema (review_cycles: 0)

- [ ] INT-001: Create conftest.py with session-scoped fixtures: run4_config, sample_prd_text, build1_root, contract_engine_params (StdioServerParameters), architect_params, codebase_intel_params (review_cycles: 0)
- [ ] INT-002: Create mock_mcp_session pytest fixture returning AsyncMock with call_tool, list_tools, initialize methods (review_cycles: 0)
- [ ] INT-003: Create make_mcp_result(data, is_error) helper that builds mock MCP tool results with TextContent containing JSON (review_cycles: 0)
- [ ] INT-004: Create poll_until_healthy(service_urls, timeout_s, interval_s, required_consecutive) async utility that polls HTTP health endpoints until all services report healthy (review_cycles: 0)
- [ ] INT-005: Create check_mcp_health(server_params, timeout) async utility that spawns MCP server, calls initialize + list_tools, returns health dict with status/tools_count/tool_names/error fields (review_cycles: 0)
- [ ] INT-006: Create parse_builder_state(output_dir) utility that reads .agent-team/STATE.json and extracts summary dict fields (success, test_passed, test_total, convergence_ratio) (review_cycles: 0)
- [ ] INT-007: Create detect_regressions(before, after) utility that compares violation snapshots and returns list of regressed violations (review_cycles: 0)

- [ ] TEST-001: Test Run4State save/load roundtrip preserves all fields including nested dicts and lists (review_cycles: 0)
- [ ] TEST-002: Test Run4State.load() returns None for missing file and None for corrupted JSON (review_cycles: 0)
- [ ] TEST-003: Test Run4Config validates paths and raises ValueError for missing build root (review_cycles: 0)
- [ ] TEST-004: Test all fixture YAML files are syntactically valid (review_cycles: 0)
- [ ] TEST-005: Test mock_mcp_session fixture produces usable AsyncMock (review_cycles: 0)
- [ ] TEST-006: Test poll_until_healthy returns results within timeout for healthy mock servers (review_cycles: 0)
- [ ] TEST-007: Test detect_regressions correctly identifies new violations not in previous snapshot (review_cycles: 0)

### Source directory structure

```
src/run4/
    __init__.py
    config.py              # Run4Config dataclass
    state.py               # Run4State, Finding dataclasses
    mcp_health.py          # check_mcp_health, poll_until_healthy
    builder.py             # builder invocation, parallel execution
    fix_pass.py            # fix loop, convergence, regression detection
    scoring.py             # per-system scoring, integration scoring, aggregate
    audit_report.py        # report generation, RTM, coverage matrices
```

### Test directory structure

```
tests/run4/
    conftest.py
    test_m1_infrastructure.py
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

## Milestone 2: Build 1 → Build 2 MCP Wiring Verification

- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Verify that every MCP tool exposed by Build 1's 3 servers is callable from Build 2's client wrappers. Test session lifecycle, error recovery, retry behavior, and fallback paths.

### MCP Tool-to-Client Wiring Map

> **Note**: This SVC table uses a 6-column format (SVC-ID, Client Method, MCP Server, MCP Tool, Request DTO, Response DTO) rather than the standard 7-column HTTP format. This is intentional — these are MCP stdio tool calls, not HTTP frontend-to-backend APIs. The `_parse_svc_table()` API contract scanner targets HTTP wiring and does not apply to MCP tool wiring. The MCP wiring verification is handled by the WIRE-xxx test requirements.
>
> **Reconciliation note**: Every SVC entry (SVC-001 through SVC-017) has been reconciled against the source Build PRD specs field-by-field. Run 4 SVC tables correctly use `dict` types for MCP return values (since MCP returns JSON dicts, not Pydantic models). Agents implementing Run 4 should verify field NAME accuracy and completeness against the Build PRD Pydantic model definitions (e.g., Build 1 SVC-002 includes `build_cycle_id` which exists in the ServiceMap Pydantic model).

| SVC-ID | Client Method | MCP Server | MCP Tool | Request DTO | Response DTO |
|--------|---------------|------------|----------|-------------|--------------|
| SVC-001 | ArchitectClient.decompose(prd_text) | Architect | decompose | { prd_text: string } | DecompositionResult { service_map: dict, domain_model: dict, contract_stubs: list, validation_issues: list, interview_questions: list[string] } |
| SVC-002 | ArchitectClient.get_service_map() | Architect | get_service_map | None | ServiceMap { project_name: string, services: list, generated_at: string, prd_hash: string, build_cycle_id: string\|null } |
| SVC-003 | ArchitectClient.get_contracts_for_service(service_name) | Architect | get_contracts_for_service | { service_name: string } | list { id: string, role: string, type: string, counterparty: string, summary: string } |
| SVC-004 | ArchitectClient.get_domain_model() | Architect | get_domain_model | None | DomainModel { entities: list, relationships: list, generated_at: string } |
| SVC-005 | ContractEngineClient.get_contract(contract_id) | Contract Engine | get_contract | { contract_id: string } | ContractEntry { id: string, service_name: string, type: string, version: string, spec: dict, spec_hash: string, status: string } |
| SVC-006 | ContractEngineClient.validate_endpoint(service_name, method, path, response_body, status_code) | Contract Engine | validate_endpoint | { service_name: string, method: string, path: string, response_body: dict, status_code: number } | ContractValidation { valid: boolean, violations: list } |
| SVC-007 | ContractEngineClient.generate_tests(contract_id, framework, include_negative) | Contract Engine | generate_tests | { contract_id: string, framework: string, include_negative: boolean } | string |
| SVC-008 | ContractEngineClient.check_breaking_changes(contract_id, new_spec) | Contract Engine | check_breaking_changes | { contract_id: string, new_spec: dict } | list { change_type: string, path: string, severity: string, old_value: string\|null, new_value: string\|null, affected_consumers: list[string] } |
| SVC-009 | ContractEngineClient.mark_implemented(contract_id, service_name, evidence_path) | Contract Engine | mark_implemented | { contract_id: string, service_name: string, evidence_path: string } | MarkResult { marked: boolean, total_implementations: number, all_implemented: boolean } |
| SVC-010 | ContractEngineClient.get_unimplemented_contracts(service_name) | Contract Engine | get_unimplemented_contracts | { service_name: string } | list { id: string, type: string, expected_service: string, version: string, status: string } |
| SVC-011 | CodebaseIntelligenceClient.find_definition(symbol, language) | Codebase Intelligence | find_definition | { symbol: string, language: string } | DefinitionResult { file_path: string, line_start: number, line_end: number, kind: string, signature: string\|null, docstring: string\|null } |
| SVC-012 | CodebaseIntelligenceClient.find_callers(symbol, max_results) | Codebase Intelligence | find_callers | { symbol: string, max_results: number } | list { file_path: string, line: number, caller_name: string } |
| SVC-013 | CodebaseIntelligenceClient.find_dependencies(file_path) | Codebase Intelligence | find_dependencies | { file_path: string } | DependencyResult { imports: list, imported_by: list, transitive_deps: list, circular_deps: list } |
| SVC-014 | CodebaseIntelligenceClient.search_semantic(query, language, service_name, n_results) | Codebase Intelligence | search_semantic | { query: string, language: string, service_name: string, n_results: number } | list { chunk_id: string, file_path: string, symbol_name: string\|null, content: string, score: number, language: string, service_name: string\|null, line_start: number, line_end: number } |
| SVC-015 | CodebaseIntelligenceClient.get_service_interface(service_name) | Codebase Intelligence | get_service_interface | { service_name: string } | ServiceInterface { service_name: string, endpoints: list, events_published: list, events_consumed: list, exported_symbols: list } |
| SVC-016 | CodebaseIntelligenceClient.check_dead_code(service_name) | Codebase Intelligence | check_dead_code | { service_name: string } | list { symbol_name: string, file_path: string, kind: string, line: number, service_name: string\|null, confidence: string } |
| SVC-017 | CodebaseIntelligenceClient.register_artifact(file_path, service_name) | Codebase Intelligence | register_artifact | { file_path: string, service_name: string } | ArtifactResult { indexed: boolean, symbols_found: number, dependencies_found: number, errors: list[string] } |

### Requirements

- [ ] REQ-009: MCP handshake test for Architect server — spawn via StdioServerParameters with correct cwd and env, call session.initialize(), verify capabilities include "tools", call session.list_tools(), verify exactly 4 tools returned (review_cycles: 0)
- [ ] REQ-010: MCP handshake test for Contract Engine server — spawn, initialize, verify capabilities, verify exactly 9 tools returned with names matching {create_contract, validate_spec, list_contracts, get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts} (review_cycles: 0)
- [ ] REQ-011: MCP handshake test for Codebase Intelligence server — spawn, initialize, verify capabilities, verify exactly 7 tools returned with names matching {find_definition, find_callers, find_dependencies, search_semantic, get_service_interface, check_dead_code, register_artifact} (review_cycles: 0)
- [ ] REQ-012: MCP tool roundtrip tests — for each of the 20 MCP tools across 3 servers: call with valid parameters, verify non-error response; call with invalid parameter types, verify isError response without crash; parse response into expected schema, verify field presence and types (review_cycles: 0)
- [ ] REQ-013: Build 2 ContractEngineClient wrapper tests — all 6 methods return correct dataclass types with mocked MCP session; all methods return safe defaults on MCP error (never raise); all methods retry 3 times on transient errors with exponential backoff (1s, 2s, 4s) (review_cycles: 0)
- [ ] REQ-014: Build 2 CodebaseIntelligenceClient wrapper tests — all 7 methods return correct dataclass types with mocked session; safe defaults on error; 3-retry pattern verified (review_cycles: 0)
- [ ] REQ-015: Build 2 ArchitectClient wrapper tests — all 4 methods return correct types; decompose() returns None on failure (fallback to standard decomposition) (review_cycles: 0)

- [ ] WIRE-001: Session lifecycle test — open session, make 10 sequential calls, close; verify all succeed without error (review_cycles: 0)
- [ ] WIRE-002: Session crash recovery test — open session, kill server process, verify client detects broken pipe on next call (review_cycles: 0)
- [ ] WIRE-003: Session timeout test — open session, simulate slow tool call exceeding mcp_tool_timeout_ms, verify TimeoutError propagation (review_cycles: 0)
- [ ] WIRE-004: Multi-server concurrency test — open 3 sessions simultaneously (one per Build 1 server), make parallel calls, verify no resource conflicts (review_cycles: 0)
- [ ] WIRE-005: Session restart test — close session, open new session to same server, verify new session has full database access to previously created data (review_cycles: 0)
- [ ] WIRE-006: Malformed JSON test — call tool with parameter that would produce malformed JSON response, verify isError returned without crash (review_cycles: 0)
- [ ] WIRE-007: Non-existent tool test — call session.call_tool("nonexistent_tool", {}), verify error response without crash (review_cycles: 0)
- [ ] WIRE-008: Server process exit test — server process exits with non-zero code, client detects and logs error (review_cycles: 0)

- [ ] WIRE-009: Fallback test — Contract Engine MCP unavailable, Build 2 falls back to run_api_contract_scan() from quality_checks.py (review_cycles: 0)
- [ ] WIRE-010: Fallback test — Codebase Intelligence MCP unavailable, Build 2 falls back to generate_codebase_map() (review_cycles: 0)
- [ ] WIRE-011: Fallback test — Architect MCP unavailable, standard PRD decomposition proceeds without error (review_cycles: 0)

- [ ] WIRE-012: Cross-server verification — Architect's get_contracts_for_service internally calls Contract Engine via HTTP; verify this works when both MCP servers and Contract Engine FastAPI are running (review_cycles: 0)

- [ ] TEST-008: Latency benchmark — measure round-trip time for each of 20 MCP tool calls; record median, p95, p99; threshold: <5s per tool call, <30s server startup (120s for Codebase Intelligence first start) (review_cycles: 0)

### Service-to-API Wiring Checklist

- [ ] SVC-001: ArchitectClient.decompose() -> Architect MCP decompose (review_cycles: 0)
- [ ] SVC-002: ArchitectClient.get_service_map() -> Architect MCP get_service_map (review_cycles: 0)
- [ ] SVC-003: ArchitectClient.get_contracts_for_service() -> Architect MCP get_contracts_for_service (review_cycles: 0)
- [ ] SVC-004: ArchitectClient.get_domain_model() -> Architect MCP get_domain_model (review_cycles: 0)
- [ ] SVC-005: ContractEngineClient.get_contract() -> Contract Engine MCP get_contract (review_cycles: 0)
- [ ] SVC-006: ContractEngineClient.validate_endpoint() -> Contract Engine MCP validate_endpoint (review_cycles: 0)
- [ ] SVC-007: ContractEngineClient.generate_tests() -> Contract Engine MCP generate_tests (review_cycles: 0)
- [ ] SVC-008: ContractEngineClient.check_breaking_changes() -> Contract Engine MCP check_breaking_changes (review_cycles: 0)
- [ ] SVC-009: ContractEngineClient.mark_implemented() -> Contract Engine MCP mark_implemented (review_cycles: 0)
- [ ] SVC-010: ContractEngineClient.get_unimplemented_contracts() -> Contract Engine MCP get_unimplemented_contracts (review_cycles: 0)
- [ ] SVC-010a: Build 3 Integrator -> Contract Engine MCP create_contract (consumed directly via MCP, not wrapped by Build 2 ContractEngineClient) (review_cycles: 0)
- [ ] SVC-010b: Build 3 Integrator -> Contract Engine MCP validate_spec (consumed directly via MCP, not wrapped by Build 2 ContractEngineClient) (review_cycles: 0)
- [ ] SVC-010c: Build 3 Integrator -> Contract Engine MCP list_contracts (consumed directly via MCP, not wrapped by Build 2 ContractEngineClient) (review_cycles: 0)
- [ ] SVC-011: CodebaseIntelligenceClient.find_definition() -> Codebase Intelligence MCP find_definition (review_cycles: 0)
- [ ] SVC-012: CodebaseIntelligenceClient.find_callers() -> Codebase Intelligence MCP find_callers (review_cycles: 0)
- [ ] SVC-013: CodebaseIntelligenceClient.find_dependencies() -> Codebase Intelligence MCP find_dependencies (review_cycles: 0)
- [ ] SVC-014: CodebaseIntelligenceClient.search_semantic() -> Codebase Intelligence MCP search_semantic (review_cycles: 0)
- [ ] SVC-015: CodebaseIntelligenceClient.get_service_interface() -> Codebase Intelligence MCP get_service_interface (review_cycles: 0)
- [ ] SVC-016: CodebaseIntelligenceClient.check_dead_code() -> Codebase Intelligence MCP check_dead_code (review_cycles: 0)
- [ ] SVC-017: CodebaseIntelligenceClient.register_artifact() -> Codebase Intelligence MCP register_artifact (review_cycles: 0)

---

## Milestone 3: Build 2 → Build 3 Wiring Verification

- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-1
- Description: Verify that Build 3's Super Orchestrator can invoke Build 2 Builders as subprocesses, parse their output, generate valid configs, and feed fix instructions. Test parallel builder isolation.

### Subprocess Wiring Map

> **Note**: This SVC table uses a 6-column subprocess wiring format (SVC-ID, Caller, Command, Input, Output, Verification) rather than the standard HTTP format. These are subprocess invocations, not HTTP APIs.

| SVC-ID | Caller | Command | Input | Output | Verification |
|--------|--------|---------|-------|--------|-------------|
| SVC-018 | pipeline.run_parallel_builders | python -m agent_team --cwd {dir} --depth {depth} | config.yaml in builder dir | .agent-team/STATE.json with summary dict | Builder exit code 0, STATE.json has summary.success |
| SVC-019 | fix_loop.feed_violations_to_builder | python -m agent_team --cwd {dir} --depth quick | FIX_INSTRUCTIONS.md in builder dir | Updated STATE.json with cost | Violations reduced after fix pass |
| SVC-020 | pipeline.generate_builder_config | N/A (file write) | SuperOrchestratorConfig | config.yaml loadable by Build 2 _dict_to_config() | Config roundtrip: generate -> load -> no errors |

### Requirements

- [ ] REQ-016: Builder subprocess invocation test — Build 3 calls `python -m agent_team --cwd {dir} --depth {depth}` via asyncio.create_subprocess_exec; builder process starts, runs, and exits with code 0; {dir}/.agent-team/STATE.json is written with summary dict; stdout/stderr captured and parseable (review_cycles: 0)
- [ ] REQ-017: STATE.json parsing test (cross-build contract) — verify Build 2's RunState.to_dict() writes summary dict containing: success (bool), test_passed (int), test_total (int), convergence_ratio (float); also verify total_cost (float), health (str), completed_phases (list[str]) at top level (review_cycles: 0)
- [ ] REQ-018: Config generation compatibility test — Build 3's generate_builder_config() produces a config.yaml that Build 2's _dict_to_config() can parse without errors; test all depth levels (quick, standard, thorough, exhaustive); verify _dict_to_config() returns tuple[AgentTeamConfig, set[str]] (Build 2's v6.0 return type) (review_cycles: 0)
- [ ] REQ-019: Parallel builder isolation test — launch 3 builders simultaneously with asyncio.Semaphore(3); each builder writes to its own directory; verify no cross-contamination between builder directories; verify Semaphore prevents 4th concurrent builder (review_cycles: 0)
- [ ] REQ-020: Fix pass invocation test — write FIX_INSTRUCTIONS.md to builder directory with categorized violations; invoke builder in quick mode; verify builder reads and processes FIX_INSTRUCTIONS.md; parse updated STATE.json and verify cost field updated (review_cycles: 0)

- [ ] WIRE-013: Agent Teams fallback test — when config.agent_teams.enabled=True but Claude CLI unavailable, create_execution_backend() returns CLIBackend with logged warning; pipeline continues with subprocess mode (review_cycles: 0)
- [ ] WIRE-014: Agent Teams hard failure test — when config.agent_teams.enabled=True and fallback_to_cli=False and CLI unavailable, RuntimeError is raised (review_cycles: 0)
- [ ] WIRE-015: Builder timeout test — set builder_timeout_s to 5 seconds, invoke builder on task that takes longer, verify proc.kill() + await proc.wait() in finally block (review_cycles: 0)
- [ ] WIRE-016: Builder environment isolation test — verify builders inherit parent environment but ANTHROPIC_API_KEY is NOT passed explicitly (SEC-001 compliance) (review_cycles: 0)
- [ ] WIRE-021: Agent Teams positive-path test — when config.agent_teams.enabled=True and Claude CLI is available, AgentTeamsBackend.execute_wave() completes with task state progression (pending -> in_progress -> completed); verify TaskCreate, TaskUpdate, and SendMessage are invoked during within-service coordination (review_cycles: 0)

- [ ] TEST-009: Test BuilderResult dataclass correctly maps all STATE.json summary fields (review_cycles: 0)
- [ ] TEST-010: Test parallel builder result aggregation — collect BuilderResult from 3 builders, verify per-service results preserved (review_cycles: 0)

### Service-to-API Wiring Checklist

- [ ] SVC-018: pipeline.run_parallel_builders -> agent_team CLI subprocess (review_cycles: 0)
- [ ] SVC-019: fix_loop.feed_violations_to_builder -> agent_team CLI quick mode (review_cycles: 0)
- [ ] SVC-020: pipeline.generate_builder_config -> Build 2 config.yaml (review_cycles: 0)

---

## Milestone 4: End-to-End Pipeline Test

- ID: milestone-4
- Status: PENDING
- Dependencies: milestone-2, milestone-3
- Description: Feed the 3-service sample PRD through the COMPLETE pipeline — Architect decomposition → Contract registration → 3 parallel Builders → Docker deployment → Integration tests → Quality Gate. All with real subprocesses; Docker via Testcontainers.

### Pipeline Phase Requirements

- [ ] REQ-021: Phase 1 (Build 1 Health) — start all Build 1 services via Docker Compose; Architect API on :8001, Contract Engine on :8002, Codebase Intelligence on :8003; all respond HTTP 200 on /api/health; gate: ALL 3 must be healthy before proceeding (review_cycles: 0)
- [ ] REQ-022: Phase 2 (MCP Smoke) — Architect MCP decompose tool callable with sample PRD; Contract Engine MCP validate_spec and get_contract tools callable; Codebase Intelligence MCP find_definition and register_artifact tools callable; gate: ALL smoke tests pass (review_cycles: 0)
- [ ] REQ-023: Phase 3 (Architect Decomposition) — feed sample TaskTracker PRD to Architect via MCP decompose; receive ServiceMap with 3 services (auth-service, order-service, notification-service); receive DomainModel with entities (User, Order, Notification); receive ContractStubs; gate: valid ServiceMap with >= 3 services AND DomainModel with >= 3 entities (review_cycles: 0)
- [ ] REQ-024: Phase 4 (Contract Registration) — register contract stubs with Contract Engine via create_contract() MCP calls; validate all contracts with validate_spec() returning valid=true; verify retrieval with list_contracts() showing all 3+ contracts; gate: ALL contracts registered AND valid (review_cycles: 0)
- [ ] REQ-025: Phase 5 (Parallel Builders) — launch 3 Builder subprocesses (one per service from ServiceMap); each runs full agent-team pipeline with contract-aware config; each writes STATE.json with summary dict; collect BuilderResult per service; gate: >= 2 of 3 builders succeed (partial success acceptable) (review_cycles: 0)
- [ ] REQ-026: Phase 6 (Deployment + Integration) — ComposeGenerator produces docker-compose.generated.yml from builder outputs; DockerOrchestrator runs docker compose up -d with merged compose files; health check all services via ServiceDiscovery.wait_all_healthy(); verify each service responds to GET /openapi.json with HTTP 200 before running Schemathesis (precondition — FastAPI exposes this by default but it can be disabled); run contract compliance via Schemathesis pointing at http://localhost:{port}/openapi.json for each of the 3 generated services (stateful mode, authenticate with JWT from auth-service login); run cross-service integration tests with per-step assertions: (1) Register: POST /register -> 201, body has {id, email, created_at}, (2) Login: POST /login -> 200, body has {access_token, refresh_token}, (3) Create order: POST /orders with JWT -> 201, body has {id, status, items, total}, (4) Check notification: GET /notifications -> 200, body is list with len >= 1; gate: all services healthy AND > 70% contract compliance (review_cycles: 0)
- [ ] REQ-027: Phase 7 (Quality Gate) — Layer 1: evaluate BuilderResult per service (test pass rate, convergence); Layer 2: evaluate IntegrationReport contract test results; Layer 3 specific checks: SEC-SCAN-001 no hardcoded secrets (regex: password|secret|api_key\s*=\s*["'][^"']+["']), CORS-001 CORS origins not set to "*" in production config, LOG-001 no print() statements (use logging module), LOG-002 all endpoints have request logging middleware, DOCKER-001 all services have HEALTHCHECK instruction, DOCKER-002 no :latest tags in FROM statements; Layer 4 static analysis checks: DEAD-001 events published but never consumed (cross-reference publish/subscribe), DEAD-002 contracts registered but never validated, ORPHAN-001 service in compose but no route in Traefik config, NAME-001 service names consistent across compose, code, and contracts; gate: overall_verdict != "failed" (review_cycles: 0)

- [ ] REQ-028: Planted violation detection — include deliberate violations in test setup: one service missing /health endpoint (HEALTH-001), one endpoint returning field not in OpenAPI contract (SCHEMA-001), one print() instead of logger (LOG-001); verify all 3 appear in Quality Gate report (review_cycles: 0)

- [ ] WIRE-017: Docker Compose merge test — Build 1 services + infrastructure + Traefik + generated services coexist in merged compose; verify via docker network inspect: frontend network contains traefik, architect, contract-engine, codebase-intelligence, auth-service, order-service, notification-service; backend network contains postgres, redis, architect, contract-engine, codebase-intelligence, auth-service, order-service, notification-service; traefik is NOT on backend network; postgres and redis are NOT on frontend network (review_cycles: 0)
- [ ] WIRE-018: Inter-container DNS test — Architect container resolves contract-engine hostname and reaches it via HTTP (review_cycles: 0)
- [ ] WIRE-019: Traefik routing test — PathPrefix labels on Build 1 services route correctly through Traefik gateway (review_cycles: 0)
- [ ] WIRE-020: Health check cascade test — startup order respects dependency chain: postgres → contract-engine → architect + codebase-intelligence → generated services → traefik (review_cycles: 0)

- [ ] TECH-004: Docker Compose test topology must use the 5-file merge: infra.yml + build1.yml + traefik.yml + generated.yml + run4.yml as specified in RUN4_ARCHITECTURE_PLAN.md Section 8 (review_cycles: 0)
- [ ] TECH-005: Testcontainers compose module must handle startup/cleanup lifecycle; ephemeral volumes for test isolation; random port mapping for parallel test safety (review_cycles: 0)
- [ ] TECH-006: Resource budget: total Docker RAM must not exceed 4.5GB (3 Build 1 services: 2GB, postgres+redis: 640MB, traefik: 128MB, 3 generated services: 1.5GB) (review_cycles: 0)

- [ ] SEC-001: No ANTHROPIC_API_KEY passed explicitly to builder subprocesses — builders inherit parent environment only (review_cycles: 0)
- [ ] SEC-002: Traefik dashboard disabled by default (--api.dashboard=false) (review_cycles: 0)
- [ ] SEC-003: Docker socket mounted read-only (/var/run/docker.sock:ro) (review_cycles: 0)

- [ ] TEST-011: End-to-end pipeline timing test — total pipeline duration recorded; GREEN threshold: <6 hours (review_cycles: 0)
- [ ] TEST-012: Pipeline state checkpoint test — verify state saved after each phase; kill pipeline mid-build, verify resume from checkpoint (review_cycles: 0)

---

## Milestone 5: Fix Pass + Defect Remediation

- ID: milestone-5
- Status: PENDING
- Dependencies: milestone-4
- Description: Catalog all defects from M2-M4, classify by priority (P0-P3), apply convergence-based fix passes, track effectiveness metrics, verify no regressions.

### Requirements

- [ ] REQ-029: Issue cataloging — scan all M2-M4 results and produce defect catalog using Finding dataclass with fields: finding_id (FINDING-NNN), priority (P0-P3), system (Build 1/Build 2/Build 3/Integration), component (specific module/function), evidence (exact reproduction or test output), recommendation (specific fix action), resolution (FIXED/OPEN/WONTFIX), fix_pass_number, fix_verification (test ID confirming fix) (review_cycles: 0)
- [ ] REQ-030: Priority classification using decision tree — P0: system cannot start/deploy, blocks everything (must fix before proceeding); P1: primary use case fails, no workaround (must fix in current pass); P2: secondary feature broken (fix if time permits); P3: cosmetic/performance/docs (document only) (review_cycles: 0)
- [ ] REQ-031: Fix pass execution — for each pass (up to max_fix_passes): (1) DISCOVER: run all scans, collect violations; (2) CLASSIFY: apply P0-P3 decision tree; (3) GENERATE: write FIX_INSTRUCTIONS.md targeting P0 first, then P1; (4) APPLY: infrastructure fixes via direct edit, Build 1/3 code via direct edit, Build 2 code via builder quick mode; (5) VERIFY: re-run specific scan that found each violation; (6) REGRESS: run full scan set, compare before/after snapshots (review_cycles: 0)
- [ ] REQ-032: Fix pass metrics tracking per pass — fix_effectiveness (fixes_resolved / fixes_attempted), regression_rate (new_violations / total_fixes_applied), new_defect_discovery_rate, score_delta (score_after - score_before) (review_cycles: 0)
- [ ] REQ-033: Convergence criteria — hard stop triggers (any one): P0=0 AND P1=0; max_fix_passes reached; budget exhausted; fix_effectiveness < 30% for 2 consecutive passes; regression_rate > 25% for 2 consecutive passes. Soft convergence ("good enough"): P0=0, P1<=2, new_defect_rate < 3 per pass for 2 consecutive, aggregate_score >= 70 (review_cycles: 0)

- [ ] TECH-007: Convergence formula: convergence = 1.0 - (remaining_p0 * 0.4 + remaining_p1 * 0.3 + remaining_p2 * 0.1) / initial_total_weighted; converged when >= 0.85 (review_cycles: 0)
- [ ] TECH-008: Violation snapshot format — dict mapping scan_code to list of file_paths; saved as JSON before and after each fix pass for regression detection (review_cycles: 0)

- [ ] TEST-013: Test regression detection — create snapshot with known violations, apply mock fixes, verify detect_regressions() finds reappearing violations (review_cycles: 0)
- [ ] TEST-014: Test convergence formula — verify formula produces correct values for known P0/P1/P2 counts (review_cycles: 0)
- [ ] TEST-015: Test hard stop triggers — verify fix loop terminates when any hard stop condition is met (review_cycles: 0)

---

## Milestone 6: Audit Report + Final Verification

- ID: milestone-6
- Status: PENDING
- Dependencies: milestone-5
- Description: Compute per-system and aggregate scores, generate the final SUPER_TEAM_AUDIT_REPORT.md with honest assessment of gaps, produce all appendices.

### Scoring Rubric

**Per-System Scoring (Build 1, Build 2, Build 3) — out of 100:**

| Category | Weight | Metric | Scoring |
|---|---|---|---|
| Functional Completeness | 30% | REQ-xxx pass rate | Linear: 0% = 0, 100% = 30 |
| Test Health | 20% | Test pass rate | Linear: 0% = 0, 100% = 20 |
| Contract Compliance | 20% | Schema validation pass rate | Linear: 0% = 0, 100% = 20 |
| Code Quality | 15% | Violation density per KLOC | Inverse: 0 = 15, >10 = 0 |
| Docker Health | 10% | Health check pass rate | Linear: 0% = 0, 100% = 10 |
| Documentation | 5% | Required artifacts present | Binary per artifact |

**Integration Scoring — out of 100:**

| Category | Weight | Metric |
|---|---|---|
| MCP Connectivity | 25% | MCP tools responding correctly (20 tools binary) |
| Data Flow Integrity | 25% | E2E flows completing (pass/fail per flow) |
| Contract Fidelity | 25% | Cross-build violations (inverse) |
| Pipeline Completion | 25% | Super Orchestrator phases completing (% done) |

**Aggregate**: `(build1 * 0.30) + (build2 * 0.25) + (build3 * 0.25) + (integration * 0.20)`

**Traffic Light**: GREEN (80-100), YELLOW (50-79), RED (0-49)

### Requirements

- [ ] REQ-034: Per-system scoring — compute scores for Build 1, Build 2, Build 3 using the rubric above; formula: system_score = (req_pass_rate * 30) + (test_pass_rate * 20) + (contract_pass_rate * 20) + max(0, 15 - violation_density * 1.5) + (health_check_rate * 10) + (artifacts_present / artifacts_required * 5); where violation_density = total_violations / (total_lines_of_code / 1000), counting .py files in service source directories (excluding tests, __pycache__, venv); artifacts_required per service (5 items): Dockerfile, requirements.txt or pyproject.toml, README.md, OpenAPI/AsyncAPI spec file, health check endpoint (/health) (review_cycles: 0)
- [ ] REQ-035: Integration scoring — compute integration score: (mcp_tools_ok / 20 * 25) + (flows_passing / flows_total * 25) + max(0, 25 - cross_build_violations * 2.5) + (phases_complete / phases_total * 25) (review_cycles: 0)
- [ ] REQ-036: Aggregate score computation — aggregate = (build1 * 0.30) + (build2 * 0.25) + (build3 * 0.25) + (integration * 0.20); classify as GREEN/YELLOW/RED (review_cycles: 0)
- [ ] REQ-037: SUPER_TEAM_AUDIT_REPORT.md generation — write to .run4/SUPER_TEAM_AUDIT_REPORT.md with sections: (1) Executive Summary (scores, verdict, fix passes, defect totals), (2) Methodology, (3) Per-System Assessment, (4) Integration Assessment, (5) Fix Pass History with per-pass metrics, (6) Gap Analysis with RTM summary, (7) Appendices (RTM, Violations, Test Results, Cost Breakdown) (review_cycles: 0)
- [ ] REQ-038: Requirements Traceability Matrix — for each REQ-xxx across all 3 Build PRDs: list implementation file(s), test ID(s), test status (PASS/FAIL/UNTESTED), verification status (Verified/Gap) (review_cycles: 0)
- [ ] REQ-039: Interface Coverage Matrix — for each of 20 MCP tools: valid request tested (Y/N), error request tested (Y/N), response parseable (Y/N), status (GREEN/YELLOW/RED); target: 100% valid, >=80% error (review_cycles: 0)
- [ ] REQ-040: Data flow path coverage — for each of 5 primary data flows and error paths: tested (Y/N), status, evidence (review_cycles: 0)

- [ ] REQ-041: Dark corners catalog — explicitly test and document: (1) MCP server startup race condition: start all 3 MCP servers simultaneously via asyncio.gather, verify all 3 reach "healthy" within mcp_startup_timeout_ms, PASS=all 3 healthy, FAIL=any server fails to start or deadlocks; (2) Docker network DNS resolution: from architect container curl http://contract-engine:8000/api/health, PASS=HTTP 200, FAIL=DNS resolution failure or connection refused; (3) Concurrent builder file conflicts: launch 3 builders targeting separate directories, verify no file in builder A's directory was written by builder B, PASS=zero cross-directory writes, FAIL=any file found in wrong directory; (4) State machine resume after crash: run pipeline to phase 3, kill process (SIGINT), restart, verify resume from phase 3 checkpoint, PASS=resumes from phase 3, FAIL=restarts from phase 1; (5) Large PRD handling: feed 200KB PRD (4x normal size) to Architect decompose, verify decomposition completes within 2x normal timeout, PASS=valid ServiceMap returned, FAIL=timeout or crash (review_cycles: 0)
- [ ] REQ-042: Cost breakdown report — per-phase cost and duration: M1 through M6 totals, grand total, comparison to budget estimate (review_cycles: 0)

- [ ] TECH-009: "Good enough" thresholds — per-system minimum: 60 (YELLOW); integration minimum: 50; aggregate minimum: 65; P0 remaining: 0 (hard); P1 remaining: <=3; test pass rate: >=85%; MCP tool coverage: >=90%; fix convergence: >=0.70 (review_cycles: 0)

- [ ] TEST-016: Test scoring formula produces correct values for known inputs (review_cycles: 0)
- [ ] TEST-017: Test audit report generation produces valid markdown with all required sections (review_cycles: 0)
- [ ] TEST-018: Test RTM correctly maps Build PRD requirements to test results (review_cycles: 0)

---

## Verification Test Matrix Summary

| Category | Tests | P0 | P1 | P2 |
|---|---|---|---|---|
| Success Criteria (SC) | 7 | 6 | 1 | 0 |
| Build 1 Verification (B1) | 20 | 14 | 5 | 1 |
| Build 2 Verification (B2) | 10 | 6 | 4 | 0 |
| Build 3 Verification (B3) | 10 | 5 | 4 | 1 |
| Cross-Build Integration (X) | 10 | 6 | 4 | 0 |
| **Total** | **57** | **37** | **18** | **2** |

### Build 1 Tests

| ID | Test | Expected | Priority | Maps To | Milestone |
|---|---|---|---|---|---|
| B1-01 | test_build1_deploy | All 3 services in compose | P0 | REQ-021 | M4 |
| B1-02 | test_build1_health | HTTP 200 on /api/health x3 | P0 | REQ-021 | M4 |
| B1-03 | test_architect_decompose | ServiceMap with >= 1 service | P0 | REQ-023, TEST-008 | M4 |
| B1-04 | test_contract_validation | validate_spec() -> valid: true | P0 | REQ-024 | M4 |
| B1-05 | test_contract_test_gen | Non-empty test code string | P1 | REQ-010 | M2 |
| B1-06 | test_codebase_indexing_perf | < 60s for 50K LOC | P2 | TEST-008 | M2 |
| B1-07 | test_mcp_tool_responses | 20 tools return non-error | P0 | REQ-012 | M2 |
| B1-08 | test_dead_code_detection | Planted dead code found | P1 | REQ-011 | M2 |
| B1-09 | test_mcp_handshake_architect | Capabilities include tools | P0 | REQ-009 | M2 |
| B1-10 | test_mcp_handshake_contract | Capabilities include tools | P0 | REQ-010 | M2 |
| B1-11 | test_mcp_handshake_codebase | Capabilities include tools | P0 | REQ-011 | M2 |
| B1-12 | test_tool_count_architect | Exactly 4 tools | P0 | REQ-009 | M2 |
| B1-13 | test_tool_count_contract | Exactly 9 tools | P0 | REQ-010 | M2 |
| B1-14 | test_tool_count_codebase | Exactly 7 tools | P0 | REQ-011 | M2 |
| B1-15 | test_invalid_tool_input | isError=True, no crash | P0 | REQ-012, WIRE-006 | M2 |
| B1-16 | test_nonexistent_tool | Error response, no crash | P1 | WIRE-007 | M2 |
| B1-17 | test_server_crash_recovery | Client detects, recovers | P0 | WIRE-002 | M2 |
| B1-18 | test_multi_server_simultaneous | No resource conflicts | P0 | WIRE-004 | M2 |
| B1-19 | test_architect_cross_ref | get_contracts_for_service returns data | P1 | WIRE-012 | M2 |
| B1-20 | test_inter_container_dns | Architect reaches Contract Engine by hostname | P1 | WIRE-018 | M4 |

### Build 2 Tests

| ID | Test | Expected | Priority | Maps To | Milestone |
|---|---|---|---|---|---|
| B2-01 | test_contract_client_all_methods | All 6 return correct types | P0 | REQ-013 | M3 |
| B2-02 | test_codebase_client_all_methods | All 7 return correct types | P0 | REQ-014 | M3 |
| B2-03 | test_mcp_safe_defaults | All methods return safe defaults on error | P0 | REQ-013, REQ-014 | M3 |
| B2-04 | test_contract_scan_detection | Planted violation found | P0 | TEST-009 | M3 |
| B2-05 | test_parallel_builders | Both complete, no conflicts | P1 | TEST-010 | M3 |
| B2-06 | test_artifact_registration | register_artifact -> indexed=True | P1 | REQ-014 | M3 |
| B2-07 | test_fallback_contract_engine | Static scan runs when MCP unavailable | P0 | WIRE-009 | M2 |
| B2-08 | test_fallback_codebase_intel | Static map generated when MCP unavailable | P0 | WIRE-010 | M2 |
| B2-09 | test_backward_compat | All B2 features disabled = v14.0 behavior | P1 | REQ-015 | M3 |
| B2-10 | test_retry_exponential_backoff | 3 retries with 1s, 2s, 4s delays | P1 | REQ-013 | M3 |

### Build 3 Tests

| ID | Test | Expected | Priority | Maps To | Milestone |
|---|---|---|---|---|---|
| B3-01 | test_pipeline_e2e | All phases complete | P0 | REQ-026, TEST-011 | M4 |
| B3-02 | test_deploy_and_health | 3/3 healthy | P0 | REQ-021, REQ-026 | M4 |
| B3-03 | test_schemathesis_violations | Contract violations detected | P1 | REQ-026, REQ-028 | M4 |
| B3-04 | test_gate_layer_order | L1 before L2 before L3 before L4 | P0 | REQ-027 | M4 |
| B3-05 | test_cli_commands | All 8 commands registered and callable: init, plan, build, integrate, verify, run, status, resume | P1 | TEST-012 | M4 |
| B3-06 | test_compose_generation | Valid docker-compose.yml produced | P0 | WIRE-017 | M4 |
| B3-07 | test_traefik_routing | PathPrefix labels route correctly | P1 | WIRE-019 | M4 |
| B3-08 | test_state_persistence | Save/load roundtrip preserves all fields | P0 | TEST-012, TEST-001 | M1, M4 |
| B3-09 | test_graceful_shutdown | State saved on SIGINT | P1 | TEST-012 | M4 |
| B3-10 | test_budget_tracking | Cost accumulated across phases | P2 | REQ-042 | M6 |

### Cross-Build Integration Tests

| ID | Test | Builds | Priority | Maps To | Milestone |
|---|---|---|---|---|---|
| X-01 | test_mcp_b1_to_b2_contract_engine | B1, B2 | P0 | REQ-013, WIRE-009 | M2, M3 |
| X-02 | test_mcp_b1_to_b2_codebase_intel | B1, B2 | P0 | REQ-014, WIRE-010 | M2, M3 |
| X-03 | test_mcp_b1_to_b3_architect | B1, B3 | P0 | REQ-015, WIRE-011 | M3 |
| X-04 | test_subprocess_b3_to_b2 | B2, B3 | P0 | REQ-016, TEST-010 | M3 |
| X-05 | test_state_json_contract | B2, B3 | P0 | REQ-016 | M3 |
| X-06 | test_config_generation_compat | B2, B3 | P0 | REQ-018 | M3 |
| X-07 | test_fix_instructions_consumed | B2, B3 | P1 | TEST-013 | M5 |
| X-08 | test_docker_compose_merge | B1, B3 | P1 | WIRE-017 | M4 |
| X-09 | test_quality_gate_l1_builder_result | B2, B3 | P1 | REQ-027 | M4 |
| X-10 | test_quality_gate_l3_generated_code | B2, B3 | P1 | REQ-027 | M4 |

> **Traceability Note:** All TEST-xxx items (TEST-001 through TEST-018) must have at least one matrix entry. Orphaned entries in either direction are bugs.

---

## Docker Compose Topology

### Network Architecture

> **Note**: Build 1 standalone uses a single `super-team-net` bridge network. When integrated into the full system (Run 4), the docker-compose.run4.yml overlay (Tier 4) adds network overrides to place Build 1 services on both `frontend` and `backend` networks. The topology below describes the **integrated** system after the 5-file compose merge.

```
                     HOST (Port 80, 8080)
                          |
                +-------- | ----------+
                |     FRONTEND NET    |
                |  traefik, architect,|
                |  contract-engine,   |
                |  codebase-intel,    |
                |  generated services |
                +----------+----------+
                           |
                +----------+----------+
                |     BACKEND NET     |
                |  postgres, redis,   |
                |  architect,         |
                |  contract-engine,   |
                |  codebase-intel,    |
                |  generated services |
                +---------------------+
```

### Compose Files (5-file merge)

| File | Tier | Services |
|------|------|----------|
| docker-compose.infra.yml | 0 | postgres (16-alpine), redis (7-alpine) |
| docker-compose.build1.yml | 1 | architect, contract-engine, codebase-intelligence |
| docker-compose.traefik.yml | 2 | traefik (v3.6) |
| docker-compose.generated.yml | 3 | auth-service, order-service, notification-service |
| docker-compose.run4.yml | 4 | Cross-build wiring overrides (Traefik labels, debug logging) |

### Health Check Cascade

```
Tier 0: postgres, redis (service_healthy)
    ↓
Tier 1: contract-engine (service_healthy)
    ↓
Tier 2: architect, codebase-intelligence (service_healthy)
    ↓
Tier 3: generated services (service_healthy)
    ↓
Tier 4: traefik (service_healthy)
```

### Port Assignments

| Service | Internal | External | Protocol |
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

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| ChromaDB first-download timeout (80MB model) | Medium | Codebase Intelligence MCP fails to start | Set mcp_first_start_timeout_ms: 120000; pre-download in Docker build |
| Architect HTTP call to Contract Engine fails | Medium | get_contracts_for_service returns empty | Ensure Docker Compose is up before MCP testing |
| Nested asyncio.run() in Build 3 calling Build 2 | High | RuntimeError | Use asyncio.create_subprocess_exec (subprocess isolation) |
| Docker Compose v1 vs v2 | Medium | docker-compose not found | Use `docker compose` (v2), document requirement |
| Builder timeout on large PRD | Medium | 30-min default insufficient | Configure builder_timeout_s: 3600 for initial runs |
| MCP SDK version mismatch | Low | Protocol incompatibility | Pin mcp>=1.25,<2 in both Build 1 and Build 2 |
| Windows process management | Medium | Orphan MCP server processes | Use process.terminate() + process.kill() with timeout |

---

## Appendix A: MCP Server Configuration

Build 1's `.mcp.json` (single source of truth):

```json
{
  "mcpServers": {
    "architect": {
      "command": "python",
      "args": ["-m", "src.architect.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/architect.db",
        "CONTRACT_ENGINE_URL": "http://localhost:8002"
      }
    },
    "contract-engine": {
      "command": "python",
      "args": ["-m", "src.contract_engine.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/contracts.db"
      }
    },
    "codebase-intelligence": {
      "command": "python",
      "args": ["-m", "src.codebase_intelligence.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/symbols.db",
        "CHROMA_PATH": "./data/chroma",
        "GRAPH_PATH": "./data/graph.json"
      }
    }
  }
}
```

## Appendix B: State Machine Transitions (Build 3)

| # | Trigger | Source | Dest | Guard | Cross-Build Dependency |
|---|---------|--------|------|-------|----------------------|
| 1 | start_architect | init | architect_running | prd_loaded | Build 1 Architect MCP |
| 2 | architect_done | architect_running | architect_review | has_service_map | Build 1 output artifacts |
| 3 | approve_architecture | architect_review | contracts_registering | architecture_valid | Build 1 validation |
| 4 | contracts_ready | contracts_registering | builders_running | contracts_valid | Build 1 Contract Engine MCP |
| 5 | builders_done | builders_running | builders_complete | any_builder_success | Build 2 STATE.json |
| 6 | start_integration | builders_complete | integrating | has_successful_builds | Build 2 output dirs |
| 7 | integration_done | integrating | quality_gate | integration_ran | Build 1 services (Docker) |
| 8 | quality_passed | quality_gate | complete | all_gates_passed | None |
| 9 | quality_failed | quality_gate | fix_pass | has_violations | None |
| 10 | fix_done | fix_pass | quality_gate | fix_applied | Build 2 fix subprocess |
| 11 | fail | [non-terminal] | failed | unrecoverable_error | None |
| 12 | retry_architect | architect_running | architect_running | retries_remaining | Build 1 Architect MCP |
| 13 | skip_contracts | contracts_registering | builders_running | no_contracts_needed | None |

## Appendix C: Checklist Summary

Total checklist items: **120**
- REQ-xxx: 42
- TECH-xxx: 9
- INT-xxx: 7
- WIRE-xxx: 21
- SVC-xxx: 20
- TEST-xxx: 18
- SEC-xxx: 3
