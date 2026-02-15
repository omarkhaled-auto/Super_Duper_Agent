# RUN4_PRD.md Cross-Build Accuracy Review

> **Reviewer**: cross-build-accuracy-agent
> **Date**: 2026-02-15
> **Scope**: Verify every cross-build interface in RUN4_PRD.md against BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md, and RUN4_CROSS_BUILD_INTERFACES.md
> **Method**: Field-by-field comparison of MCP tool signatures, client methods, subprocess commands, Docker services, config references, and state machine transitions

---

## 1. MCP Tool Signatures (RUN4_PRD SVC-001 to SVC-017 vs BUILD1_PRD + CROSS_BUILD_INTERFACES)

### 1.1 Architect MCP Server (4 tools)

| SVC-ID | RUN4 PRD | Ground Truth (BUILD1 + XREF) | Verdict | Finding |
|--------|----------|------------------------------|---------|---------|
| SVC-001 | `decompose(prd_text)` -> `DecompositionResult { service_map: dict, domain_model: dict, contract_stubs: list, validation_issues: list }` | BUILD1 REQ-059 + XREF 1.1: `{ service_map: ServiceMap, domain_model: DomainModel, contract_stubs: list[dict], validation_issues: list[str], interview_questions: list[str] }` | **MISMATCH** | RUN4 OMITS `interview_questions: list[str]` field. BUILD1 REQ-002 and XREF Section 1.1 both include this field. |
| SVC-002 | `get_service_map()` -> `ServiceMap { project_name: string, services: list, generated_at: string }` | XREF 1.1: `{ project_name: str, services: list[ServiceDefinition], generated_at: str, prd_hash: str, build_cycle_id: str|null }` | **MISMATCH** | RUN4 OMITS `prd_hash: str` and `build_cycle_id: str|null` fields. Both are present in XREF Section 1.1 and BUILD1 REQ-002. |
| SVC-003 | `get_contracts_for_service(service_name)` -> `list { id: string, role: string, type: string, counterparty: string }` | XREF 1.1: `list[{ id: str, role: "provider"|"consumer", type: str, counterparty: str, summary: str }]` | **MISMATCH** | RUN4 OMITS `summary: str` field from list element schema. XREF Section 1.1 includes it. |
| SVC-004 | `get_domain_model()` -> `DomainModel { entities: list, relationships: list, generated_at: string }` | XREF 1.1: `{ entities: list[DomainEntity], relationships: list[DomainRelationship], generated_at: str }` | **MATCH** | All fields present. Element types (`DomainEntity`, `DomainRelationship`) are simplified to `list` in RUN4 but this is acceptable shorthand. |

### 1.2 Contract Engine MCP Server (6 tools used by Build 2 client)

| SVC-ID | RUN4 PRD | Ground Truth (BUILD1 + XREF) | Verdict | Finding |
|--------|----------|------------------------------|---------|---------|
| SVC-005 | `get_contract(contract_id)` -> `ContractEntry { id: string, service_name: string, type: string, version: string, spec: dict }` | XREF 1.2: `ContractEntry dict` or `None` (full fields include spec_hash, status per BUILD2 TECH-014) | **PARTIAL** | RUN4 omits `spec_hash: string` and `status: string` from response DTO. BUILD2 TECH-014 defines ContractInfo with these fields. XREF 1.2 says "ContractEntry dict" without enumerating. Functionally acceptable but incomplete. |
| SVC-006 | `validate_endpoint(service_name, method, path, response_body, status_code)` -> `ContractValidation { valid: boolean, violations: list }` | XREF 1.2: `{ valid: bool, violations: list[{ field: str, expected: str, actual: str, severity: str }] }` | **MATCH** | Parameters and top-level response match. Violation inner structure not specified in RUN4 but acceptable. |
| SVC-007 | `generate_tests(contract_id, framework, include_negative)` -> `string` | XREF 1.2: `str` (complete test file content) | **MATCH** | Full match on parameters and return type. |
| SVC-008 | `check_breaking_changes(contract_id, new_spec)` -> `list { change_type: string, path: string, severity: string }` | XREF 1.2: `list[{ change_type: str, path: str, old_value: str|null, new_value: str|null, severity: str, affected_consumers: list[str] }]` | **MISMATCH** | RUN4 OMITS `old_value`, `new_value`, and `affected_consumers` from list element schema. |
| SVC-009 | `mark_implemented(contract_id, service_name, evidence_path)` -> `MarkResult { marked: boolean, total_implementations: number }` | XREF 1.2: `{ marked: bool, total_implementations: int, all_implemented: bool }` | **MISMATCH** | RUN4 OMITS `all_implemented: bool` field from response. |
| SVC-010 | `get_unimplemented_contracts(service_name)` -> `list { id: string, type: string, expected_service: string }` | XREF 1.2: `list[{ id: str, type: str, version: str, expected_service: str, status: str }]` | **MISMATCH** | RUN4 OMITS `version: str` and `status: str` from list element schema. |

### 1.3 Codebase Intelligence MCP Server (7 tools)

| SVC-ID | RUN4 PRD | Ground Truth (BUILD1 + XREF) | Verdict | Finding |
|--------|----------|------------------------------|---------|---------|
| SVC-011 | `find_definition(symbol, language)` -> `DefinitionResult { file_path: string, line_start: number, kind: string }` | XREF 1.3: `{ file_path: str, line_start: int, line_end: int, kind: str, signature: str|null, docstring: str|null }` or `None` | **MISMATCH** | RUN4 OMITS `line_end: int`, `signature: str|null`, `docstring: str|null` fields. BUILD1 REQ-057 and XREF both include them. |
| SVC-012 | `find_callers(symbol, max_results)` -> `list { file_path: string, line: number, caller_name: string }` | XREF 1.3: `list[{ file_path: str, line: int, caller_name: str }]` | **MATCH** | All fields present. |
| SVC-013 | `find_dependencies(file_path)` -> `DependencyResult { imports: list, imported_by: list, transitive_deps: list, circular_deps: list }` | XREF 1.3: `{ imports: list[str], imported_by: list[str], transitive_deps: list[str], circular_deps: list[list[str]] }` | **MATCH** | All fields present. Element type detail (`list[list[str]]` for circular_deps) is simplified in RUN4 but acceptable. |
| SVC-014 | `search_semantic(query, language, service_name, n_results)` -> `list { file_path: string, content: string, score: number }` | XREF 1.3: `list[{ chunk_id: str, file_path: str, symbol_name: str|null, content: str, score: float, language: str, service_name: str|null, line_start: int, line_end: int }]` | **MISMATCH** | RUN4 OMITS `chunk_id`, `symbol_name`, `language`, `service_name`, `line_start`, `line_end` from list element schema. Parameters are correct (all 4 present). |
| SVC-015 | `get_service_interface(service_name)` -> `ServiceInterface { endpoints: list, events_published: list, events_consumed: list }` | XREF 1.3: `{ service_name: str, endpoints: list[dict], events_published: list[dict], events_consumed: list[dict], exported_symbols: list[SymbolDefinition] }` | **MISMATCH** | RUN4 OMITS `service_name: str` and `exported_symbols: list[SymbolDefinition]` from response. |
| SVC-016 | `check_dead_code(service_name)` -> `list { symbol_name: string, file_path: string, kind: string, confidence: string }` | XREF 1.3: `list[{ symbol_name: str, file_path: str, kind: str, line: int, service_name: str|null, confidence: str }]` | **MISMATCH** | RUN4 OMITS `line: int` and `service_name: str|null` from list element schema. |
| SVC-017 | `register_artifact(file_path, service_name)` -> `ArtifactResult { indexed: boolean, symbols_found: number }` | XREF 1.3: `{ indexed: bool, symbols_found: int, dependencies_found: int, errors: list[str] }` | **MISMATCH** | RUN4 OMITS `dependencies_found: int` and `errors: list[str]` from response. BUILD2 TECH-024 defines ArtifactResult with `dependencies_found` field. |

### 1.4 MCP Tool Signature Summary

| Verdict | Count | SVC-IDs |
|---------|-------|---------|
| **MATCH** | 5 | SVC-004, SVC-006, SVC-007, SVC-012, SVC-013 |
| **PARTIAL** | 1 | SVC-005 |
| **MISMATCH** | 11 | SVC-001, SVC-002, SVC-003, SVC-008, SVC-009, SVC-010, SVC-011, SVC-014, SVC-015, SVC-016, SVC-017 |

**Accuracy: 5/17 (29.4%)** -- 11 interfaces have missing response fields

**Pattern**: All 11 mismatches are the same type of error -- RUN4's SVC table omits fields from the response DTO that exist in the ground-truth XREF document and BUILD1_PRD. The request parameters are all correct; only the response schemas are incomplete.

---

## 2. Build 2 Client Methods (RUN4 vs BUILD2_PRD)

### 2.1 ContractEngineClient (6 methods)

| RUN4 SVC | Method | BUILD2 SVC | Parameter Match | Return Type Match | Verdict |
|----------|--------|------------|-----------------|-------------------|---------|
| SVC-005 | get_contract(contract_id) | SVC-001 | YES | PARTIAL (RUN4 omits spec_hash, status) | **PARTIAL** |
| SVC-006 | validate_endpoint(service_name, method, path, response_body, status_code) | SVC-002 | YES (all 5 params match) | YES | **MATCH** |
| SVC-007 | generate_tests(contract_id, framework, include_negative) | SVC-003 | YES (all 3 params match) | YES (string) | **MATCH** |
| SVC-008 | check_breaking_changes(contract_id, new_spec) | SVC-004 | YES | NO (RUN4 shows 3 fields, BUILD2 shows "array", XREF shows 6 fields) | **MISMATCH** |
| SVC-009 | mark_implemented(contract_id, service_name, evidence_path) | SVC-005 | YES | NO (RUN4 omits all_implemented) | **MISMATCH** |
| SVC-010 | get_unimplemented_contracts(service_name) | SVC-006 | YES | NO (RUN4 omits version, status) | **MISMATCH** |

**Method count**: RUN4 has 6, BUILD2 has 6. MATCH.

### 2.2 CodebaseIntelligenceClient (7 methods)

| RUN4 SVC | Method | BUILD2 SVC | Parameter Match | Return Type Match | Verdict |
|----------|--------|------------|-----------------|-------------------|---------|
| SVC-011 | find_definition(symbol, language) | SVC-007 | YES | NO (RUN4 omits line_end, signature, docstring) | **MISMATCH** |
| SVC-012 | find_callers(symbol, max_results) | SVC-008 | YES | YES | **MATCH** |
| SVC-013 | find_dependencies(file_path) | SVC-009 | YES | YES (BUILD2 also omits circular_deps in table) | **MATCH** |
| SVC-014 | search_semantic(query, language, service_name, n_results) | SVC-010 | **MISMATCH** | PARTIAL | **MISMATCH** |
| SVC-015 | get_service_interface(service_name) | SVC-011 | YES | NO (RUN4 omits exported_symbols) | **MISMATCH** |
| SVC-016 | check_dead_code(service_name) | SVC-012 | YES | PARTIAL (RUN4 has confidence, BUILD2 table omits it) | **PARTIAL** |
| SVC-017 | register_artifact(file_path, service_name) | SVC-013 | YES | NO (RUN4 omits dependencies_found) | **MISMATCH** |

**Parameter finding for SVC-014**: RUN4 correctly shows 4 parameters (query, language, service_name, n_results) matching BUILD1 REQ-057 and XREF 1.3. BUILD2's SVC-010 table only lists 2 params (query, n_results) -- but BUILD2 REQ-034 text correctly lists all 4. So RUN4 is MORE accurate than BUILD2's SVC table here. The BUILD2 SVC table itself is simplified/incomplete.

**Method count**: RUN4 has 7, BUILD2 has 7. MATCH.

### 2.3 ArchitectClient (4 methods)

| RUN4 SVC | Method | BUILD2 INT-003 | Verdict |
|----------|--------|----------------|---------|
| SVC-001 | decompose(prd_text) | decompose(prd_text) | **MATCH** (method exists; response mismatch is Build 1 issue) |
| SVC-002 | get_service_map() | get_service_map() | **MATCH** (method exists; response mismatch is Build 1 issue) |
| SVC-003 | get_contracts_for_service(service_name) | get_contracts_for_service(service_name) | **MATCH** (method exists; response mismatch is Build 1 issue) |
| SVC-004 | get_domain_model() | get_domain_model() | **MATCH** |

**Method count**: RUN4 has 4, BUILD2 INT-003 has 4. MATCH.

### 2.4 Client Method Summary

| Category | Total | Match | Partial | Mismatch |
|----------|-------|-------|---------|----------|
| ContractEngineClient | 6 | 2 | 1 | 3 |
| CodebaseIntelligenceClient | 7 | 2 | 1 | 4 |
| ArchitectClient | 4 | 4 | 0 | 0 |
| **Total** | **17** | **8** | **2** | **7** |

**Client Method Accuracy: 8/17 (47.1%)**

**Note**: Most "mismatches" here mirror the MCP tool signature mismatches from Section 1 -- they are response DTO simplifications, not method signature errors. All method names, parameter names, and parameter counts are correct.

---

## 3. Subprocess Commands (RUN4 SVC-018 to SVC-020 vs BUILD3_PRD)

| SVC-ID | RUN4 PRD | BUILD3 Ground Truth | Verdict | Finding |
|--------|----------|---------------------|---------|---------|
| SVC-018 | `python -m agent_team --cwd {dir} --depth {depth}` via `asyncio.create_subprocess_exec` | BUILD3 REQ-048/TECH-023: `python -m agent_team --cwd {builder_dir} --depth {config.builder.depth}` via `asyncio.create_subprocess_exec` with PIPE | **MATCH** | Command, subprocess creation, and output parsing all match. |
| SVC-019 | `python -m agent_team --cwd {dir} --depth quick` with FIX_INSTRUCTIONS.md | BUILD3 REQ-024: Fix pass in quick mode with FIX_INSTRUCTIONS.md written to builder_dir | **MATCH** | Command and input mechanism match. |
| SVC-020 | Config generation: SuperOrchestratorConfig -> config.yaml loadable by Build 2 `_dict_to_config()` | BUILD3 REQ-049: `generate_builder_config()` produces config.yaml with depth, milestone, e2e_testing, post_orchestration_scans | **MATCH** | Config fields and roundtrip requirement match. |

### 3.1 STATE.json Cross-Build Contract

| Field | RUN4 PRD (REQ-017) | BUILD3 XREF 4.2 | BUILD2 TECH-031 | Verdict |
|-------|---------------------|------------------|-----------------|---------|
| `summary.success` | bool | bool | bool | **MATCH** |
| `summary.test_passed` | int | int | int | **MATCH** |
| `summary.test_total` | int | int | int | **MATCH** |
| `summary.convergence_ratio` | float | float | float | **MATCH** |
| `total_cost` | float | float | Not in summary | **MATCH** |
| `health` | str | str | str | **MATCH** |
| `completed_phases` | list[str] | list[str] | list[str] | **MATCH** |

### 3.2 _dict_to_config() Return Type

RUN4 REQ-018 correctly notes: `_dict_to_config() returns tuple[AgentTeamConfig, set[str]]` (Build 2's v6.0 return type). This matches the v6.0 Mode Upgrade Propagation change documented in MEMORY.md.

**Subprocess Accuracy: 3/3 (100%)**

---

## 4. Docker Services (RUN4 vs BUILD1_PRD + BUILD3_PRD)

### 4.1 Port Assignments

| Service | RUN4 PRD | BUILD1 REQ-062 | XREF 6.1 | Verdict |
|---------|----------|----------------|-----------|---------|
| architect | 8001:8000 | 8001->8000 | 8001:8000 | **MATCH** |
| contract-engine | 8002:8000 | 8002->8000 | 8002:8000 | **MATCH** |
| codebase-intelligence | 8003:8000 | 8003->8000 | 8003:8000 | **MATCH** |
| postgres | 5432 | N/A (BUILD3) | 5432 | **MATCH** |
| redis | 6379 | N/A (BUILD3) | 6379 | **MATCH** |
| traefik (HTTP) | 80 | N/A (BUILD3) | 80 | **MATCH** |
| traefik (API) | 8080 | N/A (BUILD3) | 8080 | **MATCH** |

### 4.2 Health Check Pattern

| Aspect | RUN4 PRD | BUILD1 REQ-062 | Verdict |
|--------|----------|----------------|---------|
| Method | `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"` | Same pattern | **MATCH** |
| Interval | 10s | 10s | **MATCH** |
| Timeout | 5s | 5s | **MATCH** |
| Retries | 5 | 5 | **MATCH** |
| Start period (architect) | Not specified in health cascade | 15s | N/A |
| Start period (contract-engine) | Not specified | 10s | N/A |
| Start period (codebase-intel) | Not specified | 20s | N/A |

### 4.3 Network Architecture

| Aspect | RUN4 PRD | BUILD1 REQ-062 | BUILD3 REQ-015 | XREF 6.1/6.4 | Verdict |
|--------|----------|----------------|----------------|---------------|---------|
| Build 1 network | frontend + backend split | `super-team-net` (single bridge) | frontend + backend split | **Build 1: `super-team-net`; Build 3: frontend+backend** | **MISMATCH** |

**FINDING**: BUILD1_PRD REQ-062 specifies a single `super-team-net` bridge network for all Build 1 services. RUN4_PRD and BUILD3_PRD use frontend+backend network separation. XREF Section 6.1 lists Build 1 services on `super-team-net`, while Section 6.4 shows the full system using frontend+backend split.

This is **architecturally intentional**: Build 1 standalone uses `super-team-net`, but when integrated into the full system (Run 4), Build 1 services are placed on both `frontend` and `backend` networks via the docker-compose merge. The `docker-compose.run4.yml` overlay (Tier 4) adds network overrides. RUN4 correctly describes the **integrated** topology, not the standalone Build 1 topology. **Verdict: ACCEPTABLE** -- the 5-file merge approach resolves this.

### 4.4 Health Check Cascade

| RUN4 PRD | BUILD3 PRD / XREF | Verdict |
|----------|-------------------|---------|
| Tier 0: postgres, redis | Yes (BUILD3 REQ-015) | **MATCH** |
| Tier 1: contract-engine | Yes (BUILD1 REQ-062 + BUILD3) | **MATCH** |
| Tier 2: architect, codebase-intelligence | Yes (BUILD1 depends_on contract-engine) | **MATCH** |
| Tier 3: generated services | Yes (depends_on postgres) | **MATCH** |
| Tier 4: traefik | Yes (BUILD3 REQ-015) | **MATCH** |

### 4.5 Compose Files (5-file merge)

| File | RUN4 PRD | XREF Section 6 | Verdict |
|------|----------|-----------------|---------|
| docker-compose.infra.yml (Tier 0) | postgres, redis | Yes | **MATCH** |
| docker-compose.build1.yml (Tier 1) | architect, contract-engine, codebase-intelligence | Yes | **MATCH** |
| docker-compose.traefik.yml (Tier 2) | traefik (v3.6) | Yes | **MATCH** |
| docker-compose.generated.yml (Tier 3) | auth-service, order-service, notification-service | Yes | **MATCH** |
| docker-compose.run4.yml (Tier 4) | Cross-build wiring overrides | Yes | **MATCH** |

### 4.6 Docker Services Summary

**Docker Accuracy: All critical fields match. Network topology is architecturally justified via compose merge.**

---

## 5. Config Cross-References (RUN4 vs BUILD2 + BUILD3)

### 5.1 Build 2 Config Fields

| Config Field | RUN4 PRD Usage | BUILD2 TECH-015/TECH-025 | Verdict |
|-------------|----------------|--------------------------|---------|
| `contract_engine.enabled` | REQ-013, referenced for gating | TECH-015: `enabled: bool = False` | **MATCH** |
| `contract_engine.mcp_command` | Appendix A: `"python"` | TECH-015: `mcp_command: str = "python"` | **MATCH** |
| `contract_engine.mcp_args` | Appendix A: `["-m", "src.contract_engine.mcp_server"]` | TECH-015: same | **MATCH** |
| `contract_engine.database_path` | Appendix A: `"./data/contracts.db"` | TECH-015: `database_path: str = ""` | **MATCH** |
| `contract_engine.server_root` | Referenced for cwd | TECH-015: `server_root: str = ""` | **MATCH** |
| `codebase_intelligence.enabled` | REQ-014, referenced for gating | TECH-025: `enabled: bool = False` | **MATCH** |
| `codebase_intelligence.chroma_path` | Appendix A: `"./data/chroma"` | TECH-025: `chroma_path: str = ""` | **MATCH** |
| `codebase_intelligence.graph_path` | Appendix A: `"./data/graph.json"` | TECH-025: `graph_path: str = ""` | **MATCH** |

### 5.2 Build 3 Config Fields

| Config Field | RUN4 PRD Usage | BUILD3 REQ-008 | Verdict |
|-------------|----------------|----------------|---------|
| `build1_services_dir` | Referenced for MCP server cwd | `build1_services_dir: str = ""` | **MATCH** |
| `builder.depth` | SVC-018 command | `depth: str = "thorough"` | **MATCH** |
| `builder.max_concurrent` | REQ-019 Semaphore(3) | `max_concurrent: int = 3` | **MATCH** |
| `builder.timeout_per_builder` | WIRE-015 (5s test) | `timeout_per_builder: int = 1800` | **MATCH** |
| `quality_gate.max_fix_retries` | REQ-027 | `max_fix_retries: int = 3` | **MATCH** |
| `agent_team_config_path` | SVC-020 config gen | `agent_team_config_path: str = ""` | **MATCH** |

**Config Accuracy: 14/14 (100%)**

---

## 6. State Machine Transitions (RUN4 Appendix B vs BUILD3_PRD)

| # | RUN4 PRD | BUILD3 PRD (lines 602-616) | Verdict |
|---|----------|---------------------------|---------|
| 1 | start_architect: init -> architect_running [prd_loaded] | Same | **MATCH** |
| 2 | architect_done: architect_running -> architect_review [has_service_map] | Same | **MATCH** |
| 3 | approve_architecture: architect_review -> contracts_registering [architecture_valid] | Same | **MATCH** |
| 4 | contracts_ready: contracts_registering -> builders_running [contracts_valid] | Same | **MATCH** |
| 5 | builders_done: builders_running -> builders_complete [any_builder_success] | Same | **MATCH** |
| 6 | start_integration: builders_complete -> integrating [has_successful_builds] | Same | **MATCH** |
| 7 | integration_done: integrating -> quality_gate [integration_ran] | Same | **MATCH** |
| 8 | quality_passed: quality_gate -> complete [all_gates_passed] | Same | **MATCH** |
| 9 | quality_failed: quality_gate -> fix_pass [has_violations] | Same | **MATCH** |
| 10 | fix_done: fix_pass -> quality_gate [fix_applied] | Same | **MATCH** |

**Missing transitions in RUN4 Appendix B**:

| # | BUILD3 PRD | RUN4 PRD | Verdict |
|---|-----------|----------|---------|
| 11 | fail: [non-terminal] -> failed | Present in RUN4 (same row) | **MATCH** |
| 12 | retry_architect: architect_running -> architect_running [retries_remaining] | **MISSING** from RUN4 Appendix B | **MISMATCH** |
| 13 | skip_contracts: contracts_registering -> builders_running | **MISSING** from RUN4 Appendix B | **MISMATCH** |

**State Machine Accuracy: 11/13 transitions (84.6%)** -- RUN4 has 10 transitions + fail, missing `retry_architect` and `skip_contracts`

---

## 7. MCP .mcp.json Configuration (RUN4 Appendix A vs XREF Appendix A)

| Field | RUN4 PRD | XREF Document | Verdict |
|-------|----------|---------------|---------|
| Architect command | `python -m src.architect.mcp_server` | Same | **MATCH** |
| Architect env: DATABASE_PATH | `./data/architect.db` | Same | **MATCH** |
| Architect env: CONTRACT_ENGINE_URL | `http://localhost:8002` | Same | **MATCH** |
| Contract Engine command | `python -m src.contract_engine.mcp_server` | Same | **MATCH** |
| Contract Engine env: DATABASE_PATH | `./data/contracts.db` | Same | **MATCH** |
| Codebase Intel command | `python -m src.codebase_intelligence.mcp_server` | Same | **MATCH** |
| Codebase Intel env: DATABASE_PATH | `./data/symbols.db` | Same | **MATCH** |
| Codebase Intel env: CHROMA_PATH | `./data/chroma` | Same | **MATCH** |
| Codebase Intel env: GRAPH_PATH | `./data/graph.json` | Same | **MATCH** |

**MCP Config Accuracy: 9/9 (100%)**

---

## 8. Contract Engine Tool Count (RUN4 REQ-010 vs BUILD1)

RUN4 REQ-010 states: "verify exactly 9 tools returned with names matching {create_contract, validate_spec, list_contracts, get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts}".

BUILD1 REQ-060 defines exactly these 9 tools. **MATCH**.

However, RUN4's SVC table only maps 6 of these 9 tools to ContractEngineClient (SVC-005 to SVC-010). The remaining 3 (create_contract, validate_spec, list_contracts) are used by Build 3's pipeline directly, not through Build 2's client wrapper. RUN4 REQ-024 correctly references these 3 tools for Phase 4 (Contract Registration). **Architecturally correct**.

---

## 9. Missing Interfaces Not Covered in RUN4 PRD

### 9.1 Covered (no gap)

- [x] Build 1 inter-service HTTP (Architect -> Contract Engine) -- RUN4 WIRE-012
- [x] Build 2 MCP fallback behavior -- RUN4 WIRE-009, WIRE-010, WIRE-011
- [x] Agent Teams optional path -- RUN4 WIRE-013, WIRE-014
- [x] Builder environment isolation (SEC-001) -- RUN4 SEC-001, WIRE-016
- [x] Traefik configuration -- RUN4 SEC-002, SEC-003, WIRE-019
- [x] State persistence and resume -- RUN4 TEST-012
- [x] Budget tracking -- referenced in Build 3 tests
- [x] Graceful shutdown -- BUILD3 signal handling acknowledged

### 9.2 Gaps

| Missing Interface | Source | Impact | Severity |
|-------------------|--------|--------|----------|
| Depth gating cross-build effects | XREF Section 8.5 | RUN4 does not document how depth setting propagates from Build 3 to Build 2 (quick/standard/thorough/exhaustive effects on contract engine and codebase intel enablement) | MEDIUM |
| ChromaDB first-download timeout | XREF 1.3 implementation notes | RUN4 Risk Assessment mentions it but no specific TEST-xxx validates the 120s timeout | LOW |
| Build 2 `EndpointTestReport` vs Build 3 `IntegrationReport` naming | BUILD2 TECH-030, BUILD3 REQ-004 | Both builds have similarly-named report types; RUN4 does not explicitly verify no name collision in shared namespace | LOW |
| Quality Gate Layer sequence enforcement | XREF 9.7, BUILD3 Wiring Anti-Patterns | RUN4 tests L1-L4 (REQ-027) but does not explicitly test "L1 must pass before L2" sequencing enforcement | LOW |
| HTTP Inter-Service Communication details | XREF Section 5 | RUN4 WIRE-012 acknowledges Architect->ContractEngine HTTP but does not specify the exact httpx client settings (connect=5.0, read=30.0 timeout) | LOW |

---

## 10. Accuracy Summary

### Per-Category Scores

| Category | Total Interfaces | Accurate | Partial | Mismatch | Accuracy |
|----------|-----------------|----------|---------|----------|----------|
| MCP Tool Response Schemas | 17 | 5 | 1 | 11 | 29.4% |
| Subprocess Commands | 3 | 3 | 0 | 0 | 100% |
| STATE.json Contract | 7 | 7 | 0 | 0 | 100% |
| Docker Port Assignments | 7 | 7 | 0 | 0 | 100% |
| Docker Health Checks | 5 | 5 | 0 | 0 | 100% |
| Docker Compose Merge | 5 | 5 | 0 | 0 | 100% |
| Config Cross-References | 14 | 14 | 0 | 0 | 100% |
| MCP .mcp.json Config | 9 | 9 | 0 | 0 | 100% |
| State Machine Transitions | 13 | 11 | 0 | 2 | 84.6% |
| **TOTAL** | **80** | **66** | **1** | **13** | **82.5%** |

### Strict Accuracy (MATCH only): 66/80 = 82.5%
### Lenient Accuracy (MATCH + PARTIAL): 67/80 = 83.8%

---

## 11. Findings Classification

### CRITICAL (blocks implementation if not fixed)

None. All mismatches are response DTO field omissions -- the implementation will work but the PRD's SVC table provides an incomplete contract for the builder to implement against. The XREF document has the complete schemas.

### HIGH (should fix before build)

| # | Finding | Affected | Recommendation |
|---|---------|----------|----------------|
| H-1 | 11 MCP tool response DTOs in SVC table are incomplete (missing 1-6 fields each) | SVC-001, 002, 003, 005, 008, 009, 010, 011, 014, 015, 016, 017 | Add missing fields to SVC table response DTOs OR add explicit reference: "See RUN4_CROSS_BUILD_INTERFACES.md Section 1 for complete response schemas" |
| H-2 | 2 state machine transitions missing from Appendix B | retry_architect (#12), skip_contracts (#13) | Add transitions 12 and 13 to Appendix B |

### MEDIUM

| # | Finding | Affected | Recommendation |
|---|---------|----------|----------------|
| M-1 | Depth gating cross-build effects not documented | RUN4 config section | Add depth gating table (XREF Section 8.5) or reference |
| M-2 | Network topology appears inconsistent with BUILD1 standalone | Docker section | Add note explaining compose merge resolves super-team-net vs frontend/backend split |

### LOW

| # | Finding | Affected | Recommendation |
|---|---------|----------|----------------|
| L-1 | No explicit test for L1->L2->L3->L4 enforcement | Test matrix | Add test case |
| L-2 | ChromaDB 120s timeout not in test matrix | Test matrix | Add timeout-specific test |
| L-3 | HTTP inter-service timeout values not specified | WIRE-012 | Add httpx timeout values |

---

## 12. Conclusion

RUN4_PRD.md is **structurally complete** -- it covers all 5 verification areas (MCP tools, client methods, subprocess commands, Docker services, config cross-references) with correct method names, parameter names, and architectural wiring. The 82.5% accuracy score is dragged down primarily by **one systematic issue**: the SVC table response DTOs omit optional/supplementary fields from the ground-truth schemas.

**Key strengths**:
- 100% accuracy on subprocess commands, STATE.json contract, Docker configuration, and config cross-references
- All 20 MCP tools are accounted for with correct tool counts (4+9+7)
- Correct identification of `_dict_to_config()` v6.0 return type change
- 5-file Docker Compose merge topology is correct

**Key weakness**:
- SVC table response DTOs systematically simplified -- omitting fields that exist in BUILD1_PRD and XREF document. This is the ONLY category causing mismatches. The XREF document (`RUN4_CROSS_BUILD_INTERFACES.md`) has the complete schemas and should be treated as authoritative for field-level accuracy.

**Recommendation**: Either (a) expand SVC table response DTOs to match XREF Section 1, or (b) add a prominent note in Milestone 2 directing implementers to use `RUN4_CROSS_BUILD_INTERFACES.md` as the authoritative field-level reference for all 17 MCP tool response schemas.
