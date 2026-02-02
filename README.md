# Agent Team

Convergence-driven multi-agent orchestration system built on the [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-agent-sdk). Takes any task — from a one-line bug fix to a full PRD — and drives it to verified completion using fleets of specialized AI agents.

---

## Quick Start (TL;DR)

```bash
git clone https://github.com/omarkhaled-auto/Super_Duper_Agent.git
cd Super_Duper_Agent
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...        # required
export FIRECRAWL_API_KEY=fc-...            # optional, enables web research
```

**5 commands that cover 90% of use cases:**

```bash
agent-team                                           # Interactive — interview first, then build
agent-team "quick fix: button doesn't submit"        # Quick bug fix (auto-detected)
agent-team "thoroughly add JWT auth"                  # Standard feature (auto-detected thorough)
agent-team --prd spec.md                              # Full app from PRD (auto exhaustive)
agent-team "redesign UI" --design-ref https://stripe.com  # Match a reference design
```

**Manage your workspace:**

```bash
agent-team init                                      # Generate a starter config.yaml
agent-team status                                    # Show .agent-team/ contents and run state
agent-team clean                                     # Delete .agent-team/ directory (with confirmation)
agent-team guide                                     # Print built-in usage guide
agent-team --dry-run "add auth"                      # Preview depth, agents, config — no API calls
```

**Cheat sheet — pick a depth:**

| Depth | Trigger | Agents | Use when |
|-------|---------|--------|----------|
| Quick | `"quick"`, `"fast"`, `"simple"` in task | 1-2 | Typo, one-file fix |
| Standard | (default) | 2-5 | Normal feature, bug |
| Thorough | `"thorough"`, `"refactor"`, `"redesign"`, `"deep"` in task | 3-8 | Multi-file feature, refactor |
| Exhaustive | `--prd`, `"exhaustive"`, `"migrate"`, `"comprehensive"` in task | 5-10 | Full app, major system |

**End the interview** by saying: `"I'm done"`, `"let's go"`, `"start building"`, `"ship it"`, `"lgtm"`, or `"proceed"`. The system will show a summary and ask you to confirm before finalizing.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
  - [Task Type A: Quick Bug Fix](#task-type-a-quick-bug-fix)
  - [Task Type B: Standard Feature](#task-type-b-standard-feature)
  - [Task Type C: Thorough Multi-File Feature](#task-type-c-thorough-multi-file-feature)
  - [Task Type D: Full App Build from PRD](#task-type-d-full-app-build-from-prd)
  - [Task Type E: Using Design References](#task-type-e-using-design-references)
  - [Task Type F: Resuming with a Previous Interview](#task-type-f-resuming-with-a-previous-interview)
- [The Interview Phase](#the-interview-phase)
- [Constraint Extraction](#constraint-extraction)
- [User Interventions](#user-interventions)
- [What It Produces](#what-it-produces)
- [Convergence Loop](#convergence-loop)
- [Design Reference](#design-reference)
- [Configuration](#configuration)
  - [Config Recipes](#config-recipes)
- [CLI Reference](#cli-reference)
  - [Subcommands](#subcommands)
- [Practical Workflow Examples](#practical-workflow-examples)
- [Depth Levels — Deep Dive](#depth-levels--deep-dive)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [Architecture](#architecture)
- [License](#license)

---

## How It Works

Agent Team runs a **convergence loop**: agents write code, reviewers try to break it, debuggers fix what's broken, and the loop repeats until every requirement passes adversarial review. Nothing ships half-done.

```
Interview → Codebase Map → Plan → Research → Architect → Contract → Schedule → Code → Review → Debug → Verify → Done
                                                                                 ↑                     ↓
                                                                                 └──── (loop until all pass) ──┘
```

### The Pipeline

| Phase | Agent | What It Does |
|-------|-------|-------------|
| 0 | **Interviewer** | Talks to you through 3 phases (Discovery → Refinement → Ready), writes `.agent-team/INTERVIEW.md` |
| 0.25 | **Constraint Extractor** | Scans your task and interview for prohibitions, requirements, and scope limits — injects them into every agent |
| 0.5 | **Codebase Map** | Analyzes project structure, detects languages/frameworks, maps dependencies |
| 0.75 | **Contract Loading** | Loads `CONTRACTS.json` for interface verification (if enabled) |
| 1 | **Planner** | Explores codebase, creates `.agent-team/REQUIREMENTS.md` with checklist |
| 2 | **Researcher** | Queries docs (Context7) and web (Firecrawl), scrapes design references, adds findings to requirements |
| 3 | **Architect** | Designs solution, file ownership map, wiring map, interface contracts |
| 4 | **Task Assigner** | Decomposes requirements into atomic tasks in `.agent-team/TASKS.md` |
| 4.5 | **Smart Scheduler** | Builds dependency DAG, detects file conflicts, computes parallel execution waves |
| 5 | **Code Writer** | Implements assigned tasks (non-overlapping files, reads from TASKS.md) |
| 6 | **Code Reviewer** | Adversarial review — tries to break everything, marks items pass/fail |
| 7 | **Debugger** | Fixes specific issues flagged by reviewers |
| 8 | **Test Runner** | Writes and runs tests for each requirement |
| 9 | **Security Auditor** | OWASP checks, dependency audit, credential scanning |
| 10 | **Progressive Verification** | 4-phase pipeline: contracts → lint → type check → tests |

Steps 5-7 repeat in a **convergence loop** until every `- [ ]` in REQUIREMENTS.md becomes `- [x]`.

### Fleet Scaling

Agents deploy in parallel fleets. Fleet size scales with task complexity:

| Depth | Planning | Research | Architecture | Coding | Review | Testing |
|-------|----------|----------|-------------|--------|--------|---------|
| Quick | 1-2 | 0-1 | 0-1 | 1 | 1-2 | 1 |
| Standard | 3-5 | 2-3 | 1-2 | 2-3 | 2-3 | 1-2 |
| Thorough | 5-8 | 3-5 | 2-3 | 3-6 | 3-5 | 2-3 |
| Exhaustive | 8-10 | 5-8 | 3-4 | 5-10 | 5-8 | 3-5 |

Depth is auto-detected from keywords in your task ("quick fix" → Quick, "thorough review" → Thorough) or set explicitly with `--depth`.

---

## Installation

### Prerequisites

- **Python 3.10+** — check with `python --version`
- **Node.js** — needed for MCP servers (Context7, Firecrawl). Check with `node --version`
- **Anthropic API key** — get one at https://console.anthropic.com/

### Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/omarkhaled-auto/Super_Duper_Agent.git
cd Super_Duper_Agent

# 2. Install the package
pip install -e .

# 3. Set your Anthropic API key (REQUIRED)
#    Linux/macOS:
export ANTHROPIC_API_KEY=sk-ant-...
#    Windows (PowerShell):
$env:ANTHROPIC_API_KEY="sk-ant-..."
#    Windows (cmd):
set ANTHROPIC_API_KEY=sk-ant-...

# 4. (Optional) Set Firecrawl key for web research + design reference scraping
export FIRECRAWL_API_KEY=fc-...

# 5. Verify
agent-team --version   # should print 0.1.0
```

### Persistent keys with .env

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
```

Load before running:

```bash
# Linux/macOS
export $(grep -v '^#' .env | xargs)

# Windows (PowerShell)
Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#][^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process") } }
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `FIRECRAWL_API_KEY` | No | Firecrawl MCP server for web research + design scraping |

---

## Usage Guide

### Task Type A: Quick Bug Fix

**Best for:** One-file fixes, typos, broken imports, CSS tweaks.

```bash
agent-team "quick fix: the submit button on /login calls the wrong API endpoint"
```

What happens:
1. Interview is skipped (task is self-explanatory at this depth)
2. 1-2 planners scan the codebase, write REQUIREMENTS.md
3. 1 code writer fixes the issue
4. 1-2 reviewers verify the fix
5. Done

**Tips:**
- Use `--no-interview` if you already know exactly what's wrong
- Add `--cwd /path/to/project` if you're not in the project directory
- The word "quick" or "fast" in your task auto-selects Quick depth

```bash
# Equivalent explicit version
agent-team --no-interview --depth quick --cwd ./my-app "fix the login button"
```

### Task Type B: Standard Feature

**Best for:** Adding a component, new API endpoint, small integration, single-module work.

```bash
agent-team "add user profile editing with avatar upload to the Express API"
```

What happens:
1. **Interview** — the interviewer asks 3-5 clarifying questions (boundaries, error handling, validation). Answer them, then say `I'm done` or `let's go`
2. **Plan** — planners explore your codebase and create REQUIREMENTS.md
3. **Research** — researchers look up library docs (e.g., multer for file uploads) via Context7
4. **Architecture** — architect designs the solution, creates a wiring map
5. **Task assignment** — decomposes into atomic TASKS.md entries
6. **Convergence loop** — code, review, debug, repeated until all items pass
7. **Testing + security audit**

**Tips:**
- Let the interview run. 2-3 exchanges gives the agents much better context
- Standard depth (default) is right for most features
- If working with an unfamiliar library, Firecrawl + Context7 help a lot — make sure both keys are set

### Task Type C: Thorough Multi-File Feature

**Best for:** Features touching 5-20 files, cross-cutting concerns, refactors, integrations.

```bash
agent-team "thoroughly refactor the authentication system to use JWT with refresh tokens"
```

Or be explicit:

```bash
agent-team --depth thorough "refactor auth to JWT with refresh tokens"
```

What happens:
- Same pipeline as Standard, but with **3-8 agents per phase**
- Multiple code writers work in parallel on non-overlapping files
- Multiple reviewers independently try to break the implementation
- The convergence loop runs more iterations with more thorough reviews

**Tips:**
- The word "thorough", "deep", "detailed", or "carefully" in your task auto-selects this depth
- Use `--agents 15` to override the total agent count if you want more
- Use `-v` (verbose) to see which tools each agent is calling — useful for debugging stalls
- Expect 3+ convergence cycles; the adversarial reviewers are strict

### Task Type D: Full App Build from PRD

**Best for:** Greenfield apps, major systems, 20+ files, anything with a full spec.

There are two paths:

**Path 1: You already have a PRD file**

```bash
agent-team --prd product-spec.md
```

This automatically forces **exhaustive** depth. The orchestrator reads the PRD, creates a MASTER_PLAN.md with milestones, and executes each milestone through the full pipeline.

**Path 2: Build the PRD through the interview**

```bash
agent-team
```

Just run with no arguments. The interviewer will ask 15-20 deep questions (target users, data model, API design, integrations, deployment). When it detects COMPLEX scope, it writes a full PRD to `.agent-team/INTERVIEW.md` and the orchestrator receives exhaustive depth.

**Tips:**
- For the interview: give detailed answers. The more context you provide, the better the requirements document
- Say "I'm done" only when all your requirements are captured
- If the interview produced scope COMPLEX, the system automatically forces exhaustive depth
- If you have design inspiration: `--design-ref https://stripe.com https://linear.app`
- The Firecrawl key is especially valuable here — researchers will scrape library docs, design references, and competitive examples

### Task Type E: Using Design References

**Best for:** Any frontend/UI task where you want to match an existing design aesthetic.

```bash
# Single reference
agent-team "build a SaaS landing page" --design-ref https://stripe.com

# Multiple references
agent-team --prd spec.md --design-ref https://stripe.com https://linear.app

# Via config.yaml (persistent) — see Configuration section below
```

What the researcher extracts:
- **Colors** — hex values for primary, secondary, accent, backgrounds
- **Typography** — font families, sizes, weights, line heights
- **Spacing** — padding, margin patterns
- **Component patterns** — nav structure, card layouts, button styles, form patterns
- **Screenshots** — cloud-hosted URLs of key pages

All findings go into REQUIREMENTS.md as `DESIGN-xxx` checklist items that code writers implement and reviewers verify. If no URL is provided, this feature is entirely skipped at zero cost.

### Task Type F: Resuming with a Previous Interview

If you ran an interview in a previous session:

```bash
agent-team --interview-doc .agent-team/INTERVIEW.md "build the dashboard"
```

This skips the live interview and feeds the existing document directly to the orchestrator. The scope is detected from the `Scope:` header in the document (SIMPLE/MEDIUM/COMPLEX).

---

## The Interview Phase

The interview is **Phase 0** — it runs before any agents deploy. A good interview saves convergence cycles downstream.

### Three Phases

The interview progresses through structured phases based on exchange count:

| Phase | When | What happens |
|-------|------|-------------|
| **Discovery** | First half of min exchanges | Interviewer explores your codebase with tools, asks clarifying questions, shows "My Current Understanding" |
| **Refinement** | Second half of min exchanges | Deepens understanding, proposes approaches, shows "What I Propose" and "Remaining Questions" |
| **Ready** | After min exchanges reached | Can finalize — shows "Final Understanding" and "Proposed Approach" |

The system enforces a minimum number of exchanges (default: 3) before allowing finalization, so the interviewer always explores your codebase before writing the document.

### Starting

```bash
agent-team                                     # Full interactive (no seed)
agent-team "build a task management app"       # With a task seed
agent-team -i "build a task management app"    # Force interactive with seed
```

### During the interview

- **Answer specifically.** "A login page" is worse than "Email + password login, no OAuth, redirect to /dashboard on success, show inline errors on failure."
- **Mention your stack.** "It's a Next.js 14 app with Supabase" gives the interviewer real context to explore.
- **Let it explore your codebase.** If you're in an existing project directory, the interviewer uses Glob/Read/Grep to ask informed questions about your actual code.
- **Don't rush.** 5-10 exchanges for a medium feature, 15-20 for a complex app. The document quality directly affects everything downstream.
- **State constraints clearly.** Say things like "never change the database schema" or "must use the existing auth system" — these get extracted and enforced across all agents (see [Constraint Extraction](#constraint-extraction)).

### Ending the interview

Say any of these phrases (case-insensitive, punctuation ignored):

> `I'm done` · `im done` · `i am done` · `let's go` · `lets go` · `start building` · `start coding` · `proceed` · `build it` · `go ahead` · `that's it` · `thats it` · `that's all` · `thats all` · `begin` · `execute` · `run it` · `ship it` · `do it` · `let's start` · `lets start` · `good to go` · `ready` · `looks good` · `lgtm`

**Negation is handled:** "I'm **not** done" and "don't proceed yet" will NOT end the interview.

**Three-tier exit handling:**

1. **Before minimum exchanges** — the system redirects you back with a summary of understanding gaps and focused questions, so nothing gets finalized too early.
2. **After minimum exchanges** — the system shows a full summary of everything discussed and asks you to confirm ("Does this capture everything? Say **yes** to finalize").
3. **After confirmation** — writes the final INTERVIEW.md document.

### Skipping the interview

```bash
agent-team --no-interview "fix the login bug"               # Skip entirely
agent-team --interview-doc .agent-team/INTERVIEW.md         # Use existing document
```

---

## Constraint Extraction

When you write things like "never change the database schema" or "must use TypeScript" in your task or during the interview, the system automatically picks them up and injects them into every agent's prompt.

### What gets extracted

| Type | Trigger words | Example |
|------|--------------|---------|
| **Prohibition** | "never", "don't", "zero", "must not" | "Don't modify the API contract" |
| **Requirement** | "must", "always", "required" | "Must use the existing auth middleware" |
| **Scope limit** | "only", "just the", "limited to" | "Only change files in src/components/" |

Constraints written in ALL CAPS or with emphasis words like "absolutely" or "critical" get higher priority. The system deduplicates across task text and interview document.

### How to use

Just write naturally — say "NEVER touch the database migrations" in your task or during the interview, and every agent will see it as a high-priority prohibition.

---

## User Interventions

If you need to redirect the agents mid-run, type a message prefixed with `!!` in the terminal:

```
!! stop changing the CSS, focus on the API endpoints
```

The orchestrator will pause new agent deployments, read your intervention, adjust the plan, and resume. This lets you course-correct without restarting.

---

## What It Produces

Agent Team creates a `.agent-team/` directory in your project:

| File | Purpose |
|------|---------|
| `INTERVIEW.md` | Structured requirements from the interview phase |
| `INTERVIEW_BACKUP.json` | JSON transcript backup of the interview |
| `REQUIREMENTS.md` | Master checklist — the single source of truth |
| `TASKS.md` | Atomic task breakdown with dependency graph |
| `MASTER_PLAN.md` | Milestone plan (PRD mode only — name is configurable) |
| `CONTRACTS.json` | Interface contracts for module exports and wiring |
| `VERIFICATION.md` | Progressive verification summary (health status per task) |
| `STATE.json` | Run state snapshot — saved on interrupt for potential resume |

### Requirements Checklist

Every requirement gets tracked with review cycles:

```markdown
## Requirements Checklist

### Functional Requirements
- [x] REQ-001: User can log in with email and password (review_cycles: 2)
- [ ] REQ-002: Password reset sends email within 30 seconds (review_cycles: 1)

### Technical Requirements
- [x] TECH-001: All endpoints return proper HTTP status codes (review_cycles: 1)

### Wiring Requirements
- [x] WIRE-001: Auth middleware wired to /api routes via Express.use() (review_cycles: 1)

### Design Requirements
- [x] DESIGN-001: Use primary color #635bff for headings and CTAs (review_cycles: 1)

## Review Log
| Cycle | Reviewer | Item | Verdict | Issues Found |
|-------|----------|------|---------|-------------|
| 1 | reviewer-1 | REQ-001 | FAIL | Missing input validation on email field |
| 2 | reviewer-2 | REQ-001 | PASS | None |
| 1 | reviewer-1 | REQ-002 | FAIL | Email service not connected |
```

The task is **complete only when every `[ ]` becomes `[x]`**.

---

## Convergence Loop

The core mechanism that ensures quality:

```
1. Code Writers implement from TASKS.md
2. Reviewers adversarially verify against REQUIREMENTS.md
3. If items fail:
   a. Failures < 3 cycles → Debuggers fix specific issues → back to step 1
   b. Failures >= 3 cycles → ESCALATION: re-plan, split requirement, retry
   c. Escalation depth exceeded → asks YOU for guidance
4. If all items pass → Testing Fleet → Security Audit → Done
```

### Convergence Gates

Four hard rules are enforced during the convergence loop to prevent quality shortcuts:

| Gate | Rule |
|------|------|
| **Review authority** | Only code-reviewer and test-runner agents can mark checklist items `[x]`. Coders, debuggers, and architects cannot. |
| **Mandatory re-review** | After every debug fix, a reviewer must verify the fix. Debug → Re-Review is non-negotiable. |
| **Cycle reporting** | After every review cycle, the orchestrator reports "Cycle N: X/Y requirements complete (Z%)". |
| **Depth ≠ thoroughness** | The depth level controls fleet size, not review quality. Even at Quick depth, reviews are thorough. |

### Escalation Protocol

If a requirement fails review 3+ times (configurable):
1. Sent back to Planning + Research fleet for re-analysis
2. Requirement is rewritten or split into sub-tasks
3. Sub-tasks go through the full pipeline
4. Max escalation depth: 2 levels (configurable)
5. If exceeded: the system asks the user for guidance

---

## Design Reference

Provide a reference website URL to have the Researcher agent scrape its design system (colors, typography, spacing, component patterns) and write the findings into REQUIREMENTS.md. Downstream agents then use those design tokens as constraints.

### How to Provide References

References can come from three sources (all are merged and deduplicated):

1. **CLI flag**: `--design-ref https://stripe.com https://linear.app`
2. **config.yaml**: set `design_reference.urls`
3. **Interview**: the interviewer asks about design inspiration for frontend tasks

### What Gets Extracted

The Researcher uses Firecrawl to scrape reference sites at three depth levels:

| Depth | What's Extracted |
|-------|-----------------|
| `branding` | Color palette, typography, spacing, component styles |
| `screenshots` | Branding + cloud-hosted screenshot URLs for each page |
| `full` (default) | Branding + screenshots + component pattern analysis (nav, cards, forms, footer) |

### Data Flow

```
config.yaml urls + --design-ref CLI + interview URLs
    → deduplicated in CLI
    → injected into orchestrator prompt
    → orchestrator assigns researcher(s) to design analysis
    → researcher scrapes via Firecrawl (branding, screenshots, components)
    → writes to REQUIREMENTS.md ## Design Reference
    → architect defines design tokens from extracted data
    → code writer applies colors, fonts, component patterns
    → reviewer verifies DESIGN-xxx items like any other requirement
```

---

## Configuration

Create `config.yaml` in your project root or `~/.agent-team/config.yaml`, or run `agent-team init` to generate a starter config.

```yaml
orchestrator:
  model: "opus"           # Model for the orchestrator
  max_turns: 500          # Max agentic turns per session
  max_budget_usd: null    # Cost cap — warns at 80%, stops at 100% (null = unlimited)
  permission_mode: "acceptEdits"

depth:
  default: "standard"     # Default depth when no keywords detected
  auto_detect: true       # Detect depth from task keywords
  keyword_map:
    quick: ["quick", "fast", "simple"]
    thorough: ["thorough", "carefully", "deep", "detailed", "refactor",
               "redesign", "restyle", "rearchitect", "overhaul",
               "rewrite", "restructure", "revamp", "modernize"]
    exhaustive: ["exhaustive", "comprehensive", "complete",
                 "migrate", "migration", "replatform", "entire", "every", "whole"]

convergence:
  max_cycles: 10                    # Max convergence loop iterations
  escalation_threshold: 3           # Failures before escalation
  max_escalation_depth: 2           # Max re-planning levels
  requirements_dir: ".agent-team"
  requirements_file: "REQUIREMENTS.md"
  master_plan_file: "MASTER_PLAN.md"  # Customizable — change to any filename

interview:
  enabled: true                        # Run interview phase
  model: "opus"                        # Model for interviewer
  max_exchanges: 50                    # Max interview exchanges
  min_exchanges: 3                     # Minimum before allowing finalization
  require_understanding_summary: true  # Force structured "My Understanding" sections
  require_codebase_exploration: true   # Force tool use (Glob/Read/Grep) in Discovery phase

design_reference:
  urls: []                # Reference website URLs for design inspiration
  depth: "full"           # "branding" | "screenshots" | "full"
  max_pages_per_site: 5   # Max pages to scrape per reference URL

codebase_map:
  enabled: true           # Analyze project structure before planning
  max_files: 5000         # Max files to scan
  max_file_size_kb: 50    # Max file size (KB) for Python files
  max_file_size_kb_ts: 100  # Max file size (KB) for TypeScript/JavaScript files
  exclude_patterns: []    # Additional directories to exclude (merged with built-in defaults)
  timeout_seconds: 30.0   # Timeout for map generation

scheduler:
  enabled: true                              # Enable smart task scheduling
  max_parallel_tasks: 5                      # Max tasks per execution wave
  conflict_strategy: "artificial-dependency"  # How to resolve file conflicts between parallel tasks
  enable_context_scoping: true               # Compute per-task file context
  enable_critical_path: true                 # Compute critical path analysis

verification:
  enabled: true                             # Enable progressive verification
  blocking: true                            # true = failures are hard stops, false = failures become warnings
  run_lint: true                            # Run lint phase
  run_type_check: true                      # Run type-check phase
  run_tests: true                           # Run test phase
  contract_file: ".agent-team/CONTRACTS.json"
  verification_file: ".agent-team/VERIFICATION.md"

agents:
  planner:
    model: "opus"
    enabled: true
  researcher:
    model: "opus"
    enabled: true
  architect:
    model: "opus"
    enabled: true
  task_assigner:
    model: "opus"
    enabled: true
  code_writer:
    model: "opus"
    enabled: true
  code_reviewer:
    model: "opus"
    enabled: true
  test_runner:
    model: "opus"
    enabled: true
  security_auditor:
    model: "opus"
    enabled: true
  debugger:
    model: "opus"
    enabled: true

mcp_servers:
  firecrawl:
    enabled: true         # Web scraping/search (requires FIRECRAWL_API_KEY)
  context7:
    enabled: true         # Library documentation (no key required)

display:
  show_cost: true
  show_tools: true
  show_fleet_composition: true    # Show agent fleet details during deployment
  show_convergence_status: true   # Show convergence cycle progress
  verbose: false
```

### Config Recipes

**Cost-conscious (small tasks):**
```yaml
orchestrator:
  max_budget_usd: 5.0     # Hard cap at $5
depth:
  default: "quick"
convergence:
  max_cycles: 3
agents:
  security_auditor:
    enabled: false
```

**Maximum quality (production features):**
```yaml
depth:
  default: "thorough"
convergence:
  max_cycles: 15
  escalation_threshold: 2
interview:
  max_exchanges: 100
  min_exchanges: 5         # Force deeper exploration
verification:
  blocking: true           # Failures are hard stops
```

**Non-blocking verification (move fast, fix later):**
```yaml
verification:
  blocking: false          # Failures become warnings instead of hard stops
```

**Mixed models (save cost on sub-agents):**
```yaml
orchestrator:
  model: "opus"
agents:
  planner:
    model: "sonnet"
  researcher:
    model: "sonnet"
  code_writer:
    model: "opus"       # keep opus for coding
  code_reviewer:
    model: "opus"       # keep opus for adversarial review
  test_runner:
    model: "sonnet"
  security_auditor:
    model: "sonnet"
  debugger:
    model: "opus"
```

**Backend-only (no design scraping):**
```yaml
mcp_servers:
  firecrawl:
    enabled: false
design_reference:
  urls: []
```

---

## CLI Reference

```
agent-team [TASK] [OPTIONS]
agent-team <subcommand>

Positional:
  TASK                    Task description (omit for interactive mode)

Subcommands:
  init                    Generate a starter config.yaml in the current directory
  status                  Show .agent-team/ contents and saved run state
  resume                  Resume from a saved STATE.json (experimental)
  clean                   Delete .agent-team/ directory (asks for confirmation)
  guide                   Print the built-in usage guide

Options:
  --prd FILE              Path to a PRD file for full application build
  --depth LEVEL           Override depth: quick | standard | thorough | exhaustive
  --agents N              Override total agent count (distributed across phases)
  --model MODEL           Override model (default: opus)
  --max-turns N           Override max agentic turns (default: 500)
  --config FILE           Path to config.yaml
  --cwd DIR               Working directory (default: current directory)
  --no-interview          Skip the interview phase
  --interview-doc FILE    Use a pre-existing interview document (skips live interview)
  --design-ref URL [URL]  Reference website URL(s) for design inspiration
  --dry-run               Show task analysis (depth, agents, config) without making API calls
  --progressive           Enable progressive verification pipeline (default)
  --no-progressive        Disable progressive verification
  --map-only              Run codebase map analysis and exit
  --no-map                Skip codebase map analysis
  -i, --interactive       Force interactive mode
  -v, --verbose           Show all tool calls and agent details
  --version               Show version
```

Note: `--progressive`/`--no-progressive` and `--map-only`/`--no-map` are mutually exclusive pairs.

### Subcommands

Run these without a task:

```bash
agent-team init       # Creates config.yaml with documented defaults
agent-team status     # Lists files in .agent-team/, shows run ID and phase if STATE.json exists
agent-team clean      # Deletes .agent-team/ — asks "Delete .agent-team/ directory? [y/N]" first
agent-team guide      # Prints a quick reference of all commands and flags
```

### Common patterns

```bash
# ---- Modes ----
agent-team                                    # Interactive (interview → orchestrate)
agent-team "task"                             # Single-shot (auto-detect depth)
agent-team -i "task"                          # Force interactive with seed
agent-team --prd spec.md                      # PRD mode (exhaustive)
agent-team --dry-run "task"                   # Preview what would happen (no API calls)

# ---- Depth control ----
agent-team --depth quick "task"               # Explicit quick
agent-team "quick fix for the typo"           # Auto-detected quick
agent-team "refactor the auth module"         # Auto-detected thorough (refactor keyword)
agent-team "migrate to PostgreSQL"            # Auto-detected exhaustive (migrate keyword)
agent-team --depth exhaustive "task"          # Explicit exhaustive

# ---- Agent control ----
agent-team --agents 20 "task"                 # Override total agents
agent-team "use 10 agents for this"           # Detected from task text
agent-team "deploy 5 agents to fix auth"      # Also detected

# ---- Interview control ----
agent-team --no-interview "task"              # Skip interview
agent-team --interview-doc doc.md "task"      # Use existing document

# ---- Design references ----
agent-team --design-ref https://stripe.com                      # Single
agent-team --design-ref https://stripe.com https://linear.app   # Multiple

# ---- Project control ----
agent-team --cwd /path/to/project "task"      # Set working directory
agent-team --config custom.yaml "task"        # Custom config file

# ---- Workspace management ----
agent-team init                               # Generate starter config.yaml
agent-team status                             # Check .agent-team/ state
agent-team clean                              # Delete .agent-team/ directory

# ---- Output control ----
agent-team -v "task"                          # Verbose (show tool calls)
```

---

## Practical Workflow Examples

### Fix a bug in an existing project

```bash
cd my-project
agent-team --no-interview "quick fix: the /api/users endpoint returns 500 when email contains a plus sign"
```

### Add a feature with interview

```bash
cd my-project
agent-team "add Stripe subscription billing to the Express backend"
# Interview: 5-8 exchanges about plans, webhooks, trial periods
# Say: "I'm done"
# Agents build it
```

### Build a full app from scratch

```bash
mkdir new-saas && cd new-saas
agent-team
# Interview: 15-20 exchanges building a full PRD
# Interviewer detects COMPLEX scope → exhaustive depth
# Say: "let's go"
# Full pipeline: plan → research → architect → code → review → debug → test
```

### Redesign UI to match a reference

```bash
cd my-frontend
agent-team "redesign the dashboard to look like Linear" \
  --design-ref https://linear.app \
  --depth thorough
```

### Run from a PRD you wrote

```bash
agent-team --prd docs/product-spec.md --design-ref https://stripe.com
# Exhaustive depth auto-activated
# MASTER_PLAN.md created with milestones
# Each milestone goes through the full convergence loop
```

### Cost-effective quick iterations

```bash
# First pass: quick depth, no interview
agent-team --no-interview --depth quick "add a logout button to the navbar"

# Review what it built, then refine with more depth
agent-team --no-interview --depth standard "fix the logout button: it should clear localStorage and redirect to /login"
```

---

## Depth Levels — Deep Dive

Depth is the single most important parameter. It controls how many agents deploy and how thorough the process is.

### How depth is determined (precedence order)

1. **`--depth` flag** — explicit, always wins
2. **`--prd` flag** — forces exhaustive automatically
3. **Interview scope COMPLEX** — forces exhaustive automatically
4. **Auto-detected from keywords** — keywords in your task text
5. **Config default** — `standard` unless changed in config.yaml

### Auto-detection keywords

| Keyword in your task | Maps to |
|---------------------|---------|
| `quick`, `fast`, `simple` | Quick |
| `thorough`, `carefully`, `deep`, `detailed`, `refactor`, `redesign`, `restyle`, `rearchitect`, `overhaul`, `rewrite`, `restructure`, `revamp`, `modernize` | Thorough |
| `exhaustive`, `comprehensive`, `complete`, `migrate`, `migration`, `replatform`, `entire`, `every`, `whole` | Exhaustive |

When multiple keywords appear, the **most intensive** depth wins. "Quick but comprehensive" resolves to **Exhaustive**.

Word-boundary matching prevents false positives — "adjustment" does NOT match "just".

The system now shows you exactly which keywords were matched and why a depth was chosen (visible in terminal output).

### What each depth level does

| | Quick | Standard | Thorough | Exhaustive |
|---|---|---|---|---|
| **Interview** | Skipped or 2-3 Q's | 3-5 questions | 5-10 questions | 15-20 questions |
| **Planners** | 1-2 | 3-5 | 5-8 | 8-10 |
| **Researchers** | 0-1 | 2-3 | 3-5 | 5-8 |
| **Code writers** | 1 | 2-3 | 3-6 | 5-10 |
| **Reviewers** | 1-2 | 2-3 | 3-5 | 5-8 |
| **Convergence cycles** | 1-2 typical | 2-4 typical | 3-6 typical | 5-10 typical |
| **Cost** | $ | $$ | $$$ | $$$$ |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Error: ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY=sk-ant-...` or add to `.env` |
| `Configuration error: ...` | Check your config.yaml — the system now shows clean error messages for invalid configs (e.g., `min_exchanges > max_exchanges`) |
| `[warn] FIRECRAWL_API_KEY not set` | Set it or disable firecrawl in config. Web research still works via Context7 |
| Interview won't let me finish | You haven't reached the minimum exchange count (default: 3). Answer a few more questions, then say "I'm done" |
| Interview exits too early | Shouldn't happen anymore — the system now asks for confirmation before finalizing. If it still does, check `min_exchanges` in config |
| Convergence loop stuck | Check `.agent-team/REQUIREMENTS.md` Review Log for what keeps failing. Consider reducing `escalation_threshold` |
| Too expensive | Set `max_budget_usd` in config, use `--depth quick`, disable unused agents, or use `sonnet` model for sub-agents |
| Want to preview before spending tokens | Use `--dry-run` to see depth, agents, and config without making any API calls |
| Need to redirect agents mid-run | Type `!! your message` in the terminal to send a priority intervention |
| Interrupted mid-run | State is auto-saved on Ctrl+C. Run `agent-team status` to see saved state |
| `agent-team` command not found | Run `pip install -e .` again, or use `python -m agent_team` instead |
| Wrong project directory | Use `--cwd /absolute/path/to/project` |

---

## Testing

The test suite covers every module with unit, integration, and end-to-end tests.

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit + integration tests (no API keys needed)
pytest tests/ -v --tb=short

# Run E2E tests (requires real API keys in environment)
pytest tests/ -v --run-e2e

# Count collected tests
pytest tests/ --co -q
```

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures, --run-e2e plugin
├── test_init.py          # Package exports and version (3 tests)
├── test_config.py        # Dataclass defaults, detect_depth, get_agent_counts,
│                         #   _deep_merge, _dict_to_config, enum validation,
│                         #   falsy-value preservation, config propagation,
│                         #   constraint extraction, DepthDetection (112 tests)
├── test_agents.py        # Prompt constants, build_agent_definitions,
│                         #   build_orchestrator_prompt, per-agent model config,
│                         #   naming consistency, template substitution,
│                         #   convergence gates, constraint injection (69 tests)
├── test_cli.py           # _detect_agent_count, _detect_prd_from_task, _parse_args,
│                         #   _handle_interrupt, main(), mutual exclusion,
│                         #   URL validation, build options, template vars (70 tests)
├── test_interviewer.py   # EXIT_PHRASES, _is_interview_exit (all 26 phrases parametrized),
│                         #   _detect_scope, InterviewResult, run_interview,
│                         #   _build_interview_options, phase helpers (66 tests)
├── test_display.py       # Smoke tests for all display functions including scheduler
│                         #   and verification output + console configuration (46 tests)
├── test_mcp_servers.py   # _firecrawl_server, _context7_server, get_mcp_servers,
│                         #   get_research_tools (18 tests)
├── test_codebase_map.py  # File discovery, exports/imports extraction, framework
│                         #   detection, role classification, import path resolution,
│                         #   pyproject parsing, async map generation,
│                         #   config wiring (max_files, exclude_patterns) (125 tests)
├── test_contracts.py     # Module/wiring contract verification, symbol presence
│                         #   (Python + TS), serialization, shared language
│                         #   detection, file read error handling (50 tests)
├── test_scheduler.py     # Task parsing, dependency graph, topological sort,
│                         #   execution waves, file conflict detection, critical
│                         #   path, file context, task context rendering,
│                         #   config wiring (max_parallel, conflict_strategy) (101 tests)
├── test_verification.py  # Subprocess runner, verify_task_completion, automated
│                         #   review phases, health computation, verification
│                         #   summary output, blocking config wiring (44 tests)
├── test_state.py         # RunState, RunSummary, save/load state, atomic writes,
│                         #   staleness detection (14 tests)
├── test_integration.py   # Cross-module pipelines: config→agents, depth→prompt,
│                         #   MCP→researcher, interview→orchestrator, runtime
│                         #   wiring for scheduler/contracts/verification,
│                         #   config field wiring end-to-end (29 tests)
└── test_e2e.py           # Real API smoke tests: CLI --help/--version,
                          #   SDK client lifecycle, Firecrawl config (5 tests)
```

**Total: 871 tests** — 866 unit/integration (always run) + 5 E2E (require `--run-e2e`).

### Known Bug Verification

The test suite explicitly verifies fixes for known bugs:

| Bug | Test | Verified Behavior |
|-----|------|-------------------|
| C1: Empty stdin loop | `test_is_interview_exit` — empty string | Returns `False`, doesn't loop |
| C2: PRD depth override | `test_prd_forces_exhaustive` | `--prd` forces exhaustive depth |
| #3: Malformed YAML | `test_load_config_malformed_yaml_raises` | Raises `yaml.YAMLError` |
| I6: Scope from --interview-doc | `test_interview_doc_scope_detected` | `_detect_scope()` called on doc |
| #7: Empty research tools | `test_empty_servers_returns_empty_list` | Returns `[]` not `None` |
| I7: Substring false match | `test_word_boundary_no_substring` | "adjustment" does not match "just" |
| I11: Bold scope format | `test_markdown_bold` | `**Scope:** COMPLEX` parses correctly |
| #9: Falsy config override | `TestDesignReferenceFalsyValues` | `urls: []` stays `[]`, not overridden by default |
| #4: Hardcoded agent model | `TestPerAgentModelConfig` | Config model propagates to agent definitions |
| #10: CLI flag collision | `TestMutualExclusion` | `--progressive`/`--no-progressive` are mutually exclusive |
| #17: Name duality | `TestAgentNamingConsistency` | Underscore config keys map to hyphenated SDK names |
| #20: Template injection | `TestTemplateSubstitution` | `safe_substitute` handles missing vars gracefully |
| Tier 3a: Off-by-one exit | `TestInterviewPhases` | Exit at exactly `min_exchanges` triggers confirmation, not redirect |
| DepthDetection recursion | `TestDepthDetection` | `__getattr__` doesn't loop during `copy.deepcopy` or `pickle` |
| O(n²) cost counting | `TestCostAccumulation` | Each `ResultMessage.total_cost_usd` counted exactly once |
| Config validation crash | `TestDictToConfig` | `min_exchanges > max_exchanges` raises clean `ValueError` |

---

## Architecture

```
src/agent_team/
├── __init__.py          # Package entry, version
├── __main__.py          # python -m agent_team support
├── cli.py               # CLI parsing, subcommands, interview/orchestrator dispatch, budget tracking
├── config.py            # YAML config loading, depth detection, constraint extraction, fleet scaling
├── agents.py            # 9 agent system prompts + orchestrator prompt builder + constraint injection
├── interviewer.py       # Phase 0: 3-phase interactive interview with min-exchange enforcement
├── display.py           # Rich terminal output (banners, tables, progress, verification)
├── state.py             # Run state persistence: save/load STATE.json, atomic writes, staleness detection
├── mcp_servers.py       # Firecrawl + Context7 MCP server configuration
├── _lang.py             # Shared language detection (Python, TS, JS, Go, Rust, etc.)
├── enums.py             # Type-safe enums (DepthLevel, TaskStatus, HealthStatus, etc.)
├── codebase_map.py      # Phase 0.5: project structure analysis, dependency mapping
├── contracts.py         # Interface contracts: module exports + wiring verification
├── scheduler.py         # Smart task scheduler: DAG, conflict detection, wave computation
└── verification.py      # Progressive verification: contracts → lint → types → tests
```

### Key Design Decisions

- **Requirements as source of truth**: Every agent reads from and writes to `.agent-team/REQUIREMENTS.md`. No implicit state.
- **Adversarial review**: Reviewers are prompted to _break_ things, not confirm they work. Items are rejected more than accepted on first pass.
- **Task atomicity**: TASKS.md decomposes work into tasks targeting 1-3 files max, with explicit dependency DAGs. Code writers get non-overlapping file assignments.
- **Wiring verification**: Architects produce a Wiring Map (WIRE-xxx entries) documenting every cross-file connection. Reviewers trace each connection from entry point to feature, flagging orphaned code.
- **Contract verification**: Interface contracts (`CONTRACTS.json`) declare which symbols each module must export and how modules import from each other. Verification is deterministic and runs without LLM involvement.
- **Progressive verification**: A 4-phase pipeline (contracts → lint → type check → tests) validates each completed task. Health is tracked as green/yellow/red across the project.
- **Constraint propagation**: User constraints ("never", "must", "only") are extracted from task text and interview, then injected into every agent's system prompt with emphasis levels.
- **Convergence gates**: Only code-reviewer and test-runner agents can mark items `[x]`. Debug fixes require mandatory re-review. These rules are embedded in each agent's prompt.
- **Smart scheduling**: Tasks are parsed into a DAG, file conflicts are detected and resolved via configurable strategies, execution waves are capped by `max_parallel_tasks`, and critical path analysis identifies bottleneck tasks.
- **Type-safe enums**: Categorical config values (`depth`, `conflict_strategy`, `severity`, etc.) use `str, Enum` classes for both type safety and JSON/YAML serialization compatibility.
- **State persistence**: Run state (task, depth, phase, cost) is saved to `STATE.json` on interrupt via atomic file writes (`tempfile` + `os.replace`), preventing corruption if the process dies mid-write.
- **Template safety**: Orchestrator prompt variables use `string.Template.safe_substitute()` — unmatched `$vars` are left intact instead of crashing.
- **Subprocess security**: All external commands (`lint`, `type check`, `test`) use `asyncio.create_subprocess_exec` (not `shell`), preventing shell injection. Command lists are constructed from hardcoded strings only.
- **Path traversal protection**: Import path resolution in codebase mapping validates resolved paths stay within the project root.
- **Transcript backup**: Interview exchanges are saved to `INTERVIEW_BACKUP.json` independently of Claude's file writes, so context is never lost.
- **Word-boundary matching**: Depth detection and scope detection use `\b` regex boundaries to prevent false positives ("adjustment" won't match "just").
- **Pipe-safe output**: Rich console uses `force_terminal=sys.stdout.isatty()` to prevent ANSI escape sequences from garbling piped output.

### Module Dependency Graph

```
cli.py ──────┬──→ config.py ──→ enums.py
             ├──→ agents.py ──→ config.py
             ├──→ interviewer.py
             ├──→ display.py
             ├──→ state.py
             ├──→ mcp_servers.py
             ├──→ codebase_map.py ──→ _lang.py
             ├──→ contracts.py ────→ _lang.py
             ├──→ scheduler.py
             └──→ verification.py ──→ contracts.py
```

---

## Security

The following security properties are maintained:

| Area | Protection |
|------|-----------|
| Subprocess execution | `create_subprocess_exec` only — no shell interpretation |
| YAML deserialization | `yaml.safe_load` — no arbitrary object instantiation |
| Template variables | `string.Template.safe_substitute` — no crash on missing vars |
| File path resolution | `Path.resolve()` + `startswith()` bounds checking |
| API key handling | Keys read from environment only, never logged or included in prompts |
| Signal handling | Thread-safe under CPython GIL, first Ctrl+C warns, second saves state and exits |
| State file writes | Atomic via `tempfile.mkstemp` + `os.replace` — no corruption on crash |

---

## License

MIT
