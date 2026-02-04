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
import os
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
    contracts_passed: bool | None = None  # None = not run, False = failed, True = passed
    build_passed: bool | None = None  # None = not applicable / not run
    lint_passed: bool | None = None  # None = not applicable / not run
    type_check_passed: bool | None = None
    tests_passed: bool | None = None
    security_passed: bool | None = None
    test_quality_score: float | None = None
    quality_health: str = "clean"  # "clean" | "minor" | "needs-attention"
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
    run_build: bool = True,
    run_lint: bool = True,
    run_type_check: bool = True,
    run_tests: bool = True,
    run_security: bool = True,
    run_quality_checks: bool = True,
    *,
    blocking: bool = True,
    min_test_count: int = 0,
    milestone_id: str | None = None,
) -> TaskVerificationResult:
    """Run the 7-phase verification pipeline for a completed task.

    Phase order (fastest first):
        0. Requirements compliance -- deterministic.
        0b. Test file existence gate -- deterministic.
        1. Contract check  -- BLOCKING. Deterministic, no LLM.
        1.5. Build check   -- BLOCKING. Runs build command.
        2. Lint/format     -- BLOCKING for errors, ADVISORY for warnings.
        3. Type check      -- BLOCKING.
        4. Test subset     -- BLOCKING.
        4.5. Test quality  -- ADVISORY. Checks assertion depth.
        5. Security audit  -- ADVISORY. Dependency/secret checks.
        6. Spot checks     -- ADVISORY. Anti-pattern regex checks.

    Returns a ``TaskVerificationResult`` with an overall status computed
    from all phases that were executed.
    """
    result = TaskVerificationResult(task_id=task_id)
    issues: list[str] = []

    # Phase 0: Requirements compliance (always runs, deterministic) -------
    req_result = _check_requirements_compliance(project_root, milestone_id=milestone_id)
    if req_result and not req_result.passed:
        issues.append(f"Requirements: {req_result.details}")

    # Phase 0b: Test file existence gate -----------------------------------
    test_gate = _check_test_files_exist(project_root)
    if test_gate and not test_gate.passed:
        issues.append(f"Test gate: {test_gate.details}")

    # Phase 1: Contract check (always runs, deterministic) ----------------
    if registry.file_missing:
        # No CONTRACTS.json on disk — this is NOT a pass, it's a warning.
        result.contracts_passed = None  # None = not applicable / skipped
        issues.append(
            "Contract: WARNING — No CONTRACTS.json found. "
            "Contract verification skipped (this is NOT a pass). "
            "Deploy the contract-generator agent to create CONTRACTS.json."
        )
    else:
        contract_result = verify_all_contracts(registry, project_root)
        result.contracts_passed = contract_result.passed
        if not contract_result.passed:
            for violation in contract_result.violations:
                issues.append(
                    f"Contract: {violation.description} ({violation.file_path})"
                )

    # Phase 1.5: Build check (Root Cause #4) ------------------------------
    if run_build:
        try:
            build_cmd = _detect_build_command(project_root)
            if build_cmd:
                returncode, stdout, stderr = await _run_command(build_cmd, project_root)
                result.build_passed = returncode == 0
                if not result.build_passed:
                    output = (stderr[:_MAX_OUTPUT_PREVIEW] or stdout[:_MAX_OUTPUT_PREVIEW]).strip()
                    issues.append(f"Build failed: {output}")
        except Exception as exc:
            issues.append(f"Build check failed: {exc}")

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

    # Phase 4.5: Test quality gate (Root Cause #6) -------------------------
    if run_tests:
        try:
            quality_result = _check_test_quality(project_root, min_test_count=min_test_count)
            if quality_result:
                result.test_quality_score = quality_result.get("score", 0.0)
                if quality_result.get("issues"):
                    for qi in quality_result["issues"]:
                        issues.append(f"Test quality: {qi}")
        except Exception as exc:
            issues.append(f"Test quality check failed: {exc}")

    # Phase 5: Security audit (Root Cause #5) ------------------------------
    if run_security:
        try:
            security_issues = await _run_security_checks(project_root)
            if security_issues:
                result.security_passed = False
                for si in security_issues:
                    issues.append(f"Security: {si}")
            else:
                result.security_passed = True
        except Exception as exc:
            issues.append(f"Security check failed: {exc}")

    # Phase 6: Anti-pattern spot checks (Root Cause #11) -------------------
    if run_quality_checks:
        try:
            from .quality_checks import run_spot_checks
            violations = run_spot_checks(project_root)
            if violations:
                for v in violations[:10]:  # Cap advisory output
                    issues.append(f"Quality: [{v.check}] {v.message} ({v.file_path}:{v.line})")
                # Compute quality health from violation count
                quality_violations_count = len(
                    [v for v in violations if v.severity in ("error", "warning")]
                )
                if quality_violations_count == 0:
                    result.quality_health = "clean"
                elif quality_violations_count <= 3:
                    result.quality_health = "minor"
                else:
                    result.quality_health = "needs-attention"
        except Exception:
            pass  # quality_checks unavailable or failed — non-blocking

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
    if result.build_passed is False:
        return fail_status
    if result.tests_passed is False:
        return fail_status  # contracts pass + tests fail = FAIL (RED) when blocking
    if result.lint_passed is False:
        return fail_status
    if result.type_check_passed is False:
        return fail_status
    # Security is advisory — does not block (only downgrades to partial)
    # if result.security_passed is False: treated as partial, not fail

    # Determine how many phases actually ran.
    phases = [
        result.contracts_passed,
        result.build_passed,
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


def _check_requirements_compliance(
    project_root: Path,
    *,
    milestone_id: str | None = None,
) -> StructuredReviewResult | None:
    """Check if the project satisfies declared technologies in REQUIREMENTS.md.

    When *milestone_id* is provided the per-milestone REQUIREMENTS.md is
    used instead of the global one.

    Returns ``None`` if no REQUIREMENTS.md exists (nothing to check).
    Otherwise returns a ``StructuredReviewResult`` with phase="requirements".
    """
    if milestone_id:
        req_path = project_root / ".agent-team" / "milestones" / milestone_id / "REQUIREMENTS.md"
    else:
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


def _load_original_task_text(project_root: Path) -> str | None:
    """Load the original task text from STATE.json if available."""
    state_path = project_root / ".agent-team" / "STATE.json"
    if not state_path.is_file():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data.get("task", None)
    except (json.JSONDecodeError, OSError):
        return None


_TEST_KEYWORDS_RE = re.compile(
    r'\b(tests?|testing|test suite|test cases?|unit tests?|integration tests?|'
    r'e2e tests?|end.to.end tests?|spec files?)\b',
    re.IGNORECASE,
)

_TEST_COUNT_RE = re.compile(r'\d+\+?\s*tests?', re.IGNORECASE)


def _check_test_files_exist(project_root: Path) -> StructuredReviewResult | None:
    """Check if tests are required by the original task but no test files exist.

    Reads both the original task text (from STATE.json) and REQUIREMENTS.md
    to determine if tests were requested. If so, verifies at least one test
    file exists in the project.

    Returns ``None`` if tests are not required.
    """
    # Gather text sources that might mention testing
    sources: list[str] = []

    # Check original task text
    task_text = _load_original_task_text(project_root)
    if task_text:
        sources.append(task_text)

    # Check REQUIREMENTS.md
    req_path = project_root / ".agent-team" / "REQUIREMENTS.md"
    if req_path.is_file():
        try:
            sources.append(req_path.read_text(encoding="utf-8"))
        except OSError:
            pass

    if not sources:
        return None

    combined = " ".join(sources).lower()

    # Check for test keywords or test count patterns
    has_test_keywords = bool(_TEST_KEYWORDS_RE.search(combined))
    has_test_count = bool(_TEST_COUNT_RE.search(combined))

    if not has_test_keywords and not has_test_count:
        return None

    # Tests are required — check if any test files exist
    has_tests = (
        any((project_root / d).is_dir() for d in ("tests", "test", "__tests__", "spec"))
        or any(project_root.rglob("*.test.*"))
        or any(project_root.rglob("*.spec.*"))
        or any(project_root.rglob("test_*.py"))
    )

    if has_tests:
        return StructuredReviewResult(
            phase="test_gate",
            passed=True,
            details="Test files found (test requirement satisfied)",
            blocking=False,
        )

    # Determine which source mentioned tests
    source_hint = "original task and/or REQUIREMENTS.md"
    if task_text and _TEST_KEYWORDS_RE.search(task_text.lower()):
        source_hint = "original user request"
    elif not task_text:
        source_hint = "REQUIREMENTS.md"

    return StructuredReviewResult(
        phase="test_gate",
        passed=False,
        details=(
            f"Tests required by {source_hint} but no test files found. "
            "Expected at least one of: tests/, test/, __tests__/, spec/ directory, "
            "or files matching *.test.*, *.spec.*, test_*.py"
        ),
        blocking=True,
    )


# ---------------------------------------------------------------------------
# Command detection helpers
# ---------------------------------------------------------------------------


def _detect_build_command(project_root: Path) -> list[str] | None:
    """Detect build command from project configuration.

    Checks (in order):
        1. ``package.json`` ``scripts.build``
        2. ``package.json`` ``scripts.tsc`` (explicit TypeScript build)
        3. ``pyproject.toml`` ``[build-system]``

    Note: ``tsconfig.json`` alone is NOT enough — ``tsc --noEmit``
    is already handled by the type-check phase. Build means producing
    output artifacts, which requires an explicit build script.
    """
    # Node / npm projects
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                scripts = data.get("scripts")
                if isinstance(scripts, dict):
                    if "build" in scripts:
                        return ["npm", "run", "build"]
                    if "tsc" in scripts:
                        return ["npm", "run", "tsc"]
        except (json.JSONDecodeError, OSError):
            pass

    # Python build (pyproject.toml with build-system)
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            content = pyproject.read_text(encoding="utf-8")
            if "[build-system]" in content:
                return ["python", "-m", "build", "--no-isolation"]
        except OSError:
            pass

    return None


def _check_test_quality(
    project_root: Path,
    *,
    min_test_count: int = 0,
) -> dict | None:
    """Check test quality beyond mere existence (Root Cause #6).

    Parses test files and checks:
    - At least 1 expect()/assert per test function (not empty tests)
    - No test.skip / xit / xdescribe (skipped tests)
    - Minimum test count threshold
    Returns dict with 'score' and 'issues' list, or None if no test files found.
    """
    test_dirs = ["tests", "test", "__tests__", "spec"]
    test_patterns = ["*.test.*", "*.spec.*", "test_*.py"]

    test_files: list[Path] = []
    for d in test_dirs:
        test_dir = project_root / d
        if test_dir.is_dir():
            for pattern in ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]:
                test_files.extend(test_dir.glob(pattern))

    for pattern in test_patterns:
        test_files.extend(project_root.rglob(pattern))

    # Deduplicate
    test_files = list({f.resolve(): f for f in test_files if f.is_file()}.values())

    if not test_files:
        return None

    issues: list[str] = []
    total_tests = 0
    empty_tests = 0
    skipped_tests = 0

    # Patterns for detecting test functions/assertions
    py_test_func = re.compile(r"^\s*(?:def|async\s+def)\s+(test_\w+)", re.MULTILINE)
    py_assert = re.compile(r"\b(?:assert|assertEqual|assertTrue|assertFalse|assertRaises|assertIn)\b")
    js_test_func = re.compile(r"(?<!\w)(?:it|test)\s*\(", re.MULTILINE)
    js_assert = re.compile(r"\b(?:expect|assert|should)\s*\(")
    skip_pattern = re.compile(r"(?:\btest\.skip\b|\bxit\b|\bxdescribe\b|\bxtest\b|@pytest\.mark\.skip|@skip)")

    for test_file in test_files[:50]:  # Cap to avoid excessive scanning
        try:
            content = test_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        is_python = test_file.suffix == ".py"

        if is_python:
            funcs = py_test_func.findall(content)
            total_tests += len(funcs)
            for func_name in funcs:
                # Extract function body (simple heuristic: lines until next def or end)
                func_start = content.find(f"def {func_name}")
                if func_start == -1:
                    func_start = content.find(f"async def {func_name}")
                if func_start >= 0:
                    next_def_sync = content.find("\ndef ", func_start + 10)
                    next_def_async = content.find("\nasync def ", func_start + 10)
                    candidates = [p for p in (next_def_sync, next_def_async) if p > 0]
                    next_def = min(candidates) if candidates else -1
                    body = content[func_start:next_def] if next_def > 0 else content[func_start:]
                    if not py_assert.search(body):
                        empty_tests += 1
        else:
            funcs = js_test_func.findall(content)
            total_tests += len(funcs)
            if funcs and not js_assert.search(content):
                empty_tests += len(funcs)

        skips = skip_pattern.findall(content)
        skipped_tests += len(skips)

    if empty_tests > 0:
        issues.append(f"{empty_tests} test(s) have no assertions (empty/shallow tests)")
    if skipped_tests > 0:
        issues.append(f"{skipped_tests} test(s) are skipped (test.skip/xit/xdescribe)")
    if min_test_count > 0 and total_tests < min_test_count:
        issues.append(f"Only {total_tests} tests found, minimum required: {min_test_count}")

    # Compute score: 1.0 = perfect, 0.0 = no tests
    if total_tests > 0:
        effective = total_tests - empty_tests - skipped_tests
        score = max(0.0, effective / total_tests)
    else:
        score = 0.0

    return {"score": score, "issues": issues, "total": total_tests, "empty": empty_tests, "skipped": skipped_tests}


async def _run_security_checks(project_root: Path) -> list[str]:
    """Run security checks on the project (Root Cause #5).

    Checks:
    1. npm audit / pip audit for dependency vulnerabilities
    2. .env files committed (should be in .gitignore)
    3. Hardcoded secrets (regex for API keys, passwords)
    """
    issues: list[str] = []

    # Check for .env files that might be committed
    env_files = list(project_root.glob("**/.env"))
    env_files += list(project_root.glob("**/.env.*"))
    # Filter out node_modules, .git, etc.
    env_files = [
        f for f in env_files
        if "node_modules" not in str(f) and ".git" not in str(f)
    ]
    if env_files:
        gitignore = project_root / ".gitignore"
        gitignore_content = ""
        if gitignore.is_file():
            try:
                gitignore_content = gitignore.read_text(encoding="utf-8")
            except OSError:
                pass
        if ".env" not in gitignore_content:
            issues.append(
                f"Found {len(env_files)} .env file(s) and .env is not in .gitignore"
            )

    # Check for hardcoded secrets in source files
    secret_patterns = [
        (re.compile(r'(?:api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9_-]{20,}["\']', re.IGNORECASE), "API key"),
        (re.compile(r'(?:password|passwd|secret)\s*[:=]\s*["\'][^"\']{8,}["\']', re.IGNORECASE), "password/secret"),
        (re.compile(r'(?:sk-|pk_live_|sk_live_|rk_live_)[a-zA-Z0-9]{20,}'), "Stripe/OpenAI key"),
        (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "GitHub personal access token"),
        (re.compile(r'(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}["\']'), "AWS secret"),
    ]

    source_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml"}
    skip_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".next", "venv", ".env"}

    for dirpath, dirnames, filenames in os.walk(project_root):
        # Prune skip directories in-place (prevents descent)
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.suffix not in source_extensions:
                continue
            try:
                if file_path.stat().st_size > 100_000:  # Skip large files
                    continue
            except OSError:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pattern, label in secret_patterns:
                if pattern.search(content):
                    rel = file_path.relative_to(project_root)
                    issues.append(f"Possible hardcoded {label} in {rel}")
                    break  # One issue per file is enough

    # Run npm audit if applicable
    if (project_root / "package-lock.json").is_file() or (project_root / "package.json").is_file():
        try:
            returncode, stdout, stderr = await _run_command(
                ["npm", "audit", "--audit-level=high", "--json"],
                project_root,
                timeout=60,
            )
            if returncode != 0 and stdout:
                try:
                    audit_data = json.loads(stdout)
                    vulns = audit_data.get("metadata", {}).get("vulnerabilities", {})
                    high = vulns.get("high", 0)
                    critical = vulns.get("critical", 0)
                    if high + critical > 0:
                        issues.append(f"npm audit: {critical} critical, {high} high vulnerabilities")
                except (json.JSONDecodeError, KeyError):
                    pass
        except Exception:
            pass  # npm audit is best-effort

    return issues


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
    """Resolve command to full path, trying .cmd and common paths on Windows.

    Resolution order:
    1. shutil.which(exe) — standard PATH lookup
    2. shutil.which(exe + ".cmd") — Windows .cmd extension fallback
    3. Common Windows installation paths for Node.js tools
    """
    import os as _os

    exe = cmd[0]
    resolved = shutil.which(exe)
    if resolved:
        return [resolved] + cmd[1:]

    if sys.platform == "win32":
        # Try .cmd extension (npm, npx ship as .cmd on Windows)
        resolved = shutil.which(exe + ".cmd")
        if resolved:
            return [resolved] + cmd[1:]

        # Try common Windows installation directories
        common_paths = [
            Path(_os.environ.get("ProgramFiles", "")) / "nodejs",
            Path(_os.environ.get("APPDATA", "")) / "npm",
            Path(_os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs",
            Path(_os.environ.get("LOCALAPPDATA", "")) / "fnm_multishells",
        ]
        for ext in ("", ".cmd", ".exe"):
            for p in common_paths:
                if not p or str(p) == ".":
                    continue
                candidate = p / (exe + ext)
                if candidate.is_file():
                    return [str(candidate)] + cmd[1:]

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
        # Last-resort fallback on Windows: try shell=True which uses
        # cmd.exe to resolve PATH differently than shutil.which.
        if sys.platform == "win32":
            try:
                process = await asyncio.create_subprocess_shell(
                    " ".join(cmd),
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
            except (asyncio.TimeoutError, FileNotFoundError, OSError):
                pass
        path_info = os.environ.get("PATH", "(empty)")
        return (
            1, "",
            f"Command not found: {cmd[0]}. "
            f"Tried: {' '.join(resolved_cmd)}. "
            f"PATH dirs: {path_info[:500]}"
        )
    except OSError as exc:
        return (1, "", f"OS error running command: {exc}")


# ---------------------------------------------------------------------------
# Verification summary output
# ---------------------------------------------------------------------------


def write_verification_summary(
    state: ProgressiveVerificationState,
    path: Path,
    *,
    milestone_id: str | None = None,
) -> None:
    """Write verification state to ``.agent-team/VERIFICATION.md``.

    When *milestone_id* is provided, writes to
    ``.agent-team/milestones/{milestone_id}/VERIFICATION.md`` instead.

    Creates the parent directory if it does not exist. The output
    format is a Markdown document with a summary table and issue list.
    """
    if milestone_id:
        path = path.parent / "milestones" / milestone_id / "VERIFICATION.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Verification Summary")
    lines.append("")
    lines.append(f"Overall Health: **{state.overall_health.upper()}**")
    lines.append("")

    # Completed tasks table ------------------------------------------------
    lines.append("## Completed Tasks")
    lines.append("")
    lines.append("| Task | Contracts | Build | Lint | Types | Tests | Security | Overall |")
    lines.append("|------|-----------|-------|------|-------|-------|----------|---------|")

    for task_id in sorted(state.completed_tasks.keys()):
        result = state.completed_tasks[task_id]
        lines.append(
            f"| {task_id} "
            f"| {_fmt_phase(result.contracts_passed)} "
            f"| {_fmt_phase(result.build_passed)} "
            f"| {_fmt_phase(result.lint_passed)} "
            f"| {_fmt_phase(result.type_check_passed)} "
            f"| {_fmt_phase(result.tests_passed)} "
            f"| {_fmt_phase(result.security_passed)} "
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
