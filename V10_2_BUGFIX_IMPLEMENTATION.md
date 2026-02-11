# Agent-Team Exhaustive Implementation — v10.2 P0 Bugfix Sweep

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (5 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `superpowers:code-reviewer` | Phase 1 — Read entire codebase, document all integration points, produce ARCHITECTURE_REPORT.md |
| `impl-cli` | `general-purpose` | Phase 2A — All changes to `src/agent_team/cli.py` |
| `impl-prompts` | `general-purpose` | Phase 2B — All changes to `src/agent_team/agents.py` |
| `impl-modules` | `general-purpose` | Phase 2C — All changes to `src/agent_team/milestone_manager.py` and `src/agent_team/scheduler.py` |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest, fix failures, iterate until green |

### Coordination Flow

```
Wave 1 (solo): architect reads entire codebase
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-cli (cli.py)
                  + impl-prompts (agents.py)
                  + impl-modules (milestone_manager.py, scheduler.py)
    |                   |                    |
    All read ARCHITECTURE_REPORT.md first
    |                   |                    |
    +---------+---------+--------------------+
              |
Wave 3 (solo): test-engineer writes ALL tests
              |
Wave 4 (solo): test-engineer runs full suite, fixes failures
              |
Wave 5: You (team lead) collect all results -> final report
```

### Agent Instructions

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **architect runs first and alone.** Its ARCHITECTURE_REPORT.md is the blueprint for all implementation.
- **impl agents run simultaneously.** They work on different files:
  - impl-cli: `src/agent_team/cli.py` ONLY
  - impl-prompts: `src/agent_team/agents.py` ONLY
  - impl-modules: `src/agent_team/milestone_manager.py` and `src/agent_team/scheduler.py` ONLY
- **test-engineer waits for ALL impl agents** before starting.
- **After the final wave completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents

- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-cli: Can create/edit `src/agent_team/cli.py`. Do NOT touch agents.py, milestone_manager.py, scheduler.py.
- impl-prompts: Can create/edit `src/agent_team/agents.py`. Do NOT touch cli.py, milestone_manager.py, scheduler.py.
- impl-modules: Can create/edit `src/agent_team/milestone_manager.py` and `src/agent_team/scheduler.py`. Do NOT touch cli.py, agents.py.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# v10.2 P0 Bugfix Sweep — Eliminating All Run-Time Failures

## Background — Why This Exists

Agent-team v10.0/v10.1 introduced milestone-based orchestration, browser testing, and numerous post-orchestration scans. A full P0 re-run on a real project (TaskFlow Pro — 139 requirements across 5 milestones) revealed **13 bugs**, of which 10 remain unfixed. These bugs fall into 4 failure patterns that cascade from a single root cause (milestone directory path mismatch). The P0 re-run completed but with degraded quality: zero review verification, zero task tracking, zero convergence cycle counting, and zero browser testing context.

### Failure 1: Milestone Directory Path Mismatch (ROOT CAUSE — 4 bug cascade)

The orchestrator creates per-milestone directories at `.agent-team/milestone-N/` but the entire MilestoneManager subsystem expects them at `.agent-team/milestones/milestone-N/`. This means `_list_milestone_ids()` returns `[]`, `check_milestone_health()` finds no per-milestone REQUIREMENTS.md files, `aggregate_milestone_convergence()` produces `health="unknown"`, and `_has_milestone_requirements()` returns False. The TASKS.md existence check at line 1048 also looks in the wrong directory. In the TaskFlow Pro run, ALL 5 milestone health checks returned empty results because the `milestones/` subdirectory never existed, despite the orchestrator creating rich per-milestone directories with REQUIREMENTS.md files at the sibling level.

### Failure 2: Lost PRD Context in Post-Orchestration (3 bugs)

In PRD mode, `args.task` is None (user provides `--prd` not `--task`). All 26 post-orchestration function calls pass `task_text=args.task`, giving every sub-orchestrator zero project context. Browser testing agents can't generate workflows because they don't know what the app does. Fallback UI generation always returns "minimal_modern" because `_infer_design_direction(None)` can't match any keywords. Fix agents get no project context in their prompts. In the TaskFlow Pro run, the fallback UI generation defaulted to minimal_modern even though the PRD described a task management system that should have matched "dashboard" design direction.

### Failure 3: TASKS.md Format Mismatch + GATE 5 Non-Enforcement (3 bugs)

The scheduler's `parse_tasks_md()` expects `### TASK-xxx` header blocks with `Status: PENDING` lines, but the orchestrator writes markdown tables (`| TASK-001 | Description | ... |`). Result: "All 0 tasks marked COMPLETE" is logged for every run. Additionally, GATE 5 promises "the system WILL force a review-only recovery pass" when review_cycles==0, but the enforcement code only triggers inside the `health=="failed"` branch. When health is "healthy" (139/139 checked) with 0 review cycles, the gate warning fires but recovery never triggers. The review fleet deployment is completely bypassed.

### Failure 4: Dead Code + Missing Review Markers (2 bugs)

`run_e2e_quality_scan()` in quality_checks.py is fully implemented (E2E-001 through E2E-007 checks) but never called from cli.py — confirmed by grep showing zero import/call references in the CLI module. Additionally, the `parse_max_review_cycles()` function counts `(review_cycles: N)` inline markers, but the reviewer prompt never instructs reviewers to write these markers. Result: review_cycles is always 0, which cascades into GATE 5 warnings and incorrect convergence reporting.

## What We're Building

**Deliverable 1: `effective_task` Variable** (Phase 2A — cli.py)
A single variable computed early in `main()` that holds enriched task context for PRD, interview, and task modes. Replaces ALL 26 `task_text=args.task` occurrences and all 4 `generate_fallback_ui_requirements(task=args.task, ...)` calls. This eliminates the entire class of "lost PRD context" bugs permanently.

**Deliverable 2: `normalize_milestone_dirs()` Function** (Phase 2C — milestone_manager.py + Phase 2A call sites)
A pure file-system normalizer that detects orphan `milestone-N/` directories at the `.agent-team/` level and copies them into `.agent-team/milestones/milestone-N/`. Called after decomposition, after each milestone execution, and before aggregate_milestone_convergence(). This bridges the path mismatch without requiring orchestrator prompt changes.

**Deliverable 3: TASKS.md Format Injection + Table Fallback Parser** (Phase 2B + Phase 2C)
Explicit `### TASK-xxx` block format example injected into the milestone workflow prompt, plus a table-format fallback branch in `parse_tasks_md()`. Prevention + detection defense-in-depth.

**Deliverable 4: GATE 5 Enforcement** (Phase 2A — cli.py)
A standalone check after the health-based recovery logic that forces `needs_recovery=True` when `review_cycles==0` regardless of apparent health. Fulfills the existing prompt promise.

**Deliverable 5: Review Cycles Marker Injection** (Phase 2B — agents.py)
Explicit instruction in the reviewer prompt to append `(review_cycles: N)` inline markers after verifying each requirement.

**Deliverable 6: E2E Quality Scan Wiring** (Phase 2A — cli.py)
Wire `run_e2e_quality_scan()` into the post-orchestration pipeline after the E2E testing phase.

**Deliverable 7: GATE 5 Promise Truth** (Phase 2B — agents.py)
Update the orchestrator prompt's GATE 5 description to match the actual enforcement behavior.

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

Before implementing ANYTHING, the architect must read the codebase and produce `.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: cli.py — main() Post-Orchestration Flow

- Read `src/agent_team/cli.py` end to end (~5300 lines)
- Document the EXACT location of each of these 26 `task_text=args.task` call sites — record line numbers for each
- Document all 4 `generate_fallback_ui_requirements(task=args.task, ...)` call sites — record line numbers
- Document the EXACT position where `effective_task` should be computed (BEFORE Phase 0.6 fallback UI generation, AFTER args parsing and interview completion)
- Document the post-orchestration pipeline order:
  1. TASKS.md diagnostic (line ~3996)
  2. Artifact verification gate (line ~4032)
  3. Contract health check (line ~4076)
  4. Convergence health check (line ~4130)
  5. GATE 5 warning (line ~4213)
  6. Recovery decision (line ~4239)
  7. Mock data scan (line ~4350)
  8. UI compliance scan (line ~4395)
  9. Integrity scans (line ~4450)
  10. Database scans (line ~4600)
  11. API contract scan (line ~4700)
  12. E2E testing phase (line ~4800)
  13. Browser testing (line ~5035)
- Identify the EXACT line where GATE 5 enforcement check should be inserted (after health-based recovery, before mock data scan)
- Identify the EXACT line where E2E quality scan wiring should be inserted (after E2E testing phase, before browser testing)

### 1B: cli.py — _run_prd_milestones() Milestone Loop

- Read `_run_prd_milestones()` (starts ~line 800, ends ~line 1200)
- Document `milestones_dir = req_dir / "milestones"` at line 872
- Document the EXACT location AFTER decomposition where `normalize_milestone_dirs()` should be called (after line 870, before the execution loop)
- Document the EXACT location AFTER each milestone execution where `normalize_milestone_dirs()` should be called (after line 1045, before health check at line 1056)
- Document `ms_tasks_path = milestones_dir / milestone.id / "TASKS.md"` check at line 1048

### 1C: milestone_manager.py — MilestoneManager Class

- Read `src/agent_team/milestone_manager.py` end to end
- Document `_milestones_dir` property (line ~509): returns `project_root / ".agent-team" / "milestones"`
- Document `_list_milestone_ids()` (line ~524): lists dirs under `_milestones_dir`
- Document `_read_requirements()` (line ~513): reads from `_milestones_dir / milestone_id / "REQUIREMENTS.md"`
- Document `check_milestone_health()` (line ~617): uses `_read_requirements()`
- Document `aggregate_milestone_convergence()` (line ~346): iterates `_list_milestone_ids()`
- Determine where `normalize_milestone_dirs()` should be defined (as a module-level function, not a method)
- Determine what imports are needed (shutil, re)

### 1D: scheduler.py — parse_tasks_md()

- Read `src/agent_team/scheduler.py` — find `parse_tasks_md()` (line ~211)
- Document the block-splitting regex: `re.split(r"(?=^###\s+TASK-)", content, flags=re.MULTILINE)`
- Document the `RE_TASK_ID`, `RE_DEPENDS`, `RE_FILES`, `RE_STATUS`, `RE_PARENT` regex constants
- Document the `TaskNode` dataclass fields
- Identify the EXACT insertion point for table-format fallback (at the start of parse_tasks_md, BEFORE existing block parsing)

### 1E: agents.py — Milestone Workflow Prompt + Reviewer Prompt

- Read `src/agent_team/agents.py` end to end (~2800 lines)
- Find `build_milestone_execution_prompt()` — locate the TASK ASSIGNER section that says "Deploy TASK ASSIGNER to create TASKS.md"
- Document the EXACT text currently used for the TASKS.md instruction
- Find the CODE_REVIEWER_PROMPT constant — document its location and current content structure
- Find the GATE 5 promise text in the orchestrator prompt (around line 178): "If convergence_cycles == 0, the system WILL force a review-only recovery pass"
- Identify where review_cycles marker instruction should be added in the reviewer prompt

### 1F: quality_checks.py — run_e2e_quality_scan()

- Read `src/agent_team/quality_checks.py` — find `run_e2e_quality_scan()` (line ~1331)
- Document its signature: `run_e2e_quality_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]`
- Document what it checks (E2E-001 through E2E-007)
- Verify it's fully implemented and NOT called from cli.py

### 1G: Test Patterns

- Read `tests/` directory — identify the testing conventions:
  - How config is mocked (AgentTeamConfig defaults, _dict_to_config)
  - How cli.py functions are tested (monkeypatch, tmp_path)
  - How prompt constants are tested (string containment assertions)
  - How parser functions are tested (direct calls with sample input)
- Document the test runner command: `python -m pytest tests/ -v --tb=short`
- Document pre-existing known failures (test_mcp_servers.py)

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1G), with exact file paths, line numbers, function names, and integration points. This is the blueprint for Phase 2.

---

## PHASE 2A: CLI Pipeline Fixes (impl-cli)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Fix 1: Create `effective_task` Variable

**In `main()`, BEFORE Phase 0.6 (design extraction), AFTER interview completion and args parsing:**

Add a block that computes `effective_task` once, early, and stores enriched project context:

```python
# ---------------------------------------------------------------
# Compute effective_task: enriched task context for all downstream
# sub-orchestrator calls. In PRD mode, args.task is None but the
# PRD content provides essential project context.
# ---------------------------------------------------------------
effective_task: str = args.task or ""
if args.prd and not args.task:
    try:
        _prd_content = Path(args.prd).read_text(encoding="utf-8")
        _prd_preview = _prd_content[:2000]
        _prd_name = Path(args.prd).name
        effective_task = (
            f"Build the application described in {_prd_name}.\n\n"
            f"PRD Summary:\n{_prd_preview}"
        )
        if len(_prd_content) > 2000:
            effective_task += "\n... (truncated — see full PRD file)"
    except (OSError, UnicodeDecodeError):
        effective_task = f"Build the application described in {Path(args.prd).name}"
elif interview_doc and not effective_task:
    effective_task = (
        f"Implement the requirements from the interview document.\n\n"
        f"Summary:\n{interview_doc[:1000]}"
    )
```

This MUST be placed BEFORE any `generate_fallback_ui_requirements(task=...)` call and BEFORE any `task_text=args.task` usage. Verify the exact insertion point from ARCHITECTURE_REPORT.md section 1A.

**Important**: The PRD file is read exactly ONCE into `_prd_content`, then sliced for the preview. If `--task` is also provided, it takes priority and the PRD is not read at all.

### Fix 2: Replace ALL `task_text=args.task` with `task_text=effective_task`

Using the 26 line numbers from ARCHITECTURE_REPORT.md section 1A, replace every occurrence:

```python
# BEFORE:
task_text=args.task,

# AFTER:
task_text=effective_task,
```

Do this for ALL 26 occurrences. Do NOT miss any. Verify the count matches.

### Fix 3: Replace ALL `generate_fallback_ui_requirements(task=args.task, ...)` with `task=effective_task`

Using the 4 line numbers from ARCHITECTURE_REPORT.md section 1A, replace:

```python
# BEFORE:
ui_requirements_content = generate_fallback_ui_requirements(
    task=args.task, config=config, cwd=cwd,
)

# AFTER:
ui_requirements_content = generate_fallback_ui_requirements(
    task=effective_task, config=config, cwd=cwd,
)
```

Do this for ALL 4 occurrences.

### Fix 4: GATE 5 Enforcement Check

**In `main()`, AFTER the health-based recovery decision block (after `elif convergence_report.health == "degraded":` handling), BEFORE `if needs_recovery:`:**

Add a GATE 5 enforcement override:

```python
# ---------------------------------------------------------------
# GATE 5 ENFORCEMENT: Force review when review_cycles == 0
# regardless of apparent health. The review fleet MUST deploy
# at least once to verify the orchestrator's convergence claims.
# ---------------------------------------------------------------
if (
    not needs_recovery
    and convergence_report is not None
    and convergence_report.review_cycles == 0
    and convergence_report.total_requirements > 0
):
    print_warning(
        "GATE 5 ENFORCEMENT: 0 review cycles detected with "
        f"{convergence_report.total_requirements} requirements. "
        "Deploying mandatory review fleet to verify convergence."
    )
    needs_recovery = True
    recovery_types.append("gate5_enforcement")
```

The exact insertion line is documented in ARCHITECTURE_REPORT.md section 1A. It must be AFTER the `elif convergence_report.health == "degraded":` block and BEFORE the `if needs_recovery:` line that launches recovery.

### Fix 5: Wire run_e2e_quality_scan()

**In `main()`, AFTER the E2E testing phase block, BEFORE the browser testing block:**

```python
# -------------------------------------------------------------------
# Post-orchestration: E2E Quality Scan (static analysis of test code)
# -------------------------------------------------------------------
if config.e2e_testing.enabled:
    try:
        from .quality_checks import run_e2e_quality_scan

        _e2e_scan_scope = scan_scope if 'scan_scope' in dir() else None
        e2e_quality_violations = run_e2e_quality_scan(
            Path(cwd),
            scope=_e2e_scan_scope,
        )
        if e2e_quality_violations:
            print_warning(
                f"E2E quality scan: {len(e2e_quality_violations)} issue(s) found."
            )
            for _v in e2e_quality_violations[:10]:
                print_warning(f"  {_v.code}: {_v.file}:{_v.line} - {_v.message}")
        else:
            print_info("E2E quality scan: 0 violations (clean)")
    except Exception as exc:
        print_warning(f"E2E quality scan failed: {exc}")
```

Verify the exact insertion point from ARCHITECTURE_REPORT.md section 1A.

### Fix 6: Call normalize_milestone_dirs()

**In `_run_prd_milestones()`, TWO call sites:**

**Call site 1: After decomposition, before execution loop** (around line 873):

```python
    mm = MilestoneManager(project_root)
    milestones_dir = req_dir / "milestones"

    # Normalize milestone directories created by decomposition
    # (orchestrator may create .agent-team/milestone-N/ instead of .agent-team/milestones/milestone-N/)
    try:
        from .milestone_manager import normalize_milestone_dirs
        _normalized = normalize_milestone_dirs(project_root, config.convergence.requirements_dir)
        if _normalized > 0:
            print_info(f"Normalized {_normalized} milestone directory path(s)")
    except Exception as exc:
        print_warning(f"Milestone directory normalization failed: {exc}")
```

**Call site 2: After each milestone execution completes, before health check** (around line 1046):

```python
            # Normalize milestone directories after execution
            # (orchestrator may have created files at .agent-team/milestone-N/ instead of milestones/)
            try:
                from .milestone_manager import normalize_milestone_dirs
                normalize_milestone_dirs(project_root, config.convergence.requirements_dir)
            except Exception:
                pass  # Best-effort normalization
```

**Call site 3: In main(), before aggregate_milestone_convergence()** (in the post-orchestration convergence section):

Find where `aggregate_milestone_convergence()` is called in main() and add normalization right before it:

```python
    # Normalize milestone dirs before aggregation
    try:
        from .milestone_manager import normalize_milestone_dirs
        normalize_milestone_dirs(Path(cwd), config.convergence.requirements_dir)
    except Exception:
        pass
```

---

## PHASE 2B: Prompt Fixes (impl-prompts)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Fix 1: TASKS.md Block Format Injection

**Target: `src/agent_team/agents.py`, `build_milestone_execution_prompt()` function**

Find the section that mentions "Deploy TASK ASSIGNER to create TASKS.md" and replace it with an expanded version that includes the EXACT format:

The current text is approximately:
```
4. Deploy TASK ASSIGNER to create TASKS.md in THIS milestone's directory
   Write to: {ms_tasks_path}
```

Replace with:
```
4. Deploy TASK ASSIGNER to create TASKS.md in THIS milestone's directory.
   Write to: {ms_tasks_path}

   CRITICAL: Use EXACTLY this block format for each task (NOT markdown tables):

   ### TASK-001: {Brief title}
   Status: PENDING
   Depends-On: TASK-002, TASK-003
   Files: path/to/file1.ts, path/to/file2.ts
   Requirements: REQ-001, REQ-002

   {One-line description of what this task accomplishes.}

   ### TASK-002: {Brief title}
   Status: PENDING
   Depends-On: —
   Files: path/to/file.ts
   Requirements: REQ-003

   {One-line description.}

   RULES:
   - Each task MUST start with ### TASK-NNN: header (triple hash)
   - Status MUST be "PENDING" for new tasks
   - Depends-On lists prerequisite TASK IDs (use — for none)
   - Files lists the files this task will create or modify
   - Requirements maps to the REQ-xxx items this task fulfills
   - Do NOT use markdown tables. The parser requires this exact block format.
```

Verify the exact insertion point and surrounding context from ARCHITECTURE_REPORT.md section 1E.

### Fix 2: Review Cycles Marker Instruction

**Target: `src/agent_team/agents.py`, CODE_REVIEWER_PROMPT constant**

Find the CODE_REVIEWER_PROMPT and add a section about review cycle markers. Add this text at an appropriate position within the reviewer instructions:

```
## Review Cycle Tracking

After you verify each requirement line in REQUIREMENTS.md, you MUST append a review cycle marker inline:

BEFORE your review:
- [x] REQ-001: Initialize Node.js project with package.json

AFTER your review (first pass):
- [x] REQ-001: Initialize Node.js project with package.json (review_cycles: 1)

If a requirement already has a review_cycles marker from a previous pass, INCREMENT the number:
- [x] REQ-001: Initialize Node.js project with package.json (review_cycles: 2)

RULES:
- The marker format MUST be exactly: (review_cycles: N) — with the parentheses, colon, and space
- Place the marker at the END of the line, after all other content
- Only mark items you have ACTUALLY verified against the codebase
- If you check an item and it's NOT implemented, change [x] to [ ] AND add the marker
- Do NOT skip this step. The system uses these markers to verify review fleet deployment.
```

### Fix 3: GATE 5 Promise Truth

**Target: `src/agent_team/agents.py`, orchestrator prompt**

Find the text (approximately line 178):
`"If convergence_cycles == 0, the system WILL force a review-only recovery pass"`

Update it to match actual behavior:
```
If review_cycles == 0 after orchestration completes, the system WILL force a mandatory review-only recovery pass, regardless of apparent convergence health. This ensures the review fleet always deploys at least once to verify the orchestrator's claims.
```

---

## PHASE 2C: Module Fixes (impl-modules)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### New Function: `normalize_milestone_dirs()` in milestone_manager.py

**Add as a module-level function (NOT a method on MilestoneManager):**

```python
import re as _re_normalize
import shutil


def normalize_milestone_dirs(
    project_root: Path,
    requirements_dir: str = ".agent-team",
) -> int:
    """Normalize milestone directory structure.

    The orchestrator may create ``milestone-N/`` directories directly under
    the requirements directory instead of under the ``milestones/`` sub-directory.
    This function detects such "orphan" directories and copies their contents
    into the canonical ``milestones/milestone-N/`` location.

    Parameters
    ----------
    project_root:
        Root directory of the project.
    requirements_dir:
        Name of the requirements directory (default ``.agent-team``).

    Returns
    -------
    int
        Number of directories normalized (copied to canonical location).
    """
    req_dir = project_root / requirements_dir
    if not req_dir.is_dir():
        return 0

    milestones_dir = req_dir / "milestones"
    normalized = 0

    _milestone_pattern = _re_normalize.compile(r"^milestone-\w+$")

    try:
        entries = list(req_dir.iterdir())
    except OSError:
        return 0

    for entry in entries:
        if not entry.is_dir():
            continue
        if not _milestone_pattern.match(entry.name):
            continue
        # Skip the "milestones" directory itself
        if entry.name == "milestones":
            continue

        target = milestones_dir / entry.name
        if not target.exists():
            milestones_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copytree(str(entry), str(target))
                normalized += 1
            except (OSError, shutil.Error):
                pass  # Best-effort copy
        else:
            # Merge: copy files that don't already exist in target
            try:
                for src_file in entry.rglob("*"):
                    if src_file.is_file():
                        rel = src_file.relative_to(entry)
                        dest_file = target / rel
                        if not dest_file.exists():
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(src_file), str(dest_file))
                            normalized += 1
            except (OSError, shutil.Error):
                pass  # Best-effort merge

    return normalized
```

Place this function AFTER the existing imports section and BEFORE the `MilestoneManager` class definition. Make sure `shutil` is imported at the top of the file.

### Modification: Table-Format Fallback in scheduler.py `parse_tasks_md()`

**Modify `parse_tasks_md()` to try block format first, then fall back to table format:**

The current implementation starts with:
```python
def parse_tasks_md(content: str) -> list[TaskNode]:
    # Split at task headers, keeping the header in each block
    blocks = re.split(r"(?=^###\s+TASK-)", content, flags=re.MULTILINE)
    ...
```

Restructure to:

```python
def parse_tasks_md(content: str) -> list[TaskNode]:
    """Parse a TASKS.md document into a list of :class:`TaskNode` objects.

    The parser uses a block-splitting state machine: it splits the document
    at ``### TASK-`` headers via :func:`re.split`, then extracts structured
    fields from each block using compiled regexes.

    Falls back to table-format parsing if no block-format tasks are found.
    """
    # Try block format first (### TASK-xxx headers)
    blocks = re.split(r"(?=^###\s+TASK-)", content, flags=re.MULTILINE)

    # Filter out preamble blocks (no TASK- header)
    task_blocks = [b for b in blocks if RE_TASK_ID.search(b)]

    if task_blocks:
        return _parse_block_format_tasks(task_blocks)

    # Fallback: try table-format parsing
    return _parse_table_format_tasks(content)
```

Then extract the existing block-parsing logic into `_parse_block_format_tasks()`:

```python
def _parse_block_format_tasks(task_blocks: list[str]) -> list[TaskNode]:
    """Parse tasks from ### TASK-xxx block format."""
    tasks: list[TaskNode] = []

    for block in task_blocks:
        block = block.strip()
        if not block:
            continue

        # (... existing parsing logic from parse_tasks_md, unchanged ...)
        # Extract task ID, title, dependencies, files, status, parent, milestone
        # Build TaskNode and append to tasks

    return tasks
```

And add a new function for table parsing:

```python
# Regex for table row: | TASK-NNN | description | depends | requirements |
_RE_TABLE_TASK_ROW = re.compile(
    r"\|\s*(TASK-\d+)\s*\|"   # Task ID
    r"\s*(.+?)\s*\|"           # Description
    r"\s*(.*?)\s*\|"           # Depends On
    r"\s*(.*?)\s*\|",          # Requirements (or any 4th column)
)


def _parse_table_format_tasks(content: str) -> list[TaskNode]:
    """Parse tasks from markdown table format (fallback).

    Handles tables with columns: Task ID | Description | Depends On | Requirements
    """
    tasks: list[TaskNode] = []
    seen_ids: set[str] = set()

    for match in _RE_TABLE_TASK_ROW.finditer(content):
        task_id = match.group(1).strip()
        if task_id in seen_ids:
            continue  # Skip duplicate rows (e.g., header separator)
        seen_ids.add(task_id)

        title = match.group(2).strip()
        depends_raw = match.group(3).strip()
        reqs_raw = match.group(4).strip() if match.lastindex >= 4 else ""

        # Parse dependencies
        depends_on: list[str] = []
        if depends_raw and depends_raw not in ("—", "-", "None", "none", "N/A"):
            depends_on = [
                d.strip() for d in re.split(r"[,;]", depends_raw)
                if d.strip().startswith("TASK-")
            ]

        # Parse requirements mapping
        requirements: list[str] = []
        if reqs_raw:
            requirements = [
                r.strip() for r in re.split(r"[,;]", reqs_raw)
                if r.strip().startswith("REQ-")
            ]

        tasks.append(TaskNode(
            id=task_id,
            title=title,
            description=title,  # Use title as description for table format
            status="PENDING",
            depends_on=depends_on,
            files=[],  # Tables typically don't include file lists
            milestone_id=None,
        ))

    return tasks
```

**CRITICAL**: The existing block-parsing logic must be moved INTO `_parse_block_format_tasks()` WITHOUT any changes to its behavior. This is a pure refactor + addition, not a modification of existing behavior.

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2A, 2B, and 2C are complete, write tests covering:

### effective_task Tests (`tests/test_v10_2_bugfixes.py`)

**PRD mode tests:**
- args.prd set, args.task None → effective_task contains PRD preview
- args.prd set, args.task also set → effective_task == args.task (explicit task takes priority)
- args.prd file unreadable (OSError) → effective_task falls back gracefully
- args.prd file very large (>2000 chars) → preview truncated with "... (truncated)" suffix
- args.prd file exactly 2000 chars → no truncation marker

**Interview mode tests:**
- interview_doc set, no args.task, no args.prd → effective_task contains interview summary
- interview_doc very long → truncated to 1000 chars

**Task mode tests:**
- args.task set → effective_task == args.task
- No PRD, no task, no interview → effective_task == ""

**Propagation tests (mock-based):**
- Verify effective_task is passed (not args.task) to at least 3 representative sub-orchestrator calls
- Verify generate_fallback_ui_requirements receives effective_task

### Milestone Normalizer Tests (`tests/test_v10_2_bugfixes.py`)

**Basic normalization:**
- milestone-1/ at .agent-team/ level → copied to .agent-team/milestones/milestone-1/
- Multiple orphan dirs (milestone-1/, milestone-2/, milestone-3/) → all normalized, returns count=3
- milestone-1/ already exists at canonical location → no duplicate, returns 0
- No orphan dirs → returns 0
- req_dir doesn't exist → returns 0

**Merge behavior:**
- Both paths exist, orphan has new file → file merged into canonical
- Both paths exist, file already at canonical → NOT overwritten (original preserved)
- Nested subdirectories in orphan → preserved during copy

**Filtering:**
- "prd-chunks/" dir at .agent-team/ → NOT moved (doesn't match milestone-\w+ pattern)
- "milestones/" dir itself → NOT moved
- Regular files at .agent-team/ → ignored

**Integration:**
- After normalization, MilestoneManager._list_milestone_ids() returns milestone IDs

### TASKS.md Parser Tests (`tests/test_v10_2_bugfixes.py`)

**Block format (existing behavior preserved):**
- Standard block format → parsed correctly (smoke test)
- Block with all fields → TaskNode has correct values

**Table format (new fallback):**
- Standard 4-column table → parsed correctly
- Table with "—" depends → empty depends_on list
- Table with "TASK-001, TASK-002" depends → correct depends_on list
- Table with REQ-001..004 requirements → parsed (if field exposed)
- Empty content → returns []
- Content with only headers (no data rows) → returns []
- Duplicate TASK IDs in table → deduplicated
- Mixed content (block + table) → block format takes priority

**Edge cases:**
- Table with extra columns → still parses first 4
- Table with missing columns → graceful handling
- Table with separator row (|---|---|) → not parsed as task

### GATE 5 Enforcement Tests (`tests/test_v10_2_bugfixes.py`)

**Enforcement logic:**
- health="healthy", review_cycles=0, total=50 → needs_recovery=True (GATE 5 fires)
- health="healthy", review_cycles=1, total=50 → needs_recovery=False
- health="healthy", review_cycles=0, total=0 → needs_recovery=False (no requirements)
- health="failed", review_cycles=0, total=50 → needs_recovery=True (existing path, NOT double-triggered)
- health="degraded", review_cycles=0, total=50 → check if degraded recovery already set

**Recovery type:**
- When GATE 5 fires → "gate5_enforcement" in recovery_types
- When GATE 5 doesn't fire → "gate5_enforcement" NOT in recovery_types

### Review Cycles Marker Tests (`tests/test_v10_2_bugfixes.py`)

**Prompt injection:**
- CODE_REVIEWER_PROMPT contains "review_cycles:"
- CODE_REVIEWER_PROMPT contains "(review_cycles: N)" or "(review_cycles:"
- CODE_REVIEWER_PROMPT contains instruction about incrementing existing markers

### E2E Quality Scan Wiring Tests (`tests/test_v10_2_bugfixes.py`)

**Wiring:**
- run_e2e_quality_scan is imported and called when e2e_testing.enabled=True (mock test)
- run_e2e_quality_scan NOT called when e2e_testing.enabled=False
- Crash isolation: scan exception doesn't propagate (caught in try/except)

### Prompt Injection Tests (`tests/test_v10_2_bugfixes.py`)

**TASKS.md format:**
- build_milestone_execution_prompt output contains "### TASK-" format example
- build_milestone_execution_prompt output contains "Status: PENDING"
- build_milestone_execution_prompt output contains "Do NOT use markdown tables"

**GATE 5 truth:**
- Orchestrator prompt contains updated GATE 5 description
- Orchestrator prompt does NOT contain stale/false GATE 5 promise

---

## PHASE 4: WIRING VERIFICATION

### 4A: Execution Position
- `effective_task` computed BEFORE Phase 0.6 (design extraction) in main()
- `normalize_milestone_dirs()` called AFTER decomposition in _run_prd_milestones()
- `normalize_milestone_dirs()` called AFTER each milestone execution in _run_prd_milestones()
- `normalize_milestone_dirs()` called BEFORE aggregate_milestone_convergence() in main()
- GATE 5 enforcement check placed AFTER health-based recovery decision, BEFORE `if needs_recovery:`
- E2E quality scan placed AFTER E2E testing phase, BEFORE browser testing block

### 4B: Config Gating
- E2E quality scan gated on `config.e2e_testing.enabled` (no new config field needed)
- `normalize_milestone_dirs()` always runs (no config gate — it's a correctness fix)
- GATE 5 enforcement always runs (no config gate — it's a correctness fix)
- `effective_task` always computed (no config gate)

### 4C: Crash Isolation
- `normalize_milestone_dirs()` wrapped in try/except at all 3 call sites
- E2E quality scan wrapped in try/except
- GATE 5 enforcement: no crash risk (pure conditional logic)
- `effective_task` PRD reading wrapped in try/except with fallback

### 4D: Backward Compatibility
- `effective_task` when no PRD → equals `args.task or ""` (identical to current behavior)
- `normalize_milestone_dirs()` when no orphan dirs → returns 0, no side effects
- Table fallback parser when content is block format → block parser runs (existing behavior)
- GATE 5 enforcement when review_cycles > 0 → no change (existing behavior)
- Review cycles markers: existing REQUIREMENTS.md files without markers → review_cycles=0 (same as before)

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL existing tests must pass (except 2 pre-existing known failures in test_mcp_servers.py)
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# v10.2 P0 Bugfix Sweep — Implementation Report

## Implementation Summary
- Modified: cli.py (effective_task + GATE 5 + E2E scan wiring + normalizer calls)
- Modified: agents.py (TASKS.md format + review_cycles markers + GATE 5 truth)
- Modified: milestone_manager.py (normalize_milestone_dirs function)
- Modified: scheduler.py (table-format fallback parser)
- New tests: tests/test_v10_2_bugfixes.py

## Bug Coverage
| Bug ID | Description | Fixed By | Method |
|--------|-------------|----------|--------|
| BUG-4 | Convergence cycles always 0 | Deliverable 2 + 5 | Milestone dir normalizer + review_cycles markers |
| BUG-5 | Milestone dir path mismatch | Deliverable 2 | normalize_milestone_dirs() bridges both paths |
| BUG-6 | Per-milestone TASKS.md not found | Deliverable 2 | Normalizer copies files to canonical path |
| BUG-7 | run_e2e_quality_scan dead code | Deliverable 6 | Wired into CLI after E2E phase |
| BUG-8 | Browser testing gets None task | Deliverable 1 | effective_task variable |
| BUG-9 | Fallback UI gets None task | Deliverable 1 | effective_task variable |
| BUG-10 | TASKS.md table vs block format | Deliverable 3 | Format injection + table fallback parser |
| BUG-11 | GATE 5 non-functional | Deliverable 4 | Standalone enforcement check |
| BUG-12 | All 26 task_text lose PRD context | Deliverable 1 | effective_task replaces args.task everywhere |
| BUG-13 | Reviewers never write cycle markers | Deliverable 5 | Explicit instruction in reviewer prompt |

## Test Results
- New tests written: {X}
- All passing: {X}/{X}
- Regressions: 0

## Wiring Verification
- Execution position: VERIFIED / ISSUES
- Config gating: VERIFIED / ISSUES
- Crash isolation: VERIFIED / ISSUES
- Backward compatibility: VERIFIED / ISSUES

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone implements anything. The ARCHITECTURE_REPORT.md is the single source of truth for integration points, patterns, and insertion locations.

2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase. Consistency over creativity.

3. **READ BEFORE YOU WRITE** — Read every file before modifying it. Understand the context around your insertion point. Never modify a file you haven't read in the current session.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong.

5. **NO SHORTCUTS** — All 7 deliverables must be fully implemented. A half-implemented bugfix suite is worse than no bugfix suite.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted since this prompt was written.

7. **CRASH ISOLATION** — Every new integration point must be wrapped in its own try/except. New feature failures must NEVER block the main execution flow.

8. **BACKWARD COMPATIBLE** — When no PRD is provided, effective_task must equal args.task (or ""). When no orphan dirs exist, normalizer must be a no-op. Existing block-format TASKS.md must still parse identically.

9. **BEST-EFFORT EXTRACTION** — The table-format fallback parser won't capture all fields (e.g., no Files column in tables). That's OK — the fallback provides TASK IDs, titles, and dependencies, which is vastly better than 0 parsed tasks.

10. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added and why in the final report.

11. **RUN TESTS AFTER EACH PHASE** — Don't wait until the end to discover failures.

12. **cli.py IS 5300+ LINES** — Use targeted reads (offset + limit), not full-file reads. Search for exact function names and line markers.

13. **THE NORMALIZER IS PURE FILE I/O** — No LLM calls, no async, no config loading. It's a simple shutil operation. Keep it simple.
