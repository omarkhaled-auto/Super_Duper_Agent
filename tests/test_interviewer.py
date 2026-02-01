"""Tests for agent_team.interviewer."""

from __future__ import annotations

import pytest

from agent_team.config import AgentTeamConfig, InterviewConfig
from agent_team.interviewer import (
    EXIT_PHRASES,
    INTERVIEWER_SYSTEM_PROMPT,
    InterviewResult,
    _detect_scope,
    _is_interview_exit,
    _NEGATION_WORDS,
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
