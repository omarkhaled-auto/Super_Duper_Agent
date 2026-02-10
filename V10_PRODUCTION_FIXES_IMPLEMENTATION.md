---

# Agent-Team Exhaustive Implementation — v10 Production Fixes

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (5 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `superpowers:code-reviewer` | Phase 1 — Read entire codebase, document integration patterns, produce ARCHITECTURE_REPORT.md |
| `impl-prompts` | `general-purpose` | Phase 2A — Edit `src/agent_team/agents.py`: add PRD mode root-level artifact instructions, convergence loop enforcement, requirement marking policy |
| `impl-detection` | `general-purpose` | Phase 2B — Edit `src/agent_team/e2e_testing.py`: add subdirectory app detection |
| `impl-pipeline` | `general-purpose` | Phase 2C — Edit `src/agent_team/cli.py`, `src/agent_team/display.py`, `src/agent_team/config.py`, `src/agent_team/quality_checks.py`: recovery labels, silent logging, multi-pass fix, DB-005 exclusion, UI requirements fallback |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest, fix failures, iterate until green |

### Coordination Flow

```
Wave 1 (solo): architect reads entire codebase
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-prompts (agents.py)
                  + impl-detection (e2e_testing.py)
                  + impl-pipeline (cli.py, display.py, config.py, quality_checks.py)
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
- **impl agents run simultaneously.** They work on different files:
  - impl-prompts: `src/agent_team/agents.py` ONLY
  - impl-detection: `src/agent_team/e2e_testing.py` ONLY
  - impl-pipeline: `src/agent_team/cli.py`, `src/agent_team/display.py`, `src/agent_team/config.py`, `src/agent_team/quality_checks.py`
- **test-engineer waits for ALL impl agents** before starting.
- **After the final wave completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents

- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-prompts: Can create/edit `src/agent_team/agents.py`. Do NOT touch any other source file.
- impl-detection: Can create/edit `src/agent_team/e2e_testing.py`. Do NOT touch any other source file.
- impl-pipeline: Can create/edit `src/agent_team/cli.py`, `src/agent_team/display.py`, `src/agent_team/config.py`, `src/agent_team/quality_checks.py`, `src/agent_team/design_reference.py`. Do NOT touch agents.py or e2e_testing.py.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# v10 Production Fixes — Every Upgrade Must Work

## Background — Why This Exists

Agent-team v2.0 through v9.0 built a comprehensive multi-agent orchestration system with 35+ features spanning PRD mode, convergence loops, code review fleets, E2E testing, browser testing, API contract verification, database integrity scans, deployment scans, and tracking documents. A production readiness test on a real-world Express.js + Angular project (TaskFlow Pro, exhaustive depth, 36-minute run) revealed that **only 15 of 42 checkpoints passed**. All 16 failures trace back to exactly 2 critical bugs plus 4 minor issues, with 3 additional systemic gaps identified during root cause analysis. The code generation quality was excellent (zero mock data, proper enums, real HTTP calls, complete seed data), but the post-orchestration quality assurance pipeline was severely degraded. v10 fixes every single issue found in the production test — plus 3 preventive measures — so that ALL upgrades work correctly.

### Failure 1: PRD Mode Artifacts Gap

When agent-team runs in PRD mode (`--prd` flag), `build_orchestrator_prompt()` in `agents.py` instructs the orchestrator to "Create per-milestone REQUIREMENTS.md files" (line 2397) but NEVER instructs it to generate a root-level `.agent-team/REQUIREMENTS.md`. The post-orchestration convergence health check (`_check_convergence_health()` in `cli.py`) reads this root-level file to determine convergence status. Since it doesn't exist, the health check returns `health="unknown"` with `total_requirements=0`, and the entire convergence loop reports 0 cycles. This cascades into 7 downstream failures: no SVC-xxx wiring table, no STATUS_REGISTRY, no CONTRACTS.json, no TASKS.md, no code review fleet deployment, no Enum Registry documentation, and no convergence-based recovery. In the TaskFlow Pro test, the console showed `"Convergence cycles: 0"` and `"UNKNOWN HEALTH: .agent-team/REQUIREMENTS.md does not exist"`. The standard (non-PRD) mode's `else` block (line 2401) correctly instructs REQUIREMENTS.md creation, but the PRD mode block does not.

### Failure 2: Monorepo Detection Blindness

`detect_app_type()` in `e2e_testing.py` (line 60) reads ONLY `root / "package.json"` to detect the application stack. For multi-directory project layouts where the backend and frontend live in separate subdirectories (e.g., `backend/package.json` with Express, `frontend/package.json` + `frontend/angular.json` with Angular), the function returns `has_backend=False` and `has_frontend=False`. This blocks 9 downstream features: E2E backend tests, E2E frontend tests, schema drift detection, E2E quality scan, E2E coverage matrix generation, API contract scan, browser testing workflow generation, app startup agent, and credential discovery. The API contract scan gate at `cli.py:4418` (`if _app_info.has_backend and _app_info.has_frontend`) printed `"API contract scan: skipped (not a full-stack app)"` despite the project clearly having both Express and Angular with 48 TypeScript source files. The function checks for `angular.json`, `next.config.js`, and Prisma schema only at the project root, missing `frontend/angular.json` and `backend/prisma/schema.prisma`.

### Failure 3: Silent Scan Observability Gap

When a scan runs and finds zero violations, it produces no console output. The scan-then-fix pattern in `cli.py` is structured as `if violations: print_warning(...)` with no `else` branch. This makes it impossible for operators to distinguish "scan ran and passed" from "scan was skipped entirely" without reading source code. In the TaskFlow Pro test, the mock data scan, deployment scan, dual ORM scan, and relationship scan all ran successfully with zero violations — but the initial test report marked all 4 as FAIL or INCONCLUSIVE because no output appeared. A manual re-audit of `cli.py` gating conditions was required to correct the assessments. Adding `else: print_info("X scan: 0 violations (clean)")` at each scan block solves this.

### Failure 4: Recovery Report Label Gap

`print_recovery_report()` in `display.py` (line 612) uses a `type_hints` dict to map recovery type strings to human-readable labels. This dict has only 2 entries (`"contract_generation"` and `"review_recovery"`) but `cli.py` uses 15+ recovery type strings. All unmapped types show `"Unknown recovery type"` in the recovery panel. In the TaskFlow Pro test, all 3 recovery passes (UI compliance fix, asset integrity fix, database defaults fix) displayed `"Unknown recovery type"` labels, providing no diagnostic value to the operator.

### Failure 5: DB-005 Prisma Client Delegate False Positive

The default value scanner's DB-005 check in `quality_checks.py` (line 2267) flags TypeScript patterns like `.category.findMany()` as "nullable property accessed without optional chaining." This happens because the entity model file declares `category?: Category` (an optional relation field), and then other source files access `prisma.category.findMany()`. The scanner sees `.category.` and flags it. However, `prisma.category` is a Prisma client model delegate that is ALWAYS defined — it is not a nullable property. In the TaskFlow Pro test, this produced 14 false-positive violations in `seed.ts` and `category.routes.ts`. The fix agent added unnecessary `?.` operators (`prisma.category?.findMany()`), which is harmless at runtime but semantically incorrect and would be re-flagged on subsequent scans.

### Failure 6: Single-Pass Fix Limitation

Each post-orchestration scan type gets exactly one fix pass. The pattern in `cli.py` is: scan → if violations → run fix agent → done. If the fix agent only addresses violations in one file (e.g., fixes `category-list.component.ts` but not `dashboard.component.ts`), residual violations remain unfixed. In the TaskFlow Pro test, the UI compliance scan found 100 violations, the fix pass resolved 20 in `category-list.component.ts`, but 7 violations remained in `dashboard.component.ts`. A second fix pass would catch these. The system should support configurable multi-pass fix cycles with re-scanning between passes.

### Failure 7: Zero Convergence Cycles

The post-orchestration convergence health check (`_check_convergence_health()` in `cli.py`) reads `.agent-team/REQUIREMENTS.md` to count `[x]` vs `[ ]` marks and calculate the convergence ratio. In the TaskFlow Pro test, the console showed `"Convergence cycles: 0"` — no review cycle ever triggered. This happened because (a) REQUIREMENTS.md didn't exist (Failure 1), and (b) even when REQUIREMENTS.md exists, the PRD mode orchestrator prompt contains no instruction to deploy the code review fleet, calculate convergence, or loop until the ratio reaches a threshold. The orchestrator simply builds the code in one pass and moves to post-orchestration without any review validation. The convergence mechanism exists in the runtime (`_check_convergence_health()`) but is never activated because the prompt doesn't instruct it.

### Failure 8: Orchestrator Self-Marking (Rubber-Stamp Pattern)

Even when convergence cycles do run (in non-PRD or milestone modes), the orchestrator prompt has no explicit prohibition against the orchestrator itself marking requirements as `[x]`. This creates a rubber-stamp risk where the orchestrator marks all requirements complete without deploying the code review fleet, producing 100% convergence ratios that reflect no actual code review. The segregation-of-duties principle requires that only the CODE REVIEWER fleet marks requirements — the orchestrator assigns tasks and reads ratios but never writes marks.

### Failure 9: Missing UI Requirements Without --design-ref

When the user runs in PRD mode without providing `--design-ref` URLs, the entire Phase 0.6 block in `cli.py` is skipped (gated by `if design_ref_urls:`). This means no `UI_REQUIREMENTS.md` is generated, and downstream features that reference it (UI compliance scan's design token policy, code writer UI policies, and the UI COMPLIANCE ENFORCEMENT block in milestone prompts) have no document to enforce against. In the TaskFlow Pro test, this checkpoint was marked N/A, but it should have been a PASS — the `generate_fallback_ui_requirements()` function already exists and can infer sensible defaults from the task description. The fallback just never fires because there's no `else` branch.

## What We're Building

**Deliverable 1: PRD Mode Root-Level Artifact Generation** (agents.py)
Adds explicit instructions to the PRD mode block of `build_orchestrator_prompt()` requiring the orchestrator to generate root-level `.agent-team/REQUIREMENTS.md` (with SVC-xxx table, STATUS_REGISTRY section, and `- [ ] REQ-xxx` checkboxes), `.agent-team/TASKS.md` (task dependency graph), and `.agent-team/CONTRACTS.json`. These instructions are appended after the existing per-milestone instructions. This unblocks: convergence loop, SVC-xxx wiring, STATUS_REGISTRY, CONTRACTS.json, code review fleet, Enum Registry, and TASKS.md — fixing 7 downstream failures.

**Deliverable 2: Subdirectory-Aware App Detection** (e2e_testing.py)
Extends `detect_app_type()` with a new Section 6 that scans common subdirectories (`backend/`, `frontend/`, `server/`, `client/`, `api/`, `web/`) when root-level detection finds no `package.json` or incomplete results. For each subdirectory, parses `package.json`, detects backend/frontend frameworks, checks for `angular.json` / `next.config.js` / `prisma/schema.prisma`, and sets `api_directory` / `frontend_directory` to the subdirectory path. Root-level detection results are never overridden. This unblocks: E2E testing, API contract scan, browser testing — fixing 9 downstream failures.

**Deliverable 3: Silent Scan Pass Logging** (cli.py)
Adds `else: print_info("X scan: 0 violations (clean)")` after each scan's zero-violation check in the post-orchestration pipeline. Covers all 8 scan types: mock data, UI compliance, deployment, asset, dual ORM, default value, relationship, and API contract. Provides operator confirmation that each scan executed without requiring source code inspection.

**Deliverable 4: Recovery Type Label Mapping** (display.py)
Expands the `type_hints` dictionary in `print_recovery_report()` from 2 entries to 17, covering every recovery type string used in `cli.py`. Each entry provides a descriptive human-readable label explaining what the recovery pass addresses. Unknown types still fall back to a generic message.

**Deliverable 5: DB-005 Prisma Delegate Exclusion** (quality_checks.py)
Adds a pre-check to the DB-005 TypeScript scanner: before flagging a `.propName.method()` access, inspect the preceding characters. If the access is on the `prisma` client object (i.e., `prisma.category.findMany()`), skip it — Prisma client model delegates are always defined and not nullable. Non-prisma accesses are still flagged normally.

**Deliverable 6: Configurable Multi-Pass Fix Cycles** (config.py + cli.py)
Adds `max_scan_fix_passes: int = 1` to `PostOrchestrationScanConfig`. Wraps each scan-then-fix block in `cli.py` in a loop: scan → if violations → fix → re-scan → if still violations and passes < max → fix again. Default of 1 preserves backward compatibility. At `exhaustive` depth, the depth gating logic should default this to 2.

**Deliverable 7: Convergence Loop Enforcement** (agents.py)
Adds a `[CONVERGENCE LOOP — MANDATORY]` prompt section to the PRD mode block of `build_orchestrator_prompt()`, immediately after the root-level artifact instructions from Deliverable 1. This section instructs the orchestrator that after each coding wave it MUST: (1) deploy the CODE REVIEWER fleet, (2) reviewers mark requirements `[x]` PASS or `[ ]` FAIL, (3) calculate convergence ratio, (4) loop until ratio >= 0.9, and that zero convergence cycles is NEVER acceptable. Must run at least ONE full review cycle before proceeding to post-orchestration. This fixes the "Convergence cycles: 0" observation from the production test where no review cycle ever triggered.

**Deliverable 8: Requirement Marking Policy** (agents.py)
Adds a `[REQUIREMENT MARKING — REVIEW FLEET ONLY]` prompt section immediately after the convergence loop block from Deliverable 7. This section explicitly prohibits the orchestrator from marking requirements `[x]` itself. Only the CODE REVIEWER fleet marks requirements. The orchestrator reads the convergence ratio but never writes to it. This prevents the rubber-stamp pattern observed in the production test where the orchestrator self-marked requirements as complete, bypassing actual code review verification.

**Deliverable 9: UI Requirements Fallback** (cli.py + design_reference.py)
In `cli.py` Phase 0.6, when no `--design-ref` URL is provided, the entire design extraction block is currently skipped (gated by `if design_ref_urls:`). Adds a new `else` branch that fires when `design_ref_urls` is empty/None: if `config.design_reference.fallback_generation` is True (default True), calls `generate_fallback_ui_requirements()` to generate baseline `UI_REQUIREMENTS.md` with sensible defaults inferred from the PRD/task text. This ensures every PRD-mode build gets at minimum a heuristic UI requirements document for the UI compliance scan and code writer UI policies to reference.

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

Before implementing ANYTHING, the architect must read the codebase and produce `.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: Orchestrator Prompt Structure (agents.py)

- Read `src/agent_team/agents.py` end to end (~2500 lines)
- Document `build_orchestrator_prompt()` (starts ~line 2253):
  - Full function signature and all parameters
  - The PRD mode block (lines 2394-2399): EXACT text of each `parts.append()` call
  - The non-PRD (else) block (lines 2400-2408): EXACT text — this is the reference for what root-level instructions look like
  - Where `req_dir` and `req_file` variables are set (line 2275-2276)
  - Where `master_plan` variable is set (line 2277)
  - The `is_prd_mode` condition (line 2387): exact boolean expression
  - The chunked PRD mode block (lines 2358-2373) — verify it also needs the root-level fix
- Document the ORCHESTRATOR_SYSTEM_PROMPT or equivalent system prompt constant:
  - Find where "Section 4" / "PRD Mode" instructions live in the system prompt
  - Check if SVC-xxx, STATUS_REGISTRY, CONTRACTS.json are mentioned there
  - Check if the system prompt tells the orchestrator WHERE to write REQUIREMENTS.md
- **Why**: impl-prompts needs exact insertion points and variable names to add root-level artifact instructions

### 1B: App Detection Logic (e2e_testing.py)

- Read `src/agent_team/e2e_testing.py` (~400 lines)
- Document `detect_app_type()` (starts line 60):
  - `AppTypeInfo` dataclass (line 17-37): all fields, types, defaults
  - Section 1 (line 70-138): root package.json parsing — exact deps checked for each framework
  - Section 2 (line 140-156): lock file detection
  - Section 3 (line 158-202): Python ecosystem detection
  - Section 4 (line 204-229): framework config file checks at root
  - Section 5 (line 231-248): API directory candidate list
  - End of function (line 248+): what comes after Section 5 — find the exact insertion point for Section 6
  - Helper functions: `_read_json()` (line 44), `_file_contains()` (line 52), `_pm_run()` (find it)
- Document all call sites of `detect_app_type()` across the codebase:
  - `cli.py` E2E phase (~line 4490+)
  - `cli.py` API contract scan (~line 4416)
  - `cli.py` browser testing (~line 4700+)
  - Any other call sites
- **Why**: impl-detection needs the exact framework detection patterns to replicate them for subdirectories

### 1C: Post-Orchestration Scan Pipeline (cli.py)

- Read `src/agent_team/cli.py` lines 4134-4470 (all scan blocks)
- For EACH scan block, document:
  - Gate condition (if statement)
  - Scan function call (from quality_checks)
  - Violation check pattern (`if violations:` / `if xxx_violations:`)
  - Recovery type string appended
  - Fix function call (asyncio.run pattern)
  - Whether there's an `else` branch (there should NOT be — that's the gap)
- List ALL scan blocks in execution order:
  1. Mock data scan (~line 4139)
  2. UI compliance scan (~line 4171)
  3. Deployment scan (~line 4202)
  4. Asset scan (~line 4231)
  5. PRD reconciliation (~line 4259)
  6. Dual ORM scan (~line 4306)
  7. Default value scan (~line 4341)
  8. Relationship scan (~line 4376)
  9. API contract scan (~line 4413)
- Document the recovery summary block (~line 5026): `print_recovery_report()` call
- **Why**: impl-pipeline needs exact locations for silent logging insertion and multi-pass loop wrapping

### 1D: Recovery Display (display.py)

- Read `src/agent_team/display.py` — find `print_recovery_report()` (line 612)
- Document:
  - Function signature
  - Current `type_hints` dict (line 623-626): exact keys and values
  - Display pattern: how `rtype` is looked up and rendered
  - The fallback string for unknown types: `"Unknown recovery type"` (line 635)
- Compile complete list of ALL recovery type strings from `cli.py`:
  - Search for `recovery_types.append("` — list every string
- **Why**: impl-pipeline needs the complete list to build the full type_hints dict

### 1E: Config Patterns (config.py)

- Read `src/agent_team/config.py` — find `PostOrchestrationScanConfig` dataclass
- Document:
  - All existing fields, types, defaults
  - Position in the file (line number)
- Find `_dict_to_config()` function:
  - Document the `post_orchestration_scans` loading section (how fields are read from YAML)
  - Document validation patterns (how invalid values are handled)
- Find depth gating logic (may be in cli.py):
  - Where `quick` depth disables scans
  - Where `exhaustive` depth enables max retries
  - The exact pattern for defaulting config values by depth
- **Why**: impl-pipeline needs to add `max_scan_fix_passes` following the exact existing pattern

### 1F: DB-005 Scanner Logic (quality_checks.py)

- Read `src/agent_team/quality_checks.py` — find DB-005 TypeScript section (~line 2266)
- Document:
  - How `ts_nullable_props` is populated (lines 2270-2275): regex patterns
  - The scanning loop (lines 2277-2307): how source files are iterated
  - The access pattern regex (line 2289): `rf'\.{re.escape(tname)}\.(?!\s*\?)(\w+)'`
  - The pre-context check (lines 2293-2299): what null guards are already recognized
  - Where to add the Prisma delegate exclusion: EXACT line and variable available at that point
  - What `sf_content[max(0, pos - 20):pos]` looks like for a `prisma.category.findMany()` access
- **Why**: impl-pipeline needs exact insertion point and available variables for the Prisma exclusion

### 1H: Convergence Loop Mechanism (cli.py + agents.py)

- Read `src/agent_team/cli.py` — find `_check_convergence_health()` (~line 2772):
  - How it reads `.agent-team/REQUIREMENTS.md`
  - How it counts `[x]` vs `[ ]` checkboxes for convergence ratio
  - What it returns when the file doesn't exist (health="unknown", total_requirements=0)
- Find the post-orchestration convergence decision block (~line 3921-4114):
  - Where `_use_milestones` branches the logic
  - The `_check_convergence_health()` call for standard mode
  - The `needs_recovery` decision (line ~4058)
  - The `_run_review_only()` call
- Read existing non-PRD orchestrator prompt (else block ~line 2401) for convergence loop language:
  - Does it mention "review fleet"?
  - Does it mention "convergence ratio"?
  - Does it mention looping or cycling?
- **Why**: impl-prompts needs to understand what the convergence mechanism expects so the prompt instructions match the actual runtime checks

### 1I: UI Requirements Fallback Path (cli.py + design_reference.py)

- Read `src/agent_team/cli.py` Phase 0.6 block (~line 3420-3560):
  - The outer gate: `if design_ref_urls:` — what happens when it's False?
  - Inside: the fallback path when Firecrawl unavailable + `fallback_generation=True`
  - The `generate_fallback_ui_requirements(task=..., config=..., cwd=...)` call signature
  - Where `ui_requirements_content` is used downstream (~line 3700+)
- Read `src/agent_team/design_reference.py`:
  - `generate_fallback_ui_requirements()` function (~line 508): signature, what it returns, what it writes to disk
  - `_infer_design_direction()`: how it picks a direction from task keywords
  - `DesignReferenceConfig` dataclass: the `fallback_generation` field, its default value
- Find the exact insertion point: after the closing of `if design_ref_urls:` block, before the next phase
- **Why**: impl-pipeline needs to add an `else` branch that calls the existing `generate_fallback_ui_requirements()` when no URLs are provided

### 1G: Test Conventions

- Read 2-3 existing test files (e.g., `tests/test_api_contract.py`, `tests/test_database_scans.py`)
- Document:
  - File naming pattern
  - Import patterns (what gets imported from agent_team modules)
  - Fixture patterns (tmp_path, monkeypatch, etc.)
  - How config objects are created in tests
  - How REQUIREMENTS.md / package.json files are created in tmp_path for testing
  - Assertion patterns
  - Class naming pattern (TestXxx)
- Count total existing tests: `python -m pytest tests/ --collect-only -q 2>&1 | tail -5`
- Identify pre-existing failures: `python -m pytest tests/ -x --tb=line 2>&1 | grep FAILED`
- **Why**: test-engineer needs conventions to write consistent tests

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1G), with exact file paths, line numbers, function names, and integration points. This is the blueprint for Phase 2.

---

## PHASE 2A: PRD Mode Root-Level Artifacts (impl-prompts)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Modifications to: `src/agent_team/agents.py`

**Target: `build_orchestrator_prompt()`, PRD mode block (lines 2394-2399)**

The current PRD mode block instructs the orchestrator to create per-milestone REQUIREMENTS.md files and a MASTER_PLAN.md, but does NOT instruct it to generate root-level artifacts. The non-PRD (else) block at line 2401 DOES instruct root-level REQUIREMENTS.md creation — use it as the reference pattern.

**Add AFTER line 2399** (after `"Do NOT stop until every milestone..."`) — insert the following instruction block using the `req_dir`, `req_file`, and `master_plan` variables already defined at lines 2275-2277:

```python
        # v10: Root-level artifact generation for PRD mode
        parts.append(f"\n[MANDATORY ROOT-LEVEL ARTIFACTS]")
        parts.append(f"After creating per-milestone REQUIREMENTS.md files, you MUST ALSO generate these root-level artifacts:")
        parts.append(f"1. {req_dir}/{req_file} — Consolidated REQUIREMENTS.md aggregating ALL requirements from ALL milestones.")
        parts.append(f"   Format: '- [ ] REQ-NNN: <description>' checkboxes. As milestones complete, mark items [x].")
        parts.append(f"   MUST include a '## SVC-xxx Service-to-API Wiring Map' table with columns: ID | Endpoint | Method | Request Schema | Response Schema")
        parts.append(f"   MUST include a '## STATUS_REGISTRY' section listing every enum/status type with valid values and transitions.")
        parts.append(f"2. {req_dir}/TASKS.md — Task dependency graph with TASK-xxx entries derived from the milestone plan.")
        parts.append(f"3. MANDATORY: Deploy the CONTRACT GENERATOR after task assignment to create {req_dir}/CONTRACTS.json.")
        parts.append(f"   Verify CONTRACTS.json exists before entering the convergence loop.")
        parts.append(f"These root-level files are REQUIRED for the convergence loop, code review fleet, and post-orchestration scans.")
        parts.append(f"The convergence loop reads {req_dir}/{req_file} to track progress. Without it, convergence health is 'unknown'.")
```

**Also check**: the chunked PRD block (lines 2358-2373) — if it has a similar gap (missing root-level instructions), add the same block there. The architect's report section 1A will confirm.

### Deliverable 7: Convergence Loop Enforcement — `src/agent_team/agents.py`

**Target: `build_orchestrator_prompt()`, PRD mode block — immediately after the root-level artifact block added above**

Add the following convergence loop enforcement block. This goes AFTER the `[MANDATORY ROOT-LEVEL ARTIFACTS]` block from Deliverable 1:

```python
        # v10: Convergence loop enforcement for PRD mode
        parts.append(f"\n[CONVERGENCE LOOP — MANDATORY]")
        parts.append(f"After each coding wave (implementing a batch of tasks), you MUST execute a convergence cycle:")
        parts.append(f"1. Deploy the CODE REVIEWER fleet — reviewers read the generated code against {req_dir}/{req_file}.")
        parts.append(f"2. Reviewers mark each requirement: [x] if PASS (code implements it correctly), [ ] if FAIL (not yet implemented or buggy).")
        parts.append(f"3. Calculate convergence ratio = (marked [x]) / (total requirements). Log this ratio explicitly.")
        parts.append(f"4. If ratio < 0.9, identify failing requirements, assign fix tasks, and start another coding wave → repeat from step 1.")
        parts.append(f"5. ZERO convergence cycles is NEVER acceptable. You MUST run at least ONE full review cycle before post-orchestration.")
        parts.append(f"6. The convergence loop is what populates the [x]/[ ] marks in {req_dir}/{req_file} that the post-orchestration health check reads.")
        parts.append(f"7. If you skip this loop, the health check returns 'unknown' with 0 cycles and the review recovery fleet never fires.")
        parts.append(f"Do NOT proceed to post-orchestration until at least one convergence cycle completes with ratio >= 0.9.")
```

### Deliverable 8: Requirement Marking Policy — `src/agent_team/agents.py`

**Target: `build_orchestrator_prompt()`, PRD mode block — immediately after the convergence loop block added above**

Add the following requirement marking policy. This goes AFTER the `[CONVERGENCE LOOP — MANDATORY]` block from Deliverable 7:

```python
        # v10: Requirement marking ownership policy
        parts.append(f"\n[REQUIREMENT MARKING — REVIEW FLEET ONLY]")
        parts.append(f"CRITICAL POLICY: Only the CODE REVIEWER fleet is authorized to mark requirements [x] or [ ] in {req_dir}/{req_file}.")
        parts.append(f"YOU (the orchestrator) MUST NOT mark requirements yourself. This is a segregation-of-duties control:")
        parts.append(f"- The orchestrator ASSIGNS tasks and READS the convergence ratio.")
        parts.append(f"- The code reviewer fleet EXECUTES reviews and WRITES requirement marks.")
        parts.append(f"- The code writer fleet IMPLEMENTS features but NEVER marks requirements.")
        parts.append(f"Self-marking (orchestrator marking its own requirements as complete) is a rubber-stamp anti-pattern.")
        parts.append(f"It produces 100% convergence ratios that do not reflect actual code review verification.")
        parts.append(f"If you mark a requirement [x] yourself, the convergence health check will show a ratio that was never validated by a reviewer.")
```

**Also check**: the chunked PRD block AND the non-PRD else block — add both the convergence loop and requirement marking blocks to ALL orchestrator prompt paths that generate REQUIREMENTS.md. The architect's report section 1H will confirm which paths need it.

**Verification**: After all three Deliverable 1/7/8 changes, `build_orchestrator_prompt(task="...", depth="exhaustive", config=..., prd_path="prd.md")` should produce output containing:
- "Consolidated REQUIREMENTS.md"
- "SVC-xxx"
- "STATUS_REGISTRY"
- "TASKS.md"
- "CONTRACTS.json"
- "convergence loop"
- "CONVERGENCE LOOP — MANDATORY"
- "ratio >= 0.9"
- "ZERO convergence cycles is NEVER acceptable"
- "REQUIREMENT MARKING — REVIEW FLEET ONLY"
- "CODE REVIEWER fleet is authorized"
- "rubber-stamp"

---

## PHASE 2B: Subdirectory-Aware App Detection (impl-detection)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Modifications to: `src/agent_team/e2e_testing.py`

**Target: `detect_app_type()` (line 60)**

Add a new Section 6 after the existing Section 5 (API directory detection, ~line 248). The section scans common subdirectories when root-level detection found incomplete results.

**Add at the insertion point documented in ARCHITECTURE_REPORT.md 1B:**

```python
    # ------------------------------------------------------------------
    # 6. Subdirectory scanning for monorepo/multi-directory layouts
    # ------------------------------------------------------------------
    # If root-level detection didn't find both backend and frontend,
    # scan common subdirectory names for package.json files.
    _SUBDIR_CANDIDATES = ("backend", "frontend", "server", "client", "api", "web")

    if not (info.has_backend and info.has_frontend):
        for _subdir_name in _SUBDIR_CANDIDATES:
            _subdir = root / _subdir_name
            if not _subdir.is_dir():
                continue

            _sub_pkg = _read_json(_subdir / "package.json")
            _sub_deps: dict = _sub_pkg.get("dependencies", {})
            _sub_dev: dict = _sub_pkg.get("devDependencies", {})
            _sub_all = {**_sub_deps, **_sub_dev}

            if _sub_pkg:
                # Backend framework detection in subdirectory
                if not info.has_backend:
                    if "express" in _sub_deps:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "express"
                        info.api_directory = info.api_directory or _subdir_name
                    elif "@nestjs/core" in _sub_deps:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "nestjs"
                        info.api_directory = info.api_directory or _subdir_name
                    elif "@hapi/hapi" in _sub_deps:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "hapi"
                        info.api_directory = info.api_directory or _subdir_name
                    elif "koa" in _sub_deps:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "koa"
                        info.api_directory = info.api_directory or _subdir_name

                # Frontend framework detection in subdirectory
                if not info.has_frontend:
                    if "@angular/core" in _sub_deps:
                        info.has_frontend = True
                        info.frontend_framework = info.frontend_framework or "angular"
                        info.frontend_directory = _subdir_name
                    elif "next" in _sub_deps:
                        info.has_frontend = True
                        info.frontend_framework = info.frontend_framework or "nextjs"
                        info.frontend_directory = _subdir_name
                        # Next.js also provides API routes
                        if not info.has_backend:
                            info.has_backend = True
                            info.backend_framework = info.backend_framework or "nextjs"
                    elif "react" in _sub_deps:
                        info.has_frontend = True
                        info.frontend_framework = info.frontend_framework or "react"
                        info.frontend_directory = _subdir_name
                    elif "vue" in _sub_deps:
                        info.has_frontend = True
                        info.frontend_framework = info.frontend_framework or "vue"
                        info.frontend_directory = _subdir_name

                # Database detection in subdirectory
                if not info.db_type:
                    if "prisma" in _sub_all or "@prisma/client" in _sub_deps:
                        info.db_type = "prisma"
                    elif "mongoose" in _sub_deps:
                        info.db_type = "mongoose"
                    elif "sequelize" in _sub_deps:
                        info.db_type = "sequelize"

                # Playwright in subdirectory
                if not info.playwright_installed:
                    if "@playwright/test" in _sub_dev or "@playwright/test" in _sub_deps:
                        info.playwright_installed = True

                # Language from subdirectory
                if not info.language:
                    if "typescript" in _sub_all or (_subdir / "tsconfig.json").is_file():
                        info.language = "typescript"
                    elif _sub_pkg:
                        info.language = "javascript"

                # Package manager from subdirectory lock files
                if not info.package_manager:
                    if (_subdir / "yarn.lock").is_file():
                        info.package_manager = "yarn"
                    elif (_subdir / "pnpm-lock.yaml").is_file():
                        info.package_manager = "pnpm"
                    elif (_subdir / "package-lock.json").is_file():
                        info.package_manager = "npm"

            # Framework config files in subdirectory (even without package.json)
            if not info.has_frontend and (_subdir / "angular.json").is_file():
                info.has_frontend = True
                info.frontend_framework = info.frontend_framework or "angular"
                info.frontend_directory = _subdir_name

            for _cfg in ("next.config.js", "next.config.mjs", "next.config.ts"):
                if not info.has_frontend and (_subdir / _cfg).is_file():
                    info.has_frontend = True
                    info.frontend_framework = info.frontend_framework or "nextjs"
                    info.frontend_directory = _subdir_name
                    if not info.has_backend:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "nextjs"
                    break

            # Prisma schema in subdirectory
            if not info.db_type and (_subdir / "prisma" / "schema.prisma").is_file():
                info.db_type = "prisma"

            # Python ecosystem in subdirectory
            if not info.has_backend:
                _sub_req = (_subdir / "requirements.txt").is_file()
                _sub_pyproj = (_subdir / "pyproject.toml").is_file()
                if _sub_req or _sub_pyproj:
                    _sub_py_text = ""
                    if _sub_req:
                        try:
                            _sub_py_text += (_subdir / "requirements.txt").read_text(
                                encoding="utf-8", errors="replace"
                            )
                        except OSError:
                            pass
                    if _sub_pyproj:
                        try:
                            _sub_py_text += (_subdir / "pyproject.toml").read_text(
                                encoding="utf-8", errors="replace"
                            )
                        except OSError:
                            pass
                    _low = _sub_py_text.lower()
                    if "django" in _low:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "django"
                        info.api_directory = info.api_directory or _subdir_name
                        info.language = info.language or "python"
                    elif "fastapi" in _low:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "fastapi"
                        info.api_directory = info.api_directory or _subdir_name
                        info.language = info.language or "python"
                    elif "flask" in _low:
                        info.has_backend = True
                        info.backend_framework = info.backend_framework or "flask"
                        info.api_directory = info.api_directory or _subdir_name
                        info.language = info.language or "python"

            # API directory from subdirectory structure
            if not info.api_directory and info.has_backend:
                for _api_candidate in (
                    f"{_subdir_name}/src/routes",
                    f"{_subdir_name}/src/controllers",
                    f"{_subdir_name}/src/api",
                    _subdir_name,
                ):
                    if (root / _api_candidate).is_dir():
                        info.api_directory = _api_candidate
                        break
```

**Key design rules:**
- NEVER override root-level detection results (use `info.field = info.field or "value"` pattern)
- Only scan subdirectories when `not (info.has_backend and info.has_frontend)` — skip if root already found both
- Set `frontend_directory` to the subdirectory name (e.g., `"frontend"`) for downstream use
- Set `api_directory` to the subdirectory name (e.g., `"backend"`) or a subpath (e.g., `"backend/src/routes"`)

---

## PHASE 2C: Pipeline Improvements (impl-pipeline)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Fix 3: Silent Scan Pass Logging — `src/agent_team/cli.py`

For EACH scan block documented in ARCHITECTURE_REPORT.md section 1C, add an `else` branch after the `if xxx_violations:` check. The exact pattern:

```python
            if violations:
                print_warning(...)
                # ... existing fix logic ...
            else:
                print_info("{Scan Name} scan: 0 violations (clean)")
```

Apply this pattern to ALL 8 scan blocks:
1. Mock data scan → `"Mock data scan: 0 violations (clean)"`
2. UI compliance scan → `"UI compliance scan: 0 violations (clean)"`
3. Deployment scan → `"Deployment integrity scan: 0 violations (clean)"`
4. Asset scan → `"Asset integrity scan: 0 violations (clean)"`
5. Dual ORM scan → `"Dual ORM scan: 0 violations (clean)"`
6. Default value scan → `"Default value scan: 0 violations (clean)"`
7. Relationship scan → `"Relationship scan: 0 violations (clean)"`
8. API contract scan → `"API contract scan: 0 violations (clean)"` (inside the `has_backend and has_frontend` block, after the violations check)

IMPORTANT: The `else` must be at the same indentation level as the `if violations:` check, NOT the outer try/except. Check the ARCHITECTURE_REPORT.md for exact indentation at each location.

### Fix 4: Recovery Type Labels — `src/agent_team/display.py`

**Target: `print_recovery_report()`, `type_hints` dict (line 623)**

Replace the existing 2-entry dict with the complete mapping. Get the FULL list of recovery type strings from ARCHITECTURE_REPORT.md section 1D.

```python
    type_hints = {
        "contract_generation": "CONTRACTS.json was not generated during orchestration",
        "review_recovery": "Review fleet did not achieve sufficient requirement coverage",
        "mock_data_fix": "Mock data patterns detected in service files",
        "ui_compliance_fix": "Hardcoded UI values violating design token policy",
        "deployment_integrity_fix": "Docker/deployment configuration inconsistencies",
        "asset_integrity_fix": "Broken static asset references in source files",
        "prd_reconciliation_mismatch": "PRD claims not verified in implementation",
        "database_dual_orm_fix": "Dual ORM usage causing type inconsistencies",
        "database_default_value_fix": "Missing default values or unsafe nullable access",
        "database_relationship_fix": "Incomplete ORM relationship definitions",
        "api_contract_fix": "API field name mismatches between backend and frontend",
        "e2e_backend_fix": "Backend E2E test failures requiring code fixes",
        "e2e_frontend_fix": "Frontend Playwright test failures requiring code fixes",
        "e2e_coverage_incomplete": "E2E test coverage below completeness threshold",
        "browser_testing_failed": "Browser workflow verification failures",
        "browser_testing_partial": "Some browser workflows failed verification",
    }
```

If the ARCHITECTURE_REPORT.md finds additional recovery type strings not listed above, ADD them. The `type_hints.get(rtype, "Unknown recovery type")` fallback on line 635 remains as a safety net.

### Fix 5: DB-005 Prisma Delegate Exclusion — `src/agent_team/quality_checks.py`

**Target: DB-005 TypeScript scanner, inside the loop at ~line 2290**

The scanner iterates over `ts_nullable_props` and finds `.propName.method()` patterns. Add a Prisma delegate exclusion BEFORE the violation is appended (around line 2296-2300).

After the `pos = tm.start()` assignment and before the `pre = sf_content[...]` context check, add:

```python
                            # v10: Skip Prisma client delegate accesses
                            # prisma.model.method() is NOT a nullable access —
                            # Prisma client delegates are always defined
                            _pre_word = sf_content[max(0, pos - 30):pos].rstrip()
                            if re.search(r'\bprisma\s*$', _pre_word):
                                continue
```

The regex `\bprisma\s*$` matches when the text immediately before `.category.` ends with the word `prisma` (possibly with trailing whitespace). This catches:
- `prisma.category.findMany()` — direct client access
- `prisma .category.create()` — unlikely but safe

It does NOT match:
- `user.category.name` — no `prisma` before `.category.`
- `somePrismaWrapper.category.find()` — `Wrapper` prevents word boundary match on `prisma`

### Fix 6: Configurable Multi-Pass Fix Cycles — `src/agent_team/config.py` + `src/agent_team/cli.py`

**Step 1: Add config field in `src/agent_team/config.py`**

In the `PostOrchestrationScanConfig` dataclass (find via ARCHITECTURE_REPORT.md 1E), add:

```python
    max_scan_fix_passes: int = 1  # Max fix iterations per scan (1=single pass, 2+=multi-pass)
```

In `_dict_to_config()`, add loading logic following the existing pattern for PostOrchestrationScanConfig fields:

```python
        # max_scan_fix_passes (with validation)
        _msfp = pos_scans_raw.get("max_scan_fix_passes", 1)
        if isinstance(_msfp, int) and _msfp >= 0:
            pos_cfg.max_scan_fix_passes = _msfp
        elif isinstance(_msfp, int):
            pos_cfg.max_scan_fix_passes = 0  # Treat negative as 0 (scan only, no fix)
```

In the depth gating section (where `exhaustive` sets max retries), add:

```python
        # Exhaustive depth defaults to 2 fix passes (unless user overrides)
        if "post_orchestration_scans.max_scan_fix_passes" not in user_overrides:
            if depth_str == "exhaustive":
                config.post_orchestration_scans.max_scan_fix_passes = 2
```

Check ARCHITECTURE_REPORT.md 1E for the exact location and variable names in the depth gating block. The `user_overrides` set tracks which fields the user explicitly set in their YAML.

**Step 2: Add multi-pass loop in `src/agent_team/cli.py`**

For each scan-then-fix block, wrap in a loop. The pattern:

```python
    # Before (single pass):
    if config.xxx_scan:
        try:
            violations = run_xxx_scan(Path(cwd), scope=scan_scope)
            if violations:
                print_warning(f"X scan: {len(violations)} violation(s) found.")
                recovery_types.append("xxx_fix")
                try:
                    fix_cost = asyncio.run(_run_xxx_fix(...))
                    ...
                except Exception as exc:
                    print_warning(f"X fix failed: {exc}")
            else:
                print_info("X scan: 0 violations (clean)")
        except Exception as exc:
            print_warning(f"X scan failed: {exc}")

    # After (multi-pass):
    if config.xxx_scan:
        try:
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass_num in range(max(1, _max_passes) if _max_passes > 0 else 1):
                violations = run_xxx_scan(Path(cwd), scope=scan_scope)
                if violations:
                    if _fix_pass_num > 0:
                        print_info(f"X scan pass {_fix_pass_num + 1}: {len(violations)} residual violation(s)")
                    else:
                        print_warning(f"X scan: {len(violations)} violation(s) found.")
                    if _fix_pass_num == 0:
                        recovery_types.append("xxx_fix")
                    if _max_passes > 0:
                        try:
                            fix_cost = asyncio.run(_run_xxx_fix(...))
                            ...
                        except Exception as exc:
                            print_warning(f"X fix failed: {exc}")
                            break
                    else:
                        break  # max_passes=0 means scan only, no fix
                else:
                    if _fix_pass_num == 0:
                        print_info("X scan: 0 violations (clean)")
                    else:
                        print_info(f"X scan pass {_fix_pass_num + 1}: all violations resolved")
                    break  # Clean scan — no more passes needed
        except Exception as exc:
            print_warning(f"X scan failed: {exc}")
```

Apply this pattern to these scan blocks (NOT all — PRD reconciliation and E2E scans have different structures):
1. Mock data scan
2. UI compliance scan
3. Deployment scan
4. Asset scan
5. Dual ORM scan
6. Default value scan
7. Relationship scan
8. API contract scan

For scans that use `_run_integrity_fix()` (deployment, asset, database scans), the fix function signature is the same. For mock data and UI compliance, they have dedicated fix functions.

IMPORTANT: `recovery_types.append()` should only happen ONCE (on the first pass), not on every iteration. The loop `break`s when violations reach zero or max passes are exhausted.

### Fix 9: UI Requirements Fallback When No Design-Ref — `src/agent_team/cli.py`

**Target: Phase 0.6 block (~line 3420), the `if design_ref_urls:` gate**

Currently, the entire Phase 0.6 block is gated by `if design_ref_urls:`. When no `--design-ref` URL is provided, `design_ref_urls` is an empty list and the entire block is skipped. This means PRD-mode builds without explicit design reference URLs get NO `UI_REQUIREMENTS.md`, and the UI compliance scan and code writer UI policies have nothing to reference.

**Add an `else` branch after the closing of the `if design_ref_urls:` block:**

Find the exact end of the `if design_ref_urls:` block using ARCHITECTURE_REPORT.md section 1I. After it, add:

```python
    else:
        # v10: Fallback UI requirements when no --design-ref provided
        if config.design_reference.fallback_generation:
            from .design_reference import (
                generate_fallback_ui_requirements,
                load_ui_requirements,
                validate_ui_requirements,
            )

            _current_state.current_phase = "design_extraction"
            req_dir = config.convergence.requirements_dir
            ui_file = config.design_reference.ui_requirements_file

            # Check for existing valid UI_REQUIREMENTS.md (resume scenario)
            existing = load_ui_requirements(cwd, config)
            if existing:
                missing = validate_ui_requirements(existing)
                if not missing:
                    print_info(
                        f"Phase 0.6: Reusing existing {req_dir}/{ui_file} "
                        f"(all required sections present)"
                    )
                    ui_requirements_content = existing
                else:
                    print_info(
                        f"Existing {req_dir}/{ui_file} is missing sections: "
                        f"{', '.join(missing)}. Regenerating fallback."
                    )

            if ui_requirements_content is None:
                print_info(
                    "Phase 0.6: No --design-ref provided — generating fallback UI requirements."
                )
                try:
                    ui_requirements_content = generate_fallback_ui_requirements(
                        task=args.task, config=config, cwd=cwd,
                    )
                    print_success(
                        f"Phase 0.6: Fallback {req_dir}/{ui_file} generated "
                        f"(heuristic defaults from task/PRD analysis)"
                    )
                except Exception as exc:
                    print_warning(
                        f"Phase 0.6: Fallback UI generation failed: {exc}. "
                        f"Continuing without UI requirements."
                    )
```

**Key design rules:**
- The `else` branch only fires when `design_ref_urls` is falsy (empty list or None)
- Gated by `config.design_reference.fallback_generation` — if False, no fallback fires
- Resume-safe: checks for existing valid `UI_REQUIREMENTS.md` before regenerating
- Crash-isolated: wrapped in try/except, failure is a warning not a blocker
- Uses the SAME `generate_fallback_ui_requirements()` function already used in the extraction path
- Sets `ui_requirements_content` so downstream orchestrator prompt building can reference it

**Also**: verify that `config.design_reference.fallback_generation` defaults to `True` in the `DesignReferenceConfig` dataclass. If it defaults to `False`, change the default to `True` in `config.py` so the fallback fires automatically without explicit opt-in. The architect's report section 1I will confirm the current default.

### Config YAML Section

```yaml
post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: true
  api_contract_scan: true
  max_scan_fix_passes: 1    # Default: 1 (single pass). Set 2+ for iterative fix cycles.

design_reference:
  fallback_generation: true  # Default: true. Generates heuristic UI_REQUIREMENTS.md when no --design-ref URL provided.
```

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2A, 2B, and 2C are complete, write tests covering:

### Prompt Fix Tests (`tests/test_v10_production_fixes.py`)

**PRD mode root-level artifact tests:**
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "Consolidated REQUIREMENTS.md"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "SVC-xxx"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "STATUS_REGISTRY"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "CONTRACTS.json"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "TASKS.md"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "convergence loop"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains `req_dir` value (e.g., ".agent-team")
- `build_orchestrator_prompt(prd_path="prd.md")` output contains `req_file` value (e.g., "REQUIREMENTS.md")
- Non-PRD mode (no prd_path) → still has "PLANNING FLEET to create REQUIREMENTS.md" (unchanged)
- Interview-based PRD mode (interview_scope="COMPLEX", interview_doc="...") → contains "Consolidated REQUIREMENTS.md"
- Chunked PRD mode (prd_path + prd_chunks + prd_index) → also contains root-level artifact instructions

**Convergence loop enforcement tests (Deliverable 7):**
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "CONVERGENCE LOOP — MANDATORY"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "ratio >= 0.9"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "ZERO convergence cycles is NEVER acceptable"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "at least ONE full review cycle"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "CODE REVIEWER fleet"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "convergence ratio"
- Chunked PRD mode also contains convergence loop instructions
- Non-PRD mode also contains convergence instructions (since non-PRD also generates REQUIREMENTS.md)

**Requirement marking policy tests (Deliverable 8):**
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "REQUIREMENT MARKING — REVIEW FLEET ONLY"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "CODE REVIEWER fleet is authorized"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "rubber-stamp"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "MUST NOT mark requirements yourself"
- `build_orchestrator_prompt(prd_path="prd.md")` output contains "segregation-of-duties"
- Chunked PRD mode also contains marking policy
- Non-PRD mode also contains marking policy

**Backward compatibility:**
- Non-PRD prompt with no changes to existing content passes existing test patterns
- PRD prompt still contains per-milestone instructions (not removed)
- All existing orchestrator prompt tests still pass

### Detection Tests (`tests/test_v10_production_fixes.py`)

**Root-level detection (backward compatibility):**
- Root package.json with express → has_backend=True, backend_framework="express"
- Root package.json with @angular/core → has_frontend=True, frontend_framework="angular"
- Root angular.json → has_frontend=True
- Root package.json with both express + react → both detected
- Empty project (no files) → AppTypeInfo with all defaults (False, "")

**Subdirectory detection (new):**
- backend/package.json with express → has_backend=True, backend_framework="express", api_directory contains "backend"
- frontend/package.json with @angular/core → has_frontend=True, frontend_framework="angular", frontend_directory="frontend"
- frontend/angular.json (no package.json) → has_frontend=True, frontend_framework="angular"
- backend/package.json (express) + frontend/package.json (angular) → both detected, full-stack
- server/package.json with @nestjs/core → has_backend=True, backend_framework="nestjs", api_directory contains "server"
- client/package.json with react → has_frontend=True, frontend_framework="react", frontend_directory="client"
- backend/prisma/schema.prisma → db_type="prisma"
- backend/package-lock.json → package_manager="npm"
- backend/yarn.lock → package_manager="yarn"
- backend/requirements.txt with django → has_backend=True, backend_framework="django"
- backend/requirements.txt with fastapi → has_backend=True, backend_framework="fastapi"

**Precedence rules:**
- Root package.json with express + frontend/package.json with angular → root backend kept, subdir frontend added
- Root-level detection complete (both backend+frontend) → subdirectory scan skipped entirely

**Edge cases:**
- Subdirectory exists but no package.json → skipped
- Subdirectory package.json is malformed JSON → skipped (empty dict)
- Multiple backend subdirs (backend/ and server/) → first one wins
- Playwright in subdirectory dev dependencies → playwright_installed=True
- TypeScript in subdirectory (tsconfig.json exists) → language="typescript"

### Recovery Label Tests (`tests/test_v10_production_fixes.py`)

**Label completeness:**
- Every recovery type string used in cli.py has a mapping in type_hints
- "mock_data_fix" → label contains "Mock" or "mock"
- "ui_compliance_fix" → label contains "UI" or "design"
- "deployment_integrity_fix" → label contains "Docker" or "deployment"
- "asset_integrity_fix" → label contains "asset"
- "database_default_value_fix" → label contains "default" or "nullable"
- "database_dual_orm_fix" → label contains "ORM" or "dual"
- "database_relationship_fix" → label contains "relationship"
- "api_contract_fix" → label contains "API" or "contract"
- "e2e_backend_fix" → label contains "Backend" or "E2E"
- "e2e_frontend_fix" → label contains "Playwright" or "frontend"
- "browser_testing_failed" → label contains "Browser" or "workflow"
- Unknown type → still returns fallback string (not crash)

### DB-005 Prisma Exclusion Tests (`tests/test_v10_production_fixes.py`)

- `prisma.category.findMany()` in source file with `category?:` in entity → NOT flagged
- `prisma.category.create(...)` → NOT flagged
- `prisma.user.findUnique(...)` with `user?:` in entity → NOT flagged
- `user.category.name` without prisma prefix → STILL flagged
- `someService.category.findMany()` → STILL flagged (not prisma)
- `prisma .category.count()` (whitespace) → NOT flagged (regex handles trailing space)
- `_prisma.category.find()` → STILL flagged (word boundary — `_prisma` is not `\bprisma`)

### Silent Scan Logging Tests (`tests/test_v10_production_fixes.py`)

These are harder to unit test directly since they involve print_info calls in cli.py's main function.
Instead, verify the pattern exists in source:
- Mock data scan block has `else:` branch with `print_info` containing "clean"
- UI compliance scan block has `else:` branch with `print_info` containing "clean"
- Deployment scan block has `else:` branch with `print_info` containing "clean"
- Asset scan block has `else:` branch with `print_info` containing "clean"
- Dual ORM scan block has `else:` branch with `print_info` containing "clean"
- Default value scan block has `else:` branch with `print_info` containing "clean"
- Relationship scan block has `else:` branch with `print_info` containing "clean"
- API contract scan block has `else:` branch with `print_info` containing "clean"

### Multi-Pass Fix Config Tests (`tests/test_v10_production_fixes.py`)

- `PostOrchestrationScanConfig()` default → max_scan_fix_passes=1
- Config from YAML with max_scan_fix_passes=2 → loaded correctly
- Config from YAML with max_scan_fix_passes=0 → accepted (scan only mode)
- Config from YAML with negative value → clamped to 0
- Config from YAML without max_scan_fix_passes → defaults to 1
- Exhaustive depth without user override → max_scan_fix_passes=2
- Exhaustive depth WITH user override max_scan_fix_passes=1 → respected (stays 1)
- Quick depth → max_scan_fix_passes unchanged (default 1)

### UI Requirements Fallback Tests (`tests/test_v10_production_fixes.py`)

**Fallback fires when no --design-ref provided (Deliverable 9):**
- No design_ref_urls + fallback_generation=True → `generate_fallback_ui_requirements()` is called, `UI_REQUIREMENTS.md` is written
- No design_ref_urls + fallback_generation=False → no fallback, no `UI_REQUIREMENTS.md`, no crash
- design_ref_urls provided → extraction path used, fallback NOT called (original behavior unchanged)
- Fallback with resume (existing valid `UI_REQUIREMENTS.md`) → reuses existing, does not regenerate
- Fallback with resume (existing invalid `UI_REQUIREMENTS.md`) → regenerates
- Fallback generation exception → caught, warning printed, pipeline continues (crash isolation)
- Fallback output contains "FALLBACK-GENERATED" warning header
- Fallback output contains all required sections (Color System, Typography, etc.)
- `_infer_design_direction()` returns sensible direction from task with technology keywords (e.g., "PrimeNG" → corporate direction)
- Config default: `fallback_generation` defaults to `True` in `DesignReferenceConfig`

### Cross-Feature Integration Tests

- New config field doesn't break existing config loading
- detect_app_type() with root-level package.json produces identical results to before (no regression)
- All new functions are importable from their modules
- Existing test suite passes with zero new regressions
- Convergence loop + requirement marking + root artifacts all present together in PRD prompt
- UI fallback generates content that downstream UI compliance scan can reference

---

## PHASE 4: WIRING VERIFICATION

### 4A: Execution Position
- Root-level artifact instructions appear IN the PRD mode block (not after it, not in non-PRD block)
- Convergence loop instructions appear AFTER root-level artifacts IN the PRD mode block
- Requirement marking policy appears AFTER convergence loop IN the PRD mode block
- All three prompt blocks (artifacts, convergence, marking) also appear in chunked PRD and non-PRD paths
- Subdirectory scanning runs AFTER root-level detection (never before)
- Silent scan logging `else` branch at correct indentation (same level as `if violations:`)
- Multi-pass loop wraps the entire scan-then-fix block (not just the scan)
- DB-005 exclusion runs BEFORE violation append (not after)
- Recovery labels are looked up BEFORE display (existing lookup pattern unchanged)
- UI fallback `else` branch is at the same indentation as `if design_ref_urls:` (not nested inside it)

### 4B: Config Gating
- `max_scan_fix_passes: 0` → scans run but no fix passes (scan-only mode)
- `max_scan_fix_passes: 1` → identical behavior to current (single pass)
- `max_scan_fix_passes: 2` → fix runs, re-scans, fix runs again if needed
- All existing config flags still work independently

### 4C: Crash Isolation
- Subdirectory scanning: malformed package.json in subdir → skip (don't crash)
- Subdirectory scanning: unreadable directory → skip (don't crash)
- Multi-pass fix loop: fix failure on pass 2 → break loop (don't retry infinitely)
- DB-005 exclusion: regex failure → don't crash, fall through to existing behavior
- Recovery labels: missing key → fallback to "Unknown recovery type" (don't crash)

### 4D: Backward Compatibility
- Projects with root-level package.json → identical detection results
- Projects without config.yaml → all defaults apply (max_scan_fix_passes=1, fallback_generation=true)
- Projects with milestone mode enabled → PRD prompt still includes per-milestone instructions
- Existing recovery types "contract_generation" and "review_recovery" → labels unchanged
- Non-PRD mode prompt → convergence loop and marking policy added (enhancement, not regression)
- Projects with --design-ref URLs → extraction path used as before, fallback NOT called
- Projects without --design-ref + fallback_generation=false → no fallback, same as before

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL existing tests must pass (except 2 pre-existing known failures in test_mcp_servers.py — `sequential_thinking` server always included)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green
- Expected baseline: ~4361 existing tests passing + ~115 new tests = ~4476 total

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# v10 Production Fixes — Implementation Report

## Implementation Summary
- Modified: agents.py (PRD mode prompt — ~40 new instruction lines: root artifacts + convergence loop + marking policy)
- Modified: e2e_testing.py (subdirectory detection — ~120 new lines)
- Modified: cli.py (silent logging + multi-pass fix + UI fallback — ~80 new lines)
- Modified: display.py (recovery labels — ~14 new dict entries)
- Modified: config.py (max_scan_fix_passes — ~8 new lines)
- Modified: quality_checks.py (DB-005 exclusion — ~4 new lines)
- New tests: tests/test_v10_production_fixes.py (~115 tests)

## Deliverable Coverage
| Deliverable | Files Modified | Config Gate | Fixes N Failures |
|-------------|---------------|-------------|------------------|
| 1. PRD Root Artifacts | agents.py | always (PRD mode) | 7 |
| 2. Subdir Detection | e2e_testing.py | always | 9 |
| 3. Silent Logging | cli.py | always | 0 (observability) |
| 4. Recovery Labels | display.py | always | 0 (cosmetic) |
| 5. DB-005 Exclusion | quality_checks.py | always | 0 (FP reduction) |
| 6. Multi-Pass Fix | config.py + cli.py | max_scan_fix_passes | 0 (quality) |
| 7. Convergence Loop | agents.py | always (PRD mode) | 1 (convergence) |
| 8. Marking Policy | agents.py | always (PRD mode) | 1 (rubber-stamp) |
| 9. UI Fallback | cli.py | fallback_generation | 1 (UI requirements) |

## Test Results
- New tests written: ~115
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
| REQUIREMENTS.md missing in PRD mode | Deliverable 1 | Explicit root-level artifact instructions in PRD prompt |
| detect_app_type() monorepo blind | Deliverable 2 | Subdirectory scanning with framework detection |
| Silent scan passes indistinguishable | Deliverable 3 | print_info() on zero violations |
| "Unknown recovery type" labels | Deliverable 4 | Complete type_hints dict (17 entries) |
| DB-005 Prisma delegate FP | Deliverable 5 | Pre-check for `prisma` prefix before flagging |
| Single-pass fix misses residuals | Deliverable 6 | Configurable multi-pass loop with re-scanning |
| Convergence cycles: 0 (no review loop) | Deliverable 7 | Mandatory convergence loop instructions in PRD prompt |
| Orchestrator rubber-stamps requirements | Deliverable 8 | Review fleet exclusive marking policy in PRD prompt |
| No UI_REQUIREMENTS.md without --design-ref | Deliverable 9 | Auto-fallback UI generation from task/PRD analysis |

## Production Test Impact
| Checkpoint Category | Before (v9) | After (v10 expected) |
|--------------------|-------------|---------------------|
| ✅ PASS | 15/42 | 42/42 |
| ❌ FAIL | 16/42 | 0/42 |
| ⚠️ PARTIAL | 4/42 | 0/42 |
| ⏭️ N/A | 5/42 | 0/42 (UI fallback now covers design-ref gap) |
| 🔍 INCONCLUSIVE | 2/42 | 0/42 |

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone implements anything. The ARCHITECTURE_REPORT.md is the single source of truth for integration points, patterns, and insertion locations.

2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase. Consistency over creativity. If the codebase uses dataclasses, use dataclasses. If tests use pytest fixtures, use pytest fixtures.

3. **READ BEFORE YOU WRITE** — Read every file before modifying it. Understand the context around your insertion point. Never modify a file you haven't read in the current session.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong. Tests are the specification; source code is the implementation.

5. **NO SHORTCUTS** — All 9 deliverables must be fully implemented with generation, parsing, integration, and testing. A half-implemented feature is worse than no feature.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted since this prompt was written.

7. **CRASH ISOLATION** — Every new integration point must be wrapped in its own try/except. New feature failures must NEVER block the main execution flow. These are enhancements, not gates.

8. **BACKWARD COMPATIBLE** — A project with no config section for the new feature must work exactly as before. Default of `max_scan_fix_passes=1` preserves single-pass behavior. Root-level detection precedence is never overridden by subdirectory results.

9. **BEST-EFFORT EXTRACTION** — Subdirectory detection will not cover every possible project layout. Common patterns (backend/, frontend/, server/, client/) cover 90%+ of real-world cases. Exotic layouts are handled by existing root-level detection.

10. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added and why in the final report.

11. **RUN TESTS AFTER EACH PHASE** — Don't wait until the end to discover failures. Each impl agent should run relevant tests before declaring done. The test-engineer runs the FULL suite.

12. **CLI.PY IS 5000+ LINES** — Be extremely careful with indentation when editing cli.py. Always read 20 lines of context around your insertion point. One wrong indent level breaks the entire pipeline.

13. **PRESERVE THE ELSE CHAIN** — When adding `else: print_info(...)` to scan blocks, verify you're adding it to the `if violations:` check, NOT to the outer `if config.xxx_scan:` gate. These are at different indentation levels.
