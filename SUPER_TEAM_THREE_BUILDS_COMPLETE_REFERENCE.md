# Super Agent Team — Complete Build Reference

## The Three Builds + Integration Run

**Total estimated infrastructure: ~145-150K LOC | ~$250-370 total cost | Each build independently testable**

| Build | What Gets Built | Est. LOC | Dependencies | Est. Cost |
|-------|----------------|----------|--------------|-----------|
| **Build 1** | Architect + Contract Engine + Codebase Intelligence | ~60K | None (foundation) | ~$80-120 |
| **Build 2** | Builder Fleet upgrade + Agent Teams integration | ~35K | Build 1 outputs | ~$60-90 |
| **Build 3** | Integrator + Quality Gate + Super Orchestrator | ~50K | Build 1 + 2 outputs | ~$70-100 |
| **Run 4** | Wire all 3 builds, end-to-end verification, fix pass | ~5K (fixes) | All builds complete | ~$40-60 |

The builds are sequenced so each uses the output of the previous. After all three, a dedicated integration run wires, reviews, and verifies the complete system.

---

## The Five Systems Being Built

The super team is not one system. It is five systems working as one, each handling a distinct concern at a distinct level of abstraction.

| System | Purpose | Technology | Est. LOC | Build |
|--------|---------|-----------|----------|-------|
| **1. Architect** | Decompose PRD into services + contracts | Python + Opus CLI | ~15K | Build 1 |
| **2. Contract Engine** | OpenAPI + AsyncAPI registry, validation, test generation | Python + FastAPI | ~20K | Build 1 |
| **3. Codebase Intelligence** | Live queryable index via MCP | Python + Tree-sitter + ChromaDB | ~25K | Build 1 |
| **4. Builder Fleet** | Upgraded agent-team with native agent teams + contracts | Python + Claude Code Agent Teams | ~35K | Build 2 |
| **5. Integrator + Quality Gate** | Cross-service wiring, 4-layer verification | Python + Docker + Schemathesis + Pact | ~30K | Build 3 |
| **Super Orchestrator** | Coordinates all 5 systems end-to-end | Python CLI | ~20K | Build 3 |

### How The Five Systems Work Together

```
PRD / Product Spec
       │
   [System 1: ARCHITECT]
       │
       ├── Service Map (8 services defined)
       ├── Contract Registry (OpenAPI + AsyncAPI + Domain Model)
       │
       ▼
   [System 2: BUILDER FLEET] ← 8 parallel instances
       │                         Each uses Claude Code agent teams
       │                         Each runs full 15-stage pipeline
       │                         Each registers artifacts with System 5
       │
       ├── Service A: 60K LOC, deployed, tested
       ├── Service B: 50K LOC, deployed, tested
       ├── ...
       ├── Service H: 45K LOC, deployed, tested
       │
       ▼
   [System 3: INTEGRATOR]
       │
       ├── Contract compliance: verified
       ├── Cross-service tests: generated + passing
       ├── Docker Compose (12 services): all healthy
       ├── API gateway: configured
       │
       ▼
   [System 4: QUALITY GATE]
       │
       ├── Layer 1 (per-service): ✅ from Builders
       ├── Layer 2 (cross-service): ✅ from Integrator
       ├── Layer 3 (system-level): security + performance + observability
       ├── Layer 4 (adversarial review): seam analysis
       │
       ▼
   [System 5: CODEBASE INTELLIGENCE] ← live throughout entire process
       │
       └── Queryable index of all services, contracts, entities, events
```

---

# BUILD 1: THE FOUNDATION (~60K LOC, ~$80-120)

## What Gets Built

Three services that form the foundation every other system depends on:
1. **The Architect** — service decomposition engine
2. **The Contract Engine** — OpenAPI/AsyncAPI registry + validation + test generation
3. **The Codebase Intelligence service** — Tree-sitter AST index + dependency graph + semantic search via MCP

## Build 1 PRD Structure — Single PRD, 7-8 Milestones

### M1: Core Data Models + Shared Infrastructure
- SQLite schema for contract registry, codebase index metadata
- Python project scaffolding with FastAPI, MCP SDK, Tree-sitter bindings, ChromaDB
- Docker Compose with PostgreSQL (pgvector extension), the three services, and a shared network

### M2: The Architect Service
- PRD parser that extracts service boundaries, domain contexts, and inter-service relationships
- Service Map generator (YAML output)
- Interview module for clarification questions
- Validation that service boundaries are coherent (no circular dependencies, no domain overlap, every entity owned by exactly one service)

**How the Architect works:** Runs as a single Opus session with extended context (1M token window). It reads the full PRD, asks clarifying questions via structured interview, then iterates on the decomposition. This is the one phase that benefits from human review before proceeding, because the cost of a wrong service decomposition propagates to every downstream build.

**Key insight:** The Architect does NOT use Claude Code agent teams. Service decomposition is a reasoning task, not a parallelizable task. One deep thinker outperforms five shallow ones for architecture.

**Architect produces three artifacts:**

**Artifact 1: Service Map** — A YAML document defining every service in the platform: its bounded domain, technology stack, external dependencies, team assignment, and estimated complexity. Example:
```yaml
services:
  auth-service:
    domain: Authentication & Authorization
    stack: { backend: Express+TypeScript, db: PostgreSQL }
    estimated_loc: 45000
  billing-service:
    domain: Subscription & Payment Processing
    stack: { backend: .NET 8, db: PostgreSQL }
    estimated_loc: 60000
```

**Artifact 2: Contract Registry** — The single source of truth for all inter-service communication:
- **OpenAPI 3.1 specs** for every HTTP API contract between services. Each endpoint, request schema, response schema, error code, pagination parameter. Generated from the Architect's understanding of the service boundaries.
- **AsyncAPI 3.1 specs** for every event-driven contract. Every message broker channel, every event schema, every publish/subscribe relationship. AsyncAPI is the industry standard for documenting event-driven architectures, used by eBay, Slack, TransferGo in production.
- **Shared data models** as JSON Schema. Entity definitions that cross service boundaries (e.g., UserProfile, Order, PaymentIntent) are defined once and referenced by all services that use them.
- Contracts are versioned and immutable within a build cycle. No Builder agent can modify a contract. They can only implement against it or flag a violation.

**Artifact 3: Domain Model** — The ubiquitous language for the entire platform. Entity names, relationship types, state machines, and cross-domain business rules. This prevents the classic drift where one service calls something a "User" and another calls it an "Account" and they represent the same concept with different shapes.

### M3: Contract Engine Core
- OpenAPI 3.1 spec storage, parsing, and validation
- AsyncAPI 3.1 spec storage, parsing, and validation
- JSON Schema registry for shared data models
- Version tracking with immutability within a build cycle
- Breaking change detection between versions

**Contract Engine is a standalone service** that stores, validates, and generates tests from the contracts produced by the Architect. It is the enforcement layer that prevents contract drift. Core capabilities:
- **Contract storage and versioning** — OpenAPI and AsyncAPI specs stored in a structured registry (SQLite-backed). Each contract has a version, a hash, and a list of consumers/providers.
- **Schema validation** — When a Builder produces an API endpoint, the Contract Engine validates that the actual response schema matches the contracted schema.

### M4: Contract Test Generation
- Schemathesis integration for property-based API testing from OpenAPI specs
- Pact test generation for consumer-driven contract testing
- Test output as runnable pytest/jest suites
- Contract compliance checker that takes an actual API response and validates against the spec

### M5: Codebase Intelligence Layer 1+2
- Tree-sitter AST parsing for Python, TypeScript, C#, Go (the four languages in our builds)
- Import/reference extraction and dependency graph construction with NetworkX
- Symbol table (all classes, functions, interfaces, their locations)
- Dead code detection (defined but never called — the M4 pattern scanner at system level)

**Codebase Intelligence is the new capability that makes 500K LOC manageable.** It's a live, queryable index of the entire codebase that any agent can access at any time. When an agent in Service A needs to understand how Service B's event schema works, it doesn't read all of Service B's source files. It queries the index: "What is the schema for OrderCreated event?" and gets back the exact type definition, its location, what publishes it, what consumes it, and when it last changed.

**Three layers:**
- **Layer 1: AST Index (Tree-sitter)** — Deterministic symbol queries. Used by Cursor, Aider, every serious AI code tool. Deterministic, no ML required. 40+ languages supported.
- **Layer 2: Dependency Graph (NetworkX + SQLite)** — PageRank for architectural relevance ranking. Research shows graph-based approach achieves highest efficiency (4.3-6.5% context utilization) while preserving architectural context.
- **Layer 3: Semantic Index (ChromaDB/pgvector)** — Vector embeddings of code chunks for semantic search: "find code that handles payment retry logic" even if those exact words don't appear. Uses language-specific embedding models for better semantic understanding. This layer is optional but valuable for discovery queries.

### M6: Codebase Intelligence Layer 3 + MCP
- ChromaDB vector embeddings for semantic code search
- MCP server exposing all query tools:
  - `find_definition(symbol)` → exact file/line for any class, function, interface
  - `find_callers(symbol)` → all call sites across the entire 500K LOC codebase
  - `find_dependencies(file)` → dependency graph for a specific file
  - `search_semantic(query)` → most relevant code chunks for a natural language query
  - `get_service_interface(service)` → all public APIs/events for a service
  - `check_dead_code(service)` → functions defined but never called (the M4 pattern)
- Incremental index updates — as each Builder generates code, it registers new artifacts. Agents working on Service B can query code that Service A's Builder just generated five minutes ago.

### M7: Architect MCP + Contract Engine MCP
- MCP server interfaces for both services
- The Architect exposes: `get_service_map`, `get_contracts_for_service`, `get_domain_model`
- The Contract Engine exposes: `validate_endpoint`, `get_contract`, `generate_tests`, `check_breaking_changes`
- End-to-end test: feed a sample PRD, generate service map + contracts, query them through MCP

### M8 (Optional): Integration + Docker
- Full Docker Compose with all three services
- Health checks
- API documentation
- CLI interface for manual testing
- Sample data showing a realistic 8-service decomposition

## Build 1 Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **AST Parsing** | Tree-sitter (python bindings) | Industry standard. 40+ languages. Used by Cursor, Aider, every major AI code tool. Deterministic, no ML required. |
| **Dependency Graph** | NetworkX + SQLite | Lightweight, no external services. PageRank for relevance. Research shows graph-based approach achieves highest efficiency (4.3-6.5% context utilization). |
| **Vector Search** | ChromaDB | Embeddable, no server required. Python-native. Sufficient for 500K LOC. Alternative: pgvector if already running PostgreSQL. |
| **API Contract Testing** | Schemathesis | Property-based testing from OpenAPI. 1.4-4.5x more defects found vs alternatives. CLI + Python API. Generates tests automatically from schema. |
| **Consumer Contract Testing** | Pact (Python) | De-facto standard. Polyglot. Consumer-driven. Bi-directional support with OpenAPI. Used by thousands of teams in production. |
| **Event Contract Spec** | AsyncAPI 3.1 | Industry standard for event-driven APIs. Protocol-agnostic. Code generation for all major languages. Contract testing via Microcks. Used by eBay, Slack, TransferGo. |
| **Agent Interface** | MCP (stdio) | Claude Code's native protocol. Teammates load MCP servers automatically. No HTTP overhead for local queries. Direct tool integration. |

## Build 1 Success Criteria
- All three services deploy in Docker Compose and pass health checks
- Architect produces valid Service Map + Contracts from a sample PRD
- Contract Engine validates schemas and generates runnable test suites
- Codebase Intelligence indexes a 50K+ LOC codebase in under 60 seconds
- All MCP tools respond correctly when queried by Claude Code
- Dead code detection finds at least the known M4 patterns

---

# BUILD 2: THE BUILDER FLEET UPGRADE (~35K LOC, ~$60-90)

## What Gets Built

Upgrade the existing agent-team to use Claude Code native agent teams for within-service orchestration, integrate with the Contract Engine and Codebase Intelligence from Build 1, and add contract-aware scanning.

## The Three Critical Upgrades to the Builder Fleet

### Upgrade 1: Claude Code Native Agent Teams

This is the transformative integration. Claude Code's agent teams feature, shipped with Opus 4.6, provides native multi-agent coordination that replaces our Python CLI orchestration for within-service work.

**Key capabilities from the research:**

- **Shared task list** with dependency tracking. Tasks move through pending/in-progress/completed states. File locking prevents race conditions when multiple teammates claim simultaneously.
- **Peer-to-peer messaging.** Unlike subagents which only report back to a parent, teammates can message each other directly. When the backend agent finishes type definitions, it messages the frontend agent directly. No round-trip through the coordinator.
- **Team lead + delegate mode.** The lead coordinates, observes, and synthesizes. In delegate mode it ONLY coordinates, never implements. This maps directly to our orchestrator pattern.
- **Self-claiming.** After finishing a task, a teammate picks up the next unassigned, unblocked task autonomously.
- **Hooks.** TeammateIdle and TaskCompleted hooks enforce rules. Exit code 2 sends feedback and keeps the teammate working. This enables our convergence mandate and review guardrails.

**What this replaces:** Our Python CLI's agent spawning, task assignment, result collection, and merge conflict management. The orchestration code shrinks approximately 60% while gaining native file awareness, git integration, and structured communication.

**What this does NOT replace:** Our prompt engineering (review criteria, convergence logic, scan directives), the 15-stage pipeline structure, the 13 self-healing fix loops, and the quality scanning infrastructure. These are the IP. Agent teams provides the coordination substrate; our prompts provide the judgment.

**Critical detail:** Teammates load CLAUDE.md and MCP servers automatically but don't inherit the lead's conversation history — so our prompts transfer via project files, not conversation context. Known limitation: experimental, no session resumption, no nested teams. Build 2 is designed so it's revertible if agent teams proves unreliable.

### Upgrade 2: Contract-Aware Generation

Each Builder receives the Contract Registry and is instructed to implement against it. New scan directives enforce compliance:

- **CONTRACT-001:** Every API endpoint must match its OpenAPI spec (path, method, request/response schema, status codes)
- **CONTRACT-002:** Every event publisher must match its AsyncAPI spec (channel, payload schema, headers)
- **CONTRACT-003:** Every event consumer must handle the exact schema defined in the contract
- **CONTRACT-004:** Shared data model types must match the JSON Schema definitions exactly

These scans are enforced in the post-orchestration scan phase, alongside the existing mock data, XREF, and database scans.

### Upgrade 3: Codebase Intelligence Integration

Replace the static CODEBASE_MAP.md with live MCP queries to the Codebase Intelligence service. Builders register their generated code with the index as they produce it. Agents query the index when they need context about other parts of the system.

## Build 2 PRD Structure — Single PRD, 6-7 Milestones

### M1: Agent Teams Integration Layer
- Replace our Python CLI agent spawning with Claude Code native agent teams
- Map our current agent roles (architect, code-writer, reviewer, test-engineer, wiring-verifier) to Claude Code teammate roles
- Implement delegate mode for the orchestrator
- Wire the TeammateIdle and TaskCompleted hooks to enforce convergence mandates and review guardrails
- **This is the hardest milestone because it touches the core orchestration loop**

### M2: Contract-Aware Pipeline
- Add the four CONTRACT scans (001-004) to the post-orchestration scan phase
- Integrate with the Contract Engine MCP server so Builders can query contracts during generation
- Add contract validation as a gate between milestone completion and the next milestone

### M3: Codebase Intelligence Integration
- Replace the static CODEBASE_MAP.md with live MCP queries to the Codebase Intelligence service
- Builders register their generated code with the index as they produce it
- Agents query the index when they need context about other parts of the system

### M4: Multi-Instance Coordination
- The ability to run multiple Builder instances in parallel across different service directories
- Shared config that tells each Builder which service it owns, where the contract registry is, and how to reach the codebase index
- Result collection and Build Report aggregation

### M5: Enhanced Prompts + Directives
- Updated prompt templates that include contract awareness, codebase index queries, and cross-service context
- New scan directives for contract compliance
- Updated review criteria that check for contract violations

### M6: End-to-End Test
- Deploy Build 1 services
- Run the upgraded Builder against a test PRD (TaskFlow Pro or equivalent)
- Verify the Builder uses MCP to query contracts and codebase index
- Verify contract scans catch deliberate violations
- Verify multi-instance parallelism works

## Build 2 Critical Design Decisions

**Agent Teams vs. our Python CLI:** We keep our Python CLI as the top-level orchestrator (spawning one Builder per service) but replace the within-Builder agent coordination with native agent teams. This gives us: Python CLI for service-level parallelism (proven, reliable, our code) + Claude Code agent teams for within-service parallelism (native, better file awareness, peer messaging). Two-level hierarchy.

**Prompt preservation:** The prompts, review criteria, convergence logic, and scan configurations are the intellectual property developed over 12 versions. These transfer directly into the CLAUDE.md files that agent teams teammates load automatically. Every teammate inherits the project context including CLAUDE.md.

**Hooks as guardrails:** The convergence mandate ("do not mark this task complete until all requirements are met") and review guardrails ("run adversarial review before declaring done") become TaskCompleted hooks. Exit code 2 prevents completion and sends feedback. This is a native enforcement mechanism for our behavioral controls.

## Build 2 Success Criteria
- Builder uses Claude Code agent teams for internal coordination
- Builder queries Contract Engine MCP and gets valid responses
- Builder queries Codebase Intelligence MCP and gets valid responses
- CONTRACT scans detect deliberate violations in test scenarios
- Two Builders run in parallel on different services without conflicts
- Generated code registers with codebase index incrementally

---

# BUILD 3: THE INTEGRATOR + SUPER ORCHESTRATOR (~50K LOC, ~$70-100)

## What Gets Built

The cross-service integration framework, the four-layer quality gate, and the Super Orchestrator that coordinates all five systems end-to-end.

## Build 3 PRD Structure — Single PRD, 7-8 Milestones

### M1: Integration Test Framework
- Multi-service Docker Compose orchestration
- Service startup sequencing with health check conditions (`service_healthy`)
- Traefik API gateway with automatic Docker service discovery via container labels
- Cross-service test runner that can execute a test flow spanning multiple services

**The Integrator** is the system that doesn't exist yet and is the hardest one to build. After the Builders finish, the Integrator wires everything together. It reads every Build Report. It reads the Contract Registry. Then it verifies everything.

### M2: Contract Compliance Verification
- Automated Schemathesis runs against every deployed service
- Automated Pact provider verification
- Report generation showing compliance per-service and per-endpoint
- Fix loop that feeds violations back to the relevant Builder for remediation

**Contract Compliance** — does each service's actual API match the contract? Not just "does the endpoint exist" but "does the response schema match, do the error codes match, do the pagination parameters match." This is automated — generate contract tests from the OpenAPI specs and run them against each service.

### M3: Cross-Service Integration Tests
- Test flow generator that reads the Contract Registry and Domain Model to produce end-to-end test scenarios
- Test executor that orchestrates multi-service flows
- Data flow tracer that follows a request through every service and verifies transformations
- Boundary testing (camelCase/snake_case, timezone handling, null vs missing fields)

**Cross-Service Integration Tests** — the Integrator generates tests that span services. "Create a user in auth service → create an order in core API → trigger a notification → verify notification service received the event." These tests require all services running simultaneously in Docker Compose.

### M4: Quality Gate Layers 3-4
- **Security scanner:** JWT validation on every endpoint, no unauthenticated access, CORS headers
- **Observability checker:** consistent log format, trace ID propagation, health endpoints
- **System-level dead code detection** via Codebase Intelligence (events published but never consumed, contracts defined but never implemented)
- **Adversarial review fleet** that reads ALL services focusing on the seams

**The Quality Gate has four layers, gated sequentially:**
- **Layer 1 (per-service):** Does each service pass its own tests, build cleanly, deploy successfully? Already done by Builders.
- **Layer 2 (cross-service contract compliance):** Does each service's actual API match the contracted API? Automated via Schemathesis + Pact.
- **Layer 3 (system-level):** Security, performance, observability. Are JWTs validated everywhere? Are trace IDs propagated? Do health endpoints exist? Can the system handle concurrent requests? This is the XREF scanner elevated to system-level cross-reference.
- **Layer 4 (adversarial review):** Human-quality review of the seams. The review fleet reads all services simultaneously, looking for subtle integration issues. If Service A publishes events that no service consumes, you have a dead system.

**Each layer gates the next.** A service that fails Layer 1 doesn't get to Layer 2. A system that fails Layer 2 doesn't get to Layer 3. This prevents wasting expensive integration tests on broken individual services.

### M5: Super Orchestrator
- The top-level CLI that coordinates the full pipeline: Architect → Contract Engine → parallel Builders → Integrator → Quality Gate
- State management for pause/resume/retry
- Cost tracking
- Progress reporting
- Failure recovery (if one Builder fails, others continue; failed service can be retried)

### M6: Configuration + CLI
- YAML configuration for the entire super team (service count, technology preferences, quality thresholds, cost limits)
- CLI commands:
  - `super-team init` — create project
  - `super-team plan` — run Architect only
  - `super-team build` — run Builders
  - `super-team integrate` — run Integrator
  - `super-team verify` — run Quality Gate
  - `super-team run` — full pipeline

### M7: End-to-End Test
- Run the complete pipeline against a small (3-service) test application
- Verify every system communicates correctly
- Generate a final system report

## Build 3 Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **API Gateway** | Traefik v3 | Auto-discovers Docker containers via labels. Zero manual config for routing. Built-in health checks, load balancing, SSL. 3B+ downloads, 55K GitHub stars. |
| **Service Orchestration** | Docker Compose v2 | depends_on with service_healthy conditions. Health checks with start_period for initialization grace. service_completed_successfully for migrations. Proven at 5 services in DrawSpace V2, extends to 12+. |
| **Integration Tests** | pytest + httpx + Testcontainers | pytest for test orchestration. httpx for async HTTP calls across services. Testcontainers for Docker management from tests. |
| **Contract Compliance** | Schemathesis + Pact | Schemathesis for property-based OpenAPI testing. Pact for consumer-driven contracts. |

## Build 3 Success Criteria
- Complete pipeline runs end-to-end without human intervention
- 3-service test app deploys, all health checks pass, integration tests pass
- Contract violations are detected and reported
- Quality Gate layers execute sequentially with proper gating
- Super Orchestrator CLI works for all commands

---

# RUN 4: INTEGRATION + VERIFICATION (~5K LOC fixes, ~$40-60)

## What Happens

Wire all 3 builds together, end-to-end verification, fix pass. This is not a build — it's a verification and remediation run.

### Phase 1: Wiring Verification
Verify that Build 1 services (Architect, Contract Engine, Codebase Intelligence) are accessible via MCP from Build 2 (Builder Fleet). Verify that Build 2 outputs feed correctly into Build 3 (Integrator + Quality Gate).

### Phase 2: Builder Fleet Integration Test
Run a test build of a small service and confirm the Builder makes MCP calls for contract validation and code queries.

### Phase 3: End-to-End Pipeline Test
Feed a real PRD (a simplified 3-service application) through the complete pipeline: Architect decomposes it, Contract Engine stores contracts, three Builders generate services in parallel, Integrator wires them, Quality Gate verifies them.

### Phase 4: Fix Pass
Catalog every issue found in Phases 1-3. Prioritize P0 (system won't function) through P3 (nice-to-have). Apply fixes using the proven fix pass methodology: exhaustive prompt, parallel agents, convergence cycles.

### Phase 5: Audit + Report
Audit each system against its success criteria. Produce the final Super Team Audit Report with per-system scores, integration test results, and honest assessment of remaining gaps.

## Run 4 Success Criteria
- Complete pipeline runs end-to-end without human intervention
- 3-service test app deploys, all health checks pass, integration tests pass
- Contract violations are detected and reported
- Codebase Intelligence indexes the generated code and responds to MCP queries
- Total time from PRD to deployed system: under 6 hours for 3-service app

---

# HOW THE SUPER TEAM RUNS A 500K LOC BUILD (Post-Completion)

Once all three builds and the integration run are complete, the exact execution flow:

**Step 1: Input.** Human provides a comprehensive PRD describing the desired platform. Example: "Enterprise project management platform with authentication, billing, real-time collaboration, file storage, notification system, reporting engine, admin dashboard, and public API."

**Step 2: Architect (30-60 min).** Single Opus session decomposes the PRD into 8-10 services. Produces Service Map, Contract Registry, and Domain Model. Human reviews the decomposition (optional but recommended for the first few runs).

**Step 3: Contract Engine (5 min).** Ingests all contracts. Validates schema consistency. Generates contract test suites for every endpoint. Stores in registry.

**Step 4: Builder Fleet (4-8 hours).** 8-10 Builder instances launch in parallel. Each runs the full 15-stage pipeline against its service. Each uses Claude Code agent teams for within-service parallelism. Each queries Contract Engine and Codebase Intelligence via MCP. Each produces a deployed Docker service with tests. Cost: ~$80-150 for all builders combined.

**Step 5: Integrator (1-2 hours).** Generates top-level Docker Compose with Traefik. Runs contract compliance tests. Generates and executes cross-service integration tests. Traces data flows. Feeds violations back to relevant Builders for fix loops.

**Step 6: Quality Gate (1-2 hours).** Four-layer verification. Per-service quality (already done by Builders). Cross-service quality (from Integrator). System-level security/performance/observability. Adversarial review at scale.

**Step 7: Output.** A fully deployed 500K LOC platform running in Docker Compose with: every service passing its tests, every contract verified, every cross-service integration tested, API gateway configured, health checks passing, and a comprehensive audit report.

**Total estimated time: 8-14 hours. Total estimated cost: $150-300.**

---

# HONEST RISK ASSESSMENT

## Risk 1: Agent Teams Is Experimental
Claude Code agent teams shipped one week ago with Opus 4.6. Known limitations: no session resumption, no nested teams, one team per session. The coordination quality is unproven at our scale. If agent teams proves unreliable, we fall back to our proven Python CLI orchestration (which works but is less efficient).

**Mitigation:** Build 2 is designed so agent teams integration is isolated. If it fails, we revert to the existing orchestration without losing Builds 1 or 3.

## Risk 2: Cross-Service Wiring at Scale
The M4 pattern (built correctly, never wired) is our biggest proven failure mode. At 8-12 services, the number of possible wiring failures increases combinatorially. The Integrator is specifically designed to catch this, but it's the newest, least proven system.

**Mitigation:** Contract-first approach means wiring failures surface as contract violations (testable) rather than silent behavioral bugs (hard to detect). The Quality Gate Layer 4 adversarial review specifically hunts for unwired connections.

## Risk 3: Context Ceiling for Integration Testing
Generating integration tests that span 8 services requires understanding 8 services simultaneously. Even with the Codebase Intelligence index, the agent generating integration tests needs enough context to reason about cross-service flows. This may exceed effective reasoning capability.

**Mitigation:** Contract Registry provides a compressed representation of inter-service communication. The agent doesn't need to read 500K LOC. It reads the contracts (maybe 5K LOC total) and generates tests against those. The contracts ARE the compressed context.

## Risk 4: Infrastructure Complexity
Building the super team itself is ~145K LOC of infrastructure. That's roughly equal to everything we've built so far combined. If the infrastructure has bugs, the applications it generates will inherit those bugs systematically.

**Mitigation:** Each build is independently tested before proceeding. The integration run specifically hunts for infrastructure bugs. And we have the proven fix pass methodology to remediate.

## Risk 5: Prompt Quality Transfer
The current agent-team's quality comes from 12 versions of prompt engineering. Transferring those prompts into CLAUDE.md files for agent teams teammates may lose nuance. Prompt compliance is a behavioral property that can only be verified through real builds.

**Mitigation:** Run the first 500K build with extra scrutiny on prompt compliance. Compare agent behavior in new system vs. old system. Iterate on CLAUDE.md until behavioral parity is achieved.

---

# PREDICTIONS

| Outcome | Probability | Reasoning |
|---------|------------|-----------|
| **Build 1 succeeds (foundation)** | **90%** | Standard Python services. Well-understood technologies. No agent coordination complexity. Within proven generation capability. |
| **Build 2 succeeds (builder upgrade)** | **70%** | Agent teams integration is new and experimental. MCP wiring across services adds complexity. But core generation pipeline is proven. |
| **Build 3 succeeds (integrator)** | **75%** | Docker orchestration proven at 5 services. Traefik is mature. But cross-service test generation and adversarial review at scale are new. |
| **Run 4 achieves full integration** | **65%** | Fix pass methodology proven (51→90 on M4). But wiring 3 independent builds has unknown-unknowns. |
| **Compound: full system works** | **~30-40%** | Product of above. Realistic. But even partial success (e.g., 250K working) is a breakthrough. |
| **First 500K LOC app generation** | **20-30%** | Requires full system working AND a well-defined target app. First attempt will likely hit 250-350K functional LOC with gaps. |
| **250K LOC app (5 services)** | **55-65%** | 5 services at 50K each. Contract-first integration. Agent-team proven at 100K per service. Running 5x with shared contracts is coordination, not generation. |

**Key insight:** Even if we don't hit 500K on the first attempt, a working super team that reliably produces 250K LOC functional applications would be unprecedented. No existing AI system comes close. Devin's 3/20 success rate is on single-service tasks. We'd be demonstrating multi-service, multi-language, contract-verified platform generation.

---

# CORE PROBLEMS THE SUPER TEAM SOLVES

**Context ceiling:** At 100K LOC, the orchestrator can still hold a mental model of the full system. At 500K, no single agent can understand the whole thing. That's not a prompt engineering problem, it's an architectural one. Solution: Codebase Intelligence gives every agent queryable access to the full codebase without reading it.

**Cross-service wiring:** The M4 pattern — "this service produces events but no service consumes them" or "this contract is defined but no service implements it." At 8-12 services, the number of possible wiring failures increases combinatorially. Solution: Contract-first approach + Integrator + Quality Gate Layer 4 adversarial review.

**Contract drift:** When 8 services are built in parallel by independent agents, each makes micro-decisions about API shapes, field names, error codes. Without enforced contracts, these decisions diverge. Service A sends camelCase; Service B expects snake_case. Both pass unit tests. Integration fails silently. Solution: Contract Engine enforces immutable contracts that all Builders implement against.

---

# IMMEDIATE NEXT STEPS

1. Review and finalize blueprint. Flag gaps, wrong assumptions, missing capabilities.
2. Write the Build 1 PRD using exhaustive implementation prompt template (full milestone breakdown, agent team composition, architecture discovery phase, success criteria).
3. Execute Build 1 (~90% success probability). Its output (MCP servers for contracts and codebase intelligence) is tested independently.
4. Based on Build 1 results, refine Build 2 PRD. Agent teams integration may need adjustment.
5. Execute Builds 2 and 3 sequentially, with review checkpoints.
6. Integration Run 4. Wire, test, fix, verify.
7. First real 500K LOC generation attempt: start with 3 services (150K) → 5 services (250K) → 8-10 services (500K).
