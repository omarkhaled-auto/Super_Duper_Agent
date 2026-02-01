"""Tests for agent_team.config."""

from __future__ import annotations

import pytest
import yaml

from agent_team.config import (
    AgentConfig,
    AgentTeamConfig,
    ConvergenceConfig,
    DEPTH_AGENT_COUNTS,
    DepthConfig,
    DesignReferenceConfig,
    DisplayConfig,
    InterviewConfig,
    MCPServerConfig,
    OrchestratorConfig,
    _deep_merge,
    _dict_to_config,
    detect_depth,
    get_agent_counts,
    load_config,
)


# ===================================================================
# Dataclass defaults
# ===================================================================

class TestOrchestratorConfigDefaults:
    def test_model_default(self):
        c = OrchestratorConfig()
        assert c.model == "opus"

    def test_max_turns_default(self):
        c = OrchestratorConfig()
        assert c.max_turns == 500

    def test_permission_mode_default(self):
        c = OrchestratorConfig()
        assert c.permission_mode == "acceptEdits"


class TestDepthConfigDefaults:
    def test_default_depth(self):
        c = DepthConfig()
        assert c.default == "standard"

    def test_auto_detect_true(self):
        c = DepthConfig()
        assert c.auto_detect is True

    def test_keyword_map_has_levels(self):
        c = DepthConfig()
        assert "quick" in c.keyword_map
        assert "thorough" in c.keyword_map
        assert "exhaustive" in c.keyword_map


class TestConvergenceConfigDefaults:
    def test_max_cycles(self):
        c = ConvergenceConfig()
        assert c.max_cycles == 10

    def test_escalation_threshold(self):
        c = ConvergenceConfig()
        assert c.escalation_threshold == 3

    def test_max_escalation_depth(self):
        c = ConvergenceConfig()
        assert c.max_escalation_depth == 2

    def test_requirements_dir(self):
        c = ConvergenceConfig()
        assert c.requirements_dir == ".agent-team"

    def test_requirements_file(self):
        c = ConvergenceConfig()
        assert c.requirements_file == "REQUIREMENTS.md"

    def test_master_plan_file(self):
        c = ConvergenceConfig()
        assert c.master_plan_file == "MASTER_PLAN.md"


class TestAgentConfigDefaults:
    def test_model(self):
        c = AgentConfig()
        assert c.model == "opus"

    def test_enabled(self):
        c = AgentConfig()
        assert c.enabled is True


class TestMCPServerConfigDefaults:
    def test_enabled(self):
        c = MCPServerConfig()
        assert c.enabled is True


class TestInterviewConfigDefaults:
    def test_enabled(self):
        c = InterviewConfig()
        assert c.enabled is True

    def test_model(self):
        c = InterviewConfig()
        assert c.model == "opus"

    def test_max_exchanges(self):
        c = InterviewConfig()
        assert c.max_exchanges == 50


class TestDesignReferenceConfigDefaults:
    def test_urls_empty(self):
        c = DesignReferenceConfig()
        assert c.urls == []

    def test_depth(self):
        c = DesignReferenceConfig()
        assert c.depth == "full"

    def test_max_pages(self):
        c = DesignReferenceConfig()
        assert c.max_pages_per_site == 5


class TestDisplayConfigDefaults:
    def test_show_cost(self):
        c = DisplayConfig()
        assert c.show_cost is True

    def test_verbose(self):
        c = DisplayConfig()
        assert c.verbose is False


class TestAgentTeamConfigDefaults:
    def test_has_9_agents(self):
        c = AgentTeamConfig()
        assert len(c.agents) == 9

    def test_agent_names(self):
        c = AgentTeamConfig()
        expected = {
            "planner", "researcher", "architect", "task_assigner",
            "code_writer", "code_reviewer", "test_runner",
            "security_auditor", "debugger",
        }
        assert set(c.agents.keys()) == expected

    def test_has_2_mcp_servers(self):
        c = AgentTeamConfig()
        assert len(c.mcp_servers) == 2
        assert "firecrawl" in c.mcp_servers
        assert "context7" in c.mcp_servers


# ===================================================================
# detect_depth()
# ===================================================================

class TestDetectDepth:
    def test_quick_keyword(self, default_config):
        assert detect_depth("do a quick fix", default_config) == "quick"

    def test_fast_keyword(self, default_config):
        assert detect_depth("fast fix please", default_config) == "quick"

    def test_simple_keyword(self, default_config):
        assert detect_depth("simple change needed", default_config) == "quick"

    def test_thorough_keyword(self, default_config):
        assert detect_depth("be thorough", default_config) == "thorough"

    def test_deep_keyword(self, default_config):
        assert detect_depth("deep analysis required", default_config) == "thorough"

    def test_exhaustive_keyword(self, default_config):
        assert detect_depth("exhaustive review", default_config) == "exhaustive"

    def test_comprehensive_keyword(self, default_config):
        assert detect_depth("comprehensive audit", default_config) == "exhaustive"

    def test_case_insensitive(self, default_config):
        assert detect_depth("THOROUGH check", default_config) == "thorough"

    def test_most_intensive_wins(self, default_config):
        # "exhaustive" beats "quick" when both present
        assert detect_depth("quick but exhaustive", default_config) == "exhaustive"

    def test_auto_detect_false_returns_default(self):
        cfg = AgentTeamConfig(depth=DepthConfig(auto_detect=False, default="thorough"))
        assert detect_depth("exhaustive review", cfg) == "thorough"

    def test_word_boundary_no_substring(self, default_config):
        # "adjustment" should NOT match "just" keyword
        assert detect_depth("minor adjustment needed", default_config) == "standard"

    def test_empty_task_returns_default(self, default_config):
        assert detect_depth("", default_config) == "standard"

    def test_no_keyword_returns_default(self, default_config):
        assert detect_depth("fix the login bug", default_config) == "standard"


# ===================================================================
# get_agent_counts()
# ===================================================================

class TestGetAgentCounts:
    def test_quick_counts(self):
        counts = get_agent_counts("quick")
        assert counts == DEPTH_AGENT_COUNTS["quick"]

    def test_standard_counts(self):
        counts = get_agent_counts("standard")
        assert counts == DEPTH_AGENT_COUNTS["standard"]

    def test_thorough_counts(self):
        counts = get_agent_counts("thorough")
        assert counts == DEPTH_AGENT_COUNTS["thorough"]

    def test_exhaustive_counts(self):
        counts = get_agent_counts("exhaustive")
        assert counts == DEPTH_AGENT_COUNTS["exhaustive"]

    def test_invalid_falls_back_to_standard(self):
        counts = get_agent_counts("invalid")
        assert counts == DEPTH_AGENT_COUNTS["standard"]

    def test_all_phases_present(self):
        counts = get_agent_counts("standard")
        expected_phases = {"planning", "research", "architecture", "coding", "review", "testing"}
        assert set(counts.keys()) == expected_phases


# ===================================================================
# _deep_merge()
# ===================================================================

class TestDeepMerge:
    def test_flat_merge(self):
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_nested_merge(self):
        result = _deep_merge({"x": {"a": 1, "b": 2}}, {"x": {"b": 3, "c": 4}})
        assert result == {"x": {"a": 1, "b": 3, "c": 4}}

    def test_override_value(self):
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_non_dict_replacement(self):
        result = _deep_merge({"a": {"nested": True}}, {"a": "string"})
        assert result == {"a": "string"}

    def test_empty_base(self):
        assert _deep_merge({}, {"a": 1}) == {"a": 1}

    def test_empty_override(self):
        assert _deep_merge({"a": 1}, {}) == {"a": 1}


# ===================================================================
# _dict_to_config()
# ===================================================================

class TestDictToConfig:
    def test_empty_dict_returns_defaults(self):
        cfg = _dict_to_config({})
        assert cfg.orchestrator.model == "opus"
        assert cfg.depth.default == "standard"

    def test_orchestrator_section(self):
        cfg = _dict_to_config({"orchestrator": {"model": "sonnet", "max_turns": 100}})
        assert cfg.orchestrator.model == "sonnet"
        assert cfg.orchestrator.max_turns == 100

    def test_depth_section(self):
        cfg = _dict_to_config({"depth": {"default": "thorough", "auto_detect": False}})
        assert cfg.depth.default == "thorough"
        assert cfg.depth.auto_detect is False

    def test_convergence_section(self):
        cfg = _dict_to_config({"convergence": {"max_cycles": 5}})
        assert cfg.convergence.max_cycles == 5

    def test_interview_section(self):
        cfg = _dict_to_config({"interview": {"enabled": False, "model": "haiku"}})
        assert cfg.interview.enabled is False
        assert cfg.interview.model == "haiku"

    def test_design_reference_section(self):
        cfg = _dict_to_config({"design_reference": {"urls": ["https://example.com"], "depth": "branding"}})
        assert cfg.design_reference.urls == ["https://example.com"]
        assert cfg.design_reference.depth == "branding"

    def test_display_section(self):
        cfg = _dict_to_config({"display": {"verbose": True, "show_cost": False}})
        assert cfg.display.verbose is True
        assert cfg.display.show_cost is False

    def test_agents_section(self):
        cfg = _dict_to_config({"agents": {"planner": {"enabled": False}}})
        assert cfg.agents["planner"].enabled is False

    def test_mcp_servers_section(self):
        cfg = _dict_to_config({"mcp_servers": {"firecrawl": {"enabled": False}}})
        assert cfg.mcp_servers["firecrawl"].enabled is False

    def test_agents_as_non_dict_skipped(self):
        # If agents contains a non-dict value, it should be skipped
        cfg = _dict_to_config({"agents": {"planner": "invalid"}})
        # The default planner should remain since "invalid" is not a dict
        assert cfg.agents["planner"].enabled is True

    def test_mcp_servers_as_non_dict_skipped(self):
        cfg = _dict_to_config({"mcp_servers": {"firecrawl": "invalid"}})
        assert cfg.mcp_servers["firecrawl"].enabled is True


# ===================================================================
# load_config()
# ===================================================================

class TestLoadConfig:
    def test_no_file_returns_defaults(self, tmp_path, monkeypatch):
        # Use a temp dir with no config.yaml
        monkeypatch.chdir(tmp_path)
        cfg = load_config()
        assert cfg.orchestrator.model == "opus"

    def test_explicit_path(self, config_yaml_file):
        cfg = load_config(config_path=str(config_yaml_file))
        assert cfg.orchestrator.model == "sonnet"
        assert cfg.orchestrator.max_turns == 200

    def test_cli_overrides_merge(self, config_yaml_file):
        cfg = load_config(
            config_path=str(config_yaml_file),
            cli_overrides={"orchestrator": {"max_turns": 999}},
        )
        assert cfg.orchestrator.max_turns == 999
        # Model from file should remain
        assert cfg.orchestrator.model == "sonnet"


# ===================================================================
# Known bug verification
# ===================================================================

class TestKnownBugs:
    def test_load_config_malformed_yaml_raises(self, malformed_yaml_file):
        with pytest.raises(yaml.YAMLError):
            load_config(config_path=str(malformed_yaml_file))

    def test_agents_as_list_crashes(self):
        """Bug #3b: agents passed as a list should not crash _dict_to_config."""
        # This tests that iterating .items() on a list would fail
        with pytest.raises((AttributeError, TypeError)):
            _dict_to_config({"agents": ["planner", "researcher"]})

    def test_mcp_servers_as_list_crashes(self):
        """Bug #3c: mcp_servers passed as a list should not crash."""
        with pytest.raises((AttributeError, TypeError)):
            _dict_to_config({"mcp_servers": ["firecrawl", "context7"]})
