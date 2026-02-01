"""Codebase map — static analysis of a target project.

Discovers source files, extracts imports/exports, builds a dependency graph,
identifies high-fan-in shared files, and detects frameworks.  The resulting
``CodebaseMap`` is injected into the orchestrator prompt so every agent has
structural awareness of the project it is working on.

All analysis is performed with the Python standard library only (no external
dependencies).  Heavy lifting runs synchronously inside an executor so the
async entry-point can enforce a wall-clock timeout.
"""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ._lang import _LANGUAGE_MAP as _CORE_LANGUAGE_MAP, detect_language as _detect_language_core

if sys.version_info >= (3, 11):
    import tomllib
else:
    tomllib = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ModuleInfo:
    """Metadata for a single source file discovered during the scan."""

    path: str                    # relative path from project root (POSIX-normalized)
    language: str                # "typescript" | "python" | "javascript" | ...
    role: str                    # "component" | "service" | "util" | "config" | "test" | "style" | "unknown"
    exports: list[str]           # exported symbol names
    imports: list[str]           # paths this module imports from
    lines: int                   # line count


@dataclass
class ImportEdge:
    """A directed edge in the import graph."""

    source: str                  # importing module path
    target: str                  # imported module path
    symbols: list[str]           # specific imports (empty = wildcard/default)


@dataclass
class SharedFile:
    """A file imported by many other modules (high fan-in)."""

    path: str
    importers: list[str]         # modules that import this file
    fan_in: int                  # len(importers)
    risk: str                    # "high" (>=8) | "medium" (>=5) | "low" (>=3)


@dataclass
class FrameworkInfo:
    """A detected framework or meta-framework."""

    name: str                    # "next.js" | "express" | "fastapi" | "django" | ...
    version: str | None
    detected_from: str           # "package.json" | "pyproject.toml" | ...


@dataclass
class CodebaseMap:
    """Complete structural overview of a project."""

    root: str
    modules: list[ModuleInfo]
    import_graph: list[ImportEdge]
    shared_files: list[SharedFile]
    frameworks: list[FrameworkInfo]
    total_files: int
    total_lines: int
    primary_language: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_EXCLUDE: set[str] = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    ".next", "venv", ".env", ".venv", "coverage", ".tox",
}

_SOURCE_EXTENSIONS: set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
}

# Extended map for codebase_map (includes non-code files for completeness)
_LANGUAGE_MAP: dict[str, str] = {
    **_CORE_LANGUAGE_MAP,
    ".css": "style",
    ".scss": "style",
    ".less": "style",
    ".html": "html",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".sql": "sql",
    ".md": "markdown",
    ".sh": "shell",
    ".bash": "shell",
}

_MAX_FILES = 5000

# Size limits in bytes.
_MAX_SIZE_PY = 50 * 1024       # 50 KB
_MAX_SIZE_TS = 100 * 1024      # 100 KB

# Framework detection maps ---------------------------------------------------

_JS_FRAMEWORK_MAP: dict[str, str] = {
    "next": "next.js",
    "express": "express",
    "react": "react",
    "vue": "vue",
    "nuxt": "nuxt",
    "svelte": "svelte",
    "angular": "angular",
    "fastify": "fastify",
    "koa": "koa",
    "nestjs": "nestjs",
    "@nestjs/core": "nestjs",
    "gatsby": "gatsby",
    "remix": "remix",
    "@remix-run/node": "remix",
    "hono": "hono",
    "electron": "electron",
}

_PY_FRAMEWORK_NAMES: dict[str, str] = {
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "starlette": "starlette",
    "tornado": "tornado",
    "sanic": "sanic",
    "aiohttp": "aiohttp",
    "bottle": "bottle",
    "falcon": "falcon",
    "litestar": "litestar",
}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _normalize_path(path: Path, root: Path) -> str:
    """Convert *path* to a POSIX-style path relative to *root*."""
    return path.relative_to(root).as_posix()


def _get_language(path: Path) -> str:
    """Return the language identifier for a source file."""
    return _LANGUAGE_MAP.get(path.suffix.lower(), "unknown")


# ---------------------------------------------------------------------------
# Role classification
# ---------------------------------------------------------------------------

def _classify_role(path: Path) -> str:
    """Classify a file's architectural role based on path heuristics."""
    parts_lower = [p.lower() for p in path.parts]
    name_lower = path.stem.lower()

    # Test files / directories
    if any(p in ("test", "tests", "__tests__", "spec", "specs") for p in parts_lower):
        return "test"
    if name_lower.endswith((".test", ".spec", "_test", "_spec")):
        return "test"
    if name_lower.startswith("test_"):
        return "test"

    # Config files
    if any(p in ("config", "configs", "configuration") for p in parts_lower):
        return "config"
    if name_lower.endswith(".config") or name_lower.startswith("."):
        return "config"
    if name_lower in (
        "settings", "config", "configuration", "setup",
        "tsconfig", "eslintrc", "prettierrc", "babel",
        "webpack", "vite", "rollup", "jest",
    ):
        return "config"

    # Styles
    if any(p in ("styles", "css", "scss", "style") for p in parts_lower):
        return "style"
    if path.suffix.lower() in (".css", ".scss", ".less", ".sass"):
        return "style"

    # Components (React, Vue, Svelte, etc.)
    if any(p in ("components", "component", "widgets", "ui") for p in parts_lower):
        return "component"

    # Services / API layer
    if any(p in ("services", "service", "api", "apis", "routes", "controllers", "handlers") for p in parts_lower):
        return "service"

    # Utilities / libraries
    if any(p in ("utils", "util", "utilities", "lib", "libs", "helpers", "helper", "shared", "common") for p in parts_lower):
        return "util"

    return "unknown"


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _discover_source_files(root: Path, exclude: set[str]) -> list[Path]:
    """Walk *root* and collect source files, pruning excluded directories in-place.

    Uses ``os.walk()`` with in-place ``dirnames`` mutation for O(1) directory
    pruning — intentionally avoids ``pathlib.rglob()`` which cannot prune.
    """
    result: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # In-place prune so os.walk() does not descend into excluded dirs.
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in _SOURCE_EXTENSIONS:
                result.append(fpath)
    return result


# ---------------------------------------------------------------------------
# Python: export extraction
# ---------------------------------------------------------------------------

def _extract_exports_py(content: str) -> list[str]:
    """Extract exported symbols from a Python module using ``ast``.

    Priority:
    1. If ``__all__`` is defined, its contents are authoritative.
    2. Otherwise, collect top-level public classes, functions, and simple
       assignments (skip names beginning with ``_``).
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    # 1. Check for __all__ — authoritative if present.
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return _extract_all_value(node.value)
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                if node.value is not None:
                    return _extract_all_value(node.value)

    # 2. Fallback: scan tree.body for public definitions.
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    exports.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                exports.append(node.target.id)
    return exports


def _extract_all_value(node: ast.expr) -> list[str]:
    """Extract string elements from an ``__all__`` assignment value node."""
    names: list[str] = []
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                names.append(elt.value)
    return names


# ---------------------------------------------------------------------------
# TypeScript / JavaScript: export extraction
# ---------------------------------------------------------------------------

# Each pattern captures the exported symbol name in group 1.
_TS_EXPORT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"export\s+function\s+(\w+)"),
    re.compile(r"export\s+async\s+function\s+(\w+)"),
    re.compile(r"export\s+class\s+(\w+)"),
    re.compile(r"export\s+abstract\s+class\s+(\w+)"),
    re.compile(r"export\s+const\s+(\w+)"),
    re.compile(r"export\s+let\s+(\w+)"),
    re.compile(r"export\s+var\s+(\w+)"),
    re.compile(r"export\s+type\s+(\w+)"),
    re.compile(r"export\s+interface\s+(\w+)"),
    re.compile(r"export\s+enum\s+(\w+)"),
    re.compile(r"export\s+default\s+(?:class|function|abstract\s+class)\s+(\w+)"),
    re.compile(r"export\s+default\s+(\w+)"),
    # Re-exports: export { Foo, Bar } from '...'  and  export { Foo, Bar }
    re.compile(r"export\s*\{([^}]+)\}"),
    # module.exports = { a, b }
    re.compile(r"module\.exports\s*=\s*\{([^}]+)\}"),
]

# Star re-export — no named symbol, captured separately.
_TS_EXPORT_STAR_RE = re.compile(r"export\s+\*\s+from\s+['\"]([^'\"]+)['\"]")


def _extract_exports_ts(content: str) -> list[str]:
    """Extract exported symbol names from a TS/JS file via regex."""
    exports: list[str] = []
    seen: set[str] = set()

    for pat in _TS_EXPORT_PATTERNS:
        for match in pat.finditer(content):
            raw = match.group(1)
            # The { A, B as C } patterns need splitting.
            if "," in raw or " as " in raw:
                for token in raw.split(","):
                    token = token.strip()
                    if not token:
                        continue
                    # "Foo as Bar" — the *exported* name is Bar.
                    if " as " in token:
                        token = token.split(" as ")[-1].strip()
                    if token and token not in seen:
                        seen.add(token)
                        exports.append(token)
            else:
                name = raw.strip()
                if name and name not in seen:
                    seen.add(name)
                    exports.append(name)

    # Star re-exports do not contribute named symbols but confirm the file
    # is a barrel; we intentionally omit them from the name list.

    return exports


# ---------------------------------------------------------------------------
# Python: import extraction
# ---------------------------------------------------------------------------

def _extract_imports_py(content: str) -> list[str]:
    """Extract imported module paths from Python source using ``ast.walk()``.

    Walking the full tree (rather than just ``tree.body``) ensures we catch
    imports hidden inside ``if TYPE_CHECKING:`` blocks and similar guards.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    modules: list[str] = []
    seen: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in seen:
                    seen.add(alias.name)
                    modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module not in seen:
                seen.add(node.module)
                modules.append(node.module)

    return modules


# ---------------------------------------------------------------------------
# TypeScript / JavaScript: import extraction
# ---------------------------------------------------------------------------

_TS_IMPORT_PATTERNS: list[re.Pattern[str]] = [
    # import { X } from 'Y'  /  import X from 'Y'  /  import * as X from 'Y'
    re.compile(r"""import\s+(?:[\w{},\s*]+\s+from\s+)?['"]([^'"]+)['"]"""),
    # require('Y')
    re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    # Dynamic import('Y')
    re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
]


def _extract_imports_ts(content: str) -> list[str]:
    """Extract import paths from TS/JS source via regex."""
    paths: list[str] = []
    seen: set[str] = set()

    for pat in _TS_IMPORT_PATTERNS:
        for match in pat.finditer(content):
            spec = match.group(1)
            if spec not in seen:
                seen.add(spec)
                paths.append(spec)

    return paths


# ---------------------------------------------------------------------------
# Import resolution
# ---------------------------------------------------------------------------

_TS_EXTENSIONS: tuple[str, ...] = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
_TS_INDEX_NAMES: tuple[str, ...] = tuple(f"index{ext}" for ext in _TS_EXTENSIONS)


def _resolve_import_path(source: Path, import_spec: str, root: Path) -> str | None:
    """Try to resolve an import specifier to an actual file path.

    Handles:
    - Relative paths (``./foo``, ``../bar``)
    - Bare package specifiers (returns ``None`` — external dependency)
    - Python dotted module paths (``my.package.module``)

    Returns a POSIX-normalized relative path on success, else ``None``.

    Security: all resolved paths are verified to stay within *root* via
    both ``Path.resolve()`` comparison and ``Path.relative_to()`` (which
    raises ``ValueError`` for paths outside the base).  This prevents
    path-traversal attacks from crafted import specifiers.
    """
    resolved_root = root.resolve()

    def _is_within_root(p: Path) -> bool:
        """Ensure resolved path stays within project root (path traversal protection)."""
        try:
            resolved = p.resolve()
            return str(resolved).startswith(str(resolved_root))
        except (OSError, ValueError):
            return False

    # --- Relative path (JS/TS style) -----------------------------------------
    if import_spec.startswith("."):
        base_dir = source.parent
        candidate = (base_dir / import_spec).resolve()

        # Path traversal check: reject paths that escape the project root.
        if not _is_within_root(candidate):
            return None

        # Exact match with extension.
        if candidate.is_file():
            try:
                return _normalize_path(candidate, root)
            except ValueError:
                return None

        # Try adding common extensions.
        for ext in _TS_EXTENSIONS:
            attempt = candidate.with_suffix(ext)
            if attempt.is_file():
                try:
                    return _normalize_path(attempt, root)
                except ValueError:
                    return None

        # Try as directory with index file.
        if candidate.is_dir():
            for idx in _TS_INDEX_NAMES:
                attempt = candidate / idx
                if attempt.is_file():
                    try:
                        return _normalize_path(attempt, root)
                    except ValueError:
                        return None

        return None

    # --- Python dotted imports ------------------------------------------------
    parts = import_spec.split(".")
    # Try as a path from project root.
    candidate = root.joinpath(*parts)

    # Path traversal check: reject paths that escape the project root.
    if not _is_within_root(candidate):
        return None

    # foo.bar.baz  ->  foo/bar/baz.py
    py_file = candidate.with_suffix(".py")
    if py_file.is_file():
        try:
            return _normalize_path(py_file, root)
        except ValueError:
            return None

    # foo.bar.baz  ->  foo/bar/baz/__init__.py
    pkg_init = candidate / "__init__.py"
    if pkg_init.is_file():
        try:
            return _normalize_path(pkg_init, root)
        except ValueError:
            return None

    # External / unresolvable.
    return None


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

def _detect_framework(root: Path) -> list[FrameworkInfo]:
    """Detect frameworks from manifest files at the project root."""
    frameworks: list[FrameworkInfo] = []

    # --- package.json ---------------------------------------------------------
    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            data = {}
        all_deps: dict[str, str] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            deps = data.get(key)
            if isinstance(deps, dict):
                all_deps.update(deps)
        for pkg_name, display_name in _JS_FRAMEWORK_MAP.items():
            if pkg_name in all_deps:
                frameworks.append(FrameworkInfo(
                    name=display_name,
                    version=all_deps[pkg_name],
                    detected_from="package.json",
                ))

    # --- pyproject.toml -------------------------------------------------------
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        frameworks.extend(_parse_pyproject(pyproject))

    # --- requirements.txt -----------------------------------------------------
    req_txt = root / "requirements.txt"
    if req_txt.is_file():
        try:
            text = req_txt.read_text(encoding="utf-8-sig")
        except OSError:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Match lines like "fastapi==0.95.0", "django>=4.0", "flask"
            m = re.match(r"^([A-Za-z0-9_-]+)\s*(?:[><=!~].*)?$", line)
            if m:
                dep_name = m.group(1).lower().replace("-", "_")
                if dep_name in _PY_FRAMEWORK_NAMES:
                    # Extract version if present.
                    ver_match = re.search(r"[><=!~]+\s*([0-9][^\s,;]*)", line)
                    ver = ver_match.group(1) if ver_match else None
                    # Avoid duplicates (pyproject.toml may have already found it).
                    if not any(f.name == _PY_FRAMEWORK_NAMES[dep_name] for f in frameworks):
                        frameworks.append(FrameworkInfo(
                            name=_PY_FRAMEWORK_NAMES[dep_name],
                            version=ver,
                            detected_from="requirements.txt",
                        ))

    return frameworks


def _parse_pyproject(path: Path) -> list[FrameworkInfo]:
    """Extract framework information from a ``pyproject.toml`` file."""
    results: list[FrameworkInfo] = []

    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError:
        return results

    if tomllib is not None:
        try:
            data = tomllib.loads(raw)
        except (KeyError, TypeError, ValueError):
            data = {}
        # Look in [project].dependencies and [tool.poetry].dependencies.
        deps: list[str] = []
        project_deps = (data.get("project") or {}).get("dependencies")
        if isinstance(project_deps, list):
            deps.extend(project_deps)
        poetry_deps = (
            (data.get("tool") or {}).get("poetry") or {}
        ).get("dependencies")
        if isinstance(poetry_deps, dict):
            deps.extend(poetry_deps.keys())

        for dep_line in deps:
            # "fastapi>=0.95" — grab name and optional version.
            m = re.match(r"^([A-Za-z0-9_-]+)\s*(?:[><=!~](.*))?", dep_line)
            if not m:
                continue
            dep_name = m.group(1).lower().replace("-", "_")
            if dep_name in _PY_FRAMEWORK_NAMES:
                ver_match = re.search(r"([0-9][^\s,;]*)", dep_line)
                ver = ver_match.group(1) if ver_match else None
                results.append(FrameworkInfo(
                    name=_PY_FRAMEWORK_NAMES[dep_name],
                    version=ver,
                    detected_from="pyproject.toml",
                ))
    else:
        # Regex fallback for Python < 3.11 (no tomllib).
        for dep_name, fw_name in _PY_FRAMEWORK_NAMES.items():
            # Look for the dependency name anywhere in the file.
            pattern = re.compile(
                rf"""['"]?{re.escape(dep_name)}['"]?\s*(?:[><=!~]+\s*['"]?([0-9][^\s'",$]*)|)""",
                re.IGNORECASE,
            )
            m = pattern.search(raw)
            if m:
                results.append(FrameworkInfo(
                    name=fw_name,
                    version=m.group(1) if m.group(1) else None,
                    detected_from="pyproject.toml",
                ))

    return results


# ---------------------------------------------------------------------------
# Import graph construction
# ---------------------------------------------------------------------------

def _build_import_graph(modules: list[ModuleInfo], root: Path) -> list[ImportEdge]:
    """Build the directed import graph by resolving each module's imports."""
    edges: list[ImportEdge] = []
    module_paths: set[str] = {m.path for m in modules}

    for mod in modules:
        source_path = root / mod.path
        for imp in mod.imports:
            resolved = _resolve_import_path(source_path, imp, root)
            if resolved and resolved in module_paths and resolved != mod.path:
                edges.append(ImportEdge(
                    source=mod.path,
                    target=resolved,
                    symbols=[],  # symbol-level tracking would need deeper parsing
                ))

    return edges


# ---------------------------------------------------------------------------
# Shared-file detection
# ---------------------------------------------------------------------------

def _find_shared_files(import_graph: list[ImportEdge]) -> list[SharedFile]:
    """Identify files with fan-in >= 3 and rank by risk."""
    importers_map: dict[str, list[str]] = {}
    for edge in import_graph:
        importers_map.setdefault(edge.target, [])
        if edge.source not in importers_map[edge.target]:
            importers_map[edge.target].append(edge.source)

    shared: list[SharedFile] = []
    for target, importers in importers_map.items():
        fan_in = len(importers)
        if fan_in < 3:
            continue
        if fan_in >= 8:
            risk = "high"
        elif fan_in >= 5:
            risk = "medium"
        else:
            risk = "low"
        shared.append(SharedFile(
            path=target,
            importers=sorted(importers),
            fan_in=fan_in,
            risk=risk,
        ))

    # Sort by fan-in descending for relevance.
    shared.sort(key=lambda s: s.fan_in, reverse=True)
    return shared


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def _detect_primary_language(modules: list[ModuleInfo]) -> str:
    """Return the most common language across all discovered modules."""
    if not modules:
        return "unknown"
    counter: Counter[str] = Counter()
    for mod in modules:
        if mod.language not in ("unknown", "json", "style"):
            counter[mod.language] += 1
    if not counter:
        return "unknown"
    return counter.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Synchronous core
# ---------------------------------------------------------------------------

def _generate_map_sync(root: Path) -> CodebaseMap:
    """Perform the full scan synchronously.  Called inside an executor."""
    exclude = set(_DEFAULT_EXCLUDE)
    files = _discover_source_files(root, exclude)

    # Cap at _MAX_FILES to prevent unbounded work.
    files = files[:_MAX_FILES]

    modules: list[ModuleInfo] = []
    for fpath in files:
        lang = _get_language(fpath)
        if lang in ("unknown", "json", "style"):
            # We still record style/json for counts but skip deep parsing.
            pass

        # Size guard.
        try:
            size = fpath.stat().st_size
        except OSError:
            continue
        max_size = _MAX_SIZE_TS if lang in ("typescript", "javascript") else _MAX_SIZE_PY
        if size > max_size:
            continue
        if size == 0:
            continue

        # Read content.
        try:
            content = fpath.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue

        rel_path = _normalize_path(fpath, root)
        role = _classify_role(fpath)

        if lang == "python":
            exports = _extract_exports_py(content)
            imports = _extract_imports_py(content)
        elif lang in ("typescript", "javascript"):
            exports = _extract_exports_ts(content)
            imports = _extract_imports_ts(content)
        else:
            exports = []
            imports = []

        line_count = content.count("\n") + 1

        modules.append(ModuleInfo(
            path=rel_path,
            language=lang,
            role=role,
            exports=exports,
            imports=imports,
            lines=line_count,
        ))

    import_graph = _build_import_graph(modules, root)
    shared_files = _find_shared_files(import_graph)
    frameworks = _detect_framework(root)
    total_lines = sum(m.lines for m in modules)
    primary_language = _detect_primary_language(modules)

    return CodebaseMap(
        root=str(root),
        modules=modules,
        import_graph=import_graph,
        shared_files=shared_files,
        frameworks=frameworks,
        total_files=len(modules),
        total_lines=total_lines,
        primary_language=primary_language,
    )


# ---------------------------------------------------------------------------
# Async entry-point
# ---------------------------------------------------------------------------

async def generate_codebase_map(
    project_root: str | Path,
    timeout: float = 30.0,
) -> CodebaseMap:
    """Scan *project_root* and return a complete ``CodebaseMap``.

    The synchronous analysis work is offloaded to an executor so the
    caller can enforce a wall-clock timeout (default 30 s).

    Parameters
    ----------
    project_root:
        Path to the project directory to scan.
    timeout:
        Maximum wall-clock seconds before the scan is cancelled.
        Defaults to 30.0; callers should pass
        ``config.codebase_map.timeout_seconds`` to honour user config.
    """
    root = Path(project_root).resolve()
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, _generate_map_sync, root),
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------

def summarize_map(cmap: CodebaseMap, max_lines: int = 200) -> str:
    """Render a human-readable markdown summary of a ``CodebaseMap``.

    The output is intended for injection into an LLM prompt so every agent
    has structural context.  It is truncated to *max_lines* to stay within
    token budgets.
    """
    lines: list[str] = []

    # -- Header / overview ----------------------------------------------------
    lines.append("# Codebase Map")
    lines.append("")
    lines.append(f"- **Root:** `{cmap.root}`")
    lines.append(f"- **Total files:** {cmap.total_files}")
    lines.append(f"- **Total lines:** {cmap.total_lines:,}")
    lines.append(f"- **Primary language:** {cmap.primary_language}")

    # Frameworks
    if cmap.frameworks:
        fw_parts: list[str] = []
        for fw in cmap.frameworks:
            if fw.version:
                fw_parts.append(f"{fw.name} ({fw.version})")
            else:
                fw_parts.append(fw.name)
        lines.append(f"- **Frameworks:** {', '.join(fw_parts)}")
    lines.append("")

    # -- Module breakdown by role ---------------------------------------------
    role_counts: Counter[str] = Counter()
    lang_counts: Counter[str] = Counter()
    for mod in cmap.modules:
        role_counts[mod.role] += 1
        lang_counts[mod.language] += 1

    lines.append("## Module Breakdown")
    lines.append("")
    lines.append("| Role | Count |")
    lines.append("|------|-------|")
    for role, count in role_counts.most_common():
        lines.append(f"| {role} | {count} |")
    lines.append("")

    if len(lang_counts) > 1:
        lines.append("| Language | Files |")
        lines.append("|----------|-------|")
        for lang, count in lang_counts.most_common():
            lines.append(f"| {lang} | {count} |")
        lines.append("")

    # -- Shared / high-fan-in files -------------------------------------------
    if cmap.shared_files:
        lines.append("## Shared Files (high fan-in)")
        lines.append("")
        lines.append("| File | Fan-in | Risk |")
        lines.append("|------|--------|------|")
        for sf in cmap.shared_files[:20]:  # Cap the table.
            lines.append(f"| `{sf.path}` | {sf.fan_in} | {sf.risk} |")
        lines.append("")

    # -- Import graph statistics ----------------------------------------------
    lines.append("## Import Graph")
    lines.append("")
    lines.append(f"- **Edges:** {len(cmap.import_graph)}")
    if cmap.import_graph:
        source_set = {e.source for e in cmap.import_graph}
        target_set = {e.target for e in cmap.import_graph}
        lines.append(f"- **Importing modules:** {len(source_set)}")
        lines.append(f"- **Imported modules:** {len(target_set)}")
        isolated = set()
        all_in_graph = source_set | target_set
        all_paths = {m.path for m in cmap.modules}
        isolated = all_paths - all_in_graph
        if isolated:
            lines.append(f"- **Isolated modules (no imports/exports resolved):** {len(isolated)}")
    lines.append("")

    # -- Truncate to max_lines ------------------------------------------------
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("")
        lines.append(f"_(truncated to {max_lines} lines)_")

    return "\n".join(lines)
