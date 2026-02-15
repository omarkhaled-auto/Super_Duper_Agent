# Run 4 Cross-Build Interface Matrix

> **Purpose**: Exhaustive catalog of EVERY integration point between Builds 1-3 that Run 4 must wire and verify.
> **Sources**: BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md, BUILD3_ARCHITECTURE_PLAN.md, RUN4_TECH_MCP_WIRING.md, RUN4_TECH_DOCKER_ORCHESTRATION.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md

---

## Table of Contents

1. [MCP Tool Signatures (Build 1 Servers)](#1-mcp-tool-signatures-build-1-servers)
2. [MCP Client Method Signatures (Build 2)](#2-mcp-client-method-signatures-build-2)
3. [MCP Client Method Signatures (Build 3)](#3-mcp-client-method-signatures-build-3)
4. [Subprocess Invocations (Build 3 to Build 2)](#4-subprocess-invocations-build-3-to-build-2)
5. [HTTP Inter-Service Communication (Build 1 Internal)](#5-http-inter-service-communication-build-1-internal)
6. [Docker Service Definitions](#6-docker-service-definitions)
7. [State Persistence JSON Schemas](#7-state-persistence-json-schemas)
8. [Config Cross-References](#8-config-cross-references)
9. [Integration Matrix Summary](#9-integration-matrix-summary)

---

## 1. MCP Tool Signatures (Build 1 Servers)

### 1.1 Architect MCP Server (4 tools)

**Server**: `src/architect/mcp_server.py`
**Name**: "Architect"
**Transport**: stdio (`python -m src.architect.mcp_server`)
**Database**: `architect.db` (SQLite, WAL mode)
**Build 2 consumers**: `ArchitectClient` (in `mcp_clients.py`, per INT-003)
**Build 3 consumers**: `run_architect_phase()` (in `pipeline.py`, per REQ-046)

| Tool | Parameters | Return Schema | Error Cases | Verification Test |
|------|-----------|---------------|-------------|-------------------|
| `decompose` | `prd_text: str` (min 10 chars, max 1MB) | `{ "service_map": ServiceMap, "domain_model": DomainModel, "contract_stubs": list[dict], "validation_issues": list[str], "interview_questions": list[str] }` | 422 if validation fails; ParsingError if PRD unparseable; 413 if > 1MB | Tool call returns well-formed DecompositionResult dict |
| `get_service_map` | (none) | `{ "project_name": str, "services": list[ServiceDefinition], "generated_at": str, "prd_hash": str, "build_cycle_id": str\|null }` | Returns `None` / empty dict if no service map exists | Non-null response after decompose() |
| `get_contracts_for_service` | `service_name: str` | `list[{ "id": str, "role": "provider"\|"consumer", "type": str, "counterparty": str, "summary": str }]` | Empty list if service not found; HTTP timeout to Contract Engine (30s) | Returns contracts for known service |
| `get_domain_model` | (none) | `{ "entities": list[DomainEntity], "relationships": list[DomainRelationship], "generated_at": str }` | Returns `None` / empty dict if no domain model exists | Non-null response after decompose() |

**Implementation notes**:
- `get_contracts_for_service` internally calls Contract Engine via `httpx.Client` (sync) at `CONTRACT_ENGINE_URL` (default `http://contract-engine:8000`). Uses `httpx.Timeout(connect=5.0, read=30.0)`. Defined as sync `def` (MCP SDK runs in thread pool via `anyio.to_thread.run_sync()`).
- Each MCP server creates its OWN `ConnectionPool` instance. Does NOT share state with FastAPI app.
- Ref: BUILD1_PRD REQ-059, TECH-026

### 1.2 Contract Engine MCP Server (9 tools)

**Server**: `src/contract_engine/mcp_server.py`
**Name**: "Contract Engine"
**Transport**: stdio (`python -m src.contract_engine.mcp_server`)
**Database**: `contracts.db` (SQLite, WAL mode)
**Build 2 consumers**: `ContractEngineClient` (in `contract_client.py`)
**Build 3 consumers**: `run_contract_registration()` (in `pipeline.py`), `ContractComplianceVerifier` (in `contract_compliance.py`)

| Tool | Parameters | Return Schema | Error Cases | Verification Test |
|------|-----------|---------------|-------------|-------------------|
| `create_contract` | `service_name: str, type: str, version: str, spec: dict, build_cycle_id: str = ""` | `{ "id": str, "status": str, "spec_hash": str }` | ImmutabilityViolationError (409) if same build_cycle_id exists; ValidationError (422) if spec invalid | Create + retrieve roundtrip |
| `validate_spec` | `spec: dict, type: str` | `{ "valid": bool, "errors": list[str], "warnings": list[str] }` | type must be "openapi"\|"asyncapi"\|"json_schema" | Valid spec returns `valid: true` |
| `list_contracts` | `service_name: str = "", type: str = "", page: int = 1, page_size: int = 50` | `{ "items": list[ContractEntry], "total": int, "page": int, "page_size": int }` | Empty list if no matches | Paginated results after create |
| `get_contract` | `contract_id: str` | `ContractEntry dict` or `None` | Returns None if not found | Retrieve by ID after create |
| `validate_endpoint` | `service_name: str, method: str, path: str, response_body: dict, status_code: int = 200` | `{ "valid": bool, "violations": list[{ "field": str, "expected": str, "actual": str, "severity": str }] }` | Returns `valid: false` with violations on schema mismatch | Detect deliberate field mismatch |
| `generate_tests` | `contract_id: str, framework: str = "pytest", include_negative: bool = True` | `str` (complete test file content) | Empty string if contract not found | Generated code compiles (`ast.parse()`) |
| `check_breaking_changes` | `contract_id: str, new_spec: dict` | `list[{ "change_type": str, "path": str, "old_value": str\|null, "new_value": str\|null, "severity": str, "affected_consumers": list[str] }]` | Empty list if no changes | Detect removed field as breaking |
| `mark_implemented` | `contract_id: str, service_name: str, evidence_path: str` | `{ "marked": bool, "total_implementations": int, "all_implemented": bool }` | `marked: false` on failure | Mark + verify via get_unimplemented |
| `get_unimplemented_contracts` | `service_name: str = ""` | `list[{ "id": str, "type": str, "version": str, "expected_service": str, "status": str }]` | Empty list if all implemented | Returns gap list before mark |

**Implementation notes**:
- `spec_hash` computed via `hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()` (TECH-009)
- Immutability enforced per build_cycle_id (TECH-010)
- Test suites cached in `test_suites` table by `spec_hash`
- Ref: BUILD1_PRD REQ-060, Milestones 3-4

### 1.3 Codebase Intelligence MCP Server (7 tools)

**Server**: `src/codebase_intelligence/mcp_server.py`
**Name**: "Codebase Intelligence"
**Transport**: stdio (`python -m src.codebase_intelligence.mcp_server`)
**Database**: `symbols.db` (SQLite, WAL mode) + ChromaDB (PersistentClient at `CHROMA_PATH`) + NetworkX graph (at `GRAPH_PATH`)
**Build 2 consumers**: `CodebaseIntelligenceClient` (in `codebase_client.py`)
**Build 3 consumers**: None directly (Build 3 accesses via Build 2 clients or subprocess)

| Tool | Parameters | Return Schema | Error Cases | Verification Test |
|------|-----------|---------------|-------------|-------------------|
| `find_definition` | `symbol: str, language: str\|None = None` | `{ "file_path": str, "line_start": int, "line_end": int, "kind": str, "signature": str\|null, "docstring": str\|null }` or `None` | Returns None if symbol not found | Find known symbol after indexing |
| `find_callers` | `symbol: str, max_results: int = 50` | `list[{ "file_path": str, "line": int, "caller_name": str }]` | Empty list if no callers | Find callers of known function |
| `find_dependencies` | `file_path: str` | `{ "imports": list[str], "imported_by": list[str], "transitive_deps": list[str], "circular_deps": list[list[str]] }` | Empty lists if file not indexed | Correct import graph after indexing |
| `search_semantic` | `query: str, language: str\|None = None, service_name: str\|None = None, n_results: int = 10` | `list[{ "chunk_id": str, "file_path": str, "symbol_name": str\|null, "content": str, "score": float, "language": str, "service_name": str\|null, "line_start": int, "line_end": int }]` | Empty list if no matches | Relevant results for "payment processing" |
| `get_service_interface` | `service_name: str` | `{ "service_name": str, "endpoints": list[dict], "events_published": list[dict], "events_consumed": list[dict], "exported_symbols": list[SymbolDefinition] }` | Empty dict if service not found | Returns endpoints for known service |
| `check_dead_code` | `service_name: str\|None = None` | `list[{ "symbol_name": str, "file_path": str, "kind": str, "line": int, "service_name": str\|null, "confidence": str }]` | Empty list if no dead code | Finds planted dead function |
| `register_artifact` | `file_path: str, service_name: str` | `{ "indexed": bool, "symbols_found": int, "dependencies_found": int, "errors": list[str] }` | `indexed: false` if file unparseable | Index file + verify via find_definition |

**Implementation notes**:
- ChromaDB downloads ~80MB embedding model on first use (TECH-023). First startup may take 120s+.
- ChromaDB collection uses `DefaultEmbeddingFunction()` with cosine space (TECH-021/022)
- `register_artifact` triggers full `IncrementalIndexer.index_file()` pipeline: parse -> extract -> resolve -> graph -> persist -> embed
- Must process files within 5 seconds (INT-005 from Build 2)
- Ref: BUILD1_PRD REQ-057, Milestone 6

---

## 2. MCP Client Method Signatures (Build 2)

### 2.1 ContractEngineClient (`contract_client.py`)

**Session factory**: `create_contract_engine_session()` in `mcp_client.py`
**Config**: `ContractEngineConfig` in `config.py`
**Error handling**: 3 retries with exponential backoff (1s, 2s, 4s) on transient errors; immediate safe default on non-transient
**Safe defaults**: Never raises to caller

| Client Method | MCP Tool Called | Request | Response Dataclass | Safe Default |
|--------------|----------------|---------|-------------------|--------------|
| `get_contract(contract_id)` | `get_contract` | `{ contract_id: str }` | `ContractInfo \| None` | `None` |
| `validate_endpoint(service_name, method, path, response_body, status_code=200)` | `validate_endpoint` | `{ service_name, method, path, response_body, status_code }` | `ContractValidation(valid, violations, error)` | `ContractValidation(error="...")` |
| `generate_tests(contract_id, framework="pytest", include_negative=True)` | `generate_tests` | `{ contract_id, framework, include_negative }` | `str` | `""` |
| `check_breaking_changes(contract_id, new_spec)` | `check_breaking_changes` | `{ contract_id, new_spec }` | `list[dict]` | `[]` |
| `mark_implemented(contract_id, service_name, evidence_path)` | `mark_implemented` | `{ contract_id, service_name, evidence_path }` | `dict` | `{"marked": False}` |
| `get_unimplemented_contracts(service_name=None)` | `get_unimplemented_contracts` | `{ service_name }` | `list[dict]` | `[]` |

**Helper methods**:
- `_extract_json(result) -> Any`: Iterates `result.content`, finds `TextContent`, parses JSON
- `_extract_text(result) -> str`: Iterates `result.content`, returns first text

**Session creation** (`create_contract_engine_session()`):
```python
StdioServerParameters(
    command=config.contract_engine.mcp_command,  # "python"
    args=config.contract_engine.mcp_args,  # ["-m", "src.contract_engine.mcp_server"]
    env={"DATABASE_PATH": config.contract_engine.database_path},
    cwd=config.contract_engine.server_root  # Build 1 project root
)
```

### 2.2 CodebaseIntelligenceClient (`codebase_client.py`)

**Session factory**: `create_codebase_intelligence_session()` in `mcp_client.py`
**Config**: `CodebaseIntelligenceConfig` in `config.py`
**Error handling**: Same 3-retry pattern as ContractEngineClient

| Client Method | MCP Tool Called | Request | Response Dataclass | Safe Default |
|--------------|----------------|---------|-------------------|--------------|
| `find_definition(symbol, language=None)` | `find_definition` | `{ symbol, language }` | `DefinitionResult(file, line, kind, signature, found)` | `DefinitionResult()` |
| `find_callers(symbol, max_results=50)` | `find_callers` | `{ symbol, max_results }` | `list[dict]` | `[]` |
| `find_dependencies(file_path)` | `find_dependencies` | `{ file_path }` | `DependencyResult(imports, imported_by, transitive_deps, circular_deps)` | `DependencyResult()` |
| `search_semantic(query, language=None, service_name=None, n_results=10)` | `search_semantic` | `{ query, language, service_name, n_results }` | `list[dict]` | `[]` |
| `get_service_interface(service_name)` | `get_service_interface` | `{ service_name }` | `dict` | `{}` |
| `check_dead_code(service_name=None)` | `check_dead_code` | `{ service_name }` | `list[dict]` | `[]` |
| `register_artifact(file_path, service_name)` | `register_artifact` | `{ file_path, service_name }` | `ArtifactResult(indexed, symbols_found, dependencies_found)` | `ArtifactResult()` |

**Session creation** (`create_codebase_intelligence_session()`):
```python
StdioServerParameters(
    command=config.codebase_intelligence.mcp_command,  # "python"
    args=config.codebase_intelligence.mcp_args,  # ["-m", "src.codebase_intelligence.mcp_server"]
    env={
        "DATABASE_PATH": config.codebase_intelligence.database_path,
        "CHROMA_PATH": config.codebase_intelligence.chroma_path,
        "GRAPH_PATH": config.codebase_intelligence.graph_path,
    },
    cwd=config.codebase_intelligence.server_root
)
```

### 2.3 ArchitectClient (Build 2 INT-003)

**Location**: `mcp_clients.py` (created per INT-003)
**Pattern**: Same as ContractEngineClient/CodebaseIntelligenceClient
**Fallback**: Standard PRD decomposition without live queries

| Client Method | MCP Tool Called | Safe Default |
|--------------|----------------|--------------|
| `decompose(prd_text)` | `decompose` | `None` (fallback to standard decomposition) |
| `get_service_map()` | `get_service_map` | `None` |
| `get_contracts_for_service(service_name)` | `get_contracts_for_service` | `[]` |
| `get_domain_model()` | `get_domain_model` | `None` |

### 2.4 Build 2 MCP Server Configuration (`mcp_servers.py`)

| Function | Returns | Gating |
|----------|---------|--------|
| `_contract_engine_mcp_server(config)` | `{"type": "stdio", "command": ..., "args": ..., "env": {"DATABASE_PATH": ...}}` | `config.contract_engine.enabled` |
| `_codebase_intelligence_mcp_server(config)` | `{"type": "stdio", "command": ..., "args": ..., "env": {DATABASE_PATH, CHROMA_PATH, GRAPH_PATH}}` | `config.codebase_intelligence.enabled` |
| `get_contract_aware_servers(config)` | All standard servers + Build 1 MCP servers | Either enabled |

---

## 3. MCP Client Method Signatures (Build 3)

### 3.1 Architect MCP Usage in Pipeline (`pipeline.py`)

Build 3's `run_architect_phase()` calls Build 1's Architect MCP directly:

```python
# Primary path: MCP stdio
async with stdio_client(StdioServerParameters(
    command="python",
    args=["-m", "src.architect.mcp_server"],
    cwd=config.build1_services_dir
)) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("decompose", {"prd_text": prd_content})
```

**Fallback**: Subprocess + JSON if MCP SDK import fails (lazy import with ImportError)

### 3.2 Contract Engine MCP Usage in Pipeline

Build 3's `run_contract_registration()` calls Contract Engine MCP:

| Tool Called | Purpose | Phase |
|------------|---------|-------|
| `create_contract` | Register contract stubs from Architect output | contracts_registering |
| `validate_spec` | Validate all contracts are structurally correct | contracts_registering |
| `list_contracts` | Verify contracts were stored | contracts_registering |

---

## 4. Subprocess Invocations (Build 3 to Build 2)

### 4.1 Builder Invocation

**Source**: `run_parallel_builders()` in `pipeline.py` (REQ-048)
**Target**: Build 2's `agent_team` CLI

| Aspect | Value |
|--------|-------|
| **Command** | `python -m agent_team --cwd {builder_dir} --depth {config.builder.depth}` |
| **Working directory** | Each builder gets its own isolated directory (`output_dir`) |
| **Subprocess creation** | `asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", str(builder_dir), "--depth", config.builder.depth, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)` |
| **Concurrency** | Bounded by `asyncio.Semaphore(max_concurrent)` (default 3, created INSIDE function body) |
| **Timeout** | `config.builder.timeout_per_builder` (default 1800s = 30 min) |
| **Config passing** | Write `config.yaml` to `{builder_dir}/config.yaml` via `yaml.safe_dump()` |
| **Result parsing** | Read `{builder_dir}/.agent-team/STATE.json` |
| **Cleanup** | `proc.kill()` + `await proc.wait()` in `finally` block |
| **Environment** | Builders inherit parent environment (SEC-001: no ANTHROPIC_API_KEY passed explicitly) |

**Generated builder config** (from `generate_builder_config()`):
```yaml
depth: "thorough"  # from global_config.builder.depth
milestone:
  enabled: true
  health_gate: true
e2e_testing:
  enabled: true
  backend_api_tests: true
post_orchestration_scans:
  mock_data_scan: true
  api_contract_scan: true
```

### 4.2 BuilderResult Parsing from STATE.json

Build 3 reads Build 2's STATE.json and maps fields to `BuilderResult`:

| BuilderResult Field | STATE.json Path | Type |
|--------------------|----------------|------|
| `success` | `summary.success` | `bool` |
| `cost` | `total_cost` | `float` |
| `test_passed` | `summary.test_passed` | `int` |
| `test_total` | `summary.test_total` | `int` |
| `convergence_ratio` | `summary.convergence_ratio` | `float` |

**Prerequisite**: Build 2's `RunState.to_dict()` must include a top-level `summary` dict with these computed fields (TECH-031 from Build 2).

### 4.3 Fix Pass Invocations

**Source**: `ContractFixLoop.feed_violations_to_builder()` in `fix_loop.py` (REQ-024)
**Target**: Build 2's `agent_team` CLI in quick mode

| Aspect | Value |
|--------|-------|
| **Command** | `python -m agent_team --cwd {builder_dir} --depth quick` |
| **Input** | `FIX_INSTRUCTIONS.md` written to `{builder_dir}/` with categorized violations |
| **Result** | Cost extracted from `{builder_dir}/.agent-team/STATE.json` → `total_cost` field |
| **Timeout** | `config.builder.timeout_per_builder` |
| **Cleanup** | `proc.kill()` + `await proc.wait()` on timeout |

### 4.4 Agent Teams Backend (Optional)

When `config.agent_teams.enabled` is True and Build 2's `AgentTeamsBackend` is active:

| Aspect | Value |
|--------|-------|
| **Backend selection** | `create_execution_backend(config)` factory function |
| **Wave execution** | `AgentTeamsBackend.execute_wave()` uses Claude Code TaskCreate/TaskUpdate |
| **Fallback** | `CLIBackend` wraps existing subprocess logic |
| **Polling** | TaskList polled every 30s via `await asyncio.sleep(30)` |
| **Shutdown** | `shutdown_request` sent to all active teammates |

---

## 5. HTTP Inter-Service Communication (Build 1 Internal)

### 5.1 Architect to Contract Engine

| Source | Target | Method | Path | Purpose |
|--------|--------|--------|------|---------|
| `src/architect/routers/decomposition.py` | Contract Engine | POST | `/api/contracts` | Register generated contract stubs |
| `src/architect/mcp_server.py` (`get_contracts_for_service`) | Contract Engine | GET | `/api/contracts?service_name={name}` | Fetch contracts for a service |

**Client**: `httpx.AsyncClient` (decomposition router) / `httpx.Client` (MCP tool, sync)
**URL**: `CONTRACT_ENGINE_URL` env var (default `http://contract-engine:8000`)
**Timeout**: `httpx.Timeout(connect=5.0, read=30.0)`

### 5.2 Build 1 REST API Endpoints (used by Build 3 integration tests)

**Architect** (port 8001 external, 8000 internal):

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/decompose` | `DecomposeRequest { prd_text: str }` | `DecompositionResult` (201) |
| GET | `/api/service-map` | None | `ServiceMap` (200) or 404 |
| GET | `/api/domain-model` | None | `DomainModel` (200) or 404 |
| GET | `/api/health` | None | `HealthStatus` (200) |

**Contract Engine** (port 8002 external, 8000 internal):

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/contracts` | `ContractCreate` | `ContractEntry` (201) |
| GET | `/api/contracts` | QueryParams | `ContractListResponse` (200) |
| GET | `/api/contracts/{id}` | PathParam | `ContractEntry` (200/404) |
| DELETE | `/api/contracts/{id}` | PathParam | None (204/404) |
| POST | `/api/validate` | `ValidateRequest` | `ValidationResult` |
| POST | `/api/breaking-changes/{id}` | `{ new_spec: dict }` | `list[BreakingChange]` |
| POST | `/api/implementations/mark` | `MarkRequest` | `MarkResponse` |
| GET | `/api/implementations/unimplemented` | QueryParam | `list[UnimplementedContract]` |
| POST | `/api/tests/generate/{id}` | `{ framework, include_negative }` | `ContractTestSuite` |
| GET | `/api/tests/{id}` | None | `ContractTestSuite` |
| GET | `/api/health` | None | `HealthStatus` (200) |

**Codebase Intelligence** (port 8003 external, 8000 internal):

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/symbols` | QueryParams (name, language) | Symbol list |
| GET | `/api/dependencies` | QueryParam (file_path) | Dependency info |
| POST | `/api/search` | `{ query, language, service_name, n_results }` | Semantic results |
| POST | `/api/artifacts` | `{ file_path, service_name }` | Index stats |
| GET | `/api/dead-code` | QueryParam (service_name) | Dead code list |
| GET | `/api/health` | None | `HealthStatus` (200) |

---

## 6. Docker Service Definitions

### 6.1 Build 1 Services

| Service | Image / Build Context | Ports | Health Check | Volumes | Networks | Depends On |
|---------|----------------------|-------|-------------|---------|----------|------------|
| `architect` | `docker/architect/Dockerfile` | 8001:8000 | `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"` interval=10s timeout=5s retries=5 start_period=15s | `architect-data:/data` | `super-team-net` | `contract-engine` (service_healthy) |
| `contract-engine` | `docker/contract_engine/Dockerfile` | 8002:8000 | Same pattern, start_period=10s | `contract-data:/data` | `super-team-net` | None |
| `codebase-intel` | `docker/codebase_intelligence/Dockerfile` | 8003:8000 | Same pattern, start_period=20s | `intel-data:/data`, ChromaDB data | `super-team-net` | `contract-engine` (service_healthy) |

**Dockerfile pattern** (all 3):
- Base: `python:3.12-slim`
- WORKDIR: `/app`
- COPY `src/shared/` (WIRE-023: shared package must be in all containers)
- Non-root user: `appuser`
- EXPOSE 8000
- CMD: `["uvicorn", "src.{service}.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- Codebase Intelligence additionally pre-downloads ChromaDB model: `RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; DefaultEmbeddingFunction()"`

**Environment variables**:

| Service | Env Var | Default | Description |
|---------|---------|---------|-------------|
| All | `DATABASE_PATH` | `./data/service.db` | SQLite database path |
| All | `LOG_LEVEL` | `info` | Log verbosity |
| Architect | `CONTRACT_ENGINE_URL` | `http://contract-engine:8000` | Contract Engine internal URL |
| Architect | `CODEBASE_INTEL_URL` | `http://codebase-intel:8000` | Codebase Intelligence internal URL |
| Codebase Intel | `CHROMA_PATH` | `./data/chroma` | ChromaDB persistence path |
| Codebase Intel | `GRAPH_PATH` | `./data/graph.json` | NetworkX graph path |
| Codebase Intel | `CONTRACT_ENGINE_URL` | (same) | For cross-service queries |

### 6.2 Build 3 Infrastructure Services

| Service | Image | Ports | Health Check | Volumes | Networks |
|---------|-------|-------|-------------|---------|----------|
| `traefik` | `traefik:v3.6` | 80, 8080 | `traefik healthcheck --ping` (requires `--ping=true` in command) | `/var/run/docker.sock:/var/run/docker.sock:ro` (SEC-004) | `frontend` |
| `postgres` | `postgres:16-alpine` | 5432 | `pg_isready` | `postgres-data:/var/lib/postgresql/data` | `backend` |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ping` | `redis-data:/data` | `backend` |

**Traefik configuration**:
- Docker provider: `exposedByDefault: false`
- Entrypoint: `web` on `:80`
- Dashboard disabled by default (`--api.dashboard=false`, SEC-003)
- Generated service labels: `traefik.enable=true`, `traefik.http.routers.{svc}.rule=PathPrefix(...)`, strip prefix middleware

### 6.3 Build 2 Generated Services

Build 2 Builders produce service directories with Dockerfiles. Build 3's `ComposeGenerator` creates entries for each:

| Aspect | Value |
|--------|-------|
| Build context | `{builder_result.output_dir}` |
| Health check | Service-specific `/health` endpoint |
| Traefik labels | Generated by `TraefikConfigGenerator.generate_labels(service_name, port, path_prefix)` |
| depends_on | `postgres` (service_healthy) |
| Networks | `frontend` + `backend` |

### 6.4 Network Topology

```
frontend network: traefik, architect, contract-engine, codebase-intel, generated-services
backend network:  postgres, redis, architect, contract-engine, codebase-intel, generated-services
```

**Key rule**: Traefik is ONLY on frontend. Postgres/Redis are ONLY on backend. Application services span both.

### 6.5 Named Volumes

| Volume | Service(s) | Mount Point |
|--------|-----------|-------------|
| `architect-data` | architect | `/data` |
| `contract-data` | contract-engine | `/data` |
| `intel-data` | codebase-intel | `/data` |
| `postgres-data` | postgres | `/var/lib/postgresql/data` |
| `redis-data` | redis | `/data` |

---

## 7. State Persistence JSON Schemas

### 7.1 Build 2: RunState (STATE.json)

**Path**: `{project_dir}/.agent-team/STATE.json`
**Writer**: `RunState.to_dict()` in `state.py`
**Reader**: Build 3's `run_parallel_builders()` for BuilderResult extraction

```json
{
  "total_cost": 0.0,
  "health": "passed|partial|failed|unknown",
  "completed_phases": ["..."],
  "contract_report": {
    "total_contracts": 0,
    "verified_contracts": 0,
    "violated_contracts": 0,
    "missing_implementations": 0,
    "violations": [],
    "health": "unknown",
    "verified_contract_ids": [],
    "violated_contract_ids": []
  },
  "endpoint_test_report": {
    "total_endpoints": 0,
    "tested_endpoints": 0,
    "passed_endpoints": 0,
    "failed_endpoints": 0,
    "untested_contracts": [],
    "health": "unknown"
  },
  "registered_artifacts": [],
  "agent_teams_active": false,
  "summary": {
    "success": true,
    "test_passed": 150,
    "test_total": 160,
    "convergence_ratio": 0.95
  }
}
```

**CRITICAL**: The `summary` dict is the cross-build contract. Build 3 reads `summary.success`, `summary.test_passed`, `summary.test_total`, `summary.convergence_ratio` to construct `BuilderResult`. If Build 2 does not write these fields, Build 3 cannot parse builder results.

### 7.2 Build 3: PipelineState (PIPELINE_STATE.json)

**Path**: `.super-orchestrator/PIPELINE_STATE.json`
**Writer**: `PipelineState.save()` using `atomic_write_json()`
**Reader**: `PipelineState.load()` for resume

```json
{
  "pipeline_id": "uuid",
  "prd_path": "path/to/prd.md",
  "config_path": "config.yaml",
  "depth": "standard",
  "current_state": "builders_running",
  "previous_state": "contracts_registering",
  "completed_phases": ["init", "architect_running", "architect_review", "contracts_registering"],
  "phase_artifacts": {
    "architect_running": {"service_map": "path", "domain_model": "path"},
    "contracts_registering": {"registry": "path"}
  },
  "architect_retries": 0,
  "max_architect_retries": 2,
  "service_map_path": "path",
  "contract_registry_path": "path",
  "domain_model_path": "path",
  "builder_statuses": {"auth-service": "building", "order-service": "built"},
  "builder_costs": {"auth-service": 15.0, "order-service": 12.0},
  "builder_results": [{"system_id": "...", "service_id": "...", "success": true, "...": "..."}],
  "total_builders": 3,
  "successful_builders": 2,
  "services_deployed": ["auth-service", "order-service"],
  "integration_report_path": "path",
  "quality_attempts": 0,
  "max_quality_retries": 3,
  "last_quality_results": {},
  "quality_report_path": "path",
  "total_cost": 45.0,
  "phase_costs": {"architect_running": 5.0, "builders_running": 30.0},
  "budget_limit": null,
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "interrupted": false,
  "interrupt_reason": "",
  "schema_version": 1
}
```

### 7.3 Build 3: PipelineCostTracker

```json
{
  "phases": {
    "architect_running": {
      "phase_name": "architect_running",
      "cost_usd": 5.0,
      "start_time": "ISO-8601",
      "end_time": "ISO-8601",
      "sub_phases": {}
    }
  },
  "budget_limit": null
}
```

### 7.4 Build 3: IntegrationReport

```json
{
  "services_deployed": 3,
  "services_healthy": 3,
  "contract_tests_total": 50,
  "contract_tests_passed": 48,
  "integration_tests_total": 20,
  "integration_tests_passed": 18,
  "data_flow_tests_total": 10,
  "data_flow_tests_passed": 9,
  "boundary_tests_total": 15,
  "boundary_tests_passed": 14,
  "violations": [],
  "overall_health": "passed"
}
```

### 7.5 Build 3: QualityGateReport

```json
{
  "layers": {
    "layer1_service": {"layer": "layer1_service", "verdict": "passed", "violations": [], "total_checks": 3, "passed_checks": 3},
    "layer2_contract": {"layer": "layer2_contract", "verdict": "passed", "violations": [], "contract_violations": []},
    "layer3_system": {"layer": "layer3_system", "verdict": "partial", "violations": [{"code": "SEC-001", "...": "..."}]},
    "layer4_adversarial": {"layer": "layer4_adversarial", "verdict": "passed", "violations": []}
  },
  "overall_verdict": "partial",
  "fix_attempts": 1,
  "max_fix_attempts": 3,
  "total_violations": 5,
  "blocking_violations": 1
}
```

---

## 8. Config Cross-References

### 8.1 Build 2 Config Fields Referencing Build 1

| Config Field | Dataclass | Purpose | Default |
|-------------|-----------|---------|---------|
| `contract_engine.enabled` | `ContractEngineConfig` | Enable Contract Engine MCP | `False` |
| `contract_engine.mcp_command` | `ContractEngineConfig` | MCP server command | `"python"` |
| `contract_engine.mcp_args` | `ContractEngineConfig` | MCP server args | `["-m", "src.contract_engine.mcp_server"]` |
| `contract_engine.database_path` | `ContractEngineConfig` | SQLite DB path for MCP env | `""` |
| `contract_engine.server_root` | `ContractEngineConfig` | Build 1 project root (cwd for subprocess) | `""` |
| `contract_engine.startup_timeout_ms` | `ContractEngineConfig` | MCP server startup timeout | `30000` |
| `contract_engine.tool_timeout_ms` | `ContractEngineConfig` | Per-tool call timeout | `60000` |
| `contract_engine.validation_on_build` | `ContractEngineConfig` | Validate endpoints during build | `True` |
| `contract_engine.test_generation` | `ContractEngineConfig` | Generate contract tests | `True` |
| `codebase_intelligence.enabled` | `CodebaseIntelligenceConfig` | Enable Codebase Intelligence MCP | `False` |
| `codebase_intelligence.mcp_command` | `CodebaseIntelligenceConfig` | MCP server command | `"python"` |
| `codebase_intelligence.mcp_args` | `CodebaseIntelligenceConfig` | MCP server args | `["-m", "src.codebase_intelligence.mcp_server"]` |
| `codebase_intelligence.database_path` | `CodebaseIntelligenceConfig` | SQLite DB path | `""` |
| `codebase_intelligence.chroma_path` | `CodebaseIntelligenceConfig` | ChromaDB path | `""` |
| `codebase_intelligence.graph_path` | `CodebaseIntelligenceConfig` | NetworkX graph path | `""` |
| `codebase_intelligence.server_root` | `CodebaseIntelligenceConfig` | Build 1 project root | `""` |
| `codebase_intelligence.replace_static_map` | `CodebaseIntelligenceConfig` | Replace static codebase map | `True` |
| `codebase_intelligence.register_artifacts` | `CodebaseIntelligenceConfig` | Auto-register new files | `True` |

### 8.2 Build 3 Config Fields Referencing Build 1

| Config Field | Dataclass | Purpose | Default |
|-------------|-----------|---------|---------|
| `build1_services_dir` | `SuperOrchestratorConfig` | Path to Build 1 project root for MCP subprocess | `""` |
| `integration.traefik_image` | `IntegrationConfig` | Traefik Docker image | `"traefik:v3.6"` |
| `integration.compose_file` | `IntegrationConfig` | Docker Compose file path | `"docker-compose.yml"` |
| `integration.test_compose_file` | `IntegrationConfig` | Test Docker Compose file | `"docker-compose.test.yml"` |

### 8.3 Build 3 Config Fields Referencing Build 2

| Config Field | Dataclass | Purpose | Default |
|-------------|-----------|---------|---------|
| `agent_team_config_path` | `SuperOrchestratorConfig` | Path to Build 2 config.yaml template | `""` |
| `builder.max_concurrent` | `BuilderConfig` | Max parallel builders | `3` |
| `builder.timeout_per_builder` | `BuilderConfig` | Per-builder timeout (seconds) | `1800` |
| `builder.depth` | `BuilderConfig` | Builder depth mode | `"thorough"` |
| `quality_gate.max_fix_retries` | `QualityGateConfig` | Fix loop iterations | `3` |

### 8.4 Build 3 SuperOrchestratorConfig (complete)

```yaml
architect:
  max_retries: 2
  timeout: 900
  auto_approve: false
builder:
  max_concurrent: 3
  timeout_per_builder: 1800
  depth: "thorough"
integration:
  timeout: 600
  traefik_image: "traefik:v3.6"
  compose_file: "docker-compose.yml"
  test_compose_file: "docker-compose.test.yml"
quality_gate:
  max_fix_retries: 3
  layer3_scanners: ["security", "cors", "logging", "trace", "secrets", "docker", "health"]
  layer4_enabled: true
  blocking_severity: "error"
budget_limit: null
depth: "standard"
phase_timeouts: {}
build1_services_dir: ""
agent_team_config_path: ""
```

### 8.5 Depth Gating Cross-Build Effects

| Depth | Build 2 Effects | Build 3 Effects |
|-------|----------------|-----------------|
| `quick` | All contract/codebase features OFF | N/A (Build 3 does not use quick) |
| `standard` | Contract Engine enabled (validation only), Codebase Intel enabled (queries only, no replace/register), CONTRACT-001/002 on | Builder depth = "standard" |
| `thorough` | Full contract engine + codebase intel + all 4 CONTRACT scans + agent teams (if env set) | Builder depth = "thorough", e2e_pass_rate_gate applies |
| `exhaustive` | Same as thorough | Builder depth = "exhaustive" |

---

## 9. Integration Matrix Summary

### 9.1 MCP Tool Interfaces (Build 1 -> Build 2 / Build 3)

| Source | Target | Interface Type | Tools | Verification Test Needed |
|--------|--------|---------------|-------|------------------------|
| Build 1 Architect MCP | Build 2 ArchitectClient | MCP stdio (4 tools) | decompose, get_service_map, get_contracts_for_service, get_domain_model | Tool call success + response schema for all 4 |
| Build 1 Architect MCP | Build 3 pipeline.run_architect_phase | MCP stdio (1 tool) | decompose | Decompose PRD returns ServiceMap + DomainModel |
| Build 1 Contract Engine MCP | Build 2 ContractEngineClient | MCP stdio (6 tools) | get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts | All 6 return correct dataclass + safe defaults on error |
| Build 1 Contract Engine MCP | Build 3 pipeline.run_contract_registration | MCP stdio (3 tools) | create_contract, validate_spec, list_contracts | Create + validate + list roundtrip |
| Build 1 Codebase Intelligence MCP | Build 2 CodebaseIntelligenceClient | MCP stdio (7 tools) | find_definition, find_callers, find_dependencies, search_semantic, get_service_interface, check_dead_code, register_artifact | All 7 return correct dataclass + safe defaults on error |

### 9.2 Subprocess Interfaces (Build 3 -> Build 2)

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 3 pipeline.run_parallel_builders | Build 2 agent_team CLI | Subprocess | `python -m agent_team --cwd {dir} --depth {depth}` | Builder completes, STATE.json has summary dict |
| Build 3 fix_loop.feed_violations_to_builder | Build 2 agent_team CLI | Subprocess | `python -m agent_team --cwd {dir} --depth quick` | FIX_INSTRUCTIONS.md consumed, violations reduced |
| Build 3 pipeline.generate_builder_config | Build 2 config.yaml | YAML file | depth, milestone, e2e_testing, post_orchestration_scans | Generated config loadable by Build 2 `_dict_to_config()` |

### 9.3 HTTP Interfaces (Build 1 Internal)

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 1 Architect (decompose) | Build 1 Contract Engine | HTTP POST | `/api/contracts` (register stubs) | Contracts appear in Contract Engine after decompose |
| Build 1 Architect MCP (get_contracts_for_service) | Build 1 Contract Engine | HTTP GET | `/api/contracts?service_name={name}` | Returns contracts list for known service |

### 9.4 State Persistence Interfaces

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 2 RunState.to_dict() | Build 3 run_parallel_builders | JSON file | STATE.json `summary` dict (success, test_passed, test_total, convergence_ratio) | Summary fields present and correctly typed |
| Build 3 PipelineState | Build 3 resume | JSON file | PIPELINE_STATE.json (all phase artifacts, builder results) | Save/load roundtrip preserves all fields |
| Build 3 PipelineState | Build 3 GracefulShutdown | JSON file | Atomic write on signal | State not corrupted on simulated crash |

### 9.5 Docker Infrastructure Interfaces

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 1 docker-compose.yml | Build 3 ComposeGenerator | Docker Compose merge | 3 services + volumes + network | All 3 Build 1 services healthy in merged compose |
| Build 3 ComposeGenerator | Generated services | Docker Compose generation | Per-service Dockerfile, Traefik labels, health checks | Generated services deploy + route through Traefik |
| Build 3 TraefikConfigGenerator | Traefik | Docker labels | PathPrefix rules, strip prefix middleware | HTTP requests route to correct service |
| Build 3 DockerOrchestrator | Docker Compose v2 | Subprocess | `docker compose up/down/ps` | Services start, health check, stop |
| Build 3 ServiceDiscovery | All services | HTTP GET | `/health` or `/healthz` or `/ready` | All services report healthy |

### 9.6 Config Cross-Build Interfaces

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 2 AgentTeamConfig | Build 3 generate_builder_config | Config generation | depth, milestone, e2e, scans fields | Generated YAML matches Build 2 field names |
| Build 3 SuperOrchestratorConfig.build1_services_dir | Build 1 MCP servers | cwd for subprocess | Path to Build 1 project root | MCP servers start from correct directory |
| Build 3 SuperOrchestratorConfig.builder.depth | Build 2 AgentTeamConfig.depth | Propagated value | "quick"\|"standard"\|"thorough"\|"exhaustive" | Builder uses correct depth |

### 9.7 Quality Gate Data Flow

| Source | Target | Interface Type | Specific Items | Verification Test Needed |
|--------|--------|---------------|----------------|------------------------|
| Build 2 BuilderResult | Build 3 Layer1Scanner | Data consumption | success, test_passed, test_total, convergence_ratio | L1 correctly evaluates builder results |
| Build 3 IntegrationReport | Build 3 Layer2Scanner | Data consumption | contract_tests_total/passed, violations | L2 correctly evaluates contract compliance |
| Build 3 Layer3 scanners | Build 2 generated code | File scanning | SEC-001..006, CORS-001..003, LOG-001/004/005, etc. | Scanners find violations in generated code |
| Build 3 QualityGateReport | Build 3 fix_loop | Violation routing | ContractViolation list per service | Violations correctly routed to builder fix |

### 9.8 Complete Verification Checklist

| # | Test | Builds Involved | Priority |
|---|------|----------------|----------|
| 1 | MCP handshake: All 3 Build 1 servers respond to `initialize()` | B1 | CRITICAL |
| 2 | MCP tool listing: 4 + 9 + 7 = 20 tools discovered via `list_tools()` | B1 | CRITICAL |
| 3 | Architect decompose: PRD in -> ServiceMap + DomainModel out (MCP) | B1, B3 | CRITICAL |
| 4 | Contract Engine create+validate: Contract stored and retrievable | B1, B2, B3 | CRITICAL |
| 5 | Contract Engine validate_endpoint: Detects schema mismatch | B1, B2 | CRITICAL |
| 6 | Codebase Intelligence register+find: Index file, query symbol | B1, B2 | CRITICAL |
| 7 | Build 2 ContractEngineClient: All 6 methods return correct types | B1, B2 | HIGH |
| 8 | Build 2 CodebaseIntelligenceClient: All 7 methods return correct types | B1, B2 | HIGH |
| 9 | Build 2 MCP fallback: Safe defaults when server unavailable | B2 | HIGH |
| 10 | Builder subprocess: Build 3 launches Build 2, gets STATE.json | B2, B3 | CRITICAL |
| 11 | STATE.json summary: Build 2 writes `summary` dict, Build 3 reads it | B2, B3 | CRITICAL |
| 12 | Builder config generation: Build 3 config loadable by Build 2 | B2, B3 | CRITICAL |
| 13 | Fix pass: FIX_INSTRUCTIONS.md consumed by Build 2 quick mode | B2, B3 | HIGH |
| 14 | Docker Compose merge: Build 1 + Build 3 services coexist | B1, B3 | HIGH |
| 15 | Inter-container DNS: Architect reaches Contract Engine by hostname | B1 | HIGH |
| 16 | Traefik routing: PathPrefix labels route to correct service | B3 | HIGH |
| 17 | Health checks: All services respond to health endpoints | B1, B3 | HIGH |
| 18 | Quality Gate L1: Correctly parses BuilderResult from Build 2 | B2, B3 | HIGH |
| 19 | Quality Gate L3: Scanners find violations in generated code | B2, B3 | HIGH |
| 20 | Pipeline state persistence: Save/resume at every phase | B3 | HIGH |
| 21 | Graceful shutdown: State saved on SIGINT | B3 | MEDIUM |
| 22 | Budget tracking: Cost accumulated across all phases | B3 | MEDIUM |
| 23 | Backward compat: Build 2 with all B2 features disabled = v14.0 | B2 | HIGH |
| 24 | Agent Teams fallback: AgentTeamsBackend -> CLIBackend on failure | B2 | MEDIUM |
| 25 | Contract compliance E2E: Schemathesis against live services | B1, B3 | HIGH |
| 26 | Cross-service flows: Generated flow tests pass | B3 | MEDIUM |
| 27 | Boundary tests: camelCase/snake_case, timezone, null handling | B3 | MEDIUM |
| 28 | Contract compliance matrix: Tracking document generated | B2, B3 | LOW |
| 29 | Pact verification: Consumer-driven contracts verified | B3 | MEDIUM |
| 30 | Adversarial scanner: Dead events, dead contracts detected | B3 | LOW |

---

## Appendix A: MCP .mcp.json Configuration

Build 1's `.mcp.json` (the single source of truth for MCP server configs):

```json
{
  "mcpServers": {
    "architect": {
      "command": "python",
      "args": ["-m", "src.architect.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/architect.db",
        "CONTRACT_ENGINE_URL": "http://localhost:8002"
      }
    },
    "contract-engine": {
      "command": "python",
      "args": ["-m", "src.contract_engine.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/contracts.db"
      }
    },
    "codebase-intelligence": {
      "command": "python",
      "args": ["-m", "src.codebase_intelligence.mcp_server"],
      "env": {
        "DATABASE_PATH": "./data/symbols.db",
        "CHROMA_PATH": "./data/chroma",
        "GRAPH_PATH": "./data/graph.json"
      }
    }
  }
}
```

## Appendix B: State Machine Transitions (Build 3)

| # | Trigger | Source | Dest | Guard | Cross-Build Dependency |
|---|---------|--------|------|-------|----------------------|
| 1 | start_architect | init | architect_running | prd_loaded | Build 1 Architect MCP |
| 2 | architect_done | architect_running | architect_review | has_service_map | Build 1 output artifacts |
| 3 | approve_architecture | architect_review | contracts_registering | architecture_valid | Build 1 validation |
| 4 | contracts_ready | contracts_registering | builders_running | contracts_valid | Build 1 Contract Engine MCP |
| 5 | builders_done | builders_running | builders_complete | any_builder_success | Build 2 STATE.json |
| 6 | start_integration | builders_complete | integrating | has_successful_builds | Build 2 output dirs |
| 7 | integration_done | integrating | quality_gate | integration_ran | Build 1 services (Docker) |
| 8 | quality_passed | quality_gate | complete | all_gates_passed | None (internal) |
| 9 | quality_failed | quality_gate | fix_pass | has_violations | None (internal) |
| 10 | fix_done | fix_pass | quality_gate | fix_applied | Build 2 fix subprocess |
| 11 | fail | [non-terminal] | failed | -- | None |
| 12 | retry_architect | architect_running | architect_running | retries_remaining | Build 1 Architect MCP |
| 13 | skip_contracts | contracts_registering | builders_running | -- | None |

## Appendix C: Data Flow Through Pipeline

```
PRD.md
  |
  v
[Build 1: Architect MCP] -- decompose(prd_text) -->
  |
  +-- ServiceMap (YAML)
  +-- DomainModel (JSON)
  +-- ContractStubs (list[dict])
  |
  v
[Build 1: Contract Engine MCP] -- create_contract(), validate_spec() -->
  |
  +-- Contract Registry (SQLite)
  |
  v
[Build 3: generate_builder_config()] -- writes config.yaml per service -->
  |
  v
[Build 2: agent_team --cwd {dir}] x N parallel (Semaphore bounded)
  |
  +-- Per-service source code
  +-- Per-service tests
  +-- Per-service Dockerfile
  +-- .agent-team/STATE.json (with summary dict)
  |
  v
[Build 3: ComposeGenerator] -- produces docker-compose.yml -->
  |
  v
[Build 3: DockerOrchestrator] -- docker compose up -d -->
  |
  +-- Build 1 services (architect, contract-engine, codebase-intel)
  +-- Infrastructure (traefik, postgres, redis)
  +-- Generated services (auth, orders, notifications, ...)
  |
  v
[Build 3: ContractComplianceVerifier]
  +-- Schemathesis (OpenAPI fuzz testing against live services)
  +-- Pact (consumer-driven contract verification)
  |
  v
[Build 3: CrossServiceTestRunner]
  +-- Flow tests (multi-service request chains)
  +-- Boundary tests (camelCase, timezone, null)
  |
  v
[Build 3: QualityGateEngine]
  +-- Layer 1: Per-service (BuilderResult evaluation)
  +-- Layer 2: Contract compliance (IntegrationReport)
  +-- Layer 3: System-level (40 scan codes: security, CORS, logging, secrets, Docker, health)
  +-- Layer 4: Adversarial (dead events, dead contracts, orphans, naming, error handling, races)
  |
  v
[PASS] -> complete
[FAIL] -> fix_pass -> [Build 2: agent_team --depth quick] -> re-verify
```
