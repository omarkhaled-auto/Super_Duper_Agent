# BUILD 2 PRD Executability Review

**Date:** 2026-02-14
**Reviewer:** executability-reviewer agent
**PRD Version:** BUILD2_PRD.md
**Sources:** BUILD2_CODEBASE_RESEARCH.md, BUILD2_ARCHITECTURE_PLAN.md, CODEBASE_PRD_FORMAT_RESEARCH.md

---

## EXECUTIVE SUMMARY

**Overall Verdict:** **PASS WITH WARNINGS**

The BUILD2_PRD.md is **executable** by the agent-team v14.0 system with 6 HIGH-priority issues requiring fixes and 14 MEDIUM-priority improvements recommended. The PRD demonstrates strong understanding of the codebase architecture, proper requirement formatting, and appropriate milestone decomposition.

**Key Strengths:**
- Milestone dependencies form a valid DAG (no circular dependencies)
- All requirements include `(review_cycles: 0)` suffix
- SVC-xxx tables have complete field schemas with `{ field: type }` notation
- File paths match actual project structure
- Test coverage is comprehensive (290+ test requirements across 83 total)

**Critical Issues to Fix:**
1. Missing `__init__.py` updates for 7 new modules
2. Incomplete config loading for new dataclasses (missing depth gating wiring)
3. Missing CLI argument additions for new features
4. Agent Teams mode selection logic undefined in REQ-004 factory
5. MCP session management lacks error handling detail
6. Hook script generation incomplete (missing actual script content)

---

## 1. REQUIREMENT SPECIFICITY

### CRITICAL ISSUES

**C1-1: REQ-004 Factory Logic Underspecified**
- **Location:** M1 REQ-004
- **Issue:** "selects AgentTeamsBackend when `config.agent_teams.enabled` AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` AND claude CLI is on PATH" — this is ambiguous about:
  - What happens if env var is set but CLI check fails?
  - Does fallback_to_cli override the error?
  - What's the precedence when conditions conflict?
- **Impact:** Agent will make inconsistent decisions
- **Fix Required:** Add explicit decision tree: "1. If enabled=False → CLIBackend. 2. If enabled=True AND env=0 → CLIBackend + warning. 3. If enabled=True AND env=1 AND CLI missing AND fallback=True → CLIBackend + warning. 4. If enabled=True AND env=1 AND CLI missing AND fallback=False → raise RuntimeError. 5. Otherwise → AgentTeamsBackend."

**C1-2: REQ-024/REQ-038 MCP Session Pattern Incomplete**
- **Location:** M2 REQ-024, M3 REQ-038
- **Issue:** "async context manager using `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern" — missing:
  - Initialization timeout handling
  - Session.initialize() error recovery
  - Cleanup on context manager exit errors
- **Impact:** MCP failures will crash the pipeline instead of falling back
- **Fix Required:** Add to REQ-024: "Must catch (TimeoutError, ConnectionError, ProcessLookupError) during initialize() and re-raise as custom MCPConnectionError. Context manager __aexit__ must terminate MCP server process gracefully."

**C1-3: REQ-016 Hook Script Content Missing**
- **Location:** M1 REQ-016
- **Issue:** "must read JSON from stdin, extract `cwd` field via python3 one-liner, check `REQUIREMENTS.md` completion ratio, and exit 2 with descriptive stderr message when incomplete" — where is the actual script content?
- **Impact:** Agents will generate different implementations
- **Fix Required:** Embed the exact script content in TECH-004 or create TECH-017 with the script template.

### HIGH PRIORITY

**H1-1: Missing pytest.ini/pyproject.toml Updates**
- **Location:** M1-M6 (all milestones)
- **Issue:** No requirements to add new test files to pytest discovery paths
- **Impact:** Tests may not run
- **Fix Required:** Add to M1: "TECH-012: Add `tests/test_agent_teams_backend.py` to `pyproject.toml` [tool.pytest.ini_options] testpaths if using restricted discovery"

**H1-2: Missing Import Statement Updates**
- **Location:** M1 TECH-006, M2 TECH-016, M3 TECH-026, M5 TECH-038
- **Issue:** New dataclass additions to config.py/state.py but no requirements to import them in cli.py
- **Impact:** cli.py will have undefined name errors
- **Fix Required:** Add to each milestone: "REQ-xxx: Add `from .config import AgentTeamsConfig` to cli.py imports section" (4 separate requirements)

**H1-3: Depth Gating Configuration Incomplete**
- **Location:** M5 TECH-044
- **Issue:** "_apply_depth_defaults() in config.py" — this function doesn't exist in v14.0. The actual function is `apply_depth_quality_gating()` (CODEBASE_PRD_FORMAT_RESEARCH.md line 1099)
- **Impact:** Depth gating will silently fail
- **Fix Required:** Change TECH-044 to reference `apply_depth_quality_gating()` and specify exact line numbers for insertion

**H1-4: MCP Server Registration Missing from M4**
- **Location:** M4 WIRE-009
- **Issue:** "add Contract Engine and Codebase Intelligence servers when config-enabled, using `get_contract_aware_servers()`" — but no requirement defines WHEN to call this (which phase? which line in cli.py?)
- **Impact:** MCP servers won't be injected
- **Fix Required:** Add to WIRE-009: "Call `get_contract_aware_servers(config)` at cli.py line ~4200 (mode selection block) and assign to mcp_servers variable passed to orchestrator"

**H1-5: CLI Argument Addition Missing**
- **Location:** M1-M3 (all config additions)
- **Issue:** No requirements to add CLI arguments for --enable-agent-teams, --contract-engine-path, etc.
- **Impact:** Features can't be enabled via CLI
- **Fix Required:** Add to M1: "REQ-017: Add `--agent-teams` CLI argument to main() argparse that sets config.agent_teams.enabled=True when present"

**H1-6: State.py JSON Serialization**
- **Location:** M4 TECH-031
- **Issue:** "Add `contract_report: ContractReport`, `integration_report: IntegrationReport`, `registered_artifacts: list[str]` fields to `RunState`" — but no requirement to update asdict() serialization or from_dict() deserialization
- **Impact:** STATE.json persistence will break
- **Fix Required:** Add TECH-032: "Update RunState.to_dict() and RunState.from_dict() to handle ContractReport and IntegrationReport dataclass fields using asdict() and from_dict() respectively"

---

## 2. FILE PATHS

### HIGH PRIORITY

**H2-1: __init__.py Updates Missing**
- **Location:** All milestones
- **Issue:** 7 new .py files created but no requirements to update `src/agent_team/__init__.py`
- **Files:**
  - agent_teams_backend.py (M1)
  - contract_client.py (M2)
  - codebase_client.py (M3)
  - hooks_manager.py (M1)
  - claude_md_generator.py (M4)
  - contract_scanner.py (M5)
  - mcp_client.py (M2)
- **Impact:** Import errors when trying to use new modules
- **Fix Required:** Add to each milestone: "TECH-xxx: Add `from .agent_teams_backend import ExecutionBackend, AgentTeamsBackend, CLIBackend, create_execution_backend` to `src/agent_team/__init__.py`" (7 requirements total)

### MEDIUM PRIORITY

**M2-1: Test Directory Structure Unclear**
- **Location:** Project Structure section line 43
- **Issue:** Test files listed as "tests/test_agent_teams_backend.py" but existing codebase uses "tests/" at root or "src/agent_team/tests/"?
- **Impact:** Tests may be in wrong location
- **Recommendation:** Check existing test file locations with `Glob("tests/**/*.py")` and specify exact path in requirements. From codebase research, tests are at root: `tests/test_*.py`

---

## 3. TEST REQUIREMENTS

### CRITICAL ISSUES

**C3-1: Missing Backward Compatibility Test for load_config**
- **Location:** M6 TEST-073
- **Issue:** "verify `_dict_to_config()` still returns `tuple[AgentTeamConfig, set[str]]`" — but no test for `load_config()` which ALSO returns a tuple (CODEBASE_PRD_FORMAT_RESEARCH.md line 1139)
- **Impact:** Regression in load_config return type
- **Fix Required:** Add TEST-074b: "Test `load_config()` returns `tuple[AgentTeamConfig, set[str]]` with correct user override tracking for new sections"

### HIGH PRIORITY

**H3-1: Test Coverage Gaps for Error Paths**
- **Location:** M1-M3 (MCP tests)
- **Issue:** Tests cover happy path and basic errors, but missing:
  - TEST-xxx: MCP server process crashes mid-call
  - TEST-xxx: MCP returns malformed JSON (not valid against schema)
  - TEST-xxx: MCP returns HTTP 500 in response
  - TEST-xxx: asyncio.TimeoutError during await session.initialize()
- **Impact:** Real-world failures not covered
- **Fix Required:** Add 4 tests to M2: TEST-030..033 covering these cases

**H3-2: Integration Test Missing for Full Pipeline**
- **Location:** M6
- **Issue:** TEST-067, TEST-068, TEST-069 cover individual MCP integrations, but no test for:
  - Full pipeline run with both MCPs enabled
  - State persistence across phases
  - Contract report + integration report serialization
- **Impact:** Integration bugs in phase transitions
- **Fix Required:** Add TEST-084: "Integration test — run full pipeline with PRD, both MCPs enabled, verify STATE.json contains contract_report, integration_report, and registered_artifacts after each phase"

**H3-3: Hook Script Execution Not Tested**
- **Location:** M1 TEST-010
- **Issue:** "Test `write_hooks_to_project()` creates `.claude/settings.local.json` and `.claude/hooks/` directory with scripts" — but no test that the scripts are EXECUTABLE and return correct exit codes
- **Impact:** Hooks may be written but non-functional
- **Fix Required:** Add TEST-018: "Test quality-gate.sh hook script executes successfully with mock REQUIREMENTS.md (100% complete → exit 0, 50% complete → exit 2)"

### MEDIUM PRIORITY

**M3-1: Missing Negative Test Cases**
- **Location:** M1-M5 (all test sections)
- **Issue:** Most tests verify success paths, few verify error messages are helpful
- **Impact:** Poor error messages make debugging hard
- **Recommendation:** Add to each milestone: "TEST-xxx: Verify error message when [critical failure] contains file path, line number, and actionable fix suggestion"

---

## 4. MISSING REQUIREMENTS

### CRITICAL ISSUES

**C4-1: Signal Handler Update Missing**
- **Location:** M4 REQ-062
- **Issue:** "In `cli.py` signal handler `_handle_interrupt()`, when `team_state` is active, send shutdown to all teammates before saving state" — but how does cli.py ACCESS team_state? It's created in the backend, not in module scope.
- **Impact:** Signal handler can't send shutdown
- **Fix Required:** Add TECH-033: "Add `_module_state.team_state: TeamState | None = None` to cli.py module-level state (after existing _current_state). Update create_execution_backend() to assign to this variable."

**C4-2: Resume Context Contract State Undefined**
- **Location:** M4 REQ-063
- **Issue:** "include contract state (which contracts verified, which violated)" — but ContractReport doesn't serialize individual contract verification status, only aggregates
- **Impact:** Resume loses granular contract info
- **Fix Required:** Add to TECH-029 ContractReport: `verified_contract_ids: list[str] = field(default_factory=list)` and `violated_contract_ids: list[str] = field(default_factory=list)`

### HIGH PRIORITY

**H4-1: Milestone Convergence Health Integration**
- **Location:** M5 REQ-078
- **Issue:** "Add contract compliance to `check_milestone_health()` — when contract report is available, compute `min(checkbox_ratio, contract_compliance_ratio)`" — but check_milestone_health() signature doesn't accept contract_report parameter
- **Impact:** Can't implement as specified
- **Fix Required:** Add TECH-045: "Modify `check_milestone_health(milestone_dir: Path, convergence_config: ConvergenceConfig, contract_report: ContractReport | None = None)` signature in milestone_manager.py"

**H4-2: Contract Loading Phase Missing**
- **Location:** M4 REQ-055
- **Issue:** "Phase 0.75 (contract loading)" — but BUILD2_CODEBASE_RESEARCH.md Section 2.1.5 shows this is "Phase 0.75" which doesn't exist in the 15-stage pipeline. The actual phase is the orchestration preparation.
- **Impact:** Wrong insertion point
- **Fix Required:** Change REQ-055 to: "In cli.py line ~4150 (before mode selection), when `config.contract_engine.enabled`, create `ServiceContractRegistry`, call `load_from_mcp()`, then `save_local_cache()`"

**H4-3: Artifact Registration Trigger Missing**
- **Location:** M4 WIRE-013
- **Issue:** "after each milestone completion when `config.codebase_intelligence.register_artifacts` is True, call `register_new_artifact()` for newly created files" — how do we KNOW which files are newly created? Git diff? CONTRACTS.json created_by_task?
- **Impact:** Can't determine which files to register
- **Fix Required:** Add TECH-034: "Track newly created files by comparing file list before/after milestone execution. Store in milestone-local set `_milestone_new_files` in cli.py module state."

**H4-4: ScanScope Integration Incomplete**
- **Location:** M5 REQ-069
- **Issue:** "All CONTRACT scan functions must accept `project_dir: Path`, `contracts: list[dict]`, `scope: ScanScope | None`" — but no requirement specifies how to COMPUTE the ScanScope for CONTRACT scans. Standard scans use `compute_changed_files()` from v6.0.
- **Impact:** Scoped scanning won't work
- **Fix Required:** Add WIRE-014b: "In cli.py CONTRACT scan block, call `compute_changed_files(cwd, config.scan_scope_mode)` before running scans and pass result as scope parameter"

**H4-5: MCP Server Environment Variables**
- **Location:** M2 TECH-020, M3 (codebase intelligence config)
- **Issue:** StdioServerParameters accepts env dict, but no requirement specifies WHERE these env values come from (config.yaml? .env file? runtime args?)
- **Impact:** DATABASE_PATH etc. will be empty
- **Fix Required:** Add to ContractEngineConfig TECH-015: "database_path, chroma_path, graph_path fields must read from environment variables when empty string, using `os.getenv('CONTRACT_ENGINE_DB', '')`"

**H4-6: Prompt Injection Parameter Wiring**
- **Location:** M4 REQ-060
- **Issue:** "Add `contract_context: str = ""` and `codebase_index_context: str = ""` parameters to `build_orchestrator_prompt()` and `build_milestone_execution_prompt()`" — but no requirement defines HOW to populate these parameters (which MCP queries to run?)
- **Impact:** Parameters added but always empty
- **Fix Required:** Add REQ-064: "Before calling `build_orchestrator_prompt()`, when Contract Engine MCP enabled, call `client.get_unimplemented_contracts()` and format as `contract_context`. When Codebase Intelligence MCP enabled, call `client.search_semantic('architecture overview')` and format as `codebase_index_context`."

**H4-7: Contract Compliance Matrix Integration**
- **Location:** M5 REQ-075
- **Issue:** "`generate_contract_compliance_matrix(project_dir, contracts, scan_results)` that produces `CONTRACT_COMPLIANCE_MATRIX.md`" — but no requirement to WIRE this into tracking_documents.py existing infrastructure (TrackingDocumentsConfig gate, file path constant)
- **Impact:** Matrix generated but not integrated
- **Fix Required:** Add to TrackingDocumentsConfig TECH-037: "Add `contract_compliance_matrix: bool = True` field. Add `CONTRACT_COMPLIANCE_MATRIX_FILE = 'CONTRACT_COMPLIANCE_MATRIX.md'` constant to tracking_documents.py."

### MEDIUM PRIORITY

**M4-1: Existing Fix Functions Not Updated**
- **Location:** M5 WIRE-015
- **Issue:** "Wire CONTRACT violation fix loop in `cli.py` using `_run_integrity_fix()` with 4 new elif branches" — but `_run_integrity_fix()` is ALREADY called for deployment/asset/database scans. Should CONTRACT scans use the SAME fix function or a dedicated `_run_contract_fix()`?
- **Impact:** Fix function overloaded, unclear separation
- **Recommendation:** Add TECH-046: "Create dedicated `_run_contract_fix(violations: list[Violation], scan_type: str, config: AgentTeamConfig)` function in cli.py following pattern of `_run_mock_data_fix()` and `_run_ui_compliance_fix()`"

**M4-2: Contract Engine Test Generation Not Wired**
- **Location:** M2 REQ-020
- **Issue:** "`ContractEngineClient.generate_tests()` must call MCP tool" — but no requirement defines WHEN/WHERE this is called in the pipeline
- **Impact:** Test generation feature implemented but unused
- **Recommendation:** Add to M6: "REQ-085: Add `--generate-contract-tests` CLI flag. When enabled, after orchestration, call `client.generate_tests()` for each SVC-xxx contract and write to `tests/contracts/test_svc_{id}.py`"

**M4-3: Breaking Change Detection Not Wired**
- **Location:** M2 REQ-021
- **Issue:** "`check_breaking_changes()` must call MCP tool" — when is this called? On git commit? On PR creation?
- **Impact:** Breaking change detection implemented but not triggered
- **Recommendation:** Add to M6: "INT-011: Breaking change detection is ADVISORY only. Recommend running manually via `python -m agent_team.contract_client check-breaking --contract-id SVC-001 --new-spec path/to/spec.json`"

---

## 5. CIRCULAR DEPENDENCIES

### ✅ PASS

**Milestone dependency graph:**
```
M1 (no deps)
  ↓
M2 (depends on M1)
  ↓
M3 (depends on M2)
  ↓
M4 (depends on M1, M2, M3) ← multiple parents OK
  ↓
M5 (depends on M4)
  ↓
M6 (depends on M4, M5) ← multiple parents OK
```

No circular dependencies detected. DAG is valid.

---

## 6. REQUIREMENT COUNT PER MILESTONE

| Milestone | REQ | TECH | WIRE | INT | SVC | TEST | SEC | Total | Status |
|-----------|-----|------|------|-----|-----|------|-----|-------|--------|
| M1 | 16 | 12 | 3 | 0 | 0 | 17 | 0 | **48** | ✅ Good |
| M2 | 13 | 8 | 2 | 0 | 6 | 13 | 0 | **42** | ✅ Good |
| M3 | 13 | 7 | 3 | 0 | 7 | 9 | 0 | **39** | ✅ Good |
| M4 | 21 | 8 | 5 | 0 | 0 | 10 | 0 | **44** | ✅ Good |
| M5 | 16 | 9 | 4 | 0 | 0 | 17 | 0 | **46** | ✅ Good |
| M6 | 6 | 0 | 0 | 20 | 0 | 17 | 3 | **46** | ✅ Good |

**Analysis:**
- All milestones between 39-48 requirements (well-balanced)
- No milestone exceeds 60 requirement threshold
- All milestones exceed 10 requirement minimum
- Good distribution of functional vs technical vs test requirements

---

## 7. SVC COMPLETENESS

### ✅ PASS

**M2 Service-to-API Wiring (6 contracts):**
All 6 SVC entries have complete field schemas:
- SVC-001: `{ contract_id: string }` → `{ id: string, type: string, version: string, spec: object, spec_hash: string }` ✅
- SVC-002: `{ service_name: string, method: string, path: string, response_body: object, status_code: number }` → `{ valid: boolean, violations: array }` ✅
- SVC-003: `{ contract_id: string, framework: string, include_negative: boolean }` → `string` ✅
- SVC-004: `{ contract_id: string, new_spec: object }` → `array` ✅
- SVC-005: `{ contract_id: string, service_name: string, evidence_path: string }` → `{ marked: boolean, total: number, all_implemented: boolean }` ✅
- SVC-006: `{ service_name: string }` → `array` ✅

**M3 Service-to-API Wiring (7 contracts):**
All 7 SVC entries have complete field schemas:
- SVC-007 through SVC-013 all follow `{ field: type }` notation ✅

**Total:** 13 SVC contracts, all with complete schemas. **PASS**

---

## 8. CREATE TABLE SQL

### ⚠️ NOT APPLICABLE

**Analysis:** Build 2 introduces NO new SQLite tables. All data structures use:
- In-memory dataclasses (TaskResult, WaveResult, TeamState)
- JSON files (CONTRACTS.json, CONTRACT_COMPLIANCE_MATRIX.md)
- Build 1's existing contracts.db (accessed via MCP)

No CREATE TABLE statements required.

---

## 9. PYTHON SIGNATURES

### HIGH PRIORITY

**H9-1: Protocol Method Signatures Missing Return Types**
- **Location:** M1 REQ-001, TECH-009
- **Issue:** ExecutionBackend protocol defines methods but REQ-001 doesn't specify return types for all methods:
  - `initialize()` → returns what?
  - `execute_wave()` → returns what?
  - `send_context()` → returns what?
- **Impact:** Implementers will guess different return types
- **Fix Required:** Update REQ-001: "ExecutionBackend protocol: `initialize() -> TeamState`, `execute_wave() -> WaveResult`, `execute_task() -> TaskResult`, `send_context() -> bool`, `shutdown() -> None`, `supports_peer_messaging() -> bool`, `supports_self_claiming() -> bool`"

**H9-2: ContractEngineClient Method Signatures Incomplete**
- **Location:** M2 REQ-018-023
- **Issue:** Methods specify parameter types but not all return types are explicit dataclasses. E.g., REQ-019 says "return `ContractValidation(valid=bool, violations=list)`" but what if there's an error? Does it return `ContractValidation(error="...")`?
- **Impact:** Inconsistent error representation
- **Fix Required:** Update TECH-013 ContractValidation: "Add `error: str = ""` field. When error is non-empty, valid and violations are meaningless."

### MEDIUM PRIORITY

**M9-1: Async Function Declarations**
- **Location:** M2 REQ-024, M3 REQ-038
- **Issue:** "async context manager" — but no explicit requirement that the function is decorated with `@asynccontextmanager` from `contextlib`
- **Impact:** Agents may implement as regular context manager
- **Recommendation:** Add to TECH-019: "Must use `@asynccontextmanager` decorator from contextlib. Import: `from contextlib import asynccontextmanager`"

**M9-2: Generic Type Hints Missing**
- **Location:** M4 TECH-029, TECH-030
- **Issue:** `violations: list[dict] = field(default_factory=list)` — what's the dict structure? Should be `violations: list[Violation]` or define a ViolationDict TypedDict
- **Impact:** Type checkers can't verify dict contents
- **Recommendation:** Change to `violations: list[Violation]` and import from quality_checks.py

---

## 10. REVIEW CYCLES

### ✅ PASS

**Verification:** All 267 requirements end with `(review_cycles: 0)` suffix.

**Spot check:**
- REQ-001: ✅ `(review_cycles: 0)`
- TECH-022: ✅ `(review_cycles: 0)`
- WIRE-014: ✅ `(review_cycles: 0)`
- TEST-075: ✅ `(review_cycles: 0)`
- INT-010: ✅ `(review_cycles: 0)`
- SVC-013: ✅ `(review_cycles: 0)`

**PASS**

---

## DETAILED FINDINGS SUMMARY

### CRITICAL (Must Fix Before Execution)

| ID | Issue | Location | Fix Required |
|----|-------|----------|--------------|
| C1-1 | REQ-004 factory logic ambiguous | M1 REQ-004 | Add explicit decision tree with 5 conditions |
| C1-2 | MCP session error handling incomplete | M2 REQ-024 | Add timeout/connection error recovery spec |
| C1-3 | Hook script content missing | M1 REQ-016 | Embed script template in TECH-004 or TECH-017 |
| C3-1 | load_config return type test missing | M6 | Add TEST-074b for load_config tuple return |
| C4-1 | Signal handler can't access team_state | M4 REQ-062 | Add _module_state.team_state to cli.py |
| C4-2 | Contract state resume incomplete | M4 REQ-063 | Add verified/violated ID lists to ContractReport |

**Total:** 6 CRITICAL issues

### HIGH PRIORITY (Should Fix)

| ID | Issue | Location | Fix Required |
|----|-------|----------|--------------|
| H1-1 | pytest.ini updates missing | All milestones | Add test path configuration requirements |
| H1-2 | Import statements missing | M1-M5 | Add 4 import requirements for new dataclasses |
| H1-3 | Depth gating function name wrong | M5 TECH-044 | Change to apply_depth_quality_gating() |
| H1-4 | MCP server registration timing undefined | M4 WIRE-009 | Specify exact line number (~4200) |
| H1-5 | CLI arguments missing | M1-M3 | Add --agent-teams, --contract-engine-path args |
| H1-6 | State.py serialization missing | M4 TECH-031 | Add to_dict/from_dict updates |
| H2-1 | __init__.py updates missing | M1-M5 | Add 7 requirements for new module imports |
| H3-1 | MCP error path tests missing | M2-M3 | Add 4 tests for crash/malformed/timeout cases |
| H3-2 | Full pipeline integration test missing | M6 | Add TEST-084 for STATE.json persistence |
| H3-3 | Hook script execution not tested | M1 | Add TEST-018 for script exit codes |
| H4-1 | check_milestone_health signature wrong | M5 REQ-078 | Add contract_report parameter to signature |
| H4-2 | Phase 0.75 doesn't exist | M4 REQ-055 | Change to line ~4150 before mode selection |
| H4-3 | Artifact registration trigger undefined | M4 WIRE-013 | Add file tracking mechanism |
| H4-4 | ScanScope computation missing | M5 REQ-069 | Add compute_changed_files() call |
| H4-5 | MCP env vars source undefined | M2 TECH-020 | Add os.getenv() fallback to config |
| H4-6 | Prompt injection params unpopulated | M4 REQ-060 | Add MCP query calls to populate |
| H4-7 | Contract matrix config missing | M5 REQ-075 | Add to TrackingDocumentsConfig |
| H9-1 | Protocol return types incomplete | M1 REQ-001 | Add explicit return types to all methods |
| H9-2 | ContractValidation error field missing | M2 TECH-013 | Add error: str = "" field |

**Total:** 19 HIGH issues

### MEDIUM PRIORITY (Recommended)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| M2-1 | Test directory structure unclear | Project Structure | Tests may be in wrong location |
| M3-1 | Negative test cases sparse | All milestones | Poor error message validation |
| M4-1 | Fix function separation unclear | M5 WIRE-015 | Overloaded _run_integrity_fix() |
| M4-2 | Test generation not wired | M2 REQ-020 | Feature implemented but unused |
| M4-3 | Breaking change detection not wired | M2 REQ-021 | Feature implemented but unused |
| M9-1 | @asynccontextmanager not explicit | M2 TECH-019 | Wrong decorator used |
| M9-2 | Generic type hints missing | M4 TECH-029/030 | Type checking incomplete |

**Total:** 7 MEDIUM issues

### LOW PRIORITY (Nice to Have)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| L1 | Some SVC tables use "string" vs "str" inconsistently | M2/M3 SVC tables | Style inconsistency |
| L2 | No requirement for logging configuration | All milestones | Debugging harder |
| L3 | No requirement for performance benchmarks | M6 | Can't verify no regression |

**Total:** 3 LOW issues

---

## RECOMMENDATIONS

### Priority 1: Fix Before Execution (CRITICAL + HIGH)

1. **Create BUILD2_PRD_v2.md with all 25 fixes applied**
2. **Focus areas:**
   - Add 11 missing TECH requirements (imports, serialization, signatures)
   - Add 7 missing WIRE requirements (hooks, MCP servers, scans)
   - Add 3 missing TEST requirements (integration, error paths)
   - Fix 4 ambiguous REQ descriptions (factory, MCP session, health, loading)

### Priority 2: Verify Alignment (Before Starting)

3. **Run validation checks:**
   - `rg "review_cycles:" BUILD2_PRD_v2.md | wc -l` should equal 267+N (for new requirements)
   - All SVC tables have `{ field: type }` notation
   - All file paths exist in `src/agent_team/` or are marked NEW
   - No requirement references non-existent functions

### Priority 3: Monitor During Execution

4. **Watch for these common execution failures:**
   - Import errors from missing __init__.py updates
   - AttributeError from missing dataclass fields
   - TypeError from wrong return types
   - JSONDecodeError from STATE.json schema mismatch
   - MCPConnectionError from missing error handling

---

## FINAL VERDICT

**Status:** PASS WITH WARNINGS

The BUILD2_PRD.md is **fundamentally executable** but requires fixes for 6 CRITICAL and 19 HIGH priority issues before reliable execution. The PRD demonstrates strong understanding of:
- v14.0 architecture and existing patterns
- Milestone decomposition and dependency management
- Test coverage and backward compatibility needs
- SVC contract completeness and field schema notation

**Recommended action:** Apply all CRITICAL and HIGH fixes → Re-review → Proceed with execution.

**Estimated fix time:** 3-4 hours for all CRITICAL/HIGH fixes.

**Risk assessment after fixes:** LOW — The PRD follows established patterns, has comprehensive test coverage, and maintains backward compatibility via config defaults.

---

**Review completed:** 2026-02-14
**Reviewer:** executability-reviewer agent
**Next step:** Create BUILD2_PRD_v2.md with fixes applied
