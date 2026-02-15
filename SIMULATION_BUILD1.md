# BUILD1 PRD Pipeline Simulation Report

> Simulated trace of `prompts/BUILD1_PRD.md` through every phase of the agent-team pipeline.
> Generated: 2026-02-15

---

## Executive Summary

BUILD1 is a **pure backend** PRD (3 Python/FastAPI MCP servers, no frontend, no UI). The agent-team pipeline was designed with full-stack projects in mind (React/Angular + Express/Django). Several phases will waste budget or behave suboptimally, but **no pipeline-breaking blockers** were found. The biggest risk is the tech research phase failing to detect BUILD1's core technologies (tree-sitter, ChromaDB, NetworkX, MCP SDK).

| Category | Count |
|----------|-------|
| BLOCKER | 0 |
| WARNING | 9 |
| OPTIMIZATION | 5 |

---

## Phase 0: Config & PRD Loading

### What Happens

1. **PRD size**: BUILD1_PRD.md is **103,145 bytes** (~103KB), well above the 50KB chunking threshold.
2. **Depth mode**: Depends on user invocation. If "exhaustive" is used (recommended for critical builds), E2E testing, browser testing, and tech research get maximum settings.
3. **Config**: No special `config.yaml` needed -- BUILD1 uses Python/FastAPI which are well-supported.

### Issues

**None** -- Config loading is straightforward.

---

## Phase 0.5: Codebase Map

### What Happens

Since BUILD1 starts from scratch (empty project directory), the codebase map phase will find zero files and produce an empty map. This is expected and harmless.

### Issues

**None**

---

## Phase 0.6: Design Reference Extraction

### What Happens

BUILD1 has no design reference URLs (pure backend). The pipeline enters the `else` branch at `cli.py:4413`.

**WARNING-1: Unnecessary fallback UI requirements generation**

Since `config.design_reference.fallback_generation` defaults to `True`, the pipeline will call `generate_fallback_ui_requirements()` at `cli.py:4447`. This generates a `UI_REQUIREMENTS.md` with color systems, typography, spacing, and component patterns -- **completely useless for a backend-only project**.

The `_infer_design_direction()` function (`design_reference.py:485`) will attempt to match PRD keywords against direction tables (brutalist, luxury, industrial, minimal_modern, editorial). BUILD1's PRD text contains keywords like "developer", "tool", "code" which will match the **brutalist** direction. The file will be generated with hex colors, font families, and spacing scales that will never be used.

**Impact**: Wasted file creation. The UI_REQUIREMENTS.md content will be injected into prompts, consuming context window tokens without benefit.

**Location**: `cli.py:4413-4460`, `design_reference.py:485-507`

**Severity**: WARNING (budget waste, ~$0.00 compute but adds noise to prompts)

---

## Phase 1: Tech Research (via Context7)

### What Happens

`detect_tech_stack()` (`tech_research.py:426`) runs 6 file-based detectors then text-based detection.

**What WILL be detected from PRD text** (text patterns in `_TEXT_TECH_PATTERNS`):
- FastAPI (line 74: `\bFastAPI\b`) with version 0.129.0
- SQLite (line 85: `\bSQLite\b`)
- Python (line 110: `\bPython\b`) with version 3.12

**What WILL be detected from project files** (once `pyproject.toml` is created):
- FastAPI from `_PYTHON_PACKAGE_MAP` (line 153: `fastapi`)
- Pytest from `_PYTHON_PACKAGE_MAP` (line 158: `pytest`)

**WARNING-2: Critical technologies NOT detected**

The following BUILD1-critical technologies have NO detection patterns:

| Technology | Version | Why Critical | Detection Gap |
|-----------|---------|--------------|---------------|
| tree-sitter | 0.25.2 | Core AST parsing engine. API changed in 0.25.0 (QueryCursor, captures returns dict). Wrong API = broken code. | Not in `_TEXT_TECH_PATTERNS` or `_PYTHON_PACKAGE_MAP` |
| ChromaDB | 1.5.0 | Vector search engine. API nuances (nested lists, DefaultEmbeddingFunction import path). | Not in any detection map |
| NetworkX | 3.6.1 | Graph analysis. `edges="edges"` parameter required (not deprecated "links"). | Not in any detection map |
| MCP SDK | >=1.25,<2 | MCP server creation. `@mcp.tool()` decorators, `mcp.run(transport="stdio")`. | Not in any detection map |
| Schemathesis | 4.10.1 | Contract testing. `schemathesis.openapi.from_path()` API. | Not in any detection map |
| prance | 25.4.8.0 | OpenAPI $ref resolution. `ResolvingParser` API. | Not in any detection map |
| pydantic-settings | >=2.1.0 | Config loading. `BaseSettings` v2 syntax. | Not in any detection map |
| onnxruntime | (indirect) | ChromaDB embedding model dependency. | Not in any detection map |

**Impact**: The tech research sub-orchestrator will only query Context7 for FastAPI, SQLite, Python, and Pytest. It will miss research on tree-sitter 0.25.x API changes, ChromaDB query patterns, NetworkX serialization, and MCP SDK tool registration -- all areas where agents commonly make mistakes.

**Location**: `tech_research.py:64-113` (text patterns), `tech_research.py:152-164` (Python package map)

**Severity**: WARNING (HIGH -- most likely source of code errors in milestones 5-7)

---

## Phase 1.5: PRD Chunking

### What Happens

BUILD1_PRD.md is **103KB** > 50KB threshold. `detect_large_prd()` at `prd_chunking.py:49` returns `True`. The PRD will be chunked.

**Section boundary detection** (`prd_chunking.py:62`): Splits on `#` and `##` headings. BUILD1's structure:

| Heading | Section Type | Size Estimate |
|---------|-------------|---------------|
| `# Super Agent Team...` | general | ~250 bytes |
| `## Technology Stack` | dependencies | ~2KB |
| `## Architectural Principle` | general | ~1KB |
| `## Project Structure` | general | ~4KB |
| `## Milestone 1: Core Data Models` | general | ~15KB |
| `## Milestone 2: Architect Service` | general | ~10KB |
| `## Milestone 3: Contract Engine Core` | general | ~12KB |
| `## Milestone 4: Contract Test Generation` | general | ~4KB |
| `## Milestone 5: Codebase Intelligence Layers 1 and 2` | general | ~12KB |
| `## Milestone 6: Codebase Intelligence Layer 3 and MCP Server` | general | ~10KB |
| `## Milestone 7: Architect MCP and Contract Engine MCP Servers` | general | ~8KB |
| `## Milestone 8: Integration, Docker, and End-to-End Tests` | general | ~10KB |
| `## Status Registry` | general | ~2KB |
| `## Architecture Decision` | general | ~5KB |
| `## Review Log` | general | ~100 bytes |

**WARNING-3: Most milestones classified as "general" section type**

The `_SECTION_PATTERNS` at `prd_chunking.py:19` detect keywords like "features", "database", "api", "frontend", "auth", "infrastructure", "testing", "dependencies". BUILD1's headings like "Milestone 1: Core Data Models" and "Milestone 3: Contract Engine Core" won't match any pattern and will be classified as "general" with the generic focus "Analyze this section for relevant requirements".

This means the chunk analysis won't get targeted focus instructions. The "api" pattern would match "Milestone 3: Contract Engine Core" (contains no "api" keyword), and "database" would match if "database" or "schema" appears in the heading text -- "Milestone 1: Core Data Models" contains "Data Models" but not "database" or "schema" exactly.

**Impact**: Chunked analysis will use generic focus descriptions instead of targeted ones. Mild quality reduction in decomposition.

**Location**: `prd_chunking.py:19-29`

**Severity**: WARNING (LOW -- decomposition still works, just less focused)

---

## Phase 2: Decomposition

### What Happens

`build_decomposition_prompt()` in `agents.py` sends the PRD (or chunks) to the decomposition agent which creates `MASTER_PLAN.md`.

BUILD1 has 8 milestones with clear boundaries and explicit cross-milestone dependencies (e.g., M5 references M6's SemanticIndexer). The decomposition agent should handle this well since:
- Milestones are explicitly numbered and described
- Dependencies are called out ("Cross-milestone dependency: The IncrementalIndexer (REQ-055) references SemanticIndexer.index_symbols() which is implemented in M6")
- Each milestone has clear REQ/TECH/WIRE/TEST/SVC/INT requirement types

**WARNING-4: 8 milestones is a large count**

`config.milestone.max_milestones_warning` defaults to 30, so 8 milestones won't trigger a warning. However, 8 milestones at $5-15 each means $40-120 in milestone execution alone, before post-orchestration scans.

### Issues

**No blockers.** The decomposition should work correctly.

---

## Phase 3: Milestone Execution Loop

### What Happens

8 milestones execute sequentially via `build_milestone_execution_prompt()`.

**Milestone 1** (Core Data Models): Straightforward scaffolding. Pydantic models, SQLite schemas, Docker base config. Should execute cleanly.

**Milestone 2** (Architect Service): Service logic with NetworkX, FastAPI routers, Depends() injection. Agent needs NetworkX knowledge (not researched -- see WARNING-2).

**Milestone 3** (Contract Engine Core): AsyncAPI custom parser (~500 lines), OpenAPI validation, breaking change detection. Complex but well-specified.

**Milestone 4** (Contract Test Generation): Schemathesis integration. Agent needs schemathesis API knowledge (not researched -- see WARNING-2).

**Milestone 5** (Codebase Intelligence Layers 1-2): **HIGHEST RISK.** tree-sitter 0.25.x API, 4 language parsers, NetworkX graph construction.

**WARNING-5: tree-sitter 0.25.x API is critical and unresearched**

The PRD explicitly calls out API changes: "QueryCursor was introduced in 0.25.0", "captures() return type changed from list[tuple] to dict[str, list[Node]] in 0.25.0". Without Context7 research on tree-sitter 0.25.x, the agent will rely on training data which may contain the OLD API (pre-0.25.0 patterns). This is the single most likely source of code errors.

**Location**: REQ-043 in BUILD1_PRD.md (lines 430-431)

**Severity**: WARNING (HIGH -- likely to produce broken code that needs fix cycles)

**Milestone 6** (Codebase Intelligence Layer 3 + MCP): ChromaDB integration, MCP server creation. Both APIs are unresearched.

**WARNING-6: ChromaDB API nuances**

ChromaDB's `collection.query()` returns nested lists (results["ids"][0], not results["ids"]). The PRD documents this in TECH-021, but without research the agent may still get it wrong. Also, `DefaultEmbeddingFunction` import path from `chromadb.utils.embedding_functions` is non-obvious.

**Milestone 7** (MCP Servers): Creates MCP servers for Architect and Contract Engine. Agent needs MCP SDK knowledge.

**WARNING-7: MCP SDK tool registration patterns**

The MCP SDK uses `@mcp.tool()` decorators and `mcp.run(transport="stdio")`. Without Context7 research, the agent may use outdated or incorrect patterns. The PRD specifies detailed patterns (TECH-024, TECH-026, TECH-027, TECH-028) which helps, but research would prevent common mistakes.

**Milestone 8** (Integration + Docker): Docker Compose finalization, inter-service HTTP calls, E2E tests. Well-specified and straightforward.

---

## Phase 4: Post-Orchestration Scans

### Mock Data Scan (MOCK-001..008)

**What Happens**: `run_mock_data_scan()` scans files matching `_RE_SERVICE_PATH` regex (`services?|clients?|api|http|data-access|repositor|provider|store|facade|composable`).

BUILD1's file paths include `services/` directories (e.g., `src/architect/services/prd_parser.py`, `src/contract_engine/services/contract_store.py`). These **will** be scanned.

**WARNING-8: Potential false positives on test fixtures and sample data**

BUILD1 creates `sample_data/sample_prd.md`, `sample_data/sample_openapi.yaml`, etc. The `_RE_SERVICE_PATH` regex won't match `sample_data/` paths, so sample data files are safe.

However, BUILD1's actual service files contain:
- Test fixture generation code (TestGenerator creates test code with hardcoded values)
- Sample/default data in constants (e.g., default embedding function names)
- Variable names like `mock` in test-related code

The `_RE_TEST_FILE` pattern (`\.test\.|\.spec\.|__tests__|\.stories\.|test_`) will correctly exclude test files. Service files that generate test code (e.g., `test_generator.py`) will be scanned -- the filename doesn't match `_RE_TEST_FILE` since it's `test_generator.py` not `test_*.py`.

**Possible false positive**: `test_generator.py` in `src/contract_engine/services/` generates test code strings containing hardcoded data. MOCK-003 (`_RE_MOCK_VARIABLE`) would flag variables like `mock_response` if they appear in the generated test template strings.

**Impact**: 0-3 false positive violations. Non-blocking (scan produces warnings, fix loop may waste one cycle).

**Location**: `quality_checks.py:307-310` (service path regex), `quality_checks.py:753-850` (mock checks)

**Severity**: WARNING (LOW)

### UI Compliance Scan (UI-001..004)

**What Happens**: Scans files with extensions `.tsx`, `.jsx`, `.vue`, `.svelte`, `.css`, `.scss`, `.html`.

BUILD1 is **pure Python**. Zero files match these extensions. **Zero violations. Scan completes instantly.**

### Deployment Scan (DEPLOY-001..004)

**What Happens**: Cross-references `docker-compose.yml` with `.env*` files.

BUILD1 creates `docker-compose.yml` and `.env.example`. The deployment scan will:
- DEPLOY-001: Check port mappings (8001:8000, 8002:8000, 8003:8000) -- should pass
- DEPLOY-002: Check environment variables are defined in `.env*` files -- should pass if `.env.example` is complete
- DEPLOY-003: Check CORS origins match frontend URL -- N/A (no frontend CORS)
- DEPLOY-004: Check service name consistency -- should pass

**Impact**: Should produce zero or minimal violations if BUILD1 is implemented correctly.

### Asset Scan (ASSET-001..003)

**What Happens**: Scans for broken static asset references (src, href, url(), require, import).

BUILD1 has no frontend assets. **Zero violations expected.**

### Database Scan (DB-001..008)

**What Happens**: `run_dual_orm_scan()` first calls `_detect_data_access_methods()` which checks for both ORM and raw SQL usage.

BUILD1 uses:
- Raw SQL via `sqlite3` (`cursor.execute`)
- No ORM (no SQLAlchemy, no Prisma, no TypeORM)

`_detect_data_access_methods()` at `quality_checks.py:1910` checks:
- Python: `cursor.execute` in content -> `has_raw = True`
- Python: `SQLAlchemy` in requirements.txt -> `has_orm = True` (NOT PRESENT in BUILD1)

Since `has_orm = False` and `has_raw = True`, the check `if not (has_orm and has_raw): return []` at line 2052 triggers. **DB-001..003 return zero violations.**

`run_default_value_scan()` and `run_relationship_scan()` also depend on ORM detection patterns. Since BUILD1 uses raw SQL without an ORM, these scans should produce zero or minimal violations.

**Impact**: Database scans will be harmless no-ops for BUILD1.

### API Contract Scan (API-001..003)

**What Happens**: Gated at `cli.py:5529`:
```python
if _app_info.has_backend and _app_info.has_frontend:
```

BUILD1's `detect_app_type()` will return:
- `has_backend = True` (FastAPI detected from pyproject.toml/requirements.txt)
- `has_frontend = False` (no React/Vue/Angular/Next.js)

**API contract scan is SKIPPED.** The gate requires both backend AND frontend.

**WARNING-9: SVC table format mismatch (dormant bug)**

BUILD1's SVC tables have **7 columns**: `| ID | Frontend Service | Method | HTTP | Backend Endpoint | Request DTO | Response DTO |`

The `_parse_svc_table()` parser at `quality_checks.py:2781` supports only **5 or 6 columns**. With 7 columns, the parser enters the `len(cells) >= 6` branch and misaligns:
- cells[2] becomes `decompose()` instead of the actual endpoint `/api/decompose`
- cells[4] becomes `/api/decompose` instead of the request DTO
- cells[5] becomes the request DTO instead of the response DTO
- cells[6] (actual response DTO) is **completely ignored**

This bug is **dormant** because the API contract scan is skipped (no frontend). If BUILD1 ever adds a frontend, or if the gate logic changes, this would produce completely wrong field-mismatch violations.

**Location**: `quality_checks.py:2781-2831` (parser), `cli.py:5524-5529` (gate)

**Severity**: WARNING (dormant bug -- no impact for BUILD1, but indicates a 7-column format gap)

---

## Phase 5: E2E Testing

### What Happens

If `e2e_testing.enabled` is True (thorough/exhaustive depth):

1. `detect_app_type(Path(cwd))` at `cli.py:5691`:
   - `has_backend = True` (FastAPI from requirements.txt/pyproject.toml)
   - `has_frontend = False` (no JS framework)
   - `backend_framework = "fastapi"`
   - `start_command = "uvicorn main:app --reload"` (default for FastAPI)

2. **Backend E2E tests**: Will run. The E2E prompt asks the agent to write pytest tests against FastAPI endpoints. This should work well -- FastAPI + TestClient is a standard pattern.

3. **Frontend E2E tests**: Skipped via `config.e2e_testing.skip_if_no_frontend` (default True) at `cli.py:5856`: `if config.e2e_testing.skip_if_no_frontend and not app_info.has_frontend: skip`.

**Potential issue with MCP server testing**: BUILD1's MCP servers use `stdio` transport, not HTTP. The E2E test generation prompts focus on HTTP endpoint testing. The agent may not know how to test MCP servers via `stdio_client` + `ClientSession` without explicit guidance from the PRD's TEST-032/TEST-035 requirements.

**Impact**: Backend API E2E tests should work. MCP tool E2E tests may be incomplete.

---

## Phase 6: Browser Testing

### What Happens

Browser testing is gated at `cli.py:5951`:
```python
if config.browser_testing.enabled:
```

For thorough/exhaustive depth with PRD mode, `browser_testing.enabled` is set to True at `config.py:581-583`.

However, the browser testing phase has a secondary gate at `cli.py:5959`:
```python
if e2e_total == 0:
    print_info("Browser testing skipped: E2E phase did not run")
    browser_report.health = "skipped"
```

If E2E testing ran backend-only tests, `e2e_total > 0` and the gate passes. The browser testing agent then tries to:
1. Start the app on a port
2. Navigate to it in a browser
3. Execute visual workflows

For a **backend-only FastAPI API server**, the browser will navigate to `http://localhost:{port}` and see either:
- The FastAPI auto-generated Swagger UI (at `/docs`)
- A JSON response from the root endpoint
- A 404 page

The startup agent should detect and start the app. But workflow generation will fail or produce trivial workflows since there's no real UI to interact with.

**Impact**: Browser testing will run but produce minimal useful results. Budget waste of $5-15.

**OPTIMIZATION-1**: The browser testing phase should detect backend-only projects and auto-skip, similar to `skip_if_no_frontend` in E2E testing.

---

## Issue Summary

### BLOCKER Issues (0)

None identified. The pipeline will not crash or fail for BUILD1.

### WARNING Issues (9)

| ID | Phase | Issue | Severity | Location |
|----|-------|-------|----------|----------|
| W-1 | 0.6 | Unnecessary fallback UI_REQUIREMENTS.md generated for backend-only project | LOW | `cli.py:4413-4460` |
| W-2 | 1 | 8 critical technologies (tree-sitter, ChromaDB, NetworkX, MCP SDK, schemathesis, prance, pydantic-settings, onnxruntime) have no detection patterns | HIGH | `tech_research.py:64-164` |
| W-3 | 1.5 | Most milestone chunks classified as "general" (no targeted focus) | LOW | `prd_chunking.py:19-29` |
| W-4 | 2 | 8 milestones = $40-120 execution cost | INFO | N/A |
| W-5 | 3 (M5) | tree-sitter 0.25.x API changes unresearched -- highest risk of broken code | HIGH | `tech_research.py` (missing patterns) |
| W-6 | 3 (M6) | ChromaDB API nuances (nested lists, import paths) unresearched | MEDIUM | `tech_research.py` (missing patterns) |
| W-7 | 3 (M7) | MCP SDK tool registration patterns unresearched | MEDIUM | `tech_research.py` (missing patterns) |
| W-8 | 4 | Potential false positives on `test_generator.py` service file (contains mock-like generated code) | LOW | `quality_checks.py:307-310` |
| W-9 | 4 | SVC table parser doesn't support 7-column format (dormant -- API scan skipped for backend-only) | MEDIUM | `quality_checks.py:2781-2831` |

### OPTIMIZATION Suggestions (5)

| ID | Phase | Suggestion | Impact |
|----|-------|-----------|--------|
| O-1 | 0.6 | Skip fallback UI_REQUIREMENTS.md for projects with no frontend detected (check `detect_app_type()` early) | Saves token noise |
| O-2 | 1 | Add detection patterns for: tree-sitter, ChromaDB, NetworkX, MCP SDK, schemathesis, prance, pydantic-settings, onnxruntime | Enables Context7 research for critical BUILD1 techs |
| O-3 | 1.5 | Add PRD chunk section patterns for "milestone", "models", "service" headings | Better chunk focus descriptions |
| O-4 | 4 | Support 7-column SVC tables in `_parse_svc_table()` | Future-proofs for varied PRD formats |
| O-5 | 6 | Add `skip_if_no_frontend` gate to browser testing (not just E2E testing) | Saves $5-15 on backend-only projects |

---

## Recommended Config for BUILD1

```yaml
orchestrator:
  model: opus
  max_turns: 500
  max_budget_usd: 150.0

depth:
  default: exhaustive

milestone:
  enabled: true
  review_recovery_retries: 3

design_reference:
  fallback_generation: false   # OVERRIDE: no UI to design
  require_ui_doc: false

e2e_testing:
  enabled: true
  skip_if_no_frontend: true
  backend_api_tests: true
  frontend_playwright_tests: false  # No frontend

browser_testing:
  enabled: false   # OVERRIDE: no browser UI to test

tech_research:
  enabled: true
  max_queries_per_tech: 4
```

**Key overrides**:
- `design_reference.fallback_generation: false` -- prevents useless UI doc
- `browser_testing.enabled: false` -- prevents wasted browser testing budget
- `e2e_testing.frontend_playwright_tests: false` -- explicit frontend skip

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tree-sitter 0.25.x API errors | HIGH (70%) | Code breaks in M5 | PRD has detailed API docs; review cycles will catch |
| ChromaDB query pattern errors | MEDIUM (40%) | Broken semantic search in M6 | TECH-021 documents nested list pattern |
| NetworkX edges="edges" forgotten | LOW (20%) | Serialization fails in M5/M6 | TECH-018 explicitly documents this |
| MCP SDK pattern errors | MEDIUM (30%) | MCP servers won't start in M7 | TECH-024/027 document patterns |
| Budget overrun | MEDIUM (40%) | >$150 total | 8 milestones + E2E + scans |

---

## Conclusion

BUILD1 will execute through the pipeline without crashes. The primary risk is **code quality in milestones 5-7** due to missing tech research for tree-sitter, ChromaDB, NetworkX, and MCP SDK. The PRD itself contains detailed technical requirements (TECH-016 through TECH-028) that partially compensate for the missing research, but agents may still use outdated API patterns from training data.

The recommended config overrides (disable UI fallback, disable browser testing) will save approximately $5-20 in unnecessary budget and reduce prompt noise.

**Overall pipeline readiness for BUILD1: 85/100** (deducted for missing tech research patterns and backend-only handling gaps).
