"""Tests for config evolution (v6.0 Mode Upgrade Propagation).

Covers PostOrchestrationScanConfig, _dict_to_config tuple return,
user_overrides tracking, load_config tuple return, and scan_scope_mode
validation.
"""

import pytest

from agent_team.config import (
    AgentTeamConfig,
    PostOrchestrationScanConfig,
    _dict_to_config,
    load_config,
)


# ---------------------------------------------------------------------------
# PostOrchestrationScanConfig tests
# ---------------------------------------------------------------------------

class TestPostOrchestrationScanConfig:
    def test_default_values(self):
        cfg = PostOrchestrationScanConfig()
        assert cfg.mock_data_scan is True
        assert cfg.ui_compliance_scan is True

    def test_custom_values(self):
        cfg = PostOrchestrationScanConfig(mock_data_scan=False, ui_compliance_scan=False)
        assert cfg.mock_data_scan is False
        assert cfg.ui_compliance_scan is False

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert hasattr(cfg, "post_orchestration_scans")
        assert isinstance(cfg.post_orchestration_scans, PostOrchestrationScanConfig)
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.post_orchestration_scans.ui_compliance_scan is True


# ---------------------------------------------------------------------------
# _dict_to_config return type tests
# ---------------------------------------------------------------------------

class TestDictToConfigReturnType:
    def test_returns_tuple(self):
        result = _dict_to_config({})
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_first_element_is_config(self):
        cfg, _ = _dict_to_config({})
        assert isinstance(cfg, AgentTeamConfig)

    def test_second_element_is_set(self):
        _, overrides = _dict_to_config({})
        assert isinstance(overrides, set)

    def test_empty_yaml_returns_empty_overrides(self):
        _, overrides = _dict_to_config({})
        assert overrides == set()


# ---------------------------------------------------------------------------
# User overrides tracking — milestone section
# ---------------------------------------------------------------------------

class TestUserOverridesMilestone:
    def test_milestone_mock_data_scan_tracked(self):
        _, overrides = _dict_to_config({"milestone": {"mock_data_scan": True}})
        assert "milestone.mock_data_scan" in overrides

    def test_milestone_ui_compliance_scan_tracked(self):
        _, overrides = _dict_to_config({"milestone": {"ui_compliance_scan": False}})
        assert "milestone.ui_compliance_scan" in overrides

    def test_milestone_review_recovery_retries_tracked(self):
        _, overrides = _dict_to_config({"milestone": {"review_recovery_retries": 2}})
        assert "milestone.review_recovery_retries" in overrides

    def test_milestone_enabled_not_tracked(self):
        _, overrides = _dict_to_config({"milestone": {"enabled": True}})
        assert "milestone.enabled" not in overrides

    def test_multiple_milestone_keys_tracked(self):
        _, overrides = _dict_to_config({
            "milestone": {
                "mock_data_scan": False,
                "review_recovery_retries": 0,
            }
        })
        assert "milestone.mock_data_scan" in overrides
        assert "milestone.review_recovery_retries" in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — e2e_testing section
# ---------------------------------------------------------------------------

class TestUserOverridesE2E:
    def test_e2e_enabled_tracked(self):
        _, overrides = _dict_to_config({"e2e_testing": {"enabled": True}})
        assert "e2e_testing.enabled" in overrides

    def test_e2e_enabled_false_tracked(self):
        _, overrides = _dict_to_config({"e2e_testing": {"enabled": False}})
        assert "e2e_testing.enabled" in overrides

    def test_e2e_max_fix_retries_tracked(self):
        _, overrides = _dict_to_config({"e2e_testing": {"max_fix_retries": 3}})
        assert "e2e_testing.max_fix_retries" in overrides

    def test_e2e_backend_api_tests_not_tracked(self):
        _, overrides = _dict_to_config({"e2e_testing": {"backend_api_tests": True}})
        assert "e2e_testing.backend_api_tests" not in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — integrity_scans section
# ---------------------------------------------------------------------------

class TestUserOverridesIntegrity:
    def test_deployment_scan_tracked(self):
        _, overrides = _dict_to_config({"integrity_scans": {"deployment_scan": False}})
        assert "integrity_scans.deployment_scan" in overrides

    def test_asset_scan_tracked(self):
        _, overrides = _dict_to_config({"integrity_scans": {"asset_scan": True}})
        assert "integrity_scans.asset_scan" in overrides

    def test_prd_reconciliation_tracked(self):
        _, overrides = _dict_to_config({"integrity_scans": {"prd_reconciliation": True}})
        assert "integrity_scans.prd_reconciliation" in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — database_scans section
# ---------------------------------------------------------------------------

class TestUserOverridesDatabase:
    def test_dual_orm_scan_tracked(self):
        _, overrides = _dict_to_config({"database_scans": {"dual_orm_scan": False}})
        assert "database_scans.dual_orm_scan" in overrides

    def test_default_value_scan_tracked(self):
        _, overrides = _dict_to_config({"database_scans": {"default_value_scan": True}})
        assert "database_scans.default_value_scan" in overrides

    def test_relationship_scan_tracked(self):
        _, overrides = _dict_to_config({"database_scans": {"relationship_scan": False}})
        assert "database_scans.relationship_scan" in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — quality section
# ---------------------------------------------------------------------------

class TestUserOverridesQuality:
    def test_production_defaults_tracked(self):
        _, overrides = _dict_to_config({"quality": {"production_defaults": False}})
        assert "quality.production_defaults" in overrides

    def test_craft_review_tracked(self):
        _, overrides = _dict_to_config({"quality": {"craft_review": True}})
        assert "quality.craft_review" in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — post_orchestration_scans section
# ---------------------------------------------------------------------------

class TestUserOverridesPostOrchestration:
    def test_mock_data_scan_tracked(self):
        _, overrides = _dict_to_config({
            "post_orchestration_scans": {"mock_data_scan": False}
        })
        assert "post_orchestration_scans.mock_data_scan" in overrides

    def test_ui_compliance_scan_tracked(self):
        _, overrides = _dict_to_config({
            "post_orchestration_scans": {"ui_compliance_scan": True}
        })
        assert "post_orchestration_scans.ui_compliance_scan" in overrides


# ---------------------------------------------------------------------------
# User overrides tracking — cross-section aggregation
# ---------------------------------------------------------------------------

class TestUserOverridesAggregation:
    def test_multiple_sections(self):
        _, overrides = _dict_to_config({
            "milestone": {"mock_data_scan": True},
            "e2e_testing": {"enabled": False},
            "integrity_scans": {"deployment_scan": True},
            "database_scans": {"dual_orm_scan": False},
            "quality": {"production_defaults": True},
            "post_orchestration_scans": {"ui_compliance_scan": False},
        })
        assert "milestone.mock_data_scan" in overrides
        assert "e2e_testing.enabled" in overrides
        assert "integrity_scans.deployment_scan" in overrides
        assert "database_scans.dual_orm_scan" in overrides
        assert "quality.production_defaults" in overrides
        assert "post_orchestration_scans.ui_compliance_scan" in overrides
        assert len(overrides) == 6


# ---------------------------------------------------------------------------
# PostOrchestrationScanConfig YAML loading
# ---------------------------------------------------------------------------

class TestPostOrchestrationYAML:
    def test_yaml_with_post_orchestration_section(self):
        cfg, _ = _dict_to_config({
            "post_orchestration_scans": {
                "mock_data_scan": False,
                "ui_compliance_scan": True,
            }
        })
        assert cfg.post_orchestration_scans.mock_data_scan is False
        assert cfg.post_orchestration_scans.ui_compliance_scan is True

    def test_yaml_without_section_uses_defaults(self):
        cfg, _ = _dict_to_config({})
        assert cfg.post_orchestration_scans.mock_data_scan is True
        assert cfg.post_orchestration_scans.ui_compliance_scan is True


# ---------------------------------------------------------------------------
# Backward compatibility: milestone -> post_orchestration_scans migration
# ---------------------------------------------------------------------------

class TestBackwardCompatMigration:
    def test_old_milestone_mock_data_scan_migrates(self):
        cfg, _ = _dict_to_config({
            "milestone": {"mock_data_scan": False}
        })
        # Old location migrates to new location
        assert cfg.post_orchestration_scans.mock_data_scan is False

    def test_old_milestone_ui_compliance_scan_migrates(self):
        cfg, _ = _dict_to_config({
            "milestone": {"ui_compliance_scan": False}
        })
        assert cfg.post_orchestration_scans.ui_compliance_scan is False

    def test_post_orchestration_takes_precedence_over_milestone(self):
        cfg, _ = _dict_to_config({
            "milestone": {"mock_data_scan": False},
            "post_orchestration_scans": {"mock_data_scan": True},
        })
        # Explicit post_orchestration_scans takes precedence
        assert cfg.post_orchestration_scans.mock_data_scan is True

    def test_milestone_only_section_still_sets_milestone_config(self):
        cfg, _ = _dict_to_config({
            "milestone": {"mock_data_scan": False, "review_recovery_retries": 2}
        })
        # Milestone config itself is also set
        assert cfg.milestone.mock_data_scan is False
        assert cfg.milestone.review_recovery_retries == 2


# ---------------------------------------------------------------------------
# scan_scope_mode validation
# ---------------------------------------------------------------------------

class TestScanScopeModeValidation:
    def test_auto_is_valid(self):
        cfg, _ = _dict_to_config({"depth": {"scan_scope_mode": "auto"}})
        assert cfg.depth.scan_scope_mode == "auto"

    def test_full_is_valid(self):
        cfg, _ = _dict_to_config({"depth": {"scan_scope_mode": "full"}})
        assert cfg.depth.scan_scope_mode == "full"

    def test_changed_is_valid(self):
        cfg, _ = _dict_to_config({"depth": {"scan_scope_mode": "changed"}})
        assert cfg.depth.scan_scope_mode == "changed"

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError, match="scan_scope_mode"):
            _dict_to_config({"depth": {"scan_scope_mode": "invalid"}})

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="scan_scope_mode"):
            _dict_to_config({"depth": {"scan_scope_mode": ""}})

    def test_default_is_auto(self):
        cfg = AgentTeamConfig()
        assert cfg.depth.scan_scope_mode == "auto"


# ---------------------------------------------------------------------------
# load_config return type
# ---------------------------------------------------------------------------

class TestLoadConfigReturnType:
    def test_returns_tuple(self, tmp_path):
        result = load_config(config_path=tmp_path / "nonexistent.yaml")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_no_config_file_returns_defaults_and_empty_set(self, tmp_path):
        cfg, overrides = load_config(config_path=tmp_path / "nonexistent.yaml")
        assert isinstance(cfg, AgentTeamConfig)
        assert overrides == set()

    def test_config_file_with_overrides(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "milestone:\n  mock_data_scan: true\ne2e_testing:\n  enabled: false\n",
            encoding="utf-8",
        )
        cfg, overrides = load_config(config_path=config_file)
        assert "milestone.mock_data_scan" in overrides
        assert "e2e_testing.enabled" in overrides

    def test_full_yaml_all_sections(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "milestone:\n  mock_data_scan: true\n"
            "e2e_testing:\n  enabled: false\n"
            "integrity_scans:\n  deployment_scan: true\n"
            "database_scans:\n  dual_orm_scan: false\n"
            "quality:\n  production_defaults: true\n"
            "post_orchestration_scans:\n  ui_compliance_scan: false\n",
            encoding="utf-8",
        )
        cfg, overrides = load_config(config_path=config_file)
        assert isinstance(cfg, AgentTeamConfig)
        assert len(overrides) >= 6
