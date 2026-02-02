"""Configuration loading and validation for Agent Team."""

from __future__ import annotations

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
    max_budget_usd: float | None = None
    backend: str = "auto"  # "auto" | "api" | "cli"


@dataclass
class DepthConfig:
    default: str = "standard"
    auto_detect: bool = True
    keyword_map: dict[str, list[str]] = field(default_factory=lambda: {
        "quick": ["quick", "fast", "simple"],
        "thorough": [
            "thorough", "thoroughly", "careful", "carefully", "deep", "detailed",
            "refactor", "redesign", "restyle", "rearchitect", "overhaul",
            "rewrite", "restructure", "revamp", "modernize",
        ],
        "exhaustive": [
            "exhaustive", "exhaustively", "comprehensive",
            "comprehensively", "complete",
            "migrate", "migration", "replatform", "entire", "every", "whole",
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
    min_exchanges: int = 3
    require_understanding_summary: bool = True
    require_codebase_exploration: bool = True


def _validate_interview_config(cfg: InterviewConfig) -> None:
    if cfg.min_exchanges < 1:
        raise ValueError("min_exchanges must be >= 1")
    if cfg.min_exchanges > cfg.max_exchanges:
        raise ValueError("min_exchanges must be <= max_exchanges")


@dataclass
class DesignReferenceConfig:
    urls: list[str] = field(default_factory=list)
    depth: str = "full"  # "branding" | "screenshots" | "full"
    max_pages_per_site: int = 5


@dataclass
class DisplayConfig:
    show_cost: bool = True
    show_tools: bool = True
    show_fleet_composition: bool = True
    show_convergence_status: bool = True
    verbose: bool = False


@dataclass
class CodebaseMapConfig:
    enabled: bool = True
    max_files: int = 5000
    max_file_size_kb: int = 50       # Python files
    max_file_size_kb_ts: int = 100   # TS/JS files (codegen can be larger)
    timeout_seconds: int = 30
    exclude_patterns: list[str] = field(default_factory=lambda: [
        "node_modules", ".git", "__pycache__", "dist", "build", ".next", "venv",
    ])


@dataclass
class SchedulerConfig:
    enabled: bool = False             # opt-in
    max_parallel_tasks: int = 5
    conflict_strategy: str = "artificial-dependency"
    enable_context_scoping: bool = True
    enable_critical_path: bool = True


@dataclass
class VerificationConfig:
    enabled: bool = False             # opt-in
    contract_file: str = "CONTRACTS.json"
    verification_file: str = "VERIFICATION.md"
    blocking: bool = True
    run_lint: bool = True
    run_type_check: bool = True
    run_tests: bool = True


@dataclass
class ConstraintEntry:
    text: str
    category: str  # "prohibition" | "requirement" | "scope"
    source: str    # "task" | "interview"
    emphasis: int  # 1=normal, 2=caps, 3=caps+emphasis word


@dataclass
class DepthDetection:
    level: str
    source: str  # "keyword" | "scope" | "default" | "override"
    matched_keywords: list[str]
    explanation: str

    def __str__(self) -> str:
        return self.level

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.level == other
        if isinstance(other, DepthDetection):
            return self.level == other.level
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.level)

    def __getattr__(self, name: str):
        # Guard against recursion during copy/pickle/deepcopy: these
        # protocols probe for __reduce__, __getstate__, etc. before
        # __dict__ is populated, which would cause self.level to
        # re-enter __getattr__ infinitely.
        try:
            level = self.__dict__["level"]
        except KeyError:
            raise AttributeError(name) from None
        return getattr(level, name)


@dataclass
class AgentTeamConfig:
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    depth: DepthConfig = field(default_factory=DepthConfig)
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    interview: InterviewConfig = field(default_factory=InterviewConfig)
    design_reference: DesignReferenceConfig = field(default_factory=DesignReferenceConfig)
    codebase_map: CodebaseMapConfig = field(default_factory=CodebaseMapConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    # Agent keys use underscores (Python convention) in config files.
    # The SDK uses hyphens (e.g., "code-writer"). See agents.py for the mapping.
    agents: dict[str, AgentConfig] = field(default_factory=lambda: {
        name: AgentConfig()
        for name in (
            "planner", "researcher", "architect", "task_assigner",
            "code_writer", "code_reviewer", "test_runner",
            "security_auditor", "debugger",
            "integration_agent", "contract_generator",
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


def detect_depth(task: str, config: AgentTeamConfig) -> DepthDetection:
    """Detect depth level from task keywords. Returns a DepthDetection with metadata.

    Uses word-boundary matching to avoid substring false positives.
    The returned DepthDetection supports str() conversion and == comparison
    with strings for backwards compatibility.
    """
    if not config.depth.auto_detect:
        return DepthDetection(config.depth.default, "default", [], "Auto-detect disabled")
    task_lower = task.lower()
    for level in ("exhaustive", "thorough", "quick"):
        keywords = config.depth.keyword_map.get(level, [])
        matched = [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", task_lower)]
        if matched:
            return DepthDetection(level, "keyword", matched, f"Matched keywords: {matched}")
    return DepthDetection(config.depth.default, "default", [], "No keyword matches")


def get_agent_counts(depth: str) -> dict[str, tuple[int, int]]:
    """Return (min, max) agent counts per phase for the given depth."""
    return DEPTH_AGENT_COUNTS.get(depth, DEPTH_AGENT_COUNTS["standard"])


# ---------------------------------------------------------------------------
# Constraint extraction
# ---------------------------------------------------------------------------

_PROHIBITION_RE = re.compile(
    r"(?:^|[.!?;]\s*)((?:no|zero|never|don'?t|do\s+not|must\s+not|shall\s+not|cannot|can'?t)\s+.{5,200}?)(?:[.!?;]|$)",
    re.IGNORECASE | re.MULTILINE,
)
_REQUIREMENT_RE = re.compile(
    r"(?:^|[.!?;]\s*)((?:must|always|required|shall|need\s+to|have\s+to)\s+.{5,200}?)(?:[.!?;]|$)",
    re.IGNORECASE | re.MULTILINE,
)
_SCOPE_RE_CONSTRAINT = re.compile(
    r"(?:^|[.!?;]\s*)((?:only|limited\s+to|just\s+the|nothing\s+but|exclusively)\s+.{5,200}?)(?:[.!?;]|$)",
    re.IGNORECASE | re.MULTILINE,
)
_EMPHASIS_WORDS = {"zero", "never", "absolutely", "strictly", "critical", "crucial", "must"}

_FALSE_POSITIVE_PHRASES = frozenset({
    "cannot be overstated", "cannot thank", "cannot emphasize enough",
    "cannot stress enough", "cannot overstate", "must have seen",
    "must have been", "must be noted", "do not hesitate",
})


def _compute_emphasis(text: str, normalized: str, emphasis_words: set[str]) -> int:
    """Compute emphasis level for a constraint.

    Returns:
        1 = normal
        2 = ALL_CAPS or emphasis word present
        3 = ALL_CAPS + emphasis word
    """
    emphasis = 1
    is_all_caps = text != text.lower() and text.upper() == text
    has_emphasis_word = any(w in normalized for w in emphasis_words)

    if is_all_caps:
        emphasis = 2
    if has_emphasis_word:
        emphasis = max(emphasis, 2)
        if is_all_caps:
            emphasis = 3

    return emphasis


def extract_constraints(task: str, interview_doc: str | None = None) -> list[ConstraintEntry]:
    """Extract user constraints from task description and interview document."""
    constraints: list[ConstraintEntry] = []

    seen_texts: set[str] = set()

    def _add_constraints(text: str, source: str) -> None:
        for match in _PROHIBITION_RE.finditer(text):
            constraint_text = match.group(1).strip()
            normalized = constraint_text.lower()
            # Filter false positives
            if any(fp in normalized for fp in _FALSE_POSITIVE_PHRASES):
                continue
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                emphasis = _compute_emphasis(constraint_text, normalized, _EMPHASIS_WORDS)
                constraints.append(ConstraintEntry(constraint_text, "prohibition", source, emphasis))

        for match in _REQUIREMENT_RE.finditer(text):
            constraint_text = match.group(1).strip()
            normalized = constraint_text.lower()
            # Filter false positives
            if any(fp in normalized for fp in _FALSE_POSITIVE_PHRASES):
                continue
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                emphasis = _compute_emphasis(constraint_text, normalized, _EMPHASIS_WORDS)
                constraints.append(ConstraintEntry(constraint_text, "requirement", source, emphasis))

        for match in _SCOPE_RE_CONSTRAINT.finditer(text):
            constraint_text = match.group(1).strip()
            normalized = constraint_text.lower()
            # Filter false positives
            if any(fp in normalized for fp in _FALSE_POSITIVE_PHRASES):
                continue
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                emphasis = _compute_emphasis(constraint_text, normalized, _EMPHASIS_WORDS)
                constraints.append(ConstraintEntry(constraint_text, "scope", source, emphasis))

    _add_constraints(task, "task")
    if interview_doc:
        _add_constraints(interview_doc, "interview")

    return constraints


def format_constraints_block(constraints: list[ConstraintEntry]) -> str:
    """Format constraints as a prompt block for injection into agent prompts."""
    if not constraints:
        return ""
    lines = ["", "============================================================",
             "USER CONSTRAINTS (MANDATORY — VIOLATING THESE IS A FAILURE)",
             "============================================================", ""]
    for c in constraints:
        prefix = {"prohibition": "PROHIBITION", "requirement": "REQUIREMENT", "scope": "SCOPE"}.get(c.category, "CONSTRAINT")
        emphasis_marker = "!!!" if c.emphasis >= 3 else "!!" if c.emphasis >= 2 else ""
        lines.append(f"  [{prefix}] {emphasis_marker}{c.text}")
    lines.append("")
    return "\n".join(lines)


def parse_max_review_cycles(requirements_content: str) -> int:
    """Parse the maximum review_cycles value from REQUIREMENTS.md content."""
    matches = re.findall(r'\(review_cycles:\s*(\d+)\)', requirements_content)
    return max((int(m) for m in matches), default=0)


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
        backend = o.get("backend", cfg.orchestrator.backend)
        if backend not in ("auto", "api", "cli"):
            raise ValueError(
                f"Invalid orchestrator.backend: {backend!r}. "
                f"Must be one of: auto, api, cli"
            )
        cfg.orchestrator = OrchestratorConfig(
            model=o.get("model", cfg.orchestrator.model),
            max_turns=o.get("max_turns", cfg.orchestrator.max_turns),
            permission_mode=o.get("permission_mode", cfg.orchestrator.permission_mode),
            max_budget_usd=o.get("max_budget_usd", cfg.orchestrator.max_budget_usd),
            backend=backend,
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
            min_exchanges=iv.get("min_exchanges", cfg.interview.min_exchanges),
            require_understanding_summary=iv.get("require_understanding_summary", cfg.interview.require_understanding_summary),
            require_codebase_exploration=iv.get("require_codebase_exploration", cfg.interview.require_codebase_exploration),
        )
        # Validate the InterviewConfig
        _validate_interview_config(cfg.interview)

    if "design_reference" in data and isinstance(data["design_reference"], dict):
        dr = data["design_reference"]
        cfg.design_reference = DesignReferenceConfig(
            urls=dr.get("urls", cfg.design_reference.urls),
            depth=dr.get("depth", cfg.design_reference.depth),
            max_pages_per_site=dr.get("max_pages_per_site", cfg.design_reference.max_pages_per_site),
        )

        # Validate design_reference.depth enum value
        if cfg.design_reference.depth and cfg.design_reference.depth not in ("branding", "screenshots", "full", ""):
            raise ValueError(
                f"Invalid design_reference.depth: {cfg.design_reference.depth!r}. "
                f"Must be one of: branding, screenshots, full"
            )

    if "codebase_map" in data and isinstance(data["codebase_map"], dict):
        cm = data["codebase_map"]
        cfg.codebase_map = CodebaseMapConfig(
            enabled=cm.get("enabled", cfg.codebase_map.enabled),
            max_files=cm.get("max_files", cfg.codebase_map.max_files),
            max_file_size_kb=cm.get("max_file_size_kb", cfg.codebase_map.max_file_size_kb),
            max_file_size_kb_ts=cm.get("max_file_size_kb_ts", cfg.codebase_map.max_file_size_kb_ts),
            timeout_seconds=cm.get("timeout_seconds", cfg.codebase_map.timeout_seconds),
            exclude_patterns=cm.get("exclude_patterns", cfg.codebase_map.exclude_patterns),
        )

    if "scheduler" in data and isinstance(data["scheduler"], dict):
        sc = data["scheduler"]
        cfg.scheduler = SchedulerConfig(
            enabled=sc.get("enabled", cfg.scheduler.enabled),
            max_parallel_tasks=sc.get("max_parallel_tasks", cfg.scheduler.max_parallel_tasks),
            conflict_strategy=sc.get("conflict_strategy", cfg.scheduler.conflict_strategy),
            enable_context_scoping=sc.get("enable_context_scoping", cfg.scheduler.enable_context_scoping),
            enable_critical_path=sc.get("enable_critical_path", cfg.scheduler.enable_critical_path),
        )

        # Validate conflict_strategy enum value
        if cfg.scheduler.conflict_strategy not in ("artificial-dependency", "integration-agent"):
            raise ValueError(
                f"Invalid scheduler.conflict_strategy: {cfg.scheduler.conflict_strategy!r}. "
                f"Must be one of: artificial-dependency, integration-agent"
            )

    if "verification" in data and isinstance(data["verification"], dict):
        vr = data["verification"]
        cfg.verification = VerificationConfig(
            enabled=vr.get("enabled", cfg.verification.enabled),
            contract_file=vr.get("contract_file", cfg.verification.contract_file),
            verification_file=vr.get("verification_file", cfg.verification.verification_file),
            blocking=vr.get("blocking", cfg.verification.blocking),
            run_lint=vr.get("run_lint", cfg.verification.run_lint),
            run_type_check=vr.get("run_type_check", cfg.verification.run_type_check),
            run_tests=vr.get("run_tests", cfg.verification.run_tests),
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
                # Security: yaml.safe_load restricts deserialization to safe
                # Python types (str, int, float, bool, list, dict, None).
                # Never use yaml.load() or yaml.unsafe_load() here -- they
                # can instantiate arbitrary Python objects from YAML tags.
                loaded = yaml.safe_load(f) or {}
            raw = _deep_merge(raw, loaded)
            break  # Use first found file

    # Apply CLI overrides
    if cli_overrides:
        raw = _deep_merge(raw, cli_overrides)

    return _dict_to_config(raw)
