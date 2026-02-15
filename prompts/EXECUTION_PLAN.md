# Super Agent Team — Complete Execution Plan

**Purpose:** This document is the COMPLETE guide for a Claude Code session that will run the agent-team tool across 4 PRDs to build the Super Agent Team. You must follow this plan exactly, monitor every phase, and write detailed verification logs.

**Date:** 2026-02-15
**Runner Tool:** agent-team v15.0 (located at `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team`)
**Model:** All agents use Claude Opus

---

## Table of Contents
1. [What You're Building](#1-what-youre-building)
2. [Directory Layout](#2-directory-layout)
3. [How the Agent-Team Works](#3-how-the-agent-team-works)
4. [Verification Log Protocol](#4-verification-log-protocol)
5. [Phase 0: Preparation](#5-phase-0-preparation)
6. [Phase 1A: Build 1 — Foundation Services](#6-phase-1a-build-1)
7. [Phase 1B: Build 2 — Builder Fleet Upgrade](#7-phase-1b-build-2)
8. [Checkpoint 1: Verify Build 1 + Build 2](#8-checkpoint-1)
9. [Phase 2: Build 3 — Integrator + Quality Gate + Super Orchestrator](#9-phase-2-build-3)
10. [Checkpoint 2: Verify Build 3](#10-checkpoint-2)
11. [Phase 3: Run 4 — End-to-End Verification](#11-phase-3-run-4)
12. [Final Review](#12-final-review)
13. [Troubleshooting Guide](#13-troubleshooting-guide)
14. [FAQ](#14-faq)

---

## 1. What You're Building

The Super Agent Team is a 4-part AI code generation platform. You will use the agent-team tool to build each part by feeding it a PRD (Product Requirements Document). The agent-team reads the PRD, decomposes it into milestones, generates code, runs quality scans, and produces a working project.

### The 4 Parts

| # | PRD File | What It Builds | Target Dir | Starts From | Milestones | Est. Cost | Est. Time |
|---|----------|----------------|------------|-------------|------------|-----------|-----------|
| 1 | `BUILD1_PRD.md` | 3 MCP servers (Architect, Contract Engine, Codebase Intelligence) | `super-team/` | **Empty directory** | 8 (M1-M8) | $25-40 | 30-60 min |
| 2 | `BUILD2_PRD.md` | Upgrades agent-team with MCP clients, agent teams, contract scans | `agent-team-v15/` | **Copy of agent-team** | 6 (M1-M6) | $20-35 | 25-45 min |
| 3 | `BUILD3_PRD.md` | Integrator + Quality Gate + Super Orchestrator + CLI | `super-team/` | **On top of Build 1** | 7 (M1-M7) | $35-50 | 45-75 min |
| 4 | `RUN4_PRD.md` | Verification scripts + 57-test matrix + audit report | `super-team/` | **On top of Build 1+3** | 6 (M1-M6) | $15-25 | 20-40 min |

### How They Connect

```
Build 1 (Foundation — 3 MCP servers)
  ├── Architect MCP (4 tools) ──────────────┐
  ├── Contract Engine MCP (9 tools) ────────┤
  └── Codebase Intelligence MCP (7 tools) ──┤
                                             ▼
Build 2 (Builder Fleet Upgrade)      Build 3 (Orchestrator)
  ├── Wraps 6 of 9 CE tools           ├── Calls Architect MCP via stdio
  ├── Wraps all 7 CI tools            ├── Calls CE MCP (3 remaining tools)
  ├── Wraps all 4 Architect tools     ├── Calls agent-team subprocess (Build 2)
  └── Agent teams abstraction         └── Docker Compose + Traefik + Quality Gate
                                             │
                                             ▼
                                      Run 4 (Verification)
                                        ├── Tests ALL 20 SVC wiring points
                                        ├── 57-test verification matrix
                                        ├── 5-tier Docker Compose merge
                                        └── SUPER_TEAM_AUDIT_REPORT.md
```

### Key Dependency Rules
- Build 1 and Build 2 are **INDEPENDENT** — can run in parallel
- Build 3 **REQUIRES** Build 1 code to exist in `super-team/` (same directory)
- Build 3 code has lazy imports — does NOT need Build 1 services running during build
- Run 4 **REQUIRES** all 3 builds complete
- Build 2 targets a **COPY** of agent-team — NEVER the running agent-team itself

---

## 2. Directory Layout

```
C:\Users\Omar Khaled\OneDrive\Desktop\
  │
  ├── claude-agent-team/          ← THE RUNNER (never modified by any build)
  │     ├── src/agent_team/       ← Agent-team source code
  │     ├── prompts/              ← PRD files + config files + this plan
  │     │     ├── BUILD1_PRD.md
  │     │     ├── BUILD2_PRD.md
  │     │     ├── BUILD3_PRD.md
  │     │     ├── RUN4_PRD.md
  │     │     ├── config_build1.yaml
  │     │     ├── config_build2.yaml
  │     │     ├── config_build3.yaml
  │     │     └── config_run4.yaml
  │     └── tests/
  │
  ├── super-team/                 ← BUILD TARGET for Build 1 + Build 3 + Run 4
  │     ├── (empty initially)
  │     ├── (Build 1 creates: src/architect/, src/contract_engine/, src/codebase_intelligence/, src/shared/)
  │     ├── (Build 3 adds:   src/super_orchestrator/, src/integrator/, src/quality_gate/, src/build3_shared/)
  │     └── (Run 4 adds:     src/run4/, tests/run4/)
  │
  └── agent-team-v15/             ← BUILD TARGET for Build 2 (copy of claude-agent-team)
        ├── src/agent_team/       ← Gets modified by Build 2
        └── tests/
```

---

## 3. How the Agent-Team Works

### Pipeline Phases (In Order)

When you run `agent-team --prd <file> --config <file> --cwd <dir>`, it executes these phases:

| # | Phase | What Happens | Key Artifact |
|---|-------|--------------|-------------|
| 0 | Interview (skipped with `--no-interview`) | Collects context | `INTERVIEW.md` |
| 0.25 | Constraint Extraction | Extracts rules from task | — |
| 0.5 | Codebase Map | Maps existing code structure | — |
| 0.6 | Design Reference | Extracts UI requirements | `UI_REQUIREMENTS.md` |
| 1 | PRD Decomposition | Analyzes PRD → milestones + requirements | `MASTER_PLAN.md`, `REQUIREMENTS.md` |
| 1.5 | Tech Research | Queries Context7 for library docs | `TECH_RESEARCH.md` |
| 2 | Milestone Execution | Builds each milestone sequentially | Per-milestone `REQUIREMENTS.md`, `TASKS.md` |
| 3a | Post-Orchestration Scans | Mock data, API contract, UI compliance, DB, integrity scans | Various scan reports |
| 3b | E2E Testing | Backend API tests + frontend tests | `E2E_RESULTS.md` |
| 3c | Browser Testing | Playwright MCP workflows (if enabled) | `WORKFLOW_STATE.md` |
| 4 | Verification | Final contract + lint + type check + build + test | `VERIFICATION.md` |

### Key Files to Monitor

| File | Location | What It Tells You |
|------|----------|-------------------|
| `STATE.json` | `.agent-team/STATE.json` | Current phase, cost, completed phases, milestone progress |
| `MASTER_PLAN.md` | `.agent-team/MASTER_PLAN.md` | Milestone list with health status (HEALTHY/DEGRADED/FAILED) |
| `REQUIREMENTS.md` | `.agent-team/REQUIREMENTS.md` | Requirement checklist — count `[x]` vs `[ ]` for progress |
| `FIX_CYCLE_LOG.md` | `.agent-team/FIX_CYCLE_LOG.md` | Every fix attempt with strategy + result |
| `E2E_COVERAGE_MATRIX.md` | `.agent-team/E2E_COVERAGE_MATRIX.md` | Test coverage tracking |
| `MILESTONE_HANDOFF.md` | `.agent-team/MILESTONE_HANDOFF.md` | Interface contracts between milestones |
| `TECH_RESEARCH.md` | `.agent-team/TECH_RESEARCH.md` | Context7 research results |
| `VERIFICATION.md` | `.agent-team/VERIFICATION.md` | Final verification status |

### How to Check Progress

Run these commands against the `--cwd` target directory to see what's happening:

```bash
# Check current phase and cost
cat <target-dir>/.agent-team/STATE.json 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(f'Phase: {d.get(\"current_phase\",\"?\")}, Cost: ${d.get(\"total_cost\",0):.2f}, Milestones: {len(d.get(\"completed_milestones\",[]))}/{len(d.get(\"milestone_order\",[]))}')"

# Check milestone health in MASTER_PLAN.md
grep -E "Health:|Status:" <target-dir>/.agent-team/MASTER_PLAN.md 2>/dev/null

# Count requirements progress
echo "Checked: $(grep -c '\[x\]' <target-dir>/.agent-team/REQUIREMENTS.md 2>/dev/null || echo 0) / Total: $(grep -c '\[.\]' <target-dir>/.agent-team/REQUIREMENTS.md 2>/dev/null || echo 0)"

# Check if fix cycles are running
wc -l <target-dir>/.agent-team/FIX_CYCLE_LOG.md 2>/dev/null

# List completed milestones
ls <target-dir>/.agent-team/milestones/ 2>/dev/null

# Check total cost from STATE.json
cat <target-dir>/.agent-team/STATE.json 2>/dev/null | python -c "import sys,json; print(f'Cost: \${json.load(sys.stdin).get(\"total_cost\",0):.2f}')"
```

---

## 4. Verification Log Protocol

**You MUST write a verification log for EACH of the 4 runs.** Save them in the `prompts/` directory:

| Run | Log File |
|-----|----------|
| Build 1 | `prompts/VERIFICATION_LOG_BUILD1.md` |
| Build 2 | `prompts/VERIFICATION_LOG_BUILD2.md` |
| Build 3 | `prompts/VERIFICATION_LOG_BUILD3.md` |
| Run 4 | `prompts/VERIFICATION_LOG_RUN4.md` |

### Log Template

Each verification log MUST follow this exact format:

```markdown
# VERIFICATION LOG — Super Agent Team [Build N / Run 4]

**Start Time:** YYYY-MM-DD ~HH:MM UTC+X
**End Time:** YYYY-MM-DD ~HH:MM UTC+X (filled when complete)
**Total Cost:** $XX.XX (from STATE.json)
**Config:** exhaustive depth, PRD mode, milestones enabled
**PRD:** [Brief tech stack description]
**CLI:** agent-team v15.0
**Target Directory:** [absolute path]
**Final Status:** [PASS / PARTIAL / FAIL] (filled when complete)

---

## Pre-Flight Checks

- [x] PF-01: Target directory exists and is in expected state
- [x] PF-02: Config file validated (all settings correct)
- [x] PF-03: .agent-team/ directory clean (no stale state)
- [x] PF-04: ANTHROPIC_API_KEY environment variable set
- [x] PF-05: Disk space sufficient (>5GB free)
- [ ] PF-06: [any additional checks]

---

## Build Timeline

### [HH:MM] — Phase 0: Initialization
- Agent-team started with command: `[exact command]`
- [Observations about startup]

### [HH:MM] — Phase 1: PRD Decomposition
- MASTER_PLAN.md created with N milestones
- [List milestone names]
- [Note any unusual decomposition decisions]

### [HH:MM] — Phase 1.5: Tech Research
- Technologies researched: [list]
- Context7 queries: N
- [Note any research gaps]

### [HH:MM] — Milestone 1: [Name] Starting
- [Observations as milestone progresses]

### [HH:MM] — Milestone 1 Complete
┌──────────────────────────────────────────────────────┐
│ milestone-1: [Name]                                   │
│ Health: [HEALTHY/DEGRADED/FAILED]                     │
│ Requirements: XX/XX MET                               │
│ Review Cycles: N                                      │
│ Cost so far: $XX.XX                                   │
└──────────────────────────────────────────────────────┘

[Repeat for each milestone...]

### [HH:MM] — Post-Orchestration Scans
- Mock Data Scan: [X violations / clean]
- API Contract Scan: [X violations / clean]
- UI Compliance Scan: [X violations / clean / skipped]
- Database Scans: [X violations / clean]
- Integrity Scans: [X violations / clean]
- PRD Reconciliation: [X mismatches / clean]
- Fix passes applied: N

### [HH:MM] — E2E Testing Phase
- Backend tests: [passed X/Y / skipped]
- Frontend tests: [passed X/Y / skipped]
- Fix cycles used: N

### [HH:MM] — Verification Phase
- Lint: [PASS/FAIL]
- Type check: [PASS/FAIL]
- Tests: [PASS X/Y / FAIL]
- Build: [PASS/FAIL]

### [HH:MM] — Run Complete
- Final health: [PASS/PARTIAL/FAIL]
- Total cost: $XX.XX

---

## Findings

### FINDING-001: [Descriptive Title]
**Timestamp:** HH:MM
**Severity:** CRITICAL / HIGH / MEDIUM / LOW / INFO / POSITIVE
**Phase:** [Which phase this was observed in]
**What happened:** [2-5 sentence narrative of what occurred]
**Evidence:** [Specific file paths, line numbers, error messages, or command output]
**Impact:** [What this means for the build or downstream builds]
**Resolution:** [How it was resolved, or "Unresolved — requires manual fix"]

[Repeat for each finding...]

---

## Checkpoint Summary

| ID | Check | Status | Notes |
|----|-------|--------|-------|
| CP-01 | MASTER_PLAN.md has correct milestones | ✅ PASS | N milestones as expected |
| CP-02 | Tech research found all key libraries | ✅ PASS | X/Y detected |
| CP-03 | All milestones reached HEALTHY | ⚠️ PARTIAL | M3 was DEGRADED |
| CP-04 | No mock data violations | ✅ PASS | Clean |
| CP-05 | E2E tests pass | ✅ PASS | X/Y passed |
| CP-06 | Final verification pass | ✅ PASS | All checks green |
| [build-specific checkpoints...] | | | |

---

## Cost Breakdown

| Phase | Cost |
|-------|------|
| Decomposition | $X.XX |
| Tech Research | $X.XX |
| Milestone 1 | $X.XX |
| Milestone 2 | $X.XX |
| [...] | |
| Post-Orchestration Scans | $X.XX |
| E2E Testing | $X.XX |
| **Total** | **$XX.XX** |

---

## Artifacts Produced

| Artifact | Path | Size | Status |
|----------|------|------|--------|
| MASTER_PLAN.md | .agent-team/MASTER_PLAN.md | X KB | Complete |
| REQUIREMENTS.md | .agent-team/REQUIREMENTS.md | X KB | XX/XX checked |
| [list all significant artifacts] | | | |
```

### Monitoring Schedule

**You MUST check on each running build periodically.** Follow this schedule:

| Time Since Start | What to Check | How |
|------------------|---------------|-----|
| 2 minutes | Build started successfully, no immediate crash | Check if process is alive |
| 5 minutes | Phase 1 (decomposition) complete | Check for `MASTER_PLAN.md` existence |
| 10 minutes | Tech research complete, first milestone starting | Read `STATE.json` for `current_phase` |
| Every 10 min after | Milestone progress, cost accumulation | Read `STATE.json` + `MASTER_PLAN.md` |
| When milestones done | Post-orchestration scan results | Check scan output in log |
| When scans done | E2E test results | Check `E2E_RESULTS.md` |
| On completion | Final status, total cost, verification | Read `VERIFICATION.md` + `STATE.json` |

### What to Log at Each Check

At EVERY monitoring check, add a timeline entry to the verification log:

```markdown
### [HH:MM] — Monitoring Check #N
- **Phase:** [current_phase from STATE.json]
- **Cost:** $XX.XX
- **Milestones:** X/Y complete
- **Observations:** [anything notable — errors in agent output, slow progress, retries, etc.]
```

### What Counts as a Finding

Log a FINDING entry for ANY of these:
- Agent errors or crashes (CRITICAL)
- Milestone marked DEGRADED or FAILED (HIGH)
- Fix cycle > 2 retries on same issue (MEDIUM)
- Scan finding > 5 violations of same type (MEDIUM)
- Unexpected files created or missing (MEDIUM)
- Cost exceeding estimate by >50% (HIGH)
- Phase taking 2x expected time (MEDIUM)
- Agent appears stuck (no progress for 10+ minutes) (HIGH)
- Any error message in agent output (severity varies)
- Positive: something worked surprisingly well (POSITIVE)
- Informational: interesting observation, no action needed (INFO)

---

## 5. Phase 0: Preparation

### Step 0.1: Verify Environment

```bash
# Verify ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY | head -c 10
# Should show "sk-ant-..." (first 10 chars)

# Verify agent-team is functional
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"
python -m agent_team --help

# Check disk space (need ~5GB for all builds)
df -h .
```

### Step 0.2: Create Target Directories

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop"

# Create empty super-team directory (Build 1 + Build 3 + Run 4 target)
mkdir -p super-team

# Copy agent-team for Build 2
# IMPORTANT: This creates a SEPARATE copy so Build 2 doesn't modify the running tool
cp -r claude-agent-team agent-team-v15

# CRITICAL: Clean stale state from the copy
rm -rf agent-team-v15/.agent-team
```

### Step 0.3: Verify Config Files Exist

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"
ls -la prompts/config_build1.yaml prompts/config_build2.yaml prompts/config_build3.yaml prompts/config_run4.yaml
ls -la prompts/BUILD1_PRD.md prompts/BUILD2_PRD.md prompts/BUILD3_PRD.md prompts/RUN4_PRD.md
```

All 8 files must exist. If any are missing, STOP and report.

### Step 0.4: Initialize Verification Logs

Create empty verification log files for all 4 runs with the header template (fill in details as each run starts).

---

## 6. Phase 1A: Build 1 — Foundation Services

### What Build 1 Creates
- 3 FastAPI microservices with 20 MCP tools total
- SQLite databases (architect.db, contracts.db, symbols.db)
- ChromaDB vector store for semantic search
- Docker Compose with health checks
- 300+ tests

### Tech Stack to Watch For
tree-sitter 0.25.2, ChromaDB 1.5.0, NetworkX 3.6.1, FastAPI 0.129.0, MCP SDK >=1.25, Schemathesis 4.10.1, prance 25.4.8.0, pydantic-settings >=2.1.0

### Command

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"

python -m agent_team \
  --prd prompts/BUILD1_PRD.md \
  --config prompts/config_build1.yaml \
  --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" \
  --no-interview
```

### Build 1 Specific Checkpoints

| ID | Checkpoint | When to Check | Pass Criteria |
|----|-----------|---------------|---------------|
| B1-CP-01 | MASTER_PLAN.md has 8 milestones (M1-M8) | After Phase 1 | Exactly 8 milestones listed |
| B1-CP-02 | Tech research finds tree-sitter, ChromaDB, NetworkX, MCP SDK | After Phase 1.5 | All 4 detected in TECH_RESEARCH.md |
| B1-CP-03 | M1 creates pyproject.toml + shared models | After M1 | `src/shared/models/` exists with architect.py, contracts.py, codebase.py |
| B1-CP-04 | M2 creates Architect service | After M2 | `src/architect/main.py` + `mcp_server.py` exist |
| B1-CP-05 | M3 creates Contract Engine | After M3 | `src/contract_engine/main.py` + `mcp_server.py` exist |
| B1-CP-06 | M5/M6 creates Codebase Intelligence | After M5+M6 | `src/codebase_intelligence/main.py` + `mcp_server.py` exist |
| B1-CP-07 | M7 creates MCP servers for Architect + Contract Engine | After M7 | MCP tools registered correctly |
| B1-CP-08 | M8 creates Docker Compose + integration tests | After M8 | `docker-compose.yml` exists with 3 services |
| B1-CP-09 | No mock data violations | After scans | Mock data scan returns 0 violations |
| B1-CP-10 | Cross-milestone dependency handled (M5→M6 ChromaDB stub) | During M5 | SemanticIndexer stub logged, replaced in M6 |

### Build 1 Known Risks
1. **tree-sitter version sensitivity** — Must use 0.25.x API (QueryCursor, dict return). Tech research should catch this.
2. **ChromaDB M5/M6 dependency** — M5 stubs SemanticIndexer, M6 implements it. Watch for cross-milestone wiring.
3. **3 separate SQLite databases** — Each service has its own DB. Ensure no accidental sharing.

---

## 7. Phase 1B: Build 2 — Builder Fleet Upgrade

### What Build 2 Creates
- MCP client wrappers (ContractEngineClient, CodebaseIntelligenceClient, ArchitectClient)
- Agent Teams abstraction layer (AgentTeamsBackend)
- Claude Code hooks manager
- CLAUDE.md generator for 5 roles
- CONTRACT-001..004 quality scans
- All backward-compatible with v14.0

### CRITICAL: Build 2 Modifies Existing Code
Unlike Build 1 (fresh directory), Build 2 MODIFIES the agent-team codebase. It will edit `cli.py`, `config.py`, `agents.py`, and create new files. This is why we run it on a COPY.

### Command

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"

python -m agent_team \
  --prd prompts/BUILD2_PRD.md \
  --config prompts/config_build2.yaml \
  --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\agent-team-v15" \
  --no-interview
```

### Build 2 Specific Checkpoints

| ID | Checkpoint | When to Check | Pass Criteria |
|----|-----------|---------------|---------------|
| B2-CP-01 | MASTER_PLAN.md has 6 milestones (M1-M6) | After Phase 1 | Exactly 6 milestones |
| B2-CP-02 | M1 creates agent_teams_backend.py | After M1 | File exists with ExecutionBackend protocol |
| B2-CP-03 | M2 creates contract_client.py wrapping 6 of 9 CE tools | After M2 | ContractEngineClient class with 6 methods |
| B2-CP-04 | M3 creates codebase_client.py wrapping all 7 CI tools | After M3 | CodebaseIntelligenceClient with 7 methods |
| B2-CP-05 | M4 wires everything into cli.py | After M4 | cli.py modified with MCP client integration |
| B2-CP-06 | M5 adds CONTRACT-001..004 scans | After M5 | contract_scanner.py exists |
| B2-CP-07 | M6 backward compatibility verified | After M6 | All v14.0 tests still pass |
| B2-CP-08 | mcp_clients.py filename consistent (plural) | After M4 | No `mcp_client.py` (singular) anywhere |
| B2-CP-09 | Config uses `_dict_to_config()` tuple return correctly | After M4 | All callers unpack (config, overrides) |

### Build 2 Known Risks
1. **Meta-circularity** — Build 2 upgrades the agent-team. The agent writing the code IS the agent-team. Watch for self-referential confusion.
2. **Backward compatibility** — All new features default disabled. Existing tests must pass unchanged.
3. **Filename consistency** — PRD had `mcp_client.py` vs `mcp_clients.py` inconsistency (fixed in PRD, but verify in output).

---

## 8. Checkpoint 1: Verify Build 1 + Build 2

**Do NOT proceed to Build 3 until both builds pass these checks.**

### Verify Build 1

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team"

# 1. Check project structure exists
ls src/architect/main.py src/contract_engine/main.py src/codebase_intelligence/main.py

# 2. Run tests
python -m pytest tests/ -q 2>&1 | tail -5

# 3. Check Docker Compose file exists and is valid
cat docker-compose.yml | head -20

# 4. Try starting services (optional but recommended)
docker compose up -d
sleep 30
curl -s http://localhost:8001/api/health && echo " Architect OK"
curl -s http://localhost:8002/api/health && echo " Contract Engine OK"
curl -s http://localhost:8003/api/health && echo " Codebase Intel OK"
docker compose down
```

**Pass Criteria:**
- [ ] All 3 service directories exist with main.py + mcp_server.py
- [ ] Tests pass (allow some warnings)
- [ ] docker-compose.yml has 3 services defined
- [ ] (Optional) Health endpoints return 200

### Verify Build 2

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\agent-team-v15"

# 1. Check new files exist
ls src/agent_team/agent_teams_backend.py src/agent_team/contract_client.py src/agent_team/codebase_client.py

# 2. Run full test suite (MUST include all v14.0 tests passing)
python -m pytest tests/ -q 2>&1 | tail -5

# 3. Verify backward compat — help still works
python -m agent_team --help
```

**Pass Criteria:**
- [ ] New files created (agent_teams_backend.py, contract_client.py, codebase_client.py, etc.)
- [ ] ALL existing tests still pass (zero regressions)
- [ ] CLI help command works

### If Issues Found
- Log each issue as a FINDING in the respective verification log
- Attempt fix via `agent-team resume` if the issue is with incomplete generation
- If fundamental issues exist (wrong project structure, tests crashing), re-run the build after clearing `.agent-team/`

---

## 9. Phase 2: Build 3 — Integrator + Quality Gate + Super Orchestrator

### CRITICAL: Clean Stale State First!

```bash
# Build 1 left .agent-team/ in super-team/ — this MUST be removed!
# Without this, Build 3 will load Build 1's MASTER_PLAN.md and use wrong milestones
rm -rf "C:\Users\Omar Khaled\OneDrive\Desktop\super-team\.agent-team"
```

**If you forget this step, Build 3 will try to resume Build 1's milestones. This is a known gotcha documented in agent-team memory.**

### What Build 3 Creates (ON TOP of Build 1)
- `src/super_orchestrator/` — Async state machine pipeline (~3,850 LOC)
- `src/integrator/` — Docker, Traefik, Pact, Schemathesis (~6,100 LOC)
- `src/quality_gate/` — 4-layer quality scanning (~5,500 LOC)
- `src/build3_shared/` — Build 3's own shared module (avoids collision with Build 1's `src/shared/`)
- `docker/traefik/` — Traefik API gateway configuration
- 8 CLI commands: init, plan, build, integrate, verify, run, status, resume

### Command

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"

python -m agent_team \
  --prd prompts/BUILD3_PRD.md \
  --config prompts/config_build3.yaml \
  --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" \
  --no-interview
```

### Build 3 Specific Checkpoints

| ID | Checkpoint | When to Check | Pass Criteria |
|----|-----------|---------------|---------------|
| B3-CP-01 | PRD was chunked (106KB > 80KB threshold) | After Phase 1 | "PRD chunked" message in output or prd-chunks/ dir exists |
| B3-CP-02 | MASTER_PLAN.md has 7 milestones (M1-M7), NOT Build 1's 8 | After Phase 1 | 7 milestones with correct Build 3 names |
| B3-CP-03 | Tech research finds pact-python, schemathesis, transitions, Typer, Traefik | After Phase 1.5 | All detected in TECH_RESEARCH.md |
| B3-CP-04 | Build 1 directories untouched | After M1 | `src/shared/`, `src/architect/`, `src/contract_engine/`, `src/codebase_intelligence/` unchanged |
| B3-CP-05 | build3_shared used (NOT shared/) for Build 3 models | After M1 | `src/build3_shared/` exists, NO modifications to `src/shared/` |
| B3-CP-06 | M2/M3 parallelizable annotation present | During M2 | M2 or M3 description mentions parallel capability |
| B3-CP-07 | State machine uses transitions AsyncMachine | After M1 | `state_machine.py` imports from transitions |
| B3-CP-08 | CLI has 8 commands (not 6) | After M6 | Typer app registers init, plan, build, integrate, verify, run, status, resume |
| B3-CP-09 | pyproject.toml EXTENDED not overwritten | After M1 | Build 1's dependencies still present in pyproject.toml |
| B3-CP-10 | docker-compose.yml EXTENDED not overwritten | After completion | Build 1's 3 services still in docker-compose.yml alongside Build 3 additions |

### Build 3 Known Risks
1. **LARGEST BUILD** — 106KB PRD, will be chunked. Watch for cross-chunk context loss.
2. **Directory collision** — Must use `build3_shared/`, not `shared/`. If it overwrites Build 1's shared/, that's a CRITICAL finding.
3. **pyproject.toml merge** — Build 3 needs to ADD dependencies, not replace Build 1's. Verify both sets of deps present.
4. **docker-compose.yml merge** — Same issue. Build 1's 3 services + Build 3's Traefik + postgres + redis must coexist.
5. **pact-python v3 FFI** — Needs Debian-based Docker images (not Alpine). PRD specifies this.

---

## 10. Checkpoint 2: Verify Build 3

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team"

# 1. Verify Build 1 code still intact
ls src/architect/main.py src/contract_engine/main.py src/codebase_intelligence/main.py src/shared/__init__.py

# 2. Verify Build 3 code exists
ls src/super_orchestrator/cli.py src/integrator/docker_orchestrator.py src/quality_gate/gate_engine.py src/build3_shared/__init__.py

# 3. Run ALL tests (Build 1 + Build 3)
python -m pytest tests/ -q 2>&1 | tail -5

# 4. Verify pyproject.toml has BOTH sets of dependencies
grep -c "tree-sitter\|chromadb\|networkx" pyproject.toml   # Build 1 deps (should be > 0)
grep -c "transitions\|typer\|pact-python" pyproject.toml     # Build 3 deps (should be > 0)

# 5. Verify docker-compose.yml has services from both builds
grep -c "architect\|contract.engine\|codebase" docker-compose.yml   # Build 1 services
grep -c "traefik\|postgres\|redis" docker-compose.yml                # Build 3 services
```

**Pass Criteria:**
- [ ] Build 1 source directories intact and unmodified
- [ ] Build 3 source directories created
- [ ] `build3_shared/` used (NOT `shared/`)
- [ ] Tests pass (both Build 1 and Build 3 tests)
- [ ] pyproject.toml has dependencies from both builds
- [ ] docker-compose.yml has services from both builds

---

## 11. Phase 3: Run 4 — End-to-End Verification

### CRITICAL: Clean Stale State Again!

```bash
rm -rf "C:\Users\Omar Khaled\OneDrive\Desktop\super-team\.agent-team"
```

### What Run 4 Does (NOT a Build)
Run 4 is a **verification and remediation framework**. It creates test scripts that:
- Test all 20 SVC wiring points across all 3 builds
- Run a 57-test verification matrix
- Start a 5-tier Docker Compose stack (infra → Build 1 → Traefik → generated services → Run 4 overrides)
- Catalog defects and apply convergence-based fix passes
- Generate `SUPER_TEAM_AUDIT_REPORT.md`

### Configure Run 4 Paths

Before running, update `prompts/config_run4.yaml` to add the `run4` section with correct paths:

```yaml
# Add to the END of config_run4.yaml:
run4:
  build1_project_root: "C:/Users/Omar Khaled/OneDrive/Desktop/super-team"
  build2_project_root: "C:/Users/Omar Khaled/OneDrive/Desktop/agent-team-v15"
  build3_project_root: "C:/Users/Omar Khaled/OneDrive/Desktop/super-team"
  output_dir: ".run4"
```

### Command

```bash
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"

python -m agent_team \
  --prd prompts/RUN4_PRD.md \
  --config prompts/config_run4.yaml \
  --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" \
  --no-interview
```

### Run 4 Specific Checkpoints

| ID | Checkpoint | When to Check | Pass Criteria |
|----|-----------|---------------|---------------|
| R4-CP-01 | MASTER_PLAN.md has 6 milestones (M1-M6) | After Phase 1 | 6 milestones with Run 4 names |
| R4-CP-02 | M1 creates test infrastructure + fixtures | After M1 | `src/run4/config.py`, `tests/run4/conftest.py`, fixture files |
| R4-CP-03 | M2 tests all 17 SVC wiring entries (Build 1 → Build 2) | After M2 | SVC-001 through SVC-017 tested |
| R4-CP-04 | M3 tests Build 2 → Build 3 subprocess wiring | After M3 | SVC-018, SVC-019, SVC-020 tested |
| R4-CP-05 | M4 runs full pipeline E2E | After M4 | 7-phase pipeline test executed |
| R4-CP-06 | M5 catalogs defects and applies fixes | After M5 | Finding dataclass populated |
| R4-CP-07 | M6 generates SUPER_TEAM_AUDIT_REPORT.md | After M6 | Report exists with per-system scores |
| R4-CP-08 | 57-test matrix executed | After M4-M6 | All test IDs (SC-01..SC-07, B1-01..B1-20, etc.) have results |

---

## 12. Final Review

After Run 4 completes, read `SUPER_TEAM_AUDIT_REPORT.md` and log the results:

```bash
cat "C:\Users\Omar Khaled\OneDrive\Desktop\super-team\.run4\SUPER_TEAM_AUDIT_REPORT.md" 2>/dev/null || \
cat "C:\Users\Omar Khaled\OneDrive\Desktop\super-team\SUPER_TEAM_AUDIT_REPORT.md" 2>/dev/null || \
echo "Report not found — check .agent-team/ directory"
```

### Final Status Summary

Create `prompts/FINAL_STATUS.md` with:

```markdown
# Super Agent Team — Final Build Status

| Build | Status | Tests | Cost | Findings |
|-------|--------|-------|------|----------|
| Build 1 | PASS/PARTIAL/FAIL | XX/XX | $XX.XX | X critical, Y high, Z medium |
| Build 2 | PASS/PARTIAL/FAIL | XX/XX | $XX.XX | X critical, Y high, Z medium |
| Build 3 | PASS/PARTIAL/FAIL | XX/XX | $XX.XX | X critical, Y high, Z medium |
| Run 4  | PASS/PARTIAL/FAIL | XX/XX | $XX.XX | X critical, Y high, Z medium |
| **Total** | | | **$XX.XX** | |

## Open Issues
[Any unresolved findings from all 4 verification logs]

## Audit Report Summary
[Key metrics from SUPER_TEAM_AUDIT_REPORT.md]
```

---

## 13. Troubleshooting Guide

### Agent-Team Crashes During a Build

```bash
# Check the last state
cat <target-dir>/.agent-team/STATE.json | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"

# Resume from where it left off
cd "C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team"
python -m agent_team resume
```

### Build 3 Shows Build 1's Milestones

You forgot to delete `.agent-team/` between builds. Fix:
```bash
rm -rf "C:\Users\Omar Khaled\OneDrive\Desktop\super-team\.agent-team"
# Re-run Build 3
```

### Build 3 Overwrites Build 1's pyproject.toml

This is a CRITICAL finding. Fix:
1. Log it as FINDING with severity CRITICAL
2. Use git to check the diff: `cd super-team && git diff pyproject.toml`
3. Manually merge Build 1's dependencies back
4. Consider running Build 3 again with a note in the task about preserving Build 1 deps

### Cost Exceeds Budget

```bash
# Check current cost
cat <target-dir>/.agent-team/STATE.json | python -c "import sys,json; print(f'Cost: \${json.load(sys.stdin).get(\"total_cost\",0):.2f}')"
```

If cost exceeds the config's `max_budget_usd`, the agent-team will stop. You can:
1. Resume with a higher budget in the config
2. Accept partial results and move to the next build

### Agent Appears Stuck (No Progress for 15+ Minutes)

1. Check STATE.json for `current_phase` — is it changing?
2. Check if the sub-orchestrator process is alive
3. Log as FINDING-xxx with severity HIGH
4. If truly stuck, interrupt (Ctrl+C) and resume — the agent-team saves state

### Tests Fail After Build 3

Build 3 may have broken Build 1 code. Check:
1. Are the failures in Build 1's test files or Build 3's?
2. Did Build 3 modify any Build 1 source files? (`git diff` or compare timestamps)
3. Did Build 3 overwrite shared configuration files?

---

## 14. FAQ

### Q: Can I run Build 1 and Build 2 simultaneously?
**Yes.** They are completely independent — different PRDs, different target directories, different tech stacks. If you have two terminals and API budget, run them in parallel.

### Q: Do I need Build 1 services RUNNING when building Build 3?
**No.** During BUILD TIME, the agent-team just generates code. Build 3's code has lazy imports (INT-006) and doesn't need Build 1 services live. The generated code won't be EXECUTED during the build — only written to disk.

### Q: Why not use the upgraded agent-team (Build 2 output) for Build 3?
Build 2 adds RUNTIME features (MCP clients, agent teams) that matter when the Super Agent Team OPERATES, not when building it. The current agent-team v14+ is perfectly capable of generating all the code. Using an untested upgraded version introduces risk.

### Q: What if a milestone fails?
The agent-team has review recovery loops (up to N retries per milestone). If a milestone is marked DEGRADED, the pipeline continues but logs the issue. If marked FAILED, the pipeline may stop. Log the failure as a FINDING and assess whether to resume or re-run.

### Q: What's the total estimated cost?
| Build | Cost | Time |
|-------|------|------|
| Build 1 | $25-40 | 30-60 min |
| Build 2 | $20-35 | 25-45 min |
| Build 3 | $35-50 | 45-75 min |
| Run 4 | $15-25 | 20-40 min |
| **Total** | **$95-150** | **2-3.5 hours** |

### Q: Why delete .agent-team/ between builds in the same directory?
The `.agent-team/` directory contains `MASTER_PLAN.md` with milestone definitions from the PREVIOUS build. If Build 3 sees Build 1's `MASTER_PLAN.md`, it will try to resume Build 1's milestones instead of starting Build 3's milestones. Always clean between different PRD runs in the same directory.

### Q: What does the monitoring session need to have access to?
- The agent-team source directory (`claude-agent-team/`)
- All target directories (`super-team/`, `agent-team-v15/`)
- Ability to run bash commands (to check STATE.json, run tests, etc.)
- Write access to `prompts/` for verification logs

### Q: What's the recommended monitoring interval?
Check every 5-10 minutes during active milestone execution. Check immediately when:
- A milestone completes (to log the status box)
- Post-orchestration scans start (to capture scan results)
- The build completes (to capture final status)
- You notice the agent has been on the same milestone for >20 minutes

---

## Execution Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: PREPARATION                                           │
│   1. mkdir super-team                                          │
│   2. cp -r claude-agent-team agent-team-v15                    │
│   3. rm -rf agent-team-v15/.agent-team/                        │
│   4. Verify env vars, config files, disk space                 │
│   5. Initialize 4 verification log files                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│ PHASE 1A        │             │ PHASE 1B        │
│ Build 1         │  PARALLEL   │ Build 2         │
│ → super-team/   │  (optional) │ → agent-team-v15│
│ (empty dir)     │             │ (copy)          │
│ 8 milestones    │             │ 6 milestones    │
│ ~$30, ~45min    │             │ ~$25, ~35min    │
│                 │             │                 │
│ Monitor q5-10m  │             │ Monitor q5-10m  │
│ Write VER LOG 1 │             │ Write VER LOG 2 │
└────────┬────────┘             └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         ▼
              ┌─────────────────────┐
              │ CHECKPOINT 1        │
              │ ☐ B1 tests pass     │
              │ ☐ B1 services start │
              │ ☐ B2 tests pass     │
              │ ☐ B2 backward compat│
              │ Log results in VLs  │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ CLEAN STALE STATE   │
              │ rm -rf super-team/  │
              │         .agent-team/│
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ PHASE 2: Build 3    │
              │ → super-team/       │
              │ (on top of Build 1) │
              │ 7 milestones        │
              │ ~$40, ~60min        │
              │                     │
              │ Monitor q5-10m      │
              │ Write VER LOG 3     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ CHECKPOINT 2        │
              │ ☐ B1 code intact    │
              │ ☐ B3 code created   │
              │ ☐ build3_shared/ ok │
              │ ☐ pyproject merged  │
              │ ☐ compose merged    │
              │ ☐ All tests pass    │
              │ Log results in VL3  │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ CLEAN STALE STATE   │
              │ rm -rf super-team/  │
              │         .agent-team/│
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ PHASE 3: Run 4      │
              │ → super-team/       │
              │ (verification)      │
              │ 6 milestones        │
              │ ~$20, ~30min        │
              │                     │
              │ Monitor q5-10m      │
              │ Write VER LOG 4     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ FINAL REVIEW        │
              │ Read AUDIT REPORT   │
              │ Write FINAL_STATUS  │
              │ Compile all VER LOGs│
              └─────────────────────┘
```

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| **Run Build 1** | `python -m agent_team --prd prompts/BUILD1_PRD.md --config prompts/config_build1.yaml --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" --no-interview` |
| **Run Build 2** | `python -m agent_team --prd prompts/BUILD2_PRD.md --config prompts/config_build2.yaml --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\agent-team-v15" --no-interview` |
| **Run Build 3** | `python -m agent_team --prd prompts/BUILD3_PRD.md --config prompts/config_build3.yaml --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" --no-interview` |
| **Run Run 4** | `python -m agent_team --prd prompts/RUN4_PRD.md --config prompts/config_run4.yaml --cwd "C:\Users\Omar Khaled\OneDrive\Desktop\super-team" --no-interview` |
| **Check progress** | `cat <dir>/.agent-team/STATE.json \| python -c "import sys,json; d=json.load(sys.stdin); print(f'Phase: {d[\"current_phase\"]}, Cost: \${d[\"total_cost\"]:.2f}')"` |
| **Resume after crash** | `python -m agent_team resume` |
| **Clean between runs** | `rm -rf <dir>/.agent-team` |
