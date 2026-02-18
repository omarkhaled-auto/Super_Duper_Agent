"""Tests for allowed_tools recomputation after MCP server override.

Validates that when mcp_servers is swapped (e.g., for browser testing),
allowed_tools is recalculated to include the correct tool names.
"""

from __future__ import annotations

import pytest

from agent_team.mcp_servers import (
    _BASE_TOOLS,
    get_browser_testing_servers,
    get_mcp_servers,
    get_orchestrator_st_tool_name,
    get_playwright_tools,
    get_research_tools,
    recompute_allowed_tools,
)
from agent_team.config import AgentTeamConfig, MCPServerConfig


# ===================================================================
# get_playwright_tools()
# ===================================================================


class TestGetPlaywrightTools:
    """Verify the Playwright tool name list."""

    def test_returns_list(self):
        result = get_playwright_tools()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_all_prefixed_correctly(self):
        for tool in get_playwright_tools():
            assert tool.startswith("mcp__playwright__"), f"Bad prefix: {tool}"

    def test_contains_essential_tools(self):
        tools = get_playwright_tools()
        essentials = [
            "mcp__playwright__browser_navigate",
            "mcp__playwright__browser_snapshot",
            "mcp__playwright__browser_click",
            "mcp__playwright__browser_type",
            "mcp__playwright__browser_take_screenshot",
            "mcp__playwright__browser_close",
        ]
        for name in essentials:
            assert name in tools, f"Missing essential tool: {name}"

    def test_contains_22_tools(self):
        assert len(get_playwright_tools()) == 22

    def test_no_duplicates(self):
        tools = get_playwright_tools()
        assert len(tools) == len(set(tools))


# ===================================================================
# _BASE_TOOLS
# ===================================================================


class TestBaseTools:
    """Verify the base tools constant."""

    def test_contains_core_tools(self):
        expected = ["Read", "Write", "Edit", "Bash", "Glob", "Grep",
                    "Task", "WebSearch", "WebFetch"]
        assert _BASE_TOOLS == expected

    def test_is_list(self):
        assert isinstance(_BASE_TOOLS, list)


# ===================================================================
# recompute_allowed_tools() — core function
# ===================================================================


class TestRecomputeAllowedTools:
    """Test the recompute_allowed_tools function with various server combinations."""

    def test_empty_servers_returns_base_only(self):
        result = recompute_allowed_tools(_BASE_TOOLS, {})
        assert result == list(_BASE_TOOLS)

    def test_does_not_mutate_input(self):
        base = list(_BASE_TOOLS)
        original = list(base)
        recompute_allowed_tools(base, {"playwright": {}})
        assert base == original, "Input list was mutated"

    def test_context7_adds_research_tools(self):
        servers = {"context7": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert "mcp__context7__resolve-library-id" in result
        assert "mcp__context7__query-docs" in result

    def test_firecrawl_adds_research_tools(self):
        servers = {"firecrawl": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert "mcp__firecrawl__firecrawl_search" in result
        assert "mcp__firecrawl__firecrawl_scrape" in result

    def test_sequential_thinking_adds_st_tool(self):
        servers = {"sequential_thinking": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert get_orchestrator_st_tool_name() in result

    def test_playwright_adds_all_playwright_tools(self):
        servers = {"playwright": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        for tool in get_playwright_tools():
            assert tool in result, f"Missing Playwright tool: {tool}"

    def test_playwright_plus_context7(self):
        servers = {
            "playwright": {"type": "stdio"},
            "context7": {"type": "stdio"},
        }
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        # Base tools present
        for t in _BASE_TOOLS:
            assert t in result
        # Playwright tools present
        for t in get_playwright_tools():
            assert t in result
        # Context7 tools present
        assert "mcp__context7__resolve-library-id" in result
        assert "mcp__context7__query-docs" in result

    def test_all_servers_combined(self):
        servers = {
            "firecrawl": {"type": "stdio"},
            "context7": {"type": "stdio"},
            "sequential_thinking": {"type": "stdio"},
            "playwright": {"type": "stdio"},
        }
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        # All categories present
        assert "mcp__firecrawl__firecrawl_search" in result
        assert "mcp__context7__resolve-library-id" in result
        assert get_orchestrator_st_tool_name() in result
        assert "mcp__playwright__browser_navigate" in result

    def test_no_playwright_when_not_in_servers(self):
        servers = {"context7": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        for tool in get_playwright_tools():
            assert tool not in result

    def test_no_st_when_not_in_servers(self):
        servers = {"playwright": {"type": "stdio"}}
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert get_orchestrator_st_tool_name() not in result

    def test_custom_base_tools(self):
        custom = ["Read", "Write"]
        servers = {"playwright": {"type": "stdio"}}
        result = recompute_allowed_tools(custom, servers)
        assert "Read" in result
        assert "Write" in result
        assert "mcp__playwright__browser_navigate" in result
        # Base tools not in custom should be absent
        assert "Bash" not in result

    def test_returns_new_list(self):
        base = list(_BASE_TOOLS)
        result = recompute_allowed_tools(base, {})
        assert result is not base


# ===================================================================
# Browser server override scenario
# ===================================================================


class TestBrowserServerOverrideScenario:
    """Simulate the exact pattern used in cli.py for browser testing."""

    def _make_config(self) -> AgentTeamConfig:
        """Create a config with context7 enabled."""
        cfg = AgentTeamConfig()
        cfg.mcp_servers["context7"] = MCPServerConfig(enabled=True)
        return cfg

    def test_browser_servers_include_playwright(self):
        config = self._make_config()
        servers = get_browser_testing_servers(config)
        assert "playwright" in servers

    def test_browser_servers_include_context7(self):
        config = self._make_config()
        servers = get_browser_testing_servers(config)
        assert "context7" in servers

    def test_recompute_after_browser_override_has_playwright_tools(self):
        """The exact fix scenario: after overriding mcp_servers with
        browser_servers, recompute should include Playwright tools."""
        config = self._make_config()
        browser_servers = get_browser_testing_servers(config)
        result = recompute_allowed_tools(_BASE_TOOLS, browser_servers)
        # Must have Playwright tools
        assert "mcp__playwright__browser_navigate" in result
        assert "mcp__playwright__browser_click" in result
        assert "mcp__playwright__browser_snapshot" in result
        # Must still have base tools
        assert "Read" in result
        assert "Write" in result
        # Must still have Context7 tools
        assert "mcp__context7__resolve-library-id" in result

    def test_recompute_without_override_has_no_playwright(self):
        """Normal path: get_mcp_servers returns no playwright, so
        recompute should NOT include Playwright tools."""
        config = self._make_config()
        normal_servers = get_mcp_servers(config)
        result = recompute_allowed_tools(_BASE_TOOLS, normal_servers)
        assert "mcp__playwright__browser_navigate" not in result

    def test_browser_servers_no_context7(self):
        """If context7 is disabled, browser servers only has playwright."""
        config = AgentTeamConfig()
        # Explicitly disable context7
        config.mcp_servers["context7"] = MCPServerConfig(enabled=False)
        servers = get_browser_testing_servers(config)
        assert "playwright" in servers
        assert "context7" not in servers
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert "mcp__playwright__browser_navigate" in result
        assert "mcp__context7__resolve-library-id" not in result


# ===================================================================
# Consistency with _build_options
# ===================================================================


class TestConsistencyWithBuildOptions:
    """Verify that recompute_allowed_tools produces the same result as
    the original inline logic in _build_options for non-browser paths."""

    def test_matches_original_logic_context7_only(self):
        servers = {"context7": {"type": "stdio"}}
        # Original logic: base + get_research_tools(servers) + (ST if present)
        original = list(_BASE_TOOLS) + get_research_tools(servers)
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert result == original

    def test_matches_original_logic_context7_and_st(self):
        servers = {
            "context7": {"type": "stdio"},
            "sequential_thinking": {"type": "stdio"},
        }
        original = (
            list(_BASE_TOOLS)
            + get_research_tools(servers)
            + [get_orchestrator_st_tool_name()]
        )
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert result == original

    def test_matches_original_logic_empty(self):
        servers = {}
        original = list(_BASE_TOOLS) + get_research_tools(servers)
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert result == original

    def test_matches_original_logic_all_research(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
        servers = {
            "firecrawl": {"type": "stdio"},
            "context7": {"type": "stdio"},
            "sequential_thinking": {"type": "stdio"},
        }
        original = (
            list(_BASE_TOOLS)
            + get_research_tools(servers)
            + [get_orchestrator_st_tool_name()]
        )
        result = recompute_allowed_tools(_BASE_TOOLS, servers)
        assert result == original
