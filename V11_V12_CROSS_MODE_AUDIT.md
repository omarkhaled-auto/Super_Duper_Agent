# v11/v12 Cross-Mode Coverage Audit

## Step 1: Operational Mode Mapping

### 1.1 Execution Modes

| Mode | Trigger | `_use_milestones` | Default Depth | Post-Orch Scans |
|------|---------|-------------------|---------------|-----------------|
| **Interactive** | No `--task`, no `--prd`, or `-i` flag | `False` | `args.depth` or `"standard"` | YES |
| **Standard Task** | `--task "..."` without `--prd` | `False` | Auto-detected via `detect_depth()` | YES |
| **Standard PRD** | `--prd` with `milestone.enabled=false` | `False` | `"exhaustive"` (auto-override) | YES |
| **Milestone PRD (PRD+)** | `--prd` with `milestone.enabled=true` | `True` | `"exhaustive"` (auto-override) | YES |

**Key facts:**
- NO "evolution mode" exists in the codebase. Only these 4 modes.
- ALL modes reach post-orchestration scans (line 4641+). Even if orchestration crashes, the `except` at line 4211 catches and continues.
- `_use_milestones` only gates 2 scans: mock data (line 4663) and UI compliance (line 4711). These run per-milestone instead, NOT disabled.
- PRD mode auto-overrides depth to `"exhaustive"` unless user explicitly passes `--depth`.

### 1.2 Depth Levels and Config Gating

Source: `apply_depth_quality_gating()` in `config.py:488-569`

| Config Gate | Quick | Standard | Thorough | Exhaustive |
|-------------|-------|----------|----------|------------|
| `post_orchestration_scans.mock_data_scan` | OFF | ON | ON | ON |
| `post_orchestration_scans.ui_compliance_scan` | OFF | ON | ON | ON |
| `post_orchestration_scans.api_contract_scan` | OFF | ON | ON | ON |
| `post_orchestration_scans.silent_data_loss_scan` | OFF | ON | ON | ON |
| `post_orchestration_scans.endpoint_xref_scan` | OFF | ON | ON | ON |
| `post_orchestration_scans.max_scan_fix_passes` | 0 | 1 (default) | 1 (default) | 2 |
| `integrity_scans.deployment_scan` | OFF | ON | ON | ON |
| `integrity_scans.asset_scan` | OFF | ON | ON | ON |
| `integrity_scans.prd_reconciliation` | OFF | OFF | ON* | ON |
| `database_scans.dual_orm_scan` | OFF | ON | ON | ON |
| `database_scans.default_value_scan` | OFF | ON | ON | ON |
| `database_scans.relationship_scan` | OFF | ON | ON | ON |
| `e2e_testing.enabled` | OFF | OFF (default) | ON (2 retries) | ON (3 retries) |
| `browser_testing.enabled` | OFF | OFF (default) | ON if PRD (3 retries) | ON if PRD (5 retries) |
| `quality.craft_review` | OFF | ON | ON | ON |
| `quality.production_defaults` | OFF | ON | ON | ON |

*\* PRD reconciliation at thorough has a quality gate: REQUIREMENTS.md must be >500 bytes and contain REQ-xxx patterns.*

### 1.3 Post-Orchestration Scan Pipeline (Complete)

Pipeline order in `cli.py` (lines 4641-5670+):

| # | Scan | CLI Line | Config Gate | Mode Guard |
|---|------|----------|-------------|------------|
| 1 | Scan Scope Computation | 4641 | always | none |
| 2 | Mock Data Scan | 4663 | `post_orch.mock_data_scan OR milestone.mock_data_scan` | `if not _use_milestones` |
| 3 | UI Compliance Scan | 4711 | `post_orch.ui_compliance_scan OR milestone.ui_compliance_scan` | `if not _use_milestones` |
| 4 | Deployment Integrity | 4758 | `integrity_scans.deployment_scan` | none |
| 5 | Asset Integrity | 4803 | `integrity_scans.asset_scan` | none |
| 6 | PRD Reconciliation | 4847 | `integrity_scans.prd_reconciliation` | none |
| 7 | Dual ORM Scan | 4894 | `database_scans.dual_orm_scan` | none |
| 8 | Default Value Scan | 4944 | `database_scans.default_value_scan` | none |
| 9 | Relationship Scan | 4994 | `database_scans.relationship_scan` | none |
| 10 | API Contract Scan | 5046 | `post_orch.api_contract_scan` + `has_backend AND has_frontend` | none |
| 11 | Silent Data Loss (SDL) Scan | 5097 | `post_orch.silent_data_loss_scan` | none |
| 12 | Endpoint XREF Scan | 5145 | `post_orch.endpoint_xref_scan` | none |
| 13 | E2E Testing Phase | 5195 | `e2e_testing.enabled` | none |
| 14 | E2E Quality Scan | 5438 | `e2e_testing.enabled` | none |
| 15 | Browser Testing Phase | 5465 | `browser_testing.enabled` | none |

### 1.4 Scan Fix Function Table

| # | Scan | Fix Function | Loop Pattern | Re-scans After Fix? | Report-Only? |
|---|------|-------------|-------------|---------------------|-------------|
| 2 | Mock Data | `_run_mock_data_fix()` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 3 | UI Compliance | `_run_ui_compliance_fix()` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 4 | Deployment Integrity | `_run_integrity_fix(scan_type="deployment")` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 5 | Asset Integrity | `_run_integrity_fix(scan_type="asset")` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 6 | PRD Reconciliation | `_run_prd_reconciliation()` | NO loop (single LLM call) | Parses output, NO re-scan | **REPORT-ONLY** |
| 7 | Dual ORM | `_run_integrity_fix(scan_type="database_dual_orm")` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 8 | Default Value | `_run_integrity_fix(scan_type="database_defaults")` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 9 | Relationship | `_run_integrity_fix(scan_type="database_relationships")` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 10 | API Contract | `_run_api_contract_fix()` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 11 | SDL | `_run_silent_data_loss_fix()` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 12 | Endpoint XREF | `_run_endpoint_xref_fix()` | `for _fix_pass in range(max(1, _max_passes))` | YES | NO |
| 13 | E2E Backend | `_run_e2e_fix()` → `_run_backend_e2e_tests()` | `while health not in ("passed","skipped","unknown") and retries < max_fix_retries` | YES (re-runs tests) | NO |
| 13 | E2E Frontend | `_run_e2e_fix()` → `_run_frontend_e2e_tests()` | `while health not in ("passed","skipped","unknown") and retries < max_fix_retries` | YES (re-runs tests) | NO |
| 14 | E2E Quality | **NONE** | **NO loop** | **NO** | **REPORT-ONLY** |
| 15 | Browser Workflows | `_run_browser_workflow_fix()` → `_run_browser_workflow_executor()` | `while not workflow_passed and retries <= max_fix_retries` | YES (re-executes) | NO |
| 15 | Browser Regression | `_run_browser_regression_sweep()` → `_run_browser_workflow_fix()` | per-workflow loop | YES (re-executes) | NO |

**Summary**: 13/15 pipeline stages have self-healing fix loops with re-scan verification. Only PRD Reconciliation and E2E Quality Scan are report-only.

**Fix loop mechanics:**
- Static scans use `max_scan_fix_passes` config (default 1, exhaustive 2, quick 0 = scan-only)
- E2E uses `max_fix_retries` config (thorough 2, exhaustive 3)
- Browser uses `max_fix_retries` config (thorough 3, exhaustive 5)
- When `max_scan_fix_passes = 0`: loop runs exactly once (scan only, no fix) — `range(max(1, 0) if 0 > 0 else 1)` = `range(1)`

---

## Step 2: v11 Feature Trace (CP-43 through CP-48)

### CP-43: ENUM-004 Static Scan (.NET JsonStringEnumConverter)
- **Location**: `_check_enum_serialization()` in `quality_checks.py:2989`
- **Invoked by**: `run_api_contract_scan()` at line 3322/3333/3348/3368
- **CLI block**: API Contract Scan at `cli.py:5046`
- **Config gate**: `config.post_orchestration_scans.api_contract_scan` + `has_backend AND has_frontend`
- **Fix function**: `_run_api_contract_fix()` (shared with API-001/002/003/004)
- **Depth**: quick=OFF, standard+=ON

### CP-44: SDL-001 Static Scan (CQRS Missing Persistence)
- **Location**: `_check_cqrs_persistence()` in `quality_checks.py`
- **CLI block**: Silent Data Loss scan at `cli.py:5097`
- **Config gate**: `config.post_orchestration_scans.silent_data_loss_scan`
- **Fix function**: `_run_silent_data_loss_fix()`
- **Depth**: quick=OFF, standard+=ON

### CP-45: API-002 Bidirectional Scan (Frontend Extra Fields)
- **Location**: `_check_frontend_extra_fields()` in `quality_checks.py:3156`
- **Invoked by**: `run_api_contract_scan()` at line 3362
- **CLI block**: API Contract Scan at `cli.py:5046`
- **Config gate**: `config.post_orchestration_scans.api_contract_scan` + `has_backend AND has_frontend`
- **Fix function**: `_run_api_contract_fix()` (shared)
- **Depth**: quick=OFF, standard+=ON

### CP-46: Architect .NET Serialization Prompt
- **Location**: `ARCHITECT_PROMPT` in `agents.py` (line ~994 area)
- **Loaded by**: `build_agent_definitions()` → `agents["architect"]`
- **Consumed by**: Orchestrator when it delegates to architect agent
- **Config gate**: `config.agents.architect.enabled` (default True)
- **Mode/Depth**: **UNIVERSAL** — all modes, all depths (prompts are compiled into agent definitions)

### CP-47: Reviewer ENUM-004/SDL-001/SDL-002/SDL-003 Prompt
- **Location**: `CODE_REVIEWER_PROMPT` in `agents.py:1346-1367`
- **Loaded by**: `build_agent_definitions()` → `agents["code-reviewer"]`
- **Consumed by**: Orchestrator when it delegates to code-reviewer agent
- **Config gate**: `config.agents.code_reviewer.enabled` (default True)
- **Mode/Depth**: **UNIVERSAL** — all modes, all depths
- **Note**: Quick depth strips "CODE CRAFT REVIEW" section (lines 1479-1489) but this does NOT affect ENUM-004 or SDL directives (they're at lines 1346-1367, well above the stripped section)

### CP-48: E2E Mutation Verification Prompt
- **Location**: `BACKEND_E2E_PROMPT` in `e2e_testing.py` (line ~713 area)
- **Consumed by**: E2E backend testing agent
- **Config gate**: `config.e2e_testing.enabled`
- **Depth**: quick=OFF, standard=OFF, thorough+=ON

---

## Step 3: v12 Feature Trace (CP-49 through CP-54)

### CP-49: XREF-001/002 Static Scan (Endpoint Cross-Reference)
- **Location**: `run_endpoint_xref_scan()` in `quality_checks.py` (after line 3371)
- **CLI block**: Endpoint XREF Scan at `cli.py:5145`
- **Config gate**: `config.post_orchestration_scans.endpoint_xref_scan`
- **Fix function**: `_run_endpoint_xref_fix()`
- **Depth**: quick=OFF, standard+=ON

### CP-50: API-004 Static Scan (Write-Side Field Passthrough)
- **Location**: `_check_request_field_passthrough()` in `quality_checks.py`
- **Invoked by**: `run_api_contract_scan()` (integrated in API contract scan)
- **CLI block**: API Contract Scan at `cli.py:5046`
- **Config gate**: `config.post_orchestration_scans.api_contract_scan` + `has_backend AND has_frontend`
- **Fix function**: `_run_api_contract_fix()` (shared)
- **Depth**: quick=OFF, standard+=ON

### CP-51: E2E Prompt Directives (6 total)
- **Location**: `e2e_testing.py`
  - BACKEND_E2E_PROMPT: Endpoint Exhaustiveness Rule, Role Authorization Rule
  - FRONTEND_E2E_PROMPT: State Persistence Rule, Revisit Testing Rule, Dropdown Verification Rule, Button Outcome Verification Rule
- **Consumed by**: E2E testing agents (backend API, frontend Playwright)
- **Config gate**: `config.e2e_testing.enabled`
- **Depth**: quick=OFF, standard=OFF, thorough+=ON

### CP-52: Browser Prompt Directives (2 total)
- **Location**: `browser_testing.py`
  - BROWSER_WORKFLOW_EXECUTOR_PROMPT: DEEP VERIFICATION RULES
  - BROWSER_REGRESSION_SWEEP_PROMPT: Content Verification
- **Consumed by**: Browser testing agents (workflow executor, regression sweep)
- **Config gate**: `config.browser_testing.enabled`
- **Depth**: quick=OFF, standard=OFF, thorough+PRD=ON, non-PRD=OFF

### CP-53: Architect Endpoint Completeness Prompt
- **Location**: `ARCHITECT_PROMPT` in `agents.py` (after line 994)
- **Loaded by**: `build_agent_definitions()` → `agents["architect"]`
- **Consumed by**: Orchestrator when it delegates to architect agent
- **Config gate**: `config.agents.architect.enabled` (default True)
- **Mode/Depth**: **UNIVERSAL**

### CP-54: Reviewer Endpoint Cross-Reference Prompt
- **Location**: `CODE_REVIEWER_PROMPT` in `agents.py:1296-1303`
- **Loaded by**: `build_agent_definitions()` → `agents["code-reviewer"]`
- **Consumed by**: Orchestrator when it delegates to code-reviewer agent
- **Config gate**: `config.agents.code_reviewer.enabled` (default True)
- **Mode/Depth**: **UNIVERSAL**
- **Note**: Located above the "CODE CRAFT REVIEW" stripping zone — never affected by quick depth stripping

---

## Step 4: Cross-Mode Coverage Matrix

### Legend
- **ON**: Feature is active and will execute
- **OFF**: Feature is disabled by depth gating
- **PROMPT**: Prompt exists in agent definition but the phase that consumes it doesn't run
- **RELOCATED**: Not skipped — runs per-milestone instead of post-orchestration
- **PRD-ONLY**: Only enabled when in PRD mode (Standard PRD or Milestone PRD)

### 4.1 Static Scans

| Checkpoint | Quick | Standard | Thorough | Exhaustive | Mode Exception |
|-----------|-------|----------|----------|------------|----------------|
| CP-43: ENUM-004 scan | OFF | ON | ON | ON (2-pass) | Requires backend+frontend |
| CP-44: SDL-001 scan | OFF | ON | ON | ON (2-pass) | none |
| CP-45: API-002 bidirectional | OFF | ON | ON | ON (2-pass) | Requires backend+frontend |
| CP-49: XREF-001/002 scan | OFF | ON | ON | ON (2-pass) | none |
| CP-50: API-004 scan | OFF | ON | ON | ON (2-pass) | Requires backend+frontend |

### 4.2 E2E & Browser Phases

| Checkpoint | Quick | Standard | Thorough | Exhaustive | Mode Exception |
|-----------|-------|----------|----------|------------|----------------|
| CP-48: E2E mutation prompt | OFF | OFF | ON (2 retries) | ON (3 retries) | none |
| CP-51: E2E 6 directives | OFF | OFF | ON (2 retries) | ON (3 retries) | none |
| CP-52: Browser 2 directives | OFF | OFF | PRD-ONLY (3 retries) | PRD-ONLY (5 retries) | Standard Task: always OFF |

### 4.3 Agent Prompt Directives (Universal)

| Checkpoint | Quick | Standard | Thorough | Exhaustive | Mode Exception |
|-----------|-------|----------|----------|------------|----------------|
| CP-46: Architect .NET serial. | ON | ON | ON | ON | none |
| CP-47: Reviewer ENUM/SDL | ON | ON | ON | ON | none |
| CP-53: Architect endpoint compl. | ON | ON | ON | ON | none |
| CP-54: Reviewer endpoint XREF | ON | ON | ON | ON | none |

### 4.4 Mode-Specific Behavior (Milestone PRD only)

| Scan | Standard PRD | Milestone PRD | Difference |
|------|-------------|---------------|------------|
| Mock Data (post-orch) | ON | RELOCATED (per-milestone) | Equivalent coverage |
| UI Compliance (post-orch) | ON | RELOCATED (per-milestone) | Equivalent coverage |
| All other scans | ON | ON | Identical |

### 4.5 Summary Grid (12 Checkpoints x 4 Depth Levels)

| | Quick | Standard | Thorough | Exhaustive |
|---|:---:|:---:|:---:|:---:|
| CP-43 ENUM-004 scan | OFF | ON | ON | ON |
| CP-44 SDL-001 scan | OFF | ON | ON | ON |
| CP-45 API-002 bidir. | OFF | ON | ON | ON |
| CP-46 Architect prompt | ON | ON | ON | ON |
| CP-47 Reviewer prompt | ON | ON | ON | ON |
| CP-48 E2E mutation | OFF | OFF | ON | ON |
| CP-49 XREF-001/002 | OFF | ON | ON | ON |
| CP-50 API-004 scan | OFF | ON | ON | ON |
| CP-51 E2E 6 directives | OFF | OFF | ON | ON |
| CP-52 Browser directives | OFF | OFF | PRD-ONLY | PRD-ONLY |
| CP-53 Architect prompt | ON | ON | ON | ON |
| CP-54 Reviewer prompt | ON | ON | ON | ON |

**Coverage percentages:**
- Quick: 4/12 = 33% (prompts only)
- Standard: 9/12 = 75% (scans + prompts, no E2E/browser)
- Thorough: 11/12 = 92% (all except browser in non-PRD)
- Exhaustive: 11/12 = 92% (all except browser in non-PRD)
- Exhaustive + PRD: 12/12 = 100%

---

## Step 5: Gap Analysis

### GAP-1: Quick Depth — Zero Scan Coverage
**Affected checkpoints**: CP-43, CP-44, CP-45, CP-48, CP-49, CP-50, CP-51, CP-52
**Root cause**: `apply_depth_quality_gating()` sets ALL scan configs to `False` at quick depth (config.py:514-542)
**Impact**: At quick depth, the ONLY v11/v12 protection is the 4 prompt directives (CP-46, CP-47, CP-53, CP-54). These are probabilistic — the LLM may or may not follow them.
**Recommendation**: This is BY DESIGN. Quick depth is for rapid iteration. The prompts provide a probabilistic safety net. No fix needed.

### GAP-2: Standard Depth — No E2E Phase
**Affected checkpoints**: CP-48, CP-51 (6 E2E directives), CP-52 (2 browser directives)
**Root cause**: `e2e_testing.enabled` defaults to `False` and is only auto-enabled at thorough+ depth (config.py:550, 560)
**Impact**: Standard depth misses 8 prompt directives that target E2E test quality. These directives catch bugs like:
- Revisit testing (Bug #1, #9, #25)
- Button outcome verification (Bug #27, #28, #36)
- Dropdown verification (Bug #30)
- State persistence (Bug #9, #33)
**Recommendation**: This is BY DESIGN. E2E testing is expensive. Standard depth relies on static scans and prompts. For production builds, users should use thorough or exhaustive.

### GAP-3: Browser Testing — PRD-Only
**Affected checkpoint**: CP-52
**Root cause**: Browser testing auto-enable is gated by `if prd_mode or config.milestone.enabled` (config.py:554, 564)
**Impact**: Standard Task mode with thorough/exhaustive depth gets E2E but NOT browser testing. The 2 browser directives (Deep Verification Rules, Content Verification) never fire.
**Recommendation**: Intentional design — browser testing requires a PRD to generate meaningful workflows. Without a PRD, there's no requirements matrix to derive test workflows from. The `generate_browser_workflows()` function needs `requirements_dir` content.

### GAP-4: Interactive Mode — `depth` Variable Undefined
**Affected**: ALL fix function calls in post-orchestration scan blocks
**Root cause**: In interactive mode, `depth` is only set inside `_run_interactive()` as a local variable (`last_depth`). At `main()` scope, `depth` is only set in the `else:` branch (line 4144). Post-orchestration fix calls use `depth=depth if not _use_milestones else "standard"` which would crash with `NameError`.
**Impact**: If interactive mode triggers scan violations requiring fixes, the fix function calls would crash. However, `apply_depth_quality_gating()` IS called inside `_run_interactive()` so configs are properly gated. The crash would only occur if violations are found AND the fix loop tries to invoke a sub-orchestrator.
**Severity**: MEDIUM — known issue from v7.0 Production Readiness Audit. Crash is isolated by try/except around each scan block, so it doesn't bring down the entire pipeline. The scan still runs; only the fix function crashes.
**Recommendation**: Add `depth = depth_override or "standard"` before the `if interactive:` branch in `main()`.

### GAP-5: E2E Quality Scan — Report-Only, No Fix Loop
**Affected**: E2E-001 through E2E-007 violations detected by `run_e2e_quality_scan()`
**Root cause**: The E2E quality scan (cli.py:5438) only prints warnings — no fix function, no loop.
**Impact**: Static analysis of E2E test code finds issues (hardcoded ports, shallow assertions, etc.) but does not auto-fix them. These are informational warnings only.
**Recommendation**: Acceptable for now. E2E quality issues in test code are less critical than issues in production code. The E2E fix loop handles actual test failures; the quality scan is supplementary.

### GAP-6: API Contract + XREF Scans — Full-Stack Gate
**Affected checkpoints**: CP-43 (ENUM-004), CP-45 (API-002 bidir), CP-50 (API-004)
**Root cause**: API contract scan has additional gate: `if _app_info.has_backend and _app_info.has_frontend` (cli.py:5051)
**Impact**: Backend-only or frontend-only projects skip all API contract verification including ENUM-004 and API-004. The XREF scan (CP-49) does NOT have this gate — it only requires `endpoint_xref_scan` config.
**Recommendation**: Correct by design. API contract verification inherently requires both sides. ENUM-004 (inside api_contract_scan) could theoretically run for backend-only projects, but the practical value is low without a frontend consumer.

---

## Step 6: Prompt Injection Cross-Mode Check

### 6.1 Agent Prompt Compilation Path

All agent prompts flow through the same path regardless of mode:

```
main() → _setup_orchestrator_session() → build_agent_definitions()
                                              ├── ARCHITECT_PROMPT → agents["architect"]
                                              ├── CODE_WRITER_PROMPT → agents["code-writer"]
                                              ├── CODE_REVIEWER_PROMPT → agents["code-reviewer"]
                                              └── (other agents...)
```

`_setup_orchestrator_session()` is called by:
- `_run_interactive()` (interactive mode)
- `_run_single()` (standard task / standard PRD)
- Per-milestone orchestrator calls in `_run_prd_milestones()` (milestone PRD)

### 6.2 Prompt Directive Locations (v11/v12)

| Directive | Prompt Constant | Line Range | Strippable? |
|-----------|----------------|------------|-------------|
| .NET serialization | ARCHITECT_PROMPT | ~994 | NO |
| Endpoint completeness | ARCHITECT_PROMPT | ~994 | NO |
| API Contract Fields | CODE_REVIEWER_PROMPT | 1276-1293 | NO |
| Endpoint Cross-Ref | CODE_REVIEWER_PROMPT | 1296-1303 | NO |
| ENUM-004 reviewer | CODE_REVIEWER_PROMPT | 1346-1352 | NO |
| SDL-001/002/003 reviewer | CODE_REVIEWER_PROMPT | 1355-1367 | NO |
| CODE CRAFT REVIEW | CODE_REVIEWER_PROMPT | 1479-1489 | **YES** (quick) |

**Key finding**: The "CODE CRAFT REVIEW" stripping (lines 1479-1489, triggered when `config.quality.craft_review = False` at quick depth) removes ONLY the 6 CRAFT scans (CRAFT-001 through CRAFT-006). ALL v11/v12 directives are located ABOVE line 1479 and are NEVER stripped.

### 6.3 E2E/Browser Prompt Compilation

E2E and browser prompts are compiled strings (not conditional):

| Prompt | Module | Injected Directives | Active When |
|--------|--------|-------------------|-------------|
| BACKEND_E2E_PROMPT | e2e_testing.py | Mutation Verification (v11), Endpoint Exhaustiveness (v12), Role Authorization (v12) | E2E phase runs |
| FRONTEND_E2E_PROMPT | e2e_testing.py | State Persistence (v12), Revisit Testing (v12), Dropdown Verification (v12), Button Outcome (v12) | E2E phase runs |
| BROWSER_WORKFLOW_EXECUTOR_PROMPT | browser_testing.py | Deep Verification Rules (v12) | Browser phase runs |
| BROWSER_REGRESSION_SWEEP_PROMPT | browser_testing.py | Content Verification (v12) | Browser phase runs |

These prompts exist in the code always, but are only consumed when the respective phase executes. The prompt text is NOT conditionally compiled — the gating is at the phase execution level.

### 6.4 Prompt Injection Verdict

| Concern | Status |
|---------|--------|
| v11/v12 prompts missing from any mode | **NO** — all prompts are universal |
| Quick depth stripping removes v11/v12 content | **NO** — stripping only affects CRAFT section (lines 1479-1489) |
| Milestone mode uses different prompts | **NO** — same `build_agent_definitions()` path |
| Interactive mode uses different prompts | **NO** — same `_setup_orchestrator_session()` path |
| E2E/browser prompts conditionally compiled | **NO** — prompts are static strings, gating is at phase level |

**VERDICT**: All v11/v12 prompt directives are correctly injected in ALL modes. The only limitation is that E2E and browser prompt directives are inert when their respective phases don't run (standard and quick depths).

---

## Summary

### What Works
1. **Static scans (v11/v12)** run in ALL modes at standard+ depth — no mode-specific gaps
2. **Prompt directives** are UNIVERSAL — present in all modes, all depths, never stripped
3. **Milestone PRD** relocates mock/UI scans per-milestone but does NOT skip v11/v12 features
4. **Fix loops** are comprehensive — 13/15 pipeline stages self-heal with re-scan verification
5. **Exhaustive + PRD** mode achieves 100% coverage of all 12 v11/v12 checkpoints

### What Doesn't Work
1. **Quick depth** = 33% coverage (prompts only, all scans disabled) — BY DESIGN
2. **Standard depth** = 75% coverage (no E2E/browser) — BY DESIGN
3. **Non-PRD builds** never get browser testing, even at exhaustive — BY DESIGN
4. **Interactive mode** has undefined `depth` variable for fix functions — KNOWN BUG (v7.0)
5. **E2E Quality Scan** is report-only, no fix loop — ACCEPTABLE

### Risk Assessment

| Depth | Bug Detection | Self-Healing | Confidence |
|-------|--------------|-------------|------------|
| Quick | Prompt-only (probabilistic) | None | LOW |
| Standard | Deterministic scans + prompts | Static scan fix loops | MEDIUM |
| Thorough | Full scans + E2E + prompts | All fix loops active | HIGH |
| Exhaustive + PRD | Maximum coverage | Multi-pass fix loops + browser | HIGHEST |
