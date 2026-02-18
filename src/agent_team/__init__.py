"""Agent Team — Convergence-driven multi-agent orchestration system."""

__version__ = "0.1.0"

from .cli import main
from . import audit_team, milestone_manager, quality_checks, wiring

__all__ = ["main", "__version__", "audit_team", "milestone_manager", "quality_checks", "wiring"]
