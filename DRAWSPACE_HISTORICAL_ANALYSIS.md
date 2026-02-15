# DRAWSPACE HISTORICAL ANALYSIS

**Date:** 2026-02-15
**Analyst:** Historical Issue Analyst (Opus 4.6)
**Scope:** DrawSpace V1 (greenfield build) + Canvas Upgrade (existing codebase upgrade)
**Purpose:** Pattern extraction for Super Agent Team PRD runs

---

## 1. Timeline of ALL Runs

### Run 1: DrawSpace V1 (Greenfield Build)
- **Start:** 2026-02-11 ~18:49 UTC+2
- **Config:** exhaustive + PRD + milestones, Opus 4.6
- **PRD:** 90KB, 84 SVC entries, Fabric.js canvas
- **Stack:** .NET 8 / Angular 18 / PostgreSQL / Fabric.js
- **Milestones:** 9 (synthesizer chose 9 instead of PRD's 5)
- **CRITICAL FAILURE at 19:01:** MASTER_PLAN.md used `###` headers (h3) but parser expects `##` (h2) -- ZERO milestones parsed. Build aborted.
- **Manual fix at 19:04:** Killed build, fixed headers h3->h2, cleaned STATE.json, restarted (build ID b58641f)
- **M1-M9 execution:** ~19:04 to ~02:00+ (estimated)
- **Post-orchestration:** Scans, E2E testing (77/77 passed after 6 fix cycles)
- **Browser testing:** SKIPPED (port mismatch: app on 80, config expected 9876)
- **V1 Rubric Score:** 870/1000 (pre-canvas upgrade)
- **Critical Bug:** Canvas entity persistence -- entities don't survive page reload

### Run 2: Canvas Upgrade (Existing Codebase Upgrade)
- **Start:** 2026-02-12 ~13:42 UTC
- **Config:** exhaustive + PRD + milestones, Opus 4.6
- **PRD:** 76KB, 1525 lines, 7 milestones
- **Stack:** Adds Konva.js, Yjs, Hocuspocus, Python/FastAPI export service
- **Baseline:** 345 .cs files, 108 .ts files, 18,674 LOC, 349 tests passing
- **CRITICAL ISSUE at 13:42:** Stale .agent-team from V1 detected (9 greenfield milestones). Stopped, cleaned, relaunched at 13:44.
- **M1 (Bug Fixes):** 13:58-14:45 -- 8 reqs, 7 bugs fixed, 349 tests pass, HEALTHY
- **M2 (Canvas Engine):** 14:45-15:18 -- 71 sub-reqs, Fabric.js removed, Konva.js 4-layer arch, HEALTHY
- **M3 (CAD Tools):** 15:18-17:35 -- 46 sub-reqs, 8 tool files (3308 LOC), snap engine (679L), HEALTHY (2 review cycles)
- **M4 (Layer & Style):** 17:35-19:00 -- 83 sub-reqs, 21 tasks, HEALTHY
- **CRITICAL at 19:50 -- M5-M7 SKIPPED:** `_parse_deps()` choked on parenthetical comment in M5's dependency string. `"milestone-2 (server-side setup can parallel...)"` -- comma-split produced tokens matching no milestone ID -> `get_ready_milestones()` returned empty -> pipeline exited milestone loop. **3 milestones never attempted.**
- **Cost at M4 complete:** $95.66
- **Total cost Run 2 (M1-M4 + post-orch + E2E):** $103.26

### Run 3: Canvas Upgrade RESUMED (M5-M7)
- **Start:** 2026-02-12 ~20:00 UTC
- **Resume from:** M5 (M1-M4 complete in STATE.json)
- **Bug fixes before resume:** (a) `_parse_deps()` strips parenthetical text, (b) `main()` resume path loads existing RunState instead of creating fresh one, (c) `validate_for_resume` needed non-empty task string
- **Previous cost carried:** $103.26
- **M5 (Collaboration):** 20:05-21:30 -- Yjs CRDT, Hocuspocus server, 6 Angular services, Docker multi-service. **F-007: Orchestrator wrote code directly instead of delegating to fleet** (resume context loss).
- **M6 (DXF/DWG Export):** 21:30-22:25 -- 24 coding agents + 3 review agents (largest fleet), Python FastAPI service, HEALTHY
- **M7 (Performance & Polish):** 22:45-23:42 -- 20 tasks, virtual renderer, mini-map, drawing comparison, HEALTHY
- **Post-orchestration scans:** 23:42-00:00+ -- all scans completed (deployment/asset clean, PRD recon 85%, DB scans fixed)
- **E2E Testing:** 77/77 passed (100%) after 6 fix cycles, $8.74
- **Browser Testing:** SKIPPED again (port mismatch 80 vs 9876)
- **Total cost all runs:** ~$112+ (orchestration: $96.57, E2E: $8.74, browser: ~$2, fix pass: ~$7)

### Run 4: Fix Pass (Post-Upgrade Wiring Gap Closure)
- **Start:** 2026-02-13 ~08:10 UTC
- **Mode:** thorough, non-PRD task mode (not milestone mode)
- **Task:** 31-issue fix pass from FIX_PASS_TASK.md (wiring dead code services, symbol library, DXF headers, etc.)
- **Convergence:** 3 review cycles (79.6% -> 88% -> 98.5%)
- **E2E:** 130/130 passed (100%) -- expanded from 77 tests
- **Browser Testing:** SKIPPED AGAIN (same port mismatch)
- **Total run cost:** ~$7

### Run 5: Manual Verification Sessions
- **Full E2E Verification Report (2026-02-15):** 17 test areas, 98% pass rate
- **Canvas Verification Report (2026-02-15):** 14 tools verified, 97% pass

---

## 2. SYSTEMIC Issues (Would Affect Super Agent Team Runs)

### S-1: MASTER_PLAN.md Header Format Mismatch [SEVERITY: CRITICAL]
**V1 Impact:** ZERO milestones parsed, build aborted, required manual intervention.
**Root Cause:** Synthesizer agent used `###` (h3) headers; parser regex expected `##` (h2).
**Fix Applied:** v13 Fix 1 -- `_RE_MILESTONE_HEADER` now accepts `#{2,4}`.
**Risk for Super Agent Team:** LOW (already fixed). But if a new PRD produces unusual MASTER_PLAN formatting, the build could still fail at Phase 1.
**Recommendation:** Validate `parse_master_plan()` returns >0 milestones immediately after synthesis, before entering milestone loop.

### S-2: `_parse_deps()` Parenthetical Text Crash [SEVERITY: CRITICAL]
**Canvas Upgrade Impact:** M5-M7 (3 milestones, ~43% of build) SKIPPED silently. Required code fix + resume.
**Root Cause:** MASTER_PLAN synthesizer added helpful notes like `"milestone-2 (server-side setup can parallel with milestone-3, milestone-4)"`. Comma-split on the parenthetical produced tokens that matched no completed milestone ID -> `get_ready_milestones()` returned empty -> silent exit.
**Fix Applied:** `_parse_deps()` now strips parenthetical text via `re.sub(r'\([^)]*\)', '', raw)`.
**Risk for Super Agent Team:** LOW (fixed in codebase), but the PATTERN is critical: any synthesizer free-text in dependency strings can break parsing. If a new synthesizer format appears (e.g., square brackets, semicolons), the parser may fail again.
**Recommendation:** Add integration test that verifies `_parse_deps` handles all known annotation patterns.

### S-3: Resume State Corruption [SEVERITY: HIGH]
**Canvas Upgrade Impact:** Resume failed initially because `main()` created a FRESH RunState instead of loading the existing one, wiping all milestone progress.
**Fix Applied:** Resume path now loads existing RunState from STATE.json.
**Risk for Super Agent Team:** MEDIUM. Resume is CRITICAL for large builds -- if a Super Agent Team PRD run fails at milestone 6/12, resume must work correctly. Any bug in resume state loading = entire rebuild from scratch.
**Recommendation:** Test resume from every possible interruption point (mid-milestone, between milestones, during post-orchestration scans).

### S-4: Stale .agent-team Directory [SEVERITY: HIGH]
**Canvas Upgrade Impact:** V1's 9-milestone MASTER_PLAN was still present when Canvas Upgrade launched. Would have executed entirely wrong plan.
**V1 Impact:** Also mentioned -- STATE.json from aborted first build needed manual cleanup.
**Risk for Super Agent Team:** HIGH. Super Agent Team runs 4 builds sequentially in the same workspace. Each build MUST start with a clean .agent-team directory. If any build leaves artifacts, the next build may use stale plans.
**Recommendation:** Add automatic `rm -rf .agent-team` before each new PRD run. Or validate that MASTER_PLAN.md content matches current PRD.

### S-5: Browser Testing Port Mismatch [SEVERITY: MEDIUM]
**Impact:** Browser testing SKIPPED in ALL 3 runs (V1, Canvas Upgrade, Fix Pass).
**Root Cause:** App runs on Docker port 80, but `BrowserTestingConfig.app_port` defaults to 9876. Startup agent detects healthy app on 80, but CLI expects 9876.
**Risk for Super Agent Team:** HIGH. Browser testing never ran on Drawspace. It's effectively untested for Docker-based projects.
**Recommendation:** Browser testing port should be configurable in config.yaml AND/OR auto-detected from Docker Compose / APP_STARTUP.md.

### S-6: Review Fleet Empty Outputs (F-004) [SEVERITY: MEDIUM]
**Canvas Upgrade Impact:** Review sub-agents returned empty output files in M4 and M7. Orchestrator compensated with manual spot-checking, but this is weaker review than designed.
**Root Cause:** Sub-agents completed successfully but didn't write their analysis to the output file. Possibly tool call issues or context window pressure.
**Risk for Super Agent Team:** MEDIUM. Weaker reviews = more bugs reaching post-orchestration. For Super Agent Team PRDs (larger milestones), review quality is critical.
**Recommendation:** Add validation gate after review fleet: if ALL review outputs are empty, retry with fresh agents.

### S-7: Orchestrator Self-Coding (F-007) [SEVERITY: MEDIUM]
**Canvas Upgrade Impact:** In M5 (collaboration) and M7 (performance), the orchestrator wrote critical code directly instead of delegating to the coding fleet. Caused by resume context loss -- no TASKS.md for the new milestone, plus orchestrator had deep context from reading all handoffs.
**Risk for Super Agent Team:** MEDIUM-HIGH. Resume + complex milestones = orchestrator may bypass fleet. Fleet parallelism is lost, and code quality depends on single-agent context.
**Recommendation:** Enforce TASKS.md creation as a hard gate before any coding begins, even on resume.

### S-8: Design Direction Inference for Technical Apps [SEVERITY: LOW]
**V1 Impact:** DrawSpace (CAD/construction app) got "minimal_modern" instead of "professional/technical" design direction.
**Risk for Super Agent Team:** LOW. Design direction affects UI tokens but not functionality.

### S-9: Context7 Not Available to Sub-Agents [SEVERITY: LOW]
**Canvas Upgrade Impact:** Tech research Phase 1.5 fell back to WebSearch instead of Context7. TECH_RESEARCH.md still comprehensive but not from primary source.
**Risk for Super Agent Team:** LOW. WebSearch fallback works adequately.

### S-10: XREF False Positive for Absolute Route Overrides [SEVERITY: LOW]
**Canvas Upgrade Impact:** `GET /api/drawings/search` flagged as XREF-001 violation twice. Endpoint exists in `SearchController.cs` with absolute route override `[HttpGet("/api/drawings/search")]` -- scanner only checked `DrawingsController`.
**Risk for Super Agent Team:** LOW for most stacks, but any ASP.NET project using route overrides will hit this.

### S-11: Mock Scan False Positives on setTimeout [SEVERITY: LOW]
**Canvas Upgrade Impact:** Same 3 `setTimeout` calls in measurement tools flagged across M3, M4, and the fix pass. Each time the fix agent correctly identified them as false positives, but burned fix cycles.
**Risk for Super Agent Team:** LOW. Wastes fix cycle time but doesn't produce incorrect code changes.

---

## 3. PRD-SPECIFIC Issues (Unique to Drawspace)

### P-1: Canvas Entity Persistence Bug (V1) [SEVERITY: CRITICAL for V1 rubric]
**Impact:** Entities don't survive page reload. `DrawingEntity` batch API returned empty. Canvas becomes non-functional after reload. Lost 20 rubric points.
**Root Cause:** Backend batch persistence handler had a LayerId FK validation issue.
**Resolution:** Fixed in Canvas Upgrade M1 (Bug Fixes milestone).

### P-2: Status Transition 500 Errors (V1) [SEVERITY: HIGH for V1 rubric]
**Impact:** Project archive/restore, drawing status transitions (Draft->InReview, InReview->Approved) all returned 500. Lost ~25 rubric points.
**Root Cause:** `ActivityLogService.SaveChangesAsync()` throwing inside command handlers.
**Resolution:** Fixed in Canvas Upgrade M1 with try-catch wrapper.

### P-3: Organization Update 500 Error (V1) [SEVERITY: MEDIUM for V1 rubric]
**Impact:** PUT /api/organization returned 500. Lost 5 rubric points.
**Resolution:** Fixed in Canvas Upgrade M1.

### P-4: 9 Milestones Instead of PRD's 5 (V1)
**Impact:** More milestones = more orchestration cycles, longer build time.
**Root Cause:** Synthesizer chose its own logical breakdown instead of following PRD structure.
**Risk for Super Agent Team:** MEDIUM. If synthesizer creates 15 milestones for a 7-milestone PRD, budget and time costs increase proportionally.

### P-5: Recovery Agent "Prompt Injection" Refusal (V1) [SEVERITY: HIGH]
**Impact:** Recovery agent interpreted recovery prompt as "prompt injection attempt" and partially refused instructions.
**Root Cause:** Recovery prompt contained directives like "CRITICAL RECOVERY", "MANDATORY" -- agent's over-caution triggered.
**Resolution:** v13 Fix 3 -- Recovery prompt uses `[PHASE: REVIEW VERIFICATION]` + `[SYSTEM:]` tag, no alarm language.

### P-6: M4 Service-to-Rendering Wiring Gap (Canvas Upgrade)
**Impact:** M4 services (line types, text styles, dimension styles, block manager) scored 7-10 on internal quality but rendering pipeline scored near-zero on consuming them. Dead code services.
**Root Cause:** Parallel execution model -- one agent built services, different agent built rendering, they never communicated.
**Resolution:** Fix Pass (Run 4) wired all dead code services.
**Risk for Super Agent Team:** MEDIUM-HIGH. Inter-agent communication gaps within milestones are a fundamental limitation of the parallel fleet model.

---

## 4. PATTERN Observations

### Pattern 1: First Milestone Always Succeeds
- V1 M1 (Infrastructure): 16/16, HEALTHY, 1 cycle
- Canvas M1 (Bug Fixes): 8/8, HEALTHY, 1 cycle
Both first milestones achieved single-cycle convergence with 100% requirement coverage.

### Pattern 2: Middle Milestones Need Review Cycles
- V1 M2: 59/59, 1 fix cycle (indexes)
- V1 M3: 34/34, 1 fix cycle (IConfiguration)
- V1 M4: 78/78, 1 fix cycle (auth + scoping + logging)
- Canvas M3: 46/46, 2 review cycles (dead code tool files)
- Canvas M4: 83/83, 1 cycle (review empty, spot-checked)
Middle milestones consistently need 1-2 review cycles to reach convergence.

### Pattern 3: Later Milestones Have Weaker Reviews
- Canvas M6: 0 review cycles (zero-cycle milestone)
- Canvas M7: 0 review cycles, review fleet outputs empty
- V1 M8+: Not documented in available logs
Later milestones tend to have weaker review coverage. Either review fleets produce empty outputs or the pipeline skips formal review.

### Pattern 4: Post-Orchestration Scans Work But Are Noisy
- DB-005 (nullable access): Always finds 100+ violations, takes 2-3 fix cycles
- XREF: Produces false positives for route overrides
- Mock scan: Produces false positives for setTimeout/Observable patterns
- Deployment/Asset scans: Usually clean (0 violations)
- PRD Reconciliation: Catches real gaps (85-98% verification rate)

### Pattern 5: E2E Testing Requires Multiple Fix Cycles
- V1 E2E: 6 fix cycles to reach 77/77 (100%)
- Canvas E2E: 77/77 on first inherited run, expanded to 130/130
- Fix Pass E2E: 2 fix cycles to reach 130/130
E2E testing consistently requires 4-6 fix cycles for initial runs. Major blockers: rate limiting (429s), stale test data, PrimeNG selector issues, localStorage access.

### Pattern 6: Builds Compile but Runtime Fails
- V1: Backend compiled with 0 warnings but had 500 errors at runtime (entity persistence, status transitions, org update)
- Canvas M3: Review caught dead code tools -- TypeScript compiled but tools were never called
Build success is NOT a reliable indicator of functional correctness.

### Pattern 7: Handoff Documents Are Comprehensive When Working
- All milestones generated substantial handoff documents
- Completeness gate triggered twice in Canvas M5 (false positive)
- Wiring completeness frequently shows 0/141 (formatting issue, not real)
The handoff system works but the completeness gate has false positive issues.

---

## 5. BUDGET ANALYSIS

### Cost Per Run
| Run | Scope | Cost | Duration |
|-----|-------|------|----------|
| V1 Greenfield | 9 milestones, .NET/Angular/PG | Not tracked (pre-V14) | ~7-8 hours |
| Canvas Upgrade (M1-M4) | 4/7 milestones, existing codebase | $95.66 | ~6 hours |
| Canvas Upgrade Resume (M5-M7) | 3/7 milestones | ~$7 (incremental) | ~4 hours |
| Canvas Upgrade Post-Orch + E2E | Scans + 77 Playwright tests | $8.74 | ~2 hours |
| Fix Pass | 31 issues, 22 tasks, 130 E2E tests | ~$7 | ~3.5 hours |
| **TOTAL Canvas Upgrade** | **7 milestones + scans + E2E + fix pass** | **~$112** | **~15.5 hours** |

### Cost Projections for Super Agent Team
- Canvas Upgrade: 7 milestones, 76KB PRD, ~$112 total
- Per-milestone average: ~$16/milestone
- Super Agent Team PRDs are described as "MUCH larger than Drawspace"
- **Estimated cost per Super Agent Team PRD run: $150-250** (assuming 10-15 milestones per PRD)
- **Total 4 PRD runs: $600-1000**
- **With fix passes and resumed runs: $800-1200**

### Budget Sufficiency
- Claude subscription model (not per-API-call) means cost is primarily in time, not dollars
- The bigger concern is **time**: Canvas Upgrade took ~15.5 hours across all runs
- Super Agent Team runs should budget **20-30 hours per PRD** including monitoring, resumes, and fix passes
- **4 PRDs = 80-120 hours total**

---

## 6. RESUME ANALYSIS

### Why Resumes Were Needed

#### V1 Resume (Build Restart):
- **Cause:** MASTER_PLAN.md header format mismatch (h3 vs h2)
- **Action:** Kill build, fix headers, clean STATE.json, restart
- **Result:** Full restart from M1 (previous artifacts reused: MASTER_PLAN.md, UI_REQUIREMENTS.md, analysis files, prd-chunks)

#### Canvas Upgrade Resume #1 (M5-M7):
- **Cause:** `_parse_deps()` bug choking on parenthetical text in dependency string
- **Action:** Fix `_parse_deps()` code, fix `main()` resume state loading, edit STATE.json task field
- **Result:** Successful resume from M5, M1-M4 correctly skipped

#### Canvas Upgrade Resume #2 (implicit):
- The resumed.log is 48 lines (just the resume banner + tech research). This suggests the first resume attempt failed quickly (possibly due to the `validate_for_resume` issue requiring a non-empty task string), and was immediately re-attempted as resumed2.

### What Worked in Resume
1. **Phase skipping:** Interview, constraints, codebase_map, design_extraction, pre_orchestration all correctly skipped
2. **Milestone skipping:** M1-M4 marked COMPLETE, M5 started as "MILESTONE 5/7"
3. **Artifact reuse:** MASTER_PLAN.md, CONTRACTS.json, UI_REQUIREMENTS.md all reused without regeneration
4. **Tech research re-ran:** Phase 1.5 ran again (non-blocking, enhanced existing TECH_RESEARCH.md)

### What Failed in Resume
1. **STATE.json state loading:** `main()` originally created fresh RunState instead of loading existing one -- wiped all milestone progress
2. **TASKS.md loss:** No TASKS.md existed for M5 on resume, triggering F-007 (orchestrator self-coding)
3. **validate_for_resume:** Required non-empty task string in STATE.json -- manual edit needed
4. **Cost tracking not reset:** Previous cost ($103.26) carried forward correctly, but if the build had been killed uncleanly, cost could have been lost

### Resume Recommendations for Super Agent Team
1. **Pre-validate resume state before entering milestone loop** -- if any required field is missing, error with specific guidance
2. **Create TASKS.md immediately on milestone start** -- even if empty, it prevents F-007
3. **Log exact cost at every milestone boundary** -- enables accurate cost tracking across resumes
4. **Test resume from every milestone boundary** -- automated test that interrupts at each milestone and verifies successful resume

---

## 7. RECOMMENDATIONS for Agent-Team Improvements

### Critical (Block Super Agent Team Success)

**R-1: Auto-detect app port from Docker Compose**
Browser testing failed in ALL Drawspace runs due to port mismatch. For Super Agent Team, this means we have ZERO validation that browser testing works with Docker-based apps.
- Parse docker-compose.yml for published ports
- Set `BrowserTestingConfig.app_port` accordingly
- Or read from APP_STARTUP.md

**R-2: Validate milestone parsing immediately after synthesis**
If `parse_master_plan()` returns 0 milestones, halt and provide clear error BEFORE entering the milestone loop. The V1 silent failure to recover was because the system entered "recovery mode" instead of stopping.

**R-3: Clean .agent-team/ before new PRD runs**
The stale MASTER_PLAN.md issue hit BOTH V1 and Canvas Upgrade. For Super Agent Team running 4 PRDs sequentially, this is a guaranteed collision unless addressed.

### High Priority

**R-4: Validate review fleet outputs**
If ALL review agent output files are empty (F-004 pattern), retry with fresh agents. At least one meaningful review output should be required before marking review as complete.

**R-5: Enforce TASKS.md as hard gate before coding**
Even on resume, even if the orchestrator has deep context, TASKS.md MUST be created before any `Edit` or `Write` tool calls for code files. This prevents F-007 (orchestrator self-coding).

**R-6: Resume integration tests**
Create automated tests that:
- Interrupt build at each milestone boundary
- Verify resume loads correct RunState
- Verify correct milestones are skipped
- Verify cost carries forward
- Verify TASKS.md exists or is created

### Medium Priority

**R-7: Reduce DB-005 noise**
The nullable access scan consistently finds 100+ violations (most are false positives from Angular template bindings like `[style.height.px]`). Consider:
- Excluding Angular template syntax from nullable scanning
- Reducing max violations from 100 to 50
- Adding pattern exclusion list for known false positive patterns

**R-8: Improve mock scan setTimeout handling**
setTimeout in canvas/UI services is almost always a false positive. Consider:
- Checking if the file imports HttpClient (if not, setTimeout is likely a UI timer)
- Checking if the surrounding context has any API-related keywords
- Adding per-file exclusion mechanism

**R-9: Track compound prediction vs actual**
Drawspace Canvas Upgrade achieved 89.3% milestone score vs 2-5% compound prediction. The prediction model dramatically underestimates actual success. This may cause overly conservative budget planning for Super Agent Team.

### Low Priority

**R-10: Fix wiring completeness metric**
Wiring completeness shows "0/141 (0%)" even when actual wiring is confirmed by zero build errors + SVC review passes. This is a MILESTONE_HANDOFF.md formatting issue that confuses verification.

**R-11: Add design direction keywords for technical/CAD/engineering apps**
Current keyword lists don't include CAD, construction, engineering, technical drawing terms.

---

## 8. Summary for Super Agent Team Readiness

### What WILL Work (High Confidence)
- Milestone execution with wave-based task deployment
- CQRS/MediatR code generation (.NET)
- Angular service generation with real API wiring (zero mock data)
- Convergence loops (1-2 cycles typical)
- E2E Playwright testing (with 4-6 fix cycles expected)
- Post-orchestration scan pipeline (deployment, asset, PRD recon, DB scans)
- Handoff document generation between milestones

### What MIGHT Fail (Medium Confidence)
- Browser testing with Docker apps (port detection issue)
- Review fleet outputs (may be empty for late milestones)
- Resume from mid-build interruption (worked after manual fixes, but fragile)
- Orchestrator self-coding on complex milestones after resume
- Wiring completeness gate (false positives on handoff docs)

### What WILL Fail Without Fixes (High Confidence)
- Running 4 PRD builds in same workspace without cleaning .agent-team/
- Browser testing with default port config on Docker apps
- Any PRD where synthesizer adds parenthetical notes in dependency strings (already fixed)

### Key Metrics for Planning
| Metric | Drawspace V1 | Canvas Upgrade | Predicted for Super Agent Team |
|--------|-------------|----------------|-------------------------------|
| Milestones | 9 | 7 | 10-15 per PRD |
| Requirements | 300+ | 332 | 400-600 per PRD |
| E2E Tests | 77 | 130 | 150-200 per PRD |
| Fix Cycles (E2E) | 6 | 2 (inherited) | 4-6 per PRD |
| Review Cycles | 1-2 per milestone | 0-2 per milestone | 1-2 per milestone |
| Cost | Not tracked | ~$112 | $150-250 per PRD |
| Duration | ~8 hours | ~15.5 hours (incl. resumes) | 20-30 hours per PRD |
| Resume Events | 1 | 2 | 0-2 per PRD (target: 0) |
