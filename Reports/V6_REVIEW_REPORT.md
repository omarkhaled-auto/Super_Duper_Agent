# v6.0 Mode Upgrade Propagation -- Adversarial Review Report

## Summary
- Total issues found: 9
- CRITICAL: 0
- HIGH: 2
- MEDIUM: 3
- LOW: 4

Overall assessment: The implementation is solid and well-structured. The config evolution (`_dict_to_config` tuple return, `load_config` tuple return, user_overrides tracking) is correctly propagated through all callers. Depth gating logic is correct for all 4 depths. The main weakness is that **scoped scanning introduces semantic correctness issues** in scan functions that depend on cross-file context or project-level aggregation.

---

## Issues

### [HIGH] H1: `run_e2e_quality_scan` scope filtering breaks project-level E2E-005 check
- **File**: `src/agent_team/quality_checks.py:1339-1341`
- **Description**: When scope filtering limits `source_files` to only changed files, the E2E-005 "inverted auth test" check cannot see auth E2E test files that exist in **unchanged** files. The check iterates only scoped files, sets `has_auth_e2e_test = False` because the unchanged auth test file was filtered out, and then emits a false-positive warning "No auth E2E test found" even though such a test exists on disk.
- **Expected**: Scoped scanning should not produce false positives for project-level aggregate checks.
- **Actual**: Scope filtering applies before the E2E-005 aggregate check, causing it to miss auth tests in unchanged files.
- **Impact**: Users on standard depth with scoped scanning may see spurious E2E-005 violations that don't exist, eroding trust in the scan system.
- **Fix**: Either (a) skip the E2E-005 inverted check entirely when scope is active (`if scope and scope.changed_files: pass` around the E2E-005 block), or (b) use the FULL source_files list for the aggregate `has_auth_e2e_test` check while only reporting per-file E2E-001..004 violations on scoped files. Option (b) is cleaner -- collect auth test presence from the full list, but only emit per-file violations for scoped files.

### [HIGH] H2: `run_dual_orm_scan` scope filtering on detection phase causes scan skip
- **File**: `src/agent_team/quality_checks.py:1967-1969`
- **Description**: Scope filtering is applied to `all_files` **before** `_detect_data_access_methods(project_root, all_files)` at line 1972. If only ORM entity files were changed (but the raw SQL query file was NOT changed), the filtered `all_files` won't contain the raw SQL file, so `has_raw` will be False, and the scan returns `[]` at line 1975 even though there IS a dual-ORM pattern and the changed entity file might have a type mismatch.
- **Expected**: Data access method detection should use the FULL file list to determine if dual-ORM scanning is warranted. Only the violation reporting phase should be scoped.
- **Actual**: Detection uses the scoped (filtered) file list, causing premature scan exit.
- **Impact**: Changed entity files with type mismatches between ORM and raw SQL go undetected in scoped mode.
- **Fix**: Move the scope filter AFTER the detection phase. Change the order to:
  1. Walk all_files (full project)
  2. Detect data access methods with full all_files
  3. Find entity_files from full source_files
  4. **Then** apply scope filter to entity_files before violation scanning

### [MEDIUM] M1: `run_relationship_scan` scope filtering breaks cross-file FK/nav matching
- **File**: `src/agent_team/quality_checks.py:2363-2365`
- **Description**: `entity_files` is scoped to changed files only. The relationship scan collects `entity_info` (FK props, nav props, config calls) from scoped entity files and then checks for missing inverse relationships. If entity A (changed) has a FK pointing to entity B (unchanged), entity B won't be in `entity_info`, and the scan may report "FK has no navigation property" even though entity B defines the inverse nav property.
- **Expected**: Relationship checks that depend on cross-file entity references should have full visibility.
- **Actual**: Only changed entity files contribute to `entity_info`, breaking cross-file relationship matching.
- **Impact**: False-positive DB-006/DB-007/DB-008 violations when relationships span changed and unchanged files.
- **Fix**: Collect `entity_info` from ALL entity_files (full context), but only REPORT violations for entity_files that are in the scoped set. This preserves full cross-reference context while limiting noise to changed files.

### [MEDIUM] M2: PRD reconciliation quality gate has no crash isolation
- **File**: `src/agent_team/cli.py:3932-3943`
- **Description**: The quality gate code at lines 3935-3941 reads REQUIREMENTS.md (`stat()` + `read_text()`) outside any try/except block. If the file is deleted or becomes unreadable between the `is_file()` check (line 3935) and the `stat()`/`read_text()` calls (lines 3936-3937), an OSError propagates uncaught up the call stack, potentially crashing the entire post-orchestration section.
- **Expected**: Quality gate failures should be crash-isolated like all other post-orchestration blocks.
- **Actual**: No try/except wraps the file I/O in the quality gate check.
- **Impact**: Race condition (TOCTOU) could crash post-orchestration. Low probability but violates the "crash isolation" design principle (Rule 7 in the implementation plan).
- **Fix**: Wrap lines 3933-3943 in a try/except that defaults `_should_run_prd_recon = True` (safe fallback: run reconciliation if quality gate crashes).

### [MEDIUM] M3: `ScanScope.mode` documented but never consumed by any scan function
- **File**: `src/agent_team/quality_checks.py:50` (ScanScope.mode)
- **Description**: The `ScanScope.mode` field supports three values: "full", "changed_only", and "changed_and_imports". The "changed_and_imports" mode is described as including "changed files + their importers". However, NO scan function reads `scope.mode` -- all functions only check `scope.changed_files`. The cli.py scope computation sets mode to "changed_and_imports" for standard depth (line 3800), implying broader scanning that never actually happens.
- **Expected**: If the mode specifies "changed_and_imports", the import graph should be traversed to include files that import the changed files.
- **Actual**: Mode is set but never read. "changed_and_imports" behaves identically to "changed_only".
- **Impact**: Standard depth scoping is documented as scanning importers but doesn't. Users expecting broader coverage get narrower-than-documented scanning.
- **Fix**: Either (a) implement import graph traversal in `compute_changed_files` or a new helper, or (b) remove the "changed_and_imports" mode and document that scoping is always "changed_only" to set correct expectations.

### [LOW] L1: Quick mode computes scope unnecessarily
- **File**: `src/agent_team/cli.py:3792-3804`
- **Description**: When depth is "quick" and `scan_scope_mode` is "auto", the condition at line 3793 is True (`depth in ("quick", "standard")`), so `compute_changed_files()` runs (2 subprocess calls). But quick mode disables ALL scans via depth gating -- no scan will ever read `scan_scope`. The subprocess calls are wasted work.
- **Expected**: Scope computation should be skipped when all scans are disabled.
- **Actual**: Two `git` subprocess calls execute for no benefit in quick mode.
- **Impact**: ~10ms wasted per quick-mode run. Negligible but technically inefficient.
- **Fix**: Add `depth != "quick"` check or check if any scan is still enabled before computing scope.

### [LOW] L2: Redundant `import re as _re_mod` in cli.py
- **File**: `src/agent_team/cli.py:3938`
- **Description**: The PRD reconciliation quality gate does `import re as _re_mod` to use `_re_mod.search()`. But `re` is already imported at `cli.py:13`. The `_re_mod` alias works but is unnecessary.
- **Expected**: Use the existing `re` import.
- **Actual**: Creates a redundant alias `_re_mod`.
- **Impact**: No functional impact, just code smell.
- **Fix**: Replace `import re as _re_mod` and `_re_mod.search(...)` with `re.search(...)`.

### [LOW] L3: `run_e2e_quality_scan` has scope parameter but is never called from cli.py
- **File**: `src/agent_team/quality_checks.py:1328`
- **Description**: `run_e2e_quality_scan` was given a `scope` parameter as part of the v6.0 upgrade, but it is never called from the post-orchestration pipeline in cli.py (grep confirms zero usages). The scope parameter is dead code for this function.
- **Expected**: If the function isn't called in post-orchestration, it shouldn't need scope.
- **Actual**: Scope parameter added but unused at the call site.
- **Impact**: No functional impact, but the added scope filtering logic (lines 1339-1341) is unreachable from the production pipeline. It also interacts poorly with E2E-005 (see H1), so it's actually harmful if someone starts calling it with scope in the future.
- **Fix**: Either (a) remove the scope parameter from `run_e2e_quality_scan` since it's not used in production, or (b) if it will be used in the future, fix H1 first.

### [LOW] L4: Inconsistent scope_set construction across scan functions
- **File**: `src/agent_team/quality_checks.py` (multiple functions)
- **Description**: Three different patterns for building the scope set:
  - Pattern A (mock/ui/e2e/default_value/relationship): `scope_set = set(scope.changed_files)` -- uses paths as-is (already resolved)
  - Pattern B (asset): `scope_set = set(f.resolve() for f in scope.changed_files)` -- resolves again (redundant since `compute_changed_files` already resolves)
  - Pattern C (dual_orm): `scope_set = set(f.resolve() for f in scope.changed_files)` -- same as B
- **Expected**: All functions should use the same pattern.
- **Actual**: Patterns B and C do redundant `.resolve()` calls on already-resolved paths.
- **Impact**: No functional impact (both work correctly), but inconsistent code style.
- **Fix**: Standardize on Pattern A since paths from `compute_changed_files` are already resolved.

---

## Verified Correct (No Issues Found)

1. **`_dict_to_config()` tuple return**: All production and test callers correctly unpack `(cfg, user_overrides)`. No missed callers.
2. **`load_config()` tuple return**: Single production caller at cli.py:2868 correctly unpacks. All test callers updated.
3. **`apply_depth_quality_gating()` user_overrides**: Correctly passed at both call sites (cli.py:3409 and cli.py:389). `_gate` helper correctly checks user_overrides before applying.
4. **Backward compat migration**: `milestone.mock_data_scan` in YAML correctly migrates to `post_orchestration_scans` when no explicit `post_orchestration_scans` section present.
5. **OR gate for mock/UI scans**: `config.post_orchestration_scans.X or config.milestone.X` correctly supports both old and new config locations.
6. **`scan_scope_mode` validation**: Correctly rejects invalid values in `_dict_to_config()` with clear error message.
7. **Depth gating for all 4 levels**: Quick/standard/thorough/exhaustive all gate correctly per spec.
8. **E2E auto-enablement**: Thorough and exhaustive correctly auto-enable E2E. Quick correctly disables. Standard leaves default (False).
9. **PostOrchestrationScanConfig dataclass**: Correctly defined, correctly added to AgentTeamConfig, correctly loaded from YAML.
10. **Crash isolation**: compute_changed_files failure falls back to None (full scan). Each scan wrapped in its own try/except (pre-existing pattern preserved).

---

## Verdict

**MINOR FIXES NEEDED** -- No critical issues. Two HIGH issues (H1, H2) should be fixed before production use as they can cause false-positive violations in scoped mode, undermining trust. The MEDIUM issues are worth addressing but non-blocking. LOW issues are cosmetic/cleanup.

Priority fix order: H2 > H1 > M1 > M2 > M3 > L1-L4
