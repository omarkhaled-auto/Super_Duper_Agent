# BUILD1_PRD Fix Changelog

All changes applied from 4 review documents: Format, Technology, Architecture, and Executability reviews.

---

## CRITICAL Fixes (8)

### 1. EXEC-CRIT-001: PRD Parser Algorithm Specified (REQ-013)
- **Before**: "Use regex and NLP heuristics, not LLM calls"
- **After**: Full deterministic algorithm specification — entity extraction via capitalized nouns in headers/bold/lists/verb patterns, relationship extraction via "X has many Y" patterns with 6 verb templates, bounded context grouping via markdown sections, technology hints from predefined list of 18 technologies

### 2. EXEC-CRIT-002: Service Boundary Algorithm Specified (REQ-014)
- **Before**: "groups entities into service boundaries using Domain-Driven Design principles"
- **After**: 5-step concrete algorithm: (1) bounded contexts become service candidates, (2) entity with most outgoing relationships is aggregate root, (3) single-reference entities stay, (4) multi-reference entities assigned by aggregate root claim or most-edges metric, (5) cross-boundary relationships become contract points

### 3. EXEC-CRIT-003: Complete Database Schemas Added (REQ-007)
- **Before**: "init_architect_db() creates service_maps, domain_models, decomposition_runs tables with indexes" (no column definitions)
- **After**: Full CREATE TABLE SQL for ALL 14 tables across 3 databases — architect.db (3 tables), contracts.db (8 tables including shared_schemas + schema_consumers), symbols.db (5 tables) — with all columns, types, constraints, indexes, CHECK constraints, UNIQUE constraints, foreign keys. Sourced directly from Architecture Plan Section 3.

### 4. EXEC-CRIT-004: Missing Pydantic Models Added
- **Before**: DecomposeRequest, ValidateRequest, MarkRequest, MarkResponse, UnimplementedContract referenced in SVC tables but undefined
- **After**: All 5 models defined in REQ-002 (DecomposeRequest) and REQ-003 (ValidateRequest, MarkRequest, MarkResponse, UnimplementedContract) with full field types and defaults

### 5. EXEC-CRIT-005: Breaking Changes Endpoint Changed to POST (REQ-035, SVC-010)
- **Before**: "GET /api/breaking-changes/{contract_id} accepts new_spec as query/body"
- **After**: "POST /api/breaking-changes/{contract_id} accepts new_spec dict as request body"
- **SVC-010**: Updated from "PathParam+Body" to "BreakingChangeRequest { contract_id: string, new_spec: dict }"

### 6. EXEC-CRIT-006: SchemaRegistry Tables Added (REQ-007, REQ-029)
- **Before**: No shared_schemas or schema_consumers tables defined
- **After**: Both tables added to init_contracts_db() in REQ-007: `shared_schemas (name TEXT PRIMARY KEY, schema_json, owning_service, created_at, updated_at)` and `schema_consumers (schema_name REFERENCES shared_schemas, service_name, PRIMARY KEY)`. REQ-029 updated to reference both tables.

### 7. ARCH-CRIT-001: Schema Registry Test Added (TEST-040)
- **Before**: No TEST-xxx for tests/test_contract_engine/test_schema_registry.py
- **After**: TEST-040 added to Milestone 3 with 5 test cases: register_schema, list_schemas filter, get_consumers, add_consumer, duplicate registration update

### 8. ARCH-CRIT-002: Codebase Intelligence Router Test Added (TEST-041)
- **Before**: No TEST-xxx for tests/test_codebase_intelligence/test_routers.py
- **After**: TEST-041 added to Milestone 6 with 6 endpoint tests and minimum 10 test cases

---

## HIGH Fixes (14)

### 9. EXEC-HIGH-001: State Machine Detection Specified (REQ-016)
- **Before**: "state machines for entities with lifecycle states"
- **After**: Explicit detection criteria: entity has state machine if fields include "status"/"state"/"phase", OR PRD contains "X can be Y or Z" phrases. States from enum values, transitions from verb phrases.

### 10. EXEC-HIGH-002: Error Response Schema Defined (REQ-015)
- **Before**: "standard error responses (400, 404, 422, 500)"
- **After**: Explicit schemas: 400/404/500 use `{"detail": "message"}`, 422 uses Pydantic validation format `{"detail": [{"loc": ["string"], "msg": "string", "type": "string"}]}`

### 11. EXEC-HIGH-003: Default Values Specified (REQ-002, REQ-003, REQ-004, REQ-005)
- **Before**: Optional fields lacked explicit defaults
- **After**: All optional fields now have explicit `= None`, list fields have `= []`, enum fields have explicit defaults (e.g. ContractStatus.DRAFT, ImplementationStatus.PENDING, "healthy", "connected", "high", "error", "pending", "running")

### 12. EXEC-HIGH-004: DecompositionRun Model Added (REQ-002)
- **Before**: Referenced in REQ-007/REQ-020/Status Registry but no Pydantic model
- **After**: Full DecompositionRun model in REQ-002 with all fields: id, prd_content_hash, status, service_map_id, domain_model_id, validation_issues, interview_questions, started_at, completed_at

### 13. EXEC-HIGH-005: AsyncAPI $ref Resolution Scope Expanded (REQ-027, TECH-011)
- **Before**: Only #/components/messages/* and #/components/schemas/*
- **After**: 4 patterns: #/components/schemas/{name}, #/components/messages/{name}, #/channels/{name}, #/channels/{name}/messages/{msgName}. Plus nested resolution (one level) and circular $ref detection with ParsingError.

### 14. EXEC-HIGH-006: Pagination Defaults Added (REQ-025, REQ-033)
- **Before**: No default values for page/page_size
- **After**: page: int = 1, page_size: int = 20 (max 100)

### 15. EXEC-HIGH-007: Logging Implementation Specified (REQ-010)
- **Before**: "JSON-formatted logger with trace_id, service_name fields"
- **After**: stdlib `logging` with custom `JSONFormatter`, trace_id via `str(uuid.uuid4())` per request using `contextvars.ContextVar` in FastAPI middleware

### 16. EXEC-HIGH-008: Exception Status Codes Mapped (REQ-011)
- **Before**: "all extending a base AppError with status_code and detail"
- **After**: Explicit mapping: ValidationError=422, NotFoundError=404, ConflictError=409, ImmutabilityViolationError=409, ParsingError=400, SchemaError=422, ContractNotFoundError=404. Plus FastAPI exception handler.

### 17. EXEC-HIGH-009: Dead Code Entry Points Specified (REQ-048)
- **Before**: "framework lifecycle methods" (undefined)
- **After**: Explicit list: FastAPI (lifespan, on_event), Pydantic (model_validator, field_validator), Python dunder (__init__, __new__, __del__, __str__, __repr__, __enter__, __exit__, __aenter__, __aexit__), CLI (main, cli, app)

### 18. EXEC-HIGH-010: MCP Server Initialization Clarified (REQ-057, REQ-059, REQ-060, TECH-028)
- **Before**: Ambiguous about whether MCP servers share state with FastAPI apps
- **After**: "Each MCP server creates its OWN ConnectionPool instance. MCP servers do NOT import or share state with FastAPI apps — they are independent processes that access the same database files."

### 19. EXEC-HIGH-011: MCP Roundtrip Test Data Seeding Specified (REQ-061)
- **Before**: No setup steps for test data
- **After**: 4-step seeding: initialize schemas, seed architect.db via ServiceMapStore, seed contracts.db via ContractStore, seed symbols.db via SymbolDB from sample_codebase/

### 20. EXEC-HIGH-012: TypeScript Path Alias Handling Expanded (REQ-045)
- **Before**: "Handle: TypeScript path aliases (@/ prefix)"
- **After**: Read tsconfig.json compilerOptions.paths if present. Map @/ to src/ by default, ~/ to src/ by default. Custom paths: resolve first matching pattern. No tsconfig: only relative + @/ alias.

### 21. EXEC-HIGH-013: config.yaml Removed from Project Structure
- **Before**: Listed in file structure with no requirement
- **After**: Removed from project structure (it's agent-team config, not a deliverable)

### 22. EXEC-HIGH-014: Sample Data Content Specified (REQ-023, REQ-037, REQ-038)
- **Before**: Vague content descriptions
- **After**: REQ-023: explicit e-commerce entities (User, Order, Product, Payment, Notification), 3 services, 2 state machines. REQ-037/038: must pass respective validators.

---

## MEDIUM Fixes (17)

### 23. EXEC-MED-001: Compliance checker depth specified (REQ-040)
- Added: "Compare all top-level required fields. For nested objects, recursively check required fields up to 3 levels deep. For arrays, check the items schema type. Use resolved (no $ref) schema from prance."

### 24. EXEC-MED-002: ServiceInterfaceExtractor patterns added (REQ-056)
- Added patterns for Python (@app.get), TypeScript (app.get(), @Get()), C# ([HttpGet], [Route]), Go (http.HandleFunc). Plus event patterns: publish(), emit(), subscribe(), on_event().

### 25. EXEC-MED-003: SymbolDefinition.id format enforced (REQ-004)
- Added: "id generated via @model_validator(mode='before') from file_path and symbol_name"

### 26. EXEC-MED-004 / TECH-WARN-002: ChromaDB embedding_function parameter added (REQ-054)
- Changed: `get_or_create_collection("symbols", configuration=...)` -> `get_or_create_collection("symbols", embedding_function=DefaultEmbeddingFunction(), configuration=...)`

### 27. EXEC-MED-005: UUID generation method specified (TECH-032 new)
- Added: TECH-032 "All UUIDs must be generated using str(uuid.uuid4()) from the stdlib uuid module"

### 28. EXEC-MED-006: IncrementalIndexer return type clarified (REQ-055)
- Added: "Return a plain dict (not a Pydantic model) with indexed, symbols_found, dependencies_found, errors"

### 29. EXEC-MED-007: Test generator template specified (REQ-039)
- Added complete template structure with imports, BASE_URL, @schema.parametrize(), and negative test patterns

### 30. EXEC-MED-008: Decompose endpoint success status code specified (REQ-020)
- Added: "Returns 201 on successful decomposition"

### 31. EXEC-MED-009 through MED-012: All missing table schemas added (REQ-007)
- graph_snapshots, test_suites (with spec_hash + UNIQUE), indexed_files (with file_hash + loc), import_references — all with complete column definitions from Architecture Plan

### 32. EXEC-MED-013: Decompose endpoint marked async (REQ-020)
- Added: "The endpoint MUST be `async def` to support async HTTP calls to Contract Engine"

### 33. EXEC-MED-014: Input size limits added (TECH-034 new)
- Added: TECH-034 "PRD text input: max 1MB. Contract spec dict: max 5MB"

### 34. EXEC-MED-015: SQL parameterization required (TECH-033 new)
- Added: TECH-033 "All SQL queries MUST use parameterized queries (? placeholders)"

### 35. EXEC-MED-016: C#/Go tree-sitter node types specified (REQ-044)
- Added: explicit node type names for C# and Go

### 36. EXEC-MED-017: HealthStatus service_name source specified (INT-001)
- Added: "service_name loaded from constants e.g. 'architect', 'contract-engine', 'codebase-intelligence'"

---

## LOW Fixes (10)

### 37. EXEC-LOW-001: spec_hash auto-computation noted (REQ-003)
- Added: "spec_hash auto-computed via TECH-009 algorithm not provided by caller"

### 38. EXEC-LOW-002: Dockerfile CMD paths specified (INT-003)
- Added: exact CMD paths per service: `src.architect.main:app`, `src.contract_engine.main:app`, `src.codebase_intelligence.main:app`

### 39. EXEC-LOW-003: .mcp.json env vars fully specified (INT-005)
- Added: complete JSON with all env vars per MCP server

### 40. EXEC-LOW-005: HealthStatus.details type clarified (REQ-005)
- Changed: `details dict` -> `details: dict[str, Any] = Field(default_factory=dict)` with example

### 41. EXEC-LOW-006: Test count minimums added to all TEST requirements
- Added minimum test case counts to all TEST-xxx that lacked them (6-10 per test file)

### 42. EXEC-LOW-007: review_cycles note added
- Added note at PRD top: "Each requirement includes (review_cycles: N) — this is tracked by the build system"

### 43. EXEC-LOW-008: Codebase Intelligence router prefixes specified (REQ-058, WIRE-024 new)
- Added router prefix mapping and new WIRE-024

### 44. EXEC-LOW-010: tests/test_integration/__init__.py added to file structure
- Already present in original, confirmed present

---

## Technology Review Fixes (3)

### 45. TECH-INFO-001: mcp version comma (REQ-001)
- Already correct in PRD (`mcp>=1.25,<2`), confirmed preserved

### 46. TECH-WARN-001: QueryCursor detail added (REQ-043)
- Added: "Use QueryCursor(query) to execute queries — cursor.captures(root_node) returns dict[str, list[Node]]"

### 47. TECH-WARN-002: ChromaDB embedding_function parameter (REQ-054)
- Added: `embedding_function=DefaultEmbeddingFunction()` parameter (see fix #26)

---

## Architecture Review Fixes (7)

### 48. ARCH-CRIT-001: test_schema_registry.py test requirement (TEST-040)
- See fix #7

### 49. ARCH-CRIT-002: test_codebase_intelligence/test_routers.py test requirement (TEST-041)
- See fix #8

### 50. ARCH-WARN-001: Prompts directory removed from file structure
- Removed `src/architect/prompts/` (4 files) since Build 1 is deterministic/non-LLM

### 51. ARCH-WARN-002: Per-service config.py files given requirements (INT-006 new)
- Added: INT-006 "Create per-service config.py files that import and re-export their corresponding config class"

### 52. ARCH-WARN-003: Contract Engine storage layer simplified
- Removed `storage/contract_db.py` and `storage/implementation_db.py` from file structure since services handle DB directly via ConnectionPool

### 53. ARCH-WARN-004: src/__init__.py added to requirements
- Added to REQ-012: "create src/__init__.py"
- Added to WIRE-003: "src/__init__.py must also be created"

### 54. ARCH-WARN-005: All __init__.py files covered
- Added to WIRE-003: "All Python package directories shown in the file structure must contain an __init__.py file"

---

## Format Review Fixes (1)

### 55. FMT-WARN-003: Duplicate sections
- Kept both top-level Technology Stack/Project Structure and Architecture Decision subsections (format reviewer said this is acceptable and no parser impact)

---

## New Requirements Added

| ID | Milestone | Description |
|---|---|---|
| TECH-032 | M1 | UUID generation using str(uuid.uuid4()) |
| TECH-033 | M1 | SQL parameterized queries required |
| TECH-034 | M1 | Input size limits (1MB PRD, 5MB spec) |
| TEST-040 | M3 | Schema registry tests |
| TEST-041 | M6 | Codebase Intelligence router tests |
| INT-006 | M1 | Per-service config.py re-export files |
| WIRE-024 | M6 | Codebase Intelligence router prefixes |

## Requirement Count Summary (Updated)

| Prefix | Count | Range |
|---|---|---|
| REQ | 73 | 001-073 |
| TECH | 34 | 001-034 |
| WIRE | 24 | 001-024 |
| TEST | 41 | 001-041 |
| INT | 6 | 001-006 |
| SVC | 12 | 001-012 |
| **TOTAL** | **190** | |
