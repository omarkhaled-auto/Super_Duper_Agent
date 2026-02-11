# Agent-Team v11.0 — E2E Gap Closure

## Agent Team Structure — 3-Agent Pipeline

You MUST execute this implementation using a coordinated agent team. The architecture-first pattern is non-negotiable: discovery prevents guessing.

### Team Composition (3 agents)

| Agent Name | Type | Role | File Access |
|------------|------|------|-------------|
| `gap-architect` | `Explore` | Phase 1 — Read the entire codebase. Map every existing scan pattern, prompt injection point, config wiring path, CLI pipeline position, and violation reporting flow. Produce ARCHITECTURE_REPORT.md. | **READ ONLY** — no source edits |
| `implementer` | `general-purpose` | Phase 2 — All code changes: 3 new scans, API-002 enhancement, 4 prompt injections, config field, CLI wiring, display label, quality standards constant, fix function. | quality_checks.py, agents.py, e2e_testing.py, code_quality_standards.py, config.py, cli.py, display.py |
| `test-engineer` | `general-purpose` | Phase 3 — Write ALL tests, run pytest, diagnose and fix failures, verify wiring, iterate until green. | Test files + source files (for bug fixes found during testing) |

### Coordination Flow

```
Wave 1 (solo): gap-architect reads entire codebase
    │
    Produces: ARCHITECTURE_REPORT.md
    │
Wave 2 (solo): implementer reads ARCHITECTURE_REPORT.md, implements ALL changes
    │           (scans → prompts → config → cli wiring → display → standards)
    │
Wave 3 (solo): test-engineer writes tests, runs full suite, fixes failures
    │           Also performs wiring verification as part of testing
    │
Wave 4: You (team lead) collect all results → produce final report
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **gap-architect runs first and alone.** It must finish before the implementer starts. Its architecture report is the single source of truth.
- **implementer runs second.** It reads the architecture report, then implements ALL changes across all 7 files. Single agent avoids file ownership conflicts.
- **test-engineer runs last.** It writes tests, runs them, verifies wiring, and iterates until green. It may edit source files to fix bugs discovered during testing.
- **Shut down all agents** after Wave 3 completes. Collect results and write the final report yourself.

### Critical Rules for Agents

- **gap-architect**: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- **implementer**: Can edit the 7 files listed above. No test files. No other source files.
- **test-engineer**: Can create/edit test files AND source files (to fix bugs found during testing).
- If any agent finds a conflict or architectural issue, send it to the team lead immediately.

---

# E2E Gap Closure — From 27% to 60% Bug Prevention

## Background — Why This Exists

We ran a comprehensive manual E2E test on Bayan (the agent-team's flagship output — 104K LOC enterprise procurement system). Found 30 bugs during the full tender lifecycle walkthrough. Analyzed each bug against the current 42-checkpoint system. Results:

- **8/30 (27%) now caught** by existing v10.2 checkpoints
- **5/30 partially caught**
- **17/30 not caught at all**

Of those 17, analysis identified **3 systematic patterns** that represent addressable gaps in the agent-team's scan and prompt system. Fixing these 3 patterns would catch an additional 7-10 bugs, raising prevention from 27% to ~50-60%.

The remaining bugs (business logic, UX flow, runtime data path) are genuinely beyond static analysis — only full browser testing and comprehensive E2E cover them.

### Pattern A: ASP.NET Enum Integer Serialization (3 bugs)

**What happened:** ASP.NET serializes C# enums as integers by default (`Status = 0` instead of `"submitted"`). Frontend JavaScript does string comparisons (`status === 'submitted'`). Every DTO with an enum field was broken.

**Bug examples:**
- Fix 8: Clarification status showed "0" instead of "Submitted" — backend sent integer, frontend expected string
- Fix 11: Admin clarification service had no enum normalization — same pattern, different component
- Fix 29: `startApproval()` called `.toLowerCase()` on an integer — TypeError crash

**Why existing scans missed it:** Enum Registry (ENUM-001..003) verifies enum *values* exist on both sides. It doesn't check the *wire format* — whether the backend sends integers or strings. API Contract Scan checks field *names*, not field *types or serialization behavior*.

### Pattern B: Silent Data Loss (3 bugs — 1 CRITICAL)

**What happened:** Operations appeared to succeed — no error, no crash, no warning — but data was missing, truncated, or not persisted.

**Bug examples:**
- Fix 22 (CRITICAL): CQRS `MatchBidItemsCommandHandler` returned valid DTOs but NEVER called `SaveChangesAsync()`. BidPricing table stayed empty. All downstream handlers read from an empty table. The 5-step import wizard appeared to work but produced zero data.
- Fix 23: Frontend used `switchMap(() =>` instead of `switchMap((mapResult) =>`, ignoring the API response entirely. Only 10 of 48 items were passed to the next step.
- Fix 20: `if (!this.bidDocument) return;` — a null guard silently aborted execution. No error, no log, no user feedback. Button click did nothing.

**Why existing scans missed it:** All scans are structural (file patterns, field names, config values). None trace data flow — whether a handler persists, whether a frontend uses a response, whether a guard produces feedback.

### Pattern C: DTO Field Presence Mismatch — Bidirectional (3 bugs)

**What happened:** Frontend interfaces declared fields that didn't exist in the backend DTO at all. Not a name mismatch — a field *presence* mismatch.

**Bug examples:**
- Fix 14: Frontend accessed `bulletin.clarifications` (array) but backend DTO only had `clarificationCount` (integer). Result: `Cannot read properties of undefined (reading 'length')`.
- Fix 15: Frontend expected `companyName` on BidReceiptDto. Backend DTO didn't have it. Empty string rendered.
- Fix 18: Frontend expected `hasSubmittedBid` on tender access DTO. Backend didn't include it. Status display wrong.

**Why existing scans missed it:** API-002 checks if backend DTO field names appear in the frontend. It does NOT check the reverse — whether frontend interface fields exist in the backend response. The check was one-directional.

## What We're Building

Optimized for **maximum bug prevention with minimum false-positive risk**. The key insight: **prompts prevent bugs during build (earlier = better); scans catch bugs post-build (safety net)**. We invest heavily in prompts, keep scans simple and precise.

**Category 1: Scans (2 new + 1 enhanced in quality_checks.py)**
- ENUM-004: Global enum serialization converter check (.NET — simplified to ~30 lines)
- SDL-001: CQRS handler missing persistence call (file-level keyword check — ~50 lines)
- API-002 bidirectional: Check frontend→backend field presence (reverse of existing check)

**Category 2: Prompt-Only Coverage (no scan — AI reviewer handles it)**
- SDL-002 (frontend ignoring response): Covered by CODE_REVIEWER_PROMPT injection — regex can't distinguish intentional fire-and-forget from data-loss bugs; the AI reviewer can.
- SDL-003 (silent guard without feedback): Covered by CODE_REVIEWER_PROMPT injection — requires multi-line context (method name + guard + nearby feedback check) beyond regex capability.

**Category 3: Prompt Injections (4 blocks across 3 files)**
- Architect: .NET serialization boilerplate (PREVENTION — stops enum bugs at source)
- Code reviewer: Enum serialization vigilance (DETECTION during review)
- Code reviewer: Silent data loss detection — SDL-001/002/003 (DETECTION during review)
- E2E test standards: Mutation verification requirement (VERIFICATION during testing)

**Why SDL-002/003 are prompt-only (no scan):**
- SDL-002 requires **data flow analysis** to determine if the next operation uses the ignored response — this is fundamentally beyond line-level regex. The original plan acknowledged ">20% false positive risk" and suggested prompt-only fallback. We start there.
- SDL-003 requires **multi-line context** — determining if code is inside a click handler and whether feedback exists nearby. All existing scans are line-level or whole-file. The AI reviewer naturally understands method context.
- Both bugs are still caught at the same prevention rate — just during code review instead of post-build scan. **Earlier detection is actually better.**

---

## PHASE 1: ARCHITECTURE DISCOVERY (gap-architect)

Before implementing ANYTHING, the gap-architect must read the codebase and produce ARCHITECTURE_REPORT.md. The report must be FOCUSED — answer exactly what the implementer needs, not document everything.

### 1A: Scan Implementation Pattern in quality_checks.py

- Read quality_checks.py end to end
- Document the EXACT pattern for writing a new scan function:
  - Function signature: `def run_xxx_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:`
  - Violation constructor: `Violation(check="XXX-001", message="...", file_path="...", line=0, severity="error")`
  - File walking: which helpers exist? (`_iter_source_files`, `_find_files_by_pattern`, `Path.rglob`)
  - Scope filtering pattern: how `scope.changed_files` is applied
  - Cap: `_MAX_VIOLATIONS = 100`
  - Sort: by `_SEVERITY_ORDER` then file_path then line
- Document how `run_api_contract_scan` works — specifically:
  - `_parse_svc_table()` → SvcContract dataclass → response_fields dict
  - `_check_frontend_fields()` → finds frontend type files, extracts identifiers, checks against SVC fields
  - `_check_backend_fields()` → same for backend with PascalCase conversion
  - WHERE the one-directional gap is (schema→code only, no code→schema reverse check)
  - The `_extract_identifiers_from_file()` helper and `_to_pascal_case()`
- Document `detect_app_type()` in e2e_testing.py — how it detects .NET, Python, Angular, etc.

### 1B: Prompt Injection Points

- Read agents.py — focus on these 3 prompts:
  - **ARCHITECT_PROMPT**: Find the "Service-to-API Wiring Plan" section (~line 921-952) and the "Status/Enum Registry" section (~line 955-978). The .NET boilerplate block goes ADJACENT to the enum registry.
  - **CODE_REVIEWER_PROMPT**: Find the "API Contract Field Verification" section (~line 1261-1279) and the "Enum/Status Registry" verification section (~line 1308-1320). New blocks go AFTER the enum section.
  - **E2E test prompts**: These are in **e2e_testing.py** (NOT agents.py): `BACKEND_E2E_PROMPT` and `FRONTEND_E2E_PROMPT`. Find where test-writing instructions are and where the mutation verification block fits.
- Document the EXACT formatting convention: section headers (`###`), severity language, pattern ID references
- Note: prompts are **static strings** — there is NO conditional injection infrastructure. Technology-specific prompts use "For .NET backends:" prefixes that the AI applies contextually.

### 1C: Config + CLI Wiring

- Read config.py:
  - Document `PostOrchestrationScanConfig` fields and how new fields are added
  - Document `_dict_to_config()` — specifically how `post_orchestration_scans` is parsed (~line 1164-1181) and how `user_overrides` is tracked
  - Document `apply_depth_quality_gating()` — specifically the `quick` block where scans are disabled (~line 512-538)
- Read cli.py post-orchestration pipeline:
  - Document the EXACT order: mock data → UI compliance → integrity → database → API contract → (NEW: SDL goes here) → E2E → browser
  - Document the scan block template (config gate → try/except → fix loop → recovery_types.append → fix function → cost tracking)
  - Document `_run_api_contract_fix()` as a template for `_run_silent_data_loss_fix()`
- Read display.py:
  - Document `type_hints` dict (~line 623-642) — new recovery type needs a display label here
- Read code_quality_standards.py:
  - Document `_AGENT_STANDARDS_MAP` (~line 614-620) — new standards constant needs mapping here
  - Document how `get_standards_for_agent()` works

### Output

ARCHITECTURE_REPORT.md answering ALL questions above. Include exact line numbers. This is the implementer's blueprint.

---

## PHASE 2: IMPLEMENTATION (implementer)

Read ARCHITECTURE_REPORT.md first. Follow every existing pattern EXACTLY as documented.

### CRITICAL DESIGN PRINCIPLES

1. **PRECISION OVER RECALL** — false positives destroy trust. When in doubt, DON'T flag.
2. **SIMPLICITY** — these scans must be regex/keyword-level. No AST parsing, no data flow analysis.
3. **FOLLOW PATTERNS** — every function, config field, and prompt section must look like it was always there.

### 2.1: ENUM-004 — Global Enum Serialization Check

**File:** quality_checks.py

**What it detects:** .NET projects that don't configure `JsonStringEnumConverter` globally, causing all enums to serialize as integers.

**Simplified approach (~30 lines):**

```python
def _check_enum_serialization(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """ENUM-004: Check .NET projects for global JsonStringEnumConverter.

    ASP.NET serializes enums as integers by default. Without a global
    JsonStringEnumConverter, every enum field sent to the frontend will
    be an integer while the frontend expects a string.
    """
    # 1. Detect .NET — check for .csproj files
    csproj_files = list(project_root.rglob("*.csproj"))
    if not csproj_files:
        return []  # Not a .NET project — skip entirely

    # 2. Check for global JsonStringEnumConverter in startup files
    for startup_name in ("Program.cs", "Startup.cs"):
        for startup_file in project_root.rglob(startup_name):
            try:
                content = startup_file.read_text(errors="ignore")
                if "JsonStringEnumConverter" in content:
                    return []  # Globally configured — all enums serialize as strings
            except OSError:
                continue

    # 3. No global converter found — flag it
    return [Violation(
        check="ENUM-004",
        message=(
            "No global JsonStringEnumConverter configured. All C# enums will serialize "
            "as integers (0, 1, 2) but frontend code expects strings ('submitted', 'approved'). "
            "Add to Program.cs: builder.Services.AddControllers().AddJsonOptions(o => "
            "o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));"
        ),
        file_path="Program.cs",
        line=0,
        severity="error",
    )]
```

**Why this simplified approach catches ALL 3 Bayan enum bugs:** Every Bayan bug (Fix 8, 11, 29) was caused by the missing global converter. The per-property check from the original plan adds ~170 lines of C# type-resolution complexity for zero additional coverage on agent-generated code.

**Pattern ID:** ENUM-004
**Severity:** error (HIGH — causes silent display failures and TypeError crashes)
**Conditional:** .NET projects only. Returns `[]` for everything else.
**False positive rate:** ZERO — the global converter either exists or it doesn't.

**Integration:** Call inside `run_api_contract_scan()` as a final pass — ENUM-004 is semantically an API contract issue (the wire format of enum fields). Append violations to the same list. No new config field needed; gates on existing `api_contract_scan`.

### 2.2: SDL-001 — CQRS Command Handler Missing Persistence

**File:** quality_checks.py

**What it detects:** Command handler files that contain zero persistence calls. These handlers "succeed" but never save data.

**File-level keyword approach (~50 lines):**

```python
def _check_cqrs_persistence(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """SDL-001: CQRS command handlers missing persistence calls.

    Checks if command handler files contain at least one persistence keyword.
    File-level check (not method-body parsing) for simplicity and reliability.
    """
    violations: list[Violation] = []

    # Persistence keywords — if a command handler contains NONE of these, flag it
    _PERSISTENCE_KEYWORDS = (
        "SaveChangesAsync", "SaveChanges", "CommitAsync", "Commit(",
        "_repository.Add", "_repository.Update", "_repository.Delete",
        "_repository.Remove", "_repository.Insert",
        "_context.Add", "_context.Update", "_dbContext.Add", "_dbContext.Update",
        "_unitOfWork.Complete", "_unitOfWork.SaveChanges", "_unitOfWork.Commit",
        "session.flush", "db.commit", "await session.commit",
        "db.session.add", "db.session.commit",
    )

    # Skip keywords — handlers that only dispatch events legitimately don't persist
    _SKIP_KEYWORDS = (
        "INotificationHandler", "_mediator.Publish", "_eventBus",
        "_messageQueue", "IEventHandler", "EventHandler",
    )

    # Find command handler files (both .NET and Python patterns)
    command_handler_patterns = (
        r"CommandHandler", r"command_handler",
    )

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for fname in files:
            # Match command handler files, exclude query handlers
            if not any(p.lower() in fname.lower() for p in ("commandhandler", "command_handler")):
                continue
            if any(skip.lower() in fname.lower() for skip in ("queryhandler", "query_handler", "test", "spec")):
                continue

            fpath = Path(root) / fname
            if scope and scope.changed_files:
                if fpath.resolve() not in set(scope.changed_files):
                    continue

            try:
                content = fpath.read_text(errors="ignore")
            except OSError:
                continue

            # Skip event-only handlers
            if any(sk in content for sk in _SKIP_KEYWORDS):
                continue

            # Check for persistence
            if not any(pk in content for pk in _PERSISTENCE_KEYWORDS):
                rel = fpath.relative_to(project_root).as_posix()
                violations.append(Violation(
                    check="SDL-001",
                    message=(
                        f"Command handler '{fname}' contains no persistence call "
                        f"(SaveChangesAsync, SaveChanges, Commit, etc.). "
                        f"Data modifications will be lost. Add a persistence call."
                    ),
                    file_path=rel,
                    line=0,
                    severity="error",
                ))

            if len(violations) >= _MAX_VIOLATIONS:
                break

    return sorted(violations, key=lambda v: (_SEVERITY_ORDER.get(v.severity, 9), v.file_path, v.line))
```

**Pattern ID:** SDL-001
**Severity:** error (CRITICAL — data appears saved but is lost)
**Conditional:** Skips projects with no command handler files. Works for .NET (C#) and Python (SQLAlchemy).
**False positive risk:** LOW — command handlers that delegate to services that persist internally will be flagged. This is an acceptable false positive given the severity (better to over-report than miss Fix 22).

### 2.3: API-002 Enhancement — Bidirectional Field Check

**File:** quality_checks.py — modify existing `run_api_contract_scan()` internals

**What it adds:** A reverse check — for each SVC entry, find the matching frontend TypeScript interface and flag fields that exist in the interface but NOT in the SVC response schema.

**Approach — SVC table as source of truth:**

1. Keep existing `_check_frontend_fields()` and `_check_backend_fields()` UNCHANGED
2. ADD a new function `_check_frontend_extra_fields()`:
   - For each SVC entry with `response_fields`:
     - Find frontend type/interface/model files using existing `_find_files_by_pattern()`
     - Parse TypeScript interface field declarations using regex: `^\s+(\w+)\s*[?]?\s*:\s*`
     - For each interface whose declared fields are a SUPERSET of the SVC `response_fields` (≥50% overlap), consider it a match
     - For each field in the matched interface that is NOT in `response_fields`:
       - Skip universal fields: `id`, `createdAt`, `updatedAt`, `createdBy`, `updatedBy`
       - Skip UI-only fields: `isLoading`, `isSelected`, `isExpanded`, `className`, `key`, `ref`, `children`, `style`
       - Remaining fields → **API-002 violation** (severity: "error", or "warning" if field is optional `?`)
3. Call `_check_frontend_extra_fields()` inside `run_api_contract_scan()` alongside the existing checks

**Violation format:**
```
API-002: Frontend interface expects field 'companyName' but SVC-009 response schema does not include it.
  Backend must either add this field to the response DTO or frontend must remove it from the interface.
```

**False positive prevention:**
- ≥50% field overlap required to match interface to SVC entry (prevents matching unrelated interfaces)
- Skip universal fields (`id`, timestamps) and UI-only fields
- Optional fields (`field?:`) flagged as "warning" not "error"
- If no matching interface found → skip (no violation)
- camelCase↔PascalCase normalization via existing `_to_pascal_case()`

**Backward compatibility:** Existing API-001 and API-002 behavior is UNCHANGED. This is purely ADDITIVE — a new pass inside the same function.

### 2.4: Prompt Injection — Architect .NET Boilerplate (NEW — not in original plan)

**File:** agents.py — ARCHITECT_PROMPT

**Inject into:** After the "Status/Enum Registry" section (~line 978), before "Milestone Handoff" section.

**Why this exists:** The architect decides the project's boilerplate. If we teach it to always include `JsonStringEnumConverter`, the ENUM-004 scan becomes a safety net that never fires. **Prevention > Detection.**

**Content (~50 tokens):**

```
### .NET Serialization Configuration
When designing a .NET backend, ALWAYS include in the startup/Program.cs boilerplate:
  builder.Services.AddControllers().AddJsonOptions(o =>
    o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));
This prevents all enum serialization mismatches between backend integers and frontend strings.
Without this, EVERY enum field breaks — Fix 8, 11, 29 from Bayan were all caused by this single missing line.
```

### 2.5: Prompt Injection — Enum Serialization (Code Reviewer)

**File:** agents.py — CODE_REVIEWER_PROMPT

**Inject into:** After the "Enum/Status Registry" verification section (~line 1320), before "Orphan Detection".

**Content (~120 tokens):**

```
### Enum Serialization (ENUM-004)
For .NET backends: VERIFY that Program.cs / Startup.cs configures JsonStringEnumConverter globally:
  builder.Services.AddControllers().AddJsonOptions(o =>
    o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));
If NOT configured globally, EVERY DTO enum property sent to the frontend MUST have:
  [JsonConverter(typeof(JsonStringEnumConverter))]
Without this, enums serialize as integers (0, 1, 2) but frontend code compares strings ("submitted", "approved"). This causes silent display failures and TypeError crashes on .toLowerCase().
FLAG any enum property in a response DTO without string serialization configured.
```

**Note on conditionality:** agents.py prompts are static strings — there is NO per-project conditional injection. The "For .NET backends:" prefix makes the AI apply it contextually. This matches how the existing ZERO MOCK DATA POLICY lists Angular/React/Vue/Python patterns in a single prompt.

### 2.6: Prompt Injection — Silent Data Loss (Code Reviewer)

**File:** agents.py — CODE_REVIEWER_PROMPT

**Inject into:** Immediately after the enum serialization block from 2.5.

**Content (~180 tokens):**

```
### Silent Data Loss Prevention (SDL-001/002/003)
These are CRITICAL bugs that appear to succeed but lose data silently. REJECT the review if found:

SDL-001 — CQRS PERSISTENCE: Every CommandHandler that modifies data MUST call SaveChangesAsync() or equivalent. A handler that returns a DTO without persisting is a data-loss bug — AUTOMATIC REVIEW FAILURE.

SDL-002 — RESPONSE CONSUMPTION: When chaining API calls, ALWAYS use the response from the previous call:
  WRONG: switchMap(() => this.service.nextCall(staleData))
  RIGHT: switchMap((result) => this.service.nextCall(result.items))
Ignoring a response means the next operation uses stale or empty data.

SDL-003 — SILENT GUARDS: If a user-initiated method (click handler, submit, save) has a guard clause that returns early, it MUST provide user feedback (toast, console.warn, or error message). A button that silently does nothing is a UX bug.

These bugs pass all tests and only surface during manual E2E testing.
```

### 2.7: Prompt Injection — E2E Mutation Verification

**File:** e2e_testing.py — BACKEND_E2E_PROMPT and FRONTEND_E2E_PROMPT

**IMPORTANT:** This goes in e2e_testing.py, NOT agents.py. The E2E test generation prompts live there.

**Inject into:** Both `BACKEND_E2E_PROMPT` and `FRONTEND_E2E_PROMPT`, at the end of test-writing instructions.

**Content (~90 tokens each):**

```
### Mutation Verification Rule
Every test that performs a mutation (POST, PUT, PATCH, DELETE) MUST verify the effect with a subsequent GET request. Do NOT trust the mutation response alone.

Example:
  // Create a task
  const created = await POST('/api/tasks', payload);
  expect(created.status).toBe(201);
  // VERIFY it actually persisted
  const fetched = await GET(`/api/tasks/${created.body.id}`);
  expect(fetched.body.title).toBe(payload.title);

This catches handlers that return success but don't persist data (SDL-001).
```

### 2.8: Config — New Field + All Wiring Touchpoints

**This is a checklist — every item MUST be completed or the feature silently fails.**

#### 2.8a: PostOrchestrationScanConfig (config.py)

Add `silent_data_loss_scan: bool = True` to the dataclass:

```python
@dataclass
class PostOrchestrationScanConfig:
    mock_data_scan: bool = True
    ui_compliance_scan: bool = True
    api_contract_scan: bool = True
    silent_data_loss_scan: bool = True    # NEW: SDL-001 CQRS persistence check
    max_scan_fix_passes: int = 1
```

#### 2.8b: _dict_to_config() (config.py ~line 1164)

In the `if "post_orchestration_scans" in data` block, add:
- Parse `silent_data_loss_scan` from YAML (with default True)
- Track it in `user_overrides` if explicitly set

Follow the EXACT pattern of the existing `api_contract_scan` parsing.

#### 2.8c: apply_depth_quality_gating() (config.py ~line 512)

In the `if depth == "quick":` block, add:
```python
_gate("post_orchestration_scans.silent_data_loss_scan", False, config.post_orchestration_scans, "silent_data_loss_scan")
```

No changes needed for standard/thorough/exhaustive — default True is correct for all.

#### 2.8d: display.py type_hints (~line 623)

Add to the `type_hints` dict:
```python
"silent_data_loss_fix": "Command handlers missing persistence calls (SDL-001)",
```

#### 2.8e: code_quality_standards.py

Add a new constant after `API_CONTRACT_STANDARDS`:

```python
SILENT_DATA_LOSS_STANDARDS = r"""
## Silent Data Loss Prevention Standards

### SDL-001: CQRS Command Handler Missing Persistence
**Severity:** error
A command handler modifies data but never calls SaveChangesAsync() or equivalent.
Data appears saved but is lost. Every command handler that writes data MUST persist.

### ENUM-004: Enum Serialization Format
**Severity:** error
A .NET project does not configure JsonStringEnumConverter globally.
Enums serialize as integers (0, 1, 2) instead of strings ("submitted", "approved"),
causing silent display failures and TypeError crashes in the frontend.
""".strip()
```

Add to `_AGENT_STANDARDS_MAP`:
```python
"code-writer": [FRONTEND_STANDARDS, BACKEND_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS, SILENT_DATA_LOSS_STANDARDS],
"code-reviewer": [CODE_REVIEW_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS, SILENT_DATA_LOSS_STANDARDS],
```

### 2.9: CLI Wiring — SDL Scan Block (cli.py)

**Insert between:** the API contract scan block (ends ~line 4930) and the E2E Testing Phase (starts ~line 4932).

**Follow the EXACT template from the API contract scan block.** Here is the structure:

```python
    # -------------------------------------------------------------------
    # Post-orchestration: Silent Data Loss scan (SDL-001)
    # -------------------------------------------------------------------
    if config.post_orchestration_scans.silent_data_loss_scan:
        try:
            from .quality_checks import _check_cqrs_persistence
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                sdl_violations = _check_cqrs_persistence(Path(cwd), scope=scan_scope)
                if sdl_violations:
                    if _fix_pass > 0:
                        print_info(f"SDL scan pass {_fix_pass + 1}: {len(sdl_violations)} residual violation(s)")
                    else:
                        for v in sdl_violations[:5]:
                            print_contract_violation(v.check, v.message, v.severity)
                        print_warning(
                            f"Silent data loss scan: {len(sdl_violations)} "
                            f"violation(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("silent_data_loss_fix")
                    if _max_passes > 0:
                        try:
                            sdl_fix_cost = asyncio.run(_run_silent_data_loss_fix(
                                cwd=cwd,
                                config=config,
                                sdl_violations=sdl_violations,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += sdl_fix_cost
                        except Exception as exc:
                            print_warning(f"SDL fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Silent data loss scan: 0 violations (clean)")
                    else:
                        print_info(f"SDL scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Silent data loss scan failed: {exc}")
```

### 2.10: Fix Function — _run_silent_data_loss_fix() (cli.py)

**Model after `_run_api_contract_fix()` (~line 1518-1595).** Same structure, different fix prompt.

```python
async def _run_silent_data_loss_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    sdl_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix silent data loss violations (SDL-001).

    Creates a focused prompt listing each violation and instructing
    the orchestrator to deploy code-writers to add persistence calls.
    """
    if not sdl_violations:
        return 0.0

    print_info(f"Running SDL fix pass ({len(sdl_violations)} violations)")

    violation_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in sdl_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: SILENT DATA LOSS FIX]\n\n"
        f"The following silent data loss violations were detected — command handlers\n"
        f"that modify data but never persist changes.\n\n"
        f"Violations found:\n{violation_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For SDL-001 (CQRS handler missing persistence):\n"
        f"   - Add SaveChangesAsync() call before the handler returns\n"
        f"   - Ensure _context / _dbContext is injected via constructor\n"
        f"   - If using Unit of Work pattern, call _unitOfWork.SaveChangesAsync()\n"
        f"   - The handler MUST persist its changes — returning a DTO without saving is a data loss bug\n"
        f"2. For ENUM-004 (missing JsonStringEnumConverter):\n"
        f"   - Add to Program.cs: builder.Services.AddControllers().AddJsonOptions(o =>\n"
        f"       o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));\n"
        f"   - Add 'using System.Text.Json.Serialization;' if not present\n"
        f"3. Fix ONLY the listed violations. Do not refactor or change anything else.\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Silent Data Loss",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in sdl_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="silent_data_loss_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"SDL fix pass failed: {exc}")

    return cost
```

### 2.11: ENUM-004 Integration into run_api_contract_scan()

**File:** quality_checks.py — inside `run_api_contract_scan()`

After the existing checks (API-001, API-002, API-003), add:

```python
    # ENUM-004: Check .NET enum serialization (runs as part of API contract scan)
    violations.extend(_check_enum_serialization(project_root, scope))
```

This is a ONE-LINE addition to the existing function. The `_check_enum_serialization` function handles all the logic.

---

## PHASE 3: TESTS + WIRING VERIFICATION (test-engineer)

After Phase 2 is complete, write tests and verify wiring. The test-engineer handles BOTH testing and wiring verification (previously separate agents — merged to eliminate coordination overhead).

### Test File: tests/test_v11_gap_closure.py

### ENUM-004 Tests (~12 tests)

**Positive detection:**
- .NET project (has .csproj) with no JsonStringEnumConverter in Program.cs → 1 ENUM-004 violation
- .NET project with no Program.cs or Startup.cs at all → 1 violation

**Negative (no false positives):**
- .NET project WITH `JsonStringEnumConverter` in Program.cs → 0 violations
- .NET project WITH `JsonStringEnumConverter` in Startup.cs → 0 violations
- Python project (no .csproj) → 0 violations (scan skips)
- Node.js project (no .csproj) → 0 violations (scan skips)
- Empty directory → 0 violations, no crash

**Edge cases:**
- Multiple .csproj files → still works (finds any)
- JsonStringEnumConverter in a nested Startup.cs → still caught
- Project with .csproj but no .cs files → 1 violation (correct — still needs global converter)
- File read error on Program.cs → graceful handling, doesn't crash

### SDL-001 Tests (~15 tests)

**Positive detection:**
- File named `CreateOrderCommandHandler.cs` with no persistence keywords → 1 SDL-001 violation
- File named `import_command_handler.py` with no `db.session.commit()` → 1 violation
- File in Commands/ directory matching pattern → flagged

**Negative:**
- File named `GetOrderQueryHandler.cs` → NOT flagged (query handler excluded)
- File named `CreateOrderCommandHandler.cs` with `SaveChangesAsync` → NOT flagged (has persistence)
- File named `CreateOrderCommandHandler.cs` with `_repository.Add` → NOT flagged
- File named `CreateOrderCommandHandler.cs` with `_unitOfWork.Complete` → NOT flagged
- File containing `INotificationHandler` → NOT flagged (event-only)
- File containing `_mediator.Publish` → NOT flagged (event dispatch)
- Non-handler file → NOT scanned
- Test files (`CreateOrderCommandHandler.test.cs`) → NOT scanned
- No command handler files in project → 0 violations, no crash

**Edge cases:**
- Handler delegates to repository (repo persists internally) → flagged (acceptable FP)
- ScanScope filtering works correctly
- Empty project → 0 violations, no crash
- _MAX_VIOLATIONS cap respected

### API-002 Bidirectional Tests (~15 tests)

**Positive detection:**
- Frontend interface has field `companyName`, SVC response_fields doesn't → violation
- Frontend interface has field `clarifications`, SVC has `clarificationCount` → violation (different name)
- Multiple extra fields in one interface → multiple violations

**Negative:**
- Frontend and backend fields match (camelCase↔PascalCase) → 0 violations
- Frontend optional field (`field?: type`) → flagged as "warning" not "error"
- Universal fields (`id`, `createdAt`, `updatedAt`) → NOT checked
- UI-only fields (`isLoading`, `isSelected`, `className`) → NOT checked
- Interface with <50% field overlap → NOT matched (different type)

**Backward compatibility:**
- ALL existing API-001 tests still pass unchanged
- ALL existing API-002 (forward) tests still pass unchanged
- New bidirectional check is additive only

### Config Tests (~10 tests)

- `PostOrchestrationScanConfig` has `silent_data_loss_scan` field with default `True`
- `_dict_to_config({})` returns config with `silent_data_loss_scan=True`
- `_dict_to_config({"post_orchestration_scans": {"silent_data_loss_scan": False}})` returns `False`
- `_dict_to_config({"post_orchestration_scans": {"silent_data_loss_scan": True}})` adds to user_overrides
- `apply_depth_quality_gating("quick", ...)` sets `silent_data_loss_scan=False`
- `apply_depth_quality_gating("standard", ...)` leaves `silent_data_loss_scan=True`
- User override of `silent_data_loss_scan` is NOT overridden by depth gating
- Unknown YAML keys don't break parsing

### Prompt Tests (~10 tests)

- ARCHITECT_PROMPT contains "JsonStringEnumConverter" and ".NET Serialization"
- CODE_REVIEWER_PROMPT contains "Enum Serialization (ENUM-004)"
- CODE_REVIEWER_PROMPT contains "Silent Data Loss Prevention (SDL-001/002/003)"
- CODE_REVIEWER_PROMPT contains "CQRS PERSISTENCE"
- CODE_REVIEWER_PROMPT contains "RESPONSE CONSUMPTION"
- CODE_REVIEWER_PROMPT contains "SILENT GUARDS"
- BACKEND_E2E_PROMPT contains "Mutation Verification Rule"
- FRONTEND_E2E_PROMPT contains "Mutation Verification Rule"
- SILENT_DATA_LOSS_STANDARDS in code_quality_standards exists
- SILENT_DATA_LOSS_STANDARDS mapped to code-writer and code-reviewer in _AGENT_STANDARDS_MAP
- Total new prompt tokens < 550 (measure by splitting on whitespace)

### Wiring Verification Tests (~10 tests)

- Pattern IDs ENUM-004, SDL-001 don't collide with existing IDs (FRONT-xxx, BACK-xxx, MOCK-xxx, UI-xxx, E2E-xxx, DEPLOY-xxx, ASSET-xxx, PRD-xxx, DB-xxx, API-xxx, ENUM-001..003)
- `"silent_data_loss_fix"` exists in display.py type_hints dict
- New imports in cli.py resolve correctly (mock test)
- SDL scan block position: after API contract, before E2E testing (verify by reading cli.py source order)
- ENUM-004 scan runs inside run_api_contract_scan (verify by reading function body)
- `_run_silent_data_loss_fix` function exists in cli.py with correct signature
- Recovery type "silent_data_loss_fix" is appended when violations found
- Config gating: when `silent_data_loss_scan=False`, SDL block is skipped

### Regression Tests

- Run the FULL existing test suite: `pytest tests/ -v --tb=short`
- ALL existing tests must pass (except pre-existing known failures: test_mcp_servers.py)
- Zero new regressions
- Existing API-002 behavior unchanged
- Existing prompt content unchanged (only additions)
- Existing config behavior unchanged (only additions)

### Test Iteration Protocol

- Run `pytest tests/ -v --tb=short` after writing tests
- If any test fails: diagnose root cause, fix the CODE not the test (unless test expectation is provably wrong)
- Re-run until fully green
- Report final counts: total tests, new tests, failures, regressions

---

## PHASE 4: FINAL REPORT

After all phases complete, you (team lead) produce:

```markdown
# v11.0 E2E Gap Closure — Audit Report

## Implementation Summary
- New scans: 2 (ENUM-004 simplified, SDL-001 simplified)
- Enhanced scans: 1 (API-002 bidirectional)
- Prompt injections: 4 (architect .NET, reviewer enum, reviewer SDL, E2E mutation)
- Prompt-only coverage: 2 (SDL-002, SDL-003 — AI reviewer handles these)
- Config fields added: 1 (silent_data_loss_scan)
- Recovery types added: 1 (silent_data_loss_fix)
- Quality standards added: 1 (SILENT_DATA_LOSS_STANDARDS)
- Files modified: 7 (quality_checks.py, agents.py, e2e_testing.py, config.py, cli.py, display.py, code_quality_standards.py)

## Scan Coverage Matrix
| Pattern ID | What It Catches | Severity | Method | Conditional On | Original Bug |
|------------|----------------|----------|--------|----------------|--------------|
| ENUM-004 | .NET missing global JsonStringEnumConverter | error | Scan + architect prompt + reviewer prompt | .NET project | Fix 8, 11, 29 |
| SDL-001 | CQRS handler missing persistence call | error | Scan + reviewer prompt + E2E mutation | Command handler files exist | Fix 22 |
| SDL-002 | Frontend ignoring API response | — | Reviewer prompt only (no scan — FP risk too high) | All projects | Fix 23 |
| SDL-003 | Silent early return without feedback | — | Reviewer prompt only (no scan — requires method context) | All projects | Fix 20 |
| API-002 (enhanced) | Frontend field missing in backend DTO | error/warning | Scan (bidirectional) | SVC table exists | Fix 14, 15, 18 |

## Prompt Injection Summary
| Block | Target Prompt | File | Token Cost | Conditional |
|-------|--------------|------|------------|-------------|
| .NET serialization boilerplate | Architect | agents.py | ~50 tokens | "For .NET" prefix |
| Enum serialization | Code reviewer | agents.py | ~120 tokens | "For .NET" prefix |
| Silent data loss (SDL-001/002/003) | Code reviewer | agents.py | ~180 tokens | All projects |
| Mutation verification | E2E test (backend + frontend) | e2e_testing.py | ~90 tokens × 2 | All projects |

## Bug Prevention Coverage (Updated)
| Original Bug | Caught By | Method | Confidence |
|-------------|----------|--------|------------|
| Fix 8 (enum int→string) | ENUM-004 scan + architect prompt + reviewer prompt | Prevention + Detection + Safety net | HIGH |
| Fix 11 (admin enum) | ENUM-004 scan + architect prompt + reviewer prompt | Same | HIGH |
| Fix 14 (field presence) | API-002 bidirectional scan | Automated detection | HIGH |
| Fix 15 (missing field) | API-002 bidirectional scan | Automated detection | HIGH |
| Fix 18 (missing field) | API-002 bidirectional scan | Automated detection | HIGH |
| Fix 20 (silent guard) | Reviewer prompt (SDL-003 block) | AI review detection | MEDIUM |
| Fix 22 (no persistence) | SDL-001 scan + reviewer prompt + E2E mutation | Detection + Verification | HIGH |
| Fix 23 (ignored response) | Reviewer prompt (SDL-002 block) | AI review detection | MEDIUM-HIGH |
| Fix 29 (enum crash) | ENUM-004 scan + architect prompt + reviewer prompt | Same as Fix 8 | HIGH |

## Test Results
- New tests written: X
- All passing: YES/NO
- Regressions: X
- Pre-existing failures (unchanged): test_mcp_servers.py

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — gap-architect MUST finish before the implementer starts.
2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase. Consistency over creativity.
3. **READ BEFORE YOU WRITE** — Read every file before modifying it. The implementer must read ARCHITECTURE_REPORT.md before touching code.
4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test is wrong.
5. **ALL 8 FILES** — The implementer must make changes in all 7 source files listed in the team composition table. The test-engineer adds 1 test file. Missing any file = incomplete implementation.
6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate.
7. **PRECISION OVER RECALL** — For scans, false negatives are acceptable. False positives are not. A scan that flags 5 real issues is better than one that flags 50 with 45 false positives. When in doubt, don't flag it.
8. **CRASH ISOLATION** — Each scan independently wrapped in try/except. One failure cannot cascade.
9. **CONDITIONAL SCANS** — Every scan must skip gracefully when its preconditions aren't met (wrong language, missing framework, etc.).
10. **PROMPT ECONOMY** — Total new prompt content across all 4 injections must be under 550 tokens combined. Measure before and after. Cut ruthlessly.
11. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added and why in the final report.
12. **RUN TESTS AFTER IMPLEMENTATION** — The test-engineer runs the full suite and iterates until green.
13. **ScanScope SUPPORT** — All new scan functions must accept `scope: ScanScope | None = None` parameter. Apply scope filtering when provided, fall back to full-project scan when None.
