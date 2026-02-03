"""Tests for extended RunState fields (Agent 4)."""
from __future__ import annotations

import json
import pytest

from agent_team.state import RunState, load_state, save_state


class TestRunStateExtendedFields:
    def test_convergence_cycles_default(self):
        s = RunState()
        assert s.convergence_cycles == 0

    def test_requirements_checked_default(self):
        s = RunState()
        assert s.requirements_checked == 0

    def test_requirements_total_default(self):
        s = RunState()
        assert s.requirements_total == 0

    def test_error_context_default(self):
        s = RunState()
        assert s.error_context == ""

    def test_milestone_progress_default(self):
        s = RunState()
        assert s.milestone_progress == {}

    def test_custom_convergence_fields(self):
        s = RunState(
            convergence_cycles=5,
            requirements_checked=18,
            requirements_total=24,
            error_context="ProcessError: timeout",
            milestone_progress={"M1": {"checked": 10, "total": 12, "cycles": 3}},
        )
        assert s.convergence_cycles == 5
        assert s.requirements_checked == 18
        assert s.requirements_total == 24
        assert s.error_context == "ProcessError: timeout"
        assert s.milestone_progress["M1"]["checked"] == 10


class TestRunStateExtendedSerialization:
    def test_round_trip_convergence_fields(self, tmp_path):
        original = RunState(
            task="test task",
            convergence_cycles=3,
            requirements_checked=15,
            requirements_total=20,
            error_context="some error",
            milestone_progress={"M1": {"checked": 5, "total": 10}},
        )
        save_state(original, str(tmp_path))
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.convergence_cycles == 3
        assert loaded.requirements_checked == 15
        assert loaded.requirements_total == 20
        assert loaded.error_context == "some error"
        assert loaded.milestone_progress == {"M1": {"checked": 5, "total": 10}}

    def test_backward_compat_missing_fields(self, tmp_path):
        """Old STATE.json without new fields should load with defaults."""
        state_file = tmp_path / "STATE.json"
        old_data = {
            "run_id": "abc123",
            "task": "old task",
            "depth": "standard",
            "current_phase": "init",
            "completed_phases": [],
            "total_cost": 0.0,
            "artifacts": {},
            "interrupted": False,
            "timestamp": "2025-01-01T00:00:00+00:00",
        }
        state_file.write_text(json.dumps(old_data), encoding="utf-8")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded.convergence_cycles == 0
        assert loaded.requirements_checked == 0
        assert loaded.requirements_total == 0
        assert loaded.error_context == ""
        assert loaded.milestone_progress == {}

    def test_json_contains_new_fields(self, tmp_path):
        state = RunState(
            task="test",
            convergence_cycles=2,
            requirements_checked=10,
            requirements_total=15,
        )
        path = save_state(state, str(tmp_path))
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "convergence_cycles" in data
        assert data["convergence_cycles"] == 2
        assert "requirements_checked" in data
        assert "requirements_total" in data
        assert "error_context" in data
        assert "milestone_progress" in data
