"""Tests for agent_team.agents."""

from __future__ import annotations

from agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_REVIEWER_PROMPT,
    CODE_WRITER_PROMPT,
    DEBUGGER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    SECURITY_AUDITOR_PROMPT,
    TASK_ASSIGNER_PROMPT,
    TEST_RUNNER_PROMPT,
    build_agent_definitions,
    build_orchestrator_prompt,
)
from agent_team.config import AgentConfig, AgentTeamConfig


# ===================================================================
# Prompt constants
# ===================================================================

class TestPromptConstants:
    def test_orchestrator_prompt_non_empty(self):
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 100

    def test_planner_prompt_non_empty(self):
        assert len(PLANNER_PROMPT) > 100

    def test_researcher_prompt_non_empty(self):
        assert len(RESEARCHER_PROMPT) > 100

    def test_architect_prompt_non_empty(self):
        assert len(ARCHITECT_PROMPT) > 100

    def test_code_writer_prompt_non_empty(self):
        assert len(CODE_WRITER_PROMPT) > 100

    def test_code_reviewer_prompt_non_empty(self):
        assert len(CODE_REVIEWER_PROMPT) > 100

    def test_test_runner_prompt_non_empty(self):
        assert len(TEST_RUNNER_PROMPT) > 100

    def test_security_auditor_prompt_non_empty(self):
        assert len(SECURITY_AUDITOR_PROMPT) > 100

    def test_debugger_prompt_non_empty(self):
        assert len(DEBUGGER_PROMPT) > 100

    def test_task_assigner_prompt_non_empty(self):
        assert len(TASK_ASSIGNER_PROMPT) > 100

    def test_orchestrator_has_convergence_placeholders(self):
        assert "{escalation_threshold}" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "{max_escalation_depth}" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_section_headers(self):
        assert "SECTION 1:" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "SECTION 2:" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "SECTION 3:" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_planner_references_requirements(self):
        assert "REQUIREMENTS.md" in PLANNER_PROMPT

    def test_researcher_references_context7(self):
        assert "Context7" in RESEARCHER_PROMPT

    def test_researcher_references_firecrawl(self):
        assert "firecrawl" in RESEARCHER_PROMPT.lower()

    def test_architect_references_wiring_map(self):
        assert "Wiring Map" in ARCHITECT_PROMPT

    def test_reviewer_is_adversarial(self):
        assert "ADVERSARIAL" in CODE_REVIEWER_PROMPT

    def test_task_assigner_references_dag(self):
        assert "DAG" in TASK_ASSIGNER_PROMPT

    def test_debugger_references_wire(self):
        assert "WIRE-xxx" in DEBUGGER_PROMPT


# ===================================================================
# build_agent_definitions()
# ===================================================================

class TestBuildAgentDefinitions:
    def test_returns_9_agents(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert len(agents) == 9

    def test_agent_names_are_hyphenated(self, default_config):
        agents = build_agent_definitions(default_config, {})
        expected = {
            "planner", "researcher", "architect", "task-assigner",
            "code-writer", "code-reviewer", "test-runner",
            "security-auditor", "debugger",
        }
        assert set(agents.keys()) == expected

    def test_disabled_agent_excluded(self, config_with_disabled_agents):
        agents = build_agent_definitions(config_with_disabled_agents, {})
        assert "planner" not in agents
        assert "researcher" not in agents
        assert "debugger" not in agents

    def test_all_disabled_returns_empty(self):
        cfg = AgentTeamConfig()
        for name in cfg.agents:
            cfg.agents[name] = AgentConfig(enabled=False)
        agents = build_agent_definitions(cfg, {})
        assert agents == {}

    def test_researcher_includes_mcp_tools(self, default_config):
        servers = {"firecrawl": {"type": "stdio"}, "context7": {"type": "stdio"}}
        agents = build_agent_definitions(default_config, servers)
        researcher_tools = agents["researcher"]["tools"]
        # Should contain firecrawl and context7 tool names
        assert any("firecrawl" in t for t in researcher_tools)
        assert any("context7" in t for t in researcher_tools)

    def test_researcher_no_mcp_tools(self, default_config):
        agents = build_agent_definitions(default_config, {})
        researcher_tools = agents["researcher"]["tools"]
        assert not any("firecrawl" in t for t in researcher_tools)
        assert not any("context7" in t for t in researcher_tools)

    def test_all_agents_use_opus(self, default_config):
        agents = build_agent_definitions(default_config, {})
        for name, defn in agents.items():
            assert defn["model"] == "opus", f"{name} model should be opus"

    def test_planner_tools(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "Read" in agents["planner"]["tools"]
        assert "Write" in agents["planner"]["tools"]
        assert "Bash" in agents["planner"]["tools"]

    def test_each_agent_has_description_and_prompt(self, default_config):
        agents = build_agent_definitions(default_config, {})
        for name, defn in agents.items():
            assert "description" in defn, f"{name} missing description"
            assert "prompt" in defn, f"{name} missing prompt"
            assert len(defn["description"]) > 0
            assert len(defn["prompt"]) > 0

    def test_each_agent_has_tools(self, default_config):
        agents = build_agent_definitions(default_config, {})
        for name, defn in agents.items():
            assert "tools" in defn, f"{name} missing tools"
            assert len(defn["tools"]) > 0


# ===================================================================
# build_orchestrator_prompt()
# ===================================================================

class TestBuildOrchestratorPrompt:
    def test_contains_depth_label(self, default_config):
        prompt = build_orchestrator_prompt("fix bug", "thorough", default_config)
        assert "[DEPTH: THOROUGH]" in prompt

    def test_contains_task_text(self, default_config):
        prompt = build_orchestrator_prompt("fix the login bug", "standard", default_config)
        assert "fix the login bug" in prompt

    def test_contains_agent_count(self, default_config):
        prompt = build_orchestrator_prompt("task", "standard", default_config, agent_count=5)
        assert "AGENT COUNT: 5" in prompt

    def test_contains_prd_path(self, default_config):
        prompt = build_orchestrator_prompt("task", "exhaustive", default_config, prd_path="/tmp/prd.md")
        assert "PRD MODE ACTIVE" in prompt
        assert "/tmp/prd.md" in prompt

    def test_contains_cwd(self, default_config):
        prompt = build_orchestrator_prompt("task", "standard", default_config, cwd="/project")
        assert "[PROJECT DIR: /project]" in prompt

    def test_contains_interview_doc(self, default_config, sample_interview_doc):
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            interview_doc=sample_interview_doc,
        )
        assert "INTERVIEW DOCUMENT" in prompt
        assert "Feature Brief: Login Page" in prompt

    def test_contains_design_reference_urls(self, default_config):
        urls = ["https://stripe.com", "https://linear.app"]
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            design_reference_urls=urls,
        )
        assert "DESIGN REFERENCE" in prompt
        assert "https://stripe.com" in prompt
        assert "https://linear.app" in prompt

    def test_fleet_scaling_section(self, default_config):
        prompt = build_orchestrator_prompt("task", "standard", default_config)
        assert "FLEET SCALING" in prompt
        assert "planning:" in prompt
        assert "research:" in prompt
