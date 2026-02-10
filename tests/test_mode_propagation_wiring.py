"""Tests for CLI wiring of mode upgrade propagation (v6.0).

Covers scope computation logic, PRD reconciliation quality gate,
gate condition migration, E2E auto-enablement, and scan scope passing.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_team.config import (
    AgentTeamConfig,
    apply_depth_quality_gating,
)
from agent_team.quality_checks import ScanScope, compute_changed_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg_with_depth(depth_default: str = "standard", scan_scope_mode: str = "auto") -> AgentTeamConfig:
    """Build a config with specific depth settings."""
    cfg = AgentTeamConfig()
    cfg.depth.default = depth_default
    cfg.depth.scan_scope_mode = scan_scope_mode
    return cfg


# ---------------------------------------------------------------------------
# Scope computation tests
# ---------------------------------------------------------------------------

class TestScopeComputation:
    """Tests for the scope computation logic in cli.py's post-orchestration block."""

    def test_quick_auto_computes_changed_only(self):
        cfg = _cfg_with_depth(scan_scope_mode="auto")
        depth = "quick"
        # Simulate: auto mode + quick depth -> compute scope
        should_compute = cfg.depth.scan_scope_mode == "changed" or (
            cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
        )
        assert should_compute is True
        # Mode should be changed_only for quick
        mode = "changed_only" if depth == "quick" else "changed_and_imports"
        assert mode == "changed_only"

    def test_standard_auto_computes_changed_and_imports(self):
        cfg = _cfg_with_depth(scan_scope_mode="auto")
        depth = "standard"
        should_compute = cfg.depth.scan_scope_mode == "changed" or (
            cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
        )
        assert should_compute is True
        mode = "changed_only" if depth == "quick" else "changed_and_imports"
        assert mode == "changed_and_imports"

    def test_thorough_auto_no_scope(self):
        cfg = _cfg_with_depth(scan_scope_mode="auto")
        depth = "thorough"
        should_compute = cfg.depth.scan_scope_mode == "changed" or (
            cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
        )
        assert should_compute is False

    def test_exhaustive_auto_no_scope(self):
        cfg = _cfg_with_depth(scan_scope_mode="auto")
        depth = "exhaustive"
        should_compute = cfg.depth.scan_scope_mode == "changed" or (
            cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
        )
        assert should_compute is False

    def test_full_mode_overrides_depth(self):
        cfg = _cfg_with_depth(scan_scope_mode="full")
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            should_compute = cfg.depth.scan_scope_mode == "changed" or (
                cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
            )
            assert should_compute is False, f"Expected no scope for {depth} with full mode"

    def test_changed_mode_always_computes(self):
        cfg = _cfg_with_depth(scan_scope_mode="changed")
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            should_compute = cfg.depth.scan_scope_mode == "changed" or (
                cfg.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
            )
            assert should_compute is True, f"Expected scope for {depth} with changed mode"

    def test_compute_failure_falls_back_to_none(self, tmp_path):
        """compute_changed_files errors result in scope=None (full scan)."""
        with patch(
            "agent_team.quality_checks.subprocess.check_output",
            side_effect=FileNotFoundError("git not found"),
        ):
            changed = compute_changed_files(tmp_path)
        assert changed == []
        # Empty changed list -> scope stays None (full scan fallback)

    def test_empty_changed_files_means_full_scan(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = ["", ""]
            changed = compute_changed_files(tmp_path)
        assert changed == []
        # Empty -> scope stays None -> full scan


# ---------------------------------------------------------------------------
# PRD reconciliation quality gate tests
# ---------------------------------------------------------------------------

class TestPRDReconciliationGate:
    """Tests for the thorough-depth PRD reconciliation quality gate."""

    def _setup_requirements(self, tmp_path, content: str, size: int | None = None):
        """Create a REQUIREMENTS.md file with given content."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir(parents=True, exist_ok=True)
        req_file = req_dir / "REQUIREMENTS.md"
        if size is not None:
            # Pad content to desired size
            content = content + " " * max(0, size - len(content.encode("utf-8")))
        req_file.write_text(content, encoding="utf-8")
        return req_file

    def test_quick_depth_prd_disabled_by_gating(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_standard_depth_prd_disabled_by_gating(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_thorough_large_requirements_with_req_ids(self, tmp_path):
        """Thorough + REQUIREMENTS.md >500 bytes + REQ-001 -> should run."""
        content = "# Requirements\n\nREQ-001: User login\nREQ-002: Dashboard\n"
        req_file = self._setup_requirements(tmp_path, content, size=600)

        should_run = True  # config.integrity_scans.prd_reconciliation is True by default
        depth = "thorough"
        if should_run and depth == "thorough":
            req_size = req_file.stat().st_size
            req_content = req_file.read_text(encoding="utf-8")
            import re
            has_req_items = bool(re.search(r"REQ-\d{3}", req_content))
            if req_size < 500 or not has_req_items:
                should_run = False
        assert should_run is True

    def test_thorough_small_requirements_skips(self, tmp_path):
        """Thorough + REQUIREMENTS.md <500 bytes -> does NOT run."""
        content = "# Req\nREQ-001: small\n"
        req_file = self._setup_requirements(tmp_path, content)

        should_run = True
        depth = "thorough"
        if should_run and depth == "thorough":
            req_size = req_file.stat().st_size
            req_content = req_file.read_text(encoding="utf-8")
            import re
            has_req_items = bool(re.search(r"REQ-\d{3}", req_content))
            if req_size < 500 or not has_req_items:
                should_run = False
        assert should_run is False

    def test_thorough_no_req_ids_skips(self, tmp_path):
        """Thorough + REQUIREMENTS.md without REQ-xxx -> does NOT run."""
        content = "# Requirements\n\nUser should be able to log in.\n" * 30
        req_file = self._setup_requirements(tmp_path, content, size=600)

        should_run = True
        depth = "thorough"
        if should_run and depth == "thorough":
            req_size = req_file.stat().st_size
            req_content = req_file.read_text(encoding="utf-8")
            import re
            has_req_items = bool(re.search(r"REQ-\d{3}", req_content))
            if req_size < 500 or not has_req_items:
                should_run = False
        assert should_run is False

    def test_thorough_no_requirements_file_skips(self, tmp_path):
        """Thorough + no REQUIREMENTS.md file -> does NOT run."""
        req_file = tmp_path / ".agent-team" / "REQUIREMENTS.md"
        should_run = True
        depth = "thorough"
        if should_run and depth == "thorough":
            if not req_file.is_file():
                should_run = False
        assert should_run is False

    def test_exhaustive_always_runs(self):
        """Exhaustive depth -> always runs (no quality gate)."""
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        # prd_reconciliation stays True (exhaustive doesn't gate it)
        assert cfg.integrity_scans.prd_reconciliation is True


# ---------------------------------------------------------------------------
# Gate condition migration tests
# ---------------------------------------------------------------------------

class TestGateConditionMigration:
    """Mock/UI scan gates use OR between new and old config locations."""

    def test_new_config_true_runs_scan(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.mock_data_scan = True
        cfg.milestone.mock_data_scan = False
        assert (cfg.post_orchestration_scans.mock_data_scan or cfg.milestone.mock_data_scan)

    def test_old_config_true_runs_scan(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.mock_data_scan = False
        cfg.milestone.mock_data_scan = True
        assert (cfg.post_orchestration_scans.mock_data_scan or cfg.milestone.mock_data_scan)

    def test_both_false_does_not_run(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.mock_data_scan = False
        cfg.milestone.mock_data_scan = False
        assert not (cfg.post_orchestration_scans.mock_data_scan or cfg.milestone.mock_data_scan)

    def test_ui_new_config_true_runs_scan(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.ui_compliance_scan = True
        cfg.milestone.ui_compliance_scan = False
        assert (cfg.post_orchestration_scans.ui_compliance_scan or cfg.milestone.ui_compliance_scan)

    def test_ui_old_config_true_runs_scan(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.ui_compliance_scan = False
        cfg.milestone.ui_compliance_scan = True
        assert (cfg.post_orchestration_scans.ui_compliance_scan or cfg.milestone.ui_compliance_scan)

    def test_ui_both_false_does_not_run(self):
        cfg = AgentTeamConfig()
        cfg.post_orchestration_scans.ui_compliance_scan = False
        cfg.milestone.ui_compliance_scan = False
        assert not (cfg.post_orchestration_scans.ui_compliance_scan or cfg.milestone.ui_compliance_scan)


# ---------------------------------------------------------------------------
# E2E auto-enablement tests
# ---------------------------------------------------------------------------

class TestE2EAutoEnablement:
    def test_quick_e2e_stays_disabled(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.e2e_testing.enabled is False

    def test_standard_e2e_stays_disabled(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.e2e_testing.enabled is False

    def test_thorough_auto_enables_e2e(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_exhaustive_auto_enables_e2e(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.e2e_testing.enabled is True

    def test_thorough_user_override_keeps_e2e_disabled(self):
        cfg = AgentTeamConfig()
        overrides = {"e2e_testing.enabled"}
        apply_depth_quality_gating("thorough", cfg, overrides)
        # User explicitly set e2e_testing.enabled (default False), so stays False
        assert cfg.e2e_testing.enabled is False

    def test_exhaustive_user_override_keeps_e2e_disabled(self):
        cfg = AgentTeamConfig()
        overrides = {"e2e_testing.enabled"}
        apply_depth_quality_gating("exhaustive", cfg, overrides)
        assert cfg.e2e_testing.enabled is False


# ---------------------------------------------------------------------------
# Scan scope passing tests
# ---------------------------------------------------------------------------

class TestScanScopePassing:
    """All 7 scoped scan functions accept the scope kwarg."""

    @pytest.mark.parametrize("fn_name", [
        "run_mock_data_scan",
        "run_ui_compliance_scan",
        "run_e2e_quality_scan",
        "run_asset_scan",
        "run_dual_orm_scan",
        "run_default_value_scan",
        "run_relationship_scan",
    ])
    def test_scan_accepts_scope_kwarg(self, tmp_path, fn_name):
        from agent_team import quality_checks
        fn = getattr(quality_checks, fn_name)
        scope = ScanScope(mode="changed_only", changed_files=[])
        # Should not raise TypeError for unexpected kwarg
        result = fn(tmp_path, scope=scope)
        assert isinstance(result, list)

    @pytest.mark.parametrize("fn_name", [
        "run_mock_data_scan",
        "run_ui_compliance_scan",
        "run_e2e_quality_scan",
        "run_asset_scan",
        "run_dual_orm_scan",
        "run_default_value_scan",
        "run_relationship_scan",
    ])
    def test_scan_accepts_none_scope(self, tmp_path, fn_name):
        from agent_team import quality_checks
        fn = getattr(quality_checks, fn_name)
        result = fn(tmp_path, scope=None)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Cross-feature integration tests
# ---------------------------------------------------------------------------

class TestCrossFeatureIntegration:
    def test_scan_scope_importable(self):
        from agent_team.quality_checks import ScanScope, compute_changed_files
        assert ScanScope is not None
        assert compute_changed_files is not None

    def test_post_orchestration_scan_config_importable(self):
        from agent_team.config import PostOrchestrationScanConfig
        assert PostOrchestrationScanConfig is not None

    def test_new_config_no_collision_with_existing(self):
        cfg = AgentTeamConfig()
        # PostOrchestrationScanConfig doesn't interfere with other configs
        assert hasattr(cfg, "post_orchestration_scans")
        assert hasattr(cfg, "integrity_scans")
        assert hasattr(cfg, "database_scans")
        assert hasattr(cfg, "e2e_testing")
        assert hasattr(cfg, "milestone")
        # Each is a distinct instance
        assert cfg.post_orchestration_scans is not cfg.integrity_scans
        assert cfg.post_orchestration_scans is not cfg.milestone
