# Super Agent Team — Exhaustive Research Report

**Date:** 2026-02-14
**Purpose:** Foundation research for PRD creation — all technologies validated, gaps identified, corrections documented
**Research Method:** 25-step sequential thinking + firecrawl web scraping + Context7 library queries + codebase exploration

---

## 1. FINAL OBJECTIVE — What We're Actually Building

A **meta-system** (the "Super Agent Team") that transforms a single PRD into a fully deployed, contract-verified, multi-service platform of 250-500K LOC. It is five systems working as one:

1. **Architect** — Decomposes PRDs into service boundaries + contracts
2. **Contract Engine** — Stores, validates, and generates tests from OpenAPI/AsyncAPI specs
3. **Codebase Intelligence** — Live queryable AST/graph/semantic index via MCP
4. **Builder Fleet** — Upgraded agent-team (v14.0) with native agent teams + contract awareness
5. **Integrator + Quality Gate + Super Orchestrator** — Cross-service wiring, 4-layer verification, end-to-end coordination

The system is built in **3 sequential builds + 1 integration run**, totaling ~145K LOC of infrastructure.

---

## 2. VALIDATED TECHNOLOGY STACK

Every technology below has been verified against current documentation (February 2026).

### 2.1 Build 1 Technologies

| Technology | Version | Status | Source | Notes |
|------------|---------|--------|--------|-------|
| **py-tree-sitter** | 0.25.2 | VALIDATED | tree-sitter.github.io/py-tree-sitter | Pre-compiled wheels for all platforms. `Language(path)` API loads .so/.dll grammars. Query-based pattern matching via `language.query()`. Supports Python, TypeScript, C#, Go out of the box. |
| **ChromaDB** | Latest | VALIDATED | Context7 /chroma-core/chroma | `PersistentClient(path="./chroma_db")` for disk-backed storage. `collection.add(documents, metadatas, ids)` for insertion. `collection.query(query_texts, n_results)` for semantic search. Auto-embeds with sentence-transformers. No external server needed. |
| **NetworkX** | Latest | VALIDATED | Context7 /networkx/networkx | `DiGraph()` for directed dependency graphs. `nx.pagerank(G)` for architectural relevance ranking. `nx.simple_cycles(G)` for circular dependency detection. `nx.shortest_path(G, source, target)` for impact analysis. Pure Python, no compiled dependencies. |
| **MCP Python SDK** | Latest | VALIDATED | Context7 /modelcontextprotocol/python-sdk | `MCPServer("name")` + `@mcp.tool()` decorator for tool registration. `@mcp.resource("uri://{param}")` for resources. stdio transport for Claude Code integration. Client via `stdio_client()` + `ClientSession`. |
| **SQLite** | 3.x (stdlib) | VALIDATED | Built-in | **REPLACES PostgreSQL from reference doc.** WAL mode for concurrent reads. No external service needed. Sufficient for contract registry + metadata. |
| **OpenAPI 3.1** | Ecosystem | VALIDATED | Multiple sources | `openapi-spec-validator` for validation, `prance` for dereferencing, `openapi-core` for request/response validation. Mature ecosystem. |
| **AsyncAPI 3.1** | Spec only | RISK | asyncapi.com + GitHub | **NO mature Python parser exists.** `asyncapi-python-parser` on GitHub has 1 star, last commit 1.5 years ago. Must build lightweight parser (~500 lines) using `pyyaml` + `jsonschema`. Spec itself is well-defined. |
| **Schemathesis** | Latest (Feb 2026) | VALIDATED | schemathesis.readthedocs.io + PyPI | Property-based API testing from OpenAPI specs. CLI: `st run --url http://... /openapi.json`. Python API: `schemathesis.from_uri()`. Auto-generates test cases, validates response schemas, checks status codes. Most recent release: February 2026. |
| **Pact Python** | v2 stable / v3 beta | SECONDARY | docs.pact.io | v2 wraps Ruby standalone (requires Ruby runtime). v3 beta uses native C FFI (no Ruby). **Recommend v3 beta for new projects but treat as secondary to Schemathesis.** Consumer-driven contract testing. |
| **FastAPI** | Latest | VALIDATED | Standard | For Contract Engine HTTP API. Auto-generates OpenAPI specs. Async support. |

### 2.2 Build 2 Technologies

| Technology | Version | Status | Source | Notes |
|------------|---------|--------|--------|-------|
| **Claude Code Agent Teams** | Opus 4.6 | EXPERIMENTAL | code.claude.com/docs/en/agent-teams | **Disabled by default** — requires `agentTeams: true` in settings. Shared task list (TaskCreate, TaskList, TaskUpdate), peer messaging (SendMessage), delegate mode. **Known limitations:** no session resumption, no nested teams, one team per session, Windows Terminal split-panes don't work. |
| **Claude Code Hooks** | Opus 4.6 | VALIDATED | code.claude.com/docs/en/hooks-guide | Three types: `command` (shell), `prompt` (single LLM call), `agent` (multi-turn with tool access). Key events: `TeammateIdle`, `TaskCompleted`, `Stop`. Exit code 2 blocks action + sends feedback. Agent hooks have full tool access. Perfect for convergence enforcement. |
| **Existing agent-team** | v14.0 | PROVEN | Local codebase (28,749 LOC) | 28 files, 5400+ tests. scheduler.py (parallel execution), contracts.py (contract primitives), quality_checks.py (13 scan types), agents.py (prompt engineering). This is the base being upgraded. |

### 2.3 Build 3 Technologies

| Technology | Version | Status | Source | Notes |
|------------|---------|--------|--------|-------|
| **Traefik** | v3 | VALIDATED | traefik.io | API gateway with Docker label auto-discovery. No manual route config needed — services declare their routes via Docker labels. 55K GitHub stars, 3B+ downloads. |
| **Docker Compose** | v2 | VALIDATED | Standard | `depends_on` with `condition: service_healthy`. `healthcheck` with `start_period` for initialization grace. Proven at 5 services (DrawSpace V2), scales to 12+. |
| **Testcontainers** | Python | VALIDATED | testcontainers.com | Manages Docker containers from pytest. `DockerContainer("image").with_exposed_ports(port)`. Automatic cleanup. |
| **pytest + httpx** | Latest | VALIDATED | Standard | pytest for test orchestration, httpx for async HTTP calls across services. |

---

## 3. CORRECTIONS TO REFERENCE DOCUMENT

### CORRECTION 1: Drop PostgreSQL — Use SQLite + ChromaDB (Build 1 M1)

**Reference says:** "Docker Compose with PostgreSQL (pgvector extension)"
**Research finding:** PostgreSQL is unnecessary overhead for Build 1. The contract registry and metadata storage are simple key-value/relational queries that SQLite handles perfectly. ChromaDB already provides vector search (replacing pgvector). SQLite is zero-config, embedded, and reduces the Docker Compose complexity.

**Impact on PRD:** Remove PostgreSQL from M1 Docker Compose. Use SQLite for Contract Engine storage. Use ChromaDB's PersistentClient for vector embeddings. This eliminates an external dependency and simplifies deployment.

**Exception:** If a generated application (the 500K LOC target) uses PostgreSQL, that's fine — but the Super Team infrastructure itself doesn't need it.

### CORRECTION 2: AsyncAPI Python Tooling Gap (Build 1 M3)

**Reference says:** "AsyncAPI 3.1 spec storage, parsing, and validation"
**Research finding:** There is no mature Python library for AsyncAPI parsing. The `asyncapi-python-parser` on GitHub has 1 star and hasn't been updated in 1.5 years. The official AsyncAPI tooling ecosystem is JavaScript-focused (modelina, generator, studio — all Node.js).

**Impact on PRD:** Build 1 M3 must include a "Lightweight AsyncAPI Parser" sub-milestone (~500 lines). Use `pyyaml` for YAML parsing + `jsonschema` for schema validation. Parse the spec structure manually following the AsyncAPI 3.1 specification. Do NOT depend on any external AsyncAPI Python library. Alternatively, start with OpenAPI-only contracts and add AsyncAPI incrementally.

### CORRECTION 3: Pact Should Be Secondary to Schemathesis (Build 1 M4)

**Reference says:** Lists Pact and Schemathesis as co-equal for contract testing
**Research finding:** Pact Python v2 requires a Ruby runtime (wraps Ruby standalone). Pact v3 is in beta with native C FFI but has limited documentation. Schemathesis, on the other hand, is actively maintained (February 2026 release), generates tests automatically from OpenAPI specs, and has a clean Python API.

**Impact on PRD:** Make Schemathesis the PRIMARY contract testing tool. Add Pact as OPTIONAL/secondary for consumer-driven scenarios only. This reduces Build 1 M4 scope and eliminates the Ruby dependency.

### CORRECTION 4: Agent Teams Are Experimental (Build 2 M1)

**Reference acknowledges this** but the PRD must go further in specifying the fallback.
**Research finding:** Agent Teams require `agentTeams: true` in settings (disabled by default). There's no session resumption — if a teammate crashes, its state is lost. No nested teams. Windows Terminal doesn't support split panes for team visualization. The API surface is small but unproven at scale.

**Impact on PRD:** Build 2 M1 must define an **abstraction layer** that can switch between:
- Mode A: Claude Code Agent Teams (native, when available and stable)
- Mode B: Current subprocess-based orchestration (fallback, proven)

The abstraction should expose: `create_team()`, `assign_task()`, `send_message()`, `wait_for_completion()`. Both modes implement this interface. All higher-level code (prompts, scans, pipelines) operates through the abstraction, not directly on agent teams.

### CORRECTION 5: MCP SDK API Surface (Build 1 M6-M7)

**Reference says:** "MCP server interfaces" (generic)
**Research finding:** The exact API is:
```python
from mcp.server.mcpserver import MCPServer
mcp = MCPServer("ServiceName")

@mcp.tool()
def tool_name(param: type) -> return_type:
    """Tool description shown to Claude"""
    ...

@mcp.resource("protocol://{param}")
def resource_name(param: str) -> str:
    ...

# Run with stdio transport (default for Claude Code)
mcp.run(transport="stdio")
```

**Impact on PRD:** M6 and M7 must specify exact MCP tool signatures with this pattern. Every tool must have type annotations and docstrings (Claude reads these for tool selection).

---

## 4. GAPS — Missing From Reference Document

### GAP 1: Hook Architecture for Convergence (Build 2)

**What's missing:** The reference mentions hooks conceptually but doesn't specify the architecture.
**Research finding:** Claude Code hooks support three types:
- `command`: Shell script execution (for pre-checks)
- `prompt`: Single LLM call (for quick validation)
- `agent`: Multi-turn subagent with full tool access (for convergence verification)

The `agent` type is ideal for convergence enforcement:
```json
{
  "hooks": {
    "TaskCompleted": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Read REQUIREMENTS.md. Verify ALL items marked [x]. If any unmarked, exit with code 2 and explain what's missing.",
        "timeout": 120
      }]
    }]
  }
}
```

**Must add to PRD:** Build 2 must define the complete hook configuration including:
- `TaskCompleted` → convergence verification agent
- `TeammateIdle` → workload rebalancing check
- `Stop` → final quality gate verification
- Custom hooks for contract compliance checks

### GAP 2: CLAUDE.md Generation Strategy (Build 2)

**What's missing:** How prompts transfer from current agent-team to agent teams teammates.
**Research finding:** Claude Code teammates automatically load `CLAUDE.md` from the project root. They do NOT inherit the lead's conversation history.

**Must add to PRD:** Build 2 must define a `generate_claude_md()` function that:
1. Takes the current prompt templates (from agents.py)
2. Adds service-specific context (which service, its contracts, its dependencies)
3. Adds MCP server configurations (Contract Engine, Codebase Intelligence)
4. Writes a `CLAUDE.md` file to each service's directory before spawning teammates
5. Includes convergence mandates, review criteria, and scan directives

### GAP 3: Contract Implementation Tracking (Build 1-2)

**What's missing:** How to know which Builder consumed which contract, and whether all contracts are implemented.
**Must add to PRD:** The Contract Engine needs a `mark_implemented(contract_id, service_name, evidence_path)` tool. After a Builder generates an endpoint, it calls this tool. The Integrator can then query `get_unimplemented_contracts()` to find gaps.

### GAP 4: Windows Compatibility Plan (All Builds)

**What's missing:** The reference doesn't address Windows-specific concerns.
**Research finding:** Omar's primary platform is Windows 11. Agent Teams split panes don't work on Windows Terminal. Process isolation differs (no Unix signals). Path separators need handling.

**Must add to PRD:** Each build must include Windows compatibility notes:
- Use `pathlib.Path` everywhere (not string concatenation)
- Use `subprocess.CREATE_NEW_PROCESS_GROUP` on Windows
- Test Docker Compose on Docker Desktop for Windows
- Agent Teams fallback mode is especially important for Windows

### GAP 5: SQLite Concurrency Under Parallel Builders (Build 1-2)

**What's missing:** Multiple Builders writing to SQLite simultaneously.
**Must add to PRD:** Configure SQLite with WAL (Write-Ahead Logging) mode:
```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
```
WAL mode allows concurrent readers with one writer. For the Codebase Intelligence index, use per-service SQLite files that merge into a global index periodically.

### GAP 6: Cost Estimation and Budget Management (Build 3)

**What's missing:** How to track and limit costs across multiple agent team runs.
**Must add to PRD:** The Super Orchestrator needs:
- Per-builder cost tracking (already exists in current agent-team as `total_cost`)
- Aggregate cost reporting across all parallel builders
- Budget gates that pause execution if costs exceed thresholds
- Cost prediction based on service complexity estimates from the Architect

### GAP 7: Incremental Indexing Protocol (Build 1 M6)

**What's missing:** How Codebase Intelligence updates as Builders generate code.
**Must add to PRD:** Define an incremental indexing protocol:
1. Builder generates file → calls `register_artifact(file_path, service_name)` via MCP
2. Codebase Intelligence parses the new file with Tree-sitter
3. Updates dependency graph (NetworkX) with new imports/exports
4. Adds code chunks to ChromaDB for semantic search
5. Other agents querying the index see updated results within seconds

---

## 5. EXPANSIONS — Need More Detail in PRDs

### EXPANSION 1: Architect Decomposition Algorithm (Build 1 M2)

**Reference says:** "PRD parser that extracts service boundaries"
**Needs expansion:** How does the Architect actually decompose a PRD into services? The reference describes it as "a single Opus session" but doesn't specify the algorithm.

**Recommended approach (from research):**
1. **Entity Extraction** — LLM identifies all business entities (User, Order, Payment, Notification, etc.)
2. **Relationship Mapping** — LLM maps relationships between entities (owns, references, triggers)
3. **Bounded Context Identification** — LLM groups entities into bounded contexts using DDD principles
4. **Service Boundary Validation** — Automated checks:
   - No circular dependencies between contexts
   - No entity owned by multiple contexts
   - Every entity reachable from at least one context
   - Communication between contexts mapped to API/event contracts
5. **Human Review Checkpoint** — Before proceeding, display the proposed decomposition for review
6. **Contract Generation** — For each inter-context boundary, generate OpenAPI (sync) or AsyncAPI (async) stubs

This is fundamentally an LLM reasoning task (not a code task), so the Architect should use structured output (JSON mode) to produce machine-parseable results that feed directly into the Contract Engine.

### EXPANSION 2: Contract Immutability Mechanism (Build 1 M3)

**Reference says:** "Contracts are versioned and immutable within a build cycle"
**Needs expansion:** How is immutability enforced?

**Recommended approach:**
1. Each contract gets a SHA-256 hash on registration
2. The Contract Engine stores `(contract_id, version, hash, created_at, build_cycle_id)`
3. Any `update_contract()` call within the same `build_cycle_id` is REJECTED with an error
4. New versions require incrementing the `build_cycle_id` (which only the Super Orchestrator can do)
5. Builders receive contracts with their hash — if they detect a mismatch, they raise a violation

### EXPANSION 3: Quality Gate Layer Specifications (Build 3 M4)

**Reference says:** Four layers, gated sequentially
**Needs expansion:** Exact checks per layer:

**Layer 1 (Per-Service) — Already done by Builders:**
- Unit tests pass (>80% coverage)
- Build succeeds without errors
- Docker image builds and starts
- Health endpoint responds 200
- No CRITICAL scan violations

**Layer 2 (Cross-Service Contracts) — Integrator:**
- Schemathesis run against every endpoint in OpenAPI spec
- Response schema matches contracted schema (exact field names, types, required fields)
- Error codes match contracted error codes
- Pagination parameters match (if applicable)
- Event schemas match AsyncAPI spec (channel, payload, headers)
- Every contract has at least one implementation

**Layer 3 (System-Level) — Quality Gate:**
- JWT validation on every authenticated endpoint (no unauthenticated access to protected routes)
- CORS headers correctly configured (no wildcard in production)
- Consistent log format across all services (structured JSON with trace_id)
- Trace ID propagation (request in Service A carries trace_id to Service B)
- Health endpoints on all services (/health or /healthz)
- No hardcoded secrets in source code
- Docker images use non-root users

**Layer 4 (Adversarial Review) — Review Fleet:**
- Events published but never consumed (dead events)
- Contracts defined but never implemented (dead contracts)
- Services that never communicate with any other service (orphan services)
- Inconsistent naming across service boundaries (camelCase vs snake_case)
- Missing error handling at service boundaries (what if Service B is down?)
- Race conditions in event processing (ordering guarantees)

### EXPANSION 4: Super Orchestrator State Machine (Build 3 M5)

**Reference says:** "State management for pause/resume/retry"
**Needs expansion:** Define exact states and transitions:

```
States:
  INIT → ARCHITECT_RUNNING → ARCHITECT_REVIEW → CONTRACTS_REGISTERING →
  BUILDERS_RUNNING → BUILDERS_COMPLETE → INTEGRATING → QUALITY_GATE →
  FIX_PASS → COMPLETE | FAILED

Transitions:
  INIT → ARCHITECT_RUNNING: on `super-team run` or `super-team plan`
  ARCHITECT_RUNNING → ARCHITECT_REVIEW: when Architect produces Service Map
  ARCHITECT_REVIEW → CONTRACTS_REGISTERING: on human approval (or auto-approve)
  CONTRACTS_REGISTERING → BUILDERS_RUNNING: when all contracts stored
  BUILDERS_RUNNING → BUILDERS_COMPLETE: when all Builders finish (or max retries)
  BUILDERS_COMPLETE → INTEGRATING: automatic
  INTEGRATING → QUALITY_GATE: when Integrator produces integration report
  QUALITY_GATE → FIX_PASS: when violations found
  QUALITY_GATE → COMPLETE: when all layers pass
  FIX_PASS → BUILDERS_RUNNING: when fixes require Builder changes
  FIX_PASS → INTEGRATING: when fixes are integration-level
  FIX_PASS → QUALITY_GATE: when fixes are verified
  Any → FAILED: on unrecoverable error + max retries exhausted

Persistence:
  State stored in .super-team/state.json
  Each transition logged with timestamp, cost, and artifact paths
  Resume from any state via `super-team resume`
```

---

## 6. NEW RISKS (Beyond the 5 in Reference)

### Risk 6: Windows Compatibility
**Severity:** MEDIUM
**Description:** Omar's primary platform is Windows 11. Agent Teams split panes don't work on Windows Terminal. Docker Desktop for Windows has different networking. Path handling differs.
**Mitigation:** All code uses `pathlib.Path`. Docker Compose tested on Docker Desktop for Windows. Agent Teams abstraction layer has subprocess fallback.

### Risk 7: SQLite Concurrency Under Parallel Builders
**Severity:** LOW-MEDIUM
**Description:** 8 parallel Builders all registering artifacts with Codebase Intelligence simultaneously could hit SQLite write locks.
**Mitigation:** WAL mode + busy_timeout. Per-service index files that merge periodically. ChromaDB handles its own concurrency.

### Risk 8: Cost Management with Multi-Agent Teams
**Severity:** MEDIUM
**Description:** 8 parallel Builders, each running Claude Code agent teams with multiple teammates, could generate $300+ in a single run. Without budget gates, costs can spiral.
**Mitigation:** Super Orchestrator tracks per-builder costs. Budget gates at configurable thresholds. Service complexity estimates from Architect inform cost predictions. Start with 3-service runs before attempting 8+.

---

## 7. DEPENDENCY GRAPH — Critical Path

```
Build 1:
  M1 (scaffold) → M2 (Architect) → M3 (Contract Engine) → M4 (test gen)
                                                              ↓
  M1 → M5 (CI Layer 1+2) → M6 (CI Layer 3 + MCP) → M7 (Architect+CE MCP) → M8 (integration)

Build 2 (depends on Build 1 M7 outputs):
  M1 (agent teams abstraction) → M2 (contract pipeline) → M3 (CI integration)
                                                             ↓
  M1 → M4 (multi-instance) → M5 (prompts) → M6 (E2E test)

Build 3 (depends on Build 1 M7 + Build 2 M4):
  M1 (Docker/Traefik) → M2 (compliance) → M3 (cross-svc tests) → M4 (quality gate)
                                                                     ↓
  M1 → M5 (super orchestrator) → M6 (CLI) → M7 (E2E)

Run 4 (depends on all builds):
  Phase 1 (wiring) → Phase 2 (builder test) → Phase 3 (E2E) → Phase 4 (fix) → Phase 5 (audit)
```

**Critical path:** Build 1 M1→M2→M3→M7 → Build 2 M1→M2→M6 → Build 3 M1→M5→M7 → Run 4
**Estimated critical path duration:** ~25-30 milestones across 4 phases

---

## 8. PRD CREATION STRATEGY

### Order
1. **PRD-1: Build 1** (no dependencies, most foundational)
2. **PRD-2: Build 2** (depends on Build 1 MCP interfaces being defined)
3. **PRD-3: Build 3** (depends on both Build 1 and Build 2 outputs)
4. **PRD-4: Run 4** (depends on all 3 builds, shortest PRD)

### Format Requirements (for agent-team v14.0 compatibility)
Each PRD must:
- Use **REQ-xxx** identifiers for functional requirements
- Use **SVC-xxx** tables for API contracts (leverages v9.0 API contract verification)
- Use **FRONT-xxx** for UI requirements where applicable
- Include **exact file paths** and function signatures (agent reads literally)
- Include **MCP tool signatures** with full type annotations
- Be structured with **## headers** for automatic chunking (PRDs will exceed 50KB)
- Define **8-10 milestones** each (matching agent-team's milestone system)
- Include **success criteria** per milestone (for convergence verification)
- Include **technology versions** (all validated above)

### Level of Detail
- Each milestone must be completable in a single agent-team run
- Contract schemas must be complete JSON/TypeScript/Python types
- MCP tool signatures must include parameter types, return types, and docstrings
- Docker Compose must specify ports, health checks, environment variables
- Test expectations must be specific (">80% coverage", "responds in <500ms")

### Milestone Estimates
- **Build 1:** 8 milestones (M1: scaffold, M2: Architect, M3: Contract Engine core, M4: test generation, M5: CI Layer 1+2, M6: CI Layer 3 + MCP, M7: Architect+CE MCP, M8: integration + Docker)
- **Build 2:** 6 milestones (M1: agent teams abstraction, M2: contract pipeline, M3: CI integration, M4: multi-instance, M5: enhanced prompts, M6: E2E test)
- **Build 3:** 7 milestones (M1: Docker/Traefik framework, M2: contract compliance, M3: cross-service tests, M4: quality gate layers 3-4, M5: super orchestrator, M6: CLI, M7: E2E test)
- **Run 4:** 5 phases (wiring, builder test, E2E pipeline, fix pass, audit)

---

## 9. UPDATED PROBABILITY ASSESSMENT

| Outcome | Reference Prob | Updated Prob | Reasoning |
|---------|---------------|-------------|-----------|
| Build 1 succeeds | 90% | **75%** | AsyncAPI gap adds risk. No PostgreSQL simplifies but SQLite concurrency is untested at scale. Tree-sitter + ChromaDB validated. |
| Build 2 succeeds | 70% | **80%** | Agent Teams abstraction layer de-risks. Hook architecture validated. Existing codebase (28.7K LOC) is proven foundation. Higher than reference because fallback mode is well-defined. |
| Build 3 succeeds | 75% | **70%** | Cross-service integration testing is genuinely hard. Adversarial review quality is unknown. Docker orchestration proven but at 5 services, not 12. |
| Run 4 achieves integration | 65% | **65%** | Unchanged. Fix pass methodology proven. Unknown-unknowns remain. |
| Compound: full system | 30-40% | **27-35%** | Slightly lower due to AsyncAPI gap. Still ambitious but feasible. |
| 250K LOC app (5 services) | 55-65% | **55-65%** | Unchanged. This is the realistic first target. |

---

## 10. EXISTING CODEBASE ARCHITECTURE (Agent-Team v14.0)

### Core Files (28 files, 28,749 LOC total)

| File | LOC | Purpose | Build 2 Impact |
|------|-----|---------|----------------|
| cli.py | 6,213 | Main entry point, orchestration loop, all fix functions, scan wiring | **HEAVY MODIFICATION** — agent teams integration, new MCP client calls |
| quality_checks.py | 4,346 | 13 scan types (mock, UI, E2E, DB, API, XREF, etc.) | **ADD** CONTRACT-001..004 scans |
| agents.py | 2,621 | All prompt templates (orchestrator, architect, writer, reviewer) | **HEAVY MODIFICATION** — add contract awareness, MCP query instructions |
| scheduler.py | 1,368 | Parallel agent execution, task scheduling | **REPLACE/UPGRADE** — agent teams abstraction layer |
| config.py | 1,310 | AgentTeamConfig with all sub-configs | **ADD** ContractConfig, AgentTeamsConfig |
| browser_testing.py | 1,304 | Playwright MCP workflow testing | Minimal changes |
| tracking_documents.py | 1,160 | E2E coverage matrix, fix cycle log, milestone handoff | **ADD** contract tracking document |
| verification.py | 1,141 | Convergence verification, requirement checking | **ADD** contract compliance verification |
| e2e_testing.py | 973 | E2E test generation and execution | Minimal changes |
| codebase_map.py | 956 | Static CODEBASE_MAP.md generation | **REPLACE** with MCP queries to Codebase Intelligence |
| milestone_manager.py | 934 | MASTER_PLAN.md parsing, milestone health | Minimal changes |
| tech_research.py | 746 | Context7-based tech stack research | Minimal changes |
| design_reference.py | 666 | UI requirements extraction | Minimal changes |
| code_quality_standards.py | 664 | Quality standard constants | **ADD** CONTRACT standards, INTEGRATION standards |
| contracts.py | 650 | Contract primitives (existing) | **HEAVY MODIFICATION** — MCP client to Contract Engine |
| state.py | 304 | RunState, ConvergenceReport dataclasses | **ADD** ContractReport, IntegrationReport |
| mcp_servers.py | 170 | MCP server configurations | **ADD** Contract Engine, Codebase Intelligence servers |
| prd_chunking.py | 225 | Large PRD chunking (>50KB) | Minimal changes |

### Key Architecture Patterns to Preserve in Build 2
1. **15-stage pipeline** — proven over 14 versions, do not restructure
2. **13 self-healing fix loops** — each independently crash-isolated
3. **Post-orchestration scan chain** — mock → UI → integrity → DB → API → E2E
4. **Milestone-based execution** — MASTER_PLAN.md parsing, per-milestone health
5. **Config-gated features** — every scan/feature has a bool gate in config
6. **Depth-based behavior** — quick/standard/thorough/exhaustive modes

---

## 11. MCP TOOL INTERFACE SPECIFICATIONS

### Codebase Intelligence MCP Server Tools

```python
@mcp.tool()
def find_definition(symbol: str, language: str | None = None) -> dict:
    """Find the exact file and line number where a symbol is defined.
    Returns: {file: str, line: int, kind: str, signature: str}"""

@mcp.tool()
def find_callers(symbol: str, max_results: int = 50) -> list[dict]:
    """Find all call sites for a symbol across the entire codebase.
    Returns: [{file: str, line: int, context: str}]"""

@mcp.tool()
def find_dependencies(file_path: str) -> dict:
    """Get the dependency graph for a specific file.
    Returns: {imports: [str], imported_by: [str], transitive_deps: [str]}"""

@mcp.tool()
def search_semantic(query: str, n_results: int = 10) -> list[dict]:
    """Semantic search across the codebase using natural language.
    Returns: [{file: str, lines: str, content: str, score: float}]"""

@mcp.tool()
def get_service_interface(service_name: str) -> dict:
    """Get all public APIs and events for a service.
    Returns: {endpoints: [...], events_published: [...], events_consumed: [...]}"""

@mcp.tool()
def check_dead_code(service_name: str | None = None) -> list[dict]:
    """Find functions/classes defined but never called.
    Returns: [{symbol: str, file: str, line: int, kind: str}]"""

@mcp.tool()
def register_artifact(file_path: str, service_name: str) -> dict:
    """Register a newly generated file for indexing.
    Returns: {indexed: bool, symbols_found: int, dependencies_found: int}"""
```

### Contract Engine MCP Server Tools

```python
@mcp.tool()
def get_contract(contract_id: str) -> dict:
    """Get a contract by ID with full schema.
    Returns: {id: str, type: str, version: str, spec: dict, hash: str}"""

@mcp.tool()
def validate_endpoint(service_name: str, method: str, path: str, response_schema: dict) -> dict:
    """Validate an endpoint implementation against its contract.
    Returns: {valid: bool, violations: [{field: str, expected: str, actual: str}]}"""

@mcp.tool()
def generate_tests(contract_id: str, framework: str = "pytest") -> str:
    """Generate runnable test code from a contract.
    Returns: Test file content as string"""

@mcp.tool()
def check_breaking_changes(contract_id: str, new_spec: dict) -> list[dict]:
    """Check if a spec change would break existing consumers.
    Returns: [{change: str, severity: str, affected_consumers: [str]}]"""

@mcp.tool()
def mark_implemented(contract_id: str, service_name: str, evidence_path: str) -> dict:
    """Mark a contract as implemented by a service.
    Returns: {marked: bool, total_implementations: int}"""

@mcp.tool()
def get_unimplemented_contracts() -> list[dict]:
    """Get all contracts that haven't been implemented yet.
    Returns: [{id: str, type: str, expected_service: str}]"""
```

### Architect MCP Server Tools

```python
@mcp.tool()
def get_service_map() -> dict:
    """Get the complete service decomposition map.
    Returns: {services: [{name: str, domain: str, stack: dict, estimated_loc: int}]}"""

@mcp.tool()
def get_contracts_for_service(service_name: str) -> list[dict]:
    """Get all contracts (provider + consumer) for a specific service.
    Returns: [{id: str, role: str, type: str, counterparty: str}]"""

@mcp.tool()
def get_domain_model() -> dict:
    """Get the ubiquitous language / domain model.
    Returns: {entities: [...], relationships: [...], state_machines: [...]}"""
```

---

## 12. ACTIONABLE NEXT STEPS

1. **Create PRD-1 (Build 1)** — Most critical, no dependencies. Include all corrections (SQLite, AsyncAPI parser, Schemathesis primary). Define exact MCP tool interfaces (Section 11 above). 8 milestones.

2. **Create PRD-2 (Build 2)** — After PRD-1. Reference Build 1's MCP interfaces. Define agent teams abstraction layer. Map existing codebase modifications. 6 milestones.

3. **Create PRD-3 (Build 3)** — After PRD-2. Define Quality Gate layers precisely (Expansion 3). Define Super Orchestrator state machine (Expansion 4). 7 milestones.

4. **Create PRD-4 (Run 4)** — After PRD-3. Shortest document. 5 phases, mostly verification checklists.

**Start with PRD-1 immediately. It is the foundation everything depends on.**
