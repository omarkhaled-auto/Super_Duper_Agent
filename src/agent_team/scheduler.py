"""Smart scheduler for Agent Team -- DAG-based task scheduling.

Provides DAG construction, topological sorting (Kahn's algorithm),
wave-based parallel execution planning, file-conflict detection with
artificial-dependency resolution, and critical-path analysis via
forward/backward passes.

All algorithms are O(V+E) where V = tasks and E = dependency edges.
Zero external dependencies -- stdlib only.
"""

from __future__ import annotations

import logging
import re
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import SchedulerConfig

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TaskNode:
    """A single schedulable task parsed from TASKS.md."""

    id: str  # "TASK-001", "TASK-002", etc.
    title: str
    description: str
    files: list[str]  # files this task touches (POSIX-normalized)
    depends_on: list[str]  # task IDs this depends on
    status: str  # "PENDING" | "IN_PROGRESS" | "COMPLETE" | "FAILED"
    assigned_agent: str | None = None
    integration_declares: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FileConflict:
    """A detected file-level conflict between tasks in the same wave."""

    file_path: str
    task_ids: list[str]  # tasks that both touch this file
    conflict_type: str  # "write-write"
    resolution: str  # "artificial-dependency" | "integration-agent"


@dataclass
class ExecutionWave:
    """A group of tasks that can execute in parallel."""

    wave_number: int
    task_ids: list[str]  # tasks that can run in parallel
    estimated_conflicts: list[FileConflict] = field(default_factory=list)


@dataclass
class CriticalPathInfo:
    """Result of the critical-path analysis."""

    path: list[str]  # task IDs on the critical path
    total_length: int  # number of tasks on critical path
    bottleneck_tasks: list[str]  # tasks with zero slack


@dataclass
class ScheduleResult:
    """Complete scheduling output for a set of tasks."""

    waves: list[ExecutionWave]
    total_waves: int
    conflict_summary: dict[str, int]
    integration_tasks: list[str]
    critical_path: CriticalPathInfo


@dataclass
class FileContext:
    """Context about a single file relevant to a task."""

    path: str
    relevant_sections: list[str]
    role: str  # "modify" | "read-only" | "create"


@dataclass
class TaskContext:
    """Complete context package prepared for a task's agent."""

    task_id: str
    files: list[FileContext]
    contracts: list[str]
    integration_notes: str


# ---------------------------------------------------------------------------
# Compiled regexes for TASKS.md parsing
# ---------------------------------------------------------------------------

RE_TASK_ID = re.compile(r"^###\s+(TASK-\d+)(?::\s*(.+))?$", re.MULTILINE)
RE_DEPENDS = re.compile(
    r"-\s*(?:dependencies|depends\s*on|requires):\s*(.+)", re.IGNORECASE
)
RE_FILES = re.compile(
    r"-\s*(?:files|targets|modifies):\s*(.+)", re.IGNORECASE
)
RE_STATUS = re.compile(r"-\s*(?:status):\s*(\w+)", re.IGNORECASE)
RE_PARENT = re.compile(r"-\s*(?:parent):\s*(.+)", re.IGNORECASE)
RE_DESC = re.compile(
    r"-\s*(?:description):\s*(.+)", re.IGNORECASE | re.DOTALL
)

_TASK_ID_PATTERN = re.compile(r"TASK-\d+")


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


def normalize_file_path(path: str) -> str:
    """Normalize a file path to POSIX forward-slash format.

    Converts backslashes to forward slashes and strips any leading ``./``
    prefix so that paths are comparable across platforms.
    """
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


# ---------------------------------------------------------------------------
# TASKS.md parsing
# ---------------------------------------------------------------------------


def _parse_dependency_list(raw: str) -> list[str]:
    """Extract TASK-xxx IDs from a comma-separated dependency string.

    Handles formats like:
    - ``TASK-001, TASK-002``
    - ``TASK-001``
    - ``none`` / ``None`` / ``N/A``
    """
    if not raw or raw.strip().lower() in ("none", "n/a", "-", ""):
        return []
    tokens = [t.strip() for t in raw.split(",")]
    return [t for t in tokens if _TASK_ID_PATTERN.match(t)]


def _parse_file_list(raw: str) -> list[str]:
    """Extract and normalize file paths from a comma-separated string."""
    if not raw or raw.strip().lower() in ("none", "n/a", "-", ""):
        return []
    tokens = [t.strip() for t in raw.split(",")]
    return [normalize_file_path(t) for t in tokens if t]


def _extract_description(block: str, field_lines: set[int]) -> str:
    """Extract the task description from remaining non-field text.

    Uses two strategies in order:
    1. An explicit ``- Description: ...`` field (may span multiple lines).
    2. All non-field, non-header, non-blank lines concatenated.
    """
    lines = block.splitlines()

    # Strategy 1: explicit description field
    desc_match = RE_DESC.search(block)
    if desc_match:
        # Grab the first line of the description field
        first_line = desc_match.group(1).strip()
        # Check for continuation lines (indented or not starting with ``-``)
        start_idx = block[: desc_match.start()].count("\n")
        continuation: list[str] = [first_line]
        for line in lines[start_idx + 1 :]:
            stripped = line.strip()
            # Stop on the next field line or blank line
            if not stripped or (stripped.startswith("-") and ":" in stripped):
                break
            continuation.append(stripped)
        return " ".join(continuation)

    # Strategy 2: collect non-field text
    remaining: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("###"):
            continue
        if i in field_lines:
            continue
        if stripped.startswith("-") and ":" in stripped[:40]:
            continue
        remaining.append(stripped)
    return " ".join(remaining)


def parse_tasks_md(content: str) -> list[TaskNode]:
    """Parse a TASKS.md document into a list of :class:`TaskNode` objects.

    The parser uses a block-splitting state machine: it splits the document
    at ``### TASK-`` headers via :func:`re.split`, then extracts structured
    fields from each block using compiled regexes.
    """
    # Split at task headers, keeping the header in each block
    blocks = re.split(r"(?=^###\s+TASK-)", content, flags=re.MULTILINE)

    tasks: list[TaskNode] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract task ID and optional title from the header line
        id_match = RE_TASK_ID.search(block)
        if not id_match:
            continue  # not a task block (e.g. preamble)

        task_id = id_match.group(1)
        title = (id_match.group(2) or "").strip()

        # Track which lines are field lines so we can extract description
        field_lines: set[int] = set()

        # Dependencies
        depends_on: list[str] = []
        dep_match = RE_DEPENDS.search(block)
        if dep_match:
            depends_on = _parse_dependency_list(dep_match.group(1))
            line_num = block[: dep_match.start()].count("\n")
            field_lines.add(line_num)

        # Files
        files: list[str] = []
        files_match = RE_FILES.search(block)
        if files_match:
            files = _parse_file_list(files_match.group(1))
            line_num = block[: files_match.start()].count("\n")
            field_lines.add(line_num)

        # Status (default PENDING)
        status = "PENDING"
        status_match = RE_STATUS.search(block)
        if status_match:
            status = status_match.group(1).upper()
            line_num = block[: status_match.start()].count("\n")
            field_lines.add(line_num)

        # Parent (tracked via field_lines but not stored separately)
        parent_match = RE_PARENT.search(block)
        if parent_match:
            line_num = block[: parent_match.start()].count("\n")
            field_lines.add(line_num)

        # Description
        description = _extract_description(block, field_lines)

        tasks.append(
            TaskNode(
                id=task_id,
                title=title,
                description=description,
                files=files,
                depends_on=depends_on,
                status=status,
            )
        )

    return tasks


def update_tasks_md_statuses(
    content: str,
    completed_ids: set[str] | None = None,
) -> str:
    """Update task statuses in TASKS.md content.

    For each ``### TASK-xxx`` block, if the task ID is in *completed_ids*
    (or *completed_ids* is ``None`` meaning mark ALL complete), the
    ``- Status: PENDING`` line is replaced with ``- Status: COMPLETE``.

    Returns the updated Markdown string.  Non-task content is preserved
    verbatim.
    """
    if completed_ids is not None and not completed_ids:
        return content  # empty set → nothing to update

    lines = content.split("\n")
    current_task_id: str | None = None
    result: list[str] = []

    for line in lines:
        # Detect task header (### TASK-001: ...)
        stripped = line.strip()
        if stripped.startswith("###"):
            id_match = RE_TASK_ID.match(stripped)
            if id_match:
                current_task_id = id_match.group(1)

        # Replace status line if task should be marked complete
        if current_task_id is not None:
            status_match = RE_STATUS.match(stripped)
            if status_match:
                old_status = status_match.group(1).upper()
                should_update = (
                    completed_ids is None or current_task_id in completed_ids
                )
                if should_update and old_status == "PENDING":
                    line = line.replace(
                        status_match.group(1), "COMPLETE"
                    )

        result.append(line)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Dependency graph construction
# ---------------------------------------------------------------------------


def build_dependency_graph(tasks: list[TaskNode]) -> dict[str, list[str]]:
    """Build a forward adjacency list from task dependencies.

    Edge direction: if task B depends on task A, the edge goes ``A -> B``
    (A is a predecessor of B; B is a successor of A).

    Returns a dict mapping each task ID to the list of task IDs that
    depend on it (its successors).
    """
    graph: dict[str, list[str]] = {t.id: [] for t in tasks}
    task_ids = {t.id for t in tasks}

    for task in tasks:
        for dep_id in task.depends_on:
            if dep_id in task_ids:
                # dep_id -> task.id  (task depends on dep_id)
                if task.id not in graph[dep_id]:
                    graph[dep_id].append(task.id)

    return graph


# ---------------------------------------------------------------------------
# Graph validation
# ---------------------------------------------------------------------------


def _detect_cycles_dfs(
    graph: dict[str, list[str]], all_nodes: set[str]
) -> list[str]:
    """Detect cycles using DFS three-color marking.

    Colors:
    - WHITE (0): unvisited
    - GRAY  (1): currently in the recursion stack
    - BLACK (2): fully processed

    Returns a list of error messages describing any cycles found.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in all_nodes}
    errors: list[str] = []

    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if color.get(neighbor) == GRAY:
                # Found a cycle: extract the cycle portion
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                errors.append(
                    f"Cycle detected: {' -> '.join(cycle)}"
                )
            elif color.get(neighbor) == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for node in sorted(all_nodes):
        if color[node] == WHITE:
            dfs(node, [])

    return errors


def validate_graph(
    graph: dict[str, list[str]], tasks: list[TaskNode]
) -> list[str]:
    """Validate the dependency graph for common errors.

    Checks performed:
    1. **Cycle detection** -- DFS three-color marking.
    2. **Missing dependencies** -- task references a dependency that
       does not exist in the task list.
    3. **Orphan detection** -- tasks with no predecessors AND no
       successors (completely disconnected, not just root nodes).

    Returns a list of human-readable error/warning messages.
    An empty list means the graph is valid.
    """
    errors: list[str] = []
    task_ids = {t.id for t in tasks}

    # 1. Missing dependencies
    for task in tasks:
        for dep_id in task.depends_on:
            if dep_id not in task_ids:
                errors.append(
                    f"Task {task.id} depends on unknown task {dep_id}"
                )

    # 2. Cycle detection
    cycle_errors = _detect_cycles_dfs(graph, task_ids)
    errors.extend(cycle_errors)

    # 3. Orphan detection (tasks with no edges at all)
    has_predecessor = set()
    has_successor = set()
    for node, successors in graph.items():
        if successors:
            has_successor.add(node)
            for s in successors:
                has_predecessor.add(s)

    for task in tasks:
        if (
            task.id not in has_predecessor
            and task.id not in has_successor
            and len(tasks) > 1
        ):
            errors.append(
                f"Warning: Task {task.id} is an orphan "
                f"(no dependencies and no dependents)"
            )

    return errors


# ---------------------------------------------------------------------------
# Topological sort (Kahn's algorithm)
# ---------------------------------------------------------------------------


def topological_sort(
    graph: dict[str, list[str]], in_degree: dict[str, int]
) -> list[str]:
    """Topological sort using Kahn's algorithm.

    Complexity: O(V + E) where V is the number of tasks and E is the
    number of dependency edges.

    Cycle detection: if ``len(result) != len(in_degree)`` after
    processing, the graph contains a cycle (some nodes could never
    reach in-degree zero).

    Parameters
    ----------
    graph:
        Forward adjacency list ``{node: [successors]}``.
    in_degree:
        In-degree counts ``{node: count}``.

    Returns
    -------
    list[str]
        Tasks in topological order.  If a cycle exists, the returned
        list will be shorter than the total number of nodes.
    """
    remaining = dict(in_degree)
    queue: deque[str] = deque()

    # Seed queue with all zero-in-degree nodes (sorted for determinism)
    for node in sorted(remaining):
        if remaining[node] == 0:
            queue.append(node)

    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for successor in sorted(graph.get(node, [])):
            remaining[successor] -= 1
            if remaining[successor] == 0:
                queue.append(successor)

    return result


# ---------------------------------------------------------------------------
# Execution wave computation
# ---------------------------------------------------------------------------


def _build_in_degree(
    tasks: list[TaskNode], graph: dict[str, list[str]]
) -> dict[str, int]:
    """Compute in-degree for every task from the forward adjacency list."""
    in_deg: dict[str, int] = {t.id: 0 for t in tasks}
    for _node, successors in graph.items():
        for succ in successors:
            if succ in in_deg:
                in_deg[succ] += 1
    return in_deg


def compute_execution_waves(
    tasks: list[TaskNode],
    graph: dict[str, list[str]],
    *,
    max_parallel_tasks: int | None = None,
) -> list[ExecutionWave]:
    """Compute parallel execution waves using level-by-level Kahn's.

    Tasks with in-degree 0 form wave 1.  After removing those tasks
    and decrementing successor in-degrees, the next batch of
    in-degree-0 tasks forms wave 2, and so on.

    When *max_parallel_tasks* is set and positive, each "ready" batch
    is split into sub-waves of at most that many tasks.

    Returns a list of :class:`ExecutionWave` with ``wave_number``
    starting at 1.  If a cycle is detected (no ready tasks but
    remaining nodes exist), the function stops early.
    """
    in_degree = _build_in_degree(tasks, graph)

    waves: list[ExecutionWave] = []
    wave_num = 1
    remaining = dict(in_degree)

    while remaining:
        # Find all nodes with in-degree 0
        ready = sorted(t for t, deg in remaining.items() if deg == 0)
        if not ready:
            break  # cycle detected -- cannot proceed

        # Split ready batch into sub-waves if max_parallel_tasks is set
        if max_parallel_tasks is not None and max_parallel_tasks > 0 and len(ready) > max_parallel_tasks:
            chunks = [ready[i:i + max_parallel_tasks] for i in range(0, len(ready), max_parallel_tasks)]
        else:
            chunks = [ready]

        for chunk in chunks:
            wave = ExecutionWave(wave_number=wave_num, task_ids=chunk)
            waves.append(wave)
            wave_num += 1

        # Remove all ready nodes and decrement successors' in-degrees
        for t in ready:
            del remaining[t]
            for succ in graph.get(t, []):
                if succ in remaining:
                    remaining[succ] -= 1

    return waves


# ---------------------------------------------------------------------------
# File-conflict detection
# ---------------------------------------------------------------------------


def detect_file_conflicts(
    wave: ExecutionWave,
    tasks: dict[str, TaskNode],
    *,
    conflict_strategy: str | None = None,
) -> list[FileConflict]:
    """Detect file-level conflicts within a single execution wave.

    All file accesses are treated as writes (conservative assumption).
    If two or more tasks in the same wave touch the same file, a
    ``write-write`` conflict is reported.

    Parameters
    ----------
    wave:
        The execution wave to check.
    tasks:
        Mapping of task ID to :class:`TaskNode` for lookup.
    conflict_strategy:
        Resolution strategy for detected conflicts.  Defaults to
        ``"artificial-dependency"`` when ``None``.

    Returns
    -------
    list[FileConflict]
        Detected conflicts, sorted by file path for determinism.
    """
    effective_strategy = conflict_strategy or "artificial-dependency"

    # Build a map of file -> list of task IDs that touch it
    file_to_tasks: dict[str, list[str]] = {}
    for task_id in wave.task_ids:
        task = tasks.get(task_id)
        if not task:
            continue
        for f in task.files:
            normalized = normalize_file_path(f)
            if normalized not in file_to_tasks:
                file_to_tasks[normalized] = []
            file_to_tasks[normalized].append(task_id)

    conflicts: list[FileConflict] = []
    for file_path in sorted(file_to_tasks):
        task_ids = file_to_tasks[file_path]
        if len(task_ids) > 1:
            conflicts.append(
                FileConflict(
                    file_path=file_path,
                    task_ids=sorted(task_ids),
                    conflict_type="write-write",
                    resolution=effective_strategy,
                )
            )

    return conflicts


# ---------------------------------------------------------------------------
# Conflict resolution via artificial dependency injection
# ---------------------------------------------------------------------------


def resolve_conflicts_via_dependency(
    tasks: list[TaskNode], conflicts: list[FileConflict]
) -> list[TaskNode]:
    """Resolve file conflicts by injecting artificial dependency edges.

    For each conflict, the conflicting task IDs are sorted
    deterministically, and a chain of dependencies is created:
    ``task_ids[1]`` depends on ``task_ids[0]``,
    ``task_ids[2]`` depends on ``task_ids[1]``, etc.

    This serializes access to the conflicting file while keeping
    the rest of the schedule as parallel as possible.

    Parameters
    ----------
    tasks:
        The full list of tasks (modified in-place).
    conflicts:
        Conflicts detected by :func:`detect_file_conflicts`.

    Returns
    -------
    list[TaskNode]
        The same task list with updated ``depends_on`` fields.
    """
    task_map = {t.id: t for t in tasks}

    for conflict in conflicts:
        sorted_ids = sorted(conflict.task_ids)
        for i in range(1, len(sorted_ids)):
            later = task_map[sorted_ids[i]]
            earlier_id = sorted_ids[i - 1]
            if earlier_id not in later.depends_on:
                later.depends_on.append(earlier_id)

    return tasks


# ---------------------------------------------------------------------------
# Critical-path analysis (forward/backward pass)
# ---------------------------------------------------------------------------


def compute_critical_path(
    tasks: list[TaskNode], graph: dict[str, list[str]]
) -> CriticalPathInfo:
    """Compute the critical path through the task DAG.

    Uses a two-pass approach assuming uniform task duration of 1:

    **Forward pass** (earliest start/finish):
    - ``earliest_start[t] = max(earliest_finish[dep] for dep in predecessors)``
    - ``earliest_finish[t] = earliest_start[t] + 1``

    **Backward pass** (latest start/finish):
    - ``latest_finish[t] = min(latest_start[succ] for succ in successors)``
    - ``latest_start[t] = latest_finish[t] - 1``

    **Slack** = ``latest_start[t] - earliest_start[t]``.
    Tasks with zero slack lie on the critical path.

    Returns
    -------
    CriticalPathInfo
        The critical path, its length, and the bottleneck tasks.
    """
    if not tasks:
        return CriticalPathInfo(path=[], total_length=0, bottleneck_tasks=[])

    task_ids = [t.id for t in tasks]

    # Build reverse graph (predecessors)
    predecessors: dict[str, list[str]] = {t: [] for t in task_ids}
    for node, succs in graph.items():
        for s in succs:
            if s in predecessors:
                predecessors[s].append(node)

    # Compute in-degree for topological sort
    in_degree = _build_in_degree(tasks, graph)

    # Get topological order
    topo_order = topological_sort(graph, in_degree)

    # -- Forward pass --
    earliest_start: dict[str, int] = {t: 0 for t in task_ids}
    earliest_finish: dict[str, int] = {t: 1 for t in task_ids}

    for t in topo_order:
        preds = predecessors.get(t, [])
        if preds:
            earliest_start[t] = max(earliest_finish[p] for p in preds)
        earliest_finish[t] = earliest_start[t] + 1

    # -- Backward pass --
    max_finish = max(earliest_finish.values()) if earliest_finish else 0

    latest_finish: dict[str, int] = {t: max_finish for t in task_ids}
    latest_start: dict[str, int] = {t: max_finish - 1 for t in task_ids}

    for t in reversed(topo_order):
        succs = graph.get(t, [])
        if succs:
            latest_finish[t] = min(latest_start[s] for s in succs)
        latest_start[t] = latest_finish[t] - 1

    # -- Slack and critical path --
    slack: dict[str, int] = {
        t: latest_start[t] - earliest_start[t] for t in task_ids
    }
    critical = [t for t in topo_order if slack[t] == 0]

    return CriticalPathInfo(
        path=critical,
        total_length=len(critical),
        bottleneck_tasks=critical,
    )


# ---------------------------------------------------------------------------
# Full scheduling pipeline
# ---------------------------------------------------------------------------


def compute_schedule(
    tasks: list[TaskNode],
    *,
    scheduler_config: "SchedulerConfig | None" = None,
) -> ScheduleResult:
    """Run the full scheduling pipeline.

    Steps:
    1. **Validate** the dependency graph (cycles, missing deps, orphans).
    2. **Build** the forward adjacency list.
    3. **Compute waves** via level-by-level Kahn's algorithm.
    4. **Detect conflicts** within each wave.
    5. **Resolve conflicts** by injecting artificial dependencies.
    6. **Recompute waves** after conflict resolution.
    7. **Compute the critical path** via forward/backward passes.

    Parameters
    ----------
    tasks:
        List of parsed task nodes.
    scheduler_config:
        Optional scheduler configuration. When provided, honours
        ``max_parallel_tasks``, ``conflict_strategy``,
        ``enable_critical_path``, and ``enable_context_scoping``.

    Raises
    ------
    ValueError
        If the graph contains cycles or references missing tasks.

    Returns
    -------
    ScheduleResult
        Complete scheduling output including waves, conflict summary,
        integration tasks, and critical-path information.
    """
    if not tasks:
        return ScheduleResult(
            waves=[],
            total_waves=0,
            conflict_summary={},
            integration_tasks=[],
            critical_path=CriticalPathInfo(
                path=[], total_length=0, bottleneck_tasks=[]
            ),
        )

    # Extract config values (all default to None / True for backwards compat)
    max_parallel = None
    conflict_strat = None
    enable_cp = True
    if scheduler_config is not None:
        max_parallel = scheduler_config.max_parallel_tasks
        conflict_strat = scheduler_config.conflict_strategy
        enable_cp = scheduler_config.enable_critical_path
        if not scheduler_config.enable_context_scoping:
            _logger.info("Context scoping disabled via config.")

    if conflict_strat == "integration-agent":
        _logger.warning(
            "conflict_strategy='integration-agent' is not fully implemented; "
            "falling back to 'artificial-dependency' for conflict resolution."
        )

    # Step 1: Build graph and validate
    graph = build_dependency_graph(tasks)
    errors = validate_graph(graph, tasks)

    # Separate hard errors from warnings
    hard_errors = [e for e in errors if not e.startswith("Warning:")]
    if hard_errors:
        raise ValueError(
            "Dependency graph validation failed:\n"
            + "\n".join(hard_errors)
        )

    # Step 2: Initial wave computation
    waves = compute_execution_waves(tasks, graph, max_parallel_tasks=max_parallel)

    # Step 3: Detect conflicts across all waves
    task_map = {t.id: t for t in tasks}
    all_conflicts: list[FileConflict] = []
    for wave in waves:
        wave_conflicts = detect_file_conflicts(wave, task_map, conflict_strategy=conflict_strat)
        wave.estimated_conflicts = wave_conflicts
        all_conflicts.extend(wave_conflicts)

    # Step 4: Resolve conflicts if any were found
    if all_conflicts:
        tasks = resolve_conflicts_via_dependency(tasks, all_conflicts)

        # Rebuild graph and recompute waves after resolution
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph, max_parallel_tasks=max_parallel)

        # Re-detect to capture any residual conflicts
        for wave in waves:
            wave.estimated_conflicts = detect_file_conflicts(
                wave, task_map, conflict_strategy=conflict_strat
            )

    # Step 5: Compute critical path (gated by config)
    if enable_cp:
        critical_path = compute_critical_path(tasks, graph)
    else:
        critical_path = CriticalPathInfo(path=[], total_length=0, bottleneck_tasks=[])

    # Step 6: Build conflict summary
    conflict_summary: dict[str, int] = {}
    for conflict in all_conflicts:
        ctype = conflict.conflict_type
        conflict_summary[ctype] = conflict_summary.get(ctype, 0) + 1

    # Step 7: Identify integration tasks (tasks with integration_declares)
    integration_tasks = [
        t.id for t in tasks if t.integration_declares
    ]

    return ScheduleResult(
        waves=waves,
        total_waves=len(waves),
        conflict_summary=conflict_summary,
        integration_tasks=integration_tasks,
        critical_path=critical_path,
    )


# ---------------------------------------------------------------------------
# Context scoping -- determine what each agent needs
# ---------------------------------------------------------------------------


def compute_file_context(
    task: TaskNode, codebase_map: "CodebaseMap | None" = None
) -> list[FileContext]:
    """Determine exactly which files (and which sections) an agent needs.

    For each file listed in the task:
    - If the file exists (inferable from ``codebase_map``), it is a
      ``modify`` target.
    - If the file does not exist, it is a ``create`` target.

    When no ``codebase_map`` is available, all files default to
    ``modify`` and relevant sections are left empty (the agent will
    read the full file).

    Parameters
    ----------
    task:
        The task whose file context to compute.
    codebase_map:
        Optional codebase map for richer section-level scoping.

    Returns
    -------
    list[FileContext]
        Ordered list of file contexts for the task's agent.
    """
    contexts: list[FileContext] = []

    for file_path in task.files:
        normalized = normalize_file_path(file_path)
        role = "modify"  # default assumption
        relevant_sections: list[str] = []

        if codebase_map is not None:
            # Use codebase map to determine role and sections
            existing_files = set()
            # Duck-type: expect codebase_map to have a files attribute or
            # be iterable of file paths
            if hasattr(codebase_map, "files"):
                existing_files = {
                    normalize_file_path(f)
                    for f in codebase_map.files  # type: ignore[union-attr]
                }
            elif hasattr(codebase_map, "file_map"):
                existing_files = {
                    normalize_file_path(f)
                    for f in codebase_map.file_map  # type: ignore[union-attr]
                }

            if normalized not in existing_files:
                role = "create"

            # If the codebase map provides section info, use it
            if hasattr(codebase_map, "get_sections"):
                sections = codebase_map.get_sections(normalized)  # type: ignore[union-attr]
                if sections:
                    relevant_sections = list(sections)
        else:
            # Without a codebase map we cannot distinguish create vs modify;
            # default to modify and let the agent figure it out.
            pass

        contexts.append(
            FileContext(
                path=normalized,
                relevant_sections=relevant_sections,
                role=role,
            )
        )

    # Add dependency files as read-only context
    # (files from tasks this one depends on)
    seen_paths = {normalize_file_path(f) for f in task.files}
    # Note: the caller would need to pass full task list for this;
    # we keep it as a simple pass for now since depends_on contains IDs,
    # not file paths.

    return contexts


def build_task_context(
    task: TaskNode,
    codebase_map: "CodebaseMap | None" = None,
    contracts: list[str] | None = None,
) -> TaskContext:
    """Build the complete context package for a task's agent.

    Combines file context, contract information, and integration notes
    into a single :class:`TaskContext` that can be rendered as markdown
    and injected into the agent's prompt.

    Parameters
    ----------
    task:
        The task to build context for.
    codebase_map:
        Optional codebase map for file-level scoping.
    contracts:
        Optional list of interface contract strings relevant to this task.

    Returns
    -------
    TaskContext
        The assembled context package.
    """
    files = compute_file_context(task, codebase_map)

    # Build integration notes from the task's integration_declares
    integration_parts: list[str] = []
    if task.integration_declares:
        for key, values in task.integration_declares.items():
            integration_parts.append(
                f"- {key}: {', '.join(values)}"
            )
    integration_notes = "\n".join(integration_parts) if integration_parts else ""

    return TaskContext(
        task_id=task.id,
        files=files,
        contracts=contracts or [],
        integration_notes=integration_notes,
    )


def render_task_context_md(ctx: TaskContext) -> str:
    """Render a :class:`TaskContext` as markdown for agent prompt injection.

    The output is a self-contained markdown section that an agent can
    read to understand its assignment scope, relevant files, interface
    contracts, and integration requirements.

    Parameters
    ----------
    ctx:
        The task context to render.

    Returns
    -------
    str
        Markdown-formatted context string.
    """
    lines: list[str] = []

    lines.append(f"## Task Context: {ctx.task_id}")
    lines.append("")

    # Files section
    if ctx.files:
        lines.append("### Files")
        lines.append("")
        for fc in ctx.files:
            role_badge = f"[{fc.role.upper()}]"
            lines.append(f"- {role_badge} `{fc.path}`")
            if fc.relevant_sections:
                for section in fc.relevant_sections:
                    lines.append(f"  - Section: {section}")
        lines.append("")

    # Contracts section
    if ctx.contracts:
        lines.append("### Interface Contracts")
        lines.append("")
        for contract in ctx.contracts:
            lines.append(f"- {contract}")
        lines.append("")

    # Integration notes section
    if ctx.integration_notes:
        lines.append("### Integration Notes")
        lines.append("")
        lines.append(ctx.integration_notes)
        lines.append("")

    return "\n".join(lines)
