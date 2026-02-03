"""Progressive verification pipeline for Agent Team.

Provides a 4-phase verification pipeline that validates task completions
through contract checks, linting, type checking, and testing. Each phase
runs in order from fastest to slowest, with all phases blocking by default.

The pipeline maintains a progressive verification state that tracks the
health of the overall project as tasks are completed and verified.

Health model:
    - green:  all completed tasks pass
    - yellow: some warnings but no blocking failures
    - red:    any blocking failure (including contracts pass + tests fail)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import sys

from .contracts import (
    ContractRegistry,
    verify_all_contracts,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_OUTPUT_PREVIEW = 500


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class StructuredReviewResult:
    """Result from a single automated review phase (lint, type check, or test)."""

    phase: str  # "contract" | "lint" | "type" | "test"
    passed: bool
    details: str
    blocking: bool  # True = must fix before proceeding


@dataclass
class TaskVerificationResult:
    """Aggregated verification result for a single task."""

    task_id: str
    contracts_passed: bool = False
    lint_passed: bool | None = None  # None = not applicable / not run
    type_check_passed: bool | None = None
    tests_passed: bool | None = None
    overall: str = "pass"  # "pass" | "fail" | "partial"
    issues: list[str] = field(default_factory=list)


@dataclass
class ProgressiveVerificationState:
    """Tracks verification health across all completed tasks."""

    completed_tasks: dict[str, TaskVerificationResult] = field(default_factory=dict)
    pending_contracts: list[str] = field(default_factory=list)
    overall_health: str = "green"  # "green" | "yellow" | "red"


# ---------------------------------------------------------------------------
# Core verification pipeline
# ---------------------------------------------------------------------------


async def verify_task_completion(
    task_id: str,
    project_root: Path,
    registry: ContractRegistry,
    run_lint: bool = True,
    run_type_check: bool = True,
    run_tests: bool = True,
    *,
    blocking: bool = True,
) -> TaskVerificationResult:
    """Run the 4-phase verification pipeline for a completed task.

    Phase order (fastest first):
        1. Contract check  -- BLOCKING. Deterministic, no LLM.
        2. Lint/format     -- BLOCKING for errors, ADVISORY for warnings.
        3. Type check      -- BLOCKING.
        4. Test subset     -- BLOCKING.

    Returns a ``TaskVerificationResult`` with an overall status computed
    from all phases that were executed.
    """
    result = TaskVerificationResult(task_id=task_id)
    issues: list[str] = []

    # Phase 0: Requirements compliance (always runs, deterministic) -------
    req_result = _check_requirements_compliance(project_root)
    if req_result and not req_result.passed:
        issues.append(f"Requirements: {req_result.details}")

    # Phase 1: Contract check (always runs, deterministic) ----------------
    contract_result = verify_all_contracts(registry, project_root)
    result.contracts_passed = contract_result.passed
    if not contract_result.passed:
        for violation in contract_result.violations:
            issues.append(
                f"Contract: {violation.description} ({violation.file_path})"
            )

    # Phase 2: Lint (if enabled) ------------------------------------------
    if run_lint:
        lint_cmd = _detect_lint_command(project_root)
        if lint_cmd:
            returncode, stdout, stderr = await _run_command(lint_cmd, project_root)
            result.lint_passed = returncode == 0
            if not result.lint_passed:
                output = (stderr[:_MAX_OUTPUT_PREVIEW] or stdout[:_MAX_OUTPUT_PREVIEW]).strip()
                issues.append(f"Lint failed: {output}")

    # Phase 3: Type check (if enabled) ------------------------------------
    if run_type_check:
        type_cmd = _detect_type_check_command(project_root)
        if type_cmd:
            returncode, stdout, stderr = await _run_command(type_cmd, project_root)
            result.type_check_passed = returncode == 0
            if not result.type_check_passed:
                output = (stderr[:_MAX_OUTPUT_PREVIEW] or stdout[:_MAX_OUTPUT_PREVIEW]).strip()
                issues.append(f"Type check failed: {output}")

    # Phase 4: Tests (if enabled) -----------------------------------------
    if run_tests:
        test_cmd = _detect_test_command(project_root)
        if test_cmd:
            returncode, stdout, stderr = await _run_command(test_cmd, project_root)
            result.tests_passed = returncode == 0
            if not result.tests_passed:
                output = (stderr[:_MAX_OUTPUT_PREVIEW] or stdout[:_MAX_OUTPUT_PREVIEW]).strip()
                issues.append(f"Tests failed: {output}")

    result.issues = issues
    result.overall = compute_overall_status(result, blocking=blocking)
    return result


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------


def compute_overall_status(result: TaskVerificationResult, *, blocking: bool = True) -> str:
    """Compute overall status from individual phase results.

    Rules:
        - Any phase explicitly fails -> ``"fail"`` (or ``"partial"`` when *blocking* is False)
        - All executed phases pass    -> ``"pass"``
        - Mix of pass/None (some phases not run) -> ``"partial"``
        - No phases ran at all        -> ``"partial"``

    IMPORTANT: contracts pass + tests fail = ``"fail"`` (behavioral
    regression overrides structural satisfaction).

    When *blocking* is ``False``, failures are downgraded to ``"partial"``
    instead of ``"fail"``, allowing the pipeline to continue with warnings.
    """
    fail_status = "fail" if blocking else "partial"

    # Check blocking failures first.
    if result.contracts_passed is False:
        return fail_status
    if result.tests_passed is False:
        return fail_status  # contracts pass + tests fail = FAIL (RED) when blocking
    if result.lint_passed is False:
        return fail_status
    if result.type_check_passed is False:
        return fail_status

    # Determine how many phases actually ran.
    phases = [
        result.contracts_passed,
        result.lint_passed,
        result.type_check_passed,
        result.tests_passed,
    ]
    ran = [p for p in phases if p is not None]
    if not ran:
        return "partial"
    if all(p for p in ran):
        return "pass"
    return "partial"


# ---------------------------------------------------------------------------
# Progressive state management
# ---------------------------------------------------------------------------


def update_verification_state(
    state: ProgressiveVerificationState,
    result: TaskVerificationResult,
) -> ProgressiveVerificationState:
    """Update the progressive verification state with a new task result.

    Health rules:
        - green:  all completed tasks pass
        - yellow: some warnings but no blocking failures
        - red:    any blocking failure
        - IMPORTANT: contracts pass + tests fail = RED
          (behavioral regression overrides structural satisfaction)
    """
    state.completed_tasks[result.task_id] = result
    state.overall_health = _health_from_results(state.completed_tasks)
    return state


def _health_from_results(
    results: dict[str, TaskVerificationResult],
) -> str:
    """Compute health from all task results.

    - If any task has overall == ``"fail"``    -> ``"red"``
    - If any task has overall == ``"partial"``  -> ``"yellow"``
    - Otherwise                                -> ``"green"``
    """
    if not results:
        return "green"
    for _task_id, result in results.items():
        if result.overall == "fail":
            return "red"
    for _task_id, result in results.items():
        if result.overall == "partial":
            return "yellow"
    return "green"


# ---------------------------------------------------------------------------
# Automated review phases (lint, type check, test)
# ---------------------------------------------------------------------------


async def run_automated_review_phases(
    project_root: Path,
    run_lint: bool = True,
    run_type_check: bool = True,
    run_tests: bool = True,
) -> list[StructuredReviewResult]:
    """Run lint, type check, and test phases independently.

    For each phase:
        1. Detect the appropriate command from project configuration.
        2. Run the command via ``asyncio.create_subprocess_exec``.
        3. Capture stdout/stderr.
        4. Parse exit code (0 = pass, non-zero = fail).
        5. Return ``StructuredReviewResult``.

    If a tool is not found for a phase, that phase is skipped (not
    included in the returned list).
    """
    results: list[StructuredReviewResult] = []

    if run_lint:
        lint_cmd = _detect_lint_command(project_root)
        if lint_cmd:
            returncode, stdout, stderr = await _run_command(lint_cmd, project_root)
            results.append(
                StructuredReviewResult(
                    phase="lint",
                    passed=returncode == 0,
                    details=(stderr or stdout).strip()[:500],
                    blocking=returncode != 0,
                )
            )

    if run_type_check:
        type_cmd = _detect_type_check_command(project_root)
        if type_cmd:
            returncode, stdout, stderr = await _run_command(type_cmd, project_root)
            results.append(
                StructuredReviewResult(
                    phase="type",
                    passed=returncode == 0,
                    details=(stderr or stdout).strip()[:500],
                    blocking=returncode != 0,
                )
            )

    if run_tests:
        test_cmd = _detect_test_command(project_root)
        if test_cmd:
            returncode, stdout, stderr = await _run_command(test_cmd, project_root)
            results.append(
                StructuredReviewResult(
                    phase="test",
                    passed=returncode == 0,
                    details=(stderr or stdout).strip()[:500],
                    blocking=returncode != 0,
                )
            )

    return results


# ---------------------------------------------------------------------------
# Requirements compliance check
# ---------------------------------------------------------------------------


def _check_requirements_compliance(project_root: Path) -> StructuredReviewResult | None:
    """Check if the project satisfies declared technologies in REQUIREMENTS.md.

    Returns ``None`` if no REQUIREMENTS.md exists (nothing to check).
    Otherwise returns a ``StructuredReviewResult`` with phase="requirements".
    """
    req_path = project_root / ".agent-team" / "REQUIREMENTS.md"
    if not req_path.is_file():
        return None

    try:
        req_content = req_path.read_text(encoding="utf-8")
    except OSError:
        return None

    if not req_content.strip():
        return None

    issues: list[str] = []

    # --- Technology presence check ---
    tech_re = re.compile(
        r'\b(Express(?:\.js)?|React(?:\.js)?|Next\.js|Vue(?:\.js)?|Angular|'
        r'Node\.js|Django|Flask|FastAPI|Spring\s*Boot|Rails|Laravel|'
        r'MongoDB|PostgreSQL|MySQL|SQLite|Redis|Supabase|Firebase|'
        r'TypeScript|GraphQL|REST\s*API|gRPC|WebSocket|'
        r'Tailwind(?:\s*CSS)?|Prisma|Drizzle|Sequelize|TypeORM|Mongoose)\b',
        re.IGNORECASE,
    )
    declared_techs = set(m.group(1).lower() for m in tech_re.finditer(req_content))

    if declared_techs:
        pkg_json = project_root / "package.json"
        pkg_content = ""
        if pkg_json.is_file():
            try:
                pkg_content = pkg_json.read_text(encoding="utf-8").lower()
            except OSError:
                pass

        pyproject = project_root / "pyproject.toml"
        pyproject_content = ""
        if pyproject.is_file():
            try:
                pyproject_content = pyproject.read_text(encoding="utf-8").lower()
            except OSError:
                pass

        all_deps = pkg_content + pyproject_content
        for tech in sorted(declared_techs):
            # Normalize for dependency lookup
            lookup = tech.replace(".js", "").replace(" ", "").replace(".", "")
            if lookup not in all_deps and tech not in all_deps:
                issues.append(f"Technology '{tech}' declared in REQUIREMENTS.md but not found in dependencies")

    # --- Monorepo structure check ---
    req_lower = req_content.lower()
    if "monorepo" in req_lower:
        has_structure = (
            (project_root / "client").is_dir()
            or (project_root / "server").is_dir()
            or (project_root / "packages").is_dir()
            or (project_root / "apps").is_dir()
        )
        if not has_structure:
            issues.append("Monorepo declared in REQUIREMENTS.md but no client/, server/, packages/, or apps/ directory found")

    # --- Test files check ---
    if "testing" in req_lower or "test suite" in req_lower or re.search(r'\d+\+?\s*tests?', req_lower):
        has_tests = (
            any((project_root / d).is_dir() for d in ("tests", "test", "__tests__", "spec"))
            or any(project_root.rglob("*.test.*"))
            or any(project_root.rglob("*.spec.*"))
            or any(project_root.rglob("test_*.py"))
        )
        if not has_tests:
            issues.append("Testing mentioned in REQUIREMENTS.md but no test files or test directories found")

    if issues:
        return StructuredReviewResult(
            phase="requirements",
            passed=False,
            details="; ".join(issues),
            blocking=True,
        )

    return StructuredReviewResult(
        phase="requirements",
        passed=True,
        details="All declared requirements satisfied",
        blocking=False,
    )


# ---------------------------------------------------------------------------
# Command detection helpers
# ---------------------------------------------------------------------------


def _detect_lint_command(project_root: Path) -> list[str] | None:
    """Detect lint command from project configuration.

    Checks (in order):
        1. ``package.json`` ``scripts.lint``
        2. ``pyproject.toml`` ``[tool.ruff]``
        3. ``.eslintrc*`` files
        4. ``.flake8`` file
    """
    # Node / npm projects
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "lint" in data.get("scripts", {}):
                return ["npm", "run", "lint"]
        except (json.JSONDecodeError, OSError):
            pass

    # Python — ruff
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "[tool.ruff]" in content:
                return ["ruff", "check", "."]
        except OSError:
            pass

    # ESLint config files
    for name in (".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml"):
        if (project_root / name).is_file():
            return ["npx", "eslint", "."]

    # Flake8
    if (project_root / ".flake8").is_file():
        return ["flake8", "."]

    return None


def _detect_type_check_command(project_root: Path) -> list[str] | None:
    """Detect type check command from project configuration.

    Checks (in order):
        1. ``tsconfig.json``       -> ``tsc --noEmit``
        2. ``pyproject.toml`` ``[tool.mypy]`` -> ``mypy .``
        3. ``pyrightconfig.json``  -> ``pyright``
    """
    # TypeScript
    if (project_root / "tsconfig.json").is_file():
        return ["npx", "tsc", "--noEmit"]

    # Python — mypy
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "[tool.mypy]" in content:
                return ["mypy", "."]
        except OSError:
            pass

    # Pyright
    if (project_root / "pyrightconfig.json").is_file():
        return ["pyright"]

    return None


def _detect_test_command(project_root: Path) -> list[str] | None:
    """Detect test command from project configuration.

    Checks (in order):
        1. ``package.json`` ``scripts.test``
        2. ``pytest.ini`` or ``pyproject.toml`` ``[tool.pytest]``
        3. ``jest.config.*`` files
    """
    # Node / npm projects
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "test" in scripts:
                # Skip placeholder "test" scripts that just echo an error.
                test_val = scripts["test"]
                if "no test specified" not in test_val:
                    return ["npm", "test"]
        except (json.JSONDecodeError, OSError):
            pass

    # Python — pytest
    if (project_root / "pytest.ini").is_file():
        return ["pytest"]
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "[tool.pytest" in content:
                return ["pytest"]
        except OSError:
            pass

    # Jest
    for name in ("jest.config.js", "jest.config.ts", "jest.config.json"):
        if (project_root / name).is_file():
            return ["npx", "jest"]

    return None


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------


def _resolve_command(cmd: list[str]) -> list[str]:
    """Resolve command to full path, trying .cmd on Windows."""
    exe = cmd[0]
    resolved = shutil.which(exe)
    if resolved:
        return [resolved] + cmd[1:]
    if sys.platform == "win32":
        resolved = shutil.which(exe + ".cmd")
        if resolved:
            return [resolved] + cmd[1:]
    return cmd


async def _run_command(
    cmd: list[str],
    cwd: Path,
    timeout: int = 120,
) -> tuple[int, str, str]:
    """Run a command asynchronously and return (returncode, stdout, stderr).

    Uses ``asyncio.create_subprocess_exec`` with the given *timeout*
    (in seconds). If the process does not complete within *timeout*,
    it is killed and a non-zero return code is returned.

    Security note: ``create_subprocess_exec`` is used (not ``create_subprocess_shell``).
    This means *cmd* elements are passed directly to ``execve()`` without shell
    interpretation, so shell metacharacter injection is not possible.  All command
    lists are constructed internally from hardcoded strings by the ``_detect_*``
    helpers -- no user-controlled input flows into *cmd*.
    """
    resolved_cmd = _resolve_command(cmd)
    try:
        process = await asyncio.create_subprocess_exec(
            *resolved_cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )
        returncode = process.returncode if process.returncode is not None else 1
        return (
            returncode,
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
        )
    except asyncio.TimeoutError:
        # Kill the process if it timed out.
        try:
            process.kill()  # type: ignore[possibly-undefined]
        except (ProcessLookupError, OSError):
            pass
        return (1, "", f"Command timed out after {timeout}s: {' '.join(cmd)}")
    except FileNotFoundError:
        return (1, "", f"Command not found: {cmd[0]}")
    except OSError as exc:
        return (1, "", f"OS error running command: {exc}")


# ---------------------------------------------------------------------------
# Verification summary output
# ---------------------------------------------------------------------------


def write_verification_summary(
    state: ProgressiveVerificationState,
    path: Path,
) -> None:
    """Write verification state to ``.agent-team/VERIFICATION.md``.

    Creates the parent directory if it does not exist. The output
    format is a Markdown document with a summary table and issue list.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Verification Summary")
    lines.append("")
    lines.append(f"Overall Health: **{state.overall_health.upper()}**")
    lines.append("")

    # Completed tasks table ------------------------------------------------
    lines.append("## Completed Tasks")
    lines.append("")
    lines.append("| Task | Contracts | Lint | Types | Tests | Overall |")
    lines.append("|------|-----------|------|-------|-------|---------|")

    for task_id in sorted(state.completed_tasks.keys()):
        result = state.completed_tasks[task_id]
        lines.append(
            f"| {task_id} "
            f"| {_fmt_phase(result.contracts_passed)} "
            f"| {_fmt_phase(result.lint_passed)} "
            f"| {_fmt_phase(result.type_check_passed)} "
            f"| {_fmt_phase(result.tests_passed)} "
            f"| {result.overall.upper()} |"
        )

    lines.append("")

    # Issues section -------------------------------------------------------
    all_issues: list[tuple[str, str]] = []
    for task_id in sorted(state.completed_tasks.keys()):
        result = state.completed_tasks[task_id]
        for issue in result.issues:
            all_issues.append((task_id, issue))

    lines.append("## Issues")
    lines.append("")
    if all_issues:
        for task_id, issue in all_issues:
            lines.append(f"- {task_id}: {issue}")
    else:
        lines.append("No issues found.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_phase(value: bool | None) -> str:
    """Format a phase result for the summary table."""
    if value is None:
        return "N/A"
    return "PASS" if value else "FAIL"
