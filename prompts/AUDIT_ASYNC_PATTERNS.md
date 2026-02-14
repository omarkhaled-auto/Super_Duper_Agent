# Async Patterns Technical Audit — All 3 Build PRDs

**Reviewer:** Python Async Patterns Technical Reviewer
**Date:** 2026-02-14
**Scope:** BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md
**Focus:** asyncio, subprocess, signal handling, MCP/anyio interop, concurrency correctness

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 3 | Will cause event loop blocking or runtime failures |
| HIGH | 3 | Will cause zombie processes or missing cleanup |
| MEDIUM | 5 | Ambiguities that will lead to implementation bugs |
| LOW | 3 | Best practices, non-functional |

**Overall Assessment:** 3 CRITICAL issues must be fixed before implementation. The cross-build async integration is architecturally sound (process isolation via subprocess), but several individual PRDs contain sync-in-async blocking violations that will degrade performance or cause hangs under load.

---

## CRITICAL Issues

### CRIT-1: Build 1 REQ-020 — Sync SQLite + CPU-bound parsing in `async def` FastAPI handler

**Location:** Build 1, Milestone 2, REQ-020 (POST /api/decompose endpoint)

**Problem:** REQ-020 mandates `async def` for the decompose endpoint to support async HTTP calls to Contract Engine (REQ-064). However, the endpoint also calls:
- `prd_parser.parse_prd()` — CPU-bound regex/string processing
- `service_boundary.identify_boundaries()` — CPU-bound algorithm
- `validator.validate_decomposition()` — CPU-bound NetworkX graph analysis
- `ServiceMapStore.save()` — sync SQLite I/O via ConnectionPool
- `DomainModelStore.save()` — sync SQLite I/O via ConnectionPool

All of these are synchronous. When called inside an `async def` handler, they **block the asyncio event loop**, preventing all other concurrent requests from being served. Under load (e.g., multiple decomposition requests), the server will appear frozen.

**Why this matters:** FastAPI runs `async def` handlers directly on the event loop thread. Only `def` (sync) handlers are automatically run in a thread pool. Since REQ-020 explicitly requires `async def`, all sync calls inside it become blocking.

**Fix:** Add to REQ-020:
```
The endpoint must wrap all synchronous calls (prd_parser.parse_prd,
service_boundary.identify_boundaries, validator.validate_decomposition,
ServiceMapStore.save, DomainModelStore.save) in asyncio.to_thread()
to prevent blocking the event loop. Only the httpx.AsyncClient call
to Contract Engine should be awaited directly.

Example pattern:
    service_map = await asyncio.to_thread(identify_boundaries, entities, relationships, contexts)
    await asyncio.to_thread(store.save, service_map, prd_hash)
    async with httpx.AsyncClient() as client:
        await client.post(contract_engine_url, json=stubs)
```

Add a new TECH requirement:
```
TECH-035: Any sync function (SQLite queries, CPU-bound parsing, NetworkX
analysis) called from an async def handler MUST be wrapped in
asyncio.to_thread() to prevent event loop blocking.
```

---

### CRIT-2: Build 3 REQ-019 — Schemathesis sync calls in async function

**Location:** Build 3, Milestone 2, REQ-019 (SchemathesisRunner.run_against_service)

**Problem:** The method is declared `async` but calls:
- `schemathesis.openapi.from_url(openapi_url, base_url=base_url)` — uses `requests` internally (sync HTTP)
- `case.call(base_url=base_url)` — uses `requests` internally (sync HTTP)
- `case.validate_response(response)` — sync validation

All three schemathesis operations use the `requests` library internally, which performs blocking I/O. Calling them inside an async function blocks the event loop for the duration of every HTTP request.

**Impact:** During contract compliance verification (REQ-023 `verify_all_services` uses `asyncio.gather`), multiple services are tested "in parallel" via gather. But if each test blocks the event loop, they actually execute sequentially, defeating the purpose of async.

**Fix:** Add to REQ-019:
```
All schemathesis calls (from_url, case.call, case.validate_response)
must be wrapped in asyncio.to_thread() since schemathesis uses the
sync `requests` library internally:

    schema = await asyncio.to_thread(
        schemathesis.openapi.from_url, openapi_url, base_url=base_url
    )
    for path, methods in schema.items():
        for method, operation in methods.items():
            case = operation.make_case()
            response = await asyncio.to_thread(case.call, base_url=base_url)
            try:
                await asyncio.to_thread(case.validate_response, response)
            except CheckFailed as e:
                violations.append(...)
```

---

### CRIT-3: Build 3 REQ-021 — Pact verifier.verify() sync FFI in async function

**Location:** Build 3, Milestone 2, REQ-021 (PactManager.verify_provider)

**Problem:** The method is declared `async` but calls `verifier.verify()`, which is a synchronous call to pact-python's Rust FFI layer. This call:
1. Starts a mock provider internally
2. Replays all Pact interactions
3. Blocks until all interactions are verified or fail

This is a long-running sync operation (potentially 10-30 seconds per provider) that blocks the event loop.

**Fix:** Add to REQ-021:
```
The verifier.verify() call must be wrapped in asyncio.to_thread()
since pact-python's Verifier uses synchronous Rust FFI:

    try:
        await asyncio.to_thread(verifier.verify)
    except PactVerificationError as e:
        violations.append(...)
```

---

## HIGH Issues

### HIGH-1: Build 1 TECH-026 — Sync httpx.Client in MCP tool function must use sync `def`

**Location:** Build 1, Milestone 7, TECH-026

**Problem:** TECH-026 specifies that `get_contracts_for_service` in the Architect MCP server must use `httpx.Client` (sync) for HTTP calls to the Contract Engine. The MCP SDK's `@mcp.tool()` decorator supports both sync and async tool functions:
- `def` (sync) tools: The MCP SDK runs them in a thread pool automatically via anyio
- `async def` tools: Run directly on the event loop

If the tool is implemented as `async def` with sync `httpx.Client`, it will block the MCP server's event loop.

**Fix:** Add to TECH-026:
```
The get_contracts_for_service tool function MUST be defined as a
regular def (not async def) since it uses sync httpx.Client. The MCP
SDK will automatically run sync tool functions in a thread pool via
anyio.to_thread.run_sync(), preventing event loop blocking.

Example:
    @mcp.tool()
    def get_contracts_for_service(service_name: str) -> list[dict]:
        """..."""
        with httpx.Client(timeout=httpx.Timeout(connect=5.0, read=30.0)) as client:
            response = client.get(f"{contract_engine_url}/api/contracts", ...)
            return response.json()
```

---

### HIGH-2: Build 3 REQ-024 + REQ-046 — Missing `await proc.wait()` after `proc.kill()` on subprocess timeout

**Location:** Build 3, Milestone 2 REQ-024 (ContractFixLoop) and Milestone 5 REQ-046 (run_architect_phase)

**Problem:** Both requirements describe subprocess timeout handling where the process is killed on timeout. However, neither mentions `await proc.wait()` after `proc.kill()`. Without this:
1. The process becomes a zombie on Unix
2. File descriptors may leak
3. On Windows, the process handle is not released

**Current pattern (implied):**
```python
try:
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
except asyncio.TimeoutError:
    proc.kill()  # Process killed but not reaped
    return 0.0   # Zombie process left behind
```

**Correct pattern:**
```python
try:
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
except asyncio.TimeoutError:
    proc.kill()
    await proc.wait()  # Reap the zombie process
    return 0.0
```

**Fix:** Add to both REQ-024 and REQ-046:
```
After calling proc.kill() on timeout, MUST call await proc.wait() to
reap the child process and release system resources. Failure to do
this creates zombie processes on Unix and leaked handles on Windows.
```

Also add a general TECH requirement to Build 3:
```
TECH-031: All asyncio.create_subprocess_exec() calls that implement
timeout via asyncio.wait_for() MUST follow the pattern:
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=T)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()  # MANDATORY: reap child process
        raise/return
```

---

### HIGH-3: Build 3 REQ-053 — No subprocess cleanup on graceful shutdown during builders_running

**Location:** Build 3, Milestone 5, REQ-053 (execute_pipeline)

**Problem:** When `shutdown.should_stop` is detected between phases, the pipeline saves state and exits. But if shutdown is signaled DURING `run_parallel_builders()`, multiple builder subprocesses may be running. The current design has no mechanism to:
1. Signal running builder subprocesses to terminate
2. Wait for them to exit
3. Collect partial results

Without this, orphaned builder subprocesses continue running after the orchestrator exits, consuming resources and potentially corrupting state.

**Fix:** Add to REQ-048 (run_parallel_builders):
```
run_parallel_builders must accept a shutdown: GracefulShutdown parameter.
During the gather loop, periodically check shutdown.should_stop. If True:
1. Call proc.terminate() on all running builder subprocesses
2. Give each 10 seconds to exit gracefully (await asyncio.wait_for(proc.wait(), timeout=10))
3. Call proc.kill() + await proc.wait() on any that haven't exited
4. Collect partial BuilderResults from completed builders
5. Return results with remaining builders marked as failed with error="interrupted"
```

Add to REQ-053:
```
The shutdown check must also be performed inside run_parallel_builders,
not only between phases. Pass GracefulShutdown to run_parallel_builders
and check should_stop periodically.
```

---

## MEDIUM Issues

### MED-1: Build 2 REQ-007 — Polling interval must use asyncio.sleep, not time.sleep

**Location:** Build 2, Milestone 1, REQ-007 (AgentTeamsBackend.execute_wave)

**Problem:** REQ-007 says "poll TaskList every 30 seconds until all tasks complete or timeout" but does not specify whether to use `time.sleep(30)` or `await asyncio.sleep(30)`. Since `execute_wave` is an async method, using `time.sleep()` would block the event loop for 30 seconds on each poll iteration.

**Fix:** Add to REQ-007:
```
Polling must use await asyncio.sleep(30), NOT time.sleep(30), to
avoid blocking the event loop during the poll interval.
```

---

### MED-2: Build 3 REQ-017/REQ-018 — Docker health polling must use asyncio.sleep

**Location:** Build 3, Milestone 1, REQ-017 (DockerOrchestrator.wait_for_healthy) and REQ-018 (ServiceDiscovery.wait_all_healthy)

**Problem:** REQ-017 says "polling docker compose ps every 5s" and REQ-018 says "polling all services every 3s" but neither specifies `asyncio.sleep` vs `time.sleep`. Both methods are async.

**Fix:** Add to REQ-017 and REQ-018:
```
Polling intervals must use await asyncio.sleep(N), NOT time.sleep(N).
```

---

### MED-3: Build 1 — ChromaDB sync operations in async context

**Location:** Build 1, Milestone 6, REQ-052 (SemanticIndexer), REQ-053 (SemanticSearcher), REQ-054 (ChromaStore)

**Problem:** ChromaDB's `collection.add()`, `collection.query()`, and `collection.delete()` are synchronous operations that involve:
- Computing embeddings (CPU-intensive, ~50ms per chunk with MiniLM)
- Writing to persistent storage (disk I/O)

If these are called from async FastAPI endpoints (REQ-058) or async MCP tool functions (REQ-057), they will block the event loop.

**Fix:** Add to TECH requirements:
```
TECH-036: ChromaDB operations (collection.add, collection.query,
collection.delete) are synchronous. When called from async contexts
(FastAPI async endpoints or async MCP tool functions), they MUST be
wrapped in asyncio.to_thread() or the calling function must be
defined as sync def (for MCP tools, the SDK handles threading).

Recommended approach for MCP tools: Define ChromaDB-using tool
functions as regular def (not async def). The MCP SDK runs sync tools
in a thread pool automatically.

Recommended approach for FastAPI endpoints: Use asyncio.to_thread():
    results = await asyncio.to_thread(searcher.search, query, n_results=10)
```

---

### MED-4: Build 3 REQ-048 — Semaphore + gather pattern should be explicit

**Location:** Build 3, Milestone 5, REQ-048 (run_parallel_builders)

**Problem:** REQ-048 says "launches multiple Builder subprocesses bounded by asyncio.Semaphore(max_concurrent)" but doesn't show the pattern. The correct pattern must:
1. Create a semaphore
2. Wrap each builder launch in `async with sem:`
3. Use `asyncio.gather(*tasks, return_exceptions=True)` for parallel execution

An incorrect implementation (e.g., acquiring semaphore globally instead of per-builder, or not using gather) would serialize builders or fail to limit concurrency.

**Fix:** Add to REQ-048:
```
The semaphore pattern must be:

    sem = asyncio.Semaphore(max_concurrent)

    async def run_one_builder(builder_config: dict) -> BuilderResult:
        async with sem:  # Limits concurrent builders
            proc = await asyncio.create_subprocess_exec(
                "python", "-m", "agent_team",
                "--cwd", str(builder_config["output_dir"]),
                "--depth", config.builder.depth,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=config.builder.timeout_per_builder
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return BuilderResult(service_id=..., success=False, error="timeout")
            # Parse result from STATE.json
            return BuilderResult(...)

    results = await asyncio.gather(
        *[run_one_builder(c) for c in builder_configs],
        return_exceptions=True,
    )
    # Convert exceptions to failed BuilderResults
```

---

### MED-5: Build 3 REQ-013 — Signal handler _emergency_save reentrancy risk

**Location:** Build 3, Milestone 1, REQ-013 (GracefulShutdown._handle_signal)

**Problem:** The signal handler calls `_emergency_save()` which calls `PipelineState.save()` which calls `atomic_write_json()`. If the signal arrives while the main event loop is already inside `atomic_write_json()` (from a normal state save after a phase transition), both writes target the same directory. While `atomic_write_json` uses tmp+rename (so the rename itself is atomic), having two concurrent writes to different .tmp files with renames can produce a state file from either the signal handler or the main loop, potentially losing the more recent state.

**Mitigation (already in PRD):** atomic_write_json uses tmp+rename, so corruption is unlikely.

**Fix:** Add note to REQ-013:
```
_emergency_save() should use a threading.Lock (or a simple boolean
guard) to prevent reentrancy. If a save is already in progress,
the signal handler should only set _should_stop = True and skip the
save — the main loop will save state when it next checks should_stop.

    def _handle_signal(self, signum, frame):
        self._should_stop = True
        if not self._saving:  # Simple guard
            self._saving = True
            try:
                self._emergency_save()
            finally:
                self._saving = False
```

---

## LOW Issues

### LOW-1: Build 1/2/3 — Document anyio + asyncio compatibility assumption

**Location:** All 3 PRDs

**Problem:** The MCP SDK uses anyio internally, while all application code uses asyncio directly. This works because anyio is designed to run on asyncio as a backend. However, this assumption is not documented anywhere in the PRDs.

**Fix:** Add a note to each PRD's Technology Stack section:
```
NOTE: The MCP Python SDK uses anyio internally. anyio is compatible
with asyncio as a backend — when an asyncio event loop is already
running, anyio operations execute on it transparently. No special
configuration is needed.
```

---

### LOW-2: Build 3 — Document single asyncio.run() entry point

**Location:** Build 3, TECH-027

**Problem:** TECH-027 correctly states "must call asyncio.run() exactly once." This is important but could be more explicit about WHERE the single call happens.

**Fix:** Expand TECH-027:
```
TECH-027: asyncio.run() must be called exactly once, in the CLI
command handler (e.g., typer command function). All other async code
must use await. Pattern:

    @app.command()
    def run(prd_path: Path, resume: bool = False):
        asyncio.run(_async_run(prd_path, resume))

    async def _async_run(prd_path: Path, resume: bool):
        await execute_pipeline(...)

Never call asyncio.run() from within an async function, from a
signal handler, or from a subprocess callback.
```

---

### LOW-3: Build 2 TECH-010 — _verify_claude_available uses sync subprocess from sync context

**Location:** Build 2, Milestone 1, TECH-010

**Problem:** Uses `subprocess.run()` (sync) which is correct since `create_execution_backend()` is a sync factory function. However, if a future refactor makes the factory async, this would need to change.

**Status:** CORRECT as specified. No fix needed, just a note for awareness.

---

## Cross-Build Async Integration Verification

### Build 3 -> Build 1 MCP (Architect, Contract Engine) via stdio

**Pattern:** Build 3 spawns Build 1 MCP servers as subprocesses via `asyncio.create_subprocess_exec()`, communicates via stdio pipes using MCP SDK's `stdio_client()` + `ClientSession`.

**Event Loop Isolation:** GUARANTEED. Each subprocess has its own Python process with its own event loop. The MCP SDK in Build 3 (client side) uses anyio which runs on Build 3's asyncio loop. The MCP SDK in Build 1 (server side) starts its own anyio/asyncio loop in the subprocess.

**VERDICT:** CORRECT. No cross-process event loop conflicts possible.

---

### Build 3 -> Build 2 (Builder subprocesses)

**Pattern:** Build 3 spawns `python -m agent_team` subprocesses via `asyncio.create_subprocess_exec()`. Each builder runs its own `asyncio.run()` in its `main()` function.

**Event Loop Isolation:** GUARANTEED. Each builder subprocess is a separate process.

**Communication:** Via stdout/stderr pipes and STATE.json file.

**VERDICT:** CORRECT. No conflicts.

---

### Build 2 -> Build 1 MCP (Contract Engine, Codebase Intelligence)

**Pattern:** Build 2's MCP clients (`ContractEngineClient`, `CodebaseIntelligenceClient`) use `stdio_client()` + `ClientSession` to communicate with Build 1 MCP servers.

**Event Loop Context:** Build 2 runs within agent-team's `asyncio.run()` event loop. MCP client calls are `await`ed within async functions.

**anyio Compatibility:** The MCP SDK uses anyio internally. When called from an asyncio event loop, anyio detects it and uses asyncio as its backend. No conflict.

**VERDICT:** CORRECT. anyio + asyncio interop is well-supported.

---

### Nested asyncio.run() Risk Assessment

| Location | Risk | Status |
|----------|------|--------|
| Build 3 CLI `asyncio.run()` | Single entry point | CORRECT (TECH-027) |
| Build 2 agent-team `asyncio.run()` in `main()` | Runs in subprocess (isolated) | CORRECT |
| Build 1 MCP `mcp.run()` (uses anyio.run internally) | Runs in subprocess (isolated) | CORRECT |
| Build 2 `_run_review_only()` nested asyncio.run | Known CRITICAL bug, already fixed | FIXED |

**VERDICT:** No nested asyncio.run() issues. All entry points are in separate processes.

---

## Checklist Summary

| Pattern | Build 1 | Build 2 | Build 3 |
|---------|---------|---------|---------|
| asyncio.run() called once | N/A (FastAPI/MCP) | CORRECT | CORRECT (TECH-027) |
| asyncio.create_subprocess_exec() | N/A | N/A | CORRECT |
| subprocess.PIPE handling | N/A | CORRECT | CORRECT |
| asyncio.gather(return_exceptions=True) | N/A | CORRECT (TECH-011) | CORRECT (REQ-023) |
| asyncio.Semaphore for concurrency | N/A | N/A | NEEDS DETAIL (MED-4) |
| asyncio.sleep for polling | N/A | NEEDS FIX (MED-1) | NEEDS FIX (MED-2) |
| asyncio.wait_for + proc.kill + proc.wait | N/A | N/A | MISSING proc.wait (HIGH-2) |
| asyncio.to_thread for blocking calls | MISSING (CRIT-1) | N/A | MISSING (CRIT-2, CRIT-3) |
| Signal handling (Windows + Unix) | N/A | N/A | CORRECT (TECH-006) |
| MCP anyio compatibility | CORRECT | CORRECT | CORRECT |
| Event loop isolation (subprocesses) | CORRECT | CORRECT | CORRECT |
| FastAPI async/sync handler choice | NEEDS FIX (CRIT-1) | N/A | N/A |
| Graceful shutdown subprocess cleanup | N/A | N/A | MISSING (HIGH-3) |

---

## Recommended Fixes (Ordered by Priority)

1. **CRIT-1:** Build 1 REQ-020 — Add `asyncio.to_thread()` wrapping for all sync calls in async decompose endpoint
2. **CRIT-2:** Build 3 REQ-019 — Add `asyncio.to_thread()` wrapping for schemathesis sync calls
3. **CRIT-3:** Build 3 REQ-021 — Add `asyncio.to_thread()` wrapping for pact verifier.verify()
4. **HIGH-1:** Build 1 TECH-026 — Specify MCP tool must be `def` (not `async def`) when using sync httpx
5. **HIGH-2:** Build 3 REQ-024/REQ-046 — Add `await proc.wait()` after `proc.kill()` on timeout
6. **HIGH-3:** Build 3 REQ-048/REQ-053 — Add subprocess cleanup on graceful shutdown
7. **MED-1:** Build 2 REQ-007 — Specify `await asyncio.sleep(30)` for polling
8. **MED-2:** Build 3 REQ-017/REQ-018 — Specify `await asyncio.sleep()` for polling
9. **MED-3:** Build 1 — Clarify sync/async boundary for ChromaDB operations
10. **MED-4:** Build 3 REQ-048 — Add explicit semaphore + gather pattern
11. **MED-5:** Build 3 REQ-013 — Add reentrancy guard on signal handler save
