"""Tests for agent_team.interviewer."""

from __future__ import annotations

import pytest

from agent_team.config import AgentTeamConfig, InterviewConfig
from agent_team.interviewer import (
    EXIT_PHRASES,
    INTERVIEWER_SYSTEM_PROMPT,
    InterviewResult,
    _detect_scope,
    _estimate_scope_from_spec,
    _is_interview_exit,
    _NEGATION_WORDS,
    _get_interview_phase,
    _build_exchange_prompt,
    _build_continuation_prompt,
    _build_exit_confirmation_prompt,
)


# ===================================================================
# Constants
# ===================================================================

class TestConstants:
    def test_exit_phrases_not_empty(self):
        assert len(EXIT_PHRASES) > 0

    def test_exit_phrases_all_lowercase(self):
        for phrase in EXIT_PHRASES:
            assert phrase == phrase.lower(), f"EXIT_PHRASES should be lowercase: {phrase}"

    def test_negation_words_complete(self):
        expected = {"not", "no", "don't", "dont", "won't", "wont", "can't", "cant", "never", "isn't", "isnt"}
        assert _NEGATION_WORDS == expected


# ===================================================================
# _is_interview_exit()
# ===================================================================

class TestIsInterviewExit:
    @pytest.mark.parametrize("phrase", EXIT_PHRASES)
    def test_exact_match(self, phrase):
        assert _is_interview_exit(phrase) is True

    def test_punctuation_handling(self):
        assert _is_interview_exit("I'm done.") is True
        assert _is_interview_exit("let's go!") is True
        assert _is_interview_exit("proceed?") is True

    def test_whitespace(self):
        assert _is_interview_exit("  i'm done  ") is True

    def test_case_insensitive(self):
        assert _is_interview_exit("I'M DONE") is True
        assert _is_interview_exit("Let's Go") is True
        assert _is_interview_exit("LGTM") is True

    def test_in_longer_sentence(self):
        assert _is_interview_exit("yeah I'm done with the questions") is True

    def test_negation_not_done(self):
        assert _is_interview_exit("I'm not done") is False

    def test_negation_dont(self):
        assert _is_interview_exit("don't proceed yet") is False

    def test_negation_cant(self):
        assert _is_interview_exit("can't go ahead right now") is False

    def test_negation_never(self):
        assert _is_interview_exit("never ready for this") is False

    def test_far_away_negation_still_triggers(self):
        # Negation more than 3 words before the phrase should NOT block exit
        assert _is_interview_exit("I am not sure about this but I'm done") is True

    def test_empty_string(self):
        assert _is_interview_exit("") is False

    def test_unrelated_text(self):
        assert _is_interview_exit("tell me about the database schema") is False

    def test_start_building_exact(self):
        assert _is_interview_exit("start building") is True

    def test_ship_it_exact(self):
        assert _is_interview_exit("ship it") is True

    def test_good_to_go(self):
        assert _is_interview_exit("good to go") is True

    def test_looks_good(self):
        assert _is_interview_exit("looks good") is True

    def test_lgtm(self):
        assert _is_interview_exit("lgtm") is True


# ===================================================================
# _detect_scope()
# ===================================================================

class TestDetectScope:
    def test_simple_scope(self):
        doc = "# Task Brief\nScope: SIMPLE\n"
        assert _detect_scope(doc) == "SIMPLE"

    def test_medium_scope(self):
        doc = "# Feature Brief\nScope: MEDIUM\n"
        assert _detect_scope(doc) == "MEDIUM"

    def test_complex_scope(self):
        doc = "# PRD\nScope: COMPLEX\n"
        assert _detect_scope(doc) == "COMPLEX"

    def test_case_insensitive(self):
        doc = "scope: complex\n"
        assert _detect_scope(doc) == "COMPLEX"

    def test_markdown_bold(self):
        """I11 bug: **Scope:** COMPLEX should work."""
        doc = "**Scope:** COMPLEX\n"
        assert _detect_scope(doc) == "COMPLEX"

    def test_hash_prefix(self):
        doc = "## Scope: MEDIUM\n"
        assert _detect_scope(doc) == "MEDIUM"

    def test_no_header_returns_medium(self):
        doc = "# Task Brief\nSome content without scope\n"
        assert _detect_scope(doc) == "MEDIUM"

    def test_empty_string_returns_medium(self):
        assert _detect_scope("") == "MEDIUM"

    def test_invalid_value_returns_medium(self):
        doc = "Scope: INVALID\n"
        assert _detect_scope(doc) == "MEDIUM"

    def test_multiple_headers_first_wins(self):
        doc = "Scope: SIMPLE\nScope: COMPLEX\n"
        assert _detect_scope(doc) == "SIMPLE"


# ===================================================================
# InterviewResult dataclass
# ===================================================================

class TestInterviewResult:
    def test_all_fields_accessible(self):
        r = InterviewResult(
            doc_content="content",
            doc_path="/path/to/doc.md",
            scope="MEDIUM",
            exchange_count=5,
            cost=1.23,
        )
        assert r.doc_content == "content"
        assert r.doc_path == "/path/to/doc.md"
        assert r.scope == "MEDIUM"
        assert r.exchange_count == 5
        assert r.cost == 1.23


# ===================================================================
# _build_interview_options()
# ===================================================================

class TestBuildInterviewOptions:
    def test_uses_config_model(self):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig(interview=InterviewConfig(model="haiku"))
        opts = _build_interview_options(cfg)
        assert opts.model == "haiku"

    def test_system_prompt_is_interviewer(self):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig()
        opts = _build_interview_options(cfg)
        assert opts.system_prompt == INTERVIEWER_SYSTEM_PROMPT

    def test_max_turns_from_config(self):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig(interview=InterviewConfig(max_exchanges=10))
        opts = _build_interview_options(cfg)
        assert opts.max_turns == 40  # max_exchanges * 4

    def test_cwd_passed(self, tmp_path):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig()
        opts = _build_interview_options(cfg, cwd=str(tmp_path))
        assert opts.cwd == tmp_path

    def test_max_thinking_tokens_passed_when_set(self):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig(interview=InterviewConfig(max_thinking_tokens=8192))
        opts = _build_interview_options(cfg)
        assert opts.max_thinking_tokens == 8192

    def test_max_thinking_tokens_not_passed_when_none(self):
        from agent_team.interviewer import _build_interview_options
        cfg = AgentTeamConfig()
        opts = _build_interview_options(cfg)
        assert getattr(opts, "max_thinking_tokens", None) is None


# ===================================================================
# _detect_scope() — scope detection from document content (Finding #2)
# ===================================================================

class TestDetectScopeFromContent:
    """Additional tests for _detect_scope with varied document content."""

    def test_simple_scope_detection(self):
        """Simple task doc should detect as SIMPLE."""
        doc = "# Task Brief: Fix button\nScope: SIMPLE\nDate: 2025-01-01\n"
        result = _detect_scope(doc)
        assert result == "SIMPLE"

    def test_complex_prd_scope_detection(self):
        """Complex PRD-like text should detect as COMPLEX."""
        doc = (
            "# PRD: Full SaaS Application\n"
            "Scope: COMPLEX\n"
            "Date: 2025-01-01\n\n"
            "## Executive Summary\n"
            "Build a full SaaS application with user authentication, "
            "payment processing with Stripe, admin dashboard, "
            "multi-tenant architecture, real-time notifications, "
            "REST API, GraphQL endpoint, database migrations, "
            "CI/CD pipeline, and comprehensive testing suite.\n"
        )
        result = _detect_scope(doc)
        assert result == "COMPLEX"

    def test_scope_value_always_valid(self):
        """_detect_scope should always return one of the three valid values."""
        for doc in [
            "Scope: SIMPLE\n",
            "Scope: MEDIUM\n",
            "Scope: COMPLEX\n",
            "No scope header here\n",
            "",
        ]:
            result = _detect_scope(doc)
            assert result in ("SIMPLE", "MEDIUM", "COMPLEX")


# ===================================================================
# InterviewResult — additional dataclass tests (Finding #2)
# ===================================================================

class TestInterviewResultExtended:
    """Extended tests for InterviewResult dataclass."""

    def test_creation_with_all_fields(self):
        result = InterviewResult(
            doc_content="# Interview\nTest content",
            doc_path="/some/path/INTERVIEW.md",
            scope="MODERATE",
            exchange_count=5,
            cost=0.50,
        )
        assert result.doc_content == "# Interview\nTest content"
        assert result.doc_path == "/some/path/INTERVIEW.md"
        assert result.scope == "MODERATE"
        assert result.exchange_count == 5
        assert result.cost == 0.50

    def test_empty_doc_content(self):
        result = InterviewResult(
            doc_content="",
            doc_path="/path/INTERVIEW.md",
            scope="SIMPLE",
            exchange_count=0,
            cost=0.0,
        )
        assert result.doc_content == ""
        assert result.exchange_count == 0

    def test_zero_cost(self):
        result = InterviewResult(
            doc_content="content",
            doc_path="/path/INTERVIEW.md",
            scope="MEDIUM",
            exchange_count=3,
            cost=0.0,
        )
        assert result.cost == 0.0


# ===================================================================
# run_interview() — async function check (Finding #2)
# ===================================================================

class TestRunInterview:
    """Tests for run_interview async function."""

    def test_run_interview_is_async(self):
        """run_interview should be an async function."""
        import asyncio
        from agent_team.interviewer import run_interview
        assert asyncio.iscoroutinefunction(run_interview)


# ===================================================================
# Interview phase detection
# ===================================================================

class TestInterviewPhases:
    def test_discovery_first_exchange(self):
        assert _get_interview_phase(1, 3) == "DISCOVERY"

    def test_discovery_at_half(self):
        assert _get_interview_phase(1, 4) == "DISCOVERY"
        assert _get_interview_phase(2, 4) == "DISCOVERY"

    def test_refinement_after_half(self):
        assert _get_interview_phase(2, 3) == "REFINEMENT"
        assert _get_interview_phase(3, 4) == "REFINEMENT"

    def test_refinement_at_min(self):
        assert _get_interview_phase(3, 3) == "REFINEMENT"

    def test_ready_after_min(self):
        assert _get_interview_phase(4, 3) == "READY"
        assert _get_interview_phase(10, 3) == "READY"

    def test_zero_min_always_ready(self):
        assert _get_interview_phase(0, 0) == "READY"
        assert _get_interview_phase(1, 0) == "READY"

    def test_min_one(self):
        assert _get_interview_phase(1, 1) == "REFINEMENT"
        assert _get_interview_phase(2, 1) == "READY"


# ===================================================================
# Exchange prompt building
# ===================================================================

class TestBuildExchangePrompt:
    def test_discovery_includes_sections(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY")
        assert "My Current Understanding" in prompt
        assert "What I Found in the Codebase" in prompt
        assert "Questions" in prompt

    def test_discovery_forbids_finalization(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY")
        assert "Do NOT suggest finalizing" in prompt

    def test_refinement_includes_sections(self):
        prompt = _build_exchange_prompt("hello", 2, 3, "REFINEMENT")
        assert "Updated Understanding" in prompt
        assert "What I Propose" in prompt
        assert "Remaining Questions" in prompt

    def test_ready_allows_finalization(self):
        prompt = _build_exchange_prompt("hello", 4, 3, "READY")
        assert "Final Understanding" in prompt
        assert "Proposed Approach" in prompt

    def test_includes_user_message(self):
        prompt = _build_exchange_prompt("my specific question", 1, 3, "DISCOVERY")
        assert "my specific question" in prompt

    def test_includes_exchange_count(self):
        prompt = _build_exchange_prompt("hello", 2, 3, "REFINEMENT")
        assert "Exchange 2" in prompt

    def test_includes_phase_label(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY")
        assert "Phase: DISCOVERY" in prompt

    def test_exploration_requirement(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY")
        assert "Glob" in prompt or "Grep" in prompt or "Read" in prompt or "tools" in prompt.lower()

    def test_discovery_no_understanding_skips_section(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY", require_understanding=False)
        assert "My Current Understanding" not in prompt

    def test_discovery_no_exploration_skips_tools(self):
        prompt = _build_exchange_prompt("hello", 1, 3, "DISCOVERY", require_exploration=False)
        assert "Glob" not in prompt and "Grep" not in prompt and "Read" not in prompt

    def test_refinement_no_understanding_skips_section(self):
        prompt = _build_exchange_prompt("hello", 2, 3, "REFINEMENT", require_understanding=False)
        assert "Updated Understanding" not in prompt

    def test_refinement_no_exploration_skips_tools(self):
        prompt = _build_exchange_prompt("hello", 2, 3, "REFINEMENT", require_exploration=False)
        assert "exploring the codebase" not in prompt


# ===================================================================
# Continuation prompt
# ===================================================================

class TestContinuationPrompt:
    def test_includes_exchange_count(self):
        prompt = _build_continuation_prompt(1, 3)
        assert "1" in prompt
        assert "3" in prompt

    def test_includes_remaining(self):
        prompt = _build_continuation_prompt(1, 3)
        assert "2" in prompt  # 3 - 1 = 2 remaining

    def test_asks_questions(self):
        prompt = _build_continuation_prompt(1, 3)
        assert "question" in prompt.lower()

    def test_does_not_finalize(self):
        prompt = _build_continuation_prompt(1, 3)
        assert "Do NOT finalize" in prompt or "not" in prompt.lower()


# ===================================================================
# Exit confirmation prompt
# ===================================================================

class TestExitConfirmationPrompt:
    def test_includes_summary_request(self):
        prompt = _build_exit_confirmation_prompt()
        assert "summary" in prompt.lower()

    def test_includes_scope_assessment(self):
        prompt = _build_exit_confirmation_prompt()
        assert "scope" in prompt.lower() or "SIMPLE" in prompt or "MEDIUM" in prompt or "COMPLEX" in prompt

    def test_includes_confirmation_request(self):
        prompt = _build_exit_confirmation_prompt()
        assert "yes" in prompt.lower()


# ===================================================================
# Min exchange config integration
# ===================================================================

class TestMinExchangeConfigIntegration:
    def test_interview_config_has_min_exchanges(self):
        from agent_team.config import InterviewConfig
        cfg = InterviewConfig()
        assert cfg.min_exchanges == 3

    def test_custom_min_exchanges(self):
        from agent_team.config import InterviewConfig
        cfg = InterviewConfig(min_exchanges=5)
        assert cfg.min_exchanges == 5

    def test_system_prompt_has_mandatory_format(self):
        assert "MANDATORY RESPONSE FORMAT" in INTERVIEWER_SYSTEM_PROMPT

    def test_system_prompt_has_anti_patterns(self):
        assert "ANTI-PATTERN" in INTERVIEWER_SYSTEM_PROMPT or "anti-pattern" in INTERVIEWER_SYSTEM_PROMPT.lower()

    def test_system_prompt_has_interview_phases(self):
        assert "INTERVIEW PHASES" in INTERVIEWER_SYSTEM_PROMPT or "DISCOVERY" in INTERVIEWER_SYSTEM_PROMPT


# ===================================================================
# Exit boundary tests (Tier 2/3a boundary)
# ===================================================================

class TestExitBoundary:
    """Test that exit phrase handling respects min_exchanges boundary correctly."""

    def test_phase_at_exactly_min_is_refinement(self):
        """At exactly min_exchanges, phase should be REFINEMENT (not READY)."""
        assert _get_interview_phase(3, 3) == "REFINEMENT"

    def test_phase_at_min_plus_one_is_ready(self):
        """At min_exchanges + 1, phase should be READY."""
        assert _get_interview_phase(4, 3) == "READY"

    def test_phase_below_min_is_not_ready(self):
        """Below min_exchanges, phase should never be READY."""
        for i in range(1, 4):
            assert _get_interview_phase(i, 3) != "READY"

    def test_continuation_prompt_at_boundary(self):
        """Continuation prompt at exactly min should have 0 remaining."""
        prompt = _build_continuation_prompt(3, 3)
        assert "0" in prompt  # 3 - 3 = 0 remaining

    def test_exit_confirmation_always_asks_for_yes(self):
        """Exit confirmation should always ask for explicit confirmation."""
        prompt = _build_exit_confirmation_prompt()
        assert "yes" in prompt.lower()


# ===================================================================
# _estimate_scope_from_spec()
# ===================================================================

class TestEstimateScopeFromSpec:
    """Tests for _estimate_scope_from_spec heuristic function."""

    def test_empty_string_returns_medium(self):
        assert _estimate_scope_from_spec("") == "MEDIUM"

    def test_short_spec_returns_simple(self):
        """A short spec with few features should return SIMPLE."""
        spec = "Build a hello world app.\n- Print hello\n- Exit cleanly\n"
        assert _estimate_scope_from_spec(spec) == "SIMPLE"

    def test_medium_spec(self):
        """A spec with >4 features should return MEDIUM."""
        lines = ["Feature line\n"] * 50
        bullets = ["- Feature {}\n".format(i) for i in range(5)]
        spec = "".join(lines + bullets)
        assert _estimate_scope_from_spec(spec) == "MEDIUM"

    def test_complex_spec_long_and_many_features(self):
        """A spec with >500 lines AND >8 features should return COMPLEX."""
        lines = ["Description line\n"] * 510
        bullets = ["- Feature {}\n".format(i) for i in range(10)]
        spec = "".join(lines + bullets)
        assert _estimate_scope_from_spec(spec) == "COMPLEX"

    def test_long_but_few_features_returns_medium(self):
        """A spec with >500 lines but <=8 features should return MEDIUM (lines > 200)."""
        lines = ["Description line\n"] * 510
        bullets = ["- Feature A\n", "- Feature B\n"]
        spec = "".join(lines + bullets)
        result = _estimate_scope_from_spec(spec)
        assert result == "MEDIUM"

    def test_short_but_many_features_returns_medium(self):
        """A spec with <=200 lines but >4 features should return MEDIUM."""
        bullets = ["- Feature {}\n".format(i) for i in range(6)]
        spec = "".join(bullets)
        assert _estimate_scope_from_spec(spec) == "MEDIUM"

    def test_numbered_items_count_as_features(self):
        """Numbered items (1. 2. etc.) should count as features."""
        items = ["{}. Feature item\n".format(i) for i in range(1, 6)]
        spec = "".join(items)
        assert _estimate_scope_from_spec(spec) == "MEDIUM"

    def test_headings_count_as_features(self):
        """Markdown headings should count as features."""
        headings = ["## Section {}\n".format(i) for i in range(6)]
        spec = "".join(headings)
        assert _estimate_scope_from_spec(spec) == "MEDIUM"

    def test_always_returns_valid_scope(self):
        """Return value is always one of SIMPLE, MEDIUM, COMPLEX."""
        for text in ["", "x", "x\n" * 1000, "- " * 100]:
            result = _estimate_scope_from_spec(text)
            assert result in ("SIMPLE", "MEDIUM", "COMPLEX")


# ===================================================================
# _detect_scope() with spec_text fallback
# ===================================================================

class TestDetectScopeWithSpecFallback:
    """Tests for _detect_scope with the spec_text fallback parameter."""

    def test_header_takes_priority_over_spec(self):
        """When Scope: header exists, spec_text fallback is not used."""
        doc = "Scope: SIMPLE\n"
        complex_spec = "".join(["line\n"] * 600 + ["- Feature\n"] * 10)
        assert _detect_scope(doc, spec_text=complex_spec) == "SIMPLE"

    def test_fallback_to_spec_when_no_header(self):
        """When no Scope: header exists and spec_text is provided, estimate from spec."""
        doc = "# Task Brief\nSome content without scope header\n"
        complex_spec = "".join(["line\n"] * 600 + ["- Feature\n"] * 10)
        result = _detect_scope(doc, spec_text=complex_spec)
        assert result == "COMPLEX"

    def test_backward_compat_no_spec(self):
        """Without spec_text, _detect_scope still defaults to MEDIUM when no header."""
        doc = "# No scope header here\n"
        assert _detect_scope(doc) == "MEDIUM"

    def test_empty_doc_with_spec_fallback(self):
        """Empty doc_content with spec_text should use the heuristic."""
        spec = "".join(["- Feature {}\n".format(i) for i in range(6)])
        result = _detect_scope("", spec_text=spec)
        assert result == "MEDIUM"

    def test_empty_doc_empty_spec(self):
        """Both empty should return MEDIUM."""
        assert _detect_scope("", spec_text="") == "MEDIUM"
