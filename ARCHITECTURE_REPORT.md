# ARCHITECTURE REPORT: v11 E2E Gap Closure — Silent Data Loss Scan

**Date:** 2026-02-11
**Author:** gap-architect agent
**Purpose:** Blueprint for implementers — exact line numbers, patterns, signatures, insertion points

---

## 1. quality_checks.py — Scan Function Architecture

**File:** `src/agent_team/quality_checks.py`

### 1.1 Core Dataclasses

| Dataclass | Line | Fields |
|-----------|------|--------|
| `ScanScope` | 37 | `mode: str`, `changed_files: list[Path]` |
| `Violation` | 92 | `check: str`, `message: str`, `file_path: str`, `line: int`, `severity: str` |
| `SvcContract` | 2646 | `svc_id`, `frontend_service_method`, `backend_endpoint`, `http_method`, `request_dto`, `response_dto`, `request_fields: dict[str,str]`, `response_fields: dict[str,str]` |

### 1.2 Constants

| Constant | Line | Value/Purpose |
|----------|------|---------------|
| `_MAX_VIOLATIONS` | 107 | `100` — cap per scan |
| `_MAX_FILE_SIZE` | 109 | `100_000` (100 KB) — skip large files |
| `_SKIP_DIRS` | 111 | frozenset: node_modules, .git, __pycache__, dist, build, .next, venv |
| `_SEVERITY_ORDER` | 121 | `{"error": 0, "warning": 1, "info": 2}` |

### 1.3 File Walking Helpers

| Function | Line | Signature | Purpose |
|----------|------|-----------|---------|
| `_iter_source_files` | 1177 | `(project_root: Path) -> list[Path]` | os.walk with _SKIP_DIRS pruning |
| `_find_files_by_pattern` | 2781 | `(project_root: Path, pattern: str, scope: ScanScope \| None = None) -> list[Path]` | Regex filter on relative paths, scope-aware |
| `_extract_identifiers_from_file` | 2772 | `(content: str) -> set[str]` | `re.findall(r'\b[a-zA-Z_]\w*\b', content)` |
| `_to_pascal_case` | 2762 | `(camel_name: str) -> str` | `camel_name[0].upper() + camel_name[1:]` |
| `compute_changed_files` | 54 | `(project_root: Path) -> list[Path]` | git diff + untracked files |

### 1.4 Scan Function Signatures — CANONICAL PATTERN

All public scan functions follow this exact pattern:

```python
def run_xxx_scan(
    project_root: Path,
    scope: ScanScope | None = None,
) -> list[Violation]:
```

**Exceptions:**
- `run_spot_checks(project_root: Path) -> list[Violation]` (line 1205) — NO scope param
- `run_deployment_scan(project_root: Path) -> list[Violation]` (line 1599) — NO scope param

**Complete scan function registry:**

| Function | Line | Scope? | Checks |
|----------|------|--------|--------|
| `run_spot_checks` | 1205 | No | All FRONT/BACK/SLOP checks |
| `run_mock_data_scan` | 1259 | Yes | MOCK-001..007 |
| `run_ui_compliance_scan` | 1295 | Yes | UI-001..004 |
| `run_e2e_quality_scan` | 1331 | Yes | E2E-001..007 |
| `run_deployment_scan` | 1599 | No | DEPLOY-001..004 |
| `run_asset_scan` | 1749 | Yes | ASSET-001..003 |
| `run_dual_orm_scan` | 1975 | Yes | DB-001..003 |
| `run_default_value_scan` | 2108 | Yes | DB-004..005 |
| `run_relationship_scan` | 2391 | Yes | DB-006..008 |
| `run_api_contract_scan` | 2967 | Yes | API-001..003 |

### 1.5 Scope Filtering Pattern (template for new scans)

```python
source_files = _iter_source_files(project_root)
if scope and scope.changed_files:
    scope_set = set(scope.changed_files)
    source_files = [f for f in source_files if f.resolve() in scope_set]
```

For scans that need full-project context for aggregate checks (like `run_dual_orm_scan`, `run_relationship_scan`), the detection phase uses ALL files but violation-reporting is limited to scoped files.

### 1.6 Sort and Cap Pattern (end of every scan function)

```python
violations = violations[:_MAX_VIOLATIONS]
violations.sort(
    key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
)
return violations
```

### 1.7 Violation Constructor Pattern

```python
violations.append(Violation(
    check="XXX-001",
    message="Human-readable description",
    file_path=rel_path,   # relative POSIX path, or "REQUIREMENTS.md" for contract checks
    line=lineno,           # 1-based, or 0 for project-level
    severity="error",      # "error" | "warning" | "info"
))
```

### 1.8 API Contract Scan — Detailed Analysis (lines 2640-3035)

**One-directional gap (THE GAP to close):**
The current `run_api_contract_scan()` checks:
- Schema → Backend code: `_check_backend_fields()` verifies SVC-xxx response fields exist in backend DTOs
- Schema → Frontend code: `_check_frontend_fields()` verifies SVC-xxx response fields exist in frontend models/interfaces
- Type compatibility: `_check_type_compatibility()` warns on unusual types

**What is MISSING (the SDL gap):**
- **Code → Schema reverse check:** There is NO check that says "backend endpoint returns field X but SVC-xxx doesn't list it" or "frontend reads field Y but SVC-xxx doesn't define it"
- **Silent data loss detection:** If a backend controller calls a repository that does NOT `.Include()` or `.Select()` a navigation property, the API returns null/empty for that field. The frontend shows blank/missing data. No scan catches this.
- **Partial select detection:** Backend code using `.Select(x => new { x.Id, x.Title })` drops fields that the frontend expects. No scan catches this.

**SVC table parsing:**
- `_RE_SVC_ROW_START` (line 2640): `re.compile(r'^\|\s*SVC-\d+\s*\|', re.MULTILINE)`
- `_RE_FIELD_SCHEMA` (line 2642): `re.compile(r'\{[^}]+\}')` — matches `{ field: type }` blocks
- `_parse_svc_table()` (line 2708): Supports 5-column and 6-column tables
- `_parse_field_schema()` (line 2658): Extracts `field_name -> type_hint` from `{ id: number, title: string }`

### 1.9 Extension Sets Available for Reuse

| Set | Line | Extensions |
|-----|------|------------|
| `_EXT_ENTITY` | 341 | `.cs`, `.py`, `.ts`, `.js` |
| `_EXT_TYPESCRIPT` | 461 | `.ts`, `.tsx` |
| `_EXT_BACKEND` | 462 | `.ts`, `.js`, `.py` |
| `_EXT_JS_ALL` | 463 | `.ts`, `.tsx`, `.js`, `.jsx` |

### 1.10 Entity/Model Detection Patterns (reusable for SDL scan)

| Pattern | Line | Detects |
|---------|------|---------|
| `_RE_ENTITY_INDICATOR_CS` | 442 | `[Table]`, `DbContext`, `: DbContext` |
| `_RE_ENTITY_INDICATOR_TS` | 445 | `@Entity(`, `Schema(` |
| `_RE_ENTITY_INDICATOR_PY` | 448 | `models.Model`, `Base.metadata`, `declarative_base`, class inheriting Base |
| `_RE_ENTITY_DIR` | 451 | Entity/Model/Domain directories |

### 1.11 Regex Pattern Reference for SDL Scan

**Existing patterns that detect relevant constructs for SDL:**

| Existing Pattern | Line | What It Matches | Reuse for SDL? |
|-----------------|------|-----------------|----------------|
| `_RE_DB_CSHARP_NAV_PROP` | 410 | C# navigation properties (`public virtual Entity X {}`) | YES — detect .Include() targets |
| `_RE_DB_CSHARP_FK_PROP` | 407 | C# FK properties (`public int XId {}`) | YES — FK implies joinable data |
| `_RE_DB_SQL_STRING` | 312 | Raw SQL keywords | YES — detect SELECT without JOIN |

---

## 2. agents.py — Prompt Injection Points

**File:** `src/agent_team/agents.py`

### 2.1 ARCHITECT_PROMPT

| Section | Line | Purpose |
|---------|------|---------|
| `## Service-to-API Wiring Plan` | 921 | Mandates SVC-xxx entries for every frontend service method |
| `### EXACT FIELD SCHEMAS IN SVC-xxx TABLE` | 936 | Forces field names+types in DTO columns |
| `## Status/Enum Registry` | 955 | Mandates ENUM-001..003 status tracking |
| `## Milestone Handoff Preparation` | 980 | Response shape documentation |

**New SDL content should go after the Status/Enum Registry section (~line 978) as a new `## Silent Data Loss Prevention` section.**

### 2.2 CODE_WRITER_PROMPT

| Section | Line | Purpose |
|---------|------|---------|
| `ZERO MOCK DATA POLICY` | 1017 | Absolute no-mock rule |
| `## API CONTRACT COMPLIANCE` | 1032 | SVC-xxx field name enforcement |
| `FIX CYCLE AWARENESS` | 1051 | Read previous fix logs |
| `MILESTONE HANDOFF AWARENESS` | 1055 | Use handoff endpoints |

**New SDL content should go after the API CONTRACT COMPLIANCE section (~line 1050) as a new `## SILENT DATA LOSS PREVENTION` subsection within the code-writer instructions.**

### 2.3 CODE_REVIEWER_PROMPT

| Section | Line | Purpose |
|---------|------|---------|
| `## API Contract Field Verification` | 1261 | API-001/002/003 field-level checks |
| `## Enum/Status Registry Verification` | 1308 | ENUM-001..003 verification |
| `## Mock Data Detection` | 1342 | MOCK pattern scanning |

**New SDL review duties should go after the Enum/Status Registry Verification section (~line 1321) as a new `## Silent Data Loss Verification` section.**

### 2.4 Formatting Conventions (MUST follow)

- Section headers: `## Section Name (MANDATORY for condition)`
- Pattern IDs: `XXX-NNN` (uppercase prefix, 3-digit zero-padded number)
- Severity language: `VIOLATION = AUTOMATIC REVIEW FAILURE` / `HARD FAILURE` / `= BLOCKING`
- Conditional prefixes: `For .NET backends:`, `For TypeScript/Angular:`
- Subsection bullets use numbered lists with lettered sub-items
- "MANDATORY" keyword in parentheses after section title

---

## 3. e2e_testing.py — E2E Prompt Templates

**File:** `src/agent_team/e2e_testing.py`

| Constant | Line | Purpose |
|----------|------|---------|
| `BACKEND_E2E_PROMPT` | 556 | Backend API E2E testing instructions |
| `FRONTEND_E2E_PROMPT` | 705 | Playwright browser testing instructions |
| `detect_app_type()` | 60 | Detects .NET, Python, Angular, React, Vue, NestJS from package.json/requirements.txt |

### 3.1 detect_app_type() Details

- Returns `AppTypeInfo` dataclass
- Checks `package.json` dependencies for framework detection
- Detects: express, @nestjs/core, next, react, vue, @angular/core
- Detects: prisma, mongoose, sequelize for DB type
- Also checks `requirements.txt`, `pyproject.toml` for Python frameworks
- Key fields: `has_backend: bool`, `has_frontend: bool`, `backend_framework: str`, `frontend_framework: str`

---

## 4. config.py — Configuration Points

**File:** `src/agent_team/config.py`

### 4.1 PostOrchestrationScanConfig (line 293)

```python
@dataclass
class PostOrchestrationScanConfig:
    mock_data_scan: bool = True
    ui_compliance_scan: bool = True
    api_contract_scan: bool = True
    max_scan_fix_passes: int = 1
```

**New field needed:** `silent_data_loss_scan: bool = True`

### 4.2 _dict_to_config() — PostOrchestrationScanConfig parsing (line 1164)

```python
if "post_orchestration_scans" in data and isinstance(data["post_orchestration_scans"], dict):
    pos = data["post_orchestration_scans"]
    for key in ("mock_data_scan", "ui_compliance_scan", "api_contract_scan", "max_scan_fix_passes"):
        if key in pos:
            user_overrides.add(f"post_orchestration_scans.{key}")
```

**Action:** Add `"silent_data_loss_scan"` to the key list at line 1166, and add the field to the PostOrchestrationScanConfig constructor at line 1176.

### 4.3 apply_depth_quality_gating() — quick block (line 512)

```python
if depth == "quick":
    _gate("post_orchestration_scans.mock_data_scan", False, ...)
    _gate("post_orchestration_scans.ui_compliance_scan", False, ...)
    _gate("post_orchestration_scans.api_contract_scan", False, ...)
```

**Action:** Add `_gate("post_orchestration_scans.silent_data_loss_scan", False, ...)` at line ~519 (after api_contract_scan gate).

### 4.4 AgentTeamConfig (line 404)

The `post_orchestration_scans` field at line 424 uses `PostOrchestrationScanConfig` — no change needed there since adding the field to the dataclass suffices.

---

## 5. cli.py — Pipeline Wiring

**File:** `src/agent_team/cli.py`

### 5.1 Post-Orchestration Pipeline ORDER

The scan blocks appear in this sequence in `main()`:

1. **Mock data scan** — `config.post_orchestration_scans.mock_data_scan` OR `config.milestone.mock_data_scan`
2. **UI compliance scan** — `config.post_orchestration_scans.ui_compliance_scan` OR `config.milestone.ui_compliance_scan`
3. **Integrity scans** — `config.integrity_scans.deployment_scan`, `.asset_scan`, `.prd_reconciliation`
4. **Database scans** — `config.database_scans.dual_orm_scan`, `.default_value_scan`, `.relationship_scan`
5. **API contract scan** — `config.post_orchestration_scans.api_contract_scan` (line 4884)
6. **E2E Testing Phase** — `config.e2e_testing.enabled` (line 4932)
7. **Browser Testing Phase** — `config.browser_testing.enabled`

**SDL scan insertion point: AFTER API contract scan (line 4930), BEFORE E2E Testing Phase (line 4932).**

### 5.2 Scan Block Template (from API contract scan, lines 4884-4930)

```python
# -------------------------------------------------------------------
# Post-orchestration: API Contract Verification scan
# -------------------------------------------------------------------
if config.post_orchestration_scans.api_contract_scan:
    try:
        from .quality_checks import run_api_contract_scan
        from .e2e_testing import detect_app_type as _detect_app
        _app_info = _detect_app(Path(cwd))
        if _app_info.has_backend and _app_info.has_frontend:
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                api_contract_violations = run_api_contract_scan(Path(cwd), scope=scan_scope)
                if api_contract_violations:
                    if _fix_pass > 0:
                        print_info(f"API contract scan pass {_fix_pass + 1}: {len(api_contract_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"API contract scan: {len(api_contract_violations)} "
                            f"field mismatch violation(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("api_contract_fix")
                    if _max_passes > 0:
                        try:
                            api_fix_cost = asyncio.run(_run_api_contract_fix(
                                cwd=cwd,
                                config=config,
                                api_violations=api_contract_violations,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += api_fix_cost
                        except Exception as exc:
                            print_warning(f"API contract fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("API contract scan: 0 violations (clean)")
                    else:
                        print_info(f"API contract scan pass {_fix_pass + 1}: all violations resolved")
                    break
        else:
            print_info("API contract scan: skipped (not a full-stack app).")
    except Exception as exc:
        print_warning(f"API contract scan failed: {exc}")
```

### 5.3 _run_api_contract_fix() — Template for _run_silent_data_loss_fix() (line 1518)

```python
async def _run_api_contract_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    api_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
```

**Key elements to replicate:**
1. Guard: `if not violations: return 0.0`
2. `print_info(f"Running ... fix pass ({len(violations)} violations)")`
3. Violation text formatting: `f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"`
4. Fix prompt with `[PHASE: XXX]` header
5. Fix cycle log injection (`config.tracking_documents.fix_cycle_log`)
6. `_build_options()` call
7. `ClaudeSDKClient` context manager with `query` + `_process_response`
8. `current_phase="xxx_fix"` in _process_response
9. Intervention draining
10. Exception handling with `print_warning`

### 5.4 Variables Available in Scope at Insertion Point

At line 4930 (after API contract scan), these variables are in scope:
- `cwd: str` — working directory
- `config: AgentTeamConfig`
- `scan_scope: ScanScope | None`
- `effective_task: str`
- `constraints: list`
- `intervention: InterventionQueue`
- `depth: str | DepthDetection`
- `_use_milestones: bool`
- `_current_state: RunState | None`
- `recovery_types: list[str]`
- `recovery_passes: int`

---

## 6. display.py — type_hints Dict

**File:** `src/agent_team/display.py`

### 6.1 type_hints Dict (line 623)

Located inside `print_recovery_report()` function. Current entries:

```python
type_hints = {
    "contract_generation": "...",
    "review_recovery": "...",
    "mock_data_fix": "...",
    "ui_compliance_fix": "...",
    "deployment_integrity_fix": "...",
    "asset_integrity_fix": "...",
    "prd_reconciliation_mismatch": "...",
    "database_dual_orm_fix": "...",
    "database_default_value_fix": "...",
    "database_relationship_fix": "...",
    "api_contract_fix": "...",          # <-- line 634
    "e2e_backend_fix": "...",
    "e2e_frontend_fix": "...",
    "e2e_coverage_incomplete": "...",
    "browser_testing_failed": "...",
    "browser_testing_partial": "...",
    "artifact_recovery": "...",
    "gate5_enforcement": "...",
}
```

**Action:** Add `"silent_data_loss_fix": "Silent data loss patterns detected — missing Includes, partial Selects, or dropped fields"` after line 634 (after `"api_contract_fix"`).

---

## 7. code_quality_standards.py — Standards Constants

**File:** `src/agent_team/code_quality_standards.py`

### 7.1 _AGENT_STANDARDS_MAP (line 614)

```python
_AGENT_STANDARDS_MAP: dict[str, list[str]] = {
    "code-writer": [FRONTEND_STANDARDS, BACKEND_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS],
    "code-reviewer": [CODE_REVIEW_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS],
    "test-runner": [TESTING_STANDARDS, E2E_TESTING_STANDARDS],
    "debugger": [DEBUGGING_STANDARDS],
    "architect": [ARCHITECTURE_QUALITY_STANDARDS, DATABASE_INTEGRITY_STANDARDS],
}
```

### 7.2 get_standards_for_agent() (line 623)

```python
def get_standards_for_agent(agent_name: str) -> str:
    standards = _AGENT_STANDARDS_MAP.get(agent_name, [])
    return "\n\n".join(standards) if standards else ""
```

### 7.3 Where to Add New Constant

New `SILENT_DATA_LOSS_STANDARDS` constant should be defined at ~line 611 (after `API_CONTRACT_STANDARDS` ends at line 611, before `_AGENT_STANDARDS_MAP`).

Then add to `_AGENT_STANDARDS_MAP`:
- `"code-writer"` list: append `SILENT_DATA_LOSS_STANDARDS`
- `"code-reviewer"` list: append `SILENT_DATA_LOSS_STANDARDS`
- `"architect"` list: append `SILENT_DATA_LOSS_STANDARDS`

---

## 8. Implementation Checklist

### 8.1 New Patterns to Detect (SDL-001..SDL-005)

| Pattern ID | Severity | Description | Detection Strategy |
|-----------|----------|-------------|-------------------|
| SDL-001 | error | Missing `.Include()` / `.ThenInclude()` for navigation properties used in response | Parse C# LINQ queries: find `.Select()` or `.FirstOrDefault()` without `.Include()` for nav props referenced in the projection |
| SDL-002 | error | Partial `.Select()` projection drops fields defined in SVC-xxx schema | Compare fields in `.Select(x => new { ... })` against SVC-xxx response_fields |
| SDL-003 | warning | Missing `.populate()` (Mongoose) or eager loading (TypeORM/Prisma `include`) | Same as SDL-001 but for JS/TS ORMs |
| SDL-004 | warning | DTO mapping drops fields (AutoMapper profile or manual mapping missing properties) | Detect AutoMapper `CreateMap<Source,Dest>()` without `ForMember` for nav props; detect manual `new Dto { }` missing fields |
| SDL-005 | info | Response DTO has fewer properties than entity (potential silent data loss) | Compare entity property count against DTO property count (heuristic) |

### 8.2 Files to Modify (7 files)

| # | File | Changes |
|---|------|---------|
| 1 | `quality_checks.py` | New regex patterns (SDL-001..005), `run_silent_data_loss_scan()` function |
| 2 | `config.py` | `silent_data_loss_scan` field on PostOrchestrationScanConfig, `_dict_to_config()` update, `apply_depth_quality_gating()` quick gate |
| 3 | `agents.py` | SDL prevention prompts in ARCHITECT, CODE_WRITER, CODE_REVIEWER |
| 4 | `code_quality_standards.py` | `SILENT_DATA_LOSS_STANDARDS` constant, `_AGENT_STANDARDS_MAP` update |
| 5 | `cli.py` | `_run_silent_data_loss_fix()` async function, scan block wiring after API contract |
| 6 | `display.py` | `"silent_data_loss_fix"` entry in type_hints |
| 7 | `e2e_testing.py` | Optional: Add SDL awareness to BACKEND_E2E_PROMPT |

### 8.3 Detection Approach (Regex-Based, No AST)

All existing scans are regex-based (no AST parsing). The SDL scan MUST follow the same approach.

**C# `.Include()` detection (SDL-001):**
```python
# Step 1: Find files with navigation properties AND LINQ queries
# Step 2: For each nav prop, check if .Include("NavProp") exists in the query chain
_RE_SDL_CSHARP_INCLUDE = re.compile(r'\.Include\s*\(\s*\w*\s*=>\s*\w+\.(\w+)\)', re.IGNORECASE)
_RE_SDL_CSHARP_QUERY = re.compile(r'\.(?:FirstOrDefault|ToList|Where|Select|SingleOrDefault)\s*\(')
```

**C# partial Select detection (SDL-002):**
```python
# Match: .Select(x => new SomeDto { Field1 = x.Field1, Field2 = x.Field2 })
# Compare projected fields against SVC-xxx response_fields
_RE_SDL_CSHARP_SELECT = re.compile(r'\.Select\s*\(\s*\w+\s*=>\s*new\s+\w+\s*\{([^}]+)\}')
```

**TypeScript/Prisma include detection (SDL-003):**
```python
# Prisma: findMany({ include: { relation: true } })
# TypeORM: { relations: ['relation'] }
_RE_SDL_PRISMA_INCLUDE = re.compile(r'include\s*:\s*\{([^}]+)\}')
_RE_SDL_TYPEORM_RELATIONS = re.compile(r'relations\s*:\s*\[([^\]]+)\]')
```

**Mongoose populate detection (SDL-003):**
```python
_RE_SDL_MONGOOSE_POPULATE = re.compile(r'\.populate\s*\(\s*[\'"](\w+)[\'"]')
```

### 8.4 Cross-Reference Strategy (SDL-002)

The SDL-002 check requires cross-referencing:
1. Parse SVC-xxx response_fields from REQUIREMENTS.md (reuse `_parse_svc_table()`)
2. Find backend handler files (reuse `_find_files_by_pattern()` with controller/handler patterns)
3. In each handler, find `.Select()` projections
4. Extract projected field names from the projection
5. Compare against response_fields — any missing field = SDL-002 violation

This follows the same pattern as `_check_backend_fields()` (line 2800).

### 8.5 Scope Filtering

Follow the H2 pattern from v6.0 review: detection phase uses full file list, violation-reporting filters by scope. This prevents false negatives where the navigation property definition is in an unscoped file.

---

## 9. Key Gotchas for Implementers

1. **Violation fields are `.check`, `.file_path`, `.line`** — NOT `.code`, `.file`. Burned once at cli.py:5131.

2. **`_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]`** — all callers must unpack.

3. **Scope filtering**: Use `scope_set = set(scope.changed_files)` then `f.resolve() in scope_set` for path comparison (resolve needed for Windows path normalization).

4. **Windows encoding**: Use `write_text(encoding="utf-8")` for files with Unicode chars.

5. **File size guard**: Check `len(content) > _MAX_FILE_SIZE` before processing (100KB cap).

6. **Test files**: Tests need `patch("dotenv.load_dotenv")` when deleting ANTHROPIC_API_KEY from env.

7. **Pre-existing test failures**: `test_mcp_servers.py` has 2 pre-existing failures — do not count these as regressions.

8. **Regex compilation**: All patterns must be compiled at module level (not inside functions) for performance.

9. **Entity detection**: For C# entities, use `_RE_ENTITY_INDICATOR_CS` (line 442) and `_RE_ENTITY_DIR` (line 451) to identify entity files before scanning for navigation properties.

10. **Backward compatibility**: Rows without field schemas (`_RE_FIELD_SCHEMA` returns `{}`) should produce zero violations — same as API contract scan.
