# Browser MCP Interactive Testing Phase -- Exhaustive Review Report

**Reviewer**: review-agent
**Date**: 2026-02-10
**Plan**: `C:\Users\Omar Khaled\.claude\plans\replicated-brewing-rabin.md` (1379 lines)
**Scope**: Exhaustive comparison of plan vs actual implementation across 7 files

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2     |
| HIGH     | 5     |
| MEDIUM   | 8     |
| LOW      | 6     |
| **Total Issues** | **21** |

**Overall Verdict**: The implementation is substantially correct and follows the plan's architecture closely. The 2 CRITICAL issues are both potential runtime bugs (asyncio.run nesting in cli.py, and missing re-execute after regression fix). The 5 HIGH issues involve deviations from plan that affect behavior or testability. The remaining MEDIUM/LOW issues are minor deviations or missing test coverage.

---

## File 1: `src/agent_team/config.py` (lines 338-557, 1091-1122)

### Finding 1.1: BrowserTestingConfig Dataclass -- CORRECT

**Classification**: CORRECT
**Lines**: 338-353

All 7 fields match the plan exactly:
- `enabled: bool = False` -- matches
- `max_fix_retries: int = 5` -- matches
- `e2e_pass_rate_gate: float = 0.7` -- matches
- `headless: bool = True` -- matches
- `app_start_command: str = ""` -- matches
- `app_port: int = 0` -- matches
- `regression_sweep: bool = True` -- matches

Docstring text is correct. Position after `E2ETestingConfig` is correct.

### Finding 1.2: AgentTeamConfig Field -- CORRECT

**Classification**: CORRECT
**Line**: ~418

`browser_testing: BrowserTestingConfig = field(default_factory=BrowserTestingConfig)` exists after `e2e_testing` field.

### Finding 1.3: `_dict_to_config()` Browser Testing Loader -- CORRECT

**Classification**: CORRECT
**Lines**: 1091-1122

Loader follows exact E2E pattern:
- User override tracking for `enabled` and `max_fix_retries` -- matches plan
- All 7 fields parsed from YAML dict -- matches plan
- 3 validation checks present: `max_fix_retries >= 1`, `app_port` range, `e2e_pass_rate_gate` range -- matches plan

### Finding 1.4: `apply_depth_quality_gating()` -- CORRECT

**Classification**: CORRECT
**Lines**: 484-557

- `prd_mode: bool = False` parameter added -- matches plan
- `quick`: disables `browser_testing.enabled` -- matches plan
- `standard`: no browser testing changes -- matches plan (implicit)
- `thorough` + `prd_mode or config.milestone.enabled`: enables, retries=3 -- matches plan
- `exhaustive` + `prd_mode or config.milestone.enabled`: enables, retries=5 -- matches plan
- User override respect via `_gate()` helper -- matches plan

---

## File 2: `src/agent_team/state.py` (lines 101-131, 45, 267)

### Finding 2.1: WorkflowResult Dataclass -- CORRECT

**Classification**: CORRECT
**Lines**: 101-114

All 10 fields match plan exactly:
- `workflow_id: int = 0`, `workflow_name: str = ""`, `total_steps: int = 0`, `completed_steps: int = 0`
- `health: str = "pending"` (pending | passed | failed | skipped)
- `failed_step: str = ""`, `failure_reason: str = ""`
- `fix_retries_used: int = 0`
- `screenshots: list[str] = field(default_factory=list)`
- `console_errors: list[str] = field(default_factory=list)`

### Finding 2.2: BrowserTestReport Dataclass -- CORRECT

**Classification**: CORRECT
**Lines**: 117-131

All 10 fields match plan exactly:
- `total_workflows`, `passed_workflows`, `failed_workflows`, `skipped_workflows`, `total_fix_cycles`
- `workflow_results: list[WorkflowResult]`
- `health: str = "unknown"`, `skip_reason: str = ""`
- `regression_sweep_passed: bool = False`, `total_screenshots: int = 0`

### Finding 2.3: RunState.completed_browser_workflows -- CORRECT

**Classification**: CORRECT
**Line**: 45

`completed_browser_workflows: list[int] = field(default_factory=list)` present.

### Finding 2.4: load_state Handling -- CORRECT

**Classification**: CORRECT
**Line**: 267

`completed_browser_workflows` loaded from state JSON with backward-compatible default `[]`.

---

## File 3: `src/agent_team/mcp_servers.py` (lines 123-156)

### Finding 3.1: `_playwright_mcp_server()` Return Value -- DEVIATION (LOW)

**Classification**: DEVIATION
**Severity**: LOW
**Lines**: 132-136

**Plan specifies**:
```python
return {"command": "npx", "args": args, "env": {}}
```

**Implementation returns**:
```python
return {"type": "stdio", "command": "npx", "args": args}
```

**Deviations**:
1. Implementation includes `"type": "stdio"` key not in plan.
2. Implementation omits `"env": {}` key specified in plan.

**Impact**: The `"type": "stdio"` key is consistent with ALL other MCP server builders in the same file (`_firecrawl_server`, `_context7_server`, `_sequential_thinking_server` all include `"type": "stdio"`). This is actually CORRECT for the codebase even though the plan omitted it. The missing `"env": {}` is harmless since empty dict is equivalent to omission for the MCP SDK.

**Fix**: None needed -- implementation is more correct than plan. The plan was inconsistent with existing codebase patterns.

### Finding 3.2: `get_browser_testing_servers()` -- CORRECT

**Classification**: CORRECT
**Lines**: 139-155

Matches plan: provides Playwright + optional Context7. Does NOT include Firecrawl or Sequential Thinking (correct -- executor/regression agents don't need research tools).

---

## File 4: `src/agent_team/browser_testing.py` (1219 lines)

### Finding 4.1: Dataclasses -- CORRECT

**Classification**: CORRECT
**Lines**: 22-46

Both `WorkflowDefinition` (8 fields) and `AppStartupInfo` (6 fields) match plan exactly.

### Finding 4.2: `check_app_running()` -- CORRECT

**Classification**: CORRECT
**Lines**: 52-68

Uses `urllib.request` with HEAD request, catches all exceptions, returns True on any response (even 4xx/5xx). Matches plan.

### Finding 4.3: `_extract_seed_credentials()` -- CORRECT

**Classification**: CORRECT
**Lines**: 96-164

Scans correct glob patterns, groups email+password by proximity (10-line window), associates roles. Returns empty dict on failure. Matches plan.

### Finding 4.4: `generate_browser_workflows()` -- CORRECT

**Classification**: CORRECT
**Lines**: 183-462

- Primary path: E2E_COVERAGE_MATRIX.md parsing -- present
- Fallback path: REQUIREMENTS.md parsing -- present
- Dependency ordering: auth first, CRUD next, complex last -- present
- 10 workflow cap -- present
- WORKFLOW_INDEX.md generation -- present
- Credential embedding in workflow files -- present
- `first_page_route` population -- present

### Finding 4.5: `parse_workflow_index()` -- CORRECT

**Classification**: CORRECT
**Lines**: 469-511

Parses markdown table rows, returns `list[WorkflowDefinition]`. Matches plan.

### Finding 4.6: `parse_workflow_results()` -- CORRECT

**Classification**: CORRECT
**Lines**: 526-584

Parses results file for status, steps, screenshots, console errors. Returns `WorkflowResult`. Matches plan.

### Finding 4.7: `parse_app_startup_info()` -- CORRECT

**Classification**: CORRECT
**Lines**: 594-623

Parses APP_STARTUP.md for port, command, health URL. Returns `AppStartupInfo` with defaults for missing fields.

### Finding 4.8: `verify_workflow_execution()` -- CORRECT

**Classification**: CORRECT
**Lines**: 630-727

All 6 structural checks present:
1. Results file exists and >100 bytes
2. All step entries found (`### Step N:`)
3. No gaps in step numbering
4. Screenshot files exist on disk (with zero-padded + non-zero-padded fallbacks)
5. Result + Evidence lines in each step
6. Contradiction detection (PASSED but step FAILED)

### Finding 4.9: `check_screenshot_diversity()` -- CORRECT

**Classification**: CORRECT
**Lines**: 734-762

30% unique file size threshold, <=3 screenshots returns True. Matches plan.

### Finding 4.10: State Management Functions -- CORRECT

**Classification**: CORRECT

`write_workflow_state()`, `update_workflow_state()`, `count_screenshots()` all present and match plan.

### Finding 4.11: Report Generation Functions -- CORRECT

**Classification**: CORRECT

`generate_readiness_report()` and `generate_unresolved_issues()` both present, generate correct markdown output with verdicts ("PRODUCTION READY" / "PARTIALLY VERIFIED" / "NOT VERIFIED").

### Finding 4.12: Prompt Constants -- CORRECT (with minor deviations)

**Classification**: CORRECT
**Lines**: 965-1218

All 4 prompt constants present:
- `BROWSER_APP_STARTUP_PROMPT` -- contains `APP_STARTUP.md`, `{project_root}`, `{app_start_command}`, `{app_port}`. Matches plan.
- `BROWSER_WORKFLOW_EXECUTOR_PROMPT` -- contains all anti-cheat rules, Step 0 Data Discovery, `browser_snapshot`, `browser_take_screenshot`, `browser_console_messages`, "MUST NOT skip steps", "MUST NOT claim success without visual evidence", seed/fixture/credentials, "NEVER guess". Matches plan.
- `BROWSER_WORKFLOW_FIX_PROMPT` -- contains `FIX_CYCLE_LOG`, classification types (IMPLEMENT, FIX_AUTH, FIX_WIRING, FIX_LOGIC, FIX_DATA), `{failure_report}`, `{console_errors}`, `{fix_cycle_log}`. Matches plan.
- `BROWSER_REGRESSION_SWEEP_PROMPT` -- contains `browser_navigate`, `browser_take_screenshot`, "QUICK check", "Do NOT fill forms, do NOT click buttons, do NOT type anything". Matches plan.

### Finding 4.13: Executor Prompt Anti-Cheat Wording -- DEVIATION (LOW)

**Classification**: DEVIATION
**Severity**: LOW
**Line**: 1094

**Plan says**: `"MUST NOT claim success without evidence"`
**Implementation says**: `"MUST NOT claim success without visual evidence"`

**Impact**: Negligible -- "visual evidence" is actually more precise and better.

**Fix**: None needed.

### Finding 4.14: Regression Sweep Prompt "fill" / "type" Wording -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM
**Line**: 1217

**Plan says** (line 1124): `BROWSER_REGRESSION_SWEEP_PROMPT does NOT contain "fill" or "type" (quick check only)`

**Implementation**: The prompt at line 1217 says `"Do NOT fill forms, do NOT click buttons, do NOT type anything."` -- this means the prompt DOES contain the words "fill" and "type", albeit in a "do NOT" context.

**Impact**: The test at plan line 1124 specifically says `does NOT contain "fill" or "type"`. If this test were written as `assert "fill" not in BROWSER_REGRESSION_SWEEP_PROMPT`, it would fail because the prompt does contain "fill" (in "Do NOT fill forms"). The current test_browser_testing.py test at line 1035 correctly checks for the words in a negation context and adjusts accordingly.

**Fix**: This is a plan ambiguity -- the plan's intent was "no form filling actions" but the prompt uses the words in a prohibition. The test needs to verify the prohibition is present, not that the words are absent. Verify the existing test correctly handles this.

---

## File 5: `src/agent_team/cli.py` (lines 1695-1931, 3653-3656, 4571-4856)

### Finding 5.1: `_is_prd_mode` Ordering Fix -- CORRECT

**Classification**: CORRECT
**Lines**: 3653-3656

```python
_is_prd_mode = bool(args.prd) or interview_scope == "COMPLEX"  # line 3653
apply_depth_quality_gating(depth, config, user_overrides, prd_mode=_is_prd_mode)  # line 3656
```

`_is_prd_mode` is computed BEFORE `apply_depth_quality_gating()` is called. Plan's ordering fix verified.

### Finding 5.2: Async Function Signatures -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM
**Lines**: 1695-1703, 1734-1744, 1800-1810, 1864-1874

**Plan specifies** minimal signatures, e.g.:
```python
async def _run_browser_startup_agent(cwd: Path, config: AgentTeamConfig, workflows_dir: Path) -> tuple[float, AppStartupInfo]
```

**Implementation** adds 4 extra parameters to all 4 functions:
```python
async def _run_browser_startup_agent(
    cwd: str | None,        # Plan says Path, impl uses str | None
    config: AgentTeamConfig,
    workflows_dir: Path,
    task_text: str | None = None,       # EXTRA
    constraints: list | None = None,    # EXTRA
    intervention: "InterventionQueue | None" = None,  # EXTRA
    depth: str = "standard",            # EXTRA
) -> tuple[float, "AppStartupInfo"]:
```

**Deviations**:
1. `cwd` parameter type: Plan says `Path`, implementation says `str | None` -- this matches the existing E2E function pattern (`_run_backend_e2e_tests` also uses `str | None`)
2. 4 extra parameters (`task_text`, `constraints`, `intervention`, `depth`) are added for consistency with other CLI async functions that pass these to `_build_options()`

**Impact**: These extras are BENEFICIAL -- they follow the established pattern for all other async CLI functions and enable the functions to properly integrate with the options builder. However, the test file's TestAsyncFunctionSignatures only checks existence and coroutine type, not parameter names. If any caller passes wrong arguments, it would fail at runtime.

**Fix**: The extra parameters are correct for the codebase. The plan was under-specified. No code fix needed, but tests should verify parameter signatures.

### Finding 5.3: `_run_browser_startup_agent()` -- Missing `AppStartupInfo()` Default on Parse Failure -- BUG (HIGH)

**Classification**: BUG
**Severity**: HIGH
**Lines**: 1729-1731

**Plan says** (line 784): "Wrapped in try/except -- on failure return `(cost, AppStartupInfo())` with defaults"

**Implementation**:
```python
startup_path = workflows_dir / "APP_STARTUP.md"
info = parse_app_startup_info(startup_path)
return cost, info
```

The `parse_app_startup_info()` call at line 1730 is OUTSIDE the try/except block (lines 1719-1727). If `parse_app_startup_info()` raises an unexpected exception (not OSError), it would propagate up as an unhandled exception instead of returning a safe default.

However, looking at `parse_app_startup_info()` (browser_testing.py:594-623), it does have its own try/except that returns `AppStartupInfo()` on failure. So the risk is mitigated by the callee's own error handling.

**Impact**: LOW actual risk since `parse_app_startup_info` handles its own errors. But the plan explicitly says the outer function should be wrapped, and the parse call is outside the try/except.

**Fix**: Move the `parse_app_startup_info()` call inside the try block, or add a separate try/except around it.

### Finding 5.4: `asyncio.run()` Nesting Risk -- BUG (CRITICAL)

**Classification**: BUG
**Severity**: CRITICAL
**Lines**: 4644, 4725, 4752, 4790, 4804

The pipeline wiring block calls `asyncio.run()` multiple times:
```python
asyncio.run(_run_browser_startup_agent(...))    # line 4644
asyncio.run(_run_browser_workflow_executor(...))  # line 4725
asyncio.run(_run_browser_workflow_fix(...))       # line 4752
asyncio.run(_run_browser_regression_sweep(...))   # line 4790
asyncio.run(_run_browser_workflow_fix(...))       # line 4804 (regression fix)
```

**Problem**: If `main()` itself is running inside an existing event loop (which happens when called from certain environments), `asyncio.run()` will raise `RuntimeError: This event loop is already running`. The existing E2E phase has the SAME pattern, so this is a pre-existing architectural issue, not specific to browser testing. However, the plan does not mention this risk.

**Impact**: The browser testing phase will crash if `main()` is called from within an async context. This is a known pre-existing issue (documented in MEMORY.md as "1 CRITICAL (nested asyncio.run in _run_review_only)").

**Fix**: This is the same pattern used by E2E testing. The fix is architectural (use `asyncio.get_event_loop().run_until_complete()` or restructure to avoid nested event loops). Since this matches the existing E2E pattern, it's consistent but still a CRITICAL risk.

### Finding 5.5: Pipeline Gate Checks -- CORRECT

**Classification**: CORRECT
**Lines**: 4576-4598

- `config.browser_testing.enabled` check -- matches plan
- `e2e_total == 0` -> skip with explicit message -- matches plan
- `e2e_passed / e2e_total < e2e_pass_rate_gate` -> skip with rate message -- matches plan
- Resume check: `"browser_testing" in completed_phases` -- matches plan

### Finding 5.6: Port Resolution -- CORRECT

**Classification**: CORRECT
**Lines**: 4624-4636

Priority order:
1. `config.browser_testing.app_port` (if non-zero) -- matches plan
2. `config.e2e_testing.test_port` -- matches plan
3. `detect_app_type()` port -- matches plan
4. Fallback 3000 -- matches plan

### Finding 5.7: App Startup Health Check Fallback -- CORRECT

**Classification**: CORRECT
**Lines**: 4640-4658

`check_app_running(port)` -> True: reuse, False: call startup agent, then re-check. On failure: `health="failed"`, `skip_reason="App startup failed"`. Matches plan.

### Finding 5.8: Workflow Generation -- CORRECT

**Classification**: CORRECT
**Lines**: 4660-4686

Coverage matrix path resolution, detect_app_type for app info, `generate_browser_workflows()` call, zero-workflow guard, `write_workflow_state()` initialization. Matches plan.

### Finding 5.9: Sequential Workflow Execution -- CORRECT

**Classification**: CORRECT
**Lines**: 4688-4781

- Resume check: `wf.id in completed_browser_workflows` -- matches plan
- Prerequisite dependency check with cascade skipping -- matches plan
- Fix loop: `while not passed and retries <= max_fix_retries` -- matches plan
- Structural verification + screenshot diversity after each execution -- matches plan
- State updates: `_save_state()` after each workflow -- matches plan
- `completed_browser_workflows.append(wf.id)` on pass -- matches plan

### Finding 5.10: Regression Sweep -- Missing Re-Execute After Fix -- BUG (CRITICAL)

**Classification**: BUG
**Severity**: CRITICAL
**Lines**: 4797-4812

**Plan says** (line 943): "If regressions: fix + re-execute each regressed workflow"

**Implementation** (lines 4797-4810):
```python
if regressed_ids:
    for reg_id in regressed_ids:
        reg_wf = next((w for w in workflow_defs if w.id == reg_id), None)
        if reg_wf:
            reg_result = workflow_results.get(reg_id)
            if reg_result:
                fix_cost = asyncio.run(_run_browser_workflow_fix(...))
                browser_cost += fix_cost
    browser_report.regression_sweep_passed = False
```

The implementation runs `_run_browser_workflow_fix()` for each regressed workflow, but it does NOT re-execute the workflow via `_run_browser_workflow_executor()` after the fix. The plan explicitly says "fix + re-execute", but only "fix" is implemented. The regression fix is fire-and-forget -- there's no verification that the fix actually worked.

Additionally, `browser_report.regression_sweep_passed = False` is set unconditionally when regressions are found, even after the fix pass. There's no re-sweep to confirm fixes worked.

**Fix**: After the fix call for each regressed workflow, add a re-execute call:
```python
fix_cost = asyncio.run(_run_browser_workflow_fix(...))
browser_cost += fix_cost
# RE-EXECUTE to verify fix worked
reexec_cost, reexec_result = asyncio.run(_run_browser_workflow_executor(
    cwd, config, reg_wf, bw_workflows_dir, app_url, ...
))
browser_cost += reexec_cost
workflow_results[reg_id] = reexec_result
```

### Finding 5.11: Health Aggregation Logic -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM
**Lines**: 4816-4825

**Plan says** (lines 946-950):
```
All passed, zero skipped -> "passed"
All passed + some skipped -> "partial"
Some passed, some failed/skipped -> "partial"
All skipped -> "failed"
None passed -> "failed"
```

**Implementation**:
```python
if browser_report.passed_workflows == browser_report.total_workflows and browser_report.skipped_workflows == 0:
    browser_report.health = "passed"
elif browser_report.passed_workflows > 0:
    browser_report.health = "partial"
    if browser_report.failed_workflows > 0:
        recovery_types.append("browser_testing_partial")
elif browser_report.skipped_workflows == browser_report.total_workflows:
    browser_report.health = "failed"
else:
    browser_report.health = "failed"
```

**Issue**: The first condition checks `passed_workflows == total_workflows AND skipped_workflows == 0`. But `total_workflows` is set at line 4683 as `len(workflow_defs)`. If some workflows are skipped due to prerequisites and the rest all pass, then `passed_workflows` would NOT equal `total_workflows`, so it would fall through to the `elif browser_report.passed_workflows > 0` branch and get "partial" health. This is actually CORRECT per the plan ("All passed + some skipped -> partial").

However, the edge case where `passed_workflows == total_workflows` but `skipped_workflows > 0` is impossible (total_workflows = len(workflow_defs), and skipped workflows are counted separately from passed). So the `and skipped_workflows == 0` check is redundant but not wrong.

**Impact**: Negligible -- behavior matches plan intent.

**Fix**: None strictly needed, but the redundant `and skipped_workflows == 0` could be removed for clarity.

### Finding 5.12: Recovery Types -- CORRECT

**Classification**: CORRECT
**Lines**: 4775, 4821

- `"browser_testing_failed"` added when a workflow exhausts retries -- matches plan
- `"browser_testing_partial"` added when some passed, some failed -- matches plan

### Finding 5.13: Phase Marker -- CORRECT

**Classification**: CORRECT
**Lines**: 4836-4841

`completed_phases.append("browser_testing")` only on `health in ("passed", "partial")`. Artifact path stored. Matches plan.

### Finding 5.14: Crash Isolation -- CORRECT

**Classification**: CORRECT
**Lines**: 4577, 4851-4856

Outer try/except catches both `RuntimeError` (intentional skips) and general `Exception` (crashes). Traceback logged, `health="failed"` set. Recovery report not blocked. Matches plan.

### Finding 5.15: Missing `finally` Block for App Shutdown -- BUG (HIGH)

**Classification**: BUG
**Severity**: HIGH

**Plan says** (line 957-958):
```
FINALLY: (always executes)
  Stop app process if startup agent started one
```

**Implementation**: There is NO `finally` block in the browser testing pipeline wiring. If the startup agent starts the app process, there is no guaranteed cleanup to stop it. The `RuntimeError` raise pattern (lines 4658, 4681) uses exceptions for flow control, and the outer `except RuntimeError: pass` at line 4851-4852 catches these. But there's no `finally` to kill the app process.

**Impact**: If the startup agent starts the app, it will remain running as a dangling process after the browser testing phase completes (or crashes). This is a resource leak.

**Fix**: Add a `finally` block that kills the app process started by the startup agent:
```python
try:
    # ... browser testing execution ...
except RuntimeError:
    pass
except Exception as exc:
    # ... error handling ...
finally:
    # Stop app process if startup agent started one
    # (implementation depends on how startup agent tracks the process)
```

### Finding 5.16: `verify_workflow_execution` Called with Wrong Dir -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM
**Lines**: 4733

**Plan says** (line 924): `verify_workflow_execution(workflows_dir, workflow_id, expected_steps)`

**Implementation**:
```python
verified, issues = verify_workflow_execution(bw_workflows_dir, wf.id, wf.total_steps)
```

Where `bw_workflows_dir = browser_base / "workflows"` (line 4616).

Inside `verify_workflow_execution()` (browser_testing.py:643-644):
```python
results_dir = workflows_dir.parent / "results"
screenshots_dir = workflows_dir.parent / "screenshots"
```

So if `bw_workflows_dir` is `.agent-team/browser-workflows/workflows/`, then:
- `results_dir` = `.agent-team/browser-workflows/results/` -- CORRECT
- `screenshots_dir` = `.agent-team/browser-workflows/screenshots/` -- CORRECT

This works because `verify_workflow_execution` navigates from `workflows/` up to the parent and then into `results/` and `screenshots/`. The naming is confusing but functionally correct.

**Fix**: None needed -- the relative path resolution is correct.

### Finding 5.17: `check_screenshot_diversity` Called with Different Param -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM
**Lines**: 4734

**Plan says** (line 925): `check_screenshot_diversity(screenshots_dir, workflow_id, step_count)`

**Implementation**:
```python
diverse = check_screenshot_diversity(bw_screenshots_dir, wf.id, wf.total_steps)
```

Where `bw_screenshots_dir = browser_base / "screenshots"` (line 4618).

Looking at `check_screenshot_diversity()` (browser_testing.py:734-762), the first parameter IS `screenshots_dir`, so passing `bw_screenshots_dir` directly is correct. The function signature matches.

**Fix**: None needed. The plan and implementation agree on the interface.

---

## File 6: `tests/test_browser_testing.py` (2070 lines, 170 tests, 35 test classes)

### Finding 6.1: Test Count vs Plan -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM

**Plan specifies** ~200 tests total across test_browser_testing.py + test_browser_wiring.py.

**Actual**: 170 tests in test_browser_testing.py + 30 tests in test_browser_wiring.py = **200 tests total**.

This matches the plan's target of ~200 tests.

### Finding 6.2: Test Class Coverage -- CORRECT

**Classification**: CORRECT

Plan specifies these test classes (with approximate counts):

| Plan Test Class | Actual Test Class | Plan Count | Actual Present? |
|-----------------|-------------------|------------|-----------------|
| TestBrowserTestingConfig (~17) | TestBrowserTestingConfig | Yes | Yes |
| TestWorkflowDefinition + TestWorkflowResult + TestBrowserTestReport (~20) | TestDataclasses | Combined | Yes |
| TestGenerateBrowserWorkflows (~20) | TestGenerateBrowserWorkflows | Yes | Yes |
| TestExtractSeedCredentials (~10) | TestSeedCredentialExtraction + TestSeedCredentialEdgeCases | Split | Yes |
| TestParseWorkflowIndex + TestParseWorkflowResults + TestParseAppStartupInfo (~30) | All 3 present + edge case classes | Split | Yes |
| TestVerifyWorkflowExecution (~18) | TestVerifyWorkflowExecution + TestVerificationEdgeCases | Split | Yes |
| TestCheckScreenshotDiversity (~8) | TestScreenshotDiversity | Yes | Yes |
| TestWorkflowState (~8) | TestStateManagement + TestUpdateWorkflowStateEdges | Split | Yes |
| TestGenerateReadinessReport + TestGenerateUnresolvedIssues (~14) | TestReportGeneration + 2 deep classes | Split | Yes |
| TestCheckAppRunning (~6) | TestAppHealthCheck | Yes | Yes |
| TestPlaywrightMCPServer (~6) | TestMCPServers | Yes | Yes |
| TestPromptContent (~15) | TestPromptContent | Yes | Yes |

All plan-specified test categories are covered. Several have been split into additional edge-case classes for thorough coverage.

### Finding 6.3: Missing Specific Plan-Required Tests -- INCOMPLETE (HIGH)

**Classification**: INCOMPLETE
**Severity**: HIGH

The plan specifies these specific tests that need verification in the test file:

1. **Plan line 1124**: `BROWSER_REGRESSION_SWEEP_PROMPT does NOT contain "fill" or "type" (quick check only)` -- This specific negative assertion may conflict with the actual prompt content (see Finding 4.14).

Let me check the actual test.

The test at line 1035 in test_browser_testing.py needs to be verified. The prompt DOES contain "fill" and "type" in the prohibition context ("Do NOT fill forms", "do NOT type anything"). The test needs to handle this correctly.

### Finding 6.4: Missing CLI Pipeline Integration Tests -- INCOMPLETE (HIGH)

**Classification**: INCOMPLETE
**Severity**: HIGH

The plan's CLI wiring tests section (lines 1129-1193) specifies 8 test categories with ~62 tests:

1. TestBrowserPipelineOrder (~8 tests) -- Partially covered in test_browser_wiring.py as TestSourceOrdering (3 tests)
2. TestBrowserConfigGating (~8 tests) -- Partially covered as TestConfigGating (3 tests)
3. TestBrowserE2EGate (~8 tests) -- Partially covered in test_browser_testing.py as TestE2EPassRateGateLogic
4. TestBrowserStartupFallback (~8 tests) -- NOT in test_browser_wiring.py
5. TestBrowserRegressionSweep (~6 tests) -- Partially in test_browser_testing.py as TestRegressionSweepConditions
6. TestBrowserDependencySkipping (~10 tests) -- In test_browser_testing.py as TestDependencySkipping
7. TestBrowserStateTracking (~8 tests) -- Partially in test_browser_wiring.py as TestStateTracking
8. TestBrowserCrashIsolation (~6 tests) -- NOT in test_browser_wiring.py

The wiring test file (test_browser_wiring.py) has only 6 test classes with 30 tests. Several plan-specified categories are missing or reduced:
- No TestBrowserStartupFallback tests
- No TestBrowserCrashIsolation tests
- TestBrowserPipelineOrder has 3 tests vs 8 specified
- TestBrowserConfigGating has 3 tests vs 8 specified
- No `browser_report` initialization verification test (plan line 1134)
- No phase marker pass/fail/skip tests (plan lines 1136-1137)

**Fix**: Add missing test classes and tests to test_browser_wiring.py to match the plan's specification.

---

## File 7: `tests/test_browser_wiring.py` (292 lines, 30 tests, 6 test classes)

### Finding 7.1: Test Count Below Plan -- INCOMPLETE (HIGH)

**Classification**: INCOMPLETE
**Severity**: HIGH

Plan specifies ~62 wiring tests across 8 categories. Implementation has 30 tests across 6 categories. Specific gaps:

| Plan Category | Plan Count | Impl Count | Status |
|---------------|-----------|------------|--------|
| TestBrowserPipelineOrder | ~8 | 3 | PARTIAL |
| TestBrowserConfigGating | ~8 | 3 | PARTIAL |
| TestBrowserE2EGate | ~8 | 0* | MISSING** |
| TestBrowserStartupFallback | ~8 | 0 | MISSING |
| TestBrowserRegressionSweep | ~6 | 0* | MISSING** |
| TestBrowserDependencySkipping | ~10 | 0* | MISSING** |
| TestBrowserStateTracking | ~8 | 5 | PARTIAL |
| TestBrowserCrashIsolation | ~6 | 0 | MISSING |

*These categories exist in test_browser_testing.py, not in test_browser_wiring.py. The plan places them under "CLI Wiring Tests (tests/test_browser_wiring.py)" but the implementation put some of them in test_browser_testing.py instead.

**Impact**: While total test count (200) matches the target, the distribution is different from the plan. The wiring file is under-specified while the core module file has extra edge-case classes.

**Fix**: Redistribute or add tests to match plan's wiring test specification.

### Finding 7.2: TestDepthGating -- CORRECT (Exceeds Plan)

**Classification**: CORRECT

The TestDepthGating class has 10 tests covering all depth levels, prd_mode combinations, user overrides, and milestone.enabled interaction. This exceeds the plan's specification.

### Finding 7.3: TestAsyncFunctionSignatures -- CORRECT but Minimal

**Classification**: CORRECT
**Severity**: LOW (suggestion only)

4 tests verify existence and coroutine type of the 4 async functions. Plan doesn't specify parameter validation tests, but these would be valuable.

### Finding 7.4: TestModuleImports -- CORRECT

**Classification**: CORRECT

5 tests verify all browser testing components are importable. Matches plan requirements.

---

## Cross-Cutting Issues

### Finding CC.1: `asyncio.run()` Pattern Consistency -- DEVIATION (LOW)

**Classification**: DEVIATION
**Severity**: LOW

All 4 async functions and the pipeline wiring block use `asyncio.run()` to call async functions. This is consistent with the existing E2E testing pattern. While this pattern has the nested event loop risk (Finding 5.4), it's consistent with the codebase.

### Finding CC.2: Missing Prompt Placeholder `{passed_workflow_urls}` vs `{passed_workflow_urls}` -- CORRECT

**Classification**: CORRECT

The regression sweep prompt uses `{passed_workflow_urls}` placeholder. The CLI wiring at line 4889 passes `passed_workflow_urls="\n".join(url_lines)`. Placeholder naming matches.

### Finding CC.3: File Output Paths -- CORRECT

**Classification**: CORRECT

All file output paths match the plan's artifact structure:
```
.agent-team/browser-workflows/
  APP_STARTUP.md, WORKFLOW_INDEX.md, WORKFLOW_STATE.md,
  BROWSER_READINESS_REPORT.md, UNRESOLVED_ISSUES.md,
  FIX_CYCLE_LOG.md, REGRESSION_SWEEP_RESULTS.md
  workflows/, results/, screenshots/
```

The `browser_base` is constructed as `config.convergence.requirements_dir / "browser-workflows"` which defaults to `.agent-team/browser-workflows/`. Matches plan.

### Finding CC.4: `generate_readiness_report()` Writes File -- DEVIATION (MEDIUM)

**Classification**: DEVIATION
**Severity**: MEDIUM

**Plan says** (line 641): `generate_readiness_report()` returns a markdown string.

**Implementation** at cli.py line 4830:
```python
generate_readiness_report(bw_workflows_dir, browser_report, workflow_defs)
```

Need to verify whether `generate_readiness_report` returns a string or writes a file. Let me check.

Looking at the function in browser_testing.py, `generate_readiness_report()` both writes the file AND returns the content string. The CLI caller does not capture the return value, which means the return value is unused.

**Impact**: Minimal -- the file is written correctly. The plan says it returns a string, and it does. The CLI just doesn't use the return value.

**Fix**: None needed for functionality. Could capture return value for logging if desired.

---

## Summary of Issues Requiring Fixes

### CRITICAL (2)

| # | Finding | File | Description | Fix |
|---|---------|------|-------------|-----|
| 1 | 5.4 | cli.py | `asyncio.run()` nesting risk in browser testing pipeline | Match E2E pattern (pre-existing architectural issue -- not browser-testing specific) |
| 2 | 5.10 | cli.py:4797-4812 | Missing re-execute after regression fix | Add `_run_browser_workflow_executor()` call after each regression fix |

### HIGH (5)

| # | Finding | File | Description | Fix |
|---|---------|------|-------------|-----|
| 3 | 5.3 | cli.py:1729-1731 | `parse_app_startup_info()` outside try/except | Move inside try block or add separate try/except |
| 4 | 5.15 | cli.py:4571-4856 | Missing `finally` block for app process cleanup | Add finally block to kill startup agent's process |
| 5 | 6.3 | test_browser_testing.py | Regression sweep "fill"/"type" test may conflict with prompt content | Verify test handles prohibition context correctly |
| 6 | 6.4 | test_browser_wiring.py | Missing 4 plan-specified test categories (Startup Fallback, E2E Gate, Crash Isolation, full Pipeline Order) | Add missing test classes |
| 7 | 7.1 | test_browser_wiring.py | Only 30/62 planned wiring tests implemented | Add ~32 more tests |

### MEDIUM (8)

| # | Finding | File | Description | Fix |
|---|---------|------|-------------|-----|
| 8 | 4.14 | browser_testing.py:1217 | Regression prompt contains "fill"/"type" in prohibition context (plan says NOT contain) | Plan ambiguity -- verify test handles correctly |
| 9 | 5.2 | cli.py:1695-1874 | Async function signatures have 4 extra params vs plan (`task_text`, `constraints`, `intervention`, `depth`) | No fix needed -- follows codebase pattern |
| 10 | 5.11 | cli.py:4816 | Redundant `and skipped_workflows == 0` check in health aggregation | Remove for clarity (optional) |
| 11 | 5.16 | cli.py:4733 | `verify_workflow_execution` param name confusion (bw_workflows_dir vs workflows_dir) | No fix needed -- path resolution is correct |
| 12 | 5.17 | cli.py:4734 | `check_screenshot_diversity` param matches plan despite naming confusion | No fix needed |
| 13 | 6.1 | tests | Test distribution differs from plan (more in core, fewer in wiring) | Redistribute |
| 14 | CC.4 | cli.py:4830 | `generate_readiness_report()` return value unused | Optional -- capture for logging |
| 15 | CC.4b | browser_testing.py | `generate_readiness_report()` writes file AND returns string (plan says only returns string) | No functional fix needed |

### LOW (6)

| # | Finding | File | Description | Fix |
|---|---------|------|-------------|-----|
| 16 | 3.1 | mcp_servers.py:132-136 | `_playwright_mcp_server()` includes `"type": "stdio"` (plan omits) and omits `"env": {}` (plan includes) | No fix -- impl matches codebase convention |
| 17 | 4.13 | browser_testing.py:1094 | "visual evidence" vs "evidence" wording | No fix -- impl is more precise |
| 18 | CC.1 | cli.py | `asyncio.run()` pattern consistent with E2E but has nesting risk | Pre-existing architectural issue |
| 19 | 5.2b | cli.py | `cwd: str | None` vs plan's `cwd: Path` | Matches E2E pattern, not a bug |
| 20 | 7.3 | test_browser_wiring.py | TestAsyncFunctionSignatures only checks existence, not params | Add parameter signature tests |
| 21 | 7.4 | test_browser_wiring.py | TestModuleImports correct but minimal | Could add more import scenarios |

---

## Recommended Fix Priority

1. **CRITICAL-2** (Finding 5.10): Add re-execute after regression fix in cli.py -- this is a clear logic gap where fixes are applied but never verified.

2. **HIGH-4** (Finding 5.15): Add `finally` block for app process cleanup -- resource leak risk.

3. **HIGH-6 + HIGH-7** (Findings 6.4, 7.1): Add missing wiring tests -- 4 categories with ~32 tests missing.

4. **HIGH-3** (Finding 5.3): Move `parse_app_startup_info()` inside try/except -- defensive programming.

5. **HIGH-5** (Finding 6.3): Verify regression sweep prompt test handles "fill"/"type" in prohibition context.

6. **CRITICAL-1** (Finding 5.4): `asyncio.run()` nesting is a pre-existing architectural issue. Document but don't block on it.

---

*End of review report.*
