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
    # Granular convergence tracking (Root Cause #2, #3)
    convergence_cycles: int = 0
    requirements_checked: int = 0
    requirements_total: int = 0
    error_context: str = ""
    milestone_progress: dict[str, dict] = field(default_factory=dict)
    # Per-milestone orchestration fields (schema version 2)
    schema_version: int = 2
    current_milestone: str = ""
    completed_milestones: list[str] = field(default_factory=list)
    failed_milestones: list[str] = field(default_factory=list)
    milestone_order: list[str] = field(default_factory=list)
    completion_ratio: float = 0.0  # completed_milestones / total_milestones

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
    health: str = "unknown"
    recovery_passes_triggered: int = 0
    recovery_types: list[str] = field(default_factory=list)


@dataclass
class ConvergenceReport:
    """Result of a convergence health check after orchestration."""

    total_requirements: int = 0
    checked_requirements: int = 0
    review_cycles: int = 0
    convergence_ratio: float = 0.0  # checked/total
    review_fleet_deployed: bool = False  # cycles > 0
    health: str = "unknown"  # "healthy" | "degraded" | "failed"
    escalated_items: list[str] = field(default_factory=list)  # items at escalation threshold still unchecked
    # M3: Zero-cycle milestone tracking (Issue #10)
    zero_cycle_milestones: list[str] = field(default_factory=list)  # milestones with 0 review cycles


@dataclass
class E2ETestReport:
    """Result of E2E testing phase — tracks backend API and frontend Playwright tests."""

    backend_total: int = 0
    backend_passed: int = 0
    frontend_total: int = 0
    frontend_passed: int = 0
    fix_retries_used: int = 0
    total_fix_cycles: int = 0       # Total fix cycles across both parts
    skipped: bool = False
    skip_reason: str = ""           # "Build failed", "No backend detected", etc.
    health: str = "unknown"         # "passed" | "partial" | "failed" | "skipped"
    failed_tests: list[str] = field(default_factory=list)


_STATE_FILE = "STATE.json"
_CURRENT_SCHEMA_VERSION = 2


def update_milestone_progress(
    state: RunState,
    milestone_id: str,
    status: str,
) -> None:
    """Update the milestone tracking fields on *state* in place.

    Parameters
    ----------
    state : RunState
        The run state to update.
    milestone_id : str
        The milestone whose status changed.
    status : str
        New status: ``"IN_PROGRESS"``, ``"COMPLETE"``, or ``"FAILED"``.
    """
    status_upper = status.upper()
    if status_upper == "IN_PROGRESS":
        state.current_milestone = milestone_id
    elif status_upper == "COMPLETE":
        state.current_milestone = ""
        if milestone_id not in state.completed_milestones:
            state.completed_milestones.append(milestone_id)
        # Remove from failed if it was retried successfully
        if milestone_id in state.failed_milestones:
            state.failed_milestones.remove(milestone_id)
    elif status_upper == "FAILED":
        state.current_milestone = ""
        if milestone_id not in state.failed_milestones:
            state.failed_milestones.append(milestone_id)

    state.milestone_progress[milestone_id] = {"status": status_upper}


def get_resume_milestone(state: RunState) -> str | None:
    """Determine which milestone to resume from after an interruption.

    Returns the milestone ID to resume from, or ``None`` if there is
    nothing to resume.
    """
    # If there was a milestone in progress when interrupted, resume there
    if state.current_milestone:
        return state.current_milestone

    # Otherwise find the first milestone in order that isn't complete
    for mid in state.milestone_order:
        if mid not in state.completed_milestones:
            return mid

    return None


def update_completion_ratio(state: RunState) -> None:
    """Recompute completion_ratio from completed/total milestones."""
    total = len(state.milestone_order)
    if total > 0:
        state.completion_ratio = len(state.completed_milestones) / total
    else:
        state.completion_ratio = 0.0


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
            convergence_cycles=_expect(data.get("convergence_cycles", 0), (int, float), 0),
            requirements_checked=_expect(data.get("requirements_checked", 0), (int, float), 0),
            requirements_total=_expect(data.get("requirements_total", 0), (int, float), 0),
            error_context=_expect(data.get("error_context", ""), str, ""),
            milestone_progress=_expect(data.get("milestone_progress", {}), dict, {}),
            # Schema version 2 fields — backward-compatible defaults
            schema_version=_expect(data.get("schema_version", 1), (int, float), 1),
            current_milestone=_expect(data.get("current_milestone", ""), str, ""),
            completed_milestones=_expect(data.get("completed_milestones", []), list, []),
            failed_milestones=_expect(data.get("failed_milestones", []), list, []),
            milestone_order=_expect(data.get("milestone_order", []), list, []),
            completion_ratio=_expect(data.get("completion_ratio", 0.0), (int, float), 0.0),
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
