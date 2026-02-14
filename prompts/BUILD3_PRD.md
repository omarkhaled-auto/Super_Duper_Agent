# Super Agent Team — Build 3 PRD: Integrator + Quality Gate + Super Orchestrator

Build 3 is the final build of the Super Agent Team platform. It wires all five systems together: the Architect (Build 1), the Contract Engine (Build 1), Codebase Intelligence (Build 1), the Builder Fleet (Build 2), and the new Integrator + Quality Gate + Super Orchestrator (this build). Build 3 produces a CLI-driven pipeline that takes a PRD as input, orchestrates the Architect for decomposition, dispatches parallel Builders via the Agent Teams abstraction, deploys all services via Docker Compose with Traefik API gateway, runs 4-layer quality verification (per-service, contract compliance, system-level security/observability, adversarial review), and iterates fix passes until all gates pass. No frontend, no UI — pure backend infrastructure + CLI.

Each requirement includes `(review_cycles: N)` — this is tracked by the build system. Agents must preserve this suffix when modifying requirements.

## Technology Stack

- **Language:** Python 3.12+
- **Async Runtime:** asyncio (stdlib) + MCP Python SDK (anyio-compatible)
- **State Machine:** transitions 0.9.2+ (AsyncMachine with guard conditions, queued transitions)
- **CLI Framework:** typer[all] 0.21.0+ (type-safe CLI with Rich integration)
- **Terminal UI:** rich 13.0+ (progress bars, tables, panels, live display)
- **HTTP Framework:** FastAPI 0.129.0+ (health/status endpoints)
- **ASGI Server:** uvicorn 0.34.0+
- **Property-Based API Testing:** schemathesis 4.x (OpenAPI fuzz testing)
- **Consumer-Driven Contracts:** pact-python 3.2.1+ (Pact V4 spec, Rust FFI)
- **Docker Test Integration:** testcontainers[compose] 4.x (DockerCompose with wait strategies)
- **Async HTTP Client:** httpx 0.28.x+ (AsyncClient for cross-service requests)
- **Test Framework:** pytest 8.x+ with pytest-asyncio 0.24.x+ (asyncio_mode = "auto")
- **Secret Scanning:** detect-secrets 1.5+ (Python API with transient_settings)
- **JWT Verification:** PyJWT 2.8+ (algorithm enforcement, claim validation)
- **Trace Context:** opentelemetry-api 1.25+ / opentelemetry-sdk 1.25+ (W3C traceparent)
- **API Gateway:** Traefik v3.6 (Docker provider auto-discovery)
- **Service Orchestration:** Docker Compose v2 (depends_on with service_healthy)
- **Configuration:** PyYAML 6.x+, pydantic 2.x+
- **Docker SDK:** docker-py 7.x+
- **MCP SDK:** mcp>=1.25,<2 (Claude Code native protocol, stdio transport)

## Project Structure

```
super-team/
  src/
    super_orchestrator/
      __init__.py
      cli.py
      state_machine.py
      pipeline.py
      state.py
      cost.py
      display.py
      config.py
      exceptions.py
      shutdown.py

    integrator/
      __init__.py
      docker_orchestrator.py
      traefik_config.py
      service_discovery.py
      compose_generator.py
      cross_service_test_generator.py
      cross_service_test_runner.py
      data_flow_tracer.py
      boundary_tester.py
      contract_compliance.py
      pact_manager.py
      schemathesis_runner.py
      fix_loop.py
      report.py

    quality_gate/
      __init__.py
      gate_engine.py
      layer1_per_service.py
      layer2_contract_compliance.py
      layer3_system_level.py
      layer4_adversarial.py
      security_scanner.py
      observability_checker.py
      docker_security.py
      adversarial_patterns.py
      scan_aggregator.py
      report.py

    build3_shared/
      __init__.py
      models.py
      protocols.py
      constants.py
      utils.py

  tests/
    conftest.py
    test_state_machine.py
    test_cli.py
    test_pipeline.py
    test_docker_orchestrator.py
    test_contract_compliance.py
    test_cross_service.py
    test_quality_gate.py
    test_security_scanner.py
    test_observability.py
    test_adversarial.py
    test_docker_security.py
    test_state_persistence.py
    test_cost_tracking.py
    test_config.py
    test_integration_e2e.py
    test_traefik_config.py
    test_service_discovery.py
    test_compose_generator.py
    test_scan_aggregator.py
    test_display.py
    test_fix_loop.py
    test_reports.py
    fixtures/
      sample_openapi.yaml
      sample_pact.json
      sample_docker_compose.yml
      sample_prd.md

  docker/
    docker-compose.yml
    docker-compose.test.yml
    traefik/
      traefik.yml
      dynamic/

  pyproject.toml
  config.yaml
```

---

## Milestone 1: Shared Models, Config, and State Machine Engine

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Create all shared data models (ServiceInfo, BuilderResult, ContractViolation, ScanViolation, LayerResult, QualityGateReport, IntegrationReport), protocol classes, constants (scan codes, phase names, timeouts), utility functions, SuperOrchestratorConfig with nested dataclasses, PipelineState persistence with atomic JSON write, PipelineCostTracker, the AsyncMachine-based state machine with 11 states and 13 transitions, Docker infrastructure modules (ComposeGenerator, DockerOrchestrator, TraefikConfigGenerator, ServiceDiscovery), GracefulShutdown signal handler, and custom exception classes. This milestone is the foundation that all subsequent milestones depend on.

### Functional Requirements

- [ ] REQ-001: Create `src/build3_shared/models.py` with the following enums: `ServiceStatus` (str, Enum) with values (pending, building, built, deploying, healthy, unhealthy, failed), `QualityLevel` (str, Enum) with values (layer1_service, layer2_contract, layer3_system, layer4_adversarial), `GateVerdict` (str, Enum) with values (passed, failed, partial, skipped) (review_cycles: 0)

- [ ] REQ-002: In `src/build3_shared/models.py`, create the following dataclasses: `ServiceInfo` (service_id: str, domain: str, stack: dict[str, str], estimated_loc: int = 0, docker_image: str = "", health_endpoint: str = "/health", port: int = 8080, status: ServiceStatus = ServiceStatus.PENDING, build_cost: float = 0.0, build_dir: str = ""), `BuilderResult` (system_id: str, service_id: str, success: bool = False, cost: float = 0.0, error: str = "", output_dir: str = "", test_passed: int = 0, test_total: int = 0, convergence_ratio: float = 0.0, artifacts: list[str] = field(default_factory=list)) (review_cycles: 0)

- [ ] REQ-003: In `src/build3_shared/models.py`, create: `ContractViolation` (code: str, severity: str, service: str, endpoint: str, message: str, expected: str = "", actual: str = "", file_path: str = ""), `ScanViolation` (code: str, severity: str, category: str, file_path: str = "", line: int = 0, service: str = "", message: str = "") (review_cycles: 0)

- [ ] REQ-004: In `src/build3_shared/models.py`, create: `LayerResult` (layer: QualityLevel, verdict: GateVerdict = GateVerdict.SKIPPED, violations: list[ScanViolation] = field(default_factory=list), contract_violations: list[ContractViolation] = field(default_factory=list), total_checks: int = 0, passed_checks: int = 0, duration_seconds: float = 0.0), `QualityGateReport` (layers: dict[str, LayerResult] = field(default_factory=dict), overall_verdict: GateVerdict = GateVerdict.SKIPPED, fix_attempts: int = 0, max_fix_attempts: int = 3, total_violations: int = 0, blocking_violations: int = 0), `IntegrationReport` (services_deployed: int = 0, services_healthy: int = 0, contract_tests_total: int = 0, contract_tests_passed: int = 0, integration_tests_total: int = 0, integration_tests_passed: int = 0, data_flow_tests_total: int = 0, data_flow_tests_passed: int = 0, boundary_tests_total: int = 0, boundary_tests_passed: int = 0, violations: list[ContractViolation] = field(default_factory=list), overall_health: str = "unknown") (review_cycles: 0)

- [ ] REQ-005: Create `src/build3_shared/protocols.py` with `@runtime_checkable` Protocol classes: `PhaseExecutor` (async execute(context) -> float, async can_execute(context) -> bool), `QualityScanner` (scan(project_root: Path) -> list[ScanViolation], property scan_codes -> list[str]) (review_cycles: 0)

- [ ] REQ-006: Create `src/build3_shared/constants.py` with phase name constants (PHASE_ARCHITECT through PHASE_FAILED mapping to state machine state names), PHASE_TIMEOUTS dict (architect: 900s, architect_review: 300s, contracts: 180s, builders: 3600s, integration: 600s, quality_gate: 600s, fix_pass: 900s), all 40 quality gate scan codes organized by category (SECURITY_SCAN_CODES SEC-001..006, CORS_SCAN_CODES CORS-001..003, LOGGING_SCAN_CODES LOG-001/004/005, TRACE_SCAN_CODES TRACE-001, SECRET_SCAN_CODES SEC-SECRET-001..012, DOCKER_SCAN_CODES DOCKER-001..008, ADVERSARIAL_SCAN_CODES ADV-001..006, HEALTH_SCAN_CODES HEALTH-001), ALL_SCAN_CODES aggregate list with len == 40, DEFAULT_MAX_CONCURRENT_BUILDERS = 3, DEFAULT_BUILDER_TIMEOUT = 1800, STATE_DIR = ".super-orchestrator", STATE_FILE = "PIPELINE_STATE.json" (review_cycles: 0)

- [ ] REQ-007: Create `src/build3_shared/utils.py` with `atomic_write_json(path: Path, data: dict) -> None` that writes to a .tmp file then renames for crash safety, `load_json(path: Path) -> dict | None` that returns None if file missing or invalid, `ensure_dir(path: Path) -> Path` that creates directory and returns it (review_cycles: 0)

- [ ] REQ-008: Create `src/super_orchestrator/config.py` with nested dataclasses: `ArchitectConfig` (max_retries: int = 2, timeout: int = 900, auto_approve: bool = False), `BuilderConfig` (max_concurrent: int = 3, timeout_per_builder: int = 1800, depth: str = "thorough"), `IntegrationConfig` (timeout: int = 600, traefik_image: str = "traefik:v3.6", compose_file: str = "docker-compose.yml", test_compose_file: str = "docker-compose.test.yml"), `QualityGateConfig` (max_fix_retries: int = 3, layer3_scanners: list[str] = ["security", "cors", "logging", "trace", "secrets", "docker", "health"], layer4_enabled: bool = True, blocking_severity: str = "error"), `SuperOrchestratorConfig` (architect: ArchitectConfig, builder: BuilderConfig, integration: IntegrationConfig, quality_gate: QualityGateConfig, budget_limit: float | None = None, depth: str = "standard", phase_timeouts: dict[str, int] = field(default_factory=dict), build1_services_dir: str = "", agent_team_config_path: str = ""). Include `load_super_config(path: Path) -> SuperOrchestratorConfig` that loads from YAML with defaults for missing keys (review_cycles: 0)

- [ ] REQ-009: Create `src/super_orchestrator/state.py` with `PipelineState` dataclass containing all persistence fields: pipeline_id, prd_path, config_path, depth, current_state, previous_state, completed_phases list, phase_artifacts dict, architect_retries, max_architect_retries = 2, service_map_path, contract_registry_path, domain_model_path, builder_statuses dict, builder_costs dict, builder_results list[dict], total_builders, successful_builders, services_deployed list, integration_report_path, quality_attempts, max_quality_retries = 3, last_quality_results dict, quality_report_path, total_cost, phase_costs dict, budget_limit float | None, started_at, updated_at, interrupted bool, interrupt_reason, schema_version = 1. Methods: `save(directory)` using atomic_write_json, `load(directory)` class method returning PipelineState | None, `clear(directory)` class method (review_cycles: 0)

- [ ] REQ-010: Create `src/super_orchestrator/cost.py` with `PhaseCost` dataclass (phase_name, cost_usd = 0.0, start_time = "", end_time = "", sub_phases: dict[str, float] = field(default_factory=dict)) and `PipelineCostTracker` dataclass (phases: dict[str, PhaseCost], budget_limit: float | None = None) with properties/methods: total_cost property, add_phase_cost(phase, cost), check_budget() -> tuple[bool, str] returning (True, "") if within budget or no limit, (False, message) if exceeded, to_dict() for persistence (review_cycles: 0)

- [ ] REQ-011: Create `src/super_orchestrator/state_machine.py` with STATES list defining 11 State objects (init, architect_running, architect_review, contracts_registering, builders_running, builders_complete, integrating, quality_gate, fix_pass, complete, failed) with on_enter callbacks for logging and display updates, and TRANSITIONS list defining 13 transition dicts with triggers, sources, destinations, guard conditions, and callbacks as specified in the architecture plan. Create `create_pipeline_machine(model, initial_state="init") -> AsyncMachine` factory function using `transitions.extensions.asyncio.AsyncMachine` with `model=model`, `states=STATES`, `transitions=TRANSITIONS`, `initial=initial_state`, `auto_transitions=False`, `send_event=True`, `queued=True`. The factory MUST pass `model=model` — omitting it causes the machine itself to become the model, breaking state persistence. The `fail` transition (#11) must use `source=["init", "architect_running", "architect_review", "contracts_registering", "builders_running", "builders_complete", "integrating", "quality_gate", "fix_pass"]` (explicit list excluding `complete` and `failed`) instead of `source="*"` wildcard to prevent `complete -> failed` corruption of final state. Include RESUME_TRIGGERS dict mapping each state to its resume trigger (review_cycles: 0)

- [ ] REQ-012: Create `src/super_orchestrator/exceptions.py` with custom exception classes: `PipelineError` (base), `PhaseTimeoutError(PipelineError)` with phase_name attribute, `BudgetExceededError(PipelineError)` with total_cost and budget_limit attributes, `ConfigurationError(PipelineError)`, `BuilderFailureError(PipelineError)` with service_id attribute, `IntegrationFailureError(PipelineError)`, `QualityGateFailureError(PipelineError)` with layer attribute (review_cycles: 0)

- [ ] REQ-013: Create `src/super_orchestrator/shutdown.py` with `GracefulShutdown` class: `__init__()` initializing _should_stop = False and _state reference, `install()` registering SIGINT and SIGTERM handlers (using signal.signal on Windows, loop.add_signal_handler on Unix with try/except fallback to signal.signal), `_handle_signal(signum, frame)` guarding against reentrancy with `if self._should_stop: return` (second SIGINT during save would corrupt state), then setting `_should_stop = True` and calling `_emergency_save()`, `_emergency_save()` saving PipelineState if reference exists, `should_stop` property returning bool, `set_state(state: PipelineState) -> None` for deferred state injection (review_cycles: 0)

- [ ] REQ-014: Create `src/build3_shared/__init__.py`, `src/super_orchestrator/__init__.py`, `src/integrator/__init__.py`, `src/quality_gate/__init__.py` with `__version__ = "3.0.0"` (review_cycles: 0)

- [ ] REQ-015: Create `src/integrator/compose_generator.py` with `ComposeGenerator` class: `__init__(self, config: SuperOrchestratorConfig)`, `generate(self, service_map: dict, builder_results: list[BuilderResult]) -> str` producing a valid docker-compose.yml string with: Traefik API gateway service (image traefik:v3.6, ports 80 and 8080, Docker provider auto-discovery, command includes `--ping=true` to enable the ping endpoint, health check using `traefik healthcheck --ping` — NOTE: `--ping=true` is a prerequisite for the healthcheck command to work), PostgreSQL service (image postgres:16-alpine, healthcheck using pg_isready, named volume), Redis service (image redis:7-alpine, healthcheck using redis-cli ping), one service entry per successfully built service (with `build: {context: builder_result.output_dir}` assuming builder has created a Dockerfile, healthcheck, Traefik labels for routing via TraefikConfigGenerator, depends_on postgres with service_healthy), frontend/backend network separation, named volumes. If no Dockerfile exists in builder output_dir, generate a default Python Dockerfile based on ServiceInfo.stack (review_cycles: 0)

- [ ] REQ-016: Create `src/integrator/traefik_config.py` with `TraefikConfigGenerator` class: `generate_labels(self, service_name: str, port: int, path_prefix: str) -> dict[str, str]` producing Traefik Docker labels for automatic routing: `traefik.enable=true`, `traefik.http.routers.{service}.rule=PathPrefix(\`{path_prefix}\`)`, `traefik.http.services.{service}.loadbalancer.server.port={port}`, strip prefix middleware labels `traefik.http.middlewares.{service}-strip.stripprefix.prefixes={path_prefix}` and `traefik.http.routers.{service}.middlewares={service}-strip`, `generate_static_config(self) -> str` producing traefik.yml with providers.docker (exposedByDefault: false) and entrypoints.web (address: ":80") (review_cycles: 0)

- [ ] REQ-017: Create `src/integrator/docker_orchestrator.py` with `DockerOrchestrator` class: `__init__(self, compose_file: Path, project_name: str = "super-team")`, `async start_services(self) -> dict[str, ServiceInfo]` running `docker compose -p {project_name} -f {compose_file} up -d` via asyncio.create_subprocess_exec, `async stop_services(self) -> None` running `docker compose -p {project_name} -f {compose_file} down`, `async wait_for_healthy(self, services: list[str], timeout: int = 120) -> dict[str, bool]` polling `docker compose ps --format json` every 5s (using `await asyncio.sleep(5)`, NOT `time.sleep(5)`) until all services healthy or timeout, `async get_service_url(self, service_name: str, port: int) -> str` returning `http://localhost:{mapped_port}` from `docker compose port {service} {port}` output, `async get_service_logs(self, service_name: str, tail: int = 100) -> str`, `async restart_service(self, service_name: str) -> None`, `async is_service_healthy(self, service_name: str) -> bool` (review_cycles: 0)

- [ ] REQ-018: Create `src/integrator/service_discovery.py` with `ServiceDiscovery` class: `__init__(self, compose_file: Path)`, `get_service_ports(self) -> dict[str, int]` parsing compose YAML for port mappings, `async check_health(self, service_name: str, url: str) -> bool` sending GET to health endpoint with httpx.AsyncClient(timeout=5.0), `async wait_all_healthy(self, services: dict[str, str], timeout: int = 120) -> dict[str, bool]` polling all services every 3s (using `await asyncio.sleep(3)`, NOT `time.sleep(3)`) until healthy or timeout (review_cycles: 0)

### Technical Requirements

- [ ] TECH-001: All file paths must use pathlib.Path, never string concatenation (review_cycles: 0)
- [ ] TECH-002: All file I/O must specify encoding="utf-8" explicitly (review_cycles: 0)
- [ ] TECH-003: All enums must use `class Name(str, Enum)` pattern for JSON serialization compatibility (review_cycles: 0)
- [ ] TECH-004: PipelineState.save() must use atomic_write_json (write .tmp then rename) to prevent corruption on crash (review_cycles: 0)
- [ ] TECH-005: AsyncMachine must be imported from `transitions.extensions.asyncio` — the `transitions.Machine` base class does NOT support async callbacks (review_cycles: 0)
- [ ] TECH-006: Signal handlers on Windows must use `signal.signal()` — `loop.add_signal_handler()` is not supported on Windows. Use try/except RuntimeError to handle both platforms (review_cycles: 0)
- [ ] TECH-007: All dataclass fields with mutable defaults must use `field(default_factory=...)` (review_cycles: 0)
- [ ] TECH-008: Docker Compose commands must use `docker compose` (v2 syntax, no hyphen) not `docker-compose` (v1 deprecated) (review_cycles: 0)
- [ ] TECH-009: Docker Compose subprocess calls must capture stdout and stderr separately and log both on failure (review_cycles: 0)
- [ ] TECH-010: Traefik labels must use backtick syntax for PathPrefix rules: `PathPrefix(\`/api/service\`)` — this is Traefik v3 syntax. In Python, use string concatenation or raw strings to produce backtick characters (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-001: `src/build3_shared/models.py` must be importable by all three packages (super_orchestrator, integrator, quality_gate) (review_cycles: 0)
- [ ] WIRE-002: `src/super_orchestrator/state_machine.py` must import State from transitions and STATES/TRANSITIONS must be module-level constants for testability (review_cycles: 0)
- [ ] WIRE-003: `src/super_orchestrator/state.py` must import atomic_write_json from build3_shared.utils (review_cycles: 0)
- [ ] WIRE-004: `src/super_orchestrator/shutdown.py` must accept a PipelineState reference via set_state(state) method, not constructor injection, because state is created after shutdown handler is installed (review_cycles: 0)
- [ ] WIRE-005: `ComposeGenerator` must call `TraefikConfigGenerator.generate_labels()` for each service entry in the generated docker-compose.yml (review_cycles: 0)
- [ ] WIRE-006: `DockerOrchestrator.wait_for_healthy()` should delegate to `ServiceDiscovery.wait_all_healthy()` or compose `ServiceDiscovery` for health checking and port mapping (review_cycles: 0)

### Test Requirements

- [ ] TEST-001: `tests/test_state_machine.py` — test all 13 transitions fire correctly with mocked guard conditions returning True, test guard conditions that return False prevent transitions, test wildcard `fail` trigger works from every non-terminal state, test `fail` trigger is ignored from `complete` and `failed` states (ignore_invalid_triggers), test resume triggers map to correct states — minimum 20 test cases (review_cycles: 0)
- [ ] TEST-002: `tests/test_state_persistence.py` — test PipelineState.save() creates JSON file in .super-orchestrator/, test PipelineState.load() reconstructs identical state, test PipelineState.clear() removes directory, test atomic write survives simulated crash (write .tmp exists but rename not called), test load returns None for missing directory — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-003: `tests/test_cost_tracking.py` — test PipelineCostTracker.add_phase_cost accumulates correctly, test total_cost property sums all phases, test check_budget returns (True, "") when no limit, test check_budget returns (False, message) when exceeded, test to_dict roundtrips — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-004: `tests/test_config.py` — test SuperOrchestratorConfig defaults, test load_super_config from YAML file with all sections, test load_super_config with missing sections uses defaults, test ArchitectConfig/BuilderConfig/IntegrationConfig/QualityGateConfig field defaults — minimum 12 test cases (review_cycles: 0)
- [ ] TEST-005: `tests/conftest.py` — provide shared fixtures: tmp_path for state directory, sample PipelineState, sample SuperOrchestratorConfig, sample BuilderResult list, sample IntegrationReport, sample QualityGateReport — minimum 6 fixtures (review_cycles: 0)
- [ ] TEST-006: `tests/test_docker_orchestrator.py` — test start_services runs docker compose up, test stop_services runs docker compose down, test wait_for_healthy with mocked healthy response, test wait_for_healthy timeout, test get_service_url returns correct URL — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-007: `tests/test_compose_generator.py` — test ComposeGenerator.generate produces valid YAML with Traefik service, PostgreSQL, Redis, user services, test Traefik labels use correct PathPrefix backtick syntax, test service health checks are present, test depends_on uses service_healthy condition, test missing Dockerfile generates default — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-008: `tests/test_traefik_config.py` — test TraefikConfigGenerator.generate_labels produces correct Docker labels with PathPrefix backtick syntax, test strip prefix middleware labels are present, test generate_static_config produces valid YAML with Docker provider and entrypoints.web — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-009: `tests/test_service_discovery.py` — test ServiceDiscovery.get_service_ports parses compose file correctly, test check_health with mocked healthy/unhealthy responses, test wait_all_healthy with mixed health states, test wait_all_healthy timeout — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-010: `tests/test_state_machine.py` — test GracefulShutdown.set_state() stores reference, test _emergency_save() calls PipelineState.save(), test should_stop property, test signal handler sets _should_stop = True — minimum 6 test cases (review_cycles: 0)

---

## Milestone 2: Contract Compliance Verification

- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Implement Schemathesis integration for property-based OpenAPI testing against live services, Pact provider verification for consumer-driven contracts, compliance reporting with per-service and per-endpoint granularity, and a fix loop that feeds violations back to Builders. This milestone produces the contract verification layer consumed by the Quality Gate (M4) and the Integrator (M5).

### Functional Requirements

- [ ] REQ-019: Create `src/integrator/schemathesis_runner.py` with `SchemathesisRunner` class: `__init__(self, project_root: Path)`, `async run_against_service(self, service_name: str, openapi_url: str, base_url: str, max_examples: int = 50) -> list[ContractViolation]` that uses `schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)` to load schema, then iterates API operations programmatically using the `get_all_operations()` API: `for api_operation in schema.get_all_operations(): case = api_operation.make_case(); response = case.call(base_url=base_url); case.validate_response(response)`, catching `schemathesis.failures.FailureGroup` (a list-like container of `Failure` objects) to extract failure details. NOTE: `schema.items()` and `schema[path][method]` are NOT valid Schemathesis 4.x APIs — always use `get_all_operations()` for programmatic iteration. Converts failures to ContractViolation with code "SCHEMA-001" for response schema conformance violations, "SCHEMA-002" for unexpected status codes (4xx/5xx when 2xx expected), "SCHEMA-003" for response time exceeding 5s. The `@schema.parametrize()` decorator is used ONLY in `generate_test_file()`, NOT in programmatic execution. IMPORTANT: Schemathesis `from_url()`, `case.call()`, and `case.validate_response()` are synchronous blocking calls — the async `run_against_service()` method must wrap them with `await asyncio.to_thread(...)` to avoid blocking the event loop (review_cycles: 0)

- [ ] REQ-020: `SchemathesisRunner` continued: `async run_negative_tests(self, service_name: str, openapi_url: str, base_url: str) -> list[ContractViolation]` that tests invalid inputs (empty required fields, wrong types, oversized payloads) are rejected with 4xx status codes, `generate_test_file(self, openapi_path: Path, service_name: str, base_url: str) -> str` returning runnable pytest test code string using `@schema.parametrize()` decorator pattern for the generated file: `schema = schemathesis.openapi.from_path(str(openapi_path)); @schema.parametrize() def test_{service}(case): case.call_and_validate(base_url="{base_url}")` (review_cycles: 0)

- [ ] REQ-021: Create `src/integrator/pact_manager.py` with `PactManager` class: `__init__(self, pact_dir: Path)`, `load_pacts(self) -> dict[str, list[Path]]` scanning pact_dir for *.json Pact files grouped by provider name, `async verify_provider(self, provider_name: str, provider_url: str, pact_files: list[Path]) -> list[ContractViolation]` using `from pact.v3.verifier import Verifier; verifier = Verifier().set_info("provider", url=provider_url)`, adding each pact file via `verifier.add_source(str(pf))`, setting state handler via `verifier.set_state_handler(url=f"{provider_url}/_pact/state", teardown=True)`, then executing `try: result = verifier.verify(); except Exception as e:` — `verify()` returns `Self` (the Verifier instance) on success for method chaining; on failure it raises an exception. IMPORTANT: `Verifier(name)` constructor does NOT exist — use `Verifier().set_info("provider", url=url)`. The `add_transport()` method requires a `host` parameter. `set_state()` does NOT exist — use `set_state_handler()`. All Pact Verifier methods are synchronous — the async `verify_provider()` must wrap `verifier.verify()` with `await asyncio.to_thread(verifier.verify)` to avoid blocking the event loop. Convert failures to ContractViolation with code "PACT-001" for interaction failures and "PACT-002" for state setup failures (review_cycles: 0)

- [ ] REQ-022: `PactManager` continued: `generate_pact_state_handler(self, provider_name: str) -> str` returning Python code for a `/_pact/state` FastAPI endpoint handler that sets up provider states for Pact verification: `@app.post("/_pact/state") async def handle_state(request: Request): body = await request.json(); state = body.get("state"); # dispatch to state setup functions` (review_cycles: 0)

- [ ] REQ-023: Create `src/integrator/contract_compliance.py` with `ContractComplianceVerifier` class: `__init__(self, contract_registry_path: Path, services: dict[str, str])` where services maps service_name to base_url, `async run_schemathesis_tests(self, service_name: str) -> list[ContractViolation]` loading OpenAPI spec from the contract registry and running SchemathesisRunner against the live service, `async run_pact_verification(self, provider_name: str) -> list[ContractViolation]` running PactManager verification, `async verify_all_services(self) -> IntegrationReport` running both Schemathesis and Pact verification for all services in parallel using asyncio.gather with return_exceptions=True, `generate_compliance_report(self) -> str` producing a markdown report with per-service and per-endpoint results (review_cycles: 0)

- [ ] REQ-024: Create `src/integrator/fix_loop.py` with `ContractFixLoop` class: `__init__(self, config: SuperOrchestratorConfig)`, `async feed_violations_to_builder(self, service_id: str, violations: list[ContractViolation], builder_dir: Path) -> float` that: (1) writes `{builder_dir}/FIX_INSTRUCTIONS.md` with categorized violations using `classify_violations()` output formatted as markdown sections per severity (critical first, then error, warning, info), (2) launches subprocess: `proc = await asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", str(builder_dir), "--depth", "quick", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)`, (3) awaits completion with timeout `config.builder.timeout_per_builder`, (4) extracts cost from `{builder_dir}/.agent-team/STATE.json` by reading `json.loads(path.read_text(encoding='utf-8')).get('total_cost', 0.0)`, (5) returns cost as float. On timeout, kills subprocess with `proc.kill()` followed by `await proc.wait()` to reap the zombie process, then returns 0.0. The subprocess must be cleaned up in a `finally` block to prevent resource leaks. `classify_violations(self, violations: list[ContractViolation]) -> dict[str, list[ContractViolation]]` grouping violations by severity (review_cycles: 0)

- [ ] REQ-025: Create `src/integrator/report.py` with `generate_integration_report(results: IntegrationReport) -> str` that produces INTEGRATION_REPORT.md with sections: Summary (pass/fail counts), Per-Service Results (table), Violations (grouped by code), Recommendations (review_cycles: 0)

### Technical Requirements

- [ ] TECH-011: Schemathesis must use `schemathesis.openapi.from_url()` for live service testing and `schemathesis.openapi.from_path()` for static spec testing. The `from_url()` loader resolves all $ref references automatically (review_cycles: 0)
- [ ] TECH-012: Schemathesis `case.validate_response()` raises `schemathesis.failures.FailureGroup` on failure — this is a list-like container of `Failure` objects. Catch this specific exception class to extract violation details. Import via `from schemathesis.failures import FailureGroup`. NOTE: `schemathesis.exceptions.CheckFailed` does NOT exist in Schemathesis 4.x (review_cycles: 0)
- [ ] TECH-013: Pact provider verification must use `from pact.v3.verifier import Verifier`. Constructor is `Verifier()` (no arguments), then chain `.set_info("provider", url=url)` to set the provider. The `.verify()` method returns `Self` (the Verifier instance) on success for method chaining. On failure it raises an exception. There is NO `Verifier(name)` constructor, NO `pact.error.PactVerificationError` class, and NO `set_state()` method — use `set_state_handler()` instead. All Pact Verifier calls are synchronous and must be wrapped in `asyncio.to_thread()` when called from async code (review_cycles: 0)
- [ ] TECH-014: All async methods must use httpx.AsyncClient for HTTP calls with `timeout=30.0` to prevent hanging on unresponsive services (review_cycles: 0)
- [ ] TECH-014a: Schemathesis and Pact libraries are synchronous blocking libraries. All calls to `schemathesis.openapi.from_url()`, `case.call()`, `case.validate_response()`, `verifier.verify()`, and `verifier.set_state_handler()` MUST be wrapped with `await asyncio.to_thread(...)` when called from async methods to avoid blocking the event loop. Example: `schema = await asyncio.to_thread(schemathesis.openapi.from_url, openapi_url, base_url=base_url)` (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-007: `ContractComplianceVerifier` must compose `SchemathesisRunner` and `PactManager` internally — callers only interact with the verifier (review_cycles: 0)
- [ ] WIRE-008: `ContractFixLoop.feed_violations_to_builder()` must write FIX_INSTRUCTIONS.md to the builder's project directory and invoke `python -m agent_team` as a subprocess (review_cycles: 0)

### Service-to-API Wiring

| SVC-ID | Client Method | MCP Tool / HTTP | Request DTO | Response DTO |
|--------|---------------|-----------------|-------------|--------------|
| SVC-001 | ContractComplianceVerifier.run_schemathesis_tests(service_name, openapi_url, base_url) | schemathesis.openapi.from_url() + case.call() + case.validate_response() | { service_name: string, openapi_url: string, base_url: string } | list[ContractViolation] |
| SVC-002 | PactManager.verify_provider(provider_name, provider_url, pact_files) | pact.v3.verifier.Verifier().set_info("provider", url=url).add_source(file).verify() -> Self / raises on failure | { provider_name: string, provider_url: string, pact_files: list[string] } | list[ContractViolation] |
| SVC-003 | ContractFixLoop.feed_violations_to_builder(service_id, violations, builder_dir) | subprocess: python -m agent_team --cwd {builder_dir} --depth quick | { service_id: string, violations: list[ContractViolation], builder_dir: string } | { cost: number } |

- [ ] SVC-001: ContractComplianceVerifier.run_schemathesis_tests(service_name, openapi_url, base_url) -> schemathesis.openapi.from_url() + case.validate_response() { service_name: string, openapi_url: string, base_url: string } -> list[ContractViolation] (review_cycles: 0)
- [ ] SVC-002: PactManager.verify_provider(provider_name, provider_url, pact_files) -> pact.v3.verifier.Verifier().set_info("provider", url=url).add_source(file).verify() returns Self / raises on failure { provider_name: string, provider_url: string, pact_files: list[string] } -> list[ContractViolation] (review_cycles: 0)
- [ ] SVC-003: ContractFixLoop.feed_violations_to_builder(service_id, violations, builder_dir) -> subprocess python -m agent_team --cwd builder_dir --depth quick { service_id: string, violations: list[ContractViolation], builder_dir: string } -> { cost: number } (review_cycles: 0)

### Test Requirements

- [ ] TEST-011: `tests/test_contract_compliance.py` — test SchemathesisRunner.generate_test_file produces valid Python (compile with ast.parse()), test programmatic API uses from_url + get_all_operations + make_case + call + validate_response (not @parametrize or schema.items()), test ContractComplianceVerifier.verify_all_services aggregates results from multiple services, test PactManager.load_pacts groups files by provider — minimum 15 test cases (review_cycles: 0)
- [ ] TEST-012: `tests/test_contract_compliance.py` — test with mocked responses: SCHEMA-001 for schema mismatch, SCHEMA-002 for status code mismatch, SCHEMA-003 for slow response, PACT-001 for interaction failure via Pact exception, test verify_all_services returns IntegrationReport with correct counts, test generate_compliance_report produces markdown — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-013: `tests/test_fix_loop.py` — test ContractFixLoop.feed_violations_to_builder writes FIX_INSTRUCTIONS.md, test subprocess launched with correct args (python -m agent_team --cwd --depth quick), test cost extracted from STATE.json, test classify_violations groups by severity, test timeout kills subprocess and returns 0.0 — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-014: `tests/test_reports.py` — test generate_integration_report produces markdown with Summary, Per-Service, Violations, Recommendations sections, test empty IntegrationReport produces valid markdown — minimum 4 test cases (review_cycles: 0)

---

## Milestone 3: Cross-Service Integration Tests

- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-1
- Description: Build the cross-service test infrastructure: test flow generator that creates integration tests from the Contract Registry + Domain Model using deterministic chain detection, multi-service test executor, data flow tracer that verifies request transformations through service chains, and boundary testing for serialization edge cases (camelCase/snake_case, timezones, null vs missing). This milestone can run in parallel with M2 since both depend only on M1.

### Functional Requirements

- [ ] REQ-026: Create `src/integrator/cross_service_test_generator.py` with `CrossServiceTestGenerator` class: `__init__(self, contract_registry_path: Path, domain_model_path: Path | None = None)`, `generate_flow_tests(self) -> list[dict]` that analyzes contracts to identify multi-service request flows using the following deterministic algorithm: (1) For each OpenAPI contract, extract all POST/PUT endpoint response schemas and all endpoint request schemas. (2) For each pair (Service A response schema, Service B request schema), compute field overlap by counting fields with matching names (case-insensitive) and compatible types (string=string, integer=number, object=object). (3) If field overlap >= 2, create a chain link from Service A to Service B. (4) Build a directed graph of chain links. (5) Find all simple paths of length 2+ with max depth 5. (6) For each path, create a flow dict with flow_id = f"flow_{index}", description, steps list where each step has: service, method, path, request_template (from schema), expected_status (200/201). (7) Sort flows by path length descending, return top 20 (review_cycles: 0)

- [ ] REQ-027: `CrossServiceTestGenerator` continued: `generate_boundary_tests(self) -> list[dict]` creating tests for serialization edge cases: camelCase/snake_case field names across service boundaries, timezone format consistency (ISO 8601 with Z vs +00:00), null vs missing vs empty string. Each test dict contains: test_id, test_type ("case_sensitivity" | "timezone" | "null_handling"), service, endpoint, test_data. `generate_test_file(self, flows: list[dict]) -> str` producing runnable pytest code using httpx.AsyncClient with parameterized flows (review_cycles: 0)

- [ ] REQ-028: Create `src/integrator/cross_service_test_runner.py` with `CrossServiceTestRunner` class: `__init__(self, services: dict[str, str])` mapping service_name to base_url, `async run_flow_tests(self, flows: list[dict]) -> IntegrationReport` executing each flow sequentially (steps within a flow depend on previous step output), collecting results per flow, `async run_single_flow(self, flow: dict) -> tuple[bool, list[str]]` executing one flow's steps in order, passing response data from step N as request data for step N+1, returning (success, error_messages) (review_cycles: 0)

- [ ] REQ-029: Create `src/integrator/data_flow_tracer.py` with `DataFlowTracer` class: `__init__(self, services: dict[str, str])`, `async trace_request(self, entry_service: str, method: str, path: str, body: dict) -> list[dict]` that: (1) generates a unique trace_id = str(uuid.uuid4()), (2) sends request to entry service URL with headers `{"traceparent": f"00-{trace_id}-0000000000000001-01"}` using httpx.AsyncClient, (3) records first hop as `{"service": entry_service, "status": response.status_code, "body": response.json(), "trace_id": trace_id}`, (4) if response contains `x-downstream-services` header or response body has `_trace` field, follow each downstream URL and record additional hops, (5) if NO trace headers are present in response, return single-hop trace list. `verify_data_transformations(self, trace: list[dict], expected_transformations: list[dict]) -> list[str]` where each expected_transformation has format `{"hop_index": int, "field": str, "expected_type": str, "expected_value_pattern": str | None}`, verifies that at each hop the specified field exists with the expected type, returns list of error message strings (review_cycles: 0)

- [ ] REQ-030: Create `src/integrator/boundary_tester.py` with `BoundaryTester` class: `__init__(self, services: dict[str, str])`, `async test_case_sensitivity(self, service_name: str, endpoint: str, camel_body: dict, snake_body: dict) -> list[ContractViolation]` testing that services accept both camelCase and snake_case or reject consistently, `async test_timezone_handling(self, service_name: str, endpoint: str, timestamps: list[str]) -> list[ContractViolation]` testing ISO 8601 format variations (Z, +00:00, +05:30), `async test_null_handling(self, service_name: str, endpoint: str, field_name: str) -> list[ContractViolation]` testing null vs missing vs empty string for optional fields, `async run_all_boundary_tests(self, contracts: list[dict]) -> list[ContractViolation]` running all boundary tests for all contracted endpoints. Each contract dict must contain: `service_name: str`, `endpoint: str` (path), `method: str` (HTTP verb), `request_schema: dict` (JSON Schema), `response_schema: dict` (JSON Schema) — extracted from OpenAPI specs (review_cycles: 0)

### Technical Requirements

- [ ] TECH-015: Cross-service test flows must be generated deterministically from contracts — given the same contract registry, the same flows are always generated in the same order (review_cycles: 0)
- [ ] TECH-016: Flow test steps must pass data using `{step_N_response.field_name}` template variables resolved at runtime — this enables testing real data propagation (review_cycles: 0)
- [ ] TECH-017: All cross-service HTTP calls must use `httpx.AsyncClient` with `timeout=30.0` and `follow_redirects=True` (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-009: `CrossServiceTestGenerator` must read contracts from the same contract registry path used by `ContractComplianceVerifier` in M2 (review_cycles: 0)
- [ ] WIRE-010: `CrossServiceTestRunner` must use the same service URL mapping provided by `DockerOrchestrator` in M1 (review_cycles: 0)

### Test Requirements

- [ ] TEST-015: `tests/test_cross_service.py` — test CrossServiceTestGenerator.generate_flow_tests produces valid flows from sample contracts with at least 2 multi-step flows, test chain detection algorithm matches response schema fields to request schema fields with >= 2 field overlap, test generate_boundary_tests produces camelCase/snake_case test cases, test generate_test_file produces valid Python — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-016: `tests/test_cross_service.py` — test CrossServiceTestRunner.run_single_flow with mocked httpx: success case (all steps pass), failure case (step 2 fails), test data propagation between steps passes response fields to next request, test DataFlowTracer.trace_request with mocked responses returns trace list, test single-hop fallback when no trace headers — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-017: `tests/test_cross_service.py` — test BoundaryTester.test_case_sensitivity with mocked service accepting camelCase but rejecting snake_case, test test_timezone_handling with various ISO 8601 formats, test test_null_handling distinguishing null from missing, test run_all_boundary_tests with sample contracts — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-018: `tests/test_cross_service.py` — test DataFlowTracer.trace_request with single-hop service (no trace headers in response returns single-element list), test multi-hop trace following x-downstream-services header, test verify_data_transformations with correct transformations returns empty error list, test verify_data_transformations with wrong type returns error string, test trace_id is valid UUID format — minimum 8 test cases (review_cycles: 0)

---

## Milestone 4: Quality Gate (4 Layers)

- ID: milestone-4
- Status: PENDING
- Dependencies: milestone-2, milestone-3
- Description: Implement the 4-layer sequential quality gate engine: Layer 1 aggregates per-service build results from Builders, Layer 2 runs cross-service contract compliance (consuming M2's Schemathesis + Pact results), Layer 3 performs system-level security and observability scanning (40 scan codes across 8 categories), Layer 4 runs adversarial heuristic analysis using purely static regex-based detection (dead events, dead contracts, orphan services, naming inconsistency, error boundaries, race conditions). Sequential gating logic: each layer must pass before the next runs, with configurable blocking severity.

### Functional Requirements

- [ ] REQ-031: Create `src/quality_gate/gate_engine.py` with `QualityGateEngine` class: `__init__(self, config: QualityGateConfig, project_root: Path)`, `async run_all_layers(self, builder_results: list[BuilderResult], integration_report: IntegrationReport) -> QualityGateReport` running layers sequentially with gating logic (L1 must pass for L2, L2 for L3, L3 for L4), using `ScanAggregator.aggregate()` to produce the final QualityGateReport. `async run_layer(self, layer: QualityLevel) -> LayerResult` dispatching to the appropriate layer scanner, `should_promote(self, current_layer: QualityLevel, result: LayerResult) -> bool` returning True if the layer passed or if all violations are below blocking_severity, `classify_violations(self, violations: list[ScanViolation]) -> dict[str, list[ScanViolation]]` grouping by severity. Promotion logic: L1 FAIL excludes service from L2+; L2 FAIL with blocking violations enters fix loop; L3 FAIL with severity >= blocking_severity enters fix loop; L4 is always advisory (review_cycles: 0)

- [ ] REQ-032: Create `src/quality_gate/layer1_per_service.py` with `Layer1Scanner` class: `__init__(self, config: QualityGateConfig)`, `evaluate(self, builder_results: list[BuilderResult]) -> LayerResult` checking each BuilderResult for: build success (success == True), test pass rate (test_passed / test_total >= 0.9), convergence ratio (convergence_ratio >= 0.9). Services failing L1 are excluded from subsequent layers. Return LayerResult with total_checks = len(builder_results), passed_checks = number passing all 3 criteria (review_cycles: 0)

- [ ] REQ-033: Create `src/quality_gate/layer2_contract_compliance.py` with `Layer2Scanner` class: `__init__(self, config: QualityGateConfig)`, `evaluate(self, integration_report: IntegrationReport) -> LayerResult` converting IntegrationReport violations to LayerResult. Mark verdict as PASSED if contract_tests_passed == contract_tests_total, PARTIAL if > 70% pass, FAILED otherwise (review_cycles: 0)

- [ ] REQ-034: Create `src/quality_gate/security_scanner.py` with `SecurityScanner` class: `__init__(self, project_root: Path)`, `scan_jwt_auth(self) -> list[ScanViolation]` detecting SEC-001 (unauthenticated endpoints by finding route decorators without auth middleware — pattern: `@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(` without `Depends\(.*auth` within 10 lines), SEC-002 (`algorithms=["none"]` or `algorithms=['none']`), SEC-003 (`verify_signature[\s:=]*False` or `"verify_signature"\s*:\s*False` — must also catch PyJWT `options={"verify_signature": False}` dict format), SEC-004 (`verify_exp[\s:=]*False` or `"verify_exp"\s*:\s*False` — must also catch PyJWT `options={"verify_exp": False}` dict format), SEC-005 (hardcoded JWT secret: `jwt\.(?:encode|decode)\(.+["'][A-Za-z0-9_\-]{20,}["']`), SEC-006 (`algorithms=["HS256"]` used with a variable containing "public" or "pub_key") (review_cycles: 0)

- [ ] REQ-035: `SecurityScanner` continued: `scan_cors(self) -> list[ScanViolation]` detecting CORS-001 (`allow_origins=["*"]` or `allow_origins=\["?\*"?\]`), CORS-002 (`allow_credentials=True` combined with wildcard origins within same CORSMiddleware call), CORS-003 (origin set from request header without validation: `origin\s*=\s*request\.headers`), `scan_secrets(self) -> list[ScanViolation]` detecting SEC-SECRET-001 `AKIA[0-9A-Z]{16}` (AWS access key), SEC-SECRET-002 `-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----` (private key — covers RSA, EC, DSA, OpenSSH, and encrypted PEM formats), SEC-SECRET-003 `(?:api[_-]?key|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]` (API key), SEC-SECRET-004 `(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@` (DB connection string), SEC-SECRET-005 `Bearer\s+[A-Za-z0-9\-._~+/]+=*` (bearer token literal), SEC-SECRET-006 `(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}['"]` (hardcoded password), SEC-SECRET-007 `gh[psatr]_[A-Za-z0-9_]{36,}` (GitHub token — covers ghp_ personal, ghs_ server-to-server, gha_ actions, ghr_ refresh, gho_ OAuth, ghu_ user-to-server), SEC-SECRET-008 `glpat-[A-Za-z0-9\-_]{20,}` (GitLab token), SEC-SECRET-009 `sk_(?:live|test)_[A-Za-z0-9]{24,}` (Stripe key), SEC-SECRET-010 `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` (hardcoded JWT), SEC-SECRET-011 `xox[bpoas]-[0-9]+-[0-9A-Za-z\-]+` (Slack token — covers xoxb bot, xoxp user, xoxa app, xoxo legacy, xoxs session tokens), SEC-SECRET-012 `SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}` (SendGrid key). `scan_all(self) -> list[ScanViolation]` aggregating all JWT + CORS + secrets results (review_cycles: 1)

- [ ] REQ-036: Create `src/quality_gate/observability_checker.py` with `ObservabilityChecker` class: `__init__(self, project_root: Path)`, `scan_logging(self) -> list[ScanViolation]` detecting LOG-001 (`print\s*\(` in .py files excluding test files), LOG-004 (`console\.log\s*\(` in .ts/.js files excluding test/spec files), LOG-005 (sensitive data in log calls — `logging\.(?:info|debug|warning|error)\(.*(?:password|secret|token|api_key)` pattern), `scan_trace_propagation(self) -> list[ScanViolation]` detecting TRACE-001 (httpx/requests/fetch calls without traceparent header — find `httpx\.(?:get|post|put|patch|delete|AsyncClient)` or `requests\.(?:get|post|put)` and check for `traceparent` in headers dict within 10 lines). NOTE: W3C traceparent format is `00-{trace_id}-{parent_id}-{flags}` where trace_id is 32 hex chars, parent_id is 16 hex chars, flags is 2 hex chars (e.g., `00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01`), `scan_health_endpoints(self) -> list[ScanViolation]` detecting HEALTH-001 (services without /health, /healthz, or /ready route — scan for service directories containing route decorators but none matching health path patterns), `scan_all(self) -> list[ScanViolation]` aggregating all results (review_cycles: 0)

- [ ] REQ-037: Create `src/quality_gate/docker_security.py` with `DockerSecurityScanner` class: `__init__(self, project_root: Path)`, `scan_dockerfiles(self) -> list[ScanViolation]` detecting DOCKER-001 (no USER directive after FROM — `^FROM\s+` without subsequent `^USER\s+`), DOCKER-002 (`^ENV\s+(?:PASSWORD|SECRET|API_KEY|PRIVATE_KEY)\s*=`), DOCKER-003 (`^FROM\s+\S+:latest\b` or `^FROM\s+[^:]+$` without tag), DOCKER-004 (`^COPY\s+\.\s+\.`), DOCKER-005 (no `^HEALTHCHECK\s+` instruction in Dockerfile), `scan_compose_files(self) -> list[ScanViolation]` detecting DOCKER-006 (`privileged:\s*true`), DOCKER-007 (`network_mode:\s*["']?host`), DOCKER-008 (`cap_add:.*(?:SYS_ADMIN|ALL)`), `scan_all(self) -> list[ScanViolation]` aggregating results (review_cycles: 0)

- [ ] REQ-038: Create `src/quality_gate/layer3_system_level.py` with `Layer3Scanner` class: `__init__(self, config: QualityGateConfig, project_root: Path)`, `evaluate(self) -> LayerResult` instantiating SecurityScanner, ObservabilityChecker, DockerSecurityScanner and running their scan_all() methods, aggregating all violations, setting verdict based on whether any violations have severity >= config.blocking_severity (review_cycles: 0)

- [ ] REQ-039: Create `src/quality_gate/adversarial_patterns.py` with `AdversarialScanner` class (purely static, NO MCP dependency): `__init__(self, project_root: Path)`, `detect_dead_events(self) -> list[ScanViolation]` finding ADV-001 using compiled regex: publisher pattern `_RE_EVENT_PUBLISH = re.compile(r"(?:publish|emit|dispatch|send_event|fire)\s*\(\s*['\"](\w+)['\"]")`, consumer pattern `_RE_EVENT_SUBSCRIBE = re.compile(r"(?:subscribe|on|addEventListener|consume|handle|listen)\s*\(\s*['\"](\w+)['\"]")`. Scan all .py/.ts/.js files (excluding node_modules, .venv, __pycache__, dist, build). Collect published event names and consumed event names. Report ADV-001 for each event name in publishers but not consumers (review_cycles: 0)

- [ ] REQ-040: `AdversarialScanner` continued: `detect_dead_contracts(self) -> list[ScanViolation]` finding ADV-002 by scanning contract directories (contracts/, .contracts/, pacts/) for JSON/YAML contract files, extracting endpoint paths from OpenAPI `paths` keys, then searching project files for route decorators matching those paths using `_RE_ROUTE_PATH = re.compile(r"(?:@(?:app|router)\.\w+|@Route|@HttpGet|@HttpPost|HandleFunc)\s*\(\s*['\"]([^'\"]+)['\"]")`. Report ADV-002 for paths in contracts with no matching route (review_cycles: 0)

- [ ] REQ-041: `AdversarialScanner` continued: `detect_orphan_services(self) -> list[ScanViolation]` finding ADV-003 by scanning for service directories (containing Dockerfile or package.json or pyproject.toml), then checking each for HTTP client imports (`_RE_HTTP_CLIENT = re.compile(r"(?:httpx|requests|fetch|axios|HttpClient)")`) and HTTP server imports (`_RE_HTTP_SERVER = re.compile(r"(?:FastAPI|Express|app\.listen|WebApplication)")`). Report ADV-003 for directories with no HTTP client AND no HTTP server AND no event publish/subscribe patterns (review_cycles: 0)

- [ ] REQ-042: `AdversarialScanner` continued: `check_naming_consistency(self) -> list[ScanViolation]` finding ADV-004 by scanning API handler files for JSON field naming using `_RE_JSON_FIELD = re.compile(r"['\"](\w+)['\"]\s*:")`. Classify as camelCase (`[a-z]+(?:[A-Z][a-z]*)+`) or snake_case (`[a-z]+(?:_[a-z]+)+`). Report ADV-004 for services using mixed conventions (both styles in >10% of fields each). `scan_error_handling(self) -> list[ScanViolation]` finding ADV-005 using `_RE_ASYNC_DEF = re.compile(r"async\s+(?:def|function)\s+\w+")` followed by body without `try` within next 50 lines, and `_RE_BARE_EXCEPT = re.compile(r"except\s*(?:Exception\s*)?:")` without re-raise. `scan_race_conditions(self) -> list[ScanViolation]` finding ADV-006 using `_RE_GLOBAL_MUTABLE = re.compile(r"^(\w+)\s*(?::\s*(?:list|dict|set|List|Dict|Set))?\s*=\s*(?:\[|\{|dict\(|list\(|set\()", re.MULTILINE)` then checking if the variable appears inside an `async def` body. `scan_all(self) -> list[ScanViolation]` aggregating all results (review_cycles: 0)

- [ ] REQ-043: Create `src/quality_gate/layer4_adversarial.py` with `Layer4Scanner` class: `__init__(self, config: QualityGateConfig, project_root: Path)`, `evaluate(self) -> LayerResult` running AdversarialScanner.scan_all(), setting verdict to PASSED always (Layer 4 is advisory-only), populating violations list for reporting (review_cycles: 0)

- [ ] REQ-044: Create `src/quality_gate/scan_aggregator.py` with `ScanAggregator` class: `aggregate(self, layer_results: list[LayerResult]) -> QualityGateReport` computing overall_verdict (PASSED if all layers passed, PARTIAL if any layer partial, FAILED if any blocking layer failed), total_violations and blocking_violations counts, `deduplicate(self, violations: list[ScanViolation]) -> list[ScanViolation]` removing duplicate violations with same code+file_path+line (review_cycles: 0)

- [ ] REQ-045: Create `src/quality_gate/report.py` with `generate_quality_gate_report(report: QualityGateReport) -> str` producing QUALITY_GATE_REPORT.md with sections: Overall Verdict, Per-Layer Results (table with layer name, verdict, violation count), Blocking Violations (grouped by category), Advisory Findings (Layer 4 results), Fix History (attempts count and max) (review_cycles: 0)

### Technical Requirements

- [ ] TECH-018: All security scanner regex patterns must be compiled once at module level (re.compile) for performance — each scanner may process thousands of files (review_cycles: 0)
- [ ] TECH-019: Security scanner must skip files in node_modules/, .venv/, venv/, __pycache__/, .git/, dist/, build/ directories (review_cycles: 0)
- [ ] TECH-020: Secret scanning must support inline suppression comments: `# nosec`, `// nosec`, `# noqa: SEC-SECRET-xxx` — lines with these comments are skipped (review_cycles: 0)
- [ ] TECH-021: Layer 3 scanners must cap violations at 200 per category to prevent report explosion on large codebases (review_cycles: 0)
- [ ] TECH-022: AdversarialScanner must be purely static (regex-based). No MCP calls, no Build 1 dependency. This ensures M4 is executable without running services and complies with INT-006 (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-011: `QualityGateEngine` must compose all 4 layer scanners internally and accept BuilderResults + IntegrationReport as inputs (review_cycles: 0)
- [ ] WIRE-012: `Layer2Scanner` consumes IntegrationReport from M2's ContractComplianceVerifier (review_cycles: 0)
- [ ] WIRE-013: `Layer3Scanner` instantiates SecurityScanner, ObservabilityChecker, DockerSecurityScanner and calls their scan_all() methods (review_cycles: 0)
- [ ] WIRE-014: `QualityGateEngine.run_all_layers()` must call `ScanAggregator.aggregate()` to produce the final QualityGateReport (review_cycles: 0)

### Service-to-API Wiring

| SVC-ID | Client Method | Internal | Request DTO | Response DTO |
|--------|---------------|----------|-------------|--------------|
| SVC-004 | Layer2Scanner.evaluate(integration_report) | Internal: IntegrationReport consumption | { integration_report: IntegrationReport } | LayerResult { verdict: string, violations: list, total_checks: number, passed_checks: number } |

- [ ] SVC-004: Layer2Scanner.evaluate(integration_report) -> Internal IntegrationReport consumption { integration_report: IntegrationReport } -> LayerResult { verdict: string, violations: list, total_checks: number, passed_checks: number } (review_cycles: 0)

### Test Requirements

- [ ] TEST-019: `tests/test_quality_gate.py` — test QualityGateEngine.run_all_layers with all layers passing returns PASSED verdict, test L1 failure excludes service from L2+, test L2 failure with blocking severity enters fix path, test L3 non-blocking warning allows L4 to run, test L4 always advisory, test ScanAggregator produces correct overall_verdict — minimum 15 test cases (review_cycles: 0)
- [ ] TEST-020: `tests/test_quality_gate.py` — test Layer1Scanner.evaluate with all passing BuilderResults (success=True, test_passed/test_total >= 0.9, convergence_ratio >= 0.9), test L1 with failing BuilderResult (success=False) marks service as excluded, test L1 with low test pass rate (<0.9) marks partial, test L1 with zero builders returns empty — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-021: `tests/test_quality_gate.py` — test Layer2Scanner.evaluate with all contracts passing (verdict PASSED), test L2 with >70% pass rate (verdict PARTIAL), test L2 with <70% pass rate (verdict FAILED), test L2 with zero contract tests (verdict SKIPPED) — minimum 4 test cases (review_cycles: 0)
- [ ] TEST-022: `tests/test_quality_gate.py` — test Layer3Scanner.evaluate instantiates and runs SecurityScanner, ObservabilityChecker, DockerSecurityScanner, test L3 with no violations returns PASSED, test L3 with warning-severity violations and blocking_severity="error" returns PASSED, test L3 with error-severity violations returns FAILED — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-023: `tests/test_security_scanner.py` — test SEC-001 through SEC-006 each with planted vulnerable code, test CORS-001/002/003, test SEC-SECRET-001 through SEC-SECRET-012 with planted secrets matching exact regex patterns, test nosec suppression comment skips violation, test skip directories (node_modules, .venv) — minimum 20 test cases (review_cycles: 0)
- [ ] TEST-024: `tests/test_observability.py` — test LOG-001 detects print() in .py files, test LOG-004 detects console.log in .ts, test LOG-005 detects password in log calls, test TRACE-001 detects HTTP calls without traceparent, test HEALTH-001 detects missing health endpoint — minimum 10 test cases (review_cycles: 0)
- [ ] TEST-025: `tests/test_docker_security.py` — test DOCKER-001 through DOCKER-008 each with planted vulnerable Dockerfile or compose file, test scan skips non-Docker files — minimum 12 test cases (review_cycles: 0)
- [ ] TEST-026: `tests/test_adversarial.py` — test ADV-001 with planted publish/subscribe calls and unmatched events, test ADV-002 with contract file having path not in any route decorator, test ADV-003 with orphan service directory, test ADV-004 with mixed camelCase/snake_case in same service, test ADV-005 with async function missing try/except, test ADV-006 with global mutable list modified in async def, test Layer4 verdict is always PASSED regardless of violations — minimum 14 test cases (review_cycles: 0)
- [ ] TEST-027: `tests/test_scan_aggregator.py` — test ScanAggregator.aggregate computes correct overall_verdict (all passed -> PASSED, any failed -> FAILED, mixed -> PARTIAL), test deduplicate removes duplicate code+file_path+line combinations, test blocking_violations count excludes advisory — minimum 6 test cases (review_cycles: 0)
- [ ] TEST-028: `tests/test_reports.py` — test generate_quality_gate_report produces markdown with Overall Verdict, Per-Layer Results, Blocking Violations, Advisory Findings, Fix History sections — minimum 4 test cases (review_cycles: 0)
- [ ] TEST-029: `tests/test_reports.py` — test generate_integration_report with zero violations produces valid markdown, test with 50+ violations produces truncated violation table, test markdown headers match expected section names (Summary, Per-Service Results, Violations, Recommendations) — minimum 4 test cases (review_cycles: 0)

---

## Milestone 5: Super Orchestrator Pipeline

- ID: milestone-5
- Status: PENDING
- Dependencies: milestone-1, milestone-4
- Description: Implement the Super Orchestrator's async pipeline execution engine that drives the state machine through all phases: Architect (Build 1 MCP), Contract Registration (Build 1 MCP), parallel Builders (Build 2 agent-team), Integration (M1 Docker + M2 contracts + M3 cross-service), Quality Gate (M4), and fix passes. Includes cost tracking per phase, state persistence for pause/resume/retry, individual builder failure isolation, per-transition error handling, and the main execute_pipeline() loop.

### Functional Requirements

- [ ] REQ-046: Create `src/super_orchestrator/pipeline.py` with `async run_architect_phase(prd_path: Path, config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> float` that invokes the Build 1 Architect via MCP stdio. Uses: `from mcp import StdioServerParameters; from mcp.client.stdio import stdio_client; from mcp.client.session import ClientSession`. Creates session: `async with stdio_client(StdioServerParameters(command="python", args=["-m", "src.architect.mcp_server"], cwd=config.build1_services_dir)) as (read, write): async with ClientSession(read, write) as session: await session.initialize(); result = await session.call_tool("decompose", {"prd_text": prd_content})`. Falls back to subprocess + JSON if MCP SDK import fails: `proc = await asyncio.create_subprocess_exec("python", "-m", "src.architect.mcp_server", stdin=PIPE, stdout=PIPE)`. Extracts ServiceMap, DomainModel, contract_stubs from result JSON. Saves artifact paths to state. Returns estimated cost. Timeout: config.architect.timeout seconds. On timeout raise PhaseTimeoutError (review_cycles: 0)

- [ ] REQ-047: Create `async run_contract_registration(service_map_path: Path, config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> float` that reads the ServiceMap, extracts contract stubs, registers them with the Build 1 Contract Engine via MCP (using `create_contract`, `validate_spec`), validates all contracts are stored, saves contract_registry_path to state, returns cost (review_cycles: 0)

- [ ] REQ-048: Create `async run_parallel_builders(builder_configs: list[dict], config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker, max_concurrent: int = 3) -> list[BuilderResult]` that launches multiple Builder subprocesses bounded by `asyncio.Semaphore(max_concurrent)` (create the semaphore INSIDE the function body, not at module level, to ensure it is bound to the running event loop). Each builder_config dict contains: `service_id: str`, `service_info: ServiceInfo`, `prd_content: str` (service-specific PRD section), `contracts_path: Path` (service's contracts), `output_dir: Path` (where builder writes output), `config: dict` (from generate_builder_config()). Collects BuilderResult from each by parsing the builder's `{output_dir}/.agent-team/STATE.json`. Map STATE.json fields to BuilderResult fields as follows: `success = state_json["summary"]["success"]` (bool), `cost = state_json["total_cost"]` (float), `test_passed = state_json["summary"]["test_passed"]` (int), `test_total = state_json["summary"]["test_total"]` (int), `convergence_ratio = state_json["summary"]["convergence_ratio"]` (float). NOTE: Build 2's RunState.to_dict() writes these computed summary fields — see Build 2 TECH-031, updates state.builder_statuses and state.builder_costs per builder, handles individual builder failures without killing the pipeline (return BuilderResult with success=False and error message), returns all results (review_cycles: 0)

- [ ] REQ-049: Create `generate_builder_config(global_config: SuperOrchestratorConfig, service_info: ServiceInfo, contracts_path: Path) -> dict` that produces a scoped config.yaml dict for one Builder matching agent-team config.yaml format. The generated config must include: `{"depth": global_config.builder.depth, "milestone": {"enabled": True, "health_gate": True}, "e2e_testing": {"enabled": True, "backend_api_tests": True}, "post_orchestration_scans": {"mock_data_scan": True, "api_contract_scan": True}}`. IMPORTANT: All keys in the generated dict must match the exact field names from agent-team's AgentTeamConfig — verify against Build 2's config.py. The `depth` value must propagate from `global_config.builder.depth` (not be hardcoded). The dict is written to `{builder_output_dir}/config.yaml` via `yaml.safe_dump()` by the caller (review_cycles: 0)

- [ ] REQ-050: Create `async run_integration_phase(builder_results: list[BuilderResult], config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> IntegrationReport` that: (1) generates docker-compose.yml from builder outputs using ComposeGenerator (M1), (2) starts services via DockerOrchestrator (M1), (3) waits for health checks, (4) runs ContractComplianceVerifier.verify_all_services() from M2, (5) runs CrossServiceTestRunner.run_flow_tests() from M3, (6) runs BoundaryTester.run_all_boundary_tests() from M3, (7) calls `generate_integration_report()` and writes INTEGRATION_REPORT.md to .super-orchestrator/, (8) stops services in finally block, (9) returns aggregated IntegrationReport (review_cycles: 0)

- [ ] REQ-051: Create `async run_quality_gate(integration_report: IntegrationReport, builder_results: list[BuilderResult], config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> QualityGateReport` that runs QualityGateEngine.run_all_layers() from M4 with builder_results and integration_report, calls `generate_quality_gate_report()` and writes QUALITY_GATE_REPORT.md to .super-orchestrator/, saves quality_report_path to state, returns report (review_cycles: 0)

- [ ] REQ-052: Create `async run_fix_pass(quality_report: QualityGateReport, config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker) -> float` that identifies violating services from the quality report, uses ContractFixLoop.feed_violations_to_builder() from M2 for each violating service, increments state.quality_attempts, returns total fix cost (review_cycles: 0)

- [ ] REQ-053: Create `async execute_pipeline(prd_path: Path, config: SuperOrchestratorConfig, state: PipelineState, tracker: PipelineCostTracker, shutdown: GracefulShutdown) -> None` — the main pipeline loop that: (1) creates the state machine via create_pipeline_machine(), (2) checks shutdown.should_stop before each phase, (3) drives transitions through the state machine (start_architect -> architect_done -> approve_architecture -> contracts_ready -> builders_done -> start_integration -> integration_done -> quality_passed/quality_failed), (4) saves state after every phase transition, (5) checks budget after every phase, (6) handles the quality gate fix loop (quality_failed -> fix_pass -> fix_done -> quality_gate, up to max_fix_retries), (7) on complete: prints summary, (8) on failed: saves failure report. All subprocess management (builders, fix passes) must use `try/finally` to ensure `proc.kill()` + `await proc.wait()` cleanup on cancellation or timeout. Error handling per transition: (a) `start_architect` raises PhaseTimeoutError -> retry up to `config.architect.max_retries`, then transition to `failed` with interrupt_reason. (b) `contracts_ready` fails -> log warning, proceed with available contracts (partial is OK). (c) `builders_done` with all builders failed (all BuilderResult.success == False) -> transition to `failed`. If some failed, proceed with successful builders only. (d) `integration_done` -> proceed to quality_gate regardless of integration health (quality gate evaluates). (e) `quality_failed` -> enter fix loop bounded by `config.quality_gate.max_fix_retries` (review_cycles: 1)

### Technical Requirements

- [ ] TECH-023: Builder subprocesses must run via `asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", str(builder_dir), "--depth", config.builder.depth)` with stdout/stderr capture for logging (review_cycles: 0)
- [ ] TECH-024: Builder subprocess isolation: each builder runs in its own directory with its own config.yaml, its own .agent-team/ state, and cannot access other builders' directories (review_cycles: 0)
- [ ] TECH-025: The pipeline must save state (PipelineState.save()) BEFORE every phase transition to enable resume from the exact point of interruption (review_cycles: 0)
- [ ] TECH-026: Budget checking must happen after every phase. If budget exceeded, save state and raise BudgetExceededError (review_cycles: 0)
- [ ] TECH-027: The top-level entry point must call `asyncio.run()` exactly once. All subsequent async calls use `await`. No nested asyncio.run() (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-015: `run_architect_phase` must use MCP stdio transport to communicate with Build 1's Architect service — import MCP client lazily inside function body with ImportError fallback to subprocess + JSON (review_cycles: 0)
- [ ] WIRE-016: `run_parallel_builders` must use Build 2's `create_execution_backend()` pattern when Agent Teams is available, falling back to subprocess mode (review_cycles: 0)
- [ ] WIRE-017: `run_integration_phase` must compose DockerOrchestrator (M1), ContractComplianceVerifier (M2), CrossServiceTestRunner (M3), and BoundaryTester (M3) (review_cycles: 0)
- [ ] WIRE-018: `execute_pipeline` must pass the GracefulShutdown instance's should_stop check before each phase transition (review_cycles: 0)
- [ ] WIRE-019: `run_integration_phase()` must call `generate_integration_report()` after collecting results and write INTEGRATION_REPORT.md to .super-orchestrator/ (review_cycles: 0)
- [ ] WIRE-020: `run_quality_gate()` must call `generate_quality_gate_report()` after gate completes and write QUALITY_GATE_REPORT.md to .super-orchestrator/ (review_cycles: 0)

### Service-to-API Wiring

| SVC-ID | Client Method | MCP Tool / Subprocess | Request DTO | Response DTO |
|--------|---------------|----------------------|-------------|--------------|
| SVC-005 | run_architect_phase(prd_path) | MCP stdio: python -m src.architect.mcp_server -> decompose (fallback: subprocess + JSON) | { prd_text: string } | { service_map: ServiceMap, domain_model: DomainModel, contract_stubs: list } |
| SVC-006 | run_contract_registration(service_map_path) | MCP stdio: Contract Engine -> create_contract | { service_name: string, type: string, version: string, spec: dict } | { id: string, status: string, spec_hash: string } |
| SVC-007 | run_contract_registration(service_map_path) | MCP stdio: Contract Engine -> validate_spec | { spec: dict, type: string } | { valid: boolean, errors: list, warnings: list } |
| SVC-008 | run_contract_registration(service_map_path) | MCP stdio: Contract Engine -> list_contracts | { service_name: string } | list[{ id: string, type: string, version: string, status: string }] |
| SVC-009 | run_parallel_builders(builder_configs) | subprocess: python -m agent_team --cwd {dir} --depth {depth} | { service_id: string, output_dir: string, config: dict } | BuilderResult { success: boolean, cost: number, test_passed: number, test_total: number } |
| SVC-010 | run_quality_gate(integration_report, builder_results) | Internal: QualityGateEngine.run_all_layers() | { builder_results: list[BuilderResult], integration_report: IntegrationReport } | QualityGateReport { overall_verdict: string, layers: dict, total_violations: number } |
| SVC-011 | run_fix_pass(quality_report) | subprocess: python -m agent_team --cwd {dir} --depth quick | { service_id: string, violations: list[ContractViolation] } | { cost: number } |

- [ ] SVC-005: run_architect_phase(prd_path) -> MCP stdio python -m src.architect.mcp_server -> decompose { prd_text: string } -> { service_map: ServiceMap, domain_model: DomainModel, contract_stubs: list } (review_cycles: 0)
- [ ] SVC-006: run_contract_registration(service_map_path) -> MCP stdio Contract Engine -> create_contract { service_name: string, type: string, version: string, spec: dict } -> { id: string, status: string, spec_hash: string } (review_cycles: 0)
- [ ] SVC-007: run_contract_registration(service_map_path) -> MCP stdio Contract Engine -> validate_spec { spec: dict, type: string } -> { valid: boolean, errors: list, warnings: list } (review_cycles: 0)
- [ ] SVC-008: run_contract_registration(service_map_path) -> MCP stdio Contract Engine -> list_contracts { service_name: string } -> list[{ id: string, type: string, version: string, status: string }] (review_cycles: 0)
- [ ] SVC-009: run_parallel_builders(builder_configs) -> subprocess python -m agent_team --cwd {dir} --depth {depth} { service_id: string, output_dir: string, config: dict } -> BuilderResult { success: boolean, cost: number, test_passed: number, test_total: number } (review_cycles: 0)
- [ ] SVC-010: run_quality_gate(integration_report, builder_results) -> QualityGateEngine.run_all_layers() { builder_results: list[BuilderResult], integration_report: IntegrationReport } -> QualityGateReport { overall_verdict: string, layers: dict, total_violations: number } (review_cycles: 0)
- [ ] SVC-011: run_fix_pass(quality_report) -> subprocess python -m agent_team --cwd {dir} --depth quick { service_id: string, violations: list[ContractViolation] } -> { cost: number } (review_cycles: 0)

### Test Requirements

- [ ] TEST-030: `tests/test_pipeline.py` — test run_architect_phase with mocked MCP session returning ServiceMap, test MCP fallback to subprocess when import fails, test run_parallel_builders with 3 mocked builders (2 succeed, 1 fails), test run_integration_phase with mocked Docker and verifier, test run_quality_gate with mocked gate engine, test run_fix_pass with mocked fix loop, test execute_pipeline full flow with all phases mocked — minimum 20 test cases (review_cycles: 0)
- [ ] TEST-031: `tests/test_pipeline.py` — test budget check halts pipeline when exceeded, test shutdown.should_stop halts pipeline between phases, test state saved before each transition, test resume from saved state re-enters at correct phase, test individual builder failure doesn't kill pipeline, test all-builders-fail transitions to failed state, test partial contract failure proceeds with warning — minimum 12 test cases (review_cycles: 0)
- [ ] TEST-032: `tests/test_pipeline.py` — test generate_builder_config produces valid agent-team config.yaml dict with depth from global config, milestone enabled, e2e enabled, test builder_config format has all required fields (service_id, service_info, prd_content, contracts_path, output_dir, config) — minimum 6 test cases (review_cycles: 0)

---

## Milestone 6: CLI + Display

- ID: milestone-6
- Status: PENDING
- Dependencies: milestone-5
- Description: Implement the Typer CLI with 6 commands (init, plan, build, integrate, verify, run) plus status and resume utilities, Rich terminal UI with progress bars and live dashboard, and the YAML configuration template for the entire super team.

### Functional Requirements

- [ ] REQ-054: Create `src/super_orchestrator/cli.py` with Typer app defining 8 commands plus a `--version` flag callback: `def version_callback(value: bool): if value: typer.echo(f"super-orchestrator {__version__}"); raise typer.Exit()` registered as `app = typer.Typer(...); @app.callback() def main(version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True))`. The 8 commands are: `init(prd_path: Path, output_dir: Path = Path("."))` validating PRD, creating .super-orchestrator/, initializing PipelineState; `plan(system: str = "all")` loading state and running Architect phase; `build(parallel: bool = True, system: list[int] | None = None, max_concurrent: int = 3)` running Builder fleet; `integrate(compose_file: Path | None = None)` running Integrator; `verify(fix: bool = True, layer: int | None = None)` running Quality Gate; `run(prd_path: Path, resume: bool = False)` running full pipeline; `status()` displaying current state; `resume()` resuming interrupted pipeline (review_cycles: 0)

- [ ] REQ-055: The `init` command must: validate PRD file exists and is > 100 bytes, create .super-orchestrator/ directory, copy PRD to .super-orchestrator/PRD.md, generate pipeline_id as UUID, initialize PipelineState and save, write default config.yaml if not present, check for `docker compose version` and warn if not found (review_cycles: 0)

- [ ] REQ-056: The `run` command must: call init if --resume is False, install GracefulShutdown handler, create PipelineCostTracker, call execute_pipeline(), catch PipelineError and display Rich error panel, catch KeyboardInterrupt and save state (review_cycles: 0)

- [ ] REQ-057: The `status` command must: load PipelineState, display Rich table with current_state, completed_phases, builder statuses (per-service table), quality gate results (per-layer), total cost, elapsed time since started_at (review_cycles: 0)

- [ ] REQ-058: The `resume` command must: load PipelineState (exit with error if none exists), validate PRD and config files still exist, determine resume trigger from RESUME_TRIGGERS map, re-enter pipeline at saved state by calling execute_pipeline with pre-loaded state (review_cycles: 0)

- [ ] REQ-059: Create `src/super_orchestrator/display.py` with Rich-based display functions: `print_pipeline_header(state: PipelineState, tracker: PipelineCostTracker)` using `Panel(title="Pipeline Overview")`, `print_phase_table(state: PipelineState, tracker: PipelineCostTracker)` using `Table(title="Phase Status")` with columns phase/status/cost/duration, `print_builder_table(state: PipelineState)` using `Table(title="Builder Status")` with columns service/status/tests/cost, `print_quality_summary(report: QualityGateReport)` using `Panel(Group(Table(...)))` (import Group from `rich.console` via `from rich.console import Group`) with per-layer results, `print_error_panel(error: Exception)` using `Panel(style="red")`, `create_progress_bar(description: str) -> Progress` returning `Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn())`, `print_final_summary(state: PipelineState, tracker: PipelineCostTracker)` showing complete pipeline summary on completion. All display functions must use a module-level `_console = Console()` singleton (created once at module level) to ensure consistent terminal width detection and avoid overhead of repeated Console instantiation (review_cycles: 0)

- [ ] REQ-060: Create default `config.yaml` template in project root with all SuperOrchestratorConfig fields documented with comments explaining each option (review_cycles: 0)

### Technical Requirements

- [ ] TECH-028: Typer CLI must use `typer.Typer(name="super-orchestrator", help="Super Agent Team Pipeline Orchestrator")` with `rich_markup_mode="rich"` for formatted help text (review_cycles: 0)
- [ ] TECH-029: All CLI commands that run async code must use `asyncio.run()` via a wrapper pattern: define the Typer command as a sync function that calls `asyncio.run(_async_impl())`. Example: `@app.command() def run(...): asyncio.run(_run_impl(...))`. This avoids issues with Typer's own sync/async handling. There must be exactly ONE `asyncio.run()` call per CLI invocation — never nest `asyncio.run()` inside an already-running event loop (review_cycles: 0)
- [ ] TECH-030: Rich Progress must use `Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn())` for consistent display. Import all from their correct modules: `from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn`, `from rich.panel import Panel`, `from rich.table import Table`, `from rich.console import Console, Group` (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-021: CLI commands must load SuperOrchestratorConfig from config.yaml in cwd or .super-orchestrator/ (review_cycles: 0)
- [ ] WIRE-022: `run` command must instantiate GracefulShutdown, PipelineCostTracker, load/create PipelineState, and pass all to execute_pipeline() (review_cycles: 0)

### Test Requirements

- [ ] TEST-033: `tests/test_cli.py` — test init command creates .super-orchestrator/ with PipelineState, test init rejects empty PRD (< 100 bytes), test init checks docker compose version, test status displays table without error, test resume exits with error when no state, test run command with mocked pipeline, test all 8 commands are registered — minimum 14 test cases using typer.testing.CliRunner (review_cycles: 0)
- [ ] TEST-034: `tests/test_display.py` — test print_pipeline_header produces Rich Panel, test print_phase_table produces Rich Table with correct columns, test print_builder_table shows per-service data, test print_quality_summary shows per-layer results, test print_error_panel shows error in red panel, test create_progress_bar returns Progress with correct columns — minimum 8 test cases (review_cycles: 0)
- [ ] TEST-035: `tests/test_config.py` — test default config.yaml template contains all SuperOrchestratorConfig fields with documented comments, test load_super_config from template produces valid config, test YAML round-trip (write template, load back, verify all fields match defaults), test config.yaml with unknown keys is silently ignored — minimum 6 test cases (review_cycles: 0)

---

## Milestone 7: End-to-End Verification

- ID: milestone-7
- Status: PENDING
- Dependencies: milestone-5, milestone-6
- Description: Full pipeline integration test using a 3-service test application (auth, orders, notifications), system report generation verifying all quality gate layers pass, performance benchmarks, backward compatibility checks ensuring Build 3 works correctly with Build 1 and Build 2 outputs.

### Functional Requirements

- [ ] REQ-061: Create `tests/fixtures/sample_prd.md` — a realistic 3-service application PRD with: auth-service (user registration, login, JWT tokens), order-service (CRUD orders, order state machine: pending -> confirmed -> shipped -> delivered), notification-service (email/SMS on order events). Must include at least 3 entities (User, Order, Notification), at least 2 cross-service API contracts, at least 1 event-driven contract (OrderCreated, OrderShipped events), at least 1 state machine (review_cycles: 0)

- [ ] REQ-062: Create `tests/fixtures/sample_openapi.yaml` — valid OpenAPI 3.1 spec for the order-service with GET/POST/PUT endpoints, User and Order schemas, standard error responses. Must pass openapi-spec-validator validation (review_cycles: 0)

- [ ] REQ-063: Create `tests/fixtures/sample_pact.json` — valid Pact V4 contract between notification-service (consumer) and order-service (provider) with interactions for GET /orders/{id} and POST /orders/{id}/events (review_cycles: 0)

- [ ] REQ-064: Create `tests/fixtures/sample_docker_compose.yml` — minimal compose file for 3 test services with health checks, Traefik, and PostgreSQL (review_cycles: 0)

- [ ] REQ-065: Create `tests/test_integration_e2e.py` with full pipeline integration test: mock Build 1 MCP tools (Architect returns sample ServiceMap, Contract Engine validates specs), mock Build 2 builders (return successful BuilderResults with test counts), run integration phase with mocked Docker (services report healthy), run quality gate with planted violations in test files, verify fix loop triggers for blocking violations, verify final report is generated. This test must run entirely with mocked external dependencies (no real Docker, no real MCP servers) (review_cycles: 1)

- [ ] REQ-066: Test that `execute_pipeline` produces PIPELINE_STATE.json with all fields populated after successful run, including completed_phases containing all phase names, total_cost > 0, quality_report_path pointing to existing file (review_cycles: 0)

- [ ] REQ-067: Test that resume from any interrupted state (architect_running, builders_running, quality_gate, fix_pass) correctly re-enters the pipeline at the saved state and completes without re-running completed phases (review_cycles: 0)

- [ ] REQ-068: Test that GracefulShutdown handler correctly saves state when SIGINT is received during execute_pipeline — simulate by setting shutdown.should_stop = True between phases (review_cycles: 0)

- [ ] REQ-069: Test that budget exceeded during builders_running phase correctly saves state and raises BudgetExceededError with accurate cost information (review_cycles: 0)

- [ ] REQ-070: Test that all 40 quality gate scan codes from constants.py are exercised by at least one scanner — verify by checking scan_codes property of each scanner matches expected codes, `len(ALL_SCAN_CODES) == 40` (review_cycles: 0)

### Integration Requirements

- [ ] INT-001: Build 3 depends on Build 1's Architect MCP server for PRD decomposition — when unavailable, pipeline must raise ConfigurationError with clear message directing user to start Build 1 services (review_cycles: 0)
- [ ] INT-002: Build 3 depends on Build 1's Contract Engine MCP server for contract registration and validation — when unavailable, pipeline must raise ConfigurationError (review_cycles: 0)
- [ ] INT-003: Build 3 depends on Build 2's agent-team CLI for Builder execution — when unavailable, pipeline must raise ConfigurationError. Build 2 with `agent_teams.enabled=False` (CLI mode) is the minimum requirement (review_cycles: 0)
- [ ] INT-004: Docker Compose v2 and Docker Engine must be available for integration testing — the `init` command should check for `docker compose version` and warn if not found (review_cycles: 0)
- [ ] INT-005: Build 3 must work with Build 1 services running either locally (via Docker Compose) or via MCP stdio (subprocess) — the config must allow both modes (review_cycles: 0)
- [ ] INT-006: All Build 3 modules must be importable without Build 1 or Build 2 installed — MCP client imports must be lazy (inside function bodies) with clear ImportError messages (review_cycles: 0)
- [ ] INT-007: Pipeline phase order (architect -> contracts -> builders -> integration -> quality_gate -> fix) must be preserved — the state machine enforces this via transitions (review_cycles: 0)
- [ ] INT-008: State persistence must survive process restart at any phase — PipelineState.load() from .super-orchestrator/ must reconstruct the exact state for resume (review_cycles: 0)

### Security Requirements

- [ ] SEC-001: The Super Orchestrator must not pass ANTHROPIC_API_KEY or other secrets as environment variables to Builder subprocesses — Builders inherit environment from parent process (review_cycles: 0)
- [ ] SEC-002: Docker Compose files generated by ComposeGenerator must not contain hardcoded passwords — use ${ENV_VAR:-default} syntax for all secrets (review_cycles: 0)
- [ ] SEC-003: Traefik dashboard must be disabled by default (--api.dashboard=false) — enabled only when explicitly configured (review_cycles: 0)
- [ ] SEC-004: Docker socket mount must be read-only (:/var/run/docker.sock:ro) in generated compose files (review_cycles: 0)

### Test Requirements

- [ ] TEST-036: `tests/test_integration_e2e.py` — full pipeline test with 3-service sample app: mock Architect producing ServiceMap with 3 services, mock Contract Engine validating specs, mock 3 Builders returning successful results, mock Docker starting and health-checking, run quality gate against test fixture files with planted SEC-001 and LOG-001 violations, verify fix loop triggers, verify final report generated — minimum 15 test cases (review_cycles: 1)
- [ ] TEST-037: `tests/test_integration_e2e.py` — test resume scenarios: interrupt during architect_running (re-run architect), interrupt during builders_running (re-run failed builders only), interrupt during quality_gate (re-run gate), interrupt during fix_pass (re-run fix) — minimum 4 test cases (review_cycles: 0)
- [ ] TEST-038: `tests/test_integration_e2e.py` — test error scenarios: all builders fail (pipeline fails gracefully with failed state), Docker unavailable (clear error message), budget exceeded mid-build (state saved, error raised), Architect produces invalid ServiceMap (rejection and retry up to max_retries) — minimum 4 test cases (review_cycles: 0)
- [ ] TEST-039: `tests/test_integration_e2e.py` — test all 40 scan codes are covered by scanners (len(ALL_SCAN_CODES) == 40), test deduplication removes duplicate violations, test Layer 4 adversarial findings are advisory-only — minimum 5 test cases (review_cycles: 0)
- [ ] TEST-040: `tests/test_integration_e2e.py` — test per-transition error handling: architect timeout retries, partial contract failure proceeds, all-builders-fail transitions to failed, partial builder failure proceeds with successful builders, integration proceeds regardless of health — minimum 5 test cases (review_cycles: 0)

---

## Status Registry

| Entity | Field | Values | DB Type | API Type |
|---|---|---|---|---|
| PipelineState | current_state | init, architect_running, architect_review, contracts_registering, builders_running, builders_complete, integrating, quality_gate, fix_pass, complete, failed | TEXT | string |
| ServiceInfo | status | pending, building, built, deploying, healthy, unhealthy, failed | TEXT | string |
| QualityGateReport | overall_verdict | passed, failed, partial, skipped | TEXT | string |
| LayerResult | verdict | passed, failed, partial, skipped | TEXT | string |
| IntegrationReport | overall_health | passed, partial, failed, unknown | TEXT | string |

## Milestone Dependency Graph

```
M1 (Shared Models, Config, State Machine, Docker Infrastructure)
├── M2 (Contract Compliance Verification)
│   └── M4 (Quality Gate)
│       └── M5 (Super Orchestrator Pipeline)
│           └── M6 (CLI + Display)
│               └── M7 (End-to-End Verification)
├── M3 (Cross-Service Integration Tests)
│   └── M4 (Quality Gate)
└── M5 (Super Orchestrator Pipeline) [also depends on M4]
```

**Critical Path:** M1 -> M2 -> M4 -> M5 -> M6 -> M7

**Parallel Opportunities:**
- M2 and M3 can run in parallel (both depend only on M1)
- No circular dependencies exist — Docker infrastructure is in M1, consumed by M5

---

## Scan Code Reference (40 Codes)

| Category | Codes | Count | Scanner |
|---|---|---|---|
| JWT Security | SEC-001..006 | 6 | SecurityScanner |
| CORS | CORS-001..003 | 3 | SecurityScanner |
| Logging | LOG-001, LOG-004, LOG-005 | 3 | ObservabilityChecker |
| Trace Propagation | TRACE-001 | 1 | ObservabilityChecker |
| Secret Detection | SEC-SECRET-001..012 | 12 | SecurityScanner |
| Docker Security | DOCKER-001..008 | 8 | DockerSecurityScanner |
| Adversarial | ADV-001..006 | 6 | AdversarialScanner |
| Health Endpoints | HEALTH-001 | 1 | ObservabilityChecker |
| **Total** | | **40** | |

---

## State Machine Transitions Reference

| # | Trigger | Source | Dest | Guard | Description |
|---|---|---|---|---|---|
| 1 | start_architect | init | architect_running | prd_loaded | Start PRD decomposition |
| 2 | architect_done | architect_running | architect_review | has_service_map | Architect produced service map |
| 3 | approve_architecture | architect_review | contracts_registering | architecture_valid | Manual/auto approval |
| 4 | contracts_ready | contracts_registering | builders_running | contracts_valid | Contracts registered |
| 5 | builders_done | builders_running | builders_complete | any_builder_success | At least one builder succeeded |
| 6 | start_integration | builders_complete | integrating | has_successful_builds | Start Docker + tests |
| 7 | integration_done | integrating | quality_gate | integration_ran | Integration phase complete |
| 8 | quality_passed | quality_gate | complete | all_gates_passed | All quality layers passed |
| 9 | quality_failed | quality_gate | fix_pass | has_violations | Blocking violations found |
| 10 | fix_done | fix_pass | quality_gate | fix_applied | Re-run quality gate |
| 11 | fail | [init, architect_running, architect_review, contracts_registering, builders_running, builders_complete, integrating, quality_gate, fix_pass] | failed | — | Any unrecoverable error (excludes complete and failed to prevent final state corruption) |
| 12 | retry_architect | architect_running | architect_running | retries_remaining | Retry on timeout |
| 13 | skip_contracts | contracts_registering | builders_running | — | Proceed without contracts |

---

## Architecture Decision

### Technology Stack

- Backend: Python 3.12+ with asyncio
- State Machine: transitions 0.9.2+ (AsyncMachine)
- CLI: Typer 0.21.0+ with Rich 13.0+
- API Testing: Schemathesis 4.x + pact-python 3.2.1+
- Docker: Docker Compose v2 + Traefik v3.6
- Security: detect-secrets 1.5+ + PyJWT 2.8+
- Observability: opentelemetry-api 1.25+
- HTTP: httpx 0.28.x+ (async), FastAPI 0.129.0+ (health endpoints)
- Testing: pytest 8.x+ with pytest-asyncio 0.24.x+
- Docker: testcontainers[compose] 4.x, docker-py 7.x+

### File Structure

```
super-team/
  src/
    super_orchestrator/  # Pipeline orchestration + state machine + CLI (~3,850 LOC)
    integrator/          # Docker orchestration + contract testing + cross-service (~6,100 LOC)
    quality_gate/        # 4-layer quality verification engine (~5,500 LOC)
    build3_shared/       # Models, protocols, constants, utilities (~950 LOC) — named build3_shared to avoid namespace collision with Build 1's src/shared/
  tests/                 # Unit + integration tests (~6,400 LOC)
  docker/                # Docker Compose + Traefik configuration
```

### Integration Roadmap

#### Entry Points

| Entry Point | File | Purpose |
|---|---|---|
| Super Orchestrator CLI | src/super_orchestrator/cli.py | Typer app with 8 commands |
| Pipeline Engine | src/super_orchestrator/pipeline.py | Async phase execution functions |
| Quality Gate | src/quality_gate/gate_engine.py | 4-layer sequential gate engine |
| Docker Orchestrator | src/integrator/docker_orchestrator.py | Docker Compose lifecycle |
| Contract Verifier | src/integrator/contract_compliance.py | Schemathesis + Pact verification |

#### Wiring Map

| ID | Source | Target | Mechanism | Priority |
|---|---|---|---|---|
| WIRE-001 | src/build3_shared/models.py | All 3 packages | build3_shared import | HIGH |
| WIRE-002 | src/super_orchestrator/state_machine.py | transitions library | AsyncMachine import | HIGH |
| WIRE-003 | src/super_orchestrator/state.py | src/build3_shared/utils.py | atomic_write_json import | HIGH |
| WIRE-004 | src/super_orchestrator/shutdown.py | src/super_orchestrator/state.py | set_state() reference | HIGH |
| WIRE-005 | src/integrator/compose_generator.py | src/integrator/traefik_config.py | generate_labels() call | HIGH |
| WIRE-006 | src/integrator/docker_orchestrator.py | src/integrator/service_discovery.py | health check delegation | HIGH |
| WIRE-007 | src/integrator/contract_compliance.py | schemathesis_runner + pact_manager | internal composition | HIGH |
| WIRE-008 | src/integrator/fix_loop.py | agent_team subprocess | subprocess + FIX_INSTRUCTIONS.md | HIGH |
| WIRE-009 | src/integrator/cross_service_test_generator.py | contract registry path | shared path reference | HIGH |
| WIRE-010 | src/integrator/cross_service_test_runner.py | DockerOrchestrator URLs | service URL mapping | HIGH |
| WIRE-011 | src/quality_gate/gate_engine.py | 4 layer scanners | internal composition | HIGH |
| WIRE-012 | src/quality_gate/layer2_contract_compliance.py | IntegrationReport | M2 output consumption | HIGH |
| WIRE-013 | src/quality_gate/layer3_system_level.py | security + observability + docker scanners | scanner instantiation | HIGH |
| WIRE-014 | src/quality_gate/gate_engine.py | scan_aggregator.py | aggregate() call | HIGH |
| WIRE-015 | src/super_orchestrator/pipeline.py | Build 1 Architect MCP | MCP stdio transport | HIGH |
| WIRE-016 | src/super_orchestrator/pipeline.py | Build 2 agent-team | subprocess / ExecutionBackend | HIGH |
| WIRE-017 | src/super_orchestrator/pipeline.py | M1+M2+M3 modules | phase composition | HIGH |
| WIRE-018 | src/super_orchestrator/pipeline.py | GracefulShutdown | should_stop check | HIGH |
| WIRE-019 | src/super_orchestrator/pipeline.py | integrator/report.py | INTEGRATION_REPORT.md generation | HIGH |
| WIRE-020 | src/super_orchestrator/pipeline.py | quality_gate/report.py | QUALITY_GATE_REPORT.md generation | HIGH |
| WIRE-021 | src/super_orchestrator/cli.py | config.yaml | YAML config loading | HIGH |
| WIRE-022 | src/super_orchestrator/cli.py (run) | pipeline.py | execute_pipeline() call | HIGH |

#### Wiring Anti-Patterns

- Never call asyncio.run() more than once per CLI invocation — all async code must be awaited under a single event loop. Use `asyncio.run(_async_impl())` in each Typer command, not `asyncio.run()` inside already-running async code
- Never import Build 1/Build 2 at module level — use lazy imports inside function bodies with ImportError handling
- Never share mutable state between Builder subprocesses — each builder runs isolated
- Never hardcode Docker service URLs — use Docker Compose service names or ServiceDiscovery
- Never skip state persistence before phase transitions — resume depends on saved state
- Never bypass the quality gate layer sequence — L1 must pass before L2, L2 before L3

#### Initialization Order

1. Load SuperOrchestratorConfig from config.yaml
2. Initialize or load PipelineState from .super-orchestrator/
3. Install GracefulShutdown signal handler
4. Create PipelineCostTracker (with optional budget_limit)
5. Create AsyncMachine state machine (initial state from PipelineState or "init")
6. Enter pipeline loop (execute_pipeline)

## Review Log

| Cycle | Agent | Item | Verdict | Issues |
|---|---|---|---|---|
