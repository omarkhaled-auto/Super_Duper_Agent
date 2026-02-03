"""Wiring dependency detection for the scheduler.

Parses TASKS.md content to identify WIRE-xxx tasks (integration/wiring tasks)
and builds a dependency map showing which implementation tasks must complete
before each wiring task can start.  This enables the scheduler to defer wiring
tasks until all of their prerequisite implementation tasks are finished,
preventing premature integration attempts.

The ``build_wiring_schedule_hint`` function produces a human-readable summary
suitable for prompt injection, so that orchestration agents understand which
tasks are blocked on wiring prerequisites.

All algorithms are O(N) where N = number of task blocks in TASKS.md.
Zero external dependencies -- stdlib only.
"""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Compiled regexes for TASKS.md parsing
# ---------------------------------------------------------------------------

_RE_TASK_HEADER = re.compile(
    r"^###\s+(TASK-\d+)(?::\s*(.+))?$", re.MULTILINE
)
_RE_PARENT = re.compile(
    r"-\s*(?:parent):\s*(.+)", re.IGNORECASE
)
_RE_DEPENDS = re.compile(
    r"-\s*(?:dependencies|depends\s*on|requires):\s*(.+)", re.IGNORECASE
)
_RE_FILES = re.compile(
    r"-\s*(?:files|targets|modifies):\s*(.+)", re.IGNORECASE
)
_RE_STATUS = re.compile(
    r"-\s*(?:status):\s*(\w+)", re.IGNORECASE
)

_TASK_ID_PATTERN = re.compile(r"TASK-\d+")
_WIRE_ID_PATTERN = re.compile(r"WIRE-\d+")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_task_ids(raw: str) -> list[str]:
    """Extract TASK-xxx IDs from a comma-separated string.

    Handles formats like:
    - ``TASK-001, TASK-002``
    - ``TASK-001``
    - ``none`` / ``None`` / ``N/A``

    Returns an empty list for values indicating no dependencies.
    """
    if not raw or raw.strip().lower() in ("none", "n/a", "-", ""):
        return []
    return _TASK_ID_PATTERN.findall(raw)


def _parse_wire_id(raw: str) -> str | None:
    """Extract a single WIRE-xxx ID from a parent field value.

    Returns ``None`` if no WIRE-xxx ID is found.
    """
    if not raw:
        return None
    match = _WIRE_ID_PATTERN.search(raw.strip())
    return match.group(0) if match else None


def _parse_file_list(raw: str) -> list[str]:
    """Extract file paths from a comma-separated string.

    Returns an empty list for values indicating no files.
    """
    if not raw or raw.strip().lower() in ("none", "n/a", "-", ""):
        return []
    tokens = [t.strip() for t in raw.split(",")]
    return [t for t in tokens if t]


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------


class _WireTaskInfo:
    """Internal representation of a parsed wiring task block."""

    __slots__ = ("task_id", "title", "wire_parent", "dependencies", "files", "status")

    def __init__(
        self,
        task_id: str,
        title: str,
        wire_parent: str | None,
        dependencies: list[str],
        files: list[str],
        status: str,
    ) -> None:
        self.task_id = task_id
        self.title = title
        self.wire_parent = wire_parent
        self.dependencies = dependencies
        self.files = files
        self.status = status


# ---------------------------------------------------------------------------
# TASKS.md block parser
# ---------------------------------------------------------------------------


def _parse_task_blocks(content: str) -> list[_WireTaskInfo]:
    """Parse TASKS.md content into a list of task info objects.

    Uses block-splitting at ``### TASK-`` headers, then extracts
    structured fields from each block using compiled regexes.

    Returns all parsed tasks, not just wiring tasks.
    """
    if not content or not content.strip():
        return []

    blocks = re.split(r"(?=^###\s+TASK-)", content, flags=re.MULTILINE)
    tasks: list[_WireTaskInfo] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        header_match = _RE_TASK_HEADER.search(block)
        if not header_match:
            continue

        task_id = header_match.group(1)
        title = (header_match.group(2) or "").strip()

        # Parent field (WIRE-xxx or REQ-xxx)
        wire_parent: str | None = None
        parent_match = _RE_PARENT.search(block)
        if parent_match:
            wire_parent = _parse_wire_id(parent_match.group(1))

        # Dependencies
        dependencies: list[str] = []
        dep_match = _RE_DEPENDS.search(block)
        if dep_match:
            dependencies = _parse_task_ids(dep_match.group(1))

        # Files
        files: list[str] = []
        files_match = _RE_FILES.search(block)
        if files_match:
            files = _parse_file_list(files_match.group(1))

        # Status
        status = "PENDING"
        status_match = _RE_STATUS.search(block)
        if status_match:
            status = status_match.group(1).upper()

        tasks.append(
            _WireTaskInfo(
                task_id=task_id,
                title=title,
                wire_parent=wire_parent,
                dependencies=dependencies,
                files=files,
                status=status,
            )
        )

    return tasks


# ---------------------------------------------------------------------------
# Public API: detect_wiring_deps
# ---------------------------------------------------------------------------


def detect_wiring_deps(tasks_md: str) -> dict[str, list[str]]:
    """Detect wiring dependencies from TASKS.md content.

    Parses the TASKS.md document and identifies tasks whose parent is a
    ``WIRE-xxx`` requirement.  For each such wiring task, collects the
    implementation task IDs listed in its ``Dependencies`` field.

    Parameters
    ----------
    tasks_md:
        Raw string content of TASKS.md.

    Returns
    -------
    dict[str, list[str]]
        Maps each ``WIRE-xxx`` ID to the list of implementation ``TASK-xxx``
        IDs that must complete before the wiring task can start.

        Example::

            {
                "WIRE-001": ["TASK-001", "TASK-003"],
                "WIRE-002": ["TASK-004"],
            }

        If a ``WIRE-xxx`` parent appears on multiple tasks, the
        dependency lists are merged (deduplicated, sorted).

        Returns an empty dict if the content is empty, contains no
        tasks, or contains no WIRE-xxx parents.
    """
    if not tasks_md or not tasks_md.strip():
        return {}

    tasks = _parse_task_blocks(tasks_md)
    if not tasks:
        return {}

    # Build a set of all known task IDs for validation
    known_task_ids = {t.task_id for t in tasks}

    # Collect dependencies grouped by WIRE-xxx parent
    wire_deps: dict[str, set[str]] = {}

    for task in tasks:
        if task.wire_parent is None:
            continue

        wire_id = task.wire_parent

        if wire_id not in wire_deps:
            wire_deps[wire_id] = set()

        # Add all dependency task IDs that actually exist in the document
        for dep_id in task.dependencies:
            if dep_id in known_task_ids:
                wire_deps[wire_id].add(dep_id)

    # Convert sets to sorted lists for deterministic output
    return {
        wire_id: sorted(dep_ids)
        for wire_id, dep_ids in sorted(wire_deps.items())
    }


# ---------------------------------------------------------------------------
# Public API: build_wiring_schedule_hint
# ---------------------------------------------------------------------------


def build_wiring_schedule_hint(tasks_md: str) -> str:
    """Produce a human-readable wiring schedule summary for prompt injection.

    Generates a concise Markdown-formatted summary that describes which
    wiring tasks are waiting on which implementation tasks.  This summary
    can be injected into orchestration agent prompts so they understand
    scheduling constraints.

    Parameters
    ----------
    tasks_md:
        Raw string content of TASKS.md.

    Returns
    -------
    str
        A Markdown-formatted summary.  Returns a short message if there
        are no wiring dependencies to report.

        Example output::

            ## Wiring Schedule Constraints

            The following wiring tasks are blocked until their prerequisite
            implementation tasks complete:

            - **WIRE-001** (2 prerequisites):
              - Blocked by: TASK-001, TASK-003
              - Wiring tasks: TASK-005
            - **WIRE-002** (1 prerequisite):
              - Blocked by: TASK-004
              - Wiring tasks: TASK-008, TASK-009

            **Total:** 2 wiring groups, 3 prerequisite tasks.
    """
    if not tasks_md or not tasks_md.strip():
        return "No wiring dependencies detected (empty TASKS.md content)."

    wire_deps = detect_wiring_deps(tasks_md)
    if not wire_deps:
        return "No wiring dependencies detected. All tasks can be scheduled independently."

    # Also collect which task IDs belong to each WIRE parent for the summary
    tasks = _parse_task_blocks(tasks_md)
    wire_task_ids: dict[str, list[str]] = {}
    for task in tasks:
        if task.wire_parent is not None:
            wire_id = task.wire_parent
            if wire_id not in wire_task_ids:
                wire_task_ids[wire_id] = []
            wire_task_ids[wire_id].append(task.task_id)

    # Build the Markdown summary
    lines: list[str] = []
    lines.append("## Wiring Schedule Constraints")
    lines.append("")
    lines.append(
        "The following wiring tasks are blocked until their prerequisite "
        "implementation tasks complete:"
    )
    lines.append("")

    total_prereqs: set[str] = set()

    for wire_id in sorted(wire_deps):
        prereqs = wire_deps[wire_id]
        total_prereqs.update(prereqs)
        count = len(prereqs)
        plural = "prerequisite" if count == 1 else "prerequisites"

        wiring_tasks = sorted(wire_task_ids.get(wire_id, []))
        wiring_tasks_str = ", ".join(wiring_tasks) if wiring_tasks else "(none)"

        lines.append(f"- **{wire_id}** ({count} {plural}):")
        lines.append(f"  - Blocked by: {', '.join(prereqs)}")
        lines.append(f"  - Wiring tasks: {wiring_tasks_str}")

    lines.append("")
    lines.append(
        f"**Total:** {len(wire_deps)} wiring "
        f"{'group' if len(wire_deps) == 1 else 'groups'}, "
        f"{len(total_prereqs)} prerequisite "
        f"{'task' if len(total_prereqs) == 1 else 'tasks'}."
    )

    return "\n".join(lines)
