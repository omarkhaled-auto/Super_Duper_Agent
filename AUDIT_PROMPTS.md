# AUDIT_PROMPTS.md -- Prompt Readiness Audit for Super Agent Team PRD Runs

**Auditor:** prompt-auditor agent
**Date:** 2026-02-15
**File:** `src/agent_team/agents.py` (2744 lines)
**Supporting:** `src/agent_team/code_quality_standards.py` (665 lines)
**PRDs reviewed:** BUILD1, BUILD2, BUILD3, RUN4

---

## Executive Summary

The prompt system in `agents.py` is **PRODUCTION READY** for the 4 Super Agent Team PRD runs, with **3 MEDIUM** findings, **5 LOW** findings, and **0 CRITICAL/HIGH** issues. The prompts are comprehensive, well-structured, and cover all requirement types. The main concerns are around prompt size under extreme conditions and a few missing domain-specific patterns.

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 0 | - |
| HIGH | 0 | - |
| MEDIUM | 3 | Prompt size risk, missing Python backend patterns, no MCP-specific guidance |
| LOW | 5 | Minor gaps in domain coverage, redundant instructions |
| INFO | 4 | Observations with no action needed |

---

## 1. Decomposition Prompt (`build_decomposition_prompt`, lines 2012-2157)

### 1.1 Milestone Handling (6-8 milestones)
**PASS** -- The decomposition prompt does not impose a milestone count limit. It instructs the orchestrator to "Synthesize outputs into MASTER_PLAN.md with ordered milestones" (line 2144) and creates per-milestone REQUIREMENTS.md files (line 2145). The milestone parser in `milestone_manager.py` handles arbitrary counts via regex.

### 1.2 Dependency Ordering
**PASS** -- The MASTER_PLAN.md format includes `Dependencies: none | milestone-N` fields (lines 2131-2134). The milestone parser preserves ordering. Parallel milestone annotations (M2+M3) are supported at the parser level.

### 1.3 Write Tool Enforcement
**PASS** -- Lines 2098-2119 explicitly enforce Write tool usage for analysis files in chunked mode: "Each planner MUST use the Write tool to persist their analysis" and "CRITICAL: Each planner MUST call the Write tool to create their analysis file."

### 1.4 Parallel Milestone Annotations
**PASS** -- The format supports `Dependencies: milestone-1, milestone-2` which the parser handles. However, the prompt does not explicitly mention "parallel" annotations or M2+M3 notation. This is handled implicitly through the dependency graph.

### 1.5 BUILD3 Complex State Machine Descriptions
**PASS** -- The decomposition prompt is generic enough to handle any PRD content. BUILD3's AsyncMachine/state machine descriptions will be passed as raw PRD text. The planner fleet (10+ planners) will parse them as technical requirements. No special state machine handling is needed at the decomposition level.

### 1.6 Chunked vs Standard Mode
**PASS** -- Lines 2086-2156 correctly branch between chunked (large PRDs >50KB) and standard mode. Both paths enforce the ## header format requirement.

**Verdict: PASS -- No issues found.**

---

## 2. Orchestrator Prompt (`build_orchestrator_prompt`, lines 2450-2744)

### 2.1 Nine-Step Workflow
**PASS** -- Section 7 (lines 551-616) defines the complete 9-step workflow: 0. Interview, 1. Depth detection, 2. Planning, 2.5. Spec validation, 3. Research, 3.5. Architecture, 3.7. UI Design System, 4. Task assignment, 4.5. Contract generator, 5. Convergence loop, 6. Testing, 7. Security audit, 8. Final check, 9. Completion.

### 2.2 Tech Research Context
**PASS** -- Lines 2513-2536 inject tech research content with `[TECH STACK BEST PRACTICES -- FROM DOCUMENTATION]` and Context7 live research instructions.

### 2.3 ZERO MOCK DATA POLICY
**PASS** -- The MOCK DATA GATE is embedded in Section 7 step 5.a2 (lines 597-605) and reinforced in the convergence loop instructions.

### 2.4 UI DESIGN SYSTEM SETUP
**PASS** -- Step 3.7 (lines 565-582) includes detailed instructions for design system setup with framework-specific guidance (React/Next.js, Angular, Vue/Nuxt, Vanilla).

### 2.5 Prompt Size Concern
**[MEDIUM] M-001: Prompt size may approach limits for complex PRDs**
- **Lines:** 2450-2744 (orchestrator prompt builder) + ORCHESTRATOR_SYSTEM_PROMPT (lines 28-652, ~25KB)
- **Issue:** The orchestrator system prompt is ~25KB. The task prompt adds: codebase map summary (variable, can be 5-20KB), UI standards (~5KB), tech research content (variable, 2-10KB), design reference content (variable), interview document (variable, can be 5-50KB for COMPLEX scope), constraints, PRD chunk index, schedule info, and v10 enforcement blocks (~3KB). For a BUILD3-class PRD with large codebase map + tech research + interview doc, total prompt could reach 80-100KB.
- **Risk:** Not a context window overflow (Claude handles 200K tokens), but a signal-to-noise ratio problem. The orchestrator may lose focus on critical instructions buried in a large prompt.
- **Recommendation:** Consider conditional injection -- omit UI standards for pure backend builds (BUILD1, BUILD3), omit design reference for non-UI PRDs. Currently UI standards are ALWAYS injected (line 2502).

### 2.6 v10 Convergence Loop Enforcement
**PASS** -- Lines 2636-2685 add strong convergence loop enforcement with explicit steps and the requirement marking ownership policy. This addresses the rubber-stamp anti-pattern.

### 2.7 Root-Level Artifact Generation
**PASS** -- Lines 2623-2634 mandate root-level REQUIREMENTS.md, TASKS.md, and CONTRACTS.json for PRD mode. This ensures post-orchestration scans have data to work with.

**Verdict: 1 MEDIUM finding (prompt size).**

---

## 3. Milestone Execution Prompt (`build_milestone_execution_prompt`, lines 2160-2447)

### 3.1 Requirement Type Coverage
**PASS** -- The 9-step MILESTONE WORKFLOW (lines 2328-2381) covers:
- REQ-xxx: Step 5 (coding fleet)
- TECH-xxx: Step 5 (coding fleet)
- WIRE-xxx: Step 5 + Step 6 (review fleet verifies wiring)
- TEST-xxx: Step 8 (testing fleet)
- SVC-xxx: Step 3 (architecture) + Step 6 (review fleet)
- INT-xxx: Covered via WIRE-xxx decomposition
- SEC-xxx: Not explicitly listed in milestone workflow but handled by security auditor agent

### 3.2 Review Recovery Loop
**PASS** -- Step 7 (line 2372): "If any items still [ ] -> deploy DEBUGGER FLEET -> re-review -> repeat". The CLI's `_run_review_only()` handles the actual recovery loop.

### 3.3 TASK ASSIGNER Instructions
**PASS** -- Step 4 (lines 2339-2362) includes detailed TASK ASSIGNER instructions with the exact block format specification for TASKS.md, including the `### TASK-NNN:` header, Status, Depends-On, Files, Requirements fields.

### 3.4 Code Quality Standards Inclusion
**PASS** -- Quality standards are injected into each agent's prompt at build time (lines 1984-1987 in `build_agent_definitions`). The milestone execution prompt doesn't need to re-inject them.

### 3.5 Tech Research Content
**PASS** -- Lines 2243-2258 inject both global tech research and milestone-specific research with appropriate priority instructions.

### 3.6 Integration Verification
**PASS** -- Lines 2424-2445 mandate cross-milestone integration verification for milestones with predecessors, including SVC-xxx wiring, DTO alignment, and mock data detection.

### 3.7 Predecessor Handoff Data Injection (FINDING-029)
**PASS** -- Lines 2216-2240 inject actual predecessor handoff data directly into the prompt, with instructions to use EXACT endpoint paths, field names, and enum values.

### 3.8 Context7 Research During Execution
**PASS** -- Lines 2261-2282 provide detailed Context7 usage instructions for the milestone executor.

**Verdict: PASS -- No issues found.**

---

## 4. Code Writer Prompt (CODE_WRITER_PROMPT, lines 1005-1187)

### 4.1 ZERO MOCK DATA POLICY
**PASS** -- Lines 1032-1067 contain an exhaustive mock data policy covering:
- RxJS patterns (`of()`, `delay()`)
- Promise patterns (`Promise.resolve()`)
- Variable naming patterns (mock*, fake*, dummy*, sample*)
- BehaviorSubject patterns
- Hardcoded counts for badges/notifications
- Framework-specific HTTP call requirements (Angular, React, Vue/Nuxt, Python)

### 4.2 API CONTRACT COMPLIANCE
**PASS** -- Lines 1050-1067 mandate exact field name matching from SVC-xxx entries, including C# PascalCase-to-camelCase mapping.

### 4.3 UI COMPLIANCE POLICY and Backend PRDs
**[LOW] L-001: UI compliance policy is always injected even for pure backend builds**
- **Lines:** 1093-1116
- **Issue:** The UI-FAIL-001..007 rules and UI compliance workflow are always present in CODE_WRITER_PROMPT. For BUILD1 (pure backend MCP servers) and BUILD3 (pure backend CLI/orchestrator), these ~24 lines are irrelevant noise.
- **Impact:** Minimal -- the policy is gated by "When UI_REQUIREMENTS.md exists" (line 1094), so it's self-disabling. But it adds prompt length for no benefit.
- **Recommendation:** No action needed -- the conditional check inside the prompt is sufficient.

### 4.4 FRONT-019/020/021 Relevance for Backend Builds
**[INFO] I-001: Frontend standards injected for all code-writer agents**
- **Lines:** `build_agent_definitions` line 1987 injects `get_standards_for_agent("code-writer")` which includes FRONTEND_STANDARDS, BACKEND_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS, SILENT_DATA_LOSS_STANDARDS, ENDPOINT_XREF_STANDARDS.
- **Issue:** Pure backend builds (BUILD1, BUILD3) get frontend standards injected. For BUILD1 (Python FastAPI MCP servers), FRONT-001..021 are irrelevant.
- **Impact:** Minimal -- standards are reference material, not binding instructions. The agent will naturally focus on backend standards for backend code.
- **Recommendation:** Consider `get_standards_for_agent("code-writer", project_type="backend")` to filter irrelevant standards. But the ROI is low.

### 4.5 Prompt Size for Simple Milestones
**[LOW] L-002: CODE_WRITER_PROMPT is ~180 lines regardless of milestone complexity**
- **Lines:** 1005-1187
- **Issue:** Every code-writer gets the full 180-line prompt including mock data policy, API contract compliance, UI compliance, seed data completeness, enum/status registry, validation middleware, DRY utilities, transaction safety, route parameter validation. For a simple milestone like "set up project scaffold" (BUILD1 Milestone 1), most of this is irrelevant.
- **Impact:** Low -- code-writers ignore irrelevant sections. Claude handles long prompts well.
- **Recommendation:** No action needed.

### 4.6 MCP Pattern Guidance for BUILD1
**[MEDIUM] M-002: No MCP-specific coding patterns in code-writer prompt**
- **Lines:** CODE_WRITER_PROMPT (1005-1187)
- **Issue:** BUILD1 requires code-writers to implement MCP servers using `mcp>=1.25,<2` with `@mcp.tool()` decorators, stdio transport, and the high-level MCPServer API. The code-writer prompt has no MCP-specific guidance. It knows HTTP patterns (Angular HttpClient, React fetch, Python requests) but not MCP patterns.
- **Impact:** Medium -- code-writers will rely on Context7 research (injected by the milestone executor) and the PRD itself for MCP patterns. This is the intended flow (tech research -> prompt injection -> code writer reads it). However, the code-writer has no baseline awareness of MCP patterns, so if tech research is thin, it falls back on training data which may be outdated.
- **Recommendation:** Add to CODE_WRITER_PROMPT a brief note: "For MCP server implementations, follow the exact patterns from tech research content. Key patterns: `@mcp.tool()` decorator, `MCPServer` class, `stdio_server()` transport, `tool()` return types. Do NOT use deprecated FastMCP patterns." This is ~4 lines and prevents training data staleness.

### 4.7 Python Backend Patterns
**[MEDIUM] M-003: Missing Python-specific backend patterns**
- **Lines:** CODE_WRITER_PROMPT (1005-1187)
- **Issue:** The code-writer prompt has framework-specific HTTP call examples for Angular, React, Vue/Nuxt, and Python (line 1043: `requests.get` / `httpx.get`). But BUILD1/BUILD3 require extensive Python patterns not covered:
  - `asyncio.to_thread()` for wrapping synchronous calls (BUILD1 architectural principle, line 24 of BUILD1 PRD)
  - FastAPI dependency injection patterns
  - SQLAlchemy async session management
  - Pydantic model validation patterns
  - `async def` vs `def` endpoint handler distinction
  These are critical for BUILD1 (all 3 services use FastAPI) and BUILD3 (super orchestrator, integrator, quality gate).
- **Impact:** Medium -- again, tech research will inject relevant patterns. But unlike frontend frameworks (which have explicit anti-patterns FRONT-001..021), Python backend patterns have no equivalent explicit list.
- **Recommendation:** The existing BACK-001..020 standards cover generic backend patterns. Python-specific patterns should come from tech research (Context7 FastAPI docs). No code change needed, but the gap should be noted. The system's design (tech research -> prompt injection) compensates.

**Verdict: 1 MEDIUM (MCP patterns), 1 MEDIUM (Python patterns), 2 LOW.**

---

## 5. Code Reviewer Prompt (CODE_REVIEWER_PROMPT, lines 1189-1498)

### 5.1 Quality Gates
**PASS** -- The reviewer checks:
- Functional requirements (lines 1197-1209)
- Integration/wiring verification (lines 1255-1265)
- SVC-xxx wiring verification (lines 1267-1297)
- API contract field verification (lines 1279-1297)
- Endpoint cross-reference verification (lines 1299-1306)
- UI compliance (lines 1308-1322)
- Seed data verification (lines 1324-1333)
- Enum/status registry verification (lines 1335-1356)
- Silent data loss prevention (lines 1358-1370)
- Orphan detection (lines 1372-1390)
- Mock data detection (lines 1392-1416)
- Design quality review (lines 1418-1458)
- Code quality review (lines 1460-1480)
- CODE CRAFT REVIEW (lines 1482-1493)

### 5.2 API Contract Field Verification
**PASS** -- Lines 1279-1297 define API-001, API-002, API-003 verification with explicit field-level checks.

### 5.3 Mock Data Detection
**PASS** -- Lines 1392-1416 define comprehensive mock data detection with pattern scan and cross-reference.

### 5.4 BUILD-Scale Calibration (60+ Requirements per Milestone)
**[LOW] L-003: No guidance on review prioritization for large milestones**
- **Lines:** 1189-1498
- **Issue:** BUILD1 Milestone 2 has 49 requirements. BUILD3 milestones may have 60+. The reviewer prompt instructs "For EACH unchecked item" (line 1197) but doesn't provide prioritization guidance for large batches. A reviewer processing 60 items may run out of context or lose quality on later items.
- **Impact:** Low -- the orchestrator deploys multiple reviewers (depth-scaled fleet), so each reviewer handles a subset. The prompt says "EACH unchecked item" which is correct within a reviewer's assigned scope.
- **Recommendation:** No change needed. The fleet scaling handles this.

### 5.5 Silent Data Loss Prevention
**PASS** -- SDL-001, SDL-002, SDL-003 (lines 1358-1370) are well-defined and cover CQRS persistence, response consumption, and silent guards. These are particularly relevant for BUILD3's command handler patterns.

### 5.6 Endpoint Cross-Reference
**PASS** -- XREF-001, XREF-002, API-004 (lines 1299-1306) cover missing endpoints, method mismatches, and write-side field drops.

**Verdict: PASS -- 1 LOW finding.**

---

## 6. Architect Prompt (ARCHITECT_PROMPT, lines 836-1003)

### 6.1 EXACT FIELD SCHEMAS IN SVC-xxx TABLE
**PASS** -- Lines 936-952 mandate exact field names and types in SVC-xxx entries, not just class names. Includes C# PascalCase-to-camelCase mapping, nested object notation, and array notation.

### 6.2 Seed Data Completeness Policy
**PASS** -- Lines 955-977 define the Status/Enum Registry with ENUM-001, ENUM-002, ENUM-003 violation IDs and cross-layer representation requirements.

### 6.3 BUILD3 Complex Architecture
**PASS** -- The architect prompt is generic enough to handle BUILD3's complex architecture (state machine, Docker orchestration, Traefik, 4-layer quality gate). The key patterns (error handling hierarchy, dependency flow, feature grouping, caching strategy) are all covered in lines 901-908.

### 6.4 Endpoint Completeness Verification
**PASS** -- Lines 996-1002 mandate ENDPOINT COMPLETENESS VERIFICATION for every SVC-xxx row.

### 6.5 .NET Serialization Configuration
**PASS** -- Lines 980-985 include .NET JsonStringEnumConverter guidance. This is relevant for RUN4 if test services use .NET, but all 4 PRDs use Python/FastAPI, so this section is informational but not harmful.

### 6.6 Milestone Handoff Preparation
**PASS** -- Lines 987-994 mandate endpoint documentation with exact field names and types for milestone handoff.

**Verdict: PASS -- No issues found.**

---

## 7. Prompt Size Analysis

### 7.1 Component Sizes (Estimated)

| Component | Size (chars) | Size (tokens ~4c/t) |
|-----------|-------------|---------------------|
| ORCHESTRATOR_SYSTEM_PROMPT | ~25,000 | ~6,250 |
| CODE_WRITER_PROMPT + standards | ~12,000 | ~3,000 |
| CODE_REVIEWER_PROMPT + standards | ~14,000 | ~3,500 |
| ARCHITECT_PROMPT + standards | ~8,000 | ~2,000 |
| PLANNER_PROMPT | ~4,500 | ~1,125 |
| TASK_ASSIGNER_PROMPT | ~5,000 | ~1,250 |
| UI_DESIGN_STANDARDS | ~5,000 | ~1,250 |
| Investigation protocol (if enabled) | ~3,000 | ~750 |
| Sequential thinking (if enabled) | ~2,500 | ~625 |
| Orchestrator ST instructions | ~3,000 | ~750 |

### 7.2 Maximum Orchestrator Prompt (BUILD3, Exhaustive Depth)

| Injection | Size (tokens) |
|-----------|---------------|
| System prompt | ~6,250 |
| Codebase map summary | ~3,000 |
| UI standards | ~1,250 |
| Tech research content | ~2,500 |
| Context7 instructions | ~400 |
| Interview/PRD content | ~8,000 |
| v10 enforcement blocks | ~1,500 |
| Constraints | ~200 |
| Schedule info | ~500 |
| Total | **~23,600** |

**Assessment:** At ~24K tokens for the maximum case, this is well within Claude's context window (200K tokens for Opus). Even with a 100K-token response budget, there's ample room. **No context window overflow risk.**

**Signal-to-noise concern:** The orchestrator receives ~24K tokens of instructions + context. For a skilled orchestrator (Claude Opus), this is manageable. The structured section headers ([PHASE:], [DEPTH:], [INSTRUCTIONS]) help parsing. **No action needed.**

### 7.3 Maximum Sub-Agent Prompt (CODE_REVIEWER, Investigation + ST)

| Injection | Size (tokens) |
|-----------|---------------|
| Original user request | ~2,000 |
| CODE_REVIEWER_PROMPT | ~3,500 |
| Quality standards (review + DB + API + SDL) | ~3,000 |
| Investigation protocol | ~750 |
| Sequential thinking | ~625 |
| Constraints | ~200 |
| Total | **~10,075** |

**Assessment:** Sub-agent prompts are much smaller. Well within limits.

---

## 8. Super Agent Team Specific Concerns

### 8.1 BUILD1: Python/FastAPI MCP Servers
**[MEDIUM -- already covered as M-002/M-003]**
- MCP patterns not in code-writer prompt baseline
- Python-specific async patterns not in anti-pattern list
- **Mitigation:** Tech research phase (v14.0) will inject Context7 documentation for FastAPI, MCP SDK, ChromaDB, tree-sitter, etc. The milestone executor has Context7 live access (lines 2261-2282).
- **Risk level:** LOW after tech research injection. The system's design compensates.

### 8.2 BUILD2: Claude Code Hooks
**[INFO] I-002: Hook API patterns not in prompts (by design)**
- BUILD2 requires implementing Claude Code hooks (agent, command, prompt types) and Agent Teams (TaskCreate, TaskUpdate, SendMessage).
- These patterns are NOT in the code-writer prompt and SHOULD NOT be -- they are project-specific implementation details that belong in the PRD and tech research, not in generic agent prompts.
- **Assessment:** CORRECT DESIGN. The code-writer reads REQUIREMENTS.md (which contains BUILD2's PRD) and tech research (which contains hook API docs). No prompt change needed.

### 8.3 BUILD3: pact-python v3, AsyncMachine, Docker
**[INFO] I-003: Domain-specific libraries handled by tech research**
- pact-python v3 (consumer-driven contracts), transitions AsyncMachine (state machine), Docker Compose subprocess management, Traefik config generation, Schemathesis (property-based testing).
- None of these are in the code-writer prompt. This is correct -- they are handled by:
  1. TechResearchConfig: `detect_tech_stack()` will detect Python, FastAPI, Docker from BUILD3's project files
  2. `build_research_queries()` will generate queries for pact-python, transitions, schemathesis
  3. Context7 will provide current documentation
  4. Milestone executor injects tech research into sub-agent context
- **Assessment:** CORRECT DESIGN. No prompt change needed.

### 8.4 RUN4: Verification/Audit (Non-Build PRD)
**[LOW] L-004: Orchestrator prompt assumes "build" paradigm**
- **Lines:** ORCHESTRATOR_SYSTEM_PROMPT Section 3 (convergence loop), Section 4 (PRD mode)
- **Issue:** RUN4 is a verification/audit run, not a build. It tests integration between 3 pre-built systems, runs E2E tests, and produces audit reports. The orchestrator prompt's convergence loop assumes "deploy coding fleet -> deploy review fleet -> mark requirements [x]". For RUN4, the "coding" is actually "fix integration issues" and "write test infrastructure", and the "review" is actually "run integration tests and verify results".
- **Impact:** Low -- the orchestrator is intelligent enough to map "write integration tests" to the coding fleet pattern and "verify results" to the review fleet pattern. RUN4's PRD is explicit about what needs to happen.
- **Recommendation:** No change needed. The prompt is generic enough that RUN4 maps naturally.

### 8.5 RUN4: Cross-Build Interface Verification
**[LOW] L-005: No explicit "verification run" mode in orchestrator**
- **Issue:** RUN4 needs to verify interfaces between BUILD1, BUILD2, and BUILD3. The orchestrator has milestone execution mode and standard mode, but no "verification" mode. RUN4 will run as a standard PRD with milestones.
- **Impact:** Low -- RUN4's PRD defines its own milestones (MCP Wiring, E2E Testing, Docker Orchestration, Audit Scoring). The milestone execution flow handles this correctly.
- **Recommendation:** No change needed.

---

## 9. Additional Observations

### 9.1 Code Quality Standards Coverage
**[INFO] I-004: Standards map is comprehensive**
```python
_AGENT_STANDARDS_MAP = {
    "code-writer": [FRONTEND, BACKEND, DATABASE, API_CONTRACT, SDL, XREF],
    "code-reviewer": [CODE_REVIEW, DATABASE, API_CONTRACT, SDL],
    "test-runner": [TESTING, E2E_TESTING],
    "debugger": [DEBUGGING],
    "architect": [ARCHITECTURE, DATABASE, XREF],
}
```
All critical agents have appropriate standards. The reviewer gets SDL (silent data loss) which is particularly important for BUILD3's command handlers.

### 9.2 Constraint Injection
**PASS** -- Lines 1976-1981 inject user constraints into ALL agent prompts. Lines 2738-2742 inject them into the orchestrator task prompt. This double injection ensures constraints are visible at both system prompt and task prompt levels.

### 9.3 Investigation Protocol Integration
**PASS** -- Lines 1990-2007 inject investigation protocol and sequential thinking into review agents based on config. This is correctly gated by `config.investigation.enabled` and `config.investigation.sequential_thinking`.

### 9.4 Spec Validator
**PASS** -- Lines 728-772 define a comprehensive spec validator that checks missing technologies, features, architecture layers, test requirements, and scope reduction. This prevents the common "planner simplifies the user's request" failure.

---

## 10. Findings Summary

| ID | Severity | Component | Line(s) | Finding | Action |
|----|----------|-----------|---------|---------|--------|
| M-001 | MEDIUM | build_orchestrator_prompt | 2502 | UI standards always injected, even for pure backend PRDs | Consider conditional injection based on project type |
| M-002 | MEDIUM | CODE_WRITER_PROMPT | 1005-1187 | No MCP-specific coding patterns | Add ~4 lines of MCP pattern guidance |
| M-003 | MEDIUM | CODE_WRITER_PROMPT | 1005-1187 | No Python-specific backend patterns (asyncio.to_thread, FastAPI DI) | Covered by tech research; document the gap |
| L-001 | LOW | CODE_WRITER_PROMPT | 1093-1116 | UI compliance policy always present for backend builds | Self-gating via UI_REQUIREMENTS.md check; no action |
| L-002 | LOW | CODE_WRITER_PROMPT | 1005-1187 | Full 180-line prompt for simple milestones | No action; Claude handles long prompts |
| L-003 | LOW | CODE_REVIEWER_PROMPT | 1189-1498 | No prioritization for 60+ requirement batches | Fleet scaling handles this |
| L-004 | LOW | ORCHESTRATOR_SYSTEM_PROMPT | 28-652 | Prompt assumes "build" paradigm; RUN4 is verification | Generic enough to handle verification runs |
| L-005 | LOW | build_orchestrator_prompt | 2450-2744 | No explicit "verification run" mode | RUN4 maps to milestone execution naturally |

### Findings NOT requiring action:
- I-001: Frontend standards injected for backend code-writers (self-ignoring)
- I-002: Hook API patterns not in prompts (correct design -- tech research handles)
- I-003: Domain-specific libraries handled by tech research (correct design)
- I-004: Standards map is comprehensive (positive observation)

---

## 11. Recommendations (Priority Ordered)

### Priority 1: Consider for immediate action
None. All findings are MEDIUM or below and the system's existing design (tech research -> prompt injection) compensates for the gaps.

### Priority 2: Consider for next version
1. **M-001**: Add `project_type` parameter to `build_orchestrator_prompt` to conditionally skip UI standards injection for backend-only builds. This saves ~1,250 tokens per prompt.
2. **M-002**: Add a brief MCP pattern note to CODE_WRITER_PROMPT (~4 lines).
3. **M-003**: Document that Python-specific patterns rely on tech research injection.

### Priority 3: Backlog
4. **L-001 through L-005**: No action recommended. These are architectural observations, not bugs.

---

## 12. Conclusion

The prompt system is **well-designed and production-ready** for all 4 Super Agent Team PRD runs. The key strengths are:

1. **Comprehensive coverage** -- Every requirement type (REQ, TECH, WIRE, TEST, SVC, INT, SEC, DESIGN, ENUM, SEED, DB, API, XREF, SDL) has corresponding instructions in at least one prompt.
2. **Layered enforcement** -- Policies are enforced at 3 levels: code-writer (prevention), code-reviewer (detection), and CLI (static scan + fix loop).
3. **Tech research compensation** -- Domain-specific patterns (MCP, pact-python, AsyncMachine) are intentionally handled by the tech research phase, not hardcoded in prompts. This is the correct design for a generic orchestration system.
4. **Convergence loop integrity** -- v10 enforcement blocks (lines 2636-2685) prevent rubber-stamping and ensure review fleet deployment.
5. **Backward compatibility** -- All injections are conditional and crash-isolated.

The 3 MEDIUM findings (M-001, M-002, M-003) represent optimization opportunities, not blockers. The system will function correctly for BUILD1, BUILD2, BUILD3, and RUN4 as-is.
