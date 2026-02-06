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
import shutil
import signal
import string
import subprocess
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
    build_decomposition_prompt,
    build_milestone_execution_prompt,
    build_orchestrator_prompt,
)
from .config import AgentTeamConfig, apply_depth_quality_gating, detect_depth, extract_constraints, load_config, parse_max_review_cycles, parse_per_item_review_cycles
from .state import ConvergenceReport
from .display import (
    console,
    print_agent_response,
    print_banner,
    print_completion,
    print_convergence_health,
    print_contract_violation,
    print_cost_summary,
    print_depth_detection,
    print_error,
    print_info,
    print_interactive_prompt,
    print_intervention,
    print_intervention_hint,
    print_interview_skip,
    print_map_complete,
    print_map_start,
    print_milestone_complete,
    print_milestone_progress,
    print_milestone_start,
    print_prd_mode,
    print_recovery_report,
    print_run_summary,
    print_schedule_summary,
    print_success,
    print_task_start,
    print_verification_summary,
    print_warning,
)
from .interviewer import _detect_scope, run_interview
from .mcp_servers import get_mcp_servers
from .prd_chunking import (
    build_prd_index,
    create_prd_chunks,
    detect_large_prd,
    validate_chunks,
)


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


_URL_RE = re.compile(r'https?://[^\s<>\[\]()"\',;]+')


def _extract_design_urls_from_interview(doc_content: str) -> list[str]:
    """Extract URLs from the 'Design Reference' section of an interview doc."""
    urls: list[str] = []
    in_section = False
    for line in doc_content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## design reference"):
            in_section = True
            continue
        if in_section and stripped.startswith("## ") and "design reference" not in stripped.lower():
            break
        if in_section:
            for match in _URL_RE.finditer(line):
                urls.append(match.group(0).rstrip(".,;:!?)"))
    return list(dict.fromkeys(urls))


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
    task_text: str | None = None,
    depth: str | None = None,
    backend: str | None = None,
) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with all agents and MCP servers."""
    # Auto-enable ST MCP server if orchestrator ST is active for this depth.
    # We build a local MCP server override dict instead of mutating config,
    # so that the caller's AgentTeamConfig is never modified as a side effect.
    _st_auto_enabled = False
    if depth:
        from .config import get_active_st_points
        active_points = get_active_st_points(depth, config.orchestrator_st)
        if active_points:
            st_cfg = config.mcp_servers.get("sequential_thinking")
            if not st_cfg or not st_cfg.enabled:
                _st_auto_enabled = True

    mcp_servers = get_mcp_servers(config)
    if _st_auto_enabled and "sequential_thinking" not in mcp_servers:
        from .mcp_servers import _sequential_thinking_server
        mcp_servers["sequential_thinking"] = _sequential_thinking_server()

    agent_defs_raw = build_agent_definitions(
        config, mcp_servers, constraints=constraints, task_text=task_text,
        gemini_available=_gemini_available,
    )

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
    from .orchestrator_reasoning import build_orchestrator_st_instructions
    st_instructions = build_orchestrator_st_instructions(
        depth or "standard", config.orchestrator_st,
    )
    system_prompt = string.Template(ORCHESTRATOR_SYSTEM_PROMPT).safe_substitute(
        escalation_threshold=str(config.convergence.escalation_threshold),
        max_escalation_depth=str(config.convergence.max_escalation_depth),
        show_fleet_composition=str(config.display.show_fleet_composition),
        show_convergence_status=str(config.display.show_convergence_status),
        max_cycles=str(config.convergence.max_cycles),
        master_plan_file=config.convergence.master_plan_file,
        max_budget_usd=str(config.orchestrator.max_budget_usd),
        orchestrator_st_instructions=st_instructions,
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

    if config.orchestrator.max_thinking_tokens is not None:
        opts_kwargs["max_thinking_tokens"] = config.orchestrator.max_thinking_tokens

    if mcp_servers:
        opts_kwargs["mcp_servers"] = mcp_servers

    if cwd:
        opts_kwargs["cwd"] = Path(cwd)

    # Use subprocess CLI transport for subscription mode (--backend cli)
    if backend == "cli":
        opts_kwargs["cli_path"] = "claude"

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

    # Budget warning check — skip in CLI/subscription mode (no per-token billing)
    if config.orchestrator.max_budget_usd is not None and _backend == "api":
        cumulative = sum(phase_costs.values())
        budget = config.orchestrator.max_budget_usd
        if cumulative >= budget:
            print_warning(f"Budget limit reached: ${cumulative:.2f} >= ${budget:.2f}")
        elif cumulative >= budget * 0.8:
            print_warning(f"Budget warning: ${cumulative:.2f} of ${budget:.2f} used (80%+)")

    return cost


async def _drain_interventions(
    client: ClaudeSDKClient,
    intervention: "InterventionQueue | None",
    config: AgentTeamConfig,
    phase_costs: dict[str, float],
) -> float:
    """Send any queued !! intervention messages to the orchestrator.

    Called after each _process_response() to check whether the user typed
    an intervention while the orchestrator was working.  Each queued
    message is sent as a follow-up query with the highest-priority tag
    that the orchestrator prompt already knows how to handle.

    Returns the cumulative cost of all intervention queries.
    """
    if intervention is None:
        return 0.0
    cost = 0.0
    while intervention.has_intervention():
        msg = intervention.get_intervention()
        if not msg:
            continue
        print_intervention(msg)
        prompt = f"[USER INTERVENTION -- HIGHEST PRIORITY]\n\n{msg}"
        await client.query(prompt)
        c = await _process_response(client, config, phase_costs, current_phase="intervention")
        cost += c
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
    intervention: "InterventionQueue | None" = None,
    resume_context: str | None = None,
    task_text: str | None = None,
) -> float:
    """Run the interactive multi-turn conversation loop. Returns total cost."""
    # Apply depth-based quality gating for initial depth
    apply_depth_quality_gating(depth_override or "standard", config)
    options = _build_options(
        config, cwd, constraints=constraints, task_text=task_text,
        depth=depth_override or "standard", backend=_backend,
    )
    phase_costs: dict[str, float] = {}
    total_cost = 0.0
    last_depth = depth_override or "standard"

    async with ClaudeSDKClient(options=options) as client:
        # If a PRD or task was provided on the CLI, send it first
        if prd_path:
            print_prd_mode(prd_path)
            prd_content = Path(prd_path).read_text(encoding="utf-8")

            # Large PRD detection and chunking
            prd_chunks = None
            prd_index = None
            if config.prd_chunking.enabled and detect_large_prd(
                prd_content, config.prd_chunking.threshold
            ):
                prd_size_kb = len(prd_content.encode("utf-8")) // 1024
                print_info(f"Large PRD detected ({prd_size_kb}KB). Using chunked decomposition.")
                chunk_dir = Path(cwd) / config.convergence.requirements_dir / "prd-chunks"
                prd_chunks = create_prd_chunks(
                    prd_content,
                    chunk_dir,
                    max_chunk_size=config.prd_chunking.max_chunk_size,
                )
                if validate_chunks(prd_chunks, chunk_dir):
                    prd_index = build_prd_index(prd_content)
                    print_info(f"Created {len(prd_chunks)} PRD chunks in {chunk_dir}")
                else:
                    print_warning("Chunk validation failed. Falling back to standard decomposition.")
                    prd_chunks = None
                    prd_index = None

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
                resume_context=resume_context,
                prd_chunks=prd_chunks,
                prd_index=prd_index,
            )
            # Clear resume_context after first use
            resume_context = None
            print_task_start(task[:200], depth, agent_count)
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs)
            total_cost += cost
            total_cost += await _drain_interventions(client, intervention, config, phase_costs)

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
            total_cost += await _drain_interventions(client, intervention, config, phase_costs)

    if config.display.show_cost and total_cost > 0 and _backend == "api":
        print_cost_summary(phase_costs)

    # Run summary (always shown, not gated behind show_cost)
    from .state import RunSummary
    summary = RunSummary(task="(interactive session)", depth=last_depth, total_cost=total_cost)
    print_run_summary(summary, backend=_backend)

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
    intervention: "InterventionQueue | None" = None,
    resume_context: str | None = None,
    task_text: str | None = None,
    schedule_info: str | None = None,
) -> float:
    """Run a single task to completion. Returns total cost."""
    options = _build_options(config, cwd, constraints=constraints, task_text=task_text or task, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}

    # Large PRD detection and chunking
    prd_chunks = None
    prd_index = None

    if prd_path:
        print_prd_mode(prd_path)
        prd_content = Path(prd_path).read_text(encoding="utf-8")

        # Chunk large PRDs to prevent context overflow
        if config.prd_chunking.enabled and detect_large_prd(
            prd_content, config.prd_chunking.threshold
        ):
            prd_size_kb = len(prd_content.encode("utf-8")) // 1024
            print_info(f"Large PRD detected ({prd_size_kb}KB). Using chunked decomposition.")
            chunk_dir = Path(cwd or ".") / config.convergence.requirements_dir / "prd-chunks"
            prd_chunks = create_prd_chunks(
                prd_content,
                chunk_dir,
                max_chunk_size=config.prd_chunking.max_chunk_size,
            )
            if validate_chunks(prd_chunks, chunk_dir):
                prd_index = build_prd_index(prd_content)
                print_info(f"Created {len(prd_chunks)} PRD chunks in {chunk_dir}")
            else:
                print_warning("Chunk validation failed. Falling back to standard decomposition.")
                prd_chunks = None
                prd_index = None

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
        resume_context=resume_context,
        schedule_info=schedule_info,
        prd_chunks=prd_chunks,
        prd_index=prd_index,
    )

    print_task_start(task, depth, agent_count)

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        total_cost = await _process_response(client, config, phase_costs)
        total_cost += await _drain_interventions(client, intervention, config, phase_costs)

    # Cost breakdown (gated behind show_cost; skip in subscription mode)
    cycle_count = 0
    req_passed = 0
    req_total = 0
    health = "unknown"

    if config.display.show_cost and _backend == "api":
        print_cost_summary(phase_costs)

    # Read REQUIREMENTS.md for actual cycle count + requirement stats (always, for RunSummary)
    req_path = Path(cwd or ".") / config.convergence.requirements_dir / config.convergence.requirements_file
    if req_path.exists():
        try:
            req_content = req_path.read_text(encoding="utf-8")
            cycle_count = parse_max_review_cycles(req_content)
            # Parse checked/unchecked counts
            checked = len(re.findall(r"^- \[x\]", req_content, re.MULTILINE))
            unchecked = len(re.findall(r"^- \[ \]", req_content, re.MULTILINE))
            req_passed = checked
            req_total = checked + unchecked
            # Derive health
            if req_total == 0:
                health = "unknown"
            elif req_passed == req_total:
                health = "healthy"
            elif cycle_count > 0 and req_passed / req_total >= config.convergence.degraded_threshold:
                health = "degraded"
            else:
                health = "failed"
        except (OSError, ValueError) as exc:
            print_warning(f"Could not parse review cycles: {exc}")

    if config.display.show_cost:
        cost_for_display = total_cost if _backend == "api" else None
        print_completion(task[:100], cycle_count, cost_for_display)

    # Run summary (always shown, not gated behind show_cost)
    from .state import RunSummary
    summary = RunSummary(
        task=task[:100],
        depth=depth,
        total_cost=total_cost,
        cycle_count=cycle_count,
        requirements_passed=req_passed,
        requirements_total=req_total,
        health=health,
    )
    print_run_summary(summary, backend=_backend)

    return total_cost


# ---------------------------------------------------------------------------
# PRD milestone orchestration loop
# ---------------------------------------------------------------------------


def _build_completed_milestones_context(
    plan: "MasterPlan",
    milestone_manager: "MilestoneManager",
) -> list["MilestoneCompletionSummary"]:
    """Build compressed summaries for all completed milestones."""
    from .milestone_manager import (
        MilestoneCompletionSummary,
        build_completion_summary,
        load_completion_cache,
        save_completion_cache,
    )

    summaries: list[MilestoneCompletionSummary] = []
    for m in plan.milestones:
        if m.status == "COMPLETE":
            # Try cache first
            cached = load_completion_cache(
                str(milestone_manager._milestones_dir), m.id,
            )
            if cached:
                summaries.append(cached)
                continue
            # Fallback: build from REQUIREMENTS.md
            exported_files = list(milestone_manager._collect_milestone_files(m.id))
            summary = build_completion_summary(
                milestone=m,
                exported_files=exported_files[:20],
                summary_line=m.description[:120] if m.description else m.title,
            )
            # Cache for future iterations
            save_completion_cache(
                str(milestone_manager._milestones_dir), m.id, summary,
            )
            summaries.append(summary)
    return summaries


async def _run_prd_milestones(
    task: str,
    config: AgentTeamConfig,
    cwd: str | None,
    depth: str,
    prd_path: str | None,
    interview_doc: str | None = None,
    codebase_map_summary: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    design_reference_urls: list[str] | None = None,
) -> tuple[float, ConvergenceReport | None]:
    """Execute the per-milestone orchestration loop for PRD mode.

    Phase 1: Decomposition — one orchestrator call to create MASTER_PLAN.md
    Phase 2: Execution — one fresh session per milestone, in dependency order

    Returns ``(total_cost, convergence_report)`` where the report aggregates
    health across all milestones (or ``None`` if no milestones completed).
    """
    from .milestone_manager import (
        MilestoneManager,
        aggregate_milestone_convergence,
        build_milestone_context,
        compute_rollup_health,
        parse_master_plan,
        render_predecessor_context,
        update_master_plan_status,
    )
    from .state import save_state, update_completion_ratio, update_milestone_progress

    global _current_state

    total_cost = 0.0
    project_root = Path(cwd or ".")
    req_dir = project_root / config.convergence.requirements_dir
    master_plan_path = req_dir / config.convergence.master_plan_file

    # ------------------------------------------------------------------
    # Phase 1: DECOMPOSITION
    # ------------------------------------------------------------------
    # Check if MASTER_PLAN.md already exists (resume scenario)
    if not master_plan_path.is_file():
        print_info("Phase 1: PRD Decomposition — creating MASTER_PLAN.md")

        # Large PRD detection and chunking
        prd_chunks = None
        prd_index = None
        prd_content_for_check = Path(prd_path).read_text(encoding="utf-8") if prd_path else task
        if config.prd_chunking.enabled and detect_large_prd(
            prd_content_for_check, config.prd_chunking.threshold
        ):
            prd_size_kb = len(prd_content_for_check.encode("utf-8")) // 1024
            print_info(f"Large PRD detected ({prd_size_kb}KB). Using chunked decomposition.")
            chunk_dir = req_dir / "prd-chunks"
            prd_chunks = create_prd_chunks(
                prd_content_for_check,
                chunk_dir,
                max_chunk_size=config.prd_chunking.max_chunk_size,
            )
            if validate_chunks(prd_chunks, chunk_dir):
                prd_index = build_prd_index(prd_content_for_check)
                print_info(f"Created {len(prd_chunks)} PRD chunks in {chunk_dir}")
            else:
                print_warning("Chunk validation failed. Falling back to standard decomposition.")
                prd_chunks = None
                prd_index = None

        decomp_prompt = build_decomposition_prompt(
            task=task,
            depth=depth,
            config=config,
            prd_path=prd_path,
            cwd=cwd,
            interview_doc=interview_doc,
            codebase_map_summary=codebase_map_summary,
            design_reference_urls=design_reference_urls,
            prd_chunks=prd_chunks,
            prd_index=prd_index,
        )

        options = _build_options(config, cwd, constraints=constraints, task_text=task, depth=depth, backend=_backend)
        phase_costs: dict[str, float] = {}

        async with ClaudeSDKClient(options=options) as client:
            await client.query(decomp_prompt)
            decomp_cost = await _process_response(client, config, phase_costs)
            if intervention:
                decomp_cost += await _drain_interventions(client, intervention, config, phase_costs)
            total_cost += decomp_cost

        if not master_plan_path.is_file():
            print_error(
                "Decomposition did not create MASTER_PLAN.md. "
                "The orchestrator may need a different prompt. Aborting milestone loop."
            )
            return total_cost, None
    else:
        print_info("Phase 1: Skipping decomposition — MASTER_PLAN.md already exists")

    # Parse the master plan
    plan_content = master_plan_path.read_text(encoding="utf-8")
    plan = parse_master_plan(plan_content)

    if not plan.milestones:
        print_error("MASTER_PLAN.md contains no milestones. Aborting.")
        return total_cost, None

    # Warn if decomposition produced too many milestones
    if len(plan.milestones) > config.milestone.max_milestones_warning:
        print_warning(
            f"Decomposition produced {len(plan.milestones)} milestones "
            f"(threshold: {config.milestone.max_milestones_warning}). "
            f"Consider consolidating to reduce execution cost."
        )

    # Save milestone order in state
    if _current_state:
        _current_state.milestone_order = [m.id for m in plan.milestones]

    mm = MilestoneManager(project_root)
    milestones_dir = req_dir / "milestones"

    # Determine resume point
    resume_from = config.milestone.resume_from_milestone
    if not resume_from and _current_state:
        from .state import get_resume_milestone
        resume_from = get_resume_milestone(_current_state)

    # ------------------------------------------------------------------
    # Phase 2: EXECUTION LOOP
    # ------------------------------------------------------------------
    print_info(f"Phase 2: Executing {len(plan.milestones)} milestones")

    iteration = 0
    max_iterations = len(plan.milestones) * 2  # safety limit

    while not plan.all_complete() and iteration < max_iterations:
        iteration += 1
        ready = plan.get_ready_milestones()

        if not ready:
            # Check for deadlock or all failed
            health = compute_rollup_health(plan)
            if health["health"] == "failed":
                print_error("Milestone plan health: FAILED. Stopping.")
                break
            print_warning("No milestones ready. Waiting for dependencies to resolve...")
            break

        for milestone in ready:
            # Skip already-completed milestones (resume scenario)
            if resume_from and milestone.id != resume_from:
                completed_ids = {m.id for m in plan.milestones if m.status == "COMPLETE"}
                if milestone.id in completed_ids:
                    continue

            # Clear resume_from after first milestone starts
            resume_from = None

            # Track milestone index for display
            ms_index = next(
                (i + 1 for i, m in enumerate(plan.milestones) if m.id == milestone.id),
                0,
            )

            print_milestone_start(
                milestone.id, milestone.title,
                ms_index, len(plan.milestones),
            )

            # Update plan and state
            milestone.status = "IN_PROGRESS"
            plan_content = update_master_plan_status(plan_content, milestone.id, "IN_PROGRESS")
            master_plan_path.write_text(plan_content, encoding="utf-8")

            if _current_state:
                update_milestone_progress(_current_state, milestone.id, "IN_PROGRESS")
                update_completion_ratio(_current_state)
                save_state(_current_state, directory=str(req_dir.parent / ".agent-team"))

            # Build scoped context
            predecessor_summaries = _build_completed_milestones_context(plan, mm)
            ms_context = build_milestone_context(
                milestone, milestones_dir, predecessor_summaries,
            )
            predecessor_str = render_predecessor_context(predecessor_summaries)

            # Build milestone-specific prompt
            ms_prompt = build_milestone_execution_prompt(
                task=task,
                depth=depth,
                config=config,
                milestone_context=ms_context,
                cwd=cwd,
                codebase_map_summary=codebase_map_summary,
                predecessor_context=predecessor_str,
                design_reference_urls=design_reference_urls,
            )

            # Fresh session for this milestone
            ms_options = _build_options(
                config, cwd, constraints=constraints,
                task_text=task, depth=depth, backend=_backend,
            )
            ms_phase_costs: dict[str, float] = {}
            health_report: ConvergenceReport | None = None

            try:
                async with ClaudeSDKClient(options=ms_options) as client:
                    await client.query(ms_prompt)
                    ms_cost = await _process_response(client, config, ms_phase_costs)
                    if intervention:
                        ms_cost += await _drain_interventions(
                            client, intervention, config, ms_phase_costs,
                        )
                    total_cost += ms_cost
            except Exception as exc:
                print_warning(f"Milestone {milestone.id} failed: {exc}")
                milestone.status = "FAILED"
                plan_content = update_master_plan_status(
                    plan_content, milestone.id, "FAILED",
                )
                master_plan_path.write_text(plan_content, encoding="utf-8")
                if _current_state:
                    update_milestone_progress(_current_state, milestone.id, "FAILED")
                    update_completion_ratio(_current_state)
                    save_state(_current_state, directory=str(req_dir.parent / ".agent-team"))
                continue

            # Health check (if gate enabled)
            health_report = mm.check_milestone_health(
                milestone.id,
                min_convergence_ratio=config.convergence.min_convergence_ratio,
            )

            if config.milestone.health_gate and health_report.health == "failed":
                print_warning(
                    f"Milestone {milestone.id} health gate FAILED "
                    f"({health_report.checked_requirements}/{health_report.total_requirements}). "
                    f"Marking as FAILED."
                )
                milestone.status = "FAILED"
                plan_content = update_master_plan_status(
                    plan_content, milestone.id, "FAILED",
                )
                master_plan_path.write_text(plan_content, encoding="utf-8")
                if _current_state:
                    update_milestone_progress(_current_state, milestone.id, "FAILED")
                    update_completion_ratio(_current_state)
                    save_state(_current_state, directory=str(req_dir.parent / ".agent-team"))
                continue

            # Wiring verification with retry loop (if enabled)
            if config.milestone.wiring_check:
                max_retries = config.milestone.wiring_fix_retries
                for wiring_attempt in range(max_retries + 1):
                    export_issues = mm.verify_milestone_exports(milestone.id)
                    if not export_issues:
                        break  # Clean — no wiring gaps
                    if wiring_attempt < max_retries:
                        print_warning(
                            f"Milestone {milestone.id} has {len(export_issues)} wiring issues "
                            f"(attempt {wiring_attempt + 1}/{max_retries + 1}). "
                            f"Running wiring fix pass."
                        )
                        wiring_cost = await _run_milestone_wiring_fix(
                            milestone_id=milestone.id,
                            wiring_issues=export_issues,
                            config=config,
                            cwd=cwd,
                            depth=depth,
                            task=task,
                            constraints=constraints,
                            intervention=intervention,
                        )
                        total_cost += wiring_cost
                    else:
                        print_warning(
                            f"Milestone {milestone.id} still has {len(export_issues)} "
                            f"wiring issues after {max_retries} fix attempt(s). "
                            f"Proceeding anyway."
                        )

            # Mark complete
            milestone.status = "COMPLETE"
            plan_content = update_master_plan_status(
                plan_content, milestone.id, "COMPLETE",
            )
            master_plan_path.write_text(plan_content, encoding="utf-8")

            if _current_state:
                update_milestone_progress(_current_state, milestone.id, "COMPLETE")
                update_completion_ratio(_current_state)
                save_state(_current_state, directory=str(req_dir.parent / ".agent-team"))

            # Cache completion summary for future iterations
            from .milestone_manager import save_completion_cache, build_completion_summary as _build_cs
            _cs = _build_cs(
                milestone=milestone,
                exported_files=list(mm._collect_milestone_files(milestone.id))[:20],
                summary_line=milestone.description[:120] if milestone.description else milestone.title,
            )
            save_completion_cache(str(mm._milestones_dir), milestone.id, _cs)

            health_status = health_report.health if health_report else "unknown"
            print_milestone_complete(milestone.id, milestone.title, health_status)

        # Re-read plan for next iteration
        plan_content = master_plan_path.read_text(encoding="utf-8")
        plan = parse_master_plan(plan_content)

        rollup = compute_rollup_health(plan)
        print_milestone_progress(
            rollup.get("complete", 0),
            rollup.get("total", 0),
            rollup.get("failed", 0),
        )

    # Aggregate convergence across all milestones
    milestone_report = aggregate_milestone_convergence(
        mm,
        min_convergence_ratio=config.convergence.min_convergence_ratio,
        degraded_threshold=config.convergence.degraded_threshold,
    )
    return total_cost, milestone_report


async def _run_milestone_wiring_fix(
    milestone_id: str,
    wiring_issues: list[str],
    config: AgentTeamConfig,
    cwd: str | None,
    depth: str,
    task: str,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
) -> float:
    """Run a targeted wiring fix pass for cross-milestone integration gaps.

    Launches a fresh orchestrator session with instructions to fix only
    the listed wiring issues, without touching other milestones' code.

    Returns the cost of the wiring fix pass.
    """
    if not wiring_issues:
        return 0.0

    print_info(f"Running wiring fix for milestone {milestone_id} ({len(wiring_issues)} issues)")

    wiring_block = "\n".join(f"  - {issue}" for issue in wiring_issues)
    fix_prompt = (
        f"[PHASE: WIRING FIX]\n"
        f"[MILESTONE: {milestone_id}]\n"
        f"\nThe following cross-milestone wiring issues were detected:\n"
        f"{wiring_block}\n\n"
        f"Fix ONLY these wiring issues. Do NOT modify other functionality.\n"
        f"After fixing, verify the connections work by tracing the import chain.\n"
        f"\n[ORIGINAL USER REQUEST]\n{task}"
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt)
            cost = await _process_response(client, config, phase_costs)
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Wiring fix for {milestone_id} failed: {exc}")

    return cost


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
        "--backend",
        choices=["auto", "api", "cli"],
        default=None,
        help="Authentication backend: auto (default), api (require ANTHROPIC_API_KEY), cli (require claude login)",
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
    """Handle agent-team subcommands (except 'resume', which is handled in main)."""
    if cmd == "init":
        _subcommand_init()
    elif cmd == "status":
        _subcommand_status()
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
        "  verbose: false\n"
        "\ndesign_reference:\n"
        "  # standards_file: ./my-design-standards.md  # replace built-in UI standards\n"
        "  # depth: full  # branding | screenshots | full\n"
        "\n# investigation:\n"
        "#   enabled: false          # opt-in: equip review agents with deep investigation\n"
        "#   gemini_model: ''        # empty = default; e.g. gemini-2.5-pro\n"
        "#   max_queries_per_agent: 8\n"
        "#   timeout_seconds: 120\n"
        "#   agents:\n"
        "#     - code-reviewer\n"
        "#     - security-auditor\n"
        "#     - debugger\n",
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


def _subcommand_resume() -> tuple[argparse.Namespace, str] | None:
    """Resume from STATE.json.

    Returns (args_namespace, resume_context) on success, or None if
    resume is not possible.
    """
    from types import SimpleNamespace

    from .display import print_resume_banner
    from .state import load_state, validate_for_resume

    state = load_state()
    if not state:
        print_error("No saved state found. Nothing to resume.")
        return None

    issues = validate_for_resume(state)
    for issue in issues:
        if issue.startswith("ERROR"):
            print_error(issue)
        else:
            print_warning(issue)
    if any(i.startswith("ERROR") for i in issues):
        return None

    print_resume_banner(state)

    # Check for existing INTERVIEW.md
    interview_path = Path(".agent-team") / "INTERVIEW.md"
    interview_doc_path: str | None = str(interview_path) if interview_path.is_file() else None

    # Recover design_ref from saved artifacts
    design_ref: list[str] | None = None
    saved_urls = state.artifacts.get("design_ref_urls", "")
    if saved_urls:
        design_ref = [u for u in saved_urls.split(",") if u.strip()]

    args = SimpleNamespace(
        task=state.task,
        depth=state.depth if state.depth != "pending" else None,
        interview_doc=interview_doc_path,
        no_interview=True,
        prd=state.artifacts.get("prd_path"),
        config=state.artifacts.get("config_path"),
        cwd=state.artifacts.get("cwd"),
        design_ref=design_ref,
        model=None,
        max_turns=None,
        agents=None,
        backend=None,
        verbose=False,
        interactive=False,
        dry_run=False,
        no_map="codebase_map" in state.completed_phases,
        map_only=False,
        progressive=False,
        no_progressive=False,
    )

    resume_ctx = _build_resume_context(state, args.cwd or os.getcwd())
    return (args, resume_ctx)


def _build_resume_context(state: object, cwd: str) -> str:
    """Build a context string for the orchestrator about the interrupted run.

    Scans .agent-team/ for existing artifacts and produces instructions
    for the orchestrator to continue from where it left off.
    """
    run_id = getattr(state, "run_id", "unknown")
    current_phase = getattr(state, "current_phase", "unknown")
    completed_phases = getattr(state, "completed_phases", [])

    lines: list[str] = [
        "\n[RESUME MODE -- Continuing from an interrupted run]",
        f"Run ID: {run_id}",
        f"Interrupted at phase: {current_phase}",
        f"Completed phases: {', '.join(completed_phases) if completed_phases else 'none'}",
    ]

    # List existing artifacts in .agent-team/
    agent_dir = Path(cwd) / ".agent-team"
    known_artifacts = [
        "INTERVIEW.md", "REQUIREMENTS.md", "TASKS.md",
        "MASTER_PLAN.md", "CONTRACTS.json", "VERIFICATION.md",
    ]
    found_artifacts: list[str] = []
    if agent_dir.is_dir():
        for name in known_artifacts:
            artifact_path = agent_dir / name
            if artifact_path.is_file():
                size = artifact_path.stat().st_size
                found_artifacts.append(f"  - {name} ({size} bytes)")

    if found_artifacts:
        lines.append("Existing artifacts in .agent-team/:")
        lines.extend(found_artifacts)

    # Phase-specific resume context (Root Cause #3, Agent 6)
    cycles = getattr(state, "convergence_cycles", 0)
    req_checked = getattr(state, "requirements_checked", 0)
    req_total = getattr(state, "requirements_total", 0)
    error_ctx = getattr(state, "error_context", "")

    if cycles or req_checked or req_total:
        lines.append(f"Convergence state: {req_checked}/{req_total} requirements, {cycles} review cycles")
    if error_ctx:
        lines.append(f"Error that caused interruption: {error_ctx}")

    milestone_progress = getattr(state, "milestone_progress", {})
    if milestone_progress:
        lines.append("Milestone progress:")
        for mid, mdata in milestone_progress.items():
            checked = mdata.get("checked", 0)
            total = mdata.get("total", 0)
            mc = mdata.get("cycles", 0)
            status = mdata.get("status", "unknown")
            lines.append(f"  - {mid}: {status} ({checked}/{total} requirements, {mc} cycles)")

    # Schema version 2 milestone-aware resume context
    current_ms = getattr(state, "current_milestone", "")
    completed_ms = getattr(state, "completed_milestones", [])
    failed_ms = getattr(state, "failed_milestones", [])
    ms_order = getattr(state, "milestone_order", [])

    if ms_order:
        lines.append(f"Milestone order: {', '.join(ms_order)}")
        if completed_ms:
            lines.append(f"Completed milestones: {', '.join(completed_ms)}")
        if failed_ms:
            lines.append(f"Failed milestones: {', '.join(failed_ms)}")
        if current_ms:
            lines.append(f"Interrupted during milestone: {current_ms}")

    lines.append("")
    lines.append("[RESUME INSTRUCTIONS]")

    # Phase-specific resume strategies
    if current_phase == "orchestration" and cycles == 0 and req_total > 0:
        lines.append("- CRITICAL: Previous run interrupted during orchestration with 0 review cycles.")
        lines.append("- You MUST deploy the review fleet FIRST before any new coding.")
        lines.append("- Read REQUIREMENTS.md and run code-reviewer on each unchecked item.")
    elif current_phase == "post_orchestration":
        lines.append("- Previous run interrupted during post-orchestration.")
        lines.append("- Skip to verification: run build, lint, type check, and tests.")
    elif current_phase == "verification":
        lines.append("- Previous run interrupted during verification.")
        lines.append("- Re-run verification only: build, lint, type check, tests.")
    else:
        lines.append("- Read ALL existing artifacts in .agent-team/ FIRST before planning.")
        lines.append("- Do NOT recreate REQUIREMENTS.md or TASKS.md if they already exist.")
        lines.append("- Continue convergence from the first PENDING task in TASKS.md.")
        lines.append("- If REQUIREMENTS.md has unchecked items, resume the convergence loop.")

    lines.append("- Treat existing [x] items as already verified.")

    artifacts = getattr(state, "artifacts", {})
    if artifacts.get("design_research_complete") == "true":
        lines.append("- Design research is ALREADY COMPLETE. Do NOT re-scrape design reference URLs.")
        lines.append("  Use the existing Design Reference section in REQUIREMENTS.md as-is.")

    return "\n".join(lines)


def _has_milestone_requirements(cwd: str, config: AgentTeamConfig) -> bool:
    """Check if any milestone-level REQUIREMENTS.md files exist.

    Returns True if at least one ``milestones/*/REQUIREMENTS.md`` file
    is present in the requirements directory.
    """
    milestones_dir = (
        Path(cwd) / config.convergence.requirements_dir / "milestones"
    )
    if not milestones_dir.is_dir():
        return False
    return any(
        (d / "REQUIREMENTS.md").is_file()
        for d in milestones_dir.iterdir()
        if d.is_dir()
    )


def _check_convergence_health(cwd: str, config: AgentTeamConfig) -> ConvergenceReport:
    """Check convergence health after orchestration completes.

    Reads REQUIREMENTS.md, counts [x] vs [ ], parses review cycle info.
    Detects items stuck at or above escalation_threshold still unchecked.
    Returns a ConvergenceReport with health assessment.
    """
    report = ConvergenceReport()
    req_path = (
        Path(cwd) / config.convergence.requirements_dir
        / config.convergence.requirements_file
    )
    if not req_path.is_file():
        report.health = "unknown"
        return report

    try:
        content = req_path.read_text(encoding="utf-8")
    except OSError:
        report.health = "unknown"
        return report

    # Count checked vs unchecked requirements
    checked = len(re.findall(r"^\s*-\s*\[x\]", content, re.MULTILINE | re.IGNORECASE))
    unchecked = len(re.findall(r"^\s*-\s*\[ \]", content, re.MULTILINE))
    report.total_requirements = checked + unchecked
    report.checked_requirements = checked

    # Parse review cycles from Review Log or review_cycles markers
    report.review_cycles = parse_max_review_cycles(content)

    # Detect per-item escalation: unchecked items with cycles >= threshold
    escalation_threshold = config.convergence.escalation_threshold
    for item_id, is_checked, cycles in parse_per_item_review_cycles(content):
        if not is_checked and cycles >= escalation_threshold:
            report.escalated_items.append(f"{item_id} (cycles: {cycles})")

    # Compute convergence ratio
    if report.total_requirements > 0:
        report.convergence_ratio = report.checked_requirements / report.total_requirements
    else:
        report.convergence_ratio = 0.0

    report.review_fleet_deployed = report.review_cycles > 0

    # Determine health using configurable thresholds
    min_ratio = config.convergence.min_convergence_ratio
    degraded_ratio = config.convergence.degraded_threshold
    if report.total_requirements == 0:
        report.health = "unknown"
    elif report.convergence_ratio >= min_ratio:
        report.health = "healthy"
    elif report.review_fleet_deployed and report.convergence_ratio >= degraded_ratio:
        report.health = "degraded"
    else:
        report.health = "failed"

    return report


def _display_per_milestone_health(cwd: str, config: AgentTeamConfig) -> None:
    """Display per-milestone convergence breakdown.

    H2: Extracted helper to ensure per-milestone display happens in both
    the main path (when milestone_convergence_report is not None) and
    the fallback path (when it's None and we aggregate from disk).
    """
    from .milestone_manager import MilestoneManager

    mm = MilestoneManager(Path(cwd))
    ms_ids = mm._list_milestone_ids()
    if ms_ids:
        print_info(f"Per-milestone convergence ({len(ms_ids)} milestones):")
        for mid in ms_ids:
            mr = mm.check_milestone_health(
                mid,
                min_convergence_ratio=config.convergence.min_convergence_ratio,
                degraded_threshold=config.convergence.degraded_threshold,
            )
            print_info(
                f"  {mid}: {mr.checked_requirements}/{mr.total_requirements} "
                f"({mr.health}, cycles: {mr.review_cycles})"
            )


def _run_review_only(
    cwd: str,
    config: AgentTeamConfig,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    task_text: str | None = None,
    checked: int = 0,
    total: int = 0,
    review_cycles: int = 0,
) -> float:
    """Run a review-only recovery pass when convergence health check detects failures.

    Creates a focused orchestrator prompt that forces the review fleet deployment.
    Adapts the prompt based on whether this is a zero-cycle failure or a partial-review
    failure (review fleet deployed but did not cover enough items).
    Returns cost of the recovery pass.
    """
    is_zero_cycle = checked == 0 and total > 0
    unchecked_count = total - checked

    if is_zero_cycle:
        situation = (
            "CRITICAL RECOVERY: The previous orchestration run completed with ZERO review cycles. "
            "The review fleet was NEVER deployed. This is a convergence failure."
        )
    else:
        situation = (
            f"CRITICAL RECOVERY: The previous orchestration run left {unchecked_count}/{total} "
            f"requirements UNCHECKED ({checked}/{total} checked). "
            "The review fleet was deployed but did not achieve sufficient coverage."
        )

    review_prompt = (
        f"{situation}\n\n"
        "You MUST do the following NOW:\n"
        f"1. Read {config.convergence.requirements_dir}/{config.convergence.requirements_file}\n"
        "2. Deploy the REVIEW FLEET (code-reviewer agents) to verify EACH unchecked item\n"
        "3. For each item, find the implementation and verify correctness\n"
        "4. Mark items [x] ONLY if fully implemented, or document issues in Review Log\n"
        "5. ALWAYS update (review_cycles: N) to (review_cycles: N+1) on EVERY evaluated item\n"
        "6. Deploy TEST RUNNER agents to run tests\n"
        f"7. Report final convergence status: target {total}/{total} requirements checked\n\n"
        "This is NOT optional. The system has detected a convergence failure and this "
        "review pass is MANDATORY."
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, backend=_backend)
    phase_costs: dict[str, float] = {}

    async def _recovery() -> float:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(review_prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="review_recovery")
            cost += await _drain_interventions(client, intervention, config, phase_costs)
        return cost

    if is_zero_cycle:
        print_warning("Convergence health check FAILED: 0 review cycles detected.")
    else:
        print_warning(
            f"Convergence health check FAILED: {unchecked_count}/{total} "
            f"requirements still unchecked after {review_cycles} review cycles."
        )
    print_info("Launching review-only recovery pass...")
    return asyncio.run(_recovery())


def _run_contract_generation(
    cwd: str,
    config: AgentTeamConfig,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    task_text: str | None = None,
    milestone_mode: bool = False,
) -> float:
    """Run a contract-generation recovery pass when CONTRACTS.json is missing.

    Creates a focused orchestrator prompt that forces the contract-generator
    deployment.  When *milestone_mode* is True, the prompt references
    milestone-level REQUIREMENTS.md files instead of the top-level one.
    Returns cost of the recovery pass.
    """
    if milestone_mode:
        req_source = (
            f"the milestone-level REQUIREMENTS.md files under "
            f"{config.convergence.requirements_dir}/milestones/*/REQUIREMENTS.md"
        )
    else:
        req_source = (
            f"{config.convergence.requirements_dir}/{config.convergence.requirements_file}"
        )

    contract_prompt = (
        "CRITICAL RECOVERY: The previous orchestration run completed but CONTRACTS.json "
        "was never generated. The contract-generator agent was NEVER deployed.\n\n"
        "You MUST do the following NOW:\n"
        f"1. Read {req_source}\n"
        "2. Focus on the Architecture Decision, Integration Roadmap, and Wiring Map sections\n"
        "3. Deploy the CONTRACT GENERATOR agent to generate .agent-team/CONTRACTS.json\n"
        "4. Verify the file was written successfully\n\n"
        "This is NOT optional. The system detected that CONTRACTS.json is missing and "
        "contract verification cannot proceed without it."
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, backend=_backend)
    phase_costs: dict[str, float] = {}

    async def _recovery() -> float:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(contract_prompt)
            cost = await _process_response(
                client, config, phase_costs, current_phase="contract_recovery",
            )
            cost += await _drain_interventions(client, intervention, config, phase_costs)
        return cost

    print_warning("Contract health check FAILED: CONTRACTS.json not generated.")
    print_info("Launching contract-generation recovery pass...")
    return asyncio.run(_recovery())


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
# Backend detection
# ---------------------------------------------------------------------------

# Module-level backend tracker: set during main() after detection.
_backend: str = "api"

# Module-level Gemini CLI availability: set during main() when investigation enabled.
_gemini_available: bool = False


def _detect_gemini_cli() -> bool:
    """Detect whether Gemini CLI is installed and runnable.

    Checks shutil.which first (fast), then falls back to subprocess
    for Windows .cmd scripts that shutil.which may miss.
    """
    # Fast path: shutil.which checks PATH
    if shutil.which("gemini") is not None:
        return True
    # Windows fallback: .cmd extension
    if sys.platform == "win32" and shutil.which("gemini.cmd") is not None:
        return True
    # Subprocess fallback: try running it
    try:
        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _check_claude_cli_auth() -> bool:
    """Check if claude CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _detect_backend(requested: str) -> str:
    """Detect which authentication backend to use.

    Returns "api" or "cli". Exits with error if neither works.
    """
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if requested == "api":
        if not has_api_key:
            print_error("--backend=api requires ANTHROPIC_API_KEY.")
            print_info("Get your key at: https://console.anthropic.com/settings/keys")
            sys.exit(1)
        return "api"

    if requested == "cli":
        if not _check_claude_cli_auth():
            print_error("--backend=cli requires 'claude login' authentication.")
            print_info("Run: claude login")
            sys.exit(1)
        return "cli"

    # auto: prefer API key, fall back to CLI
    if has_api_key:
        return "api"
    if _check_claude_cli_auth():
        return "cli"

    # Neither available
    print_error("No authentication found.")
    print_info("Option 1 — API key:")
    if sys.platform == "win32":
        print_info('  PowerShell: $env:ANTHROPIC_API_KEY = "sk-..."')
        print_info('  CMD: set ANTHROPIC_API_KEY=sk-...')
    else:
        print_info('  export ANTHROPIC_API_KEY="sk-..."')
    print_info("Option 2 — Claude subscription:")
    print_info("  Run: claude login")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    # Load .env file if python-dotenv is available (RC7).
    # Must run before _detect_backend() reads ANTHROPIC_API_KEY.
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass

    # Reset globals at start to prevent stale state across multiple invocations
    global _interrupt_count, _current_state, _backend, _gemini_available
    _interrupt_count = 0
    _current_state = None
    _backend = "api"
    _gemini_available = False

    # Check for subcommands before argparse
    _resume_ctx: str | None = None
    if len(sys.argv) > 1 and sys.argv[1] in {"init", "status", "resume", "clean", "guide"}:
        if sys.argv[1] == "resume":
            resume_result = _subcommand_resume()
            if resume_result is None:
                return
            args, _resume_ctx = resume_result
        else:
            _handle_subcommand(sys.argv[1])
            return
    else:
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

    if design_ref_urls:
        from .mcp_servers import is_firecrawl_available
        if not is_firecrawl_available(config):
            print_warning(
                "Design reference URLs provided but Firecrawl is unavailable "
                "(FIRECRAWL_API_KEY not set or firecrawl disabled). "
                "Researchers will fall back to WebFetch with less detail."
            )

    # Detect Gemini CLI when investigation is enabled
    if config.investigation.enabled:
        _gemini_available = _detect_gemini_cli()
        if _gemini_available:
            print_info("Investigation: Gemini CLI detected -- deep investigation enabled")
        else:
            print_warning(
                "Investigation enabled but Gemini CLI not found. "
                "Agents will use the structured investigation methodology "
                "with Read/Glob/Grep only (still valuable, but no cross-file Gemini queries)."
            )

    # Validate custom standards file if specified
    if config.design_reference.standards_file:
        standards_path = Path(config.design_reference.standards_file)
        if not standards_path.is_file():
            print_warning(
                f"Custom standards file not found: {config.design_reference.standards_file}. "
                f"Falling back to built-in UI design standards."
            )

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

    # Detect authentication backend
    backend_requested = getattr(args, "backend", None) or config.orchestrator.backend
    _backend = _detect_backend(backend_requested)

    if _backend == "api":
        print_info("Backend: Anthropic API (ANTHROPIC_API_KEY)")
    else:
        print_info("Backend: Claude subscription (claude login)")

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
    # C2: Initialize RunState early (before interview) so interrupted
    # interviews also get state saved.
    # -------------------------------------------------------------------
    from .state import RunState
    _current_state = RunState(task=args.task or "", depth=args.depth or "pending")
    _current_state.current_phase = "init"
    _current_state.artifacts["cwd"] = cwd

    # Persist the original task text early so verification can access it
    # even if the run is interrupted before completion.
    try:
        from .state import save_state
        save_state(_current_state, directory=str(Path(cwd) / ".agent-team"))
    except Exception:
        pass  # Non-critical — verification falls back to REQUIREMENTS.md only

    if args.config:
        _current_state.artifacts["config_path"] = args.config
    if args.prd:
        _current_state.artifacts["prd_path"] = args.prd
    if design_ref_urls:
        _current_state.artifacts["design_ref_urls"] = ",".join(design_ref_urls)

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
                backend=_backend,
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

    if interview_doc:
        interview_urls = _extract_design_urls_from_interview(interview_doc)
        if interview_urls:
            design_ref_urls.extend(interview_urls)
            design_ref_urls = list(dict.fromkeys(design_ref_urls))
            print_info(f"Extracted {len(interview_urls)} design reference URL(s) from interview")
            # Update state with merged URLs
            _current_state.artifacts["design_ref_urls"] = ",".join(design_ref_urls)

    _current_state.completed_phases.append("interview")
    _current_state.current_phase = "constraints"

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

    _current_state.completed_phases.append("constraints")
    _current_state.current_phase = "codebase_map"

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

    _current_state.completed_phases.append("codebase_map")
    _current_state.current_phase = "pre_orchestration"

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
                contract_registry.file_missing = True
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
                # Persist integration tasks back to TASKS.md
                if schedule_info.integration_tasks and schedule_info.tasks:
                    task_map = {t.id: t for t in schedule_info.tasks}
                    integration_blocks: list[str] = []
                    for tid in schedule_info.integration_tasks:
                        t = task_map.get(tid)
                        if t:
                            block = (
                                f"\n### {t.id}: {t.title}\n"
                                f"- Status: {t.status}\n"
                                f"- Dependencies: {', '.join(t.depends_on)}\n"
                                f"- Files: {', '.join(t.files)}\n"
                                f"- Agent: {t.assigned_agent or 'integration-agent'}\n\n"
                                f"{t.description}\n"
                            )
                            integration_blocks.append(block)
                    if integration_blocks:
                        tasks_path.write_text(
                            tasks_content + "\n" + "\n".join(integration_blocks),
                            encoding="utf-8",
                        )
                        print_info(f"Appended {len(integration_blocks)} integration task(s) to TASKS.md.")
            else:
                print_info("No TASKS.md found -- scheduler will be used post-orchestration.")
        except Exception as exc:
            print_warning(f"Scheduler failed: {exc}")

    _current_state.completed_phases.append("pre_orchestration")
    _current_state.current_phase = "orchestration"

    # M1: Capture pre-orchestration review cycles for staleness detection (Issue #1, #2)
    pre_orchestration_cycles = 0
    try:
        _pre_report = _check_convergence_health(cwd, config)
        pre_orchestration_cycles = _pre_report.review_cycles
    except Exception:
        pass  # Best-effort — new projects have no REQUIREMENTS.md yet

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

        # Start intervention queue — reads stdin in a daemon thread and
        # queues lines prefixed with "!!".  Queued messages are drained
        # after each orchestrator turn via _drain_interventions().
        intervention.start()
        if sys.stdin.isatty():
            print_intervention_hint()

        # Update phase to orchestration
        if _current_state:
            _current_state.current_phase = "orchestration"

        run_cost = 0.0
        _use_milestones = False
        milestone_convergence_report: ConvergenceReport | None = None
        try:
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
                    intervention=intervention,
                    resume_context=_resume_ctx,
                    task_text=args.task,
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

                # Apply depth-based quality gating (QUICK disables quality features)
                apply_depth_quality_gating(depth, config)

                # Route to milestone loop if PRD mode + milestone feature enabled
                _is_prd_mode = bool(args.prd) or interview_scope == "COMPLEX"
                _master_plan_exists = (
                    Path(cwd) / config.convergence.requirements_dir
                    / config.convergence.master_plan_file
                ).is_file()
                _use_milestones = (
                    config.milestone.enabled
                    and (_is_prd_mode or _master_plan_exists)
                )

                if _use_milestones:
                    print_info("Milestone orchestration enabled — entering per-milestone loop")
                    run_cost, milestone_convergence_report = asyncio.run(_run_prd_milestones(
                        task=task,
                        config=config,
                        cwd=cwd,
                        depth=depth,
                        prd_path=args.prd,
                        interview_doc=interview_doc,
                        codebase_map_summary=codebase_map_summary,
                        constraints=constraints,
                        intervention=intervention,
                        design_reference_urls=design_ref_urls or None,
                    ))
                else:
                    # Format schedule for prompt injection (if available)
                    _schedule_str = None
                    if schedule_info is not None:
                        try:
                            from .scheduler import format_schedule_for_prompt
                            _schedule_str = format_schedule_for_prompt(schedule_info)
                        except (ImportError, Exception):
                            pass
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
                        intervention=intervention,
                        resume_context=_resume_ctx,
                        task_text=args.task,
                        schedule_info=_schedule_str,
                    ))
        except Exception as exc:
            # Root Cause #1: ProcessError (or any exception) during orchestration
            # must NOT prevent post-orchestration (verification, state cleanup)
            # from running. Catch and record the error, then continue.
            print_warning(f"Orchestration interrupted: {exc}")
            if _current_state:
                _current_state.interrupted = True
                _current_state.error_context = str(exc)
                run_cost = _current_state.total_cost

        # Update RunState with actual cost from orchestration
        if _current_state:
            _current_state.total_cost = run_cost or 0.0

        # Persist state to disk after orchestration (success or failure)
        if _current_state:
            try:
                from .state import save_state
                save_state(_current_state, directory=str(Path(cwd) / ".agent-team"))
            except Exception:
                pass  # Best-effort state save

        # Update phase after orchestration
        if _current_state:
            _current_state.completed_phases.append("orchestration")
            _current_state.current_phase = "post_orchestration"
        if design_ref_urls and _current_state:
            req_path = Path(cwd) / config.convergence.requirements_dir / config.convergence.requirements_file
            if req_path.is_file() and "## Design Reference" in req_path.read_text(encoding="utf-8"):
                _current_state.artifacts["design_research_complete"] = "true"

    finally:
        # Stop intervention queue
        intervention.stop()

    # -------------------------------------------------------------------
    # Post-orchestration: TASKS.md diagnostic (replaces blind mark-all)
    # -------------------------------------------------------------------
    recovery_types: list[str] = []

    if config.scheduler.enabled:
        try:
            from .scheduler import parse_tasks_md

            tasks_path = (
                Path(cwd) / config.convergence.requirements_dir / "TASKS.md"
            )
            if tasks_path.is_file():
                tasks_content = tasks_path.read_text(encoding="utf-8")
                parsed_tasks = parse_tasks_md(tasks_content)
                pending_count = sum(1 for t in parsed_tasks if t.status == "PENDING")
                complete_count = sum(1 for t in parsed_tasks if t.status == "COMPLETE")
                total_tasks = len(parsed_tasks)
                if pending_count > 0:
                    # M2: Task Status Staleness Warning with IDs (Issue #3)
                    pending_ids = [t.id for t in parsed_tasks if t.status == "PENDING"]
                    id_preview = ", ".join(pending_ids[:5])
                    if len(pending_ids) > 5:
                        id_preview += f"... (+{len(pending_ids) - 5} more)"
                    print_warning(
                        f"TASK STATUS WARNING: {pending_count}/{total_tasks} tasks still PENDING: "
                        f"{id_preview}"
                    )
                    print_info(
                        "Code-writers should have marked their own tasks COMPLETE during execution."
                    )
                else:
                    print_info(f"TASKS.md: All {total_tasks} tasks marked COMPLETE.")
        except Exception as exc:
            print_warning(f"Task status diagnostic failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Contract health check
    # -------------------------------------------------------------------
    if config.verification.enabled:
        contract_path = (
            Path(cwd) / config.convergence.requirements_dir
            / config.verification.contract_file
        )
        req_path = (
            Path(cwd) / config.convergence.requirements_dir
            / config.convergence.requirements_file
        )
        # Only attempt recovery if REQUIREMENTS.md exists (architecture phase ran)
        # and contract-generator is enabled in config
        from .config import AgentConfig as _AgentConfig
        generator_enabled = config.agents.get(
            "contract_generator", _AgentConfig()
        ).enabled
        has_requirements = req_path.is_file() or _has_milestone_requirements(cwd, config)

        if not contract_path.is_file() and has_requirements and generator_enabled:
            print_warning("RECOVERY PASS [contract_generation]: CONTRACTS.json not found after orchestration.")
            recovery_types.append("contract_generation")
            try:
                recovery_cost = _run_contract_generation(
                    cwd=cwd,
                    config=config,
                    constraints=constraints,
                    intervention=intervention,
                    task_text=args.task,
                    milestone_mode=_use_milestones,
                )
                if _current_state:
                    _current_state.total_cost += recovery_cost
                # H1: Post-recovery verification (Issue #4, #9)
                if not contract_path.is_file():
                    print_error(
                        "CONTRACT RECOVERY FAILED: CONTRACTS.json not created after recovery pass"
                    )
                else:
                    try:
                        with open(contract_path, encoding="utf-8") as f:
                            json.load(f)
                        print_success(
                            "Contract recovery verified: CONTRACTS.json created successfully"
                        )
                    except json.JSONDecodeError:
                        print_error(
                            "CONTRACT RECOVERY FAILED: CONTRACTS.json is invalid JSON"
                        )
            except Exception as exc:
                print_warning(f"Contract generation recovery failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Convergence health check (Root Cause #2)
    # -------------------------------------------------------------------
    if _use_milestones:
        if milestone_convergence_report is not None:
            convergence_report = milestone_convergence_report
        else:
            # Milestones enabled but report not returned — aggregate from disk
            from .milestone_manager import MilestoneManager, aggregate_milestone_convergence
            _mm_fallback = MilestoneManager(Path(cwd))
            convergence_report = aggregate_milestone_convergence(
                _mm_fallback,
                min_convergence_ratio=config.convergence.min_convergence_ratio,
                degraded_threshold=config.convergence.degraded_threshold,
            )
            # H2: Per-milestone display in fallback path (Issue #7)
            _display_per_milestone_health(cwd, config)
    else:
        convergence_report = _check_convergence_health(cwd, config)
    if _current_state:
        _current_state.convergence_cycles = convergence_report.review_cycles
        _current_state.requirements_checked = convergence_report.checked_requirements
        _current_state.requirements_total = convergence_report.total_requirements

    # Display convergence health panel
    if _use_milestones and milestone_convergence_report is not None:
        # Show per-milestone breakdown before the aggregate
        _display_per_milestone_health(cwd, config)

    print_convergence_health(
        health=convergence_report.health,
        req_passed=convergence_report.checked_requirements,
        req_total=convergence_report.total_requirements,
        review_cycles=convergence_report.review_cycles,
        escalated_items=convergence_report.escalated_items,
        zero_cycle_milestones=convergence_report.zero_cycle_milestones,
    )

    # H3: Unknown Health Investigation (Issue #12)
    # When health is unknown, investigate and log specific reason
    if convergence_report.health == "unknown":
        if _use_milestones:
            milestones_dir = Path(cwd) / config.convergence.requirements_dir / "milestones"
            if not milestones_dir.exists():
                print_warning(
                    "UNKNOWN HEALTH: .agent-team/milestones/ directory does not exist"
                )
            else:
                ms_with_reqs = [
                    d.name for d in milestones_dir.iterdir()
                    if d.is_dir() and (d / config.convergence.requirements_file).is_file()
                ]
                if not ms_with_reqs:
                    print_warning(
                        f"UNKNOWN HEALTH: No milestone has {config.convergence.requirements_file}"
                    )
                else:
                    print_warning(
                        f"UNKNOWN HEALTH: Milestones exist ({len(ms_with_reqs)}) "
                        "but aggregation returned 0 requirements"
                    )
        else:
            req_path = (
                Path(cwd) / config.convergence.requirements_dir
                / config.convergence.requirements_file
            )
            if not req_path.is_file():
                print_warning(
                    f"UNKNOWN HEALTH: {config.convergence.requirements_dir}/"
                    f"{config.convergence.requirements_file} does not exist"
                )
            else:
                print_warning(
                    f"UNKNOWN HEALTH: {config.convergence.requirements_file} exists "
                    "but contains no checkable items"
                )

    # Log escalated items if any
    if convergence_report.escalated_items:
        print_warning(
            f"Escalation-worthy items still unchecked ({len(convergence_report.escalated_items)}): "
            + ", ".join(convergence_report.escalated_items)
        )

    # Gate validation: log warning if review fleet was never deployed
    if (
        convergence_report.review_cycles == 0
        and convergence_report.total_requirements > 0
    ):
        print_warning(
            "GATE VIOLATION: Review fleet was never deployed "
            f"({convergence_report.total_requirements} requirements, 0 review cycles). "
            "GATE 5 enforcement will trigger recovery."
        )

    # M1: Review Cycles Staleness Detection (Issue #1, #2)
    # Warn if review_cycles didn't increase during orchestration
    if (
        convergence_report.review_cycles == pre_orchestration_cycles
        and convergence_report.total_requirements > 0
        and pre_orchestration_cycles > 0  # Only if there were previous cycles
    ):
        print_warning(
            f"STALENESS WARNING: review_cycles unchanged at {convergence_report.review_cycles}. "
            "Review fleet may not have evaluated items this run."
        )

    recovery_threshold = config.convergence.recovery_threshold
    needs_recovery = False

    if convergence_report.health == "failed":
        if convergence_report.review_cycles == 0 and convergence_report.total_requirements > 0:
            # Zero-cycle failure: review fleet was never deployed
            needs_recovery = True
        elif (
            convergence_report.review_cycles > 0
            and convergence_report.total_requirements > 0
            and convergence_report.convergence_ratio < recovery_threshold
        ):
            # Partial-review failure: deployed but insufficient coverage
            needs_recovery = True
        else:
            print_warning(
                f"Convergence failed: {convergence_report.checked_requirements}/"
                f"{convergence_report.total_requirements} requirements checked "
                f"({convergence_report.review_cycles} review cycles)."
            )
    elif convergence_report.health == "unknown":
        # PRD mode may return "unknown" if no top-level REQUIREMENTS.md exists
        milestones_dir = Path(cwd) / config.convergence.requirements_dir / "milestones"
        if milestones_dir.is_dir() and any(milestones_dir.iterdir()):
            # Milestones exist but health is unknown — treat as potential failure
            print_warning(
                "Convergence health: unknown (milestone requirements may not have been aggregated). "
                "Triggering recovery pass."
            )
            needs_recovery = True
        else:
            print_warning("Convergence health: unknown (no requirements found).")
    elif convergence_report.health == "degraded":
        if (
            convergence_report.total_requirements > 0
            and convergence_report.convergence_ratio < recovery_threshold
        ):
            # Degraded but below recovery threshold — trigger recovery
            needs_recovery = True
        else:
            print_info(
                f"Convergence partial: {convergence_report.checked_requirements}/"
                f"{convergence_report.total_requirements} requirements checked "
                f"({convergence_report.review_cycles} review cycles)."
            )

    if needs_recovery:
        print_warning(
            f"RECOVERY PASS [review_recovery]: {convergence_report.checked_requirements}/"
            f"{convergence_report.total_requirements} requirements checked "
            f"({convergence_report.review_cycles} review cycles). Launching recovery pass."
        )
        recovery_types.append("review_recovery")
        pre_recovery_cycles = convergence_report.review_cycles
        try:
            recovery_cost = _run_review_only(
                cwd=cwd,
                config=config,
                constraints=constraints,
                intervention=intervention,
                task_text=args.task,
                checked=convergence_report.checked_requirements,
                total=convergence_report.total_requirements,
                review_cycles=convergence_report.review_cycles,
            )
            if _current_state:
                _current_state.total_cost += recovery_cost
            # Re-check health after recovery
            if _use_milestones:
                from .milestone_manager import MilestoneManager as _MM2, aggregate_milestone_convergence as _agg
                convergence_report = _agg(
                    _MM2(Path(cwd)),
                    min_convergence_ratio=config.convergence.min_convergence_ratio,
                    degraded_threshold=config.convergence.degraded_threshold,
                )
            else:
                convergence_report = _check_convergence_health(cwd, config)
            if _current_state:
                _current_state.convergence_cycles = convergence_report.review_cycles
                _current_state.requirements_checked = convergence_report.checked_requirements
            # Verify cycle counter actually increased
            if convergence_report.review_cycles <= pre_recovery_cycles:
                print_warning(
                    f"Review recovery did not increment cycle counter "
                    f"(before: {pre_recovery_cycles}, after: {convergence_report.review_cycles})."
                )
        except Exception as exc:
            print_warning(f"Review recovery pass failed: {exc}")

    # Display recovery report if any recovery passes were triggered
    if recovery_types:
        print_recovery_report(len(recovery_types), recovery_types)

    if _current_state:
        _current_state.completed_phases.append("post_orchestration")
        _current_state.current_phase = "verification"

    # -------------------------------------------------------------------
    # Post-orchestration: Verification (if enabled)
    # -------------------------------------------------------------------
    # Re-read contracts from disk — the orchestrator (or recovery pass)
    # may have created CONTRACTS.json during execution.
    if config.verification.enabled:
        try:
            from .contracts import load_contracts as _load_contracts
            _contract_path = (
                Path(cwd) / config.convergence.requirements_dir
                / config.verification.contract_file
            )
            contract_registry = _load_contracts(_contract_path)
        except Exception:
            from .contracts import ContractRegistry as _CR
            contract_registry = _CR()
            contract_registry.file_missing = True

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
                run_build=config.verification.run_build,
                run_lint=config.verification.run_lint,
                run_type_check=config.verification.run_type_check,
                run_tests=config.verification.run_tests,
                run_security=config.verification.run_security,
                run_quality_checks=config.verification.run_quality_checks,
                blocking=config.verification.blocking,
                min_test_count=config.verification.min_test_count,
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

            # Quality feedback reloop: if quality_health is needs-attention
            # and quality_triggers_reloop is enabled, trigger a quality fix pass
            if (
                config.quality.quality_triggers_reloop
                and result.quality_health == "needs-attention"
            ):
                print_warning(
                    f"Quality health: {result.quality_health} — "
                    "4+ quality violations detected. Consider running a quality fix pass."
                )
        except Exception as exc:
            print_warning(f"Post-orchestration verification failed: {exc}")

    if _current_state:
        _current_state.completed_phases.append("verification")
        _current_state.current_phase = "complete"

    # -------------------------------------------------------------------
    # Clear STATE.json on successful completion
    # -------------------------------------------------------------------
    from .state import clear_state
    clear_state()
