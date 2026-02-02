"""Tests for agent_team.state."""

from __future__ import annotations

import json

import pytest

from agent_team.state import (
    RunState,
    RunSummary,
    clear_state,
    is_stale,
    load_state,
    save_state,
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
