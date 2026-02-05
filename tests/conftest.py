"""Shared fixtures and pytest plugins for Agent Team tests."""

from __future__ import annotations

import pytest
import yaml

from agent_team.config import (
    AgentConfig,
    AgentTeamConfig,
    CodebaseMapConfig,
    MCPServerConfig,
    MilestoneConfig,
    SchedulerConfig,
    VerificationConfig,
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
def env_with_anthropic_only(monkeypatch):
    """Set only ANTHROPIC_API_KEY."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic-key")
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)


@pytest.fixture()
def full_config_with_new_features() -> AgentTeamConfig:
    """AgentTeamConfig with all new features enabled."""
    return AgentTeamConfig(
        codebase_map=CodebaseMapConfig(enabled=True),
        scheduler=SchedulerConfig(enabled=True),
        verification=VerificationConfig(enabled=True),
    )


@pytest.fixture()
def config_with_milestones() -> AgentTeamConfig:
    """AgentTeamConfig with milestone orchestration enabled."""
    return AgentTeamConfig(
        milestone=MilestoneConfig(enabled=True),
        codebase_map=CodebaseMapConfig(enabled=True),
        scheduler=SchedulerConfig(enabled=True),
        verification=VerificationConfig(enabled=True),
    )


# ---------------------------------------------------------------------------
# Milestone project structure fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def milestone_project_structure(tmp_path):
    """Create a temporary milestone project structure with sample REQUIREMENTS.md files.

    Returns (project_root, milestones_dir) tuple.
    """
    agent_team_dir = tmp_path / ".agent-team"
    milestones_dir = agent_team_dir / "milestones"

    # Milestone 1: 10 requirements, 5 checked, 2 review cycles
    m1_dir = milestones_dir / "milestone-1"
    m1_dir.mkdir(parents=True)
    m1_req = (
        "# Requirements: Foundation\n\n"
        "- [x] Set up project structure (review_cycles: 2)\n"
        "- [x] Configure TypeScript (review_cycles: 2)\n"
        "- [x] Set up testing framework (review_cycles: 2)\n"
        "- [x] Configure linting (review_cycles: 1)\n"
        "- [x] Set up CI/CD pipeline (review_cycles: 1)\n"
        "- [ ] Configure deployment (review_cycles: 1)\n"
        "- [ ] Set up monitoring (review_cycles: 0)\n"
        "- [ ] Add logging framework (review_cycles: 0)\n"
        "- [ ] Set up error tracking\n"
        "- [ ] Configure environment variables\n"
    )
    (m1_dir / "REQUIREMENTS.md").write_text(m1_req, encoding="utf-8")

    # Milestone 2: 5 requirements, 3 checked, 3 review cycles
    m2_dir = milestones_dir / "milestone-2"
    m2_dir.mkdir(parents=True)
    m2_req = (
        "# Requirements: Backend API\n\n"
        "- [x] Design REST API endpoints (review_cycles: 3)\n"
        "- [x] Implement user authentication (review_cycles: 3)\n"
        "- [x] Create database schema (review_cycles: 2)\n"
        "- [ ] Add input validation (review_cycles: 1)\n"
        "- [ ] Implement rate limiting\n"
    )
    (m2_dir / "REQUIREMENTS.md").write_text(m2_req, encoding="utf-8")

    return tmp_path, milestones_dir


@pytest.fixture()
def prd_mode_config() -> AgentTeamConfig:
    """AgentTeamConfig with milestone.enabled=True for PRD mode testing."""
    return AgentTeamConfig(
        milestone=MilestoneConfig(enabled=True),
    )
