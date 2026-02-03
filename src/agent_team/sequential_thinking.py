"""Prompt-engineered Sequential Thinking methodology for review agents.

Embeds numbered thought steps, hypothesis-verification loops, revision markers,
and confidence checkpoints directly into agent prompts. This composes with the
existing investigation protocol — investigation defines the 4-phase WHAT,
sequential thinking defines the HOW (structured thought discipline).

This module follows the investigation_protocol.py pattern: string templates
assembled by a builder function based on config.
"""
from __future__ import annotations

from .config import InvestigationConfig


# ---------------------------------------------------------------------------
# Core methodology (all ST-capable agents)
# ---------------------------------------------------------------------------

_ST_METHODOLOGY_BASE = r"""
============================================================
SEQUENTIAL THINKING METHODOLOGY
============================================================

This methodology provides the STRUCTURED STEP FORMAT for Phase 2 (INVESTIGATE)
of the Investigation Protocol above. Use the Investigation Protocol phases as
your high-level flow (SCOPE → INVESTIGATE → SYNTHESIZE → EVIDENCE), and use the
numbered thought format below for each step within Phase 2.

Before investigating ANY item, estimate the number of thought steps needed.
Use the complexity of the item as your guide:
- Simple single-file check: 3-5 thoughts
- Multi-file trace: 6-10 thoughts
- Complex cross-system investigation: 10-{max_thoughts} thoughts
Cap at {max_thoughts} thoughts per item. Adjust as complexity becomes clearer.

### Numbered Thought Format

Every Phase 2 investigation step MUST follow this format:

THOUGHT [N/{total}]: {target}
  Tool: {Read|Grep|Glob|Gemini}
  Finding: {what you found — file:line reference}
  Implication: {what this means}
  Next: {what you will investigate next}

Rules:
- ONE finding per thought. No vague "looking at code now..." steps.
- Every thought must ADVANCE your understanding — state a concrete finding.
- file:line references are REQUIRED for any code finding.
- You may adjust {total} up or down as complexity becomes clearer.
- Numbering restarts for each new review item.
""".strip()


# ---------------------------------------------------------------------------
# Hypothesis-verification cycle
# ---------------------------------------------------------------------------

_ST_HYPOTHESIS_LOOP = r"""

### Hypothesis-Verification Cycle

After every 3-4 thoughts, you MUST form a hypothesis and test it.

HYPOTHESIS [H-N]: {claim}
  Evidence FOR: {supporting findings with file:line refs}
  Evidence AGAINST: {contradicting findings, or "none found"}
  Test plan: {what would confirm or refute this}

After testing:

VERDICT: CONFIRMED | REFUTED | INCONCLUSIVE
  Basis: {specific evidence that led to this verdict}

If REFUTED: revise your understanding and form a new hypothesis.
If INCONCLUSIVE: gather more evidence (add thoughts).
Do NOT conclude an investigation without at least one CONFIRMED hypothesis.
""".strip()


# ---------------------------------------------------------------------------
# Revision and confidence support
# ---------------------------------------------------------------------------

_ST_REVISION_SUPPORT = r"""

### Revision and Confidence

If new evidence contradicts an earlier thought, use an explicit revision:

REVISION [revising Thought N]:
  Original: {what you previously concluded}
  New evidence: {what changed your mind — file:line ref}
  Revised: {your updated conclusion}

Confidence checkpoints (use at synthesis / before concluding):

- HIGH: 3+ independent pieces of evidence converge on the same conclusion.
  You may conclude.
- MEDIUM: Evidence points in one direction but gaps remain.
  Note the gaps, then conclude with caveats.
- LOW: Contradictory evidence or insufficient data.
  Do NOT conclude — add more thoughts to resolve.
""".strip()


# ---------------------------------------------------------------------------
# Per-agent thought estimates and hypothesis patterns
# ---------------------------------------------------------------------------

_ST_AGENT_PROFILES: dict[str, str] = {
    "code-reviewer": r"""

### Thought Estimates: Code Review

Use these baselines (adjust per item complexity):
- REQ-xxx (requirement check): 5-8 thoughts
- TECH-xxx (technical quality): 4-6 thoughts
- WIRE-xxx (wiring/integration): 6-10 thoughts
- PERF-xxx (performance): 5-8 thoughts

Hypothesis patterns for code review:
- "This data flow preserves types at all boundaries" — trace and verify
- "This integration point is correctly wired end-to-end" — follow the chain
- "This error is handled at every failure point" — check all paths
""".strip(),

    "security-auditor": r"""

### Thought Estimates: Security Audit

Use these baselines (adjust per item complexity):
- Input validation paths: 8-12 thoughts
- Auth flow analysis: 8-10 thoughts
- Secrets/credential handling: 4-6 thoughts
- Injection vector tracing: 6-10 thoughts
- Trust boundary verification: 6-8 thoughts

Hypothesis patterns for security:
- "All user inputs are sanitized before reaching [sink]" — trace each path
- "Auth middleware covers all protected routes" — enumerate and verify
- "No secrets are hardcoded or logged" — search and confirm
""".strip(),

    "debugger": r"""

### Thought Estimates: Debugging

Use these baselines (adjust per item complexity):
- Single-file bug: 5-7 thoughts
- Multi-file bug: 8-12 thoughts
- Root cause analysis: 10-15 thoughts
- Race condition / timing: 12-18 thoughts

Hypothesis patterns for debugging:
- "The bug originates in [location] due to [cause]" — verify with evidence
- "The error propagates through [path]" — trace the chain
- "The fix at [location] resolves all instances" — search for siblings
""".strip(),
}


# ---------------------------------------------------------------------------
# Builder function
# ---------------------------------------------------------------------------

def build_sequential_thinking_protocol(
    agent_name: str,
    config: InvestigationConfig,
) -> str:
    """Build the Sequential Thinking protocol string for a given agent.

    Returns an empty string if ST is disabled or the agent is not in the
    investigation agents list.

    Args:
        agent_name: The hyphenated agent name (e.g., "code-reviewer").
        config: The InvestigationConfig from the user's config.

    Returns:
        The ST protocol string to append to the agent's prompt, or empty string.
    """
    if not config.sequential_thinking:
        return ""

    if agent_name not in config.agents:
        return ""

    parts: list[str] = []

    # Core methodology with thought budget
    parts.append(
        _ST_METHODOLOGY_BASE.replace("{max_thoughts}", str(config.max_thoughts_per_item))
    )

    # Hypothesis-verification cycle (optional)
    if config.enable_hypothesis_loop:
        parts.append(_ST_HYPOTHESIS_LOOP)

    # Revision and confidence support (always included when ST is on)
    parts.append(_ST_REVISION_SUPPORT)

    # Per-agent thought estimates
    profile = _ST_AGENT_PROFILES.get(agent_name, "")
    if profile:
        parts.append(profile)

    return "\n\n" + "\n\n".join(parts)
