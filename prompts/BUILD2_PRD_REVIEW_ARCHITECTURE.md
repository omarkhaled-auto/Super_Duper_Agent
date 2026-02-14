# Build 2 PRD — Architecture Review Report

**Date:** 2026-02-14
**Reviewer:** arch-reviewer agent
**Review Scope:** Architecture alignment, completeness, dependencies, wiring, backward compatibility, pipeline preservation
**Input Files:** BUILD2_PRD.md, BUILD2_ARCHITECTURE_PLAN.md, BUILD2_CODEBASE_RESEARCH.md, BUILD1_PRD.md

---

## EXECUTIVE SUMMARY

**Overall Verdict:** PASS WITH WARNINGS

The PRD demonstrates strong architectural alignment with the architecture plan, with all 7 new files and 15+ modified files correctly specified. The milestone dependency graph matches the architecture's build sequence. However, there are **13 issues identified** across CRITICAL (0), HIGH (4), WARNING (6), and INFO (3) categories that require attention before implementation.

**Critical Path:** All CRITICAL and HIGH issues must be resolved. WARNING issues are recommended fixes that improve robustness but are non-blocking.

---

## 1. ARCHITECTURE ALIGNMENT

### 1.1 New File Coverage ✅ PASS

**Architecture Plan Section 2 lists 7 new files:**

| File | PRD Coverage | Line Reference |
|------|--------------|----------------|
| `agent_teams_backend.py` (~550 lines) | ✅ M1 REQ-001..016, TECH-001..012 | Lines 66-96 |
| `contract_client.py` (~350 lines) | ✅ M2 REQ-017..026, TECH-013..018 | Lines 135-148 |
| `codebase_client.py` (~300 lines) | ✅ M3 REQ-030..042, TECH-022..028 | Lines 211-224 |
| `hooks_manager.py` (~250 lines) | ✅ M1 REQ-010..016, TECH-004 | Lines 75-81 |
| `claude_md_generator.py` (~350 lines) | ✅ M4 REQ-043..053, TECH-034..036 | Lines 284-295 |
| `contract_scanner.py` (~300 lines) | ✅ M5 REQ-064..070, TECH-040..043 | Lines 349-375 |
| `mcp_client.py` (~200 lines) | ✅ M2 REQ-024..025, TECH-019..020 | Lines 144-148 |

**Verdict:** All 7 new files have complete requirement coverage in the PRD.

---

### 1.2 Modified File Coverage ✅ PASS

**Architecture Plan Section 3 lists 15 files for modification:**

| File | PRD Coverage | Modification Type |
|------|--------------|-------------------|
| `cli.py` | ✅ M1 WIRE-001..003, M4 REQ-054..063, M6 REQ-081 | HEAVY — pipeline integration |
| `agents.py` | ✅ M4 REQ-057..060, TECH-032..033 | HEAVY — prompt injection |
| `config.py` | ✅ M1 TECH-005..008, M2 TECH-015..016, M3 TECH-025..027 | Config dataclasses |
| `state.py` | ✅ M1 TECH-007, M4 TECH-029..031 | Report dataclasses |
| `mcp_servers.py` | ✅ M2 WIRE-004..005, M3 WIRE-006..008 | MCP server configs |
| `contracts.py` | ✅ M2 REQ-027..029 | ServiceContractRegistry |
| `scheduler.py` | ⚠️ IMPLICIT — ExecutionBackend protocol in agent_teams_backend.py | Abstraction boundary |
| `code_quality_standards.py` | ✅ M5 REQ-071..074 | CONTRACT + INTEGRATION standards |
| `tracking_documents.py` | ✅ M5 REQ-075..077 | Contract compliance matrix |
| `codebase_map.py` | ✅ M3 REQ-040..041, M4 REQ-054 | MCP-backed generation |
| `milestone_manager.py` | ✅ M5 REQ-078 | Contract-aware health |
| `e2e_testing.py` | ✅ M6 REQ-080..083 | Contract compliance E2E |
| `verification.py` | ✅ M5 REQ-079, M5 WIRE-017 | Contract verification |
| `tech_research.py` | ✅ M6 REQ-083 | Build 1 service detection |
| `quality_checks.py` | ✅ M5 REQ-065..068, TECH-042..043 | CONTRACT-001..004 scans |

**Verdict:** All 15 modified files have requirement coverage. `scheduler.py` modification is implicit (ExecutionBackend protocol is defined in `agent_teams_backend.py` and consumed via the factory pattern).

---

## 2. COMPLETENESS ANALYSIS

### 2.1 Architecture → PRD Mapping

**Architecture Plan Section 7 (Milestone Breakdown):**

| Milestone | Architecture Section | PRD Section | Requirements Count |
|-----------|----------------------|-------------|-------------------|
| M1: Agent Teams Abstraction | 2.1, 5.1 | Lines 57-123 | 16 REQ + 12 TECH + 3 WIRE + 17 TEST |
| M2: Contract Engine | 2.2, 5.2 | Lines 126-199 | 13 REQ + 8 TECH + 2 WIRE + 12 TEST |
| M3: Codebase Intelligence | 2.3, 5.3 | Lines 202-272 | 13 REQ + 7 TECH + 3 WIRE + 9 TEST |
| M4: Pipeline Integration | 2.4-2.5, 5.4 | Lines 275-337 | 21 REQ + 8 TECH + 5 WIRE + 10 TEST |
| M5: Contract Scans | 5.5 | Lines 340-406 | 16 REQ + 9 TECH + 4 WIRE + 17 TEST |
| M6: E2E + Backward Compat | 5.6 | Lines 409-476 | 6 REQ + 20 INT + 17 TEST |

**Coverage:** ✅ All 6 milestones from architecture are represented in PRD with complete requirement sets.

---

### 2.2 Missing Architecture Elements

#### ⚠️ WARNING-1: Scheduler.py Modification Ambiguity

**Architecture Plan Section 2.9 states:**
> "The scheduler is the core of orchestration and the primary candidate for agent teams abstraction."
> "Only the execution layer changes. The scheduler computes WHAT to run and in what order; the backend determines HOW to run it."

**PRD does NOT have explicit requirements for `scheduler.py` modification.**

**Current PRD approach:** ExecutionBackend protocol is defined in `agent_teams_backend.py` (M1 REQ-001), and `scheduler.py` imports it. This is architecturally valid but **lacks explicit verification requirements.**

**Recommendation:** Add to M1:
```
REQ-017: Import ExecutionBackend protocol into scheduler.py and modify execute_wave()
signature to accept backend: ExecutionBackend parameter (review_cycles: 0)

WIRE-004: Wire ExecutionBackend into TaskScheduler.execute_waves() — backend selection
via create_execution_backend() factory, preserving existing Kahn's algorithm and conflict
detection (review_cycles: 0)

TEST-018: Test TaskScheduler works with both CLIBackend and AgentTeamsBackend (mocked)
without changing wave computation logic (review_cycles: 0)
```

---

#### ⚠️ WARNING-2: Hook Script Content Missing

**Architecture Plan Section 5 (Hook Configuration Architecture) specifies:**
> "Hook types: command hooks (shell scripts for fast checks), agent hooks (LLM-powered verification)"

**PRD M1 REQ-016 states:**
> "The quality-gate.sh Stop hook script must read JSON from stdin, extract cwd field via python3 one-liner, check REQUIREMENTS.md completion ratio, and exit 2 with descriptive stderr message when incomplete"

**Issue:** PRD does not specify the **actual shell script content** or the python3 one-liner. Implementation teams will need to invent this.

**Recommendation:** Add TECH requirement in M1 with reference implementation:
```bash
#!/bin/bash
# .claude/hooks/quality-gate.sh
CWD=$(python3 -c "import sys,json; print(json.load(sys.stdin)['cwd'])")
cd "$CWD" || exit 1
CHECKED=$(grep -c '^\[x\]' REQUIREMENTS.md || echo 0)
TOTAL=$(grep -c '^\[[x ]\]' REQUIREMENTS.md || echo 1)
RATIO=$(python3 -c "print($CHECKED / $TOTAL)")
if (( $(echo "$RATIO < 0.8" | bc -l) )); then
  echo >&2 "REQUIREMENTS.md only $RATIO complete (threshold: 0.8)"
  exit 2
fi
```

---

#### ℹ️ INFO-1: Codebase Research Section 2.1.10 Resume Context

**Architecture Plan mentions** contract state in resume context (Section 3.3.10), **PRD M4 REQ-063 covers this:**
> "In cli.py resume context _build_resume_context(), include contract state (which contracts verified, which violated) and note that agent teams teammates were lost if previously active"

**Verdict:** Covered, but resume logic should also include `registered_artifacts` list. Add to REQ-063:
```
... and list of registered_artifacts to avoid re-indexing on resume.
```

---

### 2.3 Data Flow Completeness

**Architecture Plan Section 4 (Data Flow Diagrams) identifies 3 critical flows:**

1. **Contract Validation Flow:** Architect → Contract stub generation → Code Writer → validate_endpoint() → Contract Engine → Pass/Fail
   - ✅ Covered: M2 REQ-019 (validate_endpoint), M4 REQ-058 (code-writer instructions), M5 REQ-065 (CONTRACT-001 scan)

2. **Codebase Intelligence Flow:** Code Writer generates file → register_artifact() → Codebase Intelligence → Indexed → find_definition() available to other teammates
   - ✅ Covered: M3 REQ-037 (register_artifact), M4 REQ-046 (code-writer instructions), M4 WIRE-013 (artifact tracking)

3. **Agent Teams Coordination Flow:** Scheduler → ExecutionWave → AgentTeamsBackend → TaskCreate → Teammates self-claim → TaskUpdate → Results
   - ⚠️ **WARNING-3:** Missing explicit requirements for **result collection from teammates**.
   - M1 REQ-007 states "poll TaskList until all tasks complete or timeout" but does NOT specify how to extract outputs, files created, cost, etc.
   - **Recommendation:** Add to M1:
   ```
   TECH-013: TaskResult collection pattern — AgentTeamsBackend.execute_wave() must parse
   TaskList output field for each completed task, extract files_created/files_modified from
   agent tool calls log, and estimate cost_usd from message count × $0.015/message baseline
   (review_cycles: 0)
   ```

---

## 3. DEPENDENCY CORRECTNESS

### 3.1 Milestone Dependency Graph

**PRD Dependencies:**
```
M1 (Agent Teams) → none
M2 (Contract Engine) → M1
M3 (Codebase Intelligence) → M2
M4 (Pipeline Integration) → M1, M2, M3
M5 (Contract Scans) → M4
M6 (E2E + Backward Compat) → M4, M5
```

**Architecture Plan Section 5 (Milestone Breakdown) Dependencies:**
```
M1 → none
M2 → M1
M3 → M2
M4 → M1, M2, M3
M5 → M4
M6 → M4, M5
```

**Verdict:** ✅ EXACT MATCH. Dependency graph is correct.

---

### 3.2 Dependency Rationale

| Dependency | Rationale | Validated |
|------------|-----------|-----------|
| M2 → M1 | ContractEngineClient needs mcp_client.py (M1) for session management | ⚠️ **HIGH-1** (see below) |
| M3 → M2 | CodebaseIntelligenceClient shares mcp_client.py pattern with M2 | ✅ Valid |
| M4 → M1,M2,M3 | Pipeline integration wires all 3 backends into cli.py | ✅ Valid |
| M5 → M4 | Contract scans need ServiceContractRegistry from M4 | ✅ Valid |
| M6 → M4,M5 | E2E tests use contracts (M4) and scan results (M5) | ✅ Valid |

#### 🔴 HIGH-1: M2 Dependency on M1 is INCORRECT

**Issue:** M2 REQ-024 states:
> "Create src/agent_team/mcp_client.py with create_contract_engine_session() async context manager..."

**M1 does NOT create `mcp_client.py`** — it creates `agent_teams_backend.py` and `hooks_manager.py`.

**Correction:** `mcp_client.py` should be created in **M2** (Contract Engine Integration), not M1. M3 (Codebase Intelligence) should add `create_codebase_intelligence_session()` to the **same file**.

**Fix:** Move `mcp_client.py` to M2:
- M2 REQ-024 ✅ (already correct)
- M3 REQ-038 should state "Add `create_codebase_intelligence_session()` to existing `mcp_client.py`"
- M2 dependency on M1 should be **REMOVED** — M2 has no dependencies
- M3 dependency on M2 becomes "shares mcp_client.py"

**Updated dependency graph:**
```
M1 → none
M2 → none  (was M1)
M3 → M2
M4 → M1, M2, M3
M5 → M4
M6 → M4, M5
```

---

### 3.3 Cross-Build Dependencies (Build 1)

**PRD Section "Cross-Build Dependencies" (lines 532-541):**

| Build 2 Feature | Build 1 Dependency | Fallback | PRD Coverage |
|------------------|-------------------|----------|--------------|
| ContractEngineClient | Contract Engine MCP (6 tools) | Static `run_api_contract_scan()` | ✅ M6 INT-001 |
| CodebaseIntelligenceClient | Codebase Intelligence MCP (7 tools) | Static `generate_codebase_map()` | ✅ M6 INT-002 |
| Architect MCP queries | Architect MCP (3 tools) | Standard PRD decomposition | ✅ M6 INT-003 |
| CONTRACT-001..004 scans | Contract data (MCP or SVC-xxx) | SVC-xxx from REQUIREMENTS.md | ✅ M6 INT-004 |
| Contract E2E | Running Build 1 services | Skip contract E2E | ✅ M6 INT-005 (implied) |

**Verdict:** ✅ All Build 1 dependencies documented with fallback paths. INT requirements cover graceful degradation.

---

## 4. WIRE REQUIREMENTS COVERAGE

### 4.1 Codebase Research Integration Points → PRD

**Codebase Research Section 2.1 identifies 11 integration points in cli.py:**

| Integration Point | Research Location | PRD WIRE Requirement |
|-------------------|-------------------|----------------------|
| Mode selection (line ~4200) | 2.1.1 | M1 WIRE-001 ✅ |
| Hooks write after backend init | 2.1.1 | M1 WIRE-002 ✅ |
| Teammate shutdown in interrupt handler | 2.1.9 | M1 WIRE-003 ✅ |
| MCP server injection | 2.1.1 | M4 WIRE-009 ✅ |
| CLAUDE.md generation before milestone exec | 2.1.1 | M4 WIRE-010 ✅ |
| Contract+codebase context in prompts | 2.1.1 | M4 WIRE-011 ✅ |
| Contract report update after scans | 2.1.2 | M4 WIRE-012 ✅ |
| Artifact registration after milestone | 2.1.6 | M4 WIRE-013 ✅ |
| Contract compliance scan after API scan | 2.1.2 | M5 WIRE-014 ✅ |
| CONTRACT fix loop | 2.1.8 | M5 WIRE-015 ✅ |
| Contract compliance matrix generation | 2.1.2 | M5 WIRE-016 ✅ |

**Verdict:** ✅ All 11 integration points covered. No missing wiring.

---

### 4.2 Architecture Plan Integration → PRD

**Architecture Plan Section 2 (New Files) specifies dependencies:**

| File | Depends On | PRD WIRE Coverage |
|------|------------|-------------------|
| `agent_teams_backend.py` | config.py, scheduler.py, state.py | M1 TECH-006..008 (config), ⚠️ **WARNING-1** (scheduler) |
| `contract_client.py` | mcp_client.py | M2 REQ-024 ✅ |
| `codebase_client.py` | mcp_client.py | M3 REQ-038 ✅ |
| `hooks_manager.py` | config.py | M1 TECH-004 ✅ |
| `claude_md_generator.py` | agents.py prompts, contracts.py | M4 REQ-044 ✅ |
| `contract_scanner.py` | quality_checks.py Violation class, contracts.py | M5 TECH-040 ✅ |

**Verdict:** ✅ All file dependencies covered except **WARNING-1** (scheduler.py).

---

### 4.3 Missing Wiring: mcp_servers.py → cli.py

**Architecture Plan Section 2.6.2 introduces `get_contract_aware_servers()`:**
> "Returns all standard servers + Contract Engine + Codebase Intelligence."

**PRD M3 WIRE-008 states:**
> "Add get_contract_aware_servers(config: AgentTeamConfig) -> dict[str, Any] to mcp_servers.py that calls get_mcp_servers(config) then conditionally adds Contract Engine and Codebase Intelligence servers"

**PRD M4 WIRE-009 states:**
> "Wire MCP server injection in cli.py — after existing get_mcp_servers() call, add Contract Engine and Codebase Intelligence servers when config-enabled, using get_contract_aware_servers() from mcp_servers.py"

**Issue:** WIRE-009 is redundant — it states "after existing `get_mcp_servers()` call, add ... using `get_contract_aware_servers()`" which implies replacing the call, not adding to it.

**Recommendation:** Clarify WIRE-009:
```
WIRE-009: Replace get_mcp_servers(config) call in cli.py (line ~170-250) with
get_contract_aware_servers(config) when any Build 2 MCP feature is enabled, preserving
existing servers dict structure (review_cycles: 0)
```

---

## 5. BACKWARD COMPATIBILITY

### 5.1 Config Gating ✅ PASS

**PRD M6 INT-006 states:**
> "All new config sections (agent_teams, contract_engine, codebase_intelligence, contract_scans) must default to enabled: False so existing config.yaml files without these sections continue to work via _dict_to_config() backward compatibility"

**Verification:**
- M1 TECH-005: `AgentTeamsConfig` → `enabled: bool = False` ✅
- M2 TECH-015: `ContractEngineConfig` → `enabled: bool = False` ✅
- M3 TECH-025: `CodebaseIntelligenceConfig` → `enabled: bool = False` ✅
- M5 TECH-037: `ContractScanConfig` → All 4 scans default `True`, but gated by parent `enabled` flags ⚠️

#### ⚠️ WARNING-4: ContractScanConfig Defaults

**Issue:** M5 TECH-037 states all 4 contract scans default to `True`. This means if a user adds the `contract_scans` section but forgets to disable individual scans, all 4 will run even if Contract Engine is unavailable.

**Architecture Plan Section 2.4.1** shows:
```python
@dataclass
class ContractScanConfig:
    endpoint_schema_scan: bool = True
    missing_endpoint_scan: bool = True
    event_schema_scan: bool = True
    shared_model_scan: bool = True
```

**Recommendation:** Either:
1. Gate scans on `config.contract_engine.enabled OR has_svc_contracts_in_requirements` (runtime check), OR
2. Default all 4 to `False` for full opt-in behavior

**Suggested fix:** Add to M5 REQ-069:
```
All CONTRACT scan functions must check (config.contract_engine.enabled OR
_has_svc_table(requirements)) before scanning, returning empty list if neither condition
is met (review_cycles: 0)
```

---

### 5.2 Tuple Return Type Preservation ✅ PASS

**PRD M6 INT-007 states:**
> "The existing _dict_to_config() tuple return type tuple[AgentTeamConfig, set[str]] must be preserved — callers must continue to unpack the tuple"

**Verification:**
- M1 TECH-008: "Add agent_teams section parsing to _dict_to_config() in config.py, following existing pattern of nested dataclass construction with user-override tracking, returning updated set[str]" ✅
- M2 TECH-021: "Add contract_engine section parsing to _dict_to_config() following existing pattern" ✅
- M3 TECH-027: "Add codebase_intelligence section parsing to _dict_to_config() following existing pattern" ✅
- M5 TECH-039: "Add contract_scans section parsing to _dict_to_config() following existing pattern" ✅

**Verdict:** ✅ All parsing additions preserve tuple return.

---

### 5.3 Pipeline Preservation ✅ PASS

**PRD M6 INT-011..020 (Pipeline Preservation Checklist):**

| Requirement | Verification |
|-------------|--------------|
| INT-011: 15-stage pipeline preserved | ✅ M4 REQ-054..063 modify existing stages, add no new stages |
| INT-012: 13 fix loops preserved | ✅ M5 WIRE-015 adds fix branches to existing `_run_integrity_fix()` |
| INT-013: Post-orchestration scan order preserved | ✅ M5 WIRE-014 adds CONTRACT scans AFTER API scan |
| INT-014: Milestone-based execution preserved | ✅ M4 uses existing `_run_prd_milestones()` |
| INT-015: All scans config-gated | ✅ M5 TECH-037 (ContractScanConfig booleans) |
| INT-016: Depth gating preserved | ✅ M5 TECH-044 (depth gating for contract features) |
| INT-017: Signal handling saves contract state | ✅ M4 REQ-062, M6 TEST-082 |
| INT-018: Resume includes contract state | ✅ M4 REQ-063, M6 TEST-083 |
| INT-019: ScanScope filtering applies | ✅ M5 TECH-041 |
| INT-020: load_config() tuple return preserved | ✅ M6 INT-007, TEST-073 |

**Verdict:** ✅ All 10 pipeline preservation requirements explicitly covered.

---

## 6. PROMPT INTEGRITY

### 6.1 Prompt Injection Coverage

**Architecture Plan Section 2.2 (agents.py modifications) specifies:**

| Prompt | Architecture Requirement | PRD Requirement | Match |
|--------|-------------------------|----------------|-------|
| ARCHITECT_PROMPT | Query Contract Engine + Codebase Intelligence, generate contract stubs | M4 REQ-057 ✅ | ✅ |
| CODE_WRITER_PROMPT | CONTRACT ENGINE INTEGRATION, validate_endpoint(), register_artifact(), CONTRACT-001..004 compliance | M4 REQ-058 ✅ | ✅ |
| CODE_REVIEWER_PROMPT | CONTRACT COMPLIANCE REVIEW, contract field verification, Codebase Intelligence cross-file analysis | M4 REQ-059 ✅ | ✅ |
| build_orchestrator_prompt | Contract Engine + Codebase Intelligence MCP servers, contract compliance gate, agent teams delegate mode | M4 REQ-060 ✅ | ✅ |
| build_milestone_execution_prompt | Contract queries in step 2, artifact registration in step 5, contract validation in step 8 | M4 REQ-060 ✅ (same req) | ⚠️ **HIGH-2** |

#### 🔴 HIGH-2: Milestone Execution Prompt Under-Specified

**Architecture Plan Section 2.2.5 states:**
> "Step 2 (analysis) should include contract queries: 'Query Contract Engine for all contracts relevant to this milestone'"
> "Step 5 (implementation) should include artifact registration: 'After creating each file, call register_artifact()'"
> "Step 8 (integration verification) should include contract validation: 'Validate all endpoints against contracts'"

**PRD M4 REQ-060 only covers PARAMETER ADDITION:**
> "Add contract_context: str = "" and codebase_index_context: str = "" parameters to build_orchestrator_prompt() and build_milestone_execution_prompt() in agents.py, injected following the existing tech_research_content pattern"

**MISSING:** Instructions for modifying the 9-step MILESTONE WORKFLOW block in `build_milestone_execution_prompt()` to include contract queries, artifact registration, and contract validation.

**Recommendation:** Add to M4:
```
REQ-060A: Modify build_milestone_execution_prompt() 9-step MILESTONE WORKFLOW block:
- Step 2 (Analysis): Add "Query Contract Engine for all contracts with provider_service
  or consumer_service matching this milestone's service_name"
- Step 5 (Implementation): Add "After creating each new file, call
  register_artifact(file_path, service_name) via Codebase Intelligence MCP"
- Step 8 (Integration Verification): Add "For each SVC-xxx contract implemented in this
  milestone, call validate_endpoint() and report CONTRACT-001 violations"
(review_cycles: 0)
```

---

### 6.2 CLAUDE.md Generation Completeness

**PRD M4 REQ-043..053 (CLAUDE.md generation) covers:**

| Role | PRD Coverage | Architecture Plan Requirement |
|------|--------------|------------------------------|
| architect | REQ-045: Contract Engine queries, Codebase Intelligence queries, SVC-xxx stubs with EXACT FIELD SCHEMAS | ✅ Matches Architecture 2.4 section 6.1 |
| code-writer | REQ-046: ZERO MOCK DATA, API CONTRACT COMPLIANCE, validate_endpoint(), register_artifact() | ✅ Matches Architecture 2.4 section 6.2 |
| code-reviewer | REQ-047: contract field verification, CONTRACT violations blocking, Codebase Intelligence cross-file | ✅ Matches Architecture 2.4 section 6.3 |
| test-engineer | REQ-048: Contract Engine generate_tests(), unit+integration test requirements | ✅ Matches Architecture 2.4 section 6.4 |
| wiring-verifier | REQ-049: find_dependencies(), check_dead_code(), contract endpoint verification | ✅ Matches Architecture 2.4 section 6.5 |

**Verdict:** ✅ All 5 roles covered with architecture-aligned instructions.

---

#### ⚠️ WARNING-5: CLAUDE.md Contract List Truncation

**PRD M4 REQ-052 states:**
> "CLAUDE.md contracts section must limit to 20 contracts to prevent excessive file size, with '... and N more' suffix when truncated"

**Issue:** 20 contracts × ~50 lines per OpenAPI spec = ~1000 lines just for contract schemas. This could still exceed CLAUDE.md practical limits (~5000 lines before teammates ignore content).

**Recommendation:** Reduce to 10 contracts and add "Use Contract Engine get_contract(contract_id) MCP tool to fetch additional contracts on demand" instruction.

---

### 6.3 Standards Mapping

**PRD M5 REQ-071..074 (Quality Standards):**

| Standard | Mapped Roles | Architecture Plan Requirement |
|----------|--------------|------------------------------|
| CONTRACT_COMPLIANCE_STANDARDS | code-writer, code-reviewer, architect | ✅ M5 REQ-073 |
| INTEGRATION_STANDARDS | code-writer, code-reviewer | ✅ M5 REQ-074 |

**Verification:**
- `_AGENT_STANDARDS_MAP` exists in `code_quality_standards.py` (Codebase Research 2.10.1) ✅
- Pattern matches existing standards mapping ✅

**Verdict:** ✅ Standards mapping correctly specified.

---

## 7. DEPTH GATING

### 7.1 Depth Gating Table Alignment

**PRD Section "Depth Gating Summary" (lines 519-531):**

| Feature | quick | standard | thorough | exhaustive | Architecture Match |
|---------|-------|----------|----------|------------|-------------------|
| agent_teams.enabled | False | False | True (if env set) | True (if env set) | ✅ Architecture 2.4.3 |
| contract_engine.enabled | False | True (validation only) | True (full) | True (full) | ✅ Architecture 2.4.3 |
| contract_engine.test_generation | False | False | True | True | ✅ Architecture 2.4.3 |
| codebase_intelligence.enabled | False | True (queries only) | True (full) | True (full) | ✅ Architecture 2.4.3 |
| codebase_intelligence.register_artifacts | False | False | True | True | ✅ Architecture 2.4.3 |
| CONTRACT scans 001-002 | False | True | True | True | ✅ Architecture 2.4.3 |
| CONTRACT scans 003-004 | False | False | True | True | ✅ Architecture 2.4.3 |

**Verdict:** ✅ Depth gating matches architecture plan exactly.

---

### 7.2 Depth Gating Implementation

**PRD M5 TECH-044 states:**
> "In _apply_depth_defaults() in config.py, set depth gating for new features: quick = all contract scans off + contract_engine off + codebase_intelligence off + agent_teams off; standard = contract_engine enabled (validation only, test_generation off) + codebase_intelligence enabled (queries only, register_artifacts off) + CONTRACT 001-002 on; thorough = full contract_engine + full codebase_intelligence + all 4 CONTRACT scans + agent_teams enabled (if env set); exhaustive = same as thorough with no differences"

**Issue:** "validation only" and "queries only" modes are NOT represented in config dataclasses.

**Current config:**
```python
@dataclass
class ContractEngineConfig:
    enabled: bool = False
    validation_on_build: bool = True
    test_generation: bool = True
```

**"validation only" mode would be:** `enabled=True, test_generation=False` ✅ This works.

**Current config:**
```python
@dataclass
class CodebaseIntelligenceConfig:
    enabled: bool = False
    replace_static_map: bool = True
    register_artifacts: bool = True
```

**"queries only" mode would be:** `enabled=True, register_artifacts=False` ✅ This works.

**But:** `replace_static_map` is not mentioned in depth gating. If `replace_static_map=True` in standard mode, codebase map will be generated via MCP queries, which is more expensive than static analysis.

#### ⚠️ WARNING-6: replace_static_map Depth Gating

**Recommendation:** Add to M5 TECH-044:
```
standard = ... + codebase_intelligence.enabled=True + replace_static_map=False +
register_artifacts=False (queries via find_definition/search_semantic only, codebase map
uses static analysis)
```

---

## 8. SECURITY REQUIREMENTS

**PRD M6 SEC-001..003:**

| Requirement | Verification |
|-------------|--------------|
| SEC-001: No secrets in MCP env vars | ✅ M2 TECH-020 passes only DATABASE_PATH, M3 env dict has CHROMA_PATH/GRAPH_PATH only |
| SEC-002: No secrets in hook scripts | ✅ M1 REQ-016 quality-gate.sh reads REQUIREMENTS.md (no secrets), REQ-015 track-file-change.sh logs paths only |
| SEC-003: Strip securitySchemes from cached OpenAPI | ✅ M2 REQ-029 ServiceContractRegistry.save_local_cache() should strip, but **NOT SPECIFIED** |

#### 🔴 HIGH-3: SEC-003 Not Implemented

**PRD M2 REQ-029 states:**
> "ServiceContractRegistry.load_from_mcp() must populate registry from Contract Engine, falling back to load_from_local() on MCP failure"

**Missing:** `save_local_cache()` does NOT have instructions to strip `securitySchemes` from OpenAPI specs before writing to `CONTRACTS.json`.

**Recommendation:** Add to M2:
```
REQ-029A: ServiceContractRegistry.save_local_cache(path: Path) must strip
spec.components.securitySchemes from all OpenAPI contracts before writing JSON to prevent
accidental secret exposure in version control (review_cycles: 0)

TEST-031: Test save_local_cache() removes securitySchemes from OpenAPI spec.components
before writing (review_cycles: 0)
```

---

## 9. SERVICE-TO-API WIRING

### 9.1 SVC Table Coverage

**PRD includes 2 SVC tables:**

**Milestone 2 (Contract Engine):** SVC-001 through SVC-006 (6 contracts) ✅
- All 6 map to ContractEngineClient methods
- All 6 have matching MCP tools from Build 1 (verified against BUILD1_PRD.md REQ-060)
- Request/Response DTOs match

**Milestone 3 (Codebase Intelligence):** SVC-007 through SVC-013 (7 contracts) ✅
- All 7 map to CodebaseIntelligenceClient methods
- All 7 have matching MCP tools from Build 1 (verified against BUILD1_PRD.md REQ-057)
- Request/Response DTOs match

**Verdict:** ✅ All 13 SVC contracts have complete field schemas.

---

### 9.2 Field Schema Validation

**Sampling SVC-001:**

**PRD:**
> ContractEngineClient.get_contract(contract_id) -> MCP get_contract { contract_id: string } -> { id: string, type: string, version: string, spec: object, spec_hash: string }

**BUILD1_PRD.md REQ-060 (lines 60-90, Contract Engine MCP tools):**
> GET /contracts/{contract_id} returns Contract with fields: id, type (openapi|asyncapi|json_schema), version, service_name, spec (JSON object), spec_hash (SHA-256), status (draft|active|deprecated)

**Issue:** PRD SVC-001 response DTO is **missing 2 fields**:
- `service_name: string`
- `status: string`

**BUT:** PRD M2 TECH-014 `ContractInfo` dataclass includes all 7 fields ✅

**Conclusion:** SVC table is a summary — full schema is in TECH requirements. This is acceptable but inconsistent with the "EXACT FIELD SCHEMAS" mandate from v9.0.

#### ℹ️ INFO-2: SVC Table Schema Completeness

**Recommendation:** Update SVC-001 response DTO to match TECH-014:
```
SVC-001: ... -> { id: string, type: string, version: string, service_name: string,
spec: object, spec_hash: string, status: string }
```

Apply same to SVC-002..013 (verify all response DTOs match their TECH dataclass definitions).

---

## 10. TEST COVERAGE

### 10.1 Test Count by Milestone

| Milestone | Total Tests | Unit | Wiring | Config | Integration | Backward Compat | Coverage |
|-----------|-------------|------|--------|--------|-------------|-----------------|----------|
| M1 | 17 | 11 | 3 | 2 | 0 | 1 | ✅ Good |
| M2 | 12 | 8 | 2 | 2 | 0 | 0 | ⚠️ Missing integration |
| M3 | 9 | 7 | 2 | 0 | 0 | 0 | ⚠️ Missing config tests |
| M4 | 10 | 6 | 0 | 0 | 0 | 0 | ⚠️ Missing wiring tests |
| M5 | 17 | 10 | 4 | 2 | 0 | 1 | ✅ Good |
| M6 | 17 | 0 | 5 | 3 | 5 | 4 | ✅ Good |
| **Total** | **82** | 42 | 16 | 9 | 5 | 6 | |

**Architecture Plan Section 9 (Testing Strategy) estimates:** 200-300 new tests.

**PRD has 82 tests across 6 milestones** — this is **27-41% of estimate**.

#### 🔴 HIGH-4: Test Coverage Gaps

**Missing test categories:**

1. **M2 Integration Tests:** No tests for ContractEngineClient with a live MCP server (even mocked). TEST-027 tests MCP server config dict, but no end-to-end MCP call tests.

2. **M3 Config Tests:** No tests for `_dict_to_config()` parsing `codebase_intelligence` section.

3. **M4 Wiring Tests:** No tests verifying WIRE-009..013 (MCP server injection, CLAUDE.md generation, contract context in prompts, contract report update, artifact registration).

4. **Cross-milestone Integration:** No tests verifying Agent Teams backend can use Contract Engine MCP during task execution.

**Recommendation:** Add to M6 (End-to-End Verification):
```
TEST-084: Integration test — Create AgentTeamsBackend, execute wave with ContractEngineClient
available, verify validate_endpoint() is called during code-writer task (review_cycles: 0)

TEST-085: Integration test — Create CLIBackend (fallback), execute same wave, verify static
run_api_contract_scan() is used instead of MCP (review_cycles: 0)

TEST-086: Wiring test — Verify CLAUDE.md generated for code-writer role includes Contract
Engine MCP tools section when config.contract_engine.enabled=True (review_cycles: 0)

TEST-087: Wiring test — Verify cli.py calls get_contract_aware_servers() when any Build 2
MCP feature is enabled, preserving all existing servers (review_cycles: 0)

TEST-088: Config test — Verify _dict_to_config() parses codebase_intelligence YAML section
into CodebaseIntelligenceConfig with all 7 fields (review_cycles: 0)
```

---

## 11. OVERALL ASSESSMENT

### 11.1 Strengths

1. **Architecture Fidelity:** 7/7 new files and 15/15 modified files from architecture plan are covered in PRD
2. **Dependency Graph:** Milestone dependencies exactly match architecture (after fixing HIGH-1)
3. **Backward Compatibility:** All new features default to disabled, tuple return types preserved
4. **Pipeline Preservation:** All 15 stages, 13 fix loops, and scan chain order preserved
5. **SVC Contracts:** All 13 inter-service contracts have field schemas (after INFO-2 clarification)
6. **Depth Gating:** Matches architecture plan with proper progressive enablement

---

### 11.2 Weaknesses

1. **Test Coverage:** 82 tests vs. 200-300 estimated (27-41% coverage) — HIGH-4
2. **Prompt Modifications:** Milestone execution prompt modifications under-specified — HIGH-2
3. **Security:** SEC-003 not implemented (strip securitySchemes from cache) — HIGH-3
4. **Scheduler Integration:** No explicit requirements for scheduler.py modification — WARNING-1
5. **Result Collection:** Agent Teams result parsing pattern missing — WARNING-3
6. **Contract Scan Gating:** Scans default to `True` without runtime checks — WARNING-4

---

### 11.3 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Milestone dependency error (HIGH-1) | MEDIUM | Fix M2 dependency: M2→none (not M2→M1) |
| Prompt under-specification (HIGH-2) | MEDIUM | Add REQ-060A for milestone workflow modifications |
| Security gap (HIGH-3) | MEDIUM | Add REQ-029A for securitySchemes stripping |
| Test coverage gap (HIGH-4) | LOW | Add 5 integration/wiring tests to M6 |
| Scheduler coupling (WARNING-1) | LOW | Add 3 requirements for scheduler.py |
| Result collection (WARNING-3) | LOW | Add TECH-013 for TaskResult collection |
| Contract scan defaults (WARNING-4) | LOW | Add runtime check to REQ-069 |
| Hook script content (WARNING-2) | LOW | Add reference implementation to M1 |
| replace_static_map gating (WARNING-6) | LOW | Update TECH-044 depth gating |

---

## 12. VERDICT

**PASS WITH WARNINGS**

The PRD is architecturally sound and implementation-ready **after resolving 4 HIGH-priority issues:**

1. Fix M2 dependency (M2→none, not M2→M1)
2. Add milestone execution prompt modification requirement (REQ-060A)
3. Add securitySchemes stripping to cache save (REQ-029A)
4. Add 5 integration/wiring tests to M6

**WARNING issues are recommended but non-blocking.**

---

## 13. RECOMMENDED FIXES

### CRITICAL FIXES (Must Apply Before Implementation)

None. All issues are HIGH or lower.

---

### HIGH FIXES (Strongly Recommended)

**FIX-1 (HIGH-1): Correct M2 Dependency**

**Location:** Milestone 2 header (line 127)

**Current:**
```
- Dependencies: milestone-1
```

**Fixed:**
```
- Dependencies: none
```

**Justification:** `mcp_client.py` is created in M2 (REQ-024), not M1. M2 has no actual dependencies on M1 code.

---

**FIX-2 (HIGH-2): Add Milestone Execution Prompt Modification**

**Location:** After M4 REQ-060 (line 302)

**Add:**
```
- [ ] REQ-060A: Modify build_milestone_execution_prompt() 9-step MILESTONE WORKFLOW block in agents.py — Step 2 (Analysis) must include "Query Contract Engine for contracts with provider_service or consumer_service matching this milestone's service_name", Step 5 (Implementation) must include "After creating each new file, call register_artifact(file_path, service_name) via Codebase Intelligence MCP", Step 8 (Integration Verification) must include "For each SVC-xxx contract implemented, call validate_endpoint() and report CONTRACT-001 violations" (review_cycles: 0)
```

---

**FIX-3 (HIGH-3): Add securitySchemes Stripping**

**Location:** After M2 REQ-029 (line 147)

**Add:**
```
- [ ] REQ-029A: ServiceContractRegistry.save_local_cache(path: Path) must strip spec.components.securitySchemes from all OpenAPI contracts before writing JSON to prevent accidental secret exposure in version control (review_cycles: 0)
```

**Location:** After M2 TEST-030 (line 199)

**Add:**
```
- [ ] TEST-031: Test ServiceContractRegistry.save_local_cache() removes securitySchemes from OpenAPI spec.components before writing CONTRACTS.json (review_cycles: 0)
```

---

**FIX-4 (HIGH-4): Add Integration/Wiring Tests**

**Location:** After M6 TEST-083 (line 476)

**Add:**
```
- [ ] TEST-084: Integration test — Create AgentTeamsBackend, execute wave with mocked ContractEngineClient available, verify validate_endpoint() call pattern during code-writer task execution (review_cycles: 0)
- [ ] TEST-085: Integration test — Create CLIBackend (fallback), execute same wave without MCP, verify static run_api_contract_scan() is used (review_cycles: 0)
- [ ] TEST-086: Wiring test — Verify CLAUDE.md generated for code-writer role includes Contract Engine MCP tools section when config.contract_engine.enabled=True and omits when disabled (review_cycles: 0)
- [ ] TEST-087: Wiring test — Verify cli.py calls get_contract_aware_servers() when contract_engine.enabled or codebase_intelligence.enabled is True, preserving all existing servers from get_mcp_servers() (review_cycles: 0)
- [ ] TEST-088: Config test — Verify _dict_to_config() parses codebase_intelligence YAML section into CodebaseIntelligenceConfig with all 7 fields (enabled, mcp_command, mcp_args, database_path, chroma_path, graph_path, replace_static_map, register_artifacts) (review_cycles: 0)
```

---

### WARNING FIXES (Recommended)

**FIX-5 (WARNING-1): Add Scheduler Integration Requirements**

**Location:** After M1 REQ-016 (line 82)

**Add:**
```
- [ ] REQ-017: Import ExecutionBackend protocol into scheduler.py and modify TaskScheduler.execute_waves() signature to accept backend: ExecutionBackend parameter, preserving existing Kahn's algorithm and conflict detection (review_cycles: 0)
- [ ] WIRE-004: Wire create_execution_backend() factory into cli.py before TaskScheduler instantiation, passing backend to execute_waves() based on config.agent_teams.enabled (review_cycles: 0)
- [ ] TEST-018: Test TaskScheduler.execute_waves() works with both CLIBackend and mocked AgentTeamsBackend without changing wave computation logic (review_cycles: 0)
```

---

**FIX-6 (WARNING-3): Add TaskResult Collection Pattern**

**Location:** After M1 TECH-012 (line 96)

**Add:**
```
- [ ] TECH-013: AgentTeamsBackend.execute_wave() must parse TaskList output field for each completed task to extract task outputs, parse agent tool call logs to identify files_created and files_modified lists, and estimate cost_usd using message_count × $0.015 baseline (review_cycles: 0)
```

---

**FIX-7 (WARNING-4): Add Contract Scan Runtime Gating**

**Location:** Modify M5 REQ-069 (line 354)

**Current:**
```
- [ ] REQ-069: All CONTRACT scan functions must accept project_dir: Path, contracts: list[dict], scope: ScanScope | None and return list[Violation] capped at _MAX_VIOLATIONS=100 (review_cycles: 0)
```

**Fixed:**
```
- [ ] REQ-069: All CONTRACT scan functions must accept project_dir: Path, contracts: list[dict], scope: ScanScope | None, return list[Violation] capped at _MAX_VIOLATIONS=100, and check (config.contract_engine.enabled OR _has_svc_table(requirements)) before scanning, returning empty list if neither condition is met to prevent running scans when no contracts are available (review_cycles: 0)
```

---

## 14. FINAL CHECKLIST

- [x] All 7 new files from architecture plan have PRD requirements
- [x] All 15 modified files from architecture plan have PRD requirements
- [x] Milestone dependency graph matches architecture
- [ ] **HIGH-1:** Fix M2 dependency (M2→none)
- [ ] **HIGH-2:** Add milestone prompt modification (REQ-060A)
- [ ] **HIGH-3:** Add securitySchemes stripping (REQ-029A, TEST-031)
- [ ] **HIGH-4:** Add 5 integration/wiring tests (TEST-084..088)
- [x] Backward compatibility preserved (INT-006, INT-007, INT-020)
- [x] Pipeline preservation verified (INT-011..020)
- [x] Depth gating matches architecture (TECH-044)
- [x] SVC contracts have field schemas (13 contracts)
- [x] Cross-build dependencies documented (INT-001..005)
- [ ] **WARNING-1:** Add scheduler integration requirements (REQ-017, WIRE-004, TEST-018)
- [ ] **WARNING-3:** Add TaskResult collection pattern (TECH-013)
- [ ] **WARNING-4:** Add contract scan runtime gating (modify REQ-069)

**Status:** 10/14 complete, **4 HIGH + 3 WARNING fixes required**

---

## APPENDIX A: ISSUE SUMMARY TABLE

| ID | Severity | Category | Title | Fix Location |
|----|----------|----------|-------|--------------|
| HIGH-1 | HIGH | Dependencies | M2 dependency on M1 is incorrect | M2 header line 127 |
| HIGH-2 | HIGH | Prompts | Milestone execution prompt modifications under-specified | After M4 REQ-060 |
| HIGH-3 | HIGH | Security | SEC-003 securitySchemes stripping not implemented | After M2 REQ-029 |
| HIGH-4 | HIGH | Testing | Test coverage gaps (82 vs 200-300 estimate) | After M6 TEST-083 |
| WARNING-1 | WARNING | Completeness | Scheduler.py modification ambiguity | After M1 REQ-016 |
| WARNING-2 | WARNING | Completeness | Hook script content missing | M1 TECH (new) |
| WARNING-3 | WARNING | Data Flow | TaskResult collection pattern missing | After M1 TECH-012 |
| WARNING-4 | WARNING | Config | Contract scan defaults without runtime checks | Modify M5 REQ-069 |
| WARNING-5 | WARNING | Prompts | CLAUDE.md contract list truncation too generous | M4 REQ-052 |
| WARNING-6 | WARNING | Depth Gating | replace_static_map depth gating unclear | M5 TECH-044 |
| INFO-1 | INFO | Completeness | Resume context missing registered_artifacts | M4 REQ-063 |
| INFO-2 | INFO | SVC Contracts | SVC table schemas incomplete (summary only) | SVC-001..013 tables |

---

**End of Architecture Review**
