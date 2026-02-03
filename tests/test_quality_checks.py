"""Tests for anti-pattern spot checker (Agent 19)."""
from __future__ import annotations

import pytest
from pathlib import Path

from agent_team.quality_checks import (
    Violation,
    run_spot_checks,
    _check_ts_any,
    _check_sql_concat,
    _check_console_log,
    _check_n_plus_1,
    _check_generic_fonts,
    _check_default_tailwind_colors,
)


class TestCheckTsAny:
    def test_detects_any_type(self):
        content = "const x: any = 5;"
        violations = _check_ts_any(content, "test.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "FRONT-007"

    def test_ignores_non_ts(self):
        content = "const x: any = 5;"
        violations = _check_ts_any(content, "test.py", ".py")
        assert len(violations) == 0

    def test_no_false_positive_on_many(self):
        content = "const many = 5;"
        violations = _check_ts_any(content, "test.ts", ".ts")
        assert len(violations) == 0


class TestCheckSqlConcat:
    def test_detects_concat_suffix(self):
        content = 'const q = "SELECT * FROM users WHERE id=" + userId;'
        violations = _check_sql_concat(content, "test.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "BACK-001"

    def test_clean_parameterized_query(self):
        content = 'db.query("SELECT * FROM users WHERE id=$1", [userId]);'
        violations = _check_sql_concat(content, "test.ts", ".ts")
        assert len(violations) == 0


class TestCheckConsoleLog:
    def test_detects_console_log(self):
        content = 'console.log("debug");'
        violations = _check_console_log(content, "src/app.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "FRONT-010"

    def test_allows_in_test_files(self):
        content = 'console.log("debug");'
        violations = _check_console_log(content, "src/app.test.ts", ".ts")
        assert len(violations) == 0


class TestCheckNPlus1:
    def test_detects_for_await(self):
        content = "for (const user of users) await db.find(user.id);"
        violations = _check_n_plus_1(content, "test.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "BACK-002"

    def test_no_false_positive_on_single_await(self):
        content = "const result = await db.findAll();"
        violations = _check_n_plus_1(content, "test.ts", ".ts")
        assert len(violations) == 0


class TestCheckGenericFonts:
    def test_detects_inter_font(self):
        content = "font-family: Inter, sans-serif;"
        violations = _check_generic_fonts(content, "style.css", ".css")
        assert len(violations) >= 1
        assert violations[0].check == "SLOP-003"

    def test_allows_custom_fonts(self):
        content = "font-family: 'Space Grotesk', sans-serif;"
        violations = _check_generic_fonts(content, "style.css", ".css")
        assert len(violations) == 0


class TestCheckDefaultTailwindColors:
    def test_detects_indigo_500(self):
        content = '<div className="bg-indigo-500">'
        violations = _check_default_tailwind_colors(content, "page.tsx", ".tsx")
        assert len(violations) >= 1
        assert violations[0].check == "SLOP-001"

    def test_allows_custom_colors(self):
        content = '<div className="bg-emerald-500">'
        violations = _check_default_tailwind_colors(content, "page.tsx", ".tsx")
        assert len(violations) == 0


class TestRunSpotChecks:
    def test_empty_project(self, tmp_path):
        violations = run_spot_checks(tmp_path)
        assert violations == []

    def test_finds_violations(self, tmp_path):
        ts_file = tmp_path / "app.ts"
        ts_file.write_text("const x: any = 5;\nconsole.log(x);\n", encoding="utf-8")
        violations = run_spot_checks(tmp_path)
        checks = {v.check for v in violations}
        assert "FRONT-007" in checks

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        ts_file = nm / "index.ts"
        ts_file.write_text("const x: any = 5;", encoding="utf-8")
        violations = run_spot_checks(tmp_path)
        assert all(v.file_path != "node_modules/pkg/index.ts" for v in violations)

    def test_cap_at_100(self, tmp_path):
        # Create many files with violations
        for i in range(120):
            f = tmp_path / f"file_{i}.ts"
            f.write_text("const x: any = 5;\nconst y: any = 6;\n", encoding="utf-8")
        violations = run_spot_checks(tmp_path)
        assert len(violations) <= 100

    def test_sorted_by_severity(self, tmp_path):
        ts_file = tmp_path / "app.ts"
        ts_file.write_text(
            'const q = "SELECT * FROM users WHERE id=" + userId;\n'
            'const x: any = 5;\n'
            'console.log("hi");\n',
            encoding="utf-8",
        )
        violations = run_spot_checks(tmp_path)
        if len(violations) >= 2:
            severities = [v.severity for v in violations]
            severity_order = {"error": 0, "warning": 1, "info": 2}
            assert all(
                severity_order.get(severities[i], 99) <= severity_order.get(severities[i + 1], 99)
                for i in range(len(severities) - 1)
            )
