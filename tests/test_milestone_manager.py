"""Tests for agent_team.milestone_manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_team.milestone_manager import (
    MasterPlan,
    MasterPlanMilestone,
    MilestoneCompletionSummary,
    MilestoneContext,
    MilestoneManager,
    MilestoneState,
    WiringGap,
    build_completion_summary,
    build_milestone_context,
    compute_rollup_health,
    load_completion_cache,
    parse_master_plan,
    render_predecessor_context,
    save_completion_cache,
    update_master_plan_status,
)

# Private helper -- imported directly for targeted edge-case testing.
from agent_team.milestone_manager import _parse_deps


# ===================================================================
# Shared helpers and fixtures
# ===================================================================

SAMPLE_PLAN = """\
# MASTER PLAN: My App
Generated: 2025-01-01

## Milestone 1: Foundation
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Set up project structure

## Milestone 2: Backend
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Build API layer

## Milestone 3: Frontend
- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-1, milestone-2
- Description: Build UI components
"""


def _setup_milestone(tmp_path: Path, milestone_id: str, content: str) -> None:
    """Helper to create a milestone REQUIREMENTS.md."""
    milestone_dir = tmp_path / ".agent-team" / "milestones" / milestone_id
    milestone_dir.mkdir(parents=True, exist_ok=True)
    (milestone_dir / "REQUIREMENTS.md").write_text(content, encoding="utf-8")


# ===================================================================
# parse_master_plan() -- basic parsing
# ===================================================================


class TestParseMasterPlanBasic:
    def test_parses_title(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        assert plan.title == "My App"

    def test_parses_generated_date(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        assert plan.generated == "2025-01-01"

    def test_parses_all_milestones(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        assert len(plan.milestones) == 3

    def test_parses_milestone_ids(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        ids = [m.id for m in plan.milestones]
        assert ids == ["milestone-1", "milestone-2", "milestone-3"]

    def test_parses_milestone_titles(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        titles = [m.title for m in plan.milestones]
        assert titles == ["Foundation", "Backend", "Frontend"]

    def test_parses_status(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        assert all(m.status == "PENDING" for m in plan.milestones)

    def test_parses_dependencies_none(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m1 = plan.get_milestone("milestone-1")
        assert m1 is not None
        assert m1.dependencies == []

    def test_parses_dependencies_single(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m2 = plan.get_milestone("milestone-2")
        assert m2 is not None
        assert m2.dependencies == ["milestone-1"]

    def test_parses_dependencies_multiple(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m3 = plan.get_milestone("milestone-3")
        assert m3 is not None
        assert m3.dependencies == ["milestone-1", "milestone-2"]

    def test_parses_description(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m1 = plan.get_milestone("milestone-1")
        assert m1 is not None
        assert m1.description == "Set up project structure"


# ===================================================================
# parse_master_plan() -- missing fields
# ===================================================================


class TestParseMasterPlanMissingFields:
    def test_missing_title_returns_empty(self):
        content = "## Milestone 1: Bare\n- ID: m-1\n"
        plan = parse_master_plan(content)
        assert plan.title == ""

    def test_missing_generated_returns_empty(self):
        content = "# MASTER PLAN: App\n## Milestone 1: Bare\n- ID: m-1\n"
        plan = parse_master_plan(content)
        assert plan.generated == ""

    def test_missing_id_auto_generates(self):
        content = """\
# MASTER PLAN: Test
## Milestone 1: Auto ID
- Status: PENDING
- Description: No explicit ID
"""
        plan = parse_master_plan(content)
        assert len(plan.milestones) == 1
        assert plan.milestones[0].id == "milestone-1"

    def test_missing_status_defaults_pending(self):
        content = """\
# MASTER PLAN: Test
## Milestone 1: No Status
- ID: m-1
- Description: Missing status field
"""
        plan = parse_master_plan(content)
        assert plan.milestones[0].status == "PENDING"

    def test_missing_dependencies_returns_empty_list(self):
        content = """\
# MASTER PLAN: Test
## Milestone 1: No Deps
- ID: m-1
- Status: PENDING
"""
        plan = parse_master_plan(content)
        assert plan.milestones[0].dependencies == []

    def test_missing_description_returns_empty(self):
        content = """\
# MASTER PLAN: Test
## Milestone 1: No Desc
- ID: m-1
- Status: PENDING
"""
        plan = parse_master_plan(content)
        assert plan.milestones[0].description == ""

    def test_empty_content_returns_empty_plan(self):
        plan = parse_master_plan("")
        assert plan.title == ""
        assert plan.generated == ""
        assert plan.milestones == []


# ===================================================================
# parse_master_plan() -- status variations
# ===================================================================


class TestParseMasterPlanStatusVariations:
    def test_uppercase_status(self):
        content = "## Milestone 1: Done\n- ID: m-1\n- Status: COMPLETE\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].status == "COMPLETE"

    def test_lowercase_status_normalized_to_upper(self):
        content = "## Milestone 1: Done\n- ID: m-1\n- Status: complete\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].status == "COMPLETE"

    def test_mixed_case_status_normalized(self):
        content = "## Milestone 1: Active\n- ID: m-1\n- Status: In_Progress\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].status == "IN_PROGRESS"

    def test_failed_status(self):
        content = "## Milestone 1: Broken\n- ID: m-1\n- Status: FAILED\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].status == "FAILED"


# ===================================================================
# parse_master_plan() -- header format variations
# ===================================================================


class TestParseMasterPlanHeaderVariations:
    def test_header_with_colon(self):
        content = "## Milestone 1: Auth Setup\n- ID: auth-1\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].title == "Auth Setup"

    def test_header_without_milestone_prefix(self):
        content = "## 1. Auth Setup\n- ID: auth-1\n"
        plan = parse_master_plan(content)
        assert len(plan.milestones) == 1
        assert plan.milestones[0].title == "Auth Setup"

    def test_header_with_dot_suffix(self):
        content = "## Milestone 1. Database Layer\n- ID: db-1\n"
        plan = parse_master_plan(content)
        assert plan.milestones[0].title == "Database Layer"


# ===================================================================
# MasterPlan.all_complete()
# ===================================================================


class TestAllComplete:
    def test_all_complete_when_all_complete(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="COMPLETE"),
        ])
        assert plan.all_complete() is True

    def test_all_complete_when_pending(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
        ])
        assert plan.all_complete() is False

    def test_all_complete_when_mixed(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING"),
        ])
        assert plan.all_complete() is False

    def test_all_complete_with_in_progress(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="IN_PROGRESS"),
        ])
        assert plan.all_complete() is False

    def test_all_complete_with_failed(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="FAILED"),
        ])
        assert plan.all_complete() is False

    def test_all_complete_empty_plan(self):
        plan = MasterPlan(milestones=[])
        assert plan.all_complete() is False

    def test_all_complete_single_complete(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
        ])
        assert plan.all_complete() is True


# ===================================================================
# MasterPlan.get_ready_milestones()
# ===================================================================


class TestGetReadyMilestones:
    def test_no_deps_pending_is_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING", dependencies=[]),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 1
        assert ready[0].id == "m-1"

    def test_deps_not_complete_not_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING", dependencies=["m-1"]),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 1
        assert ready[0].id == "m-1"

    def test_deps_complete_is_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING", dependencies=["m-1"]),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 1
        assert ready[0].id == "m-2"

    def test_already_complete_not_in_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 0

    def test_in_progress_not_in_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="IN_PROGRESS"),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 0

    def test_failed_not_in_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="FAILED"),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 0

    def test_partial_deps_not_ready(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING"),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING", dependencies=["m-1", "m-2"]),
        ])
        ready = plan.get_ready_milestones()
        ids = [m.id for m in ready]
        assert "m-2" in ids
        assert "m-3" not in ids

    def test_multiple_ready_at_once(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING", dependencies=["m-1"]),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING", dependencies=["m-1"]),
        ])
        ready = plan.get_ready_milestones()
        ids = [m.id for m in ready]
        assert "m-2" in ids
        assert "m-3" in ids

    def test_empty_plan_returns_empty(self):
        plan = MasterPlan(milestones=[])
        assert plan.get_ready_milestones() == []

    def test_chain_dependency_resolution(self):
        """Only the first unblocked node in a chain should be ready."""
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="COMPLETE", dependencies=["m-1"]),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING", dependencies=["m-2"]),
            MasterPlanMilestone(id="m-4", title="D", status="PENDING", dependencies=["m-3"]),
        ])
        ready = plan.get_ready_milestones()
        assert len(ready) == 1
        assert ready[0].id == "m-3"


# ===================================================================
# MasterPlan.get_milestone()
# ===================================================================


class TestGetMilestone:
    def test_found(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m = plan.get_milestone("milestone-2")
        assert m is not None
        assert m.title == "Backend"

    def test_not_found(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        assert plan.get_milestone("nonexistent") is None

    def test_empty_plan_returns_none(self):
        plan = MasterPlan(milestones=[])
        assert plan.get_milestone("m-1") is None

    def test_returns_correct_milestone_among_many(self):
        plan = parse_master_plan(SAMPLE_PLAN)
        m = plan.get_milestone("milestone-3")
        assert m is not None
        assert m.title == "Frontend"
        assert m.dependencies == ["milestone-1", "milestone-2"]


# ===================================================================
# update_master_plan_status()
# ===================================================================


class TestUpdateMasterPlanStatus:
    def test_updates_status(self):
        updated = update_master_plan_status(SAMPLE_PLAN, "milestone-1", "COMPLETE")
        assert "- Status: COMPLETE" in updated

    def test_does_not_modify_other_milestones(self):
        updated = update_master_plan_status(SAMPLE_PLAN, "milestone-1", "COMPLETE")
        plan = parse_master_plan(updated)
        m2 = plan.get_milestone("milestone-2")
        assert m2 is not None
        assert m2.status == "PENDING"

    def test_unknown_id_returns_unchanged(self):
        updated = update_master_plan_status(SAMPLE_PLAN, "nonexistent", "COMPLETE")
        assert updated == SAMPLE_PLAN

    def test_update_to_in_progress(self):
        updated = update_master_plan_status(SAMPLE_PLAN, "milestone-2", "IN_PROGRESS")
        plan = parse_master_plan(updated)
        m = plan.get_milestone("milestone-2")
        assert m is not None
        assert m.status == "IN_PROGRESS"

    def test_update_to_failed(self):
        updated = update_master_plan_status(SAMPLE_PLAN, "milestone-3", "FAILED")
        plan = parse_master_plan(updated)
        m = plan.get_milestone("milestone-3")
        assert m is not None
        assert m.status == "FAILED"

    def test_sequential_updates(self):
        """Multiple sequential updates should all take effect."""
        content = SAMPLE_PLAN
        content = update_master_plan_status(content, "milestone-1", "COMPLETE")
        content = update_master_plan_status(content, "milestone-2", "IN_PROGRESS")
        content = update_master_plan_status(content, "milestone-3", "FAILED")
        plan = parse_master_plan(content)
        assert plan.get_milestone("milestone-1").status == "COMPLETE"
        assert plan.get_milestone("milestone-2").status == "IN_PROGRESS"
        assert plan.get_milestone("milestone-3").status == "FAILED"

    def test_preserves_other_content(self):
        """Title, generated date, and descriptions remain untouched."""
        updated = update_master_plan_status(SAMPLE_PLAN, "milestone-1", "COMPLETE")
        assert "MASTER PLAN: My App" in updated
        assert "Generated: 2025-01-01" in updated
        assert "Set up project structure" in updated


# ===================================================================
# build_milestone_context()
# ===================================================================


class TestBuildMilestoneContext:
    def test_basic_context(self):
        milestone = MasterPlanMilestone(id="milestone-1", title="Foundation")
        ctx = build_milestone_context(milestone, "/project/milestones")
        assert ctx.milestone_id == "milestone-1"
        assert ctx.title == "Foundation"
        assert "milestone-1" in ctx.requirements_path
        assert ctx.requirements_path.endswith("REQUIREMENTS.md")

    def test_requirements_path_structure(self):
        milestone = MasterPlanMilestone(id="ms-auth", title="Auth")
        ctx = build_milestone_context(milestone, "/project/.agent-team/milestones")
        assert "ms-auth" in ctx.requirements_path
        assert "REQUIREMENTS.md" in ctx.requirements_path

    def test_empty_predecessor_summaries(self):
        milestone = MasterPlanMilestone(id="m-1", title="Start")
        ctx = build_milestone_context(milestone, "/dir")
        assert ctx.predecessor_summaries == []

    def test_with_predecessor_summaries(self):
        milestone = MasterPlanMilestone(id="m-2", title="Second")
        summaries = [
            MilestoneCompletionSummary(
                milestone_id="m-1",
                title="First",
                summary_line="Set up project",
            ),
        ]
        ctx = build_milestone_context(milestone, "/dir", predecessor_summaries=summaries)
        assert len(ctx.predecessor_summaries) == 1
        assert ctx.predecessor_summaries[0].milestone_id == "m-1"

    def test_milestones_dir_as_path_object(self):
        milestone = MasterPlanMilestone(id="m-1", title="Test")
        ctx = build_milestone_context(milestone, Path("/project/milestones"))
        assert "m-1" in ctx.requirements_path


# ===================================================================
# build_completion_summary()
# ===================================================================


class TestBuildCompletionSummary:
    def test_basic_summary(self):
        milestone = MasterPlanMilestone(id="m-1", title="Foundation")
        summary = build_completion_summary(
            milestone,
            exported_files=["src/app.py"],
            exported_symbols=["main"],
            summary_line="Project structure established",
        )
        assert summary.milestone_id == "m-1"
        assert summary.title == "Foundation"
        assert summary.exported_files == ["src/app.py"]
        assert summary.exported_symbols == ["main"]
        assert summary.summary_line == "Project structure established"

    def test_empty_exports(self):
        milestone = MasterPlanMilestone(id="m-1", title="Setup")
        summary = build_completion_summary(milestone)
        assert summary.exported_files == []
        assert summary.exported_symbols == []
        assert summary.summary_line == ""

    def test_none_exports_become_empty_list(self):
        milestone = MasterPlanMilestone(id="m-1", title="Setup")
        summary = build_completion_summary(milestone, exported_files=None, exported_symbols=None)
        assert summary.exported_files == []
        assert summary.exported_symbols == []

    def test_multiple_exports(self):
        milestone = MasterPlanMilestone(id="m-1", title="Core")
        summary = build_completion_summary(
            milestone,
            exported_files=["src/auth.py", "src/db.py", "src/models.py"],
            exported_symbols=["AuthService", "Database", "User", "Role"],
        )
        assert len(summary.exported_files) == 3
        assert len(summary.exported_symbols) == 4


# ===================================================================
# render_predecessor_context()
# ===================================================================


class TestRenderPredecessorContext:
    def test_empty_summaries_returns_empty(self):
        assert render_predecessor_context([]) == ""

    def test_single_summary(self):
        summaries = [
            MilestoneCompletionSummary(
                milestone_id="m-1",
                title="Foundation",
                summary_line="Project structure ready",
                exported_files=["src/app.py"],
                exported_symbols=["main"],
            ),
        ]
        result = render_predecessor_context(summaries)
        assert "## Completed Milestones Context" in result
        assert "m-1" in result
        assert "Foundation" in result
        assert "Project structure ready" in result
        assert "src/app.py" in result
        assert "main" in result

    def test_multiple_summaries(self):
        summaries = [
            MilestoneCompletionSummary(milestone_id="m-1", title="First", summary_line="Done"),
            MilestoneCompletionSummary(milestone_id="m-2", title="Second", summary_line="Also done"),
        ]
        result = render_predecessor_context(summaries)
        assert "m-1" in result
        assert "m-2" in result
        assert "First" in result
        assert "Second" in result

    def test_summary_without_optional_fields(self):
        summaries = [
            MilestoneCompletionSummary(milestone_id="m-1", title="Bare"),
        ]
        result = render_predecessor_context(summaries)
        assert "m-1" in result
        assert "Bare" in result
        # No summary_line, no files, no symbols -- should not crash
        assert "Summary:" not in result
        assert "Files:" not in result
        assert "Exports:" not in result

    def test_output_contains_header_and_sub_headers(self):
        summaries = [
            MilestoneCompletionSummary(
                milestone_id="ms-auth",
                title="Auth Setup",
                summary_line="Auth system configured",
            ),
        ]
        result = render_predecessor_context(summaries)
        assert result.startswith("## Completed Milestones Context")
        assert "### ms-auth: Auth Setup" in result

    def test_files_truncated_at_20(self):
        """Exported files list should be capped at 20 entries."""
        files = [f"src/file_{i}.py" for i in range(30)]
        summaries = [
            MilestoneCompletionSummary(
                milestone_id="m-1",
                title="Large",
                exported_files=files,
            ),
        ]
        result = render_predecessor_context(summaries)
        # Should only contain the first 20
        assert "file_19" in result
        assert "file_20" not in result


# ===================================================================
# compute_rollup_health()
# ===================================================================


class TestComputeRollupHealth:
    def test_empty_plan(self):
        plan = MasterPlan(milestones=[])
        health = compute_rollup_health(plan)
        assert health["total"] == 0
        assert health["health"] == "unknown"

    def test_all_pending_healthy(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
            MasterPlanMilestone(id="m-2", title="B", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "healthy"
        assert health["total"] == 2
        assert health["pending"] == 2
        assert health["failed"] == 0

    def test_all_complete_healthy(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="COMPLETE"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "healthy"
        assert health["complete"] == 2

    def test_mixed_statuses_no_failures_healthy(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="IN_PROGRESS"),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "healthy"
        assert health["complete"] == 1
        assert health["in_progress"] == 1
        assert health["pending"] == 1

    def test_one_failure_degraded(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="FAILED"),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "degraded"
        assert health["failed"] == 1

    def test_minority_failures_degraded(self):
        """Fewer than half failed -> degraded."""
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="COMPLETE"),
            MasterPlanMilestone(id="m-2", title="B", status="COMPLETE"),
            MasterPlanMilestone(id="m-3", title="C", status="COMPLETE"),
            MasterPlanMilestone(id="m-4", title="D", status="FAILED"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "degraded"

    def test_majority_failures_failed(self):
        """Half or more failed -> failed."""
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="FAILED"),
            MasterPlanMilestone(id="m-2", title="B", status="FAILED"),
            MasterPlanMilestone(id="m-3", title="C", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "failed"
        assert health["failed"] == 2

    def test_all_failed(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="FAILED"),
            MasterPlanMilestone(id="m-2", title="B", status="FAILED"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "failed"
        assert health["failed"] == 2
        assert health["total"] == 2

    def test_exactly_half_failed_is_failed(self):
        """At exactly 50% failure rate, health is 'failed' (failed >= total/2)."""
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="FAILED"),
            MasterPlanMilestone(id="m-2", title="B", status="COMPLETE"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "failed"

    def test_single_milestone_pending_healthy(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "healthy"

    def test_single_milestone_failed(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="FAILED"),
        ])
        health = compute_rollup_health(plan)
        assert health["health"] == "failed"

    def test_health_dict_keys(self):
        plan = MasterPlan(milestones=[
            MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
        ])
        health = compute_rollup_health(plan)
        expected_keys = {"total", "complete", "in_progress", "pending", "failed", "health"}
        assert set(health.keys()) == expected_keys


# ===================================================================
# _parse_deps()
# ===================================================================


class TestParseDeps:
    def test_none_string(self):
        assert _parse_deps("none") == []

    def test_none_uppercase(self):
        assert _parse_deps("None") == []

    def test_na_string(self):
        assert _parse_deps("n/a") == []

    def test_na_uppercase(self):
        assert _parse_deps("N/A") == []

    def test_dash_string(self):
        assert _parse_deps("-") == []

    def test_empty_string(self):
        assert _parse_deps("") == []

    def test_whitespace_only(self):
        assert _parse_deps("   ") == []

    def test_single_dep(self):
        assert _parse_deps("milestone-1") == ["milestone-1"]

    def test_comma_separated(self):
        assert _parse_deps("milestone-1, milestone-2") == ["milestone-1", "milestone-2"]

    def test_comma_separated_no_spaces(self):
        assert _parse_deps("m-1,m-2,m-3") == ["m-1", "m-2", "m-3"]

    def test_extra_whitespace(self):
        assert _parse_deps("  m-1 ,  m-2 ") == ["m-1", "m-2"]

    def test_trailing_comma(self):
        result = _parse_deps("m-1,")
        assert result == ["m-1"]

    def test_leading_comma(self):
        result = _parse_deps(",m-1")
        assert result == ["m-1"]

    def test_empty_between_commas(self):
        result = _parse_deps("m-1,,m-2")
        assert result == ["m-1", "m-2"]


# ===================================================================
# Dataclass defaults and construction
# ===================================================================


class TestDataclassDefaults:
    def test_master_plan_milestone_defaults(self):
        m = MasterPlanMilestone(id="m-1", title="Test")
        assert m.status == "PENDING"
        assert m.dependencies == []
        assert m.description == ""

    def test_master_plan_defaults(self):
        plan = MasterPlan()
        assert plan.title == ""
        assert plan.generated == ""
        assert plan.milestones == []

    def test_milestone_context_defaults(self):
        ctx = MilestoneContext(
            milestone_id="m-1",
            title="Test",
            requirements_path="/path/REQUIREMENTS.md",
        )
        assert ctx.predecessor_summaries == []

    def test_milestone_completion_summary_defaults(self):
        s = MilestoneCompletionSummary(milestone_id="m-1", title="Test")
        assert s.exported_files == []
        assert s.exported_symbols == []
        assert s.summary_line == ""

    def test_milestone_state_defaults(self):
        s = MilestoneState(milestone_id="M1")
        assert s.requirements_total == 0
        assert s.requirements_checked == 0
        assert s.convergence_cycles == 0
        assert s.status == "pending"

    def test_wiring_gap_construction(self):
        gap = WiringGap(
            source_milestone="m-1",
            target_milestone="m-2",
            missing_export="AuthService",
            expected_in_file="src/auth.ts",
        )
        assert gap.source_milestone == "m-1"
        assert gap.target_milestone == "m-2"
        assert gap.missing_export == "AuthService"
        assert gap.expected_in_file == "src/auth.ts"


# ===================================================================
# Integration: parse -> query -> update round-trip
# ===================================================================


class TestParseUpdateRoundTrip:
    def test_parse_update_reparse(self):
        """Parse, update status, re-parse -- status should be updated."""
        plan = parse_master_plan(SAMPLE_PLAN)
        assert plan.get_milestone("milestone-1").status == "PENDING"

        updated_content = update_master_plan_status(SAMPLE_PLAN, "milestone-1", "COMPLETE")
        plan2 = parse_master_plan(updated_content)
        assert plan2.get_milestone("milestone-1").status == "COMPLETE"
        assert plan2.get_milestone("milestone-2").status == "PENDING"

    def test_update_then_ready_milestones(self):
        """After completing milestone-1, milestone-2 should become ready."""
        content = update_master_plan_status(SAMPLE_PLAN, "milestone-1", "COMPLETE")
        plan = parse_master_plan(content)
        ready = plan.get_ready_milestones()
        ids = [m.id for m in ready]
        assert "milestone-2" in ids
        # milestone-3 depends on both m-1 and m-2, so not yet ready
        assert "milestone-3" not in ids

    def test_complete_chain_unlocks_final(self):
        """Completing milestone-1 and milestone-2 should unlock milestone-3."""
        content = SAMPLE_PLAN
        content = update_master_plan_status(content, "milestone-1", "COMPLETE")
        content = update_master_plan_status(content, "milestone-2", "COMPLETE")
        plan = parse_master_plan(content)
        ready = plan.get_ready_milestones()
        ids = [m.id for m in ready]
        assert "milestone-3" in ids

    def test_full_plan_completion(self):
        """All milestones marked COMPLETE should make all_complete() True."""
        content = SAMPLE_PLAN
        for mid in ["milestone-1", "milestone-2", "milestone-3"]:
            content = update_master_plan_status(content, mid, "COMPLETE")
        plan = parse_master_plan(content)
        assert plan.all_complete() is True


# ===================================================================
# MilestoneManager -- check_milestone_health()
# ===================================================================


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
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1")
        assert report.total_requirements == 3
        assert report.checked_requirements == 2
        assert report.health == "degraded"

    def test_partial_checked_failed(self, tmp_path):
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
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1", min_convergence_ratio=0.6)
        assert report.health == "healthy"

    def test_default_threshold_backward_compatible(self, tmp_path):
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report_default = mgr.check_milestone_health("M1")
        report_explicit = mgr.check_milestone_health("M1", min_convergence_ratio=0.9)
        assert report_default.health == report_explicit.health == "degraded"

    def test_configurable_degraded_threshold(self, tmp_path):
        content = "# Requirements\n- [x] Feature A\n- [x] Feature B\n- [ ] Feature C\n(review_cycles: 1)\n"
        _setup_milestone(tmp_path, "M1", content)
        mgr = MilestoneManager(tmp_path)
        report = mgr.check_milestone_health("M1", degraded_threshold=0.7)
        assert report.health == "failed"


# ===================================================================
# MilestoneManager -- cross-milestone wiring
# ===================================================================


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
        _setup_milestone(
            tmp_path,
            "M2",
            '- [ ] Import from src/services/auth.ts\nimport { login } from "src/services/auth.ts"\n',
        )
        mgr = MilestoneManager(tmp_path)
        gaps = mgr.get_cross_milestone_wiring()
        assert any(g.expected_in_file == "src/services/auth.ts" for g in gaps)


# ===================================================================
# MilestoneManager -- verify_milestone_exports()
# ===================================================================


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


# ===================================================================
# Completion cache (Improvement #1)
# ===================================================================


class TestCompletionCache:
    def test_save_and_load_completion_cache(self, tmp_path):
        """Round-trip write/read of a completion cache."""
        milestones_dir = str(tmp_path / "milestones")
        summary = MilestoneCompletionSummary(
            milestone_id="m-1",
            title="Foundation",
            exported_files=["src/app.py"],
            exported_symbols=["main"],
            summary_line="Project setup done",
        )
        save_completion_cache(milestones_dir, "m-1", summary)
        loaded = load_completion_cache(milestones_dir, "m-1")
        assert loaded is not None
        assert loaded.milestone_id == "m-1"
        assert loaded.title == "Foundation"
        assert loaded.exported_files == ["src/app.py"]
        assert loaded.exported_symbols == ["main"]
        assert loaded.summary_line == "Project setup done"

    def test_load_completion_cache_missing_file(self, tmp_path):
        """Returns None when no cache file exists."""
        result = load_completion_cache(str(tmp_path / "milestones"), "nonexistent")
        assert result is None

    def test_load_completion_cache_corrupt_json(self, tmp_path):
        """Returns None when cache file contains invalid JSON."""
        cache_dir = tmp_path / "milestones" / "m-1"
        cache_dir.mkdir(parents=True)
        (cache_dir / "COMPLETION_CACHE.json").write_text("not json{{{", encoding="utf-8")
        result = load_completion_cache(str(tmp_path / "milestones"), "m-1")
        assert result is None

    def test_save_creates_directory(self, tmp_path):
        """save_completion_cache creates the milestone directory if needed."""
        milestones_dir = str(tmp_path / "milestones")
        summary = MilestoneCompletionSummary(milestone_id="m-2", title="API")
        save_completion_cache(milestones_dir, "m-2", summary)
        assert (tmp_path / "milestones" / "m-2" / "COMPLETION_CACHE.json").is_file()


# ===================================================================
# Extended import regex (Improvement #4)
# ===================================================================


class TestImportRefRegexExtended:
    """Tests for CommonJS require() and dynamic import() patterns."""

    def test_require_with_prefix_matches(self):
        content = "const auth = require('src/services/auth')"
        refs = MilestoneManager._extract_import_references(content)
        assert any(path == "src/services/auth" for _, path in refs)

    def test_require_no_prefix_does_not_match(self):
        content = "const express = require('express')"
        refs = MilestoneManager._extract_import_references(content)
        assert not any("express" == path for _, path in refs)

    def test_require_with_symbol(self):
        content = "const connect = require('src/utils/db').connect"
        refs = MilestoneManager._extract_import_references(content)
        assert any(sym == "connect" and path == "src/utils/db" for sym, path in refs)

    def test_dynamic_import_with_prefix_matches(self):
        content = "const mod = import('src/lazy/module')"
        refs = MilestoneManager._extract_import_references(content)
        assert any(path == "src/lazy/module" for _, path in refs)

    def test_dynamic_import_no_prefix_does_not_match(self):
        content = "const lodash = import('lodash')"
        refs = MilestoneManager._extract_import_references(content)
        assert not any("lodash" == path for _, path in refs)

    def test_require_lib_prefix(self):
        content = "require('lib/helpers/format')"
        refs = MilestoneManager._extract_import_references(content)
        assert any(path == "lib/helpers/format" for _, path in refs)

    def test_require_app_prefix(self):
        content = "require('app/config/settings')"
        refs = MilestoneManager._extract_import_references(content)
        assert any(path == "app/config/settings" for _, path in refs)

    def test_existing_ts_import_still_works(self):
        """Existing TS/JS import patterns unchanged."""
        content = 'import { AuthService } from "src/auth/service"'
        refs = MilestoneManager._extract_import_references(content)
        assert ("AuthService", "src/auth/service") in refs

    def test_existing_python_import_still_works(self):
        """Existing Python import patterns unchanged."""
        content = "from src.services.db import Database"
        refs = MilestoneManager._extract_import_references(content)
        assert ("Database", "src.services.db") in refs

    def test_existing_prose_import_still_works(self):
        """Existing prose import patterns unchanged."""
        content = "imports AuthService from src/auth"
        refs = MilestoneManager._extract_import_references(content)
        assert ("AuthService", "src/auth") in refs
