# BUILD 2 PRD — Technology Review Report

**Reviewer**: Technology Review Agent (Teammate)
**Date**: 2026-02-14
**PRD Version**: BUILD2_PRD.md
**Research Sources**: BUILD2_TECHNOLOGY_RESEARCH.md + SUPER_TEAM_RESEARCH_REPORT.md

---

## Executive Summary

**Overall Verdict**: ⚠️ **PASS WITH WARNINGS**

The PRD demonstrates strong alignment with validated technology research and reflects all 7 critical corrections from the research report. However, there are **3 CRITICAL issues** requiring immediate fixes, **11 WARNING issues** needing clarification, and **5 INFO suggestions** for improvement.

**Critical Issues**:
1. Incorrect TaskResult signature — TaskUpdate API does not accept `cost_usd` parameter
2. Missing ClientSession initialization requirement — `await session.initialize()` is mandatory but not specified in all MCP integration requirements
3. Incomplete hook input schema — JSON input structure for hooks is not fully defined

**Key Strengths**:
- All 7 corrections from research report are applied
- Technology stack version claims are accurate
- MCP SDK patterns match verified API signatures
- Known limitations are properly acknowledged
- Fallback strategies are comprehensive

---

## CRITICAL ISSUES (Must Fix Before Implementation)

### C1: TaskResult Incorrect Field — `cost_usd` Does Not Exist in Claude Code API

**Location**: TECH-001 (line 85)

**PRD Claims**:
```python
@dataclass
class TaskResult:
    task_id: str
    status: str
    output: str
    error: str
    files_created: list[str]
    files_modified: list[str]
    cost_usd: float  # ❌ INCORRECT
```

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 1.4:
> "Available task tools (from official docs):
> - TaskCreate / TaskGet / TaskList / TaskUpdate"

Claude Code agent teams API does NOT expose cost tracking at the task level. Cost is tracked at the session level only. The TaskUpdate tool accepts: `taskId`, `status`, `subject`, `description`, `owner`, `metadata`, `addBlocks`, `addBlockedBy` — **no `cost_usd` field**.

**Required Fix**:
Remove `cost_usd: float` from TaskResult dataclass. Track costs separately at the Builder session level (existing agent-team v14.0 pattern already does this via `total_cost` in RunState).

**Severity**: CRITICAL — This will cause runtime errors when trying to set a non-existent field.

---

### C2: Missing `session.initialize()` Requirement in MCP Integration

**Location**: REQ-024, REQ-038, TECH-019

**PRD Claims**:
REQ-024 says "create_contract_engine_session() async context manager using StdioServerParameters + stdio_client() + ClientSession pattern" but does NOT specify that `await session.initialize()` must be called after creating the ClientSession.

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3:
```python
async with ClientSession(read, write) as session:
    # 1. Initialize the connection (REQUIRED first call)
    await session.initialize()

    # 2. List available tools
    tools = await session.list_tools()
```

The documentation explicitly states: **"Initialize the connection (REQUIRED first call)"**. Without this call, all subsequent MCP tool calls will fail.

**Required Fix**:
Add a new requirement:
- REQ-024b: `create_contract_engine_session()` must call `await session.initialize()` immediately after creating the ClientSession and before yielding
- REQ-038b: `create_codebase_intelligence_session()` must call `await session.initialize()` after creating the ClientSession

Update REQ-025 wording to: "create_contract_engine_session() must call `await session.initialize()` after creating the ClientSession **and before yielding to the caller**"

**Severity**: CRITICAL — Without this, all MCP integrations will fail at runtime.

---

### C3: Incomplete Hook Input JSON Schema Definition

**Location**: REQ-016, hooks_manager.py specifications

**PRD Claims**:
REQ-016 says: "The quality-gate.sh Stop hook script must read JSON from stdin, extract `cwd` field via python3 one-liner, check REQUIREMENTS.md completion ratio..."

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 2.4:
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

The PRD correctly references extracting `cwd`, but does NOT define the full JSON schema that hooks receive, nor does it specify that different hook events have different fields (e.g., TaskCompleted hooks receive `task_id`, `task_subject`, `teammate_name` — Section 2.6).

**Required Fix**:
Add a new TECH requirement:
- TECH-004b: `HookInput` dataclass with fields: `session_id: str`, `transcript_path: str`, `cwd: str`, `permission_mode: str`, `hook_event_name: str`, and event-specific fields (`task_id`, `task_subject` for TaskCompleted; no extra fields for Stop)

Update REQ-016 to reference this dataclass and specify the exact JSON parsing approach.

**Severity**: CRITICAL — Hook scripts will fail to parse input correctly, blocking quality gates.

---

## WARNING ISSUES (Need Clarification)

### W1: Agent Teams Fallback Logic Underspecified

**Location**: REQ-009

**PRD Claims**:
"When config.agent_teams.fallback_to_cli is True and AgentTeamsBackend fails during initialize() or execute_wave(), the factory must catch the exception and return a CLIBackend instead, logging a warning"

**Issue**:
The requirement specifies fallback during `initialize()` but does NOT specify what happens if agent teams fail during `execute_wave()` — does the system:
1. Retry the wave with CLIBackend?
2. Fail the entire build?
3. Continue with remaining waves in agent teams mode?

**Research Context**:
From SUPER_TEAM_RESEARCH_REPORT.md Section 3 CORRECTION 4:
> "Agent Teams require `agentTeams: true` in settings (disabled by default). There's no session resumption — if a teammate crashes, its state is lost."

**Recommended Fix**:
Clarify REQ-009 with three scenarios:
- Fallback during `initialize()`: Return CLIBackend (as stated)
- Fallback during `execute_wave()` (wave N fails): Retry wave N with CLIBackend, continue subsequent waves in CLI mode
- Fallback after multiple wave failures: Switch to CLIBackend for all remaining waves

---

### W2: MCP Timeout Configuration Not Specified

**Location**: Milestone 2 MCP integration

**Issue**:
The PRD does not specify values for `MCP_TIMEOUT` or `MCP_TOOL_TIMEOUT` environment variables.

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 5.3:
> "MCP_TIMEOUT: MCP server startup timeout (ms)
> MCP_TOOL_TIMEOUT: MCP tool execution timeout (ms)"

Build 1 MCP servers (Contract Engine, Codebase Intelligence) must start within the timeout window.

**Recommended Fix**:
Add to ContractEngineConfig and CodebaseIntelligenceConfig:
- `startup_timeout_ms: int = 30000` (30 seconds for server startup)
- `tool_timeout_ms: int = 60000` (60 seconds for tool execution)

Wire these into the environment variables passed to `StdioServerParameters`.

---

### W3: ExecutionBackend Protocol — Async vs Sync Methods Not Fully Specified

**Location**: REQ-001, TECH-009

**PRD Claims**:
"ExecutionBackend protocol defining initialize(), execute_wave(), execute_task(), send_context(), shutdown(), supports_peer_messaging(), supports_self_claiming() — **all async except the two boolean methods**"

**Issue**:
While the requirement states "all async except the two boolean methods", it does NOT specify:
1. Whether `supports_peer_messaging()` and `supports_self_claiming()` are @property or regular methods
2. Whether these can change during runtime (e.g., agent teams becomes unavailable mid-session)

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 1.8:
> "Known limitations: No session resumption, no nested teams, one team per session, split panes not on Windows Terminal"

If agent teams become unavailable mid-session (e.g., Claude Code update), the boolean methods should reflect current state, not initial state.

**Recommended Fix**:
- Make `supports_peer_messaging()` and `supports_self_claiming()` regular methods (not properties)
- Specify that they can return different values mid-session if backend availability changes
- CLIBackend always returns False for both

---

### W4: Hook Script Permissions on Windows Not Addressed

**Location**: REQ-014

**PRD Claims**:
"write_hooks_to_project() must write `.claude/settings.local.json` with hooks section and `.claude/hooks/*.sh` scripts with **executable permissions (chmod 0o755, graceful on Windows)**"

**Issue**:
Windows does NOT support Unix permissions (chmod is a no-op). The requirement says "graceful on Windows" but does NOT specify what "graceful" means — should it:
1. Write .bat equivalents?
2. Write .sh files and rely on WSL/Git Bash?
3. Skip hooks entirely on Windows?

**Research Finding**:
From SUPER_TEAM_RESEARCH_REPORT.md GAP 4:
> "Omar's primary platform is Windows 11. Agent Teams split panes don't work on Windows Terminal."

**Recommended Fix**:
Specify one of:
- Option A: Write both `.sh` (for WSL) and `.bat` (for cmd) on Windows
- Option B: Write `.sh` only, document that WSL or Git Bash is required
- Option C: Use Python hook scripts (`.py`) instead of bash on Windows

Add explicit Windows testing to TEST-017.

---

### W5: Contract Schema Hash Algorithm Not Specified

**Location**: Milestone 2 SVC-xxx contracts

**Issue**:
The PRD references "spec_hash" in multiple places (TECH-014: `spec_hash: str`, SVC-001 response DTO) but does NOT specify the hashing algorithm.

**Research Finding**:
From SUPER_TEAM_RESEARCH_REPORT.md EXPANSION 2:
> "Each contract gets a SHA-256 hash on registration"

**Recommended Fix**:
Add to TECH-014:
- `spec_hash: str` — **SHA-256 hex digest of canonical JSON spec (sorted keys, no whitespace)**

Add a new TECH requirement:
- TECH-014b: `_compute_spec_hash(spec: dict) -> str` helper in `ContractEngineClient` that serializes spec to canonical JSON (json.dumps with sort_keys=True, separators without spaces), computes SHA-256, returns hex digest

---

### W6: Depth Gating — Quick Mode Disables Too Many Features

**Location**: TECH-044 Depth Gating table (lines 521-530)

**PRD Claims**:
```
| agent_teams.enabled | quick: False | standard: False | thorough: True (if env set) | exhaustive: True (if env set) |
```

**Issue**:
Quick mode disables agent teams entirely. But the PRD also says (REQ-004):
> "create_execution_backend() factory function that selects AgentTeamsBackend when config.agent_teams.enabled AND CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 AND claude CLI is on PATH, otherwise returns CLIBackend"

If `config.agent_teams.enabled=False` in quick mode, but user has explicitly set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, should the system:
1. Respect the config (disable agent teams)?
2. Respect the env var (enable agent teams)?
3. Use agent teams but with reduced teammates (e.g., max_teammates=2)?

**Recommended Fix**:
Clarify depth gating priority:
- Depth setting controls the CONFIG default
- User can override via YAML (config.agent_teams.enabled=True even in quick mode)
- Env var `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is a prerequisite, not a switch
- Add to TECH-044: "Depth-based defaults can be overridden by explicit YAML config"

---

### W7: MCP Server Command Path — Relative vs Absolute

**Location**: TECH-015, TECH-025

**PRD Claims**:
```python
@dataclass
class ContractEngineConfig:
    mcp_command: str = "python"
    mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.contract_engine.mcp_server"])
```

**Issue**:
The default args use a **relative module path** (`src.contract_engine.mcp_server`). This assumes:
1. Build 1's contract engine is installed as a package
2. OR the current working directory is the Build 1 project root

But Build 2 runs in the **generated project's directory**, not Build 1's directory.

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 7.4:
```json
{
  "mcpServers": {
    "contract-engine": {
      "command": "python",
      "args": ["-m", "src.contract_engine.mcp_server"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

The Build 1 servers expect to be run from the **Build 1 project root**, not the generated project.

**Recommended Fix**:
Add to ContractEngineConfig and CodebaseIntelligenceConfig:
- `server_root: str = ""` — path to Build 1's project root
- Update TECH-020 to pass `cwd=config.contract_engine.server_root` to `StdioServerParameters`
- Document in INT-001 and INT-002 that Build 1 servers must be accessible (either installed as package or via path)

---

### W8: CLAUDE.md Contract Truncation — 20 Limit Too Low

**Location**: REQ-052

**PRD Claims**:
"CLAUDE.md contracts section must limit to 20 contracts to prevent excessive file size, with '... and N more' suffix when truncated"

**Issue**:
For a 12-service system with 30-50 inter-service contracts, truncating at 20 means teammates won't see 50%+ of contracts. This could cause:
1. Missing contract violations (teammate doesn't know a contract exists)
2. Duplicate contract creation (teammate re-creates a truncated contract)
3. Incomplete API coverage (teammate skips implementing truncated endpoints)

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 4.1:
> "Content is injected into the system prompt"

Claude Code has a **large context window** (>200K tokens for Opus 4.6). A typical OpenAPI contract is 100-500 lines (~1-5K tokens). 50 contracts = ~50-250K tokens, well within limits.

**Recommended Fix**:
Increase truncation limit to **100 contracts** or make it **configurable**:
- `contract_limit: int = 100` in AgentTeamsConfig
- Document that teammates should query Contract Engine MCP for full details if they need a specific contract

---

### W9: ContractEngineClient — No Retry Logic for Transient Failures

**Location**: REQ-026

**PRD Claims**:
"Every ContractEngineClient method must log a warning with exc_info=True on exception, never raise to the caller"

**Issue**:
This is a **silent failure** pattern that can hide genuine issues. If the Contract Engine MCP server is temporarily overloaded (8 parallel Builders calling validate_endpoint simultaneously), all validation calls fail silently, and Build 2 proceeds without contract verification.

**Research Finding**:
From SUPER_TEAM_RESEARCH_REPORT.md Risk 7:
> "8 parallel Builders all registering artifacts with Codebase Intelligence simultaneously could hit SQLite write locks."
> "Mitigation: WAL mode + busy_timeout."

The same concurrency issue applies to Contract Engine.

**Recommended Fix**:
Add retry logic to ContractEngineClient methods:
- Retry up to 3 times on `OSError`, `TimeoutError`, or MCP connection errors
- Exponential backoff (1s, 2s, 4s)
- Only log warning and return safe default after all retries exhausted
- Add to TECH requirement: "MCP client methods use retry-with-backoff (3 attempts, exponential backoff) for transient errors"

---

### W10: AgentTeamsBackend — No Max Timeout for Wave Execution

**Location**: REQ-007

**PRD Claims**:
"AgentTeamsBackend.execute_wave() must create TaskCreate calls for each task in the wave, set up dependencies via TaskUpdate(addBlockedBy), and **poll TaskList until all tasks complete or timeout**"

**Issue**:
The requirement mentions "timeout" but does NOT specify:
1. What the timeout value is
2. Whether it's per-task, per-wave, or total
3. What happens on timeout (retry? fail? partial completion?)

**Research Finding**:
From BUILD2_TECHNOLOGY_RESEARCH.md Section 1.5:
> "AgentTeamsConfig: teammate_idle_timeout: int = 300"

This is an idle timeout (5 minutes), not a task timeout.

**Recommended Fix**:
Add to AgentTeamsConfig:
- `wave_timeout_seconds: int = 3600` (1 hour per wave)
- `task_timeout_seconds: int = 1800` (30 minutes per task)

Add to REQ-007:
- "Poll TaskList every 30 seconds. If a task is in_progress for longer than task_timeout_seconds, mark it as failed. If wave total time exceeds wave_timeout_seconds, fail remaining tasks and return WaveResult."

---

### W11: Missing Fallback for Build 1 Service Unavailability

**Location**: INT-001, INT-002, INT-003

**PRD Claims**:
- INT-001: "Build 2 depends on Build 1's Contract Engine MCP server — when unavailable, all features gracefully fall back to static scanning"
- INT-002: "Build 2 depends on Build 1's Codebase Intelligence MCP server — when unavailable, codebase map generation falls back to existing static generate_codebase_map()"
- INT-003: "Build 2 depends on Build 1's Architect MCP server — consumed during PRD decomposition phase **when available**"

**Issue**:
INT-001 and INT-002 specify fallbacks, but INT-003 does NOT. What happens if Architect MCP is unavailable during PRD decomposition?

**Research Finding**:
From SUPER_TEAM_RESEARCH_REPORT.md Section 13 Cross-Build Dependencies:
```
| Architect MCP queries | Architect MCP server (3 tools) | Standard PRD decomposition without live queries |
```

**Recommended Fix**:
Update INT-003:
- "Build 2 depends on Build 1's Architect MCP server (3 tools) — consumed during PRD decomposition phase when available. **When unavailable, fallback to standard PRD decomposition using only the PRD text (no live service map queries).**"

---

## INFO ISSUES (Suggestions)

### I1: Consider Adding MCP Connection Pooling

**Location**: Milestone 2, MCP client design

**Observation**:
The PRD specifies creating new MCP sessions via `async with create_contract_engine_session()` on every call. For high-frequency operations (e.g., validate_endpoint called 50 times during a build), this creates 50 separate MCP server processes.

**Suggestion**:
Add connection pooling:
- Create MCP session once at Builder initialization
- Reuse the session across multiple tool calls
- Close session at Builder shutdown

**Benefit**:
Reduces MCP server startup overhead from 50x to 1x per Builder.

---

### I2: Add Structured Logging for MCP Tool Calls

**Location**: ContractEngineClient, CodebaseIntelligenceClient

**Observation**:
REQ-026 specifies "log a warning with exc_info=True on exception" but does NOT specify logging successful MCP calls.

**Suggestion**:
Add structured logging for all MCP tool calls:
```python
logger.info("MCP tool call", extra={
    "tool": "validate_endpoint",
    "server": "contract-engine",
    "duration_ms": elapsed,
    "success": True
})
```

**Benefit**:
Enables debugging, performance profiling, and cost tracking.

---

### I3: Add MCP Server Health Check Before First Call

**Location**: Milestone 2, MCP integration

**Suggestion**:
Add a health check tool to Contract Engine and Codebase Intelligence MCP servers:
```python
@mcp.tool()
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
```

Call this during `session.initialize()` to fail fast if the server is unresponsive.

**Benefit**:
Clearer error messages ("MCP server not responding") vs. generic timeout errors.

---

### I4: Document Agent Teams Display Mode Defaults

**Location**: AgentTeamsConfig (TECH-005)

**Observation**:
The PRD does not specify which `teammateMode` (in-process, tmux, split) should be default.

**Suggestion**:
Add to AgentTeamsConfig:
- `teammate_display_mode: str = "in-process"` (safer default, works on Windows Terminal)

Document in INT-010 that split panes don't work on Windows Terminal.

---

### I5: Consider Adding Contract Validation Caching

**Location**: ContractEngineClient.validate_endpoint

**Observation**:
If validate_endpoint is called multiple times with the same inputs (e.g., during fix retries), it hits the Contract Engine MCP server every time.

**Suggestion**:
Add in-memory caching:
```python
_validation_cache: dict[tuple, ContractValidation] = {}

def validate_endpoint(...):
    cache_key = (service_name, method, path, json.dumps(response_body, sort_keys=True))
    if cache_key in _validation_cache:
        return _validation_cache[cache_key]
    # ... make MCP call
    _validation_cache[cache_key] = result
    return result
```

**Benefit**:
Reduces redundant MCP calls during fix loops.

---

## CORRECTIONS APPLIED (Research Report Section 4)

✅ **CORRECTION 1 (PostgreSQL → SQLite)**: PRD correctly uses SQLite, not PostgreSQL. Verified in INT-001/INT-002 env vars (no postgres mentioned).

✅ **CORRECTION 2 (AsyncAPI Tooling Gap)**: PRD does NOT claim AsyncAPI support. Event schema scan (CONTRACT-003) references "AsyncAPI contract" but implementation is deferred. Acceptable for Build 2 scope.

✅ **CORRECTION 3 (Pact Secondary)**: PRD does NOT mention Pact. Schemathesis is not in scope (handled by Build 1). Correct.

✅ **CORRECTION 4 (Agent Teams Experimental)**: PRD includes abstraction layer (ExecutionBackend protocol), CLIBackend fallback (REQ-009), and documents limitations (INT-009, known limitations in agent_teams section). Excellent coverage.

✅ **CORRECTION 5 (MCP SDK API)**: PRD uses correct `stdio_client()` + `ClientSession` + `call_tool()` pattern (REQ-024, REQ-038). Matches BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3 exactly.

✅ **CORRECTION 6 (Hooks Architecture)**: PRD defines TaskCompleted, TeammateIdle, Stop, PostToolUse hooks (REQ-011..015). Matches research Section 2 exactly.

✅ **CORRECTION 7 (CLAUDE.md Generation)**: PRD includes complete CLAUDE.md generation strategy (REQ-043..053, Milestone 4). Matches research GAP 2 recommendations.

---

## GAPS ADDRESSED (Research Report Section 4)

✅ **GAP 1 (Hook Architecture)**: Fully addressed in Milestone 1 (REQ-010..016). Includes agent-type hooks for TaskCompleted (convergence verification).

✅ **GAP 2 (CLAUDE.md Generation)**: Fully addressed in Milestone 4 (REQ-043..053). Includes role-specific sections, MCP tools, convergence mandates.

✅ **GAP 3 (Contract Implementation Tracking)**: Fully addressed via `mark_implemented()` tool (SVC-005, REQ-022).

⚠️ **GAP 4 (Windows Compatibility)**: Partially addressed. INT-010 mentions Windows, TEST-017 tests chmod graceful degradation, but W4 above identifies missing .bat/.sh strategy.

✅ **GAP 5 (SQLite Concurrency)**: Not directly in Build 2 scope (Build 1 responsibility), but acknowledged in INT-001 fallback logic.

✅ **GAP 6 (Cost Estimation)**: TaskResult incorrectly includes cost_usd (C1 issue), but RunState tracking pattern is preserved from v14.0.

✅ **GAP 7 (Incremental Indexing)**: Fully addressed via register_artifact() tool (SVC-013, REQ-037, REQ-041).

---

## EXPANSIONS VERIFICATION (Research Report Section 5)

**EXPANSION 1 (Architect Decomposition)**: Not in Build 2 scope (Build 1 responsibility). PRD correctly references Build 1 Architect MCP as dependency (INT-003).

**EXPANSION 2 (Contract Immutability)**: PRD includes spec_hash in contracts (TECH-014, SVC-001 response), but does NOT specify the hash algorithm (W5 above).

**EXPANSION 3 (Quality Gate Layers)**: Not in Build 2 scope (Build 3 responsibility). PRD correctly focuses on contract compliance only.

**EXPANSION 4 (Super Orchestrator State Machine)**: Not in Build 2 scope (Build 3 responsibility).

---

## TECHNOLOGY VERSION VERIFICATION

| Technology | PRD Claim | Research Validation | Status |
|------------|-----------|---------------------|--------|
| Python | 3.12+ | Existing codebase uses 3.12+ | ✅ CORRECT |
| asyncio | Existing runtime | Existing codebase uses asyncio | ✅ CORRECT |
| MCP Python SDK | mcp>=1.25,<2 | Context7 /modelcontextprotocol/python-sdk confirmed | ✅ CORRECT |
| Agent Teams | Experimental (Opus 4.6) | EXPERIMENTAL flag required, Section 1.1 | ✅ CORRECT |
| pytest | Latest | Existing infrastructure | ✅ CORRECT |
| YAML | Standard | Existing config.py | ✅ CORRECT |

---

## API SIGNATURE VERIFICATION

### ExecutionBackend Protocol (TECH-009)

**PRD Claims**:
```python
@runtime_checkable Protocol with:
- initialize() -> async
- execute_wave() -> async
- execute_task() -> async
- send_context() -> async
- shutdown() -> async
- supports_peer_messaging() -> bool (sync)
- supports_self_claiming() -> bool (sync)
```

**Validation**: ✅ CORRECT pattern. Protocol + runtime_checkable is the standard Python typing approach.

---

### MCP Client Pattern (REQ-024, TECH-019)

**PRD Claims**:
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Missing: await session.initialize()  ❌ C2 issue
        result = await session.call_tool(...)
```

**Validation**: ⚠️ MISSING session.initialize() (C2 above). Otherwise correct.

---

### Hook Configuration (TECH-004, REQ-010..016)

**PRD Claims**:
```python
@dataclass
class HookConfig:
    hooks: dict[str, list[dict[str, Any]]]
    scripts: dict[str, str]
```

**Research Pattern**:
```json
{
  "hooks": {
    "TaskCompleted": [{
      "hooks": [{
        "type": "agent",
        "prompt": "...",
        "timeout": 120
      }]
    }]
  }
}
```

**Validation**: ✅ CORRECT structure matches Section 2.2 schema.

---

### MCP Tool Call Pattern (TECH-017, TECH-018)

**PRD Claims**:
```python
_extract_json(result: Any) -> Any:
    # Iterates result.content, finds TextContent, parses JSON

_extract_text(result: Any) -> str:
    # Iterates result.content, returns first text
```

**Research Pattern**:
```python
if result.content:
    for content in result.content:
        if isinstance(content, types.TextContent):
            return content.text
```

**Validation**: ✅ CORRECT pattern matches Section 3.4.

---

## SERVICE-TO-API WIRING VERIFICATION

All 13 SVC-xxx contracts verified:

| SVC-ID | Contract | Validation |
|--------|----------|-----------|
| SVC-001 | get_contract | ✅ Matches BUILD2_TECHNOLOGY_RESEARCH.md Section 7.2 |
| SVC-002 | validate_endpoint | ✅ Matches research |
| SVC-003 | generate_tests | ✅ Matches research |
| SVC-004 | check_breaking_changes | ✅ Matches research |
| SVC-005 | mark_implemented | ✅ Matches research |
| SVC-006 | get_unimplemented_contracts | ✅ Matches research |
| SVC-007 | find_definition | ✅ Matches Section 7.3 |
| SVC-008 | find_callers | ✅ Matches research |
| SVC-009 | find_dependencies | ✅ Matches research |
| SVC-010 | search_semantic | ✅ Matches research |
| SVC-011 | get_service_interface | ✅ Matches research |
| SVC-012 | check_dead_code | ✅ Matches research |
| SVC-013 | register_artifact | ✅ Matches research |

All SVC contracts include correct request/response DTO schemas matching Build 1 specifications.

---

## KNOWN LIMITATIONS VERIFICATION

**PRD Claims** (INT-009, Section 1.8 implications):
- Agent Teams is experimental
- No session resumption
- No nested teams
- One team per session
- Windows Terminal split panes unsupported

**Research Validation** (Section 1.8):
All 6 limitations are correctly documented in the PRD.

**Additional limitation NOT in PRD**:
- From research: "Permissions set at spawn — cannot dynamically modify teammate permissions"

**Recommendation**: Add to INT-009: "Teammate permissions are set at spawn time and cannot be changed mid-session."

---

## FALLBACK STRATEGY VERIFICATION

**PRD Claims**:
1. Agent Teams → CLI subprocess fallback (REQ-009, INT-009)
2. Contract Engine MCP → static API contract scan fallback (INT-001)
3. Codebase Intelligence MCP → static codebase_map.py fallback (INT-002)
4. Architect MCP → standard PRD decomposition fallback (INT-003, needs clarification per W11)

**Research Requirements** (Section 13 Cross-Build Dependencies):
All 4 fallbacks are required and documented.

**Validation**: ✅ CORRECT with W11 caveat.

---

## DEPTH GATING VERIFICATION

**PRD Claims** (TECH-044):
```
| Feature | quick | standard | thorough | exhaustive |
| agent_teams.enabled | False | False | True (if env set) | True |
| contract_engine.enabled | False | True (validation only) | True (full) | True |
| codebase_intelligence.enabled | False | True (queries only) | True (full) | True |
```

**Issue**: See W6 above — depth setting vs explicit YAML override priority is unclear.

**Validation**: ⚠️ NEEDS CLARIFICATION (W6).

---

## BACKWARD COMPATIBILITY VERIFICATION

**PRD Claims** (INT-006, INT-007, INT-008, INT-020):
- All new config sections default to `enabled: False`
- `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]` (preserved)
- Existing `Violation` dataclass interface preserved
- Disabling all Build 2 features produces identical v14.0 behavior

**Research Requirements** (SUPER_TEAM_RESEARCH_REPORT.md Section 10):
> "Key Architecture Patterns to Preserve in Build 2:
> 1. 15-stage pipeline
> 2. 13 self-healing fix loops
> 3. Post-orchestration scan chain
> 4. Milestone-based execution
> 5. Config-gated features
> 6. Depth-based behavior"

**Validation**: ✅ CORRECT. All patterns preserved.

---

## FINAL RECOMMENDATIONS

### Must Fix Before Implementation (CRITICAL)
1. Fix C1: Remove `cost_usd` from TaskResult
2. Fix C2: Add `session.initialize()` requirement to all MCP integration specs
3. Fix C3: Define complete HookInput dataclass with event-specific fields

### Should Clarify (WARNING)
1. W1: Agent teams wave-level fallback logic
2. W2: MCP timeout configuration values
3. W6: Depth gating vs explicit config override priority
4. W7: MCP server command path (relative vs absolute)
5. W11: Architect MCP fallback strategy

### Consider for Quality (INFO)
1. I1: MCP connection pooling
2. I2: Structured logging for MCP calls
3. I3: MCP server health checks
4. I9: Add retry logic to ContractEngineClient (promoted from W9)

---

## OVERALL ASSESSMENT

**Strengths**:
- Comprehensive coverage of all research findings
- All 7 corrections applied correctly
- Technology stack matches validated versions
- Fallback strategies are well-designed
- Backward compatibility is preserved

**Weaknesses**:
- 3 critical API errors that would cause runtime failures
- 11 ambiguities in specifications
- Some edge cases not fully addressed (Windows hooks, MCP timeouts)

**Verdict**: ⚠️ **PASS WITH WARNINGS**

The PRD is **implementable after fixing the 3 critical issues**. The warning issues should be addressed during milestone planning, but they do not block implementation start.

---

**Review Completed**: 2026-02-14
**Next Action**: Fix C1, C2, C3 → Update PRD → Re-review critical sections → Proceed to implementation
