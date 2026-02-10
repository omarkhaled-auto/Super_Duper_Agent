# Agent-Team Exhaustive Implementation — Per-Phase Tracking Documents (IMPLEMENTED)

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (5 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `superpowers:code-reviewer` | Phase 1 — Read entire codebase, document integration patterns, produce ARCHITECTURE_REPORT.md |
| `impl-core` | `general-purpose` | Phase 2A — New `tracking_documents.py` module + `config.py` additions + `state.py` additions |
| `impl-prompts` | `general-purpose` | Phase 2B — All prompt injections in `agents.py` + `e2e_testing.py` prompt constant modifications |
| `impl-wiring` | `general-purpose` | Phase 2C — All CLI wiring in `cli.py` + `milestone_manager.py` modifications |
| `test-engineer` | `general-purpose` | Phase 3+4 — Write ALL tests, run pytest, fix failures, iterate until green |

### Coordination Flow

```
Wave 1 (solo): architect reads entire codebase
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-core (new module + config)
                  + impl-prompts (prompt injections)
                  + impl-wiring (CLI + milestone_manager)
    |                   |                    |
    All read ARCHITECTURE_REPORT.md first
    |                   |                    |
    +---------+---------+--------------------+
              |
Wave 3 (solo): test-engineer writes ALL tests
              |
Wave 4 (solo): test-engineer runs full suite, fixes failures
              |
Wave 5: You (team lead) collect all results -> final report
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **architect runs first and alone.** Its ARCHITECTURE_REPORT.md is the blueprint for all implementation.
- **impl-core, impl-prompts, and impl-wiring run simultaneously.** They work on different files:
  - impl-core: `src/agent_team/tracking_documents.py` (NEW), `src/agent_team/config.py`, `src/agent_team/state.py`
  - impl-prompts: `src/agent_team/agents.py`, `src/agent_team/e2e_testing.py`
  - impl-wiring: `src/agent_team/cli.py`, `src/agent_team/milestone_manager.py`
- **test-engineer waits for ALL 3 impl agents** before starting.
- **After Wave 4 completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents
- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-core: Can create `tracking_documents.py`, edit `config.py` and `state.py`. Do NOT touch cli.py, agents.py, e2e_testing.py, or milestone_manager.py.
- impl-prompts: Can edit `agents.py` and `e2e_testing.py`. Do NOT touch cli.py, config.py, state.py, or tracking_documents.py.
- impl-wiring: Can edit `cli.py` and `milestone_manager.py`. Do NOT touch config.py, agents.py, e2e_testing.py, or tracking_documents.py.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# Per-Phase Tracking Documents — Guaranteed Agent Progress Visibility

## Background — Why This Exists

The agent-team system builds software through multi-agent orchestration: planners decompose tasks, code-writers implement, reviewers verify, and fix loops iterate until convergence. But agents have **no structured memory between phases**. Each sub-orchestrator starts fresh, reading REQUIREMENTS.md and source code but having no record of what was specifically attempted, completed, or failed in prior phases.

This creates three catastrophic failure modes that no existing check catches proactively.

### Failure 1: Superficial E2E Testing ("3 Happy Paths and Done")

The E2E testing phase deploys a sub-orchestrator that reads REQUIREMENTS.md and writes tests. But there is no structured mapping from requirements to tests. The agent commonly writes 3-5 tests covering the most obvious flows (login, create item, view list) and declares success. A project with 20 API endpoints and 15 frontend routes gets 5 tests — and the E2E phase reports "passed" because those 5 tests pass. The remaining 30+ workflows are never tested. There is no mechanism forcing completeness because there is no checklist saying "these 30 items need tests and only 5 have them."

### Failure 2: Blind Fix Loops ("Same Fix Three Times")

When E2E tests fail, the fix agent receives the failure output and source code. It diagnoses the issue and applies a fix. If the fix doesn't work, a NEW sub-orchestrator session starts with the SAME failure output — but zero knowledge of what was already tried. The agent often applies the exact same fix, or a minor variation of it, wasting 2-3 cycles ($0.40-$1.20 each) before accidentally stumbling onto the real solution. This affects ALL fix loops: E2E backend, E2E frontend, mock data, UI compliance, and integrity fixes. There is no "fix history" document that says "Cycle 1 tried X, it failed because Y."

### Failure 3: Zero Cross-Milestone Wiring ("75 Mock Methods")

In PRD+ milestone mode, the BAYAN Tender project built 5 milestones. Milestone 1 created the backend API. Milestone 3 created the frontend. But Milestone 3's sub-orchestrator had no structured knowledge of what Milestone 1 built — only a vague "predecessor summary" paragraph. The frontend agent scaffolded 75 service methods with `of(mockData).pipe(delay(500))` because it didn't know the exact API endpoints, request shapes, or response types. The wiring check caught this AFTER all milestones completed, requiring expensive repair passes. A handoff document listing every exposed endpoint with its exact contract would have let Milestone 3 wire directly to real APIs from the start.

## What We're Building

Three per-phase tracking documents that agents generate, progressively mark, and read before working. Each uses the same pattern: **starts with all items unchecked → agents mark as they complete work → next agent reads before starting → can't declare "done" with unchecked items.**

**Document 1: E2E_COVERAGE_MATRIX.md** (E2E Testing Phase)
Generated from REQUIREMENTS.md before test writing. Maps every requirement, endpoint, route, and cross-role workflow to a test. Agents mark `[x]` as tests are written and executed. Fix loops read the matrix to target specific failing rows. The agent cannot complete the E2E phase with unchecked rows.

**Document 2: FIX_CYCLE_LOG.md** (ALL Fix Loops)
Created by the first fix cycle. Each subsequent cycle appends: what failed, what was tried, what files changed, what the result was. The next fix agent MUST read the full log before attempting a fix. Prevents repeating failed strategies.

**Document 3: MILESTONE_HANDOFF.md** (PRD+ Milestone Mode)
Written by each completing milestone. Lists every exposed interface (endpoints, response shapes, env vars, database state). Next milestone reads it BEFORE coding and marks each consumed interface as wired. Prevents the "75 mock methods" failure.

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

Before implementing ANYTHING, the architect must read the codebase and produce `.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: Existing Document Generation Patterns

- Read `src/agent_team/e2e_testing.py` end to end (638 lines)
- Document BACKEND_E2E_PROMPT (lines 382-467), FRONTEND_E2E_PROMPT (lines 470-557), E2E_FIX_PROMPT (lines 559-638):
  - Exact format variables each prompt uses (`{requirements_dir}`, `{task_text}`, etc.)
  - How prompts instruct agents to read/write files (exact phrases used)
  - Where document generation instructions would naturally fit in each prompt
- Read `src/agent_team/agents.py` — find `build_milestone_execution_prompt()` (line 1922):
  - Document the 9-step MILESTONE WORKFLOW block (lines 2009-2040)
  - Document where predecessor context is injected
  - Document the integration verification block at the end (lines 2061-2080)
  - Identify EXACT insertion points for handoff instructions

### 1B: Fix Loop Architecture

- Read `src/agent_team/cli.py` — find ALL fix functions:
  - `_run_mock_data_fix()` (line 1298) — signature, prompt string, how it's called
  - `_run_ui_compliance_fix()` (line 1357) — signature, prompt string
  - `_run_e2e_fix()` (line 1502) — signature, prompt string, how failures are passed
  - `_run_integrity_fix()` (line 1632) — signature, prompt string, scan_type variants
  - `_run_review_only()` — signature, how it's called from milestone recovery
- Document the COMMON PATTERN across all fix functions:
  - Build prompt string → create ClaudeSDKClient → query → process response → return cost
  - How each function receives its violations/failures
  - How the prompt string is constructed (f-string pattern)
- Document how each fix function is CALLED from post-orchestration:
  - What triggers each call (violation list, health status, etc.)
  - What happens after the call returns (re-scan? recovery type? state save?)

### 1C: CLI Post-Orchestration Execution Flow

- Read `src/agent_team/cli.py` post-orchestration section (approximately lines 3470-3830)
- Document the EXACT order of all checks with line numbers:
  1. Mock data scan → mock fix
  2. UI compliance scan → UI fix
  3. Deployment scan → deployment fix
  4. Asset scan → asset fix
  5. PRD reconciliation
  6. E2E testing (backend → frontend)
  7. Recovery report
- For EACH check, document:
  - Config flag that gates it
  - Try/except wrapping pattern
  - Recovery type string added on violation
  - State persistence calls

### 1D: Milestone Execution Flow

- Read `src/agent_team/cli.py` function `_run_prd_milestones()` (line 692)
- Document the per-milestone execution flow:
  1. Build milestone context (line 957)
  2. Execute session (line 978)
  3. TASKS.md check (line 1023)
  4. Health check (line 1031)
  5. Review recovery loop (line 1038)
  6. Mock data scan (milestone-level)
  7. UI compliance scan (milestone-level)
  8. Wiring check
  9. Update MASTER_PLAN.md status
- Identify EXACT insertion point for handoff document generation: after review recovery completes (line 1095), before wiring check begins
- Document `milestone_manager.py` functions used: `check_milestone_health()`, `build_completion_summary()`, `save_completion_cache()`

### 1E: Config Integration Pattern

- Read `src/agent_team/config.py`:
  - Document `E2ETestingConfig` dataclass (line 307) — field names, types, defaults
  - Document `IntegrityScanConfig` dataclass (line 325) — field names, types, defaults
  - Document how these are added to `AgentTeamConfig` (line 355 area)
  - Document `_dict_to_config()` YAML loading pattern (lines 899-930)
  - Document validation pattern (how E2E validates max_fix_retries >= 1, test_port range)
- Determine: The new `TrackingDocumentsConfig` should follow the EXACT same pattern.

### 1F: State Tracking and Resume Pattern

- Read `src/agent_team/state.py`:
  - Document `RunState` dataclass (line 20) — all fields
  - Document `save_state()` function (line 165) — atomic write pattern
  - Document `completed_phases` list usage pattern
- Read cli.py resume logic:
  - How `"e2e_backend" in completed_phases` gates re-execution (line 3639)
  - Pattern for new phase markers

### 1G: REQUIREMENTS.md Parsing Pattern

- Read `src/agent_team/milestone_manager.py`:
  - Document `_parse_requirements_counts()` (line 536) — checkbox regex
  - Document `_parse_max_review_cycles()` (line 549) — review_cycles regex
  - Document `check_milestone_health()` (line 617) — full flow
- Read `src/agent_team/cli.py` `_check_convergence_health()` (line 2144):
  - Document the checkbox parsing duplicate (different from milestone_manager version?)
  - Determine if there's a shared utility or duplicated logic

### 1H: Prompt Injection Points (Full Map)

Map every location where the 3 tracking documents need to be referenced:

**E2E_COVERAGE_MATRIX.md references needed in:**
- `BACKEND_E2E_PROMPT` — "Generate E2E_COVERAGE_MATRIX.md first, then write tests"
- `FRONTEND_E2E_PROMPT` — "Update E2E_COVERAGE_MATRIX.md as you write tests"
- `E2E_FIX_PROMPT` — "Read E2E_COVERAGE_MATRIX.md to identify failing rows"
- `cli.py` E2E phase — parse matrix after tests for coverage stats

**FIX_CYCLE_LOG.md references needed in:**
- `_run_mock_data_fix()` prompt — "Read FIX_CYCLE_LOG.md first, append after fixing"
- `_run_ui_compliance_fix()` prompt — same
- `_run_e2e_fix()` prompt — same (E2E_FIX_PROMPT)
- `_run_integrity_fix()` prompt — same
- `_run_review_only()` prompt — same
- All fix function callers — pass `requirements_dir` for log path

**MILESTONE_HANDOFF.md references needed in:**
- `build_milestone_execution_prompt()` — "Read MILESTONE_HANDOFF.md before coding, update before completing"
- `CODE_WRITER_PROMPT` — "Read MILESTONE_HANDOFF.md for available API contracts"
- `_run_prd_milestones()` — generate/verify handoff after each milestone

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1H), with exact file paths, line numbers, function names, and integration points. This is the blueprint for Phase 2.

---

## PHASE 2A: CORE MODULE + CONFIG (impl-core)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### New File: `src/agent_team/tracking_documents.py`

This module contains ALL generation, parsing, and template logic for the 3 tracking documents. No CLI wiring, no prompt injection — just pure functions and constants.

#### Document 1: E2E_COVERAGE_MATRIX.md

**Generation Function: `generate_e2e_coverage_matrix()`**

```python
def generate_e2e_coverage_matrix(
    requirements_content: str,
    app_info: "AppTypeInfo | None" = None,
    route_files: list[str] | None = None,
) -> str:
```

How it works:
1. Parse REQUIREMENTS.md content to extract ALL requirement IDs (REQ-xxx, SVC-xxx, WIRE-xxx, TECH-xxx that involve endpoints or UI)
2. For each requirement, extract: the requirement text, any endpoint mentioned (method + path), any route mentioned, any role mentioned
3. Group into 3 tables:
   - **Backend API Coverage**: One row per API endpoint/requirement. Columns: `Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed`
   - **Frontend Route Coverage**: One row per frontend route/page. Columns: `Route | Component | Key Workflows | Test File | Tested | Passed`
   - **Cross-Role Workflows**: One row per multi-role workflow. Columns: `Workflow | Steps | Roles Involved | Tested | Passed`
4. All checkboxes start as `[ ]`
5. Add a coverage summary footer: `## Coverage: 0/N written (0%) | 0/0 passing (0%)`
6. If `app_info` is provided, add detected framework/stack info header
7. Return the complete markdown string

**Parsing Function: `parse_e2e_coverage_matrix()`**

```python
def parse_e2e_coverage_matrix(content: str) -> E2ECoverageStats:
```

How it works:
1. Count all `[x]` in "Test Written" column → `tests_written`
2. Count all `[x]` in "Test Passed" column → `tests_passed`
3. Count total rows across all 3 tables → `total_items`
4. Compute `coverage_ratio = tests_written / total_items`
5. Compute `pass_ratio = tests_passed / tests_written` (if tests_written > 0)
6. Return stats dataclass

**Template Constant: `E2E_COVERAGE_MATRIX_TEMPLATE`**

The markdown template with section headers, table headers, and placeholder rows. Used by the generation function as the skeleton.

**Requirement Extraction Helpers:**

```python
def _extract_api_requirements(content: str) -> list[dict]:
    """Extract REQ/SVC items that mention endpoints (GET/POST/PUT/DELETE/PATCH + /path)."""

def _extract_route_requirements(content: str) -> list[dict]:
    """Extract requirements that mention frontend routes (/path) or page components."""

def _extract_workflow_requirements(content: str) -> list[dict]:
    """Extract requirements describing multi-step or multi-role workflows."""
```

These use regex to find patterns like:
- `POST /api/auth/register` → API endpoint
- `GET /api/tenders` → API endpoint
- `/dashboard`, `/login`, `/tenders/new` → Frontend routes
- "create → review → approve" or "User A creates, User B approves" → Workflows
- Role mentions: "admin", "user", "reviewer", etc.

The extraction should be BEST-EFFORT — it's building a checklist for humans/agents, not a compiler. Missing items are caught by agents who read the matrix and add missing rows.

#### Document 2: FIX_CYCLE_LOG.md

**Initialization Function: `initialize_fix_cycle_log()`**

```python
def initialize_fix_cycle_log(requirements_dir: str) -> Path:
    """Create FIX_CYCLE_LOG.md with header if it doesn't exist. Return path."""
```

How it works:
1. Check if `{requirements_dir}/FIX_CYCLE_LOG.md` exists
2. If not, create it with a header:
   ```markdown
   # Fix Cycle Log

   This document tracks every fix attempt across all fix loops.
   Each fix agent MUST read this log before attempting a fix.
   DO NOT repeat a previously attempted strategy.

   ---
   ```
3. Return the path

**Append Function: `build_fix_cycle_entry()`**

```python
def build_fix_cycle_entry(
    phase: str,          # "E2E Backend", "E2E Frontend", "Mock Data", "UI Compliance", "Integrity (deployment)", etc.
    cycle_number: int,
    failures: list[str],
    previous_cycles: int = 0,
) -> str:
```

How it works:
1. Build a markdown section for this fix cycle:
   ```markdown
   ## {phase} — Cycle {cycle_number}

   **Failures to fix:**
   {numbered list of failures}

   **Previous cycles in this phase:** {previous_cycles}

   **Instructions for this cycle:**
   - Review the failures above
   - If previous cycles exist, read them below — DO NOT repeat their strategies
   - Diagnose root cause, apply fix, record what you did

   **After fixing, append to this section:**
   - Root cause identified: {describe}
   - Files modified: {list with line numbers}
   - Strategy used: {describe approach}
   - Result: {which failures are fixed, which remain}
   ```
2. Return the markdown string (the fix agent will append the "After fixing" part)

**Parsing Function: `parse_fix_cycle_log()`**

```python
def parse_fix_cycle_log(content: str) -> FixCycleStats:
```

How it works:
1. Count total cycles (count `## ` headers matching the pattern)
2. Group by phase name
3. For each phase, track: cycle count, whether last cycle reported all-fixed
4. Return stats dataclass

**Prompt Injection Snippet: `FIX_CYCLE_LOG_INSTRUCTIONS`**

A constant string to be injected into ALL fix prompts:

```python
FIX_CYCLE_LOG_INSTRUCTIONS = """\
[FIX CYCLE MEMORY — MANDATORY]

Before attempting ANY fix:
1. Read {requirements_dir}/FIX_CYCLE_LOG.md (if it exists)
2. Study ALL previous cycles for this phase — understand what was tried and why it failed
3. DO NOT repeat a previously attempted strategy that didn't work
4. If 3+ cycles have been attempted with no progress, consider a fundamentally different approach

After completing your fix:
5. Append to FIX_CYCLE_LOG.md with:
   - Root cause identified
   - Files modified (with line numbers)
   - Strategy used (how this differs from previous attempts)
   - Result (which failures fixed, which remain)
"""
```

#### Document 3: MILESTONE_HANDOFF.md

**Generation Function: `generate_milestone_handoff_entry()`**

```python
def generate_milestone_handoff_entry(
    milestone_id: str,
    milestone_title: str,
    status: str = "COMPLETE",
) -> str:
```

How it works:
1. Build a markdown section for this milestone:
   ```markdown
   ## {milestone_id}: {milestone_title} — {status}

   ### Exposed Interfaces
   | Endpoint | Method | Auth Required | Request Body | Response Shape |
   |----------|--------|--------------|-------------|---------------|
   <!-- Agent: Fill this table with EVERY endpoint this milestone created or modified -->

   ### Database State After This Milestone
   <!-- Agent: List all tables/collections created or modified, with column names and types -->

   ### Environment Variables
   <!-- Agent: List all env vars this milestone requires or introduces -->

   ### Files Created/Modified
   <!-- Agent: List key files with brief descriptions -->

   ### Known Limitations
   <!-- Agent: Note anything NOT yet implemented that later milestones should know about -->
   ```
2. Return the markdown string (the milestone agent fills in the tables)

**Consumption Checklist Function: `generate_consumption_checklist()`**

```python
def generate_consumption_checklist(
    milestone_id: str,
    milestone_title: str,
    predecessor_interfaces: list[dict],
) -> str:
```

How it works:
1. Parse the handoff document's "Exposed Interfaces" tables from ALL predecessor milestones
2. Build a consumption checklist for the current milestone:
   ```markdown
   ### {milestone_id}: {milestone_title} — Consuming From Predecessors
   | Source Milestone | Endpoint | Method | Frontend Service | Wired? |
   |-----------------|----------|--------|-----------------|:------:|
   | milestone-1 | POST /api/auth/register | POST | AuthService.register() | [ ] |
   | milestone-1 | POST /api/auth/login | POST | AuthService.login() | [ ] |
   | milestone-1 | GET /api/tenders | GET | TenderService.getAll() | [ ] |

   **Wiring: 0/{N} complete (0%)**
   ```
3. The milestone agent marks `[x]` as it wires each endpoint
4. Return the markdown string

**Parsing Functions:**

```python
def parse_milestone_handoff(content: str) -> list[MilestoneHandoffEntry]:
    """Parse MILESTONE_HANDOFF.md into structured entries per milestone."""

def parse_handoff_interfaces(content: str, milestone_id: str) -> list[dict]:
    """Extract the Exposed Interfaces table for a specific milestone."""

def compute_wiring_completeness(content: str, milestone_id: str) -> tuple[int, int]:
    """Count checked vs total in consumption checklist. Returns (wired, total)."""
```

**Prompt Injection Snippet: `MILESTONE_HANDOFF_INSTRUCTIONS`**

```python
MILESTONE_HANDOFF_INSTRUCTIONS = """\
[MILESTONE HANDOFF — MANDATORY]

BEFORE writing ANY code in this milestone:
1. Read {requirements_dir}/MILESTONE_HANDOFF.md
2. Study the "Exposed Interfaces" tables from ALL predecessor milestones
3. Use EXACT endpoint paths, methods, request bodies, and response shapes from the handoff
4. Do NOT guess API contracts — they are documented in the handoff

BEFORE completing this milestone:
5. Update MILESTONE_HANDOFF.md — add YOUR milestone's section with:
   - Every endpoint you created/modified (with exact path, method, auth, request/response shapes)
   - Database state (tables/columns created)
   - Environment variables introduced
   - Known limitations for future milestones
6. If this milestone consumes predecessor interfaces, mark ALL consumed endpoints as [x] in your
   consumption checklist. Any unmarked items = unwired services = AUTOMATIC REVIEW FAILURE.

NEVER scaffold with mock data when the handoff document shows the real endpoint exists.
"""
```

#### Dataclasses (add to this module or state.py — architect decides)

```python
@dataclass
class E2ECoverageStats:
    total_items: int = 0
    tests_written: int = 0
    tests_passed: int = 0
    coverage_ratio: float = 0.0
    pass_ratio: float = 0.0

@dataclass
class FixCycleStats:
    total_cycles: int = 0
    cycles_by_phase: dict[str, int] = field(default_factory=dict)
    last_phase_resolved: bool = False

@dataclass
class MilestoneHandoffEntry:
    milestone_id: str = ""
    milestone_title: str = ""
    status: str = ""
    interfaces: list[dict] = field(default_factory=list)
    wiring_complete: int = 0
    wiring_total: int = 0
```

### Config Additions: `TrackingDocumentsConfig`

Add to `src/agent_team/config.py` following the EXACT pattern of `E2ETestingConfig` and `IntegrityScanConfig`:

```python
@dataclass
class TrackingDocumentsConfig:
    """Configuration for per-phase tracking documents."""
    e2e_coverage_matrix: bool = True      # Generate E2E_COVERAGE_MATRIX.md before E2E testing
    fix_cycle_log: bool = True            # Maintain FIX_CYCLE_LOG.md across all fix loops
    milestone_handoff: bool = True        # Generate MILESTONE_HANDOFF.md in PRD+ mode
    coverage_completeness_gate: float = 0.8  # Minimum coverage ratio to pass E2E (0.0-1.0)
    wiring_completeness_gate: float = 1.0    # Minimum wiring ratio to pass milestone (0.0-1.0)
```

**Add to AgentTeamConfig:**
```python
tracking_documents: TrackingDocumentsConfig = field(default_factory=TrackingDocumentsConfig)
```

**Add to `_dict_to_config()`:**
```python
if "tracking_documents" in data and isinstance(data["tracking_documents"], dict):
    td = data["tracking_documents"]
    cfg.tracking_documents = TrackingDocumentsConfig(
        e2e_coverage_matrix=td.get("e2e_coverage_matrix", cfg.tracking_documents.e2e_coverage_matrix),
        fix_cycle_log=td.get("fix_cycle_log", cfg.tracking_documents.fix_cycle_log),
        milestone_handoff=td.get("milestone_handoff", cfg.tracking_documents.milestone_handoff),
        coverage_completeness_gate=td.get("coverage_completeness_gate", cfg.tracking_documents.coverage_completeness_gate),
        wiring_completeness_gate=td.get("wiring_completeness_gate", cfg.tracking_documents.wiring_completeness_gate),
    )
    # Validation
    if not (0.0 <= cfg.tracking_documents.coverage_completeness_gate <= 1.0):
        raise ValueError(
            f"Invalid tracking_documents.coverage_completeness_gate: "
            f"{cfg.tracking_documents.coverage_completeness_gate}. Must be between 0.0 and 1.0"
        )
    if not (0.0 <= cfg.tracking_documents.wiring_completeness_gate <= 1.0):
        raise ValueError(
            f"Invalid tracking_documents.wiring_completeness_gate: "
            f"{cfg.tracking_documents.wiring_completeness_gate}. Must be between 0.0 and 1.0"
        )
```

### Config YAML Section

```yaml
tracking_documents:
  e2e_coverage_matrix: true      # Generate coverage matrix before E2E tests
  fix_cycle_log: true            # Track fix attempts across all fix loops
  milestone_handoff: true        # Generate handoff docs between milestones
  coverage_completeness_gate: 0.8  # 80% of requirements must have E2E tests
  wiring_completeness_gate: 1.0    # 100% of predecessor interfaces must be wired
```

---

## PHASE 2B: PROMPT INJECTIONS (impl-prompts)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Injection 1: E2E Coverage Matrix into E2E Prompts

**Inject into: BACKEND_E2E_PROMPT** (in `e2e_testing.py`, line 382)

Add AFTER the existing instruction "3. Create E2E test plan in {requirements_dir}/E2E_TEST_PLAN.md":

```
4. BEFORE writing any test code, generate {requirements_dir}/E2E_COVERAGE_MATRIX.md:
   - Read REQUIREMENTS.md and extract EVERY API endpoint (REQ-xxx, SVC-xxx items)
   - Create a table with columns: Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed
   - Include a row for EVERY endpoint — no exceptions
   - Add a Cross-Role Workflows section if auth/roles are detected
   - All checkboxes start as [ ]
   - Add a coverage summary footer: ## Coverage: 0/N written (0%)

5. As you write each test:
   - Update the corresponding row in E2E_COVERAGE_MATRIX.md: mark Test Written as [x]
   - Add the test file name to the Test File column

6. After running tests:
   - Update Test Passed column: [x] for passing, [ ] for failing
   - Update the coverage summary footer with actual counts

7. You CANNOT declare this phase complete if E2E_COVERAGE_MATRIX.md has unchecked Test Written rows.
   Every row must have a test. If a requirement is not testable via API, mark it as [N/A] with a reason.
```

**Inject into: FRONTEND_E2E_PROMPT** (in `e2e_testing.py`, line 470)

Add AFTER the existing instruction about reading REQUIREMENTS.md:

```
3. BEFORE writing any Playwright test, update {requirements_dir}/E2E_COVERAGE_MATRIX.md:
   - If the matrix already exists (from backend phase), ADD a Frontend Route Coverage section
   - If it doesn't exist, CREATE it with Frontend Route Coverage table:
     Route | Component | Key Workflows | Test File | Tested | Passed
   - Add a Cross-Role Workflows section covering multi-step UI workflows
   - All checkboxes start as [ ]

4. As you write each Playwright test:
   - Update the corresponding row: mark Tested as [x], add test file name

5. After running tests:
   - Update Passed column: [x] for passing, [ ] for failing
   - Update coverage summary

6. You CANNOT declare this phase complete with unchecked Tested rows in the frontend section.
```

**Inject into: E2E_FIX_PROMPT** (in `e2e_testing.py`, line 559)

Add AFTER the existing "INSTRUCTIONS:" section:

```
0. FIRST: Read {requirements_dir}/E2E_COVERAGE_MATRIX.md to understand which specific
   tests are failing and which requirements they cover. This tells you WHAT to fix.

   ALSO: Read {requirements_dir}/FIX_CYCLE_LOG.md (if it exists) to see what previous
   fix cycles attempted. DO NOT repeat a strategy that already failed.

   After completing your fix:
   - Update E2E_COVERAGE_MATRIX.md: mark fixed tests as [x] Passed, keep failing tests as [ ]
   - Append to FIX_CYCLE_LOG.md with: root cause, files modified, strategy used, result
```

### Injection 2: Fix Cycle Log into ALL Fix Prompts

**Inject into: _run_mock_data_fix() prompt string** (via constant in `e2e_testing.py` or inline in agents.py)

The `FIX_CYCLE_LOG_INSTRUCTIONS` constant (defined in tracking_documents.py) must be imported and appended to every fix prompt. Since fix prompts are built as f-strings in cli.py, the impl-wiring agent will handle the actual f-string modification. But impl-prompts must add the instruction text to any prompt CONSTANTS that fix agents read.

Add to `E2E_FIX_PROMPT` (already covered above).

For the non-E2E fix prompts (mock, UI, integrity), the instruction text is injected by impl-wiring into the f-string prompts in cli.py. impl-prompts should create the `FIX_CYCLE_LOG_INSTRUCTIONS` constant in `tracking_documents.py` (done by impl-core) and add a reference note in `agents.py`:

Add to `CODE_WRITER_PROMPT` after the ZERO MOCK DATA POLICY section:

```
- **FIX CYCLE AWARENESS**: When deployed as part of a fix loop (mock data fix, UI compliance fix,
  integrity fix), ALWAYS read FIX_CYCLE_LOG.md in the requirements directory FIRST. Study what
  previous fix cycles attempted. Apply a DIFFERENT strategy from what was already tried.
  After fixing, APPEND your fix details to FIX_CYCLE_LOG.md.
```

### Injection 3: Milestone Handoff into Milestone Prompts

**Inject into: `build_milestone_execution_prompt()`** (in `agents.py`, line 1922)

Add the `MILESTONE_HANDOFF_INSTRUCTIONS` constant (from tracking_documents.py) to the prompt parts. Insert it AFTER the predecessor context section and BEFORE the 9-step MILESTONE WORKFLOW block:

```python
# After predecessor context injection (around line 1970)
if config.tracking_documents.milestone_handoff:
    from .tracking_documents import MILESTONE_HANDOFF_INSTRUCTIONS
    parts.append(MILESTONE_HANDOFF_INSTRUCTIONS.format(
        requirements_dir=req_dir,
    ))
```

**Inject into: `CODE_WRITER_PROMPT`** (in `agents.py`, line 939)

Add after the ZERO MOCK DATA POLICY section:

```
- **MILESTONE HANDOFF AWARENESS**: When working inside a milestone that has predecessors:
  1. Read MILESTONE_HANDOFF.md BEFORE writing any service/client code
  2. Use the EXACT endpoint paths, methods, and response shapes documented in the handoff
  3. Do NOT guess API contracts. Do NOT scaffold with mock data when the handoff shows the real endpoint.
  4. After completing your assigned task, if you created new endpoints or modified existing ones,
     note them clearly in your code comments — the milestone completion step will add them to the handoff.
```

**Inject into: Integration Verification block** (in `agents.py`, lines 2061-2080)

Extend the existing integration verification with handoff awareness:

```python
# After existing line 2076 ("5. If mismatches found, deploy DEBUGGER FLEET...")
if config.tracking_documents.milestone_handoff:
    parts.append(
        "6. Verify MILESTONE_HANDOFF.md consumption checklist is fully marked:\n"
        "   - Every predecessor endpoint used by this milestone must be [x] in the checklist\n"
        "   - Unmarked items = unwired services = MUST be fixed before milestone completes\n"
        "7. Update MILESTONE_HANDOFF.md with this milestone's exposed interfaces section\n"
        "   - List EVERY new/modified endpoint with exact path, method, auth, request/response shapes\n"
        "   - Include database state changes, environment variables, known limitations"
    )
```

### Injection 4: Milestone Handoff into ARCHITECT_PROMPT

**Inject into: `ARCHITECT_PROMPT`** (in `agents.py`, line 836)

After the existing "API Wiring Map (SVC-xxx Requirements)" section:

```
## Milestone Handoff Preparation
When designing the architecture for a milestone that creates API endpoints:
- Document EVERY endpoint in a format suitable for MILESTONE_HANDOFF.md:
  Endpoint | Method | Auth | Request Body Schema | Response Schema
- Be SPECIFIC about response shapes — include field names and types
- This documentation will be used by subsequent milestones to wire frontend services
- Vague documentation ("returns tender object") is NOT acceptable
- Specify: `{ id: string, title: string, status: "draft"|"active"|"closed", createdAt: ISO8601 }`
```

---

## PHASE 2C: CLI WIRING + MILESTONE MANAGER (impl-wiring)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Wiring 1: E2E Coverage Matrix into E2E Phase

**In `cli.py`, inside the E2E testing post-orchestration block (around line 3637):**

BEFORE calling `_run_backend_e2e_tests()`, add coverage matrix generation:

```python
# Generate E2E Coverage Matrix (if enabled)
if config.tracking_documents.e2e_coverage_matrix:
    try:
        from .tracking_documents import generate_e2e_coverage_matrix
        req_dir = Path(cwd) / config.convergence.requirements_dir
        req_content = (req_dir / "REQUIREMENTS.md").read_text(encoding="utf-8")
        matrix_content = generate_e2e_coverage_matrix(
            requirements_content=req_content,
            app_info=app_info,
        )
        matrix_path = req_dir / "E2E_COVERAGE_MATRIX.md"
        matrix_path.write_text(matrix_content, encoding="utf-8")
        print_info(f"Generated E2E coverage matrix: {matrix_path}")
    except Exception as exc:
        print_warning(f"Failed to generate E2E coverage matrix: {exc}")
```

AFTER E2E phase completes (before recovery report), add coverage stats parsing:

```python
# Parse E2E Coverage Matrix for stats (if it exists)
if config.tracking_documents.e2e_coverage_matrix:
    try:
        from .tracking_documents import parse_e2e_coverage_matrix
        matrix_path = Path(cwd) / config.convergence.requirements_dir / "E2E_COVERAGE_MATRIX.md"
        if matrix_path.is_file():
            stats = parse_e2e_coverage_matrix(matrix_path.read_text(encoding="utf-8"))
            print_info(
                f"E2E Coverage: {stats.tests_written}/{stats.total_items} tests written "
                f"({stats.coverage_ratio:.0%}), {stats.tests_passed}/{stats.tests_written} passing "
                f"({stats.pass_ratio:.0%})"
            )
            if stats.coverage_ratio < config.tracking_documents.coverage_completeness_gate:
                print_warning(
                    f"E2E coverage ({stats.coverage_ratio:.0%}) below gate "
                    f"({config.tracking_documents.coverage_completeness_gate:.0%}). "
                    f"Some requirements may not have E2E tests."
                )
                recovery_types.append("e2e_coverage_incomplete")
    except Exception as exc:
        print_warning(f"Failed to parse E2E coverage matrix: {exc}")
```

### Wiring 2: Fix Cycle Log into ALL Fix Loops

For EACH fix function in cli.py, modify the prompt construction to include fix cycle log instructions.

**Pattern (apply to ALL 5 fix functions):**

```python
# At the START of each fix function, after building the base prompt:
fix_log_section = ""
if config.tracking_documents.fix_cycle_log:
    try:
        from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
        req_dir_str = str(Path(cwd) / config.convergence.requirements_dir)
        log_path = initialize_fix_cycle_log(req_dir_str)

        # Build cycle entry for this fix attempt
        cycle_entry = build_fix_cycle_entry(
            phase="{phase_name}",  # varies per function
            cycle_number=cycle_number,  # track externally
            failures=failures_list,
        )

        # Inject into prompt
        fix_log_section = (
            f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
            f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
        )
    except Exception:
        pass  # Non-critical — don't block fix if log fails

fix_prompt = base_prompt + fix_log_section
```

Apply this to:
1. `_run_mock_data_fix()` — phase="Mock Data"
2. `_run_ui_compliance_fix()` — phase="UI Compliance"
3. `_run_e2e_fix()` — phase="E2E {test_type}"
4. `_run_integrity_fix()` — phase="Integrity ({scan_type})"
5. `_run_review_only()` — phase="Review Recovery"

**Cycle counting:** For E2E fix loops, the cycle number is already tracked in the for-loop counter (the `for retry in range(max_fix_retries)` loop). Pass `retry + 1` as `cycle_number`. For other fix functions that don't loop internally, use `cycle_number=1`.

### Wiring 3: Milestone Handoff into Milestone Flow

**In `cli.py`, inside `_run_prd_milestones()` (around line 692):**

**3a. Generate handoff document AFTER milestone completes and review recovery finishes:**

Insert at approximately line 1095 (after review recovery loop, before wiring check):

```python
# Generate/update MILESTONE_HANDOFF.md
if config.tracking_documents.milestone_handoff:
    try:
        from .tracking_documents import generate_milestone_handoff_entry
        handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"

        # Generate this milestone's handoff section
        entry = generate_milestone_handoff_entry(
            milestone_id=milestone.id,
            milestone_title=milestone.title,
            status="COMPLETE",
        )

        # Append to handoff document (create if first milestone)
        if handoff_path.is_file():
            existing = handoff_path.read_text(encoding="utf-8")
            # Check if this milestone already has an entry (resume case)
            if f"## {milestone.id}:" not in existing:
                handoff_path.write_text(existing + "\n\n---\n\n" + entry, encoding="utf-8")
        else:
            header = "# Milestone Handoff Registry\n\nThis document tracks interfaces exposed by each milestone.\nSubsequent milestones MUST read this before coding.\n\n---\n\n"
            handoff_path.write_text(header + entry, encoding="utf-8")

        print_info(f"Updated MILESTONE_HANDOFF.md with {milestone.id}")

        # Run a sub-orchestrator to fill in the handoff details
        handoff_cost = await _generate_handoff_details(
            cwd=cwd,
            config=config,
            milestone_id=milestone.id,
            milestone_title=milestone.title,
            requirements_path=str(ms_req_path),
            task_text=task,
            constraints=constraints,
            intervention=intervention,
            depth=depth,
        )
        total_cost += handoff_cost
    except Exception as exc:
        print_warning(f"Failed to update MILESTONE_HANDOFF.md: {exc}")
```

**3b. New function `_generate_handoff_details()`:**

```python
async def _generate_handoff_details(
    cwd: str | None,
    config: AgentTeamConfig,
    milestone_id: str,
    milestone_title: str,
    requirements_path: str,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
```

This function deploys a SMALL sub-orchestrator session that:
1. Reads the milestone's REQUIREMENTS.md and source code
2. Fills in the MILESTONE_HANDOFF.md section with actual endpoint details, DB state, env vars
3. Returns cost

Prompt:
```python
HANDOFF_GENERATION_PROMPT = """\
[PHASE: MILESTONE HANDOFF DOCUMENTATION]

Milestone {milestone_id} ({milestone_title}) just completed.
You must document EVERY interface this milestone exposes for subsequent milestones.

STEP 1: Read {requirements_path} to understand what was built.

STEP 2: Scan the codebase for:
- API endpoints (route files, controllers): extract path, method, auth, request/response shapes
- Database schema (migrations, models): extract table names, column names, types
- Environment variables (configs, .env): extract variable names and purposes

STEP 3: Update {requirements_dir}/MILESTONE_HANDOFF.md — find the section for {milestone_id}
and fill in ALL tables:
- Exposed Interfaces table: EVERY endpoint with exact path, method, auth, request body schema,
  response schema (include field names AND types)
- Database State: ALL tables with columns and types
- Environment Variables: ALL env vars with descriptions
- Known Limitations: Anything not yet implemented

Be EXHAUSTIVE. A vague entry like "returns tender object" is NOT acceptable.
Write: {{ id: string, title: string, status: "draft"|"active"|"closed", createdAt: string (ISO8601) }}

[ORIGINAL USER REQUEST]
{task_text}"""
```

**3c. Inject consumption checklist BEFORE milestone execution:**

In `_run_prd_milestones()`, BEFORE building `ms_prompt` (around line 957), add:

```python
# Generate consumption checklist if predecessors exist and handoff is enabled
if config.tracking_documents.milestone_handoff and predecessor_summaries:
    try:
        from .tracking_documents import generate_consumption_checklist, parse_handoff_interfaces
        handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"
        if handoff_path.is_file():
            handoff_content = handoff_path.read_text(encoding="utf-8")
            # Extract interfaces from all predecessor milestones
            all_interfaces = []
            for pred_id in [dep for dep in milestone.dependencies if dep]:
                interfaces = parse_handoff_interfaces(handoff_content, pred_id)
                all_interfaces.extend(interfaces)

            if all_interfaces:
                checklist = generate_consumption_checklist(
                    milestone_id=milestone.id,
                    milestone_title=milestone.title,
                    predecessor_interfaces=all_interfaces,
                )
                # Append consumption checklist to handoff document
                handoff_content += "\n\n" + checklist
                handoff_path.write_text(handoff_content, encoding="utf-8")
    except Exception as exc:
        print_warning(f"Failed to generate consumption checklist: {exc}")
```

**3d. Verify wiring completeness AFTER milestone execution:**

After the handoff generation (3a), add a wiring completeness check:

```python
# Check wiring completeness
if config.tracking_documents.milestone_handoff and config.tracking_documents.wiring_completeness_gate > 0:
    try:
        from .tracking_documents import compute_wiring_completeness
        handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"
        if handoff_path.is_file():
            wired, total_wiring = compute_wiring_completeness(
                handoff_path.read_text(encoding="utf-8"),
                milestone.id,
            )
            if total_wiring > 0:
                ratio = wired / total_wiring
                print_info(f"Wiring completeness for {milestone.id}: {wired}/{total_wiring} ({ratio:.0%})")
                if ratio < config.tracking_documents.wiring_completeness_gate:
                    print_warning(
                        f"Wiring completeness ({ratio:.0%}) below gate "
                        f"({config.tracking_documents.wiring_completeness_gate:.0%}). "
                        f"Some predecessor interfaces may not be wired."
                    )
    except Exception as exc:
        print_warning(f"Failed to check wiring completeness: {exc}")
```

### Wiring 4: State Tracking

Add new phase markers for tracking document events:

```python
# After E2E coverage matrix generation:
# (No phase marker needed — this is part of the E2E phase)

# After handoff generation in milestone mode:
# (No separate phase marker — part of milestone completion)
```

The tracking documents don't need their own phase markers because they're integrated into existing phases. But the FIX_CYCLE_LOG should be included in the state artifacts:

```python
# In save_state calls, include tracking document paths in artifacts
if _current_state:
    fix_log_path = Path(cwd) / config.convergence.requirements_dir / "FIX_CYCLE_LOG.md"
    if fix_log_path.is_file():
        _current_state.artifacts["fix_cycle_log"] = str(fix_log_path)
    matrix_path = Path(cwd) / config.convergence.requirements_dir / "E2E_COVERAGE_MATRIX.md"
    if matrix_path.is_file():
        _current_state.artifacts["e2e_coverage_matrix"] = str(matrix_path)
    handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"
    if handoff_path.is_file():
        _current_state.artifacts["milestone_handoff"] = str(handoff_path)
```

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2A, 2B, and 2C are complete, write tests covering:

### E2E Coverage Matrix Tests (`tests/test_tracking_documents.py`)

**Generation tests:**
- Generate from REQUIREMENTS.md with API endpoints → verify correct table rows
- Generate from REQUIREMENTS.md with frontend routes → verify route table
- Generate from REQUIREMENTS.md with multi-role workflows → verify workflow table
- Generate from REQUIREMENTS.md with no endpoints → verify empty tables with headers
- Generate with AppTypeInfo → verify framework header
- Generate from REQUIREMENTS.md with SVC-xxx entries → verify they appear as rows
- All rows start with `[ ]` checkboxes

**Parsing tests:**
- Parse matrix with all items checked → coverage 100%
- Parse matrix with half items checked → coverage 50%
- Parse matrix with zero items checked → coverage 0%
- Parse matrix with N/A items → they don't count toward total
- Parse empty/missing matrix → return zero stats
- Parse matrix with only frontend section → correct stats
- Parse matrix with both backend + frontend → combined stats

**Edge cases:**
- REQUIREMENTS.md with no clear endpoints (prose only) → best-effort extraction
- REQUIREMENTS.md with duplicate endpoints → deduplicated rows
- Endpoints with path parameters (`/api/tenders/:id`) → correctly extracted
- Very long REQUIREMENTS.md (>100 items) → all extracted
- Unicode in requirement descriptions → handled correctly

### Fix Cycle Log Tests

**Initialization tests:**
- Initialize on empty directory → creates file with header
- Initialize when file exists → returns existing path, doesn't overwrite
- Initialize with Unicode path → works correctly

**Entry building tests:**
- Build entry for E2E Backend cycle 1 → correct markdown format
- Build entry for Mock Data cycle 3 → includes previous cycle count
- Build entry with empty failures list → still produces valid entry
- Build entry with special characters in failures → escaped correctly

**Parsing tests:**
- Parse log with 3 cycles → total_cycles = 3
- Parse log with cycles across 2 phases → correct cycles_by_phase
- Parse empty log → zero stats
- Parse log with only header → zero cycles

**Integration tests:**
- FIX_CYCLE_LOG_INSTRUCTIONS constant is non-empty and contains key phrases:
  "Read", "FIX_CYCLE_LOG.md", "DO NOT repeat", "Append"

### Milestone Handoff Tests

**Generation tests:**
- Generate entry for milestone-1 → correct markdown structure with all sections
- Generate with status="IN PROGRESS" → status reflected
- Entry contains all required tables (Interfaces, Database, Environment, Files, Limitations)

**Consumption checklist tests:**
- Generate checklist from 3 predecessor interfaces → 3 rows with [ ]
- Generate checklist from empty predecessors → empty section
- Generate checklist with mixed milestone sources → correct source column

**Parsing tests:**
- Parse handoff with 2 milestone sections → 2 entries
- Parse handoff with filled interfaces table → correct field extraction
- Parse handoff with empty tables → empty interface lists
- Compute wiring: 3 wired / 5 total → (3, 5)
- Compute wiring: all wired → (N, N)
- Compute wiring: none wired → (0, N)
- Compute wiring: no checklist for milestone → (0, 0)

**Edge cases:**
- Handoff with resume (duplicate milestone section) → only one entry
- Handoff with malformed tables → graceful degradation
- Very long endpoint paths → correctly parsed
- Response shapes with nested objects → correctly preserved

### Config Tests

- TrackingDocumentsConfig has correct defaults (all True, gates at 0.8 and 1.0)
- Config loads from YAML correctly
- Config validates coverage_completeness_gate in range [0.0, 1.0]
- Config validates wiring_completeness_gate in range [0.0, 1.0]
- Invalid gate value raises ValueError
- Unknown YAML keys don't break parsing
- Partial YAML (only some fields) → defaults for missing

### Prompt Injection Tests

- BACKEND_E2E_PROMPT contains "E2E_COVERAGE_MATRIX.md"
- FRONTEND_E2E_PROMPT contains "E2E_COVERAGE_MATRIX.md"
- E2E_FIX_PROMPT contains "FIX_CYCLE_LOG.md" and "E2E_COVERAGE_MATRIX.md"
- CODE_WRITER_PROMPT contains "FIX_CYCLE_LOG.md" reference
- CODE_WRITER_PROMPT contains "MILESTONE_HANDOFF.md" reference
- build_milestone_execution_prompt() output contains MILESTONE_HANDOFF_INSTRUCTIONS when config enabled
- build_milestone_execution_prompt() output does NOT contain handoff instructions when config disabled
- ARCHITECT_PROMPT contains "Milestone Handoff Preparation"
- MILESTONE_HANDOFF_INSTRUCTIONS contains key phrases: "Read", "MILESTONE_HANDOFF.md", "Exposed Interfaces", "consumption checklist"
- FIX_CYCLE_LOG_INSTRUCTIONS contains key phrases: "Read", "FIX_CYCLE_LOG.md", "DO NOT repeat"

### CLI Wiring Tests

- E2E coverage matrix generated before E2E tests when config enabled
- E2E coverage matrix NOT generated when config disabled
- Coverage stats parsed and printed after E2E phase
- Coverage below gate adds "e2e_coverage_incomplete" to recovery_types
- Fix cycle log initialized before first fix call
- Fix cycle log instructions injected into mock data fix prompt
- Fix cycle log instructions injected into UI compliance fix prompt
- Fix cycle log instructions injected into E2E fix prompt
- Fix cycle log instructions injected into integrity fix prompt
- Milestone handoff generated after milestone completion
- Milestone handoff NOT generated when config disabled
- Consumption checklist generated before milestone with predecessors
- Wiring completeness checked after milestone completion
- Handoff generation has crash isolation (try/except)
- Coverage matrix generation has crash isolation (try/except)

### Cross-Feature Integration Tests

- New config dataclass doesn't collide with existing configs
- tracking_documents.py imports correctly from config.py and state.py
- All new functions are importable
- New prompt injections don't break existing prompt structure
- Existing tests still pass (zero regressions)

---

## PHASE 4: WIRING VERIFICATION (included in test-engineer's scope)

The test-engineer should also verify:

### 4A: Execution Position
- E2E coverage matrix generation happens BEFORE `_run_backend_e2e_tests()` call
- Coverage stats parsing happens AFTER E2E phase completes
- Fix cycle log initialization happens at the START of each fix function
- Milestone handoff generation happens AFTER review recovery, BEFORE wiring check

### 4B: Config Gating
- `tracking_documents.e2e_coverage_matrix: false` → matrix not generated, no coverage stats
- `tracking_documents.fix_cycle_log: false` → no log initialization, no log instructions in prompts
- `tracking_documents.milestone_handoff: false` → no handoff generation, no consumption checklist, no wiring check

### 4C: Crash Isolation
- Matrix generation failure doesn't block E2E tests
- Fix log failure doesn't block fix execution
- Handoff generation failure doesn't block milestone completion
- Each wrapped in its own try/except

### 4D: Backward Compatibility
- Projects without tracking_documents config section → defaults apply (all enabled)
- Projects that disable all tracking → everything works as before (no documents generated)
- Existing E2E phase behavior unchanged when matrix enabled (just adds document)
- Existing fix loops unchanged when log enabled (just adds instructions to prompt)
- Existing milestone flow unchanged when handoff enabled (just adds generation step)

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL existing tests must pass (except pre-existing test_mcp_servers.py failures — 2 known)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# Per-Phase Tracking Documents — Implementation Report

## Implementation Summary
- New module: src/agent_team/tracking_documents.py ({N} functions, {M} constants)
- Config: TrackingDocumentsConfig (5 fields)
- Prompt injections: {N} locations across agents.py, e2e_testing.py
- CLI wiring: {N} integration points in cli.py, {M} in milestone_manager.py

## Document Coverage
| Document | Generated By | Marked By | Read By | Config Gate |
|----------|-------------|----------|---------|-------------|
| E2E_COVERAGE_MATRIX.md | CLI (pre-E2E) | E2E agents | E2E fix agent | tracking_documents.e2e_coverage_matrix |
| FIX_CYCLE_LOG.md | First fix cycle | Each fix cycle | Next fix cycle | tracking_documents.fix_cycle_log |
| MILESTONE_HANDOFF.md | Post-milestone | Milestone agent | Next milestone | tracking_documents.milestone_handoff |

## Test Results
- New tests written: X
- All passing: X/X
- Regressions: 0

## Wiring Verification
- Execution position: VERIFIED / ISSUES
- Config gating: VERIFIED / ISSUES
- Crash isolation: VERIFIED / ISSUES
- Backward compatibility: VERIFIED / ISSUES

## Failure Pattern Coverage
| Original Failure | Fixed By | Method |
|-----------------|----------|--------|
| Superficial E2E testing | E2E_COVERAGE_MATRIX.md | Requirement-to-test mapping, completeness gate |
| Blind fix loops | FIX_CYCLE_LOG.md | Fix history with mandatory read-before-fix |
| Zero cross-milestone wiring | MILESTONE_HANDOFF.md | Interface documentation + consumption checklist |

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone implements anything
2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase (E2ETestingConfig for config, existing prompt injection style for prompts, existing fix function pattern for CLI wiring). Consistency over creativity.
3. **READ BEFORE YOU WRITE** — Read every file before modifying it. The codebase has 3800+ lines in cli.py — understand the context around your insertion point.
4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong.
5. **NO SHORTCUTS** — All 3 documents must be fully implemented with generation, parsing, prompt injection, and CLI wiring.
6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted.
7. **CRASH ISOLATION** — Every new integration point must be wrapped in its own try/except. Tracking document failures must NEVER block the main execution flow. These are enhancements, not gates.
8. **BACKWARD COMPATIBLE** — A project with no tracking_documents config section must work exactly as before. Defaults are all-enabled, but failure to generate a document silently degrades to no document (not a crash).
9. **BEST-EFFORT EXTRACTION** — The requirement extraction for coverage matrix and handoff parsing will not be perfect. That's OK. The documents serve as STARTING POINTS that agents refine. A matrix with 80% of endpoints auto-extracted is vastly better than no matrix.
10. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added and why in the final report.
11. **RUN TESTS AFTER EACH PHASE** — Don't wait until the end to discover failures.
