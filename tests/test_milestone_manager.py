"""Tests for milestone manager (Agents 17, 18)."""
from __future__ import annotations

import pytest
from pathlib import Path

from agent_team.milestone_manager import MilestoneManager, MilestoneState, WiringGap


def _setup_milestone(tmp_path: Path, milestone_id: str, content: str) -> None:
    """Helper to create a milestone REQUIREMENTS.md."""
    milestone_dir = tmp_path / ".agent-team" / "milestones" / milestone_id
    milestone_dir.mkdir(parents=True, exist_ok=True)
    (milestone_dir / "REQUIREMENTS.md").write_text(content, encoding="utf-8")


class TestMilestoneState:
    def test_defaults(self):
        s = MilestoneState(milestone_id="M1")
        assert s.requirements_total == 0
        assert s.requirements_checked == 0
        assert s.convergence_cycles == 0
        assert s.status == "pending"


class TestCheckMilestoneHealth:
    def test_missing_milestone(self, tmp_path):
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("nonexistent")
        assert report.health == "unknown"

    def test_empty_requirements(self, tmp_path):
        _setup_milestone(tmp_path, "M1", "")
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.health == "unknown"

    def test_all_checked(self, tmp_path):
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n(review_cycles: 3)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.total_requirements == 2
        assert report.checked_requirements == 2
        assert report.review_cycles == 3
        assert report.health == "healthy"

    def test_partial_checked_degraded(self, tmp_path):
        # ratio = 2/3 = 0.67 (>= 0.5) AND cycles = 1 (> 0) → degraded
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.total_requirements == 3
        assert report.checked_requirements == 2
        assert report.health == "degraded"

    def test_partial_checked_failed(self, tmp_path):
        # ratio = 1/3 = 0.33 (< 0.5) with cycles = 1 → still failed (need BOTH conditions)
        content = "# Requirements\n- [x] Feature A\n- [ ] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.health == "failed"

    def test_none_checked_no_cycles(self, tmp_path):
        content = "# Requirements\n- [ ] Feature A\n- [ ] Feature B\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.review_cycles == 0
        assert report.health == "failed"

    def test_configurable_min_convergence_ratio(self, tmp_path):
        # ratio = 2/3 = 0.67 — with default 0.9 this is "degraded", but with 0.6 it's "healthy"
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1", min_convergence_ratio=0.6)
        assert report.health == "healthy"

    def test_default_threshold_backward_compatible(self, tmp_path):
        # ratio = 2/3 = 0.67, cycles > 0 → "degraded" with default 0.9
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report_default = mgr.check_milestone_health("M1")
        report_explicit = mgr.check_milestone_health("M1", min_convergence_ratio=0.9)
        assert report_default.health == report_explicit.health == "degraded"

    def test_configurable_degraded_threshold(self, tmp_path):
        # ratio = 2/3 = 0.67, cycles > 0. Default degraded_threshold=0.5 → "degraded".
        # With degraded_threshold=0.7 → "failed" (0.67 < 0.7).
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1", degraded_threshold=0.7)
        assert report.health == "failed"


class TestCrossMilestoneWiring:
    def test_no_milestones(self, tmp_path):
        mgr = MilestoneManager(tmp_path)
        gaps = mgr.get_cross_milestone_wiring()
        assert gaps == []

    def test_no_cross_refs(self, tmp_path):
        _setup_milestone(tmp_path, "M1", "- [x] Build src/auth/login.ts\n")
        _setup_milestone(tmp_path, "M2", "- [x] Build src/dashboard/home.ts\n")
        mgr = MilestoneManager(tmp_path)
        gaps = mgr.get_cross_milestone_wiring()
        assert gaps == []

    def test_detects_missing_file(self, tmp_path):
        _setup_milestone(tmp_path, "M1", "- [x] Create src/services/auth.ts\n")
        _setup_milestone(tmp_path, "M2", "- [ ] Import from src/services/auth.ts\nimport { login } from \"src/services/auth.ts\"\n")
        mgr = MilestoneManager(tmp_path)
        gaps = mgr.get_cross_milestone_wiring()
        # Should detect that src/services/auth.ts doesn't exist on disk
        assert any(g.expected_in_file == "src/services/auth.ts" for g in gaps)


class TestVerifyMilestoneExports:
    def test_nonexistent_milestone(self, tmp_path):
        mgr = MilestoneManager(tmp_path)
        issues = mgr.verify_milestone_exports("nonexistent")
        assert issues == []

    def test_no_dependents(self, tmp_path):
        _setup_milestone(tmp_path, "M1", "- [x] Create src/auth/login.ts\n")
        mgr = MilestoneManager(tmp_path)
        issues = mgr.verify_milestone_exports("M1")
        assert issues == []
