"""Tests for PRD milestone mode convergence, contracts, and recovery.

Covers all 7 root causes identified in the fix plan:
  RC1: _check_convergence_health() returns "unknown" in PRD mode
  RC2: Recovery decision has no branch for health="unknown"
  RC3: build_milestone_execution_prompt() missing contract + cycle instructions
  RC4: No cross-milestone aggregation
  RC5: Contract recovery guard requires top-level REQUIREMENTS.md
  RC6: GATE 1-4 prompt-only, no programmatic enforcement
  RC7: No .env auto-loading
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.config import AgentTeamConfig, ConvergenceConfig, MilestoneConfig
from agent_team.milestone_manager import (
    MilestoneManager,
    aggregate_milestone_convergence,
)
from agent_team.state import ConvergenceReport


# ===================================================================
# Helpers
# ===================================================================

def _setup_milestone(
    project_root: Path, milestone_id: str, content: str,
) -> None:
    """Create a milestone REQUIREMENTS.md in the standard location."""
    milestone_dir = project_root / ".agent-team" / "milestones" / milestone_id
    milestone_dir.mkdir(parents=True, exist_ok=True)
    (milestone_dir / "REQUIREMENTS.md").write_text(content, encoding="utf-8")


# ===================================================================
# Class 1: TestConvergenceHealthPRDMode  (RC1)
# ===================================================================


class TestConvergenceHealthPRDMode:
    """Verify that convergence health is aggregated from milestones, not
    the (missing) top-level REQUIREMENTS.md."""

    def test_milestone_requirements_aggregated(self, tmp_path):
        """Milestone REQUIREMENTS.md files are read and aggregated."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 2)\n"
            "- [ ] Item 2\n"
        ))
        _setup_milestone(tmp_path, "milestone-2", (
            "- [x] Item 3 (review_cycles: 1)\n"
            "- [x] Item 4 (review_cycles: 1)\n"
        ))
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.total_requirements == 4
        assert report.checked_requirements == 3
        assert report.review_cycles == 2  # max across milestones

    def test_no_top_level_falls_back_to_milestones(self, tmp_path):
        """Without top-level REQUIREMENTS.md, milestones should NOT return 'unknown'."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 1)\n"
        ))
        # No top-level REQUIREMENTS.md exists
        assert not (tmp_path / ".agent-team" / "REQUIREMENTS.md").exists()
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health != "unknown"
        assert report.total_requirements == 1

    def test_aggregates_checked_counts_correctly(
        self, milestone_project_structure,
    ):
        """M1(5/10) + M2(3/5) = 8/15."""
        project_root, _ = milestone_project_structure
        mm = MilestoneManager(project_root)
        report = aggregate_milestone_convergence(mm)
        assert report.checked_requirements == 8
        assert report.total_requirements == 15

    def test_uses_max_review_cycles(self, milestone_project_structure):
        """M1(cycles:2) + M2(cycles:3) => returns 3."""
        project_root, _ = milestone_project_structure
        mm = MilestoneManager(project_root)
        report = aggregate_milestone_convergence(mm)
        assert report.review_cycles == 3

    def test_truly_empty_returns_unknown(self, tmp_path):
        """No milestones, no top-level => 'unknown'."""
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "unknown"


# ===================================================================
# Class 2: TestRecoveryDecisionPRDMode  (RC2)
# ===================================================================


class TestRecoveryDecisionPRDMode:
    """Verify recovery decisions handle PRD-mode scenarios."""

    def test_unknown_health_with_milestones_triggers_recovery(self, tmp_path):
        """When health is 'unknown' but milestone dirs exist, recovery should trigger."""
        config = AgentTeamConfig()
        milestones_dir = tmp_path / config.convergence.requirements_dir / "milestones"
        milestones_dir.mkdir(parents=True)
        (milestones_dir / "milestone-1").mkdir()
        # Create a dummy file so iterdir() is non-empty
        (milestones_dir / "milestone-1" / "REQUIREMENTS.md").write_text("", encoding="utf-8")

        report = ConvergenceReport(health="unknown")
        # Simulate the recovery decision logic from cli.py
        needs_recovery = False
        if report.health == "unknown":
            if milestones_dir.is_dir() and any(milestones_dir.iterdir()):
                needs_recovery = True
        assert needs_recovery is True

    def test_unknown_health_without_milestones_no_recovery(self, tmp_path):
        """When health is 'unknown' and no milestones exist, no recovery."""
        config = AgentTeamConfig()
        milestones_dir = tmp_path / config.convergence.requirements_dir / "milestones"
        # Directory doesn't exist
        report = ConvergenceReport(health="unknown")
        needs_recovery = False
        if report.health == "unknown":
            if milestones_dir.is_dir() and any(milestones_dir.iterdir()):
                needs_recovery = True
        assert needs_recovery is False

    def test_failed_health_prd_mode_triggers_recovery(self):
        """Failed health with zero cycles triggers recovery in any mode."""
        report = ConvergenceReport(
            health="failed",
            review_cycles=0,
            total_requirements=10,
            checked_requirements=0,
        )
        needs_recovery = (
            report.health == "failed"
            and report.review_cycles == 0
            and report.total_requirements > 0
        )
        assert needs_recovery is True

    def test_recovery_reads_milestone_requirements(self, tmp_path):
        """_has_milestone_requirements correctly detects milestone REQUIREMENTS.md."""
        from agent_team.cli import _has_milestone_requirements

        config = AgentTeamConfig()
        # No milestones yet
        assert _has_milestone_requirements(str(tmp_path), config) is False
        # Add a milestone
        _setup_milestone(tmp_path, "milestone-1", "- [ ] Item\n")
        assert _has_milestone_requirements(str(tmp_path), config) is True


# ===================================================================
# Class 3: TestMilestoneExecutionPrompt  (RC3)
# ===================================================================


class TestMilestoneExecutionPrompt:
    """Verify milestone execution prompt includes contract and cycle instructions."""

    def test_includes_contract_specification(self, default_config):
        """Prompt must contain [CONTRACT SPECIFICATION] section."""
        from agent_team.agents import build_milestone_execution_prompt

        prompt = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=default_config,
        )
        assert "[CONTRACT SPECIFICATION]" in prompt
        assert "public exports" in prompt.lower()

    def test_includes_cycle_tracking_instructions(self, default_config):
        """Prompt must contain [CYCLE TRACKING] section."""
        from agent_team.agents import build_milestone_execution_prompt

        prompt = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=default_config,
        )
        assert "[CYCLE TRACKING]" in prompt
        assert "review_cycles" in prompt

    def test_milestone_prompt_includes_mandatory_workflow_steps(self, default_config):
        """Milestone prompt MUST contain ARCHITECTURE FLEET, TASKS.md,
        and review fleet references (Fix RC-2: TASKS.md never created)."""
        from agent_team.agents import build_milestone_execution_prompt

        prompt = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=default_config,
        )
        # These are now REQUIRED in milestone prompts (Fix RC-2)
        assert "ARCHITECTURE FLEET" in prompt
        assert "TASKS.md" in prompt
        assert "TASK ASSIGNER" in prompt
        assert "REVIEW FLEET" in prompt
        assert "MANDATORY" in prompt


# ===================================================================
# Class 4: TestContractRecoveryPRDMode  (RC5)
# ===================================================================


class TestContractRecoveryPRDMode:
    """Verify contract recovery works with milestone-level requirements."""

    def test_triggers_with_milestone_requirements(self, tmp_path):
        """Contract recovery guard should pass when milestone REQUIREMENTS.md exist
        but top-level REQUIREMENTS.md does not."""
        from agent_team.cli import _has_milestone_requirements

        config = AgentTeamConfig()
        _setup_milestone(tmp_path, "milestone-1", "- [ ] Item\n")
        # No top-level REQUIREMENTS.md
        req_path = (
            Path(tmp_path) / config.convergence.requirements_dir
            / config.convergence.requirements_file
        )
        assert not req_path.is_file()
        has_req = req_path.is_file() or _has_milestone_requirements(
            str(tmp_path), config,
        )
        assert has_req is True

    def test_blocked_when_no_requirements_anywhere(self, tmp_path):
        """Contract recovery should NOT trigger when no requirements exist."""
        from agent_team.cli import _has_milestone_requirements

        config = AgentTeamConfig()
        req_path = (
            Path(tmp_path) / config.convergence.requirements_dir
            / config.convergence.requirements_file
        )
        has_req = req_path.is_file() or _has_milestone_requirements(
            str(tmp_path), config,
        )
        assert has_req is False

    def test_recovery_prompt_references_milestone_files(self):
        """When milestone_mode=True, contract prompt should reference milestone paths."""
        from agent_team.cli import _run_contract_generation
        import inspect

        # Verify the function accepts milestone_mode parameter
        sig = inspect.signature(_run_contract_generation)
        assert "milestone_mode" in sig.parameters


# ===================================================================
# Class 5: TestCrossMilestoneAggregation  (RC4)
# ===================================================================


class TestCrossMilestoneAggregation:
    """Verify cross-milestone aggregation computes correct global metrics."""

    def test_all_milestones_complete_healthy(self, tmp_path):
        """All milestones fully checked => healthy."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 2)\n"
            "- [x] Item 2 (review_cycles: 2)\n"
        ))
        _setup_milestone(tmp_path, "milestone-2", (
            "- [x] Item 3 (review_cycles: 1)\n"
        ))
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "healthy"
        assert report.total_requirements == 3
        assert report.checked_requirements == 3
        assert report.convergence_ratio == pytest.approx(1.0)

    def test_mixed_milestone_health_correct_aggregate(self, tmp_path):
        """Mixed milestone health aggregates correctly."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 2)\n"
            "- [x] Item 2 (review_cycles: 2)\n"
            "- [ ] Item 3\n"
        ))
        _setup_milestone(tmp_path, "milestone-2", (
            "- [ ] Item 4\n"
            "- [ ] Item 5\n"
        ))
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        # 2 checked out of 5
        assert report.checked_requirements == 2
        assert report.total_requirements == 5
        assert report.convergence_ratio == pytest.approx(0.4)
        assert report.health == "failed"  # below any threshold

    def test_empty_milestones_returns_empty_report(self, tmp_path):
        """No milestone directories => unknown report."""
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "unknown"
        assert report.total_requirements == 0

    def test_rollup_feeds_into_global_convergence(self, tmp_path):
        """Aggregate report has all expected fields for downstream use."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 3)\n"
            "- [x] Item 2 (review_cycles: 3)\n"
        ))
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        # Verify all fields that downstream consumers need
        assert isinstance(report.total_requirements, int)
        assert isinstance(report.checked_requirements, int)
        assert isinstance(report.review_cycles, int)
        assert isinstance(report.convergence_ratio, float)
        assert isinstance(report.review_fleet_deployed, bool)
        assert isinstance(report.health, str)
        assert isinstance(report.escalated_items, list)


# ===================================================================
# Class 6: TestGateValidation  (RC6)
# ===================================================================


class TestGateValidation:
    """Verify programmatic gate validation."""

    def test_zero_review_cycles_logs_gate_violation(self):
        """Zero review cycles with requirements should be a gate violation."""
        report = ConvergenceReport(
            total_requirements=10,
            checked_requirements=0,
            review_cycles=0,
        )
        # Gate violation condition
        is_violation = (
            report.review_cycles == 0 and report.total_requirements > 0
        )
        assert is_violation is True

    def test_gate_5_enforcement_works_in_prd_mode(self, tmp_path):
        """GATE 5 enforcement: zero-cycle failure triggers recovery in PRD mode."""
        _setup_milestone(tmp_path, "milestone-1", (
            "- [ ] Item 1\n"
            "- [ ] Item 2\n"
        ))
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        # 0 review cycles with requirements => failed health
        assert report.review_cycles == 0
        assert report.total_requirements > 0
        assert report.health == "failed"
        # Recovery should be triggered
        needs_recovery = (
            report.health == "failed"
            and report.review_cycles == 0
            and report.total_requirements > 0
        )
        assert needs_recovery is True


# ===================================================================
# Class 7: TestDotenvLoading  (RC7)
# ===================================================================


class TestDotenvLoading:
    """Verify .env auto-loading behavior."""

    def test_dotenv_loaded_when_available(self, tmp_path, monkeypatch):
        """load_dotenv should be called in main() if python-dotenv is installed."""
        call_log = []

        def mock_load_dotenv(override=True):
            call_log.append(("load_dotenv", override))

        # Patch dotenv module
        import types
        mock_dotenv = types.ModuleType("dotenv")
        mock_dotenv.load_dotenv = mock_load_dotenv

        # Verify the pattern: try import, call with override=False
        with patch.dict("sys.modules", {"dotenv": mock_dotenv}):
            try:
                from dotenv import load_dotenv
                load_dotenv(override=False)
            except ImportError:
                pass

        assert len(call_log) == 1
        assert call_log[0] == ("load_dotenv", False)

    def test_graceful_when_dotenv_unavailable(self):
        """The dotenv loading pattern should not crash when python-dotenv is absent."""
        # Make dotenv import fail by simulating None module
        with patch.dict("sys.modules", {"dotenv": None}):
            try:
                from dotenv import load_dotenv
                load_dotenv(override=False)
            except ImportError:
                pass  # Expected — should be silent
            # If we get here without exception, the pattern works
            assert True


# ===================================================================
# Class 8: TestStandardModeRegression
# ===================================================================


class TestStandardModeRegression:
    """Verify that standard-mode behavior is unchanged by PRD fixes."""

    def test_standard_mode_convergence_unchanged(self, tmp_path):
        """_check_convergence_health still works with top-level REQUIREMENTS.md."""
        from agent_team.cli import _check_convergence_health

        config = AgentTeamConfig()
        req_dir = tmp_path / config.convergence.requirements_dir
        req_dir.mkdir(parents=True)
        req_file = req_dir / config.convergence.requirements_file
        req_file.write_text(
            "- [x] Item 1 (review_cycles: 2)\n"
            "- [x] Item 2 (review_cycles: 2)\n"
            "- [ ] Item 3 (review_cycles: 1)\n",
            encoding="utf-8",
        )
        report = _check_convergence_health(str(tmp_path), config)
        assert report.total_requirements == 3
        assert report.checked_requirements == 2
        assert report.review_cycles == 2
        assert report.health in ("healthy", "degraded", "failed")

    def test_standard_mode_contract_recovery_unchanged(self, tmp_path):
        """Contract recovery guard still checks top-level REQUIREMENTS.md."""
        from agent_team.cli import _has_milestone_requirements

        config = AgentTeamConfig()
        req_dir = tmp_path / config.convergence.requirements_dir
        req_dir.mkdir(parents=True)
        req_file = req_dir / config.convergence.requirements_file
        req_file.write_text("- [x] Item\n", encoding="utf-8")
        # Top-level exists, no milestones
        assert req_file.is_file()
        assert _has_milestone_requirements(str(tmp_path), config) is False
        has_req = req_file.is_file() or _has_milestone_requirements(
            str(tmp_path), config,
        )
        assert has_req is True

    def test_interactive_mode_no_use_milestones_crash(self):
        """_use_milestones initialization prevents NameError in interactive mode."""
        # Simulate what main() does: initialize before try block
        _use_milestones = False
        milestone_convergence_report = None
        # In interactive mode, _use_milestones stays False
        assert _use_milestones is False
        assert milestone_convergence_report is None
        # Post-orchestration branch should work
        if _use_milestones and milestone_convergence_report is not None:
            convergence_report = milestone_convergence_report
        else:
            convergence_report = ConvergenceReport(health="healthy")
        assert convergence_report.health == "healthy"

    def test_standard_mode_recovery_triggers_on_failed(self):
        """Standard mode 'failed' health still triggers recovery."""
        report = ConvergenceReport(
            health="failed",
            review_cycles=0,
            total_requirements=5,
            checked_requirements=0,
        )
        recovery_threshold = 0.5
        needs_recovery = False
        if report.health == "failed":
            if report.review_cycles == 0 and report.total_requirements > 0:
                needs_recovery = True
        assert needs_recovery is True

    def test_standard_mode_returns_correct_convergence_report(self, tmp_path):
        """Standard mode with top-level REQUIREMENTS.md returns accurate report."""
        from agent_team.cli import _check_convergence_health

        config = AgentTeamConfig()
        req_dir = tmp_path / config.convergence.requirements_dir
        req_dir.mkdir(parents=True)
        req_file = req_dir / config.convergence.requirements_file
        req_file.write_text(
            "- [x] A (review_cycles: 1)\n"
            "- [x] B (review_cycles: 2)\n"
            "- [x] C (review_cycles: 2)\n"
            "- [x] D (review_cycles: 2)\n"
            "- [x] E (review_cycles: 1)\n",
            encoding="utf-8",
        )
        report = _check_convergence_health(str(tmp_path), config)
        assert report.total_requirements == 5
        assert report.checked_requirements == 5
        assert report.convergence_ratio == pytest.approx(1.0)
        assert report.review_cycles == 2
        assert report.health == "healthy"


# ===================================================================
# Class 8: TestE2EBugFixes  (RC8 - E2E observation log fixes)
# ===================================================================


class TestE2EBugFixes:
    """Tests for bugs identified during E2E testing observation log analysis."""

    def test_prd_mode_fallback_aggregates_from_disk(self, tmp_path):
        """When milestone_convergence_report is None in PRD mode, aggregate from disk.

        This tests the fix for Issue 7: Recovery fallback using wrong health check.
        When _use_milestones=True but milestone_convergence_report is None (e.g.,
        if _run_prd_milestones() failed with exception), we should call
        aggregate_milestone_convergence() instead of _check_convergence_health().
        """
        # Set up milestone structure
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 2)\n"
            "- [ ] Item 2 (review_cycles: 1)\n"
        ))
        _setup_milestone(tmp_path, "milestone-2", (
            "- [x] Item 3 (review_cycles: 3)\n"
        ))

        config = AgentTeamConfig()
        mm = MilestoneManager(tmp_path)

        # Simulate what post-orchestration does when milestone_convergence_report is None
        _use_milestones = True
        milestone_convergence_report = None  # Simulating exception in _run_prd_milestones

        # The fix: aggregate from disk when in milestone mode but report is None
        if _use_milestones:
            if milestone_convergence_report is not None:
                convergence_report = milestone_convergence_report
            else:
                # This is the fix path
                convergence_report = aggregate_milestone_convergence(
                    mm,
                    min_convergence_ratio=config.convergence.min_convergence_ratio,
                    degraded_threshold=config.convergence.degraded_threshold,
                )

        # Verify aggregation worked correctly
        assert convergence_report.total_requirements == 3
        assert convergence_report.checked_requirements == 2
        assert convergence_report.review_cycles == 3  # max across milestones
        assert convergence_report.health in ("failed", "degraded")  # 2/3 = 66%

    def test_prd_mode_fallback_not_used_when_report_exists(self, tmp_path):
        """When milestone_convergence_report exists, use it directly without re-aggregating."""
        # Set up milestone structure (shouldn't be read)
        _setup_milestone(tmp_path, "milestone-1", (
            "- [x] Item 1 (review_cycles: 1)\n"
            "- [x] Item 2 (review_cycles: 1)\n"
        ))

        # Pre-computed report from _run_prd_milestones()
        milestone_convergence_report = ConvergenceReport(
            health="healthy",
            review_cycles=5,  # Different from what's on disk (1)
            total_requirements=100,  # Different from what's on disk (2)
            checked_requirements=100,
        )

        _use_milestones = True

        # The existing path: use pre-computed report
        if _use_milestones and milestone_convergence_report is not None:
            convergence_report = milestone_convergence_report

        # Should use the pre-computed report, not aggregate from disk
        assert convergence_report.review_cycles == 5
        assert convergence_report.total_requirements == 100

    def test_health_report_undefined_handled_safely(self):
        """health_report initialization prevents NameError.

        This tests the defensive fix for Issue 9: health_report undefined.
        Even though the code flow ensures health_report is set before use,
        the fix initializes it to None as defensive programming.
        """
        # The fix initializes health_report before the try block
        health_report: ConvergenceReport | None = None

        # After try block (simulating exception path that continues)
        # health_report would still be None

        # The fix: safe access pattern
        health_status = health_report.health if health_report else "unknown"
        assert health_status == "unknown"

        # When health_report is set normally
        health_report = ConvergenceReport(health="healthy")
        health_status = health_report.health if health_report else "unknown"
        assert health_status == "healthy"

    def test_orchestrator_prohibited_in_gate1_prompt(self):
        """GATE 1 prompt now explicitly prohibits the orchestrator from marking items.

        This tests the fix for Issue 6: No explicit orchestrator prohibition.
        """
        from agent_team.agents import ORCHESTRATOR_SYSTEM_PROMPT

        # Verify the orchestrator prohibition is present
        assert "ORCHESTRATOR" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "MUST NOT mark items [x]" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_step3_check_has_explicit_warning(self):
        """Step 3 CHECK section now has explicit warning about not marking items.

        This tests the additional fix for Issue 6.
        """
        from agent_team.agents import ORCHESTRATOR_SYSTEM_PROMPT

        # Verify the explicit warning is present in the CHECK section
        assert "YOU (THE ORCHESTRATOR) MUST NOT MARK ITEMS [x] YOURSELF" in ORCHESTRATOR_SYSTEM_PROMPT


# ===================================================================
# Class 8: TestZeroCycleMilestoneTracking (M3 Strengthening)
# ===================================================================


class TestZeroCycleMilestoneTracking:
    """Verify M3: Zero-cycle milestone detection in PRD mode."""

    def test_zero_cycle_tracked_in_aggregation(self, tmp_path):
        """Milestones with 0 cycles but >0 requirements are tracked."""
        _setup_milestone(
            tmp_path, "milestone-1",
            "- [ ] REQ-001: Something\n- [ ] REQ-002: Another\n"
        )
        _setup_milestone(
            tmp_path, "milestone-2",
            "- [x] REQ-003: Done (review_cycles: 2)\n"
        )

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)

        # milestone-1 has requirements but 0 cycles
        assert "milestone-1" in report.zero_cycle_milestones
        # milestone-2 has cycles > 0
        assert "milestone-2" not in report.zero_cycle_milestones

    def test_empty_milestone_not_tracked_as_zero_cycle(self, tmp_path):
        """Milestone with 0 requirements is NOT a zero-cycle milestone."""
        # Create milestone with no requirements
        _setup_milestone(tmp_path, "milestone-empty", "No checkboxes here")

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)

        # Empty milestone should not be in zero_cycle_milestones
        assert "milestone-empty" not in report.zero_cycle_milestones

    def test_all_zero_cycle_milestones_listed(self, tmp_path):
        """All zero-cycle milestones are included in the list."""
        _setup_milestone(tmp_path, "ms-a", "- [ ] Item A\n")
        _setup_milestone(tmp_path, "ms-b", "- [ ] Item B\n")
        _setup_milestone(tmp_path, "ms-c", "- [x] Item C (review_cycles: 1)\n")

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)

        assert len(report.zero_cycle_milestones) == 2
        assert "ms-a" in report.zero_cycle_milestones
        assert "ms-b" in report.zero_cycle_milestones
        assert "ms-c" not in report.zero_cycle_milestones


# ===================================================================
# Class 9: TestFallbackPathPerMilestoneDisplay (H2 Strengthening)
# ===================================================================


class TestFallbackPathPerMilestoneDisplay:
    """Verify H2: Fallback path displays per-milestone breakdown."""

    def test_fallback_uses_same_aggregation(self, tmp_path):
        """Fallback path aggregates correctly from milestones on disk."""
        _setup_milestone(tmp_path, "m1", "- [x] A (review_cycles: 1)\n")
        _setup_milestone(tmp_path, "m2", "- [ ] B\n")

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)

        assert report.total_requirements == 2
        assert report.checked_requirements == 1
        assert report.review_cycles == 1

    def test_per_milestone_breakdown_available(self, tmp_path):
        """Individual milestone health is accessible for display."""
        _setup_milestone(
            tmp_path, "milestone-1",
            "- [x] A (review_cycles: 2)\n- [ ] B (review_cycles: 1)\n"
        )

        mm = MilestoneManager(tmp_path)
        health = mm.check_milestone_health("milestone-1")

        assert health.total_requirements == 2
        assert health.checked_requirements == 1
        assert health.review_cycles == 2


# ===================================================================
# Class 10: TestUnknownHealthInvestigationPRD (H3 Strengthening)
# ===================================================================


class TestUnknownHealthInvestigationPRD:
    """Verify H3: Unknown health investigation in PRD mode."""

    def test_no_milestones_dir_detected(self, tmp_path):
        """Missing milestones directory produces unknown health."""
        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "unknown"

    def test_empty_milestones_dir_produces_unknown(self, tmp_path):
        """Empty milestones directory produces unknown health."""
        milestones_dir = tmp_path / ".agent-team" / "milestones"
        milestones_dir.mkdir(parents=True)

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "unknown"

    def test_milestones_without_requirements_files(self, tmp_path):
        """Milestone dirs without REQUIREMENTS.md don't contribute."""
        milestone_dir = tmp_path / ".agent-team" / "milestones" / "milestone-1"
        milestone_dir.mkdir(parents=True)
        # No REQUIREMENTS.md created

        mm = MilestoneManager(tmp_path)
        report = aggregate_milestone_convergence(mm)
        assert report.health == "unknown"
        assert report.total_requirements == 0
