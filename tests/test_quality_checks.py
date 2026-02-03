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
    _check_transaction_safety,
    _check_param_validation,
    _check_validation_data_flow,
    _check_gitignore,
    _check_duplicate_functions,
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
        # Provide .gitignore so the project-level check doesn't fire
        (tmp_path / ".gitignore").write_text("node_modules\ndist\n.env\n", encoding="utf-8")
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


# ===================================================================
# New Spot Checks (Quality Optimization)
# ===================================================================

class TestCheckDuplicateFunctions:
    def test_duplicate_functions_detected(self, tmp_path):
        f1 = tmp_path / "routes.ts"
        f1.write_text("function formatDate(d: Date) { return d.toISOString(); }\n", encoding="utf-8")
        f2 = tmp_path / "utils.ts"
        f2.write_text("function formatDate(d: Date) { return d.toLocaleDateString(); }\n", encoding="utf-8")
        source_files = [f1, f2]
        violations = _check_duplicate_functions(tmp_path, source_files)
        assert len(violations) >= 1
        assert any("FRONT-016" in v.check for v in violations)

    def test_no_duplicate_false_positive(self, tmp_path):
        f1 = tmp_path / "routes.ts"
        f1.write_text("function formatDate(d: Date) { return d.toISOString(); }\n", encoding="utf-8")
        f2 = tmp_path / "utils.ts"
        f2.write_text("function parseInput(s: string) { return s.trim(); }\n", encoding="utf-8")
        source_files = [f1, f2]
        violations = _check_duplicate_functions(tmp_path, source_files)
        assert len(violations) == 0

    def test_const_non_function_not_flagged(self, tmp_path):
        """const config = {...} should NOT be detected as a function."""
        f1 = tmp_path / "a.ts"
        f1.write_text("const config = { port: 3000 };\n", encoding="utf-8")
        f2 = tmp_path / "b.ts"
        f2.write_text("const config = { port: 8080 };\n", encoding="utf-8")
        source_files = [f1, f2]
        violations = _check_duplicate_functions(tmp_path, source_files)
        assert len(violations) == 0

    def test_const_arrow_function_detected(self, tmp_path):
        """const formatDate = () => ... SHOULD be detected as a function."""
        f1 = tmp_path / "a.ts"
        f1.write_text("const formatDate = (d: Date) => d.toISOString();\n", encoding="utf-8")
        f2 = tmp_path / "b.ts"
        f2.write_text("const formatDate = (d: Date) => d.toLocaleDateString();\n", encoding="utf-8")
        source_files = [f1, f2]
        violations = _check_duplicate_functions(tmp_path, source_files)
        assert len(violations) >= 1


class TestCheckTransactionSafety:
    def test_transaction_safety_flagged(self):
        content = (
            "async function replaceItems(userId: string) {\n"
            "  await prisma.item.deleteMany({ where: { userId } });\n"
            "  await prisma.item.createMany({ data: newItems });\n"
            "}\n"
        )
        violations = _check_transaction_safety(content, "items.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "BACK-016"

    def test_transaction_safety_passes(self):
        content = (
            "async function replaceItems(userId: string) {\n"
            "  await prisma.$transaction(async (tx) => {\n"
            "    await tx.item.deleteMany({ where: { userId } });\n"
            "    await tx.item.createMany({ data: newItems });\n"
            "  });\n"
            "}\n"
        )
        violations = _check_transaction_safety(content, "items.ts", ".ts")
        assert len(violations) == 0


class TestCheckParamValidation:
    def test_param_validation_flagged(self):
        content = (
            "app.get('/users/:id', (req, res) => {\n"
            "  const id = Number(req.params.id);\n"
            "  const user = db.getUser(id);\n"
            "  res.json(user);\n"
            "});\n"
        )
        violations = _check_param_validation(content, "routes.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "BACK-018"

    def test_param_validation_passes(self):
        content = (
            "app.get('/users/:id', (req, res) => {\n"
            "  const id = Number(req.params.id);\n"
            "  if (isNaN(id)) return res.status(400).json({ error: 'Invalid ID' });\n"
            "  const user = db.getUser(id);\n"
            "  res.json(user);\n"
            "});\n"
        )
        violations = _check_param_validation(content, "routes.ts", ".ts")
        assert len(violations) == 0


class TestCheckValidationDataFlow:
    def test_validation_flow_flagged(self):
        content = (
            "app.post('/users', (req, res) => {\n"
            "  schema.parse(req.body);\n"
            "  const user = createUser(req.body);\n"
            "  res.json(user);\n"
            "});\n"
        )
        violations = _check_validation_data_flow(content, "routes.ts", ".ts")
        assert len(violations) >= 1
        assert violations[0].check == "BACK-017"

    def test_validation_flow_passes(self):
        content = (
            "app.post('/users', (req, res) => {\n"
            "  const data = schema.parse(req.body);\n"
            "  const user = createUser(data);\n"
            "  res.json(user);\n"
            "});\n"
        )
        violations = _check_validation_data_flow(content, "routes.ts", ".ts")
        assert len(violations) == 0

    def test_validation_flow_return_not_flagged(self):
        """return schema.parse(req.body) should NOT be flagged — result is used."""
        content = (
            "function validate(req: Request) {\n"
            "  return schema.parse(req.body);\n"
            "}\n"
        )
        violations = _check_validation_data_flow(content, "middleware.ts", ".ts")
        assert len(violations) == 0


class TestCheckGitignore:
    def test_gitignore_missing(self, tmp_path):
        violations = _check_gitignore(tmp_path)
        assert len(violations) >= 1

    def test_gitignore_present(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("node_modules\ndist\n.env\n", encoding="utf-8")
        violations = _check_gitignore(tmp_path)
        assert len(violations) == 0
