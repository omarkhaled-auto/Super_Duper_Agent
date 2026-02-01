"""Tests for agent_team.__init__."""

import re


def test_version_is_semver():
    from agent_team import __version__
    assert __version__ == "0.1.0"
    assert re.match(r"^\d+\.\d+\.\d+", __version__)


def test_main_is_callable():
    from agent_team import main
    assert callable(main)


def test_all_exports():
    import agent_team
    assert hasattr(agent_team, "__all__")
    assert set(agent_team.__all__) == {"main", "__version__"}
