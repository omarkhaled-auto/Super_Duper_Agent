# Agent-Team Exhaustive Implementation — Database Integrity Upgrades

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (5 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `scanner-architect` | `superpowers:code-reviewer` | Phase 1 — Read ALL existing quality checks, scan functions, config dataclasses, cli.py wiring, agent prompts. Map existing patterns. Produce architecture report for implementation agents. |
| `impl-scans` | `general-purpose` | Phase 2A — Implement the 3 static scan functions (dual ORM, default values, relationship wiring) in `quality_checks.py` + config in `config.py` + CLI wiring in `cli.py` + standards in `code_quality_standards.py` following existing patterns exactly |
| `impl-prompts` | `general-purpose` | Phase 2B — Implement the 2 prompt injections (seed data completeness, enum/status registry) in `agents.py` following existing prompt patterns exactly |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest, diagnose and fix failures, iterate until green |
| `wiring-verifier` | `general-purpose` | Phase 4 — Trace cli.py execution flow, verify all 3 scans trigger correctly, config gating works, results feed into recovery report, crash isolation exists. Write wiring verification tests. |

### Coordination Flow

```
Wave 1 (solo): scanner-architect reads entire codebase
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-scans (scan functions + config + CLI wiring + standards)
                  + impl-prompts (prompt injections in agents.py)
    |                         |
    Both read ARCHITECTURE_REPORT.md first
    |                         |
    +-------------------------+
              |
Wave 3 (parallel): test-engineer (writes ALL tests)
                  + wiring-verifier (traces cli.py, writes wiring tests)
    |                                         |
    +=========================================+
              |
Wave 4 (solo): test-engineer runs full suite, fixes failures
              |
Wave 5: You (team lead) collect all results -> final report
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **scanner-architect runs first and alone.** Its ARCHITECTURE_REPORT.md is the blueprint for all implementation.
- **impl-scans and impl-prompts run simultaneously.** They work on different files:
  - impl-scans: `src/agent_team/quality_checks.py`, `src/agent_team/config.py`, `src/agent_team/cli.py` (scan wiring only), `src/agent_team/code_quality_standards.py`
  - impl-prompts: `src/agent_team/agents.py`
- **test-engineer and wiring-verifier run simultaneously** after both impl agents complete.
- **After Wave 3 completes,** test-engineer runs `pytest tests/ -v --tb=short` and iterates on failures until all pass (except pre-existing known failures in test_mcp_servers.py).
- **Shut down all agents** after Wave 4 completes. Collect results and write the final report yourself.

### Critical Rules for Agents

- scanner-architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-scans: Can create/edit `quality_checks.py`, `config.py`, `cli.py` (scan wiring section only), `code_quality_standards.py`. Do NOT touch `agents.py`.
- impl-prompts: Can edit `agents.py` only. Do NOT touch `quality_checks.py`, `config.py`, `cli.py`, or `code_quality_standards.py`.
- test-engineer: Can create/edit test files AND source files (to fix bugs found during testing).
- wiring-verifier: READ ONLY for source files. Can create test files for wiring verification.
- If any agent finds a conflict or architectural issue, send it immediately — don't wait for full completion.

---

# Database Integrity Upgrades — Agent-Team Production Hardening

## Background — Why This Exists

The agent-team system builds full-stack applications through multi-agent orchestration. The agents
write database schemas, ORM models, API endpoints, and frontend services. But agents have no
awareness of CROSS-LAYER type consistency. Agent A designs the ORM model with string enums.
Agent B writes raw SQL queries comparing those same columns as integers. Agent C seeds the database
with records that don't satisfy the app's own query filters. These bugs are the most expensive
to debug because they fail SILENTLY — no errors, no crashes, just wrong data or missing results.

These 5 failure patterns were discovered during the Bayan Tender Management System project
(104K LOC enterprise procurement app). Each one cost hours of debugging because the symptoms
were invisible until a user reported "I can't find my data."

### Failure 1: Dual ORM Type Mismatch

Bayan used EF Core for most data access but Dapper for performance-critical queries. EF Core
stored bid status as a string enum ("Opened"). Dapper raw SQL queries compared it as an integer
(`WHERE status = 2`). Same column, two access methods, different type assumptions. The bid opening
flow returned zero results. No error. No exception. Just an empty result set. This went undetected
through all automated tests because unit tests only tested one ORM at a time.

### Failure 2: Seed Data Incompleteness

User accounts were seeded with `email_verified=false` by default. The API's user listing query
filtered on `email_verified=true`. Every fresh deployment had invisible users. The system "worked"
but nobody could find any users until someone manually edited the database. This pattern applies
to any boolean flag or status field that a query filters on — if the seed data doesn't match the
filter, seeded records are invisible to the application.

### Failure 3: Missing Default Values

Boolean columns without explicit defaults. Nullable columns where the app code assumed non-null.
The create path (built by Agent A) inserted a record with NULL in a column. The read path (built
by Agent B) called `.ToString()` on that column without a null check. Silent NullReferenceException
caught by a global handler, returned as a generic 500. The user saw "Something went wrong" with
no indication that a missing default was the root cause.

### Failure 4: Status/Enum String Mismatches

Frontend called `updateTenderStatus('cancelled')`. Backend enum had `'Closed'`, not `'Cancelled'`.
The API accepted the string parameter without validation, stored a status value that no query
ever matched. The tender disappeared from every list view. No error anywhere. The record existed
in the database with an orphaned status value that no code path could find.

### Failure 5: Relationship Wiring Gaps

Foreign key columns existed in the database migration. But the entity configuration was missing
`.HasMany()` or `.WithOne()` calls. EF Core generated the correct SQL schema but navigation
properties returned null when eager loading. Any query using `.Include(x => x.RelatedEntity)`
silently returned null instead of the related data. Again — no error, just missing data.

## What We're Building

5 upgrades split into two categories:

**Category A: Static Scans (3 scan functions in quality_checks.py)**
These scan the codebase WITHOUT running the app. They detect structural inconsistencies by reading
source files and comparing patterns. They plug into the existing quality checks pipeline alongside
`run_mock_data_scan()`, `run_ui_compliance_scan()`, `run_deployment_scan()`, and `run_asset_scan()`.
Pattern IDs: DB-001 through DB-008.

**Category B: Prompt Injections (2 prompt policies in agents.py)**
These add requirements to the architect and code-reviewer prompts so agents produce correct
database code in the FIRST PLACE, rather than catching bugs after the fact. Pattern IDs: SEED-001
through SEED-003, ENUM-001 through ENUM-003.

---

## PHASE 1: ARCHITECTURE DISCOVERY (scanner-architect)

Before implementing ANYTHING, the scanner-architect must read the codebase and produce
`.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: Existing Scan Function Pattern

- Read `src/agent_team/quality_checks.py` end to end (~1601 lines)
- Document the `Violation` dataclass (line 35):
  - Fields: `check: str`, `message: str`, `file_path: str`, `line: int`, `severity: str`
  - This is the EXACT return type element for all scan functions
- Document `_MAX_VIOLATIONS = 100` (line 50) — how it's used for early exit in scan loops
- Document `_SEVERITY_ORDER` dict (line 64) — `{"error": 0, "warning": 1, "info": 2}`
- Document `_SKIP_DIRS` frozenset (line 54) — directories excluded from scanning
- Document `_iter_source_files()` (line 967):
  - Signature: `(project_root: Path) -> list[Path]`
  - Uses `os.walk()` with in-place pruning of `_SKIP_DIRS`
  - Calls `_should_scan_file()` (line 951) for size/extension filtering
- Document the per-file check function signature pattern:
  `(content: str, rel_path: str, extension: str) -> list[Violation]`
  Used by: `_check_ts_any`, `_check_mock_data_patterns`, `_check_ui_compliance`, etc. (12 functions)
- Document the public scan function signature pattern:
  `(project_root: Path) -> list[Violation]`
  Used by: `run_mock_data_scan` (line 1049), `run_ui_compliance_scan` (line 1082),
  `run_deployment_scan` (line 1357), `run_asset_scan` (line 1507), etc.
- Document the sorting pattern applied at the end of every scan:
  ```python
  violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
  ```
- Document ALL existing pattern IDs to avoid collisions:
  FRONT-007/010/016, BACK-001/002/016/017/018, SLOP-001/003, MOCK-001..007, UI-001..004,
  E2E-001..007, DEPLOY-001..004, ASSET-001..003, PRD-001
  **New scans MUST use DB-001 through DB-008 (no collisions)**

### 1B: Targeted Scan Pattern (run_mock_data_scan / run_deployment_scan)

The new database scans are TARGETED scans (not the generic `run_spot_checks` that runs _ALL_CHECKS).
Study the targeted scan pattern closely:

- Read `run_mock_data_scan()` (line 1049):
  - How it uses `_iter_source_files()` to get files
  - How it filters to only service-related files (regex on path)
  - How it calls the internal `_check_mock_data_patterns()` per file
  - How it enforces `_MAX_VIOLATIONS` cap
  - How it sorts and returns
- Read `run_deployment_scan()` (line 1357):
  - How it handles conditional scanning (requires docker-compose.yml to exist)
  - How it calls multiple internal helper functions
  - How it builds violations from cross-file comparisons (not per-line regex)
  - This is the closest pattern to the new database scans (cross-file analysis)
- Read `run_asset_scan()` (line 1507):
  - How it resolves references across files (`_resolve_asset()`)
  - Another cross-file analysis pattern

### 1C: Config Integration Pattern

- Read `src/agent_team/config.py` (~957 lines)
- Document `IntegrityScanConfig` (line 325):
  - 3 boolean fields: `deployment_scan`, `asset_scan`, `prd_reconciliation` — all `True`
  - Docstring style and content
  - This is the CLOSEST pattern for the new database scan config
- Document how it's wired in `AgentTeamConfig` (line 355):
  ```python
  integrity_scans: IntegrityScanConfig = field(default_factory=IntegrityScanConfig)
  ```
- Document how it's loaded in `_dict_to_config()` (line 899):
  ```python
  if "integrity_scans" in data and isinstance(data["integrity_scans"], dict):
      isc = data["integrity_scans"]
      cfg.integrity_scans = IntegrityScanConfig(
          deployment_scan=isc.get("deployment_scan", cfg.integrity_scans.deployment_scan),
          ...
      )
  ```
- Document the `E2ETestingConfig` validation pattern (line 920):
  - `max_fix_retries >= 1` check → `raise ValueError(...)`
  - Range validation pattern for reference
- **CRITICAL DECISION:** Should database scans extend `IntegrityScanConfig` with 3 more booleans,
  or get their own `DatabaseScanConfig` dataclass? Recommend based on:
  - IntegrityScanConfig currently has 3 fields (deployment/asset/PRD) — adding 3 more makes 6
  - The database scans are conceptually different (data integrity vs infrastructure integrity)
  - A separate `DatabaseScanConfig` is more consistent with the existing separation
  - **Recommendation: Create `DatabaseScanConfig` as a separate dataclass** following the exact
    same pattern as `IntegrityScanConfig`

### 1D: CLI Post-Orchestration Wiring Pattern

- Read `src/agent_team/cli.py` post-orchestration section
- Document the EXACT execution order with line numbers:
  1. TASKS.md Diagnostic (line 3187)
  2. Contract Generation Recovery (line 3221)
  3. Convergence Health Check (line 3272)
  4. Mock Data Scan (line 3468)
  5. UI Compliance Scan (line 3500)
  6. Deployment Integrity Scan (line 3535)
  7. Asset Integrity Scan (line 3564)
  8. PRD Reconciliation Scan (line 3593)
  9. **← NEW DATABASE SCANS GO HERE (after line ~3617, before E2E) ←**
  10. E2E Testing Phase (line 3622)
  11. Recovery Report (line 3826)
- Document the EXACT wiring pattern by studying Deployment Integrity Scan (line 3535):
  ```python
  if config.integrity_scans.deployment_scan:
      try:
          from .quality_checks import run_deployment_scan
          violations = run_deployment_scan(Path(cwd))
          if violations:
              print_warning(f"Deployment scan: {len(violations)} issue(s) found.")
              recovery_types.append("deployment_integrity_fix")
              try:
                  fix_cost = asyncio.run(_run_integrity_fix(
                      cwd=cwd, config=config, violations=violations,
                      scan_type="deployment", task_text=args.task,
                      constraints=constraints, intervention=intervention,
                      depth=depth if not _use_milestones else "standard",
                  ))
                  if _current_state:
                      _current_state.total_cost += fix_cost
              except Exception as exc:
                  print_warning(f"Deployment fix recovery failed: {exc}")
      except Exception as exc:
          print_warning(f"Deployment scan failed: {exc}")
  ```
- Document `recovery_types` initialization (line 3185): `recovery_types: list[str] = []`
- Document all existing recovery type strings:
  `"contract_generation"`, `"review_recovery"`, `"mock_data_fix"`, `"ui_compliance_fix"`,
  `"deployment_integrity_fix"`, `"asset_integrity_fix"`, `"prd_reconciliation_mismatch"`,
  `"e2e_backend_fix"`, `"e2e_frontend_fix"`
- Document `_run_integrity_fix()` signature (line 1670):
  ```python
  async def _run_integrity_fix(
      cwd, config, violations, scan_type, task_text=None,
      constraints=None, intervention=None, depth="standard"
  ) -> float:
  ```
  This function handles BOTH deployment AND asset fix via the `scan_type` parameter.
  **New database scans should reuse this function with `scan_type="database"`**.

**IMPORTANT:** The Tracking Documents implementation (TRACKING_DOCUMENTS_IMPLEMENTATION.md) will
be applied BEFORE this implementation. It adds:
- `TrackingDocumentsConfig` to config.py
- `tracking_documents.py` new module
- E2E coverage matrix generation BEFORE E2E tests in cli.py
- Fix cycle log integration into existing fix functions
- Milestone handoff wiring into `_run_prd_milestones()`

These changes may shift line numbers. The scanner-architect MUST verify actual line numbers
by reading the source, not trusting this prompt.

### 1E: Agent Prompt Injection Pattern

- Read `src/agent_team/agents.py`
- Document `CODE_WRITER_PROMPT` (line 948):
  - Section order: Tasks → Rules → ZERO MOCK DATA POLICY (line 975) → UI COMPLIANCE POLICY (line 1019) → Validation → DRY → Transactions → Code Quality Standards
  - **New policies insert AFTER UI COMPLIANCE POLICY (line ~1042), BEFORE Validation Middleware (line ~1043)**
- Document the EXACT format of ZERO MOCK DATA POLICY (lines 975-994):
  ```
  - **ZERO MOCK DATA POLICY** (ABSOLUTE — NO EXCEPTIONS):
    [Multi-line description with indented bullet dashes]
    VIOLATION = AUTOMATIC REVIEW FAILURE.
  ```
  Key format characteristics:
  - Bold policy name with severity parenthetical: `**NAME** (ABSOLUTE — NO EXCEPTIONS):`
  - Indented bullet list with `  - ` prefix for each pattern/rule
  - Framework-specific examples inline
  - Terminal severity statement: `VIOLATION = AUTOMATIC REVIEW FAILURE.`
- Document `CODE_REVIEWER_PROMPT` (line 1084):
  - Where UI Compliance Verification is (line 1154)
  - **New reviewer verification sections insert AFTER UI Compliance Verification (line ~1169), BEFORE Orphan Detection (line ~1170)**
  - Reviewer verification format:
    ```
    ## [Policy Name] Verification (MANDATORY)
    For each [item type]:
    1. [Verification step]
    2. [Verification step]
    If violations found: Review Log entry with "[ITEM-ID]", FAIL verdict, list violations.
    ```
- Document `ARCHITECT_PROMPT` (line 836):
  - Where Service-to-API Wiring Plan is (line ~921)
  - Where Milestone Handoff Preparation is (line ~938) — THIS EXISTS (added by Tracking Documents)
  - **New architect sections insert BETWEEN Service-to-API Wiring Plan and Milestone Handoff Preparation**

### 1F: Quality Standards Pattern

- Read `src/agent_team/code_quality_standards.py`
- Document `_AGENT_STANDARDS_MAP` (line 537):
  ```python
  _AGENT_STANDARDS_MAP: dict[str, list[str]] = {
      "code-writer": [FRONTEND_STANDARDS, BACKEND_STANDARDS],
      "code-reviewer": [CODE_REVIEW_STANDARDS],
      "test-runner": [TESTING_STANDARDS, E2E_TESTING_STANDARDS],
      "debugger": [DEBUGGING_STANDARDS],
      "architect": [ARCHITECTURE_QUALITY_STANDARDS],
  }
  ```
- Document `BACKEND_STANDARDS` (line 124):
  - Existing database-related entries: BACK-002 (N+1), BACK-010 (indexes), BACK-016 (transactions), BACK-019 (FK references)
  - Format: `**BACK-NNN: Short Name**` followed by `- NEVER ...` and `- FIX: ...`
  - New database standards should be added to BACKEND_STANDARDS after BACK-020
  - Use IDs: BACK-021 through BACK-028 (mapped from DB-001..008 concepts)
- Document `E2E_TESTING_STANDARDS` (line 444) as format reference:
  - Section header: `## E2E TESTING QUALITY STANDARDS (APPLIED DURING E2E PHASE)`
  - Alternatively, create a standalone `DATABASE_INTEGRITY_STANDARDS` constant (cleaner separation)
- Document `get_standards_for_agent()` function (line 546):
  ```python
  def get_standards_for_agent(agent_name: str) -> str:
      standards = _AGENT_STANDARDS_MAP.get(agent_name, [])
      return "\n\n".join(standards) if standards else ""
  ```

### 1G: State and Resume Pattern

- Read `src/agent_team/state.py`
- Document `RunState.completed_phases` (line 27): `list[str]`
- Document `RunState.artifacts` (line 29): `dict[str, str]`
- Determine: Do database scans need their own `completed_phases` marker?
  - Compare with deployment/asset scans — they do NOT have individual phase markers
  - All integrity scans are part of the `"post_orchestration"` phase
  - **Recommendation: No separate phase marker needed for database scans**
- Document `RunSummary.recovery_types` (line 66): `list[str]`

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1G),
with exact file paths, line numbers, function names, and integration points. This is the blueprint
for Phase 2.

---

## PHASE 2A: IMPLEMENT STATIC SCANS + CONFIG + CLI WIRING (impl-scans)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Scan 1: Dual Data Access Type Consistency (`run_dual_orm_scan`)

**What it detects:** Projects using TWO+ data access methods (e.g., EF Core + Dapper,
Prisma + raw SQL, SQLAlchemy + raw queries) with type mismatches on the same columns.

**New scan function in `quality_checks.py`:**

```python
def run_dual_orm_scan(project_root: Path) -> list[Violation]:
    """Detect type mismatches between ORM models and raw SQL queries.

    Only runs if 2+ data access methods are detected (ORM + raw queries).
    Skips gracefully if only one access method found.

    Pattern IDs: DB-001 (enum mismatch), DB-002 (boolean mismatch), DB-003 (datetime mismatch)
    """
```

**How it works:**

1. **Detect data access methods.** Scan `package.json`, `requirements.txt`, `*.csproj`, and source
   files for indicators of multiple data access methods. Check for:

   ORM indicators (at least one must be present):
   - C#: `Microsoft.EntityFrameworkCore` in csproj, `DbContext` in source, `[Table]`/`[Column]` attributes
   - TypeScript: `prisma` or `typeorm` or `sequelize` or `mongoose` in package.json
   - Python: `sqlalchemy` or `django` in requirements.txt, `Base.metadata` or `models.Model` in source

   Raw query indicators (at least one must ALSO be present):
   - C#: `Dapper` in csproj, `SqlConnection`, `QueryAsync`, `ExecuteAsync` in source
   - TypeScript: `knex` or `pg` or `mysql2` in package.json, raw SQL strings (`SELECT`, `INSERT`, `WHERE`)
   - Python: `pymongo` (when mongoose also present), `cursor.execute()`, raw SQL strings

2. **If only ONE access method found → return empty list with no violations.**
   Print info message: `"Dual ORM scan: single data access method detected, skipping."`

3. **If TWO+ methods found:**

   a. Extract entity/model definitions from ORM files:
   - Property/field names
   - Types (especially enums, booleans, dates)
   - Table/column mappings if explicit

   b. Extract raw query patterns from source files:
   - Column names referenced in SQL strings (after `WHERE`, `SET`, `=`, in `SELECT`)
   - Type comparisons (integer literals vs string literals vs boolean)

   c. Cross-reference: For each column that appears in BOTH ORM models AND raw queries:
   - DB-001: ORM defines as string enum but raw SQL compares as integer (or vice versa)
   - DB-002: ORM defines as bool but raw SQL checks `0`/`1` vs `'true'`/`'false'`
   - DB-003: ORM defines datetime type but raw SQL uses incompatible format string

**Module-level regex constants** (add alongside existing patterns, after line ~246):

```python
# ── Dual ORM detection ──────────────────────────────────────────────
_RE_SQL_STRING = re.compile(
    r"""(?:SELECT|INSERT|UPDATE|DELETE|WHERE|SET|JOIN)\s""",
    re.IGNORECASE,
)
_RE_SQL_ENUM_INT_CMP = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*\d+""",
    re.IGNORECASE,
)
_RE_SQL_ENUM_STR_CMP = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*['"]""",
    re.IGNORECASE,
)
_RE_SQL_BOOL_INT = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*[01]\b""",
    re.IGNORECASE,
)
_RE_CSHARP_ENUM_PROP = re.compile(
    r"""public\s+(\w+)\s+(\w+)\s*\{""",
)
_RE_CSHARP_BOOL_PROP = re.compile(
    r"""public\s+bool\??\s+(\w+)\s*\{""",
)
# Add file extension sets for ORM/entity files
_EXT_ENTITY = frozenset({".cs", ".py", ".ts", ".js"})
```

**Severity:** All HIGH — these cause silent data corruption.

**Conditional:** Only runs if 2+ data access methods detected. Skip gracefully otherwise.

### Scan 2: Default Value & Nullability Verification (`run_default_value_scan`)

**What it detects:** Entity/model properties with no explicit default AND nullable properties
accessed without null checks.

**New scan function in `quality_checks.py`:**

```python
def run_default_value_scan(project_root: Path) -> list[Violation]:
    """Detect missing defaults and unsafe nullable access in entity models.

    Scans ORM entity/model files for boolean/enum properties without defaults
    and nullable properties used without null guards.

    Pattern IDs: DB-004 (missing default), DB-005 (nullable without null check)
    """
```

**How it works:**

1. **Find entity/model files.** Look for files containing ORM entity indicators:
   - C#: `[Table]` attribute, inherits `DbContext`, in `Entities/`/`Models/` folders
   - TypeScript: Prisma schema (`.prisma`), TypeORM `@Entity()` decorator, Mongoose `Schema()`
   - Python: SQLAlchemy `Base` subclass, Django `models.Model` subclass

2. **For each boolean or enum property:**
   - C#: `public bool IsActive { get; set; }` without `= false;` or `= true;`
   - C#: `public Status Status { get; set; }` without `= Status.Draft;`
   - Prisma: `isActive Boolean` without `@default(false)`
   - Django: `BooleanField()` without `default=` parameter
   - SQLAlchemy: `Column(Boolean)` without `default=` or `server_default=`
   - If no explicit default → **DB-004** (severity: MEDIUM)

3. **For each nullable property:**
   - C#: `string? Description`, `int? CategoryId`
   - Prisma: `description String?`
   - Python: `Optional[str]`, `Column(String, nullable=True)`
   - Search the codebase for usages of that property WITHOUT null checks:
     - C#: `.Property.Method()` without `?.` or `if (x.Property != null)` guard
     - TypeScript: `obj.property.method()` without `?.` or `if (obj.property)` guard
     - Python: `obj.property.method()` without `if obj.property:` guard
   - If unsafe access found → **DB-005** (severity: HIGH)

**Module-level regex constants:**

```python
# ── Default value detection ─────────────────────────────────────────
_RE_CSHARP_BOOL_NO_DEFAULT = re.compile(
    r"""public\s+bool\s+(\w+)\s*\{\s*get;\s*set;\s*\}(?!\s*=)""",
)
_RE_CSHARP_NULLABLE_PROP = re.compile(
    r"""public\s+(\w+)\?\s+(\w+)\s*\{""",
)
_RE_PRISMA_NO_DEFAULT = re.compile(
    r"""(\w+)\s+(?:Boolean|Int|String)\s*$""",
    re.MULTILINE,
)
_RE_DJANGO_BOOL_NO_DEFAULT = re.compile(
    r"""BooleanField\s*\(\s*\)""",
)
_RE_SQLALCHEMY_NO_DEFAULT = re.compile(
    r"""Column\s*\(\s*(?:Boolean|Enum)\b[^)]*\)(?!.*default)""",
    re.IGNORECASE,
)
```

**Conditional:** Always runs if entity/model files detected. Skips if no ORM entities found.

### Scan 3: ORM Relationship Completeness (`run_relationship_scan`)

**What it detects:** Foreign key columns missing navigation properties or relationship configuration.

**New scan function in `quality_checks.py`:**

```python
def run_relationship_scan(project_root: Path) -> list[Violation]:
    """Detect incomplete ORM relationship configurations.

    Finds FK columns without navigation properties, navigation properties
    without inverse relationships, and FKs with no relationship config at all.

    Pattern IDs: DB-006 (FK no nav), DB-007 (nav no inverse), DB-008 (FK no config)
    """
```

**How it works:**

1. **Extract all FK columns from entity files:**
   - C#: Properties ending in `Id` that aren't `Id` itself (e.g., `TenderId`, `UserId`, `CategoryId`)
   - TypeORM: `@ManyToOne()`, `@OneToMany()`, `@JoinColumn()` decorators
   - Prisma: `@relation` fields
   - Django: `ForeignKey()`, `OneToOneField()`, `ManyToManyField()`
   - SQLAlchemy: `ForeignKey()` in Column definition, `relationship()` calls

2. **For each FK column, verify:**

   a. A navigation property exists on the same entity:
   - C#: `public Tender Tender { get; set; }` matching `TenderId`
   - TypeORM: `@ManyToOne(() => Tender)` on same class
   - If missing → **DB-006** (severity: MEDIUM)

   b. The inverse navigation exists on the related entity:
   - C#: `public ICollection<Bid> Bids { get; set; }` on Tender class
   - TypeORM: `@OneToMany(() => Bid, bid => bid.tender)` on related class
   - If missing → **DB-007** (severity: LOW)

   c. Relationship configuration exists:
   - C#: `.HasMany().WithOne()` or `.HasOne().WithMany()` in `OnModelCreating` or `IEntityTypeConfiguration<>`
   - If NO navigation AND no configuration → **DB-008** (severity: HIGH)

3. **Special cases to handle correctly:**
   - Self-referential FKs (e.g., `ParentId` on same entity) — should still be flagged if no nav
   - Composite keys — skip these (they need manual configuration anyway)
   - Abstract/base classes — scan them too
   - Separate configuration files (C# `IEntityTypeConfiguration<T>`) — scan alongside entity files

**Module-level regex constants:**

```python
# ── Relationship completeness ───────────────────────────────────────
_RE_CSHARP_FK_PROP = re.compile(
    r"""public\s+(?:int|long|Guid|string)\??\s+(\w+Id)\s*\{""",
)
_RE_CSHARP_NAV_PROP = re.compile(
    r"""public\s+(?:virtual\s+)?(?:ICollection<|IList<|IEnumerable<|List<)?(\w+)>?\s+(\w+)\s*\{""",
)
_RE_CSHARP_HAS_MANY = re.compile(
    r"""\.Has(?:Many|One)\s*\(\s*\w*\s*=>\s*\w+\.(\w+)\)""",
)
_RE_TYPEORM_RELATION = re.compile(
    r"""@(?:ManyToOne|OneToMany|OneToOne|ManyToMany)\s*\(""",
)
_RE_DJANGO_FK = re.compile(
    r"""(?:ForeignKey|OneToOneField|ManyToManyField)\s*\(""",
)
_RE_SQLALCHEMY_RELATIONSHIP = re.compile(
    r"""relationship\s*\(""",
)
```

**Conditional:** Only runs if ORM entity/model files detected. Skips if none found.

### Config: `DatabaseScanConfig`

Add to `src/agent_team/config.py` following the EXACT pattern of `IntegrityScanConfig` (line 325):

```python
@dataclass
class DatabaseScanConfig:
    """Configuration for database integrity static scans.

    Three lightweight static analysis checks that detect cross-layer type
    inconsistencies, missing defaults, and incomplete ORM relationships.
    All produce warnings (non-blocking) and default to enabled since they
    are cheap regex/filesystem scans.
    """

    dual_orm_scan: bool = True        # Detect type mismatches between ORM and raw queries
    default_value_scan: bool = True   # Detect missing defaults and unsafe nullable access
    relationship_scan: bool = True    # Detect incomplete ORM relationship configuration
```

**Add to `AgentTeamConfig`** (after `integrity_scans` field, line ~355):

```python
database_scans: DatabaseScanConfig = field(default_factory=DatabaseScanConfig)
```

**Add to `_dict_to_config()`** (after the `integrity_scans` section, line ~905):

```python
if "database_scans" in data and isinstance(data["database_scans"], dict):
    dsc = data["database_scans"]
    cfg.database_scans = DatabaseScanConfig(
        dual_orm_scan=dsc.get("dual_orm_scan", cfg.database_scans.dual_orm_scan),
        default_value_scan=dsc.get("default_value_scan", cfg.database_scans.default_value_scan),
        relationship_scan=dsc.get("relationship_scan", cfg.database_scans.relationship_scan),
    )
```

**Config YAML section:**

```yaml
database_scans:
  dual_orm_scan: true        # Detect ORM vs raw SQL type mismatches
  default_value_scan: true   # Detect missing defaults and unsafe nullable access
  relationship_scan: true    # Detect incomplete relationship configuration
```

### CLI Wiring for All 3 Scans

**In `src/agent_team/cli.py`, insert AFTER PRD reconciliation (line ~3617) and BEFORE E2E testing (line ~3622):**

Follow the EXACT pattern of the Deployment Integrity Scan block (line 3535). Each scan gets its own
independent try/except block for crash isolation.

```python
    # -------------------------------------------------------------------
    # Post-orchestration: Database Integrity Scans
    # -------------------------------------------------------------------

    # Scan 1: Dual ORM type consistency
    if config.database_scans.dual_orm_scan:
        try:
            from .quality_checks import run_dual_orm_scan

            db_dual_violations = run_dual_orm_scan(Path(cwd))
            if db_dual_violations:
                print_warning(
                    f"Dual ORM scan: {len(db_dual_violations)} "
                    f"type mismatch(es) found."
                )
                recovery_types.append("database_dual_orm_fix")
                try:
                    fix_cost = asyncio.run(
                        _run_integrity_fix(
                            cwd=cwd,
                            config=config,
                            violations=db_dual_violations,
                            scan_type="database_dual_orm",
                            task_text=args.task,
                            constraints=constraints,
                            intervention=intervention,
                            depth=depth if not _use_milestones else "standard",
                        )
                    )
                    if _current_state:
                        _current_state.total_cost += fix_cost
                except Exception as exc:
                    import traceback
                    print_warning(
                        f"Database dual ORM fix recovery failed: {exc}\n"
                        f"{traceback.format_exc()}"
                    )
        except Exception as exc:
            print_warning(f"Dual ORM scan failed: {exc}")

    # Scan 2: Default value & nullability
    if config.database_scans.default_value_scan:
        try:
            from .quality_checks import run_default_value_scan

            db_default_violations = run_default_value_scan(Path(cwd))
            if db_default_violations:
                print_warning(
                    f"Default value scan: {len(db_default_violations)} "
                    f"issue(s) found."
                )
                recovery_types.append("database_default_value_fix")
                try:
                    fix_cost = asyncio.run(
                        _run_integrity_fix(
                            cwd=cwd,
                            config=config,
                            violations=db_default_violations,
                            scan_type="database_defaults",
                            task_text=args.task,
                            constraints=constraints,
                            intervention=intervention,
                            depth=depth if not _use_milestones else "standard",
                        )
                    )
                    if _current_state:
                        _current_state.total_cost += fix_cost
                except Exception as exc:
                    import traceback
                    print_warning(
                        f"Database default value fix recovery failed: {exc}\n"
                        f"{traceback.format_exc()}"
                    )
        except Exception as exc:
            print_warning(f"Default value scan failed: {exc}")

    # Scan 3: ORM relationship completeness
    if config.database_scans.relationship_scan:
        try:
            from .quality_checks import run_relationship_scan

            db_rel_violations = run_relationship_scan(Path(cwd))
            if db_rel_violations:
                print_warning(
                    f"Relationship scan: {len(db_rel_violations)} "
                    f"issue(s) found."
                )
                recovery_types.append("database_relationship_fix")
                try:
                    fix_cost = asyncio.run(
                        _run_integrity_fix(
                            cwd=cwd,
                            config=config,
                            violations=db_rel_violations,
                            scan_type="database_relationships",
                            task_text=args.task,
                            constraints=constraints,
                            intervention=intervention,
                            depth=depth if not _use_milestones else "standard",
                        )
                    )
                    if _current_state:
                        _current_state.total_cost += fix_cost
                except Exception as exc:
                    import traceback
                    print_warning(
                        f"Database relationship fix recovery failed: {exc}\n"
                        f"{traceback.format_exc()}"
                    )
        except Exception as exc:
            print_warning(f"Relationship scan failed: {exc}")
```

### Quality Standards

Add database integrity standards to `src/agent_team/code_quality_standards.py`.

**Option A (Preferred):** Create a new `DATABASE_INTEGRITY_STANDARDS` constant (like `E2E_TESTING_STANDARDS`):

```python
DATABASE_INTEGRITY_STANDARDS = r"""## DATABASE INTEGRITY QUALITY STANDARDS

### Anti-Patterns (NEVER produce these)

**DB-001: Enum Type Mismatch (ORM vs Raw SQL)**
- NEVER compare an enum column as an integer in raw SQL when the ORM stores it as a string (or vice versa).
- The ORM model type and raw query comparison type MUST match exactly.
- FIX: Use the same type representation in both ORM and raw queries. If ORM uses string enum, raw SQL must compare to strings.

**DB-002: Boolean Type Mismatch (ORM vs Raw SQL)**
- NEVER compare a boolean column as 0/1 in raw SQL when the ORM stores it as true/false (or vice versa).
- FIX: Match the database engine's boolean representation consistently. Use parameterized queries.

**DB-003: DateTime Format Mismatch**
- NEVER hardcode date format strings in raw SQL that differ from the ORM's serialization format.
- FIX: Use parameterized queries for dates. Let the ORM/driver handle serialization.

**DB-004: Missing Default Value**
- NEVER leave boolean or enum properties without an explicit default in entity/model definitions.
- Every boolean MUST have `= false` or `= true`. Every enum MUST have a default member.
- FIX: Add explicit defaults to all boolean and enum properties.

**DB-005: Nullable Property Without Null Check**
- NEVER access a nullable property without a null guard.
- `entity.NullableField.Method()` without `?.` or null check = NullReferenceException.
- FIX: Use null-conditional access (`?.`) or explicit null checks before property access.

**DB-006: FK Without Navigation Property**
- NEVER leave a FK column (`TenderId`, `UserId`) without a corresponding navigation property.
- Without navigation, eager loading (`Include()`) silently returns null.
- FIX: Add navigation property matching the FK name (minus the `Id` suffix).

**DB-007: Navigation Property Without Inverse**
- ALWAYS define the inverse navigation when using navigation properties.
- Without inverse, the ORM cannot properly track changes in both directions.
- FIX: Add `ICollection<Child>` on the parent and parent reference on the child.

**DB-008: FK With No Relationship Configuration**
- NEVER rely on convention-only FK detection for complex relationships.
- Without explicit `.HasMany().WithOne()` or `@relation`, the ORM may not generate correct cascade behavior.
- FIX: Add explicit relationship configuration in entity configuration classes.

### Quality Rules

**Seed Data Completeness:**
- ALL seeded records MUST satisfy the application's standard query filters.
- If the user listing filters on `isActive=true`, seeded users MUST have `isActive=true`.
- Every role defined in the system MUST have at least one seeded account.

**Enum/Status Registry:**
- Every entity with a status/enum field MUST have a complete registry of valid values.
- The DB representation, API representation, and frontend representation MUST be documented.
- State transitions MUST be explicitly defined (which transitions are valid, which are not).
"""
```

**Add to `_AGENT_STANDARDS_MAP`:**

```python
_AGENT_STANDARDS_MAP: dict[str, list[str]] = {
    "code-writer": [FRONTEND_STANDARDS, BACKEND_STANDARDS, DATABASE_INTEGRITY_STANDARDS],
    "code-reviewer": [CODE_REVIEW_STANDARDS, DATABASE_INTEGRITY_STANDARDS],
    "test-runner": [TESTING_STANDARDS, E2E_TESTING_STANDARDS],
    "debugger": [DEBUGGING_STANDARDS],
    "architect": [ARCHITECTURE_QUALITY_STANDARDS, DATABASE_INTEGRITY_STANDARDS],
}
```

---

## PHASE 2B: IMPLEMENT PROMPT INJECTIONS (impl-prompts)

Read ARCHITECTURE_REPORT.md first. Follow every prompt pattern EXACTLY as documented.

### Prompt 1: Seed Data Completeness Policy

**Inject into: `CODE_WRITER_PROMPT`** (in `agents.py`, line 948)

Insert AFTER UI COMPLIANCE POLICY (line ~1042), BEFORE Validation Middleware (line ~1043).
Follow the EXACT format of ZERO MOCK DATA POLICY (bold name, severity parenthetical, indented
bullets, terminal severity statement):

```
- **SEED DATA COMPLETENESS POLICY** (ABSOLUTE — NO EXCEPTIONS):
  When designing or implementing seed data (database seeding, initial data migration, dev fixtures):

  EVERY seeded record MUST be COMPLETE and QUERYABLE:
  - SEED-001: Incomplete seed record — every field must be explicitly set, not relying on defaults.
    If a user record has `isActive`, `emailVerified`, `role`, `createdAt` fields, ALL must be set.
  - SEED-002: Seed record not queryable by standard API filters — if the user listing endpoint
    filters on `isActive=true AND emailVerified=true`, then seeded users MUST have BOTH set to true.
    A seeded record invisible to the app's own queries = BROKEN SEED DATA.
  - SEED-003: Role without seed account — every role defined in the authorization system MUST have
    at least one seeded user account. Admin, User, Reviewer, etc. — ALL need seed accounts.

  SEED DATA RULES:
  1. Define seed data in a dedicated section/file (e.g., SeedData.cs, seed.ts, fixtures.py)
  2. Every field for every seeded record MUST be explicitly set — do NOT rely on database defaults
  3. Cross-check seeded values against ALL query filters in the API layer
  4. Include ALL roles, ALL statuses, ALL enum values that the app expects to find
  5. Seed data is TEST DATA for development — it must exercise the app's actual query paths

  VIOLATION = AUTOMATIC REVIEW FAILURE.
```

**Inject into: `CODE_REVIEWER_PROMPT`** (in `agents.py`, line 1084)

Insert AFTER UI Compliance Verification (line ~1169), BEFORE Orphan Detection (line ~1170).
Follow the reviewer verification section format:

```
## Seed Data Verification (MANDATORY when seed/fixture files exist)
For every seed data file or migration that inserts initial records:
1. Verify EVERY field is explicitly set (SEED-001) — no reliance on implicit defaults
2. Cross-reference seeded values against API query filters:
   - Find ALL endpoints that filter on boolean flags (isActive, emailVerified, isApproved)
   - Verify seeded records have values that PASS those filters (SEED-002)
3. Verify every role in the authorization system has a seed account (SEED-003):
   - Find role definitions (enums, constants, config)
   - Verify seed data includes at least one account per role
If violations found: Review Log entry with "SEED-NNN", FAIL verdict, list specific fields/roles missing.
```

### Prompt 2: Enum/Status Registry Requirement

**Inject into: `ARCHITECT_PROMPT`** (in `agents.py`, line 836)

Insert AFTER the Service-to-API Wiring Plan section (line ~935), BEFORE the Milestone Handoff
Preparation section (which NOW EXISTS — added by Tracking Documents implementation). Follow the architect section format:

```
## Status/Enum Registry (MANDATORY for projects with status or enum fields)
You MUST produce a STATUS_REGISTRY section in your architecture document that defines:

1. **Entity Inventory:** Every entity that has a status, state, type, or enum field
2. **Complete Value List:** Every possible value for each enum — the COMPLETE list, not "Draft, Published, etc."
3. **State Transitions:** Every valid state transition:
   - Draft -> Published: YES (via publish action)
   - Published -> Draft: NO (cannot unpublish)
   - Format: `FROM -> TO: YES/NO (trigger/reason)`
4. **Cross-Layer Representation:**
   - Database type: string enum, integer, varchar(50), etc.
   - Backend API: exact string values in request/response JSON
   - Frontend: exact string values used in UI state and API calls
   ALL THREE MUST MATCH. If the DB stores "Opened" but the frontend sends "Open" = BUG.
5. **Validation Rules:** Backend MUST validate incoming status strings against the enum.
   A status value not in the registry MUST be rejected with 400 Bad Request.

VIOLATION IDs:
- ENUM-001: Entity with status/enum field but no registry entry → HARD FAILURE
- ENUM-002: Frontend status string doesn't match backend enum value → HARD FAILURE
- ENUM-003: State transition not defined in registry → HARD FAILURE

Every architect MUST produce this registry. Every code-writer MUST consult it.
Every code-reviewer MUST verify code matches it.
```

**Inject into: `CODE_WRITER_PROMPT`** (in `agents.py`, line 948)

Insert AFTER the Seed Data Completeness Policy (just added above):

```
- **ENUM/STATUS REGISTRY COMPLIANCE** (ABSOLUTE — NO EXCEPTIONS):
  When working with entities that have status/type/enum fields:
  1. Read the STATUS_REGISTRY from the architecture document FIRST
  2. Use the EXACT string values defined in the registry — do NOT invent new status strings
  3. Frontend status strings MUST match backend enum values EXACTLY (case-sensitive)
  4. Backend MUST validate incoming status strings against the enum — reject unknown values
  5. Raw SQL queries MUST use the same type representation as the ORM (string vs integer)
  If no STATUS_REGISTRY exists, CREATE one before writing status-dependent code.
  ENUM-001: Missing registry → REVIEW FAILURE.
  ENUM-002: Mismatched status string → REVIEW FAILURE.
  ENUM-003: Undefined state transition → REVIEW FAILURE.
```

**Inject into: `CODE_REVIEWER_PROMPT`** (in `agents.py`, line 1084)

Insert AFTER the Seed Data Verification section (just added above):

```
## Enum/Status Registry Verification (MANDATORY when status/enum fields exist)
For every entity with a status, state, type, or enum field:
1. Verify a STATUS_REGISTRY exists in the architecture document (ENUM-001)
2. Cross-check every frontend service method that sends a status string:
   - The string MUST match the backend enum value exactly (ENUM-002)
3. Cross-check every backend controller that accepts a status parameter:
   - It MUST validate against the defined enum values (ENUM-002)
4. Cross-check every raw SQL query that references a status column:
   - The comparison type (string vs integer) MUST match the ORM definition (DB-001 overlap)
5. Verify all state transitions in the code match the registry's allowed transitions (ENUM-003):
   - Find all places where status is updated
   - Verify the FROM→TO transition is marked YES in the registry
If violations found: Review Log entry with "ENUM-NNN", FAIL verdict, list specific mismatches.
```

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2A and 2B are complete, write tests covering ALL of the following.

### Scan Function Tests (`tests/test_database_scans.py`)

#### Dual ORM Scan Tests

**Positive detection tests (DB-001, DB-002, DB-003):**
- C# project with EF Core enum + Dapper integer comparison → DB-001 violation
- TypeScript project with Prisma boolean + raw SQL `= 0` → DB-002 violation
- Python project with SQLAlchemy datetime + raw SQL format string → DB-003 violation
- C# project with BOTH EF Core AND Dapper packages → dual ORM correctly detected
- Project with raw SQL `WHERE status = 2` and ORM `public Status Status { get; set; }` → DB-001

**Negative tests (no false positives):**
- Single ORM project (EF Core only, no Dapper) → scan skips with message, zero violations
- Single ORM project (Prisma only, no raw SQL) → scan skips, zero violations
- Project with ORM using parameterized queries (no type comparison in SQL strings) → zero violations
- Raw SQL that correctly uses string comparison matching ORM enum → zero violations

**Edge cases:**
- Empty project (no source files) → scan returns empty list
- Project with only frontend (no database files) → scan skips gracefully
- SQL strings that are comments or documentation (not actual queries) → should NOT be flagged
- Multiple ORM contexts in same project → all contexts scanned
- Enum defined in separate file from entity → cross-file resolution works

#### Default Value Scan Tests

**Positive detection tests (DB-004, DB-005):**
- C# `public bool IsActive { get; set; }` without `= false;` → DB-004 violation
- C# `public Status Status { get; set; }` without `= Status.Draft;` → DB-004 violation
- Prisma `isActive Boolean` without `@default(false)` → DB-004 violation
- Django `BooleanField()` without `default=` → DB-004 violation
- C# `string? Description` accessed as `.Description.Length` without null check → DB-005 violation
- TypeScript nullable accessed without optional chaining → DB-005 violation

**Negative tests (no false positives):**
- `public bool IsActive { get; set; } = false;` → no DB-004 (has default)
- Prisma `isActive Boolean @default(false)` → no DB-004
- Nullable property accessed with `?.` → no DB-005
- Nullable property with explicit null check before access → no DB-005
- Non-entity class with boolean property (DTO, ViewModel) → should NOT be flagged

**Edge cases:**
- No entity files in project → scan skips, zero violations
- Entity with no boolean or enum properties → scan runs but finds nothing
- Property with default set via constructor (not field initializer) → implementation decides
- Abstract base class with boolean properties → should be scanned

#### Relationship Scan Tests

**Positive detection tests (DB-006, DB-007, DB-008):**
- C# entity with `public int TenderId { get; set; }` but no `public Tender Tender { get; set; }` → DB-006
- C# entity with navigation property but related entity missing inverse collection → DB-007
- C# entity with FK column AND no navigation AND no `HasMany/WithOne` config → DB-008
- TypeORM entity with `@JoinColumn()` but no `@ManyToOne()` → DB-006

**Negative tests (no false positives):**
- Properly configured relationship (FK + nav + inverse + config) → zero violations
- Primary key `Id` property → NOT flagged as FK
- Property ending in `Id` but not a FK (e.g., `ExternalId` that's a string identifier) → should NOT be flagged
  (or implementation must handle — document decision)
- Non-entity file with properties ending in `Id` → NOT flagged

**Edge cases:**
- No ORM entities in project → scan skips, zero violations
- Self-referential FK (`ParentCategoryId` on Category) → should detect missing nav
- Multiple FK columns to same related entity → each independently checked
- Composite keys → skipped (document why)
- Entity using only Fluent API configuration (no data annotations) → configuration still detected

### Conditional Skip Tests

- Single ORM project → dual ORM scan prints skip message and returns empty
- No entity files → default value scan returns empty
- No ORM detected → relationship scan returns empty
- `config.database_scans.dual_orm_scan = False` → dual ORM scan not called
- `config.database_scans.default_value_scan = False` → default value scan not called
- `config.database_scans.relationship_scan = False` → relationship scan not called

### Prompt Injection Tests

**Verify prompt content:**
- `CODE_WRITER_PROMPT` contains "SEED DATA COMPLETENESS POLICY"
- `CODE_WRITER_PROMPT` contains "SEED-001", "SEED-002", "SEED-003"
- `CODE_WRITER_PROMPT` contains "ENUM/STATUS REGISTRY COMPLIANCE"
- `CODE_WRITER_PROMPT` contains "ENUM-001", "ENUM-002", "ENUM-003"
- `CODE_REVIEWER_PROMPT` contains "Seed Data Verification"
- `CODE_REVIEWER_PROMPT` contains "SEED-001", "SEED-002", "SEED-003"
- `CODE_REVIEWER_PROMPT` contains "Enum/Status Registry Verification"
- `CODE_REVIEWER_PROMPT` contains "ENUM-001", "ENUM-002", "ENUM-003"
- `ARCHITECT_PROMPT` contains "Status/Enum Registry"
- `ARCHITECT_PROMPT` contains "ENUM-001", "ENUM-002", "ENUM-003"
- Both CODE_WRITER policies use "AUTOMATIC REVIEW FAILURE" or "REVIEW FAILURE" severity language
- Both CODE_REVIEWER sections include "FAIL verdict" language

**Verify prompt integration:**
- All existing policies still present (ZERO MOCK DATA, UI COMPLIANCE)
- New policies don't break existing prompt structure
- New policies appear AFTER existing policies (correct ordering)
- No duplicate section headers
- Prompt is valid (no unclosed quotes, no syntax errors in the raw string)

### Config Tests

- `DatabaseScanConfig` has correct defaults: all 3 booleans `True`
- `DatabaseScanConfig` loads from YAML correctly:
  ```python
  cfg = _dict_to_config({"database_scans": {"dual_orm_scan": False}})
  assert cfg.database_scans.dual_orm_scan is False
  assert cfg.database_scans.default_value_scan is True  # default preserved
  ```
- Unknown YAML keys in `database_scans` don't break parsing
- Missing `database_scans` section → all defaults applied
- `AgentTeamConfig()` includes `database_scans` field with correct type
- Partial YAML (only some fields) → defaults for missing fields

### CLI Wiring Tests

- Database scans appear in correct position: after PRD reconciliation, before E2E testing
- Each scan independently gated by its config flag
- Each scan wrapped in its own try/except (crash isolation)
- Dual ORM scan failure doesn't prevent default value scan from running
- Default value scan failure doesn't prevent relationship scan from running
- All 3 scans failing doesn't prevent E2E phase from running
- Violations add correct recovery type strings:
  `"database_dual_orm_fix"`, `"database_default_value_fix"`, `"database_relationship_fix"`
- Recovery types appear in recovery report
- `_run_integrity_fix()` called with correct `scan_type` parameter for each scan
- `_current_state.total_cost` updated after fix passes

### Quality Standards Tests

- `DATABASE_INTEGRITY_STANDARDS` constant exists and is non-empty
- `DATABASE_INTEGRITY_STANDARDS` contains all 8 pattern IDs: DB-001 through DB-008
- `get_standards_for_agent("code-writer")` includes `DATABASE_INTEGRITY_STANDARDS`
- `get_standards_for_agent("code-reviewer")` includes `DATABASE_INTEGRITY_STANDARDS`
- `get_standards_for_agent("architect")` includes `DATABASE_INTEGRITY_STANDARDS`
- `get_standards_for_agent("test-runner")` does NOT include `DATABASE_INTEGRITY_STANDARDS`
- Standards contain "Seed Data Completeness" and "Enum/Status Registry" quality rules

### Cross-Feature Integration Tests

- DB-001 through DB-008 pattern IDs don't collide with ANY existing pattern IDs
  (MOCK-001..007, UI-001..004, E2E-001..007, DEPLOY-001..004, ASSET-001..003, PRD-001,
  FRONT-007/010/016, BACK-001/002/016/017/018, SLOP-001/003)
- SEED-001..003 and ENUM-001..003 don't collide with existing prompt pattern IDs
- All 3 new scan functions are importable from `quality_checks`
- New `DatabaseScanConfig` doesn't break existing config loading
- All new imports resolve correctly
- Existing tests still pass — zero regressions

### Regression Tests

- Run the FULL existing test suite → verify zero new failures
- Existing scan functions (`run_mock_data_scan`, `run_ui_compliance_scan`, etc.) still work
- Existing prompt content unchanged (ZERO MOCK DATA policy text identical)
- Existing config fields unchanged (IntegrityScanConfig still has 3 fields)
- `_dict_to_config()` still parses all existing sections correctly

---

## PHASE 4: WIRING VERIFICATION (wiring-verifier)

Read cli.py and trace execution flow. Write verification tests in `tests/test_database_wiring.py`.

### 4A: Scan Execution Position

- Database scans run AFTER existing integrity scans (deployment scan at line ~3535, asset scan
  at line ~3564, PRD reconciliation at line ~3593) and BEFORE the E2E testing phase (line ~3622).
- Document the exact order by reading the actual source — don't trust line numbers in this prompt.
- The 3 database scans run in sequence: dual ORM → defaults → relationships.
- Verify no scan depends on another scan's output (they're independent).

### 4B: Config Gating

- `config.database_scans.dual_orm_scan = False` → `run_dual_orm_scan()` is NOT called
  (not called-and-returned-early — actually not invoked at all)
- `config.database_scans.default_value_scan = False` → `run_default_value_scan()` NOT called
- `config.database_scans.relationship_scan = False` → `run_relationship_scan()` NOT called
- All 3 flags can be independently set without affecting each other
- Missing `database_scans` config section → all 3 scans run (defaults are True)

### 4C: Crash Isolation

- Each scan is wrapped in its own try/except
- If `run_dual_orm_scan()` raises an exception, `run_default_value_scan()` still runs
- If `run_default_value_scan()` raises, `run_relationship_scan()` still runs
- If ALL 3 database scans crash, the E2E testing phase still runs
- Exception messages include traceback information (not silently swallowed)
- The outer try/except catches the scan function itself
- The inner try/except catches the fix function (`_run_integrity_fix`)

### 4D: Recovery Integration

- When `run_dual_orm_scan()` finds violations, `"database_dual_orm_fix"` is appended to `recovery_types`
- When `run_default_value_scan()` finds violations, `"database_default_value_fix"` appended
- When `run_relationship_scan()` finds violations, `"database_relationship_fix"` appended
- Recovery report at the end includes all database recovery types
- Each recovery type triggers `_run_integrity_fix()` with the correct `scan_type`

### 4E: State Tracking

- Database scans do NOT need their own `completed_phases` marker (they're part of `"post_orchestration"`)
- `_current_state.total_cost` is updated after each fix pass
- Verify this matches the pattern used by deployment and asset scans

### 4F: Prompt Injection Verification

Read the FINAL prompt strings (after all assembly/concatenation) and verify:
- Seed Data Completeness policy is present in `CODE_WRITER_PROMPT`
- Seed Data Completeness verification is present in `CODE_REVIEWER_PROMPT`
- Enum/Status Registry section is present in `ARCHITECT_PROMPT`
- Enum/Status Registry compliance is present in `CODE_WRITER_PROMPT`
- Enum/Status Registry verification is present in `CODE_REVIEWER_PROMPT`
- No truncation, no duplication, no ordering issues
- Existing policies (ZERO MOCK DATA, UI COMPLIANCE) are STILL present and unmodified

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL existing tests must pass (except 2 pre-existing known failures in `test_mcp_servers.py`)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test
  expectation is provably wrong), and re-run
- Iterate until fully green
- **IMPORTANT:** The Tracking Documents implementation will have been applied before this.
  The test suite will include tracking document tests — those must ALSO still pass.

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# Database Integrity Upgrades — Implementation Report

## Implementation Summary
- Scan functions added: 3 (run_dual_orm_scan, run_default_value_scan, run_relationship_scan)
- Pattern IDs added: DB-001 through DB-008
- Prompt policies added: 2 (Seed Data Completeness, Enum/Status Registry)
- Prompt pattern IDs added: SEED-001..003, ENUM-001..003
- Quality standards added: DATABASE_INTEGRITY_STANDARDS constant
- Config: DatabaseScanConfig (3 boolean fields)
- CLI wiring points: 3 (one per scan, in post-orchestration section)

## Scan Coverage Matrix
| Pattern ID | What It Catches | Severity | Conditional On |
|------------|----------------|----------|----------------|
| DB-001 | Enum type mismatch (ORM vs raw SQL) | HIGH | 2+ data access methods |
| DB-002 | Boolean type mismatch (ORM vs raw SQL) | HIGH | 2+ data access methods |
| DB-003 | DateTime format mismatch (ORM vs raw SQL) | HIGH | 2+ data access methods |
| DB-004 | Boolean/enum without explicit default | MEDIUM | Entity files exist |
| DB-005 | Nullable property used without null check | HIGH | Entity files exist |
| DB-006 | FK without navigation property | MEDIUM | ORM entities exist |
| DB-007 | Navigation without inverse relationship | LOW | ORM entities exist |
| DB-008 | FK with no relationship config at all | HIGH | ORM entities exist |

## Prompt Policy Coverage
| Policy | Injected Into | Pattern IDs | Prevents |
|--------|--------------|-------------|----------|
| Seed Data Completeness | Writer + Reviewer | SEED-001..003 | Invisible users, broken fresh deployments |
| Enum/Status Registry | Architect + Writer + Reviewer | ENUM-001..003 | Status string mismatches, disappeared records |

## Test Results
- New tests written: {X}
- All passing: {X}/{X}
- Regressions: 0

## Wiring Verification
- Scan position: VERIFIED / ISSUES
- Config gating: VERIFIED / ISSUES
- Crash isolation: VERIFIED / ISSUES
- Recovery integration: VERIFIED / ISSUES
- State tracking: VERIFIED / ISSUES
- Prompt injection: VERIFIED / ISSUES

## Bayan Pattern Coverage (Final Check)
| Bayan Failure | Fixed By | Scan/Prompt | Status |
|--------------|----------|-------------|--------|
| Dual ORM type mismatch | DB-001, DB-002, DB-003 | Dual ORM Scan | VERIFIED |
| Seed data incompleteness | SEED-001, SEED-002, SEED-003 | Seed Data Policy | VERIFIED |
| Missing default values | DB-004, DB-005 | Default Value Scan | VERIFIED |
| Status string mismatches | ENUM-001, ENUM-002, ENUM-003 | Enum Registry Policy | VERIFIED |
| Relationship wiring gaps | DB-006, DB-007, DB-008 | Relationship Scan | VERIFIED |

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — scanner-architect MUST finish before anyone implements anything.
   The ARCHITECTURE_REPORT.md is the single source of truth for integration points, patterns, and
   insertion locations.

2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must
   follow the exact patterns already in the codebase. If existing scans use `_iter_source_files()`,
   use `_iter_source_files()`. If existing prompts use bold headers with severity parentheticals,
   use bold headers with severity parentheticals. Consistency over creativity.

3. **READ BEFORE YOU WRITE** — Read every file before modifying it. The codebase has 3800+ lines
   in cli.py and 1600+ lines in quality_checks.py — understand the context around your insertion point.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test
   expectation is provably wrong.

5. **NO SHORTCUTS** — All 3 scans and 2 prompt injections must be fully implemented with detection
   logic, config gating, CLI wiring, quality standards, and exhaustive tests.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase.
   Line numbers are approximate and WILL have shifted due to the Tracking Documents implementation.

7. **CONDITIONAL SCANS** — Every scan must skip gracefully when its preconditions aren't met.
   No crashes on projects without databases. No crashes on projects with a single ORM.
   No crashes on projects without entity files. Print an info-level message and return empty.

8. **CRASH ISOLATION** — Each scan independently wrapped in its own try/except. One scan failure
   cannot cascade to block another scan or the E2E phase.

9. **BACKWARD COMPATIBLE** — A project with no `database_scans` config section must work exactly
   as before. Defaults are all-enabled, but failure to detect database patterns silently degrades
   to no violations (not a crash).

10. **BEST-EFFORT EXTRACTION** — The regex-based detection of ORM models, FK columns, raw SQL
    patterns, and entity definitions will not be perfect. That's OK. These scans catch the OBVIOUS
    cases (which are the most common failures). A scan that catches 80% of the Bayan-style bugs
    is vastly better than no scan.

11. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden
    these scans beyond what this prompt describes (additional patterns, edge cases, integration
    improvements), DO IT. Document what you added and why in the final report.

12. **TRACKING DOCUMENTS AWARENESS** — This implementation runs AFTER the Tracking Documents
    implementation is complete. The codebase will contain `tracking_documents.py`,
    `TrackingDocumentsConfig`, and additional wiring in cli.py. Do NOT break or modify any
    tracking document code. Verify all tracking document tests still pass.
