---

# Agent-Team Exhaustive Implementation — v10.1 Runtime Guarantees

## Prerequisite: V10 Must Be Complete

This prompt is a FOLLOW-UP to V10_PRODUCTION_FIXES_IMPLEMENTATION.md. All 9 V10 deliverables
must be implemented and passing before executing this prompt. Phase 0 verifies this.

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (3 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `verifier` | `superpowers:code-reviewer` | Phase 0 — Verify all 9 V10 deliverables are implemented, run tests, confirm baseline. Phase 1 — Read V10-modified codebase, document exact insertion points for Deliverables 10+11 |
| `impl-runtime` | `general-purpose` | Phase 2 — Edit `src/agent_team/cli.py` (artifact verification gate + mandatory convergence recovery) |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest, fix failures, iterate until green |

### Coordination Flow

```
Wave 1 (solo): verifier confirms V10 + discovers insertion points
    |
    Produces: .agent-team/V10_VERIFICATION_REPORT.md
    |
    GATE: If V10 verification FAILS → STOP. Do not proceed.
    |
Wave 2 (solo): impl-runtime implements Deliverables 10+11 in cli.py
    |
    Reads V10_VERIFICATION_REPORT.md first
    |
Wave 3 (solo): test-engineer writes + runs ALL tests
    |
Wave 4: You (team lead) collect results → final report
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **verifier runs first and alone.** It MUST confirm V10 is complete before anyone else starts.
- **impl-runtime runs second.** Both deliverables touch cli.py only — one agent is correct.
- **test-engineer runs last.** Writes tests, runs full suite, fixes failures.
- **After the final wave completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents

- verifier: READ ONLY. Do not edit any source files. Produce V10_VERIFICATION_REPORT.md only.
- impl-runtime: Can create/edit `src/agent_team/cli.py` ONLY. Do NOT touch any other source file.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# v10.1 Runtime Guarantees — From Prompt Enforcement to Code Enforcement

## Background — Why This Exists

V10 implemented 9 deliverables fixing production test failures. Deliverables 1-6 and 9 are
deterministic code changes. But Deliverables 7 and 8 (convergence loop enforcement, requirement
marking policy) are PROMPT-ONLY — they add text to the orchestrator prompt telling the LLM to
run convergence cycles and not self-mark requirements. There is no runtime code that verifies
these instructions were followed.

In production testing, the orchestrator LLM can ignore prompt instructions under context pressure.
This means:

- If the orchestrator ignores the "run convergence cycles" instruction → convergence_cycles = 0
- If it ignores the "generate REQUIREMENTS.md" instruction → health = "unknown"
- If it self-marks requirements → convergence_ratio = 1.0 without actual review

Prompt instructions have ~70-80% compliance rate. To reach 40/42 deterministic PASS, we need
runtime code that catches and corrects non-compliance. The prompt is the first line of defense;
the runtime gate is the guarantee.

### Gap 1: No Artifact Verification After Orchestration

The orchestrator is instructed (by V10 Deliverable 1) to generate root-level `.agent-team/REQUIREMENTS.md`,
`TASKS.md`, and `CONTRACTS.json`. But nothing CHECKS if it actually did. If the orchestrator
skips these files, the convergence health check returns `health="unknown"` with
`total_requirements=0`, the contract recovery gate sees `has_requirements = req_path.is_file()` as
False and skips, and 7+ downstream checkpoints fail silently.

The fix: after orchestration completes, check if these files exist. If not, deploy a recovery
agent that reads the generated code + PRD and creates them. This converts the prompt instruction
from "please generate this" to "generate this, and if you didn't, we'll do it for you."

### Gap 2: Unknown Health Never Triggers Recovery in PRD Mode

The convergence health check block at cli.py line ~4047-4058 handles `health="unknown"`:
- If milestones dir exists → `needs_recovery = True` (milestone mode only)
- Else → prints warning, `needs_recovery` stays False

This means: in standard PRD mode (non-milestone), when REQUIREMENTS.md is missing or has no
checkable items, the review fleet NEVER deploys. The existing code at line 4030-4033 handles
`health="failed"` with `review_cycles=0` correctly — but "unknown" is not "failed".

The fix: when `health="unknown"` AND we're in PRD mode, set `needs_recovery = True`. This
ensures the review fleet deploys even if the artifact recovery agent produced a REQUIREMENTS.md
with no parseable checkboxes. Combined with Gap 1 fix, every path leads to review fleet deployment.

### How They Work Together

```
Orchestrator finishes
    │
    ▼
[Deliverable 10] REQUIREMENTS.md exists?
    ├─ YES → skip
    └─ NO → Deploy artifact recovery agent → generates REQUIREMENTS.md + TASKS.md
    │
    ▼
[Existing] CONTRACTS.json exists?
    ├─ YES → skip
    └─ NO → Contract recovery (existing mechanism, now has_requirements=True)
    │
    ▼
[Existing] _check_convergence_health()
    ├─ REQUIREMENTS.md with [x]/[ ] marks → health="failed" (0 checked)
    │   └─ review_cycles=0 → needs_recovery=True → review fleet deploys (EXISTING CODE)
    ├─ REQUIREMENTS.md exists but no checkboxes → health="unknown"
    │   └─ [Deliverable 11] _is_prd_mode → needs_recovery=True → review fleet deploys
    └─ REQUIREMENTS.md missing (artifact recovery failed) → health="unknown"
        └─ [Deliverable 11] _is_prd_mode → needs_recovery=True → review fleet deploys
    │
    ▼
Review fleet marks [x]/[ ] → convergence ratio > 0 → PASS
```

Every path terminates at review fleet deployment. That's the guarantee.

## Issues Investigated Before Implementation

These issues were identified during prompt review and traced against the actual codebase:

| # | Issue | Verdict | Resolution |
|---|-------|---------|------------|
| 1 | `_backend` variable in `_run_artifact_recovery()` not in function signature | **NOT A BUG** — `_backend` is a module-level global (line 3063: `_backend: str = "api"`), referenced the same way by all 20+ async functions including `_run_prd_reconciliation()`. **HOWEVER**, the original prompt template used `_run_agent_session()` which doesn't exist. Fixed: template now uses the actual `ClaudeSDKClient` inline pattern. |
| 2 | Artifact gate missing milestones exclusion | **CONFIRMED** — Gate must be `_is_prd_mode and not _use_milestones`. Milestones have per-milestone REQUIREMENTS.md, not root-level. Fixed in all code templates and Phase 4 wiring. |
| 3 | "Read ALL source files" could blow context window | **VALID CONCERN** — For large projects (900+ files), reading everything is infeasible. Fixed: prompt now prioritizes route/controller files (SVC-xxx), model/entity files (STATUS_REGISTRY), and entry points (features). |
| 4 | No end-to-end flow integration test | **CONFIRMED GAP** — Tests checked content/gates but not execution ORDER. Fixed: added `TestPipelineExecutionOrder` class with 4 source position trace tests, same pattern as v7.0's `test_pipeline_execution_order.py`. |
| 5 | Review fleet marks nothing (review_cycles>0, ratio=0.0) | **ALREADY HANDLED** — Line 4083-4089: `review_cycles > 0 AND ratio < recovery_threshold (0.8)` → `needs_recovery=True` → second review recovery fires. No fix needed. Added confirmation test. |

## What We're Building

**Deliverable 10: Post-Orchestration Artifact Verification Gate** (cli.py)
After orchestration completes, before the contract health check, verify that critical artifacts
exist. If `.agent-team/REQUIREMENTS.md` is missing and we're in PRD mode, deploy a recovery
sub-orchestrator that reads all generated source code + the PRD document and produces:
(1) REQUIREMENTS.md with `- [ ] REQ-xxx` checkboxes, `## SVC-xxx` wiring table, and
`## STATUS_REGISTRY` section; (2) TASKS.md with task entries if not present. This is gated on
`_is_prd_mode` and crash-isolated. It uses the same sub-orchestrator pattern as
`_run_prd_reconciliation()`. A new async function `_run_artifact_recovery()` handles this,
with a corresponding `ARTIFACT_RECOVERY_PROMPT` constant.

**Deliverable 11: Mandatory Convergence Recovery for PRD Mode** (cli.py)
Modifies the convergence health check's `health="unknown"` handler (line ~4047-4058). In the
non-milestones branch (currently line 4057-4058), when `_is_prd_mode` is True, set
`needs_recovery = True` instead of just printing a warning. This ensures the review fleet
deploys in PRD mode even when REQUIREMENTS.md has no parseable checkboxes or when the artifact
recovery agent failed. The existing recovery mechanism (`_run_review_only()`) then handles the
actual review fleet deployment — no new recovery function needed.

---

## PHASE 0: V10 VERIFICATION (verifier)

Before implementing ANYTHING, the verifier must confirm all 9 V10 deliverables are in place.
For each deliverable, check the specific evidence. If ANY deliverable is MISSING, report it
and STOP — do not proceed to Phase 1.

### V10 Deliverable Checklist

**D1: PRD Root-Level Artifacts (agents.py)**
- Read `src/agent_team/agents.py` → find `build_orchestrator_prompt()`
- Confirm PRD mode block contains: "MANDATORY ROOT-LEVEL ARTIFACTS"
- Confirm it mentions: "Consolidated REQUIREMENTS.md", "SVC-xxx", "STATUS_REGISTRY", "TASKS.md", "CONTRACTS.json"
- Status: PASS / FAIL

**D2: Subdirectory App Detection (e2e_testing.py)**
- Read `src/agent_team/e2e_testing.py` → find `detect_app_type()`
- Confirm Section 6 exists: subdirectory scanning with `_SUBDIR_CANDIDATES`
- Confirm it checks: backend/, frontend/, server/, client/, api/, web/
- Status: PASS / FAIL

**D3: Silent Scan Pass Logging (cli.py)**
- Read `src/agent_team/cli.py` → find mock data scan block
- Confirm `else: print_info(` branch exists after `if mock_violations:`
- Spot-check 2 more scan blocks (deployment, API contract) for the same pattern
- Status: PASS / FAIL

**D4: Recovery Type Labels (display.py)**
- Read `src/agent_team/display.py` → find `print_recovery_report()`
- Confirm `type_hints` dict has > 10 entries (V9 had only 2)
- Confirm "mock_data_fix", "ui_compliance_fix", "database_default_value_fix" are present
- Status: PASS / FAIL

**D5: DB-005 Prisma Exclusion (quality_checks.py)**
- Read `src/agent_team/quality_checks.py` → find DB-005 TypeScript section
- Confirm there's a `prisma` prefix check before violation append (regex `\bprisma\s*$`)
- Status: PASS / FAIL

**D6: Multi-Pass Fix Config (config.py + cli.py)**
- Read `src/agent_team/config.py` → find `PostOrchestrationScanConfig`
- Confirm `max_scan_fix_passes` field exists with default 1
- Spot-check one scan block in cli.py for loop wrapping pattern
- Status: PASS / FAIL

**D7: Convergence Loop Enforcement (agents.py)**
- Read `src/agent_team/agents.py` → find `build_orchestrator_prompt()` PRD block
- Confirm "CONVERGENCE LOOP — MANDATORY" section exists
- Confirm it mentions: "ratio >= 0.9", "ZERO convergence cycles", "at least ONE full review cycle"
- Status: PASS / FAIL

**D8: Requirement Marking Policy (agents.py)**
- Same location as D7
- Confirm "REQUIREMENT MARKING — REVIEW FLEET ONLY" section exists
- Confirm it mentions: "rubber-stamp", "CODE REVIEWER fleet is authorized"
- Status: PASS / FAIL

**D9: UI Requirements Fallback (cli.py)**
- Read `src/agent_team/cli.py` → find Phase 0.6 block
- Confirm `else:` branch exists after `if design_ref_urls:`
- Confirm it calls `generate_fallback_ui_requirements()`
- Status: PASS / FAIL

### Test Baseline

Run: `python -m pytest tests/ -v --tb=short 2>&1 | tail -20`

- Record total tests passing
- Record any failures (distinguish pre-existing vs new)
- ALL V10 tests must be passing
- If V10 tests are failing → STOP, report which ones

### Output

Write `.agent-team/V10_VERIFICATION_REPORT.md`:

```markdown
# V10 Verification Report

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| D1: PRD Root Artifacts | PASS/FAIL | [line number, exact text found] |
| D2: Subdir Detection | PASS/FAIL | [line number, exact text found] |
| D3: Silent Logging | PASS/FAIL | [line numbers of else branches found] |
| D4: Recovery Labels | PASS/FAIL | [count of type_hints entries] |
| D5: DB-005 Exclusion | PASS/FAIL | [line number, regex found] |
| D6: Multi-Pass Config | PASS/FAIL | [field name, default value] |
| D7: Convergence Loop | PASS/FAIL | [line number, section header found] |
| D8: Marking Policy | PASS/FAIL | [line number, section header found] |
| D9: UI Fallback | PASS/FAIL | [line number, else branch found] |

## Test Baseline
- Total passing: XXXX
- Pre-existing failures: X (list)
- V10 new test failures: X (list)

## Verdict
ALL 9 DELIVERABLES VERIFIED / BLOCKED — [list missing deliverables]
```

**GATE: If verdict is BLOCKED, STOP. Do not proceed to Phase 1.**

---

## PHASE 1: ARCHITECTURE DISCOVERY (verifier — continues after Phase 0 passes)

After V10 verification passes, the verifier reads the V10-modified cli.py to find exact
insertion points for Deliverables 10+11. Add these sections to V10_VERIFICATION_REPORT.md.

### 1A: Artifact Verification Insertion Point

- Read `src/agent_team/cli.py` — find these landmarks:
  - TASKS.md diagnostic block end (~line 3865): exact last line
  - Contract health check start (~line 3867): exact first line
  - The variables available at this point: `cwd`, `config`, `args`, `_is_prd_mode`, `_use_milestones`, `_current_state`, `total_cost`, `constraints`, `intervention`, `recovery_types`, `depth`, `_backend`
  - The `req_path` definition pattern (how it's computed from config)
- Read `_run_prd_reconciliation()` function (~line 2071):
  - Full signature
  - How it builds the prompt (PRD_RECONCILIATION_PROMPT.format())
  - How it calls `_build_options()`
  - How it calls `_run_agent_session()`
  - How it returns cost
- **Why**: impl-runtime needs the exact insertion point, variable context, and async function pattern

### 1B: Convergence Unknown Handler

- Read the convergence health check block — specifically the `elif convergence_report.health == "unknown":` branch (~line 4047-4058)
- Document:
  - The milestones_dir check (lines 4049-4056): exact logic
  - The non-milestones else block (lines 4057-4058): exact current code
  - Whether `_is_prd_mode` variable is accessible at this point
  - The `needs_recovery` variable: confirm it's defined before this block
- **Why**: impl-runtime needs to know exactly what to change in the unknown handler

### 1C: _run_review_only() Usage Pattern

- Read `_run_review_only()` signature (~line 2857)
- Document the call site at line 4082: exact arguments passed
- Confirm the recovery mechanism works: needs_recovery=True → recovery_types.append → _run_review_only() → re-check health
- **Why**: Deliverable 11 doesn't need a new recovery function — it reuses the existing one. Confirm the mechanism is intact.

### 1D: Existing PRD_RECONCILIATION_PROMPT

- Find `PRD_RECONCILIATION_PROMPT` in cli.py
- Document its full text or at least its structure
- Document the {requirements_dir} and {task_text} format placeholders
- **Why**: The ARTIFACT_RECOVERY_PROMPT will follow the same pattern

### Output

Append sections 1A-1D to `.agent-team/V10_VERIFICATION_REPORT.md`.

---

## PHASE 2: IMPLEMENTATION (impl-runtime)

Read V10_VERIFICATION_REPORT.md first. Follow every pattern EXACTLY as documented.

### Deliverable 10: Artifact Verification Gate — `src/agent_team/cli.py`

**Step 1: Add the ARTIFACT_RECOVERY_PROMPT constant**

Find where `PRD_RECONCILIATION_PROMPT` is defined in cli.py (it's a module-level string constant).
Add `ARTIFACT_RECOVERY_PROMPT` near it. The prompt must instruct the sub-orchestrator to:

```python
ARTIFACT_RECOVERY_PROMPT = """\
[ARTIFACT RECOVERY — POST-ORCHESTRATION]

The orchestrator has finished building the project but did NOT generate the required
tracking documents. You MUST create these files by analyzing the generated source code
and the original PRD/task description.

STEP 1: Scan the project structure. PRIORITIZE reading these files first:
  - Route/controller files (routes/, controllers/, api/) — needed for SVC-xxx table
  - Model/entity files (models/, entities/, prisma/schema.prisma) — needed for STATUS_REGISTRY
  - Main entry points (app.ts, main.ts, index.ts, server.ts) — needed for feature inventory
  - Component index files (components/, pages/, features/) — needed for frontend REQ-xxx items
  For large projects (100+ files), focus on these categories. Do NOT attempt to read every file.
STEP 2: Read the PRD document if it exists.
STEP 3: Generate {requirements_dir}/REQUIREMENTS.md with this EXACT format:

## Requirements

For each feature you can identify in the source code, write:
- [ ] REQ-NNN: <description of the feature>

Number them sequentially starting from REQ-001.
Include ALL features: API endpoints, UI components, authentication, database operations, etc.
Mark ALL as [ ] (unchecked) — the REVIEW FLEET will mark them [x] after verification.

## SVC-xxx Service-to-API Wiring Map

| ID | Endpoint | Method | Request Schema | Response Schema |
|----|----------|--------|---------------|-----------------|
| SVC-001 | /api/... | GET/POST/... | {{ field: type }} | {{ field: type }} |

Populate this table by reading the actual route/controller files.
One row per API endpoint. Use the actual field names from the code.

## STATUS_REGISTRY

List every enum, status type, and state machine found in the codebase:
- Enum Name: [list of valid values]
- Status transitions: [from → to rules if discoverable]

STEP 4: If {requirements_dir}/TASKS.md does NOT exist, generate it:

## Tasks

For each REQ-xxx requirement, create a corresponding task:
- TASK-NNN: <implementation task> (status: COMPLETE)

Mark all tasks COMPLETE since the code is already built.
{task_text}
"""
```

**Step 2: Add the async function `_run_artifact_recovery()`**

Add this function near `_run_prd_reconciliation()` (follow the same pattern exactly):

```python
async def _run_artifact_recovery(
    cwd: str | None,
    config: AgentTeamConfig,
    task_text: str | None = None,
    prd_path: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Deploy artifact recovery agent to generate missing REQUIREMENTS.md and TASKS.md.

    This is a safety net for PRD mode when the orchestrator fails to generate
    root-level tracking artifacts. Reads all generated source code + PRD and
    produces structured REQUIREMENTS.md with REQ-xxx checkboxes, SVC-xxx table,
    and STATUS_REGISTRY section.

    NOTE: _backend is a module-level global (line ~3063: `_backend: str = "api"`),
    referenced the same way by _run_prd_reconciliation() and all 20+ async functions.
    """
    print_info("Artifact recovery: generating missing REQUIREMENTS.md from source code analysis...")

    prompt = ARTIFACT_RECOVERY_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}" if task_text else "",
    )

    # If PRD document exists, prepend it as context
    if prd_path:
        prd_file = Path(prd_path)
        if prd_file.is_file():
            try:
                prd_content = prd_file.read_text(encoding="utf-8", errors="replace")
                prompt = f"[PRD DOCUMENT]\n{prd_content}\n\n{prompt}"
            except OSError:
                pass

    # Follow the EXACT pattern from _run_prd_reconciliation() (line ~2091-2104):
    # _backend is a module-level global, NOT a parameter.
    options = _build_options(
        config, cwd, constraints=constraints, task_text=task_text,
        depth=depth, backend=_backend,
    )
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(
                client, config, phase_costs, current_phase="artifact_recovery",
            )
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Artifact recovery agent failed: {exc}\n{traceback.format_exc()}")

    return cost
```

**IMPORTANT**: This function uses `ClaudeSDKClient` + `client.query()` + `_process_response()` inline —
the exact same pattern as `_run_prd_reconciliation()` (line ~2095-2104). There is NO `_run_agent_session()`
helper in cli.py. Do NOT invent one. Copy the pattern exactly from `_run_prd_reconciliation()`.

**Step 3: Add the verification gate in `main()` — cli.py**

Find the exact insertion point documented in V10_VERIFICATION_REPORT.md section 1A.
Insert AFTER the TASKS.md diagnostic block and BEFORE the contract health check:

```python
    # -------------------------------------------------------------------
    # v10.1: Artifact Verification Gate — ensure REQUIREMENTS.md exists
    # -------------------------------------------------------------------
    if _is_prd_mode and not _use_milestones:
        req_path_check = (
            Path(cwd) / config.convergence.requirements_dir
            / config.convergence.requirements_file
        )
        if not req_path_check.is_file():
            print_warning(
                "ARTIFACT RECOVERY: REQUIREMENTS.md not found after orchestration. "
                "Deploying recovery agent to generate from source code analysis."
            )
            recovery_types.append("artifact_recovery")
            try:
                _artifact_cost = asyncio.run(_run_artifact_recovery(
                    cwd=cwd,
                    config=config,
                    task_text=args.task,
                    prd_path=getattr(args, "prd", None),
                    constraints=constraints,
                    intervention=intervention,
                    depth=depth,
                ))
                if _current_state:
                    _current_state.total_cost += _artifact_cost

                # Verify recovery produced the file
                if req_path_check.is_file():
                    print_success("Artifact recovery: REQUIREMENTS.md generated successfully.")
                else:
                    print_warning("Artifact recovery completed but REQUIREMENTS.md still not found.")

                # Also check TASKS.md
                tasks_path_check = (
                    Path(cwd) / config.convergence.requirements_dir / "TASKS.md"
                )
                if tasks_path_check.is_file():
                    print_info("Artifact recovery: TASKS.md also generated.")
            except Exception as exc:
                import traceback
                print_warning(f"Artifact recovery failed: {exc}")
                print_warning(traceback.format_exc())
        else:
            print_info("Artifact verification: REQUIREMENTS.md exists (no recovery needed).")
```

**Key design rules:**
- Gated on `_is_prd_mode` only — non-PRD mode already generates REQUIREMENTS.md via the else block
- Uses the same `asyncio.run()` pattern as all other recovery passes
- Crash-isolated: try/except with traceback logging
- Verifies the file was actually created after recovery
- Adds "artifact_recovery" to recovery_types for display
- Also checks TASKS.md as a bonus

### Deliverable 11: Mandatory Convergence Recovery — `src/agent_team/cli.py`

**Target: The convergence health check block, `elif convergence_report.health == "unknown":` branch**

Find the exact lines documented in V10_VERIFICATION_REPORT.md section 1B.

The current non-milestones else block (~line 4057-4058):

```python
        else:
            print_warning("Convergence health: unknown (no requirements found).")
```

Replace with:

```python
        else:
            if _is_prd_mode:
                # v10.1: Force recovery in PRD mode even when no requirements found.
                # Artifact recovery (Deliverable 10) should have created REQUIREMENTS.md,
                # but if it failed or produced no parseable checkboxes, we still want
                # the review fleet to deploy and establish baseline convergence.
                print_warning(
                    "UNKNOWN HEALTH in PRD mode — deploying mandatory review fleet "
                    "to establish baseline convergence."
                )
                needs_recovery = True
            else:
                print_warning("Convergence health: unknown (no requirements found).")
```

**Also**: Add "artifact_recovery" to the `type_hints` dict in `display.py` — BUT ONLY IF impl-runtime has access to display.py. If not, skip this and let the test-engineer handle it. Actually, per the agent rules, impl-runtime can ONLY edit cli.py. So this label addition should be noted for the test-engineer to add if needed.

**UPDATE display.py type_hints**: The test-engineer (who can edit any source file) should add this entry to the `type_hints` dict in `display.py`:

```python
"artifact_recovery": "Missing REQUIREMENTS.md recovered from source code analysis",
```

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2 is complete, write tests in `tests/test_v10_1_runtime_guarantees.py`.

### Artifact Recovery Tests

**Function existence and signature:**
- `_run_artifact_recovery` is importable or definable (it's async, returns float)
- `ARTIFACT_RECOVERY_PROMPT` constant exists in cli.py
- `ARTIFACT_RECOVERY_PROMPT` contains "REQUIREMENTS.md"
- `ARTIFACT_RECOVERY_PROMPT` contains "SVC-xxx"
- `ARTIFACT_RECOVERY_PROMPT` contains "STATUS_REGISTRY"
- `ARTIFACT_RECOVERY_PROMPT` contains "TASKS.md"
- `ARTIFACT_RECOVERY_PROMPT` contains "{requirements_dir}" placeholder
- `ARTIFACT_RECOVERY_PROMPT` contains "{task_text}" placeholder

**Gate logic tests (mock the main() pipeline inline or test the gate conditions):**
- `_is_prd_mode=True` + REQUIREMENTS.md missing → recovery block entered (verify via source pattern)
- `_is_prd_mode=True` + REQUIREMENTS.md exists → recovery skipped
- `_is_prd_mode=False` → recovery skipped entirely
- Recovery exception → caught, warning printed, pipeline continues (verify try/except exists)
- "artifact_recovery" added to recovery_types only when REQUIREMENTS.md missing

**Recovery type label:**
- "artifact_recovery" has a mapping in `type_hints` dict in display.py
- The label contains "REQUIREMENTS" or "source code"

### Mandatory Convergence Recovery Tests

**Convergence unknown handler tests:**
- `health="unknown"` + `_is_prd_mode=True` (non-milestones) → `needs_recovery=True`
- `health="unknown"` + `_is_prd_mode=False` (non-milestones) → `needs_recovery=False`
- `health="unknown"` + milestones dir exists → `needs_recovery=True` (existing, verify preserved)
- `health="failed"` + `review_cycles=0` → `needs_recovery=True` (existing, verify preserved)
- `health="healthy"` → `needs_recovery=False` (existing, verify preserved)
- `health="degraded"` below threshold → `needs_recovery=True` (existing, verify preserved)

**Source pattern verification:**
- The `elif convergence_report.health == "unknown":` block contains `_is_prd_mode` check
- The `_is_prd_mode` branch sets `needs_recovery = True`
- The non-PRD branch still prints the existing warning message

### Pipeline Order Trace Test (CRITICAL — addresses Issue 4)

This is the most important integration test. It reads `src/agent_team/cli.py` as source text
and verifies the execution order by checking line number positions:

```python
class TestPipelineExecutionOrder:
    """Verify the post-orchestration pipeline order in cli.py source code."""

    def test_artifact_recovery_before_contract_check(self):
        """Artifact verification gate must appear BEFORE contract health check."""
        source = Path("src/agent_team/cli.py").read_text(encoding="utf-8")
        artifact_pos = source.find("ARTIFACT RECOVERY")  # or the actual marker text
        contract_pos = source.find("Contract health check")
        assert artifact_pos > 0, "Artifact recovery block not found in cli.py"
        assert contract_pos > 0, "Contract health check block not found in cli.py"
        assert artifact_pos < contract_pos, (
            f"Artifact recovery (pos {artifact_pos}) must appear BEFORE "
            f"contract check (pos {contract_pos})"
        )

    def test_contract_check_before_convergence_check(self):
        """Contract health check must appear BEFORE convergence health check."""
        source = Path("src/agent_team/cli.py").read_text(encoding="utf-8")
        contract_pos = source.find("Contract health check")
        convergence_pos = source.find("Convergence health check")
        assert contract_pos < convergence_pos

    def test_convergence_check_before_scan_scope(self):
        """Convergence health check must appear BEFORE scan scope computation."""
        source = Path("src/agent_team/cli.py").read_text(encoding="utf-8")
        convergence_pos = source.find("Convergence health check")
        scan_scope_pos = source.find("Compute scan scope")
        assert convergence_pos < scan_scope_pos

    def test_prd_mode_unknown_handler_has_force_recovery(self):
        """The unknown health handler must force recovery in PRD mode."""
        source = Path("src/agent_team/cli.py").read_text(encoding="utf-8")
        # Find the unknown handler block
        unknown_pos = source.find('convergence_report.health == "unknown"')
        assert unknown_pos > 0
        # Within 500 chars after, find _is_prd_mode check
        block = source[unknown_pos:unknown_pos + 800]
        assert "_is_prd_mode" in block, "Unknown handler must check _is_prd_mode"
        assert "needs_recovery = True" in block, "Unknown handler must set needs_recovery"
```

Adapt the exact marker strings after reading the actual source in V10_VERIFICATION_REPORT.md.
The test-engineer should use the EXACT comment strings from the codebase.

### End-to-End Flow Verification

**Full path trace (source pattern checks):**
- Artifact verification gate appears BEFORE contract health check in cli.py
- Artifact verification gate appears AFTER TASKS.md diagnostic in cli.py
- Mandatory convergence recovery is INSIDE the convergence health check block
- The `needs_recovery=True` path leads to `_run_review_only()` call (existing mechanism)
- Every `_is_prd_mode and not _use_milestones` path through the artifact gate terminates at either "REQUIREMENTS.md exists" or "recovery attempted"
- Every `health="unknown" and _is_prd_mode` path terminates at `needs_recovery=True`

### Issue 5 Confirmation Test

**Review fleet marks nothing scenario (verify existing code handles it):**
- When `health="failed"` AND `review_cycles > 0` AND `convergence_ratio < recovery_threshold` (0.8 default) → `needs_recovery=True`
- This means: if review fleet ran but marked 0 requirements, ratio=0.0 < 0.8 → second review recovery fires
- Test: read cli.py, find the `elif review_cycles > 0` branch inside `health == "failed"`, confirm `convergence_ratio < recovery_threshold` → `needs_recovery = True`
- This is NOT a bug — it's correct behavior. The test documents it.

**Backward compatibility:**
- Non-PRD mode: no artifact recovery, no convergence force — identical behavior
- PRD mode with REQUIREMENTS.md present: artifact recovery skipped — identical behavior
- Projects without config.yaml: all defaults apply, no crashes
- Milestones mode: artifact recovery skipped (milestones have their own REQUIREMENTS.md per-milestone)

**Config safety:**
- No new config fields are introduced (both deliverables use existing `_is_prd_mode` gate)
- Existing config loading is unchanged

### V10 Regression Tests

- ALL existing V10 tests still pass (zero regressions)
- V10 test file exists: `tests/test_v10_production_fixes.py`
- V10 test count matches baseline from Phase 0

---

## PHASE 4: WIRING VERIFICATION

### 4A: Execution Position
- Artifact verification gate appears AFTER TASKS.md diagnostic, BEFORE contract health check
- Mandatory convergence recovery is INSIDE the `elif health == "unknown":` block
- The `_is_prd_mode` variable is accessible at both insertion points
- No code was added outside the designated insertion points

### 4B: Flow Correctness
- Artifact recovery → contract recovery → convergence check → review recovery
- If artifact recovery creates REQUIREMENTS.md → contract recovery sees `has_requirements=True`
- If artifact recovery creates REQUIREMENTS.md with checkboxes → convergence returns health="failed" (0 checked) → existing recovery fires
- If artifact recovery creates REQUIREMENTS.md without checkboxes → convergence returns health="unknown" → Deliverable 11 forces recovery
- If artifact recovery fails → convergence returns health="unknown" → Deliverable 11 forces recovery

### 4C: Crash Isolation
- Artifact recovery: try/except with traceback logging → non-blocking
- Convergence unknown handler: no new try/except needed (inside existing try block)
- Artifact recovery exception does NOT prevent convergence check from running
- Convergence recovery exception does NOT prevent post-orchestration scans from running

### 4D: Backward Compatibility
- Non-PRD mode: both deliverables gated on `_is_prd_mode` → no change
- Milestones mode: artifact recovery gated on `_is_prd_mode` and `not req_path_check.is_file()` → milestones have per-milestone REQUIREMENTS.md, not root-level, so this may trigger → need to also check `not _use_milestones` in the gate
- The artifact verification gate IS: `if _is_prd_mode and not _use_milestones:` — milestones don't need root-level REQUIREMENTS.md (Issue 2 resolved)

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL V10 tests must pass
- ALL existing tests must pass (except 2 pre-existing known failures in test_mcp_servers.py)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green
- Expected: V10 baseline + ~30-40 new tests

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# v10.1 Runtime Guarantees — Implementation Report

## V10 Verification
- All 9 V10 deliverables: VERIFIED / [list missing]
- V10 test baseline: XXXX passing

## Implementation Summary
- Modified: cli.py (artifact verification gate ~40 lines + convergence recovery ~8 lines)
- Modified: display.py (1 new type_hints entry)
- New constant: ARTIFACT_RECOVERY_PROMPT (~35 lines)
- New function: _run_artifact_recovery() (~30 lines)
- New tests: tests/test_v10_1_runtime_guarantees.py (~35 tests)

## Deliverable Coverage
| Deliverable | Files Modified | Gate Condition | Mechanism |
|-------------|---------------|----------------|-----------|
| 10. Artifact Verification | cli.py | `_is_prd_mode and not _use_milestones` AND NOT req_path.is_file() | Sub-orchestrator recovery agent (ClaudeSDKClient pattern) |
| 11. Mandatory Convergence | cli.py | health="unknown" AND _is_prd_mode | needs_recovery=True → existing _run_review_only() |

## Flow Guarantee
| Scenario | Before v10.1 | After v10.1 |
|----------|-------------|------------|
| Orchestrator generates REQUIREMENTS.md | Convergence works | Convergence works (unchanged) |
| Orchestrator skips REQUIREMENTS.md | health="unknown", 0 cycles, no recovery | Artifact recovery creates it, convergence fires |
| Artifact recovery fails | N/A | health="unknown", Deliverable 11 forces review fleet |
| REQUIREMENTS.md has no checkboxes | health="unknown", no recovery | Deliverable 11 forces review fleet |

## Test Results
- New tests written: ~35
- All passing: X/X
- V10 regressions: 0
- Total suite: XXXX passing

## Production Test Impact (projected)
| Checkpoint Category | v9 (before) | v10 (prompt) | v10.1 (runtime) |
|--------------------|-------------|-------------|----------------|
| ✅ PASS | 15/42 | 35-38/42 | 40/42 |
| ❌ FAIL | 16/42 | 2-5/42 | 0/42 |
| ⚠️ PARTIAL | 4/42 | 1-2/42 | 0/42 |
| ⏭️ N/A | 5/42 | 1/42 | 2/42 (RC-1 milestone-only, cost tracking infra) |
| 🔍 INCONCLUSIVE | 2/42 | 0/42 | 0/42 |

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **V10 FIRST** — Do NOT start implementation until Phase 0 confirms all 9 V10 deliverables are in place. If any are missing, STOP and report.

2. **ONE FILE** — Both deliverables edit cli.py. One impl agent is the correct team size. No parallel implementation needed.

3. **FOLLOW EXISTING PATTERNS** — `_run_artifact_recovery()` must exactly follow the `_run_prd_reconciliation()` pattern: same parameter style, same `_build_options()` call, same `_run_agent_session()` call, same cost return.

4. **READ BEFORE YOU WRITE** — Read cli.py around your insertion point (20 lines before and after). Verify indentation. Verify variable availability. cli.py is 5000+ lines — one wrong indent breaks everything.

5. **CRASH ISOLATION** — Both new code blocks must be wrapped in try/except. Artifact recovery failure must NOT prevent convergence check. Convergence recovery failure must NOT prevent post-orchestration scans.

6. **GATE CORRECTLY** — Artifact verification: `_is_prd_mode and not _use_milestones`. Convergence force: `_is_prd_mode`. Do NOT trigger these in non-PRD mode or milestone mode where they're unnecessary.

7. **BACKWARD COMPATIBLE** — No new config fields. No new CLI flags. Both deliverables are gated on existing runtime flags. A non-PRD project sees zero behavioral change.

8. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong.

9. **DON'T FORGET display.py** — The test-engineer should add "artifact_recovery" to the `type_hints` dict in display.py since impl-runtime only touches cli.py.

10. **VERIFY THE FLOW** — After implementation, trace the full path: orchestrator → artifact recovery → contract recovery → convergence check → review recovery. Every `_is_prd_mode` path must terminate at review fleet deployment.
