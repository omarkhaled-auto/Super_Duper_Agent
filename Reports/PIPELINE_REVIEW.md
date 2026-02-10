# PIPELINE REVIEW

> Production Readiness Audit — CLI Pipeline Execution Review
> Reviewer: REVIEWER-PIPELINE
> Date: 2026-02-10
> Scope: `src/agent_team/cli.py` — post-orchestration pipeline, fix functions, state management
> Architecture Inventory: `.agent-team/ARCHITECTURE_INVENTORY.md` used as checklist

---

## Summary

Reviewed `cli.py` (~4440 lines) line-by-line focusing on:
1. `load_config` / `apply_depth_quality_gating` call sites
2. Post-orchestration execution order (Steps 0-9)
3. Fix functions (5 types)
4. State management
5. Tracking document integration

**Overall Assessment: MINOR FIXES NEEDED**

Found **1 HIGH** bug, **2 MEDIUM** bugs, and **3 LOW** issues. No CRITICAL issues. The pipeline structure is solid with proper crash isolation and config gating throughout.

---

## Findings

### F-1: Missing `json` import in `main()` scope [HIGH]

**File:** `cli.py`
**Lines:** 3579-3588
**Severity:** HIGH

At line 3581, `json.load(f)` is called to validate CONTRACTS.json after recovery. At line 3585, `json.JSONDecodeError` is caught. However, `json` is NOT imported at the module level (line 1-22) or anywhere in `main()`'s local scope.

`json` is only imported locally inside `_run_prd_milestones()` (line 887) and `_save_milestone_progress()` (line 2012). Python's scoping rules mean those local imports only bind `json` in their respective function scopes, not in `main()`.

**Impact:** When the contract recovery path at line 3563-3588 executes, `json.load(f)` raises `NameError: name 'json' is not defined`. This is caught by the outer `except Exception as exc:` at line 3589, which prints "Contract generation recovery failed: name 'json' is not defined". The actual validation of CONTRACTS.json is silently skipped — a corrupted JSON file would be reported as a recovery failure rather than a validation failure.

**Suggested Fix:**
Add `import json` at the module level (line 9-20 area), or add a local `import json` inside the verification block at line 3578.

---

### F-2: `depth` variable undefined in interactive mode [MEDIUM]

**File:** `cli.py`
**Lines:** 3370-3409 (definition), 3793-4239 (usage)
**Severity:** MEDIUM

The variable `depth` is set at line 3397 or 3400 inside the `else:` branch (non-interactive path). In the interactive path (line 3373-3390), `depth` is NEVER assigned in `main()`'s local scope — it is only passed as `depth_override` into `_run_interactive()`.

Post-orchestration code references `depth` at 26 locations:
- Line 3793: `depth in ("quick", "standard")` — scan scope computation
- Line 3800: `depth == "quick"` — scope mode selection
- Lines 3829, 3861, 3893, 3922, 3933, 3955, 3999, 4034, 4069, 4136, 4153, 4160, 4215, 4232, 4239 — all fix function calls

**Impact:** In interactive mode, all post-orchestration code that references `depth` raises `NameError`. Each is individually caught by crash-isolation `try/except` handlers:
- Scan scope computation (line 3795): caught at line 3803, falls back to full scan
- Fix function calls: caught by their respective inner `try/except`, logged as warnings
- PRD recon quality gate (line 3933): caught by outer `try/except` at line 3970

The net effect is that in interactive mode:
1. Scan scope is always "full" (acceptable fallback)
2. All fix recovery passes silently fail (significant — violations are detected but never fixed)
3. PRD reconciliation quality gate is bypassed

**Suggested Fix:**
Initialize `depth` before the `if interactive:` branch:
```python
depth = depth_override or "standard"  # Default before routing
```
Or resolve it from `_current_state.depth` after the orchestration call.

---

### F-3: Fix cycle log `cycle_number` always hardcoded to 1 in `_run_integrity_fix` [MEDIUM]

**File:** `cli.py`
**Lines:** 1978
**Severity:** MEDIUM

In `_run_integrity_fix()` (line 1976-1984), `build_fix_cycle_entry()` is called with `cycle_number=1` hardcoded. The same hardcoding exists in `_run_mock_data_fix()` (line 1438), `_run_ui_compliance_fix()` (line 1521), `_run_e2e_fix()` (line 1662), and `_run_review_only()` (line 2601).

However, the E2E fix loop calls `_run_e2e_fix()` multiple times in a retry loop (lines 4147-4163, 4226-4244), each time recording `cycle_number=1`. The fix cycle log would show multiple entries all claiming to be "cycle 1".

**Impact:** Fix cycle log entries have incorrect cycle numbers, reducing their diagnostic value. Not a functional issue since the fix cycle log is purely informational, but it creates misleading tracking data.

**Suggested Fix:**
Pass the current retry count to the fix functions and forward it to `build_fix_cycle_entry()`.

---

### F-4: `_run_integrity_fix` fallback branch uses asset prompt for unknown scan types [LOW]

**File:** `cli.py`
**Lines:** 1954-1967
**Severity:** LOW

The `else` branch at line 1954 in `_run_integrity_fix()` creates an "ASSET INTEGRITY FIX" prompt for any unrecognized `scan_type`. While all 5 known scan types are covered by `if/elif` branches (deployment, database_dual_orm, database_defaults, database_relationships), and the `else` catches `asset`, this means:
1. Any future scan type that forgets to add its own branch would silently get the asset fix prompt.
2. The `else` branch is implicitly "asset" but the code comment/docstring at line 1861 explicitly lists "asset" as a valid value.

**Impact:** Very low — all current callers pass one of the 5 documented values. But defensively, the `else` should be `elif scan_type == "asset"` with an `else: raise ValueError(...)` or at least a warning log.

---

### F-5: `_run_review_only` not wrapped in try/except internally [LOW]

**File:** `cli.py`
**Lines:** 2626-2630
**Severity:** LOW

The `async with ClaudeSDKClient(options=options) as client:` block at line 2626 in `_run_review_only()` is NOT wrapped in a try/except, unlike all other fix functions (`_run_mock_data_fix`, `_run_ui_compliance_fix`, `_run_integrity_fix`, `_run_e2e_fix`).

If the SDK client raises during review recovery, the exception propagates. The caller at line 3754 wraps it in `asyncio.run()`, and the `except Exception` at line 3785 catches it.

**Impact:** Functionally safe since the caller catches the exception. But it's inconsistent with the pattern used by all other fix functions (which log `traceback.format_exc()` before re-raising/swallowing). A failure here would produce a less informative warning message.

---

### F-6: `e2e_testing` phase completion unconditionally appended [LOW]

**File:** `cli.py`
**Line:** 4289
**Severity:** LOW

At line 4289: `_current_state.completed_phases.append("e2e_testing")` is executed unconditionally (inside the `config.e2e_testing.enabled` gate) regardless of whether any tests actually ran or whether the health is "failed". This contrasts with the more granular `e2e_backend` and `e2e_frontend` which are only appended when health is "passed" or "partial" (lines 4175, 4253).

**Impact:** On resume, the system would skip the E2E testing phase entirely even if it had failed. For `e2e_backend` and `e2e_frontend`, failed phases correctly re-run on resume. But the outer `e2e_testing` phase marker prevents the entire section from re-executing.

However, looking at `_build_resume_context()` (line 2325) — resume logic uses `completed_phases` to build context strings, not to gate re-execution of post-orchestration steps. The post-orchestration scans are always re-run on resume regardless of completed_phases (they check `config.e2e_testing.enabled`, not `"e2e_testing" in completed_phases`). So actual impact is minimal — the `e2e_testing` phase marker is used for state display, not for gating.

The `backend_already_done` / `frontend_already_done` checks (lines 4119-4126) ARE properly gated by `"e2e_backend"` / `"e2e_frontend"` phase markers, and those ARE correctly conditioned on health.

---

## Execution Order Verification

### load_config Call Sites

| Location | Line | Unpacking | Correct? |
|----------|------|-----------|----------|
| `main()` | 2868 | `config, user_overrides = load_config(...)` | YES |

Only ONE call site in cli.py. Correct tuple unpacking.

### apply_depth_quality_gating Call Sites

| Location | Line | user_overrides param | Correct? |
|----------|------|---------------------|----------|
| `_run_interactive()` | 389 | `user_overrides` (function param, default `None`) | YES |
| `main()` else branch | 3409 | `user_overrides` (from `load_config` unpacking) | YES |

Both sites pass `user_overrides`. Correct.

### Post-Orchestration Execution Order Diagram

```
main() line 3503
  |
  +-- Step 0: Task Status Diagnostic (line 3503-3537)
  |     Gate: config.scheduler.enabled
  |     Crash isolation: try/except
  |
  +-- Step 1: Contract Health Check (line 3541-3590)
  |     Gate: config.verification.enabled
  |     Recovery: _run_contract_generation() -> asyncio.run()
  |     Post-recovery: JSON validation [BUG: json not imported]
  |     Crash isolation: try/except (outer)
  |
  +-- Step 2: Convergence Health Check (line 3592-3786)
  |     Branches: milestones vs standard mode
  |     Recovery: asyncio.run(_run_review_only())
  |     Post-recovery: re-check health, verify cycle increment
  |     Crash isolation: try/except
  |
  +-- Step 3: Scan Scope Computation (line 3788-3804)
  |     Gate: config.depth.scan_scope_mode
  |     Modes: "changed" | "auto" + quick/standard depth
  |     Crash isolation: try/except pass
  |     [BUG: depth undefined in interactive mode]
  |
  +-- Step 4: Mock Data Scan (line 3807-3836)
  |     Gate: not _use_milestones AND (post_orch.mock OR milestone.mock)
  |     Scan: run_mock_data_scan(scope=scan_scope)
  |     Fix: _run_mock_data_fix() with fix cycle log
  |     Crash isolation: nested try/except
  |
  +-- Step 5: UI Compliance Scan (line 3838-3868)
  |     Gate: not _use_milestones AND (post_orch.ui OR milestone.ui)
  |     Scan: run_ui_compliance_scan(scope=scan_scope)
  |     Fix: _run_ui_compliance_fix() with fix cycle log
  |     Crash isolation: nested try/except
  |
  +-- Step 6: Deployment Integrity Scan (line 3873-3900)
  |     Gate: config.integrity_scans.deployment_scan
  |     Scan: run_deployment_scan() — NO scope (always full)
  |     Fix: _run_integrity_fix(scan_type="deployment")
  |     Crash isolation: nested try/except
  |
  +-- Step 7: Asset Integrity Scan (line 3902-3929)
  |     Gate: config.integrity_scans.asset_scan
  |     Scan: run_asset_scan(scope=scan_scope)
  |     Fix: _run_integrity_fix(scan_type="asset")
  |     Crash isolation: nested try/except
  |
  +-- Step 8: PRD Reconciliation (line 3931-3971)
  |     Gate: config.integrity_scans.prd_reconciliation
  |     Quality gate (thorough): file > 500B + REQ-\d{3} pattern
  |     Quality gate crash isolation: try/except OSError
  |     Execution: asyncio.run(_run_prd_reconciliation())
  |     Parse: parse_prd_reconciliation()
  |     PRD violations: non-blocking warnings (recovery_types only)
  |     Crash isolation: try/except
  |
  +-- Step 9: Database Dual ORM Scan (line 3977-4010)
  |     Gate: config.database_scans.dual_orm_scan
  |     Scan: run_dual_orm_scan(scope=scan_scope)
  |     Fix: _run_integrity_fix(scan_type="database_dual_orm")
  |     Crash isolation: nested try/except + traceback
  |
  +-- Step 10: Database Default Value Scan (line 4012-4045)
  |     Gate: config.database_scans.default_value_scan
  |     Scan: run_default_value_scan(scope=scan_scope)
  |     Fix: _run_integrity_fix(scan_type="database_defaults")
  |     Crash isolation: nested try/except + traceback
  |
  +-- Step 11: Database Relationship Scan (line 4047-4080)
  |     Gate: config.database_scans.relationship_scan
  |     Scan: run_relationship_scan(scope=scan_scope)
  |     Fix: _run_integrity_fix(scan_type="database_relationships")
  |     Crash isolation: nested try/except + traceback
  |
  +-- Step 12: E2E Testing Phase (line 4082-4326)
  |     Gate: config.e2e_testing.enabled
  |     Pre: Generate coverage matrix (config-gated)
  |     Resume: backend_already_done / frontend_already_done checks
  |     Backend: _run_backend_e2e_tests() + fix loop
  |       Fix guard: health not in ("passed", "skipped", "unknown")
  |       Phase complete: only when health in ("passed", "partial")
  |     Frontend gate: 70% backend pass rate
  |     Frontend: _run_frontend_e2e_tests() + fix loop
  |       Fix loop updates: failed_tests = pw_report.failed_tests[:]
  |       Phase complete: only when health in ("passed", "partial")
  |     Post: Parse coverage matrix stats, coverage gate
  |     Crash isolation: outer try/except with traceback
  |
  +-- Recovery Report (line 4328-4330)
  +-- Phase Tracking (line 4332-4349)
  |     Artifact persistence: fix_cycle_log, coverage matrix, handoff
  +-- Verification (line 4351-4429)
  |     Gate: config.verification.enabled AND contract_registry
  |     verify_all_contracts + verify_task_completion
  |     Quality reloop awareness
  +-- State Cleanup (line 4435-4439)
        clear_state()
```

### Execution Order: VERIFIED CORRECT

The order matches the Architecture Inventory specification exactly:
1. Mock data scan -> UI compliance scan -> Deployment -> Asset -> PRD recon -> DB scans -> E2E -> Verification
2. Each scan independently config-gated
3. Each scan in its own try/except (crash isolation)
4. Fix functions called only when violations detected
5. recovery_types accumulated throughout

### Fix Function Verification

| Function | Line | scan_type branches | Fix cycle log | Crash isolation |
|----------|------|-------------------|---------------|-----------------|
| `_run_mock_data_fix()` | 1388 | N/A (single type) | YES | YES |
| `_run_ui_compliance_fix()` | 1466 | N/A (single type) | YES | YES |
| `_run_integrity_fix()` | 1857 | 5 branches: deployment, database_dual_orm, database_defaults, database_relationships, else=asset | YES | YES |
| `_run_e2e_fix()` | 1630 | N/A (parameterized by test_type) | YES | YES |
| `_run_milestone_wiring_fix()` | 1339 | N/A | NO | YES |
| `_run_review_only()` | 2529 | N/A | YES | NO (caller catches) |

All 5 `_run_integrity_fix` branches verified:
- `deployment` (line 1889): DEPLOY-001..004 instructions
- `database_dual_orm` (line 1905): DB-001..003 instructions
- `database_defaults` (line 1921): DB-004..005 instructions
- `database_relationships` (line 1936): DB-006..008 instructions
- `else` / asset (line 1954): ASSET-001..003 instructions

### State Management Verification

| State Update | Location | Correct? |
|-------------|----------|----------|
| `_use_milestones = False` | line 3370 (before try) | YES |
| `milestone_convergence_report = None` | line 3371 (before try) | YES |
| `run_cost` | line 3369 (before try) | YES |
| `_current_state.total_cost` | line 3476 (after orch) | YES |
| `completed_phases.append("orchestration")` | line 3488 | YES |
| `e2e_report` populated | lines 4139-4141, 4218-4220 | YES |
| `failed_tests` updated in fix loop | lines 4169, 4247 | YES (`[:]` copy) |
| `completed_phases: e2e_backend` | line 4176 (health=passed/partial) | YES |
| `completed_phases: e2e_frontend` | line 4254 (health=passed/partial) | YES |
| `recovery_types` accumulation | throughout | YES |

### Tracking Document Integration

| Integration Point | Location | Config Gate | Crash Isolation |
|-------------------|----------|-------------|-----------------|
| Coverage matrix generation | line 4101 | `tracking_documents.e2e_coverage_matrix` | YES |
| Coverage matrix parsing | line 4302 | `tracking_documents.e2e_coverage_matrix` | YES |
| Fix cycle log: mock fix | line 1433 | `tracking_documents.fix_cycle_log` | YES |
| Fix cycle log: UI fix | line 1516 | `tracking_documents.fix_cycle_log` | YES |
| Fix cycle log: integrity fix | line 1971 | `tracking_documents.fix_cycle_log` | YES |
| Fix cycle log: E2E fix | line 1657 | `tracking_documents.fix_cycle_log` | YES |
| Fix cycle log: review recovery | line 2596 | `tracking_documents.fix_cycle_log` | YES |
| Artifact path persistence | line 4336-4349 | unconditional | YES |

All tracking document integrations are config-gated and crash-isolated. Correct.

---

## Positive Observations

1. **Crash isolation is thorough**: Every post-orchestration scan has independent try/except. A failing scan never blocks subsequent scans.
2. **Config gating is consistent**: Each scan checks its own config boolean before executing.
3. **OR gate backward compatibility**: Mock and UI compliance scans use `post_orchestration_scans.X or milestone.X` (lines 3811, 3843), correctly supporting old YAML configs.
4. **E2E fix loop guards are correct**: `health not in ("passed", "skipped", "unknown")` prevents burning retries on non-failure states.
5. **Frontend fix loop updates `failed_tests`**: Line 4247 uses `pw_report.failed_tests[:]` to create a copy, preventing stale reference issues.
6. **Phase completion gating**: `e2e_backend` and `e2e_frontend` only appended when health is "passed" or "partial" (lines 4175, 4253).
7. **traceback.format_exc()** used in E2E outer exception handler (line 4324) and DB scan fix handlers (lines 4007, 4042, 4077).
8. **State persistence after orchestration**: Correct save_state call at line 3482 before post-orchestration begins.
9. **Intervention queue stopped in finally block**: Line 3501 ensures cleanup even on exception.
10. **PRD recon quality gate crash isolation**: File I/O wrapped in try/except OSError at line 3945 (M2 fix from v6 review).

---

## Assessment: MINOR FIXES NEEDED

| ID | Severity | Summary | Blocking? |
|----|----------|---------|-----------|
| F-1 | HIGH | Missing `json` import in `main()` — contract validation silently fails | No (caught by outer except) |
| F-2 | MEDIUM | `depth` undefined in interactive mode — all post-orch fixes fail silently | No (each caught individually) |
| F-3 | MEDIUM | Fix cycle log `cycle_number` always 1 — misleading tracking data | No (informational only) |
| F-4 | LOW | `_run_integrity_fix` else branch implicitly asset — no guard for future types | No |
| F-5 | LOW | `_run_review_only` no internal try/except — inconsistent pattern | No |
| F-6 | LOW | `e2e_testing` phase marker unconditionally appended | No (not used for gating) |

**Recommendation**: Fix F-1 and F-2 before production deployment. F-1 is a straightforward `import json` addition. F-2 needs a `depth` default before the interactive/non-interactive branch. F-3 through F-6 are non-blocking improvements.

The pipeline execution order, crash isolation, config gating, state management, and tracking document integration are all correctly implemented and match the Architecture Inventory specification.

---

*End of Pipeline Review*
