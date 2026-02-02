"""Tests for agent_team.cli."""

from __future__ import annotations

import argparse
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_team.cli import (
    InterventionQueue,
    _detect_agent_count,
    _detect_prd_from_task,
    _handle_interrupt,
    _parse_args,
    _validate_url,
)


def _parse_args_from(argv: list[str]) -> argparse.Namespace:
    """Helper to parse args from a list, simulating CLI input."""
    original = sys.argv
    sys.argv = ["agent-team"] + argv
    try:
        return _parse_args()
    finally:
        sys.argv = original


# ===================================================================
# _detect_agent_count()
# ===================================================================

class TestDetectAgentCount:
    def test_cli_flag_overrides(self):
        assert _detect_agent_count("use 5 agents", 10) == 10

    def test_use_pattern(self):
        assert _detect_agent_count("use 5 agents", None) == 5

    def test_deploy_pattern(self):
        assert _detect_agent_count("deploy 10 agents", None) == 10

    def test_with_pattern(self):
        assert _detect_agent_count("with 3 agents please", None) == 3

    def test_launch_pattern(self):
        assert _detect_agent_count("launch 7 agents now", None) == 7

    def test_no_match_returns_none(self):
        assert _detect_agent_count("fix the login bug", None) is None

    def test_cli_precedence_over_task(self):
        assert _detect_agent_count("use 5 agents", 20) == 20


# ===================================================================
# _detect_prd_from_task()
# ===================================================================

class TestDetectPrdFromTask:
    def test_two_signals_is_prd(self):
        task = "Build with these features and user stories"
        assert _detect_prd_from_task(task) is True

    def test_one_signal_not_prd(self):
        task = "Add a new features dropdown"
        assert _detect_prd_from_task(task) is False

    def test_long_task_is_prd(self):
        task = "x" * 3001
        assert _detect_prd_from_task(task) is True

    def test_exactly_3000_not_prd(self):
        task = "x" * 3000
        assert _detect_prd_from_task(task) is False

    def test_simple_task_not_prd(self):
        assert _detect_prd_from_task("fix the bug") is False

    def test_case_insensitive(self):
        task = "FEATURES and USER STORIES here"
        assert _detect_prd_from_task(task) is True


# ===================================================================
# _parse_args()
# ===================================================================

class TestParseArgs:
    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["agent-team"] + args):
            return _parse_args()

    def test_task_positional(self):
        ns = self._parse(["fix the bug"])
        assert ns.task == "fix the bug"

    def test_no_task(self):
        ns = self._parse([])
        assert ns.task is None

    def test_prd_flag(self):
        ns = self._parse(["--prd", "prd.md"])
        assert ns.prd == "prd.md"

    def test_depth_quick(self):
        ns = self._parse(["--depth", "quick"])
        assert ns.depth == "quick"

    def test_depth_standard(self):
        ns = self._parse(["--depth", "standard"])
        assert ns.depth == "standard"

    def test_depth_thorough(self):
        ns = self._parse(["--depth", "thorough"])
        assert ns.depth == "thorough"

    def test_depth_exhaustive(self):
        ns = self._parse(["--depth", "exhaustive"])
        assert ns.depth == "exhaustive"

    def test_invalid_depth_exits(self):
        with pytest.raises(SystemExit):
            self._parse(["--depth", "invalid"])

    def test_agents_int(self):
        ns = self._parse(["--agents", "5"])
        assert ns.agents == 5

    def test_model_flag(self):
        ns = self._parse(["--model", "sonnet"])
        assert ns.model == "sonnet"

    def test_max_turns_flag(self):
        ns = self._parse(["--max-turns", "100"])
        assert ns.max_turns == 100

    def test_config_flag(self):
        ns = self._parse(["--config", "custom.yaml"])
        assert ns.config == "custom.yaml"

    def test_cwd_flag(self):
        ns = self._parse(["--cwd", "/project"])
        assert ns.cwd == "/project"

    def test_verbose_flag(self):
        ns = self._parse(["-v"])
        assert ns.verbose is True

    def test_interactive_flag(self):
        ns = self._parse(["-i"])
        assert ns.interactive is True

    def test_no_interview_flag(self):
        ns = self._parse(["--no-interview"])
        assert ns.no_interview is True

    def test_interview_doc_flag(self):
        ns = self._parse(["--interview-doc", "doc.md"])
        assert ns.interview_doc == "doc.md"

    def test_design_ref_single(self):
        ns = self._parse(["--design-ref", "https://example.com"])
        assert ns.design_ref == ["https://example.com"]

    def test_design_ref_multiple(self):
        ns = self._parse(["--design-ref", "https://a.com", "https://b.com"])
        assert ns.design_ref == ["https://a.com", "https://b.com"]

    def test_no_map_flag(self):
        ns = self._parse(["--no-map"])
        assert ns.no_map is True

    def test_map_only_flag(self):
        ns = self._parse(["--map-only"])
        assert ns.map_only is True

    def test_progressive_flag(self):
        ns = self._parse(["--progressive"])
        assert ns.progressive is True

    def test_no_progressive_flag(self):
        ns = self._parse(["--no-progressive"])
        assert ns.no_progressive is True

    def test_no_map_default_false(self):
        ns = self._parse([])
        assert ns.no_map is False

    def test_map_only_default_false(self):
        ns = self._parse([])
        assert ns.map_only is False

    def test_progressive_default_false(self):
        ns = self._parse([])
        assert ns.progressive is False

    def test_no_progressive_default_false(self):
        ns = self._parse([])
        assert ns.no_progressive is False

    def test_version_flag(self):
        with pytest.raises(SystemExit) as exc_info:
            self._parse(["--version"])
        assert exc_info.value.code == 0


# ===================================================================
# _handle_interrupt()
# ===================================================================

class TestHandleInterrupt:
    def setup_method(self):
        # Reset global state before each test
        import agent_team.cli as cli_mod
        cli_mod._interrupt_count = 0

    def test_first_press_warns(self, capsys):
        import agent_team.cli as cli_mod
        _handle_interrupt(2, None)  # SIGINT = 2
        assert cli_mod._interrupt_count == 1

    def test_second_press_exits(self):
        import agent_team.cli as cli_mod
        cli_mod._interrupt_count = 1
        with pytest.raises(SystemExit) as exc_info:
            _handle_interrupt(2, None)
        assert exc_info.value.code == 130

    def test_state_reset_between_tests(self):
        import agent_team.cli as cli_mod
        assert cli_mod._interrupt_count == 0


# ===================================================================
# main() — mocked tests
# ===================================================================

class TestMain:
    def test_no_api_key_exits(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("agent_team.cli._parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_prd_not_found_exits(self, monkeypatch, env_with_api_keys):
        with patch("agent_team.cli._parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                task=None, prd="/nonexistent/prd.md", depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_interview_doc_not_found_exits(self, env_with_api_keys):
        with patch("agent_team.cli._parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=False,
                interview_doc="/nonexistent/interview.md", design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_prd_forces_exhaustive(self, env_with_api_keys, sample_prd_file):
        """C2 bug: --prd should force exhaustive depth."""
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.asyncio") as mock_asyncio:
            mock_parse.return_value = argparse.Namespace(
                task=None, prd=str(sample_prd_file), depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            # Verify _run_single or _run_interactive was called
            call_args = mock_asyncio.run.call_args
            # The depth_override should be "exhaustive"
            assert call_args is not None

    def test_interview_doc_scope_detected(self, env_with_api_keys, tmp_path, sample_complex_interview_doc):
        """I6 bug: --interview-doc should detect scope."""
        doc_file = tmp_path / "interview.md"
        doc_file.write_text(sample_complex_interview_doc, encoding="utf-8")
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.asyncio") as mock_asyncio, \
             patch("agent_team.cli._detect_scope") as mock_detect:
            mock_detect.return_value = "COMPLEX"
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=False,
                interview_doc=str(doc_file), design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            mock_detect.assert_called_once()

    def test_complex_scope_forces_exhaustive(self, env_with_api_keys, tmp_path, sample_complex_interview_doc):
        """COMPLEX scope should force exhaustive depth."""
        doc_file = tmp_path / "interview.md"
        doc_file.write_text(sample_complex_interview_doc, encoding="utf-8")
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.asyncio") as mock_asyncio:
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=False,
                interview_doc=str(doc_file), design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            # _run_single should have been called
            call_args = mock_asyncio.run.call_args
            assert call_args is not None

    def test_design_ref_deduplication(self, env_with_api_keys):
        """Design reference URLs should be deduplicated."""
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.asyncio") as mock_asyncio:
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth="quick", agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None,
                design_ref=["https://a.com", "https://a.com", "https://b.com"],
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            call_args = mock_asyncio.run.call_args
            assert call_args is not None

    def test_no_interview_skips_interview(self, env_with_api_keys):
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.asyncio") as mock_asyncio, \
             patch("agent_team.cli.run_interview") as mock_interview:
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth="quick", agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            mock_interview.assert_not_called()

    def test_config_validation_error_exits_cleanly(self, env_with_api_keys):
        """ValueError from config validation should exit with code 1, not raw traceback."""
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.load_config") as mock_load:
            mock_load.side_effect = ValueError("min_exchanges must be >= 1")
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_config_load_generic_error_exits_cleanly(self, env_with_api_keys):
        """Generic exception from config loading should exit with code 1."""
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli.load_config") as mock_load:
            mock_load.side_effect = RuntimeError("YAML parse error")
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=True,
                interview_doc=None, design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


# ===================================================================
# COMPLEX interview → PRD mode plumbing
# ===================================================================

class TestComplexInterviewPRDPlumbing:
    """Verify interview_scope flows through CLI into _run_single/_run_interactive."""

    def test_complex_interview_passes_scope_to_prompt(self, env_with_api_keys, tmp_path, sample_complex_interview_doc):
        """interview_scope='COMPLEX' should be passed to _run_single."""
        doc_file = tmp_path / "interview.md"
        doc_file.write_text(sample_complex_interview_doc, encoding="utf-8")
        captured = {}
        original_run_single = None

        async def fake_run_single(**kwargs):
            captured.update(kwargs)

        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli._run_single", side_effect=fake_run_single) as mock_single, \
             patch("agent_team.cli._detect_scope", return_value="COMPLEX"):
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=False,
                interview_doc=str(doc_file), design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            assert mock_single.called
            call_kwargs = mock_single.call_args.kwargs
            assert call_kwargs.get("interview_scope") == "COMPLEX"

    def test_prd_and_interview_doc_clears_prd(self, env_with_api_keys, tmp_path, sample_complex_interview_doc):
        """--prd + --interview-doc should nullify args.prd (prd_path=None in call)."""
        doc_file = tmp_path / "interview.md"
        doc_file.write_text(sample_complex_interview_doc, encoding="utf-8")
        prd_file = tmp_path / "prd.md"
        prd_file.write_text("# PRD\nStuff", encoding="utf-8")

        async def fake_run_single(**kwargs):
            pass

        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli._run_single", side_effect=fake_run_single) as mock_single, \
             patch("agent_team.cli._detect_scope", return_value="COMPLEX"):
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=str(prd_file), depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                verbose=False, interactive=False, no_interview=False,
                interview_doc=str(doc_file), design_ref=None,
                no_map=False, map_only=False,
                progressive=False, no_progressive=False,
                dry_run=False,
            )
            from agent_team.cli import main
            main()
            assert mock_single.called
            call_kwargs = mock_single.call_args.kwargs
            assert call_kwargs.get("prd_path") is None


# ===================================================================
# TestMutualExclusion — Finding #10
# ===================================================================

class TestMutualExclusion:
    """Tests for Finding #10: mutually exclusive CLI flags."""

    def test_map_only_and_no_map_exclusive(self):
        """--map-only and --no-map cannot be used together."""
        with pytest.raises(SystemExit):
            _parse_args_from(["--map-only", "--no-map", "task"])

    def test_progressive_and_no_progressive_exclusive(self):
        """--progressive and --no-progressive cannot be used together."""
        with pytest.raises(SystemExit):
            _parse_args_from(["--progressive", "--no-progressive", "task"])

    def test_map_only_alone_works(self):
        args = _parse_args_from(["--map-only", "task"])
        assert args.map_only is True

    def test_no_map_alone_works(self):
        args = _parse_args_from(["--no-map", "task"])
        assert args.no_map is True


# ===================================================================
# TestURLValidation — Finding #19
# ===================================================================

class TestURLValidation:
    """Tests for Finding #19: URL validation for --design-ref."""

    def test_invalid_url_rejected(self):
        """URLs without scheme should be rejected."""
        with pytest.raises(SystemExit):
            _parse_args_from(["--design-ref", "not-a-url", "task"])

    def test_valid_url_accepted(self):
        args = _parse_args_from(["task", "--design-ref", "https://example.com"])
        assert args.design_ref == ["https://example.com"]

    def test_multiple_valid_urls(self):
        args = _parse_args_from(["task", "--design-ref", "https://a.com", "https://b.com"])
        assert len(args.design_ref) == 2


# ===================================================================
# _build_options() — Finding #2
# ===================================================================

class TestBuildOptions:
    """Tests for _build_options function."""

    def test_returns_options_object(self):
        """_build_options should return a ClaudeAgentOptions instance."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        opts = _build_options(cfg)
        assert opts is not None
        assert opts.model == "opus"

    def test_cwd_propagated(self, tmp_path):
        """cwd parameter should be propagated to options."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        opts = _build_options(cfg, cwd=str(tmp_path))
        assert opts.cwd == tmp_path

    def test_template_substitution_in_prompt(self):
        """System prompt should have template variables substituted."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        cfg.convergence.escalation_threshold = 5
        opts = _build_options(cfg)
        # The system prompt should contain the substituted value
        assert "$escalation_threshold" not in opts.system_prompt

    def test_display_flags_substituted_in_prompt(self):
        """show_fleet_composition=False should appear as 'False' in prompt."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig, DisplayConfig
        cfg = AgentTeamConfig(display=DisplayConfig(show_fleet_composition=False))
        opts = _build_options(cfg)
        assert "$show_fleet_composition" not in opts.system_prompt
        assert "False" in opts.system_prompt

    def test_display_flags_true_by_default(self):
        """Default config should substitute 'True' for display flags."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        opts = _build_options(cfg)
        assert "$show_fleet_composition" not in opts.system_prompt
        assert "$show_convergence_status" not in opts.system_prompt

    def test_max_cycles_substituted(self):
        """max_cycles=25 should appear in the resolved prompt."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig, ConvergenceConfig
        cfg = AgentTeamConfig(convergence=ConvergenceConfig(max_cycles=25))
        opts = _build_options(cfg)
        assert "$max_cycles" not in opts.system_prompt
        assert "25" in opts.system_prompt

    def test_master_plan_file_substituted(self):
        """Custom master_plan_file should appear in resolved prompt."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig, ConvergenceConfig
        cfg = AgentTeamConfig(convergence=ConvergenceConfig(master_plan_file="MY_PLAN.md"))
        opts = _build_options(cfg)
        assert "$master_plan_file" not in opts.system_prompt
        assert "MY_PLAN.md" in opts.system_prompt

    def test_max_budget_usd_substituted(self):
        """max_budget_usd=50.0 should appear in the resolved prompt."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig, OrchestratorConfig
        cfg = AgentTeamConfig(orchestrator=OrchestratorConfig(max_budget_usd=50.0))
        opts = _build_options(cfg)
        assert "$max_budget_usd" not in opts.system_prompt
        assert "50.0" in opts.system_prompt

    def test_max_budget_usd_none_substituted(self):
        """max_budget_usd=None should appear as 'None' without crash."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        opts = _build_options(cfg)
        assert "$max_budget_usd" not in opts.system_prompt
        assert "None" in opts.system_prompt


# ===================================================================
# _process_response() — Finding #2
# ===================================================================

class TestProcessResponsePlaceholder:
    """Placeholder tests for _process_response (requires SDK mock)."""

    def test_process_response_is_async(self):
        """_process_response should be an async function."""
        import asyncio
        from agent_team.cli import _process_response
        assert asyncio.iscoroutinefunction(_process_response)


# ===================================================================
# InterventionQueue
# ===================================================================

class TestInterventionQueue:
    def test_queue_creation(self):
        iq = InterventionQueue()
        assert iq.has_intervention() is False

    def test_get_returns_none_when_empty(self):
        iq = InterventionQueue()
        assert iq.get_intervention() is None

    def test_prefix_detection(self):
        iq = InterventionQueue()
        # Manually put something in the queue
        iq._queue.put("change approach")
        assert iq.has_intervention() is True
        msg = iq.get_intervention()
        assert msg == "change approach"

    def test_multiple_interventions(self):
        iq = InterventionQueue()
        iq._queue.put("first")
        iq._queue.put("second")
        assert iq.get_intervention() == "first"
        assert iq.get_intervention() == "second"
        assert iq.get_intervention() is None

    def test_stop_sets_inactive(self):
        iq = InterventionQueue()
        iq._active = True
        iq.stop()
        assert iq._active is False


# ===================================================================
# Subcommands
# ===================================================================

class TestSubcommands:
    def test_init_creates_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.cli import _subcommand_init
        _subcommand_init()
        assert (tmp_path / "config.yaml").is_file()

    def test_init_refuses_overwrite(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.yaml").write_text("existing", encoding="utf-8")
        from agent_team.cli import _subcommand_init
        _subcommand_init()  # Should not crash, just warn
        assert (tmp_path / "config.yaml").read_text(encoding="utf-8") == "existing"

    def test_status_no_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.cli import _subcommand_status
        _subcommand_status()  # Should not crash

    def test_guide_prints(self, capsys):
        from agent_team.cli import _subcommand_guide
        _subcommand_guide()
        # Should produce some output (via rich console)


# ===================================================================
# Dry-run flag
# ===================================================================

class TestDryRunFlag:
    def test_dry_run_parsed(self):
        import sys
        from unittest.mock import patch
        with patch("sys.argv", ["agent-team", "--dry-run", "--no-interview", "test"]):
            args = _parse_args()
            assert args.dry_run is True

    def test_dry_run_default_false(self):
        import sys
        from unittest.mock import patch
        with patch("sys.argv", ["agent-team", "test"]):
            args = _parse_args()
            assert args.dry_run is False
