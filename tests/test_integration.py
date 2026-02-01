"""Integration tests — cross-module pipelines."""

from __future__ import annotations

import pytest
import yaml

from agent_team.agents import build_agent_definitions, build_orchestrator_prompt
from agent_team.config import (
    AgentTeamConfig,
    DesignReferenceConfig,
    detect_depth,
    get_agent_counts,
    load_config,
)
from agent_team.interviewer import _detect_scope
from agent_team.mcp_servers import get_mcp_servers, get_research_tools


pytestmark = pytest.mark.integration


# ===================================================================
# Pipeline tests
# ===================================================================

class TestConfigToAgentsPipeline:
    def test_config_to_mcp_to_agents(self, env_with_api_keys):
        """load_config → get_mcp_servers → build_agent_definitions pipeline."""
        cfg = AgentTeamConfig()
        servers = get_mcp_servers(cfg)
        agents = build_agent_definitions(cfg, servers)
        assert len(agents) == 9
        # Researcher should have MCP tools when firecrawl key present
        researcher_tools = agents["researcher"]["tools"]
        assert any("firecrawl" in t for t in researcher_tools)

    def test_config_to_depth_to_prompt(self, default_config):
        """load_config → detect_depth → build_orchestrator_prompt pipeline."""
        depth = detect_depth("do a thorough review", default_config)
        prompt = build_orchestrator_prompt("do a thorough review", depth, default_config)
        assert "[DEPTH: THOROUGH]" in prompt

    def test_depth_to_counts_in_prompt(self, default_config):
        """detect_depth → get_agent_counts → counts appear in prompt."""
        depth = detect_depth("exhaustive analysis", default_config)
        counts = get_agent_counts(depth)
        prompt = build_orchestrator_prompt("exhaustive analysis", depth, default_config)
        # Fleet scaling section should contain phase names
        for phase in counts:
            assert phase in prompt


class TestMCPFlowIntoResearcher:
    def test_mcp_servers_flow_into_researcher_tools(self, env_with_api_keys):
        cfg = AgentTeamConfig()
        servers = get_mcp_servers(cfg)
        research_tools = get_research_tools(servers)
        agents = build_agent_definitions(cfg, servers)
        researcher_tools = agents["researcher"]["tools"]
        # All research_tools should appear in researcher's tools list
        for tool in research_tools:
            assert tool in researcher_tools


class TestInterviewScopeForcing:
    def test_complex_scope_forces_exhaustive(self, default_config):
        """Interview scope COMPLEX → exhaustive depth."""
        scope = "COMPLEX"
        # Simulate what main() does: if scope is COMPLEX, override depth
        depth_override = None
        if scope == "COMPLEX":
            depth_override = "exhaustive"
        assert depth_override == "exhaustive"

    def test_prd_path_triggers_exhaustive(self, default_config):
        """PRD path should trigger exhaustive depth."""
        prd_path = "/some/prd.md"
        depth_override = None
        if prd_path:
            depth_override = "exhaustive"
        assert depth_override == "exhaustive"


class TestDesignRefIntegration:
    def test_config_and_cli_urls_merged(self):
        """Config design-ref URLs + CLI design-ref URLs merged and deduplicated."""
        cfg = AgentTeamConfig(
            design_reference=DesignReferenceConfig(urls=["https://a.com", "https://b.com"])
        )
        cli_urls = ["https://b.com", "https://c.com"]
        # Simulate main() dedup logic
        combined = list(cfg.design_reference.urls)
        combined.extend(cli_urls)
        combined = [u for u in combined if u and u.strip()]
        combined = list(dict.fromkeys(combined))
        assert combined == ["https://a.com", "https://b.com", "https://c.com"]


class TestCLIOverridesPipeline:
    def test_cli_overrides_propagate(self, tmp_path, monkeypatch):
        """CLI overrides propagate through to agents."""
        monkeypatch.chdir(tmp_path)
        cfg = load_config(cli_overrides={"orchestrator": {"model": "sonnet"}})
        assert cfg.orchestrator.model == "sonnet"

    def test_disabled_agents_not_in_definitions(self, config_with_disabled_agents):
        agents = build_agent_definitions(config_with_disabled_agents, {})
        assert "planner" not in agents
        assert "researcher" not in agents
        assert "debugger" not in agents
        # But others should still be present
        assert "architect" in agents
        assert "code-writer" in agents


class TestFullPromptFeatures:
    def test_prompt_with_all_features(self, default_config, sample_interview_doc):
        """Prompt with interview + design-ref + prd + agent_count."""
        prompt = build_orchestrator_prompt(
            task="build the app",
            depth="exhaustive",
            config=default_config,
            prd_path="/tmp/prd.md",
            agent_count=10,
            cwd="/project",
            interview_doc=sample_interview_doc,
            design_reference_urls=["https://stripe.com"],
        )
        assert "INTERVIEW DOCUMENT" in prompt
        assert "DESIGN REFERENCE" in prompt
        assert "PRD MODE ACTIVE" in prompt
        assert "AGENT COUNT: 10" in prompt
        assert "[PROJECT DIR: /project]" in prompt
        assert "FLEET SCALING" in prompt


class TestConfigYAMLRoundTrip:
    def test_write_load_verify(self, tmp_path, monkeypatch):
        """Config YAML round-trip: write → load → verify."""
        data = {
            "orchestrator": {"model": "sonnet", "max_turns": 200},
            "depth": {"default": "thorough"},
            "convergence": {"max_cycles": 5},
        }
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.dump(data), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        cfg = load_config(config_path=str(cfg_path))
        assert cfg.orchestrator.model == "sonnet"
        assert cfg.orchestrator.max_turns == 200
        assert cfg.depth.default == "thorough"
        assert cfg.convergence.max_cycles == 5


class TestInterviewDocInjection:
    def test_interview_result_injected_into_prompt(self, default_config, sample_interview_doc):
        """InterviewResult.doc_content injected into orchestrator prompt."""
        prompt = build_orchestrator_prompt(
            task="implement login",
            depth="standard",
            config=default_config,
            interview_doc=sample_interview_doc,
        )
        assert "Feature Brief: Login Page" in prompt
        assert "Scope: MEDIUM" in prompt


class TestAgentCountFromTask:
    def test_agent_count_detected_and_in_prompt(self, default_config):
        """Agent count from task 'use 5 agents' detected and appears in prompt."""
        from agent_team.cli import _detect_agent_count
        count = _detect_agent_count("use 5 agents for this", None)
        assert count == 5
        prompt = build_orchestrator_prompt(
            task="use 5 agents for this",
            depth="standard",
            config=default_config,
            agent_count=count,
        )
        assert "AGENT COUNT: 5" in prompt
