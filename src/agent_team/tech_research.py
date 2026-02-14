"""Tech stack research utilities for agent-team (Phase 1.5).

Detects the project tech stack (with versions) from project files and PRD
text, generates Context7 queries, validates research completeness, and
produces a compact summary for prompt injection.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TechStackEntry:
    """A single technology detected in the project."""

    name: str               # e.g. "Next.js"
    version: str | None     # e.g. "14.2.3" or None
    category: str           # frontend_framework | backend_framework | database | orm | ui_library | language | testing | other
    source: str             # package.json | requirements.txt | pyproject.toml | go.mod | csproj | prd_text | master_plan
    context7_id: str = ""   # resolved library ID from Context7


@dataclass
class TechResearchResult:
    """Aggregated result from the tech research phase."""

    stack: list[TechStackEntry] = field(default_factory=list)
    findings: dict[str, str] = field(default_factory=dict)  # tech_name -> research content
    queries_made: int = 0
    techs_covered: int = 0
    techs_total: int = 0
    is_complete: bool = False       # all techs have findings
    output_path: str = ""           # path to TECH_RESEARCH.md


# ---------------------------------------------------------------------------
# Category priority for sorting (lower = higher priority)
# ---------------------------------------------------------------------------

_CATEGORY_PRIORITY: dict[str, int] = {
    "frontend_framework": 0,
    "backend_framework": 1,
    "database": 2,
    "orm": 3,
    "ui_library": 4,
    "language": 5,
    "testing": 6,
    "other": 7,
}


# ---------------------------------------------------------------------------
# Known technology patterns for text-based detection
# ---------------------------------------------------------------------------

_TEXT_TECH_PATTERNS: list[tuple[str, str, str]] = [
    # (regex_pattern, canonical_name, category)
    # Frameworks
    (r"\bNext\.?js\s*(?:v?(\d+(?:\.\d+)*))?", "Next.js", "frontend_framework"),
    (r"\bReact\b(?:\.js)?\s*(?:v?(\d+(?:\.\d+)*))?", "React", "frontend_framework"),
    (r"\bVue\.?js\s*(?:v?(\d+(?:\.\d+)*))?", "Vue.js", "frontend_framework"),
    (r"\bAngular\b\s*(?:v?(\d+(?:\.\d+)*))?", "Angular", "frontend_framework"),
    (r"\bSvelte\b\s*(?:v?(\d+(?:\.\d+)*))?", "Svelte", "frontend_framework"),
    (r"\bExpress\.?js\b\s*(?:v?(\d+(?:\.\d+)*))?", "Express", "backend_framework"),
    (r"\bNest\.?js\b\s*(?:v?(\d+(?:\.\d+)*))?", "NestJS", "backend_framework"),
    (r"\bFastAPI\b\s*(?:v?(\d+(?:\.\d+)*))?", "FastAPI", "backend_framework"),
    (r"\bDjango\b\s*(?:v?(\d+(?:\.\d+)*))?", "Django", "backend_framework"),
    (r"\bFlask\b\s*(?:v?(\d+(?:\.\d+)*))?", "Flask", "backend_framework"),
    (r"\bSpring\s*Boot\b\s*(?:v?(\d+(?:\.\d+)*))?", "Spring Boot", "backend_framework"),
    (r"\bLaravel\b\s*(?:v?(\d+(?:\.\d+)*))?", "Laravel", "backend_framework"),
    (r"\bRails\b\s*(?:v?(\d+(?:\.\d+)*))?", "Rails", "backend_framework"),
    # Databases
    (r"\bPostgreSQL\b\s*(?:v?(\d+(?:\.\d+)*))?", "PostgreSQL", "database"),
    (r"\bMySQL\b\s*(?:v?(\d+(?:\.\d+)*))?", "MySQL", "database"),
    (r"\bMongoDB\b\s*(?:v?(\d+(?:\.\d+)*))?", "MongoDB", "database"),
    (r"\bRedis\b\s*(?:v?(\d+(?:\.\d+)*))?", "Redis", "database"),
    (r"\bSQLite\b\s*(?:v?(\d+(?:\.\d+)*))?", "SQLite", "database"),
    (r"\bSupabase\b\s*(?:v?(\d+(?:\.\d+)*))?", "Supabase", "database"),
    (r"\bFirebase\b\s*(?:v?(\d+(?:\.\d+)*))?", "Firebase", "database"),
    # ORMs
    (r"\bPrisma\b\s*(?:v?(\d+(?:\.\d+)*))?", "Prisma", "orm"),
    (r"\bDrizzle\b\s*(?:v?(\d+(?:\.\d+)*))?", "Drizzle", "orm"),
    (r"\bTypeORM\b\s*(?:v?(\d+(?:\.\d+)*))?", "TypeORM", "orm"),
    (r"\bSequelize\b\s*(?:v?(\d+(?:\.\d+)*))?", "Sequelize", "orm"),
    (r"\bSQLAlchemy\b\s*(?:v?(\d+(?:\.\d+)*))?", "SQLAlchemy", "orm"),
    (r"\bMongoose\b\s*(?:v?(\d+(?:\.\d+)*))?", "Mongoose", "orm"),
    # UI Libraries
    (r"\bTailwind\s*CSS\b\s*(?:v?(\d+(?:\.\d+)*))?", "Tailwind CSS", "ui_library"),
    (r"\bshadcn(?:/ui)?\b", "shadcn/ui", "ui_library"),
    (r"\bChakra\s*UI\b\s*(?:v?(\d+(?:\.\d+)*))?", "Chakra UI", "ui_library"),
    (r"\bMaterial[- ]?UI\b\s*(?:v?(\d+(?:\.\d+)*))?", "Material UI", "ui_library"),
    (r"\bAnt\s*Design\b\s*(?:v?(\d+(?:\.\d+)*))?", "Ant Design", "ui_library"),
    (r"\bRadix\s*UI\b", "Radix UI", "ui_library"),
    # Testing
    (r"\bJest\b\s*(?:v?(\d+(?:\.\d+)*))?", "Jest", "testing"),
    (r"\bVitest\b\s*(?:v?(\d+(?:\.\d+)*))?", "Vitest", "testing"),
    (r"\bPytest\b\s*(?:v?(\d+(?:\.\d+)*))?", "Pytest", "testing"),
    (r"\bPlaywright\b\s*(?:v?(\d+(?:\.\d+)*))?", "Playwright", "testing"),
    (r"\bCypress\b\s*(?:v?(\d+(?:\.\d+)*))?", "Cypress", "testing"),
    # Languages (only detect from text if not already detected from files)
    (r"\bTypeScript\b\s*(?:v?(\d+(?:\.\d+)*))?", "TypeScript", "language"),
    (r"\bPython\b\s*(?:v?(\d+(?:\.\d+)*))?", "Python", "language"),
    (r"\bGolang\b\s*(?:v?(\d+(?:\.\d+)*))?|\bGo\s+v?(\d+\.\d+(?:\.\d+)*)", "Go", "language"),
    (r"\bRust\b\s*(?:v?(\d+(?:\.\d+)*))?", "Rust", "language"),
]

# Map npm package names to canonical tech names + categories
_NPM_PACKAGE_MAP: dict[str, tuple[str, str]] = {
    "next": ("Next.js", "frontend_framework"),
    "react": ("React", "frontend_framework"),
    "vue": ("Vue.js", "frontend_framework"),
    "@angular/core": ("Angular", "frontend_framework"),
    "svelte": ("Svelte", "frontend_framework"),
    "express": ("Express", "backend_framework"),
    "@nestjs/core": ("NestJS", "backend_framework"),
    "fastify": ("Fastify", "backend_framework"),
    "prisma": ("Prisma", "orm"),
    "@prisma/client": ("Prisma", "orm"),
    "drizzle-orm": ("Drizzle", "orm"),
    "typeorm": ("TypeORM", "orm"),
    "sequelize": ("Sequelize", "orm"),
    "mongoose": ("Mongoose", "orm"),
    "tailwindcss": ("Tailwind CSS", "ui_library"),
    "@chakra-ui/react": ("Chakra UI", "ui_library"),
    "@mui/material": ("Material UI", "ui_library"),
    "antd": ("Ant Design", "ui_library"),
    "@radix-ui/react-primitive": ("Radix UI", "ui_library"),
    "jest": ("Jest", "testing"),
    "vitest": ("Vitest", "testing"),
    "@playwright/test": ("Playwright", "testing"),
    "cypress": ("Cypress", "testing"),
    "typescript": ("TypeScript", "language"),
    "pg": ("PostgreSQL", "database"),
    "mysql2": ("MySQL", "database"),
    "mongodb": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "ioredis": ("Redis", "database"),
    "better-sqlite3": ("SQLite", "database"),
    "@supabase/supabase-js": ("Supabase", "database"),
    "firebase": ("Firebase", "database"),
}

# Map Python package names to canonical tech names + categories
_PYTHON_PACKAGE_MAP: dict[str, tuple[str, str]] = {
    "django": ("Django", "backend_framework"),
    "fastapi": ("FastAPI", "backend_framework"),
    "flask": ("Flask", "backend_framework"),
    "sqlalchemy": ("SQLAlchemy", "orm"),
    "prisma": ("Prisma", "orm"),
    "pytest": ("Pytest", "testing"),
    "psycopg2": ("PostgreSQL", "database"),
    "psycopg": ("PostgreSQL", "database"),
    "pymongo": ("MongoDB", "database"),
    "redis": ("Redis", "database"),
    "celery": ("Celery", "other"),
}


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def _read_json_safe(path: Path) -> dict:
    """Read and parse a JSON file, returning empty dict on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _strip_version_prefix(version: str) -> str:
    """Strip npm version prefixes like ^, ~, >= etc."""
    return re.sub(r'^[^0-9]*', '', version).strip()


def _detect_from_package_json(root: Path) -> list[TechStackEntry]:
    """Detect technologies from package.json."""
    entries: list[TechStackEntry] = []
    seen_names: set[str] = set()

    pkg = _read_json_safe(root / "package.json")
    if not pkg:
        return entries

    deps: dict = pkg.get("dependencies") or {}
    dev_deps: dict = pkg.get("devDependencies") or {}
    all_deps = {**deps, **dev_deps}

    for pkg_name, (canonical, category) in _NPM_PACKAGE_MAP.items():
        if pkg_name in all_deps and canonical not in seen_names:
            version_raw = all_deps[pkg_name]
            version = _strip_version_prefix(version_raw) if isinstance(version_raw, str) else None
            entries.append(TechStackEntry(
                name=canonical,
                version=version or None,
                category=category,
                source="package.json",
            ))
            seen_names.add(canonical)

    return entries


def _parse_python_version(line: str) -> str | None:
    """Extract version from a pip requirements line like 'django==4.2.3'."""
    match = re.search(r'[=~><!]+\s*(\d+(?:\.\d+)*)', line)
    return match.group(1) if match else None


def _detect_from_requirements_txt(root: Path) -> list[TechStackEntry]:
    """Detect technologies from requirements.txt."""
    entries: list[TechStackEntry] = []
    seen_names: set[str] = set()

    req_path = root / "requirements.txt"
    if not req_path.is_file():
        return entries

    try:
        content = req_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return entries

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name (before any version specifier)
        pkg_match = re.match(r'^([a-zA-Z0-9_-]+)', line)
        if not pkg_match:
            continue
        pkg_name = pkg_match.group(1).lower()

        if pkg_name in _PYTHON_PACKAGE_MAP:
            canonical, category = _PYTHON_PACKAGE_MAP[pkg_name]
            if canonical not in seen_names:
                version = _parse_python_version(line)
                entries.append(TechStackEntry(
                    name=canonical,
                    version=version,
                    category=category,
                    source="requirements.txt",
                ))
                seen_names.add(canonical)

    # Detect Python language itself
    if entries and "Python" not in seen_names:
        entries.append(TechStackEntry(
            name="Python", version=None, category="language",
            source="requirements.txt",
        ))

    return entries


def _detect_from_pyproject(root: Path) -> list[TechStackEntry]:
    """Detect technologies from pyproject.toml."""
    entries: list[TechStackEntry] = []
    seen_names: set[str] = set()

    pp_path = root / "pyproject.toml"
    if not pp_path.is_file():
        return entries

    try:
        content = pp_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return entries

    for pkg_name, (canonical, category) in _PYTHON_PACKAGE_MAP.items():
        if pkg_name in content and canonical not in seen_names:
            # Try to extract version from common patterns
            version_match = re.search(
                rf'{re.escape(pkg_name)}\s*[=~><!]+\s*"?(\d+(?:\.\d+)*)',
                content,
            )
            version = version_match.group(1) if version_match else None
            entries.append(TechStackEntry(
                name=canonical,
                version=version,
                category=category,
                source="pyproject.toml",
            ))
            seen_names.add(canonical)

    if entries and "Python" not in seen_names:
        entries.append(TechStackEntry(
            name="Python", version=None, category="language",
            source="pyproject.toml",
        ))

    return entries


def _detect_from_go_mod(root: Path) -> list[TechStackEntry]:
    """Detect Go and modules from go.mod."""
    entries: list[TechStackEntry] = []
    go_mod = root / "go.mod"
    if not go_mod.is_file():
        return entries

    try:
        content = go_mod.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return entries

    # Detect Go version
    go_version_match = re.search(r'^go\s+(\d+\.\d+)', content, re.MULTILINE)
    go_version = go_version_match.group(1) if go_version_match else None
    entries.append(TechStackEntry(
        name="Go", version=go_version, category="language", source="go.mod",
    ))

    return entries


_CSPROJ_SKIP_DIRS = frozenset({
    ".git", "node_modules", "bin", "obj", ".vs",
    "packages", "__pycache__", ".nuget", "TestResults",
})


def _detect_from_csproj(root: Path) -> list[TechStackEntry]:
    """Detect .NET/C# technologies from *.csproj files."""
    entries: list[TechStackEntry] = []

    # Collect csproj files while skipping heavy directories
    csproj_files: list[Path] = []
    for csproj_path in root.rglob("*.csproj"):
        if any(part in _CSPROJ_SKIP_DIRS for part in csproj_path.parts):
            continue
        csproj_files.append(csproj_path)
        if len(csproj_files) >= 5:
            break

    if not csproj_files:
        return entries

    for csproj_path in csproj_files:
        try:
            content = csproj_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "Microsoft.NET.Sdk.Web" in content:
            tf_match = re.search(r'<TargetFramework>net(\d+\.\d+)', content)
            version = tf_match.group(1) if tf_match else None
            entries.append(TechStackEntry(
                name="ASP.NET Core", version=version,
                category="backend_framework", source="csproj",
            ))
            break  # One detection is enough

    if entries:
        entries.append(TechStackEntry(
            name="C#", version=None, category="language", source="csproj",
        ))

    return entries


def _detect_from_cargo(root: Path) -> list[TechStackEntry]:
    """Detect Rust from Cargo.toml."""
    entries: list[TechStackEntry] = []
    cargo_path = root / "Cargo.toml"
    if not cargo_path.is_file():
        return entries

    entries.append(TechStackEntry(
        name="Rust", version=None, category="language", source="Cargo.toml",
    ))

    try:
        content = cargo_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return entries

    if "actix" in content:
        entries.append(TechStackEntry(
            name="Actix", version=None, category="backend_framework",
            source="Cargo.toml",
        ))
    if "tokio" in content:
        entries.append(TechStackEntry(
            name="Tokio", version=None, category="other",
            source="Cargo.toml",
        ))

    return entries


def _detect_from_text(text: str, source: str) -> list[TechStackEntry]:
    """Detect technologies mentioned in free-form text (PRD, MASTER_PLAN)."""
    entries: list[TechStackEntry] = []
    seen_names: set[str] = set()

    for pattern, canonical, category in _TEXT_TECH_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if canonical not in seen_names:
                # Extract version from the first non-None capture group
                version = None
                if match.lastindex:
                    for gi in range(1, match.lastindex + 1):
                        if match.group(gi):
                            version = match.group(gi)
                            break
                entries.append(TechStackEntry(
                    name=canonical,
                    version=version,
                    category=category,
                    source=source,
                ))
                seen_names.add(canonical)

    return entries


def detect_tech_stack(
    cwd: Path | str,
    prd_text: str = "",
    master_plan_text: str = "",
    max_techs: int = 8,
) -> list[TechStackEntry]:
    """Detect the project tech stack with versions from files and text.

    Project files take precedence over text mentions for version info.
    Results are sorted by category priority and capped at *max_techs*.
    """
    root = Path(cwd)
    seen: dict[str, TechStackEntry] = {}  # canonical_name -> entry

    # 1. Project file detection (highest priority — has version info)
    for detector in (
        _detect_from_package_json,
        _detect_from_requirements_txt,
        _detect_from_pyproject,
        _detect_from_go_mod,
        _detect_from_csproj,
        _detect_from_cargo,
    ):
        for entry in detector(root):
            if entry.name not in seen:
                seen[entry.name] = entry

    # 2. Text detection (lower priority — may lack version)
    for text, source in [
        (prd_text, "prd_text"),
        (master_plan_text, "master_plan"),
    ]:
        if text:
            for entry in _detect_from_text(text, source):
                if entry.name not in seen:
                    seen[entry.name] = entry

    # Sort by category priority, then by name
    sorted_entries = sorted(
        seen.values(),
        key=lambda e: (_CATEGORY_PRIORITY.get(e.category, 99), e.name),
    )

    return sorted_entries[:max_techs]


# ---------------------------------------------------------------------------
# Query building
# ---------------------------------------------------------------------------

_CATEGORY_QUERY_TEMPLATES: dict[str, list[str]] = {
    "frontend_framework": [
        "{name} {version_str} setup and project structure best practices",
        "{name} {version_str} routing and state management patterns",
        "{name} {version_str} common pitfalls and migration gotchas",
        "{name} {version_str} performance optimization and security",
    ],
    "backend_framework": [
        "{name} {version_str} API design and middleware patterns",
        "{name} {version_str} authentication and security best practices",
        "{name} {version_str} error handling and validation patterns",
        "{name} {version_str} database integration and deployment",
    ],
    "database": [
        "{name} {version_str} schema design and indexing best practices",
        "{name} {version_str} connection management and performance",
        "{name} {version_str} security and backup strategies",
        "{name} {version_str} common pitfalls and scaling patterns",
    ],
    "orm": [
        "{name} {version_str} schema definition and migration patterns",
        "{name} {version_str} query optimization and N+1 prevention",
        "{name} {version_str} relationship modeling best practices",
        "{name} {version_str} transaction handling and error recovery",
    ],
    "ui_library": [
        "{name} {version_str} component patterns and theming setup",
        "{name} {version_str} accessibility and responsive design",
        "{name} {version_str} customization and override patterns",
        "{name} {version_str} performance and bundle size optimization",
    ],
    "testing": [
        "{name} {version_str} test setup and configuration",
        "{name} {version_str} mocking and fixture patterns",
        "{name} {version_str} async testing and common pitfalls",
        "{name} {version_str} CI/CD integration and coverage",
    ],
    "language": [
        "{name} {version_str} project structure and tooling",
        "{name} {version_str} type system and coding patterns",
    ],
    "other": [
        "{name} {version_str} setup and configuration best practices",
        "{name} {version_str} common patterns and pitfalls",
    ],
}


def build_research_queries(
    stack: list[TechStackEntry],
    max_per_tech: int = 4,
) -> list[tuple[str, str]]:
    """Generate (library_name, query) tuples for Context7 research.

    Returns version-aware, category-specific queries capped at
    *max_per_tech* per technology.
    """
    results: list[tuple[str, str]] = []

    for entry in stack:
        version_str = f"v{entry.version}" if entry.version else ""
        templates = _CATEGORY_QUERY_TEMPLATES.get(
            entry.category,
            _CATEGORY_QUERY_TEMPLATES["other"],
        )

        for template in templates[:max_per_tech]:
            query = template.format(
                name=entry.name,
                version_str=version_str,
            ).strip()
            # Clean up double spaces from empty version_str
            query = re.sub(r'\s+', ' ', query)
            results.append((entry.name, query))

    return results


# ---------------------------------------------------------------------------
# Expanded research queries (best practices, integration, code examples)
# ---------------------------------------------------------------------------

_EXPANDED_QUERY_TEMPLATES: list[str] = [
    "{name} {version_str} best practices for production applications",
    "{name} {version_str} common mistakes and anti-patterns to avoid",
    "{name} {version_str} code examples for common use cases",
    "{name} {version_str} error handling and debugging patterns",
]

# PRD feature keywords that trigger domain-specific research queries
_PRD_FEATURE_QUERY_MAP: dict[str, str] = {
    "file upload": "{name} {version_str} file upload implementation",
    "real-time": "{name} {version_str} WebSocket or real-time updates",
    "real time": "{name} {version_str} WebSocket or real-time updates",
    "websocket": "{name} {version_str} WebSocket implementation",
    "authentication": "{name} {version_str} authentication and JWT patterns",
    "auth": "{name} {version_str} authentication and authorization patterns",
    "jwt": "{name} {version_str} JWT token handling",
    "export": "{name} {version_str} data export to file patterns",
    "excel": "{name} {version_str} Excel file generation",
    "pdf": "{name} {version_str} PDF generation patterns",
    "email": "{name} {version_str} email sending integration",
    "notification": "{name} {version_str} notification system patterns",
    "pagination": "{name} {version_str} pagination and infinite scroll",
    "search": "{name} {version_str} search and filtering patterns",
    "drag": "{name} {version_str} drag and drop implementation",
    "chart": "{name} {version_str} data visualization and charts",
    "dashboard": "{name} {version_str} dashboard layout patterns",
    "form": "{name} {version_str} form handling and validation",
    "table": "{name} {version_str} data table with sorting and filtering",
    "role": "{name} {version_str} role-based access control patterns",
    "permission": "{name} {version_str} permission and authorization patterns",
    "cache": "{name} {version_str} caching strategies and patterns",
    "queue": "{name} {version_str} job queue and background processing",
    "i18n": "{name} {version_str} internationalization setup",
    "localization": "{name} {version_str} localization and translation",
}

# Cross-technology integration query templates.
# Keys are frozensets of (category_a, category_b) pairs.
_INTEGRATION_QUERY_TEMPLATES: dict[frozenset[str], list[str]] = {
    frozenset({"frontend_framework", "backend_framework"}): [
        "{fe_name} calling {be_name} API endpoints with HTTP client",
        "CORS configuration between {fe_name} and {be_name}",
        "{fe_name} proxy setup for {be_name} backend development",
    ],
    frozenset({"backend_framework", "orm"}): [
        "{be_name} integration with {orm_name} ORM setup and configuration",
        "{orm_name} migration workflow in {be_name} project",
    ],
    frozenset({"frontend_framework", "ui_library"}): [
        "{fe_name} with {ui_name} component library integration",
        "{ui_name} theming and customization in {fe_name} project",
    ],
    frozenset({"backend_framework", "database"}): [
        "{be_name} connection to {db_name} database setup",
        "{db_name} connection pooling and optimization in {be_name}",
    ],
}


def build_expanded_research_queries(
    stack: list[TechStackEntry],
    prd_text: str = "",
    max_expanded_per_tech: int = 4,
) -> list[tuple[str, str]]:
    """Generate expanded research queries beyond basic version lookups.

    Produces three types of additional queries:
    1. Best-practice/anti-pattern queries for each technology
    2. PRD-feature-aware queries (e.g. file upload, auth, real-time)
    3. Cross-technology integration queries (e.g. Angular + ASP.NET Core)

    Parameters
    ----------
    stack : list[TechStackEntry]
        Detected tech stack entries.
    prd_text : str
        PRD or task text for feature-aware query generation.
    max_expanded_per_tech : int
        Maximum expanded queries per technology (excluding integration).

    Returns
    -------
    list[tuple[str, str]]
        (library_name, query) tuples.
    """
    results: list[tuple[str, str]] = []
    prd_lower = prd_text.lower() if prd_text else ""

    # 1. Best-practice queries per technology
    for entry in stack:
        version_str = f"v{entry.version}" if entry.version else ""
        tech_queries: list[str] = []

        for template in _EXPANDED_QUERY_TEMPLATES:
            if len(tech_queries) >= max_expanded_per_tech:
                break
            query = template.format(name=entry.name, version_str=version_str).strip()
            query = re.sub(r'\s+', ' ', query)
            tech_queries.append(query)

        # 2. PRD-feature-aware queries
        if prd_lower:
            for keyword, template in _PRD_FEATURE_QUERY_MAP.items():
                if len(tech_queries) >= max_expanded_per_tech:
                    break
                if keyword in prd_lower:
                    query = template.format(name=entry.name, version_str=version_str).strip()
                    query = re.sub(r'\s+', ' ', query)
                    if query not in tech_queries:
                        tech_queries.append(query)

        for q in tech_queries[:max_expanded_per_tech]:
            results.append((entry.name, q))

    # 3. Cross-technology integration queries
    category_map: dict[str, TechStackEntry] = {}
    for entry in stack:
        if entry.category not in category_map:
            category_map[entry.category] = entry

    for cat_pair, templates in _INTEGRATION_QUERY_TEMPLATES.items():
        cats = list(cat_pair)
        if len(cats) != 2:
            continue
        cat_a, cat_b = cats[0], cats[1]
        entry_a = category_map.get(cat_a)
        entry_b = category_map.get(cat_b)
        if not entry_a or not entry_b:
            continue

        # Build substitution mapping
        substitutions: dict[str, str] = {}
        for cat, entry in [(cat_a, entry_a), (cat_b, entry_b)]:
            if cat == "frontend_framework":
                substitutions["fe_name"] = entry.name
            elif cat == "backend_framework":
                substitutions["be_name"] = entry.name
            elif cat == "orm":
                substitutions["orm_name"] = entry.name
            elif cat == "ui_library":
                substitutions["ui_name"] = entry.name
            elif cat == "database":
                substitutions["db_name"] = entry.name

        for template in templates:
            try:
                query = template.format(**substitutions).strip()
                query = re.sub(r'\s+', ' ', query)
                # Attribute to the first tech in the pair
                results.append((entry_a.name, query))
            except KeyError:
                continue  # Template placeholder not in substitutions — skip

    return results


def build_milestone_research_queries(
    milestone_title: str,
    milestone_requirements: str,
    tech_stack: list[TechStackEntry],
) -> list[tuple[str, str]]:
    """Generate Context7 queries specific to a milestone's technology needs.

    Cross-references the milestone requirements text against the detected
    tech stack to produce targeted queries relevant to this milestone only.

    Parameters
    ----------
    milestone_title : str
        The milestone title (e.g. "Auth & User Management").
    milestone_requirements : str
        The milestone's REQUIREMENTS.md content.
    tech_stack : list[TechStackEntry]
        Full project tech stack for cross-referencing.

    Returns
    -------
    list[tuple[str, str]]
        (library_name, query) tuples specific to this milestone.
    """
    results: list[tuple[str, str]] = []
    if not milestone_requirements and not milestone_title:
        return results

    combined_text = f"{milestone_title}\n{milestone_requirements}".lower()

    # Find which technologies are mentioned in this milestone
    relevant_techs: list[TechStackEntry] = []
    for entry in tech_stack:
        name_lower = entry.name.lower()
        if name_lower in combined_text:
            relevant_techs.append(entry)

    # If no explicit mentions, use framework-level techs (frontend + backend)
    # since they are always relevant
    if not relevant_techs:
        relevant_techs = [
            e for e in tech_stack
            if e.category in ("frontend_framework", "backend_framework")
        ]

    # Generate milestone-scoped queries
    for entry in relevant_techs:
        version_str = f"v{entry.version}" if entry.version else ""

        # PRD-feature queries scoped to this milestone
        for keyword, template in _PRD_FEATURE_QUERY_MAP.items():
            if keyword in combined_text:
                query = template.format(name=entry.name, version_str=version_str).strip()
                query = re.sub(r'\s+', ' ', query)
                if (entry.name, query) not in results:
                    results.append((entry.name, query))

    # Cap at reasonable number per milestone
    return results[:8]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_tech_research(
    result: TechResearchResult,
    min_coverage: float = 0.6,
) -> tuple[bool, list[str]]:
    """Validate that research meets minimum coverage threshold.

    Returns ``(is_valid, missing_tech_names)`` where *is_valid* is True
    when at least *min_coverage* fraction of techs have non-empty findings.
    """
    if result.techs_total == 0:
        return True, []

    missing = [
        entry.name
        for entry in result.stack
        if entry.name not in result.findings or not result.findings[entry.name].strip()
    ]

    covered = result.techs_total - len(missing)
    ratio = covered / result.techs_total if result.techs_total > 0 else 0.0

    result.techs_covered = covered
    result.is_complete = len(missing) == 0

    return ratio >= min_coverage, missing


# ---------------------------------------------------------------------------
# Summary extraction
# ---------------------------------------------------------------------------

def extract_research_summary(
    result: TechResearchResult,
    max_chars: int = 6000,
) -> str:
    """Produce a compact Markdown summary for prompt injection.

    Framework and database findings are prioritized. The output is
    truncated at *max_chars* on a line boundary.
    """
    if not result.findings:
        return ""

    # Order findings by category priority of their stack entries
    entry_map = {e.name: e for e in result.stack}
    ordered_names = sorted(
        result.findings.keys(),
        key=lambda n: (
            _CATEGORY_PRIORITY.get(
                entry_map[n].category, 99,
            ) if n in entry_map else 99,
            n,
        ),
    )

    lines: list[str] = []
    total = 0

    for name in ordered_names:
        content = result.findings[name].strip()
        if not content:
            continue

        entry = entry_map.get(name)
        version_str = f" (v{entry.version})" if entry and entry.version else ""
        header = f"## {name}{version_str}"

        block = f"{header}\n{content}\n"
        block_len = len(block)

        if total + block_len > max_chars:
            # Try to fit a truncated version
            remaining = max_chars - total
            if remaining > len(header) + 50:
                truncated = block[:remaining].rsplit('\n', 1)[0]
                lines.append(truncated)
            break

        lines.append(block)
        total += block_len

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parsing TECH_RESEARCH.md
# ---------------------------------------------------------------------------

_RE_TECH_SECTION = re.compile(
    r'^##\s+(.+?)(?:\s+\(v[^)]+\))?\s*$',
    re.MULTILINE,
)


def parse_tech_research_file(content: str) -> TechResearchResult:
    """Parse a TECH_RESEARCH.md file into a TechResearchResult.

    The file is expected to have ``## TechName (vVersion)`` sections
    written by the research sub-orchestrator.
    """
    result = TechResearchResult()
    if not content or not content.strip():
        return result

    sections = _RE_TECH_SECTION.split(content)
    # sections[0] is preamble, then alternating (name, body)

    findings: dict[str, str] = {}
    i = 1
    while i < len(sections) - 1:
        tech_name = sections[i].strip()
        body = sections[i + 1].strip()
        if tech_name and body:
            findings[tech_name] = body
        i += 2

    result.findings = findings
    result.techs_covered = len(findings)
    result.techs_total = len(findings)  # Will be updated by caller
    result.is_complete = True
    result.queries_made = 0  # Not tracked in file

    # Rebuild stack entries from parsed sections
    for tech_name in findings:
        # Try to extract version from the original content
        version_match = re.search(
            rf'^##\s+{re.escape(tech_name)}\s+\(v([^)]+)\)',
            content,
            re.MULTILINE,
        )
        version = version_match.group(1) if version_match else None
        result.stack.append(TechStackEntry(
            name=tech_name,
            version=version,
            category="other",  # Category not preserved in file
            source="tech_research",
        ))

    return result


# ---------------------------------------------------------------------------
# Prompt constant
# ---------------------------------------------------------------------------

TECH_RESEARCH_PROMPT = """[PHASE: TECH STACK RESEARCH]
[ROLE: Documentation Researcher]

You are performing mandatory tech stack research using Context7 documentation.
Your goal is to query official documentation for each technology and compile
actionable best practices that will guide the build.

## Technologies to Research

{tech_list}

## Instructions

For EACH technology listed above:

1. Call `mcp__context7__resolve-library-id` with the technology name to get the Context7 library ID.
2. Call `mcp__context7__query-docs` with the resolved library ID and each query below.
3. Extract the MOST RELEVANT patterns, pitfalls, and best practices.

{queries_block}

## Output

Write ALL findings to `{output_path}` using this format:

```markdown
# Tech Stack Research

## TechName (vVersion)
- **Setup**: Key setup patterns and project structure
- **Best Practices**: Recommended patterns from official docs
- **Pitfalls**: Common mistakes and what to avoid
- **Security**: Security-relevant configuration

## NextTechName (vVersion)
...
```

IMPORTANT:
- Include SPECIFIC code patterns and configuration examples when available.
- Focus on ACTIONABLE guidance, not general descriptions.
- If a library is not found in Context7, note it and move on.
- Do NOT fabricate documentation — only include what Context7 returns.
"""
