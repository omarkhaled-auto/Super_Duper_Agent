"""Shared fixtures and pytest plugins for Agent Team tests."""

from __future__ import annotations

import pytest
import yaml

from agent_team.config import (
    AgentConfig,
    AgentTeamConfig,
    ConvergenceConfig,
    DepthConfig,
    DesignReferenceConfig,
    DisplayConfig,
    InterviewConfig,
    MCPServerConfig,
    OrchestratorConfig,
)


# ---------------------------------------------------------------------------
# pytest CLI flag: --run-e2e
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests that require real API keys",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if config.getoption("--run-e2e"):
        return
    skip_e2e = pytest.mark.skip(reason="need --run-e2e flag to run")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def default_config() -> AgentTeamConfig:
    """AgentTeamConfig with all defaults."""
    return AgentTeamConfig()


@pytest.fixture()
def custom_config() -> AgentTeamConfig:
    """Non-default config values."""
    return AgentTeamConfig(
        orchestrator=OrchestratorConfig(model="sonnet", max_turns=100),
        depth=DepthConfig(default="thorough"),
        convergence=ConvergenceConfig(max_cycles=5, escalation_threshold=2),
    )


@pytest.fixture()
def config_with_disabled_agents() -> AgentTeamConfig:
    """Config with planner, researcher, and debugger disabled."""
    cfg = AgentTeamConfig()
    cfg.agents["planner"] = AgentConfig(enabled=False)
    cfg.agents["researcher"] = AgentConfig(enabled=False)
    cfg.agents["debugger"] = AgentConfig(enabled=False)
    return cfg


@pytest.fixture()
def config_with_disabled_mcp() -> AgentTeamConfig:
    """Config with firecrawl and context7 disabled."""
    cfg = AgentTeamConfig()
    cfg.mcp_servers["firecrawl"] = MCPServerConfig(enabled=False)
    cfg.mcp_servers["context7"] = MCPServerConfig(enabled=False)
    return cfg


@pytest.fixture()
def config_yaml_file(tmp_path):
    """Write a valid YAML config file and return its path."""
    data = {
        "orchestrator": {"model": "sonnet", "max_turns": 200},
        "depth": {"default": "thorough"},
        "display": {"verbose": True},
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


@pytest.fixture()
def malformed_yaml_file(tmp_path):
    """Write an invalid YAML file and return its path."""
    p = tmp_path / "bad.yaml"
    p.write_text("key: [unterminated", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Interview / PRD fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_interview_doc() -> str:
    """Interview document string with Scope: MEDIUM."""
    return (
        "# Feature Brief: Login Page\n"
        "Scope: MEDIUM\n"
        "Date: 2025-01-01\n\n"
        "## Objective\nBuild a login page.\n"
    )


@pytest.fixture()
def sample_complex_interview_doc() -> str:
    """Interview document string with Scope: COMPLEX."""
    return (
        "# PRD: Full SaaS App\n"
        "Scope: COMPLEX\n"
        "Date: 2025-01-01\n\n"
        "## Executive Summary\nBuild a SaaS application.\n"
    )


@pytest.fixture()
def sample_prd_file(tmp_path):
    """Create a PRD file on disk and return its path."""
    p = tmp_path / "prd.md"
    p.write_text(
        "# PRD: My App\n\n## Features\n- Feature 1\n- Feature 2\n\n"
        "## User Stories\n- As a user I want to login\n",
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Environment fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_with_api_keys(monkeypatch):
    """Set both API keys in the environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic-key")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-firecrawl-key")


@pytest.fixture()
def env_without_api_keys(monkeypatch):
    """Remove both API keys from the environment."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)


@pytest.fixture()
def env_with_anthropic_only(monkeypatch):
    """Set only ANTHROPIC_API_KEY."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic-key")
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
