"""CLI entry point for Agent Team.

Handles argument parsing, depth detection, interactive/single-shot modes,
signal handling, and cost tracking.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import queue
import re
import signal
import string
import sys
import threading
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from . import __version__
from .agents import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    build_agent_definitions,
    build_orchestrator_prompt,
)
from .config import AgentTeamConfig, detect_depth, extract_constraints, load_config, parse_max_review_cycles
from .display import (
    console,
    print_agent_response,
    print_banner,
    print_completion,
    print_contract_violation,
    print_cost_summary,
    print_depth_detection,
    print_error,
    print_info,
    print_interactive_prompt,
    print_interview_skip,
    print_map_complete,
    print_map_start,
    print_prd_mode,
    print_run_summary,
    print_schedule_summary,
    print_task_start,
    print_verification_summary,
    print_warning,
)
from .interviewer import _detect_scope, run_interview
from .mcp_servers import get_mcp_servers


# ---------------------------------------------------------------------------
# Intervention queue for background stdin reading
# ---------------------------------------------------------------------------

class InterventionQueue:
    """Background stdin reader that queues messages prefixed with '!!'."""

    _PREFIX = "!!"

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._active = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start background thread if stdin is a TTY."""
        if not sys.stdin.isatty():
            return
        self._active = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background thread."""
        self._active = False

    def has_intervention(self) -> bool:
        """Check if there's a pending intervention."""
        return not self._queue.empty()

    def get_intervention(self) -> str | None:
        """Get the next intervention message, or None."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _reader(self) -> None:
        """Background reader thread."""
        while self._active:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith(self._PREFIX):
                    self._queue.put(line[len(self._PREFIX):].strip())
            except (EOFError, OSError):
                break


# ---------------------------------------------------------------------------
# Agent count parsing
# ---------------------------------------------------------------------------

_AGENT_COUNT_RE = re.compile(
    r"(?:use|deploy|with|launch)\s+(\d+)\s+agents?",
    re.IGNORECASE,
)


def _detect_agent_count(task: str, cli_count: int | None) -> int | None:
    """Detect user-specified agent count from CLI flag or task text."""
    if cli_count is not None:
        return cli_count
    match = _AGENT_COUNT_RE.search(task)
    if match:
        return int(match.group(1))
    return None


def _validate_url(url: str) -> str:
    """Validate a URL has scheme and netloc. Raises argparse.ArgumentTypeError."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise argparse.ArgumentTypeError(
            f"Invalid URL: {url!r} — must include scheme (https://) and host"
        )
    return url


# ---------------------------------------------------------------------------
# PRD detection
# ---------------------------------------------------------------------------

def _detect_prd_from_task(task: str) -> bool:
    """Heuristic: does the task look like a full PRD?"""
    prd_signals = [
        "features", "user stories", "user story", "acceptance criteria",
        "product requirements", "prd", "build this app", "build an app",
        "full application", "entire application",
    ]
    task_lower = task.lower()
    signal_count = sum(1 for s in prd_signals if s in task_lower)
    # PRD-like if multiple signals or very long task
    return signal_count >= 2 or len(task) > 3000


# ---------------------------------------------------------------------------
# Build ClaudeAgentOptions
# ---------------------------------------------------------------------------

def _build_options(
    config: AgentTeamConfig,
    cwd: str | None = None,
    constraints: list | None = None,
) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with all agents and MCP servers."""
    mcp_servers = get_mcp_servers(config)
    agent_defs_raw = build_agent_definitions(config, mcp_servers, constraints=constraints)

    # Convert raw dicts to AgentDefinition objects
    agent_defs = {
        name: AgentDefinition(**defn)
        for name, defn in agent_defs_raw.items()
    }

    # Inject runtime values into orchestrator system prompt.
    # Security note: safe_substitute is used (not substitute) so unknown
    # $-references are left untouched rather than raising.  The values are
    # int-typed config fields converted to str -- no user-controlled template
    # syntax can reach here because yaml.safe_load produces Python ints, not
    # arbitrary strings containing $ placeholders.
    system_prompt = string.Template(ORCHESTRATOR_SYSTEM_PROMPT).safe_substitute(
        escalation_threshold=str(config.convergence.escalation_threshold),
        max_escalation_depth=str(config.convergence.max_escalation_depth),
        show_fleet_composition=str(config.display.show_fleet_composition),
        show_convergence_status=str(config.display.show_convergence_status),
        max_cycles=str(config.convergence.max_cycles),
        master_plan_file=config.convergence.master_plan_file,
        max_budget_usd=str(config.orchestrator.max_budget_usd),
    )

    opts_kwargs: dict[str, Any] = {
        "model": config.orchestrator.model,
        "system_prompt": system_prompt,
        "permission_mode": config.orchestrator.permission_mode,
        "max_turns": config.orchestrator.max_turns,
        "agents": agent_defs,
        "allowed_tools": [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
            "Task", "WebSearch", "WebFetch",
        ],
    }

    if mcp_servers:
        opts_kwargs["mcp_servers"] = mcp_servers

    if cwd:
        opts_kwargs["cwd"] = Path(cwd)

    return ClaudeAgentOptions(**opts_kwargs)


# ---------------------------------------------------------------------------
# Response processing
# ---------------------------------------------------------------------------

async def _process_response(
    client: ClaudeSDKClient,
    config: AgentTeamConfig,
    phase_costs: dict[str, float],
    current_phase: str = "orchestration",
) -> float:
    """Process streaming response from the SDK client. Returns cost for this query."""
    cost = 0.0
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print_agent_response(block.text)
                elif isinstance(block, ToolUseBlock):
                    if config.display.verbose or config.display.show_tools:
                        print_info(f"[tool] {block.name}")
        elif isinstance(msg, ResultMessage):
            if msg.total_cost_usd:
                cost = msg.total_cost_usd
                phase_costs[current_phase] = phase_costs.get(current_phase, 0.0) + cost

    # Budget warning check
    if config.orchestrator.max_budget_usd is not None:
        cumulative = sum(phase_costs.values())
        budget = config.orchestrator.max_budget_usd
        if cumulative >= budget:
            print_warning(f"Budget limit reached: ${cumulative:.2f} >= ${budget:.2f}")
        elif cumulative >= budget * 0.8:
            print_warning(f"Budget warning: ${cumulative:.2f} of ${budget:.2f} used (80%+)")

    return cost


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

async def _run_interactive(
    config: AgentTeamConfig,
    cwd: str | None,
    depth_override: str | None,
    agent_count_override: int | None,
    prd_path: str | None,
    interview_doc: str | None = None,
    interview_scope: str | None = None,
    design_reference_urls: list[str] | None = None,
    codebase_map_summary: str | None = None,
    constraints: list | None = None,
) -> float:
    """Run the interactive multi-turn conversation loop. Returns total cost."""
    options = _build_options(config, cwd, constraints=constraints)
    phase_costs: dict[str, float] = {}
    total_cost = 0.0
    last_depth = depth_override or "standard"

    async with ClaudeSDKClient(options=options) as client:
        # If a PRD or task was provided on the CLI, send it first
        if prd_path:
            print_prd_mode(prd_path)
            prd_content = Path(prd_path).read_text(encoding="utf-8")
            task = f"Build this application from the following PRD:\n\n{prd_content}"
            depth = depth_override or "exhaustive"
            last_depth = depth
            agent_count = agent_count_override
            prompt = build_orchestrator_prompt(
                task=task,
                depth=depth,
                config=config,
                prd_path=prd_path,
                agent_count=agent_count,
                cwd=cwd,
                interview_doc=interview_doc,
                interview_scope=interview_scope,
                design_reference_urls=design_reference_urls,
                codebase_map_summary=codebase_map_summary,
                constraints=constraints,
            )
            print_task_start(task[:200], depth, agent_count)
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs)
            total_cost += cost

        # Interactive loop
        while True:
            user_input = print_interactive_prompt()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                break

            if depth_override:
                depth = depth_override
            else:
                detection = detect_depth(user_input, config)
                depth = detection.level
                print_depth_detection(detection)
            last_depth = depth
            agent_count = _detect_agent_count(user_input, agent_count_override)
            is_prd = _detect_prd_from_task(user_input)

            # I4 fix: inline PRD detection forces exhaustive depth
            if is_prd and not depth_override:
                depth = "exhaustive"
                last_depth = depth

            prompt = build_orchestrator_prompt(
                task=user_input,
                depth=depth,
                config=config,
                prd_path="inline" if is_prd else None,
                agent_count=agent_count,
                cwd=cwd,
                interview_doc=interview_doc,
                interview_scope=interview_scope,
                design_reference_urls=design_reference_urls,
                codebase_map_summary=codebase_map_summary,
                constraints=constraints,
            )
            # Clear interview doc after first query -- the orchestrator has
            # already received it. Re-injecting on every interactive query
            # would waste context and could cause confusion.
            interview_doc = None

            if is_prd:
                print_prd_mode("inline")

            print_task_start(user_input, depth, agent_count)
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs)
            total_cost += cost

    if config.display.show_cost and total_cost > 0:
        print_cost_summary(phase_costs)

    # Run summary (always shown, not gated behind show_cost)
    from .state import RunSummary
    summary = RunSummary(task="(interactive session)", depth=last_depth, total_cost=total_cost)
    print_run_summary(summary)

    return total_cost


# ---------------------------------------------------------------------------
# Single-shot mode
# ---------------------------------------------------------------------------

async def _run_single(
    task: str,
    config: AgentTeamConfig,
    cwd: str | None,
    depth: str,
    agent_count: int | None,
    prd_path: str | None,
    interview_doc: str | None = None,
    interview_scope: str | None = None,
    design_reference_urls: list[str] | None = None,
    codebase_map_summary: str | None = None,
    constraints: list | None = None,
) -> float:
    """Run a single task to completion. Returns total cost."""
    options = _build_options(config, cwd, constraints=constraints)
    phase_costs: dict[str, float] = {}

    if prd_path:
        print_prd_mode(prd_path)
        prd_content = Path(prd_path).read_text(encoding="utf-8")
        task = f"Build this application from the following PRD:\n\n{prd_content}"

    prompt = build_orchestrator_prompt(
        task=task,
        depth=depth,
        config=config,
        prd_path=prd_path,
        agent_count=agent_count,
        cwd=cwd,
        interview_doc=interview_doc,
        interview_scope=interview_scope,
        design_reference_urls=design_reference_urls,
        codebase_map_summary=codebase_map_summary,
        constraints=constraints,
    )

    print_task_start(task, depth, agent_count)

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        total_cost = await _process_response(client, config, phase_costs)

    # Cost breakdown (gated behind show_cost)
    cycle_count = 0
    if config.display.show_cost:
        print_cost_summary(phase_costs)

    # Read REQUIREMENTS.md for actual cycle count (always, for RunSummary)
    req_path = Path(cwd or ".") / config.convergence.requirements_dir / config.convergence.requirements_file
    if req_path.exists():
        try:
            cycle_count = parse_max_review_cycles(req_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print_warning(f"Could not parse review cycles: {exc}")

    if config.display.show_cost:
        print_completion(task[:100], cycle_count, total_cost)

    # Run summary (always shown, not gated behind show_cost)
    from .state import RunSummary
    summary = RunSummary(task=task[:100], depth=depth, total_cost=total_cost, cycle_count=cycle_count)
    print_run_summary(summary)

    return total_cost


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

# Note: _interrupt_count is a module-level global accessed from the signal
# handler. This is safe because signal handlers in CPython run in the main
# thread (GIL protects single-threaded integer increment).  The asyncio
# event loop also runs in the main thread, so there is no concurrent
# modification from other threads.
_interrupt_count = 0
_current_state = None  # Module-level for state saving


def _handle_interrupt(signum: int, frame: Any) -> None:
    """Handle Ctrl+C: first press warns, second saves state and exits."""
    global _interrupt_count, _current_state
    _interrupt_count += 1
    if _interrupt_count >= 2:
        if _current_state is not None:
            try:
                from .state import save_state
                save_state(_current_state)
                print_warning("Double interrupt — state saved. Run 'agent-team resume' to continue.")
            except Exception:
                print_warning("Double interrupt — state save failed. Exiting.")
        else:
            print_warning("Double interrupt — exiting immediately.")
        sys.exit(130)
    print_warning("Interrupt received. Press Ctrl+C again to save state and exit.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="agent-team",
        description="Convergence-driven multi-agent orchestration system",
    )
    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Task description (omit for interactive mode)",
    )
    parser.add_argument(
        "--prd",
        metavar="FILE",
        default=None,
        help="Path to a PRD file for full application build",
    )
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "thorough", "exhaustive"],
        default=None,
        help="Override depth level",
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=None,
        metavar="N",
        help="Override total agent count (distributed across phases)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override model (default: opus)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override max agentic turns",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="FILE",
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the project (default: current dir)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all tool calls and fleet details",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode (default when no task given)",
    )
    parser.add_argument(
        "--no-interview",
        action="store_true",
        help="Skip the interview phase and go straight to the orchestrator",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show task analysis without making API calls",
    )
    parser.add_argument(
        "--interview-doc",
        metavar="FILE",
        default=None,
        help="Path to a pre-existing interview document (skips live interview)",
    )
    parser.add_argument(
        "--design-ref",
        metavar="URL",
        nargs="+",
        default=None,
        type=_validate_url,
        help="Reference website URL(s) for design inspiration",
    )
    map_group = parser.add_mutually_exclusive_group()
    map_group.add_argument(
        "--no-map",
        action="store_true",
        help="Skip codebase mapping phase",
    )
    map_group.add_argument(
        "--map-only",
        action="store_true",
        help="Run codebase map and print summary, then exit",
    )

    prog_group = parser.add_mutually_exclusive_group()
    prog_group.add_argument(
        "--progressive",
        action="store_true",
        help="Enable progressive verification",
    )
    prog_group.add_argument(
        "--no-progressive",
        action="store_true",
        help="Disable progressive verification",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _handle_subcommand(cmd: str) -> None:
    """Handle agent-team subcommands."""
    if cmd == "init":
        _subcommand_init()
    elif cmd == "status":
        _subcommand_status()
    elif cmd == "resume":
        _subcommand_resume()
    elif cmd == "clean":
        _subcommand_clean()
    elif cmd == "guide":
        _subcommand_guide()


def _subcommand_init() -> None:
    """Generate a starter config.yaml with comments."""
    config_path = Path("config.yaml")
    if config_path.exists():
        print_warning("config.yaml already exists. Delete it first or use a different name.")
        return
    config_path.write_text(
        "# Agent Team Configuration\n"
        "# See: https://github.com/omar-agent-team/docs\n\n"
        "orchestrator:\n"
        "  model: opus\n"
        "  max_turns: 500\n\n"
        "depth:\n"
        "  default: standard\n"
        "  auto_detect: true\n\n"
        "convergence:\n"
        "  max_cycles: 10\n\n"
        "interview:\n"
        "  enabled: true\n"
        "  min_exchanges: 3\n\n"
        "display:\n"
        "  show_cost: true\n"
        "  verbose: false\n",
        encoding="utf-8",
    )
    print_info("Created config.yaml with default settings.")


def _subcommand_status() -> None:
    """Show .agent-team/ contents and state."""
    agent_dir = Path(".agent-team")
    if not agent_dir.exists():
        print_info("No .agent-team/ directory found.")
        return
    print_info(f"Agent Team directory: {agent_dir.resolve()}")
    for f in sorted(agent_dir.iterdir()):
        size = f.stat().st_size
        print_info(f"  {f.name} ({size} bytes)")
    # Check for state
    from .state import load_state
    state = load_state(str(agent_dir))
    if state:
        print_info(f"  Run ID: {state.run_id}")
        print_info(f"  Task: {state.task[:80]}")
        print_info(f"  Phase: {state.current_phase}")
        print_info(f"  Interrupted: {state.interrupted}")


def _subcommand_resume() -> None:
    """Resume from STATE.json."""
    from .state import is_stale, load_state
    state = load_state()
    if not state:
        print_error("No saved state found. Nothing to resume.")
        return
    if is_stale(state, ""):
        print_warning(
            f"Saved state is from a different task: {state.task[:80]}\n"
            "Run 'agent-team clean' to clear stale state, or re-run with the same task."
        )
    print_info(f"Resuming run {state.run_id} — task: {state.task[:80]}")
    print_info(f"Last phase: {state.current_phase}")
    print_warning("Resume is not yet fully implemented. Please re-run with the same task.")


def _subcommand_clean() -> None:
    """Delete .agent-team/ with confirmation."""
    import shutil
    agent_dir = Path(".agent-team")
    if not agent_dir.exists():
        print_info("No .agent-team/ directory to clean.")
        return
    try:
        response = input("Delete .agent-team/ directory? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if response in ("y", "yes"):
        shutil.rmtree(agent_dir)
        print_info("Cleaned .agent-team/ directory.")
    else:
        print_info("Cancelled.")


def _subcommand_guide() -> None:
    """Print built-in usage guide."""
    guide = (
        "Agent Team — Usage Guide\n"
        "========================\n\n"
        "Quick Start:\n"
        "  agent-team 'fix the login bug'     # Single task\n"
        "  agent-team -i                       # Interactive mode\n"
        "  agent-team --prd spec.md            # Build from PRD\n\n"
        "Flags:\n"
        "  --depth LEVEL    Override depth (quick/standard/thorough/exhaustive)\n"
        "  --agents N       Override agent count\n"
        "  --no-interview   Skip interview phase\n"
        "  --dry-run        Preview without API calls\n"
        "  --design-ref URL Reference website(s) for design\n\n"
        "Subcommands:\n"
        "  agent-team init     Create starter config.yaml\n"
        "  agent-team status   Show current state\n"
        "  agent-team resume   Resume interrupted run\n"
        "  agent-team clean    Delete .agent-team/ directory\n"
        "  agent-team guide    Show this guide\n"
    )
    console.print(guide)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    # Reset globals at start to prevent stale state across multiple invocations
    global _interrupt_count, _current_state
    _interrupt_count = 0
    _current_state = None

    # Check for subcommands before argparse
    if len(sys.argv) > 1 and sys.argv[1] in {"init", "status", "resume", "clean", "guide"}:
        _handle_subcommand(sys.argv[1])
        return

    args = _parse_args()

    # Signal handling
    signal.signal(signal.SIGINT, _handle_interrupt)

    # Build CLI overrides
    cli_overrides: dict[str, Any] = {}
    if args.model:
        cli_overrides.setdefault("orchestrator", {})["model"] = args.model
    if args.max_turns:
        cli_overrides.setdefault("orchestrator", {})["max_turns"] = args.max_turns
    if args.verbose:
        cli_overrides.setdefault("display", {})["verbose"] = True
        cli_overrides.setdefault("display", {})["show_tools"] = True

    # Load config
    try:
        config = load_config(config_path=args.config, cli_overrides=cli_overrides)
    except ValueError as exc:
        print_error(f"Configuration error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print_error(f"Failed to load configuration: {exc}")
        sys.exit(1)

    # Apply progressive verification flags
    if args.progressive:
        config.verification.enabled = True
    elif args.no_progressive:
        config.verification.enabled = False

    # Collect, filter, and deduplicate design reference URLs
    design_ref_urls: list[str] = list(config.design_reference.urls)
    if args.design_ref:
        design_ref_urls.extend(args.design_ref)
    design_ref_urls = [u for u in design_ref_urls if u and u.strip()]
    design_ref_urls = list(dict.fromkeys(design_ref_urls))  # deduplicate preserving order

    # Resolve working directory
    cwd = args.cwd or os.getcwd()

    # Print banner
    print_banner()

    # Validate PRD file
    if args.prd and not Path(args.prd).is_file():
        print_error(f"PRD file not found: {args.prd}")
        sys.exit(1)

    # Validate interview-doc file
    if args.interview_doc and not Path(args.interview_doc).is_file():
        print_error(f"Interview document not found: {args.interview_doc}")
        sys.exit(1)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print_error("ANTHROPIC_API_KEY environment variable not set.")
        print_info("Get your key at: https://console.anthropic.com/settings/keys")
        print_info("Then set it:")
        if sys.platform == "win32":
            print_info('  PowerShell: $env:ANTHROPIC_API_KEY = "sk-..."')
            print_info('  CMD: set ANTHROPIC_API_KEY=sk-...')
        else:
            print_info('  export ANTHROPIC_API_KEY="sk-..."')
        sys.exit(1)

    # -------------------------------------------------------------------
    # C4: Dry-run mode (early gate before interview)
    # -------------------------------------------------------------------
    if args.dry_run:
        task = args.task or "(interactive mode)"
        if args.task:
            detection = detect_depth(task, config)
            depth = detection.level
        else:
            depth = args.depth or "standard"
        print_info("DRY RUN — no API calls will be made")
        print_info(f"Task: {task[:200]}")
        print_info(f"Depth: {depth}")
        print_info(f"Interview: {'enabled' if config.interview.enabled else 'disabled'}")
        print_info(f"Min exchanges: {config.interview.min_exchanges}")
        print_info(f"Model: {config.orchestrator.model}")
        print_info(f"Max turns: {config.orchestrator.max_turns}")
        return

    # -------------------------------------------------------------------
    # Phase 0: Interview
    # -------------------------------------------------------------------
    interview_doc: str | None = None
    interview_scope: str | None = None

    if args.prd and args.interview_doc:
        print_warning("Both --prd and --interview-doc provided; using --interview-doc")
        args.prd = None  # Clear to prevent dual PRD/interview injection

    if args.interview_doc:
        # Pre-existing interview document provided
        interview_doc = Path(args.interview_doc).read_text(encoding="utf-8")
        interview_scope = _detect_scope(interview_doc)  # I6 fix: parse scope
        print_interview_skip(f"using provided document: {args.interview_doc}")
    elif args.prd:
        # PRD mode — skip interview, the PRD IS the requirements
        print_interview_skip("PRD file provided (--prd)")
    elif args.no_interview:
        # Explicitly skipped
        print_interview_skip("--no-interview flag")
    elif config.interview.enabled:
        # Run the live interview with error handling
        try:
            result = asyncio.run(run_interview(
                config=config,
                cwd=cwd,
                initial_task=args.task,
            ))
            interview_doc = result.doc_content if result.doc_content else None
            interview_scope = result.scope

            if not interview_doc:
                print_warning(
                    "Interview completed but produced no document. "
                    "Proceeding without interview context."
                )
            elif result.scope == "COMPLEX":
                print_info(
                    "Interview scope is COMPLEX — orchestrator will use "
                    "exhaustive depth and PRD mode."
                )
        except KeyboardInterrupt:
            print_warning("Interview interrupted. Proceeding without interview context.")
        except Exception as exc:
            print_error(f"Interview failed: {exc}")
            print_info("Proceeding without interview context.")

    # -------------------------------------------------------------------
    # Phase 0.25: Constraint Extraction
    # -------------------------------------------------------------------
    constraints: list | None = None
    task_for_constraints = args.task or ""
    try:
        extracted = extract_constraints(task_for_constraints, interview_doc)
        if extracted:
            constraints = extracted
            print_info(f"Extracted {len(constraints)} user constraint(s)")
    except Exception as exc:
        print_warning(f"Constraint extraction failed: {exc}")

    # -------------------------------------------------------------------
    # C2: Initialize RunState after task is known
    # -------------------------------------------------------------------
    from .state import RunState
    _current_state = RunState(task=task_for_constraints or "", depth="pending")
    _current_state.current_phase = "post-interview"

    # -------------------------------------------------------------------
    # Phase 0.5: Codebase Map
    # -------------------------------------------------------------------
    codebase_map_summary: str | None = None
    if config.codebase_map.enabled and not args.no_map:
        try:
            from .codebase_map import generate_codebase_map, summarize_map
            print_map_start(cwd)
            cmap = asyncio.run(generate_codebase_map(
                cwd,
                timeout=config.codebase_map.timeout_seconds,
                max_files=config.codebase_map.max_files,
                max_file_size_kb=config.codebase_map.max_file_size_kb,
                max_file_size_kb_ts=config.codebase_map.max_file_size_kb_ts,
                exclude_patterns=config.codebase_map.exclude_patterns,
            ))
            codebase_map_summary = summarize_map(cmap)
            print_map_complete(cmap.total_files, cmap.primary_language)
            if args.map_only:
                console.print(codebase_map_summary)
                sys.exit(0)
        except Exception as exc:
            print_warning(f"Codebase mapping failed: {exc}")
            print_info("Proceeding without codebase map.")

    # -------------------------------------------------------------------
    # Phase 0.75: Contract Loading + Scheduling
    # -------------------------------------------------------------------
    contract_registry = None
    schedule_info = None

    if config.verification.enabled:
        try:
            from .contracts import ContractRegistry, load_contracts
            contract_path = Path(cwd) / config.convergence.requirements_dir / config.verification.contract_file
            if contract_path.is_file():
                contract_registry = load_contracts(contract_path)
                print_info(f"Contracts loaded from {contract_path}")
            else:
                print_info("No contract file found -- verification will use empty registry.")
                contract_registry = ContractRegistry()
        except Exception as exc:
            print_warning(f"Contract loading failed: {exc}")

    if config.scheduler.enabled:
        try:
            from .scheduler import compute_schedule, parse_tasks_md
            tasks_path = Path(cwd) / config.convergence.requirements_dir / "TASKS.md"
            if tasks_path.is_file():
                tasks_content = tasks_path.read_text(encoding="utf-8")
                task_graph = parse_tasks_md(tasks_content)
                schedule_info = compute_schedule(task_graph, scheduler_config=config.scheduler)
                total_conflicts = sum(schedule_info.conflict_summary.values())
                print_schedule_summary(
                    waves=schedule_info.total_waves,
                    conflicts=total_conflicts,
                )
            else:
                print_info("No TASKS.md found -- scheduler will be used post-orchestration.")
        except Exception as exc:
            print_warning(f"Scheduler failed: {exc}")

    # -------------------------------------------------------------------
    # C5: Initialize and start InterventionQueue
    # -------------------------------------------------------------------
    intervention = InterventionQueue()

    try:
        # -------------------------------------------------------------------
        # Determine orchestrator mode
        # -------------------------------------------------------------------
        # If interview produced a document, we have enough context for single-shot,
        # unless the user explicitly asked for interactive mode with -i.
        has_interview = interview_doc is not None
        interactive = args.interactive or (
            args.task is None and args.prd is None and not has_interview
        )

        # Auto-override depth based on interview scope or PRD mode when user didn't set --depth
        depth_override = args.depth
        if not depth_override and (interview_scope == "COMPLEX" or args.prd):
            depth_override = "exhaustive"

        # Start intervention queue (infrastructure ready for future SDK
        # mid-stream injection support; hint suppressed until polling is wired)
        intervention.start()

        # Update phase to orchestration
        if _current_state:
            _current_state.current_phase = "orchestration"

        run_cost = 0.0
        if interactive:
            run_cost = asyncio.run(_run_interactive(
                config=config,
                cwd=cwd,
                depth_override=depth_override,
                agent_count_override=args.agents,
                prd_path=args.prd,
                interview_doc=interview_doc,
                interview_scope=interview_scope,
                design_reference_urls=design_ref_urls or None,
                codebase_map_summary=codebase_map_summary,
                constraints=constraints,
            ))
        else:
            # Use the interview doc as the task if no explicit task was given
            task = args.task or ""
            if has_interview and not task:
                task = "Implement the requirements from the interview document."
            if depth_override:
                depth = depth_override
            else:
                detection = detect_depth(task, config)
                depth = detection.level
                print_depth_detection(detection)
            agent_count = _detect_agent_count(task, args.agents)

            # Update RunState with resolved depth
            if _current_state:
                _current_state.depth = depth

            run_cost = asyncio.run(_run_single(
                task=task,
                config=config,
                cwd=cwd,
                depth=depth,
                agent_count=agent_count,
                prd_path=args.prd,
                interview_doc=interview_doc,
                interview_scope=interview_scope,
                design_reference_urls=design_ref_urls or None,
                codebase_map_summary=codebase_map_summary,
                constraints=constraints,
            ))

        # Update RunState with actual cost from orchestration
        if _current_state:
            _current_state.total_cost = run_cost or 0.0

        # Update phase to complete after orchestration
        if _current_state:
            _current_state.current_phase = "complete"

    finally:
        # Stop intervention queue
        intervention.stop()

    # -------------------------------------------------------------------
    # Post-orchestration: Update TASKS.md statuses
    # -------------------------------------------------------------------
    if config.scheduler.enabled:
        try:
            from .scheduler import update_tasks_md_statuses

            tasks_path = (
                Path(cwd) / config.convergence.requirements_dir / "TASKS.md"
            )
            if tasks_path.is_file():
                old_content = tasks_path.read_text(encoding="utf-8")
                new_content = update_tasks_md_statuses(old_content)
                tasks_path.write_text(new_content, encoding="utf-8")
                print_info("TASKS.md statuses updated to COMPLETE.")
        except Exception as exc:
            print_warning(f"Task status update failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Verification (if enabled)
    # -------------------------------------------------------------------
    if config.verification.enabled and contract_registry is not None:
        try:
            from .contracts import verify_all_contracts
            from .verification import (
                ProgressiveVerificationState,
                update_verification_state,
                verify_task_completion,
                write_verification_summary,
            )

            verification_path = (
                Path(cwd) / config.convergence.requirements_dir
                / config.verification.verification_file
            )
            print_info("Running post-orchestration verification...")

            # Phase 1: Verify contracts against current project state
            vr = verify_all_contracts(contract_registry, Path(cwd))
            if not vr.passed:
                for v in vr.violations:
                    print_contract_violation(v.description)

            # Phase 2-4: Run full verification pipeline
            result = asyncio.run(verify_task_completion(
                task_id="post-orchestration",
                project_root=Path(cwd),
                registry=contract_registry,
                run_lint=config.verification.run_lint,
                run_type_check=config.verification.run_type_check,
                run_tests=config.verification.run_tests,
                blocking=config.verification.blocking,
            ))

            # Build state and write summary
            state = ProgressiveVerificationState()
            update_verification_state(state, result)
            write_verification_summary(state, verification_path)

            print_verification_summary({
                "overall_health": state.overall_health,
                "completed_tasks": {
                    result.task_id: result.overall,
                },
            })
        except Exception as exc:
            print_warning(f"Post-orchestration verification failed: {exc}")
