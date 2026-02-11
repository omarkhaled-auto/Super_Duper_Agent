"""Browser MCP interactive testing for visual production verification.

Generates deterministic workflow definitions from existing artifacts,
provides prompt constants for Playwright MCP sub-orchestrator agents,
and implements structural verification to prevent false passes.
"""

from __future__ import annotations

import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Convert a workflow name into a safe filename component.

    Replaces all non-alphanumeric characters (except hyphens/underscores)
    with underscores, collapses runs of underscores, and strips edges.
    Handles Windows-illegal characters (``< > : " / \\ | ? *``).
    """
    safe = re.sub(r"[^a-z0-9_-]", "_", name.lower())
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:100] or "unnamed"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WorkflowDefinition:
    """A single browser workflow to execute."""

    id: int = 0
    name: str = ""
    path: str = ""
    priority: str = "MEDIUM"            # CRITICAL | HIGH | MEDIUM
    total_steps: int = 0
    first_page_route: str = "/"
    prd_requirements: list[str] = field(default_factory=list)
    depends_on: list[int] = field(default_factory=list)


@dataclass
class AppStartupInfo:
    """Parsed app startup details from startup agent."""

    start_command: str = ""
    seed_command: str = ""
    port: int = 3000
    health_url: str = ""
    env_setup: list[str] = field(default_factory=list)
    build_command: str = ""


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_app_running(port: int, timeout: int = 5) -> bool:
    """Quick health check -- is the app responding on this port?

    Sends a HEAD request to ``http://localhost:{port}``.  Returns True if
    any HTTP response is received (even 4xx/5xx -- the app is running).
    Returns False on connection refused, timeout, or any other error.
    """
    try:
        url = f"http://localhost:{port}"
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
        return True
    except urllib.error.HTTPError:
        # 4xx/5xx means the server IS running
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Seed credential extraction
# ---------------------------------------------------------------------------

_RE_EMAIL = re.compile(
    r"""(?:email|mail|username)\s*[:=]\s*["']([^"']+@[^"']+)["']""",
    re.IGNORECASE,
)
_RE_PASSWORD = re.compile(
    r"""(?:password|passwd|pass)\s*[:=]\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_RE_ROLE = re.compile(
    r"""(?:role|type|user_?type)\s*[:=]\s*["']([^"']+)["']""",
    re.IGNORECASE,
)

# Extended patterns for Prisma / ORM seed files where values are variable refs or enums
_RE_PASSWORD_VAR_REF = re.compile(
    r"""(?:password|passwd)\s*:\s*([a-zA-Z_]\w*)""",
    re.IGNORECASE,
)
_RE_PASSWORD_VAR_ASSIGN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?"""
    r"""(?:bcrypt\.hash|argon2\.hash|hashSync|hash)\s*\(\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_RE_ROLE_ENUM = re.compile(
    r"""(?:role|type|user_?type)\s*:\s*(?:\w+\.)?(\w+)\s*[,\n}]""",
    re.IGNORECASE,
)

_SEED_PATTERNS = [
    "**/seed*.ts", "**/seed*.js", "**/seed*.py", "**/seed*.cs",
    "**/Seed*.cs", "**/fixture*.*", "prisma/seed.ts",
    "**/fixtures/*.json", "**/management/commands/*seed*.py",
    "**/seeds/**/*.ts", "**/seeds/**/*.js",
]


def _extract_seed_credentials(project_root: Path) -> dict[str, dict[str, str]]:
    """Best-effort extraction of test account credentials from seed files.

    Scans common seed/fixture file locations for email+password pairs
    and associates them with role names found nearby.  Supports both
    direct literal values (``password: 'secret'``) and ORM patterns
    like Prisma where passwords are hashed via ``bcrypt.hash('secret', 10)``
    and roles use TypeScript enums (``UserRole.admin``).

    Returns dict like: ``{"admin": {"email": "admin@example.com", "password": "Admin123!"}}``
    Returns empty dict if nothing found.
    """
    credentials: dict[str, dict[str, str]] = {}
    seen_files: set[Path] = set()

    for pattern in _SEED_PATTERNS:
        for path in project_root.glob(pattern):
            if path in seen_files or not path.is_file():
                continue
            seen_files.add(path)
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
            except (OSError, UnicodeDecodeError):
                continue

            # --- Pass 1: build variable→plaintext map for hashed passwords ---
            password_vars: dict[str, str] = {}
            for line in lines:
                m = _RE_PASSWORD_VAR_ASSIGN.search(line)
                if m:
                    password_vars[m.group(1)] = m.group(2)

            # --- Pass 2: find emails, passwords, and roles ---
            emails: list[tuple[int, str]] = []
            passwords: list[tuple[int, str]] = []
            roles: list[tuple[int, str]] = []

            for i, line in enumerate(lines):
                for m in _RE_EMAIL.finditer(line):
                    emails.append((i, m.group(1)))

                # Direct literal passwords
                for m in _RE_PASSWORD.finditer(line):
                    passwords.append((i, m.group(1)))

                # Variable-reference passwords (resolve via password_vars)
                if not _RE_PASSWORD.search(line):
                    for m in _RE_PASSWORD_VAR_REF.finditer(line):
                        var_name = m.group(1)
                        if var_name in password_vars:
                            passwords.append((i, password_vars[var_name]))

                # Direct quoted roles
                for m in _RE_ROLE.finditer(line):
                    roles.append((i, m.group(1)))

                # Enum roles (e.g. UserRole.admin → "admin")
                if not _RE_ROLE.search(line):
                    for m in _RE_ROLE_ENUM.finditer(line):
                        roles.append((i, m.group(1)))

            # Group by proximity -- email+password within 10 lines belong together
            for e_line, email in emails:
                closest_pw = None
                closest_dist = 11  # beyond proximity window
                for p_line, pw in passwords:
                    dist = abs(e_line - p_line)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_pw = pw
                if closest_pw is None:
                    continue

                # Find role near this credential pair
                role_name = "user"
                closest_role_dist = 15
                for r_line, role in roles:
                    dist = min(abs(e_line - r_line), abs((e_line + closest_dist) - r_line))
                    if dist < closest_role_dist:
                        closest_role_dist = dist
                        role_name = role.lower()

                # Also infer role from email prefix
                if role_name == "user":
                    prefix = email.split("@")[0].lower()
                    for common in ("admin", "manager", "supervisor", "operator", "vendor", "supplier"):
                        if common in prefix:
                            role_name = common
                            break

                if role_name not in credentials:
                    credentials[role_name] = {"email": email, "password": closest_pw}

    return credentials


# ---------------------------------------------------------------------------
# Workflow generation
# ---------------------------------------------------------------------------

_MAX_WORKFLOWS = 10

_RE_REQ_LINE = re.compile(
    r"^\s*-\s*\[[ xX]\]\s*((?:REQ|TECH|INT|WIRE|DESIGN|TEST|SVC|FRONT|BACK)-\d+):\s*(.+?)(?:\(|$)",
    re.MULTILINE,
)
_RE_ROUTE = re.compile(
    r"""(?:path|route|url)\s*[:=]\s*["'](/[^"']*?)["']""",
    re.IGNORECASE,
)


def generate_browser_workflows(
    requirements_dir: Path,
    coverage_matrix_path: Path | None,
    app_type_info: Any | None,
    project_root: Path,
) -> list[WorkflowDefinition]:
    """Generate browser workflow definitions from existing artifacts.

    NO LLM call. Pure Python extraction. Deterministic and reproducible.
    Generates 1-10 goal-oriented workflow files plus WORKFLOW_INDEX.md.
    """
    credentials = _extract_seed_credentials(project_root)
    workflows: list[WorkflowDefinition] = []
    requirement_items: list[tuple[str, str]] = []  # (id, description)
    routes: list[str] = []

    # ---- PRIMARY PATH: E2E_COVERAGE_MATRIX.md ----
    matrix_content = ""
    if coverage_matrix_path and coverage_matrix_path.is_file():
        try:
            matrix_content = coverage_matrix_path.read_text(encoding="utf-8")
        except OSError:
            matrix_content = ""

    if matrix_content:
        # Parse matrix table rows for endpoint/route data
        for line in matrix_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and not stripped.startswith("|-"):
                cols = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cols) >= 2 and cols[0] and not cols[0].startswith("Req"):
                    requirement_items.append((cols[0], cols[1] if len(cols) > 1 else ""))

    # ---- FALLBACK PATH: REQUIREMENTS.md ----
    if not requirement_items:
        req_path = requirements_dir / "REQUIREMENTS.md"
        if req_path.is_file():
            try:
                req_content = req_path.read_text(encoding="utf-8")
                for m in _RE_REQ_LINE.finditer(req_content):
                    requirement_items.append((m.group(1), m.group(2).strip()))
            except OSError:
                pass

    if not requirement_items:
        return []

    # ---- Route discovery ----
    if project_root.is_dir():
        for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.cs"):
            for f in project_root.rglob(ext):
                rel = str(f.relative_to(project_root))
                if any(skip in rel for skip in ("node_modules", ".git", "__pycache__", "dist", "build")):
                    continue
                if any(kw in rel.lower() for kw in ("route", "router", "urls", "controller", "endpoint")):
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        for m in _RE_ROUTE.finditer(content):
                            route = m.group(1)
                            if route not in routes:
                                routes.append(route)
                    except OSError:
                        pass

    # ---- Categorize requirements ----
    auth_items: list[tuple[str, str]] = []
    crud_items: list[tuple[str, str]] = []
    complex_items: list[tuple[str, str]] = []
    error_items: list[tuple[str, str]] = []

    auth_keywords = ("login", "auth", "register", "sign in", "sign up", "logout", "password", "credential")
    crud_keywords = ("create", "add", "update", "edit", "delete", "remove", "list", "view", "display")
    error_keywords = ("error", "invalid", "unauthorized", "forbidden", "404", "validation")

    for req_id, desc in requirement_items:
        desc_lower = desc.lower()
        if any(kw in desc_lower for kw in auth_keywords):
            auth_items.append((req_id, desc))
        elif any(kw in desc_lower for kw in error_keywords):
            error_items.append((req_id, desc))
        elif any(kw in desc_lower for kw in crud_keywords):
            crud_items.append((req_id, desc))
        else:
            complex_items.append((req_id, desc))

    # ---- Generate workflow definitions ----
    workflow_id = 0
    workflows_dir = requirements_dir / "browser-workflows" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    def _credential_text(role: str) -> str:
        if role in credentials:
            cred = credentials[role]
            return f"(email: {cred['email']}, password: {cred['password']})"
        return "(discover credentials from seed files)"

    def _add_workflow(
        name: str,
        priority: str,
        steps: list[str],
        route: str,
        reqs: list[str],
        deps: list[int],
    ) -> WorkflowDefinition | None:
        nonlocal workflow_id
        if workflow_id >= _MAX_WORKFLOWS:
            return None
        workflow_id += 1
        wf = WorkflowDefinition(
            id=workflow_id,
            name=name,
            path=str(workflows_dir / f"workflow_{workflow_id:02d}_{_sanitize_filename(name)}.md"),
            priority=priority,
            total_steps=len(steps),
            first_page_route=route,
            prd_requirements=reqs,
            depends_on=deps,
        )

        # Write workflow file
        content_lines = [
            f"# Workflow {wf.id}: {name}",
            "",
            f"**Priority:** {priority}",
            f"**Requirements:** {', '.join(reqs) if reqs else 'General'}",
            f"**Prerequisites:** {', '.join(f'Workflow {d}' for d in deps) if deps else 'None'}",
            "",
            "## Goal",
            f"Complete the {name.lower()} workflow as a real user would.",
            "",
            "## Steps",
        ]
        for i, step in enumerate(steps, 1):
            content_lines.append(f"### Step {i}: {step}")
            content_lines.append("")

        content_lines.extend([
            "## Success Criteria",
            f"- All {len(steps)} steps completed without errors",
            "- No uncaught console errors",
            "- Page state reflects the completed action",
            "",
        ])

        Path(wf.path).write_text("\n".join(content_lines), encoding="utf-8")
        workflows.append(wf)
        return wf

    # Auth workflows first
    auth_wf_id = None
    if auth_items:
        login_items = [it for it in auth_items if any(kw in it[1].lower() for kw in ("login", "sign in"))]
        if login_items:
            role = "admin" if credentials.get("admin") else list(credentials.keys())[0] if credentials else "admin"
            wf = _add_workflow(
                name="Authentication Login",
                priority="CRITICAL",
                steps=[
                    "Navigate to the login page",
                    f"Enter credentials for {role} {_credential_text(role)}",
                    "Submit the login form",
                    "Verify successful login (dashboard or home page loads)",
                ],
                route="/login",
                reqs=[it[0] for it in login_items[:3]],
                deps=[],
            )
            if wf:
                auth_wf_id = wf.id

        register_items = [it for it in auth_items if any(kw in it[1].lower() for kw in ("register", "sign up"))]
        if register_items:
            _add_workflow(
                name="User Registration",
                priority="HIGH",
                steps=[
                    "Navigate to the registration page",
                    "Fill in all required registration fields with valid test data",
                    "Submit the registration form",
                    "Verify successful registration (confirmation or redirect to login)",
                ],
                route="/register",
                reqs=[it[0] for it in register_items[:3]],
                deps=[],
            )

    # CRUD workflows
    auth_dep = [auth_wf_id] if auth_wf_id else []
    entity_groups: dict[str, list[tuple[str, str]]] = {}
    for req_id, desc in crud_items:
        # Group by entity name (extract noun after CRUD verb)
        desc_lower = desc.lower()
        entity = "item"
        for verb in ("create", "add", "update", "edit", "delete", "remove", "list", "view", "display"):
            idx = desc_lower.find(verb)
            if idx >= 0:
                rest = desc[idx + len(verb):].strip()
                words = rest.split()
                if words:
                    entity = words[0].strip(".,;:()").lower()
                    break
        if entity not in entity_groups:
            entity_groups[entity] = []
        entity_groups[entity].append((req_id, desc))

    for entity, items in list(entity_groups.items())[:4]:
        entity_title = entity.title()
        crud_route = f"/{entity}s" if not entity.endswith("s") else f"/{entity}"
        # Find matching route
        for r in routes:
            if entity in r.lower():
                crud_route = r
                break

        _add_workflow(
            name=f"{entity_title} CRUD Operations",
            priority="HIGH",
            steps=[
                f"Navigate to the {entity} management page",
                f"Create a new {entity} with valid test data",
                f"Verify the new {entity} appears in the list",
                f"Open the {entity} for editing",
                f"Modify a field and save changes",
                f"Verify the changes are reflected",
            ],
            route=crud_route,
            reqs=[it[0] for it in items[:5]],
            deps=auth_dep,
        )

    # Complex workflows
    for req_id, desc in complex_items[:2]:
        desc_short = desc[:50].strip()
        _add_workflow(
            name=f"Complex: {desc_short}",
            priority="MEDIUM",
            steps=[
                "Navigate to the relevant page",
                f"Perform: {desc}",
                "Verify the outcome matches expected behavior",
            ],
            route="/",
            reqs=[req_id],
            deps=auth_dep,
        )

    # Error handling workflows
    if error_items and workflow_id < _MAX_WORKFLOWS:
        _add_workflow(
            name="Error Handling Validation",
            priority="MEDIUM",
            steps=[
                "Navigate to a form page",
                "Submit the form with invalid or empty data",
                "Verify appropriate error messages are displayed",
                "Verify the form does not submit with invalid data",
            ],
            route="/",
            reqs=[it[0] for it in error_items[:3]],
            deps=auth_dep,
        )

    # ---- Write WORKFLOW_INDEX.md ----
    index_path = requirements_dir / "browser-workflows" / "WORKFLOW_INDEX.md"
    index_lines = [
        "# Browser Workflow Index",
        "",
        "| ID | Name | Priority | Steps | Dependencies | Requirements |",
        "|----|------|----------|-------|-------------|--------------|",
    ]
    for wf in workflows:
        deps_str = ", ".join(str(d) for d in wf.depends_on) if wf.depends_on else "None"
        reqs_str = ", ".join(wf.prd_requirements[:5]) if wf.prd_requirements else "General"
        index_lines.append(
            f"| {wf.id} | {wf.name} | {wf.priority} | {wf.total_steps} | {deps_str} | {reqs_str} |"
        )
    index_lines.append("")
    index_path.write_text("\n".join(index_lines), encoding="utf-8")

    return workflows


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------

def parse_workflow_index(path: Path) -> list[WorkflowDefinition]:
    """Parse WORKFLOW_INDEX.md back to WorkflowDefinition list."""
    if not path.is_file():
        return []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    workflows: list[WorkflowDefinition] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|-") or stripped.startswith("| ID"):
            continue
        cols = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cols) < 4:
            continue
        try:
            wf_id = int(cols[0])
        except (ValueError, IndexError):
            continue
        deps: list[int] = []
        if len(cols) >= 5 and cols[4] and cols[4] != "None":
            for d in cols[4].split(","):
                d = d.strip()
                try:
                    deps.append(int(d))
                except ValueError:
                    pass
        reqs: list[str] = []
        if len(cols) >= 6 and cols[5] and cols[5] != "General":
            reqs = [r.strip() for r in cols[5].split(",")]

        workflows.append(WorkflowDefinition(
            id=wf_id,
            name=cols[1] if len(cols) > 1 else "",
            priority=cols[2] if len(cols) > 2 else "MEDIUM",
            total_steps=int(cols[3]) if len(cols) > 3 and cols[3].isdigit() else 0,
            depends_on=deps,
            prd_requirements=reqs,
        ))

    return workflows


# ---------------------------------------------------------------------------
# Result parsing
# ---------------------------------------------------------------------------

_RE_STATUS = re.compile(r"##\s*Status:\s*(PASSED|FAILED)", re.IGNORECASE)
_RE_STEP_HEADER = re.compile(r"###\s*Step\s+(\d+):")
_RE_RESULT_LINE = re.compile(r"Result:\s*(PASSED|FAILED|SUCCESS|FAILURE)", re.IGNORECASE)
_RE_EVIDENCE_LINE = re.compile(r"Evidence:", re.IGNORECASE)
_RE_SCREENSHOT_REF = re.compile(r"(w\d+_step\d+\.png)")
_RE_CONSOLE_ERROR = re.compile(r"(?:console error|error:)\s*(.+)", re.IGNORECASE)


def parse_workflow_results(path: Path) -> "WorkflowResult":
    """Parse workflow_{id}_results.md into WorkflowResult.

    Imports WorkflowResult from state to avoid circular imports at module level.
    """
    from .state import WorkflowResult

    if not path.is_file():
        return WorkflowResult(health="failed", failure_reason="Results file not found")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return WorkflowResult(health="failed", failure_reason="Cannot read results file")

    if len(content) < 100:
        return WorkflowResult(health="failed", failure_reason="Results file too small")

    result = WorkflowResult()

    # Parse status
    status_match = _RE_STATUS.search(content)
    if status_match:
        result.health = status_match.group(1).lower()

    # Parse steps
    steps_found: list[int] = []
    failed_step = ""
    for m in _RE_STEP_HEADER.finditer(content):
        steps_found.append(int(m.group(1)))

    result.total_steps = max(steps_found) if steps_found else 0
    result.completed_steps = len(steps_found)

    # Find failed step
    lines = content.splitlines()
    current_step = ""
    for line in lines:
        step_m = _RE_STEP_HEADER.search(line)
        if step_m:
            current_step = f"Step {step_m.group(1)}"
        result_m = _RE_RESULT_LINE.search(line)
        if result_m and result_m.group(1).upper() in ("FAILED", "FAILURE"):
            if not failed_step:
                failed_step = current_step
    result.failed_step = failed_step

    # Parse screenshots
    for m in _RE_SCREENSHOT_REF.finditer(content):
        if m.group(1) not in result.screenshots:
            result.screenshots.append(m.group(1))

    # Parse console errors
    for m in _RE_CONSOLE_ERROR.finditer(content):
        error_text = m.group(1).strip()
        if error_text and error_text not in result.console_errors:
            result.console_errors.append(error_text)

    return result


# ---------------------------------------------------------------------------
# App startup parsing
# ---------------------------------------------------------------------------

_RE_KV = re.compile(r"^\s*(?:\*\*)?(\w[\w\s]*?)(?:\*\*)?:\s*(.+)$", re.MULTILINE)


def parse_app_startup_info(path: Path) -> AppStartupInfo:
    """Parse APP_STARTUP.md into AppStartupInfo."""
    if not path.is_file():
        return AppStartupInfo()
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return AppStartupInfo()

    info = AppStartupInfo()
    kv: dict[str, str] = {}
    for m in _RE_KV.finditer(content):
        key = m.group(1).strip().lower().replace(" ", "_")
        kv[key] = m.group(2).strip().strip("`")

    info.start_command = kv.get("start_command", kv.get("command", ""))
    info.seed_command = kv.get("seed_command", kv.get("seed", ""))
    info.build_command = kv.get("build_command", kv.get("build", ""))
    info.health_url = kv.get("health_url", kv.get("url", ""))

    port_str = kv.get("port", kv.get("app_port", ""))
    if port_str:
        try:
            port_match = re.search(r"\d+", port_str)
            if port_match:
                info.port = int(port_match.group())
        except (AttributeError, ValueError):
            pass

    return info


# ---------------------------------------------------------------------------
# Structural verification
# ---------------------------------------------------------------------------

def verify_workflow_execution(
    workflows_dir: Path,
    workflow_id: int,
    expected_steps: int,
) -> tuple[bool, list[str]]:
    """Structural verification of workflow execution -- prevents false passes.

    Checks: results file exists, step numbering complete, screenshot files exist,
    Result/Evidence lines present, no contradictions (PASSED but step FAILED).

    Returns (passed, issues) where issues is empty on success.
    """
    issues: list[str] = []
    results_dir = workflows_dir.parent / "results"
    screenshots_dir = workflows_dir.parent / "screenshots"

    # Check 1: Results file exists and has content
    results_file = results_dir / f"workflow_{workflow_id:02d}_results.md"
    # Also check without zero-padding
    if not results_file.is_file():
        results_file = results_dir / f"workflow_{workflow_id}_results.md"
    if not results_file.is_file():
        issues.append(f"Results file not found for workflow {workflow_id}")
        return False, issues

    try:
        content = results_file.read_text(encoding="utf-8")
    except OSError:
        issues.append(f"Cannot read results file for workflow {workflow_id}")
        return False, issues

    if len(content) < 100:
        issues.append(f"Results file too small ({len(content)} bytes) for workflow {workflow_id}")
        return False, issues

    # Check 2: All step entries found
    found_steps: set[int] = set()
    for m in _RE_STEP_HEADER.finditer(content):
        found_steps.add(int(m.group(1)))

    for step_num in range(1, expected_steps + 1):
        if step_num not in found_steps:
            issues.append(f"Missing step {step_num} in workflow {workflow_id}")

    # Check 3: No gaps in step numbering
    if found_steps:
        expected_set = set(range(1, max(found_steps) + 1))
        gaps = expected_set - found_steps
        if gaps:
            issues.append(f"Gap in step numbering: missing steps {sorted(gaps)}")

    # Check 4: Screenshots exist on disk
    for step_num in range(1, expected_steps + 1):
        screenshot = screenshots_dir / f"w{workflow_id:02d}_step{step_num:02d}.png"
        # Also check alternative naming patterns
        alt1 = screenshots_dir / f"w{workflow_id}_step{step_num}.png"
        alt2 = screenshots_dir / f"w{workflow_id:02d}_step{step_num}.png"
        if not (screenshot.is_file() or alt1.is_file() or alt2.is_file()):
            issues.append(f"Screenshot missing for step {step_num} of workflow {workflow_id}")

    # Check 5: Result and Evidence lines in each step
    lines = content.splitlines()
    current_step_num = 0
    step_has_result: dict[int, bool] = {}
    step_has_evidence: dict[int, bool] = {}
    step_result_value: dict[int, str] = {}

    for line in lines:
        step_m = _RE_STEP_HEADER.search(line)
        if step_m:
            current_step_num = int(step_m.group(1))
            step_has_result.setdefault(current_step_num, False)
            step_has_evidence.setdefault(current_step_num, False)
        if current_step_num > 0:
            if _RE_RESULT_LINE.search(line):
                step_has_result[current_step_num] = True
                rm = _RE_RESULT_LINE.search(line)
                if rm:
                    step_result_value[current_step_num] = rm.group(1).upper()
            if _RE_EVIDENCE_LINE.search(line):
                step_has_evidence[current_step_num] = True

    for step_num in range(1, expected_steps + 1):
        if not step_has_result.get(step_num, False):
            issues.append(f"Missing Result line in step {step_num} of workflow {workflow_id}")
        if not step_has_evidence.get(step_num, False):
            issues.append(f"Missing Evidence line in step {step_num} of workflow {workflow_id}")

    # Check 6: Contradiction detection
    status_match = _RE_STATUS.search(content)
    if status_match and status_match.group(1).upper() == "PASSED":
        for step_num, val in step_result_value.items():
            if val in ("FAILED", "FAILURE"):
                issues.append(
                    f"Contradiction: workflow {workflow_id} marked PASSED but step {step_num} has Result: FAILED"
                )

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# Screenshot diversity check
# ---------------------------------------------------------------------------

def check_screenshot_diversity(
    screenshots_dir: Path,
    workflow_id: int,
    step_count: int,
) -> bool:
    """Check that screenshots aren't identical repeated captures.

    For workflows with >3 screenshots, at least 30% must have unique file sizes.
    Returns True if diverse (or too few to check), False if too many identical.
    """
    files: list[Path] = []
    for i in range(1, step_count + 1):
        for pattern in [
            f"w{workflow_id:02d}_step{i:02d}.png",
            f"w{workflow_id}_step{i}.png",
            f"w{workflow_id:02d}_step{i}.png",
        ]:
            p = screenshots_dir / pattern
            if p.is_file():
                files.append(p)
                break

    if len(files) <= 3:
        return True  # Too few to check

    sizes = [f.stat().st_size for f in files]
    unique_sizes = len(set(sizes))
    diversity_ratio = unique_sizes / len(sizes)
    return diversity_ratio >= 0.3


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def write_workflow_state(
    workflows_dir: Path,
    definitions: list[WorkflowDefinition],
    initial_status: str = "PENDING",
) -> None:
    """Create WORKFLOW_STATE.md -- Python-managed, not LLM-editable."""
    state_path = workflows_dir.parent / "WORKFLOW_STATE.md"
    lines = [
        "# Workflow Execution State",
        "",
        "| ID | Name | Status | Retries | Screenshots |",
        "|----|------|--------|---------|-------------|",
    ]
    for wf in definitions:
        lines.append(f"| {wf.id} | {wf.name} | {initial_status} | 0 | 0 |")
    lines.append("")
    state_path.write_text("\n".join(lines), encoding="utf-8")


def update_workflow_state(
    workflows_dir: Path,
    workflow_id: int,
    status: str,
    retries: int = 0,
    screenshots: int = 0,
) -> None:
    """Update single workflow row in WORKFLOW_STATE.md."""
    state_path = workflows_dir.parent / "WORKFLOW_STATE.md"
    if not state_path.is_file():
        return
    try:
        content = state_path.read_text(encoding="utf-8")
    except OSError:
        return

    new_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and not stripped.startswith("|-") and not stripped.startswith("| ID"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if cols:
                try:
                    row_id = int(cols[0])
                except (ValueError, IndexError):
                    new_lines.append(line)
                    continue
                if row_id == workflow_id:
                    name = cols[1] if len(cols) > 1 else ""
                    line = f"| {row_id} | {name} | {status} | {retries} | {screenshots} |"
        new_lines.append(line)

    state_path.write_text("\n".join(new_lines), encoding="utf-8")


def count_screenshots(screenshots_dir: Path) -> int:
    """Count screenshot files (.png) in the screenshots directory."""
    if not screenshots_dir.is_dir():
        return 0
    return len(list(screenshots_dir.glob("*.png")))


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_readiness_report(
    workflows_dir: Path,
    report: Any,  # BrowserTestReport
    workflow_defs: list[WorkflowDefinition],
) -> str:
    """Generate BROWSER_READINESS_REPORT.md -- production readiness proof."""
    # Determine verdict
    if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
        verdict = "PRODUCTION READY"
    elif report.passed_workflows > 0:
        verdict = "PARTIALLY VERIFIED"
    else:
        verdict = "NOT VERIFIED"

    lines = [
        "# Browser Readiness Report",
        "",
        f"## Verdict: {verdict}",
        "",
        "## Summary",
        f"- **Total workflows:** {report.total_workflows}",
        f"- **Passed:** {report.passed_workflows}",
        f"- **Failed:** {report.failed_workflows}",
        f"- **Skipped:** {report.skipped_workflows}",
        f"- **Fix cycles:** {report.total_fix_cycles}",
        f"- **Total screenshots:** {report.total_screenshots}",
        f"- **Regression sweep:** {'Passed' if report.regression_sweep_passed else 'Not run / Failed'}",
        "",
        "## Workflow Results",
        "",
        "| # | Workflow | Steps | Status | Screenshots | Retries |",
        "|---|---------|-------|--------|-------------|---------|",
    ]

    result_map: dict[int, Any] = {}
    for wr in report.workflow_results:
        result_map[wr.workflow_id] = wr

    for wf in workflow_defs:
        wr = result_map.get(wf.id)
        if wr:
            lines.append(
                f"| {wf.id} | {wf.name} | {wr.completed_steps}/{wr.total_steps} | "
                f"{wr.health.upper()} | {len(wr.screenshots)} | {wr.fix_retries_used} |"
            )
        else:
            lines.append(f"| {wf.id} | {wf.name} | 0/{wf.total_steps} | UNKNOWN | 0 | 0 |")

    # Per-workflow details
    lines.extend(["", "## Detailed Results", ""])
    for wf in workflow_defs:
        wr = result_map.get(wf.id)
        lines.append(f"### Workflow {wf.id}: {wf.name}")
        if wr:
            lines.append(f"- **Health:** {wr.health.upper()}")
            if wr.failed_step:
                lines.append(f"- **Failed at:** {wr.failed_step}")
                lines.append(f"- **Reason:** {wr.failure_reason}")
            if wr.console_errors:
                lines.append("- **Console errors:**")
                for err in wr.console_errors[:10]:
                    lines.append(f"  - {err}")
            if wr.screenshots:
                lines.append(f"- **Screenshots:** {', '.join(wr.screenshots[:10])}")
        else:
            lines.append("- **Health:** UNKNOWN")
        lines.append("")

    # Console error summary
    all_errors: list[str] = []
    for wr in report.workflow_results:
        for err in wr.console_errors:
            if err not in all_errors:
                all_errors.append(err)
    if all_errors:
        lines.extend(["## Console Error Summary", ""])
        for err in all_errors[:20]:
            lines.append(f"- {err}")
        lines.append("")

    content = "\n".join(lines)

    # Write report
    report_path = workflows_dir.parent / "BROWSER_READINESS_REPORT.md"
    report_path.write_text(content, encoding="utf-8")

    return content


def generate_unresolved_issues(
    workflows_dir: Path,
    failed_results: list[Any],  # list[WorkflowResult]
) -> str:
    """Generate UNRESOLVED_ISSUES.md -- detailed failure records for handoff."""
    if not failed_results:
        return ""

    lines = [
        "# Unresolved Browser Testing Issues",
        "",
        f"**Total unresolved workflows:** {len(failed_results)}",
        "",
    ]

    for wr in failed_results:
        lines.extend([
            f"## Workflow {wr.workflow_id}: {wr.workflow_name}",
            f"- **Failed at:** {wr.failed_step or 'Unknown'}",
            f"- **Reason:** {wr.failure_reason or 'Unknown'}",
            f"- **Fix attempts:** {wr.fix_retries_used}",
        ])
        if wr.console_errors:
            lines.append("- **Console errors at failure:**")
            for err in wr.console_errors[:5]:
                lines.append(f"  - {err}")
        if wr.screenshots:
            lines.append(f"- **Last screenshot:** {wr.screenshots[-1] if wr.screenshots else 'None'}")
        lines.append("")

    content = "\n".join(lines)

    issues_path = workflows_dir.parent / "UNRESOLVED_ISSUES.md"
    issues_path.write_text(content, encoding="utf-8")

    return content


# ---------------------------------------------------------------------------
# Prompt constants
# ---------------------------------------------------------------------------

BROWSER_APP_STARTUP_PROMPT = """\
You are an application startup agent. Your job is to get the target application
running locally so that browser testing can proceed.

## Project Root
{project_root}

## User Override (if provided)
- Start command: {app_start_command}
- Port: {app_port}

## Instructions

1. **DISCOVER** the project structure:
   - Read package.json, requirements.txt, docker-compose.yml, or similar
   - Identify the start command (e.g., `npm run dev`, `python manage.py runserver`)
   - Identify the database setup (migrations, seed commands)

2. **INSTALL** dependencies if needed:
   - `npm install`, `pip install -r requirements.txt`, `dotnet restore`, etc.
   - Skip if node_modules/venv already exists

3. **DATABASE** setup:
   - Run migrations if applicable
   - Run seed/fixture commands to populate test data
   - Record the seed command used

4. **START** the application:
   - Use the discovered or user-provided start command
   - Run in background (do NOT block)
   - Wait for the app to be ready (check health URL or wait 10 seconds)

5. **VERIFY** the app is running:
   - Try to access the root URL
   - Record the actual port and URL

6. **REPORT** in APP_STARTUP.md:
   Write a file called APP_STARTUP.md in the .agent-team/browser-workflows/ directory with:
   - **Start Command:** the command used
   - **Seed Command:** the seed command used (or N/A)
   - **Port:** the port number
   - **Health URL:** the URL to check health
   - **Build Command:** any build command used (or N/A)

If the app fails to start, still write APP_STARTUP.md with what you attempted
and mark it as FAILED with the error details.
"""


BROWSER_WORKFLOW_EXECUTOR_PROMPT = """\
You are a browser testing executor agent with access to Playwright MCP tools.
You will execute a single workflow by navigating a real browser, interacting
with the application exactly as a human user would, and documenting every step
with screenshots and evidence.

## Application URL
{app_url}

## Workflow ID
{workflow_id}

## Screenshots Directory
{screenshots_dir}

## Workflow Definition
{workflow_content}

## MANDATORY: STEP 0 -- DATA DISCOVERY (before ANY browser interaction)

Before touching the browser, you MUST discover test data:

1. Search for seed/fixture files:
   - Look in: **/seed*.ts, **/seed*.js, **/seed*.py, **/seed*.cs
   - Look in: **/fixture*.*, prisma/seed.ts, **/fixtures/*.json
   - Look in: **/management/commands/*seed*.py
   - Look in: tests/e2e/** for existing test credentials

2. Extract credentials for EVERY role mentioned in the workflow:
   - Email addresses
   - Passwords
   - Role assignments

3. Record ALL findings under ## Test Data Discovery in your results file

4. If credentials for a required role are NOT found:
   - Report FAILURE immediately
   - Do NOT guess or invent credentials
   - NEVER use placeholder credentials like test@test.com / password123

## WORKFLOW EXECUTION (Steps 1-N)

For EACH step in the workflow:

### Before the action:
- Call `browser_snapshot()` to see the current page state
- Decide what action to take based on what you SEE (not assumptions)

### Execute the action:
- Use the appropriate Playwright MCP tool:
  - `browser_navigate` for page navigation
  - `browser_click` for clicking elements (use ref from snapshot)
  - `browser_type` for typing text
  - `browser_fill_form` for filling forms
  - `browser_select_option` for dropdowns
  - `browser_wait_for` to wait for elements

### After the action:
- Call `browser_take_screenshot` and save as `w{{workflow_id:02d}}_step{{step_num:02d}}.png` \
in the screenshots directory
- Call `browser_snapshot()` to verify the page changed
- Call `browser_console_messages` to check for errors

### ADAPT to unexpected state:
- If a modal/dialog appears, handle it before proceeding
- If a redirect occurs, update your understanding of the page
- If an element isn't visible, scroll or look for it
- If a loading spinner is visible, wait for it to disappear

### On FAILURE:
- STOP immediately -- do NOT continue past a failed step
- Document exactly what happened, what was expected, and what was observed
- Include the screenshot and console errors

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

## ANTI-CHEAT RULES (NON-NEGOTIABLE)

- You MUST call browser_snapshot() BEFORE every step action
- You MUST call browser_take_screenshot() AFTER every step action
- You MUST call browser_console_messages() AFTER every step action
- You MUST NOT skip steps -- every step must be attempted
- You MUST NOT claim success without visual evidence
- If the page does NOT change after an action = FAILURE
- If there are uncaught console errors (TypeError, ReferenceError, etc.) = FAILURE
- If you cannot find credentials for a required role = FAILURE
- You MUST NEVER guess or invent test data -- only use what you discover
- You MUST NEVER use hardcoded selectors like data-testid -- find elements by what you SEE

## OUTPUT

Write results to the results directory as `workflow_{{workflow_id:02d}}_results.md`:

```markdown
## Status: PASSED/FAILED

## Test Data Discovery
- Admin: admin@example.com / ****
- User: user@example.com / ****

### Step 1: [Step description]
Result: PASSED/FAILED
Evidence: [What was observed on screen]
Screenshot: w{{workflow_id:02d}}_step01.png
Console: [Any console messages]

### Step 2: ...
```
"""


BROWSER_WORKFLOW_FIX_PROMPT = """\
You are a code fix agent. A browser workflow test has failed. Your job is to
fix the APPLICATION code (not the test workflow) to make the workflow pass.

## Failure Report
{failure_report}

## Workflow Definition
{workflow_content}

## Console Errors
{console_errors}

## Fix Cycle Log (previous attempts)
{fix_cycle_log}

## Instructions

1. **ANALYZE** the failure:
   - Read the failure report carefully
   - Check the console errors for clues
   - Read the FIX_CYCLE_LOG.md to see what was already tried
   - Do NOT repeat a fix strategy that already failed

2. **CLASSIFY** the issue:
   - IMPLEMENT: Feature not implemented yet
   - FIX_AUTH: Authentication/authorization issue
   - FIX_WIRING: API endpoint or routing issue
   - FIX_LOGIC: Business logic error
   - FIX_DATA: Missing or incorrect seed/test data

3. **FIX** the app code:
   - Make targeted changes to fix the specific failure
   - Do not make unrelated changes
   - If the fix requires database changes, update seed files too

4. **LOG** your fix in FIX_CYCLE_LOG.md:
   - Append an entry with: cycle number, classification, what you changed, file paths

5. **If max retries exhausted:** Write detailed notes in UNRESOLVED_ISSUES.md
   explaining what was tried and what remains broken.

IMPORTANT: Fix the APP, not the workflow definition. The workflow describes
what a user should be able to do. If they can't, the app is wrong.
"""


BROWSER_REGRESSION_SWEEP_PROMPT = """\
You are a regression sweep agent with access to Playwright MCP tools.
Your job is a QUICK check: navigate to each passed workflow's starting page
and verify it still loads correctly. No form filling, no multi-step interaction.

## Application URL
{app_url}

## Screenshots Directory
{screenshots_dir}

## Passed Workflow URLs to Check
{passed_workflow_urls}

## Instructions

For EACH URL in the list above:
1. Call `browser_navigate` to go to the URL
2. Call `browser_snapshot` to see the page
3. Call `browser_take_screenshot` to capture proof
4. Verify: page loads (not blank, not error page, not 404, not "Cannot GET")
5. Move to the next URL -- do NOT interact further

## Content Verification
For each page, verify it is not just loading but has MEANINGFUL content:
  - Tables should have at least one data row (not just headers)
  - Lists should have at least one item
  - Forms should have populated fields or labels
  - Dashboards should have at least one card/widget with data
A page that loads but shows only empty containers or "No data" when data should exist = REGRESSED.

## Output

Write results to REGRESSION_SWEEP_RESULTS.md:

```markdown
## Regression Sweep Results

| # | URL | Status | Screenshot |
|---|-----|--------|------------|
| 1 | /login | OK | regression_01.png |
| 2 | /dashboard | REGRESSED | regression_02.png |
```

### Regressed Pages
- /dashboard: Shows blank page instead of dashboard content

### Summary
- Total checked: N
- OK: N
- Regressed: N
- Regressed workflow IDs: [list]
```

IMPORTANT: This is a QUICK check. Navigate, screenshot, verify, move on.
Do NOT fill forms, do NOT click buttons, do NOT type anything.
"""
