# Build 3 Architecture Plan: Integrator + Quality Gate + Super Orchestrator

> **Author**: Architecture Planner Agent
> **Date**: 2026-02-14
> **Purpose**: Exhaustive architecture blueprint for the Build 3 PRD writer. Every class, method, field, and dependency is specified.
> **Inputs**: BUILD3_CODEBASE_RESEARCH.md, BUILD3_TECH_STATE_CLI.md, BUILD3_TECH_TESTING.md, BUILD3_TECH_SECURITY_OBS.md, BUILD3_TECH_DOCKER_TRAEFIK.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md, BUILD1_PRD.md, BUILD2_PRD.md

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Complete Project Structure](#2-complete-project-structure)
3. [Class Hierarchy per Module](#3-class-hierarchy-per-module)
4. [Data Flow Diagram](#4-data-flow-diagram)
5. [State Machine Design](#5-state-machine-design)
6. [Quality Gate Layer Specification](#6-quality-gate-layer-specification)
7. [Docker Compose Template](#7-docker-compose-template)
8. [MCP Tool Interfaces](#8-mcp-tool-interfaces)
9. [CLI Command Design](#9-cli-command-design)
10. [Milestone Dependency Graph](#10-milestone-dependency-graph)
11. [Integration Points with Build 1+2](#11-integration-points-with-build-12)
12. [Risk Assessment](#12-risk-assessment)

---

## 1. Technology Stack

### Core Runtime

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| **Language** | Python | 3.12+ | Match Build 1+2. f-strings, `type` aliases, `asyncio.TaskGroup`. |
| **Async Runtime** | asyncio | stdlib | Already used by agent-team v14. No new deps. |
| **MCP SDK** | mcp[cli] | >=1.25, <2 | Claude Code native protocol. Match Build 1+2. |
| **HTTP Framework** | FastAPI | 0.129.0+ | Health/status endpoints. Match Build 1. |
| **ASGI Server** | uvicorn | 0.34.0+ | Run FastAPI endpoints. Match Build 1. |

### State Machine + CLI

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| **State Machine** | transitions | 0.9.2+ | Declarative FSM, `AsyncMachine`, guard conditions, queued transitions. |
| **CLI Framework** | typer | 0.21.0+ | Type-safe, Rich integration, Pythonic. Includes Click internally. |
| **Terminal UI** | rich | 13.0+ | Progress bars, tables, panels, live display. Bundled with `typer[all]`. |

### Testing + Contract Compliance

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| **Property-Based API Testing** | schemathesis | 4.x (latest) | OpenAPI fuzz testing. `from_url()`, `@schema.parametrize()`, stateful testing. |
| **Consumer-Driven Contracts** | pact-python | 3.2.1+ | Pact V4 spec, native Rust FFI. Consumer/provider verification. |
| **Docker Test Integration** | testcontainers | 4.x + compose extra | `DockerCompose` class with per-service wait strategies. |
| **Async HTTP Client** | httpx | 0.28.x+ | `AsyncClient`, concurrent cross-service requests. |
| **Test Framework** | pytest | 8.x+ | Test orchestration, fixtures, parametrize. |
| **Async Test Support** | pytest-asyncio | 0.24.x+ | `asyncio_mode = "auto"` in pyproject.toml. |

### Security + Observability

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| **Secret Scanning** | detect-secrets | 1.5+ | `SecretsCollection` Python API with `transient_settings`. |
| **JWT Verification** | PyJWT | 2.8+ | Validation patterns. v2 requires `algorithms` param. |
| **Trace Context** | opentelemetry-api | 1.25+ | `TraceContextTextMapPropagator` for W3C traceparent. |
| **Trace SDK** | opentelemetry-sdk | 1.25+ | `TracerProvider`, `BatchSpanProcessor`. |

### Infrastructure

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| **API Gateway** | Traefik | v3.6 | Docker provider auto-discovery via labels. 55K GitHub stars. |
| **Service Orchestration** | Docker Compose | v2 | `depends_on` with `service_healthy`/`service_completed_successfully`. |
| **Configuration** | PyYAML | 6.x+ | Already in agent-team deps. |
| **Docker SDK** | docker-py | 7.x+ | Programmatic container management. |
| **Data Validation** | pydantic | 2.x+ | Config and DTO validation. Match Build 1. |

### Full requirements.txt Additions (over Build 1+2)

```
transitions>=0.9.2
typer[all]>=0.21.0
schemathesis>=4.0.0
pact-python>=3.2.1
testcontainers[postgres,redis,compose]>=4.0.0
httpx>=0.28.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
detect-secrets>=1.5.0
PyJWT>=2.8.0
opentelemetry-api>=1.25.0
opentelemetry-sdk>=1.25.0
docker>=7.0.0
```

---

## 2. Complete Project Structure

```
super-team/
  src/
    super_orchestrator/                   # Build 3: Super Orchestrator (~20K LOC)
      __init__.py                         # Package init, version
      cli.py                              # Typer app, 6 commands + status/resume (~800 LOC)
      state_machine.py                    # AsyncMachine, OrchestratorState, transitions (~400 LOC)
      pipeline.py                         # Phase execution: async functions per phase (~1200 LOC)
      state.py                            # PipelineState persistence, atomic write (~300 LOC)
      cost.py                             # PipelineCostTracker, PhaseCost (~200 LOC)
      display.py                          # Rich console, tables, progress bars, live dashboard (~400 LOC)
      config.py                           # SuperOrchestratorConfig, extends AgentTeamConfig (~350 LOC)
      exceptions.py                       # PhaseTimeoutError, BudgetExceededError, etc. (~80 LOC)
      shutdown.py                         # GracefulShutdown signal handler (~120 LOC)

    integrator/                           # Build 3: Integrator (~15K LOC)
      __init__.py
      docker_orchestrator.py              # Docker Compose lifecycle management (~600 LOC)
      traefik_config.py                   # Traefik label generation, routing rules (~400 LOC)
      service_discovery.py                # Service health checking, port mapping (~300 LOC)
      compose_generator.py                # Dynamic docker-compose.yml generation (~500 LOC)
      cross_service_test_generator.py     # Generate integration tests from contracts (~800 LOC)
      cross_service_test_runner.py        # Execute cross-service test flows (~600 LOC)
      data_flow_tracer.py                 # Trace requests through services, verify transformations (~500 LOC)
      boundary_tester.py                  # camelCase/snake_case, timezone, null vs missing (~400 LOC)
      contract_compliance.py              # Schemathesis + Pact verification orchestration (~700 LOC)
      pact_manager.py                     # Pact consumer/provider contract management (~500 LOC)
      schemathesis_runner.py              # Schemathesis test execution + result parsing (~500 LOC)
      fix_loop.py                         # Feed violations back to Builders for remediation (~400 LOC)
      report.py                           # IntegrationReport generation (~300 LOC)

    quality_gate/                         # Build 3: Quality Gate (~15K LOC)
      __init__.py
      gate_engine.py                      # 4-layer sequential gate with promotion/demotion (~600 LOC)
      layer1_per_service.py               # Aggregate per-service results from Builders (~300 LOC)
      layer2_contract_compliance.py       # Cross-service contract verification (~500 LOC)
      layer3_system_level.py              # Security + observability + system scans (~800 LOC)
      layer4_adversarial.py               # Adversarial review orchestration (~600 LOC)
      security_scanner.py                 # JWT, CORS, secrets scanning (~700 LOC)
      observability_checker.py            # Logging, trace propagation, health endpoints (~500 LOC)
      docker_security.py                  # Dockerfile + docker-compose security checks (~400 LOC)
      adversarial_patterns.py             # Dead events, dead contracts, orphans, naming, races (~600 LOC)
      scan_aggregator.py                  # Collect + deduplicate + prioritize all violations (~300 LOC)
      report.py                           # QualityGateReport generation (~300 LOC)

    shared/                               # Build 3: Shared models (~3K LOC)
      __init__.py
      models.py                           # Core dataclasses: BuilderResult, ServiceInfo, etc. (~400 LOC)
      protocols.py                        # Protocol classes for type safety (~200 LOC)
      constants.py                        # Scan codes, phase names, timeouts (~150 LOC)
      utils.py                            # atomic_write_json, file helpers (~200 LOC)

  tests/                                  # Build 3 tests (~15K LOC)
    conftest.py                           # Shared fixtures: compose, clients, mock services (~300 LOC)
    test_state_machine.py                 # State machine transitions, guards, callbacks (~500 LOC)
    test_cli.py                           # CLI commands via CliRunner (~400 LOC)
    test_pipeline.py                      # Phase execution, error handling, resume (~600 LOC)
    test_docker_orchestrator.py           # Docker lifecycle, health checks (~400 LOC)
    test_contract_compliance.py           # Schemathesis + Pact integration (~500 LOC)
    test_cross_service.py                 # Cross-service test generation + execution (~600 LOC)
    test_quality_gate.py                  # 4-layer gate engine, promotion/demotion (~500 LOC)
    test_security_scanner.py              # JWT, CORS, secrets detection (~600 LOC)
    test_observability.py                 # Logging, trace propagation (~400 LOC)
    test_adversarial.py                   # Dead events, contracts, orphans, naming, races (~500 LOC)
    test_docker_security.py              # Dockerfile + compose security (~300 LOC)
    test_state_persistence.py             # Save/load/resume/clear (~300 LOC)
    test_cost_tracking.py                 # Cost aggregation, budget checks (~200 LOC)
    test_config.py                        # Config loading, validation, depth gating (~300 LOC)
    test_integration_e2e.py               # Full pipeline integration (3-service app) (~800 LOC)
    fixtures/                             # Test data
      sample_openapi.yaml                 # Sample OpenAPI spec for Schemathesis tests
      sample_pact.json                    # Sample Pact contract
      sample_docker_compose.yml           # Sample compose for Docker tests
      sample_prd.md                       # 3-service test PRD

  docker/                                 # Docker infrastructure
    docker-compose.yml                    # Production compose (Build 1 services + Build 3)
    docker-compose.test.yml               # Test compose (isolated)
    traefik/
      traefik.yml                         # Static Traefik configuration
      dynamic/                            # Dynamic Traefik config (file provider)

  pyproject.toml                          # Project metadata, dependencies, pytest config
  config.yaml                             # Default Super Orchestrator config
```

### Estimated LOC Breakdown

| Module | Estimated LOC |
|--------|---------------|
| `super_orchestrator/` | ~3,850 |
| `integrator/` | ~6,100 |
| `quality_gate/` | ~5,500 |
| `shared/` | ~950 |
| `tests/` | ~6,400 |
| Docker configs + fixtures | ~500 |
| **Total** | **~23,300** |

---

## 3. Class Hierarchy per Module

### 3.1 `shared/models.py`

```python
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

class ServiceStatus(str, Enum):
    PENDING = "pending"
    BUILDING = "building"
    BUILT = "built"
    DEPLOYING = "deploying"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"

class QualityLevel(str, Enum):
    LAYER1_SERVICE = "layer1_service"
    LAYER2_CONTRACT = "layer2_contract"
    LAYER3_SYSTEM = "layer3_system"
    LAYER4_ADVERSARIAL = "layer4_adversarial"

class GateVerdict(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"

@dataclass
class ServiceInfo:
    """Metadata about a service in the build."""
    service_id: str                           # e.g., "auth-service"
    domain: str                               # e.g., "Authentication & Authorization"
    stack: dict[str, str]                     # e.g., {"backend": "Express+TypeScript", "db": "PostgreSQL"}
    estimated_loc: int = 0
    docker_image: str = ""                    # Built image tag
    health_endpoint: str = "/health"
    port: int = 8080
    status: ServiceStatus = ServiceStatus.PENDING
    build_cost: float = 0.0
    build_dir: str = ""                       # Absolute path to service directory

@dataclass
class BuilderResult:
    """Result from a single Builder execution."""
    system_id: str                            # "system-3", "system-4", etc.
    service_id: str                           # "auth-service"
    success: bool = False
    cost: float = 0.0
    error: str = ""
    output_dir: str = ""
    test_passed: int = 0
    test_total: int = 0
    convergence_ratio: float = 0.0
    artifacts: list[str] = field(default_factory=list)

@dataclass
class ContractViolation:
    """A single contract compliance violation."""
    code: str                                 # e.g., "SCHEMA-001", "PACT-001"
    severity: str                             # "error", "warning", "info"
    service: str                              # Service that violated
    endpoint: str                             # API endpoint path
    message: str                              # Human-readable description
    expected: str = ""                        # Expected schema/value
    actual: str = ""                          # Actual schema/value
    file_path: str = ""

@dataclass
class ScanViolation:
    """A single quality gate scan violation."""
    code: str                                 # e.g., "SEC-001", "CORS-001", "ADV-001"
    severity: str                             # "critical", "error", "warning", "info"
    category: str                             # "security", "cors", "logging", "docker", "adversarial"
    file_path: str = ""
    line: int = 0
    service: str = ""
    message: str = ""

@dataclass
class LayerResult:
    """Result from one quality gate layer."""
    layer: QualityLevel
    verdict: GateVerdict = GateVerdict.SKIPPED
    violations: list[ScanViolation] = field(default_factory=list)
    contract_violations: list[ContractViolation] = field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    duration_seconds: float = 0.0

@dataclass
class QualityGateReport:
    """Complete quality gate report across all layers."""
    layers: dict[str, LayerResult] = field(default_factory=dict)
    overall_verdict: GateVerdict = GateVerdict.SKIPPED
    fix_attempts: int = 0
    max_fix_attempts: int = 3
    total_violations: int = 0
    blocking_violations: int = 0

@dataclass
class IntegrationReport:
    """Report from the Integrator phase."""
    services_deployed: int = 0
    services_healthy: int = 0
    contract_tests_total: int = 0
    contract_tests_passed: int = 0
    integration_tests_total: int = 0
    integration_tests_passed: int = 0
    data_flow_tests_total: int = 0
    data_flow_tests_passed: int = 0
    boundary_tests_total: int = 0
    boundary_tests_passed: int = 0
    violations: list[ContractViolation] = field(default_factory=list)
    overall_health: str = "unknown"          # "passed", "partial", "failed"
```

### 3.2 `shared/protocols.py`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class PhaseExecutor(Protocol):
    """Protocol for pipeline phase execution."""
    async def execute(self, context: "PipelineContext") -> float:
        """Execute the phase, return cost in USD."""
        ...

    async def can_execute(self, context: "PipelineContext") -> bool:
        """Check if preconditions are met."""
        ...

@runtime_checkable
class QualityScanner(Protocol):
    """Protocol for quality gate scanners."""
    def scan(self, project_root: "Path") -> list["ScanViolation"]:
        """Run scan and return violations."""
        ...

    @property
    def scan_codes(self) -> list[str]:
        """Return the scan codes this scanner produces."""
        ...
```

### 3.3 `shared/constants.py`

```python
# Phase names (match state machine states)
PHASE_ARCHITECT = "architect_running"
PHASE_ARCHITECT_REVIEW = "architect_review"
PHASE_CONTRACTS = "contracts_registering"
PHASE_BUILDERS = "builders_running"
PHASE_INTEGRATION = "integrating"
PHASE_QUALITY_GATE = "quality_gate"
PHASE_FIX_PASS = "fix_pass"
PHASE_COMPLETE = "complete"
PHASE_FAILED = "failed"

# Phase timeout defaults (seconds)
PHASE_TIMEOUTS: dict[str, int] = {
    PHASE_ARCHITECT: 900,           # 15 minutes
    PHASE_ARCHITECT_REVIEW: 300,    # 5 minutes
    PHASE_CONTRACTS: 180,           # 3 minutes
    PHASE_BUILDERS: 3600,           # 60 minutes (parallel, longest builder)
    PHASE_INTEGRATION: 600,         # 10 minutes
    PHASE_QUALITY_GATE: 600,        # 10 minutes per layer
    PHASE_FIX_PASS: 900,            # 15 minutes
}

# Quality gate scan codes — all 30 from 7 categories
SECURITY_SCAN_CODES = ["SEC-001", "SEC-002", "SEC-003", "SEC-004", "SEC-005", "SEC-006"]
CORS_SCAN_CODES = ["CORS-001", "CORS-002", "CORS-003"]
LOGGING_SCAN_CODES = ["LOG-001", "LOG-004", "LOG-005"]
TRACE_SCAN_CODES = ["TRACE-001"]
SECRET_SCAN_CODES = [f"SEC-SECRET-{i:03d}" for i in range(1, 13)]
DOCKER_SCAN_CODES = [f"DOCKER-{i:03d}" for i in range(1, 9)]
ADVERSARIAL_SCAN_CODES = [f"ADV-{i:03d}" for i in range(1, 7)]
HEALTH_SCAN_CODES = ["HEALTH-001"]

ALL_SCAN_CODES = (
    SECURITY_SCAN_CODES + CORS_SCAN_CODES + LOGGING_SCAN_CODES +
    TRACE_SCAN_CODES + SECRET_SCAN_CODES + DOCKER_SCAN_CODES +
    ADVERSARIAL_SCAN_CODES + HEALTH_SCAN_CODES
)

# Builder concurrency
DEFAULT_MAX_CONCURRENT_BUILDERS = 3
DEFAULT_BUILDER_TIMEOUT = 1800  # 30 minutes

# State persistence
STATE_DIR = ".super-orchestrator"
STATE_FILE = "PIPELINE_STATE.json"
```

### 3.4 `super_orchestrator/state_machine.py`

```python
from transitions.extensions.asyncio import AsyncMachine
from transitions import State
from enum import Enum

# 11 states (10 operational + 1 terminal-error)
STATES = [
    State(name="init", on_enter=["log_entry"]),
    State(name="architect_running", on_enter=["start_timer", "update_display"]),
    State(name="architect_review", on_enter=["update_display"]),
    State(name="contracts_registering", on_enter=["update_display"]),
    State(name="builders_running", on_enter=["start_timer", "update_display"]),
    State(name="builders_complete", on_enter=["update_display"]),
    State(name="integrating", on_enter=["start_timer", "update_display"]),
    State(name="quality_gate", on_enter=["start_timer", "update_display"]),
    State(name="fix_pass", on_enter=["start_timer", "update_display"]),
    State(name="complete", on_enter=["print_summary", "clear_state"], ignore_invalid_triggers=True),
    State(name="failed", on_enter=["save_failure_report"], ignore_invalid_triggers=True),
]

# 13 transitions with guard conditions
TRANSITIONS = [
    {
        "trigger": "start_architect",
        "source": "init",
        "dest": "architect_running",
        "prepare": "load_prd",
        "conditions": ["has_valid_prd", "has_valid_config"],
        "before": "validate_config",
        "after": "launch_architect_phase",
    },
    {
        "trigger": "architect_done",
        "source": "architect_running",
        "dest": "architect_review",
        "conditions": ["architect_outputs_exist"],
    },
    {
        "trigger": "approve_architecture",
        "source": "architect_review",
        "dest": "contracts_registering",
        "conditions": ["review_approved"],
        "after": "register_contracts",
    },
    {
        "trigger": "reject_architecture",
        "source": "architect_review",
        "dest": "architect_running",
        "conditions": ["retries_remaining"],
        "after": "increment_architect_retries",
    },
    {
        "trigger": "contracts_ready",
        "source": "contracts_registering",
        "dest": "builders_running",
        "conditions": ["contracts_valid"],
        "after": "launch_builders",
    },
    {
        "trigger": "builders_done",
        "source": "builders_running",
        "dest": "builders_complete",
        "conditions": ["at_least_one_builder_succeeded"],
    },
    {
        "trigger": "start_integration",
        "source": "builders_complete",
        "dest": "integrating",
        "after": "launch_integration_phase",
    },
    {
        "trigger": "integration_done",
        "source": "integrating",
        "dest": "quality_gate",
        "conditions": ["integration_report_exists"],
        "after": "launch_quality_gate",
    },
    {
        "trigger": "quality_passed",
        "source": "quality_gate",
        "dest": "complete",
        "conditions": ["all_layers_passed"],
    },
    {
        "trigger": "quality_failed",
        "source": "quality_gate",
        "dest": "fix_pass",
        "conditions": ["fix_retries_remaining"],
        "after": "launch_fix_pass",
    },
    {
        "trigger": "fix_done",
        "source": "fix_pass",
        "dest": "quality_gate",
        "after": "launch_quality_gate",
    },
    {
        "trigger": "fail",
        "source": "*",
        "dest": "failed",
        "conditions": ["is_not_terminal"],
        "before": "save_state_on_failure",
    },
    {
        "trigger": "retry_quality",
        "source": "failed",
        "dest": "quality_gate",
        "conditions": ["manual_retry_requested"],
    },
]

def create_pipeline_machine(model: object, initial_state: str = "init") -> AsyncMachine:
    """Create the pipeline state machine with AsyncMachine."""
    return AsyncMachine(
        model=model,
        states=STATES,
        transitions=TRANSITIONS,
        initial=initial_state,
        auto_transitions=False,
        send_event=True,
        queued=True,
    )
```

### 3.5 `super_orchestrator/state.py`

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import json

@dataclass
class PipelineState:
    """Persisted state for the Super Orchestrator pipeline."""
    # Identity
    pipeline_id: str = ""
    prd_path: str = ""
    config_path: str = ""
    depth: str = "standard"

    # State machine
    current_state: str = "init"
    previous_state: str = ""

    # Phase tracking
    completed_phases: list[str] = field(default_factory=list)
    phase_artifacts: dict[str, list[str]] = field(default_factory=dict)

    # Architect tracking
    architect_retries: int = 0
    max_architect_retries: int = 2
    service_map_path: str = ""
    contract_registry_path: str = ""
    domain_model_path: str = ""

    # Builder tracking
    builder_statuses: dict[str, str] = field(default_factory=dict)
    builder_costs: dict[str, float] = field(default_factory=dict)
    builder_results: list[dict] = field(default_factory=list)
    total_builders: int = 0
    successful_builders: int = 0

    # Integration tracking
    services_deployed: list[str] = field(default_factory=list)
    integration_report_path: str = ""

    # Quality gate tracking
    quality_attempts: int = 0
    max_quality_retries: int = 3
    last_quality_results: dict[str, str] = field(default_factory=dict)
    quality_report_path: str = ""

    # Cost
    total_cost: float = 0.0
    phase_costs: dict[str, float] = field(default_factory=dict)
    budget_limit: float | None = None

    # Timing
    started_at: str = ""
    updated_at: str = ""

    # Interruption
    interrupted: bool = False
    interrupt_reason: str = ""

    # Schema version
    schema_version: int = 1

    def save(self, directory: str = ".super-orchestrator") -> Path: ...
    @classmethod
    def load(cls, directory: str = ".super-orchestrator") -> "PipelineState | None": ...
    @classmethod
    def clear(cls, directory: str = ".super-orchestrator") -> None: ...
```

### 3.6 `super_orchestrator/cost.py`

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class PhaseCost:
    phase_name: str
    cost_usd: float = 0.0
    start_time: str = ""
    end_time: str = ""
    sub_phases: dict[str, float] = field(default_factory=dict)

@dataclass
class PipelineCostTracker:
    phases: dict[str, PhaseCost] = field(default_factory=dict)
    budget_limit: float | None = None

    @property
    def total_cost(self) -> float: ...
    def add_phase_cost(self, phase: str, cost: float) -> None: ...
    def check_budget(self) -> tuple[bool, str]: ...
    def to_dict(self) -> dict: ...
```

### 3.7 `super_orchestrator/config.py`

```python
from dataclasses import dataclass, field

@dataclass
class ArchitectConfig:
    max_retries: int = 2
    timeout: int = 900
    auto_approve: bool = False

@dataclass
class BuilderConfig:
    max_concurrent: int = 3
    timeout_per_builder: int = 1800
    depth: str = "thorough"

@dataclass
class IntegrationConfig:
    timeout: int = 600
    traefik_image: str = "traefik:v3.6"
    compose_file: str = "docker-compose.yml"
    test_compose_file: str = "docker-compose.test.yml"

@dataclass
class QualityGateConfig:
    max_fix_retries: int = 3
    layer3_scanners: list[str] = field(default_factory=lambda: [
        "security", "cors", "logging", "trace", "secrets", "docker", "health"
    ])
    layer4_enabled: bool = True
    blocking_severity: str = "error"

@dataclass
class SuperOrchestratorConfig:
    architect: ArchitectConfig = field(default_factory=ArchitectConfig)
    builder: BuilderConfig = field(default_factory=BuilderConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    quality_gate: QualityGateConfig = field(default_factory=QualityGateConfig)
    budget_limit: float | None = None
    depth: str = "standard"
    phase_timeouts: dict[str, int] = field(default_factory=dict)
    build1_services_dir: str = ""
    agent_team_config_path: str = ""
```

### 3.8 `super_orchestrator/pipeline.py`

```python
# Key async functions — one per pipeline phase

async def run_architect_phase(
    prd_path: Path,
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
) -> float:
    """Run the Architect (Build 1) to decompose PRD into service map + contracts.
    Returns cost in USD.
    """
    ...

async def run_contract_registration(
    service_map_path: Path,
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
) -> float:
    """Register contracts with the Contract Engine (Build 1).
    Returns cost in USD.
    """
    ...

async def run_parallel_builders(
    builder_configs: list[dict],
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
    max_concurrent: int = 3,
) -> list[BuilderResult]:
    """Run multiple Builders (Build 2) in parallel with semaphore.
    Each Builder is a subprocess running agent-team.
    """
    ...

async def run_integration_phase(
    builder_results: list[BuilderResult],
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
) -> IntegrationReport:
    """Run the Integrator: deploy services, run contract tests, cross-service tests.
    Returns IntegrationReport.
    """
    ...

async def run_quality_gate(
    integration_report: IntegrationReport,
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
) -> QualityGateReport:
    """Run the 4-layer quality gate.
    Returns QualityGateReport.
    """
    ...

async def run_fix_pass(
    quality_report: QualityGateReport,
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
) -> float:
    """Feed violations back to relevant Builders for fix.
    Returns cost in USD.
    """
    ...

async def execute_pipeline(
    prd_path: Path,
    config: SuperOrchestratorConfig,
    state: PipelineState,
    tracker: PipelineCostTracker,
    shutdown: GracefulShutdown,
) -> None:
    """Main pipeline loop. Drives the state machine through all phases."""
    ...
```

### 3.9 `super_orchestrator/shutdown.py`

```python
class GracefulShutdown:
    """Signal handler that saves state on interrupt."""
    def __init__(self): ...
    def install(self) -> None: ...
    def _handle_signal(self, signum: int, frame: Any) -> None: ...
    def _emergency_save(self) -> None: ...
    @property
    def should_stop(self) -> bool: ...
```

### 3.10 `integrator/docker_orchestrator.py`

```python
class DockerOrchestrator:
    """Manages Docker Compose lifecycle for multi-service deployment."""

    def __init__(self, compose_file: Path, project_name: str = "super-team"): ...

    async def start_services(self) -> dict[str, ServiceInfo]: ...
    async def stop_services(self) -> None: ...
    async def wait_for_healthy(self, services: list[str], timeout: int = 120) -> dict[str, bool]: ...
    async def get_service_url(self, service_name: str, port: int) -> str: ...
    async def get_service_logs(self, service_name: str, tail: int = 100) -> str: ...
    async def restart_service(self, service_name: str) -> None: ...
    async def is_service_healthy(self, service_name: str) -> bool: ...
```

### 3.11 `integrator/contract_compliance.py`

```python
class ContractComplianceVerifier:
    """Orchestrates Schemathesis + Pact verification."""

    def __init__(self, contract_registry_path: Path, services: dict[str, str]): ...

    async def run_schemathesis_tests(self, service_name: str, openapi_url: str) -> list[ContractViolation]: ...
    async def run_pact_verification(self, provider_name: str, provider_url: str, pact_dir: Path) -> list[ContractViolation]: ...
    async def verify_all_services(self) -> IntegrationReport: ...
    def generate_compliance_report(self) -> str: ...
```

### 3.12 `quality_gate/gate_engine.py`

```python
class QualityGateEngine:
    """4-layer sequential quality gate with promotion/demotion logic."""

    def __init__(self, config: QualityGateConfig, project_root: Path): ...

    async def run_all_layers(
        self,
        builder_results: list[BuilderResult],
        integration_report: IntegrationReport,
    ) -> QualityGateReport: ...

    async def run_layer(self, layer: QualityLevel) -> LayerResult: ...

    def should_promote(self, current_layer: QualityLevel, result: LayerResult) -> bool:
        """Determine if results pass the gate to proceed to next layer."""
        ...

    def classify_violations(self, violations: list[ScanViolation]) -> dict[str, list[ScanViolation]]:
        """Group violations by severity for fix prioritization."""
        ...
```

### 3.13 `quality_gate/security_scanner.py`

```python
class SecurityScanner:
    """JWT, CORS, secrets scanning. Produces SEC-xxx, CORS-xxx, SEC-SECRET-xxx codes."""

    def __init__(self, project_root: Path): ...

    def scan_jwt_auth(self) -> list[ScanViolation]: ...
    def scan_jwt_misconfigurations(self) -> list[ScanViolation]: ...
    def scan_cors(self) -> list[ScanViolation]: ...
    def scan_secrets(self) -> list[ScanViolation]: ...
    def scan_all(self) -> list[ScanViolation]: ...
```

### 3.14 `quality_gate/adversarial_patterns.py`

```python
class AdversarialScanner:
    """ADV-001..006 adversarial patterns. Dead events, dead contracts, orphans, naming, races."""

    def __init__(self, project_root: Path): ...

    def detect_dead_events(self) -> list[ScanViolation]: ...
    def detect_dead_contracts(self) -> list[ScanViolation]: ...
    def detect_orphan_services(self) -> list[ScanViolation]: ...
    def check_naming_consistency(self) -> list[ScanViolation]: ...
    def scan_error_handling(self) -> list[ScanViolation]: ...
    def scan_race_conditions(self) -> list[ScanViolation]: ...
    def scan_all(self) -> list[ScanViolation]: ...
```

---

## 4. Data Flow Diagram

```
                              USER INPUT
                                  |
                              [PRD.md]
                                  |
                                  v
  +---------------------------------------------------------------+
  |                    SUPER ORCHESTRATOR CLI                       |
  |  (Typer app + AsyncMachine state machine + PipelineCostTracker)|
  +---------------------------------------------------------------+
        |                    |                    |
        v                    v                    v
  +-----------+    +------------------+    +---------------+
  | Phase 1:  |    | Phase 2:         |    | Phase 3:      |
  | ARCHITECT |--->| CONTRACT         |--->| BUILDERS      |
  | (Build 1  |    | REGISTRATION     |    | (Build 2      |
  |  MCP)     |    | (Build 1 MCP)    |    |  agent-team)  |
  +-----------+    +------------------+    +---------------+
        |                    |                    |
        v                    v                    v
  [ServiceMap.yaml]  [CONTRACTS.json]     [N x ServiceDir/]
  [DomainModel.yaml]                      [N x BuildReport]
                                                  |
                                                  v
                              +-----------------------------------+
                              |         Phase 4: INTEGRATOR        |
                              |  Docker Compose + Traefik + Tests  |
                              +-----------------------------------+
                                    |              |
                                    v              v
                            [docker-compose.yml]  [IntegrationReport]
                            [All services        [Contract test results]
                             deployed + healthy]  [Cross-service test results]
                                                  |
                                                  v
                              +-----------------------------------+
                              |     Phase 5: QUALITY GATE          |
                              |  4 Layers (sequential, gated)      |
                              +-----------------------------------+
                              | L1: Per-service (from Builders)    |
                              | L2: Contract compliance            |
                              |     (Schemathesis + Pact)          |
                              | L3: System-level                   |
                              |     (30 scan codes across 7 cats)  |
                              | L4: Adversarial review             |
                              |     (ADV-001..006)                 |
                              +-----------------------------------+
                                    |
                            pass?   |   fail?
                           +--------+--------+
                           |                 |
                           v                 v
                    [COMPLETE]         [FIX PASS]
                    [Final Report]     [Feed violations
                                       back to Builders]
                                            |
                                            v
                                     [Re-run Quality Gate]
                                     (up to max_fix_retries)
```

### Data Artifacts Produced Per Phase

| Phase | Input | Output |
|-------|-------|--------|
| Architect | PRD.md | ServiceMap.yaml, DomainModel.yaml, ContractRegistry/ |
| Contract Registration | ContractRegistry/ | CONTRACTS.json (validated + stored) |
| Builders (parallel) | CONTRACTS.json, per-service PRD | N service directories, N BuilderResults |
| Integrator | N service dirs, CONTRACTS.json | docker-compose.yml, IntegrationReport |
| Quality Gate L1 | BuilderResults | LayerResult (pass-through) |
| Quality Gate L2 | IntegrationReport, CONTRACTS | LayerResult (Schemathesis + Pact) |
| Quality Gate L3 | All source code | LayerResult (30 scan codes) |
| Quality Gate L4 | All source code | LayerResult (ADV-001..006) |
| Fix Pass | QualityGateReport | Updated service code, cost |

---

## 5. State Machine Design

### 5.1 States (11 total)

| # | State | Type | Description |
|---|-------|------|-------------|
| 1 | `init` | Initial | Pipeline loaded, config validated, PRD ready |
| 2 | `architect_running` | Active | Build 1 Architect decomposing PRD |
| 3 | `architect_review` | Decision | Review decomposition, approve/reject |
| 4 | `contracts_registering` | Active | Build 1 Contract Engine storing contracts |
| 5 | `builders_running` | Active | Build 2 Builders generating services (parallel) |
| 6 | `builders_complete` | Checkpoint | All builders finished, results collected |
| 7 | `integrating` | Active | Integrator deploying + testing cross-service |
| 8 | `quality_gate` | Active | 4-layer quality verification |
| 9 | `fix_pass` | Active | Remediation of quality gate failures |
| 10 | `complete` | Terminal | Pipeline succeeded |
| 11 | `failed` | Terminal | Pipeline failed (unrecoverable) |

### 5.2 Transition Table (13 transitions)

| # | Trigger | Source | Dest | Guard Condition | Callback |
|---|---------|--------|------|-----------------|----------|
| 1 | `start_architect` | init | architect_running | config loaded, PRD valid | `launch_architect_phase` |
| 2 | `architect_done` | architect_running | architect_review | ServiceMap + Contracts exist | -- |
| 3 | `approve_architecture` | architect_review | contracts_registering | review passed | `register_contracts` |
| 4 | `reject_architecture` | architect_review | architect_running | retries < max_architect_retries | `increment_architect_retries` |
| 5 | `contracts_ready` | contracts_registering | builders_running | CONTRACTS.json valid | `launch_builders` |
| 6 | `builders_done` | builders_running | builders_complete | >= 1 builder succeeded | -- |
| 7 | `start_integration` | builders_complete | integrating | -- | `launch_integration_phase` |
| 8 | `integration_done` | integrating | quality_gate | IntegrationReport exists | `launch_quality_gate` |
| 9 | `quality_passed` | quality_gate | complete | all layers passed | -- |
| 10 | `quality_failed` | quality_gate | fix_pass | quality_attempts < max_fix_retries | `launch_fix_pass` |
| 11 | `fix_done` | fix_pass | quality_gate | fix cycle complete | `launch_quality_gate` |
| 12 | `fail` | * (non-terminal) | failed | unrecoverable error | `save_state_on_failure` |
| 13 | `retry_quality` | failed | quality_gate | manual retry requested | -- |

### 5.3 Guard Condition Implementations

```python
def has_valid_prd(self, event) -> bool:
    return bool(self.prd_content) and len(self.prd_content) > 100

def has_valid_config(self, event) -> bool:
    return self.config is not None

def architect_outputs_exist(self, event) -> bool:
    return (
        Path(self.state.service_map_path).is_file()
        and Path(self.state.contract_registry_path).is_file()
    )

def review_approved(self, event) -> bool:
    return self._architect_review_verdict == "approved"

def retries_remaining(self, event) -> bool:
    return self.state.architect_retries < self.state.max_architect_retries

def contracts_valid(self, event) -> bool:
    return Path(self.state.contract_registry_path).is_file()

def at_least_one_builder_succeeded(self, event) -> bool:
    return self.state.successful_builders >= 1

def integration_report_exists(self, event) -> bool:
    return Path(self.state.integration_report_path).is_file()

def all_layers_passed(self, event) -> bool:
    return self._quality_report.overall_verdict == GateVerdict.PASSED

def fix_retries_remaining(self, event) -> bool:
    return self.state.quality_attempts < self.state.max_quality_retries

def is_not_terminal(self, event) -> bool:
    return self.state not in ("complete", "failed")

def manual_retry_requested(self, event) -> bool:
    return self._manual_retry
```

### 5.4 Resume Logic

```python
RESUME_TRIGGERS: dict[str, str] = {
    "init": "start_architect",
    "architect_running": "start_architect",
    "architect_review": "approve_architecture",
    "contracts_registering": "contracts_ready",
    "builders_running": "builders_done",       # Re-run failed builders only
    "builders_complete": "start_integration",
    "integrating": "start_integration",
    "quality_gate": "quality_passed",          # Re-check
    "fix_pass": "fix_done",
}
```

---

## 6. Quality Gate Layer Specification

### 6.1 Layer Overview

| Layer | Name | Input | Scanner | Blocking? |
|-------|------|-------|---------|-----------|
| L1 | Per-Service Quality | BuilderResults | Pass-through from agent-team | Yes (service must build+test) |
| L2 | Contract Compliance | Deployed services | Schemathesis + Pact | Yes |
| L3 | System-Level | All source code | 30 scan codes across 7 categories | Configurable by severity |
| L4 | Adversarial Review | All source code | ADV-001..006 heuristics | No (advisory) |

### 6.2 Layer 1: Per-Service Quality

**Source**: BuilderResults from each agent-team run.

| Check | Pass Condition |
|-------|---------------|
| Build success | `BuilderResult.success == True` |
| Test pass rate | `test_passed / test_total >= 0.9` |
| Convergence | `convergence_ratio >= 0.9` |

**Gating rule**: A service that fails Layer 1 is excluded from Layer 2 testing (no point testing contracts against a broken service).

### 6.3 Layer 2: Cross-Service Contract Compliance

**Tools**: Schemathesis 4.x + Pact Python 3.2.1

**Sub-checks**:

| Check | Tool | Description |
|-------|------|-------------|
| Schema conformance | Schemathesis `@schema.parametrize()` | Every response matches OpenAPI schema |
| Status code conformance | Schemathesis check | Responses use documented status codes |
| Response time | Schemathesis `--max-response-time` | Endpoints respond within threshold |
| Consumer contracts | Pact `Verifier.verify()` | Provider satisfies consumer expectations |
| Negative testing | Schemathesis `mode=negative` | Invalid inputs rejected (422/400) |

**Gating rule**: Services failing Layer 2 enter the fix loop. Services passing Layer 2 proceed to Layer 3.

### 6.4 Layer 3: System-Level (30 scan codes, 7 categories)

#### Category 1: Security (SEC-001..006)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| SEC-001 | Unauthenticated endpoint | Missing auth middleware/decorator | error |
| SEC-002 | Algorithm 'none' | `algorithms = ['none']` | critical |
| SEC-003 | Signature verification disabled | `verify_signature: False` | critical |
| SEC-004 | Expiration check disabled | `verify_exp: False` | high |
| SEC-005 | Hardcoded JWT secret | `JWT_SECRET = 'value'` | critical |
| SEC-006 | HS256 with public key | Algorithm confusion risk | high |

#### Category 2: CORS (CORS-001..003)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| CORS-001 | Wildcard origin | `allow_origins = ["*"]` | error |
| CORS-002 | Credentials + wildcard | `allow_credentials=True` + wildcard | critical |
| CORS-003 | Origin reflection | Dynamic origin without validation | high |

#### Category 3: Logging (LOG-001, LOG-004, LOG-005)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| LOG-001 | print() instead of logger | `print(` in .py files | warning |
| LOG-004 | console.log in production | `console.log(` in .ts/.js | warning |
| LOG-005 | Sensitive data in logs | password/secret/token in log calls | error |

#### Category 4: Trace Propagation (TRACE-001)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| TRACE-001 | Missing trace propagation | HTTP calls without traceparent injection | warning |

#### Category 5: Secrets (SEC-SECRET-001..012)

| Code | Name | Pattern | Severity |
|------|------|---------|----------|
| SEC-SECRET-001 | AWS Access Key | `AKIA[A-Z0-9]{16}` | critical |
| SEC-SECRET-002 | AWS Secret Key | `aws_secret.*=[A-Za-z0-9/+=]{40}` | critical |
| SEC-SECRET-003 | Private Key | `-----BEGIN.*PRIVATE KEY` | critical |
| SEC-SECRET-004 | Generic API Key | `api_key = '[a-z0-9]{20,}'` | high |
| SEC-SECRET-005 | DB Connection String | `postgres://user:pass@host` | critical |
| SEC-SECRET-006 | Bearer Token | Hardcoded bearer token | high |
| SEC-SECRET-007 | Hardcoded Password | `password = 'value'` | high |
| SEC-SECRET-008 | GitHub/GitLab Token | `ghp_`, `glpat-` patterns | critical |
| SEC-SECRET-009 | Stripe Keys | `sk_live_`, `pk_live_` | critical |
| SEC-SECRET-010 | Hardcoded JWT | `eyJ...` (3-segment base64) | high |
| SEC-SECRET-011 | Slack Token | `xox[baprs]-` pattern | high |
| SEC-SECRET-012 | SendGrid Key | `SG.[A-Za-z0-9_-]{22}...` | critical |

#### Category 6: Docker Security (DOCKER-001..008)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| DOCKER-001 | Runs as root | No `USER` directive | error |
| DOCKER-002 | Secrets in ENV | `ENV PASSWORD=value` | critical |
| DOCKER-003 | Unpinned tag | `FROM image:latest` or no tag | warning |
| DOCKER-004 | Broad COPY | `COPY . .` | warning |
| DOCKER-005 | No HEALTHCHECK | Missing `HEALTHCHECK` instruction | warning |
| DOCKER-006 | Privileged mode | `privileged: true` in compose | critical |
| DOCKER-007 | Host network | `network_mode: host` | warning |
| DOCKER-008 | Dangerous caps | `cap_add: SYS_ADMIN/ALL` | high |

#### Category 7: Health (HEALTH-001)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| HEALTH-001 | Missing health endpoint | No `/health`, `/healthz`, `/ready` route | warning |

### 6.5 Layer 4: Adversarial Review (ADV-001..006)

| Code | Name | Detection | Severity |
|------|------|-----------|----------|
| ADV-001 | Dead events | Published but never consumed | warning |
| ADV-002 | Dead contracts | Defined but never implemented | warning |
| ADV-003 | Orphan services | No inbound/outbound connections | warning |
| ADV-004 | Naming inconsistency | camelCase vs snake_case across boundaries | info |
| ADV-005 | Missing error handling | async without try-catch, bare except | warning |
| ADV-006 | Race conditions | Shared mutable state without locks | warning |

### 6.6 Promotion/Demotion Logic

```
Layer 1 PASS -> proceed to Layer 2
Layer 1 FAIL -> exclude service from L2+L3+L4, enter fix loop for that service

Layer 2 PASS -> proceed to Layer 3
Layer 2 FAIL (blocking) -> enter fix loop for contract violations
Layer 2 FAIL (non-blocking) -> proceed to Layer 3 with warnings

Layer 3 PASS -> proceed to Layer 4
Layer 3 FAIL (severity >= blocking_severity) -> enter fix loop
Layer 3 FAIL (severity < blocking_severity) -> proceed to Layer 4 with warnings

Layer 4 -> always advisory, never blocks
```

---

## 7. Docker Compose Template

```yaml
# docker-compose.yml — Super Agent Team Production
# Generated by the Super Orchestrator

version: "3.9"

services:
  # === API Gateway ===
  traefik:
    image: traefik:v3.6
    command:
      - "--api.dashboard=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedByDefault=false"
      - "--entrypoints.web.address=:80"
      - "--ping=true"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    healthcheck:
      test: ["CMD-SHELL", "traefik healthcheck --ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - frontend

  # === Database ===
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-superteam}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-superteam_secret}
      POSTGRES_DB: ${DB_NAME:-superteam}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    networks:
      - backend

  # === Cache ===
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - backend

  # === Migrations (run-once) ===
  migrations:
    build:
      context: ./migrations
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - backend

  # === Build 1: Architect Service ===
  architect:
    build:
      context: ./src/architect
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.architect.rule=PathPrefix(`/api/architect`)"
      - "traefik.http.services.architect.loadbalancer.server.port=8001"
      - "traefik.http.routers.architect.middlewares=architect-strip"
      - "traefik.http.middlewares.architect-strip.stripprefix.prefixes=/api/architect"
    networks:
      - frontend
      - backend

  # === Build 1: Contract Engine ===
  contract-engine:
    build:
      context: ./src/contract_engine
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.contract-engine.rule=PathPrefix(`/api/contracts`)"
      - "traefik.http.services.contract-engine.loadbalancer.server.port=8002"
      - "traefik.http.routers.contract-engine.middlewares=contracts-strip"
      - "traefik.http.middlewares.contracts-strip.stripprefix.prefixes=/api/contracts"
    networks:
      - frontend
      - backend

  # === Build 1: Codebase Intelligence ===
  codebase-intelligence:
    build:
      context: ./src/codebase_intelligence
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8003/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.codebase-intel.rule=PathPrefix(`/api/codebase`)"
      - "traefik.http.services.codebase-intel.loadbalancer.server.port=8003"
      - "traefik.http.routers.codebase-intel.middlewares=codebase-strip"
      - "traefik.http.middlewares.codebase-strip.stripprefix.prefixes=/api/codebase"
    networks:
      - frontend
      - backend

  # === User-defined services (generated per PRD) ===
  # Placeholder: the Integrator generates service entries dynamically
  # based on the Architect's ServiceMap output

volumes:
  pgdata:

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # Not accessible from host
```

---

## 8. MCP Tool Interfaces

### 8.1 Build 1 MCP Tools Consumed by Build 3 (17 tools)

#### Architect Service (3 tools)

| Tool | Signature | Build 3 Usage |
|------|-----------|---------------|
| `get_service_map()` | `() -> ServiceMap` | Super Orchestrator queries decomposition result |
| `get_contracts_for_service(service_name: str)` | `(str) -> list[Contract]` | Integrator loads contracts per service for testing |
| `get_domain_model()` | `() -> DomainModel` | Quality Gate checks domain consistency |

#### Contract Engine (7 tools)

| Tool | Signature | Build 3 Usage |
|------|-----------|---------------|
| `get_contract(contract_id: str)` | `(str) -> Contract` | Load specific contract for compliance check |
| `validate_endpoint(service: str, method: str, path: str, request_body: dict, response_body: dict, status_code: int)` | `(...) -> ValidationResult` | Runtime contract validation in Integrator |
| `generate_tests(contract_id: str, format: str)` | `(str, str) -> list[TestCase]` | Generate conformance tests per contract |
| `check_breaking_changes(contract_id: str, old_version: str, new_version: str)` | `(...) -> list[BreakingChange]` | Quality Gate L2 detects regressions |
| `mark_implemented(contract_id: str, service: str)` | `(str, str) -> None` | Builders mark contracts as implemented |
| `get_unimplemented_contracts(service: str)` | `(str) -> list[Contract]` | Quality Gate L4 finds gaps |
| `list_contracts()` | `() -> list[ContractSummary]` | Integrator enumerates all contracts |

#### Codebase Intelligence (7 tools)

| Tool | Signature | Build 3 Usage |
|------|-----------|---------------|
| `find_definition(symbol: str, language: str)` | `(str, str) -> Location` | Quality Gate traces symbol definitions |
| `find_callers(symbol: str)` | `(str) -> list[Location]` | Quality Gate impact analysis |
| `find_dependencies(file_path: str)` | `(str) -> DependencyGraph` | ADV-003 orphan detection |
| `search_semantic(query: str)` | `(str) -> list[CodeChunk]` | Discovery queries in adversarial review |
| `get_service_interface(service_name: str)` | `(str) -> ServiceInterface` | Integrator extracts public API surface |
| `check_dead_code(service_name: str)` | `(str) -> list[DeadCode]` | ADV-001/002 dead event/contract detection |
| `register_artifact(file_path: str, service_name: str)` | `(str, str) -> None` | Builders register generated code |

### 8.2 Build 2 Modules Consumed by Build 3 (16 modules)

| Module | Class/Function | Build 3 Usage |
|--------|----------------|---------------|
| `agent_teams_backend.py` | `ExecutionBackend` protocol | Builder dispatch interface |
| `agent_teams_backend.py` | `AgentTeamsBackend` | Agent Teams execution mode |
| `agent_teams_backend.py` | `CLIBackend` | CLI fallback mode |
| `agent_teams_backend.py` | `create_execution_backend()` | Factory for Builder creation |
| `contract_client.py` | `ContractEngineClient` | Typed MCP client for contracts |
| `codebase_client.py` | `CodebaseIntelligenceClient` | Typed MCP client for codebase |
| `hooks_manager.py` | `generate_hooks_config()` | Quality gate hooks for Builders |
| `claude_md_generator.py` | `generate_claude_md()` | Teammate context generation |
| `contract_scanner.py` | `run_contract_compliance_scan()` | CONTRACT-001..004 scanning |
| `mcp_client.py` | `create_contract_engine_session()` | MCP session management |
| `mcp_client.py` | `create_codebase_intelligence_session()` | MCP session management |
| `config.py` | `AgentTeamsConfig` | Agent Teams settings |
| `config.py` | `ContractEngineConfig` | Contract Engine settings |
| `config.py` | `CodebaseIntelligenceConfig` | Codebase Intelligence settings |
| `config.py` | `ContractScanConfig` | CONTRACT scan settings |
| `state.py` | `ContractReport` | Contract compliance state |

---

## 9. CLI Command Design

### 9.1 Command Overview (6 commands + 2 utility)

```
super-orchestrator [OPTIONS] COMMAND [ARGS]

Options:
  --config, -c PATH       Path to config.yaml
  --verbose, -v           Verbose output
  --depth DEPTH           Override depth (quick|standard|thorough|exhaustive)

Commands:
  init       Initialize a new build from a PRD file
  plan       Run the Architect to produce service decomposition
  build      Run Builders to produce service code
  integrate  Run the Integrator to deploy and test services
  verify     Run the Quality Gate verification
  run        Run full pipeline: plan -> build -> integrate -> verify
  status     Show current pipeline state and progress
  resume     Resume an interrupted pipeline from saved state
```

### 9.2 Command Details

#### `super-orchestrator init`

```
Arguments:
  PRD_PATH    Path to PRD file (required)

Options:
  --output-dir, -o PATH   Output directory (default: .)

Behavior:
  1. Validate PRD file exists and is > 100 bytes
  2. Create .super-orchestrator/ directory
  3. Copy PRD to .super-orchestrator/PRD.md
  4. Initialize PipelineState with pipeline_id (UUID)
  5. Write initial config.yaml if not present
```

#### `super-orchestrator plan`

```
Options:
  --system TEXT    Which system to plan (default: all)

Behavior:
  1. Load state from .super-orchestrator/
  2. Start Architect (Build 1 MCP) with PRD
  3. Wait for ServiceMap, ContractRegistry, DomainModel
  4. If --auto-approve in config: proceed to contracts
  5. Otherwise: print summary and wait for approval
  6. Save state after completion
```

#### `super-orchestrator build`

```
Options:
  --parallel/--sequential   Run builders in parallel (default: parallel)
  --system, -s INT          Build specific systems only (repeatable)
  --max-concurrent INT      Max concurrent builders (default: 3)

Behavior:
  1. Load state, verify contracts are registered
  2. Generate per-service PRD + config for each Builder
  3. Launch Builder subprocesses (agent-team with Build 2)
  4. Collect results with semaphore-bounded concurrency
  5. Report: N/M builders succeeded, total cost
  6. Save state with builder results
```

#### `super-orchestrator integrate`

```
Options:
  --compose-file PATH   Custom compose file path

Behavior:
  1. Load state, verify at least 1 builder succeeded
  2. Generate docker-compose.yml from ServiceMap + builder outputs
  3. Start services via DockerOrchestrator
  4. Wait for all health checks
  5. Run Schemathesis tests against each service
  6. Run Pact provider verification
  7. Run cross-service integration tests
  8. Generate IntegrationReport
  9. Stop services
  10. Save state
```

#### `super-orchestrator verify`

```
Options:
  --fix/--no-fix   Auto-fix failures (default: yes)
  --layer INT      Run specific layer only (1-4)

Behavior:
  1. Load state, verify integration report exists
  2. Run QualityGateEngine.run_all_layers()
  3. If failures and --fix: enter fix loop
  4. Fix loop: feed violations to Builders, re-run gate
  5. Repeat until pass or max_fix_retries
  6. Generate QualityGateReport
  7. Save state
```

#### `super-orchestrator run`

```
Arguments:
  PRD_PATH    Path to PRD file (required)

Options:
  --resume/--fresh   Resume from saved state (default: fresh)

Behavior:
  1. init + plan + build + integrate + verify (all phases)
  2. State machine drives transitions
  3. GracefulShutdown handler saves state on Ctrl+C
  4. Budget checking after each phase
  5. Rich terminal UI for progress display
```

#### `super-orchestrator status`

```
Behavior:
  1. Load PipelineState from .super-orchestrator/
  2. Display Rich table with:
     - Current state
     - Completed phases
     - Builder statuses
     - Quality gate results
     - Total cost
     - Elapsed time
```

#### `super-orchestrator resume`

```
Behavior:
  1. Load PipelineState
  2. Validate state (PRD exists, outputs present)
  3. Determine resume trigger from RESUME_TRIGGERS map
  4. Re-enter pipeline at saved state
```

### 9.3 Terminal UI Design (Rich)

```
+-----------------------------------------------------+
|              Super Orchestrator Pipeline              |
+-----------------------------------------------------+
| State: builders_running     | Cost: $45.30 / $200    |
| Phase: Build (3/5 complete) | Elapsed: 2h 15m        |
+-----------------------------------------------------+

+------------------+-----------+----------+
| Phase            | Status    | Cost     |
+------------------+-----------+----------+
| Architect        | DONE      | $12.50   |
| Contracts        | DONE      | $0.30    |
| Builders         | RUNNING   | $32.50   |
|   auth-service   |   DONE    |   $8.20  |
|   core-api       |   RUNNING |   $12.40 |
|   billing        |   DONE    |   $7.90  |
|   notifications  |   PENDING |   $0.00  |
|   gateway        |   RUNNING |   $4.00  |
| Integration      | PENDING   | $0.00   |
| Quality Gate     | PENDING   | $0.00   |
+------------------+-----------+----------+
```

---

## 10. Milestone Dependency Graph

### 10.1 Milestone DAG (7 milestones)

```
M1: Shared Models + Config + State Machine
    |
    +----> M2: Super Orchestrator Core
    |          |
    +----> M3: Quality Gate Engine
    |          |
    |          +----> M4: Integration Layer (depends M2, M3)
    |                     |
    |                     +----> M5: CLI + Docker Orchestration (depends M4)
    |                     |
    |                     +----> M6: Integrator Tests + Contract Tests (depends M4)
    |                                 |
    |                                 +----> M7: E2E Verification (depends M5, M6)
```

### 10.2 Milestone Details

| Milestone | Title | Dependencies | Estimated LOC | Key Deliverables |
|-----------|-------|-------------|---------------|-----------------|
| M1 | Shared Models, Config, State Machine Engine | none | ~2,500 | `shared/`, `state_machine.py`, `state.py`, `cost.py`, `config.py`, `shutdown.py` |
| M2 | Super Orchestrator Core | milestone-1 | ~2,000 | `pipeline.py` (all phase functions), subprocess management |
| M3 | Quality Gate Engine | milestone-1 | ~4,500 | `quality_gate/` (all scanners, gate engine, 30 scan codes) |
| M4 | Integration Layer | milestone-2, milestone-3 | ~5,000 | `integrator/` (Docker, Traefik, Schemathesis, Pact, cross-service tests) |
| M5 | CLI + Docker Orchestration | milestone-4 | ~1,500 | `cli.py`, `display.py`, docker-compose template, Traefik config |
| M6 | Integrator Tests + Contract Tests | milestone-4 | ~4,000 | `tests/` (unit + integration tests for all modules) |
| M7 | E2E Verification + Backward Compat | milestone-5, milestone-6 | ~3,800 | Full pipeline test with 3-service app, backward compat checks |

### 10.3 Milestone Execution Order

```
1. M1 (no deps)          -> foundation for everything
2. M2 + M3 (parallel)    -> orchestrator core + quality gate (both depend only on M1)
3. M4 (needs M2 + M3)    -> integration layer wires orchestrator + quality gate
4. M5 + M6 (parallel)    -> CLI/Docker + tests (both depend only on M4)
5. M7 (needs M5 + M6)    -> full pipeline E2E test
```

---

## 11. Integration Points with Build 1+2

### 11.1 Build 1 Integration Points

| Integration | Mechanism | Direction | Module |
|------------|-----------|-----------|--------|
| Architect decomposition | MCP stdio | Build 3 -> Build 1 | `pipeline.py:run_architect_phase()` |
| Contract registration | MCP stdio | Build 3 -> Build 1 | `pipeline.py:run_contract_registration()` |
| Contract validation | MCP stdio | Build 3 -> Build 1 | `integrator/contract_compliance.py` |
| Test generation | MCP stdio | Build 3 -> Build 1 | `integrator/contract_compliance.py` |
| Codebase queries | MCP stdio | Build 3 -> Build 1 | `quality_gate/adversarial_patterns.py` |
| Dead code detection | MCP stdio | Build 3 -> Build 1 | `quality_gate/adversarial_patterns.py` |
| Docker hosting | Docker Compose | Build 3 manages Build 1 | `integrator/docker_orchestrator.py` |
| Health monitoring | HTTP GET /health | Build 3 -> Build 1 | `integrator/service_discovery.py` |

### 11.2 Build 2 Integration Points

| Integration | Mechanism | Direction | Module |
|------------|-----------|-----------|--------|
| Builder dispatch | Subprocess (`python -m agent_team`) | Build 3 -> Build 2 | `pipeline.py:run_parallel_builders()` |
| Cost aggregation | RunState.total_cost (JSON) | Build 2 -> Build 3 | `cost.py:PipelineCostTracker` |
| Build report | RunState artifacts | Build 2 -> Build 3 | `pipeline.py` |
| Contract scanning | `run_contract_compliance_scan()` | Build 2 internal | Runs within each Builder |
| Hooks enforcement | `generate_hooks_config()` | Build 3 -> Build 2 config | `pipeline.py` |
| Config inheritance | YAML config per Builder | Build 3 -> Build 2 | `pipeline.py` |

### 11.3 Cross-Build Data Flow

```
Build 1 (Architect) --[MCP]--> Build 3 (Super Orchestrator)
  ServiceMap.yaml, ContractRegistry/, DomainModel.yaml

Build 1 (Contract Engine) --[MCP]--> Build 3 (Integrator)
  validate_endpoint(), generate_tests(), check_breaking_changes()

Build 1 (Codebase Intelligence) --[MCP]--> Build 3 (Quality Gate)
  find_callers(), check_dead_code(), get_service_interface()

Build 3 (Super Orchestrator) --[subprocess]--> Build 2 (Builder Fleet)
  Per-service PRD + config.yaml + CONTRACTS.json

Build 2 (Builder Fleet) --[RunState JSON]--> Build 3 (Super Orchestrator)
  BuilderResult (success, cost, test results, artifacts)

Build 3 (Integrator) --[Docker Compose]--> All service containers
  Start/stop/health-check all services for integration testing
```

### 11.4 Configuration Inheritance

The Super Orchestrator generates per-Builder configs by scoping the global config:

```python
def generate_builder_config(
    global_config: SuperOrchestratorConfig,
    service_info: ServiceInfo,
    contracts_path: Path,
) -> dict:
    """Generate a scoped config.yaml for one Builder."""
    return {
        "depth": global_config.builder.depth,
        "milestone": {
            "enabled": True,
            "health_gate": True,
            "wiring_check": True,
        },
        "e2e_testing": {
            "enabled": True,
            "backend_api_tests": True,
            "frontend_playwright_tests": service_info.stack.get("frontend") is not None,
        },
        "post_orchestration_scans": {
            "mock_data_scan": True,
            "api_contract_scan": True,
        },
        "contract_engine": {
            "enabled": True,
            "server_command": f"mcp-connect {global_config.build1_services_dir}/contract_engine",
        },
        "codebase_intelligence": {
            "enabled": True,
            "server_command": f"mcp-connect {global_config.build1_services_dir}/codebase_intelligence",
        },
    }
```

---

## 12. Risk Assessment

### Risk 1: `transitions` Library AsyncMachine + asyncio.run() Nesting

**Severity**: HIGH
**Description**: The existing agent-team uses `asyncio.run()` from synchronous CLI commands. AsyncMachine callbacks are async. If the Super Orchestrator CLI calls `asyncio.run()` and inside that, a transition callback also tries `asyncio.run()`, this causes `RuntimeError: cannot be called from a running event loop`.
**Mitigation**: All phase functions are `async def`. The CLI entry point calls `asyncio.run()` exactly once. All subsequent calls use `await`. State machine callbacks are `async` and use `await` internally. No nested `asyncio.run()`.
**Evidence**: This is the same pattern issue found and noted in Build 2 (the "CRITICAL pre-existing architectural issue" in browser testing review).

### Risk 2: Docker Compose Health Check Timing

**Severity**: MEDIUM
**Description**: Services may take variable time to become healthy. If `start_period` is too short, the health check counts failures during startup. If too long, genuine failures are masked.
**Mitigation**: Use generous `start_period: 30s` for all application services. Use `interval: 10s` for responsive detection after startup. The `DockerOrchestrator.wait_for_healthy()` has its own timeout (120s default) independent of Docker's health check.

### Risk 3: Schemathesis + Pact Running Against Live Services

**Severity**: MEDIUM
**Description**: Schemathesis property-based testing generates random inputs. Against a live service with a real database, this can create garbage data, trigger rate limits, or cause cascading failures.
**Mitigation**: Use a dedicated `docker-compose.test.yml` with isolated test databases seeded with known state. Schemathesis runs with `--max-examples 50` (limited). Pact provider states set up known data via the `/_pact/state` endpoint. Tests run in a Testcontainers-managed lifecycle with cleanup.

### Risk 4: Builder Subprocess Isolation

**Severity**: LOW
**Description**: Builders run as subprocesses in separate directories. If two Builders write to the same shared file (e.g., a shared types package), race conditions can occur.
**Mitigation**: The Architect's ServiceMap defines clear service boundaries. Each Builder operates in its own directory. Shared types are defined in contracts (CONTRACTS.json) and are read-only for Builders. The only shared write is `register_artifact()` to the Codebase Intelligence index, which handles concurrent writes internally.

### Risk 5: Quality Gate False Positives

**Severity**: MEDIUM
**Description**: The 30 static analysis scan codes will produce false positives, especially SEC-001 (may flag intentionally public endpoints) and ADV-001/002 (may flag internal-only patterns).
**Mitigation**: Layer 3 violations at "warning" severity are non-blocking by default. Layer 4 (adversarial) is entirely advisory. The `blocking_severity` config controls what blocks the pipeline (default: "error"). False positives can be suppressed via inline comments (`# nosec`, `# noqa: SEC-001`).

### Risk 6: Cost Budget Overrun

**Severity**: MEDIUM
**Description**: With N parallel Builders at ~$10-20 each, plus Architect ($12) and integration ($5-10), a 5-service build costs $70-120. Budget overrun happens if fix loops trigger multiple Builder re-runs.
**Mitigation**: `PipelineCostTracker.check_budget()` runs after every phase. Budget warning at 80%. Hard stop at 100%. Fix loops are capped at `max_fix_retries` (default: 3). Each fix pass targets only the violating service, not all services.

### Risk 7: State Persistence Across Crashes

**Severity**: LOW
**Description**: If the Super Orchestrator crashes between state saves, the resume logic may re-run completed work.
**Mitigation**: State is saved after EVERY phase transition (in `on_enter_*` callbacks). The `atomic_write_json()` pattern (tmp+rename) prevents corruption. The resume logic re-checks actual file existence, not just state flags, so re-running a completed phase is safe (idempotent).

### Risk 8: Agent Teams Experimental Nature

**Severity**: HIGH
**Description**: Claude Code Agent Teams (used in Build 2 Builders) is experimental. No session resumption, no nested teams. If Agent Teams proves unreliable, Builders fall back to CLI mode, which is slower but proven.
**Mitigation**: Build 2's `create_execution_backend()` factory supports both `AgentTeamsBackend` and `CLIBackend`. The Super Orchestrator config can set `builder.use_agent_teams: false` to force CLI mode. This is a per-Builder decision, not global.

### Risk 9: Cross-Service Test Generation Quality

**Severity**: MEDIUM
**Description**: Generating meaningful cross-service integration tests requires understanding multi-service data flows. The test generator works from contracts (structured) rather than implementation (unstructured), which limits coverage to contracted behaviors.
**Mitigation**: Layer 2 (contract compliance) covers all contracted behaviors. Layer 3 adds static analysis for system-level concerns. Layer 4 (adversarial) hunts for uncontracted behaviors. The combination of four layers compensates for any single layer's gaps.

### Risk 10: Traefik Docker Provider Discovery Lag

**Severity**: LOW
**Description**: Traefik's Docker provider discovers containers via the Docker socket. There's a brief lag between container startup and route registration.
**Mitigation**: The `wait_for_healthy()` function waits for both Docker health checks AND Traefik route availability (via Traefik's API). Tests don't start until both conditions are met.

---

## Appendix A: PRD Format Notes (from BUILD3_CODEBASE_RESEARCH.md)

The Build 3 PRD MUST follow these formatting rules for the agent-team v14 parser:

1. **Milestone headers**: `## Milestone N: Title` (h2-h4, NOT h1)
2. **Milestone metadata**: `- ID: milestone-N`, `- Status: PENDING`, `- Dependencies: milestone-X, milestone-Y`, `- Description: ...`
3. **Requirement checklist**: `- [ ] PREFIX-NNN: Description (review_cycles: 0)`
4. **Global numbering**: REQ-001 through REQ-XXX across ALL milestones (do NOT restart per milestone)
5. **SVC table**: 7-column format with `{ field: type }` notation for API contract scan
6. **Dependencies**: `milestone-N` format, comma-separated, parenthetical comments stripped
7. **Review authority**: Only code-reviewer agents mark `[x]`
8. **Build 2 format**: Use full structured metadata (not Build 1's inline-only format)
9. **No Architecture Decision section**: That goes in REQUIREMENTS.md, not the PRD
10. **Status Registry**: Include if entities have state machines
11. **PRD size**: Likely > 50KB, design with clean `##` boundaries for chunking

## Appendix B: Config Template for Build 3

```yaml
# Build 3 — Super Agent Team config.yaml
depth: "thorough"

milestone:
  enabled: true
  health_gate: true
  wiring_check: true
  review_recovery_retries: 2

convergence:
  min_convergence_ratio: 0.9
  recovery_threshold: 0.8

tech_research:
  enabled: true
  max_techs: 8
  max_queries_per_tech: 4

e2e_testing:
  enabled: true
  max_fix_retries: 3
  backend_api_tests: true
  frontend_playwright_tests: false

post_orchestration_scans:
  mock_data_scan: true
  api_contract_scan: true
  silent_data_loss_scan: true
  endpoint_xref_scan: true
  ui_compliance_scan: false

integrity_scans:
  deployment_scan: true
  prd_reconciliation: true

database_scans:
  dual_orm_scan: true
  default_value_scan: true
  relationship_scan: true
```

---

*Architecture plan completed by the Architecture Planner agent. All specifications derived from 8 research documents totaling ~10,000 lines of technical analysis. Ready for PRD writer consumption.*
