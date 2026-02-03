"""Tests for convergence health check (Agent 2)."""
from __future__ import annotations

import pytest

from agent_team.state import ConvergenceReport
from agent_team.config import (
    AgentTeamConfig,
    ConvergenceConfig,
    parse_per_item_review_cycles,
)
from agent_team.cli import _check_convergence_health


class TestConvergenceReport:
    def test_defaults(self):
        r = ConvergenceReport()
        assert r.total_requirements == 0
        assert r.checked_requirements == 0
        assert r.review_cycles == 0
        assert r.convergence_ratio == 0.0
        assert r.review_fleet_deployed is False
        assert r.health == "unknown"
        assert r.escalated_items == []

    def test_healthy_state(self):
        r = ConvergenceReport(
            total_requirements=10,
            checked_requirements=10,
            review_cycles=3,
            convergence_ratio=1.0,
            review_fleet_deployed=True,
            health="healthy",
        )
        assert r.health == "healthy"
        assert r.review_fleet_deployed is True

    def test_failed_state_zero_cycles(self):
        r = ConvergenceReport(
            total_requirements=20,
            checked_requirements=0,
            review_cycles=0,
            convergence_ratio=0.0,
            review_fleet_deployed=False,
            health="failed",
        )
        assert r.health == "failed"
        assert r.review_fleet_deployed is False

    def test_degraded_state(self):
        r = ConvergenceReport(
            total_requirements=20,
            checked_requirements=12,
            review_cycles=2,
            convergence_ratio=0.6,
            review_fleet_deployed=True,
            health="degraded",
        )
        assert r.health == "degraded"
        assert r.convergence_ratio == pytest.approx(0.6)

    def test_escalated_items_default_empty(self):
        r = ConvergenceReport()
        assert r.escalated_items == []

    def test_escalated_items_populated(self):
        r = ConvergenceReport(
            escalated_items=["REQ-001 (cycles: 3)", "TECH-002 (cycles: 4)"],
        )
        assert len(r.escalated_items) == 2
        assert "REQ-001 (cycles: 3)" in r.escalated_items


class TestParsePerItemReviewCycles:
    def test_single_unchecked_item(self):
        content = "- [ ] REQ-001: Login page (review_cycles: 2)\n"
        result = parse_per_item_review_cycles(content)
        assert result == [("REQ-001", False, 2)]

    def test_single_checked_item(self):
        content = "- [x] REQ-001: Login page (review_cycles: 3)\n"
        result = parse_per_item_review_cycles(content)
        assert result == [("REQ-001", True, 3)]

    def test_mixed_items(self):
        content = (
            "- [x] REQ-001: Login page (review_cycles: 2)\n"
            "- [ ] REQ-002: Signup page (review_cycles: 0)\n"
            "- [ ] TECH-001: Auth middleware (review_cycles: 4)\n"
            "- [x] WIRE-001: Login wired to auth (review_cycles: 1)\n"
        )
        result = parse_per_item_review_cycles(content)
        assert len(result) == 4
        assert result[0] == ("REQ-001", True, 2)
        assert result[1] == ("REQ-002", False, 0)
        assert result[2] == ("TECH-001", False, 4)
        assert result[3] == ("WIRE-001", True, 1)

    def test_no_matching_items(self):
        content = "Some random text without requirements"
        result = parse_per_item_review_cycles(content)
        assert result == []

    def test_all_item_prefixes(self):
        content = (
            "- [ ] REQ-001: Desc (review_cycles: 1)\n"
            "- [ ] TECH-001: Desc (review_cycles: 1)\n"
            "- [ ] INT-001: Desc (review_cycles: 1)\n"
            "- [ ] WIRE-001: Desc (review_cycles: 1)\n"
            "- [ ] DESIGN-001: Desc (review_cycles: 1)\n"
            "- [ ] TEST-001: Desc (review_cycles: 1)\n"
        )
        result = parse_per_item_review_cycles(content)
        assert len(result) == 6
        ids = [item_id for item_id, _, _ in result]
        assert "REQ-001" in ids
        assert "TECH-001" in ids
        assert "INT-001" in ids
        assert "WIRE-001" in ids
        assert "DESIGN-001" in ids
        assert "TEST-001" in ids

    def test_case_insensitive_check_mark(self):
        content = "- [X] REQ-001: Login page (review_cycles: 2)\n"
        result = parse_per_item_review_cycles(content)
        assert result == [("REQ-001", True, 2)]

    def test_multi_digit_ids(self):
        content = (
            "- [ ] REQ-123: Feature 123 (review_cycles: 1)\n"
            "- [x] TECH-042: Middleware setup (review_cycles: 3)\n"
        )
        result = parse_per_item_review_cycles(content)
        assert len(result) == 2
        assert result[0] == ("REQ-123", False, 1)
        assert result[1] == ("TECH-042", True, 3)

    def test_colons_in_description(self):
        content = "- [ ] REQ-001: Auth: OAuth2 flow: token refresh (review_cycles: 2)\n"
        result = parse_per_item_review_cycles(content)
        assert result == [("REQ-001", False, 2)]

    def test_indented_items(self):
        content = "    - [ ] REQ-001: Nested item (review_cycles: 1)\n"
        result = parse_per_item_review_cycles(content)
        assert result == [("REQ-001", False, 1)]


class TestConfigurableThresholds:
    def test_default_min_convergence_ratio(self):
        cfg = ConvergenceConfig()
        assert cfg.min_convergence_ratio == 0.9

    def test_default_recovery_threshold(self):
        cfg = ConvergenceConfig()
        assert cfg.recovery_threshold == 0.8

    def test_default_degraded_threshold(self):
        cfg = ConvergenceConfig()
        assert cfg.degraded_threshold == 0.5

    def test_custom_thresholds(self):
        cfg = ConvergenceConfig(
            min_convergence_ratio=0.95,
            recovery_threshold=0.7,
            degraded_threshold=0.4,
        )
        assert cfg.min_convergence_ratio == 0.95
        assert cfg.recovery_threshold == 0.7
        assert cfg.degraded_threshold == 0.4

    def test_thresholds_from_dict_to_config(self):
        from agent_team.config import _dict_to_config
        data = {"convergence": {
            "min_convergence_ratio": 0.85,
            "recovery_threshold": 0.6,
            "degraded_threshold": 0.3,
        }}
        cfg = _dict_to_config(data)
        assert cfg.convergence.min_convergence_ratio == 0.85
        assert cfg.convergence.recovery_threshold == 0.6
        assert cfg.convergence.degraded_threshold == 0.3

    def test_thresholds_backward_compatible(self):
        """Old config without new fields should use defaults."""
        from agent_team.config import _dict_to_config
        data = {"convergence": {"max_cycles": 5}}
        cfg = _dict_to_config(data)
        assert cfg.convergence.min_convergence_ratio == 0.9
        assert cfg.convergence.recovery_threshold == 0.8
        assert cfg.convergence.degraded_threshold == 0.5


class TestConvergenceConfigValidation:
    def test_valid_defaults_accepted(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig()
        _validate_convergence_config(cfg)  # should not raise

    def test_min_ratio_above_1_raises(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig(min_convergence_ratio=1.5)
        with pytest.raises(ValueError, match="min_convergence_ratio"):
            _validate_convergence_config(cfg)

    def test_min_ratio_negative_raises(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig(min_convergence_ratio=-0.1)
        with pytest.raises(ValueError, match="min_convergence_ratio"):
            _validate_convergence_config(cfg)

    def test_recovery_threshold_above_1_raises(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig(recovery_threshold=2.0)
        with pytest.raises(ValueError, match="recovery_threshold"):
            _validate_convergence_config(cfg)

    def test_degraded_threshold_negative_raises(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig(degraded_threshold=-0.5)
        with pytest.raises(ValueError, match="degraded_threshold"):
            _validate_convergence_config(cfg)

    def test_recovery_exceeds_min_ratio_raises(self):
        from agent_team.config import _validate_convergence_config
        cfg = ConvergenceConfig(min_convergence_ratio=0.8, recovery_threshold=0.95)
        with pytest.raises(ValueError, match="recovery_threshold must be <= min_convergence_ratio"):
            _validate_convergence_config(cfg)

    def test_dict_to_config_validates(self):
        from agent_team.config import _dict_to_config
        data = {"convergence": {"min_convergence_ratio": -1.0}}
        with pytest.raises(ValueError, match="min_convergence_ratio"):
            _dict_to_config(data)

    def test_inverted_thresholds_rejected_by_dict_to_config(self):
        from agent_team.config import _dict_to_config
        data = {"convergence": {
            "min_convergence_ratio": 0.7,
            "recovery_threshold": 0.9,
        }}
        with pytest.raises(ValueError, match="recovery_threshold must be <= min_convergence_ratio"):
            _dict_to_config(data)


class TestCheckConvergenceHealthEnhanced:
    def test_escalated_items_detected(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        (req_dir / "REQUIREMENTS.md").write_text(
            "- [ ] REQ-001: Login (review_cycles: 3)\n"
            "- [x] REQ-002: Signup (review_cycles: 2)\n"
            "- [ ] TECH-001: Auth (review_cycles: 4)\n",
            encoding="utf-8",
        )
        config = AgentTeamConfig()
        config.convergence.escalation_threshold = 3
        report = _check_convergence_health(str(tmp_path), config)
        assert len(report.escalated_items) == 2
        assert "REQ-001 (cycles: 3)" in report.escalated_items
        assert "TECH-001 (cycles: 4)" in report.escalated_items

    def test_no_escalated_items_when_below_threshold(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        (req_dir / "REQUIREMENTS.md").write_text(
            "- [ ] REQ-001: Login (review_cycles: 1)\n"
            "- [ ] REQ-002: Signup (review_cycles: 2)\n",
            encoding="utf-8",
        )
        config = AgentTeamConfig()
        config.convergence.escalation_threshold = 3
        report = _check_convergence_health(str(tmp_path), config)
        assert report.escalated_items == []

    def test_checked_items_not_escalated(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        (req_dir / "REQUIREMENTS.md").write_text(
            "- [x] REQ-001: Login (review_cycles: 5)\n",
            encoding="utf-8",
        )
        config = AgentTeamConfig()
        config.convergence.escalation_threshold = 3
        report = _check_convergence_health(str(tmp_path), config)
        assert report.escalated_items == []

    def test_configurable_min_convergence_ratio(self, tmp_path):
        """Items at 85% should be healthy with min_convergence_ratio=0.8."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        # 17/20 = 0.85
        lines = []
        for i in range(1, 18):
            lines.append(f"- [x] REQ-{i:03d}: Desc (review_cycles: 1)")
        for i in range(18, 21):
            lines.append(f"- [ ] REQ-{i:03d}: Desc (review_cycles: 1)")
        (req_dir / "REQUIREMENTS.md").write_text("\n".join(lines), encoding="utf-8")
        config = AgentTeamConfig()
        config.convergence.min_convergence_ratio = 0.8
        report = _check_convergence_health(str(tmp_path), config)
        assert report.health == "healthy"

    def test_partial_review_detected_as_degraded(self, tmp_path):
        """5/10 checked with review cycles > 0 should be 'degraded' not 'healthy'."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        lines = []
        for i in range(1, 6):
            lines.append(f"- [x] REQ-{i:03d}: Desc (review_cycles: 2)")
        for i in range(6, 11):
            lines.append(f"- [ ] REQ-{i:03d}: Desc (review_cycles: 2)")
        (req_dir / "REQUIREMENTS.md").write_text("\n".join(lines), encoding="utf-8")
        config = AgentTeamConfig()
        report = _check_convergence_health(str(tmp_path), config)
        assert report.convergence_ratio == pytest.approx(0.5)
        assert report.review_fleet_deployed is True
        assert report.health == "degraded"

    def test_no_requirements_file_returns_unknown(self, tmp_path):
        config = AgentTeamConfig()
        report = _check_convergence_health(str(tmp_path), config)
        assert report.health == "unknown"

    def test_all_checked_returns_healthy(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        lines = [f"- [x] REQ-{i:03d}: Desc (review_cycles: 1)" for i in range(1, 6)]
        (req_dir / "REQUIREMENTS.md").write_text("\n".join(lines), encoding="utf-8")
        config = AgentTeamConfig()
        report = _check_convergence_health(str(tmp_path), config)
        assert report.convergence_ratio == pytest.approx(1.0)
        assert report.health == "healthy"

    def test_no_checklist_items_returns_unknown(self, tmp_path):
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        (req_dir / "REQUIREMENTS.md").write_text("# Just a title\nNo items here.", encoding="utf-8")
        config = AgentTeamConfig()
        report = _check_convergence_health(str(tmp_path), config)
        assert report.total_requirements == 0
        assert report.health == "unknown"

    def test_configurable_degraded_threshold(self, tmp_path):
        """With degraded_threshold=0.7, ratio 0.6 should be 'failed' instead of 'degraded'."""
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        lines = []
        for i in range(1, 7):
            lines.append(f"- [x] REQ-{i:03d}: Desc (review_cycles: 2)")
        for i in range(7, 11):
            lines.append(f"- [ ] REQ-{i:03d}: Desc (review_cycles: 2)")
        (req_dir / "REQUIREMENTS.md").write_text("\n".join(lines), encoding="utf-8")
        config = AgentTeamConfig()
        config.convergence.degraded_threshold = 0.7
        report = _check_convergence_health(str(tmp_path), config)
        assert report.convergence_ratio == pytest.approx(0.6)
        assert report.health == "failed"
