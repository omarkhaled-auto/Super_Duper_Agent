# Build 3 Codebase Research — PRD Format & Execution Engine Analysis

> **Purpose**: Exhaustive reverse-engineered specification of the EXACT PRD format, config structure,
> scanning rules, and execution mechanics that agent-team v14.0 expects. Every finding cites `file:line`.
> Specifically tailored for Build 3 PRD creation — the Integrator + Quality Gate + Super Orchestrator.
>
> **Methodology**: Full read of CODEBASE_PRD_FORMAT_RESEARCH.md, BUILD1_PRD.md, BUILD2_PRD.md,
> milestone_manager.py, config.py, prd_chunking.py, quality_checks.py, agents.py (grep for key functions).

---

## Table of Contents

1. [Milestone Header Format & Regex](#1-milestone-header-format--regex)
2. [Requirement Prefix Types](#2-requirement-prefix-types)
3. [SVC-xxx Table Format](#3-svc-xxx-table-format)
4. [Config.yaml Complete Template](#4-configyaml-complete-template)
5. [Depth Gating Rules](#5-depth-gating-rules)
6. [Post-Orchestration Scan Pipeline Order](#6-post-orchestration-scan-pipeline-order)
7. [Large PRD Chunking Behavior](#7-large-prd-chunking-behavior)
8. [Format Differences: Build 1 vs Build 2](#8-format-differences-build-1-vs-build-2)
9. [Pitfalls & Gotchas](#9-pitfalls--gotchas)
10. [Build 3 PRD Special Considerations](#10-build-3-prd-special-considerations)
11. [Complete PRD Template Skeleton](#11-complete-prd-template-skeleton)
12. [MASTER_PLAN.md Exact Template](#12-master_planmd-exact-template)
13. [REQUIREMENTS.md Exact Template](#13-requirementsmd-exact-template)
14. [TASKS.md Exact Template](#14-tasksmd-exact-template)
15. [Verification Pipeline Phases](#15-verification-pipeline-phases)

---

## 1. Milestone Header Format & Regex

### Parsing Regex
**Source**: `milestone_manager.py:101-104`

```python
_RE_MILESTONE_HEADER = re.compile(
    r"^#{2,4}\s+(?:Milestone\s+)?(\d+)[.:]?\s*(.*)", re.MULTILINE,
)
_RE_FIELD = re.compile(r"^-\s*(\w[\w\s]*):\s*(.+)", re.MULTILINE)
_RE_PLAN_TITLE = re.compile(r"^#\s+(?:MASTER\s+PLAN:\s*)?(.+)", re.MULTILINE)
_RE_GENERATED = re.compile(r"Generated:\s*(.+)", re.IGNORECASE)
```

### CRITICAL Rules

1. **Header levels**: MUST be `##`, `###`, or `####` (h2-h4). `#` (h1) will NOT match.
2. **Accepted header patterns** (all parsed correctly):
   - `## Milestone 1: Title Here` (canonical)
   - `## 1. Title Here` (number-first)
   - `## Milestone 1. Title Here` (with period)
   - `### Milestone 1: Title Here` (h3 also works)
   - `#### Milestone 1: Title Here` (h4 also works)
3. **Milestone ID**: Extracted from `- ID: milestone-N` field, or defaults to `milestone-{num}` from header.
4. **Status values**: `PENDING`, `IN_PROGRESS`, `COMPLETE`, `FAILED` (case-insensitive on read, uppercase on write).
5. **Dependencies**: Comma-separated `milestone-N` IDs, or literal `none`/`n/a`/`-`. Parenthetical comments are stripped: `milestone-2 (parallel with M3)` parses as `["milestone-2"]`.

### MasterPlanMilestone Dataclass
**Source**: `milestone_manager.py:32-39`

```python
@dataclass
class MasterPlanMilestone:
    id: str           # "milestone-1", "milestone-2", etc.
    title: str        # From header text after number
    status: str = "PENDING"
    dependencies: list[str] = field(default_factory=list)
    description: str = ""
```

### Status Update Mechanics
**Source**: `milestone_manager.py:187-222`

- Uses `_RE_MILESTONE_HEADER` to find milestone boundaries (not raw `## ` prefixes)
- Finds `- ID: {milestone_id}` then updates nearest `- Status: ` line
- Search bounded by milestone header regex boundaries (avoids sub-section confusion)

### Ready Milestone Logic
**Source**: `milestone_manager.py:56-64`

A milestone is "ready" when:
- `status == "PENDING"` AND
- All IDs in `dependencies` have `status == "COMPLETE"`

---

## 2. Requirement Prefix Types

**Source**: `agents.py` (various prompts), `quality_checks.py`, `CODEBASE_PRD_FORMAT_RESEARCH.md:385-401`

| Prefix | Purpose | Created By | Example |
|--------|---------|------------|---------|
| `REQ-NNN` | Functional requirements | Planner | `REQ-001: Create user authentication endpoint` |
| `TECH-NNN` | Technical requirements | Planner | `TECH-001: All file paths must use pathlib.Path` |
| `INT-NNN` | Integration requirements | Planner | `INT-001: Create skeleton FastAPI apps` |
| `WIRE-NNN` | Wiring/connection requirements | Architect | `WIRE-001: Wire auth routes to Express server` |
| `SVC-NNN` | Service-to-API wiring | Architect | `SVC-001: auth.service.login() -> POST /api/auth/login` |
| `DESIGN-NNN` | Design/UI requirements | Planner/Architect | `DESIGN-001: Implement color system` |
| `TEST-NNN` | Testing requirements | Planner | `TEST-001: Unit tests for auth module` |
| `SEC-NNN` | Security requirements | Security Auditor | `SEC-001: Sanitize all user inputs` |
| `DR-NNN` | Design Reference checklist | Design Extraction | `DR-001: Primary color extracted` |
| `TASK-NNN` | Task breakdown items | Task Assigner | `TASK-001: Create auth model` |

### Checklist Format
**Source**: `milestone_manager.py:440-441`

```python
_CHECKED_RE = re.compile(r'^\s*-\s*\[x\]', re.MULTILINE | re.IGNORECASE)
_UNCHECKED_RE = re.compile(r'^\s*-\s*\[ \]', re.MULTILINE)
```

Format: `- [ ] PREFIX-NNN: Description (review_cycles: N)`
- `[x]` marks completion (case-insensitive)
- `[ ]` must have a space (not `[]` or `[-]`)
- `(review_cycles: N)` suffix is MANDATORY for tracking

### Review Authority
**Source**: `agents.py` (CODE_REVIEWER_PROMPT, ORCHESTRATOR_SYSTEM_PROMPT)

- **Only code-reviewer agents** may change `[ ]` to `[x]`
- Code writers, debuggers, and other agents are EXPLICITLY FORBIDDEN from marking items complete

---

## 3. SVC-xxx Table Format

### Table Structure
**Source**: `quality_checks.py` — `_parse_svc_table()`, `_parse_field_schema()`
**Reference**: `CODEBASE_PRD_FORMAT_RESEARCH.md:402-414`

```markdown
#### Service-to-API Wiring Map
| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|
| SVC-001 | auth.service | login() | POST | /api/auth/login | LoginRequest { email: string, password: string } | LoginResponse { token: string, user: UserDto } |
```

### Column Names (exact)
1. **ID** — `SVC-NNN`
2. **Frontend Service** — service file name or `N/A (internal)`
3. **Method** — method name with `()`
4. **HTTP** — `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
5. **Backend Endpoint** — full path e.g. `/api/auth/login`
6. **Request DTO** — class name + `{ field: type, field: type }` OR `None`
7. **Response DTO** — class name + `{ field: type, field: type }` OR `None (204)`

### Field Schema Notation
**Source**: `quality_checks.py` — `_parse_field_schema()`

```
ClassName { field1: type1, field2: type2 }
```

- Braces `{ }` are required for the API contract scan to extract fields
- Class-name-only rows (no braces) produce ZERO violations (backward compatible)
- Fields split on commas between field declarations
- Nested objects: `user: UserDto` (references another DTO)

### SVC-xxx Checklist Items
Each SVC entry in the table MUST also appear as a checklist item:

```markdown
### Service-to-API Wiring
- [ ] SVC-001: auth.service.login() -> POST /api/auth/login (review_cycles: 0)
```

### Build 1 vs Build 2 SVC Table Difference
- **Build 1** uses the standard 7-column format for backend-to-backend internal APIs (`Frontend Service` = `N/A (internal)`)
- **Build 2** uses a different table format for MCP tool wiring:

```markdown
| SVC-ID | Client Method | MCP Tool | Request DTO | Response DTO |
|--------|---------------|----------|-------------|--------------|
| SVC-001 | ContractEngineClient.get_contract(contract_id) | get_contract | { contract_id: string } | { id: string, ... } |
```

**Key Insight**: The API contract scan (`_parse_svc_table()`) parses the standard 7-column format. Build 2's 5-column MCP format is a custom extension. Build 3 should use whichever format matches its wiring type (standard for HTTP APIs, MCP format for MCP tool wiring).

---

## 4. Config.yaml Complete Template

**Source**: `config.py` (all dataclasses), `CODEBASE_PRD_FORMAT_RESEARCH.md:418-610`

### AgentTeamConfig Root Fields
**Source**: `config.py:422-460`

```python
@dataclass
class AgentTeamConfig:
    orchestrator: OrchestratorConfig
    depth: DepthConfig
    convergence: ConvergenceConfig
    interview: InterviewConfig
    design_reference: DesignReferenceConfig
    codebase_map: CodebaseMapConfig
    scheduler: SchedulerConfig
    verification: VerificationConfig
    quality: QualityConfig
    investigation: InvestigationConfig
    orchestrator_st: OrchestratorSTConfig
    milestone: MilestoneConfig
    prd_chunking: PRDChunkingConfig
    e2e_testing: E2ETestingConfig
    browser_testing: BrowserTestingConfig
    integrity_scans: IntegrityScanConfig
    tracking_documents: TrackingDocumentsConfig
    database_scans: DatabaseScanConfig
    post_orchestration_scans: PostOrchestrationScanConfig
    tech_research: TechResearchConfig
    agents: dict[str, AgentConfig]
    mcp_servers: dict[str, MCPServerConfig]
    display: DisplayConfig
```

### Config Load Return Type
**Source**: `config.py:851` (referenced in MEMORY.md)

```python
def _dict_to_config(data: dict) -> tuple[AgentTeamConfig, set[str]]:
    # Returns (config, user_overrides)
```

**CRITICAL**: `load_config()` returns `tuple[AgentTeamConfig, set[str]]`. ALL callers MUST unpack the tuple.

### Config Search Order
1. Explicit path argument
2. `./config.yaml` (project root)
3. `~/.agent-team/config.yaml` (user home)
4. Defaults (no config file needed)

### Recommended Build 3 Config
```yaml
# Build 3 — Super Agent Team
depth: "thorough"

milestone:
  enabled: true
  health_gate: true
  wiring_check: true
  review_recovery_retries: 2

convergence:
  min_convergence_ratio: 0.9
  recovery_threshold: 0.8

tech_research:
  enabled: true
  max_techs: 8
  max_queries_per_tech: 4

e2e_testing:
  enabled: true
  max_fix_retries: 3
  backend_api_tests: true
  frontend_playwright_tests: false  # No frontend in Build 3

post_orchestration_scans:
  mock_data_scan: true
  api_contract_scan: true
  silent_data_loss_scan: true
  endpoint_xref_scan: true
  ui_compliance_scan: false  # No frontend

integrity_scans:
  deployment_scan: true
  prd_reconciliation: true

database_scans:
  dual_orm_scan: true
  default_value_scan: true
  relationship_scan: true
```

---

## 5. Depth Gating Rules

**Source**: `config.py:505-591` — `apply_depth_quality_gating()`

| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| Tech research | OFF | ON (2q/tech) | ON (3q/tech) | ON (6q/tech) |
| Spot checks | OFF | ON | ON | ON |
| Craft review | OFF | ON | ON | ON |
| Production defaults | OFF | ON | ON | ON |
| Mock data scan | OFF | ON | ON | ON |
| UI compliance scan | OFF | ON | ON | ON |
| API contract scan | OFF | ON | ON | ON |
| Silent data loss scan | OFF | ON | ON | ON |
| Endpoint XREF scan | OFF | ON | ON | ON |
| PRD reconciliation | OFF | OFF | ON | ON |
| E2E testing | OFF | OFF | ON (retries=2) | ON (retries=3) |
| Browser testing | OFF | OFF | ON+PRD (retries=3) | ON+PRD (retries=5) |
| Deployment scan | OFF | ON | ON | ON |
| Asset scan | OFF | ON | ON | ON |
| Database scans | OFF | ON | ON | ON |
| Review recovery retries | 0 | default(1) | 2 | 3 |
| Max scan fix passes | 0 | 1 | 1 | 2 |
| Scan scope mode | changed | full | full | full |

### Key Mechanics
- `user_overrides` set tracks which keys the user explicitly set in YAML
- User-overridden keys are NEVER changed by depth gating
- Browser testing requires BOTH thorough+ depth AND PRD mode (`prd_mode or config.milestone.enabled`)

---

## 6. Post-Orchestration Scan Pipeline Order

**Source**: `cli.py` (post-orchestration section), `CODEBASE_PRD_FORMAT_RESEARCH.md:694-735`

### Execution Order (sequential)

```
1. Mock Data Scan (MOCK-001..008)
   -> _run_mock_data_fix() if violations found
   -> Up to max_scan_fix_passes iterations

2. UI Compliance Scan (UI-001..004)
   -> _run_ui_compliance_fix() if violations found

3. Integrity Scans:
   a. Deployment Scan (DEPLOY-001..004)
   b. Asset Scan (ASSET-001..003)
   c. PRD Reconciliation (PRD-001)
   -> _run_integrity_fix() for deployment + asset violations
   -> _run_prd_reconciliation() for PRD violations

4. Database Scans:
   a. Dual ORM Scan (DB-001..003)
   b. Default Value Scan (DB-004..005)
   c. Relationship Scan (DB-006..008)
   -> _run_integrity_fix() with database-specific branches

5. API Contract Scan (API-001..003)
   -> _run_api_contract_fix() if violations found

6. E2E Testing Phase (if enabled):
   a. Backend E2E Tests
   b. Frontend E2E Tests (requires 70% backend pass rate)
   -> _run_e2e_fix() for failures

7. Browser Testing Phase (if enabled + PRD mode):
   a. App startup
   b. Workflow execution
   c. Workflow fix
   d. Regression sweep
```

### Gating Rules
- Each scan independently gated by config bool
- Each scan in own `try/except` (crash isolation)
- Mock/UI scans use OR gate: run if either `milestone.*_scan` or `post_orchestration_scans.*_scan` enables
- PRD reconciliation quality gate (thorough depth): file must be >500 bytes AND contain `REQ-xxx`
- E2E/Browser testing gated on depth + PRD mode

### All Violation Codes (Complete)

| Code | Scan | Severity |
|------|------|----------|
| MOCK-001..008 | Mock Data | error/warning |
| UI-001..004 | UI Compliance | warning/info |
| DEPLOY-001..004 | Deployment | warning |
| ASSET-001..003 | Asset Integrity | warning |
| PRD-001 | PRD Reconciliation | warning |
| DB-001..008 | Database Integrity | error/warning/info |
| API-001..003 | API Contract | error/warning |
| SDL-001 | Silent Data Loss | error |
| ENUM-004 | Enum Serialization | error |
| XREF-001..002 | Endpoint Cross-Ref | error |
| E2E-001..007 | E2E Quality | error/warning |
| CONTRACT-001..004 | Contract Compliance (Build 2) | error |
| FRONT-007/010/016 | Frontend Quality | info/warning |
| BACK-001/002/016/017/018 | Backend Quality | error/warning |
| SLOP-001/003 | Slop Detection | info |
| PROJ-001 | Project Structure | warning |

---

## 7. Large PRD Chunking Behavior

**Source**: `prd_chunking.py`

### Detection
**Source**: `prd_chunking.py:49`

```python
def detect_large_prd(content: str, threshold: int = 50000) -> bool:
    return len(content.encode("utf-8")) > threshold
```

**CRITICAL**: 50KB measured in BYTES after UTF-8 encoding, not character count.

### Section Patterns
**Source**: `prd_chunking.py:19-29`

```python
_SECTION_PATTERNS = [
    ("features?|user\\s+stories?|requirements?", "features"),
    ("database|schema|data\\s+model|entities", "database"),
    ("api|endpoints?|rest|graphql|routes", "api"),
    ("frontend|ui|ux|components?|pages?|views?", "frontend"),
    ("auth|authentication|authorization|security|permissions?", "auth"),
    ("infrastructure|deployment|devops|docker|ci.?cd", "infrastructure"),
    ("testing|tests?|acceptance|quality", "testing"),
    ("dependencies|third.party|external|integrations?", "dependencies"),
    ("appendix|reference|glossary", "appendix"),
]
```

### Chunking Algorithm
1. Splits at `#` and `##` heading boundaries (h1 and h2)
2. Each chunk written to `.agent-team/prd-chunks/{section_name}.md`
3. Duplicate section names get suffixed: `features`, `features_2`, etc.
4. Sections < 100 bytes are skipped
5. Index built by `build_prd_index()` with summaries

### Build 3 PRD Size Consideration
Build 1 PRD is ~26,000+ tokens (very large). Build 2 PRD is similarly large.
Build 3 PRD will likely exceed 50KB. **Design the PRD with clean `## Milestone N:` boundaries** so chunking produces coherent sections.

---

## 8. Format Differences: Build 1 vs Build 2

### Milestone Header Format

**Build 1** uses inline milestone headers (NO explicit ID/Status/Dependencies fields):
```markdown
## Milestone 1: Core Data Models and Shared Infrastructure
```
- No `- ID:` field
- No `- Status:` field
- No `- Dependencies:` field
- No `- Description:` field
- The milestone parser defaults: `id=milestone-{num}`, `status=PENDING`, `deps=[]`

**Build 2** uses the full structured format:
```markdown
## Milestone 1: Agent Teams Abstraction Layer

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Create the execution backend abstraction...
```

### Which Format to Use for Build 3?
**USE BUILD 2 FORMAT** (full structured fields). The parser handles both, but:
- Explicit `- ID:` is safer than relying on auto-generation
- Explicit `- Dependencies:` enables dependency-aware scheduling
- Explicit `- Description:` gives the orchestrator better context

### Requirement Section Organization

**Build 1**: Requirements grouped under milestone headers directly.
```markdown
## Milestone 1: Title

### Functional Requirements
- [ ] REQ-001: ...

### Technical Requirements
- [ ] TECH-001: ...
```

**Build 2**: Same structure but with the milestone metadata fields first.
```markdown
## Milestone 1: Title

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: ...

### Functional Requirements
- [ ] REQ-001: ...
```

### SVC Table Variations

**Build 1**: Standard 7-column format for HTTP APIs.
**Build 2**: 5-column format for MCP tool wiring + standard format for HTTP.

### Requirement Numbering

**Build 1**: Global numbering across all milestones (REQ-001 through REQ-073).
**Build 2**: Global numbering across all milestones (REQ-001 through REQ-085).
**Build 3**: MUST use global numbering. Do NOT restart at REQ-001 per milestone.

### Status Registry Section

**Build 1** includes a `## Status Registry` table:
```markdown
## Status Registry
| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|
| BuildCycle | status | running, completed, failed, paused | TEXT with CHECK | string |
```
**Build 2** does NOT include a Status Registry section.

### Architecture Decision Section

**Build 1** includes a full `## Architecture Decision` section with:
- Technology Stack
- File Structure
- Integration Roadmap (Entry Points, Wiring Map, Anti-Patterns, Init Order)
- Review Log

**Build 2** does NOT include this section (it's an upgrade to existing code).

### Integration Requirements

**Build 2** heavily uses `INT-xxx` requirements for backward compatibility and pipeline preservation:
```markdown
- [ ] INT-011: 15-stage pipeline execution order in main() must be preserved
- [ ] INT-012: All 13 existing self-healing fix loops must continue to function
```

**Build 3** will need similar INT requirements since it integrates Build 1 and Build 2.

### Security Requirements

**Build 2** includes `SEC-xxx` requirements:
```markdown
- [ ] SEC-001: MCP client connections must not pass ANTHROPIC_API_KEY
- [ ] SEC-002: Hook scripts must not contain embedded secrets
- [ ] SEC-003: ServiceContractRegistry must strip securitySchemes
```

### Pipeline Preservation Checklist

**Build 2** has a dedicated "Pipeline Preservation Checklist" under its integration milestone. This pattern should be replicated for Build 3 with updated pipeline reference.

---

## 9. Pitfalls & Gotchas

### Critical Parsing Rules

1. **Milestone headers MUST be h2-h4** (`##`, `###`, `####`). `#` (h1) is the plan title only.
   Source: `milestone_manager.py:101`

2. **Milestone IDs MUST be `milestone-N` format** (lowercase, hyphenated).
   Source: `milestone_manager.py:32`

3. **Dependencies field**: comma-separated milestone IDs or literal `none`. Parenthetical comments are stripped.
   Source: `milestone_manager.py:166-179`

4. **Requirements checklist format is STRICT**: `- [ ] PREFIX-NNN: Description (review_cycles: N)`.
   The `(review_cycles: N)` suffix is MANDATORY. Space in `[ ]` is required.
   Source: `milestone_manager.py:440-441`

5. **`_dict_to_config`/`load_config` return a tuple**: ALL callers must unpack.
   Source: `config.py:851`

6. **SVC-xxx field schemas MUST use braces** `{ field: type }` for the API contract scan to work.
   Source: `quality_checks.py` — `_parse_field_schema()`

7. **Stale `.agent-team/` directory**: MUST delete `.agent-team/` before re-running with a new PRD.
   Source: empirical finding

8. **Windows encoding**: `write_text(encoding="utf-8")` needed for files with Unicode.

9. **Violation dataclass fields**: `.check`, `.file_path`, `.line`, `.severity`, `.message`.
   NOT `.code`, NOT `.file`. Source: `quality_checks.py:94-100`

10. **PRD chunking threshold**: 50KB in BYTES not characters.
    Source: `prd_chunking.py:49`

11. **Max iterations guard**: `len(milestones) + 3` in milestone loop.
    Source: `cli.py`

12. **Function-call URLs**: `${this.func(...)}/path` cannot be statically resolved.
    Source: v12 XREF fixes

13. **Review authority**: ONLY code-reviewer agents may mark items `[x]`.
    Source: `agents.py` (multiple prompts)

14. **E2E fix loop guard**: Uses `not in ("passed", "skipped", "unknown")`.
    Source: `cli.py`

15. **Browser testing requires PRD mode**: `thorough` depth alone is NOT enough.
    Source: `config.py:505`

16. **Requirement numbering**: Global across milestones. DO NOT restart per milestone.

17. **TECH-xxx requirements can embed implementation details**: Build 1 PRD REQ-007 contains complete SQL DDL in the requirement text. This is valid and preferred for deterministic specifications.

18. **Milestone description field**: Include in MASTER_PLAN.md format. Without it, the orchestrator has less context for each milestone.

---

## 10. Build 3 PRD Special Considerations

### What Makes Build 3 Different

Build 3 is unique because:
1. **It references outputs from Build 1 and Build 2** as inputs. Build 1 produces MCP servers (Architect, Contract Engine, Codebase Intelligence). Build 2 produces MCP clients and Agent Teams abstraction. Build 3 must consume both.

2. **It is an orchestrator of orchestrators**. Build 3's Super Orchestrator uses Build 1's Architect to decompose PRDs, uses Build 1's Contract Engine to manage contracts, uses Build 2's Agent Teams to dispatch work, and adds its own quality gate and state machine layers.

3. **It requires Docker Compose orchestration**. All Build 1 services must be running for Build 3 to function. The PRD must specify how to start, health-check, and teardown these dependencies.

4. **No frontend**. Build 3 is pure backend infrastructure + CLI. Set `ui_compliance_scan: false` and `frontend_playwright_tests: false` in config.

### PRD Content Strategy

The PRD should include:
- A clear preamble stating this is Build 3 of a 3-build system
- Cross-references to Build 1 and Build 2 outputs (MCP tools, config sections, state dataclasses)
- Integration requirements (INT-xxx) that verify Build 1+2 services are accessible
- Backward compatibility requirements ensuring Build 2's backward compat with v14.0 is preserved
- No `## Architecture Decision` or `## Status Registry` in the PRD body (those go in REQUIREMENTS.md created by the Planner/Architect agents)

### Milestone Dependency Graph for Build 3

Given Build 3's architecture (from the Super Team research), a natural milestone DAG would be:
```
M1: Shared models + config + state machine engine (no deps)
M2: Super Orchestrator core (depends M1)
M3: Quality Gate engine (depends M1)
M4: Integration layer — wire Build 1+2+3 together (depends M2, M3)
M5: CLI + Docker orchestration (depends M4)
M6: E2E verification + backward compat (depends M5)
```

### Technology Stack Section

Build 3's tech stack section should match Build 1's format:
```markdown
## Technology Stack

- **Language:** Python 3.12+
- **Async Runtime:** asyncio + MCP Python SDK
- **Framework:** FastAPI (for health/status endpoints)
- ...
```

This section appears BEFORE the milestones (like Build 1), not as part of the Architecture Decision section.

### Test Requirements Pattern

Both Build 1 and Build 2 include TEST-xxx requirements per milestone. Build 3 MUST follow this pattern:
- Each milestone has its own `### Test Requirements` section
- Test IDs are globally numbered: `TEST-001`, `TEST-002`, etc.
- Each test requirement specifies the test file, what to test, and minimum test case count

---

## 11. Complete PRD Template Skeleton

Based on analysis of Build 1 and Build 2 PRDs:

```markdown
# Super Agent Team — Build 3 PRD: Integrator + Quality Gate + Super Orchestrator

<One-paragraph summary describing what this build does, its relationship to Build 1 and Build 2.>

Each requirement includes `(review_cycles: N)` — this is tracked by the build system. Agents must preserve this suffix when modifying requirements.

## Technology Stack

- **Language:** ...
- **Framework:** ...
- **Database:** ...
(etc.)

## Project Structure

```
super-team/
  src/
    ...
```

## Milestone 1: <Title>

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: <What this milestone produces.>

### Functional Requirements

- [ ] REQ-001: <Description> (review_cycles: 0)

### Technical Requirements

- [ ] TECH-001: <Description> (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-001: <Description> (review_cycles: 0)

### Service-to-API Wiring Map

| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|
| SVC-001 | N/A (internal) | method() | POST | /api/path | RequestDto { field: type } | ResponseDto { field: type } |

- [ ] SVC-001: description (review_cycles: 0)

### Test Requirements

- [ ] TEST-001: <Description> (review_cycles: 0)

---

## Milestone 2: <Title>

- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: <What this milestone produces.>

(repeat sections...)

---

## Milestone N: End-to-End Verification + Backward Compatibility

- ID: milestone-N
- Status: PENDING
- Dependencies: milestone-{N-2}, milestone-{N-1}
- Description: Full regression, backward compat, integration tests.

### Integration Requirements

- [ ] INT-001: <Backward compat requirement> (review_cycles: 0)

### Security Requirements

- [ ] SEC-001: <Security requirement> (review_cycles: 0)

### Pipeline Preservation Checklist

- [ ] INT-0XX: Pipeline order preserved (review_cycles: 0)

### Test Requirements

- [ ] TEST-0XX: Regression test (review_cycles: 0)

---

## Status Registry

| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|

## Architecture Decision

### Technology Stack
(repeat from above with more detail)

### File Structure
(repeat from above)

### Integration Roadmap

#### Entry Points
| Entry Point | File | Purpose |
|---|---|---|

#### Wiring Map
| ID | Source | Target | Mechanism | Priority |
|---|---|---|---|---|

#### Wiring Anti-Patterns
- ...

#### Initialization Order
1. ...

## Review Log

| Cycle | Agent | Item | Verdict | Issues |
|---|---|---|---|---|
```

---

## 12. MASTER_PLAN.md Exact Template

This is what the decomposition agent produces from the PRD:

```markdown
# Master Plan: Super Agent Team Build 3
Generated: YYYY-MM-DD HH:MM:SS

## Milestone 1: Shared Models and State Machine Engine
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Create shared data models, state machine engine, and configuration extensions.

## Milestone 2: Super Orchestrator Core
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Implement the multi-phase orchestrator with Build 1/2 MCP integration.

## Milestone 3: Quality Gate Engine
- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-1
- Description: Implement configurable quality gates with promotion/demotion logic.

## Milestone 4: Integration Layer
- ID: milestone-4
- Status: PENDING
- Dependencies: milestone-2, milestone-3
- Description: Wire all components together, Docker orchestration, service discovery.

## Milestone 5: CLI and Operational Layer
- ID: milestone-5
- Status: PENDING
- Dependencies: milestone-4
- Description: Command-line interface, logging, monitoring, graceful shutdown.

## Milestone 6: E2E Verification and Backward Compatibility
- ID: milestone-6
- Status: PENDING
- Dependencies: milestone-4, milestone-5
- Description: Full integration tests, backward compatibility verification.
```

---

## 13. REQUIREMENTS.md Exact Template

This is what the Planner + Architect agents produce per milestone:

```markdown
# Requirements Document — Super Agent Team Build 3

## Context
<Brief description of the project, constraints, cross-references to Build 1/2>

## Research Findings
<Injected from TECH_RESEARCH.md>

## Architecture Decision
### Technology Stack
- ...

### File Structure
```
src/
  ...
```

### Integration Roadmap

#### Entry Points
| Entry Point | File | Purpose |
|---|---|---|

#### Wiring Map
| ID | Source | Target | Mechanism | Priority |
|---|---|---|---|---|

#### Service-to-API Wiring Map
| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|

#### Wiring Anti-Patterns
- ...

#### Initialization Order
1. ...

### Status Registry
| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|

## Requirements Checklist

### Functional Requirements
- [ ] REQ-001: ... (review_cycles: 0)

### Technical Requirements
- [ ] TECH-001: ... (review_cycles: 0)

### Integration Requirements
- [ ] INT-001: ... (review_cycles: 0)

### Wiring Requirements
- [ ] WIRE-001: ... (review_cycles: 0)

### Service-to-API Wiring
- [ ] SVC-001: ... (review_cycles: 0)

### Test Requirements
- [ ] TEST-001: ... (review_cycles: 0)

## Review Log
| Cycle | Agent | Item | Verdict | Issues |
|---|---|---|---|---|
```

---

## 14. TASKS.md Exact Template

**Source**: `agents.py:1712-1743` (TASK_ASSIGNER_PROMPT)

```markdown
# Task Breakdown: Super Agent Team Build 3
Generated: YYYY-MM-DD HH:MM:SS
Total Tasks: N
Completed: 0/N

## Legend
- Status: PENDING | IN_PROGRESS | COMPLETE
- Dependencies: list of TASK-xxx IDs that must be COMPLETE before this task can start

## Tasks

### TASK-001: Create shared models
- Parent: REQ-001
- Status: PENDING
- Dependencies: none
- Files: src/shared/models.py
- Description: Create Pydantic v2 models for state machine, quality gate, orchestrator state.

### TASK-002: Create state machine engine
- Parent: REQ-002
- Status: PENDING
- Dependencies: TASK-001
- Files: src/engine/state_machine.py
- Description: Implement finite state machine with transition validation.
```

### Key Rules
- Each task targets **1-3 files MAXIMUM**
- Tasks numbered sequentially: TASK-001, TASK-002, ...
- Dependencies MUST form a DAG (no circular)
- Every WIRE-xxx requirement MUST generate a dedicated wiring task
- Wiring tasks targeting the same file need sequential dependencies

---

## 15. Verification Pipeline Phases

**Source**: `verification.py:86`, `CODEBASE_PRD_FORMAT_RESEARCH.md:1034-1060`

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
- **red**: any blocking failure

### Convergence
**Source**: `config.py:48`

```python
min_convergence_ratio: float = 0.9  # 90% of items must be [x]
recovery_threshold: float = 0.8    # Below this triggers recovery pass
```

Health = checked / (checked + unchecked):
- `>= min_convergence_ratio` (0.9) -> "healthy"
- `>= degraded_threshold` (0.5) AND review_cycles > 0 -> "degraded"
- Below all thresholds -> "failed"

---

## Appendix A: Build 1 Outputs Consumed by Build 3

| Build 1 Service | MCP Tool | Build 3 Usage |
|-----------------|----------|---------------|
| Architect | `get_service_map()` | Query existing service decomposition |
| Architect | `get_contracts_for_service(service_name)` | Find contracts per service |
| Architect | `get_domain_model()` | Query domain model |
| Contract Engine | `get_contract(contract_id)` | Load contract details |
| Contract Engine | `validate_endpoint(...)` | Validate API compliance |
| Contract Engine | `generate_tests(...)` | Generate conformance tests |
| Contract Engine | `check_breaking_changes(...)` | Detect breaking changes |
| Contract Engine | `mark_implemented(...)` | Track implementation status |
| Contract Engine | `get_unimplemented_contracts(...)` | Find gaps |
| Codebase Intelligence | `find_definition(symbol, language)` | Locate symbols |
| Codebase Intelligence | `find_callers(symbol)` | Impact analysis |
| Codebase Intelligence | `find_dependencies(file_path)` | Import graph |
| Codebase Intelligence | `search_semantic(query)` | Semantic code search |
| Codebase Intelligence | `get_service_interface(service_name)` | Extract endpoints |
| Codebase Intelligence | `check_dead_code(service_name)` | Dead code detection |
| Codebase Intelligence | `register_artifact(file_path, service_name)` | Incremental indexing |

## Appendix B: Build 2 Outputs Consumed by Build 3

| Build 2 Module | Class/Function | Build 3 Usage |
|----------------|----------------|---------------|
| `agent_teams_backend.py` | `ExecutionBackend` protocol | Dispatch execution waves |
| `agent_teams_backend.py` | `AgentTeamsBackend` | Agent Teams mode |
| `agent_teams_backend.py` | `CLIBackend` | CLI fallback mode |
| `agent_teams_backend.py` | `create_execution_backend()` | Factory function |
| `contract_client.py` | `ContractEngineClient` | Typed MCP client for contracts |
| `codebase_client.py` | `CodebaseIntelligenceClient` | Typed MCP client for codebase |
| `hooks_manager.py` | `generate_hooks_config()` | Quality gate hooks |
| `claude_md_generator.py` | `generate_claude_md()` | Teammate context |
| `contract_scanner.py` | `run_contract_compliance_scan()` | CONTRACT-001..004 |
| `mcp_client.py` | `create_contract_engine_session()` | MCP session mgmt |
| `mcp_client.py` | `create_codebase_intelligence_session()` | MCP session mgmt |
| `config.py` | `AgentTeamsConfig` | Agent Teams settings |
| `config.py` | `ContractEngineConfig` | Contract Engine settings |
| `config.py` | `CodebaseIntelligenceConfig` | Codebase Intel settings |
| `config.py` | `ContractScanConfig` | CONTRACT scan settings |
| `state.py` | `ContractReport` | Contract compliance state |
| `state.py` | `IntegrationReport` | Integration test state |

## Appendix C: PRD Phase Execution Order

**Source**: `cli.py:3742-4041`, `CODEBASE_PRD_FORMAT_RESEARCH.md:79-93`

```
1.  Interview Phase (optional)
2.  Constraints Loading
3.  Codebase Map (Phase 0.5)
4.  Design Reference Extraction (Phase 0.6)
5.  Tech Research (Phase 1.5)
6.  PRD Decomposition -> MASTER_PLAN.md
7.  Per-Milestone Execution -> REQUIREMENTS.md per milestone
8.  Post-Orchestration Scans
9.  E2E Testing Phase
10. Browser Testing Phase
```

---

*Research completed by codebase-researcher agent. All findings verified against source code at commit `bee4a32` (v14.0). Cross-referenced with CODEBASE_PRD_FORMAT_RESEARCH.md, BUILD1_PRD.md, and BUILD2_PRD.md.*
