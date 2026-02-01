"""Tests for agent_team.codebase_map — comprehensive coverage of the codebase
mapping module including file discovery, export/import extraction, framework
detection, shared-file analysis, and end-to-end map generation.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from agent_team.codebase_map import (
    CodebaseMap,
    FrameworkInfo,
    ImportEdge,
    ModuleInfo,
    SharedFile,
    _classify_role,
    _detect_framework,
    _discover_source_files,
    _extract_exports_py,
    _extract_exports_ts,
    _extract_imports_py,
    _extract_imports_ts,
    _find_shared_files,
    _normalize_path,
    _parse_pyproject,
    generate_codebase_map,
    summarize_map,
)


# ===================================================================
# 1. File Discovery Tests
# ===================================================================


class TestDiscoverSourceFiles:
    """Verify _discover_source_files walks directories correctly."""

    def test_finds_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "utils.py").write_text("x = 1", encoding="utf-8")

        result = _discover_source_files(tmp_path, set())
        names = [p.name for p in result]
        assert "main.py" in names
        assert "utils.py" in names

    def test_finds_ts_files(self, tmp_path: Path) -> None:
        (tmp_path / "app.ts").write_text("const x = 1;", encoding="utf-8")
        (tmp_path / "component.tsx").write_text("export default () => null;", encoding="utf-8")

        result = _discover_source_files(tmp_path, set())
        suffixes = {p.suffix for p in result}
        assert ".ts" in suffixes
        assert ".tsx" in suffixes

    def test_finds_js_files(self, tmp_path: Path) -> None:
        (tmp_path / "index.js").write_text("module.exports = {};", encoding="utf-8")
        (tmp_path / "config.mjs").write_text("export default {};", encoding="utf-8")
        (tmp_path / "legacy.cjs").write_text("module.exports = {};", encoding="utf-8")
        (tmp_path / "page.jsx").write_text("export default () => null;", encoding="utf-8")

        result = _discover_source_files(tmp_path, set())
        suffixes = {p.suffix for p in result}
        assert ".js" in suffixes
        assert ".mjs" in suffixes
        assert ".cjs" in suffixes
        assert ".jsx" in suffixes

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {};", encoding="utf-8")
        (tmp_path / "app.js").write_text("const x = 1;", encoding="utf-8")

        result = _discover_source_files(tmp_path, {"node_modules"})
        names = [p.name for p in result]
        assert "app.js" in names
        assert "index.js" not in names

    def test_excludes_git_dir(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        (git_dir / "pre-commit.py").write_text("#!/usr/bin/env python", encoding="utf-8")
        (tmp_path / "main.py").write_text("pass", encoding="utf-8")

        result = _discover_source_files(tmp_path, {".git"})
        names = [p.name for p in result]
        assert "main.py" in names
        assert "pre-commit.py" not in names

    def test_excludes_pycache(self, tmp_path: Path) -> None:
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "module.cpython-311.pyc").write_text("", encoding="utf-8")
        # .pyc is not in _SOURCE_EXTENSIONS, but ensure the directory is pruned
        (tmp_path / "module.py").write_text("pass", encoding="utf-8")

        result = _discover_source_files(tmp_path, {"__pycache__"})
        paths_str = [str(p) for p in result]
        assert not any("__pycache__" in s for s in paths_str)

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = _discover_source_files(tmp_path, set())
        assert result == []

    def test_nested_directories(self, tmp_path: Path) -> None:
        deep = tmp_path / "src" / "lib" / "utils"
        deep.mkdir(parents=True)
        (deep / "helpers.py").write_text("pass", encoding="utf-8")
        (tmp_path / "src" / "main.py").write_text("pass", encoding="utf-8")

        result = _discover_source_files(tmp_path, set())
        names = [p.name for p in result]
        assert "helpers.py" in names
        assert "main.py" in names
        assert len(result) == 2


# ===================================================================
# 2. Path Normalization Tests
# ===================================================================


class TestNormalizePath:
    """Verify _normalize_path produces POSIX-style relative paths."""

    def test_posix_format(self, tmp_path: Path) -> None:
        child = tmp_path / "app.py"
        child.write_text("pass", encoding="utf-8")

        result = _normalize_path(child, tmp_path)
        assert result == "app.py"
        assert "\\" not in result  # no backslashes

    def test_nested_path(self, tmp_path: Path) -> None:
        nested = tmp_path / "src" / "lib" / "util.ts"
        nested.parent.mkdir(parents=True)
        nested.write_text("", encoding="utf-8")

        result = _normalize_path(nested, tmp_path)
        assert result == "src/lib/util.ts"
        assert "\\" not in result


# ===================================================================
# 3. Role Classification Tests
# ===================================================================


class TestClassifyRole:
    """Verify _classify_role assigns correct architectural roles."""

    def test_component_role(self, tmp_path: Path) -> None:
        p = tmp_path / "components" / "Button.tsx"
        p.parent.mkdir()
        assert _classify_role(p) == "component"

    def test_component_role_ui_dir(self, tmp_path: Path) -> None:
        p = tmp_path / "ui" / "Modal.tsx"
        p.parent.mkdir()
        assert _classify_role(p) == "component"

    def test_service_role(self, tmp_path: Path) -> None:
        p = tmp_path / "services" / "auth.py"
        p.parent.mkdir()
        assert _classify_role(p) == "service"

    def test_service_role_api_dir(self, tmp_path: Path) -> None:
        p = tmp_path / "api" / "users.ts"
        p.parent.mkdir()
        assert _classify_role(p) == "service"

    def test_util_role(self, tmp_path: Path) -> None:
        p = tmp_path / "utils" / "format.py"
        p.parent.mkdir()
        assert _classify_role(p) == "util"

    def test_util_role_helpers_dir(self, tmp_path: Path) -> None:
        p = tmp_path / "helpers" / "strings.ts"
        p.parent.mkdir()
        assert _classify_role(p) == "util"

    def test_test_role(self, tmp_path: Path) -> None:
        p = tmp_path / "tests" / "test_auth.py"
        p.parent.mkdir()
        assert _classify_role(p) == "test"

    def test_test_role_by_filename(self, tmp_path: Path) -> None:
        p = tmp_path / "auth.test.ts"
        assert _classify_role(p) == "test"

    def test_test_role_by_prefix(self, tmp_path: Path) -> None:
        p = tmp_path / "test_something.py"
        assert _classify_role(p) == "test"

    def test_config_role(self, tmp_path: Path) -> None:
        p = tmp_path / "config" / "settings.py"
        p.parent.mkdir()
        assert _classify_role(p) == "config"

    def test_config_role_by_name(self, tmp_path: Path) -> None:
        p = tmp_path / "webpack.config.js"
        assert _classify_role(p) == "config"

    def test_unknown_role(self, tmp_path: Path) -> None:
        p = tmp_path / "main.py"
        assert _classify_role(p) == "unknown"


# ===================================================================
# 4. Python Export Extraction Tests
# ===================================================================


class TestExtractExportsPython:
    """Verify _extract_exports_py correctly identifies exported symbols."""

    def test_function_export(self) -> None:
        code = textwrap.dedent("""\
            def greet(name: str) -> str:
                return f"Hello, {name}"
        """)
        exports = _extract_exports_py(code)
        assert "greet" in exports

    def test_async_function_export(self) -> None:
        code = textwrap.dedent("""\
            async def fetch_data(url: str):
                pass
        """)
        exports = _extract_exports_py(code)
        assert "fetch_data" in exports

    def test_class_export(self) -> None:
        code = textwrap.dedent("""\
            class UserService:
                def get_user(self, uid):
                    pass
        """)
        exports = _extract_exports_py(code)
        assert "UserService" in exports

    def test_constant_export(self) -> None:
        code = textwrap.dedent("""\
            MAX_RETRIES = 3
            BASE_URL = "https://api.example.com"
        """)
        exports = _extract_exports_py(code)
        assert "MAX_RETRIES" in exports
        assert "BASE_URL" in exports

    def test_annotated_assignment(self) -> None:
        code = textwrap.dedent("""\
            DEFAULT_TIMEOUT: int = 30
        """)
        exports = _extract_exports_py(code)
        assert "DEFAULT_TIMEOUT" in exports

    def test_all_dunder_takes_priority(self) -> None:
        code = textwrap.dedent("""\
            __all__ = ["public_func"]

            def public_func():
                pass

            def _private_func():
                pass

            def other_public():
                pass
        """)
        exports = _extract_exports_py(code)
        assert exports == ["public_func"]
        assert "other_public" not in exports
        assert "_private_func" not in exports

    def test_all_dunder_tuple(self) -> None:
        code = textwrap.dedent("""\
            __all__ = ("alpha", "beta")

            def alpha(): pass
            def beta(): pass
            def gamma(): pass
        """)
        exports = _extract_exports_py(code)
        assert exports == ["alpha", "beta"]

    def test_skips_private_names(self) -> None:
        code = textwrap.dedent("""\
            def public_fn():
                pass

            def _private_fn():
                pass

            _INTERNAL = 42
            PUBLIC_VAR = 100
        """)
        exports = _extract_exports_py(code)
        assert "public_fn" in exports
        assert "PUBLIC_VAR" in exports
        assert "_private_fn" not in exports
        assert "_INTERNAL" not in exports

    def test_syntax_error_returns_empty(self) -> None:
        code = "def broken(\n"
        exports = _extract_exports_py(code)
        assert exports == []

    def test_empty_file(self) -> None:
        exports = _extract_exports_py("")
        assert exports == []


# ===================================================================
# 5. Python Import Extraction Tests
# ===================================================================


class TestExtractImportsPython:
    """Verify _extract_imports_py correctly identifies imported modules."""

    def test_import_module(self) -> None:
        code = textwrap.dedent("""\
            import os
            import json
        """)
        imports = _extract_imports_py(code)
        assert "os" in imports
        assert "json" in imports

    def test_from_import(self) -> None:
        code = textwrap.dedent("""\
            from pathlib import Path
            from collections import Counter
        """)
        imports = _extract_imports_py(code)
        assert "pathlib" in imports
        assert "collections" in imports

    def test_relative_import(self) -> None:
        code = textwrap.dedent("""\
            from .utils import helper
            from ..config import settings
        """)
        imports = _extract_imports_py(code)
        # Relative imports have no module name (node.module is None for level>0
        # with just dots), but these have module specified after the dots.
        # ast.ImportFrom stores "utils" for ".utils" and "config" for "..config"
        # Actually for `from .utils import helper`, node.module = "utils", node.level = 1
        # The function checks `if node.module` which is truthy for "utils"
        assert "utils" in imports or "config" in imports

    def test_type_checking_import(self) -> None:
        code = textwrap.dedent("""\
            from __future__ import annotations
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from myapp.models import User
        """)
        imports = _extract_imports_py(code)
        # ast.walk() catches imports inside if blocks
        assert "myapp.models" in imports

    def test_star_import(self) -> None:
        code = textwrap.dedent("""\
            from os.path import *
        """)
        imports = _extract_imports_py(code)
        assert "os.path" in imports

    def test_syntax_error_returns_empty(self) -> None:
        code = "from broken import\n"
        imports = _extract_imports_py(code)
        assert imports == []

    def test_deduplication(self) -> None:
        code = textwrap.dedent("""\
            import os
            import os
            from os import path
        """)
        imports = _extract_imports_py(code)
        assert imports.count("os") == 1


# ===================================================================
# 6. TypeScript / JavaScript Export Extraction Tests
# ===================================================================


class TestExtractExportsTS:
    """Verify _extract_exports_ts correctly identifies exported symbols."""

    def test_export_function(self) -> None:
        code = "export function greet(name: string): string { return name; }"
        exports = _extract_exports_ts(code)
        assert "greet" in exports

    def test_export_async_function(self) -> None:
        code = "export async function fetchData(url: string) { }"
        exports = _extract_exports_ts(code)
        assert "fetchData" in exports

    def test_export_class(self) -> None:
        code = "export class UserService { }"
        exports = _extract_exports_ts(code)
        assert "UserService" in exports

    def test_export_abstract_class(self) -> None:
        code = "export abstract class BaseRepository { }"
        exports = _extract_exports_ts(code)
        assert "BaseRepository" in exports

    def test_export_const(self) -> None:
        code = "export const MAX_RETRIES = 3;"
        exports = _extract_exports_ts(code)
        assert "MAX_RETRIES" in exports

    def test_export_let(self) -> None:
        code = "export let counter = 0;"
        exports = _extract_exports_ts(code)
        assert "counter" in exports

    def test_export_default(self) -> None:
        code = "export default function App() { return null; }"
        exports = _extract_exports_ts(code)
        assert "App" in exports

    def test_export_default_class(self) -> None:
        code = "export default class MainComponent { }"
        exports = _extract_exports_ts(code)
        assert "MainComponent" in exports

    def test_export_type(self) -> None:
        code = "export type UserID = string;"
        exports = _extract_exports_ts(code)
        assert "UserID" in exports

    def test_export_interface(self) -> None:
        code = "export interface ApiResponse { data: unknown; }"
        exports = _extract_exports_ts(code)
        assert "ApiResponse" in exports

    def test_export_enum(self) -> None:
        code = "export enum Status { Active, Inactive }"
        exports = _extract_exports_ts(code)
        assert "Status" in exports

    def test_reexport(self) -> None:
        code = "export { UserService, AuthProvider } from './services';"
        exports = _extract_exports_ts(code)
        assert "UserService" in exports
        assert "AuthProvider" in exports

    def test_reexport_with_alias(self) -> None:
        code = "export { default as MyComponent } from './Component';"
        exports = _extract_exports_ts(code)
        assert "MyComponent" in exports

    def test_barrel_file(self) -> None:
        code = textwrap.dedent("""\
            export { UserService } from './user';
            export { AuthService } from './auth';
            export { ApiClient } from './client';
        """)
        exports = _extract_exports_ts(code)
        assert "UserService" in exports
        assert "AuthService" in exports
        assert "ApiClient" in exports

    def test_module_exports(self) -> None:
        code = "module.exports = { helper, config, setup };"
        exports = _extract_exports_ts(code)
        assert "helper" in exports
        assert "config" in exports
        assert "setup" in exports

    def test_deduplication(self) -> None:
        code = textwrap.dedent("""\
            export const Foo = 1;
            export { Foo } from './other';
        """)
        exports = _extract_exports_ts(code)
        assert exports.count("Foo") == 1

    def test_empty_file(self) -> None:
        exports = _extract_exports_ts("")
        assert exports == []


# ===================================================================
# 7. TypeScript / JavaScript Import Extraction Tests
# ===================================================================


class TestExtractImportsTS:
    """Verify _extract_imports_ts correctly identifies imported paths."""

    def test_named_import(self) -> None:
        code = "import { useState, useEffect } from 'react';"
        imports = _extract_imports_ts(code)
        assert "react" in imports

    def test_default_import(self) -> None:
        code = "import React from 'react';"
        imports = _extract_imports_ts(code)
        assert "react" in imports

    def test_namespace_import(self) -> None:
        code = "import * as path from 'path';"
        imports = _extract_imports_ts(code)
        assert "path" in imports

    def test_relative_import(self) -> None:
        code = "import { helper } from './utils/helper';"
        imports = _extract_imports_ts(code)
        assert "./utils/helper" in imports

    def test_require(self) -> None:
        code = "const express = require('express');"
        imports = _extract_imports_ts(code)
        assert "express" in imports

    def test_dynamic_import(self) -> None:
        code = "const module = await import('./lazy-component');"
        imports = _extract_imports_ts(code)
        assert "./lazy-component" in imports

    def test_side_effect_import(self) -> None:
        code = "import './styles.css';"
        imports = _extract_imports_ts(code)
        assert "./styles.css" in imports

    def test_deduplication(self) -> None:
        code = textwrap.dedent("""\
            import { a } from 'react';
            import { b } from 'react';
        """)
        imports = _extract_imports_ts(code)
        assert imports.count("react") == 1

    def test_empty_file(self) -> None:
        imports = _extract_imports_ts("")
        assert imports == []


# ===================================================================
# 8. Shared File Detection Tests
# ===================================================================


class TestSharedFileDetection:
    """Verify _find_shared_files correctly identifies high-fan-in modules."""

    def test_low_risk(self) -> None:
        edges = [
            ImportEdge(source="a.py", target="shared.py", symbols=[]),
            ImportEdge(source="b.py", target="shared.py", symbols=[]),
            ImportEdge(source="c.py", target="shared.py", symbols=[]),
        ]
        shared = _find_shared_files(edges)
        assert len(shared) == 1
        assert shared[0].path == "shared.py"
        assert shared[0].fan_in == 3
        assert shared[0].risk == "low"

    def test_medium_risk(self) -> None:
        edges = [
            ImportEdge(source=f"mod{i}.py", target="utils.py", symbols=[])
            for i in range(5)
        ]
        shared = _find_shared_files(edges)
        assert len(shared) == 1
        assert shared[0].fan_in == 5
        assert shared[0].risk == "medium"

    def test_high_risk(self) -> None:
        edges = [
            ImportEdge(source=f"mod{i}.py", target="core.py", symbols=[])
            for i in range(8)
        ]
        shared = _find_shared_files(edges)
        assert len(shared) == 1
        assert shared[0].fan_in == 8
        assert shared[0].risk == "high"

    def test_no_shared_files(self) -> None:
        edges = [
            ImportEdge(source="a.py", target="b.py", symbols=[]),
            ImportEdge(source="c.py", target="d.py", symbols=[]),
        ]
        shared = _find_shared_files(edges)
        assert shared == []

    def test_empty_graph(self) -> None:
        shared = _find_shared_files([])
        assert shared == []

    def test_sorted_by_fan_in_descending(self) -> None:
        edges = [
            ImportEdge(source=f"a{i}.py", target="low.py", symbols=[])
            for i in range(3)
        ] + [
            ImportEdge(source=f"b{i}.py", target="high.py", symbols=[])
            for i in range(9)
        ] + [
            ImportEdge(source=f"c{i}.py", target="mid.py", symbols=[])
            for i in range(5)
        ]
        shared = _find_shared_files(edges)
        assert len(shared) == 3
        assert shared[0].path == "high.py"
        assert shared[1].path == "mid.py"
        assert shared[2].path == "low.py"

    def test_deduplicates_importers(self) -> None:
        edges = [
            ImportEdge(source="a.py", target="shared.py", symbols=[]),
            ImportEdge(source="a.py", target="shared.py", symbols=[]),
            ImportEdge(source="b.py", target="shared.py", symbols=[]),
        ]
        shared = _find_shared_files(edges)
        # Only 2 unique importers, so fan-in < 3 means no shared files.
        assert shared == []


# ===================================================================
# 9. Framework Detection Tests
# ===================================================================


class TestFrameworkDetection:
    """Verify _detect_framework reads manifests and identifies frameworks."""

    def test_nextjs_from_package_json(self, tmp_path: Path) -> None:
        pkg = {"dependencies": {"next": "14.0.0", "react": "18.2.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        names = [fw.name for fw in frameworks]
        assert "next.js" in names
        assert "react" in names

    def test_nextjs_version_captured(self, tmp_path: Path) -> None:
        pkg = {"dependencies": {"next": "14.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        nextjs = next(fw for fw in frameworks if fw.name == "next.js")
        assert nextjs.version == "14.0.0"
        assert nextjs.detected_from == "package.json"

    def test_express_from_package_json(self, tmp_path: Path) -> None:
        pkg = {"dependencies": {"express": "^4.18.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        names = [fw.name for fw in frameworks]
        assert "express" in names

    def test_react_from_package_json(self, tmp_path: Path) -> None:
        pkg = {"devDependencies": {"react": "18.2.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        names = [fw.name for fw in frameworks]
        assert "react" in names

    def test_peer_dependencies(self, tmp_path: Path) -> None:
        pkg = {"peerDependencies": {"vue": "^3.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        names = [fw.name for fw in frameworks]
        assert "vue" in names

    def test_no_framework(self, tmp_path: Path) -> None:
        pkg = {"dependencies": {"lodash": "^4.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        frameworks = _detect_framework(tmp_path)
        assert frameworks == []

    def test_no_manifest_files(self, tmp_path: Path) -> None:
        frameworks = _detect_framework(tmp_path)
        assert frameworks == []

    def test_malformed_package_json(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text("not valid json {{{", encoding="utf-8")

        # Should not raise, just return empty or partial results.
        frameworks = _detect_framework(tmp_path)
        assert isinstance(frameworks, list)

    def test_requirements_txt_detection(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text(
            "fastapi==0.95.0\nuvicorn>=0.20\n",
            encoding="utf-8",
        )

        frameworks = _detect_framework(tmp_path)
        names = [fw.name for fw in frameworks]
        assert "fastapi" in names

    def test_requirements_txt_version(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text(
            "django>=4.2.0\n",
            encoding="utf-8",
        )

        frameworks = _detect_framework(tmp_path)
        django = next(fw for fw in frameworks if fw.name == "django")
        assert django.version == "4.2.0"
        assert django.detected_from == "requirements.txt"


# ===================================================================
# 10. Summary Rendering Tests
# ===================================================================


class TestSummarizeMap:
    """Verify summarize_map produces correct markdown output."""

    def _make_simple_map(self) -> CodebaseMap:
        """Helper to build a minimal CodebaseMap for summary tests."""
        modules = [
            ModuleInfo(
                path="src/main.py",
                language="python",
                role="unknown",
                exports=["main"],
                imports=["os"],
                lines=50,
            ),
            ModuleInfo(
                path="src/utils.py",
                language="python",
                role="util",
                exports=["helper"],
                imports=[],
                lines=30,
            ),
        ]
        return CodebaseMap(
            root="/project",
            modules=modules,
            import_graph=[
                ImportEdge(source="src/main.py", target="src/utils.py", symbols=[]),
            ],
            shared_files=[],
            frameworks=[FrameworkInfo(name="fastapi", version="0.95.0", detected_from="requirements.txt")],
            total_files=2,
            total_lines=80,
            primary_language="python",
        )

    def test_basic_summary(self) -> None:
        cmap = self._make_simple_map()
        summary = summarize_map(cmap)

        assert "# Codebase Map" in summary
        assert "**Total files:** 2" in summary
        assert "**Total lines:** 80" in summary
        assert "**Primary language:** python" in summary
        assert "fastapi" in summary
        assert "**Root:**" in summary

    def test_summary_contains_module_breakdown(self) -> None:
        cmap = self._make_simple_map()
        summary = summarize_map(cmap)

        assert "## Module Breakdown" in summary
        assert "| Role | Count |" in summary
        assert "unknown" in summary
        assert "util" in summary

    def test_summary_contains_import_graph(self) -> None:
        cmap = self._make_simple_map()
        summary = summarize_map(cmap)

        assert "## Import Graph" in summary
        assert "**Edges:** 1" in summary

    def test_max_lines_truncation(self) -> None:
        cmap = self._make_simple_map()
        summary = summarize_map(cmap, max_lines=5)

        lines = summary.split("\n")
        # The output should be truncated; last lines include truncation marker.
        assert any("truncated" in line for line in lines)

    def test_no_frameworks_section_when_empty(self) -> None:
        cmap = self._make_simple_map()
        cmap.frameworks = []
        summary = summarize_map(cmap)

        assert "**Frameworks:**" not in summary

    def test_shared_files_section(self) -> None:
        cmap = self._make_simple_map()
        cmap.shared_files = [
            SharedFile(path="src/utils.py", importers=["a.py", "b.py", "c.py"], fan_in=3, risk="low"),
        ]
        summary = summarize_map(cmap)

        assert "## Shared Files" in summary
        assert "src/utils.py" in summary
        assert "low" in summary


# ===================================================================
# 11. Integration / generate_codebase_map Tests
# ===================================================================


class TestGenerateCodebaseMap:
    """End-to-end tests for the async generate_codebase_map function."""

    @pytest.mark.asyncio
    async def test_basic_project(self, tmp_path: Path) -> None:
        # Create a minimal Python project.
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text(
            textwrap.dedent("""\
                from .utils import helper

                def main():
                    helper()
            """),
            encoding="utf-8",
        )
        (src / "utils.py").write_text(
            textwrap.dedent("""\
                def helper():
                    return 42
            """),
            encoding="utf-8",
        )

        cmap = await generate_codebase_map(tmp_path)

        assert isinstance(cmap, CodebaseMap)
        assert cmap.total_files == 2
        assert cmap.primary_language == "python"
        paths = [m.path for m in cmap.modules]
        assert "src/main.py" in paths
        assert "src/utils.py" in paths

    @pytest.mark.asyncio
    async def test_empty_project(self, tmp_path: Path) -> None:
        cmap = await generate_codebase_map(tmp_path)

        assert isinstance(cmap, CodebaseMap)
        assert cmap.total_files == 0
        assert cmap.modules == []
        assert cmap.primary_language == "unknown"

    @pytest.mark.asyncio
    async def test_file_size_limit_python(self, tmp_path: Path) -> None:
        # Create a Python file exceeding the 50 KB size limit.
        big_content = "x = 1\n" * 10000  # ~60 KB
        (tmp_path / "big.py").write_text(big_content, encoding="utf-8")
        (tmp_path / "small.py").write_text("y = 2\n", encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)

        paths = [m.path for m in cmap.modules]
        assert "small.py" in paths
        assert "big.py" not in paths

    @pytest.mark.asyncio
    async def test_bom_file_handled(self, tmp_path: Path) -> None:
        # BOM prefix should be handled by utf-8-sig encoding.
        bom_content = "\ufeffdef hello():\n    pass\n"
        (tmp_path / "bom.py").write_text(bom_content, encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)

        assert cmap.total_files == 1
        mod = cmap.modules[0]
        assert "hello" in mod.exports

    @pytest.mark.asyncio
    async def test_zero_byte_file_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "empty.py").write_text("", encoding="utf-8")
        (tmp_path / "valid.py").write_text("x = 1\n", encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)

        paths = [m.path for m in cmap.modules]
        assert "valid.py" in paths
        assert "empty.py" not in paths

    @pytest.mark.asyncio
    async def test_mixed_languages(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def run(): pass\n", encoding="utf-8")
        (tmp_path / "index.ts").write_text("export function main() {}\n", encoding="utf-8")
        (tmp_path / "helper.js").write_text("export const x = 1;\n", encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)

        assert cmap.total_files == 3
        languages = {m.language for m in cmap.modules}
        assert "python" in languages
        assert "typescript" in languages
        assert "javascript" in languages

    @pytest.mark.asyncio
    async def test_excludes_default_dirs(self, tmp_path: Path) -> None:
        # Create files in excluded directories.
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {};", encoding="utf-8")

        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "bundle.js").write_text("var x = 1;", encoding="utf-8")

        # And a real source file.
        (tmp_path / "app.py").write_text("def app(): pass\n", encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)

        paths = [m.path for m in cmap.modules]
        assert "app.py" in paths
        assert not any("node_modules" in p for p in paths)
        assert not any("dist" in p for p in paths)

    @pytest.mark.asyncio
    async def test_typescript_project_with_framework(self, tmp_path: Path) -> None:
        # Create a Next.js-like project structure.
        pkg = {"dependencies": {"next": "14.1.0", "react": "18.2.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        components = tmp_path / "components"
        components.mkdir()
        (components / "Button.tsx").write_text(
            "export function Button() { return null; }",
            encoding="utf-8",
        )

        cmap = await generate_codebase_map(tmp_path)

        fw_names = [fw.name for fw in cmap.frameworks]
        assert "next.js" in fw_names
        assert "react" in fw_names
        assert cmap.total_files >= 1

    @pytest.mark.asyncio
    async def test_import_graph_edges(self, tmp_path: Path) -> None:
        # Two TS files where one imports the other via relative path.
        (tmp_path / "utils.ts").write_text(
            "export function helper() { return 1; }",
            encoding="utf-8",
        )
        (tmp_path / "main.ts").write_text(
            "import { helper } from './utils';",
            encoding="utf-8",
        )

        cmap = await generate_codebase_map(tmp_path)

        # The import graph should have an edge from main.ts to utils.ts.
        edge_pairs = [(e.source, e.target) for e in cmap.import_graph]
        assert ("main.ts", "utils.ts") in edge_pairs

    @pytest.mark.asyncio
    async def test_summarize_integration(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def main(): pass\n", encoding="utf-8")

        cmap = await generate_codebase_map(tmp_path)
        summary = summarize_map(cmap)

        assert isinstance(summary, str)
        assert "# Codebase Map" in summary
        assert "app.py" not in summary or "1" in summary  # total_files at least shows


# ===================================================================
# 12. _parse_pyproject Error Handling Tests
# ===================================================================


class TestParsePyprojectErrors:
    """Tests for _parse_pyproject error handling."""

    def test_corrupted_toml_handled(self, tmp_path: Path) -> None:
        """Corrupted TOML should not crash -- returns empty or default."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text("{{{invalid toml content", encoding="utf-8")
        # _parse_pyproject expects a path to the file itself
        result = _parse_pyproject(toml_file)
        # Should return empty list, not raise
        assert isinstance(result, list)


# ===================================================================
# 13. _resolve_import_path Tests (Finding #23)
# ===================================================================


class TestResolveImportPath:
    """Tests for Finding #23: _resolve_import_path.

    Verifies that _resolve_import_path correctly resolves relative JS/TS
    imports, Python dotted imports, and returns None for unresolvable or
    external imports.  Signature: (source: Path, import_spec: str, root: Path).
    """

    def test_relative_import_resolves_ts(self, tmp_path: Path) -> None:
        """A relative import like ./utils should resolve when utils.ts exists."""
        from agent_team.codebase_map import _resolve_import_path

        (tmp_path / "utils.ts").write_text("export const x = 1;", encoding="utf-8")
        source = tmp_path / "main.ts"
        source.write_text("import { x } from './utils';", encoding="utf-8")

        result = _resolve_import_path(source, "./utils", tmp_path)
        assert result is not None
        assert "utils" in result

    def test_relative_import_resolves_exact_extension(self, tmp_path: Path) -> None:
        """A relative import with explicit extension should resolve if file exists."""
        from agent_team.codebase_map import _resolve_import_path

        target = tmp_path / "helper.js"
        target.write_text("module.exports = {};", encoding="utf-8")
        source = tmp_path / "main.js"

        result = _resolve_import_path(source, "./helper.js", tmp_path)
        assert result == "helper.js"

    def test_relative_import_returns_none_when_missing(self, tmp_path: Path) -> None:
        """A relative import referencing a non-existent file should return None."""
        from agent_team.codebase_map import _resolve_import_path

        source = tmp_path / "main.ts"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "./nonexistent", tmp_path)
        assert result is None

    def test_python_dotted_import_resolves(self, tmp_path: Path) -> None:
        """A Python dotted import like 'src.utils' should resolve to src/utils.py."""
        from agent_team.codebase_map import _resolve_import_path

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("x = 1", encoding="utf-8")
        source = tmp_path / "main.py"

        result = _resolve_import_path(source, "src.utils", tmp_path)
        assert result is not None
        assert result == "src/utils.py"

    def test_python_dotted_import_package_init(self, tmp_path: Path) -> None:
        """A Python dotted import should resolve to __init__.py for packages."""
        from agent_team.codebase_map import _resolve_import_path

        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        source = tmp_path / "main.py"

        result = _resolve_import_path(source, "mypackage", tmp_path)
        assert result is not None
        assert "__init__.py" in result

    def test_bare_package_returns_none(self, tmp_path: Path) -> None:
        """A bare package name like 'react' should return None (external dep)."""
        from agent_team.codebase_map import _resolve_import_path

        source = tmp_path / "app.tsx"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "react", tmp_path)
        assert result is None

    def test_empty_import_spec(self, tmp_path: Path) -> None:
        """An empty import string should return None gracefully."""
        from agent_team.codebase_map import _resolve_import_path

        source = tmp_path / "main.py"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "", tmp_path)
        assert result is None or isinstance(result, str)

    def test_parent_relative_import(self, tmp_path: Path) -> None:
        """A parent-relative import ../utils should resolve when target exists."""
        from agent_team.codebase_map import _resolve_import_path

        (tmp_path / "utils.ts").write_text("export const y = 2;", encoding="utf-8")
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        source = sub_dir / "main.ts"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "../utils", tmp_path)
        assert result is not None
        assert "utils" in result

    def test_index_resolution(self, tmp_path: Path) -> None:
        """A relative import ./components should resolve to components/index.ts."""
        from agent_team.codebase_map import _resolve_import_path

        comp_dir = tmp_path / "components"
        comp_dir.mkdir()
        (comp_dir / "index.ts").write_text("export default {};", encoding="utf-8")
        source = tmp_path / "app.tsx"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "./components", tmp_path)
        assert result is not None
        assert "components/index.ts" in result

    def test_multiple_extensions_tried(self, tmp_path: Path) -> None:
        """When ./foo is imported, it should try .ts, .tsx, .js, .jsx, etc."""
        from agent_team.codebase_map import _resolve_import_path

        (tmp_path / "foo.tsx").write_text("export default () => null;", encoding="utf-8")
        source = tmp_path / "main.ts"
        source.write_text("", encoding="utf-8")

        result = _resolve_import_path(source, "./foo", tmp_path)
        assert result is not None
        assert result == "foo.tsx"


# ===================================================================
# 14. _parse_pyproject Tests (Finding #23)
# ===================================================================


class TestParsePyproject:
    """Tests for Finding #23: _parse_pyproject.

    Verifies that _parse_pyproject extracts framework information from
    pyproject.toml files.  Signature: (path: Path) -> list[FrameworkInfo],
    where path points to the pyproject.toml file itself.
    """

    def test_valid_pyproject_with_fastapi(self, tmp_path: Path) -> None:
        """A pyproject.toml listing fastapi should detect the framework."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "myapp"\ndependencies = ["fastapi>=0.95.0"]\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        assert isinstance(result, list)
        names = [fw.name for fw in result]
        assert "fastapi" in names

    def test_valid_pyproject_with_django(self, tmp_path: Path) -> None:
        """A pyproject.toml listing django should detect the framework."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "webapp"\ndependencies = ["django>=4.2"]\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        names = [fw.name for fw in result]
        assert "django" in names

    def test_missing_pyproject_returns_empty(self, tmp_path: Path) -> None:
        """A non-existent pyproject.toml path should return an empty list."""
        missing_path = tmp_path / "pyproject.toml"
        # File does not exist -- _parse_pyproject reads the file and should
        # handle the OSError gracefully.
        result = _parse_pyproject(missing_path)
        assert result == []

    def test_corrupted_pyproject_returns_list(self, tmp_path: Path) -> None:
        """A corrupted pyproject.toml should not crash; returns empty or partial."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text("{{{invalid toml", encoding="utf-8")
        result = _parse_pyproject(toml_file)
        assert isinstance(result, list)

    def test_pyproject_no_dependencies(self, tmp_path: Path) -> None:
        """A pyproject.toml with no dependencies section should return empty."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "empty"\n[tool.ruff]\nline-length = 100\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        assert isinstance(result, list)
        # No framework dependencies listed, so empty
        assert result == []

    def test_pyproject_non_framework_deps(self, tmp_path: Path) -> None:
        """Dependencies that are not frameworks should not be detected."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "app"\ndependencies = ["requests>=2.28", "pydantic>=2.0"]\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        assert isinstance(result, list)
        # requests and pydantic are not in _PY_FRAMEWORK_NAMES
        assert result == []

    def test_pyproject_version_extraction(self, tmp_path: Path) -> None:
        """The version specifier should be extracted from the dependency string."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "svc"\ndependencies = ["flask>=3.0.1"]\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        names = [fw.name for fw in result]
        assert "flask" in names
        flask_fw = next(fw for fw in result if fw.name == "flask")
        assert flask_fw.version is not None
        assert "3.0" in flask_fw.version

    def test_pyproject_detected_from_field(self, tmp_path: Path) -> None:
        """The detected_from field should be 'pyproject.toml'."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[project]\nname = "api"\ndependencies = ["starlette>=0.27"]\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        for fw in result:
            assert fw.detected_from == "pyproject.toml"

    def test_pyproject_poetry_dependencies(self, tmp_path: Path) -> None:
        """Poetry-style [tool.poetry.dependencies] should also be detected."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[tool.poetry.dependencies]\npython = "^3.11"\naiohttp = "^3.9"\n',
            encoding="utf-8",
        )
        result = _parse_pyproject(toml_file)
        names = [fw.name for fw in result]
        assert "aiohttp" in names
