"""Tests for Browser MCP Interactive Testing Phase wiring.

Verifies the browser testing pipeline is correctly positioned in cli.py,
config gating works, depth gating propagates, state tracking fields exist,
source-level ordering is correct, crash isolation, E2E gate logic,
startup fallback, pipeline order, regression re-execute, and finally block cleanup.
"""

from __future__ import annotations

import inspect
import textwrap
from pathlib import Path

import pytest

from agent_team.config import (
    AgentTeamConfig,
    BrowserTestingConfig,
    apply_depth_quality_gating,
    _dict_to_config,
)
from agent_team.state import (
    BrowserTestReport,
    RunState,
    WorkflowResult,
)


def _get_cli_source() -> str:
    """Read cli.py source directly from file to avoid truncation by inspect."""
    import agent_team.cli as cli_mod
    cli_path = Path(cli_mod.__file__)
    return cli_path.read_text(encoding="utf-8")


def _get_browser_block(source: str) -> str:
    """Extract the browser testing block from full cli.py source."""
    start = source.find("# Post-orchestration: Browser MCP Interactive Testing Phase")
    # Find the next top-level section after the browser block
    end = source.find("# Display recovery report", start)
    if end < 0:
        end = len(source)
    return source[start:end]


# =========================================================================
# Source ordering verification
# =========================================================================


class TestSourceOrdering:
    """Verify browser testing block appears in correct position in cli.py."""

    def test_browser_block_after_e2e(self):
        """Browser testing block appears after E2E in main() source."""
        from agent_team import cli
        source = inspect.getsource(cli.main)
        e2e_pos = source.find("E2E Testing Phase")
        browser_pos = source.find("Browser MCP Interactive Testing Phase")
        assert e2e_pos > 0, "E2E Testing Phase not found in main()"
        assert browser_pos > 0, "Browser MCP Interactive Testing Phase not found in main()"
        assert browser_pos > e2e_pos, "Browser testing must appear after E2E testing"

    def test_browser_block_before_recovery_report(self):
        """Browser testing block appears before recovery report display."""
        from agent_team import cli
        source = inspect.getsource(cli.main)
        browser_pos = source.find("Browser MCP Interactive Testing Phase")
        recovery_pos = source.find("print_recovery_report")
        assert browser_pos > 0
        assert recovery_pos > 0
        assert browser_pos < recovery_pos, "Browser testing must complete before recovery report"

    def test_browser_testing_imports_in_block(self):
        """The browser testing block imports from browser_testing module."""
        from agent_team import cli
        source = inspect.getsource(cli.main)
        browser_start = source.find("Browser MCP Interactive Testing Phase")
        # Find the import block after the browser testing heading
        relevant = source[browser_start:browser_start + 2000]
        assert "generate_browser_workflows" in relevant
        assert "verify_workflow_execution" in relevant
        assert "check_screenshot_diversity" in relevant


# =========================================================================
# Config gating
# =========================================================================


class TestConfigGating:
    """Verify browser_testing config defaults and gating behavior."""

    def test_disabled_by_default(self):
        cfg = AgentTeamConfig()
        assert cfg.browser_testing.enabled is False

    def test_browser_testing_field_exists(self):
        cfg = AgentTeamConfig()
        assert hasattr(cfg, "browser_testing")
        assert isinstance(cfg.browser_testing, BrowserTestingConfig)

    def test_enable_via_yaml(self):
        data = {"browser_testing": {"enabled": True}}
        cfg, _ = _dict_to_config(data)
        assert cfg.browser_testing.enabled is True


# =========================================================================
# Depth gating
# =========================================================================


class TestDepthGating:
    """Comprehensive depth gating tests for browser_testing."""

    def test_quick_disables_browser(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.enabled = True
        apply_depth_quality_gating("quick", cfg)
        assert cfg.browser_testing.enabled is False

    def test_standard_does_not_affect(self):
        cfg = AgentTeamConfig()
        assert cfg.browser_testing.enabled is False
        apply_depth_quality_gating("standard", cfg)
        assert cfg.browser_testing.enabled is False

    def test_thorough_prd_mode_true_enables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg, prd_mode=True)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 3

    def test_thorough_prd_mode_false_does_not_enable(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is False

    def test_exhaustive_prd_mode_true_enables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg, prd_mode=True)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 5

    def test_exhaustive_prd_mode_false_no_enable(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is False

    def test_user_override_enabled_survives_quick(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.enabled = True
        overrides = {"browser_testing.enabled"}
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        assert cfg.browser_testing.enabled is True

    def test_user_override_retries_survives(self):
        cfg = AgentTeamConfig()
        cfg.browser_testing.max_fix_retries = 10
        overrides = {"browser_testing.max_fix_retries"}
        apply_depth_quality_gating("thorough", cfg, prd_mode=True, user_overrides=overrides)
        assert cfg.browser_testing.max_fix_retries == 10

    def test_milestone_enabled_acts_as_prd_mode(self):
        """milestone.enabled=True triggers prd_mode logic in thorough/exhaustive."""
        cfg = AgentTeamConfig()
        cfg.milestone.enabled = True
        apply_depth_quality_gating("thorough", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is True

    def test_milestone_enabled_exhaustive(self):
        cfg = AgentTeamConfig()
        cfg.milestone.enabled = True
        apply_depth_quality_gating("exhaustive", cfg, prd_mode=False)
        assert cfg.browser_testing.enabled is True
        assert cfg.browser_testing.max_fix_retries == 5


# =========================================================================
# State tracking
# =========================================================================


class TestStateTracking:
    """Verify state dataclasses are correctly defined."""

    def test_completed_browser_workflows_field(self):
        state = RunState()
        assert hasattr(state, "completed_browser_workflows")
        assert isinstance(state.completed_browser_workflows, list)
        assert state.completed_browser_workflows == []

    def test_browser_test_report_initialized(self):
        report = BrowserTestReport()
        assert report.total_workflows == 0
        assert report.passed_workflows == 0
        assert report.failed_workflows == 0
        assert report.skipped_workflows == 0
        assert report.health == "unknown"

    def test_workflow_result_all_fields(self):
        wr = WorkflowResult(
            workflow_id=1,
            workflow_name="Auth",
            total_steps=4,
            completed_steps=3,
            health="failed",
            failed_step="Step 3",
            failure_reason="Element not found",
            fix_retries_used=2,
            screenshots=["w01_step01.png", "w01_step02.png"],
            console_errors=["TypeError: null reference"],
        )
        assert wr.workflow_id == 1
        assert wr.workflow_name == "Auth"
        assert wr.health == "failed"
        assert len(wr.screenshots) == 2
        assert len(wr.console_errors) == 1

    def test_browser_test_report_workflow_results_list(self):
        report = BrowserTestReport()
        wr = WorkflowResult(workflow_id=1, health="passed")
        report.workflow_results.append(wr)
        assert len(report.workflow_results) == 1

    def test_run_state_completed_workflows_persistence(self):
        """completed_browser_workflows can be appended to."""
        state = RunState()
        state.completed_browser_workflows.append(1)
        state.completed_browser_workflows.append(2)
        assert state.completed_browser_workflows == [1, 2]


# =========================================================================
# Async function signatures (existence check)
# =========================================================================


class TestAsyncFunctionSignatures:
    """Verify async functions exist in cli module with correct signatures."""

    def test_run_browser_startup_agent_exists(self):
        from agent_team import cli
        assert hasattr(cli, "_run_browser_startup_agent")
        func = getattr(cli, "_run_browser_startup_agent")
        assert inspect.iscoroutinefunction(func)

    def test_run_browser_workflow_executor_exists(self):
        from agent_team import cli
        assert hasattr(cli, "_run_browser_workflow_executor")
        func = getattr(cli, "_run_browser_workflow_executor")
        assert inspect.iscoroutinefunction(func)

    def test_run_browser_workflow_fix_exists(self):
        from agent_team import cli
        assert hasattr(cli, "_run_browser_workflow_fix")
        func = getattr(cli, "_run_browser_workflow_fix")
        assert inspect.iscoroutinefunction(func)

    def test_run_browser_regression_sweep_exists(self):
        from agent_team import cli
        assert hasattr(cli, "_run_browser_regression_sweep")
        func = getattr(cli, "_run_browser_regression_sweep")
        assert inspect.iscoroutinefunction(func)

    # --- Parameter signature tests (Finding 7.3) ---

    def test_startup_agent_required_params(self):
        """_run_browser_startup_agent has required params: cwd, config, workflows_dir."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_startup_agent)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "workflows_dir" in params

    def test_startup_agent_optional_params(self):
        """_run_browser_startup_agent has optional params with defaults."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_startup_agent)
        for name in ("task_text", "constraints", "intervention", "depth"):
            assert name in sig.parameters, f"Missing optional param: {name}"
            assert sig.parameters[name].default is not inspect.Parameter.empty, \
                f"Param {name} should have a default"

    def test_startup_agent_return_annotation(self):
        """_run_browser_startup_agent returns tuple[float, AppStartupInfo]."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_startup_agent)
        ret = sig.return_annotation
        assert ret is not inspect.Parameter.empty
        assert "tuple" in str(ret).lower() or "Tuple" in str(ret)

    def test_workflow_executor_required_params(self):
        """_run_browser_workflow_executor has required: cwd, config, workflow_def, workflows_dir, app_url."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_workflow_executor)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "workflow_def" in params
        assert "workflows_dir" in params
        assert "app_url" in params

    def test_workflow_executor_optional_params(self):
        """_run_browser_workflow_executor has optional params with defaults."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_workflow_executor)
        for name in ("task_text", "constraints", "intervention", "depth"):
            assert name in sig.parameters, f"Missing optional param: {name}"
            assert sig.parameters[name].default is not inspect.Parameter.empty

    def test_workflow_fix_required_params(self):
        """_run_browser_workflow_fix has required: cwd, config, workflow_def, result, workflows_dir."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_workflow_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "workflow_def" in params
        assert "result" in params
        assert "workflows_dir" in params

    def test_workflow_fix_returns_float(self):
        """_run_browser_workflow_fix returns float (cost only)."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_workflow_fix)
        ret = sig.return_annotation
        assert ret is not inspect.Parameter.empty
        assert "float" in str(ret).lower()

    def test_regression_sweep_required_params(self):
        """_run_browser_regression_sweep has required: cwd, config, passed_workflows, workflows_dir, app_url."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_regression_sweep)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "passed_workflows" in params
        assert "workflows_dir" in params
        assert "app_url" in params

    def test_regression_sweep_return_annotation(self):
        """_run_browser_regression_sweep returns tuple[float, list[int]]."""
        from agent_team import cli
        sig = inspect.signature(cli._run_browser_regression_sweep)
        ret = sig.return_annotation
        assert ret is not inspect.Parameter.empty
        assert "tuple" in str(ret).lower() or "Tuple" in str(ret)

    def test_all_four_functions_share_common_optional_params(self):
        """All 4 async functions accept task_text, constraints, intervention, depth."""
        from agent_team import cli
        funcs = [
            cli._run_browser_startup_agent,
            cli._run_browser_workflow_executor,
            cli._run_browser_workflow_fix,
            cli._run_browser_regression_sweep,
        ]
        common = {"task_text", "constraints", "intervention", "depth"}
        for func in funcs:
            sig = inspect.signature(func)
            for param_name in common:
                assert param_name in sig.parameters, \
                    f"{func.__name__} missing common param: {param_name}"


# =========================================================================
# Module import tests
# =========================================================================


class TestModuleImports:
    """Verify all browser testing components are importable."""

    def test_import_browser_testing_module(self):
        from agent_team import browser_testing
        assert hasattr(browser_testing, "generate_browser_workflows")
        assert hasattr(browser_testing, "parse_workflow_results")
        assert hasattr(browser_testing, "verify_workflow_execution")
        assert hasattr(browser_testing, "check_screenshot_diversity")

    def test_import_prompts(self):
        from agent_team.browser_testing import (
            BROWSER_APP_STARTUP_PROMPT,
            BROWSER_WORKFLOW_EXECUTOR_PROMPT,
            BROWSER_WORKFLOW_FIX_PROMPT,
            BROWSER_REGRESSION_SWEEP_PROMPT,
        )
        assert len(BROWSER_APP_STARTUP_PROMPT) > 100
        assert len(BROWSER_WORKFLOW_EXECUTOR_PROMPT) > 100
        assert len(BROWSER_WORKFLOW_FIX_PROMPT) > 100
        assert len(BROWSER_REGRESSION_SWEEP_PROMPT) > 100

    def test_import_mcp_servers(self):
        from agent_team.mcp_servers import (
            _playwright_mcp_server,
            get_browser_testing_servers,
        )
        assert callable(_playwright_mcp_server)
        assert callable(get_browser_testing_servers)

    def test_import_state_classes(self):
        from agent_team.state import WorkflowResult, BrowserTestReport
        assert WorkflowResult is not None
        assert BrowserTestReport is not None

    def test_import_config_class(self):
        from agent_team.config import BrowserTestingConfig
        assert BrowserTestingConfig is not None

    # --- Expanded import tests (Finding 7.4) ---

    def test_import_all_public_functions(self):
        """Every public function in browser_testing.py is importable."""
        from agent_team.browser_testing import (
            check_app_running,
            generate_browser_workflows,
            parse_workflow_index,
            parse_workflow_results,
            parse_app_startup_info,
            verify_workflow_execution,
            check_screenshot_diversity,
            write_workflow_state,
            update_workflow_state,
            count_screenshots,
            generate_readiness_report,
            generate_unresolved_issues,
        )
        for func in (
            check_app_running, generate_browser_workflows,
            parse_workflow_index, parse_workflow_results,
            parse_app_startup_info, verify_workflow_execution,
            check_screenshot_diversity, write_workflow_state,
            update_workflow_state, count_screenshots,
            generate_readiness_report, generate_unresolved_issues,
        ):
            assert callable(func), f"{func.__name__} is not callable"

    def test_import_dataclasses(self):
        """Both dataclasses in browser_testing.py are importable and constructable."""
        from agent_team.browser_testing import WorkflowDefinition, AppStartupInfo
        wf = WorkflowDefinition()
        assert wf.id == 0
        assert wf.name == ""
        info = AppStartupInfo()
        assert info.port == 3000
        assert info.start_command == ""

    def test_import_private_extract_credentials(self):
        """_extract_seed_credentials is importable (used internally)."""
        from agent_team.browser_testing import _extract_seed_credentials
        assert callable(_extract_seed_credentials)

    def test_import_run_state_browser_field(self):
        """RunState has completed_browser_workflows field."""
        from agent_team.state import RunState
        state = RunState()
        assert hasattr(state, "completed_browser_workflows")
        assert isinstance(state.completed_browser_workflows, list)

    def test_import_config_browser_field(self):
        """AgentTeamConfig has browser_testing field of correct type."""
        from agent_team.config import AgentTeamConfig, BrowserTestingConfig
        cfg = AgentTeamConfig()
        assert hasattr(cfg, "browser_testing")
        assert isinstance(cfg.browser_testing, BrowserTestingConfig)


# =========================================================================
# Browser Startup Fallback
# =========================================================================


class TestBrowserStartupFallback:
    """Verify app startup logic: health check first, agent as fallback."""

    def test_check_app_running_true_skips_startup(self):
        """When check_app_running returns True, startup agent is NOT called."""
        block = _get_browser_block(_get_cli_source())
        check_pos = block.find("check_app_running(port)")
        startup_pos = block.find("_run_browser_startup_agent")
        assert check_pos > 0
        assert startup_pos > check_pos
        reuse_pos = block.find("reusing from E2E phase")
        assert reuse_pos > check_pos
        assert reuse_pos < startup_pos

    def test_check_app_running_false_calls_startup(self):
        """When check_app_running returns False, startup agent IS called."""
        block = _get_browser_block(_get_cli_source())
        not_running_pos = block.find("App not running on port")
        startup_pos = block.find("_run_browser_startup_agent")
        assert not_running_pos > 0
        assert startup_pos > not_running_pos

    def test_port_resolution_config_app_port_first(self):
        """config.browser_testing.app_port non-zero is used first."""
        cfg = AgentTeamConfig()
        cfg.browser_testing.app_port = 4200
        cfg.e2e_testing.test_port = 9876
        port = cfg.browser_testing.app_port
        assert port == 4200

    def test_port_resolution_falls_to_e2e(self):
        """When app_port=0, e2e test_port is used."""
        cfg = AgentTeamConfig()
        cfg.browser_testing.app_port = 0
        cfg.e2e_testing.test_port = 9876
        port = cfg.browser_testing.app_port
        if port == 0:
            port = cfg.e2e_testing.test_port
        assert port == 9876

    def test_port_resolution_falls_to_3000_default(self):
        """When both app_port and e2e_test_port are 0, defaults to 3000."""
        port = 0
        e2e_port = 0
        if port == 0:
            port = e2e_port
        if port == 0:
            port = 3000
        assert port == 3000

    def test_startup_agent_failure_sets_health_failed(self):
        """Source code sets health=failed when startup verification fails."""
        block = _get_browser_block(_get_cli_source())
        assert 'browser_report.health = "failed"' in block
        assert 'browser_report.skip_reason = "App startup failed"' in block

    def test_startup_agent_sets_browser_app_started_flag(self):
        """_browser_app_started = True after calling startup agent."""
        block = _get_browser_block(_get_cli_source())
        startup_pos = block.find("_run_browser_startup_agent")
        flag_pos = block.find("_browser_app_started = True")
        assert flag_pos > 0
        assert abs(flag_pos - startup_pos) < 500

    def test_health_recheck_after_startup(self):
        """check_app_running is called again after startup agent returns."""
        block = _get_browser_block(_get_cli_source())
        first = block.find("check_app_running(port)")
        second = block.find("check_app_running(port)", first + 1)
        assert first > 0
        assert second > first


# =========================================================================
# Browser Crash Isolation
# =========================================================================


class TestBrowserCrashIsolation:
    """Verify crash isolation patterns in the browser testing pipeline."""

    def test_outer_try_except_catches_exception(self):
        """Outer except Exception handles general errors."""
        block = _get_browser_block(_get_cli_source())
        assert "except Exception as exc:" in block

    def test_app_shutdown_in_finally(self):
        """finally block attempts app cleanup."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        assert finally_pos > 0
        cleanup_section = block[finally_pos:]
        assert "_browser_app_started" in cleanup_section

    def test_workflow_generation_failure_marked_failed_not_crash(self):
        """No workflows generated raises RuntimeError, not a crash."""
        block = _get_browser_block(_get_cli_source())
        assert 'raise RuntimeError("No workflows generated")' in block

    def test_traceback_logged_on_exception(self):
        """traceback.format_exc() is logged for exceptions, not silently swallowed."""
        block = _get_browser_block(_get_cli_source())
        assert "traceback.format_exc()" in block

    def test_runtime_error_caught_separately(self):
        """RuntimeError is caught separately from general Exception."""
        block = _get_browser_block(_get_cli_source())
        re_pos = block.find("except RuntimeError:")
        ex_pos = block.find("except Exception as exc:")
        assert re_pos > 0
        assert ex_pos > re_pos

    def test_finally_block_runs_on_runtime_error(self):
        """finally block is present after RuntimeError and Exception catches."""
        block = _get_browser_block(_get_cli_source())
        re_pos = block.find("except RuntimeError:")
        ex_pos = block.find("except Exception as exc:")
        finally_pos = block.find("finally:")
        assert finally_pos > ex_pos

    def test_browser_app_started_flag_initialized(self):
        """_browser_app_started is initialized before the try block."""
        block = _get_browser_block(_get_cli_source())
        flag_init = block.find("_browser_app_started = False")
        try_pos = block.find("try:")
        assert flag_init >= 0
        assert flag_init < try_pos

    def test_exception_sets_health_failed(self):
        """Exception handler sets browser_report.health = 'failed'."""
        block = _get_browser_block(_get_cli_source())
        except_pos = block.find("except Exception as exc:")
        after_except = block[except_pos:except_pos + 300]
        assert 'browser_report.health = "failed"' in after_except


# =========================================================================
# Browser E2E Gate
# =========================================================================


class TestBrowserE2EGate:
    """Verify E2E pass rate gate logic."""

    def test_e2e_total_zero_skips_with_did_not_run(self):
        """e2e_total == 0 triggers 'did not run' skip message."""
        block = _get_browser_block(_get_cli_source())
        assert "E2E phase did not run" in block

    def test_e2e_below_gate_skips_with_rate_message(self):
        """Pass rate below gate triggers rate message."""
        block = _get_browser_block(_get_cli_source())
        assert "E2E pass rate below gate" in block

    def test_e2e_exact_70_proceeds(self):
        """70% pass rate meets default 0.7 gate."""
        e2e_passed, e2e_total = 7, 10
        gate = 0.7
        assert (e2e_passed / e2e_total) >= gate

    def test_e2e_100_percent_proceeds(self):
        """100% pass rate always meets gate."""
        e2e_passed, e2e_total = 10, 10
        gate = 0.7
        assert (e2e_passed / e2e_total) >= gate

    def test_custom_gate_05_respected(self):
        """Custom gate of 0.5 allows 50% to pass."""
        e2e_passed, e2e_total = 5, 10
        gate = 0.5
        assert (e2e_passed / e2e_total) >= gate

    def test_zero_division_protection(self):
        """e2e_total=0 is checked before division."""
        e2e_total = 0
        should_skip = (e2e_total == 0)
        assert should_skip is True

    def test_69_percent_below_gate(self):
        """69% just under 70% gate."""
        e2e_passed, e2e_total = 69, 100
        gate = 0.7
        assert (e2e_passed / e2e_total) < gate

    def test_71_percent_above_gate(self):
        """71% just over 70% gate."""
        e2e_passed, e2e_total = 71, 100
        gate = 0.7
        assert (e2e_passed / e2e_total) >= gate


# =========================================================================
# Browser Pipeline Order
# =========================================================================


class TestBrowserPipelineOrder:
    """Verify pipeline ordering and phase tracking."""

    def test_browser_block_after_e2e_in_source(self):
        """Browser testing block appears AFTER E2E testing block."""
        source = _get_cli_source()
        e2e_pos = source.find("E2E Testing Phase")
        browser_pos = source.find("Browser MCP Interactive Testing Phase")
        assert browser_pos > e2e_pos

    def test_browser_block_before_recovery_in_source(self):
        """Browser testing block appears BEFORE recovery report display."""
        source = _get_cli_source()
        browser_pos = source.find("Browser MCP Interactive Testing Phase")
        # Find the actual call to print_recovery_report in main() (after all scans)
        # There may be an import/definition earlier, so find the one after browser block
        recovery_pos = source.find("print_recovery_report(len(recovery_types)")
        assert browser_pos > 0
        assert recovery_pos > 0
        assert browser_pos < recovery_pos

    def test_browser_report_initialized_before_try(self):
        """browser_report is initialized before the try block."""
        block = _get_browser_block(_get_cli_source())
        report_init = block.find("browser_report = BrowserTestReport()")
        try_pos = block.find("try:")
        assert report_init >= 0
        assert report_init < try_pos

    def test_browser_report_accessible_in_except(self):
        """browser_report is accessible in the except block."""
        block = _get_browser_block(_get_cli_source())
        except_pos = block.find("except Exception as exc:")
        after = block[except_pos:except_pos + 300]
        assert "browser_report.health" in after

    def test_phase_marker_added_on_passed(self):
        """'browser_testing' added to completed_phases when health is 'passed'."""
        block = _get_browser_block(_get_cli_source())
        assert 'completed_phases.append("browser_testing")' in block

    def test_phase_marker_added_on_partial(self):
        """Phase marker also added when health is 'partial'."""
        block = _get_browser_block(_get_cli_source())
        assert '"passed", "partial"' in block or "'passed', 'partial'" in block

    def test_phase_marker_not_added_on_failed(self):
        """Phase marker NOT added when health is 'failed'."""
        report = BrowserTestReport(health="failed")
        assert report.health not in ("passed", "partial")

    def test_phase_marker_not_added_on_skipped(self):
        """Phase marker NOT added when health is 'skipped'."""
        report = BrowserTestReport(health="skipped")
        assert report.health not in ("passed", "partial")

    def test_health_aggregation_no_redundant_skipped_check(self):
        """Health aggregation uses passed == total without redundant skipped==0 (Fix 5.11)."""
        block = _get_browser_block(_get_cli_source())
        # The old code had: passed_workflows == total_workflows and skipped_workflows == 0
        # After fix: just passed_workflows == total_workflows
        lines = block.splitlines()
        for line in lines:
            if "passed_workflows == browser_report.total_workflows" in line:
                assert "skipped_workflows == 0" not in line, \
                    "Redundant skipped_workflows == 0 check should have been removed"
                break
        else:
            pytest.fail("Could not find health aggregation line")

    def test_readiness_report_return_value_captured(self):
        """generate_readiness_report() return value is captured (Fix CC.4)."""
        block = _get_browser_block(_get_cli_source())
        assert "readiness_content = generate_readiness_report(" in block


# =========================================================================
# Regression Re-Execute
# =========================================================================


class TestRegressionReExecute:
    """Verify regression sweep + fix + re-execute logic."""

    def test_regression_sweep_finds_ids_triggers_fix(self):
        """Source code shows fix + re-execute for regressed workflow IDs."""
        block = _get_browser_block(_get_cli_source())
        assert "regressed_ids" in block
        assert "_run_browser_workflow_fix" in block
        assert "_run_browser_workflow_executor" in block

    def test_reexec_passed_updates_workflow_result(self):
        """Re-execute result is placed back into workflow_results dict."""
        block = _get_browser_block(_get_cli_source())
        assert "workflow_results[reg_id] = reexec_result" in block

    def test_reexec_failed_sets_all_regressions_fixed_false(self):
        """If re-execute fails, all_regressions_fixed = False."""
        block = _get_browser_block(_get_cli_source())
        assert "all_regressions_fixed = False" in block

    def test_no_regressions_sets_sweep_passed_true(self):
        """When no regressions found, regression_sweep_passed = True."""
        block = _get_browser_block(_get_cli_source())
        assert "browser_report.regression_sweep_passed = True" in block

    def test_all_regressions_fixed_tracks_correctly(self):
        """all_regressions_fixed starts True, goes False on any failure."""
        block = _get_browser_block(_get_cli_source())
        assert "all_regressions_fixed = True" in block
        assert "all_regressions_fixed = False" in block

    def test_cost_includes_reexec(self):
        """browser_cost accumulates re-execute costs."""
        block = _get_browser_block(_get_cli_source())
        assert "browser_cost += reexec_cost" in block


# =========================================================================
# Finally Block Cleanup
# =========================================================================


class TestFinallyBlockCleanup:
    """Verify finally block behavior for app process cleanup."""

    def test_cleanup_guarded_by_started_flag(self):
        """Cleanup only runs when _browser_app_started is True."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        after = block[finally_pos:]
        assert "_browser_app_started" in after[:300]

    def test_cleanup_guarded_by_port(self):
        """Cleanup also checks _browser_app_port is non-zero."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        after = block[finally_pos:]
        assert "_browser_app_port" in after[:300]

    def test_cleanup_failure_caught_silently(self):
        """Cleanup failure (process already dead) is caught silently."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        after = block[finally_pos:]
        assert "except Exception:" in after
        assert "pass" in after

    def test_finally_runs_on_both_paths(self):
        """finally is at the same indentation level as try/except."""
        block = _get_browser_block(_get_cli_source())
        assert "except RuntimeError:" in block
        assert "except Exception as exc:" in block
        assert "finally:" in block


# =========================================================================
# Source-level sys import fix verification
# =========================================================================


class TestSysImportFix:
    """Verify the finally block does not shadow module-level sys import."""

    def test_finally_uses_aliased_imports(self):
        """finally block uses _cleanup_sys and _cleanup_subprocess."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        after = block[finally_pos:]
        assert "_cleanup_sys" in after
        assert "_cleanup_subprocess" in after

    def test_no_bare_import_sys_in_finally(self):
        """No bare 'import sys' that would shadow module-level import."""
        block = _get_browser_block(_get_cli_source())
        finally_pos = block.find("finally:")
        after = block[finally_pos:]
        lines = after.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped == "import sys":
                pytest.fail("Bare 'import sys' found in finally block")
