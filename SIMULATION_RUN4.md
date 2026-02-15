# RUN4 Pipeline Simulation Report

> Generated: 2026-02-15
> PRD: `prompts/RUN4_PRD.md` (End-to-End Integration, Verification & Audit)
> Pipeline: agent-team v15.0

---

## Executive Summary

RUN4 is a **verification/audit run** (NOT a build) that wires 3 independently-built systems together and produces SUPER_TEAM_AUDIT_REPORT.md. It creates ~5K LOC of test infrastructure, fixtures, and audit tooling.

**Simulation Result**: 2 BLOCKERS, 8 WARNINGS, 4 OPTIMIZATIONS

The two blockers are both config-level issues that must be fixed before launch. The warnings are non-fatal but will produce confusing output or wasted cost. The optimizations can save $5-15.

---

## BLOCKERS

### BLOCKER-1: Config `depth: thorough` crashes `_dict_to_config()`

**Severity**: CRITICAL — pipeline will not start
**Location**: `config.yaml` template in PRD (lines 78-120) vs `config.py:888-901`

The PRD's config template has:
```yaml
depth: thorough
```

In `_dict_to_config()` at `config.py:888`:
```python
if "depth" in data:
    d = data["depth"]  # d = "thorough" (a string!)
    scan_scope_mode = d.get("scan_scope_mode", ...)  # AttributeError: str has no .get()
```

When `depth` is a plain string (not a dict), `_dict_to_config` crashes with `AttributeError` because it calls `.get()` on a string.

**Fix**: Change the config template to either:
```yaml
# Option A: dict format
depth:
  default: thorough

# Option B: use CLI flag instead, remove depth from YAML
# python -m agent_team --prd prompts/RUN4_PRD.md --depth thorough
```

### BLOCKER-2: PRD mode auto-overrides depth to "exhaustive"

**Severity**: HIGH — wrong depth level applied
**Location**: `cli.py:4551-4554`

```python
depth_override = args.depth
if not depth_override and (interview_scope == "COMPLEX" or args.prd):
    depth_override = "exhaustive"
```

When `--prd` is provided without explicit `--depth`, the CLI auto-overrides to "exhaustive". RUN4 wants "thorough" (the PRD config says so). Without explicit `--depth thorough` on the command line, the pipeline runs at exhaustive depth, which:
- Enables browser testing (unwanted for RUN4)
- Sets max E2E fix retries to 3 instead of config's 3 (same here, but principle matters)
- Sets max_scan_fix_passes to 2
- Sets tech research max_queries_per_tech to 6 instead of 4

**Fix**: User MUST invoke with explicit `--depth thorough`:
```bash
python -m agent_team --prd prompts/RUN4_PRD.md --depth thorough --cwd /path/to/super-team
```

---

## WARNINGS

### WARNING-1: API Contract Scanner will parse non-HTTP SVC tables

**Severity**: MEDIUM — false positive risk
**Location**: `quality_checks.py:2781-2832` (`_parse_svc_table`)

RUN4's M2 SVC table uses a 6-column MCP format:
```
| SVC-001 | ArchitectClient.decompose(prd_text) | Architect | decompose | { prd_text: string } | DecompositionResult { ... } |
```

The scanner's `_parse_svc_table` matches any `| SVC-xxx |` row and interprets 6-column rows as:
- cells[1] = frontend_service_method (gets "ArchitectClient.decompose(prd_text)" -- OK)
- cells[2] = backend_endpoint (gets "Architect" -- WRONG, this is MCP server name)
- cells[3] = http_method (gets "decompose" -- WRONG, this is MCP tool name)

The `_parse_field_schema` will extract field names from the DTO columns (cells[4] and cells[5]). Since RUN4 has no traditional frontend/backend directory structure, the `_check_backend_fields` and `_check_frontend_fields` functions will likely find no matching files and produce zero violations.

**Risk**: LOW in practice because RUN4 doesn't have traditional web app file structure. But the scan will waste time parsing 20 SVC rows with nonsensical results.

**PRD mitigation**: The PRD includes an explicit reconciliation note: "_parse_svc_table() API contract scanner targets HTTP wiring and does not apply to MCP tool wiring." This is documentation-only; the scanner has no mechanism to skip non-HTTP tables.

The M3 SVC table has a completely different 6-column format (`SVC-ID | Caller | Command | Input | Output | Verification`) which will also be mis-parsed. Same low-risk conclusion.

### WARNING-2: Mock Data Scan will flag test fixtures

**Severity**: LOW — informational noise
**Location**: `quality_checks.py` MOCK-001..008 patterns

RUN4 creates intentional mock/fixture data:
- `mock_mcp_session` pytest fixture (INT-002)
- `make_mcp_result(data, is_error)` helper (INT-003)
- Sample PRD, OpenAPI specs, AsyncAPI specs, Pact contracts (REQ-004..008)

The MOCK-001..008 regex patterns scan `services/`, `src/`, `lib/`, `app/` directories. RUN4's source files live in `src/run4/` and `tests/run4/`. The `src/run4/` path matches the `src/` service pattern, so files like `src/run4/mcp_health.py` or `src/run4/builder.py` would be scanned.

However, mock data scan patterns target things like `Observable.of(`, `BehaviorSubject`, hardcoded arrays — not pytest fixtures. The risk of actual MOCK pattern matches is LOW.

**Fix (optional)**: Config already has `mock_data_scan: true` which is fine. No action needed unless false positives appear.

### WARNING-3: E2E Testing Phase may falsely detect FastAPI backend

**Severity**: MEDIUM — wasted cost if triggered
**Location**: `e2e_testing.py:60-100` (`detect_app_type`) and `cli.py:5681-5919`

RUN4's `requirements.txt` (or `pyproject.toml`) will include FastAPI as a dependency (for the TaskTracker sample app). `detect_app_type()` checks for FastAPI in requirements and would set `has_backend = True, backend_framework = "fastapi"`.

If backend is detected, the E2E phase will attempt to:
1. Run `_run_backend_e2e_tests()` which deploys a sub-orchestrator to write and run API tests
2. Try to start the FastAPI server and test endpoints

But RUN4 is a TEST FRAMEWORK, not a running API. There is no `uvicorn` command or API server to test. The sub-orchestrator would either:
- Fail to find/start a server (E2E phase fails gracefully with warning)
- Attempt to write tests for non-existent endpoints

The config has `e2e_testing.enabled: true` and `backend_api_tests: true`, which is intentional for running RUN4's own E2E verification. But the pipeline's built-in E2E phase runs GENERIC API tests, not RUN4's custom tests.

**Impact**: ~$3-8 wasted on a sub-orchestrator session that can't find a running API.

**Fix**: Add `skip_if_no_api: true` (already default). If `detect_app_type` correctly identifies that there's no server start command, it may skip. But FastAPI detection could override this.

### WARNING-4: Browser Testing auto-enabled by depth gating

**Severity**: LOW — will skip gracefully
**Location**: `config.py:581-583` (thorough depth gating)

With "thorough" depth + prd_mode, `apply_depth_quality_gating` auto-enables browser testing:
```python
if prd_mode or config.milestone.enabled:
    _gate("browser_testing.enabled", True, ...)
    _gate("browser_testing.max_fix_retries", 3, ...)
```

RUN4 has NO frontend. The browser testing phase will:
1. Try to detect app type (no frontend found)
2. Attempt startup agent (no start command)
3. Likely skip with a warning

**Impact**: Minimal — maybe $1-2 for a failed startup attempt.

**Fix**: Add `browser_testing: enabled: false` to the config template to prevent depth gating from enabling it.

### WARNING-5: All requirements have `review_cycles: 0` — recovery pass will trigger

**Severity**: MEDIUM — adds ~$3-5 per milestone
**Location**: `cli.py` GATE 5 enforcement, all RUN4 requirements

Every requirement in RUN4's PRD has `(review_cycles: 0)`. This means:
1. The milestone orchestrator builds the code
2. Post-orchestration, the system checks `review_cycles == 0`
3. GATE 5 forces a mandatory review-only recovery pass
4. The recovery pass deploys the review fleet, which increments review_cycles

This is BY DESIGN — review_cycles starts at 0 and gets incremented by reviewers. But for RUN4's 120 checklist items across 6 milestones, this means 6 mandatory recovery passes at ~$3-5 each = ~$18-30 extra cost.

The PRD estimates $36-66 total. The recovery passes could push this to $54-96.

**Fix**: No code fix needed. This is expected behavior. But the PRD's cost estimate should account for recovery passes.

### WARNING-6: Milestone execution order is serial (max_parallel = 1)

**Severity**: LOW — missed optimization
**Location**: `config.py:282` (`max_parallel_milestones: int = 1`)

The PRD states M2 and M3 can run in parallel (both depend only on M1). But the config doesn't set `max_parallel_milestones: 2`. The default is 1, so M2 and M3 run serially.

**Impact**: ~1-2 extra hours of wall-clock time.

**Fix**: Add `max_parallel_milestones: 2` to the milestone config if parallel execution is desired.

### WARNING-7: PRD size (40KB) is below chunking threshold

**Severity**: INFO — no action needed
**Location**: `prd_chunking.py:49` (threshold = 50KB)

RUN4's PRD is ~40KB, below the 50KB chunking threshold. Decomposition will process the full PRD in a single pass. This is fine — 40KB fits within context.

### WARNING-8: UI_REQUIREMENTS.md fallback generation is wasteful

**Severity**: LOW — $0.50-1 wasted
**Location**: `cli.py:4414-4458` (Phase 0.6 fallback)

RUN4 has no frontend, but Phase 0.6 will generate a fallback UI_REQUIREMENTS.md by default (since `design_reference.fallback_generation` defaults to `True`). The config doesn't disable this.

The generated doc will contain generic UI tokens that are irrelevant to RUN4. `ui_compliance_scan: false` in the config means it won't trigger false violations, but the generation step wastes a small amount of cost.

**Fix**: Add `design_reference: require_ui_doc: false` to config, or `design_reference: fallback_generation: false`.

---

## OPTIMIZATIONS

### OPT-1: Disable irrelevant scans to save $3-5

RUN4 is a Python test framework, not a web application. Several scans are irrelevant:

```yaml
# Add to config.yaml
integrity_scans:
  asset_scan: false        # No static assets in test framework

database_scans:
  dual_orm_scan: false     # No ORM layer
  default_value_scan: false
  relationship_scan: false

post_orchestration_scans:
  silent_data_loss_scan: false  # No CQRS
  endpoint_xref_scan: false     # No frontend-backend endpoints
```

### OPT-2: Tech research should prioritize Testcontainers + Schemathesis

**Value**: HIGH — these are less common libraries

The tech research phase (Phase 1.5) will detect pytest, httpx, FastAPI, Docker, PostgreSQL, Redis, etc. Most of these are well-known. But Testcontainers (Python) and Schemathesis are specialized libraries where Context7 documentation would be most valuable.

**Recommendation**: Ensure the tech stack detector picks up "Testcontainers" and "Schemathesis" from the PRD. The `_TECHNOLOGY_RE` regex in `config.py` does NOT include these libraries. They will only be detected if `detect_tech_stack()` in `tech_research.py` has broader detection.

### OPT-3: Add `--cwd` to invocation pointing to super-team root

```bash
python -m agent_team \
  --prd prompts/RUN4_PRD.md \
  --depth thorough \
  --cwd /path/to/super-team
```

RUN4 creates code IN the super-team project (under `src/run4/` and `tests/run4/`). The `--cwd` must point to the super-team project root so that:
1. Build 1/2/3 code is accessible for the agent to reference
2. Docker compose files exist for inspection
3. Integration tests can find MCP servers

Without `--cwd`, the agent creates files in the current directory, disconnected from Build 1/2/3.

### OPT-4: Pre-create `.agent-team/` directory structure

Before launching RUN4, create:
```
super-team/.agent-team/
super-team/.agent-team/milestones/
```

This prevents decomposition from failing on directory creation race conditions (unlikely but possible on Windows).

---

## Phase-by-Phase Trace

### Phase 0: Config + Setup
| Step | Result | Issues |
|------|--------|--------|
| Load config.yaml | **CRASH** | BLOCKER-1: `depth: thorough` is string, not dict |
| Parse `run4:` section | OK | Unknown keys silently ignored by `_dict_to_config` |
| PRD mode detection | OK | `--prd` sets `_is_prd_mode = True` |
| Depth resolution | **WRONG** | BLOCKER-2: Auto-overrides to "exhaustive" without `--depth` |
| Milestone detection | OK | `milestone.enabled: true` + prd_mode = `_use_milestones = True` |
| Depth quality gating | Mostly OK | Browser testing auto-enabled (WARNING-4) |
| Codebase map | OK | Scans CWD, finds Build 1/2/3 code if `--cwd` correct |
| Design extraction | Wasteful | WARNING-8: Generates irrelevant UI doc |
| Constraint extraction | OK | Extracts prohibitions/requirements from PRD text |

### Phase 1: Decomposition
| Step | Result | Issues |
|------|--------|--------|
| PRD size check | OK | 40KB < 50KB threshold (WARNING-7) |
| MASTER_PLAN.md creation | OK | PRD has clear `## Milestone N:` headers |
| Milestone parsing | OK | `_RE_MILESTONE_HEADER` matches h2-h4 |
| Dependency parsing | OK | `_parse_deps` handles "milestone-1, milestone-2" format |
| Milestone count | OK | 6 milestones < 30 threshold |

### Phase 1.5: Tech Research
| Step | Result | Issues |
|------|--------|--------|
| Stack detection | Partial | OPT-2: May miss Testcontainers/Schemathesis |
| Context7 queries | OK | Generates queries for detected techs |
| Research summary | OK | Injected into milestone execution prompts |

### Phase 2: Milestone Execution (6 milestones)
| Milestone | Code Gen | Test Execution | Issues |
|-----------|----------|---------------|--------|
| M1: Infrastructure | OK | Unit tests pass | WARNING-5: Recovery pass triggered |
| M2: MCP Wiring | OK | Tests FAIL without Build 1 | Tests need live MCP servers |
| M3: Builder Wiring | OK | Tests partial | Some need real Build 2 CLI |
| M4: E2E Pipeline | OK | Tests FAIL without Docker | Docker + all services required |
| M5: Fix Pass | OK | Unit tests pass | Logic tests work with mocks |
| M6: Audit Report | OK | Unit tests pass | Pure computation |

### Phase 3: Post-Orchestration Convergence
| Step | Result | Issues |
|------|--------|--------|
| Convergence check | Health varies | Depends on how many items reviewers marked [x] |
| Recovery passes | Triggered | WARNING-5: 0 review_cycles forces recovery |

### Phase 4: Post-Orchestration Scans
| Scan | Result | Issues |
|------|--------|--------|
| Mock data scan | Low FP risk | WARNING-2: Test fixtures in src/run4/ |
| UI compliance scan | SKIPPED | Config: `ui_compliance_scan: false` |
| Deployment scan | Useful | docker-compose files present |
| Asset scan | Low value | No static assets |
| PRD reconciliation | Useful | Verifies requirement coverage |
| Database scans | No value | No ORM layer (OPT-1) |
| API contract scan | Confusing | WARNING-1: Non-HTTP SVC tables mis-parsed |
| Silent data loss | No value | No CQRS (OPT-1) |
| Endpoint XREF | No value | No frontend (OPT-1) |

### Phase 5: E2E Testing
| Step | Result | Issues |
|------|--------|--------|
| App type detection | May false-detect | WARNING-3: FastAPI in deps |
| Backend E2E | Likely fails | No running API server |
| Frontend E2E | SKIPPED | Config: `frontend_playwright_tests: false` |

### Phase 6: Browser Testing
| Step | Result | Issues |
|------|--------|--------|
| Auto-enabled | Yes (thorough + prd) | WARNING-4 |
| Execution | SKIPPED | No frontend detected |

---

## Recommended Config Fixes

```yaml
# FIXED config.yaml for RUN4
depth:
  default: thorough          # FIX BLOCKER-1: dict format, not plain string

run4:
  build1_project_root: "../super-team"
  build2_project_root: "../agent-team"
  build3_project_root: "../super-team"
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
  api_contract_scan: true        # Will produce some noise from MCP tables
  silent_data_loss_scan: false   # FIX OPT-1: No CQRS
  endpoint_xref_scan: false      # FIX OPT-1: No frontend

design_reference:
  fallback_generation: false     # FIX WARNING-8: No frontend

browser_testing:
  enabled: false                 # FIX WARNING-4: No frontend

integrity_scans:
  asset_scan: false              # FIX OPT-1: No static assets

database_scans:
  dual_orm_scan: false           # FIX OPT-1: No ORM
  default_value_scan: false
  relationship_scan: false

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 3
```

And the invocation command:
```bash
python -m agent_team \
  --prd prompts/RUN4_PRD.md \
  --depth thorough \
  --cwd /path/to/super-team
```

---

## Cost Estimate (Revised)

| Phase | Original Estimate | Simulation Estimate | Notes |
|-------|------------------|--------------------|----|
| Config + Setup | $0 | $0.50-1 | Fallback UI doc generation |
| Decomposition | $3-5 | $3-5 | Standard |
| Tech Research | $1-2 | $1-2 | Useful for Schemathesis/Testcontainers |
| M1 Execution | $4-6 | $5-8 | +recovery pass |
| M2 Execution | $5-8 | $6-11 | +recovery pass, test failures |
| M3 Execution | $4-7 | $5-10 | +recovery pass |
| M4 Execution | $6-10 | $7-13 | +recovery pass, Docker complexity |
| M5 Execution | $4-7 | $5-10 | +recovery pass |
| M6 Execution | $3-5 | $4-7 | +recovery pass |
| Post-orch scans | $2-4 | $2-4 | Some wasted on irrelevant scans |
| E2E Testing | $3-6 | $3-6 | May fail if no running API |
| Browser Testing | $0 | $0-1 | Should be disabled |
| **Total** | **$36-66** | **$42-78** | Recovery passes add ~$18-30 |

---

## Key Architectural Insight

RUN4 is fundamentally different from a typical agent-team build:

1. **It's an AUDIT, not a build** — the agent-team is designed for building software from PRDs, but RUN4 builds TEST INFRASTRUCTURE that verifies other builds.

2. **Cross-project dependencies** — RUN4 needs Build 1/2/3 to be COMPLETE and ACCESSIBLE. The agent-team has no native concept of cross-project dependencies. This is handled entirely by:
   - `--cwd` pointing to the super-team directory (where all builds live)
   - The `run4:` config section (parsed by RUN4's own code, not agent-team)

3. **Test execution vs code generation** — The agent-team generates code + runs basic tests. But RUN4's tests require RUNNING SERVICES (Docker, MCP servers, API endpoints). The agent-team's test-runner agent will attempt to run these tests, and many will fail because the services aren't running during build.

4. **The agent must understand scope** — The decomposition and milestone execution prompts must convey that this is a verification run. The PRD's `## Project Overview` section clearly states this, but whether the LLM maintains this context through 6 milestones is uncertain.

This is the HARDEST type of project for agent-team: it crosses build boundaries, requires running infrastructure, and produces test code (not application code). The pipeline's quality scans are designed for web applications and will produce irrelevant or confusing output for a test framework project.
