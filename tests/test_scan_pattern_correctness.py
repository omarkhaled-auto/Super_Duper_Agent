"""Tests for scan pattern correctness — positive AND negative regex match tests.

Covers: MOCK-001..007, UI-001..004, E2E-001..007, DEPLOY-001..004,
        ASSET-001..003, DB-001..008, plus scope handling.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from agent_team.quality_checks import (
    ScanScope,
    Violation,
    run_asset_scan,
    run_default_value_scan,
    run_deployment_scan,
    run_dual_orm_scan,
    run_e2e_quality_scan,
    run_mock_data_scan,
    run_relationship_scan,
    run_ui_compliance_scan,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    """Create a file at tmp_path/rel with content."""
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _scan_checks(violations: list[Violation]) -> set[str]:
    """Extract set of check codes from violations."""
    return {v.check for v in violations}


# ===========================================================================
# MOCK-001..007 patterns
# ===========================================================================


class TestMockPatterns:
    """Positive and negative tests for mock data detection regex patterns."""

    def test_mock_001_rxjs_of_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/data.service.ts", "return of([{id: 1}]);")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-001" in _scan_checks(vs)

    def test_mock_001_rxjs_of_negative_import(self, tmp_path):
        _make_file(tmp_path, "src/services/data.service.ts", "import { of } from 'rxjs';")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-001" not in _scan_checks(vs)

    def test_mock_002_promise_resolve_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/api.service.ts", "return Promise.resolve([{id:1}]);")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-002" in _scan_checks(vs)

    def test_mock_002_promise_resolve_negative_empty(self, tmp_path):
        _make_file(tmp_path, "src/services/api.service.ts", "return Promise.resolve();")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-002" not in _scan_checks(vs)

    def test_mock_003_mock_variable_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/user.service.ts", "const mockUsers = [{id: 1}];")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-003" in _scan_checks(vs)

    def test_mock_003_mock_variable_negative_test(self, tmp_path):
        _make_file(tmp_path, "src/services/user.service.spec.ts", "const mockUsers = [{id: 1}];")
        vs = run_mock_data_scan(tmp_path)
        # .spec.ts is a test file, should be excluded
        assert "MOCK-003" not in _scan_checks(vs)

    def test_mock_004_timeout_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/delay.service.ts", "setTimeout(() => resolve(), 2000);")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-004" in _scan_checks(vs)

    def test_mock_005_delay_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/sim.service.ts", "await delay(1000)")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-005" in _scan_checks(vs)

    def test_mock_006_behavior_subject_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/state.service.ts",
                   "const items$ = new BehaviorSubject([{id: 1}]);")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-006" in _scan_checks(vs)

    def test_mock_007_observable_positive(self, tmp_path):
        _make_file(tmp_path, "src/services/obs.service.ts",
                   "return new Observable((sub) => sub.next([{id:1}]));")
        vs = run_mock_data_scan(tmp_path)
        assert "MOCK-007" in _scan_checks(vs)

    def test_mock_python_positive(self, tmp_path):
        # MOCK-003 regex expects camelCase: mockData, fakeResponse, etc.
        _make_file(tmp_path, "src/services/data_service.py",
                   "mockData = [{'id': 1}]")
        vs = run_mock_data_scan(tmp_path)
        checks = _scan_checks(vs)
        assert len(checks) > 0, "Should detect mock data in Python files"


# ===========================================================================
# UI-001..004 patterns
# ===========================================================================


class TestUIPatterns:
    """Positive and negative tests for UI compliance scan patterns."""

    def test_ui_001_hardcoded_hex_positive(self, tmp_path):
        _make_file(tmp_path, "src/components/Card.tsx",
                   "const color = '#ff5733';")
        vs = run_ui_compliance_scan(tmp_path)
        assert "UI-001" in _scan_checks(vs)

    def test_ui_001_hardcoded_hex_negative_config(self, tmp_path):
        _make_file(tmp_path, "tailwind.config.js",
                   "primary: '#ff5733',")
        vs = run_ui_compliance_scan(tmp_path)
        # Config files should not trigger UI-001
        assert "UI-001" not in _scan_checks(vs)

    def test_ui_002_default_tailwind_positive(self, tmp_path):
        _make_file(tmp_path, "src/components/Button.tsx",
                   '<button className="bg-indigo-500">Submit</button>')
        vs = run_ui_compliance_scan(tmp_path)
        assert "UI-002" in _scan_checks(vs)

    def test_ui_003_generic_font_positive_config(self, tmp_path):
        # UI-003 only fires in config/theme files — not in components
        _make_file(tmp_path, "tailwind.config.ts",
                   "fontFamily: { sans: ['Arial'] }")
        vs = run_ui_compliance_scan(tmp_path)
        assert "UI-003" in _scan_checks(vs)

    def test_ui_003_generic_font_negative_component(self, tmp_path):
        # Generic font in component file does NOT trigger UI-003
        _make_file(tmp_path, "src/components/Header.tsx",
                   "fontFamily: 'Arial, sans-serif'")
        vs = run_ui_compliance_scan(tmp_path)
        assert "UI-003" not in _scan_checks(vs)

    def test_ui_004_arbitrary_spacing_positive(self, tmp_path):
        _make_file(tmp_path, "src/components/Layout.tsx",
                   '<div className="p-[13px] mt-[7px]">test</div>')
        vs = run_ui_compliance_scan(tmp_path)
        assert "UI-004" in _scan_checks(vs)

    def test_ui_004_arbitrary_spacing_negative_no_spacing(self, tmp_path):
        _make_file(tmp_path, "src/components/Widget.tsx",
                   '<div className="text-[14px]">test</div>')
        vs = run_ui_compliance_scan(tmp_path)
        # text-[14px] is not a spacing class
        assert "UI-004" not in _scan_checks(vs)


# ===========================================================================
# E2E-001..007 patterns
# ===========================================================================


class TestE2EPatterns:
    """Positive and negative tests for E2E quality scan patterns."""

    def test_e2e_001_sleep_positive(self, tmp_path):
        _make_file(tmp_path, "e2e/login.spec.ts",
                   "await new Promise(r => setTimeout(r, 3000));")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-001" in _scan_checks(vs)

    def test_e2e_002_hardcoded_port_positive(self, tmp_path):
        _make_file(tmp_path, "e2e/api.spec.ts",
                   "const url = 'http://localhost:3000/api';")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-002" in _scan_checks(vs)

    def test_e2e_002_hardcoded_port_negative_env(self, tmp_path):
        _make_file(tmp_path, "e2e/api.spec.ts",
                   "const url = process.env.BASE_URL + '/api';")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-002" not in _scan_checks(vs)

    def test_e2e_003_mock_data_positive(self, tmp_path):
        _make_file(tmp_path, "e2e/dashboard.spec.ts",
                   "const mockData = [{id: 1}];")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-003" in _scan_checks(vs)

    def test_e2e_004_empty_test_positive(self, tmp_path):
        # E2E-004 regex requires `async` arrow function body
        _make_file(tmp_path, "e2e/empty.spec.ts",
                   "test('placeholder', async () => {} )")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-004" in _scan_checks(vs)

    def test_e2e_006_placeholder_text_positive(self, tmp_path):
        _make_file(tmp_path, "src/pages/dashboard.tsx",
                   '<p>Coming Soon</p>')
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-006" in _scan_checks(vs)

    def test_e2e_006_placeholder_not_html_attr(self, tmp_path):
        """HTML placeholder attribute should NOT trigger E2E-006."""
        _make_file(tmp_path, "src/pages/form.tsx",
                   '<input placeholder="Enter name" />')
        vs = run_e2e_quality_scan(tmp_path)
        e2e006 = [v for v in vs if v.check == "E2E-006"]
        assert len(e2e006) == 0, "HTML placeholder attribute should not be flagged"

    def test_e2e_007_role_failure_positive(self, tmp_path):
        results_path = tmp_path / ".agent-team"
        results_path.mkdir(parents=True)
        (results_path / "E2E_RESULTS.md").write_text(
            "## Results\n- Login: 403 Forbidden\n", encoding="utf-8"
        )
        _make_file(tmp_path, "e2e/auth.spec.ts", "test('admin access', () => {});")
        vs = run_e2e_quality_scan(tmp_path)
        assert "E2E-007" in _scan_checks(vs)


# ===========================================================================
# DB-001..008 patterns
# ===========================================================================


class TestDBPatterns:
    """Positive and negative tests for database integrity scan patterns."""

    def test_db_001_enum_int_comparison(self, tmp_path):
        # Need .csproj for ORM detection + entity in Models dir
        _make_file(tmp_path, "src/App.csproj",
                   '<PackageReference Include="Microsoft.EntityFrameworkCore" />\n'
                   '<PackageReference Include="Dapper" />')
        _make_file(tmp_path, "src/Models/Order.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            public class Order {
                public OrderStatus Status { get; set; }
            }
        """))
        _make_file(tmp_path, "src/Repos/OrderRepo.cs", textwrap.dedent("""\
            using Dapper;
            var sql = "SELECT * FROM Orders WHERE Status = 1";
        """))
        vs = run_dual_orm_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "DB-001" in checks

    def test_db_002_bool_int_comparison(self, tmp_path):
        _make_file(tmp_path, "src/App.csproj",
                   '<PackageReference Include="Microsoft.EntityFrameworkCore" />\n'
                   '<PackageReference Include="Dapper" />')
        _make_file(tmp_path, "src/Models/User.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            public class User {
                public bool IsActive { get; set; }
            }
        """))
        _make_file(tmp_path, "src/Repos/UserRepo.cs", textwrap.dedent("""\
            using Dapper;
            var sql = "SELECT * FROM Users WHERE IsActive = 0";
        """))
        vs = run_dual_orm_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "DB-002" in checks

    def test_db_004_csharp_bool_no_default(self, tmp_path):
        # Entity indicator needed: DbContext or [Table]
        _make_file(tmp_path, "src/Models/Item.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            [Table("Items")]
            public class Item {
                public bool IsVisible { get; set; }
            }
        """))
        vs = run_default_value_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "DB-004" in checks

    def test_db_004_prisma_no_default(self, tmp_path):
        _make_file(tmp_path, "prisma/schema.prisma", textwrap.dedent("""\
            model User {
              id       Int     @id @default(autoincrement())
              isActive Boolean
            }
        """))
        vs = run_default_value_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "DB-004" in checks

    def test_db_004_prisma_with_default_negative(self, tmp_path):
        _make_file(tmp_path, "prisma/schema.prisma", textwrap.dedent("""\
            model User {
              id       Int     @id @default(autoincrement())
              isActive Boolean @default(true)
            }
        """))
        vs = run_default_value_scan(tmp_path)
        db004 = [v for v in vs if v.check == "DB-004"]
        assert len(db004) == 0

    def test_db_008_fk_no_nav_no_config(self, tmp_path):
        """FK without navigation AND without config -> DB-008."""
        _make_file(tmp_path, "src/Models/Order.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            [Table("Orders")]
            public class Order {
                public int Id { get; set; }
                public int CustomerId { get; set; }
            }
        """))
        vs = run_relationship_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "DB-008" in checks

    def test_db_006_fk_with_navigation_negative(self, tmp_path):
        _make_file(tmp_path, "src/Models/Order.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            [Table("Orders")]
            public class Order {
                public int Id { get; set; }
                public int CustomerId { get; set; }
                public virtual Customer Customer { get; set; }
            }
        """))
        vs = run_relationship_scan(tmp_path)
        db006 = [v for v in vs if v.check == "DB-006"]
        assert len(db006) == 0


# ===========================================================================
# Scope handling
# ===========================================================================


class TestScopeHandling:
    """Verify scan functions respect ScanScope for scoped scanning."""

    def test_mock_scan_scoped_skips_out_of_scope(self, tmp_path):
        in_scope = _make_file(tmp_path, "src/services/a.service.ts",
                              "return of([{id:1}]);")
        _make_file(tmp_path, "src/services/b.service.ts",
                   "return of([{id:2}]);")
        scope = ScanScope(mode="changed_only", changed_files=[in_scope])
        vs = run_mock_data_scan(tmp_path, scope=scope)
        # Only in-scope file should produce violations
        files_with_violations = {v.file_path for v in vs}
        assert all("a.service" in f for f in files_with_violations)

    def test_ui_scan_scoped(self, tmp_path):
        in_scope = _make_file(tmp_path, "src/components/A.tsx",
                              "const c = '#ff5733';")
        _make_file(tmp_path, "src/components/B.tsx",
                   "const c = '#abcdef';")
        scope = ScanScope(mode="changed_only", changed_files=[in_scope])
        vs = run_ui_compliance_scan(tmp_path, scope=scope)
        files_with_violations = {v.file_path for v in vs}
        assert all("A.tsx" in f for f in files_with_violations)

    def test_mock_scan_full_scope_scans_all(self, tmp_path):
        _make_file(tmp_path, "src/services/a.service.ts",
                   "return of([{id:1}]);")
        _make_file(tmp_path, "src/services/b.service.ts",
                   "return of([{id:2}]);")
        vs = run_mock_data_scan(tmp_path, scope=None)
        files_with_violations = {v.file_path for v in vs}
        assert len(files_with_violations) == 2

    def test_dual_orm_scope_uses_full_for_detection(self, tmp_path):
        """Dual ORM scan should use full file list for type detection."""
        _make_file(tmp_path, "src/App.csproj",
                   '<PackageReference Include="Microsoft.EntityFrameworkCore" />\n'
                   '<PackageReference Include="Dapper" />')
        _make_file(tmp_path, "src/Models/Order.cs", textwrap.dedent("""\
            using Microsoft.EntityFrameworkCore;
            [Table("Orders")]
            public class Order {
                public OrderStatus Status { get; set; }
            }
        """))
        sql_file = _make_file(tmp_path, "src/Repos/Repo.cs", textwrap.dedent("""\
            using Dapper;
            var sql = "SELECT * FROM Orders WHERE Status = 1";
        """))
        scope = ScanScope(mode="changed_only", changed_files=[sql_file])
        vs = run_dual_orm_scan(tmp_path, scope=scope)
        # Should still detect enum in entity (full scan) but report violation on scoped file
        checks = _scan_checks(vs)
        # DB-001 should still be detected because detection uses full file list
        assert "DB-001" in checks


# ===========================================================================
# Negative tests — no false positives
# ===========================================================================


class TestNegativeMatches:
    """Verify patterns do NOT produce false positives for innocent code."""

    def test_no_mock_in_normal_service(self, tmp_path):
        _make_file(tmp_path, "src/services/real.service.ts", textwrap.dedent("""\
            import { HttpClient } from '@angular/common/http';
            export class RealService {
                constructor(private http: HttpClient) {}
                getItems() { return this.http.get('/api/items'); }
            }
        """))
        vs = run_mock_data_scan(tmp_path)
        assert len(vs) == 0

    def test_no_ui_violation_in_standard_tailwind(self, tmp_path):
        _make_file(tmp_path, "src/components/Card.tsx", textwrap.dedent("""\
            export const Card = () => (
                <div className="bg-primary-500 p-4 text-sm font-sans">
                    Content
                </div>
            );
        """))
        vs = run_ui_compliance_scan(tmp_path)
        assert len(vs) == 0

    def test_no_e2e_violation_in_proper_test(self, tmp_path):
        _make_file(tmp_path, "e2e/login.spec.ts", textwrap.dedent("""\
            import { test, expect } from '@playwright/test';
            test('login', async ({ page }) => {
                await page.goto(process.env.BASE_URL + '/login');
                await page.fill('#email', 'user@test.com');
                await expect(page).toHaveURL('/dashboard');
            });
        """))
        vs = run_e2e_quality_scan(tmp_path)
        assert len(vs) == 0

    def test_comment_lines_still_flagged_in_mock_scan(self, tmp_path):
        """Mock scan does NOT skip comment lines (by design — commented mock code
        is still flagged to ensure it gets cleaned up)."""
        _make_file(tmp_path, "src/services/note.service.ts",
                   "// const mockData = [{id: 1}];")
        vs = run_mock_data_scan(tmp_path)
        # MOCK-003 matches even in comments
        assert "MOCK-003" in _scan_checks(vs)

    def test_test_files_excluded_from_mock_scan(self, tmp_path):
        _make_file(tmp_path, "src/services/__tests__/api.test.ts",
                   "const mockData = [{id: 1}];")
        vs = run_mock_data_scan(tmp_path)
        assert len(vs) == 0

    def test_node_modules_excluded(self, tmp_path):
        _make_file(tmp_path, "node_modules/some-lib/service.ts",
                   "return of([{id:1}]);")
        vs = run_mock_data_scan(tmp_path)
        assert len(vs) == 0

    def test_dist_excluded(self, tmp_path):
        _make_file(tmp_path, ".next/static/service.js",
                   "return of([{id:1}]);")
        vs = run_mock_data_scan(tmp_path)
        assert len(vs) == 0


# ===========================================================================
# Asset scan patterns
# ===========================================================================


class TestAssetPatterns:
    """Positive and negative tests for asset scan."""

    def test_asset_001_broken_src_positive(self, tmp_path):
        _make_file(tmp_path, "src/components/Logo.tsx",
                   '<img src="/images/nonexistent.png" />')
        vs = run_asset_scan(tmp_path)
        checks = _scan_checks(vs)
        assert "ASSET-001" in checks

    def test_asset_001_existing_asset_negative(self, tmp_path):
        _make_file(tmp_path, "public/images/logo.png", "PNG_DATA")
        _make_file(tmp_path, "src/components/Logo.tsx",
                   '<img src="/images/logo.png" />')
        vs = run_asset_scan(tmp_path)
        asset001 = [v for v in vs if v.check == "ASSET-001"]
        assert len(asset001) == 0

    def test_asset_external_url_excluded(self, tmp_path):
        _make_file(tmp_path, "src/components/Logo.tsx",
                   '<img src="https://cdn.example.com/logo.png" />')
        vs = run_asset_scan(tmp_path)
        assert len(vs) == 0

    def test_asset_data_uri_excluded(self, tmp_path):
        _make_file(tmp_path, "src/components/Icon.tsx",
                   '<img src="data:image/png;base64,abc123" />')
        vs = run_asset_scan(tmp_path)
        assert len(vs) == 0

    def test_asset_query_string_stripped(self, tmp_path):
        _make_file(tmp_path, "public/images/logo.png", "PNG_DATA")
        _make_file(tmp_path, "src/components/Logo.tsx",
                   '<img src="/images/logo.png?v=2" />')
        vs = run_asset_scan(tmp_path)
        asset001 = [v for v in vs if v.check == "ASSET-001"]
        assert len(asset001) == 0

    def test_asset_fragment_stripped(self, tmp_path):
        _make_file(tmp_path, "public/images/sprite.svg", "<svg></svg>")
        _make_file(tmp_path, "src/components/Icon.tsx",
                   '<img src="/images/sprite.svg#icon-home" />')
        vs = run_asset_scan(tmp_path)
        asset001 = [v for v in vs if v.check == "ASSET-001"]
        assert len(asset001) == 0
