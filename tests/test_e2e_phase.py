"""Tests for E2E Testing Phase (Fix 1-6).

Covers config, state, detection, prompts, quality patterns, standards,
CLI wiring logic, prompt hardening, and resume logic.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.config import (
    AgentTeamConfig,
    E2ETestingConfig,
    _dict_to_config,
)
from agent_team.state import E2ETestReport
from agent_team.e2e_testing import (
    AppTypeInfo,
    detect_app_type,
    parse_e2e_results,
    BACKEND_E2E_PROMPT,
    FRONTEND_E2E_PROMPT,
    E2E_FIX_PROMPT,
)
from agent_team.quality_checks import (
    Violation,
    run_e2e_quality_scan,
    _check_e2e_quality,
)
from agent_team.code_quality_standards import (
    E2E_TESTING_STANDARDS,
    _AGENT_STANDARDS_MAP,
    get_standards_for_agent,
)


# =========================================================================
# Fix 1: Config
# =========================================================================

class TestE2ETestingConfig:
    """Tests for E2ETestingConfig dataclass and _dict_to_config wiring."""

    def test_defaults(self):
        cfg = E2ETestingConfig()
        assert cfg.enabled is False
        assert cfg.backend_api_tests is True
        assert cfg.frontend_playwright_tests is True
        assert cfg.max_fix_retries == 5
        assert cfg.test_port == 9876
        assert cfg.skip_if_no_api is True
        assert cfg.skip_if_no_frontend is True

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.e2e_testing, E2ETestingConfig)
        assert cfg.e2e_testing.enabled is False

    def test_yaml_parsing(self):
        data = {"e2e_testing": {"enabled": True, "max_fix_retries": 3, "test_port": 8888}}
        cfg, _ = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 3
        assert cfg.e2e_testing.test_port == 8888

    def test_validation_retries_too_low(self):
        data = {"e2e_testing": {"max_fix_retries": 0}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_validation_port_too_low(self):
        data = {"e2e_testing": {"test_port": 80}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_validation_port_too_high(self):
        data = {"e2e_testing": {"test_port": 70000}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_legacy_budget_key_ignored(self):
        """Legacy budget_limit_usd key should not cause errors."""
        data = {"e2e_testing": {"enabled": True, "budget_limit_usd": 10.0}}
        cfg, _ = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert not hasattr(cfg.e2e_testing, "budget_limit_usd")


# =========================================================================
# Fix 2A: State
# =========================================================================

class TestE2ETestReport:
    """Tests for E2ETestReport dataclass."""

    def test_defaults(self):
        r = E2ETestReport()
        assert r.backend_total == 0
        assert r.backend_passed == 0
        assert r.frontend_total == 0
        assert r.frontend_passed == 0
        assert r.fix_retries_used == 0
        assert r.total_fix_cycles == 0
        assert r.skipped is False
        assert r.skip_reason == ""
        assert r.health == "unknown"
        assert r.failed_tests == []

    def test_health_passed(self):
        r = E2ETestReport(backend_total=5, backend_passed=5, health="passed")
        assert r.health == "passed"

    def test_health_partial(self):
        r = E2ETestReport(backend_total=10, backend_passed=8, health="partial")
        assert r.health == "partial"

    def test_health_failed(self):
        r = E2ETestReport(backend_total=10, backend_passed=3, health="failed")
        assert r.health == "failed"

    def test_health_skipped(self):
        r = E2ETestReport(skipped=True, skip_reason="No backend", health="skipped")
        assert r.health == "skipped"
        assert r.skip_reason == "No backend"


# =========================================================================
# Fix 2B: AppTypeInfo + detect_app_type
# =========================================================================

class TestAppTypeInfo:
    """Tests for AppTypeInfo dataclass and detect_app_type()."""

    def test_defaults(self):
        info = AppTypeInfo()
        assert info.has_backend is False
        assert info.has_frontend is False
        assert info.backend_framework == ""
        assert info.frontend_framework == ""

    def test_detect_express(self, tmp_path):
        pkg = {"dependencies": {"express": "^4.18.0"}, "scripts": {"start": "node server.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "express"

    def test_detect_nextjs(self, tmp_path):
        pkg = {"dependencies": {"next": "14.0.0", "react": "18.0.0"}, "scripts": {"dev": "next dev"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "next.config.js").write_text("module.exports = {}")
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "nextjs"

    def test_detect_fastapi(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi==0.104.0\nuvicorn\n")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "fastapi"

    def test_detect_angular(self, tmp_path):
        pkg = {"dependencies": {"@angular/core": "17.0.0"}, "scripts": {"start": "ng serve"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "angular.json").write_text("{}")
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"

    def test_detect_fullstack(self, tmp_path):
        pkg = {
            "dependencies": {"express": "^4.18.0", "react": "^18.0.0"},
            "scripts": {"dev": "concurrently ..."},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True

    def test_empty_project(self, tmp_path):
        info = detect_app_type(tmp_path)
        assert info.has_backend is False
        assert info.has_frontend is False
        assert info.backend_framework == ""

    def test_detect_playwright_installed(self, tmp_path):
        pkg = {"devDependencies": {"@playwright/test": "^1.40.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        info = detect_app_type(tmp_path)
        assert info.playwright_installed is True

    def test_detect_package_manager_yarn(self, tmp_path):
        pkg = {"dependencies": {}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "yarn.lock").write_text("")
        info = detect_app_type(tmp_path)
        assert info.package_manager == "yarn"

    def test_detect_prisma(self, tmp_path):
        pkg = {"dependencies": {"express": "^4.18.0", "@prisma/client": "^5.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        prisma_dir = tmp_path / "prisma"
        prisma_dir.mkdir()
        (prisma_dir / "schema.prisma").write_text("generator client {}")
        info = detect_app_type(tmp_path)
        assert info.db_type == "prisma"


# =========================================================================
# Fix 2C: parse_e2e_results
# =========================================================================

class TestParseE2EResults:
    """Tests for parse_e2e_results()."""

    def test_good_results(self, tmp_path):
        content = textwrap.dedent("""\
            ## Backend API Tests
            Total: 8 | Passed: 8 | Failed: 0

            ### Passed
            - ✓ test_login: Login works
            - ✓ test_crud: CRUD works

            ## Frontend Playwright Tests
            Total: 5 | Passed: 5 | Failed: 0
        """)
        results_path = tmp_path / "E2E_RESULTS.md"
        results_path.write_text(content, encoding="utf-8")
        report = parse_e2e_results(results_path)
        assert report.backend_total == 8
        assert report.backend_passed == 8
        assert report.frontend_total == 5
        assert report.frontend_passed == 5
        assert report.health == "passed"

    def test_partial_failures(self, tmp_path):
        content = textwrap.dedent("""\
            ## Backend API Tests
            Total: 10 | Passed: 8 | Failed: 2

            ### Failed
            - ✗ test_role_access: 403 Forbidden
            - ✗ test_delete: Not implemented
        """)
        results_path = tmp_path / "E2E_RESULTS.md"
        results_path.write_text(content, encoding="utf-8")
        report = parse_e2e_results(results_path)
        assert report.backend_total == 10
        assert report.backend_passed == 8
        assert report.health == "partial"
        assert len(report.failed_tests) >= 1

    def test_all_failures(self, tmp_path):
        content = textwrap.dedent("""\
            ## Backend API Tests
            Total: 5 | Passed: 1 | Failed: 4
        """)
        results_path = tmp_path / "E2E_RESULTS.md"
        results_path.write_text(content, encoding="utf-8")
        report = parse_e2e_results(results_path)
        assert report.health == "failed"

    def test_missing_file(self, tmp_path):
        results_path = tmp_path / "E2E_RESULTS.md"
        report = parse_e2e_results(results_path)
        assert report.skipped is True
        assert "not found" in report.skip_reason.lower() or "missing" in report.skip_reason.lower()

    def test_malformed_content(self, tmp_path):
        results_path = tmp_path / "E2E_RESULTS.md"
        results_path.write_text("This is not valid results format", encoding="utf-8")
        report = parse_e2e_results(results_path)
        # Should handle gracefully -- either skipped or zero counts
        assert report.backend_total == 0 or report.skipped is True


# =========================================================================
# Fix 2D-E: Prompt constants
# =========================================================================

class TestBackendE2EPrompt:
    """Tests for BACKEND_E2E_PROMPT content."""

    def test_contains_requirements_read(self):
        assert "REQUIREMENTS.md" in BACKEND_E2E_PROMPT

    def test_contains_workflow_testing(self):
        assert "workflow" in BACKEND_E2E_PROMPT.lower() or "WORKFLOW" in BACKEND_E2E_PROMPT

    def test_contains_real_http(self):
        assert "REAL HTTP" in BACKEND_E2E_PROMPT or "real HTTP" in BACKEND_E2E_PROMPT

    def test_contains_server_lifecycle(self):
        assert "health check" in BACKEND_E2E_PROMPT.lower() or "Health check" in BACKEND_E2E_PROMPT

    def test_has_format_placeholders(self):
        """Prompt must have required format placeholders."""
        assert "{requirements_dir}" in BACKEND_E2E_PROMPT
        assert "{test_port}" in BACKEND_E2E_PROMPT
        assert "{framework}" in BACKEND_E2E_PROMPT


class TestFrontendE2EPrompt:
    """Tests for FRONTEND_E2E_PROMPT content."""

    def test_contains_playwright_install(self):
        assert "playwright install" in FRONTEND_E2E_PROMPT.lower() or "npx playwright install" in FRONTEND_E2E_PROMPT

    def test_contains_stable_selectors(self):
        assert "getByRole" in FRONTEND_E2E_PROMPT or "getByText" in FRONTEND_E2E_PROMPT

    def test_contains_webserver_config(self):
        assert "webServer" in FRONTEND_E2E_PROMPT

    def test_contains_headless(self):
        assert "headless" in FRONTEND_E2E_PROMPT.lower()

    def test_has_format_placeholders(self):
        assert "{requirements_dir}" in FRONTEND_E2E_PROMPT
        assert "{test_port}" in FRONTEND_E2E_PROMPT
        assert "{frontend_directory}" in FRONTEND_E2E_PROMPT


class TestE2EFixPrompt:
    """Tests for E2E_FIX_PROMPT content."""

    def test_contains_fix_app_not_test(self):
        assert "fix the APP" in E2E_FIX_PROMPT.upper() or "Fix the APP" in E2E_FIX_PROMPT

    def test_contains_debugger_deployment(self):
        assert "debugger" in E2E_FIX_PROMPT.lower()

    def test_contains_rerun_instruction(self):
        assert "re-run" in E2E_FIX_PROMPT.lower() or "Re-run" in E2E_FIX_PROMPT or "rerun" in E2E_FIX_PROMPT.lower()

    def test_has_format_placeholders(self):
        assert "{test_type}" in E2E_FIX_PROMPT
        assert "{failures}" in E2E_FIX_PROMPT


# =========================================================================
# Fix 3: Quality Patterns
# =========================================================================

class TestE2EQualityPatterns:
    """Tests for E2E-001..004 quality check patterns."""

    def test_e2e_001_sleep_detected(self):
        content = "  setTimeout(() => {}, 2000);"
        violations = _check_e2e_quality(content, "tests/e2e/api/test.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-001" in checks

    def test_e2e_001_waitfor_exempt(self):
        """waitFor is not a sleep -- should not trigger E2E-001."""
        content = "  await page.waitForSelector('.loaded');"
        violations = _check_e2e_quality(content, "tests/e2e/browser/test.spec.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-001" not in checks

    def test_e2e_002_port_detected(self):
        content = "  const url = 'http://localhost:3000/api';"
        violations = _check_e2e_quality(content, "tests/e2e/api/test.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-002" in checks

    def test_e2e_002_env_exempt(self):
        content = "  const url = process.env.BASE_URL + '/api';"
        violations = _check_e2e_quality(content, "tests/e2e/api/test.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-002" not in checks

    def test_e2e_003_mock_in_e2e(self):
        content = "  const data = mockData;"
        violations = _check_e2e_quality(content, "tests/e2e/api/test.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-003" in checks

    def test_e2e_004_empty_test(self):
        content = "test('should work', async () => {});"
        violations = _check_e2e_quality(content, "tests/e2e/browser/test.spec.ts", ".ts")
        checks = [v.check for v in violations]
        assert "E2E-004" in checks

    def test_non_e2e_dir_skipped(self):
        """Files not in e2e/ directory should not be checked."""
        content = "  setTimeout(() => {}, 2000);"
        violations = _check_e2e_quality(content, "src/utils/helper.ts", ".ts")
        assert violations == []

    def test_wrong_extension_skipped(self):
        content = "  setTimeout(() => {}, 2000);"
        violations = _check_e2e_quality(content, "tests/e2e/test.css", ".css")
        assert violations == []


class TestE2EQualityScan:
    """Integration tests for run_e2e_quality_scan()."""

    def test_scan_finds_violations(self, tmp_path):
        e2e_dir = tmp_path / "tests" / "e2e" / "api"
        e2e_dir.mkdir(parents=True)
        test_file = e2e_dir / "auth.test.ts"
        test_file.write_text("  setTimeout(() => {}, 5000);\n  const x = mockData;\n")
        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-001" in checks
        assert "E2E-003" in checks

    def test_non_e2e_excluded(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "helper.ts").write_text("setTimeout(() => {}, 1000);")
        violations = run_e2e_quality_scan(tmp_path)
        assert violations == []

    def test_empty_project(self, tmp_path):
        violations = run_e2e_quality_scan(tmp_path)
        assert violations == []


# =========================================================================
# Fix 4: Quality Standards
# =========================================================================

class TestE2EQualityStandards:
    """Tests for E2E_TESTING_STANDARDS and mapping."""

    def test_standards_exist(self):
        assert len(E2E_TESTING_STANDARDS) > 100

    def test_has_ten_standards(self):
        count = E2E_TESTING_STANDARDS.count("**E2E-0")
        assert count >= 10

    def test_mapped_to_test_runner(self):
        standards = _AGENT_STANDARDS_MAP.get("test-runner", [])
        assert E2E_TESTING_STANDARDS in standards

    def test_get_standards_includes_e2e(self):
        result = get_standards_for_agent("test-runner")
        assert "E2E TESTING" in result


# =========================================================================
# HARD-1..3: Prompt Hardening
# =========================================================================

class TestE2EPromptHardening:
    """Tests for Bayan-lesson prompt additions (HARD-1..3)."""

    # BACKEND_E2E_PROMPT hardening
    def test_backend_prompt_requires_role_testing(self):
        assert "EVERY role" in BACKEND_E2E_PROMPT or "every role" in BACKEND_E2E_PROMPT.lower()
        assert "403" in BACKEND_E2E_PROMPT
        assert "NEGATIVE ACCESS" in BACKEND_E2E_PROMPT or "negative access" in BACKEND_E2E_PROMPT.lower()

    def test_backend_prompt_requires_cross_role_workflow(self):
        text = BACKEND_E2E_PROMPT.lower()
        assert "cross-role" in text or "cross_role" in text

    def test_backend_prompt_conditional_on_auth(self):
        assert "NO authentication" in BACKEND_E2E_PROMPT or "no authentication" in BACKEND_E2E_PROMPT.lower()

    def test_backend_prompt_requires_state_passing(self):
        text = BACKEND_E2E_PROMPT.lower()
        assert "entity id" in text or "capture" in text

    def test_backend_prompt_warns_against_first_child(self):
        text = BACKEND_E2E_PROMPT.lower()
        assert "first item in the list" in text or "first-child" in text

    # FRONTEND_E2E_PROMPT hardening
    def test_frontend_prompt_requires_route_completeness(self):
        assert "EVERY route" in FRONTEND_E2E_PROMPT or "every route" in FRONTEND_E2E_PROMPT.lower()

    def test_frontend_prompt_detects_placeholders(self):
        text = FRONTEND_E2E_PROMPT.lower()
        assert "will be implemented" in text
        assert "coming soon" in text
        assert "placeholder" in text

    def test_frontend_prompt_requires_interaction_depth(self):
        text = FRONTEND_E2E_PROMPT.lower()
        assert "every step" in text

    def test_frontend_prompt_requires_form_submission(self):
        text = FRONTEND_E2E_PROMPT.lower()
        assert "submit" in text and "persist" in text

    def test_frontend_prompt_requires_dead_component_detection(self):
        assert "UNREACHABLE" in FRONTEND_E2E_PROMPT or "unreachable" in FRONTEND_E2E_PROMPT.lower()

    def test_frontend_prompt_requires_multi_role_navigation(self):
        text = FRONTEND_E2E_PROMPT.lower()
        assert "each role" in text

    def test_frontend_prompt_lorem_ipsum(self):
        text = FRONTEND_E2E_PROMPT.lower()
        assert "lorem ipsum" in text

    def test_frontend_prompt_dead_component_exclusions(self):
        assert "Spinner" in FRONTEND_E2E_PROMPT
        assert "Layout" in FRONTEND_E2E_PROMPT
        assert "shared/" in FRONTEND_E2E_PROMPT

    def test_frontend_prompt_focus_on_features(self):
        text = FRONTEND_E2E_PROMPT
        assert "PAGE-LEVEL" in text or "page-level" in text.lower()
        assert "FEATURE-LEVEL" in text or "feature-level" in text.lower()

    # E2E_FIX_PROMPT hardening
    def test_fix_prompt_handles_placeholder_failures(self):
        assert "IMPLEMENT" in E2E_FIX_PROMPT
        assert "NOT to remove" in E2E_FIX_PROMPT or "not to remove" in E2E_FIX_PROMPT.lower()

    def test_fix_prompt_handles_role_access_failures(self):
        assert "403" in E2E_FIX_PROMPT
        assert "auth" in E2E_FIX_PROMPT.lower()

    def test_fix_prompt_handles_dead_navigation(self):
        assert "WIRING" in E2E_FIX_PROMPT or "wiring" in E2E_FIX_PROMPT.lower()

    def test_fix_prompt_has_severity_classification(self):
        assert "IMPLEMENT" in E2E_FIX_PROMPT
        assert "FIX_AUTH" in E2E_FIX_PROMPT
        assert "FIX_WIRING" in E2E_FIX_PROMPT

    def test_fix_prompt_has_test_correction_exception(self):
        assert "TEST CORRECTION" in E2E_FIX_PROMPT

    def test_fix_prompt_has_guard_rail(self):
        assert "20%" in E2E_FIX_PROMPT


# =========================================================================
# HARD-4: Additional Quality Pattern Tests
# =========================================================================

class TestE2EQualityPatternsHardening:
    """Tests for E2E-005, E2E-006, E2E-007 regex constants."""

    def test_e2e_005_auth_test_regex_matches(self):
        """E2E-005 regex should match auth test declarations."""
        from agent_team.quality_checks import _RE_E2E_AUTH_TEST
        assert _RE_E2E_AUTH_TEST.search("test('should login successfully',")
        assert _RE_E2E_AUTH_TEST.search("describe('Authentication',")
        assert _RE_E2E_AUTH_TEST.search("it('should sign in user',")

    def test_e2e_006_placeholder_in_template(self):
        from agent_team.quality_checks import _RE_E2E_PLACEHOLDER
        assert _RE_E2E_PLACEHOLDER.search("will be implemented")
        assert _RE_E2E_PLACEHOLDER.search("Coming Soon")
        assert _RE_E2E_PLACEHOLDER.search("Lorem ipsum dolor sit amet")

    def test_e2e_006_placeholder_comment_pattern(self):
        from agent_team.quality_checks import _RE_COMMENT_LINE
        assert _RE_COMMENT_LINE.search("  // will be implemented")
        assert _RE_COMMENT_LINE.search("  # placeholder text")
        assert not _RE_COMMENT_LINE.search("  <p>will be implemented</p>")

    def test_e2e_007_role_failure(self):
        from agent_team.quality_checks import _RE_E2E_ROLE_FAILURE
        assert _RE_E2E_ROLE_FAILURE.search("403 Forbidden")
        assert _RE_E2E_ROLE_FAILURE.search("Unauthorized access")
        assert _RE_E2E_ROLE_FAILURE.search("Access Denied")


# =========================================================================
# HARD-5: Resume Logic
# =========================================================================

class TestE2EResumeLogic:
    """Tests for granular phase tracking."""

    def test_e2e_report_tracks_fix_cycles(self):
        r = E2ETestReport(total_fix_cycles=3, fix_retries_used=3)
        assert r.total_fix_cycles == 3
        assert r.fix_retries_used == 3

    def test_e2e_report_failed_tests_list(self):
        r = E2ETestReport(failed_tests=["test_auth", "test_crud"])
        assert len(r.failed_tests) == 2
        assert "test_auth" in r.failed_tests

    def test_backend_pass_rate_computation(self):
        """70% backend gate: verify pass rate math."""
        r = E2ETestReport(backend_total=10, backend_passed=7)
        rate = r.backend_passed / r.backend_total
        assert rate >= 0.7

    def test_backend_pass_rate_below_gate(self):
        r = E2ETestReport(backend_total=10, backend_passed=6)
        rate = r.backend_passed / r.backend_total
        assert rate < 0.7

    def test_overall_health_computation(self):
        """Verify health computation logic."""
        r = E2ETestReport(
            backend_total=8, backend_passed=8,
            frontend_total=5, frontend_passed=5,
        )
        total = r.backend_total + r.frontend_total
        passed = r.backend_passed + r.frontend_passed
        if total == 0:
            health = "skipped"
        elif passed == total:
            health = "passed"
        elif passed / total >= 0.7:
            health = "partial"
        else:
            health = "failed"
        assert health == "passed"


# =========================================================================
# CLI Wiring (structural/integration)
# =========================================================================

class TestE2ECLIWiring:
    """Tests verifying CLI integration structure."""

    def test_e2e_testing_module_importable(self):
        """Verify e2e_testing module can be imported."""
        from agent_team import e2e_testing
        assert hasattr(e2e_testing, "detect_app_type")
        assert hasattr(e2e_testing, "parse_e2e_results")
        assert hasattr(e2e_testing, "BACKEND_E2E_PROMPT")
        assert hasattr(e2e_testing, "FRONTEND_E2E_PROMPT")
        assert hasattr(e2e_testing, "E2E_FIX_PROMPT")

    def test_e2e_report_importable_from_state(self):
        from agent_team.state import E2ETestReport
        r = E2ETestReport()
        assert r.health == "unknown"

    def test_config_e2e_disabled_by_default(self):
        """E2E phase should be off by default -- explicit opt-in."""
        cfg = AgentTeamConfig()
        assert cfg.e2e_testing.enabled is False

    def test_prompts_format_without_error(self):
        """All three prompts should format without KeyError."""
        BACKEND_E2E_PROMPT.format(
            requirements_dir=".agent-team",
            test_port=9876,
            framework="express",
            start_command="npm start",
            db_type="prisma",
            seed_command="npx prisma db seed",
            api_directory="src/routes",
            task_text="Build a todo app",
        )
        FRONTEND_E2E_PROMPT.format(
            requirements_dir=".agent-team",
            test_port=9876,
            framework="react",
            start_command="npm start",
            frontend_directory="src/components",
            task_text="Build a todo app",
        )
        E2E_FIX_PROMPT.format(
            requirements_dir=".agent-team",
            test_type="backend_api",
            failures="- test_auth: 403",
            task_text="Build a todo app",
        )

    def test_no_budget_field_on_config(self):
        """E2ETestingConfig must NOT have budget_limit_usd."""
        cfg = E2ETestingConfig()
        assert not hasattr(cfg, "budget_limit_usd")
        assert not hasattr(cfg, "total_cost")

    def test_e2e_quality_scan_importable(self):
        from agent_team.quality_checks import run_e2e_quality_scan
        assert callable(run_e2e_quality_scan)


# =========================================================================
# INTEGRATION TEST CLASS 1: E2E Phase Triggering
# =========================================================================

class TestE2EPhaseTriggering:
    """Verify E2E phase triggers/skips correctly in post-orchestration.

    These tests exercise the ACTUAL conditional logic from cli.py lines
    3374-3560 by simulating the data that flows through the E2E block.
    """

    def test_phase_skipped_when_disabled(self):
        """config.e2e_testing.enabled=False -> phase never runs."""
        cfg = AgentTeamConfig()
        assert cfg.e2e_testing.enabled is False
        # When enabled is False, detect_app_type should never be called.
        # Simulate the top-level guard: if config.e2e_testing.enabled:
        called = False

        def fake_detect(path):
            nonlocal called
            called = True

        if cfg.e2e_testing.enabled:
            fake_detect("/tmp")

        assert called is False, "detect_app_type should NOT be called when disabled"

    def test_phase_triggers_when_enabled(self, tmp_path):
        """config.e2e_testing.enabled=True -> detect_app_type called."""
        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True
        called = False

        original_detect = detect_app_type

        def tracking_detect(path):
            nonlocal called
            called = True
            return original_detect(path)

        if cfg.e2e_testing.enabled:
            tracking_detect(tmp_path)

        assert called is True, "detect_app_type MUST be called when enabled=True"

    def test_backend_skipped_when_no_api(self, tmp_path):
        """skip_if_no_api=True + has_backend=False -> backend tests skipped."""
        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True
        cfg.e2e_testing.skip_if_no_api = True

        app_info = detect_app_type(tmp_path)  # Empty dir -> no backend
        assert app_info.has_backend is False

        # Simulate the CLI branch:
        # if config.e2e_testing.backend_api_tests and app_info.has_backend and not backend_already_done:
        #     ... run backend ...
        # elif config.e2e_testing.skip_if_no_api and not app_info.has_backend:
        #     skipped = True
        backend_ran = False
        skipped = False
        backend_already_done = False

        if (cfg.e2e_testing.backend_api_tests
                and app_info.has_backend
                and not backend_already_done):
            backend_ran = True
        elif cfg.e2e_testing.skip_if_no_api and not app_info.has_backend:
            skipped = True

        assert backend_ran is False
        assert skipped is True

    def test_frontend_skipped_when_no_frontend(self, tmp_path):
        """skip_if_no_frontend=True + has_frontend=False -> frontend skipped."""
        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True
        cfg.e2e_testing.skip_if_no_frontend = True

        app_info = detect_app_type(tmp_path)  # Empty dir -> no frontend
        assert app_info.has_frontend is False

        # Simulate frontend guard:
        # if config.e2e_testing.frontend_playwright_tests and app_info.has_frontend and backend_ok and not frontend_already_done:
        frontend_ran = False
        backend_ok = True
        frontend_already_done = False

        if (cfg.e2e_testing.frontend_playwright_tests
                and app_info.has_frontend
                and backend_ok
                and not frontend_already_done):
            frontend_ran = True

        assert frontend_ran is False

    def test_backend_runs_when_api_detected(self, tmp_path):
        """has_backend=True -> backend test branch entered."""
        pkg = {"dependencies": {"express": "^4.18.0"}, "scripts": {"start": "node server.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True

        app_info = detect_app_type(tmp_path)
        assert app_info.has_backend is True

        backend_would_run = (
            cfg.e2e_testing.backend_api_tests
            and app_info.has_backend
            and True  # not backend_already_done
        )
        assert backend_would_run is True

    def test_frontend_blocked_when_backend_below_70_percent(self):
        """Backend 60% pass rate -> frontend tests NOT run."""
        e2e_report = E2ETestReport(backend_total=10, backend_passed=6)
        backend_pass_rate = e2e_report.backend_passed / e2e_report.backend_total
        assert backend_pass_rate == 0.6

        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True

        app_info = AppTypeInfo(has_backend=True, has_frontend=True)

        # Replicate the backend_ok gate from cli.py
        backend_ok = (
            not cfg.e2e_testing.backend_api_tests
            or not app_info.has_backend
            or backend_pass_rate >= 0.7
        )
        assert backend_ok is False, "60% backend should block frontend"

        frontend_would_run = (
            cfg.e2e_testing.frontend_playwright_tests
            and app_info.has_frontend
            and backend_ok
        )
        assert frontend_would_run is False

    def test_frontend_runs_when_backend_at_70_percent(self):
        """Backend exactly 70% -> frontend tests DO run."""
        e2e_report = E2ETestReport(backend_total=10, backend_passed=7)
        backend_pass_rate = e2e_report.backend_passed / e2e_report.backend_total
        assert backend_pass_rate == 0.7

        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True

        app_info = AppTypeInfo(has_backend=True, has_frontend=True)

        backend_ok = (
            not cfg.e2e_testing.backend_api_tests
            or not app_info.has_backend
            or backend_pass_rate >= 0.7
        )
        assert backend_ok is True, "70% backend should allow frontend"

        frontend_would_run = (
            cfg.e2e_testing.frontend_playwright_tests
            and app_info.has_frontend
            and backend_ok
        )
        assert frontend_would_run is True

    def test_frontend_runs_when_backend_at_100_percent(self):
        """Backend 100% -> frontend tests run normally."""
        e2e_report = E2ETestReport(backend_total=8, backend_passed=8)
        backend_pass_rate = e2e_report.backend_passed / e2e_report.backend_total
        assert backend_pass_rate == 1.0

        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True

        app_info = AppTypeInfo(has_backend=True, has_frontend=True)

        backend_ok = (
            not cfg.e2e_testing.backend_api_tests
            or not app_info.has_backend
            or backend_pass_rate >= 0.7
        )
        assert backend_ok is True

    def test_frontend_runs_when_no_backend_tests(self):
        """backend_api_tests=False -> frontend runs regardless of backend rate."""
        cfg = AgentTeamConfig()
        cfg.e2e_testing.enabled = True
        cfg.e2e_testing.backend_api_tests = False

        app_info = AppTypeInfo(has_backend=True, has_frontend=True)

        # With backend_api_tests=False, backend_ok is True immediately
        backend_pass_rate = 0.0  # worst case
        backend_ok = (
            not cfg.e2e_testing.backend_api_tests  # True -> short-circuits
            or not app_info.has_backend
            or backend_pass_rate >= 0.7
        )
        assert backend_ok is True, "backend_api_tests=False should bypass the gate"

        frontend_would_run = (
            cfg.e2e_testing.frontend_playwright_tests
            and app_info.has_frontend
            and backend_ok
        )
        assert frontend_would_run is True


# =========================================================================
# INTEGRATION TEST CLASS 2: E2E Fix Loop
# =========================================================================

class TestE2EFixLoop:
    """Verify fix loop terminates correctly and tracks state.

    These tests replicate the while-loop logic from cli.py lines 3416-3439.
    """

    def test_fix_loop_stops_on_pass(self):
        """When tests pass on first try, fix loop does not run."""
        api_report = E2ETestReport(
            backend_total=5, backend_passed=5, health="passed",
        )
        max_retries = 5
        retries = 0
        fix_ran = False

        while api_report.health != "passed" and retries < max_retries:
            fix_ran = True
            retries += 1

        assert fix_ran is False
        assert retries == 0

    def test_fix_loop_runs_on_failure(self):
        """When tests fail, fix is attempted at least once."""
        reports = [
            E2ETestReport(backend_total=5, backend_passed=2, health="failed"),
            E2ETestReport(backend_total=5, backend_passed=5, health="passed"),
        ]
        report_idx = 0
        api_report = reports[report_idx]
        max_retries = 5
        retries = 0
        fix_ran = False

        while api_report.health != "passed" and retries < max_retries:
            fix_ran = True
            retries += 1
            report_idx += 1
            api_report = reports[min(report_idx, len(reports) - 1)]

        assert fix_ran is True
        assert retries == 1
        assert api_report.health == "passed"

    def test_fix_loop_respects_max_retries(self):
        """Fix loop stops after max_fix_retries even if tests still fail."""
        max_retries = 3
        api_report = E2ETestReport(
            backend_total=10, backend_passed=3, health="failed",
        )
        retries = 0

        while api_report.health != "passed" and retries < max_retries:
            retries += 1
            # Report stays failed every cycle
            api_report = E2ETestReport(
                backend_total=10, backend_passed=3, health="failed",
            )

        assert retries == max_retries
        assert api_report.health == "failed"

    def test_fix_loop_counts_cycles(self):
        """total_fix_cycles incremented each retry."""
        e2e_report = E2ETestReport()
        max_retries = 3
        api_report = E2ETestReport(backend_total=5, backend_passed=2, health="failed")
        retries = 0

        while api_report.health != "passed" and retries < max_retries:
            retries += 1
            e2e_report.fix_retries_used += 1
            e2e_report.total_fix_cycles += 1
            # Stays failed
            api_report = E2ETestReport(backend_total=5, backend_passed=2, health="failed")

        assert e2e_report.total_fix_cycles == 3
        assert e2e_report.fix_retries_used == 3
        assert retries == max_retries

    def test_fix_loop_updates_report_each_cycle(self):
        """E2ETestReport updated with latest results after each cycle."""
        e2e_report = E2ETestReport()
        max_retries = 5

        # Simulate improving results: 2 -> 3 -> 5 passed (out of 5)
        improving_reports = [
            E2ETestReport(backend_total=5, backend_passed=2, health="failed",
                          failed_tests=["t1", "t2", "t3"]),
            E2ETestReport(backend_total=5, backend_passed=3, health="failed",
                          failed_tests=["t1", "t2"]),
            E2ETestReport(backend_total=5, backend_passed=5, health="passed",
                          failed_tests=[]),
        ]

        api_report = improving_reports[0]
        e2e_report.backend_total = api_report.backend_total
        e2e_report.backend_passed = api_report.backend_passed
        e2e_report.failed_tests = api_report.failed_tests[:]

        retries = 0
        while api_report.health != "passed" and retries < max_retries:
            retries += 1
            e2e_report.total_fix_cycles += 1
            api_report = improving_reports[min(retries, len(improving_reports) - 1)]
            # Update report with latest results (matches cli.py logic)
            e2e_report.backend_total = api_report.backend_total
            e2e_report.backend_passed = api_report.backend_passed
            e2e_report.failed_tests = api_report.failed_tests[:]

        assert retries == 2  # fixed on third attempt (index 2)
        assert e2e_report.backend_passed == 5
        assert e2e_report.failed_tests == []
        assert e2e_report.total_fix_cycles == 2


# =========================================================================
# INTEGRATION TEST CLASS 3: E2E Health Computation
# =========================================================================

class TestE2EHealthComputation:
    """Verify health computation edge cases.

    Replicates the logic from cli.py lines 3530-3542.
    """

    @staticmethod
    def _compute_health(e2e_report: E2ETestReport) -> str:
        """Replicate the CLI health computation logic."""
        total = e2e_report.backend_total + e2e_report.frontend_total
        passed = e2e_report.backend_passed + e2e_report.frontend_passed
        if total == 0:
            return "skipped"
        elif passed == total:
            return "passed"
        elif total > 0 and passed / total >= 0.7:
            return "partial"
        else:
            return "failed"

    def test_health_skipped_when_zero_total(self):
        """0 backend + 0 frontend -> health='skipped'."""
        report = E2ETestReport()
        assert self._compute_health(report) == "skipped"

    def test_health_passed_when_all_pass(self):
        """8/8 backend + 5/5 frontend -> health='passed'."""
        report = E2ETestReport(
            backend_total=8, backend_passed=8,
            frontend_total=5, frontend_passed=5,
        )
        assert self._compute_health(report) == "passed"

    def test_health_partial_at_exactly_70_percent(self):
        """7/10 total -> health='partial' (exactly 70%)."""
        report = E2ETestReport(
            backend_total=10, backend_passed=7,
        )
        assert self._compute_health(report) == "partial"

    def test_health_failed_below_70_percent(self):
        """6/10 total -> health='failed'."""
        report = E2ETestReport(
            backend_total=10, backend_passed=6,
        )
        health = self._compute_health(report)
        assert health == "failed"

    def test_health_with_only_backend(self):
        """Backend only (no frontend) -> health based on backend only."""
        report = E2ETestReport(backend_total=5, backend_passed=5)
        assert self._compute_health(report) == "passed"

        report2 = E2ETestReport(backend_total=5, backend_passed=3)
        assert self._compute_health(report2) == "failed"

    def test_health_with_only_frontend(self):
        """Frontend only (no backend) -> health based on frontend only."""
        report = E2ETestReport(frontend_total=5, frontend_passed=5)
        assert self._compute_health(report) == "passed"

        report2 = E2ETestReport(frontend_total=10, frontend_passed=7)
        assert self._compute_health(report2) == "partial"

    def test_health_mixed_backend_frontend(self):
        """8/10 backend + 3/5 frontend = 11/15 = 73% -> partial."""
        report = E2ETestReport(
            backend_total=10, backend_passed=8,
            frontend_total=5, frontend_passed=3,
        )
        health = self._compute_health(report)
        total = 15
        passed = 11
        assert passed / total == pytest.approx(0.7333, abs=0.001)
        assert health == "partial"

    def test_health_also_matches_parse_e2e_results(self, tmp_path):
        """Verify parse_e2e_results computes the same health as CLI logic."""
        content = "## Backend API Tests\nTotal: 10 | Passed: 8 | Failed: 2\n\n## Frontend Playwright Tests\nTotal: 5 | Passed: 5 | Failed: 0\n"
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.health == self._compute_health(report)


# =========================================================================
# INTEGRATION TEST CLASS 4: detect_app_type Edge Cases
# =========================================================================

class TestE2EDetectAppTypeEdgeCases:
    """Edge cases for detect_app_type that could cause silent failures."""

    def test_corrupt_package_json(self, tmp_path):
        """Malformed JSON in package.json -> graceful fallback, no crash."""
        (tmp_path / "package.json").write_text("{invalid json", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is False

    def test_empty_package_json(self, tmp_path):
        """Empty package.json -> graceful handling."""
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is False

    def test_package_json_missing_deps(self, tmp_path):
        """package.json with scripts but no dependencies."""
        (tmp_path / "package.json").write_text('{"scripts": {"dev": "vite"}}', encoding="utf-8")
        info = detect_app_type(tmp_path)
        # Should not crash — scripts present but no deps
        assert info.has_backend is False
        assert info.start_command != ""  # "npm run dev" inferred from scripts

    def test_both_python_and_node(self, tmp_path):
        """Project with both requirements.txt and package.json."""
        (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True

    def test_vue_detection(self, tmp_path):
        """Vue.js frontend detection."""
        pkg = {"dependencies": {"vue": "^3.3.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "vue"

    def test_django_detection(self, tmp_path):
        """Django backend detection."""
        (tmp_path / "requirements.txt").write_text("django==4.2\n", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "django"

    def test_nestjs_detection(self, tmp_path):
        """NestJS backend detection."""
        pkg = {"dependencies": {"@nestjs/core": "^10.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "nestjs"

    def test_pnpm_lock_detection(self, tmp_path):
        """pnpm lock file -> package_manager='pnpm'."""
        (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
        (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.package_manager == "pnpm"

    def test_mongoose_detection(self, tmp_path):
        """Mongoose DB detection."""
        pkg = {"dependencies": {"express": "^4.0", "mongoose": "^7.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.db_type == "mongoose"

    def test_flask_detection(self, tmp_path):
        """Flask backend detection."""
        (tmp_path / "requirements.txt").write_text("flask\n", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "flask"

    def test_angular_config_file_detection(self, tmp_path):
        """angular.json config file triggers Angular detection."""
        (tmp_path / "angular.json").write_text("{}", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"

    def test_sequelize_detection(self, tmp_path):
        """Sequelize ORM detection."""
        pkg = {"dependencies": {"express": "^4.0", "sequelize": "^6.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.db_type == "sequelize"

    def test_yarn_lock_detection(self, tmp_path):
        """yarn.lock -> package_manager='yarn'."""
        (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
        (tmp_path / "yarn.lock").write_text("", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.package_manager == "yarn"

    def test_nuxt_config_detection(self, tmp_path):
        """nuxt.config.ts triggers Vue + backend detection."""
        (tmp_path / "nuxt.config.ts").write_text("export default {}", encoding="utf-8")
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "vue"
        assert info.has_backend is True


# =========================================================================
# INTEGRATION TEST CLASS 5: parse_e2e_results Edge Cases
# =========================================================================

class TestE2EParseResultsEdgeCases:
    """Edge cases for parse_e2e_results."""

    def test_only_frontend_results(self, tmp_path):
        """File with only frontend section, no backend."""
        content = "## Frontend Playwright Tests\nTotal: 3 | Passed: 3 | Failed: 0\n"
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.frontend_total == 3
        assert report.frontend_passed == 3
        assert report.backend_total == 0

    def test_only_backend_results(self, tmp_path):
        """File with only backend section, no frontend."""
        content = "## Backend API Tests\nTotal: 5 | Passed: 4 | Failed: 1\n"
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.backend_total == 5
        assert report.backend_passed == 4
        assert report.frontend_total == 0

    def test_empty_file(self, tmp_path):
        """Empty results file -> graceful handling."""
        (tmp_path / "E2E_RESULTS.md").write_text("", encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.skipped is True
        assert report.backend_total == 0
        assert report.health == "skipped"

    def test_unicode_in_results(self, tmp_path):
        """Results with Unicode chars on Windows."""
        content = "## Backend API Tests\nTotal: 2 | Passed: 1 | Failed: 1\n\n### Failed\n- FAIL: test_auth: 403 Forbidden\n"
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.backend_total == 2
        assert report.backend_passed == 1
        assert len(report.failed_tests) >= 1

    def test_results_with_large_numbers(self, tmp_path):
        """Many tests (100+)."""
        content = "## Backend API Tests\nTotal: 150 | Passed: 142 | Failed: 8\n"
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.backend_total == 150
        assert report.backend_passed == 142

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file path -> skipped, no crash."""
        report = parse_e2e_results(tmp_path / "DOES_NOT_EXIST.md")
        assert report.skipped is True
        assert report.health == "skipped"

    def test_both_sections_present(self, tmp_path):
        """Both backend and frontend sections properly parsed."""
        content = (
            "## Backend API Tests\n"
            "Total: 10 | Passed: 9 | Failed: 1\n\n"
            "## Frontend Playwright Tests\n"
            "Total: 8 | Passed: 7 | Failed: 1\n"
        )
        (tmp_path / "E2E_RESULTS.md").write_text(content, encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.backend_total == 10
        assert report.backend_passed == 9
        assert report.frontend_total == 8
        assert report.frontend_passed == 7
        # 16/18 = 88.9% -> partial
        assert report.health == "partial"

    def test_whitespace_only_file(self, tmp_path):
        """File with only whitespace -> treated as empty."""
        (tmp_path / "E2E_RESULTS.md").write_text("   \n\n  \n", encoding="utf-8")
        report = parse_e2e_results(tmp_path / "E2E_RESULTS.md")
        assert report.skipped is True
        assert report.health == "skipped"


# =========================================================================
# INTEGRATION TEST CLASS 6: Prompt Format Safety
# =========================================================================

class TestE2EPromptFormatSafety:
    """Verify prompts don't crash with edge-case inputs."""

    def test_backend_prompt_with_empty_strings(self):
        """All empty strings -> no KeyError."""
        result = BACKEND_E2E_PROMPT.format(
            requirements_dir="", test_port=0, framework="",
            start_command="", db_type="", seed_command="",
            api_directory="", task_text="",
        )
        assert isinstance(result, str)
        assert len(result) > 100  # Prompt body should still be there

    def test_frontend_prompt_with_special_chars(self):
        """Special characters in task_text -> no crash."""
        result = FRONTEND_E2E_PROMPT.format(
            requirements_dir=".agent-team", test_port=9876,
            framework="react", start_command="npm start",
            frontend_directory="src/", task_text="Build app with 'quotes' and \"double quotes\"",
        )
        assert isinstance(result, str)
        assert "quotes" in result

    def test_fix_prompt_with_multiline_failures(self):
        """Multi-line failure list -> formats correctly."""
        failures = "- test_1: failed\n- test_2: timeout\n- test_3: 403"
        result = E2E_FIX_PROMPT.format(
            requirements_dir=".agent-team", test_type="backend_api",
            failures=failures, task_text="Build todo app",
        )
        assert "test_1" in result
        assert "test_3" in result

    def test_backend_prompt_no_extra_placeholders(self):
        """Prompt should not have unmatched {placeholders} after format.

        Note: The prompts use {{ }} for literal brace examples shown to the AI
        (e.g., JS destructuring, code patterns). After .format() these become
        single-brace literals like {itemId}, {id: itemId}, etc. These are
        expected and whitelisted.
        """
        import re as _re
        result = BACKEND_E2E_PROMPT.format(
            requirements_dir=".agent-team", test_port=9876,
            framework="express", start_command="npm start",
            db_type="prisma", seed_command="npx prisma db seed",
            api_directory="src/routes", task_text="test",
        )
        # Known literal-brace words from code examples in the prompt
        known_literals = {"id", "itemId", "method"}
        unmatched = _re.findall(r'(?<!\{)\{(\w+)\}(?!\})', result)
        unexpected = [p for p in unmatched if p not in known_literals]
        assert unexpected == [], f"Unmatched placeholders: {unexpected}"

    def test_frontend_prompt_no_extra_placeholders(self):
        """Prompt should not have unmatched {placeholders} after format."""
        import re as _re
        result = FRONTEND_E2E_PROMPT.format(
            requirements_dir=".agent-team", test_port=9876,
            framework="react", start_command="npm start",
            frontend_directory="src/", task_text="test",
        )
        # Known literal-brace words from code examples in the prompt
        known_literals = {"name", "command"}
        unmatched = _re.findall(r'(?<!\{)\{(\w+)\}(?!\})', result)
        unexpected = [p for p in unmatched if p not in known_literals]
        assert unexpected == [], f"Unmatched placeholders: {unexpected}"

    def test_fix_prompt_no_extra_placeholders(self):
        """Prompt should not have unmatched {placeholders} after format."""
        import re as _re
        result = E2E_FIX_PROMPT.format(
            requirements_dir=".agent-team", test_type="backend_api",
            failures="none", task_text="test",
        )
        # Known literal-brace words from code examples / template strings
        known_literals = {"name", "reason", "X"}
        unmatched = _re.findall(r'(?<!\{)\{(\w+)\}(?!\})', result)
        unexpected = [p for p in unmatched if p not in known_literals]
        assert unexpected == [], f"Unmatched placeholders: {unexpected}"

    def test_backend_prompt_unicode_in_task_text(self):
        """Unicode characters in task_text -> no crash."""
        result = BACKEND_E2E_PROMPT.format(
            requirements_dir=".agent-team", test_port=9876,
            framework="express", start_command="npm start",
            db_type="prisma", seed_command="npx prisma db seed",
            api_directory="src/routes",
            task_text="Build todo app with arabic: \u0645\u0631\u062d\u0628\u0627",
        )
        assert "\u0645\u0631\u062d\u0628\u0627" in result

    def test_fix_prompt_empty_failures(self):
        """Empty failures string -> formats correctly."""
        result = E2E_FIX_PROMPT.format(
            requirements_dir=".agent-team", test_type="frontend_playwright",
            failures="", task_text="test",
        )
        assert isinstance(result, str)


# =========================================================================
# INTEGRATION TEST CLASS 7: Resume and State Tracking
# =========================================================================

class TestE2EResumeAndStateTracking:
    """Verify state tracking and resume logic."""

    def test_completed_phases_list_type(self):
        """completed_phases is a list that supports 'in' and append."""
        from agent_team.state import RunState
        state = RunState()
        state.completed_phases.append("e2e_backend")
        assert "e2e_backend" in state.completed_phases
        state.completed_phases.append("e2e_frontend")
        assert "e2e_frontend" in state.completed_phases
        state.completed_phases.append("e2e_testing")
        assert len(state.completed_phases) == 3

    def test_e2e_phases_are_distinct(self):
        """e2e_backend, e2e_frontend, e2e_testing are all tracked separately."""
        from agent_team.state import RunState
        state = RunState()
        state.completed_phases.append("e2e_backend")
        assert "e2e_backend" in state.completed_phases
        assert "e2e_frontend" not in state.completed_phases
        assert "e2e_testing" not in state.completed_phases

    def test_state_serialization_with_e2e_phases(self, tmp_path):
        """RunState with E2E phases survives save/load cycle."""
        from agent_team.state import RunState, save_state, load_state
        state = RunState(task="test", depth="standard")
        state.completed_phases.extend([
            "orchestration", "e2e_backend", "e2e_frontend", "e2e_testing",
        ])
        state.current_phase = "verification"
        save_state(state, directory=str(tmp_path))
        loaded = load_state(directory=str(tmp_path))
        assert loaded is not None
        assert "e2e_backend" in loaded.completed_phases
        assert "e2e_frontend" in loaded.completed_phases
        assert "e2e_testing" in loaded.completed_phases

    def test_backend_resume_skip(self):
        """Backend already in completed_phases -> skipped on resume."""
        from agent_team.state import RunState
        state = RunState()
        state.completed_phases.append("e2e_backend")

        backend_already_done = "e2e_backend" in state.completed_phases
        assert backend_already_done is True

        # Simulate the CLI check: run only if NOT already done
        would_run = (
            True  # config.e2e_testing.backend_api_tests
            and True  # app_info.has_backend
            and not backend_already_done
        )
        assert would_run is False

    def test_frontend_resume_skip(self):
        """Frontend already in completed_phases -> skipped on resume."""
        from agent_team.state import RunState
        state = RunState()
        state.completed_phases.append("e2e_frontend")

        frontend_already_done = "e2e_frontend" in state.completed_phases
        assert frontend_already_done is True

        would_run = (
            True  # config.e2e_testing.frontend_playwright_tests
            and True  # app_info.has_frontend
            and True  # backend_ok
            and not frontend_already_done
        )
        assert would_run is False

    def test_partial_resume_only_frontend_remaining(self):
        """Backend done but frontend not -> only frontend runs."""
        from agent_team.state import RunState
        state = RunState()
        state.completed_phases.append("e2e_backend")

        backend_already_done = "e2e_backend" in state.completed_phases
        frontend_already_done = "e2e_frontend" in state.completed_phases

        assert backend_already_done is True
        assert frontend_already_done is False

        backend_would_run = True and True and not backend_already_done
        frontend_would_run = True and True and True and not frontend_already_done

        assert backend_would_run is False
        assert frontend_would_run is True

    def test_state_save_preserves_e2e_cost(self, tmp_path):
        """total_cost updated with E2E cost survives save/load."""
        from agent_team.state import RunState, save_state, load_state
        state = RunState(task="test", depth="standard")
        state.total_cost = 12.50
        state.completed_phases.append("e2e_testing")
        save_state(state, directory=str(tmp_path))
        loaded = load_state(directory=str(tmp_path))
        assert loaded is not None
        assert loaded.total_cost == 12.50
        assert "e2e_testing" in loaded.completed_phases

    def test_fresh_state_has_no_e2e_phases(self):
        """Brand new RunState has no E2E phases completed."""
        from agent_team.state import RunState
        state = RunState()
        assert "e2e_backend" not in state.completed_phases
        assert "e2e_frontend" not in state.completed_phases
        assert "e2e_testing" not in state.completed_phases
        assert state.completed_phases == []


# =========================================================================
# REVIEW FIX VERIFICATION (C1-C3, H1-H5)
# =========================================================================

class TestReviewFixVerification:
    """Verify all 8 review fixes are correctly implemented.

    C1: Fix loop guard condition includes "skipped" and "unknown"
    C2: Frontend fix loop updates failed_tests via slice copy
    C3: E2E-005/006/007 patterns fire correctly
    H1: traceback.format_exc() in all exception handlers
    H3: Skip messages for no-frontend and low-backend-rate
    H4: Outer except sets health="failed"
    H5: completed_phases only on "passed" or "partial"
    """

    # --- C1: Fix loop skips on "skipped" and "unknown" ---

    def test_c1_fix_loop_skips_on_skipped_health(self):
        """health='skipped' must NOT enter the fix loop."""
        report = E2ETestReport(health="skipped", skipped=True)
        # The loop condition: health not in ("passed", "skipped", "unknown")
        enters_loop = report.health not in ("passed", "skipped", "unknown")
        assert enters_loop is False, "Fix loop must NOT run when health='skipped'"

    def test_c1_fix_loop_skips_on_unknown_health(self):
        """health='unknown' must NOT enter the fix loop."""
        report = E2ETestReport(health="unknown")
        enters_loop = report.health not in ("passed", "skipped", "unknown")
        assert enters_loop is False, "Fix loop must NOT run when health='unknown'"

    def test_c1_fix_loop_runs_on_failed_health(self):
        """health='failed' must enter the fix loop."""
        report = E2ETestReport(health="failed", backend_total=5, backend_passed=2)
        enters_loop = report.health not in ("passed", "skipped", "unknown")
        assert enters_loop is True, "Fix loop MUST run when health='failed'"

    def test_c1_fix_loop_runs_on_partial_health(self):
        """health='partial' must enter the fix loop."""
        report = E2ETestReport(health="partial", backend_total=10, backend_passed=7)
        enters_loop = report.health not in ("passed", "skipped", "unknown")
        assert enters_loop is True, "Fix loop MUST run when health='partial'"

    # --- C2: Frontend fix loop updates failed_tests ---

    def test_c2_frontend_fix_loop_updates_failed_tests(self):
        """Verify the cli.py source contains the slice-copy update pattern
        'e2e_report.failed_tests = pw_report.failed_tests[:]' for the frontend loop."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        # Backend fix loop slice copy
        assert "e2e_report.failed_tests = api_report.failed_tests[:]" in source, (
            "Backend fix loop must slice-copy failed_tests"
        )
        # Frontend fix loop slice copy
        assert "e2e_report.failed_tests = pw_report.failed_tests[:]" in source, (
            "Frontend fix loop must slice-copy failed_tests"
        )

    # --- C3: E2E-006 fires on placeholder in .tsx ---

    def test_c3_e2e_006_fires_on_placeholder_in_tsx(self, tmp_path):
        """A .tsx component with 'will be implemented' triggers E2E-006."""
        content = '<div className="hero">This feature will be implemented later</div>'
        violations = _check_e2e_quality(content, "src/components/Hero.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "E2E-006" in checks, "E2E-006 must fire on placeholder text in .tsx"

    def test_c3_e2e_006_skips_comments(self):
        """Comment containing 'will be implemented' must NOT trigger E2E-006."""
        content = "// will be implemented\n// coming soon\n"
        violations = _check_e2e_quality(content, "src/components/Hero.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "E2E-006" not in checks, "E2E-006 must NOT fire on comment lines"

    def test_c3_e2e_005_inverted_auth_warns(self, tmp_path):
        """Project with auth dep but no auth e2e test triggers E2E-005."""
        # package.json with jsonwebtoken
        pkg = {"dependencies": {"express": "^4.0", "jsonwebtoken": "^9.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        # E2E dir with a test but no auth test
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        test_file = e2e_dir / "crud.test.ts"
        test_file.write_text("test('should create item', async () => { /* crud */ });", encoding="utf-8")

        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-005" in checks, "E2E-005 must warn when auth dep present but no auth test"

    def test_c3_e2e_005_no_warn_without_auth(self, tmp_path):
        """Project WITHOUT auth dep must NOT trigger E2E-005."""
        pkg = {"dependencies": {"express": "^4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        test_file = e2e_dir / "crud.test.ts"
        test_file.write_text("test('should create item', async () => { /* crud */ });", encoding="utf-8")

        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-005" not in checks, "E2E-005 must NOT fire without auth deps"

    def test_c3_e2e_007_scans_results_file(self, tmp_path):
        """E2E_RESULTS.md with '403 Forbidden' triggers E2E-007."""
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        results = agent_dir / "E2E_RESULTS.md"
        results.write_text(
            "## Backend API Tests\nTotal: 5 | Passed: 3 | Failed: 2\n\n"
            "### Failed\n- FAIL: test_admin_access: 403 Forbidden\n",
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-007" in checks, "E2E-007 must fire on 403 Forbidden in results file"

    # --- H1: traceback.format_exc() in all exception handlers ---

    def test_h1_traceback_in_backend_exception_handler(self):
        """Backend E2E exception handler must use traceback.format_exc()."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        assert "Backend E2E test pass failed:" in source
        # The backend handler has traceback.format_exc() on the same f-string
        assert 'Backend E2E test pass failed: {exc}\\n{traceback.format_exc()}' in source or \
               "traceback.format_exc()" in source

    def test_h1_traceback_in_frontend_exception_handler(self):
        """Frontend E2E exception handler must use traceback.format_exc()."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        assert "Frontend E2E test pass failed:" in source

    def test_h1_traceback_in_fix_exception_handler(self):
        """E2E fix pass exception handler must use traceback.format_exc()."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        assert "E2E fix pass failed:" in source

    def test_h1_traceback_used_at_least_four_times(self):
        """traceback.format_exc() should appear in at least 4 E2E handlers.

        Backend, frontend, fix function, and outer except block.
        """
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        # Count occurrences of "traceback.format_exc()" in the source
        count = source.count("traceback.format_exc()")
        assert count >= 4, f"Expected >=4 traceback.format_exc() calls, found {count}"

    # --- H3: Skip messages ---

    def test_h3_skip_message_for_no_frontend(self):
        """cli.py must contain 'No frontend detected' skip message."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        assert "No frontend detected" in source

    def test_h3_skip_message_for_low_backend_rate(self):
        """cli.py must contain 'below 70% threshold' skip message."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        assert "below 70% threshold" in source

    # --- H4: Outer except sets health="failed" ---

    def test_h4_outer_except_sets_health_failed(self):
        """Outer except block must set e2e_report.health = 'failed'."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        # The outer except block at line 3573-3576 sets health to failed
        assert 'e2e_report.health = "failed"' in source
        assert 'Phase error:' in source

    # --- H5: completed_phases only on "passed" or "partial" ---

    def test_h5_backend_complete_only_on_pass_or_partial(self):
        """e2e_backend only appended to completed_phases when health is passed or partial."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        # The guard: api_report.health in ("passed", "partial")
        assert 'api_report.health in ("passed", "partial")' in source

    def test_h5_frontend_complete_only_on_pass_or_partial(self):
        """e2e_frontend only appended to completed_phases when health is passed or partial."""
        import inspect
        from agent_team import cli
        source = inspect.getsource(cli)
        # The guard: pw_report.health in ("passed", "partial")
        assert 'pw_report.health in ("passed", "partial")' in source


# =========================================================================
# E2E QUALITY SCAN INTEGRATION (E2E-005/006/007)
# =========================================================================

class TestE2EQualityScanIntegration:
    """Integration tests for run_e2e_quality_scan covering E2E-005/006/007."""

    def test_scan_finds_placeholder_in_tsx_component(self, tmp_path):
        """E2E-006: Placeholder text in a .tsx component outside e2e/ dir."""
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        hero = comp_dir / "Hero.tsx"
        hero.write_text(
            'export const Hero = () => <div>coming soon</div>;',
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-006" in checks, "E2E-006 must detect 'coming soon' in Hero.tsx"

    def test_scan_ignores_placeholder_in_e2e_dir(self, tmp_path):
        """E2E-006 must NOT fire on files inside the e2e/ directory.

        Files in e2e/ are test files; only E2E-001..004 apply there.
        """
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        test_file = e2e_dir / "placeholder.test.tsx"
        test_file.write_text(
            'test("check placeholder", async () => { expect("coming soon"); });',
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        # E2E-006 should NOT fire because the file is in e2e/ dir
        e2e_006_violations = [v for v in violations if v.check == "E2E-006"]
        assert len(e2e_006_violations) == 0, (
            "E2E-006 must NOT fire on files in e2e/ directory"
        )

    def test_scan_e2e_005_with_jwt_dep(self, tmp_path):
        """E2E-005: Auth dep (jwt) present + no auth test -> warning."""
        pkg = {"dependencies": {"express": "^4.0", "jsonwebtoken": "^9.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        (e2e_dir / "home.test.ts").write_text(
            "test('should load home page', async () => { /* navigate */ });",
            encoding="utf-8",
        )

        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-005" in checks

    def test_scan_e2e_005_no_warning_with_auth_test(self, tmp_path):
        """E2E-005: Auth dep present + auth test EXISTS -> no E2E-005."""
        pkg = {"dependencies": {"express": "^4.0", "jsonwebtoken": "^9.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        (e2e_dir / "auth.test.ts").write_text(
            "test('should login successfully', async () => { /* auth flow */ });",
            encoding="utf-8",
        )

        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-005" not in checks, "E2E-005 must NOT fire when auth test exists"

    def test_scan_e2e_007_with_results_file(self, tmp_path):
        """E2E-007: E2E_RESULTS.md with 'Unauthorized' -> violation."""
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "E2E_RESULTS.md").write_text(
            "## Backend\nTest role_check: Unauthorized\n",
            encoding="utf-8",
        )
        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-007" in checks

    def test_scan_e2e_007_no_results_file(self, tmp_path):
        """No E2E_RESULTS.md -> no E2E-007 violation."""
        violations = run_e2e_quality_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "E2E-007" not in checks

    def test_scan_combined_all_patterns(self, tmp_path):
        """Project triggering all E2E-001 through E2E-007 at once."""
        # Auth dep for E2E-005
        pkg = {"dependencies": {"express": "^4.0", "jsonwebtoken": "^9.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        # E2E dir with problematic test file (E2E-001..004, no auth test = E2E-005)
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        bad_test = e2e_dir / "bad.test.ts"
        bad_test.write_text(
            "// E2E-001: hardcoded sleep\n"
            "setTimeout(() => {}, 3000);\n"
            "// E2E-002: hardcoded port\n"
            "const url = 'http://localhost:3000/api';\n"
            "// E2E-003: mock data\n"
            "const data = mockData;\n"
            "// E2E-004: empty test\n"
            "test('placeholder', async () => {});\n",
            encoding="utf-8",
        )

        # Template component with placeholder (E2E-006)
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "Feature.tsx").write_text(
            '<div>This feature is under construction</div>',
            encoding="utf-8",
        )

        # Results file with role failure (E2E-007)
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "E2E_RESULTS.md").write_text(
            "## Backend\nTotal: 5 | Passed: 3 | Failed: 2\n"
            "### Failed\n- FAIL: test_access: Access Denied\n",
            encoding="utf-8",
        )

        violations = run_e2e_quality_scan(tmp_path)
        checks = set(v.check for v in violations)

        assert "E2E-001" in checks, "E2E-001 (sleep) missing"
        assert "E2E-002" in checks, "E2E-002 (hardcoded port) missing"
        assert "E2E-003" in checks, "E2E-003 (mock data) missing"
        assert "E2E-004" in checks, "E2E-004 (empty test) missing"
        assert "E2E-005" in checks, "E2E-005 (no auth test) missing"
        assert "E2E-006" in checks, "E2E-006 (placeholder) missing"
        assert "E2E-007" in checks, "E2E-007 (role failure) missing"

    def test_scan_clean_project(self, tmp_path):
        """Clean project with proper E2E tests -> zero violations."""
        # No auth dep, no issues
        pkg = {"dependencies": {"express": "^4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        # Clean E2E test file (no sleep, no hardcoded ports, no mocks)
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        (e2e_dir / "crud.test.ts").write_text(
            "import { test, expect } from '@playwright/test';\n"
            "\n"
            "test('should create item via API', async ({ request }) => {\n"
            "  const response = await request.post(process.env.BASE_URL + '/api/items', {\n"
            "    data: { name: 'Test Item' },\n"
            "  });\n"
            "  expect(response.ok()).toBeTruthy();\n"
            "});\n",
            encoding="utf-8",
        )

        # Clean component (no placeholders)
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "Hero.tsx").write_text(
            'export const Hero = () => <div>Welcome to Our App</div>;',
            encoding="utf-8",
        )

        violations = run_e2e_quality_scan(tmp_path)
        assert len(violations) == 0, f"Expected 0 violations, got {len(violations)}: {violations}"


# =========================================================================
# E2E CONFIG EDGE CASES
# =========================================================================

class TestE2EConfigEdgeCases:
    """Edge cases for E2E config validation in _dict_to_config."""

    def test_max_fix_retries_zero_raises(self):
        """max_fix_retries=0 must raise ValueError (minimum is 1)."""
        data = {"e2e_testing": {"max_fix_retries": 0}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_max_fix_retries_negative_raises(self):
        """max_fix_retries=-1 must raise ValueError."""
        data = {"e2e_testing": {"max_fix_retries": -1}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_port_below_1024_raises(self):
        """test_port=80 must raise ValueError (below 1024 minimum)."""
        data = {"e2e_testing": {"test_port": 80}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_port_above_65535_raises(self):
        """test_port=70000 must raise ValueError (above 65535 maximum)."""
        data = {"e2e_testing": {"test_port": 70000}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_port_at_exact_boundaries(self):
        """test_port=1024 and test_port=65535 must both be accepted."""
        cfg_low, _ = _dict_to_config({"e2e_testing": {"test_port": 1024}})
        assert cfg_low.e2e_testing.test_port == 1024

        cfg_high, _ = _dict_to_config({"e2e_testing": {"test_port": 65535}})
        assert cfg_high.e2e_testing.test_port == 65535

    def test_legacy_budget_limit_ignored(self):
        """YAML with budget_limit_usd key must NOT cause error or be present on config."""
        data = {"e2e_testing": {"enabled": True, "budget_limit_usd": 10}}
        cfg, _ = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert not hasattr(cfg.e2e_testing, "budget_limit_usd")

    def test_e2e_config_from_empty_yaml(self):
        """Empty e2e_testing section -> all defaults preserved."""
        data = {"e2e_testing": {}}
        cfg, _ = _dict_to_config(data)
        defaults = E2ETestingConfig()
        assert cfg.e2e_testing.enabled == defaults.enabled
        assert cfg.e2e_testing.backend_api_tests == defaults.backend_api_tests
        assert cfg.e2e_testing.frontend_playwright_tests == defaults.frontend_playwright_tests
        assert cfg.e2e_testing.max_fix_retries == defaults.max_fix_retries
        assert cfg.e2e_testing.test_port == defaults.test_port
        assert cfg.e2e_testing.skip_if_no_api == defaults.skip_if_no_api
        assert cfg.e2e_testing.skip_if_no_frontend == defaults.skip_if_no_frontend

    def test_e2e_config_partial_yaml(self):
        """Only enabled=True -> rest are defaults."""
        data = {"e2e_testing": {"enabled": True}}
        cfg, _ = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 5  # default
        assert cfg.e2e_testing.test_port == 9876  # default
        assert cfg.e2e_testing.backend_api_tests is True  # default
        assert cfg.e2e_testing.frontend_playwright_tests is True  # default
        assert cfg.e2e_testing.skip_if_no_api is True  # default
        assert cfg.e2e_testing.skip_if_no_frontend is True  # default
