# CONFIG & SCANS REVIEW REPORT

> Reviewer: REVIEWER-CONFIG-SCANS
> Date: 2026-02-10
> Files reviewed: `src/agent_team/config.py` (1179 lines), `src/agent_team/quality_checks.py` (2625 lines)
> Method: Line-by-line manual audit against ARCHITECTURE_INVENTORY.md checklist

---

## Summary

| Metric | Count |
|--------|-------|
| Total checks performed | 82 |
| PASSED | 72 |
| FAILED | 10 |
| Severity breakdown | 0 CRITICAL, 2 HIGH, 4 MEDIUM, 4 LOW |

---

## FAILED CHECKS

### F1. HIGH | quality_checks.py:278-280 | E2E-006 `_RE_E2E_PLACEHOLDER` matches HTML `placeholder` attribute

**Description:** The regex `_RE_E2E_PLACEHOLDER` matches the bare word `placeholder` (line 279):
```python
r'(?:placeholder|coming.soon|will.be.implemented|...'
```
The HTML `placeholder` attribute is standard and universally used in `<input placeholder="Enter name">`. Every form input with a `placeholder` attribute will trigger a false-positive E2E-006 violation ("Placeholder text in UI component -- implement the actual feature"). This fires on **every** template file (`_EXT_TEMPLATE_CONTENT`) that is NOT in an `e2e/` directory (line 959).

**Impact:** High false-positive rate in real projects. Any React/Vue/Angular form component with `<input placeholder=...>` will be flagged. This undermines trust in the scan results.

**Suggested Fix:** Change the pattern to match *placeholder text indicators* rather than the HTML attribute name. For example:
```python
r'(?:coming.soon|will.be.implemented|future.milestone|under.construction|not.yet.available|lorem.ipsum|placeholder.text|placeholder.content)'
```
Or add a negative lookbehind/context check to exclude lines containing `placeholder="` or `placeholder={`.

---

### F2. HIGH | quality_checks.py:50-51 | `ScanScope.mode` field is declared but never read

**Description:** The `ScanScope` dataclass has a `mode` field (line 50: `mode: str = "full"`) with documented values `"full"`, `"changed_only"`, and `"changed_and_imports"`. However, no scan function in `quality_checks.py` ever reads `scope.mode`. All 7 scope-aware scan functions (`run_mock_data_scan`, `run_ui_compliance_scan`, `run_e2e_quality_scan`, `run_asset_scan`, `run_dual_orm_scan`, `run_default_value_scan`, `run_relationship_scan`) only check `scope.changed_files`.

The `mode` value is set in `cli.py` (per the architecture inventory, line ~3788):
```python
scan_scope = ScanScope(
    mode="changed_only" if depth == "quick" else "changed_and_imports",
    changed_files=changed,
)
```
But since no scan reads `mode`, the distinction between `"changed_only"` and `"changed_and_imports"` is **dead logic** -- both behave identically (filter to `changed_files` only).

**Impact:** The `"changed_and_imports"` mode promises to also scan importers of changed files, but this is never implemented. Scoped scans in `standard` depth miss transitively-affected files.

**Suggested Fix:** Either implement the `changed_and_imports` mode (compute importers using `_RE_ASSET_IMPORT` or similar) or remove the `mode` field and the CLI code that sets it, to avoid misleading behavior.

---

### F3. MEDIUM | config.py:937-943 | `quality.quality_triggers_reloop` not tracked in `user_overrides`

**Description:** The `_dict_to_config` quality section (lines 937-943) tracks `production_defaults` and `craft_review` in `user_overrides`, but NOT `quality_triggers_reloop`:
```python
for key in ("production_defaults", "craft_review"):
    if key in q:
        user_overrides.add(f"quality.{key}")
```
However, `quality_triggers_reloop` is not gated by `apply_depth_quality_gating` today (no `_gate()` call for it), so this is not currently exploitable. But if a future depth mode wants to gate this field, the missing override tracking would cause user config to be silently overridden.

**Impact:** Low today (the field is not gated), but violates the design principle that all gatable fields should be tracked.

**Suggested Fix:** Add `"quality_triggers_reloop"` to the override tracking loop, or document that this field is intentionally not depth-gatable.

---

### F4. MEDIUM | quality_checks.py:1268,1304 vs 1753,2036 | Inconsistent scope filtering approach

**Description:** Four scope-aware scan functions build their scope set differently:
- `run_mock_data_scan` (1268): `scope_set = set(scope.changed_files)` then `f.resolve() in scope_set`
- `run_ui_compliance_scan` (1304): `scope_set = set(scope.changed_files)` then `f.resolve() in scope_set`
- `run_asset_scan` (1753): `scope_set = set(f.resolve() for f in scope.changed_files)` then `file_path.resolve() in scope_set`
- `run_dual_orm_scan` (2036): `scope_set = set(f.resolve() for f in scope.changed_files)` then `f.resolve() in scope_set`

Since `compute_changed_files()` already returns resolved paths (line 86), the double-resolve in `run_asset_scan` and `run_dual_orm_scan` is redundant but harmless. However, the inconsistency is confusing for maintainers. Additionally, `run_default_value_scan` (2117) uses `set(scope.changed_files)` then `f.resolve() in scope_set`, and `run_relationship_scan` (2403) uses `set(scope.changed_files)` then `f.resolve() in scope_set`.

**Impact:** No runtime bug (paths are already resolved), but inconsistent patterns make reasoning about correctness harder.

**Suggested Fix:** Standardize all scope filtering to one approach. Recommended: always `set(scope.changed_files)` since the paths are already resolved.

---

### F5. MEDIUM | quality_checks.py:384-387 | `_RE_DB_PRISMA_ENUM_NO_DEFAULT` overlaps with `_RE_DB_PRISMA_NO_DEFAULT` and Prisma model keywords

**Description:** The regex `_RE_DB_PRISMA_ENUM_NO_DEFAULT` at line 384-387:
```python
r"""(\w+)\s+([A-Z]\w+)\s*$"""
```
This matches `fieldName  TypeName` at end of line where TypeName starts with uppercase. However, this pattern also matches Prisma model field directives/annotations and structural elements. For example, Prisma lines like:
- `@@map("some_table")` -- won't match (no space+Uppercase)
- `model User {` -- won't match (has `{`)
- `id  String` -- matches but filtered by `_PRISMA_BUILTIN_TYPES`

The regex is validated by the `_PRISMA_BUILTIN_TYPES` filter at line 2342, but it could still false-positive on Prisma model/enum declarations or relation fields with `@relation` directives on the next line (since the regex looks at `$` end-of-line).

A line like `author  User` in a Prisma schema would match and get flagged as "enum field without @default" even though it's a relation field (not an enum). The `@default` check on the next line won't help because relation fields don't have `@default`.

**Impact:** False positives on Prisma relation fields that reference user-defined model types. E.g., `author User` flagged as needing `@default`.

**Suggested Fix:** After the `_PRISMA_BUILTIN_TYPES` filter, add a check for `@relation` on the next line. Or maintain a set of known model names and skip fields whose type matches a model name (indicating a relation, not an enum).

---

### F6. MEDIUM | quality_checks.py:2166-2202 | DB-005 C# nullable access pattern has quadratic complexity

**Description:** For each entity file, `run_default_value_scan` collects nullable properties, then iterates ALL source files checking for unsafe access (line 2173: `for sf in source_files`). If there are N entity files each with M nullable props and S source files, the complexity is O(N * M * S * content_size). For a project with many entity files, this could be slow.

The same issue exists for Python (line 2234) and TypeScript (line 2274) nullable property checks.

This is not a correctness bug, but a performance concern for large projects.

**Impact:** Scan could become slow on large codebases (many entity files + many source files).

**Suggested Fix:** Consider building a single pass index of all property accesses across source files, then checking nullable properties against the index. Or at minimum, add a file count guard.

---

### F7. LOW | config.py:490-511 | Quick mode does not gate `tracking_documents` or `investigation` fields

**Description:** `apply_depth_quality_gating` disables 13+ fields in quick mode (quality, post_orchestration_scans, milestone, integrity_scans, database_scans, e2e_testing) but does NOT disable:
- `tracking_documents.e2e_coverage_matrix` (moot since E2E is disabled, but not explicitly off)
- `tracking_documents.fix_cycle_log` (could still fire in review recovery)
- `tracking_documents.milestone_handoff` (moot if milestones not enabled, but not gated)
- `investigation.enabled` (Gemini investigation)

**Impact:** LOW -- tracking documents are mostly gated indirectly by their parent phases being disabled. Investigation is opt-in by default. But explicit gating would be cleaner.

**Suggested Fix:** Consider adding explicit `_gate()` calls for `tracking_documents.*` in quick mode.

---

### F8. LOW | quality_checks.py:279 | `_RE_E2E_PLACEHOLDER` uses `.` instead of `\.` for literal dots

**Description:** The regex uses `coming.soon`, `will.be.implemented`, etc. The `.` is regex wildcard matching any character, not a literal dot. This means `coming_soon`, `comingXsoon`, etc. would all match. While this broadens detection (which may be intentional for flexible text matching), it's technically imprecise.

**Impact:** Very minor false-positive expansion. Most matches will be correct.

**Suggested Fix:** If strict matching is desired, use `coming\.soon` etc. If flexible matching is intentional, document it.

---

### F9. LOW | config.py:977-1006 | `milestone.mock_data_scan` and `milestone.ui_compliance_scan` user_overrides tracked separately from migration target

**Description:** When the user sets `milestone.mock_data_scan: true` in YAML, the override is tracked as `"milestone.mock_data_scan"` (line 981). But the backward-compat migration (lines 1103-1109) copies the value to `post_orchestration_scans.mock_data_scan` without tracking `"post_orchestration_scans.mock_data_scan"` as an override. This means:
1. User sets `milestone.mock_data_scan: true`
2. Migration copies to `post_orchestration_scans.mock_data_scan = true`
3. Depth gating calls `_gate("post_orchestration_scans.mock_data_scan", False, ...)` in quick mode
4. Since `"post_orchestration_scans.mock_data_scan"` is NOT in overrides, it gets gated to `False`
5. But `"milestone.mock_data_scan"` IS in overrides, so the milestone field stays `True`
6. The OR gate in cli.py saves the day: `config.post_orchestration_scans.mock_data_scan or config.milestone.mock_data_scan`

So the behavior is ultimately correct due to the OR gate, but the logic chain is fragile and non-obvious.

**Impact:** Works correctly today due to the OR gate, but is a maintenance hazard. If the OR gate is ever removed, depth gating would override user intent.

**Suggested Fix:** When migrating from `milestone.*` to `post_orchestration_scans.*`, also add the target key to `user_overrides`:
```python
if "mock_data_scan" in ms:
    user_overrides.add("post_orchestration_scans.mock_data_scan")
```

---

### F10. LOW | quality_checks.py:92-100 | `Violation` dataclass field naming inconsistency with architecture docs

**Description:** The `Violation` dataclass uses `check` (line 96) but the architecture inventory and some code comments reference it as "rule" or "pattern ID". The field name `check` is used consistently in the code, but the architecture inventory at line 74 says `rule, severity, file, line, message, suggestion` which includes a `suggestion` field that does not exist on the actual dataclass.

**Impact:** Documentation mismatch only. The code is internally consistent.

**Suggested Fix:** Update the architecture inventory to match the actual field names: `check, message, file_path, line, severity`.

---

## PASSED CHECKS

### Review Area 1: Config Dataclasses (18 dataclasses verified)

| Dataclass | Status | Notes |
|-----------|--------|-------|
| `OrchestratorConfig` | PASS | 6 fields, correct types and defaults |
| `DepthConfig` | PASS | 4 fields including `scan_scope_mode` |
| `ConvergenceConfig` | PASS | 8 fields with validation function |
| `AgentConfig` | PASS | 2 fields |
| `MCPServerConfig` | PASS | 1 field |
| `InterviewConfig` | PASS | 7 fields with validation |
| `InvestigationConfig` | PASS | 8 fields with validation |
| `OrchestratorSTConfig` | PASS | 3 fields with validation |
| `DesignReferenceConfig` | PASS | 10 fields including v3.0 additions |
| `DisplayConfig` | PASS | 5 fields |
| `CodebaseMapConfig` | PASS | 6 fields |
| `SchedulerConfig` | PASS | 5 fields |
| `QualityConfig` | PASS | 3 fields |
| `VerificationConfig` | PASS | 11 fields |
| `MilestoneConfig` | PASS | 10 fields including legacy mock/UI scan bools |
| `PostOrchestrationScanConfig` | PASS | 2 fields (v6.0) |
| `PRDChunkingConfig` | PASS | 3 fields |
| `E2ETestingConfig` | PASS | 7 fields with validation |
| `IntegrityScanConfig` | PASS | 3 fields |
| `TrackingDocumentsConfig` | PASS | 5 fields with gate validations |
| `DatabaseScanConfig` | PASS | 3 fields |
| `AgentTeamConfig` | PASS | 18 sub-configs, all wired |

No dead fields found (all referenced in code). No missing fields found.

### Review Area 2: Config Loading (`_dict_to_config`)

| Check | Status | Notes |
|-------|--------|-------|
| Every dataclass has `if "section" in data:` block | PASS | All 16 sections covered |
| Every field uses `.get()` with correct default | PASS | Verified for all sections |
| Return type is `tuple[AgentTeamConfig, set[str]]` | PASS | Line 787 |
| `scan_scope_mode` validation | PASS | Line 821, validates against `("auto", "full", "changed")` |
| `extraction_retries >= 0` validation | PASS | Line 885 |
| `test_port` 1024-65535 validation | PASS | Line 1055 |
| `max_fix_retries >= 1` validation | PASS | Line 1049 |
| `coverage_completeness_gate` 0.0-1.0 validation | PASS | Line 1071 |
| `wiring_completeness_gate` 0.0-1.0 validation | PASS | Line 1077 |
| `review_recovery_retries >= 0` validation | PASS | Line 1008 |
| `convergence` thresholds validated | PASS | `_validate_convergence_config` called at line 846 |
| Backward-compat migration | PASS | Lines 1103-1109: milestone.mock_data_scan -> post_orchestration_scans |
| User overrides tracking covers gatable fields | PASS (with caveat) | See F3 for `quality_triggers_reloop` gap |

**Tracked user_overrides keys:**
- `quality.production_defaults`, `quality.craft_review` (line 939)
- `milestone.mock_data_scan`, `milestone.ui_compliance_scan`, `milestone.review_recovery_retries` (line 981)
- `integrity_scans.deployment_scan`, `integrity_scans.asset_scan`, `integrity_scans.prd_reconciliation` (line 1026)
- `e2e_testing.enabled`, `e2e_testing.max_fix_retries` (line 1037)
- `database_scans.dual_orm_scan`, `database_scans.default_value_scan`, `database_scans.relationship_scan` (line 1087)
- `post_orchestration_scans.mock_data_scan`, `post_orchestration_scans.ui_compliance_scan` (line 1098)

### Review Area 3: Depth Gating (`apply_depth_quality_gating`)

| Check | Status | Notes |
|-------|--------|-------|
| Signature includes `user_overrides: set[str] \| None = None` | PASS | Line 468 |
| `_gate()` helper checks key not in overrides | PASS | Line 487 |
| Quick mode: 14 fields disabled | PASS | Lines 492-511, verified all scan/quality fields |
| Quick mode: `review_recovery_retries=0` | PASS | Line 500 |
| Standard mode: only `prd_reconciliation` disabled | PASS | Line 515 |
| Thorough mode: E2E enabled, retries=2 | PASS | Lines 519-521 |
| Exhaustive mode: E2E enabled, retries=3 | PASS | Lines 525-527 |
| No unexpected mutation | PASS | All changes go through `_gate()` |

### Review Area 4: Scan Functions (10 functions verified)

| Function | Signature | Scope | Returns | MAX_VIOLATIONS | Status |
|----------|-----------|-------|---------|----------------|--------|
| `run_spot_checks` | `(Path)` | N/A (full) | `list[Violation]` | Yes (1246) | PASS |
| `run_mock_data_scan` | `(Path, ScanScope\|None)` | Simple filter | `list[Violation]` | Yes (1285) | PASS |
| `run_ui_compliance_scan` | `(Path, ScanScope\|None)` | Simple filter | `list[Violation]` | Yes (1321) | PASS |
| `run_e2e_quality_scan` | `(Path, ScanScope\|None)` | Two-phase (H1 fix) | `list[Violation]` | Yes (1437) | PASS |
| `run_deployment_scan` | `(Path)` | N/A (always full) | `list[Violation]` | Yes (1706) | PASS |
| `run_asset_scan` | `(Path, ScanScope\|None)` | Scope filter | `list[Violation]` | Yes (1808) | PASS |
| `parse_prd_reconciliation` | `(Path)` | N/A (file-based) | `list[Violation]` | Yes (1843) | PASS |
| `run_dual_orm_scan` | `(Path, ScanScope\|None)` | Two-phase (H2 fix) | `list[Violation]` | Yes (2100) | PASS |
| `run_default_value_scan` | `(Path, ScanScope\|None)` | Scope filter | `list[Violation]` | Yes (2377) | PASS |
| `run_relationship_scan` | `(Path, ScanScope\|None)` | Two-phase (M1 fix) | `list[Violation]` | Yes (2622) | PASS |

**Scope-aware two-phase logic:**
- `run_e2e_quality_scan` E2E-005: PASS -- aggregate check uses full file list (line 1376-1388)
- `run_dual_orm_scan`: PASS -- detection phase uses `all_files` (line 1995), violations scoped (line 2034-2037)
- `run_relationship_scan`: PASS -- `entity_info` from ALL files (line 2416), violations scoped via `_scoped_entity_rel_paths` (line 2568)

### Review Area 5: Regex Pattern Correctness

**MOCK-001..007 (7 patterns, lines 178-206):**
| Pattern | Regex valid | Semantics | Status |
|---------|-------------|-----------|--------|
| MOCK-001 (`_RE_RXJS_OF_MOCK`, `_RE_RXJS_DELAY_PIPE`, `_RE_MOCK_RETURN_OF`) | PASS | Correct targets | PASS |
| MOCK-002 (`_RE_PROMISE_RESOLVE_MOCK`) | PASS | Correct target | PASS |
| MOCK-003 (`_RE_MOCK_VARIABLE`) | PASS | Case-insensitive, good word list | PASS |
| MOCK-004 (`_RE_TIMEOUT_MOCK`) | PASS | Correct target | PASS |
| MOCK-005 (`_RE_DELAY_SIMULATE`) | PASS | Correct target | PASS |
| MOCK-006 (`_RE_BEHAVIOR_SUBJECT_MOCK`) | PASS | Correct target | PASS |
| MOCK-007 (`_RE_OBSERVABLE_MOCK`) | PASS | Correct target | PASS |

**UI-001..004 (4 patterns + supporting, lines 213-247):**
| Pattern | Status | Notes |
|---------|--------|-------|
| UI-001 (`_RE_HARDCODED_HEX_CSS`, `_RE_HARDCODED_HEX_STYLE`, `_RE_TAILWIND_ARBITRARY_HEX`) | PASS | Correct targets, config file exempt |
| UI-002 (`_RE_DEFAULT_TAILWIND_EXTENDED`) | PASS | Extended palette (indigo/violet/purple 400-700) |
| UI-003 (`_RE_GENERIC_FONT_CONFIG`) | PASS | `fontFamily` camelCase supported |
| UI-004 (`_RE_ARBITRARY_SPACING`) | PASS | Directional Tailwind `p[tlbrxy]?-`, `m[tlbrxy]?-` |
| `_RE_CONFIG_FILE` | PASS | Path-segment-aware, avoids ThemeToggle.tsx false positive |

**E2E-001..007 (7 patterns, lines 253-289):**
| Pattern | Status | Notes |
|---------|--------|-------|
| E2E-001 (`_RE_E2E_SLEEP`) | PASS | setTimeout + time.sleep |
| E2E-002 (`_RE_E2E_HARDCODED_PORT`) | PASS | With exemption for env/config refs |
| E2E-003 (`_RE_E2E_MOCK_DATA`) | PASS | mockData, fakeResponse, Promise.resolve |
| E2E-004 (`_RE_E2E_EMPTY_TEST`) | PASS | Empty async test body |
| E2E-005 (`_RE_E2E_AUTH_TEST`) | PASS | Inverted check with full-file aggregate |
| E2E-006 (`_RE_E2E_PLACEHOLDER`) | **FAIL** | See F1 -- matches HTML `placeholder` attribute |
| E2E-007 (`_RE_E2E_ROLE_FAILURE`) | PASS | 403/Forbidden/Unauthorized in results |

**DEPLOY-001..004 (infrastructure patterns):**
| Pattern | Status | Notes |
|---------|--------|-------|
| `_parse_docker_compose` | PASS | Returns None for non-dict YAML |
| `_parse_env_file` | PASS | BOM strip + export prefix handling |
| `_BUILTIN_ENV_VARS` | PASS | Standard env vars excluded |
| `_RE_ENV_WITH_DEFAULT` | PASS | process.env with ||/??, os.getenv 2-arg |
| `_RE_APP_LISTEN_PORT` | PASS | .listen(), uvicorn.run, .set("port") |
| `_RE_CORS_ORIGIN` | PASS | cors(), CORS_ALLOWED, allow_origins, enableCors |

**ASSET-001..003 (asset patterns):**
| Pattern | Status | Notes |
|---------|--------|-------|
| `_is_static_asset_ref` | PASS | Query string/fragment stripping, external URL exclusion |
| `_resolve_asset` | PASS | 7 candidate paths, query/hash strip |
| `_RE_ASSET_SRC`, `_RE_ASSET_HREF` | PASS | Standard src/href extraction |
| `_RE_ASSET_CSS_URL` | PASS | url() extraction |

**DB-001..008 (database patterns):**
| Pattern | Status | Notes |
|---------|--------|-------|
| DB-001 enum detection | PASS | `_CSHARP_NON_ENUM_TYPES` + suffix filtering |
| DB-002 bool detection | PASS | `_RE_DB_SQL_BOOL_INT` |
| DB-003 datetime detection | PASS | Implemented (was dead code, now working) |
| DB-004 C# bool no-default | PASS | `init;`, `private set;`, `protected set;` supported |
| DB-004 Prisma no-default | PASS | Boolean/Int + enum + String status |
| DB-004 Django/SQLAlchemy | PASS | BooleanField(), Column(Boolean/Enum) |
| DB-005 C#/TS/Python nullable | PASS | 500-char window, optional chaining, Optional[] |
| DB-006 FK no nav | PASS | Correct severity "warning" |
| DB-007 nav no inverse | PASS | Correct severity "info" |
| DB-008 FK no config | PASS | Correct severity "error" |
| `_RE_ENTITY_INDICATOR_PY` | PASS | `declarative_base` pattern, not bare `\bBase\b` |
| TS raw SQL comment skipping | PASS | Lines 1919-1921 skip `//`, `*`, `/*` lines |
| Prisma enum → `_PRISMA_BUILTIN_TYPES` filter | PASS (with caveat) | See F5 for relation field false positives |

**PRD-001 (reconciliation):**
| Pattern | Status | Notes |
|---------|--------|-------|
| `parse_prd_reconciliation` | PASS | h4 (`####`) does not exit mismatch mode (line 1831 checks `#{2,3}` only) |

---

## Overall Assessment

**MINOR FIXES** -- The codebase is well-structured with consistent patterns. The 10 findings break down as:

- **2 HIGH**: E2E-006 `placeholder` false positives (F1) and dead `ScanScope.mode` field (F2) are the most impactful. F1 is the most likely to cause user-visible issues in production.
- **4 MEDIUM**: Override tracking gap (F3), inconsistent scope filtering (F4), Prisma relation false positives (F5), and quadratic DB-005 complexity (F6) are design debt items.
- **4 LOW**: Missing tracking document gating (F7), imprecise dot escaping (F8), fragile migration chain (F9), and doc mismatch (F10) are cosmetic.

No CRITICAL issues found. All scan functions respect `_MAX_VIOLATIONS`, all return `list[Violation]`, all config validations are present. The depth gating logic is correct and comprehensive. The two-phase scope handling for E2E-005, dual ORM, and relationship scans is properly implemented.

The most impactful fix would be F1 (E2E-006 placeholder regex), which will cause false positives in virtually every real project with form inputs.
