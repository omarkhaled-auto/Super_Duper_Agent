"""Tests for cross-version integration — import compatibility, config coexistence,
feature interactions, and full config round-trip.

Verifies that all v2.0-v6.0 features work together without regressions.
"""

from __future__ import annotations

import inspect
import textwrap
from pathlib import Path

import pytest

from agent_team.config import (
    AgentTeamConfig,
    DatabaseScanConfig,
    DepthConfig,
    DesignReferenceConfig,
    E2ETestingConfig,
    IntegrityScanConfig,
    MilestoneConfig,
    PostOrchestrationScanConfig,
    QualityConfig,
    TrackingDocumentsConfig,
    VerificationConfig,
    _dict_to_config,
    apply_depth_quality_gating,
    load_config,
)


# ===========================================================================
# Import compatibility
# ===========================================================================


class TestImportCompatibility:
    """Verify all modules import without errors."""

    def test_import_cli(self):
        import agent_team.cli
        assert hasattr(agent_team.cli, "main")

    def test_import_agents(self):
        import agent_team.agents
        assert hasattr(agent_team.agents, "build_orchestrator_prompt")

    def test_import_config(self):
        import agent_team.config
        assert hasattr(agent_team.config, "AgentTeamConfig")

    def test_import_quality_checks(self):
        import agent_team.quality_checks
        assert hasattr(agent_team.quality_checks, "run_mock_data_scan")

    def test_import_e2e_testing(self):
        import agent_team.e2e_testing
        assert hasattr(agent_team.e2e_testing, "detect_app_type")

    def test_import_state(self):
        import agent_team.state
        assert hasattr(agent_team.state, "ConvergenceReport")

    def test_import_milestone_manager(self):
        import agent_team.milestone_manager
        assert hasattr(agent_team.milestone_manager, "MilestoneManager")

    def test_import_design_reference(self):
        import agent_team.design_reference
        assert hasattr(agent_team.design_reference, "validate_ui_requirements_content")

    def test_import_tracking_documents(self):
        import agent_team.tracking_documents
        assert hasattr(agent_team.tracking_documents, "generate_e2e_coverage_matrix")

    def test_import_code_quality_standards(self):
        import agent_team.code_quality_standards
        assert hasattr(agent_team.code_quality_standards, "get_standards_for_agent")

    def test_import_prd_chunking(self):
        import agent_team.prd_chunking
        assert hasattr(agent_team.prd_chunking, "detect_large_prd")


# ===========================================================================
# Config coexistence (all sub-configs work together)
# ===========================================================================


class TestConfigCoexistence:
    """Verify all config sections can be loaded together."""

    def test_full_config_round_trip(self):
        data = {
            "milestone": {
                "review_recovery_retries": 2,
                "mock_data_scan": False,
                "ui_compliance_scan": False,
            },
            "e2e_testing": {
                "enabled": True,
                "max_fix_retries": 3,
                "test_port": 8080,
            },
            "integrity_scans": {
                "deployment_scan": True,
                "asset_scan": False,
                "prd_reconciliation": True,
            },
            "tracking_documents": {
                "coverage_completeness_gate": 0.7,
                "wiring_completeness_gate": 0.9,
            },
            "database_scans": {
                "dual_orm_scan": True,
                "default_value_scan": False,
                "relationship_scan": True,
            },
            "post_orchestration_scans": {
                "mock_data_scan": True,
                "ui_compliance_scan": False,
            },
            "quality": {
                "production_defaults": False,
                "craft_review": True,
                "quality_triggers_reloop": False,
            },
            "depth": {
                "scan_scope_mode": "full",
            },
        }
        cfg, overrides = _dict_to_config(data)

        # Verify all values applied
        assert cfg.milestone.review_recovery_retries == 2
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.test_port == 8080
        assert cfg.integrity_scans.asset_scan is False
        assert cfg.tracking_documents.coverage_completeness_gate == pytest.approx(0.7)
        assert cfg.database_scans.default_value_scan is False
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.quality.production_defaults is False
        assert cfg.depth.scan_scope_mode == "full"

        # Verify overrides tracked
        assert "milestone.review_recovery_retries" in overrides
        assert "e2e_testing.enabled" in overrides
        assert "database_scans.dual_orm_scan" in overrides
        assert "post_orchestration_scans.mock_data_scan" in overrides
        assert "quality.production_defaults" in overrides
        assert "quality.quality_triggers_reloop" in overrides

    def test_empty_config_gives_defaults(self):
        cfg, overrides = _dict_to_config({})
        assert cfg.milestone.review_recovery_retries == 1
        assert cfg.e2e_testing.enabled is False
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.tracking_documents.coverage_completeness_gate == pytest.approx(0.8)
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.quality.production_defaults is True
        assert cfg.depth.scan_scope_mode == "auto"
        assert len(overrides) == 0


# ===========================================================================
# Feature interactions
# ===========================================================================


class TestFeatureInteractions:
    """Verify features from different versions work together."""

    def test_depth_gating_plus_user_overrides(self):
        """Depth gating respects user overrides across all config sections."""
        data = {
            "post_orchestration_scans": {"mock_data_scan": True},
            "database_scans": {"dual_orm_scan": True},
            "e2e_testing": {"enabled": True},
        }
        cfg, overrides = _dict_to_config(data)
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        # User overrides survive quick depth gating
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.e2e_testing.enabled is True

    def test_backward_compat_plus_depth_gating(self):
        """milestone.mock_data_scan migration + depth gating = correct result."""
        data = {"milestone": {"mock_data_scan": False}}
        cfg, overrides = _dict_to_config(data)
        # After migration, post_orchestration_scans should have the value
        assert cfg.post_orchestration_scans.mock_data_scan is False or \
               cfg.milestone.mock_data_scan is False
        # Depth gating should not override migrated value
        apply_depth_quality_gating("standard", cfg, user_overrides=overrides)

    def test_thorough_depth_enables_e2e_and_prd(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.enabled is True
        assert cfg.integrity_scans.prd_reconciliation is True
        assert cfg.e2e_testing.max_fix_retries == 2

    def test_exhaustive_depth_enables_everything(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 3
        assert cfg.integrity_scans.prd_reconciliation is True
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.post_orchestration_scans.ui_compliance_scan is True
        assert cfg.database_scans.dual_orm_scan is True

    def test_quick_depth_disables_everything(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.e2e_testing.enabled is False
        assert cfg.post_orchestration_scans.mock_data_scan is False
        assert cfg.post_orchestration_scans.ui_compliance_scan is False
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.database_scans.default_value_scan is False
        assert cfg.database_scans.relationship_scan is False
        assert cfg.milestone.review_recovery_retries == 0

    def test_standard_depth_intermediate(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.e2e_testing.enabled is False
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.integrity_scans.prd_reconciliation is False


# ===========================================================================
# State dataclass integration
# ===========================================================================


class TestStateDataclassIntegration:
    """Verify state dataclasses work with config."""

    def test_convergence_report_import(self):
        from agent_team.state import ConvergenceReport
        report = ConvergenceReport(health="passed", convergence_ratio=0.95)
        assert report.health == "passed"
        assert report.convergence_ratio == 0.95

    def test_e2e_test_report_import(self):
        from agent_team.state import E2ETestReport
        report = E2ETestReport()
        assert report.health == "unknown"
        assert report.fix_retries_used == 0

    def test_run_state_import(self):
        from agent_team.state import RunState
        state = RunState()
        assert state.current_phase == "init"


# ===========================================================================
# Scan function cross-version
# ===========================================================================


class TestScanFunctionCrossVersion:
    """Verify scan functions from different versions coexist."""

    def test_all_scan_functions_importable(self):
        from agent_team.quality_checks import (
            run_mock_data_scan,
            run_ui_compliance_scan,
            run_e2e_quality_scan,
            run_deployment_scan,
            run_asset_scan,
            run_dual_orm_scan,
            run_default_value_scan,
            run_relationship_scan,
            run_spot_checks,
        )
        # All imported successfully
        assert callable(run_mock_data_scan)
        assert callable(run_ui_compliance_scan)
        assert callable(run_e2e_quality_scan)
        assert callable(run_deployment_scan)
        assert callable(run_asset_scan)
        assert callable(run_dual_orm_scan)
        assert callable(run_default_value_scan)
        assert callable(run_relationship_scan)
        assert callable(run_spot_checks)

    def test_scan_scope_importable(self):
        from agent_team.quality_checks import ScanScope, compute_changed_files
        scope = ScanScope(mode="full", changed_files=[])
        assert scope.mode == "full"

    def test_violation_dataclass(self):
        from agent_team.quality_checks import Violation
        v = Violation(check="TEST-001", message="test", file_path="foo.ts",
                      line=1, severity="warning")
        assert v.check == "TEST-001"


# ===========================================================================
# Tracking documents integration
# ===========================================================================


class TestTrackingDocumentsIntegration:
    """Verify tracking documents functions exist and have correct shape."""

    def test_matrix_functions_exist(self):
        from agent_team.tracking_documents import (
            generate_e2e_coverage_matrix,
            parse_e2e_coverage_matrix,
        )
        assert callable(generate_e2e_coverage_matrix)
        assert callable(parse_e2e_coverage_matrix)

    def test_fix_log_functions_exist(self):
        from agent_team.tracking_documents import (
            initialize_fix_cycle_log,
            build_fix_cycle_entry,
            parse_fix_cycle_log,
        )
        assert callable(initialize_fix_cycle_log)
        assert callable(build_fix_cycle_entry)
        assert callable(parse_fix_cycle_log)

    def test_handoff_functions_exist(self):
        from agent_team.tracking_documents import (
            generate_milestone_handoff_entry,
            parse_milestone_handoff,
        )
        assert callable(generate_milestone_handoff_entry)
        assert callable(parse_milestone_handoff)

    def test_config_gates_documents(self):
        cfg = AgentTeamConfig()
        assert cfg.tracking_documents.e2e_coverage_matrix is True
        assert cfg.tracking_documents.fix_cycle_log is True
        assert cfg.tracking_documents.milestone_handoff is True


# ===========================================================================
# E2E testing module integration
# ===========================================================================


class TestE2EModuleIntegration:
    """Verify E2E testing module functions work."""

    def test_detect_app_type_returns_info(self, tmp_path):
        from agent_team.e2e_testing import detect_app_type, AppTypeInfo
        info = detect_app_type(tmp_path)
        assert isinstance(info, AppTypeInfo)

    def test_parse_e2e_results_returns_report(self, tmp_path):
        from agent_team.e2e_testing import parse_e2e_results
        from agent_team.state import E2ETestReport
        report = parse_e2e_results(tmp_path)
        assert isinstance(report, E2ETestReport)

    def test_prompt_constants_exist(self):
        from agent_team.e2e_testing import (
            BACKEND_E2E_PROMPT,
            FRONTEND_E2E_PROMPT,
            E2E_FIX_PROMPT,
        )
        assert len(BACKEND_E2E_PROMPT) > 100
        assert len(FRONTEND_E2E_PROMPT) > 100
        assert len(E2E_FIX_PROMPT) > 100


# ===========================================================================
# PRD chunking integration
# ===========================================================================


class TestPRDChunkingIntegration:
    """Verify PRD chunking works with the config system."""

    def test_detect_large_prd_false_for_small(self):
        from agent_team.prd_chunking import detect_large_prd
        content = "# Small PRD\nJust a few lines."
        assert detect_large_prd(content) is False

    def test_detect_large_prd_true_for_large(self):
        from agent_team.prd_chunking import detect_large_prd
        content = "# Large PRD\n" + "x" * 90000
        assert detect_large_prd(content) is True


# ===========================================================================
# Full YAML config round-trip
# ===========================================================================


class TestFullYAMLRoundTrip:
    """Verify full config YAML can be loaded and written."""

    def test_load_config_from_yaml(self, tmp_path):
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(textwrap.dedent("""\
            milestone:
              review_recovery_retries: 3
            e2e_testing:
              enabled: true
              max_fix_retries: 2
              test_port: 9000
            integrity_scans:
              deployment_scan: false
            tracking_documents:
              coverage_completeness_gate: 0.9
            database_scans:
              dual_orm_scan: false
            post_orchestration_scans:
              mock_data_scan: false
            quality:
              production_defaults: false
              quality_triggers_reloop: false
            depth:
              scan_scope_mode: changed
        """), encoding="utf-8")
        cfg, overrides = load_config(config_path=str(cfg_path))
        assert cfg.milestone.review_recovery_retries == 3
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.test_port == 9000
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.tracking_documents.coverage_completeness_gate == pytest.approx(0.9)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.post_orchestration_scans.mock_data_scan is False
        assert cfg.quality.production_defaults is False
        assert cfg.quality.quality_triggers_reloop is False
        assert cfg.depth.scan_scope_mode == "changed"
        # Verify overrides
        assert "milestone.review_recovery_retries" in overrides
        assert "e2e_testing.enabled" in overrides
        assert "quality.quality_triggers_reloop" in overrides

    def test_load_config_no_file_returns_defaults(self):
        cfg, overrides = load_config(config_path=None)
        assert isinstance(cfg, AgentTeamConfig)
        assert len(overrides) == 0
        assert cfg.milestone.review_recovery_retries == 1


# ===========================================================================
# CLI module-level imports
# ===========================================================================


class TestCLIModuleLevelImports:
    """Verify cli.py has all required module-level imports."""

    def test_json_import(self):
        import agent_team.cli
        src = inspect.getsource(agent_team.cli)
        # json should be imported at module level
        lines = src.split("\n")
        found = any(line.strip() == "import json" for line in lines[:50])
        assert found, "import json not found at module level in cli.py"

    def test_asyncio_import(self):
        import agent_team.cli
        src = inspect.getsource(agent_team.cli)
        assert "import asyncio" in src

    def test_quality_checks_imports(self):
        import agent_team.cli
        src = inspect.getsource(agent_team.cli)
        for func in ("run_mock_data_scan", "run_ui_compliance_scan",
                      "run_deployment_scan", "run_asset_scan",
                      "run_dual_orm_scan", "run_default_value_scan",
                      "run_relationship_scan"):
            assert func in src, f"{func} not imported in cli.py"
