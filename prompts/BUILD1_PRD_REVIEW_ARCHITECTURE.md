# Build 1 PRD -- Architecture Completeness Review

## Summary

- **Missing items found:** 7
- **Critical (feature gap):** 2
- **Warning (partial coverage):** 5
- **Covered:** 154/161 files have explicit or implicit requirement coverage
- **MCP Tools:** 16/16 FULLY COVERED
- **Database Tables:** 14/14 FULLY COVERED
- **API Endpoints:** All endpoints FULLY COVERED
- **Milestone Dependencies:** CORRECT
- **Cross-Service Integration:** FULLY COVERED

Overall the PRD is remarkably thorough. The 2 critical gaps are missing test requirements for specific modules. The 5 warnings are about files listed in the project structure that lack explicit requirements (prompts directory, per-service configs, storage layer abstraction files).

---

## File Coverage Matrix

### Root Files

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| pyproject.toml | Section 1, Appendix A | REQ-001 | COVERED |
| README.md | Section 1 | REQ-073 | COVERED |
| docker-compose.yml | Section 1, Appendix B | INT-002 (skeleton), REQ-062 (finalize) | COVERED |
| .env.example | Section 1 | INT-004 | COVERED |
| .mcp.json | Section 1, Section 8.3 | INT-005 (create), REQ-072 (finalize), WIRE-020 | COVERED |
| config.yaml | Section 9.1 | N/A (build tool config, not project deliverable) | N/A |

### src/shared/ (13 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| src/shared/__init__.py | Section 1 | REQ-012 | COVERED |
| src/shared/models/__init__.py | Section 1 | REQ-012, WIRE-001 | COVERED |
| src/shared/models/architect.py | Section 2.1 | REQ-002 | COVERED |
| src/shared/models/contracts.py | Section 2.2 | REQ-003 | COVERED |
| src/shared/models/codebase.py | Section 2.3 | REQ-004 | COVERED |
| src/shared/models/common.py | Section 2.4 | REQ-005 | COVERED |
| src/shared/db/__init__.py | Section 1 | REQ-012 | COVERED |
| src/shared/db/connection.py | Section 3.4 | REQ-006 | COVERED |
| src/shared/db/schema.py | Section 3.1-3.3 | REQ-007 | COVERED |
| src/shared/config.py | Section 9.2 | REQ-008 | COVERED |
| src/shared/constants.py | Section 1 | REQ-009 | COVERED |
| src/shared/logging.py | Section 1 | REQ-010 | COVERED |
| src/shared/errors.py | Section 1 | REQ-011 | COVERED |

### src/architect/ (22 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| src/architect/__init__.py | Section 1 | WIRE-003 | COVERED |
| src/architect/main.py | Section 5.1 | INT-001, WIRE-004, WIRE-005 | COVERED |
| src/architect/mcp_server.py | Section 4.1 | REQ-059 | COVERED |
| src/architect/config.py | Section 1 | **NONE** | **WARNING** |
| src/architect/routers/__init__.py | Section 1 | Implicit from WIRE-004 | COVERED (implicit) |
| src/architect/routers/decomposition.py | Section 5.1 | REQ-020, WIRE-006 | COVERED |
| src/architect/routers/service_map.py | Section 5.1 | REQ-021 | COVERED |
| src/architect/routers/domain_model.py | Section 5.1 | REQ-022 | COVERED |
| src/architect/routers/health.py | Section 5.1 | INT-001 | COVERED |
| src/architect/services/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/architect/services/prd_parser.py | Section 5.1 | REQ-013 | COVERED |
| src/architect/services/service_boundary.py | Section 5.1 | REQ-014 | COVERED |
| src/architect/services/contract_generator.py | Section 5.1 | REQ-015 | COVERED |
| src/architect/services/domain_modeler.py | Section 5.1 | REQ-016 | COVERED |
| src/architect/services/validator.py | Section 5.1 | REQ-017, TECH-006 | COVERED |
| src/architect/storage/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/architect/storage/service_map_store.py | Section 5.1 | REQ-018 | COVERED |
| src/architect/storage/domain_model_store.py | Section 5.1 | REQ-019 | COVERED |
| src/architect/prompts/__init__.py | Section 1 | **NONE** | **WARNING** |
| src/architect/prompts/decomposition_prompt.py | Section 1 | **NONE** | **WARNING** |
| src/architect/prompts/interview_prompt.py | Section 1 | **NONE** | **WARNING** |
| src/architect/prompts/validation_prompt.py | Section 1 | **NONE** | **WARNING** |

### src/contract_engine/ (25 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| src/contract_engine/__init__.py | Section 1 | WIRE-003 | COVERED |
| src/contract_engine/main.py | Section 5.2 | INT-001, WIRE-007, WIRE-008 | COVERED |
| src/contract_engine/mcp_server.py | Section 4.2 | REQ-060 | COVERED |
| src/contract_engine/config.py | Section 1 | **NONE** | **WARNING** |
| src/contract_engine/routers/__init__.py | Section 1 | Implicit from WIRE-007 | COVERED (implicit) |
| src/contract_engine/routers/contracts.py | Section 5.2 | REQ-033, WIRE-009 | COVERED |
| src/contract_engine/routers/validation.py | Section 5.2 | REQ-034 | COVERED |
| src/contract_engine/routers/tests.py | Section 5.2 | REQ-041, WIRE-010 | COVERED |
| src/contract_engine/routers/implementations.py | Section 5.2 | REQ-036 | COVERED |
| src/contract_engine/routers/breaking_changes.py | Section 5.2 | REQ-035 | COVERED |
| src/contract_engine/routers/health.py | Section 5.2 | INT-001 | COVERED |
| src/contract_engine/services/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/contract_engine/services/contract_store.py | Section 5.2 | REQ-025 | COVERED |
| src/contract_engine/services/openapi_validator.py | Section 5.2 | REQ-026 | COVERED |
| src/contract_engine/services/asyncapi_parser.py | Section 5.2 | REQ-027 | COVERED |
| src/contract_engine/services/asyncapi_validator.py | Section 5.2 | REQ-028 | COVERED |
| src/contract_engine/services/schema_registry.py | Section 5.2 | REQ-029 | COVERED |
| src/contract_engine/services/version_manager.py | Section 5.2 | REQ-030, TECH-010 | COVERED |
| src/contract_engine/services/breaking_change_detector.py | Section 5.2 | REQ-031 | COVERED |
| src/contract_engine/services/test_generator.py | Section 5.2 | REQ-039, TECH-013, TECH-014 | COVERED |
| src/contract_engine/services/compliance_checker.py | Section 5.2 | REQ-040, TECH-015 | COVERED |
| src/contract_engine/services/implementation_tracker.py | Section 5.2 | REQ-032 | COVERED |
| src/contract_engine/storage/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/contract_engine/storage/contract_db.py | Section 1 | **NONE** | **WARNING** |
| src/contract_engine/storage/implementation_db.py | Section 1 | **NONE** | **WARNING** |

### src/codebase_intelligence/ (31 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| src/codebase_intelligence/__init__.py | Section 1 | WIRE-003 | COVERED |
| src/codebase_intelligence/main.py | Section 5.3 | INT-001, WIRE-016 | COVERED |
| src/codebase_intelligence/mcp_server.py | Section 4.3 | REQ-057, TECH-024 | COVERED |
| src/codebase_intelligence/config.py | Section 1 | **NONE** | **WARNING** |
| src/codebase_intelligence/routers/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/codebase_intelligence/routers/symbols.py | Section 5.3 | REQ-058 | COVERED |
| src/codebase_intelligence/routers/dependencies.py | Section 5.3 | REQ-058 | COVERED |
| src/codebase_intelligence/routers/search.py | Section 5.3 | REQ-058 | COVERED |
| src/codebase_intelligence/routers/artifacts.py | Section 5.3 | REQ-058 | COVERED |
| src/codebase_intelligence/routers/dead_code.py | Section 5.3 | REQ-058 | COVERED |
| src/codebase_intelligence/routers/health.py | Section 5.3 | INT-001, REQ-058 | COVERED |
| src/codebase_intelligence/services/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/codebase_intelligence/services/ast_parser.py | Section 5.3 | REQ-042, WIRE-012 | COVERED |
| src/codebase_intelligence/services/symbol_extractor.py | Section 5.3 | REQ-043 | COVERED |
| src/codebase_intelligence/services/import_resolver.py | Section 5.3 | REQ-045 | COVERED |
| src/codebase_intelligence/services/graph_builder.py | Section 5.3 | REQ-046, WIRE-013 | COVERED |
| src/codebase_intelligence/services/graph_analyzer.py | Section 5.3 | REQ-047 | COVERED |
| src/codebase_intelligence/services/semantic_indexer.py | Section 5.3 | REQ-052 | COVERED |
| src/codebase_intelligence/services/semantic_searcher.py | Section 5.3 | REQ-053 | COVERED |
| src/codebase_intelligence/services/dead_code_detector.py | Section 5.3 | REQ-048 | COVERED |
| src/codebase_intelligence/services/incremental_indexer.py | Section 5.3 | REQ-055, WIRE-017 | COVERED |
| src/codebase_intelligence/services/service_interface_extractor.py | Section 5.3 | REQ-056 | COVERED |
| src/codebase_intelligence/parsers/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/codebase_intelligence/parsers/python_parser.py | Section 5.3 | REQ-044 | COVERED |
| src/codebase_intelligence/parsers/typescript_parser.py | Section 5.3 | REQ-044 | COVERED |
| src/codebase_intelligence/parsers/csharp_parser.py | Section 5.3 | REQ-044 | COVERED |
| src/codebase_intelligence/parsers/go_parser.py | Section 5.3 | REQ-044 | COVERED |
| src/codebase_intelligence/storage/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| src/codebase_intelligence/storage/symbol_db.py | Section 5.3 | REQ-049 | COVERED |
| src/codebase_intelligence/storage/graph_db.py | Section 5.3 | REQ-050, WIRE-014 | COVERED |
| src/codebase_intelligence/storage/chroma_store.py | Section 5.3 | REQ-054 | COVERED |

### tests/ (45 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| tests/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/conftest.py | Section 1 | TEST-004 | COVERED |
| tests/test_shared/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/test_shared/test_models.py | Section 1 | TEST-001 | COVERED |
| tests/test_shared/test_db_connection.py | Section 1 | TEST-002 | COVERED |
| tests/test_shared/test_config.py | Section 1 | TEST-003 | COVERED |
| tests/test_architect/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/test_architect/test_prd_parser.py | Section 1 | TEST-005 | COVERED |
| tests/test_architect/test_service_boundary.py | Section 1 | TEST-006 | COVERED |
| tests/test_architect/test_contract_generator.py | Section 1 | TEST-007 | COVERED |
| tests/test_architect/test_domain_modeler.py | Section 1 | TEST-008 | COVERED |
| tests/test_architect/test_validator.py | Section 1 | TEST-009 | COVERED |
| tests/test_architect/test_routers.py | Section 1 | TEST-010 | COVERED |
| tests/test_architect/test_mcp_tools.py | Section 1 | TEST-033 | COVERED |
| tests/test_contract_engine/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/test_contract_engine/test_contract_store.py | Section 1 | TEST-011 | COVERED |
| tests/test_contract_engine/test_openapi_validator.py | Section 1 | TEST-012 | COVERED |
| tests/test_contract_engine/test_asyncapi_parser.py | Section 1 | TEST-013 | COVERED |
| tests/test_contract_engine/test_asyncapi_validator.py | Section 1 | TEST-014 | COVERED |
| tests/test_contract_engine/test_schema_registry.py | Section 1 | **NONE** | **CRITICAL** |
| tests/test_contract_engine/test_version_manager.py | Section 1 | TEST-015 | COVERED |
| tests/test_contract_engine/test_breaking_change_detector.py | Section 1 | TEST-016 | COVERED |
| tests/test_contract_engine/test_test_generator.py | Section 1 | TEST-019 | COVERED |
| tests/test_contract_engine/test_compliance_checker.py | Section 1 | TEST-020 | COVERED |
| tests/test_contract_engine/test_implementation_tracker.py | Section 1 | TEST-017 | COVERED |
| tests/test_contract_engine/test_routers.py | Section 1 | TEST-018 | COVERED |
| tests/test_contract_engine/test_mcp_tools.py | Section 1 | TEST-034 | COVERED |
| tests/test_codebase_intelligence/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/test_codebase_intelligence/test_ast_parser.py | Section 1 | TEST-021 | COVERED |
| tests/test_codebase_intelligence/test_symbol_extractor.py | Section 1 | TEST-022 | COVERED |
| tests/test_codebase_intelligence/test_import_resolver.py | Section 1 | TEST-023 | COVERED |
| tests/test_codebase_intelligence/test_graph_builder.py | Section 1 | TEST-024 | COVERED |
| tests/test_codebase_intelligence/test_graph_analyzer.py | Section 1 | TEST-025 | COVERED |
| tests/test_codebase_intelligence/test_semantic_indexer.py | Section 1 | TEST-029 | COVERED |
| tests/test_codebase_intelligence/test_semantic_searcher.py | Section 1 | TEST-030 | COVERED |
| tests/test_codebase_intelligence/test_dead_code_detector.py | Section 1 | TEST-026 | COVERED |
| tests/test_codebase_intelligence/test_incremental_indexer.py | Section 1 | TEST-031 | COVERED |
| tests/test_codebase_intelligence/test_language_parsers.py | Section 1 | TEST-027 | COVERED |
| tests/test_codebase_intelligence/test_routers.py | Section 1 | **NONE** | **CRITICAL** |
| tests/test_codebase_intelligence/test_mcp_tools.py | Section 1 | TEST-032 | COVERED |
| tests/test_integration/__init__.py | Section 1 | Implicit | COVERED (implicit) |
| tests/test_integration/test_architect_to_contracts.py | Section 1 | TEST-036, REQ-065 | COVERED |
| tests/test_integration/test_codebase_indexing.py | Section 1 | TEST-037, REQ-066 | COVERED |
| tests/test_integration/test_mcp_roundtrip.py | Section 1 | TEST-035, TEST-039, REQ-061 | COVERED |
| tests/test_integration/test_docker_compose.py | Section 1 | TEST-038, REQ-067 | COVERED |

### docker/ (6 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| docker/architect/Dockerfile | Appendix B | INT-003, REQ-063 | COVERED |
| docker/architect/requirements.txt | Section 1 | INT-003 | COVERED |
| docker/contract_engine/Dockerfile | Appendix B | INT-003, REQ-063 | COVERED |
| docker/contract_engine/requirements.txt | Section 1 | INT-003 | COVERED |
| docker/codebase_intelligence/Dockerfile | Appendix B | INT-003, REQ-063, TECH-023 | COVERED |
| docker/codebase_intelligence/requirements.txt | Section 1 | INT-003 | COVERED |

### docs/ (4 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| docs/architecture.md | Section 1 | REQ-068 | COVERED |
| docs/api_reference.md | Section 1 | REQ-069 | COVERED |
| docs/mcp_tools.md | Section 1 | REQ-070 | COVERED |
| docs/deployment.md | Section 1 | REQ-071 | COVERED |

### sample_data/ (8 files)

| File | Architecture Plan | PRD Requirement | Status |
|---|---|---|---|
| sample_data/sample_prd.md | Section 1 | REQ-023 | COVERED |
| sample_data/sample_service_map.yaml | Section 1 | REQ-024 | COVERED |
| sample_data/sample_openapi.yaml | Section 1 | REQ-037 | COVERED |
| sample_data/sample_asyncapi.yaml | Section 1 | REQ-038 | COVERED |
| sample_data/sample_codebase/auth_service/auth.py | Section 1 | REQ-051 | COVERED |
| sample_data/sample_codebase/auth_service/models.py | Section 1 | REQ-051 | COVERED |
| sample_data/sample_codebase/billing_service/billing.ts | Section 1 | REQ-051 | COVERED |
| sample_data/sample_codebase/billing_service/types.ts | Section 1 | REQ-051 | COVERED |

---

## MCP Tool Coverage

### Architect MCP Server (3 tools)

| Tool | Server | PRD Requirement | Parameters OK | Return OK | Status |
|---|---|---|---|---|---|
| get_service_map() | Architect | REQ-059 | YES (no params) | YES (ServiceMap dict) | OK |
| get_contracts_for_service(service_name) | Architect | REQ-059 | YES (service_name: str) | YES (list of contract dicts with id/role/type/counterparty/summary) | OK |
| get_domain_model() | Architect | REQ-059 | YES (no params) | YES (DomainModel dict) | OK |

### Contract Engine MCP Server (6 tools)

| Tool | Server | PRD Requirement | Parameters OK | Return OK | Status |
|---|---|---|---|---|---|
| get_contract(contract_id) | Contract Engine | REQ-060 | YES (contract_id: str) | YES (full contract dict or None) | OK |
| validate_endpoint(service_name, method, path, response_body, status_code) | Contract Engine | REQ-060 | YES (5 params with defaults) | YES (dict with valid/violations) | OK |
| generate_tests(contract_id, framework, include_negative) | Contract Engine | REQ-060 | YES (3 params with defaults) | YES (test file content string) | OK |
| check_breaking_changes(contract_id, new_spec) | Contract Engine | REQ-060 | YES (2 params) | YES (list of BreakingChange dicts) | OK |
| mark_implemented(contract_id, service_name, evidence_path) | Contract Engine | REQ-060 | YES (3 params) | YES (dict with marked/total/all_implemented) | OK |
| get_unimplemented_contracts(service_name) | Contract Engine | REQ-060 | YES (optional service_name) | YES (list of unimplemented contract dicts) | OK |

### Codebase Intelligence MCP Server (7 tools)

| Tool | Server | PRD Requirement | Parameters OK | Return OK | Status |
|---|---|---|---|---|---|
| find_definition(symbol, language) | Codebase Intel | REQ-057 | YES (symbol: str, language: optional) | YES (location dict or None) | OK |
| find_callers(symbol, max_results) | Codebase Intel | REQ-057 | YES (symbol: str, max_results=50) | YES (list of caller dicts) | OK |
| find_dependencies(file_path) | Codebase Intel | REQ-057 | YES (file_path: str) | YES (imports/imported_by/transitive/circular dicts) | OK |
| search_semantic(query, language, service_name, n_results) | Codebase Intel | REQ-057 | YES (4 params with defaults) | YES (list of result dicts) | OK |
| get_service_interface(service_name) | Codebase Intel | REQ-057 | YES (service_name: str) | YES (interface dict) | OK |
| check_dead_code(service_name) | Codebase Intel | REQ-057 | YES (optional service_name) | YES (list of dead code dicts) | OK |
| register_artifact(file_path, service_name) | Codebase Intel | REQ-057 | YES (2 params) | YES (stats dict with indexed/symbols/deps/errors) | OK |

**MCP Tool Summary: 16/16 tools FULLY COVERED with correct parameters and return types.**

---

## Database Table Coverage

### architect.db (3 tables)

| Table | Database | PRD Requirement | Columns OK | Indexes OK | Status |
|---|---|---|---|---|---|
| service_maps | architect.db | REQ-007 | YES (id, project_name, prd_hash, map_json, build_cycle_id, generated_at) | YES (idx_smap_project, idx_smap_prd) | OK |
| domain_models | architect.db | REQ-007 | YES (id, project_name, model_json, generated_at) | YES (idx_dmodel_project) | OK |
| decomposition_runs | architect.db | REQ-007 | YES (id, prd_content_hash, service_map_id, domain_model_id, validation_issues, interview_questions, status, started_at, completed_at) | YES + CHECK(status) | OK |

### contracts.db (6 tables)

| Table | Database | PRD Requirement | Columns OK | Indexes OK | Status |
|---|---|---|---|---|---|
| build_cycles | contracts.db | REQ-007 | YES (id, project_name, started_at, completed_at, status, services_planned, services_completed, total_cost_usd) | YES (idx_build_cycles_status) + CHECK(status) | OK |
| contracts | contracts.db | REQ-007, TECH-012 | YES (id, type, version, service_name, spec_json, spec_hash, status, build_cycle_id, created_at, updated_at) | YES (5 indexes) + UNIQUE(service_name, type, version) + CHECK(type, status) | OK |
| contract_versions | contracts.db | REQ-007 | YES (id, contract_id, version, spec_hash, build_cycle_id, is_breaking, change_summary, created_at) | YES (idx_versions_contract, idx_versions_build) + FK | OK |
| breaking_changes | contracts.db | REQ-007 | YES (id, contract_version_id, change_type, json_path, old_value, new_value, severity, affected_consumers, created_at) | YES (idx_breaking_version) + CHECK(severity) + FK | OK |
| implementations | contracts.db | REQ-007 | YES (id, contract_id, service_name, evidence_path, status, verified_at, created_at) | YES (3 indexes) + UNIQUE(contract_id, service_name) + CHECK(status) + FK | OK |
| test_suites | contracts.db | REQ-007 | YES (id, contract_id, framework, test_code, test_count, generated_at) | YES (idx_tests_contract) + CHECK(framework) + FK | OK |

### symbols.db (5 tables)

| Table | Database | PRD Requirement | Columns OK | Indexes OK | Status |
|---|---|---|---|---|---|
| indexed_files | symbols.db | REQ-007 | YES (file_path, language, service_name, file_hash, loc, indexed_at) | YES (3 indexes) + CHECK(language) | OK |
| symbols | symbols.db | REQ-007 | YES (id, file_path, symbol_name, kind, language, service_name, line_start, line_end, signature, docstring, is_exported, parent_symbol, chroma_id, indexed_at) | YES (6 indexes) + CHECK(kind) + FK | OK |
| dependency_edges | symbols.db | REQ-007 | YES (id, source_symbol_id, target_symbol_id, relation, source_file, target_file, line, created_at) | YES (5 indexes) + UNIQUE(source, target, relation) + CHECK(relation) | OK |
| import_references | symbols.db | REQ-007 | YES (id, source_file, target_file, imported_names, line, is_relative) | YES (2 indexes) + UNIQUE(source, target, line) + FK | OK |
| graph_snapshots | symbols.db | REQ-007 | YES (id, graph_json, node_count, edge_count, created_at) | N/A (no indexes specified, PK only) | OK |

**Database Summary: 14/14 tables FULLY COVERED with correct schemas, indexes, and constraints.**

---

## API Endpoint Coverage

### Architect Service (4 endpoints)

| Endpoint | PRD Requirement | SVC ID | Status |
|---|---|---|---|
| POST /api/decompose | REQ-020, WIRE-006 | SVC-001 | OK |
| GET /api/service-map | REQ-021 | SVC-002 | OK |
| GET /api/domain-model | REQ-022 | SVC-003 | OK |
| GET /api/health | INT-001 | SVC-004 | OK |

### Contract Engine Service (11 endpoints)

| Endpoint | PRD Requirement | SVC ID | Status |
|---|---|---|---|
| POST /api/contracts | REQ-033 | SVC-005 | OK |
| GET /api/contracts | REQ-033 | SVC-006 | OK |
| GET /api/contracts/{id} | REQ-033 | SVC-007 | OK |
| DELETE /api/contracts/{id} | REQ-033 | SVC-008 | OK |
| POST /api/validate | REQ-034 | SVC-009 | OK |
| GET /api/breaking-changes/{id} | REQ-035 | SVC-010 | OK |
| POST /api/implementations/mark | REQ-036 | SVC-011 | OK |
| GET /api/implementations/unimplemented | REQ-036 | SVC-012 | OK |
| POST /api/tests/generate/{id} | REQ-041 | N/A | OK |
| GET /api/tests/{id} | REQ-041 | N/A | OK |
| GET /api/health | INT-001 | N/A | OK |

### Codebase Intelligence Service (6 endpoints)

| Endpoint | PRD Requirement | Status |
|---|---|---|
| GET /api/symbols | REQ-058 | OK |
| GET /api/dependencies | REQ-058 | OK |
| POST /api/search | REQ-058 | OK |
| POST /api/artifacts | REQ-058 | OK |
| GET /api/dead-code | REQ-058 | OK |
| GET /api/health | INT-001, REQ-058 | OK |

---

## Milestone Dependency Verification

Architecture plan Appendix C defines the dependency graph:

```
M1 (Core Models + Shared)
  |--- M2 (Architect) ---> M7 (MCP Servers) ---> M8 (Integration)
  |--- M3 (Contract Core) ---> M4 (Test Gen) ---> M7
  |--- M5 (CI L1+L2) ---> M6 (CI L3+MCP) ---> M8
```

PRD milestones match this order. No early-milestone requirement depends on a later-milestone feature:

| Milestone | PRD Dependencies (Implicit) | Architecture Dependencies | Match |
|---|---|---|---|
| M1 | None | None | YES |
| M2 | Needs M1 models+DB | milestone-1 | YES |
| M3 | Needs M1 models+DB | milestone-1 | YES |
| M4 | Needs M3 contract_store | milestone-3 | YES |
| M5 | Needs M1 models+DB | milestone-1 | YES |
| M6 | Needs M5 AST+symbols | milestone-5 | YES |
| M7 | Needs M2 storage + M3 services + M4 test_gen | milestone-2, milestone-3, milestone-4 | YES |
| M8 | Needs M6 MCP + M7 MCP | milestone-6, milestone-7 | YES |

**Milestone Dependencies: CORRECT. No circular or forward dependencies.**

---

## Cross-Service Integration

| Integration Point | PRD Coverage | Status |
|---|---|---|
| Architect -> Contract Engine HTTP (register stubs) | REQ-064, WIRE-021, TECH-029 | COVERED |
| Architect MCP -> Contract Engine HTTP (get_contracts_for_service) | REQ-059, TECH-026 | COVERED |
| Inter-service Docker networking | REQ-062, WIRE-022 | COVERED |
| Docker service -> health check | REQ-062, TECH-030 | COVERED |
| MCP server -> service layer wiring (Architect) | WIRE-018 | COVERED |
| MCP server -> service layer wiring (Contract Engine) | WIRE-019 | COVERED |
| MCP server -> service layer wiring (Codebase Intel) | WIRE-015 | COVERED |
| Dockerfiles copy src/shared/ | WIRE-023 | COVERED |

---

## Critical Gaps

### ARCH-CRIT-001: Missing test requirement for test_contract_engine/test_schema_registry.py

- **What's missing**: The file `tests/test_contract_engine/test_schema_registry.py` is listed in the PRD project structure (line 169) and the architecture plan, but there is NO TEST-xxx requirement that specifies what tests it should contain. REQ-029 defines the SchemaRegistry implementation but has no corresponding test requirement.
- **Impact**: The SchemaRegistry (register_schema, get_schema, list_schemas, get_consumers methods) will be implemented via REQ-029 but will have NO dedicated test coverage. The agent may not create this test file at all since there is no requirement for it.
- **Fix**: Add a test requirement like: `TEST-0XX: tests/test_contract_engine/test_schema_registry.py -- test register_schema stores and retrieves a schema, test list_schemas with owning_service filter, test get_consumers returns correct service list, test duplicate registration updates existing schema.` Place in Milestone 3.

### ARCH-CRIT-002: Missing test requirement for test_codebase_intelligence/test_routers.py

- **What's missing**: The file `tests/test_codebase_intelligence/test_routers.py` is listed in the PRD project structure (line 189) and the architecture plan, but there is NO TEST-xxx requirement that specifies what tests it should contain. REQ-058 defines the FastAPI endpoints but has no router integration test requirement.
- **Impact**: The Codebase Intelligence REST API endpoints (GET /api/symbols, GET /api/dependencies, POST /api/search, POST /api/artifacts, GET /api/dead-code) will be implemented but will have NO dedicated FastAPI TestClient integration tests. The test_architect/test_routers.py has TEST-010, and test_contract_engine/test_routers.py has TEST-018, but the Codebase Intelligence equivalent is missing.
- **Fix**: Add a test requirement like: `TEST-0XX: tests/test_codebase_intelligence/test_routers.py -- integration tests with FastAPI TestClient for all 6 endpoints: GET /api/symbols returns symbols or empty list, GET /api/dependencies returns dependency info or 404, POST /api/search returns semantic results, POST /api/artifacts registers file and returns stats, GET /api/dead-code returns dead code list, GET /api/health returns 200 with HealthStatus.` Place in Milestone 6.

---

## Warning Gaps

### ARCH-WARN-001: Architect prompts/ directory (4 files) has no requirements

- **What's missing**: `src/architect/prompts/__init__.py`, `src/architect/prompts/decomposition_prompt.py`, `src/architect/prompts/interview_prompt.py`, `src/architect/prompts/validation_prompt.py` are all listed in the PRD file structure but have no REQ-xxx covering their implementation.
- **Impact**: These files won't be created during the build. REQ-013 explicitly says "Use regex and NLP heuristics, not LLM calls" so these prompt files may be for future LLM integration.
- **Fix**: Either (a) add requirements for placeholder implementations with exported prompt strings, or (b) remove these 4 files from the PRD file structure since Build 1 is deterministic/non-LLM.

### ARCH-WARN-002: Per-service config.py files have no requirements

- **What's missing**: `src/architect/config.py`, `src/contract_engine/config.py`, `src/codebase_intelligence/config.py` are listed in both the PRD file structure and architecture plan, but REQ-008 puts all configuration classes in `src/shared/config.py`. No requirement creates the per-service config files.
- **Impact**: If a service needs configuration beyond what's in SharedConfig, there's no designated file for it. The per-service config.py files could re-export from shared or add service-specific settings.
- **Fix**: Either (a) add a requirement: "Each service's config.py imports and re-exports its config class from src/shared/config.py for local convenience," or (b) remove these files from the file structure since all configs are in shared/config.py.

### ARCH-WARN-003: Contract Engine storage layer files have no requirements

- **What's missing**: `src/contract_engine/storage/contract_db.py` and `src/contract_engine/storage/implementation_db.py` are listed in the architecture plan as "Direct SQLite operations" files, but the PRD's requirements (REQ-025, REQ-032) put DB operations directly in the service classes (ContractStore, ImplementationTracker use ConnectionPool directly).
- **Impact**: Either the storage files are unnecessary (services do DB directly) or the services should delegate to storage (clean layering). The PRD requirements are internally consistent but don't match the file structure.
- **Fix**: Either (a) add requirements for these storage files and update REQ-025/REQ-032 to delegate to them, or (b) remove them from the file structure since services handle DB directly.

### ARCH-WARN-004: src/__init__.py has no explicit requirement

- **What's missing**: `src/__init__.py` is listed in the file structure but no requirement or wiring spec creates it. WIRE-003 only covers "Each service's __init__.py."
- **Impact**: Minor. Python needs this file for the `src` package to be importable. It would likely be created as part of scaffolding, but strictness says it should be covered.
- **Fix**: Expand WIRE-003 to include: "src/__init__.py must be created as an empty file to enable the src package."

### ARCH-WARN-005: Subdirectory __init__.py files rely on implicit creation

- **What's missing**: 12 __init__.py files in subdirectories (routers/, services/, storage/, parsers/) across all 3 services have no explicit requirements. They're listed in the file structure but rely on implicit creation.
- **Impact**: Minor. These are boilerplate files needed for Python packaging. The agent-team system typically creates them, but without explicit requirements they could be missed.
- **Fix**: Add a single wiring requirement: "All Python package directories shown in the file structure must contain an __init__.py file (empty or with relevant exports)."

---

## Requirement Count Summary

| Category | Count | Notes |
|---|---|---|
| Functional Requirements (REQ-xxx) | 73 | REQ-001 through REQ-073 |
| Technical Requirements (TECH-xxx) | 31 | TECH-001 through TECH-031 |
| Wiring Requirements (WIRE-xxx) | 23 | WIRE-001 through WIRE-023 |
| Test Requirements (TEST-xxx) | 39 | TEST-001 through TEST-039 |
| Integration Requirements (INT-xxx) | 5 | INT-001 through INT-005 |
| Service Wiring Map (SVC-xxx) | 12 | SVC-001 through SVC-012 |
| **Total** | **183** | |

---

## Verdict

The PRD is **95%+ complete** relative to the architecture plan. The 2 critical gaps are easily fixable by adding 2 test requirements (TEST-0XX for schema_registry and CI routers). The 5 warnings are minor structural inconsistencies between the file structure and requirements.

**Recommended fixes before build:**

1. Add TEST-0XX for `test_schema_registry.py` in Milestone 3
2. Add TEST-0XX for `test_codebase_intelligence/test_routers.py` in Milestone 6
3. Either remove or add requirements for the `src/architect/prompts/` directory
4. Clarify whether per-service `config.py` files are needed or remove from structure
5. Clarify whether `storage/contract_db.py` and `storage/implementation_db.py` are needed or remove from structure
