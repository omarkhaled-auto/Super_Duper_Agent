# Build 3 PRD Executability Review

> **Reviewer**: Agent-Team Executability Reviewer
> **PRD**: `prompts/BUILD3_PRD.md` (531 lines, 7 milestones)
> **References**: BUILD3_CODEBASE_RESEARCH.md, BUILD1_PRD.md, BUILD2_PRD.md
> **Date**: 2026-02-14

---

## Executive Summary

Build 3 PRD is **70-75% execution-ready**. The foundation (M1), quality gate (M4), CLI (M6), and E2E (M7) milestones are well-specified. However, there are **14 vague/ambiguous requirements**, **1 MCP/static analysis ambiguity** affecting 3 SVCs, and a **low test requirement count** compared to Build 1/2. The PRD needs targeted fixes before agent-team v14.0 can reliably execute it.

**Verdict**: NEEDS REVISION before execution.

---

## 1. Requirement Count Comparison

| Metric | Build 1 | Build 2 | Build 3 | Concern? |
|--------|---------|---------|---------|----------|
| Lines | 678 | 588 | 531 | Build 3 is shortest but most complex |
| Milestones | 8 | 6 | 7 | OK |
| REQ-xxx | 73 | 85 | 60 | LOW - 18% fewer than Build 1 |
| TECH-xxx | 34 | 43 | 29 | LOW |
| WIRE-xxx | 24 | 17 | 19 | OK |
| TEST-xxx | 41 | 94 | 24 | CRITICALLY LOW - 42% of Build 1, 26% of Build 2 |
| SVC-xxx | 12 | 13 | 19 | Good coverage |
| INT-xxx | 6 | 20 | 6 | LOW - Build 2 had 20 |
| SEC-xxx | 0 | 3 | 4 | OK |
| **Total items** | **172** | **239** | **161** | LOW for the most complex build |

**Key finding**: Build 3 has the fewest TEST-xxx requirements of all three builds despite being the most architecturally complex. Agent-team relies on TEST-xxx to gate milestone completion.

---

## 2. Parser Compatibility Check

All items PASS:

- [x] Milestone headers use `## Milestone N:` format (h2)
- [x] Requirement prefixes: REQ-NNN, TECH-NNN, WIRE-NNN, TEST-NNN, INT-NNN, SEC-NNN, SVC-NNN (all with dash + 3 digits)
- [x] `(review_cycles: N)` suffix on every requirement
- [x] Structured milestone metadata: ID, Status, Dependencies, Description
- [x] No nested tables or HTML
- [x] Global numbering (REQ-001 through REQ-060, not restarting per milestone)
- [x] Status Registry section present
- [x] Technology Stack section before milestones
- [x] Project Structure section present
- [x] SVC tables have both table format AND checklist items

---

## 3. SVC Table Completeness

| SVC-ID | Has Field Schema? | Issue |
|--------|-------------------|-------|
| SVC-001 | Yes `{ service_name: string, openapi_url: string, base_url: string }` | OK |
| SVC-002 | Yes | OK |
| SVC-003 | Yes | OK |
| SVC-004 | Yes | **AMBIGUOUS** - References MCP Codebase Intelligence, but AdversarialScanner is a static scanner |
| SVC-005 | Yes | **AMBIGUOUS** - Same issue |
| SVC-006 | Yes | **AMBIGUOUS** - Same issue |
| SVC-007 | Yes | OK (Internal) |
| SVC-008 | Yes | OK |
| SVC-009 | Yes | OK |
| SVC-010 | Yes | OK |
| SVC-011 | Yes | OK |
| SVC-012 | Yes | OK |
| SVC-013 | Yes | OK |
| SVC-014 | Yes | OK |
| SVC-015 | Yes | OK |
| SVC-016 | Yes | OK |
| SVC-017 | Yes | OK |
| SVC-018 | Yes | OK |
| SVC-019 | Yes | OK |

**Missing SVC entries**: None. All API calls have corresponding SVC entries.

**Ambiguous SVC entries (SVC-004/005/006)**: These reference Build 1's Codebase Intelligence MCP tools, but the AdversarialScanner (REQ-028) is described as a static scanner in the quality gate layer. The PRD does not specify:
1. Does the scanner require a running MCP server?
2. What is the fallback when Build 1 is not available?
3. How do tests mock these MCP calls?

---

## 4. Flagged Vague Requirements (14 Issues)

### SEVERITY: CRITICAL (3 issues)

#### VAGUE-1: REQ-012 — Schemathesis API pattern mismatch
**Problem**: REQ-012 says "generates test cases with `@schema.parametrize()` pattern, calls `case.call_and_validate(base_url=base_url)`" — but `@schema.parametrize()` is a pytest decorator pattern for test files, not a programmatic API pattern. The `run_against_service()` method is async and runs programmatically. These are two different usage modes. The agent will be confused about whether to generate test files or run tests programmatically.

**Fix**: Clarify that `run_against_service()` uses the programmatic API: `for test_case in schema.get_all_tests(): response = test_case.call(base_url=base_url); test_case.validate_response(response)`. Reserve `@schema.parametrize()` for `generate_test_file()` only.

#### VAGUE-2: REQ-017 — Chain detection algorithm unspecified
**Problem**: "finding chains where one service's response feeds into another service's request" has NO algorithm specified. How does the generator match response schemas to request schemas? By field name overlap? By explicit contract reference? By type matching? Without this, the agent will invent an algorithm that may not match expectations.

**Fix**: Add explicit algorithm: "Match chains by: (1) scan all contracts for endpoint pairs where Service A's response schema contains fields that match Service B's request schema field names AND types, (2) a field match requires exact name match (case-insensitive) and compatible type (string matches string, int matches int/number), (3) require at least 2 matching fields for a chain link, (4) sort flows by chain length descending."

#### VAGUE-3: REQ-028 — Adversarial scanner detection patterns unspecified
**Problem**: REQ-028 describes 6 detection methods (ADV-001 through ADV-006) at a HIGH level without specifying the regex patterns or algorithms. Compare to Build 1's REQ-024 which lists every SEC-xxx code with EXACT patterns (e.g., SEC-SECRET-001 `AKIA[0-9A-Z]{16}`). Build 3 just says "scan for publish/emit calls" without specifying what patterns to match.

Also, SVC-004/005/006 indicate MCP calls to Codebase Intelligence, but the quality gate should work without Build 1 running. This creates a hard dependency that contradicts M7 INT-006 ("All Build 3 modules must be importable without Build 1 or Build 2 installed").

**Fix**: For each ADV-xxx, specify the exact regex patterns:
- ADV-001: `r"(?:publish|emit|dispatch|send_event)\s*\(\s*['\"](\w+)['\"]"` for publishers, `r"(?:subscribe|on|addEventListener|consume)\s*\(\s*['\"](\w+)['\"]"` for consumers
- ADV-002: Scan contract registry files for contract IDs, then `glob('**/services/**/*.{py,ts,cs}')` for implementation files containing the contract's endpoint paths
- ADV-003: Scan for service directories containing no HTTP client/server imports and no event publish/subscribe patterns
- ADV-004: `r'\b([a-z]+(?:[A-Z][a-z]*)+)\b'` for camelCase in API payloads, `r'\b([a-z]+(?:_[a-z]+)+)\b'` for snake_case — flag services using mixed conventions
- ADV-005: `r'async\s+(?:def|function)\s+\w+\s*\([^)]*\)\s*(?:->|\{|:)(?:(?!try|except|catch).)*$'` for async without error handling
- ADV-006: `r'(?:global\s+\w+|^[A-Z_]+\s*=\s*(?:\[|\{|dict|list)).*(?:async\s+def|await)'` for shared mutable state in async

Also: Remove SVC-004/005/006 MCP dependency. Make AdversarialScanner purely static (regex-based). Build 1 MCP should be optional enhancement, not required.

### SEVERITY: HIGH (5 issues)

#### VAGUE-4: REQ-013 — Pact-python API version ambiguity
**Problem**: "using pact-python Verifier to verify provider satisfies consumer expectations" — pact-python 3.x has a significantly different API from 2.x. The PRD specifies `pact-python 3.2.1+` in tech stack but REQ-013 uses `pact.Verifier()` which is the 2.x API. The 3.x API uses `pact.v3.Verifier` with different methods.

**Fix**: Specify exact import and method chain: `from pact.v3.verifier import Verifier; verifier = Verifier().set_info("Provider", url=provider_url); verifier.add_source(str(pact_file)); result = verifier.verify(); if not result.success: # extract failures`

#### VAGUE-5: REQ-015 — Fix loop subprocess command undefined
**Problem**: "launches a targeted agent-team fix pass (subprocess) against the builder directory, returns cost in USD" — does not specify the exact subprocess command, arguments, or how cost is extracted from the subprocess output.

**Fix**: Specify: `asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", str(builder_dir), "--depth", "quick", "--fix-instructions", str(fix_instructions_path))`. Cost extracted by parsing `STATE.json` from the builder directory after subprocess completes: `json.loads((builder_dir / ".agent-team" / "STATE.json").read_text())["total_cost"]`.

#### VAGUE-6: REQ-019 — Data flow tracer assumptions
**Problem**: `trace_request()` "traces its propagation through downstream services by examining response headers for trace IDs" — this assumes services are instrumented with OpenTelemetry trace propagation. If they are not (which is likely for freshly built services), the tracer will find nothing. Also, `expected_transformations` parameter format is undefined.

**Fix**: Add: "If no traceparent header is present in the response, fall back to: (1) inspect response body for `trace_id` or `request_id` fields, (2) if none found, return a single-hop trace containing only the entry service response." Define `expected_transformations` format: `[{"hop": 1, "field": "user_id", "from_type": "string", "to_type": "integer"}, ...]`

#### VAGUE-7: REQ-032 — MCP client pattern unspecified
**Problem**: `run_architect_phase()` "invokes the Build 1 Architect via MCP stdio (using subprocess with `python -m src.architect.mcp_server`)" — but it doesn't specify whether to use the MCP Python SDK's `stdio_client()` + `ClientSession` pattern (like Build 2 does) or raw subprocess with JSON. Build 2's research doc specifies the exact pattern but Build 3's requirement doesn't.

**Fix**: Add: "Use MCP SDK pattern: `async with stdio_client(StdioServerParameters(command='python', args=['-m', 'src.architect.mcp_server'])) as (read, write): async with ClientSession(read, write) as session: await session.initialize(); result = await session.call_tool('decompose', {'prd_text': prd_content})`. Fall back to subprocess + JSON if MCP SDK import fails."

#### VAGUE-8: REQ-039 — Error handling per transition
**Problem**: `execute_pipeline()` lists the transition chain but doesn't specify error handling for each transition. What happens if `contracts_ready` fails (some contracts invalid)? If `builders_done` has 1 of 3 builders failed? If `integration_done` has partial results?

**Fix**: Add per-transition error policy:
- `start_architect` fails -> retry up to `config.architect.max_retries` times, then transition to `failed`
- `contracts_ready` fails -> log warning, proceed with available contracts (partial is OK)
- `builders_done` with partial failure -> proceed if at least 1 builder succeeded, transition to `failed` if all failed
- `integration_done` with partial health -> proceed to quality_gate (partial results are evaluated there)
- `quality_failed` -> enter fix loop (already specified)

### SEVERITY: MEDIUM (4 issues)

#### VAGUE-9: REQ-046 — Service entry Dockerfile template
**Problem**: ComposeGenerator.generate() says "one service entry per successfully built service (with build context, healthcheck, Traefik labels for routing, depends_on postgres with service_healthy)" — but doesn't specify the Dockerfile template for user services. Are Dockerfiles expected to already exist in builder output dirs? Or should the generator create them?

**Fix**: Add: "Each service entry uses `build: {context: builder_result.output_dir}` assuming the builder has created a Dockerfile in its output directory. If no Dockerfile exists, generate a default Python/Node.js Dockerfile based on the service's stack from ServiceInfo.stack."

#### VAGUE-10: REQ-020 — Boundary tester scope
**Problem**: `run_all_boundary_tests(contracts: list[dict])` — the `contracts` parameter format is not defined. Is it the same as ContractViolation? Is it the OpenAPI spec? What fields does each dict have?

**Fix**: Add: "Each contract dict must contain: `service_name: str`, `endpoint: str` (path), `method: str` (HTTP verb), `request_schema: dict` (JSON Schema for request body), `response_schema: dict` (JSON Schema for response body). These are extracted from the contract registry's OpenAPI specs."

#### VAGUE-11: REQ-035 — generate_builder_config output format
**Problem**: Returns "a scoped config.yaml dict" — but what format? Is it agent-team config.yaml format? Does it include PRD path? Requirements path?

**Fix**: Add: "Returns a dict matching agent-team config.yaml format: `{'depth': config.builder.depth, 'milestone': {'enabled': True, 'health_gate': True}, 'e2e_testing': {'enabled': True, 'backend_api_tests': True}, 'post_orchestration_scans': {'mock_data_scan': True, 'api_contract_scan': True}}`. The dict is written to `{builder_output_dir}/config.yaml` by the caller."

#### VAGUE-12: REQ-034 — run_parallel_builders builder_configs format
**Problem**: `builder_configs: list[dict]` — what fields does each dict have? How does it map to ServiceInfo?

**Fix**: Add: "Each builder_config dict contains: `service_id: str`, `service_info: ServiceInfo`, `prd_content: str` (service-specific PRD section), `contracts_path: Path` (service's contracts), `output_dir: Path` (where builder writes output), `config: dict` (from generate_builder_config())."

### SEVERITY: LOW (2 issues)

#### VAGUE-13: REQ-045 — Rich display function coverage
**Problem**: 7 display functions listed without specifying the exact Rich widgets used for each. The agent might use Table when Panel is expected, or vice versa.

**Fix**: Add specific Rich types: `print_pipeline_header` -> `Panel(title="Pipeline Overview")`, `print_phase_table` -> `Table(title="Phase Status")`, `print_builder_table` -> `Table(title="Builder Status")`, `print_quality_summary` -> `Panel(Group(Table(...)))`, `print_error_panel` -> `Panel(style="red")`.

#### VAGUE-14: TECH-028 — Traefik backtick syntax example
**Problem**: The backtick syntax example shows `` PathPrefix(`/api/service`) `` but the actual label key format is not shown.

**Fix**: Show the full label: `traefik.http.routers.{service}.rule=PathPrefix(\`/api/{service}\`)`. Note: in Python code, use f-string with escaped backticks or string concatenation.

---

## 5. Test Requirement Executability

| TEST-ID | File Specified? | What to Test? | Expected Outcomes? | Min Cases? |
|---------|-----------------|---------------|-------------------|------------|
| TEST-001 | Yes | Yes (all 13 transitions) | Yes | 20 |
| TEST-002 | Yes | Yes (state persistence) | Yes | 10 |
| TEST-003 | Yes | Yes (cost tracking) | Yes | 8 |
| TEST-004 | Yes | Yes (config defaults) | Yes | 12 |
| TEST-005 | Yes | Yes (conftest fixtures) | Yes | 6 fixtures |
| TEST-006 | Yes | Yes (contract compliance) | Yes | 15 |
| TEST-007 | Yes | Yes (mocked HTTP) | Yes | 10 |
| TEST-008 | Yes | Yes (flow tests) | Yes | 10 |
| TEST-009 | Yes | Yes (mocked runner) | Yes | 10 |
| TEST-010 | Yes | Yes (boundary tests) | Yes | 8 |
| TEST-011 | Yes | Yes (gate engine) | Yes | 15 |
| TEST-012 | Yes | Yes (security scanner) | Yes | 20 |
| TEST-013 | Yes | Yes (observability) | Yes | 10 |
| TEST-014 | Yes | Yes (docker security) | Yes | 12 |
| TEST-015 | Yes | Yes (adversarial) | Yes | 12 |
| TEST-016 | Yes | Yes (pipeline functions) | Yes | 20 |
| TEST-017 | Yes | Yes (budget/shutdown/resume) | Yes | 10 |
| TEST-018 | Yes | Yes (CLI commands) | Yes | 12 |
| TEST-019 | Yes | Yes (docker orchestrator) | Yes | 10 |
| TEST-020 | Yes | Yes (compose generator) | Yes | 10 |
| TEST-021 | Yes | Yes (E2E full pipeline) | Yes | 15 |
| TEST-022 | Yes | Yes (resume scenarios) | Yes | 4 |
| TEST-023 | Yes | Yes (error scenarios) | Yes | 4 |
| TEST-024 | Yes | Yes (scan code coverage) | Yes | 5 |

All 24 TEST-xxx requirements are well-specified individually. The issue is COUNT, not QUALITY.

**Missing test areas** (compared to Build 1/2 patterns):
- No dedicated test for `TraefikConfigGenerator` (REQ-047)
- No dedicated test for `ServiceDiscovery` (REQ-049)
- No dedicated test for `ComposeGenerator` output YAML validity (only tested via TEST-020 which combines with docker orchestrator)
- No test for `GracefulShutdown` signal handler installation (only integration-level in TEST-017)
- No test for `generate_integration_report()` (REQ-016)
- No test for `ScanAggregator` deduplication logic (REQ-030)

---

## 6. Milestone Executability

| Milestone | Can Execute in Single Agent Run? | External Service Deps? | File Conflicts? |
|-----------|----------------------------------|----------------------|-----------------|
| M1 | YES - Pure data models + state machine | None | None |
| M2 | YES - Contract verification (mocked) | None (tests mock schemathesis/pact) | None |
| M3 | YES - Cross-service tests (mocked) | None (tests mock HTTP) | None |
| M4 | YES - Quality gate (static scanning) | **CONCERN**: SVC-004/005/006 reference MCP | None |
| M5 | YES - Pipeline (all calls mocked) | None (tests mock subprocess/MCP) | None |
| M6 | YES - CLI + Docker (mocked) | None (tests mock docker commands) | None |
| M7 | YES - E2E tests (all mocked) | None | None |

**M4 Concern**: REQ-028 AdversarialScanner references Build 1 Codebase Intelligence MCP tools via SVC-004/005/006, but M4 is supposed to be executable without running services. The agent will try to import or call these MCP tools and fail. **This must be clarified**: make AdversarialScanner purely static, or add explicit try/except with regex fallback.

---

## 7. Comparison with Build 1/2 Specificity

### Areas where Build 3 is LESS specific than Build 1:

1. **Security scanner patterns**: Build 1 REQ-024 defines 12 SECRET codes with regex patterns inline. Build 3 REQ-024 lists the same codes but says "using regex patterns for AWS keys, private keys..." without the actual patterns. Agent must invent them.

2. **Adversarial scanner**: Build 3 REQ-028 has NO regex patterns for any of the 6 ADV codes. Build 1 always provided detection algorithms for its scan codes.

3. **Test count**: Build 1 had 41 TEST-xxx; Build 3 has 24. Several modules lack dedicated test requirements.

### Areas where Build 3 is EQUALLY specific as Build 1:

1. **Data models** (REQ-001): Exhaustively detailed with every field, type, and default. Matches Build 1 REQ-002/003/004 quality.
2. **State machine** (REQ-008): All 11 states and 13 transitions specified. Comparable to Build 1's state machine definitions.
3. **Config dataclasses** (REQ-005): All nested dataclasses with defaults specified. Matches Build 1 REQ-008.

### Areas where Build 3 is MORE specific than Build 2:

1. **SVC tables**: Build 3 has 19 SVC entries vs Build 2's 13, all with field schemas.
2. **Status Registry**: Build 3 includes one; Build 2 did not.

---

## 8. Specific Rewrites for Top 10 Issues

### Rewrite 1: REQ-012 (CRITICAL — Schemathesis API)

**Current** (truncated):
> `async run_against_service(self, service_name: str, openapi_url: str, base_url: str, max_examples: int = 50) -> list[ContractViolation]` that uses `schemathesis.openapi.from_url(openapi_url)` to load schema, generates test cases with `@schema.parametrize()` pattern, calls `case.call_and_validate(base_url=base_url)` for each case

**Rewrite**:
> `async run_against_service(self, service_name: str, openapi_url: str, base_url: str, max_examples: int = 50) -> list[ContractViolation]` that uses `schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)` to load schema, then iterates test cases programmatically via `for endpoint in schema.get_all_endpoints(): for case in endpoint.make_case(): response = case.call(); try: case.validate_response(response) except schemathesis.failures.FailureGroup as fg: for failure in fg.failures: violations.append(...)`. Catches `schemathesis.failures.FailureGroup` and extracts individual `Failure` objects. The `@schema.parametrize()` decorator pattern is used ONLY in `generate_test_file()` for producing runnable pytest files, not in programmatic execution.

### Rewrite 2: REQ-017 (CRITICAL — Chain detection algorithm)

**Current** (truncated):
> `generate_flow_tests(self) -> list[dict]` that analyzes contracts to identify multi-service request flows (e.g., create-user -> create-order -> process-payment) by finding chains where one service's response feeds into another service's request

**Rewrite**:
> `generate_flow_tests(self) -> list[dict]` that analyzes contracts to identify multi-service request flows using the following deterministic algorithm: (1) For each OpenAPI contract, extract all POST endpoint response schemas and all non-POST endpoint request schemas. (2) For each pair (Service A POST response, Service B request), compute field overlap by counting fields with matching names (case-insensitive) and compatible types (string=string, integer=number, object=object). (3) If field overlap >= 2, create a chain link from A to B. (4) Build a directed graph of chain links using NetworkX DiGraph. (5) Find all simple paths of length 2+ using `nx.all_simple_paths(G, cutoff=5)`. (6) For each path, create a flow dict with flow_id = f"flow_{hash}", steps list where each step has service, method, path, request_template (from schema), expected_status (200/201). (7) Sort flows by path length descending, return top 20.

### Rewrite 3: REQ-028 (CRITICAL — Adversarial patterns)

**Current** (truncated):
> `detect_dead_events(self) -> list[ScanViolation]` finding ADV-001 (events published but never consumed — scan for publish/emit calls and subscribe/on handlers with matching event names)

**Rewrite**:
> `detect_dead_events(self) -> list[ScanViolation]` finding ADV-001 using compiled regex patterns: publisher pattern `_RE_EVENT_PUBLISH = re.compile(r"(?:publish|emit|dispatch|send_event|fire)\s*\(\s*['\"](\w+)['\"]")`, consumer pattern `_RE_EVENT_SUBSCRIBE = re.compile(r"(?:subscribe|on|addEventListener|consume|handle|listen)\s*\(\s*['\"](\w+)['\"]")`. Scan all .py/.ts/.js/.cs files (excluding node_modules, .venv, __pycache__, dist, build). Collect all published event names and all consumed event names. Report ADV-001 for each event name that appears in publishers but not consumers.
>
> `detect_dead_contracts(self) -> list[ScanViolation]` finding ADV-002 by scanning contract registry directory (contracts/, .contracts/, pacts/) for JSON/YAML contract files, extracting endpoint paths from OpenAPI `paths` keys, then searching project files for route decorators matching those paths using `_RE_ROUTE_PATH = re.compile(r"(?:@(?:app|router)\.\w+|Route|HttpGet|HttpPost|HandleFunc)\s*\(\s*['\"]([^'\"]+)['\"]")`. Report ADV-002 for paths in contracts with no matching route.
>
> `detect_orphan_services(self) -> list[ScanViolation]` finding ADV-003 by scanning for service directories (directories containing Dockerfile or package.json or pyproject.toml), then checking each for HTTP client imports (`_RE_HTTP_CLIENT = re.compile(r"(?:httpx|requests|fetch|axios|HttpClient)")`) and HTTP server imports (`_RE_HTTP_SERVER = re.compile(r"(?:FastAPI|Express|app\.listen|WebApplication)")`). Report ADV-003 for directories with no HTTP client AND no HTTP server AND no event publish/subscribe patterns.
>
> `check_naming_consistency(self) -> list[ScanViolation]` finding ADV-004 by scanning API response/request handler files for JSON field naming. Extract field names from response dicts/objects using `_RE_JSON_FIELD = re.compile(r"['\"](\w+)['\"]\s*:")`. Classify each as camelCase (matches `[a-z]+(?:[A-Z][a-z]*)+`), snake_case (matches `[a-z]+(?:_[a-z]+)+`), or other. Report ADV-004 for services using mixed conventions (both camelCase and snake_case in >10% of fields each).
>
> `scan_error_handling(self) -> list[ScanViolation]` finding ADV-005 by scanning for `async def` or `async function` definitions followed by a body that does NOT contain `try` within the next 50 lines, AND for bare `except:` or `except Exception:` without re-raise. Use `_RE_ASYNC_DEF = re.compile(r"async\s+(?:def|function)\s+\w+")` and `_RE_BARE_EXCEPT = re.compile(r"except\s*(?:Exception\s*)?:")`. Report ADV-005 for each match.
>
> `scan_race_conditions(self) -> list[ScanViolation]` finding ADV-006 by scanning for module-level mutable assignments (`_RE_GLOBAL_MUTABLE = re.compile(r"^(\w+)\s*(?::\s*(?:list|dict|set|List|Dict|Set))?\s*=\s*(?:\[|\{|dict\(|list\(|set\()", re.MULTILINE)`) and then checking if the assigned variable name appears inside an `async def` body. Report ADV-006 for each global mutable variable modified in an async function.
>
> Remove SVC-004, SVC-005, SVC-006 from the SVC table. AdversarialScanner is purely static (regex-based). No MCP dependency.

### Rewrite 4: REQ-013 (HIGH — Pact API)

**Current** (truncated):
> `async verify_provider(self, provider_name: str, provider_url: str, pact_files: list[Path]) -> list[ContractViolation]` using pact-python Verifier to verify provider satisfies consumer expectations

**Rewrite**:
> `async verify_provider(self, provider_name: str, provider_url: str, pact_files: list[Path]) -> list[ContractViolation]` using `from pact.v3.verifier import Verifier`. Create verifier: `verifier = Verifier().set_info(provider_name, url=provider_url)`. Add each pact file: `for pf in pact_files: verifier.add_source(str(pf))`. Execute: `result = verifier.verify()`. If `not result.success`, parse `result.output` string for failed interaction lines (lines containing "Verifier output" with failure details), create ContractViolation for each with code "PACT-001" and the interaction description as message. If provider state setup fails (indicated by "state handler" in output), use code "PACT-002".

### Rewrite 5: REQ-015 (HIGH — Fix loop subprocess)

**Current** (truncated):
> `async feed_violations_to_builder(self, service_id: str, violations: list[ContractViolation], builder_dir: Path) -> float` that writes a FIX_INSTRUCTIONS.md file ... launches a targeted agent-team fix pass (subprocess) against the builder directory, returns cost in USD

**Rewrite**:
> `async feed_violations_to_builder(self, service_id: str, violations: list[ContractViolation], builder_dir: Path) -> float` that: (1) writes `{builder_dir}/FIX_INSTRUCTIONS.md` with categorized violations using `classify_violations()` output, formatted as markdown sections per severity, (2) launches subprocess: `proc = await asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", str(builder_dir), "--depth", "quick")` with `stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE`, (3) awaits completion with timeout `config.builder.timeout_per_builder`, (4) extracts cost from `{builder_dir}/.agent-team/STATE.json` by reading `json.loads(path.read_text(encoding='utf-8')).get('total_cost', 0.0)`, (5) returns cost as float. On timeout, kills subprocess and returns 0.0.

### Rewrite 6: REQ-019 (HIGH — Data flow tracer)

**Current** (truncated):
> `async trace_request(self, entry_service: str, method: str, path: str, body: dict) -> list[dict]` that sends a request to the entry service and traces its propagation through downstream services by examining response headers for trace IDs

**Rewrite**:
> `async trace_request(self, entry_service: str, method: str, path: str, body: dict) -> list[dict]` that: (1) generates a unique trace_id = str(uuid.uuid4()), (2) sends request to entry service URL with headers `{"traceparent": f"00-{trace_id}-0000000000000001-01"}` using httpx.AsyncClient, (3) records first hop as `{"service": entry_service, "status": response.status_code, "body": response.json(), "trace_id": trace_id}`, (4) if response contains `x-downstream-services` header or response body has `_trace` field, follow each downstream URL and record additional hops, (5) if NO trace headers are present in response, return single-hop trace list. Returns list of hop dicts.
>
> `verify_data_transformations(self, trace: list[dict], expected_transformations: list[dict]) -> list[str]` where each expected_transformation has format `{"hop_index": int, "field": str, "expected_type": str, "expected_value_pattern": str | None}`. Verifies that at each hop, the specified field exists with the expected type. Returns list of error message strings, empty if all transformations verified.

### Rewrite 7: REQ-032 (HIGH — MCP client pattern)

**Current** (truncated):
> `async run_architect_phase(prd_path, config, state, tracker) -> float` that invokes the Build 1 Architect via MCP stdio (using subprocess with `python -m src.architect.mcp_server`)

**Rewrite**:
> `async run_architect_phase(prd_path: Path, config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> float` that invokes the Build 1 Architect via MCP stdio. Uses: `from mcp import StdioServerParameters; from mcp.client.stdio import stdio_client; from mcp.client.session import ClientSession`. Creates session: `async with stdio_client(StdioServerParameters(command="python", args=["-m", "src.architect.mcp_server"], cwd=config.build1_services_dir)) as (read, write): async with ClientSession(read, write) as session: await session.initialize(); result = await session.call_tool("decompose", {"prd_text": prd_path.read_text(encoding="utf-8")})`. Extracts ServiceMap, DomainModel, contract_stubs from result JSON. Falls back to subprocess + JSON if MCP SDK import fails: `proc = await asyncio.create_subprocess_exec("python", "-m", "src.architect.mcp_server", stdin=PIPE, stdout=PIPE)`. Saves artifacts to state. Returns estimated cost 0.0 (MCP calls are free).

### Rewrite 8: REQ-039 (HIGH — Pipeline error handling)

Add after existing REQ-039 text:
> Error handling per transition: (a) `start_architect` raises PhaseTimeoutError -> retry up to `config.architect.max_retries`, then transition to `failed` with interrupt_reason. (b) `approve_architecture` -> if validation_issues non-empty AND config.architect.auto_approve is False, log warning and proceed (issues are advisory). (c) `contracts_ready` -> if some contracts fail validation, log warning and proceed with valid contracts only. (d) `builders_done` -> if all builders failed (all BuilderResult.success == False), transition to `failed`. If some failed, proceed with successful builders only. (e) `integration_done` -> proceed to quality_gate regardless of integration health (quality gate evaluates). (f) `quality_failed` -> enter fix loop bounded by `config.quality_gate.max_fix_retries`.

### Rewrite 9: REQ-024 (Provide example SEC-SECRET patterns)

Add to REQ-024 after "SEC-SECRET-001 through SEC-SECRET-012":
> Exact regex patterns: SEC-SECRET-001 `AKIA[0-9A-Z]{16}` (AWS key), SEC-SECRET-002 `-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----` (private key), SEC-SECRET-003 `(?:api[_-]?key|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]` (API key), SEC-SECRET-004 `(?:postgres|mysql|mongodb)://[^:]+:[^@]+@` (DB connection string), SEC-SECRET-005 `Bearer\s+[A-Za-z0-9\-._~+/]+=*` (bearer token), SEC-SECRET-006 `(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}['"]` (hardcoded password), SEC-SECRET-007 `gh[ps]_[A-Za-z0-9_]{36,}` (GitHub token), SEC-SECRET-008 `glpat-[A-Za-z0-9\-_]{20,}` (GitLab token), SEC-SECRET-009 `sk_(?:live|test)_[A-Za-z0-9]{24,}` (Stripe key), SEC-SECRET-010 `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` (hardcoded JWT), SEC-SECRET-011 `xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+` (Slack token), SEC-SECRET-012 `SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}` (SendGrid key).

### Rewrite 10: Missing test requirements

Add the following TEST requirements:

> - [ ] TEST-025: `tests/test_contract_compliance.py` -- test TraefikConfigGenerator.generate_labels produces correct Docker labels with PathPrefix backtick syntax, test generate_static_config produces valid YAML with Docker provider -- minimum 6 test cases (review_cycles: 0)
>
> - [ ] TEST-026: `tests/test_contract_compliance.py` -- test ServiceDiscovery.get_service_ports parses compose file correctly, test check_health with mocked healthy/unhealthy responses, test wait_all_healthy with mixed health states -- minimum 6 test cases (review_cycles: 0)
>
> - [ ] TEST-027: `tests/test_quality_gate.py` -- test ScanAggregator.aggregate computes correct overall_verdict (all passed -> PASSED, any failed -> FAILED, mixed -> PARTIAL), test deduplicate removes duplicate code+file_path+line combinations -- minimum 6 test cases (review_cycles: 0)
>
> - [ ] TEST-028: `tests/test_quality_gate.py` -- test generate_quality_gate_report produces markdown with all sections (Overall Verdict, Per-Layer Results, Blocking Violations, Advisory Findings, Fix History) -- minimum 4 test cases (review_cycles: 0)
>
> - [ ] TEST-029: `tests/test_pipeline.py` -- test generate_builder_config produces valid agent-team config.yaml dict with depth from global config, milestone enabled, e2e enabled -- minimum 5 test cases (review_cycles: 0)
>
> - [ ] TEST-030: `tests/test_docker_orchestrator.py` -- test generate_integration_report produces markdown with Summary, Per-Service, Violations, Recommendations sections -- minimum 4 test cases (review_cycles: 0)

---

## 9. Issue Summary

| Category | Count |
|----------|-------|
| Vague/ambiguous requirements | 14 |
| Missing SVC entries | 0 |
| Under-specified test requirements | 6 missing test areas |
| MCP vs static analysis ambiguity | 1 (affecting SVC-004/005/006) |
| Missing regex patterns | 2 (REQ-024 secrets, REQ-028 adversarial) |
| Missing algorithm specifications | 1 (REQ-017 chain detection) |
| API version ambiguity | 2 (REQ-012 schemathesis, REQ-013 pact) |

### Issues Ranked by Severity

| Rank | ID | Severity | Issue |
|------|-----|----------|-------|
| 1 | VAGUE-3 | CRITICAL | REQ-028 adversarial patterns — no regex, no algorithm, MCP dependency contradicts INT-006 |
| 2 | VAGUE-2 | CRITICAL | REQ-017 chain detection — no algorithm for matching schemas |
| 3 | VAGUE-1 | CRITICAL | REQ-012 schemathesis — programmatic vs decorator API confusion |
| 4 | VAGUE-4 | HIGH | REQ-013 pact-python 3.x vs 2.x API |
| 5 | VAGUE-5 | HIGH | REQ-015 fix loop subprocess command |
| 6 | VAGUE-6 | HIGH | REQ-019 data flow tracer assumptions |
| 7 | VAGUE-7 | HIGH | REQ-032 MCP client pattern |
| 8 | VAGUE-8 | HIGH | REQ-039 per-transition error handling |
| 9 | VAGUE-9 | MEDIUM | REQ-046 service Dockerfile template |
| 10 | VAGUE-10 | MEDIUM | REQ-020 boundary tester contract format |
| 11 | VAGUE-11 | MEDIUM | REQ-035 builder config output format |
| 12 | VAGUE-12 | MEDIUM | REQ-034 builder_configs dict format |
| 13 | VAGUE-13 | LOW | REQ-045 Rich widget types |
| 14 | VAGUE-14 | LOW | TECH-028 Traefik label format |

---

## 10. Recommendations

1. **Apply all 10 rewrites above** to bring the PRD to Build 1/2 specificity levels.
2. **Add 6 missing TEST requirements** (TEST-025 through TEST-030) to match Build 1's test coverage density.
3. **Remove SVC-004/005/006** and make AdversarialScanner purely static. Add MCP enhancement as optional future improvement.
4. **Add SEC-SECRET regex patterns** to REQ-024 (currently says "using regex patterns" without providing them).
5. **Clarify REQ-012/013** with exact import paths and method chains for schemathesis and pact-python 3.x.
6. **Add per-transition error policies** to REQ-039 execute_pipeline.

After these fixes, the PRD should be **95%+ execution-ready** for agent-team v14.0.
