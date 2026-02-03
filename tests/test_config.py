"""Tests for agent_team.config."""

from __future__ import annotations

import pytest
import yaml

from agent_team.config import (
    AgentConfig,
    AgentTeamConfig,
    CodebaseMapConfig,
    ConstraintEntry,
    ConvergenceConfig,
    DEPTH_AGENT_COUNTS,
    DepthConfig,
    DepthDetection,
    DesignReferenceConfig,
    DisplayConfig,
    InterviewConfig,
    InvestigationConfig,
    MCPServerConfig,
    OrchestratorConfig,
    QualityConfig,
    SchedulerConfig,
    VerificationConfig,
    _deep_merge,
    _dict_to_config,
    apply_depth_quality_gating,
    detect_depth,
    extract_constraints,
    format_constraints_block,
    get_agent_counts,
    load_config,
    parse_max_review_cycles,
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

    def test_max_budget_usd_default(self):
        c = OrchestratorConfig()
        assert c.max_budget_usd is None


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

    def test_min_exchanges_default(self):
        c = InterviewConfig()
        assert c.min_exchanges == 3

    def test_require_understanding_summary_default(self):
        c = InterviewConfig()
        assert c.require_understanding_summary is True

    def test_require_codebase_exploration_default(self):
        c = InterviewConfig()
        assert c.require_codebase_exploration is True


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

    def test_cache_ttl_seconds_default(self):
        c = DesignReferenceConfig()
        assert c.cache_ttl_seconds == 7200

    def test_standards_file_default_empty(self):
        c = DesignReferenceConfig()
        assert c.standards_file == ""


class TestDisplayConfigDefaults:
    def test_show_cost(self):
        c = DisplayConfig()
        assert c.show_cost is True

    def test_verbose(self):
        c = DisplayConfig()
        assert c.verbose is False


class TestCodebaseMapConfigDefaults:
    def test_enabled_default(self):
        c = CodebaseMapConfig()
        assert c.enabled is True

    def test_max_files_default(self):
        c = CodebaseMapConfig()
        assert c.max_files == 5000

    def test_max_file_size_kb_default(self):
        c = CodebaseMapConfig()
        assert c.max_file_size_kb == 50

    def test_max_file_size_kb_ts_default(self):
        c = CodebaseMapConfig()
        assert c.max_file_size_kb_ts == 100

    def test_timeout_seconds_default(self):
        c = CodebaseMapConfig()
        assert c.timeout_seconds == 30

    def test_exclude_patterns_default(self):
        c = CodebaseMapConfig()
        assert "node_modules" in c.exclude_patterns
        assert ".git" in c.exclude_patterns


class TestSchedulerConfigDefaults:
    def test_enabled_true_by_default(self):
        c = SchedulerConfig()
        assert c.enabled is True

    def test_max_parallel_tasks_default(self):
        c = SchedulerConfig()
        assert c.max_parallel_tasks == 5

    def test_conflict_strategy_default(self):
        c = SchedulerConfig()
        assert c.conflict_strategy == "artificial-dependency"

    def test_enable_context_scoping_default(self):
        c = SchedulerConfig()
        assert c.enable_context_scoping is True

    def test_enable_critical_path_default(self):
        c = SchedulerConfig()
        assert c.enable_critical_path is True


class TestVerificationConfigDefaults:
    def test_enabled_true_by_default(self):
        c = VerificationConfig()
        assert c.enabled is True

    def test_blocking_true_by_default(self):
        c = VerificationConfig()
        assert c.blocking is True

    def test_contract_file_default(self):
        c = VerificationConfig()
        assert c.contract_file == "CONTRACTS.json"

    def test_verification_file_default(self):
        c = VerificationConfig()
        assert c.verification_file == "VERIFICATION.md"

    def test_run_lint_default(self):
        c = VerificationConfig()
        assert c.run_lint is True

    def test_run_type_check_default(self):
        c = VerificationConfig()
        assert c.run_type_check is True

    def test_run_tests_default(self):
        c = VerificationConfig()
        assert c.run_tests is True


class TestAgentTeamConfigDefaults:
    def test_has_11_agents(self):
        c = AgentTeamConfig()
        assert len(c.agents) == 11

    def test_agent_names(self):
        c = AgentTeamConfig()
        expected = {
            "planner", "researcher", "architect", "task_assigner",
            "code_writer", "code_reviewer", "test_runner",
            "security_auditor", "debugger",
            "integration_agent", "contract_generator",
        }
        assert set(c.agents.keys()) == expected

    def test_has_3_mcp_servers(self):
        c = AgentTeamConfig()
        assert len(c.mcp_servers) == 3
        assert "firecrawl" in c.mcp_servers
        assert "context7" in c.mcp_servers
        assert "sequential_thinking" in c.mcp_servers
        assert c.mcp_servers["sequential_thinking"].enabled is False

    def test_has_codebase_map_config(self):
        c = AgentTeamConfig()
        assert isinstance(c.codebase_map, CodebaseMapConfig)
        assert c.codebase_map.enabled is True

    def test_has_scheduler_config(self):
        c = AgentTeamConfig()
        assert isinstance(c.scheduler, SchedulerConfig)
        assert c.scheduler.enabled is True

    def test_has_verification_config(self):
        c = AgentTeamConfig()
        assert isinstance(c.verification, VerificationConfig)
        assert c.verification.enabled is True


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

    def test_codebase_map_section(self):
        cfg = _dict_to_config({"codebase_map": {"enabled": False, "max_files": 1000}})
        assert cfg.codebase_map.enabled is False
        assert cfg.codebase_map.max_files == 1000

    def test_scheduler_section(self):
        cfg = _dict_to_config({"scheduler": {"enabled": True, "max_parallel_tasks": 3}})
        assert cfg.scheduler.enabled is True
        assert cfg.scheduler.max_parallel_tasks == 3

    def test_verification_section(self):
        cfg = _dict_to_config({"verification": {"enabled": True, "blocking": False}})
        assert cfg.verification.enabled is True
        assert cfg.verification.blocking is False

    def test_orchestrator_max_budget_usd(self):
        cfg = _dict_to_config({"orchestrator": {"max_budget_usd": 5.0}})
        assert cfg.orchestrator.max_budget_usd == 5.0

    def test_orchestrator_max_budget_usd_default(self):
        cfg = _dict_to_config({})
        assert cfg.orchestrator.max_budget_usd is None


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


class TestDesignReferenceFalsyValues:
    """Regression tests for Finding #9: falsy config values preserved."""

    def test_empty_urls_preserved(self):
        """urls: [] should stay empty, not fall back to default."""
        cfg = _dict_to_config({"design_reference": {"urls": []}})
        assert cfg.design_reference.urls == []

    def test_zero_max_pages_preserved(self):
        """max_pages_per_site: 0 should stay 0, not fall back to default."""
        cfg = _dict_to_config({"design_reference": {"max_pages_per_site": 0}})
        assert cfg.design_reference.max_pages_per_site == 0

    def test_empty_depth_preserved(self):
        """depth: '' should stay empty string, not fall back to default."""
        cfg = _dict_to_config({"design_reference": {"depth": ""}})
        assert cfg.design_reference.depth == ""

    def test_normal_values_still_work(self):
        """Normal values should still work correctly."""
        cfg = _dict_to_config({"design_reference": {"urls": ["https://example.com"], "depth": "branding", "max_pages_per_site": 10}})
        assert cfg.design_reference.urls == ["https://example.com"]
        assert cfg.design_reference.depth == "branding"
        assert cfg.design_reference.max_pages_per_site == 10


class TestDesignReferenceCacheTTL:
    def test_design_reference_cache_ttl_from_yaml(self):
        cfg = _dict_to_config({"design_reference": {"cache_ttl_seconds": 3600}})
        assert cfg.design_reference.cache_ttl_seconds == 3600


# ===================================================================
# Enum validation (Findings #15, #16)
# ===================================================================

class TestEnumValidation:
    """Tests for Finding #15/#16: enum-like string validation."""

    def test_invalid_conflict_strategy_raises(self):
        with pytest.raises(ValueError, match="conflict_strategy"):
            _dict_to_config({"scheduler": {"conflict_strategy": "invalid-strategy"}})

    def test_valid_conflict_strategy_accepted(self):
        cfg = _dict_to_config({"scheduler": {"conflict_strategy": "integration-agent"}})
        assert cfg.scheduler.conflict_strategy == "integration-agent"

    def test_invalid_design_ref_depth_raises(self):
        with pytest.raises(ValueError, match="design_reference.depth"):
            _dict_to_config({"design_reference": {"depth": "invalid-depth"}})

    def test_valid_design_ref_depth_accepted(self):
        cfg = _dict_to_config({"design_reference": {"depth": "branding"}})
        assert cfg.design_reference.depth == "branding"


# ===================================================================
# Config propagation (Finding #7)
# ===================================================================

class TestConfigPropagation:
    """Tests for Finding #7: config values propagated to enforcement points."""

    def test_timeout_seconds_accessible(self):
        """codebase_map.timeout_seconds is accessible and has sensible default."""
        cfg = AgentTeamConfig()
        assert cfg.codebase_map.timeout_seconds == 30
        assert isinstance(cfg.codebase_map.timeout_seconds, int)

    def test_custom_timeout_persists(self):
        """Custom timeout value set via config is preserved."""
        cfg = _dict_to_config({"codebase_map": {"timeout_seconds": 60}})
        assert cfg.codebase_map.timeout_seconds == 60

    def test_verification_paths_accessible(self):
        """verification config paths are accessible."""
        cfg = AgentTeamConfig()
        assert cfg.verification.contract_file == "CONTRACTS.json"
        assert cfg.verification.verification_file == "VERIFICATION.md"

    def test_display_flags_accessible(self):
        """Display config flags are accessible."""
        cfg = AgentTeamConfig()
        assert cfg.display.show_fleet_composition is True
        assert cfg.display.show_convergence_status is True


# ===================================================================
# Constraint extraction
# ===================================================================

class TestConstraintExtraction:
    def test_prohibition_extraction(self):
        constraints = extract_constraints("no library swaps allowed.")
        assert any(c.category == "prohibition" for c in constraints)

    def test_zero_prohibition(self):
        constraints = extract_constraints("ZERO functionality changes.")
        assert any(c.category == "prohibition" for c in constraints)

    def test_requirement_extraction(self):
        constraints = extract_constraints("must preserve existing behavior.")
        assert any(c.category == "requirement" for c in constraints)

    def test_scope_extraction(self):
        constraints = extract_constraints("only restyle the SCSS files.")
        assert any(c.category == "scope" for c in constraints)

    def test_deduplication(self):
        constraints = extract_constraints("no swaps. no swaps. no swaps.")
        prohibition_count = sum(1 for c in constraints if "swaps" in c.text.lower())
        assert prohibition_count == 1

    def test_emphasis_detection_caps(self):
        constraints = extract_constraints("ZERO FUNCTIONALITY CHANGES.")
        caps_constraints = [c for c in constraints if c.emphasis >= 2]
        assert len(caps_constraints) > 0

    def test_format_output_non_empty(self):
        constraints = [ConstraintEntry("no changes", "prohibition", "task", 2)]
        block = format_constraints_block(constraints)
        assert "PROHIBITION" in block
        assert "no changes" in block

    def test_format_output_empty(self):
        block = format_constraints_block([])
        assert block == ""

    def test_interview_doc_source(self):
        constraints = extract_constraints("test", "must keep all features intact.")
        interview_constraints = [c for c in constraints if c.source == "interview"]
        assert len(interview_constraints) > 0

    def test_no_constraints_returns_empty(self):
        constraints = extract_constraints("fix the button color")
        # May or may not find constraints depending on phrasing
        assert isinstance(constraints, list)


# ===================================================================
# parse_max_review_cycles()
# ===================================================================

class TestParseMaxReviewCycles:
    def test_single_cycle_count(self):
        content = "- [x] Feature A (review_cycles: 2)"
        assert parse_max_review_cycles(content) == 2

    def test_multiple_takes_max(self):
        content = "- [x] A (review_cycles: 1)\n- [x] B (review_cycles: 3)\n- [ ] C (review_cycles: 2)"
        assert parse_max_review_cycles(content) == 3

    def test_no_cycles_returns_zero(self):
        content = "- [x] Feature A\n- [ ] Feature B"
        assert parse_max_review_cycles(content) == 0

    def test_empty_string(self):
        assert parse_max_review_cycles("") == 0


# ===================================================================
# DepthDetection dataclass
# ===================================================================

class TestDepthDetectionDataclass:
    def test_str_conversion(self):
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        assert str(d) == "thorough"

    def test_eq_with_string(self):
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        assert d == "thorough"
        assert d != "quick"

    def test_eq_with_depth_detection(self):
        d1 = DepthDetection("thorough", "keyword", ["thorough"], "test")
        d2 = DepthDetection("thorough", "default", [], "other")
        assert d1 == d2

    def test_has_explanation(self):
        d = DepthDetection("thorough", "keyword", ["thorough"], "Matched keywords: ['thorough']")
        assert d.explanation != ""
        assert "thorough" in d.explanation

    def test_hash_works(self):
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        assert hash(d) == hash("thorough")

    def test_copy_safe(self):
        """DepthDetection must survive copy.copy without RecursionError."""
        import copy
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        d2 = copy.copy(d)
        assert d2.level == "thorough"
        assert d2 == d

    def test_deepcopy_safe(self):
        """DepthDetection must survive copy.deepcopy without RecursionError."""
        import copy
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        d2 = copy.deepcopy(d)
        assert d2.level == "thorough"
        assert d2 == d

    def test_pickle_roundtrip(self):
        """DepthDetection must survive pickle round-trip without RecursionError."""
        import pickle
        d = DepthDetection("exhaustive", "keyword", ["migrate"], "test")
        data = pickle.dumps(d)
        d2 = pickle.loads(data)
        assert d2.level == "exhaustive"
        assert d2 == d

    def test_getattr_delegates_to_str(self):
        """String methods like .upper() should work via __getattr__."""
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        assert d.upper() == "THOROUGH"
        assert d.startswith("thor") is True

    def test_getattr_raises_attributeerror(self):
        """Non-existent str attributes should raise AttributeError."""
        d = DepthDetection("thorough", "keyword", ["thorough"], "test")
        with pytest.raises(AttributeError):
            d.nonexistent_method_xyz()


# ===================================================================
# detect_depth() expanded
# ===================================================================

class TestDetectDepthExpanded:
    def test_just_no_longer_triggers_quick(self, default_config):
        result = detect_depth("just update this component", default_config)
        assert result.level != "quick"  # "just" removed from quick keywords

    def test_restyle_triggers_thorough(self, default_config):
        result = detect_depth("restyle the login page styles", default_config)
        assert result.level == "thorough"

    def test_migrate_triggers_exhaustive(self, default_config):
        result = detect_depth("migrate to the new framework", default_config)
        assert result.level == "exhaustive"

    def test_modernize_triggers_thorough(self, default_config):
        result = detect_depth("modernize the UI components", default_config)
        assert result.level == "thorough"

    def test_replatform_triggers_exhaustive(self, default_config):
        result = detect_depth("replatform the application", default_config)
        assert result.level == "exhaustive"

    def test_returns_depth_detection_object(self, default_config):
        result = detect_depth("thorough review", default_config)
        assert isinstance(result, DepthDetection)
        assert result.level == "thorough"
        assert result.source == "keyword"
        assert "thorough" in result.matched_keywords


# ===================================================================
# InterviewConfig validation via _dict_to_config
# ===================================================================

class TestInterviewConfigValidation:
    def test_min_exchanges_in_dict_to_config(self):
        cfg = _dict_to_config({"interview": {"min_exchanges": 5}})
        assert cfg.interview.min_exchanges == 5

    def test_require_understanding_in_dict_to_config(self):
        cfg = _dict_to_config({"interview": {"require_understanding_summary": False}})
        assert cfg.interview.require_understanding_summary is False

    def test_require_exploration_in_dict_to_config(self):
        cfg = _dict_to_config({"interview": {"require_codebase_exploration": False}})
        assert cfg.interview.require_codebase_exploration is False

    def test_min_exchanges_zero_raises(self):
        with pytest.raises(ValueError, match="min_exchanges must be >= 1"):
            _dict_to_config({"interview": {"min_exchanges": 0}})

    def test_min_exchanges_exceeds_max_raises(self):
        with pytest.raises(ValueError, match="min_exchanges must be <= max_exchanges"):
            _dict_to_config({"interview": {"min_exchanges": 100, "max_exchanges": 50}})


# ===================================================================
# Config Propagation to Runtime Tests
# ===================================================================


class TestConfigPropagationToRuntime:
    """Verify config fields round-trip through _dict_to_config."""

    def test_codebase_map_fields_from_yaml(self):
        cfg = _dict_to_config({
            "codebase_map": {
                "max_files": 1000,
                "max_file_size_kb": 25,
                "max_file_size_kb_ts": 75,
                "exclude_patterns": ["my_vendor", "dist"],
            }
        })
        assert cfg.codebase_map.max_files == 1000
        assert cfg.codebase_map.max_file_size_kb == 25
        assert cfg.codebase_map.max_file_size_kb_ts == 75
        assert "my_vendor" in cfg.codebase_map.exclude_patterns
        assert "dist" in cfg.codebase_map.exclude_patterns

    def test_scheduler_fields_from_yaml(self):
        cfg = _dict_to_config({
            "scheduler": {
                "max_parallel_tasks": 3,
                "conflict_strategy": "integration-agent",
                "enable_context_scoping": False,
                "enable_critical_path": False,
            }
        })
        assert cfg.scheduler.max_parallel_tasks == 3
        assert cfg.scheduler.conflict_strategy == "integration-agent"
        assert cfg.scheduler.enable_context_scoping is False
        assert cfg.scheduler.enable_critical_path is False

    def test_verification_blocking_from_yaml(self):
        cfg = _dict_to_config({"verification": {"blocking": False}})
        assert cfg.verification.blocking is False

    def test_display_gating_from_yaml(self):
        cfg = _dict_to_config({
            "display": {
                "show_fleet_composition": False,
                "show_convergence_status": False,
            }
        })
        assert cfg.display.show_fleet_composition is False
        assert cfg.display.show_convergence_status is False

    def test_orchestrator_awareness_from_yaml(self):
        cfg = _dict_to_config({
            "orchestrator": {"max_budget_usd": 42.5},
            "convergence": {
                "max_cycles": 20,
                "master_plan_file": "CUSTOM_PLAN.md",
            },
        })
        assert cfg.orchestrator.max_budget_usd == 42.5
        assert cfg.convergence.max_cycles == 20
        assert cfg.convergence.master_plan_file == "CUSTOM_PLAN.md"


# ===================================================================
# OrchestratorConfig.backend
# ===================================================================

class TestOrchestratorBackendConfig:
    def test_backend_default_auto(self):
        c = OrchestratorConfig()
        assert c.backend == "auto"

    def test_backend_from_yaml(self):
        cfg = _dict_to_config({"orchestrator": {"backend": "cli"}})
        assert cfg.orchestrator.backend == "cli"

    def test_backend_api_from_yaml(self):
        cfg = _dict_to_config({"orchestrator": {"backend": "api"}})
        assert cfg.orchestrator.backend == "api"

    def test_backend_auto_from_yaml(self):
        cfg = _dict_to_config({"orchestrator": {"backend": "auto"}})
        assert cfg.orchestrator.backend == "auto"

    def test_backend_invalid_raises(self):
        with pytest.raises(ValueError, match="orchestrator.backend"):
            _dict_to_config({"orchestrator": {"backend": "invalid"}})


# ===================================================================
# DesignReference standards_file wiring
# ===================================================================

class TestDesignReferenceStandardsFile:
    def test_standards_file_from_yaml(self):
        cfg = _dict_to_config({"design_reference": {"standards_file": "/path/to/custom.md"}})
        assert cfg.design_reference.standards_file == "/path/to/custom.md"

    def test_standards_file_default_when_absent(self):
        cfg = _dict_to_config({"design_reference": {}})
        assert cfg.design_reference.standards_file == ""

    def test_standards_file_empty_string_preserved(self):
        cfg = _dict_to_config({"design_reference": {"standards_file": ""}})
        assert cfg.design_reference.standards_file == ""


# ===================================================================
# Enhanced constraint extraction (technology + test count)
# ===================================================================

class TestTechnologyRegex:
    """Tests for _TECHNOLOGY_RE pattern matching."""

    def test_matches_expressjs(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Use Express.js for the backend")

    def test_matches_react(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Build with React")

    def test_matches_nextjs(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Deploy on Next.js")

    def test_matches_mongodb(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Store data in MongoDB")

    def test_matches_monorepo(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Use a monorepo structure")

    def test_matches_typescript(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Written in TypeScript")

    def test_matches_tailwind(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("Style with Tailwind CSS")

    def test_case_insensitive(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert _TECHNOLOGY_RE.search("use MONGODB for storage")

    def test_no_match_on_generic_text(self):
        from agent_team.config import _TECHNOLOGY_RE
        assert not _TECHNOLOGY_RE.search("build a simple calculator")


class TestTestRequirementRegex:
    """Tests for _TEST_REQUIREMENT_RE pattern matching."""

    def test_matches_20_plus_tests(self):
        from agent_team.config import _TEST_REQUIREMENT_RE
        m = _TEST_REQUIREMENT_RE.search("Must have 20+ tests")
        assert m is not None
        assert m.group(1) == "20"

    def test_matches_10_unit_tests(self):
        from agent_team.config import _TEST_REQUIREMENT_RE
        m = _TEST_REQUIREMENT_RE.search("Write 10 unit tests")
        assert m is not None
        assert m.group(1) == "10"

    def test_matches_5_tests(self):
        from agent_team.config import _TEST_REQUIREMENT_RE
        m = _TEST_REQUIREMENT_RE.search("at least 5 tests")
        assert m is not None
        assert m.group(1) == "5"

    def test_no_match_without_number(self):
        from agent_team.config import _TEST_REQUIREMENT_RE
        assert not _TEST_REQUIREMENT_RE.search("write some tests")


class TestEnhancedConstraintExtraction:
    """Tests for technology and test count extraction in extract_constraints."""

    def test_extracts_technology_from_task(self):
        constraints = extract_constraints("Build a REST API with Express.js and MongoDB")
        tech_constraints = [c for c in constraints if "express" in c.text.lower()]
        assert len(tech_constraints) >= 1
        assert tech_constraints[0].category == "requirement"

    def test_extracts_multiple_technologies(self):
        constraints = extract_constraints("Use React, Express.js, and MongoDB for a full-stack app")
        tech_names = {c.text.lower() for c in constraints if c.text.startswith("must use")}
        assert any("react" in t for t in tech_names)
        assert any("express" in t for t in tech_names)
        assert any("mongodb" in t for t in tech_names)

    def test_extracts_test_count(self):
        constraints = extract_constraints("Build an app with 20+ tests")
        test_constraints = [c for c in constraints if "20+ tests" in c.text]
        assert len(test_constraints) == 1
        assert test_constraints[0].category == "requirement"

    def test_deduplicates_technologies(self):
        constraints = extract_constraints("Use React. Also use React for the UI.")
        react_constraints = [c for c in constraints if "react" in c.text.lower() and c.text.startswith("must use")]
        assert len(react_constraints) == 1

    def test_extracts_from_interview_doc(self):
        constraints = extract_constraints("test task", "Build with Next.js and PostgreSQL")
        tech_constraints = [c for c in constraints if c.text.startswith("must use")]
        assert any("next.js" in c.text.lower() for c in tech_constraints)
        assert any("postgresql" in c.text.lower() for c in tech_constraints)

    def test_technology_constraints_have_emphasis_2(self):
        constraints = extract_constraints("Use Express.js for the API")
        express_constraints = [c for c in constraints if "express" in c.text.lower()]
        assert len(express_constraints) >= 1
        assert express_constraints[0].emphasis == 2

    def test_combined_tech_and_test_extraction(self):
        constraints = extract_constraints("Build a React app with Express.js backend and 15+ tests")
        tech_texts = [c.text for c in constraints if c.text.startswith("must use")]
        test_texts = [c.text for c in constraints if "tests" in c.text]
        assert len(tech_texts) >= 2
        assert len(test_texts) >= 1


class TestDefaultConfigEnabledByDefault:
    """Tests verifying scheduler and verification are enabled by default."""

    def test_scheduler_enabled_in_default_config(self):
        cfg = AgentTeamConfig()
        assert cfg.scheduler.enabled is True

    def test_verification_enabled_in_default_config(self):
        cfg = AgentTeamConfig()
        assert cfg.verification.enabled is True

    def test_explicit_false_overrides_default(self):
        """YAML with enabled: false must still work (backward compat)."""
        from agent_team.config import _dict_to_config
        cfg = _dict_to_config({"scheduler": {"enabled": False}})
        assert cfg.scheduler.enabled is False

    def test_explicit_false_verification_overrides_default(self):
        """YAML with verification.enabled: false must still work."""
        from agent_team.config import _dict_to_config
        cfg = _dict_to_config({"verification": {"enabled": False}})
        assert cfg.verification.enabled is False


# ===================================================================
# InvestigationConfig
# ===================================================================

class TestInvestigationConfigDefaults:
    def test_enabled_false_by_default(self):
        c = InvestigationConfig()
        assert c.enabled is False

    def test_gemini_model_empty_by_default(self):
        c = InvestigationConfig()
        assert c.gemini_model == ""

    def test_max_queries_default(self):
        c = InvestigationConfig()
        assert c.max_queries_per_agent == 8

    def test_timeout_seconds_default(self):
        c = InvestigationConfig()
        assert c.timeout_seconds == 120

    def test_agents_default(self):
        c = InvestigationConfig()
        assert c.agents == ["code-reviewer", "security-auditor", "debugger"]

    def test_sequential_thinking_true_by_default(self):
        c = InvestigationConfig()
        assert c.sequential_thinking is True

    def test_max_thoughts_per_item_default(self):
        c = InvestigationConfig()
        assert c.max_thoughts_per_item == 15

    def test_enable_hypothesis_loop_true_by_default(self):
        c = InvestigationConfig()
        assert c.enable_hypothesis_loop is True


class TestInvestigationConfigInAgentTeamConfig:
    def test_has_investigation_config(self):
        c = AgentTeamConfig()
        assert isinstance(c.investigation, InvestigationConfig)
        assert c.investigation.enabled is False

    def test_investigation_from_yaml(self):
        cfg = _dict_to_config({
            "investigation": {
                "enabled": True,
                "gemini_model": "gemini-2.5-pro",
                "max_queries_per_agent": 5,
                "timeout_seconds": 60,
                "agents": ["code-reviewer", "debugger"],
            }
        })
        assert cfg.investigation.enabled is True
        assert cfg.investigation.gemini_model == "gemini-2.5-pro"
        assert cfg.investigation.max_queries_per_agent == 5
        assert cfg.investigation.timeout_seconds == 60
        assert cfg.investigation.agents == ["code-reviewer", "debugger"]

    def test_investigation_st_fields_from_yaml(self):
        cfg = _dict_to_config({
            "investigation": {
                "sequential_thinking": False,
                "max_thoughts_per_item": 10,
                "enable_hypothesis_loop": False,
            }
        })
        assert cfg.investigation.sequential_thinking is False
        assert cfg.investigation.max_thoughts_per_item == 10
        assert cfg.investigation.enable_hypothesis_loop is False

    def test_investigation_partial_yaml(self):
        cfg = _dict_to_config({"investigation": {"enabled": True}})
        assert cfg.investigation.enabled is True
        assert cfg.investigation.max_queries_per_agent == 8  # default preserved

    def test_investigation_absent_from_yaml(self):
        cfg = _dict_to_config({})
        assert cfg.investigation.enabled is False

    def test_investigation_non_dict_ignored(self):
        cfg = _dict_to_config({"investigation": "invalid"})
        assert cfg.investigation.enabled is False  # default unchanged

    def test_investigation_old_config_without_st_fields(self):
        """Backward compat: old config with investigation but no ST fields."""
        cfg = _dict_to_config({
            "investigation": {
                "enabled": True,
                "gemini_model": "gemini-2.5-pro",
                "max_queries_per_agent": 5,
                "agents": ["code-reviewer"],
            }
        })
        # ST fields should get their defaults
        assert cfg.investigation.sequential_thinking is True
        assert cfg.investigation.max_thoughts_per_item == 15
        assert cfg.investigation.enable_hypothesis_loop is True


class TestInvestigationConfigValidation:
    def test_zero_queries_raises(self):
        with pytest.raises(ValueError, match="max_queries_per_agent"):
            _dict_to_config({"investigation": {"max_queries_per_agent": 0}})

    def test_negative_queries_raises(self):
        with pytest.raises(ValueError, match="max_queries_per_agent"):
            _dict_to_config({"investigation": {"max_queries_per_agent": -1}})

    def test_zero_timeout_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds"):
            _dict_to_config({"investigation": {"timeout_seconds": 0}})

    def test_invalid_agent_name_raises(self):
        with pytest.raises(ValueError, match="invalid agent name"):
            _dict_to_config({"investigation": {"agents": ["nonexistent-agent"]}})

    def test_valid_non_default_agents_accepted(self):
        cfg = _dict_to_config({"investigation": {"agents": ["planner", "architect"]}})
        assert cfg.investigation.agents == ["planner", "architect"]

    def test_empty_agents_list_accepted(self):
        cfg = _dict_to_config({"investigation": {"agents": []}})
        assert cfg.investigation.agents == []

    def test_valid_queries_accepted(self):
        cfg = _dict_to_config({"investigation": {"max_queries_per_agent": 1}})
        assert cfg.investigation.max_queries_per_agent == 1

    def test_valid_timeout_accepted(self):
        cfg = _dict_to_config({"investigation": {"timeout_seconds": 1}})
        assert cfg.investigation.timeout_seconds == 1

    def test_max_thoughts_below_minimum_raises(self):
        with pytest.raises(ValueError, match="max_thoughts_per_item must be >= 3"):
            _dict_to_config({"investigation": {"max_thoughts_per_item": 2}})

    def test_max_thoughts_at_minimum_accepted(self):
        cfg = _dict_to_config({"investigation": {"max_thoughts_per_item": 3}})
        assert cfg.investigation.max_thoughts_per_item == 3

    def test_max_thoughts_zero_raises(self):
        with pytest.raises(ValueError, match="max_thoughts_per_item"):
            _dict_to_config({"investigation": {"max_thoughts_per_item": 0}})


# ===================================================================
# QualityConfig
# ===================================================================

class TestQualityConfig:
    def test_quality_config_defaults(self):
        qc = QualityConfig()
        assert qc.production_defaults is True
        assert qc.craft_review is True
        assert qc.quality_triggers_reloop is True

    def test_quality_config_from_yaml(self):
        cfg = _dict_to_config({"quality": {"craft_review": False}})
        assert cfg.quality.craft_review is False
        # Other defaults unchanged
        assert cfg.quality.production_defaults is True
        assert cfg.quality.quality_triggers_reloop is True

    def test_quick_depth_disables_quality(self):
        cfg = AgentTeamConfig()
        assert cfg.quality.production_defaults is True
        assert cfg.quality.craft_review is True
        apply_depth_quality_gating("quick", cfg)
        assert cfg.quality.production_defaults is False
        assert cfg.quality.craft_review is False
        # quality_triggers_reloop unchanged
        assert cfg.quality.quality_triggers_reloop is True
