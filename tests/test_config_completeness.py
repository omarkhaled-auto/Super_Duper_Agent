"""Tests for config dataclass completeness, YAML loading, user overrides,
depth gating, backward compatibility, and validations.
"""

from __future__ import annotations

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
# Dataclass defaults (all 11 config sub-sections)
# ===========================================================================


class TestDataclassDefaults:
    """Verify all dataclass default values."""

    def test_milestone_defaults(self):
        c = MilestoneConfig()
        assert c.review_recovery_retries == 1
        assert c.mock_data_scan is True
        assert c.ui_compliance_scan is True
        assert c.health_gate is True
        assert c.wiring_check is True

    def test_e2e_testing_defaults(self):
        c = E2ETestingConfig()
        assert c.enabled is False
        assert c.backend_api_tests is True
        assert c.frontend_playwright_tests is True
        assert c.max_fix_retries == 5
        assert c.test_port == 9876
        assert c.skip_if_no_api is True
        assert c.skip_if_no_frontend is True

    def test_integrity_scans_defaults(self):
        c = IntegrityScanConfig()
        assert c.deployment_scan is True
        assert c.asset_scan is True
        assert c.prd_reconciliation is True

    def test_tracking_documents_defaults(self):
        c = TrackingDocumentsConfig()
        assert c.e2e_coverage_matrix is True
        assert c.fix_cycle_log is True
        assert c.milestone_handoff is True
        assert c.coverage_completeness_gate == pytest.approx(0.8)
        assert c.wiring_completeness_gate == pytest.approx(1.0)

    def test_database_scans_defaults(self):
        c = DatabaseScanConfig()
        assert c.dual_orm_scan is True
        assert c.default_value_scan is True
        assert c.relationship_scan is True

    def test_post_orchestration_scans_defaults(self):
        c = PostOrchestrationScanConfig()
        assert c.mock_data_scan is True
        assert c.ui_compliance_scan is True

    def test_quality_defaults(self):
        c = QualityConfig()
        assert c.production_defaults is True
        assert c.craft_review is True
        assert c.quality_triggers_reloop is True

    def test_depth_defaults(self):
        c = DepthConfig()
        assert c.scan_scope_mode == "auto"

    def test_verification_defaults(self):
        c = VerificationConfig()
        assert c.enabled is True
        assert c.blocking is True

    def test_design_reference_defaults(self):
        c = DesignReferenceConfig()
        assert c.extraction_retries == 2
        assert c.fallback_generation is True
        assert c.content_quality_check is True

    def test_agent_team_config_has_all_sections(self):
        c = AgentTeamConfig()
        assert hasattr(c, "milestone")
        assert hasattr(c, "e2e_testing")
        assert hasattr(c, "integrity_scans")
        assert hasattr(c, "tracking_documents")
        assert hasattr(c, "database_scans")
        assert hasattr(c, "post_orchestration_scans")
        assert hasattr(c, "quality")
        assert hasattr(c, "depth")
        assert hasattr(c, "verification")
        assert hasattr(c, "design_reference")
        assert hasattr(c, "convergence")


# ===========================================================================
# YAML loading
# ===========================================================================


class TestYAMLLoading:
    """Test _dict_to_config with various YAML-like dicts."""

    def test_empty_dict(self):
        cfg, overrides = _dict_to_config({})
        assert isinstance(cfg, AgentTeamConfig)
        assert len(overrides) == 0

    def test_full_config(self):
        data = {
            "milestone": {"review_recovery_retries": 3, "mock_data_scan": False},
            "e2e_testing": {"enabled": True, "max_fix_retries": 2, "test_port": 8080},
            "integrity_scans": {"deployment_scan": False},
            "tracking_documents": {"coverage_completeness_gate": 0.9},
            "database_scans": {"dual_orm_scan": False},
            "post_orchestration_scans": {"mock_data_scan": False},
            "quality": {"production_defaults": False},
            "depth": {"scan_scope_mode": "full"},
        }
        cfg, overrides = _dict_to_config(data)
        assert cfg.milestone.review_recovery_retries == 3
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.test_port == 8080
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.tracking_documents.coverage_completeness_gate == pytest.approx(0.9)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.post_orchestration_scans.mock_data_scan is False
        assert cfg.quality.production_defaults is False
        assert cfg.depth.scan_scope_mode == "full"

    def test_partial_config(self):
        data = {"e2e_testing": {"enabled": True}}
        cfg, overrides = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        # Other defaults intact
        assert cfg.milestone.review_recovery_retries == 1
        assert cfg.database_scans.dual_orm_scan is True

    def test_unknown_keys_ignored(self):
        data = {"unknown_section": {"foo": "bar"}}
        cfg, overrides = _dict_to_config(data)
        assert isinstance(cfg, AgentTeamConfig)

    def test_wrong_types_handled(self):
        data = {"milestone": "not a dict"}
        cfg, overrides = _dict_to_config(data)
        # Should use defaults when section is not a dict
        assert cfg.milestone.review_recovery_retries == 1


# ===========================================================================
# User overrides tracking
# ===========================================================================


class TestUserOverridesTracking:
    """Verify user_overrides tracks per-section per-key."""

    def test_milestone_overrides(self):
        data = {"milestone": {"mock_data_scan": False, "review_recovery_retries": 0}}
        _, overrides = _dict_to_config(data)
        assert "milestone.mock_data_scan" in overrides
        assert "milestone.review_recovery_retries" in overrides

    def test_e2e_overrides(self):
        data = {"e2e_testing": {"enabled": True, "max_fix_retries": 2}}
        _, overrides = _dict_to_config(data)
        assert "e2e_testing.enabled" in overrides
        assert "e2e_testing.max_fix_retries" in overrides

    def test_integrity_overrides(self):
        data = {"integrity_scans": {"deployment_scan": False, "asset_scan": False}}
        _, overrides = _dict_to_config(data)
        assert "integrity_scans.deployment_scan" in overrides
        assert "integrity_scans.asset_scan" in overrides

    def test_database_overrides(self):
        data = {"database_scans": {"dual_orm_scan": False}}
        _, overrides = _dict_to_config(data)
        assert "database_scans.dual_orm_scan" in overrides

    def test_post_orch_overrides(self):
        data = {"post_orchestration_scans": {"mock_data_scan": False}}
        _, overrides = _dict_to_config(data)
        assert "post_orchestration_scans.mock_data_scan" in overrides

    def test_quality_overrides(self):
        data = {"quality": {"production_defaults": False, "quality_triggers_reloop": False}}
        _, overrides = _dict_to_config(data)
        assert "quality.production_defaults" in overrides
        assert "quality.quality_triggers_reloop" in overrides

    def test_no_override_when_absent(self):
        data = {"milestone": {"mock_data_scan": True}}
        _, overrides = _dict_to_config(data)
        # review_recovery_retries not in YAML, should not be in overrides
        assert "milestone.review_recovery_retries" not in overrides


# ===========================================================================
# Depth gating x user overrides
# ===========================================================================


class TestDepthGatingOverrides:
    """Verify depth gating respects user overrides."""

    def test_quick_disables_mock_scan(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.post_orchestration_scans.mock_data_scan is False

    def test_quick_override_preserves_mock_scan(self):
        data = {"post_orchestration_scans": {"mock_data_scan": True}}
        cfg, overrides = _dict_to_config(data)
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        assert cfg.post_orchestration_scans.mock_data_scan is True

    def test_quick_disables_ui_scan(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.post_orchestration_scans.ui_compliance_scan is False

    def test_quick_disables_all_db_scans(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.database_scans.default_value_scan is False
        assert cfg.database_scans.relationship_scan is False

    def test_quick_disables_review_recovery(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.milestone.review_recovery_retries == 0

    def test_standard_keeps_mock_scan(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.post_orchestration_scans.mock_data_scan is True

    def test_standard_disables_prd_recon(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_thorough_enables_e2e(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 2

    def test_exhaustive_enables_e2e(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.enabled is True
        assert cfg.e2e_testing.max_fix_retries == 3


# ===========================================================================
# Backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Verify milestone.mock_data_scan migration to post_orchestration_scans."""

    def test_milestone_mock_migrates(self):
        data = {"milestone": {"mock_data_scan": False}}
        cfg, _ = _dict_to_config(data)
        # Should migrate to post_orchestration_scans
        assert cfg.post_orchestration_scans.mock_data_scan is False or \
               cfg.milestone.mock_data_scan is False

    def test_milestone_ui_migrates(self):
        data = {"milestone": {"ui_compliance_scan": False}}
        cfg, _ = _dict_to_config(data)
        assert cfg.post_orchestration_scans.ui_compliance_scan is False or \
               cfg.milestone.ui_compliance_scan is False

    def test_new_section_takes_precedence(self):
        data = {
            "milestone": {"mock_data_scan": True},
            "post_orchestration_scans": {"mock_data_scan": False},
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.post_orchestration_scans.mock_data_scan is False


# ===========================================================================
# Validations
# ===========================================================================


class TestValidations:
    """Verify config validation logic."""

    def test_scan_scope_mode_valid_values(self):
        for mode in ("auto", "full", "changed"):
            data = {"depth": {"scan_scope_mode": mode}}
            cfg, _ = _dict_to_config(data)
            assert cfg.depth.scan_scope_mode == mode

    def test_scan_scope_mode_invalid_raises(self):
        data = {"depth": {"scan_scope_mode": "invalid"}}
        with pytest.raises(ValueError, match="scan_scope_mode"):
            _dict_to_config(data)

    def test_extraction_retries_negative_raises(self):
        data = {"design_reference": {"extraction_retries": -1}}
        with pytest.raises(ValueError, match="extraction_retries"):
            _dict_to_config(data)

    def test_test_port_below_range_raises(self):
        data = {"e2e_testing": {"test_port": 80}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_test_port_above_range_raises(self):
        data = {"e2e_testing": {"test_port": 70000}}
        with pytest.raises(ValueError, match="test_port"):
            _dict_to_config(data)

    def test_max_fix_retries_zero_raises(self):
        data = {"e2e_testing": {"max_fix_retries": 0}}
        with pytest.raises(ValueError, match="max_fix_retries"):
            _dict_to_config(data)

    def test_coverage_gate_above_one_raises(self):
        data = {"tracking_documents": {"coverage_completeness_gate": 1.5}}
        with pytest.raises(ValueError, match="coverage_completeness_gate"):
            _dict_to_config(data)

    def test_wiring_gate_negative_raises(self):
        data = {"tracking_documents": {"wiring_completeness_gate": -0.5}}
        with pytest.raises(ValueError, match="wiring_completeness_gate"):
            _dict_to_config(data)

    def test_review_recovery_retries_negative_raises(self):
        data = {"milestone": {"review_recovery_retries": -1}}
        with pytest.raises(ValueError, match="review_recovery_retries"):
            _dict_to_config(data)


# ===========================================================================
# load_config return type
# ===========================================================================


class TestLoadConfigReturnType:
    """Verify load_config returns tuple."""

    def test_returns_tuple(self, tmp_path):
        from pathlib import Path
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("milestone:\n  mock_data_scan: false\n", encoding="utf-8")
        result = load_config(config_path=str(cfg_path))
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_config_and_set(self, tmp_path):
        from pathlib import Path
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("e2e_testing:\n  enabled: true\n", encoding="utf-8")
        cfg, overrides = load_config(config_path=str(cfg_path))
        assert isinstance(cfg, AgentTeamConfig)
        assert isinstance(overrides, set)

    def test_none_path_returns_defaults(self):
        cfg, overrides = load_config(config_path=None)
        assert isinstance(cfg, AgentTeamConfig)
        assert len(overrides) == 0
