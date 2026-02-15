# BUILD3 Pipeline Simulation Report

## Summary

BUILD3_PRD.md (Integrator + Quality Gate + Super Orchestrator) is the largest, most complex, and riskiest PRD in the Super Agent Team platform. This simulation traces it through every phase of the agent-team pipeline, identifying blockers, warnings, and optimization opportunities.

**PRD Stats:**
- File size: **106,219 bytes** (745 lines)
- Milestones: 7 (M1-M7)
- Requirements: 70 REQ-xxx + 32 TECH-xxx + 22 WIRE-xxx + 40 TEST-xxx + 8 INT-xxx + 4 SEC-xxx + 11 SVC-xxx
- Estimated LOC: ~22,800 (from PRD architecture section)
- Tech stack: Python 3.12, pact-python 3.2.1+, Schemathesis 4.x, transitions 0.9.2+, Typer, Traefik v3.6, Docker Compose v2, httpx, FastAPI, Rich, PyJWT, opentelemetry-api

---

## Phase 0: Configuration

### PRD Chunking

**BLOCKER-01: PRD WILL trigger chunking (106KB > 50KB threshold)**

The PRD is 106,219 bytes, which exceeds the 50,000-byte chunking threshold (`prd_chunking.py:detect_large_prd()`). When chunking is enabled (default), `create_prd_chunks()` will split the PRD on `#` and `##` headings.

**Problem**: The PRD has 7 milestone sections at `##` level, plus Technology Stack, Project Structure, Status Registry, Milestone Dependency Graph, Scan Code Reference, State Machine Transitions Reference, and Architecture Decision sections. The chunking algorithm (`_find_section_boundaries`) splits on `heading_level <= 2`, which means milestones will become separate chunks.

**Impact**: The section detection patterns in `_SECTION_PATTERNS` will classify these chunks as:
- M1 "Shared Models..." -> "general" (no pattern match for "models" or "state machine")
- M2 "Contract Compliance Verification" -> "general" (no "api" match in title)
- M3 "Cross-Service Integration Tests" -> "testing" (matches "tests")
- M4 "Quality Gate" -> "general" (matches nothing)
- M5 "Super Orchestrator Pipeline" -> "general"
- M6 "CLI + Display" -> "general"
- M7 "End-to-End Verification" -> "testing"

Multiple chunks will get the same section name "general" causing deduplication suffixes (general, general_2, general_3, general_4). The focus descriptions will be generic ("Analyze this section for relevant requirements") instead of milestone-specific.

**Severity**: WARNING. Chunking still works mechanically, but the focus descriptions are suboptimal. The orchestrator will still read all chunks. The milestone decomposition phase will re-parse the full PRD anyway.

**Recommendation**: Set `prd_chunking.threshold: 120000` in config.yaml to disable chunking for this PRD, OR the pipeline handles it acceptably since milestone mode overrides chunking behavior.

### Config Requirements

Recommended `config.yaml`:
```yaml
depth:
  default: exhaustive

milestone:
  enabled: true
  max_parallel_milestones: 1  # M2+M3 can be 2, but safer at 1
  health_gate: true
  wiring_check: true
  review_recovery_retries: 3
  orchestrator_direct_integration: true

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false  # No frontend!
  skip_if_no_frontend: true

browser_testing:
  enabled: false  # No browser UI

integrity_scans:
  deployment_scan: true   # BUILD3 generates docker-compose
  asset_scan: false       # No static assets
  prd_reconciliation: true

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false  # No UI
  api_contract_scan: true
  silent_data_loss_scan: false  # No CQRS
  endpoint_xref_scan: false    # No frontend-backend xref

tech_research:
  enabled: true
  max_techs: 8
  max_queries_per_tech: 6  # exhaustive
  expanded_queries: true
```

---

## Phase 0.5: Design Reference Extraction

**WARNING-01: Design extraction will run unnecessarily**

`cli.py` Phase 0.6 runs design reference extraction based on `config.design_reference.require_ui_doc` (default True) and the presence of design URLs. BUILD3 has NO frontend, NO UI, NO design URLs.

**What happens**: With no URLs extracted, the pipeline will:
1. Skip Firecrawl extraction (no URLs)
2. Potentially call `generate_fallback_ui_requirements()` which produces a heuristic `UI_REQUIREMENTS.md`
3. `_infer_design_direction()` will match "minimal_modern" (default) since BUILD3 task text has no design keywords

**Impact**: A fallback `UI_REQUIREMENTS.md` will be generated containing color systems, typography, spacing, etc. that are completely irrelevant to a CLI tool. This is harmless but wastes ~$0.50 of budget and produces a misleading artifact.

**Recommendation**: Set `design_reference.require_ui_doc: false` in config.yaml. This prevents the fallback from running.

---

## Phase 1: Tech Stack Research

**BLOCKER-02: Critical technologies MISSING from detection**

`detect_tech_stack()` in `tech_research.py` has NO patterns for:
- **pact-python** - Not in `_PYTHON_PACKAGE_MAP` (only has django, fastapi, flask, sqlalchemy, prisma, pytest, psycopg2, psycopg, pymongo, redis, celery)
- **schemathesis** - Not in `_PYTHON_PACKAGE_MAP`
- **transitions** (AsyncMachine) - Not in `_PYTHON_PACKAGE_MAP`
- **typer** - Not in `_PYTHON_PACKAGE_MAP`
- **traefik** - Not in `_TEXT_TECH_PATTERNS`
- **docker-compose** - Not in `_TEXT_TECH_PATTERNS`
- **httpx** - Not in `_PYTHON_PACKAGE_MAP`
- **opentelemetry** - Not in `_PYTHON_PACKAGE_MAP`
- **rich** - Not in `_PYTHON_PACKAGE_MAP`

**What WILL be detected** (from PRD text via `_TEXT_TECH_PATTERNS`):
- FastAPI (backend_framework) - matches `\bFastAPI\b`
- Python (language) - matches `\bPython\b`
- Pytest (testing) - matches `\bPytest\b`
- PostgreSQL (database) - matches `\bPostgreSQL\b`
- Redis (database) - matches `\bRedis\b`
- Docker (no pattern in text detection!)

**Text detection will also find** (if the PRD text is passed):
- TypeScript (from mentions in PRD like "camelCase" field naming tests)

**Result**: Out of BUILD3's ~14 critical technologies, only 4-5 will be detected. The 3 most critical (pact-python v3, schemathesis 4.x, transitions AsyncMachine) are completely invisible to detection.

**Context7 Research Impact**: Even if detected, Context7 may not have docs for:
- **pact-python v3** - This is a relatively new Rust FFI-based rewrite. Context7 may have v2 docs which use completely different API (Pact, not Verifier). The PRD has extensive inline documentation of the v3 API precisely because it is so poorly documented.
- **schemathesis 4.x** - API changed from 3.x. `get_all_operations()` vs `schema.items()` etc.
- **transitions AsyncMachine** - Niche library. May not be in Context7 at all.

**Severity**: BLOCKER. The tech research phase will produce minimal useful output for the technologies that matter most. The agent will have to rely on the PRD's inline technical documentation (which is thankfully very detailed).

**Mitigation**: The PRD itself contains extremely detailed API usage notes for pact-python v3 (REQ-021, TECH-013), schemathesis (REQ-019, TECH-011, TECH-012), and transitions (REQ-011, TECH-005). These are embedded directly in the requirements. If the code-writer reads REQUIREMENTS.md carefully, it has all the information needed. The risk is that the code-writer uses training data (which likely has v2 pact-python patterns like `Pact()` constructor, `set_info()`, `set_state_handler()`) instead of the PRD-specified v3 patterns.

---

## Phase 2: Decomposition

**WARNING-02: 7 milestones with complex dependency DAG**

The PRD specifies a specific dependency graph:
```
M1 -> M2, M3 (parallel)
M2, M3 -> M4
M1, M4 -> M5
M5 -> M6
M5, M6 -> M7
```

The decomposition phase parses milestone sections from the PRD and creates MASTER_PLAN.md. The milestone parser (`milestone_manager.py`) reads `## Milestone N:` headings and `- Dependencies:` lines.

**Will the DAG be parsed correctly?** Yes. The PRD uses the standard format:
```
## Milestone 2: Contract Compliance Verification
- ID: milestone-2
- Dependencies: milestone-1
```

The `_RE_MILESTONE_HEADER` regex (now `#{2,4}`) will match these correctly.

**Parallel execution**: `max_parallel_milestones: 1` (recommended) means M2 and M3 will execute sequentially despite being parallelizable. Setting to 2 would allow parallel execution but increases risk of cross-milestone interference.

**WARNING-03: M4 depends on BOTH M2 AND M3**

The pipeline's milestone execution loop processes milestones in dependency order. M4 must wait for both M2 AND M3 to complete. The pipeline handles multi-dependency correctly via the `_get_ready_milestones()` function in `milestone_manager.py`, but this should be verified.

---

## Phase 3: Milestone Execution

### M1: Shared Models, Config, State Machine Engine (34 requirements)

**WARNING-04: `transitions` AsyncMachine is the highest-risk component**

REQ-011 specifies a state machine with 11 states, 13 transitions, guard conditions, and async callbacks using `transitions.extensions.asyncio.AsyncMachine`. Key gotchas documented in PRD:
- Must use `model=model` parameter (omitting causes machine to become model)
- `fail` transition must use explicit source list (not `source="*"`) to prevent `complete -> failed`
- RESUME_TRIGGERS dict with None values for re-execution vs trigger names for advancement
- `queued=True` for transition queueing

**Risk**: The agent's training data likely has basic `transitions.Machine` examples, not `AsyncMachine`. The `transitions.extensions.asyncio` import path is unusual. However, TECH-005 explicitly documents this.

**Prediction**: The code-writer will likely get the basic structure right (the PRD is extremely detailed) but may miss:
1. The `queued=True` parameter (documented but easy to overlook)
2. The `send_event=True` parameter
3. The explicit source list for `fail` transition (may use `"*"` wildcard)

The review cycle should catch these if the reviewer reads the REQUIREMENTS.md carefully.

### M2: Contract Compliance Verification (7 requirements + 4 test blocks)

**BLOCKER-03: pact-python v3 API is a critical risk**

REQ-021 documents the correct v3 API:
```python
from pact.v3.verifier import Verifier
verifier = Verifier(provider_name)  # NOT Verifier() with no args
verifier.add_transport(url=provider_url)  # NOT set_info()
verifier.add_source(str(pf))
verifier.state_handler(handler_function, teardown=True)  # NOT set_state_handler()
verifier.verify()  # Returns Self on success, raises on failure
```

**The agent will almost certainly use the wrong API on first attempt.** Training data has pact-python v2 patterns:
```python
# WRONG v2 patterns the agent will likely use:
pact = Pact(consumer="...", provider="...")  # v2 constructor
pact.set_info(...)  # DOES NOT EXIST in v3
pact.set_state(...)  # DOES NOT EXIST in v3
pact.set_state_handler(...)  # DOES NOT EXIST in v3
```

**Prediction**: First build cycle will use v2 API. Review cycle should catch it since TECH-013 is explicit. Second build cycle may fix it. This alone may consume 2-3 review cycles per the PRD's `review_cycles: 0` annotation (meaning it expects 0 review cycles, which is optimistic).

**BLOCKER-04: Schemathesis API confusion**

REQ-019 documents:
```python
schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)
for api_operation in schema.get_all_operations():
    case = api_operation.make_case()
    response = case.call(base_url=base_url)
    case.validate_response(response)
```

Training data likely has:
```python
# WRONG patterns:
@schema.parametrize()  # This is for test files only, not programmatic
schema.items()  # NOT a schemathesis API
```

Also critical: TECH-012 notes `schemathesis.exceptions.CheckFailed` does NOT exist in 4.x. The correct exception is `schemathesis.failures.FailureGroup`.

**TECH-014a**: Both Schemathesis and Pact are synchronous. Async methods must wrap with `asyncio.to_thread()`. This is documented but the agent may forget to wrap individual calls, especially `case.call()` and `case.validate_response()`.

### M3: Cross-Service Integration Tests (5 requirements)

**WARNING-05: Deterministic chain detection algorithm complexity**

REQ-026 specifies a complex algorithm for generating cross-service test flows from contract schemas. The algorithm involves:
1. Extract response schemas from all POST/PUT endpoints
2. Compute field overlap between (Service A response, Service B request) pairs
3. Build a directed graph of chain links (overlap >= 2)
4. Find all simple paths of length 2+ with max depth 5
5. Sort by path length descending, return top 20

This is implementable but complex. The agent may oversimplify the algorithm (e.g., skip the graph traversal, just check pairwise overlaps without building paths).

### M4: Quality Gate (15 requirements, 40 scan codes)

**WARNING-06: 40 scan codes implementation is massive**

REQ-034 through REQ-042 specify 40 scan codes across 8 categories:
- SEC-001..006 (JWT) - 6 codes
- CORS-001..003 - 3 codes
- LOG-001, LOG-004, LOG-005 - 3 codes
- TRACE-001 - 1 code
- SEC-SECRET-001..012 - 12 codes
- DOCKER-001..008 - 8 codes
- ADV-001..006 - 6 codes
- HEALTH-001 - 1 code

**Risk**: The agent may:
1. Implement fewer than 40 codes (miss some SEC-SECRET patterns)
2. Get regex patterns slightly wrong (the PRD provides exact regex for all 40)
3. Forget `len(ALL_SCAN_CODES) == 40` validation in tests

**Prediction**: Implementation will likely be 80-90% correct on first pass. The review cycle should catch missing codes. The SEC-SECRET patterns are very specific (e.g., `gh[psatr]_[A-Za-z0-9_]{36,}` for GitHub tokens with 5 subtypes) and may be simplified incorrectly.

### M5: Super Orchestrator Pipeline (8 requirements)

**WARNING-07: MCP SDK integration with fallback**

REQ-046 requires MCP stdio transport to communicate with Build 1's Architect:
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
```

With fallback to subprocess + JSON if import fails. The lazy import pattern with try/except ImportError is standard but the agent needs to get the fallback subprocess protocol right.

**BLOCKER-05: `asyncio.run()` nesting risk**

TECH-027 states: "The top-level entry point must call `asyncio.run()` exactly once. All subsequent async calls use `await`. No nested asyncio.run()."

This is the same architectural issue found in agent-team itself (production readiness audit found nested `asyncio.run()` in `_run_review_only()`). The agent building BUILD3 is running INSIDE agent-team, which already has its own event loop. If the agent tries to test BUILD3's `asyncio.run()` during the build phase, it will get "RuntimeError: cannot be called from a running event loop."

**Impact**: Tests in M5 and M7 that call `asyncio.run()` directly will fail during the build. The agent should use `pytest-asyncio` with `asyncio_mode = "auto"` (documented in TECH-032) which handles the event loop correctly for tests. But any integration test that calls the CLI entry point directly may still fail.

### M6: CLI + Display (7 requirements)

**WARNING-08: Rich Group import location**

REQ-059 specifies: `from rich.console import Console, Group`. The PRD explicitly notes `Group` is imported from `rich.console`. In some Rich versions, `Group` was in `rich.renderables.group` or `rich.console`. The agent may import from the wrong module. The PRD is explicit about this.

### M7: End-to-End Verification (10 requirements + 5 test blocks)

**WARNING-09: TEST-036 requires 15 test cases with ALL mocked externals**

REQ-065 specifies: "This test must run entirely with mocked external dependencies (no real Docker, no real MCP servers)." This is correct but complex. The agent must mock:
- MCP stdio transport (Architect, Contract Engine)
- Build 2 agent-team subprocess
- Docker Compose subprocess
- httpx HTTP calls (health checks, service calls)
- Schemathesis (schema loading, validation)
- Pact verifier

This is a large amount of mocking. The agent may struggle with the MCP session mocking pattern.

---

## Phase 4: Post-Orchestration Scans

### Mock Data Scan

**BLOCKER-06: HIGH false positive risk from test fixtures**

BUILD3 specifies test fixture files:
- `tests/fixtures/sample_openapi.yaml`
- `tests/fixtures/sample_pact.json`
- `tests/fixtures/sample_docker_compose.yml`
- `tests/fixtures/sample_prd.md`

The mock data scan (`run_mock_data_scan()` in `quality_checks.py`) uses MOCK-001..008 patterns that scan for:
- `of(` patterns (MOCK-001) - likely in RxJS patterns
- `Promise.resolve` with hardcoded data (MOCK-002)
- Variables named `mock`, `dummy`, `fake`, `stub` (MOCK-003)

**MOCK-003 risk**: The code will have variables like `mock_builder_result`, `mock_service_map`, etc. in test files. The scan SHOULD exclude test files (`tests/` directory), but the regex path check in `run_mock_data_scan()` uses `_RE_SERVICE_PATH` which matches:
```python
_RE_SERVICE_PATH = re.compile(
    r"(?:services?|api|client|http|fetch|axios|providers?|stores?|hooks?)"
    r"[/\\]", re.IGNORECASE
)
```

The fixture and test files should NOT match this pattern. But the `conftest.py` fixtures that create `sample_` prefixed test data could trigger MOCK-003 if they are in directories matching the service path pattern.

**More concerning**: BUILD3 has `src/integrator/pact_manager.py` and `src/integrator/schemathesis_runner.py` which create contract test data. If these files contain template data or example schemas, MOCK-003 could fire.

**Prediction**: 5-15 false positive violations likely. The fix loop will waste 1-2 cycles.

### Deployment Scan

**WARNING-10: Dynamically generated docker-compose files**

BUILD3's `ComposeGenerator.generate()` method PRODUCES docker-compose.yml files at runtime. The deployment scan (`DEPLOY-001..004`) expects to find docker-compose files in the project root and scan them statically.

**What will happen**:
1. The `docker/docker-compose.yml` and `docker/docker-compose.test.yml` static files will be scanned correctly
2. Dynamically generated compose files (output of ComposeGenerator) will NOT be scanned because they don't exist at scan time

This is actually correct behavior -- the deployment scan should check the static infrastructure files, not runtime-generated ones. But the scan may report DEPLOY-001 (port mismatch) or DEPLOY-002 (undefined env vars) for the test compose file that uses `${ENV_VAR}` syntax.

### Database Scan

**WARNING-11: No traditional database, but PostgreSQL references**

BUILD3 uses PostgreSQL as infrastructure (in docker-compose) but its own persistence is JSON files (PipelineState uses `atomic_write_json`). The database scan may:
1. Skip correctly if no ORM files are detected (no Prisma, TypeORM, etc.)
2. But may trigger DB-004 (missing defaults) on the Pydantic/dataclass model files since they look like entity definitions

**Prediction**: 0-3 false positives. Low risk.

### API Contract Scan

**WARNING-12: SVC table references Build 1 and Build 2 types**

BUILD3's SVC table includes entries like:
```
| SVC-005 | run_architect_phase | MCP stdio: python -m src.architect.mcp_server -> decompose | { prd_text: string } | { service_map: ServiceMap (see Build 1 REQ-002), ... } |
```

The `_parse_svc_table()` function will parse these rows. The `_check_backend_fields()` function will try to find `ServiceMap` in the project's source files. Since `ServiceMap` is defined in Build 1's codebase (not BUILD3), this will fail to validate.

**Impact**: API-001 violations for cross-build type references. These are false positives since the types come from Build 1 via MCP, not from BUILD3's own codebase.

**Prediction**: 5-10 false positive API contract violations for cross-build references.

---

## Phase 5: E2E Testing

**BLOCKER-07: BUILD3 is a CLI tool with Docker dependencies, not a web server**

The E2E testing phase (`e2e_testing.py`) is designed for web applications:
- `detect_app_type()` will detect `has_backend=True` (FastAPI for health endpoints), `has_frontend=False`
- `skip_if_no_frontend: true` will correctly skip frontend Playwright tests
- Backend API tests will attempt to start the server: `uvicorn main:app --reload`

**Problem**: BUILD3's main entry point is a Typer CLI (`src/super_orchestrator/cli.py`), not a web server. The FastAPI health endpoints (REQ-046 mentions them) are for the SERVICES that BUILD3 orchestrates, not for BUILD3 itself. The E2E test runner will:
1. Try to start the FastAPI server (which doesn't exist as a standalone server)
2. Fail to find a health check endpoint
3. Mark backend E2E tests as failed

**However**: If `e2e_testing.enabled: true` and `backend_api_tests: true`, the sub-orchestrator will read REQUIREMENTS.md and realize this is a CLI tool. The E2E test agent should pivot to testing the CLI commands via subprocess instead of HTTP. But the prompts (`BACKEND_E2E_PROMPT`) are heavily HTTP-oriented ("REAL HTTP calls", "GET /health", server lifecycle).

**Mitigation**: Set `e2e_testing.backend_api_tests: false` OR trust the E2E agent to adapt. With `max_fix_retries: 3-5`, the agent may figure out it needs CLI testing instead of HTTP testing.

**Alternative**: The M7 milestone (End-to-End Verification) already specifies comprehensive integration tests. These will test the pipeline flow with mocked externals. The E2E phase is somewhat redundant.

**Recommendation**: Set `e2e_testing.enabled: false` and rely on M7's test requirements for integration testing.

---

## Phase 6: Browser Testing

**OPTIMIZATION-01: Correctly skipped**

Browser testing will be correctly skipped for BUILD3 because:
1. `config.browser_testing.enabled: false` (recommended)
2. Even if enabled, `detect_app_type()` returns `has_frontend=False`
3. Even if somehow it starts, the E2E pass rate gate would filter it out since E2E tests won't produce passing results for a CLI app

No issues here.

---

## Cross-Cutting Concerns

### BLOCKER-08: State Machine Library Knowledge Gap

The `transitions` library with `AsyncMachine` is not well-represented in LLM training data. Specific risks:
1. Import path `transitions.extensions.asyncio` vs `transitions.extensions.asyncio.AsyncMachine`
2. `queued=True` parameter semantics
3. Guard condition signature (must accept `EventData` parameter with `send_event=True`)
4. `on_enter_<state>` callback naming convention
5. `auto_transitions=False` meaning
6. `ignore_invalid_triggers` for terminal states

The PRD documents these extensively (REQ-011 is one of the longest requirements). If the code-writer reads it carefully, it should work.

### WARNING-13: Budget Concerns

BUILD3 at "exhaustive" depth with 7 milestones, each potentially consuming 2-3 review cycles, plus fix loops for pact-python and schemathesis API mistakes:
- M1: ~$8-12 (large, many files)
- M2: ~$6-10 (pact/schemathesis complexity, likely 2+ review cycles)
- M3: ~$5-8 (cross-service tests)
- M4: ~$8-12 (40 scan codes)
- M5: ~$6-10 (pipeline orchestration)
- M6: ~$4-6 (CLI + display)
- M7: ~$6-10 (integration tests)
- Post-orchestration: ~$3-5
- Fix loops: ~$5-15

**Estimated total: $51-88**

Set `orchestrator.max_budget_usd: 100` as a safety valve.

### WARNING-14: Parallel Milestone Opportunity Lost

M2 and M3 can run in parallel (both depend only on M1). With `max_parallel_milestones: 1`, the build takes ~30% longer than necessary. With `max_parallel_milestones: 2`, M2 and M3 run simultaneously, saving $5-10 and 30-60 minutes.

**Risk of parallel**: Cross-milestone wiring issues are harder to debug. M2 and M3 have no direct dependency on each other, so parallel should be safe.

---

## Findings Summary

### BLOCKERS (must address before running)

| ID | Finding | Recommendation |
|---|---|---|
| BLOCKER-01 | PRD triggers chunking (106KB > 50KB) with poor section classification | Set `prd_chunking.threshold: 120000` or accept default behavior |
| BLOCKER-02 | Tech research misses pact-python, schemathesis, transitions (0/3 critical libs detected) | Accept: PRD has inline docs. Tech research adds limited value here |
| BLOCKER-03 | pact-python v3 API will likely be wrong on first attempt (training data has v2) | Expect 2-3 review cycles on M2. Budget accordingly |
| BLOCKER-04 | Schemathesis 4.x API confusion (`get_all_operations` vs `schema.items()`, `FailureGroup` vs `CheckFailed`) | Same as above. PRD is explicit but agent may default to training data |
| BLOCKER-05 | `asyncio.run()` nesting risk during test execution | Use `pytest-asyncio` with `asyncio_mode = "auto"` (TECH-032 specifies this) |
| BLOCKER-06 | Mock data scan false positives from test fixtures and contract template code | Set `max_scan_fix_passes: 0` or accept 1-2 wasted fix cycles |
| BLOCKER-07 | E2E phase designed for web servers, BUILD3 is a CLI tool | Set `e2e_testing.enabled: false`, rely on M7's tests |
| BLOCKER-08 | `transitions` AsyncMachine not in agent training data | PRD is explicit enough. Risk is code-writer ignoring PRD details |

### WARNINGS (may cause issues, not fatal)

| ID | Finding | Impact |
|---|---|---|
| WARNING-01 | Design extraction runs unnecessarily (no UI) | Wastes ~$0.50, produces irrelevant UI_REQUIREMENTS.md |
| WARNING-02 | 7 milestones with complex dependency DAG | Parser handles correctly but verify M4's dual dependency |
| WARNING-03 | M4 depends on both M2 AND M3 | Verify `_get_ready_milestones()` handles multi-dependency |
| WARNING-04 | transitions AsyncMachine has many subtle gotchas | PRD documents them; review should catch |
| WARNING-05 | Deterministic chain detection algorithm is complex | Agent may oversimplify; review should catch |
| WARNING-06 | 40 scan codes is massive implementation | Expect 80-90% correct on first pass |
| WARNING-07 | MCP SDK integration with subprocess fallback | Standard pattern but complex |
| WARNING-08 | Rich Group import location | PRD is explicit (`from rich.console import Console, Group`) |
| WARNING-09 | M7 requires mocking 6+ external systems | Complex but achievable |
| WARNING-10 | Deployment scan vs dynamically generated compose files | Static files scanned correctly, runtime ones skipped (correct) |
| WARNING-11 | Database scan on non-database project | 0-3 false positives expected |
| WARNING-12 | API contract scan fails on cross-build type references | 5-10 false positive violations |
| WARNING-13 | Budget estimate $51-88 for exhaustive depth | Set max_budget_usd: 100 |
| WARNING-14 | M2+M3 parallel opportunity with max_parallel_milestones: 1 | 30% slower but safer |

### OPTIMIZATIONS

| ID | Finding | Recommendation |
|---|---|---|
| OPT-01 | Browser testing correctly skipped | No action needed |
| OPT-02 | M2+M3 parallel execution | Set `max_parallel_milestones: 2` if budget allows |
| OPT-03 | Disable irrelevant scans | ui_compliance_scan: false, asset_scan: false, silent_data_loss_scan: false, endpoint_xref_scan: false |
| OPT-04 | PRD chunking threshold | Raise to 120KB to avoid suboptimal chunk classification |

---

## Recommended config.yaml for BUILD3

```yaml
depth:
  default: exhaustive

orchestrator:
  max_budget_usd: 100
  max_turns: 500

milestone:
  enabled: true
  max_parallel_milestones: 2  # M2+M3 parallelism
  health_gate: true
  wiring_check: true
  review_recovery_retries: 3
  orchestrator_direct_integration: true

prd_chunking:
  threshold: 120000  # Avoid suboptimal chunking

design_reference:
  require_ui_doc: false  # No frontend UI

e2e_testing:
  enabled: false  # CLI tool, not web server. M7 handles integration tests.

browser_testing:
  enabled: false  # No browser UI

integrity_scans:
  deployment_scan: true
  asset_scan: false
  prd_reconciliation: true

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false
  api_contract_scan: true
  silent_data_loss_scan: false
  endpoint_xref_scan: false
  max_scan_fix_passes: 1

tech_research:
  enabled: true
  max_techs: 8
  max_queries_per_tech: 6
  expanded_queries: true
```

---

## Critical Path Analysis

1. **M1** (foundation) - ~$8-12, 1-2 review cycles likely
2. **M2+M3** (parallel) - ~$11-18 combined, M2 at highest risk (pact-python v3)
3. **M4** (quality gate) - ~$8-12, 40 scan codes is large but well-specified
4. **M5** (pipeline) - ~$6-10, MCP integration is complex
5. **M6** (CLI) - ~$4-6, straightforward
6. **M7** (verification) - ~$6-10, heavy mocking but well-scoped
7. **Post-orchestration** - ~$3-5, mock data false positives are the main risk

**Total estimated wall-clock time**: 4-6 hours at exhaustive depth with 7 milestones.

**Highest risk milestone**: M2 (Contract Compliance) due to pact-python v3 and schemathesis 4.x API gotchas.

**Second highest risk**: M1 (State Machine) due to transitions AsyncMachine subtleties.
