# Build 1 Architecture Plan — Architect + Contract Engine + Codebase Intelligence

> **Date:** 2026-02-14
> **Purpose:** Complete architecture specification for Build 1 of the Super Agent Team.
> Every technical decision references BUILD1_TECHNOLOGY_RESEARCH.md (tech) or CODEBASE_PRD_FORMAT_RESEARCH.md (format).
> This document is designed for direct conversion into a PRD with REQ-xxx, SVC-xxx, WIRE-xxx identifiers.

---

## Table of Contents

1. [Complete Project File Structure](#1-complete-project-file-structure)
2. [Complete Data Models](#2-complete-data-models)
3. [Complete Database Schema](#3-complete-database-schema)
4. [MCP Server Tool Specifications](#4-mcp-server-tool-specifications)
5. [Service Architecture](#5-service-architecture)
6. [Milestone Breakdown (8 Milestones)](#6-milestone-breakdown-8-milestones)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Integration Points with Build 2 and Build 3](#8-integration-points-with-build-2-and-build-3)
9. [Configuration Design](#9-configuration-design)
10. [Risk Mitigations](#10-risk-mitigations)

---

## 1. Complete Project File Structure

The monorepo uses a `src/` layout with four Python packages. Each service is independently deployable via Docker but shares models and utilities from `shared/`.

```
super-team/
  pyproject.toml                          # Project metadata, dependencies, build config
  README.md                               # Project overview and setup instructions
  docker-compose.yml                      # Multi-service Docker Compose orchestration
  .env.example                            # Environment variable template
  .mcp.json                               # MCP server configuration for Claude Code
  config.yaml                             # agent-team config for building this project

  src/
    __init__.py

    shared/                               # Shared utilities and models used by all services
      __init__.py
      models/
        __init__.py
        architect.py                      # Architect data models (ServiceDefinition, DomainEntity, etc.)
        contracts.py                      # Contract data models (ContractEntry, OpenAPIContract, etc.)
        codebase.py                       # Codebase Intelligence models (SymbolDefinition, etc.)
        common.py                         # Shared models (BuildCycle, HealthStatus, ArtifactRegistration)
      db/
        __init__.py
        connection.py                     # SQLite connection pool with WAL mode, thread-local connections
        schema.py                         # Schema initialization and migration helpers
      config.py                           # Shared configuration loader (Pydantic Settings)
      constants.py                        # Shared constants (version strings, default ports, etc.)
      logging.py                          # Structured logging configuration (JSON format with trace_id)
      errors.py                           # Shared exception classes (ValidationError, NotFoundError, etc.)

    architect/                            # System 1: PRD Decomposition Engine
      __init__.py
      main.py                             # FastAPI app with lifespan, router registration
      mcp_server.py                       # MCP server entry point (stdio transport)
      config.py                           # Architect-specific settings (Pydantic BaseSettings)
      routers/
        __init__.py
        decomposition.py                  # POST /api/decompose — trigger PRD decomposition
        service_map.py                    # GET /api/service-map — retrieve service map
        domain_model.py                   # GET /api/domain-model — retrieve domain model
        health.py                         # GET /api/health — health check endpoint
      services/
        __init__.py
        prd_parser.py                     # Extract entities, relationships, bounded contexts from PRD text
        service_boundary.py               # Identify service boundaries using DDD principles
        contract_generator.py             # Generate OpenAPI/AsyncAPI stubs from service boundaries
        domain_modeler.py                 # Build ubiquitous language / domain model
        validator.py                      # Validate decomposition (no cycles, no overlap, completeness)
      storage/
        __init__.py
        service_map_store.py              # Persist ServiceMap to SQLite + YAML export
        domain_model_store.py             # Persist DomainModel to SQLite
      prompts/
        __init__.py
        decomposition_prompt.py           # LLM prompt for PRD decomposition
        interview_prompt.py               # LLM prompt for clarification questions
        validation_prompt.py              # LLM prompt for decomposition validation

    contract_engine/                      # System 2: Contract Registry + Validation + Test Generation
      __init__.py
      main.py                             # FastAPI app with lifespan, router registration
      mcp_server.py                       # MCP server entry point (stdio transport)
      config.py                           # Contract Engine-specific settings
      routers/
        __init__.py
        contracts.py                      # CRUD endpoints for contracts (/api/contracts/*)
        validation.py                     # POST /api/validate — validate a spec
        tests.py                          # POST /api/tests/generate — generate test suites
        implementations.py                # Track which services implement which contracts
        breaking_changes.py               # GET /api/breaking-changes — detect breaking changes
        health.py                         # GET /api/health — health check
      services/
        __init__.py
        contract_store.py                 # SQLite-backed contract CRUD with hash-based change detection
        openapi_validator.py              # OpenAPI 3.1 validation using openapi-spec-validator + prance
        asyncapi_parser.py                # Lightweight AsyncAPI 3.0 parser (~500 lines, custom)
        asyncapi_validator.py             # AsyncAPI 3.0 validation (custom, YAML + jsonschema)
        schema_registry.py                # JSON Schema registry for shared data models
        version_manager.py                # Contract versioning with immutability per build cycle
        breaking_change_detector.py       # Detect breaking changes between contract versions
        test_generator.py                 # Generate conformance tests from contracts (Schemathesis)
        compliance_checker.py             # Check actual API response against contracted schema
        implementation_tracker.py         # Track which services implement which contracts
      storage/
        __init__.py
        contract_db.py                    # Direct SQLite operations for contracts table
        implementation_db.py              # Direct SQLite operations for implementations table

    codebase_intelligence/                # System 3: Live Queryable Codebase Index via MCP
      __init__.py
      main.py                             # FastAPI app with lifespan, router registration
      mcp_server.py                       # MCP server entry point (stdio transport) — PRIMARY interface
      config.py                           # Codebase Intelligence-specific settings
      routers/
        __init__.py
        symbols.py                        # GET /api/symbols — query symbol index
        dependencies.py                   # GET /api/dependencies — query dependency graph
        search.py                         # POST /api/search — semantic search
        artifacts.py                      # POST /api/artifacts — register new files
        dead_code.py                      # GET /api/dead-code — find unused symbols
        health.py                         # GET /api/health — health check
      services/
        __init__.py
        ast_parser.py                     # Tree-sitter AST parsing for Python, TypeScript, C#, Go
        symbol_extractor.py               # Extract classes, functions, interfaces, types from AST
        import_resolver.py                # Resolve import paths to actual file paths
        graph_builder.py                  # Build NetworkX DiGraph from imports/calls/inherits
        graph_analyzer.py                 # PageRank, cycle detection, topological sort, impact analysis
        semantic_indexer.py               # ChromaDB indexing of code chunks
        semantic_searcher.py              # ChromaDB semantic search with metadata filtering
        dead_code_detector.py             # Find symbols defined but never referenced
        incremental_indexer.py            # Index new/changed files incrementally
        service_interface_extractor.py    # Extract public API surface per service
      parsers/
        __init__.py
        python_parser.py                  # Python-specific tree-sitter queries and symbol extraction
        typescript_parser.py              # TypeScript-specific tree-sitter queries and symbol extraction
        csharp_parser.py                  # C#-specific tree-sitter queries and symbol extraction
        go_parser.py                      # Go-specific tree-sitter queries and symbol extraction
      storage/
        __init__.py
        symbol_db.py                      # SQLite operations for symbols table
        graph_db.py                       # SQLite persistence for dependency edges + NetworkX serialization
        chroma_store.py                   # ChromaDB collection management (create, upsert, query, delete)

  tests/
    __init__.py
    conftest.py                           # Shared pytest fixtures (tmp DB, test data, mock services)

    test_shared/
      __init__.py
      test_models.py                      # Unit tests for all Pydantic/dataclass models
      test_db_connection.py               # Unit tests for SQLite connection pool
      test_config.py                      # Unit tests for shared config loader

    test_architect/
      __init__.py
      test_prd_parser.py                  # Unit tests for PRD entity extraction
      test_service_boundary.py            # Unit tests for service boundary identification
      test_contract_generator.py          # Unit tests for OpenAPI/AsyncAPI stub generation
      test_domain_modeler.py              # Unit tests for domain model construction
      test_validator.py                   # Unit tests for decomposition validation
      test_routers.py                     # Integration tests for FastAPI endpoints
      test_mcp_tools.py                   # Integration tests for MCP tool responses

    test_contract_engine/
      __init__.py
      test_contract_store.py              # Unit tests for contract CRUD
      test_openapi_validator.py           # Unit tests for OpenAPI validation
      test_asyncapi_parser.py             # Unit tests for AsyncAPI 3.0 parser
      test_asyncapi_validator.py          # Unit tests for AsyncAPI validation
      test_schema_registry.py             # Unit tests for JSON Schema registry
      test_version_manager.py             # Unit tests for versioning + immutability
      test_breaking_change_detector.py    # Unit tests for breaking change detection
      test_test_generator.py              # Unit tests for test suite generation
      test_compliance_checker.py          # Unit tests for compliance checking
      test_implementation_tracker.py      # Unit tests for implementation tracking
      test_routers.py                     # Integration tests for FastAPI endpoints
      test_mcp_tools.py                   # Integration tests for MCP tool responses

    test_codebase_intelligence/
      __init__.py
      test_ast_parser.py                  # Unit tests for tree-sitter AST parsing
      test_symbol_extractor.py            # Unit tests for symbol extraction
      test_import_resolver.py             # Unit tests for import path resolution
      test_graph_builder.py               # Unit tests for dependency graph construction
      test_graph_analyzer.py              # Unit tests for graph algorithms
      test_semantic_indexer.py            # Unit tests for ChromaDB indexing
      test_semantic_searcher.py           # Unit tests for semantic search
      test_dead_code_detector.py          # Unit tests for dead code detection
      test_incremental_indexer.py         # Unit tests for incremental indexing
      test_language_parsers.py            # Unit tests for Python/TS/C#/Go parsers
      test_routers.py                     # Integration tests for FastAPI endpoints
      test_mcp_tools.py                   # Integration tests for MCP tool responses

    test_integration/
      __init__.py
      test_architect_to_contracts.py      # E2E: PRD → Architect → Contract Engine
      test_codebase_indexing.py           # E2E: Source files → index → query
      test_mcp_roundtrip.py              # E2E: MCP client → server → response
      test_docker_compose.py             # E2E: Full Docker Compose health checks

  docker/
    architect/
      Dockerfile                          # Architect service Docker image
      requirements.txt                    # Architect-specific pip dependencies
    contract_engine/
      Dockerfile                          # Contract Engine Docker image
      requirements.txt                    # Contract Engine-specific pip dependencies
    codebase_intelligence/
      Dockerfile                          # Codebase Intelligence Docker image
      requirements.txt                    # CI-specific pip dependencies

  docs/
    architecture.md                       # Architecture overview diagram
    api_reference.md                      # Combined API reference for all services
    mcp_tools.md                          # MCP tool documentation for Claude Code users
    deployment.md                         # Deployment and configuration guide

  sample_data/
    sample_prd.md                         # Sample PRD for testing decomposition
    sample_service_map.yaml               # Expected output from Architect
    sample_openapi.yaml                   # Sample OpenAPI 3.1 contract
    sample_asyncapi.yaml                  # Sample AsyncAPI 3.0 contract
    sample_codebase/                      # Small codebase for testing indexing
      auth_service/
        auth.py                           # Sample Python service file
        models.py                         # Sample models file
      billing_service/
        billing.ts                        # Sample TypeScript service file
        types.ts                          # Sample types file
```

**Total files: ~120 Python files + ~15 config/Docker/doc files = ~135 files**

---

## 2. Complete Data Models

All API-facing models use Pydantic v2 BaseModel. Internal state uses Python dataclasses. All models live in `src/shared/models/` for cross-service reuse.

### 2.1 Architect Models (`src/shared/models/architect.py`)

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ServiceStack(BaseModel):
    """Technology stack for a single service."""
    backend: str = Field(..., examples=["FastAPI+Python"])
    database: str = Field(..., examples=["PostgreSQL"])
    frontend: str | None = Field(None, examples=["React+TypeScript"])
    message_broker: str | None = Field(None, examples=["RabbitMQ"])


class ServiceDefinition(BaseModel):
    """A single service in the decomposed architecture."""
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$",
                      examples=["auth-service"])
    domain: str = Field(..., min_length=1, examples=["Authentication & Authorization"])
    description: str = Field(..., min_length=10)
    stack: ServiceStack
    estimated_loc: int = Field(..., ge=1000, le=200000)
    owns_entities: list[str] = Field(default_factory=list,
                                      description="Entity names owned by this service")
    provides_contracts: list[str] = Field(default_factory=list,
                                          description="Contract IDs this service provides")
    consumes_contracts: list[str] = Field(default_factory=list,
                                          description="Contract IDs this service consumes")


class ServiceMap(BaseModel):
    """Complete service decomposition produced by the Architect."""
    project_name: str = Field(..., min_length=1)
    services: list[ServiceDefinition] = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    prd_hash: str = Field(..., description="SHA-256 hash of source PRD for change detection")
    build_cycle_id: str | None = None


class RelationshipType(str, Enum):
    OWNS = "owns"
    REFERENCES = "references"
    TRIGGERS = "triggers"
    EXTENDS = "extends"
    DEPENDS_ON = "depends_on"


class DomainEntity(BaseModel):
    """A business entity in the domain model."""
    name: str = Field(..., min_length=1, examples=["User", "Order"])
    description: str = Field(..., min_length=5)
    owning_service: str = Field(..., description="Service name that owns this entity")
    fields: list[EntityField] = Field(default_factory=list)
    state_machine: StateMachine | None = None


class EntityField(BaseModel):
    """A field on a domain entity."""
    name: str = Field(..., min_length=1)
    type: str = Field(..., examples=["string", "integer", "uuid", "datetime"])
    required: bool = True
    description: str = ""


class StateMachine(BaseModel):
    """State machine for an entity with defined transitions."""
    states: list[str] = Field(..., min_length=2)
    initial_state: str
    transitions: list[StateTransition] = Field(default_factory=list)


class StateTransition(BaseModel):
    """A single state transition."""
    from_state: str
    to_state: str
    trigger: str = Field(..., description="Event or action that causes the transition")
    guard: str | None = Field(None, description="Condition that must be true")


class DomainRelationship(BaseModel):
    """Relationship between two domain entities."""
    source_entity: str
    target_entity: str
    relationship_type: RelationshipType
    cardinality: str = Field(..., pattern=r"^(1|N):(1|N)$", examples=["1:N", "N:N"])
    description: str = ""


class DomainModel(BaseModel):
    """Complete domain model — the ubiquitous language for the platform."""
    entities: list[DomainEntity] = Field(default_factory=list)
    relationships: list[DomainRelationship] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DecompositionResult(BaseModel):
    """Complete output of the Architect's decomposition process."""
    service_map: ServiceMap
    domain_model: DomainModel
    contract_stubs: list[dict] = Field(default_factory=list,
                                        description="OpenAPI/AsyncAPI spec dicts to register")
    validation_issues: list[str] = Field(default_factory=list,
                                          description="Warnings from validation pass")
    interview_questions: list[str] = Field(default_factory=list,
                                            description="Clarification questions for human review")
```

### 2.2 Contract Models (`src/shared/models/contracts.py`)

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ContractType(str, Enum):
    OPENAPI = "openapi"
    ASYNCAPI = "asyncapi"
    JSON_SCHEMA = "json_schema"


class ContractStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class ImplementationStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"


class ContractEntry(BaseModel):
    """A contract stored in the registry."""
    id: str = Field(..., min_length=1)
    type: ContractType
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    service_name: str = Field(..., min_length=1)
    spec: dict = Field(..., description="Full OpenAPI/AsyncAPI/JSONSchema spec dict")
    spec_hash: str = Field(..., description="SHA-256 hash of the spec JSON")
    status: ContractStatus = ContractStatus.ACTIVE
    build_cycle_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class ContractCreate(BaseModel):
    """Request model for creating/updating a contract."""
    service_name: str = Field(..., min_length=1, max_length=100)
    type: ContractType
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    spec: dict = Field(..., description="OpenAPI/AsyncAPI/JSONSchema spec as JSON")
    build_cycle_id: str | None = None


class ContractListResponse(BaseModel):
    """Paginated list of contracts."""
    items: list[ContractEntry]
    total: int
    page: int
    page_size: int


class OpenAPIContract(BaseModel):
    """Parsed OpenAPI 3.1 contract with extracted endpoints."""
    contract_id: str
    openapi_version: str = Field(default="3.1.0")
    title: str
    api_version: str
    endpoints: list[EndpointSpec] = Field(default_factory=list)
    schemas: dict[str, dict] = Field(default_factory=dict,
                                      description="Component schemas keyed by name")


class EndpointSpec(BaseModel):
    """A single API endpoint extracted from OpenAPI spec."""
    path: str
    method: str = Field(..., pattern=r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$")
    operation_id: str | None = None
    summary: str = ""
    parameters: list[dict] = Field(default_factory=list)
    request_body_schema: dict | None = None
    response_schemas: dict[str, dict] = Field(default_factory=dict,
                                                description="Status code -> schema mapping")


class AsyncAPIContract(BaseModel):
    """Parsed AsyncAPI 3.0 contract with extracted channels and operations."""
    contract_id: str
    asyncapi_version: str = Field(default="3.0.0")
    title: str
    api_version: str
    channels: list[ChannelSpec] = Field(default_factory=list)
    operations: list[OperationSpec] = Field(default_factory=list)
    schemas: dict[str, dict] = Field(default_factory=dict)


class ChannelSpec(BaseModel):
    """A message channel from AsyncAPI spec."""
    name: str
    address: str
    description: str = ""
    messages: list[MessageSpec] = Field(default_factory=list)


class MessageSpec(BaseModel):
    """A message definition from AsyncAPI spec."""
    name: str
    content_type: str = "application/json"
    payload_schema: dict = Field(default_factory=dict)
    headers_schema: dict | None = None


class OperationSpec(BaseModel):
    """An operation (send/receive) from AsyncAPI spec."""
    name: str
    action: str = Field(..., pattern=r"^(send|receive)$")
    channel_name: str
    summary: str = ""
    message_names: list[str] = Field(default_factory=list)


class SharedSchema(BaseModel):
    """A shared JSON Schema used across services."""
    name: str
    schema: dict
    owning_service: str
    consuming_services: list[str] = Field(default_factory=list)


class ContractVersion(BaseModel):
    """Version tracking for a contract."""
    contract_id: str
    version: str
    spec_hash: str
    build_cycle_id: str
    created_at: datetime
    is_breaking: bool = False
    breaking_changes: list[BreakingChange] = Field(default_factory=list)


class BreakingChange(BaseModel):
    """A detected breaking change between contract versions."""
    change_type: str = Field(..., description="removed_field, type_change, removed_endpoint, etc.")
    path: str = Field(..., description="JSON path to the changed element")
    old_value: str | None = None
    new_value: str | None = None
    severity: str = Field(default="error", pattern=r"^(error|warning|info)$")
    affected_consumers: list[str] = Field(default_factory=list)


class ImplementationRecord(BaseModel):
    """Tracks which service implements which contract."""
    contract_id: str
    service_name: str
    evidence_path: str = Field(..., description="File path proving implementation")
    status: ImplementationStatus = ImplementationStatus.PENDING
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of validating a spec or an implementation."""
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ContractTestSuite(BaseModel):
    """Generated test suite from a contract."""
    contract_id: str
    framework: str = Field(default="pytest", pattern=r"^(pytest|jest)$")
    test_code: str = Field(..., description="Complete runnable test file content")
    test_count: int = Field(..., ge=0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceResult(BaseModel):
    """Result of checking an actual API response against its contract."""
    endpoint_path: str
    method: str
    compliant: bool
    violations: list[ComplianceViolation] = Field(default_factory=list)


class ComplianceViolation(BaseModel):
    """A single compliance violation."""
    field: str
    expected: str
    actual: str
    severity: str = "error"
```

### 2.3 Codebase Intelligence Models (`src/shared/models/codebase.py`)

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SymbolKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"
    TYPE = "type"
    ENUM = "enum"
    VARIABLE = "variable"
    METHOD = "method"


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    GO = "go"


class DependencyRelation(str, Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    USES = "uses"


class SymbolDefinition(BaseModel):
    """A code symbol (class, function, interface, etc.) with location info."""
    id: str = Field(..., description="Unique ID: file_path::symbol_name")
    file_path: str
    symbol_name: str
    kind: SymbolKind
    language: Language
    service_name: str | None = None
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    signature: str | None = Field(None, description="Function/method signature string")
    docstring: str | None = None
    is_exported: bool = True
    parent_symbol: str | None = Field(None, description="Enclosing class/module name")


class ImportReference(BaseModel):
    """An import statement linking two files."""
    source_file: str = Field(..., description="File containing the import")
    target_file: str = Field(..., description="File being imported")
    imported_names: list[str] = Field(default_factory=list,
                                       description="Specific names imported (empty = wildcard)")
    line: int = Field(..., ge=1)
    is_relative: bool = False


class DependencyEdge(BaseModel):
    """An edge in the dependency graph."""
    source_symbol_id: str
    target_symbol_id: str
    relation: DependencyRelation
    source_file: str
    target_file: str
    line: int | None = None


class CodeChunk(BaseModel):
    """A chunk of code for semantic indexing in ChromaDB."""
    id: str = Field(..., description="Unique chunk ID")
    file_path: str
    content: str = Field(..., description="Code content + docstring for embedding")
    language: Language
    service_name: str | None = None
    symbol_name: str | None = None
    symbol_kind: SymbolKind | None = None
    line_start: int
    line_end: int


class SemanticSearchResult(BaseModel):
    """A single result from semantic search."""
    chunk_id: str
    file_path: str
    symbol_name: str | None = None
    content: str
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (lower = more similar)")
    language: Language
    service_name: str | None = None
    line_start: int
    line_end: int


class ServiceInterface(BaseModel):
    """Public API surface of a service."""
    service_name: str
    endpoints: list[dict] = Field(default_factory=list,
                                    description="HTTP endpoints with path/method/handler")
    events_published: list[dict] = Field(default_factory=list,
                                          description="Events this service publishes")
    events_consumed: list[dict] = Field(default_factory=list,
                                         description="Events this service subscribes to")
    exported_symbols: list[SymbolDefinition] = Field(default_factory=list)


class DeadCodeEntry(BaseModel):
    """A symbol that is defined but never referenced."""
    symbol_name: str
    file_path: str
    kind: SymbolKind
    line: int
    service_name: str | None = None
    confidence: str = Field(default="high", pattern=r"^(high|medium|low)$")


class GraphAnalysis(BaseModel):
    """Results of analyzing the dependency graph."""
    node_count: int
    edge_count: int
    is_dag: bool
    circular_dependencies: list[list[str]] = Field(default_factory=list)
    top_files_by_pagerank: list[tuple[str, float]] = Field(default_factory=list)
    connected_components: int
    build_order: list[str] | None = None


class IndexStats(BaseModel):
    """Statistics about the codebase index."""
    total_files: int
    total_symbols: int
    total_edges: int
    total_chunks: int
    languages: dict[str, int] = Field(default_factory=dict,
                                       description="Language -> file count")
    services: dict[str, int] = Field(default_factory=dict,
                                      description="Service -> symbol count")
    last_indexed_at: datetime | None = None
```

### 2.4 Common Models (`src/shared/models/common.py`)

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime


class BuildCycle(BaseModel):
    """Tracks a single build cycle across all services."""
    id: str = Field(..., description="Unique build cycle ID (UUID)")
    project_name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: str = Field(default="running",
                         pattern=r"^(running|completed|failed|paused)$")
    services_planned: int = 0
    services_completed: int = 0
    total_cost_usd: float = 0.0


class ArtifactRegistration(BaseModel):
    """Registration of a newly created file for indexing."""
    file_path: str
    service_name: str
    build_cycle_id: str | None = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Standard health check response for all services."""
    status: str = Field(default="healthy", pattern=r"^(healthy|degraded|unhealthy)$")
    service_name: str
    version: str
    database: str = Field(default="connected",
                           pattern=r"^(connected|disconnected)$")
    uptime_seconds: float
    details: dict = Field(default_factory=dict)
```

---

## 3. Complete Database Schema

All three services use SQLite with WAL mode. Each service has its own database file. The schema uses `TEXT` for timestamps (ISO 8601) and `TEXT` for UUIDs (SQLite has no native UUID type).

**Reference:** BUILD1_TECHNOLOGY_RESEARCH.md Section 5 — SQLite WAL configuration

### 3.1 Contract Engine Database (`contracts.db`)

```sql
-- ===========================================================
-- Contract Engine Database Schema
-- SQLite with WAL mode, foreign keys enabled
-- ===========================================================

-- Build cycle tracking
CREATE TABLE IF NOT EXISTS build_cycles (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK(status IN ('running', 'completed', 'failed', 'paused')),
    services_planned INTEGER NOT NULL DEFAULT 0,
    services_completed INTEGER NOT NULL DEFAULT 0,
    total_cost_usd REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX idx_build_cycles_status ON build_cycles(status);

-- Contract registry — stores OpenAPI, AsyncAPI, and JSON Schema specs
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('openapi', 'asyncapi', 'json_schema')),
    version TEXT NOT NULL,
    service_name TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    spec_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK(status IN ('active', 'deprecated', 'draft')),
    build_cycle_id TEXT REFERENCES build_cycles(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(service_name, type, version)
);

CREATE INDEX idx_contracts_service ON contracts(service_name);
CREATE INDEX idx_contracts_type ON contracts(type);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_build ON contracts(build_cycle_id);
CREATE INDEX idx_contracts_hash ON contracts(spec_hash);

-- Contract version history (append-only log)
CREATE TABLE IF NOT EXISTS contract_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    spec_hash TEXT NOT NULL,
    build_cycle_id TEXT REFERENCES build_cycles(id) ON DELETE SET NULL,
    is_breaking INTEGER NOT NULL DEFAULT 0,
    change_summary TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_versions_contract ON contract_versions(contract_id);
CREATE INDEX idx_versions_build ON contract_versions(build_cycle_id);

-- Breaking changes detected between versions
CREATE TABLE IF NOT EXISTS breaking_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_version_id INTEGER NOT NULL
        REFERENCES contract_versions(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    json_path TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    severity TEXT NOT NULL DEFAULT 'error'
        CHECK(severity IN ('error', 'warning', 'info')),
    affected_consumers TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_breaking_version ON breaking_changes(contract_version_id);

-- Implementation tracking — which services implement which contracts
CREATE TABLE IF NOT EXISTS implementations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('verified', 'pending', 'failed')),
    verified_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(contract_id, service_name)
);

CREATE INDEX idx_impl_contract ON implementations(contract_id);
CREATE INDEX idx_impl_service ON implementations(service_name);
CREATE INDEX idx_impl_status ON implementations(status);

-- Generated test suites
CREATE TABLE IF NOT EXISTS test_suites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    framework TEXT NOT NULL DEFAULT 'pytest'
        CHECK(framework IN ('pytest', 'jest')),
    test_code TEXT NOT NULL,
    test_count INTEGER NOT NULL DEFAULT 0,
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_tests_contract ON test_suites(contract_id);
```

### 3.2 Architect Database (`architect.db`)

```sql
-- ===========================================================
-- Architect Database Schema
-- ===========================================================

-- Service map storage
CREATE TABLE IF NOT EXISTS service_maps (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    prd_hash TEXT NOT NULL,
    map_json TEXT NOT NULL,
    build_cycle_id TEXT,
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_smap_project ON service_maps(project_name);
CREATE INDEX idx_smap_prd ON service_maps(prd_hash);

-- Domain model storage
CREATE TABLE IF NOT EXISTS domain_models (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    model_json TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_dmodel_project ON domain_models(project_name);

-- Decomposition history (for review/audit)
CREATE TABLE IF NOT EXISTS decomposition_runs (
    id TEXT PRIMARY KEY,
    prd_content_hash TEXT NOT NULL,
    service_map_id TEXT REFERENCES service_maps(id),
    domain_model_id TEXT REFERENCES domain_models(id),
    validation_issues TEXT NOT NULL DEFAULT '[]',
    interview_questions TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'running', 'completed', 'failed', 'review')),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
```

### 3.3 Codebase Intelligence Database (`symbols.db`)

```sql
-- ===========================================================
-- Codebase Intelligence Database Schema
-- Metadata is in SQLite; embeddings are in ChromaDB
-- ===========================================================

-- File registry — tracks all indexed files
CREATE TABLE IF NOT EXISTS indexed_files (
    file_path TEXT PRIMARY KEY,
    language TEXT NOT NULL
        CHECK(language IN ('python', 'typescript', 'csharp', 'go', 'unknown')),
    service_name TEXT,
    file_hash TEXT NOT NULL,
    loc INTEGER NOT NULL DEFAULT 0,
    indexed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_files_service ON indexed_files(service_name);
CREATE INDEX idx_files_language ON indexed_files(language);
CREATE INDEX idx_files_hash ON indexed_files(file_hash);

-- Symbol index — all classes, functions, interfaces, types, enums
CREATE TABLE IF NOT EXISTS symbols (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL REFERENCES indexed_files(file_path) ON DELETE CASCADE,
    symbol_name TEXT NOT NULL,
    kind TEXT NOT NULL
        CHECK(kind IN ('class', 'function', 'interface', 'type', 'enum', 'variable', 'method')),
    language TEXT NOT NULL,
    service_name TEXT,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    signature TEXT,
    docstring TEXT,
    is_exported INTEGER NOT NULL DEFAULT 1,
    parent_symbol TEXT,
    chroma_id TEXT,
    indexed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_symbols_file ON symbols(file_path);
CREATE INDEX idx_symbols_name ON symbols(symbol_name);
CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_symbols_service ON symbols(service_name);
CREATE INDEX idx_symbols_language ON symbols(language);
CREATE INDEX idx_symbols_parent ON symbols(parent_symbol);

-- Dependency edges — for graph reconstruction alongside NetworkX
CREATE TABLE IF NOT EXISTS dependency_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_symbol_id TEXT NOT NULL,
    target_symbol_id TEXT NOT NULL,
    relation TEXT NOT NULL
        CHECK(relation IN ('imports', 'calls', 'inherits', 'implements', 'uses')),
    source_file TEXT NOT NULL,
    target_file TEXT NOT NULL,
    line INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_symbol_id, target_symbol_id, relation)
);

CREATE INDEX idx_deps_source ON dependency_edges(source_symbol_id);
CREATE INDEX idx_deps_target ON dependency_edges(target_symbol_id);
CREATE INDEX idx_deps_source_file ON dependency_edges(source_file);
CREATE INDEX idx_deps_target_file ON dependency_edges(target_file);
CREATE INDEX idx_deps_relation ON dependency_edges(relation);

-- Import references — raw import data before symbol resolution
CREATE TABLE IF NOT EXISTS import_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL REFERENCES indexed_files(file_path) ON DELETE CASCADE,
    target_file TEXT NOT NULL,
    imported_names TEXT NOT NULL DEFAULT '[]',
    line INTEGER NOT NULL,
    is_relative INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source_file, target_file, line)
);

CREATE INDEX idx_imports_source ON import_references(source_file);
CREATE INDEX idx_imports_target ON import_references(target_file);

-- Graph snapshots — serialized NetworkX graphs for quick loading
CREATE TABLE IF NOT EXISTS graph_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_json TEXT NOT NULL,
    node_count INTEGER NOT NULL,
    edge_count INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 3.4 SQLite Connection Configuration

All services must initialize connections with the following pragmas (per BUILD1_TECHNOLOGY_RESEARCH.md Section 5):

```python
# src/shared/db/connection.py
import sqlite3
import threading
from pathlib import Path


class ConnectionPool:
    """Thread-local SQLite connection pool with WAL mode."""

    def __init__(self, db_path: str | Path, timeout: float = 30.0):
        self.db_path = str(db_path)
        self.timeout = timeout
        self._local = threading.local()
        # Initialize WAL mode on first connection
        conn = self._create_connection()
        conn.close()

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def get(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection()
        return self._local.conn

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
```

---

## 4. MCP Server Tool Specifications

Each service exposes tools via the MCP Python SDK using the high-level `MCPServer` API with `@mcp.tool()` decorators. All tools use the `stdio` transport for Claude Code integration.

**Reference:** BUILD1_TECHNOLOGY_RESEARCH.md Section 4 — MCP Python SDK

### 4.1 Architect MCP Server (`src/architect/mcp_server.py`)

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="Architect",
    instructions="Query the service decomposition, domain model, and contract assignments.",
    version="1.0.0",
)

@mcp.tool()
def get_service_map() -> dict:
    """Get the complete service decomposition map for the current project.

    Returns the full ServiceMap including all service definitions with their
    domains, technology stacks, estimated LOC, and contract assignments.

    Returns:
        dict with keys:
        - project_name: str
        - services: list of dicts, each with:
            - name: str (e.g. "auth-service")
            - domain: str (e.g. "Authentication & Authorization")
            - description: str
            - stack: dict with backend, database, frontend, message_broker
            - estimated_loc: int
            - owns_entities: list[str]
            - provides_contracts: list[str]
            - consumes_contracts: list[str]
        - generated_at: str (ISO 8601)

    Implementation: Load from architect.db service_maps table, parse map_json,
    return the most recent map for the active project.
    """
    ...

@mcp.tool()
def get_contracts_for_service(service_name: str) -> list[dict]:
    """Get all contracts (both provided and consumed) for a specific service.

    Use this to understand what APIs a service must implement (provides) and
    what external APIs it depends on (consumes).

    Args:
        service_name: The service name (e.g. "auth-service")

    Returns:
        list of dicts, each with:
        - id: str (contract ID)
        - role: str ("provider" or "consumer")
        - type: str ("openapi" or "asyncapi")
        - counterparty: str (the other service in the contract)
        - summary: str (brief description of the contract)

    Implementation: Query service_maps table for the named service,
    extract provides_contracts and consumes_contracts, look up each
    contract ID in the Contract Engine via HTTP.
    """
    ...

@mcp.tool()
def get_domain_model() -> dict:
    """Get the ubiquitous language and domain model for the current project.

    Returns all business entities, their relationships, state machines,
    and cross-domain rules. Use this to understand the data model and
    ensure consistent naming across services.

    Returns:
        dict with keys:
        - entities: list of dicts, each with:
            - name: str (e.g. "User", "Order")
            - description: str
            - owning_service: str
            - fields: list of dicts (name, type, required)
            - state_machine: dict or null (states, transitions)
        - relationships: list of dicts, each with:
            - source_entity: str
            - target_entity: str
            - relationship_type: str (owns, references, triggers, etc.)
            - cardinality: str (1:1, 1:N, N:N)

    Implementation: Load from architect.db domain_models table,
    parse model_json, return the most recent model.
    """
    ...
```

### 4.2 Contract Engine MCP Server (`src/contract_engine/mcp_server.py`)

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="Contract Engine",
    instructions="Store, validate, query, and generate tests from OpenAPI/AsyncAPI contracts. Use this to ensure cross-service API compliance.",
    version="1.0.0",
)

@mcp.tool()
def get_contract(contract_id: str) -> dict:
    """Get a contract by its unique ID with the full specification.

    Args:
        contract_id: The contract's unique identifier (e.g. "auth-user-api-v1")

    Returns:
        dict with keys:
        - id: str
        - type: str ("openapi", "asyncapi", or "json_schema")
        - version: str (semver)
        - service_name: str
        - spec: dict (full OpenAPI/AsyncAPI spec)
        - spec_hash: str (SHA-256)
        - status: str ("active", "deprecated", "draft")
        - created_at: str (ISO 8601)

    Implementation: Query contracts table by id. Parse spec_json.
    Return None if not found.
    """
    ...

@mcp.tool()
def validate_endpoint(
    service_name: str,
    method: str,
    path: str,
    response_body: dict | None = None,
    status_code: int = 200,
) -> dict:
    """Validate an endpoint implementation against its contract.

    Checks that the response body schema matches the contracted schema
    for the given service, method, and path combination.

    Args:
        service_name: Name of the service (e.g. "auth-service")
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path: API path (e.g. "/api/users/{userId}")
        response_body: Actual response body to validate (optional)
        status_code: HTTP status code to validate against (default 200)

    Returns:
        dict with keys:
        - valid: bool
        - violations: list of dicts, each with:
            - field: str (JSON path to the violating field)
            - expected: str (what the contract specifies)
            - actual: str (what the implementation provides)
            - severity: str ("error" or "warning")

    Implementation: Find the OpenAPI contract for service_name. Resolve the
    path+method to an operation. Compare response_body against the response
    schema for the given status_code. Report field-level violations.
    """
    ...

@mcp.tool()
def generate_tests(
    contract_id: str,
    framework: str = "pytest",
    include_negative: bool = True,
) -> str:
    """Generate runnable test code from a contract specification.

    Creates a complete test file that validates an API implementation
    against its contracted schemas using Schemathesis.

    Args:
        contract_id: The contract to generate tests for
        framework: Test framework ("pytest" or "jest")
        include_negative: Include negative test cases (invalid inputs)

    Returns:
        str: Complete test file content ready to write to disk

    Implementation: Load the contract spec. For OpenAPI contracts, generate
    Schemathesis-based pytest tests. For AsyncAPI, generate schema validation
    tests. Include test setup, teardown, and assertions.
    """
    ...

@mcp.tool()
def check_breaking_changes(contract_id: str, new_spec: dict) -> list[dict]:
    """Check if updating a contract spec would break existing consumers.

    Compares the new spec against the current stored spec and identifies
    any breaking changes (removed fields, type changes, removed endpoints).

    Args:
        contract_id: The contract to check
        new_spec: The proposed new specification

    Returns:
        list of dicts, each with:
        - change_type: str (removed_field, type_change, removed_endpoint,
                           added_required_field, changed_status_code)
        - path: str (JSON path to the changed element)
        - old_value: str or null
        - new_value: str or null
        - severity: str ("error" or "warning")
        - affected_consumers: list[str] (service names)

    Implementation: Load current spec from contracts table. Deep-diff the
    two specs. Classify changes as breaking or non-breaking. Look up
    implementations table for affected consumers.
    """
    ...

@mcp.tool()
def mark_implemented(
    contract_id: str,
    service_name: str,
    evidence_path: str,
) -> dict:
    """Mark a contract as implemented by a specific service.

    Called by Builder agents after generating an endpoint that fulfills
    a contract. The evidence_path should point to the implementation file.

    Args:
        contract_id: The contract being implemented
        service_name: The service that implements it
        evidence_path: File path proving the implementation exists

    Returns:
        dict with keys:
        - marked: bool (True if successfully recorded)
        - total_implementations: int (total services implementing this contract)
        - all_implemented: bool (True if all expected consumers have implemented)

    Implementation: Upsert into implementations table with status='pending'.
    Count total implementations for this contract_id.
    """
    ...

@mcp.tool()
def get_unimplemented_contracts(service_name: str | None = None) -> list[dict]:
    """Get all contracts that haven't been fully implemented.

    Use this to find gaps — contracts that were defined but no service
    has registered an implementation for them.

    Args:
        service_name: Optional filter by expected implementing service

    Returns:
        list of dicts, each with:
        - id: str (contract ID)
        - type: str
        - version: str
        - expected_service: str (service that should implement this)
        - status: str ("missing" or "pending" or "failed")

    Implementation: LEFT JOIN contracts with implementations. Return rows
    where implementation is NULL or status != 'verified'.
    """
    ...
```

### 4.3 Codebase Intelligence MCP Server (`src/codebase_intelligence/mcp_server.py`)

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="Codebase Intelligence",
    instructions="Query the live codebase index for symbol definitions, dependencies, semantic search, and dead code detection. Use this to understand code structure without reading entire files.",
    version="1.0.0",
)

@mcp.tool()
def find_definition(symbol: str, language: str | None = None) -> dict | None:
    """Find the exact file and line number where a symbol is defined.

    Searches the AST-based symbol index for classes, functions, interfaces,
    types, and enums matching the given name.

    Args:
        symbol: Name of the symbol to find (e.g. "UserService", "calculate_total")
        language: Optional filter by language ("python", "typescript", "csharp", "go")

    Returns:
        dict with keys:
        - file: str (file path)
        - line: int (line number)
        - kind: str (class, function, interface, type, enum)
        - signature: str (function signature or class declaration)
        - service_name: str or null
        - docstring: str or null
        Returns null if not found.

    Implementation: Query symbols table by symbol_name with optional
    language filter. Return the first match (prefer exported symbols).
    """
    ...

@mcp.tool()
def find_callers(symbol: str, max_results: int = 50) -> list[dict]:
    """Find all call sites for a symbol across the entire codebase.

    Useful for impact analysis: "if I change this function, what breaks?"

    Args:
        symbol: Name of the symbol to find callers for
        max_results: Maximum number of results (default 50, max 200)

    Returns:
        list of dicts, each with:
        - file: str (file path of the calling code)
        - line: int (line number of the call)
        - caller_symbol: str (name of the function/class containing the call)
        - context: str (the line of code containing the call)
        - service_name: str or null

    Implementation: Find the symbol's ID in symbols table. Query
    dependency_edges where target_symbol_id matches and relation
    is 'calls' or 'uses'. Join with symbols for caller info.
    """
    ...

@mcp.tool()
def find_dependencies(file_path: str) -> dict:
    """Get the complete dependency information for a specific file.

    Shows what the file imports, what imports it, and the full transitive
    dependency tree.

    Args:
        file_path: Path to the file (relative to project root)

    Returns:
        dict with keys:
        - imports: list[str] (files this file directly imports)
        - imported_by: list[str] (files that import this file)
        - transitive_deps: list[str] (all files in the dependency tree)
        - circular_deps: list[list[str]] (any circular dependency chains)

    Implementation: Load the NetworkX graph. Use successors() for imports,
    predecessors() for imported_by. Use nx.ancestors() for transitive deps.
    Use nx.simple_cycles() filtered to this file for circular deps.
    """
    ...

@mcp.tool()
def search_semantic(
    query: str,
    language: str | None = None,
    service_name: str | None = None,
    n_results: int = 10,
) -> list[dict]:
    """Semantic search across the codebase using natural language.

    Find code related to a concept even if exact keywords don't appear.
    Example: "payment retry logic" finds retry handlers in billing code.

    Args:
        query: Natural language description of what to find
        language: Optional filter (python, typescript, csharp, go)
        service_name: Optional filter by service
        n_results: Number of results (default 10, max 50)

    Returns:
        list of dicts, each with:
        - file: str (file path)
        - symbol_name: str or null
        - content: str (matched code chunk)
        - score: float (similarity, lower = more similar)
        - language: str
        - service_name: str or null
        - line_start: int
        - line_end: int

    Implementation: Query ChromaDB collection with query_texts=[query].
    Apply metadata filters for language and service_name. Return top
    n_results sorted by distance.
    """
    ...

@mcp.tool()
def get_service_interface(service_name: str) -> dict:
    """Get the complete public API surface for a service.

    Includes HTTP endpoints, published events, consumed events, and
    all exported symbols.

    Args:
        service_name: Name of the service (e.g. "auth-service")

    Returns:
        dict with keys:
        - service_name: str
        - endpoints: list of dicts (path, method, handler function)
        - events_published: list of dicts (event name, channel, schema)
        - events_consumed: list of dicts (event name, channel, handler)
        - exported_symbols: list of dicts (name, kind, file, line)

    Implementation: Query symbols table for service_name with
    is_exported=1. For endpoints, look for route decorators (@app.get,
    @router.post, etc.) in the AST. For events, look for publish/subscribe
    patterns.
    """
    ...

@mcp.tool()
def check_dead_code(service_name: str | None = None) -> list[dict]:
    """Find functions, classes, and interfaces that are defined but never called.

    Identifies potential dead code across the codebase or within a specific
    service. High-confidence results only (excludes entry points, tests,
    and known framework patterns).

    Args:
        service_name: Optional filter by service (null = all services)

    Returns:
        list of dicts, each with:
        - symbol: str (symbol name)
        - file: str (file path)
        - line: int (line number)
        - kind: str (class, function, interface)
        - service_name: str or null
        - confidence: str (high, medium, low)

    Implementation: Find all symbols with no incoming edges in the
    dependency graph (in_degree == 0 in NetworkX). Filter out known
    entry points (main, __init__, route handlers, test functions).
    Classify confidence based on export status and symbol kind.
    """
    ...

@mcp.tool()
def register_artifact(file_path: str, service_name: str) -> dict:
    """Register a newly generated or modified file for indexing.

    Called by Builder agents after generating code. Triggers incremental
    parsing: Tree-sitter AST extraction, dependency graph update, and
    ChromaDB embedding.

    Args:
        file_path: Path to the new/modified file (relative to project root)
        service_name: Which service this file belongs to

    Returns:
        dict with keys:
        - indexed: bool (True if successfully parsed and indexed)
        - symbols_found: int (number of symbols extracted)
        - dependencies_found: int (number of import/call edges found)
        - errors: list[str] (any parsing errors)

    Implementation: Read the file, detect language from extension.
    Parse with tree-sitter. Extract symbols → insert into symbols table.
    Extract imports → resolve paths → insert into dependency_edges.
    Generate code chunks → upsert into ChromaDB. Update NetworkX graph.
    """
    ...
```

---

## 5. Service Architecture

### 5.1 Architect Service

**Entry point:** `src/architect/main.py` — FastAPI app

```
Request flow:
  POST /api/decompose (PRD text)
    → prd_parser.py: extract entities, relationships, bounded contexts
    → service_boundary.py: group into services using DDD principles
    → validator.py: check no cycles, no overlap, entity completeness
    → contract_generator.py: generate OpenAPI/AsyncAPI stubs
    → domain_modeler.py: build domain model
    → service_map_store.py: persist to SQLite
    → Return DecompositionResult
```

**Core modules:**

| Module | Dependencies | Async? |
|--------|-------------|--------|
| `prd_parser.py` | None (pure text processing) | No |
| `service_boundary.py` | `prd_parser` output | No |
| `contract_generator.py` | `service_boundary` output, `openapi_validator` | No |
| `domain_modeler.py` | `prd_parser` output, `service_boundary` output | No |
| `validator.py` | `networkx` (cycle detection) | No |
| `service_map_store.py` | `shared.db.connection` | No |

**Error handling:** All errors propagate as HTTPExceptions with structured error bodies. Validation errors return 422. Not-found errors return 404. Internal errors return 500 with logged traceback.

### 5.2 Contract Engine Service

**Entry point:** `src/contract_engine/main.py` — FastAPI app

```
Request flow (store contract):
  POST /api/contracts
    → openapi_validator.py or asyncapi_validator.py: validate spec
    → version_manager.py: check immutability within build cycle
    → breaking_change_detector.py: compare with previous version
    → contract_store.py: upsert with hash-based change detection
    → Return ContractEntry

Request flow (generate tests):
  POST /api/tests/generate
    → contract_store.py: load contract spec
    → test_generator.py: generate Schemathesis-based tests
    → Return ContractTestSuite

Request flow (validate endpoint):
  POST /api/validate
    → contract_store.py: load contract for service
    → compliance_checker.py: compare response against schema
    → Return ComplianceResult
```

**Core modules:**

| Module | Dependencies | Async? |
|--------|-------------|--------|
| `contract_store.py` | `shared.db.connection`, `hashlib` | No |
| `openapi_validator.py` | `openapi-spec-validator`, `prance` | No |
| `asyncapi_parser.py` | `pyyaml`, `jsonschema` | No |
| `asyncapi_validator.py` | `asyncapi_parser`, `jsonschema` | No |
| `schema_registry.py` | `contract_store` | No |
| `version_manager.py` | `contract_store`, `hashlib` | No |
| `breaking_change_detector.py` | `contract_store` | No |
| `test_generator.py` | `schemathesis`, `contract_store` | No |
| `compliance_checker.py` | `jsonschema`, `contract_store` | No |
| `implementation_tracker.py` | `shared.db.connection` | No |

**Immutability enforcement:** `version_manager.py` rejects any `update_contract()` call where the `build_cycle_id` matches an existing record. New versions require a new `build_cycle_id` (only the Super Orchestrator can create new build cycles).

### 5.3 Codebase Intelligence Service

**Entry point:** `src/codebase_intelligence/mcp_server.py` — MCP Server (PRIMARY)
**Secondary:** `src/codebase_intelligence/main.py` — FastAPI app (for Docker health checks and REST access)

```
Indexing flow:
  register_artifact(file_path, service_name)
    → ast_parser.py: parse file with tree-sitter (language auto-detected)
    → symbol_extractor.py: extract all symbols (classes, functions, etc.)
    → import_resolver.py: resolve import paths to actual files
    → graph_builder.py: add nodes/edges to NetworkX DiGraph
    → semantic_indexer.py: generate code chunks → embed in ChromaDB
    → symbol_db.py: persist to SQLite
    → graph_db.py: persist edges to SQLite

Query flow:
  find_definition(symbol)
    → symbol_db.py: query symbols table by name
    → Return SymbolDefinition

  search_semantic(query)
    → chroma_store.py: query ChromaDB collection
    → Return list[SemanticSearchResult]

  find_dependencies(file)
    → graph_analyzer.py: load NetworkX graph, compute paths
    → Return dependency info

  check_dead_code()
    → graph_analyzer.py: find nodes with in_degree == 0
    → Filter known entry points
    → Return list[DeadCodeEntry]
```

**Core modules:**

| Module | Dependencies | Async? |
|--------|-------------|--------|
| `ast_parser.py` | `tree-sitter`, language grammars | No |
| `symbol_extractor.py` | `ast_parser` (tree-sitter queries) | No |
| `import_resolver.py` | `pathlib`, language-specific rules | No |
| `graph_builder.py` | `networkx` | No |
| `graph_analyzer.py` | `networkx` (pagerank, cycles, paths) | No |
| `semantic_indexer.py` | `chromadb` | No |
| `semantic_searcher.py` | `chromadb` | No |
| `dead_code_detector.py` | `graph_analyzer` | No |
| `incremental_indexer.py` | All of the above | No |
| `python_parser.py` | `tree-sitter-python` | No |
| `typescript_parser.py` | `tree-sitter-typescript` | No |
| `csharp_parser.py` | `tree-sitter-c-sharp` | No |
| `go_parser.py` | `tree-sitter-go` | No |
| `symbol_db.py` | `shared.db.connection` | No |
| `graph_db.py` | `shared.db.connection`, `networkx` JSON serialization | No |
| `chroma_store.py` | `chromadb.PersistentClient` | No |

**Tree-sitter language detection:** File extension mapping:
- `.py` → Python (`tree_sitter_python.language()`)
- `.ts`, `.tsx` → TypeScript (`tree_sitter_typescript.language_typescript()` / `.language_tsx()`)
- `.cs` → C# (`tree_sitter_c_sharp.language()`)
- `.go` → Go (`tree_sitter_go.language()`)

---

## 6. Milestone Breakdown (8 Milestones)

### M1: Core Data Models + Shared Infrastructure

**Scope:** Project scaffolding, all Pydantic models, SQLite schema, Docker base, shared utilities.

**Files delivered:**
- `pyproject.toml` — project metadata with all dependencies
- `src/shared/` — all 8 files (models, db, config, logging, errors, constants)
- `docker-compose.yml` — skeleton with 3 services
- `docker/*/Dockerfile` — 3 Dockerfiles
- `docker/*/requirements.txt` — 3 requirements files
- `.mcp.json` — MCP server configuration
- `tests/conftest.py` + `tests/test_shared/` — 3 test files

**Dependencies:** None (first milestone)

**Deliverables:**
- All Pydantic models importable and passing validation tests
- SQLite database creation with all tables via `schema.py`
- Docker Compose starts all 3 containers (empty FastAPI apps with /health)
- Connection pool creates WAL-mode connections

**Success criteria:**
- `pytest tests/test_shared/` passes with 100% of tests
- `docker compose up` starts all 3 services and health checks pass
- All models serialize/deserialize correctly (roundtrip tests)

**Estimated complexity:** ~2,500 LOC, ~25 files

**Testing requirements:**
- Model validation tests (valid/invalid inputs for every model)
- SQLite connection pool tests (thread safety, WAL mode)
- Docker Compose health check integration test

---

### M2: Architect Service

**Scope:** PRD parsing, service boundary identification, contract stub generation, domain modeling, validation, FastAPI endpoints.

**Files delivered:**
- `src/architect/` — all 14 files
- `tests/test_architect/` — 7 test files
- `sample_data/sample_prd.md`
- `sample_data/sample_service_map.yaml`

**Dependencies:** milestone-1

**Deliverables:**
- POST /api/decompose accepts PRD text, returns DecompositionResult
- GET /api/service-map returns stored ServiceMap
- GET /api/domain-model returns stored DomainModel
- Validation catches: circular dependencies, entity overlap, orphan entities
- Sample PRD produces a realistic 5-service decomposition

**Success criteria:**
- Architect produces valid ServiceMap from sample PRD (all fields populated)
- Validator rejects a PRD with circular service dependencies
- Domain model includes all entities from PRD with correct ownership
- Contract stubs are valid OpenAPI 3.1 YAML
- All FastAPI endpoints return correct response codes (201, 200, 404, 422)

**Estimated complexity:** ~4,000 LOC, ~21 files

**Testing requirements:**
- PRD parser extracts entities from multiple PRD formats
- Service boundary algorithm produces non-overlapping services
- Validator detects planted bugs (cycles, overlap, missing entities)
- Router integration tests with TestClient

---

### M3: Contract Engine Core

**Scope:** Contract CRUD, OpenAPI validation, AsyncAPI parser + validation, versioning with immutability, breaking change detection.

**Files delivered:**
- `src/contract_engine/` — all files EXCEPT `test_generator.py` and `mcp_server.py`
- `tests/test_contract_engine/` — 8 test files (excluding test_generator, mcp)
- `sample_data/sample_openapi.yaml`
- `sample_data/sample_asyncapi.yaml`

**Dependencies:** milestone-1

**Deliverables:**
- CRUD for contracts via FastAPI endpoints
- OpenAPI 3.1 validation using openapi-spec-validator + prance for $ref resolution
- AsyncAPI 3.0 parser (~500 lines) using pyyaml + jsonschema
- Version tracking with immutability within a build cycle
- Breaking change detection between versions
- Implementation tracking (mark_implemented, get_unimplemented)

**Success criteria:**
- Store and retrieve OpenAPI and AsyncAPI contracts
- Reject invalid OpenAPI specs with clear error messages
- Parse AsyncAPI 3.0 spec and extract channels, operations, schemas
- Reject contract update within same build_cycle_id (immutability)
- Detect breaking changes: removed field, type change, removed endpoint
- Implementation tracker correctly reports unimplemented contracts

**Estimated complexity:** ~5,500 LOC, ~20 files

**Testing requirements:**
- OpenAPI validation: valid spec passes, invalid spec fails with errors
- AsyncAPI parser: parses sample spec, extracts all channels/operations
- Immutability: attempt to update within same build cycle is rejected
- Breaking change: detect 5 types of breaking changes
- CRUD: create, read, list, delete, filter by service/type

---

### M4: Contract Test Generation

**Scope:** Schemathesis integration, test suite generation from contracts, compliance checker.

**Files delivered:**
- `src/contract_engine/services/test_generator.py`
- `src/contract_engine/services/compliance_checker.py`
- `src/contract_engine/routers/tests.py` (new endpoints)
- `tests/test_contract_engine/test_test_generator.py`
- `tests/test_contract_engine/test_compliance_checker.py`

**Dependencies:** milestone-3

**Deliverables:**
- Generate runnable pytest test files from OpenAPI contracts using Schemathesis
- Compliance checker validates actual API response against contracted schema
- Generated tests cover: schema conformance, status codes, required fields

**Success criteria:**
- Generated test file is valid Python that imports and runs
- Generated tests use Schemathesis `@schema.parametrize()` pattern
- Compliance checker detects: missing field, wrong type, extra required field
- End-to-end: store contract → generate tests → tests are runnable

**Estimated complexity:** ~2,000 LOC, ~5 files

**Testing requirements:**
- Generated test code compiles and is importable
- Compliance checker catches 5 planted violations
- Test generation for AsyncAPI produces schema validation tests

---

### M5: Codebase Intelligence Layer 1+2

**Scope:** Tree-sitter AST parsing for 4 languages, symbol extraction, import resolution, NetworkX dependency graph, dead code detection.

**Files delivered:**
- `src/codebase_intelligence/services/ast_parser.py`
- `src/codebase_intelligence/services/symbol_extractor.py`
- `src/codebase_intelligence/services/import_resolver.py`
- `src/codebase_intelligence/services/graph_builder.py`
- `src/codebase_intelligence/services/graph_analyzer.py`
- `src/codebase_intelligence/services/dead_code_detector.py`
- `src/codebase_intelligence/parsers/` — 4 language-specific parsers
- `src/codebase_intelligence/storage/symbol_db.py`
- `src/codebase_intelligence/storage/graph_db.py`
- `tests/test_codebase_intelligence/` — 8 test files
- `sample_data/sample_codebase/` — test files in Python + TypeScript

**Dependencies:** milestone-1

**Deliverables:**
- Parse Python, TypeScript, C#, Go files with tree-sitter
- Extract classes, functions, interfaces, types, enums with line numbers
- Resolve import paths to actual files for all 4 languages
- Build NetworkX DiGraph from imports/calls/inherits relationships
- PageRank ranking of file importance
- Circular dependency detection
- Dead code detection (defined but never referenced)
- SQLite persistence for symbols and edges
- NetworkX JSON serialization for graph snapshots

**Success criteria:**
- Parse 1000-line Python file and extract all symbols with correct line numbers
- Parse TypeScript file with interfaces and exported functions
- Resolve relative and absolute imports for Python and TypeScript
- Build graph with 50+ nodes and detect planted circular dependency
- PageRank produces sensible ranking (high-import files rank highest)
- Dead code detector finds planted unused functions
- Index 10K LOC sample codebase in under 5 seconds

**Estimated complexity:** ~6,000 LOC, ~18 files

**Testing requirements:**
- AST parsing: each language has 10+ test cases with known expected output
- Import resolution: relative, absolute, package, wildcard imports
- Graph algorithms: cycle detection, pagerank, topological sort
- Dead code: known dead functions found, known live functions excluded
- Performance: 10K LOC indexed in <5s

---

### M6: Codebase Intelligence Layer 3 + MCP Server

**Scope:** ChromaDB semantic search, MCP server with all 7 tools, incremental indexing.

**Files delivered:**
- `src/codebase_intelligence/services/semantic_indexer.py`
- `src/codebase_intelligence/services/semantic_searcher.py`
- `src/codebase_intelligence/services/incremental_indexer.py`
- `src/codebase_intelligence/services/service_interface_extractor.py`
- `src/codebase_intelligence/storage/chroma_store.py`
- `src/codebase_intelligence/mcp_server.py`
- `tests/test_codebase_intelligence/test_semantic_*` — 3 test files
- `tests/test_codebase_intelligence/test_mcp_tools.py`

**Dependencies:** milestone-5

**Deliverables:**
- ChromaDB PersistentClient with code chunk embeddings
- Semantic search that finds conceptually related code
- 7 MCP tools fully functional via stdio transport
- Incremental indexing: register_artifact triggers parse+index
- Service interface extraction: public APIs per service

**Success criteria:**
- Semantic search for "payment processing" returns billing-related code
- MCP tools respond correctly when called via MCP client
- Incremental indexing: add a file, immediately queryable
- Service interface: correctly lists endpoints, events, exports
- ChromaDB persistence: restart service, data still available
- Index 50K LOC codebase in under 60 seconds

**Estimated complexity:** ~4,000 LOC, ~10 files

**Testing requirements:**
- Semantic search relevance: top-3 results are correct for 5 test queries
- MCP roundtrip: client calls tool → server processes → client receives response
- Incremental: register file → find_definition returns it
- Persistence: create collection → restart → data preserved

---

### M7: Architect MCP + Contract Engine MCP

**Scope:** MCP servers for Architect and Contract Engine, end-to-end tool testing.

**Files delivered:**
- `src/architect/mcp_server.py` — 3 MCP tools
- `src/contract_engine/mcp_server.py` — 6 MCP tools
- `tests/test_architect/test_mcp_tools.py`
- `tests/test_contract_engine/test_mcp_tools.py`
- `tests/test_integration/test_mcp_roundtrip.py`

**Dependencies:** milestone-2, milestone-3, milestone-4

**Deliverables:**
- Architect MCP with 3 tools: get_service_map, get_contracts_for_service, get_domain_model
- Contract Engine MCP with 6 tools: get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts
- End-to-end test: PRD → Architect → contracts → Contract Engine → MCP query

**Success criteria:**
- All 9 MCP tools respond via stdio transport
- End-to-end: decompose PRD → store contracts → query contract via MCP → get response
- Tool descriptions are clear enough for Claude to select the right tool
- Type annotations produce correct JSON Schema in MCP tool listing

**Estimated complexity:** ~2,500 LOC, ~5 files

**Testing requirements:**
- Each MCP tool tested with valid and invalid inputs
- MCP client integration test (call each tool)
- End-to-end integration test spanning all 3 services

---

### M8: Integration + Docker + E2E Tests

**Scope:** Full Docker Compose with health checks, inter-service communication, CLI, sample data, documentation.

**Files delivered:**
- `docker-compose.yml` — complete with health checks, depends_on, volumes
- `docker/*/Dockerfile` — finalized with proper layers
- `.mcp.json` — complete configuration
- `tests/test_integration/` — 4 E2E test files
- `docs/` — 4 documentation files
- `sample_data/` — all sample data finalized

**Dependencies:** milestone-6, milestone-7

**Deliverables:**
- Docker Compose starts all 3 services with health checks passing
- Services communicate via internal Docker network
- Architect can call Contract Engine API to register generated contracts
- Codebase Intelligence can reach Contract Engine for contract-aware indexing
- Full E2E test: PRD → decompose → store contracts → index sample code → query
- Documentation: architecture overview, API reference, MCP tools, deployment

**Success criteria:**
- `docker compose up` — all 3 services healthy within 60 seconds
- Health endpoints return 200 with correct HealthStatus for all services
- E2E test passes: decompose sample PRD → contracts stored → index sample codebase → query MCP tools
- All MCP tools work from Claude Code (verify with .mcp.json)
- Documentation is complete and accurate

**Estimated complexity:** ~3,000 LOC, ~15 files

**Testing requirements:**
- Docker Compose health check integration test
- Inter-service HTTP communication test
- Full pipeline E2E test (PRD to MCP query)
- MCP server startup and tool listing test

---

## 7. Data Flow Diagrams

### 7.1 PRD Decomposition Flow

```
PRD Text (markdown)
    │
    ▼
[Architect: prd_parser.py]
    │ Extract: entities, relationships, bounded contexts
    ▼
[Architect: service_boundary.py]
    │ Group entities into service boundaries (DDD)
    ▼
[Architect: validator.py]
    │ Check: no cycles, no overlap, completeness
    │ Uses: NetworkX DiGraph for cycle detection
    ▼
[Architect: contract_generator.py]
    │ Generate: OpenAPI 3.1 stubs for HTTP APIs
    │ Generate: AsyncAPI 3.0 stubs for event channels
    ▼
[Architect: domain_modeler.py]
    │ Build: entity definitions, relationships, state machines
    ▼
ServiceMap (YAML) + Contract Stubs (dict[]) + DomainModel
    │
    ├──► [architect.db] — persist ServiceMap + DomainModel
    │
    └──► [Contract Engine: /api/contracts] — register each contract stub
             │
             ├──► [contracts.db] — persist with hash + version
             └──► Return: ContractEntry[] with IDs
```

### 7.2 Contract Lifecycle Flow

```
Contract Registration:
    Architect POST /api/contracts
        │
        ▼
    [openapi_validator.py] or [asyncapi_validator.py]
        │ Validate spec structure
        ▼
    [version_manager.py]
        │ Check: immutability within build_cycle_id
        │ Compute: SHA-256 hash of spec JSON
        ▼
    [contract_store.py]
        │ Upsert into contracts table
        │ Append to contract_versions table
        ▼
    ContractEntry (id, hash, version)

Contract Test Generation:
    Builder GET /api/tests/generate/{contract_id}
        │
        ▼
    [contract_store.py] — load spec
        │
        ▼
    [test_generator.py]
        │ For OpenAPI: generate Schemathesis @schema.parametrize() tests
        │ For AsyncAPI: generate schema validation tests
        ▼
    ContractTestSuite (test_code: str)

Implementation Tracking:
    Builder calls mark_implemented(contract_id, service, evidence)
        │
        ▼
    [implementation_tracker.py]
        │ Upsert into implementations table
        ▼
    Integrator calls get_unimplemented_contracts()
        │ LEFT JOIN contracts with implementations
        ▼
    list[UnimplementedContract]
```

### 7.3 Codebase Indexing Flow

```
Source File (Python/TypeScript/C#/Go)
    │
    ▼
[ast_parser.py]
    │ Detect language from extension
    │ Parse with tree-sitter → AST
    ▼
[symbol_extractor.py]
    │ Query AST for classes, functions, interfaces
    │ Extract: name, line, signature, docstring, exports
    ▼
[import_resolver.py]
    │ Extract import statements from AST
    │ Resolve import paths to actual file paths
    ▼
Symbols[] + ImportReferences[]
    │
    ├──► [symbol_db.py] → symbols table in symbols.db
    │
    ├──► [graph_builder.py] → NetworkX DiGraph
    │        Nodes = file paths with metadata
    │        Edges = imports/calls/inherits with relation type
    │
    ├──► [graph_db.py] → dependency_edges table + graph_snapshots
    │
    └──► [semantic_indexer.py] → ChromaDB collection
             Generate code chunks (symbol + docstring)
             Embed with all-MiniLM-L6-v2 (default, local)
             Store with metadata (file, service, language, lines)

Query flows:
    find_definition(symbol) → symbol_db.py → SQLite query
    find_callers(symbol) → graph_analyzer.py → NetworkX predecessors
    find_dependencies(file) → graph_analyzer.py → NetworkX ancestors/descendants
    search_semantic(query) → chroma_store.py → ChromaDB.query()
    check_dead_code() → graph_analyzer.py → in_degree == 0, filtered
    register_artifact(file) → incremental_indexer.py → full pipeline above
```

### 7.4 MCP Query Flow

```
Claude Code Agent
    │
    │ tool call via stdio
    ▼
[MCP Server (stdio transport)]
    │
    │ @mcp.tool() handler
    ▼
[Service Layer]
    │
    ├──► SQLite (symbols, contracts)
    ├──► ChromaDB (semantic search)
    ├──► NetworkX (dependency graph, in-memory)
    │
    ▼
Structured Response (dict/list)
    │
    │ JSON serialization
    ▼
Claude Code Agent (receives tool result)
```

---

## 8. Integration Points with Build 2 and Build 3

### 8.1 Build 2 (Builder Fleet) Consumes Build 1

**Which MCP tools does Build 2 call?**

| Build 2 Agent | MCP Server | Tool | Parameters | Purpose |
|---------------|-----------|------|------------|---------|
| Code Writer | Contract Engine | `get_contract(contract_id)` | Contract ID from REQUIREMENTS.md SVC-xxx | Get the exact API schema to implement against |
| Code Writer | Codebase Intel | `search_semantic(query)` | Natural language query about related code | Find existing patterns to follow |
| Code Writer | Codebase Intel | `register_artifact(file, service)` | Path to newly created file | Index new code for other agents |
| Code Reviewer | Contract Engine | `validate_endpoint(service, method, path, body)` | Endpoint details from code review | Verify implementation matches contract |
| Code Reviewer | Codebase Intel | `find_callers(symbol)` | Changed symbol name | Verify no callers are broken |
| Architect Agent | Architect | `get_service_map()` | None | Understand service decomposition |
| Architect Agent | Architect | `get_contracts_for_service(service)` | Service being built | Get all contracts for this service |
| Architect Agent | Architect | `get_domain_model()` | None | Get entity definitions and relationships |
| Test Runner | Contract Engine | `generate_tests(contract_id)` | Contract ID | Generate contract conformance tests |
| Debug Agent | Codebase Intel | `find_definition(symbol)` | Error-related symbol | Find where a symbol is defined |
| Debug Agent | Codebase Intel | `find_dependencies(file)` | File with errors | Understand dependency chain |

**Data format:** All tools return JSON dicts/lists as specified in Section 4.

### 8.2 Build 3 (Integrator + Quality Gate) Consumes Build 1

| Build 3 System | MCP Server | Tool | Parameters | Purpose |
|----------------|-----------|------|------------|---------|
| Integrator | Contract Engine | `get_unimplemented_contracts()` | None or service_name | Find gaps in implementation |
| Integrator | Contract Engine | `get_contract(id)` | Each contract ID | Get specs for integration test generation |
| Quality Gate L2 | Contract Engine | `validate_endpoint(...)` | Per endpoint | Verify deployed API matches contract |
| Quality Gate L2 | Contract Engine | `check_breaking_changes(id, spec)` | Contract + live spec | Detect drift from original contract |
| Quality Gate L4 | Codebase Intel | `check_dead_code()` | None | Find dead events/contracts system-wide |
| Quality Gate L4 | Codebase Intel | `get_service_interface(service)` | Each service | Verify all published events are consumed |
| Super Orchestrator | Architect | `get_service_map()` | None | Know how many builders to spawn |

### 8.3 .mcp.json Configuration for Downstream Builds

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

For Docker Compose deployment, services communicate via HTTP:
```
Architect         → http://contract-engine:8000/api/contracts  (register stubs)
Codebase Intel    → http://contract-engine:8000/api/contracts  (contract-aware indexing)
Builder (Build 2) → MCP stdio to each service (local .mcp.json)
Integrator (B3)   → HTTP to all services (Docker network)
```

---

## 9. Configuration Design

### 9.1 config.yaml for Building Build 1 with agent-team

This config is used when running `agent-team` against the Build 1 PRD.

```yaml
# Agent Team Configuration — Build 1: Super Team Foundation
# Optimized for a Python infrastructure project (no frontend, no UI)

# Use thorough depth for infrastructure (many integration points)
depth: "thorough"

# Orchestrator
orchestrator:
  model: "claude-sonnet-4-20250514"
  max_turns: 250
  permission_mode: "plan"

# Fleet — infrastructure project benefits from review parallelism
fleet:
  coding: 1
  review: 1
  debug: 1

# Convergence — strict for infrastructure code
convergence:
  min_convergence_ratio: 0.95
  max_review_cycles: 5
  recovery_threshold: 0.8

# Quality — all checks on, infrastructure code is critical
quality:
  spot_checks: true
  craft_review: true
  production_defaults: true

# Milestone — 8 milestones, strict health gating
milestone:
  enabled: true
  health_gate: true
  wiring_check: true
  review_recovery_retries: 3

# Post-orchestration scans — most relevant for Python infra
post_orchestration_scans:
  mock_data_scan: true          # Critical — no mock data in infrastructure
  ui_compliance_scan: false     # No UI in Build 1
  api_contract_scan: true       # FastAPI endpoints must match specs
  silent_data_loss_scan: false  # No CQRS in Build 1
  endpoint_xref_scan: false     # No frontend
  max_scan_fix_passes: 3

# Integrity scans
integrity_scans:
  deployment_scan: true          # Docker Compose cross-reference
  asset_scan: false              # No static assets
  prd_reconciliation: true       # Verify PRD coverage

# Database scans — SQLite, no ORM mix
database_scans:
  dual_orm_scan: false           # Single ORM (raw SQLite)
  default_value_scan: true       # Catch missing defaults
  relationship_scan: false       # No ORM relationships

# Design reference — no UI
design_reference:
  enabled: false

# Tech research — critical for infrastructure dependencies
tech_research:
  enabled: true
  max_techs: 6
  max_queries_per_tech: 3

# E2E testing — test the APIs
e2e_testing:
  enabled: true
  backend_api_tests: true
  frontend_playwright_tests: false
  max_fix_retries: 3
  test_port: 9876
  skip_if_no_api: true
  skip_if_no_frontend: true

# Browser testing — no browser UI
browser_testing:
  enabled: false

# Tracking documents
tracking_documents:
  e2e_coverage_matrix: true
  fix_cycle_log: true
  milestone_handoff: true
  coverage_completeness_gate: 0.8
  wiring_completeness_gate: 1.0

# Verification
verification:
  enabled: true
```

### 9.2 Service-level Configuration (`src/shared/config.py`)

```python
from pydantic_settings import BaseSettings
from pydantic import Field


class SharedConfig(BaseSettings):
    """Shared configuration loaded from environment variables."""
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    database_path: str = Field(default="./data/service.db", alias="DATABASE_PATH")

    model_config = {"env_prefix": "", "case_sensitive": False}


class ArchitectConfig(SharedConfig):
    contract_engine_url: str = Field(
        default="http://contract-engine:8000",
        alias="CONTRACT_ENGINE_URL",
    )
    codebase_intel_url: str = Field(
        default="http://codebase-intel:8000",
        alias="CODEBASE_INTEL_URL",
    )


class ContractEngineConfig(SharedConfig):
    # No additional fields needed — self-contained
    pass


class CodebaseIntelConfig(SharedConfig):
    chroma_path: str = Field(default="./data/chroma", alias="CHROMA_PATH")
    graph_path: str = Field(default="./data/graph.json", alias="GRAPH_PATH")
    contract_engine_url: str = Field(
        default="http://contract-engine:8000",
        alias="CONTRACT_ENGINE_URL",
    )
```

---

## 10. Risk Mitigations

### Risk 1: AsyncAPI Parser Gap

**Risk:** No mature Python library for AsyncAPI 3.0 parsing exists.
**Source:** SUPER_TEAM_RESEARCH_REPORT.md Correction 2

**Mitigation:**
- Build a lightweight parser (~500 lines) in `src/contract_engine/services/asyncapi_parser.py`
- Use `pyyaml` for YAML loading and `jsonschema` for schema validation
- Parse only the sections needed: `info`, `channels`, `operations`, `components/messages`, `components/schemas`
- Handle `$ref` resolution only for `#/components/*` local references (no external file refs)
- Return `AsyncAPISpec` dataclass with `channels`, `operations`, `schemas`
- Include `validate_asyncapi()` function that checks structural completeness
- Test against the sample spec in `sample_data/sample_asyncapi.yaml`
- Exact implementation pattern documented in BUILD1_TECHNOLOGY_RESEARCH.md Section 9

### Risk 2: SQLite Concurrency

**Risk:** Multiple Build 2 agents writing to SQLite simultaneously during parallel builds.
**Source:** SUPER_TEAM_RESEARCH_REPORT.md Gap 5

**Mitigation:**
- **WAL mode** (`PRAGMA journal_mode=WAL`) — allows concurrent readers with one writer
- **busy_timeout=30000** (30 seconds) — prevents immediate SQLITE_BUSY errors
- **Thread-local connections** via `ConnectionPool` class (one connection per thread)
- **Per-service databases** — each service has its own `.db` file (architect.db, contracts.db, symbols.db), so writes to different services don't contend
- **Short transactions** — use `BEGIN IMMEDIATE` for write transactions, keep them brief
- **ChromaDB handles its own concurrency** — no custom locking needed for vector operations
- Connection pool pattern documented in BUILD1_TECHNOLOGY_RESEARCH.md Section 5

### Risk 3: MCP SDK Stability

**Risk:** MCP Python SDK is v1.x with v2.x planned; API surface may change.
**Source:** SUPER_TEAM_RESEARCH_REPORT.md Correction 5

**Mitigation:**
- Pin to `mcp>=1.25,<2` in requirements
- All MCP tool functions are plain Python functions decorated with `@mcp.tool()` — if the decorator API changes, the business logic is unaffected
- Isolate MCP concerns in dedicated `mcp_server.py` files (one per service) — the service layer has no MCP imports
- Use the high-level `MCPServer` API (not the low-level `Server` class) — this is the stable public API
- If MCP SDK v2 breaks the decorator pattern, only 3 files need updating

### Risk 4: Windows Compatibility

**Risk:** Omar's primary platform is Windows 11. Path handling, process isolation, and Docker Desktop differ.
**Source:** SUPER_TEAM_RESEARCH_REPORT.md Gap 4 and Risk 6

**Mitigation:**
- Use `pathlib.Path` everywhere — no string concatenation for paths
- All file I/O uses `encoding="utf-8"` explicitly
- Docker Compose tested on Docker Desktop for Windows (uses WSL2 backend)
- SQLite database paths use `Path` objects that normalize separators
- Tree-sitter language grammars use pre-built binary wheels (pip install works on Windows)
- ChromaDB PersistentClient path uses forward slashes internally
- No Unix-specific process isolation (no signals, no fork) — use `subprocess` with `CREATE_NEW_PROCESS_GROUP` if needed

### Risk 5: Tree-sitter Grammar Compatibility

**Risk:** Tree-sitter grammar packages must match the core ABI version.
**Source:** BUILD1_TECHNOLOGY_RESEARCH.md Section 1 Gotchas

**Mitigation:**
- Pin all tree-sitter packages to compatible versions:
  - `tree-sitter==0.25.2`
  - `tree-sitter-python==0.25.0`
  - `tree-sitter-typescript==0.23.2`
  - `tree-sitter-c-sharp==0.23.1`
  - `tree-sitter-go==0.25.0`
- Test each language parser in CI with a known source file
- If a grammar package has ABI mismatch, fall back to `tree-sitter-language-pack`
- TypeScript requires using `language_typescript()` for `.ts` and `language_tsx()` for `.tsx` — never mix these

### Risk 6: ChromaDB First-Use Download

**Risk:** Default embedding model (all-MiniLM-L6-v2) downloads ~80MB on first use.
**Source:** BUILD1_TECHNOLOGY_RESEARCH.md Section 2 Gotchas

**Mitigation:**
- Pre-download the model in the Dockerfile: `RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; DefaultEmbeddingFunction()"`
- For local development, document that first run may take 30-60 seconds for model download
- Store the model in the Docker volume so it persists across restarts
- If offline usage is needed, bundle the model in the Docker image

---

## Appendix A: Dependency Versions (pyproject.toml)

```toml
[project]
name = "super-team"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    # Web framework
    "fastapi==0.129.0",
    "uvicorn>=0.30.0",
    "httpx>=0.27.0",

    # MCP SDK
    "mcp>=1.25,<2",

    # AST parsing
    "tree-sitter==0.25.2",
    "tree-sitter-python==0.25.0",
    "tree-sitter-typescript==0.23.2",
    "tree-sitter-c-sharp==0.23.1",
    "tree-sitter-go==0.25.0",

    # Vector search
    "chromadb==1.5.0",

    # Graph analysis
    "networkx==3.6.1",

    # OpenAPI validation
    "openapi-spec-validator>=0.7.0",
    "prance>=25.0.0",

    # AsyncAPI support
    "pyyaml>=6.0",
    "jsonschema>=4.20.0",

    # Contract testing
    "schemathesis==4.10.1",

    # Configuration
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",

    # Utilities
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.5.0",
    "mypy>=1.8.0",
]
```

---

## Appendix B: Docker Compose (Complete)

```yaml
version: "3.8"

services:
  architect:
    build:
      context: .
      dockerfile: docker/architect/Dockerfile
    container_name: super-team-architect
    ports:
      - "8001:8000"
    environment:
      - DATABASE_PATH=/data/architect.db
      - CONTRACT_ENGINE_URL=http://contract-engine:8000
      - CODEBASE_INTEL_URL=http://codebase-intel:8000
      - LOG_LEVEL=info
    volumes:
      - architect-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    depends_on:
      contract-engine:
        condition: service_healthy
    networks:
      - super-team-net
    restart: unless-stopped

  contract-engine:
    build:
      context: .
      dockerfile: docker/contract_engine/Dockerfile
    container_name: super-team-contract-engine
    ports:
      - "8002:8000"
    environment:
      - DATABASE_PATH=/data/contracts.db
      - LOG_LEVEL=info
    volumes:
      - contract-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - super-team-net
    restart: unless-stopped

  codebase-intel:
    build:
      context: .
      dockerfile: docker/codebase_intelligence/Dockerfile
    container_name: super-team-codebase-intel
    ports:
      - "8003:8000"
    environment:
      - DATABASE_PATH=/data/symbols.db
      - CHROMA_PATH=/data/chroma
      - GRAPH_PATH=/data/graph.json
      - CONTRACT_ENGINE_URL=http://contract-engine:8000
      - LOG_LEVEL=info
    volumes:
      - intel-data:/data
      - ./target-codebase:/codebase:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
    depends_on:
      contract-engine:
        condition: service_healthy
    networks:
      - super-team-net
    restart: unless-stopped

volumes:
  architect-data:
    driver: local
  contract-data:
    driver: local
  intel-data:
    driver: local

networks:
  super-team-net:
    driver: bridge
```

---

## Appendix C: Milestone Dependency Graph

```
M1 (Core Models + Shared)
  │
  ├──► M2 (Architect Service)
  │      │
  │      └──► M7 (Architect MCP + Contract Engine MCP)
  │             │
  │             └──► M8 (Integration + Docker + E2E)
  │
  ├──► M3 (Contract Engine Core)
  │      │
  │      ├──► M4 (Contract Test Generation)
  │      │      │
  │      │      └──► M7
  │      │
  │      └──► M7
  │
  └──► M5 (Codebase Intelligence L1+L2)
         │
         └──► M6 (Codebase Intelligence L3 + MCP)
                │
                └──► M8

Critical path: M1 → M3 → M4 → M7 → M8
Parallel tracks:
  Track A: M1 → M2 → M7
  Track B: M1 → M3 → M4 → M7
  Track C: M1 → M5 → M6 → M8
```

---

## Appendix D: Estimated LOC Summary

| Milestone | Source LOC | Test LOC | Config/Doc LOC | Total |
|-----------|-----------|----------|----------------|-------|
| M1: Core Models | 1,500 | 800 | 200 | 2,500 |
| M2: Architect | 2,800 | 1,000 | 200 | 4,000 |
| M3: Contract Engine | 4,000 | 1,200 | 300 | 5,500 |
| M4: Test Generation | 1,200 | 600 | 200 | 2,000 |
| M5: CI Layer 1+2 | 4,200 | 1,500 | 300 | 6,000 |
| M6: CI Layer 3 + MCP | 2,800 | 1,000 | 200 | 4,000 |
| M7: Architect+CE MCP | 1,500 | 800 | 200 | 2,500 |
| M8: Integration | 1,500 | 1,000 | 500 | 3,000 |
| **Total** | **19,500** | **7,900** | **2,100** | **29,500** |

This is ~30K LOC total, significantly less than the reference estimate of ~60K LOC. The reference estimate likely includes more extensive test suites, documentation, and sample data. The milestones can be extended with additional tests and edge-case handling to reach 40-45K LOC.

---

*Architecture plan generated for the Super Agent Team Build 1 PRD creation effort.*
*All technology decisions reference BUILD1_TECHNOLOGY_RESEARCH.md.*
*All format decisions reference CODEBASE_PRD_FORMAT_RESEARCH.md.*
