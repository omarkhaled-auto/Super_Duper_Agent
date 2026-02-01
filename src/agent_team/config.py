"""Configuration loading and validation for Agent Team."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorConfig:
    model: str = "opus"
    max_turns: int = 500
    permission_mode: str = "acceptEdits"


@dataclass
class DepthConfig:
    default: str = "standard"
    auto_detect: bool = True
    keyword_map: dict[str, list[str]] = field(default_factory=lambda: {
        "quick": ["quick", "fast", "simple", "just"],
        "thorough": ["thorough", "thoroughly", "careful", "carefully", "deep", "detailed"],
        "exhaustive": [
            "exhaustive", "exhaustively", "comprehensive",
            "comprehensively", "complete",
        ],
    })


@dataclass
class ConvergenceConfig:
    max_cycles: int = 10
    escalation_threshold: int = 3
    max_escalation_depth: int = 2
    requirements_dir: str = ".agent-team"
    requirements_file: str = "REQUIREMENTS.md"
    master_plan_file: str = "MASTER_PLAN.md"


@dataclass
class AgentConfig:
    model: str = "opus"
    enabled: bool = True


@dataclass
class MCPServerConfig:
    enabled: bool = True


@dataclass
class InterviewConfig:
    enabled: bool = True
    model: str = "opus"
    max_exchanges: int = 50


@dataclass
class DisplayConfig:
    show_cost: bool = True
    show_tools: bool = True
    show_fleet_composition: bool = True
    show_convergence_status: bool = True
    verbose: bool = False


@dataclass
class AgentTeamConfig:
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    depth: DepthConfig = field(default_factory=DepthConfig)
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    interview: InterviewConfig = field(default_factory=InterviewConfig)
    agents: dict[str, AgentConfig] = field(default_factory=lambda: {
        name: AgentConfig()
        for name in (
            "planner", "researcher", "architect", "task_assigner",
            "code_writer", "code_reviewer", "test_runner",
            "security_auditor", "debugger",
        )
    })
    mcp_servers: dict[str, MCPServerConfig] = field(default_factory=lambda: {
        "firecrawl": MCPServerConfig(),
        "context7": MCPServerConfig(),
    })
    display: DisplayConfig = field(default_factory=DisplayConfig)


# ---------------------------------------------------------------------------
# Depth detection
# ---------------------------------------------------------------------------

DEPTH_AGENT_COUNTS: dict[str, dict[str, tuple[int, int]]] = {
    "quick": {
        "planning": (1, 2), "research": (0, 1), "architecture": (0, 1),
        "coding": (1, 1), "review": (1, 2), "testing": (1, 1),
    },
    "standard": {
        "planning": (3, 5), "research": (2, 3), "architecture": (1, 2),
        "coding": (2, 3), "review": (2, 3), "testing": (1, 2),
    },
    "thorough": {
        "planning": (5, 8), "research": (3, 5), "architecture": (2, 3),
        "coding": (3, 6), "review": (3, 5), "testing": (2, 3),
    },
    "exhaustive": {
        "planning": (8, 10), "research": (5, 8), "architecture": (3, 4),
        "coding": (5, 10), "review": (5, 8), "testing": (3, 5),
    },
}


def detect_depth(task: str, config: AgentTeamConfig) -> str:
    """Detect depth level from task keywords. Returns the most intensive match.

    Uses word-boundary matching to avoid substring false positives
    (e.g. "adjustment" should not match "just").
    """
    if not config.depth.auto_detect:
        return config.depth.default
    task_lower = task.lower()
    # Check from most intensive to least
    for level in ("exhaustive", "thorough", "quick"):
        keywords = config.depth.keyword_map.get(level, [])
        if any(re.search(rf"\b{re.escape(kw)}\b", task_lower) for kw in keywords):
            return level
    return config.depth.default


def get_agent_counts(depth: str) -> dict[str, tuple[int, int]]:
    """Return (min, max) agent counts per phase for the given depth."""
    return DEPTH_AGENT_COUNTS.get(depth, DEPTH_AGENT_COUNTS["standard"])


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _dict_to_config(data: dict[str, Any]) -> AgentTeamConfig:
    """Convert a raw dict (from YAML) into an AgentTeamConfig."""
    cfg = AgentTeamConfig()

    if "orchestrator" in data:
        o = data["orchestrator"]
        cfg.orchestrator = OrchestratorConfig(
            model=o.get("model", cfg.orchestrator.model),
            max_turns=o.get("max_turns", cfg.orchestrator.max_turns),
            permission_mode=o.get("permission_mode", cfg.orchestrator.permission_mode),
        )

    if "depth" in data:
        d = data["depth"]
        cfg.depth = DepthConfig(
            default=d.get("default", cfg.depth.default),
            auto_detect=d.get("auto_detect", cfg.depth.auto_detect),
            keyword_map=d.get("keyword_map", cfg.depth.keyword_map),
        )

    if "convergence" in data:
        c = data["convergence"]
        cfg.convergence = ConvergenceConfig(
            max_cycles=c.get("max_cycles", cfg.convergence.max_cycles),
            escalation_threshold=c.get("escalation_threshold", cfg.convergence.escalation_threshold),
            max_escalation_depth=c.get("max_escalation_depth", cfg.convergence.max_escalation_depth),
            requirements_dir=c.get("requirements_dir", cfg.convergence.requirements_dir),
            requirements_file=c.get("requirements_file", cfg.convergence.requirements_file),
            master_plan_file=c.get("master_plan_file", cfg.convergence.master_plan_file),
        )

    if "interview" in data:
        iv = data["interview"]
        cfg.interview = InterviewConfig(
            enabled=iv.get("enabled", cfg.interview.enabled),
            model=iv.get("model", cfg.interview.model),
            max_exchanges=iv.get("max_exchanges", cfg.interview.max_exchanges),
        )

    if "agents" in data:
        for name, agent_data in data["agents"].items():
            if isinstance(agent_data, dict):
                cfg.agents[name] = AgentConfig(
                    model=agent_data.get("model", "opus"),
                    enabled=agent_data.get("enabled", True),
                )

    if "mcp_servers" in data:
        for name, server_data in data["mcp_servers"].items():
            if isinstance(server_data, dict):
                cfg.mcp_servers[name] = MCPServerConfig(
                    enabled=server_data.get("enabled", True),
                )

    if "display" in data:
        d = data["display"]
        cfg.display = DisplayConfig(
            show_cost=d.get("show_cost", cfg.display.show_cost),
            show_tools=d.get("show_tools", cfg.display.show_tools),
            show_fleet_composition=d.get("show_fleet_composition", cfg.display.show_fleet_composition),
            show_convergence_status=d.get("show_convergence_status", cfg.display.show_convergence_status),
            verbose=d.get("verbose", cfg.display.verbose),
        )

    return cfg


def load_config(
    config_path: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AgentTeamConfig:
    """Load configuration from YAML files with CLI overrides.

    Search order:
    1. Explicit config_path (if provided)
    2. ./config.yaml (cwd)
    3. ~/.agent-team/config.yaml (user home fallback)
    4. Built-in defaults
    """
    raw: dict[str, Any] = {}

    search_paths: list[Path] = []
    if config_path:
        search_paths.append(Path(config_path))
    search_paths.append(Path.cwd() / "config.yaml")
    search_paths.append(Path.home() / ".agent-team" / "config.yaml")

    for path in search_paths:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            raw = _deep_merge(raw, loaded)
            break  # Use first found file

    # Apply CLI overrides
    if cli_overrides:
        raw = _deep_merge(raw, cli_overrides)

    return _dict_to_config(raw)
