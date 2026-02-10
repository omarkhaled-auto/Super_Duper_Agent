# Agent-Team Exhaustive Implementation — Production Readiness Audit (v2.0–v6.0)

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (6 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `general-purpose` | Phase 1 — Read ALL source files end-to-end, produce ARCHITECTURE_INVENTORY.md: complete feature inventory with function names, file paths, config gates, callers, and test coverage status for every v2.0–v6.0 upgrade |
| `reviewer-config-scans` | `general-purpose` | Phase 2A — Review `src/agent_team/config.py` + `src/agent_team/quality_checks.py`: verify all config dataclasses, all scan functions, all regex patterns, all severity levels, scope handling, config loaders, validation rules. Produce CONFIG_SCANS_REVIEW.md |
| `reviewer-pipeline` | `general-purpose` | Phase 2B — Review `src/agent_team/cli.py`: verify post-orchestration execution order, gate conditions, crash isolation, fix functions, recovery loops, state updates, scope passing, E2E phase. Produce PIPELINE_REVIEW.md |
| `reviewer-prompts-modules` | `general-purpose` | Phase 2C — Review `src/agent_team/agents.py` + `src/agent_team/e2e_testing.py` + `src/agent_team/tracking_documents.py` + `src/agent_team/design_reference.py` + `src/agent_team/code_quality_standards.py` + `src/agent_team/state.py`: verify all prompt policies, module functions, generation/parsing logic. Produce PROMPTS_MODULES_REVIEW.md |
| `wiring-verifier` | `general-purpose` | Phase 2D — Cross-reference ALL source files: verify every function defined → called, every config field → consumed, every prompt → injected, every scan → wired, every recovery type → handled. Produce E2E_WIRING_REPORT.md |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write 7 exhaustive test files (~280+ tests), run full pytest suite, fix any failures or bugs discovered. These tests VERIFY production readiness across all upgrade versions |

### Coordination Flow

```
Wave 1 (solo): architect reads ALL source files
    |
    Produces: .agent-team/ARCHITECTURE_INVENTORY.md
    |
Wave 2 (parallel): reviewer-config-scans (config.py + quality_checks.py)
                  + reviewer-pipeline (cli.py)
                  + reviewer-prompts-modules (agents.py + modules)
                  + wiring-verifier (cross-file verification)
    |                   |                    |                |
    All read ARCHITECTURE_INVENTORY.md first
    |                   |                    |                |
    Produce: CONFIG_SCANS_REVIEW.md          |                |
             PIPELINE_REVIEW.md              |                |
             PROMPTS_MODULES_REVIEW.md       |                |
             E2E_WIRING_REPORT.md            |                |
    +---------+---------+--------------------+----------------+
              |
Wave 3 (solo): test-engineer reads ALL 5 reports, writes 7 test files
              |
Wave 4 (solo): test-engineer runs full pytest suite, fixes failures
              |
Wave 5: You (team lead) collect all reports + test results
              → PRODUCTION_READINESS_VERDICT.md
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **architect runs first and alone.** Its ARCHITECTURE_INVENTORY.md is the blueprint for all reviewers.
- **Review agents + wiring-verifier run simultaneously.** They review different file scopes:
  - reviewer-config-scans: `src/agent_team/config.py`, `src/agent_team/quality_checks.py` — READ ONLY
  - reviewer-pipeline: `src/agent_team/cli.py` — READ ONLY
  - reviewer-prompts-modules: `src/agent_team/agents.py`, `src/agent_team/e2e_testing.py`, `src/agent_team/tracking_documents.py`, `src/agent_team/design_reference.py`, `src/agent_team/code_quality_standards.py`, `src/agent_team/state.py` — READ ONLY
  - wiring-verifier: ALL source files in `src/agent_team/` — READ ONLY
- **test-engineer waits for ALL reviewers** before starting.
- **If any reviewer finds a bug**, report it in the review document with severity, file, line, description, and suggested fix. The test-engineer will fix confirmed bugs during Phase 4.
- **After the final wave completes,** shut down all agents. Collect results and write the final PRODUCTION_READINESS_VERDICT.md yourself.

### Critical Rules for Agents

- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_INVENTORY.md only.
- reviewer-config-scans: READ ONLY. Produce CONFIG_SCANS_REVIEW.md. Do NOT edit source files.
- reviewer-pipeline: READ ONLY. Produce PIPELINE_REVIEW.md. Do NOT edit source files.
- reviewer-prompts-modules: READ ONLY. Produce PROMPTS_MODULES_REVIEW.md. Do NOT edit source files.
- wiring-verifier: READ ONLY. Produce E2E_WIRING_REPORT.md. Do NOT edit source files.
- test-engineer: Can create/edit test files in `tests/`. Can edit ANY source file in `src/agent_team/` to fix bugs discovered during testing.
- ALL review agents: Your job is to FIND issues, NOT to give a pass. Actively look for gaps, dead code, broken gates, missing crash isolation, wrong execution order, and semantic errors. A clean report with zero findings should be treated with SUSPICION — go back and look harder.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# Production Readiness Audit — Verifying 20 Upgrades Across 6 Versions

## Background — Why This Exists

The agent-team has undergone 6 major upgrade cycles (v2.0 through v6.0) adding 20+ features: mock
data scanning, UI compliance enforcement, E2E testing, deployment/asset integrity scans, PRD
reconciliation, tracking documents, database integrity checks, and depth-intelligent scoping.
These upgrades were implemented incrementally across multiple sessions with multiple review rounds,
each finding and fixing real bugs. **We need to verify that ALL upgrades are production-ready: fully
implemented, correctly wired, properly gated, crash-isolated, backward-compatible, and tested.**

Previous review rounds have consistently found real bugs:
- v2.0 review: decomposition threshold bug, missing TASKS.md check
- v3.0 review: dead code (E2E-005/006/007), fix loop burning retries on skipped status
- v3.1 review: BOM stripping missing, query string in asset resolution
- v3.2 audit: nested asyncio.run (CRITICAL), _resolve_asset query string bug
- v5.0 review: 24 bugs across 2 rounds (2 CRITICAL: unimplemented DB-003/DB-007, wrong fix prompts)
- v6.0 review: 5 bugs fixed (2 HIGH: scoped scanning semantic errors)

This audit ASSUMES bugs still exist. The goal is to find them, fix them, and write tests that prevent regression.

### Failure 1: Wiring Gaps — Functions Exist But Are Never Called

A scan function or generation function is implemented in a module but NEVER wired into cli.py's execution pipeline. The code exists, passes unit tests in isolation, but never runs in production. This has happened before: E2E-005, E2E-006, and E2E-007 quality patterns were implemented in quality_checks.py but the code paths that triggered them were dead until v3.0 review found it. Similarly, DB-003 and DB-007 scan patterns existed but their detection logic was unimplemented — the regex patterns matched nothing because the surrounding code never called them.

### Failure 2: Wrong Execution Order — Steps Run At The Wrong Time

A scan runs before its prerequisite, or after the results are needed. The post-orchestration pipeline in cli.py has a specific execution order: scope computation → mock scan → UI scan → deployment scan → asset scan → PRD reconciliation → database scans → E2E testing. Each step depends on the previous one for correct state. If scope is computed AFTER scans start, scans get `None` scope and run full-project instead of scoped. If E2E backend runs AFTER frontend, the 70% backend pass-rate gate is meaningless. If tracking documents are generated before the phase they track, they capture incomplete data.

### Failure 3: Broken Config Gating — Flags Don't Control What They Claim

A config field exists in the dataclass, is loaded from YAML, but doesn't actually gate the runtime behavior it claims to control. This happened with `milestone.mock_data_scan` — the field was on `MilestoneConfig` but controlled a non-milestone scan, confusing users. It also happened with depth gating: `apply_depth_quality_gating()` only gated 2 quality prompt sections for quick mode, leaving 10+ expensive scans running. Users who selected "quick" expected fast runs but got full post-orchestration.

### Failure 4: Missing Crash Isolation — New Feature Crashes Kill The Pipeline

A new scan or generation function throws an unhandled exception that propagates up and kills the entire post-orchestration pipeline. Every integration point MUST be wrapped in its own `try/except`. This was found in v6.0: the PRD reconciliation quality gate read REQUIREMENTS.md without try/except — if the file was deleted between the `is_file()` check and `read_text()` call, the entire pipeline crashed.

### Failure 5: Backward Incompatibility — Old Projects Break On Upgrade

A return type change, new required config field, or missing default breaks existing projects that haven't updated their config. The most dangerous case was `load_config()` changing from returning `AgentTeamConfig` to `tuple[AgentTeamConfig, set[str]]` in v6.0. If ANY caller was missed, it would crash at runtime. Similarly, if a new config dataclass field didn't have a default, existing YAML files without that field would fail to parse.

### Failure 6: Semantic Scan Incorrectness — False Positives or False Negatives

A regex pattern matches too broadly (false positives) or too narrowly (false negatives). This has happened multiple times: `_RE_FONT_FAMILY` missed camelCase `fontFamily`, `_RE_COMPONENT_TYPE` missed plurals like "Buttons", `_RE_DB_CSHARP_ENUM_PROP` matched non-enum types, `_RE_ENTITY_INDICATOR_PY` matched bare `Base` (too broad), scoped scanning broke aggregate checks (E2E-005 false positive, relationship cross-file false positive).

### Failure 7: Prompt Policy Gaps — Policies Defined But Not Injected

A prompt policy constant is defined in agents.py or code_quality_standards.py but never injected into the actual prompt function output. Or injected into the wrong role (code-writer policy in architect prompt, or vice versa). The E2E_TESTING_STANDARDS, DATABASE_INTEGRITY_STANDARDS, ZERO MOCK DATA POLICY, UI COMPLIANCE POLICY, SEED DATA COMPLETENESS, and ENUM/STATUS REGISTRY all have specific role targets — if any mapping is wrong, agents get the wrong instructions.

### Failure 8: Recovery Loop Incompleteness — Fix Functions Miss Violation Types

A fix function handles some violation types but not all. This was CRITICAL in v5.0: `_run_integrity_fix()` was sending the ASSET fix prompt for ALL database scans because it had no database-specific elif branches. The fix function existed and was called, but it generated wrong fix prompts for 3 out of 5 violation types.

## What We're Building

**Deliverable 1: Architecture Inventory** (Phase 1)
Complete inventory of every v2.0–v6.0 feature: function name, file path, approximate line, config gate, caller in cli.py, recovery type, test file, test count. This is the MASTER CHECKLIST that all reviewers verify against.

**Deliverable 2: Config & Scan Correctness Report** (Phase 2A)
Line-by-line review of all config dataclasses (11 total), all scan functions (8 total), all regex patterns (40+ total), all severity assignments, scope handling, config loaders, and validation rules. Every finding tagged with severity and exact fix.

**Deliverable 3: Pipeline Execution Correctness Report** (Phase 2B)
Line-by-line review of cli.py's post-orchestration pipeline: execution order, gate conditions, crash isolation, fix functions, recovery loops, state updates. Every finding tagged with severity and exact fix.

**Deliverable 4: Prompt & Module Correctness Report** (Phase 2C)
Line-by-line review of all prompt constants, prompt build functions, module functions, generation/parsing logic, and role-to-standard mappings. Every finding tagged with severity and exact fix.

**Deliverable 5: End-to-End Wiring Report** (Phase 2D)
Cross-file verification: every function defined → called, every config field → consumed, every prompt → injected, every scan → wired with correct params, every recovery type → handled by correct fix function. A table with PASS/FAIL for each row.

**Deliverable 6: Production Readiness Test Suite** (Phase 3)
Seven test files with ~280+ tests covering: regression safety, pipeline ordering, config completeness, scan pattern correctness, prompt integrity, fix function completeness, and cross-version integration.

**Deliverable 7: Production Readiness Verdict** (Phase 5)
Final report synthesizing all reviewer findings, wiring verification results, and test results into a GO/NO-GO verdict with any remaining action items.

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

Before ANYONE reviews or tests anything, the architect must read the ENTIRE codebase and produce `.agent-team/ARCHITECTURE_INVENTORY.md` — a complete inventory of every v2.0–v6.0 feature.

**CRITICAL INSTRUCTION:** You MUST read the `Agent-team_New_Upgrades.md` file in the project root FIRST. This file documents every upgrade from v2.0 through v6.0 with implementation details. Use it as your REFERENCE CHECKLIST — every feature listed there must appear in your inventory with verified file locations.

### 1A: Config Layer (`src/agent_team/config.py`)

- Read `src/agent_team/config.py` end to end (~1100 lines)
- Document EVERY dataclass with ALL fields, types, and defaults:
  - `DepthConfig` — especially `scan_scope_mode: str = "auto"`
  - `QualityConfig` — `production_defaults`, `craft_review`
  - `ConvergenceConfig` — `requirements_dir`, `requirements_file`, thresholds
  - `MilestoneConfig` — `mock_data_scan`, `ui_compliance_scan`, `review_recovery_retries`, and ALL other fields
  - `DesignReferenceConfig` — `extraction_retries`, `fallback_generation`, `content_quality_check`
  - `PostOrchestrationScanConfig` — `mock_data_scan`, `ui_compliance_scan`
  - `E2ETestingConfig` — `enabled`, `backend_api_tests`, `frontend_playwright_tests`, `max_fix_retries`, `test_port`, `skip_if_no_api`, `skip_if_no_frontend`
  - `IntegrityScanConfig` — `deployment_scan`, `asset_scan`, `prd_reconciliation`
  - `DatabaseScanConfig` — `dual_orm_scan`, `default_value_scan`, `relationship_scan`
  - `TrackingDocumentsConfig` — `e2e_coverage_matrix`, `fix_cycle_log`, `milestone_handoff`, `coverage_completeness_gate`, `wiring_completeness_gate`
  - `AgentTeamConfig` — ALL sub-config field names
- Document `_dict_to_config()`:
  - Return type: `tuple[AgentTeamConfig, set[str]]`
  - ALL YAML section names it handles (list them)
  - user_overrides tracking: which sections, which keys
  - Backward-compat migration logic (milestone → post_orchestration_scans)
  - Validation rules (scan_scope_mode, extraction_retries, test_port, max_fix_retries)
- Document `load_config()`: return type, all callers
- Document `apply_depth_quality_gating()`:
  - Signature with `user_overrides` parameter
  - What each depth level gates (quick/standard/thorough/exhaustive)
  - `_gate()` helper logic
  - ALL config fields it modifies per depth level
- WHY: This is the foundation — every other verification depends on knowing the config layer perfectly

### 1B: Quality Checks Layer (`src/agent_team/quality_checks.py`)

- Read `src/agent_team/quality_checks.py` end to end (~2500+ lines)
- Document `ScanScope` dataclass and `compute_changed_files()` function
- Document `Violation` dataclass fields and `_MAX_VIOLATIONS` constant
- Document `_iter_source_files()`, `_find_entity_files()`, `_should_skip_dir()`, `_should_scan_file()` helpers
- Document ALL 8 scan functions with EXACT signatures, approximate lines, and scope handling:
  - `run_mock_data_scan(project_root, scope)` — MOCK-001..007 patterns
  - `run_ui_compliance_scan(project_root, scope)` — UI-001..004 patterns
  - `run_e2e_quality_scan(project_root, scope)` — E2E-001..007 patterns (note: E2E-005 aggregate check uses full file list)
  - `run_deployment_scan(project_root)` — DEPLOY-001..004 patterns (NO scope parameter)
  - `run_asset_scan(project_root, scope)` — ASSET-001..003 patterns
  - `run_dual_orm_scan(project_root, scope)` — DB-001..003 patterns (detection phase uses full files, violation phase scoped)
  - `run_default_value_scan(project_root, scope)` — DB-004..005 patterns
  - `run_relationship_scan(project_root, scope)` — DB-006..008 patterns (entity_info from all files, violations scoped)
- Document ALL regex patterns: pattern name, what it matches, what it should NOT match
- Document ALL severity assignments for each violation check ID
- Document helper functions specific to each scan:
  - `_detect_data_access_methods()`, `_parse_docker_compose()`, `_parse_env_file()`
  - `_is_static_asset_ref()`, `_resolve_asset()`
  - `_BUILTIN_ENV_VARS` frozenset, `_RE_ENV_WITH_DEFAULT`
  - `_CSHARP_NON_ENUM_TYPES` set
- WHY: Every regex pattern and severity level must be verified. The scan functions are the enforcement layer.

### 1C: CLI Pipeline Layer (`src/agent_team/cli.py`)

- Read `src/agent_team/cli.py` — focus on the complete post-orchestration section (approximately lines 3780–4100+)
- Document the EXACT execution order of ALL post-orchestration steps:
  1. Scope computation block (depth-based, compute_changed_files)
  2. Mock data scan (gate + call + fix)
  3. UI compliance scan (gate + call + fix)
  4. Deployment integrity scan (gate + call + fix)
  5. Asset integrity scan (gate + call + fix)
  6. PRD reconciliation (quality gate + LLM call)
  7. Database scans: dual_orm, default_value, relationship (gate + call + fix for each)
  8. E2E testing phase (backend → frontend → fix loops)
- For EACH step, document:
  - Exact gate condition (the `if` statement)
  - Function called with EXACT parameters (especially `scope=scan_scope`)
  - Try/except present (crash isolation)
  - Fix function called on violations (with recovery_type string)
  - State updated after completion
- Document ALL fix functions:
  - `_run_mock_data_fix()` — parameters, recovery_type
  - `_run_ui_compliance_fix()` — parameters, recovery_type
  - `_run_integrity_fix()` — ALL 5 scan_type values it handles (deployment, asset, dual_orm, default_value, relationship)
  - `_run_e2e_fix()` — parameters
- Document `load_config()` call site: verify tuple unpacking `config, user_overrides = load_config(...)`
- Document BOTH `apply_depth_quality_gating()` call sites: verify `user_overrides` passed
- Document E2E testing phase:
  - Backend test execution → health check → 70% pass-rate gate → frontend test execution → fix loop
  - Fix loop guard conditions
  - completed_phases tracking
- Document tracking document generation/parsing call sites
- Document `_run_prd_reconciliation()` and PRD quality gate
- WHY: cli.py is the ORCHESTRATION layer. Every upgrade feature must be wired here at the right position.

### 1D: Prompt Layer (`src/agent_team/agents.py`)

- Read `src/agent_team/agents.py` end to end
- Document ALL prompt constants that contain upgrade-related content:
  - `CODE_WRITER_PROMPT` — find: ZERO MOCK DATA POLICY, UI COMPLIANCE POLICY (UI-FAIL-001..007), FRONT-019/020/021
  - `CODE_REVIEWER_PROMPT` — find: UI compliance duties, mock data detection guidance
  - Orchestrator prompt — find: step 3.7 UI DESIGN SYSTEM SETUP
- Document ALL prompt build functions:
  - `build_orchestrator_prompt()` — what it includes, config toggles
  - `build_milestone_execution_prompt()` — 9-step MILESTONE WORKFLOW, TASK ASSIGNER, UI COMPLIANCE ENFORCEMENT, tracking document instructions
  - `build_decomposition_prompt()` — analysis file enforcement
  - Any build function that injects tracking document instructions
- Document prompt policy injection points:
  - SEED DATA COMPLETENESS (SEED-001..003) — which prompt, which role
  - ENUM/STATUS REGISTRY (ENUM-001..003) — which prompt, which role
  - SVC-xxx wiring instructions — which prompts
  - DATABASE_INTEGRITY_STANDARDS — which roles
  - E2E_TESTING_STANDARDS — which roles
- WHY: Prompt policies are the mechanism that makes agents follow the rules. Missing or misplaced policies = agents ignore the rules.

### 1E: E2E Testing Module (`src/agent_team/e2e_testing.py`)

- Read `src/agent_team/e2e_testing.py` end to end
- Document:
  - `AppTypeInfo` dataclass
  - `detect_app_type()` — what it parses (package.json, requirements.txt, angular.json)
  - `parse_e2e_results()` — what format it expects (E2E_RESULTS.md)
  - `BACKEND_E2E_PROMPT`, `FRONTEND_E2E_PROMPT`, `E2E_FIX_PROMPT` constants
  - Tracking document instructions injected into E2E prompts
- WHY: E2E testing is the most complex post-orchestration feature with multiple interacting components.

### 1F: Tracking Documents Module (`src/agent_team/tracking_documents.py`)

- Read `src/agent_team/tracking_documents.py` end to end (~988 lines)
- Document ALL dataclasses (3 total)
- Document ALL generation functions — what they produce, when called
- Document ALL parsing functions — what format they expect, what they return
- Document ALL prompt constants (2 total)
- Document ALL regex patterns (7 total)
- Document config gates (TrackingDocumentsConfig fields)
- WHY: Tracking documents have the most complex generation/parsing lifecycle.

### 1G: Design Reference Module (`src/agent_team/design_reference.py`)

- Read `src/agent_team/design_reference.py`
- Document:
  - `validate_ui_requirements_content()` — validation logic
  - `run_design_extraction_with_retry()` — retry/fallback chain
  - `generate_fallback_ui_requirements()` — fallback generation
  - Error type splitting (DesignExtractionError vs OSError vs generic Exception)
- WHY: UI requirements generation has a complex retry/fallback chain that must work correctly.

### 1H: State Layer (`src/agent_team/state.py`)

- Read `src/agent_team/state.py`
- Document ALL dataclasses:
  - `ConvergenceReport` — fields, how it's used
  - `RunState` — fields, how it's persisted
  - `E2ETestReport` — fields, health values, failed_tests list
- WHY: State dataclasses are shared across modules. Incorrect fields = incorrect state tracking.

### 1I: Code Quality Standards (`src/agent_team/code_quality_standards.py`)

- Read `src/agent_team/code_quality_standards.py`
- Document ALL standard constants:
  - `DATABASE_INTEGRITY_STANDARDS` — mapped to which roles?
  - `E2E_TESTING_STANDARDS` — mapped to which roles?
  - Any other standard constants
- Document the role → standard mapping mechanism
- WHY: Standards must map to the correct agent roles.

### 1J: Test Inventory

- List ALL existing test files in `tests/` with approximate test counts
- Identify which upgrade version each test file covers
- Identify GAPS: upgrades or features without dedicated tests
- Document pre-existing test failures (test_mcp_servers.py)
- WHY: test-engineer needs to know what's already covered vs what needs new tests.

### Output

Write `.agent-team/ARCHITECTURE_INVENTORY.md` with all findings, organized by section (1A through 1J), with exact file paths, line numbers, function names, config fields, and integration points. Include a MASTER CHECKLIST table at the end:

```markdown
## Master Checklist

| Version | Feature | File | Function | Config Gate | Caller in cli.py | Crash-Isolated | Tested By | Status |
|---------|---------|------|----------|-------------|-------------------|----------------|-----------|--------|
| v2.0 | MOCK-001..007 patterns | quality_checks.py | run_mock_data_scan | milestone.mock_data_scan | line XXXX | YES/NO | test_prd_fixes.py | VERIFY |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

This table must have ONE ROW per feature/function — not per version. A version with 6 features gets 6 rows.

---

## PHASE 2A: CONFIG & SCAN REVIEW (reviewer-config-scans)

Read ARCHITECTURE_INVENTORY.md first. Use it as your checklist.

**Your mission:** Review `src/agent_team/config.py` and `src/agent_team/quality_checks.py` LINE BY LINE. For every item in the inventory, verify it exists and is correct. ACTIVELY LOOK FOR BUGS.

### Review Area 1: Config Dataclasses (config.py)

For EACH of the 11 dataclasses:
- [ ] All fields have correct types
- [ ] All fields have correct defaults
- [ ] No field is dead (unused by any code)
- [ ] No field is missing (referenced in code but not defined)

### Review Area 2: Config Loading (_dict_to_config)

- [ ] Every dataclass section has a corresponding `if "section_name" in data:` block
- [ ] Every field within each section uses `.get()` with the correct default
- [ ] `user_overrides` tracking covers ALL gatable fields:
  - quality: production_defaults, craft_review
  - milestone: mock_data_scan, ui_compliance_scan, review_recovery_retries
  - integrity_scans: deployment_scan, asset_scan, prd_reconciliation
  - e2e_testing: enabled, max_fix_retries
  - database_scans: dual_orm_scan, default_value_scan, relationship_scan
  - post_orchestration_scans: mock_data_scan, ui_compliance_scan
- [ ] Backward-compat migration: `milestone.mock_data_scan` → `post_orchestration_scans.mock_data_scan` when no `post_orchestration_scans` section
- [ ] `scan_scope_mode` validation rejects values not in ("auto", "full", "changed")
- [ ] `extraction_retries >= 0` validation present
- [ ] `test_port` validation (1024–65535) present
- [ ] `max_fix_retries` validation (minimum 1) present
- [ ] Return type is `tuple[AgentTeamConfig, set[str]]`

### Review Area 3: Depth Gating (apply_depth_quality_gating)

- [ ] Signature includes `user_overrides: set[str] | None = None`
- [ ] `_gate()` helper checks `key not in uo` before overriding
- [ ] **Quick mode gates:**
  - quality.production_defaults = False
  - quality.craft_review = False
  - post_orchestration_scans.mock_data_scan = False (via _gate)
  - milestone.mock_data_scan = False (via _gate)
  - post_orchestration_scans.ui_compliance_scan = False (via _gate)
  - milestone.ui_compliance_scan = False (via _gate)
  - integrity_scans.deployment_scan = False (via _gate)
  - integrity_scans.asset_scan = False (via _gate)
  - integrity_scans.prd_reconciliation = False (via _gate)
  - database_scans.dual_orm_scan = False (via _gate)
  - database_scans.default_value_scan = False (via _gate)
  - database_scans.relationship_scan = False (via _gate)
  - milestone.review_recovery_retries = 0 (via _gate)
- [ ] **Standard mode gates:**
  - integrity_scans.prd_reconciliation = False (via _gate)
  - Nothing else changed
- [ ] **Thorough mode gates:**
  - e2e_testing.enabled = True (via _gate)
  - milestone.review_recovery_retries = 2 (via _gate)
- [ ] **Exhaustive mode gates:**
  - e2e_testing.enabled = True (via _gate)
  - milestone.review_recovery_retries = 3 (via _gate)

### Review Area 4: Scan Functions (quality_checks.py)

For EACH of the 8 scan functions:
- [ ] Correct signature: `(project_root: Path, scope: ScanScope | None = None) -> list[Violation]`
  - EXCEPTION: `run_deployment_scan` has NO scope parameter
- [ ] Scope filtering applied correctly:
  - `run_mock_data_scan`: filters `_iter_source_files()` output
  - `run_ui_compliance_scan`: filters `_iter_source_files()` output
  - `run_e2e_quality_scan`: per-file checks use scoped files; E2E-005 aggregate uses FULL file list
  - `run_asset_scan`: builds `scope_set` once before `os.walk()` loop
  - `run_dual_orm_scan`: detection (`_detect_data_access_methods`) uses FULL file list; violation reporting scoped
  - `run_default_value_scan`: filters `_find_entity_files()` output
  - `run_relationship_scan`: collects `entity_info` from ALL files; reports violations only for scoped files
- [ ] Each scan returns `list[Violation]`
- [ ] Each scan respects `_MAX_VIOLATIONS` cap
- [ ] `compute_changed_files()` handles: FileNotFoundError, SubprocessError, TimeoutExpired, OSError → returns `[]`

### Review Area 5: Regex Pattern Correctness (quality_checks.py)

For EACH pattern category, verify the regex is syntactically valid and semantically correct:

**MOCK-001..007:**
- [ ] MOCK-001: hardcoded arrays in service files
- [ ] MOCK-002: `setTimeout`/`setInterval` with fake data
- [ ] MOCK-003: `Math.random()` for ID generation
- [ ] MOCK-004: `TODO`/`FIXME`/`HACK` comments with mock data
- [ ] MOCK-005: hardcoded credentials/tokens
- [ ] MOCK-006: BehaviorSubject with mock initial value
- [ ] MOCK-007: `new Observable` with inline mock data

**UI-001..004:**
- [ ] UI-001: hardcoded colors (hex, rgb) outside design system
- [ ] UI-002: arbitrary font-family declarations (matches camelCase `fontFamily`)
- [ ] UI-003: hardcoded spacing (arbitrary Tailwind including directional `p[tlbrxy]?-`, `m[tlbrxy]?-`)
- [ ] UI-004: component types without design system (handles plurals with `s?`)

**E2E-001..007:**
- [ ] E2E-001: missing test assertions
- [ ] E2E-002: hardcoded test data
- [ ] E2E-003: missing error scenario tests
- [ ] E2E-004: missing edge case tests
- [ ] E2E-005: inverted auth check (aggregate, not per-file)
- [ ] E2E-006: placeholder text in templates
- [ ] E2E-007: 403 in test results

**DEPLOY-001..004:**
- [ ] DEPLOY-001: port mismatch
- [ ] DEPLOY-002: undefined env vars (excludes `_BUILTIN_ENV_VARS`, excludes vars with defaults via `_RE_ENV_WITH_DEFAULT`)
- [ ] DEPLOY-003: CORS origin mismatch
- [ ] DEPLOY-004: service name mismatch

**ASSET-001..003:**
- [ ] ASSET-001: broken `src` attribute references
- [ ] ASSET-002: broken `url()` CSS references
- [ ] ASSET-003: broken `import`/`require` asset references
- [ ] `_is_static_asset_ref()` strips query strings/fragments
- [ ] `_resolve_asset()` checks 7 candidate paths
- [ ] Excludes: external URLs, data URIs, template variables, webpack aliases

**DB-001..008:**
- [ ] DB-001: ORM entity type differs from raw SQL column type — severity "error"
- [ ] DB-002: ORM property name differs from raw SQL column name — severity "error"
- [ ] DB-003: raw SQL query returns columns not mapped to ORM — severity "error"
- [ ] DB-004: nullable property without default value — severity "warning"
- [ ] DB-005: nullable property accessed without null check (500-char window, TypeScript optional chaining, Python Optional[] guard) — severity "error"
- [ ] DB-006: FK property without navigation property — severity "warning"
- [ ] DB-007: navigation property without inverse — severity "info"
- [ ] DB-008: FK without fluent API / OnModelCreating config — severity "error"
- [ ] C# enum regex excludes `_CSHARP_NON_ENUM_TYPES` + Dto/Service/Controller/Repository suffix filtering
- [ ] Python entity indicator: `Base\s*=\s*declarative_base|class\s+\w+\(.*Base\)|Base\.metadata` (NOT bare `\bBase\b`)
- [ ] Prisma enum types detected by no-default regex
- [ ] C# bool no-default handles `init;`, `private set;`, `protected set;`
- [ ] TypeScript raw SQL skips comment lines
- [ ] Prisma String status-like fields scanned (`_RE_DB_PRISMA_STRING_STATUS_NO_DEFAULT`)

### Output

Write `CONFIG_SCANS_REVIEW.md` in the project root with:
1. Summary: total checks, pass count, fail count
2. For each FAILED check: severity (CRITICAL/HIGH/MEDIUM/LOW), file, line, description, suggested fix
3. For each PASSED check: brief confirmation
4. Overall assessment: PASS / MINOR FIXES / MAJOR ISSUES

---

## PHASE 2B: PIPELINE EXECUTION REVIEW (reviewer-pipeline)

Read ARCHITECTURE_INVENTORY.md first. Use it as your checklist.

**Your mission:** Review `src/agent_team/cli.py` LINE BY LINE through the entire post-orchestration section. Verify execution order, gate conditions, crash isolation, fix functions, and state management. ACTIVELY LOOK FOR BUGS.

### Review Area 1: load_config and apply_depth_quality_gating Call Sites

- [ ] `load_config()` called with correct tuple unpacking: `config, user_overrides = load_config(...)`
- [ ] Find ALL call sites of `load_config()` in cli.py — verify EVERY one unpacks the tuple
- [ ] `apply_depth_quality_gating()` called at BOTH call sites:
  - Main orchestration (around line 3407): `apply_depth_quality_gating(depth, config, user_overrides)`
  - Sub-orchestrator runs (around line 388): verify `user_overrides` passed
- [ ] `user_overrides` variable is in scope at both call sites

### Review Area 2: Post-Orchestration Execution Order

Verify the EXACT order by reading cli.py sequentially through the post-orchestration block:

- [ ] Step 0: Scope computation block (compute_changed_files, ScanScope construction)
  - auto mode: quick/standard → compute scope; thorough/exhaustive → None
  - "changed" mode → always compute
  - "full" mode → never compute (scope stays None)
  - Wrapped in try/except (crash isolation)
- [ ] Step 1: Mock data scan
  - Gate: `not _use_milestones and (config.post_orchestration_scans.mock_data_scan or config.milestone.mock_data_scan)`
  - Call: `run_mock_data_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_mock_data_fix()` on violations
  - Crash isolation: try/except present
- [ ] Step 2: UI compliance scan
  - Gate: `not _use_milestones and (config.post_orchestration_scans.ui_compliance_scan or config.milestone.ui_compliance_scan)`
  - Call: `run_ui_compliance_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_ui_compliance_fix()` on violations
  - Crash isolation: try/except present
- [ ] Step 3: Deployment integrity scan
  - Gate: `config.integrity_scans.deployment_scan`
  - Call: `run_deployment_scan(Path(cwd))` — NO scope parameter
  - Fix: `_run_integrity_fix(scan_type="deployment")` on violations
  - Crash isolation: try/except present
- [ ] Step 4: Asset integrity scan
  - Gate: `config.integrity_scans.asset_scan`
  - Call: `run_asset_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_integrity_fix(scan_type="asset")` on violations
  - Crash isolation: try/except present
- [ ] Step 5: PRD reconciliation
  - Quality gate (thorough only): REQUIREMENTS.md exists + >500 bytes + REQ-xxx pattern
  - Quality gate crash isolation: wrapped in try/except OSError
  - Gate: `config.integrity_scans.prd_reconciliation` (modified by quality gate for thorough)
  - Call: `_run_prd_reconciliation()` (async sub-orchestrator LLM call)
  - Crash isolation: try/except present
- [ ] Step 6: Database dual ORM scan
  - Gate: `config.database_scans.dual_orm_scan`
  - Call: `run_dual_orm_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_integrity_fix(scan_type="dual_orm")` on violations
  - Crash isolation: try/except present
- [ ] Step 7: Database default value scan
  - Gate: `config.database_scans.default_value_scan`
  - Call: `run_default_value_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_integrity_fix(scan_type="default_value")` on violations
  - Crash isolation: try/except present
- [ ] Step 8: Database relationship scan
  - Gate: `config.database_scans.relationship_scan`
  - Call: `run_relationship_scan(Path(cwd), scope=scan_scope)`
  - Fix: `_run_integrity_fix(scan_type="relationship")` on violations
  - Crash isolation: try/except present
- [ ] Step 9: E2E testing phase
  - Gate: `config.e2e_testing.enabled`
  - Backend before frontend
  - 70% backend pass-rate gate for frontend
  - Fix loop guard: `not in ("passed", "skipped", "unknown")`
  - Frontend fix loop updates `e2e_report.failed_tests` each cycle
  - completed_phases tracking: only for `health in ("passed", "partial")`
  - Crash isolation: outer try/except with traceback logging

### Review Area 3: Fix Functions

- [ ] `_run_integrity_fix()` has FIVE elif branches for scan_type:
  - "deployment" → deployment-specific fix prompt
  - "asset" → asset-specific fix prompt
  - "dual_orm" → database dual ORM fix prompt
  - "default_value" → database default value fix prompt
  - "relationship" → database relationship fix prompt
- [ ] Each fix function adds correct recovery_type to recovery_types set
- [ ] Fix functions are crash-isolated (called within try/except)
- [ ] Fix cycle log entries generated if tracking documents enabled

### Review Area 4: State Management

- [ ] `e2e_report` correctly populated with backend/frontend totals, passed, health
- [ ] `completed_phases` correctly updated
- [ ] `convergence_report` or `milestone_convergence_report` correctly set
- [ ] `recovery_types` set correctly accumulates violation types
- [ ] `print_recovery_report()` called with correct arguments

### Review Area 5: Tracking Document Integration

- [ ] E2E coverage matrix generated after E2E tests run (if config enabled)
- [ ] Fix cycle log entries in ALL 5 fix functions (mock, UI, integrity, E2E)
- [ ] Milestone handoff generated after milestone completion (if config enabled)
- [ ] `_generate_handoff_details()` sub-orchestrator called at correct lifecycle point
- [ ] All tracking document calls crash-isolated

### Output

Write `PIPELINE_REVIEW.md` in the project root with:
1. Summary: total checks, pass count, fail count
2. For each FAILED check: severity, file, line range, description, suggested fix
3. Execution order diagram (verified against source)
4. Overall assessment: PASS / MINOR FIXES / MAJOR ISSUES

---

## PHASE 2C: PROMPTS & MODULES REVIEW (reviewer-prompts-modules)

Read ARCHITECTURE_INVENTORY.md first. Use it as your checklist.

**Your mission:** Review ALL prompt constants, prompt build functions, and module files. Verify every policy is injected into the correct role, every generation function produces correct output, every parsing function handles edge cases. ACTIVELY LOOK FOR BUGS.

### Review Area 1: Prompt Constants (agents.py)

- [ ] `CODE_WRITER_PROMPT` contains:
  - "ZERO MOCK DATA" or equivalent policy text
  - "UI-FAIL-001" through "UI-FAIL-007" (UI COMPLIANCE POLICY)
  - "FRONT-019" through "FRONT-021" standards
  - Zero mock data enforcement for Vue/Nuxt, Python, BehaviorSubject patterns
- [ ] `CODE_REVIEWER_PROMPT` contains:
  - UI compliance review duties
  - Mock data detection guidance
- [ ] Orchestrator/architect prompts contain:
  - SVC-xxx wiring instructions
  - UI DESIGN SYSTEM SETUP step (step 3.7)

### Review Area 2: Prompt Build Functions (agents.py)

- [ ] `build_milestone_execution_prompt()` contains:
  - 9-step MILESTONE WORKFLOW
  - TASK ASSIGNER section
  - [UI COMPLIANCE ENFORCEMENT] section
  - Tracking document instructions (when config.tracking_documents fields enabled)
- [ ] `build_orchestrator_prompt()` contains:
  - Step 3.7 UI DESIGN SYSTEM SETUP
  - Tracking document instructions (when config enabled)
- [ ] `build_decomposition_prompt()` contains:
  - Write tool enforcement for analysis files
- [ ] Prompt build functions EXCLUDE tracking document instructions when config disabled

### Review Area 3: Prompt Policies (agents.py)

- [ ] SEED DATA COMPLETENESS (SEED-001..003):
  - Defined in correct constant
  - Injected into architect AND code-writer roles
- [ ] ENUM/STATUS REGISTRY (ENUM-001..003):
  - Defined in correct constant
  - Injected into architect AND code-writer AND code-reviewer roles

### Review Area 4: Code Quality Standards (code_quality_standards.py)

- [ ] `DATABASE_INTEGRITY_STANDARDS` constant exists with correct content
- [ ] `DATABASE_INTEGRITY_STANDARDS` mapped to: code-writer, code-reviewer, architect
- [ ] `E2E_TESTING_STANDARDS` constant exists with correct content
- [ ] `E2E_TESTING_STANDARDS` mapped to: test-runner (verify exact role name)
- [ ] No standard constant is defined but unmapped (dead code)

### Review Area 5: E2E Testing Module (e2e_testing.py)

- [ ] `detect_app_type()`:
  - Parses package.json → extracts framework (React, Angular, Vue, Next.js)
  - Parses requirements.txt → extracts Python framework (Django, Flask, FastAPI)
  - Parses angular.json → detects Angular
  - Returns `AppTypeInfo` with correct fields
- [ ] `parse_e2e_results()`:
  - Parses E2E_RESULTS.md with ## sections
  - Extracts total/passed counts for backend and frontend
  - Returns `E2ETestReport` with correct fields
  - Handles missing/malformed file gracefully
- [ ] Prompt constants (`BACKEND_E2E_PROMPT`, `FRONTEND_E2E_PROMPT`, `E2E_FIX_PROMPT`):
  - Contain role-based testing instructions (when applicable)
  - Contain tracking document instructions (matrix update, fix log)
  - E2E_FIX_PROMPT contains pattern-specific fix guidance

### Review Area 6: Tracking Documents Module (tracking_documents.py)

- [ ] ALL generation functions produce correct markdown format
- [ ] ALL parsing functions handle:
  - Valid full input → correct dataclass
  - Partial input → best-effort extraction
  - Empty input → empty/default dataclass (no crash)
  - Malformed input → graceful degradation (no crash)
- [ ] ALL regex patterns are syntactically valid
- [ ] Config gates (`e2e_coverage_matrix`, `fix_cycle_log`, `milestone_handoff`) respected
- [ ] Coverage completeness gate (0.8 default) correctly compared
- [ ] Wiring completeness gate (1.0 default) correctly compared

### Review Area 7: Design Reference Module (design_reference.py)

- [ ] `validate_ui_requirements_content()` checks for meaningful content (not just whitespace)
- [ ] `run_design_extraction_with_retry()`:
  - Retries on DesignExtractionError (up to extraction_retries)
  - Retries on OSError/ConnectionError/TimeoutError
  - Does NOT retry on generic Exception (raises immediately)
- [ ] `generate_fallback_ui_requirements()` produces valid UI requirements
- [ ] Phase 0.6 retry+fallback chain in cli.py correctly wired

### Review Area 8: State Dataclasses (state.py)

- [ ] `E2ETestReport` has all required fields:
  - backend_total, backend_passed, frontend_total, frontend_passed
  - fix_retries_used, total_fix_cycles, health, failed_tests, skip_reason
- [ ] `ConvergenceReport` has correct fields for health check results
- [ ] No dataclass field type mismatch with how it's used in cli.py

### Output

Write `PROMPTS_MODULES_REVIEW.md` in the project root with:
1. Summary: total checks, pass count, fail count
2. For each FAILED check: severity, file, line, description, suggested fix
3. Prompt policy mapping table (policy → role → verified)
4. Overall assessment: PASS / MINOR FIXES / MAJOR ISSUES

---

## PHASE 2D: END-TO-END WIRING VERIFICATION (wiring-verifier)

Read ARCHITECTURE_INVENTORY.md first. Use it as your master reference.

**Your mission:** Cross-reference ALL source files to verify that every function defined is called, every config field is consumed, every prompt policy is injected, and every scan is wired with correct parameters. This is the CROSS-FILE verification that individual reviewers can't do.

### Verification 1: Function Call Graph

For EVERY public function in each module, verify it has at least one caller:

**quality_checks.py → cli.py:**
- [ ] `run_mock_data_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `run_ui_compliance_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `run_e2e_quality_scan()` → called from cli.py (verify WHERE and WITH WHAT params)
- [ ] `run_deployment_scan()` → called from cli.py post-orchestration (NO scope)
- [ ] `run_asset_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `run_dual_orm_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `run_default_value_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `run_relationship_scan()` → called from cli.py post-orchestration with `scope=scan_scope`
- [ ] `compute_changed_files()` → called from cli.py scope computation block
- [ ] `ScanScope` → imported and used in cli.py scope computation
- [ ] `parse_prd_reconciliation()` → called from cli.py after PRD reconciliation

**e2e_testing.py → cli.py:**
- [ ] `detect_app_type()` → called from cli.py E2E phase
- [ ] `parse_e2e_results()` → called from cli.py E2E phase (backend + frontend)
- [ ] `BACKEND_E2E_PROMPT` → used in cli.py `_run_backend_e2e_tests()`
- [ ] `FRONTEND_E2E_PROMPT` → used in cli.py `_run_frontend_e2e_tests()`
- [ ] `E2E_FIX_PROMPT` → used in cli.py `_run_e2e_fix()`

**tracking_documents.py → cli.py:**
- [ ] Matrix generation function → called after E2E tests
- [ ] Matrix parsing function → called after matrix generation
- [ ] Fix cycle log function → called in ALL fix functions (mock, UI, integrity, E2E)
- [ ] Handoff generation function → called after milestone completion
- [ ] Handoff verification function → called at start of next milestone

**design_reference.py → cli.py:**
- [ ] `run_design_extraction_with_retry()` → called in Phase 0.6
- [ ] `validate_ui_requirements_content()` → called in Phase 0.6
- [ ] `generate_fallback_ui_requirements()` → called on extraction failure

**config.py → cli.py:**
- [ ] `load_config()` → called with tuple unpacking
- [ ] `apply_depth_quality_gating()` → called at BOTH sites with `user_overrides`
- [ ] `detect_depth()` → called before depth gating

### Verification 2: Config Field Consumption

For EVERY config field that gates behavior, verify it's actually checked at runtime:

- [ ] `config.post_orchestration_scans.mock_data_scan` → consumed in mock scan gate
- [ ] `config.post_orchestration_scans.ui_compliance_scan` → consumed in UI scan gate
- [ ] `config.milestone.mock_data_scan` → consumed in mock scan gate (OR with above)
- [ ] `config.milestone.ui_compliance_scan` → consumed in UI scan gate (OR with above)
- [ ] `config.milestone.review_recovery_retries` → consumed in review recovery loop
- [ ] `config.integrity_scans.deployment_scan` → consumed in deployment scan gate
- [ ] `config.integrity_scans.asset_scan` → consumed in asset scan gate
- [ ] `config.integrity_scans.prd_reconciliation` → consumed in PRD recon gate
- [ ] `config.database_scans.dual_orm_scan` → consumed in dual ORM scan gate
- [ ] `config.database_scans.default_value_scan` → consumed in default value scan gate
- [ ] `config.database_scans.relationship_scan` → consumed in relationship scan gate
- [ ] `config.e2e_testing.enabled` → consumed in E2E phase gate
- [ ] `config.e2e_testing.max_fix_retries` → consumed in E2E fix loop
- [ ] `config.e2e_testing.backend_api_tests` → consumed in E2E backend decision
- [ ] `config.e2e_testing.frontend_playwright_tests` → consumed in E2E frontend decision
- [ ] `config.e2e_testing.skip_if_no_api` → consumed in E2E skip logic
- [ ] `config.e2e_testing.skip_if_no_frontend` → consumed in E2E skip logic
- [ ] `config.tracking_documents.e2e_coverage_matrix` → consumed in matrix generation gate
- [ ] `config.tracking_documents.fix_cycle_log` → consumed in fix log gate
- [ ] `config.tracking_documents.milestone_handoff` → consumed in handoff generation gate
- [ ] `config.design_reference.extraction_retries` → consumed in retry loop
- [ ] `config.design_reference.fallback_generation` → consumed in fallback decision
- [ ] `config.depth.scan_scope_mode` → consumed in scope computation

### Verification 3: Scan → Fix → Recovery Chain

For EVERY scan type, verify the complete chain: scan runs → violations detected → fix function called → recovery_type added:

| Scan | Function | Fix Function | scan_type param | recovery_type |
|------|----------|-------------|-----------------|---------------|
| Mock | run_mock_data_scan | _run_mock_data_fix | N/A | verify |
| UI | run_ui_compliance_scan | _run_ui_compliance_fix | N/A | verify |
| Deploy | run_deployment_scan | _run_integrity_fix | "deployment" | verify |
| Asset | run_asset_scan | _run_integrity_fix | "asset" | verify |
| Dual ORM | run_dual_orm_scan | _run_integrity_fix | "dual_orm" | verify |
| Default Value | run_default_value_scan | _run_integrity_fix | "default_value" | verify |
| Relationship | run_relationship_scan | _run_integrity_fix | "relationship" | verify |

- [ ] Verify each row: scan output → if violations → fix function called → recovery_type string
- [ ] Verify `_run_integrity_fix()` has elif branches for ALL 5 scan_type values
- [ ] Verify each fix function uses the CORRECT prompt for each scan_type

### Verification 4: Import Chain

- [ ] All `from .quality_checks import ...` in cli.py include: `run_mock_data_scan`, `run_ui_compliance_scan`, `run_deployment_scan`, `run_asset_scan`, `run_dual_orm_scan`, `run_default_value_scan`, `run_relationship_scan`, `ScanScope`, `compute_changed_files`, `parse_prd_reconciliation`
- [ ] All `from .e2e_testing import ...` in cli.py include: `detect_app_type`, `parse_e2e_results`, prompt constants
- [ ] All `from .tracking_documents import ...` in cli.py include: generation and parsing functions
- [ ] All `from .config import ...` in cli.py include: `apply_depth_quality_gating`, `load_config`, `detect_depth`
- [ ] No circular imports between modules
- [ ] All lazy imports (inside try blocks) correctly catch ImportError

### Output

Write `E2E_WIRING_REPORT.md` in the project root with:

```markdown
## Function Call Graph
| Source Module | Function | Called From | Parameters | Status |
|--------------|----------|-------------|------------|--------|
| quality_checks | run_mock_data_scan | cli.py:XXXX | (Path(cwd), scope=scan_scope) | PASS/FAIL |
| ... | ... | ... | ... | ... |

## Config Field Consumption
| Config Field | Consumed At | Gate Condition | Status |
|-------------|-------------|----------------|--------|
| post_orchestration_scans.mock_data_scan | cli.py:XXXX | OR with milestone.mock_data_scan | PASS/FAIL |
| ... | ... | ... | ... |

## Scan-Fix-Recovery Chain
| Scan Type | Fix Function | scan_type | recovery_type | Status |
|-----------|-------------|-----------|---------------|--------|
| mock | _run_mock_data_fix | N/A | {verify} | PASS/FAIL |
| ... | ... | ... | ... | ... |

## Overall: PASS / ISSUES FOUND
```

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After ALL Phase 2 agents complete, read ALL 5 reports (ARCHITECTURE_INVENTORY.md, CONFIG_SCANS_REVIEW.md, PIPELINE_REVIEW.md, PROMPTS_MODULES_REVIEW.md, E2E_WIRING_REPORT.md). Use the findings to inform your test design. Fix any confirmed bugs BEFORE writing tests.

**CRITICAL: Read `Agent-team_New_Upgrades.md` in the project root. This is the master document of ALL upgrades. Every upgrade listed there must have test coverage.**

### Test File 1: Regression Tests (`tests/test_production_regression.py`) — ~40 tests

These tests verify that EVERY previously-found bug across all review rounds remains fixed. Each test targets ONE specific bug with a descriptive name.

**v2.0 regressions:**
- Decomposition analysis file threshold is 1/2 (not 1/3) — verify in build_decomposition_prompt output
- ZERO MOCK DATA POLICY text present in CODE_WRITER_PROMPT
- MOCK-006 pattern matches BehaviorSubject with mock initial value
- MOCK-007 pattern matches `new Observable` with inline mock data
- Python service files scanned by run_mock_data_scan (not just TS/JS)

**v2.2 regressions:**
- `_RE_FONT_FAMILY` regex matches camelCase `fontFamily` and `font:` shorthand
- `_RE_COMPONENT_TYPE` regex matches plurals (Buttons, Cards, Inputs)
- `_RE_CONFIG_FILE` regex does NOT match `ThemeToggle.tsx` (path-segment-aware)
- `_RE_ARBITRARY_SPACING` matches directional Tailwind: `pt-`, `mx-`, `pb-`
- `_infer_design_direction` uses word boundary (does not match substring)
- Design extraction retry splits errors: DesignExtractionError → retry, generic Exception → raise

**v3.0 regressions:**
- E2E fix loop guard: `not in ("passed", "skipped", "unknown")` — does NOT burn retries on skipped
- Frontend fix loop updates `e2e_report.failed_tests` each cycle (not stale from first run)
- E2E-005 pattern is actually triggered (not dead code)
- E2E-006 pattern detects placeholder text in templates
- E2E-007 pattern detects 403 status in results
- completed_phases only appends for `health in ("passed", "partial")` — NOT for "failed"

**v3.1 regressions:**
- `_parse_docker_compose()` returns None for non-dict YAML (e.g., list at top level)
- `_parse_env_file()` strips BOM character from first line
- `_parse_env_file()` strips `export ` prefix (with space or tab)
- `_is_static_asset_ref()` strips query strings (`?v=1.2.3`) before extension check
- `_is_static_asset_ref()` strips fragments (`#section`) before extension check
- PRD reconciliation parser: h4 subheaders (`####`) do NOT exit mismatch mode

**v5.0 regressions:**
- `_run_integrity_fix()` has "dual_orm" elif branch (not sending asset prompt)
- `_run_integrity_fix()` has "default_value" elif branch
- `_run_integrity_fix()` has "relationship" elif branch
- DB-005 detects TypeScript optional chaining (`?.`) as null check
- DB-005 detects Python `Optional[]` guard as null check
- C# enum regex filters `_CSHARP_NON_ENUM_TYPES` (string, int, bool, etc.)
- C# enum regex filters Dto/Service/Controller/Repository suffixes
- Python entity indicator uses `declarative_base` pattern (NOT bare `\bBase\b`)
- Prisma enum types trigger no-default violation
- C# bool no-default regex handles `init;`, `private set;`, `protected set;`
- TypeScript raw SQL detection skips `//` comment lines
- Prisma String status-like fields detected by dedicated regex

**v6.0 regressions:**
- E2E-005 aggregate check uses FULL file list when scoped (no false positive)
- Dual ORM detection phase uses FULL file list (not scoped)
- Relationship scan collects entity_info from ALL files (scoped violation reporting only)
- PRD reconciliation quality gate wrapped in try/except OSError
- No redundant `import re as _re_mod` in cli.py (uses existing `re`)

### Test File 2: Pipeline Execution Order (`tests/test_pipeline_execution_order.py`) — ~35 tests

These tests verify the EXACT order and conditions of the post-orchestration pipeline by reading cli.py source and/or mocking execution.

**Order verification:**
- Scope computation executes BEFORE any scan call
- apply_depth_quality_gating executes BEFORE scope computation
- Mock scan executes BEFORE UI scan
- UI scan executes BEFORE deployment scan
- Deployment scan executes BEFORE asset scan
- Asset scan executes BEFORE PRD reconciliation
- PRD reconciliation executes BEFORE database scans
- Database scans execute BEFORE E2E testing
- Dual ORM scan executes BEFORE default value scan
- Default value scan executes BEFORE relationship scan
- E2E backend executes BEFORE E2E frontend
- 70% backend pass-rate check happens BEFORE frontend starts

**Conditional execution:**
- PRD quality gate: thorough + >500B + REQ-xxx → runs
- PRD quality gate: thorough + <500B → skips
- PRD quality gate: thorough + no REQ-xxx → skips
- PRD quality gate: thorough + no REQUIREMENTS.md → skips
- PRD quality gate: exhaustive → always runs (no gate)
- PRD quality gate: quick → already disabled by depth gating
- E2E auto-enabled for thorough depth (no user override)
- E2E auto-enabled for exhaustive depth (no user override)
- E2E stays disabled for standard depth
- E2E stays disabled if user set enabled=false (even thorough)

**Tracking document lifecycle:**
- Coverage matrix generated AFTER E2E tests complete
- Fix cycle log entry added INSIDE each fix function
- Milestone handoff generated AFTER milestone completion
- Handoff verification at START of next milestone

### Test File 3: Config Completeness (`tests/test_config_completeness.py`) — ~50 tests

**Dataclass defaults:**
- For each of 11 config dataclasses: instantiate with no args → verify all field defaults correct
- AgentTeamConfig default → all sub-configs have correct defaults

**YAML loading:**
- Empty YAML → all defaults, empty user_overrides
- Full YAML (all sections, all keys) → all values loaded, full user_overrides
- Partial YAML (only depth section) → depth loaded, rest defaults
- Partial YAML (only milestone section) → milestone loaded, rest defaults
- Unknown YAML keys ignored (no crash)
- Wrong type YAML values handled gracefully

**user_overrides tracking (per section × per key):**
- quality.production_defaults in YAML → "quality.production_defaults" in overrides
- quality.craft_review in YAML → "quality.craft_review" in overrides
- milestone.mock_data_scan in YAML → "milestone.mock_data_scan" in overrides
- milestone.ui_compliance_scan in YAML → "milestone.ui_compliance_scan" in overrides
- milestone.review_recovery_retries in YAML → "milestone.review_recovery_retries" in overrides
- integrity_scans.deployment_scan in YAML → "integrity_scans.deployment_scan" in overrides
- integrity_scans.asset_scan in YAML → "integrity_scans.asset_scan" in overrides
- integrity_scans.prd_reconciliation in YAML → "integrity_scans.prd_reconciliation" in overrides
- e2e_testing.enabled in YAML → "e2e_testing.enabled" in overrides
- e2e_testing.max_fix_retries in YAML → "e2e_testing.max_fix_retries" in overrides
- database_scans.dual_orm_scan in YAML → "database_scans.dual_orm_scan" in overrides
- database_scans.default_value_scan in YAML → "database_scans.default_value_scan" in overrides
- database_scans.relationship_scan in YAML → "database_scans.relationship_scan" in overrides
- post_orchestration_scans.mock_data_scan in YAML → "post_orchestration_scans.mock_data_scan" in overrides
- post_orchestration_scans.ui_compliance_scan in YAML → "post_orchestration_scans.ui_compliance_scan" in overrides

**Depth gating × user overrides (selected combos):**
- Quick + user set mock_data_scan:true → stays True
- Quick + user set deployment_scan:true → stays True
- Quick + no overrides → all scans disabled
- Thorough + user set e2e_testing.enabled:false → stays False
- Standard + user set prd_reconciliation:true → stays True
- apply_depth_quality_gating with None user_overrides → treats as empty set

**Backward compatibility:**
- milestone.mock_data_scan only (no post_orchestration_scans) → migrated
- post_orchestration_scans.mock_data_scan (no milestone) → used directly
- Both present → post_orchestration_scans takes precedence

**Validation:**
- scan_scope_mode "auto" → valid
- scan_scope_mode "full" → valid
- scan_scope_mode "changed" → valid
- scan_scope_mode "invalid" → raises ValueError
- extraction_retries -1 → raises ValueError
- test_port 80 → raises ValueError (below 1024)
- test_port 70000 → raises ValueError (above 65535)
- max_fix_retries 0 → raises ValueError (below 1)

### Test File 4: Scan Pattern Correctness (`tests/test_scan_pattern_correctness.py`) — ~60 tests

**For each regex pattern, write positive AND negative match tests:**

**MOCK patterns:**
- MOCK-001: `const users = [{name: "John"}]` in service file → matches
- MOCK-001: `const users = []` → does NOT match (empty array)
- MOCK-005: `const token = "abc123"` in service file → matches
- MOCK-006: `new BehaviorSubject([{id:1}])` → matches
- MOCK-007: `new Observable(subscriber => subscriber.next([{fake:true}]))` → matches

**UI patterns:**
- UI-002: `font-family: Arial` → matches
- UI-002: `fontFamily: 'Arial'` → matches (camelCase)
- UI-002: `font: 14px Arial` → matches (shorthand)
- UI-003: `pt-4` → matches (directional)
- UI-003: `mx-auto` → matches
- UI-004: `Button` → matches
- UI-004: `Buttons` → matches (plural)

**DB patterns:**
- DB-004: C# `public string Name { get; set; }` without `= "";` → matches
- DB-004: C# `public bool IsActive { get; init; }` → matches (`init;`)
- DB-004: C# `public bool IsActive { get; private set; }` → matches
- DB-005: Nullable accessed without TypeScript `?.` within 500 chars → matches
- DB-005: Nullable with `Optional[str]` guard in Python → does NOT match
- DB-001: C# enum property with `string Status { get; set; }` in entity → matches status-like field
- C# enum regex: `UserDto` class → does NOT trigger (Dto suffix filtered)

**Scope handling (for each of 7 scoped functions):**
- scope=None → scans all files
- scope with changed_files=[] → scans all files (empty = full fallback)
- scope with changed_files=[file_a] → only scans file_a
- scope with changed_files=[file_not_matching] → returns empty violations

### Test File 5: Prompt Integrity (`tests/test_prompt_integrity.py`) — ~30 tests

- CODE_WRITER_PROMPT contains "ZERO MOCK DATA" (or "zero mock data")
- CODE_WRITER_PROMPT contains "UI-FAIL-001"
- CODE_WRITER_PROMPT contains "UI-FAIL-007"
- CODE_WRITER_PROMPT contains "FRONT-019"
- CODE_WRITER_PROMPT contains "FRONT-020"
- CODE_WRITER_PROMPT contains "FRONT-021"
- CODE_REVIEWER_PROMPT contains "UI compliance" or "ui compliance"
- build_milestone_execution_prompt output contains "MILESTONE WORKFLOW"
- build_milestone_execution_prompt output contains "TASK ASSIGNER"
- build_milestone_execution_prompt output contains "UI COMPLIANCE" or "ui compliance"
- build_orchestrator_prompt output contains "UI DESIGN SYSTEM" or "design system"
- build_decomposition_prompt output contains "Write" tool reference
- DATABASE_INTEGRITY_STANDARDS is a non-empty string
- E2E_TESTING_STANDARDS is a non-empty string
- SEED DATA policy text present in appropriate prompt
- ENUM/STATUS REGISTRY policy text present in appropriate prompt
- SVC-xxx text present in architect-facing prompt
- Tracking document instructions present in milestone prompt when config enabled
- Tracking document instructions ABSENT in milestone prompt when config disabled
- E2E prompts contain coverage matrix instructions when config enabled
- E2E prompts contain fix cycle log instructions when config enabled

### Test File 6: Fix Function Completeness (`tests/test_fix_completeness.py`) — ~25 tests

- `_run_integrity_fix` source code contains elif branch for "deployment"
- `_run_integrity_fix` source code contains elif branch for "asset"
- `_run_integrity_fix` source code contains elif branch for "dual_orm"
- `_run_integrity_fix` source code contains elif branch for "default_value"
- `_run_integrity_fix` source code contains elif branch for "relationship"
- `_run_integrity_fix` docstring lists all 5 scan types
- Mock fix function exists and is callable
- UI fix function exists and is callable
- E2E fix function exists and is callable
- Each fix function signature includes correct parameters (cwd, config, violations, task_text, constraints, intervention, depth)
- Fix functions add recovery types to the recovery set
- Fix cycle log integration: fix function calls tracking document log function when enabled
- Fix functions are crash-isolated (verify try/except in cli.py around each call)

### Test File 7: Cross-Version Integration (`tests/test_cross_version_integration.py`) — ~40 tests

**Import compatibility:**
- `from agent_team.config import AgentTeamConfig, apply_depth_quality_gating, load_config` works
- `from agent_team.quality_checks import ScanScope, compute_changed_files` works
- `from agent_team.quality_checks import run_mock_data_scan, run_ui_compliance_scan, run_deployment_scan, run_asset_scan, run_dual_orm_scan, run_default_value_scan, run_relationship_scan` works
- `from agent_team.e2e_testing import detect_app_type, parse_e2e_results` works
- `from agent_team.tracking_documents import ...` works (all public functions)
- `from agent_team.design_reference import validate_ui_requirements_content, run_design_extraction_with_retry, generate_fallback_ui_requirements` works
- No circular imports between any two modules

**Config coexistence:**
- Full config with ALL sections → loads without error
- Config with v2.0 + v6.0 sections simultaneously → works
- All 11 dataclass defaults → AgentTeamConfig instantiates correctly
- _dict_to_config with all sections → returns valid config + complete overrides set

**Feature interaction:**
- v2.0 mock scan + v6.0 scoping: `run_mock_data_scan(root, scope=ScanScope(...))` returns correct results
- v2.2 UI scan + v6.0 scoping: `run_ui_compliance_scan(root, scope=ScanScope(...))` returns correct results
- v5.0 DB scan + v6.0 scoping: `run_dual_orm_scan(root, scope=ScanScope(...))` detection uses full files
- v5.0 DB scan + v6.0 scoping: `run_relationship_scan(root, scope=ScanScope(...))` entity_info from all files
- v3.0 E2E + v6.0 depth: thorough depth auto-enables E2E
- v4.0 tracking docs + v3.0 E2E: matrix generation after E2E tests
- v6.0 depth gating: quick mode disables v2.0 mock + v2.2 UI + v3.1 deploy/asset + v5.0 DB scans
- v6.0 backward compat: milestone.mock_data_scan config still works

**Full config round-trip:**
- Write YAML with all sections → load → verify all values correct
- Write YAML → load → apply_depth_quality_gating("quick") → verify all quick-mode gates applied
- Write YAML with user overrides → load → apply_depth_quality_gating("quick") → verify overrides respected

---

## PHASE 4: WIRING VERIFICATION

Phase 4 is performed by the **wiring-verifier** agent in Wave 2 (see Phase 2D above). The test-engineer should also verify these during testing:

### 4A: Execution Position
- Scope computation BEFORE any scan
- Depth gating BEFORE scope computation
- Each scan at correct position in pipeline (see Phase 2B, Review Area 2)
- E2E testing LAST in post-orchestration
- Tracking documents at correct lifecycle points

### 4B: Config Gating
- Each scan independently gated by its config flag
- Quick mode disables all post-orchestration scans
- Standard mode disables only PRD reconciliation
- Thorough mode auto-enables E2E
- User overrides survive all depth levels

### 4C: Crash Isolation
- Every scan call in its own try/except
- compute_changed_files failure → fallback to full scan
- PRD quality gate failure → safe fallback (run reconciliation)
- E2E phase in outer try/except with traceback logging
- Tracking document failures don't block pipeline

### 4D: Backward Compatibility
- No config → all defaults
- Old milestone.mock_data_scan config → migrated
- load_config() tuple unpacking at ALL callers
- apply_depth_quality_gating() without user_overrides → works
- All scan functions without scope → works

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass (7 new test files, ~280+ tests)
- ALL existing tests must pass (except 2 pre-existing known failures in test_mcp_servers.py — sequential_thinking always included)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green
- **Windows encoding note:** Use `encoding="utf-8"` when writing files with Unicode characters
- **If reviewers found bugs:** Fix them BEFORE running the full suite. Document each fix.
- **CRITICAL:** The total test count should exceed 4000 (existing ~3741 + ~280 new)

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# Production Readiness Audit — v2.0–v6.0 Verdict

## Executive Summary
- Audit scope: {N} source files, {M} functions, {K} config fields, {L} regex patterns
- Review findings: {X} CRITICAL, {Y} HIGH, {Z} MEDIUM, {W} LOW
- Bugs fixed: {N}
- New tests written: {N} across 7 files
- Total tests passing: {N}/{N}
- Regressions: 0

## Review Results

### CONFIG_SCANS_REVIEW.md Summary
- Checks: {pass}/{total}
- Issues found: {list}
- Fixed: {list}

### PIPELINE_REVIEW.md Summary
- Checks: {pass}/{total}
- Issues found: {list}
- Fixed: {list}

### PROMPTS_MODULES_REVIEW.md Summary
- Checks: {pass}/{total}
- Issues found: {list}
- Fixed: {list}

### E2E_WIRING_REPORT.md Summary
- Function call graph: {pass}/{total}
- Config consumption: {pass}/{total}
- Scan-fix-recovery chain: {pass}/{total}

## Failure Mode Coverage

| Failure Mode | Verified By | Test Count | Status |
|-------------|------------|------------|--------|
| Wiring gaps / dead code | E2E_WIRING_REPORT + test_cross_version_integration | {N} | PASS/FAIL |
| Wrong execution order | PIPELINE_REVIEW + test_pipeline_execution_order | {N} | PASS/FAIL |
| Broken config gating | CONFIG_SCANS_REVIEW + test_config_completeness | {N} | PASS/FAIL |
| Missing crash isolation | PIPELINE_REVIEW + test_pipeline_execution_order | {N} | PASS/FAIL |
| Backward incompatibility | All reviews + test_config_completeness | {N} | PASS/FAIL |
| Semantic scan incorrectness | CONFIG_SCANS_REVIEW + test_scan_pattern_correctness | {N} | PASS/FAIL |
| Prompt policy gaps | PROMPTS_MODULES_REVIEW + test_prompt_integrity | {N} | PASS/FAIL |
| Recovery loop incompleteness | PIPELINE_REVIEW + test_fix_completeness | {N} | PASS/FAIL |

## Production Readiness Matrix

| Version | Feature Count | Config Gates | Crash-Isolated | Tested | Wired E2E | Status |
|---------|-------------|--------------|----------------|--------|-----------|--------|
| v2.0 | 6 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v2.2 | 6 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v3.0 | 7 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v3.1 | 3 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v3.2 | 4 | N/A | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v4.0 | 3 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v5.0 | 5 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |
| v6.0 | 3 | {Y/N} | {Y/N} | {Y/N} | {Y/N} | READY/ISSUES |

## Verdict

**PRODUCTION READY** / **NEEDS FIXES** / **NOT READY**

{Justification paragraph}

### Remaining Action Items (if any)
1. {action item}
2. {action item}
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone reviews or tests anything. The ARCHITECTURE_INVENTORY.md is the single source of truth for what exists, where it lives, and how it's wired.

2. **FOLLOW EXISTING PATTERNS** — Every test must follow the exact patterns already in the codebase. Consistency over creativity. If existing tests use pytest fixtures, use pytest fixtures. If they use `tmp_path`, use `tmp_path`.

3. **READ BEFORE YOU REVIEW** — Read every file end-to-end before making any assessment. Understand the full context. Never claim something is missing without searching the entire file.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong. The test suite is the SPECIFICATION of production readiness.

5. **NO SHORTCUTS** — Every checklist item must be individually verified. Do not batch-pass sections. If a check takes 5 minutes, spend 5 minutes on it.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted since this prompt was written.

7. **CRASH ISOLATION** — Every new test must be independent. No test should depend on another test's side effects. Use `tmp_path` for file system isolation.

8. **BACKWARD COMPATIBLE** — Tests for backward compatibility are MANDATORY. A project with no config file must work identically to before any upgrades were applied.

9. **ADVERSARIAL MINDSET** — Reviewers must actively look for bugs. A review that finds zero issues should be treated with suspicion. Previous reviews of this codebase have CONSISTENTLY found real bugs (avg 5-10 per review round). If you find zero, look harder.

10. **OPTIMIZE IF YOU SEE IT** — If while reviewing you find bugs not covered by this prompt, report them. If while testing you find edge cases not listed, add them.

11. **RUN TESTS AFTER EACH PHASE** — test-engineer should run tests incrementally as files are written, not wait until all 7 are complete.

12. **WINDOWS COMPATIBILITY** — Use `encoding="utf-8"` when writing files with Unicode characters. Use `Path` objects for cross-platform paths. Use `tmp_path` for test isolation.

13. **REVIEW REPORTS ARE STRUCTURED** — Every review report must use the EXACT format specified (Summary → Findings → Assessment). This allows the team lead to synthesize quickly.

14. **EVERY BUG GETS A TEST** — If a reviewer finds a bug, the test-engineer MUST write a regression test for it before marking it fixed. No fix without test.

15. **COMPLETE COVERAGE OR EXPLAIN WHY NOT** — The final report must account for every v2.0–v6.0 feature. If a feature is not tested, document WHY (not just "skipped").
