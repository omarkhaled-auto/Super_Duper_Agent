# Cross-Build Integration Audit Report

## Executive Summary

This audit reviews integration correctness across all 3 Super Agent Team PRDs (Build 1: Architect + Contract Engine + Codebase Intelligence, Build 2: Builder Fleet Upgrade, Build 3: Integrator + Quality Gate + Super Orchestrator). The audit identified **4 CRITICAL blockers, 4 HIGH-severity issues, 4 MEDIUM design inconsistencies, and 3 LOW-severity gaps**. The two most severe issues are MCP tool name mismatches where Build 3 calls 4 tools that do not exist in Build 1, and a `src/shared/` package namespace collision between Build 1 and Build 3.

---

## Integration Map

### Build 1 Exposed Interfaces

#### Architect MCP Server (3 tools) - `src/architect/mcp_server.py`
| Tool Name | Parameters | Returns |
|-----------|-----------|---------|
| `get_service_map()` | none | ServiceMap dict |
| `get_contracts_for_service(service_name)` | service_name: str | list of contract dicts |
| `get_domain_model()` | none | DomainModel dict |

#### Contract Engine MCP Server (6 tools) - `src/contract_engine/mcp_server.py`
| Tool Name | Parameters | Returns |
|-----------|-----------|---------|
| `get_contract(contract_id)` | contract_id: str | contract dict or None |
| `validate_endpoint(service_name, method, path, response_body, status_code)` | 5 params | {valid: bool, violations: list} |
| `generate_tests(contract_id, framework, include_negative)` | 3 params | test code string |
| `check_breaking_changes(contract_id, new_spec)` | 2 params | list of breaking change dicts |
| `mark_implemented(contract_id, service_name, evidence_path)` | 3 params | {marked, total, all_implemented} |
| `get_unimplemented_contracts(service_name)` | service_name: str | list of contract dicts |

#### Codebase Intelligence MCP Server (7 tools) - `src/codebase_intelligence/mcp_server.py`
| Tool Name | Parameters | Returns |
|-----------|-----------|---------|
| `find_definition(symbol, language)` | 2 params | location dict or None |
| `find_callers(symbol, max_results)` | 2 params | list of caller dicts |
| `find_dependencies(file_path)` | file_path: str | {imports, imported_by, transitive_deps, circular_deps} |
| `search_semantic(query, language, service_name, n_results)` | 4 params | list of result dicts |
| `get_service_interface(service_name)` | service_name: str | {endpoints, events_published, events_consumed} |
| `check_dead_code(service_name)` | service_name: str | list of dead code dicts |
| `register_artifact(file_path, service_name)` | 2 params | {indexed, symbols_found, dependencies_found} |

#### REST API Endpoints (Build 1)
- Architect: `POST /api/decompose`, `GET /api/service-map`, `GET /api/domain-model`, `GET /api/health`
- Contract Engine: `POST /api/contracts`, `GET /api/contracts`, `GET /api/contracts/{id}`, `DELETE /api/contracts/{id}`, `POST /api/validate`, `POST /api/breaking-changes/{id}`, `POST /api/implementations/mark`, `GET /api/implementations/unimplemented`, `GET /api/health`
- Codebase Intelligence: `GET /api/symbols`, `GET /api/dependencies`, `POST /api/search`, `POST /api/artifacts`, `GET /api/dead-code`, `GET /api/health`

---

### Build 1 -> Build 2 Integration

| What Build 2 Consumes | Build 1 Source | Status |
|----------------------|----------------|--------|
| Contract Engine MCP (6 tools) | `ContractEngineClient` wraps all 6 | MATCH |
| Codebase Intelligence MCP (7 tools) | `CodebaseIntelligenceClient` wraps all 7 | MATCH |
| Architect MCP (3 tools) | INT-003 declares dependency | NO CLIENT DEFINED |

**Build 2 SVC-001..006 -> Contract Engine MCP**: All 6 tool names match. Parameter schemas match. Return types match. **Verified correct.**

**Build 2 SVC-007..013 -> Codebase Intelligence MCP**: All 7 tool names match. Parameter schemas match. Return types match. **Verified correct.**

**Build 2 INT-003 -> Architect MCP**: Build 2 M6 INT-003 declares: "Build 2 depends on Build 1's Architect MCP server (3 tools) -- `get_service_map()`, `get_contracts_for_service()`, `get_domain_model()` -- consumed during PRD decomposition phase when available." However, Build 2 defines NO `ArchitectClient` class and no code consumes these 3 tools. **See HIGH-01.**

---

### Build 1 -> Build 3 Integration

| What Build 3 Consumes | Build 1 Source | Status |
|----------------------|----------------|--------|
| Architect "decompose" MCP tool | Architect MCP | TOOL DOES NOT EXIST |
| Contract Engine "create_contract" MCP tool | Contract Engine MCP | TOOL DOES NOT EXIST |
| Contract Engine "validate_spec" MCP tool | Contract Engine MCP | TOOL DOES NOT EXIST |
| Contract Engine "list_contracts" MCP tool | Contract Engine MCP | TOOL DOES NOT EXIST |

Build 3 M5 `run_architect_phase` (REQ-046) calls `session.call_tool("decompose", {"prd_text": prd_content})`. Build 1 Architect MCP does NOT expose a "decompose" tool. The decompose capability is REST-only (`POST /api/decompose`). **See CRIT-01.**

Build 3 M5 `run_contract_registration` (REQ-047) calls `create_contract`, `validate_spec`, `list_contracts` via MCP. Build 1 Contract Engine MCP exposes: `get_contract`, `validate_endpoint`, `generate_tests`, `check_breaking_changes`, `mark_implemented`, `get_unimplemented_contracts`. None of the 3 tools Build 3 calls exist. **See CRIT-02.**

---

### Build 2 -> Build 3 Integration

| What Build 3 Consumes | Build 2 Source | Status |
|----------------------|----------------|--------|
| Builder subprocess output | `python -m agent_team --cwd {dir} --depth {depth}` | PARTIAL MATCH |
| STATE.json for results | `.agent-team/STATE.json` | FIELD MISMATCH |

Build 3's `run_parallel_builders` (REQ-048) launches Build 2 as subprocess and reads STATE.json. Build 3 constructs `BuilderResult` with fields: `success`, `cost`, `test_passed`, `test_total`, `convergence_ratio`, `artifacts`. Build 2's `RunState` serializes different fields (`total_cost`, `health`, phase-specific data). The mapping from `RunState.to_dict()` output to `BuilderResult` fields is undefined. **See CRIT-04.**

Build 3's `generate_builder_config` (REQ-049) produces a config.yaml for each Builder but omits Build 2's contract-aware sections (`agent_teams`, `contract_engine`, `codebase_intelligence`, `contract_scans`). **See HIGH-04.**

---

## Shared Data Type Comparison

### ServiceMap / ServiceDefinition / ServiceInfo

| Field | Build 1 `ServiceDefinition` | Build 3 `ServiceInfo` | Match? |
|-------|---------------------------|----------------------|--------|
| name/id | `name: str` | `service_id: str` | NAME MISMATCH |
| domain | `domain: str` | `domain: str` | YES |
| description | `description: str` | not present | MISSING |
| stack | `stack: ServiceStack` (typed) | `stack: dict[str, str]` | TYPE MISMATCH |
| estimated_loc | `estimated_loc: int` | `estimated_loc: int` | YES |
| owns_entities | `owns_entities: list[str]` | not present | MISSING |
| provides_contracts | `provides_contracts: list[str]` | not present | MISSING |
| consumes_contracts | `consumes_contracts: list[str]` | not present | MISSING |
| docker_image | not present | `docker_image: str` | BUILD 3 ONLY |
| health_endpoint | not present | `health_endpoint: str` | BUILD 3 ONLY |
| port | not present | `port: int` | BUILD 3 ONLY |
| status | not present | `status: ServiceStatus` | BUILD 3 ONLY |
| build_cost | not present | `build_cost: float` | BUILD 3 ONLY |
| build_dir | not present | `build_dir: str` | BUILD 3 ONLY |

**Verdict**: These are complementary but not interchangeable. Build 3 must map Build 1's ServiceDefinition to its ServiceInfo, handling `name` -> `service_id` and `ServiceStack` -> `dict`. **See HIGH-02.**

### ContractEntry (Build 1) vs ServiceContract (Build 2) vs ContractViolation (Build 3)

| Field | Build 1 `ContractEntry` | Build 2 `ServiceContract` | Match? |
|-------|------------------------|--------------------------|--------|
| id | `id: str` | `contract_id: str` | NAME MISMATCH |
| type | `type: ContractType` | `contract_type: str` | NAME MISMATCH |
| version | `version: str` | `version: str` | YES |
| service_name | `service_name: str` | split: `provider_service + consumer_service` | STRUCTURAL MISMATCH |
| spec | `spec: dict` | `spec: dict` | YES |
| spec_hash | `spec_hash: str` | `spec_hash: str` | YES |
| status | `status: ContractStatus` | not present (has `implemented: bool`) | DIFFERENT CONCEPT |

**Verdict**: Build 2's ServiceContract adds provider/consumer distinction not in Build 1's ContractEntry. Build 2 must derive provider_service from ServiceDefinition.provides_contracts. **See MED-02.**

### IntegrationReport Name Collision

| Field | Build 2 `IntegrationReport` | Build 3 `IntegrationReport` |
|-------|---------------------------|---------------------------|
| total_endpoints | YES | NO |
| tested_endpoints | YES | NO |
| services_deployed | NO | YES |
| contract_tests_total | NO | YES |
| integration_tests_total | NO | YES |
| data_flow_tests_total | NO | YES |
| boundary_tests_total | NO | YES |

**Verdict**: Completely different structures sharing the same class name. Build 2's is in `state.py`, Build 3's is in `shared/models.py`. If both are imported, name collision occurs. **See HIGH-03.**

### BuilderResult (Build 3) vs RunState (Build 2)

Build 3 `BuilderResult` expects these from Build 2's STATE.json:

| Build 3 Field | Build 2 STATE.json Field | Match? |
|--------------|--------------------------|--------|
| success | Not present (has `health: str`) | NO |
| cost | `total_cost: float` | NAME MISMATCH |
| test_passed | Not a top-level field | NO |
| test_total | Not a top-level field | NO |
| convergence_ratio | Not a top-level field | NO |
| artifacts | Not present | NO |

**Verdict**: Build 3 cannot construct BuilderResult from Build 2's STATE.json without a documented mapping. **See CRIT-04.**

---

## Issue Details

### CRIT-01: Build 3 calls non-existent "decompose" MCP tool on Architect

- **Location**: Build 3 `pipeline.py` REQ-046
- **Problem**: `session.call_tool("decompose", {"prd_text": prd_content})` targets a tool that Build 1 Architect MCP does not expose. Build 1 Architect MCP (REQ-059) only has: `get_service_map`, `get_contracts_for_service`, `get_domain_model`.
- **Impact**: Build 3 pipeline cannot start (architect phase is step 1).
- **Fix Options**:
  - **(A)** Add `decompose(prd_text)` tool to Build 1 Architect MCP (REQ-059). This tool would call the same pipeline as `POST /api/decompose` and return `DecompositionResult`.
  - **(B)** Change Build 3 REQ-046 to use REST `POST /api/decompose` via `httpx.AsyncClient` instead of MCP. Add fallback: try MCP first, fall back to REST.
- **Recommended**: Option A -- add the decompose tool to Build 1 MCP. This keeps Build 3's MCP-first design consistent.

### CRIT-02: Build 3 calls 3 non-existent Contract Engine MCP tools

- **Location**: Build 3 `pipeline.py` REQ-047, SVC-006/007/008
- **Problem**: Build 3 calls `create_contract`, `validate_spec`, `list_contracts` via MCP. Build 1 Contract Engine MCP (REQ-060) does not expose any of these. The equivalent operations are REST-only: `POST /api/contracts`, `POST /api/validate`, `GET /api/contracts`.
- **Impact**: Build 3 cannot register or validate contracts via the pipeline.
- **Fix Options**:
  - **(A)** Add `create_contract(service_name, type, version, spec)`, `validate_spec(spec, type)`, `list_contracts(service_name)` tools to Build 1 Contract Engine MCP (REQ-060).
  - **(B)** Change Build 3 REQ-047 to use REST API calls instead of MCP for these 3 operations.
- **Recommended**: Option A -- add the 3 tools to Build 1 MCP. This brings the total Contract Engine MCP tools from 6 to 9. The REST endpoints already implement the logic; MCP tools would be thin wrappers.

### CRIT-03: `src/shared/` namespace collision between Build 1 and Build 3

- **Location**: Build 1 `src/shared/` (models/, db/, config.py, constants.py, logging.py, errors.py) vs Build 3 `src/shared/` (models.py, protocols.py, constants.py, utils.py)
- **Problem**: Both builds define `src/shared/` in the same `super-team/` project root with completely different modules. `constants.py` exists in both with different contents. `models.py`/`models/` collide structurally.
- **Impact**: Build 3 code cannot coexist with Build 1 code in the same Python project without import failures.
- **Fix Options**:
  - **(A)** Rename Build 3's shared package to `src/orchestrator_shared/` or `src/build3_shared/`.
  - **(B)** Merge Build 3's shared types into Build 1's `src/shared/` by adding new modules (e.g., `src/shared/models/orchestrator.py`, `src/shared/protocols.py`).
  - **(C)** Use separate project roots: Build 1 in `super-team/`, Build 3 in `super-orchestrator/`.
- **Recommended**: Option C is cleanest -- each build is its own installable package. Build 3 can `pip install` Build 1's shared types if needed.

### CRIT-04: Build 3 BuilderResult cannot be constructed from Build 2 STATE.json

- **Location**: Build 3 `pipeline.py` REQ-048 reads `.agent-team/STATE.json`; Build 2 `state.py` RunState.to_dict()
- **Problem**: Build 3 expects `success`, `test_passed`, `test_total`, `convergence_ratio` as top-level STATE.json fields. Build 2's RunState has `total_cost` and `health` but not these fields. E2E test results are nested in `e2e_report`, not top-level. There is no `success` boolean.
- **Impact**: Build 3 cannot determine if a Builder succeeded or extract test metrics.
- **Fix Options**:
  - **(A)** Add `success: bool`, `test_passed: int`, `test_total: int`, `convergence_ratio: float` fields to Build 2's `RunState.to_dict()` output as top-level computed properties (derive from health, e2e_report, convergence data).
  - **(B)** Add a `BuilderSummary` method to Build 2 that produces the exact dict Build 3 expects.
  - **(C)** Document the exact STATE.json -> BuilderResult field mapping in Build 3 PRD and implement a parser.
- **Recommended**: Option A -- add computed summary fields to Build 2's STATE.json serialization. This is backward-compatible.

### HIGH-01: Build 2 declares Architect MCP dependency but has no ArchitectClient

- **Location**: Build 2 M6 INT-003
- **Problem**: "Build 2 depends on Build 1's Architect MCP server (3 tools)" but no ArchitectClient class is defined anywhere in Build 2. Only ContractEngineClient and CodebaseIntelligenceClient exist.
- **Impact**: Build 2 cannot query service maps or domain models from Build 1 during PRD decomposition.
- **Fix**: Either (A) create an ArchitectClient class in Build 2 mirroring the ContractEngineClient/CodebaseIntelligenceClient pattern, or (B) remove INT-003 if this dependency is not actually needed.

### HIGH-02: ServiceDefinition.name vs ServiceInfo.service_id field name mismatch

- **Location**: Build 1 `src/shared/models/architect.py` ServiceDefinition.name; Build 3 `src/shared/models.py` ServiceInfo.service_id
- **Problem**: The primary identifier for a service is `name` in Build 1 and `service_id` in Build 3. Every point where Build 3 processes Build 1's ServiceMap must handle this translation.
- **Fix**: Either (A) align on one field name (prefer `service_name` or `name`), or (B) document the mapping explicitly in Build 3 and implement a converter.

### HIGH-03: IntegrationReport name collision between Build 2 and Build 3

- **Location**: Build 2 `state.py` IntegrationReport; Build 3 `shared/models.py` IntegrationReport
- **Problem**: Both define `IntegrationReport` with completely different fields. If Build 3 imports Build 2's types (it imports `agent_team` as subprocess), naming ambiguity arises.
- **Fix**: Rename one. Suggested: Build 2's should be `EndpointTestReport`, Build 3's keeps `IntegrationReport`.

### HIGH-04: Build 3 generate_builder_config omits Build 2 contract-aware sections

- **Location**: Build 3 `pipeline.py` REQ-049
- **Problem**: The generated config.yaml for Builders includes only `depth`, `milestone`, `e2e_testing`, `post_orchestration_scans`. It does NOT include `contract_engine`, `codebase_intelligence`, or `contract_scans` sections. This means Builders spawned by Build 3 will NOT use Build 2's MCP integrations.
- **Fix**: Add `contract_engine: {enabled: True, server_root: config.build1_services_dir}`, `codebase_intelligence: {enabled: True, server_root: config.build1_services_dir}`, `contract_scans: {endpoint_schema_scan: True, ...}` to the generated config.

### MED-01: Inconsistent failure philosophy (graceful vs hard fail)

- **Location**: Build 2 all MCP clients (safe defaults on failure); Build 3 INT-001/002 (ConfigurationError on failure)
- **Problem**: Build 2 degrades gracefully when Build 1 is unavailable. Build 3 fails hard. A user running Build 3 with Build 1 temporarily down gets an exception, while Build 2 would silently continue.
- **Fix**: Consider adding a `graceful_degradation: bool` flag to Build 3's config. When True, skip MCP-dependent phases rather than raising.

### MED-02: ContractEntry.service_name vs ServiceContract.provider_service/consumer_service

- **Location**: Build 1 `ContractEntry` has single `service_name`; Build 2 `ServiceContract` has `provider_service` + `consumer_service`
- **Problem**: Build 1 stores one service_name per contract. Build 2 needs provider/consumer separation. The derivation logic (using `ServiceDefinition.provides_contracts`/`consumes_contracts`) is not documented.
- **Fix**: Document the mapping in Build 2 PRD: provider_service = service whose provides_contracts contains this contract; consumer_service = service whose consumes_contracts contains it.

### MED-03: Adversarial Scanner static-only vs vision's Codebase Intelligence integration

- **Location**: Build 3 M4 TECH-022; vision document M4 description
- **Problem**: Vision says Layer 4 uses "Codebase Intelligence (events published but never consumed, contracts defined but never implemented)". Build 3 TECH-022 mandates "purely static (regex-based), No MCP calls, no Build 1 dependency". The richer analysis from querying the codebase index is lost.
- **Fix**: This is a deliberate design decision for M4 independence. Consider adding an optional MCP-enhanced mode gated by a config flag in a future iteration.

### MED-04: CONTRACT scan code namespace overlap

- **Location**: Build 2 `contract_scanner.py` CONTRACT-001..004; Build 3 uses SCHEMA-001..003, PACT-001..002
- **Problem**: Build 2 and Build 3 both scan for contract compliance but use different code prefixes. If both run in the same pipeline, reporting could be confusing.
- **Impact**: Low -- they use different prefixes, so no actual collision. But documentation should clarify that BUILD 2 scans are static and BUILD 3 scans are dynamic.

### LOW-01: Vision's "Interview module" not implemented

- **Location**: Vision "Interview module for clarification questions"; Build 1 REQ-002 `interview_questions` field
- **Problem**: Build 1 stores interview_questions in DecompositionResult but has no interactive interview capability.
- **Fix**: Add to Build 1 M8 (optional milestone) or accept as a future enhancement.

### LOW-02: Build 3 subprocess fallback is still MCP, not REST

- **Location**: Build 3 REQ-046 fallback path
- **Problem**: The "fallback to subprocess + JSON if MCP SDK import fails" still uses `python -m src.architect.mcp_server` which IS MCP (stdio transport). A true fallback would use HTTP POST to `/api/decompose`.
- **Fix**: Change the fallback to use `httpx.AsyncClient.post(f"{architect_url}/api/decompose", json={"prd_text": prd_content})`.

### LOW-03: No version negotiation between builds

- **Location**: All 3 PRDs
- **Problem**: No mechanism to check Build 1 version compatibility from Build 2/3. If Build 1 MCP tool signatures change, clients break silently.
- **Fix**: Add a `get_version()` tool to each Build 1 MCP server. Build 2/3 clients check version on first connection and warn if incompatible.

---

## Feature Coverage vs Vision

| Vision Feature | Covered In | Status |
|---------------|-----------|--------|
| Architect PRD decomposition | Build 1 M2 | YES |
| Contract Engine (OpenAPI + AsyncAPI) | Build 1 M3-4 | YES |
| Codebase Intelligence (3 layers) | Build 1 M5-6 | YES |
| All MCP servers (3) | Build 1 M7 | YES |
| Agent Teams integration | Build 2 M1 | YES |
| Contract-aware generation (CONTRACT-001..004) | Build 2 M5 | YES |
| Codebase Intelligence MCP integration | Build 2 M3 | YES |
| Multi-instance Builder coordination | Build 2 M4 (via Agent Teams) | PARTIAL (no explicit M4) |
| Traefik API gateway | Build 3 M1 | YES |
| Docker Compose orchestration | Build 3 M1 | YES |
| Schemathesis contract testing | Build 3 M2 | YES |
| Pact consumer-driven contracts | Build 3 M2 | YES |
| Cross-service integration tests | Build 3 M3 | YES |
| 4-layer quality gate | Build 3 M4 | YES |
| Super Orchestrator CLI | Build 3 M5-6 | YES |
| Interactive architect interview | Build 1 M2 | STUB ONLY |
| Layer 4 via Codebase Intelligence | Build 3 M4 | NO (static only) |
| "decompose" as MCP tool | Build 1 M7 | NOT EXPOSED |
| create/validate/list contracts via MCP | Build 1 M7 | NOT EXPOSED |

### Redundancies
- CONTRACT-001..004 scans exist in BOTH Build 2 (static) and Build 3 (dynamic). These are complementary, not redundant, but should be documented as such.

---

## Recommended Fixes (Priority Order)

### Must Fix Before Build

1. **CRIT-01 + CRIT-02**: Add 4 new MCP tools to Build 1 PRD:
   - Architect MCP: add `decompose(prd_text: str)` tool (REQ-059)
   - Contract Engine MCP: add `create_contract(service_name, type, version, spec)`, `validate_spec(spec, type)`, `list_contracts(service_name, type, page, page_size)` tools (REQ-060)
   - Update Build 1 M7 test requirements to cover new tools

2. **CRIT-03**: Resolve `src/shared/` collision:
   - Rename Build 3's `src/shared/` to `src/build3_shared/` or use separate project roots
   - Update all imports in Build 3 PRD accordingly

3. **CRIT-04**: Define STATE.json -> BuilderResult mapping:
   - Add computed fields to Build 2 RunState.to_dict(): `summary: {success: bool, test_passed: int, test_total: int, convergence_ratio: float}`
   - Document mapping in Build 3 PRD REQ-048

4. **HIGH-01**: Either create ArchitectClient in Build 2 or remove INT-003
5. **HIGH-02**: Align service identifier field name across builds
6. **HIGH-03**: Rename Build 2's IntegrationReport to avoid collision
7. **HIGH-04**: Add contract-aware config sections to Build 3's generate_builder_config

### Should Fix

8. **MED-01**: Add graceful degradation option to Build 3
9. **MED-02**: Document provider/consumer derivation logic in Build 2
10. **LOW-03**: Add version checking tools to Build 1 MCP servers

---

## Verification Checklist

After fixes are applied, verify:

- [ ] Build 1 Architect MCP exposes 4 tools (original 3 + decompose)
- [ ] Build 1 Contract Engine MCP exposes 9 tools (original 6 + create/validate/list)
- [ ] Build 3 `src/shared/` does not collide with Build 1 `src/shared/`
- [ ] Build 2 STATE.json contains fields that Build 3 BuilderResult can parse
- [ ] Build 2 has ArchitectClient OR INT-003 is removed
- [ ] ServiceDefinition.name -> ServiceInfo.service_id mapping is documented
- [ ] Build 2 IntegrationReport is renamed to avoid collision with Build 3
- [ ] Build 3 generate_builder_config includes contract_engine/codebase_intelligence sections
- [ ] All MCP tool names called by Build 2 exist in Build 1 (verified: 13/13 match)
- [ ] All MCP tool names called by Build 3 exist in Build 1 (currently 0/4 match -- need fixes)
