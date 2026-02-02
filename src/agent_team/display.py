"""Rich terminal output for Agent Team.

Provides formatted banners, convergence status, fleet composition,
review results, and cost tables.
"""

from __future__ import annotations

import os
import sys

# Force UTF-8 on Windows so Rich can render box-drawing characters
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console(force_terminal=sys.stdout.isatty())


# ---------------------------------------------------------------------------
# Banners & headers
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Print the Agent Team startup banner."""
    banner = Text()
    banner.append("AGENT TEAM", style="bold cyan")
    banner.append(" - Convergence-Driven Multi-Agent Orchestration", style="dim")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def print_task_start(task: str, depth: str, agent_count: int | None = None) -> None:
    """Print task initialization info."""
    console.print()
    console.print(f"[bold white]Task:[/] {task[:120]}{'...' if len(task) > 120 else ''}")
    console.print(f"[bold white]Depth:[/] [bold yellow]{depth.upper()}[/]")
    if agent_count:
        console.print(f"[bold white]Agent Count:[/] [bold yellow]{agent_count}[/] (user-specified)")
    console.print()


def print_prd_mode(prd_path: str) -> None:
    """Print PRD mode activation."""
    console.print(Panel(
        f"[bold magenta]PRD MODE ACTIVE[/]\nSource: {prd_path}",
        border_style="magenta",
        title="Full Application Build",
    ))


# ---------------------------------------------------------------------------
# Fleet deployment
# ---------------------------------------------------------------------------

def print_fleet_deployment(
    phase: str,
    agent_type: str,
    count: int,
    assignments: list[str] | None = None,
) -> None:
    """Print a fleet deployment banner.

    Prompt-invoked: called by the orchestrator agent during fleet
    deployment, not directly from Python runtime code.
    """
    header = Text()
    header.append(f"Deploying {phase.upper()} Fleet", style="bold green")
    header.append(f"  [{count} x {agent_type}]", style="dim green")

    console.print()
    console.print(f"[green]{'=' * 60}[/]")
    console.print(header)
    if assignments:
        for i, assignment in enumerate(assignments, 1):
            console.print(f"  [dim]{agent_type}-{i}:[/] {assignment}")
    console.print(f"[green]{'=' * 60}[/]")


# ---------------------------------------------------------------------------
# Convergence status
# ---------------------------------------------------------------------------

def print_convergence_status(
    cycle: int,
    total_items: int,
    completed_items: int,
    remaining_items: list[str] | None = None,
    escalated_items: list[str] | None = None,
) -> None:
    """Print convergence loop status after a review cycle.

    Prompt-invoked: called by the orchestrator agent during convergence
    loops, not directly from Python runtime code.
    """
    pct = (completed_items / total_items * 100) if total_items > 0 else 0
    bar_filled = int(pct / 5)
    bar_empty = 20 - bar_filled
    bar = f"[green]{'#' * bar_filled}[/][dim]{'.' * bar_empty}[/]"

    console.print()
    console.print(f"[bold cyan]=== Convergence Cycle {cycle} ===[/]")
    console.print(f"  Checklist: {bar} {completed_items}/{total_items} ({pct:.0f}%)")

    if remaining_items:
        items_str = ", ".join(remaining_items[:8])
        if len(remaining_items) > 8:
            items_str += f", ... (+{len(remaining_items) - 8} more)"
        console.print(f"  [yellow]Remaining:[/] {items_str}")

    if escalated_items:
        esc_str = ", ".join(escalated_items)
        console.print(f"  [red]Escalated:[/] {esc_str}")

    if completed_items == total_items:
        console.print(f"  [bold green]ALL ITEMS COMPLETE[/]")
    else:
        console.print(f"  [dim]Deploying next fleet for {total_items - completed_items} failing items...[/]")


# ---------------------------------------------------------------------------
# Review results
# ---------------------------------------------------------------------------

def print_review_results(
    passed: list[str],
    failed: list[tuple[str, str]],
) -> None:
    """Print review results summary.

    Prompt-invoked: called by the orchestrator agent after review
    cycles, not directly from Python runtime code.
    """
    table = Table(title="Review Results", show_lines=False, border_style="dim")
    table.add_column("Item", style="white")
    table.add_column("Verdict", style="bold")
    table.add_column("Issues", style="dim")

    for item in passed:
        table.add_row(item, "[green]PASS[/]", "-")

    for item, issues in failed:
        table.add_row(item, "[red]FAIL[/]", issues[:80])

    console.print(table)


# ---------------------------------------------------------------------------
# Completion & cost
# ---------------------------------------------------------------------------

def print_completion(task: str, total_cycles: int, total_cost: float | None) -> None:
    """Print task completion summary."""
    content = Text()
    content.append("TASK COMPLETE\n\n", style="bold green")
    content.append(f"Task: {task[:100]}\n", style="white")
    content.append(f"Convergence cycles: {total_cycles}\n", style="white")
    if total_cost is not None:
        content.append(f"Total cost: ${total_cost:.4f}\n", style="white")

    console.print()
    console.print(Panel(content, border_style="green", title="Complete"))


def print_cost_summary(phase_costs: dict[str, float]) -> None:
    """Print a cost breakdown table."""
    if not phase_costs:
        return

    table = Table(title="Cost Breakdown", border_style="dim")
    table.add_column("Phase", style="white")
    table.add_column("Cost (USD)", style="yellow", justify="right")

    total = 0.0
    for phase, cost in phase_costs.items():
        table.add_row(phase, f"${cost:.4f}")
        total += cost

    table.add_row("[bold]Total[/]", f"[bold]${total:.4f}[/]", style="bold")
    console.print(table)


# ---------------------------------------------------------------------------
# Errors & warnings
# ---------------------------------------------------------------------------

def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]Error:[/] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]{message}[/]")


def print_escalation(item: str, reason: str) -> None:
    """Print an escalation notice.

    Prompt-invoked: called by the orchestrator agent when escalation
    is triggered, not directly from Python runtime code.
    """
    console.print()
    console.print(Panel(
        f"[bold red]ESCALATION TRIGGERED[/]\n\n"
        f"Item: {item}\n"
        f"Reason: {reason}\n\n"
        f"Sending back to Planning + Research fleet for re-analysis...",
        border_style="red",
        title="Escalation",
    ))


def print_user_intervention_needed(item: str) -> None:
    """Print when max escalation depth is exceeded and user input is needed.

    Prompt-invoked: called by the orchestrator agent when human
    intervention is required, not directly from Python runtime code.
    """
    console.print()
    console.print(Panel(
        f"[bold red]HUMAN INTERVENTION REQUIRED[/]\n\n"
        f"Item: {item}\n"
        f"This item has exceeded the maximum escalation depth.\n"
        f"The system needs your guidance to proceed.",
        border_style="red",
        title="Intervention Required",
    ))


# ---------------------------------------------------------------------------
# Interview phase
# ---------------------------------------------------------------------------

def print_interview_start(initial_task: str | None = None, min_exchanges: int | None = None) -> None:
    """Print the interview phase startup banner."""
    content = Text()
    content.append("INTERVIEW PHASE\n\n", style="bold magenta")
    content.append(
        "The interviewer will discuss your requirements before the agents begin.\n",
        style="white",
    )
    content.append(
        'Say "I\'m done", "let\'s go", or "start building" when ready to proceed.\n',
        style="dim",
    )
    if min_exchanges is not None:
        content.append(
            f"Minimum exchanges: {min_exchanges} (the interviewer will explore before accepting finalization)\n",
            style="dim yellow",
        )
    if initial_task:
        content.append(f"\nSeeded with: {initial_task[:120]}", style="dim cyan")
    console.print()
    console.print(Panel(content, border_style="magenta", title="Phase 0"))


def print_interview_prompt() -> str:
    """Print the interview prompt and return user input."""
    console.print()
    try:
        return console.input("[bold magenta]you>[/] ")
    except (EOFError, KeyboardInterrupt):
        return ""


def print_interview_end(exchange_count: int, scope: str, doc_path: str) -> None:
    """Print interview completion summary."""
    content = Text()
    content.append("INTERVIEW COMPLETE\n\n", style="bold green")
    content.append(f"Exchanges: {exchange_count}\n", style="white")
    content.append(f"Detected scope: {scope.upper()}\n", style="white")
    content.append(f"Document saved: {doc_path}\n", style="dim")
    console.print()
    console.print(Panel(content, border_style="green", title="Interview Done"))


def print_interview_skip(reason: str) -> None:
    """Print when the interview phase is skipped."""
    console.print(f"[dim]Interview skipped: {reason}[/]")
    console.print()


def print_interview_min_not_reached(exchange_count: int, min_exchanges: int) -> None:
    """Print when user tries to exit before minimum exchanges."""
    console.print(
        f"[yellow]Interview at {exchange_count} of {min_exchanges} minimum exchanges. "
        f"The interviewer will continue exploring before finalizing.[/]"
    )


def print_interview_pending_exit() -> None:
    """Print when interview is in pending exit confirmation state."""
    console.print(
        "[dim]The interviewer is preparing a final summary. "
        "Say 'yes' to confirm and finalize, or continue the conversation.[/]"
    )


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def print_interactive_prompt() -> str:
    """Print the interactive mode prompt and return user input."""
    console.print()
    try:
        return console.input("[bold cyan]agent-team>[/] ")
    except (EOFError, KeyboardInterrupt):
        return ""


def print_agent_response(text: str) -> None:
    """Print an agent's text response."""
    console.print(text)


# ---------------------------------------------------------------------------
# Codebase map phase
# ---------------------------------------------------------------------------

def print_map_start(cwd: str) -> None:
    """Print codebase map analysis start."""
    console.print(Panel(
        f"[bold blue]Analyzing project structure...[/]\n"
        f"[dim]Directory: {cwd}[/]",
        border_style="blue",
        title="Phase 0.5: Codebase Map",
    ))


def print_map_complete(file_count: int, language: str) -> None:
    """Print codebase map analysis completion."""
    console.print(
        f"[green]Codebase map complete:[/] "
        f"[bold]{file_count}[/] files, "
        f"primary language: [bold]{language}[/]"
    )
    console.print()


# ---------------------------------------------------------------------------
# Depth detection & intervention
# ---------------------------------------------------------------------------

def print_depth_detection(detection: object) -> None:
    """Show why a particular depth level was chosen.

    Args:
        detection: A DepthDetection-like object with .level, .source,
                   .matched_keywords, and .explanation attributes.
    """
    if detection is None:
        return
    level = getattr(detection, "level", str(detection))
    source = getattr(detection, "source", "unknown")
    keywords = getattr(detection, "matched_keywords", [])
    explanation = getattr(detection, "explanation", "")

    parts = [f"[bold white]Depth:[/] [bold yellow]{level.upper()}[/]"]
    if source == "keyword" and keywords:
        parts.append(f"  [dim]Matched: {', '.join(keywords)}[/]")
    elif source == "default":
        parts.append(f"  [dim]No keyword match — using default[/]")
    if explanation:
        parts.append(f"  [dim]{explanation}[/]")
    for part in parts:
        console.print(part)


def print_intervention_hint() -> None:
    """Print a hint about mid-run intervention capability."""
    console.print(
        "[dim]Tip: Type !! followed by your message to intervene during orchestration[/]"
    )


# ---------------------------------------------------------------------------
# Scheduler phase
# ---------------------------------------------------------------------------

def print_schedule_summary(waves: int, conflicts: int) -> None:
    """Print task schedule summary."""
    content = Text()
    content.append("SCHEDULE COMPUTED\n\n", style="bold cyan")
    content.append(f"Execution waves: {waves}\n", style="white")
    content.append(f"File conflicts resolved: {conflicts}\n", style="white")
    console.print(Panel(content, border_style="cyan", title="Smart Scheduler"))


def print_wave_start(wave_num: int, task_count: int) -> None:
    """Print wave execution start."""
    console.print()
    console.print(
        f"[bold cyan]=== Wave {wave_num} ===[/] "
        f"[dim]({task_count} tasks in parallel)[/]"
    )


def print_wave_complete(wave_num: int) -> None:
    """Print wave execution completion."""
    console.print(f"[green]Wave {wave_num} complete.[/]")


# ---------------------------------------------------------------------------
# Verification phase
# ---------------------------------------------------------------------------

def print_verification_result(task_id: str, status: str) -> None:
    """Print a single task's verification result."""
    style_map = {
        "pass": "bold green",
        "fail": "bold red",
        "partial": "bold yellow",
    }
    style = style_map.get(status, "white")
    console.print(f"  [{style}]{status.upper()}[/] {task_id}")


def print_verification_summary(state: dict) -> None:
    """Print the overall verification summary.

    Args:
        state: Dict with keys 'overall_health', 'completed_tasks' (dict of task_id -> status)
    """
    health = state.get("overall_health", "unknown")
    health_styles = {
        "green": "bold green",
        "yellow": "bold yellow",
        "red": "bold red",
    }
    style = health_styles.get(health, "white")

    completed = state.get("completed_tasks", {})
    pass_count = sum(1 for v in completed.values() if v == "pass")
    fail_count = sum(1 for v in completed.values() if v == "fail")
    total = len(completed)

    content = Text()
    content.append("VERIFICATION SUMMARY\n\n", style="bold white")
    content.append(f"Overall health: ", style="white")
    content.append(f"{health.upper()}\n", style=style)
    content.append(f"Tasks verified: {total}\n", style="white")
    content.append(f"Passed: {pass_count}  ", style="green")
    content.append(f"Failed: {fail_count}\n", style="red" if fail_count > 0 else "dim")

    console.print(Panel(content, border_style=health if health in health_styles else "white",
                        title="Progressive Verification"))


def print_contract_violation(violation: str) -> None:
    """Print a contract violation."""
    console.print(f"  [red]VIOLATION:[/] {violation}")


# ---------------------------------------------------------------------------
# Run summary
# ---------------------------------------------------------------------------

def print_run_summary(summary) -> None:
    """Print a comprehensive run summary.

    Args:
        summary: A RunSummary-like object with task, depth, total_cost,
                 cycle_count, requirements_passed, requirements_total,
                 and files_changed attributes.
    """
    task = getattr(summary, "task", "")
    depth = getattr(summary, "depth", "standard")
    total_cost = getattr(summary, "total_cost", 0.0)
    cycle_count = getattr(summary, "cycle_count", 0)
    req_passed = getattr(summary, "requirements_passed", 0)
    req_total = getattr(summary, "requirements_total", 0)
    files_changed = getattr(summary, "files_changed", [])

    content = Text()
    content.append("RUN SUMMARY\n\n", style="bold green")
    content.append(f"Task: {task[:100]}\n", style="white")
    content.append(f"Depth: {depth.upper()}\n", style="white")
    content.append(f"Convergence cycles: {cycle_count}\n", style="white")
    if req_total > 0:
        pct = req_passed / req_total * 100
        content.append(f"Requirements: {req_passed}/{req_total} ({pct:.0f}%)\n", style="white")
    if total_cost > 0:
        content.append(f"Total cost: ${total_cost:.4f}\n", style="white")
    if files_changed:
        content.append(f"Files changed: {len(files_changed)}\n", style="white")
        for f in files_changed[:10]:
            content.append(f"  {f}\n", style="dim")
        if len(files_changed) > 10:
            content.append(f"  ... and {len(files_changed) - 10} more\n", style="dim")

    console.print()
    console.print(Panel(content, border_style="green", title="Summary"))