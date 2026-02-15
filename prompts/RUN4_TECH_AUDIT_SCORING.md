# Run 4 — Audit Scoring & Gap Analysis Research

## Purpose

This document provides the audit methodology, scoring rubrics, defect categorization, gap analysis frameworks, fix pass convergence metrics, and report generation patterns for Run 4 of the Super Agent Team. Run 4 is a verification + remediation run that wires 3 independently-built systems together and produces a final honest assessment.

---

## 1. Software Audit Methodologies

### 1.1 ISO/IEC 25010 — Software Quality Model (Adapted)

ISO 25010 defines 8 quality characteristics. We adapt 5 that are directly measurable by automated verification:

| Characteristic | Sub-Characteristic | How We Measure | Applies To |
|---|---|---|---|
| **Functional Suitability** | Functional completeness | % of REQ-xxx requirements verified | All builds |
| **Functional Suitability** | Functional correctness | Test pass rate (unit + integration) | All builds |
| **Reliability** | Fault tolerance | Service recovery after crash, health check pass rate | Build 1, Build 3 |
| **Reliability** | Availability | Docker health check uptime during test window | Build 3 |
| **Compatibility** | Interoperability | Contract compliance rate (Schemathesis + Pact) | Cross-build |
| **Maintainability** | Modularity | Dead code ratio, orphan service count (ADV-001..003) | All builds |
| **Security** | Confidentiality | SEC-001..006, SEC-SECRET-001..012 violation count | Build 3 |

**Adaptation rationale:** Performance efficiency and usability are excluded because Run 4 is an infrastructure pipeline, not a user-facing application. Portability is excluded because Docker Compose is the sole deployment target. We keep security because the infrastructure handles secrets and auth tokens.

### 1.2 Coverage-Based Audit

Coverage-based audit answers: "What percentage of the specification has been verified?"

**Three coverage dimensions:**

1. **Requirement Coverage** = (Requirements with at least one passing test) / (Total requirements)
   - Parsed from REQ-xxx checkboxes in each Build PRD
   - A requirement counts as "covered" if its corresponding TEST-xxx passes
   - Target: >= 90% for each build

2. **Interface Coverage** = (MCP tools tested with valid response) / (Total MCP tools defined)
   - Build 1 defines ~12 MCP tools across Architect, Contract Engine, Codebase Intelligence
   - Build 2 adds contract-aware scan MCP calls
   - A tool counts as "covered" if it returns a parseable response (not error) to a valid request
   - Target: 100% for Build 1 MCP tools, >= 90% for Build 2

3. **Integration Coverage** = (Cross-build data flows tested) / (Total cross-build data flows)
   - Architect -> Contract Engine (service map -> contracts)
   - Contract Engine -> Builder Fleet (contracts -> scan directives)
   - Builder Fleet -> Integrator (build results -> Docker compose)
   - All five -> Quality Gate (all artifacts -> 4-layer verification)
   - Target: 100% for primary paths, >= 80% for error/edge paths

### 1.3 Risk-Based Audit (Blast Radius Prioritization)

Not all components carry equal risk. A failure in the Architect's service decomposition propagates to every downstream system. A failure in a display function affects only terminal output.

**Risk tiers:**

| Tier | Components | Blast Radius | Audit Depth |
|---|---|---|---|
| **Tier 1 (Critical Path)** | Architect decomposition, Contract Engine validation, Super Orchestrator pipeline loop | Failure cascades to all downstream systems | Exhaustive: test every code path |
| **Tier 2 (Integration Seams)** | MCP server interfaces, Docker Compose generation, Builder -> Integrator handoff | Failure blocks integration but individual systems survive | Thorough: test happy path + top-3 error paths |
| **Tier 3 (Quality Infrastructure)** | Security scanner, Observability checker, Adversarial scanner | Failure means missed defects but system still runs | Standard: test regex patterns against known samples |
| **Tier 4 (Reporting/Display)** | CLI display, Report generation, Cost tracking | Failure is cosmetic | Spot check: verify output is parseable |

**Audit time allocation:** Tier 1 gets 40% of verification effort, Tier 2 gets 30%, Tier 3 gets 20%, Tier 4 gets 10%.

### 1.4 CMMI-Adapted Maturity Assessment

Instead of CMMI's 5-level organizational maturity, we assess each system's implementation maturity:

| Level | Name | Criteria | Score |
|---|---|---|---|
| **L0** | Non-functional | Service doesn't start, tests don't run, MCP server crashes | 0 |
| **L1** | Initial | Service starts, some tests pass, but core functionality has gaps | 1-3 |
| **L2** | Managed | All core functions work, tests pass at >80%, but integration untested | 4-6 |
| **L3** | Defined | Integration works, contracts verified, but edge cases and error handling incomplete | 7-8 |
| **L4** | Quantitatively Managed | All tests pass, all contracts verified, all scans clean, documented | 9 |
| **L5** | Optimizing | L4 + performance verified, adversarial review clean, no known gaps | 10 |

---

## 2. Scoring Rubrics

### 2.1 Per-System Scoring (Build 1, Build 2, Build 3)

Each system receives a composite score out of 100, computed from weighted sub-scores:

| Category | Weight | Metric | Scoring |
|---|---|---|---|
| **Functional Completeness** | 30% | REQ-xxx pass rate | Linear: 0% = 0, 100% = 30 |
| **Test Health** | 20% | Test pass rate (passed/total) | Linear: 0% = 0, 100% = 20 |
| **Contract Compliance** | 20% | Schemathesis + Pact pass rate | Linear: 0% = 0, 100% = 20 |
| **Code Quality** | 15% | Scan violation density (violations per KLOC) | Inverse: 0 viol/KLOC = 15, >10 viol/KLOC = 0 |
| **Docker Health** | 10% | Health check pass rate across all services | Linear: 0% = 0, 100% = 10 |
| **Documentation** | 5% | Required artifacts present (reports, configs) | Binary per artifact: present = 1, missing = 0 |

**Scoring formula per system:**

```
system_score = (req_pass_rate * 30) + (test_pass_rate * 20) + (contract_pass_rate * 20)
             + (max(0, 15 - violation_density * 1.5)) + (health_check_rate * 10)
             + (artifacts_present / artifacts_required * 5)
```

### 2.2 Integration Scoring

Integration between builds is scored separately because it tests the seams, not the components:

| Category | Weight | Metric | Scoring |
|---|---|---|---|
| **MCP Connectivity** | 25% | MCP tools responding correctly | Binary per tool |
| **Data Flow Integrity** | 25% | End-to-end data flows completing | Pass/fail per flow |
| **Contract Fidelity** | 25% | Cross-build contract violations | Inverse of violation count |
| **Pipeline Completion** | 25% | Super Orchestrator phases completing | % of phases that reach "done" state |

**Integration score formula:**

```
integration_score = (mcp_tools_ok / mcp_tools_total * 25)
                  + (flows_passing / flows_total * 25)
                  + (max(0, 25 - cross_build_violations * 2.5))
                  + (phases_complete / phases_total * 25)
```

### 2.3 Aggregate Score

The aggregate score represents the overall system health:

```
aggregate = (build1_score * 0.30) + (build2_score * 0.25) + (build3_score * 0.25)
          + (integration_score * 0.20)
```

**Rationale for weights:** Build 1 gets 30% because it's the foundation everything depends on. Build 2 and Build 3 get 25% each because they're equally critical but independent. Integration gets 20% because it represents the "glue" quality.

### 2.4 Score Normalization

Different metrics use different scales. We normalize all to 0-100 before applying weights:

| Metric Type | Raw Range | Normalization |
|---|---|---|
| Pass rate (tests, requirements) | 0.0 - 1.0 | Multiply by 100 |
| Violation count | 0 - unbounded | `max(0, 100 - (count * penalty_per_violation))` |
| Binary (present/absent) | 0 or 1 | 0 or 100 |
| Time-based (indexing speed) | 0s - unbounded | `100 if time < threshold else max(0, 100 - (time - threshold) / threshold * 100)` |
| Density (violations/KLOC) | 0.0 - unbounded | `max(0, 100 - density * 10)` |

### 2.5 Traffic Light Classification

| Color | Score Range | Meaning |
|---|---|---|
| **GREEN** | 80-100 | System/integration is production-ready or close |
| **YELLOW** | 50-79 | System works but has significant gaps requiring attention |
| **RED** | 0-49 | System has critical failures blocking integration |

---

## 3. Defect Categorization (P0-P3)

### 3.1 Priority Definitions

| Priority | Name | Definition | SLA | Example |
|---|---|---|---|---|
| **P0** | Blocker | System cannot function. Blocks all downstream work. | Must fix before any other work | MCP server won't start; Docker Compose fails to build; state machine crashes on init; Contract Engine rejects all valid specs |
| **P1** | Critical | Major feature broken. System runs but a primary use case fails. | Must fix in current fix pass | Contract validation returns false positives on >50% of valid specs; Builder can't query Codebase Intelligence; Quality Gate Layer 2 skips contract checks; Integrator generates invalid docker-compose.yml |
| **P2** | Major | Minor feature broken or degraded. System is usable but incomplete. | Fix if time permits in current pass, otherwise document | Dead code detection misses some patterns; Report formatting broken; Cost tracking inaccurate; Adversarial scanner has false positives |
| **P3** | Minor | Nice-to-have. No functionality affected. | Document for future improvement | Performance optimization opportunity; Documentation incomplete; Log messages unclear; CLI help text missing |

### 3.2 Classification Criteria Decision Tree

```
Is the system unable to start or deploy?
  YES -> P0

Does a primary use case fail end-to-end?
  YES -> Is there a workaround?
    NO  -> P0
    YES -> P1

Does a secondary feature fail?
  YES -> Does it affect integration with other builds?
    YES -> P1
    NO  -> P2

Is it cosmetic, performance, or documentation?
  YES -> P3
```

### 3.3 Defect Examples by Build

#### Build 1 (Architect + Contract Engine + Codebase Intelligence)

| Priority | Example Defect | Evidence |
|---|---|---|
| P0 | Architect MCP server crashes on startup with ImportError | `python -m src.architect.mcp_server` exits with code 1 |
| P0 | Contract Engine rejects all OpenAPI 3.1 specs as invalid | `validate_spec` returns `{valid: false}` for known-good specs |
| P1 | Codebase Intelligence indexes but `find_callers()` returns empty for known callers | MCP query returns `[]` when grep confirms 5 call sites exist |
| P1 | Breaking change detection fails to detect field removal | Removing a required field from OpenAPI spec produces no warning |
| P2 | `search_semantic()` returns irrelevant results for specific query types | Query "payment retry logic" returns unrelated code chunks |
| P2 | Dead code detection has false positives on test helper functions | `check_dead_code` reports test fixtures as dead |
| P3 | Indexing takes 90 seconds for 50K LOC (spec says < 60s) | Performance benchmark shows 1.5x slower than target |
| P3 | MCP tool descriptions are missing or unclear | `list_tools` returns tools with empty descriptions |

#### Build 2 (Builder Fleet)

| Priority | Example Defect | Evidence |
|---|---|---|
| P0 | Builder subprocess crashes immediately with config parse error | `python -m agent_team --cwd dir` exits code 1 before any generation |
| P0 | Agent Teams coordination deadlocks: all teammates idle, no tasks claimed | TaskList shows pending tasks but TeammateIdle hook fires continuously |
| P1 | Builder ignores CONTRACT-001 scan directive: generates non-compliant endpoints | Post-build scan shows endpoints missing from contract, no scan violations raised |
| P1 | Builder can't connect to Codebase Intelligence MCP: falls back to no-context generation | MCP connection timeout, builder proceeds without querying index |
| P2 | CONTRACT-004 scan has false positives on optional fields | Scan reports violation for optional fields that are legitimately omitted |
| P2 | Multi-instance coordination fails when >3 builders run simultaneously | Semaphore contention causes 4th builder to hang |
| P3 | Build Report missing cost breakdown per milestone | Report shows total cost but not per-milestone cost |

#### Build 3 (Integrator + Quality Gate + Super Orchestrator)

| Priority | Example Defect | Evidence |
|---|---|---|
| P0 | `super-orchestrator run` crashes: state machine transition error | Execute_pipeline raises MachineError on first transition |
| P0 | Docker Compose generation produces invalid YAML | `docker compose config` fails with syntax error |
| P1 | Quality Gate Layer 2 always returns PASSED regardless of violations | Layer2Scanner.evaluate ignores integration_report violations |
| P1 | Fix pass doesn't feed violations back to correct Builder | Violations from service A sent to service B's fix pass |
| P2 | Traefik routing generates wrong PathPrefix for nested paths | `/api/v1/users` routes to wrong service |
| P2 | Adversarial scanner ADV-001 misses events published via different patterns | Only detects `publish("event")` but misses `eventBus.emit("event")` |
| P3 | CLI `status` command doesn't show elapsed time | Time column in status table shows "N/A" |

#### Cross-Build Integration

| Priority | Example Defect | Evidence |
|---|---|---|
| P0 | Build 1 MCP servers unreachable from Build 2 Builders | MCP stdio connection fails: "command not found" or wrong cwd |
| P0 | Build 2 Builder output format doesn't match Build 3 Integrator's expected input | STATE.json field names changed between Build 2 and Build 3 expectations |
| P1 | Contract Engine returns contracts in format Builder doesn't parse | JSON schema format mismatch between Contract Engine output and Builder input |
| P1 | Codebase Intelligence index doesn't update when Builder registers new code | `register_artifact` MCP call succeeds but `find_definition` can't find registered symbol |
| P2 | Builder queries Codebase Intelligence for wrong service's code | Service boundary not respected in queries |
| P3 | MCP call latency causes Builder timeout on large codebases | Queries taking >5s for 50K+ LOC index |

### 3.4 Defect Density Metrics

| Metric | Formula | Healthy | Concerning | Critical |
|---|---|---|---|---|
| **Defect density** | Total defects / KLOC | < 2.0 | 2.0 - 5.0 | > 5.0 |
| **P0 density** | P0 defects / system count | 0 | 1 per system | > 1 per system |
| **P1 density** | P1 defects / system count | < 2 | 2-5 | > 5 |
| **Scan violation density** | Scan violations / KLOC | < 1.0 | 1.0 - 3.0 | > 3.0 |
| **Contract violation rate** | Contract violations / total endpoints | 0% | 1-10% | > 10% |

---

## 4. Gap Analysis Frameworks

### 4.1 Requirements Traceability Matrix (RTM)

The RTM traces each requirement through four stages:

```
REQ-xxx (Specification) -> SRC (Implementation) -> TEST-xxx (Test) -> VERIFY (Verification)
```

**RTM table format:**

| Req ID | Build | Description | Implementation File(s) | Test ID(s) | Test Status | Verification Status |
|---|---|---|---|---|---|---|
| REQ-001 | B3-M1 | ServiceStatus enum | models.py:L15 | TEST-001a | PASS | Verified |
| REQ-031 | B3-M4 | QualityGateEngine | gate_engine.py:L1 | TEST-019 | FAIL | Gap |
| REQ-046 | B3-M5 | run_architect_phase | pipeline.py:L45 | TEST-030 | PASS | Verified |

**Gap identification rules:**
- **Implementation Gap:** REQ-xxx has no corresponding source file -> RED
- **Test Gap:** REQ-xxx has implementation but no TEST-xxx -> YELLOW
- **Verification Gap:** TEST-xxx exists but never executed in Run 4 -> YELLOW
- **Full Trace:** All four stages populated and passing -> GREEN

**Completeness metric:**
```
RTM_completeness = GREEN_requirements / total_requirements
```

### 4.2 Interface Coverage Matrix

Every MCP tool across all three builds must be tested with at least one valid request and one error request.

| MCP Server | Tool Name | Build | Valid Request Tested | Error Request Tested | Response Parseable | Status |
|---|---|---|---|---|---|---|
| Architect | `decompose` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Architect | `get_service_map` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Contract Engine | `validate_spec` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Contract Engine | `create_contract` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Contract Engine | `generate_tests` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Codebase Intel | `find_definition` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Codebase Intel | `find_callers` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |
| Codebase Intel | `search_semantic` | B1 | YES/NO | YES/NO | YES/NO | GREEN/YELLOW/RED |

**Coverage target:** 100% valid request coverage, >= 80% error request coverage.

### 4.3 Data Flow Path Coverage

Every data flow path through the pipeline must be tested end-to-end:

**Primary paths (must all be GREEN):**

| # | Path | Source | Destination | Data Shape | Verified |
|---|---|---|---|---|---|
| 1 | PRD -> Service Map | User | Architect | Text -> YAML | |
| 2 | Service Map -> Contracts | Architect | Contract Engine | YAML -> OpenAPI/AsyncAPI | |
| 3 | Contracts -> Builder Config | Contract Engine | Builder Fleet | JSON -> config.yaml | |
| 4 | Builder Output -> Build Result | Builder Fleet | Integrator | STATE.json -> BuilderResult | |
| 5 | Build Results -> Docker Compose | Integrator | Docker | BuilderResult -> YAML | |
| 6 | Docker Services -> Health Checks | Docker | Integrator | HTTP -> bool | |
| 7 | Health Services -> Contract Tests | Integrator | Schemathesis/Pact | URL -> violations | |
| 8 | All Results -> Quality Gate | Integrator | Quality Gate | Reports -> QualityGateReport | |
| 9 | Violations -> Fix Pass | Quality Gate | Builder Fleet | violations -> fix prompt | |
| 10 | Fix Results -> Re-verification | Builder Fleet | Quality Gate | BuilderResult -> re-scan | |

**Error paths (should be at least YELLOW):**

| # | Error Scenario | Expected Behavior | Verified |
|---|---|---|---|
| E1 | Architect times out | Retry up to max_retries, then fail with clear error | |
| E2 | Contract validation fails | Log warning, proceed with valid contracts | |
| E3 | Builder crashes mid-generation | Other builders continue, failed builder marked in report | |
| E4 | Docker service fails health check | Service excluded from integration tests, reported | |
| E5 | MCP server unreachable | Fallback to subprocess mode (Build 1 MCP tools) | |
| E6 | Budget exceeded mid-pipeline | Save state, raise BudgetExceededError, enable resume | |
| E7 | SIGINT during pipeline | GracefulShutdown saves state, clean Docker teardown | |

### 4.4 "Dark Corners" Identification

Dark corners are integration points that no test covers. They represent unknown risk.

**Systematic identification method:**

1. **List all cross-build function calls** (functions in Build X that call functions in Build Y)
2. **List all shared data structures** (dataclasses/schemas used by multiple builds)
3. **List all environment-dependent behavior** (Docker networking, file system paths, MCP stdio transport)
4. **For each item, check:** Is there a test that exercises this exact interaction?
5. **Dark corner = no test exists**

**Common dark corners in multi-system pipelines:**

| Dark Corner | Why It's Missed | How to Test |
|---|---|---|
| MCP server startup race condition | Works in isolation, fails when 3 servers start simultaneously | Start all 3 MCP servers, query each within 2 seconds |
| Docker network DNS resolution | Works with `localhost`, fails with service names in Docker network | Query service B from service A using Docker Compose service name |
| File path format across OS | Paths work on Linux build host, fail on Windows CI | Run subset of tests on Windows (or mock `os.sep`) |
| Concurrent Builder file conflicts | Single builder works, two builders writing to shared index conflict | Run 2 builders targeting same Codebase Intelligence index |
| State machine resume after crash | Normal flow tested, resume from mid-state untested | Kill pipeline mid-build, resume, verify correct re-entry |
| Large PRD handling | Small test PRDs work, real 50-page PRD causes context overflow | Feed a real-scale PRD through Architect |

---

## 5. Fix Pass Convergence Metrics

### 5.1 Defect Discovery Rate

Track defects found per fix pass to measure whether we're converging:

| Fix Pass | New P0 | New P1 | New P2 | New P3 | Total New | Cumulative |
|---|---|---|---|---|---|---|
| Initial scan | ? | ? | ? | ? | ? | ? |
| Fix pass 1 | ? | ? | ? | ? | ? | ? |
| Fix pass 2 | ? | ? | ? | ? | ? | ? |
| Fix pass N | ? | ? | ? | ? | ? | ? |

**Convergence signal:** New defect discovery rate should decrease monotonically. If fix pass N finds MORE new defects than fix pass N-1, something is wrong (fixes are introducing regressions or initial scan was incomplete).

**Expected curve:**

```
Defects found
     |
  30 |  *
     |
  20 |     *
     |
  10 |        *
     |           *    *
   0 |________________*___
     1    2    3    4    5   Fix Pass
```

### 5.2 Fix Effectiveness Rate

Not all fixes actually resolve their target defect. Track:

```
fix_effectiveness = fixes_that_resolved_target / total_fixes_attempted
```

| Fix Pass | Fixes Attempted | Fixes Resolved | Fixes Failed | Effectiveness |
|---|---|---|---|---|
| 1 | ? | ? | ? | ?% |
| 2 | ? | ? | ? | ?% |
| N | ? | ? | ? | ?% |

**Healthy range:** >= 80% effectiveness. Below 60% indicates the fix prompts are poorly targeted or the defects are misdiagnosed.

### 5.3 Regression Introduction Rate

Fixes can introduce new defects. Track:

```
regression_rate = new_defects_introduced_by_fixes / total_fixes_applied
```

**Healthy range:** < 10% regression rate. Above 20% means the fix pass is net-negative (creating more problems than it solves).

**Regression detection method:**
1. Before fix pass N, run full scan: record all violations
2. Apply fixes
3. After fix pass N, run full scan: record all violations
4. New violations not in pre-fix set = regressions

### 5.4 Convergence Criteria (When to Stop)

**Hard stop conditions (any one triggers):**
- P0 count reaches 0 AND P1 count reaches 0
- Max fix passes reached (configured, default 5)
- Budget exhausted
- Fix effectiveness drops below 30% for 2 consecutive passes
- Regression rate exceeds 25% for 2 consecutive passes

**Soft convergence (declare "good enough"):**
- P0 count = 0
- P1 count <= 2 (with documented workarounds)
- New defect discovery rate < 3 per pass for 2 consecutive passes
- Aggregate score >= 70

**Formula for convergence score:**

```
convergence = 1.0 - (remaining_p0 * 0.4 + remaining_p1 * 0.3 + remaining_p2 * 0.1) / initial_total_weighted
```

When convergence >= 0.85, declare "converged enough."

### 5.5 The "Last 10%" Problem

In practice, the final defects are the hardest:
- **Cross-build timing issues** that only manifest under load
- **Edge cases in contract validation** that require understanding both producer and consumer
- **State machine transitions** that only fail on specific resume paths

**Mitigation strategies:**
1. **Time-box the last fix pass:** If pass N takes 2x longer than pass N-1, stop and document
2. **Downgrade remaining P1s:** If a P1 has been attempted 3 times, assess whether it's actually a P2 with a workaround
3. **Accept documented gaps:** The audit report should honestly list remaining issues rather than claiming false completion
4. **Separate "works" from "works perfectly":** An 85% score with documented gaps is more valuable than a claimed 100% with hidden issues

---

## 6. Report Generation Patterns

### 6.1 Executive Summary Format (SUPER_TEAM_AUDIT_REPORT.md - Top Section)

```markdown
# Super Agent Team — Audit Report

## Executive Summary

| System | Score | Status | P0 | P1 | P2 | P3 |
|--------|-------|--------|----|----|----|----|
| Build 1: Architect + Contract Engine + Codebase Intelligence | XX/100 | GREEN/YELLOW/RED | 0 | 0 | 2 | 3 |
| Build 2: Builder Fleet | XX/100 | GREEN/YELLOW/RED | 0 | 1 | 3 | 2 |
| Build 3: Integrator + Quality Gate + Super Orchestrator | XX/100 | GREEN/YELLOW/RED | 0 | 0 | 1 | 4 |
| Cross-Build Integration | XX/100 | GREEN/YELLOW/RED | 0 | 0 | 2 | 1 |
| **Aggregate** | **XX/100** | **GREEN/YELLOW/RED** | **0** | **1** | **8** | **10** |

**Verdict:** [ONE SENTENCE: "The Super Agent Team is/is not ready for production use. [reason]."]

**Fix Passes Completed:** N of M max
**Total Defects Found:** X (Y resolved, Z remaining)
**Convergence:** [converged / partially converged / not converged]
```

### 6.2 Detailed Finding Format

Each finding follows a 5-field structure:

```markdown
### FINDING-XXX: [Short Title]

**Priority:** P0/P1/P2/P3
**System:** Build 1 / Build 2 / Build 3 / Integration
**Component:** [Specific module or function]

**Evidence:**
[Exact reproduction steps or test output showing the defect]

**Recommendation:**
[Specific fix action, not vague "improve this"]

**Resolution:** [FIXED in Fix Pass N / OPEN / WONTFIX with justification]
**Fix Verification:** [Test ID that confirms the fix, or "pending"]
```

### 6.3 Fix Pass Trend Tracking

```markdown
## Fix Pass History

### Fix Pass 1 (Date: YYYY-MM-DD, Cost: $X.XX)

| Metric | Value |
|--------|-------|
| Defects targeted | N |
| Defects resolved | N |
| Regressions introduced | N |
| Fix effectiveness | X% |
| Score before | XX/100 |
| Score after | XX/100 |
| Delta | +X |

**Notable fixes:** [List of significant P0/P1 fixes applied]
**Notable regressions:** [List of any regressions introduced, or "None"]

### Fix Pass 2 ...
```

### 6.4 Full Audit Report Structure

```
SUPER_TEAM_AUDIT_REPORT.md
├── Executive Summary (Section 6.1)
├── Methodology
│   ├── Audit approach (coverage + risk-based hybrid)
│   ├── Scoring rubric summary
│   └── Tools used
├── Per-System Assessment
│   ├── Build 1: Architect + Contract Engine + Codebase Intelligence
│   │   ├── Score breakdown (table)
│   │   ├── Success criteria verification (from reference doc)
│   │   ├── Findings (ordered by priority)
│   │   └── MCP tool coverage matrix
│   ├── Build 2: Builder Fleet
│   │   ├── Score breakdown
│   │   ├── Success criteria verification
│   │   ├── Findings
│   │   └── Contract scan coverage
│   └── Build 3: Integrator + Quality Gate + Super Orchestrator
│       ├── Score breakdown
│       ├── Success criteria verification
│       ├── Findings
│       └── Quality Gate layer results
├── Integration Assessment
│   ├── Integration score breakdown
│   ├── Data flow path coverage (Section 4.3)
│   ├── Interface coverage matrix (Section 4.2)
│   ├── Dark corners identified (Section 4.4)
│   └── Integration findings
├── Fix Pass History (Section 6.3)
│   ├── Per-pass metrics
│   ├── Convergence chart
│   └── Remaining open defects
├── Gap Analysis
│   ├── Requirements traceability summary
│   ├── Untested integration paths
│   ├── Known limitations
│   └── Recommended follow-up work
├── Appendices
│   ├── A: Full RTM table
│   ├── B: All scan violations
│   ├── C: All test results
│   └── D: Cost breakdown
```

---

## 7. Success Criteria Mapping

### 7.1 Build 1 Success Criteria -> Verifiable Assertions

| Success Criterion | Assertion Type | Test Method | Pass Condition |
|---|---|---|---|
| All three services deploy in Docker Compose and pass health checks | Binary | `docker compose up -d && docker compose ps` | All 3 services show "healthy" |
| Architect produces valid Service Map + Contracts from a sample PRD | Binary | MCP call `decompose` with sample PRD | Returns parseable YAML service map + valid OpenAPI specs |
| Contract Engine validates schemas and generates runnable test suites | Binary | MCP call `validate_spec` + `generate_tests` | `validate_spec` returns `{valid: true}` for valid spec; generated tests execute without import errors |
| Codebase Intelligence indexes a 50K+ LOC codebase in under 60 seconds | Graduated | Time `index_codebase` on 50K LOC repo | GREEN: < 60s, YELLOW: 60-120s, RED: > 120s |
| All MCP tools respond correctly when queried by Claude Code | Binary | Query each MCP tool via stdio transport | All tools return non-error responses |
| Dead code detection finds at least the known M4 patterns | Binary | Index codebase with planted dead code, call `check_dead_code` | Returns at least the planted dead functions |

### 7.2 Build 2 Success Criteria -> Verifiable Assertions

| Success Criterion | Assertion Type | Test Method | Pass Condition |
|---|---|---|---|
| Builder uses Claude Code agent teams for internal coordination | Graduated | Check for agent teams API calls in builder logs | GREEN: Uses agent teams, YELLOW: Falls back to subprocess, RED: Crashes |
| Builder queries Contract Engine MCP and gets valid responses | Binary | Grep builder logs for MCP `validate_endpoint` calls | At least 1 successful MCP call logged |
| Builder queries Codebase Intelligence MCP and gets valid responses | Binary | Grep builder logs for MCP `find_definition` calls | At least 1 successful MCP call logged |
| CONTRACT scans detect deliberate violations in test scenarios | Binary | Plant CONTRACT-001 violation, run post-build scan | Scan reports the planted violation |
| Two Builders run in parallel on different services without conflicts | Binary | Run 2 builders simultaneously, check both complete | Both BuilderResults have success=True |
| Generated code registers with codebase index incrementally | Binary | After builder completes, query index for generated symbols | `find_definition` returns locations in generated code |

### 7.3 Build 3 Success Criteria -> Verifiable Assertions

| Success Criterion | Assertion Type | Test Method | Pass Condition |
|---|---|---|---|
| Complete pipeline runs end-to-end without human intervention | Binary | `super-orchestrator run --prd sample.md` | Pipeline reaches "complete" state without manual input |
| 3-service test app deploys, all health checks pass, integration tests pass | Binary | Run pipeline on 3-service PRD, check IntegrationReport | `services_healthy == 3`, `integration_tests_passed == integration_tests_total` |
| Contract violations are detected and reported | Binary | Plant contract violation in test service, run pipeline | QUALITY_GATE_REPORT.md lists the violation |
| Quality Gate layers execute sequentially with proper gating | Binary | Check QUALITY_GATE_REPORT.md for all 4 layers | All 4 layers have non-SKIPPED verdict (or L1 FAIL prevents L2+) |
| Super Orchestrator CLI works for all commands | Binary | Run each of 8 CLI commands | Each returns exit code 0 (or expected error for invalid input) |

### 7.4 Run 4 Success Criteria -> Verifiable Assertions

| Success Criterion | Assertion Type | Test Method | Pass Condition |
|---|---|---|---|
| Complete pipeline runs end-to-end without human intervention | Binary | Full pipeline execution on real PRD | Pipeline completes all phases |
| 3-service test app deploys, all health checks pass, integration tests pass | Binary | Docker compose up, health checks, test execution | All services healthy, all integration tests pass |
| Contract violations are detected and reported | Binary | Introduce deliberate violation, verify detection | Quality Gate catches and reports it |
| Codebase Intelligence indexes generated code and responds to MCP queries | Binary | After build, query index for generated symbols | Returns correct file/line locations |
| Total time from PRD to deployed system: under 6 hours for 3-service app | Graduated | Measure wall-clock time | GREEN: < 6h, YELLOW: 6-10h, RED: > 10h |

### 7.5 Binary vs. Graduated Success

| Assertion Type | When to Use | Scoring |
|---|---|---|
| **Binary** | Feature either works or doesn't: MCP tool responds, Docker service starts, test passes | 0 or 100 (no partial credit) |
| **Graduated** | Performance targets, coverage rates, quality metrics | Linear scale with thresholds for GREEN/YELLOW/RED |

**Rule of thumb:** Use binary for "does it function?" and graduated for "how well does it function?"

### 7.6 "Good Enough" Thresholds

| Criterion | Minimum Acceptable | Target | Stretch |
|---|---|---|---|
| Per-system score | 60/100 (YELLOW) | 80/100 (GREEN) | 90/100 |
| Integration score | 50/100 | 75/100 | 90/100 |
| Aggregate score | 65/100 | 80/100 | 90/100 |
| P0 defects remaining | 0 (hard requirement) | 0 | 0 |
| P1 defects remaining | <= 3 with workarounds | 0 | 0 |
| Test pass rate | >= 85% | >= 95% | 100% |
| Contract compliance | >= 80% | >= 95% | 100% |
| MCP tool coverage | >= 90% | 100% | 100% + error paths |
| Fix pass convergence | >= 0.70 | >= 0.85 | >= 0.95 |

---

## 8. Recommendations for Run 4 Implementation

### 8.1 Audit Execution Order

1. **Phase 1 (Wiring Verification):** Focus on P0 detection. Test every MCP connection, every Docker service startup, every cross-build data handoff. Binary pass/fail only. No scoring yet.

2. **Phase 2 (Builder Integration Test):** Run a single Builder against Build 1 services. Verify MCP calls succeed. This is still P0/P1 territory — if the Builder can't talk to Build 1, everything downstream fails.

3. **Phase 3 (End-to-End Pipeline Test):** First time scoring applies. Run the full pipeline on a 3-service test PRD. Populate the RTM, interface coverage matrix, and data flow path coverage. Compute initial per-system and integration scores.

4. **Phase 4 (Fix Pass):** Use the defect catalog from Phase 3. Apply the convergence criteria from Section 5.4. Track fix effectiveness and regression rate. Stop when convergence criteria are met.

5. **Phase 5 (Final Audit):** Generate SUPER_TEAM_AUDIT_REPORT.md using the template from Section 6.4. Honest assessment — document what works, what doesn't, and what's unknown.

### 8.2 Audit Prompt Design

The audit agent should receive a structured prompt that includes:

```
AUDIT AGENT INSTRUCTIONS:

1. You are scoring the system, not building it. Your job is to FIND problems, not fix them.
2. Test every assertion in Section 7 against the actual system.
3. For each assertion, record: PASS, FAIL, or UNTESTABLE (with reason).
4. Classify every failure as P0/P1/P2/P3 using the decision tree in Section 3.2.
5. Populate the RTM (Section 4.1) as you verify requirements.
6. Populate the interface coverage matrix (Section 4.2) as you test MCP tools.
7. Populate the data flow path coverage (Section 4.3) as you trace data through the pipeline.
8. Compute scores using the formulas in Section 2.
9. Write SUPER_TEAM_AUDIT_REPORT.md using the template in Section 6.4.
10. Be HONEST. A "RED" system with documented gaps is more valuable than a "GREEN" system with hidden issues.
```

### 8.3 Fix Pass Prompt Design

The fix agent should receive:

```
FIX AGENT INSTRUCTIONS:

1. You are fixing defects, not adding features. Do not refactor or improve code that isn't broken.
2. Fix P0 defects first, then P1, then P2. Do not fix P3 defects.
3. For each fix: (a) identify root cause, (b) apply minimal change, (c) verify the fix resolves the specific defect, (d) run adjacent tests to check for regressions.
4. If a fix attempt fails twice, escalate to the audit agent for re-classification.
5. Track: defect ID, fix description, files changed, tests affected, regression check result.
6. Do not modify test expectations to match broken behavior. Fix the code, not the test.
```

### 8.4 Score Interpretation Guide

| Aggregate Score | Interpretation | Action |
|---|---|---|
| 90-100 | System exceeds expectations. Ship it. | Final documentation pass |
| 80-89 | System meets expectations with minor gaps. | Document gaps, ship with caveats |
| 70-79 | System works but has significant gaps. | One more fix pass recommended |
| 60-69 | System partially works. Major features have issues. | Multiple fix passes needed |
| 50-59 | System has critical failures. Some builds may need rework. | Targeted rework of failing builds |
| < 50 | System has fundamental issues. | Reassess architecture/approach |

### 8.5 Key Risk for Run 4

The biggest risk is **false GREEN** — the audit reports everything passing when in fact integration edge cases were never tested. Mitigations:

1. **Require dark corner testing (Section 4.4):** The audit agent must explicitly test race conditions, concurrent access, and resume-from-crash scenarios.
2. **Require negative testing:** For every MCP tool, test with invalid input and verify the error response is useful.
3. **Require the fix pass to introduce a deliberate regression** and verify the audit detects it. This validates the audit itself.
4. **Cap the score at 85** if any dark corner from Section 4.4 was not tested. This prevents false confidence.

### 8.6 Artifact Checklist

Run 4 should produce these artifacts:

| Artifact | Location | Required |
|---|---|---|
| SUPER_TEAM_AUDIT_REPORT.md | .super-orchestrator/ | Yes |
| Requirements Traceability Matrix | Appendix A of audit report | Yes |
| Interface Coverage Matrix | Appendix B of audit report | Yes |
| Data Flow Path Coverage | Appendix C of audit report | Yes |
| Fix Pass Log | Section in audit report | Yes |
| Per-system score breakdown | Section in audit report | Yes |
| Defect catalog (all FINDING-xxx) | Section in audit report | Yes |
| Convergence chart | Section in audit report | If > 1 fix pass |
| Dark corners tested/untested | Gap Analysis section | Yes |
| Cost breakdown | Appendix D | Yes |
