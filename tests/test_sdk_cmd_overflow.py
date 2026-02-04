"""Tests for SDK subprocess_cli.py command-line overflow fix.

Verifies that _build_command() temp-files large arguments (--system-prompt,
--agents, --append-system-prompt, --mcp-config) when the command line exceeds
_CMD_LENGTH_LIMIT, preventing Windows CreateProcess failures.
"""

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_agent_sdk._internal.transport.subprocess_cli import (
    SubprocessCLITransport,
    _CMD_LENGTH_LIMIT,
)
from claude_agent_sdk.types import AgentDefinition, ClaudeAgentOptions


def make_transport(
    system_prompt: str | None = None,
    agents: dict | None = None,
    mcp_servers: dict | None = None,
    append_system_prompt: str | None = None,
) -> SubprocessCLITransport:
    """Create a SubprocessCLITransport with given options."""
    sp = system_prompt
    if append_system_prompt:
        sp = {"type": "preset", "append": append_system_prompt}

    options = ClaudeAgentOptions(
        system_prompt=sp,
        agents=agents,
        mcp_servers=mcp_servers,
        cli_path="claude",
    )
    return SubprocessCLITransport(prompt="test prompt", options=options)


def get_flag_value(cmd: list[str], flag: str) -> str | None:
    """Extract value of a CLI flag from command list."""
    try:
        idx = cmd.index(flag)
        return cmd[idx + 1]
    except (ValueError, IndexError):
        return None


class TestSystemPromptTempFiling:
    """Test that --system-prompt gets temp-filed when command is too long."""

    def test_short_system_prompt_stays_inline(self):
        """System prompts under threshold stay inline."""
        transport = make_transport(system_prompt="Short prompt")
        cmd = transport._build_command()
        value = get_flag_value(cmd, "--system-prompt")

        assert value == "Short prompt"
        assert not value.startswith("@")
        assert len(transport._temp_files) == 0

    def test_long_system_prompt_gets_temp_filed(self):
        """System prompt gets temp-filed when command exceeds limit."""
        # Create a system prompt large enough to exceed _CMD_LENGTH_LIMIT
        large_prompt = "X" * (_CMD_LENGTH_LIMIT + 5000)
        transport = make_transport(system_prompt=large_prompt)
        cmd = transport._build_command()
        value = get_flag_value(cmd, "--system-prompt")

        # Should be a @filepath reference
        assert value is not None
        assert value.startswith("@"), f"Expected @filepath, got: {value[:50]}..."
        filepath = value[1:]  # Strip the @ prefix

        # Temp file should exist and contain the original prompt
        assert Path(filepath).exists(), f"Temp file not found: {filepath}"
        content = Path(filepath).read_text(encoding="utf-8")
        assert content == large_prompt
        assert len(transport._temp_files) == 1

        # Cleanup
        Path(filepath).unlink(missing_ok=True)

    def test_command_length_reduced_after_temp_filing(self):
        """Total command length is under limit after temp-filing."""
        large_prompt = "Y" * (_CMD_LENGTH_LIMIT + 5000)
        transport = make_transport(system_prompt=large_prompt)
        cmd = transport._build_command()
        cmd_str = " ".join(cmd)

        # After temp-filing, command should be well under the limit
        assert len(cmd_str) < _CMD_LENGTH_LIMIT, (
            f"Command still too long after temp-filing: {len(cmd_str)} chars"
        )

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)

    def test_small_system_prompt_not_temp_filed_even_if_cmd_long(self):
        """Small system prompts (<1000 chars) are not temp-filed, even if
        the command is long due to other arguments."""
        small_prompt = "Z" * 500  # Under 1000 char threshold
        # Make command long via agents instead
        agents = {
            f"agent_{i}": AgentDefinition(
                description=f"Agent {i} " * 200,
                prompt=f"Instructions for agent {i} " * 200,
            )
            for i in range(5)
        }
        transport = make_transport(system_prompt=small_prompt, agents=agents)
        cmd = transport._build_command()
        sp_value = get_flag_value(cmd, "--system-prompt")

        # System prompt should stay inline (it's small)
        assert sp_value == small_prompt
        assert not sp_value.startswith("@")

        # But agents should be temp-filed (they're large)
        agents_value = get_flag_value(cmd, "--agents")
        assert agents_value.startswith("@")

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)


class TestAgentsTempFiling:
    """Regression tests: --agents temp-filing still works after refactor."""

    def test_large_agents_get_temp_filed(self):
        """Large --agents JSON gets temp-filed when command exceeds limit."""
        agents = {
            f"agent_{i}": AgentDefinition(
                description=f"Agent {i} description " * 500,
                prompt=f"Instructions " * 500,
            )
            for i in range(3)
        }
        transport = make_transport(agents=agents)
        cmd = transport._build_command()
        value = get_flag_value(cmd, "--agents")

        assert value is not None
        assert value.startswith("@"), f"Expected @filepath, got: {value[:50]}..."
        assert len(transport._temp_files) >= 1

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)

    def test_small_agents_stay_inline(self):
        """Small --agents JSON stays inline."""
        agents = {
            "one_agent": AgentDefinition(
                description="A helper agent",
                prompt="Do stuff",
            )
        }
        transport = make_transport(agents=agents)
        cmd = transport._build_command()
        value = get_flag_value(cmd, "--agents")

        assert value is not None
        assert not value.startswith("@")
        assert len(transport._temp_files) == 0


class TestCombinedOverflow:
    """Test when both --agents and --system-prompt are large."""

    def test_both_agents_and_system_prompt_temp_filed(self):
        """Both large --agents and --system-prompt get temp-filed."""
        large_prompt = "A" * 10000
        agents = {
            f"agent_{i}": AgentDefinition(
                description=f"Agent {i} " * 300,
                prompt=f"Instructions " * 300,
            )
            for i in range(3)
        }
        transport = make_transport(system_prompt=large_prompt, agents=agents)
        cmd = transport._build_command()

        sp_value = get_flag_value(cmd, "--system-prompt")
        agents_value = get_flag_value(cmd, "--agents")

        # Both should be temp-filed
        assert sp_value.startswith("@"), "System prompt should be temp-filed"
        assert agents_value.startswith("@"), "Agents should be temp-filed"
        assert len(transport._temp_files) == 2

        # Command should now be short
        cmd_str = " ".join(cmd)
        assert len(cmd_str) < _CMD_LENGTH_LIMIT

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)


class TestAppendSystemPromptTempFiling:
    """Test --append-system-prompt gets temp-filed."""

    def test_large_append_system_prompt_temp_filed(self):
        """Large --append-system-prompt gets temp-filed."""
        large_append = "B" * (_CMD_LENGTH_LIMIT + 5000)
        transport = make_transport(append_system_prompt=large_append)
        cmd = transport._build_command()
        value = get_flag_value(cmd, "--append-system-prompt")

        assert value is not None
        assert value.startswith("@"), f"Expected @filepath, got: {value[:50]}..."

        filepath = value[1:]
        content = Path(filepath).read_text(encoding="utf-8")
        assert content == large_append

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)


class TestTempFileCleanup:
    """Test that temp files are tracked for cleanup."""

    def test_temp_files_tracked(self):
        """All created temp files are tracked in _temp_files list."""
        large_prompt = "C" * (_CMD_LENGTH_LIMIT + 5000)
        transport = make_transport(system_prompt=large_prompt)
        cmd = transport._build_command()

        assert len(transport._temp_files) >= 1
        for f in transport._temp_files:
            assert Path(f).exists(), f"Tracked temp file doesn't exist: {f}"

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)

    def test_temp_file_suffix_matches_flag(self):
        """Temp files use appropriate suffixes (.txt for prompts, .json for agents)."""
        large_prompt = "D" * (_CMD_LENGTH_LIMIT + 5000)
        transport = make_transport(system_prompt=large_prompt)
        transport._build_command()

        # System prompt should use .txt suffix
        assert any(f.endswith(".txt") for f in transport._temp_files)

        # Cleanup
        for f in transport._temp_files:
            Path(f).unlink(missing_ok=True)


class TestErrorMessage:
    """Test improved error message for command-line overflow."""

    def test_cmd_length_constant_on_windows(self):
        """Verify _CMD_LENGTH_LIMIT is 8000 on Windows."""
        if platform.system() == "Windows":
            assert _CMD_LENGTH_LIMIT == 8000
        else:
            assert _CMD_LENGTH_LIMIT == 100000

    def test_build_command_returns_valid_list(self):
        """_build_command always returns a list of strings."""
        transport = make_transport(system_prompt="hello")
        cmd = transport._build_command()

        assert isinstance(cmd, list)
        assert all(isinstance(x, str) for x in cmd)
        assert cmd[0] == "claude"
