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

import collections
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScanScope:
    """Controls which files a scan examines.

    When passed to a scan function, limits scanning to the specified files
    instead of walking the entire project tree.  When ``None`` is passed
    (the default), scans behave identically to the original full-project mode.

    Attributes:
        mode: "full" (scan everything), "changed_only" (only changed files),
              or "changed_and_imports" (changed files + their importers).
        changed_files: Absolute paths of files changed since last commit.
    """

    mode: str = "full"
    changed_files: list[Path] = field(default_factory=list)


def compute_changed_files(project_root: Path) -> list[Path]:
    """Compute files changed since last commit + untracked new files.

    Uses ``git diff --name-only HEAD`` for modified files and
    ``git ls-files --others --exclude-standard`` for new untracked files.

    Returns absolute paths. Returns an empty list if:
    - Not a git repository
    - git is not available
    - Any subprocess error occurs

    An empty list signals the caller to fall back to full-project scanning.
    """
    try:
        diff_output = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=project_root,
            text=True,
            timeout=10,
            stderr=subprocess.DEVNULL,
        ).strip()
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=project_root,
            text=True,
            timeout=10,
            stderr=subprocess.DEVNULL,
        ).strip()
        files: list[Path] = []
        for line in (diff_output + "\n" + untracked).splitlines():
            line = line.strip()
            if line:
                files.append((project_root / line).resolve())
        return files
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []


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

# Directories that should be excluded from all filesystem scans.
# Third-party code (virtualenvs, node_modules, etc.) produces massive
# false-positive noise — scanning them wastes money on fix agents that
# correctly refuse to modify vendor files.
EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".venv", "venv", "node_modules", "__pycache__", ".git",
    "dist", "build", "vendor", ".tox", ".mypy_cache", ".pytest_cache",
    "site-packages", ".egg-info", ".next", "env", ".angular",
    "coverage", ".nuxt", ".output", ".svelte-kit",
})

# Mutable module-level skip set.  Starts as EXCLUDED_DIRS; callers can
# extend it via ``configure_scan_exclusions()`` to merge config-driven dirs.
_SKIP_DIRS: frozenset[str] = EXCLUDED_DIRS


def configure_scan_exclusions(extra_dirs: list[str] | None = None) -> None:
    """Merge user-configured exclusion directories into the module skip set.

    Call this once from the CLI before invoking any scan functions.
    The merged set is used by *all* scan functions (``_iter_source_files``,
    ``_should_skip_dir``, ``_path_in_excluded_dir``, and the XREF skip set).

    Args:
        extra_dirs: Additional directory names to exclude (from config
            ``post_orchestration_scans.scan_exclude_dirs``).  ``None`` or
            an empty list is a no-op.
    """
    global _SKIP_DIRS, _XREF_SKIP_PARTS  # noqa: PLW0603
    if extra_dirs:
        _SKIP_DIRS = EXCLUDED_DIRS | frozenset(extra_dirs)
    else:
        _SKIP_DIRS = EXCLUDED_DIRS
    # Keep XREF skip set in sync
    _XREF_SKIP_PARTS = _SKIP_DIRS | frozenset({".env"})


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

# BACK-016: Non-transactional multi-step writes
_RE_DELETE_MANY = re.compile(r"\.(?:deleteMany|delete)\s*\(", re.IGNORECASE)
_RE_CREATE_MANY = re.compile(r"\.(?:createMany|create)\s*\(", re.IGNORECASE)
_RE_TRANSACTION = re.compile(r"\$transaction|\btransaction\b|\.atomic\b|db\.session", re.IGNORECASE)

# BACK-018: Unvalidated route parameters
_RE_PARAM_PARSE = re.compile(r"(?:Number|parseInt|parseFloat)\s*\(\s*req\.params")
_RE_ISNAN = re.compile(r"\bisNaN\b")

# BACK-017: Validation result discarded
_RE_SCHEMA_PARSE_ASSIGNED = re.compile(
    r"(?:const|let|var|return|=)\s*.*(?:parse|safeParse|validate)\s*\(", re.IGNORECASE,
)

# MOCK-001: RxJS mock patterns in service files
_RE_RXJS_OF_MOCK = re.compile(r'\bof\s*\(\s*[\[\{]')
_RE_RXJS_DELAY_PIPE = re.compile(r'\.pipe\s*\([^)]*delay\s*\(')
_RE_MOCK_RETURN_OF = re.compile(r'return\s+of\s*\(')

# MOCK-002: Promise.resolve with hardcoded data
_RE_PROMISE_RESOLVE_MOCK = re.compile(r'Promise\.resolve\s*\(\s*[\[\{]')

# MOCK-003: Mock variable names
_RE_MOCK_VARIABLE = re.compile(
    r'\b(?:mock|fake|dummy|sample|stub|hardcoded)'
    r'(?:Data|Response|Result|Items|List|Array|Users|Tenders|Bids|Projects)\b',
    re.IGNORECASE,
)

# MOCK-004: setTimeout/setInterval simulating API responses
_RE_TIMEOUT_MOCK = re.compile(r'setTimeout\s*\(\s*(?:\(\s*\)\s*=>|function)')

# MOCK-005: delay() used to simulate network latency
_RE_DELAY_SIMULATE = re.compile(r'\bdelay\s*\(\s*\d+\s*\)')

# MOCK-006: BehaviorSubject with hardcoded initial data (non-null/non-empty)
_RE_BEHAVIOR_SUBJECT_MOCK = re.compile(
    r'new\s+BehaviorSubject\s*[<(]\s*[\[\{]',
)

# MOCK-007: new Observable returning hardcoded data
_RE_OBSERVABLE_MOCK = re.compile(
    r'new\s+Observable\s*[<(]\s*(?:\(\s*\w+\s*\)\s*=>|function)',
)

# MOCK-008: Hardcoded count/badge values in component files
_RE_HARDCODED_UI_COUNT = re.compile(
    r'(?:count|badge|notification|unread|pending|total(?:Count|Items|Results))\s*[:=]\s*[\'"]?\d+[\'"]?',
    re.IGNORECASE,
)

_RE_COMPONENT_PATH = re.compile(
    r'(?:component|page|view|screen|widget|panel|sidebar|topbar|navbar|header|footer|layout)',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# UI Compliance patterns (UI-001..004)
# ---------------------------------------------------------------------------

# UI-001: Hardcoded hex color in CSS/style attributes (not in config/variable files)
_RE_HARDCODED_HEX_CSS = re.compile(
    r'(?:color|background|border|fill|stroke)\s*:\s*#[0-9a-fA-F]{3,8}\b'
)
_RE_HARDCODED_HEX_STYLE = re.compile(
    r"(?:color|backgroundColor|borderColor|fill|stroke)\s*[:=]\s*['\"]#[0-9a-fA-F]{3,8}['\"]"
)

# UI-001b: Hardcoded hex in Tailwind arbitrary value classes
_RE_TAILWIND_ARBITRARY_HEX = re.compile(
    r'(?:bg|text|border|ring|shadow|fill|stroke)-\[#[0-9a-fA-F]{3,8}\]'
)

# UI-002: Default Tailwind colors (extended — indigo/violet/purple 400..700)
_RE_DEFAULT_TAILWIND_EXTENDED = re.compile(
    r'\b(?:bg|text|border|ring)-(?:indigo|violet|purple)-(?:4|5|6|7)00\b'
)

# UI-003: Generic fonts in config/theme files
_RE_GENERIC_FONT_CONFIG = re.compile(
    r"(?:fontFamily|font-family|fonts)\s*[:=].*\b(?:Inter|Roboto|Arial|Helvetica|system-ui)\b",
    re.IGNORECASE,
)

# UI-004: Arbitrary spacing not on 4px grid (odd pixel values in padding/margin/gap)
# Includes directional Tailwind variants: pt/pb/pl/pr, mt/mb/ml/mr
_RE_ARBITRARY_SPACING = re.compile(
    r'(?:padding|margin|gap)\s*:\s*(\d+)px|(?:p[tlbrxy]?-|m[tlbrxy]?-|space-[xy]-)(?:\[)?(\d+)(?:px)?(?:\])?'
)

# Config/theme file detection (exempt from hardcoded color checks)
# Uses path-segment boundaries to avoid matching component names like "ThemeToggle"
_RE_CONFIG_FILE = re.compile(
    r'(?:^|[/\\])(?:tailwind\.config|theme|variables|tokens|design[-_]system|_variables)(?:\.|[/\\]|$)',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# E2E Testing quality patterns (E2E-001..007)
# ---------------------------------------------------------------------------

# E2E-001: Hardcoded sleep/timeout in E2E tests (use waitFor instead)
_RE_E2E_SLEEP = re.compile(r'setTimeout\s*\(|time\.sleep\s*\(')

# E2E-002: Hardcoded port in E2E test files (use config/env)
_RE_E2E_HARDCODED_PORT = re.compile(r'localhost:\d{4}|127\.0\.0\.1:\d{4}')
# Exempt: references to env/config
_RE_E2E_PORT_EXEMPT = re.compile(r'(?:process\.env|BASE_URL|baseURL|BASE_URL|config\.|getenv)')

# E2E-003: Mock data in E2E tests (must use real calls)
_RE_E2E_MOCK_DATA = re.compile(
    r'\b(?:mockData|fakeResponse|Promise\.resolve\s*\(\s*\[)'
)

# E2E-004: Empty test body (no assertions)
_RE_E2E_EMPTY_TEST = re.compile(
    r'(?:test|it)\s*\([^,]+,\s*async\s*(?:\(\s*\)|\(\s*\{[^}]*\}\s*\))\s*=>\s*\{\s*\}\s*\)'
)

# E2E-005: Auth test presence check (inverted — warn if NOT found)
_RE_E2E_AUTH_TEST = re.compile(
    r'(?:test|it|describe)\s*\(\s*[\'"].*(?:login|auth|sign.?in)',
    re.IGNORECASE,
)

# E2E-006: Placeholder text in UI components
# NOTE: "placeholder" alone is NOT matched — it is a standard HTML attribute.
# We match "placeholder text/content" and other indicator phrases.
# The `.` wildcard intentionally matches any separator (space, underscore, dash).
_RE_E2E_PLACEHOLDER = re.compile(
    r'(?:placeholder.text|placeholder.content|coming.soon|will.be.implemented|future.milestone|under.construction|not.yet.available|lorem.ipsum)',
    re.IGNORECASE,
)
# Comment patterns to exclude from E2E-006
_RE_COMMENT_LINE = re.compile(r'^\s*(?://|#|/\*|\*|{/\*)')

# E2E-007: Role access failure in E2E results
_RE_E2E_ROLE_FAILURE = re.compile(r'(?:403|Forbidden|Unauthorized|Access.Denied)', re.IGNORECASE)

# Path patterns for E2E test directories
_RE_E2E_DIR = re.compile(r'(?:^|[/\\])(?:e2e|playwright)[/\\]', re.IGNORECASE)

# Path patterns for service/client files
_RE_SERVICE_PATH = re.compile(
    r'(?:services?|clients?|api|http|data-access|repositor|provider|store|facade|composable)',
    re.IGNORECASE,
)

# Function definition patterns for duplicate detection
_RE_FUNC_DEF_JS = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(|"
    r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:\(|=>)",
)
_RE_FUNC_DEF_PY = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)


# ---------------------------------------------------------------------------
# Dual ORM detection patterns (DB-001..003)
# ---------------------------------------------------------------------------

_RE_DB_SQL_STRING = re.compile(
    r"""(?:SELECT|INSERT|UPDATE|DELETE|WHERE|SET|JOIN)\s""",
    re.IGNORECASE,
)
_RE_DB_SQL_ENUM_INT_CMP = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*\d+""",
    re.IGNORECASE,
)
_RE_DB_SQL_ENUM_STR_CMP = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*['"]""",
    re.IGNORECASE,
)
_RE_DB_SQL_BOOL_INT = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*=\s*[01]\b""",
    re.IGNORECASE,
)
_RE_DB_SQL_DATETIME_FORMAT = re.compile(
    r"""(?:WHERE|AND|OR|SET)\s+\w+\s*(?:=|<|>|<=|>=|BETWEEN)\s*['"]?\d{4}[-/]\d{2}[-/]\d{2}""",
    re.IGNORECASE,
)
_RE_DB_CSHARP_ENUM_PROP = re.compile(
    r"""public\s+(\w+)\s+(\w+)\s*\{""",
)
_RE_DB_CSHARP_BOOL_PROP = re.compile(
    r"""public\s+bool\??\s+(\w+)\s*\{""",
)
_RE_DB_CSHARP_DATETIME_PROP = re.compile(
    r"""public\s+(?:DateTime|DateTimeOffset|DateOnly|TimeOnly)\??\s+(\w+)\s*\{""",
)
_EXT_ENTITY = frozenset({".cs", ".py", ".ts", ".js"})

# Common C# entity/navigation types to exclude from enum property detection
_CSHARP_NON_ENUM_TYPES = frozenset({
    "int", "long", "string", "bool", "decimal", "float",
    "double", "DateTime", "DateTimeOffset", "DateOnly", "TimeOnly",
    "Guid", "byte", "short", "byte[]",
    "ICollection", "IList", "List", "IEnumerable", "HashSet",
    "class", "interface", "struct", "enum", "record",
    "static", "abstract", "override", "async", "void", "virtual",
    "Task", "Action", "Func",
})

# Suffixes that indicate a type is NOT an enum (service, DTO, entity, etc.)
_CSHARP_NON_ENUM_SUFFIXES = (
    "Dto", "DTO", "Service", "Controller", "Repository",
    "Manager", "Handler", "Factory", "Builder", "Provider",
    "Validator", "Mapper", "Context", "Configuration",
    "Options", "Settings", "Response", "Request", "Command",
    "Query", "Event", "Exception", "Attribute", "Helper",
    "Model", "ViewModel", "Entity",
)

# ---------------------------------------------------------------------------
# Default value detection patterns (DB-004..005)
# ---------------------------------------------------------------------------

_RE_DB_CSHARP_BOOL_NO_DEFAULT = re.compile(
    r"""public\s+bool\s+(\w+)\s*\{\s*get;\s*(?:set|init|private\s+set|protected\s+set);\s*\}(?!\s*=)""",
)
_RE_DB_CSHARP_ENUM_NO_DEFAULT = re.compile(
    r"""public\s+(\w+)\s+(\w+)\s*\{\s*get;\s*(?:set|init|private\s+set|protected\s+set);\s*\}(?!\s*=)""",
)
_RE_DB_CSHARP_NULLABLE_PROP = re.compile(
    r"""public\s+(\w+)\?\s+(\w+)\s*\{""",
)
_RE_DB_PRISMA_NO_DEFAULT = re.compile(
    r"""(\w+)\s+(?:Boolean|Int)\s*$""",
    re.MULTILINE,
)
# Prisma String fields with status-like names that should have defaults
_RE_DB_PRISMA_STRING_STATUS_NO_DEFAULT = re.compile(
    r"""((?:status|state|type|role|category|priority|phase|level))\s+String\s*$""",
    re.MULTILINE | re.IGNORECASE,
)
# Prisma enum field without default: "status  TenderStatus" (type starts with uppercase, not a built-in)
_RE_DB_PRISMA_ENUM_NO_DEFAULT = re.compile(
    r"""(\w+)\s+([A-Z]\w+)\s*$""",
    re.MULTILINE,
)
_PRISMA_BUILTIN_TYPES = frozenset({
    "String", "Boolean", "Int", "BigInt", "Float", "Decimal",
    "DateTime", "Json", "Bytes",
})
_RE_DB_DJANGO_BOOL_NO_DEFAULT = re.compile(
    r"""BooleanField\s*\(\s*\)""",
)
_RE_DB_SQLALCHEMY_NO_DEFAULT = re.compile(
    r"""Column\s*\(\s*(?:Boolean|Enum)\b[^)]*\)""",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Relationship completeness patterns (DB-006..008)
# ---------------------------------------------------------------------------

_RE_DB_CSHARP_FK_PROP = re.compile(
    r"""public\s+(?:int|long|Guid|string)\??\s+(\w+Id)\s*\{""",
)
_RE_DB_CSHARP_NAV_PROP = re.compile(
    r"""public\s+(?:virtual\s+)?(?:(?:ICollection|IList|IEnumerable|List|HashSet)<(\w+)>\s+(\w+)|(\w+)\s+(\w+))\s*\{""",
)
_RE_DB_CSHARP_HAS_MANY = re.compile(
    r"""\.Has(?:Many|One)\s*\(\s*\w*\s*=>\s*\w+\.(\w+)\)""",
)
_RE_DB_TYPEORM_RELATION = re.compile(
    r"""@(?:ManyToOne|OneToMany|OneToOne|ManyToMany)\s*\(""",
)
_RE_DB_TYPEORM_JOIN_COLUMN = re.compile(
    r"""@JoinColumn\s*\(\s*\{[^}]*name\s*:\s*['"](\w+)['"]""",
)
_RE_DB_TYPEORM_RELATION_DETAIL = re.compile(
    r"""@(ManyToOne|OneToMany|OneToOne|ManyToMany)\s*\(\s*\(\)\s*=>\s*(\w+)""",
)
_RE_DB_DJANGO_FK = re.compile(
    r"""(?:ForeignKey|OneToOneField|ManyToManyField)\s*\(""",
)
_RE_DB_DJANGO_FK_DETAIL = re.compile(
    r"""(\w+)\s*=\s*models\.(?:ForeignKey|OneToOneField)\s*\(\s*['"]?(\w+)['"]?""",
)
_RE_DB_SQLALCHEMY_RELATIONSHIP = re.compile(
    r"""relationship\s*\(""",
)
_RE_DB_SQLALCHEMY_FK_COLUMN = re.compile(
    r"""(\w+)\s*=\s*Column\s*\([^)]*ForeignKey\s*\(\s*['"](\w+)\.(\w+)['"]""",
)
_RE_DB_SQLALCHEMY_RELATIONSHIP_DETAIL = re.compile(
    r"""(\w+)\s*=\s*relationship\s*\(\s*['"](\w+)['"]""",
)

# Entity/model file indicators
_RE_ENTITY_INDICATOR_CS = re.compile(
    r"""\[Table\]|\bDbContext\b|:\s*DbContext\b""",
)
_RE_ENTITY_INDICATOR_TS = re.compile(
    r"""@Entity\s*\(|Schema\s*\(""",
)
_RE_ENTITY_INDICATOR_PY = re.compile(
    r"""\bmodels\.Model\b|Base\.metadata|Base\s*=\s*declarative_base|class\s+\w+\s*\([^)]*Base[^)]*\)""",
)
_RE_ENTITY_DIR = re.compile(
    r"""(?:^|[/\\])(?:Entities|Models|Domain|entities|models)[/\\]""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File extension sets for each check
# ---------------------------------------------------------------------------

_EXT_TYPESCRIPT: frozenset[str] = frozenset({".ts", ".tsx"})
_EXT_BACKEND: frozenset[str] = frozenset({".ts", ".js", ".py"})
_EXT_JS_ALL: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx"})
_EXT_STYLE: frozenset[str] = frozenset({".css", ".scss", ".ts", ".tsx"})
_EXT_TEMPLATE: frozenset[str] = frozenset({".ts", ".tsx", ".jsx", ".html"})
_EXT_UI: frozenset[str] = frozenset({
    ".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".html",
})
_EXT_E2E: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx", ".py"})
_EXT_TEMPLATE_CONTENT: frozenset[str] = frozenset({
    ".tsx", ".jsx", ".vue", ".svelte", ".html", ".component.ts",
})


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


def _check_transaction_safety(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """BACK-016: Detect deleteMany followed by createMany without transaction wrapper.

    Scans for delete+create pairs within the same file and checks whether a
    $transaction or equivalent wrapper is present in the surrounding scope.
    """
    if extension not in _EXT_BACKEND:
        return []

    lines = content.splitlines()
    violations: list[Violation] = []

    for i, line in enumerate(lines):
        if _RE_DELETE_MANY.search(line):
            # Look ahead up to 20 lines for a create pattern
            window = "\n".join(lines[i:i + 20])
            if _RE_CREATE_MANY.search(window):
                # Check broader scope for transaction wrapper
                scope_start = max(0, i - 10)
                scope = "\n".join(lines[scope_start:i + 20])
                if not _RE_TRANSACTION.search(scope):
                    violations.append(Violation(
                        check="BACK-016",
                        message="Sequential delete + create without transaction — wrap in $transaction()",
                        file_path=rel_path,
                        line=i + 1,
                        severity="warning",
                    ))
    return violations


def _check_param_validation(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """BACK-018: Detect Number(req.params) or parseInt(req.params) without NaN check.

    Two-pass: find param parsing, then check next 5 lines for isNaN guard.
    """
    if extension not in _EXT_BACKEND:
        return []

    lines = content.splitlines()
    violations: list[Violation] = []

    for i, line in enumerate(lines):
        if _RE_PARAM_PARSE.search(line):
            # Check next 5 lines for isNaN guard
            window = "\n".join(lines[i:i + 6])
            if not _RE_ISNAN.search(window):
                violations.append(Violation(
                    check="BACK-018",
                    message="Route parameter parsed without NaN check — validate and return 400 on invalid",
                    file_path=rel_path,
                    line=i + 1,
                    severity="warning",
                ))
    return violations


def _check_validation_data_flow(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """BACK-017: Detect schema.parse(req.body) where result is not assigned.

    Flags statement-level calls to .parse() / .validate() that discard the
    return value (the sanitized/parsed data is not used downstream).
    """
    if extension not in _EXT_BACKEND:
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Check for parse/validate calls that are not assigned
        if ("parse(" in stripped or "validate(" in stripped) and "req." in stripped:
            if not _RE_SCHEMA_PARSE_ASSIGNED.search(stripped):
                if stripped.endswith(";") or stripped.endswith(")"):
                    violations.append(Violation(
                        check="BACK-017",
                        message="Validation result discarded — assign parsed data: `req.body = schema.parse(req.body)`",
                        file_path=rel_path,
                        line=lineno,
                        severity="warning",
                    ))
    return violations


def _check_mock_data_patterns(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """MOCK-001..007: Detect mock data patterns in service/client files.

    Flags RxJS of() with hardcoded data, Promise.resolve() with hardcoded data,
    mock variable naming patterns, delay() latency simulation, setTimeout-based
    API simulation, BehaviorSubject with hardcoded data, and new Observable
    returning mock data in service, client, API, and data access files.

    Excludes test files and files not in service-related paths.
    Scans both JS/TS and Python service files.
    """
    _mock_extensions = _EXT_JS_ALL | {".py"}
    if extension not in _mock_extensions:
        return []

    # Skip test files
    if _RE_TEST_FILE.search(rel_path):
        return []

    # Only scan service-related files
    if not _RE_SERVICE_PATH.search(rel_path):
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_RXJS_OF_MOCK.search(line):
            violations.append(Violation(
                check="MOCK-001",
                message="RxJS of() with hardcoded data in service file — must use real HTTP call",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_MOCK_RETURN_OF.search(line):
            violations.append(Violation(
                check="MOCK-001",
                message="Service method returns of() instead of real HTTP call",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_RXJS_DELAY_PIPE.search(line):
            violations.append(Violation(
                check="MOCK-001",
                message="RxJS delay() pipe simulating API latency — must use real HTTP call",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_PROMISE_RESOLVE_MOCK.search(line):
            violations.append(Violation(
                check="MOCK-002",
                message="Promise.resolve() with hardcoded data — must use real HTTP/fetch call",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_MOCK_VARIABLE.search(line):
            violations.append(Violation(
                check="MOCK-003",
                message="Mock/fake/dummy data variable in service file — replace with real API data",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_TIMEOUT_MOCK.search(line):
            violations.append(Violation(
                check="MOCK-004",
                message="setTimeout simulating async API in service — must use real HTTP call",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
        if _RE_DELAY_SIMULATE.search(line):
            violations.append(Violation(
                check="MOCK-005",
                message="delay() simulating network latency — suggests mock data pattern",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
        if _RE_BEHAVIOR_SUBJECT_MOCK.search(line):
            violations.append(Violation(
                check="MOCK-006",
                message="BehaviorSubject initialized with hardcoded data — use null + HTTP populate",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        if _RE_OBSERVABLE_MOCK.search(line):
            violations.append(Violation(
                check="MOCK-007",
                message="new Observable returning inline data — must use real HTTP call",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
    return violations


def _check_hardcoded_ui_counts(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """MOCK-008: Detect hardcoded count/badge values in component files.

    Scans component, page, view, and layout files for patterns like
    ``notificationCount = '3'`` or ``badgeCount = 5`` that indicate
    hardcoded display data instead of API-driven values.

    Only applies to JS/TS/Vue/Svelte component files. Test files are excluded.
    """
    _ui_extensions = _EXT_JS_ALL | {".vue", ".svelte"}
    if extension not in _ui_extensions:
        return []

    # Skip test files
    if _RE_TEST_FILE.search(rel_path):
        return []

    # Only scan component-related files
    if not _RE_COMPONENT_PATH.search(rel_path):
        return []

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _RE_HARDCODED_UI_COUNT.search(line):
            violations.append(Violation(
                check="MOCK-008",
                message="Hardcoded count/badge value in component — display counts must come from API or reactive state",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
    return violations


def _check_ui_compliance(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """UI-001..004: Detect UI compliance violations in component/style files.

    Checks for hardcoded colors, default Tailwind palettes, generic fonts,
    and arbitrary spacing in UI files. Config/theme files are exempt from
    color checks (they define tokens). Test files are skipped entirely.
    """
    if extension not in _EXT_UI:
        # Also check .component.ts (Angular) and config/theme .ts files
        if extension == ".ts" and (
            rel_path.endswith(".component.ts") or _RE_CONFIG_FILE.search(rel_path)
        ):
            pass  # Allow these .ts files through
        else:
            return []

    # Skip test files
    if _RE_TEST_FILE.search(rel_path):
        return []

    is_config_file = _RE_CONFIG_FILE.search(rel_path)

    violations: list[Violation] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        # UI-001: Hardcoded hex colors (skip config files — they define tokens)
        if not is_config_file:
            if _RE_HARDCODED_HEX_CSS.search(line):
                violations.append(Violation(
                    check="UI-001",
                    message="Hardcoded hex color in style — use design token variable instead",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))
            if _RE_HARDCODED_HEX_STYLE.search(line):
                violations.append(Violation(
                    check="UI-001",
                    message="Hardcoded hex color in inline style — use design token variable",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))
            # UI-001b: Tailwind arbitrary hex
            if _RE_TAILWIND_ARBITRARY_HEX.search(line):
                violations.append(Violation(
                    check="UI-001b",
                    message="Hardcoded hex in Tailwind arbitrary value — use theme color instead",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))

        # UI-002: Default Tailwind colors (always check, even in config)
        if _RE_DEFAULT_TAILWIND_EXTENDED.search(line):
            violations.append(Violation(
                check="UI-002",
                message="Default Tailwind color (indigo/violet/purple) — use project-specific palette",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))

        # UI-003: Generic fonts in config files
        if is_config_file and _RE_GENERIC_FONT_CONFIG.search(line):
            violations.append(Violation(
                check="UI-003",
                message="Generic font (Inter/Roboto/Arial) in config — use distinctive typeface",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))

        # UI-004: Arbitrary spacing (check non-grid values)
        match = _RE_ARBITRARY_SPACING.search(line)
        if match:
            try:
                # group(1) = CSS property value, group(2) = Tailwind class value
                raw = match.group(1) or match.group(2)
                if raw is not None:
                    value = int(raw)
                    # Allow 0 and multiples of 4 (4px grid) and common Tailwind values
                    if value > 0 and value % 4 != 0 and value not in (1, 2, 6, 10, 14):
                        violations.append(Violation(
                            check="UI-004",
                            message=f"Spacing value {value}px not on 4px grid — use grid-aligned value",
                            file_path=rel_path,
                            line=lineno,
                            severity="info",
                        ))
            except (ValueError, IndexError):
                pass

    return violations


def _check_e2e_quality(
    content: str,
    rel_path: str,
    extension: str,
) -> list[Violation]:
    """E2E-001..006: Detect quality issues in E2E test files and UI templates.

    E2E-001..004: Only targets files in e2e/, tests/e2e/, playwright/ directories.
    E2E-006: Targets UI template files (tsx, jsx, vue, svelte, html, component.ts)
    for placeholder text outside of comments.
    """
    violations: list[Violation] = []

    # --- E2E-006: Placeholder text in UI components (all template files) ---
    is_template_file = (
        extension in _EXT_TEMPLATE_CONTENT
        or rel_path.endswith(".component.ts")
    )
    if is_template_file and not _RE_E2E_DIR.search(rel_path):
        for lineno, line in enumerate(content.splitlines(), start=1):
            # Skip comment lines — placeholders in comments are fine
            if _RE_COMMENT_LINE.search(line):
                continue
            if _RE_E2E_PLACEHOLDER.search(line):
                violations.append(Violation(
                    check="E2E-006",
                    message="Placeholder text in UI component — implement the actual feature",
                    file_path=rel_path,
                    line=lineno,
                    severity="error",
                ))

    # --- E2E-001..004: Only E2E test directories ---
    if extension not in _EXT_E2E:
        return violations

    if not _RE_E2E_DIR.search(rel_path):
        return violations

    for lineno, line in enumerate(content.splitlines(), start=1):
        # E2E-001: Hardcoded sleep
        if _RE_E2E_SLEEP.search(line):
            violations.append(Violation(
                check="E2E-001",
                message="Hardcoded sleep/timeout in E2E test — use waitFor, waitForResponse, or waitForSelector",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
        # E2E-002: Hardcoded port
        if _RE_E2E_HARDCODED_PORT.search(line) and not _RE_E2E_PORT_EXEMPT.search(line):
            violations.append(Violation(
                check="E2E-002",
                message="Hardcoded port in E2E test — use configurable BASE_URL or process.env",
                file_path=rel_path,
                line=lineno,
                severity="warning",
            ))
        # E2E-003: Mock data in E2E
        if _RE_E2E_MOCK_DATA.search(line):
            violations.append(Violation(
                check="E2E-003",
                message="Mock data in E2E test — all calls must hit real server",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
        # E2E-004: Empty test body
        if _RE_E2E_EMPTY_TEST.search(line):
            violations.append(Violation(
                check="E2E-004",
                message="Empty E2E test body — every test must have meaningful assertions",
                file_path=rel_path,
                line=lineno,
                severity="error",
            ))
    return violations


def _check_gitignore(
    project_root: Path,
) -> list[Violation]:
    """Check for missing .gitignore or missing critical entries.

    This is a PROJECT-LEVEL check (not per-file). It checks:
    1. Whether .gitignore exists
    2. If so, whether it contains critical entries (node_modules, dist, .env)
    """
    violations: list[Violation] = []
    gitignore_path = project_root / ".gitignore"

    if not gitignore_path.is_file():
        violations.append(Violation(
            check="PROJ-001",
            message="Missing .gitignore file — add one with node_modules, dist, .env entries",
            file_path=".gitignore",
            line=0,
            severity="warning",
        ))
        return violations

    try:
        content = gitignore_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return violations

    critical_entries = ["node_modules", "dist", ".env"]
    for entry in critical_entries:
        if entry not in content:
            violations.append(Violation(
                check="PROJ-001",
                message=f".gitignore missing critical entry: {entry}",
                file_path=".gitignore",
                line=0,
                severity="warning",
            ))

    return violations


def _check_duplicate_functions(
    project_root: Path,
    source_files: list[Path],
) -> list[Violation]:
    """FRONT-016: Detect same function name defined in 2+ non-test files.

    This is a PROJECT-LEVEL check. Builds a function_name → [files] map
    and flags names that appear in 2+ files.
    """
    func_map: dict[str, list[str]] = {}

    for file_path in source_files:
        try:
            rel_path = file_path.relative_to(project_root).as_posix()
        except ValueError:
            rel_path = file_path.name

        if _RE_TEST_FILE.search(rel_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        extension = file_path.suffix
        found_names: set[str] = set()

        if extension in (".ts", ".tsx", ".js", ".jsx"):
            for match in _RE_FUNC_DEF_JS.finditer(content):
                name = match.group(1) or match.group(2)
                if name and len(name) > 2:  # Skip very short names
                    found_names.add(name)
        elif extension == ".py":
            for match in _RE_FUNC_DEF_PY.finditer(content):
                name = match.group(1)
                if name and not name.startswith("_") and len(name) > 2:
                    found_names.add(name)

        for name in found_names:
            func_map.setdefault(name, []).append(rel_path)

    violations: list[Violation] = []
    for name, files in sorted(func_map.items()):
        if len(files) >= 2:
            violations.append(Violation(
                check="FRONT-016",
                message=f"Duplicate function '{name}' defined in {len(files)} files: {', '.join(files[:3])}",
                file_path=files[0],
                line=0,
                severity="warning",
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
    _check_transaction_safety,
    _check_param_validation,
    _check_validation_data_flow,
    _check_mock_data_patterns,
    _check_hardcoded_ui_counts,
    _check_ui_compliance,
    _check_e2e_quality,
]

# Union of all file extensions any check cares about (for fast pre-filter)
_ALL_EXTENSIONS: frozenset[str] = (
    _EXT_TYPESCRIPT
    | _EXT_BACKEND
    | _EXT_JS_ALL
    | _EXT_STYLE
    | _EXT_TEMPLATE
    | _EXT_UI
    | _EXT_E2E
    | _EXT_ENTITY
)


# ---------------------------------------------------------------------------
# File traversal helpers
# ---------------------------------------------------------------------------


def _should_skip_dir(name: str) -> bool:
    """Return True if a directory named *name* should be skipped."""
    return name in _SKIP_DIRS


def _path_in_excluded_dir(file_path: Path) -> bool:
    """Return True if *file_path* has any excluded directory in its parts.

    Catches paths like ``.venv/Lib/site-packages/...`` where the parent
    dir was already pruned from ``os.walk`` but the file was discovered
    via ``rglob`` or ``glob`` which do NOT prune directories.
    """
    return any(part in _SKIP_DIRS for part in file_path.parts)


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

    Also runs project-level checks (gitignore, duplicate functions) that
    operate across files rather than per-file.

    Returns violations sorted by severity (error > warning > info), then
    by file path, then by line number.  The list is capped at
    ``_MAX_VIOLATIONS`` (100) to avoid flooding downstream consumers.
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)

    # --- Project-level checks ---
    violations.extend(_check_gitignore(project_root))
    violations.extend(_check_duplicate_functions(project_root, source_files))

    # --- Per-file checks ---
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


def run_mock_data_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Scan project for mock data patterns in service/client files.

    Unlike :func:`run_spot_checks` which runs ALL checks, this function runs
    ONLY mock data detection checks (MOCK-001..008).  Designed for targeted
    post-milestone scanning in ``cli.py``.

    Returns violations sorted by severity, capped at ``_MAX_VIOLATIONS``.
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        source_files = [f for f in source_files if f.resolve() in scope_set]

    for file_path in source_files:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = file_path.relative_to(project_root).as_posix()
        extension = file_path.suffix

        file_violations = _check_mock_data_patterns(content, rel_path, extension)
        file_violations.extend(_check_hardcoded_ui_counts(content, rel_path, extension))
        violations.extend(file_violations)

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


def run_ui_compliance_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Scan project for UI compliance violations in component/style files.

    Unlike :func:`run_spot_checks` which runs ALL checks, this function runs
    ONLY UI compliance checks (UI-001..004). Designed for targeted
    post-milestone scanning in ``cli.py``.

    Returns violations sorted by severity, capped at ``_MAX_VIOLATIONS``.
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        source_files = [f for f in source_files if f.resolve() in scope_set]

    for file_path in source_files:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = file_path.relative_to(project_root).as_posix()
        extension = file_path.suffix

        file_violations = _check_ui_compliance(content, rel_path, extension)
        violations.extend(file_violations)

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


def run_e2e_quality_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Scan project for E2E test quality issues.

    Runs E2E-001..006 checks on files in e2e/ and playwright/ directories
    and template files. Also runs:
    - E2E-005 (inverted): warns if app has auth but no auth E2E test found
    - E2E-007: scans E2E_RESULTS.md for role access failures (403/Forbidden)
    Returns violations sorted by severity, capped at _MAX_VIOLATIONS.
    """
    violations: list[Violation] = []
    all_source_files = _iter_source_files(project_root)
    # Scope filtering for per-file checks (E2E-001..004)
    scoped_files = all_source_files
    _scope_active = False
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        scoped_files = [f for f in all_source_files if f.resolve() in scope_set]
        _scope_active = True

    # Track whether any E2E test file contains auth tests (for E2E-005)
    # Use FULL file list for aggregate check to avoid false positives (H1 fix)
    has_auth_e2e_test = False
    has_e2e_tests = False

    # Per-file E2E quality checks on scoped files only
    for file_path in scoped_files:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = file_path.relative_to(project_root).as_posix()
        extension = file_path.suffix

        file_violations = _check_e2e_quality(content, rel_path, extension)
        violations.extend(file_violations)

        # Track auth test presence for E2E-005 inverted check
        if extension in _EXT_E2E and _RE_E2E_DIR.search(rel_path):
            has_e2e_tests = True
            if _RE_E2E_AUTH_TEST.search(content):
                has_auth_e2e_test = True

    # When scope is active, scan ALL e2e files for auth test presence
    # to avoid false-positive E2E-005 (H1 fix: unchanged auth test files
    # must still be visible for the aggregate check)
    if _scope_active and not has_auth_e2e_test:
        for file_path in all_source_files:
            try:
                rel_path = file_path.relative_to(project_root).as_posix()
                extension = file_path.suffix
                if extension in _EXT_E2E and _RE_E2E_DIR.search(rel_path):
                    has_e2e_tests = True
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    if _RE_E2E_AUTH_TEST.search(content):
                        has_auth_e2e_test = True
                        break
            except OSError:
                continue

    # --- E2E-005: Inverted auth test check ---
    # If app has auth dependencies but no auth E2E test, emit warning
    if has_e2e_tests and not has_auth_e2e_test:
        # Check if project has auth (look for common auth packages)
        _auth_indicators = (
            "passport", "jsonwebtoken", "jwt", "bcrypt", "@nestjs/jwt",
            "flask-login", "django.contrib.auth", "fastapi-users",
            "next-auth", "@auth/", "authjs", "firebase-auth",
        )
        pkg_json = project_root / "package.json"
        req_txt = project_root / "requirements.txt"
        has_auth = False
        for dep_file in (pkg_json, req_txt):
            if dep_file.is_file():
                try:
                    dep_content = dep_file.read_text(encoding="utf-8", errors="replace").lower()
                    if any(ind in dep_content for ind in _auth_indicators):
                        has_auth = True
                        break
                except OSError:
                    pass
        if has_auth:
            violations.append(Violation(
                check="E2E-005",
                message="No auth E2E test found — app has auth dependencies but no login/auth flow test in e2e/ directory",
                file_path="(project)",
                line=0,
                severity="warning",
            ))

    # --- E2E-007: Role access failure in E2E results ---
    results_path = project_root / ".agent-team" / "E2E_RESULTS.md"
    if results_path.is_file():
        try:
            results_content = results_path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(results_content.splitlines(), start=1):
                if _RE_E2E_ROLE_FAILURE.search(line):
                    violations.append(Violation(
                        check="E2E-007",
                        message="Role access failure detected in E2E results — check backend auth middleware/guards",
                        file_path=".agent-team/E2E_RESULTS.md",
                        line=lineno,
                        severity="error",
                    ))
        except OSError:
            pass

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


# ---------------------------------------------------------------------------
# Post-build integrity scans: Deployment, Asset, PRD reconciliation
# ---------------------------------------------------------------------------

# --- Deployment integrity patterns ---

_RE_APP_LISTEN_PORT = re.compile(
    r'\.listen\s*\(\s*(\d{2,5})'
    r'|uvicorn\.run.*port\s*=\s*(\d+)'
    r'|\.set\s*\(\s*[\'"]port[\'"]\s*,\s*(\d+)',
    re.IGNORECASE,
)
_RE_ENV_VAR_NODE = re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)')
_RE_ENV_VAR_PY = re.compile(
    r'os\.environ\s*\[\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]\s*\]'
    r'|os\.getenv\s*\(\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]'
    r'|os\.environ\.get\s*\(\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]'
)
_RE_ENV_WITH_DEFAULT = re.compile(
    r'process\.env\.\w+\s*(?:\|\||[?]{2})'
    r'|os\.getenv\s*\([^)]+,[^)]+\)'
    r'|os\.environ\.get\s*\([^)]+,[^)]+\)',
)
_BUILTIN_ENV_VARS: frozenset[str] = frozenset({
    "NODE_ENV", "PATH", "HOME", "USER", "SHELL", "TERM", "PWD",
    "HOSTNAME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP",
    "CI", "DEBUG", "VERBOSE", "LOG_LEVEL",
    # AI/LLM provider API keys — always host-provided secrets, never in docker-compose
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_API_KEY",
    "GOOGLE_API_KEY", "AZURE_OPENAI_API_KEY", "TOGETHER_API_KEY",
    "GROQ_API_KEY", "MISTRAL_API_KEY", "COHERE_API_KEY",
    "HUGGING_FACE_TOKEN", "HF_TOKEN",
})
_RE_CORS_ORIGIN = re.compile(
    r'cors\s*\(\s*\{[^}]*origin\s*:\s*[\'"]([^\'"\s]+)[\'"]'
    r'|CORS_ALLOWED_ORIGINS?\s*=\s*[\'"]([^\'"\s]+)[\'"]'
    r'|allow_origins\s*=\s*\[\s*[\'"]([^\'"\s]+)[\'"]'
    r'|enableCors\s*\(\s*\{[^}]*origin\s*:\s*[\'"]([^\'"\s]+)[\'"]',
    re.IGNORECASE | re.DOTALL,
)
_RE_DB_CONN_HOST = re.compile(
    r'mongodb://(?:\w+:?\w*@)?(\w[\w.-]*):'
    r'|postgres(?:ql)?://(?:\w+:?\w*@)?(\w[\w.-]*):'
    r'|mysql://(?:\w+:?\w*@)?(\w[\w.-]*):'
    r'|redis://(?:\w+:?\w*@)?(\w[\w.-]*):'
    r'|host\s*[:=]\s*[\'"](\w[\w.-]*)[\'"]',
    re.IGNORECASE,
)

# --- Asset integrity patterns ---

_RE_ASSET_SRC = re.compile(r'src\s*=\s*[\'"]([^\'"]+)[\'"]')
_RE_ASSET_HREF = re.compile(r'href\s*=\s*[\'"]([^\'"]+)[\'"]')
_RE_ASSET_CSS_URL = re.compile(r'url\(\s*[\'"]?([^)\'"\s]+)[\'"]?\s*\)')
_RE_ASSET_REQUIRE = re.compile(r'require\(\s*[\'"]([^\'"]+)[\'"]')
_RE_ASSET_IMPORT = re.compile(r'from\s+[\'"]([^\'"]+)[\'"]')

_ASSET_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".mp4", ".mp3", ".wav", ".ogg", ".webm",
})
_EXT_ASSET_SCAN: frozenset[str] = frozenset({
    ".tsx", ".jsx", ".vue", ".svelte", ".html", ".css", ".scss",
    ".ts", ".js", ".ejs", ".hbs", ".pug",
})


def _parse_docker_compose(project_root: Path) -> dict | None:
    """Parse docker-compose.yml/yaml, returning parsed dict or None."""
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        dc_path = project_root / name
        if dc_path.is_file():
            try:
                import yaml
                result = yaml.safe_load(dc_path.read_text(encoding="utf-8", errors="replace"))
                return result if isinstance(result, dict) else None
            except Exception:
                return None
    return None


def _parse_env_file(path: Path) -> set[str]:
    """Parse a .env file and return set of defined variable names."""
    env_vars: set[str] = set()
    if not path.is_file():
        return env_vars
    try:
        content = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip common 'export' prefix: export VAR=value (space or tab)
            if line.startswith(("export ", "export\t")):
                line = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                if key:
                    env_vars.add(key)
    except OSError:
        pass
    return env_vars


def _extract_docker_ports(dc: dict) -> dict[str, list[tuple[int, int]]]:
    """Extract port mappings from docker-compose services."""
    result: dict[str, list[tuple[int, int]]] = {}
    services = dc.get("services") or {}
    for svc_name, svc_config in services.items():
        if not isinstance(svc_config, dict):
            continue
        ports = svc_config.get("ports") or []
        mapped: list[tuple[int, int]] = []
        for p in ports:
            p_str = str(p).split("/")[0]  # strip protocol
            parts = p_str.split(":")
            try:
                if len(parts) == 2:
                    mapped.append((int(parts[0]), int(parts[1])))
                elif len(parts) == 3:
                    mapped.append((int(parts[1]), int(parts[2])))
                elif len(parts) == 1:
                    port = int(parts[0])
                    mapped.append((port, port))
            except (ValueError, IndexError):
                continue
        if mapped:
            result[svc_name] = mapped
    return result


def _extract_docker_env_vars(dc: dict) -> set[str]:
    """Extract all environment variable names from docker-compose services."""
    env_vars: set[str] = set()
    services = dc.get("services") or {}
    for _svc, svc_config in services.items():
        if not isinstance(svc_config, dict):
            continue
        env = svc_config.get("environment")
        if isinstance(env, dict):
            env_vars.update(env.keys())
        elif isinstance(env, list):
            for item in env:
                s = str(item)
                if "=" in s:
                    env_vars.add(s.split("=", 1)[0].strip())
                else:
                    env_vars.add(s.strip())
    return env_vars


def _extract_docker_service_names(dc: dict) -> set[str]:
    """Extract all service names from docker-compose."""
    return set((dc.get("services") or {}).keys())


def run_deployment_scan(project_root: Path) -> list[Violation]:
    """Scan for deployment config inconsistencies (DEPLOY-001..004).

    Only runs if docker-compose.yml/yaml exists. Returns warnings.
    """
    dc = _parse_docker_compose(project_root)
    if dc is None:
        return []

    violations: list[Violation] = []
    docker_ports = _extract_docker_ports(dc)
    docker_env = _extract_docker_env_vars(dc)
    docker_services = _extract_docker_service_names(dc)

    # Collect .env file vars
    for env_name in (
        ".env", ".env.example", ".env.local", ".env.development",
        ".env.production", ".env.staging", ".env.test",
    ):
        docker_env.update(_parse_env_file(project_root / env_name))

    container_ports: set[int] = set()
    for port_list in docker_ports.values():
        for _hp, cp in port_list:
            container_ports.add(cp)

    source_files = _iter_source_files(project_root)
    app_listen_ports: list[tuple[str, int, int]] = []
    cors_origins: list[tuple[str, int, str]] = []
    db_hosts: list[tuple[str, int, str]] = []
    env_usages: list[tuple[str, int, str]] = []

    for file_path in source_files:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel_path = file_path.relative_to(project_root).as_posix()

        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _RE_APP_LISTEN_PORT.search(line)
            if m:
                port_str = next((g for g in m.groups() if g), None)
                if port_str:
                    try:
                        app_listen_ports.append((rel_path, lineno, int(port_str)))
                    except ValueError:
                        pass

            m = _RE_CORS_ORIGIN.search(line)
            if m:
                origin = next((g for g in m.groups() if g), None)
                if origin:
                    cors_origins.append((rel_path, lineno, origin))

            m = _RE_DB_CONN_HOST.search(line)
            if m:
                host = next((g for g in m.groups() if g), None)
                if host and host not in ("localhost", "127.0.0.1", "0.0.0.0"):
                    db_hosts.append((rel_path, lineno, host))

            for env_m in _RE_ENV_VAR_NODE.finditer(line):
                if not _RE_ENV_WITH_DEFAULT.search(line):
                    env_usages.append((rel_path, lineno, env_m.group(1)))
            for env_m in _RE_ENV_VAR_PY.finditer(line):
                var = next((g for g in env_m.groups() if g), None)
                if var and not _RE_ENV_WITH_DEFAULT.search(line):
                    env_usages.append((rel_path, lineno, var))

    # DEPLOY-001: Port mismatch
    for rp, ln, port in app_listen_ports:
        if container_ports and port not in container_ports:
            violations.append(Violation(
                check="DEPLOY-001",
                message=f"Port mismatch: app listens on {port} but docker-compose container ports are {sorted(container_ports)}",
                file_path=rp, line=ln, severity="warning",
            ))

    # DEPLOY-002: Env var not defined
    all_defined = docker_env | _BUILTIN_ENV_VARS
    seen: set[str] = set()
    for rp, ln, var in env_usages:
        if var not in all_defined and var not in seen:
            seen.add(var)
            violations.append(Violation(
                check="DEPLOY-002",
                message=f"Environment variable {var} used but not defined in docker-compose or .env",
                file_path=rp, line=ln, severity="warning",
            ))

    # DEPLOY-003: CORS origin check
    for rp, ln, origin in cors_origins:
        if origin.startswith("http") and "localhost" not in origin and "*" not in origin:
            violations.append(Violation(
                check="DEPLOY-003",
                message=f"CORS origin '{origin}' — verify this matches the actual frontend deployment URL",
                file_path=rp, line=ln, severity="warning",
            ))

    # DEPLOY-004: Service name mismatch
    for rp, ln, host in db_hosts:
        if docker_services and host not in docker_services:
            violations.append(Violation(
                check="DEPLOY-004",
                message=f"Service name '{host}' in connection string not found in docker-compose services {sorted(docker_services)}",
                file_path=rp, line=ln, severity="warning",
            ))

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
    return violations


def _is_static_asset_ref(ref: str) -> bool:
    """Check if a reference points to a static asset file."""
    if not ref or ref.startswith(("http://", "https://", "//", "data:", "#", "mailto:")):
        return False
    if any(c in ref for c in ("${", "{%", "{{", "}}")):
        return False
    if ref.startswith(("@/", "~/", "~")):
        return False
    # Strip query string and hash fragment before checking extension
    clean = ref.split("?")[0].split("#")[0]
    return Path(clean).suffix.lower() in _ASSET_EXTENSIONS


def _resolve_asset(ref: str, file_dir: Path, project_root: Path) -> bool:
    """Try to resolve an asset reference to an existing file."""
    ref = ref.split("?")[0].split("#")[0]
    clean = ref.lstrip("/")
    candidates = [
        file_dir / ref,
        project_root / clean,
        project_root / "public" / clean,
        project_root / "src" / clean,
        project_root / "assets" / clean,
        project_root / "static" / clean,
        project_root / "src" / "assets" / clean,
    ]
    for c in candidates:
        try:
            if c.is_file():
                return True
        except (OSError, ValueError):
            continue
    return False


def run_asset_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Scan for broken static asset references (ASSET-001..003).

    Walks template/component files and checks that src, href, url(),
    require, and import references to static assets exist on disk.
    """
    violations: list[Violation] = []
    scope_set = set(f.resolve() for f in scope.changed_files) if scope and scope.changed_files else None

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for filename in filenames:
            if len(violations) >= _MAX_VIOLATIONS:
                break
            file_path = Path(dirpath) / filename
            if scope_set and file_path.resolve() not in scope_set:
                continue
            if file_path.suffix.lower() not in _EXT_ASSET_SCAN:
                continue
            try:
                if file_path.stat().st_size > _MAX_FILE_SIZE:
                    continue
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            rel_path = file_path.relative_to(project_root).as_posix()
            file_dir = file_path.parent
            ext = file_path.suffix.lower()

            for lineno, line in enumerate(content.splitlines(), start=1):
                # ASSET-001: src/href
                for regex in (_RE_ASSET_SRC, _RE_ASSET_HREF):
                    for m in regex.finditer(line):
                        ref = m.group(1)
                        if _is_static_asset_ref(ref) and not _resolve_asset(ref, file_dir, project_root):
                            violations.append(Violation(
                                check="ASSET-001",
                                message=f"Asset reference '{ref}' — file not found on disk",
                                file_path=rel_path, line=lineno, severity="warning",
                            ))
                # ASSET-002: CSS url()
                if ext in (".css", ".scss"):
                    for m in _RE_ASSET_CSS_URL.finditer(line):
                        ref = m.group(1)
                        if _is_static_asset_ref(ref) and not _resolve_asset(ref, file_dir, project_root):
                            violations.append(Violation(
                                check="ASSET-002",
                                message=f"CSS url() reference '{ref}' — file not found on disk",
                                file_path=rel_path, line=lineno, severity="warning",
                            ))
                # ASSET-003: require/import
                for regex in (_RE_ASSET_REQUIRE, _RE_ASSET_IMPORT):
                    for m in regex.finditer(line):
                        ref = m.group(1)
                        if _is_static_asset_ref(ref) and not _resolve_asset(ref, file_dir, project_root):
                            violations.append(Violation(
                                check="ASSET-003",
                                message=f"Asset import '{ref}' — file not found on disk",
                                file_path=rel_path, line=lineno, severity="warning",
                            ))

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
    return violations


def parse_prd_reconciliation(report_path: Path) -> list[Violation]:
    """Parse PRD_RECONCILIATION.md and return PRD-001 violations for mismatches."""
    if not report_path.is_file():
        return []
    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    violations: list[Violation] = []
    in_mismatch = False

    _re_section = re.compile(r'^#{2,3}\s')
    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("### MISMATCH") or stripped.startswith("## MISMATCH"):
            in_mismatch = True
            continue
        if _re_section.match(stripped) and "MISMATCH" not in stripped:
            in_mismatch = False
            continue
        if in_mismatch and stripped.startswith("- "):
            violations.append(Violation(
                check="PRD-001",
                message=f"PRD reconciliation mismatch: {stripped[2:].strip()}",
                file_path=str(report_path.name),
                line=lineno,
                severity="warning",
            ))

    return violations[:_MAX_VIOLATIONS]


# ---------------------------------------------------------------------------
# Database integrity scans: Dual ORM, Default Values, Relationships
# ---------------------------------------------------------------------------


def _detect_data_access_methods(
    project_root: Path,
    source_files: list[Path],
) -> tuple[bool, bool]:
    """Detect whether the project uses ORM(s) and raw SQL queries.

    Returns (has_orm, has_raw_sql).
    """
    has_orm = False
    has_raw = False

    # Check project dependency files for ORM and raw query indicators
    for dep_name in ("package.json",):
        dep_path = project_root / dep_name
        if dep_path.is_file():
            try:
                content = dep_path.read_text(encoding="utf-8", errors="replace").lower()
                # ORM indicators
                if any(kw in content for kw in ("prisma", "typeorm", "sequelize", "mongoose")):
                    has_orm = True
                # Raw query indicators
                if any(kw in content for kw in ("knex", '"pg"', '"mysql2"')):
                    has_raw = True
            except OSError:
                pass

    for dep_name in ("requirements.txt",):
        dep_path = project_root / dep_name
        if dep_path.is_file():
            try:
                content = dep_path.read_text(encoding="utf-8", errors="replace").lower()
                if any(kw in content for kw in ("sqlalchemy", "django")):
                    has_orm = True
                if any(kw in content for kw in ("psycopg", "pymysql", "pymongo")):
                    has_raw = True
            except OSError:
                pass

    # Check .csproj files for NuGet packages
    for f in source_files:
        if f.suffix == ".csproj":
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                if "Microsoft.EntityFrameworkCore" in content:
                    has_orm = True
                if "Dapper" in content:
                    has_raw = True
            except OSError:
                pass

    # Scan source files for code-level indicators
    for f in source_files:
        if f.suffix not in _EXT_ENTITY:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        ext = f.suffix
        if ext == ".cs":
            if "DbContext" in content or "[Table]" in content or "[Column]" in content:
                has_orm = True
            if any(kw in content for kw in ("SqlConnection", "QueryAsync", "ExecuteAsync")):
                has_raw = True
        elif ext in (".ts", ".js"):
            # Only flag as raw SQL if keyword appears outside comments
            for line in content.splitlines():
                stripped = line.lstrip()
                if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                    continue
                if _RE_DB_SQL_STRING.search(line):
                    has_raw = True
                    break
        elif ext == ".py":
            if "Base.metadata" in content or "models.Model" in content:
                has_orm = True
            if "cursor.execute" in content:
                has_raw = True

    return (has_orm, has_raw)


def _find_entity_files(
    project_root: Path,
    source_files: list[Path],
) -> list[Path]:
    """Return source files that appear to be ORM entity/model definitions."""
    entity_files: list[Path] = []
    for f in source_files:
        if f.suffix not in _EXT_ENTITY:
            continue
        try:
            rel = f.relative_to(project_root).as_posix()
        except ValueError:
            rel = f.name

        # Check by directory name
        if _RE_ENTITY_DIR.search(rel):
            entity_files.append(f)
            continue

        # Check by content indicators
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if f.suffix == ".cs":
            if _RE_ENTITY_INDICATOR_CS.search(content):
                entity_files.append(f)
        elif f.suffix in (".ts", ".js"):
            if _RE_ENTITY_INDICATOR_TS.search(content):
                entity_files.append(f)
        elif f.suffix == ".py":
            if _RE_ENTITY_INDICATOR_PY.search(content):
                entity_files.append(f)

    return entity_files


def run_dual_orm_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Detect type mismatches between ORM models and raw SQL queries.

    Only runs if 2+ data access methods are detected (ORM + raw queries).
    Skips gracefully if only one access method found.

    Pattern IDs: DB-001 (enum mismatch), DB-002 (boolean mismatch), DB-003 (datetime mismatch)
    """
    violations: list[Violation] = []

    # Also scan .csproj files for detection
    all_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for filename in filenames:
            fp = Path(dirpath) / filename
            if fp.suffix in _EXT_ENTITY or fp.suffix == ".csproj":
                all_files.append(fp)

    source_files = _iter_source_files(project_root)
    # H2 fix: detect data access methods with FULL file list (not scoped)
    # so that dual-ORM pattern is correctly identified even when only
    # entity files were changed but raw SQL files were not
    has_orm, has_raw = _detect_data_access_methods(project_root, all_files)

    if not (has_orm and has_raw):
        return []

    # Collect ORM property types from entity files (full list for context)
    entity_files = _find_entity_files(project_root, source_files)
    # Map: property_name_lower -> set of types ("bool", "enum", "string", "datetime")
    orm_prop_types: dict[str, set[str]] = {}

    for ef in entity_files:
        try:
            content = ef.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = ef.relative_to(project_root).as_posix()

        if ef.suffix == ".cs":
            for m in _RE_DB_CSHARP_BOOL_PROP.finditer(content):
                prop_name = m.group(1).lower()
                orm_prop_types.setdefault(prop_name, set()).add("bool")
            for m in _RE_DB_CSHARP_DATETIME_PROP.finditer(content):
                prop_name = m.group(1).lower()
                orm_prop_types.setdefault(prop_name, set()).add("datetime")
            for m in _RE_DB_CSHARP_ENUM_PROP.finditer(content):
                type_name = m.group(1)
                prop_name = m.group(2).lower()
                # Skip common non-enum types using shared frozenset
                if type_name in _CSHARP_NON_ENUM_TYPES:
                    continue
                # Skip types with non-enum suffixes (Dto, Service, Controller, etc.)
                if type_name.endswith(_CSHARP_NON_ENUM_SUFFIXES):
                    continue
                # Skip if type name looks like a known entity (present in entity_info)
                orm_prop_types.setdefault(prop_name, set()).add("enum")

    # H2 fix: apply scope filter to violation-reporting phase only
    # (detection + ORM property collection above used full file lists)
    scoped_source_files = source_files
    if scope and scope.changed_files:
        scope_set = set(f.resolve() for f in scope.changed_files)
        scoped_source_files = [f for f in source_files if f.resolve() in scope_set]

    # Scan raw SQL in source files for type comparison mismatches
    for f in scoped_source_files:
        if f.suffix not in _EXT_ENTITY:
            continue
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not _RE_DB_SQL_STRING.search(content):
            continue

        rel_path = f.relative_to(project_root).as_posix()

        for lineno, line in enumerate(content.splitlines(), start=1):
            if not _RE_DB_SQL_STRING.search(line):
                continue

            line_lower = line.lower()

            # DB-001: Enum column compared as integer or string in raw SQL
            if _RE_DB_SQL_ENUM_INT_CMP.search(line) or _RE_DB_SQL_ENUM_STR_CMP.search(line):
                for prop, types in orm_prop_types.items():
                    if "enum" in types and re.search(rf'\b{re.escape(prop)}\b', line_lower):
                        violations.append(Violation(
                            check="DB-001",
                            message=f"Possible enum type mismatch: ORM defines '{prop}' as enum but raw SQL compares as literal value",
                            file_path=rel_path,
                            line=lineno,
                            severity="error",
                        ))
                        break

            # DB-002: Boolean column compared as 0/1 in raw SQL
            if _RE_DB_SQL_BOOL_INT.search(line):
                for prop, types in orm_prop_types.items():
                    if "bool" in types and re.search(rf'\b{re.escape(prop)}\b', line_lower):
                        violations.append(Violation(
                            check="DB-002",
                            message=f"Possible boolean type mismatch: ORM defines '{prop}' as bool but raw SQL compares as 0/1",
                            file_path=rel_path,
                            line=lineno,
                            severity="error",
                        ))
                        break

            # DB-003: DateTime column with hardcoded format in raw SQL
            if _RE_DB_SQL_DATETIME_FORMAT.search(line):
                for prop, types in orm_prop_types.items():
                    if "datetime" in types and re.search(rf'\b{re.escape(prop)}\b', line_lower):
                        violations.append(Violation(
                            check="DB-003",
                            message=f"Possible datetime format mismatch: ORM defines '{prop}' as DateTime but raw SQL uses hardcoded date literal",
                            file_path=rel_path,
                            line=lineno,
                            severity="error",
                        ))
                        break

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
    return violations


def run_default_value_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Detect missing defaults and unsafe nullable access in entity models.

    Scans ORM entity/model files for boolean/enum properties without defaults
    and nullable properties used without null guards.

    Pattern IDs: DB-004 (missing default), DB-005 (nullable without null check)
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)
    entity_files = _find_entity_files(project_root, source_files)
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        entity_files = [f for f in entity_files if f.resolve() in scope_set]

    for ef in entity_files:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        try:
            content = ef.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = ef.relative_to(project_root).as_posix()
        ext = ef.suffix

        if ext == ".cs":
            # DB-004: C# bool without default
            for m in _RE_DB_CSHARP_BOOL_NO_DEFAULT.finditer(content):
                prop_name = m.group(1)
                lineno = content[:m.start()].count("\n") + 1
                violations.append(Violation(
                    check="DB-004",
                    message=f"Boolean property '{prop_name}' has no explicit default — add '= false;' or '= true;'",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))

            # DB-004: C# enum without default (L2 fix)
            for m in _RE_DB_CSHARP_ENUM_NO_DEFAULT.finditer(content):
                type_name = m.group(1)
                prop_name = m.group(2)
                # Only flag actual enum types — skip primitives and known non-enums
                if type_name in _CSHARP_NON_ENUM_TYPES:
                    continue
                # Skip types with non-enum suffixes (Dto, Service, Controller, etc.)
                if type_name.endswith(_CSHARP_NON_ENUM_SUFFIXES):
                    continue
                # Skip if it looks like a navigation property (type matches a known entity pattern)
                if type_name.endswith(("Id", "[]")):
                    continue
                lineno = content[:m.start()].count("\n") + 1
                violations.append(Violation(
                    check="DB-004",
                    message=f"Enum property '{prop_name}' (type '{type_name}') has no explicit default — add '= {type_name}.DefaultValue;'",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))

            # DB-005: C# nullable property without null check
            nullable_props: list[tuple[str, str]] = []  # (type, name)
            for m in _RE_DB_CSHARP_NULLABLE_PROP.finditer(content):
                nullable_props.append((m.group(1), m.group(2)))

            # Search other source files for unsafe access of nullable props
            if nullable_props:
                for sf in source_files:
                    if sf == ef:
                        continue
                    if len(violations) >= _MAX_VIOLATIONS:
                        break
                    try:
                        sf_content = sf.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    sf_rel = sf.relative_to(project_root).as_posix()

                    for _ntype, nname in nullable_props:
                        # Look for .PropName.Method() without ?.
                        pattern = re.compile(
                            rf'\.{re.escape(nname)}\.(?!\s*\?)(\w+)',
                        )
                        for sm in pattern.finditer(sf_content):
                            # Check if there's a null check in the surrounding context
                            pos = sm.start()
                            context_start = max(0, sf_content.rfind("\n", 0, max(0, pos - 500)))
                            context = sf_content[context_start:pos]
                            if f"{nname} != null" not in context and f"{nname} is not null" not in context and f"?.{nname}" not in sf_content[max(0, pos - 50):pos]:
                                slineno = sf_content[:pos].count("\n") + 1
                                violations.append(Violation(
                                    check="DB-005",
                                    message=f"Nullable property '{nname}' accessed without null check — use '?.' or null guard",
                                    file_path=sf_rel,
                                    line=slineno,
                                    severity="error",
                                ))

        elif ext == ".py":
            # DB-004: Django BooleanField without default
            for m in _RE_DB_DJANGO_BOOL_NO_DEFAULT.finditer(content):
                lineno = content[:m.start()].count("\n") + 1
                violations.append(Violation(
                    check="DB-004",
                    message="BooleanField() without default= parameter — add default=True or default=False",
                    file_path=rel_path,
                    line=lineno,
                    severity="warning",
                ))

            # DB-004: SQLAlchemy Column(Boolean) without default
            for m in _RE_DB_SQLALCHEMY_NO_DEFAULT.finditer(content):
                matched_text = m.group(0)
                if "default" not in matched_text and "server_default" not in matched_text:
                    lineno = content[:m.start()].count("\n") + 1
                    violations.append(Violation(
                        check="DB-004",
                        message="Column(Boolean/Enum) without default — add default= or server_default=",
                        file_path=rel_path,
                        line=lineno,
                        severity="warning",
                    ))

            # DB-005: Python Optional[] property accessed without null guard
            optional_props: list[str] = []
            for opt_m in re.finditer(r'(\w+)\s*:\s*Optional\[', content):
                optional_props.append(opt_m.group(1))
            if optional_props:
                for sf in source_files:
                    if sf == ef or sf.suffix != ".py":
                        continue
                    if len(violations) >= _MAX_VIOLATIONS:
                        break
                    try:
                        sf_content = sf.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    sf_rel = sf.relative_to(project_root).as_posix()
                    for oname in optional_props:
                        pattern = re.compile(rf'\.{re.escape(oname)}\.(\w+)')
                        for om in pattern.finditer(sf_content):
                            pos = om.start()
                            context_start = max(0, sf_content.rfind("\n", 0, max(0, pos - 500)))
                            context = sf_content[context_start:pos]
                            if (f"if {oname}" not in context
                                    and f"if self.{oname}" not in context
                                    and f"{oname} is not None" not in context
                                    and f"{oname} is None" not in context):
                                slineno = sf_content[:pos].count("\n") + 1
                                violations.append(Violation(
                                    check="DB-005",
                                    message=f"Optional property '{oname}' accessed without null guard — check 'if {oname} is not None' first",
                                    file_path=sf_rel,
                                    line=slineno,
                                    severity="error",
                                ))

        elif ext in (".ts", ".js"):
            # DB-005: TypeScript nullable property accessed without optional chaining
            # Find nullable types: prop?: Type  or  prop: Type | null  or  prop: Type | undefined
            ts_nullable_props: list[str] = []
            for ts_m in re.finditer(r'(\w+)\s*\?\s*:', content):
                ts_nullable_props.append(ts_m.group(1))
            for ts_m in re.finditer(r'(\w+)\s*:\s*\w+\s*\|\s*(?:null|undefined)', content):
                prop = ts_m.group(1)
                if prop not in ts_nullable_props:
                    ts_nullable_props.append(prop)
            if ts_nullable_props:
                for sf in source_files:
                    if sf == ef or sf.suffix not in (".ts", ".js"):
                        continue
                    if len(violations) >= _MAX_VIOLATIONS:
                        break
                    try:
                        sf_content = sf.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    sf_rel = sf.relative_to(project_root).as_posix()
                    for tname in ts_nullable_props:
                        # Look for .propName.method() without ?.propName
                        pattern = re.compile(rf'\.{re.escape(tname)}\.(?!\s*\?)(\w+)')
                        for tm in pattern.finditer(sf_content):
                            pos = tm.start()
                            # v10: Skip Prisma client delegate accesses
                            # prisma.model.method() is NOT a nullable access —
                            # Prisma client delegates are always defined
                            _pre_word = sf_content[max(0, pos - 30):pos].rstrip()
                            if re.search(r'\bprisma\s*$', _pre_word):
                                continue
                            # Check for optional chaining in nearby context
                            pre = sf_content[max(0, pos - 50):pos]
                            context_start = max(0, sf_content.rfind("\n", 0, max(0, pos - 500)))
                            context = sf_content[context_start:pos]
                            if (f"?.{tname}" not in pre
                                    and f"{tname} !== null" not in context
                                    and f"{tname} !== undefined" not in context
                                    and f"{tname} != null" not in context):
                                slineno = sf_content[:pos].count("\n") + 1
                                violations.append(Violation(
                                    check="DB-005",
                                    message=f"Nullable property '{tname}' accessed without optional chaining — use '?.{tname}' or add null guard",
                                    file_path=sf_rel,
                                    line=slineno,
                                    severity="error",
                                ))

    # Also scan .prisma files for DB-004
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for filename in filenames:
            if not filename.endswith(".prisma"):
                continue
            fp = Path(dirpath) / filename
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel_path = fp.relative_to(project_root).as_posix()

            for m in _RE_DB_PRISMA_NO_DEFAULT.finditer(content):
                field_name = m.group(1)
                # Check if the next line has @default
                end_pos = m.end()
                next_line_end = content.find("\n", end_pos + 1)
                if next_line_end == -1:
                    next_line_end = len(content)
                next_line = content[end_pos:next_line_end]
                if "@default" not in next_line:
                    lineno = content[:m.start()].count("\n") + 1
                    violations.append(Violation(
                        check="DB-004",
                        message=f"Prisma field '{field_name}' without @default — add @default(false) or similar",
                        file_path=rel_path,
                        line=lineno,
                        severity="warning",
                    ))

            # M1: Prisma enum fields without @default (user-defined types, not builtins)
            for m in _RE_DB_PRISMA_ENUM_NO_DEFAULT.finditer(content):
                field_name = m.group(1)
                type_name = m.group(2)
                # Skip Prisma built-in types (already handled above)
                if type_name in _PRISMA_BUILTIN_TYPES:
                    continue
                end_pos = m.end()
                next_line_end = content.find("\n", end_pos + 1)
                if next_line_end == -1:
                    next_line_end = len(content)
                next_line = content[end_pos:next_line_end]
                if "@default" not in next_line:
                    lineno = content[:m.start()].count("\n") + 1
                    violations.append(Violation(
                        check="DB-004",
                        message=f"Prisma enum field '{field_name}' (type '{type_name}') without @default — add @default(VALUE)",
                        file_path=rel_path,
                        line=lineno,
                        severity="warning",
                    ))

            # L2: Prisma String fields with status-like names without @default
            for m in _RE_DB_PRISMA_STRING_STATUS_NO_DEFAULT.finditer(content):
                field_name = m.group(1)
                end_pos = m.end()
                next_line_end = content.find("\n", end_pos + 1)
                if next_line_end == -1:
                    next_line_end = len(content)
                next_line = content[end_pos:next_line_end]
                if "@default" not in next_line:
                    lineno = content[:m.start()].count("\n") + 1
                    violations.append(Violation(
                        check="DB-004",
                        message=f"Prisma status field '{field_name}' (String) without @default — add @default(\"Draft\") or similar",
                        file_path=rel_path,
                        line=lineno,
                        severity="warning",
                    ))

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
    return violations


def run_relationship_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """Detect incomplete ORM relationship configurations.

    Finds FK columns without navigation properties, navigation properties
    without inverse relationships, and FKs with no relationship config at all.

    Pattern IDs: DB-006 (FK no nav), DB-007 (nav no inverse), DB-008 (FK no config)
    """
    violations: list[Violation] = []
    source_files = _iter_source_files(project_root)
    entity_files = _find_entity_files(project_root, source_files)

    if not entity_files:
        return []

    # M1 fix: determine scoped entity files for violation REPORTING only.
    # entity_info is collected from ALL entity files for full cross-file
    # relationship context (unchanged entity B's nav props must be visible
    # when checking changed entity A's FK references).
    _scoped_entity_rel_paths: set[str] | None = None
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        _scoped_entity_rel_paths = set()
        for f in entity_files:
            if f.resolve() in scope_set:
                _scoped_entity_rel_paths.add(f.relative_to(project_root).as_posix())

    # Collect all entity info: FK props, nav props, config calls
    # entity_name -> {fk_props: [(name, line, file)], nav_props: [(type, name, line, file)]}
    entity_info: dict[str, dict] = {}

    # Also scan configuration files for HasMany/HasOne
    config_references: set[str] = set()  # property names referenced in config

    for ef in entity_files:
        try:
            content = ef.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = ef.relative_to(project_root).as_posix()
        ext = ef.suffix

        if ext == ".cs":
            # Extract class name
            class_match = re.search(r'class\s+(\w+)', content)
            if not class_match:
                continue
            class_name = class_match.group(1)

            entity_data = entity_info.setdefault(class_name, {
                "fk_props": [], "nav_props": [],
            })

            # Find FK properties
            for m in _RE_DB_CSHARP_FK_PROP.finditer(content):
                prop_name = m.group(1)
                # Skip the primary key 'Id'
                if prop_name == "Id":
                    continue
                lineno = content[:m.start()].count("\n") + 1
                entity_data["fk_props"].append((prop_name, lineno, rel_path))

            # Find navigation properties
            for m in _RE_DB_CSHARP_NAV_PROP.finditer(content):
                if m.group(1) is not None:
                    # Collection type: ICollection<T>, List<T>, etc.
                    type_name = m.group(1)
                    prop_name = m.group(2)
                else:
                    # Plain type: public virtual Entity Prop {
                    type_name = m.group(3)
                    prop_name = m.group(4)
                # Skip primitive types using shared frozenset + extras
                if type_name in _CSHARP_NON_ENUM_TYPES or type_name in ("Status", "byte[]"):
                    continue
                # Skip types with non-enum suffixes (likely not navigation targets)
                if type_name.endswith(_CSHARP_NON_ENUM_SUFFIXES):
                    continue
                lineno = content[:m.start()].count("\n") + 1
                entity_data["nav_props"].append((type_name, prop_name, lineno, rel_path))

            # Scan for HasMany/HasOne configuration
            for m in _RE_DB_CSHARP_HAS_MANY.finditer(content):
                config_references.add(m.group(1))

        elif ext in (".ts", ".js"):
            # TypeORM: extract class name and relation details
            class_match = re.search(r'class\s+(\w+)', content)
            if not class_match:
                continue
            class_name = class_match.group(1)

            entity_data = entity_info.setdefault(class_name, {
                "fk_props": [], "nav_props": [],
            })

            # TypeORM @JoinColumn → FK-like reference
            for m in _RE_DB_TYPEORM_JOIN_COLUMN.finditer(content):
                col_name = m.group(1)
                lineno = content[:m.start()].count("\n") + 1
                entity_data["fk_props"].append((col_name, lineno, rel_path))

            # TypeORM relation decorators → navigation properties
            for m in _RE_DB_TYPEORM_RELATION_DETAIL.finditer(content):
                rel_type = m.group(1)  # ManyToOne, OneToMany, etc.
                target_entity = m.group(2)
                lineno = content[:m.start()].count("\n") + 1
                # Find the property name: skip decorator args until closing paren,
                # then look for the property declaration on the same/next line
                after = content[m.end():]
                # Skip past any remaining decorator arguments and closing parens
                paren_match = re.search(r'\)\s*\n?\s*(\w+)\s*[;:?!]', after)
                if paren_match:
                    prop_name = paren_match.group(1)
                else:
                    # Fallback: first word before ; or : in next 200 chars
                    prop_match = re.search(r'(\w+)\s*[;:]', after[:200])
                    prop_name = prop_match.group(1) if prop_match else target_entity.lower()
                entity_data["nav_props"].append((target_entity, prop_name, lineno, rel_path))
                config_references.add(prop_name)

        elif ext == ".py":
            # Django/SQLAlchemy: extract class and FK/relationship details
            class_match = re.search(r'class\s+(\w+)', content)
            if not class_match:
                continue
            class_name = class_match.group(1)

            entity_data = entity_info.setdefault(class_name, {
                "fk_props": [], "nav_props": [],
            })

            # Django FK fields
            for m in _RE_DB_DJANGO_FK_DETAIL.finditer(content):
                field_name = m.group(1)
                target_model = m.group(2)
                lineno = content[:m.start()].count("\n") + 1
                entity_data["fk_props"].append((field_name, lineno, rel_path))
                # Django FK implicitly creates navigation
                entity_data["nav_props"].append((target_model, field_name, lineno, rel_path))

            # SQLAlchemy FK columns
            for m in _RE_DB_SQLALCHEMY_FK_COLUMN.finditer(content):
                col_name = m.group(1)
                target_table = m.group(2)
                lineno = content[:m.start()].count("\n") + 1
                entity_data["fk_props"].append((col_name, lineno, rel_path))

            # SQLAlchemy relationship() calls → navigation
            for m in _RE_DB_SQLALCHEMY_RELATIONSHIP_DETAIL.finditer(content):
                prop_name = m.group(1)
                target_model = m.group(2)
                lineno = content[:m.start()].count("\n") + 1
                entity_data["nav_props"].append((target_model, prop_name, lineno, rel_path))
                config_references.add(prop_name)

    # Also scan all source files for entity configuration classes
    for sf in source_files:
        if sf.suffix != ".cs":
            continue
        try:
            content = sf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _RE_DB_CSHARP_HAS_MANY.finditer(content):
            config_references.add(m.group(1))

    # Build a set of all known entity names for inverse lookup
    all_entity_names = set(entity_info.keys())

    # Check entities for missing navigation, inverse, and config
    for entity_name, data in entity_info.items():
        if len(violations) >= _MAX_VIOLATIONS:
            break

        fk_props = data["fk_props"]
        nav_props = data["nav_props"]
        nav_type_names = {t for t, _n, _l, _f in nav_props}
        nav_prop_names = {n for _t, n, _l, _f in nav_props}

        for fk_name, fk_line, fk_file in fk_props:
            if len(violations) >= _MAX_VIOLATIONS:
                break

            # M1 fix: only report violations for scoped files
            if _scoped_entity_rel_paths is not None and fk_file not in _scoped_entity_rel_paths:
                continue

            # Derive expected nav property name: "TenderId" -> "Tender"
            expected_nav = fk_name[:-2] if fk_name.endswith("Id") else None
            if not expected_nav:
                continue

            has_nav = expected_nav in nav_prop_names or expected_nav in nav_type_names
            has_config = fk_name in config_references or expected_nav in config_references

            if not has_nav and not has_config:
                # DB-008: FK with no navigation AND no config
                violations.append(Violation(
                    check="DB-008",
                    message=f"FK '{fk_name}' has no navigation property and no relationship configuration",
                    file_path=fk_file,
                    line=fk_line,
                    severity="error",
                ))
            elif not has_nav:
                # DB-006: FK without navigation property
                violations.append(Violation(
                    check="DB-006",
                    message=f"FK '{fk_name}' has no navigation property '{expected_nav}' — eager loading will return null",
                    file_path=fk_file,
                    line=fk_line,
                    severity="warning",
                ))

        # DB-007: Navigation property without inverse on related entity (C2 fix)
        for nav_type, nav_name, nav_line, nav_file in nav_props:
            if len(violations) >= _MAX_VIOLATIONS:
                break
            # M1 fix: only report violations for scoped files
            if _scoped_entity_rel_paths is not None and nav_file not in _scoped_entity_rel_paths:
                continue
            # Only check if the related type is a known entity
            if nav_type not in all_entity_names:
                continue
            related_data = entity_info.get(nav_type)
            if not related_data:
                continue
            # Check if related entity has an inverse navigation back to this entity
            related_nav_types = {t for t, _n, _l, _f in related_data["nav_props"]}
            if entity_name not in related_nav_types:
                violations.append(Violation(
                    check="DB-007",
                    message=f"Navigation property '{nav_name}' (type '{nav_type}') has no inverse on '{nav_type}' — add ICollection<{entity_name}> or reference back",
                    file_path=nav_file,
                    line=nav_line,
                    severity="info",
                ))

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))
    return violations


# ---------------------------------------------------------------------------
# API Contract Verification — run_api_contract_scan()
# ---------------------------------------------------------------------------

_RE_SVC_ROW_START = re.compile(r'^\|\s*SVC-\d+\s*\|', re.MULTILINE)

_RE_FIELD_SCHEMA = re.compile(r'\{[^}]+\}')  # kept for backward compat


def _find_balanced_braces(text: str, start: int = 0) -> str | None:
    """Find the first balanced {...} block in *text* starting from *start*.

    Tracks brace depth so nested objects like ``{a, b: {x, y}, c}`` are
    captured in full.  Returns the matched substring **including** the outer
    braces, or ``None`` if no balanced block is found.
    """
    open_pos = text.find('{', start)
    if open_pos == -1:
        return None
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[open_pos:i + 1]
    return None  # unbalanced


@dataclass
class SvcContract:
    """Parsed SVC-xxx table row from REQUIREMENTS.md."""
    svc_id: str
    frontend_service_method: str
    backend_endpoint: str
    http_method: str
    request_dto: str
    response_dto: str
    request_fields: dict[str, str]   # field_name -> type_hint
    response_fields: dict[str, str]  # field_name -> type_hint


def _parse_field_schema(schema_text: str) -> dict[str, str]:
    """Parse a field schema like '{ id: number, title: string }' into a dict.

    Returns field_name -> type_hint mapping. Returns empty dict if the text
    is just a class name (no braces) or unparseable.
    """
    balanced = _find_balanced_braces(schema_text)
    if not balanced:
        return {}
    inner = balanced[1:-1].strip()  # strip outer braces
    if not inner:
        return {}

    fields: dict[str, str] = {}
    # Split on commas that are NOT inside nested braces or angle brackets
    depth = 0
    current = ""
    for char in inner:
        if char in ('{', '<', '('):
            depth += 1
            current += char
        elif char in ('}', '>', ')'):
            depth -= 1
            current += char
        elif char == ',' and depth == 0:
            _parse_single_field(current.strip(), fields)
            current = ""
        else:
            current += char
    if current.strip():
        _parse_single_field(current.strip(), fields)

    return fields


def _parse_single_field(field_text: str, fields: dict[str, str]) -> None:
    """Parse 'fieldName: type' or bare 'fieldName' into the fields dict."""
    if ':' in field_text:
        parts = field_text.split(':', 1)
        name = parts[0].strip().strip('"').strip("'").rstrip('?')
        type_hint = parts[1].strip()
        if name and type_hint:
            fields[name] = type_hint
        return
    # Bare identifier without type (e.g. shorthand "{id, email, fullName}")
    bare = field_text.strip().strip('"').strip("'").rstrip('?')
    if bare and re.match(r'^[a-zA-Z_]\w*$', bare):
        fields[bare] = ""


def _parse_svc_table(requirements_text: str) -> list[SvcContract]:
    """Parse all SVC-xxx table rows from REQUIREMENTS.md content.

    Supports both 5-column tables (``| ID | Endpoint | Method | Request | Response |``)
    and 6-column tables (``| ID | Frontend Svc | Endpoint | Method | Request | Response |``).
    """
    contracts: list[SvcContract] = []
    for line in requirements_text.splitlines():
        stripped = line.strip()
        if not _RE_SVC_ROW_START.match(stripped):
            continue

        # Split on pipe, trim whitespace, drop empty outer cells
        cells = [c.strip() for c in stripped.split('|')]
        cells = [c for c in cells if c]  # remove "" from leading/trailing |

        if len(cells) < 5:
            continue  # malformed row

        svc_id = cells[0].strip()
        if not svc_id.startswith("SVC-"):
            continue

        if len(cells) >= 6:
            # 6-column: ID | Frontend Svc | Endpoint | Method | Request | Response
            frontend_sm = cells[1]
            backend_ep = cells[2]
            http_method = cells[3]
            request_dto = cells[4]
            response_dto = cells[5]
        else:
            # 5-column: ID | Endpoint | Method | Request | Response
            frontend_sm = ""
            backend_ep = cells[1]
            http_method = cells[2]
            request_dto = cells[3]
            response_dto = cells[4]

        request_fields = _parse_field_schema(request_dto)
        response_fields = _parse_field_schema(response_dto)

        contracts.append(SvcContract(
            svc_id=svc_id,
            frontend_service_method=frontend_sm,
            backend_endpoint=backend_ep,
            http_method=http_method,
            request_dto=request_dto,
            response_dto=response_dto,
            request_fields=request_fields,
            response_fields=response_fields,
        ))
    return contracts


def _to_pascal_case(camel_name: str) -> str:
    """Convert camelCase field name to PascalCase (for C# property matching).

    Examples: 'tenderTitle' -> 'TenderTitle', 'id' -> 'Id'
    """
    if not camel_name:
        return camel_name
    return camel_name[0].upper() + camel_name[1:]


def _extract_identifiers_from_file(content: str) -> set[str]:
    """Extract all word-boundary identifiers from a source file.

    Returns a set of all tokens that look like identifiers (letters, digits, underscore).
    This is intentionally broad — the caller filters against known field names.
    """
    return set(re.findall(r'\b[a-zA-Z_]\w*\b', content))


def _find_files_by_pattern(
    project_root: Path,
    pattern: str,
    scope: "ScanScope | None" = None,
) -> list[Path]:
    """Find source files whose relative path matches the given regex pattern."""
    compiled = re.compile(pattern, re.IGNORECASE)
    matched: list[Path] = []
    source_files = _iter_source_files(project_root)
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        source_files = [f for f in source_files if f.resolve() in scope_set]
    for f in source_files:
        rel = f.relative_to(project_root).as_posix()
        if compiled.search(rel):
            matched.append(f)
    return matched


def _check_backend_fields(
    contract: SvcContract,
    project_root: Path,
    violations: list[Violation],
) -> None:
    """Check that backend DTO files contain all fields from the contract schema."""
    if not contract.response_fields:
        return

    # Find backend files (controllers, DTOs, models, handlers)
    backend_patterns = [
        r'(?:controllers?|handlers?|endpoints?)',
        r'(?:dto|dtos|models?|entities|viewmodels?|responses?)',
    ]
    backend_files: list[Path] = []
    for pat in backend_patterns:
        backend_files.extend(_find_files_by_pattern(project_root, pat))

    if not backend_files:
        return

    # Collect all identifiers from backend files
    all_backend_ids: set[str] = set()
    for bf in backend_files:
        try:
            content = bf.read_text(encoding="utf-8", errors="replace")
            if len(content) > _MAX_FILE_SIZE:
                continue
            all_backend_ids.update(_extract_identifiers_from_file(content))
        except OSError:
            continue

    if not all_backend_ids:
        return

    for field_name, type_hint in contract.response_fields.items():
        pascal_name = _to_pascal_case(field_name)
        # Accept either camelCase or PascalCase in backend code
        if field_name not in all_backend_ids and pascal_name not in all_backend_ids:
            violations.append(Violation(
                check="API-001",
                message=(
                    f"{contract.svc_id}: Backend missing field '{field_name}' "
                    f"(PascalCase: '{pascal_name}') from response schema. "
                    f"Expected type: {type_hint}"
                ),
                file_path="REQUIREMENTS.md",
                line=0,
                severity="error",
            ))


def _check_frontend_fields(
    contract: SvcContract,
    project_root: Path,
    violations: list[Violation],
) -> None:
    """Check that frontend model/service files use exact field names from the contract.

    Prioritises type-definition files (models, interfaces, types, dto) over
    general usage files (services, clients).  When type-def files exist, a
    field must appear in at least one of them; its presence only in a service
    or component file is not enough.  This catches interface definition
    mismatches even when services still reference the old name.
    """
    if not contract.response_fields:
        return

    # --- Phase 1: type-definition files (models, interfaces, types, dto) ---
    type_def_patterns = [r'(?:models?|interfaces?|types?|dto)']
    type_def_files: list[Path] = []
    for pat in type_def_patterns:
        type_def_files.extend(_find_files_by_pattern(project_root, pat))

    type_def_ids: set[str] = set()
    for ff in type_def_files:
        try:
            content = ff.read_text(encoding="utf-8", errors="replace")
            if len(content) > _MAX_FILE_SIZE:
                continue
            type_def_ids.update(_extract_identifiers_from_file(content))
        except OSError:
            continue

    # --- Phase 2: fallback to all frontend files if no type-defs found ---
    check_ids: set[str]
    if type_def_ids:
        check_ids = type_def_ids
    else:
        usage_patterns = [r'(?:services?|clients?|api)']
        usage_files: list[Path] = []
        for pat in usage_patterns:
            usage_files.extend(_find_files_by_pattern(project_root, pat))
        if not usage_files:
            return
        check_ids = set()
        for ff in usage_files:
            try:
                content = ff.read_text(encoding="utf-8", errors="replace")
                if len(content) > _MAX_FILE_SIZE:
                    continue
                check_ids.update(_extract_identifiers_from_file(content))
            except OSError:
                continue
        if not check_ids:
            return

    for field_name, type_hint in contract.response_fields.items():
        # Frontend must use the exact camelCase name from the schema
        if field_name not in check_ids:
            violations.append(Violation(
                check="API-002",
                message=(
                    f"{contract.svc_id}: Frontend missing field '{field_name}' "
                    f"from response schema. Expected type: {type_hint}. "
                    f"The frontend model/interface must use this exact field name."
                ),
                file_path="REQUIREMENTS.md",
                line=0,
                severity="error",
            ))


_TYPE_COMPAT_MAP: dict[str, set[str]] = {
    "number": {"number", "int", "long", "float", "double", "decimal", "integer", "bigint"},
    "string": {"string", "str", "datetime", "date", "guid", "uuid", "iso8601"},
    "boolean": {"boolean", "bool"},
}


def _check_type_compatibility(
    contract: SvcContract,
    project_root: Path,
    violations: list[Violation],
) -> None:
    """Check that field types in backend/frontend are compatible with the contract."""
    if not contract.response_fields:
        return

    for field_name, type_hint in contract.response_fields.items():
        normalized = type_hint.lower().strip().strip('"').strip("'")
        # Skip bare identifiers (no type provided) and complex types
        if not normalized:
            continue
        if any(c in normalized for c in ('{', '<', '[', '|', 'array', 'list')):
            continue

        # Check if the type looks like it could be mismatched
        is_known = False
        for _base_type, compat_set in _TYPE_COMPAT_MAP.items():
            if normalized in compat_set:
                is_known = True
                break

        if not is_known and normalized not in ("enum", "object", "any", "-"):
            violations.append(Violation(
                check="API-003",
                message=(
                    f"{contract.svc_id}: Field '{field_name}' has unusual type "
                    f"'{type_hint}' — verify backend/frontend type compatibility."
                ),
                file_path="REQUIREMENTS.md",
                line=0,
                severity="warning",
            ))


def _check_enum_serialization(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
    """ENUM-004: Check .NET projects for global JsonStringEnumConverter.

    ASP.NET serializes enums as integers by default. Without a global
    JsonStringEnumConverter, every enum field sent to the frontend will
    be an integer while the frontend expects a string.
    """
    # 1. Detect .NET — check for .csproj files (filter out excluded dirs)
    csproj_files = [
        f for f in project_root.rglob("*.csproj")
        if not _path_in_excluded_dir(f.relative_to(project_root))
    ]
    if not csproj_files:
        return []  # Not a .NET project — skip entirely

    # 2. Check for global JsonStringEnumConverter in startup files
    for startup_name in ("Program.cs", "Startup.cs"):
        for startup_file in project_root.rglob(startup_name):
            if _path_in_excluded_dir(startup_file.relative_to(project_root)):
                continue
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

    return sorted(violations, key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line))


# Regex to parse TypeScript interface field declarations
# Matches both multi-line (field at line start) and single-line (field after ; or {)
_RE_TS_INTERFACE_FIELD = re.compile(r'(?:^|[;{])\s*(\w+)\s*(\?)?\s*:', re.MULTILINE)

# Regex to match the START of a TypeScript interface/type declaration (up to the opening brace).
# The body is then extracted using _find_balanced_braces() to handle nested type literals.
_RE_TS_INTERFACE_START = re.compile(
    r'(?:export\s+)?(?:interface|type)\s+(\w+)\s*(?:extends\s+[^{]+)?\s*(?:=\s*)?\{',
    re.DOTALL,
)

# Kept for backward compat / other call-sites
_RE_TS_INTERFACE_BLOCK = re.compile(
    r'(?:export\s+)?(?:interface|type)\s+(\w+)\s*(?:extends\s+[^{]+)?\s*(?:=\s*)?\{([^}]*)\}',
    re.DOTALL,
)


def _strip_nested_braces(body: str) -> str:
    """Remove content inside nested ``{...}`` blocks, keeping only top-level tokens.

    Example::

        "id: string; assignee: { id: string; fullName: string } | null; title: string"
        →  "id: string; assignee:  | null; title: string"

    This prevents ``_RE_TS_INTERFACE_FIELD`` from matching fields that live
    inside nested type literals (e.g. ``fullName`` inside ``assignee``).
    """
    result: list[str] = []
    depth = 0
    for char in body:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        elif depth == 0:
            result.append(char)
    return ''.join(result)


# Request / command interface name suffixes — these model the *request body*
# sent TO the backend, not the response coming back. They should be excluded
# from the bidirectional response-field check.
_REQUEST_SUFFIXES: tuple[str, ...] = (
    'Request', 'Payload', 'Input', 'Args', 'Params', 'Command',
    'CreateRequest', 'UpdateRequest', 'DeleteRequest',
)

# Universal fields to skip in bidirectional check
_UNIVERSAL_FIELDS: frozenset[str] = frozenset({
    "id", "createdAt", "updatedAt", "createdBy", "updatedBy",
})

# UI-only fields to skip in bidirectional check
_UI_ONLY_FIELDS: frozenset[str] = frozenset({
    "isLoading", "isSelected", "isExpanded", "className",
    "key", "ref", "children", "style",
})


def _check_frontend_extra_fields(
    contract: SvcContract,
    project_root: Path,
    violations: list[Violation],
) -> None:
    """API-002 bidirectional: Check frontend interface for fields NOT in SVC response schema.

    For each SVC entry with response_fields, find matching frontend TypeScript interfaces
    and flag extra fields that the backend won't provide.
    """
    if not contract.response_fields:
        return

    svc_field_names = set(contract.response_fields.keys())
    svc_field_names_lower = {f.lower() for f in svc_field_names}

    # Find frontend type/interface files
    type_def_patterns = [r'(?:models?|interfaces?|types?|dto)']
    type_def_files: list[Path] = []
    for pat in type_def_patterns:
        type_def_files.extend(_find_files_by_pattern(project_root, pat))

    # Only check TypeScript files — exclude backend-only paths (Fix 3)
    ts_files = [
        f for f in type_def_files
        if f.suffix in ('.ts', '.tsx')
        and 'backend' not in f.relative_to(project_root).parts
    ]
    if not ts_files:
        return

    for ts_file in ts_files:
        try:
            content = ts_file.read_text(encoding="utf-8", errors="replace")
            if len(content) > _MAX_FILE_SIZE:
                continue
        except OSError:
            continue

        # Find all interface/type blocks using start-pattern + balanced braces
        for match in _RE_TS_INTERFACE_START.finditer(content):
            iface_name = match.group(1)

            # Fix 4: Skip request/command interfaces — they model the request
            # body, not the response shape.
            if iface_name.endswith(_REQUEST_SUFFIXES):
                continue

            # Extract balanced body (handles nested type literals)
            brace_start = match.end() - 1  # position of the opening {
            balanced = _find_balanced_braces(content, brace_start)
            if not balanced:
                continue
            interface_body = balanced[1:-1]  # strip outer braces

            # Strip nested braces to avoid matching fields inside nested
            # type literals (e.g. assignee: { id, fullName })
            flat_body = _strip_nested_braces(interface_body)

            # Parse field declarations from the flattened body
            interface_fields: dict[str, bool] = {}  # field_name -> is_optional
            for field_match in _RE_TS_INTERFACE_FIELD.finditer(flat_body):
                field_name = field_match.group(1)
                is_optional = field_match.group(2) == '?'
                interface_fields[field_name] = is_optional

            if not interface_fields:
                continue

            # Check overlap — interface must have >=50% of SVC *domain-specific*
            # fields to be a match.  Exclude universal fields (id, createdAt, …)
            # from both sets so that common timestamp/ID fields don't inflate the
            # overlap score and cause false matches (Fix 5).
            universal_lower = {f.lower() for f in _UNIVERSAL_FIELDS}
            interface_field_names_lower = {f.lower() for f in interface_fields}
            svc_domain_lower = svc_field_names_lower - universal_lower
            iface_domain_lower = interface_field_names_lower - universal_lower
            if not svc_domain_lower:
                continue  # SVC entry has only universal fields — skip
            domain_overlap = svc_domain_lower & iface_domain_lower
            if len(domain_overlap) < len(svc_domain_lower) * 0.5:
                continue  # Not enough domain-specific overlap — different type

            # Found a matching interface — check for extra fields
            rel = ts_file.relative_to(project_root).as_posix()
            for iface_field, is_optional in interface_fields.items():
                # Skip universal and UI-only fields
                if iface_field in _UNIVERSAL_FIELDS or iface_field in _UI_ONLY_FIELDS:
                    continue

                # Check if field exists in SVC response (case-insensitive)
                if iface_field.lower() not in svc_field_names_lower:
                    severity = "warning" if is_optional else "error"
                    violations.append(Violation(
                        check="API-002",
                        message=(
                            f"{contract.svc_id}: Frontend interface expects field "
                            f"'{iface_field}' but response schema does not include it. "
                            f"Backend must either add this field to the response DTO or "
                            f"frontend must remove it from the interface."
                        ),
                        file_path=rel,
                        line=0,
                        severity=severity,
                    ))


def run_silent_data_loss_scan(
    project_root: Path,
    scope: ScanScope | None = None,
) -> list[Violation]:
    """Scan project for silent data loss patterns (SDL-001).

    Wraps _check_cqrs_persistence() following the standard scan function signature.

    Returns:
        List of Violation objects (SDL-001).
    """
    violations = _check_cqrs_persistence(project_root, scope)
    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


def run_api_contract_scan(
    project_root: Path,
    scope: ScanScope | None = None,
) -> list[Violation]:
    """Scan project for API contract violations between SVC-xxx specs and code.

    Parses the SVC-xxx wiring table from REQUIREMENTS.md, extracts field schemas,
    and cross-references them against backend DTO properties and frontend model
    field names. Only produces violations for rows that have explicit field schemas
    (rows with just class names are skipped — backward compatible).

    Returns:
        List of Violation objects (API-001, API-002, API-003, API-004, ENUM-004).
    """
    violations: list[Violation] = []

    # Find REQUIREMENTS.md (check milestone dirs too)
    req_paths = [
        project_root / "REQUIREMENTS.md",
        project_root / ".agent-team" / "REQUIREMENTS.md",
    ]
    # Also check milestone directories
    milestones_dir = project_root / ".agent-team" / "milestones"
    if milestones_dir.is_dir():
        for ms_dir in sorted(milestones_dir.iterdir()):
            if ms_dir.is_dir():
                req_path = ms_dir / "REQUIREMENTS.md"
                if req_path.is_file():
                    req_paths.append(req_path)

    requirements_text = ""
    for req_path in req_paths:
        if req_path.is_file():
            try:
                requirements_text += "\n" + req_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

    if not requirements_text:
        # ENUM-004 check runs regardless of SVC table presence
        violations.extend(_check_enum_serialization(project_root, scope))
        violations = violations[:_MAX_VIOLATIONS]
        violations.sort(
            key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
        )
        return violations

    # Parse SVC-xxx table
    contracts = _parse_svc_table(requirements_text)
    if not contracts:
        # ENUM-004 check runs regardless of SVC table presence
        violations.extend(_check_enum_serialization(project_root, scope))
        violations = violations[:_MAX_VIOLATIONS]
        violations.sort(
            key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
        )
        return violations

    # Only check contracts that have field schemas (backward compat)
    contracts_with_schemas = [
        c for c in contracts
        if c.response_fields or c.request_fields
    ]

    if not contracts_with_schemas:
        # ENUM-004 check runs regardless of SVC table presence
        violations.extend(_check_enum_serialization(project_root, scope))
        violations = violations[:_MAX_VIOLATIONS]
        violations.sort(
            key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
        )
        return violations

    # Run all checks (API-001, API-002 forward, API-003, API-002 bidirectional)
    for contract in contracts_with_schemas:
        if len(violations) >= _MAX_VIOLATIONS:
            break
        _check_backend_fields(contract, project_root, violations)
        _check_frontend_fields(contract, project_root, violations)
        _check_type_compatibility(contract, project_root, violations)
        _check_frontend_extra_fields(contract, project_root, violations)

    # API-004: Check request field passthrough (frontend sends → backend accepts)
    violations.extend(_check_request_field_passthrough(contracts_with_schemas, project_root, scope))

    # ENUM-004: Check .NET enum serialization (runs as part of API contract scan)
    violations.extend(_check_enum_serialization(project_root, scope))

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


# ---------------------------------------------------------------------------
# XREF-001: Frontend-backend endpoint cross-reference scan
# ---------------------------------------------------------------------------

# Angular HttpClient pattern: this.http.get/post/put/delete/patch(...)
# Uses nested-generic-aware pattern to handle <Outer<Inner>> type params
_RE_ANGULAR_HTTP = re.compile(
    r"""(?:this\.)?(?:http|httpClient)\s*\.\s*"""
    r"""(get|post|put|delete|patch)\s*(?:<(?:[^<>]|<[^>]*>)*>)?\s*\(\s*"""
    r"""[`'"](.*?)[`'"]""",
    re.IGNORECASE,
)

# Axios pattern: axios.get/post/put/delete/patch(...) or api.get/post(...)
# Uses nested-generic-aware pattern to handle <Outer<Inner>> type params
_RE_AXIOS = re.compile(
    r"""(?:axios|api|apiClient|axiosInstance|client|http)\s*\.\s*"""
    r"""(get|post|put|delete|patch)\s*(?:<(?:[^<>]|<[^>]*>)*>)?\s*\(\s*"""
    r"""[`'"](.*?)[`'"]""",
    re.IGNORECASE,
)

# fetch() pattern: fetch('url') or fetch(`url`, { method: ... })
_RE_FETCH = re.compile(
    r"""fetch\s*\(\s*[`'"](.*?)[`'"]""",
    re.IGNORECASE,
)

# fetch() method extraction: { method: 'POST' } or { method: "PUT" }
_RE_FETCH_METHOD = re.compile(
    r"""method\s*:\s*['"](\w+)['"]""",
    re.IGNORECASE,
)

# .NET class-level [Route("api/...")] or [Route("[controller]")]
_RE_DOTNET_ROUTE = re.compile(
    r"""\[Route\(\s*["'](.*?)["']\s*\)\]""",
    re.IGNORECASE,
)

# .NET controller class name
_RE_DOTNET_CONTROLLER = re.compile(
    r"""class\s+(\w+Controller)\s*""",
    re.IGNORECASE,
)

# .NET HTTP method attribute [HttpGet("path")], [HttpPost], etc.
_RE_DOTNET_HTTP_METHOD = re.compile(
    r"""\[(Http(?:Get|Post|Put|Delete|Patch))\s*(?:\(\s*["'](.*?)["']\s*\))?\]""",
    re.IGNORECASE,
)

# Express router pattern: router.get('/path', ...) or app.get('/path', ...)
_RE_EXPRESS_ROUTE = re.compile(
    r"""(?:router|app)\s*\.\s*(get|post|put|delete|patch|all)\s*\(\s*"""
    r"""['"`](.*?)['"`]""",
    re.IGNORECASE,
)

# Express app.use() mount: app.use('/api/v1', someRouter)
_RE_EXPRESS_MOUNT = re.compile(
    r"""app\s*\.\s*use\s*\(\s*['"`](.*?)['"`]""",
    re.IGNORECASE,
)

# Flask route decorator: @app.route('/path', methods=['GET', 'POST'])
# or @blueprint.route('/path')
_RE_FLASK_ROUTE = re.compile(
    r"""@\s*(?:\w+\.)?route\s*\(\s*['"`](.*?)['"`]"""
    r"""(?:\s*,\s*methods\s*=\s*\[(.*?)\])?""",
    re.IGNORECASE,
)

# FastAPI route decorator: @app.get('/path'), @router.post('/path')
_RE_FASTAPI_ROUTE = re.compile(
    r"""@\s*(?:\w+\.)\s*(get|post|put|delete|patch)\s*\(\s*"""
    r"""['"`](.*?)['"`]""",
    re.IGNORECASE,
)

# Django path() in urls.py: path('api/items/', views.item_list)
_RE_DJANGO_PATH = re.compile(
    r"""path\s*\(\s*['"`](.*?)['"`]""",
    re.IGNORECASE,
)


_FrontendCall = collections.namedtuple("_FrontendCall", ["method", "path", "file_path", "line"])
_BackendRoute = collections.namedtuple("_BackendRoute", ["method", "path", "file_path", "line"])


# Directories to skip when scanning for XREF — extends EXCLUDED_DIRS
_XREF_SKIP_PARTS: frozenset[str] = EXCLUDED_DIRS | frozenset({".env"})

# File suffixes to skip (test files, specs, etc.)
_XREF_SKIP_SUFFIXES: tuple[str, ...] = (
    ".spec.ts", ".spec.js", ".test.ts", ".test.js",
    ".spec.tsx", ".test.tsx", ".spec.jsx", ".test.jsx",
    ".d.ts",
)


def _normalize_api_path(path: str) -> str:
    """Normalize an API path for matching.

    - Strips protocol + host
    - Replaces path parameter patterns with ``{param}``
    - Lowercases
    - Strips trailing slashes and leading double-slashes
    - Removes ``/api/v1`` or ``/api`` prefix for matching flexibility

    Examples::

        '/api/v1/tenders/${id}' → 'tenders/{param}'
        'https://localhost:5000/api/items' → 'items'
        '/Tenders/GetAll' → 'tenders/getall'
    """
    p = path.strip()

    # Strip protocol + host
    if "://" in p:
        idx = p.index("://") + 3
        slash_idx = p.find("/", idx)
        if slash_idx >= 0:
            p = p[slash_idx:]
        else:
            return ""

    # Strip leading base URL variable interpolations (contain `.`, indicating
    # object property access like ${this.apiUrl} or ${environment.apiUrl}).
    # These are NOT path parameters — they're base URL prefixes.
    # Mid-path params like /tenders/${tenderId}/approval are unaffected.
    p = re.sub(r'^\$\{[^}]*\.[^}]*\}\s*/?', '/', p)

    # Replace remaining template literal interpolations: ${...} → {param}
    p = re.sub(r'\$\{[^}]*\}', '{param}', p)
    # Replace :param → {param}
    p = re.sub(r'/:([^/]+)', '/{param}', p)
    # Replace [controller] placeholder
    p = re.sub(r'\[controller\]', '{controller}', p, flags=re.IGNORECASE)
    # Replace <type:param> (Flask style) → {param}
    p = re.sub(r'<[^>]*>', '{param}', p)
    # Replace {id}, {id:int}, {tenantId} etc. → {param}
    p = re.sub(r'\{[^}]*\}', '{param}', p)

    # Lowercase
    p = p.lower()

    # Ensure leading slash before prefix check
    if not p.startswith("/"):
        p = "/" + p

    # Remove common API prefixes for matching flexibility
    for prefix in ("/api/v1/", "/api/v2/", "/api/"):
        if p.startswith(prefix):
            p = "/" + p[len(prefix):]
            break

    # Normalize slashes
    p = p.rstrip("/")
    if not p.startswith("/"):
        p = "/" + p

    return p


def _is_external_url(path: str) -> bool:
    """Return True if the path points to an external (non-localhost) URL."""
    lower = path.lower().strip()
    if "://" in lower:
        # Allow localhost URLs
        for local in ("localhost", "127.0.0.1", "0.0.0.0"):
            if local in lower:
                return False
        return True
    return False


def _should_skip_xref_file(file_path: Path, project_root: Path) -> bool:
    """Return True if the file should be skipped for XREF scanning."""
    try:
        parts = file_path.relative_to(project_root).parts
    except ValueError:
        return True

    # Skip directories
    for part in parts:
        if part in _XREF_SKIP_PARTS:
            return True

    # Skip test files
    name = file_path.name
    for suffix in _XREF_SKIP_SUFFIXES:
        if name.endswith(suffix):
            return True

    # Skip e2e directories
    for part in parts:
        if part in ("e2e", "__tests__", "tests", "test"):
            return True

    return False


def _extract_frontend_http_calls(
    project_root: Path,
    scope: ScanScope | None,
) -> list["_FrontendCall"]:
    """Extract all HTTP calls from frontend source files.

    Scans TypeScript/JavaScript files for Angular HttpClient, Axios, and
    fetch() patterns.  Skips external URLs (unless localhost), test files,
    and build artifacts.

    When ``scope`` is provided, collects ALL calls from ALL files (needed for
    complete matching), but the caller should only report violations for
    scoped files (same v6 pattern as other scans).
    """
    calls: list[_FrontendCall] = []
    frontend_extensions = (".ts", ".tsx", ".js", ".jsx")

    # BUG-1 fix: regex for Angular variable-URL refs (no quotes around URL)
    # e.g., this.http.get<Task>(this.apiUrl, ...) or this.http.post(this.apiUrl, data)
    # Uses nested-generic-aware pattern: <Outer<Inner>> instead of simple <[^>]*>
    re_angular_var = re.compile(
        r"""(?:this\.)?(?:http|httpClient)\s*\.\s*"""
        r"""(get|post|put|delete|patch)\s*(?:<(?:[^<>]|<[^>]*>)*>)?\s*\(\s*"""
        r"""(this\.\w+)""",
        re.IGNORECASE,
    )
    # Regex to resolve class field values like: private apiUrl = '/api/tasks'
    # or: private apiUrl = `${environment.apiUrl}/tasks`
    re_field_value = re.compile(
        r"""(?:private|readonly|public|protected|\s)\s*(\w+)\s*[:=]\s*[`'"](.*?)[`'"]""",
    )

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in _XREF_SKIP_PARTS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix not in frontend_extensions:
                continue
            if _should_skip_xref_file(fpath, project_root):
                continue

            # Skip backend directories
            try:
                rel_parts = fpath.relative_to(project_root).parts
            except ValueError:
                continue
            if any(p in ("backend", "server", "api", "Controllers", "Handlers") for p in rel_parts):
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(content) > _MAX_FILE_SIZE:
                continue

            rel = fpath.relative_to(project_root).as_posix()

            # Build field value lookup for this file (used by BUG-1 variable
            # resolution AND BUG-3 base URL variable resolution in template literals)
            field_values: dict[str, str] = {}
            for fm in re_field_value.finditer(content):
                field_values[fm.group(1)] = fm.group(2)

            # BUG-2 fix: deduplicate by line number (not match position, since
            # Angular and Axios regexes can overlap at different char offsets
            # on the same source line, e.g. "this.http.post" matches both)
            seen_lines: set[int] = set()

            # Regex to detect leading ${this.xxx} or ${self.xxx} base URL variable
            re_base_var = re.compile(r'^\$\{(?:this|self)\.(\w+)\}')

            def _resolve_base_url_var(url_path: str) -> str:
                """Resolve leading ${this.xxx} in template literals to field value.

                If the field value is known, substitute it. Otherwise return as-is.
                """
                m_var = re_base_var.match(url_path)
                if not m_var:
                    return url_path
                var_name = m_var.group(1)
                field_val = field_values.get(var_name, "")
                if field_val:
                    # Replace ${this.xxx} with the resolved value
                    return field_val + url_path[m_var.end():]
                return url_path

            def _add_call(method: str, url_path: str, match_start: int) -> None:
                """Add a frontend call, deduplicating by line number."""
                line_no = content[:match_start].count("\n") + 1
                if line_no in seen_lines:
                    return
                # Resolve base URL variables in template literals
                url_path = _resolve_base_url_var(url_path)
                if _is_external_url(url_path):
                    return
                # Skip complex template literals with multiple interpolations
                if "${" in url_path and url_path.count("${") > 1:
                    return
                seen_lines.add(line_no)
                calls.append(_FrontendCall(method=method.upper(), path=url_path, file_path=rel, line=line_no))

            # Angular HttpClient (quoted URLs)
            for m in _RE_ANGULAR_HTTP.finditer(content):
                _add_call(m.group(1), m.group(2), m.start())

            # Axios (quoted URLs)
            for m in _RE_AXIOS.finditer(content):
                _add_call(m.group(1), m.group(2), m.start())

            # fetch() (quoted URLs)
            for m in _RE_FETCH.finditer(content):
                url_path = m.group(1)
                url_path = _resolve_base_url_var(url_path)
                if _is_external_url(url_path):
                    continue
                if "${" in url_path and url_path.count("${") > 1:
                    continue
                after = content[m.end():m.end() + 200]
                method_match = _RE_FETCH_METHOD.search(after)
                method = method_match.group(1).upper() if method_match else "GET"
                line_no = content[:m.start()].count("\n") + 1
                if line_no not in seen_lines:
                    seen_lines.add(line_no)
                    calls.append(_FrontendCall(method=method, path=url_path, file_path=rel, line=line_no))

            for m in re_angular_var.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                if line_no in seen_lines:
                    continue  # Already captured by quoted-URL regex
                method = m.group(1).upper()
                var_ref = m.group(2)  # e.g., "this.apiUrl"
                var_name = var_ref.split(".")[-1]  # e.g., "apiUrl"

                # Try to resolve the variable to a URL path
                resolved = field_values.get(var_name, "")
                if resolved:
                    # Field has a string value — use it as the path
                    _add_call(method, resolved, m.start())
                else:
                    # Can't resolve statically — skip (no false positive)
                    pass

    return calls


def _extract_backend_routes_dotnet(
    project_root: Path,
    scope: ScanScope | None,
) -> list["_BackendRoute"]:
    """Extract all API routes from .NET controller files."""
    routes: list[_BackendRoute] = []
    cs_extensions = (".cs",)

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in _XREF_SKIP_PARTS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix not in cs_extensions:
                continue
            if "Controller" not in fname:
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(content) > _MAX_FILE_SIZE:
                continue

            rel = fpath.relative_to(project_root).as_posix()

            # Extract class-level route prefix
            route_prefix = ""
            route_match = _RE_DOTNET_ROUTE.search(content)
            if route_match:
                route_prefix = route_match.group(1)

            # Replace [controller] with the controller name (minus "Controller" suffix)
            ctrl_match = _RE_DOTNET_CONTROLLER.search(content)
            ctrl_name = ""
            if ctrl_match:
                ctrl_name = ctrl_match.group(1).replace("Controller", "")
            if "[controller]" in route_prefix.lower():
                route_prefix = re.sub(r'\[controller\]', ctrl_name, route_prefix, flags=re.IGNORECASE)

            # Extract individual HTTP method attributes
            for m in _RE_DOTNET_HTTP_METHOD.finditer(content):
                attr = m.group(1)  # HttpGet, HttpPost, etc.
                action_path = m.group(2) or ""

                # Map attribute to HTTP method
                method_map = {
                    "httpget": "GET", "httppost": "POST", "httpput": "PUT",
                    "httpdelete": "DELETE", "httppatch": "PATCH",
                }
                method = method_map.get(attr.lower(), "GET")

                # Handle ~ route override (absolute path, ignore controller prefix)
                if action_path.startswith("~"):
                    full_path = action_path[1:]  # Strip ~ and use as absolute
                else:
                    # Combine prefix + action path
                    full_path = route_prefix.rstrip("/")
                    if action_path:
                        full_path = full_path + "/" + action_path.lstrip("/")
                if not full_path.startswith("/"):
                    full_path = "/" + full_path

                line_no = content[:m.start()].count("\n") + 1
                routes.append(_BackendRoute(method=method, path=full_path, file_path=rel, line=line_no))

    return routes


def _resolve_import_path(
    import_rel: str,
    mount_file: Path,
    project_root: Path,
    js_extensions: tuple[str, ...] = (".ts", ".js", ".mjs"),
) -> str | None:
    """Resolve a relative import path to a project-relative posix path.

    Tries ``import_rel`` with various extensions and ``/index`` fallbacks.
    Returns the project-relative posix path if the file exists, else ``None``.
    """
    base_dir = mount_file.parent
    # Strip leading ./ and normalize
    rel = import_rel.lstrip("./")
    candidate = base_dir / rel

    # Try as-is, then with extensions appended (NOT with_suffix, which
    # replaces multi-dot names like auth.routes → auth.ts instead of auth.routes.ts)
    candidates: list[Path] = [candidate]
    for ext in js_extensions:
        candidates.append(Path(str(candidate) + ext))
        candidates.append(candidate / ("index" + ext))

    for c in candidates:
        if c.is_file():
            try:
                return c.relative_to(project_root).as_posix()
            except ValueError:
                return c.as_posix()
    return None


def _extract_backend_routes_express(
    project_root: Path,
    scope: ScanScope | None,
) -> list["_BackendRoute"]:
    """Extract all API routes from Express/Node.js router files."""
    routes: list[_BackendRoute] = []
    js_extensions = (".ts", ".js", ".mjs")

    # BUG-4 fix: Resolve mount prefixes to ROUTE FILE paths, not mount file paths.
    # Parse app.use('/prefix', routerVar) AND import/require statements to build
    # a mapping from route_file_posix → mount_prefix.

    # Regex: app.use('/prefix', someRouter) — captures prefix AND variable name
    re_mount_full = re.compile(
        r"""app\s*\.\s*use\s*\(\s*['"`](.*?)['"`]\s*,\s*(\w+)""",
        re.IGNORECASE,
    )
    # Import patterns: import varName from './path' OR import { varName } from './path'
    re_import = re.compile(
        r"""import\s+(?:\{\s*)?(\w+)(?:\s*\})?\s+from\s+['"`](.*?)['"`]""",
    )
    # Require patterns: const varName = require('./path')
    re_require = re.compile(
        r"""(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*['"`](.*?)['"`]\s*\)""",
    )

    mount_prefixes: dict[str, str] = {}  # route_file_posix → prefix

    # First pass: parse mount files to resolve router → prefix mappings
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in _XREF_SKIP_PARTS]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix not in js_extensions:
                continue
            if _should_skip_xref_file(fpath, project_root):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Collect import/require mappings: variable_name → import_path
            imports: dict[str, str] = {}
            for m in re_import.finditer(content):
                imports[m.group(1)] = m.group(2)
            for m in re_require.finditer(content):
                imports[m.group(1)] = m.group(2)

            # Collect mount points: app.use('/prefix', routerVar)
            for m in re_mount_full.finditer(content):
                prefix = m.group(1).rstrip("/")
                router_var = m.group(2)

                # Resolve the router variable to a file path
                import_path = imports.get(router_var, "")
                if import_path:
                    resolved = _resolve_import_path(import_path, fpath, project_root, js_extensions)
                    if resolved:
                        mount_prefixes[resolved] = prefix

    # Second pass: collect route definitions and apply mount prefixes
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in _XREF_SKIP_PARTS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix not in js_extensions:
                continue
            if _should_skip_xref_file(fpath, project_root):
                continue

            # Only look at files likely to be route files
            name_lower = fname.lower()
            is_route_file = any(
                kw in name_lower
                for kw in ("route", "router", "controller", "handler", "api", "endpoint", "app", "server", "index")
            )
            if not is_route_file:
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(content) > _MAX_FILE_SIZE:
                continue

            rel = fpath.relative_to(project_root).as_posix()

            # Look up mount prefix for this route file
            prefix = mount_prefixes.get(rel, "")

            for m in _RE_EXPRESS_ROUTE.finditer(content):
                method = m.group(1).upper()
                if method == "ALL":
                    method = "GET"  # Treat app.all() as GET for matching
                route_path = m.group(2)

                # Apply mount prefix if available
                if prefix:
                    full_path = prefix.rstrip("/") + "/" + route_path.lstrip("/")
                else:
                    full_path = route_path

                line_no = content[:m.start()].count("\n") + 1
                routes.append(_BackendRoute(method=method, path=full_path, file_path=rel, line=line_no))

    return routes


def _extract_backend_routes_python(
    project_root: Path,
    scope: ScanScope | None,
) -> list["_BackendRoute"]:
    """Extract all API routes from Flask/FastAPI/Django files."""
    routes: list[_BackendRoute] = []

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in _XREF_SKIP_PARTS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix != ".py":
                continue
            if _should_skip_xref_file(fpath, project_root):
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(content) > _MAX_FILE_SIZE:
                continue

            rel = fpath.relative_to(project_root).as_posix()

            # Flask @app.route / @blueprint.route
            for m in _RE_FLASK_ROUTE.finditer(content):
                path_str = m.group(1)
                methods_str = m.group(2)
                if methods_str:
                    # Parse methods=['GET', 'POST']
                    methods = re.findall(r"['\"](\w+)['\"]", methods_str)
                    for method in methods:
                        line_no = content[:m.start()].count("\n") + 1
                        routes.append(_BackendRoute(method=method.upper(), path=path_str, file_path=rel, line=line_no))
                else:
                    line_no = content[:m.start()].count("\n") + 1
                    routes.append(_BackendRoute(method="GET", path=path_str, file_path=rel, line=line_no))

            # FastAPI @app.get / @router.post
            for m in _RE_FASTAPI_ROUTE.finditer(content):
                method = m.group(1).upper()
                path_str = m.group(2)
                line_no = content[:m.start()].count("\n") + 1
                routes.append(_BackendRoute(method=method, path=path_str, file_path=rel, line=line_no))

            # Django path() — only in urls.py files
            if "urls" in fname.lower():
                for m in _RE_DJANGO_PATH.finditer(content):
                    path_str = m.group(1)
                    # Django doesn't have method in path(), default to ALL methods
                    line_no = content[:m.start()].count("\n") + 1
                    routes.append(_BackendRoute(method="ANY", path=path_str, file_path=rel, line=line_no))

    return routes


# Regex detecting unresolvable function-call URLs like ${this.func(...)}/path
_RE_FUNCTION_CALL_URL = re.compile(
    r'\$\{(?:this|self)\.\w+\([^)]*\)\}'
)


def _has_function_call_url(raw_path: str) -> bool:
    """Return True if *raw_path* contains an unresolvable function-call interpolation.

    Example patterns that match:
      ``${this.importUrl(tenderId, bidId)}/parse``
      ``${self.getEndpoint(id)}/action``

    These can't be resolved statically so violations for them are
    demoted to ``info`` severity.
    """
    return bool(_RE_FUNCTION_CALL_URL.search(raw_path))


def _check_endpoint_xref(
    frontend_calls: list["_FrontendCall"],
    backend_routes: list["_BackendRoute"],
) -> list[Violation]:
    """Cross-reference frontend HTTP calls against backend routes.

    Uses 3-level matching:
      1. Exact match (normalized path + method)
      2. Method-agnostic match (normalized path only) → XREF-002
      3. No match at all → XREF-001

    Violations for URLs containing unresolvable function calls
    (``${this.func(...)}/...``) are demoted to ``info`` severity
    since the scanner cannot resolve them statically.
    """
    violations: list[Violation] = []

    # Normalize backend routes into lookup structures
    backend_exact: set[tuple[str, str]] = set()  # (method, normalized_path)
    backend_paths: set[str] = set()  # normalized_path only

    for route in backend_routes:
        norm = _normalize_api_path(route.path)
        if not norm:
            continue
        backend_exact.add((route.method.upper(), norm))
        backend_paths.add(norm)
        # Django "ANY" matches all methods
        if route.method == "ANY":
            for m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                backend_exact.add((m, norm))

    # Track already-reported paths to avoid duplicates
    reported: set[tuple[str, str, str]] = set()  # (method, normalized_path, file_path)

    for call in frontend_calls:
        norm = _normalize_api_path(call.path)
        if not norm:
            continue

        key = (call.method, norm, call.file_path)
        if key in reported:
            continue
        reported.add(key)

        # Detect function-call URLs — demote to info if present
        is_func_call = _has_function_call_url(call.path)

        # Level 1: exact match
        if (call.method, norm) in backend_exact:
            continue  # Perfect match

        # Level 2: method-agnostic match → method mismatch
        if norm in backend_paths:
            violations.append(Violation(
                check="XREF-002",
                message=(
                    f"Frontend calls {call.method} {call.path} but backend defines "
                    f"a different HTTP method for this path. Verify the correct "
                    f"method is used."
                ),
                file_path=call.file_path,
                line=call.line,
                severity="info" if is_func_call else "warning",
            ))
            continue

        # Level 3: no match at all → missing endpoint
        violations.append(Violation(
            check="XREF-001",
            message=(
                f"Frontend calls {call.method} {call.path} but no matching "
                f"backend endpoint was found. The backend controller/router "
                f"must define this endpoint."
                + (" (unresolvable function-call URL)" if is_func_call else "")
            ),
            file_path=call.file_path,
            line=call.line,
            severity="info" if is_func_call else "error",
        ))

        if len(violations) >= _MAX_VIOLATIONS:
            break

    return violations


def run_endpoint_xref_scan(
    project_root: Path,
    scope: ScanScope | None = None,
) -> list[Violation]:
    """Scan project for frontend-backend endpoint cross-reference mismatches.

    Auto-detects the backend framework (.NET, Express, Flask/FastAPI/Django)
    and extracts both frontend HTTP calls and backend route definitions.
    Cross-references them to find missing endpoints (XREF-001) and HTTP
    method mismatches (XREF-002).

    Returns an empty list if no frontend calls or no backend routes are found
    (project may not be full-stack).

    Returns:
        List of Violation objects (XREF-001, XREF-002).
    """
    # Extract frontend calls
    frontend_calls = _extract_frontend_http_calls(project_root, scope)
    if not frontend_calls:
        return []

    # Auto-detect backend framework and extract routes
    backend_routes: list[_BackendRoute] = []

    # Try .NET
    dotnet_routes = _extract_backend_routes_dotnet(project_root, scope)
    backend_routes.extend(dotnet_routes)

    # Try Express/Node.js
    express_routes = _extract_backend_routes_express(project_root, scope)
    backend_routes.extend(express_routes)

    # Try Python (Flask/FastAPI/Django)
    python_routes = _extract_backend_routes_python(project_root, scope)
    backend_routes.extend(python_routes)

    if not backend_routes:
        return []

    # Cross-reference
    violations = _check_endpoint_xref(frontend_calls, backend_routes)

    # Apply scope filter: only report violations for scoped files
    if scope and scope.changed_files:
        scope_posix: set[str] = set()
        for cf in scope.changed_files:
            try:
                scope_posix.add(cf.relative_to(project_root).as_posix())
            except ValueError:
                scope_posix.add(cf.as_posix())
        violations = [v for v in violations if v.file_path in scope_posix]

    violations = violations[:_MAX_VIOLATIONS]
    violations.sort(
        key=lambda v: (_SEVERITY_ORDER.get(v.severity, 99), v.file_path, v.line)
    )
    return violations


# ---------------------------------------------------------------------------
# API-004: Request field passthrough (write-side field dropped)
# ---------------------------------------------------------------------------


def _extract_csharp_class_properties(file_content: str, class_name: str) -> set[str]:
    """Extract public property names from a C# class definition.

    Finds the class by name and extracts properties defined with
    ``public Type PropertyName { get; set; }`` pattern.  Returns
    property names in their original casing.
    """
    # Find the class definition
    class_pattern = re.compile(
        rf'class\s+{re.escape(class_name)}\b[^{{]*\{{',
        re.DOTALL,
    )
    class_match = class_pattern.search(file_content)
    if not class_match:
        return set()

    # Extract balanced braces for the class body
    brace_start = class_match.end() - 1
    body = _find_balanced_braces(file_content, brace_start)
    if not body:
        return set()

    # Extract property names
    prop_pattern = re.compile(
        r'public\s+\w[\w<>\[\]?,\s]*\s+(\w+)\s*\{',
    )
    return {m.group(1) for m in prop_pattern.finditer(body)}


def _check_request_field_passthrough(
    contracts: list[SvcContract],
    project_root: Path,
    scope: ScanScope | None,
) -> list[Violation]:
    """API-004: Check that fields the frontend sends are accepted by the backend.

    For each SVC-xxx row with request_fields, extracts the backend Command/DTO
    class properties and verifies that every field the frontend sends has a
    matching property in the backend class.  Fields sent by the frontend but
    missing from the backend DTO are silently dropped.

    Only checks contracts with explicit request field schemas.
    """
    violations: list[Violation] = []

    # Collect contracts with request fields
    contracts_with_req = [c for c in contracts if c.request_fields]
    if not contracts_with_req:
        return violations

    # Find backend files (commands, DTOs, models)
    backend_patterns = [
        r'(?:commands?|handlers?|dtos?|requests?)',
        r'(?:controllers?|models?|viewmodels?)',
    ]
    backend_files: list[Path] = []
    for pat in backend_patterns:
        backend_files.extend(_find_files_by_pattern(project_root, pat))

    if not backend_files:
        return violations

    # Cache file contents
    file_contents: dict[Path, str] = {}
    for bf in backend_files:
        try:
            content = bf.read_text(encoding="utf-8", errors="replace")
            if len(content) <= _MAX_FILE_SIZE:
                file_contents[bf] = content
        except OSError:
            continue

    for contract in contracts_with_req:
        if len(violations) >= _MAX_VIOLATIONS:
            break

        # Extract class name from request_dto text: "CreateFooCommand { name: string }" → "CreateFooCommand"
        dto_text = contract.request_dto.strip()
        brace_idx = dto_text.find("{")
        if brace_idx > 0:
            class_name = dto_text[:brace_idx].strip()
        else:
            class_name = dto_text.strip()

        # Clean up class name — remove any backtick or quote artifacts
        class_name = re.sub(r'[`\'\"<>\[\]]', '', class_name).strip()
        if not class_name or not re.match(r'^[A-Za-z_]\w*$', class_name):
            continue

        # Search backend files for this class
        backend_props: set[str] = set()
        backend_ids: set[str] = set()
        for bf, content in file_contents.items():
            if class_name in content:
                props = _extract_csharp_class_properties(content, class_name)
                backend_props.update(props)
                # Also collect raw identifiers as fallback
                backend_ids.update(_extract_identifiers_from_file(content))

        # If we found explicit properties, use those; otherwise fall back to identifiers
        check_set = backend_props if backend_props else backend_ids
        if not check_set:
            continue

        for field_name in contract.request_fields:
            pascal_name = _to_pascal_case(field_name)
            # Accept either camelCase or PascalCase
            if field_name not in check_set and pascal_name not in check_set:
                violations.append(Violation(
                    check="API-004",
                    message=(
                        f"{contract.svc_id}: Frontend sends field '{field_name}' in "
                        f"{contract.http_method} request but backend class '{class_name}' "
                        f"has no matching property. The field is silently dropped. "
                        f"Add '{pascal_name}' property to '{class_name}' or remove "
                        f"the field from the frontend form."
                    ),
                    file_path="REQUIREMENTS.md",
                    line=0,
                    severity="error",
                ))

    return violations
