# Build 3 PRD — Technical Accuracy Review

**Reviewer:** Technical Accuracy Reviewer
**Date:** 2026-02-14
**Scope:** Every technical claim, API call, library version, configuration value, and architecture decision in BUILD3_PRD.md verified against the 4 research documents.

**Reference Documents:**
- BUILD3_TECH_DOCKER_TRAEFIK.md (Docker Compose v2 + Traefik v3.6)
- BUILD3_TECH_TESTING.md (Schemathesis, Pact, Testcontainers, httpx, pytest-asyncio)
- BUILD3_TECH_SECURITY_OBS.md (Security scanning, observability, adversarial patterns)
- BUILD3_TECH_STATE_CLI.md (transitions, Typer, Rich, async orchestration)

---

## 1. Library Versions

| Library | PRD Claim | Research Confirmation | Verdict |
|---------|-----------|----------------------|---------|
| Python | 3.12+ | Confirmed (STATE_CLI.md, all docs) | CORRECT |
| transitions | 0.9.2+ | Confirmed (STATE_CLI.md S1.1) | CORRECT |
| typer[all] | 0.21.0+ | Confirmed (STATE_CLI.md S2.1) | CORRECT |
| rich | 13.0+ | Confirmed (STATE_CLI.md S3.1) | CORRECT |
| FastAPI | 0.129.0+ | Not explicitly versioned in research docs; reasonable version | CORRECT (no contradiction) |
| uvicorn | 0.34.0+ | Not explicitly versioned in research docs; reasonable version | CORRECT (no contradiction) |
| schemathesis | 4.x | Confirmed (TESTING.md S1.1) | CORRECT |
| pact-python | 3.2.1+ | Confirmed (TESTING.md S2.1) | CORRECT |
| testcontainers[compose] | 4.x | Confirmed (TESTING.md S3.1) | CORRECT |
| httpx | 0.28.x+ | Confirmed (TESTING.md S4.1) | CORRECT |
| pytest | 8.x+ | Confirmed (TESTING.md S5.1) | CORRECT |
| pytest-asyncio | 0.24.x+ | Confirmed (TESTING.md S5.1) | CORRECT |
| detect-secrets | 1.5+ | Confirmed (SECURITY_OBS.md S1.1) | CORRECT |
| PyJWT | 2.8+ | Confirmed (SECURITY_OBS.md S2.1) | CORRECT |
| opentelemetry-api/sdk | 1.25+ | Confirmed (SECURITY_OBS.md S5.1) | CORRECT |
| Traefik | v3.6 | Confirmed (DOCKER_TRAEFIK.md S2.1) | CORRECT |
| Docker Compose | v2 | Confirmed (DOCKER_TRAEFIK.md S1.1) | CORRECT |
| PyYAML | 6.x+ | Not version-confirmed in research; standard lib | CORRECT (no contradiction) |
| pydantic | 2.x+ | Not version-confirmed in research; standard lib | CORRECT (no contradiction) |
| docker-py | 7.x+ | Not version-confirmed in research; reasonable version | CORRECT (no contradiction) |
| mcp | >=1.25,<2 | Not version-confirmed in research; project-internal | CORRECT (no contradiction) |

**Library Versions Summary:** 21/21 CORRECT (0 INCORRECT)

---

## 2. API Correctness

### 2.1 Docker Compose v2

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `docker compose` (no hyphen) v2 syntax | TECH-026 | DOCKER_TRAEFIK.md S1.1: "docker compose (v2, no hyphen)" | CORRECT |
| `depends_on` with `service_healthy` condition | REQ-046, TECH-025 | DOCKER_TRAEFIK.md S1.1: `depends_on: {service: {condition: service_healthy}}` | CORRECT |
| `healthcheck` with `test`, `interval`, `timeout`, `retries`, `start_period` | REQ-046 | DOCKER_TRAEFIK.md S1.2: confirms all healthcheck fields | CORRECT |
| `docker compose ps --format json` | REQ-048 | DOCKER_TRAEFIK.md S1.3: confirms `--format json` flag | CORRECT |
| `docker compose up -d` | REQ-048 | DOCKER_TRAEFIK.md S1.1: standard command | CORRECT |
| `docker compose down` | REQ-048 | DOCKER_TRAEFIK.md S1.1: standard command | CORRECT |
| `docker compose port {service} {port}` | SVC-019 | DOCKER_TRAEFIK.md S1.3: confirms port mapping command | CORRECT |
| `pg_isready` healthcheck for PostgreSQL | REQ-046 | DOCKER_TRAEFIK.md S1.2: `pg_isready -U $$POSTGRES_USER` | CORRECT |
| `redis-cli ping` healthcheck for Redis | REQ-046 | DOCKER_TRAEFIK.md S1.2: `redis-cli ping` | CORRECT |
| Named volumes syntax | REQ-046 | DOCKER_TRAEFIK.md S1.4: confirms named volumes | CORRECT |

**Docker Compose v2 Summary:** 10/10 CORRECT

### 2.2 Traefik v3

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| Docker provider auto-discovery | REQ-046, REQ-047 | DOCKER_TRAEFIK.md S2.1: `providers.docker` with `exposedByDefault: false` | CORRECT |
| `traefik.enable=true` label | REQ-047 | DOCKER_TRAEFIK.md S2.1: confirms label | CORRECT |
| `traefik.http.routers.{name}.rule=PathPrefix(...)` | REQ-047, TECH-028 | DOCKER_TRAEFIK.md S2.2: confirms router rule labels | CORRECT |
| PathPrefix backtick syntax: `` PathPrefix(`/path`) `` | TECH-028 | DOCKER_TRAEFIK.md S2.2: "Traefik v3 uses backtick syntax" | CORRECT |
| `traefik.http.services.{name}.loadbalancer.server.port` | REQ-047 | DOCKER_TRAEFIK.md S2.3: confirms service port label | CORRECT |
| StripPrefix middleware | REQ-047 | DOCKER_TRAEFIK.md S2.4.1: confirms StripPrefix middleware labels | CORRECT |
| `traefik healthcheck --ping` | REQ-046 | DOCKER_TRAEFIK.md S2.8: confirms `traefik healthcheck --ping` as healthcheck test | CORRECT |
| `--api.dashboard=false` | SEC-003 | DOCKER_TRAEFIK.md S2.7: confirms dashboard disable flag | CORRECT |
| Docker socket mount `:ro` | SEC-004 | DOCKER_TRAEFIK.md S2.8: `/var/run/docker.sock:/var/run/docker.sock:ro` | CORRECT |
| Ports 80 and 8080 | REQ-046 | DOCKER_TRAEFIK.md S2.8: ports 80:80 and 8080:8080 | CORRECT |

**Traefik v3 Summary:** 10/10 CORRECT

### 2.3 Schemathesis

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `schemathesis.openapi.from_url(openapi_url)` | REQ-012, SVC-001 | TESTING.md S1.2: confirms `schemathesis.openapi.from_url()` | CORRECT |
| `schemathesis.openapi.from_path()` for static spec | TECH-008 | TESTING.md S1.2: confirms `from_path()` | CORRECT |
| `@schema.parametrize()` decorator | REQ-012 | TESTING.md S1.3: confirms `@schema.parametrize()` | CORRECT |
| `case.call_and_validate(base_url=base_url)` | REQ-012, SVC-001 | TESTING.md S1.5: confirms `case.call_and_validate()` | CORRECT |
| `from_dict()` "skips $ref resolution" | TECH-008 | TESTING.md S1.2: `from_dict()` exists as valid loader; $ref skip claim not confirmed | **INCORRECT (LOW)** |
| `schemathesis.failures.FailureGroup` | TECH-009 | TESTING.md S6.1: actual class is `schemathesis.exceptions.CheckFailed` | **INCORRECT (HIGH)** |

**Schemathesis Summary:** 4/6 CORRECT, 2 INCORRECT

**TECH-008 Detail:** The PRD states "never from_dict() as it skips $ref resolution." The research document (TESTING.md S1.2) lists `from_dict()` as a valid loader alongside `from_url()` and `from_path()` but does NOT confirm or deny $ref resolution behavior. The claim about $ref skipping is unverified. **Severity: LOW** — the guidance to prefer `from_url()`/`from_path()` is reasonable regardless.

**TECH-009 Detail:** The PRD claims `case.call_and_validate()` raises `schemathesis.failures.FailureGroup`. The research document (TESTING.md S6.1) explicitly shows the exception class is `schemathesis.exceptions.CheckFailed`, not `schemathesis.failures.FailureGroup`. The module path and class name are both wrong. **Severity: HIGH** — code importing from the wrong module will crash at runtime with ImportError.

### 2.4 Pact

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `pact.Verifier()` | TECH-010, REQ-013 | TESTING.md S2.3: confirms `Verifier()` class | CORRECT |
| `.set_info("Provider", url=provider_url)` | TECH-010 | TESTING.md S2.3: confirms `set_info(name, url=url)` | CORRECT |
| `.add_source(pact_file)` | TECH-010 | TESTING.md S2.3: confirms `add_source()` | CORRECT |
| `.verify()` returns `VerifyResult` with `success` bool and `output` string | TECH-010 | TESTING.md S2.3: `verify() -> None`, raises on failure | **INCORRECT (HIGH)** |
| PACT-001 for interaction failures | REQ-013 | Consistent with PRD-internal code system | CORRECT |
| PACT-002 for state setup failures | REQ-013 | Consistent with PRD-internal code system | CORRECT |
| Pact V4 spec support | Line 17 | TESTING.md S2.1: confirms V4 spec with Rust FFI | CORRECT |
| `upon_receiving()`, `with_request()`, `will_respond_with()` consumer API | Implicit in SVC-002 | TESTING.md S2.2: confirms consumer DSL | CORRECT |

**Pact Summary:** 7/8 CORRECT, 1 INCORRECT

**TECH-010 Detail:** The PRD states Pact Verifier returns a `VerifyResult` with `success` bool and `output` string. The research document (TESTING.md S2.3) clearly shows `verify() -> None` — the method returns nothing on success and raises an exception on failure. There is no `VerifyResult` class. Code expecting a return value will need to use try/except instead. **Severity: HIGH** — incorrect return type will cause AttributeError at runtime.

### 2.5 Testcontainers

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `testcontainers[compose] 4.x` | Line 18 | TESTING.md S3.1: confirms package name and version | CORRECT |
| DockerCompose integration | Implicit in test setup | TESTING.md S3.5: confirms `DockerCompose` class with `waiting_for()` | CORRECT |

**Testcontainers Summary:** 2/2 CORRECT

### 2.6 transitions (State Machine)

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `AsyncMachine` from `transitions.extensions.asyncio` | TECH-005, REQ-008 | STATE_CLI.md S1.1: confirms import path | CORRECT |
| `auto_transitions=False` | REQ-008 | STATE_CLI.md S1.1: confirms parameter | CORRECT |
| `send_event=True` | REQ-008 | STATE_CLI.md S1.1: confirms parameter | CORRECT |
| `queued=True` | REQ-008 | STATE_CLI.md S1.1: confirms parameter | CORRECT |
| 11 states | REQ-008 | STATE_CLI.md S1.2: confirms 11 states (init through failed) | CORRECT |
| State names: init, architect_running, architect_review, contracts_registering, builders_running, builders_complete, integrating, quality_gate, fix_pass, complete, failed | REQ-008, Status Registry | STATE_CLI.md S1.2: all 11 state names match | CORRECT |
| 13 transitions | REQ-008 | STATE_CLI.md S1.3: confirms 13 transitions in Full Transition Table | CORRECT |
| Guard conditions on transitions | REQ-008 | STATE_CLI.md S1.1: `conditions` field in transition dicts | CORRECT |
| `on_enter` callbacks for logging | REQ-008 | STATE_CLI.md S1.1: confirms `on_enter_*` callbacks | CORRECT |
| RESUME_TRIGGERS mapping | REQ-008, REQ-044 | STATE_CLI.md S1.4: confirms resume trigger mapping | CORRECT |
| `State` import from `transitions` | WIRE-002 | STATE_CLI.md S1.1: `from transitions import State` | CORRECT |

**transitions Summary:** 11/11 CORRECT

### 2.7 Typer

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `typer.Typer(name=..., help=...)` | TECH-024 | STATE_CLI.md S2.1: confirms Typer constructor | CORRECT |
| `rich_markup_mode="rich"` | TECH-024 | STATE_CLI.md S2.1: confirms parameter | CORRECT |
| `@app.command()` decorator | REQ-040 | STATE_CLI.md S2.2: confirms command decorator | CORRECT |
| `typer.Argument()` | Implicit in REQ-040 | STATE_CLI.md S2.2: confirms Argument | CORRECT |
| `typer.Option()` | Implicit in REQ-040 | STATE_CLI.md S2.2: confirms Option | CORRECT |
| 8 CLI commands (init, plan, build, integrate, verify, run, status, resume) | REQ-040 | PRD-internal design; consistent with Typer patterns | CORRECT |
| `typer.testing.CliRunner` for tests | TEST-018 | STATE_CLI.md S2.4: confirms CliRunner | CORRECT |

**Typer Summary:** 7/7 CORRECT

### 2.8 Rich

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `Progress()` with `SpinnerColumn`, `BarColumn`, `TimeElapsedColumn` | TECH-029 | STATE_CLI.md S3.2: confirms Progress columns | CORRECT |
| `TextColumn("[progress.description]{task.description}")` | TECH-029 | STATE_CLI.md S3.2: confirms TextColumn format | CORRECT |
| `Table()` | REQ-045 | STATE_CLI.md S3.3: confirms Table | CORRECT |
| `Panel()` | REQ-045 | STATE_CLI.md S3.4: confirms Panel | CORRECT |
| `Live()` | REQ-045 | STATE_CLI.md S3.5: confirms Live display | CORRECT |

**Rich Summary:** 5/5 CORRECT

### 2.9 detect-secrets

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `detect-secrets 1.5+` with Python API | Line 21 | SECURITY_OBS.md S1.1: confirms library and version | CORRECT |
| `SecretsCollection` | Implicit in REQ-024 | SECURITY_OBS.md S1.2: confirms `SecretsCollection` | CORRECT |
| `default_settings()` | Implicit | SECURITY_OBS.md S1.2: confirms `default_settings()` | CORRECT |
| `transient_settings()` | Line 21 | SECURITY_OBS.md S1.2: confirms `transient_settings()` | CORRECT |
| `scan_file()` | Implicit in REQ-024 | SECURITY_OBS.md S1.2: confirms `scan_file()` | CORRECT |

**detect-secrets Summary:** 5/5 CORRECT

---

## 3. Configuration Values

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| `asyncio_mode = "auto"` for pytest-asyncio | Line 20 | TESTING.md S5.2: confirms `asyncio_mode = "auto"` | CORRECT |
| `timeout=30.0` for httpx.AsyncClient | TECH-011, TECH-014 | TESTING.md S4.2: confirms timeout parameter | CORRECT |
| `follow_redirects=True` for cross-service calls | TECH-014 | TESTING.md S4.2: confirms parameter | CORRECT |
| `providers.docker` in traefik.yml | REQ-047 | DOCKER_TRAEFIK.md S2.1: confirms provider config | CORRECT |
| `entrypoints.web` in traefik.yml | REQ-047 | DOCKER_TRAEFIK.md S2.1: confirms entrypoint config | CORRECT |
| `exposedByDefault: false` for Docker provider | Implicit in REQ-047 | DOCKER_TRAEFIK.md S2.1: confirms default | CORRECT |
| Blocking severity = "error" default | REQ-005, REQ-021 | PRD-internal; consistent with quality gate design | CORRECT |
| `max_fix_retries = 3` default | REQ-005 | PRD-internal; reasonable default | CORRECT |
| `DEFAULT_MAX_CONCURRENT_BUILDERS = 3` | REQ-003 | PRD-internal; reasonable default | CORRECT |
| `DEFAULT_BUILDER_TIMEOUT = 1800` (30 min) | REQ-003 | PRD-internal; reasonable default | CORRECT |
| Phase timeouts (architect: 900s, builders: 3600s, etc.) | REQ-003 | PRD-internal; reasonable timeouts | CORRECT |
| Image `postgres:16-alpine` | REQ-046 | DOCKER_TRAEFIK.md S1.2: confirms postgres alpine image | CORRECT |
| Image `redis:7-alpine` | REQ-046 | DOCKER_TRAEFIK.md S1.2: confirms redis alpine image | CORRECT |
| Image `traefik:v3.6` | REQ-005, REQ-046 | DOCKER_TRAEFIK.md S2.8: confirms traefik v3.6 image | CORRECT |

**Configuration Values Summary:** 14/14 CORRECT

---

## 4. Architecture Consistency

### 4.1 State Machine Design

| Claim | Research Reference | Verdict |
|-------|-------------------|---------|
| 11 states matching Status Registry | STATE_CLI.md S1.2 | CORRECT |
| 13 transitions with guards and callbacks | STATE_CLI.md S1.3 | CORRECT |
| Sequential quality gate gating (L1->L2->L3->L4) | SECURITY_OBS.md S9: confirms 4-layer sequence | CORRECT |
| Layer 4 advisory-only (never blocking) | SECURITY_OBS.md S8.1: confirms advisory nature | CORRECT |
| Fix loop (quality_failed -> fix_pass -> fix_done -> quality_gate) | STATE_CLI.md S1.3: confirms fix loop transitions | CORRECT |
| `asyncio.run()` called exactly once | TECH-023, STATE_CLI.md S4.1 | CORRECT |
| GracefulShutdown with signal handlers | STATE_CLI.md S4.2 | CORRECT |
| Windows `signal.signal()` fallback | TECH-006, STATE_CLI.md S4.2 | CORRECT |

**State Machine Summary:** 8/8 CORRECT

### 4.2 Scan Code Count

| Claim | Location | Research Reference | Verdict |
|-------|----------|-------------------|---------|
| "30 quality gate scan codes" | REQ-003, M4 description (line 269), REQ-060, TEST-024 | SECURITY_OBS.md S9: states "30 scan codes across 7 categories" BUT actual enumeration yields 40 | **INCORRECT (MEDIUM)** |

**Detail:** The PRD references "30 quality gate scan codes" in multiple places (REQ-003, M4 description, REQ-060, TEST-024). When enumerating the actual scan codes defined in the PRD and research:
- SEC-001..006 = 6 codes
- CORS-001..003 = 3 codes
- LOG-001, LOG-004, LOG-005 = 3 codes
- TRACE-001 = 1 code
- SEC-SECRET-001..012 = 12 codes
- DOCKER-001..008 = 8 codes
- ADV-001..006 = 6 codes
- HEALTH-001 = 1 code
- **Total = 40 codes**

Note: The research document itself (SECURITY_OBS.md S9) also claims "30" but the enumeration shows 40. The PRD inherited this inconsistency from the research doc. The code constant `ALL_SCAN_CODES` will have 40 entries, not 30. **Severity: MEDIUM** — the constant definition in REQ-003 enumerates all codes correctly; only the count claim is wrong. Tests checking `len(ALL_SCAN_CODES) == 30` would fail.

### 4.3 Milestone Dependencies / Cross-References

| Claim | Issue | Verdict |
|-------|-------|---------|
| M5 REQ-036 references ComposeGenerator (M6) and DockerOrchestrator (M6) | REQ-036 step (1) uses `ComposeGenerator` and step (2) uses `DockerOrchestrator`, both defined in M6. But M6 depends on M5. | **INCORRECT (HIGH)** |
| M2+M3 parallel execution (both depend only on M1) | M3 description says "can run in parallel with M2" | CORRECT |
| M4 depends on M2+M3 | M4 description confirms M2+M3 dependency | CORRECT |
| M5 depends on M4 | M5 description confirms M4 dependency | CORRECT |
| M6 depends on M5 | M6 description confirms M5 dependency | CORRECT |
| M7 depends on M5+M6 | M7 description confirms M5+M6 dependency | CORRECT |
| WIRE-008: CrossServiceTestRunner uses DockerOrchestrator URLs (M6) | M3 test runner needs M6 URLs at runtime (not build time) | CORRECT (runtime dependency, not build dependency) |
| WIRE-014: run_integration_phase composes M2+M3+M6 | Pipeline function in M5 composes modules from M2, M3, M6 | Consistent with REQ-036 issue above |

**Detail for M5->M6 Circular Dependency:**
REQ-036 (Milestone 5) says `run_integration_phase` must "(1) generate docker-compose.yml from builder outputs using ComposeGenerator (M6), (2) start services via DockerOrchestrator." Both `ComposeGenerator` (REQ-046) and `DockerOrchestrator` (REQ-048) are defined in Milestone 6. But M6 depends on M5 (M6's dependency field says "milestone-5"). This creates a circular dependency:
- M5 needs ComposeGenerator + DockerOrchestrator (defined in M6)
- M6 depends on M5

**Resolution options:**
1. Move ComposeGenerator and DockerOrchestrator to M3 or a new M3.5 milestone
2. Change M5's dependency to M4 only and make M6 parallel with M5
3. Split run_integration_phase: docker infra in M6, pipeline logic in M5 with M6 dependency

**Severity: HIGH** — this blocks correct milestone ordering during build. The build system cannot satisfy M5 before M6 if M5 requires M6 artifacts.

### 4.4 Project Structure

| Claim | Verdict |
|-------|---------|
| 4 packages: super_orchestrator, integrator, quality_gate, shared | CORRECT — consistent across PRD |
| File assignments match requirement locations | CORRECT — each REQ targets a specific file |
| Test file assignments match test requirements | CORRECT — TEST-xxx reference correct test files |
| docker/ directory structure (compose files + traefik/) | CORRECT — consistent with DOCKER_TRAEFIK.md |

**Project Structure Summary:** 4/4 CORRECT

### 4.5 Wiring Consistency

| Wiring | Claim | Verdict |
|--------|-------|---------|
| WIRE-001: shared/models.py importable by all packages | Consistent | CORRECT |
| WIRE-002: state_machine.py imports from transitions | Consistent with TECH-005 | CORRECT |
| WIRE-003: state.py imports atomic_write_json | Consistent with REQ-004 | CORRECT |
| WIRE-004: shutdown.py uses set_state() not constructor | Consistent with REQ-010 | CORRECT |
| WIRE-005: ContractComplianceVerifier composes internally | Consistent with REQ-014 | CORRECT |
| WIRE-006: fix_loop.py writes FIX_INSTRUCTIONS.md + subprocess | Consistent with REQ-015 | CORRECT |
| WIRE-007: CrossServiceTestGenerator uses contract registry | Consistent with REQ-017 | CORRECT |
| WIRE-008: CrossServiceTestRunner uses DockerOrchestrator URLs | Runtime dependency (valid) | CORRECT |
| WIRE-009: QualityGateEngine composes all 4 layers | Consistent with REQ-021 | CORRECT |
| WIRE-010: Layer2Scanner consumes IntegrationReport | Consistent with REQ-023 | CORRECT |
| WIRE-011: Layer3Scanner composes 3 scanners | Consistent with REQ-027 | CORRECT |
| WIRE-012: run_architect_phase uses MCP stdio | Consistent with REQ-032 | CORRECT |
| WIRE-013: run_parallel_builders uses subprocess | Consistent with REQ-034 | CORRECT |
| WIRE-014: run_integration_phase composes M2+M3+M6 | See M5->M6 dependency issue | CORRECT (intent) |
| WIRE-015: execute_pipeline checks should_stop | Consistent with REQ-039 | CORRECT |
| WIRE-016: CLI loads config from config.yaml | Consistent with REQ-040 | CORRECT |
| WIRE-017: run command wires all components | Consistent with REQ-042 | CORRECT |
| WIRE-018: ComposeGenerator called by integration phase | See M5->M6 dependency issue | CORRECT (intent) |
| WIRE-019: DockerOrchestrator in finally block | Consistent with REQ-048 | CORRECT |

**Wiring Summary:** 19/19 CORRECT (intent-wise; M5-M6 circular dependency is a milestone ordering issue, not a wiring correctness issue)

---

## 5. Security & Observability Scan Codes

| Category | Codes in PRD | Codes in Research | Match |
|----------|-------------|-------------------|-------|
| JWT Security | SEC-001..006 | SECURITY_OBS.md S2.2: SEC-001..006 | CORRECT |
| CORS | CORS-001..003 | SECURITY_OBS.md S3.1: CORS-001..003 | CORRECT |
| Logging | LOG-001, LOG-004, LOG-005 | SECURITY_OBS.md S4.1: LOG-001, LOG-004, LOG-005 | CORRECT |
| Trace Propagation | TRACE-001 | SECURITY_OBS.md S5.2: TRACE-001 | CORRECT |
| Secret Detection | SEC-SECRET-001..012 | SECURITY_OBS.md S1.3: SEC-SECRET-001..012 | CORRECT |
| Docker Security | DOCKER-001..008 | SECURITY_OBS.md S6.1: DOCKER-001..008 | CORRECT |
| Adversarial | ADV-001..006 | SECURITY_OBS.md S8.1: ADV-001..006 | CORRECT |
| Health | HEALTH-001 | SECURITY_OBS.md S4.2: HEALTH-001 | CORRECT |

**Scan Code Definitions Summary:** 8/8 categories CORRECT (all individual codes match)

---

## 6. SVC Wiring Table Accuracy

| SVC-ID | API Call Claim | Verified Against Research | Verdict |
|--------|---------------|--------------------------|---------|
| SVC-001 | schemathesis.openapi.from_url() + case.call_and_validate() | TESTING.md S1.2, S1.5 | CORRECT |
| SVC-002 | pact.Verifier().set_info().add_source().verify() | TESTING.md S2.3 (verify returns None, not VerifyResult) | **INCORRECT** (see TECH-010) |
| SVC-003 | subprocess python -m agent_team --fix | PRD-internal | CORRECT |
| SVC-004 | MCP Codebase Intelligence -> get_service_interface | PRD-internal (Build 1 reference) | CORRECT |
| SVC-005 | MCP Codebase Intelligence -> find_dependencies | PRD-internal (Build 1 reference) | CORRECT |
| SVC-006 | MCP Codebase Intelligence -> check_dead_code | PRD-internal (Build 1 reference) | CORRECT |
| SVC-007 | Layer2Scanner.evaluate(IntegrationReport) | PRD-internal | CORRECT |
| SVC-008 | MCP Architect -> decompose | PRD-internal (Build 1 reference) | CORRECT |
| SVC-009 | MCP Contract Engine -> create_contract | PRD-internal (Build 1 reference) | CORRECT |
| SVC-010 | MCP Contract Engine -> validate_spec | PRD-internal (Build 1 reference) | CORRECT |
| SVC-011 | MCP Contract Engine -> list_contracts | PRD-internal (Build 1 reference) | CORRECT |
| SVC-012 | subprocess python -m agent_team | PRD-internal (Build 2 reference) | CORRECT |
| SVC-013 | QualityGateEngine.run_all_layers() | PRD-internal | CORRECT |
| SVC-014 | subprocess python -m agent_team --fix | PRD-internal | CORRECT |
| SVC-015 | docker compose up -d | DOCKER_TRAEFIK.md S1.1 | CORRECT |
| SVC-016 | docker compose down | DOCKER_TRAEFIK.md S1.1 | CORRECT |
| SVC-017 | docker compose ps --format json | DOCKER_TRAEFIK.md S1.3 | CORRECT |
| SVC-018 | HTTP GET {url}/health | Standard health check | CORRECT |
| SVC-019 | docker compose port | DOCKER_TRAEFIK.md S1.3 | CORRECT |

**SVC Wiring Summary:** 18/19 CORRECT, 1 INCORRECT (SVC-002 inherits TECH-010 Pact return type error)

---

## 7. Summary

### Total Counts

| Category | Checked | CORRECT | INCORRECT |
|----------|---------|---------|-----------|
| Library Versions | 21 | 21 | 0 |
| Docker Compose v2 API | 10 | 10 | 0 |
| Traefik v3 API | 10 | 10 | 0 |
| Schemathesis API | 6 | 4 | 2 |
| Pact API | 8 | 7 | 1 |
| Testcontainers API | 2 | 2 | 0 |
| transitions API | 11 | 11 | 0 |
| Typer API | 7 | 7 | 0 |
| Rich API | 5 | 5 | 0 |
| detect-secrets API | 5 | 5 | 0 |
| Configuration Values | 14 | 14 | 0 |
| Architecture / State Machine | 8 | 8 | 0 |
| Scan Code Count | 1 | 0 | 1 |
| Milestone Dependencies | 8 | 7 | 1 |
| Project Structure | 4 | 4 | 0 |
| Wiring | 19 | 19 | 0 |
| SVC Table | 19 | 18 | 1 |
| **TOTAL** | **158** | **152** | **6** |

**Accuracy Rate: 96.2% (152/158)**

### All Inaccuracies Ranked by Severity

| # | Severity | Location | Issue | Fix Required |
|---|----------|----------|-------|-------------|
| 1 | **HIGH** | TECH-009 | Schemathesis exception class is `schemathesis.exceptions.CheckFailed`, NOT `schemathesis.failures.FailureGroup`. Wrong module AND wrong class name. | Change to `schemathesis.exceptions.CheckFailed` |
| 2 | **HIGH** | TECH-010 / SVC-002 | Pact `Verifier.verify()` returns `None` and raises on failure. There is NO `VerifyResult` class with `success` bool and `output` string. | Change to try/except pattern: `try: verifier.verify()` succeeds means pass, exception means fail |
| 3 | **HIGH** | REQ-036 / M5-M6 | Circular milestone dependency: REQ-036 (M5) uses `ComposeGenerator` and `DockerOrchestrator` from M6, but M6 depends on M5. Build order cannot be satisfied. | Move ComposeGenerator + DockerOrchestrator to an earlier milestone (e.g., M3), OR change M6 to not depend on M5, OR split the integration phase |
| 4 | **MEDIUM** | REQ-003 / REQ-060 / TEST-024 | PRD claims "30 quality gate scan codes" but actual enumeration (SEC 6 + CORS 3 + LOG 3 + TRACE 1 + SECRET 12 + DOCKER 8 + ADV 6 + HEALTH 1) = 40. Research doc has same error. | Change "30" to "40" in REQ-003, M4 description, REQ-060, TEST-024 |
| 5 | **LOW** | TECH-008 | Claim that `from_dict()` "skips $ref resolution" is unverified in research docs. `from_dict()` exists as a valid loader. | Either remove the $ref claim or verify it independently. The guidance to prefer `from_url()`/`from_path()` for live/static testing is still valid. |
| 6 | **LOW** | SVC-002 | SVC-002 Response DTO says `list[ContractViolation]` which is the PRD's internal mapping — but the underlying Pact API returns None/raises, so the conversion logic description in TECH-010 is the actual issue (counted above). | Already covered by TECH-010 fix |

### Recommendations

1. **TECH-009 + TECH-010 (both HIGH):** These are the most critical findings. Code written to these specs will crash at import time (TECH-009) or runtime (TECH-010). Fix before any milestone begins coding.

2. **M5-M6 Circular Dependency (HIGH):** The recommended fix is to move `ComposeGenerator` (REQ-046) and `DockerOrchestrator` (REQ-048) to Milestone 3 (or a new Milestone 3.5), since M3 has no downstream dependencies from M5. This preserves the M5 pipeline.py consuming these modules without a circular dependency.

3. **Scan Code Count (MEDIUM):** Update the count from 30 to 40 in all locations. This is a documentation-only fix but will prevent test assertion failures.

4. **TECH-008 (LOW):** Minor wording issue. Can be deferred.
