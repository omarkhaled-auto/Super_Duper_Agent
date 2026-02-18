# Audit-Team Architecture Design

**Author**: post-build-3 investigation agent
**Date**: 2026-02-18
**Status**: DESIGN COMPLETE -- Ready for implementation

---

## Part 1: Current System Investigation

### 1.1 Where the Current Reviewer Gets Invoked

The current code-reviewer agent is invoked in **three distinct places** in the pipeline:

#### A. Inside the Convergence Loop (Orchestrator-Managed)
**Location**: `agents.py` Section 3 (lines 160-238) -- ORCHESTRATOR_SYSTEM_PROMPT
**Trigger**: The orchestrator deploys the review fleet in step 2 of the convergence loop after the coding fleet.
**Mechanism**: The orchestrator (Claude SDK orchestrator) directly spawns `code-reviewer` sub-agents via the agent definitions system. The orchestrator decides when and how many reviewers to deploy based on the depth table (1-2 at quick, 5-8 at exhaustive).
**Key constraint**: GATE 1 says only code-reviewer and test-runner can mark items `[x]`. GATE 5 says Python runtime enforces at least 1 review cycle.

#### B. Per-Milestone Review Recovery Loop
**Location**: `cli.py` lines 1374-1435
**Trigger**: After each milestone completes, `mm.check_milestone_health()` is called. If health is `"failed"` or `"degraded"` and either zero review cycles or convergence ratio below `recovery_threshold`, recovery triggers.
**Mechanism**: Calls `_run_review_only()` up to `config.milestone.review_recovery_retries` times (default 1). Each call spawns a new orchestrator session with a focused review prompt. After each attempt, re-checks health. Breaks if healthy or above recovery threshold.

#### C. Post-Orchestration Review Recovery
**Location**: `cli.py` lines 4854-4993
**Trigger**: After all orchestration completes (both standard and milestone modes), `_check_convergence_health()` (standard) or `aggregate_milestone_convergence()` (milestones) produces a `ConvergenceReport`. If health is `"failed"`, `"degraded"` below threshold, or `"unknown"` with milestones/PRD mode, recovery triggers.
**Extra enforcement**: GATE 5 -- even if health appears fine, if `review_cycles == 0` and `total_requirements > 0`, recovery is forced (line 4916-4928).
**Mechanism**: Calls `_run_review_only()` once (no loop -- single shot at post-orchestration level). After recovery, re-checks health and adjusts cycle counter if LLM didn't increment markers.

### 1.2 What Prompt the Current Reviewer Uses

**Primary prompt**: `CODE_REVIEWER_PROMPT` in `agents.py` (line 1206-1405+), a ~200-line adversarial reviewer prompt containing:

1. **Core review loop** (lines 1210-1228): Read REQUIREMENTS.md, find implementations, try to break them, mark `[x]`/`[ ]`
2. **Review Log format** (line 1241): `| cycle | agent-id | item-id | PASS/FAIL | detailed issues |`
3. **Harshness rules** (lines 1244-1250): Reject more than accept, every issue must be file:line specific
4. **Review cycle tracking** (lines 1252-1270): Must append `(review_cycles: N)` to every evaluated item
5. **Integration verification** (lines 1272-1282): WIRE-xxx items -- trace from entry point to feature
6. **SVC-xxx verification** (lines 1284-1294): Service-to-API mock data detection (AUTOMATIC FAILURE on any mock)
7. **API contract field verification** (lines 1296-1314): API-001/002/003 field-level checks
8. **Endpoint cross-reference** (lines 1316-1323): XREF-001/002, API-004
9. **UI compliance** (lines 1325-1339): Color/font/spacing against UI_REQUIREMENTS.md
10. **Seed data verification** (lines 1341-1350): SEED-001..003
11. **Enum/Status registry** (lines 1352-1373): ENUM-001..004
12. **Silent data loss** (lines 1375-1387): SDL-001..003
13. **Orphan detection** (lines 1389-1405): Files/exports/components not imported anywhere
14. **Code craft review** (conditional, stripped at quick depth): 12+ craft patterns

**Recovery prompt**: Built in `_run_review_only()` (line 3544-3561) -- a focused prompt that instructs the orchestrator to deploy code-reviewer agents for unchecked items. It passes the situation (zero-cycle vs partial coverage), references the requirements file, and demands verification + fix cycle log updates.

### 1.3 How Findings Are Reported

**Two reporting mechanisms**:

1. **REQUIREMENTS.md checkboxes**: Items marked `[x]` (passed) or `[ ]` (failed) with `(review_cycles: N)` inline markers. This is the PRIMARY convergence signal -- the Python health checker parses these checkboxes to compute `checked/total` ratio.

2. **Review Log table**: Appended to REQUIREMENTS.md. Format: `| cycle | reviewer-id | item-id | PASS/FAIL | detailed issues |`. This is informational -- no code parses the Review Log for automated decisions. It serves as the human-readable audit trail.

### 1.4 How Findings Feed Back to Fix Agents

The feedback loop is **orchestrator-mediated**:
1. Reviewer writes issues to the Review Log in REQUIREMENTS.md
2. Orchestrator reads REQUIREMENTS.md, sees unchecked `[ ]` items
3. Orchestrator deploys debugger fleet (step 4 in convergence loop)
4. Debuggers read Review Log entries for their assigned items
5. After fix: mandatory re-review (GATE 2 -- Debug -> Re-Review is NON-NEGOTIABLE)

For **post-orchestration scans** (the static analysis path), findings are fed differently:
1. Scan functions return `list[Violation]` objects with `check`, `file_path`, `line`, `message`, `severity`
2. `_run_*_fix()` functions format violations into a fix prompt string
3. A new orchestrator session receives the fix prompt and deploys code-writers
4. No re-scan loop by default; `max_scan_fix_passes` (default 1) controls multi-pass behavior

### 1.5 State Boundaries Around Review

**ConvergenceReport** (`state.py` lines 71-82):
- `total_requirements: int` -- count of all `- [x]` + `- [ ]` lines
- `checked_requirements: int` -- count of `- [x]` lines only
- `review_cycles: int` -- max `(review_cycles: N)` found across all items
- `convergence_ratio: float` -- checked/total
- `review_fleet_deployed: bool` -- cycles > 0
- `health: str` -- "healthy" | "degraded" | "failed" | "unknown"
- `escalated_items: list[str]` -- items at escalation threshold still unchecked
- `zero_cycle_milestones: list[str]` -- milestones with 0 review cycles

**RunState** fields for convergence tracking:
- `convergence_cycles: int`
- `requirements_checked: int`
- `requirements_total: int`
- `current_phase: str` -- includes "review_recovery"
- `completed_phases: list[str]`

### 1.6 How the Orchestrator Decides When Review Is "Done"

**Inside the convergence loop** (orchestrator-internal):
- Step 3: "Are ALL items `[x]`?" If yes -> proceed to testing. If no -> check escalation threshold -> deploy debuggers -> loop.
- Max cycles: `config.convergence.max_cycles` (default 10). If exceeded, STOP and ask user.

**Post-orchestration** (Python-enforced in `cli.py`):
- **healthy**: `convergence_ratio >= min_convergence_ratio` (default 0.9) -> done
- **degraded**: ratio between `degraded_threshold` (0.5) and `min_convergence_ratio` (0.9) with review fleet deployed -> warning but may trigger recovery if below `recovery_threshold` (0.8)
- **failed**: below `degraded_threshold`, or review fleet never deployed -> recovery pass
- GATE 5: If `review_cycles == 0` and `total_requirements > 0`, force recovery regardless of apparent health

### 1.7 Existing Post-Orchestration Scan Pipeline (cli.py ~4995-5560)

After review recovery, the pipeline runs these scans in sequence, each independently gated:

| Order | Scan | Function | Config Gate | Fix Function |
|-------|------|----------|-------------|-------------|
| 1 | Mock data | `run_mock_data_scan()` | `post_orchestration_scans.mock_data_scan` | `_run_mock_data_fix()` |
| 2 | UI compliance | `run_ui_compliance_scan()` | `post_orchestration_scans.ui_compliance_scan` | `_run_ui_compliance_fix()` |
| 3 | Deployment integrity | `run_deployment_scan()` | `integrity_scans.deployment_scan` | `_run_integrity_fix(scan_type="deployment")` |
| 4 | Asset integrity | `run_asset_scan()` | `integrity_scans.asset_scan` | `_run_integrity_fix(scan_type="asset")` |
| 5 | PRD reconciliation | LLM sub-orchestrator | `integrity_scans.prd_reconciliation` | `_run_prd_reconciliation()` |
| 6 | Database dual ORM | `run_dual_orm_scan()` | `database_scans.dual_orm_scan` | `_run_integrity_fix(scan_type="database_dual_orm")` |
| 7 | Database defaults | `run_default_value_scan()` | `database_scans.default_value_scan` | `_run_integrity_fix(scan_type="database_defaults")` |
| 8 | Database relationships | `run_relationship_scan()` | `database_scans.relationship_scan` | `_run_integrity_fix(scan_type="database_relationships")` |
| 9 | API contract | `run_api_contract_scan()` | `post_orchestration_scans.api_contract_scan` | `_run_api_contract_fix()` |
| 10 | Silent data loss | `run_silent_data_loss_scan()` | `post_orchestration_scans.silent_data_loss_scan` | `_run_silent_data_loss_fix()` |
| 11 | Endpoint XREF | `run_endpoint_xref_scan()` | `post_orchestration_scans.endpoint_xref_scan` | `_run_endpoint_xref_fix()` |

Each scan follows the same pattern:
1. Call scan function -> get `list[Violation]`
2. If violations found -> call `_run_*_fix()` (sub-orchestrator session)
3. `max_scan_fix_passes` controls multi-pass behavior (scan -> fix -> re-scan loop)
4. Each scan in own try/except for crash isolation

After scans: E2E testing phase, then browser testing phase (these require running servers and remain separate).

### 1.8 Fix Function Pattern

All fix functions (`_run_mock_data_fix`, `_run_api_contract_fix`, `_run_integrity_fix`, etc.) follow the same architecture:

```python
async def _run_*_fix(
    cwd, config, violations, task_text, constraints, intervention, depth
) -> float:
    # 1. Format violations into text (max 20)
    violations_text = "\n".join(f"  - [{v.check}] {v.file_path}:{v.line} -- {v.message}" ...)
    # 2. Build focused fix prompt with [PHASE: ...] header
    fix_prompt = f"[PHASE: FOO FIX]\n\n{violations_text}\n\nINSTRUCTIONS:\n..."
    # 3. Optionally inject fix cycle log
    # 4. Build SDK options via _build_options()
    # 5. Run sub-orchestrator session: ClaudeSDKClient(options) -> query(fix_prompt)
    # 6. Return cost
```

---

## Part 2: New Audit-Team Architecture

### 2.1 Design Philosophy

The current system has a **monolithic reviewer** that does everything -- requirement verification, mock data checking, wiring verification, UI compliance, seed data, enum registry, orphan detection, and code craft review -- all in a single 200+ line prompt. This creates:

1. **Cognitive overload**: One agent must hold 13+ check categories in context
2. **Incomplete coverage**: The LLM frequently skips checks or does them superficially
3. **No parallelism**: Checks run sequentially through one agent
4. **No structured output**: Findings are embedded in prose/table format, not machine-parseable
5. **No prioritization**: CRITICAL issues mixed with style nits

The audit-team replaces this with **5 specialized auditors running in parallel**, a **scorer** that aggregates findings, and a **fix dispatcher** that groups issues by file scope.

### 2.2 The 5 Specialized Auditors

Each auditor is a sub-orchestrator session with a focused prompt, limited scope, and structured output format.

#### Auditor 1: Requirements Auditor
**Checks**: REQ-xxx, FUNC-xxx, FEAT-xxx, DESIGN-xxx items
**Input**: Reads REQUIREMENTS.md, searches codebase for implementations
**Method**:
- For each `- [ ]` or `- [x]` item, locate the implementation using Read/Glob/Grep
- Verify the implementation FULLY satisfies the requirement text
- Check edge cases, error handling, validation
- Verify the requirement against the [ORIGINAL USER REQUEST] text
**Output**: Structured findings list with requirement_id, verdict (PASS/FAIL/PARTIAL), file:line evidence
**Token budget**: Medium -- reads REQUIREMENTS.md once, then targeted file reads
**Tools**: Read, Glob, Grep

#### Auditor 2: Technical Auditor
**Checks**: TECH-xxx, code quality, conventions, SLOP patterns, mock data, UI compliance
**Input**: Reads REQUIREMENTS.md technical section, UI_REQUIREMENTS.md, scans codebase
**Method**:
- Receives PRE-COMPUTED results from existing Python scan functions (zero-cost static analysis):
  - `run_mock_data_scan()` -- MOCK-001..008
  - `run_ui_compliance_scan()` -- UI-001..004
  - `run_spot_checks()` -- FRONT-xxx, BACK-xxx, SLOP-xxx
- Supplements with LLM review of conventions (naming, patterns, architecture decisions)
- Checks for hardcoded values, magic numbers, dead code
**Output**: Violations list in the same structured finding format
**Token budget**: Low-medium -- primarily validates pre-computed scan results, LLM review only for convention checks
**Tools**: Read, Glob, Grep

#### Auditor 3: Interface Auditor
**Checks**: WIRE-xxx, SVC-xxx, INT-xxx, API-001..003, XREF-001..002, SDL-001..003, ENUM-001..004
**Input**: Reads REQUIREMENTS.md wiring section, backend routes, frontend services
**Method**:
- Receives PRE-COMPUTED results from existing Python scan functions:
  - `run_api_contract_scan()` -- API-001..003
  - `run_endpoint_xref_scan()` -- XREF-001..002
  - `run_silent_data_loss_scan()` -- SDL-001..003
- LLM traces wiring paths: entry point -> router -> controller -> service -> data layer
- Verifies each SVC-xxx row: frontend service method -> HTTP call -> backend endpoint -> DTO match
- Verifies enum serialization (ENUM-004)
**Output**: Structured findings with wiring evidence chains
**Token budget**: Medium-high -- requires tracing through multiple files
**Tools**: Read, Glob, Grep

#### Auditor 4: Test Auditor
**Checks**: TEST-xxx, test coverage, test correctness, seed data (SEED-001..003)
**Input**: Reads REQUIREMENTS.md test section, test files, test results
**Method**:
- Locate all test files using Glob patterns
- Verify each TEST-xxx requirement has corresponding test(s)
- Run test suites via Bash and parse results
- Check for flaky patterns (hardcoded timeouts, non-deterministic assertions)
- Verify seed data completeness (SEED-001..003)
- Check minimum test counts against project requirements
**Output**: Test results + coverage report
**Token budget**: Medium -- file reads + test execution
**Tools**: Read, Glob, Grep, Bash, Write

#### Auditor 5: MCP/Library Auditor
**Checks**: Correct library API usage, deprecated methods, configuration patterns
**Input**: Reads package.json/requirements.txt for dependency list, scans for library usage
**Method**:
- Uses Context7 MCP to fetch current documentation for key libraries
- Verifies method signatures match documentation
- Flags deprecated API usage
- Checks configuration patterns (e.g., Angular module imports, Express middleware order)
- Limited to top 5-8 most-used libraries (budget control)
**Output**: Library-specific findings with documentation references
**Token budget**: HIGH -- MCP calls are expensive. Must be budget-controlled via `max_library_checks`.
**Tools**: Read, Glob, Grep (+ Context7 MCP server)

### 2.3 Scorer (Pure Python -- No LLM)

A lightweight aggregation step that runs AFTER all 5 auditors complete. This is NOT an LLM call -- it is pure Python parsing and arithmetic.

**Input**: All 5 auditor report files from `.agent-team/audit/`
**Method**:
1. Parse each auditor's markdown report into `list[AuditFinding]`
2. Deduplicate findings (same file:line referenced by multiple auditors)
3. Assign final severity: CRITICAL > HIGH > MEDIUM > LOW > INFO
4. Compute per-auditor scores: `pass_count / total_checked`
5. Compute overall score: weighted average (requirements 30%, interface 25%, technical 20%, test 15%, library 10%)
6. Determine health: "passed" (>= pass_threshold), "needs-fixes" (>= 0.5), "critical" (< 0.5)
7. Group issues by file scope for fix dispatch
**Output**: `AuditTeamReport` dataclass + `AUDIT_REPORT.md` file
**Token budget**: ZERO -- pure Python code

### 2.4 Fix Dispatch System

After scoring, if health is "needs-fixes" or "critical":

1. **Group by file scope**: Group all findings that affect the same file(s) together
2. **Priority order**: Fix CRITICAL first, then HIGH, then MEDIUM. Skip LOW and INFO.
3. **Severity gate**: Only fix findings with severity >= `config.audit_team.severity_gate` (default "MEDIUM")
4. **Deploy fix agents**: Each fix agent gets a focused prompt with:
   - The specific findings for their file scope
   - The original requirement text
   - The file:line evidence
   - Instructions specific to the finding type
5. **After fixes**: Re-run ONLY the relevant auditors on the changed files (scope-limited re-audit using `ScanScope`)
6. **Max rounds**: `config.audit_team.max_fix_rounds` (default 3)

### 2.5 Integration Points

#### Per-Milestone Integration
**Where**: After milestone execution completes, REPLACES the current review recovery loop (cli.py lines 1374-1435)
**Flow**:
1. Milestone completes
2. Run health check first (lightweight, existing code)
3. If audit_team.enabled and audit_team.per_milestone: run audit team
4. Run all active auditors in parallel (scoped to milestone's REQUIREMENTS.md and files)
5. Score findings (Python -- no LLM)
6. If health < pass_threshold: dispatch fix agents, re-audit (up to max_fix_rounds)
7. Record audit report on RunState
8. Continue to next milestone (handoff, wiring check, etc.)

Note: The EXISTING convergence loop review inside the orchestrator still runs. The audit team is an ADDITIONAL quality gate after milestone completion.

#### End-of-Run Integration
**Where**: After all orchestration completes, REPLACES the current post-orchestration review check AND post-orchestration scan pipeline (cli.py lines 4854-5560)
**Flow**:
1. All orchestration done
2. Run convergence health check (existing code -- still needed for ConvergenceReport)
3. If audit_team.enabled and audit_team.end_of_run: run audit team
4. The technical auditor internally runs: mock data scan, UI compliance scan, spot checks
5. The interface auditor internally runs: API contract scan, XREF scan, SDL scan
6. The scorer aggregates all findings including the pre-computed scan results
7. If health < pass_threshold: dispatch fix agents, re-audit
8. EXISTING post-orchestration scans are SKIPPED when audit team runs (they are subsumed)
9. E2E testing and browser testing phases remain SEPARATE (they require running servers)

### 2.6 Parallel Execution Model

```
                    +--> Requirements Auditor --+
                    |                           |
                    +--> Technical Auditor -----+
  Milestone/Run --> +--> Interface Auditor -----+--> Scorer --> Fix Dispatch --> Re-Audit
  Completes         |                           |       (Python)
                    +--> Test Auditor ----------+
                    |                           |
                    +--> Library Auditor -------+
```

All active auditors run as **separate sub-orchestrator sessions** in parallel via `asyncio.gather()`. Each auditor is independent and reads from the codebase/requirements concurrently. The scorer waits for all to complete before aggregating.

### 2.7 Backward Compatibility

When `config.audit_team.enabled == False`:
- Per-milestone: Falls back to existing review recovery loop (`_run_review_only()`)
- Post-orchestration: Falls back to existing review recovery + individual scan pipeline
- Zero behavioral change from current system

This allows:
- Gradual rollout (enable per-project via YAML)
- Quick rollback if issues found
- `quick` depth always disables audit team (too expensive)

---

## Part 3: Configuration Design

```python
@dataclass
class AuditTeamConfig:
    """Configuration for the parallel audit-team review system.

    Replaces the monolithic code-reviewer convergence check with
    5 specialized auditors running in parallel.
    """

    enabled: bool = True

    # Which auditors to deploy
    requirements_auditor: bool = True
    technical_auditor: bool = True
    interface_auditor: bool = True
    test_auditor: bool = True
    library_auditor: bool = True

    # Scoring thresholds
    pass_threshold: float = 0.9       # 90% pass rate to skip fixes
    severity_gate: str = "MEDIUM"     # Fix everything >= this severity

    # Fix cycle limits
    max_fix_rounds: int = 3           # Max audit->fix->re-audit cycles

    # Library auditor budget control
    max_library_checks: int = 8       # Limit Context7 queries

    # Integration points
    per_milestone: bool = True        # Run after each milestone (PRD+ mode)
    end_of_run: bool = True           # Run after orchestration completes

    # Depth gating (applied automatically):
    # quick: disabled entirely (enabled=False)
    # standard: requirements + technical only, max_fix_rounds=1
    # thorough: all 5 auditors, max_fix_rounds=2, max_library_checks=5
    # exhaustive: all 5 auditors, max_fix_rounds=3, max_library_checks=8
```

### Depth Gating Table

| Depth | enabled | Active Auditors | max_fix_rounds | library_auditor | max_library_checks |
|-------|---------|----------------|----------------|-----------------|-------------------|
| quick | False | NONE | 0 | False | 0 |
| standard | True | requirements, technical | 1 | False | 0 |
| thorough | True | ALL 5 | 2 | True | 5 |
| exhaustive | True | ALL 5 | 3 | True | 8 |

### Severity Gate Levels

| Severity | Fix at "MEDIUM" gate | Fix at "HIGH" gate | Fix at "CRITICAL" gate |
|----------|---------------------|-------------------|----------------------|
| CRITICAL | Yes | Yes | Yes |
| HIGH | Yes | Yes | No |
| MEDIUM | Yes | No | No |
| LOW | No | No | No |
| INFO | No | No | No |

### YAML Example

```yaml
audit_team:
  enabled: true
  requirements_auditor: true
  technical_auditor: true
  interface_auditor: true
  test_auditor: true
  library_auditor: true
  pass_threshold: 0.9
  severity_gate: "MEDIUM"
  max_fix_rounds: 3
  max_library_checks: 8
  per_milestone: true
  end_of_run: true
```

### Validation Rules

- `pass_threshold` must be between 0.0 and 1.0
- `severity_gate` must be one of: "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
- `max_fix_rounds` must be >= 0 (0 = audit-only, no fixes)
- `max_library_checks` must be >= 0 (0 = library auditor disabled)
- If `enabled` is False, all other fields are ignored

---

## Part 4: State Design

```python
@dataclass
class AuditFinding:
    """A single finding from one of the 5 specialized auditors."""

    auditor: str          # "requirements" | "technical" | "interface" | "test" | "library"
    severity: str         # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
    requirement_id: str   # REQ-001, TECH-002, WIRE-003, SVC-004, TEST-005, LIB-006, etc.
    verdict: str          # "PASS" | "FAIL" | "PARTIAL"
    description: str      # Detailed description of the finding
    file_path: str        # Relative path to the file (POSIX-normalized)
    line_number: int      # Line number where the issue was found (0 if N/A)
    evidence: str         # Code snippet or trace evidence
    fix_hint: str = ""    # Optional: suggested fix approach


@dataclass
class AuditTeamReport:
    """Aggregate report from the audit-team review system."""

    findings: list[AuditFinding] = field(default_factory=list)

    # Per-auditor scores (0.0-1.0)
    requirements_score: float = 0.0
    technical_score: float = 0.0
    interface_score: float = 0.0
    test_score: float = 0.0
    library_score: float = 0.0

    # Totals
    total_checked: int = 0
    total_pass: int = 0
    total_fail: int = 0
    total_partial: int = 0

    # Aggregates
    overall_score: float = 0.0     # Weighted average
    health: str = "unknown"        # "passed" | "needs-fixes" | "critical"

    # Fix tracking
    fix_rounds_used: int = 0
    fix_groups: list[dict] = field(default_factory=list)

    # Metadata
    auditors_deployed: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
```

### RunState Extensions

Add these fields to the existing `RunState` dataclass in `state.py`:

```python
# Audit team tracking (v16.0)
audit_team_score: float = 0.0       # Overall audit score from last run
audit_team_health: str = "unknown"  # Last audit health
audit_fix_rounds: int = 0           # Fix rounds used
```

### Structured Output Contract

Each auditor writes its findings to a structured markdown file in `.agent-team/audit/`:

```
.agent-team/audit/
    requirements_audit.md      # Auditor 1 findings
    technical_audit.md         # Auditor 2 findings
    interface_audit.md         # Auditor 3 findings
    test_audit.md              # Auditor 4 findings
    library_audit.md           # Auditor 5 findings
    AUDIT_REPORT.md            # Scorer output (aggregated)
```

### Finding Format (Machine-Parseable Markdown)

Each auditor file uses this exact format to enable Python parsing:

```markdown
# [Auditor Name] Audit Report

## FINDINGS

### FAIL | CRITICAL | REQ-001 | User login endpoint
- **File**: src/auth/login.controller.ts:45
- **Evidence**: Missing password validation -- accepts empty strings
- **Fix Hint**: Add `if (!password || password.length < 8)` guard

### PASS | - | REQ-002 | User registration endpoint
- **File**: src/auth/register.controller.ts:12
- **Evidence**: Full validation, hashing, duplicate check verified

### PARTIAL | HIGH | REQ-003 | Password reset flow
- **File**: src/auth/reset.service.ts:78
- **Evidence**: Reset email sent but no expiration on token
- **Fix Hint**: Add `expiresAt: Date.now() + 3600000` to reset token

## SUMMARY
- Checked: 15
- Pass: 12
- Fail: 2
- Partial: 1
- Score: 0.80
```

The parser extracts findings from `### VERDICT | SEVERITY | ID | TITLE` headers and the `- **File**:`, `- **Evidence**:`, `- **Fix Hint**:` bullet points below each header.

---

## Part 5: Token Budget Management

### Cost Model

| Component | Estimated Tokens | Cost (Opus ~$15/MTok in + $75/MTok out) | Parallelizable |
|-----------|-----------------|----------------------------------------|----------------|
| Requirements Auditor | 50-80K | ~$1.50-2.50 | Yes |
| Technical Auditor | 30-50K | ~$1.00-1.50 | Yes |
| Interface Auditor | 60-100K | ~$2.00-3.00 | Yes |
| Test Auditor | 40-70K | ~$1.50-2.00 | Yes |
| Library Auditor | 40-80K | ~$1.50-2.50 | Yes |
| Scorer | 0 (Python) | $0.00 | No (waits for all) |
| Fix Round (per) | 30-60K | ~$1.00-2.00 | Partially |
| **Total (thorough, 2 fix rounds)** | **310-520K** | **~$9.50-15.50** | - |

### Budget Control Strategies

1. **Technical Auditor reuses static scans**: The `run_mock_data_scan()`, `run_ui_compliance_scan()`, `run_spot_checks()` functions are Python-native -- they execute in milliseconds with zero token cost. Pre-computed results are injected into the auditor prompt as text. The LLM auditor only activates for convention checks that can't be statically scanned.

2. **Interface Auditor reuses static scans**: `run_api_contract_scan()`, `run_endpoint_xref_scan()`, `run_silent_data_loss_scan()` are all Python-native. The LLM only traces wiring paths that require semantic understanding.

3. **Library Auditor is budget-capped**: `max_library_checks` (default 8) limits Context7 MCP queries. The auditor prioritizes: (a) libraries with known breaking changes, (b) most-used libraries, (c) libraries with complex configuration.

4. **Auditor prompts are focused**: Each auditor gets only its category of checks, not the full 200-line reviewer prompt. This reduces prompt tokens from ~15K to ~3-5K per auditor.

5. **Re-audit is scope-limited**: After fix rounds, only the relevant auditors re-run, and only on changed files (using `ScanScope` from quality_checks.py).

6. **Scorer is pure Python**: No LLM cost -- just parses the 5 audit report files and computes scores.

7. **Depth gating eliminates unnecessary work**:
   - `quick` depth: audit team disabled entirely (zero cost)
   - `standard` depth: only 2 auditors (requirements + technical), single fix round
   - `thorough` depth: all 5 auditors, 2 fix rounds
   - `exhaustive` depth: all 5 auditors, 3 fix rounds

### Comparison to Current System

| Metric | Current (monolithic reviewer) | Audit Team (5 auditors) |
|--------|------------------------------|------------------------|
| Coverage | Inconsistent (skips checks) | Guaranteed (focused scope) |
| Parallelism | None | 5-way parallel |
| Wall-clock time | Sequential | Faster (parallel execution) |
| Token cost | ~50-100K per review cycle | ~260-460K total (but more thorough) |
| Fix targeting | Imprecise (orchestrator decides) | Precise (file-scoped fix groups) |
| Re-review scope | Full re-review | Scoped to changed files only |
| Static scan integration | Separate pipeline | Embedded in auditors (zero extra cost) |

The audit team costs more per run but is significantly more thorough, and the fix dispatch is more targeted (reducing wasted fix round costs).

---

## Part 6: File/Module Plan

### New Files to Create

#### 1. `src/agent_team/audit_team.py` (~900-1100 lines)

The main audit team module. Contains:

```python
# --- Dataclasses ---
class AuditFinding: ...        # Single finding
class AuditTeamReport: ...     # Aggregate report
class AuditorResult: ...       # Per-auditor result (findings + metadata)

# --- Constants ---
SEVERITY_ORDER: dict[str, int]  # CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1, INFO=0
AUDITOR_WEIGHTS: dict[str, float]  # requirements=0.30, interface=0.25, etc.

# --- 5 Auditor Prompt Constants (~100 lines each) ---
REQUIREMENTS_AUDITOR_PROMPT: str
TECHNICAL_AUDITOR_PROMPT: str
INTERFACE_AUDITOR_PROMPT: str
TEST_AUDITOR_PROMPT: str
LIBRARY_AUDITOR_PROMPT: str

# --- Report Parsing (parse structured markdown from auditor files) ---
def parse_auditor_report(content: str, auditor_name: str) -> list[AuditFinding]
def _parse_finding_header(line: str) -> tuple[str, str, str, str] | None
def _parse_finding_body(lines: list[str]) -> tuple[str, int, str, str]
def _parse_summary(content: str) -> tuple[int, int, int, float]

# --- Scoring (pure Python, no LLM) ---
def score_audit_findings(
    findings: list[AuditFinding],
    auditors_deployed: list[str],
    pass_threshold: float = 0.9,
) -> AuditTeamReport

def _compute_per_auditor_score(
    findings: list[AuditFinding],
    auditor: str,
) -> float

def _compute_overall_score(
    per_auditor_scores: dict[str, float],
    deployed: list[str],
) -> float

def _determine_health(
    overall_score: float,
    findings: list[AuditFinding],
    pass_threshold: float,
) -> str

# --- Fix Grouping ---
def group_findings_for_fix(
    findings: list[AuditFinding],
    severity_gate: str = "MEDIUM",
) -> list[dict]
    """Group FAIL/PARTIAL findings by file scope, filtered by severity gate.
    Returns list of {files: [str], findings: [AuditFinding]} dicts."""

# --- Fix Prompt Builder ---
def build_audit_fix_prompt(
    fix_group: dict,
    task_text: str | None = None,
) -> str

# --- Pre-computed Scan Injection ---
def format_scan_results_for_technical(violations: list) -> str
def format_scan_results_for_interface(violations: list) -> str

# --- Depth Gating ---
def get_active_auditors(depth: str, config: "AuditTeamConfig") -> list[str]
    """Return list of auditor names active for the given depth."""

# --- Report Writing ---
def write_audit_report(
    report: AuditTeamReport,
    output_dir: Path,
) -> None
    """Write AUDIT_REPORT.md to the output directory."""
```

#### 2. `tests/test_audit_team.py` (~600-800 lines)

Comprehensive tests covering:
- `AuditFinding` / `AuditTeamReport` dataclass creation and defaults
- `parse_auditor_report()` with various finding formats (PASS, FAIL, PARTIAL, edge cases)
- `parse_auditor_report()` with malformed input (graceful degradation)
- `score_audit_findings()` scoring math and weighting
- `_compute_per_auditor_score()` edge cases (zero findings, all pass, all fail)
- `_compute_overall_score()` with subset of deployed auditors
- `_determine_health()` threshold logic
- `group_findings_for_fix()` grouping by file scope
- `group_findings_for_fix()` severity filtering
- `build_audit_fix_prompt()` prompt formatting
- `format_scan_results_for_technical()` / `format_scan_results_for_interface()` formatting
- `get_active_auditors()` depth gating logic for all 4 depths
- `write_audit_report()` file writing
- Integration: end-to-end parse -> score -> group -> prompt pipeline

### Files to Modify

#### 3. `src/agent_team/config.py` (~40 lines added)

**Changes**:
- Add `AuditTeamConfig` dataclass (after `PostOrchestrationScanConfig`, line ~307)
- Add `audit_team: AuditTeamConfig = field(default_factory=AuditTeamConfig)` to `AgentTeamConfig` (line ~445)
- Add `_validate_audit_team_config()` function
- Add `audit_team` section parsing in `_dict_to_config()` (with user-overrides tracking)
- Add depth gating in the existing depth-default application logic

#### 4. `src/agent_team/state.py` (~5 lines added)

**Changes**:
- Add `audit_team_score: float = 0.0` to `RunState`
- Add `audit_team_health: str = "unknown"` to `RunState`
- Add `audit_fix_rounds: int = 0` to `RunState`

#### 5. `src/agent_team/cli.py` (~350 lines added, ~200 lines gated)

**New async functions**:

```python
async def _run_audit_team(
    cwd: str,
    config: AgentTeamConfig,
    requirements_path: str | None = None,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
    scan_scope: "ScanScope | None" = None,
) -> tuple[float, AuditTeamReport]:
    """Run the parallel audit team and return (cost, report).

    1. Determine active auditors based on depth
    2. Run pre-computed Python scans (zero-cost)
    3. Launch all active auditors in parallel via asyncio.gather
    4. Parse auditor reports
    5. Score findings (Python -- no LLM)
    6. If needs fixes: dispatch fix agents, re-audit
    7. Return total cost and final report
    """

async def _run_single_auditor(
    cwd: str,
    config: AgentTeamConfig,
    auditor_name: str,
    auditor_prompt: str,
    requirements_path: str,
    task_text: str | None = None,
    constraints: list | None = None,
    depth: str = "standard",
) -> tuple[float, str]:
    """Run a single auditor sub-orchestrator session.
    Returns (cost, audit_report_file_content).
    """

async def _run_audit_fix_round(
    cwd: str,
    config: AgentTeamConfig,
    fix_groups: list[dict],
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run fix agents for grouped findings. Returns total cost."""
```

**Wiring changes**:

A. **Per-milestone integration** (around line 1374):
```python
# BEFORE: Direct review recovery loop
# AFTER: Gated on audit_team.enabled
if config.audit_team.enabled and config.audit_team.per_milestone:
    audit_cost, audit_report = await _run_audit_team(
        cwd=cwd, config=config,
        requirements_path=ms_req_path,
        task_text=task, depth=depth, ...
    )
    total_cost += audit_cost
    # Update RunState with audit results
else:
    # EXISTING review recovery loop (backward compat)
    if needs_recovery:
        for recovery_attempt in range(max_recovery):
            recovery_cost = await _run_review_only(...)
            ...
```

B. **Post-orchestration integration** (around line 4930):
```python
# BEFORE: review_only + individual scans
# AFTER: Gated on audit_team.enabled
if config.audit_team.enabled and config.audit_team.end_of_run:
    audit_cost, audit_report = asyncio.run(_run_audit_team(
        cwd=cwd, config=config,
        task_text=effective_task, depth=depth, ...
    ))
    if _current_state:
        _current_state.total_cost += audit_cost
        _current_state.audit_team_score = audit_report.overall_score
        _current_state.audit_team_health = audit_report.health
        _current_state.audit_fix_rounds = audit_report.fix_rounds_used
    # SKIP individual post-orchestration scans (subsumed by audit team)
else:
    # EXISTING review recovery + individual scan pipeline (backward compat)
    if needs_recovery:
        recovery_cost = asyncio.run(_run_review_only(...))
    # Mock data scan, UI compliance scan, integrity scans, etc.
    ...
```

#### 6. `src/agent_team/mcp_servers.py` (~10 lines added)

**Changes**:
- Add `get_audit_library_servers()` function that returns Context7-only MCP servers for the library auditor
- Implementation: reuses existing `get_context7_only_servers()` or delegates to it

### Files NOT Changed

- **agents.py**: No changes -- auditor prompts live in `audit_team.py`, existing agent definitions remain for backward compat
- **milestone_manager.py**: No changes -- audit team reads the same REQUIREMENTS.md files
- **quality_checks.py**: No changes -- audit team calls existing scan functions as-is
- **tracking_documents.py**: No changes -- fix cycle log still works the same way
- **e2e_testing.py**: No changes -- E2E phase remains separate
- **browser_testing.py**: No changes -- browser testing remains separate
- **tech_research.py**: No changes
- **prd_chunking.py**: No changes

### Implementation Order

1. **Phase 1**: Create `audit_team.py` with dataclasses, parsing, scoring, grouping (all pure Python -- testable immediately)
2. **Phase 2**: Create `tests/test_audit_team.py` with comprehensive unit tests
3. **Phase 3**: Add `AuditTeamConfig` to `config.py` and RunState fields to `state.py`
4. **Phase 4**: Add `_run_audit_team()`, `_run_single_auditor()`, `_run_audit_fix_round()` to `cli.py`
5. **Phase 5**: Wire per-milestone integration (behind `config.audit_team.enabled` gate)
6. **Phase 6**: Wire post-orchestration integration (behind gate, skips existing scans when active)

### Summary Table

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `src/agent_team/audit_team.py` | CREATE | ~1000 |
| `src/agent_team/config.py` | MODIFY | ~45 |
| `src/agent_team/state.py` | MODIFY | ~5 |
| `src/agent_team/cli.py` | MODIFY | ~350 (add) + ~200 (gated replace) |
| `src/agent_team/mcp_servers.py` | MODIFY | ~10 |
| `tests/test_audit_team.py` | CREATE | ~700 |
| **Total** | | **~2310** |

---

## Appendix A: Scoring Formula

```python
AUDITOR_WEIGHTS = {
    "requirements": 0.30,
    "interface": 0.25,
    "technical": 0.20,
    "test": 0.15,
    "library": 0.10,
}

def _compute_overall_score(
    per_auditor_scores: dict[str, float],
    deployed: list[str],
) -> float:
    """Weighted average, normalized to deployed auditors only."""
    total_weight = sum(AUDITOR_WEIGHTS[a] for a in deployed if a in AUDITOR_WEIGHTS)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(
        per_auditor_scores.get(a, 0.0) * AUDITOR_WEIGHTS[a]
        for a in deployed
        if a in AUDITOR_WEIGHTS
    )
    return weighted_sum / total_weight
```

---

## Appendix B: Key Design Decisions

1. **Sub-orchestrator sessions, not sub-agents**: Each auditor runs as a separate `ClaudeSDKClient` session (like `_run_review_only()` today), not as a sub-agent within the main orchestrator. This gives each auditor its own context window and prevents interference.

2. **Pre-computed scan results**: The technical and interface auditors receive the OUTPUT of existing Python scan functions as pre-computed text in their prompt. This eliminates redundant scanning and saves tokens -- the Python scans execute in milliseconds before the LLM sessions start.

3. **Structured output files**: Auditors write to `.agent-team/audit/` directory. The scorer parses these files using regex. This is more reliable than extracting findings from LLM conversation output, and enables re-runs without re-executing auditors.

4. **Fix-by-file-scope**: Fix agents receive all findings for a file group, not individual findings. This prevents conflicting edits and reduces the number of fix sessions needed.

5. **Scorer is pure Python**: The scorer does NOT use an LLM. It parses markdown files and computes weighted averages. This makes it deterministic, fast, and free.

6. **Backward compatible**: `config.audit_team.enabled` (default True) gates the new system. Setting it to False reverts to the existing monolithic review + post-orchestration scan path. The `quick` depth always disables the audit team. This allows safe rollout.

7. **Absorbs post-orchestration scans**: When the audit team is enabled, it subsumes: mock data scan, UI compliance scan, spot checks, deployment scan, asset scan, database scans, API contract scan, SDL scan, and XREF scan. These become internal to the technical and interface auditors (pre-computed results injected into prompts). E2E testing and browser testing remain separate because they require running application servers.

8. **No changes to convergence loop**: The audit team does NOT replace the orchestrator's internal convergence loop. The existing code-reviewer agents still run inside the convergence loop as before. The audit team is a SECOND quality gate that catches what the in-loop review missed, and provides structured, traceable evidence.

---

## Appendix C: Risk Analysis

| Risk | Mitigation |
|------|-----------|
| Higher token cost | Depth gating: quick=off, standard=2 auditors, library_auditor capped |
| Auditor output format inconsistent | Strict prompt templates + fallback parser + SUMMARY section as backup |
| Fix round doesn't fix the issue | max_fix_rounds cap + severity_gate to avoid over-fixing |
| Parallel auditors conflict on file reads | Read-only access during audit -- no writes until fix phase |
| Breaking existing review | Backward compat gate: `enabled: false` restores old behavior |
| PRD reconciliation scan (LLM-based) | Remains separate -- not absorbed by audit team (requires full PRD context) |
