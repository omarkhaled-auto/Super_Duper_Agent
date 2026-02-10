# Mode Upgrade Propagation (v6.0) -- Implementation Report

## Implementation Summary

- **Modified**: `config.py` -- new `PostOrchestrationScanConfig`, `scan_scope_mode` on `DepthConfig`, extended `apply_depth_quality_gating` with user_overrides respect, `_dict_to_config` returns `tuple[AgentTeamConfig, set[str]]`, `load_config` returns tuple
- **Modified**: `quality_checks.py` -- `ScanScope` dataclass, `compute_changed_files()`, `scope` param on 7 scan functions
- **Modified**: `cli.py` -- scope computation block, scan call updates with `scope=scan_scope`, PRD reconciliation quality gate, E2E auto-enablement, OR gate for mock/UI scans
- **New test files**: `test_depth_gating.py`, `test_scan_scope.py`, `test_config_evolution.py`, `test_mode_propagation_wiring.py`
- **Updated test files**: `test_wiring_verification.py`, `test_database_wiring.py` (marker patterns updated for scope param)

## Mode x Upgrade Propagation Matrix (verified)

| Upgrade | Quick | Standard | Thorough | Exhaustive |
|---------|-------|----------|----------|------------|
| Mock scan | SKIP (gated) | SCOPED | FULL | FULL |
| UI scan | SKIP (gated) | SCOPED | FULL | FULL |
| Deploy scan | SKIP (gated) | FULL | FULL | FULL |
| Asset scan | SKIP (gated) | SCOPED | FULL | FULL |
| PRD recon | SKIP (gated) | SKIP (gated) | CONDITIONAL | FULL |
| DB scans (3) | SKIP (gated) | SCOPED | FULL | FULL |
| E2E testing | SKIP | OPT-IN | AUTO-ENABLED | AUTO-ENABLED |
| Review retries | 0 | 1 | 2 | 3 |
| Prompt policies | ALL | ALL | ALL | ALL |

## Test Results

- **New tests written**: 166 across 4 new test files
  - `test_depth_gating.py`: 30 tests (quick/standard/thorough/exhaustive gating, user overrides, backward compat)
  - `test_scan_scope.py`: 45 tests (ScanScope dataclass, compute_changed_files, scoped scan functions, parametrized)
  - `test_config_evolution.py`: 43 tests (PostOrchestrationScanConfig, _dict_to_config tuple, user_overrides tracking x6 sections, backward compat migration, scan_scope_mode validation, load_config tuple)
  - `test_mode_propagation_wiring.py`: 48 tests (scope computation, PRD recon quality gate, gate condition migration, E2E auto-enablement, scan scope passing, cross-feature integration)
- **Updated existing tests**: 6 tests in `test_wiring_verification.py` + `test_database_wiring.py` (marker patterns for scope param and OR gate)
- **All passing**: 3648/3648
- **Pre-existing failures**: 2 (test_mcp_servers.py -- sequential_thinking always included)
- **Regressions**: 0

## Wiring Verification

- **Execution position**: VERIFIED -- `apply_depth_quality_gating()` runs BEFORE `compute_changed_files()`, scope computed ONCE and reused across all scans
- **Config gating**: VERIFIED -- 8 scans gated by quick mode, PRD recon gated by standard+quick, OR gate for mock/UI backward compat
- **Crash isolation**: VERIFIED -- `compute_changed_files()` failure falls back to full scan, each scan in own try/except
- **Backward compatibility**: VERIFIED -- `milestone.mock_data_scan` YAML migrates to `post_orchestration_scans`, `load_config()` tuple unpacking works, `apply_depth_quality_gating()` without user_overrides still works

## Changes Detail

### config.py

1. `PostOrchestrationScanConfig` dataclass (line 294) -- `mock_data_scan: bool = True`, `ui_compliance_scan: bool = True`
2. `scan_scope_mode: str = "auto"` on `DepthConfig` (line 31) -- values: "auto", "full", "changed"
3. `post_orchestration_scans` field on `AgentTeamConfig`
4. `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]` with user_overrides tracking for 6 sections (quality, milestone, integrity_scans, e2e_testing, database_scans, post_orchestration_scans)
5. `load_config()` returns `tuple[AgentTeamConfig, set[str]]`
6. `apply_depth_quality_gating()` -- `user_overrides` param, `_gate()` helper, full 4-depth handling (quick/standard/thorough/exhaustive)
7. Backward compat: `milestone.mock_data_scan`/`ui_compliance_scan` migrates to `post_orchestration_scans` when no explicit section
8. Validation: `scan_scope_mode` must be in ("auto", "full", "changed")

### quality_checks.py

1. `import subprocess` added
2. `ScanScope` dataclass (line 37) -- `mode: str = "full"`, `changed_files: list[Path]`
3. `compute_changed_files(project_root)` -- `git diff --name-only HEAD` + `git ls-files --others`, returns absolute paths, handles FileNotFoundError/SubprocessError/TimeoutExpired/OSError
4. 7 scan functions updated with `scope: ScanScope | None = None`:
   - `run_mock_data_scan`, `run_ui_compliance_scan`, `run_e2e_quality_scan`: filter via `scope_set` after `_iter_source_files()`
   - `run_asset_scan`: `scope_set` built once before `os.walk`
   - `run_dual_orm_scan`: filter `all_files` after `os.walk`
   - `run_default_value_scan`, `run_relationship_scan`: filter `entity_files` after `_find_entity_files()`

### cli.py

1. `config, user_overrides = load_config(...)` tuple unpacking (line 2868)
2. `user_overrides` param on `_run_interactive()` (line 385)
3. `apply_depth_quality_gating(depth, config, user_overrides)` at both call sites
4. Scope computation block (lines 3788-3804): auto mode + quick/standard -> compute, changed mode -> always compute, full mode -> never compute
5. All 7 scan calls pass `scope=scan_scope`
6. Mock/UI scan gates: `config.post_orchestration_scans.X or config.milestone.X` (OR gate)
7. PRD reconciliation quality gate: thorough depth checks REQUIREMENTS.md >500 bytes + REQ-xxx pattern

## Verdict

**SHIP IT** -- All 3648 tests pass, zero regressions, full backward compatibility preserved.
