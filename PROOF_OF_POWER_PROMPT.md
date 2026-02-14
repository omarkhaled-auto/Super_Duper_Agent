# Agent-Team PROOF OF POWER — Full Verification Run

## Your Mission

You are running a **single, comprehensive production build** that proves every upgrade from v2.0 through v12.3 works in a real-world application. This is not a test suite — this is a LIVE BUILD with a real PRD, real code generation, real scans, real fix loops, real E2E testing, and real browser verification.

**Application:** DrawSpace — a web-based 2D CAD application for construction professionals (.NET 8 / Angular 18 / PostgreSQL / Fabric.js)

Your job has THREE parts:
1. **Set up** the project directory, config, and verify the pre-generated PRD
2. **Launch** the agent-team using the **Claude Code CLI** (Omar Khaled's profile) and **monitor** it every 5-10 minutes
3. **Document EVERYTHING** in `VERIFICATION_LOG.md` — every checkpoint observed, every behavior noted, every scan result captured

The log you produce is **literal gold** — it becomes the evidence backbone for our investor brief. Every observation matters.

**IMPORTANT:** Use the Claude Code CLI installed under **Omar Khaled's** account. When running `agent-team`, make sure you're using the correct CLI profile/auth.

---

## PART 1: SETUP (Do This First)

### 1A: Create the Project Directory

```bash
mkdir -p ~/proof-of-power
cd ~/proof-of-power
```

### 1B: Discover and Create config.yaml

**DO NOT guess at the config format.** You must read the actual agent-team source code to produce a correct config.

#### Step 1: Find the config module

```bash
# Find the agent-team installation
which agent-team
pip show agent-team 2>/dev/null || pip3 show agent-team 2>/dev/null

# Find the config source file
find $(pip show agent-team 2>/dev/null | grep Location | cut -d' ' -f2) -name "config.py" -path "*/agent_team/*" 2>/dev/null
# Or search broadly:
find / -name "config.py" -path "*/agent_team/*" 2>/dev/null | head -5
```

#### Step 2: Read the config dataclasses

Open the config.py file and read it END TO END. Document:
- Every `@dataclass` class (these are config sections)
- Every field name, type, and default value
- The `_dict_to_config()` function (this is how YAML maps to dataclasses)
- The `load_config()` function
- Any validation logic
- Any `agents` section that allows per-agent model overrides

Pay special attention to:
- Which fields accept model names (look for `model` fields across ALL dataclasses — orchestrator, interview, agents, etc.)
- Which fields are `bool` with `enabled` pattern
- Which fields control scan behavior
- The exact section names (top-level YAML keys)

#### Step 3: Check for agent model configuration

Look specifically for:
- An `agents` config section that allows setting models per agent role
- Any `AgentsConfig` or similar dataclass
- Fields like `code_writer.model`, `researcher.model`, `reviewer.model`, etc.
- Whether individual agent models can be set to specific model strings

Also check what model strings are valid:
```bash
# Search for model string references
grep -rn "opus\|sonnet\|claude" $(find / -path "*/agent_team/*.py" 2>/dev/null) | grep -i "model" | head -20
```

#### Step 4: Generate the config with these MANDATORY requirements

Once you understand the exact schema, generate `config.yaml` following these rules:

**Model Configuration:**
- Set EVERY model field to `"opus"` — orchestrator, interview, and every individual agent
- If the system supports specific model version strings (e.g., `"claude-opus-4-6"` or `"opus-4.6"`), use the most advanced Opus variant available (Opus 4.6 / Claude Opus 4.6) for ALL agents. If it only accepts `"opus"` as the string, use `"opus"`.
- Check what model strings the code actually validates/accepts before writing them
- The goal: every single agent in the fleet runs on the most powerful model available

**Feature Enablement — ENABLE EVERYTHING:**
- Every `enabled: bool` field → `true`
- Every scan → `true`
- Every verification phase → `true`
- Every tracking document → `true`
- E2E testing → `true` (backend + frontend + browser)
- Browser testing → `true` with regression sweep
- All integrity scans → `true`
- All database scans → `true`
- All post-orchestration scans → `true`

**Specific Overrides (non-default values we need):**
- `depth.default`: `"exhaustive"` — maximum scan coverage
- `depth.scan_scope_mode`: `"full"` — always scan full project, never scoped
- `interview.enabled`: `false` — we provide a complete PRD, skip interview
- `milestone.enabled`: `true` — activate PRD+ milestone mode
- `milestone.review_recovery_retries`: `2` — more recovery attempts than default
- `convergence.min_convergence_ratio`: `0.9` — high bar for convergence
- `orchestrator.max_budget_usd`: `null` — unlimited budget
- `orchestrator.max_turns`: `500` — maximum turns
- `e2e_testing.max_fix_retries`: `5` — generous fix cycles
- `browser_testing.max_fix_retries`: `5` — generous fix cycles
- `post_orchestration_scans.max_scan_fix_passes`: `2` — multi-pass fixes at exhaustive depth
- `design_reference.urls`: `["https://linear.app"]`
- `design_reference.depth`: `"full"`
- `display.show_cost`: `true`
- `display.show_fleet_composition`: `true`
- `display.show_convergence_status`: `true`

**What NOT to do:**
- Do NOT include config keys that don't exist in the dataclasses — this may cause validation errors
- Do NOT use deprecated field locations (e.g., `milestone.mock_data_scan` was moved to `post_orchestration_scans.mock_data_scan` — check the source to confirm current locations)
- Do NOT invent field names — only use fields you found in the actual dataclass definitions
- Do NOT leave any scan or feature disabled — the entire point is maximum coverage

#### Step 5: Verify the config

```bash
# Quick validation — try a dry run
cd ~/proof-of-power
agent-team --dry-run --prd prd.md --design-ref https://linear.app 2>&1 | head -30
# If config errors appear, fix them based on the actual error messages
```

Write the final `config.yaml` to `~/proof-of-power/config.yaml`.

### 1C: Verify Firecrawl API Key

```bash
# Check that FIRECRAWL_API_KEY is set
echo $FIRECRAWL_API_KEY
# If empty, set it:
# export FIRECRAWL_API_KEY="fc-xxxxxxxxxxxxx"
```

### 1D: Verify the Pre-Generated PRD

The PRD has already been generated and is ready at `prd.md` in the project directory. It defines **DrawSpace** — a web-based 2D CAD application with:

- **Tech:** .NET 8 + EF Core + Dapper (dual ORM), CQRS/MediatR, Angular 18 + PrimeNG, Fabric.js, PostgreSQL, Docker Compose, SignalR
- **Entities:** 15+ (User, Organization, Project, Drawing, Layer, DrawingEntity, DrawingVersion, ExportJob, SharedLink, Comment, ReviewAnnotation, Template, TemplateCategory, ActivityLog, UserSettings)
- **Roles:** 4 (Admin, ProjectManager, Engineer, Viewer)
- **Milestones:** 5 (Foundation → Projects → Drawing Tools → Collaboration → Dashboard)
- **Endpoints:** 60+ SVC-xxx entries with full `{ field: type }` request/response DTOs
- **Enums:** 13+ with exact string values and state transition tables
- **Constraints:** 15 numbered rules targeting every scan category

**Verify the PRD is present and correct:**
```bash
cd ~/proof-of-power
wc -c prd.md
# Should be 55000-90000 bytes

# Quick sanity checks
grep -c "SVC-0" prd.md          # Should be 60+
grep -c "Dapper" prd.md          # Dual ORM trigger (>0)
grep -c "MediatR" prd.md         # CQRS trigger (>0)
grep -c "JsonStringEnumConverter" prd.md  # ENUM-004 trigger (>0)
```

If the PRD is missing or incomplete, generate it using `GENERATE_PRD_PROMPT.md` before proceeding.

### 1E: Initialize the Verification Log

Create `VERIFICATION_LOG.md`:

```markdown
# VERIFICATION LOG — DrawSpace Proof of Power Build

**Start Time:** [FILL ON START]
**Config:** exhaustive + PRD + milestones + all scans enabled
**PRD:** DrawSpace — .NET 8 / Angular 18 / PostgreSQL / Fabric.js / 5 milestones
**CLI:** agent-team (Omar Khaled's Claude Code profile)

---

## Pre-Flight Checks

- [ ] PF-01: config.yaml created with all sections
- [ ] PF-02: Firecrawl API key verified
- [ ] PF-03: PRD file verified (prd.md, 55-90KB)
- [ ] PF-04: agent-team version confirmed
- [ ] PF-05: --design-ref URL set (linear.app)
- [ ] PF-06: --dry-run shows exhaustive depth + correct agent count
- [ ] PF-07: Claude Code CLI confirmed (Omar Khaled's profile)

---
```

### 1F: Verify with Dry Run

```bash
cd ~/proof-of-power
agent-team --dry-run --prd prd.md --design-ref https://linear.app
```

**Observe and log:**
- Detected depth (should be "exhaustive")
- Agent count shown
- Config loaded correctly
- Design reference URL recognized

### 1G: Launch the Build

```bash
cd ~/proof-of-power
agent-team --prd prd.md --design-ref https://linear.app --no-interview 2>&1 | tee build_output.log
```

Keep this terminal running. Open a SECOND terminal for monitoring.

---

## PART 2: THE MASTER CHECKLIST

This is the complete list of **every observable checkpoint** from v2.0–v12.3. You MUST check on the build every 5-10 minutes and log what you observe against these checkpoints.

### How to Monitor

```bash
# Check build output (live)
tail -f ~/proof-of-power/build_output.log

# Check generated files
ls -la ~/proof-of-power/.agent-team/

# Check specific files as they appear
cat ~/proof-of-power/.agent-team/REQUIREMENTS.md
cat ~/proof-of-power/.agent-team/TASKS.md
cat ~/proof-of-power/.agent-team/MASTER_PLAN.md
cat ~/proof-of-power/.agent-team/MILESTONE_HANDOFF.md
cat ~/proof-of-power/.agent-team/FIX_CYCLE_LOG.md
cat ~/proof-of-power/.agent-team/E2E_COVERAGE_MATRIX.md
```

---

### PHASE 0: PRD ANALYSIS & DESIGN EXTRACTION

#### v2.0 — PRD+ Mode (6 fixes)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-01 | Analysis file persistence (RC-1) | After decomposition, check `.agent-team/analysis/` — are there actual files? Are there at least ceil(N/2) analysis files present? If missing, does auto-retry trigger? | ⬜ |
| CP-02 | TASKS.md per milestone (RC-2) | After each milestone starts, does `.agent-team/TASKS.md` get created? Does it contain TASK-NNN entries with dependencies? Check for the 9-step MANDATORY workflow in orchestrator behavior. | ⬜ |
| CP-03 | Review recovery in milestones (RC-3) | After milestone completes, if health is degraded, does the review recovery loop trigger? Check for `review_recovery_retries` behavior. Watch for "All retries exhausted" if recovery fails. | ⬜ |
| CP-04 | Zero mock data policy (RC-4) | Read any Angular service file generated — are there ANY `of()`, `delay()`, `Promise.resolve()`, hardcoded data patterns? The code-writer should have the ZERO MOCK DATA POLICY. | ⬜ |
| CP-05 | SVC-xxx wiring requirements (RC-5) | Check REQUIREMENTS.md — does it contain SVC-xxx entries mapping frontend services to backend endpoints? Does the architect produce an API Wiring Map table? | ⬜ |
| CP-06 | Mock data scan (RC-6) | In build output, look for mock data scan running post-milestone. Does it detect MOCK-001 through MOCK-007 patterns? Does it trigger a fix pass if violations found? | ⬜ |

#### v2.2 — UI Requirements Hardening (6 fixes)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-07 | Design extraction with retry | In Phase 0.6, does design extraction run against linear.app? If it fails, does it retry (up to `extraction_retries`)? Does fallback generation kick in if extraction fully fails? | ⬜ |
| CP-08 | UI_REQUIREMENTS.md created | Check `.agent-team/UI_REQUIREMENTS.md` — does it exist? Is it non-empty? Does it contain design tokens (colors, fonts, spacing)? | ⬜ |
| CP-09 | UI compliance in prompts | Observe code-writer behavior — does it follow UI COMPLIANCE POLICY (UI-FAIL-001..007)? Does reviewer check UI compliance? | ⬜ |
| CP-10 | UI compliance scan post-build | In build output, look for UI compliance scan running. Does it detect UI-001..004 patterns? If violations found, does `_run_ui_compliance_fix()` trigger? | ⬜ |

#### v10.0 — PRD Root-Level Detection

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-11 | REQUIREMENTS.md at root + .agent-team | Does the system find REQUIREMENTS.md at both project root AND `.agent-team/`? Log which location is used. | ⬜ |
| CP-12 | Recursive app type detection | Does `detect_app_type()` find the backend/frontend even if code is nested in subdirectories (e.g., `backend/`, `frontend/`)? | ⬜ |
| CP-13 | Design direction inference | Does `_infer_design_direction()` pick a direction based on PRD keywords (CAD/construction = "professional"/"technical"?) or fall back to `minimal_modern`? Log the chosen direction. | ⬜ |

---

### PHASE 1: ORCHESTRATION (Planning → Architecture → Coding → Review)

#### Core Orchestration

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-14 | MASTER_PLAN.md milestones | Does orchestrator create a MASTER_PLAN.md with 5 milestones matching the PRD? Are milestones ordered correctly? | ⬜ |
| CP-15 | Convergence loop operation | During each milestone, does the convergence loop run? How many cycles? Does `min_convergence_ratio` (0.9) get respected? Log cycle count per milestone. | ⬜ |
| CP-16 | GATE 5 enforcement (v10.1) | If review_cycles == 0 after orchestration, does GATE 5 force a review-only recovery pass? Log whether this triggers. | ⬜ |
| CP-17 | Review cycle counter (v10.2) | Does the review cycle counter track progress correctly? Does `pre_recovery_checked` tracking work? Log review cycle counts. | ⬜ |
| CP-18 | Convergence mandate in prompts (v10.0) | Observe orchestrator behavior — does it avoid 0-cycle runs? Is the convergence loop mandate enforced? | ⬜ |
| CP-19 | Requirements marking policy (v10.0) | Does the orchestrator mark requirements as MET/NOT MET in REQUIREMENTS.md? Check REQUIREMENTS.md after each milestone. | ⬜ |

#### Agent Fleet & Quality Standards (81 standards)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-20 | Code-writer standards | Are FRONT-001..021 + BACK-001..020 injected? Observe code quality in generated files. | ⬜ |
| CP-21 | Code-reviewer standards | Are REVIEW-001..015 active? Does reviewer catch anti-patterns? | ⬜ |
| CP-22 | Test-runner standards | Are TEST-001..015 + E2E-001..010 injected? | ⬜ |
| CP-23 | Database integrity standards | Are DB-001..008 + SEED-001..003 + ENUM-001..003 injected into architect/code-writer/reviewer? | ⬜ |
| CP-24 | API contract standards | Are API-001..003 standards injected into code-writer and reviewer? | ⬜ |
| CP-25 | Silent data loss standards | Are SDL-001..003 + ENUM-004 standards injected? | ⬜ |
| CP-26 | Endpoint XREF standards | Are XREF standards mapped to code-writer and architect? | ⬜ |

#### Prompt Policy Injections (17+ policies across 6 roles)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-27 | Architect — SVC-xxx table | Does architect produce SVC-xxx wiring entries with EXACT field schemas (`{ id: string, title: string }` format)? | ⬜ |
| CP-28 | Architect — Seed data completeness | Does architect specify complete seed data with all roles? | ⬜ |
| CP-29 | Architect — Enum/status registry | Does architect create an enum status registry? Do all layers reference it? | ⬜ |
| CP-30 | Architect — .NET serialization | Does architect include JsonStringEnumConverter in .NET startup boilerplate? | ⬜ |
| CP-31 | Architect — Endpoint completeness (v12) | Does architect verify every frontend call has a matching backend endpoint? | ⬜ |
| CP-32 | Architect — Milestone handoff prep (v4.0) | Does architect document every endpoint with exact response shapes for handoff? | ⬜ |
| CP-33 | Code-writer — Zero mock data policy | Does code-writer avoid all mock patterns (of(), delay(), Promise.resolve(), etc.)? | ⬜ |
| CP-34 | Code-writer — API contract compliance (v9.0) | Does code-writer use exact field names from REQUIREMENTS.md SVC-xxx table? | ⬜ |
| CP-35 | Code-writer — Fix cycle awareness (v4.0) | Does code-writer read FIX_CYCLE_LOG.md before attempting fixes? | ⬜ |
| CP-36 | Code-writer — Milestone handoff awareness (v4.0) | Does code-writer use exact contracts from MILESTONE_HANDOFF.md? | ⬜ |
| CP-37 | Reviewer — Enum serialization check (v11) | Does reviewer verify global JsonStringEnumConverter? | ⬜ |
| CP-38 | Reviewer — Silent data loss check (v11) | Does reviewer check for SDL-001/002/003 patterns? | ⬜ |
| CP-39 | Reviewer — API contract field verification (v9.0) | Does reviewer perform field-by-field API-001/002/003 checks? | ⬜ |
| CP-40 | Reviewer — Endpoint cross-ref (v12) | Does reviewer verify endpoint completeness? | ⬜ |
| CP-41 | Reviewer — UI compliance check (v2.2) | Does reviewer check UI compliance duties? | ⬜ |
| CP-42 | Reviewer — Mock detection (v2.0) | Does reviewer catch mock/stub patterns in service files? | ⬜ |

---

### PHASE 2: MILESTONE HANDOFF & CROSS-MILESTONE WIRING (v4.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-43 | MILESTONE_HANDOFF.md created | After Milestone 1 completes, does `.agent-team/MILESTONE_HANDOFF.md` get generated? Does it contain endpoint details, response shapes, DB state? | ⬜ |
| CP-44 | Enum/Status values in handoff (v4.0.1) | Does the handoff include the `### Enum/Status Values` subsection with exact valid values per entity? | ⬜ |
| CP-45 | Consumption checklist generated | Before Milestone 2 starts, does a consumption checklist get generated from M1's interfaces? Are `[ ]` checkboxes present? | ⬜ |
| CP-46 | Milestone 2 reads handoff | Does Milestone 2's execution prompt include MILESTONE_HANDOFF_INSTRUCTIONS? Does it reference M1's contracts? | ⬜ |
| CP-47 | Wiring completeness check | After M2 completes, is wired/total ratio computed? Is it checked against `wiring_completeness_gate` (1.0)? | ⬜ |
| CP-48 | normalize_milestone_dirs (v10.1) | If milestones use `milestone-N/` paths, does `normalize_milestone_dirs()` bridge to `milestones/milestone-N/`? | ⬜ |
| CP-49 | Milestone progress resume file | Does `milestone_progress.json` get written? If interrupted and resumed, are completed milestones skipped? | ⬜ |

---

### PHASE 3: POST-ORCHESTRATION SCANS (15 stages)

This is the heart of the verification. 13 of 15 stages have self-healing fix loops.

#### Stage 1: Mock Data Scan (v2.0 + v2.1)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-50 | MOCK-001..007 detection | Does scan detect RxJS of(), delay(), Promise.resolve(), mock variables, setTimeout, BehaviorSubject, new Observable? Log count of violations found. | ⬜ |
| CP-51 | Service file identification | Does scan correctly identify service/store/facade/composable files? Does it check both TS and Python files? | ⬜ |
| CP-52 | Fix loop triggered | If violations found, does `_run_mock_data_fix()` trigger? Does re-scan show reduced violations? Log fix passes. | ⬜ |
| CP-53 | Crash isolation | If scan errors, does the pipeline continue to the next scan? | ⬜ |

#### Stage 2: UI Compliance Scan (v2.2)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-54 | UI-001..004 pattern detection | Does scan check for arbitrary colors, fonts, spacing, component types? Log violations. | ⬜ |
| CP-55 | Fix loop triggered | If violations found, does `_run_ui_compliance_fix()` trigger and re-scan? | ⬜ |

#### Stage 3: Deployment Scan (v3.1)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-56 | DEPLOY-001..004 detection | Does scan cross-reference docker-compose.yml with .env files? Port mismatches? Undefined env vars? CORS origin mismatch? Service name mismatch? | ⬜ |
| CP-57 | .env file scanning | Does it scan all variants (.env, .env.example, .env.local, .env.development, etc.)? Does BOM/export prefix stripping work (v3.2 fix)? | ⬜ |
| CP-58 | Fix loop triggered | Does `_run_integrity_fix("deployment")` trigger on violations? | ⬜ |

#### Stage 4: Asset Scan (v3.1)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-59 | ASSET-001..003 detection | Does scan find broken image/font/media references, broken CSS url(), broken require/import for static assets? Does query string stripping work (v3.2 fix)? | ⬜ |
| CP-60 | Resolution paths | Does scan check all 7 candidate paths (file dir, root, public/, src/, assets/, static/, src/assets/)? | ⬜ |
| CP-61 | Fix loop triggered | Does `_run_integrity_fix("asset")` trigger? | ⬜ |

#### Stage 5: PRD Reconciliation (v3.1)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-62 | PRD reconciliation runs | Does the LLM sub-orchestrator compare REQUIREMENTS.md against built codebase? Is `PRD_RECONCILIATION.md` created? | ⬜ |
| CP-63 | Quality gate (v6.0) | Does the quality gate check REQUIREMENTS.md is >500 bytes AND contains REQ-xxx? (Exhaustive depth should always pass this.) | ⬜ |
| CP-64 | This is report-only | Confirm: no fix loop, just a report. | ⬜ |

#### Stage 6: Dual ORM Scan (v5.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-65 | Dual ORM detection | Does scan detect both EF Core AND Dapper usage in this .NET project? (PRD specifies dual ORM.) | ⬜ |
| CP-66 | DB-001..003 detection | Enum type mismatch (ORM string vs raw SQL integer)? Boolean type mismatch? DateTime format mismatch? Log violations. | ⬜ |
| CP-67 | Conditional skip | If only one ORM detected, does scan skip gracefully? (Should NOT skip for DrawSpace since both EF Core and Dapper are specified.) | ⬜ |
| CP-68 | Fix loop — database-specific prompt (v5.0.2) | Does `_run_integrity_fix("dual_orm")` use the correct database-specific fix prompt (not the asset prompt)? | ⬜ |

#### Stage 7: Default Value Scan (v5.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-69 | DB-004 detection | Boolean/enum properties without explicit default value? (Project.Status, Drawing.Status, ExportJob.Status, etc. should have defaults.) | ⬜ |
| CP-70 | DB-005 detection | Nullable properties accessed without null guard? (C# `{ get; set; }`, `{ get; init; }`, `{ get; private set; }` patterns.) | ⬜ |
| CP-71 | DB-005 Prisma FP fix (v10.0) | If any Prisma fields exist, are they correctly excluded from DB-005 to prevent false positives? | ⬜ |
| CP-72 | Null check window (500 chars, v5.0.2) | Are distant null guards correctly recognized within 500-character window? | ⬜ |

#### Stage 8: Relationship Scan (v5.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-73 | DB-006 detection | FK columns without navigation properties? (ProjectId, DrawingId, LayerId, OrganizationId, etc.) | ⬜ |
| CP-74 | DB-007 detection | Navigation properties without inverse relationships? | ⬜ |
| CP-75 | DB-008 detection | FK with no relationship configuration at all? | ⬜ |
| CP-76 | Framework detection | Does scan correctly identify EF Core patterns (C# entity classes)? | ⬜ |

#### Stage 9: API Contract Scan (v9.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-77 | SVC-xxx table parsing | Does scan parse the SVC table from REQUIREMENTS.md? Does it handle both 5-col and 6-col formats (v10.2 fix)? | ⬜ |
| CP-78 | API-001 detection | Backend DTO missing a field from the SVC schema? (PascalCase conversion: `drawingTitle` → `DrawingTitle`.) | ⬜ |
| CP-79 | API-002 detection (forward) | Frontend model uses a different field name than SVC schema? | ⬜ |
| CP-80 | API-002 detection (bidirectional, v11) | Frontend interface has extra fields not in backend DTO? Does 50% overlap threshold work? Are universal fields excluded? Are `_REQUEST_SUFFIXES` excluded (v11.0.2)? | ⬜ |
| CP-81 | API-003 detection | Unusual type warnings? | ⬜ |
| CP-82 | Balanced brace parsing (v11.0.2) | Do SVC entries with nested objects parse fully (not truncated at first `}`)? Does `_find_balanced_braces()` work? | ⬜ |
| CP-83 | API-004 detection (v12) | Frontend sends a field in POST/PUT that backend DTO doesn't have — silently dropped? (Write-side passthrough check.) | ⬜ |
| CP-84 | ENUM-004 detection (v11) | Does scan check for global JsonStringEnumConverter in Program.cs / Startup.cs? .NET-only, zero false positives. | ⬜ |
| CP-85 | Fix loop triggered | Does `_run_api_contract_fix()` trigger? Does it format first 20 violations? Does it inject fix cycle log? | ⬜ |

#### Stage 10: Silent Data Loss Scan (v11)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-86 | SDL-001 detection | CQRS command handlers missing persistence call (SaveChangesAsync, Commit, _repository.Add, etc.)? Query handler exclusion working? Event handler exclusion? | ⬜ |
| CP-87 | Conditional skip | Does scan skip on non-CQRS projects? (Should NOT skip for DrawSpace since PRD specifies CQRS with MediatR.) | ⬜ |
| CP-88 | Fix loop triggered | Does `_run_silent_data_loss_fix()` trigger? | ⬜ |

#### Stage 11: Endpoint Cross-Reference Scan (v12)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-89 | Backend route extraction | Does scan extract routes from .NET controllers ([HttpGet], [HttpPost], [Route] attributes)? ASP.NET `~` override handled (v12.2 BUG-5)? | ⬜ |
| CP-90 | Frontend call extraction | Does scan extract HTTP calls from Angular HttpClient, including variable-URL calls (v12.2 BUG-1)? Base URL variable resolution working (v12.2 BUG-3)? | ⬜ |
| CP-91 | XREF-001 detection | Frontend HTTP call with NO matching backend endpoint? Log count. | ⬜ |
| CP-92 | XREF-002 detection | Frontend call matches endpoint but WRONG method? | ⬜ |
| CP-93 | Function-call URL filter (v12.3) | Are `${this.func(...)}/path` patterns demoted to `severity="info"` and excluded from fix loop? | ⬜ |
| CP-94 | Dedup by line number (v12.2 BUG-2) | No duplicate violations from regex overlap? | ⬜ |
| CP-95 | Express mount prefix handling (v12.2 BUG-4) | If any Express-style routes exist, are mount prefixes applied correctly? (Not applicable for .NET but verify scanner doesn't crash.) | ⬜ |
| CP-96 | Severity filter in fix loop (v12.3) | Only `error` and `warning` violations trigger fix passes? Info-only violations reported but don't waste budget? | ⬜ |
| CP-97 | Fix loop triggered | Does `_run_endpoint_xref_fix()` trigger on actionable violations? Re-scan shows reduced violations? | ⬜ |

---

### PHASE 4: E2E TESTING (v3.0)

#### Backend API E2E

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-98 | App type detection | Does `detect_app_type()` correctly identify .NET backend + Angular frontend + PostgreSQL? Playwright detected? | ⬜ |
| CP-99 | E2E_COVERAGE_MATRIX.md generated (v4.0) | Before tests start, is the coverage matrix created from REQUIREMENTS.md? Does it list every endpoint, route, and workflow? | ⬜ |
| CP-100 | Backend E2E test plan | Does E2E planner create `.agent-team/E2E_TEST_PLAN.md`? Does it cover all API workflows? | ⬜ |
| CP-101 | Role-based API testing | Are test accounts for ALL 4 roles (Admin, ProjectManager, Engineer, Viewer) tested? Positive + negative access tests? | ⬜ |
| CP-102 | Cross-role workflows | User A creates → User B approves → User C views? Explicit state passing via entity IDs? | ⬜ |
| CP-103 | Mutation verification rule (v11) | Does every mutation test verify the effect with a subsequent GET? (Not just POST → 200, but POST → GET → verify data.) | ⬜ |
| CP-104 | Endpoint exhaustiveness rule (v12) | Does backend E2E agent test EVERY endpoint, not just happy paths? | ⬜ |
| CP-105 | Role authorization rule (v12) | Does backend E2E agent verify role-based access restrictions? | ⬜ |
| CP-106 | Fix loop — fix app not test | On failure, does fix loop fix the APP code, not the test? Is the 20% test-correction guard rail active? | ⬜ |
| CP-107 | FIX_CYCLE_LOG.md in use (v4.0) | Does the fix loop write to and read from FIX_CYCLE_LOG.md? Are previous cycle strategies avoided? | ⬜ |
| CP-108 | E2E_RESULTS.md created | After backend tests, is `.agent-team/E2E_RESULTS.md` updated with pass/fail counts? | ⬜ |

#### Frontend Playwright E2E

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-109 | 70% backend gate | Does frontend only run if backend API tests achieved ≥70% pass rate? | ⬜ |
| CP-110 | Route completeness | Is every defined route navigated? Are blank pages and error pages flagged as failures? | ⬜ |
| CP-111 | Placeholder detection | Are "coming soon", "placeholder", "TODO", "Lorem ipsum" detected as HARD FAILURES? | ⬜ |
| CP-112 | Form submission testing | Are forms filled, submitted, AND verified to persist? | ⬜ |
| CP-113 | State persistence rule (v12) | Does frontend E2E verify data persists after save (revisit testing)? | ⬜ |
| CP-114 | Dropdown verification rule (v12) | Are dropdowns tested for correct options? | ⬜ |
| CP-115 | Button outcome verification (v12) | Does every button click verify the outcome, not just that it was clickable? | ⬜ |
| CP-116 | Coverage matrix updated | Does the frontend E2E agent mark rows in E2E_COVERAGE_MATRIX.md? | ⬜ |
| CP-117 | Coverage completeness gate | After E2E phase, is coverage checked against 80% gate? Does incomplete coverage add `"e2e_coverage_incomplete"` to recovery? | ⬜ |

#### E2E Quality Patterns

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-118 | E2E-001..007 scan | Does the E2E quality scan run? Hardcoded timeouts? Hardcoded ports? Mock data? Empty tests? Auth coverage? Placeholder text? Role access failures? | ⬜ |
| CP-119 | This is report-only | Confirm: E2E Quality is report-only (no fix loop). | ⬜ |

#### E2E Phase Tracking

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-120 | Phase markers | Are `e2e_backend`, `e2e_frontend`, `e2e_testing` phase markers set correctly? | ⬜ |
| CP-121 | Resume behavior | If build were interrupted and resumed, would backend be skipped if already complete? (Observe marker behavior.) | ⬜ |

---

### PHASE 5: BROWSER MCP TESTING (v8.0)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-122 | Browser testing gate | Does browser testing check E2E pass rate ≥70% before proceeding? | ⬜ |
| CP-123 | App startup agent | Does `_run_browser_startup_agent()` start the app, verify health endpoint, extract startup info? | ⬜ |
| CP-124 | Workflow generation | Does `generate_browser_workflows()` create workflow definitions from REQUIREMENTS.md? How many workflows? | ⬜ |
| CP-125 | Workflow execution | Does `_run_browser_workflow_executor()` execute each workflow with Playwright MCP? Screenshots taken? | ⬜ |
| CP-126 | Deep verification rules (v12) | Does browser executor follow DEEP VERIFICATION RULES? Content verification? Not just "page loaded"? | ⬜ |
| CP-127 | Fix loop for failures | On workflow failure, does `_run_browser_workflow_fix()` fix the APP (not the test)? | ⬜ |
| CP-128 | Regression sweep (v8.0) | After fixes, does `_run_browser_regression_sweep()` re-run ALL previously passed workflows? | ⬜ |
| CP-129 | Content verification in regression (v12) | Does regression sweep verify content, not just navigation? | ⬜ |
| CP-130 | Screenshot diversity | Does `check_screenshot_diversity()` verify screenshots aren't all identical? | ⬜ |
| CP-131 | Readiness report | Is `generate_readiness_report()` called? Does it produce a meaningful summary? | ⬜ |
| CP-132 | Finally cleanup | Does the finally block terminate the app process? Does `_browser_app_started` flag prevent cleanup on startup failure? | ⬜ |
| CP-133 | Resume support | Does `RunState.completed_browser_workflows` track which workflows passed? | ⬜ |
| CP-134 | Seed credential extraction (v10.2) | Does `_extract_credentials()` correctly parse seed credentials for login workflows? Prisma/ORM patterns? bcrypt? Role enums? | ⬜ |
| CP-135 | Sanitized filenames (v10.2) | Are workflow filenames sanitized to avoid Windows path colon issues? `_sanitize_filename()` working? | ⬜ |

---

### PHASE 6: RECOVERY & FINAL REPORT

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-136 | Recovery report generated | Is a recovery report generated listing all scan results, fix passes, and remaining issues? | ⬜ |
| CP-137 | Recovery type labels (v10.0) | Are recovery types labeled specifically (e.g., "mock_data_fix", "ui_compliance_fix", "silent_data_loss_fix") instead of generic "scan_fix"? | ⬜ |
| CP-138 | Scan result logging (v10.0) | Are scan results logged throughout the pipeline? Not silent? | ⬜ |
| CP-139 | Cost tracking | Is total cost displayed at the end? | ⬜ |

---

### CROSS-CUTTING INFRASTRUCTURE

#### v6.0 — Depth-Intelligent Scanning

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-140 | Exhaustive depth = full scans | At exhaustive depth, ALL scans should run full-project (not scoped). Confirm no scoping is applied. | ⬜ |
| CP-141 | E2E auto-enabled | At exhaustive depth, E2E should be auto-enabled. Confirm `e2e_testing.enabled` is true after gating. | ⬜ |
| CP-142 | Browser auto-enabled (PRD mode) | At exhaustive + PRD, browser testing should be auto-enabled. Confirm. | ⬜ |
| CP-143 | max_scan_fix_passes = 2 | At exhaustive depth, fix passes should be set to 2. Confirm multi-pass behavior if violations found. | ⬜ |
| CP-144 | User overrides sacred | If any explicit config value conflicts with depth gating, the user's value wins. (Verify by observing that our explicit `max_fix_retries: 5` for E2E is preserved, not overridden to 3.) | ⬜ |

#### v4.0 — Fix Cycle Log

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-145 | FIX_CYCLE_LOG.md created | Is `.agent-team/FIX_CYCLE_LOG.md` created by the first fix cycle? | ⬜ |
| CP-146 | Fix log populated across ALL fix types | Do mock data, UI compliance, integrity, E2E, and review recovery fix functions all write to the log? | ⬜ |
| CP-147 | Different strategy each cycle | Does the fix agent read previous cycles and apply DIFFERENT strategies? (Check log content.) | ⬜ |

#### Pipeline Fix Loop Verification (v12.3 audit)

| # | Checkpoint | What to Observe | Status |
|---|-----------|----------------|--------|
| CP-148 | 13/15 stages have self-healing loops | Verify: Mock, UI, Deploy, Asset, Dual ORM, Default Value, Relationship, API Contract, SDL, XREF, E2E Backend, E2E Frontend, Browser all have fix loops. PRD Reconciliation and E2E Quality are report-only. | ⬜ |
| CP-149 | Each scan in its own try/except | If ANY scan crashes, the next one still runs. Observe crash isolation in action (or verify by reading build output for "Error in X, continuing"). | ⬜ |
| CP-150 | max_scan_fix_passes=0 → scan-only | At quick depth this would mean no fixes. At exhaustive, max_scan_fix_passes=2 means up to 2 fix passes per scan. Verify the passes happen. | ⬜ |

---

### FILES TO VERIFY AT END

| # | File | What to Check | Status |
|---|------|--------------|--------|
| FV-01 | `.agent-team/REQUIREMENTS.md` | REQ-xxx entries? SVC-xxx entries with field schemas? SEED/ENUM policies referenced? | ⬜ |
| FV-02 | `.agent-team/TASKS.md` | TASK-NNN entries with dependencies and file scopes? | ⬜ |
| FV-03 | `.agent-team/MASTER_PLAN.md` | 5 milestones? Ordered correctly? | ⬜ |
| FV-04 | `.agent-team/MILESTONE_HANDOFF.md` | Endpoints, response shapes, DB state, env vars, enum/status values? Multiple milestones documented? | ⬜ |
| FV-05 | `.agent-team/FIX_CYCLE_LOG.md` | Fix cycles from multiple fix types? Root causes documented? Different strategies per cycle? | ⬜ |
| FV-06 | `.agent-team/E2E_COVERAGE_MATRIX.md` | Requirements mapped to tests? Checkbox completion rate? | ⬜ |
| FV-07 | `.agent-team/E2E_TEST_PLAN.md` | Comprehensive test plan? All endpoints covered? | ⬜ |
| FV-08 | `.agent-team/E2E_RESULTS.md` | Pass/fail counts for backend and frontend? | ⬜ |
| FV-09 | `.agent-team/PRD_RECONCILIATION.md` | Mismatches identified? | ⬜ |
| FV-10 | `.agent-team/UI_REQUIREMENTS.md` | Design tokens present? Colors, fonts, spacing? | ⬜ |
| FV-11 | `docker-compose.yml` | Backend + frontend + PostgreSQL services? Ports consistent? | ⬜ |
| FV-12 | Source: Program.cs / Startup.cs | JsonStringEnumConverter configured globally? | ⬜ |
| FV-13 | Source: CQRS Command Handlers | Every command handler calls SaveChangesAsync? | ⬜ |
| FV-14 | Source: Angular Services | Zero mock patterns? Real HttpClient calls? | ⬜ |
| FV-15 | Source: Seed Data | All 4 roles seeded? All fields populated? | ⬜ |
| FV-16 | Source: Entity Models | Status enums have defaults? Nullable fields have guards? FK → Navigation properties wired? | ⬜ |

---

## PART 3: MONITORING PROTOCOL

### Every 5 Minutes During Active Build:

1. **Check build output** — `tail -20 ~/proof-of-power/build_output.log`
2. **Check .agent-team/ files** — `ls -la ~/proof-of-power/.agent-team/`
3. **Identify which phase we're in** — Planning? Coding? Review? Post-orch scan? E2E? Browser?
4. **Log the observation** — Write to VERIFICATION_LOG.md with timestamp

### Every 10 Minutes During Scan/Fix/E2E Phases:

1. **Read scan output** — What violations were found? What severity?
2. **Read fix cycle log** — How many fix passes? What strategies?
3. **Read E2E results** — Pass/fail counts? Which tests failing?
4. **Cross-reference against checklist** — Which checkpoints can you mark?
5. **Check for non-checklist anomalies** — Anything unexpected? Errors? Warnings? Weird timing? Log as FINDING-NNN.

### CRITICAL — Record Issues OUTSIDE the Checklist

The 150 checkpoints cover known upgrade features. But real production runs surface issues nobody predicted. **If you observe ANY failure, bug, unexpected behavior, crash, warning, or anomaly that does NOT map to a numbered checkpoint, log it immediately** in a dedicated section of VERIFICATION_LOG.md:

```markdown
## 🚨 NON-CHECKLIST FINDINGS

### FINDING-001: [Descriptive title]
**Timestamp:** [when observed]
**Severity:** CRITICAL / HIGH / MEDIUM / LOW
**Phase:** [which pipeline phase]
**What happened:** [Detailed description]
**Evidence:** [Log line, file path, error message — copy exact text]
**Impact:** [What did this break? Did the pipeline recover? Did it cascade?]

### FINDING-002: ...
```

Examples of things to capture here:
- Unexpected crashes or tracebacks in build output
- Scans that ran but produced nonsensical results
- Fix loops that ran more times than expected or got stuck
- Files that should exist but don't (or vice versa)
- Performance anomalies (a phase taking 10x longer than expected)
- Agent behavior oddities (agent ignoring instructions, repeating itself)
- Config values that didn't take effect
- Race conditions or ordering issues between pipeline stages
- Any error message in the build log, even if the pipeline recovered
- Anything that makes you think "that's weird" — LOG IT

These non-checklist findings are often MORE valuable than the planned checkpoints because they reveal real-world edge cases we haven't anticipated. Number them sequentially (FINDING-001, FINDING-002, ...) so we can reference them later.

### After Build Completes:

1. **Run file verification** — Check all FV-01 through FV-16
2. **Read generated source code** — Spot-check for mock data, enum correctness, CQRS persistence
3. **Read recovery report** — What issues remain?
4. **Calculate final checkpoint score** — How many of 150 checkpoints observed?
5. **Write the FINAL SUMMARY** at the bottom of VERIFICATION_LOG.md including:
   - Checkpoint score: X/150 observed, Y passed, Z failed
   - Non-checklist findings count: N findings logged
   - Top 3 most impressive observations (for investor brief)
   - Top 3 issues discovered (for engineering backlog)
   - Total build time and cost

### VERIFICATION_LOG.md Format

For each checkpoint observation, use this format:

```markdown
## [TIMESTAMP] — Phase: [PHASE NAME]

### Checkpoint CP-XX: [Name]
**Status:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL / 🔍 NOT TRIGGERED / ⏭️ N/A
**What happened:** [Detailed description of what you observed]
**Evidence:** [File path, log line, or screenshot reference]
**Notes:** [Any unexpected behavior, surprises, or insights]
```

---

## Execution Rules

1. **SETUP MUST BE PERFECT** — The PRD, config, and design-ref URL determine what checkpoints trigger. A bad config = missing evidence.
2. **MONITOR ACTIVELY** — Don't launch and walk away. Check every 5-10 minutes. The observations during the build are MORE VALUABLE than the final files.
3. **LOG EVERYTHING** — Even "this scan found 0 violations" is valuable data. It proves the scan RAN and the code was clean.
4. **NOTE UNEXPECTED BEHAVIOR** — If something triggers that shouldn't, or doesn't trigger when expected, that's critical information.
5. **CAPTURE TIMING** — How long each phase takes. How long fix loops take. How many cycles to convergence. This is performance data.
6. **DON'T INTERFERE** — Let the build run autonomously. Don't use `!!` interventions unless it's going catastrophically wrong. The point is to prove autonomous operation.
7. **IF BUILD FAILS** — Don't restart immediately. Document the failure point, the error, and which checkpoints were observed before failure. Then resume if possible.
8. **FINAL LOG IS GOLD** — The VERIFICATION_LOG.md you produce is the single most important deliverable. It becomes the evidence backbone for the V5 investor brief.
9. **NON-CHECKLIST FINDINGS ARE GOLD TOO** — If you see something weird, broken, or unexpected that doesn't match any CP-XX checkpoint, log it as a FINDING-NNN in the dedicated section. These surprise discoveries often reveal more about system maturity than the planned checks.
