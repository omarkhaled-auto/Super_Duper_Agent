# Build 3 PRD — Architectural Soundness Review

> **Reviewer**: Architectural Soundness Reviewer
> **Date**: 2026-02-14
> **Documents Reviewed**: BUILD3_PRD.md, BUILD3_ARCHITECTURE_PLAN.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md, BUILD1_PRD.md, BUILD2_PRD.md
> **Methodology**: Systematic checklist evaluation with line-level references

---

## 1. Completeness vs Vision

### 1.1 Every feature from SUPER_TEAM reference Build 3 section is covered

**PASS**

The vision document (SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md, lines 296-378) defines 7 milestones for Build 3. Every feature maps to at least one PRD requirement:

| Vision Feature | PRD Coverage | Requirements |
|---|---|---|
| M1: Integration Test Framework (Docker, Traefik, cross-service runner) | PRD M3 + M6 | REQ-017..020, REQ-046..049 |
| M2: Contract Compliance Verification (Schemathesis, Pact, fix loop) | PRD M2 | REQ-012..016 |
| M3: Cross-Service Integration Tests (flow generator, data flow tracer, boundary) | PRD M3 | REQ-017..020 |
| M4: Quality Gate Layers 3-4 (security, observability, adversarial) | PRD M4 | REQ-021..031 |
| M5: Super Orchestrator (CLI, state mgmt, cost, progress, failure recovery) | PRD M5 | REQ-032..039 |
| M6: Configuration + CLI (YAML, 6 CLI commands) | PRD M6 | REQ-040..050 |
| M7: End-to-End Test | PRD M7 | REQ-051..060 |

### 1.2 Architecture plan's class hierarchy fully represented in requirements

**PASS**

Every class from BUILD3_ARCHITECTURE_PLAN.md sections 3.1-3.14 has a corresponding requirement:

- Enums (ServiceStatus, QualityLevel, GateVerdict) -> REQ-001 (PRD line 139)
- Data models (ServiceInfo, BuilderResult, ContractViolation, ScanViolation, LayerResult, QualityGateReport, IntegrationReport) -> REQ-001 (PRD line 139)
- Protocols (PhaseExecutor, QualityScanner) -> REQ-002 (PRD line 141)
- Constants (all scan codes, phase names, timeouts) -> REQ-003 (PRD line 143)
- Utils (atomic_write_json, load_json, ensure_dir) -> REQ-004 (PRD line 145)
- Config (SuperOrchestratorConfig + 4 nested configs) -> REQ-005 (PRD line 147)
- PipelineState -> REQ-006 (PRD line 149)
- PipelineCostTracker + PhaseCost -> REQ-007 (PRD line 151)
- State machine (11 states, 13 transitions, create_pipeline_machine) -> REQ-008 (PRD line 153)
- Exceptions (6 classes) -> REQ-009 (PRD line 155)
- GracefulShutdown -> REQ-010 (PRD line 157)
- SchemathesisRunner -> REQ-012 (PRD line 197)
- PactManager -> REQ-013 (PRD line 199)
- ContractComplianceVerifier -> REQ-014 (PRD line 201)
- ContractFixLoop -> REQ-015 (PRD line 203)
- CrossServiceTestGenerator -> REQ-017 (PRD line 247)
- CrossServiceTestRunner -> REQ-018 (PRD line 249)
- DataFlowTracer -> REQ-019 (PRD line 251)
- BoundaryTester -> REQ-020 (PRD line 253)
- QualityGateEngine -> REQ-021 (PRD line 283)
- Layer1Scanner -> REQ-022 (PRD line 285)
- Layer2Scanner -> REQ-023 (PRD line 287)
- SecurityScanner -> REQ-024 (PRD line 289)
- ObservabilityChecker -> REQ-025 (PRD line 291)
- DockerSecurityScanner -> REQ-026 (PRD line 293)
- Layer3Scanner -> REQ-027 (PRD line 295)
- AdversarialScanner -> REQ-028 (PRD line 297)
- Layer4Scanner -> REQ-029 (PRD line 299)
- ScanAggregator -> REQ-030 (PRD line 301)
- ComposeGenerator -> REQ-046 (PRD line 430)
- TraefikConfigGenerator -> REQ-047 (PRD line 432)
- DockerOrchestrator -> REQ-048 (PRD line 434)
- ServiceDiscovery -> REQ-049 (PRD line 436)
- Rich display functions -> REQ-045 (PRD line 428)
- CLI with 8 commands -> REQ-040 (PRD line 418)

### 1.3 No architectural components mentioned in the plan but missing from the PRD

**PASS** (with one minor note)

All modules from the architecture plan's project structure (Plan lines 99-183) have corresponding requirements. The `exceptions.py` module is covered by REQ-009. The `__init__.py` files are covered by REQ-011.

**Note**: The architecture plan section 8.1 lists 7 Codebase Intelligence MCP tools. The PRD's SVC tables only cover 3 of them (SVC-004/005/006). See section 3.1 below for details.

### 1.4 All security/observability scan codes from the vision are included

**PASS** (exceeds vision)

The vision document says "30 security/observability scan codes." The PRD defines 40 scan codes in REQ-003 (PRD line 143):

| Category | Codes | Count |
|---|---|---|
| Security | SEC-001..006 | 6 |
| CORS | CORS-001..003 | 3 |
| Logging | LOG-001, LOG-004, LOG-005 | 3 |
| Trace | TRACE-001 | 1 |
| Secrets | SEC-SECRET-001..012 | 12 |
| Docker | DOCKER-001..008 | 8 |
| Adversarial | ADV-001..006 | 6 |
| Health | HEALTH-001 | 1 |
| **Total** | | **40** |

The PRD exceeds the vision's "30" count. The additional 10 codes come from the expanded secrets scanning (SEC-SECRET-001..012 = 12, vs potentially being grouped under SEC-xxx in the original count). This is a positive discrepancy.

---

## 2. Milestone Dependencies

### 2.1 Milestone dependency chain is correct

**PASS**

PRD milestone dependency chain:

```
M1 (no deps) → M2 + M3 (parallel, both depend on M1)
                 ↓         ↓
                 M4 (depends on M2, M3)
                   ↓
                 M5 (depends on M4)
                   ↓
                 M6 (depends on M5)
                   ↓
                 M7 (depends on M5, M6)
```

This matches the architecture plan's DAG (Plan lines 1568-1608) with one refinement: the architecture plan shows M5 (CLI) and M6 (Tests) as parallelizable, while the PRD makes M6 (CLI+Docker) depend on M5 (Super Orchestrator). This is correct because the CLI wraps the pipeline, so it must be built after the pipeline.

### 2.2 No circular dependencies

**PASS**

The dependency graph is a strict DAG (directed acyclic graph). Every edge points from lower to higher milestone numbers. Verified by tracing:
- M1 has no dependencies
- M2 depends on M1 only
- M3 depends on M1 only
- M4 depends on M2, M3 (both are upstream of M4)
- M5 depends on M4 (upstream)
- M6 depends on M5 (upstream)
- M7 depends on M5, M6 (both upstream)

No back-edges exist.

### 2.3 Each milestone is self-contained enough to be implemented in isolation

**PASS**

Each milestone has:
- Clear input requirements (dependencies)
- Self-contained deliverables (specific files and classes)
- Own test requirements (TEST-xxx per milestone)
- Own wiring requirements (WIRE-xxx per milestone)

Milestone boundaries are clean. M2 and M3 can truly run in parallel since they share only M1's data models.

---

## 3. Integration with Build 1 + Build 2

### 3.1 INT-xxx requirements cover all Build 1 integration points

**PARTIAL PASS**

The PRD's INT requirements (INT-001 through INT-006, PRD lines 511-516) cover the major integration points. However, the architecture plan (Plan section 8.1, lines 1332-1365) lists 17 Build 1 MCP tools. The PRD's SVC tables only define SVC entries for a subset:

**Covered by SVC entries:**
- Architect: `decompose` (SVC-008), `get_service_map` (implied by SVC-008 response)
- Contract Engine: `create_contract` (SVC-009), `validate_spec` (SVC-010), `list_contracts` (SVC-011)
- Codebase Intelligence: `get_service_interface` (SVC-004), `find_dependencies` (SVC-005), `check_dead_code` (SVC-006)

**Missing from SVC tables (4 tools):**
- `find_definition(symbol)` — Used by Quality Gate for symbol tracing (Plan line 1358)
- `find_callers(symbol)` — Used by Quality Gate for impact analysis (Plan line 1359)
- `search_semantic(query)` — Used in adversarial review for discovery queries (Plan line 1361)
- `register_artifact(file_path, service_name)` — Used by Builders to register generated code (Plan line 1364) — this is a Build 2 concern, not Build 3

The first 3 tools would be consumed by the AdversarialScanner (REQ-028) but aren't specified as SVC requirements. The adversarial scanner's method signatures (detect_dead_events, detect_dead_contracts, detect_orphan_services) are defined but the underlying MCP tool calls aren't fully specified.

**Impact**: MEDIUM. The adversarial scanner will work with the 3 tools already specified (SVC-004/005/006) but won't have explicit contracts for the additional discovery capabilities.

**Recommendation**: Add SVC-020 through SVC-022 for find_definition, find_callers, and search_semantic in M4's SVC table.

### 3.2 INT-xxx requirements cover all Build 2 integration points

**PASS**

Build 2 integration points from the architecture plan (Plan section 11.2, lines 1628-1636):

| Integration | PRD Coverage |
|---|---|
| Builder dispatch (subprocess) | SVC-012 (PRD line 390) |
| Cost aggregation (RunState JSON) | REQ-034 parses builder STATE.json (PRD line 355) |
| Build report (artifacts) | BuilderResult in REQ-034 (PRD line 355) |
| Contract scanning (runs within Builder) | REQ-035 sets post_orchestration_scans.api_contract_scan (PRD line 357) |
| Config inheritance | REQ-035 generate_builder_config() (PRD line 357) |

**Minor gap**: The architecture plan mentions `generate_hooks_config()` (Plan line 1635) for quality gate hooks enforcement. REQ-035 does not include hooks configuration in the builder config generation. This means Builders launched by Build 3 won't have Build 2's quality gate hooks (TaskCompleted, TeammateIdle) configured. This is a LOW-severity gap because hooks are a Build 2 internal concern — the Builder still runs its full pipeline regardless.

### 3.3 Failure modes for missing Build 1/2 services are specified

**PASS**

- INT-001: Architect MCP unavailable -> ConfigurationError with clear message (PRD line 511)
- INT-002: Contract Engine MCP unavailable -> ConfigurationError (PRD line 512)
- INT-003: Build 2 agent-team CLI unavailable -> ConfigurationError (PRD line 513)
- INT-004: Docker Compose unavailable -> init command warns (PRD line 514)
- INT-005: Build 1 local or MCP -> config allows both modes (PRD line 515)
- INT-006: Lazy imports for Build 1/2 -> ImportError messages (PRD line 516)

### 3.4 Data flow between builds is clear

**PASS**

Data flow is explicitly specified in SVC tables:

- **Build 3 -> Build 1 (Architect)**: SVC-008 sends PRD text, receives ServiceMap + DomainModel + contract stubs
- **Build 3 -> Build 1 (Contract Engine)**: SVC-009/010/011 for contract CRUD
- **Build 3 -> Build 1 (Codebase Intelligence)**: SVC-004/005/006 for code queries
- **Build 3 -> Build 2 (Builders)**: SVC-012 sends config + PRD + depth, receives BuilderResult
- **Build 3 internal (Quality Gate -> Fix Loop -> Builders)**: SVC-014 feeds violations back via subprocess

---

## 4. Wiring Completeness

### 4.1 Every module that needs to communicate with another has a WIRE-xxx requirement

**PARTIAL PASS**

19 WIRE requirements (WIRE-001 through WIRE-019) cover the primary communication paths. However, several internal composition relationships lack explicit WIRE requirements:

**Missing WIRE requirements:**

| Module | Missing Wire | Severity |
|---|---|---|
| `integrator/report.py` (REQ-016) | No WIRE specifying who calls `generate_integration_report()` | LOW |
| `quality_gate/report.py` (REQ-031) | No WIRE specifying who calls `generate_quality_gate_report()` | LOW |
| `quality_gate/scan_aggregator.py` (REQ-030) | No WIRE connecting ScanAggregator to QualityGateEngine | LOW |
| `integrator/traefik_config.py` (REQ-047) | No WIRE connecting TraefikConfigGenerator to ComposeGenerator | MEDIUM |
| `integrator/service_discovery.py` (REQ-049) | No WIRE connecting ServiceDiscovery to DockerOrchestrator or pipeline | LOW |

**Impact**: The missing WIREs are all internal composition within the same package. The callers are implied (QualityGateEngine calls ScanAggregator, ComposeGenerator calls TraefikConfigGenerator, etc.), but explicit WIRE requirements would prevent the classic "built but never wired" pattern.

**Recommendation**: Add WIRE-020 through WIRE-024 for these 5 internal compositions.

### 4.2 SVC tables cover all inter-module API calls

**PASS**

The PRD defines 19 SVC entries (SVC-001 through SVC-019) across 4 milestones:

- M2: SVC-001..003 (contract compliance + fix loop)
- M4: SVC-004..007 (adversarial + quality gate internal)
- M5: SVC-008..014 (pipeline phases)
- M6: SVC-015..019 (Docker orchestration)

Each SVC entry specifies: client method, transport mechanism (HTTP/MCP/subprocess), request DTO with field types, response DTO with field types. The `{ field: type }` notation is consistent throughout.

### 4.3 No orphan modules

**PASS** (with caveats from 4.1)

Every module in the project structure is either:
- Imported by at least one other module (via WIRE requirements)
- A test file (consumed by pytest)
- A fixture file (consumed by tests)
- An `__init__.py` (module marker)

The 5 modules without explicit WIRE requirements (report.py x2, scan_aggregator.py, traefik_config.py, service_discovery.py) are all consumed by their parent modules — just not formally specified.

---

## 5. Quality Gate Architecture

### 5.1 Layer 1 -> Layer 2 -> Layer 3 -> Layer 4 sequential gating is clear

**PASS**

REQ-021 (PRD line 283) explicitly states: "running layers sequentially with gating logic (L1 must pass for L2, L2 for L3, L3 for L4)."

The promotion logic is fully specified:
- L1 FAIL -> exclude service from L2+ (REQ-021)
- L2 FAIL with blocking violations -> enter fix loop (REQ-021)
- L3 FAIL with severity >= blocking_severity -> enter fix loop (REQ-021)
- L4 -> always advisory (REQ-029)

### 5.2 Each layer has a pass/fail threshold specified

**PASS**

| Layer | Pass Threshold | Source |
|---|---|---|
| L1 | success=True AND test_passed/test_total >= 0.9 AND convergence_ratio >= 0.9 | REQ-022 (PRD line 285) |
| L2 | contract_tests_passed == contract_tests_total (PASSED), > 70% (PARTIAL) | REQ-023 (PRD line 287) |
| L3 | No violations with severity >= config.blocking_severity | REQ-027 (PRD line 295) |
| L4 | Always PASSED (advisory) | REQ-029 (PRD line 299) |

### 5.3 All scan codes are assigned to the correct layer

**PASS**

| Layer | Scan Codes | Scanner | REQ |
|---|---|---|---|
| L1 | None (pass-through) | Layer1Scanner | REQ-022 |
| L2 | SCHEMA-001..003, PACT-001..002 | SchemathesisRunner + PactManager | REQ-012, REQ-013 |
| L3 | SEC-001..006, CORS-001..003, LOG-001/004/005, TRACE-001, SEC-SECRET-001..012, DOCKER-001..008, HEALTH-001 | SecurityScanner + ObservabilityChecker + DockerSecurityScanner | REQ-024..026 |
| L4 | ADV-001..006 | AdversarialScanner | REQ-028 |

### 5.4 Fix loop mechanism is specified

**PASS**

The fix loop is fully specified across multiple requirements:
1. Quality Gate detects violations (REQ-021, QualityGateEngine)
2. Pipeline triggers fix pass (REQ-039, quality_failed transition)
3. Fix loop feeds violations to Builders (REQ-038, run_fix_pass -> ContractFixLoop)
4. ContractFixLoop writes FIX_INSTRUCTIONS.md and runs agent-team subprocess (REQ-015)
5. Pipeline re-runs Quality Gate (REQ-039, fix_done -> quality_gate transition)
6. Loop repeats up to max_fix_retries (default 3, QualityGateConfig in REQ-005)

---

## 6. State Machine

### 6.1 All states from the architecture plan are represented

**PASS**

Architecture plan section 5.1 (Plan lines 934-948) defines 11 states. PRD REQ-008 (line 153) defines the identical 11 states:

1. init, 2. architect_running, 3. architect_review, 4. contracts_registering, 5. builders_running, 6. builders_complete, 7. integrating, 8. quality_gate, 9. fix_pass, 10. complete, 11. failed

### 6.2 All transitions are specified with guard conditions

**PASS**

Architecture plan section 5.2 (Plan lines 950-967) defines 13 transitions. PRD REQ-008 (line 153) references "13 transition dicts with triggers, sources, destinations, guard conditions, and callbacks as specified in the architecture plan."

The 13 transitions are:
1. start_architect (init -> architect_running)
2. architect_done (architect_running -> architect_review)
3. approve_architecture (architect_review -> contracts_registering)
4. reject_architecture (architect_review -> architect_running)
5. contracts_ready (contracts_registering -> builders_running)
6. builders_done (builders_running -> builders_complete)
7. start_integration (builders_complete -> integrating)
8. integration_done (integrating -> quality_gate)
9. quality_passed (quality_gate -> complete)
10. quality_failed (quality_gate -> fix_pass)
11. fix_done (fix_pass -> quality_gate)
12. fail (* -> failed)
13. retry_quality (failed -> quality_gate)

Each has guard conditions specified in the architecture plan section 5.3 (Plan lines 968-1009).

### 6.3 Error states and recovery paths are clear

**PASS**

- **Error state**: `failed` (terminal, with `ignore_invalid_triggers=True`)
- **Recovery path 1**: `retry_quality` trigger from `failed` to `quality_gate` (manual retry)
- **Recovery path 2**: `resume` command re-enters at saved state (REQ-044)
- **Emergency save**: GracefulShutdown._emergency_save() saves PipelineState on SIGINT/SIGTERM (REQ-010)
- **Architect retry**: reject_architecture -> architect_running loop with retries_remaining guard (REQ-008)

### 6.4 State persistence format is specified

**PASS**

- Format: JSON (PipelineState serialized via asdict + atomic_write_json)
- Location: `.super-orchestrator/PIPELINE_STATE.json` (REQ-003 constants, PRD line 143)
- Crash safety: atomic write (.tmp + rename) per TECH-004 (PRD line 166)
- Schema version: `schema_version = 1` field in PipelineState (REQ-006, PRD line 149)
- All fields fully specified in REQ-006 with types and defaults

---

## 7. Missing Features Check

### 7.1 Cost tracking per phase

**PASS**

- PipelineCostTracker with PhaseCost dataclass (REQ-007, PRD line 151)
- Sub-phase cost tracking via `sub_phases: dict[str, float]`
- Per-phase cost in display (REQ-045, print_phase_table)
- Phase costs saved to PipelineState.phase_costs (REQ-006)

### 7.2 Budget enforcement

**PASS**

- budget_limit field on SuperOrchestratorConfig (REQ-005)
- budget_limit field on PipelineState (REQ-006)
- check_budget() method on PipelineCostTracker (REQ-007)
- BudgetExceededError exception (REQ-009)
- TECH-022: budget checking after every phase (PRD line 372)
- TEST-059: budget exceeded test case (PRD line 505)

### 7.3 Pause/resume/retry

**PASS**

- State persistence on every phase transition: TECH-021 (PRD line 371)
- Resume command: REQ-044 (PRD line 426)
- RESUME_TRIGGERS map: REQ-008 (PRD line 153)
- Resume test cases: TEST-022 with 4 interrupt scenarios (PRD line 528)
- Interrupted flag: `interrupted: bool` and `interrupt_reason: str` in PipelineState (REQ-006)

### 7.4 Graceful shutdown (signal handling)

**PASS**

- GracefulShutdown class: REQ-010 (PRD line 157)
- SIGINT + SIGTERM handlers: REQ-010
- Windows compatibility: TECH-006 with try/except fallback (PRD line 168)
- Emergency state save: REQ-010 (_emergency_save)
- Pipeline checks should_stop before each phase: WIRE-015 (PRD line 380)
- Test case: TEST-058 simulates SIGINT during execute_pipeline (PRD line 503)

### 7.5 Progress reporting

**PASS**

- 7 Rich display functions: REQ-045 (PRD line 428)
- Progress bar specification: TECH-029 (PRD line 447)
- Rich markup mode: TECH-024 (PRD line 442)
- Terminal UI design in architecture plan section 9.3 (Plan lines 1540-1564)

---

## 8. Summary

### Scorecard

| Checklist Item | Verdict | Notes |
|---|---|---|
| **Completeness vs Vision** | | |
| Every Build 3 vision feature covered | PASS | All 7 milestones mapped |
| Architecture plan classes represented | PASS | All classes have REQ-xxx |
| No architectural components missing | PASS | All modules accounted for |
| All scan codes included | PASS | 40 codes (exceeds vision's 30) |
| **Milestone Dependencies** | | |
| Dependency chain correct | PASS | Valid DAG |
| No circular dependencies | PASS | Strict topological order |
| Milestones self-contained | PASS | Clear boundaries |
| **Integration with Build 1 + Build 2** | | |
| Build 1 integration points covered | PARTIAL PASS | 3 of 7 Codebase Intelligence tools missing from SVC tables |
| Build 2 integration points covered | PASS | Minor gap on hooks config |
| Failure modes specified | PASS | INT-001..006 comprehensive |
| Data flow clear | PASS | SVC tables specify DTOs |
| **Wiring Completeness** | | |
| All modules have WIRE-xxx | PARTIAL PASS | 5 internal compositions missing WIRE |
| SVC tables cover API calls | PASS | 19 SVC entries |
| No orphan modules | PASS | All consumed |
| **Quality Gate Architecture** | | |
| Sequential gating clear | PASS | L1->L2->L3->L4 |
| Pass/fail thresholds specified | PASS | Per-layer thresholds |
| Scan codes assigned correctly | PASS | Layer-to-code mapping complete |
| Fix loop mechanism specified | PASS | Full loop documented |
| **State Machine** | | |
| All states represented | PASS | 11/11 |
| All transitions specified | PASS | 13/13 with guards |
| Error states and recovery | PASS | failed + retry + resume |
| State persistence format | PASS | JSON + atomic write |
| **Missing Features** | | |
| Cost tracking per phase | PASS | PipelineCostTracker |
| Budget enforcement | PASS | check_budget + BudgetExceededError |
| Pause/resume/retry | PASS | PipelineState + RESUME_TRIGGERS |
| Graceful shutdown | PASS | GracefulShutdown + signal handlers |
| Progress reporting | PASS | Rich display functions |

### Totals

- **PASS**: 23
- **PARTIAL PASS**: 2
- **FAIL**: 0

---

## 9. Architecture Gaps (Ranked by Severity)

### Gap 1: Missing SVC entries for Codebase Intelligence tools (MEDIUM)

**Location**: M4 SVC table (PRD lines 320-331)

**Problem**: The architecture plan section 8.1 lists 7 Codebase Intelligence MCP tools consumed by Build 3. The PRD's SVC tables only cover 3:
- SVC-004: get_service_interface (covered)
- SVC-005: find_dependencies (covered)
- SVC-006: check_dead_code (covered)

Missing:
- `find_definition(symbol, language)` -> Used by Quality Gate for symbol tracing
- `find_callers(symbol)` -> Used by Quality Gate for impact analysis
- `search_semantic(query)` -> Used by adversarial review for discovery queries
- `register_artifact(file_path, service_name)` -> Build 2 responsibility (acceptable omission)

**Impact**: The adversarial scanner (REQ-028) can still function with SVC-004/005/006, but its detection capabilities for ADV-001 (dead events), ADV-002 (dead contracts), and ADV-004 (naming inconsistency) would be enhanced by the additional tools.

**Recommendation**: Add SVC-020 through SVC-022 to M4's SVC table for find_definition, find_callers, and search_semantic.

### Gap 2: Missing WIRE requirements for internal compositions (MEDIUM)

**Location**: Various milestones

**Problem**: 5 internal module compositions lack explicit WIRE requirements:
1. `TraefikConfigGenerator` -> `ComposeGenerator` (REQ-047 creates it, no WIRE connects to REQ-046)
2. `ScanAggregator` -> `QualityGateEngine` (REQ-030 creates it, no WIRE connects to REQ-021)
3. `integrator/report.py` -> pipeline.py (REQ-016 creates it, no WIRE specifies caller)
4. `quality_gate/report.py` -> pipeline.py (REQ-031 creates it, no WIRE specifies caller)
5. `service_discovery.py` -> DockerOrchestrator (REQ-049 creates it, no WIRE connects)

**Impact**: LOW-MEDIUM. These are internal compositions that would likely be wired correctly, but explicit WIRE requirements prevent the "built but never called" pattern that the agent-team's XREF scan is designed to catch.

**Recommendation**: Add WIRE-020 through WIRE-024:
- WIRE-020: ComposeGenerator must use TraefikConfigGenerator.generate_labels() when generating service entries
- WIRE-021: QualityGateEngine must use ScanAggregator.aggregate() to produce the final QualityGateReport
- WIRE-022: run_integration_phase() in pipeline.py must call generate_integration_report() after collecting results
- WIRE-023: run_quality_gate() in pipeline.py must call generate_quality_gate_report() after gate completes
- WIRE-024: DockerOrchestrator must use ServiceDiscovery for health checking and port mapping

### Gap 3: Hooks configuration missing from generate_builder_config (LOW)

**Location**: REQ-035 (PRD line 357)

**Problem**: The architecture plan section 11.2 (Plan line 1635) mentions `generate_hooks_config()` from Build 2 being used to configure quality gate hooks for each Builder. REQ-035's generate_builder_config() does not include hooks configuration in the generated config dict.

**Impact**: LOW. Builders launched by Build 3 will still run their full pipeline (milestones, E2E tests, scans). Hooks are a Build 2 enhancement for Agent Teams mode only, and Build 3 launches Builders in CLI mode (subprocess).

**Recommendation**: Add a comment in REQ-035 noting that hooks are an Agent Teams concern configured by Build 2's CLIBackend/AgentTeamsBackend, not by the Build 3 config generator.

### Gap 4: Architecture plan vs PRD milestone numbering mismatch (INFO)

**Location**: Architecture plan section 10.2 vs PRD milestone headers

**Problem**: The architecture plan numbers milestones differently from the PRD:
- Plan M2 = "Super Orchestrator Core" -> PRD M5
- Plan M3 = "Quality Gate Engine" -> PRD M4
- Plan M4 = "Integration Layer" -> Maps to PRD M2+M3
- Plan M5 = "CLI + Docker Orchestration" -> PRD M6
- Plan M6 = "Integrator Tests" -> No separate PRD milestone (distributed)
- Plan M7 = "E2E Verification" -> PRD M7

**Impact**: INFO only. The content is correct; only the numbering differs. The PRD's ordering (contract compliance and cross-service tests before quality gate) is actually more logical for the dependency graph.

**Recommendation**: No action needed. The PRD's milestone ordering is superior.

---

## 10. Missing Requirements That Need to Be Added

### Priority 1 (Should Add)

1. **SVC-020**: `AdversarialScanner.check_naming_consistency()` -> MCP stdio Codebase Intelligence -> find_definition `{ symbol: string, language: string }` -> `{ file: string, line: number, column: number, kind: string }`

2. **SVC-021**: `AdversarialScanner.detect_dead_events()` -> MCP stdio Codebase Intelligence -> find_callers `{ symbol: string }` -> `list[{ file: string, line: number, context: string }]`

3. **SVC-022**: `AdversarialScanner` (general) -> MCP stdio Codebase Intelligence -> search_semantic `{ query: string }` -> `list[{ file: string, chunk: string, score: number }]`

4. **WIRE-020**: ComposeGenerator must call TraefikConfigGenerator.generate_labels() for each service entry in the generated docker-compose.yml

5. **WIRE-021**: QualityGateEngine.run_all_layers() must call ScanAggregator.aggregate() to produce the final QualityGateReport

### Priority 2 (Nice to Have)

6. **WIRE-022**: run_integration_phase() must call generate_integration_report() and write INTEGRATION_REPORT.md to the .super-orchestrator/ directory

7. **WIRE-023**: run_quality_gate() must call generate_quality_gate_report() and write QUALITY_GATE_REPORT.md to the .super-orchestrator/ directory

8. **WIRE-024**: DockerOrchestrator.wait_for_healthy() should delegate to ServiceDiscovery.wait_all_healthy() or ServiceDiscovery should be composed into DockerOrchestrator

---

## 11. Verdict

The Build 3 PRD is **architecturally sound** and ready for implementation. The 2 PARTIAL PASS items are low-to-medium severity gaps that would benefit from additional SVC and WIRE requirements but do not block implementation. The state machine, quality gate architecture, milestone dependencies, and integration points are all correctly specified with no structural defects.

**Confidence level**: HIGH. The PRD comprehensively translates the architecture plan into implementable requirements with strong data type specifications, clear boundaries, and testable acceptance criteria.
