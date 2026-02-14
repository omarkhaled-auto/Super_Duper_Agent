# Codebase Deep Dive: Orchestration, MCP Servers, and Prompt Injection Analysis

> Generated: 2026-02-14
> Analyst: codebase-analyst agent
> Purpose: Foundation analysis for two critical code changes (Finding 1 & Finding 2)

---

## 1. Orchestrator Flow Map

### Entry Points

The system has two primary execution paths, both dispatched from `main()` in `cli.py` (line ~3742):

```
main()
  |
  +-- load_config() -> (AgentTeamConfig, set[str])
  +-- Interview phase (optional)
  +-- PRD chunking (if >50KB)
  |
  +-- if has_prd:
  |     _run_prd_milestones()         # Phase 1 + 1.5 + 2
  |
  +-- else:
  |     _run_single()                 # Standard mode
  |
  +-- Post-orchestration scans        # Mock, UI, Integrity, DB, API, E2E, Browser
```

### Standard Mode (`_run_single`, line ~554)

Single orchestrator session with full MCP access:

```
_run_single(cwd, task, config, mcp_servers, run_state, constraints, ...)
  |
  +-- build_orchestrator_prompt(task, cwd, ..., tech_research_content, ...)
  +-- build_agent_definitions(config, cwd, ...)
  +-- _build_options(system_prompt, agent_defs, mcp_servers, config)
  +-- ClaudeSDKClient(opts).run()
  +-- _check_convergence_health()
```

### PRD Milestone Mode (`_run_prd_milestones`, line ~887)

Three-phase execution with multiple sessions:

```
_run_prd_milestones(cwd, task, config, mcp_servers, run_state, ...)
  |
  +-- PHASE 1: Decomposition
  |     build_decomposition_prompt()
  |     _build_options(decomp_prompt, NO agents, mcp_servers, config)
  |     ClaudeSDKClient(opts).run()
  |     validate MASTER_PLAN.md created
  |
  +-- PHASE 1.5: Tech Research (if enabled)
  |     _run_tech_research(cwd, config, run_state)
  |     extract_research_summary() -> tech_research_content
  |
  +-- PHASE 2: Per-Milestone Execution Loop
        for each milestone in MASTER_PLAN.md:
          build_milestone_execution_prompt(milestone, ..., tech_research_content, ...)
          build_agent_definitions(config, cwd, ...)
          _build_options(milestone_prompt, agent_defs, mcp_servers, config)
          ClaudeSDKClient(opts).run()
          _check_convergence_health()
          review_recovery_loop (if health != "passed")
```

### Key Observation: Session Isolation

Each milestone gets a **fresh ClaudeSDKClient session**. State is NOT shared between milestone sessions. Continuity is achieved through:
- MASTER_PLAN.md (milestone list + status)
- REQUIREMENTS.md (per-milestone)
- File system artifacts
- `tech_research_content` (injected as text into each prompt)
- `predecessor_context` (handoff data from previous milestones)

---

## 2. Delegation Points (All 12+ Sub-Sessions)

Every point where the system creates a new ClaudeSDKClient session:

### Primary Orchestration Sessions

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 1 | `_run_single()` | cli.py:~554 | ALL (Firecrawl, Context7, ST) | Standard mode orchestration |
| 2 | `_run_prd_milestones()` Phase 1 | cli.py:~930 | ALL | PRD decomposition |
| 3 | `_run_prd_milestones()` Phase 2 (loop) | cli.py:~1100 | ALL | Per-milestone execution |

### Tech Research Session

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 4 | `_run_tech_research()` | cli.py:~728 | Context7 ONLY | Tech stack research via Context7 |

### Recovery/Fix Sub-Orchestrators

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 5 | `_run_review_only()` | cli.py:~3444 | ALL | Review recovery pass |
| 6 | `_run_mock_data_fix()` | cli.py:~4600+ | ALL | Mock data violation fix |
| 7 | `_run_ui_compliance_fix()` | cli.py:~4600+ | ALL | UI compliance violation fix |
| 8 | `_run_integrity_fix()` | cli.py:~4600+ | ALL | Deployment/asset/DB fix |
| 9 | `_run_api_contract_fix()` | cli.py:~4600+ | ALL | API contract violation fix |
| 10 | `_run_e2e_fix()` | cli.py:~4600+ | ALL | E2E test failure fix |

### Browser Testing Sessions

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 11 | `_run_browser_startup_agent()` | cli.py:~4600+ | NONE (Bash only) | Start app process |
| 12 | `_run_browser_workflow_executor()` | cli.py:~4600+ | Playwright + Context7 | Execute browser workflows |
| 13 | `_run_browser_workflow_fix()` | cli.py:~4600+ | ALL | Fix browser test failures |
| 14 | `_run_browser_regression_sweep()` | cli.py:~4600+ | Playwright + Context7 | Re-run all workflows |

### Design Extraction Session

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 15 | Design extraction (Phase 0.6) | cli.py:main() | Firecrawl ONLY | Extract design from URLs |

### PRD Reconciliation Session

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 16 | `_run_prd_reconciliation()` | cli.py:~4600+ | ALL | PRD vs implementation comparison |

### Handoff Generation Session

| # | Function | File:Line | MCP Servers | Purpose |
|---|----------|-----------|-------------|---------|
| 17 | `_generate_handoff_details()` | cli.py:~1300+ | ALL | Milestone handoff document |

---

## 3. MCP Server Assignment

### Server Definitions (mcp_servers.py)

```python
_firecrawl_server()        # Requires FIRECRAWL_API_KEY env var
_context7_server()         # No API key needed, uses @anthropic-ai/context7-mcp@latest
_sequential_thinking_server()  # No API key, uses @anthropic-ai/sequential-thinking-mcp
_playwright_mcp_server()   # No API key, uses @playwright/mcp@latest, headless configurable
```

### Server-to-Session Mapping

| Session Type | Firecrawl | Context7 | Sequential Thinking | Playwright |
|-------------|-----------|----------|---------------------|------------|
| Orchestrator (standard/milestone) | YES (if key) | YES | YES | NO |
| Tech Research | NO | YES | NO | NO |
| Design Extraction | YES (if key) | NO | NO | NO |
| Browser Workflow Executor | NO | YES | NO | YES |
| Browser Regression Sweep | NO | YES | NO | YES |
| Browser Startup Agent | NO | NO | NO | NO |
| Recovery/Fix sub-orchestrators | YES (if key) | YES | YES | NO |

### Server Configuration Functions

| Function | Returns | Used By |
|----------|---------|---------|
| `get_mcp_servers(config)` | Firecrawl + Context7 + ST | Orchestrator, decomposition, milestone execution, fix passes |
| `get_context7_only_servers(config)` | Context7 only | Tech research (`_run_tech_research`) |
| `get_firecrawl_only_servers(config)` | Firecrawl only | Design extraction (Phase 0.6) |
| `get_browser_testing_servers(config)` | Playwright + Context7 | Browser workflow executor, regression sweep |
| `get_research_tools(servers)` | Tool name list | Filters allowed MCP tools for research agents |

### CRITICAL: Sub-Agents Get NO MCP Servers

The `build_agent_definitions()` function in `agents.py` creates `AgentDefinition` objects with:
- `description` (string)
- `instructions` (the prompt)
- `tools` (standard tools like Read, Write, Edit, Bash, Glob, Grep)
- `model` (from config)

**There is NO `mcp_servers` field on AgentDefinition.** MCP servers are passed to `ClaudeAgentOptions` at the session level, meaning only the orchestrator (top-level agent in the session) can call MCP tools. Sub-agents (planner, code-writer, code-reviewer, debugger, etc.) have ZERO access to Context7, Firecrawl, Sequential Thinking, or Playwright.

This is explicitly documented in `ORCHESTRATOR_SYSTEM_PROMPT` Section 6:
> "Sub-agents do NOT have MCP server access — MCP servers are only available at the orchestrator level."

---

## 4. Tech Research Flow (Phase 1.5)

### Full Pipeline

```
_run_tech_research(cwd, config, run_state)
  |
  +-- 1. detect_tech_stack(cwd, task_text)
  |     Parses: package.json, requirements.txt, pyproject.toml, go.mod, *.csproj, Cargo.toml
  |     Also: free-text regex for framework mentions
  |     Returns: list[TechStackEntry] (name, version, category, source)
  |
  +-- 2. build_research_queries(tech_entries, config)
  |     Category-specific templates:
  |       framework -> "setup", "routing", "middleware"
  |       database  -> "connection", "migrations", "queries"
  |       ui        -> "components", "theming", "responsive"
  |       testing   -> "setup", "mocking", "assertions"
  |     Max techs: config.tech_research.max_techs (default 8)
  |     Max queries/tech: config.tech_research.max_queries_per_tech (default 4)
  |     Returns: list[tuple[str, str]] (library_name, query_text)
  |
  +-- 3. Build TECH_RESEARCH_PROMPT
  |     Injects: detected techs + queries
  |     Instructs agent to call:
  |       mcp__context7__resolve-library-id (to get library ID)
  |       mcp__context7__query-docs (to get documentation)
  |     Output: TECH_RESEARCH.md file
  |
  +-- 4. Create Context7-only session
  |     context7_servers = get_context7_only_servers(config)
  |     ClaudeAgentOptions(model, max_turns=50, bypassPermissions, mcp_servers=context7_servers)
  |     ClaudeSDKClient(opts).run()
  |
  +-- 5. Parse results
  |     parse_tech_research_file(cwd) -> TechResearchResult
  |     validate_tech_research(result, tech_entries, config)
  |
  +-- 6. Optional retry (if incomplete + config.retry_on_incomplete)
  |
  +-- 7. Extract summary
        extract_research_summary(result, config.injection_max_chars)
        Returns: compact markdown string (max 6000 chars default)
```

### Research Summary Injection

The `tech_research_content` string is injected into prompts via two functions:

1. **`build_orchestrator_prompt()`** — Standard mode:
   ```python
   if tech_research_content:
       parts.append(f"\n\n## TECH STACK RESEARCH RESULTS\n{tech_research_content}\n")
   ```

2. **`build_milestone_execution_prompt()`** — Milestone mode:
   ```python
   if tech_research_content:
       parts.append(f"\n\n## TECH STACK RESEARCH RESULTS\n{tech_research_content}\n")
   ```

### Depth Gating for Tech Research

From `apply_depth_quality_gating()` in config.py:

| Depth | Tech Research | Max Queries/Tech |
|-------|--------------|-----------------|
| quick | DISABLED | - |
| standard | ENABLED | 2 |
| thorough | ENABLED | 4 (default) |
| exhaustive | ENABLED | 6 |

### Limitations of Current Tech Research

1. **One-shot static injection**: Research runs ONCE in Phase 1.5, results are injected as TEXT into prompts. No live Context7 access during coding.
2. **Sub-agents can't query Context7**: The code-writer sub-agent cannot look up API docs during implementation.
3. **Staleness risk**: If the agent encounters a library not detected in Phase 1.5, it has no way to research it.
4. **Summary truncation**: Results are capped at 6000 chars — large tech stacks may lose detail.
5. **No per-milestone research**: The same summary is injected into ALL milestones, even if they use different subsets of the tech stack.

---

## 5. Prompt Injection Points

### All injection points where dynamic content is inserted into agent prompts:

#### A. Orchestrator-Level Injections (build_orchestrator_prompt / build_milestone_execution_prompt)

| # | Content | Source | Injected Into | Format |
|---|---------|--------|---------------|--------|
| 1 | `tech_research_content` | `extract_research_summary()` | Orchestrator prompt + milestone prompt | `## TECH STACK RESEARCH RESULTS\n{content}` |
| 2 | `ui_requirements_content` | UI_REQUIREMENTS.md file | Orchestrator prompt + milestone prompt | `## UI DESIGN REQUIREMENTS\n{content}` |
| 3 | `predecessor_context` | Previous milestone handoff | Milestone prompt only | `## PREDECESSOR MILESTONE CONTEXT\n{content}` |
| 4 | `codebase_map_summary` | Codebase analysis | Orchestrator prompt + milestone prompt | `## EXISTING CODEBASE MAP\n{content}` |
| 5 | `constraints` | User-specified | Orchestrator prompt + milestone prompt | `## PROJECT CONSTRAINTS\n{content}` |
| 6 | `interview_doc` | INTERVIEW_ANSWERS.md | Orchestrator prompt + milestone prompt | `## CLIENT INTERVIEW\n{content}` |
| 7 | Quality standards | `get_standards_for_agent()` | Per-agent via `build_agent_definitions()` | Embedded in agent instructions |
| 8 | Fix cycle log | FIX_CYCLE_LOG.md | Milestone prompt | `## FIX CYCLE LOG\n{content}` |
| 9 | UI compliance enforcement | Static block | Milestone prompt + code-writer prompt | `[UI COMPLIANCE ENFORCEMENT]` block |
| 10 | Milestone handoff data | MILESTONE_HANDOFF.md | Milestone prompt | `## MILESTONE HANDOFF\n{content}` |

#### B. Agent-Level Injections (in build_agent_definitions)

| # | Agent | Content Injected | Source |
|---|-------|-----------------|--------|
| 11 | code-writer | ZERO MOCK DATA POLICY | Static in CODE_WRITER_PROMPT |
| 12 | code-writer | API CONTRACT COMPLIANCE | Static in CODE_WRITER_PROMPT |
| 13 | code-writer | UI COMPLIANCE POLICY | Static in CODE_WRITER_PROMPT |
| 14 | code-reviewer | Mock data gate | Static in CODE_REVIEWER_PROMPT |
| 15 | code-reviewer | API contract verification | Static in CODE_REVIEWER_PROMPT |
| 16 | code-reviewer | UI compliance duties | Static in CODE_REVIEWER_PROMPT |
| 17 | architect | SVC-xxx exact field schemas | Static in ARCHITECT_PROMPT |
| 18 | architect | Seed data completeness | Static in ARCHITECT_PROMPT |
| 19 | architect | Enum/status registry | Static in ARCHITECT_PROMPT |
| 20 | All agents | Quality standards | `get_standards_for_agent(agent_type)` |

#### C. Sub-Orchestrator Prompt Injections

| # | Sub-Orchestrator | Content Injected |
|---|-----------------|-----------------|
| 21 | Tech research | Detected tech entries + queries |
| 22 | E2E backend tests | Test standards + app type info |
| 23 | E2E frontend tests | Test standards + app type info |
| 24 | E2E fix | Failed test details + fix guidance |
| 25 | Browser workflow executor | Workflow definitions + app URL |
| 26 | Browser fix | Failed workflow details |
| 27 | PRD reconciliation | REQUIREMENTS.md content |
| 28 | Handoff generation | Milestone details + predecessor info |

---

## 6. Integration Task Identification

Based on the analysis, here are the specific code locations that would need modification for the two findings:

### Finding 1: Orchestrator Direct Execution for Complex Integration

**Goal**: Allow the orchestrator to directly execute code instead of always delegating to sub-agents.

**Files to modify**:

1. **`agents.py`** — `ORCHESTRATOR_SYSTEM_PROMPT`
   - Section 3 ("Agent Fleet") defines the delegation model
   - Section 6 ("Research Fleet") defines MCP usage
   - Would need new section/rules for "direct execution mode"
   - The orchestrator currently has standard tools (Read, Write, Edit, Bash, Glob, Grep) in `allowed_tools` via `_build_options()`

2. **`cli.py`** — `_build_options()` (line ~246)
   - Currently: `allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "WebSearch", "WebFetch"]`
   - The orchestrator ALREADY has these tools but is instructed to DELEGATE via sub-agents
   - Key insight: This is a PROMPT change, not a code change — the orchestrator can already use these tools

3. **`config.py`** — New config field
   - `OrchestratorConfig` would need `direct_execution_enabled: bool` or similar
   - Depth gating logic in `apply_depth_quality_gating()`

4. **`agents.py`** — `build_orchestrator_prompt()` and `build_milestone_execution_prompt()`
   - Conditional injection of direct execution instructions

### Finding 2: Context7 Research Phase Injection into Prompts

**Goal**: Make tech research results available to sub-agents during implementation, or allow live Context7 access.

**Approach A: Enhanced Prompt Injection (simpler)**

1. **`tech_research.py`** — `extract_research_summary()`
   - Increase `max_chars` or make per-milestone summaries
   - Add per-technology structured output for targeted injection

2. **`agents.py`** — `build_agent_definitions()`
   - Inject tech research content into code-writer and architect prompts
   - Currently these agents have NO tech research context

3. **`agents.py`** — `CODE_WRITER_PROMPT`
   - Add section for "TECH STACK REFERENCE" with library-specific patterns

**Approach B: Live MCP Access for Sub-Agents (complex)**

1. **`mcp_servers.py`** — New function `get_code_writer_servers()`
   - Return Context7-only servers for code-writer sub-agent

2. **`agents.py`** — `AgentDefinition` changes
   - The Claude SDK `AgentDefinition` would need `mcp_servers` support
   - **BLOCKER**: Current SDK may not support MCP servers on sub-agents — needs verification

3. **`cli.py`** — `_build_options()`
   - Pass MCP servers to specific sub-agents if SDK supports it

**Approach C: Orchestrator-Mediated Research (hybrid)**

1. **`agents.py`** — `ORCHESTRATOR_SYSTEM_PROMPT`
   - Add instruction: "When a sub-agent needs library documentation, USE Context7 yourself and inject the results into the sub-agent's task description"
   - The orchestrator already has Context7 access

2. No code changes needed — purely prompt engineering
   - Risk: Increases orchestrator token usage significantly

---

## 7. Current Limitations

### L1: Sub-Agent MCP Blindness
Sub-agents (code-writer, code-reviewer, architect, debugger) have ZERO MCP access. They cannot:
- Look up library documentation (Context7)
- Search the web for solutions (Firecrawl)
- Use structured reasoning (Sequential Thinking)
- Interact with browsers (Playwright)

**Impact**: Code-writers must rely on training data for library APIs. If tech research missed a library or the summary was truncated, the code-writer has no fallback.

### L2: One-Shot Tech Research
Tech research runs ONCE in Phase 1.5, before any code is written. There is no mechanism to:
- Re-research when new libraries are discovered during coding
- Get deeper docs for a specific API encountered during implementation
- Research libraries that weren't in the initial detection

### L3: Session Isolation
Each milestone gets a fresh session. There is no shared memory between milestones except:
- File system artifacts
- MASTER_PLAN.md status
- `predecessor_context` (handoff data)
- `tech_research_content` (same for all milestones)

### L4: Summary Truncation
`extract_research_summary()` caps output at 6000 chars. For projects with 8+ technologies, each technology gets ~750 chars of documentation — often insufficient for complex APIs.

### L5: No Per-Milestone Research Targeting
The same tech research summary is injected into ALL milestones. A milestone focused on database setup gets the same React component documentation as a milestone focused on frontend UI.

### L6: Orchestrator Delegation Rigidity
The orchestrator is instructed to ALWAYS delegate to sub-agents. There is no "direct execution" mode where the orchestrator can:
- Write code itself when the task is simple
- Combine MCP research + code writing in a single step
- Fix a small issue without spawning a full sub-agent session

### L7: No Feedback Loop for Research Quality
If tech research produces poor results (wrong library versions, missing key APIs), there is no mechanism during coding to:
- Flag research gaps
- Trigger supplementary research
- Update the research summary

### L8: Fix Sub-Orchestrators Get Full MCP but Don't Leverage It
Recovery/fix sub-orchestrators (mock fix, UI fix, API fix, etc.) receive ALL MCP servers via `get_mcp_servers()`, but their prompts don't instruct them to use Context7 for research. They are focused on fixing specific violations, not on researching correct implementations.

---

## Appendix A: _build_options() Anatomy

```python
def _build_options(system_prompt, agent_defs, mcp_servers, config):
    opts_kwargs = {
        "model": config.orchestrator.model,
        "system_prompt": system_prompt,
        "permission_mode": config.orchestrator.permission_mode,
        "max_turns": config.orchestrator.max_turns,
        "agents": agent_defs,                    # Sub-agents (NO MCP)
        "allowed_tools": [
            "Read", "Write", "Edit", "Bash",
            "Glob", "Grep", "Task",
            "WebSearch", "WebFetch"
        ],
    }
    if mcp_servers:
        opts_kwargs["mcp_servers"] = mcp_servers  # MCP goes to orchestrator ONLY
    return ClaudeAgentOptions(**opts_kwargs)
```

## Appendix B: Agent Definitions Structure

```python
# From build_agent_definitions()
{
    "planner": AgentDefinition(
        description="...",
        instructions=PLANNER_PROMPT + standards,
        tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        model=config.worker.model,
    ),
    "code-writer": AgentDefinition(
        description="...",
        instructions=CODE_WRITER_PROMPT + standards,
        tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        model=config.worker.model,
    ),
    "code-reviewer": AgentDefinition(
        description="...",
        instructions=CODE_REVIEWER_PROMPT + standards,
        tools=["Read", "Glob", "Grep"],
        model=config.worker.model,
    ),
    # ... debugger, test-runner, etc.
}
# NOTE: NO mcp_servers field on AgentDefinition
```

## Appendix C: Tech Research Prompt Template (TECH_RESEARCH_PROMPT)

The prompt instructs the research agent to:
1. Call `mcp__context7__resolve-library-id` for each technology
2. Call `mcp__context7__query-docs` with the resolved library ID + query
3. Write results to `TECH_RESEARCH.md` in structured format:
   - `## {Library Name}` sections
   - `### Query: {query}` subsections
   - Code examples and API patterns
   - Version-specific notes

## Appendix D: Post-Orchestration Scan Pipeline Order

```
1. Mock Data Scan          (config.post_orchestration_scans.mock_data_scan)
2. UI Compliance Scan      (config.post_orchestration_scans.ui_compliance_scan)
3. Integrity Scans
   a. Deployment Scan      (config.integrity_scans.deployment_scan)
   b. Asset Scan           (config.integrity_scans.asset_scan)
   c. PRD Reconciliation   (config.integrity_scans.prd_reconciliation)
4. Database Scans
   a. Dual ORM Scan        (config.database_scans.dual_orm_scan)
   b. Default Value Scan   (config.database_scans.default_value_scan)
   c. Relationship Scan    (config.database_scans.relationship_scan)
5. API Contract Scan       (config.post_orchestration_scans.api_contract_scan)
6. E2E Testing Phase       (config.e2e_testing.enabled)
   a. Backend API tests
   b. Frontend Playwright tests
7. Browser Testing Phase   (config.browser_testing.enabled)
   a. App startup
   b. Workflow execution
   c. Fix loop
   d. Regression sweep
```
