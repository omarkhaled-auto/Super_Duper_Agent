# Agent Team

Convergence-driven multi-agent orchestration system built on the [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-agent-sdk). Takes any task — from a one-line bug fix to a full PRD — and drives it to verified completion using fleets of specialized AI agents.

## How It Works

Agent Team runs a **convergence loop**: agents write code, reviewers try to break it, debuggers fix what's broken, and the loop repeats until every requirement passes adversarial review. Nothing ships half-done.

```
Interview → Plan → Research → Architect → Assign Tasks → Code → Review → Debug → Test → Done
                                                          ↑                    ↓
                                                          └────── (loop until all pass) ──┘
```

### The Pipeline

| Phase | Agent | What It Does |
|-------|-------|-------------|
| 0 | **Interviewer** | Talks to you, asks clarifying questions, writes `.agent-team/INTERVIEW.md` |
| 1 | **Planner** | Explores codebase, creates `.agent-team/REQUIREMENTS.md` with checklist |
| 2 | **Researcher** | Queries docs (Context7) and web (Firecrawl), adds findings to requirements |
| 3 | **Architect** | Designs solution, file ownership map, interface contracts |
| 4 | **Task Assigner** | Decomposes requirements into atomic tasks in `.agent-team/TASKS.md` |
| 5 | **Code Writer** | Implements assigned tasks (non-overlapping files, reads from TASKS.md) |
| 6 | **Code Reviewer** | Adversarial review — tries to break everything, marks items pass/fail |
| 7 | **Debugger** | Fixes specific issues flagged by reviewers |
| 8 | **Test Runner** | Writes and runs tests for each requirement |
| 9 | **Security Auditor** | OWASP checks, dependency audit, credential scanning |

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

## Installation

Requires Python 3.10+ and Node.js (for MCP servers).

```bash
# Clone
git clone https://github.com/omarkhaled-auto/Super_Duper_Agent.git
cd Super_Duper_Agent

# Install
pip install -e .

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Optional: enable web research
export FIRECRAWL_API_KEY=fc-...
```

## Usage

### Interactive Mode (recommended)

```bash
agent-team
```

Starts an interview session. The interviewer asks about your project, writes a structured requirements document, then hands off to the orchestrator. Type `I'm done`, `let's go`, or `start building` when ready.

### Single-Shot Mode

```bash
agent-team "Add JWT authentication to the Express API"
```

Skips interactive mode. Detects depth from keywords and runs to completion.

### PRD Mode

```bash
agent-team --prd requirements.md
```

Reads a full Product Requirements Document. Activates exhaustive depth, decomposes into milestones, and executes each milestone through the full convergence pipeline.

### All CLI Options

```
agent-team [TASK] [OPTIONS]

Positional:
  TASK                    Task description (omit for interactive mode)

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
  -i, --interactive       Force interactive mode
  -v, --verbose           Show all tool calls and agent details
  --version               Show version
```

### Examples

```bash
# Quick bug fix — minimal agents, fast
agent-team "quick fix: the login button doesn't submit the form"

# Thorough feature — more agents, deeper review
agent-team "thoroughly add user profile editing with avatar upload"

# Specify exact agent count
agent-team "use 20 agents to refactor the authentication system"

# Full app from PRD with exhaustive depth
agent-team --prd product-spec.md --depth exhaustive

# Use a previous interview document
agent-team --interview-doc .agent-team/INTERVIEW.md

# Skip interview, set working directory
agent-team --no-interview --cwd /path/to/project "add dark mode"

# Interactive mode with verbose output
agent-team -i -v
```

## What It Produces

Agent Team creates a `.agent-team/` directory in your project with:

| File | Purpose |
|------|---------|
| `INTERVIEW.md` | Structured requirements from the interview phase |
| `INTERVIEW_BACKUP.json` | JSON transcript backup of the interview |
| `REQUIREMENTS.md` | Master checklist — the single source of truth |
| `TASKS.md` | Atomic task breakdown with dependency graph |
| `MASTER_PLAN.md` | Milestone plan (PRD mode only) |

### Requirements Checklist

Every requirement gets tracked with review cycles:

```markdown
## Requirements Checklist

### Functional Requirements
- [x] REQ-001: User can log in with email and password (review_cycles: 2)
- [ ] REQ-002: Password reset sends email within 30 seconds (review_cycles: 1)

### Technical Requirements
- [x] TECH-001: All endpoints return proper HTTP status codes (review_cycles: 1)

## Review Log
| Cycle | Reviewer | Item | Verdict | Issues Found |
|-------|----------|------|---------|-------------|
| 1 | reviewer-1 | REQ-001 | FAIL | Missing input validation on email field |
| 2 | reviewer-2 | REQ-001 | PASS | None |
| 1 | reviewer-1 | REQ-002 | FAIL | Email service not connected |
```

The task is **complete only when every `[ ]` becomes `[x]`**.

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

### Escalation Protocol

If a requirement fails review 3+ times (configurable):
1. Sent back to Planning + Research fleet for re-analysis
2. Requirement is rewritten or split into sub-tasks
3. Sub-tasks go through the full pipeline
4. Max escalation depth: 2 levels (configurable)
5. If exceeded: the system asks the user for guidance

## Configuration

Create `config.yaml` in your project root or `~/.agent-team/config.yaml`:

```yaml
orchestrator:
  model: "opus"           # Model for the orchestrator
  max_turns: 500          # Max agentic turns per session
  permission_mode: "acceptEdits"

depth:
  default: "standard"     # Default depth when no keywords detected
  auto_detect: true       # Detect depth from task keywords
  keyword_map:
    quick: ["quick", "fast", "simple", "just"]
    thorough: ["thorough", "carefully", "deep", "detailed"]
    exhaustive: ["exhaustive", "comprehensive", "complete"]

convergence:
  max_cycles: 10                    # Max convergence loop iterations
  escalation_threshold: 3           # Failures before escalation
  max_escalation_depth: 2           # Max re-planning levels
  requirements_dir: ".agent-team"
  requirements_file: "REQUIREMENTS.md"
  master_plan_file: "MASTER_PLAN.md"

interview:
  enabled: true           # Run interview phase
  model: "opus"           # Model for interviewer
  max_exchanges: 50       # Max interview exchanges

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
  show_fleet_composition: true
  show_convergence_status: true
  verbose: false
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `FIRECRAWL_API_KEY` | No | Firecrawl MCP server for web research |

## Architecture

```
src/agent_team/
├── __init__.py          # Package entry, version
├── __main__.py          # python -m agent_team support
├── cli.py               # CLI argument parsing, interview/orchestrator dispatch
├── config.py            # YAML config loading, depth detection, fleet scaling
├── agents.py            # 9 agent system prompts + orchestrator prompt
├── interviewer.py       # Phase 0: interactive interview session
├── display.py           # Rich terminal output (banners, tables, progress)
└── mcp_servers.py       # Firecrawl + Context7 MCP server configuration
```

### Key Design Decisions

- **Requirements as source of truth**: Every agent reads from and writes to `.agent-team/REQUIREMENTS.md`. No implicit state.
- **Adversarial review**: Reviewers are prompted to _break_ things, not confirm they work. Items are rejected more than accepted on first pass.
- **Task atomicity**: TASKS.md decomposes work into tasks targeting 1-3 files max, with explicit dependency DAGs. Code writers get non-overlapping file assignments.
- **Transcript backup**: Interview exchanges are saved to `INTERVIEW_BACKUP.json` independently of Claude's file writes, so context is never lost.
- **Word-boundary matching**: Depth detection and scope detection use `\b` regex boundaries to prevent false positives ("adjustment" won't match "just").

## License

MIT
