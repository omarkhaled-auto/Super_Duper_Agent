# AUDIT: State Machine + CLI Framework (Build 3 PRD)

> Reviewer: state-cli agent
> Date: 2026-02-14
> Sources: Context7 `/pytransitions/transitions`, `/fastapi/typer`, `/websites/rich_readthedocs_io_en_stable`
> Files reviewed: `prompts/BUILD3_PRD.md` (M1 REQ-011, M5 REQ-046..053, M6 REQ-054..060, TECH-005..006/023..030, Transitions Reference), `prompts/BUILD3_TECH_STATE_CLI.md`

---

## Summary

- **3 CRITICAL issues** (will cause build failure or wrong behavior)
- **2 HIGH issues** (will cause confusion or partial failures)
- **3 MEDIUM issues** (could cause subtle bugs)
- **2 LOW issues** (cosmetic/documentation inconsistencies)

---

## 1. transitions Library Audit

### 1.1 Verified CORRECT

| Claim | PRD Location | Context7 Confirmation |
|-------|-------------|----------------------|
| `AsyncMachine` import from `transitions.extensions.asyncio` | TECH-005, REQ-011 | Confirmed: `from transitions.extensions.asyncio import AsyncMachine` |
| Machine constructor: `states`, `transitions`, `initial`, `send_event`, `queued`, `auto_transitions` | REQ-011, tech research 1.1 | All parameters confirmed |
| Transition dict keys: `trigger`, `source`, `dest`, `conditions`, `before`, `after`, `prepare` | Tech research 1.1 | All confirmed in Context7 callback docs |
| Guard conditions: `conditions=["method_name"]` must be model methods returning bool | Tech research 1.1 | Confirmed |
| State callbacks: `on_enter_STATE(self, event)`, `on_exit_STATE(self, event)` | Tech research 1.1 | Confirmed, both sync and async work with AsyncMachine |
| `queued=True` prevents nested transitions | REQ-011, tech research 1.4 | Confirmed: "processes events sequentially" |
| Wildcard source `"*"` for transitions | Tech research 1.1 | Confirmed: `machine.add_transition('to_liquid', '*', 'liquid')` |
| `MachineError` for invalid triggers | Tech research 1.1 | Confirmed: `transitions.core.MachineError` |
| `ignore_invalid_triggers` on Machine or State | Tech research 1.4 | Confirmed: global or per-state |
| `send_event=True` passes EventData to callbacks | Tech research 1.1 | Confirmed |
| State objects: `State(name=..., on_enter=[...], ignore_invalid_triggers=True)` | Tech research 1.4 | Confirmed |
| Callback execution order: `prepare -> conditions -> before -> on_exit -> STATE_CHANGE -> on_enter -> after` | Tech research 1.1 | Confirmed by Context7 execution order doc |
| AsyncMachine supports mixing sync and async callbacks | Tech research 1.3 | Confirmed: sync callbacks are wrapped automatically |
| Self-transitions (source == dest) are supported | Transition #12 retry_architect | Confirmed by library design |

### 1.2 CRITICAL-1: Transition Table Inconsistency (3 Conflicting Definitions)

**Severity: CRITICAL**
**Location: PRD State Machine Transitions Reference (line 599-616) vs Tech Research Section 1.1 (line 52-68) vs Tech Research Section 1.3 (line 284-298)**

The PRD contains **three different transition lists** that do not match:

#### PRD Transitions Reference (lines 599-616): 13 transitions
```
1. start_architect        init -> architect_running
2. architect_done         architect_running -> architect_review
3. approve_architecture   architect_review -> contracts_registering
4. contracts_ready        contracts_registering -> builders_running
5. builders_done          builders_running -> builders_complete
6. start_integration      builders_complete -> integrating
7. integration_done       integrating -> quality_gate
8. quality_passed         quality_gate -> complete
9. quality_failed         quality_gate -> fix_pass
10. fix_done              fix_pass -> quality_gate
11. fail                  * -> failed
12. retry_architect       architect_running -> architect_running (self-transition)
13. skip_contracts        contracts_registering -> builders_running
```
**MISSING: `reject_architecture` (architect_review -> architect_running)**

#### Tech Research Section 1.1 (lines 52-68): 12 transitions + wildcard
```
Includes `reject_architecture` (#4 in the code)
MISSING: retry_architect, skip_contracts
```

#### Tech Research Section 1.3 (lines 284-298): 13 transitions
```
Includes `reject_architecture` (#4)
Includes `retry_quality` (#13: failed -> quality_gate)
MISSING: retry_architect, skip_contracts
```

**Impact:** The builder will implement whichever list it encounters first. The `reject_architecture` transition is architecturally essential for the architect retry loop (REQ-053 references architect retries). Without it, there's no way to return from `architect_review` to `architect_running` for a re-run.

**FIX:** Consolidate to a single canonical transition list. Recommended 15 transitions:
```
1-11: (as in PRD Transitions Reference)
12: reject_architecture   architect_review -> architect_running   (guard: review_failed)
13: retry_architect        architect_running -> architect_running  (guard: retries_remaining)
14: skip_contracts         contracts_registering -> builders_running (guard: none)
15: retry_quality          failed -> quality_gate                   (guard: manual_retry)
```
Update REQ-011 to say "15 transitions" and update the Transitions Reference table.

### 1.3 CRITICAL-2: `fail` Trigger Guard Inconsistency

**Severity: CRITICAL**
**Location: PRD Transitions Reference line 613 vs Tech Research line 66-67**

The PRD Transitions Reference shows:
```
| 11 | fail | * (wildcard) | failed | -- | Any unrecoverable error |
```
The guard column shows "--" (no guard).

But the tech research code shows:
```python
{"trigger": "fail", "source": "*", "dest": "failed",
 "conditions": ["is_not_terminal"]},
```

These are two different approaches:
- **No guard + `ignore_invalid_triggers=True` on complete/failed States**: The `fail` trigger fires from all states but is silently ignored on `complete` and `failed`. This means calling `model.fail()` from `complete` returns `False` (no error, no transition).
- **Guard `is_not_terminal`**: The `fail` trigger exists on all states but the guard prevents it from firing on terminal states. This means calling `model.fail()` from `complete` returns `False` (guard failed, no transition).

Both approaches produce the same behavior **if `ignore_invalid_triggers` is also set on terminal states**. But if only the guard approach is used without `ignore_invalid_triggers`, then calling an unrelated trigger from `complete`/`failed` will raise `MachineError`.

**Impact:** The builder must know which approach to use. If they implement the guard but forget `ignore_invalid_triggers`, other triggers called from terminal states will crash.

**FIX:** Use BOTH approaches together (defense in depth):
```python
states = [
    ...
    State("complete", on_enter=["print_summary"], ignore_invalid_triggers=True),
    State("failed", on_enter=["save_failure_report"], ignore_invalid_triggers=True),
]

transitions = [
    ...
    {"trigger": "fail", "source": "*", "dest": "failed", "conditions": ["is_not_terminal"]},
]
```
Document this explicitly in REQ-011: "Terminal states (`complete`, `failed`) must use `State(ignore_invalid_triggers=True)` AND the `fail` trigger must have `conditions=["is_not_terminal"]`."

### 1.4 CRITICAL-3: `create_pipeline_machine` Factory Function Return Type Mismatch

**Severity: CRITICAL**
**Location: REQ-011, Tech Research section 8.4**

REQ-011 says:
> Create `create_pipeline_machine(model, initial_state="init") -> AsyncMachine` factory function

But the tech research section 8.4 shows:
```python
def create_pipeline_machine(state: PipelineState) -> AsyncMachine:
    machine = AsyncMachine(
        states=STATES,
        transitions=TRANSITIONS,
        initial=state.current_state,
        send_event=True,
        queued=True,
    )
    return machine
```

**Problem:** This creates an AsyncMachine WITHOUT a model. When no model is passed to AsyncMachine, the machine itself becomes the model and triggers are attached to the machine object. But REQ-053 (`execute_pipeline`) expects to call triggers on a separate orchestrator model object (e.g., `await model.start_architect()`).

The correct pattern from Context7 is:
```python
model = SomeModel()
machine = AsyncMachine(model=model, states=..., transitions=..., initial=...)
await model.start_architect()  # trigger is on the model
```

If the machine is used as its own model:
```python
machine = AsyncMachine(states=..., transitions=..., initial=...)
await machine.start_architect()  # trigger is on the machine
```

REQ-011 says `model` parameter exists, tech research omits it. The builder won't know whether to pass a model or use the machine as model.

**FIX:** Clarify in REQ-011:
```python
def create_pipeline_machine(model: object, initial_state: str = "init") -> AsyncMachine:
    return AsyncMachine(
        model=model,
        states=STATES,
        transitions=TRANSITIONS,
        initial=initial_state,
        auto_transitions=False,
        send_event=True,
        queued=True,
    )
```
The model object (e.g., a PipelineExecutor class) must define all callback methods (`on_enter_*`, guard conditions, `before`/`after` callbacks). State is accessed via `model.state`.

---

## 2. Typer Audit

### 2.1 Verified CORRECT

| Claim | PRD Location | Context7 Confirmation |
|-------|-------------|----------------------|
| `typer.Typer()` app creation | REQ-054, TECH-028 | Confirmed |
| `@app.command()` decorator | REQ-054 | Confirmed |
| `typer.Option()` with help text, defaults | Tech research 2.2 | Confirmed |
| `typer.Argument()` with Path type | Tech research 2.2 | Confirmed |
| `@app.callback()` for global options | Tech research 2.2 | Confirmed |
| `raise typer.Exit(code=1)` for exit codes | REQ-055 | Confirmed: `raise typer.Exit(code=1)` |
| `typer.confirm()` for interactive prompts | Tech research 2.2 | Confirmed |
| `app.add_typer()` for subcommand groups | Tech research 2.2 | Confirmed |
| `Annotated[type, typer.Option()]` syntax | Tech research 2.2 | Confirmed (Python 3.9+ style) |
| `rich_markup_mode="rich"` | TECH-028 | Confirmed Typer parameter |
| `no_args_is_help=True` | Tech research 2.2 | Confirmed |
| Typer uses Click's `CliRunner` for testing | Tech research 2.3 | Confirmed: `from typer.testing import CliRunner` |
| No native async support (use `asyncio.run()` wrapper) | Tech research 2.3 | Confirmed |
| `typer[all]` includes Rich + shellingham | Tech research 2.2 | Confirmed |

### 2.2 HIGH-1: Missing `--version` Flag Implementation

**Severity: HIGH**
**Location: REQ-054**

REQ-054 defines 8 commands but does not include a `--version` flag. The tech research section 2.2 also omits it. Standard CLI practice requires a `--version` flag.

Context7 confirms the Typer pattern:
```python
def version_callback(value: bool) -> None:
    if value:
        typer.echo("Super Orchestrator v3.0.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Annotated[Optional[bool], typer.Option(
        "--version", callback=version_callback, is_eager=True, expose_value=False
    )] = None,
):
    ...
```

**FIX:** Add `--version` flag to `@app.callback()` using `is_eager=True` pattern. Reference `__version__` from `__init__.py` (REQ-014 already defines `__version__ = "3.0.0"`).

### 2.3 HIGH-2: `asyncio.run()` Pattern Not Documented for CLI Commands

**Severity: HIGH**
**Location: REQ-054, TECH-029**

TECH-029 says "All CLI commands that run async code must use a single `asyncio.run()` call" but REQ-054 does not show how individual commands (plan, build, integrate, verify) call async functions. Only the tech research section 8.4 shows the pattern:
```python
asyncio.run(_execute_pipeline(orchestrator, state, tracker))
```

The builder may not understand that EACH command needs its own `asyncio.run()` wrapper, since the Typer `@app.command()` function is synchronous.

**FIX:** Add to REQ-054 or TECH-029:
```python
@app.command()
def plan(system: str = "all"):
    """Run the Architect."""
    config = load_super_config(...)
    state = PipelineState.load() or PipelineState()
    asyncio.run(_async_plan(config, state, system))

async def _async_plan(config, state, system):
    await run_architect_phase(...)
```

---

## 3. Rich Audit

### 3.1 Verified CORRECT

| Claim | PRD Location | Context7 Confirmation |
|-------|-------------|----------------------|
| `Progress(SpinnerColumn(), TextColumn(...), BarColumn(), TimeElapsedColumn())` | TECH-030, REQ-059 | All column types confirmed |
| `progress.add_task(description, total=N)` | Tech research 3.2 | Confirmed |
| `progress.update(task_id, advance=N)` | Tech research 3.2 | Confirmed |
| `Table(title="...")`, `add_column()`, `add_row()` | REQ-059, tech research 3.1 | Confirmed |
| `Panel(content, title="...", border_style="...")` | REQ-059, tech research 3.1 | Confirmed |
| `Live(renderable, refresh_per_second=N)` with `live.update()` | Tech research 3.3 | Confirmed |
| `Console()` with `.print()`, `.status()`, `.log()` | Tech research 3.4 | Confirmed |
| `console.status("[bold green]...")` context manager | Tech research 3.4 | Confirmed |
| Rich markup: `[bold red]text[/bold red]`, `[/]` shorthand | Tech research 3.1 | Confirmed |
| `Layout()` with `split_column()`, `split_row()` | Tech research 3.3 | Confirmed |

### 3.2 MEDIUM-1: `Group` Import Path Not Specified

**Severity: MEDIUM**
**Location: REQ-059**

REQ-059 uses `Panel(Group(Table(...)))` but does not specify the import path for `Group`. In Rich 13+, it's:
```python
from rich.console import Group
```

**FIX:** Add to REQ-059: "Import `Group` from `rich.console`."

### 3.3 MEDIUM-2: `TimeElapsedColumn` vs `TimeRemainingColumn` Inconsistency

**Severity: MEDIUM**
**Location: TECH-030 vs Tech Research 3.2**

TECH-030 specifies:
```python
Progress(SpinnerColumn(), TextColumn("..."), BarColumn(), TimeElapsedColumn())
```

But the tech research section 3.2 uses:
```python
Progress(SpinnerColumn(), TextColumn("..."), BarColumn(), TaskProgressColumn(), TimeRemainingColumn())
```

These are different columns:
- `TimeElapsedColumn` shows how long the task has been running
- `TimeRemainingColumn` shows estimated time remaining (requires known `total`)
- `TaskProgressColumn` shows "X/Y" completed count

For the Super Orchestrator, `TimeElapsedColumn` is appropriate for phases with unknown duration (most phases), while `TimeRemainingColumn` is appropriate for builders with known total count.

**FIX:** Use `TimeElapsedColumn` for phase-level progress (TECH-030 is correct). For builder-level progress in `print_builder_table`, use `TaskProgressColumn() + TimeRemainingColumn()` since the total number of builders is known. Document both patterns in REQ-059.

### 3.4 MEDIUM-3: Missing `Console()` Singleton Pattern

**Severity: MEDIUM**
**Location: REQ-059**

REQ-059 defines display functions but doesn't specify whether they should use a shared `Console()` instance or create new ones. Creating multiple `Console()` instances can cause display corruption when used with `Live()`.

**FIX:** Add to REQ-059: "Create a module-level `console = Console()` singleton in `display.py`. All display functions must use this shared instance."

---

## 4. State Machine Design Audit

### 4.1 State Reachability Analysis

All 11 states are reachable from `init` via forward transitions:

```
init
  -> architect_running (start_architect)
    -> architect_review (architect_done)
      -> contracts_registering (approve_architecture)
        -> builders_running (contracts_ready)
          -> builders_complete (builders_done)
            -> integrating (start_integration)
              -> quality_gate (integration_done)
                -> complete (quality_passed)
                -> fix_pass (quality_failed)
                  -> quality_gate (fix_done) [cycle]
  * -> failed (fail) [from any non-terminal state]
```

**VERIFIED:** All 11 states are reachable. No orphan states.

### 4.2 Missing Reverse Transitions

The state machine has no way to go from `failed` back to any running state EXCEPT via `retry_quality` (tech research table) which the PRD Transitions Reference omits. This means:
- If the architect fails after exhausting retries, the pipeline is permanently stuck in `failed`
- If integration fails, the pipeline is permanently stuck in `failed`
- The only recovery is manual: delete state file and re-run

This is acceptable design IF documented. Currently it's ambiguous.

### 4.3 State Persistence JSON Schema

The `PipelineState` dataclass uses only JSON-serializable types:
- `str`, `int`, `float`, `bool`, `None` (primitives)
- `list[str]`, `dict[str, str]`, `dict[str, float]`, `dict[str, bool]`, `dict[str, list[str]]` (collections)

**VERIFIED:** All field types are JSON-serializable via `dataclasses.asdict()`.

### 4.4 Concurrent Access Safety

- `queued=True` prevents concurrent transition execution within a single AsyncMachine
- Each builder runs as a separate subprocess with its own state
- The Super Orchestrator's PipelineState is written atomically (tmp+rename)

**VERIFIED:** No concurrent access risks identified.

---

## 5. LOW Issues

### LOW-1: Tech Research "10 States + Terminal" Title

**Location:** Tech research section 1.3 table title (line 283)

Says "10 States + Terminal" but there are 11 states total (9 running + 2 terminal). The title should say "11 States (9 Running + 2 Terminal)" or just "11 States".

### LOW-2: RESUME_TRIGGERS Inconsistency

**Location:** Tech research section 6.3 vs REQ-011

The tech research defines `RESUME_TRIGGERS` as a dict mapping `current_state -> trigger_name`. But some mappings don't match the transition table:
- `"architect_review": "approve_architecture"` -- this would skip the review on resume, auto-approving
- `"builders_running": "start_builders"` -- `start_builders` is not a defined trigger

REQ-011 says "Include RESUME_TRIGGERS dict mapping each state to its resume trigger" but doesn't specify the exact mappings.

**FIX:** Define RESUME_TRIGGERS explicitly in REQ-011 with correct trigger names matching the canonical transition table:
```python
RESUME_TRIGGERS = {
    "init": "start_architect",
    "architect_running": "start_architect",      # Re-run architect from scratch
    "architect_review": "architect_done",         # Re-enter review (not auto-approve)
    "contracts_registering": "contracts_ready",
    "builders_running": "builders_done",           # Check builder results
    "builders_complete": "start_integration",
    "integrating": "integration_done",
    "quality_gate": "quality_passed",              # Re-evaluate gate
    "fix_pass": "fix_done",
}
```

---

## 6. Issue Summary and Recommended Fixes

| # | Severity | Issue | PRD Location | Fix |
|---|----------|-------|-------------|-----|
| C1 | CRITICAL | 3 conflicting transition lists (13 vs 12+1 vs 13 with different transitions) | REQ-011, Transitions Reference, Tech Research 1.1/1.3 | Consolidate to single canonical list of 15 transitions including reject_architecture, retry_architect, skip_contracts, retry_quality |
| C2 | CRITICAL | `fail` trigger guard inconsistency (none vs `is_not_terminal`) | Transitions Reference line 613 vs Tech Research line 66 | Use BOTH: guard condition AND `ignore_invalid_triggers=True` on terminal states. Document in REQ-011 |
| C3 | CRITICAL | `create_pipeline_machine` factory missing `model` parameter in tech research example | REQ-011 vs Tech Research 8.4 | Clarify that model object must be passed, define which class serves as model, list required callback methods |
| H1 | HIGH | Missing `--version` CLI flag | REQ-054 | Add `--version` flag via `@app.callback()` with `is_eager=True` pattern |
| H2 | HIGH | `asyncio.run()` wrapper pattern not shown for individual CLI commands | REQ-054, TECH-029 | Add explicit example showing sync command wrapping async function |
| M1 | MEDIUM | `Group` import path not specified | REQ-059 | Add: `from rich.console import Group` |
| M2 | MEDIUM | `TimeElapsedColumn` vs `TimeRemainingColumn` used inconsistently | TECH-030 vs Tech Research 3.2 | Document both: TimeElapsed for phases, TimeRemaining for builders |
| M3 | MEDIUM | No `Console()` singleton pattern specified | REQ-059 | Add module-level `console = Console()` requirement |
| L1 | LOW | "10 States + Terminal" title incorrect | Tech Research 1.3 | Fix to "11 States" |
| L2 | LOW | RESUME_TRIGGERS has undefined trigger names | Tech Research 6.3 | Define explicit mappings in REQ-011 with correct trigger names |

---

## 7. Verification Checklist (Post-Fix)

After applying fixes, verify:

- [ ] Single canonical transition list exists (either in PRD Transitions Reference or REQ-011, not both)
- [ ] `reject_architecture` transition is present
- [ ] `retry_architect` self-transition is present
- [ ] `skip_contracts` transition is present
- [ ] `fail` trigger has both guard condition AND terminal states have `ignore_invalid_triggers=True`
- [ ] `create_pipeline_machine` signature includes `model` parameter
- [ ] `--version` flag documented in REQ-054
- [ ] `asyncio.run()` wrapper pattern shown for at least one CLI command
- [ ] RESUME_TRIGGERS defined with valid trigger names
- [ ] Total transition count matches between REQ-011 description and Transitions Reference table
