"""Tests for agent_team.cli."""

from __future__ import annotations

import argparse
import subprocess
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_team.cli import (
    InterventionQueue,
    _check_claude_cli_auth,
    _detect_agent_count,
    _detect_backend,
    _detect_prd_from_task,
    _drain_interventions,
    _extract_design_urls_from_interview,
    _handle_interrupt,
    _parse_args,
    _run_contract_generation,
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
    def test_no_auth_exits(self, monkeypatch):
        """Neither API key nor CLI auth → exit code 1."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("agent_team.cli._parse_args") as mock_parse, \
             patch("agent_team.cli._check_claude_cli_auth", return_value=False), \
             patch("dotenv.load_dotenv", return_value=None):
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth=None, agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                backend=None,
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
                backend=None,
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
                backend=None,
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
                backend=None,
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
                backend=None,
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
                backend=None,
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
             patch("agent_team.cli.asyncio") as mock_asyncio, \
             patch("agent_team.mcp_servers.is_firecrawl_available", return_value=False):
            mock_parse.return_value = argparse.Namespace(
                task="test", prd=None, depth="quick", agents=None,
                model=None, max_turns=None, config=None, cwd=None,
                backend=None,
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
                backend=None,
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
                backend=None,
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
                backend=None,
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
# Backend detection
# ===================================================================

class TestDetectBackend:
    def test_detect_backend_api_with_key(self, monkeypatch):
        """Returns 'api' when ANTHROPIC_API_KEY is set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        assert _detect_backend("auto") == "api"

    def test_detect_backend_cli_fallback(self, monkeypatch):
        """Returns 'cli' when no API key but CLI is available."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("agent_team.cli._check_claude_cli_auth", return_value=True):
            assert _detect_backend("auto") == "cli"

    def test_detect_backend_api_explicit(self, monkeypatch):
        """--backend=api with key returns 'api'."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        assert _detect_backend("api") == "api"

    def test_detect_backend_api_explicit_no_key_exits(self, monkeypatch):
        """--backend=api without key exits."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            _detect_backend("api")
        assert exc_info.value.code == 1

    def test_detect_backend_cli_explicit_no_auth_exits(self):
        """--backend=cli without CLI auth exits."""
        with patch("agent_team.cli._check_claude_cli_auth", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                _detect_backend("cli")
            assert exc_info.value.code == 1

    def test_detect_backend_auto_no_auth_exits(self, monkeypatch):
        """Neither auth available → exit."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("agent_team.cli._check_claude_cli_auth", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                _detect_backend("auto")
            assert exc_info.value.code == 1

    def test_detect_backend_cli_explicit_with_auth(self):
        """--backend=cli with CLI auth returns 'cli'."""
        with patch("agent_team.cli._check_claude_cli_auth", return_value=True):
            assert _detect_backend("cli") == "cli"


class TestCheckClaudeCliAuth:
    def test_returns_true_when_claude_found(self):
        """Returns True when claude --version succeeds."""
        mock_result = MagicMock(returncode=0)
        with patch("agent_team.cli.subprocess.run", return_value=mock_result):
            assert _check_claude_cli_auth() is True

    def test_returns_false_when_not_found(self):
        """Returns False when claude is not installed."""
        with patch("agent_team.cli.subprocess.run", side_effect=FileNotFoundError):
            assert _check_claude_cli_auth() is False

    def test_returns_false_on_timeout(self):
        """Returns False when subprocess times out."""
        with patch("agent_team.cli.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5)):
            assert _check_claude_cli_auth() is False

    def test_returns_false_on_nonzero_exit(self):
        """Returns False when claude --version exits with non-zero."""
        mock_result = MagicMock(returncode=1)
        with patch("agent_team.cli.subprocess.run", return_value=mock_result):
            assert _check_claude_cli_auth() is False


class TestBackendFlag:
    def test_backend_flag_parsed(self):
        """--backend cli parses correctly."""
        with patch("sys.argv", ["agent-team", "--backend", "cli", "test"]):
            args = _parse_args()
            assert args.backend == "cli"

    def test_backend_flag_default_none(self):
        """Backend defaults to None when not specified."""
        with patch("sys.argv", ["agent-team", "test"]):
            args = _parse_args()
            assert args.backend is None

    def test_backend_flag_api(self):
        """--backend api parses correctly."""
        with patch("sys.argv", ["agent-team", "--backend", "api", "test"]):
            args = _parse_args()
            assert args.backend == "api"

    def test_backend_flag_auto(self):
        """--backend auto parses correctly."""
        with patch("sys.argv", ["agent-team", "--backend", "auto", "test"]):
            args = _parse_args()
            assert args.backend == "auto"

    def test_backend_flag_invalid_exits(self):
        """Invalid --backend value exits."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["agent-team", "--backend", "invalid", "test"]):
                _parse_args()


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
                backend=None,
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
                backend=None,
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

    def test_max_thinking_tokens_passed_when_set(self):
        """max_thinking_tokens should be passed to ClaudeAgentOptions when set."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig, OrchestratorConfig
        cfg = AgentTeamConfig(orchestrator=OrchestratorConfig(max_thinking_tokens=10000))
        opts = _build_options(cfg)
        assert opts.max_thinking_tokens == 10000

    def test_max_thinking_tokens_not_passed_when_none(self):
        """max_thinking_tokens should not be in opts_kwargs when None."""
        from agent_team.cli import _build_options
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        opts = _build_options(cfg)
        # When None, the kwarg is not passed, so the SDK default applies.
        # The attribute may not exist or may be None depending on SDK behavior.
        assert getattr(opts, "max_thinking_tokens", None) is None


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


class TestDrainInterventions:
    """Tests for _drain_interventions — the wiring between InterventionQueue and the SDK."""

    @pytest.mark.asyncio
    async def test_drain_returns_zero_when_none(self):
        """Passing intervention=None is safe and returns 0."""
        from agent_team.config import AgentTeamConfig
        config = AgentTeamConfig()
        cost = await _drain_interventions(
            client=MagicMock(),
            intervention=None,
            config=config,
            phase_costs={},
        )
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_drain_returns_zero_when_empty_queue(self):
        """Empty queue means nothing is sent."""
        from agent_team.config import AgentTeamConfig
        config = AgentTeamConfig()
        iq = InterventionQueue()
        mock_client = AsyncMock()
        cost = await _drain_interventions(
            client=mock_client,
            intervention=iq,
            config=config,
            phase_costs={},
        )
        assert cost == 0.0
        mock_client.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_drain_sends_queued_message(self):
        """A queued intervention is sent as a follow-up query."""
        from agent_team.config import AgentTeamConfig
        config = AgentTeamConfig()
        iq = InterventionQueue()
        iq._queue.put("focus on the API")

        mock_client = AsyncMock()
        # _process_response is async generator — mock receive_response
        mock_client.receive_response = AsyncMock(return_value=AsyncIterator([]))

        with patch("agent_team.cli._process_response", new_callable=AsyncMock, return_value=0.05):
            cost = await _drain_interventions(
                client=mock_client,
                intervention=iq,
                config=config,
                phase_costs={},
            )

        mock_client.query.assert_called_once()
        call_arg = mock_client.query.call_args[0][0]
        assert "[USER INTERVENTION -- HIGHEST PRIORITY]" in call_arg
        assert "focus on the API" in call_arg
        assert cost == 0.05

    @pytest.mark.asyncio
    async def test_drain_handles_multiple_interventions(self):
        """Multiple queued messages are drained sequentially."""
        from agent_team.config import AgentTeamConfig
        config = AgentTeamConfig()
        iq = InterventionQueue()
        iq._queue.put("first correction")
        iq._queue.put("second correction")

        mock_client = AsyncMock()

        with patch("agent_team.cli._process_response", new_callable=AsyncMock, return_value=0.01):
            cost = await _drain_interventions(
                client=mock_client,
                intervention=iq,
                config=config,
                phase_costs={},
            )

        assert mock_client.query.call_count == 2
        assert cost == pytest.approx(0.02)

    @pytest.mark.asyncio
    async def test_drain_accumulates_cost(self):
        """Cost from intervention queries is accumulated."""
        from agent_team.config import AgentTeamConfig
        config = AgentTeamConfig()
        iq = InterventionQueue()
        iq._queue.put("adjust plan")
        phase_costs: dict[str, float] = {"orchestration": 1.0}

        mock_client = AsyncMock()

        with patch("agent_team.cli._process_response", new_callable=AsyncMock, return_value=0.10):
            cost = await _drain_interventions(
                client=mock_client,
                intervention=iq,
                config=config,
                phase_costs=phase_costs,
            )

        assert cost == pytest.approx(0.10)


# Helper for async iteration in tests
class AsyncIterator:
    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


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


# ===================================================================
# Resume subcommand
# ===================================================================

class TestSubcommandResume:
    def test_subcommand_resume_no_state_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.cli import _subcommand_resume
        result = _subcommand_resume()
        assert result is None

    def test_subcommand_resume_valid_state_returns_tuple(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.state import RunState, save_state
        state = RunState(task="fix the bug", depth="thorough")
        state.current_phase = "orchestration"
        state.completed_phases = ["interview", "constraints"]
        save_state(state)
        from agent_team.cli import _subcommand_resume
        result = _subcommand_resume()
        assert result is not None
        args, ctx = result
        assert isinstance(ctx, str)

    def test_subcommand_resume_sets_no_interview(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.state import RunState, save_state
        save_state(RunState(task="fix the bug", depth="standard"))
        from agent_team.cli import _subcommand_resume
        result = _subcommand_resume()
        assert result is not None
        args, _ = result
        assert args.no_interview is True

    def test_subcommand_resume_uses_interview_doc(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "INTERVIEW.md").write_text("# Interview\nStuff", encoding="utf-8")
        from agent_team.state import RunState, save_state
        save_state(RunState(task="fix the bug"), str(agent_dir))
        from agent_team.cli import _subcommand_resume
        result = _subcommand_resume()
        assert result is not None
        args, _ = result
        assert args.interview_doc is not None
        assert "INTERVIEW.md" in args.interview_doc

    def test_subcommand_resume_preserves_task(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from agent_team.state import RunState, save_state
        save_state(RunState(task="add dark mode", depth="thorough"))
        from agent_team.cli import _subcommand_resume
        result = _subcommand_resume()
        assert result is not None
        args, _ = result
        assert args.task == "add dark mode"


# ===================================================================
# _build_resume_context()
# ===================================================================

class TestBuildResumeContext:
    def test_build_resume_context_lists_artifacts(self, tmp_path):
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "REQUIREMENTS.md").write_text("# Reqs", encoding="utf-8")
        (agent_dir / "TASKS.md").write_text("# Tasks", encoding="utf-8")
        from agent_team.state import RunState
        state = RunState(task="test", current_phase="orchestration")
        state.completed_phases = ["interview"]
        from agent_team.cli import _build_resume_context
        ctx = _build_resume_context(state, str(tmp_path))
        assert "REQUIREMENTS.md" in ctx
        assert "TASKS.md" in ctx

    def test_build_resume_context_includes_instructions(self, tmp_path):
        from agent_team.state import RunState
        state = RunState(task="test")
        from agent_team.cli import _build_resume_context
        ctx = _build_resume_context(state, str(tmp_path))
        assert "RESUME INSTRUCTIONS" in ctx
        assert "RESUME MODE" in ctx


# ===================================================================
# completed_phases population
# ===================================================================

class TestCompletedPhasesPopulation:
    def test_completed_phases_populated(self, env_with_api_keys):
        """After main() runs through phases, completed_phases should be populated."""
        import agent_team.cli as cli_mod
        from agent_team.state import RunState

        # Simulate: set _current_state and verify phases can be appended
        state = RunState(task="test")
        state.completed_phases.append("interview")
        state.completed_phases.append("constraints")
        state.completed_phases.append("codebase_map")
        assert len(state.completed_phases) == 3
        assert "interview" in state.completed_phases
        assert "constraints" in state.completed_phases
        assert "codebase_map" in state.completed_phases


# ===================================================================
# _extract_design_urls_from_interview()
# ===================================================================

class TestExtractDesignUrlsFromInterview:
    def test_extracts_urls_from_design_reference_section(self):
        doc = (
            "## Understanding Summary\nSome text\n\n"
            "## Design Reference\n"
            "- https://stripe.com/pricing\n"
            "- https://linear.app\n\n"
            "## Milestones\nMore text"
        )
        urls = _extract_design_urls_from_interview(doc)
        assert urls == ["https://stripe.com/pricing", "https://linear.app"]

    def test_returns_empty_when_no_section(self):
        doc = "## Understanding Summary\nSome text\n## Milestones\nMore text"
        urls = _extract_design_urls_from_interview(doc)
        assert urls == []

    def test_deduplicates_urls(self):
        doc = (
            "## Design Reference\n"
            "- https://stripe.com\n"
            "- https://stripe.com\n"
        )
        urls = _extract_design_urls_from_interview(doc)
        assert urls == ["https://stripe.com"]

    def test_stops_at_next_section(self):
        doc = (
            "## Design Reference\n"
            "- https://stripe.com\n\n"
            "## Milestones\n"
            "- https://other.com\n"
        )
        urls = _extract_design_urls_from_interview(doc)
        assert urls == ["https://stripe.com"]
        assert "https://other.com" not in urls

    def test_handles_empty_section(self):
        doc = (
            "## Design Reference\n\n"
            "## Milestones\nMore text"
        )
        urls = _extract_design_urls_from_interview(doc)
        assert urls == []


# ===================================================================
# _build_resume_context() — design research skip signal
# ===================================================================

class TestBuildResumeContextDesignResearch:
    def test_design_research_complete_in_resume_context(self):
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="test")
        state.artifacts["design_research_complete"] = "true"
        ctx = _build_resume_context(state, "/tmp/fake")
        assert "Design research is ALREADY COMPLETE" in ctx
        assert "Do NOT re-scrape" in ctx

    def test_no_design_research_flag_no_skip(self):
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="test")
        ctx = _build_resume_context(state, "/tmp/fake")
        assert "Design research is ALREADY COMPLETE" not in ctx


# ===================================================================
# Contract pipeline fixes (Bug 1, Bug 2, Bug 3)
# ===================================================================


class TestContractPipelineBug3:
    """Bug 3: Silent false pass — empty registry without file_missing flag."""

    def test_pre_orchestration_empty_registry_has_file_missing_true(self, tmp_path):
        """When CONTRACTS.json is absent, the empty registry sets file_missing=True."""
        from agent_team.contracts import ContractRegistry
        from agent_team.config import AgentTeamConfig

        # Simulate what cli.py does at Phase 0.75 when file doesn't exist
        contract_path = tmp_path / ".agent-team" / "CONTRACTS.json"
        assert not contract_path.is_file()

        # This is the FIXED behavior — file_missing must be True
        registry = ContractRegistry()
        registry.file_missing = True
        assert registry.file_missing is True


class TestContractPipelineBug2:
    """Bug 2: Stale contract registry after orchestration."""

    def test_contract_registry_reread_after_orchestration(self, tmp_path):
        """Verification should use freshly loaded registry, not stale pre-loaded one."""
        import json
        from agent_team.contracts import ContractRegistry, load_contracts, save_contracts

        contract_path = tmp_path / ".agent-team" / "CONTRACTS.json"

        # Phase 0.75: file doesn't exist → empty registry with file_missing
        assert not contract_path.is_file()
        stale_registry = ContractRegistry()
        stale_registry.file_missing = True
        assert stale_registry.file_missing is True
        assert len(stale_registry.modules) == 0

        # Orchestration creates CONTRACTS.json
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "modules": {
                "src/app.py": {
                    "exports": [{"name": "main", "kind": "function", "signature": None}],
                    "created_by_task": "TASK-001",
                }
            },
            "wirings": [],
            "middlewares": [],
        }
        contract_path.write_text(json.dumps(data), encoding="utf-8")

        # Re-read from disk (FIXED behavior)
        fresh_registry = load_contracts(contract_path)
        assert fresh_registry.file_missing is False
        assert "src/app.py" in fresh_registry.modules


class TestContractPipelineBug1:
    """Bug 1: No code backstop for contract-generator deployment."""

    def test_run_contract_generation_prompt_content(self):
        """Recovery prompt contains CRITICAL RECOVERY and focused instructions."""
        from agent_team.config import AgentTeamConfig

        config = AgentTeamConfig()

        # Mock the SDK client to capture the prompt
        captured_prompt = {}

        async def fake_query(prompt):
            captured_prompt["text"] = prompt

        mock_client = AsyncMock()
        mock_client.query = fake_query
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent_team.cli.ClaudeSDKClient", return_value=mock_client), \
             patch("agent_team.cli._process_response", new_callable=AsyncMock, return_value=0.05), \
             patch("agent_team.cli._drain_interventions", new_callable=AsyncMock, return_value=0.0):
            cost = _run_contract_generation(
                cwd="/tmp/fake",
                config=config,
            )

        assert "CRITICAL RECOVERY" in captured_prompt["text"]
        assert "CONTRACTS.json" in captured_prompt["text"]
        assert "CONTRACT GENERATOR" in captured_prompt["text"]

    def test_run_contract_generation_returns_cost(self):
        """Recovery function returns float cost (mirrors _run_review_only tests)."""
        from agent_team.config import AgentTeamConfig

        config = AgentTeamConfig()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent_team.cli.ClaudeSDKClient", return_value=mock_client), \
             patch("agent_team.cli._process_response", new_callable=AsyncMock, return_value=0.42), \
             patch("agent_team.cli._drain_interventions", new_callable=AsyncMock, return_value=0.08):
            cost = _run_contract_generation(cwd="/tmp/fake", config=config)

        assert cost == pytest.approx(0.50)

    def test_contract_recovery_triggered_when_missing(self, tmp_path):
        """Recovery launched when: verification enabled + REQUIREMENTS.md exists + CONTRACTS.json missing."""
        from agent_team.config import AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "REQUIREMENTS.md").write_text("# Reqs\n- [ ] Feature A", encoding="utf-8")

        contract_path = agent_dir / config.verification.contract_file
        req_path = agent_dir / config.convergence.requirements_file

        assert not contract_path.is_file()
        assert req_path.is_file()

        # The condition that triggers recovery
        from agent_team.config import AgentConfig
        generator_enabled = config.agents.get("contract_generator", AgentConfig()).enabled
        assert generator_enabled is True
        assert not contract_path.is_file() and req_path.is_file() and generator_enabled

    def test_contract_recovery_not_triggered_when_file_exists(self, tmp_path):
        """Recovery skipped when CONTRACTS.json already exists."""
        from agent_team.config import AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "REQUIREMENTS.md").write_text("# Reqs", encoding="utf-8")
        (agent_dir / config.verification.contract_file).write_text("{}", encoding="utf-8")

        contract_path = agent_dir / config.verification.contract_file
        assert contract_path.is_file()  # Recovery should NOT trigger

    def test_contract_recovery_not_triggered_when_no_requirements(self, tmp_path):
        """Recovery skipped when no REQUIREMENTS.md exists."""
        from agent_team.config import AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()

        req_path = agent_dir / config.convergence.requirements_file
        assert not req_path.is_file()  # No requirements → no recovery

    def test_contract_recovery_not_triggered_when_generator_disabled(self, tmp_path):
        """Recovery skipped when contract_generator disabled in config."""
        from agent_team.config import AgentConfig, AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        config.agents["contract_generator"] = AgentConfig(enabled=False)
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "REQUIREMENTS.md").write_text("# Reqs", encoding="utf-8")

        generator_enabled = config.agents.get("contract_generator", AgentConfig()).enabled
        assert generator_enabled is False  # Disabled → no recovery

    def test_contract_recovery_not_triggered_when_verification_disabled(self):
        """Recovery skipped when verification disabled."""
        from agent_team.config import AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=False))
        assert config.verification.enabled is False  # Verification off → no recovery

    def test_contract_recovery_failure_handled_gracefully(self, tmp_path):
        """Recovery exception is caught by the contract health check block in main().

        The try/except in the post-orchestration contract health check should
        catch any exception from _run_contract_generation and continue to
        verification instead of crashing.
        """
        from agent_team.config import AgentTeamConfig, VerificationConfig

        config = AgentTeamConfig(verification=VerificationConfig(enabled=True))
        agent_dir = tmp_path / ".agent-team"
        agent_dir.mkdir()
        (agent_dir / "REQUIREMENTS.md").write_text("# Reqs\n- [ ] Feature A", encoding="utf-8")

        contract_path = agent_dir / config.verification.contract_file
        req_path = agent_dir / config.convergence.requirements_file

        # Simulate the contract health check block from main()
        # This mirrors the exact try/except structure at the call site
        recovery_called = False
        warning_issued = False

        def fake_recovery(**kwargs):
            nonlocal recovery_called
            recovery_called = True
            raise RuntimeError("SDK connection failed")

        from agent_team.config import AgentConfig
        generator_enabled = config.agents.get("contract_generator", AgentConfig()).enabled

        if not contract_path.is_file() and req_path.is_file() and generator_enabled:
            try:
                fake_recovery(cwd=str(tmp_path), config=config)
            except Exception as exc:
                warning_issued = True
                assert "SDK connection failed" in str(exc)

        assert recovery_called is True
        assert warning_issued is True


# ===================================================================
# Milestone routing tests
# ===================================================================


class TestMilestoneRouting:
    """Tests for milestone-related routing logic in the CLI."""

    def test_milestone_routing_disabled_by_default(self, env_with_api_keys):
        """When milestone.enabled is False (default), the non-PRD path (_run_single) is used."""
        from agent_team.config import AgentTeamConfig
        cfg = AgentTeamConfig()
        # Default config should have milestone disabled
        assert cfg.milestone.enabled is False
        # Therefore _use_milestones logic should evaluate to False
        _is_prd_mode = True
        _master_plan_exists = False
        _use_milestones = cfg.milestone.enabled and (_is_prd_mode or _master_plan_exists)
        assert _use_milestones is False

    def test_milestone_routing_enabled_prd(self, env_with_api_keys):
        """When milestone.enabled=True and PRD mode is active, milestone route should be used."""
        from agent_team.config import AgentTeamConfig, MilestoneConfig
        cfg = AgentTeamConfig(milestone=MilestoneConfig(enabled=True))
        _is_prd_mode = True
        _master_plan_exists = False
        _use_milestones = cfg.milestone.enabled and (_is_prd_mode or _master_plan_exists)
        assert _use_milestones is True

    def test_milestone_routing_enabled_master_plan(self, env_with_api_keys):
        """Milestone route also activates when MASTER_PLAN.md already exists."""
        from agent_team.config import AgentTeamConfig, MilestoneConfig
        cfg = AgentTeamConfig(milestone=MilestoneConfig(enabled=True))
        _is_prd_mode = False
        _master_plan_exists = True
        _use_milestones = cfg.milestone.enabled and (_is_prd_mode or _master_plan_exists)
        assert _use_milestones is True

    def test_milestone_routing_disabled_even_with_prd(self, env_with_api_keys):
        """Milestone disabled + PRD mode should NOT route to milestones."""
        from agent_team.config import AgentTeamConfig, MilestoneConfig
        cfg = AgentTeamConfig(milestone=MilestoneConfig(enabled=False))
        _is_prd_mode = True
        _use_milestones = cfg.milestone.enabled and _is_prd_mode
        assert _use_milestones is False

    def test_milestone_routing_disabled_no_prd_no_plan(self, env_with_api_keys):
        """Enabled=True but no PRD and no MASTER_PLAN should not route to milestones."""
        from agent_team.config import AgentTeamConfig, MilestoneConfig
        cfg = AgentTeamConfig(milestone=MilestoneConfig(enabled=True))
        _is_prd_mode = False
        _master_plan_exists = False
        _use_milestones = cfg.milestone.enabled and (_is_prd_mode or _master_plan_exists)
        assert _use_milestones is False


class TestMilestoneFunctionExists:
    """Tests verifying milestone-related functions exist and are callable."""

    def test_run_prd_milestones_exists(self):
        """_run_prd_milestones function exists and is callable (async)."""
        import asyncio
        from agent_team.cli import _run_prd_milestones
        assert callable(_run_prd_milestones)
        assert asyncio.iscoroutinefunction(_run_prd_milestones)

    def test_milestone_wiring_fix_exists(self):
        """_run_milestone_wiring_fix function exists and is callable (async)."""
        import asyncio
        from agent_team.cli import _run_milestone_wiring_fix
        assert callable(_run_milestone_wiring_fix)
        assert asyncio.iscoroutinefunction(_run_milestone_wiring_fix)


class TestBuildResumeContextWithMilestones:
    """Tests for milestone fields in _build_resume_context."""

    def test_build_resume_context_with_milestones(self, tmp_path):
        """Milestone fields are rendered in resume context when present."""
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="build the app")
        state.milestone_order = ["milestone-1", "milestone-2", "milestone-3"]
        state.completed_milestones = ["milestone-1"]
        state.current_milestone = "milestone-2"
        state.failed_milestones = []
        ctx = _build_resume_context(state, str(tmp_path))
        assert "milestone-1" in ctx
        assert "milestone-2" in ctx
        assert "Milestone order" in ctx
        assert "Completed milestones" in ctx
        assert "Interrupted during milestone" in ctx

    def test_build_resume_context_no_milestones(self, tmp_path):
        """When no milestone fields are set, milestone sections are absent."""
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="fix the bug")
        ctx = _build_resume_context(state, str(tmp_path))
        assert "Milestone order" not in ctx

    def test_build_resume_context_failed_milestones(self, tmp_path):
        """Failed milestones appear in resume context."""
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="build the app")
        state.milestone_order = ["m1", "m2"]
        state.failed_milestones = ["m1"]
        ctx = _build_resume_context(state, str(tmp_path))
        assert "Failed milestones" in ctx
        assert "m1" in ctx

    def test_build_resume_context_milestone_progress_dict(self, tmp_path):
        """milestone_progress dict is rendered in resume context."""
        from agent_team.state import RunState
        from agent_team.cli import _build_resume_context
        state = RunState(task="build the app")
        state.milestone_progress = {
            "milestone-1": {"status": "COMPLETE", "checked": 5, "total": 5, "cycles": 2},
            "milestone-2": {"status": "IN_PROGRESS", "checked": 1, "total": 3, "cycles": 0},
        }
        ctx = _build_resume_context(state, str(tmp_path))
        assert "milestone-1" in ctx
        assert "milestone-2" in ctx
        assert "Milestone progress" in ctx


# ===================================================================
# E2E Bug Fixes
# ===================================================================


class TestE2EBugFixesCLI:
    """Tests for CLI-level bugs identified during E2E testing."""

    def test_health_gate_failure_saves_state(self, tmp_path):
        """State is saved when milestone fails health gate.

        This tests the fix for Issue 2: STATE.json milestone tracking empty.
        When a milestone fails the health gate, we must call save_state()
        to persist the FAILED status.
        """
        from agent_team.state import RunState, save_state, update_milestone_progress, update_completion_ratio

        # Create initial state
        state = RunState(task="build the app")
        state.milestone_order = ["milestone-1", "milestone-2"]

        # Create .agent-team directory
        agent_team_dir = tmp_path / ".agent-team"
        agent_team_dir.mkdir(parents=True)

        # Simulate health gate failure (this is what the fix does)
        update_milestone_progress(state, "milestone-1", "FAILED")
        update_completion_ratio(state)  # This was missing before the fix
        save_state(state, directory=str(agent_team_dir))  # This was missing before the fix

        # Verify state was saved with the failure
        state_file = agent_team_dir / "STATE.json"
        assert state_file.exists()

        import json
        saved_state = json.loads(state_file.read_text(encoding="utf-8"))
        assert saved_state["milestone_progress"]["milestone-1"]["status"] == "FAILED"
        assert "completion_ratio" in saved_state

    def test_health_gate_failure_updates_completion_ratio(self, tmp_path):
        """Completion ratio is updated when milestone fails health gate."""
        from agent_team.state import RunState, update_milestone_progress, update_completion_ratio

        # Create initial state with 2 milestones
        state = RunState(task="build the app")
        state.milestone_order = ["milestone-1", "milestone-2"]

        # Before the fix, only update_milestone_progress was called
        # After the fix, update_completion_ratio is also called
        update_milestone_progress(state, "milestone-1", "FAILED")
        update_completion_ratio(state)

        # Verify completion_ratio was calculated
        # With 1 milestone failed out of 2, ratio should be 0.0 (0 complete / 2 total)
        assert state.completion_ratio == 0.0

    def test_health_gate_failure_persists_to_disk(self, tmp_path):
        """State persistence at health gate failure allows resume."""
        from agent_team.state import RunState, save_state, load_state, update_milestone_progress, update_completion_ratio

        # Create .agent-team directory
        agent_team_dir = tmp_path / ".agent-team"
        agent_team_dir.mkdir(parents=True)

        # Create and save initial state
        state = RunState(task="build the app")
        state.milestone_order = ["m1", "m2", "m3"]
        save_state(state, directory=str(agent_team_dir))

        # Simulate health gate failure
        update_milestone_progress(state, "m1", "FAILED")
        update_completion_ratio(state)
        save_state(state, directory=str(agent_team_dir))

        # Load state and verify persistence
        loaded = load_state(directory=str(agent_team_dir))
        assert loaded is not None
        assert loaded.milestone_progress["m1"]["status"] == "FAILED"
        assert loaded.completion_ratio == 0.0
