# RUN4_PRD.md Format Compliance Review

> **Reviewed**: 2026-02-15
> **PRD File**: `prompts/RUN4_PRD.md` (642 lines)
> **Specification**: agent-team v14.0 PRD format (BUILD3_CODEBASE_RESEARCH.md)
> **Verdict**: **PASS** (0 CRITICAL, 0 HIGH, 2 MEDIUM, 2 LOW)

---

## Check 1: Milestone Headers

**Result: PASS**

All 6 milestone headers match regex `^#{2,4}\s+(?:Milestone\s+)?(\d+)[.:]?\s*(.*)`:

| Line | Header | Match |
|------|--------|-------|
| 123 | `## Milestone 1: Test Infrastructure + Fixtures` | PASS |
| 187 | `## Milestone 2: Build 1 -> Build 2 MCP Wiring Verification` | PASS |
| 265 | `## Milestone 3: Build 2 -> Build 3 Wiring Verification` | PASS |
| 304 | `## Milestone 4: End-to-End Pipeline Test` | PASS |
| 341 | `## Milestone 5: Fix Pass + Defect Remediation` | PASS |
| 365 | `## Milestone 6: Audit Report + Final Verification` | PASS |

All use `##` (h2) consistently. The `## Milestone Structure` header on line 121 does NOT match the milestone regex (no number) so it will not be parsed as a milestone -- correct behavior.

---

## Check 2: Milestone Fields (ID, Status, Dependencies)

**Result: PASS**

| Milestone | ID | Status | Dependencies | Valid |
|-----------|-----|--------|-------------|-------|
| M1 (L125-128) | milestone-1 | PENDING | none | PASS |
| M2 (L189-192) | milestone-2 | PENDING | milestone-1 | PASS |
| M3 (L267-270) | milestone-3 | PENDING | milestone-1 | PASS |
| M4 (L306-309) | milestone-4 | PENDING | milestone-2, milestone-3 | PASS |
| M5 (L343-346) | milestone-5 | PENDING | milestone-4 | PASS |
| M6 (L367-370) | milestone-6 | PENDING | milestone-5 | PASS |

All fields present. Dependency chain is valid (no circular dependencies, no references to non-existent milestones). M4 correctly depends on both M2 and M3 (parallel tracks converge).

---

## Check 3: Checklist Format — `(review_cycles: N)` Suffix

**Result: PASS**

All 119 checklist items end with `(review_cycles: 0)`. Every item uses `- [ ] ` with proper space in brackets (not `[]` or `[-]`). No exceptions found.

Note: All items use `review_cycles: 0`. This is valid for a verification/audit run where tests serve as verification rather than code review cycles.

---

## Check 4: Prefix Numbering — Sequential, No Gaps, No Duplicates

**Result: PASS**

| Prefix | Range | Milestones | Sequential |
|--------|-------|------------|-----------|
| REQ-xxx | 001-042 | M1(001-008), M2(009-015), M3(016-020), M4(021-028), M5(029-033), M6(034-042) | PASS (42 items, no gaps) |
| TECH-xxx | 001-009 | M1(001-003), M4(004-006), M5(007-008), M6(009) | PASS (9 items, no gaps) |
| INT-xxx | 001-007 | M1(001-007) | PASS (7 items, no gaps) |
| WIRE-xxx | 001-020 | M2(001-012), M3(013-016), M4(017-020) | PASS (20 items, no gaps) |
| SVC-xxx | 001-020 | M2(001-017), M3(018-020) | PASS (20 items, no gaps) |
| TEST-xxx | 001-018 | M1(001-007), M2(008), M3(009-010), M4(011-012), M5(013-015), M6(016-018) | PASS (18 items, no gaps) |
| SEC-xxx | 001-003 | M4(001-003) | PASS (3 items, no gaps) |

No DESIGN-xxx, DR-xxx, or TASK-xxx used (appropriate for non-UI verification run).

---

## Check 5: SVC Table Column Format

**Result: PASS with MEDIUM note**

### Milestone 2 SVC Table (Lines 196-214)
- **Columns**: 6 (SVC-ID, Client Method, MCP Server, MCP Tool, Request DTO, Response DTO)
- **Format**: Custom MCP wiring format (not standard 7-column HTTP, not Build 2's 5-column MCP)
- **Verdict**: Acceptable. These are MCP tool calls, not HTTP frontend-to-backend APIs. The `_parse_svc_table()` API contract scanner targets the standard 7-column format for HTTP wiring and would not apply to MCP tool wiring. The extra "MCP Server" column adds clarity about which server hosts each tool.

### Milestone 3 SVC Table (Lines 274-278)
- **Columns**: 6 (SVC-ID, Caller, Command, Input, Output, Verification)
- **Format**: Custom subprocess wiring format
- **Verdict**: Acceptable. These are subprocess invocations, not HTTP APIs.

**MEDIUM-1**: Neither SVC table matches the standard 7-column format expected by `_parse_svc_table()` in `quality_checks.py`. The API contract scan will produce zero violations for these tables (backward-compatible behavior for non-standard formats). This is correct behavior since MCP and subprocess wiring don't go through HTTP frontend/backend paths, but worth documenting.

---

## Check 6: DTO Field Notation

**Result: PASS**

All DTOs in the Milestone 2 SVC table use the `{ field: type }` brace notation:

- `{ prd_text: string }` (line 198)
- `DecompositionResult { service_map: dict, domain_model: dict, contract_stubs: list, validation_issues: list }` (line 198)
- `ServiceMap { project_name: string, services: list, generated_at: string }` (line 199)
- All 17 SVC rows follow this pattern consistently.

Milestone 3 SVC table uses prose descriptions instead of DTO notation (appropriate for subprocess I/O).

---

## Check 7: Checklist Item Count Verification

**Result: PASS**

| Prefix | Claimed (Appendix C) | Counted | Match |
|--------|----------------------|---------|-------|
| REQ-xxx | 42 | 42 | PASS |
| TECH-xxx | 9 | 9 | PASS |
| INT-xxx | 7 | 7 | PASS |
| WIRE-xxx | 20 | 20 | PASS |
| SVC-xxx | 20 | 20 | PASS |
| TEST-xxx | 18 | 18 | PASS |
| SEC-xxx | 3 | 3 | PASS |
| **Total** | **119** | **119** | **PASS** |

---

## Check 8: Config.yaml Template

**Result: PASS with MEDIUM note**

### Required Sections Present

| Section | Present | Status |
|---------|---------|--------|
| `depth:` | Yes (thorough) | PASS |
| `milestone:` | Yes (enabled, health_gate, review_recovery_retries) | PASS |
| `post_orchestration_scans:` | Yes (mock_data_scan, ui_compliance_scan, api_contract_scan) | PASS |
| `e2e_testing:` | Yes (enabled, backend_api_tests, frontend_playwright_tests, max_fix_retries) | PASS |
| `browser_testing:` | No | Uses defaults (enabled=False) -- OK for backend-only |
| `orchestrator:` | No | Uses defaults -- OK |
| `convergence:` | No | Uses defaults -- OK |
| `design_reference:` | No | No UI project -- OK |

**MEDIUM-2**: The `run4:` custom section (lines 79-101) contains 15 fields that are not part of the standard `AgentTeamConfig` schema. `_dict_to_config()` will silently ignore these keys. The Run4 codebase would need its own config loader to read these values. This is a design decision, not a parsing error, but the agent-team builder won't have access to these settings unless the Run4 code explicitly reads them from the YAML.

---

## Issue Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 0 | No parsing-breaking issues |
| HIGH | 0 | No ambiguous requirements |
| MEDIUM | 2 | M-1: Non-standard SVC table columns (6 instead of 7); M-2: Custom `run4:` config section not in AgentTeamConfig schema |
| LOW | 2 | L-1: All review_cycles=0 (valid for verification run); L-2: No browser_testing section (defaults to disabled, correct for backend-only) |

---

## Detailed Findings

### MEDIUM-1: Non-Standard SVC Table Column Count (Lines 196-214, 274-278)

**Description**: Both SVC tables use 6 columns instead of the standard 7-column format or Build 2's 5-column MCP format. Milestone 2 uses `SVC-ID | Client Method | MCP Server | MCP Tool | Request DTO | Response DTO` (6 columns). Milestone 3 uses `SVC-ID | Caller | Command | Input | Output | Verification` (6 columns).

**Impact**: The `run_api_contract_scan()` function in `quality_checks.py` will not parse these tables (it expects the standard 7-column HTTP format). This means zero API contract violations will be reported for MCP/subprocess wiring. This is actually correct behavior since these aren't HTTP frontend-to-backend calls, but it means the API contract scan provides no coverage for this PRD.

**Recommendation**: No action needed. The SVC checklist items (SVC-001 through SVC-020) duplicate the table content and will be tracked as regular checklist items. The MCP wiring verification is handled by the test requirements (WIRE-001 through WIRE-012) rather than the API contract scanner.

### MEDIUM-2: Custom `run4:` Config Section (Lines 79-101)

**Description**: The config.yaml template includes a `run4:` top-level key with 15 fields (build paths, Docker settings, MCP timeouts, builder settings, fix pass limits). These fields are not part of `AgentTeamConfig` and will be silently ignored by `_dict_to_config()`.

**Impact**: The agent-team builder cannot access Run4-specific configuration (build paths, health check timeouts, MCP timeouts, etc.) through the standard config loading mechanism. The Run4 code must implement its own config parsing to read these values.

**Recommendation**: This is a deliberate design decision. The `run4:` section serves as documentation for the Run4-specific config that will be parsed by Run4's own `Run4Config` dataclass (REQ-001). The agent-team builder only needs `depth`, `milestone`, `post_orchestration_scans`, and `e2e_testing` sections. No change needed.

### LOW-1: All review_cycles Set to 0 (All 119 items)

**Description**: Every checklist item uses `(review_cycles: 0)`, meaning no items require code review cycles.

**Impact**: The review recovery loop (`review_recovery_retries` in config) will not trigger for any requirement since none request review cycles. This is appropriate for a verification/audit run where the "tests" themselves serve as verification.

### LOW-2: No browser_testing Section in Config (Lines 76-117)

**Description**: The config.yaml template omits the `browser_testing:` section. At depth=thorough with milestones enabled, browser testing would normally be enabled by default.

**Impact**: With no `browser_testing:` section, the default `BrowserTestingConfig(enabled=False)` applies. Since Run 4 has no frontend/UI, browser testing would be skipped anyway (`skip_if_no_frontend` logic). No impact.

---

## Verdict

**PASS** -- The PRD is fully compliant with the agent-team v14.0 format specification. All 6 milestone headers parse correctly, all 119 checklist items have proper format with `(review_cycles: N)` suffixes, all prefix numbering is sequential with no gaps or duplicates, the config template has all required sections, and the claimed totals match the actual counts exactly. The 2 MEDIUM issues are design decisions appropriate for a verification/audit run targeting MCP and subprocess wiring rather than HTTP frontend-backend APIs.
