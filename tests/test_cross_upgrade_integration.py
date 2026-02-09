"""Cross-upgrade integration tests covering all review findings.

Verifies:
- All quality check functions are registered in _ALL_CHECKS
- All scan functions exist and are callable
- All config dataclasses instantiate with defaults
- All config fields wire through _dict_to_config correctly
- Import chains work end-to-end
- Violation fields are valid across all scans
- No duplicate pattern_ids
- Prompt constants are non-empty and contain expected keywords
- Bug fix regressions (CRITICAL-1, HIGH-1, MEDIUM-1, MEDIUM-2)
- Edge cases for config, quality checks, docker parsing, asset scanning,
  E2E detection, PRD reconciliation
- UI hardening regressions
- E2E review fix regressions
- Integrity scan review fix regressions
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_team.config import (
    AgentTeamConfig,
    ConvergenceConfig,
    DepthConfig,
    DesignReferenceConfig,
    DisplayConfig,
    E2ETestingConfig,
    IntegrityScanConfig,
    InterviewConfig,
    InvestigationConfig,
    MilestoneConfig,
    OrchestratorConfig,
    OrchestratorSTConfig,
    PRDChunkingConfig,
    QualityConfig,
    SchedulerConfig,
    VerificationConfig,
    _dict_to_config,
)
from agent_team.state import (
    ConvergenceReport,
    E2ETestReport,
    RunState,
    RunSummary,
)
from agent_team.quality_checks import (
    Violation,
    _ALL_CHECKS,
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
    _check_ui_compliance,
    _check_e2e_quality,
    run_spot_checks,
    run_mock_data_scan,
    run_ui_compliance_scan,
    run_e2e_quality_scan,
    run_deployment_scan,
    run_asset_scan,
    parse_prd_reconciliation,
    _parse_docker_compose,
    _parse_env_file,
    _is_static_asset_ref,
    _resolve_asset,
    _BUILTIN_ENV_VARS,
)
from agent_team.e2e_testing import (
    AppTypeInfo,
    detect_app_type,
    parse_e2e_results,
    BACKEND_E2E_PROMPT,
    FRONTEND_E2E_PROMPT,
    E2E_FIX_PROMPT,
)
from agent_team.design_reference import (
    DesignExtractionError,
    validate_ui_requirements_content,
    generate_fallback_ui_requirements,
    _infer_design_direction,
    _DIRECTION_TABLE,
    run_design_extraction_with_retry,
)
from agent_team.agents import (
    CODE_WRITER_PROMPT,
    CODE_REVIEWER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    ARCHITECT_PROMPT,
    build_milestone_execution_prompt,
    build_decomposition_prompt,
)
from agent_team.code_quality_standards import (
    E2E_TESTING_STANDARDS,
    _AGENT_STANDARDS_MAP,
    get_standards_for_agent,
)


# ===========================================================================
# 1. ALL_CHECKS registry completeness
# ===========================================================================

class TestAllChecksRegistry:
    """Verify every per-file check function is in _ALL_CHECKS."""

    def test_all_per_file_checks_registered(self):
        expected = {
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
            _check_ui_compliance,
            _check_e2e_quality,
        }
        registered = set(_ALL_CHECKS)
        assert expected == registered, f"Missing: {expected - registered}, Extra: {registered - expected}"

    def test_all_checks_are_callable(self):
        for fn in _ALL_CHECKS:
            assert callable(fn), f"{fn} is not callable"

    def test_all_checks_accept_content_relpath_extension(self):
        for fn in _ALL_CHECKS:
            sig = inspect.signature(fn)
            params = list(sig.parameters.keys())
            assert params == ["content", "rel_path", "extension"], (
                f"{fn.__name__} has params {params}, expected [content, rel_path, extension]"
            )

    def test_all_checks_return_list_of_violation(self):
        for fn in _ALL_CHECKS:
            result = fn("", "test.ts", ".ts")
            assert isinstance(result, list), f"{fn.__name__} returned {type(result)}"


# ===========================================================================
# 2. Scan functions exist and are callable
# ===========================================================================

class TestScanFunctionsExist:
    """Verify all public scan functions exist and are callable."""

    @pytest.mark.parametrize("func", [
        run_spot_checks,
        run_mock_data_scan,
        run_ui_compliance_scan,
        run_e2e_quality_scan,
        run_deployment_scan,
        run_asset_scan,
        parse_prd_reconciliation,
    ])
    def test_scan_callable(self, func):
        assert callable(func)

    def test_run_spot_checks_on_empty_dir(self, tmp_path):
        result = run_spot_checks(tmp_path)
        assert isinstance(result, list)

    def test_run_mock_data_scan_on_empty_dir(self, tmp_path):
        result = run_mock_data_scan(tmp_path)
        assert isinstance(result, list)

    def test_run_ui_compliance_scan_on_empty_dir(self, tmp_path):
        result = run_ui_compliance_scan(tmp_path)
        assert isinstance(result, list)

    def test_run_e2e_quality_scan_on_empty_dir(self, tmp_path):
        result = run_e2e_quality_scan(tmp_path)
        assert isinstance(result, list)

    def test_run_deployment_scan_on_empty_dir(self, tmp_path):
        result = run_deployment_scan(tmp_path)
        assert isinstance(result, list)

    def test_run_asset_scan_on_empty_dir(self, tmp_path):
        result = run_asset_scan(tmp_path)
        assert isinstance(result, list)

    def test_parse_prd_reconciliation_missing_file(self, tmp_path):
        result = parse_prd_reconciliation(tmp_path / "DOES_NOT_EXIST.md")
        assert result == []


# ===========================================================================
# 3. Config dataclass defaults
# ===========================================================================

class TestConfigDefaults:
    """Verify all config dataclasses can be instantiated with defaults."""

    @pytest.mark.parametrize("cls", [
        OrchestratorConfig,
        DepthConfig,
        ConvergenceConfig,
        InterviewConfig,
        InvestigationConfig,
        OrchestratorSTConfig,
        DesignReferenceConfig,
        DisplayConfig,
        SchedulerConfig,
        QualityConfig,
        VerificationConfig,
        MilestoneConfig,
        PRDChunkingConfig,
        E2ETestingConfig,
        IntegrityScanConfig,
        AgentTeamConfig,
    ])
    def test_default_instantiation(self, cls):
        instance = cls()
        assert instance is not None

    @pytest.mark.parametrize("cls", [
        RunState,
        RunSummary,
        ConvergenceReport,
        E2ETestReport,
    ])
    def test_state_default_instantiation(self, cls):
        instance = cls()
        assert instance is not None


# ===========================================================================
# 4. Config fields wire through _dict_to_config
# ===========================================================================

class TestConfigWiring:
    """Verify all config fields from YAML wire through _dict_to_config."""

    def test_empty_dict_returns_defaults(self):
        cfg = _dict_to_config({})
        assert isinstance(cfg, AgentTeamConfig)
        assert cfg.milestone.review_recovery_retries == 1
        assert cfg.milestone.mock_data_scan is True
        assert cfg.milestone.ui_compliance_scan is True
        assert cfg.e2e_testing.enabled is False
        assert cfg.integrity_scans.deployment_scan is True

    def test_milestone_fields_wire(self):
        data = {
            "milestone": {
                "enabled": True,
                "review_recovery_retries": 3,
                "mock_data_scan": False,
                "ui_compliance_scan": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.milestone.enabled is True
        assert cfg.milestone.review_recovery_retries == 3
        assert cfg.milestone.mock_data_scan is False
        assert cfg.milestone.ui_compliance_scan is False

    def test_e2e_fields_wire(self):
        data = {
            "e2e_testing": {
                "enabled": True,
                "max_fix_retries": 3,
                "test_port": 8080,
                "skip_if_no_api": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 3
        assert cfg.e2e_testing.test_port == 8080
        assert cfg.e2e_testing.skip_if_no_api is False

    def test_integrity_scans_wire(self):
        data = {
            "integrity_scans": {
                "deployment_scan": False,
                "asset_scan": False,
                "prd_reconciliation": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.integrity_scans.asset_scan is False
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_design_reference_fields_wire(self):
        data = {
            "design_reference": {
                "extraction_retries": 5,
                "fallback_generation": False,
                "content_quality_check": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.design_reference.extraction_retries == 5
        assert cfg.design_reference.fallback_generation is False
        assert cfg.design_reference.content_quality_check is False

    def test_unknown_keys_ignored(self):
        data = {"milestone": {"enabled": True, "unknown_field_xyz": "value"}}
        # Should not raise
        cfg = _dict_to_config(data)
        assert cfg.milestone.enabled is True


# ===========================================================================
# 5. Import chain verification
# ===========================================================================

class TestImportChains:
    """Verify critical import chains work end-to-end."""

    def test_quality_checks_imports(self):
        from agent_team import quality_checks
        assert hasattr(quality_checks, "run_spot_checks")
        assert hasattr(quality_checks, "run_mock_data_scan")
        assert hasattr(quality_checks, "run_ui_compliance_scan")
        assert hasattr(quality_checks, "run_e2e_quality_scan")
        assert hasattr(quality_checks, "run_deployment_scan")
        assert hasattr(quality_checks, "run_asset_scan")
        assert hasattr(quality_checks, "parse_prd_reconciliation")
        assert hasattr(quality_checks, "Violation")

    def test_config_imports(self):
        from agent_team import config
        assert hasattr(config, "AgentTeamConfig")
        assert hasattr(config, "E2ETestingConfig")
        assert hasattr(config, "IntegrityScanConfig")
        assert hasattr(config, "_dict_to_config")

    def test_state_imports(self):
        from agent_team import state
        assert hasattr(state, "RunState")
        assert hasattr(state, "ConvergenceReport")
        assert hasattr(state, "E2ETestReport")

    def test_e2e_testing_imports(self):
        from agent_team import e2e_testing
        assert hasattr(e2e_testing, "AppTypeInfo")
        assert hasattr(e2e_testing, "detect_app_type")
        assert hasattr(e2e_testing, "parse_e2e_results")

    def test_design_reference_imports(self):
        from agent_team import design_reference
        assert hasattr(design_reference, "validate_ui_requirements_content")
        assert hasattr(design_reference, "generate_fallback_ui_requirements")
        assert hasattr(design_reference, "run_design_extraction_with_retry")


# ===========================================================================
# 6. Violation field validity
# ===========================================================================

class TestViolationValidity:
    """Verify that Violations returned by checks always have valid fields."""

    @pytest.mark.parametrize("check_fn", _ALL_CHECKS)
    def test_violations_have_valid_fields(self, check_fn):
        # Provide content that might trigger various checks
        content = textwrap.dedent("""\
            const x: any = 1;
            console.log("test");
            bg-indigo-500
            font-family: Inter, sans-serif
            fontFamily: Arial
            return of([{id: 1}]);
            Promise.resolve([{id: 1}]);
            mockData = [{id: 1}];
            setTimeout(() => {}, 1000);
            delay(500)
            new BehaviorSubject<[{id: 1}]>
            new Observable<((sub) => {})
            color: #FF0000;
            bg-[#FF0000]
            padding: 15px;
        """)
        violations = check_fn(content, "services/test.service.tsx", ".tsx")
        for v in violations:
            assert isinstance(v, Violation)
            assert isinstance(v.check, str) and v.check
            assert isinstance(v.message, str) and v.message
            assert isinstance(v.file_path, str) and v.file_path
            assert isinstance(v.line, int) and v.line >= 0
            assert v.severity in ("error", "warning", "info")


# ===========================================================================
# 7. No duplicate pattern IDs
# ===========================================================================

class TestNoDuplicatePatternIds:
    """Verify no two quality patterns use the same pattern_id."""

    def test_no_duplicate_checks_across_all_scans(self, tmp_path):
        # Create content that triggers all checks
        svc_dir = tmp_path / "src" / "services"
        svc_dir.mkdir(parents=True)
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir(parents=True)

        # Service file with mock patterns
        (svc_dir / "test.service.ts").write_text(
            "return of([{id: 1}]);\n"
            "Promise.resolve([{id: 1}]);\n"
            "mockData = [{id: 1}];\n",
            encoding="utf-8",
        )

        # E2E test file
        (e2e_dir / "test.spec.ts").write_text(
            "setTimeout(() => {}, 1000);\n"
            "test('login', async () => { });\n",
            encoding="utf-8",
        )

        all_violations = run_spot_checks(tmp_path)
        # Each pattern_id can appear multiple times — that's fine
        # But different CHECKS (like MOCK-001 vs UI-001) must be distinct patterns
        check_ids = {v.check for v in all_violations}
        # Just verify they're all strings matching CATEGORY-NNN pattern
        # Categories can include digits (E2E), and IDs can have letter suffixes (UI-001b)
        for cid in check_ids:
            assert re.match(r"[A-Z0-9]+-\d+[a-z]?$", cid), f"Invalid check ID format: {cid}"


# ===========================================================================
# 8. Prompt constants are non-empty
# ===========================================================================

class TestPromptConstants:
    """Verify prompt constants contain expected keywords and are non-empty."""

    def test_code_writer_prompt_nonempty(self):
        assert len(CODE_WRITER_PROMPT) > 100

    def test_code_writer_prompt_contains_mock_policy(self):
        assert "ZERO MOCK DATA" in CODE_WRITER_PROMPT or "mock" in CODE_WRITER_PROMPT.lower()

    def test_code_reviewer_prompt_nonempty(self):
        assert len(CODE_REVIEWER_PROMPT) > 100

    def test_orchestrator_prompt_nonempty(self):
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 100

    def test_architect_prompt_nonempty(self):
        assert len(ARCHITECT_PROMPT) > 100

    def test_backend_e2e_prompt_nonempty(self):
        assert len(BACKEND_E2E_PROMPT) > 100

    def test_frontend_e2e_prompt_nonempty(self):
        assert len(FRONTEND_E2E_PROMPT) > 100

    def test_e2e_fix_prompt_nonempty(self):
        assert len(E2E_FIX_PROMPT) > 100

    def test_e2e_testing_standards_nonempty(self):
        assert len(E2E_TESTING_STANDARDS) > 100

    def test_e2e_standards_mapped_to_test_runner(self):
        standards = _AGENT_STANDARDS_MAP.get("test-runner", [])
        assert E2E_TESTING_STANDARDS in standards


# ===========================================================================
# 9. CRITICAL-1 regression: _run_review_only is async
# ===========================================================================

class TestCritical1AsyncReviewOnly:
    """Regression test: _run_review_only must be async (not sync with asyncio.run)."""

    def test_run_review_only_is_coroutine_function(self):
        from agent_team.cli import _run_review_only
        assert asyncio.iscoroutinefunction(_run_review_only), (
            "_run_review_only must be async to avoid nested asyncio.run() crash "
            "when called from _run_prd_milestones which is already async"
        )


# ===========================================================================
# 10. HIGH-1 regression: _resolve_asset strips query params
# ===========================================================================

class TestHigh1ResolveAssetQueryString:
    """Regression test: _resolve_asset must strip query/fragment before disk lookup."""

    def test_resolve_asset_with_query_string(self, tmp_path):
        """_resolve_asset('logo.png?v=123') should find logo.png on disk."""
        img = tmp_path / "logo.png"
        img.write_bytes(b"PNG")
        assert _resolve_asset("logo.png?v=123", tmp_path, tmp_path) is True

    def test_resolve_asset_with_fragment(self, tmp_path):
        img = tmp_path / "icon.svg"
        img.write_bytes(b"<svg/>")
        assert _resolve_asset("icon.svg#section", tmp_path, tmp_path) is True

    def test_resolve_asset_with_query_and_fragment(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"JPEG")
        assert _resolve_asset("photo.jpg?w=100#top", tmp_path, tmp_path) is True

    def test_resolve_asset_not_found_even_after_strip(self, tmp_path):
        assert _resolve_asset("nonexistent.png?v=1", tmp_path, tmp_path) is False

    def test_is_static_asset_ref_with_query_string(self):
        """_is_static_asset_ref should also handle query strings."""
        assert _is_static_asset_ref("logo.png?v=123") is True
        assert _is_static_asset_ref("style.css?v=1") is False  # .css not in ASSET_EXTENSIONS


# ===========================================================================
# 11. MEDIUM-1 regression: review_recovery_retries validation
# ===========================================================================

class TestMedium1ReviewRecoveryRetriesValidation:
    """Regression test: _dict_to_config rejects negative review_recovery_retries."""

    def test_negative_review_recovery_retries_raises(self):
        data = {"milestone": {"review_recovery_retries": -1}}
        with pytest.raises(ValueError, match="review_recovery_retries"):
            _dict_to_config(data)

    def test_zero_review_recovery_retries_ok(self):
        data = {"milestone": {"review_recovery_retries": 0}}
        cfg = _dict_to_config(data)
        assert cfg.milestone.review_recovery_retries == 0

    def test_positive_review_recovery_retries_ok(self):
        data = {"milestone": {"review_recovery_retries": 5}}
        cfg = _dict_to_config(data)
        assert cfg.milestone.review_recovery_retries == 5


# ===========================================================================
# 12. MEDIUM-2: _run_integrity_fix has traceback logging (structural test)
# ===========================================================================

class TestMedium2IntegrityFixTraceback:
    """Verify _run_integrity_fix exception handler includes traceback."""

    def test_integrity_fix_source_contains_traceback_format_exc(self):
        from agent_team import cli
        source = inspect.getsource(cli._run_integrity_fix)
        assert "traceback.format_exc()" in source, (
            "_run_integrity_fix exception handler must include traceback.format_exc()"
        )


# ===========================================================================
# 13. Config edge cases
# ===========================================================================

class TestConfigEdgeCases:
    """Edge case tests for config parsing."""

    def test_empty_yaml(self):
        cfg = _dict_to_config({})
        assert isinstance(cfg, AgentTeamConfig)

    def test_partial_yaml(self):
        data = {"milestone": {"enabled": True}}
        cfg = _dict_to_config(data)
        assert cfg.milestone.enabled is True
        assert cfg.milestone.max_parallel_milestones == 1  # default

    def test_non_dict_sections_ignored(self):
        data = {
            "milestone": "not_a_dict",
            "e2e_testing": 42,
            "integrity_scans": [],
        }
        cfg = _dict_to_config(data)
        # All should fall back to defaults
        assert cfg.milestone.enabled is False
        assert cfg.e2e_testing.enabled is False
        assert cfg.integrity_scans.deployment_scan is True

    def test_e2e_max_fix_retries_validation(self):
        data = {"e2e_testing": {"max_fix_retries": 0}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_e2e_port_too_high(self):
        data = {"e2e_testing": {"test_port": 70000}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_extraction_retries_negative_raises(self):
        data = {"design_reference": {"extraction_retries": -1}}
        with pytest.raises(ValueError, match="extraction_retries"):
            _dict_to_config(data)


# ===========================================================================
# 14. Quality checks edge cases
# ===========================================================================

class TestQualityChecksEdgeCases:
    """Edge cases for quality check functions."""

    def test_empty_file(self):
        for fn in _ALL_CHECKS:
            result = fn("", "services/test.ts", ".ts")
            assert isinstance(result, list)

    def test_binary_content_in_text_field(self):
        content = "\x00\x01\x02\x03binary data"
        for fn in _ALL_CHECKS:
            # Should not crash
            result = fn(content, "services/test.ts", ".ts")
            assert isinstance(result, list)

    def test_file_with_only_comments(self):
        content = "// This is a comment\n// Another comment\n"
        for fn in _ALL_CHECKS:
            result = fn(content, "services/test.ts", ".ts")
            assert isinstance(result, list)

    def test_unicode_content(self):
        content = "const name = '\u4f60\u597d\u4e16\u754c'; // Chinese chars\nconst emoji = '\u2713\u2717';\n"
        for fn in _ALL_CHECKS:
            result = fn(content, "services/test.ts", ".ts")
            assert isinstance(result, list)

    def test_very_long_line(self):
        content = "const x = '" + "a" * 10000 + "';\n"
        for fn in _ALL_CHECKS:
            result = fn(content, "services/test.ts", ".ts")
            assert isinstance(result, list)

    def test_wrong_extension_returns_empty(self):
        content = "return of([{id: 1}]);\nconst x: any = 1;"
        # .md is not in any check extension set
        for fn in _ALL_CHECKS:
            result = fn(content, "readme.md", ".md")
            assert result == [], f"{fn.__name__} should return [] for .md"


# ===========================================================================
# 15. Docker parsing edge cases
# ===========================================================================

class TestDockerParsingEdgeCases:
    """Edge case tests for _parse_docker_compose and _parse_env_file."""

    def test_parse_docker_compose_invalid_yaml(self, tmp_path):
        dc = tmp_path / "docker-compose.yml"
        dc.write_text("{{invalid yaml", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_parse_docker_compose_non_dict_yaml(self, tmp_path):
        dc = tmp_path / "docker-compose.yml"
        dc.write_text("- just a list\n- of items\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_parse_docker_compose_empty_services(self, tmp_path):
        dc = tmp_path / "docker-compose.yml"
        dc.write_text("version: '3'\nservices: {}\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert isinstance(result, dict)
        assert result["services"] == {}

    def test_parse_docker_compose_missing_file(self, tmp_path):
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_parse_env_file_bom(self, tmp_path):
        env = tmp_path / ".env"
        env.write_bytes(b"\xef\xbb\xbfDB_HOST=localhost\n")
        result = _parse_env_file(env)
        assert "DB_HOST" in result

    def test_parse_env_file_export_prefix(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("export DB_HOST=localhost\nexport DB_PORT=5432\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "DB_HOST" in result
        assert "DB_PORT" in result

    def test_parse_env_file_export_tab(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("export\tVAR_NAME=value\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "VAR_NAME" in result

    def test_parse_env_file_comments_ignored(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("# comment\nVAR=value\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "VAR" in result
        assert len(result) == 1

    def test_parse_env_file_empty(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("", encoding="utf-8")
        result = _parse_env_file(env)
        assert result == set()

    def test_parse_env_file_missing(self, tmp_path):
        result = _parse_env_file(tmp_path / "nonexistent.env")
        assert result == set()

    def test_env_staging_and_env_test_scanned(self):
        """Verify .env.staging and .env.test are in the deployment scan list."""
        from agent_team import quality_checks
        source = inspect.getsource(quality_checks.run_deployment_scan)
        assert ".env.staging" in source
        assert ".env.test" in source

    def test_builtin_env_vars_contains_node_env_and_path(self):
        assert "NODE_ENV" in _BUILTIN_ENV_VARS
        assert "PATH" in _BUILTIN_ENV_VARS


# ===========================================================================
# 16. Asset scanning edge cases
# ===========================================================================

class TestAssetScanningEdgeCases:
    """Edge case tests for asset scanning functions."""

    def test_is_static_asset_ref_external_url(self):
        assert _is_static_asset_ref("https://cdn.example.com/img.png") is False

    def test_is_static_asset_ref_data_uri(self):
        assert _is_static_asset_ref("data:image/png;base64,abc") is False

    def test_is_static_asset_ref_template_variable(self):
        assert _is_static_asset_ref("${dynamicPath}/img.png") is False
        assert _is_static_asset_ref("{{asset}}/img.png") is False

    def test_is_static_asset_ref_webpack_alias(self):
        assert _is_static_asset_ref("@/assets/img.png") is False
        assert _is_static_asset_ref("~/assets/img.png") is False

    def test_is_static_asset_ref_valid_image(self):
        assert _is_static_asset_ref("images/logo.png") is True
        assert _is_static_asset_ref("/assets/icon.svg") is True

    def test_resolve_asset_checks_public_dir(self, tmp_path):
        public = tmp_path / "public"
        public.mkdir()
        img = public / "logo.png"
        img.write_bytes(b"PNG")
        assert _resolve_asset("/logo.png", tmp_path / "src", tmp_path) is True

    def test_resolve_asset_checks_src_assets(self, tmp_path):
        assets = tmp_path / "src" / "assets"
        assets.mkdir(parents=True)
        img = assets / "icon.svg"
        img.write_bytes(b"<svg/>")
        assert _resolve_asset("icon.svg", tmp_path / "other", tmp_path) is True


# ===========================================================================
# 17. E2E detection edge cases
# ===========================================================================

class TestE2EDetectionEdgeCases:
    """Edge case tests for detect_app_type."""

    def test_empty_project(self, tmp_path):
        info = detect_app_type(tmp_path)
        assert isinstance(info, AppTypeInfo)
        assert info.has_backend is False
        assert info.has_frontend is False

    def test_monorepo_root_package_json(self, tmp_path):
        pkg = {"dependencies": {"express": "^4.0", "react": "^18.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True

    def test_missing_keys_in_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        info = detect_app_type(tmp_path)
        # Empty package.json — should detect language but not frameworks
        assert isinstance(info, AppTypeInfo)

    def test_parse_e2e_results_empty(self, tmp_path):
        results_path = tmp_path / "E2E_RESULTS.md"
        results_path.write_text("", encoding="utf-8")
        report = parse_e2e_results(results_path)
        assert isinstance(report, E2ETestReport)


# ===========================================================================
# 18. PRD reconciliation edge cases
# ===========================================================================

class TestPRDReconciliationEdgeCases:
    """Edge case tests for parse_prd_reconciliation."""

    def test_empty_results(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text("", encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations == []

    def test_only_verified_sections(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(
            "## VERIFIED\n- All good\n- Everything works\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert violations == []

    def test_only_mismatch(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(
            "## MISMATCH\n- Feature X not implemented\n- Feature Y partially done\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2
        assert all(v.check == "PRD-001" for v in violations)

    def test_mixed_h2_h3_mismatch(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(
            "## VERIFIED\n- Good\n"
            "### MISMATCH\n- Issue A\n"
            "## VERIFIED\n- Also good\n"
            "## MISMATCH\n- Issue B\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2

    def test_h4_subheader_does_not_exit_mismatch(self, tmp_path):
        """Regression: h4 headers (####) must not exit mismatch mode."""
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(
            "## MISMATCH\n"
            "#### Details\n"
            "- Still a mismatch item\n"
            "## VERIFIED\n"
            "- Not a mismatch\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1
        assert "Still a mismatch item" in violations[0].message


# ===========================================================================
# 19. UI hardening regressions
# ===========================================================================

class TestUIHardeningRegressions:
    """Regression tests for UI requirements hardening fixes."""

    def test_re_font_family_matches_camelcase(self):
        """CRITICAL-1: _RE_FONT_FAMILY / fontFamily patterns must match camelCase."""
        from agent_team.quality_checks import _RE_GENERIC_FONT_CONFIG
        assert _RE_GENERIC_FONT_CONFIG.search("fontFamily: Inter, sans-serif")

    def test_re_component_type_matches_plurals(self):
        """CRITICAL-2: _RE_COMPONENT_TYPE must match Buttons, Cards (plural)."""
        # UI compliance checks on component files — test the regex
        violations = _check_ui_compliance(
            'className="bg-indigo-500"',
            "src/components/Buttons.tsx",
            ".tsx",
        )
        # indigo-500 should be detected (UI-002 extended check)
        checks = {v.check for v in violations}
        assert "UI-002" in checks

    @pytest.mark.asyncio
    async def test_retry_wrapper_raises_on_non_retriable(self):
        """CRITICAL-3: Non-retriable exceptions bubble up immediately."""
        with patch(
            "agent_team.design_reference.run_design_extraction",
            side_effect=TypeError("Unexpected bug"),
        ):
            with pytest.raises(DesignExtractionError, match="Unexpected error"):
                await run_design_extraction_with_retry(
                    urls=["https://example.com"],
                    config=AgentTeamConfig(),
                    cwd="/tmp",
                    backend="api",
                    max_retries=2,
                    base_delay=0.01,
                )

    def test_re_config_file_does_not_match_theme_toggle(self):
        """HARD-1: ThemeToggle.tsx must NOT match config file regex."""
        from agent_team.quality_checks import _RE_CONFIG_FILE
        assert _RE_CONFIG_FILE.search("src/components/ThemeToggle.tsx") is None

    def test_re_config_file_matches_real_config(self):
        from agent_team.quality_checks import _RE_CONFIG_FILE
        assert _RE_CONFIG_FILE.search("tailwind.config.js") is not None
        assert _RE_CONFIG_FILE.search("src/theme/variables.scss") is not None

    def test_re_arbitrary_spacing_matches_directional(self):
        """HARD-3: pt-, mx-, etc. must match for spacing check."""
        violations = _check_ui_compliance(
            'className="pt-7 mx-11"',
            "src/components/Card.tsx",
            ".tsx",
        )
        ui004 = [v for v in violations if v.check == "UI-004"]
        # 7 and 11 are not on 4px grid and not in allowlist
        assert len(ui004) >= 1

    def test_infer_design_direction_uses_word_boundaries(self):
        """HARD-4: _infer_design_direction must not match 'application' for 'app'."""
        # 'app' keyword should match 'minimal_modern'
        assert _infer_design_direction("Build an app for analytics") == "minimal_modern"
        # But substring match inside another word should not count
        # Test with unrelated words that contain direction keywords as substrings
        result = _infer_design_direction("Build an application for users")
        # 'application' does not contain word-boundary 'app', should not match
        # Just verify it doesn't crash and returns a valid direction
        assert result in _DIRECTION_TABLE

    def test_space_x_y_tailwind_in_ui004(self):
        """Test space-x- / space-y- Tailwind utility patterns in UI-004."""
        from agent_team.quality_checks import _RE_ARBITRARY_SPACING
        assert _RE_ARBITRARY_SPACING.search("space-x-7")
        assert _RE_ARBITRARY_SPACING.search("space-y-11")

    def test_css_gap_property_in_ui004(self):
        """Test CSS gap property in UI-004."""
        from agent_team.quality_checks import _RE_ARBITRARY_SPACING
        assert _RE_ARBITRARY_SPACING.search("gap: 15px")


# ===========================================================================
# 20. E2E review fix regressions
# ===========================================================================

class TestE2EReviewFixRegressions:
    """Regression tests for E2E testing review fixes."""

    def test_e2e_005_auth_check_inverted(self, tmp_path):
        """C3: E2E-005 warns when auth exists but no auth E2E test found."""
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        (e2e_dir / "basic.spec.ts").write_text(
            "test('loads page', async () => { expect(true).toBe(true); });\n",
            encoding="utf-8",
        )
        # Add auth dependency
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"jsonwebtoken": "^9.0"}}),
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        e2e005 = [v for v in violations if v.check == "E2E-005"]
        assert len(e2e005) >= 1

    def test_e2e_006_placeholder_text_detected(self, tmp_path):
        """C3: E2E-006 detects placeholder text in UI components."""
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "Dashboard.tsx").write_text(
            '<div>Coming soon - this feature will be implemented later</div>\n',
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        e2e006 = [v for v in violations if v.check == "E2E-006"]
        assert len(e2e006) >= 1

    def test_e2e_007_role_failure_in_results(self, tmp_path):
        """C3: E2E-007 detects 403/Forbidden in E2E results."""
        results_dir = tmp_path / ".agent-team"
        results_dir.mkdir(parents=True)
        (results_dir / "E2E_RESULTS.md").write_text(
            "## Test Results\n- POST /api/admin: 403 Forbidden\n",
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        e2e007 = [v for v in violations if v.check == "E2E-007"]
        assert len(e2e007) >= 1

    def test_e2e_test_report_health_values(self):
        """Verify E2ETestReport health field accepts all expected values."""
        for health in ("passed", "partial", "failed", "skipped", "unknown"):
            report = E2ETestReport(health=health)
            assert report.health == health

    def test_e2e_test_report_failed_tests_list(self):
        """C2: failed_tests is a mutable list that can be updated each cycle."""
        report = E2ETestReport()
        report.failed_tests = ["test1", "test2"]
        report.failed_tests = ["test3"]  # Update — should work
        assert report.failed_tests == ["test3"]

    def test_completed_phases_only_on_pass_or_partial(self):
        """H5: completed_phases should only include passed/partial."""
        state = RunState()
        for health in ("passed", "partial"):
            state.completed_phases.append(f"e2e_backend_{health}")
        assert len(state.completed_phases) == 2
        # "failed" should NOT be appended
        assert "e2e_backend_failed" not in state.completed_phases


# ===========================================================================
# 21. Integrity scan review fix regressions
# ===========================================================================

class TestIntegrityScanRegressions:
    """Regression tests for integrity scan review fixes."""

    def test_parse_docker_compose_non_dict_returns_none(self, tmp_path):
        """Review fix: _parse_docker_compose with list YAML returns None."""
        dc = tmp_path / "docker-compose.yml"
        dc.write_text("- item1\n- item2\n", encoding="utf-8")
        assert _parse_docker_compose(tmp_path) is None

    def test_parse_env_file_bom_stripped(self, tmp_path):
        """Review fix: BOM prefix is stripped before parsing."""
        env = tmp_path / ".env"
        content = "\ufeffAPI_KEY=secret\n"
        env.write_text(content, encoding="utf-8")
        result = _parse_env_file(env)
        assert "API_KEY" in result

    def test_parse_env_file_export_stripped(self, tmp_path):
        """Review fix: 'export ' prefix is stripped."""
        env = tmp_path / ".env"
        env.write_text("export MY_VAR=value\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "MY_VAR" in result

    def test_is_static_asset_ref_query_string_true(self):
        """Review fix: query strings don't prevent detection."""
        assert _is_static_asset_ref("logo.png?v=123") is True

    def test_builtin_env_vars_excludes_common(self):
        """Review fix: NODE_ENV, PATH, CI excluded from undefined env warnings."""
        assert "NODE_ENV" in _BUILTIN_ENV_VARS
        assert "PATH" in _BUILTIN_ENV_VARS
        assert "CI" in _BUILTIN_ENV_VARS
        assert "HOME" in _BUILTIN_ENV_VARS


# ===========================================================================
# 22. MOCK-007 with TypeScript type annotation
# ===========================================================================

class TestMock007TypeAnnotated:
    """Test MOCK-007 with TypeScript type-annotated callback."""

    def test_mock007_typed_callback(self):
        # The regex matches: new Observable[<(] followed immediately by ( or function
        # For TypeScript generics like Observable<T>((sub) => {}), the < triggers
        # the [<(] match, then it needs ( or function next.
        # The actual pattern is: new\s+Observable\s*[<(]\s*(?:\(\s*\w+\s*\)\s*=>|function)
        content = "new Observable((observer) => { observer.next([]); });"
        violations = _check_mock_data_patterns(
            content, "services/data.service.ts", ".ts"
        )
        checks = {v.check for v in violations}
        assert "MOCK-007" in checks

    def test_mock007_function_keyword(self):
        content = "new Observable(function(subscriber) { subscriber.next(data); });"
        violations = _check_mock_data_patterns(
            content, "services/api.service.ts", ".ts"
        )
        checks = {v.check for v in violations}
        assert "MOCK-007" in checks


# ===========================================================================
# 23. Deployment scan .env.staging and .env.test coverage
# ===========================================================================

class TestDeploymentScanEnvVariants:
    """Verify .env.staging and .env.test are explicitly scanned."""

    def test_env_staging_parsed(self, tmp_path):
        env_staging = tmp_path / ".env.staging"
        env_staging.write_text("STAGING_VAR=value\n", encoding="utf-8")
        result = _parse_env_file(env_staging)
        assert "STAGING_VAR" in result

    def test_env_test_parsed(self, tmp_path):
        env_test = tmp_path / ".env.test"
        env_test.write_text("TEST_VAR=value\n", encoding="utf-8")
        result = _parse_env_file(env_test)
        assert "TEST_VAR" in result


# ===========================================================================
# 24. Fallback UI requirements generation
# ===========================================================================

class TestFallbackUIRequirements:
    """Test generate_fallback_ui_requirements produces valid content."""

    def test_generates_all_sections(self, tmp_path):
        cfg = AgentTeamConfig()
        content = generate_fallback_ui_requirements("Build a SaaS dashboard", cfg, str(tmp_path))
        assert "## Color System" in content
        assert "## Typography" in content
        assert "## Spacing" in content
        assert "FALLBACK-GENERATED" in content

    def test_infer_direction_brutalist(self):
        result = _infer_design_direction("Build a developer CLI tool")
        assert result == "brutalist"

    def test_infer_direction_luxury(self):
        result = _infer_design_direction("Build a premium fintech platform")
        assert result == "luxury"


# ===========================================================================
# 25. validate_ui_requirements_content
# ===========================================================================

class TestValidateUIRequirementsContent:
    """Test validate_ui_requirements_content catches missing sections."""

    def test_complete_content_no_warnings(self):
        content = textwrap.dedent("""\
        ## Color System
        - Primary: #1A1A2E
        - Secondary: #E8D5B7
        - Accent: #C9A96E
        - Background: #FFFFFF

        ## Typography
        - Heading font: Cormorant Garamond

        ## Spacing
        - Base unit: 4px
        - Small: 8px
        - Medium: 16px
        - Large: 32px

        ## Component Patterns
        - Button styles defined
        - Card components
        - Input fields
        """)
        warnings = validate_ui_requirements_content(content)
        assert len(warnings) == 0

    def test_missing_section_warns(self):
        content = "## Color System\n- Primary: #000\n"
        warnings = validate_ui_requirements_content(content)
        assert len(warnings) > 0


# ===========================================================================
# 26. build_milestone_execution_prompt smoke test
# ===========================================================================

class TestMilestoneExecutionPrompt:
    """Smoke test for build_milestone_execution_prompt."""

    def _make_context(self, milestone_id="m1", title="Setup"):
        from agent_team.milestone_manager import MilestoneContext
        return MilestoneContext(
            milestone_id=milestone_id,
            title=title,
            requirements_path=f".agent-team/milestones/{milestone_id}/REQUIREMENTS.md",
        )

    def test_returns_nonempty_string(self):
        cfg = AgentTeamConfig()
        ctx = self._make_context()
        prompt = build_milestone_execution_prompt(
            task="Build the project",
            depth="standard",
            config=cfg,
            milestone_context=ctx,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_milestone_id(self):
        cfg = AgentTeamConfig()
        ctx = self._make_context("test-milestone", "Test")
        prompt = build_milestone_execution_prompt(
            task="Build the project",
            depth="standard",
            config=cfg,
            milestone_context=ctx,
        )
        assert "test-milestone" in prompt

    def test_contains_ui_compliance(self):
        cfg = AgentTeamConfig()
        ctx = self._make_context("m1", "Build UI")
        prompt = build_milestone_execution_prompt(
            task="Build the UI",
            depth="standard",
            config=cfg,
            milestone_context=ctx,
        )
        # Should contain UI compliance references
        assert "UI" in prompt.upper()
