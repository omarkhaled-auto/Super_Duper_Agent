"""Tests for agent_team.state."""

from __future__ import annotations

import json

import pytest

from agent_team.state import (
    RunState,
    RunSummary,
    clear_state,
    get_resume_milestone,
    is_stale,
    load_state,
    save_state,
    update_completion_ratio,
    update_milestone_progress,
    validate_for_resume,
)


# ===================================================================
# RunState dataclass
# ===================================================================

class TestRunState:
    def test_default_run_id_generated(self):
        s = RunState()
        assert s.run_id != ""
        assert len(s.run_id) == 12

    def test_custom_run_id_preserved(self):
        s = RunState(run_id="custom123")
        assert s.run_id == "custom123"

    def test_default_timestamp_set(self):
        s = RunState()
        assert s.timestamp != ""

    def test_task_field(self):
        s = RunState(task="build the app")
        assert s.task == "build the app"

    def test_depth_default(self):
        s = RunState()
        assert s.depth == "standard"

    def test_interrupted_default_false(self):
        s = RunState()
        assert s.interrupted is False

    def test_artifacts_default_empty(self):
        s = RunState()
        assert s.artifacts == {}

    def test_completed_phases_default_empty(self):
        s = RunState()
        assert s.completed_phases == []


# ===================================================================
# RunSummary dataclass
# ===================================================================

class TestRunSummary:
    def test_defaults(self):
        s = RunSummary()
        assert s.task == ""
        assert s.depth == "standard"
        assert s.total_cost == 0.0
        assert s.cycle_count == 0
        assert s.requirements_passed == 0
        assert s.requirements_total == 0
        assert s.files_changed == []

    def test_health_default(self):
        s = RunSummary()
        assert s.health == "unknown"

    def test_recovery_passes_triggered_default(self):
        s = RunSummary()
        assert s.recovery_passes_triggered == 0

    def test_recovery_types_default(self):
        s = RunSummary()
        assert s.recovery_types == []

    def test_recovery_types_mutable_default_independence(self):
        """Mutable default for recovery_types should not be shared between instances."""
        s1 = RunSummary()
        s2 = RunSummary()
        s1.recovery_types.append("contract_generation")
        assert s2.recovery_types == []

    def test_custom_values(self):
        s = RunSummary(
            task="fix bug",
            depth="thorough",
            total_cost=1.50,
            cycle_count=3,
            requirements_passed=8,
            requirements_total=10,
            files_changed=["a.py", "b.py"],
        )
        assert s.task == "fix bug"
        assert s.total_cost == 1.50
        assert s.cycle_count == 3
        assert len(s.files_changed) == 2

    def test_custom_health_and_recovery(self):
        s = RunSummary(
            health="degraded",
            recovery_passes_triggered=2,
            recovery_types=["contract_generation", "review_recovery"],
        )
        assert s.health == "degraded"
        assert s.recovery_passes_triggered == 2
        assert len(s.recovery_types) == 2


# ===================================================================
# save_state()
# ===================================================================

class TestSaveState:
    def test_creates_file(self, tmp_path):
        state = RunState(task="test")
        path = save_state(state, str(tmp_path))
        assert path.is_file()

    def test_file_is_valid_json(self, tmp_path):
        state = RunState(task="test")
        path = save_state(state, str(tmp_path))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["task"] == "test"

    def test_marks_interrupted(self, tmp_path):
        state = RunState(task="test", interrupted=False)
        path = save_state(state, str(tmp_path))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["interrupted"] is True

    def test_creates_directory(self, tmp_path):
        nested = tmp_path / "subdir" / ".agent-team"
        state = RunState(task="test")
        path = save_state(state, str(nested))
        assert path.is_file()


# ===================================================================
# load_state()
# ===================================================================

class TestLoadState:
    def test_round_trip(self, tmp_path):
        original = RunState(task="build app", depth="thorough")
        save_state(original, str(tmp_path))
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.task == "build app"
        assert loaded.depth == "thorough"

    def test_missing_file_returns_none(self, tmp_path):
        result = load_state(str(tmp_path))
        assert result is None

    def test_corrupted_file_returns_none(self, tmp_path):
        state_file = tmp_path / "STATE.json"
        state_file.write_text("not json{{{", encoding="utf-8")
        result = load_state(str(tmp_path))
        assert result is None

    def test_empty_file_returns_none(self, tmp_path):
        state_file = tmp_path / "STATE.json"
        state_file.write_text("", encoding="utf-8")
        result = load_state(str(tmp_path))
        assert result is None


# ===================================================================
# is_stale()
# ===================================================================

class TestIsStale:
    def test_same_task_not_stale(self):
        state = RunState(task="fix the bug")
        assert is_stale(state, "fix the bug") is False

    def test_different_task_is_stale(self):
        state = RunState(task="fix the bug")
        assert is_stale(state, "add new feature") is True

    def test_case_insensitive(self):
        state = RunState(task="Fix The Bug")
        assert is_stale(state, "fix the bug") is False

    def test_whitespace_stripped(self):
        state = RunState(task="  fix bug  ")
        assert is_stale(state, "fix bug") is False

    def test_empty_task_is_stale(self):
        state = RunState(task="")
        assert is_stale(state, "anything") is True

    def test_empty_current_task_is_stale(self):
        state = RunState(task="something")
        assert is_stale(state, "") is True


# ===================================================================
# clear_state()
# ===================================================================

class TestClearState:
    def test_clear_state_deletes_file(self, tmp_path):
        state = RunState(task="test")
        save_state(state, str(tmp_path))
        assert (tmp_path / "STATE.json").is_file()
        clear_state(str(tmp_path))
        assert not (tmp_path / "STATE.json").exists()

    def test_clear_state_missing_file_no_error(self, tmp_path):
        """No crash if STATE.json doesn't exist."""
        clear_state(str(tmp_path))  # should not raise


# ===================================================================
# validate_for_resume()
# ===================================================================

class TestValidateForResume:
    def test_validate_no_task_returns_error(self):
        state = RunState(task="")
        issues = validate_for_resume(state)
        assert any("ERROR" in i for i in issues)

    def test_validate_old_state_returns_warning(self):
        from datetime import datetime, timedelta, timezone
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        state = RunState(task="some task", timestamp=old_time.isoformat())
        issues = validate_for_resume(state)
        assert any("WARNING" in i for i in issues)

    def test_validate_fresh_state_no_issues(self):
        state = RunState(task="some task")
        issues = validate_for_resume(state)
        assert issues == []


# ===================================================================
# RunState milestone fields
# ===================================================================

class TestRunStateMilestoneFields:
    """Tests for milestone-related fields on RunState."""

    def test_run_state_milestone_fields(self):
        """New milestone fields have correct defaults."""
        s = RunState()
        assert s.schema_version == 2
        assert s.current_milestone == ""
        assert s.completed_milestones == []
        assert s.failed_milestones == []
        assert s.milestone_order == []
        assert s.milestone_progress == {}
        assert s.completion_ratio == 0.0

    def test_milestone_fields_custom_values(self):
        """Milestone fields accept custom values via constructor."""
        s = RunState(
            current_milestone="m2",
            completed_milestones=["m1"],
            failed_milestones=["m3"],
            milestone_order=["m1", "m2", "m3"],
        )
        assert s.current_milestone == "m2"
        assert s.completed_milestones == ["m1"]
        assert s.failed_milestones == ["m3"]
        assert s.milestone_order == ["m1", "m2", "m3"]

    def test_schema_version_default(self):
        s = RunState()
        assert s.schema_version == 2

    def test_milestone_progress_default_empty(self):
        s = RunState()
        assert s.milestone_progress == {}

    def test_milestone_fields_independent_across_instances(self):
        """Mutable default fields should not be shared between instances."""
        s1 = RunState()
        s2 = RunState()
        s1.completed_milestones.append("m1")
        assert s2.completed_milestones == []


# ===================================================================
# update_milestone_progress()
# ===================================================================

class TestUpdateMilestoneProgress:
    """Tests for update_milestone_progress helper."""

    def test_update_milestone_progress_complete(self):
        """Marks a milestone as complete, clears current_milestone, adds to completed list."""
        state = RunState(task="build app")
        state.current_milestone = "m1"
        update_milestone_progress(state, "m1", "COMPLETE")
        assert state.current_milestone == ""
        assert "m1" in state.completed_milestones
        assert state.milestone_progress["m1"]["status"] == "COMPLETE"

    def test_update_milestone_progress_failed(self):
        """Marks a milestone as failed, clears current_milestone, adds to failed list."""
        state = RunState(task="build app")
        state.current_milestone = "m2"
        update_milestone_progress(state, "m2", "FAILED")
        assert state.current_milestone == ""
        assert "m2" in state.failed_milestones
        assert state.milestone_progress["m2"]["status"] == "FAILED"

    def test_update_milestone_progress_in_progress(self):
        """IN_PROGRESS sets current_milestone to the milestone ID."""
        state = RunState(task="build app")
        update_milestone_progress(state, "m3", "IN_PROGRESS")
        assert state.current_milestone == "m3"
        assert state.milestone_progress["m3"]["status"] == "IN_PROGRESS"

    def test_complete_removes_from_failed(self):
        """Completing a previously failed milestone removes it from failed list."""
        state = RunState(task="build app")
        state.failed_milestones = ["m1"]
        update_milestone_progress(state, "m1", "COMPLETE")
        assert "m1" not in state.failed_milestones
        assert "m1" in state.completed_milestones

    def test_no_duplicate_completed(self):
        """Completing the same milestone twice does not duplicate it."""
        state = RunState(task="build app")
        update_milestone_progress(state, "m1", "COMPLETE")
        update_milestone_progress(state, "m1", "COMPLETE")
        assert state.completed_milestones.count("m1") == 1

    def test_no_duplicate_failed(self):
        """Failing the same milestone twice does not duplicate it."""
        state = RunState(task="build app")
        update_milestone_progress(state, "m2", "FAILED")
        update_milestone_progress(state, "m2", "FAILED")
        assert state.failed_milestones.count("m2") == 1

    def test_case_insensitive_status(self):
        """Status strings are case-insensitive."""
        state = RunState(task="test")
        update_milestone_progress(state, "m1", "complete")
        assert "m1" in state.completed_milestones
        assert state.milestone_progress["m1"]["status"] == "COMPLETE"


# ===================================================================
# get_resume_milestone()
# ===================================================================

class TestGetResumeMilestone:
    """Tests for get_resume_milestone helper."""

    def test_get_resume_milestone_current(self):
        """Returns current_milestone if it is set."""
        state = RunState(task="build app")
        state.current_milestone = "m2"
        state.milestone_order = ["m1", "m2", "m3"]
        state.completed_milestones = ["m1"]
        assert get_resume_milestone(state) == "m2"

    def test_get_resume_milestone_from_order(self):
        """Returns first non-complete milestone from order when current is empty."""
        state = RunState(task="build app")
        state.current_milestone = ""
        state.milestone_order = ["m1", "m2", "m3"]
        state.completed_milestones = ["m1"]
        assert get_resume_milestone(state) == "m2"

    def test_get_resume_milestone_all_complete(self):
        """Returns None when all milestones are complete."""
        state = RunState(task="build app")
        state.milestone_order = ["m1", "m2"]
        state.completed_milestones = ["m1", "m2"]
        assert get_resume_milestone(state) is None

    def test_get_resume_milestone_empty_order(self):
        """Returns None when milestone_order is empty and no current."""
        state = RunState(task="build app")
        assert get_resume_milestone(state) is None

    def test_get_resume_milestone_first_in_order(self):
        """Returns first milestone when none are complete."""
        state = RunState(task="build app")
        state.milestone_order = ["m1", "m2", "m3"]
        assert get_resume_milestone(state) == "m1"


# ===================================================================
# load_state() backward compatibility
# ===================================================================

class TestLoadStateBackwardCompatible:
    """Tests for backward compatibility when loading schema v1 state."""

    def test_load_state_backward_compatible(self, tmp_path):
        """Schema v1 state (no milestone fields) loads with correct defaults."""
        state_file = tmp_path / "STATE.json"
        v1_data = {
            "run_id": "abc123",
            "task": "fix the bug",
            "depth": "standard",
            "current_phase": "orchestration",
            "completed_phases": ["interview"],
            "total_cost": 1.50,
            "artifacts": {},
            "interrupted": True,
            "timestamp": "2025-06-01T12:00:00+00:00",
            "convergence_cycles": 2,
            "requirements_checked": 5,
            "requirements_total": 10,
            "error_context": "",
            "milestone_progress": {},
        }
        state_file.write_text(json.dumps(v1_data), encoding="utf-8")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.task == "fix the bug"
        # Schema version defaults to 1 when absent
        assert loaded.schema_version == 1
        # New v2 fields should have safe defaults
        assert loaded.current_milestone == ""
        assert loaded.completed_milestones == []
        assert loaded.failed_milestones == []
        assert loaded.milestone_order == []

    def test_load_state_v2_preserves_milestone_fields(self, tmp_path):
        """Schema v2 state round-trips milestone fields correctly."""
        state = RunState(task="build app")
        state.current_milestone = "m2"
        state.completed_milestones = ["m1"]
        state.milestone_order = ["m1", "m2", "m3"]
        save_state(state, str(tmp_path))
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.schema_version == 2
        assert loaded.current_milestone == "m2"
        assert loaded.completed_milestones == ["m1"]
        assert loaded.milestone_order == ["m1", "m2", "m3"]

    def test_load_state_v1_completion_ratio_defaults(self, tmp_path):
        """Schema v1 state loads with completion_ratio defaulting to 0.0."""
        state_file = tmp_path / "STATE.json"
        v1_data = {
            "run_id": "abc123",
            "task": "fix the bug",
            "depth": "standard",
            "current_phase": "orchestration",
            "completed_phases": [],
            "total_cost": 1.0,
            "artifacts": {},
            "interrupted": True,
            "timestamp": "2025-06-01T12:00:00+00:00",
            "convergence_cycles": 0,
            "requirements_checked": 0,
            "requirements_total": 0,
            "error_context": "",
            "milestone_progress": {},
        }
        state_file.write_text(json.dumps(v1_data), encoding="utf-8")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.completion_ratio == 0.0

    def test_load_state_v2_preserves_completion_ratio(self, tmp_path):
        """Schema v2 state preserves completion_ratio correctly."""
        state = RunState(task="build app")
        state.completion_ratio = 0.5
        save_state(state, str(tmp_path))
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.completion_ratio == 0.5


# ===================================================================
# completion_ratio (Improvement #5)
# ===================================================================

class TestCompletionRatio:
    """Tests for completion_ratio field and update_completion_ratio helper."""

    def test_completion_ratio_default(self):
        s = RunState()
        assert s.completion_ratio == 0.0

    def test_update_completion_ratio_basic(self):
        state = RunState(task="build app")
        state.milestone_order = ["m1", "m2", "m3", "m4", "m5"]
        state.completed_milestones = ["m1", "m2"]
        update_completion_ratio(state)
        assert state.completion_ratio == pytest.approx(0.4)

    def test_update_completion_ratio_empty(self):
        state = RunState(task="build app")
        state.milestone_order = []
        state.completed_milestones = []
        update_completion_ratio(state)
        assert state.completion_ratio == 0.0

    def test_update_completion_ratio_all_complete(self):
        state = RunState(task="build app")
        state.milestone_order = ["m1", "m2", "m3"]
        state.completed_milestones = ["m1", "m2", "m3"]
        update_completion_ratio(state)
        assert state.completion_ratio == pytest.approx(1.0)

    def test_save_load_roundtrip_completion_ratio(self, tmp_path):
        state = RunState(task="build app")
        state.completion_ratio = 0.6
        save_state(state, str(tmp_path))
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.completion_ratio == pytest.approx(0.6)
