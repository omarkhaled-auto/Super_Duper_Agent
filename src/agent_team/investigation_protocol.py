"""Deep investigation protocol for review agents.

Equips code-reviewer, security-auditor, and debugger agents with a structured
investigation methodology inspired by Sequential Thinking + Gemini CLI workflows.
When Gemini CLI is available, agents can escalate from Read/Grep to cross-file
analysis using the gemini command via Bash.

This module follows the code_quality_standards.py pattern: string templates
assembled by a builder function based on config.
"""
from __future__ import annotations

from .config import InvestigationConfig


# ---------------------------------------------------------------------------
# Shared base protocol (all investigation-capable agents)
# ---------------------------------------------------------------------------

_BASE_PROTOCOL = r"""
============================================================
DEEP INVESTIGATION PROTOCOL
============================================================

When reviewing or debugging, follow this structured 4-phase methodology.
Use it for ANY item that requires cross-file analysis, data flow tracing,
or root cause investigation.

DYNAMIC ESCALATION RULE:
- Start with Read/Glob/Grep for simple checks (single-file, obvious logic).
- Escalate to the investigation protocol when:
  * The issue spans multiple files
  * You need to trace data flow or call chains
  * You need to find ALL instances of a pattern across the codebase
  * The root cause is not obvious from a single file
- You have a budget of {max_queries} Gemini queries (if available) -- use
  them on the items that genuinely need deep cross-file analysis.

### Phase 1: SCOPE
Define the question precisely before investigating.
- What SPECIFIC question are you answering?
- Which files/directories are in scope?
- What would a definitive answer look like?
- What are the success criteria?

### Phase 2: INVESTIGATE
Execute investigation steps dynamically -- use as many or as few as needed.
Each step must:
1. State the target (what you're looking for)
2. Execute the search (Read, Grep, Glob, or Gemini query)
3. Record the finding (file, line, what you found)
4. Draw a conclusion (what this means for your investigation)
5. Decide next step (continue, branch, or synthesize)

One finding per step. No vague "looking at code now..." steps.

### Phase 3: SYNTHESIZE
Connect your findings before concluding.
- How do the findings relate to each other?
- Are there contradictions? Gaps?
- What is the root cause / answer?
- What is your confidence level? (HIGH / MEDIUM / LOW)

### Phase 4: EVIDENCE
Conclude with specific evidence.
- State your conclusion clearly
- Reference specific files and line numbers (file:line format)
- If you found a bug: explain the root cause, not just the symptom
- If you verified correctness: explain the chain of evidence
""".strip()


# ---------------------------------------------------------------------------
# Gemini CLI section (injected when gemini_available=True)
# ---------------------------------------------------------------------------

_GEMINI_CLI_SECTION = r"""

### Gemini CLI — Cross-File Investigation Tool

You have access to Gemini CLI via Bash for deep, cross-file analysis.
Gemini can process an entire codebase (1M+ token context) in a single query,
making it ideal for:
- Tracing data flow across many files
- Finding ALL instances of a pattern
- Understanding full call chains
- Verifying wiring end-to-end

**Syntax:**
```
gemini{model_flag} "Your specific question here" --include-directories dir1,dir2
```

**Best practices:**
- Ask ONE specific question per query (not "analyze everything")
- Scope to relevant directories with --include-directories
- Ask for file:line references in the answer
- Frame questions as: "Trace where X is set/used/modified"
- Budget: You have {max_queries} queries max. Use 0-1 for simple items,
  3-5 for complex cross-file tracing.

**Good query examples:**
- `gemini "Trace where the user.role field is set during registration and where it is checked during authorization" --include-directories src/auth,src/middleware`
- `gemini "Find all places where the database connection is created or pooled, and verify they all use the same config" --include-directories src/db,src/config`
- `gemini "List every route handler that does NOT call requireAuth middleware" --include-directories src/routes`

**Bad query examples:**
- `gemini "Review all the code"` (too broad)
- `gemini "Is this good?"` (no specific question)
""".strip()


# ---------------------------------------------------------------------------
# Bash scoping for code-reviewer (MANDATORY when Gemini enabled)
# ---------------------------------------------------------------------------

_REVIEWER_BASH_SCOPING = r"""

### Bash Scoping Rules (MANDATORY)

You have been given Bash access EXCLUSIVELY for Gemini CLI queries.

ALLOWED:
- `gemini "..." --include-directories ...` commands only

PROHIBITED (will be treated as a review failure):
- Running tests (`npm test`, `pytest`, etc.)
- Running builds (`npm run build`, `tsc`, etc.)
- Modifying files (`echo`, `sed`, `mv`, `rm`, etc.)
- Installing packages (`npm install`, `pip install`, etc.)
- Any command that is NOT a `gemini` invocation

The orchestrator enforces this boundary. Stick to investigation only.
""".strip()


# ---------------------------------------------------------------------------
# Per-agent investigation focus
# ---------------------------------------------------------------------------

_AGENT_FOCUS: dict[str, str] = {
    "code-reviewer": r"""

### Investigation Focus: Code Review

Use the investigation protocol to:
- **Trace data flow**: Follow data from input to output across files.
  Verify types match at every boundary.
- **Verify wiring**: For WIRE-xxx items, trace the full connection path
  from entry point to feature. Don't just check the import exists --
  verify it's actually called/rendered/registered.
- **Find dead code**: Search for exports with zero importers, components
  never rendered, route handlers never registered.
- **Check error propagation**: Trace what happens when each operation fails.
  Does the error reach the user with a helpful message, or does it silently
  disappear?
- **Verify consistency**: Are similar patterns implemented consistently
  across the codebase? (e.g., all routes validate input, all services
  handle errors the same way)
""".strip(),

    "security-auditor": r"""

### Investigation Focus: Security Audit

Use the investigation protocol to:
- **Trace input paths**: Follow every user input from HTTP request to
  database query / file system / external API. Verify sanitization and
  validation at each step.
- **Map auth flows**: Trace authentication from login to session creation
  to middleware check to resource access. Find paths that skip auth.
- **Find injection vectors**: Search for ALL places where user input is
  concatenated into queries, commands, or templates.
- **Check trust boundaries**: At every WIRE-xxx integration point, verify
  that data crossing module boundaries is validated. Internal APIs should
  not blindly trust data from other modules.
- **Audit secrets handling**: Find all places where secrets (API keys,
  tokens, passwords) are used. Verify they come from environment/config,
  not hardcoded. Check they're not logged or exposed in errors.
""".strip(),

    "debugger": r"""

### Investigation Focus: Debugging

Use the investigation protocol to:
- **Trace variable assignments**: When a value is wrong, trace backwards
  through every assignment and transformation to find where it diverged.
- **Find all paths to error state**: Don't just find ONE cause -- find
  ALL code paths that could produce the observed error.
- **Root cause analysis**: The bug is rarely where the error appears.
  Trace the full call chain to find the ORIGIN of the problem.
- **Check recent changes**: Use git log / git diff to identify recent
  changes near the bug. The bug may be in a recent commit.
- **Verify fix completeness**: After identifying the root cause, search
  for ALL instances of the same pattern. If the bug exists in one place,
  it likely exists in similar code elsewhere.
""".strip(),
}


# ---------------------------------------------------------------------------
# Builder function
# ---------------------------------------------------------------------------

def build_investigation_protocol(
    agent_name: str,
    config: InvestigationConfig,
    gemini_available: bool = False,
) -> str:
    """Build the investigation protocol string for a given agent.

    Returns an empty string for agents not in config.agents list.
    Conditionally includes the Gemini CLI section and Bash scoping.

    Args:
        agent_name: The hyphenated agent name (e.g., "code-reviewer").
        config: The InvestigationConfig from the user's config.
        gemini_available: Whether Gemini CLI was detected on the system.

    Returns:
        The protocol string to append to the agent's prompt, or empty string.
    """
    if agent_name not in config.agents:
        return ""

    parts: list[str] = []

    # Base protocol with query budget
    parts.append(
        _BASE_PROTOCOL.replace("{max_queries}", str(config.max_queries_per_agent))
    )

    # Gemini CLI section (only when available)
    if gemini_available:
        model_flag = f" -m {config.gemini_model}" if config.gemini_model else ""
        parts.append(
            _GEMINI_CLI_SECTION
            .replace("{max_queries}", str(config.max_queries_per_agent))
            .replace("{model_flag}", model_flag)
        )

        # Bash scoping only for code-reviewer (other agents already have Bash)
        if agent_name == "code-reviewer":
            parts.append(_REVIEWER_BASH_SCOPING)

    # Per-agent investigation focus
    focus = _AGENT_FOCUS.get(agent_name, "")
    if focus:
        parts.append(focus)

    return "\n\n" + "\n\n".join(parts)
