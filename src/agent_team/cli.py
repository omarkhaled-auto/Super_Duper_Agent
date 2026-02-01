"""CLI entry point for Agent Team.

Handles argument parsing, depth detection, interactive/single-shot modes,
signal handling, and cost tracking.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import signal
import sys
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
from .config import AgentTeamConfig, detect_depth, load_config
from .display import (
    console,
    print_agent_response,
    print_banner,
    print_completion,
    print_cost_summary,
    print_error,
    print_info,
    print_interactive_prompt,
    print_interview_skip,
    print_prd_mode,
    print_task_start,
    print_warning,
)
from .interviewer import _detect_scope, run_interview
from .mcp_servers import get_mcp_servers


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
) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with all agents and MCP servers."""
    mcp_servers = get_mcp_servers(config)
    agent_defs_raw = build_agent_definitions(config, mcp_servers)

    # Convert raw dicts to AgentDefinition objects
    agent_defs = {
        name: AgentDefinition(**defn)
        for name, defn in agent_defs_raw.items()
    }

    # Inject runtime values into orchestrator system prompt
    system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.replace(
        "{escalation_threshold}",
        str(config.convergence.escalation_threshold),
    ).replace(
        "{max_escalation_depth}",
        str(config.convergence.max_escalation_depth),
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
) -> None:
    """Run the interactive multi-turn conversation loop."""
    options = _build_options(config, cwd)
    phase_costs: dict[str, float] = {}
    total_cost = 0.0

    async with ClaudeSDKClient(options=options) as client:
        # If a PRD or task was provided on the CLI, send it first
        if prd_path:
            print_prd_mode(prd_path)
            prd_content = Path(prd_path).read_text(encoding="utf-8")
            task = f"Build this application from the following PRD:\n\n{prd_content}"
            depth = depth_override or "exhaustive"
            agent_count = agent_count_override
            prompt = build_orchestrator_prompt(
                task=task,
                depth=depth,
                config=config,
                prd_path=prd_path,
                agent_count=agent_count,
                cwd=cwd,
                interview_doc=interview_doc,
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

            depth = depth_override or detect_depth(user_input, config)
            agent_count = _detect_agent_count(user_input, agent_count_override)
            is_prd = _detect_prd_from_task(user_input)

            # I4 fix: inline PRD detection forces exhaustive depth
            if is_prd and not depth_override:
                depth = "exhaustive"

            prompt = build_orchestrator_prompt(
                task=user_input,
                depth=depth,
                config=config,
                prd_path="inline" if is_prd else None,
                agent_count=agent_count,
                cwd=cwd,
                interview_doc=interview_doc,
            )
            # Only inject interview_doc on the first query
            interview_doc = None

            if is_prd:
                print_prd_mode("inline")

            print_task_start(user_input, depth, agent_count)
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs)
            total_cost += cost

    if config.display.show_cost and total_cost > 0:
        print_cost_summary(phase_costs)


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
) -> None:
    """Run a single task to completion."""
    options = _build_options(config, cwd)
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
    )

    print_task_start(task, depth, agent_count)

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        total_cost = await _process_response(client, config, phase_costs)

    if config.display.show_cost:
        print_cost_summary(phase_costs)
        print_completion(task[:100], 0, total_cost)


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

_interrupt_count = 0


def _handle_interrupt(signum: int, frame: Any) -> None:
    """Handle Ctrl+C: first press interrupts current operation, second exits."""
    global _interrupt_count
    _interrupt_count += 1
    if _interrupt_count >= 2:
        print_warning("Double interrupt — exiting immediately.")
        sys.exit(130)
    print_warning("Interrupt received. Press Ctrl+C again to exit.")


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
        "--interview-doc",
        metavar="FILE",
        default=None,
        help="Path to a pre-existing interview document (skips live interview)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
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
    config = load_config(config_path=args.config, cli_overrides=cli_overrides)

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
        print_info("Set it in your environment or create a .env file.")
        sys.exit(1)

    # -------------------------------------------------------------------
    # Phase 0: Interview
    # -------------------------------------------------------------------
    interview_doc: str | None = None
    interview_scope: str | None = None

    if args.prd and args.interview_doc:
        print_warning("Both --prd and --interview-doc provided; using --interview-doc")

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

    if interactive:
        asyncio.run(_run_interactive(
            config=config,
            cwd=cwd,
            depth_override=depth_override,
            agent_count_override=args.agents,
            prd_path=args.prd,
            interview_doc=interview_doc,
        ))
    else:
        # Use the interview doc as the task if no explicit task was given
        task = args.task or ""
        if has_interview and not task:
            task = "Implement the requirements from the interview document."
        depth = depth_override or detect_depth(task, config)
        agent_count = _detect_agent_count(task, args.agents)

        asyncio.run(_run_single(
            task=task,
            config=config,
            cwd=cwd,
            depth=depth,
            agent_count=agent_count,
            prd_path=args.prd,
            interview_doc=interview_doc,
        ))
