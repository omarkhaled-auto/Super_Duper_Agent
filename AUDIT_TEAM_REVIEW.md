# Audit Team Review Report

**Date**: 2026-02-18
**Reviewer**: Claude Opus 4.6 (Senior Code Reviewer)
**Files reviewed**:
- `src/agent_team/audit_team.py` (640 lines)
- `src/agent_team/config.py` (AuditTeamConfig, depth gating, _dict_to_config)
- `src/agent_team/cli.py` (_run_audit_team, _run_audit_fix, per-milestone wiring, end-of-run wiring)
- `tests/test_audit_team.py` (1046 lines)

---

## CRITICAL (must fix before production)

### C1: LIBRARY_AUDITOR_PROMPT missing `{requirements_path}` placeholder -- silent no-op

- **File**: `src/agent_team/audit_team.py:234-268`
- **Issue**: The `LIBRARY_AUDITOR_PROMPT` does NOT contain `{requirements_path}` anywhere in its text. However, `get_auditor_prompt()` (line 583) calls `.format(requirements_path=..., output_path=...)` on it. Python's `str.format()` silently ignores extra keyword arguments, so this does not raise an error -- but the library auditor receives **no guidance** about which requirements file to consult. It has `{output_path}` but no `{requirements_path}`, meaning the auditor has no way to locate the project's requirements document.
- **Impact**: The library auditor flies blind -- it cannot correlate its findings against the REQUIREMENTS.md requirement IDs. All other 4 auditors have `{requirements_path}` in their prompts.
- **Fix**: Add a `{requirements_path}` reference to the LIBRARY_AUDITOR_PROMPT, for example in the `## Input` section:
```python
## Input
Read {requirements_path} for any library version requirements or constraints.
Also read the codebase to identify all third-party libraries being used.
```

### C2: Shared audit directory causes cross-milestone report overwriting

- **File**: `src/agent_team/cli.py:3677`
- **Issue**: The `audit_dir` is always computed as:
  ```python
  audit_dir = Path(cwd) / config.convergence.requirements_dir / "audit-reports"
  ```
  This is a single, fixed directory regardless of whether the audit is running per-milestone or end-of-run. When `config.audit_team.per_milestone = True`, each milestone's audit writes its findings to the SAME files (e.g., `requirements_audit.md`, `technical_audit.md`). This means:
  1. Milestone B's audit **overwrites** Milestone A's audit reports
  2. The end-of-run audit overwrites the last milestone's reports
  3. There is no audit history preserved
- **Impact**: In PRD+ mode with multiple milestones, only the last milestone's audit results survive. Earlier milestone audit results are lost, making it impossible to review or debug earlier milestone findings.
- **Fix**: Make audit_dir scope-aware:
```python
if scope_label.startswith("milestone:"):
    ms_id = scope_label.split(":", 1)[1]
    audit_dir = Path(cwd) / config.convergence.requirements_dir / "milestones" / ms_id / "audit-reports"
else:
    audit_dir = Path(cwd) / config.convergence.requirements_dir / "audit-reports"
```

### C3: `completed_phases.append("audit_team")` runs even when audit crashes

- **File**: `src/agent_team/cli.py:5293-5294`
- **Issue**: The `completed_phases.append("audit_team")` is placed OUTSIDE the try/except block:
  ```python
  try:
      audit_cost, audit_report = asyncio.run(_run_audit_team(...))
      ...
  except Exception as exc:
      print_warning(f"Audit-team failed: {exc}\n{_tb_audit.format_exc()}")

  if _current_state:
      _current_state.completed_phases.append("audit_team")  # ALWAYS runs
  ```
  If the audit team crashes (exception path), the phase is still marked as completed. On resume, the audit will be **skipped** even though it never finished. This is the same class of bug previously fixed in E2E testing (Review Fix H5 from the E2E phase).
- **Impact**: A crashed audit team run is permanently marked as done, preventing retry on resume.
- **Fix**: Move the `completed_phases.append` inside the try block, after successful completion, or add a health check:
```python
if _current_state and audit_report and audit_report.health in ("passed", "needs-fixes"):
    _current_state.completed_phases.append("audit_team")
```

---

## HIGH (should fix)

### H1: Deduplication key `(requirement_id, file_path)` is too aggressive for cross-cutting findings

- **File**: `src/agent_team/audit_team.py:462-469`
- **Issue**: The dedup key is `(f.requirement_id, f.file_path)`. When `requirement_id` is empty (`""`) and `file_path` is the same file, ALL cross-cutting findings for the same file collapse into one. For example, if the technical auditor finds 3 different issues (empty catch, `any` type, hardcoded secret) in the same file with no requirement ID, they all get deduped to a single finding.
- **Evidence**: Cross-cutting findings (like those from the technical auditor's "check for" list) will have `requirement_id=""` and could share a `file_path`. The dedup key `("", "src/app.ts")` would collapse all of them.
- **Fix**: Add `description` or a hash of the description to the dedup key:
```python
key = (f.requirement_id, f.file_path, f.description[:80] if not f.requirement_id else "")
```
Or better, only dedup when `requirement_id` is non-empty:
```python
if f.requirement_id:
    key = (f.requirement_id, f.file_path)
else:
    key = (f.requirement_id, f.file_path, f.description)
```

### H2: `asyncio.run()` nesting risk at end-of-run audit wiring

- **File**: `src/agent_team/cli.py:5263`
- **Issue**: The end-of-run audit calls `asyncio.run(_run_audit_team(...))`. If `main()` is already running inside an async context (e.g., called from another async framework or if there's already an event loop running), this will raise `RuntimeError: asyncio.run() cannot be called from a running event loop`. This is a known pre-existing architectural issue (documented in MEMORY.md for E2E and browser testing), but it affects the audit team too.
- **Impact**: In environments with an existing event loop, the end-of-run audit will crash. The per-milestone wiring (line 1454) correctly uses `await _run_audit_team(...)` because it's already inside an async function, but end-of-run uses the synchronous `asyncio.run()` wrapper.
- **Note**: This is listed as pre-existing but affects audit team specifically. The per-milestone path at line 1454 is correct (uses `await`). Only the end-of-run path is affected.

### H3: User override tracking misses 7 of 11 config fields

- **File**: `src/agent_team/config.py:1289`
- **Issue**: The user_overrides tracking only captures 4 fields:
  ```python
  for key in ("enabled", "max_fix_rounds", "per_milestone", "end_of_run"):
      if key in at:
          user_overrides.add(f"audit_team.{key}")
  ```
  But AuditTeamConfig has 11 fields. The missing 7 are: `requirements_auditor`, `technical_auditor`, `interface_auditor`, `test_auditor`, `library_auditor`, `pass_threshold`, `severity_gate`. This means depth gating will override user-specified values for these fields because `_gate()` checks `user_overrides` before applying defaults.
- **Impact**: If a user sets `audit_team.library_auditor: true` in their config and runs at `standard` depth, the depth gating at line 594 will set `library_auditor=False` because `"audit_team.library_auditor"` is not in `user_overrides`. The user's explicit choice is silently discarded.
- **Fix**: Expand the tracking loop:
```python
for key in ("enabled", "max_fix_rounds", "per_milestone", "end_of_run",
            "requirements_auditor", "technical_auditor", "interface_auditor",
            "test_auditor", "library_auditor", "pass_threshold", "severity_gate"):
    if key in at:
        user_overrides.add(f"audit_team.{key}")
```

### H4: No resume guard for end-of-run audit

- **File**: `src/agent_team/cli.py:5259`
- **Issue**: The end-of-run audit block checks `config.audit_team.enabled and config.audit_team.end_of_run` but does NOT check `"audit_team" not in _current_state.completed_phases`. On resume, even if the audit completed successfully in the previous run, it will run again, wasting significant API budget (5 auditor sessions + scorer + potential fix rounds).
- **Evidence**: Other phases in the pipeline (e.g., E2E testing) check `completed_phases` before re-running.
- **Fix**: Add a resume guard:
```python
if config.audit_team.enabled and config.audit_team.end_of_run:
    if _current_state and "audit_team" in _current_state.completed_phases:
        print_info("Audit-team already completed in previous run, skipping.")
    else:
        ...
```

### H5: Fix cycle log `cycle_number` is always 1

- **File**: `src/agent_team/cli.py:3818`
- **Issue**: The `build_fix_cycle_entry` call hardcodes `cycle_number=1`:
  ```python
  cycle_entry = build_fix_cycle_entry(
      phase="Audit-Team",
      cycle_number=1,  # Always 1, regardless of fix_round
      ...
  )
  ```
  This should be `cycle_number=fix_round + 1` but the fix_cycle_section is built in `_run_audit_fix` which doesn't receive the current `fix_round` index. The calling code in `_run_audit_team` passes no round information to `_run_audit_fix`.
- **Impact**: The fix cycle log will always show cycle 1, making it impossible to track which fix attempt resolved which issue. The "Do NOT repeat strategies that already failed" instruction in the fix prompt becomes less effective because there is no cycle differentiation.
- **Fix**: Pass `fix_round` to `_run_audit_fix` and use it:
```python
# In _run_audit_fix signature:
async def _run_audit_fix(..., fix_round: int = 0, ...) -> float:
    ...
    cycle_entry = build_fix_cycle_entry(
        phase="Audit-Team",
        cycle_number=fix_round + 1,
        ...
    )
```

---

## MEDIUM (recommended)

### M1: `_RE_FIELD` regex cannot parse multi-line Evidence fields

- **File**: `src/agent_team/audit_team.py:349-351`
- **Issue**: The regex `r"^-\s+\*\*(\w+)\*\*:\s*(.+)$"` only captures text on the same line as the field label. Evidence fields often contain multi-line code snippets:
  ```markdown
  - **Evidence**:
    ```typescript
    return of({ token: 'fake' });
    ```
  ```
  This will capture only the empty string or the opening backticks, losing the actual evidence content.
- **Impact**: Evidence data passed to fix agents will be truncated or empty, reducing the quality of fix guidance.
- **Suggested fix**: After matching field headers, capture everything until the next `- **` or `## FINDING` header:
```python
# After collecting single-line fields, also capture multi-line content
evidence_match = re.search(
    r"-\s+\*\*Evidence\*\*:\s*(.*?)(?=^-\s+\*\*|\Z|^##)",
    section, re.MULTILINE | re.DOTALL,
)
if evidence_match:
    fields["evidence"] = evidence_match.group(1).strip()
```

### M2: Scorer prompt is defined but never called in the pipeline

- **File**: `src/agent_team/audit_team.py:270-319` and `src/agent_team/cli.py:3736-3742`
- **Issue**: The `AUDIT_SCORER_PROMPT` and `get_scorer_prompt()` function exist, but the CLI pipeline NEVER invokes a scorer LLM session. Instead, `_run_audit_team()` directly calls `parse_all_audit_reports()` and `score_audit_findings()` (Python-side scoring). The scorer prompt is dead code.
- **Impact**: No functional impact (the Python scoring is correct), but the dead prompt constant wastes space, confuses readers, and the `get_scorer_prompt()` is tested but never used in production. If the intention was to have an LLM-based scorer for dedup, that functionality is missing.
- **Recommendation**: Either remove `AUDIT_SCORER_PROMPT` and `get_scorer_prompt()`, or add a comment explaining it's reserved for future use.

### M3: Auditors run sequentially within each re-audit cycle

- **File**: `src/agent_team/cli.py:3727-3729`
- **Issue**: After a fix round, ALL auditors re-run in parallel. But there's no selective re-audit: if only 2 files were changed by the fix, all 5 auditors still re-scan the entire codebase. This is wasteful for thorough/exhaustive depth where all 5 auditors are active.
- **Impact**: Each fix cycle costs 5x the minimum necessary API budget. A 3-round fix loop with 5 auditors is 20 LLM sessions (5 initial + 5x3 re-audits) when it could be 5 initial + ~2x3 = 11.
- **Suggested fix**: Track which auditors reported fixable findings and only re-run those:
```python
# After fix dispatch, only re-run auditors that had findings
auditors_to_rerun = {f.auditor for f in fixable}
tasks = [_run_single_auditor(name) for name in auditors if name in auditors_to_rerun]
```

### M4: `_run_single_auditor` defined inside loop body is recreated each iteration

- **File**: `src/agent_team/cli.py:3688`
- **Issue**: The nested async function `_run_single_auditor` is defined inside the `for fix_round` loop body, meaning it is recreated as a new function object on every fix round iteration. While functionally correct (the `auditor_name` parameter avoids closure capture issues), it is wasteful and unconventional. Moving it outside the loop would be cleaner.
- **Impact**: Minor performance -- function object recreation. No correctness issue.

### M5: No validation that `severity_gate` in config aligns with `VALID_SEVERITIES`

- **File**: `src/agent_team/config.py:1292-1297` vs `src/agent_team/audit_team.py:67`
- **Issue**: The config validation (line 1293) uses a hardcoded tuple `("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")` for validation instead of importing `VALID_SEVERITIES` from `audit_team.py`. If new severity levels are added in the future, the validation and the actual severity logic could diverge.
- **Recommendation**: Import and use `VALID_SEVERITIES` from `audit_team`:
```python
from .audit_team import VALID_SEVERITIES
if severity_gate not in VALID_SEVERITIES:
    raise ValueError(...)
```

### M6: Health determination has a gap between "needs-fixes" and "critical"

- **File**: `src/agent_team/audit_team.py:486-491`
- **Issue**: The health logic:
  ```python
  if overall_score >= pass_threshold and critical_count == 0:
      health = "passed"
  elif critical_count > 3 or overall_score < 0.5:
      health = "critical"
  else:
      health = "needs-fixes"
  ```
  Consider: score=0.95 (above threshold) with 1 CRITICAL finding. The first condition fails (critical_count != 0). The second condition also fails (critical_count=1 <= 3 and score=0.95 >= 0.5). So health is "needs-fixes", which is correct. But consider: score=0.95 with exactly 3 CRITICALs -- also "needs-fixes". Only 4+ CRITICALs is "critical". Is 3 CRITICALs at 95% score really just "needs-fixes"? This seems like a gap where 3 CRITICAL issues should arguably be "critical" health. The `>3` should likely be `>=3`.
- **Impact**: Misleading health status when there are exactly 3 critical findings. The test `test_exactly_three_critical_is_needs_fixes` explicitly codifies this behavior, so this may be intentional, but it seems like an off-by-one from a domain perspective.

### M7: `parse_audit_findings` silently drops findings with unusual formatting

- **File**: `src/agent_team/audit_team.py:366-409`
- **Issue**: If an LLM produces a finding header (e.g., `## FINDING-001`) but omits required fields or uses slightly different formatting (e.g., `- **File path**:` instead of `- **File**:`, or `- **Req**: REQ-001` instead of `- **Requirement**: REQ-001`), the finding will be created with all empty/default values. The parser never warns about potentially malformed findings.
- **Impact**: Findings could be created with empty descriptions, missing requirement IDs, or default "FAIL" verdicts that don't reflect reality. The fix agent then gets low-quality guidance.
- **Suggested fix**: Add a warning when a finding has empty `description` or empty `file_path`:
```python
if not fields.get("description"):
    # Log warning: malformed finding
    pass
```

---

## LOW / INFO

### L1: Test auditor prompt says "run the test suite" but has no mechanism to report results back

- **File**: `src/agent_team/audit_team.py:207`
- **Issue**: The TEST_AUDITOR_PROMPT instructs `"Run the test suite if a test command is detectable"`, but the auditor is just an LLM session that writes to a file. Whether the LLM actually runs tests depends on the available tools. The prompt should clarify that the auditor should use Bash tool to execute tests.

### L2: `parse_all_audit_reports` uses `from pathlib import Path` inside function body

- **File**: `src/agent_team/audit_team.py:421`
- **Issue**: `Path` is imported locally inside `parse_all_audit_reports()` rather than at the module level. While functional, this is inconsistent with the rest of the codebase and adds minor overhead on repeated calls.

### L3: Fix prompt does not reference the original requirement text

- **File**: `src/agent_team/audit_team.py:321-339`
- **Issue**: `AUDIT_FIX_PROMPT` includes the finding description and evidence but not the original requirement text. The fix agent must re-read REQUIREMENTS.md to understand what was expected. Adding a `requirements_path` parameter would help.

### L4: `_run_audit_fix` groups by file but dispatches sequentially

- **File**: `src/agent_team/cli.py:3833`
- **Issue**: Fix groups are processed in a `for` loop (sequential). Since each group targets different files, they could run concurrently with `asyncio.gather()`, similar to the auditor dispatch pattern.
- **Impact**: Fix time scales linearly with the number of file groups instead of being parallelized.

### L5: No cap on total findings to prevent token explosion

- **File**: `src/agent_team/audit_team.py:354-411`
- **Issue**: If an auditor produces hundreds of findings (e.g., a large codebase with many convention violations), all are parsed and included in the fix prompt. There is no `_MAX_VIOLATIONS` cap like other scan functions in the codebase (which use `_MAX_VIOLATIONS=100`).
- **Suggested fix**: Add a cap:
```python
if len(findings) >= _MAX_FINDINGS:
    break
```

### L6: `@dataclass` decorator missing explicit `frozen=False` on `AuditTeamConfig`

- **File**: `src/agent_team/config.py:424`
- **Issue**: Purely stylistic. All other config dataclasses also lack `frozen`, so this is consistent. But since depth gating mutates these fields after creation, documenting this mutability would be helpful.

---

## Optimization Opportunities

### O1: Avoid re-running auditors that already PASSed all their findings

When only 2 of 5 auditors reported fixable issues, the fix-reaudit loop should only re-run those 2 auditors, not all 5. This saves 60% of the re-audit API budget.

**Implementation**: Track `auditors_with_issues = {f.auditor for f in fixable}` after filtering, then on the next loop iteration, only launch those auditors. On re-audit, merge their new findings with the unchanged findings from the other auditors.

### O2: Build fix prompt per-auditor-scope, not per-file

The current approach groups findings by file, which makes sense for avoiding edit conflicts. But an alternative is to group by auditor-scope (requirements issues together, wiring issues together), since the fix agent often needs domain context. Consider a two-level grouping: first by auditor domain, then by file.

### O3: Cache `_build_options()` call

In `_run_single_auditor`, `_build_options()` is called once per auditor (5 times with identical arguments). The non-library auditors could share a single options object. Since `_build_options` returns a new object each time (likely), this is safe but wasteful.

---

## Missing Test Coverage

### T1: No test for `LIBRARY_AUDITOR_PROMPT` missing `{requirements_path}` behavior
The test `test_all_auditor_prompts_have_requirements_path_placeholder` (line 903-910) intentionally excludes `LIBRARY_AUDITOR_PROMPT` from the list. This masks bug C1.

### T2: No test for per-milestone audit directory isolation
No test verifies that per-milestone audits don't overwrite each other's reports. This masks bug C2.

### T3: No test for dedup with empty requirement_id
The dedup tests only cover cases where `requirement_id` is non-empty. No test for the H1 scenario where multiple cross-cutting findings with `requirement_id=""` and the same `file_path` get incorrectly deduped.

### T4: No integration test for the fix loop
There are no tests that verify the fix-reaudit loop behavior end-to-end: initial audit -> fix -> re-audit -> break-on-pass. The tests only cover individual functions.

### T5: No test for `max_fix_rounds=0` behavior
When `max_fix_rounds=0`, the `for fix_round in range(0 + 1)` loop runs exactly once (audit only, no fix). This should be tested to verify no-fix semantics work correctly.

### T6: No test for resume behavior (completed_phases guard)
No test verifies that the end-of-run audit respects (or fails to respect) the `completed_phases` list on resume.

### T7: No test for `parse_audit_findings` with malformed fields
Tests cover invalid severity and verdict, but not:
- Missing `## FINDING` header (fields without header)
- Extra whitespace in field values
- Unicode in field values
- Field key typos (e.g., `**Req**:` instead of `**Requirement**:`)

### T8: No test for concurrent auditor failure isolation
No test verifies that if 1 of 5 auditors crashes, the other 4 results are still processed correctly.

### T9: No test for user override tracking completeness (H3)
No test verifies that setting `audit_team.library_auditor: true` in YAML is tracked in `user_overrides`.

---

## Summary

- **Total findings**: 25
- **CRITICAL**: 3 (C1: library prompt missing requirements_path, C2: shared audit directory, C3: completed_phases on crash)
- **HIGH**: 5 (H1: dedup aggression, H2: asyncio.run nesting, H3: incomplete user overrides, H4: no resume guard, H5: fix_cycle_number always 1)
- **MEDIUM**: 7 (M1: multi-line evidence, M2: dead scorer prompt, M3: full re-audit, M4: function recreation, M5: hardcoded severity set, M6: health gap, M7: silent malformed drops)
- **LOW/INFO**: 6 (L1-L6)
- **Optimization Opportunities**: 3 (O1-O3)
- **Missing Test Coverage**: 9 (T1-T9)

### Priority Recommendations

1. **Fix C1, C2, C3 immediately** -- these are production-breaking: C1 degrades library auditor quality, C2 loses audit data in multi-milestone runs, C3 prevents retry on crash.
2. **Fix H3 next** -- user overrides being silently discarded is a user-facing trust issue.
3. **Fix H4 and H5** -- resume correctness and fix cycle tracking are important for long-running builds.
4. **Add tests T1, T2, T3** -- these directly cover the critical bugs and would have caught them during development.
