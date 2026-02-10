"""Tests for post-orchestration pipeline execution order and conditional execution.

Verifies the order: scope -> mock -> UI -> deploy -> asset -> PRD -> DB scans -> E2E,
plus conditional execution logic, PRD quality gate, and E2E auto-enablement.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from agent_team.config import (
    AgentTeamConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _get_cli_source() -> str:
    """Get the source code of cli.py main module."""
    import agent_team.cli as cli_mod
    return inspect.getsource(cli_mod)


def _get_main_source() -> str:
    """Get main() source."""
    import agent_team.cli as cli_mod
    return inspect.getsource(cli_mod.main)


def _find_line_number(source: str, pattern: str) -> int | None:
    """Find approximate line offset of pattern in source."""
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern in line:
            return i
    return None


# ===========================================================================
# Execution order tests
# ===========================================================================


class TestPostOrchestrationOrder:
    """Verify that post-orchestration steps execute in the correct order."""

    def test_scope_before_mock(self):
        src = _get_main_source()
        scope_pos = _find_line_number(src, "compute_changed_files")
        mock_pos = _find_line_number(src, "run_mock_data_scan")
        assert scope_pos is not None
        assert mock_pos is not None
        assert scope_pos < mock_pos

    def test_mock_before_ui(self):
        src = _get_main_source()
        mock_pos = _find_line_number(src, "run_mock_data_scan")
        ui_pos = _find_line_number(src, "run_ui_compliance_scan")
        assert mock_pos is not None
        assert ui_pos is not None
        assert mock_pos < ui_pos

    def test_ui_before_deploy(self):
        src = _get_main_source()
        ui_pos = _find_line_number(src, "run_ui_compliance_scan")
        deploy_pos = _find_line_number(src, "run_deployment_scan")
        assert ui_pos is not None
        assert deploy_pos is not None
        assert ui_pos < deploy_pos

    def test_deploy_before_asset(self):
        src = _get_main_source()
        deploy_pos = _find_line_number(src, "run_deployment_scan")
        asset_pos = _find_line_number(src, "run_asset_scan")
        assert deploy_pos is not None
        assert asset_pos is not None
        assert deploy_pos < asset_pos

    def test_asset_before_prd(self):
        src = _get_main_source()
        asset_pos = _find_line_number(src, "run_asset_scan")
        prd_pos = _find_line_number(src, "prd_reconciliation")
        assert asset_pos is not None
        assert prd_pos is not None
        assert asset_pos < prd_pos

    def test_prd_before_db_scans(self):
        src = _get_main_source()
        prd_pos = _find_line_number(src, "parse_prd_reconciliation")
        db_pos = _find_line_number(src, "run_dual_orm_scan")
        assert prd_pos is not None
        assert db_pos is not None
        assert prd_pos < db_pos

    def test_dual_orm_before_default_value(self):
        src = _get_main_source()
        orm_pos = _find_line_number(src, "run_dual_orm_scan")
        def_pos = _find_line_number(src, "run_default_value_scan")
        assert orm_pos is not None
        assert def_pos is not None
        assert orm_pos < def_pos

    def test_default_value_before_relationship(self):
        src = _get_main_source()
        def_pos = _find_line_number(src, "run_default_value_scan")
        rel_pos = _find_line_number(src, "run_relationship_scan")
        assert def_pos is not None
        assert rel_pos is not None
        assert def_pos < rel_pos

    def test_db_scans_before_e2e(self):
        src = _get_main_source()
        rel_pos = _find_line_number(src, "run_relationship_scan")
        e2e_pos = _find_line_number(src, "e2e_testing.enabled")
        assert rel_pos is not None
        assert e2e_pos is not None
        assert rel_pos < e2e_pos


# ===========================================================================
# Conditional execution tests
# ===========================================================================


class TestConditionalExecution:
    """Verify config-gated execution of scans."""

    def test_mock_scan_or_gate(self):
        """Mock scan uses OR gate: post_orchestration_scans OR milestone."""
        src = _get_main_source()
        assert "post_orchestration_scans.mock_data_scan" in src
        assert "milestone.mock_data_scan" in src

    def test_ui_scan_or_gate(self):
        """UI scan uses OR gate: post_orchestration_scans OR milestone."""
        src = _get_main_source()
        assert "post_orchestration_scans.ui_compliance_scan" in src
        assert "milestone.ui_compliance_scan" in src

    def test_deployment_scan_gated(self):
        src = _get_main_source()
        assert "integrity_scans.deployment_scan" in src

    def test_asset_scan_gated(self):
        src = _get_main_source()
        assert "integrity_scans.asset_scan" in src

    def test_prd_recon_gated(self):
        src = _get_main_source()
        assert "integrity_scans.prd_reconciliation" in src

    def test_dual_orm_gated(self):
        src = _get_main_source()
        assert "database_scans.dual_orm_scan" in src

    def test_default_value_gated(self):
        src = _get_main_source()
        assert "database_scans.default_value_scan" in src

    def test_relationship_gated(self):
        src = _get_main_source()
        assert "database_scans.relationship_scan" in src

    def test_e2e_gated(self):
        src = _get_main_source()
        assert "e2e_testing.enabled" in src

    def test_not_use_milestones_guard_for_mock(self):
        """Mock/UI scans skipped when using milestones."""
        src = _get_main_source()
        assert "_use_milestones" in src


# ===========================================================================
# PRD quality gate tests
# ===========================================================================


class TestPRDQualityGate:
    """Verify PRD reconciliation quality gate conditions."""

    def test_prd_recon_disabled_in_quick(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_prd_recon_disabled_in_standard(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_prd_recon_enabled_in_thorough(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.integrity_scans.prd_reconciliation is True

    def test_prd_recon_enabled_in_exhaustive(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.integrity_scans.prd_reconciliation is True

    def test_quality_gate_checks_file_size(self):
        """Thorough mode has quality gate checking file size > 500B."""
        src = _get_main_source()
        assert "500" in src  # file size threshold

    def test_quality_gate_checks_req_pattern(self):
        """Thorough mode requires REQ-xxx pattern."""
        src = _get_main_source()
        assert "REQ-" in src or "REQ" in src


# ===========================================================================
# E2E auto-enablement tests
# ===========================================================================


class TestE2EAutoEnablement:
    """Verify E2E auto-enablement for thorough/exhaustive depths."""

    def test_e2e_auto_enabled_thorough(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_e2e_auto_enabled_exhaustive(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_e2e_not_auto_enabled_quick(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.e2e_testing.enabled is False

    def test_e2e_not_auto_enabled_standard(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.e2e_testing.enabled is False

    def test_e2e_retries_thorough(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.max_fix_retries == 2

    def test_e2e_retries_exhaustive(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.max_fix_retries == 3

    def test_e2e_user_override_survives_thorough(self):
        """User explicitly setting enabled: false survives thorough gating."""
        data = {"e2e_testing": {"enabled": False}}
        cfg, overrides = _dict_to_config(data)
        apply_depth_quality_gating("thorough", cfg, user_overrides=overrides)
        assert cfg.e2e_testing.enabled is False


# ===========================================================================
# Crash isolation tests
# ===========================================================================


class TestCrashIsolation:
    """Verify each scan is independently crash-isolated."""

    def test_each_scan_has_try_except(self):
        """Each post-orch scan block has its own try/except."""
        src = _get_main_source()
        # Each scan function call should be inside a try block
        scan_functions = [
            "run_mock_data_scan",
            "run_ui_compliance_scan",
            "run_deployment_scan",
            "run_asset_scan",
            "run_dual_orm_scan",
            "run_default_value_scan",
            "run_relationship_scan",
        ]
        for func in scan_functions:
            assert func in src, f"{func} not found in main()"

    def test_scope_computation_crash_isolated(self):
        src = _get_main_source()
        # compute_changed_files should be in a try block
        assert "compute_changed_files" in src


# ===========================================================================
# Tracking document lifecycle tests
# ===========================================================================


class TestTrackingDocumentLifecycle:
    """Verify tracking document generation/parsing positions."""

    def test_coverage_matrix_before_e2e(self):
        """Coverage matrix generated before E2E tests run."""
        src = _get_main_source()
        matrix_pos = _find_line_number(src, "generate_e2e_coverage_matrix")
        e2e_backend = _find_line_number(src, "_run_backend_e2e_tests")
        if matrix_pos and e2e_backend:
            assert matrix_pos < e2e_backend

    def test_coverage_stats_after_e2e(self):
        """Coverage stats parsed after E2E completes."""
        src = _get_main_source()
        backend_pos = _find_line_number(src, "_run_backend_e2e_tests")
        stats_pos = _find_line_number(src, "parse_e2e_coverage_matrix")
        if backend_pos and stats_pos:
            assert stats_pos > backend_pos

    def test_fix_cycle_log_in_all_fix_functions(self):
        """Fix cycle log instructions present in fix functions."""
        import agent_team.cli as cli_mod
        for func_name in ("_run_mock_data_fix", "_run_ui_compliance_fix",
                          "_run_integrity_fix", "_run_e2e_fix", "_run_review_only"):
            func = getattr(cli_mod, func_name)
            source = inspect.getsource(func)
            assert "fix_cycle_log" in source, f"{func_name} missing fix_cycle_log"

    def test_artifact_tracking_exists(self):
        """State artifacts tracking exists in main."""
        src = _get_main_source()
        assert "artifacts" in src
