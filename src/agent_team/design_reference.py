"""Phase 0.6: Guaranteed UI Requirements Document Generation.

Runs a focused Claude session with ONLY Firecrawl MCP tools to scrape
design reference URLs and produce a standalone UI_REQUIREMENTS.md file.
This phase runs between codebase map (0.5) and contract loading (0.75).
"""

from __future__ import annotations

import asyncio
import re
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

from .config import AgentTeamConfig


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class DesignExtractionError(Exception):
    """Raised when design reference extraction fails."""


# ---------------------------------------------------------------------------
# System prompt for the extraction session
# ---------------------------------------------------------------------------

DESIGN_EXTRACTION_SYSTEM_PROMPT = r"""You are a DESIGN REFERENCE ANALYZER. Your SOLE job is to scrape the provided URLs using Firecrawl MCP tools and produce a comprehensive UI_REQUIREMENTS.md document.

## TOOLS AVAILABLE
You have Firecrawl MCP tools: firecrawl_scrape, firecrawl_search, firecrawl_map, firecrawl_extract.
Use firecrawl_scrape on each URL to extract visual design information.

## OUTPUT REQUIREMENTS
You MUST write a file called `{ui_requirements_path}` with the following MANDATORY sections:

### Required Document Structure

```markdown
# UI Requirements — Design Reference Analysis
Generated from: <list of URLs>

## Color System
- Primary: <hex>
- Secondary: <hex>
- Accent: <hex>
- Background: <hex values for light/dark>
- Surface: <hex values>
- Text: <hex values for primary/secondary/muted text>
- Border: <hex>
- Error/Success/Warning/Info: <hex values>
- Gradient definitions (if any)

## Typography
- Font families (heading, body, mono)
- Font sizes (scale from xs to 4xl with px/rem values)
- Font weights used
- Line heights
- Letter spacing

## Spacing
- Base unit (e.g., 4px, 8px)
- Spacing scale (xs through 4xl with values)
- Container max-widths
- Section padding patterns
- Card/component internal padding

## Component Patterns
- Button styles (primary, secondary, ghost, outline — with border-radius, padding, states)
- Card patterns (shadow, border-radius, padding)
- Input field styles
- Navigation patterns (header, sidebar, mobile)
- Modal/dialog patterns
- Table/list patterns
- Badge/tag styles
- Avatar styles
- Toast/notification patterns

## Design Requirements Checklist
- [ ] DR-001: Color system tokens defined
- [ ] DR-002: Typography scale defined
- [ ] DR-003: Spacing system defined
- [ ] DR-004: Component patterns documented
- [ ] DR-005: Interactive states documented (hover, focus, active, disabled)
- [ ] DR-006: Responsive breakpoints identified
- [ ] DR-007: Animation/transition patterns noted
- [ ] DR-008: Dark mode considerations (if applicable)
```

## CRITICAL RULES
1. Scrape EVERY URL provided — do not skip any
2. Extract ACTUAL values (hex codes, pixel values, font names) — not vague descriptions
3. If a value cannot be determined from scraping, note it as "NOT FOUND — use project default"
4. Write the file using the Write tool — do NOT just output the content
5. Check ALL items in the Design Requirements Checklist that you were able to extract
6. Be thorough — this document drives the entire UI implementation
"""

# Required section headers for validation
_REQUIRED_SECTIONS = [
    "Color System",
    "Typography",
    "Spacing",
    "Component Patterns",
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

async def run_design_extraction(
    urls: list[str],
    config: AgentTeamConfig,
    cwd: str,
    backend: str,
) -> tuple[str, float]:
    """Run a focused Claude session to extract design references.

    Creates a minimal ClaudeSDKClient with only Firecrawl MCP servers,
    sends the extraction prompt, and validates the output file.

    Parameters
    ----------
    urls : list[str]
        Design reference URLs to scrape.
    config : AgentTeamConfig
        Full config (used for MCP server settings and output path).
    cwd : str
        Working directory for the Claude session.
    backend : str
        "api" or "cli" — transport backend.

    Returns
    -------
    tuple[str, float]
        (content of UI_REQUIREMENTS.md, cost in USD)

    Raises
    ------
    DesignExtractionError
        If extraction fails or output file is not written.
    """
    from .mcp_servers import get_firecrawl_only_servers

    req_dir = config.convergence.requirements_dir
    ui_file = config.design_reference.ui_requirements_file
    ui_requirements_path = f"{req_dir}/{ui_file}"

    # Build MCP servers (Firecrawl only)
    mcp_servers = get_firecrawl_only_servers(config)
    if not mcp_servers:
        raise DesignExtractionError(
            "Firecrawl MCP server unavailable — cannot extract design references"
        )

    # Format the system prompt with the output path
    system_prompt = DESIGN_EXTRACTION_SYSTEM_PROMPT.replace(
        "{ui_requirements_path}", ui_requirements_path,
    )

    # Build the task prompt
    url_list = "\n".join(f"  - {url}" for url in urls)
    task_prompt = (
        f"[DESIGN REFERENCE EXTRACTION]\n"
        f"Scrape the following design reference URLs and create "
        f"`{ui_requirements_path}`:\n\n{url_list}\n\n"
        f"Max pages per site: {config.design_reference.max_pages_per_site}\n"
        f"Extraction depth: {config.design_reference.depth}\n\n"
        f"Write the output file to: {ui_requirements_path}\n"
        f"Create the {req_dir}/ directory first if it doesn't exist."
    )

    # Build options for a minimal session
    opts_kwargs: dict[str, Any] = {
        "model": config.orchestrator.model,
        "system_prompt": system_prompt,
        "permission_mode": config.orchestrator.permission_mode,
        "max_turns": 30,  # Extraction shouldn't need many turns
        "allowed_tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        "mcp_servers": mcp_servers,
        "cwd": Path(cwd),
    }

    if backend == "cli":
        import shutil
        import sys
        _cli_name = "claude.exe" if sys.platform == "win32" else "claude"
        _resolved = shutil.which(_cli_name)
        if not _resolved:
            _home_path = Path.home() / ".local" / "bin" / _cli_name
            _resolved = str(_home_path) if _home_path.exists() else _cli_name
        opts_kwargs["cli_path"] = _resolved

    options = ClaudeAgentOptions(**opts_kwargs)
    cost = 0.0

    async with ClaudeSDKClient(options=options) as client:
        await client.query(task_prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        pass  # Tools are expected (Write, firecrawl_scrape, etc.)
            elif isinstance(msg, ResultMessage):
                if msg.total_cost_usd:
                    cost = msg.total_cost_usd

    # Read the output file
    output_path = Path(cwd) / req_dir / ui_file
    if not output_path.is_file():
        raise DesignExtractionError(
            f"Extraction session completed but {ui_requirements_path} was not written"
        )

    content = output_path.read_text(encoding="utf-8")
    if not content.strip():
        raise DesignExtractionError(
            f"{ui_requirements_path} was written but is empty"
        )

    return content, cost


def validate_ui_requirements(content: str) -> list[str]:
    """Check for required section headers in UI_REQUIREMENTS.md.

    Parameters
    ----------
    content : str
        The content of UI_REQUIREMENTS.md.

    Returns
    -------
    list[str]
        List of missing section names. Empty list means all sections present.
    """
    missing: list[str] = []
    for section in _REQUIRED_SECTIONS:
        # Match "## Color System" or "# Color System" (flexible heading level)
        pattern = rf"^#+\s+{re.escape(section)}"
        if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            missing.append(section)
    return missing


def load_ui_requirements(cwd: str, config: AgentTeamConfig) -> str | None:
    """Load existing UI_REQUIREMENTS.md for resume scenarios.

    Parameters
    ----------
    cwd : str
        Project working directory.
    config : AgentTeamConfig
        Config with requirements_dir and ui_requirements_file.

    Returns
    -------
    str | None
        Content of the file, or None if not found or empty.
    """
    req_dir = config.convergence.requirements_dir
    ui_file = config.design_reference.ui_requirements_file
    output_path = Path(cwd) / req_dir / ui_file

    if not output_path.is_file():
        return None

    content = output_path.read_text(encoding="utf-8")
    return content if content.strip() else None


def format_ui_requirements_block(content: str) -> str:
    """Wrap UI_REQUIREMENTS.md content with delimiters for prompt injection.

    The content is injected as ANALYZED FACT — not instructions to go scrape.
    This ensures the orchestrator treats it as pre-computed design data.

    Parameters
    ----------
    content : str
        Raw content of UI_REQUIREMENTS.md.

    Returns
    -------
    str
        Formatted block with delimiters.
    """
    return (
        "\n============================================================\n"
        "PRE-ANALYZED DESIGN REFERENCE (from UI_REQUIREMENTS.md)\n"
        "============================================================\n"
        "The following design reference data was extracted from the user's\n"
        "reference URLs in Phase 0.6. This is ANALYZED FACT — do NOT re-scrape\n"
        "the URLs. Use these values directly for all UI implementation.\n"
        "The extracted branding (colors, fonts, spacing) OVERRIDES generic\n"
        "design tokens, but structural principles and anti-patterns STILL APPLY.\n"
        "============================================================\n\n"
        f"{content}\n\n"
        "============================================================\n"
        "END PRE-ANALYZED DESIGN REFERENCE\n"
        "============================================================"
    )
