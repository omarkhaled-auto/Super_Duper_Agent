"""Tests for depth-based quality gating (v6.0 Mode Upgrade Propagation)."""

import pytest

from agent_team.config import (
    AgentTeamConfig,
    apply_depth_quality_gating,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_config() -> AgentTeamConfig:
    """Return a default AgentTeamConfig (all scans True, E2E False)."""
    return AgentTeamConfig()


# ---------------------------------------------------------------------------
# Quick mode tests
# ---------------------------------------------------------------------------

class TestQuickDepthGating:
    """Quick depth disables all scans and quality features."""

    def test_quick_disables_production_defaults(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.quality.production_defaults is False

    def test_quick_disables_craft_review(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.quality.craft_review is False

    def test_quick_disables_mock_data_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.post_orchestration_scans.mock_data_scan is False
        assert cfg.milestone.mock_data_scan is False

    def test_quick_disables_ui_compliance_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.post_orchestration_scans.ui_compliance_scan is False
        assert cfg.milestone.ui_compliance_scan is False

    def test_quick_disables_deployment_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.integrity_scans.deployment_scan is False

    def test_quick_disables_asset_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.integrity_scans.asset_scan is False

    def test_quick_disables_prd_reconciliation(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_quick_disables_dual_orm_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.database_scans.dual_orm_scan is False

    def test_quick_disables_default_value_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.database_scans.default_value_scan is False

    def test_quick_disables_relationship_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.database_scans.relationship_scan is False

    def test_quick_sets_review_retries_to_zero(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.milestone.review_recovery_retries == 0

    def test_quick_e2e_stays_false(self):
        cfg = _fresh_config()
        assert cfg.e2e_testing.enabled is False
        apply_depth_quality_gating("quick", cfg)
        assert cfg.e2e_testing.enabled is False


# ---------------------------------------------------------------------------
# Standard mode tests
# ---------------------------------------------------------------------------

class TestStandardDepthGating:
    """Standard depth disables PRD reconciliation only."""

    def test_standard_disables_prd_reconciliation(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_standard_keeps_mock_data_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.post_orchestration_scans.mock_data_scan is True

    def test_standard_keeps_ui_compliance_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.post_orchestration_scans.ui_compliance_scan is True

    def test_standard_keeps_deployment_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.deployment_scan is True

    def test_standard_keeps_asset_scan(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.asset_scan is True

    def test_standard_keeps_database_scans(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.database_scans.default_value_scan is True
        assert cfg.database_scans.relationship_scan is True

    def test_standard_keeps_review_retries_at_one(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.milestone.review_recovery_retries == 1

    def test_standard_e2e_stays_false(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.e2e_testing.enabled is False


# ---------------------------------------------------------------------------
# Thorough mode tests
# ---------------------------------------------------------------------------

class TestThoroughDepthGating:
    """Thorough depth auto-enables E2E and bumps retries."""

    def test_thorough_enables_e2e(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_thorough_sets_review_retries_to_two(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.milestone.review_recovery_retries == 2

    def test_thorough_keeps_all_scans_true(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.integrity_scans.asset_scan is True
        assert cfg.integrity_scans.prd_reconciliation is True
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.post_orchestration_scans.mock_data_scan is True


# ---------------------------------------------------------------------------
# Exhaustive mode tests
# ---------------------------------------------------------------------------

class TestExhaustiveDepthGating:
    """Exhaustive depth enables E2E with highest retries."""

    def test_exhaustive_enables_e2e(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_exhaustive_sets_review_retries_to_three(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.milestone.review_recovery_retries == 3

    def test_exhaustive_keeps_all_scans_true(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.integrity_scans.prd_reconciliation is True
        assert cfg.database_scans.dual_orm_scan is True


# ---------------------------------------------------------------------------
# User override tests
# ---------------------------------------------------------------------------

class TestUserOverrides:
    """User-explicit config values are NEVER overridden by depth gating."""

    def test_quick_respects_mock_scan_override(self):
        cfg = _fresh_config()
        overrides = {"post_orchestration_scans.mock_data_scan"}
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.post_orchestration_scans.mock_data_scan is True

    def test_quick_respects_deployment_scan_override(self):
        cfg = _fresh_config()
        overrides = {"integrity_scans.deployment_scan"}
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.integrity_scans.deployment_scan is True

    def test_thorough_respects_e2e_disabled_override(self):
        cfg = _fresh_config()
        overrides = {"e2e_testing.enabled"}
        apply_depth_quality_gating("thorough", cfg, overrides)
        # E2E was False by default, user explicitly set it, so stays False
        assert cfg.e2e_testing.enabled is False

    def test_standard_respects_prd_recon_override(self):
        cfg = _fresh_config()
        overrides = {"integrity_scans.prd_reconciliation"}
        apply_depth_quality_gating("standard", cfg, overrides)
        assert cfg.integrity_scans.prd_reconciliation is True

    def test_quick_respects_multiple_overrides(self):
        cfg = _fresh_config()
        overrides = {
            "integrity_scans.deployment_scan",
            "database_scans.dual_orm_scan",
            "milestone.review_recovery_retries",
        }
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.milestone.review_recovery_retries == 1  # Original default

    def test_quick_respects_milestone_mock_override(self):
        cfg = _fresh_config()
        overrides = {"milestone.mock_data_scan"}
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.milestone.mock_data_scan is True


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """Existing callers without user_overrides still work."""

    def test_no_user_overrides_param(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_none_user_overrides(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg, None)
        assert cfg.post_orchestration_scans.mock_data_scan is False

    def test_empty_set_user_overrides(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("quick", cfg, set())
        assert cfg.post_orchestration_scans.mock_data_scan is False

    def test_unknown_depth_is_noop(self):
        cfg = _fresh_config()
        apply_depth_quality_gating("unknown", cfg)
        # All defaults should be unchanged
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.e2e_testing.enabled is False
        assert cfg.milestone.review_recovery_retries == 1
