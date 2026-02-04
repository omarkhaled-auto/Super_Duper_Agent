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

70 code quality anti-patterns are **always injected** into relevant agents — no configuration needed:

| Agent | Standards Injected | Anti-Patterns |
|-------|-------------------|---------------|
| `code_writer` | Frontend + Backend | 30 (FRONT-001→015, BACK-001→015) |
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
