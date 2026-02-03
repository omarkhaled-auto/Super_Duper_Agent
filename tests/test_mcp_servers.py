"""Tests for agent_team.mcp_servers."""

from __future__ import annotations

from agent_team.config import AgentTeamConfig, MCPServerConfig
from agent_team.mcp_servers import (
    _context7_server,
    _firecrawl_server,
    _sequential_thinking_server,
    get_mcp_servers,
    get_research_tools,
    is_firecrawl_available,
)


# ===================================================================
# _firecrawl_server()
# ===================================================================

class TestFirecrawlServer:
    def test_with_key_returns_dict(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
        result = _firecrawl_server()
        assert result is not None
        assert isinstance(result, dict)
        assert result["type"] == "stdio"

    def test_without_key_returns_none(self, monkeypatch):
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
        result = _firecrawl_server()
        assert result is None

    def test_uses_npx(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
        result = _firecrawl_server()
        assert result["command"] == "npx"

    def test_env_contains_key(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
        result = _firecrawl_server()
        assert result["env"]["FIRECRAWL_API_KEY"] == "fc-test-key"


# ===================================================================
# _context7_server()
# ===================================================================

class TestContext7Server:
    def test_returns_dict(self):
        result = _context7_server()
        assert isinstance(result, dict)

    def test_no_env_key_needed(self):
        result = _context7_server()
        assert "env" not in result

    def test_uses_npx(self):
        result = _context7_server()
        assert result["command"] == "npx"


# ===================================================================
# _sequential_thinking_server()
# ===================================================================

class TestSequentialThinkingServer:
    def test_returns_dict(self):
        result = _sequential_thinking_server()
        assert isinstance(result, dict)

    def test_no_env_key_needed(self):
        result = _sequential_thinking_server()
        assert "env" not in result

    def test_uses_npx(self):
        result = _sequential_thinking_server()
        assert result["command"] == "npx"

    def test_correct_package(self):
        result = _sequential_thinking_server()
        assert "@anthropic-ai/sequential-thinking-mcp" in result["args"]

    def test_type_is_stdio(self):
        result = _sequential_thinking_server()
        assert result["type"] == "stdio"


# ===================================================================
# get_mcp_servers()
# ===================================================================

class TestGetMcpServers:
    def test_both_enabled_and_present(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        servers = get_mcp_servers(cfg)
        assert "firecrawl" in servers
        assert "context7" in servers

    def test_firecrawl_disabled(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["firecrawl"] = MCPServerConfig(enabled=False)
        servers = get_mcp_servers(cfg)
        assert "firecrawl" not in servers
        assert "context7" in servers

    def test_context7_disabled(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["context7"] = MCPServerConfig(enabled=False)
        servers = get_mcp_servers(cfg)
        assert "firecrawl" in servers
        assert "context7" not in servers

    def test_both_disabled_returns_empty(self, config_with_disabled_mcp):
        servers = get_mcp_servers(config_with_disabled_mcp)
        assert servers == {}

    def test_firecrawl_no_api_key_excluded(self, env_with_anthropic_only):
        cfg = AgentTeamConfig()
        servers = get_mcp_servers(cfg)
        assert "firecrawl" not in servers
        assert "context7" in servers

    def test_missing_config_key_skipped(self):
        cfg = AgentTeamConfig()
        # Remove the firecrawl key entirely
        del cfg.mcp_servers["firecrawl"]
        servers = get_mcp_servers(cfg)
        # Should still work, just without firecrawl
        assert "firecrawl" not in servers

    def test_sequential_thinking_included_when_enabled(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["sequential_thinking"] = MCPServerConfig(enabled=True)
        servers = get_mcp_servers(cfg)
        assert "sequential_thinking" in servers
        assert servers["sequential_thinking"]["command"] == "npx"

    def test_sequential_thinking_excluded_when_disabled(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["sequential_thinking"] = MCPServerConfig(enabled=False)
        servers = get_mcp_servers(cfg)
        assert "sequential_thinking" not in servers

    def test_sequential_thinking_excluded_when_absent(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        # ST not in default mcp_servers, so should be absent
        servers = get_mcp_servers(cfg)
        assert "sequential_thinking" not in servers


# ===================================================================
# get_research_tools()
# ===================================================================

class TestGetResearchTools:
    def test_both_servers_8_tools(self):
        servers = {"firecrawl": {"type": "stdio"}, "context7": {"type": "stdio"}}
        tools = get_research_tools(servers)
        assert len(tools) == 8

    def test_firecrawl_only_6_tools(self):
        servers = {"firecrawl": {"type": "stdio"}}
        tools = get_research_tools(servers)
        assert len(tools) == 6

    def test_context7_only_2_tools(self):
        servers = {"context7": {"type": "stdio"}}
        tools = get_research_tools(servers)
        assert len(tools) == 2

    def test_empty_servers_returns_empty_list(self):
        """Bug #7: should return [] not None."""
        tools = get_research_tools({})
        assert tools == []
        assert isinstance(tools, list)

    def test_correct_tool_names(self):
        servers = {"firecrawl": {"type": "stdio"}, "context7": {"type": "stdio"}}
        tools = get_research_tools(servers)
        assert "mcp__firecrawl__firecrawl_search" in tools
        assert "mcp__firecrawl__firecrawl_scrape" in tools
        assert "mcp__firecrawl__firecrawl_map" in tools
        assert "mcp__firecrawl__firecrawl_extract" in tools
        assert "mcp__firecrawl__firecrawl_agent" in tools
        assert "mcp__firecrawl__firecrawl_agent_status" in tools
        assert "mcp__context7__resolve-library-id" in tools
        assert "mcp__context7__query-docs" in tools


# ===================================================================
# is_firecrawl_available()
# ===================================================================

class TestIsFirecrawlAvailable:
    def test_is_firecrawl_available_with_key(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
        cfg = AgentTeamConfig()
        assert is_firecrawl_available(cfg) is True

    def test_is_firecrawl_available_no_key(self, monkeypatch):
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
        cfg = AgentTeamConfig()
        assert is_firecrawl_available(cfg) is False

    def test_is_firecrawl_available_disabled(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
        cfg = AgentTeamConfig()
        cfg.mcp_servers["firecrawl"] = MCPServerConfig(enabled=False)
        assert is_firecrawl_available(cfg) is False

    def test_is_firecrawl_available_missing_config(self):
        cfg = AgentTeamConfig()
        del cfg.mcp_servers["firecrawl"]
        assert is_firecrawl_available(cfg) is False
