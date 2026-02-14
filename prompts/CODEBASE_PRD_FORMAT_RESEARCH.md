# Codebase PRD Format Research — Agent Team v14.0

> **Purpose**: Reverse-engineered specification of the EXACT PRD format, config structure,
> and scanning rules that the agent-team system expects. Every finding cites `file:line`.
> Generated for the Super Agent Team PRD creation effort.

---

## Table of Contents

1. [PRD Detection & Activation](#1-prd-detection--activation)
2. [PRD File Path Handling](#2-prd-file-path-handling)
3. [Large PRD Chunking](#3-large-prd-chunking)
4. [MASTER_PLAN.md — Exact Format](#4-master_planmd--exact-format)
5. [REQUIREMENTS.md — Exact Format](#5-requirementsmd--exact-format)
6. [TASKS.md — Exact Format](#6-tasksmd--exact-format)
7. [Requirement Identifier Prefixes](#7-requirement-identifier-prefixes)
8. [config.yaml — Complete Template](#8-configyaml--complete-template)
9. [Prompt Templates & Injection Points](#9-prompt-templates--injection-points)
10. [Post-Orchestration Scan Pipeline](#10-post-orchestration-scan-pipeline)
11. [Quality Scan Patterns (All Codes)](#11-quality-scan-patterns-all-codes)
12. [Design Reference System](#12-design-reference-system)
13. [Tech Research Phase](#13-tech-research-phase)
14. [E2E Testing Phase](#14-e2e-testing-phase)
15. [Browser Testing Phase](#15-browser-testing-phase)
16. [Contract Verification System](#16-contract-verification-system)
17. [Verification Pipeline](#17-verification-pipeline)
18. [Convergence Loop Mechanics](#18-convergence-loop-mechanics)
19. [Depth Gating Rules](#19-depth-gating-rules)
20. [Pitfalls & Gotchas](#20-pitfalls--gotchas)

---

## 1. PRD Detection & Activation

### Detection Heuristic
**Source**: `cli.py:229` — `_detect_prd_from_task(task: str) -> bool`

The system auto-detects PRD mode using a signal-count heuristic:

```python
# Signals checked (each adds 1 to signal_count):
# - Length > 3000 characters
# - Contains "milestone" or "milestones"
# - Contains "phase" or "phases"
# - Contains "requirement" or "requirements"
# - Contains "## " (markdown h2 headers)
# - Contains "- [ ]" (checklist items)
# - Contains numbered sections (e.g., "1.", "2.")

# Activation: signal_count >= 2 OR len(task) > 3000
```

### Explicit Activation
- CLI argument: `--prd path/to/prd.md` — forces PRD mode
- The PRD path is stored in `_current_state.artifacts["prd_path"]`

### Two-Phase Execution
**Source**: `cli.py:887` — `_run_prd_milestones()`

1. **Phase 1 — Decomposition**: Creates `MASTER_PLAN.md` in `.agent-team/`
2. **Phase 2 — Per-Milestone Execution**: Iterates milestones, creates per-milestone `REQUIREMENTS.md`

---

## 2. PRD File Path Handling

**Source**: `cli.py:3742+` (main function)

```python
# PRD content is loaded from:
prd_path = args.prd  # CLI argument
prd_content = Path(prd_path).read_text(encoding="utf-8")

# Or detected from task text via _detect_prd_from_task()
# PRD content is injected into the decomposition prompt
```

### Phase Execution Order (PRD Mode)
**Source**: `cli.py:3742-4041`

```
1. Interview Phase (optional)
2. Constraints Loading
3. Codebase Map (Phase 0.5)
4. Design Reference Extraction (Phase 0.6)
5. Tech Research (Phase 1.5)
6. PRD Decomposition → MASTER_PLAN.md
7. Per-Milestone Execution → REQUIREMENTS.md per milestone
8. Post-Orchestration Scans
9. E2E Testing Phase
10. Browser Testing Phase
```

---

## 3. Large PRD Chunking

**Source**: `prd_chunking.py`

### Detection
**Source**: `prd_chunking.py:49` — `detect_large_prd(content, threshold=50*1024)`
- Threshold: **50 KB** (50 * 1024 bytes)
- Returns `True` if `len(content.encode('utf-8')) > threshold`

### Section Patterns
**Source**: `prd_chunking.py:19`
```python
_SECTION_PATTERNS = [
    "features", "database", "api", "frontend", "auth",
    "infrastructure", "testing", "dependencies", "appendix",
]
```

### Chunk Output
**Source**: `prd_chunking.py:112` — `create_prd_chunks()`
- Splits at `#` and `##` heading boundaries
- Chunks written to: `.agent-team/prd-chunks/{section_name}.md`
- Index built by `build_prd_index()` at line 171

---

## 4. MASTER_PLAN.md — Exact Format

### Parsing Regex
**Source**: `milestone_manager.py:101`
```python
_RE_MILESTONE_HEADER = re.compile(
    r"^#{2,4}\s+(?:Milestone\s+)?(\d+)[.:]?\s*(.*)",
    re.MULTILINE,
)
```

**CRITICAL**: Milestones MUST use `##`, `###`, or `####` headers (h2-h4). `#` (h1) will NOT match.

### Field Parsing
**Source**: `milestone_manager.py:104`
```python
_RE_FIELD = re.compile(r"^-\s*(\w[\w\s]*):\s*(.+)", re.MULTILINE)
```

### Milestone Dataclass
**Source**: `milestone_manager.py:32`
```python
@dataclass
class MasterPlanMilestone:
    id: str           # "milestone-1", "milestone-2", etc.
    title: str        # From header text after number
    status: str       # "PENDING" | "IN_PROGRESS" | "COMPLETE" | "FAILED"
    dependencies: list[str]  # ["milestone-1"] or [] for "none"
    description: str  # From Description field
```

### MasterPlan Dataclass
**Source**: `milestone_manager.py:43`
```python
@dataclass
class MasterPlan:
    title: str
    generated: str
    milestones: list[MasterPlanMilestone]
    # Methods: get_ready_milestones(), all_complete()
```

### Exact Template

```markdown
# Master Plan: <Project Title>
Generated: <YYYY-MM-DD HH:MM:SS>

## Milestone 1: Foundation & Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Set up project scaffolding, install dependencies, configure build tools, and create base configuration files.

## Milestone 2: Data Layer
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Create database schema, ORM models, and seed data.

## Milestone 3: API Layer
- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-2
- Description: Implement REST API endpoints with authentication and validation.

## Milestone 4: Frontend
- ID: milestone-4
- Status: PENDING
- Dependencies: milestone-3
- Description: Build UI components, pages, and integrate with API.

## Milestone 5: Integration & Polish
- ID: milestone-5
- Status: PENDING
- Dependencies: milestone-3, milestone-4
- Description: Wire all features together, add error handling, testing.
```

### Status Update
**Source**: `milestone_manager.py` — `update_master_plan_status()`
- Uses the milestone regex to find boundaries between milestones
- Updates the `Status:` field line in-place

### Ready Milestones
**Source**: `milestone_manager.py` — `get_ready_milestones()`
- A milestone is "ready" when: status == "PENDING" AND all dependencies have status "COMPLETE"

### Milestone Directory Structure
```
.agent-team/
  MASTER_PLAN.md
  milestones/
    milestone-1/
      REQUIREMENTS.md
      TASKS.md
      CONTRACTS.json
      VERIFICATION.md
    milestone-2/
      REQUIREMENTS.md
      ...
```

### Normalize Milestone Dirs
**Source**: `milestone_manager.py:501` — `normalize_milestone_dirs()`
- Fixes orphan milestone directories that don't match MASTER_PLAN.md

---

## 5. REQUIREMENTS.md — Exact Format

### Required Sections
**Source**: `agents.py:659` (PLANNER_PROMPT) and `agents.py:836` (ARCHITECT_PROMPT)

The REQUIREMENTS.md is built in two passes:
1. **Planner** creates: Context, Requirements Checklist, Review Log
2. **Architect** adds: Architecture Decision, Integration Roadmap, Wiring Map, Service-to-API Wiring Map

### Complete Template

```markdown
# Requirements Document — <Project Title>

## Context
<Brief description of the project, its purpose, and key constraints>

## Research Findings
<Tech research results injected from TECH_RESEARCH.md>

## Design Standards & Reference
<Design reference data from UI_REQUIREMENTS.md>

## Architecture Decision
### Technology Stack
- Frontend: <framework>
- Backend: <framework>
- Database: <database>
- ORM: <orm>

### File Structure
```
src/
  controllers/
  services/
  models/
  ...
```

### Integration Roadmap

#### Entry Points
| Entry Point | File | Purpose |
|---|---|---|
| Main Server | src/server.ts | Express app initialization |

#### Wiring Map
| ID | Source | Target | Mechanism | Priority |
|---|---|---|---|---|
| WIRE-001 | src/routes/auth.ts | src/server.ts | app.use('/auth', authRouter) | HIGH |

#### Service-to-API Wiring Map
| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|
| SVC-001 | auth.service | login() | POST | /api/auth/login | LoginRequest { email: string, password: string } | LoginResponse { token: string, user: UserDto } |

#### Wiring Anti-Patterns
- Never register routes after middleware
- Never import circular dependencies

#### Initialization Order
1. Database connection
2. Middleware
3. Routes

### Status Registry
| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|
| Tender | status | Draft, Published, Closed | string | string |

## Requirements Checklist

### Functional Requirements
- [ ] REQ-001: <Description> (review_cycles: 0)
- [ ] REQ-002: <Description> (review_cycles: 0)

### Technical Requirements
- [ ] TECH-001: <Description> (review_cycles: 0)

### Integration Requirements
- [ ] INT-001: <Description> (review_cycles: 0)

### Wiring Requirements
- [ ] WIRE-001: Wire auth routes to Express server (review_cycles: 0)

### Service-to-API Wiring
- [ ] SVC-001: auth.service.login() → POST /api/auth/login (review_cycles: 0)

### Design Requirements
- [ ] DESIGN-001: <Description> (review_cycles: 0)

### Test Requirements
- [ ] TEST-001: <Description> (review_cycles: 0)

## Review Log
| Cycle | Agent | Item | Verdict | Issues |
|---|---|---|---|---|
```

### Requirement Checklist Format
**Source**: `milestone_manager.py:440-441`
```python
_CHECKED_RE = re.compile(r'^\s*-\s*\[x\]', re.MULTILINE | re.IGNORECASE)
_UNCHECKED_RE = re.compile(r'^\s*-\s*\[ \]', re.MULTILINE)
```

Format: `- [ ] PREFIX-NNN: Description (review_cycles: N)`
- Checked: `- [x] PREFIX-NNN: Description (review_cycles: N)`
- The `(review_cycles: N)` suffix is mandatory for tracking review passes
- Only `code-reviewer` agents may change `[ ]` to `[x]`

---

## 6. TASKS.md — Exact Format

**Source**: `agents.py:1712-1743` (TASK_ASSIGNER_PROMPT)

```markdown
# Task Breakdown: <Project Title>
Generated: <timestamp>
Total Tasks: <N>
Completed: 0/<N>

## Legend
- Status: PENDING | IN_PROGRESS | COMPLETE
- Dependencies: list of TASK-xxx IDs that must be COMPLETE before this task can start

## Tasks

### TASK-001: <Short title>
- Parent: <REQ-xxx or TECH-xxx>
- Status: PENDING
- Dependencies: none
- Files: <file1>, <file2>
- Description: <Specific description of what to implement>

### TASK-002: <Short title>
- Parent: <REQ-xxx>
- Status: PENDING
- Dependencies: TASK-001
- Files: <file1>
- Description: <Specific description>
```

### Key Rules
- Each task targets **1-3 files MAXIMUM**
- Tasks are numbered sequentially: TASK-001, TASK-002, ...
- Dependencies MUST form a DAG (no circular dependencies)
- Every WIRE-xxx requirement MUST generate a dedicated wiring task
- Wiring tasks targeting the same file need sequential dependencies

---

## 7. Requirement Identifier Prefixes

**Source**: `agents.py` (various prompts) and `quality_checks.py`

| Prefix | Purpose | Created By |
|--------|---------|------------|
| `REQ-NNN` | Functional requirements | Planner |
| `TECH-NNN` | Technical requirements | Planner |
| `INT-NNN` | Integration requirements | Planner |
| `WIRE-NNN` | Wiring/connection requirements | Architect |
| `SVC-NNN` | Service-to-API wiring | Architect |
| `DESIGN-NNN` | Design/UI requirements | Planner/Architect |
| `TEST-NNN` | Testing requirements | Planner |
| `SEC-NNN` | Security requirements (runtime) | Security Auditor |
| `DR-NNN` | Design Reference checklist items | Design Extraction |
| `TASK-NNN` | Task breakdown items | Task Assigner |

### SVC-xxx Table Format (Critical for API Contract Scan)
**Source**: `quality_checks.py` — `_parse_svc_table()` and `_parse_field_schema()`

The SVC-xxx table rows must contain field schemas in this format:
```
| SVC-001 | auth.service | login() | POST | /api/auth/login | LoginRequest { email: string, password: string } | LoginResponse { token: string, user: UserDto } |
```

Key parsing details:
- Field schema extracted from `{ field: type, field: type }` notation
- Class-name-only rows (no braces) produce zero violations
- `_parse_field_schema()` splits on commas between field declarations
- Checks REQUIREMENTS.md + `.agent-team/REQUIREMENTS.md` + milestone REQUIREMENTS.md files

---

## 8. config.yaml — Complete Template

**Source**: `config.py` (all dataclasses, 1311 lines)

### Config Search Order
**Source**: `config.py` — `load_config()`
1. Explicit path argument
2. `./config.yaml` (project root)
3. `~/.agent-team/config.yaml` (user home)
4. Defaults (no config file needed)

### Return Type
**Source**: `config.py:851`
```python
def _dict_to_config(data: dict) -> tuple[AgentTeamConfig, set[str]]:
    # Returns (config, user_overrides)
    # user_overrides tracks which keys the user explicitly set
```

### Complete Template

```yaml
# Agent Team Configuration — v14.0
# All values shown are DEFAULTS — omit any you don't need to change

# --- Orchestrator ---
orchestrator:
  model: "claude-sonnet-4-20250514"  # Model for the orchestrator
  max_turns: 200                      # Max conversation turns
  permission_mode: "plan"             # "plan" | "full" | "auto-edit"

# --- Depth ---
# Controls how thorough the system is. Options: quick, standard, thorough, exhaustive
depth: "standard"

# --- Fleet Sizes ---
fleet:
  coding: 1       # Number of parallel code-writer agents
  review: 1       # Number of parallel code-reviewer agents
  debug: 1        # Number of parallel debugger agents

# --- Convergence ---
convergence:
  requirements_dir: ".agent-team"          # Directory for requirements files
  requirements_file: "REQUIREMENTS.md"     # Requirements filename
  master_plan_file: "MASTER_PLAN.md"       # Master plan filename
  min_convergence_ratio: 0.9               # Min ratio of [x] items to total
  max_review_cycles: 5                     # Max review-fix cycles
  recovery_threshold: 0.7                  # Min ratio before recovery pass

# --- Quality ---
quality:
  spot_checks: true           # Enable anti-pattern scanning
  craft_review: true          # Enable CODE CRAFT review section
  production_defaults: true   # Enable production readiness defaults in planner

# --- Milestone ---
milestone:
  enabled: true                    # Enable milestone-based execution
  health_gate: true                # Gate milestone completion on health
  wiring_check: true               # Check wiring between milestones
  resume_from_milestone: null      # Resume from specific milestone ID
  review_recovery_retries: 3       # Max review recovery retries per milestone
  mock_data_scan: true             # Run mock data scan per milestone (DEPRECATED — use post_orchestration_scans)
  ui_compliance_scan: true         # Run UI compliance scan per milestone (DEPRECATED — use post_orchestration_scans)

# --- Post-Orchestration Scans ---
post_orchestration_scans:
  mock_data_scan: true             # MOCK-001..008 scan
  ui_compliance_scan: true         # UI-001..004 scan
  api_contract_scan: true          # API-001..003 scan
  silent_data_loss_scan: true      # SDL-001, ENUM-004 scan
  endpoint_xref_scan: true         # XREF-001..002 scan
  max_scan_fix_passes: 3           # Max fix passes per scan type

# --- Integrity Scans ---
integrity_scans:
  deployment_scan: true            # DEPLOY-001..004 scan
  asset_scan: true                 # ASSET-001..003 scan
  prd_reconciliation: true         # PRD-001 reconciliation

# --- Database Scans ---
database_scans:
  dual_orm_scan: true              # DB-001..003 scan
  default_value_scan: true         # DB-004..005 scan
  relationship_scan: true          # DB-006..008 scan

# --- Scan Scope ---
scan_scope_mode: "auto"            # "auto" | "full" | "changed"
# auto: depth-based (quick=changed, standard/thorough/exhaustive=full)
# full: always scan all files
# changed: always scope to changed files (git diff)

# --- Design Reference ---
design_reference:
  enabled: true                           # Enable design reference extraction
  urls: []                                # Design reference URLs to scrape
  depth: "full"                           # Extraction depth
  max_pages_per_site: 5                   # Max pages to scrape per URL
  ui_requirements_file: "UI_REQUIREMENTS.md"  # Output filename
  extraction_retries: 2                   # Max retry attempts
  fallback_generation: true               # Generate fallback if extraction fails
  content_quality_check: true             # Validate content quality

# --- Tech Research ---
tech_research:
  enabled: true                    # Enable tech research phase
  max_techs: 6                     # Max technologies to research
  max_queries_per_tech: 3          # Max Context7 queries per tech
  retry_on_incomplete: true        # Retry if research is incomplete
  injection_max_chars: 15000       # Max chars for prompt injection

# --- E2E Testing ---
e2e_testing:
  enabled: false                   # Opt-in (enabled by depth gating for thorough+)
  backend_api_tests: true          # Run backend API tests
  frontend_playwright_tests: true  # Run frontend Playwright tests
  max_fix_retries: 5               # Max fix retries (min 1)
  test_port: 9876                  # Port for test server (1024-65535)
  skip_if_no_api: true             # Skip backend tests if no API detected
  skip_if_no_frontend: true        # Skip frontend tests if no frontend detected

# --- Browser Testing ---
browser_testing:
  enabled: false                   # Opt-in (enabled by depth gating for thorough+ with PRD)
  max_fix_retries: 3               # Max fix retries
  e2e_pass_rate_gate: 0.7          # Min pass rate to proceed
  headless: true                   # Run in headless mode
  app_start_command: null          # Custom app start command
  app_port: null                   # Custom app port
  regression_sweep: true           # Run regression sweep after fixes

# --- Tracking Documents ---
tracking_documents:
  e2e_coverage_matrix: true        # Generate E2E_COVERAGE_MATRIX.md
  fix_cycle_log: true              # Generate FIX_CYCLE_LOG.md
  milestone_handoff: true          # Generate MILESTONE_HANDOFF.md
  coverage_completeness_gate: 0.8  # Min coverage completeness
  wiring_completeness_gate: 1.0    # Min wiring completeness

# --- Verification ---
verification:
  enabled: true                    # Enable contract verification
  contracts_file: "CONTRACTS.json" # Contracts filename

# --- Investigation ---
investigation:
  enabled: false                   # Enable deep investigation protocols
  sequential_thinking: false       # Enable Sequential Thinking MCP
  gemini_integration: false        # Enable Gemini CLI integration

# --- Scheduler ---
scheduler:
  enabled: true                    # Enable task scheduler (wave computation)
  max_parallel_agents: 5           # Max parallel agents per wave

# --- Agents ---
# Per-agent configuration (model, enabled flag)
agents:
  planner:
    enabled: true
    model: "claude-sonnet-4-20250514"
  architect:
    enabled: true
    model: "claude-sonnet-4-20250514"
  task_assigner:
    enabled: true
    model: "claude-sonnet-4-20250514"
  code_writer:
    enabled: true
    model: "claude-sonnet-4-20250514"
  code_reviewer:
    enabled: true
    model: "claude-sonnet-4-20250514"
  test_runner:
    enabled: true
    model: "claude-sonnet-4-20250514"
  debugger:
    enabled: true
    model: "claude-sonnet-4-20250514"
  security_auditor:
    enabled: true
    model: "claude-sonnet-4-20250514"
  researcher:
    enabled: true
    model: "claude-sonnet-4-20250514"
  integration_agent:
    enabled: true
    model: "claude-sonnet-4-20250514"
  contract_generator:
    enabled: true
    model: "claude-sonnet-4-20250514"
```

---

## 9. Prompt Templates & Injection Points

### Prompt Builder Functions
**Source**: `agents.py`

| Function | Line | Purpose |
|----------|------|---------|
| `build_decomposition_prompt()` | 2012 | Creates `[PHASE: PRD DECOMPOSITION]` prompt |
| `build_milestone_execution_prompt()` | 2160 | Creates `[PHASE: MILESTONE EXECUTION]` with 9-step workflow |
| `build_orchestrator_prompt()` | 2394 | Full orchestrator prompt with all context injection |
| `build_agent_definitions()` | 1838 | Builds agent dict with prompts and tools |

### Agent Prompts
**Source**: `agents.py`

| Prompt Constant | Line | Agent |
|-----------------|------|-------|
| `ORCHESTRATOR_SYSTEM_PROMPT` | 28 | Orchestrator (main loop) |
| `PLANNER_PROMPT` | 659 | Creates REQUIREMENTS.md |
| `ARCHITECT_PROMPT` | 836 | Designs architecture, wiring map |
| `CODE_WRITER_PROMPT` | 1005 | Implements code |
| `CODE_REVIEWER_PROMPT` | 1189 | Adversarial review |
| `TEST_RUNNER_PROMPT` | 1500 | Writes and runs tests |
| `SECURITY_AUDITOR_PROMPT` | 1548 | Security audit |
| `DEBUGGER_PROMPT` | 1589 | Fixes review failures |
| `TASK_ASSIGNER_PROMPT` | 1642 | Decomposes requirements into tasks |
| `INTEGRATION_AGENT_PROMPT` | 1759 | Processes integration declarations |
| `CONTRACT_GENERATOR_PROMPT` | 1788 | Generates CONTRACTS.json |

### Injection Points for Generated Content

1. **Tech Research** (`agents.py` — `build_milestone_execution_prompt()` and `build_orchestrator_prompt()`):
   - `tech_research_content` parameter injected into prompts
   - Wrapped in delimiters: `TECH RESEARCH RESULTS`

2. **Design Reference** (`design_reference.py:636` — `format_ui_requirements_block()`):
   - Wrapped in: `PRE-ANALYZED DESIGN REFERENCE (from UI_REQUIREMENTS.md)`
   - Injected as "ANALYZED FACT" — system told NOT to re-scrape

3. **User Constraints** (`agents.py:1976`):
   - Prepended to ALL agent prompts via `format_constraints_block()`

4. **Code Quality Standards** (`agents.py:1984`):
   - Appended to relevant agent prompts via `get_standards_for_agent()`
   - Mapping in `code_quality_standards.py:648`:
     - code-writer: FRONTEND + BACKEND + DATABASE + API_CONTRACT + SDL + XREF
     - code-reviewer: CODE_REVIEW + DATABASE + API_CONTRACT + SDL
     - test-runner: TESTING + E2E_TESTING
     - debugger: DEBUGGING
     - architect: ARCHITECTURE + DATABASE + XREF

5. **Tracking Documents** (`agents.py` — 6 injection points):
   - ARCHITECT: milestone handoff awareness
   - CODE_WRITER: fix cycle awareness + milestone handoff awareness
   - Milestone execution: handoff generation instructions
   - Integration verification: coverage matrix update

6. **E2E Testing** (`e2e_testing.py` — 3 prompt constants):
   - `BACKEND_E2E_PROMPT` (line 556)
   - `FRONTEND_E2E_PROMPT` (line 732)
   - `E2E_FIX_PROMPT` (line 884)

### Orchestrator System Prompt Structure
**Source**: `agents.py:28` — `ORCHESTRATOR_SYSTEM_PROMPT` (~650 lines)

Key sections:
1. **REQUIREMENTS DOCUMENT PROTOCOL** — defines exact REQUIREMENTS.md structure
2. **FLEET DEPLOYMENT** — coding fleet, review fleet, debug fleet, security fleet
3. **CONVERGENCE LOOP** — 5 gates, cycle tracking, review authority
   - Gate 1: All `[x]` items in Requirements Checklist
   - Gate 2: Review cycles > 0 for each item
   - Gate 3: No CRITICAL/HIGH issues in Review Log
   - Gate 4: Build passes (if applicable)
   - Gate 5: No test failures
3b. **TASK ASSIGNMENT PHASE** — TASKS.md format
4. **PRD MODE** — two-phase orchestration (decomposition + milestone execution)
5-8. Additional operational sections

---

## 10. Post-Orchestration Scan Pipeline

**Source**: `cli.py` (post-orchestration section, after milestone/standard execution)

### Execution Order

```
1. Mock Data Scan (MOCK-001..008)
   → _run_mock_data_fix() if violations found
2. UI Compliance Scan (UI-001..004)
   → _run_ui_compliance_fix() if violations found
3. Integrity Scans:
   a. Deployment Scan (DEPLOY-001..004)
   b. Asset Scan (ASSET-001..003)
   c. PRD Reconciliation (PRD-001)
   → _run_integrity_fix() for deployment + asset violations
   → _run_prd_reconciliation() for PRD violations
4. Database Scans:
   a. Dual ORM Scan (DB-001..003)
   b. Default Value Scan (DB-004..005)
   c. Relationship Scan (DB-006..008)
   → _run_integrity_fix() with database-specific branches
5. API Contract Scan (API-001..003)
   → _run_api_contract_fix() if violations found
6. E2E Testing Phase (if enabled):
   a. Backend E2E Tests
   b. Frontend E2E Tests
   → _run_e2e_fix() for failures
7. Browser Testing Phase (if enabled):
   a. App startup
   b. Workflow execution
   c. Workflow fix
   d. Regression sweep
```

### Gating Rules
- Each scan independently gated by config bool
- Each scan in own `try/except` (crash isolation)
- Mock/UI scans use OR gate: run if either milestone or post_orchestration config enables
- PRD reconciliation quality gate (thorough depth): file must be >500 bytes AND contain `REQ-xxx`
- E2E/Browser testing gated on depth + PRD mode

---

## 11. Quality Scan Patterns (All Codes)

**Source**: `quality_checks.py`

### Mock Data Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| MOCK-001 | `_RE_RXJS_OF_MOCK`, `_RE_MOCK_RETURN_OF`, `_RE_RXJS_DELAY_PIPE` | error | RxJS of() with hardcoded data / delay pipe |
| MOCK-002 | `_RE_PROMISE_RESOLVE_MOCK` | error | Promise.resolve() with hardcoded data |
| MOCK-003 | `_RE_MOCK_VARIABLE` | error | mock/fake/dummy variable names |
| MOCK-004 | `_RE_TIMEOUT_MOCK` | warning | setTimeout simulating async API |
| MOCK-005 | `_RE_DELAY_SIMULATE` | warning | delay() simulating network latency |
| MOCK-006 | `_RE_BEHAVIOR_SUBJECT_MOCK` | error | BehaviorSubject with hardcoded data |
| MOCK-007 | `_RE_OBSERVABLE_MOCK` | error | new Observable returning mock data |
| MOCK-008 | `_RE_HARDCODED_UI_COUNT` | warning | Hardcoded count/badge values in components |

**Service path filter**: `_RE_SERVICE_PATH` — only scans service/client/api/http/data-access/providers/repositories paths.
**Test file exclusion**: `_RE_TEST_FILE` — skips test files.

### UI Compliance Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| UI-001 | `_RE_HARDCODED_HEX_CSS`, `_RE_HARDCODED_HEX_STYLE` | warning | Hardcoded hex color in style |
| UI-001b | `_RE_TAILWIND_ARBITRARY_HEX` | warning | Hardcoded hex in Tailwind arbitrary value |
| UI-002 | `_RE_DEFAULT_TAILWIND_EXTENDED` | warning | Default Tailwind color (indigo/violet/purple) |
| UI-003 | `_RE_GENERIC_FONT_CONFIG` | warning | Generic font in config (Inter/Roboto/Arial) |
| UI-004 | `_RE_ARBITRARY_SPACING` | info | Spacing value not on 4px grid |

**Config file exemption**: `_RE_CONFIG_FILE` files are exempt from UI-001 color checks (they define tokens).

### E2E Quality Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| E2E-001 | `_RE_E2E_SLEEP` | warning | Hardcoded sleep/timeout |
| E2E-002 | `_RE_E2E_HARDCODED_PORT` | warning | Hardcoded port |
| E2E-003 | `_RE_E2E_MOCK_DATA` | error | Mock data in E2E test |
| E2E-004 | `_RE_E2E_EMPTY_TEST` | error | Empty test body |
| E2E-005 | Aggregate check | warning | No auth E2E test when app has auth |
| E2E-006 | `_RE_E2E_PLACEHOLDER` | error | Placeholder text in UI component |
| E2E-007 | `_RE_E2E_ROLE_FAILURE` | error | Role access failure in E2E results |

### Database Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| DB-001 | Enum type mismatch (ORM vs raw SQL) | error | Enum compared differently |
| DB-002 | Boolean type mismatch (ORM vs raw SQL) | error | Bool compared as 0/1 |
| DB-003 | DateTime format mismatch | error | Hardcoded date format in raw SQL |
| DB-004 | Missing default value | warning | Bool/enum without explicit default |
| DB-005 | Nullable without null check | error | Unsafe nullable access |
| DB-006 | FK without navigation property | warning | Missing navigation |
| DB-007 | Navigation without inverse | info | Missing inverse navigation |
| DB-008 | FK with no relationship config | error | No explicit relationship |

### Deployment Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| DEPLOY-001 | Port mismatch | warning | App listens on port not in docker-compose |
| DEPLOY-002 | Undefined env var | warning | Env var used but not defined |
| DEPLOY-003 | CORS origin check | warning | CORS origin verification needed |
| DEPLOY-004 | Service name mismatch | warning | Connection string service not in compose |

### Asset Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| ASSET-001 | Broken src/href | warning | Asset file not found on disk |
| ASSET-002 | Broken CSS url() | warning | CSS url() asset not found |
| ASSET-003 | Broken require/import | warning | Asset import not found |

### API Contract Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| API-001 | Backend DTO missing field | error | Field from SVC-xxx not in backend class |
| API-002 | Frontend model field mismatch | error | Frontend uses wrong field name |
| API-003 | Type mismatch | warning | Unusual type compatibility |

### Other Patterns
| Code | Pattern | Severity | Description |
|------|---------|----------|-------------|
| SDL-001 | CQRS missing persistence | error | Command handler without SaveChangesAsync |
| ENUM-004 | Enum serialization format | error | Missing JsonStringEnumConverter |
| XREF-001 | Missing backend endpoint | error | Frontend calls non-existent endpoint |
| XREF-002 | HTTP method mismatch | error | Wrong HTTP method |
| PRD-001 | PRD reconciliation mismatch | warning | PRD vs implementation gap |
| PROJ-001 | Missing .gitignore | warning | No .gitignore or missing critical entries |
| FRONT-007 | TypeScript `any` | info | TypeScript any type abuse |
| FRONT-010 | console.log | info | Console.log in production code |
| FRONT-016 | Duplicate functions | warning | Same function in 2+ files |
| BACK-001 | SQL concatenation | error | SQL injection risk |
| BACK-002 | N+1 queries | warning | Sequential per-item queries |
| BACK-016 | Non-transactional writes | warning | Delete+create without transaction |
| BACK-017 | Validation discarded | warning | Schema.parse result not assigned |
| BACK-018 | Unvalidated params | warning | Route params without NaN check |
| SLOP-001 | Default Tailwind colors | info | indigo/blue-500/600 defaults |
| SLOP-003 | Generic fonts | info | Inter/Roboto/Arial |

### Global Limits
- `_MAX_VIOLATIONS = 100` — cap per scan function
- `_MAX_FILE_SIZE = 500_000` — skip files larger than 500KB

---

## 12. Design Reference System

**Source**: `design_reference.py`

### UI_REQUIREMENTS.md Required Sections
**Source**: `design_reference.py:111`
```python
_REQUIRED_SECTIONS = [
    "Color System",
    "Typography",
    "Spacing",
    "Component Patterns",
]
```

### Content Quality Validation
**Source**: `design_reference.py:297` — `validate_ui_requirements_content()`
- Color System: minimum 3 hex color codes
- Typography: minimum 1 font family declaration
- Spacing: minimum 3 spacing values (px/rem)
- Component Patterns: minimum 2 component type mentions
- >5 "NOT FOUND" markers = poor quality

### Design Direction Inference
**Source**: `design_reference.py:436` — `_DIRECTION_TABLE`

| Direction | Keywords | Primary | Heading Font |
|-----------|----------|---------|-------------|
| brutalist | developer, cli, terminal, tool, hacker | #000000 | Space Grotesk |
| luxury | premium, fintech, fashion, boutique | #1A1A2E | Cormorant Garamond |
| industrial | enterprise, erp, logistics, warehouse | #1E293B | Space Grotesk |
| minimal_modern | saas, dashboard, startup, app, crm | #0F172A | Plus Jakarta Sans |
| editorial | blog, news, content, magazine | #111827 | Playfair Display |

### Fallback Generation
**Source**: `design_reference.py:510` — `generate_fallback_ui_requirements()`
- Generates heuristic UI_REQUIREMENTS.md when extraction fails
- Includes `FALLBACK-GENERATED` warning header
- Uses direction inference from task keywords

---

## 13. Tech Research Phase

**Source**: `tech_research.py`

### Tech Stack Detection
**Source**: `tech_research.py:426` — `detect_tech_stack()`

Detects from:
- `package.json` (npm dependencies)
- `requirements.txt` (Python packages)
- `pyproject.toml` (Python project)
- `go.mod` (Go modules)
- `.csproj` (NuGet packages)
- `Cargo.toml` (Rust crates)
- Free-form text (PRD content)

### TechStackEntry
**Source**: `tech_research.py:22`
```python
@dataclass
class TechStackEntry:
    name: str        # e.g., "React"
    version: str     # e.g., "18.2.0" or "unknown"
    category: str    # "frontend" | "backend" | "database" | "orm" | ...
    source: str      # "package.json" | "requirements.txt" | "text"
    context7_id: str | None  # Context7 library ID if found
```

### Research Queries
**Source**: `tech_research.py:524` — `build_research_queries()`
- Category-specific Context7 query templates
- E.g., for "frontend": routing, state management, component patterns
- For "orm": migrations, relationships, querying patterns

### Output
- Written to `TECH_RESEARCH.md` in `.agent-team/`
- Format: `## TechName (vVersion)` sections with research findings
- Injected into orchestrator and milestone prompts via `tech_research_content` parameter

### Config
**Source**: `config.py:407` — `TechResearchConfig`
```python
@dataclass
class TechResearchConfig:
    enabled: bool = True
    max_techs: int = 6
    max_queries_per_tech: int = 3
    retry_on_incomplete: bool = True
    injection_max_chars: int = 15000
```

### Depth Gating
- quick: disabled
- standard: enabled, 2 queries per tech
- thorough: enabled, 3 queries per tech
- exhaustive: enabled, 6 queries per tech

---

## 14. E2E Testing Phase

**Source**: `e2e_testing.py`

### App Type Detection
**Source**: `e2e_testing.py:60` — `detect_app_type()`

Returns `AppTypeInfo` with:
- `has_backend`, `has_frontend`
- `backend_framework`, `frontend_framework`
- `backend_port`, `frontend_port`
- Detection via package.json, requirements.txt, angular.json, subdirectory scanning

### E2E Results Parsing
**Source**: `e2e_testing.py:450` — `parse_e2e_results()`
- Parses `E2E_RESULTS.md` with `Total/Passed/Failed` format
- Returns `E2ETestReport` dataclass

### Key Design
- No budget gates (runs until pass or max_fix_retries)
- 70% backend pass rate gate for frontend tests
- Granular phase tracking: e2e_backend, e2e_frontend, e2e_testing
- Fix loop guard: `not in ("passed", "skipped", "unknown")`

---

## 15. Browser Testing Phase

**Source**: `browser_testing.py`

### Components
- `WorkflowDefinition` dataclass: workflow name, steps, expected results
- `AppStartupInfo` dataclass: command, port, ready URL
- 4 prompt constants: startup, execution, fix, regression sweep

### CLI Pipeline
- `_run_browser_startup_agent()`: Starts the app
- `_run_browser_workflow_executor()`: Executes workflows
- `_run_browser_workflow_fix()`: Fixes failing workflows
- `_run_browser_regression_sweep()`: Verifies all workflows pass

### Depth Gating
- quick/standard: disabled
- thorough + PRD: enabled (retries=3)
- exhaustive + PRD: enabled (retries=5)

---

## 16. Contract Verification System

**Source**: `contracts.py`

### CONTRACTS.json Format
```json
{
  "version": "1.0",
  "modules": {
    "src/services/auth.py": {
      "exports": [
        {"name": "AuthService", "kind": "class", "signature": null}
      ],
      "created_by_task": "TASK-005"
    }
  },
  "wirings": [
    {
      "source_module": "src/routes/auth.py",
      "target_module": "src/services/auth.py",
      "imports": ["AuthService"],
      "created_by_task": "TASK-005"
    }
  ],
  "middlewares": [
    {
      "entry_file": "src/server.ts",
      "middleware_order": ["cors", "auth", "errorHandler"],
      "created_by_task": "TASK-001"
    }
  ]
}
```

### Verification
- `verify_module_contract()`: Checks symbols exist in source files (Python AST / TS regex)
- `verify_wiring_contract()`: Checks imports exist AND are used (not just imported)
- `verify_middleware_contract()`: Checks middleware order matches declaration
- `verify_all_contracts()`: Runs all verifications, returns `VerificationResult`

---

## 17. Verification Pipeline

**Source**: `verification.py`

### 7-Phase Pipeline
**Source**: `verification.py:86` — `verify_task_completion()`

```
Phase 0:   Requirements compliance (deterministic)
Phase 0b:  Test file existence gate (deterministic)
Phase 1:   Contract check (BLOCKING, deterministic)
Phase 1.5: Build check (BLOCKING)
Phase 2:   Lint/format (BLOCKING for errors)
Phase 3:   Type check (BLOCKING)
Phase 4:   Test subset (BLOCKING)
Phase 4.5: Test quality (ADVISORY)
Phase 5:   Security audit (ADVISORY)
Phase 6:   Spot checks (ADVISORY)
```

### Health Model
- **green**: all completed tasks pass
- **yellow**: some warnings but no blocking failures
- **red**: any blocking failure (contracts pass + tests fail = RED)

### Command Detection
- Build: `package.json scripts.build` → `npm run build`
- Lint: `package.json scripts.lint` → `npm run lint`, or `ruff check .`, or `npx eslint .`
- Type check: `tsconfig.json` → `npx tsc --noEmit`, or `mypy .`
- Tests: `package.json scripts.test` → `npm test`, or `pytest`

---

## 18. Convergence Loop Mechanics

**Source**: `agents.py:28` (ORCHESTRATOR_SYSTEM_PROMPT, Section 3)

### 5 Convergence Gates
1. All `[x]` items in Requirements Checklist (ratio >= `min_convergence_ratio`)
2. Review cycles > 0 for each item
3. No CRITICAL/HIGH issues in Review Log
4. Build passes (if applicable)
5. No test failures

### Convergence Ratio
**Source**: `config.py:48` — `ConvergenceConfig`
```python
min_convergence_ratio: float = 0.9  # 90% of items must be [x]
```

### Recovery
**Source**: `cli.py` — recovery pass logic
- If ratio < `recovery_threshold` (0.7), trigger recovery
- Recovery: re-deploy coding + review fleets
- Max retries: `review_recovery_retries` (default 3)

### Health Check
**Source**: `milestone_manager.py:440-441`
```python
_CHECKED_RE = re.compile(r'^\s*-\s*\[x\]', re.MULTILINE | re.IGNORECASE)
_UNCHECKED_RE = re.compile(r'^\s*-\s*\[ \]', re.MULTILINE)
```

Health = checked / (checked + unchecked). Result: "passed", "partial", "failed", or "unknown".

---

## 19. Depth Gating Rules

**Source**: `config.py:505` — `apply_depth_quality_gating()`

| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| Spot checks | off | on | on | on |
| Craft review | off | on | on | on |
| Production defaults | off | on | on | on |
| Mock data scan | off | on | on | on |
| UI compliance scan | off | on | on | on |
| PRD reconciliation | off | off | on | on |
| E2E testing | off | off | on (retries=2) | on (retries=3) |
| Browser testing | off | off | on+PRD (retries=3) | on+PRD (retries=5) |
| Tech research | off | on (2q) | on (3q) | on (6q) |
| Deployment scan | on | on | on | on |
| Asset scan | on | on | on | on |
| Database scans | on | on | on | on |
| API contract scan | off | on | on | on |
| Scan scope | changed | full | full | full |

---

## 20. Pitfalls & Gotchas

### Critical Parsing Rules

1. **MASTER_PLAN.md milestone headers MUST be h2-h4** (`##`, `###`, `####`).
   `#` (h1) headers will NOT be parsed as milestones.
   Source: `milestone_manager.py:101`

2. **Milestone IDs must be `milestone-N` format** (lowercase, hyphenated).
   Source: `milestone_manager.py:32`

3. **Dependencies field**: comma-separated milestone IDs or literal "none".
   Source: `milestone_manager.py:114` — `parse_master_plan()`

4. **Requirements checklist format is strict**: `- [ ] PREFIX-NNN: Description (review_cycles: N)`.
   The `[x]` must be lowercase or uppercase. The space in `[ ]` is required.
   Source: `milestone_manager.py:440-441`

5. **`_dict_to_config`/`load_config` return a tuple**: `(AgentTeamConfig, set[str])`.
   ALL callers must unpack the tuple. Source: `config.py:851`

6. **SVC-xxx field schemas**: must use `{ field: type, field: type }` with braces.
   Class-name-only rows (no braces) produce zero violations.
   Source: `quality_checks.py` — `_parse_field_schema()`

7. **Stale .agent-team/ directory**: MUST delete `.agent-team/` before re-running with a new PRD.
   Stale `MASTER_PLAN.md` causes wrong milestones. Source: empirical finding.

8. **Windows encoding**: `write_text(encoding="utf-8")` needed for files with Unicode characters.

9. **Violation dataclass fields**: `.check`, `.file_path`, `.line`, `.severity`, `.message`.
   NOT `.code`, NOT `.file`. Source: `quality_checks.py:94`

10. **PRD chunking threshold**: 50KB (not 50000 chars — measured in bytes after UTF-8 encoding).
    Source: `prd_chunking.py:49`

11. **Config file search order**: explicit path > `./config.yaml` > `~/.agent-team/config.yaml` > defaults.
    Source: `config.py` — `load_config()`

12. **Milestone convergence report**: Milestone mode uses `aggregate_milestone_convergence()`,
    standard mode uses `_check_convergence_health()`. Different code paths.
    Source: `cli.py` post-orchestration branches

13. **Contract recovery guard**: `has_requirements = req_path.is_file() or _has_milestone_requirements(cwd, config)`.
    Source: `cli.py`

14. **Review authority**: Only `code-reviewer` agents may mark items `[x]`. Code writers, debuggers, and
    other agents are explicitly forbidden. Source: `agents.py` (multiple prompts)

15. **E2E fix loop guard**: Uses `not in ("passed", "skipped", "unknown")` — prevents burning retries
    on non-failing health values. Source: `cli.py` E2E section

16. **Browser testing requires PRD mode**: `thorough` depth alone is NOT enough — must also have PRD.
    Source: `config.py:505` — depth gating logic

17. **Max iterations guard**: `max_iterations = len(milestones) + 3` in milestone loop.
    Prevents infinite loops. Source: `cli.py` milestone iteration

18. **Function-call URLs cannot be statically resolved**: `${this.func(...)}/path` patterns
    are a known limitation of the XREF scan. Source: v12 XREF fixes

---

## Appendix A: File Index

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| cli.py | `src/agent_team/cli.py` | ~4600+ | Main entry point, orchestration, scans |
| agents.py | `src/agent_team/agents.py` | ~2500+ | All agent prompts, prompt builders |
| config.py | `src/agent_team/config.py` | 1311 | All config dataclasses |
| milestone_manager.py | `src/agent_team/milestone_manager.py` | 935 | MASTER_PLAN.md parsing, health |
| quality_checks.py | `src/agent_team/quality_checks.py` | ~2600+ | All scan functions, patterns |
| code_quality_standards.py | `src/agent_team/code_quality_standards.py` | 665 | Non-configurable standards |
| design_reference.py | `src/agent_team/design_reference.py` | 667 | UI_REQUIREMENTS.md generation |
| tech_research.py | `src/agent_team/tech_research.py` | 747 | Tech stack detection, Context7 |
| e2e_testing.py | `src/agent_team/e2e_testing.py` | 974 | E2E testing utilities |
| browser_testing.py | `src/agent_team/browser_testing.py` | ~1219 | Browser testing with Playwright |
| prd_chunking.py | `src/agent_team/prd_chunking.py` | 226 | Large PRD chunking |
| verification.py | `src/agent_team/verification.py` | 1142 | Progressive verification pipeline |
| contracts.py | `src/agent_team/contracts.py` | 651 | Contract registry, JSON persistence |
| state.py | `src/agent_team/state.py` | ~200+ | State dataclasses |
| mcp_servers.py | `src/agent_team/mcp_servers.py` | ~200+ | MCP server configuration |
| tracking_documents.py | `src/agent_team/tracking_documents.py` | ~988 | Tracking document generation |

---

## Appendix B: Directory Structure Convention

```
project-root/
  config.yaml                    # Optional project config
  .agent-team/                   # Agent team working directory
    REQUIREMENTS.md              # Requirements document
    MASTER_PLAN.md               # Milestone plan (PRD mode)
    TASKS.md                     # Task breakdown
    CONTRACTS.json               # Module/wiring contracts
    VERIFICATION.md              # Verification summary
    SECURITY_AUDIT.md            # Security findings
    STATE.json                   # RunState persistence
    TECH_RESEARCH.md             # Tech research results
    UI_REQUIREMENTS.md           # Design reference document
    E2E_RESULTS.md               # E2E test results
    E2E_COVERAGE_MATRIX.md       # Coverage tracking
    FIX_CYCLE_LOG.md             # Fix cycle history
    PRD_RECONCILIATION.md        # PRD vs implementation comparison
    prd-chunks/                  # Large PRD chunks
      features.md
      api.md
      ...
    milestones/                  # Per-milestone directories
      milestone-1/
        REQUIREMENTS.md
        TASKS.md
        CONTRACTS.json
        VERIFICATION.md
        MILESTONE_HANDOFF.md
      milestone-2/
        ...
```

---

*Research completed by codebase-researcher agent. All findings verified against source code at commit `bee4a32` (v14.0).*
