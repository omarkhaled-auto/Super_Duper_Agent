"""Sequential Thinking decision-point templates for the orchestrator.

Provides structured reasoning prompts at 4 strategic points in the
orchestration pipeline, depth-gated so simple tasks get zero overhead.

Design principle: "ST advises, gates enforce."  The orchestrator feeds
context into the ST MCP tool at decision points; the tool's output is a
RECOMMENDATION.  Convergence gates (Section 3) remain hard constraints.

This module follows the ``sequential_thinking.py`` pattern: string
templates assembled by a builder function based on config.
"""
from __future__ import annotations

from .config import OrchestratorSTConfig, get_active_st_points


# ---------------------------------------------------------------------------
# Template strings — one per decision point
# ---------------------------------------------------------------------------

_PRE_RUN_STRATEGY = r"""You are reasoning about strategy for a multi-agent coding task BEFORE execution begins.

Context:
- Task summary: {task_summary}
- Codebase summary: {codebase_summary}
- Depth level: {depth}
- Requirement count (estimated): {requirement_count}

Analyze:
1. Task complexity — is the depth level appropriate?
2. Likely failure points — what could go wrong in implementation or review?
3. Phase emphasis — which phases need more agents than the default scaling?
4. Fleet sizing adjustments — should any phase get more or fewer agents?
5. Risk predictions — top 3 risks for this specific task.

Output format — your FINAL thought MUST contain a structured decision:
STRATEGY DECISION:
(1) Phase adjustments: <list any phases that should deviate from default agent counts>
(2) Fleet sizing notes: <specific sizing recommendations>
(3) Top 3 risk predictions: <risk, mitigation>

Hard constraints:
- You CANNOT skip any phase. You can only adjust emphasis and sizing.
- You CANNOT change the convergence gate rules.
- You CANNOT bypass the review fleet.

Budget: {max_thoughts} thoughts."""

_ARCHITECTURE_CHECKPOINT = r"""You are verifying alignment between requirements, architecture, and constraints BEFORE task decomposition.

Context:
- Requirements summary: {requirements_summary}
- Architecture summary: {architecture_summary}
- Wiring map entries: {wiring_map}
- User constraints: {constraints}

Analyze:
1. Requirement-architecture alignment — does the architecture cover every requirement?
2. Dependency conflicts — are there circular or infeasible dependencies?
3. Wiring coverage — does every feature have a WIRE-xxx entry connecting it?
4. Shared-state contention — will multiple agents need to edit the same files?
5. Constraint compliance — does the architecture violate any user constraints?

Output format — your FINAL thought MUST contain:
CHECKPOINT DECISION: PROCEED | REVISE
If REVISE: list specific issues that must be addressed before task decomposition.

Hard constraints:
- You CANNOT approve an architecture that leaves WIRE-xxx items unaddressed.
- You CANNOT approve an architecture that violates user constraints.
- If in doubt, REVISE.

Budget: {max_thoughts} thoughts."""

_CONVERGENCE_REASONING = r"""You are analyzing WHY the convergence loop has not completed after cycle {cycle_number}.

Context:
- Failing items: {failing_items}
- Review log summary: {review_log_summary}
- Previous fixes attempted: {previous_fixes_attempted}
- Cycle history: {cycle_history}

Analyze:
1. Pattern of failures — are the same items failing repeatedly? Different ones?
2. Root cause hypothesis — is the issue at decomposition, design, or implementation level?
3. Fix effectiveness — did previous debug attempts address root causes or just symptoms?
4. Escalation candidates — which items have exceeded the escalation threshold?
5. Merge opportunities — can failing items be combined into a single richer task?

Output format — your FINAL thought MUST contain exactly ONE of these decisions:
CONVERGENCE DECISION: DEBUG(items) | ESCALATE(items, reason) | REPLAN(items, new_approach) | MERGE(task_ids, reason)

- DEBUG(items): normal debug cycle for the listed items.
- ESCALATE(items, reason): send items back to planning+research for re-analysis.
- REPLAN(items, new_approach): rewrite the requirement/task with a new approach.
- MERGE(task_ids, reason): combine related failing tasks into one cohesive task.

Hard constraints:
- You CANNOT skip re-review after any fix.
- You CANNOT mark items [x] — only the review fleet does that.
- You CANNOT reduce requirements to make them pass.

Budget: {max_thoughts} thoughts."""

_COMPLETION_VERIFICATION = r"""You are verifying the system is TRULY complete before declaring done.

Context:
- Requirements status: {requirements_status}
- Cycle history: {cycle_history}
- Dependency graph: {dependency_graph}

Analyze:
1. Stale reviews — was any item marked [x] before a dependent item was rewritten?
   If item B depends on item A, and A was rewritten after B was marked [x],
   then B's review is stale and must be re-verified.
2. Dependency chain coherence — does the implementation respect the dependency order?
3. Integration completeness — are all WIRE-xxx items verified?
4. Test coverage — were tests written and passing for all functional requirements?
5. Cross-concern consistency — do related requirements produce a coherent whole?

Output format — your FINAL thought MUST contain:
COMPLETION DECISION: DONE | RE_REVIEW(items, reason)

Hard constraints:
- When in doubt, RE_REVIEW. False completion is worse than an extra review cycle.
- You CANNOT declare DONE if any item is still [ ] in REQUIREMENTS.md.

Budget: {max_thoughts} thoughts."""


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

_TEMPLATES: dict[int, tuple[str, str]] = {
    1: ("Pre-Run Strategy", _PRE_RUN_STRATEGY),
    2: ("Architecture Checkpoint", _ARCHITECTURE_CHECKPOINT),
    3: ("Convergence Reasoning", _CONVERGENCE_REASONING),
    4: ("Completion Verification", _COMPLETION_VERIFICATION),
}

_TRIGGER_DESCRIPTIONS: dict[int, str] = {
    1: "deploying the PLANNING FLEET (between step 0 and step 1 of Section 7)",
    2: "deploying the TASK ASSIGNER (between step 3.5 and step 4 of Section 7)",
    3: "deciding debug vs escalate in the convergence loop (step 3 of Section 3)",
    4: "declaring COMPLETION (step 8 of Section 7)",
}

_WHEN_CONDITIONS: dict[int, str] = {
    1: "Immediately after reading the task and interview document, before depth detection.",
    2: "After the architecture fleet completes and before the task-assigner is deployed.",
    3: "When the convergence loop fails a cycle (not all items [x]) and you need to decide what to do next.",
    4: "When all items appear to be [x] and you are about to declare the task complete.",
}


# ---------------------------------------------------------------------------
# Template formatter functions
# ---------------------------------------------------------------------------

def format_pre_run_strategy(context: dict, config: OrchestratorSTConfig) -> str:
    """Format the pre-run strategy template with context."""
    return _PRE_RUN_STRATEGY.format(
        task_summary=context.get("task_summary", "<not available>"),
        codebase_summary=context.get("codebase_summary", "<not available>"),
        depth=context.get("depth", "<not available>"),
        requirement_count=context.get("requirement_count", "<unknown>"),
        max_thoughts=config.thought_budgets.get(1, 8),
    )


def format_architecture_checkpoint(context: dict, config: OrchestratorSTConfig) -> str:
    """Format the architecture checkpoint template with context."""
    return _ARCHITECTURE_CHECKPOINT.format(
        requirements_summary=context.get("requirements_summary", "<not available>"),
        architecture_summary=context.get("architecture_summary", "<not available>"),
        wiring_map=context.get("wiring_map", "<not available>"),
        constraints=context.get("constraints", "<none>"),
        max_thoughts=config.thought_budgets.get(2, 10),
    )


def format_convergence_reasoning(context: dict, config: OrchestratorSTConfig) -> str:
    """Format the convergence reasoning template with context."""
    return _CONVERGENCE_REASONING.format(
        cycle_number=context.get("cycle_number", "<unknown>"),
        failing_items=context.get("failing_items", "<not available>"),
        review_log_summary=context.get("review_log_summary", "<not available>"),
        previous_fixes_attempted=context.get("previous_fixes_attempted", "<none>"),
        cycle_history=context.get("cycle_history", "<not available>"),
        max_thoughts=config.thought_budgets.get(3, 12),
    )


def format_completion_verification(context: dict, config: OrchestratorSTConfig) -> str:
    """Format the completion verification template with context."""
    return _COMPLETION_VERIFICATION.format(
        requirements_status=context.get("requirements_status", "<not available>"),
        cycle_history=context.get("cycle_history", "<not available>"),
        dependency_graph=context.get("dependency_graph", "<not available>"),
        max_thoughts=config.thought_budgets.get(4, 8),
    )


# ---------------------------------------------------------------------------
# Builder function
# ---------------------------------------------------------------------------

def build_orchestrator_st_instructions(
    depth: str,
    config: OrchestratorSTConfig,
) -> str:
    """Build the ST instruction block for the orchestrator system prompt.

    Returns the full Section 9 text if any ST points are active,
    or empty string if ST is disabled / no points active for this depth.
    """
    active_points = get_active_st_points(depth, config)
    if not active_points:
        return ""

    parts: list[str] = []

    parts.append("""
============================================================
SECTION 9: STRATEGIC REASONING (Sequential Thinking)
============================================================

You have access to the Sequential Thinking MCP tool (mcp__sequential-thinking__sequentialthinking).
Use it at specific decision points to REASON DELIBERATELY before acting.

PRINCIPLE: "ST advises, gates enforce." Your ST reasoning produces RECOMMENDATIONS.
The convergence gates (Section 3) remain HARD CONSTRAINTS. ST cannot bypass gates,
skip phases, or override rules. ST helps you make BETTER decisions within the pipeline.

HOW TO USE THE ST TOOL:
Call mcp__sequential-thinking__sequentialthinking with these parameters:
  - thought: your reasoning text for this step
  - totalThoughts: the budget for this decision point
  - thoughtNumber: start at 1, increment each call
  - nextThoughtNeeded: true (until your final thought, then false)

Complete ALL thought steps before acting on the decision. Do NOT deploy agents
while ST is reasoning. Finish reasoning first, extract the DECISION, then act.""")

    points_list = ", ".join(str(p) for p in active_points)
    parts.append(f"\nACTIVE DECISION POINTS FOR THIS RUN: [{points_list}]")

    for point in sorted(active_points):
        if point not in _TEMPLATES:
            continue
        name, template = _TEMPLATES[point]
        trigger = _TRIGGER_DESCRIPTIONS[point]
        when = _WHEN_CONDITIONS[point]
        budget = config.thought_budgets.get(point, 8)

        parts.append(f"""
------------------------------------------------------------
### ST POINT {point}: {name} — Use BEFORE {trigger}
------------------------------------------------------------
When: {when}
Budget: {budget} thoughts

How: Call mcp__sequential-thinking__sequentialthinking repeatedly:
  - thoughtNumber: 1 through {budget} (or fewer if you reach a decision early)
  - totalThoughts: {budget}
  - nextThoughtNeeded: true until your final thought

Template for your thought content:
{template}

After ST completes, extract the DECISION line from your final thought and act on it.
Do NOT deploy agents while ST is reasoning. Complete reasoning first, then act.""".rstrip())

    return "\n".join(parts)
