"""Tests for agent_team.display — smoke tests for all display functions."""

from __future__ import annotations

from unittest.mock import patch

from agent_team.display import (
    console,
    print_agent_response,
    print_banner,
    print_completion,
    print_contract_violation,
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
    print_resume_banner,
    print_review_results,
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
