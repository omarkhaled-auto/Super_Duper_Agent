"""MCP server configurations for Agent Team.

Provides Firecrawl (web scraping / search) and Context7 (library docs) servers
that are injected into agents that need web research capabilities.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from .config import AgentTeamConfig


def _firecrawl_server() -> dict[str, Any] | None:
    """Return Firecrawl MCP server config, or None if API key is missing."""
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("[warn] FIRECRAWL_API_KEY not set — Firecrawl MCP server disabled", file=sys.stderr)
        return None
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env": {"FIRECRAWL_API_KEY": api_key},
    }


def _context7_server() -> dict[str, Any]:
    """Return Context7 MCP server config (no API key required)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@anthropic-ai/context7-mcp@latest"],
    }


def _sequential_thinking_server() -> dict[str, Any]:
    """Return Sequential Thinking MCP server config (orchestrator only)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@anthropic-ai/sequential-thinking-mcp"],
    }


def get_mcp_servers(config: AgentTeamConfig) -> dict[str, Any]:
    """Build the MCP servers dict based on config.

    Returns a dict suitable for ClaudeAgentOptions.mcp_servers.
    Skips servers that are disabled or missing required env vars.
    """
    servers: dict[str, Any] = {}

    firecrawl_cfg = config.mcp_servers.get("firecrawl")
    if firecrawl_cfg and firecrawl_cfg.enabled:
        fc = _firecrawl_server()
        if fc:
            servers["firecrawl"] = fc

    context7_cfg = config.mcp_servers.get("context7")
    if context7_cfg and context7_cfg.enabled:
        servers["context7"] = _context7_server()

    st_cfg = config.mcp_servers.get("sequential_thinking")
    if st_cfg and st_cfg.enabled:
        servers["sequential_thinking"] = _sequential_thinking_server()

    return servers


def get_orchestrator_st_tool_name() -> str:
    """Return the MCP tool name for Sequential Thinking."""
    return "mcp__sequential-thinking__sequentialthinking"


def get_research_tools(servers: dict[str, Any]) -> list[str]:
    """Return the list of allowed MCP tool names for research agents."""
    tools: list[str] = []
    if "firecrawl" in servers:
        tools.extend([
            "mcp__firecrawl__firecrawl_search",
            "mcp__firecrawl__firecrawl_scrape",
            "mcp__firecrawl__firecrawl_map",
            "mcp__firecrawl__firecrawl_extract",
            "mcp__firecrawl__firecrawl_agent",
            "mcp__firecrawl__firecrawl_agent_status",
        ])
    if "context7" in servers:
        tools.extend([
            "mcp__context7__resolve-library-id",
            "mcp__context7__query-docs",
        ])
    return tools


def is_firecrawl_available(config: AgentTeamConfig) -> bool:
    """Check if Firecrawl MCP server is configured and has an API key."""
    firecrawl_cfg = config.mcp_servers.get("firecrawl")
    if not firecrawl_cfg or not firecrawl_cfg.enabled:
        return False
    return bool(os.environ.get("FIRECRAWL_API_KEY"))


def get_firecrawl_only_servers(config: AgentTeamConfig) -> dict[str, Any]:
    """Return MCP servers dict with ONLY Firecrawl (for focused extraction sessions).

    Used by Phase 0.6 design reference extraction to create a minimal
    Claude session that can only scrape/search — no Context7, no ST.

    Returns empty dict if Firecrawl is unavailable.
    """
    servers: dict[str, Any] = {}
    firecrawl_cfg = config.mcp_servers.get("firecrawl")
    if firecrawl_cfg and firecrawl_cfg.enabled:
        fc = _firecrawl_server()
        if fc:
            servers["firecrawl"] = fc
    return servers
