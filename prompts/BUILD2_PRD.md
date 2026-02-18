# Build 2 PRD: Builder Fleet Upgrade + Agent Teams Integration

Upgrade the existing agent-team v14.0 (28,749 LOC, 5,410+ passing tests) into a contract-aware, MCP-integrated Builder Fleet with optional Claude Code Agent Teams coordination. Three upgrade axes: (1) Agent Teams abstraction layer replacing within-Builder subprocess orchestration, (2) Contract Engine MCP integration for live contract validation, (3) Codebase Intelligence MCP integration replacing static CODEBASE_MAP.md. All upgrades are backward-compatible — disabling Build 2 features produces identical v14.0 behavior.

Each requirement includes `(review_cycles: N)` tracked by the build system. Agents must preserve this suffix.

## Technology Stack

- **Language:** Python 3.12+ (existing codebase)
- **Async Runtime:** asyncio (existing) + MCP Python SDK (anyio-compatible)
- **MCP Client:** mcp>=1.25,<2 — `stdio_client()` + `ClientSession` + `call_tool()` pattern
- **Agent Teams:** Claude Code experimental agent teams — `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **Hooks:** Claude Code hooks system — command, prompt, agent hook types
- **Testing:** pytest (existing infrastructure, 5,410+ tests)
- **Config:** YAML with dataclass parsing via `_dict_to_config()` returning `tuple[AgentTeamConfig, set[str]]`

## Project Structure (New/Modified Files)

```
src/agent_team/
  agent_teams_backend.py    NEW  ~550 lines  Agent Teams abstraction layer
  contract_client.py        NEW  ~350 lines  Contract Engine MCP client
  codebase_client.py        NEW  ~300 lines  Codebase Intelligence MCP client
  hooks_manager.py          NEW  ~250 lines  Hook config generation
  claude_md_generator.py    NEW  ~350 lines  CLAUDE.md generation for teammates
  contract_scanner.py       NEW  ~300 lines  CONTRACT-001..004 static scans
  mcp_clients.py             NEW  ~200 lines  MCP session management + ArchitectClient
  cli.py                    MOD  +300 lines  Pipeline integration
  agents.py                 MOD  +200 lines  Contract awareness in prompts
  config.py                 MOD  +120 lines  4 new config dataclasses
  state.py                  MOD  +50 lines   ContractReport, EndpointTestReport
  mcp_servers.py            MOD  +60 lines   2 new MCP server configs
  contracts.py              MOD  +150 lines  ServiceContractRegistry (note: this is the existing contracts module, not to be confused with Contract Engine service contracts)
  scheduler.py              MOD  +100 lines  ExecutionBackend protocol
  code_quality_standards.py MOD  +40 lines   CONTRACT + INTEGRATION standards
  tracking_documents.py     MOD  +100 lines  Contract compliance matrix
  codebase_map.py           MOD  +50 lines   MCP-backed generation
  milestone_manager.py      MOD  +20 lines   Contract-aware health
  e2e_testing.py            MOD  +50 lines   Contract compliance E2E
  verification.py           MOD  +80 lines   Contract compliance verification
  tech_research.py          MOD  +20 lines   Build 1 service detection

tests/
  test_agent_teams_backend.py   NEW  ~35 tests
  test_contract_client.py       NEW  ~30 tests
  test_codebase_client.py       NEW  ~30 tests
  test_hooks_manager.py         NEW  ~25 tests
  test_claude_md_generator.py   NEW  ~25 tests
  test_contract_scanner.py      NEW  ~35 tests
  test_build2_config.py         NEW  ~30 tests
  test_build2_wiring.py         NEW  ~30 tests
  test_build2_backward_compat.py NEW ~50 tests
```

---

## Milestone 1: Agent Teams Abstraction Layer

- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Create the execution backend abstraction that enables transparent switching between Claude Code Agent Teams (Mode A) and existing subprocess orchestration (Mode B). Includes ExecutionBackend protocol, AgentTeamsBackend, CLIBackend, hook configuration generator, and AgentTeamsConfig. No existing behavior changes — CLIBackend wraps current logic, AgentTeamsBackend is opt-in.

### Functional Requirements

- [ ] REQ-001: Create `src/agent_team/agent_teams_backend.py` with `ExecutionBackend` protocol defining: `async initialize() -> TeamState`, `async execute_wave(wave: ExecutionWave) -> WaveResult`, `async execute_task(task: ScheduledTask) -> TaskResult`, `async send_context(context: str) -> bool`, `async shutdown() -> None`, `supports_peer_messaging() -> bool` (sync), `supports_self_claiming() -> bool` (sync). The two boolean methods are regular methods (not properties) and may return different values mid-session if backend availability changes (review_cycles: 0)
- [ ] REQ-002: Implement `AgentTeamsBackend` class (Mode A) that creates tasks via Claude Code TaskCreate/TaskUpdate, maps ExecutionWave to parallel teammate assignments, uses hooks for quality gates, and runs in delegate mode (review_cycles: 0)
- [ ] REQ-003: Implement `CLIBackend` class (Mode B) that wraps existing `_run_single()` / `_run_prd_milestones()` logic from `cli.py`, returning `False` for `supports_peer_messaging()` and `supports_self_claiming()` (review_cycles: 0)
- [ ] REQ-004: Implement `create_execution_backend(config: AgentTeamConfig) -> ExecutionBackend` factory function with explicit decision tree: (1) If `config.agent_teams.enabled` is False → return CLIBackend. (2) If enabled=True AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var is not "1" → return CLIBackend + log warning "Agent teams enabled in config but env var not set". (3) If enabled=True AND env=1 AND `_verify_claude_available()` returns False AND `config.agent_teams.fallback_to_cli` is True → return CLIBackend + log warning "Claude CLI not available, falling back to CLI". (4) If enabled=True AND env=1 AND CLI missing AND fallback=False → raise RuntimeError("Claude CLI required for agent teams but not found"). (5) Otherwise → return AgentTeamsBackend (review_cycles: 0)
- [ ] REQ-005: Implement `detect_agent_teams_available() -> bool` that checks for env var, claude CLI availability, and returns False on Windows Terminal when split panes are required (review_cycles: 0)
- [ ] REQ-006: `AgentTeamsBackend.initialize()` must verify Claude Code CLI is available, set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, set `CLAUDE_CODE_SUBAGENT_MODEL` if `config.agent_teams.teammate_model` is non-empty, and return a `TeamState(mode="agent_teams")` (review_cycles: 0)
- [ ] REQ-007: `AgentTeamsBackend.execute_wave()` must create TaskCreate calls for each task in the wave, set up dependencies via TaskUpdate(addBlockedBy), and poll TaskList every 30 seconds (using `await asyncio.sleep(30)`, NOT `time.sleep(30)`) until all tasks complete or timeout. If a task is in_progress for longer than `config.agent_teams.task_timeout_seconds`, mark it as failed. If wave total time exceeds `config.agent_teams.wave_timeout_seconds`, fail remaining tasks and return WaveResult with partial results (review_cycles: 0)
- [ ] REQ-008: `AgentTeamsBackend.shutdown()` must send `shutdown_request` to all active teammates and set `state.active = False` (review_cycles: 0)
- [ ] REQ-009: When `config.agent_teams.fallback_to_cli` is True: (a) If AgentTeamsBackend fails during `initialize()`, the factory must catch the exception and return a CLIBackend instead, logging a warning. (b) If AgentTeamsBackend fails during `execute_wave()` (wave N), retry wave N with CLIBackend and continue all subsequent waves in CLI mode. (c) If `fallback_to_cli` is False, propagate the exception to the caller (review_cycles: 0)
- [ ] REQ-010: Create `src/agent_team/hooks_manager.py` with `generate_hooks_config(config: AgentTeamConfig, project_dir: Path, requirements_path: Path | None = None) -> HookConfig` returning a `HookConfig` dataclass containing hooks dict and shell script contents (review_cycles: 0)
- [ ] REQ-011: `generate_task_completed_hook()` must return an agent-type hook that reads REQUIREMENTS.md, verifies all `[x]` items, and exits with code 2 if claimed requirements are not satisfied — timeout 120 seconds (review_cycles: 0)
- [ ] REQ-012: `generate_teammate_idle_hook()` must return a command-type hook running `.claude/hooks/teammate-idle-check.sh` that executes `claude -p "Check TaskList for pending unblocked tasks and report count"`, parses the output for pending task count, and exits code 2 if pending unblocked tasks exist (preventing idle), allows idle (exit 0) if all tasks are completed or blocked — timeout 30 seconds (review_cycles: 0)
- [ ] REQ-013: `generate_stop_hook()` must return a command-type hook running `.claude/hooks/quality-gate.sh` that checks REQUIREMENTS.md completion ratio and exits code 2 if incomplete — timeout 30 seconds (review_cycles: 0)
- [ ] REQ-014: `write_hooks_to_project()` must write `.claude/settings.local.json` with hooks section and `.claude/hooks/*.sh` scripts with executable permissions (chmod 0o755). On Windows: write `.sh` files only (relies on WSL or Git Bash), wrap chmod in try/except OSError (no-op), and document in generated CLAUDE.md that WSL or Git Bash is required for hook execution on Windows (review_cycles: 0)
- [ ] REQ-015: `generate_post_tool_use_hook()` must return a command-type async hook with matcher `Write|Edit` that runs `.claude/hooks/track-file-change.sh` to log file changes for contract validation tracking (review_cycles: 0)
- [ ] REQ-016: The quality-gate.sh Stop hook script must read HookInput JSON from stdin (see TECH-004A), extract `cwd` field via `python3 -c "import sys,json; print(json.load(sys.stdin)['cwd'])"`, check `REQUIREMENTS.md` completion ratio (grep `[x]` vs `[ ]` checkboxes), and exit 2 with descriptive stderr message "REQUIREMENTS.md only {ratio} complete (threshold: 0.8)" when ratio < 0.8 (review_cycles: 0)

### Technical Requirements

- [ ] TECH-001: `TaskResult` dataclass with fields: `task_id: str`, `status: str` ("completed"|"failed"|"timeout"), `output: str`, `error: str`, `files_created: list[str]`, `files_modified: list[str]`, `duration_seconds: float = 0.0` — in `agent_teams_backend.py`. Note: cost tracking is at the Builder session level via `RunState.total_cost`, not per-task (Claude Code Agent Teams API does not expose per-task cost) (review_cycles: 0)
- [ ] TECH-002: `WaveResult` dataclass with fields: `wave_index: int`, `task_results: list[TaskResult]`, `all_succeeded: bool`, `duration_seconds: float = 0.0` — in `agent_teams_backend.py` (review_cycles: 0)
- [ ] TECH-003: `TeamState` dataclass with fields: `mode: str` ("agent_teams"|"cli"), `active: bool`, `teammates: list[str]`, `completed_tasks: list[str]`, `failed_tasks: list[str]`, `total_messages: int = 0` — in `agent_teams_backend.py`. Note: cost is tracked at Builder session level via RunState.total_cost, not in TeamState (review_cycles: 0)
- [ ] TECH-004: `HookConfig` dataclass with fields: `hooks: dict[str, list[dict[str, Any]]]`, `scripts: dict[str, str]` — in `hooks_manager.py` (review_cycles: 0)
- [ ] TECH-004A: `HookInput` dataclass with fields: `session_id: str = ""`, `transcript_path: str = ""`, `cwd: str = ""`, `permission_mode: str = ""`, `hook_event_name: str = ""`, `tool_name: str = ""`, `tool_input: dict[str, Any] = field(default_factory=dict)`, plus event-specific optional fields: `task_id: str = ""`, `task_subject: str = ""`, `task_description: str = ""`, `teammate_name: str = ""`, `team_name: str = ""` (for TaskCompleted and TeammateIdle hooks). Different hook events receive different subsets of these fields. Used for type-safe JSON parsing of stdin in hook scripts — in `hooks_manager.py` (review_cycles: 0)
- [ ] TECH-005: `AgentTeamsConfig` dataclass with fields: `enabled: bool = False`, `fallback_to_cli: bool = True`, `delegate_mode: bool = True`, `max_teammates: int = 5`, `teammate_model: str = ""`, `teammate_permission_mode: str = "acceptEdits"`, `teammate_idle_timeout: int = 300`, `task_completed_hook: bool = True`, `wave_timeout_seconds: int = 3600` (1 hour per wave), `task_timeout_seconds: int = 1800` (30 minutes per task), `teammate_display_mode: str = "in-process"` (safer default, works on Windows Terminal — alternatives: "tmux", "split"), `contract_limit: int = 100` (max contracts in CLAUDE.md before truncation) — in `config.py`. Note: teammate permissions are set at spawn time and cannot be changed mid-session (review_cycles: 0)
- [ ] TECH-006: Add `agent_teams: AgentTeamsConfig = field(default_factory=AgentTeamsConfig)` to root `AgentTeamConfig` dataclass in `config.py` (review_cycles: 0)
- [ ] TECH-007: Add `agent_teams_active: bool = False` field to `RunState` dataclass in `state.py` (review_cycles: 0)
- [ ] TECH-008: Add `agent_teams` section parsing to `_dict_to_config()` in `config.py`, following existing pattern of nested dataclass construction with user-override tracking, returning updated `set[str]` (review_cycles: 0)
- [ ] TECH-009: `ExecutionBackend` must be decorated with `@runtime_checkable` from `typing` and defined as a `Protocol` class, not an ABC (review_cycles: 0)
- [ ] TECH-010: `AgentTeamsBackend._verify_claude_available()` must call `subprocess.run(["claude", "--version"], capture_output=True, timeout=10)` and return `True` only if returncode is 0 (review_cycles: 0)
- [ ] TECH-011: `AgentTeamsBackend.execute_wave()` must use asyncio.gather with `return_exceptions=True` to handle individual task failures without failing the entire wave (review_cycles: 0)
- [ ] TECH-012: `write_hooks_to_project()` must merge into existing `.claude/settings.local.json` if it already exists, preserving non-hooks keys, using `json.loads()` with `try/except (json.JSONDecodeError, OSError)` fallback to empty dict (review_cycles: 0)
- [ ] TECH-012A: `AgentTeamsBackend.execute_wave()` must collect TaskResult data by: (1) parsing TaskList output field for each completed task to extract task outputs, (2) parsing agent tool call logs to identify files_created and files_modified lists, (3) tracking duration_seconds via wall-clock timing per task. Files created/modified are determined by examining the task's output for Write/Edit tool call patterns (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-001: Wire `create_execution_backend()` call into `cli.py` mode selection block (the `if interactive:` ... `else:` branch containing `_run_prd_milestones()` and `_run_single()` calls), before the existing milestone/standard branch, gated on `config.agent_teams.enabled` (review_cycles: 0)
- [ ] WIRE-002: Wire `write_hooks_to_project()` call into `cli.py` after backend initialization, gated on `team_state.mode == "agent_teams"` (review_cycles: 0)
- [ ] WIRE-003: Wire teammate shutdown into `_handle_interrupt()` in `cli.py` — if `_module_state.team_state` exists and is active, send shutdown_request to all teammates before saving state (review_cycles: 0)
- [ ] WIRE-003A: Add `team_state: TeamState | None = None` to `_module_state` in cli.py (after existing `_current_state`). Update `create_execution_backend()` to assign to `_module_state.team_state` when AgentTeamsBackend is created. This enables signal handler access to team_state for graceful shutdown (review_cycles: 0)

### Test Requirements

- [ ] TEST-001: Test `create_execution_backend()` returns CLIBackend when `agent_teams.enabled` is False (review_cycles: 0)
- [ ] TEST-002: Test `create_execution_backend()` returns CLIBackend when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var is not set (review_cycles: 0)
- [ ] TEST-003: Test `create_execution_backend()` returns AgentTeamsBackend when all conditions are met (mock `_verify_claude_available` to return True) (review_cycles: 0)
- [ ] TEST-004: Test fallback — AgentTeamsBackend.initialize() raises, factory catches and returns CLIBackend when `fallback_to_cli` is True (review_cycles: 0)
- [ ] TEST-005: Test fallback — AgentTeamsBackend.initialize() raises, factory propagates exception when `fallback_to_cli` is False (review_cycles: 0)
- [ ] TEST-006: Test `generate_task_completed_hook()` produces agent-type hook dict with correct prompt, timeout=120 (review_cycles: 0)
- [ ] TEST-007: Test `generate_teammate_idle_hook()` produces command-type hook dict referencing `.claude/hooks/teammate-idle-check.sh` with timeout=30 and returns valid bash script content (review_cycles: 0)
- [ ] TEST-008: Test `generate_stop_hook()` produces command-type hook dict referencing `.claude/hooks/quality-gate.sh` and returns valid bash script content (review_cycles: 0)
- [ ] TEST-009: Test `generate_post_tool_use_hook()` produces command-type async hook with `Write|Edit` matcher (review_cycles: 0)
- [ ] TEST-010: Test `write_hooks_to_project()` creates `.claude/settings.local.json` and `.claude/hooks/` directory with scripts (review_cycles: 0)
- [ ] TEST-011: Test `write_hooks_to_project()` merges into existing `.claude/settings.local.json` preserving non-hooks keys (review_cycles: 0)
- [ ] TEST-012: Test `AgentTeamsConfig` defaults — `enabled=False`, `fallback_to_cli=True`, `max_teammates=5` (review_cycles: 0)
- [ ] TEST-013: Test `_dict_to_config()` parses `agent_teams` YAML section into AgentTeamsConfig, and existing configs without this section still work (review_cycles: 0)
- [ ] TEST-014: Test `CLIBackend.supports_peer_messaging()` returns False, `CLIBackend.supports_self_claiming()` returns False (review_cycles: 0)
- [ ] TEST-015: Test `AgentTeamsBackend.supports_peer_messaging()` returns True, `AgentTeamsBackend.supports_self_claiming()` returns True (review_cycles: 0)
- [ ] TEST-016: Test `detect_agent_teams_available()` returns False when env var not set (review_cycles: 0)
- [ ] TEST-017: Test chmod graceful degradation on Windows — `write_hooks_to_project()` succeeds when `OSError` is raised by `chmod(0o755)` (review_cycles: 0)

---

## Milestone 2: Contract Engine Integration

- ID: milestone-2
- Status: PENDING
- Dependencies: none
- Description: Create typed MCP client wrapping 6 of 9 Contract Engine MCP tools (get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts — the remaining 3 tools: create_contract, validate_spec, list_contracts are consumed directly by Build 3's Integrator), MCP session management utilities, ServiceContractRegistry for local+MCP contract management, and MCP server configuration. Every MCP call has try/except returning safe defaults on failure, enabling fallback to existing static scans. Note: mcp_clients.py is created in this milestone (not M1), so M2 has no dependencies.

### Functional Requirements

- [ ] REQ-017: Create `src/agent_team/contract_client.py` with `ContractEngineClient` class wrapping 6 of 9 Contract Engine MCP tools (get_contract, validate_endpoint, generate_tests, check_breaking_changes, mark_implemented, get_unimplemented_contracts). The remaining 3 tools (create_contract, validate_spec, list_contracts) are consumed directly by Build 3's Integrator via MCP (review_cycles: 0)
- [ ] REQ-018: `ContractEngineClient.get_contract(contract_id: str) -> ContractInfo | None` must call MCP tool `get_contract`, return `ContractInfo` dataclass on success, `None` on any error (review_cycles: 0)
- [ ] REQ-019: `ContractEngineClient.validate_endpoint(service_name: str, method: str, path: str, response_body: dict, status_code: int = 200) -> ContractValidation` must call MCP tool `validate_endpoint`, return `ContractValidation(valid=bool, violations=list)` on success, `ContractValidation(error="...")` on failure (review_cycles: 0)
- [ ] REQ-020: `ContractEngineClient.generate_tests(contract_id: str, framework: str = "pytest", include_negative: bool = True) -> str` must call MCP tool `generate_tests`, return test file content as string, empty string on error (review_cycles: 0)
- [ ] REQ-021: `ContractEngineClient.check_breaking_changes(contract_id: str, new_spec: dict) -> list[dict]` must call MCP tool `check_breaking_changes`, return list of change dicts, empty list on error (review_cycles: 0)
- [ ] REQ-022: `ContractEngineClient.mark_implemented(contract_id: str, service_name: str, evidence_path: str) -> dict` must call MCP tool `mark_implemented`, return result dict with `marked` key, `{"marked": False}` on error (review_cycles: 0)
- [ ] REQ-023: `ContractEngineClient.get_unimplemented_contracts(service_name: str | None = None) -> list[dict]` must call MCP tool `get_unimplemented_contracts`, return list of contract dicts, empty list on error (review_cycles: 0)
- [ ] REQ-024: Create `src/agent_team/mcp_clients.py` with `create_contract_engine_session()` async context manager (decorated with `@asynccontextmanager` from contextlib) using `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern from MCP Python SDK. Must catch `(TimeoutError, ConnectionError, ProcessLookupError, OSError)` during `session.initialize()` and re-raise as custom `MCPConnectionError(str(e))`. Context manager `__aexit__` must terminate MCP server process gracefully on errors. Define `class MCPConnectionError(Exception): pass` in `mcp_clients.py`. Apply `startup_timeout_ms` as `asyncio.wait_for()` wrapper around `session.initialize()`, and `tool_timeout_ms` as `asyncio.wait_for()` wrapper around each `session.call_tool()` invocation. On timeout, raise `MCPConnectionError('MCP operation timed out after {ms}ms')` (review_cycles: 0)
- [ ] REQ-025: `create_contract_engine_session()` must call `await session.initialize()` immediately after creating the ClientSession and before yielding to the caller — this is a MANDATORY first call per MCP SDK specification, without which all subsequent tool calls will fail (review_cycles: 0)
- [ ] REQ-026: Every `ContractEngineClient` method must retry up to 3 times on transient errors (`OSError`, `TimeoutError`, `ConnectionError`, MCP connection errors) with exponential backoff (1s, 2s, 4s). After all retries exhausted, log a warning with `exc_info=True` and return safe defaults. Non-transient errors (e.g., `TypeError`, `ValueError`) must log a warning immediately and return safe defaults without retrying. Methods must never raise to the caller (review_cycles: 0)
- [ ] REQ-027: Add `ServiceContract` dataclass to `contracts.py` with fields: `contract_id: str`, `contract_type: str`, `provider_service: str`, `consumer_service: str`, `version: str`, `spec_hash: str`, `spec: dict`, `implemented: bool = False`, `evidence_path: str = ""` (review_cycles: 0)
- [ ] REQ-028: Add `ServiceContractRegistry` class to `contracts.py` with `load_from_mcp(client: ContractEngineClient)`, `load_from_local(path: Path)`, `validate_endpoint()`, `mark_implemented()`, `get_unimplemented()`, `save_local_cache(path: Path)` methods (review_cycles: 0)
- [ ] REQ-029: `ServiceContractRegistry.load_from_mcp()` must populate registry from Contract Engine, falling back to `load_from_local()` on MCP failure (review_cycles: 0)
- [ ] REQ-029A: `ServiceContractRegistry.save_local_cache(path: Path)` must strip `spec.components.securitySchemes` from all OpenAPI contracts before writing JSON to prevent accidental secret exposure in version control. This implements SEC-003 (review_cycles: 0)

### Technical Requirements

- [ ] TECH-013: `ContractValidation` dataclass with fields: `valid: bool = False`, `violations: list[dict[str, str]] = field(default_factory=list)`, `error: str = ""` — in `contract_client.py` (review_cycles: 0)
- [ ] TECH-014: `ContractInfo` dataclass with fields: `id: str = ""`, `type: str = ""`, `version: str = ""`, `service_name: str = ""`, `spec: dict[str, Any] = field(default_factory=dict)`, `spec_hash: str = ""` (SHA-256 hex digest of canonical JSON spec — `hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()` — NO compact separators, matching Build 1 TECH-009), `status: str = ""` — in `contract_client.py` (review_cycles: 0)
- [ ] TECH-015: `ContractEngineConfig` dataclass with fields: `enabled: bool = False`, `mcp_command: str = "python"`, `mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.contract_engine.mcp_server"])`, `database_path: str = ""`, `validation_on_build: bool = True`, `test_generation: bool = True`, `server_root: str = ""` (path to Build 1 project root where MCP server modules live — passed as `cwd` to `StdioServerParameters`), `startup_timeout_ms: int = 30000` (30s MCP server startup timeout), `tool_timeout_ms: int = 60000` (60s per MCP tool call timeout) — in `config.py`. When `database_path` is empty, fall back to `os.getenv('CONTRACT_ENGINE_DB', '')` (review_cycles: 0)
- [ ] TECH-016: Add `contract_engine: ContractEngineConfig = field(default_factory=ContractEngineConfig)` to root `AgentTeamConfig` in `config.py` (review_cycles: 0)
- [ ] TECH-017: `_extract_json(result: Any) -> Any` helper in `ContractEngineClient` that iterates `result.content`, finds `TextContent` with `hasattr(content, "text")`, parses JSON, returns None on any failure (review_cycles: 0)
- [ ] TECH-018: `_extract_text(result: Any) -> str` helper in `ContractEngineClient` that iterates `result.content`, returns first text content, empty string if none (review_cycles: 0)
- [ ] TECH-019: `create_contract_engine_session()` must do lazy import of `mcp` package — `from mcp import StdioServerParameters` inside the function body, raising `ImportError` with message "MCP SDK not installed. pip install mcp" (review_cycles: 0)
- [ ] TECH-020: `create_contract_engine_session()` must pass `env` dict to `StdioServerParameters` with `DATABASE_PATH` from config when non-empty (falling back to `os.getenv('CONTRACT_ENGINE_DB', '')`), `None` otherwise. Must also pass `cwd=config.contract_engine.server_root` when non-empty to ensure MCP server runs from Build 1 project root (review_cycles: 0)
- [ ] TECH-021: Add `contract_engine` section parsing to `_dict_to_config()` following existing pattern, with `mcp_args` parsed as list from YAML sequence (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-004: Add `_contract_engine_mcp_server(config: ContractEngineConfig) -> dict[str, Any]` to `mcp_servers.py`, returning `{"type": "stdio", "command": config.mcp_command, "args": config.mcp_args, "env": {"DATABASE_PATH": config.database_path}}` (review_cycles: 0)
- [ ] WIRE-005: Wire contract engine MCP server into `get_contract_aware_servers()` in `mcp_servers.py`, gated on `config.contract_engine.enabled` (review_cycles: 0)

### Service-to-API Wiring

| SVC-ID | Client Method | MCP Tool | Request DTO | Response DTO |
|--------|---------------|----------|-------------|--------------|
| SVC-001 | ContractEngineClient.get_contract(contract_id) | get_contract | { contract_id: string } | { id: string, type: string, version: string, service_name: string, spec: object, spec_hash: string, status: string } |
| SVC-002 | ContractEngineClient.validate_endpoint(service_name, method, path, response_body, status_code) | validate_endpoint | { service_name: string, method: string, path: string, response_body: object, status_code: number } | { valid: boolean, violations: array } |
| SVC-003 | ContractEngineClient.generate_tests(contract_id, framework, include_negative) | generate_tests | { contract_id: string, framework: string, include_negative: boolean } | string |
| SVC-004 | ContractEngineClient.check_breaking_changes(contract_id, new_spec) | check_breaking_changes | { contract_id: string, new_spec: object } | array |
| SVC-005 | ContractEngineClient.mark_implemented(contract_id, service_name, evidence_path) | mark_implemented | { contract_id: string, service_name: string, evidence_path: string } | { marked: boolean, total: number, all_implemented: boolean } |
| SVC-006 | ContractEngineClient.get_unimplemented_contracts(service_name) | get_unimplemented_contracts | { service_name: string } | array |

- [ ] SVC-001: ContractEngineClient.get_contract(contract_id) -> MCP get_contract { contract_id: string } -> { id: string, type: string, version: string, service_name: string, spec: object, spec_hash: string, status: string } (review_cycles: 0)
- [ ] SVC-002: ContractEngineClient.validate_endpoint(service_name, method, path, response_body, status_code) -> MCP validate_endpoint { service_name: string, method: string, path: string, response_body: object, status_code: number } -> { valid: boolean, violations: array } (review_cycles: 0)
- [ ] SVC-003: ContractEngineClient.generate_tests(contract_id, framework, include_negative) -> MCP generate_tests { contract_id: string, framework: string, include_negative: boolean } -> string (review_cycles: 0)
- [ ] SVC-004: ContractEngineClient.check_breaking_changes(contract_id, new_spec) -> MCP check_breaking_changes { contract_id: string, new_spec: object } -> array (review_cycles: 0)
- [ ] SVC-005: ContractEngineClient.mark_implemented(contract_id, service_name, evidence_path) -> MCP mark_implemented { contract_id: string, service_name: string, evidence_path: string } -> { marked: boolean, total: number, all_implemented: boolean } (review_cycles: 0)
- [ ] SVC-006: ContractEngineClient.get_unimplemented_contracts(service_name) -> MCP get_unimplemented_contracts { service_name: string } -> array (review_cycles: 0)

### Test Requirements

- [ ] TEST-018: Test all 6 `ContractEngineClient` methods with mocked MCP session returning valid JSON — verify correct dataclass construction (review_cycles: 0)
- [ ] TEST-019: Test all 6 methods with mocked MCP session raising `Exception` — verify safe defaults returned and warning logged (review_cycles: 0)
- [ ] TEST-020: Test all 6 methods with `result.isError = True` — verify safe defaults returned (review_cycles: 0)
- [ ] TEST-021: Test `_extract_json()` with valid JSON text content, invalid JSON, empty content, and None (review_cycles: 0)
- [ ] TEST-022: Test `_extract_text()` with valid text content, empty content, and no text content (review_cycles: 0)
- [ ] TEST-023: Test `create_contract_engine_session()` raises ImportError when mcp package is not available (review_cycles: 0)
- [ ] TEST-024: Test `create_contract_engine_session()` passes DATABASE_PATH env when config.database_path is non-empty, None when empty (review_cycles: 0)
- [ ] TEST-025: Test `ContractEngineConfig` defaults — `enabled=False`, `mcp_command="python"` (review_cycles: 0)
- [ ] TEST-026: Test `_dict_to_config()` parses `contract_engine` YAML section correctly, and missing section produces defaults (review_cycles: 0)
- [ ] TEST-027: Test `_contract_engine_mcp_server()` returns correct dict with type, command, args, env fields (review_cycles: 0)
- [ ] TEST-028: Test `ServiceContractRegistry.load_from_mcp()` populates registry from mocked ContractEngineClient (review_cycles: 0)
- [ ] TEST-029: Test `ServiceContractRegistry.load_from_local()` reads CONTRACTS.json and populates registry (review_cycles: 0)
- [ ] TEST-030: Test `ServiceContractRegistry.save_local_cache()` writes JSON that can be re-loaded by `load_from_local()` (review_cycles: 0)
- [ ] TEST-030A: Test `ServiceContractRegistry.save_local_cache()` removes `spec.components.securitySchemes` from OpenAPI contracts before writing CONTRACTS.json (review_cycles: 0)
- [ ] TEST-030B: Test `ContractEngineClient` methods retry 3 times on `TimeoutError` with exponential backoff before returning safe defaults (review_cycles: 0)
- [ ] TEST-030C: Test `ContractEngineClient` methods return safe defaults immediately on `TypeError` without retrying (review_cycles: 0)
- [ ] TEST-030D: Test MCP session — `create_contract_engine_session()` raises `MCPConnectionError` when MCP server process exits during `session.initialize()` (review_cycles: 0)

---

## Milestone 3: Codebase Intelligence Integration

- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-2
- Description: Create typed MCP client for Build 1's Codebase Intelligence service (7 tools), MCP-backed codebase map generation as alternative to static analysis, and artifact registration support. Shares MCP session management from M2.

### Functional Requirements

- [ ] REQ-030: Create `src/agent_team/codebase_client.py` with `CodebaseIntelligenceClient` class wrapping all 7 Codebase Intelligence MCP tools (review_cycles: 0)
- [ ] REQ-031: `CodebaseIntelligenceClient.find_definition(symbol: str, language: str | None = None) -> DefinitionResult` must call MCP tool, return `DefinitionResult(found=True, ...)` on success, `DefinitionResult()` on error (review_cycles: 0)
- [ ] REQ-032: `CodebaseIntelligenceClient.find_callers(symbol: str, max_results: int = 50) -> list[dict]` must call MCP tool, return caller list on success, empty list on error (review_cycles: 0)
- [ ] REQ-033: `CodebaseIntelligenceClient.find_dependencies(file_path: str) -> DependencyResult` must call MCP tool, return `DependencyResult` with imports, imported_by, transitive_deps, circular_deps (review_cycles: 0)
- [ ] REQ-034: `CodebaseIntelligenceClient.search_semantic(query: str, language: str | None = None, service_name: str | None = None, n_results: int = 10) -> list[dict]` must call MCP tool with all provided parameters (language and service_name are optional filters matching Build 1's tool signature), return search results, empty list on error (review_cycles: 0)
- [ ] REQ-035: `CodebaseIntelligenceClient.get_service_interface(service_name: str) -> dict` must call MCP tool, return interface dict with endpoints, events_published, events_consumed — empty dict on error (review_cycles: 0)
- [ ] REQ-036: `CodebaseIntelligenceClient.check_dead_code(service_name: str | None = None) -> list[dict]` must call MCP tool, return dead code symbols list, empty list on error (review_cycles: 0)
- [ ] REQ-037: `CodebaseIntelligenceClient.register_artifact(file_path: str, service_name: str) -> ArtifactResult` must call MCP tool, return `ArtifactResult(indexed=bool, symbols_found=int, dependencies_found=int)` (review_cycles: 0)
- [ ] REQ-038: Add `create_codebase_intelligence_session()` async context manager (decorated with `@asynccontextmanager`) to `mcp_clients.py` using same `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern, with env vars for DATABASE_PATH, CHROMA_PATH, GRAPH_PATH, and `cwd=config.server_root` when non-empty. Must call `await session.initialize()` immediately after ClientSession creation (MANDATORY first call per MCP SDK) before yielding. Same error handling as `create_contract_engine_session()` — catch transient errors, re-raise as `MCPConnectionError` (review_cycles: 0)
- [ ] REQ-039: `create_codebase_intelligence_session()` must pass non-empty env vars to `StdioServerParameters` and `None` when all are empty (review_cycles: 0)
- [ ] REQ-040: Add `generate_codebase_map_from_mcp(project_dir: Path, client: CodebaseIntelligenceClient) -> str` to `codebase_map.py` that calls `get_service_interface()`, `find_dependencies()`, and `search_semantic("architecture overview")` to produce CODEBASE_MAP.md content (review_cycles: 0)
- [ ] REQ-041: Add `register_new_artifact(client: CodebaseIntelligenceClient, file_path: str, service_name: str) -> ArtifactResult` to `codebase_map.py` that calls `register_artifact()` via MCP and returns `ArtifactResult` (review_cycles: 0)
- [ ] REQ-042: Every `CodebaseIntelligenceClient` method must retry up to 3 times on transient errors (`OSError`, `TimeoutError`, `ConnectionError`) with exponential backoff (1s, 2s, 4s). After all retries exhausted, log a warning with `exc_info=True` and return safe defaults. Non-transient errors log warning immediately and return safe defaults without retrying. Methods must never raise to the caller (review_cycles: 0)

### Technical Requirements

- [ ] TECH-022: `DefinitionResult` dataclass with fields: `file: str = ""`, `line: int = 0`, `kind: str = ""`, `signature: str = ""`, `found: bool = False` — in `codebase_client.py` (review_cycles: 0)
- [ ] TECH-023: `DependencyResult` dataclass with fields: `imports: list[str]`, `imported_by: list[str]`, `transitive_deps: list[str]`, `circular_deps: list[list[str]]` — all default empty lists — in `codebase_client.py` (review_cycles: 0)
- [ ] TECH-024: `ArtifactResult` dataclass with fields: `indexed: bool = False`, `symbols_found: int = 0`, `dependencies_found: int = 0` — in `codebase_client.py` (review_cycles: 0)
- [ ] TECH-025: `CodebaseIntelligenceConfig` dataclass with fields: `enabled: bool = False`, `mcp_command: str = "python"`, `mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.codebase_intelligence.mcp_server"])`, `database_path: str = ""`, `chroma_path: str = ""`, `graph_path: str = ""`, `replace_static_map: bool = True`, `register_artifacts: bool = True`, `server_root: str = ""` (path to Build 1 project root — passed as `cwd` to `StdioServerParameters`), `startup_timeout_ms: int = 30000`, `tool_timeout_ms: int = 60000` — in `config.py`. When paths are empty, fall back to `os.getenv()` (review_cycles: 0)
- [ ] TECH-026: Add `codebase_intelligence: CodebaseIntelligenceConfig = field(default_factory=CodebaseIntelligenceConfig)` to root `AgentTeamConfig` in `config.py` (review_cycles: 0)
- [ ] TECH-027: Add `codebase_intelligence` section parsing to `_dict_to_config()` following existing pattern (review_cycles: 0)
- [ ] TECH-028: `CodebaseIntelligenceClient._extract_json()` must share the same implementation pattern as `ContractEngineClient._extract_json()` — iterate `result.content`, find text, parse JSON, return None on failure (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-006: Add `_codebase_intelligence_mcp_server(config: CodebaseIntelligenceConfig) -> dict[str, Any]` to `mcp_servers.py`, returning `{"type": "stdio", "command": config.mcp_command, "args": config.mcp_args, "env": {DATABASE_PATH, CHROMA_PATH, GRAPH_PATH}}` (review_cycles: 0)
- [ ] WIRE-007: Wire codebase intelligence MCP server into `get_contract_aware_servers()` in `mcp_servers.py`, gated on `config.codebase_intelligence.enabled` (review_cycles: 0)
- [ ] WIRE-008: Add `get_contract_aware_servers(config: AgentTeamConfig) -> dict[str, Any]` to `mcp_servers.py` that calls `get_mcp_servers(config)` then conditionally adds Contract Engine and Codebase Intelligence servers (review_cycles: 0)

### Service-to-API Wiring

| SVC-ID | Client Method | MCP Tool | Request DTO | Response DTO |
|--------|---------------|----------|-------------|--------------|
| SVC-007 | CodebaseIntelligenceClient.find_definition(symbol, language) | find_definition | { symbol: string, language: string } | { file: string, line: number, kind: string, signature: string } |
| SVC-008 | CodebaseIntelligenceClient.find_callers(symbol, max_results) | find_callers | { symbol: string, max_results: number } | array |
| SVC-009 | CodebaseIntelligenceClient.find_dependencies(file_path) | find_dependencies | { file_path: string } | { imports: array, imported_by: array, transitive_deps: array, circular_deps: array } |
| SVC-010 | CodebaseIntelligenceClient.search_semantic(query, language, service_name, n_results) | search_semantic | { query: string, language: string, service_name: string, n_results: number } | array |
| SVC-011 | CodebaseIntelligenceClient.get_service_interface(service_name) | get_service_interface | { service_name: string } | { endpoints: array, events_published: array, events_consumed: array } |
| SVC-012 | CodebaseIntelligenceClient.check_dead_code(service_name) | check_dead_code | { service_name: string } | array |
| SVC-013 | CodebaseIntelligenceClient.register_artifact(file_path, service_name) | register_artifact | { file_path: string, service_name: string } | { indexed: boolean, symbols_found: number, dependencies_found: number } |

- [ ] SVC-007: CodebaseIntelligenceClient.find_definition(symbol, language) -> MCP find_definition { symbol: string, language: string } -> { file: string, line: number, kind: string, signature: string } (review_cycles: 0)
- [ ] SVC-008: CodebaseIntelligenceClient.find_callers(symbol, max_results) -> MCP find_callers { symbol: string, max_results: number } -> array (review_cycles: 0)
- [ ] SVC-009: CodebaseIntelligenceClient.find_dependencies(file_path) -> MCP find_dependencies { file_path: string } -> { imports: array, imported_by: array, transitive_deps: array, circular_deps: array } (review_cycles: 0)
- [ ] SVC-010: CodebaseIntelligenceClient.search_semantic(query, language, service_name, n_results) -> MCP search_semantic { query: string, language: string, service_name: string, n_results: number } -> array (review_cycles: 0)
- [ ] SVC-011: CodebaseIntelligenceClient.get_service_interface(service_name) -> MCP get_service_interface { service_name: string } -> { endpoints: array, events_published: array, events_consumed: array } (review_cycles: 0)
- [ ] SVC-012: CodebaseIntelligenceClient.check_dead_code(service_name) -> MCP check_dead_code { service_name: string } -> array (review_cycles: 0)
- [ ] SVC-013: CodebaseIntelligenceClient.register_artifact(file_path, service_name) -> MCP register_artifact { file_path: string, service_name: string } -> { indexed: boolean, symbols_found: number, dependencies_found: number } (review_cycles: 0)

### Test Requirements

- [ ] TEST-031: Test all 7 `CodebaseIntelligenceClient` methods with mocked MCP session returning valid JSON — verify correct dataclass construction (review_cycles: 0)
- [ ] TEST-032: Test all 7 methods with mocked MCP session raising Exception — verify safe defaults and warning logged (review_cycles: 0)
- [ ] TEST-033: Test all 7 methods with `result.isError = True` — verify safe defaults returned (review_cycles: 0)
- [ ] TEST-034: Test `generate_codebase_map_from_mcp()` produces valid markdown output from mocked MCP responses (review_cycles: 0)
- [ ] TEST-035: Test `register_new_artifact()` returns ArtifactResult from mocked MCP (review_cycles: 0)
- [ ] TEST-036: Test `CodebaseIntelligenceConfig` defaults — `enabled=False`, `replace_static_map=True`, `register_artifacts=True` (review_cycles: 0)
- [ ] TEST-037: Test `_codebase_intelligence_mcp_server()` returns correct dict with all 3 env vars (review_cycles: 0)
- [ ] TEST-038: Test `create_codebase_intelligence_session()` passes only non-empty env vars to StdioServerParameters (review_cycles: 0)
- [ ] TEST-039: Test `get_contract_aware_servers()` includes contract-engine and codebase-intelligence keys when both enabled, omits when disabled (review_cycles: 0)

---

## Milestone 4: Pipeline Integration + CLAUDE.md Generation

- ID: milestone-4
- Status: PENDING
- Dependencies: milestone-1, milestone-2, milestone-3
- Description: Wire all backends and MCP clients into the main cli.py pipeline. Create CLAUDE.md generator for agent teams teammates. Update prompts in agents.py with contract awareness. Add ContractReport and EndpointTestReport to state. This is the heaviest modification milestone.

### Functional Requirements

- [ ] REQ-043: Create `src/agent_team/claude_md_generator.py` with `generate_claude_md()` producing CLAUDE.md content for 5 roles: architect, code-writer, code-reviewer, test-engineer, wiring-verifier (review_cycles: 0)
- [ ] REQ-044: `generate_claude_md()` must accept parameters: `role: str`, `service_name: str`, `contracts: list[dict]`, `dependencies: list[str]`, `mcp_servers: dict`, `quality_standards: str`, `convergence_config: dict`, `tech_stack: str`, `codebase_context: str` (review_cycles: 0)
- [ ] REQ-045: CLAUDE.md generated for architect role must include: instructions to query Contract Engine for existing contracts, query Codebase Intelligence for existing code, generate SVC-xxx contract stubs with EXACT FIELD SCHEMAS (review_cycles: 0)
- [ ] REQ-046: CLAUDE.md generated for code-writer role must include: ZERO MOCK DATA POLICY, API CONTRACT COMPLIANCE, instructions to call `validate_endpoint()` after each endpoint, instructions to call `register_artifact()` after each new file (review_cycles: 0)
- [ ] REQ-047: CLAUDE.md generated for code-reviewer role must include: contract field verification, instructions to report CONTRACT violations as blocking issues, instructions to use Codebase Intelligence for cross-file impact analysis (review_cycles: 0)
- [ ] REQ-048: CLAUDE.md generated for test-engineer role must include: instructions to use Contract Engine `generate_tests()` for contract conformance tests, unit test and integration test requirements (review_cycles: 0)
- [ ] REQ-049: CLAUDE.md generated for wiring-verifier role must include: instructions to use `find_dependencies()` for import tracing, `check_dead_code()` for unused exports, contract endpoint verification (review_cycles: 0)
- [ ] REQ-050: CLAUDE.md must include "Available MCP Tools" section listing Contract Engine tools (6) and Codebase Intelligence tools (7) with parameter descriptions when those servers are in mcp_servers dict (review_cycles: 0)
- [ ] REQ-051: CLAUDE.md must include "Convergence Mandates" section with min ratio from config, contract validation requirement, artifact registration requirement, and zero mock data mandate (review_cycles: 0)
- [ ] REQ-052: CLAUDE.md contracts section must limit to `config.agent_teams.contract_limit` contracts (default 100) to prevent excessive file size, with "... and N more. Use Contract Engine get_contract(contract_id) MCP tool to fetch additional contracts on demand." suffix when truncated (review_cycles: 0)
- [ ] REQ-053: `write_teammate_claude_md(project_dir, role, service_name, config, contracts, mcp_servers) -> Path` must write to `{project_dir}/.claude/CLAUDE.md` creating the `.claude/` directory if needed, returning the path written. If CLAUDE.md already exists, append Build 2 sections under a delimited block (`<!-- AGENT-TEAMS-START -->...<!-- AGENT-TEAMS-END -->`). Replace only the delimited block on subsequent writes, preserving user content outside the block (review_cycles: 0)
- [ ] REQ-054: In `cli.py` Phase 0.5 (codebase map), when `config.codebase_intelligence.enabled` AND `config.codebase_intelligence.replace_static_map`, call `generate_codebase_map_from_mcp()` with fallback to existing `generate_codebase_map()` on exception (review_cycles: 0)
- [ ] REQ-055: In `cli.py`, after codebase map generation (Phase 0.5) and before mode selection block, when `config.contract_engine.enabled`, create `ServiceContractRegistry`, call `load_from_mcp()`, then `save_local_cache()` — falling back to `load_from_local()` only on MCP failure. Wrap in try/except with logger.warning on failure (review_cycles: 0)
- [ ] REQ-056: In `cli.py` mode selection, when agent teams backend is active, call `write_teammate_claude_md()` and `write_hooks_to_project()` before starting milestone execution (review_cycles: 0)
- [ ] REQ-057: Add contract awareness section to `ARCHITECT_PROMPT` in `agents.py` — instructions to query Contract Engine for existing contracts before designing, query Codebase Intelligence for existing code, and generate SVC-xxx contract stubs (review_cycles: 0)
- [ ] REQ-058: Add contract compliance section to `CODE_WRITER_PROMPT` in `agents.py` — instructions to call `validate_endpoint()` after each API endpoint, call `register_artifact()` after each new file, and fix validation failures before proceeding (review_cycles: 0)
- [ ] REQ-059: Add contract review section to `CODE_REVIEWER_PROMPT` in `agents.py` — instructions to verify every API endpoint matches its SVC-xxx contract, report CONTRACT violations as blocking, and use Codebase Intelligence for cross-file analysis (review_cycles: 0)
- [ ] REQ-060: Add `contract_context: str = ""` and `codebase_index_context: str = ""` parameters to `build_orchestrator_prompt()` and `build_milestone_execution_prompt()` in `agents.py`, injected following the existing `tech_research_content` pattern (review_cycles: 0)
- [ ] REQ-060A: Modify `build_milestone_execution_prompt()` 9-step MILESTONE WORKFLOW block in `agents.py` — the Analysis step must include "Query Contract Engine for all contracts with provider_service or consumer_service matching this milestone's service_name", the Implementation step must include "After creating each new file, call register_artifact(file_path, service_name) via Codebase Intelligence MCP", the Integration Verification step must include "For each SVC-xxx contract implemented in this milestone, call validate_endpoint() and report CONTRACT-001 violations" (review_cycles: 0)
- [ ] REQ-060B: Before calling `build_orchestrator_prompt()` in cli.py, when Contract Engine MCP is enabled, call `client.get_unimplemented_contracts()` and format result as `contract_context` string. When Codebase Intelligence MCP is enabled, call `client.search_semantic('architecture overview')` and format result as `codebase_index_context` string. Both in try/except returning empty string on failure (review_cycles: 0)
- [ ] REQ-061: In `cli.py` convergence health check, when `config.contract_engine.enabled` and `contract_report` exists, factor contract compliance ratio into health calculation: `health_ratio = min(checkbox_ratio, contract_compliance_ratio)` (review_cycles: 0)
- [ ] REQ-062: In `cli.py` signal handler `_handle_interrupt()`, when `team_state` is active, send shutdown to all teammates before saving state (review_cycles: 0)
- [ ] REQ-063: In `cli.py` resume context `_build_resume_context()`, include contract state (listing `contract_report.verified_contract_ids` and `contract_report.violated_contract_ids`), list of `registered_artifacts` to avoid re-indexing on resume, and note that agent teams teammates were lost if previously active (review_cycles: 0)

### Technical Requirements

- [ ] TECH-029: `ContractReport` dataclass with fields: `total_contracts: int = 0`, `verified_contracts: int = 0`, `violated_contracts: int = 0`, `missing_implementations: int = 0`, `violations: list[dict] = field(default_factory=list)`, `health: str = "unknown"`, `verified_contract_ids: list[str] = field(default_factory=list)`, `violated_contract_ids: list[str] = field(default_factory=list)` — in `state.py`. The ID lists enable granular resume context (review_cycles: 0)
- [ ] TECH-030: `EndpointTestReport` dataclass (renamed from `IntegrationReport` to avoid name collision with Build 3's IntegrationReport) with fields: `total_endpoints: int = 0`, `tested_endpoints: int = 0`, `passed_endpoints: int = 0`, `failed_endpoints: int = 0`, `untested_contracts: list[str] = field(default_factory=list)`, `health: str = "unknown"` — in `state.py` (review_cycles: 0)
- [ ] TECH-031: Add `contract_report: ContractReport | None = None`, `endpoint_test_report: EndpointTestReport | None = None`, `registered_artifacts: list[str] = field(default_factory=list)` fields to `RunState` in `state.py`. Update `save_state()` in `state.py` to serialize these fields using `dataclasses.asdict()` for ContractReport/EndpointTestReport (or None), and MUST include a top-level `summary` dict with computed fields: `success: bool` (True if health in ("passed","partial")), `test_passed: int`, `test_total: int`, `convergence_ratio: float` — derived from health, e2e_report, and convergence data. This summary is an intentional cross-build coupling point — Build 3 reads STATE.json to construct BuilderResult. Update `load_state()` in `state.py` to deserialize back into dataclass instances. STATE.json must roundtrip correctly (review_cycles: 0)
- [ ] TECH-032: The `contract_context` parameter injection in `build_orchestrator_prompt()` must be wrapped in `CONTRACT ENGINE CONTEXT` delimiters following the same pattern as `TECH RESEARCH RESULTS` (review_cycles: 0)
- [ ] TECH-033: The `codebase_index_context` parameter injection in `build_milestone_execution_prompt()` must be wrapped in `CODEBASE INTELLIGENCE CONTEXT` delimiters (review_cycles: 0)
- [ ] TECH-034: `_generate_role_section(role: str) -> str` private function in `claude_md_generator.py` must produce role-specific instructions for each of the 5 supported roles, returning a generic fallback for unknown roles (review_cycles: 0)
- [ ] TECH-035: `_generate_mcp_section(mcp_servers: dict, role: str) -> str` private function must list Contract Engine and Codebase Intelligence tools with parameter descriptions when their keys exist in mcp_servers dict (review_cycles: 0)
- [ ] TECH-036: `_generate_convergence_section(convergence_config: dict) -> str` private function must extract `min_convergence_ratio` from config dict and format convergence mandates as bullet list (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-009: Replace `get_mcp_servers(config)` call in cli.py (line ~170-250, mode selection block) with `get_contract_aware_servers(config)` when `config.contract_engine.enabled` or `config.codebase_intelligence.enabled` is True. `get_contract_aware_servers()` returns all standard servers plus Build 2 MCP servers, preserving existing servers dict structure. Assign result to the `mcp_servers` variable passed to orchestrator (review_cycles: 0)
- [ ] WIRE-010: Wire CLAUDE.md generation in `cli.py` before milestone execution when agent teams mode is active — call `generate_claude_md()` for each configured role with contracts and MCP servers (review_cycles: 0)
- [ ] WIRE-011: Wire `contract_context` and `codebase_index_context` into `build_orchestrator_prompt()` and `build_milestone_execution_prompt()` calls in `cli.py` — populate from Contract Engine and Codebase Intelligence query results (review_cycles: 0)
- [ ] WIRE-012: Wire contract report update in `cli.py` after CONTRACT scans — populate `_current_state.contract_report` with scan results (review_cycles: 0)
- [ ] WIRE-013: Wire `registered_artifacts` tracking in `cli.py` — after each milestone completion when `config.codebase_intelligence.register_artifacts` is True, call `register_new_artifact()` for newly created files. Determine newly created files by comparing `set(glob('**/*.py', '**/*.ts', '**/*.cs'))` before and after milestone execution, stored in milestone-local `_milestone_pre_files: set[str]` (review_cycles: 0)

### Test Requirements

- [ ] TEST-040: Test `generate_claude_md()` for all 5 roles produces non-empty string with role-specific sections (review_cycles: 0)
- [ ] TEST-041: Test `generate_claude_md()` includes MCP tools section when servers dict contains "contract-engine" and "codebase-intelligence" (review_cycles: 0)
- [ ] TEST-042: Test `generate_claude_md()` omits MCP tools section when servers dict is empty (review_cycles: 0)
- [ ] TEST-043: Test `generate_claude_md()` includes convergence mandates section with correct min_ratio from config (review_cycles: 0)
- [ ] TEST-044: Test `generate_claude_md()` truncates contracts list at `contract_limit` (default 100) with "... and N more. Use Contract Engine get_contract(contract_id) MCP tool to fetch additional contracts on demand." suffix (review_cycles: 0)
- [ ] TEST-045: Test `write_teammate_claude_md()` creates `.claude/CLAUDE.md` file with expected content and returns correct Path (review_cycles: 0)
- [ ] TEST-046: Test `ContractReport` and `EndpointTestReport` default to `health="unknown"` (review_cycles: 0)
- [ ] TEST-047: Test `build_orchestrator_prompt()` includes contract_context when provided, omits when empty (review_cycles: 0)
- [ ] TEST-048: Test `build_milestone_execution_prompt()` includes codebase_index_context when provided (review_cycles: 0)
- [ ] TEST-049: Test `_generate_role_section()` returns generic fallback for unknown role string (review_cycles: 0)

---

## Milestone 5: Contract Scans + Tracking + Verification

- ID: milestone-5
- Status: PENDING
- Dependencies: milestone-4
- Description: Implement CONTRACT-001..004 static scans, add contract compliance matrix to tracking documents, add contract-aware milestone health to milestone manager, add contract compliance verification function, and add CONTRACT_COMPLIANCE_STANDARDS and INTEGRATION_STANDARDS to code quality standards.

### Functional Requirements

- [ ] REQ-064: Create `src/agent_team/contract_scanner.py` with `run_contract_compliance_scan()` that runs all 4 CONTRACT scans with independent config gating and crash isolation (review_cycles: 0)
- [ ] REQ-065: Implement `run_endpoint_schema_scan(project_dir, contracts, scope)` (CONTRACT-001) — for each SVC-xxx contract or Contract Engine contract, find the implementing controller/route file, extract response DTO fields, compare against contracted field names and types, report mismatches as violations with severity "error" (review_cycles: 0)
- [ ] REQ-066: Implement `run_missing_endpoint_scan(project_dir, contracts, scope)` (CONTRACT-002) — for each contracted endpoint, search for matching route decorator or controller attribute in backend files, report missing endpoints as violations with severity "error" (review_cycles: 0)
- [ ] REQ-067: Implement `run_event_schema_scan(project_dir, contracts, scope)` (CONTRACT-003) — for each AsyncAPI contract, find publish/subscribe call sites, extract payload schema, compare against contracted schema, report mismatches with severity "error" (review_cycles: 0)
- [ ] REQ-068: Implement `run_shared_model_scan(project_dir, contracts, scope)` (CONTRACT-004) — for each JSON Schema shared model, find all TypeScript/Python/C# type definitions matching the model name, compare field names/types/optionality, check camelCase/snake_case mismatches, report drift with severity "error" (review_cycles: 0)
- [ ] REQ-069: All CONTRACT scan functions must accept `project_dir: Path`, `contracts: list[dict]`, `scope: ScanScope | None`, return `list[Violation]` capped at `_MAX_VIOLATIONS=100`, and check `(config.contract_engine.enabled OR _has_svc_table(requirements_path))` before scanning — return empty list if neither condition is met (prevents running scans when no contracts are available) (review_cycles: 0)
- [ ] REQ-070: Each scan in `run_contract_compliance_scan()` must be in its own `try/except` block with `logger.warning("CONTRACT-00N scan failed", exc_info=True)` (review_cycles: 0)
- [ ] REQ-071: Add `CONTRACT_COMPLIANCE_STANDARDS` constant to `code_quality_standards.py` defining CONTRACT-001 through CONTRACT-004 standards with descriptions and severity (review_cycles: 0)
- [ ] REQ-072: Add `INTEGRATION_STANDARDS` constant to `code_quality_standards.py` defining INT-001 (service discovery via env vars), INT-002 (trace ID propagation), INT-003 (error boundary), INT-004 (health endpoint) (review_cycles: 0)
- [ ] REQ-073: Map `CONTRACT_COMPLIANCE_STANDARDS` to code-writer, code-reviewer, and architect roles in `_AGENT_STANDARDS_MAP` in `code_quality_standards.py` (review_cycles: 0)
- [ ] REQ-074: Map `INTEGRATION_STANDARDS` to code-writer and code-reviewer roles in `_AGENT_STANDARDS_MAP` (review_cycles: 0)
- [ ] REQ-075: Add `generate_contract_compliance_matrix(project_dir, contracts, scan_results) -> str` to `tracking_documents.py` that produces `CONTRACT_COMPLIANCE_MATRIX.md` with tables for OpenAPI contracts, AsyncAPI contracts, and shared models. Add `contract_compliance_matrix: bool = True` field to `TrackingDocumentsConfig` in config.py. Add `CONTRACT_COMPLIANCE_MATRIX_FILE = 'CONTRACT_COMPLIANCE_MATRIX.md'` constant to tracking_documents.py (review_cycles: 0)
- [ ] REQ-076: Add `parse_contract_compliance_matrix(content: str) -> dict` to `tracking_documents.py` that parses the matrix document and returns a dict with total, implemented, verified, violated counts (review_cycles: 0)
- [ ] REQ-077: Add `update_contract_compliance_entry(content: str, contract_id: str, status: str) -> str` to `tracking_documents.py` that updates a single contract entry in the matrix after verification (review_cycles: 0)
- [ ] REQ-078: Add optional `contract_report: ContractReport | None = None` parameter to `check_milestone_health()` signature in `milestone_manager.py`. When contract_report is not None and `contract_report.total_contracts > 0`, compute `contract_compliance_ratio = contract_report.verified_contracts / contract_report.total_contracts` and use `min(checkbox_ratio, contract_compliance_ratio)` as the effective health ratio (review_cycles: 0)
- [ ] REQ-079: Add `verify_contract_compliance(project_dir: Path, contract_registry: ServiceContractRegistry | None) -> dict` to `verification.py` accepting project dir and registry, returning dict with `total_contracts`, `implemented`, `verified`, `violations`, `health` (review_cycles: 0)

### Technical Requirements

- [ ] TECH-037: `ContractScanConfig` dataclass with fields: `endpoint_schema_scan: bool = True`, `missing_endpoint_scan: bool = True`, `event_schema_scan: bool = True`, `shared_model_scan: bool = True` — in `config.py` (review_cycles: 0)
- [ ] TECH-038: Add `contract_scans: ContractScanConfig = field(default_factory=ContractScanConfig)` to root `AgentTeamConfig` in `config.py` (review_cycles: 0)
- [ ] TECH-039: Add `contract_scans` section parsing to `_dict_to_config()` following existing pattern (review_cycles: 0)
- [ ] TECH-040: Violations from CONTRACT scans must use the existing `Violation` dataclass from `quality_checks.py` with `.check` = "CONTRACT-001"|"CONTRACT-002"|"CONTRACT-003"|"CONTRACT-004" (review_cycles: 0)
- [ ] TECH-041: CONTRACT scans must use `ScanScope` for scoped scanning when `scan_scope_mode` is "changed" — only report violations for files in scope, but use full file list for detection phase (following H2 pattern from v6.0 review) (review_cycles: 0)
- [ ] TECH-042: CONTRACT-001 must extract response DTO fields using regex patterns for TypeScript interfaces/types, Python dataclasses/Pydantic models, and C# record/class DTOs (review_cycles: 0)
- [ ] TECH-043: CONTRACT-002 must detect route decorators across frameworks: `@app.route`/`@router.get` (Python), `[HttpGet]`/`[Route]` (C#), `router.get()` (Express), `@GetMapping` (Java) (review_cycles: 0)

### Wiring Requirements

- [ ] WIRE-014: Wire `run_contract_compliance_scan()` into `cli.py` post-orchestration scan pipeline AFTER the existing API contract scan block, gated on any contract_scans boolean being True (review_cycles: 0)
- [ ] WIRE-014A: In cli.py CONTRACT scan block, call `compute_changed_files(cwd, config.scan_scope_mode)` before running scans and pass result as `scope` parameter to all 4 CONTRACT scan functions. Follows existing pattern from v6.0 scan scope computation (review_cycles: 0)
- [ ] WIRE-015: Wire CONTRACT violation fix loop in `cli.py` using dedicated `_run_contract_fix(violations: list[Violation], scan_type: str, config: AgentTeamConfig)` function (following pattern of `_run_mock_data_fix()` and `_run_ui_compliance_fix()`) with 4 scan_type branches: `contract_endpoint_schema`, `contract_missing_endpoint`, `contract_event_schema`, `contract_shared_model` — each with specific fix prompts (review_cycles: 0)
- [ ] WIRE-016: Wire `generate_contract_compliance_matrix()` call into `cli.py` after CONTRACT scans, gated on `config.tracking_documents.e2e_coverage_matrix` (reuse existing tracking config gate) (review_cycles: 0)
- [ ] WIRE-017: Wire `verify_contract_compliance()` into `verification.py`'s `verify_task_completion()` as a new advisory phase after existing contract checks (review_cycles: 0)

### Depth Gating

- [ ] TECH-044: In `apply_depth_quality_gating()` (the actual function name in config.py), set depth gating for new features: quick = all contract scans off + contract_engine off + codebase_intelligence off + agent_teams off; standard = contract_engine enabled (validation_on_build=True, test_generation=False — this is "validation only" mode: validates contracts exist and match endpoints but does not auto-generate test files) + codebase_intelligence enabled (replace_static_map=False, register_artifacts=False — queries via find_definition/search_semantic only, codebase map uses static analysis) + CONTRACT 001-002 on; thorough = full contract_engine (test_generation=True) + full codebase_intelligence (replace_static_map=True, register_artifacts=True) + all 4 CONTRACT scans + agent_teams enabled (if env set); exhaustive = same as thorough with no differences. Note: depth-based defaults can be overridden by explicit YAML config — user overrides tracked via `set[str]` from `_dict_to_config()` take precedence over depth defaults (review_cycles: 0)

### Test Requirements

- [ ] TEST-050: Test `run_endpoint_schema_scan()` detects a deliberate field name mismatch between a SVC-xxx contract and a controller response DTO (review_cycles: 0)
- [ ] TEST-051: Test `run_missing_endpoint_scan()` detects a contracted endpoint with no corresponding route file (review_cycles: 0)
- [ ] TEST-052: Test `run_event_schema_scan()` detects mismatched event payload fields (review_cycles: 0)
- [ ] TEST-053: Test `run_shared_model_scan()` detects camelCase/snake_case drift across service type definitions (review_cycles: 0)
- [ ] TEST-054: Test `run_contract_compliance_scan()` combines all 4 scan results and caps at `_MAX_VIOLATIONS` (review_cycles: 0)
- [ ] TEST-055: Test each scan catches exceptions from other scans without affecting results (crash isolation) (review_cycles: 0)
- [ ] TEST-056: Test `CONTRACT_COMPLIANCE_STANDARDS` is mapped to code-writer, code-reviewer, architect in `_AGENT_STANDARDS_MAP` (review_cycles: 0)
- [ ] TEST-057: Test `INTEGRATION_STANDARDS` is mapped to code-writer and code-reviewer in `_AGENT_STANDARDS_MAP` (review_cycles: 0)
- [ ] TEST-058: Test `generate_contract_compliance_matrix()` produces valid markdown with OpenAPI and SharedModels tables (review_cycles: 0)
- [ ] TEST-059: Test `parse_contract_compliance_matrix()` correctly counts total, implemented, verified contracts (review_cycles: 0)
- [ ] TEST-060: Test `verify_contract_compliance()` returns "passed" when all contracts verified, "partial" when some violated, "failed" when majority violated (review_cycles: 0)
- [ ] TEST-061: Test `ContractScanConfig` defaults — all 4 scans enabled (review_cycles: 0)
- [ ] TEST-062: Test depth gating — quick disables all contract features, standard enables 001-002 only, thorough enables all 4 (review_cycles: 0)
- [ ] TEST-063: Test CONTRACT-001 field extraction works for TypeScript interfaces, Python dataclasses, and C# DTOs (review_cycles: 0)
- [ ] TEST-064: Test CONTRACT-002 route detection works for Python Flask/FastAPI, C# ASP.NET, and Express decorators (review_cycles: 0)
- [ ] TEST-065: Test `update_contract_compliance_entry()` correctly updates a single contract status in the matrix (review_cycles: 0)
- [ ] TEST-066: Test `check_milestone_health()` computes `min(checkbox_ratio, contract_compliance_ratio)` when contract report available (review_cycles: 0)

---

## Milestone 6: End-to-End Verification + Backward Compatibility

- ID: milestone-6
- Status: PENDING
- Dependencies: milestone-4, milestone-5
- Description: Add contract compliance E2E testing, extend tech research to detect Build 1 services, run full regression test suite to verify zero new regressions, and validate that disabling all Build 2 features produces identical v14.0 behavior.

### Functional Requirements

- [ ] REQ-080: Add `E2E_CONTRACT_COMPLIANCE_PROMPT` constant to `e2e_testing.py` that instructs the test agent to: (1) make HTTP requests to each SVC-xxx endpoint, (2) call `validate_endpoint()` via Contract Engine MCP with the response, (3) record pass/fail per contract, (4) write results to `CONTRACT_E2E_RESULTS.md` (review_cycles: 0)
- [ ] REQ-081: Add contract compliance E2E wiring in `cli.py` after standard E2E tests — when `config.contract_engine.enabled`, run contract compliance E2E with the `E2E_CONTRACT_COMPLIANCE_PROMPT` (review_cycles: 0)
- [ ] REQ-082: Extend `detect_app_type()` in `e2e_testing.py` to detect Build 1 MCP server availability by checking for `.mcp.json` with "contract-engine" or "codebase-intelligence" server entries (review_cycles: 0)
- [ ] REQ-083: Add Build 1 service detection to tech research queries in `tech_research.py` — when Contract Engine or Codebase Intelligence MCP configs are enabled, include their capabilities in tech research results (review_cycles: 0)
- [ ] REQ-084: All existing 5,410+ tests must pass with zero new regressions after Build 2 changes (review_cycles: 0)
- [ ] REQ-085: With all Build 2 features disabled (`agent_teams.enabled=False`, `contract_engine.enabled=False`, `codebase_intelligence.enabled=False`, all `contract_scans` booleans False), the system must behave identically to agent-team v14.0 (review_cycles: 0)

### Integration Requirements

- [ ] INT-001: Build 2 depends on Build 1's Contract Engine MCP server (9 tools) being available at the configured command/args — when unavailable, all features gracefully fall back to static scanning (review_cycles: 0)
- [ ] INT-002: Build 2 depends on Build 1's Codebase Intelligence MCP server (7 tools) being available at the configured command/args — when unavailable, codebase map generation falls back to existing static `generate_codebase_map()` (review_cycles: 0)
- [ ] INT-003: Build 2 depends on Build 1's Architect MCP server (4 tools) — `decompose()`, `get_service_map()`, `get_contracts_for_service()`, `get_domain_model()` — consumed during PRD decomposition phase when available. Create `ArchitectClient` class in `mcp_clients.py` following the same pattern as ContractEngineClient/CodebaseIntelligenceClient, wrapping all 4 tools with try/except returning empty defaults on failure. When unavailable, fallback to standard PRD decomposition using only the PRD text (no live service map queries) (review_cycles: 0)
- [ ] INT-004: Contract Engine MCP `validate_endpoint()` responses must match the schema `{ valid: boolean, violations: [{field: string, expected: string, actual: string}] }` — any schema change in Build 1 requires updating `ContractEngineClient` (review_cycles: 0)
- [ ] INT-005: Codebase Intelligence MCP `register_artifact()` must process files within 5 seconds — Build 2 code does not retry slow registrations (review_cycles: 0)
- [ ] INT-006: All new config sections (`agent_teams`, `contract_engine`, `codebase_intelligence`, `contract_scans`) must default to `enabled: False` so existing config.yaml files without these sections continue to work via `_dict_to_config()` backward compatibility (review_cycles: 0)
- [ ] INT-007: The existing `_dict_to_config()` tuple return type `tuple[AgentTeamConfig, set[str]]` must be preserved — callers must continue to unpack the tuple (review_cycles: 0)
- [ ] INT-008: The existing `Violation` dataclass interface (`.check`, `.file_path`, `.line`, `.message`, `.severity`) must be used for all CONTRACT scan violations — no new violation types (review_cycles: 0)
- [ ] INT-009: Claude Code Agent Teams integration is experimental and must not be required for any Build 2 functionality — every feature that uses Agent Teams must have a CLIBackend fallback path. Known limitations: no session resumption (if teammate crashes, state is lost), no nested teams, one team per session, split panes not supported on Windows Terminal, teammate permissions are set at spawn time and cannot be changed mid-session (review_cycles: 0)
- [ ] INT-010: Windows compatibility — all file operations must use `pathlib.Path`, all subprocess calls must handle Windows process model, all shell scripts must have Windows alternatives or graceful degradation (review_cycles: 0)

### Pipeline Preservation Checklist

- [ ] INT-011: 15-stage pipeline execution order in main() must be preserved (review_cycles: 0)
- [ ] INT-012: All 13 existing self-healing fix loops must continue to function (review_cycles: 0)
- [ ] INT-013: Post-orchestration scan chain order must be preserved — new CONTRACT scans added AFTER existing API contract scan (review_cycles: 0)
- [ ] INT-014: Milestone-based execution with MASTER_PLAN.md parsing must be preserved (review_cycles: 0)
- [ ] INT-015: Every scan/feature must remain config-gated with a boolean flag (review_cycles: 0)
- [ ] INT-016: Depth-based behavior (quick/standard/thorough/exhaustive) must be preserved with new features following established gating patterns (review_cycles: 0)
- [ ] INT-017: Signal handling (Ctrl+C) must save state including contract report and agent teams status (review_cycles: 0)
- [ ] INT-018: Resume from STATE.json must include contract state and agent teams note (review_cycles: 0)
- [ ] INT-019: ScanScope filtering must apply to CONTRACT scans — detection uses full file list, violation reporting scoped to changed files (review_cycles: 0)
- [ ] INT-020: `load_config()` tuple return type must be preserved (review_cycles: 0)

### Security Requirements

- [ ] SEC-001: MCP client connections must not pass `ANTHROPIC_API_KEY` or other secrets as MCP server environment variables — only pass database paths and configuration values (review_cycles: 0)
- [ ] SEC-002: Hook scripts written to `.claude/hooks/` must not contain embedded secrets — all secrets must come from environment variables at runtime (review_cycles: 0)
- [ ] SEC-003: `ServiceContractRegistry.save_local_cache()` must not write spec bodies containing authentication tokens — strip `securitySchemes` from OpenAPI specs before caching (review_cycles: 0)

### Test Requirements

- [ ] TEST-067: Integration test — mock Contract Engine MCP returning valid responses for all 6 tools, run pipeline end-to-end, verify contract report populated (review_cycles: 0)
- [ ] TEST-068: Integration test — mock Codebase Intelligence MCP returning valid responses for all 7 tools, run codebase map generation, verify MCP path taken (review_cycles: 0)
- [ ] TEST-069: Integration test — mock both MCP servers as unavailable, verify fallback to static analysis for both codebase map and contract verification (review_cycles: 0)
- [ ] TEST-070: Backward compat test — load config.yaml WITHOUT agent_teams/contract_engine/codebase_intelligence/contract_scans sections, verify all default to disabled (review_cycles: 0)
- [ ] TEST-071: Backward compat test — with all Build 2 features disabled, verify `get_mcp_servers()` returns same servers as v14.0 (review_cycles: 0)
- [ ] TEST-072: Backward compat test — with all Build 2 features disabled, verify post-orchestration scan pipeline executes same scans in same order as v14.0 (review_cycles: 0)
- [ ] TEST-073: Backward compat test — verify `_dict_to_config()` still returns `tuple[AgentTeamConfig, set[str]]` with correct user override tracking for new sections (review_cycles: 0)
- [ ] TEST-074: Backward compat test — verify all 4 new config dataclasses serialize to/from YAML correctly (review_cycles: 0)
- [ ] TEST-075: Regression test — run full existing test suite (5,410+ tests) and verify zero new failures (review_cycles: 0)
- [ ] TEST-076: Test `E2E_CONTRACT_COMPLIANCE_PROMPT` includes instructions for validate_endpoint() calls and CONTRACT_E2E_RESULTS.md output (review_cycles: 0)
- [ ] TEST-077: Test `detect_app_type()` correctly detects Build 1 MCP availability from `.mcp.json` (review_cycles: 0)
- [ ] TEST-078: Test MCP server fallback — ContractEngineClient returns safe defaults when MCP server process exits unexpectedly (review_cycles: 0)
- [ ] TEST-079: Test MCP server fallback — CodebaseIntelligenceClient returns safe defaults when MCP returns isError for all calls (review_cycles: 0)
- [ ] TEST-080: Backward compat test — verify `get_contract_aware_servers()` returns only standard servers when both contract_engine and codebase_intelligence are disabled (review_cycles: 0)
- [ ] TEST-081: Test CONTRACT scan pipeline order — CONTRACT scans run AFTER API contract scan in post-orchestration chain (review_cycles: 0)
- [ ] TEST-082: Test signal handler saves contract_report and agent_teams_active to STATE.json on Ctrl+C (review_cycles: 0)
- [ ] TEST-083: Test resume from STATE.json restores contract_report and notes agent teams were lost (review_cycles: 0)
- [ ] TEST-084: Integration test — Create AgentTeamsBackend, execute wave with mocked ContractEngineClient available, verify validate_endpoint() call pattern during code-writer task execution (review_cycles: 0)
- [ ] TEST-085: Integration test — Create CLIBackend (fallback), execute same wave without MCP, verify static run_api_contract_scan() is used (review_cycles: 0)
- [ ] TEST-086: Wiring test — Verify CLAUDE.md generated for code-writer role includes Contract Engine MCP tools section when config.contract_engine.enabled=True and omits when disabled (review_cycles: 0)
- [ ] TEST-087: Wiring test — Verify cli.py calls get_contract_aware_servers() when contract_engine.enabled or codebase_intelligence.enabled is True, preserving all existing servers from get_mcp_servers() (review_cycles: 0)
- [ ] TEST-088: Config test — Verify _dict_to_config() parses codebase_intelligence YAML section into CodebaseIntelligenceConfig with all fields (enabled, mcp_command, mcp_args, database_path, chroma_path, graph_path, replace_static_map, register_artifacts, server_root, startup_timeout_ms, tool_timeout_ms) (review_cycles: 0)
- [ ] TEST-089: Backward compat test — Verify `load_config()` returns `tuple[AgentTeamConfig, set[str]]` with correct user override tracking for new sections (agent_teams, contract_engine, codebase_intelligence, contract_scans) (review_cycles: 0)
- [ ] TEST-090: Test MCP session — ContractEngineClient returns safe defaults when MCP server process crashes mid-call (simulate with mocked session raising OSError) (review_cycles: 0)
- [ ] TEST-091: Test MCP session — ContractEngineClient returns safe defaults when MCP returns malformed JSON (not valid against expected schema) (review_cycles: 0)
- [ ] TEST-092: Test hook script — quality-gate.sh executes successfully with mock REQUIREMENTS.md (100% complete → exit 0, 50% complete → exit 2) (review_cycles: 0)
- [ ] TEST-093: Integration test — Run full pipeline with both MCPs enabled (mocked), verify STATE.json contains contract_report, integration_report, and registered_artifacts after phase completion (review_cycles: 0)
- [ ] TEST-094: Test CONTRACT scan pipeline order — CONTRACT scans run AFTER API contract scan and AFTER ScanScope computation in post-orchestration chain (review_cycles: 0)

---

## config.yaml Template (Build 2 Additions)

```yaml
# Build 2 additions — all default to disabled for backward compatibility

agent_teams:
  enabled: false
  fallback_to_cli: true
  delegate_mode: true
  max_teammates: 5
  teammate_model: ""
  teammate_permission_mode: "acceptEdits"
  teammate_idle_timeout: 300
  task_completed_hook: true
  wave_timeout_seconds: 3600
  task_timeout_seconds: 1800
  teammate_display_mode: "in-process"
  contract_limit: 100

contract_engine:
  enabled: false
  mcp_command: "python"
  mcp_args: ["-m", "src.contract_engine.mcp_server"]
  database_path: ""
  server_root: ""
  validation_on_build: true
  test_generation: true
  startup_timeout_ms: 30000
  tool_timeout_ms: 60000

codebase_intelligence:
  enabled: false
  mcp_command: "python"
  mcp_args: ["-m", "src.codebase_intelligence.mcp_server"]
  database_path: ""
  chroma_path: ""
  graph_path: ""
  server_root: ""
  replace_static_map: true
  register_artifacts: true
  startup_timeout_ms: 30000
  tool_timeout_ms: 60000

contract_scans:
  endpoint_schema_scan: true
  missing_endpoint_scan: true
  event_schema_scan: true
  shared_model_scan: true
```

## Depth Gating Summary

| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| agent_teams.enabled | False | False | True (if env set) | True (if env set) |
| contract_engine.enabled | False | True (validation only) | True (full) | True (full) |
| contract_engine.test_generation | False | False | True | True |
| codebase_intelligence.enabled | False | True (queries only) | True (full) | True (full) |
| codebase_intelligence.replace_static_map | False | False | True | True |
| codebase_intelligence.register_artifacts | False | False | True | True |
| CONTRACT scans 001-002 | False | True | True | True |
| CONTRACT scans 003-004 | False | False | True | True |
| All existing features | (unchanged from v14.0) | (unchanged) | (unchanged) | (unchanged) |

Note: Depth-based defaults can be overridden by explicit YAML config. User overrides tracked via `set[str]` from `_dict_to_config()` take precedence over depth defaults.

## Cross-Build Dependencies

| Build 2 Feature | Build 1 Dependency | Fallback When Unavailable |
|------------------|-------------------|---------------------------|
| ContractEngineClient | Contract Engine MCP server (6 tools) | Static `run_api_contract_scan()` from quality_checks.py |
| CodebaseIntelligenceClient | Codebase Intelligence MCP server (7 tools) | Static `generate_codebase_map()` from codebase_map.py |
| Architect MCP queries | Architect MCP server (4 tools) | Standard PRD decomposition without live queries |
| CONTRACT-001..004 scans | Contract data (from MCP or REQUIREMENTS.md SVC-xxx) | Scan uses SVC-xxx table from REQUIREMENTS.md only |
| Contract compliance E2E | Running Build 1 services | Skip contract E2E when services unavailable |

## Success Criteria

1. Builder uses Claude Code agent teams for internal coordination when enabled
2. Builder queries Contract Engine MCP and gets valid responses, falls back gracefully on failure
3. Builder queries Codebase Intelligence MCP and gets valid responses, falls back to static map on failure
4. CONTRACT-001..004 scans detect deliberate violations in test scenarios
5. All 5,410+ existing tests pass with zero new regressions
6. All Build 2 features disabled produces identical v14.0 behavior
7. Generated code registers with codebase index incrementally when MCP available
8. Hook configuration correctly prevents premature task completion and session stop
9. CLAUDE.md generated for all 5 roles contains role-specific instructions, MCP tool references, and convergence mandates
10. ServiceContractRegistry can load from MCP, cache locally, and fall back to local cache on MCP failure
