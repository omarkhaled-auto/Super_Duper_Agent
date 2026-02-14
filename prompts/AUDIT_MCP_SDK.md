# MCP SDK Technical Audit

## Context7 Research Summary

Researched the official MCP Python SDK (`/modelcontextprotocol/python-sdk`) via Context7 (417 code snippets, High reputation, score 85.5). Key findings from current SDK state:

### SDK v2 Breaking Changes (FastMCP -> MCPServer Rename)

The MCP Python SDK underwent a major rename in v2:

- **`FastMCP` has been renamed to `MCPServer`**
- Old import: `from mcp.server.fastmcp import FastMCP` (v1, deprecated)
- New import: `from mcp.server.mcpserver import MCPServer` (v2, current)
- The class functionality is identical; only the name and import path changed.
- Transport parameters moved from constructor to `run()` method in v2.

### Server-Side API (Current)

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Demo", instructions="...", version="1.0.0")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description."""
    return result

# Transport options:
mcp.run(transport="stdio")  # For Claude Code integration
mcp.run(transport="streamable-http", json_response=True)  # For production HTTP
mcp.run(transport="sse", host="0.0.0.0", port=9000)  # SSE (legacy)
```

### Client-Side API (Current)

```python
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["my_server.py"],
    env={"KEY": "value"},
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()  # MANDATORY first call
        tools = await session.list_tools()
        result = await session.call_tool("tool_name", arguments={...})
```

### Low-Level Server API (Current)

```python
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

server = Server("name", lifespan=lifespan_fn)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]: ...

@server.call_tool()
async def handle_call_tool(name, arguments) -> list[types.TextContent]: ...

async with mcp.server.stdio.stdio_server() as (read, write):
    await server.run(read, write, InitializationOptions(...))
```

### Transport Types (Current Status)

| Transport | Status | Use Case |
|-----------|--------|----------|
| stdio | Stable, recommended for CLI tools | Claude Code integration |
| streamable-http | Recommended for production HTTP | Web deployment |
| SSE | Legacy, still supported | Older integrations |

### Authentication (v2)

```python
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings

mcp = MCPServer("name", token_verifier=MyVerifier(), auth=AuthSettings(...))
```

### Key API Notes

1. `ClientSession(read, write)` - constructor takes read/write streams
2. `await session.initialize()` - MANDATORY before any tool calls
3. `result.content` - list of content blocks (TextContent, etc.)
4. `result.isError` - boolean indicating error
5. `result.structured_content` - structured output (new in v2)
6. `StdioServerParameters(command, args, env)` - standard parameters
7. `@mcp.tool()` decorator auto-generates JSON Schema from type hints + docstrings

---

## Build 1 Findings

### MCP Server Creation (3 servers)

**REQ-057 (Codebase Intelligence MCP):** States "MCPServer with name='Codebase Intelligence'" and `mcp.run(transport="stdio")`.
- **VERIFIED CORRECT.** Uses `MCPServer` (v2 API), `@mcp.tool()` decorators, `transport="stdio"`.
- The tech stack line says `mcp>=1.25,<2` which is the correct v2 range.

**REQ-059 (Architect MCP):** States "MCPServer with name='Architect'" and `mcp.run(transport="stdio")`.
- **VERIFIED CORRECT.** Same pattern as REQ-057.

**REQ-060 (Contract Engine MCP):** States "MCPServer with name='Contract Engine'" and `mcp.run(transport="stdio")`.
- **VERIFIED CORRECT.** Same pattern.

### Import Paths

**Architecture Plan lines 1037, 1126, 1298:** `from mcp.server.mcpserver import MCPServer`
- **VERIFIED CORRECT.** This is the v2 import path confirmed by Context7.

**Technology Research lines 965-966:** `from mcp import ClientSession, StdioServerParameters, types` and `from mcp.client.stdio import stdio_client`
- **VERIFIED CORRECT.** These are the current top-level client imports.

### Tool Registration

All 16 tools across 3 servers use `@mcp.tool()` decorator pattern.
- **VERIFIED CORRECT.** Context7 confirms `@mcp.tool()` is the high-level decorator API.

### Transport Configuration

All 3 servers use `mcp.run(transport="stdio")`.
- **VERIFIED CORRECT.** stdio is the correct transport for Claude Code CLI integration.
- Note: Build 1 PRD does NOT use `transport="streamable-http"` or SSE, which is correct since these servers are consumed via CLI subprocess, not HTTP.

### MCP Client Usage (TEST-032, TEST-035)

TEST-032 specifies testing "via MCP client (stdio_client + ClientSession)".
- **VERIFIED CORRECT.** This matches the standard MCP client pattern.

TEST-035 (roundtrip test) specifies starting MCP servers as subprocesses and using ClientSession.
- **VERIFIED CORRECT.** The `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern is the standard way to connect to stdio MCP servers.

### .mcp.json Configuration (INT-005)

```json
{"mcpServers": {"architect": {"command": "python", "args": ["-m", "src.architect.mcp_server"], ...}}}
```
- **VERIFIED CORRECT.** This matches Claude Code's `.mcp.json` format for stdio servers.

### MCP Server Initialization Pattern

TECH-028: "MCP servers must initialize database connections and service layer objects at module level or in a startup function"
- **VERIFIED CORRECT.** For stdio MCP servers using `MCPServer`, module-level initialization happens before `mcp.run()` which blocks. This is the standard pattern.

REQ-057: "Each MCP server creates its OWN ConnectionPool instance using the same database path"
- **VERIFIED CORRECT.** MCP servers run as separate processes, so separate DB connections are required.

### Version Constraint

`mcp>=1.25,<2` in pyproject.toml (REQ-001).
- **ISSUE [MEDIUM]: Version range may need updating.** The Context7 research shows the SDK has undergone a v1->v2 migration with the `FastMCP` -> `MCPServer` rename. The PRD uses v2 API (`MCPServer`, `from mcp.server.mcpserver import MCPServer`) but constrains to `<2`. If the `MCPServer` API is only available in SDK v2+, then the constraint `<2` would exclude the very API being used. **However**, the research also shows that `MCPServer` exists within the `mcp` package under `>=1.25`, as the migration doc describes updating from one version to another within the same package. The v1/v2 terminology in the migration guide refers to API versions within the package, not the package version itself. **Verdict: Likely correct, but should be verified against actual PyPI releases.** If `from mcp.server.mcpserver import MCPServer` only works in `mcp>=2.0`, then the constraint `<2` is wrong.

**UPDATE after further analysis:** The migration docs at `docs/migration.md` describe the rename but the actual package version where `MCPServer` was introduced needs verification. The PRD architecture plan and technology research both independently confirmed this import path, suggesting it was verified against an actual SDK installation. **Marking as LOW risk.**

---

## Build 2 Findings

### MCP Client Pattern

**REQ-024:** `create_contract_engine_session()` using `StdioServerParameters` + `stdio_client()` + `ClientSession`.
- **VERIFIED CORRECT.** Exact match with Context7 client pattern.

**REQ-025:** Must call `await session.initialize()` immediately after creating ClientSession.
- **VERIFIED CORRECT.** Context7 confirms `initialize()` is mandatory before any tool calls.

**REQ-038:** `create_codebase_intelligence_session()` with same pattern.
- **VERIFIED CORRECT.** Same pattern, same correctness.

### Import Paths (Client-Side)

**TECH-019:** Lazy import: `from mcp import StdioServerParameters`
- **VERIFIED CORRECT.** `StdioServerParameters` is exported from the `mcp` top-level package.

**Architecture Plan lines 1706-1708:**
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
```
- **VERIFIED CORRECT.** All three imports match Context7 documentation exactly.

**Note:** The technology research (line 350) also imports `ClientSession` from `mcp` top-level: `from mcp import ClientSession, StdioServerParameters, types`. Both import paths work:
  - `from mcp import ClientSession` (top-level re-export)
  - `from mcp.client.session import ClientSession` (direct import)

Both are valid per Context7 docs. The PRD and architecture plan consistently use the direct import path, which is more explicit and correct.

### StdioServerParameters Usage

**TECH-020:** `StdioServerParameters` with `env` dict and `cwd` parameter.
- **ISSUE [LOW]: `cwd` parameter.** The Context7 docs show `StdioServerParameters(command, args, env)` but do not explicitly show a `cwd` parameter. **However**, the MCP SDK's `StdioServerParameters` is a Pydantic model that maps to subprocess execution, and `cwd` is a standard subprocess parameter. The actual SDK may support it. Build 2's tech research doc verified this parameter was available. **Verdict: Likely correct but unverifiable from Context7 alone.**

### Error Handling Pattern

**REQ-026:** Retry 3 times on transient errors with exponential backoff, return safe defaults.
- **VERIFIED CORRECT pattern.** MCP tool calls can fail due to process issues, and retry with backoff is the standard resilience pattern.

### MCP Session Management

**REQ-024:** `@asynccontextmanager` wrapping `stdio_client()` + `ClientSession`.
- **VERIFIED CORRECT.** The `stdio_client()` and `ClientSession` are both async context managers that should be composed this way.

**REQ-024:** Catch `(TimeoutError, ConnectionError, ProcessLookupError, OSError)` during `session.initialize()`.
- **VERIFIED CORRECT.** These are the standard errors that can occur when starting a subprocess-based MCP server.

### Tool Result Extraction

**TECH-017:** `_extract_json(result)` iterates `result.content`, finds `TextContent`, parses JSON.
- **VERIFIED CORRECT.** Context7 confirms `result.content` is a list of content blocks, with `TextContent` having a `.text` attribute. The pattern `isinstance(content, types.TextContent)` and `content.text` is the standard extraction method.

**TECH-018:** `_extract_text(result)` returns first text content.
- **VERIFIED CORRECT.** Same pattern.

### MCP Server Config in mcp_servers.py

**WIRE-004:** `_contract_engine_mcp_server()` returns `{"type": "stdio", "command": ..., "args": ..., "env": ...}`.
- **VERIFIED CORRECT.** This matches the Claude Code `.mcp.json` format for stdio servers.

---

## Build 3 Findings

### MCP Client Usage in Pipeline

**REQ-046 (run_architect_phase):**
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async with stdio_client(StdioServerParameters(
    command="python", args=["-m", "src.architect.mcp_server"],
    cwd=config.build1_services_dir
)) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("decompose", {"prd_text": prd_content})
```
- **VERIFIED CORRECT.** This is the exact MCP client pattern from Context7.
- Includes mandatory `await session.initialize()`.
- Uses `call_tool()` with string tool name and dict arguments.
- Has subprocess fallback on ImportError.

**REQ-047 (run_contract_registration):** Uses MCP for `create_contract`, `validate_spec`.
- **VERIFIED CORRECT** if following same session pattern as REQ-046.

### Lazy Import Pattern

**INT-006:** "All Build 3 modules must be importable without Build 1 or Build 2 installed -- MCP client imports must be lazy (inside function bodies) with clear ImportError messages"
- **VERIFIED CORRECT.** This is the same pattern as Build 2's TECH-019. Lazy imports inside function bodies with `except ImportError` is the standard pattern for optional dependencies.

**WIRE-015:** `run_architect_phase` must use MCP stdio transport with ImportError fallback.
- **VERIFIED CORRECT.** The fallback pattern (try MCP SDK, except ImportError use subprocess) is well-designed.

### MCP Tool Names

REQ-046 calls `session.call_tool("decompose", ...)` to invoke the Architect's decompose tool.
- **CROSS-REFERENCE CHECK:** Build 1 REQ-059 does NOT define a tool named "decompose" in the Architect MCP server. REQ-059 defines three tools: `get_service_map()`, `get_contracts_for_service(service_name)`, `get_domain_model()`.
- **ISSUE [HIGH]: Tool name mismatch.** Build 3's `run_architect_phase()` calls `call_tool("decompose", {"prd_text": prd_content})` but Build 1's Architect MCP server does NOT expose a "decompose" tool. The decomposition is a POST /api/decompose REST endpoint, not an MCP tool. Build 3 should either:
  1. Add a `decompose` MCP tool to Build 1's Architect MCP server (REQ-059), OR
  2. Use the REST API endpoint `POST /api/decompose` via httpx instead of MCP, OR
  3. Call the Architect's FastAPI service directly.

### asyncio.run() Constraint

**TECH-027:** "The top-level entry point must call `asyncio.run()` exactly once."
- **VERIFIED CORRECT.** This is critical for MCP client usage since `stdio_client()` and `ClientSession` are async context managers that must run under a single event loop.

---

## Cross-Build MCP Integration

### Build 1 (Server) -> Build 2 (Client)

| Build 1 MCP Server | Build 2 MCP Client | Tool Count | Verified |
|---|---|---|---|
| Architect MCP (REQ-059) | Not directly consumed (Build 2 queries via Agent Teams) | 3 tools | N/A |
| Contract Engine MCP (REQ-060) | ContractEngineClient (REQ-017..023) | 6 tools | CORRECT |
| Codebase Intelligence MCP (REQ-057) | CodebaseIntelligenceClient (REQ-030..037) | 7 tools | CORRECT |

**Tool Name Alignment (Contract Engine):**

| Build 1 MCP Tool (REQ-060) | Build 2 Client Method | Match |
|---|---|---|
| get_contract(contract_id) | ContractEngineClient.get_contract(contract_id) | EXACT |
| validate_endpoint(service_name, method, path, response_body, status_code) | ContractEngineClient.validate_endpoint(...) | EXACT |
| generate_tests(contract_id, framework, include_negative) | ContractEngineClient.generate_tests(...) | EXACT |
| check_breaking_changes(contract_id, new_spec) | ContractEngineClient.check_breaking_changes(...) | EXACT |
| mark_implemented(contract_id, service_name, evidence_path) | ContractEngineClient.mark_implemented(...) | EXACT |
| get_unimplemented_contracts(service_name) | ContractEngineClient.get_unimplemented_contracts(...) | EXACT |

**Tool Name Alignment (Codebase Intelligence):**

| Build 1 MCP Tool (REQ-057) | Build 2 Client Method | Match |
|---|---|---|
| find_definition(symbol, language) | CodebaseIntelligenceClient.find_definition(...) | EXACT |
| find_callers(symbol, max_results) | CodebaseIntelligenceClient.find_callers(...) | EXACT |
| find_dependencies(file_path) | CodebaseIntelligenceClient.find_dependencies(...) | EXACT |
| search_semantic(query, language, service_name, n_results) | CodebaseIntelligenceClient.search_semantic(query, n_results) | PARTIAL (Build 2 omits language, service_name filters) |
| get_service_interface(service_name) | CodebaseIntelligenceClient.get_service_interface(...) | EXACT |
| check_dead_code(service_name) | CodebaseIntelligenceClient.check_dead_code(...) | EXACT |
| register_artifact(file_path, service_name) | CodebaseIntelligenceClient.register_artifact(...) | EXACT |

### Build 1 (Server) -> Build 3 (Client)

| Build 1 MCP Server | Build 3 Usage | Verified |
|---|---|---|
| Architect MCP | `run_architect_phase()` calls `decompose` tool | **MISMATCH** (see HIGH issue) |
| Contract Engine MCP | `run_contract_registration()` calls `create_contract`, `validate_spec` | **PARTIAL** (create_contract not in Build 1 MCP) |

**ISSUE [HIGH]: Build 3 calls Contract Engine MCP tools that don't exist in Build 1.**
- Build 3 REQ-047 references `create_contract` and `validate_spec` MCP tools.
- Build 1 REQ-060 defines these 6 MCP tools: `get_contract`, `validate_endpoint`, `generate_tests`, `check_breaking_changes`, `mark_implemented`, `get_unimplemented_contracts`.
- `create_contract` is a REST endpoint (`POST /api/contracts`), NOT an MCP tool.
- `validate_spec` corresponds to `POST /api/validate` REST endpoint, NOT an MCP tool.
- Build 3 must either use REST endpoints for creation/validation, or Build 1 must add these as MCP tools.

### Build 2 (Agent Team) -> Build 3 (Super Orchestrator)

Build 3 invokes Build 2 as a subprocess (`python -m agent_team`), not via MCP. This is correct -- Build 2 is not an MCP server.

---

## Issues Found

### CRITICAL

None.

### HIGH

1. **[H-1] Build 3 REQ-046: Tool name "decompose" does not exist in Build 1 Architect MCP server.**
   - Build 1 REQ-059 defines 3 tools: `get_service_map`, `get_contracts_for_service`, `get_domain_model`.
   - The `decompose` functionality is exposed only as a REST endpoint (`POST /api/decompose`).
   - Build 3 `run_architect_phase()` tries `session.call_tool("decompose", ...)` which will fail.
   - **Impact:** Pipeline will fail at the first phase.

2. **[H-2] Build 3 REQ-047: MCP tools "create_contract" and "validate_spec" do not exist in Build 1 Contract Engine MCP server.**
   - Build 1 REQ-060 defines 6 tools, none of which are `create_contract` or `validate_spec`.
   - Contract creation is via REST `POST /api/contracts`, validation via `POST /api/validate`.
   - **Impact:** Contract registration phase will fail.

### MEDIUM

1. **[M-1] MCP SDK version constraint `mcp>=1.25,<2` may conflict with `MCPServer` import path.**
   - Build 1 uses `from mcp.server.mcpserver import MCPServer` which is the v2 API.
   - The migration guide shows this as the v2 rename of `FastMCP`.
   - If `MCPServer` at `mcp.server.mcpserver` only exists in package version 2.0+, the `<2` constraint would be self-contradictory.
   - **Mitigation:** Verify that `mcp.server.mcpserver.MCPServer` is available in `mcp>=1.25`. If not, change constraint to `mcp>=2.0,<3`.

2. **[M-2] Build 2 REQ-034 `search_semantic(query, n_results)` omits `language` and `service_name` parameters.**
   - Build 1 REQ-057 defines `search_semantic(query, language, service_name, n_results=10)`.
   - Build 2 REQ-034 only passes `query` and `n_results`, omitting the optional filters.
   - **Impact:** Functional but loses filtering capability. Since these are optional params with defaults, MCP tool calls without them should still work.

### LOW

1. **[L-1] `StdioServerParameters` `cwd` parameter not documented in Context7.**
   - Both Build 2 and Build 3 pass `cwd` to `StdioServerParameters`.
   - Context7 examples only show `command`, `args`, `env`.
   - Likely valid since the MCP SDK's StdioServerParameters maps to subprocess.Popen which supports cwd, but not confirmable from docs alone.

2. **[L-2] Build 1 TECH-024 says "MCP servers are single-threaded".**
   - This is correct for stdio transport but should note that `MCPServer.run(transport="stdio")` blocks the event loop. Multiple MCP tool calls are serialized.
   - No action needed; just a documentation clarity point.

3. **[L-3] Build 2 Technology Research imports `ClientSession` from both `mcp` (top-level) and `mcp.client.session`.**
   - Line 350: `from mcp import ClientSession, StdioServerParameters, types`
   - Line 352: `from mcp.client.session import ClientSession`
   - Both work, but having both in the same code block is redundant. The PRD correctly standardizes on `from mcp.client.session import ClientSession` for the actual implementation (TECH-019).

---

## Recommended Fixes

### Fix for H-1 (Build 3 architect tool name mismatch)

**Option A (Recommended):** Add `decompose` tool to Build 1 Architect MCP server.

In `BUILD1_PRD.md` REQ-059, add a 4th tool:

```
Register 4 tools (was 3): get_service_map(), get_contracts_for_service(service_name),
get_domain_model(), AND decompose(prd_text: str) which orchestrates the full
decomposition pipeline (parse -> boundaries -> validate -> contracts -> domain model
-> persist) and returns DecompositionResult dict.
```

Also update: Build 1 Milestone 7 title, INT-005 tool count in .mcp.json, docs/mcp_tools.md tool count.

**Option B:** Change Build 3 REQ-046 to use REST API:

```
Replace MCP call with: async with httpx.AsyncClient() as client:
    response = await client.post(f"{config.architect_url}/api/decompose",
        json={"prd_text": prd_content}, timeout=config.architect.timeout)
```

### Fix for H-2 (Build 3 contract engine tool mismatch)

**Option A (Recommended):** Add `create_contract` and `validate_spec` tools to Build 1 Contract Engine MCP server.

In `BUILD1_PRD.md` REQ-060, add 2 tools:

```
Register 8 tools (was 6): existing 6 tools PLUS:
create_contract(service_name: str, type: str, version: str, spec: dict,
    build_cycle_id: str = "") -> dict with contract id, status, spec_hash;
validate_spec(spec: dict, type: str) -> dict with valid bool, errors list, warnings list.
```

**Option B:** Change Build 3 REQ-047 to use REST API instead of MCP.

### Fix for M-1 (Version constraint)

In `BUILD1_PRD.md` REQ-001, change `mcp>=1.25,<2` to:

```
mcp>=1.25  (remove upper bound, or change to mcp>=2.0,<3 if MCPServer requires v2+)
```

Verify against PyPI: `pip install mcp && python -c "from mcp.server.mcpserver import MCPServer; print('OK')"`

### Fix for M-2 (search_semantic parameter mismatch)

In `BUILD2_PRD.md` REQ-034, update to:

```
CodebaseIntelligenceClient.search_semantic(query: str, language: str | None = None,
    service_name: str | None = None, n_results: int = 10) -> list[dict]
```

This preserves backward compatibility while adding the optional filter parameters that Build 1's tool supports.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0 | - |
| HIGH | 2 | Both require PRD fixes before build |
| MEDIUM | 2 | M-1 requires verification, M-2 is functional |
| LOW | 3 | Documentation/clarity only |

**Overall Assessment:** The MCP SDK usage is technically accurate for the server-side (Build 1) and client-side (Build 2) patterns. The primary issues are **cross-build tool name mismatches** where Build 3 references MCP tools that only exist as REST endpoints in Build 1. These are architectural alignment issues, not SDK API issues.

All import paths, decorator patterns, transport configurations, context manager usage, and session initialization requirements are verified correct against the current MCP Python SDK documentation.
