# BUILD 2 PRD EXHAUSTIVE AUDIT REPORT

**File Audited:** `prompts/BUILD2_PRD.md` (589 lines, 6 milestones)
**Auditor:** BUILD 2 AUDITOR
**Date:** 2026-02-15
**Verdict:** CONDITIONAL PASS

---

## Summary

Build 2 PRD is a well-structured, implementation-ready specification for upgrading agent-team v14.0 with Agent Teams coordination, Contract Engine MCP integration, and Codebase Intelligence MCP integration. The PRD demonstrates strong architectural patterns: backward compatibility, graceful fallback, config gating, and crash isolation.

However, 1 CRITICAL issue, 7 HIGH issues, 6 MEDIUM issues, and 3 LOW issues were identified. The CRITICAL issue (TeammateIdle hook type) will cause a runtime failure if implemented as-is. The HIGH issues include a cross-build hash mismatch that will break contract validation, inconsistent tool counts, and SVC table field omissions that will confuse implementing agents.

**Issue Counts:** 1 CRITICAL, 7 HIGH, 6 MEDIUM, 3 LOW = 17 total issues

---

## Issue List

### CRITICAL Issues (1)

#### ISSUE-B2-001: REQ-012 specifies agent-type hook for TeammateIdle, but official docs confirm this is unsupported
- **Severity:** CRITICAL
- **Location:** Line 77 (REQ-012)
- **Dimension:** Technology Accuracy
- **Details:** REQ-012 states: `generate_teammate_idle_hook() must return an agent-type hook`. However, the official Claude Code hooks documentation at https://code.claude.com/docs/en/hooks explicitly states: **"TeammateIdle does not support prompt-based or agent-based hooks"** -- only command-type hooks are supported for TeammateIdle. Implementing this as written will produce a hook that is silently ignored or errors at runtime.
- **Fix:** Change REQ-012 to specify a command-type hook (like REQ-013's Stop hook pattern) instead of agent-type. The shell script should call `claude -p "check TaskList"` or use a Python script that checks for pending tasks.
- **Impact:** Runtime failure -- idle teammates will never be prevented from idling even when pending tasks exist.

---

### HIGH Issues (7)

#### ISSUE-B2-002: Cross-build spec_hash computation mismatch will break contract validation
- **Severity:** HIGH
- **Location:** Line 156 (TECH-014) vs Build 1 TECH-009 (line 355)
- **Dimension:** Cross-Build Compatibility
- **Details:** Build 1 TECH-009 computes spec_hash as: `hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()` -- NO compact separators. Build 2 TECH-014 computes spec_hash as: `json.dumps(spec, sort_keys=True, separators=(',', ':'))` then hash. The `separators=(',', ':')` parameter removes whitespace from JSON output, producing DIFFERENT hashes for the same spec. When Build 2's ContractEngineClient receives a contract from Build 1's Contract Engine, any local hash validation or comparison will fail because the hashes were computed differently.
- **Fix:** Remove `separators=(',', ':')` from TECH-014 to match Build 1's hash computation, OR update Build 1's TECH-009 to include compact separators (requires Build 1 PRD amendment). The hashes MUST use identical serialization.
- **Impact:** Contract change detection, cache invalidation, and version comparison will silently fail.

#### ISSUE-B2-003: Cross-build table says Architect has "3 tools" but Build 1 Milestone 7 defines 4 tools
- **Severity:** HIGH
- **Location:** Line 573 (Cross-Build Dependencies table)
- **Dimension:** Cross-Build Compatibility
- **Details:** The Cross-Build Dependencies table at line 573 states: "Architect MCP server (3 tools)". However, Build 1 REQ-059 (line 512) explicitly registers 4 tools: `decompose`, `get_service_map`, `get_contracts_for_service`, `get_domain_model`. Build 1's own Milestone 7 header (line 508) also says "Architect (4 tools)". Confusingly, Build 2 INT-003 (line 440) correctly says "Architect MCP server (4 tools)". Note: Build 1 itself has an internal inconsistency -- line 630 says "3 tools" while line 508/REQ-059 say 4.
- **Fix:** Change the Cross-Build Dependencies table entry to "Architect MCP server (4 tools)" to match Build 1 REQ-059 and Build 2 INT-003.
- **Impact:** An implementing agent may build an ArchitectClient that only wraps 3 tools, missing `get_domain_model()`.

#### ISSUE-B2-004: TEST-044 truncation threshold contradicts TECH-005 contract_limit
- **Severity:** HIGH
- **Location:** Line 341 (TEST-044) vs Line 90 (TECH-005)
- **Dimension:** Implementation Correctness
- **Details:** TEST-044 states: "Test generate_claude_md() truncates contracts list at 20 with '... and N more' suffix". But TECH-005 defines `contract_limit: int = 100` as the truncation threshold in AgentTeamsConfig. REQ-052 (line 301) references `config.agent_teams.contract_limit` for the truncation value. The test hardcodes 20, but the config default is 100.
- **Fix:** Change TEST-044 to test truncation at `contract_limit` (default 100), not hardcoded 20. OR add a test that explicitly sets `contract_limit=20` and verifies truncation at that value.
- **Impact:** Test will fail or test wrong behavior. An agent implementing the test may hardcode 20 in the function instead of using config.

#### ISSUE-B2-005: SVC-010 table missing language and service_name parameters vs REQ-034
- **Severity:** HIGH
- **Location:** Line 256 (SVC-010 table) vs Line 223 (REQ-034)
- **Dimension:** Completeness
- **Details:** REQ-034 defines `search_semantic(query: str, language: str | None = None, service_name: str | None = None, n_results: int = 10)` with 4 parameters. The SVC-010 table row (line 256) and checkbox item (line 264) only show `search_semantic(query, n_results)` with 2 parameters, omitting `language` and `service_name`. Build 1's Codebase Intelligence search_semantic MCP tool also accepts these optional filters.
- **Fix:** Update SVC-010 table and checkbox to include all 4 parameters: `search_semantic(query, language, service_name, n_results)`.
- **Impact:** Implementing agent will build a client method missing two filter parameters that Build 1 supports.

#### ISSUE-B2-006: SVC-009 response missing circular_deps from DependencyResult
- **Severity:** HIGH
- **Location:** Line 255 (SVC-009) vs Line 236 (TECH-023)
- **Dimension:** Completeness
- **Details:** TECH-023 defines `DependencyResult` with 4 fields: `imports`, `imported_by`, `transitive_deps`, `circular_deps`. The SVC-009 table row (line 255) and checkbox item (line 263) only show `{ imports: array, imported_by: array, transitive_deps: array }` -- missing `circular_deps`. Build 1 REQ-047 also returns circular dependencies via `graph_analyzer.get_dependencies()`.
- **Fix:** Add `circular_deps: array` to SVC-009 response DTO in both table and checkbox.
- **Impact:** Circular dependency detection data from Build 1 will be silently dropped.

#### ISSUE-B2-007: SVC-001 checkbox missing service_name and status fields vs table version
- **Severity:** HIGH
- **Location:** Line 181 (SVC-001 checkbox) vs Line 174 (SVC-001 table)
- **Dimension:** Completeness
- **Details:** The SVC-001 table row (line 174) shows response DTO: `{ id: string, type: string, version: string, service_name: string, spec: object, spec_hash: string, status: string }` with 7 fields. The SVC-001 checkbox item (line 181) shows only: `{ id: string, type: string, version: string, spec: object, spec_hash: string }` with 5 fields -- missing `service_name` and `status`.
- **Fix:** Update SVC-001 checkbox to include all 7 fields matching the table.
- **Impact:** ContractInfo dataclass (TECH-014) includes both fields, so implementation should be correct, but the checkbox discrepancy will confuse agents checking completeness.

#### ISSUE-B2-008: startup_timeout_ms and tool_timeout_ms defined but never applied
- **Severity:** HIGH
- **Location:** Lines 157, 238 (TECH-015, TECH-025)
- **Dimension:** Completeness
- **Details:** Both `ContractEngineConfig` and `CodebaseIntelligenceConfig` define `startup_timeout_ms: int = 30000` and `tool_timeout_ms: int = 60000`. However, no REQ or TECH requirement specifies how these timeouts are applied. `create_contract_engine_session()` (REQ-024) catches `TimeoutError` but doesn't set any timeout. `StdioServerParameters` doesn't accept timeout arguments. The MCP Python SDK's `stdio_client()` has no documented timeout parameter. Individual `call_tool()` invocations in the MCP SDK don't accept timeout either (timeout is at the transport level).
- **Fix:** Add a REQ specifying how timeouts are applied: (a) `startup_timeout_ms` should be an `asyncio.wait_for()` wrapper around `session.initialize()`, (b) `tool_timeout_ms` should be an `asyncio.wait_for()` wrapper around each `session.call_tool()` invocation. OR document that these are future placeholders.
- **Impact:** Without explicit timeout application, MCP calls can hang indefinitely if the server becomes unresponsive.

---

### MEDIUM Issues (6)

#### ISSUE-B2-009: HookInput missing team_name and task_description fields per official docs
- **Severity:** MEDIUM
- **Location:** Line 89 (TECH-004A)
- **Dimension:** Technology Accuracy
- **Details:** Per the official Claude Code hooks documentation, `TaskCompleted` hook input includes: `task_id`, `task_subject`, `task_description`, `teammate_name`, `team_name`. The `TeammateIdle` hook input includes: `teammate_name`, `team_name`. TECH-004A defines `HookInput` with `task_id`, `task_subject`, `teammate_name` but omits `team_name` and `task_description`.
- **Fix:** Add `team_name: str = ""` and `task_description: str = ""` to HookInput.
- **Impact:** Hook scripts that need team context or task description will not have access to these fields.

#### ISSUE-B2-010: REQ-060A step number references are fragile
- **Severity:** MEDIUM
- **Location:** Line 310 (REQ-060A)
- **Dimension:** Agent-Readiness
- **Details:** REQ-060A references "Step 2 (Analysis)", "Step 5 (Implementation)", "Step 8 (Integration Verification)" of the 9-step MILESTONE WORKFLOW block. These step numbers assume the current milestone workflow structure in agents.py (from v14.0). If the workflow steps are reordered, renamed, or expanded in Build 2, these references will be wrong.
- **Fix:** Reference steps by name only (e.g., "the Analysis step", "the Implementation step") rather than by number, OR include a mapping table of step names to numbers.
- **Impact:** Medium -- implementing agent can resolve by reading the current workflow, but fragile for maintenance.

#### ISSUE-B2-011: WIRE-001 hard-coded line reference (line ~4200) will be wrong
- **Severity:** MEDIUM
- **Location:** Line 102 (WIRE-001)
- **Dimension:** Agent-Readiness
- **Details:** WIRE-001 references "line ~4200" in cli.py for the mode selection block. The current cli.py is ~5500+ lines and the mode selection block location varies. Hard-coded line references become stale as the codebase evolves.
- **Fix:** Replace with a code pattern reference: "Wire into cli.py mode selection block (the `if interactive:` ... `else:` branch containing `_run_prd_milestones()` and `_run_single()` calls)."
- **Impact:** Implementing agent will need to search for the correct location rather than jumping to line ~4200.

#### ISSUE-B2-012: REQ-053 overwrites existing CLAUDE.md without merge
- **Severity:** MEDIUM
- **Location:** Line 302 (REQ-053)
- **Dimension:** Architectural Soundness
- **Details:** REQ-053 states `write_teammate_claude_md()` writes to `{project_dir}/.claude/CLAUDE.md`. If the user's project already has a CLAUDE.md with custom instructions, this will be overwritten. The existing codebase (cli.py) may also generate CLAUDE.md content that would be lost.
- **Fix:** Add merge semantics: read existing CLAUDE.md, append Build 2 sections under a clearly delimited block (e.g., `<!-- BUILD2-START -->...<!-- BUILD2-END -->`), or write to a separate file like `.claude/BUILD2_CLAUDE.md` and add an include directive.
- **Impact:** User's custom CLAUDE.md instructions will be lost when agent teams mode activates.

#### ISSUE-B2-013: MCPConnectionError custom exception not specified where defined
- **Severity:** MEDIUM
- **Location:** Line 145 (REQ-024)
- **Dimension:** Completeness
- **Details:** REQ-024 references `MCPConnectionError(str(e))` as a custom exception but doesn't specify where it should be defined (which file, which module). It's not in any TECH requirement's dataclass list. The PRD should specify: define `MCPConnectionError(Exception)` in `mcp_clients.py` (or in a shared errors module).
- **Fix:** Add a TECH requirement: "Define `class MCPConnectionError(Exception): pass` in `mcp_clients.py`."
- **Impact:** Implementing agent must decide where to put this class. Minor but adds ambiguity.

#### ISSUE-B2-014: REQ-055 references line ~4150 -- fragile line reference
- **Severity:** MEDIUM
- **Location:** Line 304 (REQ-055)
- **Dimension:** Agent-Readiness
- **Details:** Same issue as ISSUE-B2-011. REQ-055 references "line ~4150" in cli.py.
- **Fix:** Replace with pattern reference: "In cli.py, after codebase map generation (Phase 0.5) and before mode selection block."
- **Impact:** Same as ISSUE-B2-011.

---

### LOW Issues (3)

#### ISSUE-B2-015: Test count estimates in project structure don't match TEST requirements
- **Severity:** LOW
- **Location:** Lines 44-52 (Project Structure)
- **Dimension:** Completeness
- **Details:** The project structure estimates ~35 tests for agent_teams_backend, ~30 for contract_client, etc. Counting the actual TEST-xxx requirements: M1 has 17 test requirements (TEST-001..017), M2 has 17 (TEST-018..030D), M3 has 9 (TEST-031..039), M4 has 10 (TEST-040..049), M5 has 17 (TEST-050..066), M6 has 28 (TEST-067..094). The estimates are directionally correct but won't match exactly.
- **Fix:** Update estimates or add a note that they are approximate.
- **Impact:** Minimal -- estimates are clearly labeled as "~N tests".

#### ISSUE-B2-016: Missing ArchitectClient specification in contract_client.py or mcp_clients.py
- **Severity:** LOW
- **Location:** Line 440 (INT-003) vs Line 20 (Project Structure)
- **Dimension:** Completeness
- **Details:** INT-003 specifies creating an `ArchitectClient` class in `mcp_clients.py` wrapping all 4 Architect tools. However, the Project Structure (lines 19-53) doesn't list `architect_client.py` or mention ArchitectClient in any file. It's only mentioned in INT-003 (Milestone 6, Integration Requirements) but has no dedicated REQ, TECH, or TEST requirements.
- **Fix:** Add explicit REQ, TECH (ArchitectClient dataclasses), and TEST requirements for ArchitectClient, OR clarify in INT-003 that it follows the exact same pattern as ContractEngineClient/CodebaseIntelligenceClient and can be implemented from the pattern without additional specification.
- **Impact:** Low -- the pattern is well-established from M2/M3, an implementing agent can follow it. But there are no tests specified.

#### ISSUE-B2-017: WIRE-001 line ~4200 also conflicts with WIRE-009 line ~170-250
- **Severity:** LOW
- **Location:** Lines 102, 329 (WIRE-001, WIRE-009)
- **Dimension:** Implementation Correctness
- **Details:** WIRE-001 says mode selection is at "line ~4200" while WIRE-009 says MCP servers assignment is at "line ~170-250". Both reference the same conceptual location in cli.py (the mode selection / orchestration block). The line numbers are inconsistent and both wrong for the actual codebase.
- **Fix:** Remove all line number references, use pattern/function references instead.
- **Impact:** Low -- agents will search by pattern regardless.

---

## Technology Verification Table

| Technology | PRD Claim | Verified | Status |
|------------|-----------|----------|--------|
| MCP Python SDK (`mcp>=1.25,<2`) | `StdioServerParameters` + `stdio_client()` + `ClientSession` + `call_tool()` pattern | Yes -- confirmed via PyPI docs and MCP SDK source | CORRECT |
| MCP import: `from mcp import StdioServerParameters` | Top-level import from mcp package | Yes -- confirmed | CORRECT |
| MCP import: `from mcp.client.stdio import stdio_client` | Submodule import | Yes -- confirmed | CORRECT |
| Claude Code Agent Teams | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var | Yes -- confirmed via official docs | CORRECT |
| Agent Teams tools | TaskCreate, TaskUpdate, TaskList, SendMessage | Yes -- confirmed | CORRECT |
| Agent Teams display modes | "in-process" (default), "tmux", "split" | Yes -- confirmed; split not on Windows Terminal | CORRECT |
| Claude Code Hooks: 14 events | SessionStart, UserPromptSubmit, PreToolUse, etc. | Yes -- confirmed via hooks reference | CORRECT |
| Claude Code Hooks: 3 types | command, prompt, agent | Yes -- confirmed | CORRECT |
| TeammateIdle hook: agent-type | PRD claims agent-type (REQ-012) | No -- official docs say agent-type NOT supported | **INCORRECT** |
| TaskCompleted hook input fields | task_id, task_subject, teammate_name | Partial -- missing team_name, task_description | **INCOMPLETE** |
| `@runtime_checkable` Protocol | TECH-009 specifies Protocol with @runtime_checkable | Yes -- standard typing pattern | CORRECT |
| asyncio.gather with return_exceptions=True | TECH-011 for wave execution | Yes -- standard asyncio pattern | CORRECT |
| `session.initialize()` mandatory first call | REQ-025 specifies this | Yes -- confirmed per MCP SDK specification | CORRECT |
| Hook script reads JSON from stdin | REQ-016 via python3 -c parser | Yes -- confirmed per hooks docs (input piped to stdin) | CORRECT |
| `subprocess.run(["claude", "--version"])` | TECH-010 for CLI availability check | Yes -- standard approach | CORRECT |
| pathlib.Path for all file ops | INT-010 Windows compatibility | Yes -- existing v14.0 pattern | CORRECT |
| `_dict_to_config()` returns tuple | INT-007, INT-020 | Yes -- matches v6.0+ pattern | CORRECT |
| `Violation` dataclass interface | INT-008 (.check, .file_path, .line, .message, .severity) | Yes -- matches existing quality_checks.py | CORRECT |

---

## Dimension Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Technology Accuracy | 8/10 | TeammateIdle hook type wrong (CRITICAL), HookInput missing fields (MEDIUM). All other tech claims verified. |
| Implementation Correctness | 8/10 | Hash computation mismatch (HIGH), TEST-044 threshold contradiction (HIGH). Code patterns, async patterns, and MCP SDK usage are all correct. |
| Architectural Soundness | 9/10 | Strong backward compatibility design, graceful fallback, config gating. CLAUDE.md overwrite concern (MEDIUM). Clean separation of concerns across new modules. |
| Completeness | 7/10 | Multiple SVC table field omissions (3 HIGH), timeout fields defined but unused (HIGH), MCPConnectionError location unspecified (MEDIUM), ArchitectClient under-specified (LOW). |
| Agent-Readiness | 8/10 | Most REQs are implementation-ready with clear signatures and behaviors. Fragile line references (3 MEDIUM). Step number references fragile (MEDIUM). |
| Cross-Build Compatibility | 7/10 | Hash mismatch (HIGH), tool count inconsistency (HIGH). Build 3 consumption via STATE.json `summary` dict is well-specified. Fallback behaviors are comprehensive. |

**Overall Score: 7.8/10**

---

## Clean Sections

### Strengths

1. **Backward compatibility design** -- All features default to `enabled: False`, ensuring v14.0 behavior when Build 2 features are disabled. INT-006 explicitly mandates this.

2. **Graceful fallback** -- Every MCP client method returns safe defaults on failure. Every MCP-dependent feature has a static analysis fallback. The ExecutionBackend factory has a complete fallback decision tree (REQ-004).

3. **Config gating consistency** -- All new features follow the established pattern: boolean config field -> depth gating -> `_dict_to_config()` parsing -> CLI wiring with `if config.X.enabled` guard.

4. **Crash isolation** -- CONTRACT scans follow the established `try/except` per-scan pattern. Each MCP client method catches all exceptions. Each wiring point is independently gated.

5. **ScanScope integration** -- CONTRACT scans correctly follow the v6.0 H2 pattern: detection uses full file list, violation reporting scoped to changed files (TECH-041).

6. **Comprehensive test coverage** -- 94 test requirements covering unit, integration, backward compatibility, and regression testing. The test plan systematically covers happy paths, error paths, fallback paths, and edge cases.

7. **Security considerations** -- SEC-001 (no secrets in MCP env), SEC-002 (no secrets in hook scripts), SEC-003 (strip securitySchemes from cached contracts) demonstrate security awareness.

8. **Clear dependency graph** -- Milestone dependencies are explicit: M1 and M2 are independent, M3 depends on M2, M4 depends on M1+M2+M3, M5 depends on M4, M6 depends on M4+M5. This enables parallel execution of M1 and M2.

### Risks

1. **MCP server availability** -- Build 2 assumes Build 1 MCP servers are running and accessible. If Build 1 isn't deployed, all MCP features fall back to static analysis, which reduces Build 2's value.

2. **Agent Teams experimental status** -- Claude Code Agent Teams is experimental (INT-009). No session resumption means teammate crashes lose state. This is acknowledged but could cause issues in long builds.

3. **asyncio.run() nesting** -- The existing codebase has a known issue with nested `asyncio.run()` calls (noted in MEMORY.md). Build 2 adds more async functions that may trigger this. Not addressed in the PRD.

4. **Timeout enforcement gap** -- startup_timeout_ms and tool_timeout_ms are defined in config but have no corresponding implementation requirement (ISSUE-B2-008). MCP calls could hang.

### What's Missing (but acceptable)

1. **No performance benchmarks** -- No requirements for MCP call latency targets or throughput. Acceptable for an upgrade PRD.
2. **No monitoring/observability** -- No requirements for MCP call metrics, error rate tracking, or health dashboards. Build 3 handles system-level observability.
3. **No migration guide** -- No explicit guide for upgrading from v14.0 to Build 2. Acceptable because backward compatibility ensures no breaking changes.

---

## Cross-Build Compatibility Analysis

### Build 1 -> Build 2 (Consumption)

| Build 1 Output | Build 2 Consumer | Status |
|----------------|------------------|--------|
| Contract Engine MCP (9 tools) | ContractEngineClient (6 tools) | CORRECT -- remaining 3 consumed by Build 3 |
| Codebase Intelligence MCP (7 tools) | CodebaseIntelligenceClient (7 tools) | CORRECT |
| Architect MCP (4 tools) | ArchitectClient (4 tools via INT-003) | PARTIALLY SPECIFIED -- no dedicated REQ/TECH/TEST |
| spec_hash computation | ContractInfo.spec_hash | **MISMATCH** -- separators differ (ISSUE-B2-002) |
| MCP tool parameter schemas | Client method signatures | MOSTLY CORRECT -- SVC-009/010 missing fields |

### Build 2 -> Build 3 (Production)

| Build 2 Output | Build 3 Consumer | Status |
|----------------|------------------|--------|
| STATE.json with `summary` dict | BuilderResult construction (REQ-048/TECH-031) | CORRECT -- TECH-031 specifies summary fields |
| CONTRACTS.json local cache | Build 3 Integrator contract_compliance.py | CORRECT |
| CONTRACT_COMPLIANCE_MATRIX.md | Build 3 Quality Gate Layer 2 | CORRECT |
| CLAUDE.md for teammates | Build 3 Builder dispatch | CORRECT |
| RunState serialization | Build 3 pipeline resume | CORRECT |

---

## Recommendations

### Must Fix (before implementation)

1. **ISSUE-B2-001** (CRITICAL): Change REQ-012 TeammateIdle hook from agent-type to command-type.
2. **ISSUE-B2-002** (HIGH): Align spec_hash computation between Build 1 and Build 2.
3. **ISSUE-B2-004** (HIGH): Fix TEST-044 truncation threshold to match config default.

### Should Fix (before or during implementation)

4. **ISSUE-B2-003** (HIGH): Fix Cross-Build Dependencies table tool count.
5. **ISSUE-B2-005** (HIGH): Add missing parameters to SVC-010.
6. **ISSUE-B2-006** (HIGH): Add circular_deps to SVC-009 response.
7. **ISSUE-B2-007** (HIGH): Align SVC-001 checkbox with table.
8. **ISSUE-B2-008** (HIGH): Add timeout application requirements or mark as placeholders.

### Nice to Fix (can be deferred)

9. **ISSUE-B2-009** through **ISSUE-B2-017**: Medium and Low issues that add clarity but won't block implementation.

---

*Report generated by BUILD 2 AUDITOR. All findings verified against official documentation and cross-referenced with Build 1 and Build 3 PRDs.*
