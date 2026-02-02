"""Run state persistence for Agent Team.

Supports saving/loading state for graceful interrupt/resume workflows.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunState:
    """Captures the state of an agent-team run for resume capability."""

    run_id: str = ""
    task: str = ""
    depth: str = "standard"
    current_phase: str = "init"
    completed_phases: list[str] = field(default_factory=list)
    total_cost: float = 0.0
    artifacts: dict[str, str] = field(default_factory=dict)  # name -> path
    interrupted: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class RunSummary:
    """Summary of a completed agent-team run."""

    task: str = ""
    depth: str = "standard"
    total_cost: float = 0.0
    cycle_count: int = 0
    requirements_passed: int = 0
    requirements_total: int = 0
    files_changed: list[str] = field(default_factory=list)


_STATE_FILE = "STATE.json"


def save_state(state: RunState, directory: str = ".agent-team") -> Path:
    """Save run state to a JSON file in the given directory.

    Returns the path to the saved state file.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    # Create a copy of state data and set interrupted flag
    data = asdict(state)
    data["interrupted"] = True

    state_path = dir_path / _STATE_FILE

    # Atomic write: write to temp file, then replace atomically
    fd, temp_path = tempfile.mkstemp(
        dir=str(dir_path),
        prefix=".STATE_",
        suffix=".tmp"
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, state_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise

    return state_path


def _expect(value: Any, typ: type | tuple[type, ...], default: Any) -> Any:
    """Return value if it matches the expected type, otherwise return default."""
    return value if isinstance(value, typ) else default


def load_state(directory: str = ".agent-team") -> RunState | None:
    """Load run state from the JSON file in the given directory.

    Returns None if no state file exists or it cannot be parsed.
    """
    state_path = Path(directory) / _STATE_FILE
    if not state_path.is_file():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return RunState(
            run_id=_expect(data.get("run_id", ""), str, ""),
            task=_expect(data.get("task", ""), str, ""),
            depth=_expect(data.get("depth", "standard"), str, "standard"),
            current_phase=_expect(data.get("current_phase", "init"), str, "init"),
            completed_phases=_expect(data.get("completed_phases", []), list, []),
            total_cost=_expect(data.get("total_cost", 0.0), (int, float), 0.0),
            artifacts=_expect(data.get("artifacts", {}), dict, {}),
            interrupted=_expect(data.get("interrupted", False), bool, False),
            timestamp=_expect(data.get("timestamp", ""), str, ""),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError, UnicodeDecodeError):
        return None


def clear_state(directory: str = ".agent-team") -> None:
    """Delete the state file after a successful run."""
    state_path = Path(directory) / _STATE_FILE
    with contextlib.suppress(OSError):
        state_path.unlink(missing_ok=True)


def validate_for_resume(state: RunState) -> list[str]:
    """Validate saved state for resume. Returns warning/error messages."""
    issues: list[str] = []
    if not state.task:
        issues.append("ERROR: No task recorded in saved state.")
    if state.timestamp:
        try:
            saved = datetime.fromisoformat(state.timestamp)
            age_h = (datetime.now(timezone.utc) - saved).total_seconds() / 3600
            if age_h > 24:
                issues.append(f"WARNING: State is {int(age_h)}h old. Files may have changed.")
        except (ValueError, TypeError):
            pass
    return issues


def is_stale(state: RunState, current_task: str) -> bool:
    """Check if a saved state is stale (from a different task).

    A state is considered stale if the saved task differs from the
    current task (case-insensitive, stripped comparison).
    """
    if not state.task or not current_task:
        return True
    return state.task.strip().lower() != current_task.strip().lower()
