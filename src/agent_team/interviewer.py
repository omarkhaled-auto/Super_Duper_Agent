"""Interviewer phase — a separate multi-turn conversation that produces a structured brief.

The interviewer runs as a standalone ClaudeSDKClient session BEFORE the
orchestrator.  It talks directly to the user, explores the codebase if
relevant, and writes `.agent-team/INTERVIEW.md` (a Task Brief, Feature Brief,
or full PRD depending on detected scope).

The interview ends ONLY when the user says so.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

logger = logging.getLogger(__name__)

from .config import AgentTeamConfig
from .display import (
    console,
    print_agent_response,
    print_info,
    print_interview_end,
    print_interview_prompt,
    print_interview_start,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXIT_PHRASES: list[str] = [
    "i'm done",
    "im done",
    "i am done",
    "let's go",
    "lets go",
    "start building",
    "start coding",
    "proceed",
    "build it",
    "go ahead",
    "that's it",
    "thats it",
    "that's all",
    "thats all",
    "begin",
    "execute",
    "run it",
    "ship it",
    "do it",
    "let's start",
    "lets start",
    "good to go",
    "ready",
    "looks good",
    "lgtm",
]

INTERVIEWER_SYSTEM_PROMPT = r"""You are a SENIOR TECHNICAL PM / REQUIREMENTS ANALYST acting as the interviewer for the Agent Team system.

Your purpose is to have a focused, productive conversation with the user to understand EXACTLY what they want built, then produce a structured document that will feed into the multi-agent orchestrator.

============================================================
CORE RULES
============================================================

1. **YOU NEVER END THE CONVERSATION.** Only the user can end it. When the user says phrases like "I'm done", "let's go", "start building", "proceed", etc. — that is your signal to finalize the document and stop.

2. **BE CONCISE.** Ask 1-3 focused questions at a time, not 10. Listen to answers before asking more.

3. **ADAPT TO SCOPE.** A one-line bug fix needs 2-3 questions. A full SaaS app needs 15-20. Match your depth to the task.

4. **EXPLORE THE CODEBASE** when the user mentions an existing project. Use Read, Glob, and Grep to ask informed questions based on actual code, not assumptions.

5. **INCREMENTALLY SAVE** the document to `.agent-team/INTERVIEW.md` every 3-4 exchanges. This way nothing is lost if the session is interrupted.

============================================================
OPENING MESSAGE
============================================================

If you receive an initial task seed, acknowledge it and ask clarifying questions:
- "You want to [task]. Let me ask a few questions to make sure the agents build exactly what you need."
- Then ask 1-2 targeted questions based on the task.

If no initial task is provided:
- "What would you like to build or work on? Give me as much or as little detail as you'd like, and I'll ask follow-up questions."

============================================================
QUESTION FRAMEWORK (adapt to detected scope)
============================================================

### ALL tasks (SIMPLE / MEDIUM / COMPLEX):
1. **Core objective** — What exactly should be done? What is the end result?
2. **Scope & boundaries** — What's IN scope and what's explicitly OUT of scope?
3. **Technical context** — What tech stack, framework, or language? Existing project or greenfield?

### MEDIUM and COMPLEX tasks (add these):
4. **User stories** — Who uses this? What do they do? What do they expect?
5. **Functional requirements** — Specific features, behaviors, inputs/outputs
6. **Error handling** — What happens when things go wrong?
7. **UI/UX** — Any design requirements, wireframes, or interaction patterns?
8. **Design reference** — Is there a website or app whose design you'd like as inspiration?
   (e.g., "I like how stripe.com looks"). Only ask this if the task involves frontend/UI work.
   If the user provides a URL, note it prominently in the document under a "Design Reference" heading.

### COMPLEX tasks only (add these):
9. **Target users** — Who are the users? What are their needs?
10. **Data model** — What data entities exist? How do they relate?
11. **API design** — What endpoints are needed? What do they accept/return?
12. **Integrations** — What external services, APIs, or systems are involved?
13. **Non-functional requirements** — Performance, scalability, accessibility, security
14. **Deployment** — How will this be deployed? What infrastructure?
15. **Milestones** — Can this be broken into phases or milestones?

============================================================
SCOPE DETECTION
============================================================

Detect scope from conversation signals:

**SIMPLE** (Task Brief):
- Bug fix, typo, one-file change, simple feature
- User describes task in 1-2 sentences
- Involves 1-5 files
- Document: ~20-40 lines

**MEDIUM** (Feature Brief):
- Multi-file feature, new component, API endpoint, integration
- User needs to explain behavior, edge cases
- Involves 5-20 files
- Document: ~40-80 lines

**COMPLEX** (Full PRD):
- Full application, major system, multi-service architecture
- Multiple user types, complex data models, integrations
- Involves 20+ files or a new project
- Document: ~80-200+ lines

============================================================
DOCUMENT FORMATS
============================================================

### SIMPLE — Task Brief
```markdown
# Task Brief: <Title>
Scope: SIMPLE
Date: <timestamp>

## Objective
<1-2 sentences describing what needs to be done>

## Context
<Technical context — stack, files involved, current behavior>

## Requirements
- <Specific requirement 1>
- <Specific requirement 2>
- ...

## Out of Scope
- <What NOT to do>

## Acceptance Criteria
- <How to verify it's done>
```

### MEDIUM — Feature Brief
```markdown
# Feature Brief: <Title>
Scope: MEDIUM
Date: <timestamp>

## Objective
<2-4 sentences describing the feature>

## Context
<Technical context — stack, architecture, existing patterns>

## User Stories
- As a <user>, I want to <action> so that <benefit>
- ...

## Functional Requirements
- FR-1: <Description>
- FR-2: <Description>
- ...

## Technical Requirements
- TR-1: <Description>
- ...

## Error Handling
- <Error scenario 1>: <Expected behavior>
- ...

## UI/UX Notes
<Any design or interaction requirements>

## Design Reference
<Reference website URL(s) and what aspects to draw inspiration from. Omit if none provided.>

## Out of Scope
- <What NOT to do>

## Acceptance Criteria
- <How to verify each requirement>
```

### COMPLEX — Product Requirements Document (PRD)
```markdown
# PRD: <Title>
Scope: COMPLEX
Date: <timestamp>

## Executive Summary
<High-level overview of what's being built and why>

## Target Users
- <User type 1>: <Description and needs>
- ...

## User Stories
- As a <user>, I want to <action> so that <benefit>
- ...

## Functional Requirements

### Feature Group 1: <Name>
- FR-1: <Description>
- FR-2: <Description>

### Feature Group 2: <Name>
- FR-3: <Description>
- ...

## Technical Requirements
- TR-1: <Description>
- ...

## Data Model
<Entity descriptions and relationships>

## API Design
<Endpoint descriptions>

## Integrations
- <Service 1>: <How it's used>
- ...

## Non-Functional Requirements
- Performance: <Requirements>
- Security: <Requirements>
- Accessibility: <Requirements>

## Deployment
<Infrastructure and deployment requirements>

## Design Reference
<Reference website URL(s) and what aspects to draw inspiration from. Omit if none provided.>

## Milestones
1. <Milestone 1>: <Description and deliverables>
2. <Milestone 2>: <Description and deliverables>
- ...

## Out of Scope
- <What NOT to do>

## Open Questions
- <Anything still unclear>
```

============================================================
FINALIZATION
============================================================

When the user signals they're done:
1. Write the FINAL version of `.agent-team/INTERVIEW.md`
2. Include all gathered information organized into the appropriate format
3. Make sure the `Scope:` header is present (SIMPLE, MEDIUM, or COMPLEX)
4. Your last message should summarize what was captured and confirm the document is saved

============================================================
CODEBASE EXPLORATION
============================================================

When the user mentions an existing project or codebase:
- Use Glob to find project structure (package.json, pyproject.toml, etc.)
- Use Read to examine key files
- Use Grep to find relevant patterns, functions, or classes
- Reference specific files and patterns in your questions
- This makes you a MUCH more effective interviewer — you ask about real code, not hypotheticals

============================================================
ANTI-PATTERNS (DO NOT DO THESE)
============================================================

- Do NOT ask 10 questions at once — ask 1-3
- Do NOT assume scope — detect it from conversation
- Do NOT write the document after every exchange — every 3-4 exchanges
- Do NOT end the conversation — only the user can
- Do NOT skip codebase exploration when an existing project is mentioned
- Do NOT produce vague requirements — be specific and testable
- Do NOT pad the document — shorter is better if the task is simple
""".strip()


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class InterviewResult:
    """Result returned after an interview session completes."""

    doc_content: str
    doc_path: str
    scope: str  # "SIMPLE", "MEDIUM", or "COMPLEX"
    exchange_count: int
    cost: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXIT_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in EXIT_PHRASES) + r")\b",
    re.IGNORECASE,
)

_NEGATION_WORDS = {"not", "no", "don't", "dont", "won't", "wont", "can't", "cant", "never", "isn't", "isnt"}


def _is_interview_exit(user_input: str) -> bool:
    """Check if the user's input matches an exit phrase.

    Uses word boundaries to prevent false positives and rejects matches
    that are preceded by a negation word (e.g. "I'm not done" should NOT
    trigger an exit).
    """
    normalized = user_input.strip().lower().rstrip(".!,?;:")
    if not normalized:
        return False
    # Exact match against known phrases (no negation possible)
    if normalized in EXIT_PHRASES:
        return True
    # Regex search with word boundaries for phrases in longer text
    match = _EXIT_RE.search(normalized)
    if not match:
        return False
    # Negation guard: check if a negation word appears within 3 words
    # before the matched exit phrase
    prefix = normalized[: match.start()].split()
    window = prefix[-3:] if len(prefix) >= 3 else prefix
    if any(w in _NEGATION_WORDS for w in window):
        return False
    return True


_SCOPE_RE = re.compile(
    r"(?:^|[\s#>])\*{0,2}\bscope\b\*{0,2}\s*:\s*\*{0,2}\s*(\w+)",
    re.IGNORECASE,
)


def _detect_scope(doc_content: str) -> str:
    """Detect scope from the Scope: header in the interview document.

    Supports plain ``Scope: VALUE`` and markdown-formatted headers like
    ``**Scope:** COMPLEX``.  Matching is case-insensitive.
    """
    for line in doc_content.splitlines():
        match = _SCOPE_RE.search(line)
        if match:
            value = match.group(1).strip().upper()
            if value in ("SIMPLE", "MEDIUM", "COMPLEX"):
                return value
    logger.warning("Scope header not found in interview document; defaulting to MEDIUM")
    return "MEDIUM"


def _build_interview_options(
    config: AgentTeamConfig,
    cwd: str | None = None,
) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions for the interviewer session."""
    opts_kwargs: dict[str, Any] = {
        "model": config.interview.model,
        "system_prompt": INTERVIEWER_SYSTEM_PROMPT,
        "permission_mode": "acceptEdits",
        "max_turns": config.interview.max_exchanges * 4,
        "allowed_tools": [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        ],
    }

    if cwd:
        opts_kwargs["cwd"] = Path(cwd)

    return ClaudeAgentOptions(**opts_kwargs)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_interview(
    config: AgentTeamConfig,
    cwd: str | None = None,
    initial_task: str | None = None,
) -> InterviewResult:
    """Run the interactive interview session.

    Opens a ClaudeSDKClient, has a multi-turn conversation with the user,
    and produces `.agent-team/INTERVIEW.md`.  Returns an InterviewResult
    with the document content and metadata.
    """
    print_interview_start(initial_task)

    options = _build_interview_options(config, cwd)
    exchange_count = 0
    total_cost = 0.0
    transcript: list[dict[str, str]] = []  # backup transcript

    # Determine the doc path and ensure directory exists
    project_dir = Path(cwd) if cwd else Path.cwd()
    doc_dir = project_dir / ".agent-team"
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc_path = doc_dir / "INTERVIEW.md"

    # Build the opening message for the interviewer
    if initial_task:
        opening = (
            f"The user wants to work on the following task:\n\n"
            f'"{initial_task}"\n\n'
            f"The project directory is: {project_dir}\n\n"
            f"Start by acknowledging their task, exploring the codebase if "
            f"relevant, and asking 1-2 targeted clarifying questions. "
            f"Remember to save the interview document to "
            f"{doc_path} incrementally."
        )
    else:
        opening = (
            f"The user has started an interview session without specifying a task.\n\n"
            f"The project directory is: {project_dir}\n\n"
            f"Ask them what they'd like to build or work on. "
            f"Remember to save the interview document to "
            f"{doc_path} incrementally."
        )

    try:
        async with ClaudeSDKClient(options=options) as client:
            # Send the opening instruction (internal — user doesn't see this)
            await client.query(opening)

            # Process the interviewer's first response
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print_agent_response(block.text)
                        elif isinstance(block, ToolUseBlock):
                            if config.display.verbose:
                                print_info(f"[tool] {block.name}")
                elif isinstance(msg, ResultMessage):
                    if msg.total_cost_usd:
                        total_cost += msg.total_cost_usd

            # Multi-turn conversation loop
            empty_count = 0  # track consecutive empty inputs (C1 fix)
            while exchange_count < config.interview.max_exchanges:
                user_input = print_interview_prompt()
                if not user_input:
                    empty_count += 1
                    if empty_count >= 3:
                        print_info(
                            "Three consecutive empty inputs detected — "
                            "ending interview (possible non-interactive stdin)."
                        )
                        break
                    continue
                empty_count = 0  # reset on real input

                exchange_count += 1

                if _is_interview_exit(user_input):
                    transcript.append({"role": "user", "content": user_input, "action": "exit"})
                    # Send the finalization instruction
                    finalize_msg = (
                        f"The user has indicated they are done with the interview "
                        f'(they said: "{user_input}").\n\n'
                        f"Write the FINAL version of the interview document to "
                        f"{doc_path}. Make sure the Scope: header is present "
                        f"(SIMPLE, MEDIUM, or COMPLEX). Summarize what was captured "
                        f"and confirm the document is saved."
                    )
                    await client.query(finalize_msg)
                    assistant_text = ""
                    async for msg in client.receive_response():
                        if isinstance(msg, AssistantMessage):
                            for block in msg.content:
                                if isinstance(block, TextBlock):
                                    print_agent_response(block.text)
                                    assistant_text += block.text + "\n"
                                elif isinstance(block, ToolUseBlock):
                                    if config.display.verbose:
                                        print_info(f"[tool] {block.name}")
                        elif isinstance(msg, ResultMessage):
                            if msg.total_cost_usd:
                                total_cost += msg.total_cost_usd
                    if assistant_text:
                        transcript.append({"role": "assistant", "content": assistant_text.strip()})
                    break

                # Normal exchange — relay the user's message to the interviewer
                transcript.append({"role": "user", "content": user_input})
                await client.query(user_input)
                assistant_text = ""
                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                print_agent_response(block.text)
                                assistant_text += block.text + "\n"
                            elif isinstance(block, ToolUseBlock):
                                if config.display.verbose:
                                    print_info(f"[tool] {block.name}")
                    elif isinstance(msg, ResultMessage):
                        if msg.total_cost_usd:
                            total_cost += msg.total_cost_usd
                if assistant_text:
                    transcript.append({"role": "assistant", "content": assistant_text.strip()})
            else:
                # max_exchanges reached — force finalization
                print_info(
                    f"Maximum exchange limit ({config.interview.max_exchanges}) "
                    f"reached. Finalizing interview document..."
                )
                finalize_msg = (
                    f"The interview has reached the maximum exchange limit. "
                    f"Write the FINAL version of the interview document to "
                    f"{doc_path} with all information gathered so far. "
                    f"Make sure the Scope: header is present "
                    f"(SIMPLE, MEDIUM, or COMPLEX)."
                )
                await client.query(finalize_msg)
                assistant_text = ""
                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                print_agent_response(block.text)
                                assistant_text += block.text + "\n"
                            elif isinstance(block, ToolUseBlock):
                                if config.display.verbose:
                                    print_info(f"[tool] {block.name}")
                    elif isinstance(msg, ResultMessage):
                        if msg.total_cost_usd:
                            total_cost += msg.total_cost_usd
                if assistant_text:
                    transcript.append({"role": "assistant", "content": assistant_text.strip(), "action": "max_exchanges_finalization"})

    except KeyboardInterrupt:
        print_info("Interview interrupted by user.")
    except Exception as exc:
        print_info(f"Interview session error: {exc}")
        if doc_path.is_file():
            print_info(f"Partial interview document may exist at {doc_path}")

    # Write transcript backup BEFORE relying on Claude's file write (I3 fix)
    if transcript:
        backup_path = doc_dir / "INTERVIEW_BACKUP.json"
        try:
            backup_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "exchange_count": exchange_count,
                "exchanges": transcript,
            }
            backup_path.write_text(
                json.dumps(backup_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print_info(f"Transcript backup saved to {backup_path}")
        except Exception as exc:
            logger.warning("Failed to write transcript backup: %s", exc)

    # Read the final document from disk
    doc_content = ""
    if doc_path.is_file():
        doc_content = doc_path.read_text(encoding="utf-8")
    else:
        print_info(
            f"Warning: Interview document not found at {doc_path}. "
            f"The interviewer may not have saved the document."
        )

    scope = _detect_scope(doc_content) if doc_content else "MEDIUM"

    print_interview_end(exchange_count, scope, str(doc_path))

    return InterviewResult(
        doc_content=doc_content,
        doc_path=str(doc_path),
        scope=scope,
        exchange_count=exchange_count,
        cost=total_cost,
    )
