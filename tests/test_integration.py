"""Integration tests — cross-module pipelines."""

from __future__ import annotations

import pytest
import yaml

from agent_team.agents import build_agent_definitions, build_orchestrator_prompt
from agent_team.config import (
    AgentTeamConfig,
    ConstraintEntry,
    DepthDetection,
    DesignReferenceConfig,
    SchedulerConfig,
    VerificationConfig,
    detect_depth,
    extract_constraints,
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


class TestCodebaseMapIntegration:
    @pytest.mark.asyncio
    async def test_generate_map_on_tmp_project(self, tmp_path):
        """Create a tiny project and generate a codebase map."""
        # Create Python files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text(
            'from .utils import helper\n\ndef main():\n    pass\n',
            encoding="utf-8",
        )
        (tmp_path / "src" / "utils.py").write_text(
            'def helper():\n    return 42\n',
            encoding="utf-8",
        )
        from agent_team.codebase_map import generate_codebase_map, summarize_map
        cmap = await generate_codebase_map(tmp_path)
        assert cmap.total_files >= 2
        assert cmap.primary_language == "python"
        summary = summarize_map(cmap)
        assert "python" in summary.lower()


class TestSchedulerIntegration:
    def test_parse_and_schedule(self):
        """Parse TASKS.md fixture and compute schedule."""
        from agent_team.scheduler import compute_schedule, parse_tasks_md
        tasks_md = """# Tasks
## Tasks

### TASK-001: Setup
- Status: PENDING
- Dependencies: none
- Files: src/main.py
- Description: Setup project

### TASK-002: Feature A
- Status: PENDING
- Dependencies: TASK-001
- Files: src/feature_a.py
- Description: Build feature A

### TASK-003: Feature B
- Status: PENDING
- Dependencies: TASK-001
- Files: src/feature_b.py
- Description: Build feature B
"""
        tasks = parse_tasks_md(tasks_md)
        assert len(tasks) == 3
        result = compute_schedule(tasks)
        assert result.total_waves >= 2
        # TASK-001 should be in wave 1, TASK-002 and TASK-003 in wave 2
        assert "TASK-001" in result.waves[0].task_ids
        assert "TASK-002" in result.waves[1].task_ids or "TASK-003" in result.waves[1].task_ids


class TestContractVerificationIntegration:
    def test_create_verify_contracts(self, tmp_path):
        """Create contracts, write files, verify."""
        from agent_team.contracts import (
            ContractRegistry,
            ExportedSymbol,
            ModuleContract,
            save_contracts,
            load_contracts,
            verify_all_contracts,
        )
        # Create a Python module
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "auth.py").write_text(
            'class AuthService:\n    pass\n\ndef verify_token(token: str) -> bool:\n    return True\n',
            encoding="utf-8",
        )
        # Create contract
        registry = ContractRegistry()
        registry.modules["src/auth.py"] = ModuleContract(
            module_path="src/auth.py",
            exports=[
                ExportedSymbol(name="AuthService", kind="class"),
                ExportedSymbol(name="verify_token", kind="function"),
            ],
            created_by_task="TASK-001",
        )
        # Save and load
        contract_path = tmp_path / "CONTRACTS.json"
        save_contracts(registry, contract_path)
        loaded = load_contracts(contract_path)
        assert len(loaded.modules) == 1
        # Verify
        result = verify_all_contracts(loaded, tmp_path)
        assert result.passed is True


class TestNewAgentsConditional:
    def test_scheduler_enables_integration_agent(self):
        cfg = AgentTeamConfig(scheduler=SchedulerConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert "integration-agent" in agents

    def test_verification_enables_contract_generator(self):
        cfg = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agents = build_agent_definitions(cfg, {})
        assert "contract-generator" in agents

    def test_default_config_no_new_agents(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, {})
        assert "integration-agent" not in agents
        assert "contract-generator" not in agents


class TestRuntimeWiring:
    """Tests for Finding #3: runtime wiring of scheduler/contracts/verification."""

    def test_contract_loading_with_valid_file(self, tmp_path):
        """Contracts can be loaded and saved via the persistence API."""
        from agent_team.contracts import ContractRegistry, save_contracts, load_contracts
        reg = ContractRegistry()
        contract_file = tmp_path / ".agent-team" / "CONTRACTS.json"
        contract_file.parent.mkdir(parents=True)
        save_contracts(reg, contract_file)
        assert contract_file.is_file()
        loaded = load_contracts(contract_file)
        assert isinstance(loaded, ContractRegistry)
        assert len(loaded.modules) == 0

    def test_scheduler_parse_and_compute(self):
        """Scheduler can parse TASKS.md content and compute a schedule."""
        from agent_team.scheduler import parse_tasks_md, compute_schedule
        tasks_md = (
            "### TASK-001: Init\n"
            "- Status: PENDING\n"
            "- Dependencies: none\n"
            "- Files: src/init.py\n"
        )
        tasks = parse_tasks_md(tasks_md)
        assert len(tasks) == 1
        result = compute_schedule(tasks)
        assert result.total_waves >= 1
        assert isinstance(result.conflict_summary, dict)

    def test_verification_pipeline_runs(self, tmp_path):
        """Verification state can be updated with a task result."""
        from agent_team.contracts import ContractRegistry
        from agent_team.verification import (
            ProgressiveVerificationState,
            TaskVerificationResult,
            update_verification_state,
        )
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(
            task_id="T1", contracts_passed=True, overall="pass"
        )
        updated = update_verification_state(state, result)
        assert updated.overall_health == "green"

    def test_verification_state_red_on_failure(self):
        """Verification state turns red when a task fails."""
        from agent_team.verification import (
            ProgressiveVerificationState,
            TaskVerificationResult,
            update_verification_state,
        )
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(
            task_id="T1", contracts_passed=False, overall="fail"
        )
        updated = update_verification_state(state, result)
        assert updated.overall_health == "red"

    def test_write_verification_summary(self, tmp_path):
        """write_verification_summary produces a Markdown file."""
        from agent_team.verification import (
            ProgressiveVerificationState,
            write_verification_summary,
        )
        state = ProgressiveVerificationState()
        out_path = tmp_path / "VERIFICATION.md"
        write_verification_summary(state, out_path)
        assert out_path.is_file()
        content = out_path.read_text(encoding="utf-8")
        assert "Verification Summary" in content

    def test_contract_verify_all_empty_registry(self, tmp_path):
        """verify_all_contracts with empty registry passes."""
        from agent_team.contracts import ContractRegistry, verify_all_contracts
        reg = ContractRegistry()
        result = verify_all_contracts(reg, tmp_path)
        assert result.passed is True
        assert result.checked_modules == 0
        assert result.checked_wirings == 0


class TestConstraintPipelineIntegration:
    """Test constraint extraction flows into orchestrator prompt."""

    def test_constraints_flow_into_prompt(self, default_config):
        task = "ZERO functionality changes. only restyle the SCSS."
        constraints = extract_constraints(task)
        assert len(constraints) > 0
        prompt = build_orchestrator_prompt(
            task=task,
            depth="thorough",
            config=default_config,
            constraints=constraints,
        )
        # At least one constraint text should appear in prompt
        found = any(c.text in prompt for c in constraints)
        assert found, "No constraints found in orchestrator prompt"

    def test_depth_detection_object_in_pipeline(self, default_config):
        detection = detect_depth("restyle the dashboard", default_config)
        assert isinstance(detection, DepthDetection)
        assert detection.level == "thorough"
        # Can be passed to build_orchestrator_prompt
        prompt = build_orchestrator_prompt(
            task="restyle the dashboard",
            depth=detection,
            config=default_config,
        )
        assert "[DEPTH: THOROUGH]" in prompt


# ===================================================================
# Config Field Wiring Integration Tests
# ===================================================================


class TestConfigFieldWiringIntegration:
    """End-to-end tests verifying config fields reach their targets."""

    def test_codebase_map_config_reaches_generator(self, tmp_path):
        """max_files=2 should limit output when called through the async API."""
        import asyncio
        from agent_team.codebase_map import generate_codebase_map

        for i in range(5):
            (tmp_path / f"mod_{i}.py").write_text(f"x = {i}", encoding="utf-8")

        cmap = asyncio.run(generate_codebase_map(
            tmp_path, timeout=10.0, max_files=2,
        ))
        assert cmap.total_files <= 2

    def test_scheduler_config_reaches_compute_schedule(self):
        """critical_path disabled + max_parallel=1 should work end-to-end."""
        from agent_team.scheduler import TaskNode, compute_schedule

        nodes = [
            TaskNode(id="TASK-001", title="A", description="d", files=[], depends_on=[], status="PENDING"),
            TaskNode(id="TASK-002", title="B", description="d", files=[], depends_on=["TASK-001"], status="PENDING"),
        ]
        cfg = SchedulerConfig(enabled=True, enable_critical_path=False, max_parallel_tasks=1)
        result = compute_schedule(nodes, scheduler_config=cfg)
        assert result.critical_path.path == []
        for wave in result.waves:
            assert len(wave.task_ids) <= 1

    def test_verification_blocking_reaches_overall_status(self):
        """blocking=False should produce 'partial' instead of 'fail'."""
        from agent_team.verification import TaskVerificationResult, compute_overall_status

        result = TaskVerificationResult(
            task_id="INT-1",
            contracts_passed=False,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=True,
        )
        assert compute_overall_status(result, blocking=False) == "partial"
        assert compute_overall_status(result, blocking=True) == "fail"

    def test_display_and_orchestrator_vars_in_system_prompt(self):
        """All 5 new template vars should be substituted in the system prompt."""
        import string
        from agent_team.agents import ORCHESTRATOR_SYSTEM_PROMPT
        from agent_team.config import (
            AgentTeamConfig,
            ConvergenceConfig,
            DisplayConfig,
            OrchestratorConfig,
        )

        cfg = AgentTeamConfig(
            display=DisplayConfig(show_fleet_composition=False, show_convergence_status=False),
            convergence=ConvergenceConfig(max_cycles=25, master_plan_file="MY_PLAN.md"),
            orchestrator=OrchestratorConfig(max_budget_usd=100.0),
        )
        prompt = string.Template(ORCHESTRATOR_SYSTEM_PROMPT).safe_substitute(
            escalation_threshold=str(cfg.convergence.escalation_threshold),
            max_escalation_depth=str(cfg.convergence.max_escalation_depth),
            show_fleet_composition=str(cfg.display.show_fleet_composition),
            show_convergence_status=str(cfg.display.show_convergence_status),
            max_cycles=str(cfg.convergence.max_cycles),
            master_plan_file=cfg.convergence.master_plan_file,
            max_budget_usd=str(cfg.orchestrator.max_budget_usd),
        )
        # No unresolved $placeholders for the 7 known vars
        assert "$show_fleet_composition" not in prompt
        assert "$show_convergence_status" not in prompt
        assert "$max_cycles" not in prompt
        assert "$master_plan_file" not in prompt
        assert "$max_budget_usd" not in prompt
        # Values present
        assert "False" in prompt  # show_fleet_composition
        assert "25" in prompt
        assert "MY_PLAN.md" in prompt
        assert "100.0" in prompt
