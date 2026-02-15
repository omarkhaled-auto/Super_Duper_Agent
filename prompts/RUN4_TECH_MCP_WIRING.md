# Run 4 Technical Research: MCP Wiring Patterns

## Purpose

This document provides the technical foundation for Run 4's MCP wiring verification between Build 1 (3 MCP servers) and Build 2 (3 MCP clients). It covers stdio transport lifecycle, handshake protocol, error recovery, cross-build tool mapping, multi-server coordination, and testing strategies.

---

## 1. MCP stdio Transport Session Lifecycle

### 1.1 How stdio-based MCP Servers Start

The MCP Python SDK uses subprocess-based stdio transport. The client spawns the server as a child process, communicating via stdin/stdout pipes using JSON-RPC 2.0 messages.

**Process spawn sequence:**

```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "src.contract_engine.mcp_server"],
    env={"DATABASE_PATH": "./data/contracts.db"},
    cwd="/path/to/build1/project"  # server_root from config
)

async with stdio_client(server_params) as (read, write):
    # Server process is now running, stdin/stdout pipes connected
    async with ClientSession(read, write) as session:
        await session.initialize()  # MANDATORY first call
        # Session is now active, tools are available
```

**Server-side startup (Build 1 pattern):**

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Contract Engine",
    instructions="Store, validate, query, and generate tests from contracts.",
    version="1.0.0"
)

@mcp.tool()
def validate_endpoint(service_name: str, method: str, path: str,
                      response_body: dict, status_code: int = 200) -> dict:
    """Validate an API response against its contracted schema."""
    # Implementation...
    return {"valid": True, "violations": []}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 1.2 Session Lifecycle States

```
[Not Started] -> spawn subprocess -> [Process Running]
[Process Running] -> client sends initialize -> [Handshake]
[Handshake] -> server responds with capabilities -> [Active]
[Active] -> tool calls, list_tools, etc. -> [Active]
[Active] -> client exits context manager -> [Shutting Down]
[Shutting Down] -> process terminated -> [Terminated]
```

**Key lifecycle facts for Run 4:**

1. **Each `stdio_client()` context manager spawns a new process.** There is no connection pooling. Build 2's `create_contract_engine_session()` and `create_codebase_intelligence_session()` each spawn independent server processes.

2. **Session state is per-process.** When the context manager exits, the process is terminated. All in-memory state (ConnectionPool instances, cached data) is lost. Database state persists on disk.

3. **MCP servers are single-threaded** (TECH-024 from Build 1 PRD). The SDK runs sync tool functions in a thread pool via `anyio.to_thread.run_sync()`, but the event loop is single-threaded.

4. **Long-lived sessions are the expected pattern.** Build 2 should open an MCP session at the start of a phase and keep it open for multiple tool calls, not open/close per call.

### 1.3 Process Lifecycle Management

**Health checking:** MCP stdio transport has no built-in health check mechanism. The process is alive if stdin/stdout pipes are open. Build 2's clients detect server death when:
- `call_tool()` raises `OSError` (broken pipe)
- `call_tool()` raises `ConnectionError` (process exited)
- The async context manager's `__aexit__` is triggered by an exception

**Restart pattern:** The MCP SDK does not provide automatic restart. Build 2 must implement restart at the application level:

```python
# Build 2 pattern: retry with new session on transient failure
async def _call_with_retry(self, tool_name: str, arguments: dict,
                           max_retries: int = 3) -> Any:
    for attempt in range(max_retries):
        try:
            async with create_contract_engine_session(self._config) as session:
                result = await session.call_tool(tool_name, arguments=arguments)
                return result
        except (OSError, TimeoutError, ConnectionError) as e:
            if attempt == max_retries - 1:
                logger.warning("MCP call failed after %d retries: %s",
                               max_retries, e, exc_info=True)
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
```

**Session state persistence:** MCP sessions themselves have no state to persist. All persistent state lives in the underlying databases (SQLite files for Build 1). If a session is lost and restarted, the new session has full access to the same data through the database.

---

## 2. MCP Client-to-Server Handshake

### 2.1 Initialize Request/Response Protocol

The `session.initialize()` call is the MANDATORY first operation (REQ-025 from Build 2 PRD). This is a JSON-RPC 2.0 request/response exchange:

**Client sends:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "sampling": {}
    },
    "clientInfo": {
      "name": "agent-team",
      "version": "1.0.0"
    }
  }
}
```

**Server responds:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": { "listChanged": false }
    },
    "serverInfo": {
      "name": "Contract Engine",
      "version": "1.0.0"
    },
    "instructions": "Store, validate, query, and generate tests from contracts."
  }
}
```

**Client sends initialized notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 2.2 Capability Negotiation

Build 1's MCP servers expose only `tools` capability (no resources, no prompts, no sampling). The capability object tells the client what features are available:

| Server | Capabilities | Notes |
|--------|-------------|-------|
| Architect | `tools` | 4 tools, no resources |
| Contract Engine | `tools` | 9 tools, no resources |
| Codebase Intelligence | `tools` | 7 tools, no resources |

**Run 4 verification point:** After `session.initialize()`, verify `result.capabilities.tools` is present for all 3 servers.

### 2.3 Tool Listing and Schema Exchange

After initialization, the client discovers available tools:

```python
tools = await session.list_tools()
for tool in tools.tools:
    print(f"Tool: {tool.name}")
    print(f"  Description: {tool.description}")
    print(f"  Input Schema: {tool.inputSchema}")
```

The MCP SDK auto-generates JSON Schemas from Python type hints and docstrings (TECH-027). **Run 4 must verify:**
1. All expected tools are listed (4 + 9 + 7 = 20 total)
2. Input schemas match the expected parameter types
3. Tool names match exactly (no typos, no prefix collisions)

---

## 3. Error Recovery Patterns

### 3.1 Server Crash Mid-Call

When an MCP server crashes during a `call_tool()` invocation, the behavior is:

1. The server process exits (SIGKILL, unhandled exception, OOM)
2. stdout pipe closes
3. `call_tool()` raises `OSError: [Errno 32] Broken pipe` or similar
4. The `stdio_client` context manager's cleanup runs
5. Any pending reads on the pipe raise `ConnectionError`

**Build 2's handling (from REQ-026, REQ-042):**

```python
# Every ContractEngineClient / CodebaseIntelligenceClient method pattern:
async def validate_endpoint(self, service_name: str, method: str,
                            path: str, response_body: dict,
                            status_code: int = 200) -> ContractValidation:
    for attempt in range(3):
        try:
            result = await self._session.call_tool(
                "validate_endpoint",
                arguments={
                    "service_name": service_name,
                    "method": method,
                    "path": path,
                    "response_body": response_body,
                    "status_code": status_code
                }
            )
            if result.isError:
                return ContractValidation(error="Server returned error")
            data = self._extract_json(result)
            return ContractValidation(
                valid=data.get("valid", False),
                violations=data.get("violations", [])
            )
        except (OSError, TimeoutError, ConnectionError) as e:
            if attempt == 2:
                logger.warning("validate_endpoint failed: %s", e, exc_info=True)
                return ContractValidation(error=str(e))
            await asyncio.sleep(2 ** attempt)
        except (TypeError, ValueError) as e:
            # Non-transient: return immediately, no retry
            logger.warning("validate_endpoint non-transient error: %s", e)
            return ContractValidation(error=str(e))
```

### 3.2 Client-Side Retry Strategy

Build 2 implements exponential backoff with 3 retries (REQ-026, REQ-042):

| Attempt | Delay | Total Elapsed |
|---------|-------|---------------|
| 1 | 0s | 0s |
| 2 | 1s | 1s |
| 3 | 2s | 3s |
| (give up) | 4s | 7s |

**Transient errors (retry):** `OSError`, `TimeoutError`, `ConnectionError`, `ProcessLookupError`, MCP-specific connection errors.

**Non-transient errors (no retry):** `TypeError`, `ValueError`, `KeyError` — these indicate programming bugs, not infrastructure issues.

### 3.3 Timeout Handling

Build 2 defines two timeout levels (TECH-015, TECH-025):

| Timeout | Default | Purpose |
|---------|---------|---------|
| `startup_timeout_ms` | 30,000ms (30s) | Time for MCP server process to start and complete handshake |
| `tool_timeout_ms` | 60,000ms (60s) | Time for a single `call_tool()` to complete |

**Recommendation for Run 4:** The startup timeout may need to be longer for Codebase Intelligence (TECH-023 from Build 1: ChromaDB downloads ~80MB embedding model on first use). Consider 120s for first-time startup, 30s for subsequent starts.

### 3.4 Graceful Degradation

When an MCP server is completely unavailable, Build 2 falls back to static analysis:

| MCP Server Unavailable | Fallback Behavior |
|------------------------|-------------------|
| Contract Engine | Use static `run_api_contract_scan()` from quality_checks.py against SVC-xxx tables in REQUIREMENTS.md |
| Codebase Intelligence | Use static `generate_codebase_map()` from codebase_map.py |
| Architect | Standard PRD decomposition without live service map queries |

**Run 4 must verify** both the MCP path AND the fallback path work correctly.

---

## 4. Cross-Reference: Build 1 Servers ↔ Build 2 Clients

### 4.1 Architect Server (4 tools) → Build 2 ArchitectClient

| Tool Name | Parameters | Return Type | Build 2 Client Method | Fallback |
|-----------|-----------|-------------|----------------------|----------|
| `decompose` | `prd_text: str` | `DecompositionResult dict` | `ArchitectClient.decompose()` | Standard PRD decomposition |
| `get_service_map` | (none) | `ServiceMap dict` | `ArchitectClient.get_service_map()` | N/A (not critical) |
| `get_contracts_for_service` | `service_name: str` | `list[dict]` | `ArchitectClient.get_contracts_for_service()` | Read SVC-xxx from REQUIREMENTS.md |
| `get_domain_model` | (none) | `DomainModel dict` | `ArchitectClient.get_domain_model()` | N/A (not critical) |

**Note on `get_contracts_for_service`:** This tool calls Contract Engine via HTTP internally (TECH-026 from Build 1). It uses `httpx.Client` (sync) with `timeout=httpx.Timeout(connect=5.0, read=30.0)`. The MCP SDK runs this sync function in a thread pool automatically.

### 4.2 Contract Engine Server (9 tools) → Build 2 ContractEngineClient

| Tool Name | Parameters | Return Type | Build 2 Client Method | SVC-ID |
|-----------|-----------|-------------|----------------------|--------|
| `create_contract` | `service_name, type, version, spec, build_cycle_id` | `dict` with id, status, spec_hash | `ContractEngineClient.create_contract()` | — |
| `validate_spec` | `spec: dict, type: str` | `dict` with valid, errors, warnings | `ContractEngineClient.validate_spec()` | — |
| `list_contracts` | `service_name, type, page, page_size` | paginated list | `ContractEngineClient.list_contracts()` | — |
| `get_contract` | `contract_id: str` | `ContractEntry dict` or None | `ContractEngineClient.get_contract()` | SVC-001 |
| `validate_endpoint` | `service_name, method, path, response_body, status_code` | `dict` with valid, violations | `ContractEngineClient.validate_endpoint()` | SVC-002 |
| `generate_tests` | `contract_id, framework, include_negative` | test code string | `ContractEngineClient.generate_tests()` | SVC-003 |
| `check_breaking_changes` | `contract_id, new_spec` | `list[BreakingChange dict]` | `ContractEngineClient.check_breaking_changes()` | SVC-004 |
| `mark_implemented` | `contract_id, service_name, evidence_path` | `dict` with marked, total, all_implemented | `ContractEngineClient.mark_implemented()` | SVC-005 |
| `get_unimplemented_contracts` | `service_name: str` | `list[dict]` | `ContractEngineClient.get_unimplemented_contracts()` | SVC-006 |

**Build 2 PRD lists 6 tools** (SVC-001 through SVC-006), but Build 1 exposes 9. The 3 extra tools (`create_contract`, `validate_spec`, `list_contracts`) are available but not wrapped in dedicated Build 2 client methods. They may be called directly via `session.call_tool()` if needed.

### 4.3 Codebase Intelligence Server (7 tools) → Build 2 CodebaseIntelligenceClient

| Tool Name | Parameters | Return Type | Build 2 Client Method | SVC-ID |
|-----------|-----------|-------------|----------------------|--------|
| `find_definition` | `symbol: str, language: str \| None` | location dict or None | `CodebaseIntelligenceClient.find_definition()` | SVC-007 |
| `find_callers` | `symbol: str, max_results: int = 50` | `list[dict]` | `CodebaseIntelligenceClient.find_callers()` | SVC-008 |
| `find_dependencies` | `file_path: str` | imports/imported_by/transitive/circular dicts | `CodebaseIntelligenceClient.find_dependencies()` | SVC-009 |
| `search_semantic` | `query, language, service_name, n_results` | `list[SemanticSearchResult dict]` | `CodebaseIntelligenceClient.search_semantic()` | SVC-010 |
| `get_service_interface` | `service_name: str` | `ServiceInterface dict` | `CodebaseIntelligenceClient.get_service_interface()` | SVC-011 |
| `check_dead_code` | `service_name: str \| None` | `list[DeadCodeEntry dict]` | `CodebaseIntelligenceClient.check_dead_code()` | SVC-012 |
| `register_artifact` | `file_path: str, service_name: str` | stats dict | `CodebaseIntelligenceClient.register_artifact()` | SVC-013 |

### 4.4 Parameter Type Compatibility Matrix

**Critical wiring check:** Build 1 server tool parameter types must match Build 2 client call arguments exactly. The MCP SDK performs JSON Schema validation on tool inputs.

| Data Type | Build 1 Server (Python type hint) | Build 2 Client (call_tool argument) | Wire Compatible? |
|-----------|----------------------------------|--------------------------------------|-----------------|
| `str` | `symbol: str` | `{"symbol": "MyClass"}` | Yes |
| `int` | `max_results: int = 50` | `{"max_results": 50}` | Yes |
| `dict` | `spec: dict` | `{"spec": {...}}` | Yes (JSON object) |
| `bool` | `include_negative: bool = True` | `{"include_negative": true}` | Yes |
| `str \| None` | `language: str \| None = None` | `{"language": null}` or omit key | Yes (optional) |
| `int = 200` | `status_code: int = 200` | omit key (uses default) | Yes |

**Run 4 verification:** For each tool, call with all parameters explicit AND call with only required parameters (using defaults). Verify both work.

---

## 5. Multi-Server Coordination

### 5.1 Running 3+ MCP Servers Simultaneously

Each MCP server is an independent subprocess. Running 3 servers means 3 separate Python processes, each with its own:
- Event loop
- ConnectionPool (SQLite connections)
- Memory space
- stdin/stdout pipes

```python
# Build 2's get_contract_aware_servers() combines all servers
def get_contract_aware_servers(config: AgentTeamConfig) -> dict[str, Any]:
    servers = get_mcp_servers(config)  # Existing servers (playwright, context7, etc.)
    if config.contract_engine.enabled:
        servers["contract-engine"] = _contract_engine_mcp_server(config.contract_engine)
    if config.codebase_intelligence.enabled:
        servers["codebase-intelligence"] = _codebase_intelligence_mcp_server(
            config.codebase_intelligence
        )
    return servers
```

**Resource considerations for 3 simultaneous servers:**

| Resource | Per Server | Total (3 servers) |
|----------|-----------|-------------------|
| Python process | ~50-80MB RAM | ~150-240MB |
| SQLite WAL connections | 1 per thread | 3-9 connections |
| ChromaDB embedding model | ~80MB (Codebase Intel only) | ~80MB |
| File descriptors | 2 (stdin/stdout) | 6 |

### 5.2 Tool Namespace Collision Avoidance

Each MCP server is accessed through a separate `ClientSession`. There is **no namespace collision risk** because tools are scoped to their session:

```python
# Each session is independent — no name collisions possible
async with create_contract_engine_session(config) as contract_session:
    await contract_session.call_tool("get_contract", ...)  # Contract Engine's tool

async with create_codebase_intelligence_session(config) as codebase_session:
    await codebase_session.call_tool("get_service_interface", ...)  # CI's tool
```

However, when Claude Code uses `.mcp.json` to auto-load servers, all tools from all servers appear in a flat namespace. **Run 4 must verify** no tool name collisions exist across all 3 servers:

| Tool Name | Architect | Contract Engine | Codebase Intel | Collision? |
|-----------|-----------|----------------|----------------|------------|
| `decompose` | X | | | No |
| `get_service_map` | X | | | No |
| `get_contracts_for_service` | X | | | No |
| `get_domain_model` | X | | | No |
| `create_contract` | | X | | No |
| `validate_spec` | | X | | No |
| `list_contracts` | | X | | No |
| `get_contract` | | X | | No |
| `validate_endpoint` | | X | | No |
| `generate_tests` | | X | | No |
| `check_breaking_changes` | | X | | No |
| `mark_implemented` | | X | | No |
| `get_unimplemented_contracts` | | X | | No |
| `find_definition` | | | X | No |
| `find_callers` | | | X | No |
| `find_dependencies` | | | X | No |
| `search_semantic` | | | X | No |
| `get_service_interface` | | | X | No |
| `check_dead_code` | | | X | No |
| `register_artifact` | | | X | No |

**Result: 20 unique tool names, zero collisions.** All names are descriptive and service-specific.

### 5.3 Shared State Between Servers

Build 1 servers share state through two mechanisms:

**Mechanism 1: Database files (read-after-write)**

| Server | Database | Used By Other Servers? |
|--------|----------|----------------------|
| Architect | `architect.db` | No (Architect-only) |
| Contract Engine | `contracts.db` | Architect reads via HTTP (not direct DB) |
| Codebase Intelligence | `symbols.db` + ChromaDB | No (CI-only) |

**Mechanism 2: HTTP inter-service communication**

The Architect's `get_contracts_for_service` tool calls Contract Engine via HTTP (TECH-026). This is the ONLY cross-server data flow in Build 1:

```
Architect MCP server
  └─ get_contracts_for_service(service_name)
       └─ httpx.Client.get(f"{CONTRACT_ENGINE_URL}/api/contracts?service_name={service_name}")
            └─ Contract Engine FastAPI (separate process, port 8002)
                 └─ contracts.db
```

**Run 4 verification:** When all 3 MCP servers run simultaneously, the Contract Engine FastAPI service must ALSO be running (via Docker Compose or directly) for `get_contracts_for_service` to work. This is a hidden dependency — the MCP server alone is not sufficient.

### 5.4 Session Isolation

Each `create_*_session()` context manager creates an isolated MCP session. Key implications:

1. **Sessions cannot share tool calls.** You cannot call a Codebase Intelligence tool through a Contract Engine session.
2. **Sessions have independent lifetimes.** One session can be open while another is closed.
3. **No cross-session state.** If you register an artifact via Codebase Intelligence MCP, the Contract Engine session knows nothing about it.
4. **Build 2 manages coordination.** The Builder Fleet code in `cli.py` orchestrates calls across sessions, combining results at the Python level.

---

## 6. Testing MCP Connections

### 6.1 Integration Tests for MCP Tool Calls

Build 1 provides `test_mcp_roundtrip.py` (REQ-061, TEST-035) that tests all 3 servers end-to-end. The pattern:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_contract_engine_roundtrip():
    """Verify Contract Engine MCP responds to all tool calls."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.contract_engine.mcp_server"],
        env={"DATABASE_PATH": str(tmp_db_path)},
        cwd=str(build1_project_root)
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify tools are listed
            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert "validate_endpoint" in tool_names
            assert "get_contract" in tool_names
            assert len(tool_names) == 9  # All 9 Contract Engine tools

            # Call a tool
            result = await session.call_tool(
                "validate_spec",
                arguments={
                    "spec": {"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}},
                    "type": "openapi"
                }
            )
            assert not result.isError
            # Parse response
            for content in result.content:
                if hasattr(content, "text"):
                    data = json.loads(content.text)
                    assert "valid" in data
```

### 6.2 Mock Server Patterns for Unit Testing

Build 2 tests MCP clients without running actual servers by mocking the session:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from mcp import types as mcp_types

@pytest.fixture
def mock_session():
    """Create a mock MCP ClientSession for unit testing."""
    session = AsyncMock()

    # Mock call_tool to return valid TextContent
    def make_result(data: dict):
        result = MagicMock()
        result.isError = False
        content = MagicMock()
        content.text = json.dumps(data)
        result.content = [content]
        return result

    session.call_tool = AsyncMock(side_effect=lambda name, arguments=None: {
        "get_contract": make_result({"id": "c1", "type": "openapi", "version": "1.0.0"}),
        "validate_endpoint": make_result({"valid": True, "violations": []}),
    }.get(name, make_result({})))

    return session


async def test_contract_client_get_contract(mock_session):
    client = ContractEngineClient(mock_session)
    result = await client.get_contract("c1")
    assert result is not None
    assert result.id == "c1"
    assert result.type == "openapi"
    mock_session.call_tool.assert_called_once_with(
        "get_contract", arguments={"contract_id": "c1"}
    )
```

### 6.3 Health Check Patterns for MCP Servers

MCP stdio transport has no built-in health check. Run 4 should implement health checks at two levels:

**Level 1: MCP session health (can we connect?)**

```python
async def check_mcp_health(server_params: StdioServerParameters,
                           timeout: float = 30.0) -> dict:
    """Check if an MCP server starts and responds to initialize."""
    try:
        async with asyncio.timeout(timeout):
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return {
                        "status": "healthy",
                        "server": session._server_info.name if hasattr(session, '_server_info') else "unknown",
                        "tools_count": len(tools.tools),
                        "tool_names": [t.name for t in tools.tools]
                    }
    except TimeoutError:
        return {"status": "unhealthy", "error": "startup timeout"}
    except (OSError, ConnectionError) as e:
        return {"status": "unhealthy", "error": str(e)}
```

**Level 2: Tool-level health (do tools work?)**

```python
async def check_tool_health(session: ClientSession, tool_name: str,
                            test_args: dict) -> dict:
    """Check if a specific tool responds correctly."""
    try:
        result = await session.call_tool(tool_name, arguments=test_args)
        return {
            "tool": tool_name,
            "status": "healthy" if not result.isError else "error",
            "has_content": len(result.content) > 0
        }
    except Exception as e:
        return {"tool": tool_name, "status": "unhealthy", "error": str(e)}
```

### 6.4 Run 4 Verification Test Matrix

| Test Category | Test | Expected Result | Priority |
|---------------|------|-----------------|----------|
| **Handshake** | Architect MCP starts and initializes | Capabilities include `tools` | P0 |
| **Handshake** | Contract Engine MCP starts and initializes | Capabilities include `tools` | P0 |
| **Handshake** | Codebase Intelligence MCP starts and initializes | Capabilities include `tools` | P0 |
| **Tool Count** | Architect lists 4 tools | Exactly: decompose, get_service_map, get_contracts_for_service, get_domain_model | P0 |
| **Tool Count** | Contract Engine lists 9 tools | All 9 tool names present | P0 |
| **Tool Count** | Codebase Intelligence lists 7 tools | All 7 tool names present | P0 |
| **Roundtrip** | Call `validate_spec` with valid OpenAPI | `{"valid": true}` | P0 |
| **Roundtrip** | Call `find_definition` with known symbol | Location dict with file, line | P0 |
| **Roundtrip** | Call `search_semantic` with query | Non-empty results list | P1 |
| **Roundtrip** | Call `register_artifact` with test file | `{"indexed": true}` | P1 |
| **Error** | Call tool with wrong parameter types | `isError = True`, no crash | P0 |
| **Error** | Call non-existent tool name | Error response, no crash | P1 |
| **Timeout** | Call tool after server process killed | `OSError` raised, client recovers | P0 |
| **Fallback** | Contract Engine unavailable, static scan runs | Violations from SVC-xxx table | P1 |
| **Fallback** | Codebase Intelligence unavailable, static map generated | CODEBASE_MAP.md created | P1 |
| **Multi-server** | All 3 MCP servers running simultaneously | No resource conflicts | P0 |
| **Cross-ref** | Architect calls Contract Engine via HTTP during MCP call | Results include contract data | P1 |
| **B2 Client** | ContractEngineClient.validate_endpoint() with mock MCP | Returns ContractValidation | P0 |
| **B2 Client** | CodebaseIntelligenceClient.register_artifact() with mock MCP | Returns ArtifactResult | P0 |
| **B2 Client** | All client methods return safe defaults on MCP error | No exceptions propagated | P0 |

---

## 7. Recommendations for Run 4

### 7.1 MCP Wiring Verification Sequence

Execute in this order during Run 4 Phase 1:

1. **Start Build 1 services** (Docker Compose or direct). Verify all 3 FastAPI health endpoints return 200.
2. **Test each MCP server independently.** Spawn via `StdioServerParameters`, call `initialize()`, call `list_tools()`, verify tool counts match (4, 9, 7).
3. **Test each tool with valid input.** Call every tool at least once with known-good parameters.
4. **Test each tool with invalid input.** Verify errors are returned gracefully (not crashes).
5. **Test Build 2 client wrappers.** Verify `ContractEngineClient` and `CodebaseIntelligenceClient` correctly parse responses.
6. **Test fallback paths.** Kill MCP servers, verify Build 2 falls back to static analysis.
7. **Test simultaneous sessions.** Open all 3 MCP sessions at once, make interleaved calls.

### 7.2 Known Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| ChromaDB first-download timeout | Codebase Intelligence MCP fails to start within 30s | Set `startup_timeout_ms: 120000` for first run, or pre-download in Docker build |
| Architect's HTTP call to Contract Engine | `get_contracts_for_service` fails if FastAPI not running | Ensure Docker Compose is up before MCP testing |
| SQLite WAL mode lock contention | Concurrent reads/writes between FastAPI and MCP on same .db | WAL mode handles this (readers don't block writers), but verify with load test |
| Windows process management | Subprocess cleanup may leave orphan processes | Use `process.terminate()` + `process.kill()` with timeout in `__aexit__` |
| MCP SDK version mismatch | Build 1 server SDK vs Build 2 client SDK version drift | Pin `mcp>=1.25,<2` in both builds (already specified) |

### 7.3 Environment Variables for MCP Server Startup

Build 2's `StdioServerParameters` must pass the correct env vars to each Build 1 server:

| Server | Required Env Vars | Source in Build 2 Config |
|--------|-------------------|--------------------------|
| Architect | `DATABASE_PATH`, `CONTRACT_ENGINE_URL` | `config.contract_engine.database_path` (note: Architect uses its own DB, but needs CE URL for cross-service calls) |
| Contract Engine | `DATABASE_PATH` | `config.contract_engine.database_path` |
| Codebase Intelligence | `DATABASE_PATH`, `CHROMA_PATH`, `GRAPH_PATH` | `config.codebase_intelligence.database_path`, `.chroma_path`, `.graph_path` |

**Critical:** The `cwd` parameter in `StdioServerParameters` must be set to `config.*.server_root` (the Build 1 project root). Without this, Python module imports (`-m src.contract_engine.mcp_server`) will fail.

### 7.4 Recommended Test Fixtures

```python
# conftest.py for Run 4 MCP wiring tests
import pytest
from pathlib import Path

@pytest.fixture
def build1_root(tmp_path):
    """Create a minimal Build 1 project structure for testing."""
    # This would point to the actual Build 1 output directory
    return Path("/path/to/super-team")

@pytest.fixture
def contract_engine_params(build1_root, tmp_path):
    """StdioServerParameters for Contract Engine."""
    db_path = tmp_path / "contracts.db"
    return StdioServerParameters(
        command="python",
        args=["-m", "src.contract_engine.mcp_server"],
        env={"DATABASE_PATH": str(db_path)},
        cwd=str(build1_root)
    )

@pytest.fixture
def codebase_intel_params(build1_root, tmp_path):
    """StdioServerParameters for Codebase Intelligence."""
    return StdioServerParameters(
        command="python",
        args=["-m", "src.codebase_intelligence.mcp_server"],
        env={
            "DATABASE_PATH": str(tmp_path / "symbols.db"),
            "CHROMA_PATH": str(tmp_path / "chroma"),
            "GRAPH_PATH": str(tmp_path / "graph.json"),
        },
        cwd=str(build1_root)
    )

@pytest.fixture
def architect_params(build1_root, tmp_path):
    """StdioServerParameters for Architect."""
    return StdioServerParameters(
        command="python",
        args=["-m", "src.architect.mcp_server"],
        env={
            "DATABASE_PATH": str(tmp_path / "architect.db"),
            "CONTRACT_ENGINE_URL": "http://localhost:8002",
        },
        cwd=str(build1_root)
    )
```

### 7.5 Summary of MCP Wire Count

| Direction | From | To | Wire Count | Mechanism |
|-----------|------|-----|-----------|-----------|
| Build 2 → Build 1 | ContractEngineClient | Contract Engine MCP | 6 methods | `call_tool()` via stdio |
| Build 2 → Build 1 | CodebaseIntelligenceClient | Codebase Intelligence MCP | 7 methods | `call_tool()` via stdio |
| Build 2 → Build 1 | ArchitectClient | Architect MCP | 4 methods | `call_tool()` via stdio |
| Build 1 internal | Architect MCP | Contract Engine FastAPI | 1 HTTP call | `httpx.Client.get()` |
| **Total** | | | **18 wires** | |

Each wire must be individually tested in Run 4 Phase 1 (Wiring Verification).
