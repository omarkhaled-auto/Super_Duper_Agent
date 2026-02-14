# PRD Normalizer (Phase -1) — EXHAUSTIVE IMPLEMENTATION PROMPT

> **Purpose:** This prompt is a self-contained implementation guide for adding a "PRD Normalization Phase (-1)" to the agent-team CLI tool. Feed this entire document to Claude to implement the feature from scratch. Every regex, function signature, integration point, and test case is specified with codebase-verified precision.

---

## MISSION

Implement a new **Phase -1: PRD Normalization** in the `agent-team` CLI tool. This phase takes ANY rough/basic PRD file as input and transforms it into the agent-team's exact expected format — the format that triggers all 150+ scan checkpoints, parser functions, and prompt injection hooks in the pipeline. The normalizer MUST NEVER invent content that is not present or reasonably inferable from the original PRD. It is a **format translator**, not a content generator.

The feature runs as a multi-agent sub-orchestrator pipeline BEFORE Phase 0 (Interview). When the user provides `--prd path/to/rough_prd.md`, Phase -1 reads it, analyzes structural gaps, normalizes it into the target format, validates the output, and writes the normalized PRD to `.agent-team/PRD_NORMALIZED.md`. All subsequent phases then consume the normalized version instead of the raw input.

---

## STEP 0 — CODEBASE EXPLORATION (MANDATORY FIRST)

Before writing ANY code, you MUST read and understand these files in the agent-team codebase at `src/agent_team/`. This is not optional — the implementation must integrate seamlessly with existing patterns.

### 0.1 Read These Files Completely

| File | Why |
|------|-----|
| `config.py` | Understand `AgentTeamConfig`, all sub-config dataclasses, `_dict_to_config()` signature (`-> tuple[AgentTeamConfig, set[str]]`), `load_config()`, depth-gating pattern |
| `cli.py` | Understand phase ordering (Phase 0 Interview at ~line 3661, Phase 0.25 Constraints at ~line 3722, Phase 0.5 Codebase Map at ~line 3763, Phase 0.6 Design Reference at ~line 3790). Find `args.prd` usage, `_current_state.completed_phases`, `_current_state.artifacts`, crash-isolation try/except pattern |
| `quality_checks.py` | Study `Violation` dataclass (fields: `check`, `message`, `file_path`, `line`, `severity`), `_parse_svc_table()`, `_parse_field_schema()`, `_RE_SVC_ROW_START` regex, and the pattern of `run_*_scan()` functions returning `list[Violation]` |
| `agents.py` | Study prompt constant patterns (`ARCHITECT_PROMPT`, `CODE_WRITER_PROMPT`), `build_orchestrator_prompt()` signature, how prompt sections are injected |
| `prd_chunking.py` | Study `PRDChunk` dataclass, `detect_large_prd()` (50KB threshold), `create_prd_chunks()`, `build_prd_index()`, `_SECTION_PATTERNS` regex list |
| `milestone_manager.py` | Study `_RE_MILESTONE_HEADER` regex, `parse_master_plan()`, `MasterPlanMilestone` dataclass |
| `state.py` | Study `RunState`, `ConvergenceReport`, how `completed_phases` is tracked |
| `mcp_servers.py` | Study `get_mcp_servers()` pattern for sub-orchestrator MCP config |

### 0.2 Verify These Critical Patterns Before Coding

After reading, confirm you understand:

1. **Config tuple return**: `_dict_to_config()` returns `tuple[AgentTeamConfig, set[str]]` — the `set[str]` tracks user-overridden keys for depth-gating respect
2. **Violation field names**: `.check`, `.file_path`, `.line`, `.severity`, `.message` — NOT `.code`, `.file`
3. **Phase ordering**: Phase -1 must run BEFORE Phase 0 (Interview), AFTER config loading (~line 3529)
4. **Crash isolation**: Every phase block is wrapped in `try/except Exception` with `print_warning()` fallback — Phase -1 must follow this pattern
5. **completed_phases tracking**: Phases append to `_current_state.completed_phases` on success
6. **PRD chunking happens AFTER Phase -1**: The normalized PRD is what gets chunked, not the raw input

---

## STEP 1 — TARGET FORMAT SPECIFICATION

The normalizer must produce PRDs with EXACTLY these 12 sections in this order. Each section has a specific structural contract that triggers downstream parsers and scans.

### 1.1 Section Order (12 mandatory sections)

```
## 1. Executive Overview
## 2. Technology Stack
## 3. User Roles and Permissions
## 4. Entity Definitions
## 5. Enum and Status Registries
## 6. Milestone Breakdown
## 7. Seed Data Requirements
## 8. UI Requirements
## 9. Business Rules
## 10. Cross-Cutting Concerns
## 11. Docker Compose Specification
## 12. Constraints
```

### 1.2 Section Structural Contracts

#### Section 1: Executive Overview
- **Format**: Narrative paragraphs
- **Must contain**: Product name, target market, success metrics, concurrency/performance targets
- **Parser trigger**: None (human-readable context)

#### Section 2: Technology Stack
- **Format**: Subsections `### 2.1 Backend`, `### 2.2 Frontend`, `### 2.3 Database`, `### 2.4 Infrastructure`
- **Each subsection**: Markdown table with columns `| Technology | Version | Purpose |`
- **Must contain**: Framework names, version ranges, one-line purpose descriptions
- **Parser triggers**:
  - `run_dual_orm_scan()` — triggers when TWO ORMs listed (e.g., EF Core + Dapper)
  - `run_silent_data_loss_scan()` — triggers when MediatR/CQRS pattern mentioned
  - `ENUM-004` check — triggers when `JsonStringEnumConverter` mentioned
  - `run_e2e_quality_scan()` — triggers based on frontend framework detection (Angular/React/Vue)
  - XREF scan — triggers based on HttpClient/fetch/axios detection

#### Section 3: User Roles and Permissions
- **Format**: Role table + Permission Matrix table + Action-Level Permissions table
- **Role table columns**: `| Role | Code | Description |`
- **Permission matrix columns**: `| Entity — Action | Role1 | Role2 | ... |`
- **Parser triggers**:
  - `browser_testing.py` `_RE_ROLE` pattern — extracts role names from seed data proximity
  - E2E test generation — role-based API testing uses these roles

#### Section 4: Entity Definitions
- **Format**: One `### 4.N EntityName` subsection per entity
- **Each entity**: Markdown table with columns `| Field | Type | Nullable | Default | Constraints | Notes |`
- **After table**: `**Navigation Properties:**` subsection listing FK relationships, `**Indexes:**` subsection
- **Parser triggers**:
  - `run_default_value_scan()` DB-004 — checks `bool` fields have explicit defaults
  - `run_default_value_scan()` DB-005 — checks nullable fields have null guards
  - `run_relationship_scan()` DB-006..008 — checks FK bidirectional navigation
  - `run_api_contract_scan()` — validates DTO fields match entity field names

#### Section 5: Enum and Status Registries
- **Format**: One subsection per enum
- **Each enum contains**:
  - `**Values:**` line with PascalCase pipe-separated values (e.g., `Admin | ProjectManager | Engineer | Viewer`)
  - `**Database type:**` line (e.g., `VARCHAR(20) NOT NULL`)
  - `**C# enum:**` fenced code block
  - `**TypeScript:**` fenced code block with `export type` declaration
  - Optional `**State Transitions:**` table with columns `| From | To | Allowed | Trigger | Who Can Trigger |`
- **Parser triggers**:
  - `ENUM-004` scan — validates `JsonStringEnumConverter` registration when enums exist
  - `MOCK-001..007` — validates enum values are not hardcoded inline
  - Prompt injection: "Enum/Status Registry (ENUM-001..003)" in agents.py

#### Section 6: Milestone Breakdown
- **Format**: One `### Milestone N: Title — Subtitle` subsection per milestone
- **Each milestone contains**:
  - `**Entities:**` line (comma-separated entity names)
  - `**Enums:**` line (comma-separated enum names)
  - `**Deliverables:**` narrative paragraph with implementation specifics
  - `**SVC Endpoints: SVC-XXX through SVC-YYY**` range line
  - Full SVC table with 6 columns: `| SVC | Frontend Service.Method | Backend Endpoint | HTTP Method | Request DTO | Response DTO |`
- **SVC DTO notation**: Inline TypeScript-style `{ field: type, field: type }` with braces — CRITICAL for `_parse_field_schema()` which requires braces to return non-empty dict
- **DTO field casing**: camelCase for JSON fields (matching System.Text.Json default serialization for C# backends, or whatever the tech stack's default serialization produces)
- **Parser triggers**:
  - `_parse_svc_table()` — regex `^\|\s*SVC-\d+\s*\|` (MULTILINE) detects rows
  - `_parse_field_schema()` — parses `{ field: type }` into dict
  - `_check_backend_fields()` — API-001 validation
  - `_check_frontend_fields()` — API-002 validation
  - `_check_type_compatibility()` — API-003 validation
  - `run_endpoint_xref_scan()` — cross-references SVC endpoints with actual code
  - `milestone_manager.py` `_RE_MILESTONE_HEADER` — parses `## Milestone N:` headings

#### Section 7: Seed Data Requirements
- **Format**: Subsections for each seed entity type
- **Seed Users table columns**: `| Role | Email | Password | Full Name | Phone | IsActive |`
- **Password format**: Plaintext (e.g., `Admin123!`) — consumed by `browser_testing.py` credential extraction
- **Parser triggers**:
  - `browser_testing.py` `_RE_EMAIL` / `_RE_PASSWORD` / `_RE_ROLE` — credential extraction with 10-15 line proximity
  - `_SEED_PATTERNS` glob list — searches for seed data files
  - Prompt injection: "Seed Data Completeness (SEED-001..003)" in agents.py

#### Section 8: UI Requirements
- **Format**: Design direction, component library specification, page-by-page layout descriptions
- **Must reference**: Specific component names from the chosen library (e.g., PrimeNG DataTable, MUI DataGrid)
- **Parser triggers**:
  - `run_ui_compliance_scan()` UI-001..004 — validates font families, component types, config files, spacing
  - `design_reference.py` — extracts UI requirements for `UI_REQUIREMENTS.md`

#### Section 9: Business Rules
- **Format**: Subsections grouping related rules with narrative explanations
- **Must contain**: Validation rules, authorization rules, workflow rules, data integrity rules
- **Parser trigger**: PRD reconciliation scan (PRD-001) compares rules against implementation

#### Section 10: Cross-Cutting Concerns
- **Format**: Subsections for error handling, logging, security, performance, etc.
- **Must contain**: HTTP status codes, JWT configuration, CORS policy, file upload limits
- **Parser triggers**:
  - `run_e2e_quality_scan()` E2E-005 — auth middleware checking
  - `run_e2e_quality_scan()` E2E-007 — 403 detection
  - Prompt injection: JWT validation exception list, file upload constraints

#### Section 11: Docker Compose Specification
- **Format**: Fenced YAML code block with `docker-compose.yml` content, followed by Environment Variables table and Example `.env` file
- **Env var table columns**: `| Variable | Required | Default | Description |`
- **Parser triggers**:
  - `run_deployment_scan()` DEPLOY-001 — port mismatch between compose and .env
  - `run_deployment_scan()` DEPLOY-002 — undefined env vars (vars in compose but not in .env)
  - `run_deployment_scan()` DEPLOY-003 — CORS origin mismatch
  - `run_deployment_scan()` DEPLOY-004 — service name mismatch

#### Section 12: Constraints
- **Format**: Numbered list (1-N) with narrative descriptions
- **Each constraint**: One mandatory rule that maps to a scan family
- **Must cover these scan families** (at minimum, whatever applies to the tech stack):
  - MOCK-xxx (mock data prohibition)
  - ENUM-xxx (enum casing consistency)
  - SDL-xxx (save/persist after writes)
  - DB-xxx (boolean defaults, FK navigation, null guards)
  - API-xxx (DTO field matching)
  - DEPLOY-xxx (Docker service consistency)
  - ASSET-xxx (static asset references)
  - SEED-xxx (seed data completeness)
- **Parser trigger**: Constraint extraction in Phase 0.25 reads this section

---

## STEP 2 — ARCHITECTURE

### 2.1 New File: `src/agent_team/prd_normalizer.py`

This is the main module. It contains:

1. **Detection function** — `needs_normalization(content: str) -> NormalizationAnalysis`
2. **7-step pipeline** — the core transformation engine
3. **Structural validator** — validates output matches target format using actual parser regex
4. **Faithfulness validator** — ensures no content was invented
5. **Prompt constants** — for each agent in the pipeline

### 2.2 Pipeline Architecture (7 Steps)

```
Step 1: Analyzer Agent
    Reads raw PRD, produces structural analysis JSON
    (which sections exist, which are missing, tech stack detection)
         |
Step 2: Entity Normalizer Agent
    Extracts entities, produces 6-column tables + enums with
    PascalCase values, C#/TS blocks, state transitions
         |
    +----+----+
    |         |
Step 3a:  Step 3b:
API         Metadata
Normalizer  Normalizer
(SVC        (Seeds,
 tables,     Docker,
 DTOs,       Constraints,
 milestones) UI, Business
             Rules)
    |         |
    +----+----+
         |
Step 4: Assembler
    Combines all outputs into final 12-section PRD
         |
Step 5: Structural Validator
    Runs regex-based checks against target format
    (reuses quality_checks.py patterns)
         |
Step 6: Faithfulness Validator
    Compares normalized PRD against original
    (ensures no invented content, flags gaps)
         |
Step 7: Output Writer
    Writes to .agent-team/PRD_NORMALIZED.md
    Writes validation report to .agent-team/PRD_NORMALIZATION_REPORT.md
```

### 2.3 Agent Execution Model

Steps 1, 2, 4, 6 run as **sub-orchestrator calls** (same pattern as `_run_prd_reconciliation()` in cli.py — async function calling `orchestrate()` with a specialized prompt and MCP servers).

Steps 3a and 3b run **in parallel** (same pattern as parallel milestone execution).

Steps 5 and 7 are **local Python functions** (no LLM needed — pure regex validation and file I/O).

### 2.4 Faithfulness Guarantees

The normalizer MUST obey these rules:

| Rule | Description |
|------|-------------|
| **NO-INVENT** | Never add entities, endpoints, enums, business rules, or constraints not present in the original PRD |
| **STANDARD-FIELDS-EXCEPTION** | May add standard infrastructure fields (Id, CreatedAt, UpdatedAt, CreatedBy, IsActive) to entities IF the original PRD defines entities but omits these fields. Mark with `[inferred]` note |
| **TRACEABILITY-MAP** | Every section in the normalized PRD must map back to a section/paragraph in the original PRD. The report documents this mapping |
| **GAP-FLAGGING** | If a required section cannot be populated from the original PRD, insert a `<!-- GAP: [section name] — not present in source PRD -->` comment and list it in the report |
| **NO-RENAME** | Entity names, field names, endpoint paths MUST match the original PRD exactly (casing normalization is allowed per tech stack conventions) |
| **CASING-INFERENCE** | Field casing for DTOs is inferred from tech stack: C#/ASP.NET → camelCase JSON, Python/Django → snake_case, Node/Express → camelCase |

---

## STEP 3 — IMPLEMENTATION SPECIFICATION

### 3.1 Config Additions (`config.py`)

Add this dataclass BEFORE `AgentTeamConfig`:

```python
@dataclass
class PRDNormalizationConfig:
    """Configuration for Phase -1 PRD Normalization."""
    enabled: bool = True
    # "auto" = normalize only if needs_normalization() returns True
    # "always" = always normalize
    # "never" = skip normalization
    mode: str = "auto"
    # How aggressively to infer missing content
    # "strict" = only format-translate, flag all gaps
    # "moderate" = add standard fields (Id, timestamps), infer casing
    # "aggressive" = generate placeholder SVC tables from endpoint lists
    inference_level: str = "moderate"
    # What to do with gaps
    # "flag" = insert GAP comments and proceed
    # "warn" = flag + print warnings
    # "block" = fail normalization if critical gaps exist
    gap_handling: str = "warn"
    # Max LLM calls for the pipeline (budget guard)
    max_pipeline_budget_usd: float = 2.0
    # Output paths (relative to cwd)
    output_file: str = ".agent-team/PRD_NORMALIZED.md"
    report_file: str = ".agent-team/PRD_NORMALIZATION_REPORT.md"
```

Add to `AgentTeamConfig`:
```python
prd_normalization: PRDNormalizationConfig = field(default_factory=PRDNormalizationConfig)
```

Update `_dict_to_config()`:
```python
# In the section parsing config subsections:
if "prd_normalization" in data:
    norm_data = data["prd_normalization"]
    config.prd_normalization = PRDNormalizationConfig(
        enabled=norm_data.get("enabled", True),
        mode=norm_data.get("mode", "auto"),
        inference_level=norm_data.get("inference_level", "moderate"),
        gap_handling=norm_data.get("gap_handling", "warn"),
        max_pipeline_budget_usd=norm_data.get("max_pipeline_budget_usd", 2.0),
        output_file=norm_data.get("output_file", ".agent-team/PRD_NORMALIZED.md"),
        report_file=norm_data.get("report_file", ".agent-team/PRD_NORMALIZATION_REPORT.md"),
    )
    # Track user overrides
    for key in norm_data:
        user_overrides.add(f"prd_normalization.{key}")
```

Add validation in `_dict_to_config()`:
```python
if config.prd_normalization.mode not in ("auto", "always", "never"):
    raise ValueError(f"prd_normalization.mode must be auto|always|never, got {config.prd_normalization.mode!r}")
if config.prd_normalization.inference_level not in ("strict", "moderate", "aggressive"):
    raise ValueError(f"prd_normalization.inference_level must be strict|moderate|aggressive, got {config.prd_normalization.inference_level!r}")
if config.prd_normalization.gap_handling not in ("flag", "warn", "block"):
    raise ValueError(f"prd_normalization.gap_handling must be flag|warn|block, got {config.prd_normalization.gap_handling!r}")
if config.prd_normalization.max_pipeline_budget_usd < 0.1:
    raise ValueError(f"prd_normalization.max_pipeline_budget_usd must be >= 0.1, got {config.prd_normalization.max_pipeline_budget_usd}")
```

Depth-gating rules:
```python
# In the depth-gating section of _dict_to_config():
if depth == "quick":
    if "prd_normalization.enabled" not in user_overrides:
        config.prd_normalization.enabled = False
# standard, thorough, exhaustive: all enabled by default
```

### 3.2 New Module: `src/agent_team/prd_normalizer.py`

#### 3.2.1 Imports and Constants

```python
"""PRD Normalization Phase (-1) — transforms rough PRDs into agent-team target format."""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import AgentTeamConfig, PRDNormalizationConfig

logger = logging.getLogger(__name__)
```

#### 3.2.2 Dataclasses

```python
@dataclass
class NormalizationAnalysis:
    """Result of analyzing whether a PRD needs normalization."""
    needs_normalization: bool
    confidence: float  # 0.0 to 1.0
    missing_sections: list[str]
    malformed_sections: list[str]
    detected_tech_stack: dict[str, str]  # e.g., {"backend": "aspnet", "frontend": "angular"}
    detected_entities: list[str]
    detected_endpoints: int
    detected_enums: list[str]
    raw_section_map: dict[str, tuple[int, int]]  # section_name -> (start_line, end_line)

@dataclass
class NormalizationGap:
    """A gap in the normalized PRD that couldn't be filled from the source."""
    section: str
    description: str
    severity: str  # "critical" | "warning" | "info"
    original_reference: str  # where in original PRD this relates to (or "not found")

@dataclass
class TraceabilityEntry:
    """Maps a normalized section back to the source PRD."""
    normalized_section: str
    source_sections: list[str]
    source_lines: list[tuple[int, int]]  # (start, end) ranges in original
    transformation: str  # "format-only" | "restructured" | "inferred" | "gap"

@dataclass
class NormalizationReport:
    """Complete report of the normalization pipeline run."""
    original_size_bytes: int
    normalized_size_bytes: int
    gaps: list[NormalizationGap]
    traceability: list[TraceabilityEntry]
    structural_violations: list[dict[str, Any]]  # from structural validator
    faithfulness_score: float  # 0.0 to 1.0
    sections_normalized: int
    sections_gap: int
    output_file: Path
    report_file: Path
```

#### 3.2.3 Detection Function

```python
# Required sections in target format
_REQUIRED_SECTIONS = [
    "Executive Overview",
    "Technology Stack",
    "User Roles and Permissions",
    "Entity Definitions",
    "Enum and Status Registries",
    "Milestone Breakdown",
    "Seed Data Requirements",
    "UI Requirements",
    "Business Rules",
    "Cross-Cutting Concerns",
    "Docker Compose Specification",
    "Constraints",
]

# Regex patterns for detecting target-format compliance
_RE_NUMBERED_SECTION = re.compile(
    r"^##\s+\d+\.\s+(.+)", re.MULTILINE
)
_RE_SVC_TABLE_ROW = re.compile(
    r"^\|\s*SVC-\d+\s*\|", re.MULTILINE
)
_RE_ENTITY_TABLE = re.compile(
    r"^\|\s*Field\s*\|\s*Type\s*\|\s*Nullable\s*\|\s*Default\s*\|\s*Constraints\s*\|\s*Notes\s*\|",
    re.MULTILINE,
)
_RE_ENUM_VALUES_LINE = re.compile(
    r"\*\*Values:\*\*\s*`[A-Z]", re.MULTILINE
)
_RE_ENUM_CSHARP_BLOCK = re.compile(
    r"```csharp\s*\n\s*public\s+enum\s+\w+", re.MULTILINE
)
_RE_ENUM_TYPESCRIPT_BLOCK = re.compile(
    r"```typescript\s*\n\s*export\s+type\s+\w+", re.MULTILINE
)
_RE_MILESTONE_HEADER = re.compile(
    r"^###?\s+Milestone\s+\d+[.:]\s*", re.MULTILINE
)
_RE_SEED_USER_TABLE = re.compile(
    r"^\|\s*(?:Admin|Role)\s*\|.*(?:Email|email)\s*\|.*(?:Password|password)\s*\|",
    re.MULTILINE,
)
_RE_DOCKER_COMPOSE = re.compile(
    r"```ya?ml\s*\n(?:.*\n)*?services:", re.MULTILINE
)
_RE_CONSTRAINT_LIST = re.compile(
    r"^\d+\.\s+\*\*[A-Z\s]+\*\*:", re.MULTILINE
)
_RE_DTO_BRACE_NOTATION = re.compile(
    r"\{\s*\w+:\s*\w+", re.MULTILINE
)

# Tech stack detection patterns
_TECH_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "backend": [
        (re.compile(r"ASP\.NET|\.NET\s+\d|C#|Entity\s+Framework", re.I), "aspnet"),
        (re.compile(r"Express|Node\.?js|NestJS|Fastify", re.I), "express"),
        (re.compile(r"Django|Flask|FastAPI|Python", re.I), "python"),
        (re.compile(r"Spring\s+Boot|Java|Kotlin", re.I), "spring"),
        (re.compile(r"Laravel|PHP|Symfony", re.I), "laravel"),
        (re.compile(r"Ruby\s+on\s+Rails|Rails|Ruby", re.I), "rails"),
        (re.compile(r"Go\s+|Golang|Gin|Echo|Fiber", re.I), "go"),
    ],
    "frontend": [
        (re.compile(r"Angular\s+\d|Angular\b(?!\s+JS)", re.I), "angular"),
        (re.compile(r"React\b|Next\.?js", re.I), "react"),
        (re.compile(r"Vue\b|Nuxt", re.I), "vue"),
        (re.compile(r"Svelte|SvelteKit", re.I), "svelte"),
        (re.compile(r"Blazor|Razor", re.I), "blazor"),
    ],
    "database": [
        (re.compile(r"PostgreSQL|Postgres|Npgsql", re.I), "postgresql"),
        (re.compile(r"MySQL|MariaDB", re.I), "mysql"),
        (re.compile(r"SQL\s+Server|MSSQL|SqlServer", re.I), "sqlserver"),
        (re.compile(r"MongoDB|Mongo\b", re.I), "mongodb"),
        (re.compile(r"SQLite", re.I), "sqlite"),
    ],
    "orm": [
        (re.compile(r"Entity\s+Framework|EF\s+Core|DbContext", re.I), "efcore"),
        (re.compile(r"Dapper", re.I), "dapper"),
        (re.compile(r"Prisma", re.I), "prisma"),
        (re.compile(r"TypeORM", re.I), "typeorm"),
        (re.compile(r"Sequelize", re.I), "sequelize"),
        (re.compile(r"Django\s+ORM|models\.Model", re.I), "django"),
        (re.compile(r"SQLAlchemy|declarative_base", re.I), "sqlalchemy"),
    ],
}


def needs_normalization(content: str) -> NormalizationAnalysis:
    """Analyze whether a PRD needs normalization to match target format.

    Checks for:
    1. Numbered section headings (## 1. Title format)
    2. SVC table presence with { field: type } DTOs
    3. Entity tables with 6-column format
    4. Enum registries with C#/TS blocks
    5. Milestone headers with SVC ranges
    6. Seed data tables with credentials
    7. Docker Compose YAML block
    8. Numbered constraints list

    Returns:
        NormalizationAnalysis with needs_normalization=True if format
        diverges significantly from target.
    """
    missing: list[str] = []
    malformed: list[str] = []

    # Check numbered sections
    found_sections = _RE_NUMBERED_SECTION.findall(content)
    found_section_names = [s.strip().rstrip(":") for s in found_sections]
    for req in _REQUIRED_SECTIONS:
        if not any(req.lower() in fs.lower() for fs in found_section_names):
            missing.append(req)

    # Check SVC tables
    svc_count = len(_RE_SVC_TABLE_ROW.findall(content))
    if svc_count == 0:
        malformed.append("SVC tables (no SVC-xxx rows found)")

    # Check DTO brace notation
    dto_count = len(_RE_DTO_BRACE_NOTATION.findall(content))
    if svc_count > 0 and dto_count == 0:
        malformed.append("DTO notation (SVC rows exist but no { field: type } DTOs)")

    # Check entity tables
    entity_tables = len(_RE_ENTITY_TABLE.findall(content))
    if entity_tables == 0:
        malformed.append("Entity tables (no 6-column Field|Type|Nullable|Default|Constraints|Notes tables)")

    # Check enum format
    enum_values = len(_RE_ENUM_VALUES_LINE.findall(content))
    enum_csharp = len(_RE_ENUM_CSHARP_BLOCK.findall(content))
    enum_ts = len(_RE_ENUM_TYPESCRIPT_BLOCK.findall(content))
    if enum_values == 0:
        malformed.append("Enum registries (no **Values:** lines with PascalCase)")
    if enum_csharp == 0 and enum_ts == 0:
        malformed.append("Enum code blocks (no C# or TypeScript enum definitions)")

    # Check milestones
    milestone_count = len(_RE_MILESTONE_HEADER.findall(content))
    if milestone_count == 0:
        malformed.append("Milestone headers (no 'Milestone N:' headings)")

    # Check seed data
    if not _RE_SEED_USER_TABLE.search(content):
        malformed.append("Seed user table (no Role|Email|Password table)")

    # Check Docker
    if not _RE_DOCKER_COMPOSE.search(content):
        malformed.append("Docker Compose (no YAML block with services:)")

    # Check constraints
    constraint_count = len(_RE_CONSTRAINT_LIST.findall(content))
    if constraint_count == 0:
        malformed.append("Constraints (no numbered **KEYWORD**: constraint list)")

    # Detect tech stack
    detected_tech: dict[str, str] = {}
    for category, patterns in _TECH_PATTERNS.items():
        for pattern, name in patterns:
            if pattern.search(content):
                detected_tech[category] = name
                break

    # Detect entities (look for ### headings or table-of-contents patterns)
    _re_entity_heading = re.compile(r"^###\s+\d+\.\d+\s+(\w+)\s*$", re.MULTILINE)
    detected_entities = _re_entity_heading.findall(content)
    if not detected_entities:
        # Fallback: look for entity-like words near "entity", "model", "table"
        _re_entity_mention = re.compile(
            r"(?:entity|model|table|schema)[:\s]+(\w+)", re.I
        )
        detected_entities = list(set(_re_entity_mention.findall(content)))

    # Detect enums
    _re_enum_name = re.compile(r"(?:enum|status|type)\s+(\w+)\s*[{:]", re.I)
    detected_enums = list(set(_re_enum_name.findall(content)))

    # Build section map (approximate line ranges)
    raw_section_map: dict[str, tuple[int, int]] = {}
    lines = content.split("\n")
    current_section = ""
    current_start = 0
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            if current_section:
                raw_section_map[current_section] = (current_start, i - 1)
            current_section = line.lstrip("# ").strip()
            current_start = i
    if current_section:
        raw_section_map[current_section] = (current_start, len(lines))

    # Calculate confidence
    total_checks = 12  # sections + structural elements
    issues = len(missing) + len(malformed)
    confidence = max(0.0, 1.0 - (issues / total_checks))

    needs_norm = issues >= 3 or len(missing) >= 2

    return NormalizationAnalysis(
        needs_normalization=needs_norm,
        confidence=confidence,
        missing_sections=missing,
        malformed_sections=malformed,
        detected_tech_stack=detected_tech,
        detected_entities=detected_entities,
        detected_endpoints=svc_count,
        detected_enums=detected_enums,
        raw_section_map=raw_section_map,
    )
```

#### 3.2.4 Prompt Constants

Define these 6 prompt constants in `prd_normalizer.py`. Each drives one agent in the pipeline.

```python
ANALYZER_PROMPT = """You are a PRD Structure Analyzer. Your job is to read a raw PRD and produce a JSON analysis.

INPUT: A raw PRD document (any format — narrative, bullet points, tables, mixed).

OUTPUT: A JSON object with this exact schema:

```json
{
  "product_name": "string",
  "tech_stack": {
    "backend": {"framework": "string", "language": "string", "version": "string"},
    "frontend": {"framework": "string", "language": "string", "version": "string"},
    "database": {"type": "string", "version": "string"},
    "orm": ["string"],
    "additional": [{"name": "string", "version": "string", "purpose": "string"}]
  },
  "entities": [
    {
      "name": "string",
      "fields": [{"name": "string", "type": "string", "nullable": false, "constraints": "string"}],
      "relationships": [{"target": "string", "type": "one-to-many|many-to-one|many-to-many", "fk_field": "string"}]
    }
  ],
  "enums": [
    {"name": "string", "values": ["string"], "used_by_entity": "string", "has_transitions": false}
  ],
  "endpoints": [
    {"method": "string", "path": "string", "description": "string", "request_fields": ["string"], "response_fields": ["string"]}
  ],
  "roles": [{"name": "string", "code": "string", "description": "string"}],
  "seed_data_mentioned": true,
  "docker_mentioned": true,
  "sections_found": {"section_name": {"start_line": 0, "end_line": 0, "has_content": true}}
}
```

RULES:
1. Extract ONLY what exists in the PRD. Do NOT invent entities, fields, or endpoints.
2. If a section is ambiguous, extract what you can and note uncertainty in a "notes" field.
3. For endpoints: if the PRD lists them as bullet points or narrative, still extract method + path.
4. For entities: if described narratively, extract field names and best-guess types.
5. For enums: extract ALL value lists, status types, category types mentioned anywhere.
6. Write the JSON to ANALYSIS.json using the Write tool.
"""

ENTITY_NORMALIZER_PROMPT = """You are an Entity & Enum Normalizer. You take a JSON analysis of a PRD and produce normalized entity tables and enum registries.

INPUT: ANALYSIS.json from the Analyzer step.

OUTPUT: Write ENTITIES_NORMALIZED.md with:

For EACH entity:
```
### N.M EntityName

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| Id | Guid | No | `Guid.NewGuid()` | PK | Auto-generated |
| ... | ... | ... | ... | ... | ... |
| CreatedAt | DateTime | No | `DateTime.UtcNow` | — | Audit timestamp |
| UpdatedAt | DateTime | Yes | `null` | — | Set on modification |

**Navigation Properties:**
- `CreatedByUser` → User (via CreatedById FK)
- `Items` → Collection<ChildEntity>

**Indexes:**
- `IX_EntityName_FieldName` on (FieldName) — for frequent lookups
```

For EACH enum, write to ENUMS_NORMALIZED.md:
```
### N.M EnumName

**Values:** `Value1` | `Value2` | `Value3`

**Database type:** `VARCHAR(N) NOT NULL`

**{Language} enum:**
```{language}
// exact enum definition in backend language
```

**TypeScript:**
```typescript
export type EnumName = 'Value1' | 'Value2' | 'Value3';
```

[If has_transitions=true, add State Transitions table:]
| From | To | Allowed | Trigger | Who Can Trigger |
|------|----|---------|---------|-----------------|
```

RULES:
1. {inference_level_rules}  ← (injected based on config.inference_level)
2. Field types MUST match the detected backend language:
   - C#/.NET: Guid, string, bool, int, double, DateTime, enum names
   - TypeScript/Node: string, number, boolean, Date, enum names
   - Python: uuid.UUID, str, bool, int, float, datetime, enum names
3. Enum values MUST be PascalCase (e.g., InReview, not in_review or IN_REVIEW)
4. Every entity MUST have: Id (PK), CreatedAt, UpdatedAt at minimum (STANDARD-FIELDS-EXCEPTION)
5. Navigation properties MUST be bidirectional for every FK relationship
6. DO NOT invent fields not mentioned or reasonably implied by the source PRD
"""

API_NORMALIZER_PROMPT = """You are an API Endpoint & Milestone Normalizer. You take the analysis JSON and produce SVC tables grouped by milestones.

INPUT: ANALYSIS.json + ENTITIES_NORMALIZED.md

OUTPUT: Write API_NORMALIZED.md with:

For EACH milestone:
```
### Milestone N: Title — Subtitle

**Entities:** Entity1, Entity2
**Enums:** Enum1, Enum2

**Deliverables:** [Paragraph describing what this milestone implements]

**SVC Endpoints: SVC-XXX through SVC-YYY**

| SVC | Frontend Service.Method | Backend Endpoint | HTTP Method | Request DTO | Response DTO |
|-----|------------------------|------------------|-------------|-------------|--------------|
| SVC-001 | AuthService.login() | POST /api/auth/login | POST | `{ email: string, password: string }` | `{ token: string, user: { id: string, role: string } }` |
```

RULES:
1. SVC numbering is sequential across ALL milestones (SVC-001, SVC-002, ..., SVC-N)
2. Each milestone's SVC table MUST contain ONLY the endpoints that milestone delivers
3. DTO notation MUST use braces: `{{ field: type, field: type }}`
4. DTO field casing: {casing_rule}  ← (injected based on detected tech stack)
5. Milestone distribution:
   - M1: Auth + core entities (User, Org, Settings) — typically 12-20 endpoints
   - M2: Primary domain entities — typically 15-25 endpoints
   - M3: Secondary domain + workflows — typically 10-20 endpoints
   - M4: Advanced features (search, reports, exports) — typically 8-15 endpoints
   - M5: Polish (templates, admin, analytics) — typically 5-12 endpoints
6. Every endpoint in the original PRD MUST appear in exactly one milestone's SVC table
7. Frontend service names follow: {service_naming_rule}  ← (injected based on frontend framework)
8. DO NOT invent endpoints not described or implied by the source PRD
9. For endpoints without explicit request/response schemas, infer minimal DTOs from entity fields
"""

METADATA_NORMALIZER_PROMPT = """You are a Metadata Normalizer. You produce seed data, Docker config, UI requirements, business rules, cross-cutting concerns, and constraints.

INPUT: ANALYSIS.json + ENTITIES_NORMALIZED.md + the original raw PRD

OUTPUT: Write METADATA_NORMALIZED.md with these sections:

## Seed Data Requirements
- Seed Users table: | Role | Email | Password | Full Name | Phone | IsActive |
  - One user per role defined in the PRD
  - Emails: {role}@{product_slug}.com
  - Passwords: {Role}123! (matching browser_testing.py extraction patterns)
  - All IsActive = true
- Seed records for each primary entity (1-3 records each)

## UI Requirements
- Design direction based on the product domain
- Component library from tech stack (PrimeNG for Angular, MUI for React, Vuetify for Vue, etc.)
- Page-by-page layout descriptions covering every route implied by the PRD

## Business Rules
- Extract ALL validation rules, authorization rules, workflow rules from the original PRD
- Group by domain area
- DO NOT invent rules not present in the source PRD

## Cross-Cutting Concerns
- HTTP error codes and formats
- JWT configuration (if auth mentioned)
- CORS policy (if web app)
- File upload limits (if file handling mentioned)
- Logging and monitoring requirements

## Docker Compose Specification
- Generate docker-compose.yml with services matching the tech stack:
  - Backend service on appropriate port
  - Frontend service on port 80 (dev port varies)
  - Database service on standard port
  - All env vars referenced via ${{VAR}} syntax
- Environment variables table: | Variable | Required | Default | Description |
- Example .env file with concrete values

## Constraints
- Generate numbered constraints covering EVERY applicable scan family:
  {constraint_families}  ← (injected based on detected tech stack)
- Each constraint: numbered, bold keyword, colon, narrative description
- Only include constraints relevant to the detected tech stack

RULES:
1. Seed user passwords MUST match the pattern: {Role}123! (Capital first letter + "123!")
2. Seed user emails MUST match: {lowercased_role}@{product_slug}.com
3. Docker service names MUST be: backend, frontend, db (lowercase, no hyphens in db)
4. DO NOT invent business rules. Extract only from the source PRD.
5. Constraints MUST map to actual scan families in quality_checks.py
"""

ASSEMBLER_INSTRUCTIONS = """Combine the following normalized sections into a single PRD document with exactly 12 numbered sections:

## 1. Executive Overview — from source PRD (preserve original text, light reformatting only)
## 2. Technology Stack — from ANALYSIS.json tech_stack
## 3. User Roles and Permissions — from ANALYSIS.json roles + source PRD permissions
## 4. Entity Definitions — from ENTITIES_NORMALIZED.md
## 5. Enum and Status Registries — from ENUMS_NORMALIZED.md
## 6. Milestone Breakdown — from API_NORMALIZED.md
## 7. Seed Data Requirements — from METADATA_NORMALIZED.md
## 8. UI Requirements — from METADATA_NORMALIZED.md
## 9. Business Rules — from METADATA_NORMALIZED.md
## 10. Cross-Cutting Concerns — from METADATA_NORMALIZED.md
## 11. Docker Compose Specification — from METADATA_NORMALIZED.md
## 12. Constraints — from METADATA_NORMALIZED.md

Use `---` horizontal rules between sections.
Preserve ALL content from the intermediate files.
Add section numbering to all ## headings.
"""

FAITHFULNESS_VALIDATOR_PROMPT = """You are a Faithfulness Validator. Compare the NORMALIZED PRD against the ORIGINAL PRD.

INPUT:
1. The original raw PRD (ORIGINAL_PRD.md)
2. The normalized PRD (PRD_NORMALIZED.md)

OUTPUT: Write FAITHFULNESS_REPORT.md with:

## Faithfulness Score: X.XX / 1.00

## Traceability Map
| Normalized Section | Source Section(s) | Lines in Original | Transformation |
|--------------------|-------------------|-------------------|----------------|
| 1. Executive Overview | Introduction (1-15) | 1-15 | format-only |
| 4. Entity Definitions | Data Model (30-80) | 30-80 | restructured |
| ... | ... | ... | ... |

## Invented Content (VIOLATIONS)
List ANY content in the normalized PRD that does NOT exist in the original:
- [List specific items with line numbers]

## Gap Report
List sections that couldn't be fully populated:
- [Section name] — [What's missing] — Severity: [critical|warning|info]

## Field Name Accuracy
Check that entity names, field names, endpoint paths in normalized PRD match original:
- [List any renaming or casing changes]

RULES:
1. Score 1.0 = perfect faithful translation (no invented content, all gaps flagged)
2. Deduct 0.1 for each invented entity/endpoint/business rule
3. Deduct 0.05 for each invented field or constraint
4. Standard infrastructure fields (Id, CreatedAt, UpdatedAt) do NOT count as invented
5. Casing normalization (snake_case → camelCase) does NOT count as invention
6. Be STRICT — if something appears in normalized but not in original, flag it
"""
```

#### 3.2.5 Structural Validator (Pure Python, No LLM)

```python
def validate_structure(content: str) -> list[dict[str, Any]]:
    """Validate normalized PRD matches target structural format.

    Uses the same regex patterns that downstream parsers use,
    ensuring the output will be correctly parsed by quality_checks.py,
    milestone_manager.py, browser_testing.py, etc.

    Returns:
        List of violation dicts with keys: check, message, severity
    """
    violations: list[dict[str, Any]] = []

    # STRUCT-001: All 12 numbered sections present
    found = _RE_NUMBERED_SECTION.findall(content)
    found_lower = [s.strip().lower() for s in found]
    for req in _REQUIRED_SECTIONS:
        if not any(req.lower() in f for f in found_lower):
            violations.append({
                "check": "STRUCT-001",
                "message": f"Missing required section: {req}",
                "severity": "error",
            })

    # STRUCT-002: SVC tables have brace-notation DTOs
    svc_rows = _RE_SVC_TABLE_ROW.findall(content)
    if not svc_rows:
        violations.append({
            "check": "STRUCT-002",
            "message": "No SVC-xxx table rows found",
            "severity": "error",
        })
    else:
        # Check that DTOs use { field: type } notation
        # (critical for _parse_field_schema() to return non-empty dict)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if _RE_SVC_TABLE_ROW.match(line):
                if "{" not in line:
                    violations.append({
                        "check": "STRUCT-002",
                        "message": f"SVC row at line {i+1} missing brace DTO notation",
                        "severity": "warning",
                    })

    # STRUCT-003: Entity tables have 6 columns
    if not _RE_ENTITY_TABLE.search(content):
        violations.append({
            "check": "STRUCT-003",
            "message": "No 6-column entity tables (Field|Type|Nullable|Default|Constraints|Notes)",
            "severity": "error",
        })

    # STRUCT-004: Enums have Values + code blocks
    if not _RE_ENUM_VALUES_LINE.search(content):
        violations.append({
            "check": "STRUCT-004",
            "message": "No enum **Values:** lines found",
            "severity": "error",
        })

    # STRUCT-005: Milestones with SVC ranges
    milestones = _RE_MILESTONE_HEADER.findall(content)
    if not milestones:
        violations.append({
            "check": "STRUCT-005",
            "message": "No Milestone N: headers found",
            "severity": "error",
        })
    # Check SVC range lines
    _re_svc_range = re.compile(
        r"\*\*SVC\s+Endpoints:\s*SVC-\d+\s+through\s+SVC-\d+\*\*", re.I
    )
    if milestones and not _re_svc_range.search(content):
        violations.append({
            "check": "STRUCT-005",
            "message": "Milestones exist but no 'SVC Endpoints: SVC-XXX through SVC-YYY' range lines",
            "severity": "warning",
        })

    # STRUCT-006: Seed data with credential table
    if not _RE_SEED_USER_TABLE.search(content):
        violations.append({
            "check": "STRUCT-006",
            "message": "No seed user table with Role|Email|Password columns",
            "severity": "warning",
        })

    # STRUCT-007: Docker Compose YAML block
    if not _RE_DOCKER_COMPOSE.search(content):
        violations.append({
            "check": "STRUCT-007",
            "message": "No Docker Compose YAML block with services:",
            "severity": "warning",
        })

    # STRUCT-008: Numbered constraints
    constraints = _RE_CONSTRAINT_LIST.findall(content)
    if not constraints:
        violations.append({
            "check": "STRUCT-008",
            "message": "No numbered constraints (N. **KEYWORD**: description)",
            "severity": "warning",
        })

    # STRUCT-009: Enum PascalCase check
    _re_enum_value = re.compile(r"\*\*Values:\*\*\s*(.+)")
    for match in _re_enum_value.finditer(content):
        values_text = match.group(1)
        # Extract values between backticks
        values = re.findall(r"`(\w+)`", values_text)
        for v in values:
            if v != v[0].upper() + v[1:]:  # Not PascalCase
                violations.append({
                    "check": "STRUCT-009",
                    "message": f"Enum value '{v}' is not PascalCase",
                    "severity": "warning",
                })

    # STRUCT-010: Sequential SVC numbering
    svc_numbers = [
        int(m.group(1))
        for m in re.finditer(r"\|\s*SVC-(\d+)\s*\|", content)
    ]
    if svc_numbers:
        expected = list(range(1, max(svc_numbers) + 1))
        missing_svcs = set(expected) - set(svc_numbers)
        if missing_svcs:
            violations.append({
                "check": "STRUCT-010",
                "message": f"Non-sequential SVC numbering. Missing: {sorted(missing_svcs)[:10]}",
                "severity": "warning",
            })

    return violations
```

#### 3.2.6 Tech-Stack-Aware Helpers

```python
def _get_casing_rule(tech_stack: dict[str, str]) -> str:
    """Return DTO field casing rule based on backend framework."""
    backend = tech_stack.get("backend", "")
    rules = {
        "aspnet": "camelCase (System.Text.Json default for C# property serialization)",
        "express": "camelCase (JavaScript native object key convention)",
        "python": "snake_case (Python/Django REST framework convention)",
        "spring": "camelCase (Jackson default for Java property serialization)",
        "laravel": "snake_case (PHP/Laravel convention)",
        "rails": "snake_case (Ruby convention)",
        "go": "camelCase (encoding/json convention with struct tags)",
    }
    return rules.get(backend, "camelCase (default)")


def _get_service_naming_rule(tech_stack: dict[str, str]) -> str:
    """Return frontend service naming convention."""
    frontend = tech_stack.get("frontend", "")
    rules = {
        "angular": "Angular services: {Entity}Service with .{action}() methods (e.g., ProjectService.getAll())",
        "react": "React hooks/services: use{Entity} hooks or {entity}Api.{action}() (e.g., useProjects() or projectApi.getAll())",
        "vue": "Vue composables: use{Entity} with .{action}() methods (e.g., useProjects().getAll())",
        "svelte": "Svelte stores: {entity}Store.{action}() (e.g., projectStore.getAll())",
        "blazor": "Blazor services: {Entity}Service.{Action}Async() (e.g., ProjectService.GetAllAsync())",
    }
    return rules.get(frontend, "EntityService.action() pattern")


def _get_constraint_families(tech_stack: dict[str, str]) -> str:
    """Return applicable constraint families based on tech stack."""
    families: list[str] = []

    # Always applicable
    families.append("- MOCK DATA PROHIBITION (MOCK-001..007): No hardcoded/fake data in service files")
    families.append("- DTO-ONLY PAYLOADS: Never return ORM entities directly in API responses")
    families.append("- PAGINATION MANDATORY: page + pageSize params, default 20, max 100, totalCount in response")

    backend = tech_stack.get("backend", "")
    orm = tech_stack.get("orm", "")

    if backend == "aspnet":
        families.append("- JSONSTRINGENUMCONVERTER: Must register in Program.cs for PascalCase enum serialization")
        families.append("- BOOLEAN DEFAULTS EXPLICIT: `public bool X { get; set; } = true;` (no bare declarations)")
        families.append("- FK BIDIRECTIONAL NAVIGATION: Both reference and collection nav properties + OnModelCreating")
        families.append("- NULL GUARD MANDATORY: ?., ??, ??=, or if(x!=null) checks on nullable access")
    if "efcore" in str(tech_stack.get("orm", "")):
        families.append("- ENUM/STATUS CASING: PascalCase across C#, database, JSON, and TypeScript")
    if "dapper" in str(tech_stack.get("orm", "")):
        families.append("- DAPPER PARAMETERIZED SQL: No string interpolation in queries")
    if "mediatr" in str(tech_stack.get("additional", "")):
        families.append("- MEDIATR SAVECHANGESASYNC: CommandHandlers MUST call SaveChangesAsync()")

    families.append("- DOCKER THREE SERVICES: backend + frontend + db with correct ports and env vars")
    families.append("- SEED USERS ALL ROLES: One user per role with explicit credentials")
    families.append("- SERVER AUTHORITY: Frontend displays server-provided counts, no local computation")
    families.append("- ACTIVITY LOG ON STATUS: All status changes create audit log entries")

    if tech_stack.get("frontend") == "angular":
        families.append("- ANGULAR HTTP INTERCEPTOR: JWT token attached to all API calls except auth endpoints")
    elif tech_stack.get("frontend") == "react":
        families.append("- AXIOS INTERCEPTOR / FETCH WRAPPER: JWT token attached to all API calls except auth endpoints")

    return "\n".join(families)


def _get_inference_level_rules(level: str) -> str:
    """Return inference rules based on config level."""
    if level == "strict":
        return """STRICT MODE:
- ONLY format-translate fields that exist in the source PRD
- DO NOT add Id, CreatedAt, UpdatedAt, or any inferred fields
- Flag EVERY missing field as a GAP
- If an entity has no explicit fields, create an EMPTY table with a GAP comment"""
    elif level == "moderate":
        return """MODERATE MODE:
- Add standard infrastructure fields if entity is defined but they're missing:
  Id (PK), CreatedAt (DateTime), UpdatedAt (DateTime nullable), CreatedById (FK to User if auth exists)
- Mark all inferred fields with `[inferred]` in Notes column
- Infer nullable from context (FK fields = No, description/notes fields = Yes)
- Infer defaults for booleans (IsActive=true, IsDeleted=false, IsDefault=false)
- DO NOT invent domain-specific fields (e.g., don't add Price to a User entity)"""
    else:  # aggressive
        return """AGGRESSIVE MODE:
- All MODERATE rules apply
- Additionally: generate SVC table rows from endpoint descriptions
  (e.g., "users can create projects" → SVC: POST /api/projects)
- Infer request/response DTOs from entity fields
- Generate missing milestone structures based on entity dependency graph
- Mark ALL generated content with [inferred] annotations"""
```

#### 3.2.7 Pipeline Orchestrator

```python
async def run_normalization_pipeline(
    raw_content: str,
    config: AgentTeamConfig,
    cwd: str,
) -> NormalizationReport:
    """Execute the 7-step PRD normalization pipeline.

    Steps:
    1. Analyzer Agent — produce ANALYSIS.json
    2. Entity Normalizer Agent — produce ENTITIES_NORMALIZED.md + ENUMS_NORMALIZED.md
    3a. API Normalizer Agent — produce API_NORMALIZED.md (parallel with 3b)
    3b. Metadata Normalizer Agent — produce METADATA_NORMALIZED.md (parallel with 3a)
    4. Assembler — combine into PRD_NORMALIZED.md
    5. Structural Validator — regex-based format checks
    6. Faithfulness Validator Agent — compare against original
    7. Output Writer — write final files

    Args:
        raw_content: The original PRD content
        config: Agent team configuration
        cwd: Current working directory

    Returns:
        NormalizationReport with all results
    """
    from .mcp_servers import get_mcp_servers

    work_dir = Path(cwd) / ".agent-team" / "prd-normalization"
    work_dir.mkdir(parents=True, exist_ok=True)

    norm_config = config.prd_normalization
    analysis = needs_normalization(raw_content)

    # Write original for faithfulness comparison
    (work_dir / "ORIGINAL_PRD.md").write_text(raw_content, encoding="utf-8")

    total_cost = 0.0
    gaps: list[NormalizationGap] = []
    traceability: list[TraceabilityEntry] = []

    # --- Step 1: Analyzer ---
    logger.info("Phase -1 Step 1: Running PRD Analyzer")
    analyzer_prompt = ANALYZER_PROMPT + f"\n\nThe PRD to analyze:\n\n{raw_content}"
    # Execute as sub-orchestrator (same pattern as _run_prd_reconciliation)
    cost = await _run_sub_agent(
        prompt=analyzer_prompt,
        work_dir=str(work_dir),
        config=config,
        phase_name="prd_normalize_analyze",
    )
    total_cost += cost

    # Validate ANALYSIS.json was created
    analysis_path = work_dir / "ANALYSIS.json"
    if not analysis_path.is_file():
        raise FileNotFoundError("Analyzer agent did not produce ANALYSIS.json")
    analysis_data = json.loads(analysis_path.read_text(encoding="utf-8"))

    # --- Step 2: Entity Normalizer ---
    logger.info("Phase -1 Step 2: Running Entity Normalizer")
    inference_rules = _get_inference_level_rules(norm_config.inference_level)
    entity_prompt = ENTITY_NORMALIZER_PROMPT.replace(
        "{inference_level_rules}", inference_rules
    )
    cost = await _run_sub_agent(
        prompt=entity_prompt,
        work_dir=str(work_dir),
        config=config,
        phase_name="prd_normalize_entities",
    )
    total_cost += cost

    # --- Step 3a + 3b: Parallel API + Metadata Normalization ---
    logger.info("Phase -1 Step 3: Running API + Metadata Normalizers (parallel)")

    casing_rule = _get_casing_rule(analysis.detected_tech_stack)
    service_rule = _get_service_naming_rule(analysis.detected_tech_stack)
    constraint_families = _get_constraint_families(analysis.detected_tech_stack)

    api_prompt = API_NORMALIZER_PROMPT.replace(
        "{casing_rule}", casing_rule
    ).replace(
        "{service_naming_rule}", service_rule
    )

    metadata_prompt = METADATA_NORMALIZER_PROMPT.replace(
        "{constraint_families}", constraint_families
    )

    import asyncio
    api_task = _run_sub_agent(
        prompt=api_prompt,
        work_dir=str(work_dir),
        config=config,
        phase_name="prd_normalize_api",
    )
    metadata_task = _run_sub_agent(
        prompt=metadata_prompt,
        work_dir=str(work_dir),
        config=config,
        phase_name="prd_normalize_metadata",
    )
    costs = await asyncio.gather(api_task, metadata_task)
    total_cost += sum(costs)

    # Budget guard
    if total_cost > norm_config.max_pipeline_budget_usd:
        logger.warning(
            "Phase -1 budget exceeded: $%.2f > $%.2f limit",
            total_cost, norm_config.max_pipeline_budget_usd,
        )

    # --- Step 4: Assembler (local file I/O) ---
    logger.info("Phase -1 Step 4: Assembling normalized PRD")
    normalized_content = _assemble_normalized_prd(work_dir, raw_content)

    # --- Step 5: Structural Validator (local regex) ---
    logger.info("Phase -1 Step 5: Validating structure")
    struct_violations = validate_structure(normalized_content)
    if struct_violations:
        logger.warning(
            "Phase -1: %d structural violations found", len(struct_violations)
        )

    # --- Step 6: Faithfulness Validator ---
    logger.info("Phase -1 Step 6: Running Faithfulness Validator")
    # Write normalized content for the validator to read
    normalized_path = Path(cwd) / norm_config.output_file
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text(normalized_content, encoding="utf-8")

    faithfulness_prompt = FAITHFULNESS_VALIDATOR_PROMPT
    cost = await _run_sub_agent(
        prompt=faithfulness_prompt,
        work_dir=str(work_dir),
        config=config,
        phase_name="prd_normalize_faithfulness",
    )
    total_cost += cost

    # Parse faithfulness score from report
    faith_report_path = work_dir / "FAITHFULNESS_REPORT.md"
    faithfulness_score = _parse_faithfulness_score(faith_report_path)

    # --- Step 7: Output Writer ---
    logger.info("Phase -1 Step 7: Writing final output")
    output_file = Path(cwd) / norm_config.output_file
    report_file = Path(cwd) / norm_config.report_file

    output_file.write_text(normalized_content, encoding="utf-8")

    report = NormalizationReport(
        original_size_bytes=len(raw_content.encode("utf-8")),
        normalized_size_bytes=len(normalized_content.encode("utf-8")),
        gaps=gaps,
        traceability=traceability,
        structural_violations=struct_violations,
        faithfulness_score=faithfulness_score,
        sections_normalized=12 - len([
            v for v in struct_violations if v["check"] == "STRUCT-001"
        ]),
        sections_gap=len([
            v for v in struct_violations if v["check"] == "STRUCT-001"
        ]),
        output_file=output_file,
        report_file=report_file,
    )

    _write_normalization_report(report, report_file)

    return report


def _assemble_normalized_prd(
    work_dir: Path, original_content: str
) -> str:
    """Assemble normalized PRD from intermediate files."""
    sections: list[str] = []

    # Section 1: Executive Overview — extract from original
    sections.append(_extract_executive_overview(original_content))

    # Section 2: Technology Stack — from ANALYSIS.json
    analysis_path = work_dir / "ANALYSIS.json"
    if analysis_path.is_file():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        sections.append(_build_tech_stack_section(analysis))
    else:
        sections.append("## 2. Technology Stack\n\n<!-- GAP: Could not extract tech stack -->")

    # Section 3: Roles — from ANALYSIS.json
    if analysis_path.is_file():
        sections.append(_build_roles_section(analysis))
    else:
        sections.append("## 3. User Roles and Permissions\n\n<!-- GAP: No roles detected -->")

    # Section 4: Entity Definitions — from ENTITIES_NORMALIZED.md
    entities_path = work_dir / "ENTITIES_NORMALIZED.md"
    if entities_path.is_file():
        sections.append(
            "## 4. Entity Definitions\n\n"
            + entities_path.read_text(encoding="utf-8")
        )
    else:
        sections.append("## 4. Entity Definitions\n\n<!-- GAP: Entity normalization failed -->")

    # Section 5: Enums — from ENUMS_NORMALIZED.md
    enums_path = work_dir / "ENUMS_NORMALIZED.md"
    if enums_path.is_file():
        sections.append(
            "## 5. Enum and Status Registries\n\n"
            + enums_path.read_text(encoding="utf-8")
        )
    else:
        sections.append("## 5. Enum and Status Registries\n\n<!-- GAP: Enum normalization failed -->")

    # Section 6: Milestones — from API_NORMALIZED.md
    api_path = work_dir / "API_NORMALIZED.md"
    if api_path.is_file():
        sections.append(
            "## 6. Milestone Breakdown\n\n"
            + api_path.read_text(encoding="utf-8")
        )
    else:
        sections.append("## 6. Milestone Breakdown\n\n<!-- GAP: API normalization failed -->")

    # Sections 7-12: from METADATA_NORMALIZED.md
    metadata_path = work_dir / "METADATA_NORMALIZED.md"
    if metadata_path.is_file():
        metadata = metadata_path.read_text(encoding="utf-8")
        sections.append(_extract_metadata_section(metadata, "Seed Data Requirements", 7))
        sections.append(_extract_metadata_section(metadata, "UI Requirements", 8))
        sections.append(_extract_metadata_section(metadata, "Business Rules", 9))
        sections.append(_extract_metadata_section(metadata, "Cross-Cutting Concerns", 10))
        sections.append(_extract_metadata_section(metadata, "Docker Compose Specification", 11))
        sections.append(_extract_metadata_section(metadata, "Constraints", 12))
    else:
        for num, name in [
            (7, "Seed Data Requirements"), (8, "UI Requirements"),
            (9, "Business Rules"), (10, "Cross-Cutting Concerns"),
            (11, "Docker Compose Specification"), (12, "Constraints"),
        ]:
            sections.append(f"## {num}. {name}\n\n<!-- GAP: Metadata normalization failed -->")

    # Join with horizontal rules
    return "\n\n---\n\n".join(sections)


def _parse_faithfulness_score(report_path: Path) -> float:
    """Extract faithfulness score from validator report."""
    if not report_path.is_file():
        return 0.0
    content = report_path.read_text(encoding="utf-8")
    match = re.search(r"Faithfulness\s+Score:\s*(\d+\.?\d*)", content, re.I)
    if match:
        return min(1.0, float(match.group(1)))
    return 0.0


async def _run_sub_agent(
    prompt: str,
    work_dir: str,
    config: AgentTeamConfig,
    phase_name: str,
) -> float:
    """Run a sub-orchestrator agent. Returns cost.

    Uses the same pattern as _run_prd_reconciliation() in cli.py.
    """
    # Implementation follows the existing sub-orchestrator pattern:
    # 1. Build MCP servers config
    # 2. Call orchestrate() with the prompt
    # 3. Return cost
    #
    # The actual orchestrate() call depends on the agent-team's
    # orchestration API. Match the exact pattern from cli.py's
    # _run_prd_reconciliation() or _run_mock_data_fix().
    raise NotImplementedError(
        "Wire this to match your orchestration API. "
        "Copy the pattern from _run_prd_reconciliation() in cli.py."
    )
```

### 3.3 CLI Wiring (`cli.py`)

#### 3.3.1 Phase -1 Block Location

Insert AFTER config loading (~line 3530) and BEFORE Phase 0 Interview (~line 3661).

```python
# -------------------------------------------------------------------
# Phase -1: PRD Normalization (only when --prd provided)
# -------------------------------------------------------------------
_prd_normalized = False
_normalization_report: "NormalizationReport | None" = None

if args.prd and config.prd_normalization.enabled:
    from .prd_normalizer import (
        needs_normalization,
        run_normalization_pipeline,
        NormalizationReport,
    )

    try:
        prd_path = Path(args.prd)
        if not prd_path.is_file():
            print_warning(f"Phase -1: PRD file not found: {args.prd}")
        else:
            raw_prd = prd_path.read_text(encoding="utf-8")
            norm_config = config.prd_normalization

            should_normalize = False
            if norm_config.mode == "always":
                should_normalize = True
            elif norm_config.mode == "auto":
                analysis = needs_normalization(raw_prd)
                if analysis.needs_normalization:
                    print_info(
                        f"Phase -1: PRD needs normalization "
                        f"(confidence: {analysis.confidence:.0%}, "
                        f"missing: {len(analysis.missing_sections)} sections, "
                        f"malformed: {len(analysis.malformed_sections)} elements)"
                    )
                    should_normalize = True
                else:
                    print_info(
                        f"Phase -1: PRD already in target format "
                        f"(confidence: {analysis.confidence:.0%}). Skipping normalization."
                    )
            # mode == "never" → should_normalize stays False

            if should_normalize:
                print_info("Phase -1: Starting PRD Normalization Pipeline")
                _normalization_report = asyncio.run(
                    run_normalization_pipeline(
                        raw_content=raw_prd,
                        config=config,
                        cwd=cwd,
                    )
                )

                # Report results
                nr = _normalization_report
                print_info(
                    f"Phase -1 complete: "
                    f"{nr.sections_normalized}/12 sections normalized, "
                    f"{nr.sections_gap} gaps, "
                    f"{len(nr.structural_violations)} structural issues, "
                    f"faithfulness: {nr.faithfulness_score:.0%}"
                )

                if nr.structural_violations:
                    errors = [v for v in nr.structural_violations if v["severity"] == "error"]
                    warnings = [v for v in nr.structural_violations if v["severity"] == "warning"]
                    if errors:
                        print_warning(f"  {len(errors)} structural errors (may affect downstream parsing)")
                    if warnings:
                        print_info(f"  {len(warnings)} structural warnings")

                if nr.faithfulness_score < 0.8:
                    print_warning(
                        f"  Faithfulness score {nr.faithfulness_score:.0%} is below 80% — "
                        f"review {nr.report_file} for invented content"
                    )

                # Gap handling
                if norm_config.gap_handling == "block" and nr.sections_gap > 0:
                    print_error(
                        f"Phase -1: {nr.sections_gap} section gaps detected and "
                        f"gap_handling=block. Cannot proceed."
                    )
                    return  # Exit main()

                # Swap PRD path to normalized version
                if nr.output_file.is_file():
                    args.prd = str(nr.output_file)
                    _prd_normalized = True
                    print_info(f"Phase -1: Subsequent phases will use {nr.output_file}")

                _current_state.completed_phases.append("prd_normalization")
                _current_state.artifacts["prd_normalization_report"] = str(nr.report_file)
                if _prd_normalized:
                    _current_state.artifacts["prd_normalized"] = str(nr.output_file)

    except Exception as exc:
        import traceback
        logger.error("Phase -1 failed: %s\n%s", exc, traceback.format_exc())
        print_warning(f"Phase -1: Normalization failed: {exc}")
        print_info("Proceeding with original PRD (non-blocking)")
```

#### 3.3.2 Integration with PRD Chunking

IMPORTANT: After Phase -1 swaps `args.prd` to the normalized version, the existing PRD chunking code (`detect_large_prd()` / `create_prd_chunks()`) will automatically operate on the normalized content. No changes needed to the chunking code itself.

#### 3.3.3 Integration with Prompt Injection

In `build_orchestrator_prompt()` in `agents.py`, add normalization context if available:

```python
# Add after existing prd_chunks injection (~line 2454):
if normalization_report_path:
    # Let orchestrator know the PRD was normalized
    prompt += f"""

## PRD NORMALIZATION NOTE
This PRD was automatically normalized from a rough input format into the
agent-team's target structure. The normalization report is at:
{normalization_report_path}

If you encounter any GAP comments (<!-- GAP: ... -->) in the PRD, treat
those sections as undefined requirements. Do NOT invent implementations
for GAP sections — flag them for the user.
"""
```

### 3.4 Testing Specification

Create `tests/test_prd_normalizer.py` with the following test classes:

#### Class 1: TestNeedsNormalization (~15 tests)
```python
class TestNeedsNormalization:
    """Test the needs_normalization() detection function."""

    def test_perfect_prd_returns_false(self):
        """A PRD in perfect target format should not need normalization."""
        # Use the DrawSpace PRD as reference

    def test_bare_narrative_prd_returns_true(self):
        """A PRD with only narrative text needs normalization."""

    def test_missing_svc_tables_flagged(self):
        """PRD without SVC tables is flagged as malformed."""

    def test_missing_entity_tables_flagged(self):
        """PRD without 6-column entity tables is flagged."""

    def test_missing_enum_registries_flagged(self):
        """PRD without enum code blocks is flagged."""

    def test_missing_sections_detected(self):
        """Each missing required section is listed."""

    def test_tech_stack_detection_aspnet(self):
        """Detects ASP.NET backend from technology mentions."""

    def test_tech_stack_detection_react(self):
        """Detects React frontend from technology mentions."""

    def test_tech_stack_detection_python(self):
        """Detects Python/Django backend."""

    def test_entity_extraction_from_headings(self):
        """Extracts entity names from ### N.M EntityName headings."""

    def test_entity_extraction_fallback(self):
        """Falls back to narrative extraction when no headings."""

    def test_enum_extraction(self):
        """Extracts enum names from enum/status declarations."""

    def test_confidence_score_calculation(self):
        """Confidence decreases with more issues."""

    def test_section_map_line_ranges(self):
        """raw_section_map captures correct line ranges."""

    def test_edge_case_empty_prd(self):
        """Empty string returns needs_normalization=True."""
```

#### Class 2: TestStructuralValidator (~12 tests)
```python
class TestStructuralValidator:
    """Test the validate_structure() function."""

    def test_all_sections_present(self):
        """No STRUCT-001 violations when all 12 sections present."""

    def test_missing_section_reported(self):
        """STRUCT-001 for each missing section."""

    def test_svc_rows_without_braces_warned(self):
        """STRUCT-002 warning for SVC rows missing { } DTO notation."""

    def test_no_svc_rows_error(self):
        """STRUCT-002 error when zero SVC rows found."""

    def test_entity_table_format_validated(self):
        """STRUCT-003 checks for 6-column header."""

    def test_enum_pascal_case_validated(self):
        """STRUCT-009 warns on non-PascalCase enum values."""

    def test_sequential_svc_numbering(self):
        """STRUCT-010 warns on gaps in SVC numbering."""

    def test_milestone_without_svc_range(self):
        """STRUCT-005 warns on milestones missing SVC range line."""

    def test_seed_table_missing(self):
        """STRUCT-006 warns on missing seed credential table."""

    def test_docker_block_missing(self):
        """STRUCT-007 warns on missing Docker YAML."""

    def test_constraints_missing(self):
        """STRUCT-008 warns on missing constraint list."""

    def test_perfect_format_zero_violations(self):
        """Perfect target-format PRD produces zero violations."""
```

#### Class 3: TestTechStackHelpers (~10 tests)
```python
class TestTechStackHelpers:
    """Test tech-stack-aware helper functions."""

    def test_casing_rule_aspnet(self):
        """ASP.NET returns camelCase rule."""

    def test_casing_rule_python(self):
        """Python returns snake_case rule."""

    def test_casing_rule_unknown(self):
        """Unknown backend returns camelCase default."""

    def test_service_naming_angular(self):
        """Angular returns EntityService pattern."""

    def test_service_naming_react(self):
        """React returns useEntity/entityApi pattern."""

    def test_constraint_families_aspnet_full(self):
        """ASP.NET + EF Core + Dapper + MediatR produces all constraint families."""

    def test_constraint_families_express_minimal(self):
        """Express.js produces minimal constraint set."""

    def test_inference_rules_strict(self):
        """Strict mode forbids all inferred fields."""

    def test_inference_rules_moderate(self):
        """Moderate mode allows standard fields."""

    def test_inference_rules_aggressive(self):
        """Aggressive mode allows SVC generation."""
```

#### Class 4: TestConfigValidation (~8 tests)
```python
class TestConfigValidation:
    """Test PRDNormalizationConfig loading and validation."""

    def test_default_config(self):
        """Default config has expected values."""

    def test_invalid_mode_rejected(self):
        """mode must be auto|always|never."""

    def test_invalid_inference_level_rejected(self):
        """inference_level must be strict|moderate|aggressive."""

    def test_invalid_gap_handling_rejected(self):
        """gap_handling must be flag|warn|block."""

    def test_budget_minimum_enforced(self):
        """max_pipeline_budget_usd must be >= 0.1."""

    def test_depth_quick_disables(self):
        """Quick depth disables normalization by default."""

    def test_user_override_respected(self):
        """Explicit user override prevents depth-gating."""

    def test_yaml_loading(self):
        """Config loads correctly from YAML section."""
```

#### Class 5: TestCLIWiring (~10 tests)
```python
class TestCLIWiring:
    """Test Phase -1 integration in cli.py."""

    def test_phase_minus_1_runs_before_phase_0(self):
        """Phase -1 executes before Interview phase."""

    def test_prd_path_swapped_after_normalization(self):
        """args.prd points to normalized file after success."""

    def test_original_prd_preserved(self):
        """Original PRD file is not modified."""

    def test_crash_isolation(self):
        """Phase -1 failure does not block subsequent phases."""

    def test_mode_never_skips(self):
        """mode=never skips normalization entirely."""

    def test_mode_auto_skips_good_prd(self):
        """mode=auto skips normalization for already-formatted PRDs."""

    def test_gap_handling_block_exits(self):
        """gap_handling=block exits main() when gaps exist."""

    def test_completed_phases_tracking(self):
        """'prd_normalization' added to completed_phases on success."""

    def test_artifacts_tracking(self):
        """Report and output paths added to artifacts."""

    def test_no_prd_flag_skips_entirely(self):
        """Without --prd, Phase -1 is completely skipped."""
```

#### Class 6: TestFaithfulnessScoreParsing (~5 tests)
```python
class TestFaithfulnessScoreParsing:
    """Test _parse_faithfulness_score() helper."""

    def test_parses_decimal_score(self):
        """Extracts 0.95 from 'Faithfulness Score: 0.95 / 1.00'."""

    def test_parses_integer_score(self):
        """Extracts 1.0 from 'Faithfulness Score: 1 / 1.00'."""

    def test_missing_file_returns_zero(self):
        """Non-existent file returns 0.0."""

    def test_malformed_report_returns_zero(self):
        """Report without score line returns 0.0."""

    def test_caps_at_one(self):
        """Score > 1.0 is capped at 1.0."""
```

**Total test count target: ~60 tests minimum across 6 classes.**

---

## STEP 4 — VERIFICATION CHECKLIST

After implementation, verify ALL of the following:

### 4.1 Config Integration
- [ ] `PRDNormalizationConfig` exists in config.py with all 7 fields
- [ ] Added to `AgentTeamConfig` as `prd_normalization` field
- [ ] `_dict_to_config()` handles `prd_normalization` section with validation
- [ ] `load_config()` returns tuple (no regression from v6.0 change)
- [ ] Depth-gating: `quick` disables, `standard`/`thorough`/`exhaustive` enable
- [ ] User override tracking: `prd_normalization.*` keys added to `user_overrides` set

### 4.2 Detection Function
- [ ] `needs_normalization()` returns `NormalizationAnalysis` dataclass
- [ ] Detects all 12 missing sections
- [ ] Detects malformed SVC tables (no brace DTOs)
- [ ] Detects malformed entity tables (wrong column count)
- [ ] Detects missing enum code blocks
- [ ] Tech stack detection for all 7 backend + 5 frontend + 5 database + 7 ORM patterns
- [ ] Returns `needs_normalization=False` for a PRD already in perfect format

### 4.3 Pipeline Execution
- [ ] Steps 1-7 execute in correct order
- [ ] Steps 3a and 3b run in parallel
- [ ] Budget guard prevents runaway costs
- [ ] All intermediate files written to `.agent-team/prd-normalization/`
- [ ] Sub-agent calls follow existing `_run_prd_reconciliation()` pattern
- [ ] `_assemble_normalized_prd()` produces 12-section output with `---` separators

### 4.4 Structural Validation
- [ ] STRUCT-001 through STRUCT-010 checks implemented
- [ ] Uses same regex patterns as downstream parsers
- [ ] Returns violations as `list[dict]` with `check`, `message`, `severity` keys

### 4.5 CLI Wiring
- [ ] Phase -1 block inserted BEFORE Phase 0 Interview
- [ ] `args.prd` swapped to normalized path on success
- [ ] Crash-isolated with try/except + traceback logging
- [ ] `completed_phases` and `artifacts` updated
- [ ] `mode="never"` and missing `--prd` both skip Phase -1
- [ ] `gap_handling="block"` exits `main()` when gaps > 0

### 4.6 Faithfulness
- [ ] Prompt constants include NO-INVENT, STANDARD-FIELDS-EXCEPTION, TRACEABILITY-MAP, GAP-FLAGGING, NO-RENAME, CASING-INFERENCE rules
- [ ] Faithfulness validator prompt explicitly checks for invented content
- [ ] Score parsed from report file
- [ ] Warning printed when score < 0.8

### 4.7 Tests
- [ ] `test_prd_normalizer.py` exists with 6+ test classes
- [ ] 60+ tests across detection, validation, helpers, config, wiring, parsing
- [ ] All tests pass with `pytest tests/test_prd_normalizer.py -v`
- [ ] Full test suite (`pytest tests/ -v`) shows 0 new regressions

### 4.8 Cross-Compatibility
- [ ] Normalized PRD triggers `detect_large_prd()` correctly (respects 50KB threshold)
- [ ] `_parse_svc_table()` in quality_checks.py parses normalized SVC tables
- [ ] `_parse_field_schema()` returns non-empty dict for normalized DTO notation
- [ ] `_RE_MILESTONE_HEADER` in milestone_manager.py matches normalized milestone headers
- [ ] `_RE_EMAIL`/`_RE_PASSWORD`/`_RE_ROLE` in browser_testing.py extract seed credentials
- [ ] PRD chunking `_SECTION_PATTERNS` match normalized section headings

---

## STEP 5 — WHAT NOT TO DO

| Anti-Pattern | Why |
|-------------|-----|
| Invent endpoints not in the source PRD | Violates faithfulness — the normalizer translates format, not content |
| Add entities the user never mentioned | Same as above — flag gaps instead |
| Hardcode tech stack assumptions | Must detect from source PRD and adapt |
| Skip structural validation | The whole point is ensuring downstream parser compatibility |
| Use `asyncio.run()` inside an already-async context | Known architectural issue — follow existing E2E/browser testing pattern |
| Modify the original PRD file | Always write to `.agent-team/PRD_NORMALIZED.md` |
| Block the pipeline on non-critical gaps | Use severity levels — only `gap_handling=block` should halt |
| Create the module without reading cli.py first | Integration points are precise — wrong line numbers = broken wiring |

---

## STEP 6 — SIZE AND COMPLEXITY TARGETS

| Metric | Target |
|--------|--------|
| `prd_normalizer.py` | 800-1200 lines |
| New config in `config.py` | 30-50 lines |
| CLI wiring in `cli.py` | 60-80 lines |
| Prompt injection in `agents.py` | 5-10 lines |
| `test_prd_normalizer.py` | 400-600 lines, 60+ tests |
| Total new code | ~1400-1900 lines |
| Files modified | 3 (config.py, cli.py, agents.py) |
| Files created | 2 (prd_normalizer.py, test_prd_normalizer.py) |

---

## EXECUTION ORDER

1. Read all files listed in Step 0
2. Create `PRDNormalizationConfig` in config.py + update `_dict_to_config()`
3. Create `prd_normalizer.py` with detection function, dataclasses, and structural validator
4. Add prompt constants to `prd_normalizer.py`
5. Implement pipeline orchestrator (wire `_run_sub_agent` to match existing pattern)
6. Add Phase -1 block to cli.py
7. Add normalization context injection to agents.py
8. Create `test_prd_normalizer.py` with all 6 test classes
9. Run full test suite, fix any regressions
10. Run verification checklist from Step 4
