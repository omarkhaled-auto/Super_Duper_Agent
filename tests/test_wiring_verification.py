"""Phase 3: Wiring Verification of cli.py Execution Flow.

Verifies:
  3A — Post-orchestration order (mock scan → UI scan → deploy scan → asset scan → PRD recon → E2E → recovery report)
  3B — Config flag gating (each flag disables its feature)
  3C — Recovery type registration (each scan adds correct type)
  3D — Crash isolation (each check in its own try/except)
  3E — State persistence (save_state at key points, phase markers)
  3F — Function signatures (async functions, return types, parameters)
"""

from __future__ import annotations

import ast
import inspect
import re
import textwrap
from pathlib import Path
from typing import get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — read source once
# ---------------------------------------------------------------------------

_CLI_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"


@pytest.fixture(scope="module")
def cli_source() -> str:
    return _CLI_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cli_lines(cli_source: str) -> list[str]:
    return cli_source.splitlines()


@pytest.fixture(scope="module")
def cli_ast(cli_source: str) -> ast.Module:
    return ast.parse(cli_source, filename=str(_CLI_PATH))


# ===================================================================
# 3A — Post-orchestration order
# ===================================================================

class TestPostOrchestrationOrder:
    """Verify the EXACT sequence of post-orchestration checks in main()."""

    def test_mock_scan_before_ui_scan(self, cli_source: str) -> None:
        """Mock data scan must appear before UI compliance scan."""
        mock_pos = cli_source.find("Post-orchestration: Mock data scan")
        ui_pos = cli_source.find("Post-orchestration: UI compliance scan")
        assert mock_pos != -1, "Mock data scan section not found in cli.py"
        assert ui_pos != -1, "UI compliance scan section not found in cli.py"
        assert mock_pos < ui_pos, "Mock data scan must come before UI compliance scan"

    def test_ui_scan_before_integrity_scans(self, cli_source: str) -> None:
        """UI compliance scan must appear before integrity scans."""
        ui_pos = cli_source.find("Post-orchestration: UI compliance scan")
        integrity_pos = cli_source.find("Post-orchestration: Integrity Scans")
        assert ui_pos != -1
        assert integrity_pos != -1
        assert ui_pos < integrity_pos, "UI scan must come before integrity scans"

    def test_integrity_scans_order(self, cli_source: str) -> None:
        """Within integrity scans: deployment → asset → PRD reconciliation."""
        deploy_pos = cli_source.find("Scan 1: Deployment integrity")
        asset_pos = cli_source.find("Scan 2: Asset integrity")
        prd_pos = cli_source.find("Scan 3: PRD reconciliation")
        assert deploy_pos != -1, "Deployment scan comment not found"
        assert asset_pos != -1, "Asset scan comment not found"
        assert prd_pos != -1, "PRD reconciliation comment not found"
        assert deploy_pos < asset_pos < prd_pos, (
            "Integrity scans must follow order: deployment → asset → PRD"
        )

    def test_e2e_after_integrity_scans(self, cli_source: str) -> None:
        """E2E testing phase must appear after all integrity scans."""
        prd_recon_pos = cli_source.find("Scan 3: PRD reconciliation")
        e2e_pos = cli_source.find("Post-orchestration: E2E Testing Phase")
        assert prd_recon_pos != -1
        assert e2e_pos != -1
        assert prd_recon_pos < e2e_pos, "E2E must come after integrity scans"

    def test_recovery_report_after_e2e(self, cli_source: str) -> None:
        """Recovery report must appear after E2E testing phase."""
        e2e_pos = cli_source.find("Post-orchestration: E2E Testing Phase")
        report_pos = cli_source.find("print_recovery_report(len(recovery_types)")
        assert e2e_pos != -1
        assert report_pos != -1
        assert e2e_pos < report_pos, "Recovery report must come after E2E"

    def test_full_seven_step_order(self, cli_source: str) -> None:
        """Verify the complete 7-step post-orchestration sequence.

        1. Mock data scan
        2. UI compliance scan
        3. Deployment scan
        4. Asset scan
        5. PRD reconciliation
        6. E2E Testing Phase
        7. Recovery report
        """
        markers = [
            "run_mock_data_scan(Path(cwd)",
            "run_ui_compliance_scan(Path(cwd)",
            "run_deployment_scan(Path(cwd))",
            "run_asset_scan(Path(cwd)",
            "_run_prd_reconciliation(",
            "detect_app_type(Path(cwd))",  # E2E entry point
            "print_recovery_report(",
        ]
        # Find positions in main() context (after recovery_types initialization)
        recovery_init = cli_source.find("recovery_types: list[str] = []")
        assert recovery_init != -1
        post_orch = cli_source[recovery_init:]

        positions = []
        for m in markers:
            pos = post_orch.find(m)
            assert pos != -1, f"Marker not found in post-orchestration: {m}"
            positions.append(pos)

        for i in range(len(positions) - 1):
            assert positions[i] < positions[i + 1], (
                f"Order violation: '{markers[i]}' (pos {positions[i]}) "
                f"must come before '{markers[i+1]}' (pos {positions[i+1]})"
            )


# ===================================================================
# 3B — Config → Feature Gating
# ===================================================================

class TestConfigGating:
    """Verify each config flag actually gates its feature."""

    def test_mock_data_scan_gated_by_config(self, cli_source: str) -> None:
        """Mock data scan guarded by post_orchestration_scans OR milestone config."""
        # v6.0: OR gate for backward compat
        assert "config.post_orchestration_scans.mock_data_scan" in cli_source
        assert "config.milestone.mock_data_scan" in cli_source

    def test_ui_compliance_scan_gated_by_config(self, cli_source: str) -> None:
        """UI compliance scan guarded by post_orchestration_scans OR milestone config."""
        assert "config.post_orchestration_scans.ui_compliance_scan" in cli_source
        assert "config.milestone.ui_compliance_scan" in cli_source

    def test_deployment_scan_gated_by_integrity_config(self, cli_source: str) -> None:
        """Deployment scan guarded by `config.integrity_scans.deployment_scan`."""
        assert "config.integrity_scans.deployment_scan" in cli_source

    def test_asset_scan_gated_by_integrity_config(self, cli_source: str) -> None:
        """Asset scan guarded by `config.integrity_scans.asset_scan`."""
        assert "config.integrity_scans.asset_scan" in cli_source

    def test_prd_reconciliation_gated_by_integrity_config(self, cli_source: str) -> None:
        """PRD reconciliation guarded by `config.integrity_scans.prd_reconciliation`."""
        assert "config.integrity_scans.prd_reconciliation" in cli_source

    def test_e2e_gated_by_e2e_enabled(self, cli_source: str) -> None:
        """E2E phase guarded by `config.e2e_testing.enabled`."""
        assert "config.e2e_testing.enabled" in cli_source

    def test_backend_e2e_gated_by_backend_flag(self, cli_source: str) -> None:
        """Backend E2E tests guarded by config.e2e_testing.backend_api_tests."""
        assert "config.e2e_testing.backend_api_tests" in cli_source

    def test_frontend_e2e_gated_by_frontend_flag(self, cli_source: str) -> None:
        """Frontend E2E tests guarded by config.e2e_testing.frontend_playwright_tests."""
        assert "config.e2e_testing.frontend_playwright_tests" in cli_source

    def test_backend_skip_if_no_api(self, cli_source: str) -> None:
        """Backend skip gated by skip_if_no_api + no backend."""
        assert "config.e2e_testing.skip_if_no_api" in cli_source

    def test_frontend_skip_if_no_frontend(self, cli_source: str) -> None:
        """Frontend skip gated by skip_if_no_frontend + no frontend."""
        assert "config.e2e_testing.skip_if_no_frontend" in cli_source

    def test_mock_scan_only_in_standard_mode(self, cli_source: str) -> None:
        """Mock data scan runs only in standard mode (not milestones),
        because milestones handle it per-milestone."""
        # v6.0: OR gate between post_orchestration_scans and milestone config
        pattern = r"if not _use_milestones and \(config\.post_orchestration_scans\.mock_data_scan or config\.milestone\.mock_data_scan\)"
        assert re.search(pattern, cli_source), (
            "Mock data scan must be gated by `not _use_milestones` with OR gate"
        )

    def test_ui_scan_only_in_standard_mode(self, cli_source: str) -> None:
        """UI compliance scan runs only in standard mode."""
        pattern = r"if not _use_milestones and \(config\.post_orchestration_scans\.ui_compliance_scan or config\.milestone\.ui_compliance_scan\)"
        assert re.search(pattern, cli_source), (
            "UI compliance scan must be gated by `not _use_milestones` with OR gate"
        )

    def test_integrity_scans_run_in_both_modes(self, cli_source: str) -> None:
        """Integrity scans are NOT gated by _use_milestones — they run in all modes."""
        # Find the deployment scan if-block
        deploy_section = cli_source[cli_source.find("config.integrity_scans.deployment_scan"):
                                     cli_source.find("config.integrity_scans.deployment_scan") + 200]
        assert "_use_milestones" not in deploy_section.split("\n")[0], (
            "Deployment scan should NOT be gated by _use_milestones"
        )

    def test_e2e_runs_in_both_modes(self, cli_source: str) -> None:
        """E2E testing is NOT gated by _use_milestones — runs in all modes."""
        e2e_line_idx = None
        for i, line in enumerate(cli_source.splitlines()):
            if "config.e2e_testing.enabled" in line and "if" in line:
                e2e_line_idx = i
                break
        assert e2e_line_idx is not None
        e2e_line = cli_source.splitlines()[e2e_line_idx]
        assert "_use_milestones" not in e2e_line, (
            "E2E testing should NOT be gated by _use_milestones"
        )


# ===================================================================
# 3C — Recovery Type Registration
# ===================================================================

class TestRecoveryTypeRegistration:
    """Verify each scan adds the correct recovery type when violations found."""

    def test_mock_data_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("mock_data_fix")' in cli_source

    def test_ui_compliance_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("ui_compliance_fix")' in cli_source

    def test_deployment_integrity_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("deployment_integrity_fix")' in cli_source

    def test_asset_integrity_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("asset_integrity_fix")' in cli_source

    def test_prd_reconciliation_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("prd_reconciliation_mismatch")' in cli_source

    def test_e2e_backend_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("e2e_backend_fix")' in cli_source

    def test_e2e_frontend_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("e2e_frontend_fix")' in cli_source

    def test_contract_generation_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("contract_generation")' in cli_source

    def test_review_recovery_type(self, cli_source: str) -> None:
        assert 'recovery_types.append("review_recovery")' in cli_source

    def test_recovery_types_initialized_as_empty(self, cli_source: str) -> None:
        """recovery_types must be initialized as empty list before all checks."""
        assert "recovery_types: list[str] = []" in cli_source

    def test_recovery_report_uses_recovery_types(self, cli_source: str) -> None:
        """Recovery report is only displayed when recovery_types is non-empty."""
        assert "if recovery_types:" in cli_source
        assert "print_recovery_report(len(recovery_types), recovery_types)" in cli_source

    def test_all_recovery_types_are_unique_strings(self, cli_source: str) -> None:
        """All appended recovery types must be distinct."""
        appends = re.findall(r'recovery_types\.append\("([^"]+)"\)', cli_source)
        # Allow duplicates in code (e.g. different branches), but all values
        # that could be appended must be unique identifiers.
        unique = set(appends)
        assert len(unique) == len(appends), (
            f"Duplicate recovery type names found: {appends}"
        )


# ===================================================================
# 3D — Crash Isolation
# ===================================================================

class TestCrashIsolation:
    """Verify each post-orchestration check has its own try/except block."""

    def _count_try_except_blocks(self, source_section: str) -> int:
        """Count top-level try/except blocks in a source section."""
        try_count = len(re.findall(r'^\s+try:\s*$', source_section, re.MULTILINE))
        except_count = len(re.findall(r'^\s+except\s', source_section, re.MULTILINE))
        return min(try_count, except_count)

    def test_mock_scan_has_own_try_except(self, cli_source: str) -> None:
        """Mock data scan is wrapped in its own try/except."""
        section = cli_source[
            cli_source.find("Post-orchestration: Mock data scan"):
            cli_source.find("Post-orchestration: UI compliance scan")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def test_ui_scan_has_own_try_except(self, cli_source: str) -> None:
        """UI compliance scan is wrapped in its own try/except."""
        section = cli_source[
            cli_source.find("Post-orchestration: UI compliance scan"):
            cli_source.find("Post-orchestration: Integrity Scans")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def test_deployment_scan_has_own_try_except(self, cli_source: str) -> None:
        """Deployment scan has independent crash isolation."""
        section = cli_source[
            cli_source.find("Scan 1: Deployment integrity"):
            cli_source.find("Scan 2: Asset integrity")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def test_asset_scan_has_own_try_except(self, cli_source: str) -> None:
        """Asset scan has independent crash isolation."""
        section = cli_source[
            cli_source.find("Scan 2: Asset integrity"):
            cli_source.find("Scan 3: PRD reconciliation")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def test_prd_reconciliation_has_own_try_except(self, cli_source: str) -> None:
        """PRD reconciliation has independent crash isolation."""
        section = cli_source[
            cli_source.find("Scan 3: PRD reconciliation"):
            cli_source.find("Post-orchestration: E2E Testing Phase")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def test_e2e_phase_has_own_try_except(self, cli_source: str) -> None:
        """E2E testing phase has independent crash isolation."""
        section = cli_source[
            cli_source.find("Post-orchestration: E2E Testing Phase"):
            cli_source.find("Display recovery report")
            if cli_source.find("Display recovery report") != -1
            else cli_source.find("print_recovery_report")
        ]
        assert "try:" in section
        assert "except Exception" in section

    def _get_e2e_section(self, cli_source: str) -> str:
        """Extract E2E testing section (from header to recovery report)."""
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        assert e2e_start != -1, "E2E section not found"
        # Find print_recovery_report AFTER the E2E section start
        report_pos = cli_source.find("print_recovery_report(len(recovery_types)", e2e_start)
        assert report_pos != -1, "print_recovery_report not found after E2E section"
        return cli_source[e2e_start:report_pos]

    def test_outer_e2e_except_logs_traceback(self, cli_source: str) -> None:
        """The outer E2E try/except must log traceback for crash debugging."""
        section = self._get_e2e_section(cli_source)
        assert "traceback.format_exc()" in section, (
            "E2E phase outer except must log traceback"
        )

    def test_e2e_except_sets_health_failed(self, cli_source: str) -> None:
        """Outer E2E except block must set e2e_report.health = 'failed'."""
        section = self._get_e2e_section(cli_source)
        assert 'e2e_report.health = "failed"' in section

    def test_e2e_except_sets_skip_reason(self, cli_source: str) -> None:
        """Outer E2E except block must set e2e_report.skip_reason."""
        section = self._get_e2e_section(cli_source)
        assert "e2e_report.skip_reason" in section


# ===================================================================
# 3E — State Persistence
# ===================================================================

class TestStatePersistence:
    """Verify save_state is called at appropriate points and phase markers are set."""

    def test_e2e_phase_marker_set(self, cli_source: str) -> None:
        """current_phase set to 'e2e_testing' when entering E2E."""
        assert '_current_state.current_phase = "e2e_testing"' in cli_source

    def test_save_state_at_e2e_entry(self, cli_source: str) -> None:
        """save_state called immediately after setting e2e_testing phase."""
        e2e_phase_set = cli_source.find('_current_state.current_phase = "e2e_testing"')
        # Find the next save_state call after phase set
        next_save = cli_source.find("_save_state_e2e", e2e_phase_set)
        assert next_save != -1
        # It should be within a reasonable distance (100 chars)
        assert next_save - e2e_phase_set < 200, (
            "save_state must be called soon after setting e2e_testing phase"
        )

    def test_e2e_backend_phase_appended_on_success(self, cli_source: str) -> None:
        """completed_phases.append('e2e_backend') only when health in (passed, partial)."""
        assert '_current_state.completed_phases.append("e2e_backend")' in cli_source
        # Verify it's gated by health check
        idx = cli_source.find('_current_state.completed_phases.append("e2e_backend")')
        surrounding = cli_source[max(0, idx - 200):idx]
        assert 'api_report.health in ("passed", "partial")' in surrounding, (
            "e2e_backend phase should only be appended when health is passed or partial"
        )

    def test_e2e_frontend_phase_appended_on_success(self, cli_source: str) -> None:
        """completed_phases.append('e2e_frontend') only when health in (passed, partial)."""
        assert '_current_state.completed_phases.append("e2e_frontend")' in cli_source
        idx = cli_source.find('_current_state.completed_phases.append("e2e_frontend")')
        surrounding = cli_source[max(0, idx - 200):idx]
        assert 'pw_report.health in ("passed", "partial")' in surrounding

    def test_e2e_testing_phase_appended_always(self, cli_source: str) -> None:
        """completed_phases.append('e2e_testing') is always appended at end of E2E block."""
        assert '_current_state.completed_phases.append("e2e_testing")' in cli_source

    def test_save_state_after_backend_phase(self, cli_source: str) -> None:
        """save_state called after appending e2e_backend phase."""
        idx = cli_source.find('_current_state.completed_phases.append("e2e_backend")')
        next_save = cli_source.find("_save_state_e2e2", idx)
        assert next_save != -1, "save_state must be called after backend phase completion"
        assert next_save - idx < 200

    def test_save_state_after_frontend_phase(self, cli_source: str) -> None:
        """save_state called after appending e2e_frontend phase."""
        idx = cli_source.find('_current_state.completed_phases.append("e2e_frontend")')
        next_save = cli_source.find("_save_state_e2e3", idx)
        assert next_save != -1, "save_state must be called after frontend phase completion"
        assert next_save - idx < 200

    def test_post_orchestration_phase_set(self, cli_source: str) -> None:
        """Phase set to 'post_orchestration' after orchestration."""
        assert '_current_state.current_phase = "post_orchestration"' in cli_source

    def test_orchestration_phase_appended(self, cli_source: str) -> None:
        """'orchestration' appended to completed_phases."""
        assert '_current_state.completed_phases.append("orchestration")' in cli_source

    def test_post_orchestration_phase_appended(self, cli_source: str) -> None:
        """'post_orchestration' appended to completed_phases."""
        assert '_current_state.completed_phases.append("post_orchestration")' in cli_source

    def test_verification_phase_appended(self, cli_source: str) -> None:
        """'verification' appended to completed_phases."""
        assert '_current_state.completed_phases.append("verification")' in cli_source

    def test_complete_phase_set(self, cli_source: str) -> None:
        """current_phase set to 'complete' after verification."""
        assert '_current_state.current_phase = "complete"' in cli_source

    def test_verification_phase_after_post_orchestration(self, cli_source: str) -> None:
        """verification phase is set after post_orchestration phase completes."""
        post_orch = cli_source.find(
            '_current_state.completed_phases.append("post_orchestration")'
        )
        verify = cli_source.find(
            '_current_state.current_phase = "verification"'
        )
        assert post_orch < verify, (
            "verification phase must come after post_orchestration phase"
        )

    def test_resume_logic_checks_completed_phases(self, cli_source: str) -> None:
        """E2E resume logic checks completed_phases for e2e_backend and e2e_frontend."""
        assert '"e2e_backend" in _current_state.completed_phases' in cli_source
        assert '"e2e_frontend" in _current_state.completed_phases' in cli_source


# ===================================================================
# 3F — Function Signatures
# ===================================================================

class TestFunctionSignatures:
    """Verify all async function signatures match expected contracts."""

    def test_run_backend_e2e_tests_signature(self, cli_source: str) -> None:
        """_run_backend_e2e_tests returns tuple[float, E2ETestReport]."""
        assert "async def _run_backend_e2e_tests(" in cli_source
        # Check return type annotation
        sig_section = cli_source[
            cli_source.find("async def _run_backend_e2e_tests("):
            cli_source.find("async def _run_backend_e2e_tests(") + 500
        ]
        assert "-> tuple[float, E2ETestReport]:" in sig_section

    def test_run_frontend_e2e_tests_signature(self, cli_source: str) -> None:
        """_run_frontend_e2e_tests returns tuple[float, E2ETestReport]."""
        assert "async def _run_frontend_e2e_tests(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_frontend_e2e_tests("):
            cli_source.find("async def _run_frontend_e2e_tests(") + 500
        ]
        assert "-> tuple[float, E2ETestReport]:" in sig_section

    def test_run_e2e_fix_signature(self, cli_source: str) -> None:
        """_run_e2e_fix returns float."""
        assert "async def _run_e2e_fix(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_e2e_fix("):
            cli_source.find("async def _run_e2e_fix(") + 500
        ]
        assert "-> float:" in sig_section

    def test_run_integrity_fix_signature(self, cli_source: str) -> None:
        """_run_integrity_fix returns float."""
        assert "async def _run_integrity_fix(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_integrity_fix("):
            cli_source.find("async def _run_integrity_fix(") + 500
        ]
        assert "-> float:" in sig_section

    def test_run_prd_reconciliation_signature(self, cli_source: str) -> None:
        """_run_prd_reconciliation returns float."""
        assert "async def _run_prd_reconciliation(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_prd_reconciliation("):
            cli_source.find("async def _run_prd_reconciliation(") + 500
        ]
        assert "-> float:" in sig_section

    def test_run_ui_compliance_fix_signature(self, cli_source: str) -> None:
        """_run_ui_compliance_fix returns float."""
        assert "async def _run_ui_compliance_fix(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_ui_compliance_fix("):
            cli_source.find("async def _run_ui_compliance_fix(") + 500
        ]
        assert "-> float:" in sig_section

    def test_run_mock_data_fix_signature(self, cli_source: str) -> None:
        """_run_mock_data_fix returns float."""
        assert "async def _run_mock_data_fix(" in cli_source
        sig_section = cli_source[
            cli_source.find("async def _run_mock_data_fix("):
            cli_source.find("async def _run_mock_data_fix(") + 500
        ]
        assert "-> float:" in sig_section

    def test_run_review_only_has_requirements_path_param(self, cli_source: str) -> None:
        """_run_review_only accepts requirements_path parameter."""
        sig_section = cli_source[
            cli_source.find("def _run_review_only("):
            cli_source.find("def _run_review_only(") + 500
        ]
        assert "requirements_path" in sig_section

    def test_run_review_only_has_depth_param(self, cli_source: str) -> None:
        """_run_review_only accepts depth parameter."""
        sig_section = cli_source[
            cli_source.find("def _run_review_only("):
            cli_source.find("def _run_review_only(") + 500
        ]
        assert "depth" in sig_section

    def test_run_review_only_is_async(self, cli_source: str) -> None:
        """_run_review_only is async to avoid nested asyncio.run() in _run_prd_milestones."""
        assert "async def _run_review_only(" in cli_source

    def test_run_integrity_fix_has_scan_type_param(self, cli_source: str) -> None:
        """_run_integrity_fix accepts scan_type parameter ('deployment' or 'asset')."""
        sig_section = cli_source[
            cli_source.find("async def _run_integrity_fix("):
            cli_source.find("async def _run_integrity_fix(") + 500
        ]
        assert "scan_type" in sig_section

    def test_run_e2e_fix_has_test_type_param(self, cli_source: str) -> None:
        """_run_e2e_fix accepts test_type parameter."""
        sig_section = cli_source[
            cli_source.find("async def _run_e2e_fix("):
            cli_source.find("async def _run_e2e_fix(") + 500
        ]
        assert "test_type" in sig_section

    def test_run_e2e_fix_has_failures_param(self, cli_source: str) -> None:
        """_run_e2e_fix accepts failures list parameter."""
        sig_section = cli_source[
            cli_source.find("async def _run_e2e_fix("):
            cli_source.find("async def _run_e2e_fix(") + 500
        ]
        assert "failures" in sig_section

    def test_all_async_e2e_functions_log_traceback(self, cli_source: str) -> None:
        """All 3 async E2E functions must log traceback on exception."""
        for fn_name in [
            "_run_backend_e2e_tests",
            "_run_frontend_e2e_tests",
            "_run_e2e_fix",
        ]:
            fn_start = cli_source.find(f"async def {fn_name}(")
            # Find next function definition to delimit
            next_fn = cli_source.find("async def ", fn_start + 1)
            if next_fn == -1:
                next_fn = cli_source.find("\ndef ", fn_start + 1)
            fn_body = cli_source[fn_start:next_fn] if next_fn != -1 else cli_source[fn_start:]
            assert "traceback.format_exc()" in fn_body, (
                f"{fn_name} must log traceback.format_exc() in except block"
            )


# ===================================================================
# 3B Extended — Deeper Config Gating Tests (AST-based)
# ===================================================================

class TestConfigGatingAST:
    """AST-based tests that verify config-gating logic more precisely."""

    def test_mock_scan_condition_uses_not_use_milestones(self, cli_ast: ast.Module) -> None:
        """Verify the mock data scan condition includes `not _use_milestones`."""
        # Find all if-statements that reference mock_data_scan
        found = False
        for node in ast.walk(cli_ast):
            if isinstance(node, ast.If):
                source_segment = ast.dump(node.test)
                if "mock_data_scan" in source_segment and "_use_milestones" in source_segment:
                    found = True
                    break
        assert found, "No if-statement found combining _use_milestones and mock_data_scan"

    def test_ui_compliance_condition_uses_not_use_milestones(self, cli_ast: ast.Module) -> None:
        """Verify the UI compliance scan condition includes `not _use_milestones`."""
        found = False
        for node in ast.walk(cli_ast):
            if isinstance(node, ast.If):
                source_segment = ast.dump(node.test)
                if "ui_compliance_scan" in source_segment and "_use_milestones" in source_segment:
                    found = True
                    break
        assert found, "No if-statement found combining _use_milestones and ui_compliance_scan"


# ===================================================================
# 3D Extended — Nested Exception Handling
# ===================================================================

class TestNestedExceptionHandling:
    """Verify inner fix functions also have their own try/except."""

    def test_mock_fix_has_inner_try_except(self, cli_source: str) -> None:
        """Mock data fix within the scan section has its own try/except."""
        section = cli_source[
            cli_source.find("Post-orchestration: Mock data scan"):
            cli_source.find("Post-orchestration: UI compliance scan")
        ]
        # Should have at least 2 try blocks: outer (scan) + inner (fix)
        try_count = section.count("try:")
        assert try_count >= 2, (
            f"Expected at least 2 try blocks in mock scan section, found {try_count}"
        )

    def test_ui_fix_has_inner_try_except(self, cli_source: str) -> None:
        """UI compliance fix within the scan section has its own try/except."""
        section = cli_source[
            cli_source.find("Post-orchestration: UI compliance scan"):
            cli_source.find("Post-orchestration: Integrity Scans")
        ]
        try_count = section.count("try:")
        assert try_count >= 2, (
            f"Expected at least 2 try blocks in UI scan section, found {try_count}"
        )

    def test_deployment_fix_has_inner_try_except(self, cli_source: str) -> None:
        """Deployment integrity fix has its own inner try/except."""
        section = cli_source[
            cli_source.find("Scan 1: Deployment integrity"):
            cli_source.find("Scan 2: Asset integrity")
        ]
        try_count = section.count("try:")
        assert try_count >= 2

    def test_asset_fix_has_inner_try_except(self, cli_source: str) -> None:
        """Asset integrity fix has its own inner try/except."""
        section = cli_source[
            cli_source.find("Scan 2: Asset integrity"):
            cli_source.find("Scan 3: PRD reconciliation")
        ]
        try_count = section.count("try:")
        assert try_count >= 2


# ===================================================================
# 3E Extended — E2E Fix Loop Behavior
# ===================================================================

class TestE2EFixLoopBehavior:
    """Verify E2E fix loop semantics (guards, state updates)."""

    def test_backend_fix_loop_guard(self, cli_source: str) -> None:
        """Backend fix loop only runs when health is not in (passed, skipped, unknown)."""
        assert 'api_report.health not in ("passed", "skipped", "unknown")' in cli_source

    def test_frontend_fix_loop_guard(self, cli_source: str) -> None:
        """Frontend fix loop only runs when health is not in (passed, skipped, unknown)."""
        assert 'pw_report.health not in ("passed", "skipped", "unknown")' in cli_source

    def test_backend_fix_loop_updates_failed_tests(self, cli_source: str) -> None:
        """Backend fix loop updates e2e_report.failed_tests each cycle."""
        # After backend fix loop, failed_tests should be updated with slice copy
        assert "e2e_report.failed_tests = api_report.failed_tests[:]" in cli_source

    def test_frontend_fix_loop_updates_failed_tests(self, cli_source: str) -> None:
        """Frontend fix loop updates e2e_report.failed_tests each cycle."""
        assert "e2e_report.failed_tests = pw_report.failed_tests[:]" in cli_source

    def test_fix_retries_incremented(self, cli_source: str) -> None:
        """fix_retries_used and total_fix_cycles are incremented in fix loops."""
        assert "e2e_report.fix_retries_used += 1" in cli_source
        assert "e2e_report.total_fix_cycles += 1" in cli_source

    def test_backend_70_percent_gate_for_frontend(self, cli_source: str) -> None:
        """Frontend tests gated by 70% backend pass rate."""
        assert "backend_pass_rate >= 0.7" in cli_source

    def test_max_fix_retries_limits_loop(self, cli_source: str) -> None:
        """Fix loops are bounded by config.e2e_testing.max_fix_retries."""
        assert "config.e2e_testing.max_fix_retries" in cli_source

    def test_frontend_skip_no_frontend_message(self, cli_source: str) -> None:
        """Skip message logged when no frontend detected."""
        assert "No frontend detected" in cli_source

    def test_frontend_skip_low_backend_message(self, cli_source: str) -> None:
        """Skip message logged when backend pass rate below 70%."""
        assert "below 70% threshold" in cli_source


# ===================================================================
# 3E Extended — E2E Health Computation
# ===================================================================

class TestE2EHealthComputation:
    """Verify the overall health computation logic for E2E."""

    def test_health_skipped_when_no_tests(self, cli_source: str) -> None:
        """Health is 'skipped' when total == 0."""
        assert 'e2e_report.health = "skipped"' in cli_source

    def test_health_passed_when_all_pass(self, cli_source: str) -> None:
        """Health is 'passed' when passed == total."""
        assert 'e2e_report.health = "passed"' in cli_source

    def test_health_partial_when_70_percent(self, cli_source: str) -> None:
        """Health is 'partial' when >= 70% pass."""
        assert 'e2e_report.health = "partial"' in cli_source

    def test_health_failed_when_below_70(self, cli_source: str) -> None:
        """Health is 'failed' when below 70%."""
        assert 'e2e_report.health = "failed"' in cli_source


# ===================================================================
# 3F Extended — _use_milestones Initialization
# ===================================================================

class TestMilestoneInitialization:
    """Verify _use_milestones is properly initialized."""

    def test_use_milestones_initialized_before_try(self, cli_source: str) -> None:
        """_use_milestones is set to False before the try block."""
        init_pos = cli_source.find("_use_milestones = False")
        try_pos = cli_source.find("try:", init_pos)
        assert init_pos != -1, "_use_milestones = False not found"
        assert init_pos < try_pos, (
            "_use_milestones must be initialized before the try block"
        )

    def test_milestone_convergence_report_initialized_before_try(self, cli_source: str) -> None:
        """milestone_convergence_report initialized before try block."""
        init_pos = cli_source.find("milestone_convergence_report: ConvergenceReport | None = None")
        try_pos = cli_source.find("try:", init_pos)
        assert init_pos != -1
        assert init_pos < try_pos

    def test_use_milestones_set_conditionally_in_else(self, cli_source: str) -> None:
        """_use_milestones is only set to True in the non-interactive (else) branch."""
        # Find where _use_milestones is computed
        compute_pos = cli_source.find("_use_milestones = (\n")
        if compute_pos == -1:
            # Single-line form
            compute_pos = cli_source.find("_use_milestones = (")
        assert compute_pos != -1, "_use_milestones computation not found"
        # Verify it appears after the interactive check
        interactive_check = cli_source.find("if interactive:")
        assert interactive_check < compute_pos


# ===================================================================
# Milestone-level scans (3A extension)
# ===================================================================

class TestMilestoneLevelScans:
    """Verify that milestone mode runs scans per-milestone (not post-orchestration)."""

    def test_milestone_mock_scan_exists(self, cli_source: str) -> None:
        """Per-milestone mock data scan exists in _run_prd_milestones."""
        assert "Post-milestone mock data scan" in cli_source

    def test_milestone_ui_scan_exists(self, cli_source: str) -> None:
        """Per-milestone UI compliance scan exists in _run_prd_milestones."""
        assert "Post-milestone UI compliance scan" in cli_source

    def test_milestone_mock_scan_rescan_after_fix(self, cli_source: str) -> None:
        """Per-milestone mock scan re-scans after fix."""
        section = cli_source[
            cli_source.find("Post-milestone mock data scan"):
            cli_source.find("Post-milestone UI compliance scan")
        ]
        assert "Re-scan after fix" in section

    def test_milestone_ui_scan_rescan_after_fix(self, cli_source: str) -> None:
        """Per-milestone UI scan re-scans after fix."""
        # Find the second "Re-scan after fix"
        first = cli_source.find("Re-scan after fix")
        second = cli_source.find("Re-scan after fix", first + 1)
        assert second != -1, "Second 'Re-scan after fix' not found (for UI scan)"


# ===================================================================
# PRD Reconciliation Prompt (3F extension)
# ===================================================================

class TestPRDReconciliationPrompt:
    """Verify PRD_RECONCILIATION_PROMPT structure."""

    def test_prompt_exists(self, cli_source: str) -> None:
        assert "PRD_RECONCILIATION_PROMPT" in cli_source

    def test_prompt_has_requirements_dir_placeholder(self, cli_source: str) -> None:
        """Prompt uses {requirements_dir} placeholder."""
        prompt_start = cli_source.find('PRD_RECONCILIATION_PROMPT = """')
        assert prompt_start != -1
        prompt_end = cli_source.find('"""', prompt_start + 30)
        prompt = cli_source[prompt_start:prompt_end]
        assert "{requirements_dir}" in prompt

    def test_prompt_has_task_text_placeholder(self, cli_source: str) -> None:
        """Prompt uses {task_text} placeholder."""
        prompt_start = cli_source.find('PRD_RECONCILIATION_PROMPT = """')
        prompt_end = cli_source.find('"""', prompt_start + 30)
        prompt = cli_source[prompt_start:prompt_end]
        assert "{task_text}" in prompt

    def test_prompt_instructs_mismatch_format(self, cli_source: str) -> None:
        """Prompt instructs use of ### MISMATCH header format."""
        prompt_start = cli_source.find('PRD_RECONCILIATION_PROMPT = """')
        prompt_end = cli_source.find('"""', prompt_start + 30)
        prompt = cli_source[prompt_start:prompt_end]
        assert "MISMATCH" in prompt


# ===================================================================
# Cost Tracking (3E extension)
# ===================================================================

class TestCostTracking:
    """Verify costs are accumulated correctly."""

    def test_e2e_cost_added_to_state(self, cli_source: str) -> None:
        """E2E cost is added to _current_state.total_cost."""
        assert "_current_state.total_cost += e2e_cost" in cli_source

    def test_mock_fix_cost_added_to_state(self, cli_source: str) -> None:
        """Mock fix cost is added to state."""
        assert "_current_state.total_cost += mock_fix_cost" in cli_source

    def test_ui_fix_cost_added_to_state(self, cli_source: str) -> None:
        """UI fix cost is added to state."""
        assert "_current_state.total_cost += ui_fix_cost" in cli_source

    def test_deploy_fix_cost_added_to_state(self, cli_source: str) -> None:
        """Deployment fix cost is added to state."""
        assert "_current_state.total_cost += deploy_fix_cost" in cli_source

    def test_asset_fix_cost_added_to_state(self, cli_source: str) -> None:
        """Asset fix cost is added to state."""
        assert "_current_state.total_cost += asset_fix_cost" in cli_source

    def test_prd_recon_cost_added_to_state(self, cli_source: str) -> None:
        """PRD reconciliation cost is added to state."""
        assert "_current_state.total_cost += prd_recon_cost" in cli_source
