# Finding 2: Context7 Research Phase Enhancement — Implementation Report

> Generated: 2026-02-14
> Implementer: impl-finding2 agent
> Status: COMPLETE — 0 regressions, 5472 tests passing

---

## Design Rationale

### Problem
Sub-agents (code-writer, architect, etc.) have NO access to Context7 MCP servers due to the SDK's architectural constraint (`AgentDefinition` only carries `tools`, not `mcp_servers`). The v14.0 tech research phase was limited to:
1. Generic version-lookup queries ("React v19 setup and project structure")
2. A single global research pass injected identically into ALL milestones
3. No instructions for milestone executors to use Context7 during execution

### Solution: 3 Enhancements

**Enhancement 1: Expanded Research Queries** — Generate richer queries beyond basic version lookups: best practices, anti-patterns, PRD-feature-aware queries (file upload, auth, real-time, etc.), and cross-technology integration queries (Angular + ASP.NET Core CORS, Prisma + NestJS migration workflow, etc.).

**Enhancement 2: Per-Milestone Research Context** — Parse each milestone's REQUIREMENTS.md for technology references, cross-reference with detected tech stack, and generate milestone-specific research queries. These are injected as actionable suggestions for the milestone executor to look up via Context7 during execution.

**Enhancement 3: Milestone Executor Context7 Instructions** — Since milestone executors run as sub-orchestrators with MCP access, add explicit instructions telling them to USE Context7 proactively during execution. Also add Context7 usage instructions to the standard-mode orchestrator prompt.

---

## Changes Made

### File 1: `src/agent_team/config.py`

**New fields on `TechResearchConfig`** (lines 421-422):
```python
expanded_queries: bool = True    # Generate expanded best-practice/integration queries
max_expanded_queries: int = 4    # Extra queries per technology beyond basic version query
```

**Updated `_dict_to_config`** (lines 1248-1250, 1270-1275):
- Added `expanded_queries` and `max_expanded_queries` to the TechResearchConfig constructor
- Added validation: `max_expanded_queries >= 0`

**Depth gating**: No new depth gating needed — expanded queries are controlled by the `expanded_queries` bool (default True). When `quick` depth disables tech research entirely (`enabled=False`), expanded queries are also disabled.

### File 2: `src/agent_team/tech_research.py`

**New constants** (after line 551):
- `_EXPANDED_QUERY_TEMPLATES`: 4 templates for best-practice/anti-pattern/code-example queries
- `_PRD_FEATURE_QUERY_MAP`: 25 PRD feature keywords mapped to domain-specific query templates (file upload, auth, real-time, WebSocket, Excel, PDF, email, notification, pagination, search, drag-and-drop, charts, dashboard, forms, tables, role-based access, caching, queues, i18n)
- `_INTEGRATION_QUERY_TEMPLATES`: Cross-technology integration queries keyed by frozenset category pairs:
  - frontend_framework + backend_framework: HTTP client, CORS, proxy
  - backend_framework + orm: ORM integration, migration workflow
  - frontend_framework + ui_library: component integration, theming
  - backend_framework + database: connection setup, pooling

**New function: `build_expanded_research_queries()`** (~80 lines):
- Parameters: `stack`, `prd_text`, `max_expanded_per_tech`
- Produces 3 types of queries:
  1. Best-practice queries per technology (from `_EXPANDED_QUERY_TEMPLATES`)
  2. PRD-feature-aware queries (scans `prd_text` for keywords from `_PRD_FEATURE_QUERY_MAP`)
  3. Cross-technology integration queries (matches category pairs from `_INTEGRATION_QUERY_TEMPLATES`)
- Returns `list[tuple[str, str]]` (library_name, query)

**New function: `build_milestone_research_queries()`** (~40 lines):
- Parameters: `milestone_title`, `milestone_requirements`, `tech_stack`
- Cross-references milestone text against tech stack for relevant technologies
- Falls back to framework-level techs (frontend + backend) if no explicit mentions
- Generates milestone-scoped PRD-feature queries
- Capped at 8 queries per milestone
- Returns `list[tuple[str, str]]` (library_name, query)

### File 3: `src/agent_team/agents.py`

**New parameter on `build_milestone_execution_prompt()`** (line 2171):
```python
milestone_research_content: str = "",
```

**New injection block: Milestone-Specific Research** (after tech_research_content injection):
```
[MILESTONE-SPECIFIC TECH RESEARCH -- TARGETED FOR THIS MILESTONE]
The following documentation was researched specifically for THIS milestone's
technology needs. Prioritize these patterns over generic research above.
{milestone_research_content}
```

**New injection block: Context7 Research During Execution** (always present in milestone prompt):
```
[CONTEXT7 RESEARCH DURING EXECUTION]
You have access to Context7 MCP tools for looking up current library documentation.
USE THEM proactively during this milestone execution:

When to use Context7:
1. Before implementing ANY library API call — verify the correct method signature
2. When encountering an unfamiliar library pattern — look up the documentation
3. When writing configuration files — verify the correct config format and options
4. When writing tests — look up the testing framework's current API
5. When a code-writer reports an error related to a library — research the fix

How to use Context7:
1. Call `mcp__context7__resolve-library-id` with the library name
2. Call `mcp__context7__query-docs` with the resolved ID and your specific question
3. Use the results to write CORRECT code or inject into sub-agent task context

DO NOT:
- Guess at API signatures from training data when Context7 can verify them
- Use deprecated patterns when current documentation is available
- Skip the lookup because you think you already know the answer
```

**New injection in `build_orchestrator_prompt()`** (after tech_research_content):
```
[CONTEXT7 — LIVE DOCUMENTATION ACCESS]
You have access to Context7 MCP tools for querying library documentation:
1. `mcp__context7__resolve-library-id` — resolve a library name to Context7 ID
2. `mcp__context7__query-docs` — query documentation for a resolved library

USE THESE TOOLS when:
- A code-writer reports an error related to a library API
- You need to verify the correct API signature for a specific library version
- Integration between two technologies needs clarification
- A reviewer flags a pattern that may be outdated or incorrect

INJECT results into sub-agent task context when delegating implementation.
```

### File 4: `src/agent_team/cli.py`

**Updated import in `_run_tech_research()`** (line 744):
- Added `build_expanded_research_queries` to imports

**Expanded query integration** (after line 773):
```python
if config.tech_research.expanded_queries:
    expanded = build_expanded_research_queries(
        stack=stack,
        prd_text=prd_text,
        max_expanded_per_tech=config.tech_research.max_expanded_queries,
    )
    queries.extend(expanded)
```

**Tech stack preservation** (line 1089):
```python
_detected_tech_stack: list = []  # Preserved for per-milestone research queries
```
And after tech_result is available:
```python
_detected_tech_stack = tech_result.stack
```

**Per-milestone research generation** (before `build_milestone_execution_prompt` call):
- Reads milestone's REQUIREMENTS.md
- Calls `build_milestone_research_queries()` with milestone title + requirements + detected stack
- Formats queries as actionable suggestions for Context7 lookup
- Passes `ms_research_content` to `build_milestone_execution_prompt()`

---

## Config Defaults and Depth Gating

| Config Field | Default | Quick | Standard | Thorough | Exhaustive |
|---|---|---|---|---|---|
| `tech_research.enabled` | True | False | True | True | True |
| `tech_research.expanded_queries` | True | N/A (disabled) | True | True | True |
| `tech_research.max_expanded_queries` | 4 | N/A | 4 | 4 | 4 |
| `tech_research.max_queries_per_tech` | 4 | N/A | 2 | 4 | 6 |

Expanded queries follow the same enable/disable pattern as tech research itself. When tech research is disabled (quick depth), expanded queries are never generated.

---

## Integration with Existing Tech Research Flow

```
Phase 1.5: _run_tech_research()
  |
  +-- 1. detect_tech_stack()
  |     → saves stack as _detected_tech_stack for per-milestone use
  |
  +-- 2. build_research_queries()            [EXISTING - unchanged]
  |     → basic category-specific queries
  |
  +-- 2b. build_expanded_research_queries()  [NEW - Enhancement 1]
  |     → best practices, PRD-feature, cross-tech integration queries
  |     → appended to basic queries list
  |
  +-- 3. Research sub-orchestrator runs ALL queries via Context7
  |
  +-- 4. extract_research_summary() → tech_research_content
  |
  Phase 2: Per-Milestone Execution Loop
  |
  +-- For each milestone:
  |     +-- build_milestone_research_queries()  [NEW - Enhancement 2]
  |     |     → milestone-specific queries from REQUIREMENTS.md
  |     |     → injected as ms_research_content
  |     |
  |     +-- build_milestone_execution_prompt()
  |           → tech_research_content (global)
  |           → milestone_research_content (per-milestone)  [NEW]
  |           → Context7 live research instructions          [NEW - Enhancement 3]
```

---

## Zero Regression Guarantees

1. **All existing parameters preserved**: `build_milestone_execution_prompt()` and `build_orchestrator_prompt()` have identical signatures with only additive optional parameters
2. **Basic queries unchanged**: `build_research_queries()` is untouched; expanded queries are appended after it
3. **Config backward compatible**: New fields have defaults (`expanded_queries=True`, `max_expanded_queries=4`) — no YAML changes required
4. **Config loader handles missing fields**: `_dict_to_config` uses `.get()` with defaults for new fields
5. **All crash-isolated**: Per-milestone research wrapped in try/except, Context7 instructions are static text injection
6. **Test results**: 5472 passed, 5 skipped, 0 failed (excluding 2 pre-existing test_mcp_servers.py failures)

---

## New Functions Summary

| Function | File | Purpose |
|---|---|---|
| `build_expanded_research_queries()` | tech_research.py | Best-practice, PRD-aware, cross-tech integration queries |
| `build_milestone_research_queries()` | tech_research.py | Per-milestone targeted research queries |

## New Constants Summary

| Constant | File | Purpose |
|---|---|---|
| `_EXPANDED_QUERY_TEMPLATES` | tech_research.py | 4 generic best-practice query templates |
| `_PRD_FEATURE_QUERY_MAP` | tech_research.py | 25 PRD feature keywords → query templates |
| `_INTEGRATION_QUERY_TEMPLATES` | tech_research.py | Cross-technology integration query templates |
