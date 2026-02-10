# Agent-Team Exhaustive Implementation — Mode Upgrade Propagation (v6.0)

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition (5 agents)

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `superpowers:code-reviewer` | Phase 1 — Read entire codebase, document integration patterns, produce ARCHITECTURE_REPORT.md |
| `impl-config` | `general-purpose` | Phase 2A — Modify `src/agent_team/config.py`: extend `apply_depth_quality_gating()`, add `user_overrides` tracking to `_dict_to_config()`, add `ScanScope` config field, add `PostOrchestrationScanConfig`, backward-compat alias |
| `impl-scans` | `general-purpose` | Phase 2B — Modify `src/agent_team/quality_checks.py`: add `ScanScope` dataclass, `compute_changed_files()`, add `scope` parameter to 7 scan functions |
| `impl-wiring` | `general-purpose` | Phase 2C — Modify `src/agent_team/cli.py`: wire `compute_changed_files()` in post-orchestration, pass `scope` to scans, add PRD reconciliation quality gate, add E2E depth-aware auto-enablement |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest, fix failures, iterate until green |

### Coordination Flow

```
Wave 1 (solo): architect reads config.py, quality_checks.py, cli.py
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-config (config.py)
                  + impl-scans (quality_checks.py)
                  + impl-wiring (cli.py)
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
  - impl-config: `src/agent_team/config.py` ONLY
  - impl-scans: `src/agent_team/quality_checks.py` ONLY
  - impl-wiring: `src/agent_team/cli.py` ONLY
- **test-engineer waits for ALL impl agents** before starting.
- **After the final wave completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents

- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-config: Can create/edit `src/agent_team/config.py`. Do NOT touch quality_checks.py or cli.py.
- impl-scans: Can create/edit `src/agent_team/quality_checks.py`. Do NOT touch config.py or cli.py.
- impl-wiring: Can create/edit `src/agent_team/cli.py`. Do NOT touch config.py or quality_checks.py.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# Mode Upgrade Propagation — Depth-Intelligent Post-Orchestration

## Background — Why This Exists

The agent-team accumulated 5 major upgrade cycles (v2.0–v5.0) with 20 upgrades including mock data
scanning, UI compliance enforcement, E2E testing, integrity scans, tracking documents, and database
integrity checks. Investigation revealed that **19 of 20 upgrades already work in all non-PRD modes**
(only U-12 Milestone Handoff is structurally PRD-only). The post-orchestration pipeline is IDENTICAL
across all 4 depth levels — a 1-line bugfix triggers the exact same 12+ scans as an exhaustive build.

### Failure 1: Quick-Mode Scan Waste

A user says `"Quick fix the login button"`. Depth detection resolves to "quick" mode. The orchestrator
runs with minimal agents (1 coder, 1-2 reviewers) — fast and efficient. But then post-orchestration
hits: mock data scan, UI compliance scan, deployment integrity scan, asset scan, PRD reconciliation
(an entire LLM sub-orchestrator session!), 3 database scans, and full verification. Each scan walks
the ENTIRE project tree. On a 50,000-line codebase, this adds 30-60 seconds of scanning plus $0.50-2.00
for the PRD reconciliation LLM call — all for a 3-line CSS fix. The `apply_depth_quality_gating()`
function at `config.py:451-459` only disables 2 quality prompt sections for quick mode; it doesn't
touch any post-orchestration scans.

### Failure 2: E2E Testing Hidden Behind Opt-In

E2E testing is the most valuable verification step (catches actual runtime bugs), but
`config.e2e_testing.enabled` defaults to `False` at `config.py:315`. A user running
`"Thoroughly refactor the API layer"` gets thorough-depth agents but NO E2E testing unless they
manually add `e2e_testing.enabled: true` to their config.yaml. Users who want thorough work expect
comprehensive verification — hiding E2E behind opt-in defeats the purpose of depth selection.

### Failure 3: Full-Project Scans on Scoped Changes

When a user adds a single feature in standard mode, ALL 8 scan functions walk the entire project tree
because they only accept `project_root: Path`. On a mature codebase with pre-existing issues, scans
find 20-50 violations unrelated to the user's change. This creates noise, wastes time on irrelevant
fixes, and undermines trust in the scan system.

### Failure 4: Config Semantic Confusion

Mock data scan and UI compliance scan are gated by `config.milestone.mock_data_scan` and
`config.milestone.ui_compliance_scan` (fields on `MilestoneConfig` at `config.py:288-289`), but they
run in NON-milestone mode via the `not _use_milestones` gate at `cli.py:3791` and `cli.py:3823`. Users
see "milestone" in the config key and assume it only affects PRD mode — it doesn't.

### Failure 5: PRD Reconciliation Without PRD

PRD reconciliation at `cli.py:3912` runs for ALL modes including non-PRD quick fixes. It launches an
LLM sub-orchestrator to compare REQUIREMENTS.md claims against code. For a quick bugfix, REQUIREMENTS.md
is a thin interview summary — reconciliation is pure waste ($0.50-2.00 per run).

## What We're Building

**Deliverable 1: Extended Depth Gating** (Wave 1 — config.py)
Extend `apply_depth_quality_gating()` to disable expensive post-orchestration scans for quick mode,
disable PRD reconciliation for quick+standard, auto-adjust review recovery retries per depth, and
auto-enable E2E for thorough/exhaustive. Add `user_overrides` tracking to `_dict_to_config()` so
explicit user config values survive depth gating. Add `PostOrchestrationScanConfig` dataclass to
move mock/UI scan config off `MilestoneConfig` with backward-compat alias.

**Deliverable 2: Scoped Scanning** (Wave 2 — quality_checks.py)
Add a `ScanScope` dataclass and `compute_changed_files()` helper that uses `git diff` to determine
what changed. Add an optional `scope: ScanScope | None = None` parameter to 7 scan functions. When
scope is None, scans behave identically to today (full project). When provided, scans filter their
file lists to the scoped set. Fully backward-compatible.

**Deliverable 3: Post-Orchestration Wiring** (Wave 2 — cli.py)
Wire `compute_changed_files()` into the post-orchestration pipeline. Compute scope once based on
depth, then pass it to all scan calls. Add PRD reconciliation REQUIREMENTS.md quality gate for
thorough mode. Wire E2E auto-enablement. Update all scan call sites to pass scope.

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

Before implementing ANYTHING, the architect must read the codebase and produce `.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: Depth Gating Infrastructure (config.py)

- Read `src/agent_team/config.py` end to end (~1040 lines)
- Document `apply_depth_quality_gating()` at line 451:
  - Current signature: `(depth: str, config: AgentTeamConfig) -> None`
  - Current body: only handles `depth == "quick"` → sets `production_defaults=False`, `craft_review=False`
  - Called at `cli.py:3407` (main orchestration) and `cli.py:388` (sub-orchestrator runs)
  - WHY: This is where ALL new depth gates will be added
- Document `_dict_to_config()` at line 719:
  - Pattern: checks `if "section_name" in data:`, then constructs config with `.get()` defaults
  - Currently returns `AgentTeamConfig` with NO tracking of which keys came from user YAML
  - WHY: We need to add `user_overrides: set[str]` tracking here
- Document `load_config()` at line 1024:
  - Returns `AgentTeamConfig` only — needs to also return `user_overrides` set
  - WHY: `apply_depth_quality_gating()` needs to know which fields user explicitly set
- Document these config dataclasses with EXACT field names, types, defaults:
  - `MilestoneConfig` (line 272): especially `mock_data_scan: bool = True` (line 288), `ui_compliance_scan: bool = True` (line 289), `review_recovery_retries: int = 1` (line 287)
  - `IntegrityScanConfig` (line 325): `deployment_scan: bool = True` (334), `asset_scan: bool = True` (335), `prd_reconciliation: bool = True` (336)
  - `DatabaseScanConfig` (line 357): `dual_orm_scan: bool = True` (366), `default_value_scan: bool = True` (367), `relationship_scan: bool = True` (368)
  - `E2ETestingConfig` (line 307): `enabled: bool = False` (315), `max_fix_retries: int = 5` (318)
  - `QualityConfig` (line 209): `production_defaults: bool = True` (211), `craft_review: bool = True` (212)
  - `AgentTeamConfig` (line 372): all sub-config field names and types

### 1B: Scan Function Signatures (quality_checks.py)

- Read `src/agent_team/quality_checks.py` (~2400 lines)
- Document EVERY scan function signature with EXACT line numbers:
  - `run_mock_data_scan(project_root: Path)` at line 1199 — uses `_iter_source_files()` at line 1209
  - `run_ui_compliance_scan(project_root: Path)` at line 1232 — uses `_iter_source_files()` at line 1242
  - `run_e2e_quality_scan(project_root: Path)` at line 1265 — uses `_iter_source_files()` at line 1275
  - `run_deployment_scan(project_root: Path)` at line 1507 — uses `_parse_docker_compose()` (self-gating)
  - `run_asset_scan(project_root: Path)` at line 1657 — uses `os.walk()` at line 1665
  - `run_dual_orm_scan(project_root: Path)` at line 1880 — uses `os.walk()` at line 1892
  - `run_default_value_scan(project_root: Path)` at line 2003 — uses `_iter_source_files()` then `_find_entity_files()` at line 2012-2013
  - `run_relationship_scan(project_root: Path)` at line 2277 — uses `_iter_source_files()` then `_find_entity_files()` at line 2286-2287
- Document `_iter_source_files(project_root: Path) -> list[Path]` at line 1117 — the main file walker
- Document `_find_entity_files(project_root, source_files) -> list[Path]` at line 1842
- Document `Violation` dataclass at line 36: fields `check`, `message`, `file_path`, `line`, `severity`
- Document `_MAX_VIOLATIONS = 100` (find the exact line)
- Document `_should_skip_dir()` and `_should_scan_file()` helpers
- WHY: Every scan function needs the same `scope` parameter pattern

### 1C: Post-Orchestration Pipeline (cli.py)

- Read `src/agent_team/cli.py` lines 3786-4065 (the complete post-orchestration scan section)
- Document EVERY scan call site with its exact gate condition:
  - Mock data scan: `not _use_milestones and config.milestone.mock_data_scan` at line 3791, calls `run_mock_data_scan(Path(cwd))` at line 3794
  - UI compliance scan: `not _use_milestones and config.milestone.ui_compliance_scan` at line 3823, calls `run_ui_compliance_scan(Path(cwd))` at line 3826
  - Deployment scan: `config.integrity_scans.deployment_scan` at line 3854, calls `run_deployment_scan(Path(cwd))` at line 3857
  - Asset scan: `config.integrity_scans.asset_scan` at line 3883, calls `run_asset_scan(Path(cwd))` at line 3886
  - PRD reconciliation: `config.integrity_scans.prd_reconciliation` at line 3912, calls `_run_prd_reconciliation()` at line 3914
  - Dual ORM scan: `config.database_scans.dual_orm_scan` at line 3943, calls `run_dual_orm_scan(Path(cwd))` at line 3947
  - Default value scan: `config.database_scans.default_value_scan` at line 3978, calls `run_default_value_scan(Path(cwd))` at line 3982
  - Relationship scan: `config.database_scans.relationship_scan` at line 4013, calls `run_relationship_scan(Path(cwd))` at line 4017
  - E2E testing: `config.e2e_testing.enabled` at line 4050
- Document `apply_depth_quality_gating(depth, config)` call at line 3407
- Document where `depth` variable is available (set earlier in main(), available throughout post-orchestration)
- Document the fix function signatures:
  - `_run_mock_data_fix(cwd, config, mock_violations, task_text, constraints, intervention, depth)` at line 1387
  - `_run_ui_compliance_fix(cwd, config, ui_violations, task_text, constraints, intervention, depth)` at line 1465
  - `_run_integrity_fix(cwd, config, violations, scan_type, task_text, constraints, intervention, depth)` at line 1856
- WHY: Every scan call needs scope parameter added; some need gate condition changes

### 1D: Import Locations and Test Conventions

- Document all `from .quality_checks import ...` lines in cli.py (they are lazy imports inside try blocks)
- Document existing test file patterns in `tests/` directory — how test files are structured, which fixtures exist
- Document the pre-existing test failures (test_mcp_servers.py) so test-engineer knows to ignore them
- WHY: impl-wiring needs to add new imports; test-engineer needs to follow existing conventions

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1D), with exact file paths, line numbers, function names, and integration points.

---

## PHASE 2A: DEPTH GATING & CONFIG EVOLUTION (impl-config)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Modification 1: Add `PostOrchestrationScanConfig` dataclass

**In `src/agent_team/config.py`, AFTER the `MilestoneConfig` class (after line 289):**

```python
@dataclass
class PostOrchestrationScanConfig:
    """Configuration for post-orchestration quality scans.

    These scans run after the main orchestration loop in ALL modes.
    They were previously on MilestoneConfig but are mode-agnostic.
    """

    mock_data_scan: bool = True       # Scan for mock data in service files
    ui_compliance_scan: bool = True   # Scan for UI compliance violations
```

### Modification 2: Add `PostOrchestrationScanConfig` to `AgentTeamConfig`

**In `src/agent_team/config.py`, in the `AgentTeamConfig` dataclass (line 372), add after `database_scans`:**

```python
    post_orchestration_scans: PostOrchestrationScanConfig = field(default_factory=PostOrchestrationScanConfig)
```

### Modification 3: Add `scan_scope_mode` to `DepthConfig`

**In `src/agent_team/config.py`, in the `DepthConfig` dataclass (line 28), add:**

```python
    scan_scope_mode: str = "auto"  # "auto" (depth-based), "full" (always full), "changed" (always changed-only)
```

### Modification 4: Modify `_dict_to_config()` — add `user_overrides` tracking + new sections

**CRITICAL CHANGE**: `_dict_to_config()` currently returns `AgentTeamConfig`. Change it to return `tuple[AgentTeamConfig, set[str]]` where the set tracks which config paths the user explicitly set.

**At line 719, change the function signature and add tracking:**

```python
def _dict_to_config(data: dict[str, Any]) -> tuple[AgentTeamConfig, set[str]]:
    """Convert a raw dict (from YAML) into an AgentTeamConfig.

    Returns (config, user_overrides) where user_overrides is a set of
    dotted key paths that were explicitly present in the YAML (e.g.,
    'milestone.mock_data_scan', 'e2e_testing.enabled').
    """
    cfg = AgentTeamConfig()
    user_overrides: set[str] = set()
```

**For each config section that has depth-gatable fields, track which keys are present.** Example pattern — in the `"milestone"` section (line 891), add tracking lines:

```python
    if "milestone" in data and isinstance(data["milestone"], dict):
        ms = data["milestone"]
        # Track user-explicit overrides for depth gating
        for key in ("mock_data_scan", "ui_compliance_scan", "review_recovery_retries"):
            if key in ms:
                user_overrides.add(f"milestone.{key}")
        # ... rest of existing MilestoneConfig construction unchanged ...
```

Apply the same pattern for:
- `"integrity_scans"` section: track `"deployment_scan"`, `"asset_scan"`, `"prd_reconciliation"`
- `"database_scans"` section: track `"dual_orm_scan"`, `"default_value_scan"`, `"relationship_scan"`
- `"e2e_testing"` section: track `"enabled"`, `"max_fix_retries"`
- `"quality"` section: track `"production_defaults"`, `"craft_review"`

**Add the new `post_orchestration_scans` section loader (after the `database_scans` section, ~line 994):**

```python
    if "post_orchestration_scans" in data and isinstance(data["post_orchestration_scans"], dict):
        pos = data["post_orchestration_scans"]
        for key in ("mock_data_scan", "ui_compliance_scan"):
            if key in pos:
                user_overrides.add(f"post_orchestration_scans.{key}")
        cfg.post_orchestration_scans = PostOrchestrationScanConfig(
            mock_data_scan=pos.get("mock_data_scan", cfg.post_orchestration_scans.mock_data_scan),
            ui_compliance_scan=pos.get("ui_compliance_scan", cfg.post_orchestration_scans.ui_compliance_scan),
        )
    # Backward-compat: if user has milestone.mock_data_scan but no post_orchestration_scans section,
    # copy the milestone values to the new config location
    elif "milestone" in data and isinstance(data["milestone"], dict):
        ms = data["milestone"]
        if "mock_data_scan" in ms:
            cfg.post_orchestration_scans.mock_data_scan = ms["mock_data_scan"]
        if "ui_compliance_scan" in ms:
            cfg.post_orchestration_scans.ui_compliance_scan = ms["ui_compliance_scan"]
```

**Add depth.scan_scope_mode loading in the `"depth"` section (line 742):**

```python
    if "depth" in data:
        d = data["depth"]
        cfg.depth = DepthConfig(
            default=d.get("default", cfg.depth.default),
            auto_detect=d.get("auto_detect", cfg.depth.auto_detect),
            keyword_map=d.get("keyword_map", cfg.depth.keyword_map),
            scan_scope_mode=d.get("scan_scope_mode", cfg.depth.scan_scope_mode),
        )
```

**Change the return at line 1021:**

```python
    return cfg, user_overrides
```

### Modification 5: Update `load_config()` to return `user_overrides`

**At line 1024, change signature and return type:**

```python
def load_config(
    config_path: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> tuple[AgentTeamConfig, set[str]]:
```

**Find where `_dict_to_config(raw)` is called inside `load_config()` and update to unpack the tuple.** The return should be `return cfg, user_overrides` (or `return AgentTeamConfig(), set()` for the default path).

### Modification 6: Extend `apply_depth_quality_gating()`

**Replace the entire function at line 451 with:**

```python
def apply_depth_quality_gating(
    depth: str,
    config: AgentTeamConfig,
    user_overrides: set[str] | None = None,
) -> None:
    """Apply depth-based gating to config fields.

    QUICK depth disables expensive post-orchestration scans to keep runs fast.
    STANDARD disables PRD reconciliation (low value without rich PRD).
    THOROUGH/EXHAUSTIVE auto-enable E2E testing.

    Fields explicitly set by the user in config.yaml are NEVER overridden.
    The ``user_overrides`` set tracks which dotted key paths were present
    in the user's YAML file.
    """
    uo = user_overrides or set()

    def _gate(key: str, setter: callable) -> None:
        """Apply gate only if user didn't explicitly set the key."""
        if key not in uo:
            setter()

    if depth == "quick":
        # Quality prompt sections (existing behavior)
        config.quality.production_defaults = False
        config.quality.craft_review = False

        # Post-orchestration scans: disable all for quick mode
        _gate("post_orchestration_scans.mock_data_scan",
              lambda: setattr(config.post_orchestration_scans, "mock_data_scan", False))
        _gate("milestone.mock_data_scan",
              lambda: setattr(config.milestone, "mock_data_scan", False))
        _gate("post_orchestration_scans.ui_compliance_scan",
              lambda: setattr(config.post_orchestration_scans, "ui_compliance_scan", False))
        _gate("milestone.ui_compliance_scan",
              lambda: setattr(config.milestone, "ui_compliance_scan", False))

        # Integrity scans: disable all for quick mode
        _gate("integrity_scans.deployment_scan",
              lambda: setattr(config.integrity_scans, "deployment_scan", False))
        _gate("integrity_scans.asset_scan",
              lambda: setattr(config.integrity_scans, "asset_scan", False))
        _gate("integrity_scans.prd_reconciliation",
              lambda: setattr(config.integrity_scans, "prd_reconciliation", False))

        # Database scans: disable all for quick mode
        _gate("database_scans.dual_orm_scan",
              lambda: setattr(config.database_scans, "dual_orm_scan", False))
        _gate("database_scans.default_value_scan",
              lambda: setattr(config.database_scans, "default_value_scan", False))
        _gate("database_scans.relationship_scan",
              lambda: setattr(config.database_scans, "relationship_scan", False))

        # Review recovery: 0 retries for quick mode
        _gate("milestone.review_recovery_retries",
              lambda: setattr(config.milestone, "review_recovery_retries", 0))

    elif depth == "standard":
        # PRD reconciliation is low-value without rich requirements
        _gate("integrity_scans.prd_reconciliation",
              lambda: setattr(config.integrity_scans, "prd_reconciliation", False))

    elif depth in ("thorough", "exhaustive"):
        # Auto-enable E2E testing for thorough/exhaustive
        _gate("e2e_testing.enabled",
              lambda: setattr(config.e2e_testing, "enabled", True))

        # More review recovery retries for thorough/exhaustive
        if depth == "thorough":
            _gate("milestone.review_recovery_retries",
                  lambda: setattr(config.milestone, "review_recovery_retries", 2))
        else:  # exhaustive
            _gate("milestone.review_recovery_retries",
                  lambda: setattr(config.milestone, "review_recovery_retries", 3))
```

### Modification 7: Fix ALL callers of `load_config()` and `apply_depth_quality_gating()`

Search for every call to `load_config()` in cli.py and update to unpack `(config, user_overrides)`. Pass `user_overrides` to every call to `apply_depth_quality_gating()`.

Key call sites:
- `cli.py:3407`: `apply_depth_quality_gating(depth, config)` → `apply_depth_quality_gating(depth, config, user_overrides)`
- `cli.py:388`: `apply_depth_quality_gating(depth_override or "standard", config)` → add `user_overrides` parameter
- Every `load_config()` call: unpack to `config, user_overrides = load_config(...)`

**NOTE to impl-config:** You ONLY modify config.py. The cli.py caller updates are impl-wiring's job. But you MUST ensure the function signatures are compatible. Document the new signatures clearly in the ARCHITECTURE_REPORT.md.

### Validation Rules

- `scan_scope_mode` must be one of: `"auto"`, `"full"`, `"changed"` — add validation in `_dict_to_config()`
- `PostOrchestrationScanConfig` fields are all `bool`, no validation needed beyond type
- Backward-compat: `milestone.mock_data_scan: true` in YAML still works (via the elif branch)

---

## PHASE 2B: SCOPED SCANNING (impl-scans)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### New Code: `ScanScope` dataclass and `compute_changed_files()`

**Add at the TOP of `src/agent_team/quality_checks.py`, after the existing imports and before the `Violation` class (before line 36):**

```python
import subprocess


@dataclass
class ScanScope:
    """Controls which files a scan examines.

    When passed to a scan function, limits scanning to the specified files
    instead of walking the entire project tree.  When ``None`` is passed
    (the default), scans behave identically to the original full-project mode.

    Attributes:
        mode: "full" (scan everything), "changed_only" (only changed files),
              or "changed_and_imports" (changed files + their importers).
        changed_files: Absolute paths of files changed since last commit.
    """

    mode: str = "full"  # "full" | "changed_only" | "changed_and_imports"
    changed_files: list[Path] = field(default_factory=list)


def compute_changed_files(project_root: Path) -> list[Path]:
    """Compute files changed since last commit + untracked new files.

    Uses ``git diff --name-only HEAD`` for modified files and
    ``git ls-files --others --exclude-standard`` for new untracked files.

    Returns absolute paths. Returns an empty list if:
    - Not a git repository
    - git is not available
    - Any subprocess error occurs

    An empty list signals the caller to fall back to full-project scanning.
    """
    try:
        diff_output = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=project_root,
            text=True,
            timeout=10,
            stderr=subprocess.DEVNULL,
        ).strip()
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=project_root,
            text=True,
            timeout=10,
            stderr=subprocess.DEVNULL,
        ).strip()
        files: list[Path] = []
        for line in (diff_output + "\n" + untracked).splitlines():
            line = line.strip()
            if line:
                files.append((project_root / line).resolve())
        return files
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []  # Non-git project or git not available -> full scan fallback
```

**NOTE:** The `dataclass` import already exists at the top of quality_checks.py (used by `Violation`). Verify this during architecture discovery. The `subprocess` import is NEW and must be added.

### Modification to 7 scan functions: Add `scope` parameter

**Pattern for each function:** Add `scope: ScanScope | None = None` as the second parameter. Add a scope-filtering block right after the file collection step. Leave everything else unchanged.

#### 1. `run_mock_data_scan` (line 1199)

Change signature:
```python
def run_mock_data_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

After line 1209 (`source_files = _iter_source_files(project_root)`), add:
```python
    if scope and scope.changed_files:
        scope_set = set(scope.changed_files)
        source_files = [f for f in source_files if f.resolve() in scope_set]
```

#### 2. `run_ui_compliance_scan` (line 1232)

Change signature:
```python
def run_ui_compliance_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

After line 1242 (`source_files = _iter_source_files(project_root)`), add the same scope filter pattern.

#### 3. `run_e2e_quality_scan` (line 1265)

Change signature:
```python
def run_e2e_quality_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

After line 1275 (`source_files = _iter_source_files(project_root)`), add the same scope filter pattern.

#### 4. `run_asset_scan` (line 1657)

Change signature:
```python
def run_asset_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

This function uses `os.walk()` directly at line 1665. Add scope filtering differently — after the `for dirpath, dirnames, filenames in os.walk(project_root):` loop body, add an early-continue check:

```python
            file_path = Path(dirpath) / filename
            # Scope filtering: skip files not in changed set
            if scope and scope.changed_files:
                if file_path.resolve() not in set(scope.changed_files):
                    continue
```

Place this AFTER the `file_path = Path(dirpath) / filename` line (line 1670) and BEFORE the suffix check.

**NOTE:** Build the `scope_set` ONCE before the loop for efficiency, not inside the loop:
```python
    scope_set = set(f.resolve() for f in scope.changed_files) if scope and scope.changed_files else None
    for dirpath, dirnames, filenames in os.walk(project_root):
        ...
        file_path = Path(dirpath) / filename
        if scope_set and file_path.resolve() not in scope_set:
            continue
```

#### 5. `run_dual_orm_scan` (line 1880)

Change signature:
```python
def run_dual_orm_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

This function walks files with `os.walk()` at line 1892. Apply scope filtering to the file collection loop. Build a `scope_set` before the loop and filter `all_files` after collection:

```python
    # After all_files is populated (after the os.walk loop):
    if scope and scope.changed_files:
        scope_set = set(f.resolve() for f in scope.changed_files)
        all_files = [f for f in all_files if f.resolve() in scope_set]
```

#### 6. `run_default_value_scan` (line 2003)

Change signature:
```python
def run_default_value_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

After line 2013 (`entity_files = _find_entity_files(project_root, source_files)`), add:
```python
    if scope and scope.changed_files:
        scope_set = set(f.resolve() for f in scope.changed_files)
        entity_files = [f for f in entity_files if f.resolve() in scope_set]
```

#### 7. `run_relationship_scan` (line 2277)

Change signature:
```python
def run_relationship_scan(project_root: Path, scope: ScanScope | None = None) -> list[Violation]:
```

After line 2287 (`entity_files = _find_entity_files(project_root, source_files)`), add the same scope filter pattern.

### Export Changes

Ensure `ScanScope` and `compute_changed_files` are importable from `quality_checks`. If there's an `__all__` list, add them. Otherwise they're automatically importable.

---

## PHASE 2C: CLI WIRING (impl-wiring)

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Wiring 1: Update `load_config()` callers

**Search for ALL calls to `load_config()` in cli.py.** Each must unpack the new tuple return:

Before: `config = load_config(...)`
After: `config, user_overrides = load_config(...)`

Store `user_overrides` in a variable accessible throughout main().

### Wiring 2: Update `apply_depth_quality_gating()` callers

**At line 3407:**
```python
# Before:
apply_depth_quality_gating(depth, config)

# After:
apply_depth_quality_gating(depth, config, user_overrides)
```

**At line 388 (sub-orchestrator):**
```python
# Before:
apply_depth_quality_gating(depth_override or "standard", config)

# After:
apply_depth_quality_gating(depth_override or "standard", config, user_overrides)
```

**NOTE:** `user_overrides` may need to be passed through function parameters if it's not in scope at line 388. Check the architecture report for the exact scope chain.

### Wiring 3: Compute `ScanScope` once in post-orchestration

**Add BEFORE the mock data scan section (before line 3786), inside the post-orchestration block:**

```python
    # -------------------------------------------------------------------
    # Compute scan scope based on depth for post-orchestration scans
    # -------------------------------------------------------------------
    scan_scope = None
    if config.depth.scan_scope_mode == "changed" or (
        config.depth.scan_scope_mode == "auto" and depth in ("quick", "standard")
    ):
        try:
            from .quality_checks import ScanScope, compute_changed_files
            changed = compute_changed_files(Path(cwd))
            if changed:  # Only scope if we found changed files
                scan_scope = ScanScope(
                    mode="changed_only" if depth == "quick" else "changed_and_imports",
                    changed_files=changed,
                )
        except Exception:
            pass  # Fall back to full scan on any error
```

### Wiring 4: Update mock data scan gate + pass scope

**At line 3791, change the gate condition to use new config location:**

```python
# Before:
if not _use_milestones and config.milestone.mock_data_scan:

# After:
if not _use_milestones and (config.post_orchestration_scans.mock_data_scan or config.milestone.mock_data_scan):
```

**At line 3794, pass scope:**

```python
# Before:
mock_violations = run_mock_data_scan(Path(cwd))

# After:
mock_violations = run_mock_data_scan(Path(cwd), scope=scan_scope)
```

### Wiring 5: Update UI compliance scan gate + pass scope

**At line 3823, change the gate condition:**

```python
# Before:
if not _use_milestones and config.milestone.ui_compliance_scan:

# After:
if not _use_milestones and (config.post_orchestration_scans.ui_compliance_scan or config.milestone.ui_compliance_scan):
```

**At line 3826, pass scope:**

```python
# Before:
ui_violations = run_ui_compliance_scan(Path(cwd))

# After:
ui_violations = run_ui_compliance_scan(Path(cwd), scope=scan_scope)
```

### Wiring 6: Pass scope to integrity scans

**Asset scan at line 3886:**
```python
# Before:
asset_violations = run_asset_scan(Path(cwd))

# After:
asset_violations = run_asset_scan(Path(cwd), scope=scan_scope)
```

**Deployment scan at line 3857:** No scope change needed (self-gates on docker-compose, cheap).

### Wiring 7: Add PRD reconciliation REQUIREMENTS.md quality gate

**At line 3912, add a quality check for thorough mode:**

```python
# Before:
if config.integrity_scans.prd_reconciliation:

# After:
_should_run_prd_recon = config.integrity_scans.prd_reconciliation
if _should_run_prd_recon and depth == "thorough":
    # For thorough mode, only reconcile if REQUIREMENTS.md is substantial
    _req_path = Path(cwd) / config.convergence.requirements_dir / config.convergence.requirements_file
    if _req_path.is_file():
        _req_size = _req_path.stat().st_size
        _req_content = _req_path.read_text(encoding="utf-8", errors="replace")
        import re as _re_mod
        _has_req_items = bool(_re_mod.search(r"REQ-\d{3}", _req_content))
        if _req_size < 500 or not _has_req_items:
            _should_run_prd_recon = False
    else:
        _should_run_prd_recon = False
if _should_run_prd_recon:
```

### Wiring 8: Pass scope to database scans

**Dual ORM scan at line 3947:**
```python
# Before:
db_dual_violations = run_dual_orm_scan(Path(cwd))

# After:
db_dual_violations = run_dual_orm_scan(Path(cwd), scope=scan_scope)
```

**Default value scan at line 3982:**
```python
# Before:
db_default_violations = run_default_value_scan(Path(cwd))

# After:
db_default_violations = run_default_value_scan(Path(cwd), scope=scan_scope)
```

**Relationship scan at line 4017:**
```python
# Before:
db_rel_violations = run_relationship_scan(Path(cwd))

# After:
db_rel_violations = run_relationship_scan(Path(cwd), scope=scan_scope)
```

### Wiring 9: Add import for ScanScope and compute_changed_files

The scope computation in Wiring 3 uses a lazy import. Also ensure `PostOrchestrationScanConfig` is imported if needed (it's accessed via config object, so no explicit import needed in cli.py).

### Wiring 10: Update import at top of cli.py

**At line 42, update the config import to include the new function signatures:**

```python
# Verify this import includes apply_depth_quality_gating — it already does at line 42
from .config import AgentTeamConfig, apply_depth_quality_gating, detect_depth, ...
```

No change needed — the function is already imported. The new `user_overrides` parameter is optional, so existing calls work.

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

After Phase 2A, 2B, and 2C are complete, write tests covering:

### Depth Gating Tests (`tests/test_depth_gating.py`)

**Quick-mode gating tests:**
- Quick depth + default config → `mock_data_scan` is False
- Quick depth + default config → `ui_compliance_scan` is False
- Quick depth + default config → `deployment_scan` is False
- Quick depth + default config → `asset_scan` is False
- Quick depth + default config → `prd_reconciliation` is False
- Quick depth + default config → `dual_orm_scan` is False
- Quick depth + default config → `default_value_scan` is False
- Quick depth + default config → `relationship_scan` is False
- Quick depth + default config → `review_recovery_retries` is 0
- Quick depth + default config → `production_defaults` is False
- Quick depth + default config → `craft_review` is False
- Quick depth + default config → `e2e_testing.enabled` stays False (not changed)

**Standard-mode gating tests:**
- Standard depth → `prd_reconciliation` is False
- Standard depth → all other scans remain True (unchanged)
- Standard depth → `review_recovery_retries` remains 1 (unchanged)

**Thorough-mode gating tests:**
- Thorough depth → `e2e_testing.enabled` is True (auto-enabled)
- Thorough depth → `review_recovery_retries` is 2
- Thorough depth → all scans remain True

**Exhaustive-mode gating tests:**
- Exhaustive depth → `e2e_testing.enabled` is True (auto-enabled)
- Exhaustive depth → `review_recovery_retries` is 3
- Exhaustive depth → all scans remain True

**User override tests:**
- Quick depth + user set `mock_data_scan: true` → mock_data_scan stays True (override respected)
- Quick depth + user set `deployment_scan: true` → deployment_scan stays True
- Thorough depth + user set `e2e_testing.enabled: false` → E2E stays False (override respected)
- Standard depth + user set `prd_reconciliation: true` → prd_reconciliation stays True
- User override set contains exact dotted key path strings

**Backward compatibility tests:**
- Default config (no YAML) → all scans True, E2E False (same as before v6.0)
- `apply_depth_quality_gating("standard", config)` with no user_overrides → same as before
- `apply_depth_quality_gating("quick", config, None)` → None treated as empty set

### ScanScope Tests (`tests/test_scan_scope.py`)

**ScanScope dataclass tests:**
- Default ScanScope has mode="full", changed_files=[]
- ScanScope with changed_files stores paths correctly

**compute_changed_files tests:**
- Returns list of Path objects for modified files (mock subprocess)
- Returns list including untracked files (mock subprocess)
- Returns empty list when git not available (mock subprocess raising FileNotFoundError)
- Returns empty list when not a git repo (mock subprocess raising SubprocessError)
- Returns empty list on timeout (mock subprocess raising TimeoutExpired)
- Paths are resolved to absolute paths
- Empty git output → empty list (not crash)
- Lines with whitespace are stripped

**Scoped scan function tests (for each of 7 functions):**
- `run_X(project_root)` with no scope → scans all files (unchanged behavior)
- `run_X(project_root, scope=None)` → scans all files (unchanged behavior)
- `run_X(project_root, scope=ScanScope(changed_files=[...]))` → only scans specified files
- `run_X(project_root, scope=ScanScope(changed_files=[]))` → scans all files (empty = full fallback)
- Scope with files that don't match scan type → returns empty violations

### Config Evolution Tests (`tests/test_config_evolution.py`)

**PostOrchestrationScanConfig tests:**
- Default values: mock_data_scan=True, ui_compliance_scan=True
- YAML loading with `post_orchestration_scans:` section works
- YAML loading with old `milestone.mock_data_scan:` → copied to new config (backward-compat)
- Both sections present → `post_orchestration_scans` takes precedence

**_dict_to_config return type tests:**
- Returns tuple of (AgentTeamConfig, set)
- Empty YAML → empty user_overrides set
- YAML with `milestone.mock_data_scan: true` → "milestone.mock_data_scan" in user_overrides
- YAML with `e2e_testing.enabled: true` → "e2e_testing.enabled" in user_overrides
- YAML with `integrity_scans.deployment_scan: false` → "integrity_scans.deployment_scan" in user_overrides

**load_config return type tests:**
- Returns tuple of (AgentTeamConfig, set)
- No config file → (defaults, empty set)

**scan_scope_mode validation tests:**
- `scan_scope_mode: "auto"` → valid
- `scan_scope_mode: "full"` → valid
- `scan_scope_mode: "changed"` → valid
- `scan_scope_mode: "invalid"` → raises ValueError

### CLI Wiring Tests (`tests/test_mode_propagation_wiring.py`)

**Scope computation tests:**
- Quick depth + auto scope mode → scope computed with changed_only
- Standard depth + auto scope mode → scope computed with changed_and_imports
- Thorough depth + auto scope mode → scope is None (full scan)
- Exhaustive depth + auto scope mode → scope is None (full scan)
- scope_mode="full" overrides depth → scope is None always
- scope_mode="changed" overrides depth → scope computed always
- compute_changed_files failure → scope falls back to None

**PRD reconciliation quality gate tests:**
- Quick depth → PRD reconciliation disabled (via depth gating)
- Standard depth → PRD reconciliation disabled (via depth gating)
- Thorough depth + REQUIREMENTS.md >500 bytes with REQ-001 → runs
- Thorough depth + REQUIREMENTS.md <500 bytes → does NOT run
- Thorough depth + REQUIREMENTS.md without REQ-xxx → does NOT run
- Thorough depth + no REQUIREMENTS.md file → does NOT run
- Exhaustive depth → always runs (no quality gate)

**Scan call scope passing tests (mock scan functions):**
- Mock data scan called with scope when depth is standard
- Mock data scan called with scope=None when depth is thorough
- All 7 scoped scan functions receive scope parameter
- Deployment scan does NOT receive scope (no change)

**Gate condition migration tests:**
- `config.post_orchestration_scans.mock_data_scan = True` → scan runs
- `config.milestone.mock_data_scan = True` (old location) → scan runs (backward-compat OR)
- Both False → scan does NOT run

**E2E auto-enablement tests:**
- Quick depth → E2E stays disabled
- Standard depth → E2E stays disabled (user must opt in)
- Thorough depth + no user override → E2E auto-enabled
- Exhaustive depth + no user override → E2E auto-enabled
- Thorough depth + user set `e2e_testing.enabled: false` → E2E stays disabled

### Cross-Feature Integration Tests

- New PostOrchestrationScanConfig doesn't collide with existing configs
- `ScanScope` and `compute_changed_files` importable from quality_checks
- All scan functions still return `list[Violation]`
- Existing tests still pass (zero regressions)
- `_dict_to_config` with full YAML (all sections) → returns correct tuple

---

## PHASE 4: WIRING VERIFICATION

### 4A: Execution Position
- `compute_changed_files()` runs BEFORE any post-orchestration scan
- `apply_depth_quality_gating()` runs BEFORE `compute_changed_files()` (so disabled scans don't waste time computing scope)
- Scope is computed ONCE and reused across all scans
- PRD reconciliation quality gate runs BEFORE the LLM sub-orchestrator call

### 4B: Config Gating
- `config.post_orchestration_scans.mock_data_scan: false` → mock scan does not run
- `config.milestone.mock_data_scan: false` (old location) → mock scan does not run
- `config.e2e_testing.enabled: false` → E2E does not run even if depth is thorough
- Quick-mode depth gating disables 8 scans + sets 0 retries
- User override prevents depth gating from overriding explicit config

### 4C: Crash Isolation
- `compute_changed_files()` failure doesn't block any scan (falls back to full)
- `ScanScope` filtering failure doesn't crash scan functions
- Each post-orchestration scan still wrapped in its own try/except
- PRD reconciliation quality gate failure falls through to running reconciliation (safe default)

### 4D: Backward Compatibility
- Projects without `post_orchestration_scans` config → defaults apply (both True)
- Projects with `milestone.mock_data_scan: true` → still works via backward-compat alias
- `load_config()` callers that don't unpack tuple → **THIS WILL BREAK** — test-engineer must find and fix ALL callers
- `apply_depth_quality_gating(depth, config)` without user_overrides → still works (parameter defaults to None)
- All scan functions called without scope → still work (parameter defaults to None)

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
- **CRITICAL**: Check for ALL callers of `load_config()` — the return type changed from `AgentTeamConfig` to `tuple[AgentTeamConfig, set[str]]`. Every caller must be updated.
- **CRITICAL**: Windows encoding — use `encoding="utf-8"` when writing files with Unicode chars (checkmarks, etc.)

---

## PHASE 6: FINAL REPORT

After all phases complete, produce:

```markdown
# Mode Upgrade Propagation (v6.0) — Implementation Report

## Implementation Summary
- Modified: config.py (new PostOrchestrationScanConfig, extended apply_depth_quality_gating, user_overrides tracking)
- Modified: quality_checks.py (ScanScope dataclass, compute_changed_files, scope param on 7 functions)
- Modified: cli.py (scope computation, scan call updates, PRD recon quality gate, E2E auto-enable)
- New test files: test_depth_gating.py, test_scan_scope.py, test_config_evolution.py, test_mode_propagation_wiring.py

## Mode × Upgrade Propagation Matrix (verified)
| Upgrade | Quick | Standard | Thorough | Exhaustive |
|---------|-------|----------|----------|------------|
| Mock scan | SKIP (gated) | SCOPED | FULL | FULL |
| UI scan | SKIP (gated) | SCOPED | FULL | FULL |
| Deploy scan | SKIP (gated) | FULL | FULL | FULL |
| Asset scan | SKIP (gated) | SCOPED | FULL | FULL |
| PRD recon | SKIP (gated) | SKIP (gated) | CONDITIONAL | FULL |
| DB scans (3) | SKIP (gated) | SCOPED | FULL | FULL |
| E2E testing | SKIP | OPT-IN | AUTO-ENABLED | AUTO-ENABLED |
| Review retries | 0 | 1 | 2 | 3 |
| Prompt policies | ALL | ALL | ALL | ALL |

## Test Results
- New tests written: {X}
- All passing: {X}/{X}
- Regressions: 0

## Wiring Verification
- Execution position: VERIFIED
- Config gating: VERIFIED
- Crash isolation: VERIFIED
- Backward compatibility: VERIFIED

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone implements anything. The ARCHITECTURE_REPORT.md is the single source of truth for integration points, patterns, and insertion locations.

2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase. Consistency over creativity.

3. **READ BEFORE YOU WRITE** — Read every file before modifying it. Understand the context around your insertion point. Never modify a file you haven't read in the current session.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong.

5. **NO SHORTCUTS** — All deliverables must be fully implemented with generation, parsing, integration, and testing.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted.

7. **CRASH ISOLATION** — Every new integration point must be wrapped in its own try/except. New feature failures must NEVER block the main execution flow.

8. **BACKWARD COMPATIBLE** — A project with no config section for the new feature must work exactly as before. The `load_config()` return type change is the BIGGEST compatibility risk — find and fix ALL callers.

9. **BEST-EFFORT SCOPING** — If `compute_changed_files()` fails or returns empty, fall back to full-project scanning. Never let scoping logic prevent a scan from running.

10. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added.

11. **RUN TESTS AFTER EACH PHASE** — Don't wait until the end to discover failures.

12. **USER OVERRIDES ARE SACRED** — If a user explicitly sets a config field in YAML, depth gating MUST NOT override it. The `user_overrides` set is the enforcement mechanism.

13. **TUPLE UNPACKING IS CRITICAL** — `load_config()` now returns `(AgentTeamConfig, set[str])`. Every single caller must be found and updated. Missing even one will cause a runtime crash.
