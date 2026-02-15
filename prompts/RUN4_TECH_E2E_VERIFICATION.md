# Run 4 — E2E Verification Technical Research

End-to-end verification patterns, pytest infrastructure, and test tooling for validating that Builds 1, 2, and 3 work together as a unified pipeline.

---

## Table of Contents

1. [Multi-System Pipeline Testing Patterns](#1-multi-system-pipeline-testing-patterns)
2. [pytest Fixture Design for Cross-System Tests](#2-pytest-fixture-design-for-cross-system-tests)
3. [Testcontainers Compose Module](#3-testcontainers-compose-module)
4. [httpx Async Client for Multi-Service Health Polling](#4-httpx-async-client-for-multi-service-health-polling)
5. [Subprocess Orchestration for Parallel Verification](#5-subprocess-orchestration-for-parallel-verification)
6. [Test Data and Fixture Specifications](#6-test-data-and-fixture-specifications)
7. [Verification Matrix Design](#7-verification-matrix-design)
8. [Recommendations](#8-recommendations)

---

## 1. Multi-System Pipeline Testing Patterns

### 1.1 Phase-Gated Verification

The complete pipeline has 7 phases, each of which must pass before the next starts. This is a strict sequential gate — not a suggestion.

```
Phase 1: Build 1 Service Health
    ├── Architect API responds on :8001
    ├── Contract Engine API responds on :8002
    └── Codebase Intelligence API responds on :8003
         │
         ▼ GATE: all 3 healthy
Phase 2: MCP Tool Smoke Tests
    ├── Architect MCP: decompose tool callable
    ├── Contract Engine MCP: 6 tools callable
    └── Codebase Intelligence MCP: 7 tools callable
         │
         ▼ GATE: all 16 tools respond
Phase 3: Architect Decomposition
    ├── Feed sample PRD to Architect
    ├── Receive ServiceMap with 3 services
    ├── Receive DomainModel with entities
    └── Receive contract stubs
         │
         ▼ GATE: valid ServiceMap + DomainModel
Phase 4: Contract Registration
    ├── Register contract stubs with Contract Engine
    ├── Validate all contracts stored
    └── Verify contract retrieval works
         │
         ▼ GATE: all contracts registered + valid
Phase 5: Parallel Builder Execution
    ├── Launch 3 Builders (one per service)
    ├── Each Builder runs agent-team pipeline
    ├── Each Builder registers artifacts with Codebase Intelligence
    └── Collect BuilderResult per service
         │
         ▼ GATE: >= 2/3 builders succeed
Phase 6: Integration + Deployment
    ├── Generate docker-compose.yml from builder outputs
    ├── Deploy via Docker Compose + Traefik
    ├── Health check all services
    ├── Run contract compliance (Schemathesis)
    └── Run cross-service integration tests
         │
         ▼ GATE: all services healthy + >70% contract compliance
Phase 7: Quality Gate + Fix Pass
    ├── Layer 1: per-service quality
    ├── Layer 2: contract compliance
    ├── Layer 3: system-level (security, observability)
    ├── Layer 4: adversarial review
    └── Fix pass if blocking violations found
         │
         ▼ GATE: overall_verdict != "failed"
```

**Implementation pattern — phase executor with gating:**

```python
import pytest
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PhaseResult:
    phase_name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0

class PipelineVerifier:
    """Drives phases sequentially with strict gating."""

    def __init__(self):
        self.results: list[PhaseResult] = []
        self._artifacts: dict[str, Any] = {}

    def run_phase(self, phase_name: str, executor, **kwargs) -> PhaseResult:
        """Run a single phase. Raises if gate fails."""
        import time
        start = time.monotonic()
        try:
            result = executor(**kwargs, artifacts=self._artifacts)
            elapsed = time.monotonic() - start
            phase_result = PhaseResult(
                phase_name=phase_name,
                passed=result.get("passed", False),
                errors=result.get("errors", []),
                artifacts=result.get("artifacts", {}),
                duration_seconds=elapsed,
            )
        except Exception as e:
            elapsed = time.monotonic() - start
            phase_result = PhaseResult(
                phase_name=phase_name,
                passed=False,
                errors=[str(e)],
                duration_seconds=elapsed,
            )

        self.results.append(phase_result)
        self._artifacts.update(phase_result.artifacts)

        if not phase_result.passed:
            raise PhaseGateError(
                f"Phase '{phase_name}' failed: {phase_result.errors}"
            )
        return phase_result

class PhaseGateError(Exception):
    pass
```

### 1.2 Partial Pipeline Testing

Not every test run needs to exercise the full pipeline. Partial testing accelerates development by verifying subsections independently.

| Test Scope | Phases Exercised | When to Use |
|---|---|---|
| Build 1 smoke | 1-2 only | After Build 1 deployment changes |
| Architect flow | 1-4 | After decomposition logic changes |
| Builder integration | 1-5 | After Build 2 changes |
| Full pipeline | 1-7 | Release verification, nightly CI |

**Implementation — pytest marks for scope selection:**

```python
import pytest

# Mark definitions
build1_only = pytest.mark.build1
architect_flow = pytest.mark.architect_flow
builder_integration = pytest.mark.builder_integration
full_pipeline = pytest.mark.full_pipeline

@pytest.mark.build1
def test_architect_health(build1_services):
    assert build1_services["architect"].is_healthy()

@pytest.mark.full_pipeline
def test_complete_pipeline(pipeline_verifier):
    # Only runs with: pytest -m full_pipeline
    pipeline_verifier.run_phase("health", check_health)
    pipeline_verifier.run_phase("mcp_smoke", check_mcp_tools)
    # ... all 7 phases
```

### 1.3 Pipeline State Checkpoint and Resume

When a phase fails, the pipeline should save its state so the next run can resume from the failure point instead of re-running everything.

```python
import json
from pathlib import Path
from datetime import datetime, timezone

@dataclass
class PipelineCheckpoint:
    last_completed_phase: int  # 0-indexed
    phase_artifacts: dict[str, Any]
    timestamp: str
    errors: list[str] = field(default_factory=list)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({
                "last_completed_phase": self.last_completed_phase,
                "phase_artifacts": self.phase_artifacts,
                "timestamp": self.timestamp,
                "errors": self.errors,
            }, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)

    @classmethod
    def load(cls, path: Path) -> "PipelineCheckpoint | None":
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None
```

**Usage in the verifier:**

```python
CHECKPOINT_PATH = Path(".run4-verification/checkpoint.json")

def run_e2e_verification(resume: bool = False):
    verifier = PipelineVerifier()
    start_phase = 0

    if resume:
        checkpoint = PipelineCheckpoint.load(CHECKPOINT_PATH)
        if checkpoint:
            start_phase = checkpoint.last_completed_phase + 1
            verifier._artifacts = checkpoint.phase_artifacts

    phases = [
        ("build1_health", phase1_health),
        ("mcp_smoke", phase2_mcp_smoke),
        ("architect_decomposition", phase3_architect),
        ("contract_registration", phase4_contracts),
        ("parallel_builders", phase5_builders),
        ("integration_deployment", phase6_integration),
        ("quality_gate", phase7_quality),
    ]

    for i, (name, executor) in enumerate(phases):
        if i < start_phase:
            continue
        try:
            verifier.run_phase(name, executor)
            PipelineCheckpoint(
                last_completed_phase=i,
                phase_artifacts=verifier._artifacts,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).save(CHECKPOINT_PATH)
        except PhaseGateError:
            PipelineCheckpoint(
                last_completed_phase=i - 1,
                phase_artifacts=verifier._artifacts,
                timestamp=datetime.now(timezone.utc).isoformat(),
                errors=[str(verifier.results[-1].errors)],
            ).save(CHECKPOINT_PATH)
            raise
```

---

## 2. pytest Fixture Design for Cross-System Tests

### 2.1 Fixture Hierarchy

The fixture chain follows the dependency order: Docker Compose startup (session) -> service health (session) -> client creation (module) -> test isolation (function).

```
session-scoped                module-scoped          function-scoped
┌────────────────┐   ┌───────────────────┐   ┌──────────────────┐
│ docker_compose │──▶│ service_clients   │──▶│ clean_test_state │
│ (start/stop)   │   │ (httpx clients)   │   │ (reset per test) │
└────────────────┘   └───────────────────┘   └──────────────────┘
        │                     │
        ▼                     ▼
┌────────────────┐   ┌───────────────────┐
│ service_urls   │   │ mcp_sessions      │
│ (port mapping) │   │ (MCP clients)     │
└────────────────┘   └───────────────────┘
```

### 2.2 Session-Scoped Fixtures (Docker Compose Startup)

```python
import pytest
import asyncio
from pathlib import Path
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy, LogMessageWaitStrategy


@pytest.fixture(scope="session")
def docker_compose():
    """Start all Build 1 + Build 3 services via Docker Compose.

    Session-scoped: starts once, shared across ALL tests.
    Cleanup happens after all tests complete.
    """
    compose = DockerCompose(
        context=str(Path(__file__).parent.parent / "super-team"),
        compose_file_name="docker-compose.yml",
    )

    with compose.waiting_for({
        "architect": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
        "contract-engine": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
        "codebase-intel": HttpWaitStrategy(8000).for_status_code(200).for_path("/api/health"),
    }):
        yield compose
    # DockerCompose context manager handles teardown (docker compose down)


@pytest.fixture(scope="session")
def service_urls(docker_compose: DockerCompose) -> dict[str, str]:
    """Resolve mapped ports to localhost URLs for each service."""
    urls = {}
    services = {
        "architect": 8000,
        "contract-engine": 8000,
        "codebase-intel": 8000,
    }
    for service_name, internal_port in services.items():
        host = docker_compose.get_service_host(service_name, internal_port)
        port = docker_compose.get_service_port(service_name, internal_port)
        urls[service_name] = f"http://{host}:{port}"
    return urls
```

### 2.3 Module-Scoped Fixtures (Service Health Verification)

```python
import httpx

@pytest.fixture(scope="module")
def verified_services(service_urls: dict[str, str]) -> dict[str, str]:
    """Verify all services are healthy before running module tests.

    Module-scoped: re-checks health at the start of each test module.
    This catches services that became unhealthy between modules.
    """
    unhealthy = []
    for name, url in service_urls.items():
        try:
            resp = httpx.get(f"{url}/api/health", timeout=5.0)
            if resp.status_code != 200:
                unhealthy.append(f"{name}: status {resp.status_code}")
        except httpx.RequestError as e:
            unhealthy.append(f"{name}: {e}")

    if unhealthy:
        pytest.fail(f"Unhealthy services: {', '.join(unhealthy)}")
    return service_urls


@pytest.fixture(scope="module")
def architect_client(verified_services: dict[str, str]) -> httpx.Client:
    """HTTP client pre-configured for the Architect service."""
    with httpx.Client(
        base_url=verified_services["architect"],
        timeout=httpx.Timeout(30.0, connect=10.0),
    ) as client:
        yield client


@pytest.fixture(scope="module")
def contract_engine_client(verified_services: dict[str, str]) -> httpx.Client:
    """HTTP client pre-configured for the Contract Engine service."""
    with httpx.Client(
        base_url=verified_services["contract-engine"],
        timeout=httpx.Timeout(30.0, connect=10.0),
    ) as client:
        yield client
```

### 2.4 Function-Scoped Fixtures (Test Isolation)

```python
@pytest.fixture
def clean_contract_state(contract_engine_client: httpx.Client):
    """Ensure clean contract state for each test.

    Function-scoped: runs before and after each test function.
    """
    # Capture initial state
    resp = contract_engine_client.get("/api/contracts")
    initial_ids = {c["id"] for c in resp.json().get("items", [])}

    yield

    # Cleanup: delete contracts created during the test
    resp = contract_engine_client.get("/api/contracts")
    for contract in resp.json().get("items", []):
        if contract["id"] not in initial_ids:
            contract_engine_client.delete(f"/api/contracts/{contract['id']}")


@pytest.fixture
def sample_prd_text() -> str:
    """Load the 3-service sample PRD for testing."""
    prd_path = Path(__file__).parent / "fixtures" / "sample_prd.md"
    return prd_path.read_text(encoding="utf-8")
```

### 2.5 Fixture Dependency Chain (Complete)

```python
# conftest.py — the complete chain

@pytest.fixture(scope="session")
def docker_compose():
    # Level 0: Infrastructure
    ...

@pytest.fixture(scope="session")
def service_urls(docker_compose):
    # Level 1: Port resolution (depends on compose)
    ...

@pytest.fixture(scope="module")
def verified_services(service_urls):
    # Level 2: Health verification (depends on URLs)
    ...

@pytest.fixture(scope="module")
def architect_client(verified_services):
    # Level 3: HTTP clients (depends on health)
    ...

@pytest.fixture
def decomposition_result(architect_client, sample_prd_text):
    # Level 4: Test-specific data (depends on client)
    resp = architect_client.post(
        "/api/decompose",
        json={"prd_text": sample_prd_text},
    )
    assert resp.status_code == 201
    return resp.json()
```

### 2.6 Shared Test Data Management

```python
@pytest.fixture(scope="session")
def shared_test_data(tmp_path_factory) -> Path:
    """Create a session-scoped temp directory for shared test artifacts.

    All tests can write intermediate artifacts here (contract files,
    builder output, etc.) without polluting the project directory.
    """
    return tmp_path_factory.mktemp("run4_e2e")


@pytest.fixture(scope="session")
def builder_output_dirs(shared_test_data: Path) -> dict[str, Path]:
    """Pre-create builder output directories for the 3-service test app."""
    dirs = {}
    for service in ["auth-service", "order-service", "notification-service"]:
        d = shared_test_data / "builders" / service
        d.mkdir(parents=True, exist_ok=True)
        dirs[service] = d
    return dirs
```

---

## 3. Testcontainers Compose Module

### 3.1 DockerCompose from pytest

Testcontainers Python provides a `DockerCompose` class that manages Docker Compose from within pytest. It handles startup, readiness, port mapping, and teardown.

**Key API (testcontainers 4.x):**

```python
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy, LogMessageWaitStrategy

# Construction
compose = DockerCompose(
    context="./path/to/project",       # Directory containing docker-compose.yml
    compose_file_name="docker-compose.yml",  # Can be a list for overlays
)

# Start with readiness detection
with compose.waiting_for({
    "service-name": HttpWaitStrategy(port).for_status_code(200).for_path("/health"),
    "db": LogMessageWaitStrategy("database system is ready"),
}):
    # Services are ready here
    host = compose.get_service_host("service-name", port)
    port = compose.get_service_port("service-name", port)
    # ... run tests ...

# Multiple compose files (overlay pattern)
compose = DockerCompose(
    context="./",
    compose_file_name=["docker-compose.yml", "docker-compose.test.yml"],
)
```

### 3.2 Service Readiness Detection for Run 4

Each Build 1 service has a `/api/health` endpoint returning `HealthStatus`. Use `HttpWaitStrategy` for all three.

```python
BUILD1_WAIT_STRATEGIES = {
    "architect": (
        HttpWaitStrategy(8000)
        .for_status_code(200)
        .for_path("/api/health")
        .with_startup_timeout(60)
    ),
    "contract-engine": (
        HttpWaitStrategy(8000)
        .for_status_code(200)
        .for_path("/api/health")
        .with_startup_timeout(60)
    ),
    "codebase-intel": (
        HttpWaitStrategy(8000)
        .for_status_code(200)
        .for_path("/api/health")
        .with_startup_timeout(90)  # ChromaDB init takes longer
    ),
}
```

For Build 3 services (user-generated services deployed via Traefik), readiness is detected by the Integrator's `ServiceDiscovery.wait_all_healthy()`.

### 3.3 Port Mapping and Service URL Resolution

Docker Compose maps internal container ports to random host ports. Testcontainers resolves these.

```python
def get_service_url(compose: DockerCompose, service: str, internal_port: int) -> str:
    """Resolve a service's internal port to a reachable localhost URL."""
    host = compose.get_service_host(service, internal_port)
    port = compose.get_service_port(service, internal_port)
    return f"http://{host}:{port}"
```

**For Run 4 specifically:**

| Service | Internal Port | Host Port | URL Pattern |
|---|---|---|---|
| architect | 8000 | dynamic | `http://localhost:{mapped}/api/` |
| contract-engine | 8000 | dynamic | `http://localhost:{mapped}/api/` |
| codebase-intel | 8000 | dynamic | `http://localhost:{mapped}/api/` |
| traefik | 80 | dynamic | `http://localhost:{mapped}/` |
| traefik (dashboard) | 8080 | dynamic | `http://localhost:{mapped}/dashboard/` |
| postgres | 5432 | dynamic | `postgresql://localhost:{mapped}/` |

### 3.4 Container Lifecycle Management

```python
@pytest.fixture(scope="session")
def build1_compose():
    """Full lifecycle: start -> wait -> yield -> stop."""
    compose = DockerCompose(
        context="./super-team",
        compose_file_name="docker-compose.yml",
    )

    with compose.waiting_for(BUILD1_WAIT_STRATEGIES):
        yield compose
    # `with` block exit triggers: docker compose down --remove-orphans --volumes


@pytest.fixture(scope="session")
def build3_compose(build1_compose):
    """Build 3 test services — depends on Build 1 being up.

    Uses a separate compose file for the generated test services.
    """
    compose = DockerCompose(
        context="./super-team",
        compose_file_name="docker-compose.test.yml",
    )

    with compose.waiting_for({
        "auth-service": HttpWaitStrategy(8080).for_status_code(200).for_path("/health"),
        "order-service": HttpWaitStrategy(8080).for_status_code(200).for_path("/health"),
        "notification-service": HttpWaitStrategy(8080).for_status_code(200).for_path("/health"),
    }):
        yield compose
```

### 3.5 Cleanup and Resource Management

```python
# testcontainers handles cleanup via context manager (__exit__)
# For additional cleanup (e.g., database state):

@pytest.fixture(scope="session", autouse=True)
def cleanup_volumes(docker_compose):
    """Ensure volumes are removed after all tests."""
    yield
    # DockerCompose.__exit__ runs `docker compose down`
    # For explicit volume removal:
    import subprocess
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "down", "-v"],
        cwd="./super-team",
        capture_output=True,
    )
```

---

## 4. httpx Async Client for Multi-Service Health Polling

### 4.1 Async Health Check Polling Pattern

```python
import httpx
import asyncio
from dataclasses import dataclass

@dataclass
class HealthCheckResult:
    service: str
    healthy: bool
    status_code: int = 0
    response_time_ms: float = 0.0
    error: str = ""

async def check_service_health(
    client: httpx.AsyncClient,
    service_name: str,
    url: str,
    path: str = "/api/health",
) -> HealthCheckResult:
    """Check a single service's health endpoint."""
    import time
    start = time.monotonic()
    try:
        resp = await client.get(f"{url}{path}")
        elapsed = (time.monotonic() - start) * 1000
        return HealthCheckResult(
            service=service_name,
            healthy=resp.status_code == 200,
            status_code=resp.status_code,
            response_time_ms=elapsed,
        )
    except httpx.RequestError as e:
        elapsed = (time.monotonic() - start) * 1000
        return HealthCheckResult(
            service=service_name,
            healthy=False,
            error=str(e),
            response_time_ms=elapsed,
        )
```

### 4.2 Concurrent Health Checks Across Services

```python
async def check_all_services(
    service_urls: dict[str, str],
    timeout: float = 10.0,
) -> list[HealthCheckResult]:
    """Check all services concurrently."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout, connect=5.0),
    ) as client:
        tasks = [
            check_service_health(client, name, url)
            for name, url in service_urls.items()
        ]
        return await asyncio.gather(*tasks)
```

### 4.3 Polling with Timeout and Retry

```python
async def poll_until_healthy(
    service_urls: dict[str, str],
    timeout_seconds: float = 120.0,
    poll_interval: float = 3.0,
    required_consecutive: int = 2,
) -> dict[str, HealthCheckResult]:
    """Poll all services until all are healthy or timeout.

    Args:
        service_urls: Map of service_name -> base_url.
        timeout_seconds: Max time to wait for all services.
        poll_interval: Seconds between poll attempts.
        required_consecutive: Number of consecutive healthy checks required
                              before declaring a service healthy (prevents
                              false positives during startup).

    Returns:
        Final health status for each service.
    """
    import time
    deadline = time.monotonic() + timeout_seconds
    consecutive_healthy: dict[str, int] = {name: 0 for name in service_urls}
    final_results: dict[str, HealthCheckResult] = {}

    while time.monotonic() < deadline:
        results = await check_all_services(service_urls)

        all_healthy = True
        for result in results:
            final_results[result.service] = result
            if result.healthy:
                consecutive_healthy[result.service] += 1
            else:
                consecutive_healthy[result.service] = 0
                all_healthy = False

        # Check if all services have enough consecutive healthy checks
        if all(
            count >= required_consecutive
            for count in consecutive_healthy.values()
        ):
            return final_results

        await asyncio.sleep(poll_interval)

    # Timeout — return last known state
    return final_results
```

### 4.4 Health Aggregation

```python
@dataclass
class HealthAggregation:
    total_services: int
    healthy_services: int
    unhealthy_services: list[str]
    all_healthy: bool
    results: dict[str, HealthCheckResult]

def aggregate_health(results: dict[str, HealthCheckResult]) -> HealthAggregation:
    """Aggregate individual health results into a summary."""
    unhealthy = [
        name for name, result in results.items() if not result.healthy
    ]
    return HealthAggregation(
        total_services=len(results),
        healthy_services=len(results) - len(unhealthy),
        unhealthy_services=unhealthy,
        all_healthy=len(unhealthy) == 0,
        results=results,
    )
```

### 4.5 Integration with pytest

```python
@pytest.fixture(scope="session")
def all_services_healthy(service_urls: dict[str, str]) -> HealthAggregation:
    """Wait for all services to be healthy. Fail session if not."""
    results = asyncio.get_event_loop().run_until_complete(
        poll_until_healthy(service_urls, timeout_seconds=120.0)
    )
    agg = aggregate_health(results)
    if not agg.all_healthy:
        unhealthy_details = "; ".join(
            f"{name}: {results[name].error or f'status {results[name].status_code}'}"
            for name in agg.unhealthy_services
        )
        pytest.fail(
            f"{agg.healthy_services}/{agg.total_services} services healthy. "
            f"Unhealthy: {unhealthy_details}"
        )
    return agg
```

---

## 5. Subprocess Orchestration for Parallel Verification

### 5.1 Running Multiple Builder Instances as Subprocesses

Each Builder runs as a separate `python -m agent_team` process with its own working directory, config, and state.

```python
import asyncio
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class BuilderInvocation:
    service_id: str
    working_dir: Path
    depth: str = "standard"
    config_path: Path | None = None

@dataclass
class BuilderOutput:
    service_id: str
    success: bool
    cost: float = 0.0
    test_passed: int = 0
    test_total: int = 0
    convergence_ratio: float = 0.0
    error: str = ""
    stdout: str = ""
    stderr: str = ""

async def run_single_builder(
    invocation: BuilderInvocation,
    timeout: int = 1800,
) -> BuilderOutput:
    """Run a single builder subprocess."""
    cmd = [
        "python", "-m", "agent_team",
        "--cwd", str(invocation.working_dir),
        "--depth", invocation.depth,
    ]
    if invocation.config_path:
        cmd.extend(["--config", str(invocation.config_path)])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Parse builder state from output directory
        state_path = invocation.working_dir / ".agent-team" / "STATE.json"
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            summary = state.get("summary", {})
            return BuilderOutput(
                service_id=invocation.service_id,
                success=summary.get("success", False),
                cost=state.get("total_cost", 0.0),
                test_passed=summary.get("test_passed", 0),
                test_total=summary.get("test_total", 0),
                convergence_ratio=summary.get("convergence_ratio", 0.0),
                stdout=stdout,
                stderr=stderr,
            )
        else:
            return BuilderOutput(
                service_id=invocation.service_id,
                success=False,
                error=f"STATE.json not found at {state_path}",
                stdout=stdout,
                stderr=stderr,
            )

    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return BuilderOutput(
            service_id=invocation.service_id,
            success=False,
            error=f"Timeout after {timeout}s",
        )
    except Exception as e:
        return BuilderOutput(
            service_id=invocation.service_id,
            success=False,
            error=str(e),
        )
```

### 5.2 Parallel Builder Execution with Semaphore

```python
async def run_parallel_builders(
    invocations: list[BuilderInvocation],
    max_concurrent: int = 3,
    timeout_per_builder: int = 1800,
) -> list[BuilderOutput]:
    """Run multiple builders in parallel, bounded by semaphore."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_run(inv: BuilderInvocation) -> BuilderOutput:
        async with semaphore:
            return await run_single_builder(inv, timeout=timeout_per_builder)

    results = await asyncio.gather(
        *[bounded_run(inv) for inv in invocations],
        return_exceptions=True,
    )

    outputs = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            outputs.append(BuilderOutput(
                service_id=invocations[i].service_id,
                success=False,
                error=str(result),
            ))
        else:
            outputs.append(result)
    return outputs
```

### 5.3 Result Aggregation

```python
@dataclass
class BuildFleetResult:
    total_builders: int
    successful_builders: int
    failed_builders: int
    total_cost: float
    builder_outputs: list[BuilderOutput]
    all_passed: bool

def aggregate_builder_results(outputs: list[BuilderOutput]) -> BuildFleetResult:
    """Aggregate results from parallel builder execution."""
    successful = [o for o in outputs if o.success]
    return BuildFleetResult(
        total_builders=len(outputs),
        successful_builders=len(successful),
        failed_builders=len(outputs) - len(successful),
        total_cost=sum(o.cost for o in outputs),
        builder_outputs=outputs,
        all_passed=len(successful) == len(outputs),
    )
```

### 5.4 Builder Output Capture and Parsing

```python
def parse_builder_state(output_dir: Path) -> dict:
    """Parse a builder's STATE.json to extract verification-relevant data."""
    state_path = output_dir / ".agent-team" / "STATE.json"
    if not state_path.is_file():
        return {"error": "STATE.json not found"}

    state = json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "success": state.get("summary", {}).get("success", False),
        "cost": state.get("total_cost", 0.0),
        "test_passed": state.get("summary", {}).get("test_passed", 0),
        "test_total": state.get("summary", {}).get("test_total", 0),
        "convergence_ratio": state.get("summary", {}).get("convergence_ratio", 0.0),
        "completed_phases": state.get("completed_phases", []),
        "health": state.get("convergence_health", "unknown"),
        "artifacts": list_artifacts(output_dir),
    }

def list_artifacts(output_dir: Path) -> list[str]:
    """List all significant artifacts produced by a builder."""
    patterns = ["**/*.py", "**/*.ts", "**/*.js", "Dockerfile", "docker-compose.yml"]
    artifacts = []
    for pattern in patterns:
        for f in output_dir.glob(pattern):
            if ".agent-team" not in str(f) and "node_modules" not in str(f):
                artifacts.append(str(f.relative_to(output_dir)))
    return artifacts
```

---

## 6. Test Data and Fixture Specifications

### 6.1 Three-Service Sample Application

The test application must be small enough to build quickly but complex enough to exercise all cross-service wiring patterns.

**Architecture:**

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  auth-service    │────▶│  order-service    │────▶│ notification-service │
│  (Python/FastAPI)│     │  (Python/FastAPI) │     │   (Python/FastAPI)   │
│                  │     │                   │     │                      │
│ POST /register   │     │ POST /orders      │     │ POST /notify         │
│ POST /login      │     │ GET  /orders/:id  │     │ GET  /notifications  │
│ GET  /users/me   │     │ PUT  /orders/:id  │     │                      │
│                  │     │ GET  /health      │     │ GET  /health         │
│ GET  /health     │     │                   │     │                      │
└─────────────────┘     └──────────────────┘     └──────────────────────┘
        │                       │                          ▲
        │    JWT validation     │    OrderCreated event    │
        └───────────────────────┘──────────────────────────┘
```

**Entities:**

| Entity | Service | Fields |
|---|---|---|
| User | auth-service | id (UUID), email (string), password_hash (string), created_at (datetime) |
| Order | order-service | id (UUID), user_id (UUID), status (enum: pending/confirmed/shipped/delivered), items (list), total (decimal), created_at (datetime) |
| Notification | notification-service | id (UUID), user_id (UUID), type (enum: email/sms), message (string), sent_at (datetime) |

**Contracts:**

| Contract | Type | Provider | Consumer |
|---|---|---|---|
| auth-api | OpenAPI 3.1 | auth-service | order-service |
| order-api | OpenAPI 3.1 | order-service | notification-service |
| order-events | AsyncAPI 3.0 | order-service | notification-service |

**State Machine (Order):**

```
pending ──(confirm)──▶ confirmed ──(ship)──▶ shipped ──(deliver)──▶ delivered
    │                      │                     │
    └────(cancel)──────────┴─────(cancel)────────┘──▶ cancelled
```

### 6.2 Mock PRD Structure

File: `tests/fixtures/sample_prd.md`

```markdown
# TaskTracker — 3-Service Test Application

## Overview
A minimal task/order tracking system with authentication, order management,
and notification delivery. Designed as a verification target for the
Super Agent Team pipeline.

## Services

### Auth Service
- User registration with email + password
- JWT-based login (access + refresh tokens)
- Token validation endpoint for other services
- Technology: Python, FastAPI, PostgreSQL

### Order Service
- CRUD operations on orders
- Order state machine: pending -> confirmed -> shipped -> delivered
- Validates JWT tokens via auth-service
- Publishes OrderCreated and OrderShipped events
- Technology: Python, FastAPI, PostgreSQL

### Notification Service
- Consumes OrderCreated and OrderShipped events
- Sends email/SMS notifications (mock provider)
- Notification history retrieval
- Technology: Python, FastAPI, PostgreSQL

## Cross-Service Contracts
- Auth Service provides JWT validation API consumed by Order Service
- Order Service provides Order query API consumed by Notification Service
- Order Service publishes events consumed by Notification Service

## Non-Functional Requirements
- All services expose /health endpoint
- All HTTP calls include traceparent header
- All services use structured JSON logging
- No hardcoded secrets
```

### 6.3 Expected Contract Artifacts

File: `tests/fixtures/sample_openapi_auth.yaml`

```yaml
openapi: "3.1.0"
info:
  title: Auth Service API
  version: "1.0.0"
paths:
  /register:
    post:
      operationId: registerUser
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: { type: string, format: email }
                password: { type: string, minLength: 8 }
              required: [email, password]
      responses:
        "201":
          description: User created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
  /login:
    post:
      operationId: loginUser
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: { type: string }
                password: { type: string }
              required: [email, password]
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token: { type: string }
                  refresh_token: { type: string }
                  token_type: { type: string }
  /users/me:
    get:
      operationId: getCurrentUser
      security:
        - bearerAuth: []
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
components:
  schemas:
    User:
      type: object
      properties:
        id: { type: string, format: uuid }
        email: { type: string, format: email }
        created_at: { type: string, format: date-time }
      required: [id, email, created_at]
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### 6.4 Expected Build Artifacts (per service)

After a Builder completes, each service directory should contain:

```
{service_dir}/
  src/
    main.py          # FastAPI app entry point
    routes/           # API route handlers
    models/           # Pydantic models
    services/         # Business logic
    config.py         # Configuration
  tests/
    test_*.py         # Unit + integration tests
  Dockerfile          # Container build
  requirements.txt    # Dependencies
  .agent-team/
    STATE.json        # Builder state (cost, tests, convergence)
    REQUIREMENTS.md   # Completed requirements
```

---

## 7. Verification Matrix Design

### 7.1 Success Criteria to Test Assertion Mapping

This matrix maps every Run 4 success criterion to specific test assertions.

| ID | Success Criterion | Test Function | Assertion | Phase |
|---|---|---|---|---|
| SC-01 | Complete pipeline runs end-to-end without human intervention | `test_full_pipeline_no_intervention` | `pipeline_result.completed is True` | 7 |
| SC-02 | 3-service test app deploys | `test_app_deployment` | All 3 services in docker compose ps | 6 |
| SC-03 | All health checks pass | `test_health_checks` | `health_agg.all_healthy is True` | 6 |
| SC-04 | Integration tests pass | `test_integration_tests` | `integration_report.overall_health != "failed"` | 6 |
| SC-05 | Contract violations detected and reported | `test_contract_violation_detection` | Planted violations appear in report | 6-7 |
| SC-06 | Codebase Intelligence indexes generated code | `test_codebase_indexing` | `index_stats.total_symbols > 0` | 5 |
| SC-07 | CI responds to MCP queries | `test_mcp_queries` | `find_definition("User")` returns result | 5 |
| SC-08 | Total time under 6 hours for 3-service app | `test_pipeline_duration` | `total_duration < 21600` | 7 |

### 7.2 Build 1 Success Criteria Verification

| ID | Build 1 Criterion | Test | Expected |
|---|---|---|---|
| B1-01 | All 3 services deploy in Docker Compose | `test_build1_deploy` | `compose.get_service_port()` returns for all 3 |
| B1-02 | Health checks pass | `test_build1_health` | HTTP 200 on /api/health for all 3 |
| B1-03 | Architect produces valid ServiceMap | `test_architect_decompose` | ServiceMap with >= 1 service |
| B1-04 | Contract Engine validates schemas | `test_contract_validation` | `validate_spec()` returns `{valid: true}` |
| B1-05 | Contract Engine generates test suites | `test_contract_test_gen` | Non-empty test code string |
| B1-06 | Codebase Intelligence indexes 50K+ LOC | `test_codebase_indexing_perf` | Duration < 60s for 50K LOC |
| B1-07 | All MCP tools respond | `test_mcp_tool_responses` | 16 tools return non-error |
| B1-08 | Dead code detection works | `test_dead_code_detection` | Planted dead code found |

### 7.3 Build 2 Success Criteria Verification

| ID | Build 2 Criterion | Test | Expected |
|---|---|---|---|
| B2-01 | Builder uses Agent Teams | `test_agent_teams_mode` | `team_state.mode == "agent_teams"` |
| B2-02 | Builder queries Contract Engine MCP | `test_contract_mcp_calls` | MCP call log contains get_contract |
| B2-03 | Builder queries Codebase Intelligence MCP | `test_codebase_mcp_calls` | MCP call log contains find_definition |
| B2-04 | CONTRACT scans detect violations | `test_contract_scan_detection` | Planted violation found by scan |
| B2-05 | Two Builders run in parallel | `test_parallel_builders` | Both complete, no conflicts |
| B2-06 | Generated code registers with index | `test_artifact_registration` | `register_artifact()` returns indexed=True |

### 7.4 Build 3 Success Criteria Verification

| ID | Build 3 Criterion | Test | Expected |
|---|---|---|---|
| B3-01 | Complete pipeline runs end-to-end | `test_pipeline_e2e` | All phases complete |
| B3-02 | 3-service app deploys and passes health | `test_deploy_and_health` | 3/3 healthy |
| B3-03 | Contract violations detected | `test_schemathesis_violations` | SCHEMA-001/002 detected |
| B3-04 | Quality Gate layers sequential | `test_gate_layer_order` | L1 before L2 before L3 before L4 |
| B3-05 | CLI works for all commands | `test_cli_commands` | All 8 commands registered |

### 7.5 Coverage Tracking

```python
VERIFICATION_MATRIX = {
    # Run 4 success criteria
    "SC-01": {"tests": ["test_full_pipeline_no_intervention"], "covered": False},
    "SC-02": {"tests": ["test_app_deployment"], "covered": False},
    "SC-03": {"tests": ["test_health_checks"], "covered": False},
    "SC-04": {"tests": ["test_integration_tests"], "covered": False},
    "SC-05": {"tests": ["test_contract_violation_detection"], "covered": False},
    "SC-06": {"tests": ["test_codebase_indexing"], "covered": False},
    "SC-07": {"tests": ["test_mcp_queries"], "covered": False},
    "SC-08": {"tests": ["test_pipeline_duration"], "covered": False},
    # Build 1 criteria
    "B1-01": {"tests": ["test_build1_deploy"], "covered": False},
    "B1-02": {"tests": ["test_build1_health"], "covered": False},
    "B1-03": {"tests": ["test_architect_decompose"], "covered": False},
    "B1-04": {"tests": ["test_contract_validation"], "covered": False},
    "B1-05": {"tests": ["test_contract_test_gen"], "covered": False},
    "B1-06": {"tests": ["test_codebase_indexing_perf"], "covered": False},
    "B1-07": {"tests": ["test_mcp_tool_responses"], "covered": False},
    "B1-08": {"tests": ["test_dead_code_detection"], "covered": False},
    # Build 2 criteria
    "B2-01": {"tests": ["test_agent_teams_mode"], "covered": False},
    "B2-02": {"tests": ["test_contract_mcp_calls"], "covered": False},
    "B2-03": {"tests": ["test_codebase_mcp_calls"], "covered": False},
    "B2-04": {"tests": ["test_contract_scan_detection"], "covered": False},
    "B2-05": {"tests": ["test_parallel_builders"], "covered": False},
    "B2-06": {"tests": ["test_artifact_registration"], "covered": False},
    # Build 3 criteria
    "B3-01": {"tests": ["test_pipeline_e2e"], "covered": False},
    "B3-02": {"tests": ["test_deploy_and_health"], "covered": False},
    "B3-03": {"tests": ["test_schemathesis_violations"], "covered": False},
    "B3-04": {"tests": ["test_gate_layer_order"], "covered": False},
    "B3-05": {"tests": ["test_cli_commands"], "covered": False},
}

def check_coverage(test_results: dict[str, bool]) -> dict:
    """Check which success criteria are covered by passing tests."""
    covered = 0
    total = len(VERIFICATION_MATRIX)
    uncovered = []

    for criterion_id, spec in VERIFICATION_MATRIX.items():
        tests_pass = all(
            test_results.get(t, False) for t in spec["tests"]
        )
        spec["covered"] = tests_pass
        if tests_pass:
            covered += 1
        else:
            uncovered.append(criterion_id)

    return {
        "total_criteria": total,
        "covered": covered,
        "uncovered": uncovered,
        "coverage_pct": (covered / total * 100) if total > 0 else 0,
    }
```

### 7.6 Regression Detection Between Fix Passes

```python
@dataclass
class FixPassSnapshot:
    pass_number: int
    violations: dict[str, list[str]]  # {scan_code: [file_paths]}
    test_results: dict[str, bool]     # {test_name: passed}
    timestamp: str

def detect_regressions(
    before: FixPassSnapshot,
    after: FixPassSnapshot,
) -> list[str]:
    """Detect violations that were fixed but reappeared."""
    regressions = []
    for code, files_before in before.violations.items():
        files_after = set(after.violations.get(code, []))
        fixed_files = set(files_before) - files_after
        # Check if any previously-passing tests now fail
        for test_name, passed_before in before.test_results.items():
            passed_after = after.test_results.get(test_name, False)
            if passed_before and not passed_after:
                regressions.append(
                    f"REGRESSION: {test_name} passed in fix pass "
                    f"#{before.pass_number} but failed in #{after.pass_number}"
                )
    return regressions
```

---

## 8. Recommendations

### 8.1 Test Infrastructure for Run 4

| Decision | Recommendation | Rationale |
|---|---|---|
| **Test runner** | pytest 8.x + pytest-asyncio 0.24.x | Matches Build 3 stack; `asyncio_mode = "auto"` simplifies async tests |
| **Docker management** | testcontainers[compose] 4.x | Handles startup, readiness, port mapping, cleanup from within pytest |
| **HTTP client** | httpx 0.28.x (AsyncClient) | Async-native, timeout configuration, connection pooling |
| **Compose files** | Two: `docker-compose.yml` (Build 1) + `docker-compose.test.yml` (generated services) | Separates infrastructure from test targets |
| **Test marks** | `@pytest.mark.build1`, `@pytest.mark.full_pipeline`, etc. | Enables partial pipeline testing during development |
| **State checkpointing** | JSON checkpoint in `.run4-verification/` | Enables resume after failure without re-running passed phases |

### 8.2 Test Organization

```
tests/
  run4/
    conftest.py                    # All fixtures (compose, clients, data)
    test_phase1_build1_health.py   # Build 1 service health
    test_phase2_mcp_smoke.py       # MCP tool smoke tests
    test_phase3_architect.py       # Architect decomposition
    test_phase4_contracts.py       # Contract registration
    test_phase5_builders.py        # Parallel builder execution
    test_phase6_integration.py     # Integration + deployment
    test_phase7_quality_gate.py    # Quality gate + fix pass
    test_regression.py             # Regression detection across fix passes
    fixtures/
      sample_prd.md                # 3-service test PRD
      sample_openapi_auth.yaml     # Auth service OpenAPI spec
      sample_openapi_order.yaml    # Order service OpenAPI spec
      sample_asyncapi_order.yaml   # Order events AsyncAPI spec
      sample_pact.json             # Pact contract
      sample_docker_compose.yml    # Test compose file
```

### 8.3 Timing Expectations

| Phase | Expected Duration | Timeout |
|---|---|---|
| Build 1 health + MCP smoke | 2-5 min | 10 min |
| Architect decomposition | 5-15 min | 30 min |
| Contract registration | 1-3 min | 10 min |
| Parallel builders (3) | 2-4 hours | 6 hours |
| Integration + deployment | 10-30 min | 60 min |
| Quality gate | 10-20 min | 60 min |
| Fix pass (if needed) | 30-90 min | 2 hours |
| **Total** | **3-6 hours** | **10 hours** |

### 8.4 Key Design Decisions

1. **Session-scoped Docker Compose**: Build 1 services start once and stay up for all tests. This avoids the 30-60s startup cost per test module.

2. **Two-level health checking**: Testcontainers `HttpWaitStrategy` for initial startup, then httpx `poll_until_healthy` for runtime verification between phases. The two-level approach catches both startup failures and mid-run crashes.

3. **Semaphore-bounded builder parallelism**: `asyncio.Semaphore(max_concurrent=3)` prevents resource exhaustion. The semaphore is created inside the function body (not at module level) to avoid event loop binding issues.

4. **Checkpoint-resume pattern**: JSON state file in `.run4-verification/` enables resuming after builder failures without re-running the Architect phase. This saves significant time and cost during iterative fix passes.

5. **Planted violations for testing**: Test fixtures should include deliberate violations (SEC-001 unauthenticated endpoint, LOG-001 print statement, SCHEMA-001 wrong response type) to verify that the Quality Gate detects them. This is the "test the tests" pattern.

6. **Regression detection between fix passes**: Compare violation snapshots before and after each fix pass. If a previously-fixed violation reappears, flag it as a regression. This catches fix loops that break other things.

### 8.5 Risk Mitigations

| Risk | Mitigation |
|---|---|
| Docker Compose startup timeout | Use `with_startup_timeout(90)` for Codebase Intelligence (ChromaDB init is slow) |
| Builder subprocess hangs | `asyncio.wait_for()` with timeout + `proc.kill()` in `finally` block |
| Port conflicts | Testcontainers uses dynamic port mapping — never hardcode host ports |
| Flaky health checks | Require 2 consecutive healthy checks before declaring ready |
| MCP server startup race | Wait for health endpoint first, then verify MCP tools |
| Large test output | Cap violation lists at 200 per category (already in Build 3 TECH-021) |
| Windows compatibility | Use `pathlib.Path` everywhere; `signal.signal()` instead of `loop.add_signal_handler()` |
