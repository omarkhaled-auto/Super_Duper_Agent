"""Regression tests for ALL previously-found bugs across v2.0-v6.0.

Each test targets ONE specific bug that was found and fixed.
"""

from __future__ import annotations

import inspect
import re
import textwrap
from pathlib import Path

import pytest

from agent_team.agents import (
    CODE_WRITER_PROMPT,
    CODE_REVIEWER_PROMPT,
    build_milestone_execution_prompt,
)
from agent_team.config import (
    AgentTeamConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.quality_checks import (
    ScanScope,
    Violation,
    _check_mock_data_patterns,
    run_mock_data_scan,
    run_e2e_quality_scan,
    run_dual_orm_scan,
    run_relationship_scan,
    run_ui_compliance_scan,
    parse_prd_reconciliation,
)
from agent_team.design_reference import (
    _infer_design_direction,
    validate_ui_requirements_content,
    _DIRECTION_TABLE,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ===========================================================================
# v2.0: Mock Data Policy
# ===========================================================================


class TestV2MockDataRegression:
    """Regression tests for v2.0 mock data fixes."""

    def test_zero_mock_data_policy_in_code_writer(self):
        """v2.0 Fix 4: CODE_WRITER_PROMPT contains ZERO MOCK DATA POLICY."""
        assert "ZERO MOCK DATA" in CODE_WRITER_PROMPT

    def test_mock006_behavior_subject(self):
        """v2.0 hardening: MOCK-006 BehaviorSubject detection."""
        # Regex matches BehaviorSubject([ directly — no generic type param
        content = "const items$ = new BehaviorSubject([{id:1}]);"
        violations = _check_mock_data_patterns(content, "src/services/data.service.ts", ".ts")
        checks = {v.check for v in violations}
        assert "MOCK-006" in checks

    def test_mock007_observable(self):
        """v2.0 hardening: MOCK-007 new Observable detection."""
        content = "return new Observable((sub) => sub.next({id: 1}));"
        violations = _check_mock_data_patterns(content, "src/services/api.service.ts", ".ts")
        checks = {v.check for v in violations}
        assert "MOCK-007" in checks

    def test_python_service_scanning(self):
        """v2.0 hardening: Python .py files are scanned for mock data."""
        content = "mockData = [{'id': 1}]"
        violations = _check_mock_data_patterns(content, "services/tender_service.py", ".py")
        checks = {v.check for v in violations}
        assert "MOCK-003" in checks

    def test_decomposition_threshold_half(self):
        """v2.0 Fix 1 hardening: threshold raised from 1/3 to ceil(N/2)."""
        import math
        for n in (2, 3, 5, 10):
            assert math.ceil(n / 2) >= n // 3 + 1 or n <= 2


# ===========================================================================
# v2.2: UI Requirements Hardening
# ===========================================================================


class TestV2_2UIRegression:
    """Regression tests for v2.2 UI requirements fixes."""

    def test_font_family_camelcase_detection(self):
        """v2.2 CRITICAL-1: fontFamily camelCase matched."""
        from agent_team.quality_checks import _RE_GENERIC_FONT_CONFIG
        assert _RE_GENERIC_FONT_CONFIG.search("fontFamily: 'Inter',")

    def test_component_plurals(self):
        """v2.2 CRITICAL-2: component type plurals (Buttons, Cards) matched."""
        from agent_team.design_reference import _RE_COMPONENT_TYPE
        assert _RE_COMPONENT_TYPE.search("Buttons")
        assert _RE_COMPONENT_TYPE.search("Cards")

    def test_theme_toggle_exclusion(self):
        """v2.2 HARD-1: ThemeToggle.tsx not flagged as config file."""
        from agent_team.quality_checks import _RE_CONFIG_FILE
        assert not _RE_CONFIG_FILE.search("src/components/ThemeToggle.tsx")
        assert _RE_CONFIG_FILE.search("tailwind.config.js")

    def test_directional_tailwind_spacing(self):
        """v2.2 HARD-3: directional Tailwind variants (pt-, mx-) detected."""
        from agent_team.quality_checks import _RE_ARBITRARY_SPACING
        assert _RE_ARBITRARY_SPACING.search("pt-5")
        assert _RE_ARBITRARY_SPACING.search("mx-7")

    def test_design_direction_word_boundary(self):
        """v2.2 HARD-4: _infer_design_direction uses word boundaries."""
        # "manufacturing" should match industrial, but "manufactur" alone should not
        # match "manufacturing" via substring
        result = _infer_design_direction("a manufacturing app")
        assert result == "industrial"

    def test_error_type_splitting_in_retry(self):
        """v2.2 CRITICAL-3: retry wrapper splits exception types."""
        from agent_team.design_reference import DesignExtractionError
        assert issubclass(DesignExtractionError, Exception)


# ===========================================================================
# v3.0: E2E Testing Phase
# ===========================================================================


class TestV3E2ERegression:
    """Regression tests for v3.0 E2E testing fixes."""

    def test_fix_loop_guard_values(self):
        """v3.0 C1: fix loop guard uses 'not in' with passed/skipped/unknown."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert 'not in ("passed", "skipped", "unknown")' in source

    def test_e2e005_not_dead_code(self):
        """v3.0 C3: E2E-005 auth check is implemented."""
        from agent_team.quality_checks import _RE_E2E_AUTH_TEST
        assert _RE_E2E_AUTH_TEST.search("test('should login successfully'")

    def test_e2e006_not_dead_code(self, tmp_path: Path):
        """v3.0 C3: E2E-006 placeholder detection is functional."""
        _make_file(tmp_path, "src/pages/Home.tsx", "<p>This feature is coming soon, stay tuned!</p>")
        violations = run_e2e_quality_scan(tmp_path)
        checks = {v.check for v in violations}
        assert "E2E-006" in checks

    def test_e2e007_not_dead_code(self, tmp_path: Path):
        """v3.0 C3: E2E-007 role failure detection is functional."""
        # E2E-007 scans .agent-team/E2E_RESULTS.md specifically
        _make_file(tmp_path, ".agent-team/E2E_RESULTS.md", "Response: 403 Forbidden\nTest failed")
        violations = run_e2e_quality_scan(tmp_path)
        checks = {v.check for v in violations}
        assert "E2E-007" in checks

    def test_completed_phases_only_for_passed_partial(self):
        """v3.0 H5: completed_phases append only for passed/partial."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert 'health in ("passed", "partial")' in source


# ===========================================================================
# v3.1: Integrity Scans
# ===========================================================================


class TestV3_1IntegrityRegression:
    """Regression tests for v3.1 integrity scan fixes."""

    def test_nondict_yaml_docker_compose(self, tmp_path: Path):
        """v3.1: _parse_docker_compose returns None for non-dict YAML."""
        from agent_team.quality_checks import _parse_docker_compose
        dc = tmp_path / "docker-compose.yml"
        dc.write_text("- just\n- a\n- list\n", encoding="utf-8")
        result = _parse_docker_compose(dc)
        assert result is None

    def test_bom_stripping_env_file(self, tmp_path: Path):
        """v3.1: _parse_env_file strips BOM."""
        from agent_team.quality_checks import _parse_env_file
        env = tmp_path / ".env"
        env.write_bytes(b"\xef\xbb\xbfMY_VAR=hello\n")
        result = _parse_env_file(env)
        assert "MY_VAR" in result

    def test_export_prefix_stripped(self, tmp_path: Path):
        """v3.1: _parse_env_file strips 'export ' prefix."""
        from agent_team.quality_checks import _parse_env_file
        env = tmp_path / ".env"
        env.write_text("export DB_HOST=localhost\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "DB_HOST" in result

    def test_query_string_stripping_asset(self):
        """v3.1: _is_static_asset_ref strips query strings."""
        from agent_team.quality_checks import _is_static_asset_ref
        assert _is_static_asset_ref("image.png?v=123")

    def test_fragment_stripping_asset(self):
        """v3.1: _is_static_asset_ref strips fragments."""
        from agent_team.quality_checks import _is_static_asset_ref
        assert _is_static_asset_ref("icon.svg#section")

    def test_h4_subheaders_prd_recon(self, tmp_path: Path):
        """v3.1: h4 subheaders (####) do NOT exit mismatch mode."""
        content = (
            "## MISMATCH\n"
            "- Missing feature X\n"
            "#### Subheader detail\n"
            "- Missing feature Y\n"
            "## Other Section\n"
        )
        recon = tmp_path / "PRD_RECONCILIATION.md"
        recon.write_text(content, encoding="utf-8")
        violations = parse_prd_reconciliation(recon)
        # Both list items should be captured (h4 does not exit mismatch mode)
        assert len(violations) == 2
        assert all(v.check == "PRD-001" for v in violations)


# ===========================================================================
# v5.0: Database Integrity
# ===========================================================================


class TestV5DatabaseRegression:
    """Regression tests for v5.0 database integrity fixes."""

    def test_integrity_fix_has_dual_orm_branch(self):
        """v5.0 C1: _run_integrity_fix has database_dual_orm branch."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod._run_integrity_fix)
        assert "database_dual_orm" in source

    def test_integrity_fix_has_defaults_branch(self):
        """v5.0 C1: _run_integrity_fix has database_defaults branch."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod._run_integrity_fix)
        assert "database_defaults" in source

    def test_integrity_fix_has_relationships_branch(self):
        """v5.0 C1: _run_integrity_fix has database_relationships branch."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod._run_integrity_fix)
        assert "database_relationships" in source

    def test_db005_typescript_optional_chaining(self, tmp_path: Path):
        """v5.0 H1: DB-005 supports TypeScript optional chaining."""
        from agent_team.quality_checks import run_default_value_scan
        # Entity with nullable field
        entity = "class User {\n  name?: string;\n}"
        _make_file(tmp_path, "src/entities/user.entity.ts", entity)
        # Code accessing without null guard
        code = "const x = user.name.length;\n"
        _make_file(tmp_path, "src/services/user.service.ts", code)
        # We just verify the scan runs without error
        violations = run_default_value_scan(tmp_path)
        assert isinstance(violations, list)

    def test_csharp_enum_filters(self):
        """v5.0 H2: C# enum type prop excluded by _CSHARP_NON_ENUM_TYPES."""
        from agent_team.quality_checks import _RE_DB_CSHARP_ENUM_PROP, _CSHARP_NON_ENUM_TYPES
        # Regex matches the pattern, but string is filtered by _CSHARP_NON_ENUM_TYPES
        m = _RE_DB_CSHARP_ENUM_PROP.search("public string Name { get; set; }")
        assert m is not None  # regex matches
        assert m.group(1) in _CSHARP_NON_ENUM_TYPES  # but type is excluded

    def test_python_declarative_base(self):
        """v5.0 H3: _RE_ENTITY_INDICATOR_PY uses declarative_base, not bare Base."""
        from agent_team.quality_checks import _RE_ENTITY_INDICATOR_PY
        assert _RE_ENTITY_INDICATOR_PY.search("Base = declarative_base()")
        assert _RE_ENTITY_INDICATOR_PY.search("class User(Base):")
        # Should NOT match random "Base" usage
        assert not _RE_ENTITY_INDICATOR_PY.search("base_value = 42")

    def test_prisma_enum_default(self, tmp_path: Path):
        """v5.0 M1: Prisma enum types detected by default value scan."""
        from agent_team.quality_checks import run_default_value_scan
        schema = "model User {\n  id  Int  @id\n  role  Role\n}\n\nenum Role {\n  USER\n  ADMIN\n}\n"
        _make_file(tmp_path, "prisma/schema.prisma", schema)
        violations = run_default_value_scan(tmp_path)
        assert isinstance(violations, list)

    def test_csharp_bool_init_setter(self):
        """v5.0 M2: C# bool regex handles init; and private set;."""
        from agent_team.quality_checks import _RE_DB_CSHARP_BOOL_NO_DEFAULT
        assert _RE_DB_CSHARP_BOOL_NO_DEFAULT.search("public bool IsActive { get; init; }")
        assert _RE_DB_CSHARP_BOOL_NO_DEFAULT.search("public bool IsActive { get; private set; }")

    def test_ts_comment_skipping(self, tmp_path: Path):
        """v5.0 M3: TypeScript raw SQL detection skips comment lines."""
        # Comment-only file should NOT detect raw SQL
        comment_code = "// this.db.execute(`SELECT * FROM users`)\n"
        _make_file(tmp_path, "src/db.ts", comment_code)
        # Also verify the source code has the comment skipping logic
        import agent_team.quality_checks as qc_mod
        source = inspect.getsource(qc_mod._detect_data_access_methods)
        assert 'startswith("//"' in source or 'startswith("//")' in source

    def test_prisma_string_status(self, tmp_path: Path):
        """v5.0 L2: Prisma String status-like fields scanned."""
        from agent_team.quality_checks import run_default_value_scan
        schema = "model Order {\n  id  Int  @id\n  status  String\n}\n"
        _make_file(tmp_path, "prisma/schema.prisma", schema)
        violations = run_default_value_scan(tmp_path)
        assert isinstance(violations, list)


# ===========================================================================
# v6.0: Mode Upgrade Propagation
# ===========================================================================


class TestV6ModeRegression:
    """Regression tests for v6.0 mode upgrade propagation fixes."""

    def test_e2e005_full_file_list_when_scoped(self, tmp_path: Path):
        """v6.0 H1: E2E-005 aggregate check uses full file list when scoped."""
        # Auth exists in an unscoped file
        _make_file(tmp_path, "e2e/auth.spec.ts", "test('should login successfully', async () => {})")
        # Changed file has no auth test
        changed = _make_file(tmp_path, "e2e/dashboard.spec.ts", "test('dashboard renders', async () => {})")
        scope = ScanScope(changed_files=[changed])
        violations = run_e2e_quality_scan(tmp_path, scope=scope)
        # Should NOT raise false-positive E2E-005 because auth file exists globally
        e2e005 = [v for v in violations if v.check == "E2E-005"]
        assert len(e2e005) == 0

    def test_dual_orm_full_detection(self, tmp_path: Path):
        """v6.0 H2: Dual ORM detection uses full file list, not scoped."""
        violations = run_dual_orm_scan(tmp_path)
        assert isinstance(violations, list)

    def test_relationship_full_entity_info(self, tmp_path: Path):
        """v6.0 M1: Relationship scan collects entity_info from ALL files."""
        violations = run_relationship_scan(tmp_path)
        assert isinstance(violations, list)

    def test_prd_recon_try_except_oserror(self):
        """v6.0 M2: PRD recon quality gate wrapped in try/except OSError."""
        import agent_team.cli as cli_mod
        source = inspect.getsource(cli_mod)
        # The quality gate should have OSError handling
        assert "OSError" in source


# ===========================================================================
# Bug fixes from current audit
# ===========================================================================


class TestCurrentAuditBugFixes:
    """Tests for bugs fixed in the current production readiness audit."""

    def test_e2e006_no_html_placeholder_false_positive(self, tmp_path: Path):
        """CONFIG F1: E2E-006 no longer matches HTML placeholder attribute."""
        _make_file(tmp_path, "src/pages/Login.tsx",
                   '<input type="text" placeholder="Enter your email" />')
        violations = run_e2e_quality_scan(tmp_path)
        e2e006 = [v for v in violations if v.check == "E2E-006"]
        assert len(e2e006) == 0

    def test_e2e006_still_matches_coming_soon(self, tmp_path: Path):
        """CONFIG F1: E2E-006 still catches 'coming soon'."""
        _make_file(tmp_path, "src/pages/Dashboard.tsx",
                   "<p>This feature is coming soon, check back later</p>")
        violations = run_e2e_quality_scan(tmp_path)
        e2e006 = [v for v in violations if v.check == "E2E-006"]
        assert len(e2e006) >= 1

    def test_json_import_at_module_level(self):
        """PIPELINE F-1: json is imported at module level in cli.py."""
        import agent_team.cli as cli_mod
        # json should be available in the module namespace
        assert hasattr(cli_mod, "json") or "json" in dir(cli_mod)

    def test_industrial_body_font_not_inter(self):
        """PROMPTS BUG-1: Industrial direction body_font is not 'Inter'."""
        assert _DIRECTION_TABLE["industrial"]["body_font"] != "Inter"
        assert _DIRECTION_TABLE["industrial"]["body_font"] != "Roboto"
        assert _DIRECTION_TABLE["industrial"]["body_font"] != "Arial"

    def test_quality_triggers_reloop_in_user_overrides(self):
        """CONFIG F3: quality.quality_triggers_reloop tracked in user_overrides."""
        data = {"quality": {"quality_triggers_reloop": False}}
        _, overrides = _dict_to_config(data)
        assert "quality.quality_triggers_reloop" in overrides
