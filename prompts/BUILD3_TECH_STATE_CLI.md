# Build 3 Technology Research: State Machine, CLI & Async Orchestration

> Research Date: 2026-02-14
> Python Target: 3.12+
> Purpose: Technology decisions and API references for the Super Orchestrator

---

## Table of Contents

1. [Python State Machine Patterns](#1-python-state-machine-patterns)
2. [CLI Framework Comparison (Click vs Typer)](#2-cli-framework-comparison)
3. [Rich Terminal UI](#3-rich-terminal-ui)
4. [Async Orchestration Patterns](#4-async-orchestration-patterns)
5. [Cost Tracking](#5-cost-tracking)
6. [State Persistence](#6-state-persistence)
7. [Existing Agent-Team Patterns](#7-existing-agent-team-patterns)
8. [Recommendations](#8-recommendations)

---

## 1. Python State Machine Patterns

### 1.1 `transitions` Library (Recommended)

**Install:** `pip install transitions`
**Version:** 0.9.2+ (latest stable)
**Async Support:** Built-in via `AsyncMachine`

#### Basic Machine API

```python
from transitions import Machine

class SuperOrchestrator:
    pass

states = [
    "init",
    "architect_running",
    "architect_review",
    "contracts_registering",
    "builders_running",
    "builders_complete",
    "integrating",
    "quality_gate",
    "fix_pass",
    "complete",
    "failed",
]

transitions = [
    # trigger, source, dest
    {"trigger": "start_architect", "source": "init", "dest": "architect_running"},
    {"trigger": "architect_done", "source": "architect_running", "dest": "architect_review"},
    {"trigger": "approve_architecture", "source": "architect_review", "dest": "contracts_registering"},
    {"trigger": "reject_architecture", "source": "architect_review", "dest": "architect_running"},
    {"trigger": "contracts_ready", "source": "contracts_registering", "dest": "builders_running"},
    {"trigger": "builders_done", "source": "builders_running", "dest": "builders_complete"},
    {"trigger": "start_integration", "source": "builders_complete", "dest": "integrating"},
    {"trigger": "integration_done", "source": "integrating", "dest": "quality_gate"},
    {"trigger": "quality_passed", "source": "quality_gate", "dest": "complete"},
    {"trigger": "quality_failed", "source": "quality_gate", "dest": "fix_pass"},
    {"trigger": "fix_done", "source": "fix_pass", "dest": "quality_gate"},
    # Error transitions from any non-terminal state
    {"trigger": "fail", "source": "*", "dest": "failed",
     "conditions": ["is_not_terminal"]},
]

orchestrator = SuperOrchestrator()
machine = Machine(
    model=orchestrator,
    states=states,
    transitions=transitions,
    initial="init",
    auto_transitions=False,  # Disable auto-generated to_<state>() methods
    send_event=True,         # Pass EventData to callbacks
)

# Usage
orchestrator.start_architect()    # init -> architect_running
print(orchestrator.state)         # "architect_running"
orchestrator.architect_done()     # architect_running -> architect_review
```

#### Callbacks (before/after/on_enter/on_exit/prepare/conditions)

```python
transitions = [
    {
        "trigger": "start_architect",
        "source": "init",
        "dest": "architect_running",
        "before": "validate_config",       # Called before transition
        "after": "launch_architect_agent",  # Called after transition
        "prepare": "load_prd",             # Called before conditions check
        "conditions": ["has_valid_prd"],    # Must return True to proceed
    },
]

class SuperOrchestrator:
    def validate_config(self, event):
        """Called before transition. Raise to abort."""
        if not self.config:
            raise ValueError("No config loaded")

    def launch_architect_agent(self, event):
        """Called after successful transition."""
        self.architect_cost = asyncio.run(self._run_architect())

    def load_prd(self, event):
        """Called before conditions are evaluated."""
        self.prd_content = Path("PRD.md").read_text()

    def has_valid_prd(self, event) -> bool:
        """Guard condition. Return False to block transition."""
        return bool(getattr(self, "prd_content", ""))

    def on_enter_architect_running(self, event):
        """Automatic callback when entering state."""
        print(f"Entering architect_running at {datetime.now()}")

    def on_exit_init(self, event):
        """Automatic callback when leaving state."""
        print("Leaving init state")
```

#### AsyncMachine for Async Transitions (Python 3.12+)

```python
from transitions.extensions.asyncio import AsyncMachine
import asyncio

class AsyncOrchestrator:
    async def on_enter_architect_running(self, event):
        """Async callback — awaited automatically."""
        self.cost = await self._run_architect_session()

    async def on_enter_builders_running(self, event):
        """Launch parallel builders."""
        results = await asyncio.gather(
            self._run_builder("system3"),
            self._run_builder("system4"),
            self._run_builder("system5"),
            return_exceptions=True,
        )
        self.builder_results = results

    async def _run_architect_session(self) -> float:
        # Sub-orchestrator call
        return 0.0

    async def _run_builder(self, system: str) -> float:
        return 0.0

machine = AsyncMachine(
    model=AsyncOrchestrator(),
    states=states,
    transitions=transitions,
    initial="init",
    send_event=True,
)

# Must be awaited
async def main():
    orch = AsyncOrchestrator()
    machine = AsyncMachine(model=orch, states=states,
                           transitions=transitions, initial="init")
    await orch.start_architect()   # Async trigger
    await orch.architect_done()
```

#### Alternative: MachineFactory for async

```python
from transitions.extensions import MachineFactory

AsyncMachine = MachineFactory.get_predefined(asyncio=True)
# Equivalent to: from transitions.extensions.asyncio import AsyncMachine
```

#### State Objects (Rich State Metadata)

```python
from transitions import Machine, State

states = [
    State(name="init", on_enter=["log_entry"], on_exit=["log_exit"]),
    State(name="architect_running", on_enter=["start_timer"]),
    State(name="failed", on_enter=["save_failure_report"], ignore_invalid_triggers=True),
    State(name="complete", on_enter=["print_summary"], ignore_invalid_triggers=True),
]
```

#### Queued Transitions (Thread-Safe)

```python
machine = Machine(
    model=orchestrator,
    states=states,
    transitions=transitions,
    initial="init",
    queued=True,  # Queue transitions triggered during callbacks
)
```

### 1.2 Custom Enum-Based FSM (Alternative — No Dependencies)

```python
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Any

class OrchestratorState(Enum):
    INIT = auto()
    ARCHITECT_RUNNING = auto()
    ARCHITECT_REVIEW = auto()
    CONTRACTS_REGISTERING = auto()
    BUILDERS_RUNNING = auto()
    BUILDERS_COMPLETE = auto()
    INTEGRATING = auto()
    QUALITY_GATE = auto()
    FIX_PASS = auto()
    COMPLETE = auto()
    FAILED = auto()

@dataclass
class Transition:
    source: OrchestratorState
    dest: OrchestratorState
    guard: Callable[..., bool] | None = None
    before: Callable[..., Any] | None = None
    after: Callable[..., Any] | None = None

class StateMachine:
    def __init__(self, initial: OrchestratorState):
        self.state = initial
        self._transitions: dict[str, list[Transition]] = {}
        self._on_enter: dict[OrchestratorState, list[Callable]] = {}
        self._on_exit: dict[OrchestratorState, list[Callable]] = {}

    def add_transition(self, trigger: str, transition: Transition) -> None:
        self._transitions.setdefault(trigger, []).append(transition)

    def add_on_enter(self, state: OrchestratorState, callback: Callable) -> None:
        self._on_enter.setdefault(state, []).append(callback)

    def trigger(self, event: str, **kwargs: Any) -> bool:
        for t in self._transitions.get(event, []):
            if t.source != self.state:
                continue
            if t.guard and not t.guard(**kwargs):
                continue
            # Execute transition
            if t.before:
                t.before(**kwargs)
            for cb in self._on_exit.get(self.state, []):
                cb(**kwargs)
            self.state = t.dest
            for cb in self._on_enter.get(t.dest, []):
                cb(**kwargs)
            if t.after:
                t.after(**kwargs)
            return True
        return False

    @property
    def is_terminal(self) -> bool:
        return self.state in (OrchestratorState.COMPLETE, OrchestratorState.FAILED)

# Usage
sm = StateMachine(OrchestratorState.INIT)
sm.add_transition("start_architect", Transition(
    source=OrchestratorState.INIT,
    dest=OrchestratorState.ARCHITECT_RUNNING,
    guard=lambda: True,
))
sm.trigger("start_architect")
assert sm.state == OrchestratorState.ARCHITECT_RUNNING
```

### 1.3 Full Transition Table (10 States + Terminal)

| # | Trigger                | Source                | Dest                  | Guard Condition           |
|---|------------------------|-----------------------|-----------------------|---------------------------|
| 1 | `start_architect`      | INIT                  | ARCHITECT_RUNNING     | config loaded, PRD valid  |
| 2 | `architect_done`       | ARCHITECT_RUNNING     | ARCHITECT_REVIEW      | output files exist        |
| 3 | `approve_architecture` | ARCHITECT_REVIEW      | CONTRACTS_REGISTERING | review passed             |
| 4 | `reject_architecture`  | ARCHITECT_REVIEW      | ARCHITECT_RUNNING     | review failed, retries<N  |
| 5 | `contracts_ready`      | CONTRACTS_REGISTERING | BUILDERS_RUNNING      | CONTRACTS.json valid      |
| 6 | `builders_done`        | BUILDERS_RUNNING      | BUILDERS_COMPLETE     | all builders finished     |
| 7 | `start_integration`    | BUILDERS_COMPLETE     | INTEGRATING           | >=1 builder succeeded     |
| 8 | `integration_done`     | INTEGRATING           | QUALITY_GATE          | integration report exists |
| 9 | `quality_passed`       | QUALITY_GATE          | COMPLETE              | all checks pass           |
| 10| `quality_failed`       | QUALITY_GATE          | FIX_PASS              | failures exist, retries<N |
| 11| `fix_done`             | FIX_PASS              | QUALITY_GATE          | fix cycle complete        |
| 12| `fail`                 | *(any non-terminal)*  | FAILED                | unrecoverable error       |
| 13| `retry_quality`        | FAILED                | QUALITY_GATE          | manual retry requested    |

### 1.4 Decision: `transitions` Library vs Custom Enum FSM

| Criterion                    | `transitions` Library           | Custom Enum FSM          |
|------------------------------|--------------------------------|--------------------------|
| Dependencies                 | 1 package (transitions)        | None                     |
| Async support                | Built-in AsyncMachine          | Must implement manually  |
| Guard conditions             | Declarative `conditions=[...]` | Manual if/else            |
| Callback ordering            | prepare > conditions > before > on_exit > on_enter > after | Manual |
| Queued transitions           | Built-in `queued=True`         | Must implement manually  |
| State diagrams               | `transitions[diagrams]`        | None                     |
| Wildcard sources (`"*"`)     | Built-in                       | Must implement manually  |
| Type safety                  | String-based states            | Enum-based (mypy-safe)   |
| Test complexity              | Moderate (mock callbacks)      | Low (direct state check) |
| Lines of code                | ~20 lines setup                | ~80 lines implementation |

**RECOMMENDATION:** Use `transitions` library with `AsyncMachine`. The declarative transition table matches the Super Orchestrator's needs exactly, and the built-in async support avoids reinventing callback management. The 10-state FSM with guard conditions is the library's sweet spot.

---

## 2. CLI Framework Comparison

### 2.1 Click (v8.1+)

**Install:** `pip install click`
**Source:** Context7 `/pallets/click` (654 code snippets, High reputation, Score 88.6)

#### Super Orchestrator CLI Structure with Click

```python
import click
from pathlib import Path

@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), default=None,
              help="Path to config.yaml")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--depth", type=click.Choice(["quick", "standard", "thorough", "exhaustive"]),
              default=None, help="Override depth level")
@click.pass_context
def cli(ctx, config, verbose, depth):
    """Super Orchestrator -- Multi-system build pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["depth"] = depth

@cli.command()
@click.argument("prd_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default=".", help="Output directory")
@click.pass_context
def init(ctx, prd_path, output_dir):
    """Initialize a new build from a PRD file."""
    config = load_config(ctx.obj["config_path"])
    # ... initialization logic

@cli.command()
@click.option("--system", type=click.Choice(["all", "3", "4", "5"]), default="all")
@click.pass_context
def plan(ctx, system):
    """Run the Architect (System 1) to produce architecture docs."""
    pass

@cli.command()
@click.option("--parallel/--sequential", default=True,
              help="Run builders in parallel (default) or sequentially")
@click.option("--system", "-s", multiple=True,
              help="Build specific systems only (3, 4, 5)")
@click.pass_context
def build(ctx, parallel, system):
    """Run Builders (Systems 3-5) to produce code."""
    pass

@cli.command()
@click.pass_context
def integrate(ctx):
    """Run the Integrator to merge builder outputs."""
    pass

@cli.command()
@click.option("--fix/--no-fix", default=True,
              help="Auto-fix failures (default: yes)")
@click.pass_context
def verify(ctx):
    """Run quality gate verification."""
    pass

@cli.command()
@click.argument("prd_path", type=click.Path(exists=True))
@click.option("--resume/--fresh", default=False,
              help="Resume from saved state")
@click.pass_context
def run(ctx, prd_path, resume):
    """Run full pipeline: plan -> build -> integrate -> verify."""
    pass

@cli.command()
@click.pass_context
def status(ctx):
    """Show current pipeline state and progress."""
    pass

@cli.command()
@click.pass_context
def resume(ctx):
    """Resume an interrupted pipeline from saved state."""
    pass

if __name__ == "__main__":
    cli()
```

#### Click Key Features

```python
# Choice parameter with validation
@click.option("--depth", type=click.Choice(["quick", "standard", "thorough", "exhaustive"]))

# File path with existence check
@click.argument("prd", type=click.Path(exists=True, path_type=Path))

# Multiple values
@click.option("--system", "-s", multiple=True, type=int)

# Password prompt (for API keys)
@click.option("--api-key", prompt=True, hide_input=True)

# Confirmation
@click.confirm("Run the full pipeline?", abort=True)

# Environment variable fallback
@click.option("--api-key", envvar="ANTHROPIC_API_KEY")

# Progress bar
with click.progressbar(items, label="Building") as bar:
    for item in bar:
        process(item)

# Context passing to subcommands
@click.pass_context
def cmd(ctx):
    ctx.obj["key"] = "value"  # Available to child commands
```

### 2.2 Typer (v0.21+)

**Install:** `pip install typer[all]`  (includes Rich + shellingham)
**Source:** Context7 `/fastapi/typer` (736 code snippets, Medium reputation, Score 86.8)

#### Super Orchestrator CLI Structure with Typer

```python
import typer
from pathlib import Path
from typing import Annotated, Optional
from enum import Enum

class Depth(str, Enum):
    quick = "quick"
    standard = "standard"
    thorough = "thorough"
    exhaustive = "exhaustive"

app = typer.Typer(
    name="super-orchestrator",
    help="Multi-system build pipeline with state machine orchestration.",
    no_args_is_help=True,
)

@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[Optional[Path], typer.Option(
        "--config", "-c", help="Path to config.yaml"
    )] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    depth: Annotated[Optional[Depth], typer.Option()] = None,
):
    """Super Orchestrator -- Multi-system build pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["depth"] = depth

@app.command()
def init(
    ctx: typer.Context,
    prd_path: Annotated[Path, typer.Argument(help="Path to PRD file")],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("."),
):
    """Initialize a new build from a PRD file."""
    if not prd_path.exists():
        typer.echo(f"PRD not found: {prd_path}", err=True)
        raise typer.Exit(code=1)

@app.command()
def plan(
    ctx: typer.Context,
    system: Annotated[str, typer.Option()] = "all",
):
    """Run the Architect (System 1) to produce architecture docs."""
    pass

@app.command()
def build(
    ctx: typer.Context,
    parallel: Annotated[bool, typer.Option("--parallel/--sequential")] = True,
    system: Annotated[Optional[list[int]], typer.Option("--system", "-s")] = None,
):
    """Run Builders (Systems 3-5) to produce code."""
    pass

@app.command()
def integrate(ctx: typer.Context):
    """Run the Integrator to merge builder outputs."""
    pass

@app.command()
def verify(
    ctx: typer.Context,
    fix: Annotated[bool, typer.Option("--fix/--no-fix")] = True,
):
    """Run quality gate verification."""
    pass

@app.command()
def run(
    ctx: typer.Context,
    prd_path: Annotated[Path, typer.Argument()],
    resume: Annotated[bool, typer.Option("--resume/--fresh")] = False,
):
    """Run full pipeline: plan -> build -> integrate -> verify."""
    pass

@app.command()
def status(ctx: typer.Context):
    """Show current pipeline state and progress."""
    pass

if __name__ == "__main__":
    app()
```

#### Typer Key Features

```python
# Enum choices (auto-generated from Enum class)
class Depth(str, Enum):
    quick = "quick"
    standard = "standard"

# Type-safe arguments with Annotated
def cmd(name: Annotated[str, typer.Argument(help="User name")]):
    pass

# Confirmation prompt
delete = typer.confirm("Are you sure?")

# Rich integration (built-in when typer[all] installed)
from rich.console import Console
console = Console()
console.print("[bold green]Success[/]")

# Auto-completion support
# pip install typer[all]  # includes shellingham for auto-detection

# Nested sub-apps
pipeline_app = typer.Typer()
app.add_typer(pipeline_app, name="pipeline", help="Pipeline operations")

@pipeline_app.command()
def start():
    """Start the pipeline."""
    pass
```

### 2.3 Click vs Typer Comparison Table

| Criterion                    | Click 8.1                       | Typer 0.21                      | Winner       |
|------------------------------|--------------------------------|--------------------------------|--------------|
| **Type safety**              | String-based params            | Type hints + Annotated         | Typer        |
| **Learning curve**           | Moderate (decorators)          | Low (Python type hints)        | Typer        |
| **Documentation**            | Excellent (654 snippets)       | Good (736 snippets)            | Tie          |
| **Rich integration**         | Manual (separate import)       | Built-in with `typer[all]`     | Typer        |
| **Auto-completion**          | Via click-completion           | Built-in with shellingham      | Typer        |
| **Testing**                  | `CliRunner` (excellent)        | Uses Click's `CliRunner`       | Tie          |
| **Async support**            | No native async                | No native async                | Tie          |
| **Maturity**                 | 10+ years, battle-tested       | 4+ years, FastAPI ecosystem    | Click        |
| **Error messages**           | Good                           | Excellent (color + suggestions)| Typer        |
| **Subcommand nesting**       | `@cli.group()` decorator       | `app.add_typer()` method       | Tie          |
| **Env var fallback**         | `envvar=` param                | Via Click compatibility        | Click        |
| **File path validation**     | `click.Path(exists=True)`      | `Path` type + validation       | Click        |
| **Progress bars**            | `click.progressbar()`          | Via Rich (more powerful)       | Typer        |
| **Bundle size**              | ~100KB                         | ~200KB (includes Click)        | Click        |
| **Python 3.12+ compat**     | Yes                            | Yes                            | Tie          |
| **Existing agent-team style**| argparse (similar paradigm)    | Different paradigm             | Click        |

**RECOMMENDATION:** Use **Typer** for the Super Orchestrator CLI. The type-hint-based API is more Pythonic for Python 3.12+, the built-in Rich integration eliminates a separate dependency setup, and the auto-completion support improves UX. Typer is built on Click internally, so all Click testing patterns (CliRunner) work unchanged.

**NOTE:** Neither Click nor Typer has native async command support. The pattern used in the existing agent-team (wrapping async functions with `asyncio.run()` inside synchronous CLI commands) applies to both frameworks.

---

## 3. Rich Terminal UI

**Install:** `pip install rich` (included with `typer[all]`)
**Source:** Context7 `/textualize/rich` (423 code snippets, High reputation, Score 89.8)

### 3.1 Console + Panels for Phase Display

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# Phase status panel
def show_pipeline_status(state: str, phase_costs: dict[str, float]):
    table = Table(title="Pipeline Status")
    table.add_column("Phase", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Cost", justify="right", style="green")

    phases = [
        ("Architect", "architect_running"),
        ("Contracts", "contracts_registering"),
        ("Builders", "builders_running"),
        ("Integration", "integrating"),
        ("Quality Gate", "quality_gate"),
    ]

    for label, phase_key in phases:
        if phase_key == state:
            status = "[bold yellow]RUNNING[/]"
        elif phase_costs.get(phase_key, 0) > 0:
            status = "[bold green]DONE[/]"
        else:
            status = "[dim]PENDING[/]"
        cost = f"${phase_costs.get(phase_key, 0):.2f}"
        table.add_row(label, status, cost)

    console.print(Panel(table, title="Super Orchestrator", border_style="blue"))
```

### 3.2 Progress Bars for Build Phases

```python
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, TaskProgressColumn, TimeRemainingColumn,
)

# Multi-system builder progress
with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeRemainingColumn(),
) as progress:
    sys3 = progress.add_task("[cyan]System 3 (Frontend)", total=100)
    sys4 = progress.add_task("[green]System 4 (Backend)", total=100)
    sys5 = progress.add_task("[magenta]System 5 (Infra)", total=100)

    # Update as builders report progress
    progress.update(sys3, advance=10)
    progress.update(sys4, advance=15)
```

### 3.3 Live Display for Real-Time State

```python
from rich.live import Live
from rich.layout import Layout

def create_dashboard(state, costs, builders):
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"State: {state}", title="Pipeline"), name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(Panel(create_cost_table(costs)), name="costs"),
        Layout(Panel(create_builder_table(builders)), name="builders"),
    )
    return layout

# Live updating dashboard
with Live(create_dashboard(state, costs, builders), refresh_per_second=2) as live:
    while not orchestrator.is_terminal:
        live.update(create_dashboard(orchestrator.state, costs, builders))
        await asyncio.sleep(0.5)
```

### 3.4 Status Spinners for Long Operations

```python
from rich.console import Console

console = Console()

with console.status("[bold green]Running Architect (System 1)...") as status:
    cost = await run_architect()
    status.update("[bold blue]Registering contracts...")
    await register_contracts()
    status.update("[bold yellow]Launching builders...")

# Status with logging (non-blocking)
with console.status("[bold green]Building systems...") as status:
    console.log("[System 3] Frontend build started")
    console.log("[System 4] Backend build started")
    console.log("[System 5] Infra build started")
    # ... wait for completion
    console.log("[green]All builders complete")
```

### 3.5 Tables for Quality Gate Results

```python
from rich.table import Table

def display_quality_results(results: dict):
    table = Table(title="Quality Gate Results")
    table.add_column("Check", style="cyan")
    table.add_column("Result", justify="center")
    table.add_column("Details")

    for check, result in results.items():
        icon = "[green]PASS[/]" if result["passed"] else "[red]FAIL[/]"
        table.add_row(check, icon, result.get("details", ""))

    console.print(table)
```

---

## 4. Async Orchestration Patterns

### 4.1 Async Subprocess Management

```python
import asyncio
from pathlib import Path

async def run_builder_subprocess(
    system_id: str,
    prd_path: Path,
    config_path: Path,
    timeout: int = 600,  # 10 minutes default
) -> tuple[int, str, str]:
    """Run a builder system as a subprocess with timeout.

    Returns (return_code, stdout, stderr).
    """
    proc = await asyncio.create_subprocess_exec(
        "python", "-m", "agent_team",
        "--prd", str(prd_path),
        "--config", str(config_path),
        "--depth", "thorough",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        return proc.returncode or 0, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"Timeout after {timeout}s"
```

### 4.2 Parallel Builders with Error Isolation

```python
import asyncio
from dataclasses import dataclass

@dataclass
class BuilderResult:
    system_id: str
    success: bool
    cost: float
    error: str = ""
    output_dir: str = ""

async def run_parallel_builders(
    builder_configs: list[dict],
    max_concurrent: int = 3,
) -> list[BuilderResult]:
    """Run multiple builders in parallel with concurrency limit.

    Uses a semaphore to limit concurrent processes.
    Failed builders do NOT cancel successful ones.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[BuilderResult] = []

    async def _run_one(config: dict) -> BuilderResult:
        async with semaphore:
            try:
                rc, stdout, stderr = await run_builder_subprocess(
                    system_id=config["system_id"],
                    prd_path=Path(config["prd_path"]),
                    config_path=Path(config["config_path"]),
                    timeout=config.get("timeout", 600),
                )
                return BuilderResult(
                    system_id=config["system_id"],
                    success=(rc == 0),
                    cost=_extract_cost(stdout),
                    error=stderr if rc != 0 else "",
                    output_dir=config.get("output_dir", ""),
                )
            except Exception as e:
                return BuilderResult(
                    system_id=config["system_id"],
                    success=False,
                    cost=0.0,
                    error=str(e),
                )

    # gather with return_exceptions=True so one failure doesn't cancel others
    tasks = [_run_one(cfg) for cfg in builder_configs]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)
```

### 4.3 Timeout Handling Per Phase

```python
# Phase timeout configuration
PHASE_TIMEOUTS: dict[str, int] = {
    "architect_running": 900,      # 15 minutes
    "architect_review": 300,       # 5 minutes
    "contracts_registering": 180,  # 3 minutes
    "builders_running": 1800,      # 30 minutes (parallel, longest builder)
    "integrating": 600,            # 10 minutes
    "quality_gate": 300,           # 5 minutes
    "fix_pass": 900,               # 15 minutes
}

async def run_phase_with_timeout(
    phase: str,
    coro: asyncio.coroutine,
    timeout_override: int | None = None,
) -> Any:
    """Run a phase coroutine with configurable timeout."""
    timeout = timeout_override or PHASE_TIMEOUTS.get(phase, 600)
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise PhaseTimeoutError(f"Phase {phase} timed out after {timeout}s")
```

### 4.4 Signal Handling for Graceful Shutdown

```python
import signal
import asyncio
from typing import Any

class GracefulShutdown:
    """Signal handler that saves state on interrupt."""

    def __init__(self):
        self._shutdown_requested = False
        self._interrupt_count = 0

    def install(self) -> None:
        """Install signal handlers. Must be called from main thread."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        self._interrupt_count += 1
        self._shutdown_requested = True

        if self._interrupt_count >= 2:
            # Force exit — save state first
            self._emergency_save()
            raise SystemExit(130)

        print("\nGraceful shutdown requested. Finishing current phase...")
        print("Press Ctrl+C again to force exit (state will be saved).")

    def _emergency_save(self) -> None:
        """Synchronous state save on double-interrupt."""
        # Direct JSON write, no async
        import json, tempfile, os
        state = self._get_current_state()
        if state:
            data = state.to_dict()
            fd, tmp = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, ".agent-team/STATE.json")

    @property
    def should_stop(self) -> bool:
        return self._shutdown_requested

# Usage in async loop
shutdown = GracefulShutdown()
shutdown.install()

async def pipeline_loop():
    while not orchestrator.is_terminal:
        if shutdown.should_stop:
            save_state(current_state)
            break
        await run_next_phase()
```

### 4.5 Process Pool Pattern for Builder Isolation

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def _run_builder_sync(system_id: str, prd_path: str, config_path: str) -> dict:
    """Synchronous builder entry point for process pool."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "agent_team", "--prd", prd_path, "--config", config_path],
        capture_output=True, text=True, timeout=1800,
    )
    return {
        "system_id": system_id,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

async def run_builders_in_pool(configs: list[dict], max_workers: int = 3):
    """Run builders in separate processes for full isolation."""
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            loop.run_in_executor(
                pool,
                _run_builder_sync,
                cfg["system_id"],
                cfg["prd_path"],
                cfg["config_path"],
            )
            for cfg in configs
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)
    return results
```

---

## 5. Cost Tracking

### 5.1 Claude API Pricing Model

```python
# Claude API pricing (as of 2025 — verify current rates)
PRICING = {
    "claude-opus-4": {
        "input_per_1k": 0.015,     # $15 per 1M input tokens
        "output_per_1k": 0.075,    # $75 per 1M output tokens
        "cache_read_per_1k": 0.00375,  # 75% discount on cached
    },
    "claude-sonnet-4": {
        "input_per_1k": 0.003,     # $3 per 1M input tokens
        "output_per_1k": 0.015,    # $15 per 1M output tokens
        "cache_read_per_1k": 0.00075,
    },
    "claude-haiku-4": {
        "input_per_1k": 0.0008,    # $0.80 per 1M input tokens
        "output_per_1k": 0.004,    # $4 per 1M output tokens
        "cache_read_per_1k": 0.0002,
    },
}
```

### 5.2 Per-Phase Cost Aggregation

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class PhaseCost:
    phase_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    start_time: str = ""
    end_time: str = ""
    sub_phases: dict[str, float] = field(default_factory=dict)

@dataclass
class PipelineCostTracker:
    """Tracks cost across all pipeline phases."""

    phases: dict[str, PhaseCost] = field(default_factory=dict)
    budget_limit: float | None = None

    @property
    def total_cost(self) -> float:
        return sum(p.cost_usd for p in self.phases.values())

    def add_phase_cost(self, phase: str, cost: float) -> None:
        if phase not in self.phases:
            self.phases[phase] = PhaseCost(
                phase_name=phase,
                start_time=datetime.now(timezone.utc).isoformat(),
            )
        self.phases[phase].cost_usd += cost
        self.phases[phase].end_time = datetime.now(timezone.utc).isoformat()

    def check_budget(self) -> tuple[bool, str]:
        """Returns (within_budget, message)."""
        if self.budget_limit is None:
            return True, ""
        total = self.total_cost
        if total >= self.budget_limit:
            return False, f"Budget exceeded: ${total:.2f} >= ${self.budget_limit:.2f}"
        if total >= self.budget_limit * 0.8:
            return True, f"Budget warning: ${total:.2f} of ${self.budget_limit:.2f} (80%+)"
        return True, ""

    def to_dict(self) -> dict:
        return {
            "total_cost_usd": self.total_cost,
            "budget_limit_usd": self.budget_limit,
            "phases": {
                name: {
                    "cost_usd": p.cost_usd,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                }
                for name, p in self.phases.items()
            },
        }
```

### 5.3 How Agent-Team Currently Tracks Cost

From `src/agent_team/cli.py`:

```python
# 1. ResultMessage carries total_cost_usd from the SDK
async for msg in client.receive_response():
    if isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            cost = msg.total_cost_usd
            phase_costs[current_phase] = phase_costs.get(current_phase, 0.0) + cost

# 2. Budget check after each response
if config.orchestrator.max_budget_usd is not None:
    cumulative = sum(phase_costs.values())
    budget = config.orchestrator.max_budget_usd
    if cumulative >= budget:
        print_warning(f"Budget limit reached: ${cumulative:.2f} >= ${budget:.2f}")

# 3. RunState.total_cost persists across phases
_current_state.total_cost = run_cost or 0.0
_current_state.total_cost += recovery_cost
_current_state.total_cost += e2e_cost
```

**Integration with Super Orchestrator:** The Super Orchestrator wraps each phase as a separate `agent-team` invocation. Each invocation returns its `total_cost` via RunState. The Super Orchestrator aggregates these into `PipelineCostTracker`.

---

## 6. State Persistence

### 6.1 Atomic File Write Pattern (from existing agent-team)

```python
import json
import os
import tempfile
from pathlib import Path

def atomic_write_json(data: dict, path: Path) -> None:
    """Write JSON atomically using tmp+rename pattern.

    Prevents corruption if the process is interrupted during write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)  # Atomic on same filesystem
    except Exception:
        import contextlib
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise
```

### 6.2 Super Orchestrator State Schema

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class PipelineState:
    """Persisted state for the Super Orchestrator pipeline."""

    # Identity
    pipeline_id: str = ""
    prd_path: str = ""
    config_path: str = ""
    depth: str = "standard"

    # State machine
    current_state: str = "init"
    previous_state: str = ""

    # Phase tracking
    completed_phases: list[str] = field(default_factory=list)
    phase_artifacts: dict[str, list[str]] = field(default_factory=dict)

    # Builder tracking
    builder_statuses: dict[str, str] = field(default_factory=dict)  # system_id -> status
    builder_costs: dict[str, float] = field(default_factory=dict)   # system_id -> cost

    # Quality gate
    quality_attempts: int = 0
    max_quality_retries: int = 3
    last_quality_results: dict[str, bool] = field(default_factory=dict)

    # Cost
    total_cost: float = 0.0
    phase_costs: dict[str, float] = field(default_factory=dict)
    budget_limit: float | None = None

    # Timing
    started_at: str = ""
    updated_at: str = ""

    # Interruption
    interrupted: bool = False
    interrupt_reason: str = ""

    # Schema version for forward compatibility
    schema_version: int = 1

    def save(self, directory: str = ".super-orchestrator") -> Path:
        """Save state atomically."""
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.interrupted = True
        path = Path(directory) / "PIPELINE_STATE.json"
        atomic_write_json(asdict(self), path)
        return path

    @classmethod
    def load(cls, directory: str = ".super-orchestrator") -> "PipelineState | None":
        """Load state from disk. Returns None if not found."""
        path = Path(directory) / "PIPELINE_STATE.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items()
                          if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    @classmethod
    def clear(cls, directory: str = ".super-orchestrator") -> None:
        """Delete state file after successful completion."""
        import contextlib
        path = Path(directory) / "PIPELINE_STATE.json"
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
```

### 6.3 State Recovery on Restart

```python
def resume_pipeline(state: PipelineState) -> str:
    """Determine which phase to resume from.

    Returns the state machine trigger to invoke.
    """
    # Map current_state to the trigger that enters it
    RESUME_TRIGGERS = {
        "init": "start_architect",
        "architect_running": "start_architect",      # Re-run architect
        "architect_review": "approve_architecture",   # Re-review
        "contracts_registering": "contracts_ready",   # Re-register
        "builders_running": "start_builders",          # Re-run failed builders only
        "builders_complete": "start_integration",
        "integrating": "start_integration",            # Re-run integration
        "quality_gate": "run_quality_check",
        "fix_pass": "start_fix",
    }

    trigger = RESUME_TRIGGERS.get(state.current_state)
    if not trigger:
        return "fail"  # Unknown state — cannot resume
    return trigger

def validate_state_for_resume(state: PipelineState) -> list[str]:
    """Validate saved state for resume. Returns warning messages."""
    issues = []

    if not state.prd_path or not Path(state.prd_path).exists():
        issues.append("ERROR: PRD file not found at saved path")

    if state.updated_at:
        from datetime import datetime, timezone
        try:
            saved = datetime.fromisoformat(state.updated_at)
            age_h = (datetime.now(timezone.utc) - saved).total_seconds() / 3600
            if age_h > 24:
                issues.append(f"WARNING: State is {int(age_h)}h old")
        except ValueError:
            pass

    # Check if builder outputs still exist
    for system_id, status in state.builder_statuses.items():
        if status == "complete":
            output_dir = state.phase_artifacts.get(f"builder_{system_id}", [])
            if output_dir and not Path(output_dir[0]).exists():
                issues.append(f"WARNING: Builder {system_id} output missing")

    return issues
```

---

## 7. Existing Agent-Team Patterns (Integration Reference)

### 7.1 RunState — Current State Persistence

From `src/agent_team/state.py`:

```python
@dataclass
class RunState:
    run_id: str = ""               # UUID hex[:12]
    task: str = ""                  # Task description
    depth: str = "standard"        # Depth level
    current_phase: str = "init"    # Current phase name
    completed_phases: list[str]    # Completed phases
    total_cost: float = 0.0        # Cumulative cost in USD
    artifacts: dict[str, str]      # name -> path mapping
    interrupted: bool = False       # Was this run interrupted?
    timestamp: str = ""             # ISO timestamp
    schema_version: int = 2         # Forward compatibility

    # Milestone tracking (v2)
    current_milestone: str = ""
    completed_milestones: list[str]
    failed_milestones: list[str]
    milestone_order: list[str]
    completion_ratio: float = 0.0

# Key functions:
save_state(state, directory=".agent-team")  # Atomic JSON write
load_state(directory=".agent-team")          # Returns RunState | None
clear_state(directory=".agent-team")         # Delete on success
validate_for_resume(state) -> list[str]      # Warning messages
is_stale(state, current_task) -> bool        # Different task?
```

### 7.2 Signal Handling Pattern (from cli.py)

```python
# Module-level globals (safe in CPython — GIL + main thread)
_interrupt_count = 0
_current_state = None

def _handle_interrupt(signum, frame):
    global _interrupt_count
    _interrupt_count += 1
    if _interrupt_count >= 2:
        save_state(_current_state)
        sys.exit(130)
    print("Press Ctrl+C again to save state and exit.")

signal.signal(signal.SIGINT, _handle_interrupt)
```

### 7.3 Async Process Pattern (from cli.py)

```python
# All async functions are called via asyncio.run() from sync CLI
run_cost = asyncio.run(_run_single(config, cwd, ...))

# Sub-orchestrator pattern (reusable for Super Orchestrator phases)
async def _run_review_only(cwd, config, requirements_path, depth) -> float:
    client = ClaudeSDKClient(options)
    await client.query(prompt)
    cost = await _process_response(client, config, phase_costs)
    return cost
```

### 7.4 Cost Tracking Pattern (from cli.py)

```python
# Phase-level: dict[str, float] aggregated per response
phase_costs: dict[str, float] = {}

# Response processing extracts cost from ResultMessage
async for msg in client.receive_response():
    if isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            cost = msg.total_cost_usd
            phase_costs[current_phase] += cost

# Global state accumulation
_current_state.total_cost = run_cost or 0.0
_current_state.total_cost += recovery_cost
```

### 7.5 Config Loading Pattern (from config.py)

```python
# YAML config loading with validation
config, user_overrides = load_config(config_path)

# Depth-based gating modifies config in-place
apply_depth_quality_gating(depth, config, user_overrides, prd_mode=True)

# Key: load_config returns tuple[AgentTeamConfig, set[str]]
# user_overrides tracks explicitly set keys (never overridden by depth gating)
```

---

## 8. Recommendations

### 8.1 Technology Stack for Super Orchestrator

| Component              | Library              | Rationale                                          |
|------------------------|----------------------|----------------------------------------------------|
| **State Machine**      | `transitions` 0.9+   | Declarative FSM, AsyncMachine, guard conditions    |
| **CLI Framework**      | `typer` 0.21+        | Type-safe, Rich integration, Pythonic              |
| **Terminal UI**         | `rich` 13+           | Progress bars, tables, panels, live display        |
| **Async Runtime**      | `asyncio` (stdlib)   | Already used by agent-team, no new deps            |
| **Config Loading**     | `pyyaml` (existing)  | Consistent with agent-team config pattern          |
| **State Persistence**  | `json` + atomic write| Match agent-team pattern (tmp+rename)              |

### 8.2 Dependencies (requirements.txt additions)

```
transitions>=0.9.2
typer[all]>=0.21.0
# rich is included via typer[all]
# pyyaml already in agent-team deps
```

### 8.3 Architecture Skeleton

```python
# super_orchestrator/
#   __init__.py
#   cli.py          # Typer app with 6 commands
#   state_machine.py # AsyncMachine + OrchestratorState + transitions
#   pipeline.py     # Phase execution (async functions)
#   state.py        # PipelineState persistence
#   cost.py         # PipelineCostTracker
#   display.py      # Rich console, tables, progress
#   config.py       # SuperOrchestratorConfig (extends AgentTeamConfig)

# Entry point (pyproject.toml):
# [project.scripts]
# super-orchestrator = "super_orchestrator.cli:app"
```

### 8.4 State Machine + CLI Integration Pattern

```python
# cli.py
import typer
from .state_machine import create_pipeline_machine
from .state import PipelineState
from .cost import PipelineCostTracker

app = typer.Typer()

@app.command()
def run(prd_path: Path, resume: bool = False):
    """Run full pipeline."""
    if resume:
        state = PipelineState.load()
        if not state:
            raise typer.Exit(code=1)
    else:
        state = PipelineState(prd_path=str(prd_path))

    orchestrator = create_pipeline_machine(state)
    tracker = PipelineCostTracker(budget_limit=config.budget)

    asyncio.run(_execute_pipeline(orchestrator, state, tracker))

# state_machine.py
from transitions.extensions.asyncio import AsyncMachine

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

### 8.5 Key Integration Points with Existing Agent-Team

1. **Each phase invokes `agent-team` as a sub-process** — the Super Orchestrator does NOT import agent-team internals. This ensures isolation and allows different agent-team versions per system.

2. **State file location:** `.super-orchestrator/PIPELINE_STATE.json` (separate from `.agent-team/STATE.json`)

3. **Cost aggregation:** Each agent-team run writes its cost to RunState. The Super Orchestrator reads this after each subprocess completes and aggregates into PipelineCostTracker.

4. **Config inheritance:** The Super Orchestrator config extends AgentTeamConfig with pipeline-specific fields (phase timeouts, builder parallelism, quality gate retries). Each builder receives a scoped config.

5. **Resume compatibility:** The Super Orchestrator resume reads `PIPELINE_STATE.json` and determines which phase to re-enter. Individual agent-team runs within each phase use their own `.agent-team/STATE.json` for fine-grained resume.

---

## Sources

- [pytransitions/transitions on GitHub](https://github.com/pytransitions/transitions)
- [transitions on PyPI](https://pypi.org/project/transitions/)
- [Click documentation (Context7 /pallets/click)](https://click.palletsprojects.com/)
- [Typer documentation (Context7 /fastapi/typer)](https://typer.tiangolo.com/)
- [Rich documentation (Context7 /textualize/rich)](https://rich.readthedocs.io/)
- [python-statemachine on PyPI](https://pypi.org/project/python-statemachine/)
- Existing agent-team source: `src/agent_team/state.py`, `src/agent_team/config.py`, `src/agent_team/cli.py`
