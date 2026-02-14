# Build 2 Codebase Research — Complete Modification Map

**Date:** 2026-02-14
**Source:** Deep-dive of all 10 core source files (28,749 LOC) + 4 reference documents
**Purpose:** Provide the architecture agent with exact file:line locations for every Build 2 modification point

---

## 1. EXECUTIVE SUMMARY

Build 2 upgrades the existing agent-team v14.0 (28,749 LOC across 28 files) into a **contract-aware, MCP-integrated Builder Fleet** with optional Claude Code Agent Teams coordination. The codebase is structured around a 15-stage pipeline in `cli.py` (6,214 lines) with prompt engineering in `agents.py` (2,622 lines), 40+ static analysis patterns in `quality_checks.py` (4,347 lines), and 21 config dataclasses in `config.py` (1,311 lines).

**Three upgrade axes:**
1. **Agent Teams Abstraction Layer** — Replace/augment Python CLI orchestration with native Claude Code agent teams (fallback to existing subprocess model)
2. **Contract Engine Integration** — MCP client calls to Build 1's Contract Engine for contract validation, test generation, and compliance checking
3. **Codebase Intelligence Integration** — Replace static CODEBASE_MAP.md with live MCP queries to Build 1's Codebase Intelligence service

**Key constraint:** The 15-stage pipeline, 13 self-healing fix loops, and post-orchestration scan chain are proven IP developed over 14 versions. Build 2 must preserve these while adding contract awareness and MCP integration.

---

## 2. FILE-BY-FILE MODIFICATION MAP

### 2.1 cli.py — HEAVY MODIFICATION (6,214 lines)

The main entry point containing the complete orchestration pipeline. Every phase of execution flows through `main()` (lines 3742-6214, ~2,500 lines).

#### 2.1.1 Orchestration Loop (Lines 4200-4600)

**Current behavior:** Three modes — interactive, milestone (`_run_prd_milestones`), or standard (`_run_single`). All use `_backend` module-level global to call Claude CLI/API.

**Build 2 modifications needed:**
- **Agent Teams mode selection** (new branch): When `config.agent_teams.enabled` is True and the environment supports it, replace the standard orchestration with agent teams coordination
- **Fallback logic**: If agent teams fails or is unavailable, gracefully fall back to existing `_run_single()` / `_run_prd_milestones()`
- **MCP server injection**: Add Contract Engine and Codebase Intelligence MCP servers to the server list passed to agents

**Key insertion points:**
- `cli.py:4200` — Mode selection branch (add agent teams branch)
- `cli.py:170-250` — MCP server list construction (currently imports from `mcp_servers.py`)
- `cli.py:3650-3735` — `_detect_backend()` (may need agent teams detection)

#### 2.1.2 Post-Orchestration Scan Pipeline (Lines 5100-5800)

**Current order (from cli.py):**
1. Mock data scan (line ~5130)
2. UI compliance scan (line ~5200)
3. Deployment scan (line ~5300)
4. Asset scan (line ~5350)
5. PRD reconciliation (line ~5400)
6. Dual ORM scan (line ~5450)
7. Default value scan (line ~5500)
8. Relationship scan (line ~5550)
9. API contract scan (line ~5600)
10. SDL scan (line ~5650)
11. XREF scan (line ~5700)

**Build 2 modifications needed:**
- **Add CONTRACT-001..004 scans** after the existing API contract scan (position ~5650)
- **Wire to Contract Engine MCP** for live validation (not just static regex)
- Each scan needs its own `max_scan_fix_passes` loop with crash isolation

#### 2.1.3 Phase 0.5: Codebase Map (Lines ~4050-4100)

**Current behavior:** Calls `generate_codebase_map()` from `codebase_map.py` which produces a static `CODEBASE_MAP.md` file via AST analysis.

**Build 2 modification:** Replace with MCP query to Codebase Intelligence service when available. Keep static generation as fallback.

```
Current:  codebase_map_content = await generate_codebase_map(cwd, ...)
Build 2:  if config.codebase_intelligence.enabled:
              codebase_map_content = await _query_codebase_index(cwd, ...)
          else:
              codebase_map_content = await generate_codebase_map(cwd, ...)
```

#### 2.1.4 Phase 0.6: Design Reference (Lines ~4100-4150)

No changes needed. Design reference extraction is UI-focused and independent of Build 2 concerns.

#### 2.1.5 Phase 0.75: Contract Loading (Lines ~4150-4200)

**Current behavior:** Loads `CONTRACTS.json` from local filesystem via `contracts.py`.

**Build 2 modification:** When Contract Engine MCP is available, fetch contracts from the MCP server instead of / in addition to local files. The local `CONTRACTS.json` becomes a cache/fallback.

#### 2.1.6 E2E Testing Phase (Lines 5800-6000)

**Current behavior:** `_run_backend_e2e_tests()`, `_run_frontend_e2e_tests()`, `_run_e2e_fix()` — all gated on `config.e2e_testing.enabled`.

**Build 2 modification:** Add contract compliance E2E tests. After standard E2E, run contract-specific E2E tests that validate actual API responses against contracted schemas (via Contract Engine MCP `validate_endpoint()` tool).

#### 2.1.7 Browser Testing Phase (Lines 6000-6150)

No changes needed. Browser testing is UI-focused.

#### 2.1.8 Fix Functions (Lines 2772-2916)

**Current `_run_integrity_fix()`** handles 5 scan types: deployment, asset, database_dual_orm, database_defaults, database_relationships. Each has its own elif branch with a specific fix prompt.

**Build 2 modification:** Add elif branches for:
- `contract_field_mismatch` — Fix API endpoints to match contracted schemas
- `contract_missing_endpoint` — Generate missing endpoints from contracts
- `contract_event_schema` — Fix event schemas to match AsyncAPI specs
- `contract_type_mismatch` — Fix type incompatibilities

#### 2.1.9 Signal Handling and State (Lines 2919-2970)

**Current behavior:** `_save_milestone_progress()` saves to JSON, `_handle_interrupt()` handles Ctrl+C with state save.

**Build 2 modification:** If using agent teams, signal handling must also coordinate teammate shutdown. The `_handle_interrupt` function needs a branch that sends `shutdown_request` to all active teammates before saving state.

#### 2.1.10 Subcommand: resume (Lines 3177-3338)

**Current behavior:** `_build_resume_context()` reconstructs state from `STATE.json` with milestone awareness.

**Build 2 modification:** Resume context must include contract state (which contracts are verified, which have violations). If agent teams was active, resume context must note that teammates were lost (agent teams has no session resumption).

#### 2.1.11 _check_convergence_health (Lines 3359-3416)

**Current behavior:** Reads REQUIREMENTS.md, counts `[x]`/`[ ]` checkboxes, computes convergence ratio.

**Build 2 modification:** Add contract compliance to convergence calculation. A milestone is not "healthy" if it has unresolved contract violations.

---

### 2.2 agents.py — HEAVY MODIFICATION (2,622 lines)

All prompt templates for every agent type. Build 2 needs contract awareness injected into every role.

#### 2.2.1 ARCHITECT_PROMPT (Lines 1-150)

**Current content:** System design instructions, technology selection, REQUIREMENTS.md format, service boundary definition. Already includes "EXACT FIELD SCHEMAS IN SVC-xxx TABLE" (added in v9.0).

**Build 2 modifications:**
- Add instruction to query Contract Engine MCP for existing contracts when designing service boundaries
- Add instruction to query Codebase Intelligence MCP for understanding existing codebase structure
- Add instruction to generate contract stubs that match Contract Engine's expected format

#### 2.2.2 CODE_WRITER_PROMPT (Lines 150-500)

**Current content:** Implementation instructions, ZERO MOCK DATA POLICY, API CONTRACT COMPLIANCE (v9.0), UI COMPLIANCE POLICY, quality standards references.

**Build 2 modifications:**
- Add "CONTRACT ENGINE INTEGRATION" section: instructions to call `validate_endpoint()` after implementing each API endpoint
- Add "CODEBASE INTELLIGENCE QUERIES" section: instructions to use `find_definition()`, `search_semantic()` instead of reading entire files
- Add "ARTIFACT REGISTRATION" section: instructions to call `register_artifact()` after creating each new file
- Add CONTRACT-001..004 compliance mandates

#### 2.2.3 CODE_REVIEWER_PROMPT (Lines 500-700)

**Current content:** Review criteria, convergence verification, API Contract Field Verification (API-001/002/003 from v9.0).

**Build 2 modifications:**
- Add "CONTRACT COMPLIANCE REVIEW" section: reviewer must verify every API endpoint against its contract via MCP
- Add contract violation as a review failure condition (currently only checks field names)
- Reviewer should query Codebase Intelligence for cross-file impact analysis

#### 2.2.4 build_orchestrator_prompt (Lines 2000-2250)

**Current content:** 15-stage pipeline instructions, technology context, codebase map injection, tech research content injection.

**Build 2 modifications:**
- Add Contract Engine MCP server to orchestrator's available tools
- Add Codebase Intelligence MCP server to orchestrator's available tools
- Add contract compliance verification as a gate between stages
- If agent teams mode: instructions for delegate mode coordination

#### 2.2.5 build_milestone_execution_prompt (Lines 2250-2500)

**Current content:** 9-step MILESTONE WORKFLOW block, TASK ASSIGNER, integration verification, handoff generation.

**Build 2 modifications:**
- Step 2 (analysis) should include contract queries: "Query Contract Engine for all contracts relevant to this milestone"
- Step 5 (implementation) should include artifact registration: "After creating each file, call register_artifact()"
- Step 8 (integration verification) should include contract validation: "Validate all endpoints against contracts"
- Add contract compliance as a milestone completion gate

#### 2.2.6 build_decomposition_prompt (Lines 1800-2000)

**Current content:** PRD decomposition into milestones, MASTER_PLAN.md generation, complexity estimation.

**Build 2 modifications:**
- Add instruction to consider contract dependencies when ordering milestones
- Add instruction to include contract registration/validation tasks in each milestone

#### 2.2.7 Prompt Injection Points (6 existing from tracking_documents.py)

**Current injection architecture:** Prompt text is composed by concatenating base prompts with conditional sections. `agents.py:2050-2100` shows the pattern — `tech_research_content` parameter is appended when available.

**Build 2 pattern:** Follow the same injection pattern for contract context and codebase intelligence context. Add `contract_context: str = ""` and `codebase_index_context: str = ""` parameters to `build_orchestrator_prompt()` and `build_milestone_execution_prompt()`.

---

### 2.3 quality_checks.py — ADD ~300 lines (Currently 4,347 lines)

All static analysis scan functions. Build 2 adds CONTRACT-001..004 patterns.

#### 2.3.1 Existing Scan Architecture

Every scan function follows the same pattern:
```python
def run_xxx_scan(project_dir: Path, scope: ScanScope | None = None) -> list[Violation]:
    violations = []
    files = _get_files(project_dir, extensions, scope)
    for file_path in files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Pattern matching logic
        if match:
            violations.append(Violation(check="XXX-NNN", ...))
    return violations[:_MAX_VIOLATIONS]
```

**Key classes** (from quality_checks.py):
- `Violation` dataclass: `.check` (str), `.file_path` (str), `.line` (int), `.message` (str), `.severity` (str)
- `ScanScope` dataclass: `.changed_files` (set[str]), `.mode` (str)
- `SvcContract` dataclass (v9.0): parsed SVC-xxx table rows

#### 2.3.2 New CONTRACT Scans Needed

**CONTRACT-001: Endpoint Schema Mismatch**
- Parse REQUIREMENTS.md for SVC-xxx contract definitions (existing `_parse_svc_table()` at line ~3800)
- For each contracted endpoint, find the implementing file
- Verify response schema field names and types match the contract
- Severity: "error"

**CONTRACT-002: Missing Contracted Endpoint**
- For each SVC-xxx entry, verify a corresponding route/controller exists
- Check both backend routes and frontend service calls
- Severity: "error"

**CONTRACT-003: Event Schema Mismatch** (AsyncAPI)
- Parse any AsyncAPI specs in the project
- Verify event publishers emit the contracted schema
- Verify event consumers handle the contracted schema
- Severity: "error"

**CONTRACT-004: Shared Model Type Drift**
- Parse JSON Schema definitions for shared models
- Verify TypeScript/Python/C# type definitions match
- Check for camelCase/snake_case mismatches across service boundaries
- Severity: "error"

**Integration with existing infrastructure:**
- Follow `run_api_contract_scan()` pattern (line ~3750)
- Use `_get_files()` with appropriate extensions
- Return `list[Violation]` with standard format
- Wire into cli.py scan pipeline with `max_scan_fix_passes` loop

#### 2.3.3 Existing v9.0 API Contract Scan (Lines 3750-4050)

**Current `run_api_contract_scan()`:** Parses SVC-xxx tables from REQUIREMENTS.md, extracts field schemas, checks backend DTOs (API-001), frontend models (API-002), and type compatibility (API-003).

**Build 2 enhancement:** The current scan is purely static (regex-based). Build 2 should add an optional MCP-enhanced mode that calls Contract Engine's `validate_endpoint()` for live validation. The static scan remains as a fast pre-check; the MCP validation is the authoritative check.

---

### 2.4 config.py — ADD ~100 lines (Currently 1,311 lines)

21 config dataclasses loaded from YAML with `_dict_to_config()` returning `tuple[AgentTeamConfig, set[str]]`.

#### 2.4.1 New Config Dataclasses Needed

```python
@dataclass
class AgentTeamsConfig:
    """Configuration for Claude Code Agent Teams integration."""
    enabled: bool = False  # Disabled by default (experimental)
    fallback_to_cli: bool = True  # Fall back to subprocess if agent teams fails
    delegate_mode: bool = True  # Lead coordinates only, never implements
    max_teammates: int = 5  # Max concurrent teammates
    teammate_idle_timeout: int = 300  # Seconds before idle teammate is reassigned
    task_completed_hook: bool = True  # Enable TaskCompleted convergence hook

@dataclass
class ContractEngineConfig:
    """Configuration for Build 1 Contract Engine MCP integration."""
    enabled: bool = False  # Disabled when Build 1 not available
    mcp_command: str = "python"  # Command to start Contract Engine MCP
    mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.contract_engine.mcp_server"])
    database_path: str = ""  # Path to contracts.db
    validation_on_build: bool = True  # Validate endpoints during build
    test_generation: bool = True  # Generate contract tests

@dataclass
class CodebaseIntelligenceConfig:
    """Configuration for Build 1 Codebase Intelligence MCP integration."""
    enabled: bool = False  # Disabled when Build 1 not available
    mcp_command: str = "python"
    mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.codebase_intelligence.mcp_server"])
    database_path: str = ""  # Path to symbols.db
    chroma_path: str = ""  # Path to ChromaDB
    graph_path: str = ""  # Path to NetworkX graph
    replace_static_map: bool = True  # Replace CODEBASE_MAP.md with live queries
    register_artifacts: bool = True  # Auto-register generated files

@dataclass
class ContractScanConfig:
    """Configuration for CONTRACT-001..004 scans."""
    endpoint_schema_scan: bool = True  # CONTRACT-001
    missing_endpoint_scan: bool = True  # CONTRACT-002
    event_schema_scan: bool = True  # CONTRACT-003
    shared_model_scan: bool = True  # CONTRACT-004
```

#### 2.4.2 Integration with AgentTeamConfig

**Current `AgentTeamConfig`** (config.py:1100-1311) is the root dataclass with nested configs for milestones, E2E testing, browser testing, design reference, tracking documents, database scans, integrity scans, post-orchestration scans, and tech research.

**Build 2 additions to `AgentTeamConfig`:**
```python
agent_teams: AgentTeamsConfig = field(default_factory=AgentTeamsConfig)
contract_engine: ContractEngineConfig = field(default_factory=ContractEngineConfig)
codebase_intelligence: CodebaseIntelligenceConfig = field(default_factory=CodebaseIntelligenceConfig)
contract_scans: ContractScanConfig = field(default_factory=ContractScanConfig)
```

#### 2.4.3 Depth Gating

**Current pattern** (config.py:1200-1270): `_apply_depth_defaults()` function sets defaults based on depth level.

**Build 2 depth gating:**
| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| Agent Teams | off | off | enabled | enabled |
| Contract Engine MCP | off | enabled (validation only) | enabled (full) | enabled (full) |
| Codebase Intelligence MCP | off | enabled (queries only) | enabled (full + registration) | enabled (full + registration) |
| CONTRACT scans | off | 001-002 only | all 4 | all 4 |

#### 2.4.4 _dict_to_config() Modification

**Current signature** (config.py:1000): `def _dict_to_config(raw: dict) -> tuple[AgentTeamConfig, set[str]]`

**Build 2:** Add parsing for the 4 new config sections. Follow the existing pattern of nested dataclass construction with user-override tracking.

---

### 2.5 state.py — ADD ~50 lines (Currently 305 lines)

#### 2.5.1 New Dataclasses

```python
@dataclass
class ContractReport:
    """Report from contract compliance verification."""
    total_contracts: int = 0
    verified_contracts: int = 0
    violated_contracts: int = 0
    missing_implementations: int = 0
    violations: list[dict] = field(default_factory=list)
    health: str = "unknown"  # passed | partial | failed | unknown

@dataclass
class IntegrationReport:
    """Report from cross-service integration verification."""
    total_endpoints: int = 0
    tested_endpoints: int = 0
    passed_endpoints: int = 0
    failed_endpoints: int = 0
    untested_contracts: list[str] = field(default_factory=list)
    health: str = "unknown"
```

#### 2.5.2 RunState Modifications

**Current `RunState`** (state.py:50-120) tracks: completed_phases, total_cost, convergence_reports, e2e_report, browser_test_report, completed_browser_workflows.

**Build 2 additions:**
```python
contract_report: ContractReport = field(default_factory=ContractReport)
integration_report: IntegrationReport = field(default_factory=IntegrationReport)
agent_teams_active: bool = False
registered_artifacts: list[str] = field(default_factory=list)
```

---

### 2.6 mcp_servers.py — ADD ~60 lines (Currently 171 lines)

#### 2.6.1 Current Structure

```python
def get_mcp_servers(config) -> dict:
    """Returns MCP server configs for: firecrawl, context7, sequential-thinking"""

def get_browser_testing_servers(config) -> dict:
    """Returns: playwright"""

def get_context7_only_servers() -> dict:
    """Returns: context7 only (for tech research)"""

def _playwright_mcp_server() -> dict:
    """Internal helper for Playwright config"""
```

#### 2.6.2 New Functions Needed

```python
def _contract_engine_mcp_server(config: ContractEngineConfig) -> dict:
    """MCP server config for Contract Engine."""
    return {
        "command": config.mcp_command,
        "args": config.mcp_args,
        "env": {
            "DATABASE_PATH": config.database_path,
        }
    }

def _codebase_intelligence_mcp_server(config: CodebaseIntelligenceConfig) -> dict:
    """MCP server config for Codebase Intelligence."""
    return {
        "command": config.mcp_command,
        "args": config.mcp_args,
        "env": {
            "DATABASE_PATH": config.database_path,
            "CHROMA_PATH": config.chroma_path,
            "GRAPH_PATH": config.graph_path,
        }
    }

def get_contract_aware_servers(config) -> dict:
    """Returns all standard servers + Contract Engine + Codebase Intelligence."""
    servers = get_mcp_servers(config)
    if config.contract_engine.enabled:
        servers["contract-engine"] = _contract_engine_mcp_server(config.contract_engine)
    if config.codebase_intelligence.enabled:
        servers["codebase-intelligence"] = _codebase_intelligence_mcp_server(config.codebase_intelligence)
    return servers
```

---

### 2.7 contracts.py — HEAVY MODIFICATION (651 lines)

#### 2.7.1 Current Structure

- `ExportedSymbol` dataclass: name, kind, file_path, line, signature
- `ModuleContract` dataclass: module_path, exports, imports, dependencies
- `WiringContract` dataclass: source, target, mechanism
- `ContractRegistry` class: load/save from JSON, verify contracts against codebase
- Verification functions: AST-based and regex-based import/export checking

#### 2.7.2 Build 2 Modifications

**The current `contracts.py` manages local module-to-module contracts (intra-service wiring).** Build 2 needs to add **inter-service contract management** that bridges to the Contract Engine MCP.

**New classes needed:**
```python
@dataclass
class ServiceContract:
    """A contract between two services (from Contract Engine)."""
    contract_id: str
    contract_type: str  # "openapi" | "asyncapi" | "json_schema"
    provider_service: str
    consumer_service: str
    version: str
    spec_hash: str
    spec: dict  # The actual OpenAPI/AsyncAPI/JSON Schema spec
    implemented: bool = False
    evidence_path: str = ""

class ServiceContractRegistry:
    """Registry of inter-service contracts, backed by Contract Engine MCP."""

    def load_from_mcp(self, mcp_client) -> None:
        """Load all contracts from Contract Engine MCP server."""

    def load_from_local(self, path: Path) -> None:
        """Load from local cache (fallback when MCP unavailable)."""

    def validate_endpoint(self, service_name, method, path, response) -> dict:
        """Validate an endpoint against its contract via MCP."""

    def mark_implemented(self, contract_id, service_name, evidence) -> bool:
        """Mark a contract as implemented via MCP."""

    def get_unimplemented(self) -> list[ServiceContract]:
        """Get all unimplemented contracts."""

    def save_local_cache(self, path: Path) -> None:
        """Cache contracts locally for offline/fallback use."""
```

**Key design decision:** The existing `ContractRegistry` (intra-service) and new `ServiceContractRegistry` (inter-service) coexist. Build 2 does not replace the existing contract system — it adds a layer on top.

---

### 2.8 codebase_map.py — CONDITIONAL REPLACEMENT (957 lines)

#### 2.8.1 Current Structure

- `ModuleInfo` dataclass: path, language, imports, exports, classes, functions, dependencies
- `ImportEdge` dataclass: source, target, symbols
- `CodebaseMap` class: async generation with timeout, file walking, AST extraction
- `generate_codebase_map()` async function: entry point, returns markdown content

#### 2.8.2 Build 2 Modifications

**When Codebase Intelligence MCP is available:** Replace the static generation with live queries.

```python
async def generate_codebase_map_from_mcp(mcp_client, service_name: str) -> str:
    """Generate CODEBASE_MAP.md content from Codebase Intelligence MCP queries.

    Calls:
    - get_service_interface(service_name) for API surface
    - find_dependencies(file) for each key file
    - search_semantic("architecture overview") for high-level structure
    """
```

**When MCP is unavailable:** Fall back to existing `generate_codebase_map()`. The existing code is preserved entirely.

**New function for artifact registration:**
```python
async def register_new_artifact(mcp_client, file_path: str, service_name: str) -> dict:
    """Register a newly generated file with Codebase Intelligence.

    Calls register_artifact(file_path, service_name) via MCP.
    Returns: {indexed: bool, symbols_found: int, dependencies_found: int}
    """
```

---

### 2.9 scheduler.py — UPGRADE/ABSTRACTION (1,369 lines)

#### 2.9.1 Current Structure

- `TaskNode` dataclass: id, description, files, dependencies, priority, estimated_cost
- `ExecutionWave` dataclass: tasks grouped by dependency level
- `TaskScheduler` class: Kahn's algorithm for topological sort, wave computation, conflict detection
- `_parse_bullet_format_tasks()`: Parses TASKS.md into TaskNode objects
- Critical path computation, file conflict detection, parallel execution planning

#### 2.9.2 Build 2 Modifications

**The scheduler is the core of orchestration and the primary candidate for agent teams abstraction.**

**Abstraction layer design:**

```python
class ExecutionBackend(Protocol):
    """Abstract interface for task execution backends."""

    async def execute_wave(self, wave: ExecutionWave, context: dict) -> list[TaskResult]:
        """Execute a wave of parallel tasks."""

    async def execute_task(self, task: TaskNode, context: dict) -> TaskResult:
        """Execute a single task."""

    def supports_peer_messaging(self) -> bool:
        """Whether teammates can message each other."""

    def supports_self_claiming(self) -> bool:
        """Whether teammates auto-claim next available tasks."""

class CLIExecutionBackend(ExecutionBackend):
    """Existing subprocess-based execution (proven, fallback)."""
    # Wraps current scheduler.py logic

class AgentTeamsExecutionBackend(ExecutionBackend):
    """Claude Code Agent Teams execution (experimental)."""
    # Uses TaskCreate, TaskUpdate, SendMessage
    # Maps TaskNode to Agent Teams tasks
    # Maps ExecutionWave to parallel task groups
```

**Key decision:** The `TaskScheduler` (Kahn's algorithm, wave computation, conflict detection) is preserved regardless of backend. Only the execution layer changes. The scheduler computes WHAT to run and in what order; the backend determines HOW to run it.

**Agent Teams task mapping:**
| scheduler.py concept | Agent Teams API |
|---------------------|-----------------|
| `TaskNode` | `TaskCreate(subject, description)` |
| `TaskNode.dependencies` | `TaskUpdate(addBlockedBy=[...])` |
| `ExecutionWave` (parallel group) | Tasks with no blockedBy (self-claiming) |
| Wave-level synchronization | `TaskList()` polling for all completed |
| Task result collection | `SendMessage(type="message")` from teammate |

---

### 2.10 code_quality_standards.py — ADD ~40 lines (Currently 665 lines)

#### 2.10.1 Current Structure

11 standards constants mapped to agent roles via `_AGENT_STANDARDS_MAP`:
- `MOCK_DATA_STANDARDS`, `UI_COMPLIANCE_STANDARDS`, `E2E_TESTING_STANDARDS`
- `DATABASE_INTEGRITY_STANDARDS`, `API_CONTRACT_STANDARDS`
- Plus 6 more for deployment, asset, browser testing, etc.

#### 2.10.2 New Standards Needed

```python
CONTRACT_COMPLIANCE_STANDARDS = """
## Contract Compliance Standards

### CONTRACT-001: Endpoint Schema Match
Every API endpoint MUST return a response body whose field names and types
exactly match the OpenAPI spec registered in the Contract Engine.

### CONTRACT-002: Endpoint Existence
Every endpoint defined in SVC-xxx contracts MUST have a corresponding
route/controller implementation.

### CONTRACT-003: Event Schema Match
Every event publisher MUST emit payloads matching the AsyncAPI spec.
Every event consumer MUST handle the exact contracted schema.

### CONTRACT-004: Shared Model Consistency
Shared data model types (defined as JSON Schema) MUST be implemented
identically across all services that reference them.
"""

INTEGRATION_STANDARDS = """
## Cross-Service Integration Standards

### INT-001: Service Discovery
Services MUST use environment variables for inter-service URLs, never hardcoded.

### INT-002: Trace ID Propagation
Every HTTP request MUST include a trace_id header that propagates across services.

### INT-003: Error Boundary
Service boundary errors MUST be caught and wrapped in a standard error response format.

### INT-004: Health Endpoint
Every service MUST expose /health or /api/health returning {status, service_name, version}.
"""
```

**Wire into `_AGENT_STANDARDS_MAP`:** Map CONTRACT standards to code-writer, code-reviewer, and architect roles. Map INTEGRATION standards to code-writer and code-reviewer.

---

### 2.11 tracking_documents.py — ADD ~100 lines (Currently ~988 lines)

#### 2.11.1 Current Documents

1. `E2E_COVERAGE_MATRIX.md` — Maps PRD features to E2E test coverage
2. `FIX_CYCLE_LOG.md` — Logs every fix cycle with violations and resolutions
3. `MILESTONE_HANDOFF.md` — Interface documentation between milestones

#### 2.11.2 New Document Needed

**CONTRACT_COMPLIANCE_MATRIX.md** — Maps every contracted endpoint/event to its implementation status.

```markdown
# Contract Compliance Matrix

## OpenAPI Contracts
| Contract ID | Endpoint | Provider | Consumer | Implemented | Verified | Violations |
|-------------|----------|----------|----------|-------------|----------|------------|
| SVC-001 | GET /api/users | auth-service | all | YES | YES | 0 |
| SVC-002 | POST /api/orders | core-api | billing | YES | PARTIAL | 2 |

## AsyncAPI Contracts
| Contract ID | Channel | Publisher | Subscriber | Implemented | Verified |
|-------------|---------|-----------|------------|-------------|----------|
| EVT-001 | order.created | core-api | billing | YES | NO |

## Shared Models
| Model | JSON Schema | Services Using | Consistent |
|-------|-------------|----------------|------------|
| User | user.schema.json | auth, core, admin | YES |
```

**Functions needed:**
- `generate_contract_compliance_matrix()` — Produces the matrix from contract data
- `parse_contract_compliance_matrix()` — Parses the matrix for automated checks
- `update_contract_compliance_entry()` — Updates a single entry after verification

---

### 2.12 milestone_manager.py — MINIMAL CHANGES (934 lines)

#### 2.12.1 Current Structure

- `parse_master_plan()` — Parses MASTER_PLAN.md for milestone definitions
- `check_milestone_health()` — Checks REQUIREMENTS.md completion per milestone
- `aggregate_milestone_convergence()` — Aggregates per-milestone health into overall report
- `update_master_plan_status()` — Updates MASTER_PLAN.md status markers

#### 2.12.2 Build 2 Modifications

**Minor:** Add contract compliance to milestone health calculation. Currently health is purely based on `[x]`/`[ ]` checkbox counts in REQUIREMENTS.md. Build 2 should also factor in contract violations when computing milestone health.

```python
# In check_milestone_health():
# Current: health based on checkbox_ratio
# Build 2: health = min(checkbox_ratio, contract_compliance_ratio)
```

---

### 2.13 e2e_testing.py — ADD ~50 lines (Currently ~973 lines)

#### 2.13.1 Current Structure

- `AppTypeInfo` dataclass: has_backend, has_frontend, backend_framework, frontend_framework
- `detect_app_type()` — Parses package.json/requirements.txt/angular.json
- `parse_e2e_results()` — Parses E2E_RESULTS.md
- `E2E_BACKEND_PROMPT`, `E2E_FRONTEND_PROMPT`, `E2E_FIX_PROMPT` constants

#### 2.13.2 Build 2 Modifications

**Add contract compliance E2E prompt:**

```python
E2E_CONTRACT_COMPLIANCE_PROMPT = """
You are a contract compliance tester. For each SVC-xxx contract in REQUIREMENTS.md:
1. Make an HTTP request to the actual endpoint
2. Call Contract Engine validate_endpoint() with the response
3. Record pass/fail for each contract
4. Write results to CONTRACT_E2E_RESULTS.md

Focus on:
- Field name exact match (camelCase vs snake_case)
- Required fields present
- Status codes match contracted codes
- Pagination parameters match
"""
```

**Add to `detect_app_type()`:** Detect whether Contract Engine and Codebase Intelligence MCP servers are available (check for `.mcp.json` or config).

---

### 2.14 browser_testing.py — NO CHANGES (1,219 lines)

Browser testing is UI-focused and independent of Build 2's contract/MCP concerns.

---

### 2.15 design_reference.py — NO CHANGES (~666 lines)

Design reference extraction is UI-focused.

---

### 2.16 tech_research.py — MINOR ADDITION (~746 lines)

**Add Build 1 service queries to tech research:** When Contract Engine or Codebase Intelligence are available, include their capabilities in the tech research results. This helps the orchestrator understand what MCP tools are available.

---

### 2.17 prd_chunking.py — NO CHANGES (225 lines)

PRD chunking is format-agnostic and works with any PRD content.

---

### 2.18 verification.py — ADD ~80 lines (~1,141 lines)

#### 2.18.1 Current Structure

Convergence verification functions that check requirement completion.

#### 2.18.2 Build 2 Additions

**Contract compliance verification:**
```python
def verify_contract_compliance(project_dir: Path, contract_registry) -> dict:
    """Verify all contracts are implemented and passing.

    Returns: {
        total_contracts: int,
        implemented: int,
        verified: int,
        violations: list[dict],
        health: str  # passed | partial | failed
    }
    """
```

---

## 3. NEW FILES NEEDED

### 3.1 src/agent_team/agent_teams_backend.py (~500 lines)

**The Agent Teams abstraction layer.** This is the most architecturally significant new file.

```python
"""
Agent Teams abstraction layer with fallback to CLI execution.

Provides a unified interface for task execution that can use either:
- Mode A: Claude Code Agent Teams (native, experimental)
- Mode B: Current subprocess-based orchestration (proven, fallback)
"""

class AgentTeamsBackend:
    """Claude Code Agent Teams execution backend."""

    async def create_team(self, config: AgentTeamsConfig) -> Team:
        """Create a new agent team with configured teammates."""

    async def assign_task(self, team: Team, task: TaskNode) -> None:
        """Assign a task to the team's task list."""

    async def send_message(self, team: Team, recipient: str, content: str) -> None:
        """Send a message to a specific teammate."""

    async def wait_for_completion(self, team: Team, timeout: int) -> list[TaskResult]:
        """Wait for all tasks to complete or timeout."""

    async def shutdown_team(self, team: Team) -> None:
        """Gracefully shut down all teammates."""

class CLIBackend:
    """Existing subprocess-based execution (proven fallback)."""
    # Wraps existing _run_single / _run_prd_milestones logic

def create_execution_backend(config: AgentTeamConfig) -> AgentTeamsBackend | CLIBackend:
    """Factory: returns appropriate backend based on config and environment."""
```

### 3.2 src/agent_team/contract_client.py (~300 lines)

**MCP client for Contract Engine integration.**

```python
"""
MCP client for communicating with Build 1's Contract Engine.

Provides typed wrappers around the 6 Contract Engine MCP tools:
- get_contract(contract_id)
- validate_endpoint(service_name, method, path, response_body)
- generate_tests(contract_id, framework)
- check_breaking_changes(contract_id, new_spec)
- mark_implemented(contract_id, service_name, evidence_path)
- get_unimplemented_contracts(service_name)
"""

class ContractEngineClient:
    """Typed MCP client for Contract Engine."""

    def __init__(self, mcp_session):
        self._session = mcp_session

    async def get_contract(self, contract_id: str) -> dict | None: ...
    async def validate_endpoint(self, service_name: str, method: str, path: str, response_body: dict, status_code: int = 200) -> dict: ...
    async def generate_tests(self, contract_id: str, framework: str = "pytest", include_negative: bool = True) -> str: ...
    async def check_breaking_changes(self, contract_id: str, new_spec: dict) -> list[dict]: ...
    async def mark_implemented(self, contract_id: str, service_name: str, evidence_path: str) -> dict: ...
    async def get_unimplemented_contracts(self, service_name: str | None = None) -> list[dict]: ...
```

### 3.3 src/agent_team/codebase_client.py (~250 lines)

**MCP client for Codebase Intelligence integration.**

```python
"""
MCP client for communicating with Build 1's Codebase Intelligence service.

Provides typed wrappers around the 7 Codebase Intelligence MCP tools:
- find_definition(symbol, language)
- find_callers(symbol, max_results)
- find_dependencies(file_path)
- search_semantic(query, n_results)
- get_service_interface(service_name)
- check_dead_code(service_name)
- register_artifact(file_path, service_name)
"""

class CodebaseIntelligenceClient:
    """Typed MCP client for Codebase Intelligence."""

    def __init__(self, mcp_session):
        self._session = mcp_session

    async def find_definition(self, symbol: str, language: str | None = None) -> dict: ...
    async def find_callers(self, symbol: str, max_results: int = 50) -> list[dict]: ...
    async def find_dependencies(self, file_path: str) -> dict: ...
    async def search_semantic(self, query: str, n_results: int = 10) -> list[dict]: ...
    async def get_service_interface(self, service_name: str) -> dict: ...
    async def check_dead_code(self, service_name: str | None = None) -> list[dict]: ...
    async def register_artifact(self, file_path: str, service_name: str) -> dict: ...
```

### 3.4 src/agent_team/hooks.py (~200 lines)

**Hook configuration generator for convergence enforcement.**

```python
"""
Generates .claude/hooks.json configuration for agent teams convergence enforcement.

Hook events used:
- TaskCompleted: Verify all requirements met before marking complete
- TeammateIdle: Rebalance workload if tasks remain
- Stop: Final quality gate verification
"""

def generate_hooks_config(config: AgentTeamConfig, requirements_path: Path) -> dict:
    """Generate hooks.json content for agent teams enforcement."""

def generate_task_completed_hook(requirements_path: Path) -> dict:
    """Hook that verifies convergence on task completion."""

def generate_teammate_idle_hook() -> dict:
    """Hook that rebalances work when a teammate goes idle."""

def generate_stop_hook(scan_config) -> dict:
    """Hook that runs final quality gate on session stop."""
```

### 3.5 src/agent_team/claude_md_generator.py (~300 lines)

**CLAUDE.md generation for agent teams teammates.**

```python
"""
Generates CLAUDE.md files for agent teams teammates.

Each teammate gets a CLAUDE.md that includes:
1. Role-specific prompt (from agents.py templates)
2. Service-specific context (contracts, dependencies)
3. MCP server configurations (Contract Engine, Codebase Intelligence)
4. Convergence mandates and review criteria
5. Scan directives relevant to the role
"""

def generate_claude_md(
    role: str,  # "architect" | "code-writer" | "code-reviewer" | "test-engineer"
    service_name: str,
    contracts: list[ServiceContract],
    dependencies: list[str],
    mcp_servers: dict,
    quality_standards: str,
    convergence_config: dict,
) -> str:
    """Generate complete CLAUDE.md content for a teammate."""

def write_teammate_claude_md(
    project_dir: Path,
    role: str,
    service_name: str,
    config: AgentTeamConfig,
) -> Path:
    """Write CLAUDE.md to the appropriate directory."""
```

---

## 4. CROSS-CUTTING CONCERNS

### 4.1 MCP Client Session Management

**Build 1 uses `mcp.server` (server-side).** Build 2 uses `mcp.client` (client-side). From BUILD2_TECHNOLOGY_RESEARCH.md Section 3:

```python
from mcp import stdio_client, StdioServerParameters, ClientSession

async def create_mcp_session(command: str, args: list[str], env: dict) -> ClientSession:
    params = StdioServerParameters(command=command, args=args, env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
```

**Key pattern:** MCP sessions are async context managers. Every function that calls an MCP tool must be async. This aligns with the existing codebase which is already heavily async (cli.py uses `async def main()`, all sub-orchestrator functions are async).

### 4.2 Error Handling and Fallback

Every MCP call must have a fallback path:

```python
try:
    result = await contract_client.validate_endpoint(...)
except (ConnectionError, TimeoutError, MCPError):
    logger.warning("Contract Engine MCP unavailable, falling back to static scan")
    result = run_api_contract_scan(...)  # Existing static scan
```

This pattern must be consistent across all MCP integration points.

### 4.3 Config Loading Backward Compatibility

**Current `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]`.** New config sections must have sensible defaults so existing `config.yaml` files (without Build 2 sections) continue to work. All new features default to `enabled: False`.

### 4.4 Test Strategy

**Existing test infrastructure:** 5,410+ tests across 30+ test files. Every new feature needs:
1. Unit tests for new functions/classes
2. Wiring tests verifying CLI integration points
3. Config tests verifying depth gating and backward compatibility
4. Scan pattern tests for CONTRACT-001..004

**Estimated new tests:** ~200-300 across ~6 new test files.

---

## 5. DEPENDENCY GRAPH — Build 2 Internal

```
M1: Agent Teams Abstraction Layer
    - agent_teams_backend.py (NEW)
    - hooks.py (NEW)
    - claude_md_generator.py (NEW)
    - scheduler.py (MODIFY — add ExecutionBackend protocol)
    - config.py (ADD — AgentTeamsConfig)

M2: Contract Engine Integration
    - contract_client.py (NEW)
    - contracts.py (MODIFY — add ServiceContractRegistry)
    - quality_checks.py (ADD — CONTRACT-001..004)
    - code_quality_standards.py (ADD — CONTRACT standards)
    - config.py (ADD — ContractEngineConfig, ContractScanConfig)
    - mcp_servers.py (ADD — contract engine server)

M3: Codebase Intelligence Integration
    - codebase_client.py (NEW)
    - codebase_map.py (MODIFY — add MCP-backed generation)
    - config.py (ADD — CodebaseIntelligenceConfig)
    - mcp_servers.py (ADD — codebase intelligence server)

M4: Pipeline Integration (depends on M1, M2, M3)
    - cli.py (MODIFY — all integration points)
    - agents.py (MODIFY — prompt injections)
    - state.py (ADD — ContractReport, IntegrationReport)

M5: Tracking and Verification (depends on M4)
    - tracking_documents.py (ADD — CONTRACT_COMPLIANCE_MATRIX)
    - verification.py (ADD — contract compliance verification)
    - milestone_manager.py (MODIFY — contract-aware health)

M6: E2E Testing (depends on M4)
    - e2e_testing.py (ADD — contract compliance E2E)
    - cli.py (MODIFY — contract E2E wiring)
```

---

## 6. RISK ANALYSIS — Code-Level

### 6.1 HIGH RISK: cli.py Complexity

At 6,214 lines, `cli.py` is already the largest and most complex file. Build 2 adds ~200-400 more lines. Risk: merge conflicts, regression in existing pipeline stages, difficulty testing individual phases.

**Mitigation:** Extract Build 2 additions into separate functions that cli.py calls. Keep the main pipeline flow clean. Each new function is independently testable.

### 6.2 HIGH RISK: MCP Client Reliability

MCP client sessions can fail (process crash, timeout, protocol error). Every MCP integration point needs robust error handling with fallback to the existing static approach.

**Mitigation:** The `try/except → fallback` pattern documented in Section 4.2. Every MCP call has a local fallback.

### 6.3 MEDIUM RISK: Agent Teams Experimental Status

Claude Code Agent Teams has no session resumption. If a teammate crashes, its state is lost. The coordination quality is unproven at scale.

**Mitigation:** The abstraction layer (Section 3.1) ensures Agent Teams is optional. The CLIBackend fallback is proven over 14 versions.

### 6.4 MEDIUM RISK: Config Proliferation

Adding 4 new config dataclasses to an already complex config system (21 existing dataclasses). Risk: config validation complexity, depth gating interactions.

**Mitigation:** Follow existing patterns exactly. All new features default to `enabled: False`. Depth gating is additive (new features only activate at higher depths).

### 6.5 LOW RISK: Test Count

Adding ~200-300 new tests to a 5,410+ test suite. Risk: test execution time, flaky MCP-dependent tests.

**Mitigation:** MCP-dependent tests use mocks. Only integration tests require actual MCP servers.

---

## 7. MODIFICATION SUMMARY TABLE

| File | Current LOC | Action | Est. Added LOC | Impact |
|------|-------------|--------|----------------|--------|
| cli.py | 6,214 | MODIFY | +300 | Agent teams mode, contract scans, MCP wiring |
| agents.py | 2,622 | MODIFY | +200 | Contract awareness in all prompts |
| quality_checks.py | 4,347 | ADD | +300 | CONTRACT-001..004 scan patterns |
| config.py | 1,311 | ADD | +100 | 4 new config dataclasses |
| contracts.py | 651 | MODIFY | +150 | ServiceContractRegistry |
| scheduler.py | 1,369 | MODIFY | +100 | ExecutionBackend protocol |
| state.py | 305 | ADD | +50 | ContractReport, IntegrationReport |
| mcp_servers.py | 171 | ADD | +60 | 2 new MCP server configs |
| code_quality_standards.py | 665 | ADD | +40 | CONTRACT + INTEGRATION standards |
| tracking_documents.py | 988 | ADD | +100 | CONTRACT_COMPLIANCE_MATRIX |
| codebase_map.py | 957 | MODIFY | +50 | MCP-backed generation option |
| milestone_manager.py | 934 | MODIFY | +20 | Contract-aware health |
| e2e_testing.py | 973 | ADD | +50 | Contract compliance E2E |
| verification.py | 1,141 | ADD | +80 | Contract compliance verification |
| tech_research.py | 746 | MINOR | +20 | Build 1 service detection |
| agent_teams_backend.py | NEW | CREATE | +500 | Agent Teams abstraction layer |
| contract_client.py | NEW | CREATE | +300 | Contract Engine MCP client |
| codebase_client.py | NEW | CREATE | +250 | Codebase Intelligence MCP client |
| hooks.py | NEW | CREATE | +200 | Hook config generation |
| claude_md_generator.py | NEW | CREATE | +300 | CLAUDE.md generation for teammates |
| **TOTAL** | **28,749** | | **+3,170** | **~31,919 LOC estimated** |

---

## 8. BUILD 1 MCP TOOL SIGNATURES (For Reference)

### 8.1 Contract Engine (6 tools)

```
get_contract(contract_id: str) -> {id, type, version, spec, hash} | None
validate_endpoint(service_name, method, path, response_body, status_code=200) -> {valid: bool, violations: [{field, expected, actual}]}
generate_tests(contract_id, framework="pytest", include_negative=True) -> str (test file content)
check_breaking_changes(contract_id, new_spec: dict) -> [{change, severity, affected_consumers}]
mark_implemented(contract_id, service_name, evidence_path) -> {marked: bool, total, all_implemented}
get_unimplemented_contracts(service_name) -> [{id, type, expected_service}]
```

### 8.2 Codebase Intelligence (7 tools)

```
find_definition(symbol, language=None) -> {file, line, kind, signature}
find_callers(symbol, max_results=50) -> [{file, line, context}]
find_dependencies(file_path) -> {imports, imported_by, transitive_deps}
search_semantic(query, n_results=10) -> [{file, lines, content, score}]
get_service_interface(service_name) -> {endpoints, events_published, events_consumed}
check_dead_code(service_name=None) -> [{symbol, file, line, kind}]
register_artifact(file_path, service_name) -> {indexed, symbols_found, dependencies_found}
```

### 8.3 Architect (3 tools)

```
get_service_map() -> {services: [{name, domain, stack, estimated_loc}]}
get_contracts_for_service(service_name) -> [{id, role, type, counterparty, summary}]
get_domain_model() -> {entities, relationships, state_machines}
```

---

## 9. EXISTING PIPELINE PRESERVATION CHECKLIST

These elements MUST NOT be broken by Build 2 modifications:

- [ ] 15-stage pipeline execution order in main()
- [ ] 13 self-healing fix loops (mock, UI, deployment, asset, PRD, dual_orm, defaults, relationships, api_contract, SDL, XREF, E2E, browser)
- [ ] Post-orchestration scan chain order
- [ ] Milestone-based execution with MASTER_PLAN.md
- [ ] Config-gated features (every scan/feature has a bool gate)
- [ ] Depth-based behavior (quick/standard/thorough/exhaustive)
- [ ] Signal handling (Ctrl+C state save)
- [ ] Resume from STATE.json
- [ ] Contract loading from CONTRACTS.json
- [ ] Convergence health checking
- [ ] GATE 5 enforcement
- [ ] Recovery passes (review, contract, artifact)
- [ ] Tracking document generation (coverage matrix, fix log, handoff)
- [ ] Tech research phase (Context7 integration)
- [ ] PRD chunking for large PRDs
- [ ] _dict_to_config() tuple return type
- [ ] load_config() tuple return type
- [ ] Violation dataclass interface (.check, .file_path, .line, .message, .severity)
- [ ] ScanScope filtering for scoped scans
- [ ] All existing 5,410+ tests passing
