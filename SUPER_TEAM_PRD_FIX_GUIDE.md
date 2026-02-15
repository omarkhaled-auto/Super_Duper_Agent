# SUPER AGENT TEAM PRD Fix Guide: 936/1000 -> 1000/1000

All issues identified across Build 1, Build 2, Build 3, and Run 4 PRDs.
Total issues: 19 (5 in Build 1, 3 in Build 2, 7 in Build 3, 5 in Run 4).
5 Moderate severity, 14 Minor. None are architectural blockers.

---

## Build 1: Foundation Services — 5 Fixes (+28 points)

### B1-01: tree-sitter Version Cross-Reference (MINOR, -3 Technicality)
**Problem:** REQ-043 uses QueryCursor(query) and cursor.captures(root_node) returning dict[str, list[Node]]. This API is correct for tree-sitter 0.25.x but changed between 0.22 and 0.25. The PRD lists tree-sitter 0.25.2 in the tech stack table but REQ-043 does not reference this version constraint.
**Fix:** In REQ-043, add a note after the API usage: "Note: This API requires tree-sitter >= 0.25.0 (pinned in tech stack as 0.25.2). The captures() return type changed from list[tuple] to dict[str, list[Node]] in 0.25.0."

### B1-02: M5/M6 Cross-Milestone ChromaDB Dependency (MINOR, -5 Implementation)
**Problem:** Milestone 5 (IncrementalIndexer, REQ-055) calls semantic_indexer.index_symbols() which lives in Milestone 6 (SemanticIndexer using ChromaDB). An agent implementing M5 will encounter an undefined dependency.
**Fix:** Add to M5's description: "The IncrementalIndexer references SemanticIndexer.index_symbols() which is implemented in M6. During M5 implementation, stub this call with a no-op that logs 'SemanticIndexer not yet available — skipping semantic indexing.' The stub is replaced when M6 is implemented. Alternatively, merge M5 and M6 into a single milestone if the agent-team prompt supports it."

### B1-03: Milestone Count Header (MINOR, -5 Accuracy)
**Problem:** The PRD header states 8 milestones but the document shows M1 through M7. The milestone numbering is consistent (M1-M7 are all present) but the count in the header is wrong, or M8 is missing.
**Fix:** Verify milestone count and update the header to match. If there are 7 milestones, change the header to "7 milestones". If M8 (integration testing) was intended, add it explicitly.

### B1-04: ServiceInterfaceExtractor Regex Patterns (MINOR, -7 Implementation)
**Problem:** REQ-056's ServiceInterfaceExtractor.extract() describes route detection as "looking for route decorator patterns per language" in natural language. Compare to Build 3's REQ-034 which gives exact regex. An agent will have to invent detection logic.
**Fix:** Add concrete patterns to REQ-056:
- Python/FastAPI: `@app\.(get|post|put|delete|patch)\(['"]([^'"]+)`
- Express/Node: `router\.(get|post|put|delete|patch)\(['"]([^'"]+)`
- Spring/Java: `@(Get|Post|Put|Delete|Patch)Mapping\(['"]?([^'"\)]+)`
- .NET: `\[Http(Get|Post|Put|Delete|Patch)\(['"]?([^'"\]]+)`
Or specify tree-sitter queries for each language if tree-sitter is available at this stage.

### B1-05: Async/Sync Boundary Top-Level Rule (MINOR, -8 Agent-Readiness)
**Problem:** The async/sync boundary (TECH-035/036) is scattered across individual requirements. Agents need one clear, top-level architectural rule rather than discovering it piecemeal.
**Fix:** Add a new top-level section after the Tech Stack table titled "Architectural Principle: Async/Sync Boundary" containing:
"Rule: All FastAPI endpoint handlers are async. All database operations (SQLAlchemy), ChromaDB operations, and file I/O are synchronous. Every synchronous call from an async context MUST be wrapped in asyncio.to_thread(). A bare synchronous call inside an async handler will block the entire event loop. This applies to: ChromaDB collection.add()/query()/get(), SQLAlchemy session.execute()/commit(), and any open()/pathlib.Path.read_text() on large files."
Then mark TECH-035 and TECH-036 as "See Architectural Principle: Async/Sync Boundary" to avoid duplication.

---

## Build 2: Builder Fleet Upgrade — 3 Fixes (+10 points)

### B2-01: Contract Engine Tool Count Clarification (MINOR, -5 Technicality)
**Problem:** Build 2's M2 description and REQ-017 say "6 tools" but Build 1's M7 (REQ-059) exposes 9 MCP tools. Build 2 intentionally wraps only 6 (the other 3 are consumed by Build 3 directly). But the discrepancy is confusing.
**Fix:** In M2's description, change "6 tools" to: "wraps 6 of 9 Contract Engine MCP tools (get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts). The remaining 3 tools (create_contract, validate_spec, list_contracts) are consumed directly by Build 3's Integrator."

### B2-02: Filename Inconsistency (MINOR, -2 Accuracy)
**Problem:** INT-003 references mcp_clients.py (plural) but the project structure shows mcp_client.py (singular).
**Fix:** Search Build 2 PRD for all occurrences of mcp_clients.py and mcp_client.py. Pick one canonical name and make it consistent everywhere. Recommendation: use mcp_clients.py (plural) since it contains multiple client classes.

### B2-03: 'Validation Only' Mode Definition (MINOR, -3 Completeness)
**Problem:** The depth gating table shows contract_engine.enabled = True (validation only) for standard depth, but there's no mechanism for "validation only" mode.
**Fix:** Add a footnote to the depth gating table: "'Validation only' means contract_engine.enabled = true, contract_engine.validation_on_build = true, contract_engine.test_generation = false. This validates contracts exist and match endpoints but does not auto-generate test files from contract definitions."

---

## Build 3: Integrator + Quality Gate + Super Orchestrator — 7 Fixes (+90 points)

### B3-01: Pact Native Library Installation (MODERATE, -8 Technicality)
**Problem:** pact-python 3.x uses pact_ffi (Rust-based shared library). pip install pact-python auto-downloads the FFI on standard Debian/Ubuntu. But on Alpine Linux or ARM, this fails silently. The PRD doesn't specify the Docker base image constraint.
**Fix:** Add a new TECH requirement (e.g., TECH-015): "All Docker images for Build 3 services and test runners MUST use a Debian-based Python image (e.g., python:3.12-slim-bookworm), NOT Alpine."

### B3-02: Builder Config Generation Glue Code (MODERATE, -8 Implementation)
**Problem:** REQ-048 (run_parallel_builders) consumes builder_configs and REQ-049 (generate_builder_config) creates a single config. The iteration logic is implicit.
**Fix:** Add a new REQ (e.g., REQ-049a) or expand REQ-048 preamble with the iteration pattern: `builder_configs = [generate_builder_config(svc, contracts, codebase_context) for svc in service_map.services]`

### B3-03: Default Dockerfile Template (MODERATE, -10 Completeness)
**Problem:** REQ-015 says "If no Dockerfile exists, generate a default Python Dockerfile based on ServiceInfo.stack" but does not specify the template.
**Fix:** Add default templates per stack to REQ-015 (Python/FastAPI with python:3.12-slim-bookworm, Node/Express with node:20-slim). Key constraint: base image MUST be Debian-based (see B3-01).

### B3-04: Adversarial Scanner File Walking (MINOR, -6 Implementation)
**Problem:** REQ-039 through REQ-042 specify regex patterns but describe file walking as "scan all .py/.ts/.js files excluding node_modules..." without specifying the walking mechanism.
**Fix:** Add to Layer 4 scanner section: "Use pathlib.Path.rglob() for file discovery with EXCLUDE_DIRS set. Do NOT use os.walk()."

### B3-05: M2/M3 Parallelizability (MODERATE, -8 Agent-Readiness)
**Problem:** M2 and M3 both depend only on M1 and can run in parallel, but neither milestone header states this.
**Fix:** In M2's header, add: "Parallel with: M3". In M3's header, add: "Parallel with: M2".

### B3-06: CLI Command Count (MINOR, -5 Accuracy)
**Problem:** REQ-054 says "8 commands" but earlier text says "6 commands". M6 description says "6 commands" but lists 8.
**Fix:** Standardize to: "8 CLI commands: init, plan, build, integrate, verify, run (6 pipeline commands) + status, resume (2 utility commands)."

### B3-07: pytest asyncio_mode Configuration (MINOR, -5 Completeness)
**Problem:** The tech stack mentions asyncio_mode = "auto" for pytest-asyncio but doesn't specify where this configuration goes.
**Fix:** Add TECH-028: pyproject.toml config with `asyncio_mode = "auto"` and `filterwarnings = ["ignore::DeprecationWarning"]`.

---

## Run 4: End-to-End Integration & Audit — 5 Fixes (+65 points)

### R4-01: Contract Engine 9-Tool Verification (MINOR, -5 Technicality)
**Problem:** The SVC wiring map shows Contract Engine with 6 client methods (SVC-005 through SVC-010). But Build 1 exposes 9 tools total. The 3 unwrapped tools are consumed by Build 3 directly. Run 4 should verify all 9 are callable.
**Fix:** Add SVC-010a, SVC-010b, SVC-010c for create_contract, validate_spec, list_contracts consumed by Build 3 Integrator directly via MCP.

### R4-02: OpenAPI Endpoint Precondition (MINOR, -5 Implementation)
**Problem:** REQ-026 Phase 6 runs Schemathesis against /openapi.json. FastAPI exposes this by default, but it's an undocumented assumption.
**Fix:** Add a precondition to REQ-026 Phase 6 and a verification in Run 4's M2: "Before running Schemathesis, verify each service responds to GET /openapi.json with HTTP 200."

### R4-03: Test Matrix Traceability (MINOR, -5 Completeness)
**Problem:** The 57-test reference matrix doesn't map to the 18 TEST-xxx items in the milestones.
**Fix:** Add a traceability column (Maps To, Milestone, Priority) to the 57-test matrix ensuring bidirectional coverage.

### R4-04: Directory Structure Guidance (MINOR, -5 Agent-Readiness)
**Problem:** Run 4 is described as "NOT a build" but has ~5K LOC of infrastructure. No directory structure guidance.
**Fix:** Add directory structure section: src/run4/{config, wiring, audit, fixtures} + tests/run4/{test files}.

### R4-05: SVC DTO Field Name Reconciliation (MODERATE, -10 Accuracy)
**Problem:** Run 4's SVC wiring map uses field names that diverge from Build 1's actual REQ specs (e.g., SVC-001 shows contract_stubs but Build 1's REQ-020 returns contracts).
**Fix:** Reconcile every SVC entry (SVC-001 through SVC-017) against the source Build PRD field-by-field. The Run 4 SVC map must be a MIRROR of the Build PRD specs.

---

## Cross-PRD Interface Verification (Post-Fix)

| Interface | Build 1 | Build 2 | Build 3 | Run 4 | Status |
|-----------|---------|---------|---------|-------|--------|
| Architect MCP (4 tools) | M2+M7 | INT-003 | REQ-046 | SVC-001..004 | Fix R4-05 |
| Contract Engine MCP (9 tools) | M3+M4+M7 | M2 (6/9) | REQ-047 (3/9) | SVC-005..010 | Fix B2-01, R4-01 |
| Codebase Intel MCP (7 tools) | M5+M6 | M3 (7/7) | N/A | SVC-011..017 | CLEAN |
| Builder subprocess + STATE.json | N/A | RunState | REQ-048 | REQ-017 | CLEAN |
| Config.yaml compatibility | N/A | _dict_to_config() | REQ-049 | REQ-018 | CLEAN |
| Docker Compose merge | compose | N/A | REQ-015 | TECH-004 | Fix B3-03 |
