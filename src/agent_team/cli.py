"""CLI entry point for Agent Team.

Handles argument parsing, depth detection, interactive/single-shot modes,
signal handling, and cost tracking.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import queue
import re
import shutil
import signal
import string
import subprocess
import sys
import threading
import traceback
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
from .state import BrowserTestReport, ConvergenceReport, E2ETestReport, WorkflowResult
from .e2e_testing import (
    detect_app_type,
    parse_e2e_results,
    BACKEND_E2E_PROMPT,
    FRONTEND_E2E_PROMPT,
    E2E_FIX_PROMPT,
)
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
from .mcp_servers import (
    _BASE_TOOLS,
    get_mcp_servers,
    get_orchestrator_st_tool_name,
    get_research_tools,
    recompute_allowed_tools,
)
from .audit_team import (
    AuditFinding,
    AuditTeamReport,
    build_audit_fix_prompt,
    filter_findings_for_fix,
    get_active_auditors,
    get_auditor_prompt,
    group_findings_by_file,
    parse_all_audit_reports,
    score_audit_findings,
)
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


_DESIGN_SECTION_RE = re.compile(
    r"^##\s+(design\s+reference|design|ui/?ux|visual\s+design|style\s+guide"
    r"|references|mockups?|figma|design\s+system)",
    re.IGNORECASE,
)

_DESIGN_URL_DOMAINS = frozenset({
    "figma.com", "dribbble.com", "behance.net", "sketch.cloud",
    "zeplin.io", "invisionapp.com", "framer.com", "canva.com",
})


def _extract_design_urls_from_interview(doc_content: str) -> list[str]:
    """Extract design reference URLs from a document.

    First scans for URLs under design-related section headers.  If none are
    found, falls back to extracting URLs from known design-platform domains
    anywhere in the document.
    """
    urls: list[str] = []
    in_section = False
    for line in doc_content.splitlines():
        stripped = line.strip()
        if _DESIGN_SECTION_RE.match(stripped):
            in_section = True
            continue
        if in_section and stripped.startswith("## ") and not _DESIGN_SECTION_RE.match(stripped):
            break
        if in_section:
            for match in _URL_RE.finditer(line):
                urls.append(match.group(0).rstrip(".,;:!?)"))

    if urls:
        return list(dict.fromkeys(urls))

    # Fallback: extract URLs from known design platforms anywhere in doc
    from urllib.parse import urlparse

    for match in _URL_RE.finditer(doc_content):
        url = match.group(0).rstrip(".,;:!?)")
        try:
            domain = urlparse(url).netloc.lower()
            if any(d in domain for d in _DESIGN_URL_DOMAINS):
                urls.append(url)
        except Exception:
            pass
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
        "allowed_tools": recompute_allowed_tools(_BASE_TOOLS, mcp_servers),
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
    ui_requirements_content: str | None = None,
    user_overrides: set[str] | None = None,
) -> float:
    """Run the interactive multi-turn conversation loop. Returns total cost."""
    # Apply depth-based quality gating for initial depth
    apply_depth_quality_gating(depth_override or "standard", config, user_overrides)
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
                ui_requirements_content=ui_requirements_content,
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
                ui_requirements_content=ui_requirements_content,
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
    ui_requirements_content: str | None = None,
    tech_research_content: str = "",
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
        ui_requirements_content=ui_requirements_content,
        tech_research_content=tech_research_content,
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


async def _run_tech_research(
    cwd: str | None,
    config: AgentTeamConfig,
    prd_text: str,
    master_plan_text: str,
    depth: str,
) -> tuple[float, "TechResearchResult | None"]:
    """Run Phase 1.5: Tech Stack Research via Context7.

    Detects the tech stack, builds research queries, runs a sub-orchestrator
    with Context7 MCP, parses the result, and validates coverage.

    Returns ``(cost, result)`` where *result* is ``None`` on failure.
    """
    from .tech_research import (
        TechResearchResult,
        build_research_queries,
        build_expanded_research_queries,
        detect_tech_stack,
        extract_research_summary,
        parse_tech_research_file,
        validate_tech_research,
        TECH_RESEARCH_PROMPT,
    )
    from .mcp_servers import get_context7_only_servers

    project_root = Path(cwd or ".")
    req_dir = project_root / config.convergence.requirements_dir

    # 1. Detect tech stack
    stack = detect_tech_stack(
        cwd=project_root,
        prd_text=prd_text,
        master_plan_text=master_plan_text,
        max_techs=config.tech_research.max_techs,
    )

    if not stack:
        print_info("Phase 1.5: No technologies detected — skipping research")
        return 0.0, None

    tech_names = [f"{e.name} (v{e.version})" if e.version else e.name for e in stack]
    print_info(f"Phase 1.5: Tech Stack Research — {len(stack)} technologies: {', '.join(tech_names)}")

    # 2. Build queries (basic + expanded)
    queries = build_research_queries(stack, max_per_tech=config.tech_research.max_queries_per_tech)

    # Add expanded queries (best practices, integration, PRD-aware) when enabled
    if config.tech_research.expanded_queries:
        expanded = build_expanded_research_queries(
            stack=stack,
            prd_text=prd_text,
            max_expanded_per_tech=config.tech_research.max_expanded_queries,
        )
        queries.extend(expanded)

    # 3. Format prompt
    tech_list = "\n".join(
        f"- **{e.name}** {('v' + e.version) if e.version else '(version unknown)'} [{e.category}]"
        for e in stack
    )

    queries_by_tech: dict[str, list[str]] = {}
    for lib_name, query in queries:
        queries_by_tech.setdefault(lib_name, []).append(query)

    queries_block_parts: list[str] = []
    for tech_name, tech_queries in queries_by_tech.items():
        queries_block_parts.append(f"\n### {tech_name}")
        for i, q in enumerate(tech_queries, 1):
            queries_block_parts.append(f"{i}. {q}")
    queries_block = "\n".join(queries_block_parts)

    output_path = str(req_dir / "TECH_RESEARCH.md")
    research_prompt = TECH_RESEARCH_PROMPT.format(
        tech_list=tech_list,
        queries_block=queries_block,
        output_path=output_path,
    )

    # 4. Run sub-orchestrator with Context7 MCP
    context7_servers = get_context7_only_servers(config)
    if not context7_servers:
        print_warning("Phase 1.5: Context7 MCP not available — skipping research")
        return 0.0, None

    research_options = ClaudeAgentOptions(
        model=config.orchestrator.model,
        max_turns=50,
        permission_mode="bypassPermissions",
        mcp_servers=context7_servers,
    )
    if cwd:
        research_options.cwd = cwd

    total_cost = 0.0
    phase_costs: dict[str, float] = {}

    try:
        async with ClaudeSDKClient(options=research_options) as client:
            await client.query(research_prompt)
            total_cost = await _process_response(client, config, phase_costs)
    except Exception as exc:
        print_warning(f"Phase 1.5: Research sub-orchestrator failed: {exc}")
        return total_cost, None

    # 5. Parse results
    output_file = Path(output_path)
    if not output_file.is_file():
        print_warning("Phase 1.5: TECH_RESEARCH.md not created — research incomplete")
        return total_cost, None

    try:
        file_content = output_file.read_text(encoding="utf-8")
    except OSError:
        print_warning("Phase 1.5: Could not read TECH_RESEARCH.md")
        return total_cost, None

    result = parse_tech_research_file(file_content)
    result.stack = stack
    result.techs_total = len(stack)
    result.queries_made = len(queries)
    result.output_path = output_path

    # 6. Validate coverage
    is_valid, missing = validate_tech_research(result)

    if not is_valid and config.tech_research.retry_on_incomplete:
        print_warning(
            f"Phase 1.5: Research coverage below threshold — "
            f"missing: {', '.join(missing)}. Retrying..."
        )
        # Retry once with just the missing techs
        try:
            async with ClaudeSDKClient(options=research_options) as client:
                retry_prompt = (
                    f"FIRST read the existing file at {output_path} to see what's already there.\n"
                    f"Then ADD sections for these missing technologies:\n"
                    f"{', '.join(missing)}\n\n"
                    f"Write the COMPLETE file back to {output_path} — keep ALL existing sections "
                    f"and add the new ones using the same ## TechName (vVersion) format.\n"
                    f"Do NOT remove or overwrite existing sections."
                )
                await client.query(retry_prompt)
                retry_cost = await _process_response(client, config, phase_costs)
                total_cost += retry_cost
        except Exception:
            pass  # Best-effort retry

        # Re-parse after retry
        try:
            file_content = output_file.read_text(encoding="utf-8")
            result = parse_tech_research_file(file_content)
            result.stack = stack
            result.techs_total = len(stack)
            result.queries_made = len(queries)
            result.output_path = output_path
            validate_tech_research(result)
        except OSError:
            pass

    print_info(
        f"Phase 1.5: Research complete — "
        f"{result.techs_covered}/{result.techs_total} technologies covered"
    )

    return total_cost, result


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
    ui_requirements_content: str | None = None,
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

        # Pre-create analysis directory for chunked decomposition
        if prd_chunks:
            analysis_dir = req_dir / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)

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
            ui_requirements_content=ui_requirements_content,
        )

        options = _build_options(config, cwd, constraints=constraints, task_text=task, depth=depth, backend=_backend)
        phase_costs: dict[str, float] = {}

        async with ClaudeSDKClient(options=options) as client:
            await client.query(decomp_prompt)
            decomp_cost = await _process_response(client, config, phase_costs)
            if intervention:
                decomp_cost += await _drain_interventions(client, intervention, config, phase_costs)
            total_cost += decomp_cost

        # Validate analysis files for chunked PRDs (Fix RC-1)
        if prd_chunks:
            analysis_dir = req_dir / "analysis"
            min_expected = max(1, (len(prd_chunks) + 1) // 2)  # At least half (ceil division)
            if analysis_dir.is_dir():
                analysis_files = list(analysis_dir.glob("*.md"))
                if len(analysis_files) < min_expected:
                    print_warning(
                        f"Chunked PRD analysis incomplete: {len(analysis_files)}/{len(prd_chunks)} "
                        f"analysis files (need {min_expected}). "
                        f"Re-running decomposition for missing chunks."
                    )
                    # Retry: re-deploy decomposition once for missing analysis files
                    retry_prompt = build_decomposition_prompt(
                        task=task, depth=depth, config=config,
                        prd_path=prd_path, cwd=cwd,
                        interview_doc=interview_doc,
                        codebase_map_summary=codebase_map_summary,
                        design_reference_urls=design_reference_urls,
                        prd_chunks=prd_chunks, prd_index=prd_index,
                        ui_requirements_content=ui_requirements_content,
                    )
                    retry_options = _build_options(
                        config, cwd, constraints=constraints,
                        task_text=task, depth=depth, backend=_backend,
                    )
                    retry_phase_costs: dict[str, float] = {}
                    try:
                        async with ClaudeSDKClient(options=retry_options) as retry_client:
                            await retry_client.query(retry_prompt)
                            retry_cost = await _process_response(
                                retry_client, config, retry_phase_costs,
                            )
                            total_cost += retry_cost
                    except Exception as exc:
                        print_warning(f"Analysis retry failed: {exc}")
                    # Re-check after retry
                    analysis_files = list(analysis_dir.glob("*.md"))
                    if len(analysis_files) < min_expected:
                        print_warning(
                            f"Chunked PRD analysis still incomplete after retry: "
                            f"{len(analysis_files)}/{len(prd_chunks)} analysis files. "
                            f"Synthesizer may produce incomplete MASTER_PLAN.md."
                        )
            else:
                print_warning(
                    f"Chunked PRD analysis directory not created: {analysis_dir}. "
                    "Planners may not have written analysis files to disk."
                )

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
        # Auto-fix: check if milestones use h3/h4 headers instead of h2
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        _h3h4_matches = _h3h4_re.findall(plan_content)
        if _h3h4_matches:
            print_warning(
                f"Auto-fixing {len(_h3h4_matches)} milestone header(s) from "
                f"h3/h4 to h2 in MASTER_PLAN.md"
            )
            plan_content = _h3h4_re.sub(r"## \2", plan_content)
            master_plan_path.write_text(plan_content, encoding="utf-8")
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

    # ------------------------------------------------------------------
    # Phase 1.5: TECH STACK RESEARCH
    # ------------------------------------------------------------------
    tech_research_content = ""
    _detected_tech_stack: list = []  # Preserved for per-milestone research queries
    if config.tech_research.enabled:
        try:
            prd_text_for_research = ""
            if prd_path:
                try:
                    prd_text_for_research = Path(prd_path).read_text(encoding="utf-8")
                except OSError:
                    prd_text_for_research = task
            else:
                prd_text_for_research = task

            research_cost, tech_result = await _run_tech_research(
                cwd=cwd,
                config=config,
                prd_text=prd_text_for_research,
                master_plan_text=plan_content,
                depth=depth,
            )
            total_cost += research_cost

            if tech_result:
                _detected_tech_stack = tech_result.stack
                from .tech_research import extract_research_summary
                tech_research_content = extract_research_summary(
                    tech_result,
                    max_chars=config.tech_research.injection_max_chars,
                )
        except Exception:
            print_warning("Phase 1.5: Tech research failed (non-blocking)")

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

    # Determine resume point
    resume_from = config.milestone.resume_from_milestone
    if not resume_from and _current_state:
        from .state import get_resume_milestone
        resume_from = get_resume_milestone(_current_state)

    # ------------------------------------------------------------------
    # Phase 2: EXECUTION LOOP
    # ------------------------------------------------------------------
    print_info(f"Phase 2: Executing {len(plan.milestones)} milestones")

    # Check for saved progress from a previous interrupted run
    progress_path = req_dir / "milestone_progress.json"
    if progress_path.is_file():
        import json
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            completed_ids = set(progress.get("completed_milestones", []))
            interrupted_id = progress.get("interrupted_milestone")
            if completed_ids:
                print_info(
                    f"Resuming from interrupt: {len(completed_ids)} milestones completed, "
                    f"resuming at milestone {interrupted_id}"
                )
                # Override resume_from to the interrupted milestone
                resume_from = interrupted_id
            progress_path.unlink()  # Clear progress file on resume
        except (json.JSONDecodeError, OSError):
            pass  # Ignore corrupt progress file

    iteration = 0
    max_iterations = len(plan.milestones) + 3  # one full pass + retry headroom

    while not plan.all_complete() and iteration < max_iterations:
        iteration += 1

        # State-based guard: if RunState already has all milestones completed, exit
        if _current_state:
            _all_plan_ids = {m.id for m in plan.milestones}
            _state_completed = set(getattr(_current_state, "completed_milestones", []))
            if _all_plan_ids and _all_plan_ids <= _state_completed:
                print_info("All milestones already recorded as complete in state. Exiting loop.")
                break

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

            # Generate consumption checklist if predecessors exist and handoff is enabled
            if config.tracking_documents.milestone_handoff and predecessor_summaries:
                try:
                    from .tracking_documents import generate_consumption_checklist, parse_handoff_interfaces
                    handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"
                    if handoff_path.is_file():
                        handoff_content = handoff_path.read_text(encoding="utf-8")
                        all_interfaces: list[dict] = []
                        for pred_id in [dep for dep in milestone.dependencies if dep]:
                            interfaces = parse_handoff_interfaces(handoff_content, pred_id)
                            all_interfaces.extend(interfaces)
                        if all_interfaces:
                            checklist = generate_consumption_checklist(
                                milestone_id=milestone.id,
                                milestone_title=milestone.title,
                                predecessor_interfaces=all_interfaces,
                            )
                            handoff_content += "\n\n" + checklist
                            handoff_path.write_text(handoff_content, encoding="utf-8")
                except Exception as exc:
                    print_warning(f"Failed to generate consumption checklist: {exc}")

            # Per-milestone research: generate milestone-specific research content
            ms_research_content = ""
            if config.tech_research.enabled and config.tech_research.expanded_queries:
                try:
                    from .tech_research import build_milestone_research_queries
                    # Read this milestone's requirements for targeted queries
                    _ms_req_path = Path(ms_context.requirements_path) if ms_context else None
                    _ms_req_text = ""
                    if _ms_req_path and _ms_req_path.is_file():
                        try:
                            _ms_req_text = _ms_req_path.read_text(encoding="utf-8")
                        except OSError:
                            pass
                    _ms_title = milestone.title if milestone else ""
                    _ms_queries = build_milestone_research_queries(
                        milestone_title=_ms_title,
                        milestone_requirements=_ms_req_text,
                        tech_stack=_detected_tech_stack,
                    )
                    if _ms_queries:
                        _ms_query_lines = []
                        for lib_name, query in _ms_queries:
                            _ms_query_lines.append(f"- **{lib_name}**: {query}")
                        ms_research_content = (
                            "Milestone-specific research queries (use Context7 to look these up):\n"
                            + "\n".join(_ms_query_lines)
                        )
                except Exception:
                    pass  # Non-critical: milestone research is best-effort

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
                ui_requirements_content=ui_requirements_content,
                tech_research_content=tech_research_content,
                milestone_research_content=ms_research_content,
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
            except KeyboardInterrupt:
                # Save progress for resume on user interrupt
                completed_ids = [m.id for m in plan.milestones if m.status == "COMPLETE"]
                _save_milestone_progress(
                    cwd=cwd,
                    config=config,
                    milestone_id=milestone.id,
                    completed_milestones=completed_ids,
                    error_type="KeyboardInterrupt",
                )
                print_warning(
                    f"Milestone {milestone.id} interrupted by user. "
                    f"Progress saved. Run again to resume from this milestone."
                )
                break  # Exit milestone loop
            except Exception as exc:
                # Save progress for resume on unexpected errors
                completed_ids = [m.id for m in plan.milestones if m.status == "COMPLETE"]
                _save_milestone_progress(
                    cwd=cwd,
                    config=config,
                    milestone_id=milestone.id,
                    completed_milestones=completed_ids,
                    error_type=type(exc).__name__,
                )
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

            # Normalize milestone directories after execution
            try:
                from .milestone_manager import normalize_milestone_dirs
                _norm = normalize_milestone_dirs(project_root, config.convergence.requirements_dir)
                if _norm > 0:
                    print_info(f"Normalized {_norm} milestone directory path(s)")
            except Exception:
                pass  # Best-effort normalization

            # TASKS.md existence check (Fix RC-2 hardening)
            ms_tasks_path = milestones_dir / milestone.id / "TASKS.md"
            if not ms_tasks_path.is_file():
                print_warning(
                    f"Milestone {milestone.id}: TASKS.md not created at {ms_tasks_path}. "
                    f"Task decomposition step may have been skipped."
                )

            # Health check (if gate enabled)
            health_report = mm.check_milestone_health(
                milestone.id,
                min_convergence_ratio=config.convergence.min_convergence_ratio,
            )

            # Review recovery loop (mirrors post-orchestration recovery in main flow)
            if config.milestone.health_gate and health_report and health_report.health in ("failed", "degraded"):
                needs_recovery = (
                    (health_report.review_cycles == 0 and health_report.total_requirements > 0)
                    or (
                        health_report.total_requirements > 0
                        and health_report.convergence_ratio < config.convergence.recovery_threshold
                    )
                )

                if needs_recovery:
                    max_recovery = config.milestone.review_recovery_retries
                    ms_req_path = str(
                        milestones_dir / milestone.id / config.convergence.requirements_file
                    )
                    for recovery_attempt in range(max_recovery):
                        print_warning(
                            f"Milestone {milestone.id} review recovery "
                            f"(attempt {recovery_attempt + 1}/{max_recovery}): "
                            f"{health_report.checked_requirements}/{health_report.total_requirements} "
                            f"checked, {health_report.review_cycles} review cycles."
                        )
                        try:
                            recovery_cost = await _run_review_only(
                                cwd=cwd,
                                config=config,
                                constraints=constraints,
                                intervention=intervention,
                                task_text=task,
                                checked=health_report.checked_requirements,
                                total=health_report.total_requirements,
                                review_cycles=health_report.review_cycles,
                                requirements_path=ms_req_path,
                                depth=depth,
                            )
                            total_cost += recovery_cost
                        except Exception as exc:
                            print_warning(
                                f"Milestone {milestone.id} review recovery failed: {exc}"
                            )
                            break

                        # Re-check health after recovery
                        health_report = mm.check_milestone_health(
                            milestone.id,
                            min_convergence_ratio=config.convergence.min_convergence_ratio,
                        )
                        # Break if healthy, or degraded but above recovery threshold
                        if health_report.health == "healthy":
                            break
                        if (
                            health_report.health == "degraded"
                            and health_report.convergence_ratio >= config.convergence.recovery_threshold
                        ):
                            break
                    else:
                        # All recovery attempts exhausted without sufficient improvement
                        print_warning(
                            f"Milestone {milestone.id}: all {max_recovery} review recovery "
                            f"attempts exhausted. Health: {health_report.health}, "
                            f"ratio: {health_report.convergence_ratio:.2f}."
                        )

            # Per-milestone audit-team review (after review recovery, before handoff)
            if config.audit_team.enabled and config.audit_team.per_milestone:
                try:
                    ms_req_path_audit = str(
                        milestones_dir / milestone.id / config.convergence.requirements_file
                    )
                    audit_cost, audit_report = await _run_audit_team(
                        cwd=cwd,
                        config=config,
                        depth=depth,
                        constraints=constraints,
                        intervention=intervention,
                        task_text=task,
                        requirements_path=ms_req_path_audit,
                        scope_label=f"milestone:{milestone.id}",
                    )
                    total_cost += audit_cost
                    if _current_state:
                        _current_state.artifacts[f"audit_{milestone.id}_health"] = audit_report.health
                        _current_state.artifacts[f"audit_{milestone.id}_score"] = f"{audit_report.overall_score:.2f}"
                    if audit_report.health == "critical":
                        print_warning(
                            f"Milestone {milestone.id} audit-team health: critical "
                            f"(score={audit_report.overall_score:.2f}). "
                            f"FAIL={audit_report.total_fail}, PARTIAL={audit_report.total_partial}."
                        )
                except Exception as exc:
                    print_warning(
                        f"Milestone {milestone.id} audit-team failed: {exc}\n"
                        f"{traceback.format_exc()}"
                    )

            # Generate/update MILESTONE_HANDOFF.md (after review recovery, before wiring check)
            if config.tracking_documents.milestone_handoff:
                try:
                    from .tracking_documents import generate_milestone_handoff_entry
                    handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"

                    entry = generate_milestone_handoff_entry(
                        milestone_id=milestone.id,
                        milestone_title=milestone.title,
                        status="COMPLETE",
                    )

                    if handoff_path.is_file():
                        existing = handoff_path.read_text(encoding="utf-8")
                        if f"## {milestone.id}:" not in existing:
                            handoff_path.write_text(existing + "\n\n---\n\n" + entry, encoding="utf-8")
                    else:
                        header = (
                            "# Milestone Handoff Registry\n\n"
                            "This document tracks interfaces exposed by each milestone.\n"
                            "Subsequent milestones MUST read this before coding.\n\n---\n\n"
                        )
                        handoff_path.write_text(header + entry, encoding="utf-8")

                    print_info(f"Updated MILESTONE_HANDOFF.md with {milestone.id}")

                    # Run sub-orchestrator to fill handoff details
                    ms_req_path_for_handoff = str(
                        milestones_dir / milestone.id / config.convergence.requirements_file
                    )
                    handoff_cost = await _generate_handoff_details(
                        cwd=cwd,
                        config=config,
                        milestone_id=milestone.id,
                        milestone_title=milestone.title,
                        requirements_path=ms_req_path_for_handoff,
                        task_text=task,
                        constraints=constraints,
                        intervention=intervention,
                        depth=depth,
                    )
                    total_cost += handoff_cost

                    # Validate handoff completeness — retry once if still a template
                    from .tracking_documents import validate_handoff_completeness
                    _ho_content = handoff_path.read_text(encoding="utf-8")
                    _ho_ok, _ho_unfilled = validate_handoff_completeness(_ho_content, milestone.id)

                    if not _ho_ok:
                        print_warning(
                            f"Handoff for {milestone.id} incomplete "
                            f"(unfilled: {', '.join(_ho_unfilled)}). Retrying..."
                        )
                        retry_cost = await _generate_handoff_details(
                            cwd=cwd,
                            config=config,
                            milestone_id=milestone.id,
                            milestone_title=milestone.title,
                            requirements_path=ms_req_path_for_handoff,
                            task_text=task,
                            constraints=constraints,
                            intervention=intervention,
                            depth=depth,
                        )
                        total_cost += retry_cost
                        _ho_content = handoff_path.read_text(encoding="utf-8")
                        _ho_ok, _ho_unfilled = validate_handoff_completeness(
                            _ho_content, milestone.id,
                        )
                        if _ho_ok:
                            print_info(f"Handoff for {milestone.id} filled on retry.")
                        else:
                            print_warning(
                                f"Handoff for {milestone.id} still incomplete after retry. "
                                f"Unfilled: {', '.join(_ho_unfilled)}. Continuing."
                            )
                    else:
                        print_info(f"Handoff for {milestone.id} validated — key sections filled.")
                except Exception as exc:
                    print_warning(f"Failed to update MILESTONE_HANDOFF.md: {exc}")

            # Check wiring completeness from handoff document
            if config.tracking_documents.milestone_handoff and config.tracking_documents.wiring_completeness_gate > 0:
                try:
                    from .tracking_documents import compute_wiring_completeness
                    handoff_path = Path(cwd) / config.convergence.requirements_dir / "MILESTONE_HANDOFF.md"
                    if handoff_path.is_file():
                        wired, total_wiring = compute_wiring_completeness(
                            handoff_path.read_text(encoding="utf-8"),
                            milestone.id,
                        )
                        if total_wiring > 0:
                            ratio = wired / total_wiring
                            print_info(f"Wiring completeness for {milestone.id}: {wired}/{total_wiring} ({ratio:.0%})")
                            if ratio < config.tracking_documents.wiring_completeness_gate:
                                print_warning(
                                    f"Wiring completeness ({ratio:.0%}) below gate "
                                    f"({config.tracking_documents.wiring_completeness_gate:.0%}). "
                                    f"Some predecessor interfaces may not be wired."
                                )
                except Exception as exc:
                    print_warning(f"Failed to check wiring completeness: {exc}")

            # Post-milestone mock data scan (if enabled)
            if config.milestone.mock_data_scan:
                from .quality_checks import run_mock_data_scan
                mock_violations = run_mock_data_scan(project_root)
                if mock_violations:
                    print_warning(
                        f"Milestone {milestone.id}: {len(mock_violations)} mock data "
                        f"violation(s) in service files. Running mock-data fix pass."
                    )
                    mock_fix_cost = await _run_mock_data_fix(
                        cwd=cwd,
                        config=config,
                        mock_violations=mock_violations,
                        task_text=task,
                        constraints=constraints,
                        intervention=intervention,
                        depth=depth,
                    )
                    total_cost += mock_fix_cost

                    # Re-scan after fix
                    remaining_mocks = run_mock_data_scan(project_root)
                    if remaining_mocks:
                        print_warning(
                            f"Milestone {milestone.id}: still {len(remaining_mocks)} "
                            f"mock data violations after fix pass."
                        )

            # Post-milestone UI compliance scan (if enabled)
            if config.milestone.ui_compliance_scan:
                from .quality_checks import run_ui_compliance_scan
                ui_violations = run_ui_compliance_scan(project_root)
                if ui_violations:
                    print_warning(
                        f"Milestone {milestone.id}: {len(ui_violations)} UI compliance "
                        f"violation(s) found. Running UI compliance fix pass."
                    )
                    ui_fix_cost = await _run_ui_compliance_fix(
                        cwd=cwd,
                        config=config,
                        ui_violations=ui_violations,
                        task_text=task,
                        constraints=constraints,
                        intervention=intervention,
                        depth=depth,
                    )
                    total_cost += ui_fix_cost

                    # Re-scan after fix
                    remaining_ui = run_ui_compliance_scan(project_root)
                    if remaining_ui:
                        print_warning(
                            f"Milestone {milestone.id}: still {len(remaining_ui)} "
                            f"UI compliance violations after fix pass."
                        )

            # Final health gate decision (after possible recovery)
            if config.milestone.health_gate and health_report and health_report.health == "failed":
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

        # Re-read plan for next iteration (agent may have overwritten MASTER_PLAN.md)
        plan_content = master_plan_path.read_text(encoding="utf-8")

        # Re-assert completed statuses that the agent may have reset
        for _m in plan.milestones:
            if _m.status == "COMPLETE":
                plan_content = update_master_plan_status(plan_content, _m.id, "COMPLETE")
        master_plan_path.write_text(plan_content, encoding="utf-8")

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


async def _run_mock_data_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    mock_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to replace mock data with real API calls.

    Creates a focused prompt listing each mock violation and instructing
    the orchestrator to deploy code-writers to replace mocks with real
    HTTP calls, then reviewers to verify.
    """
    if not mock_violations:
        return 0.0

    print_info(f"Running mock data fix pass ({len(mock_violations)} violations)")

    violations_text = "\n".join(
        f"  - {v.file_path}:{v.line} — {v.message}"
        for v in mock_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: MOCK DATA REPLACEMENT]\n\n"
        f"CRITICAL: The following service/client files contain mock data instead of real API calls.\n"
        f"This is a BLOCKING defect — the application is non-functional until these are fixed.\n\n"
        f"Mock violations found:\n{violations_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For EACH file listed above:\n"
        f"   a. Read the file and identify all mock patterns (of(), delay(), hardcoded data)\n"
        f"   b. Read REQUIREMENTS.md to find the API Wiring Map (SVC-xxx entries)\n"
        f"   c. Replace each mock with a real HTTP call to the correct backend endpoint\n"
        f"   d. Use the project's HTTP client (HttpClient, axios, fetch)\n"
        f"   e. Ensure request/response types match the API contracts\n"
        f"2. Deploy code-writer agents to make the replacements\n"
        f"3. Deploy code-reviewer to verify ALL mocks are gone and HTTP calls are correct\n"
        f"4. Do NOT add new mock data. Do NOT use of(). Do NOT use delay().\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Mock Data",
                cycle_number=1,
                failures=[f"{v.file_path}:{v.line} — {v.message}" for v in mock_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="mock_data_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Mock data fix pass failed: {exc}")

    return cost


async def _run_api_contract_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    api_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix API contract violations (API-001, API-002, API-003).

    Creates a focused prompt listing each field mismatch and instructing
    the orchestrator to deploy code-writers to align backend DTOs and
    frontend models with the REQUIREMENTS.md contract.
    """
    if not api_violations:
        return 0.0

    print_info(f"Running API contract fix pass ({len(api_violations)} violations)")

    violation_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in api_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: API CONTRACT FIX]\n\n"
        f"The following API contract violations were detected — field names or types\n"
        f"in backend DTOs / frontend models do not match the REQUIREMENTS.md contract.\n\n"
        f"API contract violations found:\n{violation_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For API-001 (backend field missing):\n"
        f"   - Add the missing property to the backend DTO/model class\n"
        f"   - Use PascalCase for C# properties (they serialize to camelCase)\n"
        f"2. For API-002 (frontend field mismatch):\n"
        f"   - Update the frontend model/interface to use the EXACT field name from REQUIREMENTS.md\n"
        f"   - Do NOT rename fields — match the backend JSON response shape\n"
        f"3. For API-003 (type mismatch):\n"
        f"   - Fix the type to match the contract specification\n"
        f"   - Add enum mappers where needed\n"
        f"4. Read REQUIREMENTS.md to find the SVC-xxx table with field schemas.\n"
        f"5. Fix ONLY the listed violations. Do not refactor or change anything else.\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="API Contract",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in api_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="api_contract_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"API contract fix pass failed: {exc}")

    return cost


async def _run_silent_data_loss_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    sdl_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix silent data loss violations (SDL-001).

    Creates a focused prompt listing each violation and instructing
    the orchestrator to deploy code-writers to add persistence calls.
    """
    if not sdl_violations:
        return 0.0

    print_info(f"Running SDL fix pass ({len(sdl_violations)} violations)")

    violation_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in sdl_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: SILENT DATA LOSS FIX]\n\n"
        f"The following silent data loss violations were detected — command handlers\n"
        f"that modify data but never persist changes.\n\n"
        f"Violations found:\n{violation_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For SDL-001 (CQRS handler missing persistence):\n"
        f"   - Add SaveChangesAsync() call before the handler returns\n"
        f"   - Ensure _context / _dbContext is injected via constructor\n"
        f"   - If using Unit of Work pattern, call _unitOfWork.SaveChangesAsync()\n"
        f"   - The handler MUST persist its changes — returning a DTO without saving is a data loss bug\n"
        f"2. For ENUM-004 (missing JsonStringEnumConverter):\n"
        f"   - Add to Program.cs: builder.Services.AddControllers().AddJsonOptions(o =>\n"
        f"       o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));\n"
        f"   - Add 'using System.Text.Json.Serialization;' if not present\n"
        f"3. Fix ONLY the listed violations. Do not refactor or change anything else.\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Silent Data Loss",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in sdl_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="silent_data_loss_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"SDL fix pass failed: {exc}")

    return cost


async def _run_endpoint_xref_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    xref_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix endpoint cross-reference violations (XREF-001, XREF-002, API-004).

    Creates a focused prompt listing each violation and instructing
    the orchestrator to deploy code-writers to add missing backend
    endpoints, fix HTTP method mismatches, and add missing request
    DTO properties.
    """
    if not xref_violations:
        return 0.0

    print_info(f"Running endpoint XREF fix pass ({len(xref_violations)} violations)")

    violation_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in xref_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: ENDPOINT CROSS-REFERENCE FIX]\n\n"
        f"The following endpoint cross-reference violations were detected — frontend\n"
        f"code calls backend endpoints that are missing or mismatched.\n\n"
        f"Violations found:\n{violation_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For XREF-001 (missing backend endpoint):\n"
        f"   - Add the missing controller action or route handler in the backend\n"
        f"   - Use the HTTP method and path shown in the violation\n"
        f"   - Implement the endpoint with proper request/response DTOs\n"
        f"   - Do NOT change the frontend call — add the backend endpoint to match it\n"
        f"2. For XREF-002 (HTTP method mismatch):\n"
        f"   - Verify which method is correct (frontend or backend)\n"
        f"   - Fix the side that is wrong — usually the frontend should match the backend convention\n"
        f"   - GET for reads, POST for creates, PUT for updates, DELETE for deletes\n"
        f"3. For API-004 (write-side field dropped):\n"
        f"   - Add the missing property to the backend Command/DTO class\n"
        f"   - Ensure the handler maps the new property to the entity\n"
        f"   - Verify the field is persisted to the database\n"
        f"4. Fix ONLY the listed violations. Do not refactor or change anything else.\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Endpoint XREF",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in xref_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="endpoint_xref_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Endpoint XREF fix pass failed: {exc}")

    return cost


async def _run_ui_compliance_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    ui_violations: list,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix UI compliance violations.

    Creates a focused prompt listing each UI violation and instructing
    the orchestrator to deploy code-writers to replace hardcoded colors,
    default palettes, generic fonts, and non-grid spacing with design
    token references and project-specific values.
    """
    if not ui_violations:
        return 0.0

    print_info(f"Running UI compliance fix pass ({len(ui_violations)} violations)")

    violations_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in ui_violations[:20]
    )

    fix_prompt = (
        f"[PHASE: UI COMPLIANCE FIX]\n\n"
        f"The following UI files contain design compliance violations.\n"
        f"These must be fixed to ensure consistent branding and design system adherence.\n\n"
        f"UI compliance violations found:\n{violations_text}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. For EACH violation listed above:\n"
        f"   a. UI-001/UI-001b: Replace hardcoded hex colors with design token CSS variables\n"
        f"      or Tailwind theme colors (e.g., `bg-primary`, `text-accent`, `var(--color-primary)`)\n"
        f"   b. UI-002: Replace default Tailwind colors (indigo/violet/purple) with\n"
        f"      project-specific palette colors defined in tailwind.config or theme\n"
        f"   c. UI-003: Replace generic fonts (Inter/Roboto/Arial) with the project's\n"
        f"      distinctive typeface as defined in the design reference\n"
        f"   d. UI-004: Adjust spacing values to align with 4px grid\n"
        f"      (use multiples of 4: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64)\n"
        f"2. If no design tokens exist yet, create a tokens file first\n"
        f"   (e.g., `src/styles/tokens.css` or extend `tailwind.config`)\n"
        f"3. Deploy code-writer agents to make the replacements\n"
        f"4. Deploy code-reviewer to verify all violations are resolved\n"
        f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="UI Compliance",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in ui_violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="ui_compliance_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"UI compliance fix pass failed: {exc}")

    return cost


async def _run_backend_e2e_tests(
    cwd: str | None,
    config: AgentTeamConfig,
    app_info,  # AppTypeInfo
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> tuple[float, E2ETestReport]:
    """Run backend API E2E tests via sub-orchestrator session."""
    print_info("Running backend API E2E tests...")

    prompt = BACKEND_E2E_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        test_port=config.e2e_testing.test_port,
        framework=app_info.backend_framework,
        start_command=app_info.start_command,
        db_type=app_info.db_type,
        seed_command=app_info.seed_command or "N/A",
        api_directory=app_info.api_directory or "src/",
        task_text=task_text or "",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="e2e_backend")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Backend E2E test pass failed: {exc}\n{traceback.format_exc()}")

    # Parse results
    results_path = Path(cwd) / config.convergence.requirements_dir / "E2E_RESULTS.md"
    report = parse_e2e_results(results_path)
    return cost, report


async def _run_frontend_e2e_tests(
    cwd: str | None,
    config: AgentTeamConfig,
    app_info,  # AppTypeInfo
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> tuple[float, E2ETestReport]:
    """Run frontend Playwright E2E tests via sub-orchestrator session."""
    print_info("Running frontend Playwright E2E tests...")

    prompt = FRONTEND_E2E_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        test_port=config.e2e_testing.test_port,
        framework=app_info.frontend_framework,
        start_command=app_info.start_command,
        frontend_directory=app_info.frontend_directory or "src/",
        task_text=task_text or "",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="e2e_frontend")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Frontend E2E test pass failed: {exc}\n{traceback.format_exc()}")

    results_path = Path(cwd) / config.convergence.requirements_dir / "E2E_RESULTS.md"
    report = parse_e2e_results(results_path)
    return cost, report


async def _run_e2e_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    failures: list[str],
    test_type: str,  # "backend_api" or "frontend_playwright"
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix E2E test failures."""
    if not failures:
        return 0.0

    print_info(f"Running E2E fix pass for {test_type} ({len(failures)} failures)")

    failures_text = "\n".join(f"  - {f}" for f in failures[:20])

    prompt = E2E_FIX_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        test_type=test_type,
        failures=failures_text,
        task_text=task_text or "",
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase=f"E2E {test_type}",
                cycle_number=1,
                failures=failures[:20],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase="e2e_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"E2E fix pass failed: {exc}\n{traceback.format_exc()}")

    return cost


# ---------------------------------------------------------------------------
# Browser MCP Interactive Testing — Sub-Orchestrator Functions
# ---------------------------------------------------------------------------

async def _run_browser_startup_agent(
    cwd: str | None,
    config: AgentTeamConfig,
    workflows_dir: Path,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> tuple[float, "AppStartupInfo"]:
    """Start the app via a sub-orchestrator agent (fallback when app isn't running)."""
    from .browser_testing import BROWSER_APP_STARTUP_PROMPT, AppStartupInfo, parse_app_startup_info

    print_info("Starting application via startup agent...")

    prompt = BROWSER_APP_STARTUP_PROMPT.format(
        project_root=cwd or ".",
        app_start_command=config.browser_testing.app_start_command or "auto-detect",
        app_port=config.browser_testing.app_port or "auto-detect",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="browser_startup")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Browser startup agent failed: {exc}\n{traceback.format_exc()}")
        return cost, AppStartupInfo()

    try:
        startup_path = workflows_dir / "APP_STARTUP.md"
        info = parse_app_startup_info(startup_path)
    except Exception as exc:
        print_warning(f"Failed to parse app startup info: {exc}")
        return cost, AppStartupInfo()
    return cost, info


async def _run_browser_workflow_executor(
    cwd: str | None,
    config: AgentTeamConfig,
    workflow_def: "WorkflowDefinition",
    workflows_dir: Path,
    app_url: str,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> tuple[float, WorkflowResult]:
    """Execute a single workflow via Playwright MCP browser agent."""
    from .browser_testing import BROWSER_WORKFLOW_EXECUTOR_PROMPT, parse_workflow_results
    from .mcp_servers import get_browser_testing_servers

    print_info(f"Executing workflow {workflow_def.id}: {workflow_def.name}")

    # Read workflow file content
    workflow_content = ""
    try:
        workflow_content = Path(workflow_def.path).read_text(encoding="utf-8")
    except OSError:
        workflow_content = f"Workflow {workflow_def.id}: {workflow_def.name}"

    screenshots_dir = workflows_dir.parent / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    prompt = BROWSER_WORKFLOW_EXECUTOR_PROMPT.format(
        app_url=app_url,
        workflow_id=f"{workflow_def.id:02d}",
        screenshots_dir=str(screenshots_dir),
        workflow_content=workflow_content,
    )

    # Build options with Playwright MCP servers
    browser_servers = get_browser_testing_servers(config)
    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    # Override MCP servers with browser testing servers and recompute allowed tools
    options.mcp_servers = browser_servers
    options.allowed_tools = recompute_allowed_tools(_BASE_TOOLS, browser_servers)

    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase=f"browser_wf_{workflow_def.id}")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Browser workflow {workflow_def.id} failed: {exc}\n{traceback.format_exc()}")
        return cost, WorkflowResult(
            workflow_id=workflow_def.id,
            workflow_name=workflow_def.name,
            health="failed",
            failure_reason=str(exc),
        )

    results_dir = workflows_dir.parent / "results"
    results_path = results_dir / f"workflow_{workflow_def.id:02d}_results.md"
    result = parse_workflow_results(results_path)
    result.workflow_id = workflow_def.id
    result.workflow_name = workflow_def.name
    return cost, result


async def _run_browser_workflow_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    workflow_def: "WorkflowDefinition",
    result: WorkflowResult,
    workflows_dir: Path,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Fix app code after a browser workflow failure."""
    from .browser_testing import BROWSER_WORKFLOW_FIX_PROMPT

    print_info(f"Running browser fix for workflow {workflow_def.id}: {workflow_def.name}")

    # Read workflow content
    workflow_content = ""
    try:
        workflow_content = Path(workflow_def.path).read_text(encoding="utf-8")
    except OSError:
        pass

    # Build failure report
    failure_report = (
        f"Workflow: {workflow_def.name}\n"
        f"Failed at: {result.failed_step}\n"
        f"Reason: {result.failure_reason}\n"
    )

    console_errors = "\n".join(result.console_errors[:20]) if result.console_errors else "No console errors captured"

    # Read fix cycle log
    fix_log_path = workflows_dir.parent / "FIX_CYCLE_LOG.md"
    fix_cycle_log = ""
    try:
        if fix_log_path.is_file():
            fix_cycle_log = fix_log_path.read_text(encoding="utf-8")
    except OSError:
        pass

    prompt = BROWSER_WORKFLOW_FIX_PROMPT.format(
        failure_report=failure_report,
        workflow_content=workflow_content,
        console_errors=console_errors,
        fix_cycle_log=fix_cycle_log or "No previous fix attempts",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase=f"browser_fix_{workflow_def.id}")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Browser fix for workflow {workflow_def.id} failed: {exc}\n{traceback.format_exc()}")

    return cost


async def _run_browser_regression_sweep(
    cwd: str | None,
    config: AgentTeamConfig,
    passed_workflows: list["WorkflowDefinition"],
    workflows_dir: Path,
    app_url: str,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> tuple[float, list[int]]:
    """Quick regression sweep — ONE session checks ALL passed workflows."""
    from .browser_testing import BROWSER_REGRESSION_SWEEP_PROMPT
    from .mcp_servers import get_browser_testing_servers

    url_lines = []
    for wf in passed_workflows:
        url_lines.append(f"- Workflow {wf.id} ({wf.name}): {app_url}{wf.first_page_route}")

    screenshots_dir = workflows_dir.parent / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    prompt = BROWSER_REGRESSION_SWEEP_PROMPT.format(
        app_url=app_url,
        screenshots_dir=str(screenshots_dir),
        passed_workflow_urls="\n".join(url_lines),
    )

    browser_servers = get_browser_testing_servers(config)
    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    # Override MCP servers with browser testing servers and recompute allowed tools
    options.mcp_servers = browser_servers
    options.allowed_tools = recompute_allowed_tools(_BASE_TOOLS, browser_servers)

    phase_costs: dict[str, float] = {}
    cost = 0.0
    regressed_ids: list[int] = []

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="browser_regression")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Browser regression sweep failed: {exc}\n{traceback.format_exc()}")
        return cost, []

    # Parse regression results
    sweep_path = workflows_dir.parent / "REGRESSION_SWEEP_RESULTS.md"
    if sweep_path.is_file():
        try:
            sweep_content = sweep_path.read_text(encoding="utf-8")
            # Look for "Regressed workflow IDs: [1, 3]" or individual regressed rows
            import re as _re
            ids_match = _re.search(r"Regressed workflow IDs?:\s*\[([^\]]+)\]", sweep_content)
            if ids_match:
                for num in _re.findall(r"\d+", ids_match.group(1)):
                    regressed_ids.append(int(num))
            else:
                # Parse table rows for REGRESSED status
                for line in sweep_content.splitlines():
                    if "REGRESSED" in line.upper():
                        nums = _re.findall(r"Workflow\s+(\d+)", line)
                        for n in nums:
                            regressed_ids.append(int(n))
        except (OSError, ValueError):
            pass

    return cost, regressed_ids


# ---------------------------------------------------------------------------
# PRD Reconciliation Prompt
# ---------------------------------------------------------------------------

PRD_RECONCILIATION_PROMPT = """\
[PHASE: PRD RECONCILIATION — QUANTITATIVE CLAIM VERIFICATION]

You are a dedicated verification agent. Your ONLY job is to compare the PRD's
quantitative claims against the actual codebase implementation and produce a
report.

STEP 1 — READ THE PRD:
Read {requirements_dir}/REQUIREMENTS.md (and any milestone REQUIREMENTS.md files).
Extract EVERY quantitative or countable claim, for example:
  - "N scenarios", "M user roles", "K dashboard widgets", "L API endpoints"
  - "supports X file formats", "Y-step wizard", "Z CRUD operations"
  - Specific feature lists ("bidder management, evaluator scoring, …")

STEP 2 — VERIFY AGAINST CODE:
For each claim, search the codebase to verify:
  - Route/page/component counts match stated numbers
  - Feature lists are fully implemented (not partially)
  - Data models have all stated fields
  - API endpoints exist for all stated operations
  - UI components exist for all stated widgets/sections

STEP 3 — WRITE REPORT:
Write the report to {requirements_dir}/PRD_RECONCILIATION.md using this format:

# PRD Reconciliation Report

## VERIFIED (claim matches implementation)
- [Claim]: [Evidence — file paths, counts]

### MISMATCH (claim does NOT match implementation)
- [Claim]: PRD says [X], found [Y]. Files: [paths]
- [Claim]: PRD says [X], found [Y]. Files: [paths]

## SUMMARY
- Total claims checked: N
- Verified: N
- Mismatches: N

RULES:
- Be PRECISE. Count actual files/routes/components, not estimates.
- Only flag REAL mismatches, not stylistic differences.
- If a claim is ambiguous, note it as "AMBIGUOUS" (not a mismatch).
- A missing feature is a mismatch. An extra feature is NOT a mismatch.

{task_text}
"""


async def _run_prd_reconciliation(
    cwd: str | None,
    config: AgentTeamConfig,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run PRD reconciliation via sub-orchestrator session.

    Deploys an LLM agent to compare quantitative PRD claims against the
    actual codebase and write PRD_RECONCILIATION.md with findings.
    """
    print_info("Running PRD reconciliation check...")

    prompt = PRD_RECONCILIATION_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}" if task_text else "",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="prd_reconciliation")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"PRD reconciliation pass failed: {exc}\n{traceback.format_exc()}")

    return cost


# ---------------------------------------------------------------------------
# Artifact Recovery Prompt (v10.1)
# ---------------------------------------------------------------------------

ARTIFACT_RECOVERY_PROMPT = """\
[ARTIFACT RECOVERY — POST-ORCHESTRATION]

The orchestrator has finished building the project but did NOT generate the required
tracking documents. You MUST create these files by analyzing the generated source code
and the original PRD/task description.

STEP 1: Scan the project structure. PRIORITIZE reading these files first:
  - Route/controller files (routes/, controllers/, api/) — needed for SVC-xxx table
  - Model/entity files (models/, entities/, prisma/schema.prisma) — needed for STATUS_REGISTRY
  - Main entry points (app.ts, main.ts, index.ts, server.ts) — needed for feature inventory
  - Component index files (components/, pages/, features/) — needed for frontend REQ-xxx items
  For large projects (100+ files), focus on these categories. Do NOT attempt to read every file.
STEP 2: Read the PRD document if it exists.
STEP 3: Generate {requirements_dir}/REQUIREMENTS.md with this EXACT format:

## Requirements

For each feature you can identify in the source code, write:
- [ ] REQ-NNN: <description of the feature>

Number them sequentially starting from REQ-001.
Include ALL features: API endpoints, UI components, authentication, database operations, etc.
Mark ALL as [ ] (unchecked) — the REVIEW FLEET will mark them [x] after verification.

## SVC-xxx Service-to-API Wiring Map

| ID | Endpoint | Method | Request Schema | Response Schema |
|----|----------|--------|---------------|-----------------|
| SVC-001 | /api/... | GET/POST/... | {{ field: type }} | {{ field: type }} |

Populate this table by reading the actual route/controller files.
One row per API endpoint. Use the actual field names from the code.

## STATUS_REGISTRY

List every enum, status type, and state machine found in the codebase:
- Enum Name: [list of valid values]
- Status transitions: [from → to rules if discoverable]

STEP 4: If {requirements_dir}/TASKS.md does NOT exist, generate it:

## Tasks

For each REQ-xxx requirement, create a corresponding task:
- TASK-NNN: <implementation task> (status: COMPLETE)

Mark all tasks COMPLETE since the code is already built.
{task_text}
"""


async def _run_artifact_recovery(
    cwd: str | None,
    config: AgentTeamConfig,
    task_text: str | None = None,
    prd_path: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Deploy artifact recovery agent to generate missing REQUIREMENTS.md and TASKS.md.

    This is a safety net for PRD mode when the orchestrator fails to generate
    root-level tracking artifacts. Reads all generated source code + PRD and
    produces structured REQUIREMENTS.md with REQ-xxx checkboxes, SVC-xxx table,
    and STATUS_REGISTRY section.

    NOTE: _backend is a module-level global (line ~3063: ``_backend: str = "api"``),
    referenced the same way by _run_prd_reconciliation() and all 20+ async functions.
    """
    print_info("Artifact recovery: generating missing REQUIREMENTS.md from source code analysis...")

    prompt = ARTIFACT_RECOVERY_PROMPT.format(
        requirements_dir=config.convergence.requirements_dir,
        task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}" if task_text else "",
    )

    # If PRD document exists, prepend it as context
    if prd_path:
        prd_file = Path(prd_path)
        if prd_file.is_file():
            try:
                prd_content = prd_file.read_text(encoding="utf-8", errors="replace")
                prompt = f"[PRD DOCUMENT]\n{prd_content}\n\n{prompt}"
            except OSError:
                pass

    # Follow the EXACT pattern from _run_prd_reconciliation():
    # _backend is a module-level global, NOT a parameter.
    options = _build_options(
        config, cwd, constraints=constraints, task_text=task_text,
        depth=depth, backend=_backend,
    )
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(
                client, config, phase_costs, current_phase="artifact_recovery",
            )
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Artifact recovery agent failed: {exc}\n{traceback.format_exc()}")

    return cost


# ---------------------------------------------------------------------------
# Milestone Handoff Details Generation
# ---------------------------------------------------------------------------

HANDOFF_GENERATION_PROMPT = """\
[PHASE: MILESTONE HANDOFF DOCUMENTATION]

Milestone {milestone_id} ({milestone_title}) just completed.
You must document EVERY interface this milestone exposes for subsequent milestones.

STEP 1: Read {requirements_path} to understand what was built.

STEP 2: Scan the codebase for:
- API endpoints (route files, controllers): extract path, method, auth, request/response shapes
- Database schema (migrations, models): extract table names, column names, types
- Enum/status values: for EVERY entity with a status/type/enum field, extract ALL valid values,
  the DB storage type (string vs int), and the exact string used in API responses
- Environment variables (configs, .env): extract variable names and purposes

STEP 3: Update {requirements_dir}/MILESTONE_HANDOFF.md — find the section for {milestone_id}
and fill in ALL tables:
- Exposed Interfaces table: EVERY endpoint with exact path, method, auth, request body schema,
  response schema (include field names AND types)
- Database State: ALL tables with columns and types
- Enum/Status Values table: EVERY entity with enum/status fields — list ALL valid values,
  DB type, and exact API string. This is CRITICAL for preventing cross-milestone mismatches.
- Environment Variables: ALL env vars with descriptions
- Known Limitations: Anything not yet implemented

Be EXHAUSTIVE. A vague entry like "returns tender object" is NOT acceptable.
Write: {{ id: string, title: string, status: "draft"|"active"|"closed", createdAt: string (ISO8601) }}

[ORIGINAL USER REQUEST]
{task_text}"""


async def _generate_handoff_details(
    cwd: str | None,
    config: AgentTeamConfig,
    milestone_id: str,
    milestone_title: str,
    requirements_path: str,
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a sub-orchestrator session to fill in MILESTONE_HANDOFF.md details.

    Reads the milestone's code and populates the handoff section with actual
    endpoint details, DB state, env vars. Returns the cost.
    """
    print_info(f"Generating handoff details for {milestone_id}...")

    prompt = HANDOFF_GENERATION_PROMPT.format(
        milestone_id=milestone_id,
        milestone_title=milestone_title,
        requirements_path=requirements_path,
        requirements_dir=config.convergence.requirements_dir,
        task_text=task_text or "",
    )

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            cost = await _process_response(client, config, phase_costs, current_phase="handoff_generation")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"Handoff details generation for {milestone_id} failed: {exc}\n{traceback.format_exc()}")

    return cost


async def _run_integrity_fix(
    cwd: str | None,
    config: AgentTeamConfig,
    violations: list,
    scan_type: str,  # "deployment", "asset", "database_dual_orm", "database_defaults", or "database_relationships"
    task_text: str | None = None,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    depth: str = "standard",
) -> float:
    """Run a recovery pass to fix integrity violations.

    Creates a focused prompt listing each violation and instructing the
    orchestrator to deploy code-writers to fix the issues.

    Supported scan_type values:
      - "deployment": Docker-compose config issues (DEPLOY-001..004)
      - "asset": Broken static asset references (ASSET-001..003)
      - "database_dual_orm": ORM/SQL type mismatches (DB-001..003)
      - "database_defaults": Missing default values (DB-004..005)
      - "database_relationships": Incomplete relationship config (DB-006..008)
    """
    if not violations:
        return 0.0

    print_info(f"Running {scan_type} integrity fix pass ({len(violations)} violations)")

    violations_text = "\n".join(
        f"  - [{v.check}] {v.file_path}:{v.line} — {v.message}"
        for v in violations[:20]
    )

    if scan_type == "deployment":
        fix_prompt = (
            f"[PHASE: DEPLOYMENT INTEGRITY FIX]\n\n"
            f"The following deployment configuration issues were detected.\n"
            f"Fix each issue to ensure the app can be deployed correctly.\n\n"
            f"Violations found:\n{violations_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. DEPLOY-001 (port mismatch): Update app listen port to match docker-compose,\n"
            f"   or update docker-compose to expose the correct port.\n"
            f"2. DEPLOY-002 (undefined env var): Add missing env vars to .env / .env.example,\n"
            f"   or add defaults in the code (process.env.VAR || 'default').\n"
            f"3. DEPLOY-003 (CORS): Verify CORS origin matches deployment URL, or use env var.\n"
            f"4. DEPLOY-004 (service name): Update connection string to use correct docker-compose\n"
            f"   service name, or add the service to docker-compose.\n"
            f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
        )
    elif scan_type == "database_dual_orm":
        fix_prompt = (
            f"[PHASE: DATABASE DUAL ORM FIX]\n\n"
            f"The following ORM/raw-SQL type mismatches were detected.\n"
            f"Fix each issue so ORM models and raw SQL queries use consistent types.\n\n"
            f"Violations found:\n{violations_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. DB-001 (enum mismatch): Use the ORM enum type in raw SQL instead of\n"
            f"   hardcoded integer or string literals. E.g., use parameterized queries\n"
            f"   with the enum value, or cast properly.\n"
            f"2. DB-002 (boolean mismatch): Use proper boolean values (true/false) in\n"
            f"   raw SQL instead of 0/1 integers, or use parameterized queries.\n"
            f"3. DB-003 (datetime mismatch): Use parameterized datetime values instead\n"
            f"   of hardcoded date string literals in raw SQL.\n"
            f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
        )
    elif scan_type == "database_defaults":
        fix_prompt = (
            f"[PHASE: DATABASE DEFAULT VALUE FIX]\n\n"
            f"The following missing defaults and unsafe nullable access issues were detected.\n"
            f"Fix each issue to prevent runtime null errors and undefined state.\n\n"
            f"Violations found:\n{violations_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. DB-004 (missing default): Add explicit default values to boolean and\n"
            f"   enum properties. E.g., `= false;` for bools, `= EnumType.Default;`\n"
            f"   for enums, `@default(false)` for Prisma, `default=False` for Django.\n"
            f"2. DB-005 (nullable without null check): Add null guards before accessing\n"
            f"   nullable properties. Use `?.` (optional chaining), `if (prop != null)`,\n"
            f"   or `if prop is not None:` as appropriate for the language.\n"
            f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
        )
    elif scan_type == "database_relationships":
        fix_prompt = (
            f"[PHASE: DATABASE RELATIONSHIP FIX]\n\n"
            f"The following incomplete ORM relationship configurations were detected.\n"
            f"Fix each issue to ensure relationships are fully wired.\n\n"
            f"Violations found:\n{violations_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. DB-006 (FK without navigation): Add a navigation property for the FK.\n"
            f"   E.g., add `public virtual Entity Entity {{ get; set; }}` in C#,\n"
            f"   or `@ManyToOne(() => Entity)` in TypeORM.\n"
            f"2. DB-007 (navigation without inverse): Add an inverse navigation on the\n"
            f"   related entity. E.g., `public virtual ICollection<T> Items {{ get; set; }}`\n"
            f"   or `@OneToMany(() => T, t => t.parent)` in TypeORM.\n"
            f"3. DB-008 (FK without config): Add relationship configuration in\n"
            f"   OnModelCreating / entity configuration. E.g., `.HasOne().WithMany()`\n"
            f"   or add the navigation property and FK attribute.\n"
            f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
        )
    else:
        fix_prompt = (
            f"[PHASE: ASSET INTEGRITY FIX]\n\n"
            f"The following broken asset references were detected.\n"
            f"Fix each reference so the asset loads correctly at runtime.\n\n"
            f"Violations found:\n{violations_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. ASSET-001 (broken src/href): Fix the path or add the missing asset file.\n"
            f"2. ASSET-002 (broken CSS url): Fix the path in the CSS/SCSS file.\n"
            f"3. ASSET-003 (broken import/require): Fix the import path or add the file.\n"
            f"4. Prefer fixing paths over adding placeholder files.\n"
            f"5. If an asset truly does not exist, remove the reference.\n"
            f"\n[ORIGINAL USER REQUEST]\n{task_text or ''}"
        )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase=f"Integrity ({scan_type})",
                cycle_number=1,
                failures=[f"[{v.check}] {v.file_path}:{v.line} — {v.message}" for v in violations[:20]],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}
    cost = 0.0

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(fix_prompt + fix_log_section)
            cost = await _process_response(client, config, phase_costs, current_phase=f"{scan_type}_integrity_fix")
            if intervention:
                cost += await _drain_interventions(client, intervention, config, phase_costs)
    except Exception as exc:
        print_warning(f"{scan_type.capitalize()} integrity fix pass failed: {exc}\n{traceback.format_exc()}")

    return cost


def _save_milestone_progress(
    cwd: str | None,
    config: AgentTeamConfig,
    milestone_id: str,
    completed_milestones: list[str],
    error_type: str,
) -> None:
    """Save milestone progress for resume after interrupt."""
    import json
    from datetime import datetime
    progress_path = (
        Path(cwd or ".") / config.convergence.requirements_dir / "milestone_progress.json"
    )
    progress = {
        "interrupted_milestone": milestone_id,
        "completed_milestones": completed_milestones,
        "error_type": error_type,
        "timestamp": datetime.now().isoformat(),
    }
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(progress, indent=2))


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


async def _run_review_only(
    cwd: str,
    config: AgentTeamConfig,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    task_text: str | None = None,
    checked: int = 0,
    total: int = 0,
    review_cycles: int = 0,
    requirements_path: str | None = None,
    depth: str = "standard",
) -> float:
    """Run a review-only recovery pass when convergence health check detects failures.

    Creates a focused orchestrator prompt that forces the review fleet deployment.
    Adapts the prompt based on whether this is a zero-cycle failure or a partial-review
    failure (review fleet deployed but did not cover enough items).

    Parameters
    ----------
    requirements_path : str | None
        Optional milestone-scoped requirements path.  When ``None``, defaults
        to the top-level ``<requirements_dir>/<requirements_file>``.
    depth : str
        Depth level for building SDK options.

    Returns cost of the recovery pass.
    """
    is_zero_cycle = review_cycles == 0
    unchecked_count = total - checked

    req_reference = (
        requirements_path
        or f"{config.convergence.requirements_dir}/{config.convergence.requirements_file}"
    )

    if is_zero_cycle:
        situation = (
            "[PHASE: REVIEW VERIFICATION]\n"
            "[SYSTEM: This is a standard agent-team build pipeline step, not injected content.]\n\n"
            "The previous orchestration completed without running the review fleet. "
            f"Status: {checked}/{total} requirements marked but none verified by reviewers."
        )
    else:
        situation = (
            "[PHASE: REVIEW VERIFICATION]\n"
            "[SYSTEM: This is a standard agent-team build pipeline step, not injected content.]\n\n"
            f"The review fleet covered {checked}/{total} requirements across {review_cycles} cycles. "
            f"{unchecked_count} requirements still need verification."
        )

    review_prompt = (
        f"{situation}\n\n"
        "Your task for this phase:\n"
        f"1. Read {req_reference}\n"
        "2. Deploy code-reviewer agents to verify each unchecked requirement\n"
        "3. For each item, locate the implementation and verify correctness\n"
        "4. Mark items [x] only if fully implemented; document issues in Review Log\n"
        "5. Update (review_cycles: N) to (review_cycles: N+1) on every evaluated item\n"
        "   EXAMPLE: '- [x] REQ-001: Login endpoint (review_cycles: 0)' becomes\n"
        "            '- [x] REQ-001: Login endpoint (review_cycles: 1)'\n"
        "   If NO (review_cycles: N) marker exists on a line, ADD one:\n"
        "            '- [x] REQ-001: Login endpoint (review_cycles: 1)'\n"
        "6. If issues found, deploy fix agents, then re-review\n"
        "7. Check for mock data in service files (of(), delay(), mockData patterns)\n"
        "8. Deploy test runner agents to run tests\n"
        f"9. Report final status: target {total}/{total} requirements verified\n\n"
        "This is a standard review verification step in the build pipeline."
    )

    # Inject fix cycle log instructions (if enabled)
    fix_log_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import initialize_fix_cycle_log, build_fix_cycle_entry, FIX_CYCLE_LOG_INSTRUCTIONS
            req_dir_str = str(Path(cwd or ".") / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Review Recovery",
                cycle_number=1,
                failures=["review recovery"],
            )
            fix_log_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry (append your results to this):\n{cycle_entry}\n"
            )
        except Exception:
            pass  # Non-critical — don't block fix if log fails
    review_prompt += fix_log_section

    options = _build_options(config, cwd, constraints=constraints, task_text=task_text, depth=depth, backend=_backend)
    phase_costs: dict[str, float] = {}

    if is_zero_cycle:
        print_warning("Convergence health check FAILED: 0 review cycles detected.")
    else:
        print_warning(
            f"Convergence health check FAILED: {unchecked_count}/{total} "
            f"requirements still unchecked after {review_cycles} review cycles."
        )
    print_info("Launching review-only recovery pass...")

    async with ClaudeSDKClient(options=options) as client:
        await client.query(review_prompt)
        cost = await _process_response(client, config, phase_costs, current_phase="review_recovery")
        cost += await _drain_interventions(client, intervention, config, phase_costs)
    return cost


async def _run_audit_team(
    cwd: str,
    config: AgentTeamConfig,
    depth: str = "standard",
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    task_text: str | None = None,
    requirements_path: str | None = None,
    scope_label: str = "end-of-run",
) -> tuple[float, AuditTeamReport]:
    """Run the 5-auditor parallel audit team and return (cost, report).

    Deploys up to 5 specialized auditors in parallel, each writing findings
    to a separate file.  A scorer aggregates findings.  If the health is
    "needs-fixes" or "critical", fix agents are dispatched, then relevant
    auditors re-run (up to ``config.audit_team.max_fix_rounds`` cycles).

    Parameters
    ----------
    scope_label : str
        Label for logging: "end-of-run" or "milestone:<id>".
    requirements_path : str | None
        Explicit path to REQUIREMENTS.md.  ``None`` uses top-level default.
    """
    total_cost = 0.0
    auditors = get_active_auditors(config, depth)
    if not auditors:
        return 0.0, AuditTeamReport(health="passed")

    req_path = requirements_path or str(
        Path(cwd) / config.convergence.requirements_dir / config.convergence.requirements_file
    )

    # Create audit output directory — scope-aware to prevent cross-milestone overwriting
    if scope_label.startswith("milestone:"):
        ms_id = scope_label.split(":", 1)[1]
        audit_dir = Path(cwd) / config.convergence.requirements_dir / "milestones" / ms_id / "audit-reports"
    else:
        audit_dir = Path(cwd) / config.convergence.requirements_dir / "audit-reports"
    audit_dir.mkdir(parents=True, exist_ok=True)

    print_info(
        f"[Audit-Team {scope_label}] Deploying {len(auditors)} auditors: {', '.join(auditors)}"
    )

    report = AuditTeamReport(auditors_deployed=list(auditors))

    # Nested function defined once outside the loop (avoids per-iteration recreation)
    async def _run_single_auditor(auditor_name: str) -> float:
        """Run a single auditor session. Returns cost."""
        output_file = str(audit_dir / f"{auditor_name}_audit.md")
        prompt = get_auditor_prompt(auditor_name, req_path, output_file)

        # Library auditor needs Context7 MCP
        if auditor_name == "library":
            from .mcp_servers import get_context7_only_servers
            lib_servers = get_context7_only_servers(config)
            if not lib_servers:
                print_warning(
                    f"[Audit-Team] Library auditor skipped — Context7 MCP not available."
                )
                return 0.0
            opts = _build_options(
                config, cwd, constraints=constraints,
                task_text=task_text, depth=depth, backend=_backend,
            )
            if lib_servers:
                opts.mcp_servers = lib_servers
                opts.allowed_tools = recompute_allowed_tools(_BASE_TOOLS, lib_servers)
        else:
            opts = _build_options(
                config, cwd, constraints=constraints,
                task_text=task_text, depth=depth, backend=_backend,
            )

        phase_costs: dict[str, float] = {}
        cost = 0.0
        try:
            async with ClaudeSDKClient(options=opts) as client:
                await client.query(prompt)
                cost = await _process_response(
                    client, config, phase_costs,
                    current_phase=f"audit_{auditor_name}",
                )
                if intervention:
                    cost += await _drain_interventions(
                        client, intervention, config, phase_costs,
                    )
        except Exception as exc:
            print_warning(f"Auditor '{auditor_name}' failed: {exc}")
        return cost

    # Track which auditors to run each cycle (initially all, then only those with issues)
    auditors_to_run = list(auditors)

    for fix_round in range(config.audit_team.max_fix_rounds + 1):
        # --- Phase 1: Run auditors in parallel (selective after first round) ---
        tasks = [_run_single_auditor(name) for name in auditors_to_run]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, (int, float)):
                total_cost += r
            elif isinstance(r, Exception):
                print_warning(f"Auditor exception: {r}")

        # --- Phase 2: Parse and score ---
        all_findings = parse_all_audit_reports(str(audit_dir))
        report = score_audit_findings(
            all_findings,
            pass_threshold=config.audit_team.pass_threshold,
            auditors_deployed=list(auditors),
        )
        report.fix_rounds_used = fix_round

        print_info(
            f"[Audit-Team {scope_label}] Round {fix_round}: "
            f"score={report.overall_score:.2f}, health={report.health}, "
            f"PASS={report.total_pass} FAIL={report.total_fail} PARTIAL={report.total_partial}"
        )

        # --- Phase 3: Check if done ---
        if report.health == "passed":
            break
        if fix_round >= config.audit_team.max_fix_rounds:
            break

        # --- Phase 4: Fix dispatch ---
        fixable = filter_findings_for_fix(
            report.findings,
            severity_gate=config.audit_team.severity_gate,
        )
        if not fixable:
            print_info(f"[Audit-Team {scope_label}] No fixable findings above severity gate.")
            break

        # Selective re-audit: only re-run auditors that reported fixable findings
        auditors_to_run = list({f.auditor for f in fixable} & set(auditors))
        if not auditors_to_run:
            auditors_to_run = list(auditors)  # Fallback: re-run all

        fix_cost = await _run_audit_fix(
            cwd=cwd,
            config=config,
            findings=fixable,
            constraints=constraints,
            intervention=intervention,
            task_text=task_text,
            depth=depth,
            scope_label=scope_label,
            fix_round=fix_round,
        )
        total_cost += fix_cost

    return total_cost, report


async def _run_audit_fix(
    cwd: str,
    config: AgentTeamConfig,
    findings: list[AuditFinding],
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
    task_text: str | None = None,
    depth: str = "standard",
    scope_label: str = "end-of-run",
    fix_round: int = 0,
) -> float:
    """Dispatch fix agents for audit findings grouped by file scope.

    Groups findings to avoid conflicting edits, then runs a fix session
    per group.  Fix groups run concurrently via ``asyncio.gather``.
    Returns total cost.
    """
    if not findings:
        return 0.0

    groups = group_findings_by_file(findings)
    print_info(
        f"[Audit-Team {scope_label}] Fixing {len(findings)} issues "
        f"across {len(groups)} file group(s)"
    )

    # Build fix cycle log section if enabled
    fix_cycle_section = ""
    if config.tracking_documents.fix_cycle_log:
        try:
            from .tracking_documents import (
                FIX_CYCLE_LOG_INSTRUCTIONS,
                build_fix_cycle_entry,
                initialize_fix_cycle_log,
            )
            req_dir_str = str(Path(cwd) / config.convergence.requirements_dir)
            initialize_fix_cycle_log(req_dir_str)
            cycle_entry = build_fix_cycle_entry(
                phase="Audit-Team",
                cycle_number=fix_round + 1,
                failures=[
                    f"{f.file_path}:{f.line_number} — [{f.severity}] {f.description}"
                    for f in findings[:20]
                ],
            )
            fix_cycle_section = (
                f"\n\n{FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir=req_dir_str)}\n\n"
                f"Current fix cycle entry:\n{cycle_entry}\n"
            )
        except Exception:
            pass

    total_cost = 0.0

    # Run fix groups concurrently (each targets different files, no conflicts)
    async def _fix_file_group(file_key: str, file_findings: list[AuditFinding]) -> float:
        fix_prompt = build_audit_fix_prompt(file_findings, fix_cycle_log=fix_cycle_section)
        options = _build_options(
            config, cwd, constraints=constraints,
            task_text=task_text, depth=depth, backend=_backend,
        )
        phase_costs: dict[str, float] = {}
        cost = 0.0

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(fix_prompt)
                cost = await _process_response(
                    client, config, phase_costs,
                    current_phase="audit_fix",
                )
                if intervention:
                    cost += await _drain_interventions(
                        client, intervention, config, phase_costs,
                    )
        except Exception as exc:
            print_warning(f"Audit fix for '{file_key}' failed: {exc}")

        return cost

    fix_tasks = [
        _fix_file_group(fk, ff) for fk, ff in groups.items()
    ]
    results = await asyncio.gather(*fix_tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, (int, float)):
            total_cost += r
        elif isinstance(r, Exception):
            print_warning(f"Audit fix group exception: {r}")

    return total_cost


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
        config, user_overrides = load_config(config_path=args.config, cli_overrides=cli_overrides)
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

    # NOTE: Firecrawl availability checks moved to Phase 0.6 (design extraction).
    # Phase 0.6 handles all error cases (hard-fail vs warn) based on require_ui_doc.

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

    # Extract design reference URLs from PRD content (if present)
    if args.prd:
        try:
            _prd_text = Path(args.prd).read_text(encoding="utf-8")
            _prd_design_urls = _extract_design_urls_from_interview(_prd_text)
            if _prd_design_urls:
                design_ref_urls.extend(_prd_design_urls)
                design_ref_urls = list(dict.fromkeys(design_ref_urls))
                print_info(f"Extracted {len(_prd_design_urls)} design reference URL(s) from PRD")
        except (OSError, UnicodeDecodeError):
            pass  # Non-critical — PRD will still be used for build

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
        if design_ref_urls:
            print_info(f"Design reference URLs: {len(design_ref_urls)}")
            for url in design_ref_urls:
                print_info(f"  - {url}")
            print_info(f"Phase 0.6: Design extraction will run (require_ui_doc={config.design_reference.require_ui_doc})")
            print_info(f"Output: {config.convergence.requirements_dir}/{config.design_reference.ui_requirements_file}")
        return

    # -------------------------------------------------------------------
    # C2: Initialize RunState early (before interview) so interrupted
    # interviews also get state saved.
    # On resume, load the existing state to preserve milestone progress.
    # -------------------------------------------------------------------
    from .state import RunState
    if _resume_ctx:
        # Resume mode: load the existing state from disk to preserve
        # completed_phases, milestone_progress, completed_milestones, etc.
        # We restore ANY loaded state — not just milestone runs — so that
        # standard-mode resumes also retain completed_phases and total_cost.
        from .state import load_state as _load_state_resume
        _loaded = _load_state_resume(str(Path(cwd) / ".agent-team"))
        if _loaded:
            _current_state = _loaded
            _current_state.task = args.task or _loaded.task
            _current_state.depth = args.depth or _loaded.depth
        else:
            _current_state = RunState(task=args.task or "", depth=args.depth or "pending")
            _current_state.current_phase = "init"
            _current_state.artifacts["cwd"] = cwd
    else:
        _current_state = RunState(task=args.task or "", depth=args.depth or "pending")
        _current_state.current_phase = "init"
        _current_state.artifacts["cwd"] = cwd

    # Persist the original task text early so verification can access it
    # even if the run is interrupted before completion.
    # Skip on resume to avoid overwriting milestone progress.
    if not _resume_ctx:
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

    # -------------------------------------------------------------------
    # Phase 0.6: Design Reference Extraction (UI_REQUIREMENTS.md)
    # -------------------------------------------------------------------
    ui_requirements_content: str | None = None

    if design_ref_urls:
        from .design_reference import (
            DesignExtractionError,
            generate_fallback_ui_requirements,
            load_ui_requirements,
            run_design_extraction_with_retry,
            validate_ui_requirements,
            validate_ui_requirements_content,
        )
        from .mcp_servers import is_firecrawl_available

        _current_state.current_phase = "design_extraction"
        req_dir = config.convergence.requirements_dir
        ui_file = config.design_reference.ui_requirements_file
        _require = config.design_reference.require_ui_doc

        # Check for existing valid UI_REQUIREMENTS.md (resume scenario)
        existing = load_ui_requirements(cwd, config)
        if existing:
            missing = validate_ui_requirements(existing)
            if not missing:
                print_info(
                    f"Phase 0.6: Reusing existing {req_dir}/{ui_file} "
                    f"(all required sections present)"
                )
                ui_requirements_content = existing
            else:
                print_warning(
                    f"Existing {req_dir}/{ui_file} is missing sections: "
                    f"{', '.join(missing)}. Re-extracting."
                )

        # Only run extraction if we don't have valid content yet
        if ui_requirements_content is None:
            _fallback = config.design_reference.fallback_generation

            if not is_firecrawl_available(config):
                if _fallback:
                    print_warning(
                        "Phase 0.6: Firecrawl unavailable — generating fallback UI requirements."
                    )
                    try:
                        ui_requirements_content = generate_fallback_ui_requirements(
                            task=effective_task, config=config, cwd=cwd,
                        )
                        print_success(
                            f"Phase 0.6: Fallback {req_dir}/{ui_file} generated "
                            f"(heuristic defaults — review recommended)"
                        )
                    except Exception as exc:
                        if _require:
                            print_error(f"Phase 0.6: Fallback generation failed: {exc}")
                            sys.exit(1)
                        else:
                            print_warning(f"Phase 0.6: Fallback generation failed: {exc}")
                elif _require:
                    print_error(
                        "Phase 0.6: Design reference URLs provided but Firecrawl is unavailable "
                        "(FIRECRAWL_API_KEY not set or firecrawl disabled). "
                        "Set require_ui_doc: false in config to continue without extraction."
                    )
                    sys.exit(1)
                else:
                    print_warning(
                        "Phase 0.6: Firecrawl unavailable — skipping design extraction. "
                        "URLs will be passed as soft instructions to orchestrator."
                    )
            else:
                _retries = config.design_reference.extraction_retries
                print_info(
                    f"Phase 0.6: Extracting design references → {req_dir}/{ui_file} "
                    f"(retries={_retries})"
                )
                for url in design_ref_urls:
                    print_info(f"  - {url}")

                try:
                    content, extraction_cost = asyncio.run(
                        run_design_extraction_with_retry(
                            urls=design_ref_urls,
                            config=config,
                            cwd=cwd,
                            backend=_backend,
                            max_retries=_retries,
                        )
                    )

                    # Validate section headers
                    missing = validate_ui_requirements(content)
                    if missing:
                        msg = (
                            f"Phase 0.6: {req_dir}/{ui_file} is missing required sections: "
                            f"{', '.join(missing)}"
                        )
                        if _require:
                            print_error(msg)
                            sys.exit(1)
                        else:
                            print_warning(msg + " — continuing with partial content")

                    # Content quality check (if enabled)
                    if config.design_reference.content_quality_check:
                        quality_issues = validate_ui_requirements_content(content)
                        if quality_issues and _fallback:
                            print_warning(
                                f"Phase 0.6: Content quality issues detected: "
                                f"{'; '.join(quality_issues)}. Generating fallback instead."
                            )
                            content = generate_fallback_ui_requirements(
                                task=effective_task, config=config, cwd=cwd,
                            )
                        elif quality_issues:
                            for issue in quality_issues:
                                print_warning(f"Phase 0.6: Quality issue: {issue}")

                    ui_requirements_content = content
                    cost_str = (
                        f" (${extraction_cost:.4f})"
                        if _backend == "api" and extraction_cost > 0
                        else ""
                    )
                    print_success(
                        f"Phase 0.6: {req_dir}/{ui_file} created successfully{cost_str}"
                    )
                except DesignExtractionError as exc:
                    # All retries exhausted — try fallback
                    if _fallback:
                        print_warning(
                            f"Phase 0.6: Extraction failed after retries: {exc}. "
                            f"Generating fallback."
                        )
                        try:
                            ui_requirements_content = generate_fallback_ui_requirements(
                                task=effective_task, config=config, cwd=cwd,
                            )
                            print_success(
                                f"Phase 0.6: Fallback {req_dir}/{ui_file} generated"
                            )
                        except Exception as fb_exc:
                            if _require:
                                print_error(
                                    f"Phase 0.6: Both extraction and fallback failed: {fb_exc}"
                                )
                                sys.exit(1)
                            else:
                                print_warning(
                                    f"Phase 0.6: Both extraction and fallback failed: {fb_exc}"
                                )
                    elif _require:
                        print_error(f"Phase 0.6: Design extraction failed: {exc}")
                        sys.exit(1)
                    else:
                        print_warning(
                            f"Phase 0.6: Design extraction failed: {exc} — "
                            f"continuing without UI requirements document"
                        )
                except Exception as exc:
                    if _require:
                        print_error(f"Phase 0.6: Unexpected error during extraction: {exc}")
                        sys.exit(1)
                    else:
                        print_warning(
                            f"Phase 0.6: Unexpected error: {exc} — "
                            f"continuing without UI requirements document"
                        )

        _current_state.completed_phases.append("design_extraction")

    else:
        # v10: Fallback UI requirements when no --design-ref provided
        if config.design_reference.fallback_generation:
            from .design_reference import (
                generate_fallback_ui_requirements,
                load_ui_requirements,
                validate_ui_requirements,
            )

            _current_state.current_phase = "design_extraction"
            req_dir = config.convergence.requirements_dir
            ui_file = config.design_reference.ui_requirements_file

            # Check for existing valid UI_REQUIREMENTS.md (resume scenario)
            existing = load_ui_requirements(cwd, config)
            if existing:
                missing = validate_ui_requirements(existing)
                if not missing:
                    print_info(
                        f"Phase 0.6: Reusing existing {req_dir}/{ui_file} "
                        f"(all required sections present)"
                    )
                    ui_requirements_content = existing
                else:
                    print_info(
                        f"Existing {req_dir}/{ui_file} is missing sections: "
                        f"{', '.join(missing)}. Regenerating fallback."
                    )

            if ui_requirements_content is None:
                print_info(
                    "Phase 0.6: No --design-ref provided — generating fallback UI requirements."
                )
                try:
                    ui_requirements_content = generate_fallback_ui_requirements(
                        task=effective_task, config=config, cwd=cwd,
                    )
                    print_success(
                        f"Phase 0.6: Fallback {req_dir}/{ui_file} generated "
                        f"(heuristic defaults from task/PRD analysis)"
                    )
                except Exception as exc:
                    print_warning(
                        f"Phase 0.6: Fallback UI generation failed: {exc}. "
                        f"Continuing without UI requirements."
                    )

            _current_state.completed_phases.append("design_extraction")

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
        _is_prd_mode = False
        milestone_convergence_report: ConvergenceReport | None = None
        depth = depth_override or "standard"
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
                    task_text=effective_task,
                    ui_requirements_content=ui_requirements_content,
                    user_overrides=user_overrides,
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

                # Route to milestone loop if PRD mode + milestone feature enabled
                _is_prd_mode = bool(args.prd) or interview_scope == "COMPLEX"

                # Apply depth-based quality gating (QUICK disables quality features)
                apply_depth_quality_gating(depth, config, user_overrides, prd_mode=_is_prd_mode)
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
                        ui_requirements_content=ui_requirements_content,
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

                    # Standard mode: lightweight tech research from task text
                    _std_tech_research = ""
                    _std_research_cost = 0.0
                    if config.tech_research.enabled:
                        try:
                            _std_research_cost, _std_result = asyncio.run(_run_tech_research(
                                cwd=cwd,
                                config=config,
                                prd_text=task,
                                master_plan_text="",
                                depth=depth,
                            ))
                            if _std_result:
                                from .tech_research import extract_research_summary
                                _std_tech_research = extract_research_summary(
                                    _std_result,
                                    max_chars=config.tech_research.injection_max_chars,
                                )
                        except Exception:
                            print_warning("Tech research failed (non-blocking)")

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
                        task_text=effective_task,
                        schedule_info=_schedule_str,
                        ui_requirements_content=ui_requirements_content,
                        tech_research_content=_std_tech_research,
                    ))
                    # Add tech research cost AFTER _run_single to avoid overwrite
                    if _std_research_cost > 0:
                        run_cost = (run_cost or 0.0) + _std_research_cost
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
            if ui_requirements_content:
                # Phase 0.6 already produced the document — mark complete immediately
                _current_state.artifacts["design_research_complete"] = "true"
            else:
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
    # v10.1: Post-orchestration Artifact Verification Gate
    # -------------------------------------------------------------------
    if _is_prd_mode and not _use_milestones:
        _req_path_check = (
            Path(cwd) / config.convergence.requirements_dir
            / config.convergence.requirements_file
        )
        if not _req_path_check.is_file():
            print_warning(
                "ARTIFACT RECOVERY: REQUIREMENTS.md not found after orchestration. "
                "Deploying recovery agent to generate from source code analysis."
            )
            recovery_types.append("artifact_recovery")
            try:
                _artifact_cost = asyncio.run(_run_artifact_recovery(
                    cwd=cwd,
                    config=config,
                    task_text=effective_task,
                    prd_path=getattr(args, "prd", None),
                    constraints=constraints,
                    intervention=intervention,
                    depth=depth,
                ))
                if _current_state:
                    _current_state.total_cost += _artifact_cost

                # Verify recovery produced the file
                if _req_path_check.is_file():
                    print_success("Artifact recovery: REQUIREMENTS.md generated successfully.")
                else:
                    print_warning("Artifact recovery completed but REQUIREMENTS.md still not found.")

                # Also check TASKS.md
                _tasks_path_check = (
                    Path(cwd) / config.convergence.requirements_dir / "TASKS.md"
                )
                if _tasks_path_check.is_file():
                    print_info("Artifact recovery: TASKS.md also generated.")
            except Exception as exc:
                print_warning(f"Artifact recovery failed: {exc}")
                print_warning(traceback.format_exc())
        else:
            print_info("Artifact verification: REQUIREMENTS.md exists (no recovery needed).")

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
                    task_text=effective_task,
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
            # Normalize milestone dirs before aggregation
            try:
                from .milestone_manager import normalize_milestone_dirs
                _norm = normalize_milestone_dirs(Path(cwd), config.convergence.requirements_dir)
                if _norm > 0:
                    print_info(f"Normalized {_norm} milestone directory path(s)")
            except Exception:
                pass
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
            if _is_prd_mode:
                # v10.1: Force recovery in PRD mode even when no requirements found.
                # Artifact recovery (Deliverable 10) should have created REQUIREMENTS.md,
                # but if it failed or produced no parseable checkboxes, we still want
                # the review fleet to deploy and establish baseline convergence.
                print_warning(
                    "UNKNOWN HEALTH in PRD mode — deploying mandatory review fleet "
                    "to establish baseline convergence."
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

    if needs_recovery:
        print_warning(
            f"RECOVERY PASS [review_recovery]: {convergence_report.checked_requirements}/"
            f"{convergence_report.total_requirements} requirements checked "
            f"({convergence_report.review_cycles} review cycles). Launching recovery pass."
        )
        recovery_types.append("review_recovery")
        pre_recovery_cycles = convergence_report.review_cycles
        pre_recovery_checked = convergence_report.checked_requirements
        try:
            recovery_cost = asyncio.run(_run_review_only(
                cwd=cwd,
                config=config,
                constraints=constraints,
                intervention=intervention,
                task_text=effective_task,
                checked=convergence_report.checked_requirements,
                total=convergence_report.total_requirements,
                review_cycles=convergence_report.review_cycles,
            ))
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
            # Verify cycle counter actually increased; adjust in-memory if needed
            if convergence_report.review_cycles <= pre_recovery_cycles:
                if pre_recovery_cycles == 0:
                    # GATE 5 scenario: recovery completed but LLM didn't add
                    # (review_cycles: N) markers.  A review cycle DID occur.
                    convergence_report.review_cycles = 1
                    print_info(
                        "Review recovery completed (GATE 5). "
                        "Cycle counter adjusted to 1."
                    )
                elif convergence_report.checked_requirements > pre_recovery_checked:
                    # Progress was made (more items checked) but markers not
                    # updated — adjust counter to reflect the completed cycle.
                    convergence_report.review_cycles = pre_recovery_cycles + 1
                    print_info(
                        f"Review recovery made progress "
                        f"({pre_recovery_checked} → {convergence_report.checked_requirements} checked). "
                        f"Cycle counter adjusted to {convergence_report.review_cycles}."
                    )
                else:
                    print_warning(
                        f"Review recovery did not increment cycle counter "
                        f"(before: {pre_recovery_cycles}, after: {convergence_report.review_cycles})."
                    )
                # Persist adjusted counter
                if _current_state:
                    _current_state.convergence_cycles = convergence_report.review_cycles
        except Exception as exc:
            print_warning(f"Review recovery pass failed: {exc}")

    # -------------------------------------------------------------------
    # End-of-run: Audit-Team parallel review (after review recovery)
    # -------------------------------------------------------------------
    audit_report: AuditTeamReport | None = None
    if config.audit_team.enabled and config.audit_team.end_of_run:
        # Resume guard — skip if already completed in a previous run
        if _current_state and "audit_team" in _current_state.completed_phases:
            print_info("Audit-team already completed in previous run, skipping.")
        else:
            if _current_state:
                _current_state.current_phase = "audit_team"
            try:
                audit_cost, audit_report = asyncio.run(_run_audit_team(
                    cwd=cwd,
                    config=config,
                    depth=depth,
                    constraints=constraints,
                    intervention=intervention,
                    task_text=effective_task,
                    scope_label="end-of-run",
                ))
                if _current_state:
                    _current_state.total_cost += audit_cost
                    _current_state.audit_score = audit_report.overall_score
                    _current_state.audit_health = audit_report.health
                    _current_state.audit_fix_rounds = audit_report.fix_rounds_used
                if audit_report.health == "passed":
                    print_success(
                        f"Audit-team passed: score={audit_report.overall_score:.2f}, "
                        f"{audit_report.total_pass} pass, {audit_report.total_fail} fail."
                    )
                elif audit_report.health == "critical":
                    print_warning(
                        f"Audit-team CRITICAL: score={audit_report.overall_score:.2f}, "
                        f"{audit_report.total_fail} failures after {audit_report.fix_rounds_used} fix rounds."
                    )
                else:
                    print_info(
                        f"Audit-team needs-fixes: score={audit_report.overall_score:.2f}, "
                        f"{audit_report.total_fail} failures after {audit_report.fix_rounds_used} fix rounds."
                    )
                # NOTE: "critical" health is intentionally NOT marked complete.
                # On resume, the audit will re-run to give another chance after
                # potential manual or intermediate fixes between runs.
                if _current_state and audit_report and audit_report.health in ("passed", "needs-fixes"):
                    _current_state.completed_phases.append("audit_team")
            except Exception as exc:
                print_warning(f"Audit-team failed: {exc}\n{traceback.format_exc()}")

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
            if changed:
                scan_scope = ScanScope(
                    mode="changed_only" if depth == "quick" else "changed_and_imports",
                    changed_files=changed,
                )
        except Exception:
            pass  # Fall back to full scan on any error

    # -------------------------------------------------------------------
    # Post-orchestration: Mock data scan (standard + milestone modes)
    # -------------------------------------------------------------------
    # In milestone mode, each milestone already runs mock scanning.
    # For standard (non-milestone) mode, scan here as a final safety net.
    if not _use_milestones and (config.post_orchestration_scans.mock_data_scan or config.milestone.mock_data_scan):
        try:
            from .quality_checks import run_mock_data_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                mock_violations = run_mock_data_scan(Path(cwd), scope=scan_scope)
                if mock_violations:
                    if _fix_pass > 0:
                        print_info(f"Mock data scan pass {_fix_pass + 1}: {len(mock_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Post-orchestration mock data scan: {len(mock_violations)} "
                            f"mock data violation(s) found in service files."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("mock_data_fix")
                    if _max_passes > 0:
                        try:
                            mock_fix_cost = asyncio.run(_run_mock_data_fix(
                                cwd=cwd,
                                config=config,
                                mock_violations=mock_violations,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += mock_fix_cost
                        except Exception as exc:
                            print_warning(f"Mock data fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Mock data scan: 0 violations (clean)")
                    else:
                        print_info(f"Mock data scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Mock data scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: UI compliance scan (standard mode only)
    # -------------------------------------------------------------------
    # In milestone mode, each milestone already runs UI compliance scanning.
    # For standard (non-milestone) mode, scan here as a final safety net.
    if not _use_milestones and (config.post_orchestration_scans.ui_compliance_scan or config.milestone.ui_compliance_scan):
        try:
            from .quality_checks import run_ui_compliance_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                ui_violations = run_ui_compliance_scan(Path(cwd), scope=scan_scope)
                if ui_violations:
                    if _fix_pass > 0:
                        print_info(f"UI compliance scan pass {_fix_pass + 1}: {len(ui_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Post-orchestration UI compliance scan: {len(ui_violations)} "
                            f"UI compliance violation(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("ui_compliance_fix")
                    if _max_passes > 0:
                        try:
                            ui_fix_cost = asyncio.run(_run_ui_compliance_fix(
                                cwd=cwd,
                                config=config,
                                ui_violations=ui_violations,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += ui_fix_cost
                        except Exception as exc:
                            print_warning(f"UI compliance fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("UI compliance scan: 0 violations (clean)")
                    else:
                        print_info(f"UI compliance scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"UI compliance scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Integrity Scans (deployment, asset, PRD)
    # -------------------------------------------------------------------
    # Scan 1: Deployment integrity — docker-compose vs code consistency
    if config.integrity_scans.deployment_scan:
        try:
            from .quality_checks import run_deployment_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                deploy_violations = run_deployment_scan(Path(cwd))
                if deploy_violations:
                    if _fix_pass > 0:
                        print_info(f"Deployment integrity scan pass {_fix_pass + 1}: {len(deploy_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Deployment integrity scan: {len(deploy_violations)} "
                            f"issue(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("deployment_integrity_fix")
                    if _max_passes > 0:
                        try:
                            deploy_fix_cost = asyncio.run(_run_integrity_fix(
                                cwd=cwd,
                                config=config,
                                violations=deploy_violations,
                                scan_type="deployment",
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += deploy_fix_cost
                        except Exception as exc:
                            print_warning(f"Deployment integrity fix failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Deployment integrity scan: 0 violations (clean)")
                    else:
                        print_info(f"Deployment integrity scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Deployment integrity scan failed: {exc}")

    # Scan 2: Asset integrity — broken static references
    if config.integrity_scans.asset_scan:
        try:
            from .quality_checks import run_asset_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                asset_violations = run_asset_scan(Path(cwd), scope=scan_scope)
                if asset_violations:
                    if _fix_pass > 0:
                        print_info(f"Asset integrity scan pass {_fix_pass + 1}: {len(asset_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Asset integrity scan: {len(asset_violations)} "
                            f"broken reference(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("asset_integrity_fix")
                    if _max_passes > 0:
                        try:
                            asset_fix_cost = asyncio.run(_run_integrity_fix(
                                cwd=cwd,
                                config=config,
                                violations=asset_violations,
                                scan_type="asset",
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += asset_fix_cost
                        except Exception as exc:
                            print_warning(f"Asset integrity fix failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Asset integrity scan: 0 violations (clean)")
                    else:
                        print_info(f"Asset integrity scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Asset integrity scan failed: {exc}")

    # Scan 3: PRD reconciliation — quantitative claim verification (LLM-based)
    _should_run_prd_recon = config.integrity_scans.prd_reconciliation
    if _should_run_prd_recon and depth == "thorough":
        # M2 fix: crash-isolate the quality gate file I/O (TOCTOU safe)
        try:
            _req_path = Path(cwd) / config.convergence.requirements_dir / config.convergence.requirements_file
            if _req_path.is_file():
                _req_size = _req_path.stat().st_size
                _req_content = _req_path.read_text(encoding="utf-8", errors="replace")
                _has_req_items = bool(re.search(r"REQ-\d{3}", _req_content))
                if _req_size < 500 or not _has_req_items:
                    _should_run_prd_recon = False
            else:
                _should_run_prd_recon = False
        except OSError:
            pass  # Safe fallback: run reconciliation if gate check fails
    if _should_run_prd_recon:
        try:
            prd_recon_cost = asyncio.run(_run_prd_reconciliation(
                cwd=cwd,
                config=config,
                task_text=effective_task,
                constraints=constraints,
                intervention=intervention,
                depth=depth if not _use_milestones else "standard",
            ))
            if _current_state:
                _current_state.total_cost += prd_recon_cost

            # Parse the generated report for violations
            from .quality_checks import parse_prd_reconciliation
            recon_path = Path(cwd) / config.convergence.requirements_dir / "PRD_RECONCILIATION.md"
            prd_violations = parse_prd_reconciliation(recon_path)
            if prd_violations:
                print_warning(
                    f"PRD reconciliation: {len(prd_violations)} "
                    f"mismatch(es) found between PRD claims and implementation."
                )
                recovery_types.append("prd_reconciliation_mismatch")
        except Exception as exc:
            print_warning(f"PRD reconciliation scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Database Integrity Scans
    # -------------------------------------------------------------------

    # Scan 1: Dual ORM type consistency
    if config.database_scans.dual_orm_scan:
        try:
            from .quality_checks import run_dual_orm_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                db_dual_violations = run_dual_orm_scan(Path(cwd), scope=scan_scope)
                if db_dual_violations:
                    if _fix_pass > 0:
                        print_info(f"Dual ORM scan pass {_fix_pass + 1}: {len(db_dual_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Dual ORM scan: {len(db_dual_violations)} "
                            f"type mismatch(es) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("database_dual_orm_fix")
                    if _max_passes > 0:
                        try:
                            fix_cost = asyncio.run(
                                _run_integrity_fix(
                                    cwd=cwd,
                                    config=config,
                                    violations=db_dual_violations,
                                    scan_type="database_dual_orm",
                                    task_text=effective_task,
                                    constraints=constraints,
                                    intervention=intervention,
                                    depth=depth if not _use_milestones else "standard",
                                )
                            )
                            if _current_state:
                                _current_state.total_cost += fix_cost
                        except Exception as exc:
                            print_warning(
                                f"Database dual ORM fix recovery failed: {exc}\n"
                                f"{traceback.format_exc()}"
                            )
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Dual ORM scan: 0 violations (clean)")
                    else:
                        print_info(f"Dual ORM scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Dual ORM scan failed: {exc}")

    # Scan 2: Default value & nullability
    if config.database_scans.default_value_scan:
        try:
            from .quality_checks import run_default_value_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                db_default_violations = run_default_value_scan(Path(cwd), scope=scan_scope)
                if db_default_violations:
                    if _fix_pass > 0:
                        print_info(f"Default value scan pass {_fix_pass + 1}: {len(db_default_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Default value scan: {len(db_default_violations)} "
                            f"issue(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("database_default_value_fix")
                    if _max_passes > 0:
                        try:
                            fix_cost = asyncio.run(
                                _run_integrity_fix(
                                    cwd=cwd,
                                    config=config,
                                    violations=db_default_violations,
                                    scan_type="database_defaults",
                                    task_text=effective_task,
                                    constraints=constraints,
                                    intervention=intervention,
                                    depth=depth if not _use_milestones else "standard",
                                )
                            )
                            if _current_state:
                                _current_state.total_cost += fix_cost
                        except Exception as exc:
                            print_warning(
                                f"Database default value fix recovery failed: {exc}\n"
                                f"{traceback.format_exc()}"
                            )
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Default value scan: 0 violations (clean)")
                    else:
                        print_info(f"Default value scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Default value scan failed: {exc}")

    # Scan 3: ORM relationship completeness
    if config.database_scans.relationship_scan:
        try:
            from .quality_checks import run_relationship_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                db_rel_violations = run_relationship_scan(Path(cwd), scope=scan_scope)
                if db_rel_violations:
                    if _fix_pass > 0:
                        print_info(f"Relationship scan pass {_fix_pass + 1}: {len(db_rel_violations)} residual violation(s)")
                    else:
                        print_warning(
                            f"Relationship scan: {len(db_rel_violations)} "
                            f"issue(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("database_relationship_fix")
                    if _max_passes > 0:
                        try:
                            fix_cost = asyncio.run(
                                _run_integrity_fix(
                                    cwd=cwd,
                                    config=config,
                                    violations=db_rel_violations,
                                    scan_type="database_relationships",
                                    task_text=effective_task,
                                    constraints=constraints,
                                    intervention=intervention,
                                    depth=depth if not _use_milestones else "standard",
                                )
                            )
                            if _current_state:
                                _current_state.total_cost += fix_cost
                        except Exception as exc:
                            print_warning(
                                f"Database relationship fix recovery failed: {exc}\n"
                                f"{traceback.format_exc()}"
                            )
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Relationship scan: 0 violations (clean)")
                    else:
                        print_info(f"Relationship scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Relationship scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: API Contract Verification scan
    # -------------------------------------------------------------------
    if config.post_orchestration_scans.api_contract_scan:
        try:
            from .quality_checks import run_api_contract_scan
            from .e2e_testing import detect_app_type as _detect_app
            _app_info = _detect_app(Path(cwd))
            if _app_info.has_backend and _app_info.has_frontend:
                _max_passes = config.post_orchestration_scans.max_scan_fix_passes
                for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                    api_contract_violations = run_api_contract_scan(Path(cwd), scope=scan_scope)
                    if api_contract_violations:
                        if _fix_pass > 0:
                            print_info(f"API contract scan pass {_fix_pass + 1}: {len(api_contract_violations)} residual violation(s)")
                        else:
                            print_warning(
                                f"API contract scan: {len(api_contract_violations)} "
                                f"field mismatch violation(s) found."
                            )
                        if _fix_pass == 0:
                            recovery_types.append("api_contract_fix")
                        if _max_passes > 0:
                            try:
                                api_fix_cost = asyncio.run(_run_api_contract_fix(
                                    cwd=cwd,
                                    config=config,
                                    api_violations=api_contract_violations,
                                    task_text=effective_task,
                                    constraints=constraints,
                                    intervention=intervention,
                                    depth=depth if not _use_milestones else "standard",
                                ))
                                if _current_state:
                                    _current_state.total_cost += api_fix_cost
                            except Exception as exc:
                                print_warning(f"API contract fix recovery failed: {exc}")
                                break
                        else:
                            break  # scan-only mode
                    else:
                        if _fix_pass == 0:
                            print_info("API contract scan: 0 violations (clean)")
                        else:
                            print_info(f"API contract scan pass {_fix_pass + 1}: all violations resolved")
                        break
            else:
                print_info("API contract scan: skipped (not a full-stack app).")
        except Exception as exc:
            print_warning(f"API contract scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Silent Data Loss scan (SDL-001)
    # -------------------------------------------------------------------
    if config.post_orchestration_scans.silent_data_loss_scan:
        try:
            from .quality_checks import _check_cqrs_persistence
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                sdl_violations = _check_cqrs_persistence(Path(cwd), scope=scan_scope)
                if sdl_violations:
                    if _fix_pass > 0:
                        print_info(f"SDL scan pass {_fix_pass + 1}: {len(sdl_violations)} residual violation(s)")
                    else:
                        for v in sdl_violations[:5]:
                            print_contract_violation(f"[{v.check}] {v.message}")
                        print_warning(
                            f"Silent data loss scan: {len(sdl_violations)} "
                            f"violation(s) found."
                        )
                    if _fix_pass == 0:
                        recovery_types.append("silent_data_loss_fix")
                    if _max_passes > 0:
                        try:
                            sdl_fix_cost = asyncio.run(_run_silent_data_loss_fix(
                                cwd=cwd,
                                config=config,
                                sdl_violations=sdl_violations,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += sdl_fix_cost
                        except Exception as exc:
                            print_warning(f"SDL fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        print_info("Silent data loss scan: 0 violations (clean)")
                    else:
                        print_info(f"SDL scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Silent data loss scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: Endpoint Cross-Reference scan (XREF-001)
    # -------------------------------------------------------------------
    if config.post_orchestration_scans.endpoint_xref_scan:
        try:
            from .quality_checks import run_endpoint_xref_scan
            _max_passes = config.post_orchestration_scans.max_scan_fix_passes
            for _fix_pass in range(max(1, _max_passes) if _max_passes > 0 else 1):
                xref_violations = run_endpoint_xref_scan(Path(cwd), scope=scan_scope)
                # Only actionable (error/warning) violations should trigger fix passes;
                # "info" violations are unresolvable function-call URLs demoted by the scanner.
                _xref_actionable = [v for v in xref_violations if v.severity != "info"]
                _xref_info_only = len(xref_violations) - len(_xref_actionable)
                if _xref_actionable:
                    if _fix_pass > 0:
                        print_info(f"Endpoint XREF scan pass {_fix_pass + 1}: {len(_xref_actionable)} residual violation(s)")
                    else:
                        for v in _xref_actionable[:5]:
                            print_contract_violation(f"[{v.check}] {v.message}")
                        print_warning(
                            f"Endpoint XREF scan: {len(_xref_actionable)} "
                            f"violation(s) found."
                            + (f" ({_xref_info_only} info-only skipped)" if _xref_info_only else "")
                        )
                    if _fix_pass == 0:
                        recovery_types.append("endpoint_xref_fix")
                    if _max_passes > 0:
                        try:
                            xref_fix_cost = asyncio.run(_run_endpoint_xref_fix(
                                cwd=cwd,
                                config=config,
                                xref_violations=_xref_actionable,
                                task_text=effective_task,
                                constraints=constraints,
                                intervention=intervention,
                                depth=depth if not _use_milestones else "standard",
                            ))
                            if _current_state:
                                _current_state.total_cost += xref_fix_cost
                        except Exception as exc:
                            print_warning(f"Endpoint XREF fix recovery failed: {exc}")
                            break
                    else:
                        break  # scan-only mode
                else:
                    if _fix_pass == 0:
                        if _xref_info_only:
                            print_info(f"Endpoint XREF scan: 0 actionable violations ({_xref_info_only} info-only)")
                        else:
                            print_info("Endpoint XREF scan: 0 violations (clean)")
                    else:
                        print_info(f"Endpoint XREF scan pass {_fix_pass + 1}: all violations resolved")
                    break
        except Exception as exc:
            print_warning(f"Endpoint XREF scan failed: {exc}")

    # -------------------------------------------------------------------
    # Post-orchestration: E2E Testing Phase (after all other scans)
    # -------------------------------------------------------------------
    e2e_report = E2ETestReport()
    e2e_cost = 0.0
    if config.e2e_testing.enabled:
        if _current_state:
            _current_state.current_phase = "e2e_testing"
            try:
                from .state import save_state as _save_state_e2e
                _save_state_e2e(_current_state, directory=str(Path(cwd) / ".agent-team"))
            except Exception:
                pass

        try:
            app_info = detect_app_type(Path(cwd))

            # Generate E2E Coverage Matrix (if enabled)
            if config.tracking_documents.e2e_coverage_matrix:
                try:
                    from .tracking_documents import generate_e2e_coverage_matrix
                    req_dir = Path(cwd) / config.convergence.requirements_dir
                    req_file = req_dir / "REQUIREMENTS.md"
                    if req_file.is_file():
                        req_content = req_file.read_text(encoding="utf-8")
                        matrix_content = generate_e2e_coverage_matrix(
                            requirements_content=req_content,
                            app_info=app_info,
                        )
                        matrix_path = req_dir / "E2E_COVERAGE_MATRIX.md"
                        matrix_path.write_text(matrix_content, encoding="utf-8")
                        print_info(f"Generated E2E coverage matrix: {matrix_path}")
                except Exception as exc:
                    print_warning(f"Failed to generate E2E coverage matrix: {exc}")

            # Check completed phases for resume logic
            backend_already_done = (
                _current_state
                and "e2e_backend" in _current_state.completed_phases
            )
            frontend_already_done = (
                _current_state
                and "e2e_frontend" in _current_state.completed_phases
            )

            # Part 1: Backend API E2E
            if (config.e2e_testing.backend_api_tests
                    and app_info.has_backend
                    and not backend_already_done):
                api_cost, api_report = asyncio.run(_run_backend_e2e_tests(
                    cwd=cwd, config=config, app_info=app_info,
                    task_text=effective_task, constraints=constraints,
                    intervention=intervention,
                    depth=depth if not _use_milestones else "standard",
                ))
                e2e_cost += api_cost
                e2e_report.backend_total = api_report.backend_total
                e2e_report.backend_passed = api_report.backend_passed
                e2e_report.failed_tests.extend(api_report.failed_tests)

                # Fix loop — only run if health indicates actual test failures
                retries = 0
                while (api_report.health not in ("passed", "skipped", "unknown")
                       and retries < config.e2e_testing.max_fix_retries):
                    fix_cost = asyncio.run(_run_e2e_fix(
                        cwd=cwd, config=config,
                        failures=api_report.failed_tests,
                        test_type="backend_api",
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention,
                        depth=depth if not _use_milestones else "standard",
                    ))
                    e2e_cost += fix_cost
                    rerun_cost, api_report = asyncio.run(_run_backend_e2e_tests(
                        cwd=cwd, config=config, app_info=app_info,
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention,
                        depth=depth if not _use_milestones else "standard",
                    ))
                    e2e_cost += rerun_cost
                    retries += 1
                    e2e_report.fix_retries_used += 1
                    e2e_report.total_fix_cycles += 1
                    # Update report with latest results
                    e2e_report.backend_total = api_report.backend_total
                    e2e_report.backend_passed = api_report.backend_passed
                    e2e_report.failed_tests = api_report.failed_tests[:]

                if api_report.health not in ("passed", "skipped"):
                    recovery_types.append("e2e_backend_fix")

                # Only mark backend phase complete when tests actually ran and passed (or partial)
                if _current_state and api_report.health in ("passed", "partial"):
                    _current_state.completed_phases.append("e2e_backend")
                    try:
                        from .state import save_state as _save_state_e2e2
                        _save_state_e2e2(_current_state, directory=str(Path(cwd) / ".agent-team"))
                    except Exception:
                        pass

            elif backend_already_done:
                print_info("Resuming: e2e_backend already completed, skipping")
            elif config.e2e_testing.skip_if_no_api and not app_info.has_backend:
                e2e_report.skipped = True
                e2e_report.skip_reason = "No backend API detected"

            # Compute backend pass rate for frontend gate
            if e2e_report.backend_total > 0:
                backend_pass_rate = e2e_report.backend_passed / e2e_report.backend_total
            else:
                backend_pass_rate = 1.0
            backend_ok = (
                not config.e2e_testing.backend_api_tests
                or not app_info.has_backend
                or backend_pass_rate >= 0.7
            )

            if backend_ok and 0.7 <= backend_pass_rate < 1.0:
                print_warning(
                    f"Backend API E2E: {backend_pass_rate * 100:.0f}% passed — "
                    "proceeding with frontend E2E (some failures may be backend-related)"
                )

            # Part 2: Frontend Playwright
            if (config.e2e_testing.frontend_playwright_tests
                    and app_info.has_frontend
                    and backend_ok
                    and not frontend_already_done):
                pw_cost, pw_report = asyncio.run(_run_frontend_e2e_tests(
                    cwd=cwd, config=config, app_info=app_info,
                    task_text=effective_task, constraints=constraints,
                    intervention=intervention,
                    depth=depth if not _use_milestones else "standard",
                ))
                e2e_cost += pw_cost
                e2e_report.frontend_total = pw_report.frontend_total
                e2e_report.frontend_passed = pw_report.frontend_passed
                e2e_report.failed_tests.extend(pw_report.failed_tests)

                # Fix loop — only run if health indicates actual test failures
                retries = 0
                while (pw_report.health not in ("passed", "skipped", "unknown")
                       and retries < config.e2e_testing.max_fix_retries):
                    fix_cost = asyncio.run(_run_e2e_fix(
                        cwd=cwd, config=config,
                        failures=pw_report.failed_tests,
                        test_type="frontend_playwright",
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention,
                        depth=depth if not _use_milestones else "standard",
                    ))
                    e2e_cost += fix_cost
                    rerun_cost, pw_report = asyncio.run(_run_frontend_e2e_tests(
                        cwd=cwd, config=config, app_info=app_info,
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention,
                        depth=depth if not _use_milestones else "standard",
                    ))
                    e2e_cost += rerun_cost
                    retries += 1
                    e2e_report.fix_retries_used += 1
                    e2e_report.total_fix_cycles += 1
                    e2e_report.frontend_total = pw_report.frontend_total
                    e2e_report.frontend_passed = pw_report.frontend_passed
                    e2e_report.failed_tests = pw_report.failed_tests[:]

                if pw_report.health not in ("passed", "skipped"):
                    recovery_types.append("e2e_frontend_fix")

                # Only mark frontend phase complete when tests actually ran and passed (or partial)
                if _current_state and pw_report.health in ("passed", "partial"):
                    _current_state.completed_phases.append("e2e_frontend")
                    try:
                        from .state import save_state as _save_state_e2e3
                        _save_state_e2e3(_current_state, directory=str(Path(cwd) / ".agent-team"))
                    except Exception:
                        pass

            elif frontend_already_done:
                print_info("Resuming: e2e_frontend already completed, skipping")
            elif config.e2e_testing.skip_if_no_frontend and not app_info.has_frontend:
                if not e2e_report.skip_reason:
                    e2e_report.skip_reason = "No frontend detected"
                print_info("E2E: No frontend detected — skipping Playwright tests")
            elif not backend_ok:
                print_warning(
                    f"E2E: Backend pass rate {backend_pass_rate * 100:.0f}% below 70% threshold — "
                    "skipping frontend Playwright tests"
                )

            # Compute overall health
            total = e2e_report.backend_total + e2e_report.frontend_total
            passed = e2e_report.backend_passed + e2e_report.frontend_passed
            if total == 0:
                e2e_report.health = "skipped"
                if not e2e_report.skip_reason:
                    e2e_report.skip_reason = "No tests executed"
            elif passed == total:
                e2e_report.health = "passed"
            elif total > 0 and passed / total >= 0.7:
                e2e_report.health = "partial"
            else:
                e2e_report.health = "failed"

            if _current_state:
                _current_state.total_cost += e2e_cost
                _current_state.completed_phases.append("e2e_testing")

            # Display E2E results
            print_info(
                f"E2E Testing Phase complete — "
                f"Health: {e2e_report.health.upper()} | "
                f"Backend: {e2e_report.backend_passed}/{e2e_report.backend_total} | "
                f"Frontend: {e2e_report.frontend_passed}/{e2e_report.frontend_total} | "
                f"Fix cycles: {e2e_report.total_fix_cycles} | "
                f"Cost: ${e2e_cost:.2f}"
            )

            # Parse E2E coverage matrix stats (if enabled)
            if config.tracking_documents.e2e_coverage_matrix:
                try:
                    from .tracking_documents import parse_e2e_coverage_matrix
                    matrix_path = Path(cwd) / config.convergence.requirements_dir / "E2E_COVERAGE_MATRIX.md"
                    if matrix_path.is_file():
                        stats = parse_e2e_coverage_matrix(matrix_path.read_text(encoding="utf-8"))
                        print_info(
                            f"E2E Coverage: {stats.tests_written}/{stats.total_items} tests written "
                            f"({stats.coverage_ratio:.0%}), {stats.tests_passed}/{stats.tests_written} passing "
                            f"({stats.pass_ratio:.0%})"
                        )
                        if stats.coverage_ratio < config.tracking_documents.coverage_completeness_gate:
                            print_warning(
                                f"E2E coverage ({stats.coverage_ratio:.0%}) below gate "
                                f"({config.tracking_documents.coverage_completeness_gate:.0%}). "
                                f"Some requirements may not have E2E tests."
                            )
                            recovery_types.append("e2e_coverage_incomplete")
                except Exception as exc:
                    print_warning(f"Failed to parse E2E coverage matrix: {exc}")

        except Exception as exc:
            print_warning(f"E2E testing phase failed: {exc}\n{traceback.format_exc()}")
            e2e_report.health = "failed"
            e2e_report.skip_reason = f"Phase error: {exc}"

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
                    print_warning(f"  [{_v.check}] {_v.file_path}:{_v.line} — {_v.message}")
            else:
                print_info("E2E quality scan: 0 violations (clean)")
        except Exception as exc:
            print_warning(f"E2E quality scan failed: {exc}")

    # ------------------------------------------------------------------
    # Post-orchestration: Browser MCP Interactive Testing Phase
    # ------------------------------------------------------------------
    browser_report = BrowserTestReport()
    browser_cost = 0.0
    _browser_app_started = False  # Track if we started the app (for cleanup)
    _browser_app_port = 0
    if config.browser_testing.enabled:
        try:
            print_info("Browser MCP Interactive Testing Phase")

            # Gate: E2E pass rate
            e2e_total = e2e_report.backend_total + e2e_report.frontend_total
            e2e_passed = e2e_report.backend_passed + e2e_report.frontend_passed

            if e2e_total == 0:
                print_info("Browser testing skipped: E2E phase did not run")
                browser_report.health = "skipped"
                browser_report.skip_reason = "E2E phase did not run"
            elif (e2e_passed / e2e_total) < config.browser_testing.e2e_pass_rate_gate:
                e2e_rate = e2e_passed / e2e_total
                print_warning(
                    f"Browser testing skipped: E2E pass rate {e2e_rate:.0%} "
                    f"< {config.browser_testing.e2e_pass_rate_gate:.0%}"
                )
                browser_report.health = "skipped"
                browser_report.skip_reason = "E2E pass rate below gate"
            elif _current_state and "browser_testing" in _current_state.completed_phases:
                print_info("Resuming: browser_testing already completed")
            else:
                from .browser_testing import (
                    check_app_running,
                    generate_browser_workflows,
                    verify_workflow_execution,
                    check_screenshot_diversity,
                    write_workflow_state,
                    update_workflow_state,
                    count_screenshots,
                    generate_readiness_report,
                    generate_unresolved_issues,
                )

                if _current_state:
                    _current_state.current_phase = "browser_testing"

                # Create directories
                browser_base = Path(cwd) / config.convergence.requirements_dir / "browser-workflows"
                bw_workflows_dir = browser_base / "workflows"
                bw_results_dir = browser_base / "results"
                bw_screenshots_dir = browser_base / "screenshots"
                bw_workflows_dir.mkdir(parents=True, exist_ok=True)
                bw_results_dir.mkdir(parents=True, exist_ok=True)
                bw_screenshots_dir.mkdir(parents=True, exist_ok=True)

                # Step 1: App startup — health check first, agent as fallback
                port = config.browser_testing.app_port
                if port == 0:
                    port = config.e2e_testing.test_port
                if port == 0:
                    try:
                        from .e2e_testing import detect_app_type as _detect_app_type_browser
                        _app_type_browser = _detect_app_type_browser(Path(cwd))
                        if _app_type_browser and _app_type_browser.test_port:
                            port = _app_type_browser.test_port
                    except Exception:
                        pass
                if port == 0:
                    port = 3000

                app_url = f"http://localhost:{port}"

                if check_app_running(port):
                    print_info(f"App running on port {port} — reusing from E2E phase")
                else:
                    print_info(f"App not running on port {port} — starting via startup agent")
                    startup_cost, startup_info = asyncio.run(_run_browser_startup_agent(
                        cwd, config, browser_base,
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention, depth=depth,
                    ))
                    browser_cost += startup_cost
                    _browser_app_started = True
                    if startup_info.port:
                        port = startup_info.port
                        app_url = f"http://localhost:{port}"
                    _browser_app_port = port

                    if not check_app_running(port):
                        print_warning("App startup failed — skipping browser testing")
                        browser_report.health = "failed"
                        browser_report.skip_reason = "App startup failed"
                        raise RuntimeError("App startup failed")

                # Step 2: Workflow generation (deterministic Python)
                coverage_matrix_path = Path(cwd) / config.convergence.requirements_dir / "E2E_COVERAGE_MATRIX.md"
                if not coverage_matrix_path.is_file():
                    coverage_matrix_path = None

                app_info_browser = None
                try:
                    from .e2e_testing import detect_app_type as _detect_app_type_wf
                    app_info_browser = _detect_app_type_wf(Path(cwd))
                except Exception:
                    pass

                requirements_dir = Path(cwd) / config.convergence.requirements_dir
                workflow_defs = generate_browser_workflows(
                    requirements_dir, coverage_matrix_path, app_info_browser, Path(cwd),
                )

                if not workflow_defs:
                    print_warning("No browser workflows generated — skipping")
                    browser_report.health = "failed"
                    browser_report.skip_reason = "No workflows generated"
                    raise RuntimeError("No workflows generated")

                browser_report.total_workflows = len(workflow_defs)
                write_workflow_state(bw_workflows_dir, workflow_defs)

                print_info(f"Generated {len(workflow_defs)} browser workflows")

                # Step 3: Sequential workflow execution
                any_fixes_applied = False
                workflow_results: dict[int, WorkflowResult] = {}

                for wf in workflow_defs:
                    # Resume check
                    if _current_state and wf.id in _current_state.completed_browser_workflows:
                        print_info(f"Workflow {wf.id} already completed — skipping")
                        continue

                    # Prerequisite check
                    failed_deps = [
                        dep for dep in wf.depends_on
                        if dep in workflow_results and workflow_results[dep].health in ("failed", "skipped")
                    ]
                    if failed_deps:
                        dep_str = ", ".join(str(d) for d in failed_deps)
                        print_warning(f"Workflow {wf.id} skipped: prerequisite(s) {dep_str} failed/skipped")
                        wr = WorkflowResult(
                            workflow_id=wf.id,
                            workflow_name=wf.name,
                            health="skipped",
                            failure_reason=f"Prerequisites failed/skipped: {dep_str}",
                        )
                        workflow_results[wf.id] = wr
                        browser_report.workflow_results.append(wr)
                        browser_report.skipped_workflows += 1
                        update_workflow_state(bw_workflows_dir, wf.id, "SKIPPED")
                        continue

                    update_workflow_state(bw_workflows_dir, wf.id, "IN_PROGRESS")

                    # Execute with fix loop
                    retries = 0
                    workflow_passed = False

                    while not workflow_passed and retries <= config.browser_testing.max_fix_retries:
                        exec_cost, wr = asyncio.run(_run_browser_workflow_executor(
                            cwd, config, wf, bw_workflows_dir, app_url,
                            task_text=effective_task, constraints=constraints,
                            intervention=intervention, depth=depth,
                        ))
                        browser_cost += exec_cost

                        # Structural verification
                        verified, issues = verify_workflow_execution(bw_workflows_dir, wf.id, wf.total_steps)
                        diverse = check_screenshot_diversity(bw_screenshots_dir, wf.id, wf.total_steps)

                        if verified and diverse and wr.health == "passed":
                            workflow_passed = True
                            break

                        if not verified:
                            print_warning(f"Workflow {wf.id} verification failed: {'; '.join(issues[:3])}")
                            wr.health = "failed"
                            if not wr.failure_reason:
                                wr.failure_reason = "; ".join(issues[:3])
                        if not diverse:
                            print_warning(f"Workflow {wf.id} screenshots not diverse enough")

                        if retries >= config.browser_testing.max_fix_retries:
                            break

                        # Fix pass
                        fix_cost = asyncio.run(_run_browser_workflow_fix(
                            cwd, config, wf, wr, bw_workflows_dir,
                            task_text=effective_task, constraints=constraints,
                            intervention=intervention, depth=depth,
                        ))
                        browser_cost += fix_cost
                        retries += 1
                        any_fixes_applied = True
                        browser_report.total_fix_cycles += 1

                    # Record result
                    wr.fix_retries_used = retries
                    workflow_results[wf.id] = wr
                    browser_report.workflow_results.append(wr)

                    if workflow_passed:
                        browser_report.passed_workflows += 1
                        update_workflow_state(bw_workflows_dir, wf.id, "PASSED", retries, count_screenshots(bw_screenshots_dir))
                        if _current_state:
                            _current_state.completed_browser_workflows.append(wf.id)
                    else:
                        browser_report.failed_workflows += 1
                        update_workflow_state(bw_workflows_dir, wf.id, "FAILED", retries, count_screenshots(bw_screenshots_dir))
                        recovery_types.append("browser_testing_failed")

                    if _current_state:
                        _current_state.total_cost += browser_cost
                        from .state import save_state as _save_state_browser
                        _save_state_browser(_current_state, directory=str(Path(cwd) / ".agent-team"))

                # Step 4: Regression sweep
                if (
                    config.browser_testing.regression_sweep
                    and any_fixes_applied
                    and browser_report.passed_workflows > 0
                ):
                    print_info("Running regression sweep...")
                    passed_wfs = [wf for wf in workflow_defs if workflow_results.get(wf.id) and workflow_results[wf.id].health == "passed"]
                    sweep_cost, regressed_ids = asyncio.run(_run_browser_regression_sweep(
                        cwd, config, passed_wfs, bw_workflows_dir, app_url,
                        task_text=effective_task, constraints=constraints,
                        intervention=intervention, depth=depth,
                    ))
                    browser_cost += sweep_cost

                    if regressed_ids:
                        print_warning(f"Regression detected in workflows: {regressed_ids}")
                        all_regressions_fixed = True
                        for reg_id in regressed_ids:
                            reg_wf = next((w for w in workflow_defs if w.id == reg_id), None)
                            if reg_wf:
                                reg_result = workflow_results.get(reg_id)
                                if reg_result:
                                    fix_cost = asyncio.run(_run_browser_workflow_fix(
                                        cwd, config, reg_wf, reg_result, bw_workflows_dir,
                                        task_text=effective_task, constraints=constraints,
                                        intervention=intervention, depth=depth,
                                    ))
                                    browser_cost += fix_cost
                                    # Re-execute to verify fix worked
                                    reexec_cost, reexec_result = asyncio.run(_run_browser_workflow_executor(
                                        cwd, config, reg_wf, bw_workflows_dir, app_url,
                                        task_text=effective_task, constraints=constraints,
                                        intervention=intervention, depth=depth,
                                    ))
                                    browser_cost += reexec_cost
                                    workflow_results[reg_id] = reexec_result
                                    # Update report entry
                                    for i, wr in enumerate(browser_report.workflow_results):
                                        if wr.workflow_id == reg_id:
                                            browser_report.workflow_results[i] = reexec_result
                                            break
                                    if reexec_result.health != "passed":
                                        all_regressions_fixed = False
                                        print_warning(f"Regression fix for workflow {reg_id} did not resolve the issue")
                        browser_report.regression_sweep_passed = all_regressions_fixed
                    else:
                        browser_report.regression_sweep_passed = True
                        print_info("Regression sweep passed — no regressions detected")

                # Step 5: Aggregate health
                if browser_report.passed_workflows == browser_report.total_workflows:
                    browser_report.health = "passed"
                elif browser_report.passed_workflows > 0:
                    browser_report.health = "partial"
                    if browser_report.failed_workflows > 0:
                        recovery_types.append("browser_testing_partial")
                elif browser_report.skipped_workflows == browser_report.total_workflows:
                    browser_report.health = "failed"
                else:
                    browser_report.health = "failed"

                browser_report.total_screenshots = count_screenshots(bw_screenshots_dir)

                # Step 6: Generate reports
                readiness_content = generate_readiness_report(bw_workflows_dir, browser_report, workflow_defs)
                print_info(f"Browser readiness report generated ({len(readiness_content)} chars)")

                failed_results = [wr for wr in browser_report.workflow_results if wr.health == "failed"]
                if failed_results:
                    generate_unresolved_issues(bw_workflows_dir, failed_results)

                if _current_state and browser_report.health in ("passed", "partial"):
                    _current_state.completed_phases.append("browser_testing")
                    _current_state.artifacts["browser_readiness_report"] = str(
                        browser_base / "BROWSER_READINESS_REPORT.md"
                    )

                print_info(
                    f"Browser Testing Phase complete — "
                    f"Health: {browser_report.health.upper()} | "
                    f"Passed: {browser_report.passed_workflows}/{browser_report.total_workflows} | "
                    f"Fix cycles: {browser_report.total_fix_cycles} | "
                    f"Screenshots: {browser_report.total_screenshots} | "
                    f"Cost: ${browser_cost:.2f}"
                )

        except RuntimeError:
            pass  # Already handled (skip scenarios raise RuntimeError)
        except Exception as exc:
            print_warning(f"Browser testing phase failed: {exc}\n{traceback.format_exc()}")
            browser_report.health = "failed"
            browser_report.skip_reason = f"Phase error: {exc}"
        finally:
            # Stop app process if startup agent started one
            if _browser_app_started and _browser_app_port:
                try:
                    import subprocess as _cleanup_subprocess
                    import sys as _cleanup_sys
                    if _cleanup_sys.platform == "win32":
                        _cleanup_subprocess.run(
                            ["taskkill", "/F", "/FI", f"IMAGENAME eq node.exe", "/FI", f"WINDOWTITLE eq *:{_browser_app_port}*"],
                            capture_output=True, timeout=10,
                        )
                        # Also try netstat-based kill via port
                        _cleanup_subprocess.run(
                            f'for /f "tokens=5" %p in (\'netstat -ano ^| findstr :{_browser_app_port} ^| findstr LISTENING\') do taskkill /F /PID %p',
                            shell=True, capture_output=True, timeout=10,
                        )
                    else:
                        _cleanup_subprocess.run(
                            ["fuser", "-k", f"{_browser_app_port}/tcp"],
                            capture_output=True, timeout=10,
                        )
                    print_info(f"Stopped app process on port {_browser_app_port}")
                except Exception:
                    pass  # Best-effort cleanup

    # Display recovery report if any recovery passes were triggered
    if recovery_types:
        print_recovery_report(len(recovery_types), recovery_types)

    if _current_state:
        _current_state.completed_phases.append("post_orchestration")
        _current_state.current_phase = "verification"

        # Persist tracking document artifact paths in state
        try:
            _req_dir = Path(cwd) / config.convergence.requirements_dir
            fix_log_path = _req_dir / "FIX_CYCLE_LOG.md"
            if fix_log_path.is_file():
                _current_state.artifacts["fix_cycle_log"] = str(fix_log_path)
            matrix_path = _req_dir / "E2E_COVERAGE_MATRIX.md"
            if matrix_path.is_file():
                _current_state.artifacts["e2e_coverage_matrix"] = str(matrix_path)
            handoff_path = _req_dir / "MILESTONE_HANDOFF.md"
            if handoff_path.is_file():
                _current_state.artifacts["milestone_handoff"] = str(handoff_path)
        except Exception:
            pass  # Best-effort artifact tracking

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
