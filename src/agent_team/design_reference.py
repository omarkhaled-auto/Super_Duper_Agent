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
        opts_kwargs["cli_path"] = "claude"

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


def _split_into_sections(content: str) -> dict[str, str]:
    """Split markdown content by ## headers into a dict of section_name -> section_body.

    Parameters
    ----------
    content : str
        Markdown text with ## headers.

    Returns
    -------
    dict[str, str]
        Mapping of lowercase section name to the text under that heading.
    """
    sections: dict[str, str] = {}
    current_name = ""
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_name:
                sections[current_name] = "\n".join(current_lines)
            current_name = line.lstrip("#").strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_name:
        sections[current_name] = "\n".join(current_lines)

    return sections


# Regex patterns for content quality validation
_RE_HEX_COLOR = re.compile(r'#[0-9a-fA-F]{3,8}\b')
_RE_FONT_FAMILY = re.compile(
    r'(?:font[-_]?family|fontFamily|font:|typeface)\s*[:=]?\s*["\']?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    re.IGNORECASE,
)
_RE_SPACING_VALUE = re.compile(r'\b\d+(?:px|rem|em)\b')
_RE_COMPONENT_TYPE = re.compile(
    r'\b(?:buttons?|cards?|inputs?|modals?|dialogs?|tables?|lists?|navs?|headers?|sidebars?|badges?|avatars?|toasts?|tabs?)\b',
    re.IGNORECASE,
)
_RE_NOT_FOUND = re.compile(r'NOT\s+FOUND', re.IGNORECASE)


def validate_ui_requirements_content(content: str) -> list[str]:
    """Validate that UI_REQUIREMENTS.md sections contain ACTUAL values, not just headers.

    Unlike :func:`validate_ui_requirements` which checks for section header presence,
    this function checks that each section contains meaningful design tokens:
    - Color System: at least 3 hex color codes
    - Typography: at least 1 font family declaration
    - Spacing: at least 3 spacing values (px/rem)
    - Component Patterns: at least 2 component type mentions

    Also counts "NOT FOUND" occurrences as a negative signal.

    Parameters
    ----------
    content : str
        The content of UI_REQUIREMENTS.md.

    Returns
    -------
    list[str]
        List of quality issue descriptions. Empty = good quality.
    """
    issues: list[str] = []
    sections = _split_into_sections(content)

    # Check Color System section
    color_section = sections.get("color system", "")
    hex_colors = _RE_HEX_COLOR.findall(color_section)
    if len(hex_colors) < 3:
        issues.append(
            f"Color System: only {len(hex_colors)} hex color(s) found (minimum 3 required)"
        )

    # Check Typography section
    typo_section = sections.get("typography", "")
    font_families = _RE_FONT_FAMILY.findall(typo_section)
    if len(font_families) < 1:
        issues.append(
            "Typography: no font family declarations found (minimum 1 required)"
        )

    # Check Spacing section
    spacing_section = sections.get("spacing", "")
    spacing_values = _RE_SPACING_VALUE.findall(spacing_section)
    if len(spacing_values) < 3:
        issues.append(
            f"Spacing: only {len(spacing_values)} spacing value(s) found (minimum 3 required)"
        )

    # Check Component Patterns section
    component_section = sections.get("component patterns", "")
    component_types = set(_RE_COMPONENT_TYPE.findall(component_section.lower()))
    if len(component_types) < 2:
        issues.append(
            f"Component Patterns: only {len(component_types)} component type(s) found (minimum 2 required)"
        )

    # Check for excessive NOT FOUND markers (negative signal)
    not_found_count = len(_RE_NOT_FOUND.findall(content))
    if not_found_count > 5:
        issues.append(
            f"Excessive 'NOT FOUND' markers ({not_found_count}) — extraction quality is poor"
        )

    return issues


async def run_design_extraction_with_retry(
    urls: list[str],
    config: AgentTeamConfig,
    cwd: str,
    backend: str,
    max_retries: int = 2,
    base_delay: float = 5.0,
) -> tuple[str, float]:
    """Wrap :func:`run_design_extraction` with exponential backoff retry.

    Parameters
    ----------
    urls : list[str]
        Design reference URLs.
    config : AgentTeamConfig
        Full config.
    cwd : str
        Working directory.
    backend : str
        "api" or "cli".
    max_retries : int
        Number of retry attempts (default 2).
    base_delay : float
        Base delay in seconds between retries (doubles each attempt).

    Returns
    -------
    tuple[str, float]
        (content, accumulated_cost)

    Raises
    ------
    DesignExtractionError
        If ALL attempts fail.
    """
    total_cost = 0.0
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            content, cost = await run_design_extraction(
                urls=urls, config=config, cwd=cwd, backend=backend,
            )
            total_cost += cost
            return content, total_cost
        except DesignExtractionError as exc:
            # Expected failure — retry
            last_error = exc
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            continue
        except (OSError, ConnectionError, TimeoutError) as exc:
            # Network/IO failures — retry
            last_error = exc
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            continue
        except Exception as exc:
            # Unexpected error (bug) — don't retry, surface immediately
            raise DesignExtractionError(
                f"Unexpected error during design extraction: {exc}"
            ) from exc

    raise DesignExtractionError(
        f"Design extraction failed after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )


# Direction inference table for fallback generation
_DIRECTION_TABLE: dict[str, dict[str, str]] = {
    "brutalist": {
        "keywords": "developer,cli,terminal,tool,hacker,code,devtool",
        "primary": "#000000",
        "secondary": "#FFFFFF",
        "accent": "#FF3333",
        "heading_font": "Space Grotesk",
        "body_font": "IBM Plex Mono",
        "base_unit": "8px",
    },
    "luxury": {
        "keywords": "premium,fintech,fashion,luxury,boutique,exclusive,wealth",
        "primary": "#1A1A2E",
        "secondary": "#E8D5B7",
        "accent": "#C9A96E",
        "heading_font": "Cormorant Garamond",
        "body_font": "Outfit",
        "base_unit": "8px",
    },
    "industrial": {
        "keywords": "enterprise,erp,logistics,warehouse,manufacturing,supply",
        "primary": "#1E293B",
        "secondary": "#F1F5F9",
        "accent": "#F59E0B",
        "heading_font": "Space Grotesk",
        "body_font": "Inter",
        "base_unit": "4px",
    },
    "minimal_modern": {
        "keywords": "saas,dashboard,startup,app,platform,analytics,crm",
        "primary": "#0F172A",
        "secondary": "#F8FAFC",
        "accent": "#6366F1",
        "heading_font": "Plus Jakarta Sans",
        "body_font": "Outfit",
        "base_unit": "4px",
    },
    "editorial": {
        "keywords": "blog,news,content,magazine,media,publication,article",
        "primary": "#111827",
        "secondary": "#FFFBEB",
        "accent": "#B91C1C",
        "heading_font": "Playfair Display",
        "body_font": "Newsreader",
        "base_unit": "8px",
    },
}


def _infer_design_direction(task: str) -> str:
    """Infer design direction from task keywords.

    Returns the direction name that best matches the task text.
    Falls back to 'minimal_modern' if no keywords match.
    """
    task_lower = task.lower()
    best_match = "minimal_modern"
    best_score = 0

    for direction, info in _DIRECTION_TABLE.items():
        keywords = info["keywords"].split(",")
        score = sum(
            1 for kw in keywords
            if re.search(rf"\b{re.escape(kw)}\b", task_lower)
        )
        if score > best_score:
            best_score = score
            best_match = direction

    return best_match


def generate_fallback_ui_requirements(
    task: str,
    config: AgentTeamConfig,
    cwd: str,
) -> str:
    """Generate a heuristic UI_REQUIREMENTS.md when extraction fails.

    Infers a design direction from task keywords and populates all required
    sections with direction-appropriate defaults. Writes to disk with a
    FALLBACK-GENERATED warning header.

    Parameters
    ----------
    task : str
        The user's task description (used for direction inference).
    config : AgentTeamConfig
        Config with requirements_dir and ui_requirements_file.
    cwd : str
        Project working directory.

    Returns
    -------
    str
        Content of the generated fallback UI_REQUIREMENTS.md.
    """
    direction = _infer_design_direction(task)
    d = _DIRECTION_TABLE[direction]

    content = f'''# UI Requirements — Fallback Generated
> **WARNING: FALLBACK-GENERATED** — This document was auto-generated because
> design reference extraction failed. Values are heuristic defaults based on
> detected project direction: **{direction}**. Review and customize these values.

Generated direction: {direction}

## Color System
- Primary: {d["primary"]}
- Secondary: {d["secondary"]}
- Accent: {d["accent"]}
- Background (light): #FFFFFF
- Background (dark): {d["primary"]}
- Surface: {d["secondary"]}
- Text Primary: {d["primary"]}
- Text Secondary: #64748B
- Text Muted: #94A3B8
- Border: #E2E8F0
- Error: #EF4444
- Success: #22C55E
- Warning: #F59E0B
- Info: #3B82F6

## Typography
- Heading font: {d["heading_font"]}
- Body font: {d["body_font"]}
- Mono font: JetBrains Mono
- Font sizes: xs=12px, sm=14px, base=16px, lg=18px, xl=20px, 2xl=24px, 3xl=30px, 4xl=36px
- Font weights: light=300, normal=400, medium=500, semibold=600, bold=700, extrabold=800
- Line heights: tight=1.25, normal=1.5, relaxed=1.75

## Spacing
- Base unit: {d["base_unit"]}
- Scale: xs=4px, sm=8px, md=16px, lg=24px, xl=32px, 2xl=48px, 3xl=64px, 4xl=96px
- Container max-width: 1280px
- Section padding: 64px vertical, 24px horizontal
- Card padding: 24px

## Component Patterns
- Buttons: primary (filled), secondary (outlined), ghost (text-only), destructive (red)
  - Border radius: 8px
  - Padding: 10px 20px
  - States: default, hover, focus, active, disabled, loading
- Cards: shadow-sm, border-radius 12px, padding 24px
- Inputs: border 1px, border-radius 8px, padding 10px 14px, focus ring
- Navigation: sticky header, mobile hamburger at 768px
- Modals: backdrop blur, centered, max-width 520px
- Tables: alternating row colors, sticky header
- Badges: rounded-full, padding 2px 10px

## Design Requirements Checklist
- [ ] DR-001: Color system tokens defined
- [ ] DR-002: Typography scale defined
- [ ] DR-003: Spacing system defined
- [ ] DR-004: Component patterns documented
- [ ] DR-005: Interactive states documented (hover, focus, active, disabled)
- [ ] DR-006: Responsive breakpoints identified
- [ ] DR-007: Animation/transition patterns noted
- [ ] DR-008: Dark mode considerations (if applicable)
'''

    # Write to disk
    req_dir = config.convergence.requirements_dir
    ui_file = config.design_reference.ui_requirements_file
    output_dir = Path(cwd) / req_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / ui_file
    output_path.write_text(content, encoding="utf-8")

    return content


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
