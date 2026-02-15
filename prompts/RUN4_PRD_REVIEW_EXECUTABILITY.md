# RUN4_PRD.md Executability Review

> **Reviewer**: Executability Review Agent
> **Date**: 2026-02-15
> **PRD Version**: 1.0
> **Total Requirements**: 119 (42 REQ + 9 TECH + 7 INT + 20 WIRE + 20 SVC + 18 TEST + 3 SEC)

---

## Executive Summary

**Score: 112/119 requirements are fully executable (94.1%)**

The PRD is exceptionally well-specified for LLM agent execution. The core wiring milestones (M1-M3) are essentially perfect — every requirement has exact function signatures, return types, field names, error behaviors, and test assertions. The 7 gaps are concentrated in Milestones 4-6 where some requirements use category-level descriptions rather than specific scan implementations.

**Verdict: READY FOR EXECUTION with 7 targeted clarifications recommended.**

---

## Per-Requirement Executability Assessment

### Milestone 1: Test Infrastructure + Fixtures (26 items)

| ID | Score | Notes |
|---|---|---|
| REQ-001 | EXECUTABLE | Fields enumerated in Config.yaml template; dataclass structure clear |
| REQ-002 | EXECUTABLE | Fields listed; schema details in TECH-002/REQ-029 |
| REQ-003 | EXECUTABLE | Algorithm specified (write .tmp then os.replace); load validation clear |
| REQ-004 | EXECUTABLE | Exact path, 3 services, all Python/FastAPI |
| REQ-005 | EXECUTABLE | Exact path, 3 endpoints with full schemas |
| REQ-006 | EXECUTABLE | Exact path, JWT auth header, full schemas |
| REQ-007 | EXECUTABLE | Exact path, AsyncAPI 3.0, 2 channels |
| REQ-008 | EXECUTABLE | Exact path, Pact V4, specific interaction |
| TECH-001 | EXECUTABLE | Exact exception type (ValueError), trigger (missing path) |
| TECH-002 | **NEEDS_CLARIFICATION** | References "RUN4_ARCHITECTURE_PLAN.md Section 7.1" which is external to this PRD. Finding dataclass partially specified in REQ-029 but full schema requires the external doc. |
| TECH-003 | EXECUTABLE | Specific validators named (openapi-spec-validator, structural validation) |
| INT-001 | EXECUTABLE | Exact fixture names, session-scoped, conftest.py path clear |
| INT-002 | EXECUTABLE | AsyncMock with 3 named methods |
| INT-003 | EXECUTABLE | Signature (data, is_error), TextContent + JSON format |
| INT-004 | EXECUTABLE | Signature with 4 params, polling behavior, return type |
| INT-005 | EXECUTABLE | Full return dict schema (status/tools_count/tool_names/error) |
| INT-006 | EXECUTABLE | Exact STATE.JSON fields to extract |
| INT-007 | EXECUTABLE | Compare snapshots, return regressed violations |
| TEST-001 | EXECUTABLE | Roundtrip assertion including nested structures |
| TEST-002 | EXECUTABLE | Two cases: missing file -> None, corrupted -> None |
| TEST-003 | EXECUTABLE | ValueError on missing build root |
| TEST-004 | EXECUTABLE | Syntactic validity of YAML fixtures |
| TEST-005 | EXECUTABLE | AsyncMock usability check |
| TEST-006 | EXECUTABLE | Returns within timeout for healthy mocks |
| TEST-007 | EXECUTABLE | Detects new violations not in previous snapshot |

**M1 Result: 25/26 EXECUTABLE (96.2%)**

---

### Milestone 2: Build 1 -> Build 2 MCP Wiring (37 items)

| ID | Score | Notes |
|---|---|---|
| REQ-009 | EXECUTABLE | Exact steps: spawn, initialize, verify "tools" capability, list_tools, exactly 4 tools |
| REQ-010 | EXECUTABLE | 9 tools with exact names enumerated |
| REQ-011 | EXECUTABLE | 7 tools with exact names enumerated |
| REQ-012 | EXECUTABLE | 3 test dimensions per tool: valid/invalid/parse |
| REQ-013 | EXECUTABLE | 3 assertions: types, safe defaults, retry 3x with 1s/2s/4s backoff |
| REQ-014 | EXECUTABLE | Same pattern as REQ-013, 7 methods |
| REQ-015 | EXECUTABLE | Specific: decompose() returns None on failure |
| WIRE-001 | EXECUTABLE | 10 sequential calls, all succeed |
| WIRE-002 | EXECUTABLE | Kill server, verify broken pipe detection |
| WIRE-003 | EXECUTABLE | Exceed timeout, verify TimeoutError |
| WIRE-004 | EXECUTABLE | 3 parallel sessions, no resource conflicts |
| WIRE-005 | EXECUTABLE | Close/reopen, verify data persistence |
| WIRE-006 | EXECUTABLE | Malformed JSON -> isError, no crash |
| WIRE-007 | EXECUTABLE | Non-existent tool -> error response, no crash |
| WIRE-008 | EXECUTABLE | Non-zero exit -> client detects and logs |
| WIRE-009 | EXECUTABLE | Fallback to run_api_contract_scan() |
| WIRE-010 | EXECUTABLE | Fallback to generate_codebase_map() |
| WIRE-011 | EXECUTABLE | Standard decomposition proceeds |
| WIRE-012 | EXECUTABLE | Cross-server HTTP call verification |
| TEST-008 | EXECUTABLE | Thresholds: <5s/tool, <30s startup, median/p95/p99 |
| SVC-001..017 | EXECUTABLE | Full DTO schemas in wiring map table — every field name and type listed |

**M2 Result: 37/37 EXECUTABLE (100%)**

---

### Milestone 3: Build 2 -> Build 3 Wiring (13 items)

| ID | Score | Notes |
|---|---|---|
| REQ-016 | EXECUTABLE | Exact command, 3 assertions (exit code, STATE.JSON, stdout) |
| REQ-017 | EXECUTABLE | 7 fields with exact types: success(bool), test_passed(int), etc. |
| REQ-018 | EXECUTABLE | Return type tuple[AgentTeamConfig, set[str]], all 4 depth levels |
| REQ-019 | EXECUTABLE | Semaphore(3), cross-contamination check, 4th blocked |
| REQ-020 | EXECUTABLE | 5-step procedure with specific verifications |
| WIRE-013 | EXECUTABLE | create_execution_backend() returns CLIBackend with warning |
| WIRE-014 | EXECUTABLE | RuntimeError raised |
| WIRE-015 | EXECUTABLE | 5s timeout, proc.kill() + proc.wait() in finally |
| WIRE-016 | EXECUTABLE | ANTHROPIC_API_KEY not passed explicitly |
| TEST-009 | EXECUTABLE | BuilderResult field mapping |
| TEST-010 | EXECUTABLE | 3-builder aggregation, per-service results preserved |
| SVC-018..020 | EXECUTABLE | Full subprocess wiring with commands, inputs, outputs |

**M3 Result: 13/13 EXECUTABLE (100%)**

---

### Milestone 4: E2E Pipeline Test (20 items)

| ID | Score | Notes |
|---|---|---|
| REQ-021 | EXECUTABLE | Ports 8001/8002/8003, HTTP 200 on /api/health, ALL 3 gate |
| REQ-022 | EXECUTABLE | Specific tools per server, ALL pass gate |
| REQ-023 | EXECUTABLE | >= 3 services AND >= 3 entities gate |
| REQ-024 | EXECUTABLE | create_contract, validate_spec, list_contracts, ALL gate |
| REQ-025 | EXECUTABLE | >= 2/3 builders succeed gate |
| REQ-026 | **NEEDS_CLARIFICATION** | "run contract compliance via Schemathesis against live services" — missing: which OpenAPI spec URL to point Schemathesis at, which services to test, what Schemathesis profile/options. "run cross-service integration tests" lists steps (register->login->create order->notification) but lacks per-step assertions (expected status codes, response body fields). Gate "> 70% contract compliance" is clear. |
| REQ-027 | **NEEDS_CLARIFICATION** | Layer 3: "security, CORS, logging, secrets, Docker, health scans" is a list of categories without specific checks. What constitutes a "security scan"? What CORS rules are checked? What logging patterns are verified? Layer 4: "adversarial review" methodology undefined — is it an LLM call, static analysis, or manual checklist? What determines "dead events" or "orphan services"? Gate "overall_verdict != failed" is clear but layers 3/4 are not implementable as-is. |
| REQ-028 | EXECUTABLE | 3 specific violations with IDs: HEALTH-001, SCHEMA-001, LOG-001 |
| WIRE-017 | **NEEDS_CLARIFICATION** | "correct network topology (frontend + backend networks)" — which services must be on which network? Diagram exists but no assertion spec (e.g., "verify auth-service is on both frontend and backend networks"). |
| WIRE-018 | EXECUTABLE | Architect resolves contract-engine hostname via HTTP |
| WIRE-019 | EXECUTABLE | PathPrefix routing verification |
| WIRE-020 | EXECUTABLE | Exact startup order cascade specified |
| TECH-004 | EXECUTABLE | Exact 5-file list |
| TECH-005 | EXECUTABLE | Ephemeral volumes, random port mapping |
| TECH-006 | EXECUTABLE | Exact RAM: 2GB + 640MB + 128MB + 1.5GB = 4.5GB |
| SEC-001 | EXECUTABLE | Binary: no explicit ANTHROPIC_API_KEY passing |
| SEC-002 | EXECUTABLE | Binary: --api.dashboard=false |
| SEC-003 | EXECUTABLE | Binary: /var/run/docker.sock:ro |
| TEST-011 | EXECUTABLE | Timing: <6h GREEN threshold |
| TEST-012 | EXECUTABLE | Kill mid-build, resume from checkpoint |

**M4 Result: 17/20 EXECUTABLE (85%)**

---

### Milestone 5: Fix Pass + Defect Remediation (8 items)

| ID | Score | Notes |
|---|---|---|
| REQ-029 | EXECUTABLE | Finding dataclass with 10 fields, all formats specified |
| REQ-030 | EXECUTABLE | P0-P3 decision tree with exact criteria |
| REQ-031 | EXECUTABLE | 6-step procedure: DISCOVER, CLASSIFY, GENERATE, APPLY, VERIFY, REGRESS |
| REQ-032 | EXECUTABLE | 4 metrics with exact formulas |
| REQ-033 | **NEEDS_CLARIFICATION** | "budget exhausted" listed as a hard stop trigger but Run4Config (Config.yaml template) has no budget field. The agent has no way to know what budget ceiling to check against. Other hard stops are fully specified. |
| TECH-007 | EXECUTABLE | Full convergence formula with >= 0.85 threshold |
| TECH-008 | EXECUTABLE | dict[str, list[str]] format, saved as JSON |
| TEST-013..015 | EXECUTABLE | Specific scenarios and assertions |

**M5 Result: 7/8 EXECUTABLE (87.5%)**

---

### Milestone 6: Audit Report + Final Verification (11 items)

| ID | Score | Notes |
|---|---|---|
| REQ-034 | **NEEDS_CLARIFICATION** | Formula is complete EXCEPT: (1) "violation_density per KLOC" — how is KLOC measured? Total lines in generated code? All code including tests? Only service code? (2) "artifacts_present / artifacts_required" — what is the enumerated list of required artifacts? README? Dockerfile? docker-compose.yml? OpenAPI spec? Without this list, an agent must guess. |
| REQ-035 | EXECUTABLE | Full formula with known denominators (20 tools, flows from data flows section) |
| REQ-036 | EXECUTABLE | Aggregate formula + traffic light thresholds |
| REQ-037 | EXECUTABLE | 7 sections enumerated with content descriptions |
| REQ-038 | EXECUTABLE | Per-REQ format: files, test IDs, status, verification |
| REQ-039 | EXECUTABLE | 4 columns per tool, targets (100%/80%) |
| REQ-040 | EXECUTABLE | 5 flows + error paths, tested Y/N, status, evidence |
| REQ-041 | **NEEDS_CLARIFICATION** | Lists 5 dark corner scenarios but provides no test procedures or pass/fail criteria. E.g., "MCP server startup race condition" — what is the test? Start 3 servers simultaneously and verify all reach healthy? Or inject timing delays? "large PRD handling" — how large? 100KB? 1MB? What is expected behavior? This reads as a checklist of topics to explore, not executable test specs. |
| REQ-042 | EXECUTABLE | Per-phase cost/duration, grand total, budget comparison |
| TECH-009 | EXECUTABLE | All thresholds are specific numbers |
| TEST-016..018 | EXECUTABLE | Specific inputs and assertions |

**M6 Result: 9/11 EXECUTABLE (81.8%)**

---

## Cross-Cutting Issues

### 1. Missing Source Directory Structure (MEDIUM)

The PRD specifies test file locations (tests/run4/...) but does NOT specify where production code should live. Where do these modules go?

- Run4Config and Run4State dataclasses
- Scoring functions
- Fix pass logic
- Issue cataloging
- Audit report generator
- poll_until_healthy, check_mcp_health, detect_regressions utilities

**Recommendation**: Add a source directory layout similar to the test directory structure:

```
src/run4/
    config.py          # Run4Config
    state.py           # Run4State, Finding
    mcp_health.py      # check_mcp_health, poll_until_healthy
    builder.py         # builder invocation, parallel execution
    fix_pass.py        # fix loop, convergence, regression detection
    scoring.py         # per-system scoring, integration scoring, aggregate
    audit_report.py    # report generation, RTM, coverage matrices
```

### 2. No Budget Configuration (LOW-MEDIUM)

REQ-033 references "budget exhausted" as a hard stop but the Config.yaml template has no `budget` or `max_budget` field. Either add it to config or remove the hard stop condition.

### 3. External Document Reference (LOW)

TECH-002 references "RUN4_ARCHITECTURE_PLAN.md Section 7.1" for the full Finding schema. The Finding dataclass IS described in REQ-029 with all 10 fields, so this is partially mitigated. The reference should either be inlined or removed.

---

## Requirements Needing Clarification

### 1. TECH-002 — External Schema Reference

**Issue**: References RUN4_ARCHITECTURE_PLAN.md Section 7.1 for Finding dataclass schema.
**Fix**: Inline the complete Finding schema here OR confirm REQ-029's description is the canonical source.

### 2. REQ-026 — Schemathesis Configuration

**Issue**: "Run contract compliance via Schemathesis" without specifying:
- Which OpenAPI spec URL to feed Schemathesis
- Which services to test
- Schemathesis profile/options (stateful/stateless, authentication)
- Per-step assertions for the integration test flow

**Fix**: Add:
```
Schemathesis: point at http://localhost:{port}/openapi.json for each of the 3 generated services;
use stateful mode; authenticate with JWT from auth-service login.
Integration flow assertions:
  - Register: POST /register -> 201, body has {id, email, created_at}
  - Login: POST /login -> 200, body has {access_token, refresh_token}
  - Create order: POST /orders (with JWT) -> 201, body has {id, status, items, total}
  - Notification: GET /notifications -> 200, body is list with len >= 1
```

### 3. REQ-027 — Quality Gate Layers 3 and 4

**Issue**: Layer 3 lists categories (security, CORS, logging, secrets, Docker, health) without specific checks. Layer 4 says "adversarial review" without defining methodology.

**Fix**: Enumerate specific checks, e.g.:
```
Layer 3 checks:
  - SEC-SCAN-001: No hardcoded secrets (regex: password|secret|api_key\s*=\s*["'][^"']+["'])
  - CORS-001: CORS origins not set to "*" in production config
  - LOG-001: No print() statements (use logging module)
  - LOG-002: All endpoints have request logging middleware
  - DOCKER-001: All services have HEALTHCHECK instruction
  - DOCKER-002: No :latest tags in FROM statements

Layer 4 checks (static analysis, not LLM):
  - DEAD-001: Events published but never consumed (cross-reference publish/subscribe)
  - DEAD-002: Contracts registered but never validated
  - ORPHAN-001: Service in compose but no route in Traefik config
  - NAME-001: Service names consistent across compose, code, and contracts
```

### 4. REQ-033 — Budget Hard Stop

**Issue**: "budget exhausted" is a hard stop trigger but no budget field exists in Run4Config.

**Fix**: Add `max_budget_usd: float = 100.0` to Run4Config and config.yaml template, OR remove "budget exhausted" from hard stops and keep it informational only.

### 5. REQ-034 — Scoring Ambiguities

**Issue**: Two undefined terms:
- "violation_density per KLOC" — which lines are counted?
- "artifacts_required" — which artifacts?

**Fix**: Add definitions:
```
violation_density = total_violations / (total_lines_of_code / 1000)
  where total_lines_of_code counts .py files in service source directories (excluding tests, __pycache__, venv)

artifacts_required per service (5 items):
  1. Dockerfile
  2. requirements.txt or pyproject.toml
  3. README.md
  4. OpenAPI/AsyncAPI spec file
  5. Health check endpoint (/health)
```

### 6. REQ-041 — Dark Corners Test Procedures

**Issue**: 5 scenarios listed without test procedures or pass/fail criteria.

**Fix**: Specify per scenario:
```
1. MCP server startup race condition:
   TEST: Start all 3 MCP servers simultaneously (asyncio.gather), verify all 3 reach "healthy" within mcp_startup_timeout_ms.
   PASS: All 3 healthy. FAIL: Any server fails to start or deadlocks.

2. Docker network DNS resolution:
   TEST: From architect container, curl http://contract-engine:8000/api/health.
   PASS: HTTP 200. FAIL: DNS resolution failure or connection refused.

3. Concurrent builder file conflicts:
   TEST: Launch 3 builders targeting separate directories, verify no file in builder A's directory was written by builder B.
   PASS: Zero cross-directory writes. FAIL: Any file found in wrong directory.

4. State machine resume after crash:
   TEST: Run pipeline to phase 3, kill process (SIGINT), restart, verify resume from phase 3 checkpoint.
   PASS: Resumes from phase 3, does not re-run phases 1-2. FAIL: Restarts from phase 1.

5. Large PRD handling:
   TEST: Feed 200KB PRD (4x normal size) to Architect decompose; verify decomposition completes within 2x normal timeout.
   PASS: Valid ServiceMap returned. FAIL: Timeout or crash.
```

### 7. WIRE-017 — Docker Network Assertions

**Issue**: "correct network topology" without specific assertions.

**Fix**: Add:
```
Verify via docker network inspect:
  - frontend network contains: traefik, architect, contract-engine, codebase-intelligence, auth-service, order-service, notification-service
  - backend network contains: postgres, redis, architect, contract-engine, codebase-intelligence, auth-service, order-service, notification-service
  - traefik is NOT on backend network
  - postgres and redis are NOT on frontend network
```

---

## Summary Statistics

| Milestone | Total | Executable | Needs Clarification | Ambiguous | % Executable |
|---|---|---|---|---|---|
| M1: Infrastructure | 26 | 25 | 1 | 0 | 96.2% |
| M2: B1->B2 MCP | 37 | 37 | 0 | 0 | **100%** |
| M3: B2->B3 Wiring | 13 | 13 | 0 | 0 | **100%** |
| M4: E2E Pipeline | 20 | 17 | 3 | 0 | 85.0% |
| M5: Fix Pass | 8 | 7 | 1 | 0 | 87.5% |
| M6: Audit Report | 11 | 9 | 2 | 0 | 81.8% |
| **Total** | **119** | **112** | **7** | **0** | **94.1%** |

| Category | Total | Executable | Needs Clarification |
|---|---|---|---|
| REQ-xxx | 42 | 37 | 5 |
| TECH-xxx | 9 | 8 | 1 |
| INT-xxx | 7 | 7 | 0 |
| WIRE-xxx | 20 | 19 | 1 |
| SVC-xxx | 20 | 20 | 0 |
| TEST-xxx | 18 | 18 | 0 |
| SEC-xxx | 3 | 3 | 0 |

---

## Anti-Pattern Check

| Anti-Pattern | Found? | Where |
|---|---|---|
| "Ensure proper error handling" | NO | Error handling is specific throughout |
| "Validate appropriately" | NO | Validation criteria are specific |
| "Handle edge cases" | NO | Edge cases enumerated where relevant |
| "Good performance" | NO | Thresholds are numbers (<5s, <30s, <6h) |
| "All necessary tests" | NO | Tests enumerated with IDs |
| Vague "etc." or "and more" | NO | Data structures fully specified |
| "As needed" / "suitable" | NO | Choices are explicit |
| Undefined scoring formulas | PARTIAL | 2 terms in REQ-034 need definition |
| Missing file locations | YES | Source code directory structure not specified |
| External document dependencies | YES | TECH-002 references external doc |

---

## Recommendations Priority

| Priority | ID | Fix |
|---|---|---|
| HIGH | Cross-cutting | Add source directory structure (where production code goes) |
| HIGH | REQ-027 | Enumerate specific Layer 3/4 checks |
| MEDIUM | REQ-026 | Add Schemathesis config and per-step assertions |
| MEDIUM | REQ-041 | Add test procedures and pass/fail per scenario |
| MEDIUM | REQ-034 | Define KLOC measurement and artifacts_required list |
| LOW | REQ-033 | Add budget field to config OR remove "budget exhausted" hard stop |
| LOW | TECH-002 | Inline Finding schema or confirm REQ-029 is canonical |
| LOW | WIRE-017 | Add specific network membership assertions |

---

## Conclusion

This is a high-quality PRD with 94.1% executability. The wiring milestones (M2, M3) are perfect at 100% — every field name, type, error path, and assertion is explicit. The 7 gaps are all fixable with targeted additions (mostly enumerating specific checks and measurements). No requirements are ambiguous — they all have clear intent; the gaps are specificity gaps, not conceptual ones.

The most impactful fix would be adding the source directory structure (cross-cutting) and enumerating the Quality Gate Layer 3/4 checks (REQ-027), as these affect the most implementation decisions.
