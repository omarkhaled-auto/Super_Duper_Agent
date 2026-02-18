"""Tests for MCP tool name references in prompt constants.

Every prompt string that references an MCP tool must use the full
``mcp__<server>__<tool>`` double-underscore format.  Bare shorthand names
(e.g. ``firecrawl_scrape`` instead of ``mcp__firecrawl__firecrawl_scrape``)
cause silent failures because the orchestrator cannot find those tools.
"""

from __future__ import annotations

import re

import pytest

from agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_REVIEWER_PROMPT,
    CODE_WRITER_PROMPT,
    CONTRACT_GENERATOR_PROMPT,
    DEBUGGER_PROMPT,
    INTEGRATION_AGENT_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    SECURITY_AUDITOR_PROMPT,
    SPEC_VALIDATOR_PROMPT,
    TASK_ASSIGNER_PROMPT,
    TEST_RUNNER_PROMPT,
)
from agent_team.design_reference import DESIGN_EXTRACTION_SYSTEM_PROMPT
from agent_team.tech_research import TECH_RESEARCH_PROMPT

# All prompt constants we check — add new ones here as they are created.
_ALL_PROMPT_CONSTANTS: dict[str, str] = {
    "ORCHESTRATOR_SYSTEM_PROMPT": ORCHESTRATOR_SYSTEM_PROMPT,
    "PLANNER_PROMPT": PLANNER_PROMPT,
    "SPEC_VALIDATOR_PROMPT": SPEC_VALIDATOR_PROMPT,
    "RESEARCHER_PROMPT": RESEARCHER_PROMPT,
    "ARCHITECT_PROMPT": ARCHITECT_PROMPT,
    "CODE_WRITER_PROMPT": CODE_WRITER_PROMPT,
    "CODE_REVIEWER_PROMPT": CODE_REVIEWER_PROMPT,
    "TEST_RUNNER_PROMPT": TEST_RUNNER_PROMPT,
    "SECURITY_AUDITOR_PROMPT": SECURITY_AUDITOR_PROMPT,
    "DEBUGGER_PROMPT": DEBUGGER_PROMPT,
    "TASK_ASSIGNER_PROMPT": TASK_ASSIGNER_PROMPT,
    "INTEGRATION_AGENT_PROMPT": INTEGRATION_AGENT_PROMPT,
    "CONTRACT_GENERATOR_PROMPT": CONTRACT_GENERATOR_PROMPT,
    "DESIGN_EXTRACTION_SYSTEM_PROMPT": DESIGN_EXTRACTION_SYSTEM_PROMPT,
    "TECH_RESEARCH_PROMPT": TECH_RESEARCH_PROMPT,
}

# Firecrawl tool shorthand names that must always be prefixed with mcp__firecrawl__
_FIRECRAWL_TOOLS = [
    "firecrawl_scrape",
    "firecrawl_search",
    "firecrawl_map",
    "firecrawl_extract",
    "firecrawl_agent",
    "firecrawl_agent_status",
]

# Context7 tool shorthand names that must always be prefixed with mcp__context7__
_CONTEXT7_TOOLS = [
    "resolve-library-id",
    "query-docs",
]

# Valid MCP tool name pattern: mcp__<server>__<tool>
_RE_MCP_TOOL = re.compile(r"mcp__[a-z0-9_-]+__[a-z0-9_-]+")


# ===================================================================
# Test 1: All mcp__ references use proper double-underscore format
# ===================================================================

class TestMcpToolNameFormat:
    """Every ``mcp_*`` token in prompt strings must match ``mcp__server__tool``."""

    _RE_MCP_ANY = re.compile(r"\bmcp_[a-z0-9_-]+")

    _PROMPT_ITEMS = list(_ALL_PROMPT_CONSTANTS.items())

    @pytest.mark.parametrize(
        "name,prompt",
        _PROMPT_ITEMS,
        ids=[item[0] for item in _PROMPT_ITEMS],
    )
    def test_all_mcp_references_use_double_underscore(self, name: str, prompt: str) -> None:
        for match in self._RE_MCP_ANY.finditer(prompt):
            token = match.group()
            assert _RE_MCP_TOOL.fullmatch(token), (
                f"{name} contains malformed MCP tool reference: {token!r} "
                f"(expected pattern mcp__<server>__<tool>)"
            )


# ===================================================================
# Test 2: No bare firecrawl tool references
# ===================================================================

class TestNoBareFirecrawlReferences:
    """No prompt string should contain a bare ``firecrawl_<tool>`` not preceded
    by ``mcp__firecrawl__``."""

    @pytest.mark.parametrize("tool", _FIRECRAWL_TOOLS)
    def test_no_bare_firecrawl_tool_reference(self, tool: str) -> None:
        pattern = re.compile(rf"(?<!mcp__firecrawl__){re.escape(tool)}\b")
        for name, prompt in _ALL_PROMPT_CONSTANTS.items():
            matches = pattern.findall(prompt)
            assert not matches, (
                f"{name} contains {len(matches)} bare reference(s) to {tool!r} "
                f"without mcp__firecrawl__ prefix"
            )


# ===================================================================
# Test 3: No bare Context7 tool references
# ===================================================================

class TestNoBareContext7References:
    """No prompt string should contain a bare ``resolve-library-id`` or
    ``query-docs`` not preceded by ``mcp__context7__``."""

    @pytest.mark.parametrize("tool", _CONTEXT7_TOOLS)
    def test_no_bare_context7_tool_reference(self, tool: str) -> None:
        pattern = re.compile(rf"(?<!mcp__context7__){re.escape(tool)}")
        for name, prompt in _ALL_PROMPT_CONSTANTS.items():
            matches = pattern.findall(prompt)
            assert not matches, (
                f"{name} contains {len(matches)} bare reference(s) to {tool!r} "
                f"without mcp__context7__ prefix"
            )


# ===================================================================
# Test 4: Orchestrator prompt instructs proactive Context7 usage
# ===================================================================

class TestOrchestratorProactiveContext7:
    """The orchestrator prompt must contain clear instructions about using
    Context7 proactively BEFORE deploying coding fleets."""

    def test_orchestrator_mentions_proactive_context7(self) -> None:
        assert "mcp__context7__resolve-library-id" in ORCHESTRATOR_SYSTEM_PROMPT, (
            "Orchestrator prompt must reference mcp__context7__resolve-library-id"
        )
        assert "mcp__context7__query-docs" in ORCHESTRATOR_SYSTEM_PROMPT, (
            "Orchestrator prompt must reference mcp__context7__query-docs"
        )

    def test_orchestrator_says_only_agent_with_mcp(self) -> None:
        assert "only agent with mcp" in ORCHESTRATOR_SYSTEM_PROMPT.lower(), (
            "Orchestrator prompt must tell the orchestrator it is the ONLY agent with MCP access"
        )

    def test_orchestrator_says_subagents_no_mcp(self) -> None:
        prompt_lower = ORCHESTRATOR_SYSTEM_PROMPT.lower()
        assert "sub-agents do not have mcp" in prompt_lower or \
               "sub-agents cannot access mcp" in prompt_lower or \
               "they cannot access mcp" in prompt_lower, (
            "Orchestrator prompt must warn that sub-agents cannot access MCP tools"
        )

    def test_orchestrator_says_before_deploying(self) -> None:
        assert "before deploying" in ORCHESTRATOR_SYSTEM_PROMPT.lower(), (
            "Orchestrator prompt must instruct to use Context7 BEFORE deploying coding fleets"
        )

    def test_orchestrator_says_never_delegate(self) -> None:
        assert "never delegate" in ORCHESTRATOR_SYSTEM_PROMPT.lower(), (
            "Orchestrator prompt must say NEVER delegate Context7 lookups to sub-agents"
        )


# ===================================================================
# Test 5: Correct MCP tool names appear in prompts that reference them
# ===================================================================

class TestCorrectMcpToolNamesPresent:
    """Verify that the correct full MCP tool names actually appear in
    the prompts that should reference them."""

    def test_orchestrator_lists_firecrawl_tools(self) -> None:
        for tool in ["firecrawl_search", "firecrawl_scrape", "firecrawl_map", "firecrawl_extract"]:
            full_name = f"mcp__firecrawl__{tool}"
            assert full_name in ORCHESTRATOR_SYSTEM_PROMPT, (
                f"Orchestrator prompt must list {full_name}"
            )

    def test_orchestrator_lists_context7_tools(self) -> None:
        for tool in ["resolve-library-id", "query-docs"]:
            full_name = f"mcp__context7__{tool}"
            assert full_name in ORCHESTRATOR_SYSTEM_PROMPT, (
                f"Orchestrator prompt must list {full_name}"
            )

    def test_researcher_uses_full_firecrawl_names(self) -> None:
        for tool in ["firecrawl_scrape", "firecrawl_map", "firecrawl_extract", "firecrawl_agent"]:
            full_name = f"mcp__firecrawl__{tool}"
            assert full_name in RESEARCHER_PROMPT, (
                f"Researcher prompt must use {full_name}"
            )

    def test_design_extraction_uses_full_firecrawl_names(self) -> None:
        for tool in ["firecrawl_scrape", "firecrawl_search", "firecrawl_map", "firecrawl_extract"]:
            full_name = f"mcp__firecrawl__{tool}"
            assert full_name in DESIGN_EXTRACTION_SYSTEM_PROMPT, (
                f"Design extraction prompt must use {full_name}"
            )

    def test_tech_research_uses_full_context7_names(self) -> None:
        for tool in ["resolve-library-id", "query-docs"]:
            full_name = f"mcp__context7__{tool}"
            assert full_name in TECH_RESEARCH_PROMPT, (
                f"Tech research prompt must use {full_name}"
            )
