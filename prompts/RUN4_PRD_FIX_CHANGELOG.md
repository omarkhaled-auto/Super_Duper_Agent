# RUN4_PRD.md Fix Changelog

> **Date**: 2026-02-15
> **Applied by**: fix-pass agent
> **Sources**: 4 review files (FORMAT, CROSS-BUILD, EXECUTABILITY, COMPLETENESS)
> **Total changes**: 19 fixes across 4 categories
> **New checklist items**: +1 (WIRE-021)
> **Updated total**: 119 -> 120 checklist items

---

## Category 1: SVC Response DTO Field Completions (Cross-Build Review H-1)

All 11 SVC response DTOs updated to match ground-truth schemas from RUN4_CROSS_BUILD_INTERFACES.md and BUILD1_PRD.md.

### Fix 1: SVC-001 — DecompositionResult (Milestone 2 SVC table)

**Before**: `DecompositionResult { service_map: dict, domain_model: dict, contract_stubs: list, validation_issues: list }`
**After**: `DecompositionResult { service_map: dict, domain_model: dict, contract_stubs: list, validation_issues: list, interview_questions: list[string] }`
**Added field**: `interview_questions: list[string]`
**Source**: BUILD1 REQ-002 + XREF Section 1.1

### Fix 2: SVC-002 — ServiceMap (Milestone 2 SVC table)

**Before**: `ServiceMap { project_name: string, services: list, generated_at: string }`
**After**: `ServiceMap { project_name: string, services: list, generated_at: string, prd_hash: string, build_cycle_id: string|null }`
**Added fields**: `prd_hash: string`, `build_cycle_id: string|null`
**Source**: XREF Section 1.1 + BUILD1 REQ-002

### Fix 3: SVC-003 — get_contracts_for_service list element (Milestone 2 SVC table)

**Before**: `list { id: string, role: string, type: string, counterparty: string }`
**After**: `list { id: string, role: string, type: string, counterparty: string, summary: string }`
**Added field**: `summary: string`
**Source**: XREF Section 1.1

### Fix 4: SVC-005 — ContractEntry (Milestone 2 SVC table)

**Before**: `ContractEntry { id: string, service_name: string, type: string, version: string, spec: dict }`
**After**: `ContractEntry { id: string, service_name: string, type: string, version: string, spec: dict, spec_hash: string, status: string }`
**Added fields**: `spec_hash: string`, `status: string`
**Source**: BUILD2 TECH-014 (ContractInfo) + XREF 1.2

### Fix 5: SVC-008 — check_breaking_changes list element (Milestone 2 SVC table)

**Before**: `list { change_type: string, path: string, severity: string }`
**After**: `list { change_type: string, path: string, severity: string, old_value: string|null, new_value: string|null, affected_consumers: list[string] }`
**Added fields**: `old_value: string|null`, `new_value: string|null`, `affected_consumers: list[string]`
**Source**: XREF 1.2

### Fix 6: SVC-009 — MarkResult (Milestone 2 SVC table)

**Before**: `MarkResult { marked: boolean, total_implementations: number }`
**After**: `MarkResult { marked: boolean, total_implementations: number, all_implemented: boolean }`
**Added field**: `all_implemented: boolean`
**Source**: XREF 1.2

### Fix 7: SVC-010 — get_unimplemented_contracts list element (Milestone 2 SVC table)

**Before**: `list { id: string, type: string, expected_service: string }`
**After**: `list { id: string, type: string, expected_service: string, version: string, status: string }`
**Added fields**: `version: string`, `status: string`
**Source**: XREF 1.2

### Fix 8: SVC-011 — DefinitionResult (Milestone 2 SVC table)

**Before**: `DefinitionResult { file_path: string, line_start: number, kind: string }`
**After**: `DefinitionResult { file_path: string, line_start: number, line_end: number, kind: string, signature: string|null, docstring: string|null }`
**Added fields**: `line_end: number`, `signature: string|null`, `docstring: string|null`
**Source**: BUILD1 REQ-057 + XREF 1.3

### Fix 9: SVC-014 — search_semantic list element (Milestone 2 SVC table)

**Before**: `list { file_path: string, content: string, score: number }`
**After**: `list { chunk_id: string, file_path: string, symbol_name: string|null, content: string, score: number, language: string, service_name: string|null, line_start: number, line_end: number }`
**Added fields**: `chunk_id: string`, `symbol_name: string|null`, `language: string`, `service_name: string|null`, `line_start: number`, `line_end: number`
**Source**: XREF 1.3

### Fix 10: SVC-015 — ServiceInterface (Milestone 2 SVC table)

**Before**: `ServiceInterface { endpoints: list, events_published: list, events_consumed: list }`
**After**: `ServiceInterface { service_name: string, endpoints: list, events_published: list, events_consumed: list, exported_symbols: list }`
**Added fields**: `service_name: string`, `exported_symbols: list`
**Source**: XREF 1.3

### Fix 11: SVC-016 — check_dead_code list element (Milestone 2 SVC table)

**Before**: `list { symbol_name: string, file_path: string, kind: string, confidence: string }`
**After**: `list { symbol_name: string, file_path: string, kind: string, line: number, service_name: string|null, confidence: string }`
**Added fields**: `line: number`, `service_name: string|null`
**Source**: XREF 1.3

### Fix 12: SVC-017 — ArtifactResult (Milestone 2 SVC table)

**Before**: `ArtifactResult { indexed: boolean, symbols_found: number }`
**After**: `ArtifactResult { indexed: boolean, symbols_found: number, dependencies_found: number, errors: list[string] }`
**Added fields**: `dependencies_found: number`, `errors: list[string]`
**Source**: BUILD2 TECH-024 + XREF 1.3

---

## Category 2: Executability Clarifications (Executability Review)

### Fix 13: TECH-002 — External schema reference inlined (Milestone 1)

**Before**: `Run4State JSON schema must match the schema defined in RUN4_ARCHITECTURE_PLAN.md Section 7.1 — including Finding dataclass with finding_id...`
**After**: `Run4State JSON schema must include the Finding dataclass with these 10 fields: finding_id (FINDING-NNN pattern), priority (P0-P3), system (Build 1/Build 2/Build 3/Integration), component (specific module/function), evidence (exact reproduction or test output), recommendation (specific fix action), resolution (FIXED/OPEN/WONTFIX), fix_pass_number (int), fix_verification (test ID confirming fix), created_at (ISO 8601 timestamp). The canonical schema definition is REQ-029 in this PRD.`
**Change**: Removed external document dependency, inlined all 10 fields with types, declared REQ-029 as canonical source, added `created_at` field.

### Fix 14: REQ-026 — Schemathesis configuration and per-step assertions (Milestone 4)

**Before**: Generic "run contract compliance via Schemathesis against live services; run cross-service integration tests (register -> login -> create order -> notification)"
**After**: Added Schemathesis config (point at /openapi.json per service, stateful mode, JWT auth) and 4 per-step assertions with expected status codes and response body fields.
**Change**: Specifies which OpenAPI spec URL, Schemathesis profile, and exact per-step assertions (POST /register -> 201 with {id, email, created_at}, etc.)

### Fix 15: REQ-027 — Quality Gate Layer 3/4 checks enumerated (Milestone 4)

**Before**: Generic "security, CORS, logging, secrets, Docker, health scans" for Layer 3; "adversarial review" for Layer 4.
**After**: Layer 3 enumerated: SEC-SCAN-001 (hardcoded secrets regex), CORS-001 (no wildcard CORS), LOG-001 (no print()), LOG-002 (request logging middleware), DOCKER-001 (HEALTHCHECK instruction), DOCKER-002 (no :latest tags). Layer 4 enumerated: DEAD-001 (events published but never consumed), DEAD-002 (contracts registered but never validated), ORPHAN-001 (service in compose with no Traefik route), NAME-001 (naming consistency).
**Change**: 10 specific static analysis checks replace vague category names.

### Fix 16: REQ-033 + Config — Budget hard stop (Milestone 5 + Config)

**Before**: "budget exhausted" listed as hard stop but no budget field in config.
**After**: Added `max_budget_usd: 100.0` to config.yaml template under run4 section; updated REQ-001 to mention `max_budget_usd: float = 100.0`.
**Change**: Budget field now exists for the hard stop to check against.

### Fix 17: REQ-034 — KLOC and artifacts definitions (Milestone 6)

**Before**: `violation_density per KLOC` and `artifacts_required` undefined.
**After**: Added definitions: `violation_density = total_violations / (total_lines_of_code / 1000)` counting .py files in service source directories (excluding tests, __pycache__, venv); artifacts_required per service (5 items): Dockerfile, requirements.txt or pyproject.toml, README.md, OpenAPI/AsyncAPI spec file, health check endpoint (/health).
**Change**: Both scoring terms now have concrete, implementable definitions.

### Fix 18: REQ-041 — Dark corners test procedures (Milestone 6)

**Before**: 5 scenarios listed as topics without test procedures or pass/fail criteria.
**After**: Each scenario has TEST, PASS, and FAIL criteria: (1) MCP race: asyncio.gather 3 servers, all healthy within timeout; (2) DNS: curl from architect to contract-engine, HTTP 200; (3) File conflicts: zero cross-directory writes; (4) Resume: SIGINT at phase 3, resume from phase 3; (5) Large PRD: 200KB PRD, valid ServiceMap within 2x timeout.
**Change**: All 5 scenarios are now fully executable test specifications.

### Fix 19: WIRE-017 — Docker network assertions (Milestone 4)

**Before**: "correct network topology (frontend + backend networks)" without specific assertions.
**After**: Verify via docker network inspect: frontend contains traefik + all application services; backend contains postgres, redis + all application services; traefik NOT on backend; postgres/redis NOT on frontend.
**Change**: 4 specific docker network assertions replace vague topology check.

---

## Category 3: Completeness Gap Fixes (Completeness Review)

### Fix 20: WIRE-021 — Agent Teams positive-path test (NEW item, Milestone 3)

**Added**: `WIRE-021: Agent Teams positive-path test — when config.agent_teams.enabled=True and Claude CLI is available, AgentTeamsBackend.execute_wave() completes with task state progression (pending -> in_progress -> completed); verify TaskCreate, TaskUpdate, and SendMessage are invoked during within-service coordination`
**Source**: Completeness Review MISS-1 — B2-SC-1 only had degradation path tests (WIRE-013, WIRE-014), no positive path.
**Impact**: WIRE-xxx count increased from 20 to 21. Total checklist items from 119 to 120.

### Fix 21: B3-05 — CLI commands expanded (Verification Test Matrix)

**Before**: `test_cli_commands | All commands registered`
**After**: `test_cli_commands | All 6 commands registered and callable: init, plan, build, integrate, verify, run`
**Source**: Completeness Review PART-1 — B3-SC-5 was generic, now enumerates all 6 commands.

---

## Category 4: Format Documentation Notes (Format Review)

### Fix 22: SVC table format note — Milestone 2 (FORMAT MEDIUM-1)

**Added**: Note block above MCP Tool-to-Client Wiring Map table explaining the 6-column format is intentional for MCP stdio tool calls (not HTTP APIs) and that `_parse_svc_table()` API contract scanner does not apply.

### Fix 23: SVC table format note — Milestone 3 (FORMAT MEDIUM-1)

**Added**: Note block above Subprocess Wiring Map table explaining the 6-column subprocess wiring format.

### Fix 24: Config.yaml `run4:` section note (FORMAT MEDIUM-2)

**Added**: Note block above config.yaml template explaining the `run4:` section contains fields outside `AgentTeamConfig` schema, parsed by Run4's own `Run4Config` dataclass (REQ-001). `_dict_to_config()` silently ignores unknown top-level keys.

---

## Category 5: State Machine Transitions (Cross-Build Review H-2)

### Fix 25: Appendix B — Missing transitions added

**Added 3 rows to state machine transition table**:
- Row 11: `fail | [non-terminal] | failed | unrecoverable_error | None`
- Row 12: `retry_architect | architect_running | architect_running | retries_remaining | Build 1 Architect MCP`
- Row 13: `skip_contracts | contracts_registering | builders_running | no_contracts_needed | None`

**Source**: Cross-Build Review H-2 — BUILD3_PRD has 13 transitions, RUN4 Appendix B had only 10.

---

## Category 6: Structural Additions (Executability Cross-Cutting)

### Fix 26: Source directory structure added (Milestone 1)

**Added**: Source directory layout (`src/run4/`) with 7 modules: config.py, state.py, mcp_health.py, builder.py, fix_pass.py, scoring.py, audit_report.py. Placed before the existing test directory structure.
**Source**: Executability Review cross-cutting issue — PRD specified test locations but not production code locations.

### Fix 27: Docker network topology note (Docker Compose section)

**Added**: Note block above Network Architecture diagram explaining Build 1 standalone uses `super-team-net` but the integrated system uses frontend+backend split via docker-compose.run4.yml overlay.
**Source**: Cross-Build Review M-2 — apparent inconsistency with BUILD1_PRD standalone topology.

---

## Not Changed (Review Items Assessed as No-Action)

| Review | Item | Reason |
|--------|------|--------|
| Format | LOW-1: All review_cycles=0 | Intentional for verification run |
| Format | LOW-2: No browser_testing section | Correct for backend-only run; defaults to disabled |
| Cross-Build | M-1: Depth gating cross-build effects | Already covered by REQ-018 which tests all 4 depth levels; WIRE-017 verifies integrated topology |
| Cross-Build | L-1: L1->L2->L3->L4 enforcement | Already covered by B3-04 test which verifies gate layer order |
| Cross-Build | L-2: ChromaDB 120s timeout test | Already covered by config mcp_first_start_timeout_ms: 120000 + REQ-041 dark corners scenario 1 |
| Cross-Build | L-3: HTTP inter-service timeout values | Implementation detail, not PRD-level specification |
| Completeness | MISS-2: Contract immutability test | MEDIUM priority, not in scope for this fix pass |
| Completeness | MISS-3: Pact verification test | MEDIUM priority, not in scope for this fix pass |
| Completeness | MISS-4: interview_questions assertion | Already addressed by SVC-001 DTO fix (Fix 1 above) |
| Completeness | PART-2: State machine transitions | Addressed by Appendix B additions (Fix 25) |
| Completeness | PART-3: Boundary tests | LOW-MEDIUM priority, not in scope |
| Completeness | PART-4: Contract compliance tracking doc | LOW priority |

---

## Updated Counts

| Metric | Before | After |
|--------|--------|-------|
| Total checklist items | 119 | **120** |
| REQ-xxx | 42 | 42 (no change) |
| TECH-xxx | 9 | 9 (no change) |
| INT-xxx | 7 | 7 (no change) |
| WIRE-xxx | 20 | **21** (+1: WIRE-021) |
| SVC-xxx | 20 | 20 (no change) |
| TEST-xxx | 18 | 18 (no change) |
| SEC-xxx | 3 | 3 (no change) |
| SVC DTOs with complete fields | 5/17 (29.4%) | **17/17 (100%)** |
| State machine transitions | 10 | **13** |

---

## Verification

After applying all fixes:
- Counted 120 `- [ ]` items in PRD (matches Appendix C)
- Counted 21 WIRE items (matches Appendix C)
- All items preserve `(review_cycles: 0)` suffix
- No milestone structure changes (only content within milestones modified)
- Sequential prefix numbering maintained (WIRE-021 follows WIRE-020)
