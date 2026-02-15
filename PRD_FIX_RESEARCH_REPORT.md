# PRD Fix Research Report

## Summary
- Total fixes reviewed: 19
- CONFIRMED: 13
- REJECTED: 2
- MODIFIED: 4 (fix is valid but needs adjustment)

---

## Fix-by-Fix Analysis

### B1-01: tree-sitter Version Cross-Reference
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-043 (BUILD1_PRD.md:424) uses `QueryCursor(query)` and `cursor.captures(root_node)` returning `dict[str, list[Node]]`. The tech stack at line 14 pins tree-sitter 0.25.2 but REQ-043 does not reference this version constraint.
**Technical Accuracy:** VERIFIED via web research. The QueryCursor class was introduced in py-tree-sitter v0.25.0 (July 2024). The captures() return type changed to `dict[str, list[Node]]` in v0.23.0. Before v0.25.0, captures/matches were on the `Query` class, not `QueryCursor`. The PRD's API usage is correct for 0.25.x but would fail on older versions.
**Verdict:** CONFIRMED. Adding the version cross-reference note prevents confusion if someone installs an older tree-sitter version.
**Recommended Fix Text:** As specified in the fix guide.

---

### B1-02: M5/M6 Cross-Milestone ChromaDB Dependency
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-055 (BUILD1_PRD.md:470) in Milestone 5 defines `IncrementalIndexer.index_file()` which "indexes chunks to chroma_store via semantic_indexer". The `SemanticIndexer` class is defined in REQ-052 (line 467), which is in Milestone 6. An agent implementing M5 would need `semantic_indexer.index_symbols()` but it does not exist yet.
**Technical Accuracy:** N/A — this is a dependency ordering issue, not a technical claim.
**Verdict:** CONFIRMED. The cross-milestone dependency is real and would block an M5-only implementation.
**Recommended Fix Text:** As specified in the fix guide.

---

### B1-03: Milestone Count Header
**Status:** REJECTED
**Problem Verified:** NO — The fix guide claims "The PRD header states 8 milestones but the document shows M1 through M7" and says "the count in the header is wrong, or M8 is missing." In reality:
1. The PRD header (BUILD1_PRD.md:1-3) does NOT state any milestone count at all.
2. The document actually has **8 milestones** (M1 through M8), with M8 at line 530 titled "Milestone 8: Integration, Docker, and End-to-End Tests".
**Technical Accuracy:** The fix guide's claim is factually wrong on both counts — no header count exists, and there ARE 8 milestones.
**Verdict:** REJECTED. No fix needed. The milestone count is consistent (8 milestones, M1-M8) and no header claims otherwise.

---

### B1-04: ServiceInterfaceExtractor Regex Patterns
**Status:** MODIFIED
**Problem Verified:** PARTIALLY — REQ-056 (BUILD1_PRD.md:471) describes route detection patterns in natural language: "Python: @app.get, @app.post, @router.get, @router.post etc.; TypeScript: app.get(), router.get(), @Get(), @Post() (NestJS); C#: [HttpGet], [HttpPost], [Route("path")]; Go: http.HandleFunc, r.HandleFunc, mux.HandleFunc". These are actually quite specific (concrete decorator/function names per language), not just vague "looking for route decorator patterns" as the fix guide claims.
**Technical Accuracy:** The regex patterns proposed in the fix are reasonable. However, REQ-056 already provides sufficient specificity for an agent to implement — the patterns are named concretely per language.
**Verdict:** MODIFIED. The problem is overstated. REQ-056 already lists concrete patterns per language. Adding exact regex is a nice-to-have improvement but not necessary since Build 3's REQ-034 is a completely different codebase. Recommend downgrading from "MINOR -7" to "MINOR -3" or making the regex addition optional.
**Recommended Fix Text:** Keep the proposed regex as a supplementary note rather than a mandatory fix: "Optional: For consistency with Build 3's regex-based approach, agents MAY use these regex patterns: [regex list from fix guide]."

---

### B1-05: Async/Sync Boundary Top-Level Rule
**Status:** CONFIRMED
**Problem Verified:** YES — TECH-035 (line 554) and TECH-036 (line 555) exist as separate requirements but are buried in Milestone 5's technical requirements. An agent implementing M2 (Architect) might not see these until they reach M5. The async/sync boundary is fundamental and applies from M1 onward.
**Technical Accuracy:** N/A — architectural guidance issue.
**Verdict:** CONFIRMED. Consolidating into a top-level section improves discoverability.
**Recommended Fix Text:** As specified in the fix guide.

---

### B2-01: Contract Engine Tool Count Clarification
**Status:** CONFIRMED
**Problem Verified:** YES — M2's description (BUILD2_PRD.md:134) says "Build 1's Contract Engine (6 tools)" and REQ-017 (line 138) says "wrapping all 6 Contract Engine MCP tools". However, INT-001 (line 438) says "Contract Engine MCP server (9 tools)". Build 1's M7 (REQ-059 in BUILD1_PRD.md) exposes 9 tools total. The discrepancy between "6" and "9" is confusing.
**Technical Accuracy:** Verified. Build 1 exposes 9 Contract Engine MCP tools (line 238 of RUN4_PRD.md confirms 9 tool names). Build 2 wraps 6 of them via ContractEngineClient (REQ-017 through REQ-023 in BUILD2_PRD.md).
**Verdict:** CONFIRMED. The clarification about which 6 of 9 are wrapped is valuable.
**Recommended Fix Text:** As specified in the fix guide.

---

### B2-02: Filename Inconsistency
**Status:** CONFIRMED
**Problem Verified:** YES — The project structure (BUILD2_PRD.md:27) shows `mcp_client.py` (singular). INT-003 (BUILD2_PRD.md:440) references `mcp_clients.py` (plural): "Create `ArchitectClient` class in `mcp_clients.py`".
**Technical Accuracy:** N/A — naming consistency issue.
**Verdict:** CONFIRMED. Pick one name and make it consistent.
**Recommended Fix Text:** As specified in the fix guide.

---

### B2-03: 'Validation Only' Mode Definition
**Status:** MODIFIED
**Problem Verified:** PARTIALLY — The depth gating at TECH-044 (BUILD2_PRD.md:396) says "standard = contract_engine enabled (validation_on_build=True, test_generation=False)" which IS effectively "validation only" mode — it specifies the exact config fields. The fix guide says "there's no mechanism for 'validation only' mode" which is not quite right; the mechanism IS there (the config fields), just the label isn't explicitly defined.
**Technical Accuracy:** The config fields `validation_on_build=True, test_generation=False` serve as the mechanism.
**Verdict:** MODIFIED. The mechanism exists but is described inline in TECH-044 without an explicit label. A footnote would help but the fix guide's claim that "there's no mechanism" is overstated. Recommend a lighter fix: add a parenthetical "(validation only)" after the config values in TECH-044 rather than a separate footnote.
**Recommended Fix Text:** In TECH-044, change "contract_engine enabled (validation_on_build=True, test_generation=False)" to "contract_engine enabled (validation_on_build=True, test_generation=False — this is 'validation only' mode: validates contracts exist and match endpoints but does not auto-generate test files)".

---

### B3-01: Pact Native Library Installation
**Status:** MODIFIED
**Problem Verified:** PARTIALLY — The PRD at BUILD3_PRD.md:17 specifies "pact-python 3.2.1+ (Pact V4 spec, Rust FFI)" but does NOT specify Docker base image constraints. However, the fix guide's claim that "this fails silently" on Alpine is overstated. Per web research (pact-foundation/roadmap#30), Alpine/musl support has improved since pact_ffi 0.4.17, though it remains experimental with known edge cases (shared-mime-info inconsistency on ARM64).
**Technical Accuracy:** Partially accurate. Alpine support exists but is experimental. The recommendation to use Debian-based images is sound for production reliability, but "fails silently" is too strong — installation may work on recent Alpine versions.
**Verdict:** MODIFIED. The base image constraint is a good practice but the severity should note that Alpine support exists (experimental). Change "fails silently" to "may fail or produce runtime errors on Alpine/musl due to experimental FFI support."
**Recommended Fix Text:** "All Docker images for Build 3 services and test runners SHOULD use a Debian-based Python image (e.g., python:3.12-slim-bookworm). Alpine/musl support for pact_ffi is experimental and may cause runtime issues, particularly on ARM64 architectures."

---

### B3-02: Builder Config Generation Glue Code
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-048 (BUILD3_PRD.md:396) defines `run_parallel_builders(builder_configs: list[dict], ...)` consuming a list of builder_configs. REQ-049 (line 398) defines `generate_builder_config(...)` returning a single config dict. There is no explicit iteration pattern showing how to generate configs for all services before passing them to run_parallel_builders. The connection is implicit.
**Technical Accuracy:** N/A — glue code gap.
**Verdict:** CONFIRMED. Adding the iteration pattern clarifies the assembly step.
**Recommended Fix Text:** As specified in the fix guide.

---

### B3-03: Default Dockerfile Template
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-015 (BUILD3_PRD.md:164) says "If no Dockerfile exists in builder output_dir, generate a default Python Dockerfile based on ServiceInfo.stack" but provides NO template content. An agent must invent the entire Dockerfile.
**Technical Accuracy:** N/A — completeness issue.
**Verdict:** CONFIRMED. Default templates per stack would eliminate ambiguity.
**Recommended Fix Text:** As specified in the fix guide.

---

### B3-04: Adversarial Scanner File Walking
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-039 (BUILD3_PRD.md:330) says "Scan all .py/.ts/.js files (excluding node_modules, .venv, __pycache__, dist, build)" specifying the EXCLUSION list but not the walking mechanism. However, the fix is relatively minor since Python developers would naturally use pathlib or os.walk.
**Technical Accuracy:** N/A — implementation guidance.
**Verdict:** CONFIRMED. Adding `pathlib.Path.rglob()` recommendation eliminates one implementation decision.
**Recommended Fix Text:** As specified in the fix guide.

---

### B3-05: M2/M3 Parallelizability
**Status:** MODIFIED
**Problem Verified:** PARTIALLY — M3's description (BUILD3_PRD.md:271) ALREADY states: "This milestone can run in parallel with M2 since both depend only on M1." However, M2's description (line 214) does NOT mention parallel capability. So the fix guide's claim that "neither milestone header states this" is WRONG — M3 does state it.
**Technical Accuracy:** N/A.
**Verdict:** MODIFIED. Only M2 needs the parallel annotation added. M3 already has it.
**Recommended Fix Text:** In M2's header only, add: "Parallel with: M3". Do NOT modify M3 (it already says this).

---

### B3-06: CLI Command Count
**Status:** CONFIRMED
**Problem Verified:** YES — M6's description (BUILD3_PRD.md:458) says "6 commands (init, plan, build, integrate, verify, run) plus status and resume utilities" — this is 6 pipeline + 2 utility = 8 total. TEST-033 (line 489) says "test all 8 commands are registered". The description says "6 commands" then lists 8, which is confusing.
**Technical Accuracy:** N/A — counting consistency.
**Verdict:** CONFIRMED. Standardize to "8 CLI commands" as the fix suggests.
**Recommended Fix Text:** As specified in the fix guide.

---

### B3-07: pytest asyncio_mode Configuration
**Status:** MODIFIED
**Problem Verified:** YES — The tech stack (BUILD3_PRD.md:20) mentions "pytest-asyncio 0.24.x+ (asyncio_mode = 'auto')" but there is no requirement specifying where this config goes. However, the fix suggests adding "TECH-028" but that ID is already taken (BUILD3_PRD.md:478 uses TECH-028 for Typer CLI config).
**Technical Accuracy:** The pyproject.toml config recommendation is correct.
**Verdict:** MODIFIED. The fix is valid but must use a different TECH-xxx number since TECH-028 is already taken. Use the next available TECH number (check what's available after TECH-030).
**Recommended Fix Text:** Use a new TECH-xxx ID (e.g., TECH-031 or the next available): "pyproject.toml must include `[tool.pytest.ini_options]` section with `asyncio_mode = 'auto'` and `filterwarnings = ['ignore::DeprecationWarning']`."

---

### R4-01: Contract Engine 9-Tool Verification
**Status:** CONFIRMED
**Problem Verified:** YES — The SVC wiring map (RUN4_PRD.md:221-226) shows SVC-005 through SVC-010 covering 6 Contract Engine tools wrapped by ContractEngineClient. The 3 remaining tools (create_contract, validate_spec, list_contracts) are consumed by Build 3 directly (confirmed in REQ-010 at line 238 which verifies all 9 tools). However, the SVC wiring checklist at lines 268-273 only has entries for the 6 wrapped tools, not the 3 Build 3-consumed tools.
**Technical Accuracy:** REQ-010 already tests all 9 tools at the MCP handshake level. The gap is in the SVC wiring checklist only.
**Verdict:** CONFIRMED. Adding SVC entries for the 3 Build 3-consumed tools completes the traceability.
**Recommended Fix Text:** As specified in the fix guide.

---

### R4-02: OpenAPI Endpoint Precondition
**Status:** CONFIRMED
**Problem Verified:** YES — REQ-026 (RUN4_PRD.md:340) says "Schemathesis pointing at http://localhost:{port}/openapi.json" but does not explicitly verify the endpoint responds before running tests. FastAPI exposes /openapi.json by default, but this is an undocumented assumption.
**Technical Accuracy:** FastAPI does auto-generate /openapi.json, but it can be disabled via `app = FastAPI(docs_url=None, openapi_url=None)`. The assumption is usually safe but worth documenting.
**Verdict:** CONFIRMED. Adding a precondition check is good defensive practice.
**Recommended Fix Text:** As specified in the fix guide.

---

### R4-03: Test Matrix Traceability
**Status:** CONFIRMED
**Problem Verified:** YES — The 57-test verification matrix (RUN4_PRD.md:441-520) has columns (ID, Test, Expected, Priority) but no traceability column mapping to the 18 TEST-xxx items (TEST-001 through TEST-018) defined in the milestone sections.
**Technical Accuracy:** N/A — completeness issue.
**Verdict:** CONFIRMED. Adding a traceability column would enable bidirectional coverage verification.
**Recommended Fix Text:** As specified in the fix guide.

---

### R4-04: Directory Structure Guidance
**Status:** REJECTED
**Problem Verified:** NO — The fix guide claims "Run 4 is described as 'NOT a build' but has ~5K LOC of infrastructure. No directory structure guidance." This is FACTUALLY WRONG. RUN4_PRD.md lines 164-193 contain explicit "Source directory structure" and "Test directory structure" sections with full file trees:
- `src/run4/` with 7 files (config.py, state.py, mcp_health.py, builder.py, fix_pass.py, scoring.py, audit_report.py)
- `tests/run4/` with conftest.py and 10 test files organized by milestone
**Technical Accuracy:** The directory structure IS present and comprehensive.
**Verdict:** REJECTED. No fix needed. The directory structure guidance exists at lines 164-193.

---

### R4-05: SVC DTO Field Name Reconciliation
**Status:** MODIFIED
**Problem Verified:** PARTIALLY — The fix guide claims "SVC-001 shows contract_stubs but Build 1's REQ-020 returns contracts." This specific example is WRONG:
- Build 1's REQ-002 defines `DecompositionResult` with `contract_stubs: list[dict]`
- Build 1's SVC table (line 312) shows `contract_stubs: list`
- Run 4's SVC table (line 217) also shows `contract_stubs: list`
These match. However, there ARE minor differences between the SVC tables:
- Build 1 SVC-002 omits `build_cycle_id` field which is in the Pydantic model
- Run 4 SVC-001 uses `dict` for service_map/domain_model (correct for MCP returns) while Build 1 uses `ServiceMap`/`DomainModel` (correct for Pydantic)
**Technical Accuracy:** The specific example cited is wrong, but cross-PRD SVC field verification is still valuable.
**Verdict:** MODIFIED. The principle is correct (verify SVC entries match source Build PRD specs), but the specific example (contract_stubs vs contracts) is wrong — both use contract_stubs. The fix should proceed with actual reconciliation but the guide's example should be corrected.
**Recommended Fix Text:** "Reconcile every SVC entry (SVC-001 through SVC-017) against the source Build PRD field-by-field. Note: Run 4 SVC tables correctly use `dict` types for MCP return values (since MCP returns JSON dicts, not Pydantic models). Focus reconciliation on field NAME accuracy and completeness (e.g., Build 1 SVC-002 is missing build_cycle_id which exists in the Pydantic ServiceMap model)."

---

## Cross-PRD Interface Verification Notes

The cross-PRD interface table in the fix guide is generally accurate. Key observations:
1. Contract Engine 9-tool split (6 in Build 2, 3 in Build 3) is correctly identified
2. Codebase Intelligence 7/7 coverage in Build 2 is verified
3. Docker Compose merge linkage to B3-03 is correct
4. Config.yaml compatibility through `_dict_to_config()` is correct
