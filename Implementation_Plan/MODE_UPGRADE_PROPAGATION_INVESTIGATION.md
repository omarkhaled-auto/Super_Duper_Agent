# Agent-Team Exhaustive Investigation — Mode Upgrade Propagation

## Agent Team Structure — Parallel Research Execution

You MUST execute this investigation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

**CRITICAL: This is a RESEARCH-ONLY task. NO code changes. Every finding must cite `file:line_number`.**

### Team Composition (3 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `mode-analyst` | `feature-dev:code-explorer` | Phase 1A — Deep-read cli.py, config.py, agents.py to map what each non-PRD mode actually runs (pipeline, prompts, post-orchestration gates, recovery passes). Produce MODE_ARCHITECTURE_ANALYSIS.md |
| `upgrade-tracer` | `feature-dev:code-explorer` | Phase 1B — Trace every v2.0–v5.0 upgrade through the codebase to determine exactly WHERE each is gated, WHAT is universal vs PRD-specific, and HOW it could be adapted for other modes. Produce UPGRADE_TRACE_REPORT.md |
| `plan-synthesizer` | `general-purpose` | Phase 2 — Read both Phase 1 reports, cross-reference to build the final Mode×Upgrade propagation matrix, scoped-scanning design, config schema, and implementation roadmap. Produce MODE_UPGRADE_PROPAGATION_PLAN.md |

### Coordination Flow

```
Wave 1 (parallel):  mode-analyst (reads cli.py, config.py, agents.py)
                  + upgrade-tracer (reads quality_checks.py, e2e_testing.py, tracking_documents.py,
                                          design_reference.py, agents.py, cli.py)
    |                               |
    Produces:                       Produces:
    MODE_ARCHITECTURE_ANALYSIS.md   UPGRADE_TRACE_REPORT.md
    |                               |
    +---------------+---------------+
                    |
Wave 2 (solo):  plan-synthesizer reads BOTH reports
                    |
                Produces: MODE_UPGRADE_PROPAGATION_PLAN.md
```

---

## Background — Why This Investigation Exists

### The Two-Tier Quality Problem

The agent-team accumulated 5 major upgrade cycles (v1.0 through v5.0) that dramatically improved
PRD and PRD+ mode quality. These upgrades include mock data scanning, UI compliance enforcement,
E2E testing, post-build integrity scans, tracking documents, and database integrity checks.

However, these upgrades interact with non-PRD modes in three different ways:

1. **Already universal (Bucket A):** Some upgrades live in prompts (CODE_WRITER_PROMPT,
   CODE_REVIEWER_PROMPT) that ALL modes receive. These need no propagation — they already work.

2. **Structurally PRD-exclusive (Bucket B):** Some upgrades are fundamentally tied to PRD structure
   (MASTER_PLAN.md, milestone decomposition, milestone handoff). These CANNOT be propagated.

3. **Potentially adaptable (Bucket C):** Some upgrades exist in post-orchestration pipelines
   that COULD run in other modes but may need adaptation (scoped scanning, conditional enabling,
   depth gating). **THIS is the investigation target.**

### What Goes Wrong Without Propagation

| Failure | Mode | Root Cause |
|---------|------|------------|
| Mock data ships to production | Standard mode builds a feature, generates placeholder data, no post-orchestration mock scan runs | Mock scan only runs when `config.milestone.mock_data_scan` is True, which defaults True — BUT the `not _use_milestones` gate at cli.py:3791 means it DOES run in standard mode. **Is it actually reaching non-PRD tasks? Does the depth affect it?** |
| Broken Docker deployment | Thorough mode builds a complex feature, ports mismatch docker-compose | Deployment scan at cli.py:3854 has NO milestone gate — it runs in all modes. **But is `config.integrity_scans.deployment_scan` defaulting True for all depths? Is it depth-gated anywhere?** |
| Dual ORM type mismatch | Exhaustive non-PRD builds full app, EF Core + Dapper types diverge | Database scan at cli.py:3943 has NO milestone gate. **Same question: is it config-gated differently per depth?** |
| UI design violations pile up | Quick mode patches a component, no UI compliance check | UI scan at cli.py:3823 is gated by `not _use_milestones`. **Does it run for quick depth? Should it?** |
| E2E tests never run on standard features | Standard mode adds a feature, no E2E phase | E2E at cli.py:4050 is gated by `config.e2e_testing.enabled`. **Is it appropriate for standard? What about scoped E2E for just the new feature?** |
| Fix cycles repeat the same failure | All modes have recovery passes but no Fix Cycle Log | Tracking documents are only wired in specific functions. **Which fix functions log cycles? Which don't?** |

### What Goes Wrong With Bad Propagation (Anti-Patterns)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Adding full E2E testing to quick mode | A 1-file bugfix spawns Playwright tests — absurd, wastes $5+ |
| Running all integrity scans on existing codebases after a 3-line patch | Scans the entire project, finds 50 pre-existing issues unrelated to the patch |
| Copying PRD reconciliation to non-PRD modes | There's no PRD to reconcile against — the scan is meaningless |
| Adding 20 new config fields | Config explosion — users can't understand what to set |
| Making quick mode as slow as thorough | The whole point of quick is SPEED — defeats the purpose |
| Breaking backward compatibility | Existing configs suddenly trigger new scans they didn't expect |

### The Core Insight: Depth vs Scope Are Independent Dimensions

```
              DEPTH (how thorough)
              quick ←──────────→ exhaustive

    SCOPE     full project   ■ E2E, full scans, PRD reconciliation
    (what      ↑              ■ All integrity scans, all tracking
    is         |              ■ Scoped scans, essential tracking
    checked)   ↓              ■ Changed-files-only scans
              changed files   ■ No scanning (just the fix)
```

The investigation must determine: for each (mode × upgrade), what is the RIGHT scope?

---

## PHASE 1A: Mode Architecture Analysis

**Agent: `mode-analyst`**
**Type: `feature-dev:code-explorer`**
**Constraint: READ-ONLY — produce analysis, no code changes**

### Instructions

You must produce a comprehensive map of how each non-PRD depth mode works — what runs, what doesn't,
and where the gates are. The user needs to understand the COMPLETE execution pipeline for each mode.

### Files to Read (in order)

1. **`src/agent_team/config.py`** — Read the entire file. Focus on:
   - `DepthConfig` (line ~25): keyword_map for quick/standard/thorough/exhaustive
   - `DEPTH_AGENT_COUNTS` (line ~413): agent scaling per depth
   - `apply_depth_quality_gating()` (line ~451): what quick depth disables
   - `MilestoneConfig` fields: `mock_data_scan`, `ui_compliance_scan`, `review_recovery_retries`
   - `IntegrityScanConfig` fields: deployment_scan, asset_scan, prd_reconciliation
   - `DatabaseScanConfig` fields: dual_orm_scan, default_value_scan, relationship_scan
   - `E2ETestingConfig` fields: enabled, backend_api_tests, frontend_playwright_tests, max_fix_retries
   - `TrackingDocumentsConfig` fields: all 5 fields
   - `_dict_to_config()`: how user YAML overrides interact with defaults
   - **KEY QUESTION**: Which config fields change based on depth? Are any configs depth-gated at load time?

2. **`src/agent_team/cli.py`** — Read the `main()` function (it's large, ~1000+ lines). Focus on:
   - The PRD detection logic (~line 470): `is_prd`, `_use_milestones`, `depth_override`
   - Phase pipeline order: Phase 0 → 0.25 → 0.5 → 0.6 → Orchestration → Post-orchestration
   - The post-orchestration section (~line 3786 onward): Map EVERY scan/check and its gate condition
   - Which scans are gated by `not _use_milestones` vs `config.*` vs nothing
   - The recovery pass functions: `_run_mock_data_fix()`, `_run_ui_compliance_fix()`, `_run_integrity_fix()`, `_run_e2e_fix()`
   - The E2E testing section (~line 4050): what conditions control it
   - **KEY QUESTION**: For a quick-depth, non-PRD task — what EXACTLY runs in post-orchestration?

3. **`src/agent_team/agents.py`** — Focus on:
   - `build_orchestrator_prompt()`: what parts are mode-specific vs universal
   - `CODE_WRITER_PROMPT`: which quality policies are embedded (they apply to ALL modes)
   - `CODE_REVIEWER_PROMPT`: which review duties are embedded
   - `build_milestone_execution_prompt()`: this is PRD-only, but check if any of its patterns are reusable
   - **KEY QUESTION**: Which prompt-injected standards automatically propagate to all modes?

### Deliverable: MODE_ARCHITECTURE_ANALYSIS.md

Write this file to the `.agent-team/` directory. It MUST contain:

```markdown
# Mode Architecture Analysis

## 1. Depth Mode Inventory

### Quick Mode
- **Agent counts**: {from DEPTH_AGENT_COUNTS}
- **Quality gating**: {what apply_depth_quality_gating disables}
- **Phases that run**: {list every phase}
- **Post-orchestration checks**: {list every scan/check with its gate condition and line number}
- **Recovery passes available**: {list}
- **What it DOESN'T get**: {list features/scans that don't run}

### Standard Mode
{same structure}

### Thorough Mode
{same structure}

### Exhaustive Non-PRD Mode
{same structure}

## 2. Post-Orchestration Pipeline Map

For each post-orchestration step, document:
| Step | Gate Condition | Runs in Quick? | Standard? | Thorough? | Exhaustive? | PRD? | PRD+? |
|------|---------------|----------------|-----------|-----------|-------------|------|-------|
{complete table}

## 3. Universal vs Mode-Gated Components

### Already Universal (via prompts)
- {list every prompt-injected standard that ALL modes receive, with file:line}

### Currently Gated by _use_milestones
- {list, with file:line — these run in ALL non-PRD modes but NOT in milestone mode}

### Currently Gated by config.*
- {list, with file:line — these depend on config defaults, not mode}

### Currently Gated by depth
- {list, with file:line — these change behavior based on quick/standard/thorough/exhaustive}

## 4. Config Defaults vs Depth Interaction

Document exactly what happens when a user runs:
- `agent-team "Fix login bug"` (quick depth, no config overrides)
- `agent-team "Build user auth"` (standard depth, no config overrides)
- `agent-team "Thoroughly refactor the API layer"` (thorough depth)
- `agent-team --exhaustive "Build complete payment system"` (exhaustive non-PRD)

For each: what scans run? What tracking documents are generated? What recovery passes fire?

## 5. Gap Analysis

For each mode, identify:
- Features that SHOULD run but DON'T (with justification)
- Features that DO run but SHOULDN'T for that depth (over-engineering)
- Features that need ADAPTATION (e.g., scoped scanning) to be appropriate
```

---

## PHASE 1B: Upgrade Propagation Tracing

**Agent: `upgrade-tracer`**
**Type: `feature-dev:code-explorer`**
**Constraint: READ-ONLY — produce analysis, no code changes**

### Instructions

You must trace every v2.0–v5.0 upgrade through the codebase to determine exactly WHERE each
upgrade is activated, WHAT gate conditions control it, and HOW it could be adapted for non-PRD modes.

### Upgrade Catalog to Trace

Trace EACH of these 12 upgrade categories through the codebase:

#### v2.0 — PRD Critical Fixes
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-01 | TASKS.md Generation (milestone workflow step) | agents.py (build_milestone_execution_prompt), cli.py |
| U-02 | Review Recovery Loop (retry on review failures) | cli.py (_run_review_only, review recovery) |
| U-03 | Mock Data Scanning (MOCK-001..007) | quality_checks.py (run_mock_data_scan), cli.py |
| U-04 | Mock Data Policy (ZERO MOCK DATA in prompts) | agents.py (CODE_WRITER_PROMPT) |

#### v3.0 — UI Requirements
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-05 | UI Compliance Scanning (UI-001..004) | quality_checks.py (run_ui_compliance_scan), cli.py |
| U-06 | UI Compliance Policy (UI-FAIL-001..007 in prompts) | agents.py (CODE_WRITER_PROMPT, CODE_REVIEWER_PROMPT) |
| U-07 | Design Reference Extraction (Phase 0.6) | design_reference.py, cli.py |

#### v3.5 — E2E Testing
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-08 | E2E Testing Phase (backend + frontend) | e2e_testing.py, cli.py |
| U-09 | E2E Quality Scanning (E2E-001..007) | quality_checks.py (run_e2e_quality_scan) |

#### v4.0 — Tracking Documents
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-10 | Fix Cycle Log (FIX_CYCLE_LOG.md) | tracking_documents.py, cli.py (5 fix functions) |
| U-11 | E2E Coverage Matrix | tracking_documents.py, cli.py |
| U-12 | Milestone Handoff Documents | tracking_documents.py, cli.py |

#### v4.5 — Post-Build Integrity
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-13 | Deployment Integrity Scan (DEPLOY-001..004) | quality_checks.py (run_deployment_scan), cli.py |
| U-14 | Asset Integrity Scan (ASSET-001..003) | quality_checks.py (run_asset_scan), cli.py |
| U-15 | PRD Reconciliation Scan (PRD-001) | quality_checks.py, cli.py (_run_prd_reconciliation) |

#### v5.0 — Database Integrity
| ID | Upgrade | Key Files |
|----|---------|-----------|
| U-16 | Dual ORM Scan (DB-001..003) | quality_checks.py (run_dual_orm_scan), cli.py |
| U-17 | Default Value Scan (DB-004..005) | quality_checks.py (run_default_value_scan), cli.py |
| U-18 | Relationship Scan (DB-006..008) | quality_checks.py (run_relationship_scan), cli.py |
| U-19 | Seed Data Policy (SEED-001..003) | agents.py (CODE_WRITER_PROMPT) |
| U-20 | Enum Registry Policy (ENUM-001..003) | agents.py (CODE_WRITER_PROMPT) |

### For Each Upgrade, Document

```markdown
### U-XX: {Name}

**Activation Gate**: {exact condition at file:line — e.g., `config.integrity_scans.deployment_scan` at cli.py:3854}
**Milestone Gate**: {is it behind `_use_milestones` check? YES/NO, file:line}
**Depth Gate**: {is behavior different per depth? YES/NO, details}
**Config Default**: {what is the default value? Is it True/False/enabled?}

**Universal Component**: {what part of this upgrade works regardless of mode}
**PRD-Specific Component**: {what part only makes sense with PRD/milestones}
**Adaptable Component**: {what could be modified to work in other modes}

**Adaptation Assessment**:
- Quick mode: {SKIP / PROPAGATE_AS_IS / ADAPT — with rationale}
- Standard mode: {SKIP / PROPAGATE_AS_IS / ADAPT — with rationale}
- Thorough mode: {SKIP / PROPAGATE_AS_IS / ADAPT — with rationale}
- Exhaustive non-PRD: {SKIP / PROPAGATE_AS_IS / ADAPT — with rationale}

**Adaptation Cost**: {TRIVIAL / MODERATE / SIGNIFICANT / IMPOSSIBLE}
**Dependencies**: {other upgrades this depends on}
**Scoped Scanning Applicability**: {can this upgrade scan only changed files? How?}
```

### Existing-Codebase Consideration

For EACH upgrade, specifically analyze what happens when the mode runs on an EXISTING codebase
(not a greenfield project). Consider:

- A quick-mode bugfix on a 50,000-line project: should this upgrade run? On what scope?
- A standard-mode feature addition: does it make sense to scan the entire project or just new files?
- A thorough refactor: does the full scan make sense here?

**The key mechanism to investigate**: Can scans be limited to git-diffed files? What would that
require for each scan function's API? Currently they all take `project_root: Path` — would they
need a `changed_files: list[Path]` parameter?

### Deliverable: UPGRADE_TRACE_REPORT.md

Write this file to the `.agent-team/` directory. It MUST contain:

```markdown
# Upgrade Propagation Trace Report

## 1. Upgrade-by-Upgrade Analysis
{U-01 through U-20, each with the template above}

## 2. Gate Analysis Summary

### Upgrades Gated by _use_milestones (run in non-PRD modes already)
| Upgrade | Gate Line | Currently Works in Standard? | Notes |
{table}

### Upgrades Gated by config.* Only (run everywhere if config enables)
| Upgrade | Config Field | Default | Currently Works in All Modes? | Notes |
{table}

### Upgrades With No Gate (always run)
| Upgrade | Notes |
{table}

### Upgrades Structurally Tied to PRD (cannot propagate)
| Upgrade | Why It Can't Propagate |
{table}

## 3. Scoped Scanning Feasibility

For each scan function, assess:
| Scan Function | Current Signature | Accepts Changed Files? | Adaptation Needed |
{table}

Design a `ScanScope` mechanism:
- How would `git diff` integration work?
- What about newly created files (no previous version to diff)?
- How would depth interact with scope (quick = changed only, thorough = full project)?

## 4. Inter-Upgrade Dependencies

```
U-10 (Fix Cycle Log) ←─ depends on ─→ ANY fix function existing
U-11 (Coverage Matrix) ←─ depends on ─→ U-08 (E2E Testing)
U-12 (Milestone Handoff) ←─ tied to ─→ Milestone structure (CANNOT propagate)
U-15 (PRD Reconciliation) ←─ tied to ─→ PRD document (CANNOT propagate)
{complete dependency graph}
```

## 5. Quick Wins vs Heavy Lifts

### Quick Wins (can propagate with config change only, no code)
{list}

### Moderate Effort (need scoped scanning or conditional logic)
{list}

### Heavy Lifts (need new mechanisms, significant refactoring)
{list}

### Impossible (structurally PRD-only)
{list}
```

---

## PHASE 2: Plan Synthesis

**Agent: `plan-synthesizer`**
**Type: `general-purpose`**
**Prerequisite: Both Phase 1 reports must be complete before starting**

### Instructions

You will read both Phase 1 deliverables and synthesize them into the definitive propagation plan.
This plan must be IMPLEMENTABLE — specific enough that a single follow-up session can execute it.

### Files to Read

1. `.agent-team/MODE_ARCHITECTURE_ANALYSIS.md` (from mode-analyst)
2. `.agent-team/UPGRADE_TRACE_REPORT.md` (from upgrade-tracer)
3. `src/agent_team/config.py` (to validate config change proposals)
4. `Agent-team_New_Upgrades.md` (for upgrade history context)

### Synthesis Requirements

1. **Mode×Upgrade Matrix**: For every (mode, upgrade) pair, decide:
   - **PROPAGATE**: Already works or needs only config default change
   - **ADAPT**: Needs code changes (scoped scanning, depth gating, conditional logic)
   - **SKIP**: Doesn't make sense for this mode (with 1-sentence justification)
   - **N/A**: Structurally impossible (PRD-only)

2. **Scoped Scanning Architecture**: Design the mechanism for limiting scans to relevant files:
   - Define a `ScanScope` interface or parameter pattern
   - Specify how each existing scan function would accept scoped input
   - Define depth-to-scope mapping: quick→changed_only, standard→changed+related, thorough→full, exhaustive→full+deep
   - Handle edge cases: new projects (no git history), first run, no changes detected

3. **Depth-Gating Design**: For upgrades that should only run at certain depths:
   - Define which config fields need depth-aware defaults
   - Design the gating mechanism (config override vs code gate vs both)
   - Ensure backward compatibility (existing configs keep working)

4. **Config Schema Evolution**: Define exactly what changes:
   - New fields needed (if any)
   - Default value changes per depth
   - A `depth_overrides` mechanism for per-depth config tuning
   - Migration path from current schema

5. **Implementation Roadmap**: Order the work by impact/effort:
   - **Wave 1 (Quick Wins)**: Config defaults + depth gating — no new code
   - **Wave 2 (Scoped Scanning)**: Add `changed_files` parameter to scan functions
   - **Wave 3 (Smart Adaptation)**: E2E scoping, tracking doc adaptation
   - **Wave 4 (Polish)**: Documentation, testing, edge case handling

6. **Risk Assessment**: For each proposed change:
   - Backward compatibility risk (0-3 scale)
   - Performance impact (faster/neutral/slower)
   - User confusion risk (0-3 scale)

### Deliverable: MODE_UPGRADE_PROPAGATION_PLAN.md

Write this file to the `.agent-team/` directory. This is the FINAL deliverable — the document
that will be used to execute the actual implementation. It MUST be comprehensive and actionable.

Required structure:

```markdown
# Mode Upgrade Propagation Plan

## Executive Summary
{2-3 paragraph overview of findings and recommendations}

## 1. Current State Assessment

### What Already Works (No Changes Needed)
| Upgrade | Why It Already Works | Modes Covered |
{table — these are the Bucket A prompt-injected standards}

### What Can Never Propagate (Structurally PRD-Only)
| Upgrade | Why | Alternatives for Non-PRD |
{table}

## 2. Mode × Upgrade Propagation Matrix

|  | Quick | Standard | Thorough | Exhaustive | Notes |
|--|-------|----------|----------|------------|-------|
| U-01 TASKS.md | ? | ? | ? | ? | |
| U-02 Review Recovery | ? | ? | ? | ? | |
| ... | | | | | |
| U-20 Enum Registry | ? | ? | ? | ? | |

Legend: ✅ PROPAGATE | 🔧 ADAPT | ⏭️ SKIP | ❌ N/A

## 3. Scoped Scanning Architecture

### The Problem
Running full-project scans after a 3-line bugfix is wasteful and noisy.

### Proposed Solution
{detailed design}

### Scan Function API Changes
| Function | Current Signature | New Parameter | Behavior Change |
{table}

### Depth-to-Scope Mapping
| Depth | Default Scope | Rationale |
|-------|---------------|-----------|
| quick | changed_files_only | Speed is paramount, scan only what was touched |
| standard | changed_files + imports | Reasonable balance of speed and coverage |
| thorough | full_project | Thoroughness warrants complete scan |
| exhaustive | full_project + deep | Maximum coverage, no shortcuts |

## 4. Depth-Gating Design

### Existing Depth Gates (from config.py)
{what apply_depth_quality_gating already does}

### New Depth Gates Needed
| Feature | Quick | Standard | Thorough | Exhaustive | Gate Mechanism |
{table}

### Backward Compatibility
{how existing configs continue to work unchanged}

## 5. Config Schema Evolution

### New Fields
{list with types, defaults, descriptions}

### Changed Defaults
{list of fields whose defaults change per depth}

### depth_overrides Mechanism
{design for per-depth config tuning}

### Example Configs
```yaml
# Quick mode — minimal scanning
depth:
  default: quick
e2e_testing:
  enabled: false  # Never for quick
integrity_scans:
  deployment_scan: false  # Skip for quick bugfixes
```

```yaml
# Standard mode — balanced
depth:
  default: standard
e2e_testing:
  enabled: true
  max_fix_retries: 2  # Fewer retries than exhaustive
integrity_scans:
  deployment_scan: true
  asset_scan: true
  scoped: true  # Only scan changed files
```

## 6. Implementation Roadmap

### Wave 1: Quick Wins (config + depth gating only)
| Change | Files | Effort | Impact |
{table}

### Wave 2: Scoped Scanning (new parameter on scan functions)
| Change | Files | Effort | Impact |
{table}

### Wave 3: Smart Adaptation (E2E scoping, tracking docs)
| Change | Files | Effort | Impact |
{table}

### Wave 4: Polish (docs, tests, edge cases)
| Change | Files | Effort | Impact |
{table}

### Estimated Total Effort
{per wave and total}

## 7. Risk Assessment

| Change | Backward Compat (0-3) | Performance | User Confusion (0-3) | Mitigation |
{table}

## 8. Testing Strategy

### What Needs New Tests
{list per wave}

### Regression Risks
{what existing tests might break}

## 9. Decision Log

For each controversial decision, document:
- The options considered
- The choice made
- The rationale
- What would change the decision
```

---

## Execution Rules

### For ALL Agents
1. **READ-ONLY**: This is a research task. Do NOT modify any source files.
2. **CITE EVERYTHING**: Every claim must include `file_path:line_number`.
3. **READ ACTUAL CODE**: Do not rely on memory or assumptions. Read the files.
4. **BE SPECIFIC**: "This runs in all modes" is insufficient. Say "This runs in all modes because
   the gate at cli.py:3854 checks `config.integrity_scans.deployment_scan` which defaults to True
   in config.py:342, and there is no depth or milestone gate."
5. **CONSIDER EXISTING CODEBASES**: For every propagation recommendation, explicitly state what
   happens when running on a 50K-line existing project with a 3-line change.

### For mode-analyst
- Read cli.py's main() function COMPLETELY. It's long (~1000 lines from ~3250 onward). Do not skip sections.
- Pay special attention to the `_use_milestones` variable and everywhere it gates behavior.
- Map the COMPLETE Phase 0 → 0.25 → 0.5 → 0.6 → Orchestration → Post-orchestration pipeline.
- Note which phases are PRD-only vs universal.

### For upgrade-tracer
- Read quality_checks.py COMPLETELY. Every scan function, every regex pattern.
- Read e2e_testing.py COMPLETELY. Every constant, every function.
- Read tracking_documents.py COMPLETELY. Every function, every prompt constant.
- For each upgrade, trace it from CONFIG → GATE → EXECUTION → RECOVERY.
- When you encounter a `_use_milestones` gate, note that this means the feature runs in ALL non-milestone modes.

### For plan-synthesizer
- Do NOT start until both Phase 1 reports are complete and readable.
- Cross-validate: if mode-analyst says "mock scan runs in quick mode" but upgrade-tracer says
  "mock scan is gated by milestone config", RESOLVE THE CONFLICT by reading the actual code.
- The plan must be implementable in a SINGLE follow-up session (use the EXHAUSTIVE_PROMPT_FORMAT.md
  template for the implementation prompt that will come after this investigation).
- Include SPECIFIC line numbers for every file that would need changes.

### Output Location
All deliverables go in the `.agent-team/` directory:
- `.agent-team/MODE_ARCHITECTURE_ANALYSIS.md`
- `.agent-team/UPGRADE_TRACE_REPORT.md`
- `.agent-team/MODE_UPGRADE_PROPAGATION_PLAN.md`

### Success Criteria
The investigation is complete when MODE_UPGRADE_PROPAGATION_PLAN.md contains:
1. A complete Mode×Upgrade matrix with zero empty cells
2. A scoped scanning design with concrete API changes
3. A depth-gating design with specific config field proposals
4. An implementation roadmap with 4 ordered waves
5. A risk assessment for every proposed change
6. Enough specificity that the implementation prompt can be written directly from it
