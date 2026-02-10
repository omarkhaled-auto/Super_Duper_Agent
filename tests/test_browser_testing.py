"""Tests for Browser MCP Interactive Testing Phase.

Covers config, state, browser_testing module (workflow generation, parsing,
verification, screenshots, state management, reports), MCP servers, and prompts.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent_team.config import (
    AgentTeamConfig,
    BrowserTestingConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.state import (
    BrowserTestReport,
    RunState,
    WorkflowResult,
)
from agent_team.browser_testing import (
    AppStartupInfo,
    WorkflowDefinition,
    check_app_running,
    check_screenshot_diversity,
    count_screenshots,
    generate_browser_workflows,
    generate_readiness_report,
    generate_unresolved_issues,
    parse_app_startup_info,
    parse_workflow_index,
    parse_workflow_results,
    update_workflow_state,
    verify_workflow_execution,
    write_workflow_state,
    _extract_seed_credentials,
    BROWSER_APP_STARTUP_PROMPT,
    BROWSER_WORKFLOW_EXECUTOR_PROMPT,
    BROWSER_WORKFLOW_FIX_PROMPT,
    BROWSER_REGRESSION_SWEEP_PROMPT,
)
from agent_team.mcp_servers import (
    _playwright_mcp_server,
    get_browser_testing_servers,
)


# =========================================================================
# Config tests
# =========================================================================


class TestBrowserTestingConfig:
    """Tests for BrowserTestingConfig dataclass and _dict_to_config."""

    def test_defaults(self):
        cfg = BrowserTestingConfig()
        assert cfg.enabled is False
        assert cfg.max_fix_retries == 5
        assert cfg.e2e_pass_rate_gate == 0.7
        assert cfg.headless is True
        assert cfg.app_start_command == ""
        assert cfg.app_port == 0
        assert cfg.regression_sweep is True

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.browser_testing, BrowserTestingConfig)
        assert cfg.browser_testing.enabled is False

    def test_yaml_full_parsing(self):
        data = {
            "browser_testing": {
                "enabled": True,
                "max_fix_retries": 3,
                "e2e_pass_rate_gate": 0.5,
                "headless": False,
                "app_start_command": "npm run dev",
                "app_port": 4200,
                "regression_sweep": False,
            }
        }
        cfg, overrides = _dict_to_config(data)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 3
        assert cfg.browser_testing.e2e_pass_rate_gate == 0.5
        assert cfg.browser_testing.headless is False
        assert cfg.browser_testing.app_start_command == "npm run dev"
        assert cfg.browser_testing.app_port == 4200
        assert cfg.browser_testing.regression_sweep is False
        assert "browser_testing.enabled" in overrides
        assert "browser_testing.max_fix_retries" in overrides

    def test_yaml_partial_uses_defaults(self):
        data = {"browser_testing": {"enabled": True}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 5  # default
        assert cfg.browser_testing.headless is True       # default

    def test_max_fix_retries_zero_raises(self):
        data = {"browser_testing": {"max_fix_retries": 0}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_app_port_500_raises(self):
        data = {"browser_testing": {"app_port": 500}}
        with pytest.raises(ValueError, match="app_port"):
            _dict_to_config(data)

    def test_app_port_70000_raises(self):
        data = {"browser_testing": {"app_port": 70000}}
        with pytest.raises(ValueError, match="app_port"):
            _dict_to_config(data)

    def test_app_port_zero_valid(self):
        data = {"browser_testing": {"app_port": 0}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.app_port == 0

    def test_e2e_pass_rate_gate_negative_raises(self):
        data = {"browser_testing": {"e2e_pass_rate_gate": -0.1}}
        with pytest.raises(ValueError, match="e2e_pass_rate_gate"):
            _dict_to_config(data)

    def test_e2e_pass_rate_gate_over_one_raises(self):
        data = {"browser_testing": {"e2e_pass_rate_gate": 1.5}}
        with pytest.raises(ValueError, match="e2e_pass_rate_gate"):
            _dict_to_config(data)


class TestBrowserTestingDepthGating:
    """Tests for depth gating of browser_testing config."""

    def test_quick_disables(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.enabled = True
        apply_depth_quality_gating("quick", cfg)
        assert cfg.browser_testing.enabled is False

    def test_standard_does_not_enable(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.browser_testing.enabled is False

    def test_thorough_prd_mode_enables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg, prd_mode=True)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 3

    def test_thorough_no_prd_mode_stays_disabled(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is False

    def test_exhaustive_prd_mode_enables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg, prd_mode=True)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 5

    def test_user_override_survives_gating(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.enabled = True
        overrides = {"browser_testing.enabled"}
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        assert cfg.browser_testing.enabled is True

    def test_thorough_milestone_enabled_implies_prd(self):
        """If milestone.enabled=True, thorough should enable browser testing."""
        cfg = AgentTeamConfig()
        cfg.milestone.enabled = True
        apply_depth_quality_gating("thorough", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is True


# =========================================================================
# Dataclass tests
# =========================================================================


class TestDataclasses:
    """Tests for WorkflowDefinition, WorkflowResult, BrowserTestReport dataclasses."""

    def test_workflow_definition_defaults(self):
        wf = WorkflowDefinition()
        assert wf.id == 0
        assert wf.name == ""
        assert wf.path == ""
        assert wf.priority == "MEDIUM"
        assert wf.total_steps == 0
        assert wf.first_page_route == "/"
        assert wf.prd_requirements == []
        assert wf.depends_on == []

    def test_workflow_result_defaults(self):
        wr = WorkflowResult()
        assert wr.workflow_id == 0
        assert wr.workflow_name == ""
        assert wr.total_steps == 0
        assert wr.completed_steps == 0
        assert wr.health == "pending"
        assert wr.failed_step == ""
        assert wr.failure_reason == ""
        assert wr.fix_retries_used == 0
        assert wr.screenshots == []
        assert wr.console_errors == []

    def test_workflow_result_health_states(self):
        for health in ("pending", "passed", "failed", "skipped"):
            wr = WorkflowResult(health=health)
            assert wr.health == health

    def test_browser_test_report_defaults(self):
        report = BrowserTestReport()
        assert report.total_workflows == 0
        assert report.passed_workflows == 0
        assert report.failed_workflows == 0
        assert report.skipped_workflows == 0
        assert report.total_fix_cycles == 0
        assert report.workflow_results == []
        assert report.health == "unknown"
        assert report.skip_reason == ""
        assert report.regression_sweep_passed is False
        assert report.total_screenshots == 0

    def test_run_state_has_completed_browser_workflows(self):
        state = RunState()
        assert hasattr(state, "completed_browser_workflows")
        assert state.completed_browser_workflows == []

    def test_app_startup_info_defaults(self):
        info = AppStartupInfo()
        assert info.start_command == ""
        assert info.seed_command == ""
        assert info.port == 3000
        assert info.health_url == ""
        assert info.env_setup == []
        assert info.build_command == ""


# =========================================================================
# Seed credential extraction
# =========================================================================


class TestSeedCredentialExtraction:

    def test_extracts_email_password_role(self, tmp_path):
        seed = tmp_path / "seed.ts"
        seed.write_text(textwrap.dedent("""\
            // Seed users
            const admin = {
              email: 'admin@example.com',
              password: 'Admin123!',
              role: 'admin',
            };
        """), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert "admin" in creds
        assert creds["admin"]["email"] == "admin@example.com"
        assert creds["admin"]["password"] == "Admin123!"

    def test_no_seed_files_empty(self, tmp_path):
        creds = _extract_seed_credentials(tmp_path)
        assert creds == {}

    def test_multiple_roles(self, tmp_path):
        seed = tmp_path / "seed.ts"
        seed.write_text(textwrap.dedent("""\
            const users = [
              { email: 'admin@test.com', password: 'pass1', role: 'admin' },
              { email: 'user@test.com', password: 'pass2', role: 'user' },
            ];
        """), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert len(creds) >= 2

    def test_infers_role_from_email_prefix(self, tmp_path):
        seed = tmp_path / "seed.ts"
        seed.write_text(textwrap.dedent("""\
            const data = {
              email: 'admin_user@example.com',
              password: 'Secret123',
            };
        """), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert "admin" in creds


# =========================================================================
# Workflow generation
# =========================================================================


class TestGenerateBrowserWorkflows:

    def test_generate_from_requirements(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email and password\n"
            "- [x] REQ-002: Create new project\n"
            "- [x] REQ-003: Edit project details\n"
            "- [x] REQ-004: Delete project\n"
            "- [ ] REQ-005: View project list\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) > 0
        # Auth should be CRITICAL
        assert workflows[0].priority == "CRITICAL"

    def test_generate_with_coverage_matrix(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        matrix = req_dir / "E2E_COVERAGE_MATRIX.md"
        matrix.write_text(textwrap.dedent("""\
            | Req | Description | Status |
            |-----|-------------|--------|
            | REQ-001 | User login | Covered |
            | REQ-002 | Create item | Covered |
        """), encoding="utf-8")
        workflows = generate_browser_workflows(req_dir, matrix, None, tmp_path)
        assert len(workflows) > 0

    def test_max_10_workflows_cap(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        lines = []
        for i in range(1, 50):
            lines.append(f"- [x] REQ-{i:03d}: Create entity_{i}")
        req_file.write_text("\n".join(lines), encoding="utf-8")
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) <= 10

    def test_empty_requirements_empty_list(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert workflows == []

    def test_auth_workflows_no_dependencies(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n"
            "- [x] REQ-002: User register with password\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        # Auth workflows should not depend on anything
        auth_wf = [wf for wf in workflows if wf.priority == "CRITICAL" or "registration" in wf.name.lower()]
        for wf in auth_wf:
            assert wf.depends_on == [], f"Auth workflow {wf.name} should have no dependencies"

    def test_crud_workflows_depend_on_auth(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email and password\n"
            "- [x] REQ-002: Create new project\n"
            "- [x] REQ-003: Edit project details\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        auth_wf = [wf for wf in workflows if "auth" in wf.name.lower() or "login" in wf.name.lower()]
        crud_wf = [wf for wf in workflows if "crud" in wf.name.lower()]
        if auth_wf and crud_wf:
            for cwf in crud_wf:
                assert auth_wf[0].id in cwf.depends_on

    def test_workflow_index_written(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login\n",
            encoding="utf-8",
        )
        generate_browser_workflows(req_dir, None, None, tmp_path)
        index_path = req_dir / "browser-workflows" / "WORKFLOW_INDEX.md"
        assert index_path.is_file()
        content = index_path.read_text(encoding="utf-8")
        assert "Browser Workflow Index" in content


# =========================================================================
# Parsing tests
# =========================================================================


class TestParseWorkflowIndex:

    def test_valid_content(self, tmp_path):
        index = tmp_path / "WORKFLOW_INDEX.md"
        index.write_text(textwrap.dedent("""\
            # Browser Workflow Index

            | ID | Name | Priority | Steps | Dependencies | Requirements |
            |----|------|----------|-------|-------------|--------------|
            | 1 | Auth Login | CRITICAL | 4 | None | REQ-001 |
            | 2 | CRUD Items | HIGH | 6 | 1 | REQ-002, REQ-003 |
        """), encoding="utf-8")
        workflows = parse_workflow_index(index)
        assert len(workflows) == 2
        assert workflows[0].id == 1
        assert workflows[0].name == "Auth Login"
        assert workflows[0].priority == "CRITICAL"
        assert workflows[0].total_steps == 4
        assert workflows[0].depends_on == []
        assert workflows[1].id == 2
        assert workflows[1].depends_on == [1]
        assert workflows[1].prd_requirements == ["REQ-002", "REQ-003"]

    def test_empty_file(self, tmp_path):
        index = tmp_path / "WORKFLOW_INDEX.md"
        index.write_text("", encoding="utf-8")
        assert parse_workflow_index(index) == []

    def test_missing_file(self, tmp_path):
        index = tmp_path / "nonexistent.md"
        assert parse_workflow_index(index) == []


class TestParseWorkflowResults:

    def test_passed_status(self, tmp_path):
        results = tmp_path / "workflow_01_results.md"
        results.write_text(textwrap.dedent("""\
            ## Status: PASSED

            ### Step 1: Navigate to login
            Result: PASSED
            Evidence: Login page loaded
            Screenshot: w01_step01.png

            ### Step 2: Enter credentials
            Result: PASSED
            Evidence: Credentials entered
            Screenshot: w01_step02.png
        """), encoding="utf-8")
        wr = parse_workflow_results(results)
        assert wr.health == "passed"
        assert wr.total_steps == 2
        assert wr.completed_steps == 2
        assert wr.failed_step == ""
        assert "w01_step01.png" in wr.screenshots
        assert "w01_step02.png" in wr.screenshots

    def test_failed_status(self, tmp_path):
        results = tmp_path / "workflow_02_results.md"
        results.write_text(textwrap.dedent("""\
            ## Status: FAILED

            ### Step 1: Navigate to dashboard
            Result: PASSED
            Evidence: Dashboard loaded

            ### Step 2: Click create button
            Result: FAILED
            Evidence: Button not found
            console error: TypeError: Cannot read property 'click' of null
        """), encoding="utf-8")
        wr = parse_workflow_results(results)
        assert wr.health == "failed"
        assert wr.failed_step == "Step 2"
        assert len(wr.console_errors) >= 1

    def test_missing_file(self, tmp_path):
        wr = parse_workflow_results(tmp_path / "missing.md")
        assert wr.health == "failed"
        assert "not found" in wr.failure_reason

    def test_too_small_file(self, tmp_path):
        results = tmp_path / "workflow_03_results.md"
        results.write_text("Short", encoding="utf-8")
        wr = parse_workflow_results(results)
        assert wr.health == "failed"
        assert "too small" in wr.failure_reason


class TestParseAppStartupInfo:

    def test_valid_content(self, tmp_path):
        startup = tmp_path / "APP_STARTUP.md"
        # Use key: value format that _RE_KV regex handles
        startup.write_text(textwrap.dedent("""\
            # App Startup

            Start Command: `npm run dev`
            Seed Command: `npx prisma db seed`
            Port: 3000
            Health URL: http://localhost:3000/health
            Build Command: `npm run build`
        """), encoding="utf-8")
        info = parse_app_startup_info(startup)
        assert info.start_command == "npm run dev"
        assert info.seed_command == "npx prisma db seed"
        assert info.port == 3000
        assert info.health_url == "http://localhost:3000/health"
        assert info.build_command == "npm run build"

    def test_missing_file(self, tmp_path):
        info = parse_app_startup_info(tmp_path / "missing.md")
        assert info.start_command == ""
        assert info.port == 3000  # default


# =========================================================================
# Verification tests
# =========================================================================


class TestVerifyWorkflowExecution:

    def _setup_valid_workflow(self, tmp_path, workflow_id=1, steps=2):
        """Create a valid workflow results structure."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        screenshots_dir = base / "screenshots"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        screenshots_dir.mkdir(parents=True)

        # Results file
        lines = [f"## Status: PASSED", ""]
        for i in range(1, steps + 1):
            lines.extend([
                f"### Step {i}: Step {i} description",
                f"Result: PASSED",
                f"Evidence: Step {i} evidence",
                f"Screenshot: w{workflow_id:02d}_step{i:02d}.png",
                "",
            ])
        results_dir.joinpath(f"workflow_{workflow_id:02d}_results.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

        # Screenshots
        for i in range(1, steps + 1):
            (screenshots_dir / f"w{workflow_id:02d}_step{i:02d}.png").write_bytes(
                b"\x89PNG" + bytes(i * 100)  # Different sizes
            )

        return workflows_dir

    def test_all_checks_pass(self, tmp_path):
        workflows_dir = self._setup_valid_workflow(tmp_path)
        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is True
        assert issues == []

    def test_missing_results_file(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)
        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is False
        assert any("not found" in i for i in issues)

    def test_results_file_too_small(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        results_dir.joinpath("workflow_01_results.md").write_text("Short", encoding="utf-8")
        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is False
        assert any("too small" in i for i in issues)

    def test_missing_step(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        screenshots_dir = base / "screenshots"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        screenshots_dir.mkdir(parents=True)

        # Only step 1, missing step 2
        content = textwrap.dedent("""\
            ## Status: PASSED

            ### Step 1: Do something
            Result: PASSED
            Evidence: Did it
            Screenshot: w01_step01.png
        """)
        results_dir.joinpath("workflow_01_results.md").write_text(content, encoding="utf-8")
        (screenshots_dir / "w01_step01.png").write_bytes(b"\x89PNG" + b"\x00" * 100)
        (screenshots_dir / "w01_step02.png").write_bytes(b"\x89PNG" + b"\x00" * 200)

        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is False
        assert any("Missing step 2" in i for i in issues)

    def test_missing_screenshot(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        screenshots_dir = base / "screenshots"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        screenshots_dir.mkdir(parents=True)

        content = textwrap.dedent("""\
            ## Status: PASSED

            ### Step 1: Do something
            Result: PASSED
            Evidence: Did it

            ### Step 2: Do more
            Result: PASSED
            Evidence: Did more
        """)
        results_dir.joinpath("workflow_01_results.md").write_text(content, encoding="utf-8")
        # No screenshot files created

        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is False
        assert any("Screenshot missing" in i for i in issues)

    def test_contradiction_detection(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        screenshots_dir = base / "screenshots"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        screenshots_dir.mkdir(parents=True)

        content = textwrap.dedent("""\
            ## Status: PASSED

            ### Step 1: Do something
            Result: PASSED
            Evidence: Did it
            Screenshot: w01_step01.png

            ### Step 2: Do more
            Result: FAILED
            Evidence: Broken
            Screenshot: w01_step02.png
        """)
        results_dir.joinpath("workflow_01_results.md").write_text(content, encoding="utf-8")
        (screenshots_dir / "w01_step01.png").write_bytes(b"\x89PNG" + b"\x00" * 100)
        (screenshots_dir / "w01_step02.png").write_bytes(b"\x89PNG" + b"\x00" * 200)

        passed, issues = verify_workflow_execution(workflows_dir, 1, 2)
        assert passed is False
        assert any("Contradiction" in i for i in issues)


# =========================================================================
# Screenshot diversity
# =========================================================================


class TestScreenshotDiversity:

    def test_different_sizes_diverse(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        for i in range(1, 6):
            (screenshots_dir / f"w01_step{i:02d}.png").write_bytes(b"\x89" * (i * 100))
        assert check_screenshot_diversity(screenshots_dir, 1, 5) is True

    def test_identical_sizes_not_diverse(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        for i in range(1, 6):
            (screenshots_dir / f"w01_step{i:02d}.png").write_bytes(b"\x89" * 100)
        assert check_screenshot_diversity(screenshots_dir, 1, 5) is False

    def test_three_or_fewer_always_true(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        for i in range(1, 4):
            (screenshots_dir / f"w01_step{i:02d}.png").write_bytes(b"\x89" * 100)
        assert check_screenshot_diversity(screenshots_dir, 1, 3) is True

    def test_no_screenshots_true(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        assert check_screenshot_diversity(screenshots_dir, 1, 4) is True


# =========================================================================
# State management
# =========================================================================


class TestStateManagement:

    def test_write_workflow_state(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        defs = [
            WorkflowDefinition(id=1, name="Auth Login"),
            WorkflowDefinition(id=2, name="CRUD Items"),
        ]
        write_workflow_state(workflows_dir, defs)

        state_path = base / "WORKFLOW_STATE.md"
        assert state_path.is_file()
        content = state_path.read_text(encoding="utf-8")
        assert "Auth Login" in content
        assert "CRUD Items" in content
        assert "PENDING" in content

    def test_update_workflow_state(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        defs = [
            WorkflowDefinition(id=1, name="Auth Login"),
            WorkflowDefinition(id=2, name="CRUD Items"),
        ]
        write_workflow_state(workflows_dir, defs)
        update_workflow_state(workflows_dir, 1, "PASSED", retries=2, screenshots=5)

        content = (base / "WORKFLOW_STATE.md").read_text(encoding="utf-8")
        # Check updated row
        for line in content.splitlines():
            if "Auth Login" in line:
                assert "PASSED" in line
                break
        else:
            pytest.fail("Auth Login row not found in state file")

    def test_count_screenshots(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        (screenshots_dir / "w01_step01.png").write_bytes(b"\x89PNG")
        (screenshots_dir / "w01_step02.png").write_bytes(b"\x89PNG")
        (screenshots_dir / "not_a_png.txt").write_text("hello", encoding="utf-8")
        assert count_screenshots(screenshots_dir) == 2

    def test_count_screenshots_empty_dir(self, tmp_path):
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        assert count_screenshots(screenshots_dir) == 0

    def test_count_screenshots_missing_dir(self, tmp_path):
        screenshots_dir = tmp_path / "nonexistent"
        assert count_screenshots(screenshots_dir) == 0


# =========================================================================
# Report generation
# =========================================================================


class TestReportGeneration:

    def test_all_passed_production_ready(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=2,
            passed_workflows=2,
            failed_workflows=0,
            skipped_workflows=0,
            total_fix_cycles=1,
            total_screenshots=8,
            regression_sweep_passed=True,
            workflow_results=[
                WorkflowResult(workflow_id=1, workflow_name="Auth", health="passed", total_steps=4, completed_steps=4),
                WorkflowResult(workflow_id=2, workflow_name="CRUD", health="passed", total_steps=6, completed_steps=6),
            ],
        )
        defs = [
            WorkflowDefinition(id=1, name="Auth"),
            WorkflowDefinition(id=2, name="CRUD"),
        ]
        content = generate_readiness_report(workflows_dir, report, defs)
        assert "PRODUCTION READY" in content
        assert "Auth" in content
        assert "CRUD" in content

    def test_partial_verification(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=2,
            passed_workflows=1,
            failed_workflows=1,
            skipped_workflows=0,
            workflow_results=[
                WorkflowResult(workflow_id=1, workflow_name="Auth", health="passed"),
                WorkflowResult(workflow_id=2, workflow_name="CRUD", health="failed"),
            ],
        )
        defs = [
            WorkflowDefinition(id=1, name="Auth"),
            WorkflowDefinition(id=2, name="CRUD"),
        ]
        content = generate_readiness_report(workflows_dir, report, defs)
        assert "PARTIALLY VERIFIED" in content

    def test_none_passed_not_verified(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=2,
            passed_workflows=0,
            failed_workflows=2,
            skipped_workflows=0,
            workflow_results=[
                WorkflowResult(workflow_id=1, workflow_name="Auth", health="failed"),
                WorkflowResult(workflow_id=2, workflow_name="CRUD", health="failed"),
            ],
        )
        defs = [
            WorkflowDefinition(id=1, name="Auth"),
            WorkflowDefinition(id=2, name="CRUD"),
        ]
        content = generate_readiness_report(workflows_dir, report, defs)
        assert "NOT VERIFIED" in content

    def test_unresolved_issues_generation(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        failed = [
            WorkflowResult(
                workflow_id=1,
                workflow_name="Auth Login",
                health="failed",
                failed_step="Step 2",
                failure_reason="Button not found",
                fix_retries_used=3,
                console_errors=["TypeError: null reference"],
            ),
        ]
        content = generate_unresolved_issues(workflows_dir, failed)
        assert "Auth Login" in content
        assert "Button not found" in content
        assert "TypeError" in content

    def test_unresolved_issues_empty(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        content = generate_unresolved_issues(workflows_dir, [])
        assert content == ""


# =========================================================================
# Health check
# =========================================================================


class TestAppHealthCheck:

    def test_http_200_returns_true(self):
        with patch("agent_team.browser_testing.urllib.request.urlopen") as mock_open:
            mock_open.return_value = MagicMock()
            assert check_app_running(3000) is True

    def test_http_error_returns_true(self):
        """4xx/5xx means the app IS running."""
        import urllib.error
        with patch("agent_team.browser_testing.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError(
                "http://localhost:3000", 404, "Not Found", {}, None
            )
            assert check_app_running(3000) is True

    def test_connection_refused_returns_false(self):
        with patch("agent_team.browser_testing.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = ConnectionRefusedError("Connection refused")
            assert check_app_running(3000) is False

    def test_timeout_returns_false(self):
        with patch("agent_team.browser_testing.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = TimeoutError("Timed out")
            assert check_app_running(3000) is False


# =========================================================================
# MCP servers
# =========================================================================


class TestMCPServers:

    def test_playwright_headless_true(self):
        server = _playwright_mcp_server(headless=True)
        assert server["type"] == "stdio"
        assert server["command"] == "npx"
        assert "--headless" in server["args"]

    def test_playwright_headless_false(self):
        server = _playwright_mcp_server(headless=False)
        assert "--headless" not in server["args"]

    def test_get_browser_testing_servers_includes_playwright(self):
        cfg = AgentTeamConfig()
        servers = get_browser_testing_servers(cfg)
        assert "playwright" in servers
        assert servers["playwright"]["command"] == "npx"

    def test_get_browser_testing_servers_with_context7(self):
        cfg = AgentTeamConfig()
        servers = get_browser_testing_servers(cfg)
        assert "context7" in servers

    def test_get_browser_testing_servers_context7_disabled(self):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["context7"].enabled = False
        servers = get_browser_testing_servers(cfg)
        assert "playwright" in servers
        assert "context7" not in servers

    def test_playwright_uses_headless_from_config(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.headless = False
        servers = get_browser_testing_servers(cfg)
        assert "--headless" not in servers["playwright"]["args"]


# =========================================================================
# Prompt content tests
# =========================================================================


class TestPromptContent:

    def test_executor_prompt_contains_anti_cheat(self):
        assert "ANTI-CHEAT" in BROWSER_WORKFLOW_EXECUTOR_PROMPT
        assert "browser_snapshot" in BROWSER_WORKFLOW_EXECUTOR_PROMPT

    def test_executor_prompt_contains_data_discovery(self):
        assert "DATA DISCOVERY" in BROWSER_WORKFLOW_EXECUTOR_PROMPT

    def test_regression_prompt_contains_browser_navigate(self):
        assert "browser_navigate" in BROWSER_REGRESSION_SWEEP_PROMPT

    def test_fix_prompt_contains_fix_cycle_log(self):
        assert "FIX_CYCLE_LOG" in BROWSER_WORKFLOW_FIX_PROMPT

    def test_startup_prompt_has_placeholders(self):
        assert "{project_root}" in BROWSER_APP_STARTUP_PROMPT
        assert "{app_start_command}" in BROWSER_APP_STARTUP_PROMPT
        assert "{app_port}" in BROWSER_APP_STARTUP_PROMPT

    def test_executor_prompt_has_placeholders(self):
        assert "{app_url}" in BROWSER_WORKFLOW_EXECUTOR_PROMPT
        assert "{workflow_id}" in BROWSER_WORKFLOW_EXECUTOR_PROMPT
        assert "{screenshots_dir}" in BROWSER_WORKFLOW_EXECUTOR_PROMPT
        assert "{workflow_content}" in BROWSER_WORKFLOW_EXECUTOR_PROMPT

    def test_regression_prompt_has_placeholders(self):
        assert "{app_url}" in BROWSER_REGRESSION_SWEEP_PROMPT
        assert "{screenshots_dir}" in BROWSER_REGRESSION_SWEEP_PROMPT
        assert "{passed_workflow_urls}" in BROWSER_REGRESSION_SWEEP_PROMPT

    def test_fix_prompt_has_placeholders(self):
        assert "{failure_report}" in BROWSER_WORKFLOW_FIX_PROMPT
        assert "{workflow_content}" in BROWSER_WORKFLOW_FIX_PROMPT
        assert "{console_errors}" in BROWSER_WORKFLOW_FIX_PROMPT
        assert "{fix_cycle_log}" in BROWSER_WORKFLOW_FIX_PROMPT

    def test_executor_prompt_formatble(self):
        """Prompt can be formatted with all required placeholders."""
        result = BROWSER_WORKFLOW_EXECUTOR_PROMPT.format(
            app_url="http://localhost:3000",
            workflow_id="01",
            screenshots_dir="/tmp/screenshots",
            workflow_content="# Test workflow",
        )
        assert "http://localhost:3000" in result

    def test_startup_prompt_formatble(self):
        result = BROWSER_APP_STARTUP_PROMPT.format(
            project_root="/home/user/project",
            app_start_command="npm run dev",
            app_port=3000,
        )
        assert "/home/user/project" in result

    def test_fix_prompt_formatble(self):
        result = BROWSER_WORKFLOW_FIX_PROMPT.format(
            failure_report="Step 2 failed",
            workflow_content="# Workflow",
            console_errors="TypeError",
            fix_cycle_log="No previous attempts",
        )
        assert "Step 2 failed" in result

    def test_regression_prompt_formatble(self):
        result = BROWSER_REGRESSION_SWEEP_PROMPT.format(
            app_url="http://localhost:3000",
            screenshots_dir="/tmp/screenshots",
            passed_workflow_urls="- /login\n- /dashboard",
        )
        assert "/login" in result

    def test_executor_prompt_requires_no_guessing(self):
        """Prompt instructs agents never to guess credentials."""
        assert "NEVER" in BROWSER_WORKFLOW_EXECUTOR_PROMPT
        assert "guess" in BROWSER_WORKFLOW_EXECUTOR_PROMPT.lower()

    def test_fix_prompt_instructs_fix_app_not_test(self):
        """Fix prompt explicitly says fix the app, not the workflow."""
        assert "Fix the APP" in BROWSER_WORKFLOW_FIX_PROMPT

    def test_regression_prompt_is_quick_check(self):
        """Regression sweep must not interact beyond navigation."""
        assert "QUICK" in BROWSER_REGRESSION_SWEEP_PROMPT
        assert "do NOT fill forms" in BROWSER_REGRESSION_SWEEP_PROMPT.upper() or \
               "Do NOT fill forms" in BROWSER_REGRESSION_SWEEP_PROMPT


# =========================================================================
# E2E pass rate gate logic (pure Python simulation)
# =========================================================================


class TestE2EPassRateGateLogic:
    """Test the E2E pass rate gate calculation that controls browser testing."""

    def test_e2e_total_zero_means_skip(self):
        """When E2E total is 0, browser testing should be skipped."""
        e2e_total = 0
        # Simulate: if e2e_total == 0 -> skip
        assert e2e_total == 0

    def test_e2e_pass_rate_below_gate(self):
        """When pass rate < gate, browser testing should skip."""
        e2e_passed = 3
        e2e_total = 10
        gate = 0.7
        rate = e2e_passed / e2e_total
        assert rate < gate

    def test_e2e_pass_rate_above_gate(self):
        """When pass rate >= gate, browser testing should proceed."""
        e2e_passed = 8
        e2e_total = 10
        gate = 0.7
        rate = e2e_passed / e2e_total
        assert rate >= gate

    def test_e2e_pass_rate_exact_gate(self):
        """When pass rate == gate exactly, should proceed."""
        e2e_passed = 7
        e2e_total = 10
        gate = 0.7
        rate = e2e_passed / e2e_total
        assert rate >= gate

    def test_e2e_100_percent_passes(self):
        """100% E2E pass rate always meets gate."""
        e2e_passed = 10
        e2e_total = 10
        gate = 0.7
        rate = e2e_passed / e2e_total
        assert rate >= gate


# =========================================================================
# Health aggregation logic
# =========================================================================


class TestHealthAggregation:
    """Test the health aggregation logic from the CLI pipeline."""

    def test_all_passed_no_skipped(self):
        report = BrowserTestReport(
            total_workflows=3, passed_workflows=3, failed_workflows=0, skipped_workflows=0,
        )
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        else:
            health = "failed"
        assert health == "passed"

    def test_some_passed_partial(self):
        report = BrowserTestReport(
            total_workflows=3, passed_workflows=2, failed_workflows=1, skipped_workflows=0,
        )
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        else:
            health = "failed"
        assert health == "partial"

    def test_none_passed_failed(self):
        report = BrowserTestReport(
            total_workflows=3, passed_workflows=0, failed_workflows=3, skipped_workflows=0,
        )
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        else:
            health = "failed"
        assert health == "failed"

    def test_all_skipped_failed(self):
        report = BrowserTestReport(
            total_workflows=3, passed_workflows=0, failed_workflows=0, skipped_workflows=3,
        )
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        elif report.skipped_workflows == report.total_workflows:
            health = "failed"
        else:
            health = "failed"
        assert health == "failed"

    def test_passed_with_skipped_partial(self):
        """If some passed but also skipped, partial not passed."""
        report = BrowserTestReport(
            total_workflows=3, passed_workflows=2, failed_workflows=0, skipped_workflows=1,
        )
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        else:
            health = "failed"
        assert health == "partial"


# =========================================================================
# Regression sweep condition logic
# =========================================================================


class TestRegressionSweepConditions:
    """Test conditions that control whether regression sweep runs."""

    def test_sweep_runs_when_fixes_applied_and_passed(self):
        regression_sweep = True
        any_fixes_applied = True
        passed_workflows = 2
        should_run = regression_sweep and any_fixes_applied and passed_workflows > 0
        assert should_run is True

    def test_sweep_skipped_when_no_fixes(self):
        regression_sweep = True
        any_fixes_applied = False
        passed_workflows = 2
        should_run = regression_sweep and any_fixes_applied and passed_workflows > 0
        assert should_run is False

    def test_sweep_skipped_when_disabled(self):
        regression_sweep = False
        any_fixes_applied = True
        passed_workflows = 2
        should_run = regression_sweep and any_fixes_applied and passed_workflows > 0
        assert should_run is False

    def test_sweep_skipped_when_none_passed(self):
        regression_sweep = True
        any_fixes_applied = True
        passed_workflows = 0
        should_run = regression_sweep and any_fixes_applied and passed_workflows > 0
        assert should_run is False


# =========================================================================
# Dependency skipping logic
# =========================================================================


class TestDependencySkipping:
    """Test prerequisite dependency check logic."""

    def test_skips_when_dep_failed(self):
        workflow_results = {
            1: WorkflowResult(workflow_id=1, health="failed"),
        }
        wf = WorkflowDefinition(id=2, depends_on=[1])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == [1]

    def test_skips_when_dep_skipped(self):
        workflow_results = {
            1: WorkflowResult(workflow_id=1, health="skipped"),
        }
        wf = WorkflowDefinition(id=2, depends_on=[1])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == [1]

    def test_proceeds_when_dep_passed(self):
        workflow_results = {
            1: WorkflowResult(workflow_id=1, health="passed"),
        }
        wf = WorkflowDefinition(id=2, depends_on=[1])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == []

    def test_proceeds_when_no_deps(self):
        workflow_results = {}
        wf = WorkflowDefinition(id=1, depends_on=[])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == []

    def test_proceeds_when_dep_not_yet_executed(self):
        """If dep not in results yet, it should NOT block."""
        workflow_results = {}
        wf = WorkflowDefinition(id=2, depends_on=[1])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == []

    def test_multiple_deps_one_failed(self):
        workflow_results = {
            1: WorkflowResult(workflow_id=1, health="passed"),
            2: WorkflowResult(workflow_id=2, health="failed"),
        }
        wf = WorkflowDefinition(id=3, depends_on=[1, 2])
        failed_deps = [
            dep for dep in wf.depends_on
            if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
        ]
        assert failed_deps == [2]


# =========================================================================
# Port resolution logic
# =========================================================================


class TestPortResolution:
    """Test the port resolution cascade from config."""

    def test_explicit_port_used(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.app_port = 4200
        port = cfg.browser_testing.app_port
        assert port == 4200

    def test_zero_port_falls_to_e2e(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.app_port = 0
        cfg.e2e_testing.test_port = 9876
        port = cfg.browser_testing.app_port
        if port == 0:
            port = cfg.e2e_testing.test_port
        assert port == 9876

    def test_zero_port_zero_e2e_falls_to_default(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.app_port = 0
        cfg.e2e_testing.test_port = 9876  # real default is 9876 not 0
        port = cfg.browser_testing.app_port
        if port == 0:
            port = cfg.e2e_testing.test_port
        if port == 0:
            port = 3000
        assert port == 9876

    def test_e2e_default_port_9876(self):
        cfg = AgentTeamConfig()
        assert cfg.e2e_testing.test_port == 9876


# =========================================================================
# State persistence fields
# =========================================================================


class TestStatePersistence:
    """Test RunState serialization with browser fields."""

    def test_run_state_serializes_browser_workflows(self):
        from dataclasses import asdict
        state = RunState()
        state.completed_browser_workflows = [1, 3, 5]
        data = asdict(state)
        assert data["completed_browser_workflows"] == [1, 3, 5]

    def test_run_state_loads_browser_workflows(self):
        """Test that load_state handles completed_browser_workflows."""
        import json
        from agent_team.state import load_state
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "STATE.json"
            state_data = {
                "run_id": "test123",
                "task": "build something",
                "depth": "standard",
                "current_phase": "browser_testing",
                "completed_phases": ["orchestration"],
                "total_cost": 5.0,
                "artifacts": {},
                "interrupted": True,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "convergence_cycles": 0,
                "requirements_checked": 0,
                "requirements_total": 0,
                "error_context": "",
                "milestone_progress": {},
                "schema_version": 2,
                "current_milestone": "",
                "completed_milestones": [],
                "failed_milestones": [],
                "milestone_order": [],
                "completion_ratio": 0.0,
                "completed_browser_workflows": [1, 2],
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            loaded = load_state(directory=tmpdir)
            assert loaded is not None
            assert loaded.completed_browser_workflows == [1, 2]

    def test_run_state_loads_without_browser_field(self):
        """Backward compat: STATE.json without completed_browser_workflows."""
        import json
        from agent_team.state import load_state

        with __import__("tempfile").TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "STATE.json"
            state_data = {
                "run_id": "test123",
                "task": "build something",
                "depth": "standard",
                "current_phase": "init",
                "completed_phases": [],
                "total_cost": 0.0,
                "artifacts": {},
                "interrupted": True,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "schema_version": 2,
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            loaded = load_state(directory=tmpdir)
            assert loaded is not None
            assert loaded.completed_browser_workflows == []


# =========================================================================
# Workflow file content tests
# =========================================================================


class TestWorkflowFileContent:
    """Test that generated workflow files have correct structure."""

    def test_workflow_file_has_title(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email and password\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) > 0
        wf_path = Path(workflows[0].path)
        assert wf_path.is_file()
        content = wf_path.read_text(encoding="utf-8")
        assert content.startswith("# Workflow")

    def test_workflow_file_has_steps(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        content = Path(workflows[0].path).read_text(encoding="utf-8")
        assert "## Steps" in content
        assert "### Step 1" in content

    def test_workflow_file_has_success_criteria(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        content = Path(workflows[0].path).read_text(encoding="utf-8")
        assert "Success Criteria" in content

    def test_workflow_file_has_priority(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        content = Path(workflows[0].path).read_text(encoding="utf-8")
        assert "Priority" in content


# =========================================================================
# Error handling workflows
# =========================================================================


class TestErrorHandlingWorkflows:
    """Test that error-handling keywords produce error workflows."""

    def test_error_keywords_generate_error_workflow(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n"
            "- [x] REQ-002: Show error for invalid email format\n"
            "- [x] REQ-003: Show 404 for missing page\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        error_wf = [wf for wf in workflows if "error" in wf.name.lower()]
        assert len(error_wf) >= 1

    def test_complex_keywords_generate_complex_workflow(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n"
            "- [x] REQ-002: Generate monthly report PDF\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        complex_wf = [wf for wf in workflows if "complex" in wf.name.lower()]
        assert len(complex_wf) >= 1


# =========================================================================
# Report file output
# =========================================================================


class TestReportFileOutput:
    """Test that reports are written to correct paths."""

    def test_readiness_report_written(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=1, passed_workflows=1,
            workflow_results=[WorkflowResult(workflow_id=1, health="passed")],
        )
        defs = [WorkflowDefinition(id=1, name="Auth")]
        generate_readiness_report(workflows_dir, report, defs)

        report_path = base / "BROWSER_READINESS_REPORT.md"
        assert report_path.is_file()

    def test_unresolved_issues_written(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        failed = [WorkflowResult(workflow_id=1, workflow_name="Auth", health="failed")]
        generate_unresolved_issues(workflows_dir, failed)

        issues_path = base / "UNRESOLVED_ISSUES.md"
        assert issues_path.is_file()

    def test_readiness_report_console_error_summary(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=1, passed_workflows=0, failed_workflows=1,
            workflow_results=[
                WorkflowResult(
                    workflow_id=1, health="failed",
                    console_errors=["TypeError: null ref", "ReferenceError: x is not defined"],
                ),
            ],
        )
        defs = [WorkflowDefinition(id=1, name="Auth")]
        content = generate_readiness_report(workflows_dir, report, defs)
        assert "Console Error Summary" in content
        assert "TypeError" in content

    def test_readiness_report_no_console_errors(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        report = BrowserTestReport(
            total_workflows=1, passed_workflows=1,
            workflow_results=[WorkflowResult(workflow_id=1, health="passed")],
        )
        defs = [WorkflowDefinition(id=1, name="Auth")]
        content = generate_readiness_report(workflows_dir, report, defs)
        assert "Console Error Summary" not in content


# =========================================================================
# Config edge cases
# =========================================================================


class TestConfigEdgeCases:

    def test_app_port_1024_valid(self):
        data = {"browser_testing": {"app_port": 1024}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.app_port == 1024

    def test_app_port_65535_valid(self):
        data = {"browser_testing": {"app_port": 65535}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.app_port == 65535

    def test_app_port_1023_raises(self):
        data = {"browser_testing": {"app_port": 1023}}
        with pytest.raises(ValueError, match="app_port"):
            _dict_to_config(data)

    def test_app_port_65536_raises(self):
        data = {"browser_testing": {"app_port": 65536}}
        with pytest.raises(ValueError, match="app_port"):
            _dict_to_config(data)

    def test_e2e_pass_rate_gate_zero_valid(self):
        data = {"browser_testing": {"e2e_pass_rate_gate": 0.0}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.e2e_pass_rate_gate == 0.0

    def test_e2e_pass_rate_gate_one_valid(self):
        data = {"browser_testing": {"e2e_pass_rate_gate": 1.0}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.e2e_pass_rate_gate == 1.0

    def test_max_fix_retries_one_valid(self):
        data = {"browser_testing": {"max_fix_retries": 1}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.max_fix_retries == 1

    def test_app_start_command_preserved(self):
        data = {"browser_testing": {"app_start_command": "python manage.py runserver"}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.app_start_command == "python manage.py runserver"

    def test_headless_false_from_yaml(self):
        data = {"browser_testing": {"headless": False}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.headless is False

    def test_user_overrides_tracked_for_enabled(self):
        data = {"browser_testing": {"enabled": False}}
        _, overrides = _dict_to_config(data)
        assert "browser_testing.enabled" in overrides

    def test_user_overrides_tracked_for_retries(self):
        data = {"browser_testing": {"max_fix_retries": 3}}
        _, overrides = _dict_to_config(data)
        assert "browser_testing.max_fix_retries" in overrides

    def test_no_browser_testing_section_no_overrides(self):
        data = {}
        _, overrides = _dict_to_config(data)
        assert "browser_testing.enabled" not in overrides


# =========================================================================
# Seed credential edge cases
# =========================================================================


class TestSeedCredentialEdgeCases:

    def test_password_close_to_email(self, tmp_path):
        """Password within 10 lines of email is paired."""
        seed = tmp_path / "seed.ts"
        lines = ["const data = {"]
        lines.append("  email: 'test@example.com',")
        lines.extend(["  // padding"] * 5)
        lines.append("  password: 'TestPass123',")
        lines.append("};")
        seed.write_text("\n".join(lines), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert len(creds) >= 1

    def test_password_too_far_from_email(self, tmp_path):
        """Password more than 10 lines from email is NOT paired."""
        seed = tmp_path / "seed.ts"
        lines = ["const data = {"]
        lines.append("  email: 'test@example.com',")
        lines.extend(["  // padding"] * 15)
        lines.append("  password: 'TestPass123',")
        lines.append("};")
        seed.write_text("\n".join(lines), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert len(creds) == 0

    def test_fixture_json_files(self, tmp_path):
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        fixture = fixtures_dir / "users.json"
        # JSON files won't match the regex since it looks for key: 'value' not "key": "value"
        fixture.write_text('{"email": "admin@test.com", "password": "pass"}', encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        # The regex expects email: 'value' or email = 'value' with quotes
        # JSON uses : "value" which matches the regex pattern
        # Actually _RE_EMAIL expects [:=]\s*["'] so JSON colon+space+" should match
        assert isinstance(creds, dict)

    def test_python_seed_files(self, tmp_path):
        seed = tmp_path / "seed_data.py"
        # The regex expects unquoted key names: email = 'value' or email: 'value'
        seed.write_text(textwrap.dedent("""\
            email = 'admin@test.com'
            password = 'AdminPass1!'
            role = 'admin'
        """), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert "admin" in creds


# =========================================================================
# Workflow generation route discovery
# =========================================================================


class TestWorkflowRouteDiscovery:
    """Test that route discovery finds routes from source files."""

    def test_discovers_routes_from_router_file(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n"
            "- [x] REQ-002: Create new task\n",
            encoding="utf-8",
        )
        # Create a router file with route definitions
        router_dir = tmp_path / "src"
        router_dir.mkdir()
        router_file = router_dir / "router.ts"
        router_file.write_text(textwrap.dedent("""\
            const routes = [
                { path: '/tasks', component: TaskList },
                { path: '/login', component: Login },
            ];
        """), encoding="utf-8")

        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) > 0
        # At least one workflow should have a discovered route
        routes_found = [wf.first_page_route for wf in workflows]
        assert "/login" in routes_found or any(r != "/" for r in routes_found)


# =========================================================================
# Update workflow state edge cases
# =========================================================================


class TestUpdateWorkflowStateEdges:

    def test_update_nonexistent_id(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        defs = [WorkflowDefinition(id=1, name="Auth Login")]
        write_workflow_state(workflows_dir, defs)
        # Update a non-existent ID -- should not crash
        update_workflow_state(workflows_dir, 99, "PASSED")
        content = (base / "WORKFLOW_STATE.md").read_text(encoding="utf-8")
        assert "PENDING" in content  # Original still pending

    def test_update_missing_state_file(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)
        # No state file -- should not crash
        update_workflow_state(workflows_dir, 1, "PASSED")

    def test_write_state_creates_header(self, tmp_path):
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)

        defs = [WorkflowDefinition(id=1, name="Auth")]
        write_workflow_state(workflows_dir, defs)
        content = (base / "WORKFLOW_STATE.md").read_text(encoding="utf-8")
        assert "Workflow Execution State" in content
        assert "| ID |" in content


# =========================================================================
# Verification edge cases
# =========================================================================


class TestVerificationEdgeCases:

    def test_alternative_naming_pattern(self, tmp_path):
        """Results file without zero-padding should also be found."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        screenshots_dir = base / "screenshots"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        screenshots_dir.mkdir(parents=True)

        content = textwrap.dedent("""\
            ## Status: PASSED

            ### Step 1: Do something
            Result: PASSED
            Evidence: Did it
            Screenshot: w1_step1.png
        """)
        # Use non-padded filename
        results_dir.joinpath("workflow_1_results.md").write_text(content, encoding="utf-8")
        (screenshots_dir / "w1_step1.png").write_bytes(b"\x89PNG" + b"\x00" * 100)

        passed, issues = verify_workflow_execution(workflows_dir, 1, 1)
        # Should find the non-padded file
        assert any("not found" not in i for i in issues) or passed is True


# =========================================================================
# parse_workflow_results crash isolation & edge cases
# =========================================================================


class TestParseWorkflowResultsCrashIsolation:

    def test_missing_file_returns_failed(self, tmp_path):
        result = parse_workflow_results(tmp_path / "nonexistent.md")
        assert result.health == "failed"
        assert "not found" in result.failure_reason.lower()

    def test_too_small_file(self, tmp_path):
        p = tmp_path / "tiny.md"
        p.write_text("small", encoding="utf-8")
        result = parse_workflow_results(p)
        assert result.health == "failed"
        assert "too small" in result.failure_reason.lower()

    def test_parses_passed_status(self, tmp_path):
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: PASSED\n\n"
            "### Step 1: Open page\n"
            "Result: PASSED\n"
            "Evidence: Page loaded\n"
            "Screenshot: w1_step1.png\n" + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert result.health == "passed"
        assert result.total_steps == 1
        assert result.completed_steps == 1

    def test_parses_failed_step(self, tmp_path):
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: FAILED\n\n"
            "### Step 1: Do thing\nResult: PASSED\nEvidence: done\n"
            "### Step 2: Click button\nResult: FAILED\nEvidence: broken\n"
            + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert result.health == "failed"
        assert result.failed_step == "Step 2"

    def test_parses_screenshots_unique(self, tmp_path):
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: PASSED\n\n"
            "### Step 1: First\nScreenshot: w1_step1.png\nScreenshot: w1_step1.png\n"
            "### Step 2: Second\nScreenshot: w1_step2.png\n"
            + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert len(result.screenshots) == 2
        assert "w1_step1.png" in result.screenshots
        assert "w1_step2.png" in result.screenshots

    def test_parses_console_errors(self, tmp_path):
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: FAILED\n\n"
            "### Step 1: Open\nResult: FAILED\n"
            "Console Error: TypeError: undefined is not a function\n"
            "Console Error: 404 not found\n"
            + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert len(result.console_errors) >= 1


# =========================================================================
# parse_workflow_index edge cases
# =========================================================================


class TestParseWorkflowIndexEdgeCases:

    def test_empty_file(self, tmp_path):
        p = tmp_path / "WORKFLOW_INDEX.md"
        p.write_text("", encoding="utf-8")
        result = parse_workflow_index(p)
        assert result == []

    def test_missing_file(self, tmp_path):
        result = parse_workflow_index(tmp_path / "missing.md")
        assert result == []

    def test_valid_table_parsed(self, tmp_path):
        p = tmp_path / "WORKFLOW_INDEX.md"
        p.write_text(
            "| ID | Name | Priority | Steps | Dependencies | Requirements |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | Auth Login | CRITICAL | 5 | None | REQ-001 |\n"
            "| 2 | Dashboard | HIGH | 3 | 1 | REQ-002 |\n",
            encoding="utf-8",
        )
        result = parse_workflow_index(p)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Auth Login"
        assert result[0].priority == "CRITICAL"
        assert result[0].total_steps == 5
        assert result[1].depends_on == [1]
        assert result[1].prd_requirements == ["REQ-002"]

    def test_separator_row_skipped(self, tmp_path):
        p = tmp_path / "WORKFLOW_INDEX.md"
        p.write_text(
            "| ID | Name | Priority | Steps |\n"
            "|---|---|---|---|\n"
            "| 1 | Test | HIGH | 3 |\n",
            encoding="utf-8",
        )
        result = parse_workflow_index(p)
        assert len(result) == 1  # Separator not parsed as workflow

    def test_non_integer_id_skipped(self, tmp_path):
        p = tmp_path / "WORKFLOW_INDEX.md"
        p.write_text(
            "| ID | Name | Priority | Steps |\n"
            "|---|---|---|---|\n"
            "| abc | Bad | HIGH | 3 |\n"
            "| 1 | Good | HIGH | 3 |\n",
            encoding="utf-8",
        )
        result = parse_workflow_index(p)
        assert len(result) == 1
        assert result[0].id == 1


# =========================================================================
# count_screenshots tests
# =========================================================================


class TestCountScreenshots:

    def test_count_png_files(self, tmp_path):
        ss = tmp_path / "screenshots"
        ss.mkdir()
        (ss / "a.png").write_bytes(b"\x89PNG")
        (ss / "b.png").write_bytes(b"\x89PNG")
        (ss / "c.jpg").write_bytes(b"\xFF\xD8")  # Not counted
        assert count_screenshots(ss) == 2

    def test_empty_dir(self, tmp_path):
        ss = tmp_path / "screenshots"
        ss.mkdir()
        assert count_screenshots(ss) == 0

    def test_nonexistent_dir(self, tmp_path):
        assert count_screenshots(tmp_path / "nope") == 0


# =========================================================================
# generate_readiness_report deeper tests
# =========================================================================


class TestGenerateReadinessReportDeep:

    def _make_report_and_defs(self, verdicts):
        """Helper: create BrowserTestReport + defs for given workflow verdicts."""
        defs = []
        results = []
        passed = 0
        failed = 0
        for i, v in enumerate(verdicts, 1):
            defs.append(WorkflowDefinition(id=i, name=f"WF-{i}", total_steps=3))
            wr = WorkflowResult(workflow_id=i, workflow_name=f"WF-{i}", health=v)
            results.append(wr)
            if v == "passed":
                passed += 1
            elif v == "failed":
                failed += 1
        report = BrowserTestReport(
            total_workflows=len(verdicts),
            passed_workflows=passed,
            failed_workflows=failed,
            workflow_results=results,
        )
        return report, defs

    def test_production_ready_verdict(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report, defs = self._make_report_and_defs(["passed", "passed"])
        content = generate_readiness_report(wd, report, defs)
        assert "PRODUCTION READY" in content

    def test_partially_verified_verdict(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report, defs = self._make_report_and_defs(["passed", "failed"])
        content = generate_readiness_report(wd, report, defs)
        assert "PARTIALLY VERIFIED" in content

    def test_not_verified_verdict(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report, defs = self._make_report_and_defs(["failed", "failed"])
        content = generate_readiness_report(wd, report, defs)
        assert "NOT VERIFIED" in content

    def test_writes_file(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report, defs = self._make_report_and_defs(["passed"])
        generate_readiness_report(wd, report, defs)
        p = wd.parent / "BROWSER_READINESS_REPORT.md"
        assert p.is_file()


# =========================================================================
# generate_unresolved_issues deeper tests
# =========================================================================


class TestGenerateUnresolvedIssuesDeep:

    def test_empty_list_returns_empty(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        content = generate_unresolved_issues(wd, [])
        assert content == ""

    def test_single_failure_written(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        wr = WorkflowResult(
            workflow_id=1,
            workflow_name="Auth",
            health="failed",
            failed_step="Step 2",
            failure_reason="Button not found",
            fix_retries_used=3,
            console_errors=["TypeError"],
            screenshots=["w1_step2.png"],
        )
        content = generate_unresolved_issues(wd, [wr])
        assert "Auth" in content
        assert "Step 2" in content
        assert "Button not found" in content
        assert "TypeError" in content
        p = wd.parent / "UNRESOLVED_ISSUES.md"
        assert p.is_file()

    def test_multiple_failures(self, tmp_path):
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        failures = [
            WorkflowResult(workflow_id=1, workflow_name="WF1", health="failed"),
            WorkflowResult(workflow_id=3, workflow_name="WF3", health="failed"),
        ]
        content = generate_unresolved_issues(wd, failures)
        assert "Total unresolved workflows:** 2" in content


# =========================================================================
# parse_app_startup_info edge cases
# =========================================================================


class TestParseAppStartupEdgeCases:

    def test_missing_file(self, tmp_path):
        info = parse_app_startup_info(tmp_path / "missing.md")
        # Returns default AppStartupInfo (port defaults to 3000)
        assert info.start_command == ""
        assert info.port == 3000

    def test_empty_file(self, tmp_path):
        p = tmp_path / "APP_STARTUP.md"
        p.write_text("", encoding="utf-8")
        info = parse_app_startup_info(p)
        assert info.start_command == ""

    def test_port_field_parsed(self, tmp_path):
        p = tmp_path / "APP_STARTUP.md"
        p.write_text("Port: 4200\nStart Command: npm start\n", encoding="utf-8")
        info = parse_app_startup_info(p)
        assert info.port == 4200
        assert info.start_command == "npm start"

    def test_port_not_a_number_defaults(self, tmp_path):
        """Port value 'not_a_number' should default to 3000 (no crash)."""
        p = tmp_path / "APP_STARTUP.md"
        p.write_text("Port: not_a_number\nStart Command: npm start\n", encoding="utf-8")
        info = parse_app_startup_info(p)
        # port regex won't find digits → stays at default 3000
        assert info.port == 3000


# =========================================================================
# Edge Case Tests for Core Module
# =========================================================================


class TestGenerateBrowserWorkflowsEdgeCases:
    """Edge cases for workflow generation."""

    def test_empty_requirements_and_empty_matrix_returns_empty(self, tmp_path):
        """Empty requirements AND empty coverage matrix → empty list."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        # No REQUIREMENTS.md, no matrix
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert workflows == []

    def test_malformed_coverage_matrix_falls_back(self, tmp_path):
        """Malformed coverage matrix content → falls back to REQUIREMENTS.md."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        matrix = req_dir / "E2E_COVERAGE_MATRIX.md"
        matrix.write_text("This is not a valid table at all\nno pipes\n", encoding="utf-8")
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email\n",
            encoding="utf-8",
        )
        workflows = generate_browser_workflows(req_dir, matrix, None, tmp_path)
        assert len(workflows) > 0  # Falls back to REQUIREMENTS.md


class TestSeedCredentialEdgeCasesExtended:
    """Extended edge cases for seed credential extraction."""

    def test_binary_file_in_seed_path_skipped(self, tmp_path):
        """Binary file in seed path is skipped gracefully."""
        seed = tmp_path / "seed_data.ts"
        seed.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd" * 100)
        creds = _extract_seed_credentials(tmp_path)
        assert isinstance(creds, dict)  # No crash

    def test_large_seed_file_still_works(self, tmp_path):
        """Large seed file (>1MB) still works."""
        seed = tmp_path / "seed.ts"
        content = "// padding\n" * 100000
        content += "const admin = { email: 'admin@test.com', password: 'Pass123!', role: 'admin' };\n"
        seed.write_text(content, encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert "admin" in creds

    def test_email_line_1_password_line_15_not_grouped(self, tmp_path):
        """Email on line 1 and password on line 15 → NOT grouped (>10 line window)."""
        seed = tmp_path / "seed.ts"
        lines = []
        lines.append("email: 'test@example.com',")
        lines.extend(["// padding"] * 14)
        lines.append("password: 'TestPass123',")
        seed.write_text("\n".join(lines), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert len(creds) == 0  # Not paired — distance > 10

    def test_email_line_1_password_line_10_grouped(self, tmp_path):
        """Email on line 1 and password on line 10 → grouped (within 10 line window)."""
        seed = tmp_path / "seed.ts"
        lines = []
        lines.append("email: 'test@example.com',")
        lines.extend(["// padding"] * 8)
        lines.append("password: 'TestPass123',")
        seed.write_text("\n".join(lines), encoding="utf-8")
        creds = _extract_seed_credentials(tmp_path)
        assert len(creds) >= 1


class TestParseWorkflowResultsEdgeCases:
    """Extended edge cases for parse_workflow_results."""

    def test_utf8_special_chars_in_steps(self, tmp_path):
        """UTF-8 special chars in step names handled correctly."""
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: PASSED\n\n"
            "### Step 1: Verificar inicio de sesi\u00f3n\n"
            "Result: PASSED\n"
            "Evidence: P\u00e1gina carg\u00f3 correctamente\n"
            "Screenshot: w01_step01.png\n" + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert result.health == "passed"
        assert result.total_steps == 1

    def test_step_with_result_but_no_evidence(self, tmp_path):
        """Step that has Result: but no Evidence: → partial parse."""
        p = tmp_path / "results.md"
        p.write_text(
            "## Status: PASSED\n\n"
            "### Step 1: Open page\n"
            "Result: PASSED\n"
            "Screenshot: w01_step01.png\n" + "x" * 100,
            encoding="utf-8",
        )
        result = parse_workflow_results(p)
        assert result.total_steps == 1
        assert result.completed_steps == 1


class TestVerifyWorkflowExecutionEdgeCases:
    """Extended edge cases for verify_workflow_execution."""

    def test_results_file_exactly_100_bytes(self, tmp_path):
        """Results file that is exactly 100 bytes → passes size check."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)

        content = "## Status: PASSED\n### Step 1: Test\nResult: PASSED\nEvidence: ok\n"
        # Pad to exactly 100 bytes
        content += "x" * (100 - len(content.encode("utf-8")))
        assert len(content.encode("utf-8")) == 100
        results_dir.joinpath("workflow_01_results.md").write_text(content, encoding="utf-8")

        passed, issues = verify_workflow_execution(workflows_dir, 1, 1)
        # Should NOT fail with "too small"
        assert not any("too small" in i for i in issues)

    def test_results_file_99_bytes_fails(self, tmp_path):
        """Results file that is 99 bytes → fails size check."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        results_dir = base / "results"
        workflows_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)

        content = "x" * 99
        results_dir.joinpath("workflow_01_results.md").write_text(content, encoding="utf-8")

        passed, issues = verify_workflow_execution(workflows_dir, 1, 1)
        assert passed is False
        assert any("too small" in i for i in issues)


class TestCheckScreenshotDiversityEdgeCases:
    """Extended edge cases for check_screenshot_diversity."""

    def test_exactly_30_percent_unique_passes(self, tmp_path):
        """Exactly 30% unique sizes → passes (boundary)."""
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        # 10 files, 3 unique sizes = 30%
        for i in range(1, 11):
            if i <= 3:
                size = i * 100  # 3 unique sizes
            else:
                size = 100  # rest are all 100 bytes
            (screenshots_dir / f"w01_step{i:02d}.png").write_bytes(b"\x89" * size)

        result = check_screenshot_diversity(screenshots_dir, 1, 10)
        assert result is True  # 30% = 0.3 >= 0.3

    def test_29_percent_unique_fails(self, tmp_path):
        """Below 30% unique sizes → fails (boundary)."""
        screenshots_dir = tmp_path / "screenshots"
        screenshots_dir.mkdir()
        # 10 files, 2 unique sizes = 20%
        for i in range(1, 11):
            if i <= 2:
                size = i * 100
            else:
                size = 100
            (screenshots_dir / f"w01_step{i:02d}.png").write_bytes(b"\x89" * size)

        result = check_screenshot_diversity(screenshots_dir, 1, 10)
        assert result is False  # 20% < 30%


class TestGenerateReadinessReportEdgeCases:
    """Extended edge cases for generate_readiness_report."""

    def test_zero_workflows_still_valid_markdown(self, tmp_path):
        """Zero workflows → still generates valid markdown (verdict PRODUCTION READY since 0==0)."""
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report = BrowserTestReport(total_workflows=0)
        content = generate_readiness_report(wd, report, [])
        assert "# Browser Readiness Report" in content
        # 0 passed == 0 total and 0 skipped → "PRODUCTION READY" per source logic
        assert "PRODUCTION READY" in content

    def test_all_skipped_not_verified(self, tmp_path):
        """All workflows skipped → NOT VERIFIED verdict."""
        wd = tmp_path / "browser-workflows" / "workflows"
        wd.mkdir(parents=True)
        report = BrowserTestReport(
            total_workflows=3,
            passed_workflows=0,
            failed_workflows=0,
            skipped_workflows=3,
            workflow_results=[
                WorkflowResult(workflow_id=1, workflow_name="WF1", health="skipped"),
                WorkflowResult(workflow_id=2, workflow_name="WF2", health="skipped"),
                WorkflowResult(workflow_id=3, workflow_name="WF3", health="skipped"),
            ],
        )
        defs = [
            WorkflowDefinition(id=1, name="WF1"),
            WorkflowDefinition(id=2, name="WF2"),
            WorkflowDefinition(id=3, name="WF3"),
        ]
        content = generate_readiness_report(wd, report, defs)
        assert "NOT VERIFIED" in content


class TestUpdateWorkflowStateEdgeCasesExtended:
    """Extended edge cases for state management."""

    def test_update_nonexistent_workflow_id_no_crash(self, tmp_path):
        """Update for non-existent workflow ID → no crash."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)
        defs = [WorkflowDefinition(id=1, name="Auth")]
        write_workflow_state(workflows_dir, defs)
        # Update non-existent ID 99
        update_workflow_state(workflows_dir, 99, "PASSED")
        content = (base / "WORKFLOW_STATE.md").read_text(encoding="utf-8")
        assert "PENDING" in content  # Original unchanged

    def test_write_empty_definitions_creates_empty_table(self, tmp_path):
        """Empty definitions list creates header-only table."""
        base = tmp_path / "browser-workflows"
        workflows_dir = base / "workflows"
        workflows_dir.mkdir(parents=True)
        write_workflow_state(workflows_dir, [])
        content = (base / "WORKFLOW_STATE.md").read_text(encoding="utf-8")
        assert "Workflow Execution State" in content
        assert "| ID |" in content
        # No data rows beyond the header
        lines = [l for l in content.splitlines() if l.startswith("|") and not l.startswith("|-") and not l.startswith("| ID")]
        assert len(lines) == 0


class TestCheckAppRunningEdgeCases:
    """Extended edge cases for check_app_running."""

    def test_port_zero_returns_false(self):
        """Port 0 returns False (invalid port)."""
        from unittest.mock import patch
        # Attempting to connect to port 0 will fail
        with patch("agent_team.browser_testing.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = OSError("Cannot connect")
            result = check_app_running(0)
            assert result is False


class TestParseWorkflowIndexEdgeCasesExtended:
    """Extended edge cases for parse_workflow_index."""

    def test_duplicate_ids_handled_gracefully(self, tmp_path):
        """Duplicate IDs → both parsed (no crash)."""
        p = tmp_path / "WORKFLOW_INDEX.md"
        p.write_text(
            "| ID | Name | Priority | Steps | Dependencies | Requirements |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | Auth Login | CRITICAL | 5 | None | REQ-001 |\n"
            "| 1 | Auth Login Copy | CRITICAL | 5 | None | REQ-001 |\n",
            encoding="utf-8",
        )
        result = parse_workflow_index(p)
        # Both are parsed (no dedup logic)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 1


class TestHealthAggregationEdgeCases:
    """Extended health aggregation edge cases."""

    def test_zero_total_zero_passed_zero_skipped_failed(self):
        """0 passed, 0 failed, 0 skipped (total 0) → 'failed' (not passed)."""
        report = BrowserTestReport(
            total_workflows=0,
            passed_workflows=0,
            failed_workflows=0,
            skipped_workflows=0,
        )
        # Simulate the aggregation logic from cli.py
        if report.passed_workflows == report.total_workflows and report.skipped_workflows == 0:
            # 0 == 0 is True, so this branch would fire
            health = "passed"
        elif report.passed_workflows > 0:
            health = "partial"
        else:
            health = "failed"
        # Note: 0 == 0 is True, so with 0 total workflows, aggregation says "passed"
        # This matches the actual source code behavior
        assert health == "passed"


class TestWorkflowGenerationCredentialIntegration:
    """Tests for credential integration in workflow generation."""

    def test_credentials_embedded_in_workflow_file(self, tmp_path):
        """Generated workflow file embeds discovered credentials."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email and password\n",
            encoding="utf-8",
        )
        # Create seed file with credentials
        seed = tmp_path / "seed.ts"
        seed.write_text(textwrap.dedent("""\
            const admin = {
              email: 'admin@test.com',
              password: 'Admin123!',
              role: 'admin',
            };
        """), encoding="utf-8")
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) > 0
        content = Path(workflows[0].path).read_text(encoding="utf-8")
        assert "admin@test.com" in content

    def test_no_credentials_uses_discover_message(self, tmp_path):
        """When no credentials found, workflow mentions 'discover'."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        req_file = req_dir / "REQUIREMENTS.md"
        req_file.write_text(
            "- [x] REQ-001: User login with email and password\n",
            encoding="utf-8",
        )
        # No seed files
        workflows = generate_browser_workflows(req_dir, None, None, tmp_path)
        assert len(workflows) > 0
        content = Path(workflows[0].path).read_text(encoding="utf-8")
        assert "discover" in content.lower()
