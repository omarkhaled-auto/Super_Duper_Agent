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
    max_thinking_tokens: int | None = None


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
    min_convergence_ratio: float = 0.9
    recovery_threshold: float = 0.8
    degraded_threshold: float = 0.5


def _validate_convergence_config(cfg: ConvergenceConfig) -> None:
    """Validate ConvergenceConfig threshold values and relationships."""
    if not (0.0 <= cfg.min_convergence_ratio <= 1.0):
        raise ValueError("convergence.min_convergence_ratio must be between 0.0 and 1.0")
    if not (0.0 <= cfg.recovery_threshold <= 1.0):
        raise ValueError("convergence.recovery_threshold must be between 0.0 and 1.0")
    if not (0.0 <= cfg.degraded_threshold <= 1.0):
        raise ValueError("convergence.degraded_threshold must be between 0.0 and 1.0")
    if cfg.recovery_threshold > cfg.min_convergence_ratio:
        raise ValueError(
            "convergence.recovery_threshold must be <= min_convergence_ratio"
        )


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
    max_thinking_tokens: int | None = None


def _validate_max_thinking_tokens(value: int | None, section: str) -> None:
    """Validate max_thinking_tokens: must be None or >= 1024 (SDK minimum)."""
    if value is not None and value < 1024:
        raise ValueError(f"{section}.max_thinking_tokens must be >= 1024 (got {value})")


def _validate_interview_config(cfg: InterviewConfig) -> None:
    if cfg.min_exchanges < 1:
        raise ValueError("min_exchanges must be >= 1")
    if cfg.min_exchanges > cfg.max_exchanges:
        raise ValueError("min_exchanges must be <= max_exchanges")
    _validate_max_thinking_tokens(cfg.max_thinking_tokens, "interview")


@dataclass
class InvestigationConfig:
    enabled: bool = False              # Explicit opt-in (requires Gemini CLI install)
    gemini_model: str = ""             # Empty = default; e.g. "gemini-2.5-pro"
    max_queries_per_agent: int = 8     # Hard ceiling — agent decides how many to use
    timeout_seconds: int = 120         # Max seconds per Gemini query
    agents: list[str] = field(default_factory=lambda: [
        "code-reviewer", "security-auditor", "debugger",
    ])
    sequential_thinking: bool = True          # Enable ST when investigation enabled
    max_thoughts_per_item: int = 15           # Thought step budget per item
    enable_hypothesis_loop: bool = True       # Require hypothesis-verification cycles


_VALID_INVESTIGATION_AGENTS = frozenset({
    "code-reviewer", "security-auditor", "debugger",
    "planner", "researcher", "architect", "task-assigner",
    "code-writer", "test-runner", "integration-agent",
    "contract-generator", "spec-validator",
})


def _validate_investigation_config(cfg: InvestigationConfig) -> None:
    if cfg.max_queries_per_agent < 1:
        raise ValueError("investigation.max_queries_per_agent must be >= 1")
    if cfg.timeout_seconds < 1:
        raise ValueError("investigation.timeout_seconds must be >= 1")
    if cfg.max_thoughts_per_item < 3:
        raise ValueError("investigation.max_thoughts_per_item must be >= 3")
    for agent in cfg.agents:
        if agent not in _VALID_INVESTIGATION_AGENTS:
            raise ValueError(
                f"investigation.agents contains invalid agent name: {agent!r}. "
                f"Valid agents: {sorted(_VALID_INVESTIGATION_AGENTS)}"
            )


@dataclass
class OrchestratorSTConfig:
    """Sequential Thinking at the orchestrator level — depth-gated decision points."""
    enabled: bool = True                    # On by default (depth-gated anyway)
    depth_gate: dict[str, list[int]] = field(default_factory=lambda: {
        "quick": [1, 2, 3, 4],             # All points — depth is scale, not reasoning
        "standard": [1, 2, 3, 4],
        "thorough": [1, 2, 3, 4],
        "exhaustive": [1, 2, 3, 4],
    })
    thought_budgets: dict[int, int] = field(default_factory=lambda: {
        1: 8,    # Pre-run strategy: max 8 thoughts
        2: 10,   # Architecture checkpoint: max 10 thoughts
        3: 12,   # Convergence reasoning: max 12 thoughts
        4: 8,    # Completion verification: max 8 thoughts
    })


@dataclass
class DesignReferenceConfig:
    urls: list[str] = field(default_factory=list)
    depth: str = "full"  # "branding" | "screenshots" | "full"
    max_pages_per_site: int = 5
    cache_ttl_seconds: int = 7200  # 2 hours
    standards_file: str = ""  # empty = built-in; path = custom file
    require_ui_doc: bool = True          # Hard-fail when extraction fails
    ui_requirements_file: str = "UI_REQUIREMENTS.md"  # Output filename


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
    enabled: bool = True              # enabled by default
    max_parallel_tasks: int = 5
    conflict_strategy: str = "artificial-dependency"
    enable_context_scoping: bool = True
    enable_critical_path: bool = True


@dataclass
class QualityConfig:
    """Controls production-readiness and code craft quality features."""
    production_defaults: bool = True       # Inject production-readiness TECH-xxx into planner
    craft_review: bool = True              # Enable CODE CRAFT review pass in reviewers
    quality_triggers_reloop: bool = True   # Quality violations feed back into convergence


@dataclass
class VerificationConfig:
    enabled: bool = True              # enabled by default
    contract_file: str = "CONTRACTS.json"
    verification_file: str = "VERIFICATION.md"
    blocking: bool = True
    run_lint: bool = True
    run_type_check: bool = True
    run_tests: bool = True
    run_build: bool = True
    run_security: bool = True
    run_quality_checks: bool = True
    min_test_count: int = 0


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
class MilestoneConfig:
    """Configuration for the per-milestone orchestration loop.

    Only affects PRD mode.  When ``enabled`` is False (the default),
    the milestone loop is completely bypassed and non-PRD mode is
    unchanged.
    """

    enabled: bool = False
    max_parallel_milestones: int = 1
    health_gate: bool = True
    wiring_check: bool = True
    resume_from_milestone: str | None = None
    wiring_fix_retries: int = 1
    max_milestones_warning: int = 30


@dataclass
class PRDChunkingConfig:
    """Configuration for large PRD chunking.

    When a PRD exceeds the size threshold, it is split into focused
    chunks before the PRD Analyzer Fleet is deployed. This prevents
    context overflow for very large PRDs.
    """

    enabled: bool = True
    threshold: int = 50000  # bytes - PRDs larger trigger chunking
    max_chunk_size: int = 20000  # bytes - target size per chunk


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
    quality: QualityConfig = field(default_factory=QualityConfig)
    investigation: InvestigationConfig = field(default_factory=InvestigationConfig)
    orchestrator_st: OrchestratorSTConfig = field(default_factory=OrchestratorSTConfig)
    milestone: MilestoneConfig = field(default_factory=MilestoneConfig)
    prd_chunking: PRDChunkingConfig = field(default_factory=PRDChunkingConfig)
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
        "sequential_thinking": MCPServerConfig(),
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


def apply_depth_quality_gating(depth: str, config: AgentTeamConfig) -> None:
    """Apply depth-based gating to QualityConfig.

    QUICK depth disables production_defaults and craft_review to keep
    runs fast. STANDARD and above keep the defaults (all True).
    """
    if depth == "quick":
        config.quality.production_defaults = False
        config.quality.craft_review = False


def get_agent_counts(depth: str) -> dict[str, tuple[int, int]]:
    """Return (min, max) agent counts per phase for the given depth."""
    return DEPTH_AGENT_COUNTS.get(depth, DEPTH_AGENT_COUNTS["standard"])


def get_active_st_points(depth: str, config: OrchestratorSTConfig) -> list[int]:
    """Return which ST decision points are active for this depth level."""
    if not config.enabled:
        return []
    return config.depth_gate.get(depth, [])


def _validate_orchestrator_st_config(cfg: OrchestratorSTConfig) -> None:
    """Validate OrchestratorSTConfig fields."""
    valid_depths = ("quick", "standard", "thorough", "exhaustive")
    for depth, points in cfg.depth_gate.items():
        if depth not in valid_depths:
            raise ValueError(f"orchestrator_st.depth_gate has invalid depth: {depth}")
        for p in points:
            if p not in (1, 2, 3, 4):
                raise ValueError(f"orchestrator_st.depth_gate[{depth}] has invalid point: {p}")
    valid_points = (1, 2, 3, 4)
    for point, budget in cfg.thought_budgets.items():
        if point not in valid_points:
            raise ValueError(f"orchestrator_st.thought_budgets has invalid point: {point}")
        if budget < 3 or budget > 30:
            raise ValueError(f"orchestrator_st.thought_budgets[{point}] must be 3-30")


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

_TECHNOLOGY_RE = re.compile(
    r'\b(Express(?:\.js)?|React(?:\.js)?|Next\.js|Vue(?:\.js)?|Angular|'
    r'Node\.js|Django|Flask|FastAPI|Spring\s*Boot|Rails|Laravel|'
    r'MongoDB|PostgreSQL|MySQL|SQLite|Redis|Supabase|Firebase|'
    r'TypeScript|GraphQL|REST\s*API|gRPC|WebSocket|'
    r'Docker|Kubernetes|AWS|GCP|Azure|Vercel|Netlify|Render|'
    r'Jest|Vitest|Pytest|Mocha|Cypress|Playwright|'
    r'Tailwind(?:\s*CSS)?|Sass|SCSS|Styled[\s-]?Components|'
    r'Zustand|Redux|MobX|Jotai|Recoil|Tanstack[\s-]?Query|'
    r'Prisma|Drizzle|Sequelize|TypeORM|Mongoose|Knex|'
    r'pnpm|bun|yarn|npm|'
    r'monorepo|microservices?|serverless|full[\s-]?stack)\b',
    re.IGNORECASE,
)

_TEST_FRAMEWORK_RE = re.compile(
    r'\b(jest|vitest|pytest|mocha|cypress|playwright|jasmine|ava|tap|uvu)\b',
    re.IGNORECASE,
)

_TEST_REQUIREMENT_RE = re.compile(
    r'(\d+)\+?\s*(?:unit\s+)?tests?',
    re.IGNORECASE,
)

_DESIGN_URL_RE = re.compile(
    r'(?:\[([^\]]*)\]\()?'   # optional markdown link text
    r'(https?://[^\s\)]+)'   # URL itself
    r'\)?',                   # optional closing paren
    re.IGNORECASE,
)

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

    # Extract technology stack requirements
    for source_text, source_label in [(task, "task"), (interview_doc or "", "interview")]:
        for match in _TECHNOLOGY_RE.finditer(source_text):
            tech = match.group(1).strip()
            normalized = f"must use {tech.lower()}"
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                constraints.append(ConstraintEntry(
                    f"must use {tech}", "requirement", source_label, 2
                ))

    # Extract test count requirements
    for source_text, source_label in [(task, "task"), (interview_doc or "", "interview")]:
        for match in _TEST_REQUIREMENT_RE.finditer(source_text):
            count = match.group(1)
            text = f"must have {count}+ tests"
            normalized = text.lower()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                constraints.append(ConstraintEntry(text, "requirement", source_label, 2))

    # Extract test framework preferences (Root Cause #12)
    for source_text, source_label in [(task, "task"), (interview_doc or "", "interview")]:
        for match in _TEST_FRAMEWORK_RE.finditer(source_text):
            framework = match.group(1).strip()
            normalized = f"must use {framework.lower()} for testing"
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                constraints.append(ConstraintEntry(
                    f"must use {framework} for testing", "requirement", source_label, 2
                ))

    # Extract design reference URLs (Root Cause #12)
    for source_text, source_label in [(task, "task"), (interview_doc or "", "interview")]:
        for match in _DESIGN_URL_RE.finditer(source_text):
            url = match.group(2).strip()
            # Only include design-relevant URLs (not generic docs)
            if any(kw in url.lower() for kw in ("figma", "dribbble", "behance", "design", "prototype", "sketch")):
                normalized = f"design reference: {url.lower()}"
                if normalized not in seen_texts:
                    seen_texts.add(normalized)
                    constraints.append(ConstraintEntry(
                        f"design reference: {url}", "requirement", source_label, 1
                    ))

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


def parse_per_item_review_cycles(
    requirements_content: str,
) -> list[tuple[str, bool, int]]:
    """Parse per-item review cycle data from REQUIREMENTS.md.

    Returns list of (item_id, is_checked, review_cycles) tuples.
    """
    pattern = (
        r'^\s*-\s*\[([ xX])\]\s*'
        r'((?:REQ|TECH|INT|WIRE|DESIGN|TEST)-\d+):'
        r'.*?\(review_cycles:\s*(\d+)\)'
    )
    results: list[tuple[str, bool, int]] = []
    for match in re.finditer(pattern, requirements_content, re.MULTILINE):
        is_checked = match.group(1).lower() == 'x'
        item_id = match.group(2)
        cycles = int(match.group(3))
        results.append((item_id, is_checked, cycles))
    return results


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
        max_thinking_tokens = o.get("max_thinking_tokens", cfg.orchestrator.max_thinking_tokens)
        _validate_max_thinking_tokens(max_thinking_tokens, "orchestrator")
        cfg.orchestrator = OrchestratorConfig(
            model=o.get("model", cfg.orchestrator.model),
            max_turns=o.get("max_turns", cfg.orchestrator.max_turns),
            permission_mode=o.get("permission_mode", cfg.orchestrator.permission_mode),
            max_budget_usd=o.get("max_budget_usd", cfg.orchestrator.max_budget_usd),
            backend=backend,
            max_thinking_tokens=max_thinking_tokens,
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
            min_convergence_ratio=float(c.get("min_convergence_ratio", cfg.convergence.min_convergence_ratio)),
            recovery_threshold=float(c.get("recovery_threshold", cfg.convergence.recovery_threshold)),
            degraded_threshold=float(c.get("degraded_threshold", cfg.convergence.degraded_threshold)),
        )
        _validate_convergence_config(cfg.convergence)

    if "interview" in data:
        iv = data["interview"]
        cfg.interview = InterviewConfig(
            enabled=iv.get("enabled", cfg.interview.enabled),
            model=iv.get("model", cfg.interview.model),
            max_exchanges=iv.get("max_exchanges", cfg.interview.max_exchanges),
            min_exchanges=iv.get("min_exchanges", cfg.interview.min_exchanges),
            require_understanding_summary=iv.get("require_understanding_summary", cfg.interview.require_understanding_summary),
            require_codebase_exploration=iv.get("require_codebase_exploration", cfg.interview.require_codebase_exploration),
            max_thinking_tokens=iv.get("max_thinking_tokens", cfg.interview.max_thinking_tokens),
        )
        # Validate the InterviewConfig
        _validate_interview_config(cfg.interview)

    if "design_reference" in data and isinstance(data["design_reference"], dict):
        dr = data["design_reference"]
        cfg.design_reference = DesignReferenceConfig(
            urls=dr.get("urls", cfg.design_reference.urls),
            depth=dr.get("depth", cfg.design_reference.depth),
            max_pages_per_site=dr.get("max_pages_per_site", cfg.design_reference.max_pages_per_site),
            cache_ttl_seconds=dr.get("cache_ttl_seconds", cfg.design_reference.cache_ttl_seconds),
            standards_file=dr.get("standards_file", cfg.design_reference.standards_file),
            require_ui_doc=dr.get("require_ui_doc", cfg.design_reference.require_ui_doc),
            ui_requirements_file=dr.get("ui_requirements_file", cfg.design_reference.ui_requirements_file),
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
            run_build=vr.get("run_build", cfg.verification.run_build),
            run_security=vr.get("run_security", cfg.verification.run_security),
            run_quality_checks=vr.get("run_quality_checks", cfg.verification.run_quality_checks),
            min_test_count=vr.get("min_test_count", cfg.verification.min_test_count),
        )

    if "quality" in data and isinstance(data["quality"], dict):
        q = data["quality"]
        cfg.quality = QualityConfig(
            production_defaults=q.get("production_defaults", cfg.quality.production_defaults),
            craft_review=q.get("craft_review", cfg.quality.craft_review),
            quality_triggers_reloop=q.get("quality_triggers_reloop", cfg.quality.quality_triggers_reloop),
        )

    if "investigation" in data and isinstance(data["investigation"], dict):
        inv = data["investigation"]
        cfg.investigation = InvestigationConfig(
            enabled=inv.get("enabled", cfg.investigation.enabled),
            gemini_model=inv.get("gemini_model", cfg.investigation.gemini_model),
            max_queries_per_agent=inv.get("max_queries_per_agent", cfg.investigation.max_queries_per_agent),
            timeout_seconds=inv.get("timeout_seconds", cfg.investigation.timeout_seconds),
            agents=inv.get("agents", cfg.investigation.agents),
            sequential_thinking=inv.get("sequential_thinking", cfg.investigation.sequential_thinking),
            max_thoughts_per_item=inv.get("max_thoughts_per_item", cfg.investigation.max_thoughts_per_item),
            enable_hypothesis_loop=inv.get("enable_hypothesis_loop", cfg.investigation.enable_hypothesis_loop),
        )
        _validate_investigation_config(cfg.investigation)

    if "orchestrator_st" in data and isinstance(data["orchestrator_st"], dict):
        ost = data["orchestrator_st"]
        depth_gate_raw = ost.get("depth_gate", None)
        depth_gate = cfg.orchestrator_st.depth_gate
        if depth_gate_raw and isinstance(depth_gate_raw, dict):
            depth_gate = {k: list(v) for k, v in depth_gate_raw.items()}
        thought_budgets_raw = ost.get("thought_budgets", None)
        thought_budgets = cfg.orchestrator_st.thought_budgets
        if thought_budgets_raw and isinstance(thought_budgets_raw, dict):
            thought_budgets = {int(k): int(v) for k, v in thought_budgets_raw.items()}
        cfg.orchestrator_st = OrchestratorSTConfig(
            enabled=ost.get("enabled", cfg.orchestrator_st.enabled),
            depth_gate=depth_gate,
            thought_budgets=thought_budgets,
        )
        _validate_orchestrator_st_config(cfg.orchestrator_st)

    if "milestone" in data and isinstance(data["milestone"], dict):
        ms = data["milestone"]
        resume_val = ms.get("resume_from_milestone", cfg.milestone.resume_from_milestone)
        cfg.milestone = MilestoneConfig(
            enabled=ms.get("enabled", cfg.milestone.enabled),
            max_parallel_milestones=ms.get(
                "max_parallel_milestones", cfg.milestone.max_parallel_milestones,
            ),
            health_gate=ms.get("health_gate", cfg.milestone.health_gate),
            wiring_check=ms.get("wiring_check", cfg.milestone.wiring_check),
            resume_from_milestone=resume_val if isinstance(resume_val, str) else None,
            wiring_fix_retries=ms.get(
                "wiring_fix_retries", cfg.milestone.wiring_fix_retries,
            ),
            max_milestones_warning=ms.get(
                "max_milestones_warning", cfg.milestone.max_milestones_warning,
            ),
        )

    if "prd_chunking" in data and isinstance(data["prd_chunking"], dict):
        pc = data["prd_chunking"]
        cfg.prd_chunking = PRDChunkingConfig(
            enabled=pc.get("enabled", cfg.prd_chunking.enabled),
            threshold=pc.get("threshold", cfg.prd_chunking.threshold),
            max_chunk_size=pc.get("max_chunk_size", cfg.prd_chunking.max_chunk_size),
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
