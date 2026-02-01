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

    return servers


def get_research_tools(servers: dict[str, Any]) -> list[str]:
    """Return the list of allowed MCP tool names for research agents."""
    tools: list[str] = []
    if "firecrawl" in servers:
        tools.extend([
            "mcp__firecrawl__firecrawl_search",
            "mcp__firecrawl__firecrawl_scrape",
            "mcp__firecrawl__firecrawl_map",
            "mcp__firecrawl__firecrawl_extract",
        ])
    if "context7" in servers:
        tools.extend([
            "mcp__context7__resolve-library-id",
            "mcp__context7__query-docs",
        ])
    return tools
