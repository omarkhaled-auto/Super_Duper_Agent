# Build 2 Architecture Plan — Builder Fleet Upgrade + Agent Teams Integration

> **Date:** 2026-02-14
> **Author:** architect-planner agent
> **Sources:** BUILD2_TECHNOLOGY_RESEARCH.md, BUILD2_CODEBASE_RESEARCH.md, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md, SUPER_TEAM_RESEARCH_REPORT.md, BUILD1_PRD.md, BUILD1_ARCHITECTURE_PLAN.md
> **Codebase:** agent-team v14.0 (28,749 LOC across 28 files, 5,410+ passing tests)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [New Files to Create](#2-new-files-to-create)
3. [Existing File Modifications](#3-existing-file-modifications)
4. [Data Flow Diagrams](#4-data-flow-diagrams)
5. [Hook Configuration Architecture](#5-hook-configuration-architecture)
6. [CLAUDE.md Generation Strategy](#6-claudemd-generation-strategy)
7. [Milestone Breakdown](#7-milestone-breakdown)
8. [Error Handling and Fallback Strategy](#8-error-handling-and-fallback-strategy)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Architecture Overview

### 1.1 System Diagram

```
                                    +-----------------------------------+
                                    |        SUPER ORCHESTRATOR         |
                                    |  (Python CLI — service-level)     |
                                    |  Spawns one Builder per service   |
                                    +---+------+-------+--------+------+
                                        |      |       |        |
                              +---------+  +---+---+  +--+---+  +------+
                              |            |       |  |      |         |
                     +--------v---+ +------v-+ +---v--v-+ +--v-------+|
                     | Builder A  | |Builder B| |Builder C| |Builder D||
                     | (Service 1)| |(Svc 2)  | |(Svc 3)  | |(Svc 4)  ||
                     +-----+------+ +----+----+ +----+----+ +----+----+|
                           |              |           |           |     |
                           |  ABSTRACTION LAYER (agent_teams_backend.py)|
                           |              |           |           |     |
                     +-----v--------------v-----------v-----------v----+
                     |          Execution Backend (Protocol)            |
                     |                                                  |
                     |   Mode A: AgentTeamsBackend                      |
                     |     - Claude Code native agent teams             |
                     |     - TaskCreate/TaskUpdate/SendMessage          |
                     |     - TeammateIdle + TaskCompleted hooks         |
                     |     - Delegate mode (lead coordinates only)      |
                     |                                                  |
                     |   Mode B: CLIBackend (fallback)                  |
                     |     - Existing subprocess orchestration          |
                     |     - Proven over 14 versions                    |
                     |     - _run_single() / _run_prd_milestones()      |
                     +---+-----------+-----------+---------------------+
                         |           |           |
              +----------v--+ +------v-----+ +---v--------------+
              | Contract     | | Codebase   | | Architect MCP    |
              | Engine MCP   | | Intel MCP  | | (Build 1)        |
              | (Build 1)    | | (Build 1)  | | 3 tools          |
              | 6 tools      | | 7 tools    | +------------------+
              +----------+---+ +------+-----+
                         |            |
                    +----v----+  +----v----+
                    |contracts|  |symbols  |
                    |.db      |  |.db      |
                    +---------+  |chroma/  |
                                 |graph.json|
                                 +---------+
```

**Two-Level Hierarchy (from SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md line 280):**

1. **Service-level parallelism** — Python CLI spawns one Builder per service directory. This is proven, reliable, our code. No changes to this layer.
2. **Within-service parallelism** — Each Builder either uses Claude Code Agent Teams (Mode A) or the existing subprocess model (Mode B) for internal coordination. The abstraction layer makes this transparent.

**Key Design Decision:** The Python CLI remains the top-level orchestrator. Agent Teams replaces only the within-Builder coordination. All 15 pipeline stages, 13 self-healing fix loops, and post-orchestration scan chains are preserved. The prompts, review criteria, convergence logic, and scan configurations are the intellectual property — they transfer into CLAUDE.md files for agent teams teammates.

### 1.2 Component Responsibilities

| Component | Responsibility | Mode A (Agent Teams) | Mode B (CLI Fallback) |
|-----------|---------------|---------------------|----------------------|
| **Team Lead** | Coordinates wave execution | Claude Code delegate mode | Python subprocess spawner |
| **Architect** | Designs service structure | Teammate with Architect MCP | Sub-orchestrator prompt |
| **Code Writer** | Implements code | Teammate with all MCPs | Sub-orchestrator prompt |
| **Code Reviewer** | Reviews code | Teammate with Read/Grep | Sub-orchestrator prompt |
| **Test Engineer** | Writes/runs tests | Teammate with Bash access | Sub-orchestrator prompt |
| **Wiring Verifier** | Cross-file checks | Teammate with Glob/Grep | Sub-orchestrator prompt |

### 1.3 Abstraction Boundary

The abstraction boundary sits between the scheduler (which computes WHAT to run and in what order via Kahn's algorithm, wave computation, and conflict detection) and the execution layer (which determines HOW to run tasks).

```
scheduler.py (unchanged)
    |
    | produces ExecutionWave objects
    |
    v
ExecutionBackend protocol (new)
    |
    +---> AgentTeamsBackend (Mode A)
    |       Maps TaskNode -> TaskCreate API
    |       Maps ExecutionWave -> parallel teammate assignments
    |       Uses hooks for quality gates
    |
    +---> CLIBackend (Mode B)
            Wraps existing _run_single()/_run_prd_milestones()
            Proven over 14 versions
```

---

## 2. New Files to Create

### 2.1 src/agent_team/agent_teams_backend.py (~550 lines)

**Purpose:** Abstraction layer enabling transparent switching between Claude Code Agent Teams and the existing subprocess-based orchestration. This is the most architecturally significant new file.

**Source:** SUPER_TEAM_RESEARCH_REPORT.md Correction 4, BUILD2_CODEBASE_RESEARCH.md Section 3.1

```python
"""
Agent Teams abstraction layer with fallback to CLI execution.

Provides a unified interface for task execution that can use either:
- Mode A: Claude Code Agent Teams (experimental, native coordination)
- Mode B: Current subprocess-based orchestration (proven, fallback)

The scheduler computes WHAT to run (waves, dependencies, conflicts).
The backend determines HOW to run it (agent teams vs subprocesses).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .config import AgentTeamConfig, AgentTeamsConfig
from .scheduler import TaskNode, ExecutionWave, TaskContext
from .state import RunState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TaskResult:
    """Result of executing a single task."""
    task_id: str
    status: str  # "completed" | "failed" | "timeout"
    output: str = ""
    error: str = ""
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    cost_usd: float = 0.0


@dataclass
class WaveResult:
    """Result of executing a wave of parallel tasks."""
    wave_index: int
    task_results: list[TaskResult] = field(default_factory=list)
    total_cost_usd: float = 0.0
    all_succeeded: bool = False


@dataclass
class TeamState:
    """Tracks the state of an agent team or CLI execution session."""
    mode: str  # "agent_teams" | "cli"
    active: bool = False
    teammates: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Execution Backend Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class ExecutionBackend(Protocol):
    """Abstract interface for task execution backends.

    The scheduler produces waves of TaskNode objects. The backend executes them.
    This protocol enables transparent switching between Agent Teams and CLI modes.
    """

    async def initialize(self, config: AgentTeamConfig, project_dir: Path) -> TeamState:
        """Initialize the execution backend. Returns initial state."""
        ...

    async def execute_wave(
        self,
        wave: ExecutionWave,
        context: dict[str, Any],
        state: TeamState,
    ) -> WaveResult:
        """Execute a wave of parallel tasks. Returns results for all tasks."""
        ...

    async def execute_task(
        self,
        task: TaskNode,
        context: TaskContext,
        state: TeamState,
    ) -> TaskResult:
        """Execute a single task. Returns the result."""
        ...

    async def send_context(
        self,
        state: TeamState,
        recipient: str,
        content: str,
    ) -> bool:
        """Send context/instructions to a specific agent. Returns success."""
        ...

    async def shutdown(self, state: TeamState) -> None:
        """Gracefully shut down all agents/processes."""
        ...

    def supports_peer_messaging(self) -> bool:
        """Whether agents can message each other directly."""
        ...

    def supports_self_claiming(self) -> bool:
        """Whether agents auto-claim next available tasks."""
        ...


# ---------------------------------------------------------------------------
# Agent Teams Backend (Mode A)
# ---------------------------------------------------------------------------

class AgentTeamsBackend:
    """Claude Code Agent Teams execution backend.

    Uses native agent teams for within-service coordination:
    - TaskCreate/TaskUpdate for task management
    - SendMessage for peer-to-peer messaging
    - Delegate mode: lead coordinates only, never implements
    - Hooks enforce convergence mandates and review guardrails

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 1
    """

    def __init__(self) -> None:
        self._claude_cmd: str = "claude"
        self._env: dict[str, str] = {}

    async def initialize(self, config: AgentTeamConfig, project_dir: Path) -> TeamState:
        """Set up agent teams environment.

        1. Verify Claude Code is available and agent teams is enabled
        2. Generate CLAUDE.md for the project
        3. Generate hooks configuration
        4. Generate .mcp.json with Build 1 MCP servers
        5. Set up .claude/settings.json with permissions
        """
        state = TeamState(mode="agent_teams")

        # Verify claude CLI is available
        if not self._verify_claude_available():
            raise RuntimeError("Claude Code CLI not found. Install from https://claude.com/code")

        # Set up environment
        self._env = {
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        }

        if config.agent_teams.teammate_model:
            self._env["CLAUDE_CODE_SUBAGENT_MODEL"] = config.agent_teams.teammate_model

        state.active = True
        return state

    async def execute_wave(
        self,
        wave: ExecutionWave,
        context: dict[str, Any],
        state: TeamState,
    ) -> WaveResult:
        """Execute a wave by creating tasks in the agent teams task list.

        Agent teams handles parallelism natively — teammates self-claim
        unblocked tasks. We create all tasks in the wave, set up dependencies,
        and poll until all complete or timeout.
        """
        result = WaveResult(wave_index=wave.index)
        # Implementation: create TaskCreate calls for each task in wave,
        # set up dependencies via TaskUpdate(addBlockedBy=[...]),
        # poll TaskList until all completed or timeout
        return result

    async def execute_task(
        self,
        task: TaskNode,
        context: TaskContext,
        state: TeamState,
    ) -> TaskResult:
        """Execute a single task via agent teams.

        Creates a task in the shared task list and waits for a teammate
        to claim and complete it.
        """
        return TaskResult(task_id=task.id, status="completed")

    async def send_context(
        self,
        state: TeamState,
        recipient: str,
        content: str,
    ) -> bool:
        """Send context to a teammate via SendMessage."""
        return True

    async def shutdown(self, state: TeamState) -> None:
        """Send shutdown_request to all active teammates."""
        state.active = False

    def supports_peer_messaging(self) -> bool:
        return True

    def supports_self_claiming(self) -> bool:
        return True

    def _verify_claude_available(self) -> bool:
        """Check if claude CLI is on PATH."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


# ---------------------------------------------------------------------------
# CLI Backend (Mode B — fallback)
# ---------------------------------------------------------------------------

class CLIBackend:
    """Existing subprocess-based execution (proven fallback).

    Wraps the current _run_single() / _run_prd_milestones() logic from cli.py.
    This is the proven execution path used over 14 versions of the agent-team.

    Reference: BUILD2_CODEBASE_RESEARCH.md Section 2.1
    """

    def __init__(self) -> None:
        self._backend: str = ""  # "claude" | "claude-code" | "api"

    async def initialize(self, config: AgentTeamConfig, project_dir: Path) -> TeamState:
        """Initialize CLI backend using existing _detect_backend() logic."""
        state = TeamState(mode="cli")
        self._backend = config.orchestrator.backend
        state.active = True
        return state

    async def execute_wave(
        self,
        wave: ExecutionWave,
        context: dict[str, Any],
        state: TeamState,
    ) -> WaveResult:
        """Execute a wave using subprocess parallelism."""
        result = WaveResult(wave_index=wave.index)
        # Implementation: spawn subprocesses for each task in wave,
        # collect results via stdout/stderr parsing
        return result

    async def execute_task(
        self,
        task: TaskNode,
        context: TaskContext,
        state: TeamState,
    ) -> TaskResult:
        """Execute a single task as a subprocess."""
        return TaskResult(task_id=task.id, status="completed")

    async def send_context(
        self,
        state: TeamState,
        recipient: str,
        content: str,
    ) -> bool:
        """CLI mode does not support peer messaging."""
        return False

    async def shutdown(self, state: TeamState) -> None:
        """Terminate any running subprocesses."""
        state.active = False

    def supports_peer_messaging(self) -> bool:
        return False

    def supports_self_claiming(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_execution_backend(config: AgentTeamConfig) -> ExecutionBackend:
    """Factory: returns appropriate backend based on config and environment.

    Decision logic:
    1. If config.agent_teams.enabled is False -> CLIBackend
    2. If CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var is not set -> CLIBackend
    3. If claude CLI is not available -> CLIBackend (with warning)
    4. Otherwise -> AgentTeamsBackend

    Reference: SUPER_TEAM_RESEARCH_REPORT.md Correction 4 — abstraction layer
    """
    if not config.agent_teams.enabled:
        logger.info("Agent Teams disabled in config, using CLI backend")
        return CLIBackend()

    if not os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"):
        logger.info("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS not set, using CLI backend")
        return CLIBackend()

    backend = AgentTeamsBackend()
    if not backend._verify_claude_available():
        logger.warning("Claude Code CLI not found, falling back to CLI backend")
        if config.agent_teams.fallback_to_cli:
            return CLIBackend()
        raise RuntimeError("Agent Teams enabled but Claude Code CLI not found")

    logger.info("Using Agent Teams backend")
    return backend


def detect_agent_teams_available() -> bool:
    """Check if Claude Code Agent Teams is available in this environment.

    Returns True if:
    - CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is set
    - claude CLI is on PATH
    - Running in a terminal (not headless)
    """
    if not os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"):
        return False
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
```

**Dependencies:** config.py (AgentTeamConfig, AgentTeamsConfig), scheduler.py (TaskNode, ExecutionWave, TaskContext), state.py (RunState)

---

### 2.2 src/agent_team/contract_client.py (~350 lines)

**Purpose:** Typed MCP client for communicating with Build 1's Contract Engine. Wraps the 6 Contract Engine MCP tools with proper error handling and fallback to local static scans.

**Source:** BUILD2_TECHNOLOGY_RESEARCH.md Sections 3 and 7.2, BUILD1_PRD.md REQ-060

```python
"""
MCP client for Build 1's Contract Engine.

Provides typed wrappers around the 6 Contract Engine MCP tools:
- get_contract(contract_id)
- validate_endpoint(service_name, method, path, response_body, status_code)
- generate_tests(contract_id, framework, include_negative)
- check_breaking_changes(contract_id, new_spec)
- mark_implemented(contract_id, service_name, evidence_path)
- get_unimplemented_contracts(service_name)

Uses MCP Python SDK client: stdio_client() + ClientSession + call_tool()
Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


@dataclass
class ContractValidation:
    """Result of validating an endpoint against its contract."""
    valid: bool = False
    violations: list[dict[str, str]] = field(default_factory=list)
    error: str = ""


@dataclass
class ContractInfo:
    """A contract retrieved from the Contract Engine."""
    id: str = ""
    type: str = ""
    version: str = ""
    service_name: str = ""
    spec: dict[str, Any] = field(default_factory=dict)
    spec_hash: str = ""
    status: str = ""


class ContractEngineClient:
    """Typed MCP client for Contract Engine.

    Every method has a try/except that returns a safe default on MCP failure.
    The caller can check the result and fall back to static scanning.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3-3.5
    """

    def __init__(self, session: Any) -> None:
        """Initialize with an MCP ClientSession.

        Args:
            session: An initialized mcp.ClientSession instance.
        """
        self._session = session

    async def get_contract(self, contract_id: str) -> ContractInfo | None:
        """Get a contract by ID.

        Maps to Contract Engine MCP tool: get_contract(contract_id: str)
        Reference: BUILD1_PRD.md REQ-060
        """
        try:
            result = await self._session.call_tool(
                "get_contract",
                arguments={"contract_id": contract_id},
            )
            if result.isError:
                logger.warning("get_contract(%s) returned error", contract_id)
                return None
            data = self._extract_json(result)
            if data is None:
                return None
            return ContractInfo(
                id=data.get("id", ""),
                type=data.get("type", ""),
                version=data.get("version", ""),
                service_name=data.get("service_name", ""),
                spec=data.get("spec", {}),
                spec_hash=data.get("spec_hash", ""),
                status=data.get("status", ""),
            )
        except Exception:
            logger.warning("MCP call get_contract(%s) failed", contract_id, exc_info=True)
            return None

    async def validate_endpoint(
        self,
        service_name: str,
        method: str,
        path: str,
        response_body: dict[str, Any],
        status_code: int = 200,
    ) -> ContractValidation:
        """Validate an endpoint implementation against its contract.

        Maps to Contract Engine MCP tool: validate_endpoint(...)
        Reference: BUILD1_PRD.md REQ-060, BUILD2_CODEBASE_RESEARCH.md Section 2.3.3
        """
        try:
            result = await self._session.call_tool(
                "validate_endpoint",
                arguments={
                    "service_name": service_name,
                    "method": method,
                    "path": path,
                    "response_body": response_body,
                    "status_code": status_code,
                },
            )
            if result.isError:
                return ContractValidation(error="MCP tool returned error")
            data = self._extract_json(result)
            if data is None:
                return ContractValidation(error="Failed to parse response")
            return ContractValidation(
                valid=data.get("valid", False),
                violations=data.get("violations", []),
            )
        except Exception:
            logger.warning("MCP call validate_endpoint failed", exc_info=True)
            return ContractValidation(error="MCP connection failed")

    async def generate_tests(
        self,
        contract_id: str,
        framework: str = "pytest",
        include_negative: bool = True,
    ) -> str:
        """Generate runnable test code from a contract.

        Maps to Contract Engine MCP tool: generate_tests(...)
        Reference: BUILD1_PRD.md REQ-060
        """
        try:
            result = await self._session.call_tool(
                "generate_tests",
                arguments={
                    "contract_id": contract_id,
                    "framework": framework,
                    "include_negative": include_negative,
                },
            )
            if result.isError:
                return ""
            return self._extract_text(result)
        except Exception:
            logger.warning("MCP call generate_tests failed", exc_info=True)
            return ""

    async def check_breaking_changes(
        self,
        contract_id: str,
        new_spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Check if spec changes would break consumers.

        Maps to Contract Engine MCP tool: check_breaking_changes(...)
        Reference: BUILD1_PRD.md REQ-060
        """
        try:
            result = await self._session.call_tool(
                "check_breaking_changes",
                arguments={
                    "contract_id": contract_id,
                    "new_spec": new_spec,
                },
            )
            if result.isError:
                return []
            data = self._extract_json(result)
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("MCP call check_breaking_changes failed", exc_info=True)
            return []

    async def mark_implemented(
        self,
        contract_id: str,
        service_name: str,
        evidence_path: str,
    ) -> dict[str, Any]:
        """Mark a contract as implemented by a service.

        Maps to Contract Engine MCP tool: mark_implemented(...)
        Reference: BUILD1_PRD.md REQ-060, SUPER_TEAM_RESEARCH_REPORT.md GAP 3
        """
        try:
            result = await self._session.call_tool(
                "mark_implemented",
                arguments={
                    "contract_id": contract_id,
                    "service_name": service_name,
                    "evidence_path": evidence_path,
                },
            )
            if result.isError:
                return {"marked": False}
            data = self._extract_json(result)
            return data if isinstance(data, dict) else {"marked": False}
        except Exception:
            logger.warning("MCP call mark_implemented failed", exc_info=True)
            return {"marked": False}

    async def get_unimplemented_contracts(
        self,
        service_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all contracts that haven't been implemented yet.

        Maps to Contract Engine MCP tool: get_unimplemented_contracts(...)
        Reference: BUILD1_PRD.md REQ-060
        """
        try:
            args: dict[str, Any] = {}
            if service_name:
                args["service_name"] = service_name
            result = await self._session.call_tool(
                "get_unimplemented_contracts",
                arguments=args,
            )
            if result.isError:
                return []
            data = self._extract_json(result)
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("MCP call get_unimplemented_contracts failed", exc_info=True)
            return []

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _extract_json(self, result: Any) -> Any:
        """Extract JSON data from MCP CallToolResult.

        Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.4
        """
        if not result.content:
            return None
        for content in result.content:
            if hasattr(content, "text"):
                try:
                    return json.loads(content.text)
                except (json.JSONDecodeError, TypeError):
                    return None
        return None

    def _extract_text(self, result: Any) -> str:
        """Extract plain text from MCP CallToolResult."""
        if not result.content:
            return ""
        for content in result.content:
            if hasattr(content, "text"):
                return content.text
        return ""
```

---

### 2.3 src/agent_team/codebase_client.py (~300 lines)

**Purpose:** Typed MCP client for Build 1's Codebase Intelligence service. Wraps 7 MCP tools.

**Source:** BUILD2_TECHNOLOGY_RESEARCH.md Section 7.3, BUILD1_PRD.md REQ-057

```python
"""
MCP client for Build 1's Codebase Intelligence service.

Provides typed wrappers around the 7 Codebase Intelligence MCP tools:
- find_definition(symbol, language)
- find_callers(symbol, max_results)
- find_dependencies(file_path)
- search_semantic(query, n_results)
- get_service_interface(service_name)
- check_dead_code(service_name)
- register_artifact(file_path, service_name)

Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3, BUILD1_PRD.md REQ-057
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DefinitionResult:
    """Result from find_definition."""
    file: str = ""
    line: int = 0
    kind: str = ""
    signature: str = ""
    found: bool = False


@dataclass
class DependencyResult:
    """Result from find_dependencies."""
    imports: list[str] = field(default_factory=list)
    imported_by: list[str] = field(default_factory=list)
    transitive_deps: list[str] = field(default_factory=list)
    circular_deps: list[list[str]] = field(default_factory=list)


@dataclass
class ArtifactResult:
    """Result from register_artifact."""
    indexed: bool = False
    symbols_found: int = 0
    dependencies_found: int = 0


class CodebaseIntelligenceClient:
    """Typed MCP client for Codebase Intelligence.

    Every method has a try/except that returns a safe default on MCP failure.
    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3-3.5
    """

    def __init__(self, session: Any) -> None:
        self._session = session

    async def find_definition(
        self, symbol: str, language: str | None = None
    ) -> DefinitionResult:
        """Find where a symbol is defined."""
        try:
            args: dict[str, Any] = {"symbol": symbol}
            if language:
                args["language"] = language
            result = await self._session.call_tool("find_definition", arguments=args)
            if result.isError:
                return DefinitionResult()
            data = self._extract_json(result)
            if not data:
                return DefinitionResult()
            return DefinitionResult(
                file=data.get("file", ""),
                line=data.get("line", 0),
                kind=data.get("kind", ""),
                signature=data.get("signature", ""),
                found=True,
            )
        except Exception:
            logger.warning("MCP call find_definition(%s) failed", symbol, exc_info=True)
            return DefinitionResult()

    async def find_callers(
        self, symbol: str, max_results: int = 50
    ) -> list[dict[str, Any]]:
        """Find all call sites for a symbol."""
        try:
            result = await self._session.call_tool(
                "find_callers",
                arguments={"symbol": symbol, "max_results": max_results},
            )
            if result.isError:
                return []
            data = self._extract_json(result)
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("MCP call find_callers(%s) failed", symbol, exc_info=True)
            return []

    async def find_dependencies(self, file_path: str) -> DependencyResult:
        """Get the dependency graph for a file."""
        try:
            result = await self._session.call_tool(
                "find_dependencies",
                arguments={"file_path": file_path},
            )
            if result.isError:
                return DependencyResult()
            data = self._extract_json(result)
            if not data or not isinstance(data, dict):
                return DependencyResult()
            return DependencyResult(
                imports=data.get("imports", []),
                imported_by=data.get("imported_by", []),
                transitive_deps=data.get("transitive_deps", []),
                circular_deps=data.get("circular_deps", []),
            )
        except Exception:
            logger.warning("MCP call find_dependencies failed", exc_info=True)
            return DependencyResult()

    async def search_semantic(
        self, query: str, n_results: int = 10
    ) -> list[dict[str, Any]]:
        """Semantic search across the codebase."""
        try:
            result = await self._session.call_tool(
                "search_semantic",
                arguments={"query": query, "n_results": n_results},
            )
            if result.isError:
                return []
            data = self._extract_json(result)
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("MCP call search_semantic failed", exc_info=True)
            return []

    async def get_service_interface(
        self, service_name: str
    ) -> dict[str, Any]:
        """Get all public APIs and events for a service."""
        try:
            result = await self._session.call_tool(
                "get_service_interface",
                arguments={"service_name": service_name},
            )
            if result.isError:
                return {}
            data = self._extract_json(result)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.warning("MCP call get_service_interface failed", exc_info=True)
            return {}

    async def check_dead_code(
        self, service_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Find symbols defined but never referenced."""
        try:
            args: dict[str, Any] = {}
            if service_name:
                args["service_name"] = service_name
            result = await self._session.call_tool("check_dead_code", arguments=args)
            if result.isError:
                return []
            data = self._extract_json(result)
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("MCP call check_dead_code failed", exc_info=True)
            return []

    async def register_artifact(
        self, file_path: str, service_name: str
    ) -> ArtifactResult:
        """Register a newly generated file for indexing.

        Reference: SUPER_TEAM_RESEARCH_REPORT.md GAP 7
        """
        try:
            result = await self._session.call_tool(
                "register_artifact",
                arguments={"file_path": file_path, "service_name": service_name},
            )
            if result.isError:
                return ArtifactResult()
            data = self._extract_json(result)
            if not data or not isinstance(data, dict):
                return ArtifactResult()
            return ArtifactResult(
                indexed=data.get("indexed", False),
                symbols_found=data.get("symbols_found", 0),
                dependencies_found=data.get("dependencies_found", 0),
            )
        except Exception:
            logger.warning("MCP call register_artifact failed", exc_info=True)
            return ArtifactResult()

    def _extract_json(self, result: Any) -> Any:
        """Extract JSON data from MCP CallToolResult."""
        if not result.content:
            return None
        for content in result.content:
            if hasattr(content, "text"):
                try:
                    return json.loads(content.text)
                except (json.JSONDecodeError, TypeError):
                    return None
        return None
```

---

### 2.4 src/agent_team/hooks_manager.py (~250 lines)

**Purpose:** Generate Claude Code hook configurations for agent teams enforcement. Hooks replace Python-side enforcement (GATE 5, convergence checks) with native Claude Code mechanisms.

**Source:** BUILD2_TECHNOLOGY_RESEARCH.md Section 2, SUPER_TEAM_RESEARCH_REPORT.md GAP 1

```python
"""
Hook configuration generator for agent teams convergence enforcement.

Generates .claude/settings.json hook entries that enforce:
1. TaskCompleted — verify all requirements met before marking task complete
2. TeammateIdle — rebalance workload if tasks remain
3. Stop — final quality gate verification
4. PostToolUse on Write|Edit — track file changes for contract validation

Hook types used:
- "command" hooks: shell scripts for fast checks (test runner, lint)
- "agent" hooks: multi-turn subagent verification (convergence, contract compliance)

Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 2.1-2.9
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AgentTeamConfig

logger = logging.getLogger(__name__)


@dataclass
class HookConfig:
    """Complete hook configuration for a project."""
    hooks: dict[str, list[dict[str, Any]]]
    scripts: dict[str, str]  # script_name -> script_content


def generate_hooks_config(
    config: AgentTeamConfig,
    project_dir: Path,
    requirements_path: Path | None = None,
) -> HookConfig:
    """Generate complete hooks configuration for agent teams enforcement.

    Returns HookConfig with:
    - hooks: Dict for .claude/settings.json "hooks" section
    - scripts: Shell scripts to write to .claude/hooks/
    """
    hooks: dict[str, list[dict[str, Any]]] = {}
    scripts: dict[str, str] = {}

    # 1. TaskCompleted hook — convergence verification
    if config.agent_teams.task_completed_hook:
        tc_hook = generate_task_completed_hook(requirements_path)
        hooks["TaskCompleted"] = [tc_hook]

    # 2. TeammateIdle hook — workload rebalancing
    hooks["TeammateIdle"] = [generate_teammate_idle_hook()]

    # 3. Stop hook — final quality gate
    stop_hook, stop_script = generate_stop_hook(config)
    hooks["Stop"] = [stop_hook]
    scripts["quality-gate.sh"] = stop_script

    return HookConfig(hooks=hooks, scripts=scripts)


def generate_task_completed_hook(
    requirements_path: Path | None = None,
) -> dict[str, Any]:
    """Generate TaskCompleted hook that verifies convergence.

    Uses "agent" hook type for multi-turn verification with tool access.
    The agent reads REQUIREMENTS.md and verifies all [x] items.
    Exit code 2 prevents task completion if verification fails.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 2.6 (TaskCompleted)
    SUPER_TEAM_RESEARCH_REPORT.md GAP 1 (agent hook for convergence)
    """
    req_file = str(requirements_path) if requirements_path else "REQUIREMENTS.md"

    return {
        "hooks": [{
            "type": "agent",
            "prompt": (
                f"Read {req_file}. Check every requirement line. "
                "For each [ ] (unchecked) item, verify if the implementation "
                "for this specific task addresses it. "
                "If the task's implementation does NOT satisfy all requirements "
                "it claims to address, respond with ok: false and explain "
                "what is missing. If all claimed requirements are satisfied, "
                "respond with ok: true."
            ),
            "model": "",  # Use default fast model
            "timeout": 120,
        }],
    }


def generate_teammate_idle_hook() -> dict[str, Any]:
    """Generate TeammateIdle hook that rebalances work.

    When a teammate finishes all assigned work and goes idle:
    1. Check if there are pending tasks in the task list
    2. If yes, exit code 2 prevents idle (keeps working)
    3. If no pending tasks, allow idle

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 2.6 (TeammateIdle)
    """
    return {
        "hooks": [{
            "type": "agent",
            "prompt": (
                "Use TaskList to check for pending tasks. "
                "If there are tasks with status 'pending' and no blockedBy, "
                "respond with ok: false and reason: 'Pending tasks available'. "
                "If all tasks are completed or blocked, respond with ok: true."
            ),
            "timeout": 30,
        }],
    }


def generate_stop_hook(
    config: AgentTeamConfig,
) -> tuple[dict[str, Any], str]:
    """Generate Stop hook for final quality gate.

    Uses "command" hook type that runs a shell script.
    The script checks:
    1. All tasks in task list are completed
    2. No CRITICAL scan violations remain
    3. Convergence health is "passed" or "partial"

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 2.1 (Stop event)
    """
    script = """#!/bin/bash
# Quality gate script — runs before session can stop
# Exit 0: allow stop. Exit 2: block stop with feedback.

INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd','.'))")

# Check for REQUIREMENTS.md completion
if [ -f "$CWD/REQUIREMENTS.md" ]; then
    TOTAL=$(grep -cE '^\\s*-\\s*\\[' "$CWD/REQUIREMENTS.md" 2>/dev/null || echo 0)
    DONE=$(grep -cE '^\\s*-\\s*\\[x\\]' "$CWD/REQUIREMENTS.md" 2>/dev/null || echo 0)
    if [ "$TOTAL" -gt 0 ] && [ "$DONE" -lt "$TOTAL" ]; then
        echo "Requirements incomplete: $DONE/$TOTAL checked. Complete remaining requirements." >&2
        exit 2
    fi
fi

exit 0
"""
    hook = {
        "hooks": [{
            "type": "command",
            "command": ".claude/hooks/quality-gate.sh",
            "timeout": 30,
            "statusMessage": "Running quality gate...",
        }],
    }
    return hook, script


def write_hooks_to_project(
    project_dir: Path,
    hook_config: HookConfig,
) -> None:
    """Write hook configuration and scripts to the project directory.

    Creates:
    - .claude/settings.local.json with hooks section
    - .claude/hooks/*.sh scripts (executable)
    """
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir(exist_ok=True)
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Write settings.local.json (local, not committed)
    settings_path = claude_dir / "settings.local.json"
    settings: dict[str, Any] = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    settings["hooks"] = hook_config.hooks
    settings_path.write_text(
        json.dumps(settings, indent=2) + "\n",
        encoding="utf-8",
    )

    # Write hook scripts
    for script_name, script_content in hook_config.scripts.items():
        script_path = hooks_dir / script_name
        script_path.write_text(script_content, encoding="utf-8")
        # Make executable on Unix
        try:
            script_path.chmod(0o755)
        except OSError:
            pass  # Windows doesn't need chmod

    logger.info("Wrote hooks config to %s", settings_path)
```

---

### 2.5 src/agent_team/claude_md_generator.py (~350 lines)

**Purpose:** Generate CLAUDE.md files that transfer prompt engineering from agents.py into the format that Claude Code agent teams teammates load automatically.

**Source:** SUPER_TEAM_RESEARCH_REPORT.md GAP 2, BUILD2_TECHNOLOGY_RESEARCH.md Section 4

```python
"""
CLAUDE.md generation for agent teams teammates.

Claude Code teammates automatically load CLAUDE.md from their working directory.
They do NOT inherit the lead's conversation history. Therefore, all prompt
engineering (from agents.py) must transfer into CLAUDE.md files.

Each teammate gets a CLAUDE.md that includes:
1. Role-specific instructions (architect, code-writer, reviewer, test-engineer)
2. Service-specific context (contracts, dependencies, tech stack)
3. MCP server usage instructions (Contract Engine, Codebase Intelligence)
4. Quality standards and scan directives
5. Convergence mandates and review criteria

Reference:
- BUILD2_TECHNOLOGY_RESEARCH.md Section 4 (CLAUDE.md format)
- SUPER_TEAM_RESEARCH_REPORT.md GAP 2 (generation strategy)
- BUILD2_CODEBASE_RESEARCH.md Section 2.2 (agents.py prompt templates)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .config import AgentTeamConfig

logger = logging.getLogger(__name__)


def generate_claude_md(
    role: str,
    service_name: str,
    contracts: list[dict[str, Any]],
    dependencies: list[str],
    mcp_servers: dict[str, Any],
    quality_standards: str,
    convergence_config: dict[str, Any],
    tech_stack: str = "",
    codebase_context: str = "",
) -> str:
    """Generate complete CLAUDE.md content for a teammate.

    Args:
        role: "architect" | "code-writer" | "code-reviewer" | "test-engineer" | "wiring-verifier"
        service_name: Name of the service being built
        contracts: List of contract dicts from Contract Engine
        dependencies: List of service dependency names
        mcp_servers: MCP server configurations available to this teammate
        quality_standards: Quality standards text (from code_quality_standards.py)
        convergence_config: Dict with convergence thresholds
        tech_stack: Technology stack description
        codebase_context: Codebase map or index summary

    Returns:
        Complete CLAUDE.md content as a string
    """
    sections: list[str] = []

    # Header
    sections.append(f"# {role.replace('-', ' ').title()} Instructions — {service_name}\n")

    # Role-specific instructions
    sections.append(_generate_role_section(role))

    # Service context
    sections.append(_generate_service_section(service_name, dependencies, tech_stack))

    # Contract awareness
    if contracts:
        sections.append(_generate_contract_section(contracts, role))

    # MCP server instructions
    if mcp_servers:
        sections.append(_generate_mcp_section(mcp_servers, role))

    # Quality standards
    if quality_standards:
        sections.append(f"## Quality Standards\n\n{quality_standards}\n")

    # Convergence mandates
    sections.append(_generate_convergence_section(convergence_config))

    # Codebase context
    if codebase_context:
        sections.append(f"## Codebase Context\n\n{codebase_context}\n")

    return "\n---\n\n".join(sections)


def _generate_role_section(role: str) -> str:
    """Generate role-specific instructions.

    These map to the prompt templates in agents.py:
    - ARCHITECT_PROMPT (agents.py lines 1-150)
    - CODE_WRITER_PROMPT (agents.py lines 150-500)
    - CODE_REVIEWER_PROMPT (agents.py lines 500-700)
    """
    templates = {
        "architect": (
            "## Role: Architect\n\n"
            "You design the service structure, define API contracts, and create the "
            "REQUIREMENTS.md file. You must:\n"
            "- Query Contract Engine MCP for existing contracts before designing\n"
            "- Query Codebase Intelligence MCP for understanding existing code\n"
            "- Generate contract stubs in SVC-xxx format\n"
            "- Include EXACT FIELD SCHEMAS in SVC-xxx tables\n"
            "- Validate all cross-service boundaries have contracts\n"
        ),
        "code-writer": (
            "## Role: Code Writer\n\n"
            "You implement code against requirements and contracts. You must:\n"
            "- Follow the ZERO MOCK DATA POLICY — never use placeholder/hardcoded data\n"
            "- Follow API CONTRACT COMPLIANCE — use exact field names from SVC-xxx\n"
            "- Call validate_endpoint() via Contract Engine MCP after each API endpoint\n"
            "- Call register_artifact() via Codebase Intelligence MCP after each new file\n"
            "- Follow UI COMPLIANCE POLICY if frontend work is involved\n"
        ),
        "code-reviewer": (
            "## Role: Code Reviewer\n\n"
            "You review code for correctness, contract compliance, and quality. You must:\n"
            "- Verify every API endpoint matches its SVC-xxx contract\n"
            "- Check field names, types, and required fields match exactly\n"
            "- Verify no mock data or placeholder values exist\n"
            "- Use Codebase Intelligence to check cross-file impact\n"
            "- Report CONTRACT violations as blocking issues\n"
        ),
        "test-engineer": (
            "## Role: Test Engineer\n\n"
            "You write and run tests. You must:\n"
            "- Use Contract Engine generate_tests() to create contract conformance tests\n"
            "- Write unit tests for all public functions\n"
            "- Write integration tests for API endpoints\n"
            "- Verify test coverage meets thresholds\n"
        ),
        "wiring-verifier": (
            "## Role: Wiring Verifier\n\n"
            "You verify cross-file integration and contract compliance. You must:\n"
            "- Use Codebase Intelligence find_dependencies() to trace imports\n"
            "- Verify all exports are consumed\n"
            "- Verify all contract endpoints are implemented\n"
            "- Check for dead code via check_dead_code()\n"
        ),
    }
    return templates.get(role, f"## Role: {role}\n\nFollow the project requirements.\n")


def _generate_service_section(
    service_name: str,
    dependencies: list[str],
    tech_stack: str,
) -> str:
    """Generate service context section."""
    lines = [f"## Service: {service_name}\n"]
    if tech_stack:
        lines.append(f"**Tech Stack:** {tech_stack}\n")
    if dependencies:
        lines.append("**Dependencies:**")
        for dep in dependencies:
            lines.append(f"- {dep}")
        lines.append("")
    return "\n".join(lines)


def _generate_contract_section(
    contracts: list[dict[str, Any]],
    role: str,
) -> str:
    """Generate contract awareness section."""
    lines = ["## Contracts\n"]
    lines.append("The following contracts govern this service's API boundaries:\n")
    for contract in contracts[:20]:  # Limit to prevent CLAUDE.md from being too large
        cid = contract.get("id", "unknown")
        ctype = contract.get("type", "unknown")
        crole = contract.get("role", "unknown")
        lines.append(f"- **{cid}** ({ctype}, {crole})")
    if len(contracts) > 20:
        lines.append(f"- ... and {len(contracts) - 20} more")
    lines.append("")
    if role in ("code-writer", "code-reviewer"):
        lines.append(
            "**CRITICAL:** Every API endpoint MUST match its contract exactly. "
            "Use `validate_endpoint()` from Contract Engine MCP to verify.\n"
        )
    return "\n".join(lines)


def _generate_mcp_section(
    mcp_servers: dict[str, Any],
    role: str,
) -> str:
    """Generate MCP server usage instructions."""
    lines = ["## Available MCP Tools\n"]
    if "contract-engine" in mcp_servers:
        lines.append("### Contract Engine")
        lines.append("- `get_contract(contract_id)` — Get a contract by ID")
        lines.append("- `validate_endpoint(service_name, method, path, response_body)` — Validate implementation")
        lines.append("- `generate_tests(contract_id)` — Generate conformance tests")
        lines.append("- `mark_implemented(contract_id, service_name, evidence_path)` — Mark as implemented")
        lines.append("- `get_unimplemented_contracts()` — Find gaps")
        lines.append("")
    if "codebase-intelligence" in mcp_servers:
        lines.append("### Codebase Intelligence")
        lines.append("- `find_definition(symbol)` — Find where a symbol is defined")
        lines.append("- `find_callers(symbol)` — Find all call sites")
        lines.append("- `find_dependencies(file_path)` — Get dependency graph")
        lines.append("- `search_semantic(query)` — Semantic code search")
        lines.append("- `register_artifact(file_path, service_name)` — Register new file")
        lines.append("")
    return "\n".join(lines)


def _generate_convergence_section(convergence_config: dict[str, Any]) -> str:
    """Generate convergence mandates section."""
    min_ratio = convergence_config.get("min_convergence_ratio", 0.95)
    return (
        "## Convergence Mandates\n\n"
        f"- Minimum convergence ratio: {min_ratio} ({int(min_ratio * 100)}% of requirements)\n"
        "- Do NOT mark tasks complete until all claimed requirements are implemented\n"
        "- All API endpoints must be contract-validated before completion\n"
        "- All created files must be registered with Codebase Intelligence\n"
        "- Zero mock data, zero placeholder values, zero hardcoded counts\n"
    )


def write_teammate_claude_md(
    project_dir: Path,
    role: str,
    service_name: str,
    config: AgentTeamConfig,
    contracts: list[dict[str, Any]] | None = None,
    mcp_servers: dict[str, Any] | None = None,
) -> Path:
    """Write CLAUDE.md to the project's .claude directory.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 4.1-4.2
    CLAUDE.md in project root is loaded by all teammates automatically.
    """
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir(exist_ok=True)

    content = generate_claude_md(
        role=role,
        service_name=service_name,
        contracts=contracts or [],
        dependencies=[],
        mcp_servers=mcp_servers or {},
        quality_standards="",
        convergence_config={
            "min_convergence_ratio": config.convergence.min_convergence_ratio,
        },
    )

    output_path = claude_dir / "CLAUDE.md"
    output_path.write_text(content, encoding="utf-8")
    logger.info("Wrote CLAUDE.md for %s (%s) to %s", role, service_name, output_path)
    return output_path
```

---

### 2.6 src/agent_team/contract_scanner.py (~300 lines)

**Purpose:** CONTRACT-001..004 static scans for contract compliance verification.

**Source:** BUILD2_CODEBASE_RESEARCH.md Section 2.3.2, SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md lines 230-236

```python
"""
CONTRACT-001..004 static scan patterns for contract compliance.

These scans extend the existing quality_checks.py scan infrastructure
to verify contract compliance at the static analysis level.

Scan codes:
- CONTRACT-001: Endpoint schema mismatch (response fields don't match contract)
- CONTRACT-002: Missing contracted endpoint (no route/controller found)
- CONTRACT-003: Event schema mismatch (AsyncAPI payload mismatch)
- CONTRACT-004: Shared model type drift (cross-service type inconsistency)

Reference:
- SUPER_TEAM_THREE_BUILDS_COMPLETE_REFERENCE.md lines 230-236
- BUILD2_CODEBASE_RESEARCH.md Section 2.3.2
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Import from existing quality_checks.py
# Violation dataclass: .check, .file_path, .line, .message, .severity
# ScanScope dataclass: .changed_files, .mode
# _get_files helper, _MAX_VIOLATIONS cap

_MAX_VIOLATIONS = 100


# Stub Violation for architecture doc — actual import from quality_checks.py
class _Violation:
    """Mirrors quality_checks.Violation for architecture purposes."""
    def __init__(self, check: str, file_path: str, line: int, message: str, severity: str):
        self.check = check
        self.file_path = file_path
        self.line = line
        self.message = message
        self.severity = severity


# ---------------------------------------------------------------------------
# CONTRACT-001: Endpoint Schema Mismatch
# ---------------------------------------------------------------------------

def run_endpoint_schema_scan(
    project_dir: Path,
    contracts: list[dict[str, Any]],
    scope: Any | None = None,
) -> list[Any]:
    """Scan for endpoint response schema mismatches.

    For each contracted endpoint (from SVC-xxx or Contract Engine):
    1. Find the implementing controller/route file
    2. Extract the response DTO/model
    3. Compare field names and types against the contract
    4. Report mismatches as CONTRACT-001 violations

    Severity: "error"
    """
    violations: list[Any] = []
    # Implementation: parse contracts, find implementing files,
    # compare field schemas using regex-based extraction
    return violations[:_MAX_VIOLATIONS]


# ---------------------------------------------------------------------------
# CONTRACT-002: Missing Contracted Endpoint
# ---------------------------------------------------------------------------

def run_missing_endpoint_scan(
    project_dir: Path,
    contracts: list[dict[str, Any]],
    scope: Any | None = None,
) -> list[Any]:
    """Scan for contracted endpoints that have no implementation.

    For each SVC-xxx entry or Contract Engine contract:
    1. Extract method + path
    2. Search for matching route decorator or controller attribute
    3. Report missing endpoints as CONTRACT-002 violations

    Severity: "error"
    """
    violations: list[Any] = []
    return violations[:_MAX_VIOLATIONS]


# ---------------------------------------------------------------------------
# CONTRACT-003: Event Schema Mismatch
# ---------------------------------------------------------------------------

def run_event_schema_scan(
    project_dir: Path,
    contracts: list[dict[str, Any]],
    scope: Any | None = None,
) -> list[Any]:
    """Scan for AsyncAPI event schema mismatches.

    For each AsyncAPI contract:
    1. Find publish/subscribe call sites
    2. Extract the payload being published or consumed
    3. Compare against contracted schema
    4. Report mismatches as CONTRACT-003 violations

    Severity: "error"
    """
    violations: list[Any] = []
    return violations[:_MAX_VIOLATIONS]


# ---------------------------------------------------------------------------
# CONTRACT-004: Shared Model Type Drift
# ---------------------------------------------------------------------------

def run_shared_model_scan(
    project_dir: Path,
    contracts: list[dict[str, Any]],
    scope: Any | None = None,
) -> list[Any]:
    """Scan for shared model type inconsistencies across service boundaries.

    For each JSON Schema shared model:
    1. Find all TypeScript/Python/C# type definitions matching the model name
    2. Compare field names, types, optionality
    3. Check for camelCase/snake_case mismatches
    4. Report drift as CONTRACT-004 violations

    Severity: "error"
    """
    violations: list[Any] = []
    return violations[:_MAX_VIOLATIONS]


# ---------------------------------------------------------------------------
# Aggregate scan
# ---------------------------------------------------------------------------

def run_contract_compliance_scan(
    project_dir: Path,
    contracts: list[dict[str, Any]],
    scope: Any | None = None,
    endpoint_schema: bool = True,
    missing_endpoint: bool = True,
    event_schema: bool = True,
    shared_model: bool = True,
) -> list[Any]:
    """Run all CONTRACT scans and return combined violations.

    Each scan is independently gated by its boolean parameter.
    Each scan is in its own try/except for crash isolation.

    Reference: BUILD2_CODEBASE_RESEARCH.md Section 2.1.2 (scan pipeline pattern)
    """
    all_violations: list[Any] = []

    if endpoint_schema:
        try:
            all_violations.extend(run_endpoint_schema_scan(project_dir, contracts, scope))
        except Exception:
            logger.warning("CONTRACT-001 scan failed", exc_info=True)

    if missing_endpoint:
        try:
            all_violations.extend(run_missing_endpoint_scan(project_dir, contracts, scope))
        except Exception:
            logger.warning("CONTRACT-002 scan failed", exc_info=True)

    if event_schema:
        try:
            all_violations.extend(run_event_schema_scan(project_dir, contracts, scope))
        except Exception:
            logger.warning("CONTRACT-003 scan failed", exc_info=True)

    if shared_model:
        try:
            all_violations.extend(run_shared_model_scan(project_dir, contracts, scope))
        except Exception:
            logger.warning("CONTRACT-004 scan failed", exc_info=True)

    return all_violations[:_MAX_VIOLATIONS]
```

---

### 2.7 src/agent_team/mcp_client.py (~200 lines)

**Purpose:** MCP client session management — creating and maintaining connections to Build 1 MCP servers.

**Source:** BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3

```python
"""
MCP client session management for Build 1 service connections.

Provides async context managers for creating MCP client sessions
to the Architect, Contract Engine, and Codebase Intelligence servers.

Uses the MCP Python SDK: stdio_client() + ClientSession pattern.
Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from .config import ContractEngineConfig, CodebaseIntelligenceConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_contract_engine_session(
    config: ContractEngineConfig,
) -> AsyncIterator[Any]:
    """Create an MCP client session to Contract Engine.

    Usage:
        async with create_contract_engine_session(config) as session:
            client = ContractEngineClient(session)
            contract = await client.get_contract("SVC-001")

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3
    """
    try:
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.session import ClientSession
    except ImportError:
        logger.error("MCP SDK not installed. pip install mcp")
        raise

    server_params = StdioServerParameters(
        command=config.mcp_command,
        args=config.mcp_args,
        env={"DATABASE_PATH": config.database_path} if config.database_path else None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connected to Contract Engine MCP")
            yield session


@asynccontextmanager
async def create_codebase_intelligence_session(
    config: CodebaseIntelligenceConfig,
) -> AsyncIterator[Any]:
    """Create an MCP client session to Codebase Intelligence.

    Usage:
        async with create_codebase_intelligence_session(config) as session:
            client = CodebaseIntelligenceClient(session)
            result = await client.search_semantic("payment processing")

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.3
    """
    try:
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.session import ClientSession
    except ImportError:
        logger.error("MCP SDK not installed. pip install mcp")
        raise

    env = {}
    if config.database_path:
        env["DATABASE_PATH"] = config.database_path
    if config.chroma_path:
        env["CHROMA_PATH"] = config.chroma_path
    if config.graph_path:
        env["GRAPH_PATH"] = config.graph_path

    server_params = StdioServerParameters(
        command=config.mcp_command,
        args=config.mcp_args,
        env=env or None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connected to Codebase Intelligence MCP")
            yield session
```

---

## 3. Existing File Modifications

### 3.1 config.py — ADD ~120 lines

**Reference:** BUILD2_CODEBASE_RESEARCH.md Section 2.4

#### 3.1.1 New Config Dataclasses

```python
@dataclass
class AgentTeamsConfig:
    """Configuration for Claude Code Agent Teams integration.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 1.8-1.9
    """
    enabled: bool = False          # Disabled by default (experimental)
    fallback_to_cli: bool = True   # Fall back to subprocess if agent teams fails
    delegate_mode: bool = True     # Lead coordinates only, never implements
    max_teammates: int = 5         # Max concurrent teammates
    teammate_model: str = ""       # Override model for teammates (empty = default)
    teammate_permission_mode: str = "acceptEdits"  # Permission mode for teammates
    teammate_idle_timeout: int = 300  # Seconds before idle timeout
    task_completed_hook: bool = True  # Enable TaskCompleted convergence hook


@dataclass
class ContractEngineConfig:
    """Configuration for Build 1 Contract Engine MCP integration.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 7.2
    """
    enabled: bool = False          # Disabled when Build 1 not available
    mcp_command: str = "python"
    mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.contract_engine.mcp_server"])
    database_path: str = ""        # Path to contracts.db
    validation_on_build: bool = True  # Validate endpoints during build
    test_generation: bool = True   # Generate contract tests


@dataclass
class CodebaseIntelligenceConfig:
    """Configuration for Build 1 Codebase Intelligence MCP integration.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 7.3
    """
    enabled: bool = False          # Disabled when Build 1 not available
    mcp_command: str = "python"
    mcp_args: list[str] = field(default_factory=lambda: ["-m", "src.codebase_intelligence.mcp_server"])
    database_path: str = ""
    chroma_path: str = ""
    graph_path: str = ""
    replace_static_map: bool = True   # Replace CODEBASE_MAP.md with live queries
    register_artifacts: bool = True   # Auto-register generated files


@dataclass
class ContractScanConfig:
    """Configuration for CONTRACT-001..004 scans.

    Reference: BUILD2_CODEBASE_RESEARCH.md Section 2.3.2
    """
    endpoint_schema_scan: bool = True   # CONTRACT-001
    missing_endpoint_scan: bool = True  # CONTRACT-002
    event_schema_scan: bool = True      # CONTRACT-003
    shared_model_scan: bool = True      # CONTRACT-004
```

#### 3.1.2 AgentTeamConfig Additions

Add to the root `AgentTeamConfig` dataclass:

```python
agent_teams: AgentTeamsConfig = field(default_factory=AgentTeamsConfig)
contract_engine: ContractEngineConfig = field(default_factory=ContractEngineConfig)
codebase_intelligence: CodebaseIntelligenceConfig = field(default_factory=CodebaseIntelligenceConfig)
contract_scans: ContractScanConfig = field(default_factory=ContractScanConfig)
```

#### 3.1.3 Depth Gating

Add to `_apply_depth_defaults()`:

| Feature | quick | standard | thorough | exhaustive |
|---------|-------|----------|----------|------------|
| agent_teams.enabled | False | False | True (if env set) | True (if env set) |
| contract_engine.enabled | False | True (validation only) | True (full) | True (full) |
| codebase_intelligence.enabled | False | True (queries only) | True (full) | True (full) |
| CONTRACT scans 001-002 | False | True | True | True |
| CONTRACT scans 003-004 | False | False | True | True |

#### 3.1.4 _dict_to_config() Modification

Add parsing for the 4 new config sections. Follow the existing pattern:

```python
# In _dict_to_config():
agent_teams_raw = raw.get("agent_teams", {})
if isinstance(agent_teams_raw, dict):
    # Parse fields, track overrides
    ...
```

**Backward compatibility:** All new features default to `enabled: False`. Existing config.yaml files without Build 2 sections continue to work.

---

### 3.2 cli.py — ADD ~300 lines

**Reference:** BUILD2_CODEBASE_RESEARCH.md Section 2.1

#### 3.2.1 Mode Selection (Line ~4200)

Add agent teams branch to the existing mode selection:

```python
# Current: interactive vs milestone vs standard
# Build 2 adds: agent teams mode check BEFORE milestone/standard

if config.agent_teams.enabled and detect_agent_teams_available():
    backend = create_execution_backend(config)
    team_state = await backend.initialize(config, cwd)
    # Generate CLAUDE.md, hooks, .mcp.json
    # Proceed with agent-teams-enhanced execution
    # Falls through to milestone or standard mode with backend
else:
    # Existing flow unchanged
    ...
```

#### 3.2.2 MCP Server Injection (Line ~170-250)

Add Build 1 MCP servers to the server list:

```python
# After existing get_mcp_servers() call:
if config.contract_engine.enabled:
    servers["contract-engine"] = _contract_engine_mcp_server(config.contract_engine)
if config.codebase_intelligence.enabled:
    servers["codebase-intelligence"] = _codebase_intelligence_mcp_server(config.codebase_intelligence)
```

#### 3.2.3 Phase 0.5: Codebase Map (Line ~4050-4100)

Add MCP-backed alternative:

```python
# Current: codebase_map_content = await generate_codebase_map(cwd, ...)
# Build 2:
if config.codebase_intelligence.enabled and config.codebase_intelligence.replace_static_map:
    try:
        codebase_map_content = await _query_codebase_index(cwd, config)
    except Exception:
        logger.warning("Codebase Intelligence MCP failed, falling back to static map")
        codebase_map_content = await generate_codebase_map(cwd, ...)
else:
    codebase_map_content = await generate_codebase_map(cwd, ...)
```

#### 3.2.4 Post-Orchestration Scan Pipeline (Line ~5650)

Add CONTRACT scans after API contract scan:

```python
# After existing API contract scan block (line ~5600):
if config.contract_scans.endpoint_schema_scan or config.contract_scans.missing_endpoint_scan:
    try:
        contract_violations = run_contract_compliance_scan(
            cwd, contracts, scope,
            endpoint_schema=config.contract_scans.endpoint_schema_scan,
            missing_endpoint=config.contract_scans.missing_endpoint_scan,
            event_schema=config.contract_scans.event_schema_scan,
            shared_model=config.contract_scans.shared_model_scan,
        )
        if contract_violations:
            all_violations.extend(contract_violations)
            recovery_types.add("contract_compliance")
    except Exception:
        logger.warning("CONTRACT scan failed", exc_info=True)
```

#### 3.2.5 Fix Functions (Line ~2772-2916)

Add CONTRACT-specific fix branches to `_run_integrity_fix()`:

```python
elif scan_type == "contract_endpoint_schema":
    fix_prompt = "Fix the response schema to match the contracted endpoint..."
elif scan_type == "contract_missing_endpoint":
    fix_prompt = "Implement the missing contracted endpoint..."
elif scan_type == "contract_event_schema":
    fix_prompt = "Fix the event payload to match the AsyncAPI contract..."
elif scan_type == "contract_shared_model":
    fix_prompt = "Fix the shared model type to match the JSON Schema..."
```

#### 3.2.6 Signal Handling (Line ~2919-2970)

Add teammate shutdown on interrupt:

```python
# In _handle_interrupt():
if getattr(_module_state, 'team_state', None) and _module_state.team_state.active:
    logger.info("Shutting down agent teams...")
    # Send shutdown_request to all teammates
```

#### 3.2.7 Convergence Health (Line ~3359-3416)

Add contract compliance to health calculation:

```python
# In _check_convergence_health():
# Current: health based on checkbox_ratio
# Build 2 addition:
if config.contract_engine.enabled and contract_report:
    contract_ratio = contract_report.verified_contracts / max(contract_report.total_contracts, 1)
    health_ratio = min(checkbox_ratio, contract_ratio)
```

---

### 3.3 agents.py — ADD ~200 lines

**Reference:** BUILD2_CODEBASE_RESEARCH.md Section 2.2

#### 3.3.1 ARCHITECT_PROMPT (Lines 1-150)

Add after existing content:

```python
# CONTRACT ENGINE INTEGRATION
"""
## Contract Engine Integration

When designing service boundaries, FIRST query the Contract Engine MCP:
1. Call get_contracts_for_service() for each service being designed
2. If contracts already exist, design MUST be compatible with them
3. Generate new contract stubs in the format expected by Contract Engine
4. Include EXACT FIELD SCHEMAS with types in every SVC-xxx table

## Codebase Intelligence Integration

When analyzing the existing codebase:
1. Call get_service_interface() to understand existing APIs
2. Call search_semantic() to find relevant existing code
3. Use find_dependencies() to understand module relationships
"""
```

#### 3.3.2 CODE_WRITER_PROMPT (Lines 150-500)

Add:

```python
# CONTRACT ENGINE INTEGRATION
"""
## Contract Engine Compliance

After implementing EACH API endpoint:
1. Call Contract Engine validate_endpoint(service_name, method, path, response_body)
2. If validation fails, fix the implementation to match the contract
3. After all endpoints pass, call mark_implemented(contract_id, service_name, evidence_path)

## Codebase Intelligence

After creating EACH new file:
1. Call Codebase Intelligence register_artifact(file_path, service_name)
2. Before implementing, call search_semantic() to find existing similar code
3. Before importing, call find_definition() to verify the symbol exists
"""
```

#### 3.3.3 build_orchestrator_prompt and build_milestone_execution_prompt

Add `contract_context: str = ""` and `codebase_index_context: str = ""` parameters following the existing `tech_research_content` pattern (agents.py line ~2050-2100):

```python
def build_orchestrator_prompt(
    ...,
    tech_research_content: str = "",
    contract_context: str = "",      # NEW
    codebase_index_context: str = "", # NEW
) -> str:
```

---

### 3.4 state.py — ADD ~50 lines

**Reference:** BUILD2_CODEBASE_RESEARCH.md Section 2.5

```python
@dataclass
class ContractReport:
    """Report from contract compliance verification."""
    total_contracts: int = 0
    verified_contracts: int = 0
    violated_contracts: int = 0
    missing_implementations: int = 0
    violations: list[dict] = field(default_factory=list)
    health: str = "unknown"  # passed | partial | failed | unknown


@dataclass
class IntegrationReport:
    """Report from cross-service integration verification."""
    total_endpoints: int = 0
    tested_endpoints: int = 0
    passed_endpoints: int = 0
    failed_endpoints: int = 0
    untested_contracts: list[str] = field(default_factory=list)
    health: str = "unknown"
```

Add to `RunState`:

```python
contract_report: ContractReport = field(default_factory=ContractReport)
integration_report: IntegrationReport = field(default_factory=IntegrationReport)
agent_teams_active: bool = False
registered_artifacts: list[str] = field(default_factory=list)
```

---

### 3.5 mcp_servers.py — ADD ~60 lines

**Reference:** BUILD2_CODEBASE_RESEARCH.md Section 2.6

```python
def _contract_engine_mcp_server(config: ContractEngineConfig) -> dict[str, Any]:
    """MCP server config for Contract Engine.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.9
    """
    env = {}
    if config.database_path:
        env["DATABASE_PATH"] = config.database_path
    return {
        "type": "stdio",
        "command": config.mcp_command,
        "args": config.mcp_args,
        "env": env,
    }


def _codebase_intelligence_mcp_server(config: CodebaseIntelligenceConfig) -> dict[str, Any]:
    """MCP server config for Codebase Intelligence.

    Reference: BUILD2_TECHNOLOGY_RESEARCH.md Section 3.9
    """
    env = {}
    if config.database_path:
        env["DATABASE_PATH"] = config.database_path
    if config.chroma_path:
        env["CHROMA_PATH"] = config.chroma_path
    if config.graph_path:
        env["GRAPH_PATH"] = config.graph_path
    return {
        "type": "stdio",
        "command": config.mcp_command,
        "args": config.mcp_args,
        "env": env,
    }


def get_contract_aware_servers(config: AgentTeamConfig) -> dict[str, Any]:
    """Returns all standard servers + Contract Engine + Codebase Intelligence.

    This is the primary server getter for Build 2 mode.
    Falls back to get_mcp_servers() when Build 1 services are unavailable.
    """
    servers = get_mcp_servers(config)
    if config.contract_engine.enabled:
        servers["contract-engine"] = _contract_engine_mcp_server(config.contract_engine)
    if config.codebase_intelligence.enabled:
        servers["codebase-intelligence"] = _codebase_intelligence_mcp_server(
            config.codebase_intelligence
        )
    return servers
```

---

### 3.6 Other File Modifications

| File | Change | LOC | Reference |
|------|--------|-----|-----------|
| `code_quality_standards.py` | Add `CONTRACT_COMPLIANCE_STANDARDS` and `INTEGRATION_STANDARDS` constants; map to code-writer, code-reviewer, architect in `_AGENT_STANDARDS_MAP` | +40 | BUILD2_CODEBASE_RESEARCH.md Section 2.10 |
| `tracking_documents.py` | Add `generate_contract_compliance_matrix()`, `parse_contract_compliance_matrix()`, `update_contract_compliance_entry()` | +100 | BUILD2_CODEBASE_RESEARCH.md Section 2.11 |
| `milestone_manager.py` | Add contract compliance to `check_milestone_health()`: `health = min(checkbox_ratio, contract_compliance_ratio)` | +20 | BUILD2_CODEBASE_RESEARCH.md Section 2.12 |
| `e2e_testing.py` | Add `E2E_CONTRACT_COMPLIANCE_PROMPT` constant; extend `detect_app_type()` to detect Build 1 MCP availability | +50 | BUILD2_CODEBASE_RESEARCH.md Section 2.13 |
| `verification.py` | Add `verify_contract_compliance()` function | +80 | BUILD2_CODEBASE_RESEARCH.md Section 2.18 |
| `contracts.py` | Add `ServiceContract` dataclass and `ServiceContractRegistry` class with MCP-backed methods | +150 | BUILD2_CODEBASE_RESEARCH.md Section 2.7 |
| `codebase_map.py` | Add `generate_codebase_map_from_mcp()` and `register_new_artifact()` functions | +50 | BUILD2_CODEBASE_RESEARCH.md Section 2.8 |
| `scheduler.py` | Add `ExecutionBackend` protocol import and team-aware wave mapping utilities | +100 | BUILD2_CODEBASE_RESEARCH.md Section 2.9 |
| `tech_research.py` | Add Build 1 service detection to tech research queries | +20 | BUILD2_CODEBASE_RESEARCH.md Section 2.16 |

---

## 4. Data Flow Diagrams

### 4.1 PRD Flow Through Upgraded System

```
PRD (input)
    |
    v
[Phase 0: Config Loading] -----> Load config.yaml, detect depth, detect agent teams
    |
    v
[Phase 0.5: Codebase Map]
    |-- Build 1 available?
    |   YES --> query_codebase_index() via MCP --> Codebase Intelligence
    |   NO  --> generate_codebase_map() (existing static analysis)
    |
    v
[Phase 0.6: Design Reference] (unchanged)
    |
    v
[Phase 0.75: Contract Loading]
    |-- Build 1 available?
    |   YES --> query Contract Engine MCP for service contracts
    |           + load local CONTRACTS.json as cache
    |   NO  --> load_contracts() from local CONTRACTS.json only
    |
    v
[Phase 1: Tech Research] (unchanged — Context7)
    |
    v
[Phase 1.5: PRD Decomposition] --> Architect decomposes PRD
    |                                (optionally queries Architect MCP)
    v
[Phase 2: Milestone Execution]
    |-- Agent Teams enabled?
    |   YES --> AgentTeamsBackend
    |           - Generate CLAUDE.md for each role
    |           - Generate hooks for quality gates
    |           - Create tasks in shared task list
    |           - Teammates self-claim and execute
    |           - Hooks enforce convergence
    |   NO  --> CLIBackend (existing _run_prd_milestones)
    |
    v
[Phase 3: Post-Orchestration Scans]
    |
    |-- Mock data scan
    |-- UI compliance scan
    |-- Deployment scan
    |-- Asset scan
    |-- PRD reconciliation
    |-- Dual ORM scan
    |-- Default value scan
    |-- Relationship scan
    |-- API contract scan (v9.0 static)
    |-- SDL scan
    |-- XREF scan
    |-- CONTRACT-001: Endpoint schema scan     <-- NEW
    |-- CONTRACT-002: Missing endpoint scan     <-- NEW
    |-- CONTRACT-003: Event schema scan         <-- NEW
    |-- CONTRACT-004: Shared model scan         <-- NEW
    |
    v
[Phase 4: Fix Loops] (13 existing + 4 new CONTRACT fix loops)
    |
    v
[Phase 5: E2E Testing]
    |-- Standard E2E (existing)
    |-- Contract compliance E2E (NEW — validates against MCP)
    |
    v
[Phase 6: Browser Testing] (unchanged)
    |
    v
[Complete]
```

### 4.2 Contract Validation Flow

```
Code Writer generates endpoint
    |
    v
validate_endpoint() via Contract Engine MCP
    |
    +--- valid: true --> mark_implemented() --> continue
    |
    +--- valid: false --> violations list
                |
                v
            Fix implementation
                |
                v
            Retry validation
                |
                +--- max retries --> report as CONTRACT-001 violation
```

### 4.3 Codebase Intelligence Flow

```
Builder creates new file
    |
    v
register_artifact(file_path, service_name) via MCP
    |
    v
Codebase Intelligence indexes:
    - Parse AST with tree-sitter
    - Extract symbols (classes, functions)
    - Resolve imports to file paths
    - Update NetworkX dependency graph
    - Add code chunks to ChromaDB
    |
    v
Other agents can now:
    - find_definition(symbol) --> exact location
    - find_callers(symbol) --> all call sites
    - search_semantic(query) --> relevant code
    - find_dependencies(file) --> import graph
```

### 4.4 Agent Teams Coordination Flow

```
Team Lead (delegate mode)
    |
    | Creates tasks via TaskCreate
    | Sets dependencies via TaskUpdate(addBlockedBy)
    |
    +---> Task A: "Implement UserController"  [pending]
    |     +---> Task B: "Write UserService"     [pending, blocked by A]
    |     +---> Task C: "Write UserTests"       [pending, blocked by B]
    |
    | Teammate 1 (code-writer) claims Task A
    |     - Reads CLAUDE.md with contract awareness
    |     - Calls Contract Engine for contract
    |     - Implements controller
    |     - Calls validate_endpoint()
    |     - Calls register_artifact()
    |     - TaskCompleted hook runs convergence check
    |     - Task A -> completed
    |
    | Task B unblocked, Teammate 2 (code-writer) claims it
    | Teammate 1 goes to claim next available task
    |     - TeammateIdle hook checks for pending tasks
    |     - Teammate 1 claims Task C (or another available task)
    |
    | All tasks completed
    |     - Stop hook runs final quality gate
    |     - Verifies all requirements checked
```

---

## 5. Hook Configuration Architecture

### 5.1 Complete Hook Configuration

**Location:** `.claude/settings.local.json` (not committed, per-instance)

**Reference:** BUILD2_TECHNOLOGY_RESEARCH.md Section 2.2

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Read REQUIREMENTS.md. Verify ALL items marked [x]. For each unchecked item, check if the completing task addresses it. If NOT all claimed requirements are satisfied, respond with ok: false and explain what is missing.",
            "timeout": 120
          }
        ]
      }
    ],
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Use TaskList to check for pending tasks. If there are tasks with status 'pending' and no blockedBy, respond with ok: false and reason: 'Pending tasks available'. If all tasks are completed or blocked, respond with ok: true.",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/quality-gate.sh",
            "timeout": 30,
            "statusMessage": "Running quality gate..."
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/track-file-change.sh",
            "async": true
          }
        ]
      }
    ]
  }
}
```

### 5.2 Hook Behavior Matrix

| Hook | Event | Type | Blocking? | Exit 2 Behavior | Purpose |
|------|-------|------|-----------|-----------------|---------|
| TaskCompleted | Task marked done | agent | Yes | Prevents completion, sends feedback | Convergence verification |
| TeammateIdle | Teammate about to idle | agent | Yes | Prevents idle, keeps working | Workload rebalancing |
| Stop | Session ending | command | Yes | Prevents stop, sends feedback | Final quality gate |
| PostToolUse(Write\|Edit) | After file write | command | No (async) | N/A | File change tracking |

### 5.3 What Hooks Replace

| Current Python Enforcement | Hook Replacement |
|---------------------------|------------------|
| GATE 5 in cli.py | Stop hook + quality-gate.sh |
| _check_convergence_health() | TaskCompleted agent hook |
| Review recovery loop | TaskCompleted hook prevents premature completion |
| Post-orchestration scan triggering | Stop hook ensures scans ran |

---

## 6. CLAUDE.md Generation Strategy

### 6.1 Template Structure

```markdown
# {Role} Instructions — {service_name}

---

## Role: {role-specific section}
{Instructions from agents.py prompt templates}

---

## Service: {service_name}
**Tech Stack:** {detected stack}
**Dependencies:** {list of services}

---

## Contracts
{List of SVC-xxx contracts from Contract Engine}
**CRITICAL:** Every API endpoint MUST match its contract exactly.

---

## Available MCP Tools
### Contract Engine
{Tool list with descriptions}
### Codebase Intelligence
{Tool list with descriptions}

---

## Quality Standards
{From code_quality_standards.py}

---

## Convergence Mandates
- Minimum convergence ratio: 95%
- All endpoints must be contract-validated
- All files must be registered with Codebase Intelligence
- Zero mock data, zero placeholders
```

### 6.2 How Prompts Transfer from agents.py

| agents.py Section | CLAUDE.md Section | Transfer Method |
|-------------------|-------------------|-----------------|
| ARCHITECT_PROMPT (lines 1-150) | "Role: Architect" | Direct text extraction + contract additions |
| CODE_WRITER_PROMPT (lines 150-500) | "Role: Code Writer" | Direct text extraction + MCP usage instructions |
| CODE_REVIEWER_PROMPT (lines 500-700) | "Role: Code Reviewer" | Direct text extraction + contract review criteria |
| build_orchestrator_prompt (lines 2000-2250) | Not in CLAUDE.md | Lead reads this directly, not teammates |
| build_milestone_execution_prompt (lines 2250-2500) | Partially in "Convergence Mandates" | Task context goes via TaskCreate description |

### 6.3 Per-Service Customization

Each service directory gets its own `.claude/CLAUDE.md` with:
- **Contracts:** Only the contracts relevant to this service (provider + consumer)
- **Dependencies:** Only the services this service depends on
- **MCP Servers:** Configured with paths pointing to this service's data
- **Quality Standards:** All standards that apply (CONTRACT + existing)

### 6.4 Runtime Injection Points

CLAUDE.md is generated at these points in the pipeline:
1. **Before milestone execution** — when agent teams mode is active
2. **Before each milestone** — updated with milestone-specific context
3. **After contract loading** — updated with fetched contracts

---

## 7. Milestone Breakdown

### M1: Agent Teams Abstraction Layer (~800 new LOC)

**Dependencies:** None (foundational)
**Risk:** HIGH — touches core orchestration loop
**Files:**
- CREATE: `agent_teams_backend.py` (~550 lines)
- CREATE: `hooks_manager.py` (~250 lines)
- MODIFY: `config.py` (+AgentTeamsConfig, ~30 lines)
- MODIFY: `state.py` (+agent_teams_active, ~10 lines)

**What it delivers:**
- `ExecutionBackend` protocol
- `AgentTeamsBackend` (Mode A)
- `CLIBackend` (Mode B — wraps existing logic)
- `create_execution_backend()` factory
- Hook configuration generation
- Basic wiring in cli.py for mode selection

### M2: Contract Engine Integration (~650 new LOC)

**Dependencies:** M1 (needs config infrastructure)
**Risk:** MEDIUM — MCP client reliability unknown
**Files:**
- CREATE: `contract_client.py` (~350 lines)
- CREATE: `mcp_client.py` (~200 lines, shared session management)
- MODIFY: `mcp_servers.py` (+contract engine server, ~30 lines)
- MODIFY: `config.py` (+ContractEngineConfig, ~20 lines)
- MODIFY: `contracts.py` (+ServiceContractRegistry, ~50 lines)

**What it delivers:**
- Typed MCP client for all 6 Contract Engine tools
- MCP session management (async context managers)
- MCP server config for Contract Engine
- Fallback from MCP to local contract verification

### M3: Codebase Intelligence Integration (~400 new LOC)

**Dependencies:** M2 (shares MCP client infrastructure)
**Risk:** MEDIUM — ChromaDB query performance unknown
**Files:**
- CREATE: `codebase_client.py` (~300 lines)
- MODIFY: `mcp_servers.py` (+codebase intelligence server, ~30 lines)
- MODIFY: `config.py` (+CodebaseIntelligenceConfig, ~20 lines)
- MODIFY: `codebase_map.py` (+MCP-backed generation, ~50 lines)

**What it delivers:**
- Typed MCP client for all 7 Codebase Intelligence tools
- MCP-backed codebase map generation
- Artifact registration support
- Fallback to static CODEBASE_MAP.md generation

### M4: Pipeline Integration (~600 new LOC)

**Dependencies:** M1, M2, M3 (needs all backends and clients)
**Risk:** HIGH — modifies cli.py main pipeline
**Files:**
- MODIFY: `cli.py` (+300 lines — mode selection, scan wiring, fix loops, phase integration)
- MODIFY: `agents.py` (+200 lines — contract awareness in all prompts)
- MODIFY: `state.py` (+50 lines — ContractReport, IntegrationReport)
- CREATE: `claude_md_generator.py` (~350 lines) (could be in M1 but needs contracts)

**What it delivers:**
- Full cli.py integration of agent teams, contract engine, codebase intelligence
- Updated prompts with contract and codebase intelligence instructions
- CLAUDE.md generation for agent teams teammates
- CONTRACT scan wiring in post-orchestration pipeline
- CONTRACT fix loops in recovery passes

### M5: Tracking and Verification (~220 new LOC)

**Dependencies:** M4 (needs pipeline wired)
**Risk:** LOW — follows existing patterns exactly
**Files:**
- CREATE: `contract_scanner.py` (~300 lines — actual CONTRACT-001..004 scan logic)
- MODIFY: `tracking_documents.py` (+100 lines — CONTRACT_COMPLIANCE_MATRIX)
- MODIFY: `verification.py` (+80 lines — contract compliance verification)
- MODIFY: `milestone_manager.py` (+20 lines — contract-aware health)
- MODIFY: `code_quality_standards.py` (+40 lines — CONTRACT + INTEGRATION standards)

**What it delivers:**
- CONTRACT-001..004 static scan implementations
- Contract compliance matrix document
- Contract-aware milestone health
- Updated quality standards

### M6: E2E Testing and Validation (~200 new LOC)

**Dependencies:** M4, M5 (needs full pipeline + scans)
**Risk:** LOW — extends existing E2E infrastructure
**Files:**
- MODIFY: `e2e_testing.py` (+50 lines — contract compliance E2E prompt)
- MODIFY: `cli.py` (+50 lines — contract E2E wiring)
- Tests for all new code

**What it delivers:**
- Contract compliance E2E testing
- End-to-end validation that the upgraded pipeline works
- Regression tests for all existing functionality

### LOC Summary

| Milestone | New LOC | Risk | Dependencies |
|-----------|---------|------|--------------|
| M1: Agent Teams Layer | ~800 | HIGH | None |
| M2: Contract Engine | ~650 | MEDIUM | M1 |
| M3: Codebase Intelligence | ~400 | MEDIUM | M2 |
| M4: Pipeline Integration | ~600 | HIGH | M1, M2, M3 |
| M5: Tracking & Verification | ~540 | LOW | M4 |
| M6: E2E Testing | ~200 | LOW | M4, M5 |
| **TOTAL** | **~3,190** | | |

---

## 8. Error Handling and Fallback Strategy

### 8.1 Agent Teams Failure -> CLI Fallback

```python
try:
    backend = create_execution_backend(config)
    team_state = await backend.initialize(config, cwd)
    result = await backend.execute_wave(wave, context, team_state)
except Exception as e:
    if config.agent_teams.fallback_to_cli:
        logger.warning("Agent Teams failed (%s), falling back to CLI", e)
        backend = CLIBackend()
        team_state = await backend.initialize(config, cwd)
        result = await backend.execute_wave(wave, context, team_state)
    else:
        raise
```

### 8.2 MCP Connection Failures

Every MCP client method follows the same pattern:

```python
try:
    result = await contract_client.validate_endpoint(...)
except (ConnectionError, TimeoutError, Exception):
    logger.warning("Contract Engine MCP unavailable, falling back to static scan")
    result = run_api_contract_scan(...)  # Existing static scan
```

**MCP-specific error categories:**

| Error | Handling | Fallback |
|-------|----------|----------|
| MCP server not found | Log warning, use CLIBackend | Static analysis |
| MCP server crash mid-session | Catch exception, reconnect once | Static analysis if reconnect fails |
| MCP tool returns isError | Log, return safe default | Static analysis |
| MCP timeout | Catch TimeoutError | Static analysis |
| MCP SDK not installed | ImportError at startup | Static analysis |

### 8.3 Contract Validation Errors

Contract validation errors are surfaced as violations in the scan pipeline, not as exceptions:

```python
violations = run_contract_compliance_scan(project_dir, contracts, scope)
if violations:
    # Add to recovery types for fix loop
    recovery_types.add("contract_compliance")
    # Display violations as warnings
    for v in violations:
        logger.warning("CONTRACT violation: %s in %s:%d — %s",
                       v.check, v.file_path, v.line, v.message)
```

### 8.4 Revertibility Guarantee

Build 2 is fully revertible:

1. **Disable agent teams:** Set `agent_teams.enabled: false` in config.yaml
2. **Disable Contract Engine:** Set `contract_engine.enabled: false`
3. **Disable Codebase Intelligence:** Set `codebase_intelligence.enabled: false`
4. **Disable CONTRACT scans:** Set all contract_scans booleans to false

With all Build 2 features disabled, the system behaves identically to v14.0.

---

## 9. Testing Strategy

### 9.1 Unit Tests (~150 tests)

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| `test_agent_teams_backend.py` | ~30 | ExecutionBackend protocol, factory logic, mode selection, fallback |
| `test_contract_client.py` | ~25 | All 6 ContractEngineClient methods, error handling, JSON extraction |
| `test_codebase_client.py` | ~25 | All 7 CodebaseIntelligenceClient methods, error handling |
| `test_hooks_manager.py` | ~20 | Hook config generation, script writing, all 4 hook types |
| `test_claude_md_generator.py` | ~20 | CLAUDE.md generation for all 5 roles, template rendering |
| `test_contract_scanner.py` | ~30 | CONTRACT-001..004 scan patterns, violation detection |

### 9.2 Integration Tests (~80 tests)

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| `test_build2_config.py` | ~25 | 4 new config dataclasses, depth gating, backward compatibility |
| `test_build2_wiring.py` | ~25 | CLI integration points, scan pipeline order, fix loop wiring |
| `test_build2_mcp_integration.py` | ~15 | MCP session creation, tool calling with mocks |
| `test_build2_e2e.py` | ~15 | End-to-end pipeline with Build 1 services mocked |

### 9.3 Backward Compatibility Tests (~50 tests)

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| `test_build2_backward_compat.py` | ~50 | All Build 2 features disabled produces identical behavior to v14.0 |

### 9.4 Testing Approach

- **MCP-dependent tests use mocks.** The MCP SDK client is mocked to return predefined responses. This avoids requiring Build 1 services during testing.
- **Agent Teams tests use the CLIBackend fallback.** Since Agent Teams is experimental and requires Claude Code, tests verify the abstraction layer and factory logic, then test execution through CLIBackend.
- **All existing 5,410+ tests must continue passing.** No new features can break existing functionality.

### 9.5 Test Execution Order

1. Run existing test suite (5,410+ tests) — verify zero new regressions
2. Run Build 2 unit tests — verify new code works in isolation
3. Run Build 2 integration tests — verify wiring is correct
4. Run Build 2 backward compatibility tests — verify disabling features works
5. If Build 1 services available: run Build 2 E2E tests with real MCP servers

---

## Appendix A: Existing Pipeline Preservation Checklist

These elements MUST NOT be broken by Build 2 modifications:

- [ ] 15-stage pipeline execution order in main()
- [ ] 13 self-healing fix loops
- [ ] Post-orchestration scan chain order
- [ ] Milestone-based execution with MASTER_PLAN.md
- [ ] Config-gated features (every scan/feature has a bool gate)
- [ ] Depth-based behavior (quick/standard/thorough/exhaustive)
- [ ] Signal handling (Ctrl+C state save)
- [ ] Resume from STATE.json
- [ ] Contract loading from CONTRACTS.json
- [ ] Convergence health checking
- [ ] GATE 5 enforcement
- [ ] Recovery passes (review, contract, artifact)
- [ ] Tracking document generation
- [ ] Tech research phase (Context7 integration)
- [ ] PRD chunking for large PRDs
- [ ] `_dict_to_config()` tuple return type
- [ ] `load_config()` tuple return type
- [ ] Violation dataclass interface (.check, .file_path, .line, .message, .severity)
- [ ] ScanScope filtering for scoped scans
- [ ] All existing 5,410+ tests passing

---

## Appendix B: Build 1 MCP Tool Quick Reference

### Contract Engine (6 tools — BUILD1_PRD.md REQ-060)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_contract(contract_id)` | contract_id: str | `{id, type, version, spec, spec_hash, status}` or None |
| `validate_endpoint(service_name, method, path, response_body, status_code=200)` | 5 params | `{valid: bool, violations: [{field, expected, actual}]}` |
| `generate_tests(contract_id, framework="pytest", include_negative=True)` | 3 params | test file content as string |
| `check_breaking_changes(contract_id, new_spec)` | 2 params | `[{change, severity, affected_consumers}]` |
| `mark_implemented(contract_id, service_name, evidence_path)` | 3 params | `{marked: bool, total, all_implemented}` |
| `get_unimplemented_contracts(service_name=None)` | 1 optional param | `[{id, type, expected_service}]` |

### Codebase Intelligence (7 tools — BUILD1_PRD.md REQ-057)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `find_definition(symbol, language=None)` | 2 params | `{file, line, kind, signature}` |
| `find_callers(symbol, max_results=50)` | 2 params | `[{file, line, context}]` |
| `find_dependencies(file_path)` | 1 param | `{imports, imported_by, transitive_deps}` |
| `search_semantic(query, n_results=10)` | 2 params | `[{file, lines, content, score}]` |
| `get_service_interface(service_name)` | 1 param | `{endpoints, events_published, events_consumed}` |
| `check_dead_code(service_name=None)` | 1 optional param | `[{symbol, file, line, kind}]` |
| `register_artifact(file_path, service_name)` | 2 params | `{indexed, symbols_found, dependencies_found}` |

### Architect (3 tools — BUILD1_PRD.md REQ-059)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_service_map()` | none | `{services: [{name, domain, stack, estimated_loc}]}` |
| `get_contracts_for_service(service_name)` | 1 param | `[{id, role, type, counterparty, summary}]` |
| `get_domain_model()` | none | `{entities, relationships, state_machines}` |

---

## Appendix C: Configuration Example

```yaml
# config.yaml — Build 2 additions
agent_teams:
  enabled: true
  fallback_to_cli: true
  delegate_mode: true
  max_teammates: 5
  teammate_model: ""
  teammate_permission_mode: "acceptEdits"
  task_completed_hook: true

contract_engine:
  enabled: true
  mcp_command: "python"
  mcp_args: ["-m", "src.contract_engine.mcp_server"]
  database_path: "./data/contracts.db"
  validation_on_build: true
  test_generation: true

codebase_intelligence:
  enabled: true
  mcp_command: "python"
  mcp_args: ["-m", "src.codebase_intelligence.mcp_server"]
  database_path: "./data/symbols.db"
  chroma_path: "./data/chroma"
  graph_path: "./data/graph.json"
  replace_static_map: true
  register_artifacts: true

contract_scans:
  endpoint_schema_scan: true
  missing_endpoint_scan: true
  event_schema_scan: true
  shared_model_scan: true
```

---

## Appendix D: Modification Summary Table

| File | Current LOC | Action | Est. Added LOC | Impact |
|------|-------------|--------|----------------|--------|
| `agent_teams_backend.py` | NEW | CREATE | +550 | Agent Teams abstraction layer |
| `contract_client.py` | NEW | CREATE | +350 | Contract Engine MCP client |
| `codebase_client.py` | NEW | CREATE | +300 | Codebase Intelligence MCP client |
| `hooks_manager.py` | NEW | CREATE | +250 | Hook config generation |
| `claude_md_generator.py` | NEW | CREATE | +350 | CLAUDE.md generation |
| `contract_scanner.py` | NEW | CREATE | +300 | CONTRACT-001..004 scans |
| `mcp_client.py` | NEW | CREATE | +200 | MCP session management |
| `cli.py` | 6,214 | MODIFY | +300 | Pipeline integration |
| `agents.py` | 2,622 | MODIFY | +200 | Contract awareness prompts |
| `config.py` | 1,311 | MODIFY | +120 | 4 new config dataclasses |
| `state.py` | 305 | MODIFY | +50 | ContractReport, IntegrationReport |
| `mcp_servers.py` | 171 | MODIFY | +60 | 2 new MCP server configs |
| `contracts.py` | 651 | MODIFY | +150 | ServiceContractRegistry |
| `scheduler.py` | 1,369 | MODIFY | +100 | ExecutionBackend protocol |
| `code_quality_standards.py` | 665 | MODIFY | +40 | CONTRACT + INTEGRATION standards |
| `tracking_documents.py` | 988 | MODIFY | +100 | Contract compliance matrix |
| `codebase_map.py` | 957 | MODIFY | +50 | MCP-backed generation |
| `milestone_manager.py` | 934 | MODIFY | +20 | Contract-aware health |
| `e2e_testing.py` | 973 | MODIFY | +50 | Contract compliance E2E |
| `verification.py` | 1,141 | MODIFY | +80 | Contract compliance verification |
| `tech_research.py` | 746 | MODIFY | +20 | Build 1 service detection |
| **TOTAL** | **28,749** | | **+3,690** | **~32,439 LOC estimated** |

**New test LOC:** ~280 tests across ~8 test files (~2,000 LOC)
**Grand total with tests:** ~5,690 new LOC
