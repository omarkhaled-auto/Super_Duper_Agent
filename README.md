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
| 0.25 | **Constraint Extractor** | Scans your task and interview for prohibitions, requirements, scope limits, technology stack mentions, and test count requirements — injects them into every agent |
| 0.5 | **Codebase Map** | Analyzes project structure, detects languages/frameworks, maps dependencies |
| 0.75 | **Contract Loading** | Loads `CONTRACTS.json` for interface verification (if enabled) |
| 0.9 | **Spec Validator** | Compares original user request against REQUIREMENTS.md — flags missing technologies, features, scope reductions (read-only, always active) |
| 1 | **Planner** | Explores codebase, creates `.agent-team/REQUIREMENTS.md` with checklist. Guardrails enforce: technology preservation, monorepo structure, test requirements |
| 2 | **Researcher** | Queries docs (Context7) and web (Firecrawl), scrapes design references, adds findings to requirements |
| 3 | **Architect** | Designs solution, file ownership map, wiring map, interface contracts |
| 4 | **Task Assigner** | Decomposes requirements into atomic tasks in `.agent-team/TASKS.md` |
| 4.5 | **Smart Scheduler** | Builds dependency DAG, detects file conflicts, computes parallel execution waves |
| 5 | **Code Writer** | Implements assigned tasks (non-overlapping files, reads from TASKS.md). Has 30 frontend + backend anti-patterns injected |
| 6 | **Code Reviewer** | Adversarial review — tries to break everything, marks items pass/fail. Anchored to original user request to catch spec drift. Has 15 review anti-patterns injected |
| 7 | **Debugger** | Fixes specific issues flagged by reviewers. Has 10 debugging anti-patterns + methodology injected |
| 8 | **Test Runner** | Writes and runs tests for each requirement. Has 15 testing anti-patterns injected |
| 9 | **Security Auditor** | OWASP checks, dependency audit, credential scanning |
| 9.5 | **Deep Investigation** | Optional: Gemini CLI + structured 4-phase methodology for cross-file tracing (reviewer, auditor, debugger) |
| 9.6 | **Sequential Thinking** | Structured reasoning at 4 orchestrator decision points + numbered thought methodology for review agents |
| 9.7 | **Quality Spot Checks** | Regex-based scan for anti-patterns (FRONT-xxx, BACK-xxx, SLOP-xxx) in project files |
| 9.8 | **Milestone Health** | PRD mode: tracks per-milestone convergence, detects cross-milestone wiring gaps |
| 9.9 | **Convergence Health** | Post-run health panel: healthy/degraded/failed status, requirements progress, recovery passes |
| 10 | **Progressive Verification** | 5-phase pipeline: requirements compliance → contracts → lint → type check → tests |
| 11 | **Mock Data Scan** | Regex scan for mock data patterns (MOCK-001..007) in service/store/facade files |
| 12 | **UI Compliance Scan** | Regex scan for UI compliance violations (UI-001..004) — hardcoded fonts, arbitrary spacing, missing design tokens |
| 13 | **Deployment Scan** | Cross-references docker-compose.yml with .env files — port mismatches, undefined env vars, CORS origin mismatches |
| 14 | **Asset Scan** | Detects broken static asset references (src, href, url(), require, import) |
| 15 | **PRD Reconciliation** | LLM sub-orchestrator compares REQUIREMENTS.md against built codebase — flags implementation drift |
| 16 | **Database Integrity Scans** | 3 static scans (DB-001..008): dual ORM type consistency, default values, relationship completeness |
| 17 | **API Contract Verification** | Cross-references SVC-xxx field schemas against backend DTO properties and frontend model field names — catches field mismatches before runtime |
| 18 | **E2E Testing Phase** | Real backend API tests + Playwright browser tests — verifies the app actually works end-to-end |
| 19 | **Tracking Documents** | E2E coverage matrix, fix cycle log, milestone handoff docs — structured agent memory between phases |
| 20 | **Browser MCP Testing** | Playwright-based visual browser testing — starts app, executes user workflows, takes screenshots, fixes regressions |

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

This automatically forces **exhaustive** depth. PRD mode operates in two phases: (1) **Decomposition** — the orchestrator reads the PRD and creates a MASTER_PLAN.md with ordered milestones and dependencies, (2) **Execution** — each milestone is executed in a separate orchestrator session with scoped context (its own REQUIREMENTS.md + compressed summaries of completed predecessors). Enable per-milestone orchestration with `milestone.enabled: true` in config.

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
| **Technology** | Express.js, React, Next.js, MongoDB, TypeScript, Tailwind CSS, Docker, etc. (50+ patterns) | "Build with Express.js and MongoDB" → `must use Express.js`, `must use MongoDB` |
| **Test count** | `N+ tests`, `N unit tests` | "Include 20+ tests" → `must have 20+ tests` |

Constraints written in ALL CAPS or with emphasis words like "absolutely" or "critical" get higher priority. The system deduplicates across task text and interview document. Technology names and test counts are auto-extracted from both task text and interview documents.

### How to use

Just write naturally — say "NEVER touch the database migrations" in your task or during the interview, and every agent will see it as a high-priority prohibition.

---

## User Interventions

If you need to redirect the agents mid-run, type a message prefixed with `!!` and press Enter:

```
!! stop changing the CSS, focus on the API endpoints
```

Your message is queued in the background and sent to the orchestrator as a highest-priority follow-up when the current turn finishes. The orchestrator pauses new agent deployments, reads your intervention, adjusts the plan, and resumes. This lets you course-correct without restarting.

> **Windows note:** The terminal may not visually show what you're typing while output is streaming. Type your `!! message` anyway and press Enter — the system reads input in the background.

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
| `E2E_COVERAGE_MATRIX.md` | Requirement-to-test mapping with checkboxes (E2E phase) |
| `E2E_TEST_PLAN.md` | E2E test plan — what to test, expected behavior |
| `E2E_RESULTS.md` | E2E test results — pass/fail counts, failure details |
| `FIX_CYCLE_LOG.md` | Fix attempt history across all fix loops |
| `MILESTONE_HANDOFF.md` | Interface contracts per milestone for cross-milestone wiring |
| `PRD_RECONCILIATION.md` | PRD vs implementation comparison results |

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

Five hard rules are enforced during the convergence loop to prevent quality shortcuts:

| Gate | Rule |
|------|------|
| **Review authority** | Only code-reviewer and test-runner agents can mark checklist items `[x]`. Coders, debuggers, and architects cannot. |
| **Mandatory re-review** | After every debug fix, a reviewer must verify the fix. Debug → Re-Review is non-negotiable. |
| **Mandatory test wave** | If the user's task or REQUIREMENTS.md mentions tests/testing/test suite/test count, the testing fleet is MANDATORY and BLOCKING — the project cannot be marked complete without tests passing. |
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
  max_thinking_tokens: null  # Extended thinking budget (null = disabled, >= 1024 to enable)
  permission_mode: "acceptEdits"

depth:
  default: "standard"     # Default depth when no keywords detected
  auto_detect: true       # Detect depth from task keywords
  scan_scope_mode: "auto" # "auto" (depth-based), "full" (always full), "changed" (always scoped)
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
  min_convergence_ratio: 0.9        # Minimum pass ratio to declare convergence (0.0–1.0)
  recovery_threshold: 0.8           # Below this ratio, convergence is "recovering"
  degraded_threshold: 0.5           # Below this ratio, convergence is "degraded"

interview:
  enabled: true                        # Run interview phase
  model: "opus"                        # Model for interviewer
  max_exchanges: 50                    # Max interview exchanges
  min_exchanges: 3                     # Minimum before allowing finalization
  require_understanding_summary: true  # Force structured "My Understanding" sections
  require_codebase_exploration: true   # Force tool use (Glob/Read/Grep) in Discovery phase
  max_thinking_tokens: null            # Extended thinking budget (null = disabled, >= 1024 to enable)

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
  run_build: true                           # Run build phase
  run_security: true                        # Run security scan phase
  run_quality_checks: true                  # Run regex-based anti-pattern spot checks
  min_test_count: 0                         # Minimum test count to pass verification (0 = no minimum)
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

milestone:
  enabled: false              # Enable per-milestone PRD orchestration loop
  max_parallel_milestones: 1  # Max milestones to execute concurrently
  health_gate: true           # Block next milestone if previous is unhealthy
  wiring_check: true          # Run cross-milestone wiring analysis
  resume_from_milestone: null # Resume from a specific milestone ID (null = start from beginning)
  wiring_fix_retries: 1       # Retries for wiring fix passes
  max_milestones_warning: 30  # Warn if PRD decomposes into more milestones than this
  review_recovery_retries: 1  # Max review recovery attempts per milestone
  mock_data_scan: true        # Scan for mock data after each milestone

e2e_testing:
  enabled: false              # Enable E2E testing phase (opt-in, auto-enabled at thorough/exhaustive)
  backend_api_tests: true     # Run backend API E2E tests
  frontend_playwright_tests: true  # Run frontend Playwright E2E tests
  max_fix_retries: 5          # Fix-rerun cycles per part (min: 1)
  test_port: 9876             # Non-standard port for test isolation (1024-65535)
  skip_if_no_api: true        # Auto-skip backend if no API detected
  skip_if_no_frontend: true   # Auto-skip frontend if no frontend detected

browser_testing:
  enabled: false              # Enable browser MCP testing (auto-enabled at thorough/exhaustive + PRD)
  max_fix_retries: 3          # Fix-rerun cycles per failing workflow
  e2e_pass_rate_gate: 0.7     # Minimum E2E pass rate before browser testing runs
  headless: true              # Run browser in headless mode
  app_start_command: ""       # Custom app start command (empty = auto-detect)
  app_port: 0                 # Custom port (0 = auto-detect)
  regression_sweep: true      # Re-run passed workflows after fixes

tracking_documents:
  e2e_coverage_matrix: true      # Generate coverage matrix before E2E tests
  fix_cycle_log: true            # Track fix attempts across all fix loops
  milestone_handoff: true        # Generate handoff docs between milestones
  coverage_completeness_gate: 0.8  # 80% of requirements must have E2E tests
  wiring_completeness_gate: 1.0    # 100% of predecessor interfaces must be wired

integrity_scans:
  deployment_scan: true       # Docker-compose cross-reference scan
  asset_scan: true            # Broken static asset detection
  prd_reconciliation: true    # PRD vs implementation comparison

database_scans:
  dual_orm_scan: true         # Detect ORM vs raw SQL type mismatches
  default_value_scan: true    # Detect missing defaults and unsafe nullable access
  relationship_scan: true     # Detect incomplete relationship configuration

post_orchestration_scans:
  mock_data_scan: true        # Scan for mock data in service files
  ui_compliance_scan: true    # Scan for UI compliance violations
  api_contract_scan: true     # Cross-reference SVC-xxx field schemas against code
  max_scan_fix_passes: 1      # Fix-scan loop iterations per scan type (0=no fixes, quick=0, exhaustive=2)

mcp_servers:
  firecrawl:
    enabled: true         # Web scraping/search (requires FIRECRAWL_API_KEY)
  context7:
    enabled: true         # Library documentation (no key required)
  sequential_thinking:
    enabled: true         # Sequential Thinking MCP server (enabled by default)

orchestrator_st:
  enabled: true               # Sequential Thinking at orchestrator decision points
  depth_gate:                  # Which ST decision points activate at each depth
    quick: [1, 2, 3, 4]       # All points — depth is scale, not reasoning quality
    standard: [1, 2, 3, 4]
    thorough: [1, 2, 3, 4]
    exhaustive: [1, 2, 3, 4]
  thought_budgets:             # Max thoughts per decision point
    1: 8                       # Pre-run strategy
    2: 10                      # Architecture checkpoint
    3: 12                      # Convergence reasoning
    4: 8                       # Completion verification

quality:
  production_defaults: true    # Inject production-readiness TECH-xxx items into planner
  craft_review: true           # Enable CODE CRAFT review pass in reviewers
  quality_triggers_reloop: true  # Quality violations feed back into convergence loop

investigation:
  enabled: false              # Opt-in: deep investigation protocol for review agents
  gemini_model: ""            # Gemini model (empty = default). e.g. "gemini-2.5-pro"
  max_queries_per_agent: 8    # Max Gemini queries per agent (agent self-regulates within budget)
  timeout_seconds: 120        # Max seconds per Gemini query
  agents:                     # Which agents get the investigation protocol
    - "code-reviewer"
    - "security-auditor"
    - "debugger"

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

**Deep investigation (Gemini CLI cross-file tracing):**
```yaml
investigation:
  enabled: true               # Requires Gemini CLI installed
  gemini_model: "gemini-2.5-pro"
  max_queries_per_agent: 8    # Budget per agent (self-regulated)
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
| npm/npx not found on Windows | Fixed: verification now resolves `.cmd` suffixes automatically via `shutil.which()` |
| REQUIREMENTS.md doesn't match task | spec-validator agent (always active) compares requirements against your original request and flags discrepancies |

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
│                         #   constraint extraction, technology regex,
│                         #   test requirement regex, enhanced constraint
│                         #   extraction, DepthDetection, InvestigationConfig,
│                         #   MilestoneConfig, max_thinking_tokens validation,
│                         #   defaults/validation/YAML loading (230+ tests)
├── test_agents.py        # Prompt constants, build_agent_definitions,
│                         #   build_orchestrator_prompt, per-agent model config,
│                         #   naming consistency, template substitution,
│                         #   convergence gates, constraint injection,
│                         #   code quality standards injection, UI standards
│                         #   injection, prompt strengthening, spec validator,
│                         #   reviewer anchoring, planner guardrails,
│                         #   mandatory test wave, investigation injection (166 tests)
├── test_cli.py           # _detect_agent_count, _detect_prd_from_task, _parse_args,
│                         #   _handle_interrupt, main(), mutual exclusion,
│                         #   URL validation, build options, template vars,
│                         #   subscription backend, resume subcommand,
│                         #   milestone loop, convergence health (155+ tests)
├── test_interviewer.py   # EXIT_PHRASES, _is_interview_exit (all 26 phrases parametrized),
│                         #   _detect_scope, _estimate_scope_from_spec,
│                         #   InterviewResult, run_interview, non-interactive mode,
│                         #   _build_interview_options, phase helpers (115+ tests)
├── test_display.py       # Smoke tests for all display functions including scheduler,
│                         #   verification, convergence health, recovery reports,
│                         #   milestone progress + console configuration (65+ tests)
├── test_mcp_servers.py   # _firecrawl_server, _context7_server, get_mcp_servers,
│                         #   get_research_tools (22 tests)
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
│                         #   milestone-scoped scheduling, cross-milestone deps,
│                         #   config wiring (max_parallel, conflict_strategy) (140+ tests)
├── test_verification.py  # Subprocess runner, verify_task_completion, automated
│                         #   review phases, health computation, verification
│                         #   summary output, blocking config wiring,
│                         #   requirements compliance, Windows PATH
│                         #   resolution (63 tests)
├── test_state.py         # RunState, RunSummary, save/load state, atomic writes,
│                         #   staleness detection, milestone tracking, schema v2,
│                         #   update_milestone_progress, get_resume_milestone (55+ tests)
├── test_integration.py   # Cross-module pipelines: config→agents, depth→prompt,
│                         #   MCP→researcher, interview→orchestrator, runtime
│                         #   wiring for scheduler/contracts/verification,
│                         #   milestone orchestration, convergence health,
│                         #   config field wiring end-to-end (65+ tests)
├── test_ui_standards.py  # UI design standards loading, custom standards file,
│                         #   SLOP anti-pattern validation,
│                         #   get_ui_design_standards() (25 tests)
├── test_investigation_protocol.py
│                         # Template strings, builder basics, Gemini section
│                         #   inclusion/exclusion, Bash scoping rules, query
│                         #   budget, model flag, custom agents list,
│                         #   per-agent focus content (39 tests)
├── test_code_quality_standards.py
│                         # Frontend/backend/review/testing/debugging/architecture
│                         #   standards validation, anti-pattern completeness,
│                         #   get_standards_for_agent(), agent mapping,
│                         #   edge cases (empty/case/underscore) (49 tests)
├── test_sequential_thinking.py
│                         # ST methodology builder, depth gating, thought budgets,
│                         #   review agent injection, orchestrator decision points
├── test_convergence_health.py
│                         # Convergence ratio computation, health status thresholds,
│                         #   recovery/degraded detection, report generation
├── test_milestone_manager.py
│                         # MASTER_PLAN.md parsing, milestone context building,
│                         #   completion summaries, rollup health, per-milestone
│                         #   health tracking, cross-milestone wiring gap detection,
│                         #   import reference parsing (100+ tests)
├── test_quality_checks.py
│                         # Regex-based anti-pattern spot checks, violation
│                         #   dataclass, file scanning, max violations cap
├── test_state_extended.py
│                         # Extended state persistence, convergence reports,
│                         #   milestone state tracking
├── test_build_verification.py
│                         # Build phase verification, security scan phase,
│                         #   quality checks phase integration
├── test_wiring_depth.py  # Wiring dependency detection, WIRE-xxx task parsing,
│                         #   schedule hint generation
├── test_sdk_cmd_overflow.py
│                         # SDK command overflow protection, prompt size limits,
│                         #   large task handling (12+ tests)
└── test_e2e.py           # Real API smoke tests: CLI --help/--version,
                          #   SDK client lifecycle, Firecrawl config (5 tests)
```

**Total: 5037+ tests** — 5032+ unit/integration (always run) + 5 E2E (require `--run-e2e`).

### Upgrade Test Files (v2.0-v12.3)

```
tests/
├── test_prd_fixes.py                  # v2.0: Mock data patterns, decomposition, milestone workflow (120 tests)
├── test_ui_requirements.py            # v2.2: UI compliance, font/spacing/component regex (84 tests)
├── test_e2e_phase.py                  # v3.0: E2E config, app detection, quality patterns, fix loops (186 tests)
├── test_integrity_scans.py            # v3.1: Deployment, asset, PRD reconciliation scans (309 tests)
├── test_cross_upgrade_integration.py  # v3.2: Cross-version integration (39 tests)
├── test_wiring_verification.py        # v3.2: Function wiring, config consumption (105 tests)
├── test_tracking_documents.py         # v4.0: Coverage matrix, fix log, milestone handoff (130 tests)
├── test_database_scans.py             # v5.0: DB-001..008 scan patterns (231 tests)
├── test_database_wiring.py            # v5.0: DB scan CLI wiring (105 tests)
├── test_database_integrity_specialized.py  # v5.0: Specialized DB fixtures (105 tests)
├── test_depth_gating.py               # v6.0: Quick/standard/thorough/exhaustive gating (30 tests)
├── test_scan_scope.py                 # v6.0: ScanScope, compute_changed_files (45 tests)
├── test_config_evolution.py           # v6.0: PostOrchestrationScanConfig, user overrides (43 tests)
├── test_mode_propagation_wiring.py    # v6.0: Scope computation, PRD quality gate (48 tests)
├── test_v6_edge_cases.py              # v6.0: Edge cases for all v6 features (93 tests)
├── test_production_regression.py      # v7.0: All previously-found bugs regression (41 tests)
├── test_pipeline_execution_order.py   # v7.0: Post-orchestration order verification (38 tests)
├── test_config_completeness.py        # v7.0: All 11 dataclass defaults, YAML loading (47 tests)
├── test_scan_pattern_correctness.py   # v7.0: Positive/negative regex match tests (50 tests)
├── test_prompt_integrity.py           # v7.0: All 17 prompt policies verified (33 tests)
├── test_fix_completeness.py           # v7.0: All fix function branches, signatures (30 tests)
├── test_browser_testing.py            # v8.0: Browser MCP workflow parsing, startup, screenshots, edge cases (~190 tests)
├── test_browser_wiring.py             # v8.0: Browser CLI wiring, depth gating, signatures, crash isolation (~93 tests)
├── test_api_contract.py              # v9.0: API contract scan parsing, field matching, config, CLI wiring, backward compat (106 tests)
├── test_v10_1_runtime_guarantees.py  # v10.0-10.1: Production runtime fixes, effective_task, normalizer, GATE 5, task parser (121 tests)
├── test_database_fix_verification.py # v5.0: Database fix verification (64 tests)
├── test_v10_2_bugfixes.py            # v10.2: P0 re-run bugfixes — seed credentials, API contract parser, Violation attributes (87 tests)
├── test_cross_mode_matrix.py         # v10.3: Cross-mode verification — 5-layer harness across 20 mode combinations (319 tests)
├── test_v11_gap_closure.py           # v11.0: E2E gap closure — enum serialization, silent data loss, DTO field presence (105 tests)
├── test_v12_hard_ceiling.py          # v12.0-12.1: Endpoint XREF scan, write-side passthrough, cross-mode audit (72 tests)
├── test_xref_bug_fixes.py            # v12.2: 5 XREF extraction bugs — variable URLs, dedup, base URL, mount prefix, tilde (53 tests)
├── test_xref_function_call_filter.py # v12.3: Function-call FP filter — severity demotion, CLI severity gate (26 tests)
└── test_drawspace_critical_fixes.py  # v13.0: 4 Drawspace critical fixes — header resilience, loop guard, prompt de-escalation, MOCK-008 (57 tests)
```

### Live E2E Verification

The system has been verified with live end-to-end convergence tests that confirm all orchestration features work against the real Claude API.

**13/13 verification checks passed (100%)** across 9 issues:

| Issue | Fix Validated | Evidence |
|-------|---------------|----------|
| Convergence cycles | Yes | Cycle tracking shown, 37/37 requirements at 100% |
| Requirements marking | Yes | All `- [x]` properly checked |
| Task completion | Yes | All 4 tasks marked COMPLETE |
| Contract generation | Yes | CONTRACTS.json with 4 contracts |
| Health display | Yes | `CONVERGENCE HEALTH: HEALTHY` banner |
| Schedule waves | Yes | Phase/schedule references in output |
| Recovery logging | Yes | Health info displayed |
| Cycle counter | Yes | `Convergence cycles: 0` tracked |
| Diagnostic post-orch | Yes | No blind mark-all, proper diagnostic marking |

**Convergence loop stress test:** A run-length encoding test with deliberately tricky edge cases (digits as input, multi-digit counts, roundtrip identity) confirmed the agent's ability to detect test failures and iterate on fixes within a single run — the agent went through 3 implementation attempts before all 13 tests passed.

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
| Trust gap: spec drift | `TestSpecValidatorPrompt` | spec-validator always active, read-only, catches missing tech/features |
| Trust gap: reviewer not anchored | `TestReviewerAnchoring` | CODE_REVIEWER_PROMPT references ORIGINAL USER REQUEST |
| Trust gap: planner simplifies | `TestPlannerGuardrails` | PLANNER_PROMPT preserves technologies, monorepo, test counts |
| Trust gap: tests skipped | `TestMandatoryTestWave` | ORCHESTRATOR_SYSTEM_PROMPT has MANDATORY TEST RULE |
| Trust gap: missing deps | `TestCheckRequirementsCompliance` | Phase 0 checks tech in package.json/pyproject.toml |
| Windows PATH failure | `TestResolveCommand` | `_resolve_command` tries .cmd suffix on Windows |
| Constraint: tech not extracted | `TestEnhancedConstraintExtraction` | Technology mentions auto-extracted as constraints |
| O(n²) cost counting | `TestCostAccumulation` | Each `ResultMessage.total_cost_usd` counted exactly once |
| Config validation crash | `TestDictToConfig` | `min_exchanges > max_exchanges` raises clean `ValueError` |

---

## Architecture

```
src/agent_team/
├── __init__.py              # Package entry, version
├── __main__.py              # python -m agent_team support
├── cli.py                   # CLI parsing, subcommands, interview/orchestrator dispatch, budget tracking
├── config.py                # YAML config loading, depth detection, constraint extraction (incl. tech stack + test count), fleet scaling, ST config
├── agents.py                # 10 agent system prompts (+ spec-validator) + orchestrator prompt builder + constraint/quality-standards/investigation/ST injection
├── investigation_protocol.py  # Deep investigation protocol: 4-phase methodology + Gemini CLI integration + per-agent focus
├── sequential_thinking.py   # Numbered thought methodology for review agents (composable with investigation protocol)
├── orchestrator_reasoning.py  # 4 depth-gated Sequential Thinking decision points for the orchestrator
├── code_quality_standards.py  # Non-configurable code quality standards (70 anti-patterns across 5 domains)
├── quality_checks.py        # Regex-based anti-pattern spot checker — scans project files for FRONT/BACK/SLOP violations
├── ui_standards.py          # Built-in UI design standards (SLOP-001→015) + custom standards file support
├── interviewer.py           # Phase 0: 3-phase interactive interview with min-exchange enforcement, non-interactive mode, scope estimation
├── display.py               # Rich terminal output (banners, tables, progress, verification, convergence health panels, milestone progress)
├── state.py                 # Run state persistence: save/load STATE.json, atomic writes, staleness detection, convergence reports, milestone tracking (schema v2)
├── mcp_servers.py           # Firecrawl + Context7 + Playwright MCP server configuration
├── _lang.py                 # Shared language detection (Python, TS, JS, Go, Rust, etc.)
├── enums.py                 # Type-safe enums (DepthLevel, TaskStatus, HealthStatus, etc.)
├── codebase_map.py          # Phase 0.5: project structure analysis, dependency mapping
├── contracts.py             # Interface contracts: module exports + wiring verification
├── scheduler.py             # Smart task scheduler: DAG, conflict detection, wave computation, milestone-scoped scheduling + cross-milestone deps
├── milestone_manager.py     # PRD mode: MASTER_PLAN.md parsing, two-phase orchestration (decomposition + execution), milestone context building, completion summaries, per-milestone health + cross-milestone wiring
├── wiring.py                # Wiring dependency detection — defers WIRE-xxx tasks until prerequisites complete
├── verification.py          # Progressive verification: requirements → contracts → lint → types → tests → build → security → quality checks
├── e2e_testing.py           # E2E testing: AppTypeInfo, detect_app_type(), parse_e2e_results(), backend/frontend/fix prompt constants
├── browser_testing.py       # Browser MCP testing: WorkflowDefinition, AppStartupInfo, workflow generation/parsing, 4 prompt constants
├── tracking_documents.py    # Per-phase tracking: E2E coverage matrix, fix cycle log, milestone handoff generation + parsing
├── design_reference.py      # Design reference extraction: retry, fallback, validation, UI requirements generation
└── prd_chunking.py          # Large PRD detection (>50KB), section chunking, index building
```

### Key Design Decisions

- **Requirements as source of truth**: Every agent reads from and writes to `.agent-team/REQUIREMENTS.md`. No implicit state.
- **Adversarial review**: Reviewers are prompted to _break_ things, not confirm they work. Items are rejected more than accepted on first pass.
- **Task atomicity**: TASKS.md decomposes work into tasks targeting 1-3 files max, with explicit dependency DAGs. Code writers get non-overlapping file assignments.
- **Wiring verification**: Architects produce a Wiring Map (WIRE-xxx entries) documenting every cross-file connection. Reviewers trace each connection from entry point to feature, flagging orphaned code.
- **Contract verification**: Interface contracts (`CONTRACTS.json`) declare which symbols each module must export and how modules import from each other. Verification is deterministic and runs without LLM involvement.
- **Progressive verification**: A 5-phase pipeline (requirements compliance → contracts → lint → type check → tests) validates each completed task. Phase 0 is deterministic — it checks declared technologies against `package.json`/`pyproject.toml` dependencies, validates monorepo structure, and verifies test files exist when testing is mentioned. Health is tracked as green/yellow/red across the project.
- **Constraint propagation**: User constraints ("never", "must", "only") are extracted from task text and interview, then injected into every agent's system prompt with emphasis levels. Technology mentions (Express.js, React, MongoDB, etc.) and test count requirements ("20+ tests") are also auto-extracted as constraints.
- **Spec fidelity validation**: A dedicated spec-validator agent (read-only, always active) compares the original user request against REQUIREMENTS.md to catch scope reductions, missing technologies, and missing features before code is written.
- **Original request anchoring**: The reviewer is anchored to the original user request — not just REQUIREMENTS.md — so spec drift (where the planner simplifies the user's intent) is caught at review time.
- **Planner guardrails**: The planner is explicitly instructed to preserve user-specified technologies, monorepo/full-stack structure, and test requirements. These guardrails prevent the most common cause of the "trust gap" (planner simplifying what the user asked for).
- **Mandatory test wave**: When the user's task or REQUIREMENTS.md mentions tests, the testing fleet is mandatory and blocking — the project cannot be marked complete without tests passing.
- **Code quality standards**: 70 anti-patterns across 5 domains (Frontend, Backend, Code Review, Testing, Debugging) plus Architecture quality rules are automatically injected into relevant agent prompts. Non-configurable — always on, zero setup. Each agent receives only its domain-specific standards (e.g., code-writer gets Frontend + Backend, test-runner gets Testing).
- **Convergence gates**: Only code-reviewer and test-runner agents can mark items `[x]`. Debug fixes require mandatory re-review. These rules are embedded in each agent's prompt.
- **Smart scheduling**: Tasks are parsed into a DAG, file conflicts are detected and resolved via configurable strategies, execution waves are capped by `max_parallel_tasks`, and critical path analysis identifies bottleneck tasks.
- **Type-safe enums**: Categorical config values (`depth`, `conflict_strategy`, `severity`, etc.) use `str, Enum` classes for both type safety and JSON/YAML serialization compatibility.
- **State persistence**: Run state (task, depth, phase, cost) is saved to `STATE.json` on interrupt via atomic file writes (`tempfile` + `os.replace`), preventing corruption if the process dies mid-write.
- **Template safety**: Orchestrator prompt variables use `string.Template.safe_substitute()` — unmatched `$vars` are left intact instead of crashing.
- **Subprocess security**: All external commands (`lint`, `type check`, `test`) use `asyncio.create_subprocess_exec` (not `shell`), preventing shell injection. Command lists are constructed from hardcoded strings only. On Windows, commands are resolved to full paths via `shutil.which()` with `.cmd` suffix fallback to handle npm/npx PATH issues.
- **Path traversal protection**: Import path resolution in codebase mapping validates resolved paths stay within the project root.
- **Transcript backup**: Interview exchanges are saved to `INTERVIEW_BACKUP.json` independently of Claude's file writes, so context is never lost.
- **Word-boundary matching**: Depth detection and scope detection use `\b` regex boundaries to prevent false positives ("adjustment" won't match "just").
- **Deep investigation protocol**: An optional 4-phase structured methodology (SCOPE → INVESTIGATE → SYNTHESIZE → EVIDENCE) injected into review agents (code-reviewer, security-auditor, debugger). When Gemini CLI is installed, agents can use it for cross-file tracing with a per-agent query budget. Degrades gracefully: disabled by default (zero impact), enabled without Gemini (methodology only, still valuable), enabled with Gemini (full cross-file analysis).
- **Sequential Thinking**: Two layers of structured reasoning. (1) Review agents get a numbered thought methodology (hypothesis → verify → revise) that composes with the investigation protocol. (2) The orchestrator uses Sequential Thinking at 4 decision points: pre-run strategy, architecture checkpoint, convergence reasoning, and completion verification. All 4 points fire at every depth level — depth controls fleet scale, not reasoning quality. Each point has a configurable thought budget. The Sequential Thinking MCP server is enabled by default.
- **Quality optimization**: Three production-quality features enabled by default. `production_defaults` injects production-readiness requirements (TECH-xxx) into the planner. `craft_review` adds a CODE CRAFT pass to reviewers (naming, structure, duplication). `quality_triggers_reloop` feeds quality violations back into the convergence loop so they get fixed, not just reported.
- **Anti-pattern spot checks**: `quality_checks.py` scans project files with compiled regex patterns for common anti-patterns (FRONT-xxx, BACK-xxx, SLOP-xxx). Runs as a non-blocking advisory phase in the verification pipeline. Capped at 100 violations per scan.
- **Zero mock data policy**: Code writers are explicitly prohibited from using mock data (RxJS of(), Promise.resolve(), BehaviorSubject, hardcoded variables). Seven regex patterns (MOCK-001..007) scan service/store/facade files. Covers Angular, React, Vue/Nuxt, and Python.
- **E2E testing phase**: After convergence-driven reviews pass, real HTTP calls to real APIs (backend) and real Playwright browser interactions (frontend) verify the app actually works. Fix loops diagnose failure types and apply targeted strategies (implement feature, fix auth, fix wiring, fix logic).
- **Browser MCP visual testing**: After E2E tests pass, a Playwright MCP agent launches the app in a real browser, executes user-facing workflows (login, CRUD, navigation), takes screenshots, and verifies visual correctness. Regression sweeps re-run all passed workflows after each fix. Triple-gated (config + depth + E2E pass rate). Crash-isolated with finally-block app cleanup.
- **Tracking documents**: Three per-phase documents (coverage matrix, fix cycle log, milestone handoff) give agents structured memory between phases, preventing superficial testing, repeated fix strategies, and zero cross-milestone wiring.
- **API contract verification**: Three-layer system catches DTO field name mismatches between backend and frontend. Prevention: architect prompt forces exact field schemas in SVC-xxx table. Detection: `run_api_contract_scan()` cross-references code against contract. Guarantee: fix loop runs sub-orchestrator to correct mismatches. PascalCase-aware (C# properties serialize to camelCase). Only fires for full-stack apps.
- **Database integrity scans**: Three static scans catch dual ORM type mismatches, missing default values, and incomplete relationship configuration across C#, TypeScript, and Python frameworks. Prompt policies (seed data completeness, enum/status registry) prevent these bugs at code-writing time.
- **Depth-gated post-orchestration**: The entire post-orchestration pipeline is depth-aware. Quick fixes skip all scans. Standard scopes to changed files. Thorough/exhaustive auto-enable E2E testing. User overrides are sacred — explicit config values survive depth gating.
- **Scoped scanning**: `compute_changed_files()` uses git diff to determine what changed. Seven scan functions accept an optional scope parameter. Cross-file/aggregate checks use full file lists even when scoped, ensuring semantic correctness.
- **Milestone management**: PRD mode now uses two-phase orchestration. Phase 1 (Decomposition): the orchestrator reads the PRD and creates MASTER_PLAN.md with ordered milestones and dependencies. Phase 2 (Execution): each milestone runs in a separate orchestrator session with scoped context — its own REQUIREMENTS.md plus compressed summaries of completed predecessors. `milestone_manager.py` handles MASTER_PLAN.md parsing, milestone context building, completion caching, rollup health computation, and cross-milestone wiring gap detection. Controlled via the `milestone` config section (disabled by default).
- **Convergence health display**: After each orchestration run, a convergence health panel shows status (healthy/degraded/failed), a visual requirements progress bar, review cycle count, and recovery pass information. Three configurable thresholds (`min_convergence_ratio`, `recovery_threshold`, `degraded_threshold`) drive the health classification.
- **Non-interactive interviewer**: When stdin is not a TTY (CI/CD pipelines, scripted runs), the interviewer automatically skips the interactive Q&A loop. Scope estimation falls back to heuristic analysis of the spec text when no `Scope:` header is found in the interview document.
- **Wiring dependency scheduling**: `wiring.py` identifies WIRE-xxx tasks in TASKS.md and builds a dependency map so the scheduler defers integration tasks until all prerequisite implementation tasks are complete.
- **Convergence health tracking**: Three configurable thresholds (`min_convergence_ratio`, `recovery_threshold`, `degraded_threshold`) give the orchestrator visibility into whether convergence is healthy, recovering, or degraded, enabling smarter escalation decisions.
- **Pipe-safe output**: Rich console uses `force_terminal=sys.stdout.isatty()` to prevent ANSI escape sequences from garbling piped output.

### Module Dependency Graph

```
cli.py ──────┬──→ config.py ──→ enums.py
             ├──→ agents.py ──→ config.py
             │                ├──→ investigation_protocol.py ──→ config.py
             │                ├──→ sequential_thinking.py ───→ config.py
             │                ├──→ orchestrator_reasoning.py ──→ config.py
             │                ├──→ code_quality_standards.py
             │                └──→ ui_standards.py
             ├──→ interviewer.py
             ├──→ display.py
             ├──→ state.py
             ├──→ mcp_servers.py
             ├──→ codebase_map.py ──→ _lang.py
             ├──→ contracts.py ────→ _lang.py
             ├──→ scheduler.py
             │    └──→ wiring.py
             ├──→ milestone_manager.py ──→ state.py
             ├──→ quality_checks.py (8 scan functions, ScanScope, 40+ regex patterns)
             ├──→ e2e_testing.py (AppTypeInfo, detect_app_type, parse_e2e_results)
             ├──→ browser_testing.py (WorkflowDefinition, AppStartupInfo, 4 prompts, 15+ functions)
             ├──→ tracking_documents.py (coverage matrix, fix cycle log, milestone handoff)
             ├──→ design_reference.py (extraction retry, fallback, validation)
             ├──→ prd_chunking.py (large PRD detection, section chunking)
             └──→ verification.py ──→ contracts.py
                                  └──→ quality_checks.py
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
| Command resolution | `shutil.which()` resolves commands to full paths; `.cmd` fallback on Windows for npm/npx |
| Signal handling | Thread-safe under CPython GIL, first Ctrl+C warns, second saves state and exits |
| State file writes | Atomic via `tempfile.mkstemp` + `os.replace` — no corruption on crash |

---

## Post-Orchestration Pipeline (v2.0-v12.3)

After the convergence loop completes, a 15-step post-orchestration pipeline runs quality scans, integrity checks, E2E verification, and browser testing. All steps are depth-gated, crash-isolated, and independently configurable.

```
Scope Computation → Mock Data Scan → UI Compliance Scan → Deployment Scan
→ Asset Scan → PRD Reconciliation → DB Dual ORM Scan → DB Default Value Scan
→ DB Relationship Scan → API Contract Verification → Silent Data Loss Scan
→ Endpoint XREF Scan → E2E Backend Tests → E2E Frontend Tests
→ Browser MCP Testing → Recovery Report
```

### Depth Gating

| Scan/Feature | Quick | Standard | Thorough | Exhaustive |
|-------------|-------|----------|----------|------------|
| Mock data scan | SKIP | SCOPED | FULL | FULL |
| UI compliance scan | SKIP | SCOPED | FULL | FULL |
| Deployment scan | SKIP | FULL | FULL | FULL |
| Asset scan | SKIP | SCOPED | FULL | FULL |
| PRD reconciliation | SKIP | SKIP | CONDITIONAL | FULL |
| DB scans (3) | SKIP | SCOPED | FULL | FULL |
| API contract scan | SKIP | FULL | FULL | FULL |
| Silent data loss scan | SKIP | FULL | FULL | FULL |
| Endpoint XREF scan | SKIP | FULL | FULL | FULL |
| E2E testing | SKIP | OPT-IN | AUTO-ENABLED | AUTO-ENABLED |
| Browser MCP testing | SKIP | SKIP | AUTO-ENABLED (PRD) | AUTO-ENABLED (PRD) |

**SCOPED** = only files changed since last commit are scanned (via `git diff`).
**CONDITIONAL** = PRD recon only runs if REQUIREMENTS.md >500 bytes + contains REQ-xxx.
**AUTO-ENABLED** = E2E testing turns on automatically (unless user set `enabled: false`).
**AUTO-ENABLED (PRD)** = Browser testing turns on at thorough/exhaustive depth when PRD mode is active.

### Quality Scan Patterns

| Category | Patterns | What They Catch |
|----------|---------|----------------|
| Mock Data | MOCK-001..007 | RxJS of(), Promise.resolve(), BehaviorSubject, fake variables in services |
| UI Compliance | UI-001..004 | Hardcoded fonts, arbitrary spacing, missing design tokens, config file violations |
| E2E Quality | E2E-001..007 | Hardcoded timeouts, localhost ports, mock data in tests, empty bodies, placeholder text |
| Deployment | DEPLOY-001..004 | Port mismatches, undefined env vars, CORS origin, service name mismatches |
| Asset | ASSET-001..003 | Broken image/font/media, CSS url(), require/import references |
| Database | DB-001..008 | Dual ORM type mismatch, missing defaults, nullable access, FK/nav gaps |
| API Contract | API-001..004 | Backend DTO missing field, frontend model field mismatch, type incompatibility, write-side field passthrough |
| Silent Data Loss | SDL-001 | CQRS command handler doesn't persist all fields to database |
| Endpoint XREF | XREF-001..002 | Frontend calls missing backend endpoint, HTTP method mismatch |

### Endpoint Cross-Reference (v12.0)

Auto-detects backend framework (.NET, Express, Flask/FastAPI/Django) and cross-references every frontend HTTP call against backend route definitions.

1. **Extract frontend calls** — Angular HttpClient, Axios, raw `fetch()`, variable-URL resolution
2. **Extract backend routes** — ASP.NET `[HttpGet]`, Express `router.get()`, Python decorators, mount prefix resolution
3. **3-level matching** — Exact (path+method) → method-agnostic (XREF-002 warning) → no match (XREF-001 error)
4. **Function-call URL filter** — URLs like `${this.func(...)}/path` demoted to `info` severity (unresolvable statically)
5. **Fix loop** — Sub-orchestrator creates missing backend endpoints; severity filter skips info-only violations

### API Contract Verification

When enabled (default, disabled at quick depth), the API contract scan:

1. **Parse SVC-xxx table** from REQUIREMENTS.md — extracts field schemas like `{ id: number, title: string }`
2. **Cross-reference backend** — Checks DTO/model classes for every field (PascalCase and camelCase)
3. **Cross-reference frontend** — Checks model/interface files for exact field name matches
4. **Fix loop** — Sub-orchestrator corrects field mismatches (adds properties, renames fields)

**Full-stack gate:** Only runs when `detect_app_type()` reports both `has_backend` and `has_frontend`.
**Backward compatible:** Legacy SVC-xxx rows with class names only (no field schemas) produce zero violations.

### E2E Testing Phase

When enabled (opt-in at standard, auto-enabled at thorough/exhaustive), the E2E phase:

1. **Backend API E2E** — Writes real HTTP test scripts, executes against running server, fixes APP on failure
2. **Frontend Playwright E2E** — Navigates every route, tests every workflow, verifies forms submit and persist
3. **70% Backend Gate** — Frontend tests only run if backend achieves >=70% pass rate
4. **Fix Loop** — Up to `max_fix_retries` fix-rerun cycles per part (fixes the app, not the test)
5. **Tracking** — E2E coverage matrix maps every requirement to a test; fix cycle log prevents repeated strategies

### Browser MCP Testing Phase

When enabled (auto-enabled at thorough/exhaustive + PRD mode), the Browser MCP phase:

1. **App Startup** — Starts the built application, verifies health endpoint responds
2. **Workflow Generation** — Creates user-facing workflows from REQUIREMENTS.md (login, CRUD, navigation)
3. **Workflow Execution** — Playwright MCP clicks through each workflow, takes screenshots at each step
4. **Fix Loop** — Up to `max_fix_retries` fix-rerun cycles per failing workflow (fixes the app, not the test)
5. **Regression Sweep** — After each fix, ALL previously passed workflows are re-tested
6. **Readiness Report** — Final summary with pass/fail counts, screenshot inventory, unresolved issues

**Triple gate:** `browser_testing.enabled` + depth gating (thorough/exhaustive + PRD) + `e2e_pass_rate_gate` (70% E2E pass rate).

### Tracking Documents

Three documents give agents structured memory between phases:

| Document | Phase | Prevents |
|----------|-------|----------|
| `E2E_COVERAGE_MATRIX.md` | E2E Testing | Superficial testing (5 happy paths for 30+ workflows) |
| `FIX_CYCLE_LOG.md` | All Fix Loops | Blind fix loops (same fix 3 times with no memory) |
| `MILESTONE_HANDOFF.md` | PRD+ Milestones | Zero cross-milestone wiring (75 mock methods) |

---

## Version History

For detailed upgrade documentation with all fixes, hardening passes, review rounds, and test coverage, see [Agent-team_New_Upgrades.md](Agent-team_New_Upgrades.md) (v2.0-v12.3) and [Agent-team_New_Upgrades_V2.md](Agent-team_New_Upgrades_V2.md) (v13.0+).

| Version | Feature | Key Changes |
|---------|---------|------------|
| **v2.0** | PRD+ Critical Fixes | 6 root cause fixes (analysis persistence, milestone workflow, review recovery, zero mock data policy, service-to-API wiring, mock detection). MOCK-001..007 patterns. 120 tests. |
| **v2.2** | UI Requirements Hardening | Guaranteed UI generation (retry+fallback), UI-FAIL-001..007 enforcement, UI-001..004 scan patterns, dedicated UI phase (Step 3.7). 84 tests. |
| **v3.0** | E2E Testing Phase | Backend API + Playwright browser E2E, role-based testing, PRD feature coverage, fix loops with severity classification, 70% backend gate. 186 tests. |
| **v3.1** | Post-Build Integrity Scans | Deployment config (DEPLOY-001..004), asset references (ASSET-001..003), PRD reconciliation. 309 tests. |
| **v3.2** | Production Audit #1 | 6-agent audit, 4 bugs fixed (nested asyncio.run, query string, BOM, h4 headers). 259 tests. |
| **v4.0** | Tracking Documents | E2E coverage matrix, fix cycle log, milestone handoff with interface contracts. 130 tests. |
| **v5.0** | Database Integrity | DB-001..008 scans (dual ORM, defaults, relationships), seed data + enum/status policies, C#/TS/Py support. 2 review rounds, 24 fixes. 409 tests. |
| **v6.0** | Mode Upgrade Propagation | Depth-intelligent post-orchestration, scoped scanning (git diff), user override protection, PostOrchestrationScanConfig. 259 tests. |
| **v7.0** | Production Audit #2 | 6-agent audit, 3 bugs fixed, 239 new tests, **100% PRODUCTION READY** certification. 4019 total tests passing. |
| **v8.0** | Browser MCP Testing | Playwright-based visual browser testing — workflow execution, screenshot verification, regression sweeps, fix loops. 3-agent review cycle, 5 bugs fixed, 283 new tests. 4308 total tests passing. |
| **v9.0** | API Contract Verification | 3-layer system (prevention + detection + guarantee) — catches DTO field name mismatches between backend and frontend. API-001..003 violation codes. SVC-xxx field schema enforcement. 81 tests. 4361 total tests passing. |
| **v10.0** | Production Runtime Fixes | 9 deliverables fixing all 42 production test checkpoints. PRD root-level artifacts, subdirectory app detection, silent scan logging, recovery labels, DB-005 Prisma exclusion, multi-pass fix cycles, convergence loop enforcement, marking policy, UI fallback. `max_scan_fix_passes` config. 121 tests. 4510 total. |
| **v10.1** | Runtime Guarantees | Hardened effective_task, normalize_milestone_dirs, GATE 5 enforcement, TASKS.md bullet format parser, design direction inference, review cycle counter, E2E report parsing. 49 tests updated. |
| **v10.2** | P0 Re-Run Bugfix Sweep | 8 bugs fixed (2 CRITICAL + 3 HIGH + 2 MEDIUM + 1 LOW): Violation.code AttributeError, Windows path colon in filenames, review cycle counter, frontend E2E 0/0 parser, TASKS.md bullet format, seed credential Prisma extraction, API contract SVC table 5-col parser. 87 new tests + 25 API contract tests. 4718 total tests passing. |
| **v10.3** | Cross-Mode Verification | 5-layer harness verifying all 42 v10.0-v10.2 checkpoints across 20 mode combinations (4 depths x 5 input modes). Config state, prompt content, pipeline guards, behavioral, and guard-to-config mapping layers. 1 bug fixed (display.py gate5_enforcement label). 319 new tests. 5037 total tests passing. |
| **v11.0** | E2E Gap Closure | 3 failure pattern categories: ASP.NET enum serialization (SDL-001), silent data loss (CQRS persistence), DTO field presence (API-002 bidirectional). 4 prompt injections, `silent_data_loss_scan` config. Retroactive validation + API-002 hardening (5 surgical fixes). 105 tests. 5192 total. |
| **v12.0** | Hard Ceiling: Endpoint XREF | XREF-001/002 frontend-backend endpoint cross-reference scan. API-004 write-side field passthrough. Auto-detects .NET/Express/Python backends. 3-level matching (exact → method-agnostic → no match). 12 prompt directives. `endpoint_xref_scan` config. 72 tests. 5192 total. |
| **v12.1** | Cross-Mode Coverage Audit | Read-only audit of v11/v12 across all modes/depths. GAP-4 fix: interactive mode `depth` variable undefined at main() scope. 5245 total tests passing. |
| **v12.2** | XREF Extraction Bug Fixes | 5 bugs fixed: variable-URL resolution (BUG-1), line-based dedup (BUG-2), base URL variable resolution chain (BUG-3), Express mount prefix import tracing (BUG-4), ASP.NET `~` route override (BUG-5). Validated against TaskFlow Pro (0 violations) and Bayan (29 real). 53 tests. 5217 total. |
| **v12.3** | Function-Call FP Filter | Function-call URLs (`${this.func(...)}/path`) demoted to `info` severity. CLI severity filter: fix loop only triggers on error/warning. Full 15-stage pipeline audit. Bayan: 29→9 actionable violations. 26 tests. 5243 total. |
| **v13.0** | Drawspace Critical Fixes | 4 post-mortem fixes: h2-h4 header resilience + auto-fix, infinite loop guard (state + re-assertion), recovery prompt de-escalation (`[SYSTEM:]` tag), MOCK-008 component-level count detection. Sequential thinking verified. 57 tests. 5301 total. |

### Production Readiness

```
=============================================================
   100% PRODUCTION READY (v12.3 — 2026-02-11)
=============================================================
```

- **0 CRITICAL bugs** across all versions (5 found in v12.2 — all fixed)
- **5243 tests passing** (2 pre-existing failures in test_mcp_servers.py)
- **15/15 post-orchestration blocks** independently crash-isolated
- **20/20 prompt policies** correctly mapped across 6 agent roles
- **All 60+ config fields** consumed at correct gate locations
- **Full backward compatibility** — old configs, no configs, partial configs all work
- **7/7 isolation tests passed** against live TaskFlow Pro v10.2 project (0 XREF violations)

---

## v15.2 Changelog Highlights

### Summary

Version 15.2 represents the culmination of 13 major upgrade cycles (v2.0 through v13.0) that transformed agent-team from a basic orchestration tool into a production-certified multi-agent system with 5300+ tests and 15 post-orchestration quality scan layers.

### Key Additions Since v1.0

| Area | What Changed |
|------|-------------|
| **Post-Orchestration Pipeline** | 15-step pipeline with depth-gated scans: mock data, UI compliance, deployment config, asset references, PRD reconciliation, database integrity (3 scans), API contract verification, silent data loss, endpoint XREF, E2E testing (backend + frontend), browser MCP testing |
| **Quality Scan Patterns** | 40+ regex patterns across 9 categories: MOCK-001..008, UI-001..004, DEPLOY-001..004, ASSET-001..003, DB-001..008, API-001..004, SDL-001, XREF-001..002, E2E-001..007 |
| **Depth-Gated Execution** | Entire post-orchestration pipeline is depth-aware. Quick skips all scans. Standard scopes to changed files (git diff). Thorough/exhaustive auto-enable E2E and browser testing |
| **Browser MCP Testing** | Playwright-based visual testing: workflow execution, screenshot capture, regression sweeps, fix loops. Triple-gated (config + depth + E2E pass rate) |
| **API Contract Verification** | 3-layer system (prevention + detection + guarantee) catches DTO field mismatches. PascalCase-aware for C# properties |
| **Endpoint Cross-Reference** | Frontend-backend endpoint matching across .NET, Express, and Python backends. 3-level matching with function-call URL filtering |
| **Database Integrity Scans** | Dual ORM type consistency, default value validation, relationship completeness across C#, TypeScript, and Python |
| **Tracking Documents** | E2E coverage matrix, fix cycle log, milestone handoff -- structured agent memory between phases |
| **Drawspace Critical Fixes** | h2-h4 header resilience, infinite loop guard, recovery prompt de-escalation, MOCK-008 component-level detection |
| **Test Count** | 3 tests (v1.0) to 5300+ tests (v15.2), with 100% production ready certification at v12.3 |

---

## Windows SDK Patch (WinError 206)

On Windows, the `claude_agent_sdk` passes `--system-prompt` (~44K chars) and `--agents` (~110K chars) as CLI arguments, which exceeds the Windows `CreateProcess` limit of 32,767 characters.

### Symptoms

```
OSError: [WinError 206] The filename or extension is too long
```

This occurs when the orchestrator spawns agent subprocesses, because the combined CLI argument length exceeds the Windows limit.

### Fix

Apply a temp file optimization to `subprocess_cli.py` in the installed SDK package. The fix writes any flag value >4K characters to a temporary file and passes a `@tempfile` reference instead of the raw value.

**File to patch:**
```
<python-install>/Lib/site-packages/claude_agent_sdk/_internal/transport/subprocess_cli.py
```

**Typical location:**
```
C:\Users\<user>\AppData\Local\Programs\Python\Python312\Lib\site-packages\claude_agent_sdk\_internal\transport\subprocess_cli.py
```

**After patching:**
```bash
# Delete the cached bytecode to force recompilation
del __pycache__\subprocess_cli.cpython-312.pyc
```

### Patch Logic

The patch modifies the argument construction to detect oversized values and redirect them:

1. Before building the subprocess command, check each flag value length
2. If any value exceeds 4,096 characters, write it to a temp file
3. Replace the inline value with `@<tempfile_path>`
4. The SDK's argument parser reads files prefixed with `@`

This patch is required for all Windows users. Linux and macOS are not affected due to higher process argument limits.

---

## Audit System with 6 Auditors

The production audit system (used in v3.2 and v7.0) employs 6 specialized auditor agents that independently review the codebase:

| Auditor | Focus Area | What It Checks |
|---------|-----------|---------------|
| **Requirements Auditor** | Spec fidelity | Every REQ-xxx, TECH-xxx, WIRE-xxx checklist item matches code |
| **Technical Auditor** | Code quality | Architecture patterns, error handling, type safety, security |
| **Interface Auditor** | API contracts | Endpoint signatures, request/response schemas, status codes |
| **Test Auditor** | Test coverage | Test existence, assertion quality, edge case coverage |
| **Library Auditor** | Dependencies | Version pinning, vulnerability scanning, license compliance |
| **Security Auditor** | OWASP checks | Input validation, authentication, authorization, credential scanning |

### Audit Process

1. Each auditor independently reviews the codebase and produces a report
2. Reports are scored on a 0.0-1.0 scale
3. Findings are classified by severity: CRITICAL, HIGH, MEDIUM, LOW
4. A fix agent attempts to resolve HIGH+ findings (configurable via `severity_gate`)
5. Maximum fix rounds: 2 (configurable via `max_fix_rounds`) -- Round 3 has been observed to cause regressions

### Audit Configuration (for agent-team runs)

```yaml
# In config.yaml for audit-team orchestration
audit_team:
  max_fix_rounds: 2          # 2 rounds is the sweet spot; 3 causes regressions
  severity_gate: HIGH        # Skip MEDIUM/LOW fixes to save cost
```

### Audit vs Health Gate

The audit system and the convergence health gate can disagree. The health gate checks review fleet convergence (checkbox counts), while the audit checks code quality. It is possible for:

- Health gate = FAILED + Audit = PASSED (convergence issues but code quality is good)
- Health gate = PASSED + Audit = FAILED (all checkboxes done but code has quality issues)

---

## Scanner Exclusion Configuration

Several scanners can produce false positives when scanning virtual environment directories, vendored dependencies, or coverage tool output. Use these configuration flags to suppress known false positive patterns:

### Known False Positive Sources

| Scanner | False Positive Source | Description |
|---------|---------------------|-------------|
| **Mock Data Scan** | `.venv/` files | `charset_normalizer` uses `.format()` patterns that match RxJS `of()` regex |
| **Default Value Scan** | `.venv/` files | Same `charset_normalizer` false positive as mock data scan |
| **UI Compliance Scan** | `.venv/` coverage.py CSS | Coverage tool CSS files trigger font/spacing rules |

### Recommended Exclusion Settings

```yaml
# In config.yaml
post_orchestration_scans:
  mock_data_scan: false       # Disable if .venv/ false positives are problematic
  ui_compliance_scan: false   # Disable if coverage.py CSS triggers violations

database_scans:
  default_value_scan: false   # Disable if .venv/ false positives are problematic

codebase_map:
  exclude_patterns:           # Directories to exclude from scanning
    - ".venv"
    - "node_modules"
    - "__pycache__"
    - ".git"
    - "dist"
    - "build"
    - "coverage"
```

### Per-Scan Scope Control

Scans that support scoped mode (via `git diff`) are less prone to false positives because they only examine changed files:

```yaml
depth:
  scan_scope_mode: "auto"     # "auto" = depth-based, "full" = always full, "changed" = always scoped
```

At **standard** depth with `scan_scope_mode: "auto"`, most scans run in scoped mode (only changed files), which naturally excludes `.venv/` and `node_modules/` from the scan.

---

## Resume / Recovery Guide

### Automatic State Saving

When a run is interrupted (Ctrl+C or crash), state is automatically saved to `.agent-team/STATE.json`. This includes:

- Current phase and task progress
- Completed requirements
- Convergence cycle count
- Cost accumulation
- Milestone progress (PRD mode)

### Checking State

```bash
# View the current state
agent-team status

# Shows:
#   - Run ID
#   - Current phase
#   - Files in .agent-team/
#   - Cost so far (if available)
```

### Resuming a Run

```bash
# Resume from saved state (experimental)
agent-team resume
```

### Resuming PRD Milestone Runs

For PRD-based milestone runs, you can manually edit `STATE.json` to skip past a failed milestone:

1. Open `.agent-team/STATE.json`
2. Move the failed milestone ID from `failed_milestones` to `completed_milestones`
3. Set `current_milestone` to the next milestone ID
4. Re-run with the same command:

```bash
python -m agent_team --prd your_prd.md --config config.yaml --cwd /path/to/project --no-interview
```

The system reads `STATE.json` and resumes from the next uncompleted milestone.

### Recovery from Common Failures

| Failure | Recovery |
|---------|----------|
| **Budget exceeded** | Increase `max_budget_usd` in config.yaml, then resume |
| **Max turns reached** | Increase `max_turns`, then resume |
| **Convergence stuck** | Check `.agent-team/REQUIREMENTS.md` Review Log for repeatedly failing items. Consider lowering `escalation_threshold` or manually marking items |
| **Subprocess crash** | State is saved on crash. Run `agent-team status` to verify, then `agent-team resume` |
| **Audit fix regression** | Set `audit_team.max_fix_rounds: 2` to prevent Round 3 regressions. Resume from the milestone after the regressed one |
| **Windows WinError 206** | Apply the SDK temp file patch (see section above), then resume |

### Clean Start

If recovery is not viable, clean the state and start fresh:

```bash
# Delete all agent-team state
agent-team clean

# Or manually
rm -rf .agent-team/
```

---

## License

MIT
