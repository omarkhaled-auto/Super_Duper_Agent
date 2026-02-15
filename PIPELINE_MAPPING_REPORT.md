# Pipeline Mapping Report: 4 Super Agent Team PRDs vs Agent-Team Pipeline

> Generated: 2026-02-15
> Scope: BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md, RUN4_PRD.md
> Against: agent-team v15.0 (src/agent_team/)

---

## 1. Requirement-Type-to-Handler Mapping

### 1.1 Requirement Prefix Coverage

| Prefix | Meaning | Agent-Team Handler | Status | Notes |
|--------|---------|-------------------|--------|-------|
| REQ-xxx | Functional requirements | Milestone execution prompt (`build_milestone_execution_prompt()` in agents.py) + code-writer/architect prompts | HANDLED | REQ-xxx items are parsed as checkbox items in REQUIREMENTS.md; milestone execution enforces them via the 9-step MILESTONE WORKFLOW |
| TECH-xxx | Technical constraints | Injected into prompts via `code_quality_standards.py` + code-writer/architect prompt sections | PARTIALLY HANDLED | TECH-xxx constraints appear in requirements files but agent-team has no dedicated TECH-xxx scanner. They're enforced by prompt instructions only — no static verification |
| WIRE-xxx | Wiring/integration requirements | Wiring verification in milestone_manager.py (`check_wiring()`) + integration verification step in milestone workflow | PARTIALLY HANDLED | Agent-team has wiring verification but it checks import paths, not the specific cross-module wiring patterns described in WIRE-xxx. The 9-step milestone workflow includes "Integration Verification" but it's prompt-driven, not static-scanned |
| TEST-xxx | Test requirements | E2E testing phase (e2e_testing.py) + test generation prompts | PARTIALLY HANDLED | Agent-team prompts include test writing instructions. E2E phase runs tests. But TEST-xxx with specific minimum test case counts is enforced only via prompts — no static count verification |
| SVC-xxx | Service-to-API wiring | API contract scan (`run_api_contract_scan()` in quality_checks.py) + SVC-xxx table parser | HANDLED | v9.0 implemented 3-layer API contract verification: `_parse_svc_table()` extracts SVC-xxx rows, `_check_backend_fields()`/`_check_frontend_fields()` verify implementation |
| INT-xxx | Integration requirements | No dedicated handler | GAP | INT-xxx requirements are NOT parsed or enforced by any scanner. They appear only in prompt text if the PRD includes them in REQUIREMENTS.md |
| SEC-xxx | Security requirements | No dedicated security scanner | GAP | Agent-team has no SEC-xxx scanner. The mock data scan and UI compliance scan exist but security scanning (JWT, CORS, secrets) is NOT implemented in agent-team |

### 1.2 Handler Details per Agent-Team Module

| Module | What It Handles | What It Misses from These PRDs |
|--------|----------------|-------------------------------|
| `agents.py` | ARCHITECT_PROMPT (SVC-xxx schemas), CODE_WRITER_PROMPT (zero mock data, API compliance), CODE_REVIEWER_PROMPT (API contract field verification), milestone execution (9-step workflow) | No MCP-specific guidance, no state machine guidance, no Pact/Schemathesis guidance, no Docker Compose generation guidance |
| `quality_checks.py` | run_mock_data_scan (MOCK-001..008), run_ui_compliance_scan (UI-001..004), run_e2e_quality_scan (E2E-001..007), run_api_contract_scan (API-001..003), run_dual_orm_scan (DB-001..003), run_default_value_scan (DB-004..005), run_relationship_scan (DB-006..008) | No CONTRACT-001..004, no SEC-xxx, no CORS-xxx, no LOG-xxx, no DOCKER-xxx, no ADV-xxx scan codes |
| `milestone_manager.py` | MASTER_PLAN.md parsing, milestone health checks, convergence aggregation, wiring verification | No contract compliance ratio in health check (Build 2 adds this), no MCP tool verification |
| `config.py` | AgentTeamConfig with depth gating, E2E config, browser testing config, integrity scans, post-orchestration scans, tech research, tracking documents, database scans | Missing: AgentTeamsConfig, ContractEngineConfig, CodebaseIntelligenceConfig, ContractScanConfig (all from Build 2) |
| `e2e_testing.py` | detect_app_type(), backend/frontend E2E test prompts, parse_e2e_results() | No Schemathesis integration, no Pact verification, no contract compliance E2E |
| `cli.py` | Full pipeline: decomposition, milestone execution, review recovery, mock/UI/integrity/E2E/browser scans, fix loops | No Agent Teams backend, no MCP client integration, no contract compliance scanning, no CLAUDE.md generation |

---

## 2. Category 2: Unusual/Unique Patterns

### 2.1 MCP Server Creation (BUILD1)

**Pattern**: BUILD1 requires creating 3 MCP servers from scratch using `mcp>=1.25,<2` SDK with `@mcp.tool()` decorators, `mcp.run(transport="stdio")`.

**Agent-Team Handling**: `mcp_servers.py` has `get_mcp_servers()`, `_playwright_mcp_server()`, `get_context7_only_servers()` — but these configure *consumption* of existing MCP servers. Agent-team does NOT have guidance for *creating* MCP servers.

**Gap**: CRITICAL. Agent-team prompts have no instructions for `@mcp.tool()` patterns, `MCPServer` instantiation, stdio transport setup, or the pattern of MCP-server-as-thin-adapter-over-service-layer. The tech research phase (v14.0) might pick up MCP SDK docs via Context7, but there's no structural enforcement.

**Recommendation**: Add MCP server creation patterns to `code_quality_standards.py` — tool function type hints, docstring requirements, transport selection.

### 2.2 Claude Code Hooks (BUILD2)

**Pattern**: BUILD2 introduces hook scripts (`.claude/settings.local.json`, `.claude/hooks/*.sh`) with agent, command, and async hook types. HookInput JSON parsing, quality gates via exit codes.

**Agent-Team Handling**: NONE. Agent-team has no concept of Claude Code hooks.

**Gap**: HIGH. This is entirely new infrastructure. Agent-team cannot guide hook creation. However, since BUILD2 IS the agent-team upgrade, the hooks module would be added to agent-team itself — this is a self-referential build.

### 2.3 State Machines with `transitions` Library (BUILD3)

**Pattern**: BUILD3 uses `transitions.extensions.asyncio.AsyncMachine` with 11 states, 13 transitions, guard conditions, queued transitions, and `model=model` pattern.

**Agent-Team Handling**: Agent-team's `code_quality_standards.py` has no state machine standards. The tech research phase might find `transitions` docs via Context7.

**Gap**: MEDIUM. The `transitions` library is well-documented but has specific pitfalls (e.g., `model=model` MUST be passed, `auto_transitions=False`, `queued=True`, `fail` transition must exclude terminal states). Agent-team has no state machine-specific quality checks.

**Recommendation**: Tech research phase should query Context7 for `transitions` library docs. Consider adding state machine integrity patterns to code quality standards.

### 2.4 Pact Contract Testing (BUILD3)

**Pattern**: Consumer-driven contracts using `pact-python 3.2.1+` with Pact V4 spec, Rust FFI backend. Specific API: `Verifier(provider_name).add_transport(url=url).add_source(file).state_handler(handler).verify()`.

**Agent-Team Handling**: NONE. No Pact awareness in any agent-team module.

**Gap**: HIGH. Pact v3 API has critical differences from v2 (no `set_info()`, no `set_state_handler()`, `Verifier(name)` not `Verifier()`). Without explicit guidance, the agent will likely use wrong API patterns. Tech research via Context7 might help but the API surface is subtle.

**Recommendation**: Add Pact v3 API patterns as tech research required queries.

### 2.5 Docker Compose Generation (BUILD3)

**Pattern**: `ComposeGenerator` produces docker-compose.yml programmatically with Traefik labels, health checks, depends_on conditions, network separation, volume mounts. Specific Traefik v3 backtick syntax for PathPrefix.

**Agent-Team Handling**: Agent-team has `DEPLOY-001..004` integrity scans in `quality_checks.py` that cross-reference docker-compose files, but these are for *validating* existing compose files, not *generating* them.

**Gap**: MEDIUM. Docker Compose generation is a build task, not a scan. The DEPLOY scans would run post-build to catch issues. The integrity scan should work to catch port mismatches, env var issues, etc.

### 2.6 Cross-Build Dependency Chains (RUN4)

**Pattern**: RUN4 wires 3 independently-built systems. It's NOT a build — it's a verification/audit run. Dependencies: Build 1 services must be running for Build 2 MCP clients, Build 2 CLI must be available for Build 3 subprocess calls.

**Agent-Team Handling**: No concept of cross-build dependencies. Agent-team builds one project at a time.

**Gap**: CRITICAL for RUN4. Agent-team cannot:
- Spawn and manage Build 1 Docker services as prerequisites
- Verify MCP server availability before testing
- Handle 5-file Docker Compose merges
- Run tests that span multiple independently-built codebases

**Recommendation**: RUN4 should use `exhaustive` depth with custom config. The `run4:` config section is intentionally outside AgentTeamConfig (parsed by Run4's own module). Agent-team would build the Run4 test infrastructure, but the actual cross-build wiring tests need the full Docker stack running.

### 2.7 Non-Build PRDs — Verification/Audit Runs (RUN4)

**Pattern**: RUN4 is explicitly marked "Type: Verification + Remediation Run (NOT a build)". It produces test infrastructure and an audit report, not application code.

**Agent-Team Handling**: Agent-team is designed for builds. The decomposition, milestone execution, and convergence system all assume "build something from requirements."

**Gap**: LOW-MEDIUM. The agent-team pipeline still works — it decomposes requirements, writes code (test infrastructure, config, fixtures), runs tests, and converges. The output happens to be test code + audit reports rather than an application. The milestone structure fits (6 milestones, sequential dependencies). The main gap is that agent-team has no "verification mode" that skips code generation and runs only validation.

---

## 3. Scale Analysis

### 3.1 Requirement Volume

| PRD | Milestones | REQ | TECH | WIRE | TEST | SVC | INT | SEC | Total |
|-----|-----------|-----|------|------|------|-----|-----|-----|-------|
| BUILD1 | 8 | 73 | 36 | 24 | 41 | 12 | 6 | 0 | 192 |
| BUILD2 | 6 | 94 | 44 | 17 | 94 | 13 | 20 | 3 | 285 |
| BUILD3 | 7 | 70 | 32 | 22 | 40 | 11 | 8 | 4 | 187 |
| RUN4 | 6 | 42 | 9 | 21 | 18 | 20 | 7 | 3 | 120 |
| **TOTAL** | **27** | **279** | **121** | **84** | **193** | **56** | **41** | **10** | **784** |

### 3.2 Pipeline Capacity Assessment

**Will the pipeline handle 784 requirements across 27 milestones?**

| Factor | Assessment | Risk |
|--------|-----------|------|
| PRD Size | BUILD1 ~28K tokens, BUILD2 ~25K tokens, BUILD3 ~25K tokens, RUN4 ~18K tokens | MEDIUM — each PRD exceeds 50KB threshold, triggering PRD chunking (prd_chunking.py) |
| Milestone Count | 8 milestones (BUILD1) is the largest; agent-team has handled 8+ milestones | LOW — pipeline supports arbitrary milestone counts |
| Requirements per Milestone | BUILD1 M1 has ~12 REQ + 8 TECH + 3 WIRE + 4 TEST = 27 items | LOW — agent-team handles 30+ items per milestone |
| Context Window | With all prompts, requirements, tech research, and codebase map, context could exceed 150K tokens | HIGH — especially for BUILD3 which has 40 scan codes to implement |
| Budget | BUILD1-3: $50-100 each at thorough depth; RUN4: $36-66 | MEDIUM — budget tracking exists but needs calibration |
| Convergence | Complex codebases (tree-sitter, ChromaDB, Schemathesis, Pact) may need many review cycles | HIGH — novel libraries require more iterations |

### 3.3 Bottlenecks

1. **BUILD1 Milestone 5+6 (Codebase Intelligence)**: Most complex — tree-sitter parsing for 4 languages, ChromaDB integration, NetworkX graph analysis. Agent-team has no tree-sitter-specific quality patterns.

2. **BUILD2 Self-Referential Nature**: BUILD2 upgrades agent-team itself. Running agent-team to modify agent-team creates a circular dependency. The builder needs v14.0 behavior while implementing v15.0 features.

3. **BUILD3 Scan Code Volume**: 40 quality gate scan codes across 8 categories. Each needs regex implementation + tests. Agent-team has its own scan codes (MOCK, UI, E2E, API, DB, DEPLOY, ASSET) but BUILD3's are entirely separate.

4. **RUN4 Docker Dependencies**: Requires 3 Build 1 services running + Docker Compose. Agent-team's E2E testing phase supports backend API tests but not multi-service Docker orchestration.

---

## 4. Recommended config.yaml per PRD

### 4.1 BUILD1 config.yaml

```yaml
depth: thorough

milestone:
  enabled: true
  health_gate: true
  review_recovery_retries: 3

tech_research:
  enabled: true
  max_queries: 6
  required_queries:
    - "FastAPI lifespan context manager and dependency injection"
    - "tree-sitter Python SDK 0.25 Query and QueryCursor API"
    - "ChromaDB PersistentClient collection CRUD operations"
    - "NetworkX DiGraph pagerank cycle detection topological sort"
    - "MCP Python SDK tool decorator stdio transport server"
    - "Schemathesis openapi from_path parametrize testing"

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false  # No frontend/UI
  api_contract_scan: true

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 3

browser_testing:
  enabled: false  # No frontend

integrity_scans:
  deployment_scan: true   # Docker Compose validation
  asset_scan: false       # No static assets
  prd_reconciliation: true

database_scans:
  dual_orm_scan: false     # SQLite only, no ORM mixing
  default_value_scan: true
  relationship_scan: false  # SQLite, not ORM relationships
```

### 4.2 BUILD2 config.yaml

```yaml
depth: thorough

milestone:
  enabled: true
  health_gate: true
  review_recovery_retries: 3

tech_research:
  enabled: true
  max_queries: 6
  required_queries:
    - "MCP Python SDK client session stdio_client call_tool"
    - "Claude Code Agent Teams TaskCreate TaskUpdate SendMessage"
    - "Claude Code hooks system command agent hook types"
    - "asyncio create_subprocess_exec pipe timeout"
    - "Python dataclass field default_factory typing Protocol"
    - "pydantic BaseSettings v2 env variable loading"

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false
  api_contract_scan: true

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 3

browser_testing:
  enabled: false

integrity_scans:
  deployment_scan: false
  asset_scan: false
  prd_reconciliation: true

database_scans:
  dual_orm_scan: false
  default_value_scan: false
  relationship_scan: false
```

**Note**: BUILD2 is special — it modifies agent-team itself. The config above would be used by the *current* v14.0 agent-team to build v15.0. Backward compatibility testing (TEST-075, 5,410+ tests) is critical.

### 4.3 BUILD3 config.yaml

```yaml
depth: exhaustive  # Most complex build, needs maximum verification

milestone:
  enabled: true
  health_gate: true
  review_recovery_retries: 3

tech_research:
  enabled: true
  max_queries: 6
  required_queries:
    - "transitions AsyncMachine Python state machine queued transitions"
    - "typer CLI framework command callback rich integration"
    - "Schemathesis 4.x openapi from_url get_all_operations FailureGroup"
    - "pact-python v3 Verifier add_transport state_handler verify"
    - "Docker Compose v2 python subprocess healthcheck depends_on"
    - "Traefik v3 Docker provider PathPrefix labels auto-discovery"

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false
  api_contract_scan: true

e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 5  # Higher due to complexity

browser_testing:
  enabled: false

integrity_scans:
  deployment_scan: true    # Docker Compose validation critical
  asset_scan: false
  prd_reconciliation: true

database_scans:
  dual_orm_scan: false
  default_value_scan: false
  relationship_scan: false
```

### 4.4 RUN4 config.yaml

```yaml
depth: thorough

# Run4-specific config (parsed by Run4Config, NOT AgentTeamConfig)
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
  mcp_startup_timeout_ms: 30000
  mcp_tool_timeout_ms: 60000
  mcp_first_start_timeout_ms: 120000
  max_concurrent_builders: 3
  builder_timeout_s: 1800
  builder_depth: "thorough"
  max_fix_passes: 5
  max_budget_usd: 100.0
  sample_prd_path: "tests/run4/fixtures/sample_prd.md"

# Standard agent-team sections
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

browser_testing:
  enabled: false

integrity_scans:
  deployment_scan: true
  asset_scan: false
  prd_reconciliation: true
```

---

## 5. Gap Analysis Summary

### 5.1 Critical Gaps (Require Agent-Team Changes)

| Gap ID | Description | Affected PRDs | Severity | Effort |
|--------|-------------|---------------|----------|--------|
| GAP-01 | No SEC-xxx security scanning (JWT, CORS, secrets, Docker) | BUILD3, RUN4 | HIGH | These are BUILD3-internal scan codes, not agent-team pipeline features. Agent-team doesn't need them — BUILD3 implements its own quality gate. |
| GAP-02 | No MCP server creation guidance in prompts | BUILD1 | MEDIUM | Add MCP server patterns to `code_quality_standards.py` |
| GAP-03 | No Pact v3 API awareness | BUILD3 | MEDIUM | Tech research via Context7 should cover this; add to required_queries |
| GAP-04 | No `transitions` library patterns | BUILD3 | LOW | Tech research handles this; library is well-documented |
| GAP-05 | No cross-build dependency management | RUN4 | HIGH | RUN4's `run4:` config section handles this externally; agent-team builds the test infra |
| GAP-06 | INT-xxx requirements have no scanner | All 4 | MEDIUM | INT-xxx are integration constraints (backward compat, pipeline preservation). Most are design constraints enforced by code review, not scannable |
| GAP-07 | TECH-xxx requirements have no static verifier | All 4 | LOW | TECH-xxx items like "use pathlib.Path" or "all file I/O must specify encoding=utf-8" could theoretically be scanned but are better enforced via code review prompts |
| GAP-08 | TEST-xxx minimum test count not verified | All 4 | LOW | Agent-team prompts say "write tests" but don't verify "minimum 8 test cases". Could add a test count check post-build |

### 5.2 Non-Gaps (Already Handled)

| Feature | Handler | Notes |
|---------|---------|-------|
| REQ-xxx functional requirements | Milestone execution + REQUIREMENTS.md checkboxes | Core pipeline functionality |
| SVC-xxx API contracts | `run_api_contract_scan()` + 3-layer verification | v9.0 implementation |
| Docker Compose validation | `DEPLOY-001..004` integrity scans | Post-build validation |
| Mock data prevention | `run_mock_data_scan()` MOCK-001..008 | Prompt + static scan |
| Database integrity | DB-001..008 scans | v5.0 implementation |
| PRD reconciliation | `parse_prd_reconciliation()` + LLM sub-orchestrator | Post-build check |
| Convergence tracking | `ConvergenceReport` + health checks | Core pipeline |

### 5.3 Partial Coverage (Works But Could Be Better)

| Feature | Current Coverage | Improvement |
|---------|-----------------|-------------|
| WIRE-xxx verification | Prompt-driven wiring check in milestone workflow | Could add import-graph-based static verification |
| TEST-xxx enforcement | Prompts instruct test writing; E2E phase runs tests | Could verify minimum test count per TEST-xxx item |
| TECH-xxx constraints | In prompt text only | Could add focused regex scans for common TECH patterns (pathlib, encoding, etc.) |
| Multi-service Docker apps | DEPLOY scans validate existing compose files | No compose file generation guidance |

---

## 6. Priority Fixes

### 6.1 Fixes for These Specific PRDs

| Priority | Fix | Impact | PRDs |
|----------|-----|--------|------|
| P1 | Add MCP SDK patterns to `code_quality_standards.py` (tool decorators, stdio transport, server creation) | BUILD1 agents will know how to create MCP servers correctly | BUILD1 |
| P1 | Add `transitions` library + Pact v3 + Schemathesis 4.x to tech research required queries | Prevents wrong API usage for critical libraries | BUILD3 |
| P2 | Add Schemathesis/Pact API patterns to code quality standards | BUILD3 M2 (Contract Compliance) uses non-obvious API (e.g., `get_all_operations()` not `schema.items()`) | BUILD3 |
| P2 | Add Docker Compose generation patterns to architect prompt | BUILD3 M1 generates compose files programmatically | BUILD3 |
| P3 | Add INT-xxx integration requirement type to `_parse_svc_table()` or new parser | INT-xxx items would be tracked in REQUIREMENTS.md | All 4 |
| P3 | Add TECH-xxx basic static verification (pathlib usage, encoding parameter) | Low-cost quality improvement | All 4 |
| P3 | Add TEST-xxx minimum test count verification post-build | Count test functions matching `test_*` pattern per test file | All 4 |

### 6.2 No-Fix Items (By Design)

| Item | Reason |
|------|--------|
| SEC-xxx security scanning | BUILD3 implements its own `SecurityScanner`, `ObservabilityChecker`, `DockerSecurityScanner`. Agent-team doesn't need to duplicate this. |
| Cross-build Docker orchestration | RUN4's docker topology is managed by its own `run4:` config, not agent-team pipeline. Agent-team builds the test infrastructure; Docker management is external. |
| State machine verification | BUILD3's state machine is tested by BUILD3's own tests (TEST-001 in M1). Agent-team doesn't need state machine awareness. |
| Agent Teams backend (BUILD2) | BUILD2 adds this TO agent-team. It's not a gap — it's the deliverable. |

---

## 7. Cross-PRD Dependency Map

```
BUILD1 (Foundation Services)
  ├── Produces: 3 MCP servers (20 tools), 3 FastAPI services, 3 SQLite databases
  ├── Consumed by: BUILD2 (MCP clients), BUILD3 (MCP consumers), RUN4 (verification)
  └── No dependencies on other builds

BUILD2 (Builder Fleet Upgrade)
  ├── Modifies: agent-team v14.0 → v15.0
  ├── Depends on: BUILD1 MCP servers (6+7+4 tools) — with fallback paths
  ├── Consumed by: BUILD3 (subprocess CLI), RUN4 (verification)
  └── Self-referential: uses v14.0 to build v15.0

BUILD3 (Orchestration Layer)
  ├── Depends on: BUILD1 (MCP tools), BUILD2 (agent-team CLI subprocess)
  ├── Produces: Super Orchestrator CLI, Quality Gate, Integrator
  └── No dependents (top of stack)

RUN4 (Verification)
  ├── Depends on: ALL three builds running simultaneously
  ├── Produces: SUPER_TEAM_AUDIT_REPORT.md, test infrastructure
  └── Terminal node — verification only
```

---

## 8. Conclusion

The agent-team pipeline (v15.0) can handle all 4 PRDs with the following caveats:

1. **BUILD1**: Fully compatible. The PRD is a standard multi-service Python backend. Tech research phase needs MCP SDK queries. Estimated 8 milestones at thorough depth.

2. **BUILD2**: Unique challenge — self-modifying build. Recommend running with v14.0 agent-team, then manually verifying backward compatibility. All 5,410+ existing tests must pass.

3. **BUILD3**: Most complex build. 40 scan codes, state machine, Schemathesis, Pact, Docker Compose generation, Traefik. Needs exhaustive depth + maximum tech research. The transitions library and Pact v3 API are the highest-risk components.

4. **RUN4**: Not a standard build. Agent-team builds the test infrastructure (config, state, fixtures, utilities) normally. The actual cross-build verification tests require Docker + all 3 builds running — this is outside agent-team's pipeline scope but within its code generation capability.

**Overall pipeline readiness: 85%** — the 15% gap is concentrated in library-specific API guidance (MCP creation, Pact v3, Schemathesis 4.x) that tech research should cover, and INT-xxx/TECH-xxx static verification that's nice-to-have but not blocking.
