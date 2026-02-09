# Agent Team — Cheat Sheet

Quick reference for every command, flag, config option, and feature.

---

## Commands

### Run a task

```bash
agent-team "your task description here"
```

**How:** Put your task in quotes after `agent-team`. The system detects depth from keywords, runs an interview, then builds it.
**When:** Any time you want something built, fixed, or refactored.

### Interactive mode

```bash
agent-team
agent-team -i
agent-team -i "starting idea"
```

**How:** Run with no task or with `-i`. You get a prompt where you can send multiple tasks one after another.
**When:** You want to explore, send follow-up tasks, or have a back-and-forth session.

### Build from a PRD

```bash
agent-team --prd spec.md
```

**How:** Pass a markdown file containing your product requirements. Automatically uses exhaustive depth.
**When:** You have a full spec written out and want the system to build the entire thing.

### Dry run (preview without spending tokens)

```bash
agent-team --dry-run "add user authentication"
```

**How:** Add `--dry-run` to any command. Shows detected depth, agent count, interview settings, and model — then exits.
**When:** You want to see what the system would do before committing to an API call.

---

## Subcommands

### Generate a starter config

```bash
agent-team init
```

**How:** Run from your project directory. Creates a `config.yaml` with documented defaults.
**When:** First time setting up agent-team in a project, or you want to customize behavior.

### Check project state

```bash
agent-team status
```

**How:** Lists all files in `.agent-team/`, shows run ID, task, phase, and whether it was interrupted.
**When:** You want to see what agent-team has produced so far, or check if there's a saved run.

### Clean up

```bash
agent-team clean
```

**How:** Asks for confirmation, then deletes the `.agent-team/` directory.
**When:** Starting fresh, or the previous run's artifacts are no longer useful.

### Resume an interrupted run

```bash
agent-team resume
```

**How:** Loads saved state from `.agent-team/STATE.json`. Currently experimental — shows the saved state info.
**When:** You hit Ctrl+C during a run and want to see where it left off.

### Print usage guide

```bash
agent-team guide
```

**How:** Prints a quick reference of all commands and flags to the terminal.
**When:** You need a reminder of what's available without opening docs.

---

## Flags

| Flag | Example | What it does | When to use |
|------|---------|-------------|-------------|
| `--depth LEVEL` | `--depth thorough` | Override depth: `quick`, `standard`, `thorough`, `exhaustive` | You want a specific depth regardless of keywords |
| `--agents N` | `--agents 15` | Set total agent count (distributed across phases) | You want more or fewer agents than the default for the depth |
| `--model MODEL` | `--model sonnet` | Override the orchestrator model | You want to use a cheaper/different model |
| `--max-turns N` | `--max-turns 1000` | Set max agentic turns per session | Long tasks that might hit the default 500 limit |
| `--config FILE` | `--config custom.yaml` | Use a specific config file | You have project-specific settings |
| `--cwd DIR` | `--cwd /path/to/project` | Set working directory | You're running agent-team from a different directory |
| `--no-interview` | `--no-interview` | Skip the interview phase entirely | Task is self-explanatory, no clarification needed |
| `--interview-doc FILE` | `--interview-doc .agent-team/INTERVIEW.md` | Use an existing interview document | You ran an interview before and want to reuse it |
| `--design-ref URL` | `--design-ref https://stripe.com` | Scrape a website for design tokens (colors, fonts, spacing) | Building UI and you want to match an existing design |
| `--dry-run` | `--dry-run` | Preview without API calls | Check depth/agents/config before spending tokens |
| `--progressive` | `--progressive` | Enable progressive verification (contracts → lint → types → tests) | You want automated quality checks after each task |
| `--no-progressive` | `--no-progressive` | Disable progressive verification | Verification is slowing things down or isn't needed |
| `--map-only` | `--map-only` | Run codebase analysis and print results, then exit | You just want to see the project structure analysis |
| `--no-map` | `--no-map` | Skip codebase mapping | Small project or you want to save time |
| `-v` / `--verbose` | `-v` | Show all tool calls and agent details | Debugging what agents are doing, or a run seems stuck |
| `--version` | `--version` | Print version number | Check which version you're running |

---

## Depth Levels

Depth controls how many agents deploy and how thorough the process is.

| Depth | Auto-detected by these words | Agents | Best for |
|-------|------------------------------|--------|----------|
| **Quick** | quick, fast, simple | 1-2 | One-file fix, typo, broken import |
| **Standard** | *(default when no keywords match)* | 2-5 | Normal feature, bug fix, small integration |
| **Thorough** | thorough, careful, deep, detailed, refactor, redesign, restyle, rearchitect, overhaul, rewrite, restructure, revamp, modernize | 3-8 | Multi-file feature, refactor, cross-cutting changes |
| **Exhaustive** | exhaustive, comprehensive, complete, migrate, migration, replatform, entire, every, whole | 5-10 | Full app build, major system, migration |

**Override:** `--depth thorough` always wins over auto-detection.
**Multiple keywords:** The most intensive depth wins. "Quick but comprehensive" → Exhaustive.

---

## Interview

The interview runs before agents deploy. It explores your codebase and asks questions to build a requirements document.

### Phases

| Phase | What happens | Your role |
|-------|-------------|-----------|
| **Discovery** (first half) | Interviewer reads your code with tools, asks broad questions | Answer, provide context about your project |
| **Refinement** (second half) | Proposes approaches, asks focused questions | Correct misunderstandings, add details |
| **Ready** (after minimum exchanges) | Shows final summary, asks for confirmation | Say "yes" to finalize or add what's missing |

### End the interview

Say any of: `I'm done`, `let's go`, `start building`, `proceed`, `ship it`, `lgtm`, `ready`, `build it`, `go ahead`, `that's it`, `begin`, `execute`, `run it`, `do it`, `good to go`, `looks good`

- **Before minimum exchanges:** System redirects you back with focused questions (won't finalize yet)
- **After minimum exchanges:** System shows a summary and asks you to confirm
- **After confirmation:** Writes INTERVIEW.md and hands off to the orchestrator

### Skip it

```bash
agent-team --no-interview "fix the login bug"
```

**When:** Task is simple and self-explanatory.

### Reuse a previous interview

```bash
agent-team --interview-doc .agent-team/INTERVIEW.md "build the dashboard"
```

**When:** You already ran an interview and want to skip doing it again.

---

## Constraints

Write rules in your task or during the interview. The system picks them up automatically and enforces them across all agents.

| Write this... | System detects it as... |
|--------------|------------------------|
| "never change the database schema" | Prohibition |
| "don't modify the API contract" | Prohibition |
| "must use TypeScript" | Requirement |
| "always validate user input" | Requirement |
| "only change files in src/components/" | Scope limit |
| "just the frontend, nothing else" | Scope limit |
| "Build with Express.js and MongoDB" | Technology requirements (auto-extracted) |
| "Include 20+ tests" | Test count requirement (auto-extracted) |

**ALL CAPS and emphasis words** ("absolutely", "critical", "strictly") give constraints higher priority.

**Technology names** (Express.js, React, Next.js, MongoDB, TypeScript, Tailwind CSS, Docker, etc.) are automatically extracted as `must use X` constraints. **Test counts** ("20+ tests", "10 unit tests") are extracted as `must have N+ tests` constraints.

**How:** Just write naturally in your task — `agent-team "add search, but NEVER change the database schema"`.
**When:** You have non-negotiable rules the agents must follow.

---

## User Interventions

Redirect agents mid-run without restarting.

```
!! focus on the API, stop changing CSS
```

**How:** Type `!!` followed by your message and press Enter while agents are running. Your message is queued in the background and sent to the orchestrator as a highest-priority follow-up when the current turn finishes.
**When:** Agents are going in the wrong direction and you want to course-correct without restarting.
**Note:** On Windows, the terminal may not show what you're typing while output is streaming — type anyway and press Enter. The system reads your input in the background.

---

## Graceful Interrupts

| Action | What happens |
|--------|-------------|
| First Ctrl+C | Prints a warning, keeps running |
| Second Ctrl+C | Saves state to `.agent-team/STATE.json` and exits |

**How:** Press Ctrl+C once to warn, twice to stop.
**When:** You need to stop a run but want to preserve progress.

### PRD+ Mode Milestone Resume

In PRD+ mode, if a milestone is interrupted (Ctrl+C or unexpected error), progress is saved to `.agent-team/milestone_progress.json`. On the next run, completed milestones are skipped and execution resumes from the interrupted milestone. The progress file is automatically cleaned up on resume.

---

## Config Options

Set these in `config.yaml` (create one with `agent-team init`).

### Orchestrator

| Option | Default | What it does |
|--------|---------|-------------|
| `model` | `"opus"` | Model for the orchestrator |
| `max_turns` | `500` | Max agentic turns per session |
| `max_budget_usd` | `null` | Cost cap — warns at 80%, hard stops at 100%. Set to `null` for unlimited |
| `max_thinking_tokens` | `null` | Enable extended thinking for the orchestrator. Must be >= 1024 or `null` |

### Depth

| Option | Default | What it does |
|--------|---------|-------------|
| `default` | `"standard"` | Depth when no keywords are detected |
| `auto_detect` | `true` | Detect depth from task keywords. Set to `false` to always use `default` |
| `keyword_map` | *(see README)* | Which words map to which depth levels. Fully customizable |

### Convergence

| Option | Default | What it does |
|--------|---------|-------------|
| `max_cycles` | `10` | Max convergence loop iterations before stopping |
| `escalation_threshold` | `3` | How many times a requirement can fail before escalation |
| `max_escalation_depth` | `2` | Max re-planning levels before asking the user |
| `master_plan_file` | `"MASTER_PLAN.md"` | Filename for the milestone plan (PRD mode) |
| `min_convergence_ratio` | `0.9` | Minimum pass ratio to declare convergence (0.0–1.0) |
| `recovery_threshold` | `0.8` | Below this, convergence status is "recovering" |
| `degraded_threshold` | `0.5` | Below this, convergence status is "degraded" |

### Interview

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `true` | Run the interview phase. `false` skips it entirely |
| `model` | `"opus"` | Model for the interviewer |
| `max_exchanges` | `50` | Hard cap on interview exchanges |
| `min_exchanges` | `3` | Minimum exchanges before allowing finalization |
| `require_understanding_summary` | `true` | Force structured "My Understanding" sections in responses |
| `require_codebase_exploration` | `true` | Force tool use (Glob/Read/Grep) during Discovery phase |
| `max_thinking_tokens` | `null` | Enable extended thinking for the interviewer. Must be >= 1024 or `null` |

### Codebase Map

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `true` | Analyze project structure before planning |
| `max_files` | `5000` | Max files to scan |
| `max_file_size_kb` | `50` | Max size (KB) for Python files |
| `max_file_size_kb_ts` | `100` | Max size (KB) for TypeScript/JavaScript files |
| `exclude_patterns` | `["node_modules", ".git", ...]` | Directories to skip (merged with built-in defaults) |
| `timeout_seconds` | `30` | Timeout for map generation |

### Scheduler

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `true` | Enable smart task scheduling |
| `max_parallel_tasks` | `5` | Max tasks per execution wave |
| `conflict_strategy` | `"artificial-dependency"` | How to resolve file conflicts between parallel tasks |
| `enable_context_scoping` | `true` | Compute per-task file context |
| `enable_critical_path` | `true` | Run critical path analysis to find bottleneck tasks |

### Verification

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `true` | Enable progressive verification |
| `blocking` | `true` | `true` = failures are hard stops. `false` = failures become warnings |
| `run_lint` | `true` | Run lint phase |
| `run_type_check` | `true` | Run type-check phase |
| `run_tests` | `true` | Run test phase |
| `run_build` | `true` | Run build phase |
| `run_security` | `true` | Run security scan phase |
| `run_quality_checks` | `true` | Run regex-based anti-pattern spot checks |
| `min_test_count` | `0` | Minimum test count to pass verification (0 = no minimum) |

### Orchestrator Sequential Thinking

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `true` | Enable Sequential Thinking at orchestrator decision points |
| `depth_gate` | *(see below)* | Which decision points activate at each depth level |
| `thought_budgets` | `{1: 8, 2: 10, 3: 12, 4: 8}` | Max thoughts per decision point |

Decision points: (1) Pre-run strategy, (2) Architecture checkpoint, (3) Convergence reasoning, (4) Completion verification.

Default depth gating: All 4 points active at every depth level — depth controls fleet scale, not reasoning quality.

### Milestone (PRD Mode)

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `false` | Enable per-milestone PRD orchestration loop (two-phase: decomposition + execution) |
| `max_parallel_milestones` | `1` | Max milestones to execute concurrently |
| `health_gate` | `true` | Block next milestone if previous is unhealthy |
| `wiring_check` | `true` | Run cross-milestone wiring analysis between milestones |
| `resume_from_milestone` | `null` | Resume from a specific milestone ID (null = start from beginning) |
| `wiring_fix_retries` | `1` | Retries for wiring fix passes |
| `max_milestones_warning` | `30` | Warn if PRD decomposes into more milestones than this |
| `review_recovery_retries` | `1` | Max review recovery attempts per milestone (0 = disabled) |
| `mock_data_scan` | `true` | Scan for mock data patterns in service files after each milestone |

### Quality

| Option | Default | What it does |
|--------|---------|-------------|
| `production_defaults` | `true` | Inject production-readiness requirements into the planner |
| `craft_review` | `true` | Enable CODE CRAFT review pass in reviewers |
| `quality_triggers_reloop` | `true` | Quality violations feed back into the convergence loop |

### Display

| Option | Default | What it does |
|--------|---------|-------------|
| `show_cost` | `true` | Show cost breakdown after each run |
| `show_fleet_composition` | `true` | Show agent fleet details during deployment |
| `show_convergence_status` | `true` | Show convergence cycle progress |
| `verbose` | `false` | Show all tool calls |

### Design Reference

| Option | Default | What it does |
|--------|---------|-------------|
| `urls` | `[]` | Reference website URLs for design inspiration |
| `depth` | `"full"` | Scrape depth: `"branding"`, `"screenshots"`, or `"full"` |
| `max_pages_per_site` | `5` | Max pages to scrape per URL |

### Agents

Override model or disable specific agents:

```yaml
agents:
  code_writer:
    model: "opus"       # keep opus for coding quality
  researcher:
    model: "sonnet"     # use sonnet to save cost
  security_auditor:
    enabled: false      # disable for non-security tasks
```

Available agents: `planner`, `researcher`, `architect`, `task_assigner`, `code_writer`, `code_reviewer`, `test_runner`, `security_auditor`, `debugger`

The `spec-validator` agent is always active (read-only, non-configurable) — it compares your original request against REQUIREMENTS.md to catch spec drift. `integration-agent` and `contract-generator` are enabled by default via `scheduler.enabled` and `verification.enabled`.

### Built-in Quality Standards

81 code quality anti-patterns are **always injected** into relevant agents — no configuration needed:

| Agent | Standards Injected | Anti-Patterns |
|-------|-------------------|---------------|
| `code_writer` | Frontend + Backend | 41 (FRONT-001→021, BACK-001→020) |
| `code_reviewer` | Code Review | 15 (REVIEW-001→015) |
| `test_runner` | Testing | 15 (TEST-001→015) |
| `debugger` | Debugging | 10 (DEBUG-001→010) |
| `architect` | Architecture Quality | Quality rules (no numbered codes) |

Other agents (planner, researcher, task_assigner, security_auditor) receive no quality standards.

---

## Files Produced

Everything goes in `.agent-team/` in your project:

| File | What it is | Created by |
|------|-----------|------------|
| `INTERVIEW.md` | Requirements from the interview | Interviewer |
| `INTERVIEW_BACKUP.json` | Raw transcript backup | CLI |
| `REQUIREMENTS.md` | Master checklist — source of truth | Planner |
| `TASKS.md` | Atomic task breakdown with dependencies | Task Assigner |
| `MASTER_PLAN.md` | Milestone plan | Orchestrator (PRD mode only) |
| `CONTRACTS.json` | Interface contracts for verification | Contract Generator |
| `VERIFICATION.md` | Verification results per task | Verification pipeline |
| `STATE.json` | Saved run state | CLI (on interrupt) |
| `milestone_progress.json` | Milestone resume data (which milestones completed, which was interrupted) | CLI (on interrupt/error in PRD+ mode) |

---

## Common Recipes

### Cheapest possible run

```bash
agent-team --no-interview --depth quick "fix the typo in header.tsx"
```

### Thorough feature with budget cap

```yaml
# config.yaml
orchestrator:
  max_budget_usd: 10.0
```

```bash
agent-team "refactor the authentication module"
```

### Match a design reference

```bash
agent-team "build a landing page" --design-ref https://stripe.com https://linear.app
```

### Preview before committing

```bash
agent-team --dry-run "migrate the database to PostgreSQL"
```

### Non-blocking verification (keep going despite lint failures)

```yaml
# config.yaml
verification:
  blocking: false
```

### Force deeper interviews

```yaml
# config.yaml
interview:
  min_exchanges: 8
```

### Limit parallel agents

```yaml
# config.yaml
scheduler:
  max_parallel_tasks: 2
```

---

## Verification Status

**Live E2E: 13/13 checks passed (100%)** — convergence cycles, requirements marking, task completion, contract generation, health display, schedule waves, recovery logging, cycle counter, and diagnostic post-orchestration all verified against real Claude API.

**Convergence stress test passed:** RLE encoder with 13 tricky tests (digit-in-input, multi-digit counts, roundtrip identity) — agent iterated 3 times within a single run to reach all-pass.

---

## PRD+ Mode Critical Fixes (v2.x)

Six root causes were identified and fixed after the BAYAN Tender project revealed that the agent-team could build frontend and backend independently but produce 0% functional wiring (75 mock service methods, zero review cycles, no TASKS.md per milestone).

### Fix 1: Analysis File Persistence (RC-1)
**Problem:** PRD Analyzer Fleet planners returned analysis inline instead of writing to `.agent-team/analysis/` files. Synthesizer had nothing to read from disk.
**Fix:** Strengthened `build_decomposition_prompt()` in agents.py with explicit per-planner Write tool instructions and file paths. Added validation gate in cli.py after decomposition to warn if analysis files are missing.

### Fix 2: TASKS.md in Milestone Mode (RC-2)
**Problem:** `build_milestone_execution_prompt()` said "Run the full convergence loop" but never mentioned TASKS.md or TASK ASSIGNER. Coding agents worked ad-hoc without structured task decomposition.
**Fix:** Added complete 9-step `[MILESTONE WORKFLOW — MANDATORY STEPS]` block including TASK ASSIGNER, CODING FLEET, REVIEW FLEET, MOCK DATA GATE, and FINAL CHECK. Updated Section 4 MILESTONE EXECUTION in ORCHESTRATOR_SYSTEM_PROMPT to include steps c (TASK ASSIGNER) through g.

### Fix 3: Milestone Review Recovery (RC-3)
**Problem:** After each milestone session, cli.py checked health but had no review recovery mechanism. The main flow had robust recovery; the milestone loop had none.
**Fix:** Added review recovery loop to `_run_prd_milestones()` that triggers when health is failed/degraded. Parameterized `_run_review_only()` to accept milestone-scoped `requirements_path`. Added mock data scan after recovery. New config options: `milestone.review_recovery_retries` (default: 1), `milestone.mock_data_scan` (default: true).

### Fix 4: Zero Mock Data Policy (RC-4)
**Problem:** Code-writer prompt never prohibited mock data. Frontend developers naturally scaffolded with `of(mockData).pipe(delay(500))` and never replaced it.
**Fix:** Added `ZERO MOCK DATA POLICY` section to CODE_WRITER_PROMPT listing all prohibited patterns (RxJS of(), delay(), Promise.resolve(), hardcoded variables). Added FRONT-019 (Mock Data in Services), FRONT-020 (DTO/Enum Mismatch), FRONT-021 (Hardcoded Service Responses) to code_quality_standards.py.

### Fix 5: Service-to-API Wiring (RC-5)
**Problem:** WIRE-xxx items only covered module-level connections (imports, routes). No check that frontend services made real HTTP calls to backend endpoints.
**Fix:** Added SVC-xxx (Service-to-API Wiring) requirement type to REQUIREMENTS.md template. Added API Wiring Map table and SVC generation instructions to ARCHITECT_PROMPT. Added SVC-xxx verification rules and mock detection to CODE_REVIEWER_PROMPT. Added MOCK DATA GATE step (5a.2) to workflow between coding and review. Added integration verification block to milestone execution for milestones with predecessors.

### Fix 6: Mock Detection Quality Checks (RC-6)
**Problem:** `quality_checks.py` had no mock data detection patterns. Mock data passed all quality gates.
**Fix:** Added 5 regex patterns (MOCK-001 through MOCK-005) for RxJS of(), delay(), Promise.resolve(), mock variable names, and setTimeout. Added `_check_mock_data_patterns()` check function and `run_mock_data_scan()` public API for targeted scanning. Service files identified by path pattern matching.

### New Config Options

```yaml
milestone:
  review_recovery_retries: 1  # Max review recovery attempts per milestone (0 = disabled)
  mock_data_scan: true         # Scan for mock data after each milestone
```

### New Quality Standards

| ID | Category | Description |
|----|----------|-------------|
| FRONT-019 | Anti-Pattern | Mock data in service files |
| FRONT-020 | Anti-Pattern | DTO/Enum mismatch between frontend and backend |
| FRONT-021 | Anti-Pattern | Hardcoded service responses |
| MOCK-001 | Spot Check | RxJS of() with hardcoded data / delay() pipe in services |
| MOCK-002 | Spot Check | Promise.resolve() with hardcoded data in services |
| MOCK-003 | Spot Check | Mock/fake/dummy variable names in services |
| MOCK-004 | Spot Check | setTimeout simulating async API in services |
| MOCK-005 | Spot Check | delay() simulating network latency in services |

### New Requirement Types

| Type | Purpose | Created By |
|------|---------|-----------|
| SVC-xxx | Service-to-API wiring (frontend method → backend endpoint) | Architecture Fleet |

### Hardening Pass (v2.1)

A comprehensive review and hardening pass was applied to all 6 fixes, adding robustness and expanding coverage to both standard PRD mode and PRD+ milestone mode.

| Fix | Hardening Change | Impact |
|-----|-----------------|--------|
| Fix 1 | Analysis validation threshold raised from 1/3 to ceil(N/2) | Stricter — requires at least half of analysis files |
| Fix 1 | Auto-retry on missing analysis files | Self-healing decomposition before synthesizer runs |
| Fix 2 | TASKS.md existence check after milestone execution in cli.py | Catches skipped task decomposition step |
| Fix 3 | Recovery break condition checks ratio vs `recovery_threshold` | More precise recovery decisions (was too permissive) |
| Fix 3 | "All retries exhausted" warning when max recovery attempts fail | Clear failure signaling with health/ratio stats |
| Fix 3 | Post-orchestration mock data scan added for **standard mode** | Both PRD and PRD+ modes now protected by mock scanning |
| Fix 4 | Added Vue/Nuxt (`$fetch`, `useFetch`), Python (`requests`, `httpx`), and `BehaviorSubject` patterns | Framework-agnostic mock detection |
| Fix 6 | Added MOCK-006 (BehaviorSubject with hardcoded initial data) | Catches `new BehaviorSubject([{...}])` |
| Fix 6 | Added MOCK-007 (new Observable returning inline data) | Catches `new Observable(sub => sub.next(...))` |
| Fix 6 | Extended service path regex: `store`, `facade`, `composable` | Broader file detection for Vue/Angular patterns |
| Fix 6 | Extended mock scanning to Python `.py` files | Backend service mock detection |

### Updated Quality Standards (post-hardening)

| ID | Category | Description |
|----|----------|-------------|
| MOCK-006 | Spot Check | BehaviorSubject initialized with hardcoded data in services |
| MOCK-007 | Spot Check | new Observable returning inline mock data in services |

### Test Suite: 120 Dedicated Tests

All 6 fixes and their hardening are covered by `tests/test_prd_fixes.py` (120 tests):

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| `TestCheckMockDataPatterns` | 38 | All 7 MOCK patterns, false positive exclusions, 9 service path patterns, Python files, severity levels, line numbers, multi-violation |
| `TestRunMockDataScan` | 6 | Integration: empty project, mock detection, clean files, test exclusion, multi-file, severity sorting |
| `TestMilestoneConfigNewFields` | 10 | `review_recovery_retries` and `mock_data_scan` defaults, custom values, `_dict_to_config()`, partial YAML |
| `TestCodeWriterAntiMockPolicy` | 12 | ZERO MOCK DATA POLICY, prohibited patterns, Angular/React/Vue/Python coverage, BehaviorSubject |
| `TestFrontendStandardsAntiMock` | 6 | FRONT-019/020/021 existence and content |
| `TestSVCWiringInPrompts` | 8 | SVC-xxx in orchestrator, architect, reviewer prompts; MOCK DATA GATE |
| `TestMilestoneExecutionPromptContent` | 6 | TASKS.md, TASK ASSIGNER, MANDATORY steps, 9-step workflow |
| `TestDecompositionPromptAnalysis` | 3 | Write tool enforcement, analysis directory, file persistence |
| `TestAnalysisValidationThreshold` | 6 | ceil(N/2) formula for 1/2/3/5/10/66 chunks |
| `TestSaveMilestoneProgress` | 3 | JSON validity, empty list, overwrite |
| `TestRunReviewOnlySignature` | 4 | `requirements_path` and `depth` params with defaults |
| `TestRunMockDataFixSignature` | 3 | Existence, parameter list, async verification |
| `TestCrossFixIntegration` | 4 | Import wiring, `_ALL_CHECKS` registration, Violation dataclass |
| `TestDualModeCoverage` | 5 | Mock rules present in both standard and milestone prompt paths |

### Test Results
**1978 tests passed (120 new), 3 failed (pre-existing), 5 skipped, 0 regressions.**

---

## UI Requirements Hardening (v2.2)

Six fixes ensuring that design reference extraction produces guaranteed, enforceable UI requirements — never silently skipped.

### Fix 1: Config Fields
**Problem:** No config options for retry behavior, fallback generation, or content quality checking.
**Fix:** Added `extraction_retries`, `fallback_generation`, `content_quality_check` to `DesignReferenceConfig`. Added `ui_compliance_scan` to `MilestoneConfig`.

### Fix 2: Guaranteed Generation
**Problem:** Design extraction could silently fail, leaving agents with no UI guidance.
**Fix:** Added `validate_ui_requirements_content()`, `run_design_extraction_with_retry()`, and `generate_fallback_ui_requirements()` in design_reference.py. Wired retry+fallback flow in cli.py Phase 0.6.

### Fix 3: Hard Enforcement
**Problem:** Even when UI requirements existed, agents could ignore them.
**Fix:** Added UI COMPLIANCE POLICY (UI-FAIL-001..007) to CODE_WRITER_PROMPT. Added UI compliance duties to CODE_REVIEWER_PROMPT. Added `[UI COMPLIANCE ENFORCEMENT]` block to milestone prompt.

### Fix 4: Dedicated UI Phase
**Problem:** No explicit step in the orchestration for setting up the design system.
**Fix:** Added Step 3.7 UI DESIGN SYSTEM SETUP in orchestrator prompt and step 3b in milestone workflow.

### Fix 5: UI Compliance Scan
**Problem:** No automated scanning for UI compliance violations.
**Fix:** Added UI-001..004 regex patterns in quality_checks.py. Added `run_ui_compliance_scan()` and `_run_ui_compliance_fix()` in cli.py.

### Fix 6: Tests
**84 tests in test_ui_requirements.py** across 19 test classes.

### Hardening Pass (v2.2.1)

| Change | Impact |
|--------|--------|
| `_RE_FONT_FAMILY` regex matches camelCase (`fontFamily`) | Catches React/CSS-in-JS patterns |
| `_RE_COMPONENT_TYPE` handles plurals (`Buttons`, `Cards`) | Broader detection coverage |
| Retry wrapper splits exceptions (retriable vs fatal) | No retries on unexpected errors |
| `_RE_CONFIG_FILE` uses path-segment boundaries | Avoids ThemeToggle.tsx false positive |
| Config validation for `extraction_retries >= 0` | Prevents invalid config |
| `_RE_ARBITRARY_SPACING` handles directional variants (`pt-`, `mx-`) | Catches all Tailwind spacing |
| `_infer_design_direction` uses word boundaries | Avoids substring false matches |

### Test Results
**2063 tests passed (84 new), 2 failed (pre-existing), 0 regressions.**

---

## E2E Testing Phase (v3.0) — Guaranteed Functional Verification

The most significant upgrade to agent-team. After convergence-driven reviews, mock data scans, and UI compliance checks all pass, a new **E2E Testing Phase** verifies that the built application **actually works end-to-end** — real HTTP calls to real APIs, real Playwright browser interactions against real pages.

```
BEFORE:  PRD → Build → Review → Unit Tests → "Hope it works"
AFTER:   PRD → Build → Review → Unit Tests → E2E Backend API → E2E Playwright → VERIFIED WORKING
```

### Why This Matters

Other AI coding tools stop at "code compiles + tests pass." Agent-team now guarantees the app **works from the user's perspective**:
- Auth flows that actually authenticate
- CRUD operations that actually persist data
- Multi-step wizards that complete all steps
- Role-based access that correctly restricts/allows
- Forms that submit and save — not just render

### How It Works

The E2E phase runs as a post-orchestration step (after UI compliance scan, before recovery report). It consists of two parts:

**Part 1: Backend API E2E** — Deploys a sub-orchestrator that:
1. Reads REQUIREMENTS.md + scans route/controller files
2. Creates an E2E test plan covering all API workflows
3. Writes real HTTP test scripts (not mocks)
4. Executes tests against a running server
5. On failure: fixes the APP (not the test), re-runs

**Part 2: Frontend Playwright E2E** — Deploys a sub-orchestrator that:
1. Reads REQUIREMENTS.md + scans pages/components
2. Creates Playwright test scripts with stable selectors
3. Navigates every route, tests every workflow
4. Verifies forms submit, wizards complete, navigation works
5. On failure: fixes the APP (not the test), re-runs

### Enabling E2E Testing

E2E testing is **opt-in** (disabled by default due to cost — $2-5 per E2E phase):

```yaml
# config.yaml
e2e_testing:
  enabled: true                      # Enable E2E phase
  backend_api_tests: true            # Part 1: Backend API E2E
  frontend_playwright_tests: true    # Part 2: Playwright E2E
  max_fix_retries: 5                 # Fix-rerun cycles per part (min: 1)
  test_port: 9876                    # Non-standard port for test isolation
  skip_if_no_api: true               # Auto-skip Part 1 if no API detected
  skip_if_no_frontend: true          # Auto-skip Part 2 if no frontend detected
```

### Config Options

| Option | Default | What it does |
|--------|---------|-------------|
| `enabled` | `false` | Enable E2E testing phase (opt-in) |
| `backend_api_tests` | `true` | Run backend API E2E tests |
| `frontend_playwright_tests` | `true` | Run frontend Playwright E2E tests |
| `max_fix_retries` | `5` | Max fix-rerun cycles per part (minimum 1 — at least one fix attempt) |
| `test_port` | `9876` | Port for test server (1024–65535, non-standard to avoid conflicts) |
| `skip_if_no_api` | `true` | Auto-skip backend tests if no API detected |
| `skip_if_no_frontend` | `true` | Auto-skip frontend tests if no frontend detected |

**No budget limit.** The E2E phase runs until all tests pass or `max_fix_retries` is exhausted. Cost is tracked for reporting but never gates execution — the whole point is guaranteed verification.

### App Detection

`detect_app_type()` automatically identifies your project's stack:

| Detected | How |
|----------|-----|
| Backend framework | package.json deps (express, nestjs), requirements.txt (fastapi, django, flask) |
| Frontend framework | package.json deps (react, vue, angular), config files (next.config, nuxt.config, angular.json) |
| Language | TypeScript (tsconfig.json), JavaScript, Python |
| Package manager | Lock files (package-lock.json → npm, yarn.lock → yarn, pnpm-lock.yaml → pnpm) |
| Database | Prisma schema, Mongoose models, Sequelize, Django ORM |
| Playwright | `@playwright/test` in devDependencies |

### Backend API E2E — Battle-Tested Patterns

The backend E2E prompt includes patterns learned from the BAYAN Tender project:

**Role-Based API Testing (mandatory when auth detected):**
- Test accounts for EVERY role in the system
- Positive access tests (role CAN access its endpoints)
- Negative access tests (role CANNOT access restricted endpoints)
- Complete auth flow per role (register → login → access → verify)
- Cross-role workflows (User A creates → User B approves → User C views)
- Explicit state passing via entity IDs between role switches

**State Passing:**
```javascript
// CORRECT: Capture entity ID from creation, pass to subsequent role
const createRes = await fetch('/api/items', { method: 'POST', ... });
const { id: itemId } = await createRes.json();
const approveRes = await fetch(`/api/items/${itemId}/approve`, ...);

// WRONG: Fragile, non-deterministic
await page.click('table tbody tr:first-child');
```

### Frontend Playwright E2E — PRD Feature Coverage

**Route Completeness:** Every defined route is navigated. Blank pages, error pages, and unrendered components are test failures.

**Placeholder Detection (HARD FAILURE):** Pages containing "will be implemented", "coming soon", "placeholder", "TODO", "Lorem ipsum", "not yet available", "future milestone", or "under construction" fail immediately.

**Dead Component Detection:** Components that exist in the source tree but are unreachable via navigation are flagged as warnings. Utility components (Spinner, Layout, Modal, Toast, Provider, etc.) are automatically excluded.

**Interaction Depth:** Multi-step workflows are tested through EVERY step — a 10-step wizard verified by screenshotting step 1 is a test failure.

**Form Submission:** Every form is filled, submitted, and verified to persist — not just rendered.

### Fix Loop — Pattern-Specific Guidance

When E2E tests fail, the fix loop diagnoses the failure type and applies the right strategy:

| Failure Pattern | Fix Strategy |
|----------------|-------------|
| Placeholder text | IMPLEMENT the feature (not remove the text) |
| 403 Forbidden on valid role | Fix backend auth middleware/guards |
| Dead navigation | Add missing route/import/link (not delete component) |
| Incomplete wizard/form | Fix step N specifically (earlier steps work) |

**Test Correction Exception:** The default rule is "fix the APP, not the test." But if the app behavior is correct and the test expectation is wrong (e.g., test expects "Submit" but app correctly uses "Save Changes"), the test may be fixed instead. Guard rail: if >20% of fixes are test corrections, a warning is emitted.

**Severity Classification:**
- `IMPLEMENT` — Missing feature (placeholder) → code-writer builds it
- `FIX_AUTH` — Role access bug → code-writer fixes middleware/guards
- `FIX_WIRING` — Dead navigation → code-writer adds routes/imports
- `FIX_LOGIC` — Step N fails → debugger diagnoses, code-writer fixes

### 70% Backend Gate

Frontend Playwright tests only run if backend API tests achieve **≥70% pass rate**. One flaky API test doesn't block all frontend verification. If backend is between 70–99%, a warning is printed but Playwright proceeds.

### Resume After Crash

The E2E phase uses granular 3-level phase tracking:

| Phase Marker | Added When | Resume Behavior |
|-------------|-----------|-----------------|
| `e2e_backend` | Backend tests pass or partial | Skip backend on resume |
| `e2e_frontend` | Frontend tests pass or partial | Skip frontend on resume |
| `e2e_testing` | Both complete | Entire phase skipped |

If the process crashes mid-frontend, backend is skipped and only frontend re-runs. Failed phases are **NOT** marked complete — they re-run on resume.

### Quality Patterns (E2E-001..007)

Seven quality patterns scan E2E test files and UI templates:

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| E2E-001 | Hardcoded `setTimeout`/`time.sleep` in E2E tests | Warning |
| E2E-002 | Hardcoded `localhost:XXXX` ports (use config/env) | Warning |
| E2E-003 | Mock data in E2E tests (`mockData`, `fakeResponse`, `Promise.resolve`) | Error |
| E2E-004 | Empty test bodies (no assertions) | Error |
| E2E-005 | App has auth but no auth E2E test (inverted check) | Warning |
| E2E-006 | Placeholder text in UI components ("coming soon", "Lorem ipsum") | Error |
| E2E-007 | Role access failure (403/Forbidden) in E2E results | Error |

### Quality Standards (E2E-001..010)

Ten E2E testing standards injected into the test-runner agent:

| ID | Standard |
|----|----------|
| E2E-001 | No hardcoded timeouts — use waitFor, waitForResponse, waitForSelector |
| E2E-002 | Use configurable base URL and port — never hardcode localhost:3000 |
| E2E-003 | Zero mock data in E2E tests — all calls must hit real server |
| E2E-004 | Every test must have meaningful assertions (not empty bodies) |
| E2E-005 | Tests must be independent — no order dependency, clean state per test |
| E2E-006 | Use stable selectors: data-testid, getByRole, getByText — never CSS classes |
| E2E-007 | Include both happy path and error path for each workflow |
| E2E-008 | Server lifecycle managed: start before, health check, teardown after |
| E2E-009 | API tests verify response status + body structure + data integrity |
| E2E-010 | Playwright tests verify visual state (element visible, text present, navigation correct) |

### Files Created/Modified

| File | Changes |
|------|---------|
| `src/agent_team/config.py` | `E2ETestingConfig` dataclass + `AgentTeamConfig.e2e_testing` field + `_dict_to_config()` wiring + validation |
| `src/agent_team/state.py` | `E2ETestReport` dataclass (12 fields) |
| `src/agent_team/e2e_testing.py` **(NEW)** | `AppTypeInfo`, `detect_app_type()`, `parse_e2e_results()`, 3 prompt constants (~638 lines) |
| `src/agent_team/quality_checks.py` | E2E-001..007 patterns, `_check_e2e_quality()`, `run_e2e_quality_scan()` |
| `src/agent_team/code_quality_standards.py` | `E2E_TESTING_STANDARDS` (10 standards) + `_AGENT_STANDARDS_MAP` entry |
| `src/agent_team/cli.py` | `_run_backend_e2e_tests()`, `_run_frontend_e2e_tests()`, `_run_e2e_fix()`, post-orchestration wiring (~200 lines) |
| `tests/test_e2e_phase.py` **(NEW)** | 186 tests across 24 test classes |

### Files Produced (at runtime)

| File | What it is | Created by |
|------|-----------|------------|
| `.agent-team/E2E_TEST_PLAN.md` | E2E test plan (what to test, expected behavior) | E2E Planner |
| `.agent-team/E2E_RESULTS.md` | E2E test results (pass/fail counts, failure details) | E2E Test Runner |
| `tests/e2e/api/` | Backend API E2E test scripts | E2E Code Writer |
| `tests/e2e/browser/` | Playwright `.spec.ts` test files | E2E Code Writer |

### Review & Hardening Pass (v3.0.1)

A comprehensive code review identified 3 CRITICAL and 5 HIGH bugs. All 8 were fixed and verified:

| Bug | Fix | Impact |
|-----|-----|--------|
| **C1**: Fix loop burned retries on "skipped" health | Guard changed to `not in ("passed", "skipped", "unknown")` | Prevents wasting 5 retries on no-op |
| **C2**: Frontend fix loop never updated `failed_tests` | Added `e2e_report.failed_tests = pw_report.failed_tests[:]` each cycle | Stale failure data in final report |
| **C3**: E2E-005/006/007 were dead code (compiled but never called) | Implemented in `_check_e2e_quality()` and `run_e2e_quality_scan()` | 3 quality patterns now active |
| **H1**: All 3 async E2E functions silently swallowed exceptions | Added `traceback.format_exc()` to all exception handlers | No more silent failures |
| **H3**: No skip message when frontend skipped | Added messages for `skip_if_no_frontend` and backend below 70% | Users know why frontend was skipped |
| **H4**: Outer try/except swallowed entire E2E phase | Added traceback logging + `health="failed"` + `skip_reason` | Phase-level failures visible in report |
| **H5**: Resume marked failures as complete | `completed_phases.append()` only when `health in ("passed", "partial")` | Failed phases re-run on resume |

### Test Suite: 186 Tests

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| `TestE2ETestingConfig` | 6 | Defaults, YAML parsing, _dict_to_config, validation |
| `TestAppTypeInfo` | 6 | Express, Next.js, FastAPI, frontend-only, full-stack, empty |
| `TestE2ETestReport` | 5 | Defaults, health computation, field population |
| `TestParseE2EResults` | 5 | Good/partial/all failures, missing/malformed file |
| `TestBackendE2EPrompt` | 5 | Requirements read, workflow testing, real HTTP, server lifecycle |
| `TestFrontendE2EPrompt` | 5 | Playwright install, stable selectors, webServer, headless |
| `TestE2EFixPrompt` | 3 | "Fix APP not test", debugger deployment, re-run |
| `TestE2EQualityPatterns` | 8 | E2E-001..004 detection + exemptions |
| `TestE2EQualityScan` | 3 | Integration scan, non-e2e exclusion, config exclusion |
| `TestE2EQualityStandards` | 3 | Standards exist, count ≥ 10, agent mapping |
| `TestE2ECLIWiring` | 6 | Phase position, skip-if-disabled, backend-first, 70% gate |
| `TestE2EPromptHardening` | 20 | Role testing, cross-role, placeholders, form submission, severity, guard rail |
| `TestE2EQualityPatternsHardening` | 4 | E2E-005/006/007 regex matching |
| `TestE2EResumeLogic` | 5 | Fix cycles, failed_tests, pass rate, health computation |
| `TestE2EPhaseTriggering` | 9 | Skip/run conditions, 70% gate, no-backend/no-frontend |
| `TestE2EFixLoop` | 5 | Stop on pass, run on failure, max retries, cycle counting |
| `TestE2EHealthComputation` | 8 | Skipped, passed, partial, failed, mixed scenarios |
| `TestE2EDetectAppTypeEdgeCases` | 14 | Corrupt JSON, empty, Vue, Django, NestJS, Mongoose, Flask, etc. |
| `TestE2EParseResultsEdgeCases` | 8 | Frontend-only, backend-only, empty, Unicode, large numbers |
| `TestE2EPromptFormatSafety` | 8 | Empty strings, special chars, multiline, no extra placeholders |
| `TestE2EResumeAndStateTracking` | 8 | Phase distinctness, serialization, resume skip logic |
| `TestReviewFixVerification` | 18 | All 8 review fixes verified in source code |
| `TestE2EQualityScanIntegration` | 8 | Full filesystem integration for E2E-005/006/007 |
| `TestE2EConfigEdgeCases` | 8 | Port range, retry minimum, legacy keys, partial YAML |

### Test Results
**2378 tests passed (186 in test_e2e_phase.py), 2 failed (pre-existing test_mcp_servers.py), 0 regressions.**

### Final Review Verdict
**SHIP IT.** Zero critical issues. Zero high-priority issues remaining. Three medium advisory items (E2E-006 false positive on HTML `placeholder` attributes, E2E-007 matching passing 403 tests, unconditional `e2e_testing` phase marker) — all non-blocking.

---

## Post-Build Integrity Scans (v3.1) — Deployment, Asset & PRD Reconciliation

Three non-blocking post-build scans that catch deployment misconfigurations, broken asset references, and PRD-to-implementation drift before the E2E testing phase.

### Scan 1: Deployment Configuration (DEPLOY-001..004)

Cross-references `docker-compose.yml` with `.env` files, CORS origins, and service names:

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| DEPLOY-001 | Port mismatch between docker-compose and app config | Warning |
| DEPLOY-002 | Undefined environment variables (no default, not in .env) | Warning |
| DEPLOY-003 | CORS origin mismatch between backend config and frontend URL | Warning |
| DEPLOY-004 | Service name mismatch in docker-compose references | Warning |

**Scans:** `.env`, `.env.example`, `.env.local`, `.env.development`, `.env.production`, `.env.staging`, `.env.test`
**Excludes:** Built-in vars (`NODE_ENV`, `PATH`, etc.), vars with fallback values (`||`, `??`, `os.getenv` 2-arg)

### Scan 2: Static Asset References (ASSET-001..003)

Detects broken `src`, `href`, `url()`, `require()`, and `import` references to static files:

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| ASSET-001 | Broken image/font/media reference (file not found) | Warning |
| ASSET-002 | Broken CSS url() reference | Warning |
| ASSET-003 | Broken require/import for static assets | Warning |

**Resolves:** 7 candidate paths (file dir, project root, `public/`, `src/`, `assets/`, `static/`, `src/assets/`)
**Excludes:** External URLs, data URIs, template variables, webpack aliases (`@/`, `~/`)

### Scan 3: PRD Reconciliation (PRD-001)

Deploys a sub-orchestrator LLM call to compare REQUIREMENTS.md against the built codebase, producing `PRD_RECONCILIATION.md` with any mismatches found.

### Config

```yaml
integrity_scans:
  deployment_scan: true    # Docker-compose cross-reference
  asset_scan: true         # Broken static asset detection
  prd_reconciliation: true # PRD vs implementation comparison
```

All scans are **non-blocking warnings** with `_MAX_VIOLATIONS=100` cap. Each wrapped in its own try/except for crash isolation.

### Test Results
**309 tests in test_integrity_scans.py across 35+ test classes, 2687 full suite passed.**

---

## Production-Readiness Audit (v3.2)

A 6-agent team audit (4 reviewers + wiring-verifier + test-engineer) found and fixed 4 bugs:

| Severity | Bug | Fix |
|----------|-----|-----|
| CRITICAL | Nested `asyncio.run()` in `_run_review_only()` | Switched to `await` pattern |
| HIGH | `_resolve_asset()` didn't strip query strings | Added query/fragment stripping |
| MEDIUM | PRD reconciliation h4 headers exiting mismatch mode | Fixed section parser |
| MEDIUM | `.env` BOM/export prefix not stripped | Added BOM + export handling |

**259 new tests** (154 cross-upgrade + 105 wiring), **2946 total passing**, all wiring verified.

---

## Per-Phase Tracking Documents (v4.0) — Guaranteed Agent Progress Visibility

The most significant quality upgrade since E2E Testing. Three per-phase tracking documents that give agents **structured memory between phases** — preventing the three catastrophic failure modes that no existing check catches proactively.

### Why This Matters

| Failure Mode | What Happened | Cost Impact |
|-------------|--------------|-------------|
| **Superficial E2E Testing** | Agent writes 5 happy-path tests for a project with 30+ workflows, declares "passed" | Untested features ship broken |
| **Blind Fix Loops** | Fix agent applies the SAME fix 3 times because each cycle has zero memory of previous attempts | $0.40-$1.20 wasted per repeated cycle |
| **Zero Cross-Milestone Wiring** | BAYAN Tender: Milestone 3 scaffolded 75 mock service methods because it didn't know Milestone 1's real API endpoints | Expensive repair passes after all milestones complete |

### The Three Documents

```
BEFORE:  Agents work blind — no checklist, no fix history, no interface contracts
AFTER:   Agents read → work → mark progress → next agent reads what was done
```

**Document 1: E2E_COVERAGE_MATRIX.md** (E2E Testing Phase)
- Generated from REQUIREMENTS.md BEFORE test writing
- Maps EVERY requirement, endpoint, route, and cross-role workflow to a test
- Agents mark `[x]` as tests are written and pass
- Fix loops read the matrix to target specific failing rows
- Agent CANNOT complete E2E with unchecked rows

**Document 2: FIX_CYCLE_LOG.md** (ALL Fix Loops)
- Created by the first fix cycle, appended by each subsequent cycle
- Records: what failed, what was tried, what files changed, what the result was
- Next fix agent MUST read the full log before attempting a fix
- Prevents repeating failed strategies across all 5 fix types

**Document 3: MILESTONE_HANDOFF.md** (PRD+ Milestone Mode)
- Written by each completing milestone
- Lists EVERY exposed interface: endpoints, response shapes, env vars, database state
- Next milestone reads it BEFORE coding and marks each consumed interface as wired
- Consumption checklist tracks `[x]` for every endpoint actually wired
- Prevents the "75 mock methods" failure

### How It Works

**E2E Coverage Matrix Flow:**
1. CLI generates `E2E_COVERAGE_MATRIX.md` from REQUIREMENTS.md (auto-extracts endpoints, routes, workflows)
2. Backend E2E prompt instructs agent to fill and mark the matrix as tests are written
3. Frontend E2E prompt instructs agent to add frontend routes and mark them
4. E2E Fix prompt instructs agent to READ the matrix to understand which tests are failing
5. After E2E phase, CLI parses the matrix and reports coverage stats
6. Coverage below gate (default 80%) adds `"e2e_coverage_incomplete"` to recovery types

**Fix Cycle Log Flow:**
1. Each fix function initializes `FIX_CYCLE_LOG.md` if it doesn't exist
2. Fix prompt includes `FIX_CYCLE_LOG_INSTRUCTIONS` — mandatory read-before-fix
3. Agent reads previous cycles, applies a DIFFERENT strategy
4. Agent appends: root cause, files modified, strategy used, result
5. Works across ALL 5 fix types: Mock Data, UI Compliance, E2E, Integrity, Review Recovery

**Milestone Handoff Flow:**
1. BEFORE milestone execution: consumption checklist generated from predecessor interfaces
2. Milestone prompt includes `MILESTONE_HANDOFF_INSTRUCTIONS` — read before coding
3. Code Writer prompt includes handoff awareness — use EXACT contracts, no mock scaffolding
4. AFTER milestone completes: sub-orchestrator fills in actual endpoint details, DB state, env vars
5. Wiring completeness checked: `wired/total` ratio vs gate (default 100%)
6. Architect prompt includes handoff preparation — document every endpoint with exact shapes

### Enabling Tracking Documents

Tracking documents are **enabled by default** (zero-cost when no documents are needed — they only generate when relevant phases execute):

```yaml
# config.yaml
tracking_documents:
  e2e_coverage_matrix: true      # Generate coverage matrix before E2E tests
  fix_cycle_log: true            # Track fix attempts across all fix loops
  milestone_handoff: true        # Generate handoff docs between milestones
  coverage_completeness_gate: 0.8  # 80% of requirements must have E2E tests
  wiring_completeness_gate: 1.0    # 100% of predecessor interfaces must be wired
```

### Config Options

| Option | Default | What it does |
|--------|---------|-------------|
| `e2e_coverage_matrix` | `true` | Generate E2E_COVERAGE_MATRIX.md before E2E testing phase |
| `fix_cycle_log` | `true` | Maintain FIX_CYCLE_LOG.md across all fix loops |
| `milestone_handoff` | `true` | Generate MILESTONE_HANDOFF.md in PRD+ milestone mode |
| `coverage_completeness_gate` | `0.8` | Minimum coverage ratio to pass E2E (0.0-1.0) |
| `wiring_completeness_gate` | `1.0` | Minimum wiring ratio to pass milestone (0.0-1.0) |

### Prompt Injections

| Location | What Was Injected |
|----------|-------------------|
| `BACKEND_E2E_PROMPT` | Generate, fill, and complete E2E_COVERAGE_MATRIX.md |
| `FRONTEND_E2E_PROMPT` | Update matrix with frontend routes and mark as tested |
| `E2E_FIX_PROMPT` | Read matrix + FIX_CYCLE_LOG.md before fixing |
| `CODE_WRITER_PROMPT` | Fix Cycle Awareness + Milestone Handoff Awareness |
| `ARCHITECT_PROMPT` | Milestone Handoff Preparation (document every endpoint with types) |
| `build_milestone_execution_prompt()` | MILESTONE_HANDOFF_INSTRUCTIONS + integration verification |

### CLI Wiring Points

| Integration Point | Where | Behavior |
|-------------------|-------|----------|
| Matrix generation | Before `_run_backend_e2e_tests()` | Generates from REQUIREMENTS.md |
| Coverage stats | After E2E phase completes | Parses matrix, reports stats, checks gate |
| Fix log init | Start of each fix function (5 functions) | Creates FIX_CYCLE_LOG.md if needed |
| Fix log instructions | All 5 fix prompt strings | Injects FIX_CYCLE_LOG_INSTRUCTIONS |
| Consumption checklist | Before milestone execution | Generates from predecessor interfaces |
| Handoff generation | After review recovery, before wiring check | Sub-orchestrator fills interface details |
| Wiring completeness | After handoff generation | Checks wired/total ratio vs gate |
| Artifact tracking | State save calls | Records document paths in STATE.json |

### Design Principles

- **Crash Isolation:** Every integration point wrapped in its own try/except. Tracking document failures NEVER block main execution
- **Backward Compatible:** Projects without `tracking_documents` config section use defaults (all enabled). Disabling everything works exactly as before
- **Best-Effort Extraction:** Requirement parsing is regex-based, not a compiler. ~80% auto-extracted, agents refine the rest
- **Config-Gated:** Each document independently controlled. Disable any without affecting others

### Files Created/Modified

| File | Changes |
|------|---------|
| `src/agent_team/tracking_documents.py` **(NEW)** | 3 dataclasses, 2 prompt constants, 20 functions, 7 regex patterns (~988 lines) |
| `src/agent_team/config.py` | `TrackingDocumentsConfig` dataclass (5 fields) + `AgentTeamConfig` field + `_dict_to_config()` + validation |
| `src/agent_team/agents.py` | 6 prompt injection points (ARCHITECT, CODE_WRITER, milestone execution, integration verification) |
| `src/agent_team/e2e_testing.py` | 3 prompt injections (BACKEND_E2E, FRONTEND_E2E, E2E_FIX) |
| `src/agent_team/cli.py` | Matrix generation/parsing, fix log in 5 functions, handoff generation/verification, `_generate_handoff_details()`, artifact tracking |
| `tests/test_tracking_documents.py` **(NEW)** | 130 tests across 28 test classes (~1573 lines) |

### Files Produced (at runtime)

| File | What it is | Created by | Read by |
|------|-----------|------------|---------|
| `.agent-team/E2E_COVERAGE_MATRIX.md` | Requirement-to-test mapping with checkboxes | CLI (pre-E2E) | E2E agents, fix agents |
| `.agent-team/FIX_CYCLE_LOG.md` | Fix attempt history across all loops | First fix cycle | Subsequent fix cycles |
| `.agent-team/MILESTONE_HANDOFF.md` | Interface contracts per milestone | Post-milestone sub-orchestrator | Next milestone agent |

### Test Suite: 130 Tests

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| `TestGenerateE2ECoverageMatrix` | 13 | API endpoints, frontend routes, workflows, empty, SVC entries, AppTypeInfo |
| `TestParseE2ECoverageMatrix` | 11 | All checked, half, zero, N/A, empty, frontend-only, combined |
| `TestExtractionHelpers` | 4 | API extraction, route extraction, workflow extraction, edge cases |
| `TestInitializeFixCycleLog` | 4 | Empty dir, existing file, header content, Unicode path |
| `TestBuildFixCycleEntry` | 5 | Format, previous cycles, empty failures, special chars, cycle number |
| `TestParseFixCycleLog` | 7 | Multiple cycles, phases, empty, header-only, resolution tracking |
| `TestFixCycleLogConstants` | 3 | Non-empty, key phrases, formattable |
| `TestGenerateMilestoneHandoffEntry` | 4 | Structure, status, all sections, milestone ID |
| `TestGenerateConsumptionChecklist` | 5 | From predecessors, empty, mixed sources, checkboxes, count |
| `TestParseMilestoneHandoff` | 11 | Multiple sections, interfaces, empty tables, malformed, resume |
| `TestParseHandoffInterfaces` | 4 | Specific milestone, missing, empty content, empty ID |
| `TestComputeWiringCompleteness` | 4 | Partial, all, none, missing checklist |
| `TestTrackingDocumentsConfig` | 12 | Defaults, YAML, validation, boundary, collision, backward compat |
| `TestPromptInjections` | 8 | All 6 prompts contain expected references + constant key phrases |
| `TestMilestonePromptHandoffInjection` | 4 | Enabled/disabled, integration verification, config gating |
| `TestFixCycleLogInFixFunctions` | 5 | All 5 fix functions have log injection points |
| `TestE2ECoverageMatrixWiring` | 3 | Generation, parsing, gate enforcement in CLI |
| `TestMilestoneHandoffWiring` | 5 | Generation, checklist, wiring check, config gating, crash isolation |
| `TestStateArtifactTracking` | 2 | Fix log + matrix artifacts in state |
| `TestCrossFeatureIntegration` | 7 | Imports, dataclasses, constants, config collision, backward compat |
| `TestE2ECoverageMatrixRoundTrip` | 3 | Generate → parse empty, with endpoints, mark → parse |
| `TestFixCycleLogRoundTrip` | 1 | Init → build → parse full cycle |
| `TestMilestoneHandoffRoundTrip` | 2 | Generate → parse, full flow with checklist |
| `TestDataclassDefaults` | 4 | All 3 dataclass defaults + list isolation |
| `TestExecutionPosition` | 4 | Matrix before E2E, coverage after, handoff after review, checklist before |
| `TestConfigGating` | 3 | Matrix, fix log, handoff each gated independently |
| `TestCrashIsolation` | 3 | Matrix, fix log, handoff each crash-isolated |
| `TestBackwardCompatibility` | 4 | Disabled config loads, existing prompts valid, core prompt intact |

### Follow-Up: Enum/Status Values in MILESTONE_HANDOFF.md (v4.0.1)

Added a 6th subsection to the MILESTONE_HANDOFF.md template: **Enum/Status Values**. When Milestone 1 creates an entity with `status: "Opened" | "Closed" | "Cancelled"`, subsequent milestones now see the exact valid values — preventing the Bayan Failure #4 where frontend sent `"cancelled"` (lowercase) but backend had `"Cancelled"` (PascalCase).

| Change | File | What |
|--------|------|------|
| New subsection | `tracking_documents.py` | `### Enum/Status Values` table (Entity, Field, Valid Values, DB Type, API String) between Database State and Environment Variables |
| Updated instructions | `tracking_documents.py` | `MILESTONE_HANDOFF_INSTRUCTIONS` now tells agents to study and document enum/status values |
| Updated prompt | `cli.py` | `HANDOFF_GENERATION_PROMPT` STEP 2 + STEP 3 include enum scanning |
| New tests | `test_tracking_documents.py` | 6 new tests in `TestMilestoneHandoffEnumValues` class |

**Test Results: 3082 passed (136 in test_tracking_documents.py), 2 failed (pre-existing), 0 regressions.**

### Failure Pattern Coverage

| Original Failure | Fixed By | Method |
|-----------------|----------|--------|
| Superficial E2E testing ("3 happy paths and done") | E2E_COVERAGE_MATRIX.md | Requirement-to-test mapping, completeness gate, can't declare done with unchecked rows |
| Blind fix loops ("same fix three times") | FIX_CYCLE_LOG.md | Fix history with mandatory read-before-fix, "DO NOT repeat" enforcement |
| Zero cross-milestone wiring ("75 mock methods") | MILESTONE_HANDOFF.md | Interface documentation + consumption checklist + wiring completeness gate |

---

## Database Integrity Upgrades (v5.0) — Cross-Layer Type Consistency

Five upgrades that catch the most expensive database bugs — the ones that fail SILENTLY with no errors, no crashes, just wrong data or missing results. Discovered during the Bayan Tender Management System project (104K LOC enterprise procurement app).

### Why This Matters

| Failure Pattern | What Happens | User Impact |
|----------------|-------------|-------------|
| Dual ORM type mismatch | EF Core stores enum as string, Dapper queries as integer | Queries return zero results — no error |
| Seed data incompleteness | Seeded users have `emailVerified=false`, API filters on `true` | Fresh deployments have invisible users |
| Missing default values | Boolean column has no default, app code assumes non-null | Silent NullReferenceException, generic 500 |
| Status string mismatch | Frontend sends `"cancelled"`, backend has `"Closed"` | Record disappears from all list views |
| Relationship wiring gaps | FK column exists but no navigation property configured | `.Include()` silently returns null |

### Category A: Static Scans (3 functions in quality_checks.py)

Regex-based source file analysis that runs WITHOUT deploying the app. Plugs into the existing quality checks pipeline.

#### Scan 1: Dual Data Access Type Consistency (`run_dual_orm_scan`)

Detects projects using 2+ data access methods (EF Core + Dapper, Prisma + raw SQL, SQLAlchemy + raw queries) with type mismatches on the same columns.

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| DB-001 | Enum type mismatch (ORM stores string, raw SQL compares integer) | Error |
| DB-002 | Boolean type mismatch (ORM bool vs raw SQL 0/1) | Error |
| DB-003 | DateTime format mismatch (ORM datetime vs raw SQL format string) | Error |

**Conditional:** Only runs if 2+ data access methods detected. Skips gracefully for single-ORM projects.

#### Scan 2: Default Value & Nullability Verification (`run_default_value_scan`)

Finds entity/model properties with no explicit default AND nullable properties accessed without null checks.

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| DB-004 | Boolean/enum property without explicit default value | Warning |
| DB-005 | Nullable property accessed without null guard (C#, TypeScript, Python) | Error |

**Framework support:** C# (`{ get; set; }`, `{ get; init; }`, `{ get; private set; }`), Prisma (Boolean, Int, enum, String status fields), Django (`BooleanField()`), SQLAlchemy (`Column(Boolean/Enum)`).

#### Scan 3: ORM Relationship Completeness (`run_relationship_scan`)

Finds FK columns missing navigation properties or relationship configuration.

| Pattern | What It Catches | Severity |
|---------|----------------|----------|
| DB-006 | FK column without navigation property | Warning |
| DB-007 | Navigation property without inverse relationship | Info |
| DB-008 | FK with no relationship configuration at all | Error |

**Framework support:** C# (EF Core), TypeScript (TypeORM), Python (Django, SQLAlchemy).

### Category B: Prompt Policies (2 injections in agents.py)

Requirements injected into agent prompts so they produce correct database code in the FIRST PLACE.

#### Policy 1: Seed Data Completeness

| ID | What It Prevents | Injected Into |
|----|-----------------|---------------|
| SEED-001 | Incomplete seed records (missing fields) | CODE_WRITER, CODE_REVIEWER |
| SEED-002 | Seed records invisible to API query filters | CODE_WRITER, CODE_REVIEWER |
| SEED-003 | Roles without seed accounts | CODE_WRITER, CODE_REVIEWER |

#### Policy 2: Enum/Status Registry

| ID | What It Prevents | Injected Into |
|----|-----------------|---------------|
| ENUM-001 | Entity with status field but no registry entry | ARCHITECT, CODE_WRITER, CODE_REVIEWER |
| ENUM-002 | Frontend status string doesn't match backend enum | ARCHITECT, CODE_WRITER, CODE_REVIEWER |
| ENUM-003 | State transition not defined in registry | ARCHITECT, CODE_WRITER, CODE_REVIEWER |

### Config

```yaml
database_scans:
  dual_orm_scan: true        # Detect ORM vs raw SQL type mismatches
  default_value_scan: true   # Detect missing defaults and unsafe nullable access
  relationship_scan: true    # Detect incomplete relationship configuration
```

All scans enabled by default. Each independently gated. Non-blocking warnings with `_MAX_VIOLATIONS=100` cap.

### Quality Standards

`DATABASE_INTEGRITY_STANDARDS` constant injected into code-writer, code-reviewer, and architect agents. Contains all 8 DB patterns plus Seed Data Completeness and Enum/Status Registry quality rules.

### CLI Wiring

Runs in post-orchestration after PRD reconciliation, before E2E testing. Each scan in its own try/except for crash isolation. Violations trigger `_run_integrity_fix()` with database-specific fix prompts.

### Review & Hardening (v5.0.1 + v5.0.2)

Two exhaustive review rounds found and fixed 24 total issues:

**Review Round 1 (11 fixes):**
- 2 CRITICAL: DB-003 and DB-007 were unimplemented (dead code)
- 2 HIGH: Severity mismatches + missing TypeScript/Python support for some patterns
- 7 MEDIUM/LOW: Regex improvements, dead code removal, import fixes

**Review Round 2 — Exhaustive (13 fixes):**

| Severity | Fix | Impact |
|----------|-----|--------|
| **CRITICAL** | `_run_integrity_fix()` now has 3 database-specific elif branches | Was sending ASSET fix prompt for all DB scans — completely broke fix recovery |
| **HIGH** | DB-005 now supports TypeScript (optional chaining) and Python (Optional[] guard) | Cross-framework nullable detection |
| **HIGH** | `_RE_DB_CSHARP_ENUM_PROP` tightened with suffix filtering (Dto, Service, Controller, Repository) | Eliminates false positive enum detection |
| **HIGH** | `_RE_ENTITY_INDICATOR_PY` uses `Base\s*=\s*declarative_base` instead of bare `\bBase\b` | No more false positives on generic Base classes |
| **MEDIUM** | Prisma enum types now detected by default value scan | Broader Prisma coverage |
| **MEDIUM** | C# bool regex handles `init;`, `private set;`, `protected set;` | Modern C# 9+ support |
| **MEDIUM** | TypeScript raw SQL detection skips comment lines | Fewer false positives |
| **MEDIUM** | DB-005 null check window increased from 200 to 500 characters | Fewer false positives on distant null guards |
| **MEDIUM** | Navigation property regex tightened | Better nav vs non-nav distinction |
| **LOW** | Prisma String type scanned for status-like fields | Catches `status String` without `@default` |
| **LOW** | TypeORM property name extraction improved | More reliable decorator-to-property mapping |
| **LOW** | `_run_integrity_fix()` docstring lists all 5 scan types | Accurate documentation |

### Files Created/Modified

| File | Changes |
|------|---------|
| `src/agent_team/quality_checks.py` | 3 scan functions, 20+ regex patterns, 5+ helper functions (~700 lines added) |
| `src/agent_team/config.py` | `DatabaseScanConfig` dataclass + field + loader |
| `src/agent_team/cli.py` | 3 scan wiring blocks + 3 database-specific fix prompts in `_run_integrity_fix()` |
| `src/agent_team/agents.py` | Seed Data + Enum Registry policies in ARCHITECT, CODE_WRITER, CODE_REVIEWER |
| `src/agent_team/code_quality_standards.py` | `DATABASE_INTEGRITY_STANDARDS` constant + agent mapping |
| `tests/test_database_scans.py` **(NEW)** | 135 scan tests |
| `tests/test_database_wiring.py` **(NEW)** | 105 wiring tests |
| `tests/test_database_integrity_specialized.py` **(NEW)** | 105 specialized tests (realistic fixtures, edge cases) |
| `tests/test_database_fix_verification.py` **(NEW)** | 64 fix verification tests |

### Test Results

**3482 tests passed (409 database-specific), 2 failed (pre-existing test_mcp_servers.py), 0 regressions.**

### Bayan Failure Coverage (Final Verification)

| Bayan Failure | Fixed By | Method | Status |
|--------------|----------|--------|--------|
| Dual ORM type mismatch (EF Core + Dapper) | DB-001, DB-002, DB-003 | Static scan cross-references ORM types vs raw SQL | VERIFIED |
| Seed data incompleteness (invisible users) | SEED-001, SEED-002, SEED-003 | Prompt policy enforces complete, queryable seed data | VERIFIED |
| Missing default values (null crashes) | DB-004, DB-005 | Static scan detects missing defaults + unsafe nullable access | VERIFIED |
| Status string mismatches (disappeared records) | ENUM-001, ENUM-002, ENUM-003 | Prompt policy enforces status registry across all layers | VERIFIED |
| Relationship wiring gaps (null navigation) | DB-006, DB-007, DB-008 | Static scan detects FK without nav, nav without inverse, FK without config | VERIFIED |
