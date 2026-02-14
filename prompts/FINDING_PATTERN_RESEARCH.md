# Pattern Research: Context7 Integration & Orchestrator Execution

## 1. Context7 Current Integration Analysis

### 1.1 Existing Flow (v14.0)

The current Context7 integration lives in `src/agent_team/tech_research.py` and follows this pipeline:

```
detect_tech_stack()                    -- reads package.json, requirements.txt, csproj, etc.
    |
build_research_queries()               -- generates (library_name, query) tuples
    |                                     per-category templates (frontend, backend, orm, etc.)
    |                                     max_per_tech=4 queries per technology
    |
_run_tech_research() [cli.py:728]      -- spawns a sub-orchestrator ClaudeSDKClient
    |                                     with ONLY Context7 MCP servers
    |                                     prompt = TECH_RESEARCH_PROMPT (formatted)
    |                                     agent writes findings to TECH_RESEARCH.md
    |
parse_tech_research_file()             -- parses ## TechName sections from file
    |
extract_research_summary()             -- compresses to max_chars=6000 for injection
    |
tech_research_content                  -- string injected into prompts via:
                                          build_milestone_execution_prompt()
                                          build_orchestrator_prompt()
```

### 1.2 Research Content

The current research focuses narrowly on:
- Setup and project structure
- Routing/state/middleware patterns
- Common pitfalls and migration gotchas
- Performance optimization and security

It does NOT cover:
- **Integration patterns** (how Angular + ASP.NET Core wire together)
- **Cross-technology patterns** (how Prisma schema maps to Angular services)
- **Code examples** for specific use cases in the PRD
- **Version-specific breaking changes** that are critical for the build

### 1.3 Query Template System

Queries are generated from `_CATEGORY_QUERY_TEMPLATES` dict, keyed by category:
- `frontend_framework`: 4 templates (setup, routing, pitfalls, performance)
- `backend_framework`: 4 templates (API design, auth, error handling, deployment)
- `database`: 4 templates (schema, connections, security, scaling)
- `orm`: 4 templates (schema, queries, relationships, transactions)
- `ui_library`: 4 templates (components, accessibility, customization, performance)
- `testing`: 4 templates (setup, mocking, async, CI/CD)
- `language`: 2 templates (structure, type system)
- `other`: 2 templates (setup, patterns)

**Gap**: No cross-technology integration queries. No PRD-aware queries.

---

## 2. MCP Server Assignment Analysis

### 2.1 Who Has What

| Agent/Session | Context7 | Firecrawl | Playwright | Seq. Thinking |
|---|---|---|---|---|
| **Orchestrator** (main session via `_build_options`) | YES (if config) | YES (if config) | NO | YES (if depth-gated) |
| **Sub-agents** (architect, code-writer, etc.) | **NO** | **NO** | **NO** | **NO** |
| **Tech Research sub-orchestrator** (`_run_tech_research`) | YES (only) | NO | NO | NO |
| **Browser Testing executor** (`_run_browser_workflow_executor`) | YES (if config) | NO | YES | NO |
| **E2E test sub-orchestrator** (`_run_backend_e2e_tests`, etc.) | NO | NO | NO | NO |
| **Fix sub-orchestrators** (`_run_mock_data_fix`, etc.) | NO | NO | NO | NO |
| **PRD reconciliation** (`_run_prd_reconciliation`) | NO | NO | NO | NO |

### 2.2 Critical Comment in agents.py (Line 1870-1873)

```python
# Note: Firecrawl and Context7 MCP tools are NOT included here because
# MCP servers are only available at the orchestrator level and are not
# propagated to sub-agents. The orchestrator calls MCP tools directly
# and passes results to researchers in their task context.
```

**This is the KEY architectural constraint**: Sub-agents (code-writer, architect, code-reviewer, etc.) spawned via the `agents` parameter of `ClaudeAgentOptions` do **NOT** have access to MCP servers. Only the orchestrator session itself can use MCP tools.

### 2.3 Sub-Orchestrator Pattern

Sub-orchestrators are separate `ClaudeSDKClient` sessions (NOT sub-agents). They get their OWN `ClaudeAgentOptions` with their OWN `mcp_servers` dict. This is why:

- `_run_tech_research()` creates a fresh `ClaudeSDKClient` with `get_context7_only_servers()`
- `_run_browser_workflow_executor()` creates a fresh `ClaudeSDKClient` with `get_browser_testing_servers()`

Sub-orchestrators CAN have MCP servers, but they are **independent sessions** — they don't share context with the main orchestrator.

---

## 3. Orchestrator Direct Execution Feasibility

### 3.1 Can the Orchestrator Call Context7 MCP Tools Directly?

**YES.** The orchestrator session (built by `_build_options()`) already includes Context7 MCP servers when configured:

```python
# mcp_servers.py:62-64
context7_cfg = config.mcp_servers.get("context7")
if context7_cfg and context7_cfg.enabled:
    servers["context7"] = _context7_server()
```

These servers are passed to `ClaudeAgentOptions.mcp_servers`, making `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` available as tools in the orchestrator's conversation.

**Current limitation**: The orchestrator prompt (`ORCHESTRATOR_SYSTEM_PROMPT`) does not instruct the orchestrator to use Context7 tools during execution. They're technically available but unused by the orchestrator itself — it only delegates to the Phase 1.5 sub-orchestrator.

### 3.2 Can Sub-Agents (code-writer, architect) Use Context7?

**NO — not directly.** As stated in the code comment at agents.py:1870, MCP servers are not propagated to sub-agents. The `AgentDefinition` only includes `tools` (built-in tools like Read, Write, Edit, Bash, Glob, Grep), not MCP servers.

**Workaround**: The orchestrator can:
1. Call Context7 itself during the conversation
2. Include the results in the task context when delegating to a sub-agent
3. Or, inject research results into the sub-agent's initial prompt (current approach via `tech_research_content`)

### 3.3 Claude Agent SDK Architecture (from Context7 research)

From the Claude Agent SDK docs, the key patterns are:

1. **ClaudeAgentOptions.mcp_servers**: Dict of MCP server configs passed to the main client session
2. **ClaudeAgentOptions.agents**: Dict of AgentDefinition — these define sub-agents with their own prompts, tools, and models, but they do NOT get independent MCP server access
3. **Separate ClaudeSDKClient sessions**: Create independent sessions with their own MCP servers (this is the sub-orchestrator pattern)

The SDK supports **in-process MCP servers** via `create_sdk_mcp_server()` — this could be used to create a custom tool that wraps Context7 queries and makes results available without spawning a full sub-orchestrator.

### 3.4 What Makes Tasks Better for Direct vs Delegated Execution?

**Direct (orchestrator handles it)**:
- Cross-file wiring that requires understanding the full project context
- Integration tasks where the orchestrator has the overview
- Tasks that need MCP tool access (Context7 queries, web scraping)
- Quick lookups that don't need a full agent lifecycle

**Delegated (sub-agent handles it)**:
- File-scoped implementation (write code in a single file)
- Review tasks (read + analyze, no MCP needed)
- Testing tasks (run tests, check output)
- Tasks that benefit from a specialized prompt

---

## 4. Knowledge Injection Patterns

### 4.1 Current Pattern: Pre-computed Static Injection

```
Phase 1.5: _run_tech_research() → TECH_RESEARCH.md → extract_research_summary()
                                                           ↓
                                                   tech_research_content (string)
                                                           ↓
                                        build_milestone_execution_prompt()
                                        build_orchestrator_prompt()
                                                           ↓
                                              [TECH STACK BEST PRACTICES]
                                              ... injected into prompt ...
```

**Pros**:
- Simple, predictable
- One-time cost (research happens once)
- Consistent across all milestones

**Cons**:
- Static — same content for all milestones regardless of relevance
- Limited to 6000 chars (extract_research_summary max_chars)
- Generic queries — not tailored to specific implementation tasks
- No ability to ask follow-up or clarification queries

### 4.2 Proposed Pattern: Milestone-Aware Targeted Injection

Instead of one generic research pass, generate milestone-specific queries:

```
For milestone "Auth & User Management":
  → Query: "ASP.NET Core JWT authentication middleware setup"
  → Query: "Angular HTTP interceptor for JWT token refresh"
  → Query: "Entity Framework Core Identity integration"

For milestone "Tender CRUD & BOQ":
  → Query: "Angular reactive forms with dynamic validation"
  → Query: "Entity Framework Core complex entity relationships"
  → Query: "ASP.NET Core file upload with MinIO"
```

**Implementation options**:
1. **Pre-compute per-milestone** (Phase 1.5 expanded): Run N research sessions, one per milestone
2. **On-demand in orchestrator**: Orchestrator calls Context7 during milestone execution prompt build
3. **Hybrid**: General research once + milestone-specific top-up queries

### 4.3 Proposed Pattern: Orchestrator Real-Time Context7 Access

Add instructions to `ORCHESTRATOR_SYSTEM_PROMPT` enabling the orchestrator to call Context7 during execution:

```
[CONTEXT7 — LIVE DOCUMENTATION ACCESS]
You have access to Context7 MCP tools for querying library documentation:
1. mcp__context7__resolve-library-id — resolve a library name to Context7 ID
2. mcp__context7__query-docs — query documentation for a resolved library

USE THESE TOOLS when:
- A code-writer reports an error related to a library API
- You need to verify the correct API signature for a specific library version
- Integration between two technologies needs clarification
- A reviewer flags a pattern that may be outdated

INJECT results into sub-agent task context when delegating.
```

### 4.4 Format Comparison

| Format | Token Cost | Relevance | Freshness |
|---|---|---|---|
| Static injection (current) | ~1500-2000 tokens per prompt | Low-Medium | Stale after Phase 1.5 |
| Milestone-specific pre-compute | ~800-1200 tokens per prompt | High | Fresh per milestone |
| On-demand orchestrator | Variable | Very High | Real-time |
| Hybrid (pre-compute + on-demand) | ~1000 + variable | Highest | Best |

---

## 5. Research Expansion Opportunities

### 5.1 Cross-Technology Integration Queries

Current gap: No queries for how technologies work TOGETHER. Add:

```python
_INTEGRATION_QUERY_TEMPLATES = {
    ("Angular", "ASP.NET Core"): [
        "Angular HTTP client calling ASP.NET Core API endpoints",
        "Angular proxy configuration for ASP.NET Core development",
        "CORS configuration between Angular and ASP.NET Core",
    ],
    ("React", "Express"): [
        "React fetch/axios calling Express API routes",
        "React proxy setup for Express backend",
    ],
    ("Prisma", "Next.js"): [
        "Prisma with Next.js App Router server actions",
        "Prisma client initialization in Next.js",
    ],
}
```

### 5.2 PRD-Aware Queries

Parse the PRD/REQUIREMENTS.md for domain-specific terms and generate targeted queries:
- If PRD mentions "file upload" → query for file upload patterns in the detected framework
- If PRD mentions "real-time" → query for WebSocket/SSE patterns
- If PRD mentions "export to Excel" → query for Excel library integration

### 5.3 Error-Recovery Queries

When a fix loop fails, the orchestrator could query Context7 for the specific error pattern:
- Parse the error message from the failed sub-agent
- Generate a targeted Context7 query
- Inject the solution into the next fix attempt

---

## 6. Answers to Key Questions

### Q1: Can the orchestrator directly call Context7 MCP tools during its execution?

**YES.** The orchestrator session built by `_build_options()` already includes Context7 MCP servers (line 267: `mcp_servers = get_mcp_servers(config)`). The tools `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` are available. However, the orchestrator prompt does NOT currently instruct it to use them. Adding instructions to `ORCHESTRATOR_SYSTEM_PROMPT` would enable real-time Context7 access.

### Q2: What is the current limitation — do milestone executors (sub-agents) have Context7 MCP access?

**NO.** Milestone executors are fresh `ClaudeSDKClient` sessions built via `_build_options()` — these DO have Context7 MCP servers if configured (same as the main orchestrator). However, the sub-agents WITHIN those sessions (code-writer, architect, etc.) do NOT have MCP access because `AgentDefinition` only carries `tools` (built-in), not `mcp_servers`.

**Clarification**: There are TWO levels:
1. **Milestone executor session** (the ClaudeSDKClient at cli.py:1260) — HAS Context7 MCP access
2. **Sub-agents within that session** (code-writer, architect) — do NOT have Context7 MCP access

The milestone executor session acts as an orchestrator that can call Context7, but its sub-agents cannot.

### Q3: How should we expand Context7 research to cover MORE than "what version of React"?

Three expansion vectors:
1. **Cross-technology integration queries** — how Angular+ASP.NET wire together
2. **PRD-aware queries** — parse PRD features and generate domain-specific queries (file upload, auth, real-time, etc.)
3. **Error-recovery queries** — on-demand Context7 lookups when fix loops encounter framework-specific errors

### Q4: Should Context7 research happen once (upfront) or on-demand per milestone?

**Hybrid approach recommended**:
- **Upfront (Phase 1.5)**: General best practices + cross-technology integration patterns. This content is universal and benefits all milestones.
- **Per-milestone**: Milestone-specific queries based on the milestone's REQUIREMENTS.md. Only query for technologies RELEVANT to that milestone.
- **On-demand**: Error-recovery queries when fix loops fail with framework-specific issues.

### Q5: What's the best format for injecting research results into sub-agent prompts?

Current format (`[TECH STACK BEST PRACTICES -- FROM DOCUMENTATION]` + raw markdown) is adequate but can be improved:

**Recommended format**:
```markdown
[TECH STACK REFERENCE — {milestone_id}]
## {TechName} v{Version}
### MUST USE patterns:
- Pattern 1 with code example
- Pattern 2 with code example
### MUST AVOID:
- Anti-pattern 1
- Anti-pattern 2
### Integration with {OtherTech}:
- Wiring pattern with code example
```

Key improvements:
1. **Structured sections** (MUST USE / MUST AVOID) for actionable guidance
2. **Code examples** — not just descriptions
3. **Integration sections** — cross-technology patterns
4. **Milestone-scoped** — only relevant tech for this milestone

---

## 7. MCP Python SDK Findings

### 7.1 Tool Execution Pattern

From the MCP Python SDK (`/modelcontextprotocol/python-sdk`):
- Tools are defined on MCP servers with `@server.call_tool()` decorator
- Clients call tools via `session.call_tool()` or `session.experimental.call_tool_as_task()`
- The `CallToolResult` contains `content` (text/image blocks) and optional `structured_content`

### 7.2 In-Process MCP Servers (Claude Agent SDK)

The Claude Agent SDK supports `create_sdk_mcp_server()` for in-process tools:
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("my_tool", "Description", {"param": str})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "result"}]}

server = create_sdk_mcp_server(name="custom", tools=[my_tool])
options = ClaudeAgentOptions(mcp_servers={"custom": server})
```

**Potential use**: Create an in-process wrapper around Context7 queries that caches results and provides them in a structured format optimized for prompt injection.

### 7.3 Agent Definition Pattern

```python
agents = {
    "code-reviewer": AgentDefinition(
        description="Reviews code",
        prompt="You are a code reviewer...",
        tools=["Read", "Grep", "Glob"],  # Built-in tools ONLY
        model="sonnet",
    )
}
```

Note: `AgentDefinition.tools` only accepts built-in tool names. MCP tools are NOT available to sub-agents.

---

## 8. Summary of Key Findings

| Finding | Impact | Action |
|---|---|---|
| Orchestrator HAS Context7 but doesn't use it | Medium | Add instructions to ORCHESTRATOR_SYSTEM_PROMPT |
| Sub-agents CANNOT access MCP servers | Architectural constraint | Accept — inject results via prompt |
| Milestone executor sessions CAN access Context7 | Important | They act as mini-orchestrators with MCP access |
| Research is generic, not milestone-aware | High | Add per-milestone query generation |
| No cross-technology integration queries | High | Add integration query templates |
| No error-recovery Context7 queries | Medium | Add on-demand queries in fix loops |
| 6000 char injection limit is arbitrary | Low | Make configurable per-milestone |
| In-process MCP server could wrap Context7 | Exploration | Future — cache + structure layer |
