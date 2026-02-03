"""Anti-pattern spot checker for Agent Team (Agent 19).

Scans project source files for common anti-patterns using compiled regex
patterns and returns a list of violations.  Each check targets a specific
anti-pattern from the code quality standards (FRONT-xxx, BACK-xxx, SLOP-xxx).

All checks are regex-based, require no external dependencies (stdlib only),
and are designed to run quickly as a non-blocking advisory phase inside the
progressive verification pipeline (see ``verification.py`` Phase 6).

Typical usage::

    from pathlib import Path
    from agent_team.quality_checks import run_spot_checks

    violations = run_spot_checks(Path("/path/to/project"))
    for v in violations:
        print(f"[{v.check}] {v.message} at {v.file_path}:{v.line}")
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Violation:
    """A single anti-pattern violation detected during spot checking."""

    check: str       # e.g. "FRONT-007", "BACK-002", "SLOP-003"
    message: str     # Human-readable description
    file_path: str   # Relative path to the file (POSIX-normalized)
    line: int        # Line number where the pattern was found
    severity: str    # "error" | "warning" | "info"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_VIOLATIONS = 100

_MAX_FILE_SIZE = 100_000  # 100 KB — skip files larger than this

_SKIP_DIRS: frozenset[str] = frozenset({
    "node_modules",
    ".git",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "venv",
})

_SEVERITY_ORDER: dict[str, int] = {
    "error": 0,
    "warning": 1,
    "info": 2,
}


# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level for reuse)
# ---------------------------------------------------------------------------

# FRONT-007: TypeScript `any` type usage
_RE_TS_ANY = re.compile(r":\s*any\b")

# BACK-002: N+1 query patterns (for-await loops or await-find-for patterns)
_RE_N_PLUS_1_FOR_AWAIT = re.compile(r"for[\s(].*await\s")
_RE_N_PLUS_1_AWAIT_FIND = re.compile(r"await.*\.find.*for")

# BACK-001: SQL string concatenation (injection risk)
_RE_SQL_CONCAT_PREFIX = re.compile(
    r"\+\s*['\"].*(?:SELECT|INSERT|UPDATE|DELETE)", re.IGNORECASE
)
_RE_SQL_CONCAT_SUFFIX = re.compile(
    r"(?:SELECT|INSERT|UPDATE|DELETE).*['\"]\s*\+", re.IGNORECASE
)

# FRONT-010: console.log in production code
_RE_CONSOLE_LOG = re.compile(r"console\.log\(")

# SLOP-003: Generic/overused fonts
_RE_GENERIC_FONT = re.compile(
    r"(?:font-family|fontFamily).*(?:Inter|Roboto|Arial)", re.IGNORECASE
)

# SLOP-001: Default/generic Tailwind colors (indigo/blue 500/600)
_RE_DEFAULT_TAILWIND = re.compile(r"bg-(?:indigo|blue)-(?:500|600)")

# Patterns to identify test files (excluded from FRONT-010)
_RE_TEST_FILE = re.compile(
    r"(?:\.test\.|\.spec\.|__tests__|\.stories\.|test_)", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# File extension sets for each check
# ---------------------------------------------------------------------------

_EXT_TYPESCRIPT: frozenset[str] = frozenset({".ts", ".tsx"})
_EXT_BACKEND: frozenset[str] = frozenset({".ts", ".js", ".py"})
_EXT_JS_ALL: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx"})
_EXT_STYLE: frozenset[str] = frozenset({".css", ".scss", ".ts", ".tsx"})
_EXT_TEMPLATE: frozenset[str] = frozenset({".ts", ".tsx", ".jsx", ".html"})


# ---------------------------------------------------------------------------
# Private check helpers
# ---------------------------------------------------------------------------


def _check_ts_any(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """FRONT-007: Detect TypeScript `any` type usage.

    Flags lines containing `: any` in .ts and .tsx files.  This is an error
    because ``any`` defeats the type system entirely.
    """
    if extension not in _EXT_TYPESCRIPT:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_TS_ANY.search(line):
            violations.append(Violation(
                check="FRONT-007",
                message="TypeScript `any` type detected — use `unknown`, generics, or specific types",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
    return violations


def _check_n_plus_1(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """BACK-002: Detect N+1 query patterns.

    Flags ``for ... await`` loops and ``await ... .find ... for`` patterns in
    backend source files (.ts, .js, .py).  These typically indicate a loop
    that issues one query per iteration instead of batching.
    """
    if extension not in _EXT_BACKEND:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_N_PLUS_1_FOR_AWAIT.search(line) or _RE_N_PLUS_1_AWAIT_FIND.search(line):
            violations.append(Violation(
                check="BACK-002",
                message="Possible N+1 query pattern — use batch fetches, JOINs, or DataLoader",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
    return violations


def _check_sql_concat(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """BACK-001: Detect SQL string concatenation (injection risk).

    Flags lines that concatenate string literals containing SQL keywords
    (SELECT, INSERT, UPDATE, DELETE) with the ``+`` operator.  This is
    an error because it opens the door to SQL injection.
    """
    if extension not in _EXT_BACKEND:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_SQL_CONCAT_PREFIX.search(line) or _RE_SQL_CONCAT_SUFFIX.search(line):
            violations.append(Violation(
                check="BACK-001",
                message="SQL string concatenation detected — use parameterized queries",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
    return violations


def _check_console_log(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """FRONT-010: Detect console.log in non-test production files.

    Flags ``console.log(`` calls in .ts, .tsx, .js, .jsx files, excluding
    test files (identified by name patterns like ``.test.``, ``.spec.``,
    ``__tests__``, ``.stories.``, ``test_``).
    """
    if extension not in _EXT_JS_ALL:
        return []

    # Skip test/story files
    if _RE_TEST_FILE.search(rel_path):
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_CONSOLE_LOG.search(line):
            violations.append(Violation(
                check="FRONT-010",
                message="console.log found in non-test file — use structured logging",
                file_path=rel_path,
                line=lineno,
                severity="info",
            ))
    return violations


def _check_generic_fonts(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """SLOP-003: Detect generic/overused fonts.

    Flags font-family or fontFamily declarations that reference Inter,
    Roboto, or Arial in .css, .scss, .ts, and .tsx files.  These are the
    default fonts that every tutorial uses and signal a lack of intentional
    design.
    """
    if extension not in _EXT_STYLE:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_GENERIC_FONT.search(line):
            violations.append(Violation(
                check="SLOP-003",
                message="Generic/overused font detected (Inter/Roboto/Arial) — use a distinctive typeface",
                file_path=rel_path,
                line=lineno,
                severity="info",
            ))
    return violations


def _check_default_tailwind_colors(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """SLOP-001: Detect default/generic Tailwind colors.

    Flags ``bg-indigo-500``, ``bg-indigo-600``, ``bg-blue-500``, and
    ``bg-blue-600`` classes in .ts, .tsx, .jsx, and .html files.  These
    are the default Tailwind hero colors that signal copy-paste from docs.
    """
    if extension not in _EXT_TEMPLATE:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_DEFAULT_TAILWIND.search(line):
            violations.append(Violation(
                check="SLOP-001",
                message="Default Tailwind color (indigo/blue-500/600) — use project-specific palette",
                file_path=rel_path,
                line=lineno,
                severity="info",
            ))
    return violations


# ---------------------------------------------------------------------------
# All checks registry (order does not matter — output is sorted by severity)
# ---------------------------------------------------------------------------

_ALL_CHECKS = [
    _check_ts_any,
    _check_n_plus_1,
    _check_sql_concat,
    _check_console_log,
    _check_generic_fonts,
    _check_default_tailwind_colors,
]

# Union of all file extensions any check cares about (for fast pre-filter)
_ALL_EXTENSIONS: frozenset[str] = (
    _EXT_TYPESCRIPT
    | _EXT_BACKEND
    | _EXT_JS_ALL
    | _EXT_STYLE
    | _EXT_TEMPLATE
)


# ---------------------------------------------------------------------------
# File traversal helpers
# ---------------------------------------------------------------------------


def _should_skip_dir(name: str) -> bool:
    """Return True if a directory named *name* should be skipped."""
    return name in _SKIP_DIRS


def _should_scan_file(path: Path) -> bool:
    """Return True if *path* is a regular file worth scanning.

    Skips files whose extension is not relevant to any check, and files
    exceeding ``_MAX_FILE_SIZE`` (to avoid scanning generated bundles).
    """
    if path.suffix not in _ALL_EXTENSIONS:
        return False
    try:
        if path.stat().st_size > _MAX_FILE_SIZE:
            return False
    except OSError:
        return False
    return True


def _iter_source_files(project_root: Path) -> list[Path]:
    """Walk *project_root* and return scannable source files.

    Skips directories listed in ``_SKIP_DIRS`` and files that fail the
    ``_should_scan_file`` predicate.  Uses ``os.walk`` for efficient
    directory pruning (avoids descending into ``node_modules`` etc.).
    """
    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(project_root):
        # Prune skip directories in-place (prevents os.walk from descending)
        dirnames[:] = [
            d for d in dirnames if not _should_skip_dir(d)
        ]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if _should_scan_file(file_path):
                files.append(file_path)

    return files


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_spot_checks(project_root: Path) -> list[Violation]:
    """Scan *project_root* for anti-patterns and return violations.

    Walks the project tree (skipping ``node_modules``, ``.git``,
    ``__pycache__``, ``dist``, ``build``, ``.next``, ``venv``), reads
    each relevant source file, and runs all registered checks.

    Returns violations sorted by severity (error > warning > info), then
    by file path, then by line number.  The list is capped at
    ``_MAX_VIOLATIONS`` (100) to avoid flooding downstream consumers.
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)

    for file_path in source_files:
        # Early exit if we already have enough violations
        if len(violations) >= _MAX_VIOLATIONS:
            break

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = file_path.relative_to(project_root).as_posix()
        extension = file_path.suffix

        for check_fn in _ALL_CHECKS:
            file_violations = check_fn(content, rel_path, extension)
            violations.extend(file_violations)

            # Re-check cap after each check function
            if len(violations) >= _MAX_VIOLATIONS:
                break

    # Trim to cap (a check function may have pushed us over)
    violations = violations[:_MAX_VIOLATIONS]

    # Sort: severity (error first), then file path, then line number
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )

    return violations
