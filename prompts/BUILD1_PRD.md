# Super Agent Team — Build 1 PRD: Architect + Contract Engine + Codebase Intelligence

Build 1 of the Super Agent Team platform. Three foundational services that provide PRD decomposition, API contract management, and live codebase intelligence via MCP tools. All services use Python 3.12+, FastAPI, SQLite with WAL mode, and the MCP Python SDK. No frontend, no UI — pure backend infrastructure.

Each requirement includes `(review_cycles: N)` — this is tracked by the build system. Agents must preserve this suffix when modifying requirements.

## Technology Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI 0.129.0 with uvicorn
- **Database:** SQLite with WAL mode (3 separate databases: architect.db, contracts.db, symbols.db)
- **Vector Search:** ChromaDB 1.5.0 (PersistentClient with all-MiniLM-L6-v2 default embedding)
- **Graph Analysis:** NetworkX 3.6.1 (DiGraph for dependency analysis)
- **AST Parsing:** tree-sitter 0.25.2 with language grammars (Python 0.25.0, TypeScript 0.23.2, C# 0.23.1, Go 0.25.0)
- **MCP SDK:** mcp>=1.25,<2 (high-level MCPServer API with @mcp.tool() decorators, stdio transport)
- **API Validation:** openapi-spec-validator, prance 25.4.8.0 for $ref resolution
- **Contract Testing:** Schemathesis 4.10.1 (property-based API testing from OpenAPI specs)
- **AsyncAPI:** Custom lightweight parser (~500 lines) using pyyaml + jsonschema (no mature Python library exists)
- **Configuration:** pydantic-settings>=2.1.0 (BaseSettings with env var loading)
- **Containerization:** Docker Compose with 3 services, bridge network, named volumes, health checks

## Architectural Principle: Async/Sync Boundary

**Rule:** All FastAPI endpoint handlers are async. All database operations (SQLAlchemy), ChromaDB operations, and file I/O are synchronous. Every synchronous call from an async context MUST be wrapped in `asyncio.to_thread()`. A bare synchronous call inside an async handler will block the entire event loop. This applies to: ChromaDB `collection.add()`/`query()`/`get()`, SQLAlchemy `session.execute()`/`commit()`, and any `open()`/`pathlib.Path.read_text()` on large files. See TECH-035 and TECH-036 for detailed requirements.

## Project Structure

```
super-team/
  pyproject.toml
  README.md
  docker-compose.yml
  .env.example
  .mcp.json

  src/
    __init__.py

    shared/
      __init__.py
      models/
        __init__.py
        architect.py
        contracts.py
        codebase.py
        common.py
      db/
        __init__.py
        connection.py
        schema.py
      config.py
      constants.py
      logging.py
      errors.py

    architect/
      __init__.py
      main.py
      mcp_server.py
      config.py
      routers/
        __init__.py
        decomposition.py
        service_map.py
        domain_model.py
        health.py
      services/
        __init__.py
        prd_parser.py
        service_boundary.py
        contract_generator.py
        domain_modeler.py
        validator.py
      storage/
        __init__.py
        service_map_store.py
        domain_model_store.py

    contract_engine/
      __init__.py
      main.py
      mcp_server.py
      config.py
      routers/
        __init__.py
        contracts.py
        validation.py
        tests.py
        implementations.py
        breaking_changes.py
        health.py
      services/
        __init__.py
        contract_store.py
        openapi_validator.py
        asyncapi_parser.py
        asyncapi_validator.py
        schema_registry.py
        version_manager.py
        breaking_change_detector.py
        test_generator.py
        compliance_checker.py
        implementation_tracker.py
      storage/
        __init__.py

    codebase_intelligence/
      __init__.py
      main.py
      mcp_server.py
      config.py
      routers/
        __init__.py
        symbols.py
        dependencies.py
        search.py
        artifacts.py
        dead_code.py
        health.py
      services/
        __init__.py
        ast_parser.py
        symbol_extractor.py
        import_resolver.py
        graph_builder.py
        graph_analyzer.py
        semantic_indexer.py
        semantic_searcher.py
        dead_code_detector.py
        incremental_indexer.py
        service_interface_extractor.py
      parsers/
        __init__.py
        python_parser.py
        typescript_parser.py
        csharp_parser.py
        go_parser.py
      storage/
        __init__.py
        symbol_db.py
        graph_db.py
        chroma_store.py

  tests/
    __init__.py
    conftest.py
    test_shared/
      __init__.py
      test_models.py
      test_db_connection.py
      test_config.py
    test_architect/
      __init__.py
      test_prd_parser.py
      test_service_boundary.py
      test_contract_generator.py
      test_domain_modeler.py
      test_validator.py
      test_routers.py
      test_mcp_tools.py
    test_contract_engine/
      __init__.py
      test_contract_store.py
      test_openapi_validator.py
      test_asyncapi_parser.py
      test_asyncapi_validator.py
      test_schema_registry.py
      test_version_manager.py
      test_breaking_change_detector.py
      test_test_generator.py
      test_compliance_checker.py
      test_implementation_tracker.py
      test_routers.py
      test_mcp_tools.py
    test_codebase_intelligence/
      __init__.py
      test_ast_parser.py
      test_symbol_extractor.py
      test_import_resolver.py
      test_graph_builder.py
      test_graph_analyzer.py
      test_semantic_indexer.py
      test_semantic_searcher.py
      test_dead_code_detector.py
      test_incremental_indexer.py
      test_language_parsers.py
      test_routers.py
      test_mcp_tools.py
    test_integration/
      __init__.py
      test_architect_to_contracts.py
      test_codebase_indexing.py
      test_mcp_roundtrip.py
      test_docker_compose.py

  docker/
    architect/
      Dockerfile
      requirements.txt
    contract_engine/
      Dockerfile
      requirements.txt
    codebase_intelligence/
      Dockerfile
      requirements.txt

  docs/
    architecture.md
    api_reference.md
    mcp_tools.md
    deployment.md

  sample_data/
    sample_prd.md
    sample_service_map.yaml
    sample_openapi.yaml
    sample_asyncapi.yaml
    sample_codebase/
      auth_service/
        auth.py
        models.py
      billing_service/
        billing.ts
        types.ts
```

## Milestone 1: Core Data Models and Shared Infrastructure

Project scaffolding, all Pydantic data models, SQLite database schemas, Docker base configuration, and shared utilities. This milestone produces the foundation that all subsequent milestones depend on.

### Functional Requirements

- [ ] REQ-001: Create pyproject.toml with all pinned dependencies — fastapi==0.129.0, tree-sitter==0.25.2, tree-sitter-python==0.25.0, tree-sitter-typescript==0.23.2, tree-sitter-c-sharp==0.23.1, tree-sitter-go==0.25.0, chromadb==1.5.0, networkx==3.6.1, mcp>=1.25,<2, schemathesis==4.10.1, openapi-spec-validator>=0.7.0, prance>=25.0.0, pyyaml>=6.0, jsonschema>=4.20.0, pydantic>=2.5.0, pydantic-settings>=2.1.0, python-dotenv>=1.0.0, httpx>=0.27.0, uvicorn>=0.30.0 — dev dependencies: pytest>=8.0.0, pytest-asyncio>=0.23.0, pytest-cov>=4.1.0, ruff>=0.5.0, mypy>=1.8.0 (review_cycles: 0)
- [ ] REQ-002: Create all Pydantic v2 Architect models in src/shared/models/architect.py — ServiceStack, ServiceDefinition (name with pattern ^[a-z][a-z0-9-]*$, domain, description, stack, estimated_loc ge=100 le=200000, owns_entities, provides_contracts, consumes_contracts), ServiceMap (project_name, services min_length=1, generated_at, prd_hash, build_cycle_id: str | None = None), RelationshipType enum (OWNS, REFERENCES, TRIGGERS, EXTENDS, DEPENDS_ON), DomainEntity (name, description, owning_service, fields list, state_machine: StateMachine | None = None), EntityField (name, type, required=True, description=""), StateMachine (states min_length=2, initial_state, transitions), StateTransition (from_state, to_state, trigger, guard: str | None = None), DomainRelationship (source_entity, target_entity, relationship_type, cardinality pattern ^(1|N):(1|N)$, description=""), DomainModel (entities, relationships, generated_at), DecompositionResult (service_map, domain_model, contract_stubs: list[dict] = [], validation_issues: list[str] = [], interview_questions: list[str] = []), DecomposeRequest (prd_text: str = Field(min_length=10, max_length=1_048_576)), DecompositionRun (id: str UUID, prd_content_hash: str, status: str pattern pending|running|completed|failed|review default "pending", service_map_id: str | None = None, domain_model_id: str | None = None, validation_issues: list[str] = [], interview_questions: list[str] = [], started_at: datetime, completed_at: datetime | None = None) (review_cycles: 0)
- [ ] REQ-003: Create all Pydantic v2 Contract models in src/shared/models/contracts.py — ContractType enum (openapi, asyncapi, json_schema), ContractStatus enum (active, deprecated, draft), ImplementationStatus enum (verified, pending, failed), ContractEntry (id, type, version with semver pattern, service_name, spec dict, spec_hash auto-computed via TECH-009 algorithm not provided by caller, status: ContractStatus = ContractStatus.DRAFT, build_cycle_id: str | None = None, created_at, updated_at, model_config from_attributes=True), ContractCreate (service_name max_length=100, type, version, spec, build_cycle_id: str | None = None), ContractListResponse (items, total, page, page_size), OpenAPIContract (contract_id, openapi_version=3.1.0, title, api_version, endpoints list, schemas dict), EndpointSpec (path, method pattern GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS, operation_id: str | None = None, summary="", parameters: list[dict] = [], request_body_schema: dict | None = None, response_schemas: dict[str, dict] = {}), AsyncAPIContract (contract_id, asyncapi_version=3.0.0, title, api_version, channels list, operations list, schemas dict), ChannelSpec (name, address, description="", messages list), MessageSpec (name, content_type=application/json, payload_schema: dict = {}, headers_schema: dict | None = None), OperationSpec (name, action pattern send|receive, channel_name, summary="", message_names: list[str] = []), SharedSchema (name, schema: dict, owning_service: str, consuming_services: list[str] = []), ContractVersion (contract_id, version, spec_hash, build_cycle_id, created_at, is_breaking=False, breaking_changes: list[BreakingChange] = []), BreakingChange (change_type, path, old_value: str | None = None, new_value: str | None = None, severity pattern error|warning|info default "error", affected_consumers: list[str] = []), ImplementationRecord (contract_id, service_name, evidence_path, status: ImplementationStatus = ImplementationStatus.PENDING, verified_at: datetime | None = None, created_at), ValidationResult (valid: bool, errors: list[str] = [], warnings: list[str] = []), ValidateRequest (spec: dict, type: ContractType), MarkRequest (contract_id: str, service_name: str, evidence_path: str), MarkResponse (marked: bool, total_implementations: int, all_implemented: bool), UnimplementedContract (id: str, type: str, version: str, expected_service: str, status: str), ContractTestSuite (contract_id, framework pattern pytest|jest default "pytest", test_code, test_count ge=0, generated_at), ComplianceResult (endpoint_path, method, compliant, violations list), ComplianceViolation (field, expected, actual, severity="error") (review_cycles: 0)
- [ ] REQ-004: Create all Pydantic v2 Codebase Intelligence models in src/shared/models/codebase.py — SymbolKind enum (class, function, interface, type, enum, variable, method), Language enum (python, typescript, csharp, go), DependencyRelation enum (imports, calls, inherits, implements, uses), SymbolDefinition (id as file_path::symbol_name generated via @model_validator(mode='before') from file_path and symbol_name, file_path, symbol_name, kind, language, service_name: str | None = None, line_start ge=1, line_end ge=1, signature: str | None = None, docstring: str | None = None, is_exported=True, parent_symbol: str | None = None), ImportReference (source_file, target_file, imported_names: list[str] = [], line ge=1, is_relative=False), DependencyEdge (source_symbol_id, target_symbol_id, relation, source_file, target_file, line: int | None = None), CodeChunk (id, file_path, content, language, service_name: str | None = None, symbol_name: str | None = None, symbol_kind: SymbolKind | None = None, line_start, line_end), SemanticSearchResult (chunk_id, file_path, symbol_name: str | None = None, content, score ge=0.0 le=1.0, language, service_name: str | None = None, line_start, line_end), ServiceInterface (service_name, endpoints: list[dict] = [], events_published: list[dict] = [], events_consumed: list[dict] = [], exported_symbols: list[SymbolDefinition] = []), DeadCodeEntry (symbol_name, file_path, kind, line, service_name: str | None = None, confidence pattern high|medium|low default "high"), GraphAnalysis (node_count, edge_count, is_dag, circular_dependencies: list[list[str]] = [], top_files_by_pagerank: list[tuple[str, float]] = [], connected_components, build_order: list[str] | None = None), IndexStats (total_files, total_symbols, total_edges, total_chunks, languages: dict[str, int] = {}, services: dict[str, int] = {}, last_indexed_at: datetime | None = None) (review_cycles: 0)
- [ ] REQ-005: Create Common models in src/shared/models/common.py — BuildCycle (id, project_name, started_at, completed_at: datetime | None = None, status pattern running|completed|failed|paused default "running", services_planned=0, services_completed=0, total_cost_usd=0.0), ArtifactRegistration (file_path, service_name, build_cycle_id: str | None = None, registered_at), HealthStatus (status pattern healthy|degraded|unhealthy default "healthy", service_name, version, database pattern connected|disconnected default "connected", uptime_seconds, details: dict[str, Any] = Field(default_factory=dict) — free-form metadata for debugging e.g. {'indexed_files': 1234, 'graph_nodes': 567}) (review_cycles: 0)
- [ ] REQ-006: Create SQLite connection pool in src/shared/db/connection.py — ConnectionPool class with thread-local connections, WAL mode initialization (PRAGMA journal_mode=WAL, PRAGMA busy_timeout=30000, PRAGMA foreign_keys=ON), Row factory (sqlite3.Row), get() method returns thread-local connection, close() method, timeout parameter defaulting to 30.0 seconds (review_cycles: 0)
- [ ] REQ-007: Create schema initialization in src/shared/db/schema.py — init_architect_db() creates tables with the following exact SQL: `CREATE TABLE IF NOT EXISTS service_maps (id TEXT PRIMARY KEY, project_name TEXT NOT NULL, prd_hash TEXT NOT NULL, map_json TEXT NOT NULL, build_cycle_id TEXT, generated_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX IF NOT EXISTS idx_smap_project ON service_maps(project_name); CREATE INDEX IF NOT EXISTS idx_smap_prd ON service_maps(prd_hash); CREATE TABLE IF NOT EXISTS domain_models (id TEXT PRIMARY KEY, project_name TEXT NOT NULL, model_json TEXT NOT NULL, generated_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX IF NOT EXISTS idx_dmodel_project ON domain_models(project_name); CREATE TABLE IF NOT EXISTS decomposition_runs (id TEXT PRIMARY KEY, prd_content_hash TEXT NOT NULL, service_map_id TEXT REFERENCES service_maps(id), domain_model_id TEXT REFERENCES domain_models(id), validation_issues TEXT NOT NULL DEFAULT '[]', interview_questions TEXT NOT NULL DEFAULT '[]', status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','review')), started_at TEXT NOT NULL DEFAULT (datetime('now')), completed_at TEXT);` init_contracts_db() creates tables: `CREATE TABLE IF NOT EXISTS build_cycles (id TEXT PRIMARY KEY, project_name TEXT NOT NULL, started_at TEXT NOT NULL DEFAULT (datetime('now')), completed_at TEXT, status TEXT NOT NULL DEFAULT 'running' CHECK(status IN ('running','completed','failed','paused')), services_planned INTEGER NOT NULL DEFAULT 0, services_completed INTEGER NOT NULL DEFAULT 0, total_cost_usd REAL NOT NULL DEFAULT 0.0); CREATE INDEX idx_build_cycles_status ON build_cycles(status); CREATE TABLE IF NOT EXISTS contracts (id TEXT PRIMARY KEY, type TEXT NOT NULL CHECK(type IN ('openapi','asyncapi','json_schema')), version TEXT NOT NULL, service_name TEXT NOT NULL, spec_json TEXT NOT NULL, spec_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','deprecated','draft')), build_cycle_id TEXT REFERENCES build_cycles(id) ON DELETE SET NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(service_name, type, version)); CREATE INDEX idx_contracts_service ON contracts(service_name); CREATE INDEX idx_contracts_type ON contracts(type); CREATE INDEX idx_contracts_status ON contracts(status); CREATE INDEX idx_contracts_build ON contracts(build_cycle_id); CREATE INDEX idx_contracts_hash ON contracts(spec_hash); CREATE TABLE IF NOT EXISTS contract_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE, version TEXT NOT NULL, spec_hash TEXT NOT NULL, build_cycle_id TEXT REFERENCES build_cycles(id) ON DELETE SET NULL, is_breaking INTEGER NOT NULL DEFAULT 0, change_summary TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX idx_versions_contract ON contract_versions(contract_id); CREATE INDEX idx_versions_build ON contract_versions(build_cycle_id); CREATE TABLE IF NOT EXISTS breaking_changes (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_version_id INTEGER NOT NULL REFERENCES contract_versions(id) ON DELETE CASCADE, change_type TEXT NOT NULL, json_path TEXT NOT NULL, old_value TEXT, new_value TEXT, severity TEXT NOT NULL DEFAULT 'error' CHECK(severity IN ('error','warning','info')), affected_consumers TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX idx_breaking_version ON breaking_changes(contract_version_id); CREATE TABLE IF NOT EXISTS implementations (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE, service_name TEXT NOT NULL, evidence_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('verified','pending','failed')), verified_at TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(contract_id, service_name)); CREATE INDEX idx_impl_contract ON implementations(contract_id); CREATE INDEX idx_impl_service ON implementations(service_name); CREATE INDEX idx_impl_status ON implementations(status); CREATE TABLE IF NOT EXISTS test_suites (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE, framework TEXT NOT NULL DEFAULT 'pytest' CHECK(framework IN ('pytest','jest')), test_code TEXT NOT NULL, test_count INTEGER NOT NULL DEFAULT 0, spec_hash TEXT NOT NULL, generated_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(contract_id, framework)); CREATE INDEX idx_tests_contract ON test_suites(contract_id); CREATE TABLE IF NOT EXISTS shared_schemas (name TEXT PRIMARY KEY, schema_json TEXT NOT NULL, owning_service TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE TABLE IF NOT EXISTS schema_consumers (schema_name TEXT NOT NULL REFERENCES shared_schemas(name) ON DELETE CASCADE, service_name TEXT NOT NULL, PRIMARY KEY (schema_name, service_name));` init_symbols_db() creates tables: `CREATE TABLE IF NOT EXISTS indexed_files (file_path TEXT PRIMARY KEY, language TEXT NOT NULL CHECK(language IN ('python','typescript','csharp','go','unknown')), service_name TEXT, file_hash TEXT NOT NULL, loc INTEGER NOT NULL DEFAULT 0, indexed_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX idx_files_service ON indexed_files(service_name); CREATE INDEX idx_files_language ON indexed_files(language); CREATE INDEX idx_files_hash ON indexed_files(file_hash); CREATE TABLE IF NOT EXISTS symbols (id TEXT PRIMARY KEY, file_path TEXT NOT NULL REFERENCES indexed_files(file_path) ON DELETE CASCADE, symbol_name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('class','function','interface','type','enum','variable','method')), language TEXT NOT NULL, service_name TEXT, line_start INTEGER NOT NULL, line_end INTEGER NOT NULL, signature TEXT, docstring TEXT, is_exported INTEGER NOT NULL DEFAULT 1, parent_symbol TEXT, chroma_id TEXT, indexed_at TEXT NOT NULL DEFAULT (datetime('now'))); CREATE INDEX idx_symbols_file ON symbols(file_path); CREATE INDEX idx_symbols_name ON symbols(symbol_name); CREATE INDEX idx_symbols_kind ON symbols(kind); CREATE INDEX idx_symbols_service ON symbols(service_name); CREATE INDEX idx_symbols_language ON symbols(language); CREATE INDEX idx_symbols_parent ON symbols(parent_symbol); CREATE TABLE IF NOT EXISTS dependency_edges (id INTEGER PRIMARY KEY AUTOINCREMENT, source_symbol_id TEXT NOT NULL, target_symbol_id TEXT NOT NULL, relation TEXT NOT NULL CHECK(relation IN ('imports','calls','inherits','implements','uses')), source_file TEXT NOT NULL, target_file TEXT NOT NULL, line INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now')), UNIQUE(source_symbol_id, target_symbol_id, relation)); CREATE INDEX idx_deps_source ON dependency_edges(source_symbol_id); CREATE INDEX idx_deps_target ON dependency_edges(target_symbol_id); CREATE INDEX idx_deps_source_file ON dependency_edges(source_file); CREATE INDEX idx_deps_target_file ON dependency_edges(target_file); CREATE INDEX idx_deps_relation ON dependency_edges(relation); CREATE TABLE IF NOT EXISTS import_references (id INTEGER PRIMARY KEY AUTOINCREMENT, source_file TEXT NOT NULL REFERENCES indexed_files(file_path) ON DELETE CASCADE, target_file TEXT NOT NULL, imported_names TEXT NOT NULL DEFAULT '[]', line INTEGER NOT NULL, is_relative INTEGER NOT NULL DEFAULT 0, UNIQUE(source_file, target_file, line)); CREATE INDEX idx_imports_source ON import_references(source_file); CREATE INDEX idx_imports_target ON import_references(target_file); CREATE TABLE IF NOT EXISTS graph_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, graph_json TEXT NOT NULL, node_count INTEGER NOT NULL DEFAULT 0, edge_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT (datetime('now')));` All tables use TEXT for timestamps (ISO 8601), TEXT for UUIDs, INTEGER for booleans (review_cycles: 0)
- [ ] REQ-008: Create shared configuration loader in src/shared/config.py — SharedConfig(BaseSettings) with log_level (alias LOG_LEVEL, default "info") and database_path (alias DATABASE_PATH, default ./data/service.db); ArchitectConfig extending SharedConfig with contract_engine_url (alias CONTRACT_ENGINE_URL, default http://contract-engine:8000) and codebase_intel_url (alias CODEBASE_INTEL_URL, default http://codebase-intel:8000); ContractEngineConfig extending SharedConfig; CodebaseIntelConfig extending SharedConfig with chroma_path (alias CHROMA_PATH, default ./data/chroma), graph_path (alias GRAPH_PATH, default ./data/graph.json), contract_engine_url (review_cycles: 0)
- [ ] REQ-009: Create shared constants in src/shared/constants.py — VERSION = "1.0.0", default port numbers (ARCHITECT_PORT=8001, CONTRACT_ENGINE_PORT=8002, CODEBASE_INTEL_PORT=8003, INTERNAL_PORT=8000), supported languages list, supported contract types list (review_cycles: 0)
- [ ] REQ-010: Create structured logging in src/shared/logging.py — Use stdlib `logging` module with a custom `JSONFormatter` class that outputs `{"timestamp": ..., "level": ..., "service_name": ..., "trace_id": ..., "message": ...}`. trace_id is generated as `str(uuid.uuid4())` per request using a FastAPI middleware that sets a `contextvars.ContextVar`. Log level is configurable via `LOG_LEVEL` env var (review_cycles: 0)
- [ ] REQ-011: Create shared exception classes in src/shared/errors.py — AppError base class with status_code and detail properties; ValidationError (status_code=422), NotFoundError (status_code=404), ConflictError (status_code=409), ImmutabilityViolationError (status_code=409), ParsingError (status_code=400), SchemaError (status_code=422), ContractNotFoundError (status_code=404). Register a FastAPI exception handler that catches AppError and returns JSONResponse with status_code and {"detail": error.detail} (review_cycles: 0)
- [ ] REQ-012: Create src/shared/models/__init__.py exporting all model classes; create src/shared/__init__.py, src/shared/db/__init__.py, src/__init__.py (review_cycles: 0)

### Technical Requirements

- [ ] TECH-001: All file paths must use pathlib.Path, never string concatenation — critical for Windows 11 compatibility (review_cycles: 0)
- [ ] TECH-002: All file I/O must specify encoding="utf-8" explicitly (review_cycles: 0)
- [ ] TECH-003: All Pydantic models must use v2 syntax (BaseModel, Field, model_config, from_attributes) — no v1 patterns (review_cycles: 0)
- [ ] TECH-004: SQLite databases must be initialized with WAL mode, busy_timeout=30000, foreign_keys=ON on every new connection (review_cycles: 0)
- [ ] TECH-005: All model validation tests must cover both valid and invalid inputs — test that invalid inputs raise ValidationError with appropriate messages (review_cycles: 0)
- [ ] TECH-032: All UUIDs must be generated using `str(uuid.uuid4())` from the stdlib `uuid` module (review_cycles: 0)
- [ ] TECH-033: All SQL queries MUST use parameterized queries (? placeholders). Never use string formatting or f-strings to build SQL. This prevents SQL injection (review_cycles: 0)
- [ ] TECH-034: PRD text input: max 1MB. Contract spec dict: max 5MB after JSON serialization. Reject with 413 Payload Too Large (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-001: src/shared/models/__init__.py must re-export all model classes from architect.py, contracts.py, codebase.py, common.py for convenient imports (review_cycles: 0)
- [ ] WIRE-002: src/shared/db/schema.py must import ConnectionPool from src/shared/db/connection.py and use it for all schema initialization (review_cycles: 0)
- [ ] WIRE-003: Each service's __init__.py (architect, contract_engine, codebase_intelligence) must be created as empty files to enable Python package imports. src/__init__.py must also be created. All Python package directories shown in the file structure must contain an __init__.py file (empty or with relevant exports) (review_cycles: 0)

### Test Requirements

- [ ] TEST-001: tests/test_shared/test_models.py must test all Pydantic models — valid construction, field validation (min_length, pattern, ge, le), optional field defaults (verify all optional fields default to None, all list fields default to []), serialization roundtrip (model.model_dump() then Model(**data)), from_attributes configuration — minimum 50 test cases across all models including DecomposeRequest, DecompositionRun, ValidateRequest, MarkRequest, MarkResponse, UnimplementedContract (review_cycles: 0)
- [ ] TEST-002: tests/test_shared/test_db_connection.py must test ConnectionPool — WAL mode verification (PRAGMA journal_mode returns 'wal'), foreign key enforcement, thread-local isolation (connections from different threads are different objects), connection reuse (same thread gets same connection), close() method works, timeout configuration (review_cycles: 0)
- [ ] TEST-003: tests/test_shared/test_config.py must test SharedConfig, ArchitectConfig, ContractEngineConfig, CodebaseIntelConfig — default values, environment variable override, alias mapping (review_cycles: 0)
- [ ] TEST-004: tests/conftest.py must provide shared fixtures — tmp_path for temporary databases, sample model instances, mock environment variables (review_cycles: 0)

### Integration Requirements

- [ ] INT-001: Create skeleton FastAPI apps for all 3 services (src/architect/main.py, src/contract_engine/main.py, src/codebase_intelligence/main.py) with lifespan context manager, /api/health endpoint returning HealthStatus (service_name loaded from constants e.g. "architect", "contract-engine", "codebase-intelligence"), and database initialization via schema.py on startup (review_cycles: 0)
- [ ] INT-002: Create docker-compose.yml skeleton with 3 services (architect on port 8001, contract-engine on port 8002, codebase-intel on port 8003), health checks using python urllib.request.urlopen, depends_on with condition service_healthy, named volumes (architect-data, contract-data, intel-data), bridge network (super-team-net), restart unless-stopped (review_cycles: 0)
- [ ] INT-003: Create Dockerfiles for all 3 services using python:3.12-slim base, pip install from requirements.txt, non-root user (appuser), expose 8000, CMD e.g. `["uvicorn", "src.architect.main:app", "--host", "0.0.0.0", "--port", "8000"]` (adjust module path per service: src.architect.main:app, src.contract_engine.main:app, src.codebase_intelligence.main:app) — create corresponding docker/*/requirements.txt files (review_cycles: 0)
- [ ] INT-004: Create .env.example with all environment variables documented — DATABASE_PATH, CONTRACT_ENGINE_URL, CODEBASE_INTEL_URL, CHROMA_PATH, GRAPH_PATH, LOG_LEVEL (review_cycles: 0)
- [ ] INT-005: Create .mcp.json with 3 MCP server configurations: `{"mcpServers": {"architect": {"command": "python", "args": ["-m", "src.architect.mcp_server"], "env": {"DATABASE_PATH": "./data/architect.db", "CONTRACT_ENGINE_URL": "http://localhost:8002"}}, "contract-engine": {"command": "python", "args": ["-m", "src.contract_engine.mcp_server"], "env": {"DATABASE_PATH": "./data/contracts.db"}}, "codebase-intelligence": {"command": "python", "args": ["-m", "src.codebase_intelligence.mcp_server"], "env": {"DATABASE_PATH": "./data/symbols.db", "CHROMA_PATH": "./data/chroma", "GRAPH_PATH": "./data/graph.json"}}}}` (review_cycles: 0)
- [ ] INT-006: Create per-service config.py files (src/architect/config.py, src/contract_engine/config.py, src/codebase_intelligence/config.py) that import and re-export their corresponding config class from src/shared/config.py for local convenience (review_cycles: 0)

---

## Milestone 2: Architect Service

PRD decomposition engine — parses PRD text to extract entities, identifies service boundaries using a deterministic algorithm, generates OpenAPI/AsyncAPI contract stubs, builds domain model, validates decomposition (no cycles, no overlap, completeness). Full FastAPI endpoints.

### Functional Requirements

- [ ] REQ-013: Implement src/architect/services/prd_parser.py — parse_prd(prd_text: str) function that extracts entities, relationships, bounded contexts, and technology hints from free-form PRD text using the following deterministic algorithms. Entity extraction: scan for capitalized nouns following these patterns: (a) Markdown header content (## Users, ## Orders), (b) bold text (**User**, **Order**), (c) items in lists after keywords "entities:", "models:", "data:", "manages:", "stores:", (d) nouns in "manages X", "stores X", "creates X", "tracks X" patterns. Relationship extraction: scan for verb phrases connecting two extracted entities: "X has many Y" -> (X, HAS_MANY, Y), "X belongs to Y" -> (X, BELONGS_TO, Y), "X triggers Y" -> (X, TRIGGERS, Y), "X extends Y" -> (X, EXTENDS, Y), "X depends on Y" -> (X, DEPENDS_ON, Y), "X references Y" -> (X, REFERENCES, Y). Bounded context grouping: entities that appear in the same markdown section (## heading) are grouped into the same bounded context. Technology hints: scan for known technology names from a predefined list: ["React", "Angular", "Vue", "FastAPI", "Express", "Django", "PostgreSQL", "MongoDB", "Redis", "Kafka", "RabbitMQ", "GraphQL", "REST", "gRPC", "TypeScript", "Python", "Go", "C#"]. Return structured data with entity names, relationship types, context groupings, and detected technologies. Use regex patterns and string matching, not LLM calls — this must be deterministic and fast (review_cycles: 0)
- [ ] REQ-014: Implement src/architect/services/service_boundary.py — identify_boundaries(entities, relationships, contexts) function that groups entities into service boundaries using the following algorithm: (1) Each bounded context (from prd_parser) becomes an initial service candidate. (2) Within each context, the entity with the most outgoing relationships is the aggregate root. (3) Entities referenced by only one service remain in that service. (4) Entities referenced by 2+ services are assigned to the service where they appear as an aggregate root. If no aggregate root claim, assign to the service with the most relationships (edges) to the entity. (5) Cross-boundary relationships (entity in service A references entity in service B) become contract points — the providing service exposes an API, the consuming service calls it. Return list of ServiceDefinition instances with populated owns_entities and provides_contracts/consumes_contracts (review_cycles: 0)
- [ ] REQ-015: Implement src/architect/services/contract_generator.py — generate_contract_stubs(service_definitions: list[ServiceDefinition]) function that creates OpenAPI 3.1 spec dicts for HTTP API contracts between services. Each stub includes paths for CRUD operations on owned entities, request/response schemas derived from entity fields, standard error responses: 400 with `{"detail": "message"}`, 404 with `{"detail": "message"}`, 422 with `{"detail": [{"loc": ["string"], "msg": "string", "type": "string"}]}` (Pydantic validation format), 500 with `{"detail": "message"}`. Return list of dict specs ready for Contract Engine registration (review_cycles: 0)
- [ ] REQ-016: Implement src/architect/services/domain_modeler.py — build_domain_model(entities, relationships, service_definitions) function that constructs DomainModel with all entities as DomainEntity instances, all relationships as DomainRelationship instances with cardinality, state machines for entities with lifecycle states. An entity has a state machine if: (1) its fields include a field named "status", "state", or "phase", OR (2) the PRD text contains phrases like "X can be Y or Z" where X is the entity name and Y/Z are state names. States are the enum values of the status field. Transitions are inferred from verb phrases: "submitted for review" -> (submitted, under_review, submit). The domain model is the ubiquitous language — names must be consistent across all services (review_cycles: 0)
- [ ] REQ-017: Implement src/architect/services/validator.py — validate_decomposition(service_map: ServiceMap, domain_model: DomainModel) function that checks: (1) no circular service dependencies using NetworkX DiGraph and nx.is_directed_acyclic_graph(), (2) no entity ownership overlap (each entity owned by exactly one service), (3) entity completeness (all PRD entities accounted for), (4) contract completeness (all cross-boundary relationships have a contract). Return list of validation issue strings, empty if valid (review_cycles: 0)
- [ ] REQ-018: Implement src/architect/storage/service_map_store.py — ServiceMapStore class with save(service_map, prd_hash), get_latest(project_name), get_by_prd_hash(prd_hash) methods using ConnectionPool. Persist ServiceMap as JSON in service_maps table. Generate UUID for service_map id using str(uuid.uuid4()) (review_cycles: 0)
- [ ] REQ-019: Implement src/architect/storage/domain_model_store.py — DomainModelStore class with save(domain_model, project_name), get_latest(project_name) methods using ConnectionPool. Persist DomainModel as JSON in domain_models table (review_cycles: 0)
- [ ] REQ-020: Implement POST /api/decompose endpoint in src/architect/routers/decomposition.py — the endpoint MUST be `async def` to support async HTTP calls to Contract Engine. Accepts DecomposeRequest (prd_text) as request body, orchestrates the full pipeline (parse -> boundaries -> validate -> contracts -> domain model -> persist), returns DecompositionResult. Records the decomposition run in decomposition_runs table. Returns 201 on successful decomposition, 422 if validation fails with issues. All synchronous calls (prd_parser.parse_prd, service_boundary.identify_boundaries, validator.validate_decomposition, ServiceMapStore.save, DomainModelStore.save) MUST be wrapped in `asyncio.to_thread()` to prevent blocking the event loop — only the httpx.AsyncClient call to Contract Engine should be awaited directly (review_cycles: 0)
- [ ] REQ-021: Implement GET /api/service-map endpoint in src/architect/routers/service_map.py — returns the most recent ServiceMap for the project. Returns 404 if no service map exists (review_cycles: 0)
- [ ] REQ-022: Implement GET /api/domain-model endpoint in src/architect/routers/domain_model.py — returns the most recent DomainModel. Returns 404 if no domain model exists (review_cycles: 0)
- [ ] REQ-023: Create sample PRD in sample_data/sample_prd.md — a realistic multi-service e-commerce application PRD with User, Order, Product, Payment, and Notification entities across 3 services, 2 state machines (Order lifecycle: pending->paid->shipped->delivered, Payment lifecycle: initiated->completed->refunded), event-driven communication (payment completed triggers order status change), cross-service relationships. Must include at least 5 entities, at least 2 services, at least 1 state machine, at least 1 event-driven channel (review_cycles: 0)
- [ ] REQ-024: Create expected output in sample_data/sample_service_map.yaml — the expected ServiceMap YAML from decomposing sample_prd.md, used for validation testing. Must match the entities and services defined in REQ-023's sample PRD (review_cycles: 0)

### Technical Requirements

- [ ] TECH-006: src/architect/services/validator.py must use NetworkX DiGraph for cycle detection — build directed graph of service dependencies, use nx.is_directed_acyclic_graph(G), report cycles via nx.simple_cycles(G) (review_cycles: 0)
- [ ] TECH-007: Contract stubs must be valid OpenAPI 3.1 — use openapi_version: "3.1.0" in info, include components/schemas with full property definitions, include standard error response schemas (review_cycles: 0)
- [ ] TECH-008: All service files in src/architect/services/ must be pure functions with no global state — accept dependencies as parameters, return results, raise exceptions on error. No module-level mutable variables (lists, dicts, sets). Constants (ALL_CAPS) are allowed (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-004: src/architect/main.py must include routers from routers/decomposition.py, routers/service_map.py, routers/domain_model.py, routers/health.py with prefix /api and appropriate tags (review_cycles: 0)
- [ ] WIRE-005: src/architect/main.py lifespan must initialize ConnectionPool with ArchitectConfig.database_path, call init_architect_db(), store db in app.state.db (review_cycles: 0)
- [ ] WIRE-006: src/architect/routers/decomposition.py must use FastAPI Depends() to inject ServiceMapStore, DomainModelStore, and validator from the service layer (review_cycles: 0)

### Service-to-API Wiring Map

| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|
| SVC-001 | N/A (internal) | decompose() | POST | /api/decompose | DecomposeRequest { prd_text: string } | DecompositionResult { service_map: ServiceMap, domain_model: DomainModel, contract_stubs: list, validation_issues: list, interview_questions: list } |
| SVC-002 | N/A (internal) | get_service_map() | GET | /api/service-map | None | ServiceMap { project_name: string, services: list, generated_at: string, prd_hash: string } |
| SVC-003 | N/A (internal) | get_domain_model() | GET | /api/domain-model | None | DomainModel { entities: list, relationships: list, generated_at: string } |
| SVC-004 | N/A (internal) | health() | GET | /api/health | None | HealthStatus { status: string, service_name: string, version: string, database: string, uptime_seconds: number } |

### Test Requirements

- [ ] TEST-005: tests/test_architect/test_prd_parser.py — test entity extraction from 3+ different PRD formats (markdown lists, prose, structured headers), test relationship extraction (verify "X has many Y" produces correct tuple), test bounded context identification (entities under same heading grouped together), test technology hint detection — minimum 15 test cases (review_cycles: 0)
- [ ] TEST-006: tests/test_architect/test_service_boundary.py — test that non-overlapping service boundaries are produced, test with 3-entity trivial case and 10-entity complex case, test entity ownership is exclusive, test that cross-boundary references become contract points — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-007: tests/test_architect/test_contract_generator.py — test generated OpenAPI stubs are valid (pass openapi-spec-validator validation), test CRUD paths are generated for each service, test schemas match entity fields, test error response schemas are included — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-008: tests/test_architect/test_domain_modeler.py — test all entities appear in domain model, test relationships have valid cardinality, test state machines have valid transitions (no orphan states), test state machine detection from "status" field — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-009: tests/test_architect/test_validator.py — test circular dependency detection (plant a cycle, verify it is caught), test entity overlap detection, test completeness check (remove an entity, verify it is flagged), test contract completeness — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-010: tests/test_architect/test_routers.py — integration tests with FastAPI TestClient for all 4 endpoints — POST /api/decompose with sample PRD returns 201, GET /api/service-map returns 200 or 404, GET /api/domain-model returns 200 or 404, GET /api/health returns 200 (review_cycles: 0)

---

## Milestone 3: Contract Engine Core

Contract CRUD, OpenAPI 3.1 validation, custom AsyncAPI 3.0 parser (~500 lines) and validator, semantic versioning with immutability enforcement within build cycles, breaking change detection between versions, schema registry, implementation tracking.

### Functional Requirements

- [ ] REQ-025: Implement src/contract_engine/services/contract_store.py — ContractStore class with: upsert(contract_create: ContractCreate) using SHA-256 hash-based change detection (compute hash of json.dumps(spec, sort_keys=True).encode()), get(contract_id) returning ContractEntry or None, list(service_name filter, contract_type filter, page: int = 1, page_size: int = 20 max 100) returning tuple of items and total, delete(contract_id) returning bool, has_changed(service_name, type, version, new_spec) returning bool. Use INSERT ON CONFLICT for upserts. All methods use ConnectionPool (review_cycles: 0)
- [ ] REQ-026: Implement src/contract_engine/services/openapi_validator.py — validate_openapi(spec: dict) function using openapi-spec-validator validate() and prance ResolvingParser for $ref resolution. Return ValidationResult with specific error messages. Support OpenAPI 3.0.x and 3.1.0. Use OpenAPIV31SpecValidator for detailed error iteration (review_cycles: 0)
- [ ] REQ-027: Implement src/contract_engine/services/asyncapi_parser.py — ~500 line custom parser using pyyaml. Dataclasses: AsyncAPIMessage (name, content_type, payload_schema, headers_schema), AsyncAPIChannel (address, description, messages dict), AsyncAPIOperation (action send/receive, channel_ref, summary, message_refs), AsyncAPISpec (title, version, channels, operations, schemas). Functions: parse_asyncapi(spec_path_or_dict) parses YAML, resolves $ref references, returns AsyncAPISpec. Validate asyncapi version starts with "3.". Supported $ref patterns (resolve in order): (1) #/components/schemas/{name} -> look up in components.schemas, (2) #/components/messages/{name} -> look up in components.messages, (3) #/channels/{name} -> look up in channels, (4) #/channels/{name}/messages/{msgName} -> look up channel then its messages. Nested $refs: resolve one level deep (a message payload $ref to a schema). Circular $refs: detect and raise ParsingError. Parse channels with their messages, operations with channel refs and message refs, component schemas (review_cycles: 0)
- [ ] REQ-028: Implement src/contract_engine/services/asyncapi_validator.py — validate_asyncapi(spec: AsyncAPISpec) function that checks: title and version present, all channels have address and at least one message, all operations have valid action (send/receive) and channel reference, all schemas have type field, all message payload schemas are valid JSON Schema. Return list of error strings, empty if valid. Use jsonschema for payload schema validation (review_cycles: 0)
- [ ] REQ-029: Implement src/contract_engine/services/schema_registry.py — SchemaRegistry class for managing shared JSON schemas across services. Methods: register_schema(name, schema_dict, owning_service), get_schema(name) returning SharedSchema, list_schemas(owning_service filter), get_consumers(schema_name) returning list of service names, add_consumer(schema_name, service_name). Use contracts.db shared_schemas and schema_consumers tables for persistence (review_cycles: 0)
- [ ] REQ-030: Implement src/contract_engine/services/version_manager.py — VersionManager class enforcing immutability: check_immutability(contract_id, build_cycle_id) raises ImmutabilityViolationError if a contract already exists with the same build_cycle_id. Methods: create_version(contract_id, version, spec_hash, build_cycle_id, is_breaking) records in contract_versions table, get_version_history(contract_id) returns list of ContractVersion (review_cycles: 0)
- [ ] REQ-031: Implement src/contract_engine/services/breaking_change_detector.py — detect_breaking_changes(old_spec: dict, new_spec: dict) function that deep-diffs two OpenAPI specs and classifies changes: removed_field (error), type_change (error), removed_endpoint (error), added_required_field (error), changed_status_code (warning), removed_optional_field (info). Return list of BreakingChange instances. Compare paths, methods, schemas, required fields (review_cycles: 0)
- [ ] REQ-032: Implement src/contract_engine/services/implementation_tracker.py — ImplementationTracker class with: mark_implemented(contract_id, service_name, evidence_path) upserts into implementations table with status pending, verify_implementation(contract_id, service_name) updates status to verified, get_unimplemented(service_name filter) returns contracts with no implementation or status != verified using LEFT JOIN (review_cycles: 0)
- [ ] REQ-033: Implement CRUD endpoints in src/contract_engine/routers/contracts.py — POST / (create, returns 201), GET / (list with pagination page=1, page_size=20 defaults and filters), GET /{contract_id} (returns 200 or 404), DELETE /{contract_id} (returns 204 or 404). Validate spec before storing based on contract type: for `openapi`, call `openapi_validator.validate_openapi(spec)`; for `asyncapi`, first parse via `asyncapi_parser.parse_asyncapi(spec)` to obtain an `AsyncAPISpec`, then validate via `asyncapi_validator.validate_asyncapi(parsed_spec)`; for `json_schema`, validate using `jsonschema.Draft202012Validator.check_schema(spec)` — return `ValidationResult(valid=True)` on success, `ValidationResult(valid=False, errors=[str(e)])` on `jsonschema.SchemaError`. Before validation and storage, check `len(json.dumps(contract_create.spec).encode('utf-8')) <= 5_242_880`. Return 413 Payload Too Large if exceeded (review_cycles: 0)
- [ ] REQ-034: Implement validation endpoint in src/contract_engine/routers/validation.py — POST /api/validate accepts ValidateRequest (spec dict and contract type), returns ValidationResult (review_cycles: 0)
- [ ] REQ-035: Implement breaking changes endpoint in src/contract_engine/routers/breaking_changes.py — POST /api/breaking-changes/{contract_id} accepts new_spec dict as request body, returns list of BreakingChange (review_cycles: 0)
- [ ] REQ-036: Implement implementation endpoints in src/contract_engine/routers/implementations.py — POST /api/implementations/mark accepts MarkRequest, returns MarkResponse; GET /api/implementations/unimplemented (get_unimplemented with optional service_name query filter) returns list of UnimplementedContract (review_cycles: 0)
- [ ] REQ-037: Create sample_data/sample_openapi.yaml — a valid OpenAPI 3.1 spec for a User Service with GET /users, POST /users, GET /users/{userId}, PUT /users/{userId}, DELETE /users/{userId} endpoints, User and UserCreate component schemas with proper types and required fields. Must pass openapi-spec-validator validation (review_cycles: 0)
- [ ] REQ-038: Create sample_data/sample_asyncapi.yaml — a valid AsyncAPI 3.0 spec with user.events channel, UserCreated/UserUpdated/UserDeleted messages, send and receive operations, component schemas with EventHeaders, UserCreatedPayload, UserUpdatedPayload, UserDeletedPayload. Must pass the custom asyncapi_validator (review_cycles: 0)

### Technical Requirements

- [ ] TECH-009: Hash-based change detection — use hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest() to detect spec changes without full deep comparison (review_cycles: 0)
- [ ] TECH-010: Immutability enforcement — once a contract is stored with a specific build_cycle_id, any update attempt with the same build_cycle_id must be rejected with ImmutabilityViolationError. New versions require a new build_cycle_id (review_cycles: 0)
- [ ] TECH-011: AsyncAPI parser must handle local $ref resolution for #/components/messages/*, #/components/schemas/*, #/channels/*, and #/channels/*/messages/* patterns — extract the final path segment as the reference name, look up in the parsed components dict. Resolve nested $refs one level deep. Detect and raise ParsingError on circular $refs (review_cycles: 0)
- [ ] TECH-012: Contract store must use UNIQUE(service_name, type, version) constraint and INSERT ON CONFLICT DO UPDATE for upserts — never create duplicate contracts for the same service+type+version (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-007: src/contract_engine/main.py must include routers from contracts.py, validation.py, tests.py, implementations.py, breaking_changes.py, health.py with appropriate prefixes (/api/contracts, /api/validate, /api/tests, /api/implementations, /api/breaking-changes, /api) (review_cycles: 0)
- [ ] WIRE-008: src/contract_engine/main.py lifespan must initialize ConnectionPool with ContractEngineConfig.database_path, call init_contracts_db(), store db in app.state.db (review_cycles: 0)
- [ ] WIRE-009: src/contract_engine/routers/contracts.py must validate spec type before storing — for OpenAPI contracts, call `openapi_validator.validate_openapi(spec)`. For AsyncAPI contracts, first parse via `asyncapi_parser.parse_asyncapi(spec)` to obtain an `AsyncAPISpec`, then validate via `asyncapi_validator.validate_asyncapi(parsed_spec)`. For `json_schema` type, validate using `jsonschema.Draft202012Validator.check_schema(spec)` (schema meta-validation). Return `ValidationResult(valid=True)` on success, `ValidationResult(valid=False, errors=[str(e)])` on `jsonschema.SchemaError` (review_cycles: 0)

### Service-to-API Wiring Map

| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |
|---|---|---|---|---|---|---|
| SVC-005 | N/A (internal) | create_contract() | POST | /api/contracts | ContractCreate { service_name: string, type: string, version: string, spec: dict, build_cycle_id: string } | ContractEntry { id: string, type: string, version: string, service_name: string, spec_hash: string, status: string, created_at: string } |
| SVC-006 | N/A (internal) | list_contracts() | GET | /api/contracts | QueryParams { service_name: string, type: string, page: integer, page_size: integer } | ContractListResponse { items: list, total: integer, page: integer, page_size: integer } |
| SVC-007 | N/A (internal) | get_contract() | GET | /api/contracts/{contract_id} | PathParam { contract_id: string } | ContractEntry { id: string, type: string, version: string, service_name: string, spec: dict, spec_hash: string, status: string } |
| SVC-008 | N/A (internal) | delete_contract() | DELETE | /api/contracts/{contract_id} | PathParam { contract_id: string } | None (204) |
| SVC-009 | N/A (internal) | validate_spec() | POST | /api/validate | ValidateRequest { spec: dict, type: string } | ValidationResult { valid: boolean, errors: list, warnings: list } |
| SVC-010 | N/A (internal) | check_breaking() | POST | /api/breaking-changes/{contract_id} | BreakingChangeRequest { contract_id: string, new_spec: dict } | list of BreakingChange { change_type: string, path: string, old_value: string, new_value: string, severity: string } |
| SVC-011 | N/A (internal) | mark_implemented() | POST | /api/implementations/mark | MarkRequest { contract_id: string, service_name: string, evidence_path: string } | MarkResponse { marked: boolean, total_implementations: integer, all_implemented: boolean } |
| SVC-012 | N/A (internal) | get_unimplemented() | GET | /api/implementations/unimplemented | QueryParam { service_name: string } | list of UnimplementedContract { id: string, type: string, version: string, expected_service: string, status: string } |

### Test Requirements

- [ ] TEST-011: tests/test_contract_engine/test_contract_store.py — test CRUD operations (create, read, list, delete), test hash-based change detection (same spec produces same hash, different spec produces different hash), test upsert (update existing contract), test pagination (page=1 page_size=20 defaults, max 100), test service_name filter — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-012: tests/test_contract_engine/test_openapi_validator.py — test valid OpenAPI 3.1 spec passes, test invalid spec fails with specific errors (missing info, missing paths, invalid schema type), test $ref resolution with prance — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-013: tests/test_contract_engine/test_asyncapi_parser.py — test parsing sample_asyncapi.yaml produces correct AsyncAPISpec, test channel extraction (address, messages), test operation extraction (action, channel_ref), test schema extraction, test $ref resolution for #/components/messages/*, #/components/schemas/*, #/channels/*, test rejection of non-3.x version, test circular $ref raises ParsingError — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-014: tests/test_contract_engine/test_asyncapi_validator.py — test valid spec passes, test missing title fails, test missing channel address fails, test invalid operation action fails, test empty channel messages fails — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-015: tests/test_contract_engine/test_version_manager.py — test create_version succeeds, test immutability rejection (same build_cycle_id), test version history retrieval, test different build_cycle_id succeeds — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-016: tests/test_contract_engine/test_breaking_change_detector.py — test detect removed_field, test detect type_change, test detect removed_endpoint, test detect added_required_field, test non-breaking change (added optional field) produces no error — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-017: tests/test_contract_engine/test_implementation_tracker.py — test mark_implemented creates record, test get_unimplemented returns contracts without implementation, test verify_implementation updates status — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-018: tests/test_contract_engine/test_routers.py — integration tests with FastAPI TestClient for all endpoints — POST /api/contracts with valid OpenAPI spec returns 201, POST with invalid spec returns 422, GET /api/contracts returns paginated list, GET /api/contracts/{id} returns 200 or 404, DELETE returns 204 or 404, POST /api/breaking-changes/{id} returns breaking changes list — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-040: tests/test_contract_engine/test_schema_registry.py — test register_schema stores and retrieves a schema, test list_schemas with owning_service filter, test get_consumers returns correct service list, test add_consumer updates consumer list, test duplicate registration updates existing schema — minimum 8 test cases (review_cycles: 0)

---

## Milestone 4: Contract Test Generation

Schemathesis integration for generating runnable conformance tests from OpenAPI contracts, compliance checker for validating actual API responses against contracted schemas.

### Functional Requirements

- [ ] REQ-039: Implement src/contract_engine/services/test_generator.py — TestGenerator class with generate_tests(contract_id, framework="pytest", include_negative=True) method. For OpenAPI contracts: generate a complete pytest test file using the following template structure: `import schemathesis; BASE_URL = "http://localhost:{port}"; schema = schemathesis.openapi.from_path("{spec_path}", base_url=BASE_URL); @schema.parametrize() def test_{service_name}_conformance(case): case.call_and_validate()`. Include negative test cases when include_negative=True: tests with invalid inputs that should return 4xx. For AsyncAPI contracts: generate schema validation tests using jsonschema.validate() against message payload schemas. Return ContractTestSuite with complete runnable test_code string and test_count. Persist generated suites in test_suites table — subsequent calls with same contract_id and unchanged spec_hash return cached version (review_cycles: 0)
- [ ] REQ-040: Implement src/contract_engine/services/compliance_checker.py — ComplianceChecker class with check_compliance(contract_id, endpoint_path, method, response_body, status_code=200) method. Load the OpenAPI contract, resolve the path+method to an operation using the resolved (no $ref) schema from prance. Compare response_body fields against the contracted response schema for the given status_code. Compare all top-level required fields. For nested objects, recursively check required fields up to 3 levels deep. For arrays, check the items schema type. Report field-level violations: missing required field (error), wrong type (error with expected vs actual), extra field (allowed — APIs may return extra data). Return ComplianceResult with list of ComplianceViolation instances (review_cycles: 0)
- [ ] REQ-041: Add test generation endpoints to src/contract_engine/routers/tests.py — POST /api/tests/generate/{contract_id} accepts framework and include_negative parameters, returns ContractTestSuite. GET /api/tests/{contract_id} retrieves previously generated test suite from test_suites table (review_cycles: 0)

### Technical Requirements

- [ ] TECH-013: Generated test code must be valid Python that can be imported — include proper imports (schemathesis, pytest), use @schema.parametrize() for OpenAPI tests, use jsonschema.validate() for AsyncAPI schema tests. Generated code must reference a configurable BASE_URL variable (review_cycles: 0)
- [ ] TECH-014: Schemathesis integration must use schemathesis.openapi.from_path() for local spec files and schemathesis.openapi.from_url() for remote specs — include case.call_and_validate() for automatic schema+status code checking (review_cycles: 0)
- [ ] TECH-015: Compliance checker must handle missing fields (report as error), extra fields (ignore — APIs may return extra data), wrong types (report as error with expected vs actual) (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-010: src/contract_engine/routers/tests.py must use Depends() to inject ContractStore (for loading contracts) and TestGenerator (for test generation) (review_cycles: 0)
- [ ] WIRE-011: Test generator must persist generated test suites in test_suites table and return the suite — subsequent calls with same contract_id can return cached version if spec_hash unchanged (review_cycles: 0)

### Test Requirements

- [ ] TEST-019: tests/test_contract_engine/test_test_generator.py — test generated test code is valid Python (compile with ast.parse()), test generated code contains schemathesis imports and @schema.parametrize(), test test_count matches number of test functions, test AsyncAPI generates jsonschema validation tests, test include_negative=False excludes negative cases — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-020: tests/test_contract_engine/test_compliance_checker.py — test compliant response passes, test missing required field is caught, test wrong field type is caught, test extra field is allowed, test non-existent contract returns error, test nested object field validation — minimum 8 test cases (review_cycles: 0)

---

## Milestone 5: Codebase Intelligence Layers 1 and 2

Tree-sitter AST parsing for 4 languages (Python, TypeScript, C#, Go), symbol extraction, import path resolution, NetworkX dependency graph construction, PageRank analysis, circular dependency detection, dead code detection, SQLite persistence.

**Cross-milestone dependency:** The IncrementalIndexer (REQ-055) references SemanticIndexer.index_symbols() which is implemented in M6 (REQ-052). During M5 implementation, stub this call with a no-op that logs "SemanticIndexer not yet available — skipping semantic indexing." The stub is replaced when M6 is implemented.

### Functional Requirements

- [ ] REQ-042: Implement src/codebase_intelligence/services/ast_parser.py — ASTParser class with parse_file(file_path: Path) method. Detect language from file extension (.py=python, .ts/.tsx=typescript, .cs=csharp, .go=go). Load appropriate tree-sitter grammar via Language(tree_sitter_xxx.language()) — note: TypeScript uses language_typescript() and language_tsx() instead of language(), see TECH-017. Create Parser(language) and parse file content as bytes. Return tree-sitter Tree object. Handle parse errors gracefully — return partial tree with error nodes noted (review_cycles: 0)
- [ ] REQ-043: Implement src/codebase_intelligence/services/symbol_extractor.py — SymbolExtractor class with extract_symbols(tree, source_bytes, file_path, language) method. Import Query and QueryCursor from tree_sitter (`from tree_sitter import Query, QueryCursor`). Use tree-sitter Query with language-specific patterns to extract all symbol definitions. Use `QueryCursor(query)` to execute queries — `cursor.captures(root_node)` returns `dict[str, list[Node]]` where keys are capture names. Note: This API requires tree-sitter >= 0.25.0 (pinned in tech stack as 0.25.2). The captures() return type changed from list[tuple] to dict[str, list[Node]] in 0.25.0, and QueryCursor was introduced in 0.25.0 (previously captures/matches were methods on Query). Return list of SymbolDefinition instances with accurate line numbers (start_point[0] + 1 for 1-indexed), symbol names (node.text.decode()), kinds (class, function, interface, type, enum, variable, method), signatures, docstrings, export status. Delegate to language-specific parsers in parsers/ directory (review_cycles: 0)
- [ ] REQ-044: Implement language-specific parsers in src/codebase_intelligence/parsers/ — python_parser.py: Query for class_definition, function_definition, decorated definitions (@property, @staticmethod), extract name, parameters, docstring, parent class. typescript_parser.py: Query for interface_declaration, type_alias_declaration, export_statement with function_declaration and lexical_declaration, extract name, type parameters, export status. Use language_typescript() for .ts and language_tsx() for .tsx. csharp_parser.py: Query for class_declaration, interface_declaration, method_declaration, extract name, modifiers (public/private), namespace. go_parser.py: Query for function_declaration, type_declaration, method_declaration, extract name, receiver type, package. Tree-sitter grammar node types for C#: class_declaration, interface_declaration, method_declaration, namespace_declaration. For Go: function_declaration, type_declaration, method_declaration (review_cycles: 0)
- [ ] REQ-045: Implement src/codebase_intelligence/services/import_resolver.py — ImportResolver class with resolve_imports(tree, source_bytes, file_path, language, project_root) method. Extract import statements from AST, resolve import paths to actual file paths on disk. Handle: Python relative imports (from . import x), Python absolute imports (from package.module import x), TypeScript relative imports (import from './module'), TypeScript path aliases — read tsconfig.json compilerOptions.paths if present, map @/ to src/ by default, map ~/ to src/ by default, for custom paths resolve the first matching pattern, if tsconfig.json not found only handle relative imports and @/ -> src/ alias. Return list of ImportReference instances with resolved target_file paths using pathlib.Path (review_cycles: 0)
- [ ] REQ-046: Implement src/codebase_intelligence/services/graph_builder.py — GraphBuilder class with build_graph(symbols: list[SymbolDefinition], imports: list[ImportReference]) method. Create NetworkX DiGraph with file paths as nodes (with language, loc attributes). Add edges for imports (relation="imports"), function calls (relation="calls"), class inheritance (relation="inherits"), interface implementation (relation="implements"). Provide add_file(file_path, symbols, imports) for incremental graph updates. Return nx.DiGraph (review_cycles: 0)
- [ ] REQ-047: Implement src/codebase_intelligence/services/graph_analyzer.py — GraphAnalyzer class with: analyze(graph: nx.DiGraph) returning GraphAnalysis with node_count, edge_count, is_dag, circular_dependencies (nx.simple_cycles), top_files_by_pagerank (nx.pagerank with alpha=0.85), connected_components (nx.number_weakly_connected_components), build_order (nx.topological_sort if DAG). Also: get_dependencies(file_path) returning imports list (successors), imported_by list (predecessors), transitive_deps (nx.ancestors), circular_deps filtered to file. get_impact(symbol_id) returning nx.descendants for impact analysis (review_cycles: 0)
- [ ] REQ-048: Implement src/codebase_intelligence/services/dead_code_detector.py — DeadCodeDetector class with find_dead_code(graph, symbols, service_name filter) method. Find all symbols with in_degree==0 in the dependency graph (no incoming edges means never called/imported). Filter out known entry points: __init__, __main__, main(), route handlers (@app.get, @router.post, etc.), test functions (test_*), and explicit lifecycle methods: FastAPI (lifespan, on_event), Pydantic (model_validator, field_validator), Python dunder (__init__, __new__, __del__, __str__, __repr__, __enter__, __exit__, __aenter__, __aexit__), CLI (main, cli, app). Classify confidence: high (unexported function), medium (exported function in non-entry file), low (class with no callers). Return list of DeadCodeEntry (review_cycles: 0)
- [ ] REQ-049: Implement src/codebase_intelligence/storage/symbol_db.py — SymbolDB class with: save_symbols(symbols: list[SymbolDefinition]) bulk inserts/updates, query_by_name(symbol_name, language filter) returns list, query_by_file(file_path) returns list, delete_by_file(file_path) for re-indexing. Use INSERT OR REPLACE for upserts on id primary key (review_cycles: 0)
- [ ] REQ-050: Implement src/codebase_intelligence/storage/graph_db.py — GraphDB class with: save_edges(edges: list[DependencyEdge]) bulk inserts, save_snapshot(graph: nx.DiGraph) serializes graph using nx.node_link_data(graph, edges="edges") as JSON into graph_snapshots table, load_snapshot() deserializes most recent snapshot using nx.node_link_graph(data, edges="edges"), delete_by_file(file_path) removes edges where source or target matches file (review_cycles: 0)
- [ ] REQ-051: Create sample_data/sample_codebase/ with Python and TypeScript files for testing — auth_service/auth.py (Python class with methods, imports, decorators), auth_service/models.py (Pydantic models), billing_service/billing.ts (TypeScript class with exported functions), billing_service/types.ts (TypeScript interfaces and type aliases). Each file should have 50-100 lines with realistic code patterns (review_cycles: 0)

### Technical Requirements

- [ ] TECH-016: tree-sitter node.text returns bytes — always use .decode() for string comparison. start_point is 0-indexed (row, column) — add 1 for human-readable line numbers (review_cycles: 0)
- [ ] TECH-017: TypeScript has TWO sub-languages: Language(tree_sitter_typescript.language_typescript()) for .ts files and Language(tree_sitter_typescript.language_tsx()) for .tsx files — ast_parser must select the correct one based on file extension (review_cycles: 0)
- [ ] TECH-018: NetworkX serialization must use edges="edges" parameter (not the deprecated default "links") — nx.node_link_data(G, edges="edges") and nx.node_link_graph(data, edges="edges") (review_cycles: 0)
- [ ] TECH-019: Check nx.is_directed_acyclic_graph(G) before calling nx.topological_sort(G) — topological_sort raises NetworkXUnfeasible if cycles exist (review_cycles: 0)
- [ ] TECH-020: Node IDs in NetworkX must be strings for JSON serialization — use file paths as node IDs, symbol IDs (file_path::symbol_name) as alternative for symbol-level graphs (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-012: src/codebase_intelligence/services/ast_parser.py must import and use language-specific parsers from src/codebase_intelligence/parsers/ based on detected language (review_cycles: 0)
- [ ] WIRE-013: src/codebase_intelligence/services/graph_builder.py must be used by both initial indexing (process all files) and incremental indexing (add_file method for single file updates) (review_cycles: 0)
- [ ] WIRE-014: src/codebase_intelligence/storage/graph_db.py must persist the NetworkX graph as JSON snapshot AND individual edges in dependency_edges table — the snapshot enables fast graph loading, the edges table enables SQL queries (review_cycles: 0)

### Test Requirements

- [ ] TEST-021: tests/test_codebase_intelligence/test_ast_parser.py — test parsing Python file produces tree with function_definition nodes, test parsing TypeScript file produces tree with interface_declaration nodes, test language detection from file extension, test error handling for unparseable files — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-022: tests/test_codebase_intelligence/test_symbol_extractor.py — test extraction of Python classes and functions with line numbers, test extraction of TypeScript interfaces and exported functions, test docstring extraction, test parent_symbol for methods inside classes — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-023: tests/test_codebase_intelligence/test_import_resolver.py — test Python relative imports, test Python absolute imports, test TypeScript relative imports, test path resolution against actual file system (using sample_codebase), test @/ alias resolution — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-024: tests/test_codebase_intelligence/test_graph_builder.py — test graph construction from symbols and imports, test node attributes (language, loc), test edge attributes (relation type), test incremental add_file — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-025: tests/test_codebase_intelligence/test_graph_analyzer.py — test PageRank produces sensible ranking (imported files rank higher), test cycle detection (plant a cycle, verify it is found), test topological sort on DAG, test get_dependencies returns correct imports/imported_by, test connected_components count — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-026: tests/test_codebase_intelligence/test_dead_code_detector.py — test planted dead function is found, test entry points (__init__, main, test_*) are excluded, test confidence classification (high for unexported, medium for exported), test lifecycle methods are excluded — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-027: tests/test_codebase_intelligence/test_language_parsers.py — test Python parser extracts classes, functions, decorators; test TypeScript parser extracts interfaces, types, exports; test C# parser extracts classes, interfaces, methods; test Go parser extracts functions, types, methods — minimum 5 test cases per language (review_cycles: 0)
- [ ] TEST-028: Performance test — index all files in sample_data/sample_codebase/ and verify total time is under 5 seconds (review_cycles: 0)

---

## Milestone 6: Codebase Intelligence Layer 3 and MCP Server

ChromaDB semantic search integration, MCP server with all 7 Codebase Intelligence tools via stdio transport, incremental indexing triggered by register_artifact, service interface extraction, FastAPI REST endpoints.

### Functional Requirements

- [ ] REQ-052: Implement src/codebase_intelligence/services/semantic_indexer.py — SemanticIndexer class with index_symbols(symbols: list[SymbolDefinition], file_path, source_content) method. Generate CodeChunk instances from each symbol (combine symbol signature + docstring + code body as document text). Add to ChromaDB collection using collection.add(ids, documents, metadatas). Metadata must include file_path, symbol_name, symbol_type, language, service_name, line_start, line_end. Handle upserts for re-indexing (delete existing chunks for file, then add new ones) (review_cycles: 0)
- [ ] REQ-053: Implement src/codebase_intelligence/services/semantic_searcher.py — SemanticSearcher class with search(query, language filter, service_name filter, n_results=10) method. Use ChromaDB collection.query(query_texts=[query], n_results, where filters, include=["metadatas", "documents", "distances"]). Convert results to list of SemanticSearchResult instances. Handle metadata filters: language uses where={"language": value}, service_name uses where={"service_name": value}, combined filters use $and operator (review_cycles: 0)
- [ ] REQ-054: Implement src/codebase_intelligence/storage/chroma_store.py — ChromaStore class wrapping ChromaDB PersistentClient. Methods: init(chroma_path) creates PersistentClient and get_or_create_collection("symbols", embedding_function=DefaultEmbeddingFunction(), configuration={"hnsw": {"space": "cosine"}}), add_chunks(chunks: list[CodeChunk]), query(query_text, n_results, where_filters), delete_by_file(file_path) using collection.delete(where={"file_path": file_path}), get_stats() returns collection.count(). Import DefaultEmbeddingFunction from chromadb.utils.embedding_functions (review_cycles: 0)
- [ ] REQ-055: Implement src/codebase_intelligence/services/incremental_indexer.py — IncrementalIndexer class orchestrating the full indexing pipeline for a single file. Method: index_file(file_path, service_name) detects language, parses with ast_parser, extracts symbols with symbol_extractor, resolves imports with import_resolver, updates graph via graph_builder.add_file(), saves symbols to symbol_db, saves edges to graph_db, indexes chunks to chroma_store via semantic_indexer. Return a plain dict (not a Pydantic model) with indexed=True/False, symbols_found: int, dependencies_found: int, errors: list[str] (review_cycles: 0)
- [ ] REQ-056: Implement src/codebase_intelligence/services/service_interface_extractor.py — ServiceInterfaceExtractor class with extract(service_name) method. Query symbol_db for all exported symbols in the service. Identify HTTP endpoints by looking for route decorator patterns per language: Python: @app.get, @app.post, @router.get, @router.post etc.; TypeScript: app.get(), router.get(), @Get(), @Post() (NestJS); C#: [HttpGet], [HttpPost], [Route("path")]; Go: http.HandleFunc, r.HandleFunc, mux.HandleFunc. Optional: For consistency with Build 3's regex-based approach, agents MAY use these regex patterns: Python/FastAPI: `@app\.(get|post|put|delete|patch)\(['"]([^'"]+)`, Express/Node: `router\.(get|post|put|delete|patch)\(['"]([^'"]+)`, Spring/Java: `@(Get|Post|Put|Delete|Patch)Mapping\(['"]?([^'"\)]+)`, .NET: `\[Http(Get|Post|Put|Delete|Patch)\(['"]?([^'"\]]+)`. Identify published/consumed events by looking for patterns: publish(), emit(), send_event(), subscribe(), on_event(). Return ServiceInterface instance (review_cycles: 0)
- [ ] REQ-057: Implement src/codebase_intelligence/mcp_server.py — MCPServer with name="Codebase Intelligence", instructions describing capabilities, version="1.0.0". Each MCP server creates its OWN ConnectionPool instance using the same database path as the corresponding FastAPI service. MCP servers do NOT import or share state with FastAPI apps — they are independent processes that access the same database files. Register 7 tools with @mcp.tool() decorator: find_definition(symbol, language) returning symbol location dict or None; find_callers(symbol, max_results=50) returning list of caller dicts; find_dependencies(file_path) returning imports/imported_by/transitive/circular dicts; search_semantic(query, language, service_name, n_results=10) returning list of result dicts; get_service_interface(service_name) returning interface dict; check_dead_code(service_name) returning list of dead code dicts; register_artifact(file_path, service_name) triggering incremental indexing and returning stats dict. Run with mcp.run(transport="stdio") (review_cycles: 0)
- [ ] REQ-058: Implement FastAPI endpoints in src/codebase_intelligence/routers/ — GET /api/symbols (query by name, language), GET /api/dependencies (query by file_path), POST /api/search (semantic search), POST /api/artifacts (register artifact), GET /api/dead-code (find dead code), GET /api/health (health check). Router prefixes: symbols.py -> /api/symbols, dependencies.py -> /api/dependencies, search.py -> /api/search, artifacts.py -> /api/artifacts, dead_code.py -> /api/dead-code, health.py -> /api (review_cycles: 0)

### Technical Requirements

- [ ] TECH-021: ChromaDB collection.query() returns nested lists — access results as results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0] for the first (and only) query (review_cycles: 0)
- [ ] TECH-022: ChromaDB IDs must be strings, unique within collection — use file_path::symbol_name format for symbol chunk IDs (review_cycles: 0)
- [ ] TECH-023: ChromaDB default embedding model (all-MiniLM-L6-v2) downloads ~80-100MB on first use (ONNX model + tokenizer files) — Dockerfile must pre-download by running: RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; DefaultEmbeddingFunction()" (review_cycles: 0)
- [ ] TECH-024: MCP server must run with transport="stdio" for Claude Code integration — all tool functions must have type hints for proper JSON Schema generation, docstrings for tool descriptions. MCP servers are single-threaded (review_cycles: 0)
- [ ] TECH-025: Metadata filter operators in ChromaDB — equality: where={"language": "python"}, comparison: where={"line_count": {"$gt": 100}}, logical: where={"$and": [{"language": "python"}, {"service_name": "billing"}]}, in: where={"language": {"$in": ["python", "typescript"]}} (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-015: src/codebase_intelligence/mcp_server.py must import and use SemanticSearcher, SymbolDB, GraphAnalyzer, IncrementalIndexer, ServiceInterfaceExtractor, DeadCodeDetector from the services layer — MCP server is a thin adapter over the service layer (review_cycles: 0)
- [ ] WIRE-016: src/codebase_intelligence/main.py (FastAPI) must initialize ChromaStore, SymbolDB, GraphDB, and load existing NetworkX graph on startup via lifespan — store all in app.state for dependency injection (review_cycles: 0)
- [ ] WIRE-017: register_artifact MCP tool must trigger the full IncrementalIndexer.index_file() pipeline — parse, extract, resolve, graph, persist, embed (review_cycles: 0)
- [ ] WIRE-024: src/codebase_intelligence/main.py must include routers with prefixes: symbols.py -> /api/symbols, dependencies.py -> /api/dependencies, search.py -> /api/search, artifacts.py -> /api/artifacts, dead_code.py -> /api/dead-code, health.py -> /api (review_cycles: 0)

### Test Requirements

- [ ] TEST-029: tests/test_codebase_intelligence/test_semantic_indexer.py — test indexing a Python file creates ChromaDB entries with correct metadata, test re-indexing same file updates entries, test metadata includes all required fields (file_path, symbol_name, language, line_start, line_end) — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-030: tests/test_codebase_intelligence/test_semantic_searcher.py — test semantic search for "payment processing" returns billing-related code from sample_codebase, test language filter restricts results, test service_name filter restricts results, test n_results limits output count, test scores are between 0 and 1 — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-031: tests/test_codebase_intelligence/test_incremental_indexer.py — test index_file processes a new Python file and returns symbols_found > 0 and dependencies_found >= 0, test indexed file is immediately findable via find_definition, test re-indexing updates existing entries — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-032: tests/test_codebase_intelligence/test_mcp_tools.py — test each of the 7 MCP tools via MCP client (stdio_client + ClientSession): find_definition returns correct file and line, search_semantic returns relevant results, register_artifact indexes a file, find_callers returns call sites, find_dependencies returns import graph, check_dead_code returns unused symbols, get_service_interface returns endpoints and exports (review_cycles: 0)
- [ ] TEST-041: tests/test_codebase_intelligence/test_routers.py — integration tests with FastAPI TestClient for all 6 endpoints: GET /api/symbols returns symbols or empty list, GET /api/dependencies returns dependency info or 404, POST /api/search returns semantic results, POST /api/artifacts registers file and returns stats, GET /api/dead-code returns dead code list, GET /api/health returns 200 with HealthStatus — minimum 10 test cases (review_cycles: 0)

---

## Milestone 7: Architect MCP and Contract Engine MCP Servers

MCP servers for Architect (4 tools) and Contract Engine (9 tools), end-to-end tool testing across all 3 MCP servers.

### Functional Requirements

- [ ] REQ-059: Implement src/architect/mcp_server.py — MCPServer with name="Architect", instructions="Decompose PRDs and query the service decomposition, domain model, and contract assignments.", version="1.0.0". Each MCP server creates its OWN ConnectionPool instance using the same database path as the corresponding FastAPI service. Register 4 tools: decompose(prd_text: str) orchestrates the full decomposition pipeline (parse -> boundaries -> validate -> contracts -> domain model -> persist) and returns DecompositionResult dict — this is the same logic as POST /api/decompose but exposed as an MCP tool for Build 3 Super Orchestrator consumption; get_service_map() loads latest from architect.db service_maps table and returns full ServiceMap dict; get_contracts_for_service(service_name) queries service_maps for the named service, extracts provides_contracts and consumes_contracts, looks up each in Contract Engine via HTTP, returns list of dicts with id, role (provider/consumer), type, counterparty, summary; get_domain_model() loads latest from architect.db domain_models table and returns full DomainModel dict. Run with mcp.run(transport="stdio") (review_cycles: 0)
- [ ] REQ-060: Implement src/contract_engine/mcp_server.py — MCPServer with name="Contract Engine", instructions="Store, validate, query, and generate tests from OpenAPI/AsyncAPI contracts.", version="1.0.0". Each MCP server creates its OWN ConnectionPool instance. Register 9 tools: create_contract(service_name: str, type: str, version: str, spec: dict, build_cycle_id: str = "") creates a new contract, computes spec_hash, persists to contracts table, returns dict with contract id, status, spec_hash; validate_spec(spec: dict, type: str) validates an OpenAPI or AsyncAPI spec dict for structural correctness, returns dict with valid bool, errors list, warnings list; list_contracts(service_name: str = "", type: str = "", page: int = 1, page_size: int = 50) returns paginated list of contract dicts with optional service_name and type filters; get_contract(contract_id) returns full contract dict or None; validate_endpoint(service_name, method, path, response_body, status_code=200) validates response against contracted schema, returns dict with valid bool and violations list; generate_tests(contract_id, framework="pytest", include_negative=True) returns complete test file content string; check_breaking_changes(contract_id, new_spec) returns list of breaking change dicts; mark_implemented(contract_id, service_name, evidence_path) records implementation, returns dict with marked/total/all_implemented; get_unimplemented_contracts(service_name) returns list of unimplemented contract dicts. Run with mcp.run(transport="stdio") (review_cycles: 0)
- [ ] REQ-061: Create end-to-end MCP roundtrip test in tests/test_integration/test_mcp_roundtrip.py — Test setup: (1) initialize each service's database with schema, (2) seed architect.db with a sample service_map and domain_model via ServiceMapStore, (3) seed contracts.db with a sample contract via ContractStore, (4) seed symbols.db with sample symbols from sample_codebase/ via SymbolDB. Then start all 3 MCP servers as subprocesses, use MCP ClientSession to: (1) call Architect get_service_map, (2) call Contract Engine get_contract with an ID from the service map, (3) call Codebase Intelligence search_semantic for a concept related to the contract, (4) verify all responses are well-formed JSON with expected fields (review_cycles: 0)

### Technical Requirements

- [ ] TECH-026: Architect MCP get_contracts_for_service must use httpx.Client (sync) with timeout=httpx.Timeout(connect=5.0, read=30.0) to call Contract Engine's REST API at the configured CONTRACT_ENGINE_URL — this is inter-service communication, not direct DB access. The tool function MUST be defined as a regular `def` (not `async def`) since it uses sync httpx.Client — the MCP SDK automatically runs sync tool functions in a thread pool via anyio.to_thread.run_sync(), preventing event loop blocking (review_cycles: 0)
- [ ] TECH-027: All MCP tool functions must have complete type annotations and docstrings — the MCP SDK uses these to auto-generate tool JSON schemas that Claude Code uses for tool selection (review_cycles: 0)
- [ ] TECH-028: MCP servers must initialize database connections and service layer objects at module level or in a startup function — they run as long-lived processes serving tool calls. Each MCP server creates its OWN ConnectionPool instance. MCP servers do NOT import or share state with FastAPI apps (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-018: src/architect/mcp_server.py must import ServiceMapStore, DomainModelStore from storage layer and ArchitectConfig from config — initialize ConnectionPool with config.database_path (review_cycles: 0)
- [ ] WIRE-019: src/contract_engine/mcp_server.py must import ContractStore, ComplianceChecker, TestGenerator, BreakingChangeDetector, ImplementationTracker from services layer and ContractEngineConfig from config (review_cycles: 0)
- [ ] WIRE-020: .mcp.json must be updated with correct command paths for all 3 MCP servers — architect uses python -m src.architect.mcp_server, contract-engine uses python -m src.contract_engine.mcp_server, codebase-intelligence uses python -m src.codebase_intelligence.mcp_server (review_cycles: 0)

### Test Requirements

- [ ] TEST-033: tests/test_architect/test_mcp_tools.py — test decompose accepts prd_text and returns DecompositionResult dict with service_map and domain_model, test get_service_map returns valid ServiceMap dict after running decomposition, test get_contracts_for_service returns contracts list with role and counterparty fields, test get_domain_model returns entities and relationships (review_cycles: 0)
- [ ] TEST-034: tests/test_contract_engine/test_mcp_tools.py — test create_contract creates and returns contract with id and spec_hash, test validate_spec returns valid=true for correct spec and valid=false with errors for invalid spec, test list_contracts returns paginated results with optional filters, test get_contract returns contract with spec field, test validate_endpoint detects schema violation, test generate_tests returns valid Python test code, test check_breaking_changes detects removed field, test mark_implemented records implementation, test get_unimplemented_contracts returns gap list (review_cycles: 0)
- [ ] TEST-035: tests/test_integration/test_mcp_roundtrip.py — end-to-end test spanning all 3 MCP servers as described in REQ-061, including test data seeding (review_cycles: 0)

---

## Milestone 8: Integration, Docker, and End-to-End Tests

Full Docker Compose finalization with health checks and inter-service communication, end-to-end pipeline tests, documentation, sample data finalization.

### Functional Requirements

- [ ] REQ-062: Finalize docker-compose.yml — architect service on port 8001->8000, contract-engine on port 8002->8000, codebase-intel on port 8003->8000. Health checks using python urllib.request.urlopen('http://localhost:8000/api/health') with interval=10s, timeout=5s, retries=5, start_period=15s/10s/20s respectively. depends_on: architect depends on contract-engine (service_healthy), codebase-intel depends on contract-engine (service_healthy). Named volumes: architect-data, contract-data, intel-data mounted to /data. Bridge network: super-team-net. Restart: unless-stopped. Environment variables: DATABASE_PATH, CONTRACT_ENGINE_URL, CODEBASE_INTEL_URL, CHROMA_PATH, GRAPH_PATH, LOG_LEVEL (review_cycles: 0)
- [ ] REQ-063: Finalize Dockerfiles for all 3 services — python:3.12-slim base, WORKDIR /app, copy and install requirements.txt, copy application code (including src/shared/ per WIRE-023), mkdir /data, create non-root appuser with chown, USER appuser, EXPOSE 8000, CMD e.g. `["uvicorn", "src.architect.main:app", "--host", "0.0.0.0", "--port", "8000"]`. Codebase Intelligence Dockerfile must pre-download ChromaDB embedding model (review_cycles: 0)
- [ ] REQ-064: Implement inter-service communication — Architect service POST /api/decompose must register generated contract stubs with Contract Engine via HTTP POST to http://contract-engine:8000/api/contracts using httpx.AsyncClient. Verify registered contracts via GET response. Log registration results (review_cycles: 0)
- [ ] REQ-065: Create full E2E pipeline test in tests/test_integration/test_architect_to_contracts.py — decompose sample PRD via Architect API, verify contracts are registered in Contract Engine, verify service map is persisted, verify domain model is persisted. This test requires both services running (use Docker Compose or TestClient with mocked inter-service calls) (review_cycles: 0)
- [ ] REQ-066: Create codebase indexing E2E test in tests/test_integration/test_codebase_indexing.py — register all files in sample_data/sample_codebase/ via Codebase Intelligence API, verify symbols are queryable, verify semantic search returns results, verify dependency graph is built, verify dead code detection runs (review_cycles: 0)
- [ ] REQ-067: Create Docker Compose integration test in tests/test_integration/test_docker_compose.py — verify all 3 services start and health checks pass within 60 seconds, verify each service returns correct HealthStatus with service_name and version, verify inter-service connectivity (architect can reach contract-engine) (review_cycles: 0)
- [ ] REQ-068: Create docs/architecture.md — architecture overview with service descriptions, data flow diagrams in Mermaid syntax with service-to-service communication arrows, technology choices, database schemas (review_cycles: 0)
- [ ] REQ-069: Create docs/api_reference.md — combined API reference for all 3 services with all endpoints, request/response schemas, example requests and responses (review_cycles: 0)
- [ ] REQ-070: Create docs/mcp_tools.md — MCP tool documentation for Claude Code users with tool names, descriptions, parameter schemas, example usage, expected return values for all 20 tools across 3 servers (review_cycles: 0)
- [ ] REQ-071: Create docs/deployment.md — deployment guide covering Docker Compose setup, environment variables, volume management, health check monitoring, MCP server configuration in .mcp.json, development setup without Docker (review_cycles: 0)
- [ ] REQ-072: Finalize .mcp.json with tested and verified paths for all 3 MCP servers — include env vars for DATABASE_PATH, CHROMA_PATH, GRAPH_PATH, CONTRACT_ENGINE_URL (review_cycles: 0)
- [ ] REQ-073: Create README.md — project overview, quick start instructions (Docker Compose and local development), architecture diagram, link to documentation, technology stack summary, build status (review_cycles: 0)

### Technical Requirements

- [ ] TECH-029: Inter-service HTTP calls must use httpx.AsyncClient with appropriate timeouts (connect_timeout=5.0, read_timeout=30.0) and error handling (retry on ConnectionError, log on failure) (review_cycles: 0)
- [ ] TECH-030: Docker health checks must use python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" (not curl, which may not be installed in slim images) (review_cycles: 0)
- [ ] TECH-031: All services must log startup messages with service name, version, port, and database path — use structured JSON logging from shared/logging.py (review_cycles: 0)
- [ ] TECH-035: See "Architectural Principle: Async/Sync Boundary" (top-level section). Any sync function (SQLite queries, CPU-bound parsing, NetworkX analysis) called from an `async def` handler MUST be wrapped in `asyncio.to_thread()` to prevent event loop blocking. FastAPI runs `async def` handlers directly on the event loop thread — only `def` (sync) handlers are automatically run in a thread pool (review_cycles: 0)
- [ ] TECH-036: See "Architectural Principle: Async/Sync Boundary" (top-level section). ChromaDB operations (collection.add, collection.query, collection.delete) are synchronous. When called from async contexts (FastAPI async endpoints or async MCP tool functions), they MUST be wrapped in `asyncio.to_thread()` or the calling function must be defined as sync `def` — for MCP tools, the SDK runs sync tools in a thread pool automatically (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-021: src/architect/routers/decomposition.py must use httpx.AsyncClient to POST generated contract stubs to CONTRACT_ENGINE_URL/api/contracts after successful decomposition (review_cycles: 0)
- [ ] WIRE-022: docker-compose.yml service names must match the hostnames used in environment variables — contract-engine in CONTRACT_ENGINE_URL=http://contract-engine:8000, codebase-intel in CODEBASE_INTEL_URL=http://codebase-intel:8000 (review_cycles: 0)
- [ ] WIRE-023: Each service's Dockerfile must copy the src/shared/ package in addition to its own package — shared models and utilities must be available in all containers (review_cycles: 0)

### Test Requirements

- [ ] TEST-036: tests/test_integration/test_architect_to_contracts.py — E2E test: POST sample PRD to Architect, verify DecompositionResult contains service_map with services, verify contract stubs were registered in Contract Engine, verify service_map is retrievable via GET (review_cycles: 0)
- [ ] TEST-037: tests/test_integration/test_codebase_indexing.py — E2E test: register sample_codebase files, verify find_definition returns correct symbols, verify search_semantic returns relevant results, verify find_dependencies returns import relationships (review_cycles: 0)
- [ ] TEST-038: tests/test_integration/test_docker_compose.py — Docker Compose test: verify all services healthy within 60s, verify health endpoints return correct HealthStatus, verify architect can reach contract-engine (review_cycles: 0)
- [ ] TEST-039: tests/test_integration/test_mcp_roundtrip.py — end-to-end MCP test as described in REQ-061 (review_cycles: 0)

---

## Status Registry

| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|
| BuildCycle | status | running, completed, failed, paused | TEXT with CHECK | string |
| ContractEntry | status | active, deprecated, draft | TEXT with CHECK | string |
| ContractEntry | type | openapi, asyncapi, json_schema | TEXT with CHECK | string |
| ImplementationRecord | status | verified, pending, failed | TEXT with CHECK | string |
| DecompositionRun | status | pending, running, completed, failed, review | TEXT with CHECK | string |
| HealthStatus | status | healthy, degraded, unhealthy | N/A (computed) | string |
| HealthStatus | database | connected, disconnected | N/A (computed) | string |
| SymbolDefinition | kind | class, function, interface, type, enum, variable, method | TEXT with CHECK | string |
| SymbolDefinition | language | python, typescript, csharp, go | TEXT with CHECK | string |
| DependencyEdge | relation | imports, calls, inherits, implements, uses | TEXT with CHECK | string |
| DeadCodeEntry | confidence | high, medium, low | N/A (computed) | string |
| BreakingChange | severity | error, warning, info | TEXT | string |

## Architecture Decision

### Technology Stack

- Backend: Python 3.12+ with FastAPI 0.129.0
- Database: SQLite with WAL mode (3 separate .db files per service)
- Vector Search: ChromaDB 1.5.0 with cosine similarity
- Graph: NetworkX 3.6.1 for dependency graph analysis
- AST: tree-sitter 0.25.2 for multi-language parsing
- MCP: MCP Python SDK >=1.25,<2 for Claude Code integration
- Testing: Schemathesis 4.10.1 for contract conformance tests
- Container: Docker Compose with 3 services on bridge network

### File Structure

```
super-team/
  src/
    shared/          # Models, DB, config, logging, errors (used by all services)
    architect/       # System 1: PRD decomposition engine
    contract_engine/ # System 2: Contract registry + validation + test gen
    codebase_intelligence/ # System 3: Live codebase index via MCP
  tests/             # Unit + integration tests
  docker/            # Per-service Dockerfiles
  docs/              # Architecture, API, MCP, deployment docs
  sample_data/       # Test data for development
```

### Integration Roadmap

#### Entry Points

| Entry Point | File | Purpose |
|---|---|---|
| Architect API | src/architect/main.py | FastAPI app for PRD decomposition |
| Architect MCP | src/architect/mcp_server.py | MCP server with 4 tools |
| Contract Engine API | src/contract_engine/main.py | FastAPI app for contract management |
| Contract Engine MCP | src/contract_engine/mcp_server.py | MCP server with 9 tools |
| Codebase Intel API | src/codebase_intelligence/main.py | FastAPI app for REST access |
| Codebase Intel MCP | src/codebase_intelligence/mcp_server.py | MCP server with 7 tools (PRIMARY) |

#### Wiring Map

| ID | Source | Target | Mechanism | Priority |
|---|---|---|---|---|
| WIRE-001 | src/shared/models/__init__.py | All service packages | re-export all model classes | HIGH |
| WIRE-002 | src/shared/db/schema.py | src/shared/db/connection.py | import ConnectionPool | HIGH |
| WIRE-003 | All __init__.py files | Python import system | empty __init__.py files | HIGH |
| WIRE-004 | src/architect/main.py | src/architect/routers/*.py | app.include_router() | HIGH |
| WIRE-005 | src/architect/main.py lifespan | src/shared/db/* | ConnectionPool + init_architect_db | HIGH |
| WIRE-006 | src/architect/routers/decomposition.py | src/architect/services/* | FastAPI Depends() | HIGH |
| WIRE-007 | src/contract_engine/main.py | src/contract_engine/routers/*.py | app.include_router() | HIGH |
| WIRE-008 | src/contract_engine/main.py lifespan | src/shared/db/* | ConnectionPool + init_contracts_db | HIGH |
| WIRE-009 | src/contract_engine/routers/contracts.py | openapi/asyncapi validators | type-based routing | HIGH |
| WIRE-010 | src/contract_engine/routers/tests.py | services/test_generator.py | Depends() injection | MEDIUM |
| WIRE-011 | test_generator | test_suites table | cache generated suites | MEDIUM |
| WIRE-012 | src/codebase_intelligence/services/ast_parser.py | src/codebase_intelligence/parsers/*.py | language dispatch | HIGH |
| WIRE-013 | graph_builder | incremental_indexer | add_file() method | HIGH |
| WIRE-014 | graph_db | dependency_edges + graph_snapshots | dual persistence | HIGH |
| WIRE-015 | src/codebase_intelligence/mcp_server.py | services/*.py | service layer imports | HIGH |
| WIRE-016 | src/codebase_intelligence/main.py | ChromaStore + SymbolDB + GraphDB | lifespan init | HIGH |
| WIRE-017 | register_artifact MCP tool | IncrementalIndexer.index_file() | full pipeline | HIGH |
| WIRE-018 | src/architect/mcp_server.py | storage/*.py + config.py | direct imports | HIGH |
| WIRE-019 | src/contract_engine/mcp_server.py | services/*.py + config.py | direct imports | HIGH |
| WIRE-020 | .mcp.json | all 3 mcp_server.py files | python -m paths | HIGH |
| WIRE-021 | decomposition router | Contract Engine HTTP API | httpx.AsyncClient POST | HIGH |
| WIRE-022 | docker-compose.yml | service env vars | hostname=service name | HIGH |
| WIRE-023 | Dockerfiles | src/shared/ package | COPY src/shared | HIGH |
| WIRE-024 | src/codebase_intelligence/main.py | routers/*.py | router prefixes | HIGH |

#### Wiring Anti-Patterns

- Never import MCP SDK in service layer files — MCP concerns stay in mcp_server.py only
- Never access databases cross-service via direct SQLite connection — use HTTP APIs
- Never share SQLite database files between services — each service owns its .db file
- Never use global mutable state in service layer — pass dependencies as parameters
- Never hardcode service URLs — use environment variables loaded via Pydantic Settings

#### Initialization Order

1. Load configuration from environment variables (Pydantic Settings)
2. Initialize ConnectionPool with WAL mode
3. Run schema initialization (create tables if not exists)
4. Initialize ChromaDB PersistentClient (Codebase Intelligence only)
5. Load existing NetworkX graph snapshot (Codebase Intelligence only)
6. Register FastAPI routers
7. Start uvicorn server

## Review Log

| Cycle | Agent | Item | Verdict | Issues |
|---|---|---|---|---|
