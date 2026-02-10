"""End-to-end testing utilities for agent-team.

Provides app-type detection, E2E result parsing, and prompt templates
for backend API testing, frontend Playwright testing, and E2E fix cycles.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .state import E2ETestReport


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AppTypeInfo:
    """Detected application type and tooling information."""

    has_backend: bool = False
    has_frontend: bool = False
    backend_framework: str = ""   # express, fastapi, django, nestjs
    frontend_framework: str = ""  # react, nextjs, vue, angular
    language: str = ""            # typescript, javascript, python
    package_manager: str = ""     # npm, yarn, pnpm, pip
    start_command: str = ""
    build_command: str = ""
    db_type: str = ""             # prisma, mongoose, sequelize, django-orm
    seed_command: str = ""
    api_directory: str = ""
    frontend_directory: str = ""
    playwright_installed: bool = False


# ---------------------------------------------------------------------------
# App-type detection
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    """Read and parse a JSON file, returning empty dict on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _file_contains(path: Path, needle: str) -> bool:
    """Return True if *path* is a readable text file containing *needle*."""
    try:
        return needle in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def detect_app_type(project_root: Path) -> AppTypeInfo:  # noqa: C901 — detection logic is inherently branchy
    """Detect the application stack under *project_root*.

    Inspects ``package.json``, ``requirements.txt``, ``pyproject.toml``,
    framework config files, and lock files to populate an :class:`AppTypeInfo`.
    """
    info = AppTypeInfo()
    root = Path(project_root)

    # ------------------------------------------------------------------
    # 1. package.json — JS/TS ecosystem
    # ------------------------------------------------------------------
    pkg = _read_json(root / "package.json")
    deps: dict = pkg.get("dependencies", {})
    dev_deps: dict = pkg.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}
    scripts: dict = pkg.get("scripts", {})

    if pkg:
        # Language
        if "typescript" in all_deps or (root / "tsconfig.json").is_file():
            info.language = "typescript"
        else:
            info.language = "javascript"

        # Backend frameworks
        if "express" in deps:
            info.has_backend = True
            info.backend_framework = "express"
        if "@nestjs/core" in deps:
            info.has_backend = True
            info.backend_framework = "nestjs"

        # Frontend frameworks
        if "next" in deps:
            info.has_frontend = True
            info.frontend_framework = "nextjs"
            # Next.js apps can also serve API routes
            info.has_backend = True
            if not info.backend_framework:
                info.backend_framework = "nextjs"
        elif "react" in deps:
            info.has_frontend = True
            info.frontend_framework = "react"
        if "vue" in deps:
            info.has_frontend = True
            info.frontend_framework = "vue"
        if "@angular/core" in deps:
            info.has_frontend = True
            info.frontend_framework = "angular"

        # Database
        if "prisma" in all_deps or "@prisma/client" in deps:
            info.db_type = "prisma"
        elif "mongoose" in deps:
            info.db_type = "mongoose"
        elif "sequelize" in deps:
            info.db_type = "sequelize"

        # Playwright
        if "@playwright/test" in dev_deps or "@playwright/test" in deps:
            info.playwright_installed = True

        # Commands from scripts
        if "dev" in scripts:
            info.start_command = f"{_pm_run(info)} dev"
        elif "start" in scripts:
            info.start_command = f"{_pm_run(info)} start"

        if "build" in scripts:
            info.build_command = f"{_pm_run(info)} build"

        if "seed" in scripts:
            info.seed_command = f"{_pm_run(info)} seed"
        elif "db:seed" in scripts:
            info.seed_command = f"{_pm_run(info)} db:seed"
        elif "prisma" in all_deps:
            info.seed_command = "npx prisma db seed"

    # ------------------------------------------------------------------
    # 2. Package manager from lock files
    # ------------------------------------------------------------------
    if (root / "yarn.lock").is_file():
        info.package_manager = "yarn"
    elif (root / "pnpm-lock.yaml").is_file():
        info.package_manager = "pnpm"
    elif (root / "package-lock.json").is_file():
        info.package_manager = "npm"

    # Re-derive start/build commands after package_manager is known
    if pkg and info.start_command:
        pm_run = _pm_run(info)
        # Replace the placeholder prefix
        if info.start_command.startswith("npm run "):
            info.start_command = f"{pm_run} {info.start_command.split(' ', 2)[-1]}"
        if info.build_command and info.build_command.startswith("npm run "):
            info.build_command = f"{pm_run} {info.build_command.split(' ', 2)[-1]}"

    # ------------------------------------------------------------------
    # 3. Python ecosystem
    # ------------------------------------------------------------------
    has_requirements_txt = (root / "requirements.txt").is_file()
    has_pyproject = (root / "pyproject.toml").is_file()

    if has_requirements_txt or has_pyproject:
        info.language = info.language or "python"
        info.package_manager = info.package_manager or "pip"

        # Read requirements.txt
        req_text = ""
        if has_requirements_txt:
            try:
                req_text = (root / "requirements.txt").read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

        pyproject_text = ""
        if has_pyproject:
            try:
                pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

        combined = req_text + pyproject_text

        if "django" in combined.lower():
            info.has_backend = True
            info.backend_framework = "django"
            info.db_type = info.db_type or "django-orm"
            if not info.start_command:
                info.start_command = "python manage.py runserver"
            if not info.seed_command:
                info.seed_command = "python manage.py loaddata"
        elif "fastapi" in combined.lower():
            info.has_backend = True
            info.backend_framework = "fastapi"
            if not info.start_command:
                info.start_command = "uvicorn main:app --reload"
        elif "flask" in combined.lower():
            info.has_backend = True
            info.backend_framework = "flask"
            if not info.start_command:
                info.start_command = "flask run"

    # ------------------------------------------------------------------
    # 4. Framework config files
    # ------------------------------------------------------------------
    if (root / "angular.json").is_file():
        info.has_frontend = True
        info.frontend_framework = "angular"

    for cfg_name in ("next.config.js", "next.config.mjs", "next.config.ts"):
        if (root / cfg_name).is_file():
            info.has_frontend = True
            info.frontend_framework = "nextjs"
            info.has_backend = True
            if not info.backend_framework:
                info.backend_framework = "nextjs"
            break

    for cfg_name in ("nuxt.config.js", "nuxt.config.ts"):
        if (root / cfg_name).is_file():
            info.has_frontend = True
            info.frontend_framework = "vue"
            info.has_backend = True
            break

    # Prisma schema
    if (root / "prisma" / "schema.prisma").is_file():
        info.db_type = info.db_type or "prisma"

    # ------------------------------------------------------------------
    # 5. API directory
    # ------------------------------------------------------------------
    if not info.api_directory:
        for candidate in (
            "src/routes",
            "server/routes",
            "src/controllers",
            "server/controllers",
            "src/api",
            "server",
            "app/api",            # Next.js app-router API routes
            "pages/api",          # Next.js pages-router API routes
            "app",                # Django / Flask
        ):
            if (root / candidate).is_dir():
                info.api_directory = candidate
                break

    # ------------------------------------------------------------------
    # 6. Frontend directory
    # ------------------------------------------------------------------
    if not info.frontend_directory:
        for candidate in (
            "src/app",            # Angular / Next.js app-router
            "src/components",     # React / Vue
            "app",                # Next.js app-router
            "pages",              # Next.js pages-router
            "src/pages",          # Vite React
            "src/views",          # Vue
        ):
            if (root / candidate).is_dir():
                info.frontend_directory = candidate
                break

    return info


def _pm_run(info: AppTypeInfo) -> str:
    """Return the ``<pm> run`` prefix for the detected package manager."""
    if info.package_manager == "yarn":
        return "yarn"
    if info.package_manager == "pnpm":
        return "pnpm"
    return "npm run"


# ---------------------------------------------------------------------------
# E2E result parsing
# ---------------------------------------------------------------------------

_RE_PASS_COUNT = re.compile(r"(\d+)\s*(?:passed|✓)", re.IGNORECASE)
_RE_FAIL_COUNT = re.compile(r"(\d+)\s*(?:failed|✗)", re.IGNORECASE)
_RE_TOTAL_LINE = re.compile(
    r"Total:\s*(\d+)\s*\|\s*Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)",
    re.IGNORECASE,
)
_RE_FAILURE_LINE = re.compile(r"^\s*[-*]\s*(?:FAIL:|✗)\s*(.+)", re.MULTILINE)


def parse_e2e_results(results_path: Path) -> E2ETestReport:
    """Parse an ``E2E_RESULTS.md`` file into an :class:`E2ETestReport`.

    If the file is missing or cannot be parsed, returns a report with
    ``skipped=True`` and an explanatory ``skip_reason``.
    """
    try:
        text = results_path.read_text(encoding="utf-8")
    except OSError:
        return E2ETestReport(
            skipped=True,
            skip_reason="Results file not found",
            health="skipped",
        )

    if not text.strip():
        return E2ETestReport(
            skipped=True,
            skip_reason="Results file is empty",
            health="skipped",
        )

    report = E2ETestReport()
    failed_descriptions: list[str] = []

    # Split by sections
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)

    for section in sections:
        section_lower = section.lower()
        is_backend = section_lower.startswith("backend")
        is_frontend = section_lower.startswith("frontend")

        if not is_backend and not is_frontend:
            continue

        total = 0
        passed = 0
        failed = 0

        # Try the structured "Total: N | Passed: P | Failed: F" line first
        total_match = _RE_TOTAL_LINE.search(section)
        if total_match:
            total = int(total_match.group(1))
            passed = int(total_match.group(2))
            failed = int(total_match.group(3))
        else:
            # Fall back to counting individual patterns
            for m in _RE_PASS_COUNT.finditer(section):
                passed += int(m.group(1))
            for m in _RE_FAIL_COUNT.finditer(section):
                failed += int(m.group(1))
            total = passed + failed

        # Extract failure descriptions
        for m in _RE_FAILURE_LINE.finditer(section):
            desc = m.group(1).strip()
            if desc:
                failed_descriptions.append(desc)

        if is_backend:
            report.backend_total = total
            report.backend_passed = passed
        elif is_frontend:
            report.frontend_total = total
            report.frontend_passed = passed

    report.failed_tests = failed_descriptions

    # Compute health
    total_tests = report.backend_total + report.frontend_total
    total_passed = report.backend_passed + report.frontend_passed

    if total_tests == 0:
        report.health = "skipped"
        report.skipped = True
        report.skip_reason = "Results file unparseable — no test counts found"
    elif total_passed == total_tests:
        report.health = "passed"
    elif total_tests > 0 and (total_passed / total_tests) >= 0.70:
        report.health = "partial"
    else:
        report.health = "failed"

    return report


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

BACKEND_E2E_PROMPT = """\
[PHASE: E2E BACKEND API TESTING]

You are running end-to-end tests against the REAL backend API. These are NOT unit tests —
they make REAL HTTP calls to a RUNNING server.

INSTRUCTIONS:
1. Read {requirements_dir}/REQUIREMENTS.md to understand ALL API endpoints and workflows
2. Scan {api_directory} to discover route/controller files and actual endpoints
3. Create E2E test plan in {requirements_dir}/E2E_TEST_PLAN.md listing:
   - Every API workflow to test (register → login → CRUD → verify)
   - Test accounts for each role
   - Expected request/response shapes
4. BEFORE writing any test code, generate {requirements_dir}/E2E_COVERAGE_MATRIX.md:
   - Read REQUIREMENTS.md and extract EVERY API endpoint (REQ-xxx, SVC-xxx items)
   - Create a table with columns: Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed
   - Include a row for EVERY endpoint — no exceptions
   - Add a Cross-Role Workflows section if auth/roles are detected
   - All checkboxes start as [ ]
   - Add a coverage summary footer: ## Coverage: 0/N written (0%)

5. As you write each test:
   - Update the corresponding row in E2E_COVERAGE_MATRIX.md: mark Test Written as [x]
   - Add the test file name to the Test File column

6. After running tests:
   - Update Test Passed column: [x] for passing, [ ] for failing
   - Update the coverage summary footer with actual counts

7. You CANNOT declare this phase complete if E2E_COVERAGE_MATRIX.md has unchecked Test Written rows.
   Every row must have a test. If a requirement is not testable via API, mark it as [N/A] with a reason.

8. Write API E2E test scripts in tests/e2e/api/
   - Use the project's test framework or plain fetch/axios
   - REAL HTTP calls only — zero mocks, zero stubs
   - Test WORKFLOWS not individual endpoints
9. Start the server: {start_command} on PORT={test_port}
   - Wait for health check (GET /health or /api/health returning 200)
   - Seed database if needed: {seed_command}
10. Run the tests and collect results
11. Write results to {requirements_dir}/E2E_RESULTS.md with format:
   ## Backend API Tests
   Total: N | Passed: P | Failed: F

   ### Passed
   - ✓ test_name: description

   ### Failed
   - ✗ test_name: error description
12. Shut down the server after tests complete

SERVER LIFECYCLE:
- Start: {start_command} with PORT={test_port} environment variable
- Health check: retry GET http://localhost:{test_port}/health up to 30 seconds
- Seed: {seed_command} (if applicable)
- Cleanup: kill server process, reset database state

Framework: {framework}
Database: {db_type}

Continue fixing until all tests pass or max retries exhausted. Do not stop early.

ROLE-BASED API TESTING (MANDATORY if app has authentication):

Check if the app has role-based access control (multiple user types, role fields
in user model, role-based middleware/guards/decorators). If it does:

1. ACCOUNT COVERAGE: Test plan must include test accounts for EVERY role defined
   in the system. Read auth middleware, role enums, seed data, and user model to
   find ALL roles — not just "admin."

2. POSITIVE ACCESS TESTS: For each role, test it CAN access its expected endpoints.
   Login as role → call endpoints that role should access → verify 200/201 (not 403).

3. NEGATIVE ACCESS TESTS: For each role, test it CANNOT access at least one endpoint
   restricted to a different role. Login as Role A → call Role B's endpoint → verify
   403 Forbidden.

4. COMPLETE AUTH FLOW PER ROLE: register (if applicable) → login → access protected
   resource → verify role-specific response data → test token refresh (if applicable).

5. CROSS-ROLE WORKFLOW: If the app has workflows spanning multiple roles (User A creates
   → User B approves → User C views), test the COMPLETE cross-role workflow with real
   accounts for each role. Do not test each role in isolation only.

If the app has NO authentication or a single role, skip this section entirely.

STATE PASSING BETWEEN ROLES: When testing cross-role workflows, you MUST
capture entity IDs from creation responses and pass them to subsequent
role tests. Do NOT rely on "find the first item in the list" — use explicit
IDs for deterministic testing.

Pattern for API tests:
   const createRes = await fetch('/api/items', {{ method: 'POST', ... }});
   const {{ id: itemId }} = await createRes.json();
   // Use itemId explicitly in subsequent role's requests:
   const approveRes = await fetch(`/api/items/${{itemId}}/approve`, ...);

NEVER do this:
   await page.click('table tbody tr:first-child');  // Fragile, non-deterministic

If the app doesn't expose IDs in URLs or responses, use a unique identifier
like a title or timestamp-based reference number, and search/filter for it.

[ORIGINAL USER REQUEST]
{task_text}"""

FRONTEND_E2E_PROMPT = """\
[PHASE: E2E FRONTEND PLAYWRIGHT TESTING]

You are running end-to-end Playwright tests against the REAL frontend application.
These tests open a REAL browser, navigate pages, click buttons, fill forms, and verify results.

INSTRUCTIONS:
1. Install Playwright if not already installed:
   npx playwright install chromium
2. Read {requirements_dir}/REQUIREMENTS.md to understand ALL user-facing features
3. BEFORE writing any Playwright test, update {requirements_dir}/E2E_COVERAGE_MATRIX.md:
   - If the matrix already exists (from backend phase), ADD a Frontend Route Coverage section
   - If it doesn't exist, CREATE it with Frontend Route Coverage table:
     Route | Component | Key Workflows | Test File | Tested | Passed
   - Add a Cross-Role Workflows section covering multi-step UI workflows
   - All checkboxes start as [ ]

4. As you write each Playwright test:
   - Update the corresponding row: mark Tested as [x], add test file name

5. After running tests:
   - Update Passed column: [x] for passing, [ ] for failing
   - Update coverage summary

6. You CANNOT declare this phase complete with unchecked Tested rows in the frontend section.

7. Scan {frontend_directory} for pages, components, and router config
8. Update E2E test plan in {requirements_dir}/E2E_TEST_PLAN.md with frontend scenarios
9. Write Playwright test files in tests/e2e/browser/ as .spec.ts files
   - Use page.getByRole(), page.getByText(), page.getByTestId() selectors
   - NEVER use CSS class selectors (fragile)
   - Use webServer config in playwright.config.ts for auto-start:
     webServer: {{ command: '{start_command}', port: {test_port}, reuseExistingServer: true }}
   - Run in headless mode
   - Take screenshot on failure: use test.afterEach for screenshot capture
10. Run: npx playwright test --reporter=list
11. Append results to {requirements_dir}/E2E_RESULTS.md:
   ## Frontend Playwright Tests
   Total: N | Passed: P | Failed: F

   ### Passed
   - ✓ test_name: description

   ### Failed
   - ✗ test_name: error description

Framework: {framework}

Continue fixing until all tests pass or max retries exhausted. Do not stop early.

PRD FEATURE COVERAGE (MANDATORY):

A. ROUTE COMPLETENESS: Extract EVERY route from the router config (app.routes.ts,
   router/index.ts, urls.py, or equivalent). The test plan must navigate to EVERY
   defined route. Any route leading to blank page, error page, or unrendered
   component is a TEST FAILURE.

B. PLACEHOLDER DETECTION (HARD FAILURE): If any page, tab, section, or dialog
   contains text matching ANY of these patterns, it is a HARD FAILURE:
   - "will be implemented" / "coming soon" / "placeholder"
   - "TODO" or "FIXME" visible to the user
   - "not yet available" / "future milestone" / "under construction"
   - "Lorem ipsum" (design placeholder text left in production)
   - Empty content areas where the PRD specifies functionality
   The Playwright test must assert that NO visible text on any tested page matches
   these patterns.

C. DEAD COMPONENT DETECTION: After writing all tests, verify: are there components
   in the source tree that are never reached by any test navigation? Flag as
   "UNREACHABLE COMPONENT: {{name}} — not navigable from any tested route." This is
   a WARNING (not blocking) but MUST be reported.
   EXCLUSIONS — Do NOT flag these as unreachable:
   - Components in shared/, common/, layout/, ui/, or utils/ directories
   - Components named: Loader, Spinner, Loading, Error, ErrorBoundary, Layout,
     Wrapper, Modal, Dialog, Toast, Notification, Skeleton, Tooltip, Popover,
     Dropdown, Header, Footer, Sidebar, Nav, Breadcrumb, Badge, Avatar, Icon,
     Provider, Context, Store, Hook
   - Components imported by other components (render inside parents, not via navigation)
   - Guard/interceptor/pipe/directive files (framework utilities)
   FOCUS on PAGE-LEVEL and FEATURE-LEVEL components only — those representing
   user-facing functionality in pages/, features/, views/, routes/, or screens/.

D. INTERACTION DEPTH: Multi-step workflows must be tested through EVERY step:
   - Wizard with N steps → click Next through all N, verify each step renders content
   - Multi-tab interface → click every tab, verify content
   - Dialog with form → open, fill, submit, verify result
   - CRUD feature → Create, Read, Update, AND Delete (not just Read)
   A 10-step wizard verified by screenshotting step 1 is a TEST FAILURE.

E. FORM SUBMISSION VERIFICATION: For every form in the app:
   - Fill all required fields with valid data
   - Submit the form
   - Verify submission succeeded (success toast, redirect, data in list, or API response)
   Do NOT just verify the form renders — verify it SUBMITS and the data PERSISTS.

F. MULTI-ROLE NAVIGATION (MANDATORY if app has authentication):
   - Login as EACH role, verify correct dashboard/menu/sidebar renders
   - For each role, navigate to every page that role should access — verify content loads
   - Test restricted pages are NOT accessible by wrong roles → verify redirect (not crash)
   - If app has separate portals (e.g., bidder vs admin), test BOTH as
     separate Playwright suites with their own login flows

[ORIGINAL USER REQUEST]
{task_text}"""

E2E_FIX_PROMPT = """\
[PHASE: E2E TEST FIX — {test_type}]

E2E tests have failures that need to be fixed. The PRIMARY target is the APPLICATION code,
not the tests.

Failed tests:
{failures}

INSTRUCTIONS:
0. FIRST: Read {requirements_dir}/E2E_COVERAGE_MATRIX.md to understand which specific
   tests are failing and which requirements they cover. This tells you WHAT to fix.

   ALSO: Read {requirements_dir}/FIX_CYCLE_LOG.md (if it exists) to see what previous
   fix cycles attempted. DO NOT repeat a strategy that already failed.

   After completing your fix:
   - Update E2E_COVERAGE_MATRIX.md: mark fixed tests as [x] Passed, keep failing tests as [ ]
   - Append to FIX_CYCLE_LOG.md with: root cause, files modified, strategy used, result

1. Read the full test output and each failing test file
2. For each failure, determine root cause:
   a. Is the APP code wrong? → Fix the app
   b. Is the TEST expectation wrong? → See TEST CORRECTION EXCEPTION below
3. Deploy debugger to analyze failure root cause
4. Deploy code-writer to fix the APP code
5. Re-run the failing tests to verify fixes
6. Update {requirements_dir}/E2E_RESULTS.md with new results

Fix the APP, not the tests. The tests represent correct expected behavior.

Continue until all tests pass or max retries exhausted. Do not stop early.

PATTERN-SPECIFIC FIX GUIDANCE:

When analyzing failures, check for these patterns BEFORE attempting fixes:

1. PLACEHOLDER FAILURES: If test found placeholder text ("will be implemented",
   "coming soon", etc.), the fix is NOT to remove the text — it is to IMPLEMENT
   THE FEATURE. Deploy code-writer to build the actual component.
   SIZE GATE: If feature is a single component (<50 lines), implement it.
   If feature is a full page/module, report as "UNIMPLEMENTED FEATURE: {{name}}"
   in E2E_RESULTS.md — do not waste fix cycles on it.

2. ROLE ACCESS FAILURES (403): If a role got 403 Forbidden on an endpoint it
   should access:
   - Check backend auth middleware/decorator for that endpoint
   - Verify the role is included in allowed roles list
   - Fix the BACKEND authorization, not the test
   - Common pattern: endpoint under /admin/ route but non-admin roles need access
     → either move endpoint or add role to auth list

3. DEAD NAVIGATION: If component exists but isn't reachable through navigation:
   - Check if component is imported in parent module
   - Check if route exists pointing to it
   - Fix the WIRING — add route, add import, add the button/link that navigates
   - Do NOT delete the component

4. INCOMPLETE WIZARD/FORM: If test failed at step N of multi-step workflow:
   - Steps before N work. Focus on step N only.
   - Check if "Next" button is wired to advance the stepper
   - Check if step N's component is imported and rendered
   - Check if the API call at step N matches expected request/response shape

SEVERITY CLASSIFICATION for fix priority:
- IMPLEMENT: Missing feature (placeholder) → code-writer builds it
- FIX_AUTH: Role access bug → code-writer fixes middleware/guards
- FIX_WIRING: Dead navigation → code-writer adds routes/imports
- FIX_LOGIC: Step N fails → debugger diagnoses, code-writer fixes

TEST CORRECTION EXCEPTION:
The default rule is: fix the APP, not the test. But there is ONE exception:
If the debugger determines that the app behavior is CORRECT and the test
expectation is WRONG, the test may be fixed instead. Examples:
- Test expects "7 scenarios" but app correctly shows 9 (app updated, test wasn't)
- Test looks for "Submit" but app correctly uses "Save Changes"
- Test asserts redirect to /dashboard but app correctly redirects to /home
- Test expects 5 table rows but app correctly shows 3 (test data was wrong)

When correcting a test:
- Document as "TEST CORRECTION: {{reason}}" in E2E_RESULTS.md
- Explain WHY the app is correct and the test was wrong
- Fix the assertion to match actual correct behavior

GUARD RAIL: If more than 20% of fixes in a single run are test corrections
(not app fixes), STOP and report: "WARNING: High test correction rate ({{X}}%).
Test planner may need improvement — tests are not matching actual app behavior."

[ORIGINAL USER REQUEST]
{task_text}"""
