# Build 1 PRD Technical Audit

## Verdict: NEEDS FIXES (2 HIGH issues must be resolved before execution)

## Summary
- Critical issues: 0
- High issues: 2
- Medium issues: 5
- Low issues: 5

All technologies verified against current PyPI/docs. The PRD is remarkably thorough following the 55 fixes from the Fix Changelog. The two HIGH issues are real runtime-breaking bugs that agents will hit. Medium/Low issues are documentation ambiguities or edge cases that won't block execution but should be clarified.

---

## Issue List

### ISSUE-B1-001: AsyncAPI Validation Flow Missing Parse Step (HIGH)
**Location:** WIRE-009, REQ-033, REQ-027, REQ-028
**Category:** Architecture / Implementation
**Problem:** WIRE-009 says the contracts router must "route to `openapi_validator.validate_openapi()` or `asyncapi_validator.validate_asyncapi()` based on `ContractCreate.type` field." However, `validate_asyncapi()` (REQ-028) accepts `AsyncAPISpec` (the parsed dataclass), NOT a raw `dict`. The raw spec `dict` from `ContractCreate.spec` must first be parsed via `asyncapi_parser.parse_asyncapi(spec_dict)` to produce an `AsyncAPISpec` before it can be validated. Without this parse step, the router will pass a raw `dict` to a function expecting `AsyncAPISpec`, causing a `TypeError` at runtime.
**Evidence:** REQ-027 defines `parse_asyncapi(spec_path_or_dict)` returning `AsyncAPISpec`. REQ-028 defines `validate_asyncapi(spec: AsyncAPISpec)`. WIRE-009 skips the parse step entirely.
**Recommended Fix:** Update WIRE-009 to:
> "src/contract_engine/routers/contracts.py must validate spec type before storing — for OpenAPI contracts, call `openapi_validator.validate_openapi(spec)`. For AsyncAPI contracts, first parse via `asyncapi_parser.parse_asyncapi(spec)` to obtain an `AsyncAPISpec`, then validate via `asyncapi_validator.validate_asyncapi(parsed_spec)`. For `json_schema` type, validate using `jsonschema.Draft202012Validator.check_schema(spec)` (schema meta-validation)."

Also update REQ-033 to mention the parse-then-validate flow for AsyncAPI.

---

### ISSUE-B1-002: json_schema Contract Type Has No Validation Handler (HIGH)
**Location:** REQ-033, WIRE-009, ContractType enum (REQ-003)
**Category:** Completeness
**Problem:** The `ContractType` enum defines three types: `openapi`, `asyncapi`, and `json_schema`. REQ-033 says "Validate spec before storing using openapi_validator or asyncapi_validator based on contract type." WIRE-009 says "route to openapi_validator.validate_openapi() or asyncapi_validator.validate_asyncapi()." Neither mentions handling the `json_schema` type. An agent creating a `json_schema` contract will either get no validation (silent bug) or an unhandled case error.
**Evidence:** ContractType enum in REQ-003 includes `json_schema`. No requirement, wiring, or service addresses validation of this type.
**Recommended Fix:** Add to WIRE-009 and REQ-033: "For `json_schema` type contracts, validate using `jsonschema.Draft202012Validator.check_schema(spec)` to verify the spec is a valid JSON Schema. Return `ValidationResult(valid=True)` on success, `ValidationResult(valid=False, errors=[str(e)])` on `jsonschema.SchemaError`."

---

### ISSUE-B1-003: MCP Tool Counts Wrong in Architecture Decision Section (MEDIUM)
**Location:** Architecture Decision > Entry Points table (lines ~630-634)
**Category:** Completeness / Agent-Readiness
**Problem:** The Entry Points table states "Architect MCP: MCP server with 3 tools" and "Contract Engine MCP: MCP server with 6 tools." The actual implementations are 4 tools (REQ-059: decompose, get_service_map, get_contracts_for_service, get_domain_model) and 9 tools (REQ-060: create_contract, validate_spec, list_contracts, get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts). An agent reading the summary table may under-implement.
**Evidence:** REQ-059 defines 4 tools. REQ-060 defines 9 tools. The total of 20 in REQ-070 (docs/mcp_tools.md: "all 20 tools across 3 servers") is correct: 4+9+7=20.
**Recommended Fix:** Update Entry Points table:
- "Architect MCP: MCP server with **4** tools"
- "Contract Engine MCP: MCP server with **9** tools"

---

### ISSUE-B1-004: estimated_loc Constraint Too Restrictive (MEDIUM)
**Location:** REQ-002 — ServiceDefinition model
**Category:** Implementation
**Problem:** `ServiceDefinition.estimated_loc` has constraint `ge=1000 le=200000`. A microservice or small utility service could easily be under 1,000 lines of code. The Architect's service boundary algorithm (REQ-014) produces services from entity grouping, and some bounded contexts may be genuinely small (e.g., a Notification service that just forwards events). An agent creating a ServiceDefinition for such a service would get a Pydantic validation error.
**Evidence:** `estimated_loc ge=1000` in REQ-002.
**Recommended Fix:** Lower the minimum to `ge=100` or `ge=50` to accommodate small services. Alternatively, make it optional with a default.

---

### ISSUE-B1-005: PRD Text Size Limit Enforcement Location Unclear (MEDIUM)
**Location:** REQ-002 (DecomposeRequest), TECH-034
**Category:** Agent-Readiness
**Problem:** TECH-034 says "PRD text input: max 1MB." REQ-002 defines `DecomposeRequest(prd_text: str with min_length=10, max 1MB)` but the "max 1MB" is prose, not an explicit Pydantic constraint. An agent may not know whether to add `max_length=1_048_576` on the field, use a `@model_validator`, or enforce it in the endpoint handler.
**Evidence:** No explicit `max_length` on `prd_text` field in REQ-002. TECH-034 states the limit but doesn't specify enforcement mechanism.
**Recommended Fix:** Add to REQ-002: `prd_text: str = Field(min_length=10, max_length=1_048_576)` (1MB in characters). Or specify that REQ-020 endpoint handler must check `len(request.prd_text.encode('utf-8')) <= 1_048_576` and return 413.

---

### ISSUE-B1-006: Contract Spec Size Limit Enforcement Unclear (MEDIUM)
**Location:** TECH-034, REQ-025
**Category:** Agent-Readiness
**Problem:** TECH-034 says "Contract spec dict: max 5MB after JSON serialization." But no requirement specifies where this is enforced. REQ-025 (ContractStore.upsert) and REQ-033 (POST /api/contracts) don't mention size checking. An agent won't know where to add the 5MB check.
**Evidence:** TECH-034 states the limit. No REQ/WIRE references it for contracts.
**Recommended Fix:** Add to REQ-033: "Before validation and storage, check `len(json.dumps(contract_create.spec).encode('utf-8')) <= 5_242_880`. Return 413 Payload Too Large if exceeded."

---

### ISSUE-B1-007: ChromaDB Embedding Model Size Discrepancy (MEDIUM)
**Location:** TECH-023
**Category:** Technology
**Problem:** TECH-023 states "ChromaDB default embedding model (all-MiniLM-L6-v2) downloads ~80MB on first use." Multiple sources indicate the ONNX version used by ChromaDB's DefaultEmbeddingFunction is approximately 80-90MB, but the full SentenceTransformers version is ~300MB. Since ChromaDB uses its own ONNX-based implementation, the ~80MB figure is likely correct for the ONNX model alone, but the total download (including tokenizer files and config) may be larger. The Dockerfile pre-download step will work correctly regardless.
**Evidence:** ChromaDB docs confirm DefaultEmbeddingFunction uses all-MiniLM-L6-v2 locally via ONNX Runtime. Various sources report different sizes depending on model format.
**Recommended Fix:** Change to "downloads ~80-100MB on first use" or simply "downloads on first use" to avoid precision issues.

---

### ISSUE-B1-008: OpenAPIV31SpecValidator Import Path Not Specified (LOW)
**Location:** REQ-026
**Category:** Agent-Readiness
**Problem:** REQ-026 says "Use OpenAPIV31SpecValidator for detailed error iteration" but doesn't specify the import path. The class exists at `from openapi_spec_validator.validation import OpenAPIV31SpecValidator`. An agent unfamiliar with the library may struggle to find the correct import.
**Evidence:** The class exists but is in a submodule, not the top-level package.
**Recommended Fix:** Add import path: "Use `OpenAPIV31SpecValidator` (from `openapi_spec_validator.validation`) for detailed error iteration."

---

### ISSUE-B1-009: Duplicate Architecture/Technology Sections (LOW)
**Location:** Lines 7-21 (Technology Stack) and lines 597-606 (Architecture Decision > Technology Stack)
**Category:** Completeness
**Problem:** The PRD has two nearly identical Technology Stack sections. The top-level one is the authoritative version with pinned versions. The Architecture Decision section duplicates it without version pins. This is harmless but could confuse an agent about which is canonical.
**Evidence:** FMT-WARN-003 in the Fix Changelog acknowledged this and kept both intentionally.
**Recommended Fix:** No change needed (already acknowledged). Optionally, add a note to the Architecture Decision section: "See top-level Technology Stack for pinned versions."

---

### ISSUE-B1-010: ServiceInterfaceExtractor Regex Patterns Diverge from Build 3 (LOW)
**Location:** REQ-056
**Category:** Cross-Build Compatibility
**Problem:** REQ-056 says agents "MAY use these regex patterns" (FastAPI, Express, Spring, .NET) for endpoint detection. Build 3 also uses regex patterns for similar purposes. The patterns in Build 1 and Build 3 may diverge over time if maintained independently. However, since REQ-056 marks these as optional ("MAY"), and the primary extraction method is AST-based (tree-sitter), this is low risk.
**Evidence:** REQ-056 says "Optional: For consistency with Build 3's regex-based approach, agents MAY use these regex patterns."
**Recommended Fix:** No change needed. The "MAY" qualifier handles this correctly.

---

### ISSUE-B1-011: Missing index for decomposition_runs.prd_content_hash (LOW)
**Location:** REQ-007 — init_architect_db()
**Category:** Implementation
**Problem:** The `decomposition_runs` table has `prd_content_hash TEXT NOT NULL` but no index on it. If the system needs to look up existing decompositions by PRD hash (e.g., to skip re-decomposition of the same PRD), this will require a full table scan. The `service_maps` table correctly has `idx_smap_prd ON service_maps(prd_hash)`.
**Evidence:** REQ-007 SQL for decomposition_runs has no index on prd_content_hash.
**Recommended Fix:** Add `CREATE INDEX IF NOT EXISTS idx_drun_prd ON decomposition_runs(prd_content_hash);` to init_architect_db().

---

### ISSUE-B1-012: Sample PRD Entity Count Mismatch (LOW)
**Location:** REQ-023
**Category:** Agent-Readiness
**Problem:** REQ-023 says the sample PRD should have "User, Order, Product, Payment, and Notification entities across 3 services." That's 5 entities across 3 services. But it also says "at least 5 entities, at least 2 services." The text says 3 services but the minimum is 2 — this is fine (3 >= 2). However, an agent might create exactly 2 services instead of the 3 mentioned in the entity description.
**Evidence:** "across 3 services" vs "at least 2 services" in same requirement.
**Recommended Fix:** Change "at least 2 services" to "at least 3 services" to match the entity distribution description.

---

## Technology Verification Table

| Technology | Version in PRD | Latest Stable | API Correct? | Notes |
|------------|---------------|---------------|-------------|-------|
| Python | 3.12+ | 3.13.2 | Yes | 3.12+ is appropriate |
| FastAPI | 0.129.0 | 0.129.0 | Yes | Released 2026-02-12, current |
| tree-sitter | 0.25.2 | 0.25.2 | Yes | QueryCursor, captures() dict return confirmed |
| tree-sitter-python | 0.25.0 | 0.25.0 | Yes | language() function confirmed |
| tree-sitter-typescript | 0.23.2 | 0.23.2 | Yes | language_typescript() + language_tsx() confirmed |
| tree-sitter-c-sharp | 0.23.1 | 0.23.1 | Yes | language() function expected |
| tree-sitter-go | 0.25.0 | 0.25.0 | Yes | language() function expected |
| ChromaDB | 1.5.0 | 1.5.0 | Yes | PersistentClient, DefaultEmbeddingFunction, configuration param confirmed |
| NetworkX | 3.6.1 | 3.6.1 | Yes | node_link_data(edges="edges") confirmed |
| MCP SDK | >=1.25,<2 | 1.26.0 | Yes | @mcp.tool(), transport="stdio" confirmed |
| Schemathesis | 4.10.1 | 4.10.1 | Yes | openapi.from_path(), @schema.parametrize() confirmed |
| prance | 25.4.8.0 | 25.4.8.0 | Yes | ResolvingParser confirmed |
| openapi-spec-validator | >=0.7.0 | 0.7.2 (stable) | Yes | validate(), OpenAPIV31SpecValidator confirmed |
| pydantic | >=2.5.0 | 2.x latest | Yes | v2 syntax throughout |
| pydantic-settings | >=2.1.0 | 2.x latest | Yes | BaseSettings with env vars |
| uvicorn | >=0.30.0 | 0.34.x | Yes | Standard ASGI server |
| httpx | >=0.27.0 | 0.28.x | Yes | AsyncClient + sync Client |
| pyyaml | >=6.0 | 6.0.2 | Yes | Standard YAML parser |
| jsonschema | >=4.20.0 | 4.x latest | Yes | validate(), Draft202012Validator |
| pytest | >=8.0.0 | 8.x latest | Yes | Standard test framework |
| pytest-asyncio | >=0.23.0 | 0.24.x | Yes | asyncio_mode="auto" |
| ruff | >=0.5.0 | 0.9.x | Yes | Linter/formatter |
| mypy | >=1.8.0 | 1.x latest | Yes | Type checker |

---

## Cross-Build Compatibility Check

### Build 1 -> Build 2 Interface

| Interface | Build 1 Definition | Build 2 Expectation | Match? |
|-----------|-------------------|---------------------|--------|
| Contract Engine MCP tools (9) | REQ-060: create_contract, validate_spec, list_contracts, get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts | REQ-017 wraps 6 of 9 (get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts). Remaining 3 consumed by Build 3. | YES |
| Codebase Intelligence MCP tools (7) | REQ-057: find_definition, find_callers, find_dependencies, search_semantic, get_service_interface, check_dead_code, register_artifact | Build 2 REQ-030 wraps all 7 | YES |
| Architect MCP tools (4) | REQ-059: decompose, get_service_map, get_contracts_for_service, get_domain_model | Build 3 SVC-005 calls decompose | YES |
| validate_endpoint response schema | ComplianceResult with ComplianceViolation list (field, expected, actual, severity) | Build 2 INT-004 expects { valid: boolean, violations: [{field, expected, actual}] } | YES (MCP tool wraps ComplianceResult) |
| MCP server command paths | .mcp.json: python -m src.architect.mcp_server / src.contract_engine.mcp_server / src.codebase_intelligence.mcp_server | Build 2 config mcp_args defaults: ["-m", "src.contract_engine.mcp_server"] | YES |

### Build 1 -> Build 3 Interface

| Interface | Build 1 Definition | Build 3 Expectation | Match? |
|-----------|-------------------|---------------------|--------|
| Architect decompose tool | REQ-059: decompose(prd_text: str) -> DecompositionResult dict | Build 3 SVC-005: decompose { prd_text: string } -> { service_map, domain_model, contract_stubs } | YES |
| Contract Engine create_contract | REQ-060: create_contract(...) | Build 3 REQ-047: registers via create_contract, validate_spec MCP tools | YES |
| MCP transport | stdio (REQ-057, REQ-059, REQ-060) | Build 3 WIRE-015: MCP stdio transport | YES |
| Lazy imports | Build 1 has no lazy import requirement (standalone) | Build 3 INT-006: lazy imports with ImportError fallback | N/A (Build 3 is the consumer) |

**Cross-build verdict: All interfaces match.** No data model or tool signature mismatches detected.

---

## Clean Sections (no issues found)

The following sections passed all checks with no issues:

- **Milestone 1 (Core Data Models):** All 12 REQs, 5 TECHs, 3 WIREs, 4 TESTs, 6 INTs thoroughly specified. Pydantic models are complete with field types, defaults, validators, and constraints. SQL schemas are production-grade with proper indexes, constraints, and foreign keys.

- **Milestone 2 (Architect Service):** All REQs (013-024) fully specified with deterministic algorithms. PRD parser entity/relationship extraction patterns are concrete and implementable. Service boundary algorithm is a clear 5-step process. Contract generator, domain modeler, and validator all have precise specifications.

- **Milestone 4 (Contract Test Generation):** REQ-039 (TestGenerator) has complete template structure. REQ-040 (ComplianceChecker) has clear depth rules (3 levels). Test requirements are concrete.

- **Milestone 5 (Codebase Intelligence L1-L2):** Tree-sitter integration is thoroughly specified with correct API usage for 0.25.2. Language-specific parser node types are documented. NetworkX usage is correct throughout. Dead code detection entry point exclusion list is comprehensive.

- **Milestone 6 (Codebase Intelligence L3 + MCP):** ChromaDB integration is correct with proper embedding function and configuration parameters. MCP server specification is thorough with clear independence from FastAPI apps. Incremental indexer pipeline is well-defined.

- **Milestone 7 (Architect + Contract Engine MCP Servers):** Tool definitions are complete with type annotations. Inter-service communication pattern (httpx sync for MCP) is correct per MCP SDK threading model. End-to-end test specification (REQ-061) has proper data seeding steps.

- **Milestone 8 (Integration + Docker + E2E):** Docker Compose specification is production-grade. Health check approach (python urllib, not curl) is correct for slim images. Async/sync boundary rules (TECH-035, TECH-036) are thorough and accurate. Documentation requirements are comprehensive.

- **Status Registry:** Complete and consistent with all model enums.

- **Wiring Map:** All 24 WIRE requirements are concrete and traceable. Wiring anti-patterns section is valuable.

- **Initialization Order:** Correct 7-step sequence.

---

## Fix Changelog Integration Verification

All 55 fixes from BUILD1_PRD_FIX_CHANGELOG.md have been verified as cleanly integrated:

- 8 CRITICAL fixes: All present in current PRD text
- 14 HIGH fixes: All present including dead code entry points, MCP initialization, TypeScript aliases
- 17 MEDIUM fixes: All present including compliance depth, interface patterns, UUID generation
- 10 LOW fixes: All present
- 3 Technology fixes: tree-sitter QueryCursor detail, ChromaDB embedding_function parameter present
- 7 Architecture fixes: schema registry test (TEST-040), router test (TEST-041), __init__.py coverage all present

No residual issues from the fix changelog.

---

## Requirement Coverage Verification

| Prefix | Expected Count | Verified | Gap |
|--------|---------------|----------|-----|
| REQ | 73 (001-073) | 73 | None |
| TECH | 36 (001-036) | 36 | None |
| WIRE | 24 (001-024) | 24 | None |
| TEST | 41 (001-041) | 41 | None |
| INT | 6 (001-006) | 6 | None |
| SVC | 12 (001-012) | 12 | None |
| **TOTAL** | **192** | **192** | **None** |

Note: The Fix Changelog says 190 total, but TECH-035 and TECH-036 bring it to 192. Minor accounting difference.
