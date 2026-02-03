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
    SPEC_VALIDATOR_PROMPT,
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
    def test_returns_12_agents_default(self, default_config):
        """Default config (scheduler+verification enabled) returns 12 agents."""
        agents = build_agent_definitions(default_config, {})
        assert len(agents) == 12

    def test_returns_11_without_scheduler(self):
        """Disabling scheduler removes integration-agent: 11 agents."""
        cfg = AgentTeamConfig(scheduler=SchedulerConfig(enabled=False))
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 11
        assert "integration-agent" not in agents

    def test_returns_11_without_verification(self):
        """Disabling verification removes contract-generator: 11 agents."""
        cfg = AgentTeamConfig(verification=VerificationConfig(enabled=False))
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 11
        assert "contract-generator" not in agents

    def test_returns_12_agents_with_both(self, full_config_with_new_features):
        """All features enabled returns 12 agents (includes spec-validator)."""
        agents = build_agent_definitions(full_config_with_new_features, {})
        assert len(agents) == 12
        assert "integration-agent" in agents
        assert "contract-generator" in agents
        assert "spec-validator" in agents

    def test_integration_agent_present_by_default(self, default_config):
        """Scheduler enabled by default → integration-agent present."""
        agents = build_agent_definitions(default_config, {})
        assert "integration-agent" in agents

    def test_contract_generator_present_by_default(self, default_config):
        """Verification enabled by default → contract-generator present."""
        agents = build_agent_definitions(default_config, {})
        assert "contract-generator" in agents

    def test_agent_names_are_hyphenated(self, default_config):
        agents = build_agent_definitions(default_config, {})
        expected = {
            "planner", "researcher", "architect", "task-assigner",
            "code-writer", "code-reviewer", "test-runner",
            "security-auditor", "debugger",
            "integration-agent", "contract-generator", "spec-validator",
        }
        assert set(agents.keys()) == expected

    def test_disabled_agent_excluded(self, config_with_disabled_agents):
        agents = build_agent_definitions(config_with_disabled_agents, {})
        assert "planner" not in agents
        assert "researcher" not in agents
        assert "debugger" not in agents

    def test_all_disabled_returns_spec_validator_only(self):
        """spec-validator is always present even when all config agents disabled."""
        cfg = AgentTeamConfig()
        for name in cfg.agents:
            cfg.agents[name] = AgentConfig(enabled=False)
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 1
        assert "spec-validator" in agents

    def test_researcher_no_mcp_tools_even_with_servers(self, default_config):
        """MCP tools are NOT in researcher — orchestrator calls them directly."""
        servers = {"firecrawl": {"type": "stdio"}, "context7": {"type": "stdio"}}
        agents = build_agent_definitions(default_config, servers)
        researcher_tools = agents["researcher"]["tools"]
        # MCP servers aren't propagated to sub-agents, so researcher
        # should NOT have firecrawl or context7 tool names.
        assert not any("firecrawl" in t for t in researcher_tools)
        assert not any("context7" in t for t in researcher_tools)

    def test_researcher_has_web_tools(self, default_config):
        """Researcher still has WebSearch and WebFetch for direct use."""
        agents = build_agent_definitions(default_config, {})
        researcher_tools = agents["researcher"]["tools"]
        assert "WebSearch" in researcher_tools
        assert "WebFetch" in researcher_tools

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
        # All 12 default agents should be present (scheduler+verification enabled by default)
        expected_sdk_names = {
            "planner", "researcher", "architect", "task-assigner",
            "code-writer", "code-reviewer", "test-runner",
            "security-auditor", "debugger",
            "integration-agent", "contract-generator", "spec-validator",
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

    def test_orchestrator_prompt_has_resume_context_placeholder(self, default_config):
        """resume_context param is accepted without error."""
        prompt = build_orchestrator_prompt(
            "test", "standard", default_config,
            resume_context="[RESUME MODE -- test]",
        )
        assert "[RESUME MODE -- test]" in prompt

    def test_resume_context_injected_before_task(self, default_config):
        """resume_context should appear before [TASK] in the prompt."""
        ctx = "[RESUME MODE -- Continuing from an interrupted run]"
        prompt = build_orchestrator_prompt(
            "fix the bug", "standard", default_config,
            resume_context=ctx,
        )
        ctx_pos = prompt.index(ctx)
        task_pos = prompt.index("[TASK]")
        assert ctx_pos < task_pos


# ===================================================================
# build_orchestrator_prompt() — design reference cache & dedup
# ===================================================================

class TestDesignReferenceCacheAndDedup:
    def test_prompt_contains_cache_ttl(self, default_config):
        urls = ["https://stripe.com"]
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            design_reference_urls=urls,
        )
        assert "Cache TTL (maxAge): 7200000 milliseconds" in prompt

    def test_cache_ttl_in_milliseconds(self, default_config):
        default_config.design_reference.cache_ttl_seconds = 3600
        urls = ["https://stripe.com"]
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            design_reference_urls=urls,
        )
        assert "Cache TTL (maxAge): 3600000 milliseconds" in prompt

    def test_dedup_instruction_with_multiple_urls(self, default_config):
        urls = ["https://stripe.com", "https://linear.app"]
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            design_reference_urls=urls,
        )
        assert "URL ASSIGNMENT" in prompt
        assert "EXACTLY ONE researcher" in prompt

    def test_no_dedup_instruction_with_single_url(self, default_config):
        urls = ["https://stripe.com"]
        prompt = build_orchestrator_prompt(
            "task", "standard", default_config,
            design_reference_urls=urls,
        )
        assert "URL ASSIGNMENT" not in prompt


# ===================================================================
# UI Design Standards injection
# ===================================================================

class TestUIDesignStandardsInjection:
    """Tests for built-in UI design standards in orchestrator + agent prompts."""

    def test_always_contains_ui_standards(self, default_config):
        prompt = build_orchestrator_prompt("build a landing page", "standard", default_config)
        assert "UI DESIGN STANDARDS" in prompt
        assert "SLOP-001" in prompt
        assert "SLOP-015" in prompt

    def test_ui_standards_with_design_refs(self, default_config):
        urls = ["https://stripe.com"]
        prompt = build_orchestrator_prompt("task", "standard", default_config, design_reference_urls=urls)
        assert "UI DESIGN STANDARDS" in prompt
        assert "DESIGN REFERENCE" in prompt
        assert "OVERRIDES" in prompt

    def test_ui_standards_before_design_refs(self, default_config):
        urls = ["https://stripe.com"]
        prompt = build_orchestrator_prompt("task", "standard", default_config, design_reference_urls=urls)
        standards_pos = prompt.index("UI DESIGN STANDARDS")
        ref_pos = prompt.index("[DESIGN REFERENCE")
        assert standards_pos < ref_pos

    def test_custom_standards_file_used(self, default_config, tmp_path):
        custom = tmp_path / "my-standards.md"
        custom.write_text("MY CUSTOM DESIGN RULES", encoding="utf-8")
        default_config.design_reference.standards_file = str(custom)
        prompt = build_orchestrator_prompt("build UI", "standard", default_config)
        assert "MY CUSTOM DESIGN RULES" in prompt
        assert "SLOP-001" not in prompt

    def test_architect_has_design_system_architecture(self):
        assert "Design System Architecture" in ARCHITECT_PROMPT

    def test_code_writer_has_ui_quality_standards(self):
        assert "UI Quality Standards" in CODE_WRITER_PROMPT

    def test_code_reviewer_has_design_quality_review(self):
        assert "Design Quality Review" in CODE_REVIEWER_PROMPT

    def test_code_reviewer_has_anti_pattern_check(self):
        assert "SLOP-001" in CODE_REVIEWER_PROMPT


# ===================================================================
# Code Quality Standards injection
# ===================================================================

class TestCodeQualityInjection:
    """Tests that build_agent_definitions injects quality standards into the right agents."""

    def test_code_writer_has_frontend_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "FRONT-001" in agents["code-writer"]["prompt"]
        assert "BACK-001" in agents["code-writer"]["prompt"]

    def test_code_reviewer_has_review_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "REVIEW-001" in agents["code-reviewer"]["prompt"]

    def test_test_runner_has_testing_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "TEST-001" in agents["test-runner"]["prompt"]

    def test_debugger_has_debugging_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "DEBUG-001" in agents["debugger"]["prompt"]

    def test_architect_has_architecture_quality(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "ARCHITECTURE QUALITY" in agents["architect"]["prompt"]

    def test_planner_has_no_quality_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "FRONT-001" not in agents["planner"]["prompt"]
        assert "BACK-001" not in agents["planner"]["prompt"]
        assert "REVIEW-001" not in agents["planner"]["prompt"]
        assert "TEST-001" not in agents["planner"]["prompt"]
        assert "DEBUG-001" not in agents["planner"]["prompt"]

    def test_researcher_has_no_quality_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "FRONT-001" not in agents["researcher"]["prompt"]

    def test_task_assigner_has_no_quality_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "FRONT-001" not in agents["task-assigner"]["prompt"]

    def test_security_auditor_has_no_quality_standards(self, default_config):
        agents = build_agent_definitions(default_config, {})
        assert "FRONT-001" not in agents["security-auditor"]["prompt"]
        assert "TEST-001" not in agents["security-auditor"]["prompt"]

    def test_quality_standards_after_constraints(self, default_config):
        """Quality standards appended after constraints."""
        constraints = [ConstraintEntry("Use Python 3.12", "requirement", "task", 1)]
        agents = build_agent_definitions(default_config, {}, constraints=constraints)
        prompt = agents["code-writer"]["prompt"]
        constraint_pos = prompt.index("Python 3.12")
        front_pos = prompt.index("FRONT-001")
        assert constraint_pos < front_pos

    def test_all_frontend_anti_patterns_in_code_writer(self, default_config):
        agents = build_agent_definitions(default_config, {})
        prompt = agents["code-writer"]["prompt"]
        for i in range(1, 16):
            code = f"FRONT-{i:03d}"
            assert code in prompt, f"Missing {code} in code-writer prompt"

    def test_all_backend_anti_patterns_in_code_writer(self, default_config):
        agents = build_agent_definitions(default_config, {})
        prompt = agents["code-writer"]["prompt"]
        for i in range(1, 16):
            code = f"BACK-{i:03d}"
            assert code in prompt, f"Missing {code} in code-writer prompt"

    def test_integration_agent_has_no_quality_standards(self):
        """integration-agent (scheduler-only) gets no quality standards."""
        from agent_team.config import SchedulerConfig
        cfg = AgentTeamConfig(scheduler=SchedulerConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert "integration-agent" in agents
        assert "FRONT-001" not in agents["integration-agent"]["prompt"]
        assert "REVIEW-001" not in agents["integration-agent"]["prompt"]

    def test_contract_generator_has_no_quality_standards(self):
        """contract-generator (verification-only) gets no quality standards."""
        from agent_team.config import VerificationConfig
        cfg = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert "contract-generator" in agents
        assert "FRONT-001" not in agents["contract-generator"]["prompt"]
        assert "TEST-001" not in agents["contract-generator"]["prompt"]

    def test_quality_standards_with_scheduler_enabled(self):
        """Quality standards still injected when scheduler is enabled (12 agents)."""
        from agent_team.config import SchedulerConfig
        cfg = AgentTeamConfig(scheduler=SchedulerConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 12
        assert "FRONT-001" in agents["code-writer"]["prompt"]
        assert "REVIEW-001" in agents["code-reviewer"]["prompt"]

    def test_quality_standards_with_both_enabled(self):
        """Quality standards injected correctly with scheduler + verification (12 agents)."""
        from agent_team.config import SchedulerConfig, VerificationConfig
        cfg = AgentTeamConfig(
            scheduler=SchedulerConfig(enabled=True),
            verification=VerificationConfig(enabled=True),
        )
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 12
        # Quality agents still get standards
        assert "FRONT-001" in agents["code-writer"]["prompt"]
        assert "DEBUG-001" in agents["debugger"]["prompt"]
        # Non-quality agents don't
        assert "FRONT-001" not in agents["integration-agent"]["prompt"]
        assert "FRONT-001" not in agents["contract-generator"]["prompt"]

    def test_all_disabled_no_crash_from_injection(self):
        """When all agents disabled, injection loop still includes spec-validator."""
        cfg = AgentTeamConfig()
        for name in cfg.agents:
            cfg.agents[name] = AgentConfig(enabled=False)
        agents = build_agent_definitions(cfg, {})
        assert len(agents) == 1
        assert "spec-validator" in agents

    def test_empty_constraints_plus_standards(self):
        """Empty constraints + standards: standards still injected, no constraints prefix."""
        agents = build_agent_definitions(AgentTeamConfig(), {}, constraints=[])
        prompt = agents["code-writer"]["prompt"]
        assert "FRONT-001" in prompt
        assert "USER CONSTRAINTS" not in prompt

    def test_custom_model_does_not_affect_standards(self):
        """Per-agent model config doesn't interfere with standards injection."""
        cfg = AgentTeamConfig()
        cfg.agents["code_writer"] = AgentConfig(model="sonnet")
        agents = build_agent_definitions(cfg, {})
        assert agents["code-writer"]["model"] == "sonnet"
        assert "FRONT-001" in agents["code-writer"]["prompt"]
        assert "BACK-001" in agents["code-writer"]["prompt"]


# ===================================================================
# Prompt strengthening
# ===================================================================

class TestPromptStrengthening:
    """Tests that agent prompt constants have their strengthening sections."""

    def test_architect_has_code_architecture_quality(self):
        assert "Code Architecture Quality" in ARCHITECT_PROMPT

    def test_code_writer_has_code_quality_standards(self):
        assert "Code Quality Standards" in CODE_WRITER_PROMPT

    def test_code_reviewer_has_code_quality_review(self):
        assert "Code Quality Review" in CODE_REVIEWER_PROMPT

    def test_test_runner_has_testing_quality_standards(self):
        assert "Testing Quality Standards" in TEST_RUNNER_PROMPT

    def test_debugger_has_debugging_methodology(self):
        assert "Debugging Methodology" in DEBUGGER_PROMPT


# ===================================================================
# SPEC_VALIDATOR_PROMPT
# ===================================================================

class TestSpecValidatorPrompt:
    def test_prompt_exists_and_non_empty(self):
        assert len(SPEC_VALIDATOR_PROMPT) > 100

    def test_contains_spec_fidelity(self):
        assert "SPEC FIDELITY" in SPEC_VALIDATOR_PROMPT

    def test_contains_original_user_request(self):
        assert "ORIGINAL USER REQUEST" in SPEC_VALIDATOR_PROMPT

    def test_contains_pass_fail(self):
        assert "PASS" in SPEC_VALIDATOR_PROMPT
        assert "FAIL" in SPEC_VALIDATOR_PROMPT

    def test_checks_missing_technologies(self):
        assert "Missing Technologies" in SPEC_VALIDATOR_PROMPT or "MISSING_TECH" in SPEC_VALIDATOR_PROMPT

    def test_checks_scope_reduction(self):
        assert "Scope Reduction" in SPEC_VALIDATOR_PROMPT or "SCOPE_REDUCTION" in SPEC_VALIDATOR_PROMPT

    def test_checks_missing_architecture(self):
        assert "Architecture" in SPEC_VALIDATOR_PROMPT or "ARCHITECTURE" in SPEC_VALIDATOR_PROMPT

    def test_spec_validator_in_agent_definitions(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        assert "spec-validator" in agents

    def test_spec_validator_read_only_tools(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        tools = agents["spec-validator"]["tools"]
        assert "Read" in tools
        assert "Glob" in tools
        assert "Grep" in tools
        assert "Write" not in tools
        assert "Edit" not in tools
        assert "Bash" not in tools

    def test_spec_validator_has_description(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        assert len(agents["spec-validator"]["description"]) > 0


# ===================================================================
# Reviewer anchoring to original request
# ===================================================================

class TestReviewerAnchoring:
    def test_reviewer_has_original_request_check(self):
        assert "ORIGINAL USER REQUEST" in CODE_REVIEWER_PROMPT

    def test_reviewer_has_step_1b(self):
        assert "1b." in CODE_REVIEWER_PROMPT

    def test_reviewer_flags_critical(self):
        assert "CRITICAL" in CODE_REVIEWER_PROMPT

    def test_orchestrator_passes_original_request_to_reviewers(self):
        assert "ORIGINAL USER REQUEST" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_build_orchestrator_prompt_has_original_request_section(self):
        cfg = AgentTeamConfig()
        prompt = build_orchestrator_prompt("build a REST API", "standard", cfg)
        assert "[ORIGINAL USER REQUEST]" in prompt
        assert "build a REST API" in prompt


# ===================================================================
# Planner guardrails + mandatory test wave
# ===================================================================

class TestPlannerGuardrails:
    def test_planner_has_technology_preservation(self):
        assert "MUST appear in REQUIREMENTS.md" in PLANNER_PROMPT

    def test_planner_has_monorepo_preservation(self):
        assert "monorepo" in PLANNER_PROMPT.lower()

    def test_planner_has_test_requirements(self):
        assert "Testing Requirements" in PLANNER_PROMPT

    def test_planner_prevents_architecture_simplification(self):
        assert "may NOT" in PLANNER_PROMPT or "may not" in PLANNER_PROMPT.lower()


class TestMandatoryTestWave:
    def test_orchestrator_has_mandatory_test_rule(self):
        assert "MANDATORY TEST RULE" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_mentions_test_keywords(self):
        assert "test suite" in ORCHESTRATOR_SYSTEM_PROMPT.lower() or "tests" in ORCHESTRATOR_SYSTEM_PROMPT.lower()

    def test_orchestrator_test_rule_is_blocking(self):
        assert "BLOCKING" in ORCHESTRATOR_SYSTEM_PROMPT


# ===================================================================
# Investigation protocol injection
# ===================================================================

class TestInvestigationInjection:
    """Tests that investigation protocol is injected into the right agents."""

    def test_protocol_injected_when_enabled(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "DEEP INVESTIGATION PROTOCOL" in agents["code-reviewer"]["prompt"]
        assert "DEEP INVESTIGATION PROTOCOL" in agents["security-auditor"]["prompt"]
        assert "DEEP INVESTIGATION PROTOCOL" in agents["debugger"]["prompt"]

    def test_protocol_not_injected_when_disabled(self):
        cfg = AgentTeamConfig()
        # Default: investigation.enabled = False
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "DEEP INVESTIGATION PROTOCOL" not in agents["code-reviewer"]["prompt"]
        assert "DEEP INVESTIGATION PROTOCOL" not in agents["debugger"]["prompt"]

    def test_protocol_not_injected_for_planner(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "DEEP INVESTIGATION PROTOCOL" not in agents["planner"]["prompt"]

    def test_protocol_not_injected_for_code_writer(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "DEEP INVESTIGATION PROTOCOL" not in agents["code-writer"]["prompt"]

    def test_bash_added_to_reviewer_with_gemini(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=True)
        assert "Bash" in agents["code-reviewer"]["tools"]

    def test_bash_not_added_to_reviewer_without_gemini(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "Bash" not in agents["code-reviewer"]["tools"]

    def test_bash_not_added_when_investigation_disabled(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {}, gemini_available=True)
        assert "Bash" not in agents["code-reviewer"]["tools"]

    def test_gemini_section_in_reviewer_when_available(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=True)
        assert "Gemini CLI" in agents["code-reviewer"]["prompt"]

    def test_gemini_section_not_in_reviewer_without_gemini(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "Gemini CLI" not in agents["code-reviewer"]["prompt"]

    def test_protocol_all_three_agents_enabled(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=True)
        for name in ["code-reviewer", "security-auditor", "debugger"]:
            assert "DEEP INVESTIGATION PROTOCOL" in agents[name]["prompt"], (
                f"{name} should have investigation protocol"
            )

    def test_quality_standards_still_present_with_investigation(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=True)
        # Quality standards should still be injected
        assert "REVIEW-001" in agents["code-reviewer"]["prompt"]
        assert "DEBUG-001" in agents["debugger"]["prompt"]
        # Investigation protocol should also be present
        assert "DEEP INVESTIGATION PROTOCOL" in agents["code-reviewer"]["prompt"]
        assert "DEEP INVESTIGATION PROTOCOL" in agents["debugger"]["prompt"]


class TestSequentialThinkingInjection:
    """Tests that ST methodology is injected into the right agents."""

    def test_st_injected_when_investigation_and_st_enabled(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True, sequential_thinking=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "SEQUENTIAL THINKING METHODOLOGY" in agents["code-reviewer"]["prompt"]
        assert "SEQUENTIAL THINKING METHODOLOGY" in agents["security-auditor"]["prompt"]
        assert "SEQUENTIAL THINKING METHODOLOGY" in agents["debugger"]["prompt"]

    def test_st_not_injected_when_investigation_disabled(self):
        cfg = AgentTeamConfig()
        # Default: investigation.enabled = False
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "SEQUENTIAL THINKING METHODOLOGY" not in agents["code-reviewer"]["prompt"]

    def test_st_not_injected_when_st_disabled(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True, sequential_thinking=False)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "SEQUENTIAL THINKING METHODOLOGY" not in agents["code-reviewer"]["prompt"]
        # Investigation protocol should still be present
        assert "DEEP INVESTIGATION PROTOCOL" in agents["code-reviewer"]["prompt"]

    def test_st_not_injected_for_planner(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "SEQUENTIAL THINKING METHODOLOGY" not in agents["planner"]["prompt"]

    def test_st_not_injected_for_code_writer(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "SEQUENTIAL THINKING METHODOLOGY" not in agents["code-writer"]["prompt"]

    def test_st_appears_after_investigation_protocol(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        prompt = agents["code-reviewer"]["prompt"]
        ip_idx = prompt.index("DEEP INVESTIGATION PROTOCOL")
        st_idx = prompt.index("SEQUENTIAL THINKING METHODOLOGY")
        assert ip_idx < st_idx, "ST must appear after Investigation Protocol"

    def test_hypothesis_loop_present_by_default(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "Hypothesis-Verification Cycle" in agents["code-reviewer"]["prompt"]

    def test_hypothesis_loop_absent_when_disabled(self):
        from agent_team.config import InvestigationConfig
        cfg = AgentTeamConfig()
        cfg.investigation = InvestigationConfig(enabled=True, enable_hypothesis_loop=False)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "Hypothesis-Verification Cycle" not in agents["code-reviewer"]["prompt"]
        # ST core should still be present
        assert "SEQUENTIAL THINKING METHODOLOGY" in agents["code-reviewer"]["prompt"]


# ===================================================================
# Quality Optimization: Production Readiness & Code Craft
# ===================================================================

class TestProductionReadinessDefaults:
    def test_planner_has_production_defaults(self):
        assert "PRODUCTION READINESS DEFAULTS" in PLANNER_PROMPT

    def test_planner_mentions_gitignore(self):
        assert ".gitignore" in PLANNER_PROMPT

    def test_planner_mentions_pagination(self):
        assert "pagination" in PLANNER_PROMPT.lower()

    def test_planner_mentions_nan(self):
        assert "NaN" in PLANNER_PROMPT

    def test_planner_mentions_transaction(self):
        assert "transaction" in PLANNER_PROMPT.lower()


class TestArchitectSharedUtilities:
    def test_architect_has_shared_utilities_map(self):
        assert "Shared Utilities Map" in ARCHITECT_PROMPT


class TestWriterQualitySections:
    def test_writer_has_validation_pattern(self):
        assert "Validation Middleware" in CODE_WRITER_PROMPT

    def test_writer_has_transaction_safety(self):
        assert "Transaction Safety" in CODE_WRITER_PROMPT

    def test_writer_has_param_validation(self):
        assert "Route Parameter Validation" in CODE_WRITER_PROMPT


class TestReviewerCraftReview:
    def test_reviewer_has_craft_review(self):
        assert "CODE CRAFT REVIEW" in CODE_REVIEWER_PROMPT

    def test_reviewer_has_all_craft_checks(self):
        craft_checks = [
            "CRAFT-DRY",
            "CRAFT-TYPES",
            "CRAFT-PARAMS",
            "CRAFT-TXN",
            "CRAFT-VALIDATION",
            "CRAFT-FK",
        ]
        for check in craft_checks:
            assert check in CODE_REVIEWER_PROMPT, f"Missing {check} in reviewer prompt"


class TestQualityConfigGating:
    """Verify config.quality flags control prompt content in build_agent_definitions."""

    def test_quick_depth_strips_production_defaults(self):
        from agent_team.config import QualityConfig
        cfg = AgentTeamConfig()
        cfg.quality = QualityConfig(production_defaults=False)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "PRODUCTION READINESS DEFAULTS" not in agents["planner"]["prompt"]

    def test_standard_depth_keeps_production_defaults(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "PRODUCTION READINESS DEFAULTS" in agents["planner"]["prompt"]

    def test_quick_depth_strips_craft_review(self):
        from agent_team.config import QualityConfig
        cfg = AgentTeamConfig()
        cfg.quality = QualityConfig(craft_review=False)
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "CODE CRAFT REVIEW" not in agents["code-reviewer"]["prompt"]

    def test_standard_depth_keeps_craft_review(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {}, gemini_available=False)
        assert "CODE CRAFT REVIEW" in agents["code-reviewer"]["prompt"]
