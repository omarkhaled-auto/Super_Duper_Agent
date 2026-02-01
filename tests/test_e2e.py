"""End-to-end smoke tests requiring real API keys.

Run with: pytest tests/test_e2e.py -v --run-e2e
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


pytestmark = pytest.mark.e2e


class TestE2ESmokeTests:
    def test_cli_help_exits_0(self):
        """agent-team --help exits 0."""
        result = subprocess.run(
            [sys.executable, "-m", "agent_team", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "agent-team" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_cli_version_prints_version(self):
        """agent-team --version prints 0.1.0."""
        result = subprocess.run(
            [sys.executable, "-m", "agent_team", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    async def test_sdk_client_context_manager(self):
        """ClaudeSDKClient can __aenter__ / __aexit__ without error."""
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
        opts = ClaudeAgentOptions(
            model="haiku",
            system_prompt="You are a test assistant.",
            max_turns=1,
        )
        async with ClaudeSDKClient(options=opts) as client:
            assert client is not None

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    async def test_sdk_client_say_hello(self):
        """Send 'Say hello' to SDK, receive a TextBlock response."""
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ClaudeSDKClient,
            TextBlock,
        )
        opts = ClaudeAgentOptions(
            model="haiku",
            system_prompt="Reply with exactly: Hello!",
            max_turns=1,
        )
        async with ClaudeSDKClient(options=opts) as client:
            await client.query("Say hello")
            got_text = False
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            got_text = True
            assert got_text, "Expected at least one TextBlock in response"

    @pytest.mark.skipif(
        not os.environ.get("FIRECRAWL_API_KEY"),
        reason="FIRECRAWL_API_KEY not set",
    )
    def test_firecrawl_server_config_valid(self):
        """Firecrawl server config is valid when key present."""
        from agent_team.mcp_servers import _firecrawl_server
        cfg = _firecrawl_server()
        assert cfg is not None
        assert cfg["type"] == "stdio"
        assert cfg["command"] == "npx"
        assert "FIRECRAWL_API_KEY" in cfg["env"]
