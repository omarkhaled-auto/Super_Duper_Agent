"""Comprehensive tests for agent_team.scheduler -- DAG scheduling module.

Covers parsing, graph construction, validation, topological sort,
wave computation, file-conflict detection/resolution, critical-path
analysis, path normalization, task context building, and the full
end-to-end compute_schedule pipeline.
"""

from __future__ import annotations

import pytest

from agent_team.scheduler import (
    CriticalPathInfo,
    ExecutionWave,
    FileConflict,
    ScheduleResult,
    TaskContext,
    TaskNode,
    build_dependency_graph,
    build_task_context,
    compute_critical_path,
    compute_execution_waves,
    compute_milestone_schedule,
    compute_schedule,
    detect_file_conflicts,
    filter_tasks_by_milestone,
    format_schedule_for_prompt,
    normalize_file_path,
    parse_tasks_md,
    resolve_conflicts_via_dependency,
    topological_sort,
    validate_graph,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_TASKS_MD = """# Task Breakdown: Test Project
Generated: 2025-01-01
Total Tasks: 4
Completed: 0/4

## Tasks

### TASK-001: Setup project structure
- Parent: TECH-001
- Status: PENDING
- Dependencies: none
- Files: src/config.py, src/main.py
- Description: Create the initial project scaffolding

### TASK-002: Create user model
- Parent: REQ-001
- Status: PENDING
- Dependencies: TASK-001
- Files: src/models/user.py
- Description: Define the User model with fields: id, name, email

### TASK-003: Create auth service
- Parent: REQ-002
- Status: PENDING
- Dependencies: TASK-001
- Files: src/services/auth.py
- Description: Implement authentication service

### TASK-004: Wire auth to server
- Parent: WIRE-001
- Status: PENDING
- Dependencies: TASK-002, TASK-003
- Files: src/server.py
- Description: Register auth routes on the express server
"""


def _make_node(
    task_id: str,
    title: str = "",
    files: list[str] | None = None,
    depends_on: list[str] | None = None,
    status: str = "PENDING",
) -> TaskNode:
    """Helper to build a TaskNode with sensible defaults."""
    return TaskNode(
        id=task_id,
        title=title or task_id,
        description=f"Description for {task_id}",
        files=files or [],
        depends_on=depends_on or [],
        status=status,
    )


# ===================================================================
# 1. TASKS.md Parsing Tests
# ===================================================================


class TestParseTasksMd:
    """Verify that parse_tasks_md correctly extracts TaskNode objects."""

    def test_valid_document(self):
        """Parse a well-formed TASKS.md with 4 tasks."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        assert len(tasks) == 4
        ids = [t.id for t in tasks]
        assert ids == ["TASK-001", "TASK-002", "TASK-003", "TASK-004"]

    def test_empty_content(self):
        """Empty string yields no tasks."""
        tasks = parse_tasks_md("")
        assert tasks == []

    def test_no_tasks(self):
        """Header-only content with no task blocks yields nothing."""
        content = "# Task Breakdown: Empty\nGenerated: 2025-01-01\n\n## Tasks\n"
        tasks = parse_tasks_md(content)
        assert tasks == []

    def test_task_with_all_fields(self):
        """Each parsed task should carry correct ID, status, deps, files, description."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        t4 = next(t for t in tasks if t.id == "TASK-004")
        assert t4.title == "Wire auth to server"
        assert t4.status == "PENDING"
        assert sorted(t4.depends_on) == ["TASK-002", "TASK-003"]
        assert t4.files == ["src/server.py"]
        assert "auth routes" in t4.description.lower()

    def test_task_minimal_fields(self):
        """A task block with only ID and title (no fields) still parses."""
        content = "### TASK-099: Minimal task\n"
        tasks = parse_tasks_md(content)
        assert len(tasks) == 1
        assert tasks[0].id == "TASK-099"
        assert tasks[0].title == "Minimal task"
        assert tasks[0].depends_on == []
        assert tasks[0].files == []
        assert tasks[0].status == "PENDING"

    def test_dependencies_parsing(self):
        """Dependencies: TASK-001, TASK-002 should produce a two-element list."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        t4 = next(t for t in tasks if t.id == "TASK-004")
        assert set(t4.depends_on) == {"TASK-002", "TASK-003"}

    def test_dependencies_none_keyword(self):
        """Dependencies: none should produce an empty list."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        t1 = next(t for t in tasks if t.id == "TASK-001")
        assert t1.depends_on == []

    def test_files_parsing(self):
        """Files: src/config.py, src/main.py should produce two normalized paths."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        t1 = next(t for t in tasks if t.id == "TASK-001")
        assert t1.files == ["src/config.py", "src/main.py"]

    def test_status_parsing(self):
        """Status should be upper-cased and captured correctly."""
        content = (
            "### TASK-050: Status test\n"
            "- Status: in_progress\n"
            "- Description: Check casing\n"
        )
        tasks = parse_tasks_md(content)
        assert tasks[0].status == "IN_PROGRESS"

    def test_status_defaults_to_pending(self):
        """When no status field is present, default to PENDING."""
        content = "### TASK-051: No status\n- Description: Missing status\n"
        tasks = parse_tasks_md(content)
        assert tasks[0].status == "PENDING"

    def test_multiline_description(self):
        """Description field is extracted as a string (even if one line)."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        t2 = next(t for t in tasks if t.id == "TASK-002")
        assert "user model" in t2.description.lower() or "User" in t2.description

    def test_multiple_tasks_order_preserved(self):
        """Tasks should be returned in document order."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        assert [t.id for t in tasks] == [
            "TASK-001",
            "TASK-002",
            "TASK-003",
            "TASK-004",
        ]


# ===================================================================
# 2. Graph Building Tests
# ===================================================================


class TestBuildDependencyGraph:
    """Verify build_dependency_graph produces correct forward adjacency lists."""

    def test_linear_chain(self):
        """A -> B -> C: A has successor B, B has successor C."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        graph = build_dependency_graph([a, b, c])
        assert "B" in graph["A"]
        assert "C" in graph["B"]
        assert graph["C"] == []

    def test_diamond(self):
        """Diamond: A -> B, A -> C, B -> D, C -> D."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["B", "C"])
        graph = build_dependency_graph([a, b, c, d])
        assert set(graph["A"]) == {"B", "C"}
        assert "D" in graph["B"]
        assert "D" in graph["C"]
        assert graph["D"] == []

    def test_fan_out(self):
        """Fan-out: A -> B, A -> C, A -> D."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["A"])
        graph = build_dependency_graph([a, b, c, d])
        assert set(graph["A"]) == {"B", "C", "D"}

    def test_fan_in(self):
        """Fan-in: A, B, C -> D."""
        a = _make_node("A")
        b = _make_node("B")
        c = _make_node("C")
        d = _make_node("D", depends_on=["A", "B", "C"])
        graph = build_dependency_graph([a, b, c, d])
        assert "D" in graph["A"]
        assert "D" in graph["B"]
        assert "D" in graph["C"]
        assert graph["D"] == []

    def test_no_dependencies(self):
        """Independent tasks: every node has an empty successor list."""
        tasks = [_make_node("X"), _make_node("Y"), _make_node("Z")]
        graph = build_dependency_graph(tasks)
        for node_id in ("X", "Y", "Z"):
            assert graph[node_id] == []

    def test_disconnected_components(self):
        """Two independent chains: A->B and C->D."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C")
        d = _make_node("D", depends_on=["C"])
        graph = build_dependency_graph([a, b, c, d])
        assert graph["A"] == ["B"]
        assert graph["B"] == []
        assert graph["C"] == ["D"]
        assert graph["D"] == []

    def test_unknown_dependency_ignored(self):
        """A dependency referencing a non-existent task is silently skipped."""
        a = _make_node("A", depends_on=["GHOST"])
        graph = build_dependency_graph([a])
        assert graph["A"] == []

    def test_no_duplicate_edges(self):
        """Even if depends_on is listed twice, graph should not duplicate."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A", "A"])
        graph = build_dependency_graph([a, b])
        assert graph["A"].count("B") == 1


# ===================================================================
# 3. Graph Validation Tests
# ===================================================================


class TestValidateGraph:
    """Verify validate_graph catches cycles, missing deps, and orphans."""

    def test_valid_graph(self):
        """A clean DAG should produce no errors."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        tasks = [a, b]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        assert errors == []

    def test_cycle_detected(self):
        """A -> B -> A should report a cycle."""
        a = _make_node("A", depends_on=["B"])
        b = _make_node("B", depends_on=["A"])
        tasks = [a, b]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        cycle_errors = [e for e in errors if "Cycle" in e or "cycle" in e.lower()]
        assert len(cycle_errors) >= 1

    def test_complex_cycle(self):
        """A -> B -> C -> A should report a cycle."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        # Inject cyclic dependency: A depends on C
        a.depends_on = ["C"]
        tasks = [a, b, c]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        cycle_errors = [e for e in errors if "Cycle" in e or "cycle" in e.lower()]
        assert len(cycle_errors) >= 1

    def test_missing_dependency(self):
        """Task referencing a non-existent task should produce an error."""
        a = _make_node("A", depends_on=["MISSING-001"])
        tasks = [a]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        missing_errors = [e for e in errors if "unknown" in e.lower() or "MISSING" in e]
        assert len(missing_errors) == 1

    def test_orphan_detection(self):
        """A task with no predecessors AND no successors among 2+ tasks is an orphan."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        orphan = _make_node("ORPHAN")
        tasks = [a, b, orphan]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        orphan_warnings = [e for e in errors if "orphan" in e.lower()]
        assert len(orphan_warnings) == 1
        assert "ORPHAN" in orphan_warnings[0]

    def test_single_task_no_orphan_warning(self):
        """A single task alone should NOT be flagged as orphan."""
        solo = _make_node("SOLO")
        tasks = [solo]
        graph = build_dependency_graph(tasks)
        errors = validate_graph(graph, tasks)
        orphan_warnings = [e for e in errors if "orphan" in e.lower()]
        assert orphan_warnings == []


# ===================================================================
# 4. Topological Sort Tests
# ===================================================================


class TestTopologicalSort:
    """Verify topological_sort produces valid orderings."""

    def _build_in_degree(self, tasks, graph):
        """Helper to compute in-degree from forward graph."""
        in_deg = {t.id: 0 for t in tasks}
        for _node, succs in graph.items():
            for s in succs:
                if s in in_deg:
                    in_deg[s] += 1
        return in_deg

    def test_linear_chain(self):
        """A -> B -> C should produce [A, B, C]."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        tasks = [a, b, c]
        graph = build_dependency_graph(tasks)
        in_deg = self._build_in_degree(tasks, graph)
        order = topological_sort(graph, in_deg)
        assert order == ["A", "B", "C"]

    def test_diamond(self):
        """Diamond shape: A before B and C, both before D."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["B", "C"])
        tasks = [a, b, c, d]
        graph = build_dependency_graph(tasks)
        in_deg = self._build_in_degree(tasks, graph)
        order = topological_sort(graph, in_deg)

        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_all_nodes_present(self):
        """Every task should appear exactly once in the sorted output."""
        tasks = [_make_node("X"), _make_node("Y"), _make_node("Z")]
        graph = build_dependency_graph(tasks)
        in_deg = self._build_in_degree(tasks, graph)
        order = topological_sort(graph, in_deg)
        assert set(order) == {"X", "Y", "Z"}
        assert len(order) == 3

    def test_respects_dependencies(self):
        """For every dependency edge dep -> task, dep must appear before task."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["B", "C"])
        tasks = [a, b, c, d]
        graph = build_dependency_graph(tasks)
        in_deg = self._build_in_degree(tasks, graph)
        order = topological_sort(graph, in_deg)

        for task in tasks:
            for dep_id in task.depends_on:
                assert order.index(dep_id) < order.index(task.id), (
                    f"{dep_id} should come before {task.id}"
                )

    def test_cycle_produces_short_result(self):
        """If a cycle exists, topological_sort returns fewer nodes than total."""
        a = _make_node("A", depends_on=["B"])
        b = _make_node("B", depends_on=["A"])
        tasks = [a, b]
        graph = build_dependency_graph(tasks)
        in_deg = self._build_in_degree(tasks, graph)
        order = topological_sort(graph, in_deg)
        assert len(order) < 2


# ===================================================================
# 5. Wave Computation Tests
# ===================================================================


class TestComputeExecutionWaves:
    """Verify compute_execution_waves groups tasks into correct parallel waves."""

    def test_single_wave_no_deps(self):
        """All independent tasks should land in wave 1."""
        tasks = [_make_node("A"), _make_node("B"), _make_node("C")]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert len(waves) == 1
        assert waves[0].wave_number == 1
        assert set(waves[0].task_ids) == {"A", "B", "C"}

    def test_three_waves_chain(self):
        """A -> B -> C should produce three sequential waves."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        tasks = [a, b, c]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert len(waves) == 3
        assert waves[0].wave_number == 1
        assert waves[0].task_ids == ["A"]
        assert waves[1].wave_number == 2
        assert waves[1].task_ids == ["B"]
        assert waves[2].wave_number == 3
        assert waves[2].task_ids == ["C"]

    def test_parallel_tasks_same_wave(self):
        """B and C (both depend only on A) should be in the same wave."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        tasks = [a, b, c]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert len(waves) == 2
        assert waves[1].wave_number == 2
        assert set(waves[1].task_ids) == {"B", "C"}

    def test_diamond_shape(self):
        """Diamond: Wave 1=[A], Wave 2=[B,C], Wave 3=[D]."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["B", "C"])
        tasks = [a, b, c, d]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert len(waves) == 3
        assert waves[0].task_ids == ["A"]
        assert set(waves[1].task_ids) == {"B", "C"}
        assert waves[2].task_ids == ["D"]

    def test_wave_numbers_start_at_one(self):
        """Wave numbers must be 1-indexed, not 0-indexed."""
        tasks = [_make_node("SOLO")]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert waves[0].wave_number == 1

    def test_empty_tasks(self):
        """No tasks should produce no waves."""
        waves = compute_execution_waves([], {})
        assert waves == []

    def test_complex_fan_out_fan_in(self):
        """Fan-out then fan-in: A -> [B,C,D] -> E."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["A"])
        e = _make_node("E", depends_on=["B", "C", "D"])
        tasks = [a, b, c, d, e]
        graph = build_dependency_graph(tasks)
        waves = compute_execution_waves(tasks, graph)
        assert len(waves) == 3
        assert waves[0].task_ids == ["A"]
        assert set(waves[1].task_ids) == {"B", "C", "D"}
        assert waves[2].task_ids == ["E"]


# ===================================================================
# 6. File Conflict Tests
# ===================================================================


class TestDetectFileConflicts:
    """Verify detect_file_conflicts finds overlapping file accesses in a wave."""

    def test_no_conflicts(self):
        """Tasks touching different files should produce no conflicts."""
        a = _make_node("A", files=["src/a.py"])
        b = _make_node("B", files=["src/b.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert conflicts == []

    def test_two_tasks_same_file(self):
        """Two tasks touching the same file should produce one conflict."""
        a = _make_node("A", files=["src/shared.py"])
        b = _make_node("B", files=["src/shared.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert len(conflicts) == 1
        assert conflicts[0].file_path == "src/shared.py"
        assert set(conflicts[0].task_ids) == {"A", "B"}
        assert conflicts[0].conflict_type == "write-write"

    def test_multiple_conflicts(self):
        """Two shared files should produce two separate conflicts."""
        a = _make_node("A", files=["src/x.py", "src/y.py"])
        b = _make_node("B", files=["src/x.py", "src/y.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert len(conflicts) == 2
        conflict_files = {c.file_path for c in conflicts}
        assert conflict_files == {"src/x.py", "src/y.py"}

    def test_different_files_no_conflict(self):
        """Completely disjoint file sets should produce no conflicts."""
        a = _make_node("A", files=["src/a.py", "src/b.py"])
        b = _make_node("B", files=["src/c.py", "src/d.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert conflicts == []

    def test_three_tasks_one_file(self):
        """Three tasks touching the same file produce one conflict with all three IDs."""
        a = _make_node("A", files=["src/shared.py"])
        b = _make_node("B", files=["src/shared.py"])
        c = _make_node("C", files=["src/shared.py"])
        task_map = {"A": a, "B": b, "C": c}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B", "C"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert len(conflicts) == 1
        assert set(conflicts[0].task_ids) == {"A", "B", "C"}

    def test_normalizes_paths(self):
        r"""Backslash paths like src\\foo.py should be normalized before comparison."""
        a = _make_node("A", files=["src\\foo.py"])
        b = _make_node("B", files=["src/foo.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert len(conflicts) == 1

    def test_conflict_resolution_field(self):
        """Each conflict should have resolution set to artificial-dependency."""
        a = _make_node("A", files=["shared.py"])
        b = _make_node("B", files=["shared.py"])
        task_map = {"A": a, "B": b}
        wave = ExecutionWave(wave_number=1, task_ids=["A", "B"])
        conflicts = detect_file_conflicts(wave, task_map)
        assert conflicts[0].resolution == "artificial-dependency"


# ===================================================================
# 7. Conflict Resolution Tests
# ===================================================================


class TestResolveConflicts:
    """Verify resolve_conflicts_via_dependency injects correct edges."""

    def test_adds_dependency(self):
        """A conflict between A and B should make B depend on A (sorted order)."""
        a = _make_node("A", files=["shared.py"])
        b = _make_node("B", files=["shared.py"])
        conflict = FileConflict(
            file_path="shared.py",
            task_ids=["A", "B"],
            conflict_type="write-write",
            resolution="artificial-dependency",
        )
        tasks = resolve_conflicts_via_dependency([a, b], [conflict])
        b_node = next(t for t in tasks if t.id == "B")
        assert "A" in b_node.depends_on

    def test_multiple_conflicts_chained(self):
        """Three tasks on one file: B depends on A, C depends on B."""
        a = _make_node("A", files=["shared.py"])
        b = _make_node("B", files=["shared.py"])
        c = _make_node("C", files=["shared.py"])
        conflict = FileConflict(
            file_path="shared.py",
            task_ids=["A", "B", "C"],
            conflict_type="write-write",
            resolution="artificial-dependency",
        )
        tasks = resolve_conflicts_via_dependency([a, b, c], [conflict])
        b_node = next(t for t in tasks if t.id == "B")
        c_node = next(t for t in tasks if t.id == "C")
        assert "A" in b_node.depends_on
        assert "B" in c_node.depends_on

    def test_no_conflicts_unchanged(self):
        """When no conflicts exist, tasks remain unchanged."""
        a = _make_node("A")
        b = _make_node("B")
        original_a_deps = list(a.depends_on)
        original_b_deps = list(b.depends_on)
        tasks = resolve_conflicts_via_dependency([a, b], [])
        assert tasks[0].depends_on == original_a_deps
        assert tasks[1].depends_on == original_b_deps

    def test_no_duplicate_dependency_injection(self):
        """If the dependency already exists, it should not be added again."""
        a = _make_node("A", files=["shared.py"])
        b = _make_node("B", files=["shared.py"], depends_on=["A"])
        conflict = FileConflict(
            file_path="shared.py",
            task_ids=["A", "B"],
            conflict_type="write-write",
            resolution="artificial-dependency",
        )
        tasks = resolve_conflicts_via_dependency([a, b], [conflict])
        b_node = next(t for t in tasks if t.id == "B")
        assert b_node.depends_on.count("A") == 1


# ===================================================================
# 8. Critical Path Tests
# ===================================================================


class TestComputeCriticalPath:
    """Verify compute_critical_path identifies correct bottleneck tasks."""

    def test_linear_chain_all_critical(self):
        """In a linear chain A->B->C, every task is on the critical path."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        tasks = [a, b, c]
        graph = build_dependency_graph(tasks)
        cp = compute_critical_path(tasks, graph)
        assert cp.path == ["A", "B", "C"]
        assert cp.total_length == 3
        assert cp.bottleneck_tasks == ["A", "B", "C"]

    def test_diamond_critical_path(self):
        """Diamond A->[B,C]->D: critical path should include A and D (and one of B/C)."""
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["A"])
        d = _make_node("D", depends_on=["B", "C"])
        tasks = [a, b, c, d]
        graph = build_dependency_graph(tasks)
        cp = compute_critical_path(tasks, graph)
        # With uniform weights, both B and C are critical (same length paths)
        assert "A" in cp.path
        assert "D" in cp.path
        assert cp.total_length >= 3

    def test_single_task(self):
        """A single task is itself the entire critical path."""
        solo = _make_node("SOLO")
        tasks = [solo]
        graph = build_dependency_graph(tasks)
        cp = compute_critical_path(tasks, graph)
        assert cp.path == ["SOLO"]
        assert cp.total_length == 1

    def test_parallel_paths(self):
        """Two independent parallel paths: the longer one is critical."""
        # Path 1: A -> B -> C (length 3)
        a = _make_node("A")
        b = _make_node("B", depends_on=["A"])
        c = _make_node("C", depends_on=["B"])
        # Path 2: X -> Y (length 2)
        x = _make_node("X")
        y = _make_node("Y", depends_on=["X"])
        tasks = [a, b, c, x, y]
        graph = build_dependency_graph(tasks)
        cp = compute_critical_path(tasks, graph)
        # The longer chain (A->B->C = 3) should be on the critical path
        assert "A" in cp.path
        assert "B" in cp.path
        assert "C" in cp.path

    def test_empty_tasks(self):
        """No tasks should return an empty critical path."""
        cp = compute_critical_path([], {})
        assert cp.path == []
        assert cp.total_length == 0
        assert cp.bottleneck_tasks == []


# ===================================================================
# 9. Path Normalization Tests
# ===================================================================


class TestNormalizeFilePath:
    """Verify normalize_file_path handles cross-platform path formats."""

    def test_backslash_to_forward(self):
        r"""src\utils\foo.ts should become src/utils/foo.ts."""
        assert normalize_file_path("src\\utils\\foo.ts") == "src/utils/foo.ts"

    def test_strip_dot_prefix(self):
        """./src/foo.py should become src/foo.py."""
        assert normalize_file_path("./src/foo.py") == "src/foo.py"

    def test_already_normalized(self):
        """A POSIX path without dot-prefix should be returned unchanged."""
        assert normalize_file_path("src/foo.py") == "src/foo.py"

    def test_mixed_separators(self):
        r"""./src\utils/bar.js should become src/utils/bar.js."""
        assert normalize_file_path("./src\\utils/bar.js") == "src/utils/bar.js"

    def test_deep_backslash_path(self):
        r"""a\b\c\d\e.py should become a/b/c/d/e.py."""
        assert normalize_file_path("a\\b\\c\\d\\e.py") == "a/b/c/d/e.py"

    def test_empty_string(self):
        """Empty string should remain empty."""
        assert normalize_file_path("") == ""

    def test_single_filename(self):
        """A bare filename with no directory should pass through."""
        assert normalize_file_path("readme.md") == "readme.md"

    def test_dot_prefix_only(self):
        """Path that is only ./ should become empty string."""
        assert normalize_file_path("./") == ""


# ===================================================================
# 10. Task Context Tests
# ===================================================================


class TestBuildTaskContext:
    """Verify build_task_context assembles the correct context package."""

    def test_basic_context(self):
        """Context should include task_id, files, and empty contracts/notes."""
        task = _make_node("TASK-010", files=["src/app.py", "src/utils.py"])
        ctx = build_task_context(task)
        assert isinstance(ctx, TaskContext)
        assert ctx.task_id == "TASK-010"
        assert len(ctx.files) == 2
        assert ctx.files[0].path == "src/app.py"
        assert ctx.files[1].path == "src/utils.py"
        assert ctx.contracts == []
        assert ctx.integration_notes == ""

    def test_context_with_contracts(self):
        """When contracts are passed, they appear in the context."""
        task = _make_node("TASK-020", files=["src/api.py"])
        contracts = ["UserService.create(name: str) -> User", "AuthService.login() -> Token"]
        ctx = build_task_context(task, contracts=contracts)
        assert ctx.contracts == contracts
        assert len(ctx.contracts) == 2

    def test_context_with_integration_declares(self):
        """integration_declares should be rendered as integration_notes."""
        task = _make_node("TASK-030", files=["src/server.py"])
        task.integration_declares = {"exports": ["setupRoutes", "createApp"]}
        ctx = build_task_context(task)
        assert "exports" in ctx.integration_notes
        assert "setupRoutes" in ctx.integration_notes

    def test_file_context_default_role(self):
        """Without a codebase_map, file role should default to modify."""
        task = _make_node("TASK-040", files=["src/new_file.py"])
        ctx = build_task_context(task)
        assert ctx.files[0].role == "modify"

    def test_file_context_sections_empty_without_map(self):
        """Without a codebase_map, relevant_sections should be empty."""
        task = _make_node("TASK-050", files=["src/foo.py"])
        ctx = build_task_context(task)
        assert ctx.files[0].relevant_sections == []

    def test_normalized_paths_in_context(self):
        r"""File paths in context should be POSIX-normalized."""
        task = _make_node("TASK-060", files=["src\\bar\\baz.py"])
        ctx = build_task_context(task)
        assert ctx.files[0].path == "src/bar/baz.py"

    def test_empty_files(self):
        """A task with no files should produce a context with empty files list."""
        task = _make_node("TASK-070", files=[])
        ctx = build_task_context(task)
        assert ctx.files == []


# ===================================================================
# 11. End-to-End Tests
# ===================================================================


class TestComputeSchedule:
    """Verify the full compute_schedule pipeline from parsed tasks to result."""

    def test_full_pipeline(self):
        """Parse SAMPLE_TASKS_MD, schedule, and verify waves and conflict-free result."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        result = compute_schedule(tasks)

        assert isinstance(result, ScheduleResult)
        assert result.total_waves >= 1

        # Verify all tasks appear across all waves
        all_scheduled = []
        for wave in result.waves:
            all_scheduled.extend(wave.task_ids)
        assert set(all_scheduled) == {"TASK-001", "TASK-002", "TASK-003", "TASK-004"}

        # Wave numbers are 1-indexed and sequential
        for i, wave in enumerate(result.waves):
            assert wave.wave_number == i + 1

        # TASK-001 has no dependencies, must be in wave 1
        assert "TASK-001" in result.waves[0].task_ids

        # TASK-004 depends on TASK-002 and TASK-003, must be in a later wave
        t4_wave = None
        for wave in result.waves:
            if "TASK-004" in wave.task_ids:
                t4_wave = wave.wave_number
        assert t4_wave is not None
        assert t4_wave > 1

        # Critical path should exist
        assert result.critical_path.total_length >= 1
        assert len(result.critical_path.path) >= 1

    def test_empty_tasks(self):
        """Empty task list should return an empty schedule without error."""
        result = compute_schedule([])
        assert result.total_waves == 0
        assert result.waves == []
        assert result.conflict_summary == {}
        assert result.integration_tasks == []
        assert result.critical_path.path == []

    def test_single_task_schedule(self):
        """A single task with no dependencies should produce one wave."""
        tasks = [_make_node("TASK-001", files=["src/app.py"])]
        result = compute_schedule(tasks)
        assert result.total_waves == 1
        assert result.waves[0].task_ids == ["TASK-001"]

    def test_cycle_raises_value_error(self):
        """A cyclic dependency should raise ValueError from compute_schedule."""
        a = _make_node("TASK-001", depends_on=["TASK-002"])
        b = _make_node("TASK-002", depends_on=["TASK-001"])
        with pytest.raises(ValueError, match="Dependency graph validation failed"):
            compute_schedule([a, b])

    def test_missing_dep_raises_value_error(self):
        """Referencing a non-existent task should raise ValueError."""
        a = _make_node("TASK-001", depends_on=["TASK-GHOST"])
        with pytest.raises(ValueError, match="Dependency graph validation failed"):
            compute_schedule([a])

    def test_file_conflict_resolution_in_pipeline(self):
        """Tasks sharing a file should be separated into different waves after resolution."""
        a = _make_node("TASK-001", files=["src/shared.py"])
        b = _make_node("TASK-002", files=["src/shared.py"])
        result = compute_schedule([a, b])
        # After conflict resolution, they should be in separate waves
        assert result.total_waves == 2
        assert result.conflict_summary.get("write-write", 0) >= 1

    def test_diamond_schedule_from_parsed_md(self):
        """The SAMPLE_TASKS_MD has a diamond shape. Verify wave structure."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        result = compute_schedule(tasks)
        # TASK-002 and TASK-003 both depend on TASK-001
        # TASK-004 depends on both TASK-002 and TASK-003
        # Expected: Wave 1=[TASK-001], Wave 2=[TASK-002, TASK-003], Wave 3=[TASK-004]
        assert result.total_waves == 3
        assert result.waves[0].task_ids == ["TASK-001"]
        assert set(result.waves[1].task_ids) == {"TASK-002", "TASK-003"}
        assert result.waves[2].task_ids == ["TASK-004"]

    def test_integration_tasks_empty_by_default(self):
        """Tasks without integration_declares should not appear in integration_tasks."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        result = compute_schedule(tasks)
        assert result.integration_tasks == []

    def test_schedule_preserves_all_task_ids(self):
        """Every task ID from input should appear exactly once across all waves."""
        tasks = [
            _make_node("T1"),
            _make_node("T2", depends_on=["T1"]),
            _make_node("T3", depends_on=["T1"]),
            _make_node("T4", depends_on=["T2", "T3"]),
            _make_node("T5", depends_on=["T4"]),
        ]
        result = compute_schedule(tasks)
        all_ids = []
        for wave in result.waves:
            all_ids.extend(wave.task_ids)
        assert sorted(all_ids) == ["T1", "T2", "T3", "T4", "T5"]
        # No duplicates
        assert len(all_ids) == len(set(all_ids))


# ===================================================================
# 12. compute_file_context Tests (Finding #22)
# ===================================================================


class TestComputeFileContext:
    """Tests for Finding #22: compute_file_context.

    Verifies that compute_file_context correctly builds a list of
    FileContext objects from a TaskNode, handling the presence or
    absence of a codebase_map.
    """

    def test_basic_context_returns_list(self):
        """compute_file_context returns a list of FileContext objects."""
        from agent_team.scheduler import FileContext, compute_file_context

        task = _make_node("TASK-100", files=["src/main.py", "src/utils.py"])
        result = compute_file_context(task)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(fc, FileContext) for fc in result)

    def test_file_paths_are_normalized(self):
        """File paths in the returned context should be POSIX-normalized."""
        from agent_team.scheduler import compute_file_context

        task = _make_node("TASK-101", files=["src\\models\\user.py"])
        result = compute_file_context(task)
        assert result[0].path == "src/models/user.py"

    def test_empty_files_returns_empty_list(self):
        """A task with no files should produce an empty context list."""
        from agent_team.scheduler import compute_file_context

        task = _make_node("TASK-102", files=[])
        result = compute_file_context(task)
        assert result == []

    def test_default_role_is_modify(self):
        """Without a codebase_map, every file role should default to 'modify'."""
        from agent_team.scheduler import compute_file_context

        task = _make_node("TASK-103", files=["src/app.py", "src/db.py"])
        result = compute_file_context(task, codebase_map=None)
        for fc in result:
            assert fc.role == "modify"

    def test_default_sections_are_empty(self):
        """Without a codebase_map, relevant_sections should be empty."""
        from agent_team.scheduler import compute_file_context

        task = _make_node("TASK-104", files=["src/server.py"])
        result = compute_file_context(task, codebase_map=None)
        assert result[0].relevant_sections == []

    def test_preserves_file_order(self):
        """Files should appear in the same order as the task's file list."""
        from agent_team.scheduler import compute_file_context

        files = ["src/c.py", "src/a.py", "src/b.py"]
        task = _make_node("TASK-105", files=files)
        result = compute_file_context(task)
        result_paths = [fc.path for fc in result]
        assert result_paths == ["src/c.py", "src/a.py", "src/b.py"]

    def test_single_file(self):
        """A task with a single file produces a single-element list."""
        from agent_team.scheduler import compute_file_context

        task = _make_node("TASK-106", files=["readme.md"])
        result = compute_file_context(task)
        assert len(result) == 1
        assert result[0].path == "readme.md"


# ===================================================================
# 13. render_task_context_md Tests (Finding #22)
# ===================================================================


class TestRenderTaskContextMd:
    """Tests for Finding #22: render_task_context_md.

    Verifies that render_task_context_md converts a TaskContext into
    a well-formed markdown string suitable for agent prompt injection.
    """

    def test_basic_render_contains_task_id(self):
        """Rendered markdown should include the task ID as a heading."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-200", files=["src/main.py"])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert isinstance(md, str)
        assert "TASK-200" in md

    def test_render_includes_file_paths(self):
        """Each file path should appear in the rendered output."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-201", files=["src/a.py", "src/b.py"])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert "src/a.py" in md
        assert "src/b.py" in md

    def test_render_includes_role_badges(self):
        """File roles should appear as uppercase badges like [MODIFY]."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-202", files=["src/app.py"])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert "[MODIFY]" in md

    def test_render_with_contracts(self):
        """Contracts should appear under an Interface Contracts section."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-203", files=["src/api.py"])
        contracts = ["UserService.create(name: str) -> User"]
        ctx = build_task_context(task, contracts=contracts)
        md = render_task_context_md(ctx)
        assert "Interface Contracts" in md
        assert "UserService.create" in md

    def test_render_with_multiple_files(self):
        """Multiple files should all appear, each with its own role badge."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-204", files=["src/a.py", "src/b.py", "src/c.py"])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert "TASK-204" in md
        assert md.count("[MODIFY]") == 3

    def test_render_empty_files(self):
        """A context with no files should not crash and should still produce a string."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-205", files=[])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert isinstance(md, str)
        assert "TASK-205" in md
        # Should not contain a Files section
        assert "### Files" not in md

    def test_render_with_integration_notes(self):
        """Integration declares should be rendered under Integration Notes."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-206", files=["src/server.py"])
        task.integration_declares = {"exports": ["setupRoutes", "createApp"]}
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert "Integration Notes" in md
        assert "setupRoutes" in md
        assert "createApp" in md

    def test_render_no_contracts_omits_section(self):
        """When no contracts are provided, the Interface Contracts section should be absent."""
        from agent_team.scheduler import render_task_context_md

        task = _make_node("TASK-207", files=["src/util.py"])
        ctx = build_task_context(task)
        md = render_task_context_md(ctx)
        assert "Interface Contracts" not in md


# ===================================================================
# update_tasks_md_statuses()
# ===================================================================


class TestUpdateTasksMdStatuses:
    """Tests for update_tasks_md_statuses()."""

    def test_marks_all_complete_when_no_ids(self):
        from agent_team.scheduler import update_tasks_md_statuses

        md = (
            "### TASK-001: Types\n- Status: PENDING\n"
            "### TASK-002: Store\n- Status: PENDING\n"
        )
        result = update_tasks_md_statuses(md)
        assert "PENDING" not in result
        assert result.count("COMPLETE") == 2

    def test_marks_specific_ids_only(self):
        from agent_team.scheduler import update_tasks_md_statuses

        md = (
            "### TASK-001: Types\n- Status: PENDING\n"
            "### TASK-002: Store\n- Status: PENDING\n"
        )
        result = update_tasks_md_statuses(md, completed_ids={"TASK-001"})
        assert result.count("COMPLETE") == 1
        assert "PENDING" in result

    def test_empty_set_returns_unchanged(self):
        from agent_team.scheduler import update_tasks_md_statuses

        md = "### TASK-001: Types\n- Status: PENDING\n"
        result = update_tasks_md_statuses(md, completed_ids=set())
        assert result == md

    def test_preserves_non_task_content(self):
        from agent_team.scheduler import update_tasks_md_statuses

        md = "# Tasks\nPreamble text\n### TASK-001: Types\n- Status: PENDING\n"
        result = update_tasks_md_statuses(md)
        assert "# Tasks" in result
        assert "Preamble text" in result

    def test_already_complete_stays_complete(self):
        from agent_team.scheduler import update_tasks_md_statuses

        md = "### TASK-001: Types\n- Status: COMPLETE\n"
        result = update_tasks_md_statuses(md)
        assert result.count("COMPLETE") == 1


# ===================================================================
# Scheduler Config Wiring Tests (fields 5-8)
# ===================================================================


class TestSchedulerConfigWiring:
    """Verify that SchedulerConfig fields reach scheduling functions."""

    def test_max_parallel_tasks_caps_wave_size(self):
        """5 independent tasks with max_parallel=2 should produce waves of <=2."""
        nodes = [_make_node(f"TASK-{i:03d}") for i in range(1, 6)]
        graph = build_dependency_graph(nodes)
        waves = compute_execution_waves(nodes, graph, max_parallel_tasks=2)
        for wave in waves:
            assert len(wave.task_ids) <= 2

    def test_max_parallel_tasks_none_no_cap(self):
        """All 5 independent tasks in one wave when max_parallel is None."""
        nodes = [_make_node(f"TASK-{i:03d}") for i in range(1, 6)]
        graph = build_dependency_graph(nodes)
        waves = compute_execution_waves(nodes, graph, max_parallel_tasks=None)
        assert len(waves) == 1
        assert len(waves[0].task_ids) == 5

    def test_conflict_strategy_sets_resolution_field(self):
        """conflict_strategy should appear in FileConflict.resolution."""
        nodes = [
            _make_node("TASK-001", files=["shared.py"]),
            _make_node("TASK-002", files=["shared.py"]),
        ]
        graph = build_dependency_graph(nodes)
        waves = compute_execution_waves(nodes, graph)
        conflicts = detect_file_conflicts(
            waves[0], {t.id: t for t in nodes},
            conflict_strategy="integration-agent",
        )
        assert len(conflicts) == 1
        assert conflicts[0].resolution == "integration-agent"

    def test_conflict_strategy_none_defaults_artificial(self):
        """None conflict_strategy should default to 'artificial-dependency'."""
        nodes = [
            _make_node("TASK-001", files=["shared.py"]),
            _make_node("TASK-002", files=["shared.py"]),
        ]
        graph = build_dependency_graph(nodes)
        waves = compute_execution_waves(nodes, graph)
        conflicts = detect_file_conflicts(
            waves[0], {t.id: t for t in nodes},
            conflict_strategy=None,
        )
        assert len(conflicts) == 1
        assert conflicts[0].resolution == "artificial-dependency"

    def test_enable_critical_path_false_skips_computation(self):
        """critical_path disabled should return empty CriticalPathInfo."""
        from agent_team.config import SchedulerConfig

        nodes = [
            _make_node("TASK-001"),
            _make_node("TASK-002", depends_on=["TASK-001"]),
        ]
        cfg = SchedulerConfig(enabled=True, enable_critical_path=False)
        result = compute_schedule(nodes, scheduler_config=cfg)
        assert result.critical_path.path == []
        assert result.critical_path.total_length == 0

    def test_enable_critical_path_true_computes(self):
        """critical_path enabled should produce a non-empty path."""
        from agent_team.config import SchedulerConfig

        nodes = [
            _make_node("TASK-001"),
            _make_node("TASK-002", depends_on=["TASK-001"]),
        ]
        cfg = SchedulerConfig(enabled=True, enable_critical_path=True)
        result = compute_schedule(nodes, scheduler_config=cfg)
        assert len(result.critical_path.path) > 0

    def test_integration_agent_strategy_logs_info(self, caplog):
        """integration-agent strategy should log an info message."""
        import logging
        from agent_team.config import SchedulerConfig

        nodes = [_make_node("TASK-001")]
        cfg = SchedulerConfig(
            enabled=True,
            conflict_strategy="integration-agent",
        )
        with caplog.at_level(logging.INFO, logger="agent_team.scheduler"):
            compute_schedule(nodes, scheduler_config=cfg)
        assert "integration-agent" in caplog.text

    def test_schedule_result_includes_tasks_field(self):
        """Fix 1: ScheduleResult.tasks field is populated with full task list."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        result = compute_schedule(tasks)
        assert hasattr(result, "tasks")
        assert len(result.tasks) == len(tasks)
        result_ids = {t.id for t in result.tasks}
        input_ids = {t.id for t in tasks}
        assert result_ids == input_ids

    def test_integration_tasks_in_schedule_result(self):
        """Fix 1: When conflict_strategy='integration-agent', integration tasks appear
        in both result.integration_tasks and result.tasks."""
        from agent_team.config import SchedulerConfig

        # Two tasks sharing a file to trigger conflict
        nodes = [
            _make_node("TASK-001", files=["shared.py"]),
            _make_node("TASK-002", files=["shared.py"]),
        ]
        cfg = SchedulerConfig(
            enabled=True,
            conflict_strategy="integration-agent",
        )
        result = compute_schedule(nodes, scheduler_config=cfg)
        # Should have created an integration task
        assert len(result.integration_tasks) >= 1
        # Integration task should be in result.tasks
        integration_ids = set(result.integration_tasks)
        result_ids = {t.id for t in result.tasks}
        assert integration_ids.issubset(result_ids)

    def test_compute_schedule_none_config_backwards_compat(self):
        """No config param should work identically to previous behavior."""
        nodes = [
            _make_node("TASK-001"),
            _make_node("TASK-002", depends_on=["TASK-001"]),
        ]
        result = compute_schedule(nodes)
        assert result.total_waves >= 1
        assert len(result.critical_path.path) > 0


# ===================================================================
# 14. TaskNode milestone_id Tests
# ===================================================================


class TestTaskNodeMilestoneId:
    """Tests for the milestone_id field on TaskNode."""

    def test_task_node_milestone_id_default(self):
        """TaskNode milestone_id defaults to None."""
        node = _make_node("TASK-001")
        assert node.milestone_id is None

    def test_task_node_milestone_id_set(self):
        """milestone_id can be set to a string value."""
        node = TaskNode(
            id="TASK-001",
            title="Setup",
            description="Setup project",
            files=[],
            depends_on=[],
            status="PENDING",
            milestone_id="milestone-1",
        )
        assert node.milestone_id == "milestone-1"

    def test_task_node_milestone_id_none_explicit(self):
        """Explicitly passing None leaves milestone_id as None."""
        node = TaskNode(
            id="TASK-002",
            title="Build",
            description="Build project",
            files=[],
            depends_on=[],
            status="PENDING",
            milestone_id=None,
        )
        assert node.milestone_id is None


# ===================================================================
# 15. parse_tasks_md with milestone field
# ===================================================================


SAMPLE_TASKS_MD_WITH_MILESTONES = """# Task Breakdown: Milestone Test
Generated: 2025-01-01
Total Tasks: 3

## Tasks

### TASK-001: Setup project
- Status: PENDING
- Dependencies: none
- Files: src/config.py
- Milestone: milestone-1
- Description: Create the project scaffolding

### TASK-002: Create models
- Status: PENDING
- Dependencies: TASK-001
- Files: src/models.py
- Milestone: milestone-1
- Description: Define data models

### TASK-003: Build API
- Status: PENDING
- Dependencies: TASK-002
- Files: src/api.py
- Milestone: milestone-2
- Description: Build the REST API layer
"""


class TestParseTasksMdWithMilestone:
    """Tests for parsing milestone field from TASKS.md."""

    def test_parse_tasks_md_with_milestone(self):
        """Milestone field is correctly parsed from TASKS.md."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD_WITH_MILESTONES)
        assert len(tasks) == 3
        t1 = next(t for t in tasks if t.id == "TASK-001")
        assert t1.milestone_id == "milestone-1"
        t3 = next(t for t in tasks if t.id == "TASK-003")
        assert t3.milestone_id == "milestone-2"

    def test_parse_tasks_md_without_milestone_field(self):
        """Tasks without a milestone field have milestone_id=None."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD)
        for task in tasks:
            assert task.milestone_id is None

    def test_parse_tasks_md_milestone_all_same(self):
        """All tasks in milestone-1 are correctly grouped."""
        tasks = parse_tasks_md(SAMPLE_TASKS_MD_WITH_MILESTONES)
        m1_tasks = [t for t in tasks if t.milestone_id == "milestone-1"]
        assert len(m1_tasks) == 2
        assert {t.id for t in m1_tasks} == {"TASK-001", "TASK-002"}


# ===================================================================
# 16. filter_tasks_by_milestone
# ===================================================================


class TestFilterTasksByMilestone:
    """Tests for filter_tasks_by_milestone."""

    def test_filter_tasks_by_milestone(self):
        """Filters only tasks belonging to the specified milestone."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        t2 = TaskNode(id="T2", title="T2", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        t3 = TaskNode(id="T3", title="T3", description="", files=[], depends_on=[], status="PENDING", milestone_id="m2")
        t4 = TaskNode(id="T4", title="T4", description="", files=[], depends_on=[], status="PENDING", milestone_id=None)
        result = filter_tasks_by_milestone([t1, t2, t3, t4], "m1")
        assert len(result) == 2
        assert {t.id for t in result} == {"T1", "T2"}

    def test_filter_tasks_by_milestone_empty(self):
        """Filtering by a non-existent milestone returns an empty list."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        result = filter_tasks_by_milestone([t1], "m99")
        assert result == []

    def test_filter_tasks_excludes_none_milestone(self):
        """Tasks with milestone_id=None are excluded."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id=None)
        result = filter_tasks_by_milestone([t1], "m1")
        assert result == []

    def test_filter_tasks_multiple_milestones(self):
        """Only the requested milestone's tasks are returned."""
        tasks = [
            TaskNode(id=f"T{i}", title=f"T{i}", description="", files=[], depends_on=[], status="PENDING", milestone_id=f"m{i % 3}")
            for i in range(9)
        ]
        result = filter_tasks_by_milestone(tasks, "m0")
        assert all(t.milestone_id == "m0" for t in result)
        assert len(result) == 3


# ===================================================================
# 17. compute_milestone_schedule
# ===================================================================


class TestComputeMilestoneSchedule:
    """Tests for compute_milestone_schedule."""

    def test_compute_milestone_schedule_basic(self):
        """Returns only tasks scoped to the given milestone."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        t2 = TaskNode(id="T2", title="T2", description="", files=[], depends_on=["T1"], status="PENDING", milestone_id="m1")
        t3 = TaskNode(id="T3", title="T3", description="", files=[], depends_on=[], status="PENDING", milestone_id="m2")
        result = compute_milestone_schedule([t1, t2, t3], "m1")
        assert len(result) == 2
        assert {t.id for t in result} == {"T1", "T2"}

    def test_compute_milestone_schedule_cross_dep(self):
        """Cross-milestone deps from completed milestones are removed."""
        t1 = TaskNode(id="TASK-001", title="T1", description="", files=[], depends_on=[], status="COMPLETE", milestone_id="m1")
        t2 = TaskNode(
            id="TASK-002", title="T2", description="", files=[],
            depends_on=["m1@TASK-001"],  # cross-milestone dep
            status="PENDING", milestone_id="m2",
        )
        result = compute_milestone_schedule([t1, t2], "m2", completed_milestones={"m1"})
        assert len(result) == 1
        assert result[0].id == "TASK-002"
        # Cross-dep from completed milestone should be removed
        assert "m1@TASK-001" not in result[0].depends_on

    def test_compute_milestone_schedule_cross_dep_unresolved(self):
        """Cross-milestone deps from incomplete milestones are kept."""
        t1 = TaskNode(id="TASK-001", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        t2 = TaskNode(
            id="TASK-002", title="T2", description="", files=[],
            depends_on=["m1@TASK-001"],
            status="PENDING", milestone_id="m2",
        )
        # m1 is NOT complete
        result = compute_milestone_schedule([t1, t2], "m2", completed_milestones=set())
        assert len(result) == 1
        # Unresolved cross-dep should be kept
        assert "m1@TASK-001" in result[0].depends_on

    def test_compute_milestone_schedule_empty_milestone(self):
        """Milestone with no tasks returns empty list."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        result = compute_milestone_schedule([t1], "m99")
        assert result == []

    def test_compute_milestone_schedule_no_cross_deps(self):
        """Tasks with only local deps are returned unchanged."""
        t1 = TaskNode(id="T1", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m1")
        t2 = TaskNode(id="T2", title="T2", description="", files=[], depends_on=["T1"], status="PENDING", milestone_id="m1")
        result = compute_milestone_schedule([t1, t2], "m1")
        assert len(result) == 2
        t2_result = next(t for t in result if t.id == "T2")
        assert t2_result.depends_on == ["T1"]

    def test_compute_milestone_schedule_preserves_intra_deps(self):
        """Intra-milestone dependencies are preserved after cross-dep resolution."""
        t1 = TaskNode(id="TASK-010", title="T1", description="", files=[], depends_on=[], status="PENDING", milestone_id="m2")
        t2 = TaskNode(
            id="TASK-011", title="T2", description="", files=[],
            depends_on=["TASK-010", "m1@TASK-005"],
            status="PENDING", milestone_id="m2",
        )
        result = compute_milestone_schedule([t1, t2], "m2", completed_milestones={"m1"})
        t2_result = next(t for t in result if t.id == "TASK-011")
        assert "TASK-010" in t2_result.depends_on
        assert "m1@TASK-005" not in t2_result.depends_on


# ===================================================================
# 18. format_schedule_for_prompt Tests
# ===================================================================


class TestFormatScheduleForPrompt:
    """Tests for format_schedule_for_prompt()."""

    def test_empty_schedule_returns_empty_string(self):
        """An empty schedule (no waves) should return an empty string."""
        result = ScheduleResult(
            waves=[],
            total_waves=0,
            conflict_summary={},
            integration_tasks=[],
            critical_path=CriticalPathInfo(path=[], total_length=0, bottleneck_tasks=[]),
            tasks=[],
        )
        assert format_schedule_for_prompt(result) == ""

    def test_normal_schedule_includes_waves(self):
        """A schedule with waves should include wave listings."""
        waves = [
            ExecutionWave(wave_number=1, task_ids=["TASK-001"]),
            ExecutionWave(wave_number=2, task_ids=["TASK-002", "TASK-003"]),
            ExecutionWave(wave_number=3, task_ids=["TASK-004"]),
        ]
        cp = CriticalPathInfo(path=["TASK-001", "TASK-002", "TASK-004"], total_length=3, bottleneck_tasks=[])
        result = ScheduleResult(
            waves=waves,
            total_waves=3,
            conflict_summary={},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result)
        assert "Execution waves: 3" in output
        assert "Wave 1:" in output
        assert "TASK-001" in output
        assert "Wave 2:" in output
        assert "TASK-002" in output
        assert "TASK-003" in output
        assert "Wave 3:" in output
        assert "TASK-004" in output

    def test_includes_critical_path(self):
        """Output should include critical path info when available."""
        waves = [ExecutionWave(wave_number=1, task_ids=["A", "B"])]
        cp = CriticalPathInfo(path=["A", "B"], total_length=2, bottleneck_tasks=["A", "B"])
        result = ScheduleResult(
            waves=waves,
            total_waves=1,
            conflict_summary={},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result)
        assert "Critical path: A -> B" in output

    def test_includes_conflict_summary(self):
        """Output should include conflict info when present."""
        waves = [ExecutionWave(wave_number=1, task_ids=["A"])]
        cp = CriticalPathInfo(path=["A"], total_length=1, bottleneck_tasks=[])
        result = ScheduleResult(
            waves=waves,
            total_waves=1,
            conflict_summary={"write-write": 2},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result)
        assert "Conflicts resolved:" in output
        assert "write-write: 2" in output

    def test_includes_follow_instruction(self):
        """Output should include the instruction to follow wave order."""
        waves = [ExecutionWave(wave_number=1, task_ids=["A"])]
        cp = CriticalPathInfo(path=["A"], total_length=1, bottleneck_tasks=[])
        result = ScheduleResult(
            waves=waves,
            total_waves=1,
            conflict_summary={},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result)
        assert "Follow wave order" in output

    def test_max_chars_capping(self):
        """Output should be capped at max_chars characters."""
        # Create a schedule with many waves to generate long output
        waves = [
            ExecutionWave(wave_number=i, task_ids=[f"TASK-{i:03d}-LONG-NAME-TO-FILL-SPACE"])
            for i in range(1, 50)
        ]
        cp = CriticalPathInfo(path=[], total_length=0, bottleneck_tasks=[])
        result = ScheduleResult(
            waves=waves,
            total_waves=49,
            conflict_summary={},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result, max_chars=200)
        assert len(output) <= 200
        assert output.endswith("...")

    def test_short_output_not_truncated(self):
        """Short output should not be truncated or have ellipsis."""
        waves = [ExecutionWave(wave_number=1, task_ids=["A"])]
        cp = CriticalPathInfo(path=["A"], total_length=1, bottleneck_tasks=[])
        result = ScheduleResult(
            waves=waves,
            total_waves=1,
            conflict_summary={},
            integration_tasks=[],
            critical_path=cp,
            tasks=[],
        )
        output = format_schedule_for_prompt(result, max_chars=2000)
        assert not output.endswith("...")
