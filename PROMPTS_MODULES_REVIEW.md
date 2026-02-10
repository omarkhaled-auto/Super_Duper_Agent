# PROMPTS & MODULES REVIEW REPORT

**Reviewer:** REVIEWER-PROMPTS-MODULES
**Date:** 2026-02-10
**Scope:** agents.py, code_quality_standards.py, e2e_testing.py, tracking_documents.py, design_reference.py, state.py
**Methodology:** Line-by-line review of all source files against ARCHITECTURE_INVENTORY.md checklist

---

## Summary

Reviewed 8 areas across 6 source files (~5,592 lines of code). Found **1 MEDIUM bug** (font policy contradiction in fallback UI generation) and **3 LOW documentation inaccuracies** in the architecture inventory. All prompt constants, build functions, policy injections, quality standards mappings, and dataclass definitions are correctly implemented and cross-referenced. The prompt architecture is sound, with proper config-gating, crash isolation, and backward compatibility throughout.

---

## Findings

### BUG-1: Industrial fallback direction uses banned "Inter" font [MEDIUM]

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **File** | `src/agent_team/design_reference.py` |
| **Line** | 461 |
| **Description** | The `_DIRECTION_TABLE["industrial"]` entry sets `"body_font": "Inter"`. This directly contradicts `ARCHITECT_PROMPT` (agents.py line 888) which states: *"NEVER use Inter, Roboto, or Arial"*. If the fallback path is triggered for an industrial-themed project, the generated UI requirements will contain Inter as the body font. This would then trigger UI-FAIL-002 (hardcoded font) during the UI compliance scan, causing a recovery cycle that could have been avoided. |
| **Impact** | Recovery cycle burn on industrial-themed projects using fallback generation. The font choice will be caught downstream by UI compliance scan, but wastes a fix cycle. |
| **Suggested Fix** | Replace `"body_font": "Inter"` with a distinctive alternative such as `"body_font": "IBM Plex Sans"` or `"body_font": "Source Sans 3"` which fit the industrial aesthetic without violating the ARCHITECT_PROMPT ban. |

### DOC-1: Architecture inventory lists wrong prompt constant names [LOW]

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **File** | `.agent-team/ARCHITECTURE_INVENTORY.md` |
| **Line** | N/A (inventory documentation) |
| **Description** | The inventory references `E2E_COVERAGE_MATRIX_PROMPT` and `FIX_CYCLE_LOG_PROMPT` as constant names in tracking_documents.py. The actual names are `E2E_COVERAGE_MATRIX_TEMPLATE` (line 64) and `FIX_CYCLE_LOG_INSTRUCTIONS` (line 92). |
| **Impact** | None (documentation only). No code references the incorrect names. |
| **Suggested Fix** | Update inventory to use correct constant names: `E2E_COVERAGE_MATRIX_TEMPLATE` and `FIX_CYCLE_LOG_INSTRUCTIONS`. |

### DOC-2: Architecture inventory lists non-existent AppTypeInfo fields [LOW]

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **File** | `.agent-team/ARCHITECTURE_INVENTORY.md` |
| **Line** | N/A (inventory documentation) |
| **Description** | The inventory claims AppTypeInfo has fields `backend_lang`, `frontend_lang`, `has_docker`, and `test_frameworks`. The actual dataclass (e2e_testing.py lines 22-38) uses `language` (single field, not split), has no `has_docker` field, and has no `test_frameworks` field. Actual fields include: `has_backend`, `has_frontend`, `backend_framework`, `frontend_framework`, `language`, `package_manager`, `start_command`, `build_command`, `db_type`, `seed_command`, `api_directory`, `frontend_directory`, `playwright_installed`. |
| **Impact** | None (documentation only). No code references the incorrect field names. |
| **Suggested Fix** | Update inventory to reflect actual AppTypeInfo fields. |

### DOC-3: Architecture inventory uses wrong health value for ConvergenceReport [LOW]

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **File** | `.agent-team/ARCHITECTURE_INVENTORY.md` |
| **Line** | N/A (inventory documentation) |
| **Description** | The inventory describes ConvergenceReport.health as using `"passed"`. The actual state.py dataclass (line 70) uses `"healthy"` / `"degraded"` / `"failed"` / `"unknown"`. The value `"passed"` is never used for ConvergenceReport.health. |
| **Impact** | Could mislead developers writing conditionals against ConvergenceReport.health. |
| **Suggested Fix** | Update inventory to list correct health values: `"healthy"`, `"degraded"`, `"failed"`, `"unknown"`. |

---

## Prompt Policy Mapping Table

This table maps every prompt policy to where it is defined, where it is injected, and where it is enforced/checked.

| Policy | Defined In | Injected Into | Enforcement/Check |
|--------|-----------|---------------|-------------------|
| ZERO MOCK DATA | agents.py CODE_WRITER_PROMPT (line ~1026) | code-writer agent | quality_checks.py `run_mock_data_scan()` MOCK-001..007 |
| UI-FAIL-001..007 | agents.py CODE_WRITER_PROMPT (line ~1080) | code-writer agent | quality_checks.py `run_ui_compliance_scan()` UI-001..004 |
| FRONT-019/020/021 | agents.py CODE_WRITER_PROMPT (line ~1040) | code-writer agent | Reviewer duties in CODE_REVIEWER_PROMPT |
| SEED-001..003 | agents.py CODE_WRITER_PROMPT (line ~1105) | code-writer + architect (via standards) + code-reviewer | Reviewer duties in CODE_REVIEWER_PROMPT |
| ENUM-001..003 | agents.py CODE_WRITER_PROMPT (line ~1118) | code-writer + ARCHITECT_PROMPT + code-reviewer | Reviewer duties in CODE_REVIEWER_PROMPT |
| SVC-xxx wiring | agents.py ARCHITECT_PROMPT (line ~920) | architect agent | Reviewer duties, MOCK DATA GATE |
| Step 3.7 UI DESIGN SYSTEM | agents.py ORCHESTRATOR_SYSTEM_PROMPT (line 565) | orchestrator agent | build_orchestrator_prompt() system prompt |
| UI COMPLIANCE ENFORCEMENT | agents.py build_milestone_execution_prompt (line ~2095) | milestone execution prompt | cli.py `_run_ui_compliance_fix()` |
| 9-step MILESTONE WORKFLOW | agents.py build_milestone_execution_prompt (line ~2040) | milestone execution prompt | cli.py TASKS.md existence check |
| Write tool enforcement | agents.py build_decomposition_prompt (line ~1940) | decomposition prompt | cli.py analysis file validation gate |
| FIX CYCLE AWARENESS | agents.py CODE_WRITER_PROMPT (line ~1093) | code-writer agent | tracking_documents.py FIX_CYCLE_LOG_INSTRUCTIONS |
| MILESTONE HANDOFF AWARENESS | agents.py CODE_WRITER_PROMPT (line ~1098) | code-writer agent | tracking_documents.py MILESTONE_HANDOFF_INSTRUCTIONS |
| DATABASE_INTEGRITY_STANDARDS | code_quality_standards.py (line ~500) | code-writer, code-reviewer, architect | quality_checks.py DB-001..008 scans |
| E2E_TESTING_STANDARDS | code_quality_standards.py (line ~555) | test-runner | quality_checks.py E2E-001..007 scans |
| E2E_COVERAGE_MATRIX_TEMPLATE | tracking_documents.py (line 64) | e2e_testing.py BACKEND/FRONTEND/FIX prompts | tracking_documents.py `parse_e2e_coverage_matrix()` |
| FIX_CYCLE_LOG_INSTRUCTIONS | tracking_documents.py (line 92) | cli.py 5 fix functions (lines 1435, 1518, 1659, 1973, 2598) | tracking_documents.py `parse_fix_cycle_log()` |
| MILESTONE_HANDOFF_INSTRUCTIONS | tracking_documents.py (line 109) | agents.py build_milestone_execution_prompt (line 2069) | tracking_documents.py `parse_milestone_handoff()` |

---

## Detailed Review by Area

### Area 1: Prompt Constants (agents.py) -- PASS

- **CODE_WRITER_PROMPT**: Contains all 6 inline policies (ZERO MOCK DATA, UI-FAIL, FRONT-019/020/021, FIX CYCLE AWARENESS, MILESTONE HANDOFF AWARENESS, SEED DATA, ENUM/STATUS). Vue/Nuxt, Python, BehaviorSubject mock data patterns all present. Policy language is imperative and unambiguous.
- **CODE_REVIEWER_PROMPT**: Contains 10+ review duties including UI compliance checking, mock data detection, SEED-001..003 verification, ENUM-001..003 verification. Correctly mirrors writer policies.
- **ARCHITECT_PROMPT**: Contains SVC-xxx service wiring instructions, Status/Enum Registry policy, "NEVER use Inter, Roboto, or Arial" font directive, design direction guidance.
- **ORCHESTRATOR_SYSTEM_PROMPT**: Step 3.7 UI DESIGN SYSTEM SETUP present at line 565. All 9 orchestration phases properly structured.

### Area 2: Prompt Build Functions (agents.py) -- PASS

- **build_milestone_execution_prompt()**: 9-step MILESTONE WORKFLOW block verified. Includes TASK ASSIGNER step, UI COMPLIANCE ENFORCEMENT block, tracking document conditional injection (config-gated). Handoff injection correctly checks `tracking_config.milestone_handoff`.
- **build_orchestrator_prompt()**: Correctly injects Step 3.7 in system prompt, handles UI standards, interview data, design reference, PRD mode switching.
- **build_decomposition_prompt()**: Write tool enforcement language verified. Analysis file output instructions present.

### Area 3: Prompt Policies (agents.py) -- PASS

- **SEED DATA COMPLETENESS (SEED-001..003)**: Present in CODE_WRITER_PROMPT, injected to architect via DATABASE_INTEGRITY_STANDARDS, checked by CODE_REVIEWER_PROMPT.
- **ENUM/STATUS REGISTRY (ENUM-001..003)**: Present in CODE_WRITER_PROMPT, ARCHITECT_PROMPT, and CODE_REVIEWER_PROMPT. Three-way consistency verified.

### Area 4: Code Quality Standards (code_quality_standards.py) -- PASS

- 8 standard constants defined, all mapped in `_AGENT_STANDARDS_MAP` (lines 592-598).
- No dead (defined-but-unmapped) standards.
- DATABASE_INTEGRITY_STANDARDS mapped to: code-writer, code-reviewer, architect.
- E2E_TESTING_STANDARDS mapped to: test-runner.
- `get_standards_for_agent()` correctly concatenates standards for the requested agent type.

### Area 5: E2E Testing Module (e2e_testing.py) -- PASS

- **AppTypeInfo**: All 13 fields correctly defined with proper defaults.
- **detect_app_type()**: Correctly parses package.json (frontend/backend framework detection), requirements.txt/pyproject.toml (Python backend), angular.json (Angular frontend). Uses `json.loads` with proper error handling.
- **parse_e2e_results()**: Handles missing file (OSError -> skipped), empty content (-> skipped), unparseable format (-> skipped). Regex extraction for totals/passed is correct.
- **3 prompt constants**: BACKEND_E2E_PROMPT, FRONTEND_E2E_PROMPT, E2E_FIX_PROMPT all include tracking document instructions (E2E_COVERAGE_MATRIX_TEMPLATE and FIX_CYCLE_LOG_INSTRUCTIONS).

### Area 6: Tracking Documents Module (tracking_documents.py) -- PASS

- **3 dataclasses**: E2ECoverageStats, FixCycleStats, MilestoneHandoffEntry properly defined with correct fields and defaults.
- **3 prompt constants**: E2E_COVERAGE_MATRIX_TEMPLATE, FIX_CYCLE_LOG_INSTRUCTIONS, MILESTONE_HANDOFF_INSTRUCTIONS all properly defined.
- **7 regex patterns**: All syntactically valid and tested against expected inputs. `_RE_REQ_ID` matches REQ-xxx, SVC-xxx, etc. Route/endpoint patterns correctly extract paths.
- **Generation functions**: `generate_e2e_coverage_matrix()`, `generate_fix_cycle_log_entry()`, `generate_milestone_handoff()` all produce valid markdown output.
- **Parsing functions**: `parse_e2e_coverage_matrix()`, `parse_fix_cycle_log()`, `parse_milestone_handoff()` all handle valid, partial, empty, and malformed input gracefully.
- **Config gates**: All functions check respective config flags before executing.

### Area 7: Design Reference Module (design_reference.py) -- MINOR ISSUE

- **validate_ui_requirements_content()**: Correctly checks 3+ hex colors, 1+ font family, 3+ spacing values, 2+ component types, <5 NOT FOUND markers. All regex patterns valid.
- **run_design_extraction_with_retry()**: Exception splitting into 3 branches verified (DesignExtractionError -> retry, OSError/ConnectionError/TimeoutError -> retry, Exception -> raise immediately). Correct behavior.
- **generate_fallback_ui_requirements()**: Produces valid output structure. **BUT** industrial direction uses `"body_font": "Inter"` (BUG-1 above).
- **_infer_design_direction()**: Word-boundary matching with `re.escape(kw)` correctly prevents partial matches.

### Area 8: State Dataclasses (state.py) -- PASS

- **E2ETestReport**: All required fields present: backend_total, backend_passed, frontend_total, frontend_passed, fix_retries_used, total_fix_cycles, health, failed_tests, skipped, skip_reason.
- **ConvergenceReport**: Health values are "healthy"/"degraded"/"failed"/"unknown". All fields (health, issues, requirements_coverage, tests_passing, convergence_score) correctly defined.
- **RunState**: Properly tracks completed_phases, total_cost, convergence_reports, e2e_report.
- **RunSummary**: Aggregation dataclass correctly defined.

---

## Assessment

**Overall: MINOR FIXES NEEDED**

The prompt and module architecture is well-designed and correctly implemented. All prompt injection chains are complete, config-gated, and crash-isolated. Quality standards mappings are exhaustive with no dead constants. The E2E testing and tracking documents modules handle all edge cases (missing, empty, malformed input) gracefully.

The only code bug found is a font policy contradiction in the fallback UI generation path (BUG-1, MEDIUM severity). This is a real bug that would cause unnecessary recovery cycles for industrial-themed projects, but it is caught by the downstream UI compliance scan, so it does not result in incorrect final output. The fix is a one-line change.

The three LOW-severity findings are documentation inaccuracies in the architecture inventory that do not affect runtime behavior.

| Metric | Value |
|--------|-------|
| Total lines reviewed | ~5,592 |
| MEDIUM bugs | 1 |
| LOW issues | 3 (documentation only) |
| Areas passing | 7/8 |
| Areas with issues | 1/8 (design_reference.py) |
| Prompt policies verified | 17/17 |
| Dead standards | 0 |
| Missing cross-references | 0 |
