# Infrastructure Readiness Audit — Super Agent Team PRD Runs

**Auditor**: Infrastructure Readiness Auditor
**Date**: 2026-02-15
**Scope**: 11 supporting modules, 9 audit areas
**Verdict**: READY WITH RECOMMENDATIONS — all modules are production-capable; 3 HIGH recommendations, 7 MEDIUM, 5 LOW

---

## 1. Config Completeness (config.py — 1338 lines)

### Findings

**READY.** All config sections have validation, depth gating covers all features, and `_dict_to_config` returns `tuple[AgentTeamConfig, set[str]]` for user-override tracking.

| Setting | Default | Recommendation |
|---------|---------|----------------|
| `max_budget_usd` | `None` (unlimited) | Set explicitly for cost control |
| `max_turns` | 500 | Sufficient for large PRDs |
| `e2e_testing.enabled` | `False` | Must opt-in via config or depth=thorough+ |
| `browser_testing.enabled` | `False` | Must opt-in via config or depth=thorough+PRD |
| `tech_research.max_techs` | 8 | Adequate for most stacks |
| `tech_research.max_queries_per_tech` | 4 | Adequate |
| `prd_chunking.threshold` | 50000 (50KB) | Appropriate |
| `max_scan_fix_passes` | 1 | Consider 2 for exhaustive |
| `review_recovery_retries` | 3 | Adequate |

**[HIGH-1]** `max_budget_usd` defaults to `None`. For 4 concurrent Super Agent Team runs, each potentially spawning sub-orchestrators for tech research, E2E fix loops, browser testing, PRD reconciliation, and integrity fix passes, costs can escalate. **Set explicit budgets per run.**

**[MEDIUM-1]** `max_scan_fix_passes` defaults to 1. For exhaustive depth, a single fix pass may not resolve all scan violations (mock data, UI compliance, database, API contract). Consider setting to 2 for exhaustive runs.

**[LOW-1]** `apply_depth_quality_gating()` (line 509) correctly enables features per depth level, but `depth` is undefined in interactive mode (known non-blocking issue from v7.0 audit). Not relevant for PRD runs.

### Depth Gating Summary

| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| Tech research | off | 2 queries | 4 queries | 6 queries |
| Mock data scan | off | on | on | on |
| UI compliance | off | on | on | on |
| PRD reconciliation | off | off | on | on |
| E2E testing | off | off | on (2 retries) | on (3 retries) |
| Browser testing | off | off | on (3 retries, PRD only) | on (5 retries, PRD only) |
| Database scans | off | on | on | on |
| API contract scan | off | on | on | on |
| Integrity scans | off | on | on | on |

---

## 2. State Management (state.py — 305 lines)

### Findings

**READY.** RunState covers all pipeline phases with schema_version=2, atomic writes, and milestone-level resume.

**Strengths:**
- Atomic save via `tempfile` + `os.replace` — crash-safe
- Schema version 2 with backward-compatible defaults for all new fields
- `is_stale()` validates task match before resume — prevents stale state corruption
- `get_resume_milestone()` correctly determines resume point from `completed_milestones`
- `completed_browser_workflows` tracked for regression sweep resume
- `completion_ratio` persisted for progress display

**[LOW-2]** `failed_milestones` is tracked but there is no automatic retry of failed milestones in the pipeline. A failed milestone stops the entire run. This is by design (fail-fast), but worth noting for Super Agent Team runs where partial completion is valuable.

**No issues found.** State management is robust for all 4 planned builds.

---

## 3. Milestone Manager (milestone_manager.py — 935 lines)

### Findings

**READY.** MASTER_PLAN.md parsing handles h2-h4 headers, cross-milestone wiring is verified, and aggregation correctly combines per-milestone health.

**Strengths:**
- `_RE_MILESTONE_HEADER` matches `#{2,4}` — resilient to varied formatting (v13.0 fix)
- `normalize_milestone_dirs()` handles orphan directories gracefully
- `_list_milestone_ids()` only returns dirs with REQUIREMENTS.md — prevents phantom milestones
- `aggregate_milestone_convergence()` correctly aggregates worst-case health across milestones
- Cross-milestone wiring detection via `_IMPORT_REF_RE` and `_FILE_REF_RE` patterns

**[MEDIUM-2]** `update_master_plan_status()` uses the milestone regex for boundary detection (v13.0 fix), but if a PRD generates a MASTER_PLAN.md with h1 milestone headers (`# Milestone 1`), the regex won't match. The pattern requires h2-h4. This is unlikely but worth documenting for PRD authors.

**[LOW-3]** The infinite loop guard (`max_iterations = len(milestones) + 3`) from v13.0 is correctly in place. No concern for Super Agent Team runs.

---

## 4. MCP Servers (mcp_servers.py — 171 lines)

### Findings

**READY.** Server configs are clean, function-specific server sets are properly scoped.

| Server | Requirement | Used By |
|--------|-------------|---------|
| Firecrawl | `FIRECRAWL_API_KEY` env var | Design reference extraction, research |
| Context7 | None (free) | Tech research, browser testing |
| Sequential Thinking | None (free) | Orchestrator only |
| Playwright MCP | None (npx install) | Browser testing executor |

**[HIGH-2]** `FIRECRAWL_API_KEY` is required for design reference extraction (Phase 0.6). If not set, the fallback generation (`generate_fallback_ui_requirements()`) kicks in, but it produces heuristic-only output without real design data. For Super Agent Team runs with design URLs in the PRD, ensure `FIRECRAWL_API_KEY` is set.

**[MEDIUM-3]** All MCP servers use `npx -y` for installation. On first run or after npm cache clear, this triggers downloads that can take 10-30 seconds per server. For concurrent runs, ensure npm cache is warm or pre-install packages:
```bash
npx -y firecrawl-mcp --version
npx -y @anthropic-ai/context7-mcp@latest --version
npx -y @anthropic-ai/sequential-thinking-mcp --version
npx -y @playwright/mcp@latest --version
```

---

## 5. Tech Research (tech_research.py — 968 lines)

### Findings

**READY WITH GAPS.** File-based detection covers all major ecosystems. Text-based detection covers popular frameworks but has blind spots for exotic libraries.

**File-based detectors (6):**
- `package.json` — npm/yarn dependencies with `_NPM_PACKAGE_MAP` mapping
- `requirements.txt` — Python packages with `_PYTHON_PACKAGE_MAP` mapping
- `pyproject.toml` — Python (poetry/flit/hatch)
- `go.mod` — Go modules
- `*.csproj` — .NET packages
- `Cargo.toml` — Rust crates

**Text-based detection (`_TEXT_TECH_PATTERNS`):**
- Covers: React, Angular, Vue, Next.js, Nuxt, Express, FastAPI, Django, Flask, Prisma, TypeORM, Sequelize, MongoDB, PostgreSQL, Redis, Docker, Kubernetes, Tailwind, Bootstrap, Material UI, Supabase, Firebase, AWS, GraphQL, REST, WebSocket, and more
- Does NOT explicitly detect: tree-sitter, ChromaDB, pact-python, Schemathesis, transitions (Python FSM), Traefik, MCP SDK, Typer, Click (CLI frameworks)

**[MEDIUM-4]** For builds using exotic/niche libraries, the text-based detection may miss them. However, `build_expanded_research_queries()` generates PRD-feature-aware queries that can surface these via Context7 even if not explicitly detected. The system degrades gracefully — undetected techs just won't get dedicated Context7 queries.

**[LOW-4]** `max_techs=8` cap could truncate detection for polyglot stacks. For a build using React + Next.js + Tailwind + Prisma + PostgreSQL + Redis + Docker + Kubernetes + Nginx, that's already 9 techs. The cap prioritizes based on detection order. Consider raising to 12 for exhaustive depth.

---

## 6. E2E Testing (e2e_testing.py — 974 lines)

### Findings

**READY WITH CAVEATS.** The pipeline handles web apps (frontend+backend) well but has gaps for non-web builds.

**Strengths:**
- `detect_app_type()` handles JS/TS ecosystem (React, Angular, Vue, Next, Nuxt), Python (Django, FastAPI, Flask), and monorepo subdirectory scanning
- Schema drift check is mandatory before E2E tests
- Fix loop runs until pass or `max_fix_retries` — no budget gates
- 70% backend pass rate gate before frontend testing
- Granular phase tracking (e2e_backend / e2e_frontend / e2e_testing)

**[HIGH-3]** No special handling for "library" projects that are NOT web servers. If a build produces a Python library or CLI tool (not a web app), `detect_app_type()` will find no API framework and `skip_if_no_api=True` will skip backend tests. This is correct behavior, but the E2E phase will produce no value for such builds. The browser testing phase similarly requires a running web server. For builds that are purely libraries/tools, E2E and browser testing should be explicitly disabled in config.

**[MEDIUM-5]** `test_port=9876` default is fine but could conflict if multiple runs share the same machine. Each concurrent run should use a unique port via config override.

**[MEDIUM-6]** No MCP server testing capability. If a build produces an MCP server (like this project itself), E2E testing cannot verify the MCP protocol. This is a known architectural gap, not a bug.

---

## 7. Browser Testing (browser_testing.py — 1305 lines)

### Findings

**READY.** The pipeline is well-structured with proper safeguards.

**Strengths:**
- `_MAX_WORKFLOWS = 10` prevents excessive browser testing
- `_extract_seed_credentials()` scans seed/fixture files for test credentials — prevents auth-blocked workflows
- `generate_browser_workflows()` is deterministic (pure Python, no LLM)
- `verify_workflow_execution()` structural verification prevents false passes
- `check_screenshot_diversity()` catches identical repeated screenshots
- Finally block for app process cleanup (v8.0 review fix H1)

**[MEDIUM-7]** Browser testing is only enabled at `thorough+` depth AND only in PRD mode (milestone-based). Standard mode builds will never get browser testing regardless of config. This is by design (browser testing requires REQUIREMENTS.md for workflow generation), but should be explicit in config documentation.

**No blocking issues.** Browser testing is production-ready for all 4 builds that use PRD mode.

---

## 8. PRD Chunking (prd_chunking.py — 226 lines)

### Findings

**READY.** Simple, focused module that handles large PRDs correctly.

**Strengths:**
- 50KB threshold is appropriate (most PRDs are 10-40KB)
- Splits on h1/h2 headings only — preserves semantic section boundaries
- Skips sections < 100 bytes — filters noise
- `validate_chunks()` checks file existence after writing

**[LOW-5]** `max_chunk_size` parameter in `create_prd_chunks()` is reserved but UNUSED. There is no logic to split a single large section (e.g., a 60KB section under one h2 heading). If a PRD has a single massive section, it will become one chunk regardless of size. This is unlikely in practice but could occur with auto-generated PRDs.

**No blocking issues.**

---

## 9. Scheduler (scheduler.py — 1369 lines)

### Findings

**READY.** DAG-based scheduling with comprehensive parsing and conflict resolution.

**Strengths:**
- 3 parsing formats: block (`### TASK-xxx`), table (`| TASK-xxx |`), bullet (`- TASK-xxx:`)
- `_parse_bullet_format_tasks()` detects `## Milestone N` headers for milestone assignment (v14.0 fix)
- `compute_schedule()` full pipeline: validate, build graph, topological waves, file conflicts, resolve, critical path
- Cross-milestone dependency via `@` syntax (e.g., `milestone-1@TASK-003`)
- File conflict detection prevents concurrent writes to same file

**No issues found.** The scheduler is robust for all build types.

---

## 10. Additional Modules

### Design Reference (design_reference.py — 667 lines)
- **READY.** Retry with exponential backoff, fallback generation, content quality validation
- Requires `FIRECRAWL_API_KEY` for real extraction (see HIGH-2)

### Display (display.py — 704 lines)
- **READY.** Windows UTF-8 handling at module load, Rich console output for all phases
- No issues

---

## Summary of Findings

| Severity | Count | Details |
|----------|-------|---------|
| HIGH | 3 | Budget limits (H1), Firecrawl API key (H2), Library project E2E (H3) |
| MEDIUM | 7 | Fix passes (M1), h1 headers (M2), MCP cache (M3), exotic techs (M4), port conflicts (M5), MCP server testing (M6), browser depth gate (M7) |
| LOW | 5 | Interactive depth (L1), failed milestone retry (L2), max iterations (L3), max_techs cap (L4), chunk splitting (L5) |
| BLOCKING | 0 | None |

---

## RECOMMENDED CONFIG.YAML

Optimal settings for Super Agent Team PRD runs at exhaustive depth with explicit cost controls:

```yaml
# === RECOMMENDED CONFIG FOR SUPER AGENT TEAM PRD RUNS ===
# Use this as a starting template — adjust per build.

depth: exhaustive

orchestrator:
  max_turns: 500           # Default, sufficient for large PRDs
  max_budget_usd: 50.0     # IMPORTANT: Set explicit budget per run
  model: claude-sonnet-4-5-20250929  # Or claude-opus-4-6 for maximum quality

milestones:
  review_recovery_retries: 3  # Default, adequate

e2e_testing:
  enabled: true               # Exhaustive enables automatically, but be explicit
  backend_api_tests: true
  frontend_playwright_tests: true
  max_fix_retries: 3           # Exhaustive default
  test_port: 9876              # CHANGE for concurrent runs (9877, 9878, etc.)
  skip_if_no_api: true         # Skip backend E2E if no API framework detected
  skip_if_no_frontend: true    # Skip frontend E2E if no frontend detected

browser_testing:
  enabled: true                # Exhaustive+PRD enables automatically
  max_fix_retries: 5           # Exhaustive default
  e2e_pass_rate_gate: 0.7      # Require 70% E2E pass before browser testing
  headless: true               # Set false for local debugging only
  regression_sweep: true       # Re-verify after fixes

tech_research:
  enabled: true
  max_techs: 10               # Raised from default 8 for polyglot stacks
  max_queries_per_tech: 4      # Default, adequate
  injection_max_chars: 6000    # Default, adequate

post_orchestration_scans:
  mock_data_scan: true
  ui_compliance_scan: true
  api_contract_scan: true
  max_scan_fix_passes: 2       # Raised from default 1 for exhaustive

integrity_scans:
  deployment_scan: true
  asset_scan: true
  prd_reconciliation: true

database_scans:
  dual_orm_scan: true
  default_value_scan: true
  relationship_scan: true

tracking_documents:
  e2e_coverage_matrix: true
  fix_cycle_log: true
  milestone_handoff: true
  coverage_completeness_gate: 0.8
  wiring_completeness_gate: 1.0

prd_chunking:
  threshold: 50000             # 50KB, default

design_reference:
  extraction_retries: 3
  fallback_generation: true
  content_quality_check: true

scan_scope_mode: auto          # "auto" uses depth-based scoping

mcp_servers:
  firecrawl:
    enabled: true              # Requires FIRECRAWL_API_KEY env var
  context7:
    enabled: true
  sequential_thinking:
    enabled: true
```

### Per-Build Adjustments

| Build Type | Adjustments |
|------------|-------------|
| Full-stack web app | Use config as-is |
| Backend-only API | Set `browser_testing.enabled: false`, `skip_if_no_frontend: true` |
| Frontend-only SPA | Set `skip_if_no_api: true`, consider `database_scans` all false |
| Library / CLI tool | Set `e2e_testing.enabled: false`, `browser_testing.enabled: false` |
| Monorepo | Increase `max_budget_usd`, ensure unique `test_port` |

### Environment Variables Required

```bash
export ANTHROPIC_API_KEY="sk-ant-..."       # Required
export FIRECRAWL_API_KEY="fc-..."           # Required for design extraction
# Optional: OPENAI_API_KEY for fallback models
```

### Pre-Run Checklist

1. Set `ANTHROPIC_API_KEY` and `FIRECRAWL_API_KEY`
2. Warm npm cache: `npx -y firecrawl-mcp --version && npx -y @anthropic-ai/context7-mcp@latest --version && npx -y @playwright/mcp@latest --version`
3. Ensure unique `test_port` per concurrent run
4. Delete `.agent-team/` directory if re-running with a new PRD
5. Set explicit `max_budget_usd` based on PRD complexity
6. For library/CLI builds, disable E2E and browser testing

---

## Conclusion

All 11 infrastructure modules are production-ready for Super Agent Team PRD runs. No blocking issues were found. The 3 HIGH recommendations are all configuration-level concerns that are resolved by using the recommended config.yaml above. The system's crash isolation (try/except per scan), atomic state persistence, and depth gating ensure robust execution even under failure conditions.
