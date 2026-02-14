# Build 1 PRD — Executability Review

## Summary
- Executability issues found: **47**
- Critical (agent will be blocked): **6**
- High (agent will make wrong assumption): **14**
- Medium (agent may produce suboptimal code): **17**
- Low (minor improvement): **10**

---

## Critical Issues

### EXEC-CRIT-001: PRD Parser Algorithm is Completely Unspecified
- **Requirement**: REQ-013
- **Problem**: "Use regex and NLP heuristics, not LLM calls — this must be deterministic and fast" provides zero implementation guidance. No regex patterns specified, no NLP library named, no extraction algorithm defined. The requirement says to extract "entities (nouns), relationships (verbs connecting entities), bounded contexts (groups of related entities), and technology hints" but gives no algorithm for any of these.
- **Impact**: The agent will invent an arbitrary algorithm. Two builds would produce completely different PRD parsers with different outputs, making downstream services (service_boundary, contract_generator) unpredictable.
- **Fix**: Add explicit specification:
  ```
  Entity extraction: Scan for capitalized nouns following patterns:
  - Markdown header content (## Users, ## Orders)
  - Bold text (**User**, **Order**)
  - Items in lists after "entities:", "models:", "data:"
  - Nouns in "manages X", "stores X", "creates X" patterns

  Relationship extraction: Scan for verb phrases connecting two extracted entities:
  - "X has many Y" → (X, HAS_MANY, Y)
  - "X belongs to Y" → (X, BELONGS_TO, Y)
  - "X triggers Y" → (X, TRIGGERS, Y)
  - "X extends Y" → (X, EXTENDS, Y)

  Bounded context grouping: Entities that appear in the same markdown section (## header)
  are grouped into the same bounded context.

  Technology hints: Scan for known framework/database names from a predefined list:
  ["React", "Angular", "Vue", "FastAPI", "Express", "Django", "PostgreSQL", "MongoDB",
   "Redis", "Kafka", "RabbitMQ", "GraphQL", "REST", "gRPC"]
  ```

### EXEC-CRIT-002: Service Boundary Algorithm Unspecified
- **Requirement**: REQ-014
- **Problem**: "groups entities into service boundaries using Domain-Driven Design principles: aggregate roots become service owners, shared entities get assigned to the service with strongest ownership" — there is no definition of "aggregate root detection", no metric for "strongest ownership", no algorithm for boundary identification. This is a design problem masquerading as a specification.
- **Impact**: Agent will produce arbitrary groupings. No way to validate correctness.
- **Fix**: Specify the algorithm:
  ```
  1. Each bounded context (from prd_parser) becomes an initial service candidate.
  2. Within each context, the entity with the most outgoing relationships is the aggregate root.
  3. Entities referenced by only one service remain in that service.
  4. Entities referenced by 2+ services are assigned to the service where they appear
     as an aggregate root. If no aggregate root claim, assign to the service with more
     relationships to the entity.
  5. Cross-boundary relationships (entity in service A references entity in service B)
     become contract points — the providing service exposes an API, the consuming service
     calls it.
  ```

### EXEC-CRIT-003: Database Schema Columns Not Defined for Architect and Symbols DBs
- **Requirement**: REQ-007
- **Problem**: REQ-007 says "init_architect_db() creates service_maps, domain_models, decomposition_runs tables with indexes" but does NOT specify the columns, types, constraints, or indexes for any of these 3 tables. Similarly, "init_symbols_db() creates indexed_files, symbols, dependency_edges, import_references, graph_snapshots tables" without column definitions. The contracts_db is slightly better (UNIQUE constraint mentioned) but still missing full column lists.
- **Impact**: Agent must invent table schemas. May not match what storage classes (REQ-018, REQ-019, REQ-049, REQ-050) expect.
- **Fix**: Add explicit CREATE TABLE statements for all tables. Example for architect_db:
  ```sql
  CREATE TABLE IF NOT EXISTS service_maps (
      id TEXT PRIMARY KEY,
      project_name TEXT NOT NULL,
      data_json TEXT NOT NULL,
      prd_hash TEXT NOT NULL,
      build_cycle_id TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_service_maps_project ON service_maps(project_name);
  CREATE INDEX IF NOT EXISTS idx_service_maps_prd_hash ON service_maps(prd_hash);

  CREATE TABLE IF NOT EXISTS domain_models (
      id TEXT PRIMARY KEY,
      project_name TEXT NOT NULL,
      data_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_domain_models_project ON domain_models(project_name);

  CREATE TABLE IF NOT EXISTS decomposition_runs (
      id TEXT PRIMARY KEY,
      project_name TEXT NOT NULL,
      prd_hash TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('pending','running','completed','failed','review')),
      service_map_id TEXT REFERENCES service_maps(id),
      domain_model_id TEXT REFERENCES domain_models(id),
      issues_json TEXT,
      started_at TEXT NOT NULL DEFAULT (datetime('now')),
      completed_at TEXT
  );
  ```
  Similar explicit schemas needed for: contracts_db (6 tables), symbols_db (5 tables).

### EXEC-CRIT-004: Missing Request/Response Pydantic Models
- **Requirement**: SVC-001, SVC-009, SVC-010, SVC-011, SVC-012
- **Problem**: The SVC wiring table references 5 Pydantic models that are NOT defined in any REQ:
  - `DecomposeRequest { prd_text: string }` (SVC-001)
  - `ValidateRequest { spec: dict, type: string }` (SVC-009)
  - `MarkRequest { contract_id: string, service_name: string, evidence_path: string }` (SVC-011)
  - `MarkResponse { marked: boolean, total_implementations: integer, all_implemented: boolean }` (SVC-011)
  - `UnimplementedContract { id: string, type: string, version: string, expected_service: string, status: string }` (SVC-012)
- **Impact**: Agent must invent these models. Field names, types, and validation rules may not match what the router endpoints expect.
- **Fix**: Add a new requirement (e.g., REQ-002b) defining each model with all fields, types, and validators. Or add them to the existing model files (architect.py, contracts.py) in REQ-002/REQ-003.

### EXEC-CRIT-005: Breaking Changes Endpoint Uses GET with Request Body
- **Requirement**: REQ-035, SVC-010
- **Problem**: "GET /api/breaking-changes/{contract_id} accepts new_spec as query/body" — GET requests with bodies are non-standard and many HTTP clients (including browsers and some proxies) strip or ignore GET bodies. The SVC-010 row says "PathParam+Body { contract_id: string, new_spec: dict }" which confirms a body, but dict-sized specs cannot fit in query parameters either.
- **Impact**: Agent may implement this as GET with body (fragile) or guess wrong about query vs body.
- **Fix**: Change to POST: `POST /api/breaking-changes/{contract_id}` with `new_spec: dict` in the request body. Update SVC-010 accordingly.

### EXEC-CRIT-006: SchemaRegistry Table Schema Missing
- **Requirement**: REQ-029
- **Problem**: SchemaRegistry "Use contracts.db for persistence" but REQ-007 does NOT include a shared_schemas table in the contracts_db initialization. The table columns, indexes, and constraints are completely undefined.
- **Impact**: Agent will either forget to create the table (runtime crash) or invent a schema that doesn't match the SchemaRegistry class expectations.
- **Fix**: Add to REQ-007's init_contracts_db():
  ```sql
  CREATE TABLE IF NOT EXISTS shared_schemas (
      name TEXT PRIMARY KEY,
      schema_json TEXT NOT NULL,
      owning_service TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS schema_consumers (
      schema_name TEXT NOT NULL REFERENCES shared_schemas(name) ON DELETE CASCADE,
      service_name TEXT NOT NULL,
      PRIMARY KEY (schema_name, service_name)
  );
  ```

---

## High Issues

### EXEC-HIGH-001: Domain Modeler State Machine Detection Unspecified
- **Requirement**: REQ-016
- **Problem**: "state machines for entities with lifecycle states" — no specification for how to detect which entities have lifecycle states. Is it keyword-based? Does the entity need a "status" field? Does the PRD text need to mention "states" explicitly?
- **Impact**: Agent will guess. May produce state machines for all entities or none.
- **Fix**: Specify: "An entity has a state machine if: (1) its fields include a field named 'status', 'state', or 'phase', OR (2) the PRD text contains phrases like 'X can be Y or Z' where X is the entity name and Y/Z are state names. States are the enum values of the status field. Transitions are inferred from verb phrases: 'submitted for review' → (submitted, under_review, submit)."

### EXEC-HIGH-002: Contract Generator Error Response Schema Undefined
- **Requirement**: REQ-015
- **Problem**: "standard error responses (400, 404, 422, 500)" — but no error response body schema is defined. FastAPI's default is `{"detail": "message"}` but the generated OpenAPI stubs need explicit error schemas.
- **Impact**: Generated stubs may have inconsistent error formats.
- **Fix**: Add to REQ-015: "Error response schema for all error codes: `{ detail: string }` for 400/404/500, `{ detail: [{ loc: list[string], msg: string, type: string }] }` for 422 (Pydantic validation errors)."

### EXEC-HIGH-003: Missing Default Values for Multiple Model Fields
- **Requirement**: REQ-002, REQ-003, REQ-004
- **Problem**: Several model fields lack explicit default values:
  - `ContractEntry.status` — should default to "draft" or "active"?
  - `ContractEntry.build_cycle_id` — optional? nullable? default None?
  - `SymbolDefinition.service_name` — marked "optional" but no explicit `= None`
  - `SymbolDefinition.parent_symbol` — marked "optional" but no explicit `= None`
  - `DecompositionResult.interview_questions` — type? list[str]? default?
  - `SharedSchema.consuming_services` — type? list[str]? default?
- **Impact**: Agent may choose wrong defaults, causing validation failures in tests.
- **Fix**: For every field marked "optional" in the PRD, add explicit `= None`. For enum fields with no default, specify the default value. E.g., "ContractEntry.status: ContractStatus = ContractStatus.DRAFT".

### EXEC-HIGH-004: DecompositionRun Model Missing
- **Requirement**: REQ-007, REQ-020
- **Problem**: REQ-020 says "Records the decomposition run in decomposition_runs table" and the Status Registry lists DecompositionRun statuses (pending, running, completed, failed, review), but there is NO Pydantic model defined for DecompositionRun in any REQ. The table exists (REQ-007) but the model doesn't.
- **Impact**: Agent will need to invent the model or skip it entirely.
- **Fix**: Add DecompositionRun model to REQ-002:
  ```
  DecompositionRun (id UUID, project_name, prd_hash, status pattern pending|running|completed|failed|review,
  service_map_id optional, domain_model_id optional, issues list[str] = [], started_at, completed_at optional)
  ```

### EXEC-HIGH-005: AsyncAPI Parser Missing Exact $ref Resolution Scope
- **Requirement**: REQ-027, TECH-011
- **Problem**: TECH-011 says "handle local $ref resolution for #/components/messages/* and #/components/schemas/* patterns" but doesn't specify what happens for: (1) $ref to #/channels/* (used in operations), (2) nested $ref (a message $ref contains a schema $ref), (3) circular $ref. The tech research provides a partial implementation but doesn't handle nested resolution.
- **Impact**: Parser may fail on valid AsyncAPI 3.0 specs with channel $refs in operations.
- **Fix**: Explicitly list all $ref patterns to resolve:
  ```
  Supported $ref patterns (resolve in order):
  1. #/components/schemas/{name} → look up in components.schemas
  2. #/components/messages/{name} → look up in components.messages
  3. #/channels/{name} → look up in channels
  4. #/channels/{name}/messages/{msgName} → look up channel, then its messages
  Nested $refs: resolve one level deep (a message payload $ref to a schema).
  Circular $refs: detect and raise ParsingError.
  ```

### EXEC-HIGH-006: ContractStore.list() Pagination Defaults Missing
- **Requirement**: REQ-025, REQ-033
- **Problem**: REQ-025 says `list(service_name filter, contract_type filter, page, page_size)` but no default values for page and page_size. REQ-033 says "list with pagination" but doesn't specify defaults.
- **Impact**: Agent will choose arbitrary defaults.
- **Fix**: Add: "page: int = 1, page_size: int = 20 (max 100)".

### EXEC-HIGH-007: Logging Implementation Unspecified
- **Requirement**: REQ-010
- **Problem**: "JSON-formatted logger with trace_id, service_name fields, configurable log level" — which Python logging approach? stdlib `logging` with a custom JSONFormatter? `structlog`? `loguru`? How is trace_id generated (uuid4 per request?) and propagated (middleware? context var?)?
- **Impact**: Agent will pick any approach. May not integrate well with FastAPI's logging.
- **Fix**: Specify: "Use stdlib `logging` module with a custom `JSONFormatter` class that outputs `{\"timestamp\": ..., \"level\": ..., \"service_name\": ..., \"trace_id\": ..., \"message\": ...}`. trace_id is generated as `str(uuid.uuid4())` per request using a FastAPI middleware that sets a `contextvars.ContextVar`. Log level is configurable via `LOG_LEVEL` env var."

### EXEC-HIGH-008: Exception Status Codes Not Explicitly Mapped
- **Requirement**: REQ-011
- **Problem**: "all extending a base AppError with status_code and detail properties" but individual exception status codes are not specified.
- **Impact**: Agent may assign wrong HTTP status codes.
- **Fix**: Explicitly map:
  ```
  AppError (base): status_code abstract
  ValidationError: status_code = 422
  NotFoundError: status_code = 404
  ConflictError: status_code = 409
  ImmutabilityViolationError: status_code = 409
  ParsingError: status_code = 400
  SchemaError: status_code = 422
  ContractNotFoundError: status_code = 404
  ```

### EXEC-HIGH-009: DeadCodeDetector Entry Point Filter Incomplete
- **Requirement**: REQ-048
- **Problem**: "Filter out known entry points: __init__, __main__, main(), route handlers (@app.get, @router.post), test functions (test_*), framework lifecycle methods" — "framework lifecycle methods" is undefined. Which methods? `setup()`, `teardown()`, `on_startup()`, `lifespan()`?
- **Impact**: Dead code detector may report false positives for framework lifecycle methods.
- **Fix**: Replace "framework lifecycle methods" with explicit list: "FastAPI lifecycle: lifespan, on_event. Pydantic: model_validator, field_validator. Python: __init__, __new__, __del__, __str__, __repr__, __enter__, __exit__, __aenter__, __aexit__. CLI: main, cli, app."

### EXEC-HIGH-010: MCP Server Database Initialization Pattern Unclear
- **Requirement**: TECH-028, REQ-057, REQ-059, REQ-060
- **Problem**: TECH-028 says "MCP servers must initialize database connections and service layer objects at module level or in a startup function" but MCP servers run via `mcp.run(transport="stdio")` which is blocking. Module-level initialization would happen before run(). But should the MCP servers share the same database files as the FastAPI services? Same ConnectionPool instance?
- **Impact**: Agent may create separate database connections that conflict with FastAPI service connections, or may try to import FastAPI app state (which won't exist in MCP context).
- **Fix**: Specify: "Each MCP server creates its OWN ConnectionPool instance using the same database path as the corresponding FastAPI service. MCP servers do NOT import or share state with FastAPI apps. They are independent processes that access the same database files."

### EXEC-HIGH-011: E2E MCP Roundtrip Test Data Seeding Not Specified
- **Requirement**: REQ-061, TEST-035
- **Problem**: "start all 3 MCP servers as subprocesses, use MCP ClientSession to: (1) call Architect get_service_map" — but get_service_map requires data to exist in the database. How is test data seeded? Does the test first call decompose? Or pre-populate the database?
- **Impact**: Test will fail because there's no data to query.
- **Fix**: Specify the test setup: "Before MCP roundtrip tests: (1) initialize each service's database with schema, (2) seed architect.db with a sample service_map and domain_model via direct SQL or ServiceMapStore, (3) seed contracts.db with a sample contract, (4) seed symbols.db with sample symbols from sample_codebase/."

### EXEC-HIGH-012: Import Resolver TypeScript Path Alias Handling Incomplete
- **Requirement**: REQ-045
- **Problem**: "Handle: TypeScript path aliases (@/ prefix)" — only @/ is mentioned. What about ~/ prefix? What about tsconfig.json paths mapping (e.g., "@components/*": ["src/components/*"])? Does the resolver read tsconfig.json?
- **Impact**: TypeScript imports with custom path aliases will fail to resolve.
- **Fix**: Specify: "Read tsconfig.json compilerOptions.paths if present. Map @/ to src/ by default. Map ~/ to src/ by default. For custom paths, resolve the first matching pattern. If tsconfig.json is not found, only handle relative imports and @/ → src/ alias."

### EXEC-HIGH-013: config.yaml for the Project Not Defined
- **Requirement**: Project structure shows `config.yaml` at root
- **Problem**: The project structure lists `config.yaml` at the super-team root but no REQ defines what goes in it. Is it the agent-team config.yaml? A project-specific config? Service configuration?
- **Impact**: Agent may skip creating it or create an empty file.
- **Fix**: Either remove it from the project structure or specify: "config.yaml is an optional agent-team configuration file for the build system. It is not used by the application services at runtime. Create as an empty YAML file with a comment: `# Agent team configuration — not used by application services`."

### EXEC-HIGH-014: Sample Data Files Content Not Specified
- **Requirement**: REQ-023, REQ-024, REQ-037, REQ-038, REQ-051
- **Problem**: REQ-023 says "a realistic multi-service application PRD" without exact content. REQ-024 says "expected output" from decomposing REQ-023's PRD. REQ-037 says "valid OpenAPI 3.1 spec for a User Service". REQ-038 says "valid AsyncAPI 3.0 spec". These are interrelated — REQ-024 must match REQ-023's output, and REQ-037/038 must be consistent with the sample service architecture. Without exact content, the agent will produce sample data that may not exercise all features.
- **Impact**: Tests relying on sample data may not cover edge cases. REQ-024's "expected output" will be whatever the agent decides.
- **Fix**: Either provide exact sample content in the PRD, or change the requirement to: "Generate sample data that includes: at least 5 entities with cross-service relationships, at least 2 services, at least 1 state machine, at least 1 event-driven channel. Verify sample_openapi.yaml passes openapi-spec-validator. Verify sample_asyncapi.yaml passes the custom asyncapi_validator."

---

## Medium Issues

### EXEC-MED-001: ComplianceChecker Comparison Depth Unspecified
- **Requirement**: REQ-040
- **Problem**: "compare response_body fields against the contracted response schema" — how deep? Top-level only? Nested objects? Arrays of objects? What about $ref in the schema?
- **Fix**: Add: "Compare all top-level required fields. For nested objects, recursively check required fields up to 3 levels deep. For arrays, check the items schema type. Use the resolved (no $ref) schema from prance."

### EXEC-MED-002: ServiceInterfaceExtractor Limited to Python Patterns
- **Requirement**: REQ-056
- **Problem**: "Identify HTTP endpoints by looking for route decorator patterns (@app.get, @router.post)" — only Python FastAPI patterns. No TypeScript Express patterns (app.get(), router.get()), no C# attributes ([HttpGet], [Route]), no Go patterns (http.HandleFunc).
- **Fix**: Add patterns for each supported language:
  ```
  Python: @app.get, @app.post, @router.get, @router.post, etc.
  TypeScript: app.get(), router.get(), @Get(), @Post() (NestJS)
  C#: [HttpGet], [HttpPost], [Route("path")]
  Go: http.HandleFunc, r.HandleFunc, mux.HandleFunc
  ```

### EXEC-MED-003: SymbolDefinition.id Format Needs Validation
- **Requirement**: REQ-004
- **Problem**: `SymbolDefinition.id` is defined as "file_path::symbol_name" — but this format is not enforced by a Pydantic validator. If the symbol_name contains "::", the ID becomes ambiguous.
- **Fix**: Add a model_validator or pattern constraint: `id: str = Field(..., pattern=r'^.+::[^:]+$')`. Or generate the ID in a @model_validator(mode='before') from file_path and symbol_name.

### EXEC-MED-004: ChromaDB Embedding Function Parameter Missing from REQ-054
- **Requirement**: REQ-054
- **Problem**: REQ-054 says `get_or_create_collection("symbols", configuration={"hnsw": {"space": "cosine"}})` but does NOT pass `embedding_function=DefaultEmbeddingFunction()`. The tech research shows this parameter is needed.
- **Fix**: Add to REQ-054: `embedding_function=DefaultEmbeddingFunction()` in the get_or_create_collection call.

### EXEC-MED-005: UUID Generation Method Not Specified
- **Requirement**: REQ-018, REQ-025
- **Problem**: REQ-018 says "Generate UUID for service_map id" and REQ-025 implies UUID for contract IDs, but the UUID generation method (uuid4?) and module (import uuid?) are not specified.
- **Fix**: Add to TECH requirements: "All UUIDs must be generated using `str(uuid.uuid4())` from the stdlib `uuid` module."

### EXEC-MED-006: IncrementalIndexer Return Type Ambiguous
- **Requirement**: REQ-055
- **Problem**: "Return dict with indexed=True/False, symbols_found, dependencies_found, errors list" — should this be a Pydantic model (IndexResult) or a plain dict? The PRD inconsistently uses both patterns (models for entities, dicts for return values).
- **Fix**: Either define an IndexResult Pydantic model or explicitly state: "Return a plain dict (not a Pydantic model)."

### EXEC-MED-007: Test Generator Template Structure Missing
- **Requirement**: REQ-039
- **Problem**: "generate a complete pytest test file using schemathesis.openapi.from_path()" — but the exact template structure (imports, base_url variable, test function names, class structure) is not specified.
- **Fix**: Provide a template:
  ```python
  # Template for generated test files:
  import schemathesis

  BASE_URL = "http://localhost:{port}"
  schema = schemathesis.openapi.from_path("{spec_path}", base_url=BASE_URL)

  @schema.parametrize()
  def test_{service_name}_conformance(case):
      case.call_and_validate()

  # Negative tests (if include_negative=True):
  @schema.parametrize(endpoint="/{path}", method="{method}")
  def test_{operation_id}_invalid_input(case):
      ...
  ```

### EXEC-MED-008: Decompose Endpoint HTTP Status Code Ambiguous
- **Requirement**: REQ-020
- **Problem**: "Returns 422 if validation fails with issues" — but what about the success case? SVC-001 doesn't specify the success status code. Should be 200 or 201?
- **Fix**: Add: "Returns 201 on successful decomposition, 422 if validation fails with issues."

### EXEC-MED-009: graph_snapshots Table Schema Missing
- **Requirement**: REQ-050, REQ-007
- **Problem**: REQ-050 references "graph_snapshots table" and REQ-007 lists it in init_symbols_db(), but no column definition is provided.
- **Fix**: Add:
  ```sql
  CREATE TABLE IF NOT EXISTS graph_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      data_json TEXT NOT NULL,
      node_count INTEGER NOT NULL DEFAULT 0,
      edge_count INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  ```

### EXEC-MED-010: test_suites Table Schema Missing
- **Requirement**: REQ-039, REQ-041, WIRE-011
- **Problem**: WIRE-011 says "persist generated test suites in test_suites table" and REQ-007 lists it in init_contracts_db(), but no column definition is provided.
- **Fix**: Add:
  ```sql
  CREATE TABLE IF NOT EXISTS test_suites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_id TEXT NOT NULL REFERENCES contracts(id),
      framework TEXT NOT NULL DEFAULT 'pytest',
      test_code TEXT NOT NULL,
      test_count INTEGER NOT NULL DEFAULT 0,
      spec_hash TEXT NOT NULL,
      generated_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE(contract_id, framework)
  );
  ```

### EXEC-MED-011: indexed_files Table Schema Missing
- **Requirement**: REQ-007
- **Problem**: REQ-007 mentions "indexed_files" in init_symbols_db() but no column definition.
- **Fix**: Add:
  ```sql
  CREATE TABLE IF NOT EXISTS indexed_files (
      file_path TEXT PRIMARY KEY,
      language TEXT NOT NULL,
      service_name TEXT,
      file_hash TEXT,
      symbols_count INTEGER NOT NULL DEFAULT 0,
      indexed_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  ```

### EXEC-MED-012: import_references Table Schema Missing
- **Requirement**: REQ-007
- **Problem**: REQ-007 mentions "import_references" in init_symbols_db() but no column definition.
- **Fix**: Add:
  ```sql
  CREATE TABLE IF NOT EXISTS import_references (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_file TEXT NOT NULL,
      target_file TEXT NOT NULL,
      imported_names_json TEXT NOT NULL,
      line INTEGER NOT NULL,
      is_relative INTEGER NOT NULL DEFAULT 0,
      UNIQUE(source_file, target_file, line)
  );
  CREATE INDEX IF NOT EXISTS idx_imports_source ON import_references(source_file);
  CREATE INDEX IF NOT EXISTS idx_imports_target ON import_references(target_file);
  ```

### EXEC-MED-013: Inter-Service Communication Sync/Async Mismatch
- **Requirement**: REQ-064, WIRE-021
- **Problem**: REQ-064 says "httpx.AsyncClient" for inter-service calls, and TECH-029 specifies timeouts. But the decomposition endpoint (REQ-020) is defined in a FastAPI router — if the endpoint function is `async def`, httpx.AsyncClient works. If it's `def`, it doesn't. REQ-020 doesn't specify async.
- **Fix**: Add to REQ-020: "The decompose endpoint MUST be `async def` to support async HTTP calls to Contract Engine."

### EXEC-MED-014: Maximum Input Size Not Specified
- **Requirement**: REQ-020, REQ-025
- **Problem**: POST /api/decompose accepts PRD text with no size limit. ContractCreate.spec is a dict with no size limit. An agent or user could send enormous payloads.
- **Fix**: Add to TECH requirements: "PRD text input: max 1MB. Contract spec dict: max 5MB after JSON serialization. Reject with 413 Payload Too Large."

### EXEC-MED-015: SQL Parameterization Not Explicitly Required
- **Requirement**: Global
- **Problem**: No TECH requirement explicitly mandates parameterized SQL queries. While the tech research examples use parameterized queries, the PRD should enforce this as a security requirement.
- **Fix**: Add TECH requirement: "All SQL queries MUST use parameterized queries (? placeholders). Never use string formatting or f-strings to build SQL. This prevents SQL injection."

### EXEC-MED-016: Tree-Sitter Query Patterns Not Specified for C# and Go
- **Requirement**: REQ-044
- **Problem**: REQ-044 lists query targets for each language but not the exact tree-sitter S-expression query strings. For Python and TypeScript, the tech research provides working examples. For C# and Go, there are no examples.
- **Fix**: Either provide the exact query strings or specify: "Refer to tree-sitter grammar node types for each language: C# uses class_declaration, interface_declaration, method_declaration, namespace_declaration. Go uses function_declaration, type_declaration, method_declaration."

### EXEC-MED-017: HealthStatus Model Missing service_name Default
- **Requirement**: REQ-005, INT-001
- **Problem**: HealthStatus requires service_name but INT-001 says each FastAPI app returns HealthStatus. Each service needs to know its own name. How? Hardcoded? From config?
- **Fix**: Add: "service_name is loaded from the service's config class (ArchitectConfig, ContractEngineConfig, CodebaseIntelConfig) or hardcoded as a constant in each service's main.py."

---

## Low Issues

### EXEC-LOW-001: ContractEntry.spec_hash Generation Not Cross-Referenced
- **Requirement**: REQ-003, TECH-009
- **Problem**: REQ-003 defines ContractEntry with spec_hash field. TECH-009 specifies the hash algorithm. But REQ-003 doesn't mention that spec_hash is auto-computed — the agent might make it a required input.
- **Fix**: Add to REQ-003: "spec_hash is auto-computed on creation using TECH-009 algorithm, not provided by the caller."

### EXEC-LOW-002: Dockerfile CMD Path Inconsistency
- **Requirement**: INT-003, REQ-063
- **Problem**: INT-003 says "CMD uvicorn" but the module path would be `src.architect.main:app` (if the COPY includes the full src/ directory) or `main:app` (if only the service package is copied). WIRE-023 says "copy src/shared/ in addition to its own package" which suggests COPY src/ approach.
- **Fix**: Specify exact CMD: `CMD ["uvicorn", "src.architect.main:app", "--host", "0.0.0.0", "--port", "8000"]` (adjust per service).

### EXEC-LOW-003: .mcp.json env var Names Not Fully Specified
- **Requirement**: INT-005, WIRE-020
- **Problem**: INT-005 says "each with appropriate env vars" but doesn't list which env vars each MCP server needs.
- **Fix**: Specify:
  ```json
  {
    "mcpServers": {
      "architect": {
        "command": "python", "args": ["-m", "src.architect.mcp_server"],
        "env": {"DATABASE_PATH": "./data/architect.db", "CONTRACT_ENGINE_URL": "http://localhost:8002"}
      },
      "contract-engine": {
        "command": "python", "args": ["-m", "src.contract_engine.mcp_server"],
        "env": {"DATABASE_PATH": "./data/contracts.db"}
      },
      "codebase-intelligence": {
        "command": "python", "args": ["-m", "src.codebase_intelligence.mcp_server"],
        "env": {"DATABASE_PATH": "./data/symbols.db", "CHROMA_PATH": "./data/chroma", "GRAPH_PATH": "./data/graph.json"}
      }
    }
  }
  ```

### EXEC-LOW-004: BreakingChange Severity Values Inconsistent with Pattern
- **Requirement**: REQ-003
- **Problem**: REQ-003 defines `BreakingChange.severity` with `pattern error|warning|info` (regex). REQ-031 maps specific changes to severities. These are consistent but the severity should be an enum for type safety rather than a pattern-validated string.
- **Fix**: Consider making severity a `BreakingSeverity` enum (similar to other enums in the codebase) instead of a pattern string.

### EXEC-LOW-005: HealthStatus.details Type Ambiguous
- **Requirement**: REQ-005
- **Problem**: `HealthStatus.details: dict` — what keys? What values? Is it free-form?
- **Fix**: Add: "details: dict[str, Any] = Field(default_factory=dict) — free-form metadata for debugging, e.g., {'indexed_files': 1234, 'graph_nodes': 567}."

### EXEC-LOW-006: Test Count Minimums Should Be Per-Test-File
- **Requirement**: TEST-001 through TEST-039
- **Problem**: Some test requirements specify minimums (TEST-001: "minimum 50 test cases", TEST-005: "minimum 15 test cases") but others don't (TEST-006 through TEST-009 just say "test X, test Y"). Inconsistent.
- **Fix**: Add minimum test case counts to all TEST requirements that lack them. E.g., TEST-006: "minimum 8 test cases", TEST-007: "minimum 10 test cases".

### EXEC-LOW-007: ContractCreate.build_cycle_id Field Missing
- **Requirement**: REQ-003, SVC-005
- **Problem**: REQ-003 defines ContractCreate with (service_name, type, version, spec) but SVC-005 shows `ContractCreate { ..., build_cycle_id: string }`. The build_cycle_id field is mentioned in ContractCreate's REQ-003 definition. Actually, re-reading REQ-003 more carefully, it does include build_cycle_id. This is consistent. No issue.
- **Fix**: N/A — this was a false positive on closer inspection.

### EXEC-LOW-007 (reassigned): review_cycles Suffix Clarification
- **Requirement**: All REQ/TECH/WIRE/TEST/INT
- **Problem**: Every requirement ends with "(review_cycles: 0)" which is an agent-team system field. The PRD should note that this suffix is required by the build system and should not be modified by the agent.
- **Fix**: Add a note at the top of the PRD: "Each requirement includes `(review_cycles: N)` — this is tracked by the build system. Agents must preserve this suffix when modifying requirements."

### EXEC-LOW-008: Codebase Intelligence Router Endpoint Paths Not Prefixed
- **Requirement**: REQ-058
- **Problem**: REQ-058 lists endpoints as "GET /api/symbols, POST /api/search, POST /api/artifacts" etc. but WIRE-016 doesn't specify router prefixes. Are these all under /api or do they have sub-prefixes like /api/symbols, /api/dependencies?
- **Fix**: Add to WIRE (or a new WIRE): "codebase_intelligence routers use prefixes: symbols.py → /api/symbols, dependencies.py → /api/dependencies, search.py → /api/search, artifacts.py → /api/artifacts, dead_code.py → /api/dead-code, health.py → /api."

### EXEC-LOW-009: Docker Network Name Inconsistency
- **Requirement**: INT-002, REQ-062
- **Problem**: INT-002 says "bridge network (super-team-net)" but the tech research docker-compose example uses "agent-network". The PRD should be authoritative — super-team-net is correct.
- **Fix**: No fix needed for PRD — just noting the tech research uses a different name. The agent should follow the PRD.

### EXEC-LOW-010: Missing __init__.py for tests/test_integration/
- **Requirement**: Project structure
- **Problem**: The project structure lists test_integration/ directory but doesn't explicitly list an __init__.py for it. All other test directories have __init__.py.
- **Fix**: Add `tests/test_integration/__init__.py` to the project structure.

---

## Ambiguity Inventory

| Requirement | Ambiguous Text | Suggested Replacement |
|---|---|---|
| REQ-013 | "Use regex and NLP heuristics" | Specify exact regex patterns and extraction algorithm (see EXEC-CRIT-001) |
| REQ-013 | "technology hints" | "Known technology names from a predefined list: [React, Angular, Vue, ...]" |
| REQ-013 | "bounded contexts (groups of related entities)" | "Entities in the same markdown section (## heading) form a bounded context" |
| REQ-014 | "Domain-Driven Design principles" | Specify the exact grouping algorithm (see EXEC-CRIT-002) |
| REQ-014 | "strongest ownership" | "The service with the most relationships (edges) to the entity" |
| REQ-016 | "entities with lifecycle states" | "Entities whose fields include a field named status, state, or phase" |
| REQ-023 | "a realistic multi-service application PRD" | "An e-commerce PRD with User, Order, Product, Payment, and Notification entities, 3 services, 2 state machines" |
| REQ-027 | "~500 line custom parser" | Remove line count estimate — it's misleading. Specify by functionality instead |
| REQ-035 | "query/body" | "request body (POST)" (see EXEC-CRIT-005) |
| REQ-040 | "compare response_body fields" | "Recursively compare required fields up to 3 levels deep" |
| REQ-048 | "framework lifecycle methods" | Explicit list of method names (see EXEC-HIGH-009) |
| REQ-056 | "publish/subscribe patterns" | "Function calls matching: publish(), emit(), send_event(), subscribe(), on_event()" |
| REQ-068 | "architecture overview with data flow diagrams" | "Architecture overview in Mermaid syntax with service-to-service communication arrows" |
| TECH-008 | "pure functions with no global state" | "Functions must accept all dependencies as parameters. No module-level mutable variables (lists, dicts, sets). Constants (ALL_CAPS) are allowed." |
| REQ-010 | "trace_id" | "trace_id: str generated as uuid4 per request via contextvars.ContextVar" |
| INT-002 | "health checks using python urllib.request.urlopen" | Exact health check command provided in REQ-062 — consistent |

---

## Missing Specifications Checklist

| Category | Item | Status |
|---|---|---|
| Error handling | HTTP client timeouts for MCP inter-service calls (TECH-026) | **MISSING** — only TECH-029 covers FastAPI inter-service calls |
| Security | SQL parameterized queries enforced | **MISSING** — add TECH requirement |
| Security | Input size limits (PRD text, spec dicts) | **MISSING** — add TECH requirement |
| Performance | Batch size for bulk SQLite inserts | **MISSING** — specify in REQ-049 |
| Performance | ChromaDB max batch size (41,666 docs) | **MISSING** — add note to REQ-052 |
| Reliability | Graceful shutdown behavior for FastAPI apps | SPECIFIED (lifespan context manager) |
| Logging | What events to log and at what level | **PARTIALLY SPECIFIED** — only startup messages (TECH-031) |
| Validation | Max size for PRD text input | **MISSING** |
| Validation | Max size for contract spec dict | **MISSING** |
| Threading | MCP server single-threaded assumption | **MISSING** — add note to TECH-024 |
| Database | Exact CREATE TABLE for architect_db tables | **MISSING** (see EXEC-CRIT-003) |
| Database | Exact CREATE TABLE for symbols_db tables | **MISSING** (see EXEC-CRIT-003) |
| Database | shared_schemas table for SchemaRegistry | **MISSING** (see EXEC-CRIT-006) |
| Database | test_suites table schema | **MISSING** (see EXEC-MED-010) |
| Database | graph_snapshots table schema | **MISSING** (see EXEC-MED-009) |
| Database | indexed_files table schema | **MISSING** (see EXEC-MED-011) |
| Database | import_references table schema | **MISSING** (see EXEC-MED-012) |
| Models | DecomposeRequest Pydantic model | **MISSING** (see EXEC-CRIT-004) |
| Models | ValidateRequest Pydantic model | **MISSING** (see EXEC-CRIT-004) |
| Models | MarkRequest/MarkResponse models | **MISSING** (see EXEC-CRIT-004) |
| Models | UnimplementedContract model | **MISSING** (see EXEC-CRIT-004) |
| Models | DecompositionRun model | **MISSING** (see EXEC-HIGH-004) |
| Models | Default values for optional fields | **PARTIALLY SPECIFIED** (see EXEC-HIGH-003) |
| UUID | Generation method (uuid4) | **MISSING** (see EXEC-MED-005) |
| Testing | MCP roundtrip test data seeding | **MISSING** (see EXEC-HIGH-011) |
| Docker | Exact CMD uvicorn module paths | **PARTIALLY SPECIFIED** (see EXEC-LOW-002) |
| Docker | .mcp.json complete env var listings | **PARTIALLY SPECIFIED** (see EXEC-LOW-003) |

---

## Cross-Reference Consistency Check

| Check | Status | Notes |
|---|---|---|
| SVC table field names match model definitions | **3 ISSUES** | DecomposeRequest, ValidateRequest, MarkRequest/Response not defined |
| Endpoint paths in SVC tables match REQ descriptions | OK | All paths consistent |
| Test file paths match project structure | OK | All test files listed in structure |
| WIRE source/target files exist in structure | OK | All files accounted for |
| Status Registry values match model enum definitions | OK | All values consistent |
| ContractCreate fields match SVC-005 columns | OK | All 5 fields present |
| HealthStatus model fields match health endpoint responses | OK | Consistent |
| Database table names match storage class expectations | **1 ISSUE** | shared_schemas table missing |
| Config class field names match env var names | OK | All aliases correct |
| MCP tool names match service layer method names | OK | Consistent |

---

*Executability review completed by executability-reviewer agent. Total: 6 CRITICAL, 14 HIGH, 17 MEDIUM, 10 LOW issues identified across 73 requirements.*
