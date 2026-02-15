# SIMULATION: BUILD2_PRD.md Through Agent-Team Pipeline

**PRD**: `prompts/BUILD2_PRD.md` -- Builder Fleet Upgrade (Agent Teams, MCP client wrappers, depth gating, hooks)
**Pipeline Version**: v14.0 (28,749 LOC, 5,410+ tests)
**Date**: 2026-02-15

---

## Executive Summary

BUILD2 is a **self-upgrade PRD** -- the agent-team pipeline building an upgrade to itself. This creates unique meta-circularity risks not present in typical builds. The PRD has 6 milestones, ~587 lines, 13 SVC entries, 94 TEST requirements, and produces ~3,550 new LOC across 10 new files + 13 modified files. All features default to `enabled: False` for backward compatibility.

**Overall Verdict**: BUILDABLE with 5 BLOCKERS, 8 WARNINGS, and 6 OPTIMIZATIONS identified.

---

## Phase-by-Phase Simulation

### Phase 0.25: Constraint Extraction

**Prediction**: PASS with noise.

The PRD text will trigger `_REQUIREMENT_RE` and `_PROHIBITION_RE` extensively. The `(review_cycles: N)` suffix on every requirement line will not interfere -- regex looks for sentence-ending punctuation.

**Constraints extracted** (estimated):
- `_TECHNOLOGY_RE`: Will match "Python", "TypeScript" (mentioned in PRD text patterns). Will NOT match "MCP Python SDK" -- "MCP" is not in the technology regex. "Claude Code" is not a recognized technology either.
- `_REQUIREMENT_RE`: Will extract "must call", "must verify", "must never raise" etc. from REQ descriptions -- expect ~30+ requirement constraints.
- `_PROHIBITION_RE`: Will extract "NEVER" patterns from SEC-001/002/003.

**WARNING-01**: The sheer volume of extracted constraints (~30+) will bloat the prompt. Many are implementation details (e.g., "must call `await session.initialize()`") that are not useful as orchestrator-level constraints. The constraint block will consume prompt budget without adding value.

---

### Phase 0.5: Codebase Map

**Prediction**: PASS.

The agent-team codebase itself is the target project. `generate_codebase_map()` will scan `src/agent_team/` and `tests/`. The codebase has ~28,749 LOC across ~30+ files -- well within the 5,000-file cap. The map will correctly identify all existing modules the agent needs to modify.

No issues expected.

---

### Phase 0.6: Design Reference Extraction

**Prediction**: CORRECTLY SKIPPED.

BUILD2 is pure backend/library (no UI). The PRD has no `--design-ref` URLs. The pipeline enters the `else` branch at cli.py:4413. Since `config.design_reference.fallback_generation` defaults to `True`, it will call `generate_fallback_ui_requirements()`.

**WARNING-02**: The fallback generator will attempt to create UI_REQUIREMENTS.md for a project that has ZERO UI components. The `_infer_design_direction()` function will likely default to "professional/corporate" since no UI keywords match. This document will be ignored during implementation but wastes ~$0.10 on the sub-orchestrator call.

**OPTIMIZATION-01**: Add a config flag `skip_ui_for_library: bool = False` or detect pure-library projects (no frontend framework detected) and skip fallback generation entirely. Currently low impact since the fallback is cheap.

---

### Phase 0.75: Contract Loading + Scheduling

**Prediction**: PASS.

No existing `CONTRACTS.json` will be found (new project feature). `ContractRegistry()` will be empty. Scheduling happens after TASKS.md is created -- no issue here.

---

### Phase 1: Decomposition (MASTER_PLAN.md)

**Prediction**: PASS with CONCERNS.

The PRD at ~587 lines (~35KB) is below the 50KB chunking threshold, so `detect_large_prd()` returns False. The decomposition sub-orchestrator will receive the full PRD in one piece.

The PRD specifies 6 milestones with explicit dependency structure:
- M1: no deps (Agent Teams abstraction)
- M2: no deps (Contract Engine MCP client)
- M3: depends on M2
- M4: depends on M1 + M2 + M3
- M5: depends on M4
- M6: depends on M4 + M5

**BLOCKER-01**: **MASTER_PLAN.md milestone IDs must match exactly**. The PRD uses `milestone-1` through `milestone-6`. The decomposition agent must preserve these exact IDs because `milestone_manager.py` parses them with `_RE_MILESTONE_HEADER` (pattern: `#{2,4}`). If the agent invents its own IDs (e.g., "milestone_agent_teams"), the milestone loop will fail to find and execute them.

**Mitigation**: The decomposition prompt in `agents.py` includes "Preserve milestone IDs from the PRD" instructions. Should work, but worth monitoring.

**WARNING-03**: **M1 and M2 are declared independent** in the PRD (`Dependencies: none` for both). However, the current milestone execution loop in `_run_prd_milestones()` at cli.py:897 processes milestones SEQUENTIALLY (one at a time). `config.milestone.max_parallel_milestones` defaults to 1. Even though M1 and M2 CAN run in parallel, the pipeline will serialize them. This is not a bug -- just suboptimal throughput. To exploit parallelism, the user would need to set `max_parallel_milestones: 2` in config.yaml.

---

### Phase 1.5: Tech Stack Research

**Prediction**: PARTIAL PASS.

`detect_tech_stack()` will run against the agent-team project root:
1. **`_detect_from_requirements_txt`**: Will find `pytest` -> Pytest (testing). NOT the `mcp` package -- it's not in `_PYTHON_PACKAGE_MAP`.
2. **`_detect_from_pyproject`**: Will find `pytest` if present. Same limitation for `mcp`.
3. **`_detect_from_text`**: Will scan PRD text and find:
   - "Python" -> Python (language)
   - "Pytest" -> Pytest (testing)
   - Will NOT find "MCP Python SDK" -- no regex for it
   - Will NOT find "Claude Code hooks" -- no regex for it
   - Will NOT find "transitions" library -- no regex for it
   - Will NOT find "anyio" -- no regex for it

**BLOCKER-02**: **Critical technologies undetected**. The 3 most important BUILD2 technologies are:
1. **MCP Python SDK** (`mcp>=1.25,<2`) -- the entire M2/M3 implementation depends on correct `stdio_client()` / `ClientSession` / `call_tool()` patterns.
2. **Claude Code hooks API** -- M1's hook generation depends on exact hook schema (`type`, `command`, `agent`, `matcher`, `timeout`).
3. **Claude Code Agent Teams** -- M1's core feature.

None of these are in `_TEXT_TECH_PATTERNS`, `_NPM_PACKAGE_MAP`, or `_PYTHON_PACKAGE_MAP`. Context7 research will produce queries for Python and Pytest only -- missing the technologies that actually matter.

**Impact**: The agent will implement MCP client code, hook scripts, and Agent Teams integration WITHOUT documentation-backed guidance. It will rely on the PRD's inline code patterns (which are detailed) but may miss SDK edge cases.

**OPTIMIZATION-02**: Before running BUILD2, add these entries to `_PYTHON_PACKAGE_MAP`:
```python
"mcp": ("MCP Python SDK", "other"),
"anyio": ("anyio", "other"),
```
And add to `_TEXT_TECH_PATTERNS`:
```python
(r"\bMCP\s+(?:Python\s+)?SDK\b", "MCP Python SDK", "other"),
(r"\bClaude\s+Code\b\s*(?:hooks|agent\s+teams)?", "Claude Code", "other"),
```

---

### Phase 2: Milestone Execution Loop

#### Milestone 1: Agent Teams Abstraction Layer

**Prediction**: PASS with risk.

M1 creates 2 new files (`agent_teams_backend.py`, `hooks_manager.py`) and modifies 3 (`cli.py`, `config.py`, `state.py`). The implementation is mostly self-contained.

**BLOCKER-03**: **Meta-circularity risk -- modifying cli.py while running in cli.py**. The agent will be told to add `WIRE-001` (wire `create_execution_backend()` into cli.py's mode selection block) and `WIRE-003` (wire teammate shutdown into `_handle_interrupt()`). The agent IS RUNNING INSIDE cli.py. If it modifies the wrong section, it could break the currently-running pipeline mid-execution.

The risk is theoretical but real: the agent writes to `src/agent_team/cli.py` which is the Python module loaded in memory. Python does NOT hot-reload modules, so the writes will take effect only on the NEXT run. The running process uses the in-memory version. **This is actually safe** -- Python's import caching protects against self-modification during execution.

However, there's a subtler risk: if the agent creates a syntax error in `cli.py`, any subsequent import (e.g., a review pass that re-imports) will fail. The review recovery loop calls `_run_review_only()` which does NOT re-import cli.py, so this is also safe.

**Verdict**: Safe due to Python import caching. The agent will modify the file on disk, but the running process is unaffected.

**WARNING-04**: **Hook scripts target `.claude/hooks/`**. REQ-014 creates `.claude/hooks/*.sh` scripts with `chmod 0o755`. The agent-team's OWN `.claude/` directory may already exist (for settings.local.json etc.). The hook scripts are written to the TARGET PROJECT'S `.claude/hooks/`, not the agent-team's own directory. But if BUILD2 is built inside the agent-team repo itself, the generated hooks WILL be in the agent-team's `.claude/hooks/`. This could cause the agent-team's own Claude Code session to pick up the hooks and start enforcing quality gates on its own execution.

**Mitigation**: The user should build BUILD2 in a SEPARATE directory or be aware that generated hooks will affect future Claude Code sessions in the project root.

#### Milestone 2: Contract Engine Integration

**Prediction**: PASS.

M2 creates 2 new files (`contract_client.py`, `mcp_clients.py`) and modifies 2 (`config.py`, `mcp_servers.py`). No dependencies. The MCP client pattern is well-documented in the PRD with exact code patterns.

**WARNING-05**: **MCP SDK import pattern requires exact syntax**. TECH-019 requires lazy import: `from mcp import StdioServerParameters` inside the function body. If the agent puts it at module level, the import will fail when `mcp` is not installed. The PRD is explicit about this, but agents sometimes normalize imports to the top of the file.

**SVC table parsing**: The PRD has 6 SVC entries (SVC-001 through SVC-006) with `{ field: type }` notation. The existing `_parse_svc_table()` in `quality_checks.py` will parse these correctly -- the field schema format matches the expected `{ id: number, title: string }` pattern from v9.0.

#### Milestone 3: Codebase Intelligence Integration

**Prediction**: PASS.

M3 creates 1 new file (`codebase_client.py`) and modifies 3 (`mcp_clients.py`, `codebase_map.py`, `mcp_servers.py`). Depends on M2 (for `mcp_clients.py` shared utilities). The implementation mirrors M2's pattern.

**SVC table**: 7 more SVC entries (SVC-007 through SVC-013). Total 13 SVC entries. All use the `{ field: type }` notation. `_parse_svc_table()` supports this format.

#### Milestone 4: Pipeline Integration + CLAUDE.md Generation

**Prediction**: HIGH RISK -- most complex milestone.

M4 creates 1 new file (`claude_md_generator.py`) and modifies 6 existing files (`cli.py`, `agents.py`, `config.py`, `state.py`, `mcp_servers.py`, `contracts.py`). Depends on M1 + M2 + M3.

**BLOCKER-04**: **cli.py modification scope is massive**. M4 adds ~300 lines to cli.py across multiple insertion points:
- Phase 0.5 modification (codebase map MCP fallback)
- Mode selection block modification (execution backend creation)
- Pre-milestone CLAUDE.md generation
- Convergence health check modification
- Signal handler modification
- Resume context modification

The agent must precisely identify WHERE in the 6,000+ line cli.py to insert each piece. The milestone execution prompt provides file-level context but not line-level. The agent will need to read cli.py, understand the pipeline structure, and insert code at the correct positions.

**Risk**: Off-by-one insertions, duplicate blocks, or code placed in the wrong branch of `if _use_milestones:` / `else:`.

**OPTIMIZATION-03**: The PRD could specify exact function names and line ranges for each WIRE requirement. The WIRE-009 requirement says "Replace `get_mcp_servers(config)` call in cli.py (line ~170-250, mode selection block)" -- the tilde line numbers are helpful but may drift if M1 already modified cli.py.

#### Milestone 5: Contract Scans + Tracking

**Prediction**: PASS.

M5 creates 1 new file (`contract_scanner.py`) and modifies 5 (`config.py`, `code_quality_standards.py`, `tracking_documents.py`, `milestone_manager.py`, `verification.py`). Follows established scan patterns from v5.0-v9.0.

**WARNING-06**: **Depth gating function signature**. TECH-044 specifies depth gating in `apply_depth_quality_gating()`. The function already has 4 parameters (`depth`, `config`, `user_overrides`, `prd_mode`). The new gating logic must be added as additional `_gate()` calls inside existing `if depth == "quick":` etc. blocks. The agent must extend the function, not create a separate one.

#### Milestone 6: End-to-End Verification + Backward Compatibility

**Prediction**: PASS with risk.

M6 is primarily tests (TEST-067 through TEST-094 = 28 tests) plus minor modifications. The 5,410+ existing tests must still pass.

**BLOCKER-05**: **Regression risk from cli.py modifications**. M4 and M1 both modify cli.py heavily. Any bug introduced in these modifications will cause existing test failures. The existing test suite includes `test_production_regression.py` (41 tests) and `test_pipeline_execution_order.py` (38 tests) that validate the pipeline structure. If the agent breaks import order, function signatures, or module-level state, these tests will catch it -- but the fix cycle may burn retries.

**WARNING-07**: **`_dict_to_config()` return type must be preserved**. INT-007 and INT-020 emphasize that `load_config()` returns `tuple[AgentTeamConfig, set[str]]`. All existing callers unpack this tuple. Adding new config sections (4 new dataclasses) to `_dict_to_config()` must follow the exact existing pattern. The v6.0 experience (when this tuple return type was introduced) showed that missing a single caller breaks the entire pipeline.

---

### Post-Orchestration Scans

#### Mock Data Scan (MOCK-001..008)

**Prediction**: LIKELY FALSE POSITIVES.

**WARNING-08**: BUILD2 creates MCP CLIENT code that returns SAFE DEFAULTS when MCP is unavailable. These safe defaults look like mock data:
```python
# From REQ-018: return None on any error
# From REQ-019: return ContractValidation(valid=False, violations=[])
# From REQ-020: return ""  (empty string)
# From REQ-021: return []  (empty list)
```

The MOCK-003 pattern (`_RE_MOCK_VARIABLE`) matches variable names like `mock_*`, `stub_*`, `fake_*`, `dummy_*`. BUILD2 test code (TEST-018 through TEST-030) will use `mocked MCP session` -- these test files will be in `tests/` and the mock scan only scans service/client files in `src/`, so test mocks won't trigger MOCK-003.

However, the safe default return patterns (e.g., `return []`, `return ""`) in `contract_client.py` and `codebase_client.py` will NOT trigger MOCK patterns because they are not in `return of(...)` or `Promise.resolve(...)` patterns. The scan focuses on RxJS/Promise mock patterns, not Python safe defaults.

**Verdict**: Low false positive risk. Python safe defaults (`return None`, `return []`) are not matched by MOCK-001..008 patterns which target JavaScript/TypeScript patterns.

#### UI Compliance Scan (UI-001..004)

**Prediction**: CORRECTLY PRODUCES ZERO VIOLATIONS.

BUILD2 has no UI components, CSS, or Tailwind. The UI scan only checks files matching `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`, `*.sass`, `*.html`. Python files are excluded. Zero violations expected.

#### API Contract Scan (run_api_contract_scan)

**Prediction**: PARTIAL MATCH.

The existing API contract scan in `quality_checks.py` parses SVC-xxx tables from REQUIREMENTS.md. BUILD2's 13 SVC entries use `{ field: type }` notation which is supported by `_parse_field_schema()` from v9.0.

However, BUILD2's SVC entries describe MCP tool calls, not HTTP endpoints. The scanner's `_check_backend_fields()` looks for DTO classes in backend controller/route files. BUILD2's DTOs are dataclasses in `contract_client.py` and `codebase_client.py`, not in typical controller paths.

The scanner searches for files matching `_RE_SERVICE_PATH` which includes patterns like `**/services/**`, `**/api/**`, `**/controllers/**`. The BUILD2 files (`contract_client.py`, `codebase_client.py`) are in `src/agent_team/` -- they may not match these path patterns.

**OPTIMIZATION-04**: The API contract scan may produce zero results (no violations, but also no verification) because it can't find the DTO files. This is a false negative -- the scan silently passes without checking anything. Non-blocking since the scan is advisory.

#### Deployment Scan (DEPLOY-001..004)

**Prediction**: ZERO VIOLATIONS or SKIP.

BUILD2 may not generate Docker configs. If there's no `docker-compose.yml`, the scan returns early. Clean pass.

#### Database Scans (DB-001..008)

**Prediction**: ZERO VIOLATIONS.

BUILD2 uses no database. No `*.prisma`, no Django models, no `dbContext`. The scan will find no entity files and return empty.

#### Integrity Scans (ASSET, PRD)

**Prediction**: PASS.

- Asset scan: No HTML templates with `src`/`href` references to scan.
- PRD reconciliation: Will compare BUILD2_PRD.md against REQUIREMENTS.md. May flag some quantitative claims ("5,410+ existing tests") that don't appear in code. Non-blocking warnings only.

---

### E2E Testing Phase

**Prediction**: CORRECTLY SKIPPED.

`detect_app_type()` will scan the agent-team project root:
- No `package.json` at root -> JS ecosystem detection skipped
- Has `pyproject.toml` -> Python detected, but no Django/FastAPI/Flask -> no `has_backend = True`
- No `angular.json`, no `next.config.js` -> no `has_frontend = True`

Result: `AppTypeInfo(has_backend=False, has_frontend=False)`.

With `config.e2e_testing.skip_if_no_api = True` (default) and `has_backend = False`, the backend E2E phase is skipped. With `skip_if_no_frontend = True` and `has_frontend = False`, the frontend E2E phase is skipped.

**OPTIMIZATION-05**: The E2E phase will still be ENTERED (the `if config.e2e_testing.enabled:` block at cli.py:5681 runs), calls `detect_app_type()`, and then skips both sub-phases. This is correct behavior -- no wasted sub-orchestrator calls.

---

### Browser Testing Phase

**Prediction**: CORRECTLY SKIPPED.

Browser testing is disabled by default (`config.browser_testing.enabled = False`). Even at `thorough` depth, it only enables for `prd_mode or config.milestone.enabled` -- which will be True. But the E2E pass rate gate (`e2e_pass_rate_gate: 0.7`) won't be met since E2E was skipped (0 tests). The browser testing block at cli.py:5951 checks `e2e_total == 0` and skips.

However, this depends on depth. At `standard` depth, browser testing stays disabled. At `thorough`, it would enable but still skip due to no E2E results. At `exhaustive`, same behavior.

**Verdict**: Clean skip regardless of depth.

---

## Meta-Circularity Analysis

### Risk: Agent modifying its own source code

The agent-team pipeline running BUILD2 will instruct sub-agents to modify files in `src/agent_team/`. These are the SAME files the pipeline is currently executing from.

**Python's protection**: Python loads modules into memory at import time. File-on-disk changes do NOT affect the running process. The `cli.py` modifications will be written to disk but the running cli.py uses its in-memory bytecode. This is safe.

**Exception**: If the agent uses `importlib.reload()` or if a new sub-process is spawned that imports the modified module, the new code will be loaded. The pipeline DOES spawn sub-processes (via Claude SDK). However, these sub-processes run the CLAUDE AGENT, not the Python modules directly. The agent SDK invokes `claude` CLI which is a separate Node.js process. The Python modules are only loaded by the MAIN orchestrator process.

**Risk assessment**: LOW. File modifications are safe during execution. The only real risk is if M4's cli.py modifications introduce a syntax error that prevents the POST-ORCHESTRATION scans from importing `quality_checks` or `e2e_testing` (which import from `cli` indirectly). But these modules don't import from `cli.py` -- the import direction is `cli -> quality_checks`, not the reverse.

### Risk: Agent confusing which agent-team to modify

The agent must understand it's modifying `src/agent_team/` in the CURRENT working directory, not some other copy. The codebase map (Phase 0.5) will show the exact files. The REQUIREMENTS.md will list exact file paths. The risk is low because the paths are unambiguous.

### Risk: Generated hooks affecting the build process

If BUILD2 is built inside the agent-team repo:
1. M1 writes `.claude/hooks/quality-gate.sh` to the project root
2. If the user's Claude Code session has hooks enabled, the quality-gate hook will fire on FUTURE session stops
3. The hook checks REQUIREMENTS.md completion ratio and may BLOCK session stops

This is not a problem during BUILD2 execution (hooks are written but not loaded by the running process). It becomes a problem in subsequent Claude Code sessions in the same directory.

---

## Findings Summary

### BLOCKERS (5)

| ID | Phase | Finding | Impact | Mitigation |
|----|-------|---------|--------|------------|
| BLOCKER-01 | Phase 1 | MASTER_PLAN.md milestone IDs must match `milestone-N` format exactly | Milestone loop won't find milestones | Decomposition prompt instructs ID preservation; monitor output |
| BLOCKER-02 | Phase 1.5 | MCP Python SDK, Claude Code hooks, and Agent Teams are undetectable by `detect_tech_stack()` | Zero Context7 research for the 3 most critical technologies | Add `mcp`, `claude-code` to detection patterns pre-build |
| BLOCKER-03 | M1 | Agent modifies cli.py while running inside it (meta-circularity) | Theoretical risk; Python import caching protects | Safe due to Python module loading; no action needed |
| BLOCKER-04 | M4 | cli.py modification scope is ~300 lines across 6+ insertion points in a 6,000+ line file | High risk of off-by-one insertions or wrong-branch placement | PRD provides WIRE-xxx requirements with approximate line numbers; agent reads file first |
| BLOCKER-05 | M6 | Regression risk from M1+M4 cli.py modifications; 79+ existing pipeline tests may break | Fix cycle budget may be exhausted on regressions | Run `pytest tests/test_pipeline_execution_order.py` after M4 |

### WARNINGS (8)

| ID | Phase | Finding | Impact |
|----|-------|---------|--------|
| WARNING-01 | Phase 0.25 | ~30+ constraints extracted from PRD requirement descriptions | Prompt bloat; implementation details as orchestrator constraints |
| WARNING-02 | Phase 0.6 | Fallback UI_REQUIREMENTS.md generated for pure-library project | Wasted $0.10 on irrelevant document |
| WARNING-03 | Phase 1 | M1 and M2 cannot run in parallel (max_parallel_milestones=1 default) | Suboptimal throughput; ~30min wasted |
| WARNING-04 | M1 | Hook scripts in `.claude/hooks/` may affect future Claude sessions | User surprise; hooks enforce quality gates |
| WARNING-05 | M2 | MCP SDK lazy import pattern must be in function body, not module level | ImportError when `mcp` not installed |
| WARNING-06 | M5 | Depth gating must extend existing `_gate()` calls, not create new function | Incorrect gating if agent creates separate function |
| WARNING-07 | M6 | `_dict_to_config()` tuple return type must be preserved across all callers | All callers break if return type changes |
| WARNING-08 | Scans | MCP client safe defaults may superficially resemble mock data patterns | Low risk -- Python patterns not matched by JS-focused regexes |

### OPTIMIZATIONS (6)

| ID | Finding | Recommendation |
|----|---------|----------------|
| OPT-01 | Fallback UI doc generated for library project | Skip fallback when `detect_app_type()` finds no frontend |
| OPT-02 | MCP SDK not in tech research detection | Add `"mcp": ("MCP Python SDK", "other")` to `_PYTHON_PACKAGE_MAP` |
| OPT-03 | M4 cli.py modifications lack precise insertion markers | Add function-name anchors to WIRE requirements |
| OPT-04 | API contract scan may silently skip verification | Non-blocking; scan path patterns don't match `*_client.py` |
| OPT-05 | E2E phase entered then skipped; correct but adds ~5s | Could short-circuit on `has_backend=False AND has_frontend=False` |
| OPT-06 | M1+M2 serialized despite being independent | Set `max_parallel_milestones: 2` in config.yaml for BUILD2 |

---

## Recommended config.yaml for BUILD2

```yaml
milestone:
  enabled: true
  max_parallel_milestones: 1  # Keep 1 for safety on meta-circular build
  review_recovery_retries: 2

depth:
  default: thorough

tech_research:
  enabled: true
  max_queries_per_tech: 4

e2e_testing:
  enabled: false  # Library project, no server

browser_testing:
  enabled: false  # No UI

design_reference:
  fallback_generation: false  # Skip UI doc for library
  require_ui_doc: false

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: false  # No UI
  api_contract_scan: true

integrity_scans:
  deployment_scan: false  # No Docker
  asset_scan: false  # No HTML templates
  prd_reconciliation: true
```

---

## Critical Pre-Build Actions

1. **Add MCP SDK to tech research patterns** (addresses BLOCKER-02):
   - Add `"mcp"` to `_PYTHON_PACKAGE_MAP` in `tech_research.py`
   - Add Claude Code text pattern to `_TEXT_TECH_PATTERNS`

2. **Verify no stale `.agent-team/`** exists (known gotcha from MEMORY.md):
   - Delete `.agent-team/MASTER_PLAN.md` before running BUILD2
   - Stale plans from previous runs cause wrong milestone structure

3. **Set `design_reference.fallback_generation: false`** in config:
   - Prevents wasting budget on irrelevant UI document

4. **Monitor M4 closely** (addresses BLOCKER-04):
   - After M4 completes, immediately run: `python -c "from src.agent_team import cli"` to verify no syntax errors
   - If M4 breaks cli.py imports, the review recovery loop will catch it but may exhaust retries

5. **Disable UI compliance scan** (no UI components to check):
   - Set `post_orchestration_scans.ui_compliance_scan: false`
