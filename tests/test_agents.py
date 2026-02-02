"""Tests for agent_team.agents."""

from __future__ import annotations

from agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_REVIEWER_PROMPT,
    CODE_WRITER_PROMPT,
    CONTRACT_GENERATOR_PROMPT,
    DEBUGGER_PROMPT,
    INTEGRATION_AGENT_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    SECURITY_AUDITOR_PROMPT,
    TASK_ASSIGNER_PROMPT,
    TEST_RUNNER_PROMPT,
    build_agent_definitions,
    build_orchestrator_prompt,
)
from agent_team.config import AgentConfig, AgentTeamConfig, ConstraintEntry, SchedulerConfig, VerificationConfig


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
        assert "$escalation_threshold" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "$max_escalation_depth" in ORCHESTRATOR_SYSTEM_PROMPT

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

    def test_integration_agent_prompt_non_empty(self):
        assert len(INTEGRATION_AGENT_PROMPT) > 100

    def test_contract_generator_prompt_non_empty(self):
        assert len(CONTRACT_GENERATOR_PROMPT) > 100

    def test_orchestrator_has_section_0(self):
        assert "SECTION 0:" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_section_3c(self):
        assert "SECTION 3c:" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_section_3d(self):
        assert "SECTION 3d:" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_planner_has_codebase_map_awareness(self):
        assert "codebase map" in PLANNER_PROMPT.lower()

    def test_architect_has_contract_awareness(self):
        assert "contract" in ARCHITECT_PROMPT.lower()

    def test_task_assigner_has_scheduler_awareness(self):
        assert "scheduler" in TASK_ASSIGNER_PROMPT.lower()

    def test_code_writer_has_integration_declarations(self):
        assert "Integration Declarations" in CODE_WRITER_PROMPT

    def test_code_reviewer_has_verification_awareness(self):
        assert "VERIFICATION.md" in CODE_REVIEWER_PROMPT

    def test_orchestrator_has_contract_generator_step(self):
        assert "CONTRACT GENERATOR" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_convergence_gates(self):
        assert "GATE 1" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "GATE 2" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "GATE 3" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "GATE 4" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_section_8(self):
        assert "SECTION 8" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_constraint_enforcement(self):
        assert "CONSTRAINT ENFORCEMENT" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_intervention_awareness(self):
        assert "USER INTERVENTION" in ORCHESTRATOR_SYSTEM_PROMPT or "INTERVENTION" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_code_reviewer_has_review_authority(self):
        assert "ONLY" in CODE_REVIEWER_PROMPT
        assert "authorized" in CODE_REVIEWER_PROMPT

    def test_debugger_has_review_boundary(self):
        assert "CANNOT" in DEBUGGER_PROMPT
        assert "mark" in DEBUGGER_PROMPT.lower()


# ===================================================================
# build_agent_definitions()
# ===================================================================

class TestBuildAgentDefinitions:
    def test_returns_9_agents_default(self, default_config):
        """Default config (scheduler/verification disabled) returns 9 agents."""
        agents = build_agent_definitions(default_config, {})
        assert len(agents) == 9

    def test_returns_10_agents_with_scheduler(self):
        cfg = AgentTeamConfig(scheduler=SchedulerConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 10
        assert "integration-agent" in agents

    def test_returns_10_agents_with_verification(self):
        cfg = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 10
        assert "contract-generator" in agents

    def test_returns_11_agents_with_both(self, full_config_with_new_features):
        agents = build_agent_definitions(full_config_with_new_features, {})
        assert len(agents) == 11
        assert "integration-agent" in agents
        assert "contract-generator" in agents

    def test_integration_agent_not_present_by_default(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "integration-agent" not in agents

    def test_contract_generator_not_present_by_default(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "contract-generator" not in agents

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

class TestAgentNamingConsistency:
    """Tests for Finding #17: config keys map to hyphenated SDK names."""

    def test_all_config_keys_produce_sdk_names(self):
        """Every default config agent key should produce an agent in the output."""
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        # All 9 default agents should be present
        expected_sdk_names = {
            "planner", "researcher", "architect", "task-assigner",
            "code-writer", "code-reviewer", "test-runner",
            "security-auditor", "debugger",
        }
        assert expected_sdk_names.issubset(set(agents.keys()))

    def test_underscore_to_hyphen_mapping(self):
        """Config keys with underscores produce hyphenated SDK names."""
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        # Verify specific underscore->hyphen mappings
        assert "task-assigner" in agents  # from config key "task_assigner"
        assert "code-writer" in agents     # from config key "code_writer"
        assert "code-reviewer" in agents   # from config key "code_reviewer"
        assert "test-runner" in agents     # from config key "test_runner"
        assert "security-auditor" in agents  # from config key "security_auditor"

    def test_no_underscore_names_in_output(self):
        """SDK agent names should never contain underscores."""
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        for name in agents.keys():
            assert "_" not in name, f"Agent name '{name}' contains underscore"


class TestPerAgentModelConfig:
    """Tests for Finding #4: per-agent model configuration."""

    def test_custom_model_propagates(self):
        """Config with planner.model = 'sonnet' should produce a planner with model 'sonnet'."""
        cfg = AgentTeamConfig()
        cfg.agents["planner"] = AgentConfig(model="sonnet")
        agents = build_agent_definitions(cfg, {})
        assert agents["planner"]["model"] == "sonnet"

    def test_default_model_is_opus(self):
        """Default config should produce agents with model 'opus'."""
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        assert agents["planner"]["model"] == "opus"
        assert agents["code-writer"]["model"] == "opus"

    def test_each_agent_respects_own_model(self):
        """Each agent reads its own model config, not a global one."""
        cfg = AgentTeamConfig()
        cfg.agents["code_writer"] = AgentConfig(model="haiku")
        cfg.agents["researcher"] = AgentConfig(model="sonnet")
        agents = build_agent_definitions(cfg, {})
        assert agents["code-writer"]["model"] == "haiku"
        assert agents["researcher"]["model"] == "sonnet"
        assert agents["planner"]["model"] == "opus"  # unchanged


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

    def test_contains_codebase_map_summary(self, default_config):
        summary = "## Codebase Map\n- 50 files\n- Python primary"
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            codebase_map_summary=summary,
        )
        assert "CODEBASE MAP" in prompt
        assert "50 files" in prompt

    def test_no_codebase_map_when_none(self, default_config):
        prompt = build_orchestrator_prompt("task", "standard", default_config)
        assert "CODEBASE MAP" not in prompt or "SECTION 0" not in prompt

    def test_fleet_scaling_section(self, default_config):
        prompt = build_orchestrator_prompt("task", "standard", default_config)
        assert "FLEET SCALING" in prompt
        assert "planning:" in prompt
        assert "research:" in prompt

    # --- COMPLEX interview → PRD mode tests ---

    def test_complex_interview_activates_prd_mode(self, default_config, sample_complex_interview_doc):
        """COMPLEX interview_scope + interview_doc → PRD MODE ACTIVE with INTERVIEW.md path."""
        prompt = build_orchestrator_prompt(
            "task", "exhaustive", default_config,
            interview_doc=sample_complex_interview_doc,
            interview_scope="COMPLEX",
        )
        assert "PRD MODE ACTIVE" in prompt
        assert "INTERVIEW.md" in prompt
        assert "already injected inline" in prompt

    def test_complex_interview_prd_instructions(self, default_config, sample_complex_interview_doc):
        """COMPLEX scope → PRD-specific instructions (analyzer fleet, MASTER_PLAN.md)."""
        prompt = build_orchestrator_prompt(
            "task", "exhaustive", default_config,
            interview_doc=sample_complex_interview_doc,
            interview_scope="COMPLEX",
        )
        assert "PRD ANALYZER FLEET" in prompt
        assert "MASTER_PLAN.md" in prompt
        assert "per-milestone REQUIREMENTS.md" in prompt
        # Should NOT contain standard planner instructions
        assert "PLANNING FLEET to create REQUIREMENTS.md" not in prompt

    def test_medium_interview_no_prd_mode(self, default_config, sample_interview_doc):
        """MEDIUM scope → no PRD mode activation."""
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            interview_doc=sample_interview_doc,
            interview_scope="MEDIUM",
        )
        assert "PRD MODE ACTIVE" not in prompt
        assert "PLANNING FLEET to create REQUIREMENTS.md" in prompt

    def test_prd_path_takes_precedence(self, default_config, sample_complex_interview_doc):
        """prd_path + COMPLEX → only prd_path PRD MODE marker, not interview-based one."""
        prompt = build_orchestrator_prompt(
            "task", "exhaustive", default_config,
            prd_path="/tmp/spec.md",
            interview_doc=sample_complex_interview_doc,
            interview_scope="COMPLEX",
        )
        # prd_path marker should be present
        assert "/tmp/spec.md" in prompt
        # Interview-based PRD MODE should NOT be present (guard: not prd_path)
        assert "already injected inline" not in prompt
        # PRD instructions should still activate (is_prd_mode is True from prd_path)
        assert "PRD ANALYZER FLEET" in prompt

    def test_no_scope_no_prd_mode(self, default_config, sample_interview_doc):
        """No interview_scope → no PRD mode even with interview_doc."""
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            interview_doc=sample_interview_doc,
        )
        assert "PRD MODE ACTIVE" not in prompt
        assert "PLANNING FLEET to create REQUIREMENTS.md" in prompt


# ===================================================================
# Template substitution (Finding #20)
# ===================================================================

class TestTemplateSubstitution:
    """Tests for Finding #20: template variable safety."""

    def test_template_variables_substituted(self):
        """Template variables in orchestrator prompt should be substituted correctly."""
        import string
        prompt = string.Template(ORCHESTRATOR_SYSTEM_PROMPT).safe_substitute(
            escalation_threshold="3",
            max_escalation_depth="2",
        )
        assert "$escalation_threshold" not in prompt
        assert "$max_escalation_depth" not in prompt
        assert "3" in prompt  # the substituted value
        assert "2" in prompt

    def test_safe_substitute_leaves_unknown_vars(self):
        """safe_substitute should not crash on unknown template variables."""
        import string
        prompt = string.Template(ORCHESTRATOR_SYSTEM_PROMPT).safe_substitute(
            escalation_threshold="5",
            # deliberately missing max_escalation_depth
        )
        # Should not raise, just leave $max_escalation_depth as-is
        assert "$max_escalation_depth" in prompt

    def test_no_curly_brace_template_vars(self):
        """Prompt should not contain {variable} style templates."""
        assert "{escalation_threshold}" not in ORCHESTRATOR_SYSTEM_PROMPT
        assert "{max_escalation_depth}" not in ORCHESTRATOR_SYSTEM_PROMPT


# ===================================================================
# Constraint injection
# ===================================================================

class TestConstraintInjection:
    """Tests for constraint injection into agent prompts."""

    def test_constraints_appear_in_agent_prompts(self, default_config):
        constraints = [ConstraintEntry("no library swaps", "prohibition", "task", 2)]
        agents = build_agent_definitions(default_config, {}, constraints=constraints)
        for name, defn in agents.items():
            assert "no library swaps" in defn["prompt"], f"{name} missing constraint"

    def test_none_constraints_no_change(self, default_config):
        agents_without = build_agent_definitions(default_config, {})
        agents_with_none = build_agent_definitions(default_config, {}, constraints=None)
        for name in agents_without:
            assert agents_without[name]["prompt"] == agents_with_none[name]["prompt"]

    def test_empty_constraints_no_change(self, default_config):
        agents_without = build_agent_definitions(default_config, {})
        agents_with_empty = build_agent_definitions(default_config, {}, constraints=[])
        for name in agents_without:
            assert agents_without[name]["prompt"] == agents_with_empty[name]["prompt"]

    def test_constraint_block_format(self):
        constraints = [ConstraintEntry("no changes", "prohibition", "task", 2)]
        agents = build_agent_definitions(AgentTeamConfig(), {}, constraints=constraints)
        # Check that the constraint block header is present
        for name, defn in agents.items():
            assert "USER CONSTRAINTS" in defn["prompt"]

    def test_constraints_in_orchestrator_prompt(self, default_config):
        constraints = [ConstraintEntry("only restyle SCSS", "scope", "task", 1)]
        prompt = build_orchestrator_prompt(
            "restyle the app", "thorough", default_config,
            constraints=constraints,
        )
        assert "only restyle SCSS" in prompt


# ===================================================================
# Convergence gates
# ===================================================================

class TestConvergenceGates:
    """Tests for convergence gate content in prompts."""

    def test_gate_1_review_authority(self):
        assert "REVIEW" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "GATE 1" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_gate_2_mandatory_re_review(self):
        assert "GATE 2" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "Re-Review" in ORCHESTRATOR_SYSTEM_PROMPT or "re-review" in ORCHESTRATOR_SYSTEM_PROMPT.lower()

    def test_gate_3_cycle_reporting(self):
        assert "GATE 3" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_gate_4_depth_thoroughness(self):
        assert "GATE 4" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_reviewer_exclusive_authority(self):
        assert "ONLY" in CODE_REVIEWER_PROMPT
        assert "[x]" in CODE_REVIEWER_PROMPT

    def test_debugger_cannot_mark(self):
        assert "CANNOT" in DEBUGGER_PROMPT
        assert "code-reviewer" in DEBUGGER_PROMPT.lower() or "reviewer" in DEBUGGER_PROMPT.lower()

    def test_orchestrator_has_show_fleet_composition_placeholder(self):
        assert "$show_fleet_composition" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_show_convergence_status_placeholder(self):
        assert "$show_convergence_status" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_max_cycles_placeholder(self):
        assert "$max_cycles" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_master_plan_file_placeholder(self):
        assert "$master_plan_file" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_max_budget_placeholder(self):
        assert "$max_budget_usd" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_section_6b(self):
        assert "SECTION 6b:" in ORCHESTRATOR_SYSTEM_PROMPT


# ===================================================================
# build_orchestrator_prompt depth handling
# ===================================================================

class TestBuildOrchestratorPromptDepthHandling:
    """Test that build_orchestrator_prompt handles both str and DepthDetection."""

    def test_string_depth_works(self, default_config):
        prompt = build_orchestrator_prompt("test", "thorough", default_config)
        assert "[DEPTH: THOROUGH]" in prompt

    def test_depth_detection_works(self, default_config):
        from agent_team.config import DepthDetection
        det = DepthDetection("exhaustive", "keyword", ["exhaustive"], "test")
        prompt = build_orchestrator_prompt("test", det, default_config)
        assert "[DEPTH: EXHAUSTIVE]" in prompt

    def test_constraints_param_default_none(self, default_config):
        # Should work without constraints parameter
        prompt = build_orchestrator_prompt("test", "standard", default_config)
        assert "[DEPTH: STANDARD]" in prompt
