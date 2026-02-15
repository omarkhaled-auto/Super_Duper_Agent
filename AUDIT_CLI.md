# CLI Pipeline Engine Audit Report

**File**: `src/agent_team/cli.py` (6388 lines)
**Auditor**: Code Readiness Auditor
**Date**: 2026-02-15
**Scope**: Exhaustive audit for 4 Super Agent Team PRD runs (Build 1, Build 2, Build 3, Run 4)

---

## 1. Pipeline Flow Diagram

```
main() [L3917]
  |
  +-- load_dotenv() [L3921-3925]
  +-- Reset globals [L3928-3932]
  +-- Subcommand check (init/status/resume/clean/guide) [L3936-3946]
  +-- Signal handling [L3949]
  +-- Load config -> (config, user_overrides) [L3962-3969]
  +-- Detect Gemini CLI [L3988-3997]
  +-- Resolve CWD [L4009]
  +-- Validate PRD file [L4015-4017]
  +-- Extract design URLs from PRD [L4020-4029]
  +-- Detect auth backend [L4037-4043]
  |
  +-- Phase 0: Interview [L4113-4168]
  +-- Phase 0.25: Constraint Extraction [L4175-4183]
  +-- Phase 0.5: Codebase Map [L4216-4236]
  +-- Phase 0.6: Design Reference Extraction [L4243-4460]
  +-- Phase 0.75: Contract Loading + Scheduling [L4467-4522]
  |
  +-- Pre-orchestration review cycle capture [L4528-4533]
  +-- InterventionQueue start [L4538-4561]
  |
  +-- TRY BLOCK [L4540]:
  |   +-- Determine mode (interactive vs single-shot) [L4547-4549]
  |   +-- Auto-override depth [L4552-4554]
  |   |
  |   +-- IF interactive:
  |   |     _run_interactive() [L4573-4589]
  |   |
  |   +-- ELSE (single-shot):
  |       +-- detect_depth() [L4596-4600]
  |       +-- apply_depth_quality_gating() [L4611]
  |       |
  |       +-- IF _use_milestones:
  |       |     _run_prd_milestones() [L4623-4635]
  |       |       +-- Phase 1: Decomposition (MASTER_PLAN.md) [L940-1052]
  |       |       +-- Phase 1.5: Tech Research [L1088-1119]
  |       |       +-- Phase 2: Execution Loop [L1143-1714]
  |       |            PER MILESTONE:
  |       |              +-- Build context [L1220-1291]
  |       |              +-- Execute via ClaudeSDKClient [L1302-1346]
  |       |              +-- Review recovery loop [L1372-1432]
  |       |              +-- Handoff documentation [L1434-1513]
  |       |              +-- Wiring completeness check [L1516-1535]
  |       |              +-- Post-milestone mock scan [L1538-1563]
  |       |              +-- Post-milestone UI scan [L1565-1591]
  |       |              +-- Health gate [L1593-1609]
  |       |              +-- Wiring verification [L1612-1640]
  |       |              +-- Integration verification [L1643-1664]
  |       |              +-- Mark COMPLETE [L1666-1688]
  |       |       +-- Aggregate health [L1708-1714]
  |       |
  |       +-- ELSE (standard):
  |             Tech research (standard mode) [L4647-4665]
  |             _run_single() [L4667-4685]
  |
  +-- EXCEPT (orchestration error) [L4689-4697]
  |
  +-- FINALLY:
  |     intervention.stop() [L4726]
  |
  +-- POST-ORCHESTRATION SCANS:
  |   +-- TASKS.md diagnostic [L4731-4762]
  |   +-- Artifact recovery (PRD non-milestone) [L4767-4807]
  |   +-- Contract health check [L4812-4860]
  |   +-- Convergence health check [L4865-4976]
  |   +-- GATE 5 enforcement [L5039-5051]
  |   +-- Review recovery pass [L5053-5116]
  |   +-- Compute scan scope [L5121-5134]
  |   +-- Mock data scan [L5141-5182]
  |   +-- UI compliance scan [L5189-5230]
  |   +-- Deployment integrity scan [L5236-5278]
  |   +-- Asset integrity scan [L5281-5323]
  |   +-- PRD reconciliation [L5326-5365]
  |   +-- DB dual ORM scan [L5372-5419]
  |   +-- DB default value scan [L5422-5469]
  |   +-- DB relationship scan [L5472-5519]
  |   +-- API contract scan [L5524-5570]
  |   +-- Silent data loss scan [L5575-5618]
  |   +-- Endpoint XREF scan [L5623-5674]
  |   +-- E2E Testing Phase [L5679-5919]
  |   +-- E2E Quality Scan [L5924-5942]
  |   +-- Browser MCP Testing [L5947-6275]
  |   +-- Recovery report [L6278-6279]
  |
  +-- Verification [L6305-6378]
  +-- Clear STATE.json [L6387-6388]
```

---

## 2. Audit Findings

### 2.1 Pipeline Phase Ordering

#### FINDING-01 [LOW] — `_is_prd_mode` used outside defining scope
**Lines**: 4767, 5008
**Issue**: `_is_prd_mode` is defined at line 4608 inside the `try` block (else branch of interactive check). If the `try` block raises before line 4608, `_is_prd_mode` is undefined when referenced at L4767 and L5008 in post-orchestration. However, the variable is defined at L4608 which is before the `asyncio.run()` calls, so it will always be set before the `except` at L4689. If the code entered the `interactive` branch (L4572), `_is_prd_mode` is NEVER defined.
**Severity**: **HIGH**
**Risk**: In interactive mode, post-orchestration code at L4767 (`if _is_prd_mode and not _use_milestones:`) will raise `NameError`. The interactive path at L4573 returns directly to `run_cost`, but `_is_prd_mode` is never set.
**Fix**: Initialize `_is_prd_mode = False` alongside `_use_milestones = False` at L4568.

#### FINDING-02 [LOW] — Interactive mode skips ALL post-orchestration scans
**Lines**: 4573-4589, 4728+
**Issue**: When `interactive=True`, `_run_interactive()` is called and returns. All post-orchestration scans (mock, UI, deployment, E2E, browser) still execute. However, many use `_use_milestones` (always False for interactive) and `_is_prd_mode` (undefined — see FINDING-01). The interactive path should either skip post-orchestration entirely or define these variables.
**Severity**: **MEDIUM** (post-orchestration will crash for interactive+PRD mode)

#### FINDING-03 [INFO] — Phase ordering is correct for PRD milestone mode
The ordering is: config → interview → constraints → codebase_map → design_extraction → contract_loading → orchestration (decomposition → tech_research → execution_loop) → post-orchestration scans → verification. This is correct and well-structured.

#### FINDING-04 [LOW] — No phase can be skipped unintentionally for PRD mode
Each phase is properly gated by config booleans. Resume logic correctly skips completed phases via `_current_state.completed_phases` and `milestone_progress.json`.

---

### 2.2 Error Handling & Crash Isolation

#### FINDING-05 [INFO] — Post-orchestration scans have individual try/except blocks
Every scan (mock, UI, deployment, asset, PRD reconciliation, DB scans, API contract, SDL, XREF, E2E, browser) is wrapped in its own `try/except Exception` with `print_warning`. This is excellent crash isolation — one scan failure does not block others.

#### FINDING-06 [MEDIUM] — `_run_review_only` at L3721 lacks try/except
**Lines**: 3721-3725
**Issue**: `_run_review_only` creates a `ClaudeSDKClient` directly without a try/except around the `async with`. If the SDK raises during session creation (e.g., network error), the exception propagates up. The callers (L5063, L1394) DO have try/except, but the inner function should be defensive.
**Severity**: MEDIUM — The caller catches it, so crash isolation is maintained. But traceback logging is missing inside the function.

#### FINDING-07 [LOW] — `_run_contract_generation` uses `asyncio.run()` internally
**Lines**: 3768-3779
**Issue**: `_run_contract_generation` defines an inner `async def _recovery()` and calls `asyncio.run(_recovery())`. This is called from `main()` which is synchronous at that point (after the orchestration `try` block). This works because the event loop from orchestration has ended. However, if ever called from an async context, it would crash.
**Severity**: LOW — Currently safe since it's called from synchronous post-orchestration code.

#### FINDING-08 [INFO] — `traceback.format_exc()` is used consistently in all E2E and browser functions (L2311, 2351, 2413, 2453, 2515, 2590, 2638, 2749, 2864, 2942, 3089, 5917, 6249). This is good.

---

### 2.3 Budget Management

#### FINDING-09 [MEDIUM] — Budget check only fires AFTER a phase completes
**Lines**: 357-364
**Issue**: `_process_response()` checks budget at L358-364, but only after the full response is streamed. There is no pre-check before starting expensive operations. A single milestone can consume the entire budget before the check fires.
**Severity**: MEDIUM — For Super Agent Team PRDs with 7-8 milestones, a single milestone could use $50+ before the budget warning appears.
**Mitigation**: The budget check is a WARNING, not a hard stop. The system warns at 80% and reports at 100% but never kills the session. This is by design (documented in v7.0 audit as non-blocking).

#### FINDING-10 [LOW] — Budget only checked when `_backend == "api"`
**Lines**: 358
**Issue**: Budget tracking is skipped entirely for `cli` backend. This is correct since CLI/subscription mode has no per-token billing.

#### FINDING-11 [LOW] — Phase costs are tracked per-function but not aggregated globally
Each async function creates its own `phase_costs: dict[str, float] = {}`. Costs are tracked back to `total_cost` via return values. The `_current_state.total_cost` is updated at L4701 and incrementally in post-orchestration. This is correct.

---

### 2.4 State Persistence & Resume

#### FINDING-12 [INFO] — RunState is saved after each milestone
**Lines**: 1215-1218, 1342-1345, 1673-1676
State is saved after milestone status changes (IN_PROGRESS, FAILED, COMPLETE). This enables resume from the last completed milestone.

#### FINDING-13 [MEDIUM] — No state save after individual post-orchestration scans
**Lines**: 5141-6275
**Issue**: After each post-orchestration scan+fix, the state is not saved. If the process crashes during scan #7 (out of 12), scans 1-6 will re-run on resume. The scan results themselves (violations) are not persisted in state.
**Severity**: MEDIUM — Post-orchestration scans are relatively cheap compared to milestone execution, but re-running all scans wastes time and cost.
**Fix**: Save state after each scan block (mock, UI, deployment, etc.) and add scan completion tracking to `completed_phases`.

#### FINDING-14 [LOW] — `milestone_progress.json` is deleted on successful resume
**Line**: 1160
The progress file is properly cleaned up after loading. This prevents stale progress from interfering with fresh runs.

#### FINDING-15 [INFO] — E2E phases track resume correctly
**Lines**: 5712-5718
Backend and frontend E2E phases check `_current_state.completed_phases` for "e2e_backend" / "e2e_frontend" before running. Phases are only marked complete when health is "passed" or "partial" (L5768, L5846). Failed phases re-run on resume.

---

### 2.5 Milestone Execution Loop

#### FINDING-16 [INFO] — `_run_prd_milestones()` handles parallel milestones correctly
**Lines**: 1178, 1189
`plan.get_ready_milestones()` returns all milestones whose dependencies are satisfied. The `for milestone in ready:` loop processes them sequentially within each iteration, but the outer `while` loop allows new milestones to become ready after each iteration. This means M1+M2 (independent) are processed in two iterations of the inner loop within one outer iteration — they execute sequentially, NOT in parallel.

#### FINDING-17 [MEDIUM] — No true parallel milestone execution
**Lines**: 1189
**Issue**: Even when milestones M1 and M2 have no dependencies (e.g., Build 2 M1+M2, Build 3 M2+M3), they execute sequentially in the `for milestone in ready:` loop. True parallel execution would require `asyncio.gather()` or similar.
**Severity**: MEDIUM — This increases total execution time but does not affect correctness. For the Super Agent Team PRDs, this means Build 2's independent milestones take 2x the time they could take.
**Note**: This is a known design decision — parallel milestone execution would complicate state management, error handling, and intervention draining.

#### FINDING-18 [INFO] — Convergence check logic is sound
**Lines**: 1366-1432
The health gate checks `convergence_ratio < recovery_threshold`. Recovery loop breaks early if health becomes "healthy" or "degraded above threshold". The `for...else` pattern at L1426 correctly warns when all retries are exhausted.

#### FINDING-19 [LOW] — Infinite loop protection is adequate
**Line**: 1165
`max_iterations = len(plan.milestones) + 3` prevents infinite loops. The `+3` headroom accounts for retry scenarios. The state-based guard at L1171-1176 provides a second safety net.

#### FINDING-20 [INFO] — 8-milestone handling (Build 1)
Build 1 has 8 milestones. The loop can handle any count. The `max_milestones_warning` at L1075 warns if count exceeds the threshold but does not block execution. 8 milestones is within normal bounds.

#### FINDING-21 [INFO] — Milestone never-converges scenario
If a milestone fails health gate after all recovery retries, it is marked FAILED at L1600 and the loop `continue`s. The `ready` list in the next iteration will skip milestones depending on the failed one (they have unsatisfied deps). If no milestones are ready AND health is "failed", the loop breaks at L1183-1185.

---

### 2.6 Post-Orchestration Scan Pipeline

#### FINDING-22 [INFO] — Scan order is correct
The order is: mock → UI → deployment → asset → PRD_reconciliation → DB_dual_orm → DB_defaults → DB_relationships → API_contract → SDL → XREF → E2E → E2E_quality → Browser. This is correct:
- Static scans (mock, UI, deployment, asset) run before expensive LLM-based checks (PRD recon)
- Database scans run as a group
- API contract + SDL + XREF run after DB scans (may depend on fixed DB state)
- E2E runs after all static scans (ensures code is clean before testing)
- Browser testing runs last (requires running app)

#### FINDING-23 [INFO] — Scans are properly gated by config
Each scan checks its config boolean:
- `config.post_orchestration_scans.mock_data_scan` or `config.milestone.mock_data_scan`
- `config.post_orchestration_scans.ui_compliance_scan` or `config.milestone.ui_compliance_scan`
- `config.integrity_scans.deployment_scan`
- `config.integrity_scans.asset_scan`
- `config.integrity_scans.prd_reconciliation`
- `config.database_scans.dual_orm_scan`
- `config.database_scans.default_value_scan`
- `config.database_scans.relationship_scan`
- `config.post_orchestration_scans.api_contract_scan`
- `config.post_orchestration_scans.silent_data_loss_scan`
- `config.post_orchestration_scans.endpoint_xref_scan`
- `config.e2e_testing.enabled`
- `config.browser_testing.enabled`

#### FINDING-24 [INFO] — Fix loop pattern is consistent
All scans use the same pattern: `for _fix_pass in range(max(1, _max_passes))` with scan → fix → re-scan. The `max_scan_fix_passes` config controls how many rounds. When `_max_passes == 0`, it's scan-only (no fix). This is correct.

#### FINDING-25 [LOW] — Scan results are NOT aggregated into a summary object
**Issue**: Each scan's violations are logged individually but never collected into a unified post-orchestration report object. The `recovery_types` list tracks WHICH scans triggered recovery but not HOW MANY violations remain.
**Severity**: LOW — The individual logs are sufficient for debugging. A summary object would improve reporting.

---

### 2.7 Recovery Mechanisms

#### FINDING-26 [INFO] — Recovery types tracked
`recovery_types: list[str]` at L4731 tracks all recovery passes. This list is displayed by `print_recovery_report()` at L6279.

#### FINDING-27 [INFO] — `_run_review_only()` is correctly parameterized
**Lines**: 3619-3725
Accepts `requirements_path` (for milestone-scoped reviews) and `depth`. Uses `review_cycles == 0` to distinguish zero-cycle from partial-review failures. The prompt uses `[PHASE: REVIEW VERIFICATION]` tag per v13 de-escalation fix.

#### FINDING-28 [INFO] — `_run_integrity_fix()` supports all 5 scan types
**Lines**: 2947-3091
Supports "deployment", "asset", "database_dual_orm", "database_defaults", "database_relationships" via separate prompt branches. The `else` (default) branch handles "asset" type. This is correct per v5.0 review fix C1.

#### FINDING-29 [INFO] — `max_scan_fix_passes` config controls iteration
All post-orchestration fix loops respect `config.post_orchestration_scans.max_scan_fix_passes`. Default is 1 (scan-only on 0, scan+fix on 1+).

---

### 2.8 Concurrency & Async

#### FINDING-30 [HIGH] — `asyncio.run()` nesting risk throughout post-orchestration
**Lines**: 4573, 4623, 4667, 4779, 5063, 5159, 5207, 5254, 5299, 5343, 5390, 5440, 5490, 5545, 5595, 5648, 5725, 5740, 5749, 5804, 5819, 5828, 6019, 6102, 6129, 6167, 6182, 6189, 6341
**Issue**: `main()` is synchronous. It calls `asyncio.run()` for orchestration, then calls `asyncio.run()` again for EACH post-orchestration scan fix. Each `asyncio.run()` creates and destroys an event loop. This works in CPython but:
1. If any code retains a reference to the previous event loop, it will crash
2. Each `asyncio.run()` call has overhead (loop creation/teardown)
3. Multiple sequential `asyncio.run()` calls in the same function is an anti-pattern

**Severity**: **HIGH** (architectural) — This is the pre-existing asyncio.run() nesting risk documented in v7.0 and v8.0 audits. It works in practice but is fragile.
**Mitigation**: The code carefully avoids holding event loop references across `asyncio.run()` boundaries. Each call is a fresh ClaudeSDKClient session. This has been running successfully in production.

#### FINDING-31 [LOW] — No race conditions in state management
`_current_state` is a module-level global accessed from the main thread only. The InterventionQueue uses a thread-safe `queue.Queue`. Signal handler writes are protected by the GIL. No race conditions exist.

#### FINDING-32 [LOW] — subprocess calls are properly managed
The browser testing cleanup at L6253-6275 uses `subprocess.run()` with `timeout=10` and `capture_output=True`. This is correct.

---

### 2.9 Super Agent Team Readiness

#### FINDING-33 [INFO] — Can handle 8 milestones (Build 1)
The milestone loop has no milestone count limit. `max_iterations = len(milestones) + 3 = 11` provides adequate headroom. Build 1's 8 milestones will execute sequentially with review recovery per milestone.

#### FINDING-34 [INFO] — Can handle 7 milestones with parallel deps (Build 3)
Build 3 has milestones with parallel deps (M2+M3 depend on M1 only). The `get_ready_milestones()` will return both M2 and M3 once M1 completes. They execute sequentially (FINDING-17) but correctly.

#### FINDING-35 [LOW] — Large milestones may hit max_turns limit
**Issue**: Build 1 milestones are complex (60+ requirements per milestone). If a single milestone has too many requirements, the orchestrator may hit `max_turns` (default 500) before completing all tasks. The convergence check would then report partial progress, and review recovery would attempt to finish.
**Severity**: LOW — The review recovery loop (up to `review_recovery_retries`) provides a safety net. But if `max_turns` is hit repeatedly, the milestone will eventually fail the health gate.

#### FINDING-36 [INFO] — Budget adequate for 4 PRD runs
Build 1-3 are independent builds in separate project directories. Run 4 wires them together. The budget management (`max_budget_usd`) is per-run, not cumulative across runs. Each run tracks its own cost.

#### FINDING-37 [MEDIUM] — Milestone mode has no cost-per-milestone tracking
**Issue**: Inside `_run_prd_milestones()`, `total_cost` accumulates across all milestones, but there is no per-milestone cost breakdown. When a build with 8 milestones costs $100+, it's impossible to identify which milestone was most expensive.
**Severity**: MEDIUM — Debugging cost overruns requires manual log analysis.
**Fix**: Add per-milestone cost tracking to RunState and display in the milestone completion message.

#### FINDING-38 [LOW] — `_is_prd_mode` detection may miss Build 2 scenario
**Line**: 4608
`_is_prd_mode = bool(args.prd) or interview_scope == "COMPLEX"`. Build 2 is an upgrade to an existing codebase. If the user passes `--prd BUILD2_PRD.md`, `args.prd` is set and `_is_prd_mode` is True. This is correct.

---

## 3. Summary of Findings by Severity

| Severity | Count | Finding IDs |
|----------|-------|-------------|
| **CRITICAL** | 0 | — |
| **HIGH** | 2 | FINDING-01 (NameError risk), FINDING-30 (asyncio.run nesting) |
| **MEDIUM** | 5 | FINDING-02 (interactive+PRD crash), FINDING-06 (review_only no try/except), FINDING-09 (budget post-check), FINDING-13 (no state save after scans), FINDING-17 (no parallel milestones), FINDING-37 (no per-milestone cost) |
| **LOW** | 10 | FINDING-04, FINDING-07, FINDING-10, FINDING-11, FINDING-14, FINDING-19, FINDING-25, FINDING-31, FINDING-35, FINDING-38 |
| **INFO** | 13 | FINDING-03, FINDING-05, FINDING-08, FINDING-12, FINDING-15, FINDING-16, FINDING-18, FINDING-20, FINDING-21, FINDING-22, FINDING-23, FINDING-24, FINDING-26, FINDING-27, FINDING-28, FINDING-29, FINDING-33, FINDING-34, FINDING-36 |

---

## 4. Recommendations

### Must-Fix Before Super Agent Team Runs

1. **FINDING-01** [HIGH]: Initialize `_is_prd_mode = False` at L4568, alongside `_use_milestones = False`. This prevents `NameError` in interactive mode when post-orchestration code references it.

### Should-Fix (Low Risk but Improve Reliability)

2. **FINDING-13** [MEDIUM]: Save `_current_state` after each post-orchestration scan block. Add scan completion tracking (e.g., `_current_state.completed_phases.append("scan_mock_data")`) to enable resume mid-scan.

3. **FINDING-37** [MEDIUM]: Add per-milestone cost tracking. In the milestone loop, record `ms_cost` to `_current_state.milestone_progress[milestone.id]["cost"]` and display it.

### Accepted Risk (Known, Won't Fix)

4. **FINDING-30** [HIGH — Accepted]: The `asyncio.run()` nesting pattern is a known architectural constraint documented in v7.0 and v8.0 audits. Refactoring `main()` to be fully async would be a major architectural change with high regression risk. The current pattern works reliably in production.

5. **FINDING-17** [MEDIUM — Accepted]: Sequential milestone execution is a deliberate design choice. Parallel execution would complicate state management, error handling, and intervention draining. The performance cost is acceptable for correctness.

---

## 5. Overall Readiness Assessment

**VERDICT: READY** with one HIGH fix required (FINDING-01).

The pipeline engine is well-structured, has comprehensive crash isolation (individual try/except per scan), correct phase ordering, adequate resume support, and handles large PRDs (8+ milestones, 60+ requirements) through the convergence loop.

The one HIGH finding (FINDING-01, `_is_prd_mode` undefined in interactive mode) is a real bug but only triggers when interactive mode is used with post-orchestration scans — which is an unusual combination for PRD builds. For the 4 Super Agent Team runs (all PRD-mode, non-interactive), this bug will NOT trigger.

The asyncio.run() nesting (FINDING-30) is a known architectural constraint that has been running successfully since v7.0. It should be monitored but not changed before the Super Agent Team runs.
