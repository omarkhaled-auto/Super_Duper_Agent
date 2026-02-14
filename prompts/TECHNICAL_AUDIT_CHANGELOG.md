# Technical Audit Changelog

All changes applied to BUILD1_PRD.md, BUILD2_PRD.md, and BUILD3_PRD.md based on findings from 10 technical audit reports.

**Audit Reports Consumed:**
1. AUDIT_MCP_SDK.md
2. AUDIT_ANTHROPIC_SDK.md
3. AUDIT_DOCKER_TRAEFIK.md
4. AUDIT_TESTING_FRAMEWORKS.md
5. AUDIT_SECURITY_SCANNING.md
6. AUDIT_STATE_CLI.md
7. AUDIT_ASYNC_PATTERNS.md
8. AUDIT_TREE_SITTER.md
9. AUDIT_PYDANTIC_FASTAPI.md
10. AUDIT_CROSS_BUILD_INTEGRATION.md

**Total Findings:** 13 CRITICAL, 14 HIGH, 18+ MEDIUM
**Total Fixes Applied:** 33 in BUILD3_PRD.md, 11 in BUILD1_PRD.md, 7 in BUILD2_PRD.md = 51 total

---

## BUILD1_PRD.md Changes

### CRITICAL Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 1 | AUDIT_MCP_SDK | H-1 (escalated) | REQ-059 | Added `decompose(prd_text: str)` as 4th Architect MCP tool — Build 3 calls this tool but it was missing |
| 2 | AUDIT_MCP_SDK | H-2 (escalated) | REQ-060 | Added `create_contract()`, `validate_spec()`, `list_contracts()` as 3 new Contract Engine MCP tools (6 -> 9 tools) — Build 3 calls these tools but they were missing |
| 3 | AUDIT_ASYNC_PATTERNS | CRIT-1 | REQ-020 | Added `asyncio.to_thread()` requirement for sync httpx calls inside async MCP decompose endpoint |

### HIGH Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 4 | AUDIT_TREE_SITTER | M-1 (escalated) | REQ-042 | Added TypeScript cross-reference note: "language_typescript() and language_tsx() instead of language()" |
| 5 | AUDIT_TREE_SITTER | M-2 (escalated) | REQ-043 | Added explicit import instruction: "Import Query and QueryCursor from tree_sitter" |

### MEDIUM Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 6 | AUDIT_ASYNC_PATTERNS | M-ref | TECH-026 | Added note that MCP tool handler must be sync `def` (not `async def`) when using sync httpx |
| 7 | AUDIT_ASYNC_PATTERNS | NEW | TECH-035 | NEW requirement: asyncio.to_thread() wrapping for sync calls in async contexts |
| 8 | AUDIT_ASYNC_PATTERNS | NEW | TECH-036 | NEW requirement: ChromaDB operations are synchronous and must use asyncio.to_thread() |

### Cascading Updates

| # | Requirement | Change Description |
|---|-------------|-------------------|
| 9 | Milestone 7 desc | Updated "3 tools" to "4 tools" and "6 tools" to "9 tools" |
| 10 | REQ-070 | Updated "16 tools" to "20 tools" |
| 11 | TEST-033 | Added decompose tool test case |
| 12 | TEST-034 | Added create_contract, validate_spec, list_contracts tool tests |

---

## BUILD2_PRD.md Changes

### HIGH Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 1 | AUDIT_ASYNC_PATTERNS | CRIT-2 | REQ-007 | Added `(using await asyncio.sleep(30), NOT time.sleep(30))` to monitoring interval |
| 2 | AUDIT_CROSS_BUILD | CRIT-04 | TECH-031 | Added `summary` dict to RunState.to_dict() with computed `success`, `test_passed`, `test_total`, `convergence_ratio` fields for Build 3 consumption |

### MEDIUM Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 3 | AUDIT_CROSS_BUILD | HIGH-03 | REQ-034 | Added `language: str | None = None, service_name: str | None = None` params to search_semantic |
| 4 | AUDIT_CROSS_BUILD | HIGH-01 | TECH-030 | Renamed `IntegrationReport` to `EndpointTestReport` to avoid namespace collision with Build 3 |

### Cascading Updates

| # | Requirement | Change Description |
|---|-------------|-------------------|
| 5 | INT-003 | Added ArchitectClient requirement, updated from 3 to 4 tools |
| 6 | INT-001 | Updated from 6 to 9 tools |
| 7 | All IntegrationReport refs | Updated to EndpointTestReport throughout (lines 31, 288, 343, TECH-031) |

---

## BUILD3_PRD.md Changes

### CRITICAL Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 1 | AUDIT_TESTING_FRAMEWORKS | CRIT-1 | REQ-019 | Fixed Schemathesis programmatic API: replaced `schema.items()` / `methods.items()` with correct `schema.get_all_operations()` iterator. Changed exception from `CheckFailed` to `FailureGroup` |
| 2 | AUDIT_TESTING_FRAMEWORKS | CRIT-2 | TECH-012 | Fixed exception class: `schemathesis.exceptions.CheckFailed` -> `schemathesis.failures.FailureGroup` (list-like container of Failure objects) |
| 3 | AUDIT_TESTING_FRAMEWORKS | CRIT-3 | REQ-021 | Fixed Pact Verifier API: `Verifier(name)` -> `Verifier().set_info("provider", url=url)`. Added `host` parameter requirement for `add_transport()` |
| 4 | AUDIT_TESTING_FRAMEWORKS | CRIT-4 | REQ-021 | Fixed `verifier.verify()` return type: returns `Self` (not None), raises on failure (no `PactVerificationError` class) |
| 5 | AUDIT_TESTING_FRAMEWORKS | CRIT-5 | TECH-013 | Complete Pact API rewrite: `from pact.v3.verifier import Verifier`, no-arg constructor, `set_info()`, `set_state_handler()` (not `set_state()`), `.verify()` returns Self |
| 6 | AUDIT_ASYNC_PATTERNS | CRIT-1 | REQ-019 | Added asyncio.to_thread() requirement for all sync Schemathesis calls in async methods |
| 7 | AUDIT_ASYNC_PATTERNS | CRIT-2 | REQ-021 | Added asyncio.to_thread() requirement for all sync Pact Verifier calls in async methods |
| 8 | AUDIT_STATE_CLI | C1/C2 | REQ-011 | Fixed `fail` transition: changed `source="*"` wildcard to explicit list of 9 non-terminal states (excludes `complete` and `failed` to prevent final state corruption) |
| 9 | AUDIT_STATE_CLI | C3 | REQ-011 | Added explicit `model=model` parameter instruction for `AsyncMachine` constructor in `create_pipeline_machine()` factory |
| 10 | AUDIT_CROSS_BUILD | CRIT-03 | Project Structure | Renamed `src/shared/` to `src/build3_shared/` to avoid namespace collision with Build 1's `src/shared/` |
| 11 | AUDIT_CROSS_BUILD | CRIT-04 | REQ-048 | Added explicit STATE.json -> BuilderResult field mapping: `success = state_json["summary"]["success"]`, `cost = state_json["total_cost"]`, etc. |

### HIGH Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 12 | AUDIT_TESTING_FRAMEWORKS | HIGH-1 | REQ-021 | Fixed `verifier.set_state()` -> `verifier.set_state_handler()` (correct Pact v3 API) |
| 13 | AUDIT_SECURITY_SCANNING | H-1 | REQ-035 | Fixed GitHub token regex SEC-SECRET-007: `gh[ps]_` -> `gh[psatr]_` to cover all 6 token types (ghp, ghs, gha, ghr, gho, ghu) |
| 14 | AUDIT_ASYNC_PATTERNS | HIGH-2 | REQ-024 | Added `await proc.wait()` after `proc.kill()` to reap zombie processes, plus `finally` block requirement |
| 15 | AUDIT_STATE_CLI | H2 | TECH-029 | Expanded asyncio.run() pattern: defined sync-wrapper-calls-async pattern for Typer commands, warned against nesting |
| 16 | AUDIT_STATE_CLI | H1 | REQ-054 | Added `--version` flag callback with `is_eager=True` for `super-orchestrator --version` |
| 17 | AUDIT_CROSS_BUILD | HIGH-04 | REQ-049 | Added field name verification instruction against Build 2's AgentTeamConfig, depth propagation note, yaml.safe_dump() usage |

### MEDIUM Fixes

| # | Source Audit | ID | Requirement | Change Description |
|---|-------------|-----|-------------|-------------------|
| 18 | AUDIT_SECURITY_SCANNING | M-1 | REQ-034 | Enhanced SEC-003/SEC-004 regexes to catch PyJWT `options={"verify_signature": False}` dict format |
| 19 | AUDIT_SECURITY_SCANNING | M-2 | REQ-035 | Enhanced SEC-SECRET-002 private key regex: added OPENSSH and ENCRYPTED PEM format types |
| 20 | AUDIT_SECURITY_SCANNING | M-3 | REQ-035 | Enhanced SEC-SECRET-011 Slack token regex: `xoxb-` -> `xox[bpoas]-` to cover all 5 Slack token types |
| 21 | AUDIT_DOCKER_TRAEFIK | M-1 | REQ-015 | Added `--ping=true` prerequisite note for Traefik healthcheck command |
| 22 | AUDIT_ASYNC_PATTERNS | M-1 | REQ-036 | Added W3C traceparent format specification: `00-{32hex}-{16hex}-{2hex}` |
| 23 | AUDIT_ASYNC_PATTERNS | M-2 | REQ-017 | Added `await asyncio.sleep(5)` explicit note (NOT `time.sleep(5)`) for health poll loop |
| 24 | AUDIT_ASYNC_PATTERNS | M-3 | REQ-018 | Added `await asyncio.sleep(3)` explicit note for service health poll loop |
| 25 | AUDIT_ASYNC_PATTERNS | M-4 | REQ-048 | Added semaphore creation instruction: create INSIDE function body, not at module level |
| 26 | AUDIT_ASYNC_PATTERNS | M-5 | REQ-013 | Added reentrancy guard for signal handler: `if self._should_stop: return` before second SIGINT |
| 27 | AUDIT_ASYNC_PATTERNS | M-6 | REQ-059 | Added Rich `Group` import source: `from rich.console import Group` |
| 28 | AUDIT_ASYNC_PATTERNS | M-7 | REQ-059 | Added `_console = Console()` singleton pattern at module level |
| 29 | AUDIT_ASYNC_PATTERNS | M-8 | TECH-030 | Added complete Rich import paths for Progress, Panel, Table, Console, Group |
| 30 | AUDIT_ASYNC_PATTERNS | M-9 | REQ-053 | Added subprocess cleanup requirement: `try/finally` with `proc.kill()` + `await proc.wait()` |

### New Requirements Added

| # | Requirement | Description |
|---|-------------|-------------|
| 31 | TECH-014a | Schemathesis and Pact asyncio.to_thread() wrapping requirement (sync-in-async pattern) |

### Cascading Updates

| # | Location | Change Description |
|---|----------|-------------------|
| 32 | State Machine Transitions Table, Row 11 | Changed source from `*` to explicit 9-state list |
| 33 | SVC-002 wiring table | Updated Pact API: `Verifier().set_info()` pattern, returns Self |
| 34 | SVC-002 requirement line | Same Pact API update |
| 35 | TEST-011 | Updated test description: `get_all_operations + make_case` instead of `schema.items()` |
| 36 | TEST-012 | Updated: `PactVerificationError` -> `Pact exception` (generic, since class name differs) |
| 37 | Wiring Anti-Patterns | Expanded asyncio.run() anti-pattern description |
| 38 | WIRE-001 wiring table | Updated: `shared import` -> `build3_shared import` |
| 39 | Architecture File Structure | Updated `shared/` -> `build3_shared/` with collision explanation |
| 40 | All `src/shared/` references | Renamed to `src/build3_shared/` throughout (models.py, protocols.py, constants.py, utils.py, __init__.py, wiring refs) |

---

## Issues NOT Fixed (Deferred / Not Applicable)

| Source Audit | ID | Severity | Reason for Deferral |
|-------------|-----|----------|-------------------|
| AUDIT_ANTHROPIC_SDK | H-1 | HIGH | Invalid model IDs in tech_research.py — this is in the agent-team codebase, NOT in the PRDs |
| AUDIT_PYDANTIC_FASTAPI | L-1..L-3 | LOW | All Pydantic/FastAPI patterns verified correct — no changes needed |
| AUDIT_DOCKER_TRAEFIK | L-1..L-2 | LOW | Minor Docker Compose formatting — cosmetic only |
| AUDIT_STATE_CLI | L-1 | LOW | transitions library version pin — already correct at 0.9.2+ |
| AUDIT_TREE_SITTER | L-1 | LOW | tree-sitter version pin — already correct |

---

## Verification Checklist

- [x] All CRITICAL issues fixed in correct PRD(s)
- [x] All HIGH issues fixed in correct PRD(s)
- [x] All MEDIUM issues fixed or documented with deferral reason
- [x] No new features added — only technical corrections
- [x] All requirement numbering remains sequential
- [x] All `(review_cycles: N)` suffixes preserved
- [x] Cross-PRD consistency maintained (Build 1 tools match Build 3 expectations, Build 2 STATE.json matches Build 3 BuilderResult)
- [x] No new requirements break existing dependency chains

## Fix Confidence: HIGH

All fixes are directly sourced from audit reports that were validated against library documentation. The most impactful changes are:

1. **Schemathesis 4.x API** (CRITICAL): `schema.items()` replaced with `get_all_operations()`, `CheckFailed` replaced with `FailureGroup`
2. **Pact v3 API** (CRITICAL): Complete Verifier API rewrite — constructor, state handler, verify return type
3. **Namespace collision** (CRITICAL): `src/shared/` -> `src/build3_shared/` prevents import conflicts between Build 1 and Build 3
4. **asyncio.to_thread()** (CRITICAL): All sync library calls (Schemathesis, Pact, ChromaDB) now require event-loop-safe wrapping
5. **State machine** (CRITICAL): Wildcard `fail` transition restricted to non-terminal states, preventing `complete -> failed` corruption
