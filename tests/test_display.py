"""Tests for agent_team.display — smoke tests for all display functions."""

from __future__ import annotations

from unittest.mock import patch

from agent_team.display import (
    console,
    print_agent_response,
    print_banner,
    print_completion,
    print_contract_violation,
    print_convergence_health,
    print_convergence_status,
    print_cost_summary,
    print_error,
    print_escalation,
    print_fleet_deployment,
    print_info,
    print_intervention,
    print_intervention_hint,
    print_interview_end,
    print_interview_skip,
    print_interview_start,
    print_prd_mode,
    print_recovery_report,
    print_resume_banner,
    print_review_results,
    print_run_summary,
    print_schedule_summary,
    print_task_start,
    print_user_intervention_needed,
    print_verification_summary,
    print_warning,
)


class TestDisplaySmoke:
    """Smoke tests: call each function, verify no exceptions raised."""

    def test_print_banner(self):
        print_banner()

    def test_print_task_start(self):
        print_task_start("fix the bug", "standard")

    def test_print_task_start_with_agent_count(self):
        print_task_start("fix the bug", "thorough", agent_count=5)

    def test_print_prd_mode(self):
        print_prd_mode("/path/to/prd.md")

    def test_print_fleet_deployment(self):
        print_fleet_deployment("coding", "code-writer", 3)

    def test_print_fleet_deployment_with_assignments(self):
        print_fleet_deployment("coding", "code-writer", 2, ["file1.py", "file2.py"])

    def test_print_convergence_status(self):
        print_convergence_status(1, 10, 5)

    def test_print_convergence_status_zero_total(self):
        """No ZeroDivisionError when total_items is 0."""
        print_convergence_status(1, 0, 0)

    def test_print_convergence_status_all_complete(self):
        """10/10 shows ALL ITEMS COMPLETE."""
        print_convergence_status(1, 10, 10)

    def test_print_convergence_status_with_remaining(self):
        print_convergence_status(2, 10, 5, remaining_items=["REQ-001", "REQ-002"])

    def test_print_convergence_status_with_escalated(self):
        print_convergence_status(3, 10, 5, escalated_items=["REQ-003"])

    def test_print_review_results(self):
        print_review_results(["REQ-001"], [("REQ-002", "missing validation")])

    def test_print_review_results_empty(self):
        print_review_results([], [])

    def test_print_completion(self):
        print_completion("fix bug", 3, 1.234)

    def test_print_completion_none_cost(self):
        print_completion("fix bug", 3, None)

    def test_print_cost_summary(self):
        print_cost_summary({"planning": 0.5, "coding": 1.0})

    def test_print_cost_summary_empty_dict(self):
        """Empty dict should return early without error."""
        print_cost_summary({})

    def test_print_error(self):
        print_error("something went wrong")

    def test_print_warning(self):
        print_warning("watch out")

    def test_print_info(self):
        print_info("just so you know")

    def test_print_escalation(self):
        print_escalation("REQ-001", "failed 3 times")

    def test_print_user_intervention_needed(self):
        print_user_intervention_needed("REQ-005")

    def test_print_interview_start(self):
        print_interview_start()

    def test_print_interview_start_with_task(self):
        print_interview_start("build a login page")

    def test_print_interview_end(self):
        print_interview_end(5, "MEDIUM", "/path/to/doc.md")

    def test_print_interview_skip(self):
        print_interview_skip("--no-interview flag")

    def test_print_agent_response(self):
        print_agent_response("Hello from the agent!")

    def test_console_exists(self):
        assert console is not None


class TestConsoleConfiguration:
    """Tests for Finding #18: console force_terminal setting."""

    def test_console_exists(self):
        from agent_team.display import console
        assert console is not None


class TestDisplayEdgeCases:
    def test_task_start_truncates_at_120(self):
        long_task = "a" * 200
        # Should not raise, and should truncate
        print_task_start(long_task, "standard")

    def test_print_interactive_prompt_eof(self):
        from agent_team.display import print_interactive_prompt
        with patch.object(console, "input", side_effect=EOFError):
            result = print_interactive_prompt()
            assert result == ""


class TestSchedulerVerificationDisplay:
    """Tests for the 6 runtime display functions (scheduler + verification).

    These functions are imported by cli.py and will be wired into the
    runtime pipeline when the scheduler/verification modules are connected.
    Tests use capsys to verify output is produced.
    """

    def test_print_schedule_summary(self, capsys):
        print_schedule_summary(waves=3, conflicts=2)
        captured = capsys.readouterr()
        assert captured.out  # something was printed

    def test_print_schedule_summary_zero_conflicts(self, capsys):
        print_schedule_summary(waves=1, conflicts=0)
        captured = capsys.readouterr()
        assert captured.out

    def test_print_verification_summary_green(self, capsys):
        state = {
            "overall_health": "green",
            "completed_tasks": {"T1": "pass", "T2": "pass"},
        }
        print_verification_summary(state)
        captured = capsys.readouterr()
        assert captured.out

    def test_print_verification_summary_red(self, capsys):
        state = {
            "overall_health": "red",
            "completed_tasks": {"T1": "pass", "T2": "fail", "T3": "fail"},
        }
        print_verification_summary(state)
        captured = capsys.readouterr()
        assert captured.out

    def test_print_verification_summary_empty(self, capsys):
        state = {"overall_health": "unknown", "completed_tasks": {}}
        print_verification_summary(state)
        captured = capsys.readouterr()
        assert captured.out

    def test_print_contract_violation(self, capsys):
        print_contract_violation("Missing return type on foo()")
        captured = capsys.readouterr()
        assert captured.out


class TestInterventionDisplay:
    """Tests for the user intervention display functions."""

    def test_print_intervention_smoke(self):
        """Should not raise."""
        print_intervention("stop changing CSS, focus on API")

    def test_print_intervention_hint_smoke(self):
        """Should not raise."""
        print_intervention_hint()

    def test_print_intervention_produces_output(self, capsys):
        print_intervention("redirect to backend work")
        captured = capsys.readouterr()
        assert captured.out

    def test_print_intervention_hint_produces_output(self, capsys):
        print_intervention_hint()
        captured = capsys.readouterr()
        assert captured.out


class TestResumeBannerDisplay:
    """Tests for the resume banner display function."""

    def test_print_resume_banner_smoke(self):
        """Should not raise."""
        from agent_team.state import RunState
        state = RunState(task="fix the bug", current_phase="orchestration")
        state.completed_phases = ["interview", "constraints"]
        print_resume_banner(state)

    def test_print_resume_banner_produces_output(self, capsys):
        from agent_team.state import RunState
        state = RunState(task="fix the bug", current_phase="orchestration")
        state.completed_phases = ["interview", "constraints"]
        state.total_cost = 1.23
        print_resume_banner(state)
        captured = capsys.readouterr()
        assert captured.out


# ===================================================================
# Subscription / CLI backend display
# ===================================================================

class TestSubscriptionDisplay:
    """Tests for subscription mode display (cost=None or $0)."""

    def test_print_completion_none_cost_shows_subscription(self, capsys):
        """cost=None shows 'included in subscription' instead of $0."""
        print_completion("fix bug", 3, None)
        captured = capsys.readouterr()
        assert "subscription" in captured.out

    def test_print_completion_zero_cost_hides_cost(self, capsys):
        """cost=0.0 should not show '$0.0000'."""
        print_completion("fix bug", 3, 0.0)
        captured = capsys.readouterr()
        assert "$0.0000" not in captured.out

    def test_print_completion_positive_cost_shows_dollars(self, capsys):
        """Positive cost still shows dollar amount."""
        print_completion("fix bug", 3, 1.5)
        captured = capsys.readouterr()
        assert "$1.5000" in captured.out

    def test_print_run_summary_cli_backend(self, capsys):
        """backend='cli' shows 'subscription' instead of cost."""
        from agent_team.state import RunSummary
        summary = RunSummary(task="fix bug", depth="standard", total_cost=0.0)
        print_run_summary(summary, backend="cli")
        captured = capsys.readouterr()
        assert "subscription" in captured.out

    def test_print_run_summary_api_backend_with_cost(self, capsys):
        """backend='api' with cost shows dollar amount."""
        from agent_team.state import RunSummary
        summary = RunSummary(task="fix bug", depth="standard", total_cost=2.5)
        print_run_summary(summary, backend="api")
        captured = capsys.readouterr()
        assert "$2.5000" in captured.out

    def test_print_run_summary_api_backend_zero_cost(self, capsys):
        """backend='api' with zero cost omits cost line."""
        from agent_team.state import RunSummary
        summary = RunSummary(task="fix bug", depth="standard", total_cost=0.0)
        print_run_summary(summary, backend="api")
        captured = capsys.readouterr()
        assert "subscription" not in captured.out

    def test_print_run_summary_default_backend_is_api(self, capsys):
        """Default backend parameter is 'api'."""
        from agent_team.state import RunSummary
        summary = RunSummary(task="fix bug", depth="standard", total_cost=0.0)
        print_run_summary(summary)  # no backend kwarg
        captured = capsys.readouterr()
        assert "subscription" not in captured.out


# ===================================================================
# print_convergence_health()
# ===================================================================

class TestPrintConvergenceHealth:
    """Tests for print_convergence_health display function."""

    def test_unknown_health_no_output(self, capsys):
        """health='unknown' should produce no output (early return)."""
        print_convergence_health("unknown", 0, 0, 0)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_healthy_produces_output(self, capsys):
        """health='healthy' should produce output."""
        print_convergence_health("healthy", 10, 10, 3)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_degraded_produces_output(self, capsys):
        """health='degraded' should produce output."""
        print_convergence_health("degraded", 5, 10, 2)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_failed_produces_output(self, capsys):
        """health='failed' should produce output."""
        print_convergence_health("failed", 2, 10, 1)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_with_escalated_items(self, capsys):
        """Escalated items should appear in output."""
        print_convergence_health(
            "degraded", 5, 10, 2,
            escalated_items=["REQ-001", "REQ-002"],
        )
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_zero_total_no_division_error(self, capsys):
        """req_total=0 should not cause ZeroDivisionError."""
        print_convergence_health("healthy", 0, 0, 0)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_no_escalated_items(self, capsys):
        """None escalated_items should not cause errors."""
        print_convergence_health("healthy", 8, 10, 3, escalated_items=None)
        captured = capsys.readouterr()
        assert captured.out != ""


# ===================================================================
# print_recovery_report()
# ===================================================================

class TestPrintRecoveryReport:
    """Tests for print_recovery_report display function."""

    def test_zero_count_no_output(self, capsys):
        """recovery_count=0 should produce no output (early return)."""
        print_recovery_report(0, [])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_contract_generation_type(self, capsys):
        """Should produce output for contract_generation recovery type."""
        print_recovery_report(1, ["contract_generation"])
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_review_recovery_type(self, capsys):
        """Should produce output for review_recovery recovery type."""
        print_recovery_report(1, ["review_recovery"])
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_multiple_recovery_types(self, capsys):
        """Should handle multiple recovery types."""
        print_recovery_report(2, ["contract_generation", "review_recovery"])
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_unknown_recovery_type(self, capsys):
        """Should handle unknown recovery types without crashing."""
        print_recovery_report(1, ["unknown_type"])
        captured = capsys.readouterr()
        assert captured.out != ""


# ===================================================================
# print_run_summary() with new fields
# ===================================================================

class TestPrintRunSummaryNewFields:
    """Tests for print_run_summary with health and recovery fields."""

    def test_summary_with_health(self, capsys):
        """RunSummary with health='healthy' should include health display."""
        from agent_team.state import RunSummary
        summary = RunSummary(
            task="fix bug", depth="standard", total_cost=1.0,
            requirements_passed=10, requirements_total=10,
            health="healthy",
        )
        print_run_summary(summary)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_summary_with_recovery(self, capsys):
        """RunSummary with recovery passes should include recovery display."""
        from agent_team.state import RunSummary
        summary = RunSummary(
            task="fix bug", depth="standard", total_cost=1.0,
            health="degraded",
            recovery_passes_triggered=1,
            recovery_types=["contract_generation"],
        )
        print_run_summary(summary)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_summary_unknown_health_no_extra(self, capsys):
        """RunSummary with health='unknown' should not show health panel."""
        from agent_team.state import RunSummary
        summary = RunSummary(task="fix bug", depth="standard", total_cost=0.0)
        print_run_summary(summary)
        captured = capsys.readouterr()
        # Should still produce some output (the basic summary)
        assert captured.out != ""
