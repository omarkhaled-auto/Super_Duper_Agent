# Pydantic v2 + FastAPI Technical Audit Report

Auditor: Pydantic/FastAPI Technical Reviewer
Date: 2026-02-14
Scope: BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md

---

## 1. Context7 Research Summary

### Pydantic v2 (Source: /pydantic/pydantic, High Reputation, Score 83.1)

**Verified Patterns:**
- `BaseModel` subclass syntax with type annotations: CONFIRMED
- `Field()` with `default`, `description`, `alias`, `ge`, `le`, `min_length`, `max_length`, `pattern`: CONFIRMED
- `model_config = ConfigDict(...)` or `model_config = {"key": value}` dict syntax: BOTH VALID (dict syntax is shorthand)
- `@field_validator()` replaces old `@validator()`: CONFIRMED
- `@model_validator(mode='before'|'after')` replaces old `@root_validator()`: CONFIRMED
- `model_dump()` replaces old `.dict()`: CONFIRMED
- `model_dump_json()` replaces old `.json()`: CONFIRMED
- `Model.model_validate()` replaces old `.parse_obj()`: CONFIRMED
- `Model.model_validate_json()` replaces old `.parse_raw()`: CONFIRMED
- `Literal` type for discriminated unions with `Field(discriminator='field_name')`: CONFIRMED
- `Optional[T]` and `T | None` are both valid (Python 3.10+ union syntax): CONFIRMED
- `from_attributes=True` in model_config replaces old `orm_mode = True`: CONFIRMED

### FastAPI (Source: /fastapi/fastapi, High Reputation, Score 84)

**Verified Patterns:**
- `FastAPI()` with `title`, `version`, `docs_url`: CONFIRMED
- `@app.get()`, `@app.post()`, etc. route decorators: CONFIRMED
- `Depends()` for dependency injection: CONFIRMED
- `HTTPException` for error responses: CONFIRMED
- `CORSMiddleware` from `fastapi.middleware.cors`: CONFIRMED with `add_middleware()` syntax
- `BackgroundTasks` parameter injection: CONFIRMED
- Lifespan via `@asynccontextmanager`: CONFIRMED (FastAPI >= 0.93)
- `response_model=ModelClass`: CONFIRMED
- Status codes from `starlette.status` or `fastapi.status`: CONFIRMED

### pydantic-settings (Source: training knowledge + confirmed patterns)

**Verified Patterns:**
- `from pydantic_settings import BaseSettings`: CONFIRMED (v2 moved to separate package)
- `model_config = SettingsConfigDict(env_prefix="...")`: CONFIRMED (or dict syntax)
- Field aliases for env var mapping: CONFIRMED

---

## 2. Build 1 PRD Audit

### 2.1 Pydantic v2 Models

**REQ-002 (Architect Models) - PASS**
- Uses `BaseModel`, `Field` with `pattern`, `ge`, `le`, `min_length` constraints: CORRECT
- Uses `str | None = None` syntax: CORRECT (Pydantic v2 supports Python 3.10+ union)
- Uses `@model_validator(mode='before')` for SymbolDefinition.id generation (REQ-004): CORRECT
- `model_config = {"from_attributes": True}` (ContractEntry): CORRECT (dict syntax is valid v2)

**REQ-003 (Contract Models) - PASS with 1 ADVISORY**
- All models use `BaseModel` with proper `Field()` constraints: CORRECT
- `ContractEntry` has `model_config from_attributes=True`: CORRECT
- Enums used as types (`ContractType`, `ContractStatus`, `ImplementationStatus`): CORRECT
- ADVISORY: `spec_hash` described as "auto-computed via TECH-009 algorithm not provided by caller" but defined as `spec_hash: str = Field(...)` (required). The hash computation should happen in the store layer, not the model. The PRD is consistent about this (ContractCreate does NOT include spec_hash, only ContractEntry does), so this is architecturally sound.

**REQ-004 (Codebase Models) - PASS**
- `SymbolDefinition.id` generated via `@model_validator(mode='before')` from `file_path` and `symbol_name`: CORRECT v2 syntax
- `list[SymbolDefinition]`, `dict[str, int]`: CORRECT (Pydantic v2 supports builtin generics)
- `tuple[str, float]` in `top_files_by_pagerank`: CORRECT

**REQ-005 (Common Models) - PASS**
- `HealthStatus` with `dict[str, Any] = Field(default_factory=dict)`: CORRECT
- Pattern constraints on status fields: CORRECT

**REQ-008 (Configuration) - PASS**
- Uses `pydantic_settings.BaseSettings`: CORRECT (separate package in v2)
- Uses `Field(alias="ENV_VAR")` for environment variable mapping: CORRECT
- Architecture plan shows `model_config = {"env_prefix": "", "case_sensitive": False}`: CORRECT v2 syntax

**TECH-003 - PASS**
- Explicitly mandates v2 syntax: `BaseModel, Field, model_config, from_attributes`
- Explicitly prohibits v1 patterns: CORRECT

**TEST-001 - PASS**
- Tests `model.model_dump()` then `Model(**data)` roundtrip: CORRECT v2 method name
- Tests `from_attributes` configuration: CORRECT

### 2.2 FastAPI Patterns

**INT-001 (Skeleton FastAPI apps) - PASS**
- "lifespan context manager" for app creation: CORRECT (FastAPI >= 0.93 pattern)
- `/api/health` endpoint returning `HealthStatus`: CORRECT

**REQ-020 (POST /api/decompose) - PASS**
- `async def` endpoint with request body: CORRECT
- Returns 201 on success, 422 on validation failure: CORRECT FastAPI status codes

**WIRE-004, WIRE-007 (Router inclusion) - PASS**
- `app.include_router()` with prefix and tags: CORRECT

**WIRE-005, WIRE-008 (Lifespan) - PASS**
- Lifespan initializes resources and stores in `app.state`: CORRECT FastAPI pattern

**WIRE-006, WIRE-010 (Depends injection) - PASS**
- `FastAPI Depends()` for service injection: CORRECT

**REQ-011 (Exception handler) - PASS**
- `AppError` base with `status_code` and `detail`
- FastAPI exception handler returning `JSONResponse`: CORRECT

**Architecture Plan Config (line 2282) - PASS with ADVISORY**
- `model_config = {"env_prefix": "", "case_sensitive": False}`: Valid v2 dict syntax
- ADVISORY: The preferred v2 syntax is `model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)` imported from `pydantic_settings`. The dict syntax works but `SettingsConfigDict` provides better IDE support and type checking. Not a bug, but a style preference.

### 2.3 Build 1 Issues Found

**ISSUE B1-1: SEVERITY LOW (Style)**
- Location: REQ-008, Architecture Plan line 2282
- Description: Uses `model_config = {"env_prefix": "", "case_sensitive": False}` dict syntax for BaseSettings
- Expected: `from pydantic_settings import SettingsConfigDict; model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)`
- Impact: Both syntaxes work. Dict syntax is valid but `SettingsConfigDict` gives better type checking.
- Fix: Optional style improvement, no functional impact.

**ISSUE B1-2: SEVERITY LOW (Style)**
- Location: Architecture Plan line 399
- Description: Uses `model_config = {"from_attributes": True}` dict syntax
- Expected: `from pydantic import ConfigDict; model_config = ConfigDict(from_attributes=True)`
- Impact: Both syntaxes work. Dict syntax is valid but `ConfigDict` gives better IDE support.
- Fix: Optional style improvement, no functional impact.

**NO CRITICAL OR HIGH ISSUES in Build 1 Pydantic/FastAPI usage.**

---

## 3. Build 2 PRD Audit

### 3.1 Pydantic Usage

Build 2 does NOT use Pydantic `BaseModel` for its new data structures. All new models are Python `dataclass` types:
- `TaskResult`, `WaveResult`, `TeamState`, `HookConfig`, `HookInput` (TECH-001..004A)
- `ContractValidation`, `ContractInfo` (TECH-013, TECH-014)
- `DefinitionResult`, `DependencyResult`, `ArtifactResult` (TECH-022..024)
- `ContractReport`, `IntegrationReport` (TECH-029, TECH-030)
- All config types: `AgentTeamsConfig`, `ContractEngineConfig`, `CodebaseIntelligenceConfig`, `ContractScanConfig`

**VERDICT: PASS** - Build 2 correctly uses Python `dataclasses` for its own types (consistent with existing agent-team codebase pattern) and only references Pydantic models from Build 1 via MCP tool responses. No Pydantic v1/v2 confusion possible.

### 3.2 FastAPI Usage

Build 2 has NO new FastAPI endpoints. It is a CLI tool that:
1. Consumes Build 1 FastAPI services via MCP (not HTTP)
2. Uses existing agent-team Claude Code SDK calls (not FastAPI)

**REQ-022 in Build 3** generates a FastAPI `/_pact/state` endpoint handler as a string template — this is for Build 1 provider state setup, not Build 2.

**VERDICT: PASS** - No FastAPI usage to audit in Build 2.

### 3.3 MCP SDK Usage (Pydantic-adjacent)

**REQ-024, REQ-038 (MCP sessions) - PASS**
- Uses `@asynccontextmanager` decorator: CORRECT
- `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern: CORRECT per MCP SDK
- `await session.initialize()` as mandatory first call: CORRECT

### 3.4 Build 2 Issues Found

**NO ISSUES** - Build 2 does not use Pydantic or FastAPI directly.

---

## 4. Build 3 PRD Audit

### 4.1 Pydantic Usage

Build 3 uses Pydantic minimally:
- Technology Stack lists: "pydantic 2.x+" for "Configuration and DTO validation"
- REQ-001..005: All shared models (`ServiceInfo`, `BuilderResult`, `ContractViolation`, etc.) are defined as `dataclass` types, NOT Pydantic `BaseModel`
- REQ-008: `SuperOrchestratorConfig` and nested configs are `dataclass` types loaded from YAML via `load_super_config()`, NOT Pydantic Settings

**VERDICT: PASS** - Despite listing pydantic 2.x+ in the tech stack, Build 3 uses Python `dataclasses` for all its models. The pydantic dependency is likely listed because Build 1 models (consumed via MCP) use it. No Pydantic v1/v2 confusion risk.

**ADVISORY B3-1**: The technology stack lists "pydantic 2.x+" but Build 3 never actually imports or uses Pydantic directly. The dependency may be needed transitively (Build 1 models), but the PRD should clarify this to avoid confusion.

### 4.2 FastAPI Usage

Build 3 uses FastAPI minimally:
- Technology Stack: "FastAPI 0.129.0+ (health/status endpoints)"
- REQ-022: `generate_pact_state_handler()` produces a FastAPI endpoint as a string template

**REQ-022 (Pact state handler) - PASS**
```python
@app.post("/_pact/state")
async def handle_state(request: Request):
    body = await request.json()
    state = body.get("state")
```
- Uses `@app.post()` decorator: CORRECT
- Uses `Request` body parsing: CORRECT
- Uses `await request.json()`: CORRECT

**No other FastAPI patterns in Build 3 PRD.** Build 3's CLI uses Typer, not FastAPI.

### 4.3 Build 3 Issues Found

**ISSUE B3-1: SEVERITY INFO (Clarity)**
- Location: Technology Stack
- Description: Lists "pydantic 2.x+" but Build 3 never directly uses Pydantic BaseModel/Field/etc.
- Impact: None (transitive dependency from Build 1). Could confuse builders into using Pydantic when dataclasses are intended.
- Fix: Add clarification: "pydantic 2.x+ (transitive dependency — Build 1 models)" or remove from Build 3's explicit tech stack.

---

## 5. Cross-Build Model Consistency

### 5.1 Shared Model Definitions

Build 1 defines ALL Pydantic models in `src/shared/models/`:
- `architect.py`: ServiceMap, ServiceDefinition, DomainModel, DomainEntity, etc.
- `contracts.py`: ContractEntry, ContractCreate, ValidationResult, etc.
- `codebase.py`: SymbolDefinition, SemanticSearchResult, etc.
- `common.py`: BuildCycle, HealthStatus, ArtifactRegistration

Build 2 does NOT re-define any Build 1 models. It consumes them via MCP tool JSON responses and maps to its own dataclasses:
- `ContractInfo` (dataclass) maps from Build 1's `ContractEntry` (Pydantic)
- `DefinitionResult` (dataclass) maps from Build 1's `SymbolDefinition` (Pydantic)
- `ArtifactResult` (dataclass) maps from Build 1's indexing response (plain dict)

Build 3 does NOT re-define any Build 1 models. It consumes them via:
- MCP tool responses (JSON dicts)
- Build 1 REST API responses (JSON)
- Builder subprocess outputs (STATE.json files)

### 5.2 Field Name Consistency Check

| Build 1 Model | Build 2 Mapping | Build 3 Mapping | Consistent? |
|---|---|---|---|
| ContractEntry.id | ContractInfo.id | SVC-006 response: id | YES |
| ContractEntry.type | ContractInfo.type | N/A | YES |
| ContractEntry.version | ContractInfo.version | N/A | YES |
| ContractEntry.service_name | ContractInfo.service_name | N/A | YES |
| ContractEntry.spec | ContractInfo.spec | N/A | YES |
| ContractEntry.spec_hash | ContractInfo.spec_hash | N/A | YES |
| SymbolDefinition.file_path | DefinitionResult.file | N/A | YES (renamed) |
| SymbolDefinition.line_start | DefinitionResult.line | N/A | YES (renamed) |
| SymbolDefinition.kind | DefinitionResult.kind | N/A | YES |
| SymbolDefinition.signature | DefinitionResult.signature | N/A | YES |
| ValidationResult.valid | ContractValidation.valid | N/A | YES |
| ValidationResult.errors | ContractValidation.violations | N/A | RENAMED (see B2-CROSS-1) |

### 5.3 Cross-Build Consistency Issues

**ISSUE B2-CROSS-1: SEVERITY LOW (Rename)**
- Build 1 `ValidationResult` has `errors: list[str]`
- Build 2 `ContractValidation` has `violations: list[dict[str, str]]`
- These are intentionally different types (Build 2 enriches the error format with field-level detail). Not a bug — Build 2 explicitly transforms the data.

**ISSUE B3-CROSS-1: SEVERITY INFO (Type difference)**
- Build 1 `BuildCycle` is a Pydantic `BaseModel` with `total_cost_usd: float`
- Build 3 `PipelineCostTracker` is a `dataclass` with `total_cost` property
- These represent different cost tracking scopes (Build 1 = per-build-cycle, Build 3 = per-pipeline). Not a conflict.

**ISSUE B1-B3-CROSS-2: SEVERITY LOW (Pydantic vs dataclass)**
- Build 1 uses Pydantic `BaseModel` for all API-facing models
- Build 3 uses Python `dataclass` for all its models
- Build 3 uses `SuperOrchestratorConfig` as a `dataclass` loaded from YAML, while Build 1 uses `pydantic_settings.BaseSettings` loaded from env vars
- This is an intentional design decision (Build 3 = internal CLI, Build 1 = external API). Not a conflict.

### 5.4 Enum Value Consistency

| Enum | Build 1 | Build 3 | Match? |
|---|---|---|---|
| Contract status | active, deprecated, draft | N/A | N/A |
| Health status | healthy, degraded, unhealthy | N/A (uses string) | OK |
| Service status | N/A | pending, building, built, deploying, healthy, unhealthy, failed | Build 3 only |
| Gate verdict | N/A | passed, failed, partial, skipped | Build 3 only |

No conflicting enum definitions across builds.

---

## 6. Summary

### Pass/Fail Matrix

| Check | Build 1 | Build 2 | Build 3 | Cross-Build |
|---|---|---|---|---|
| BaseModel syntax | PASS | N/A (dataclass) | N/A (dataclass) | PASS |
| Field() constraints | PASS | N/A | N/A | PASS |
| model_config syntax | PASS (dict OK) | N/A | N/A | PASS |
| Validators (@field_validator, @model_validator) | PASS | N/A | N/A | PASS |
| Serialization (model_dump) | PASS | N/A | N/A | PASS |
| Deserialization (model_validate) | PASS | N/A | N/A | PASS |
| No v1 patterns | PASS | N/A | N/A | PASS |
| FastAPI app creation | PASS | N/A | PASS (minimal) | PASS |
| FastAPI routes | PASS | N/A | PASS (minimal) | PASS |
| FastAPI Depends() | PASS | N/A | N/A | PASS |
| FastAPI CORSMiddleware | N/A (not used) | N/A | N/A | N/A |
| FastAPI lifespan | PASS | N/A | N/A | PASS |
| FastAPI HTTPException | PASS | N/A | N/A | PASS |
| pydantic-settings BaseSettings | PASS | N/A | N/A | PASS |
| Model consistency | - | - | - | PASS |
| Field name consistency | - | - | - | PASS |
| Enum consistency | - | - | - | PASS |

### Issue Summary

| ID | Severity | Build | Description | Fix Required? |
|---|---|---|---|---|
| B1-1 | LOW | 1 | Dict syntax for BaseSettings model_config instead of SettingsConfigDict | NO (both valid) |
| B1-2 | LOW | 1 | Dict syntax for BaseModel model_config instead of ConfigDict | NO (both valid) |
| B3-1 | INFO | 3 | pydantic listed in tech stack but never directly used | NO (clarification only) |
| B2-CROSS-1 | LOW | 1-2 | ValidationResult.errors vs ContractValidation.violations naming | NO (intentional transform) |
| B3-CROSS-1 | INFO | 1-3 | Different cost tracking types (BuildCycle vs PipelineCostTracker) | NO (different scopes) |
| B1-B3-CROSS-2 | LOW | 1-3 | Pydantic vs dataclass for similar concepts | NO (intentional design) |

### Overall Verdict

**ALL 3 PRDs PASS the Pydantic v2 + FastAPI technical review.**

- **0 CRITICAL issues** - No broken Pydantic v1 syntax, no incorrect FastAPI patterns
- **0 HIGH issues** - No type mismatches, no missing validators, no wrong method names
- **3 LOW issues** - Style preferences (dict vs ConfigDict), naming transforms (intentional)
- **3 INFO issues** - Clarification opportunities, no functional impact

The PRDs are technically accurate for Pydantic v2 and FastAPI. All model definitions use correct v2 syntax. All FastAPI patterns follow current best practices. Cross-build model consistency is maintained with intentional, documented transformations at MCP boundaries.

---

## 7. Recommended Fixes (Optional)

These are non-blocking style improvements:

### Fix 1: Build 1 Architecture Plan — Use ConfigDict (OPTIONAL)
```python
# Current (valid):
model_config = {"from_attributes": True}

# Preferred (better IDE support):
from pydantic import ConfigDict
model_config = ConfigDict(from_attributes=True)
```

### Fix 2: Build 1 Architecture Plan — Use SettingsConfigDict (OPTIONAL)
```python
# Current (valid):
model_config = {"env_prefix": "", "case_sensitive": False}

# Preferred (better IDE support):
from pydantic_settings import SettingsConfigDict
model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)
```

### Fix 3: Build 3 PRD — Clarify pydantic dependency (OPTIONAL)
```
# Current:
- **Configuration:** PyYAML 6.x+, pydantic 2.x+

# Suggested:
- **Configuration:** PyYAML 6.x+, pydantic 2.x+ (transitive — required by Build 1 models)
```
