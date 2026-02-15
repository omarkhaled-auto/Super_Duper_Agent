# PRD Fix Review Report

**Reviewer:** Review Agent
**Date:** 2026-02-15
**Scope:** Verify all 17 fixes (from 19 identified, 2 rejected) across 4 PRD files

## Executive Summary

| Category | Count |
|----------|-------|
| Fixes expected | 17 (13 confirmed + 4 modified) |
| PASS (correctly applied) | 2 |
| PARTIAL (applied but incomplete) | 2 |
| FAIL (not applied) | 13 |
| Rejected fixes correctly NOT applied | 2/2 |

**Overall Verdict: FAIL -- 13 of 17 fixes were not applied.**

Only Build 1 received partial attention (2 of 4 fixes applied). Build 2, Build 3, and Run 4 PRDs appear completely untouched by the fixer agent.

---

## Build 1: BUILD1_PRD.md -- 2 PASS, 2 FAIL

### B1-01: tree-sitter Version Cross-Reference
**Verdict: PASS**
**Evidence:** Line 426 in REQ-043 contains: "Note: This API requires tree-sitter >= 0.25.0 (pinned in tech stack as 0.25.2). The captures() return type changed from list[tuple] to dict[str, list[Node]] in 0.25.0, and QueryCursor was introduced in 0.25.0"
**Assessment:** Fix matches the guide specification exactly. Version constraint is documented, API change is noted.

### B1-02: M5/M6 Cross-Milestone ChromaDB Dependency
**Verdict: PASS**
**Evidence:** Line 421 in M5's description contains cross-milestone dependency text about SemanticIndexer.index_symbols() with stub guidance: "The IncrementalIndexer references SemanticIndexer.index_symbols() which is implemented in M6. During M5 implementation, stub this call with a no-op that logs 'SemanticIndexer not yet available -- skipping semantic indexing.'"
**Assessment:** Fix matches the guide specification. Stub guidance and alternative merge suggestion are present.

### B1-04: ServiceInterfaceExtractor Regex Patterns
**Verdict: FAIL**
**Evidence:** REQ-056 at line 473 still contains the original natural language pattern description ("Python: @app.get, @app.post... TypeScript: app.get(), router.get()...") without any supplementary regex patterns. No text containing "Optional", "MAY use these regex", or "supplementary" found.
**Research report said:** MODIFIED -- downgrade to optional supplementary note with concrete regex patterns.
**What was expected:** A note after the natural-language patterns saying something like "Optional: For consistency with Build 3's regex-based approach, agents MAY use these regex patterns: [Python/FastAPI, Express/Node, Spring/Java, .NET regex list]"
**What was found:** No change from original text.

### B1-05: Async/Sync Boundary Top-Level Rule
**Verdict: FAIL**
**Evidence:** No "Architectural Principle: Async/Sync Boundary" section found anywhere in BUILD1_PRD.md. TECH-035 (line 556) and TECH-036 (line 557) remain unchanged without any "See Architectural Principle" cross-reference.
**What was expected:** A new top-level section after the Tech Stack table titled "Architectural Principle: Async/Sync Boundary" with a consolidated rule about wrapping synchronous calls in asyncio.to_thread(), plus TECH-035/TECH-036 updated to cross-reference the new section.
**What was found:** No change from original text. The async/sync boundary rules remain scattered in individual TECH requirements.

---

## Build 2: BUILD2_PRD.md -- 0 PASS, 1 PARTIAL, 2 FAIL

### B2-01: Contract Engine Tool Count Clarification
**Verdict: FAIL**
**Evidence:** M2's description at line 134 still says "Build 1's Contract Engine (6 tools)" without any clarification about wrapping 6 of 9 tools. No text containing "wraps 6 of 9", "remaining 3 tools", or the explicit tool name list found.
**What was expected:** Change "6 tools" to "wraps 6 of 9 Contract Engine MCP tools (get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts). The remaining 3 tools (create_contract, validate_spec, list_contracts) are consumed directly by Build 3's Integrator."
**What was found:** No change from original text.

### B2-02: Filename Inconsistency
**Verdict: FAIL**
**Evidence:** The inconsistency remains:
- Line 27 (project structure): `mcp_client.py` (singular)
- Line 134 (M2 description): `mcp_client.py` (singular)
- Line 440 (INT-003): `mcp_clients.py` (plural)
**What was expected:** All occurrences unified to one canonical name (recommended: `mcp_clients.py` plural).
**What was found:** No change. The singular/plural inconsistency persists.

### B2-03: 'Validation Only' Mode Definition
**Verdict: PARTIAL**
**Evidence:**
- TECH-044 at line 396 contains "validation_on_build=True, test_generation=False" but does NOT include the modified fix text explaining what "validation only" means.
- The depth gating summary table at line 556 shows "True (validation only)" -- this label was already present in the original PRD.
**Research report said:** MODIFIED -- add "(this is 'validation only' mode: validates contracts exist and match endpoints but does not auto-generate test files)" to TECH-044 inline.
**What was expected:** The TECH-044 text modified to include the explanation: "contract_engine enabled (validation_on_build=True, test_generation=False -- this is 'validation only' mode: validates contracts exist and match endpoints but does not auto-generate test files)"
**What was found:** TECH-044 text is unchanged. The "validation only" label in the table at line 556 appears to have been there originally, not added by the fixer. No explanatory text added.

---

## Build 3: BUILD3_PRD.md -- 0 PASS, 1 PARTIAL, 6 FAIL

### B3-01: Pact Native Library Installation
**Verdict: FAIL**
**Evidence:** No text containing "Debian-based", "python:3.12-slim-bookworm", "SHOULD use", or any new TECH requirement about Docker base image constraints found anywhere in BUILD3_PRD.md.
**Research report said:** MODIFIED -- "All Docker images for Build 3 services and test runners SHOULD use a Debian-based Python image. Alpine/musl support for pact_ffi is experimental and may cause runtime issues."
**What was expected:** A new TECH requirement (e.g., TECH-015 or similar) specifying Debian-based Docker images.
**What was found:** No change from original text.

### B3-02: Builder Config Generation Glue Code
**Verdict: FAIL**
**Evidence:** No iteration pattern like `builder_configs = [generate_builder_config(svc, contracts, codebase_context) for svc in service_map.services]` found. REQ-048 at line 396 and REQ-049 at line 398 remain unchanged without a preamble showing the assembly step.
**What was expected:** A new REQ (REQ-049a) or expanded REQ-048 preamble with the list comprehension iteration pattern.
**What was found:** No change from original text.

### B3-03: Default Dockerfile Template
**Verdict: FAIL**
**Evidence:** REQ-015 at line 164 still says "If no Dockerfile exists in builder output_dir, generate a default Python Dockerfile based on ServiceInfo.stack" without any actual template content. No Dockerfile template for Python/FastAPI or Node/Express found.
**What was expected:** Default Dockerfile templates per stack added to REQ-015 (Python/FastAPI with python:3.12-slim-bookworm, Node/Express with node:20-slim), linked to B3-01's Debian-based constraint.
**What was found:** No change from original text.

### B3-04: Adversarial Scanner File Walking
**Verdict: FAIL**
**Evidence:** No text containing "pathlib.Path.rglob()", "EXCLUDE_DIRS", or file walking mechanism specification found in the Layer 4 scanner section (REQ-039 through REQ-042 area).
**What was expected:** "Use pathlib.Path.rglob() for file discovery with EXCLUDE_DIRS set. Do NOT use os.walk()."
**What was found:** No change from original text.

### B3-05: M2/M3 Parallelizability
**Verdict: FAIL**
**Evidence:** M2's description at line 214 does NOT contain "Parallel with: M3" or any parallel annotation. M3's description at line 271 already contains "This milestone can run in parallel with M2 since both depend only on M1" (this was present in the original PRD).
**Research report said:** MODIFIED -- Only M2 needs the parallel annotation added. M3 already has it.
**What was expected:** M2's header modified to add "Parallel with: M3" or similar text.
**What was found:** No change to M2. M3 was correctly not double-annotated (already had it).

### B3-06: CLI Command Count
**Verdict: PARTIAL**
**Evidence:**
- Line 458 (M6 description): STILL says "6 commands (init, plan, build, integrate, verify, run) plus status and resume utilities"
- Line 462 (REQ-054): Says "8 commands" -- correct
- Line 490 (TEST-033): Says "all 8 commands" -- correct
- Line 655 (summary table): Says "8 commands" -- correct
**What was expected:** Line 458 standardized to "8 CLI commands: init, plan, build, integrate, verify, run (6 pipeline commands) + status, resume (2 utility commands)"
**What was found:** The description at line 458 still says "6 commands" while everywhere else says "8 commands". The inconsistency the fix was supposed to resolve remains at the exact line flagged.

### B3-07: pytest asyncio_mode Configuration
**Verdict: FAIL**
**Evidence:**
- Tech stack at line 20 mentions "asyncio_mode = 'auto'" but this was already in the original PRD.
- TECH-028 at line 478 is taken (Typer CLI config).
- No new TECH requirement (TECH-031 or other available ID) found specifying pyproject.toml config with `[tool.pytest.ini_options]` section.
- TECH-030 at line 480 is the last TECH requirement in M6, covering Rich Progress.
**Research report said:** MODIFIED -- use a different TECH-xxx number since TECH-028 is taken (e.g., TECH-031).
**What was expected:** A new TECH-031 (or next available) requirement: "pyproject.toml must include `[tool.pytest.ini_options]` section with `asyncio_mode = 'auto'` and `filterwarnings = ['ignore::DeprecationWarning']`"
**What was found:** No new TECH requirement added.

---

## Run 4: RUN4_PRD.md -- 0 PASS, 0 PARTIAL, 4 FAIL

### R4-01: Contract Engine 9-Tool Verification
**Verdict: FAIL**
**Evidence:** The SVC wiring checklist (lines 264-280) goes from SVC-001 through SVC-017 with no SVC-010a, SVC-010b, or SVC-010c entries. The 3 Build 3-consumed tools (create_contract, validate_spec, list_contracts) are mentioned in REQ-010 (line 238) and REQ-024 (line 338) but have no dedicated SVC wiring entries.
**What was expected:** Three new SVC entries (SVC-010a, SVC-010b, SVC-010c) for create_contract, validate_spec, list_contracts consumed by Build 3 Integrator directly via MCP.
**What was found:** No change to the SVC wiring checklist.

### R4-02: OpenAPI Endpoint Precondition
**Verdict: FAIL**
**Evidence:** REQ-026 Phase 6 at line 340 still says "run contract compliance via Schemathesis pointing at http://localhost:{port}/openapi.json" without any precondition check. No text containing "precondition", "verify each service responds to GET /openapi.json with HTTP 200", or any /openapi.json availability check found.
**What was expected:** A precondition added to REQ-026 Phase 6: "Before running Schemathesis, verify each service responds to GET /openapi.json with HTTP 200."
**What was found:** No change from original text.

### R4-03: Test Matrix Traceability
**Verdict: FAIL**
**Evidence:** The test matrix tables (lines 454-519) retain the original 4-column format: ID, Test, Expected, Priority. No "Maps To", "Milestone", or traceability column added. The 57 tests have no mapping to the 18 TEST-xxx items defined in the milestone sections.
**What was expected:** A traceability column added to the 57-test matrix enabling bidirectional coverage verification between matrix entries and TEST-xxx items.
**What was found:** No change to the test matrix format.

### R4-05: SVC DTO Field Name Reconciliation
**Verdict: FAIL**
**Evidence:** SVC-001 at line 217 shows `contract_stubs: list` -- this was already correct per the research report (both Build 1 and Run 4 use `contract_stubs`, not `contracts`). However, no reconciliation note or verification annotation was added to any SVC entry. The SVC table appears unchanged.
**Research report said:** MODIFIED -- "Reconcile every SVC entry (SVC-001 through SVC-017) against the source Build PRD field-by-field. Focus reconciliation on field NAME accuracy and completeness (e.g., Build 1 SVC-002 is missing build_cycle_id which exists in the Pydantic ServiceMap model)."
**What was expected:** SVC entries verified and any missing fields (like build_cycle_id in SVC-002) added, or a reconciliation note documenting the verification.
**What was found:** No change from original text.

---

## Rejected Fixes -- Correctly NOT Applied

### B1-03: Milestone Count Header
**Verdict: CORRECTLY REJECTED**
**Evidence:** The header at line 1 does NOT state any milestone count. M8 exists at line 536 ("Milestone 8: Integration, Docker, and End-to-End Tests"). All 8 milestones (M1-M8) are present and consistent.
**Assessment:** The research report correctly identified that the fix guide was factually wrong on both counts. No change was applied, which is correct.

### R4-04: Directory Structure Guidance
**Verdict: CORRECTLY REJECTED**
**Evidence:** Directory structure sections already exist at lines 164-193 with "Source directory structure" (src/run4/ with 7 files) and "Test directory structure" (tests/run4/ with conftest.py and 10 test files).
**Assessment:** The research report correctly identified that the fix guide's claim of "no directory structure guidance" was factually wrong. No change was applied, which is correct.

---

## Cross-PRD Interface Consistency Check

| Interface | Expected Post-Fix State | Actual State |
|-----------|------------------------|--------------|
| Contract Engine 9-tool split | B2-01 clarifies 6/9 split + R4-01 adds SVC-010a/b/c | Neither fix applied -- gap remains |
| Architect MCP (4 tools) | R4-05 reconciles SVC-001..004 fields | Not reconciled -- gap remains |
| Codebase Intel MCP (7 tools) | Already CLEAN | CLEAN (no fix needed) |
| Docker Compose merge | B3-03 adds Debian-based templates | Not applied -- gap remains |
| Config.yaml compatibility | Already CLEAN | CLEAN (no fix needed) |
| Filename consistency (Build 2) | B2-02 unifies mcp_client(s).py | Not applied -- gap remains |

---

## Detailed Findings Summary

| Fix ID | PRD File | Expected | Applied? | Verdict |
|--------|----------|----------|----------|---------|
| B1-01 | BUILD1_PRD.md | tree-sitter version note in REQ-043 | YES | PASS |
| B1-02 | BUILD1_PRD.md | M5/M6 cross-milestone stub guidance | YES | PASS |
| B1-03 | BUILD1_PRD.md | REJECTED -- no fix needed | Correctly not applied | N/A |
| B1-04 | BUILD1_PRD.md | Optional regex patterns in REQ-056 | NO | FAIL |
| B1-05 | BUILD1_PRD.md | Async/Sync Boundary top-level section | NO | FAIL |
| B2-01 | BUILD2_PRD.md | "wraps 6 of 9" clarification | NO | FAIL |
| B2-02 | BUILD2_PRD.md | Filename consistency (singular vs plural) | NO | FAIL |
| B2-03 | BUILD2_PRD.md | "validation only" mode explanation | Partially (table label exists but may be original) | PARTIAL |
| B3-01 | BUILD3_PRD.md | Debian-based Docker image TECH requirement | NO | FAIL |
| B3-02 | BUILD3_PRD.md | Builder config iteration pattern | NO | FAIL |
| B3-03 | BUILD3_PRD.md | Default Dockerfile templates | NO | FAIL |
| B3-04 | BUILD3_PRD.md | pathlib.Path.rglob() specification | NO | FAIL |
| B3-05 | BUILD3_PRD.md | M2 parallel annotation | NO | FAIL |
| B3-06 | BUILD3_PRD.md | Command count "8" standardization | Line 458 still says "6" | PARTIAL |
| B3-07 | BUILD3_PRD.md | pytest asyncio_mode TECH requirement | NO | FAIL |
| R4-01 | RUN4_PRD.md | SVC-010a/b/c for Build 3 tools | NO | FAIL |
| R4-02 | RUN4_PRD.md | OpenAPI precondition check | NO | FAIL |
| R4-03 | RUN4_PRD.md | Test matrix traceability column | NO | FAIL |
| R4-04 | RUN4_PRD.md | REJECTED -- directory structure exists | Correctly not applied | N/A |
| R4-05 | RUN4_PRD.md | SVC field reconciliation | NO | FAIL |

---

## Conclusion

**2 of 17 fixes were correctly applied** (B1-01 and B1-02 in BUILD1_PRD.md).
**2 fixes are partially applied** (B2-03 and B3-06) but incomplete.
**13 fixes were not applied at all.**
**Both rejected fixes were correctly left unchanged.**

The fixer agent appears to have only worked on BUILD1_PRD.md (and even there, only completed 2 of 4 fixes). BUILD2_PRD.md, BUILD3_PRD.md, and RUN4_PRD.md show no evidence of any fix application. All remaining fixes need to be applied.
