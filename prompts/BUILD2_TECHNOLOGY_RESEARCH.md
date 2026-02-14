# BUILD 2 TECHNOLOGY RESEARCH
## Verified API Signatures, Configuration Patterns & Integration Approaches

**Date**: 2026-02-14
**Researcher**: tech-researcher agent
**Sources**: Official Claude Code docs (code.claude.com), Context7 (MCP Python SDK, Claude Code), SUPER_TEAM_RESEARCH_REPORT.md, existing agent-team v14.0 codebase

---

## 1. CLAUDE CODE AGENT TEAMS API

### 1.1 Status & Activation

**Status**: EXPERIMENTAL — disabled by default, requires explicit opt-in.

**Activation**: Set environment variable in settings.json:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Or via environment variable directly:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Related env vars:
- `CLAUDE_CODE_TEAM_NAME` — auto-set on teammates, identifies which team they belong to
- `CLAUDE_CODE_PLAN_MODE_REQUIRED` — auto-set to `true` on teammates that require plan approval (read-only, set by Claude Code at spawn)
- `CLAUDE_CODE_TASK_LIST_ID` — share a task list across sessions (set same ID in multiple instances)

### 1.2 Architecture

**Components**:
- **Team Lead**: The Claude Code instance that spawns teammates. Fixed for the session.
- **Teammates**: Independent Claude Code instances spawned by the lead.
- **Task List**: Shared work items with dependency tracking.
- **Mailbox**: Peer-to-peer messaging between team members.

**Display Modes** (`teammateMode` setting):
| Value | Behavior |
|-------|----------|
| `auto` | Picks split panes in tmux or iTerm2, in-process otherwise |
| `in-process` | All teammates run within the lead's terminal |
| `tmux` | Split panes via tmux |

**CRITICAL LIMITATION**: Split panes NOT supported in: VS Code terminal, Windows Terminal, Ghostty.

### 1.3 Team Configuration

**Config location**: `~/.claude/teams/{team-name}/config.json`
```json
{
  "members": [
    {
      "name": "researcher",
      "agentId": "agent-abc123",
      "agentType": "custom"
    }
  ]
}
```

**Task list location**: `~/.claude/tasks/{team-name}/`

### 1.4 Task System

**Task states**: `pending` -> `in_progress` -> `completed`

**Task claiming**: Uses file locking to prevent race conditions when multiple teammates try to claim the same task.

**Available task tools** (from official docs):
| Tool | Description | Permission Required |
|------|-------------|-------------------|
| `TaskCreate` | Creates a new task in the task list | No |
| `TaskGet` | Retrieves full details for a specific task | No |
| `TaskList` | Lists all tasks with their current status | No |
| `TaskUpdate` | Updates task status, dependencies, details, or deletes tasks | No |

### 1.5 Communication

**SendMessage tool** types:
- `message` — Direct message to a specific teammate (requires `recipient`)
- `broadcast` — Send to ALL teammates (expensive, use sparingly)
- `shutdown_request` — Ask a teammate to gracefully shut down
- `shutdown_response` — Respond to shutdown request (approve/reject)
- `plan_approval_response` — Approve/reject a teammate's plan

### 1.6 Delegate Mode

Activated via Shift+Tab. Restricts the lead to coordination-only work — the lead cannot write code directly and must delegate all implementation to teammates.

### 1.7 Teammate Behavior

- Teammates load: CLAUDE.md, MCP servers, skills automatically
- Teammates do NOT load: Lead's conversation history
- Each teammate has independent context, permissions set at spawn time
- No session resumption for teammates
- No nested teams (a teammate cannot spawn sub-teammates)
- One team per session
- Lead is fixed (cannot be changed mid-session)

### 1.8 Known Limitations (CRITICAL for Build 2 Design)

1. **No session resumption** — if a teammate crashes, it cannot be resumed
2. **No nested teams** — flat hierarchy only
3. **One team per session** — cannot run multiple teams simultaneously
4. **Lead is fixed** — cannot change the team lead mid-session
5. **Permissions set at spawn** — cannot dynamically modify teammate permissions
6. **Split panes not on Windows Terminal** — affects our Windows users

### 1.9 Build 2 Integration Approach

Since agent teams are experimental and have significant limitations, Build 2 MUST:
- Implement an **abstraction layer** over the raw agent teams API
- Provide fallback to the existing Python CLI parallelism when agent teams are unavailable
- Handle teammate crashes gracefully (retry logic)
- NOT depend on split pane display (use in-process mode as default)

---

## 2. CLAUDE CODE HOOKS SYSTEM

### 2.1 Complete Hook Events Reference

| Event | When it fires | Can block? | Exit 2 behavior |
|-------|---------------|-----------|-----------------|
| `SessionStart` | Session begins or resumes | No | Shows stderr to user |
| `UserPromptSubmit` | User submits prompt, before processing | Yes | Blocks prompt processing, erases prompt |
| `PreToolUse` | Before a tool call executes | Yes | Blocks the tool call |
| `PermissionRequest` | When a permission dialog appears | Yes | Denies the permission |
| `PostToolUse` | After a tool call succeeds | Yes | Shows stderr to Claude (tool already ran) |
| `PostToolUseFailure` | After a tool call fails | No | Shows stderr to Claude |
| `Notification` | Claude Code sends a notification | No | Shows stderr to user |
| `SubagentStart` | Subagent is spawned | No | Shows stderr to user |
| `SubagentStop` | Subagent finishes | Yes | Prevents subagent from stopping |
| `Stop` | Claude finishes responding | Yes | Prevents Claude from stopping |
| `TeammateIdle` | Agent team teammate about to go idle | Yes | Prevents teammate from going idle (keeps working) |
| `TaskCompleted` | Task being marked completed | Yes | Prevents task completion |
| `PreCompact` | Before context compaction | No | Shows stderr to user |
| `SessionEnd` | Session terminates | No | Shows stderr to user |

### 2.2 Hook Configuration Schema

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<regex-pattern>",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "timeout": 600,
            "statusMessage": "Running checks...",
            "async": false,
            "once": false
          }
        ]
      }
    ]
  }
}
```

**Hook locations** (in precedence order):
| Location | Scope | Shareable |
|----------|-------|-----------|
| `~/.claude/settings.json` | All projects | No |
| `.claude/settings.json` | Single project | Yes (committed) |
| `.claude/settings.local.json` | Single project | No (gitignored) |
| Managed policy settings | Organization-wide | Yes (admin) |
| Plugin `hooks/hooks.json` | When plugin enabled | Yes |
| Skill/agent frontmatter | While component active | Yes |

### 2.3 Hook Types

#### Command Hooks (`type: "command"`)
Run a shell command. Receives JSON on stdin, returns via exit code + stdout.

| Field | Required | Description |
|-------|----------|-------------|
| `command` | yes | Shell command to execute |
| `async` | no | If `true`, runs in background without blocking |

#### Prompt Hooks (`type: "prompt"`)
Send prompt to a Claude model for single-turn evaluation.

| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | yes | Prompt text. Use `$ARGUMENTS` for hook input JSON |
| `model` | no | Model to use. Defaults to fast model |
| `timeout` | no | Seconds. Default: 30 |

Response schema: `{ "ok": true|false, "reason": "..." }`

#### Agent Hooks (`type: "agent"`)
Spawn a subagent with tool access (Read, Grep, Glob) for multi-turn verification.

| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | yes | Prompt describing what to verify. `$ARGUMENTS` for input |
| `model` | no | Model to use. Defaults to fast model |
| `timeout` | no | Seconds. Default: 60 |

Response schema: same as prompt hooks `{ "ok": true|false, "reason": "..." }`

### 2.4 Hook Input JSON (Common Fields)

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" }
}
```

### 2.5 Hook Output / Decision Control

**Exit codes**:
- `0` — Success, proceed
- `2` — Block the action, feed stderr back as feedback
- Other non-zero — Error, shows stderr

**JSON output patterns**:

PreToolUse decision:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "reason text",
    "updatedInput": { "field": "new value" },
    "additionalContext": "extra info for Claude"
  }
}
```

Stop decision:
```json
{
  "decision": "block",
  "reason": "Must be provided when Claude is blocked from stopping"
}
```

PostToolUse decision:
```json
{
  "decision": "block",
  "reason": "explanation",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "additional info"
  }
}
```

### 2.6 Agent-Teams-Specific Hooks

**TeammateIdle** — fires when a teammate is about to go idle:
```json
{
  "hook_event_name": "TeammateIdle",
  "teammate_name": "researcher",
  "team_name": "my-project"
}
```
Exit code 2 prevents the teammate from going idle (keeps working).

**TaskCompleted** — fires when a task is being marked completed:
```json
{
  "hook_event_name": "TaskCompleted",
  "task_id": "task-001",
  "task_subject": "Implement user authentication",
  "task_description": "Add login and signup endpoints",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```
Exit code 2 prevents task completion — can run tests to verify before allowing completion.

Example TaskCompleted quality gate:
```bash
#!/bin/bash
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject')

if ! npm test 2>&1; then
  echo "Tests not passing. Fix failing tests before completing: $TASK_SUBJECT" >&2
  exit 2
fi

exit 0
```

### 2.7 Matcher Patterns

| Event | What matcher filters | Example values |
|-------|---------------------|----------------|
| PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest | tool name | `Bash`, `Edit\|Write`, `mcp__.*` |
| SessionStart | how session started | `startup`, `resume`, `clear`, `compact` |
| SessionEnd | why session ended | `clear`, `logout`, `prompt_input_exit`, `other` |
| Notification | notification type | `permission_prompt`, `idle_prompt`, `auth_success` |
| SubagentStart, SubagentStop | agent type | `Bash`, `Explore`, `Plan`, or custom names |
| PreCompact | what triggered | `manual`, `auto` |
| UserPromptSubmit, Stop, TeammateIdle, TaskCompleted | no matcher | always fires |

**MCP tool matching**:
- `mcp__memory__create_entities` — specific tool
- `mcp__memory__.*` — all tools from memory server
- `mcp__.*__write.*` — any write tool from any server

### 2.8 Environment Variables in Hooks

- `$CLAUDE_PROJECT_DIR` — project root directory
- `$CLAUDE_ENV_FILE` — path to file for persisting env vars across bash commands
- `${CLAUDE_PLUGIN_ROOT}` — plugin root directory (for plugin hooks)
- `$CLAUDE_CODE_REMOTE` — `"true"` if running remotely

### 2.9 Build 2 Hook Integration Plan

Build 2 should use hooks for:
1. **TaskCompleted** — quality gates (run tests, lint checks before allowing task completion)
2. **TeammateIdle** — assign new work or verify completion criteria
3. **PostToolUse** on `Write|Edit` — auto-format, auto-lint after code changes
4. **Stop** — verify all tasks complete before allowing session end
5. **SubagentStop** — capture subagent results for tracking

---

## 3. MCP CLIENT INTEGRATION (Python SDK)

### 3.1 Core API Signatures

**Installation**: `pip install mcp` (or `uv add mcp`)

**Key imports**:
```python
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
```

### 3.2 StdioServerParameters

```python
server_params = StdioServerParameters(
    command="python",          # executable
    args=["my_server.py"],     # arguments
    env={"DEBUG": "true"},     # environment variables
)
```

### 3.3 Client Session Lifecycle

```python
import asyncio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.architect.mcp_server"],
        env={"PROJECT_ROOT": "/path/to/project"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize the connection (REQUIRED first call)
            await session.initialize()

            # 2. List available tools
            tools = await session.list_tools()
            # tools.tools is a list of Tool objects
            for t in tools.tools:
                print(f"Tool: {t.name}")

            # 3. Call a tool
            result = await session.call_tool(
                "get_service_map",
                arguments={"project_root": "/path/to/project"}
            )

            # 4. Process results
            if result.content:
                for content in result.content:
                    if isinstance(content, types.TextContent):
                        print(f"Result: {content.text}")

            # 5. Access structured output if available
            if result.structured_content:
                print(f"Structured: {result.structured_content}")

            # 6. List and read resources
            resources = await session.list_resources()
            for resource in resources.resources:
                content = await session.read_resource(str(resource.uri))
                print(f"Resource {resource.uri}: {content.contents}")

            # 7. Get prompts
            prompts = await session.list_prompts()
            if prompts.prompts:
                prompt = await session.get_prompt(
                    prompts.prompts[0].name,
                    arguments={"name": "Alice"}
                )
                print(f"Prompt: {prompt.messages}")

asyncio.run(main())
```

### 3.4 Tool Call Result Types

```python
# CallToolResult contains:
result = await session.call_tool("tool_name", arguments={...})

# result.content — list of content blocks
# Each block is one of:
#   types.TextContent  — has .text field
#   types.ImageContent — has .data and .mimeType fields
#   types.EmbeddedResource — has .resource field

# result.structured_content — optional structured output (dict)
# result.isError — boolean indicating if tool call failed
```

### 3.5 Error Handling

```python
try:
    result = await session.call_tool("validate_endpoint", arguments={...})
    if result.isError:
        # Tool returned an error response (but didn't crash)
        error_text = result.content[0].text if result.content else "Unknown error"
        print(f"Tool error: {error_text}")
except Exception as e:
    # Connection/protocol-level error
    print(f"MCP error: {e}")
```

### 3.6 Task-Augmented Tools (Experimental)

```python
# For long-running operations with elicitation callbacks
result = await session.experimental.call_tool_as_task(
    "confirm_action",
    {"action": "delete files"},
)
task_id = result.task.taskId

# Poll for completion
async for status in session.experimental.poll_task(task_id):
    if status.status == "completed":
        final = await session.experimental.get_task_result(task_id, CallToolResult)
        break
```

### 3.7 MCP Server Definition (for Build 1 servers consumed by Build 2)

**Server-side pattern** (what Build 1 creates, Build 2 consumes):
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("architect-server")

@app.tool()
async def get_service_map(project_root: str) -> str:
    """Return the service dependency map."""
    # Implementation
    return json.dumps(service_map)

@app.tool()
async def get_contracts_for_service(service_name: str) -> str:
    """Return all contracts for a given service."""
    return json.dumps(contracts)

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write)
```

### 3.8 .mcp.json Format (Project-Level MCP Config)

```json
{
  "mcpServers": {
    "architect": {
      "command": "python",
      "args": ["-m", "src.architect.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}"
      }
    },
    "contract-engine": {
      "command": "python",
      "args": ["-m", "src.contract_engine.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "CONTRACT_DB": "${workspaceFolder}/.agent-team/contracts.db"
      }
    },
    "codebase-intelligence": {
      "command": "python",
      "args": ["-m", "src.codebase_intelligence.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "INDEX_PATH": "${workspaceFolder}/.agent-team/codebase.idx"
      }
    }
  }
}
```

### 3.9 Existing mcp_servers.py Pattern (Current Codebase)

The current codebase defines MCP servers as dicts returned by helper functions:

```python
def _firecrawl_server() -> dict[str, Any] | None:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env": {"FIRECRAWL_API_KEY": api_key},
    }

def get_mcp_servers(config: AgentTeamConfig) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    firecrawl_cfg = config.mcp_servers.get("firecrawl")
    if firecrawl_cfg and firecrawl_cfg.enabled:
        fc = _firecrawl_server()
        if fc:
            servers["firecrawl"] = fc
    # ... more servers
    return servers
```

Build 2 must ADD new server functions: `_architect_server()`, `_contract_engine_server()`, `_codebase_intelligence_server()` following this exact pattern.

---

## 4. CLAUDE.md FORMAT & LOADING BEHAVIOR

### 4.1 CLAUDE.md Locations & Scopes

| Location | Scope | Shared? |
|----------|-------|---------|
| `~/.claude/CLAUDE.md` | User — all projects | No |
| `CLAUDE.md` (project root) | Project — all collaborators | Yes (committed) |
| `.claude/CLAUDE.md` | Project — all collaborators | Yes (committed) |
| `CLAUDE.local.md` | Local — you, this repo only | No (gitignored) |

### 4.2 Loading Behavior

- CLAUDE.md files are loaded **automatically** at session start
- Teammates load CLAUDE.md files from their working directory
- Content is injected into the system prompt
- Multiple CLAUDE.md files are merged (user + project + local)
- The `--append-system-prompt` flag can add additional instructions

### 4.3 Auto Memory

- Auto memory directory: `~/.claude/projects/<project-hash>/memory/`
- `MEMORY.md` is always loaded into system prompt (first 200 lines)
- Can be disabled: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
- Separate topic files linked from MEMORY.md for detailed notes

### 4.4 Build 2 CLAUDE.md Generation

Build 2 must generate project-level `.claude/CLAUDE.md` that includes:
- Service architecture overview
- Contract verification instructions
- Code quality standards
- MCP tool usage instructions for teammates
- File organization conventions

---

## 5. CLAUDE CODE SETTINGS RELEVANT TO BUILD 2

### 5.1 Permission Configuration

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ],
    "defaultMode": "acceptEdits"
  }
}
```

Permission modes: `"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, `"bypassPermissions"`

### 5.2 MCP Server Management Settings

| Setting | Description |
|---------|-------------|
| `enableAllProjectMcpServers` | Auto-approve all MCP servers in `.mcp.json` |
| `enabledMcpjsonServers` | Specific servers to approve: `["memory", "github"]` |
| `disabledMcpjsonServers` | Specific servers to reject: `["filesystem"]` |

### 5.3 Key Environment Variables for Build 2

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enable agent teams (set to `1`) |
| `CLAUDE_CODE_TEAM_NAME` | Team name (auto-set on teammates) |
| `CLAUDE_CODE_TASK_LIST_ID` | Share task list across sessions |
| `CLAUDE_CODE_PLAN_MODE_REQUIRED` | Require plan approval (auto-set) |
| `ANTHROPIC_API_KEY` | API key for Claude |
| `ANTHROPIC_MODEL` | Override model |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for subagents |
| `CLAUDE_CODE_EFFORT_LEVEL` | `low`, `medium`, `high` (Opus 4.6 only) |
| `MAX_THINKING_TOKENS` | Override thinking budget |
| `MCP_TIMEOUT` | MCP server startup timeout (ms) |
| `MCP_TOOL_TIMEOUT` | MCP tool execution timeout (ms) |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Context compaction threshold (1-100) |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Max output tokens (default 32K, max 64K) |
| `BASH_DEFAULT_TIMEOUT_MS` | Default bash command timeout |
| `BASH_MAX_TIMEOUT_MS` | Maximum bash timeout |

### 5.4 Subagent Configuration

Subagents stored as Markdown files with YAML frontmatter:
- User: `~/.claude/agents/`
- Project: `.claude/agents/`

### 5.5 Available Tools

Full tool list from official docs:
| Tool | Description | Permission |
|------|-------------|-----------|
| `AskUserQuestion` | Multi-choice questions | No |
| `Bash` | Shell commands | Yes |
| `TaskOutput` | Background task output | No |
| `Edit` | Targeted file edits | Yes |
| `ExitPlanMode` | Exit plan mode | Yes |
| `Glob` | File pattern matching | No |
| `Grep` | Content search | No |
| `KillShell` | Kill background bash | No |
| `MCPSearch` | Search MCP tools | No |
| `NotebookEdit` | Jupyter cells | Yes |
| `Read` | Read files | No |
| `Skill` | Execute skills | Yes |
| `Task` | Run sub-agent | No |
| `TaskCreate` | Create task | No |
| `TaskGet` | Get task details | No |
| `TaskList` | List tasks | No |
| `TaskUpdate` | Update tasks | No |
| `WebFetch` | Fetch URLs | Yes |
| `WebSearch` | Web search | Yes |
| `Write` | Create/overwrite files | Yes |
| `LSP` | Language server ops | No |

### 5.6 Sandbox Settings (for secure execution)

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["git", "docker"],
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"],
      "allowLocalBinding": true
    }
  }
}
```

---

## 6. EXISTING AGENT-TEAM v14.0 PATTERNS

### 6.1 Scheduler (scheduler.py — ~1369 lines)

**Key dataclass**:
```python
@dataclass
class TaskNode:
    id: str
    title: str
    description: str
    files: list[str]
    depends_on: list[str]
    status: str            # "pending", "in_progress", "done", "blocked"
    assigned_agent: str
    integration_declares: list[str]
    milestone_id: str
```

**Core functions**:
- `parse_tasks_md(content: str) -> list[TaskNode]` — 3 format fallbacks (block, table, bullet)
- `compute_schedule(tasks, max_parallel_tasks) -> Schedule` — full pipeline: validate graph, build waves, detect conflicts, resolve, critical path
- `compute_execution_waves(tasks, max_parallel) -> list[list[TaskNode]]` — Kahn's algorithm
- `detect_file_conflicts(waves) -> list[FileConflict]` — finds concurrent file writes
- `resolve_conflicts_via_dependency(tasks, conflicts) -> list[TaskNode]` — adds deps to fix conflicts
- `build_task_context(task, all_tasks, codebase_map) -> TaskContext` — scopes context per agent
- `render_task_context_md(context) -> str` — renders for prompt injection

**Build 2 impact**: The scheduler stays mostly intact. Build 2 adds agent-teams-aware scheduling that maps waves to Claude Code teammate assignments.

### 6.2 Contracts (contracts.py — ~651 lines)

**Key dataclasses**:
```python
@dataclass
class ModuleContract:
    module_path: str
    exports: list[str]       # function/class names
    dependencies: list[str]  # other modules it imports

@dataclass
class WiringContract:
    source_module: str
    target_module: str
    imported_symbols: list[str]
    usage_verified: bool

@dataclass
class ContractRegistry:
    modules: dict[str, ModuleContract]
    wirings: list[WiringContract]
    middlewares: list[MiddlewareContract]
```

**Core functions**:
- `load_contracts(path: Path) -> ContractRegistry` — loads CONTRACTS.json
- `save_contracts(registry, path: Path)` — saves CONTRACTS.json
- `verify_module_contract(contract, project_root) -> VerificationResult` — Python AST for .py, regex for .ts/.js
- `verify_wiring_contract(wiring, project_root) -> VerificationResult` — checks exports + imports + usage

**Build 2 impact**: Must add MCP client calls to Contract Engine server, replacing/augmenting local JSON verification. The `verify_module_contract` and `verify_wiring_contract` functions become thin wrappers around MCP tool calls.

### 6.3 Codebase Map (codebase_map.py — ~957 lines)

**Key dataclass**:
```python
@dataclass
class CodebaseMap:
    root: Path
    modules: dict[str, ModuleInfo]
    import_graph: dict[str, list[str]]
    shared_files: list[str]
    frameworks: list[str]
    total_files: int
    total_lines: int
    primary_language: str
```

**Core functions**:
- `generate_codebase_map(root, timeout) -> CodebaseMap` — async entry point
- `_generate_map_sync(root) -> CodebaseMap` — file discovery, export/import extraction
- `summarize_map(map) -> str` — renders markdown for prompt injection

**Build 2 impact**: TO BE REPLACED by MCP queries to Codebase Intelligence server. The `generate_codebase_map()` function becomes `query_codebase_intelligence()` that calls MCP tools instead of doing local static analysis.

### 6.4 MCP Servers (mcp_servers.py — ~171 lines)

**Current server registry pattern**:
```python
def get_mcp_servers(config: AgentTeamConfig) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    # Config-gated server addition
    firecrawl_cfg = config.mcp_servers.get("firecrawl")
    if firecrawl_cfg and firecrawl_cfg.enabled:
        fc = _firecrawl_server()
        if fc:
            servers["firecrawl"] = fc
    return servers
```

**Existing servers**: Firecrawl, Context7, Sequential Thinking, Playwright

**Build 2 additions needed**:
- `_architect_server(config)` — Architect MCP
- `_contract_engine_server(config)` — Contract Engine MCP
- `_codebase_intelligence_server(config)` — Codebase Intelligence MCP

### 6.5 Config (config.py)

**Key config dataclasses**:
```python
@dataclass
class OrchestratorConfig:
    model: str
    max_turns: int
    permission_mode: str
    max_budget_usd: float
    backend: str
    max_thinking_tokens: int

@dataclass
class DepthConfig:
    default: str       # quick, standard, thorough, exhaustive
    auto_detect: bool
    scan_scope_mode: str
    keyword_map: dict

@dataclass
class ConvergenceConfig:
    max_cycles: int
    escalation_threshold: float
    min_convergence_ratio: float
    recovery_threshold: float
```

**Build 2 must add**:
```python
@dataclass
class AgentTeamsConfig:
    enabled: bool = False
    max_teammates: int = 4
    fallback_to_cli: bool = True
    teammate_model: str = ""
    teammate_permission_mode: str = "acceptEdits"

@dataclass
class ContractEngineConfig:
    enabled: bool = True
    mcp_server_command: str = "python"
    mcp_server_args: list[str] = field(default_factory=lambda: ["-m", "src.contract_engine.mcp_server"])

@dataclass
class CodebaseIntelligenceConfig:
    enabled: bool = True
    mcp_server_command: str = "python"
    mcp_server_args: list[str] = field(default_factory=lambda: ["-m", "src.codebase_intelligence.mcp_server"])
```

---

## 7. BUILD 1 MCP TOOL SIGNATURES (Cross-Reference)

### 7.1 Architect MCP (3 tools)

```
get_service_map(project_root: str) -> ServiceMap
  Returns: { services: [...], dependencies: [...], shared_modules: [...] }

get_contracts_for_service(service_name: str) -> ContractSet
  Returns: { service: str, contracts: [{ endpoint, method, request_schema, response_schema }] }

get_domain_model(service_name: str) -> DomainModel
  Returns: { entities: [...], value_objects: [...], relationships: [...] }
```

### 7.2 Contract Engine MCP (6 tools)

```
get_contract(service: str, endpoint: str) -> Contract
  Returns: { service, endpoint, method, request_schema, response_schema, version }

validate_endpoint(service: str, endpoint: str, implementation_path: str) -> ValidationResult
  Returns: { valid: bool, errors: [...], warnings: [...] }

generate_tests(service: str, endpoint: str) -> TestSuite
  Returns: { test_file: str, test_cases: [...] }

check_breaking_changes(service: str, old_version: str, new_version: str) -> BreakingChangeReport
  Returns: { breaking: bool, changes: [...] }

mark_implemented(service: str, endpoint: str, path: str) -> void
  Side effect: Updates contract DB to mark endpoint as implemented

get_unimplemented_contracts() -> list[Contract]
  Returns: [{ service, endpoint, method, ... }]
```

### 7.3 Codebase Intelligence MCP (7 tools)

```
find_definition(symbol: str, file_hint: str?) -> DefinitionResult
  Returns: { file, line, column, kind, snippet }

find_callers(symbol: str, file: str?) -> list[CallerResult]
  Returns: [{ file, line, snippet, context }]

find_dependencies(module: str) -> DependencyGraph
  Returns: { direct: [...], transitive: [...], circular: [...] }

search_semantic(query: str, scope: str?) -> list[SearchResult]
  Returns: [{ file, line, snippet, relevance_score }]

get_service_interface(service: str) -> ServiceInterface
  Returns: { exports: [...], imports: [...], endpoints: [...] }

check_dead_code(module: str) -> DeadCodeReport
  Returns: { unused_exports: [...], unreachable_functions: [...] }

register_artifact(path: str, type: str, metadata: dict) -> void
  Side effect: Registers a build artifact in the intelligence index
```

### 7.4 .mcp.json Server Configuration

```json
{
  "mcpServers": {
    "architect": {
      "command": "python",
      "args": ["-m", "src.architect.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "ARCHITECT_DB": "${workspaceFolder}/.agent-team/architect.db"
      }
    },
    "contract-engine": {
      "command": "python",
      "args": ["-m", "src.contract_engine.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "CONTRACT_DB": "${workspaceFolder}/.agent-team/contracts.db"
      }
    },
    "codebase-intelligence": {
      "command": "python",
      "args": ["-m", "src.codebase_intelligence.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "INDEX_PATH": "${workspaceFolder}/.agent-team/codebase.idx"
      }
    }
  }
}
```

---

## 8. GAPS & RISKS IDENTIFIED

### 8.1 Critical Gaps

1. **Agent Teams is EXPERIMENTAL** — No stability guarantees. Build 2 MUST implement abstraction layer with fallback.
2. **No nested teams** — Cannot have sub-teams for complex microservice builds. Must use flat hierarchy with smart task decomposition.
3. **No session resumption** — Teammate crashes lose all context. Must implement checkpoint/recovery at the Python CLI level.
4. **Windows Terminal limitation** — Split panes unsupported. Must default to `in-process` mode.

### 8.2 Architecture Risks

1. **asyncio.run() nesting** — Existing codebase has known nested asyncio.run() issues (pre-existing from E2E/browser testing). Agent teams integration must use `anyio` or careful event loop management.
2. **MCP Python SDK uses anyio** — The SDK uses `anyio` for async, while existing codebase uses `asyncio`. Need consistent async runtime.
3. **MCP server startup time** — `MCP_TIMEOUT` env var controls startup timeout. Build 1 servers must start within this window.
4. **Contract DB concurrency** — Multiple teammates may call Contract Engine simultaneously. Build 1 must handle concurrent access (SQLite WAL mode or similar).

### 8.3 Integration Approach Summary

| Component | Approach |
|-----------|----------|
| Agent Teams | Abstraction layer with CLI fallback |
| Hooks | Quality gates via TaskCompleted + TeammateIdle |
| MCP Client | `mcp.client.stdio.stdio_client` + `ClientSession` pattern |
| CLAUDE.md | Auto-generated per project + per-service |
| Settings | Programmatic `.claude/settings.json` generation |
| Existing scheduler | Keep + extend with team-aware wave mapping |
| Existing contracts | Wrap with MCP client calls |
| Existing codebase_map | Replace with MCP queries |

---

## 9. VERIFIED CORRECTIONS FROM RESEARCH REPORT

Cross-referencing against SUPER_TEAM_RESEARCH_REPORT.md Section 4:

1. **CONFIRMED**: PostgreSQL dropped — use SQLite for all local storage
2. **CONFIRMED**: AsyncAPI gap — no async event spec tooling available
3. **CONFIRMED**: Agent Teams experimental — abstraction layer required
4. **CONFIRMED**: MCP SDK exact API — `stdio_client()` + `ClientSession` + `call_tool()` verified
5. **CONFIRMED**: Pact secondary for contract testing — static verification primary approach

---

## 10. APPENDIX: QUICK REFERENCE CHEAT SHEET

### Enable Agent Teams
```json
// .claude/settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

### MCP Client Connection
```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("tool_name", arguments={...})
```

### Hook Quality Gate
```json
{
  "hooks": {
    "TaskCompleted": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/verify-task.sh"
      }]
    }]
  }
}
```

### MCP Server Config
```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "module.path"],
      "env": { "KEY": "value" }
    }
  }
}
```
