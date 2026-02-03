"""Tests for convergence health check (Agent 2)."""
from __future__ import annotations

import pytest

from agent_team.state import ConvergenceReport


class TestConvergenceReport:
    def test_defaults(self):
        r = ConvergenceReport()
        assert r.total_requirements == 0
        assert r.checked_requirements == 0
        assert r.review_cycles == 0
        assert r.convergence_ratio == 0.0
        assert r.review_fleet_deployed is False
        assert r.health == "unknown"

    def test_healthy_state(self):
        r = ConvergenceReport(
            total_requirements=10,
            checked_requirements=10,
            review_cycles=3,
            convergence_ratio=1.0,
            review_fleet_deployed=True,
            health="healthy",
        )
        assert r.health == "healthy"
        assert r.review_fleet_deployed is True

    def test_failed_state_zero_cycles(self):
        r = ConvergenceReport(
            total_requirements=20,
            checked_requirements=0,
            review_cycles=0,
            convergence_ratio=0.0,
            review_fleet_deployed=False,
            health="failed",
        )
        assert r.health == "failed"
        assert r.review_fleet_deployed is False

    def test_degraded_state(self):
        r = ConvergenceReport(
            total_requirements=20,
            checked_requirements=12,
            review_cycles=2,
            convergence_ratio=0.6,
            review_fleet_deployed=True,
            health="degraded",
        )
        assert r.health == "degraded"
        assert r.convergence_ratio == pytest.approx(0.6)
