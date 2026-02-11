# v12.0 Hard Ceiling Implementation Plan

## Team Pipeline

```
Agent 1: gap-architect    → Phase 1 (read-only: discover architecture, verify line numbers)
Agent 2: implementer      → Phase 2 (write: implement all sections 2.1-2.11)
Agent 3: test-engineer    → Phase 3 (write: create test file, run full suite)
```

Sequential execution: Agent 1 completes → Agent 2 starts → Agent 3 starts.

---

## Background

### The Problem
Agent-team v1-v11 catches **36% (12/33)** of Bayan manual E2E bugs. The V11_GAP_ANALYSIS_HONEST.md identified three production-grade recommendations to reach the hard ceiling of **~76% (25/33)**.

### What v12 Adds
| Feature | Type | Bugs Caught | Confidence |
|---------|------|-------------|------------|
| XREF-001: Frontend-Backend Endpoint Cross-Reference | Deterministic scan | Fix 7, 16, 32 (3 bugs) | 95% |
| API-004: Write-Side Field Passthrough | Deterministic scan (integrated into API contract scan) | Fix 31, 34 (2 bugs) | 85% |
| E2E Testing Directives (6 directives) | Prompt enhancement | Fix 1, 9, 25, 27, 30, 36 (+Fix 17, 28, 33) | 60-80% |
| Browser Testing Directives (5 directives) | Prompt enhancement | Overlaps with E2E (visual verification layer) | 50-70% |
| Architect + Reviewer Prompts | Prevention layer | Supports XREF-001 + API-004 | HIGH |

### Coverage Projection
| Scenario | Coverage | Bugs |
|----------|----------|------|
| v11 baseline | 36% | 12/33 |
| + XREF-001 | 45% | 15/33 |
| + API-004 | 52% | 17/33 |
| + E2E directives (conservative) | 67% | 22/33 |
| + E2E directives (optimistic) | **76%** | **25/33** |
| Hard ceiling | ~76% | ~25/33 |

### The 8 Permanently Uncatchable Bugs (24%)
| Fix | Bug | Why |
|-----|-----|-----|
| 4 | Docker internal hostname in URLs | Infrastructure deployment topology |
| 6 | PrimeNG TabMenu misuse | Framework-specific expertise |
| 12 | DraftAnswer semantic meaning | Domain vocabulary error |
| 13 | State machine lifecycle mismatch | Domain model knowledge |
| 19 | Import BOQ calls wrong function | Developer intent understanding |
| 21 | Data key priority (letter vs header) | Subtle data transformation logic |
| 24 | Wrong role in [Authorize] | Business authorization rules |
| 26 | Component built but never routed | Dead code detection at unacceptable FP |

---

## Phase 1: Architecture Discovery (Agent 1 — gap-architect)

Read ONLY. Do NOT modify any files. Discover and record:

### 1A. Read these files completely:
- `src/agent_team/quality_checks.py` — find `run_api_contract_scan()` (expect ~line 3281), `_parse_svc_table()`, `_parse_field_schema()`, `_check_backend_fields()`, `_check_frontend_extra_fields()`
- `src/agent_team/e2e_testing.py` — find `BACKEND_E2E_PROMPT` (expect ~line 556), closing `[ORIGINAL USER REQUEST]` tag (expect ~line 715), `FRONTEND_E2E_PROMPT` (expect ~line 718), closing tag (expect ~line 843)
- `src/agent_team/browser_testing.py` — find `BROWSER_WORKFLOW_EXECUTOR_PROMPT` (expect ~line 1071), `ANTI-CHEAT RULES` section (expect ~line 1145), `BROWSER_REGRESSION_SWEEP_PROMPT` (expect ~line 1227), `## Output` section (expect ~line 1250)
- `src/agent_team/agents.py` — find `EXACT FIELD SCHEMAS` (expect ~line 936), `API CONTRACT COMPLIANCE` (expect ~line 1039), `API Contract Field Verification` (expect ~line 1268)
- `src/agent_team/config.py` — find `PostOrchestrationScanConfig` (expect ~line 294), `apply_depth_quality_gating()`, `_dict_to_config()`
- `src/agent_team/cli.py` — find SDL scan block (expect ~line 5011), E2E Testing Phase comment (expect ~line 5059), `_run_silent_data_loss_fix()` (expect ~line 1598)
- `src/agent_team/code_quality_standards.py` — find `_AGENT_STANDARDS_MAP` (expect ~line 631)
- `src/agent_team/display.py` — find `type_hints` dict

### 1B. Record the EXACT line numbers for each injection point:
Write a file `.agent-team/v12_architecture.md` with the exact line numbers found for each point above.

### 1C. Verify these patterns exist (from v11):
- `Violation` namedtuple/dataclass import in quality_checks.py
- `ScanScope` usage in scan functions
- `_MAX_VIOLATIONS` constant
- `print_info`, `print_warning` imports in cli.py
- `asyncio.run()` pattern for fix functions in cli.py

### 1D. Identify frontend HTTP call patterns in any test fixtures or existing regex patterns in quality_checks.py that may be reusable.

### 1E. Pass ALL discovered line numbers and patterns to Agent 2 via the architecture file.

---

## Phase 2: Implementation (Agent 2 — implementer)

Read the architecture file from Phase 1. Implement sections 2.1 through 2.11 IN ORDER.

---

### 2.1 XREF-001 Scan — `quality_checks.py` (~280 lines)

Add AFTER `run_silent_data_loss_scan()` function (end of file or after last scan function). Create these components:

#### 2.1.1 Data structures

```python
# Reuse existing Violation. Add these lightweight containers:
_FrontendCall = collections.namedtuple("_FrontendCall", ["method", "path", "file", "line"])
_BackendRoute = collections.namedtuple("_BackendRoute", ["method", "path", "file", "line"])
```

#### 2.1.2 `_normalize_api_path(path: str) -> str`

```python
def _normalize_api_path(path: str) -> str:
    """Normalize an API path for comparison.

    - Strip leading/trailing slashes
    - Replace path parameters ({id}, :id, <id>, <int:id>) with {_}
    - Lowercase
    - Strip common /api/ or /api/v1/ prefix
    """
    path = path.strip("/").lower()
    # Replace parameterized segments
    path = re.sub(r"\{[^}]+\}", "{_}", path)      # {id}, {userId}
    path = re.sub(r":(\w+)", "{_}", path)           # :id, :userId
    path = re.sub(r"<(?:\w+:)?(\w+)>", "{_}", path) # <id>, <int:id>
    # Strip common API prefixes
    path = re.sub(r"^api/(v\d+/)?", "", path)
    return path.strip("/")
```

#### 2.1.3 `_extract_frontend_http_calls(project_root: Path, scope: ScanScope | None) -> list[_FrontendCall]`

Scan `.ts`, `.js`, `.tsx`, `.jsx` files (excluding node_modules, dist, build, .spec, .test).

**Regex patterns to extract:**

```python
# Angular HttpClient: this.http.get<Type>('/api/path')
_RE_ANGULAR_HTTP = re.compile(
    r"this\.http\.(get|post|put|delete|patch)\s*(?:<[^>]*>)?\s*\(\s*[`'\"]([^`'\"]+)[`'\"]",
    re.IGNORECASE,
)

# Axios: axios.get('/api/path'), api.get('/api/path'), this.api.get(...)
_RE_AXIOS = re.compile(
    r"(?:axios|api|this\.\w+)\.(get|post|put|delete|patch)\s*\(\s*[`'\"]([^`'\"]+)[`'\"]",
    re.IGNORECASE,
)

# fetch(): fetch('/api/path', { method: 'POST' }) or fetch('/api/path')
_RE_FETCH = re.compile(
    r"fetch\s*\(\s*[`'\"]([^`'\"]+)[`'\"]",
    re.IGNORECASE,
)
# For fetch, default method is GET unless { method: 'POST' } follows
```

**Skip rules:**
- Skip if URL starts with `http://` or `https://` (external URL) UNLESS it contains `localhost` or `127.0.0.1`
- Skip if URL contains `${` with nested expressions (complex template literal — too risky to parse)
- Skip files in `node_modules/`, `dist/`, `build/`, `.spec.`, `.test.`, `e2e/`, `__tests__/`
- Extract: strip base URL portion (everything before `/api/` or first `/` after domain)

**Scope filtering:** If `scope` is provided and `scope.changed_files` is not None, only scan files in scope. BUT always collect ALL calls for cross-reference accuracy (same pattern as DB scan scope handling from v6 review).

#### 2.1.4 `_extract_backend_routes_dotnet(project_root: Path, scope: ScanScope | None) -> list[_BackendRoute]`

Scan `.cs` files in directories containing `Controllers` or `Endpoints`.

```python
# Class-level route: [Route("api/[controller]")] or [Route("api/v1/[controller]")]
_RE_DOTNET_ROUTE = re.compile(
    r'\[Route\(\s*"([^"]+)"\s*\)\]',
)

# Controller class name: public class FooController
_RE_DOTNET_CONTROLLER = re.compile(
    r"class\s+(\w+)Controller\b",
)

# Method-level HTTP attribute: [HttpGet], [HttpGet("path")], [HttpPost("{id}")]
_RE_DOTNET_HTTP_METHOD = re.compile(
    r'\[Http(Get|Post|Put|Delete|Patch)(?:\(\s*"([^"]*)"\s*\))?\]',
    re.IGNORECASE,
)
```

**Route assembly logic:**
1. Parse class-level `[Route]` → replace `[controller]` with lowercase controller name
2. Parse method-level `[Http*]` → combine base + method path
3. Handle: `[HttpGet]` with no path = just the base route
4. Handle: `[HttpGet("{id}")]` = base + "/{id}"

#### 2.1.5 `_extract_backend_routes_express(project_root: Path, scope: ScanScope | None) -> list[_BackendRoute]`

Scan `.ts`, `.js` files in directories containing `routes`, `controllers`, `api`.

```python
# router.get('/path', handler) or app.post('/path', handler)
_RE_EXPRESS_ROUTE = re.compile(
    r"(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# app.use('/prefix', router) — for route mounting
_RE_EXPRESS_MOUNT = re.compile(
    r"(?:app|router)\.use\s*\(\s*['\"]([^'\"]+)['\"]",
)
```

**NOTE:** Express route mounting (`app.use('/api/users', userRouter)`) requires tracing the mount prefix. This is BEST-EFFORT — if we can find the mount in the same file or a clear `index.ts`/`app.ts`, use it. Otherwise, scan routes as-is. Do NOT over-engineer this.

#### 2.1.6 `_extract_backend_routes_python(project_root: Path, scope: ScanScope | None) -> list[_BackendRoute]`

Scan `.py` files (excluding tests, migrations, venv).

```python
# Flask: @app.route('/path', methods=['GET', 'POST'])
_RE_FLASK_ROUTE = re.compile(
    r"@(?:app|blueprint|bp)\.(route|get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# FastAPI: @app.get('/path'), @router.post('/path')
_RE_FASTAPI_ROUTE = re.compile(
    r"@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# Django: path('api/path', view) — basic detection
_RE_DJANGO_PATH = re.compile(
    r"path\s*\(\s*['\"]([^'\"]+)['\"]",
)
```

#### 2.1.7 `_check_endpoint_xref(frontend_calls: list[_FrontendCall], backend_routes: list[_BackendRoute]) -> list[Violation]`

**3-level matching algorithm:**

```python
def _check_endpoint_xref(frontend_calls, backend_routes):
    violations = []

    # Build normalized backend route set
    backend_exact = set()  # (method, normalized_path)
    backend_paths = set()  # normalized_path only (for method-agnostic)
    for route in backend_routes:
        norm = _normalize_api_path(route.path)
        backend_exact.add((route.method.upper(), norm))
        backend_paths.add(norm)

    for call in frontend_calls:
        norm = _normalize_api_path(call.path)
        method = call.method.upper() if call.method else "GET"

        # Level 1: Exact match (method + path)
        if (method, norm) in backend_exact:
            continue

        # Level 2: Method-agnostic (path exists, wrong method)
        if norm in backend_paths:
            # XREF-002 warning: method mismatch
            violations.append(Violation(
                check="XREF-002",
                file_path=call.file,
                line=call.line,
                message=f"Frontend calls {method} /{call.path} but backend only has different HTTP method for this route",
                severity="warning",
            ))
            continue

        # Level 3: No match at all
        violations.append(Violation(
            check="XREF-001",
            file_path=call.file,
            line=call.line,
            message=f"Frontend calls {method} /{call.path} but no matching backend endpoint exists",
            severity="error",
        ))

    # Cap and sort
    violations.sort(key=lambda v: (v.severity != "error", v.file_path, v.line))
    return violations[:_MAX_VIOLATIONS]
```

#### 2.1.8 `run_endpoint_xref_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]`

```python
def run_endpoint_xref_scan(
    project_root: Path,
    scope: ScanScope | None = None,
) -> list[Violation]:
    """Cross-reference frontend HTTP calls against backend route definitions.

    Detects:
      XREF-001: Frontend calls an endpoint that has no backend route (error)
      XREF-002: Frontend calls with wrong HTTP method (warning)
    """
    frontend_calls = _extract_frontend_http_calls(project_root, scope)

    # Auto-detect backend framework and extract routes
    backend_routes: list[_BackendRoute] = []

    # Check for .NET
    if list(project_root.rglob("*.csproj")):
        backend_routes.extend(_extract_backend_routes_dotnet(project_root, scope))

    # Check for Express/Node
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        backend_routes.extend(_extract_backend_routes_express(project_root, scope))

    # Check for Python
    if list(project_root.rglob("requirements.txt")) or list(project_root.rglob("pyproject.toml")):
        backend_routes.extend(_extract_backend_routes_python(project_root, scope))

    if not frontend_calls or not backend_routes:
        return []  # Cannot cross-reference without both sides

    return _check_endpoint_xref(frontend_calls, backend_routes)
```

---

### 2.2 API-004 — Write-Side Field Passthrough — `quality_checks.py` (~125 lines)

Add INSIDE `run_api_contract_scan()` function. Integrate as an additional check alongside existing API-001, API-002, API-003, ENUM-004.

#### 2.2.1 `_extract_csharp_class_properties(file_content: str, class_name: str) -> set[str]`

```python
def _extract_csharp_class_properties(file_content: str, class_name: str) -> set[str]:
    """Extract public property names from a C# class or record."""
    props: set[str] = set()

    # Find class/record body
    # Pattern: class ClassName ... { ... }
    class_pattern = re.compile(
        rf"(?:class|record)\s+{re.escape(class_name)}\b[^{{]*\{{",
        re.IGNORECASE,
    )
    match = class_pattern.search(file_content)
    if not match:
        return props

    # Extract properties from class body
    start = match.end()
    brace_depth = 1
    i = start
    while i < len(file_content) and brace_depth > 0:
        if file_content[i] == "{":
            brace_depth += 1
        elif file_content[i] == "}":
            brace_depth -= 1
        i += 1

    class_body = file_content[start:i]

    # Public properties: public Type Name { get; set; }
    for m in re.finditer(r"public\s+[\w<>\[\]?]+\s+(\w+)\s*\{", class_body):
        props.add(m.group(1).lower())

    # Record positional params: record Foo(string Bar, int Baz)
    record_match = re.search(
        rf"record\s+{re.escape(class_name)}\s*\(([^)]+)\)",
        file_content,
    )
    if record_match:
        for param in record_match.group(1).split(","):
            parts = param.strip().split()
            if len(parts) >= 2:
                props.add(parts[-1].lower())

    return props
```

#### 2.2.2 `_check_request_field_passthrough(svc_contracts, project_root, scope) -> list[Violation]`

```python
def _check_request_field_passthrough(
    svc_contracts: list,  # list[SvcContract] from existing _parse_svc_table
    project_root: Path,
    scope: ScanScope | None,
) -> list[Violation]:
    """API-004: Check if frontend sends fields that backend command ignores.

    For each SVC-xxx row with request_fields, find the corresponding
    backend Command class and verify it has properties for all fields.
    """
    violations: list[Violation] = []

    for svc in svc_contracts:
        # Only check rows that have explicit request field schemas
        if not svc.request_fields:
            continue

        # Find the Command/DTO class file
        # Pattern: the request_dto_name is usually like "CreateFooCommand" or "UpdateBarRequest"
        if not svc.request_dto_name:
            continue

        # Search for the class in .cs files
        target_class = svc.request_dto_name
        found = False
        for cs_file in project_root.rglob("*.cs"):
            if _should_skip_file(cs_file):
                continue
            try:
                content = cs_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            if f"class {target_class}" in content or f"record {target_class}" in content:
                props = _extract_csharp_class_properties(content, target_class)
                found = True

                for field_name in svc.request_fields:
                    if field_name.lower() not in props:
                        # Check if field appears ANYWHERE in corresponding handler
                        handler_name = target_class.replace("Command", "CommandHandler").replace("Request", "RequestHandler")
                        handler_has_field = False
                        for h_file in project_root.rglob("*.cs"):
                            if handler_name in h_file.name:
                                try:
                                    h_content = h_file.read_text(encoding="utf-8", errors="ignore")
                                    if re.search(rf"\b{re.escape(field_name)}\b", h_content, re.IGNORECASE):
                                        handler_has_field = True
                                except OSError:
                                    pass
                                break

                        if not handler_has_field:
                            violations.append(Violation(
                                check="API-004",
                                file_path=str(cs_file.relative_to(project_root)),
                                line=0,
                                message=f"Frontend sends field '{field_name}' but {target_class} has no matching property — field may be silently dropped",
                                severity="warning",
                            ))
                break  # Found the class file

    return violations
```

#### 2.2.3 Integration point

Inside `run_api_contract_scan()`, AFTER the existing `_check_frontend_extra_fields()` call, add:

```python
    # API-004: Write-side field passthrough check
    violations.extend(_check_request_field_passthrough(svc_contracts, project_root, scope))
```

Also update the docstring of `run_api_contract_scan()` to mention API-004.

**NOTE:** `SvcContract` dataclass needs a `request_fields` attribute AND a `request_dto_name` attribute. Check if `_parse_svc_table()` already extracts request DTO info. If yes, extend it. If not, add parsing for the Request DTO column using the same `_parse_field_schema()` function.

---

### 2.3 E2E Backend Directives — `e2e_testing.py` (~15 lines)

Insert AFTER the Mutation Verification Rule block (after line ~713, BEFORE the `[ORIGINAL USER REQUEST]` closing tag at line ~715).

```python
### Endpoint Exhaustiveness Rule
Before writing tests, list ALL controller/router endpoints in the project (method + route path).
For EACH endpoint, generate at least ONE test case. At the end of the test file, add a comment
block listing all endpoints and their test coverage status (TESTED / UNTESTED / SKIPPED with reason).
An endpoint with zero tests = coverage gap that MUST be justified.

### Role Authorization Rule
For endpoints with authorization decorators ([Authorize], @auth_required, middleware guards),
test with BOTH an authorized role AND an unauthorized/wrong role:
  - Correct role → expect 200/201/204
  - Wrong role → expect 403 Forbidden (NOT 500)
  - No token → expect 401 Unauthorized (NOT 500)
If the system has 2+ roles, test at least 2 distinct roles across the test suite.
```

---

### 2.4 E2E Frontend Directives — `e2e_testing.py` (~25 lines)

Insert AFTER the Mutation Verification Rule block in FRONTEND_E2E_PROMPT (after line ~840, BEFORE the `[ORIGINAL USER REQUEST]` closing tag at line ~843).

```python
### State Persistence Rule
After every write operation (form submission, entity creation, status change), REFRESH the page
(navigate away and navigate back, or call page.reload()). Verify the data persists correctly
after refresh. Data that appears in UI but vanishes on refresh = BUG (the backend didn't save it).

### Revisit Testing Rule
After creating or submitting an entity, navigate to a DIFFERENT page (e.g., dashboard or list),
then navigate BACK to the entity's detail/edit page. Verify it shows the CORRECT state:
  - Data is populated (not an empty form)
  - Status reflects the latest action (not "Draft" after submission)
  - Related data is loaded (comments, attachments, sub-items)

### Dropdown Verification Rule
For every dropdown/select element encountered during testing, verify it has REAL populated options
(not empty, not just a single placeholder like "Select..."). Click the dropdown and check the
option count. A dropdown that should show data but is empty = BUG (API not called or returns empty).

### Button Outcome Verification Rule
Every button click MUST produce a verifiable outcome BEYOND a toast/snackbar message:
  - Create button → verify new item appears in list/table
  - Save button → refresh page and verify data persists
  - Delete button → verify item removed from list
  - Submit button → verify status changes
A button that shows a toast but creates NO data change and NO navigation = potential STUB.
```

---

### 2.5 Browser Executor Directives — `browser_testing.py` (~25 lines)

Insert in `BROWSER_WORKFLOW_EXECUTOR_PROMPT` BEFORE the `## ANTI-CHEAT RULES` section (before line ~1145).

```python
## DEEP VERIFICATION RULES

### State Persistence Check
After completing any step that creates or modifies data (form submission, button click that
should save), navigate away from the current page and navigate back. Take a screenshot BEFORE
and AFTER to prove the data persisted. If data disappears after navigation = FAILURE.

### Revisit Check
After completing a multi-step workflow, go back to the starting page. Verify the entity/record
created during the workflow is visible and shows the correct final state. If the entity is
missing or shows wrong state = FAILURE.

### Dropdown Check
When a workflow step involves a dropdown/select, verify it has populated options before selecting.
If the dropdown is empty when it should have data = FAILURE. Screenshot the dropdown in open state.

### Button Outcome Check
When clicking any action button, verify the result goes BEYOND a toast notification. After the
toast disappears, check: did data actually change? Did navigation occur? Did a dialog open with
real content? A button that only produces a toast with no other observable effect = FAILURE.
```

---

### 2.6 Browser Regression Directive — `browser_testing.py` (~8 lines)

Insert in `BROWSER_REGRESSION_SWEEP_PROMPT` BEFORE the `## Output` section (before line ~1250).

```python
## Content Verification
For each page, verify it is not just loading but has MEANINGFUL content:
  - Tables should have at least one data row (not just headers)
  - Lists should have at least one item
  - Forms should have populated fields or labels
  - Dashboards should have at least one card/widget with data
A page that loads but shows only empty containers or "No data" when data should exist = REGRESSED.
```

---

### 2.7 Architect Prompt Injection — `agents.py` (~12 lines)

Insert AFTER the existing `### EXACT FIELD SCHEMAS IN SVC-xxx TABLE` block (after line ~960, within ARCHITECT_PROMPT).

```python
### ENDPOINT COMPLETENESS VERIFICATION (MANDATORY)
For EVERY SVC-xxx row in the wiring table:
  - The backend controller MUST have an action method for the specified HTTP method + route
  - The frontend service MUST have a method that calls this endpoint
  - If either side is missing, flag it as INCOMPLETE in the architecture review
  - Cross-reference: count of frontend service methods calling APIs should MATCH count of backend endpoints
  - Any frontend service method calling an API path that has no backend controller action = ARCHITECTURE BUG
```

---

### 2.8 Code Reviewer Prompt Injection — `agents.py` (~12 lines)

Insert AFTER the existing `## API Contract Field Verification` block (after line ~1290, within CODE_REVIEWER_PROMPT).

```python
## Endpoint Cross-Reference Verification
After verifying field-level contracts, verify ENDPOINT-LEVEL completeness:
  - XREF-001: For each frontend HTTP call, verify a matching backend endpoint EXISTS
  - XREF-002: Verify the HTTP METHOD matches (GET vs POST vs PUT)
  - API-004: For each field the frontend SENDS in POST/PUT requests, verify the backend
    Command/DTO class has a matching property. Fields sent by frontend but missing from
    backend = silently dropped data.
Flag any frontend→backend call where the backend endpoint or field does not exist.
```

---

### 2.9 Config + Standards — `config.py` + `code_quality_standards.py` (~25 lines)

#### 2.9.1 `config.py` — PostOrchestrationScanConfig

Add field at line ~305 (after `silent_data_loss_scan`):

```python
    endpoint_xref_scan: bool = True   # XREF-001 frontend-backend endpoint cross-reference
```

#### 2.9.2 `config.py` — `apply_depth_quality_gating()`

In the `if depth == "quick":` block, add:

```python
        config.post_orchestration_scans.endpoint_xref_scan = False
```

#### 2.9.3 `config.py` — `_dict_to_config()`

In the PostOrchestrationScanConfig parsing section, add:

```python
        if "endpoint_xref_scan" in pos_raw:
            pos_cfg.endpoint_xref_scan = bool(pos_raw["endpoint_xref_scan"])
            user_overrides.add("post_orchestration_scans.endpoint_xref_scan")
```

#### 2.9.4 `code_quality_standards.py` — New constant

Add AFTER `SILENT_DATA_LOSS_STANDARDS`:

```python
ENDPOINT_XREF_STANDARDS = r"""
## Endpoint Cross-Reference Standards

### XREF-001: Missing Backend Endpoint
Frontend code calls an API endpoint that has no matching backend controller action or route handler.
The endpoint must be created in the backend before the frontend can function correctly.

### XREF-002: HTTP Method Mismatch
Frontend calls an endpoint with a different HTTP method than what the backend defines.
Verify the frontend uses the correct method (GET vs POST vs PUT vs DELETE).

### API-004: Write-Side Field Dropped
Frontend sends a field in a POST/PUT request body that the backend Command/DTO class does not
have as a property. The field is silently ignored. Either add the property to the backend
or remove the field from the frontend form.
"""
```

#### 2.9.5 `code_quality_standards.py` — `_AGENT_STANDARDS_MAP`

Add `ENDPOINT_XREF_STANDARDS` to the code-writer and architect lists:

```python
    "code-writer": [...existing..., ENDPOINT_XREF_STANDARDS],
    "architect": [...existing..., ENDPOINT_XREF_STANDARDS],
```

---

### 2.10 CLI Wiring — `cli.py` (~50 lines)

#### 2.10.1 XREF Scan Block

Insert AFTER the SDL scan block (after line ~5057) and BEFORE the E2E Testing Phase comment (line ~5059):

```python
    # -------------------------------------------------------------------
    # Post-orchestration: Endpoint Cross-Reference scan (XREF-001)
    # -------------------------------------------------------------------
    if config.post_orchestration_scans.endpoint_xref_scan:
        try:
            from .quality_checks import run_endpoint_xref_scan as _run_xref_scan

            for _fix_pass in range(max_fix_passes):
                xref_violations = _run_xref_scan(Path(cwd), scope=scan_scope)
                if xref_violations:
                    xref_errors = [v for v in xref_violations if v.severity == "error"]
                    xref_warnings = [v for v in xref_violations if v.severity == "warning"]
                    print_warning(
                        f"Endpoint cross-reference: {len(xref_errors)} errors, "
                        f"{len(xref_warnings)} warnings"
                    )
                    for v in xref_violations[:10]:
                        print_warning(f"  [{v.check}] {v.file_path}:{v.line} — {v.message}")

                    if xref_errors and max_fix_passes > 1:
                        try:
                            xref_fix_cost = asyncio.run(_run_endpoint_xref_fix(
                                cwd=cwd,
                                config=config,
                                xref_violations=xref_errors,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += xref_fix_cost
                        except Exception as exc:
                            print_warning(f"XREF fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode or no errors
                else:
                    if _fix_pass == 0:
                        print_info("Endpoint cross-reference: 0 violations (clean)")
                    else:
                        print_info(f"XREF scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Endpoint cross-reference scan failed: {exc}")
```

---

### 2.11 Fix Function — `cli.py` (~30 lines)

Add `_run_endpoint_xref_fix()` near the other fix functions (after `_run_silent_data_loss_fix`, around line ~1650).

```python
async def _run_endpoint_xref_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    xref_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix endpoint cross-reference violations (XREF-001).

    Creates missing backend endpoints based on frontend HTTP calls.
    """
    if not xref_violations:
        return 0.0

    print_info(f"Running XREF fix pass ({len(xref_violations)} violations)")

    violation_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in xref_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: ENDPOINT CROSS-REFERENCE FIX]\n\n"
        f"The following frontend-backend endpoint mismatches were detected:\n\n"
        f"Violations found:\n{violation_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For XREF-001 (missing backend endpoint):\n"
        f"   - Create the missing controller action/route handler\n"
        f"   - Follow existing controller patterns in the project\n"
        f"   - Include proper authorization attributes matching similar endpoints\n"
        f"   - Return appropriate DTOs (check what the frontend expects)\n"
        f"2. For XREF-002 (wrong HTTP method):\n"
        f"   - Verify which side is wrong (frontend or backend)\n"
        f"   - Fix the side that deviates from the API contract\n"
    )

    # Use same sub-orchestrator pattern as _run_silent_data_loss_fix
    from .orchestrator import run_orchestrator
    cost = await run_orchestrator(
        task=fix_prompt,
        cwd=cwd,
        config=config,
        original_task=task_text,
        constraints=constraints,
        intervention=intervention,
        depth=depth,
    )
    return cost
```

#### 2.11.1 `display.py`

Add to `type_hints` dict:

```python
    "endpoint_xref_fix": "Fixing missing backend endpoints (XREF-001)",
```

---

## Phase 3: Tests (Agent 3 — test-engineer)

Create `tests/test_v12_hard_ceiling.py` with ~70 tests across 8 test classes.

### 3.1 TestNormalizeApiPath (6 tests)
```
- test_strips_slashes_and_lowercases
- test_replaces_braces_params
- test_replaces_colon_params
- test_replaces_angle_params
- test_strips_api_prefix
- test_strips_api_v1_prefix
```

### 3.2 TestFrontendHttpExtraction (10 tests)
```
- test_angular_http_client_get
- test_angular_http_client_post_put_delete
- test_axios_get_post
- test_fetch_default_get
- test_skips_external_urls
- test_skips_localhost_external (does NOT skip)
- test_skips_complex_template_literals
- test_skips_node_modules
- test_skips_test_files
- test_scope_filtering
```

### 3.3 TestBackendRouteExtraction (12 tests)
```
- test_dotnet_basic_controller
- test_dotnet_route_with_controller_placeholder
- test_dotnet_http_method_with_path
- test_dotnet_http_method_without_path
- test_express_router_get_post
- test_express_app_use_mounting
- test_flask_route_decorator
- test_fastapi_router_decorator
- test_django_path
- test_auto_detect_dotnet
- test_auto_detect_express
- test_auto_detect_python
```

### 3.4 TestEndpointXref (10 tests)
```
- test_exact_match_no_violation
- test_method_agnostic_xref002_warning
- test_no_match_xref001_error
- test_parameterized_paths_match
- test_mixed_violations_sorted
- test_cap_at_max_violations
- test_empty_frontend_no_violations
- test_empty_backend_no_violations
- test_normalized_comparison
- test_api_prefix_stripped_both_sides
```

### 3.5 TestApi004WriteFields (8 tests)
```
- test_csharp_property_extraction_basic
- test_csharp_record_param_extraction
- test_request_field_missing_from_command (API-004 violation)
- test_request_field_present_in_command (no violation)
- test_field_in_handler_not_command (no violation — handler uses it)
- test_case_insensitive_matching
- test_no_request_fields_skipped
- test_integrated_in_api_contract_scan
```

### 3.6 TestConfigWiring (8 tests)
```
- test_endpoint_xref_scan_field_exists
- test_endpoint_xref_scan_defaults_true
- test_quick_depth_disables_xref
- test_standard_depth_keeps_xref
- test_dict_to_config_parses_xref
- test_user_overrides_tracks_xref
- test_endpoint_xref_standards_exists
- test_standards_mapped_to_agents
```

### 3.7 TestPromptDirectives (8 tests)
```
- test_backend_e2e_has_endpoint_exhaustiveness
- test_backend_e2e_has_role_authorization
- test_frontend_e2e_has_state_persistence
- test_frontend_e2e_has_revisit_testing
- test_frontend_e2e_has_dropdown_verification
- test_frontend_e2e_has_button_outcome
- test_browser_executor_has_deep_verification
- test_browser_regression_has_content_verification
```

### 3.8 TestCLIWiring (8 tests)
```
- test_xref_scan_block_in_cli (grep for "Endpoint Cross-Reference")
- test_xref_scan_after_sdl_before_e2e (pipeline order)
- test_fix_function_signature
- test_fix_function_has_crash_isolation
- test_config_gating_works
- test_display_type_hint_exists
- test_architect_prompt_has_endpoint_completeness
- test_reviewer_prompt_has_xref_verification
```

### 3.9 Run Full Test Suite
```bash
python -m pytest tests/ -x -q
```

Verify: 0 new regressions, all v12 tests pass, total count increases by ~70.

---

## Phase 4: Final Report

Write `V12_HARD_CEILING_REPORT.md` with:

```markdown
# v12.0 Hard Ceiling — Implementation Report

## Implementation Summary
- New scans: 1 (XREF-001/002 endpoint cross-reference)
- Enhanced scans: 1 (API-004 write-side fields in run_api_contract_scan)
- E2E directives added: 6 (2 backend + 4 frontend)
- Browser directives added: 5 (4 executor + 1 regression)
- Prompt injections: 2 (architect endpoint completeness + reviewer XREF verification)
- Config fields added: 1 (endpoint_xref_scan)
- Recovery types added: 1 (endpoint_xref_fix)
- Quality standards added: 1 (ENDPOINT_XREF_STANDARDS)
- Files modified: 8
- Total insertions: ~610 lines (source) + ~500 lines (tests)

## Bug Coverage Matrix (All 33 Bayan Bugs)
[Table showing each bug, mechanism that catches it, confidence level]

## Test Results
- New tests: ~70 (in tests/test_v12_hard_ceiling.py)
- Full suite: [total] passed, [pre-existing] failed, 0 new regressions

## Coverage Achievement
- v11 baseline: 36% (12/33)
- v12 deterministic: 52% (17/33) — +5 bugs via XREF-001 + API-004
- v12 with E2E directives: 67-76% (22-25/33)
- Hard ceiling reached: ~76% (25/33)
```

---

## Execution Rules

1. **Agent 1 (gap-architect)** reads files ONLY. It must NOT modify any source files. Its ONLY output is `.agent-team/v12_architecture.md` with verified line numbers.

2. **Agent 2 (implementer)** implements ALL sections 2.1-2.11 in a SINGLE pass. Do NOT split into sub-tasks. Implement in the order listed.

3. **Agent 3 (test-engineer)** creates the test file, runs the full suite, and writes the final report.

4. **ZERO tolerance for placeholder code.** Every function must be fully implemented with real regex patterns and real logic. No `pass`, no `TODO`, no `NotImplementedError`.

5. **Follow existing patterns EXACTLY.** The SDL scan block (cli.py ~L5011-5056) is the template for the XREF scan block. The `_run_silent_data_loss_fix()` function is the template for `_run_endpoint_xref_fix()`. Copy structure, adapt content.

6. **Crash isolation is MANDATORY.** Every scan block in cli.py must be in its own `try/except Exception`. Every fix call must be in its own `try/except`.

7. **ScanScope support is MANDATORY.** All new scan functions must accept `scope: ScanScope | None = None` and filter files when scope is provided. Follow the v6 pattern: collect from ALL files, but report violations only for scoped files.

8. **Do NOT modify existing test files.** Create a NEW test file `tests/test_v12_hard_ceiling.py`.

9. **Do NOT modify `run_api_contract_scan()`'s public signature.** API-004 is added internally via a new helper function called inside the existing function.

10. **The `_parse_svc_table()` function needs `request_fields` and `request_dto_name` data.** Check if `SvcContract` already has these. If not, extend the parsing to extract Request DTO column data using the same `_parse_field_schema()` approach.

11. **Prompt directives must be inserted BEFORE closing tags.** In e2e_testing.py, directives go BEFORE `[ORIGINAL USER REQUEST]\n{task_text}"""`. In browser_testing.py, directives go BEFORE the `## ANTI-CHEAT RULES` or `## Output` sections.

12. **All regex patterns must be compiled at module level** (not inside functions). Use the `_RE_` prefix convention from existing code.

13. **Import the `Violation` class correctly.** Check how other functions in quality_checks.py create Violation instances and follow the same pattern.

14. **Windows compatibility.** Use `Path` objects, not string concatenation. Use `encoding="utf-8"` on all file reads. Use `errors="ignore"` for source files that may have encoding issues.

15. **The XREF scan runs AFTER SDL scan and BEFORE E2E Testing Phase.** This order is critical: fix missing endpoints first, then E2E tests can exercise them.

16. **Test the full pipeline order** in test class TestCLIWiring by reading cli.py source and verifying the comment markers appear in the correct order.

---

## Appendix: Complete 33-Bug Coverage Projection

| Fix | Bug | v11 Status | v12 Mechanism | v12 Confidence |
|-----|-----|-----------|---------------|----------------|
| 1 | Bidders not qualified after invitation | NOT CAUGHT | E2E Revisit Testing directive | 60% |
| 2 | Property name mismatch (PortalDocumentDto) | API-002 (conditional) | API-002 (unchanged) | 70% |
| 3 | Download URL missing tenderId | TypeScript compiler | (unchanged) | 90% |
| 4 | Presigned URL Docker hostname | **UNCATCHABLE** | — | 0% |
| 5 | doc.url build error | TypeScript compiler | (unchanged) | 95% |
| 6 | PrimeNG TabMenu misuse | **UNCATCHABLE** | — | 0% |
| 7 | BOQ sections endpoint missing | NOT CAUGHT | **XREF-001 scan** | **95%** |
| 8 | Enum integer serialization | ENUM-004 | (unchanged) | 95% |
| 9 | Questions disappear on refresh | NOT CAUGHT | E2E State Persistence directive | 65% |
| 10 | relatedBoqSection field mismatch | API-002 (conditional) | API-002 (unchanged) | 70% |
| 11 | Admin enum integers | ENUM-004 | (unchanged) | 95% |
| 12 | DraftAnswer semantic meaning | **UNCATCHABLE** | — | 0% |
| 13 | State machine lifecycle mismatch | **UNCATCHABLE** | — | 0% |
| 14 | Portal bulletins crash | API-002 bidirectional | (unchanged) | 80% |
| 15 | Bid receipt missing fields | API-002 | (unchanged) | 75% |
| 16 | Bid status endpoint missing | NOT CAUGHT | **XREF-001 scan** | **95%** |
| 17 | No "Back to Your Tenders" navigation | NOT CAUGHT | Browser Revisit Check | 40% |
| 18 | Tender card missing HasSubmittedBid | API-002 | (unchanged) | 75% |
| 19 | Import BOQ calls wrong function | **UNCATCHABLE** | — | 0% |
| 20 | Parse button silently fails | SDL-003 reviewer | (unchanged) | 50% |
| 21 | Preview rows key priority | **UNCATCHABLE** | — | 0% |
| 22 | CQRS handler no persistence | SDL-001 | (unchanged) | 90% |
| 23 | Frontend ignores API response | SDL-002 reviewer | (unchanged) | 60% |
| 24 | 403 wrong role in [Authorize] | **UNCATCHABLE** | — | 0% |
| 25 | Evaluation setup not found | NOT CAUGHT | E2E State Persistence + Revisit | 55% |
| 26 | Component built but not routed | **UNCATCHABLE** | — | 0% |
| 27 | loadComments() never called | NOT CAUGHT | E2E Button Outcome directive | 65% |
| 28 | Combined Scorecard empty | NOT CAUGHT | E2E Button Outcome directive | 50% |
| 29 | .toLowerCase() on integer enum | ENUM-004 | (unchanged) | 95% |
| 30 | Empty approver array | NOT CAUGHT | E2E Dropdown Verification | 70% |
| 31 | Backend ignores password | NOT CAUGHT | **API-004 scan** | **85%** |
| 32 | Delete user endpoint missing | NOT CAUGHT | **XREF-001 scan** | **95%** |
| 33 | 204 No Content handling | NOT CAUGHT | E2E State Persistence | 45% |
| 34 | NDA field not in backend entity | NOT CAUGHT | **API-004 scan** | **85%** |
| 35 | Client 6 fields missing | API-001 (conditional) | API-001 (unchanged) | 70% |
| 36 | View Details only shows toast | NOT CAUGHT | E2E Button Outcome directive | 70% |

### Summary by Confidence Tier
| Tier | Bugs | Coverage |
|------|------|----------|
| HIGH (>80%) — Deterministic scans | Fix 7, 8, 11, 16, 22, 29, 31, 32, 34 | 9 bugs |
| MEDIUM-HIGH (60-80%) — API-002 + E2E directives | Fix 1, 2, 9, 10, 14, 15, 18, 23, 27, 30, 35, 36 | 12 bugs |
| MEDIUM (40-60%) — Reviewer prompts + E2E probabilistic | Fix 17, 20, 25, 28, 33 | 5 bugs |
| CAUGHT BY COMPILER | Fix 3, 5 | 2 bugs |
| UNCATCHABLE | Fix 4, 6, 12, 13, 19, 21, 24, 26 | 8 bugs |

**Conservative (HIGH + MEDIUM-HIGH + compiler): 23/33 = 70%**
**Target (+ half of MEDIUM): 25/33 = 76%**
**Hard ceiling: 25/33 = 76%**
