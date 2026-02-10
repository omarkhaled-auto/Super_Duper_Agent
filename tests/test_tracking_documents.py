"""Tests for Per-Phase Tracking Documents (tracking_documents.py + wiring).

Covers:
 - E2E Coverage Matrix generation, parsing, edge cases
 - Fix Cycle Log initialization, entry building, parsing
 - Milestone Handoff generation, consumption checklists, parsing, wiring completeness
 - TrackingDocumentsConfig defaults, YAML loading, gate validation
 - Prompt injections (agents.py, e2e_testing.py constants)
 - CLI wiring verification (config gating, crash isolation, execution order)
 - Cross-feature integration and backward compatibility
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.config import (
    AgentTeamConfig,
    TrackingDocumentsConfig,
    _dict_to_config,
)
from agent_team.tracking_documents import (
    E2ECoverageStats,
    FixCycleStats,
    MilestoneHandoffEntry,
    FIX_CYCLE_LOG_INSTRUCTIONS,
    MILESTONE_HANDOFF_INSTRUCTIONS,
    E2E_COVERAGE_MATRIX_TEMPLATE,
    generate_e2e_coverage_matrix,
    parse_e2e_coverage_matrix,
    initialize_fix_cycle_log,
    build_fix_cycle_entry,
    parse_fix_cycle_log,
    generate_milestone_handoff_entry,
    generate_consumption_checklist,
    parse_milestone_handoff,
    parse_handoff_interfaces,
    compute_wiring_completeness,
    _extract_api_requirements,
    _extract_route_requirements,
    _extract_workflow_requirements,
)


# =========================================================================
# E2E Coverage Matrix — Generation
# =========================================================================

class TestGenerateE2ECoverageMatrix:
    """Tests for generate_e2e_coverage_matrix()."""

    def test_with_api_endpoints(self):
        """REQUIREMENTS.md with API endpoints produces table rows."""
        reqs = textwrap.dedent("""\
            # Requirements
            - [ ] REQ-001: User registration
              POST /api/auth/register
            - [ ] REQ-002: List tenders
              GET /api/tenders
        """)
        result = generate_e2e_coverage_matrix(reqs)
        assert "## Backend API Coverage" in result
        assert "/api/auth/register" in result
        assert "/api/tenders" in result
        assert "POST" in result
        assert "GET" in result

    def test_with_frontend_routes(self):
        """REQUIREMENTS.md with frontend routes produces route table rows."""
        reqs = textwrap.dedent("""\
            # Requirements
            - [ ] REQ-010: The /dashboard page shows summary
            - [ ] REQ-011: Navigate to the /login page
        """)
        result = generate_e2e_coverage_matrix(reqs)
        assert "## Frontend Route Coverage" in result
        assert "/dashboard" in result
        assert "/login" in result

    def test_with_multi_role_workflows(self):
        """REQUIREMENTS.md with multi-step workflows produces workflow table."""
        reqs = textwrap.dedent("""\
            # Requirements
            - [ ] REQ-020: User submits -> admin approves
              create -> then -> approve workflow
        """)
        result = generate_e2e_coverage_matrix(reqs)
        assert "## Cross-Role Workflows" in result

    def test_no_endpoints(self):
        """REQUIREMENTS.md with no endpoints produces empty tables with headers."""
        reqs = "Some general description without any endpoints."
        result = generate_e2e_coverage_matrix(reqs)
        assert "## Backend API Coverage" in result
        assert "## Frontend Route Coverage" in result
        assert "## Cross-Role Workflows" in result
        assert "No API endpoints detected" in result
        assert "No frontend routes detected" in result

    def test_with_app_info(self):
        """AppTypeInfo adds framework header."""
        from agent_team.e2e_testing import AppTypeInfo
        app_info = AppTypeInfo(
            backend_framework="Express",
            frontend_framework="Angular",
            language="TypeScript",
        )
        reqs = "- [ ] REQ-001: GET /api/health"
        result = generate_e2e_coverage_matrix(reqs, app_info=app_info)
        assert "Express" in result
        assert "Angular" in result
        assert "TypeScript" in result

    def test_svc_entries_appear(self):
        """SVC-xxx requirement IDs are extracted."""
        reqs = textwrap.dedent("""\
            - [ ] SVC-001: TenderService.getAll() wired to GET /api/tenders
            - [ ] SVC-002: AuthService.login() wired to POST /api/auth/login
        """)
        result = generate_e2e_coverage_matrix(reqs)
        assert "SVC-001" in result or "/api/tenders" in result
        assert "/api/auth/login" in result

    def test_all_rows_start_unchecked(self):
        """All checkboxes start as [ ] (not [x])."""
        reqs = textwrap.dedent("""\
            - [ ] REQ-001: POST /api/users
            - [ ] REQ-002: GET /api/users
        """)
        result = generate_e2e_coverage_matrix(reqs)
        assert "[x]" not in result
        assert "[ ]" in result

    def test_coverage_footer(self):
        """Output contains a coverage summary footer."""
        reqs = "- [ ] REQ-001: GET /api/health"
        result = generate_e2e_coverage_matrix(reqs)
        assert "## Coverage:" in result
        assert "written" in result

    def test_path_parameters_extracted(self):
        """Endpoints with path parameters like /api/tenders/:id are extracted."""
        reqs = "- [ ] REQ-005: GET /api/tenders/:id\n- [ ] REQ-006: DELETE /api/tenders/:id"
        result = generate_e2e_coverage_matrix(reqs)
        assert "/api/tenders/:id" in result

    def test_very_long_requirements(self):
        """Large REQUIREMENTS.md (>100 items) still extracts all."""
        lines = []
        for i in range(120):
            lines.append(f"- [ ] REQ-{i:03d}: GET /api/items/{i}")
        reqs = "\n".join(lines)
        result = generate_e2e_coverage_matrix(reqs)
        # Should have at least 100 items extracted
        assert result.count("[ ]") >= 100

    def test_unicode_in_descriptions(self):
        """Unicode characters in requirement descriptions are handled."""
        reqs = "- [ ] REQ-001: Cr\u00e9er un utilisateur POST /api/users\n- [ ] REQ-002: \u0627\u0644\u0645\u0646\u0627\u0642\u0635\u0627\u062a GET /api/tenders"
        result = generate_e2e_coverage_matrix(reqs)
        assert "/api/users" in result
        assert "/api/tenders" in result

    def test_no_clear_endpoints_prose_only(self):
        """REQUIREMENTS.md with only prose produces best-effort (may be empty tables)."""
        reqs = "The system should support user management and reporting features."
        result = generate_e2e_coverage_matrix(reqs)
        # Should still produce valid markdown
        assert "## Backend API Coverage" in result


# =========================================================================
# E2E Coverage Matrix — Parsing
# =========================================================================

class TestParseE2ECoverageMatrix:
    """Tests for parse_e2e_coverage_matrix()."""

    def test_all_checked(self):
        """All items checked => 100% coverage."""
        matrix = textwrap.dedent("""\
            ## Backend API Coverage
            | Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
            |--------|----------|--------|-------|-----------|:------------:|:-----------:|
            | REQ-001 | /api/a | GET |  | test.js | [x] | [x] |
            | REQ-002 | /api/b | POST |  | test.js | [x] | [x] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 2
        assert stats.tests_written == 2
        assert stats.tests_passed == 2
        assert stats.coverage_ratio == 1.0
        assert stats.pass_ratio == 1.0

    def test_half_checked(self):
        """Half items checked => 50% coverage."""
        matrix = textwrap.dedent("""\
            ## Backend API Coverage
            | Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
            |--------|----------|--------|-------|-----------|:------------:|:-----------:|
            | REQ-001 | /api/a | GET |  | test.js | [x] | [x] |
            | REQ-002 | /api/b | POST |  |  | [ ] | [ ] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 2
        assert stats.tests_written == 1
        assert stats.coverage_ratio == 0.5

    def test_zero_checked(self):
        """Zero items checked => 0% coverage."""
        matrix = textwrap.dedent("""\
            ## Backend API Coverage
            | Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
            |--------|----------|--------|-------|-----------|:------------:|:-----------:|
            | REQ-001 | /api/a | GET |  |  | [ ] | [ ] |
            | REQ-002 | /api/b | POST |  |  | [ ] | [ ] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 2
        assert stats.tests_written == 0
        assert stats.coverage_ratio == 0.0

    def test_na_items_excluded(self):
        """N/A items don't count toward total."""
        matrix = textwrap.dedent("""\
            ## Backend API Coverage
            | Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
            |--------|----------|--------|-------|-----------|:------------:|:-----------:|
            | REQ-001 | /api/a | GET |  | test.js | [x] | [x] |
            | REQ-002 | /api/b | POST |  |  | [N/A] | [N/A] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 1  # N/A excluded
        assert stats.tests_written == 1

    def test_empty_content(self):
        """Empty/missing matrix returns zero stats."""
        stats = parse_e2e_coverage_matrix("")
        assert stats.total_items == 0
        assert stats.tests_written == 0
        assert stats.coverage_ratio == 0.0

    def test_only_frontend_section(self):
        """Matrix with only frontend section parses correctly."""
        matrix = textwrap.dedent("""\
            ## Frontend Route Coverage
            | Route | Component | Key Workflows | Test File | Tested | Passed |
            |-------|-----------|---------------|-----------|:------:|:------:|
            | /dashboard | DashPage | View |  | [x] | [ ] |
            | /login | LoginPage | Auth |  | [x] | [x] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 2
        assert stats.tests_written == 2
        assert stats.tests_passed == 1

    def test_both_backend_and_frontend(self):
        """Combined backend + frontend sections have correct combined stats."""
        matrix = textwrap.dedent("""\
            ## Backend API Coverage
            | Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
            |--------|----------|--------|-------|-----------|:------------:|:-----------:|
            | REQ-001 | /api/a | GET |  | test.js | [x] | [x] |

            ## Frontend Route Coverage
            | Route | Component | Key Workflows | Test File | Tested | Passed |
            |-------|-----------|---------------|-----------|:------:|:------:|
            | /dashboard | DashPage | View |  | [x] | [ ] |
        """)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 2
        assert stats.tests_written == 2
        assert stats.tests_passed == 1


# =========================================================================
# E2E Coverage Matrix — Extraction Helpers
# =========================================================================

class TestExtractionHelpers:
    """Tests for the internal _extract_* functions."""

    def test_extract_api_requirements_basic(self):
        reqs = "- [ ] REQ-001: POST /api/auth/register — User registration"
        result = _extract_api_requirements(reqs)
        assert len(result) >= 1
        assert any(r["endpoint"] == "/api/auth/register" for r in result)

    def test_extract_api_deduplicates(self):
        """Duplicate endpoints are deduplicated."""
        reqs = textwrap.dedent("""\
            - [ ] REQ-001: POST /api/auth/register
            - [ ] REQ-002: POST /api/auth/register again
        """)
        result = _extract_api_requirements(reqs)
        endpoints = [r["endpoint"] for r in result if r["method"] == "POST"]
        # Should only appear once
        assert endpoints.count("/api/auth/register") == 1

    def test_extract_route_requirements(self):
        reqs = "Navigate to the /dashboard page to view stats."
        result = _extract_route_requirements(reqs)
        assert len(result) >= 1
        assert any(r["route"] == "/dashboard" for r in result)

    def test_extract_workflow_requirements(self):
        reqs = "create -> then -> approve workflow with multi-role steps"
        result = _extract_workflow_requirements(reqs)
        assert len(result) >= 1

    def test_extract_roles_from_api_reqs(self):
        reqs = "- [ ] REQ-001: Admin creates tenders POST /api/tenders"
        result = _extract_api_requirements(reqs)
        assert len(result) >= 1
        assert "admin" in result[0].get("roles", "")


# =========================================================================
# Fix Cycle Log — Initialization
# =========================================================================

class TestInitializeFixCycleLog:
    """Tests for initialize_fix_cycle_log()."""

    def test_creates_on_empty_dir(self, tmp_path):
        """Empty directory creates FIX_CYCLE_LOG.md with header."""
        req_dir = str(tmp_path / "reqs")
        path = initialize_fix_cycle_log(req_dir)
        assert path.is_file()
        content = path.read_text(encoding="utf-8")
        assert "# Fix Cycle Log" in content
        assert "DO NOT repeat" in content

    def test_existing_file_not_overwritten(self, tmp_path):
        """Existing file returns existing path, doesn't overwrite."""
        req_dir = tmp_path / "reqs"
        req_dir.mkdir()
        log_file = req_dir / "FIX_CYCLE_LOG.md"
        log_file.write_text("my custom content", encoding="utf-8")

        path = initialize_fix_cycle_log(str(req_dir))
        assert path == log_file
        content = path.read_text(encoding="utf-8")
        assert content == "my custom content"

    def test_unicode_path(self, tmp_path):
        """Unicode path works correctly."""
        req_dir = tmp_path / "\u062a\u0633\u062a"
        path = initialize_fix_cycle_log(str(req_dir))
        assert path.is_file()

    def test_creates_parent_dirs(self, tmp_path):
        """Creates parent directories if they don't exist."""
        deep_dir = str(tmp_path / "a" / "b" / "c")
        path = initialize_fix_cycle_log(deep_dir)
        assert path.is_file()


# =========================================================================
# Fix Cycle Log — Entry Building
# =========================================================================

class TestBuildFixCycleEntry:
    """Tests for build_fix_cycle_entry()."""

    def test_correct_markdown_format(self):
        """Entry has correct markdown format."""
        entry = build_fix_cycle_entry(
            phase="E2E Backend",
            cycle_number=1,
            failures=["test_login failed: 401"],
        )
        assert "## E2E Backend \u2014 Cycle 1" in entry
        assert "test_login failed: 401" in entry
        assert "Failures to fix:" in entry

    def test_previous_cycles_shown(self):
        """Previous cycle count is included."""
        entry = build_fix_cycle_entry(
            phase="Mock Data",
            cycle_number=3,
            failures=["mock in service.ts"],
            previous_cycles=2,
        )
        assert "Previous cycles in this phase:** 2" in entry

    def test_empty_failures_list(self):
        """Empty failures list produces valid entry."""
        entry = build_fix_cycle_entry(
            phase="UI Compliance",
            cycle_number=1,
            failures=[],
        )
        assert "(none specified)" in entry
        assert "## UI Compliance" in entry

    def test_special_characters_in_failures(self):
        """Special characters in failures are preserved."""
        entry = build_fix_cycle_entry(
            phase="Integrity",
            cycle_number=1,
            failures=["src/app/service.ts:42 \u2014 {mockData: true}"],
        )
        assert "{mockData: true}" in entry


# =========================================================================
# Fix Cycle Log — Parsing
# =========================================================================

class TestParseFixCycleLog:
    """Tests for parse_fix_cycle_log()."""

    def test_three_cycles(self):
        """Log with 3 cycles parses correctly."""
        content = textwrap.dedent("""\
            # Fix Cycle Log

            ---

            ## E2E Backend \u2014 Cycle 1

            **Failures to fix:**
            - test failure
            ---

            ## E2E Backend \u2014 Cycle 2

            **Failures to fix:**
            - test failure 2
            ---

            ## Mock Data \u2014 Cycle 1

            **Failures to fix:**
            - mock in service
        """)
        stats = parse_fix_cycle_log(content)
        assert stats.total_cycles == 3
        assert stats.cycles_by_phase["E2E Backend"] == 2
        assert stats.cycles_by_phase["Mock Data"] == 1

    def test_empty_log(self):
        """Empty log returns zero stats."""
        stats = parse_fix_cycle_log("")
        assert stats.total_cycles == 0
        assert stats.cycles_by_phase == {}

    def test_header_only(self):
        """Log with only header returns zero cycles."""
        content = "# Fix Cycle Log\n\nThis document tracks...\n\n---\n"
        stats = parse_fix_cycle_log(content)
        assert stats.total_cycles == 0

    def test_resolved_detection(self):
        """Detects resolved state from Result: line."""
        content = textwrap.dedent("""\
            ## E2E Backend \u2014 Cycle 1

            **Failures to fix:**
            - test failure

            Result: all fixed, 0 remain
        """)
        stats = parse_fix_cycle_log(content)
        assert stats.total_cycles == 1
        assert stats.last_phase_resolved is True


# =========================================================================
# Fix Cycle Log — Constants
# =========================================================================

class TestFixCycleLogConstants:
    """Tests for FIX_CYCLE_LOG_INSTRUCTIONS constant."""

    def test_contains_key_phrases(self):
        assert "Read" in FIX_CYCLE_LOG_INSTRUCTIONS
        assert "FIX_CYCLE_LOG.md" in FIX_CYCLE_LOG_INSTRUCTIONS
        assert "DO NOT repeat" in FIX_CYCLE_LOG_INSTRUCTIONS
        assert "Append" in FIX_CYCLE_LOG_INSTRUCTIONS

    def test_has_format_placeholder(self):
        """Has {requirements_dir} placeholder for formatting."""
        assert "{requirements_dir}" in FIX_CYCLE_LOG_INSTRUCTIONS

    def test_formateable(self):
        """Can be formatted with requirements_dir."""
        formatted = FIX_CYCLE_LOG_INSTRUCTIONS.format(requirements_dir="/my/dir")
        assert "/my/dir" in formatted
        assert "{requirements_dir}" not in formatted


# =========================================================================
# Milestone Handoff — Generation
# =========================================================================

class TestGenerateMilestoneHandoffEntry:
    """Tests for generate_milestone_handoff_entry()."""

    def test_correct_structure(self):
        """Entry has correct markdown structure with all sections."""
        entry = generate_milestone_handoff_entry(
            milestone_id="milestone-1",
            milestone_title="Backend API",
        )
        assert "## milestone-1: Backend API \u2014 COMPLETE" in entry
        assert "### Exposed Interfaces" in entry
        assert "### Database State" in entry
        assert "### Enum/Status Values" in entry
        assert "### Environment Variables" in entry
        assert "### Files Created/Modified" in entry
        assert "### Known Limitations" in entry

    def test_custom_status(self):
        """Status parameter is reflected in output."""
        entry = generate_milestone_handoff_entry(
            milestone_id="milestone-2",
            milestone_title="Frontend",
            status="IN PROGRESS",
        )
        assert "IN PROGRESS" in entry

    def test_interfaces_table_has_correct_columns(self):
        """Interfaces table has all required columns."""
        entry = generate_milestone_handoff_entry("ms-1", "API")
        assert "Endpoint" in entry
        assert "Method" in entry
        assert "Auth Required" in entry
        assert "Request Body" in entry
        assert "Response Shape" in entry


# =========================================================================
# Milestone Handoff — Enum/Status Values
# =========================================================================


class TestMilestoneHandoffEnumValues:
    """Tests for the Enum/Status Values subsection in MILESTONE_HANDOFF.md."""

    def test_handoff_entry_contains_enum_section(self):
        """generate_milestone_handoff_entry() includes Enum/Status Values subsection."""
        entry = generate_milestone_handoff_entry("m-1", "Auth Service")
        assert "### Enum/Status Values" in entry

    def test_handoff_entry_enum_table_headers(self):
        """Enum table has correct column headers."""
        entry = generate_milestone_handoff_entry("m-1", "Auth Service")
        assert "| Entity | Field | Valid Values | DB Type | API String |" in entry

    def test_handoff_entry_enum_section_position(self):
        """Enum section appears between Database State and Environment Variables."""
        entry = generate_milestone_handoff_entry("m-1", "Auth Service")
        db_pos = entry.index("### Database State")
        enum_pos = entry.index("### Enum/Status Values")
        env_pos = entry.index("### Environment Variables")
        assert db_pos < enum_pos < env_pos

    def test_handoff_entry_enum_agent_comment(self):
        """Enum section includes agent instruction comment."""
        entry = generate_milestone_handoff_entry("m-1", "Auth Service")
        assert "EVERY entity with a status/type/enum field" in entry

    def test_milestone_handoff_instructions_mention_enum(self):
        """MILESTONE_HANDOFF_INSTRUCTIONS references enum/status values."""
        from agent_team.tracking_documents import MILESTONE_HANDOFF_INSTRUCTIONS
        assert "Enum/status values" in MILESTONE_HANDOFF_INSTRUCTIONS

    def test_milestone_handoff_instructions_read_enum(self):
        """MILESTONE_HANDOFF_INSTRUCTIONS tells agents to study Enum/Status Values."""
        from agent_team.tracking_documents import MILESTONE_HANDOFF_INSTRUCTIONS
        assert "Enum/Status Values" in MILESTONE_HANDOFF_INSTRUCTIONS


# =========================================================================
# Milestone Handoff — Consumption Checklist
# =========================================================================

class TestGenerateConsumptionChecklist:
    """Tests for generate_consumption_checklist()."""

    def test_three_predecessor_interfaces(self):
        """3 predecessor interfaces produce 3 rows with [ ]."""
        interfaces = [
            {"source_milestone": "milestone-1", "endpoint": "/api/auth/login", "method": "POST", "frontend_service": "AuthService.login()"},
            {"source_milestone": "milestone-1", "endpoint": "/api/tenders", "method": "GET", "frontend_service": "TenderService.getAll()"},
            {"source_milestone": "milestone-2", "endpoint": "/api/users", "method": "GET", "frontend_service": "UserService.list()"},
        ]
        result = generate_consumption_checklist("milestone-3", "Frontend", interfaces)
        assert result.count("[ ]") == 3
        assert "milestone-1" in result
        assert "milestone-2" in result
        assert "/api/auth/login" in result

    def test_empty_predecessors(self):
        """Empty predecessors produce empty section."""
        result = generate_consumption_checklist("ms-1", "Test", [])
        assert "No predecessor interfaces to consume" in result

    def test_mixed_milestone_sources(self):
        """Multiple sources show correct source column."""
        interfaces = [
            {"source_milestone": "ms-1", "endpoint": "/a", "method": "GET", "frontend_service": ""},
            {"source_milestone": "ms-2", "endpoint": "/b", "method": "POST", "frontend_service": ""},
        ]
        result = generate_consumption_checklist("ms-3", "App", interfaces)
        assert "ms-1" in result
        assert "ms-2" in result

    def test_wiring_summary(self):
        """Wiring summary line is present."""
        interfaces = [
            {"source_milestone": "ms-1", "endpoint": "/a", "method": "GET", "frontend_service": ""},
            {"source_milestone": "ms-1", "endpoint": "/b", "method": "POST", "frontend_service": ""},
        ]
        result = generate_consumption_checklist("ms-2", "App", interfaces)
        assert "Wiring: 0/2 complete" in result


# =========================================================================
# Milestone Handoff — Parsing
# =========================================================================

class TestParseMilestoneHandoff:
    """Tests for parse_milestone_handoff()."""

    def test_two_milestone_sections(self):
        """Handoff with 2 milestone sections produces 2 entries."""
        content = textwrap.dedent("""\
            # Milestone Handoff Registry

            ---

            ## milestone-1: Backend API \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            | /api/auth/login | POST | No | {email, password} | {token, user} |

            ### Database State After This Milestone
            Users table created.

            ---

            ## milestone-2: Frontend \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
        """)
        entries = parse_milestone_handoff(content)
        assert len(entries) == 2
        assert entries[0].milestone_id == "milestone-1"
        assert entries[0].status == "COMPLETE"
        assert entries[1].milestone_id == "milestone-2"

    def test_filled_interfaces_table(self):
        """Correctly extracts interface rows."""
        content = textwrap.dedent("""\
            ## milestone-1: API \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            | /api/tenders | GET | Yes | | {id, title, status} |
            | /api/tenders | POST | Yes | {title, desc} | {id} |
        """)
        entries = parse_milestone_handoff(content)
        assert len(entries) == 1
        assert len(entries[0].interfaces) == 2
        assert entries[0].interfaces[0]["endpoint"] == "/api/tenders"
        assert entries[0].interfaces[0]["method"] == "GET"

    def test_empty_tables(self):
        """Empty tables produce empty interface lists."""
        content = textwrap.dedent("""\
            ## milestone-1: API \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            <!-- Agent: Fill this table -->

            ### Database State After This Milestone
        """)
        entries = parse_milestone_handoff(content)
        assert len(entries) == 1
        assert entries[0].interfaces == []

    def test_empty_content(self):
        """Empty content returns empty list."""
        assert parse_milestone_handoff("") == []
        assert parse_milestone_handoff("   ") == []

    def test_resume_duplicate_skipped(self):
        """Duplicate milestone sections (resume case) produce only one entry."""
        content = textwrap.dedent("""\
            ## milestone-1: API \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|

            ---

            ## milestone-1: API \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
        """)
        entries = parse_milestone_handoff(content)
        assert len(entries) == 1

    def test_malformed_tables_graceful(self):
        """Malformed tables don't crash."""
        content = textwrap.dedent("""\
            ## milestone-1: API \u2014 COMPLETE

            ### Exposed Interfaces
            |broken row without enough pipes|
            | also | broken |

            ### Database State
        """)
        entries = parse_milestone_handoff(content)
        assert len(entries) == 1  # Still parses header


# =========================================================================
# Milestone Handoff — parse_handoff_interfaces
# =========================================================================

class TestParseHandoffInterfaces:
    """Tests for parse_handoff_interfaces()."""

    def test_extracts_for_specific_milestone(self):
        content = textwrap.dedent("""\
            ## milestone-1: Backend \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            | /api/login | POST | No | {email} | {token} |

            ## milestone-2: Frontend \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            | /api/pages | GET | Yes | | {pages} |
        """)
        interfaces = parse_handoff_interfaces(content, "milestone-1")
        assert len(interfaces) == 1
        assert interfaces[0]["endpoint"] == "/api/login"
        assert interfaces[0]["source_milestone"] == "milestone-1"

    def test_missing_milestone(self):
        content = "## milestone-1: API \u2014 COMPLETE\n### Exposed Interfaces\n"
        result = parse_handoff_interfaces(content, "milestone-99")
        assert result == []

    def test_empty_content(self):
        assert parse_handoff_interfaces("", "ms-1") == []

    def test_empty_milestone_id(self):
        assert parse_handoff_interfaces("## ms-1: X \u2014 Y", "") == []


# =========================================================================
# Milestone Handoff — Wiring Completeness
# =========================================================================

class TestComputeWiringCompleteness:
    """Tests for compute_wiring_completeness()."""

    def test_three_wired_of_five(self):
        """3 wired / 5 total = (3, 5)."""
        content = textwrap.dedent("""\
            ### milestone-3: Frontend \u2014 Consuming From Predecessors
            | Source Milestone | Endpoint | Method | Frontend Service | Wired? |
            |-----------------|----------|--------|-----------------|:------:|
            | ms-1 | /api/a | GET | SvcA | [x] |
            | ms-1 | /api/b | POST | SvcB | [x] |
            | ms-1 | /api/c | DELETE | SvcC | [x] |
            | ms-2 | /api/d | GET | SvcD | [ ] |
            | ms-2 | /api/e | PUT | SvcE | [ ] |
        """)
        wired, total = compute_wiring_completeness(content, "milestone-3")
        assert wired == 3
        assert total == 5

    def test_all_wired(self):
        """All wired => (N, N)."""
        content = textwrap.dedent("""\
            ### milestone-2: App \u2014 Consuming From Predecessors
            | Source | Endpoint | Method | Service | Wired? |
            |-------|----------|--------|---------|:------:|
            | ms-1 | /a | GET | Svc | [x] |
            | ms-1 | /b | POST | Svc | [x] |
        """)
        wired, total = compute_wiring_completeness(content, "milestone-2")
        assert wired == 2
        assert total == 2

    def test_none_wired(self):
        """None wired => (0, N)."""
        content = textwrap.dedent("""\
            ### milestone-2: App \u2014 Consuming From Predecessors
            | Source | Endpoint | Method | Service | Wired? |
            |-------|----------|--------|---------|:------:|
            | ms-1 | /a | GET | Svc | [ ] |
            | ms-1 | /b | POST | Svc | [ ] |
        """)
        wired, total = compute_wiring_completeness(content, "milestone-2")
        assert wired == 0
        assert total == 2

    def test_no_checklist_for_milestone(self):
        """No checklist for the requested milestone => (0, 0)."""
        content = textwrap.dedent("""\
            ### milestone-5: Other \u2014 Consuming From Predecessors
            | Source | Endpoint | Method | Service | Wired? |
            |-------|----------|--------|---------|:------:|
            | ms-1 | /a | GET | Svc | [x] |
        """)
        wired, total = compute_wiring_completeness(content, "milestone-99")
        assert wired == 0
        assert total == 0


# =========================================================================
# Config — TrackingDocumentsConfig
# =========================================================================

class TestTrackingDocumentsConfig:
    """Tests for TrackingDocumentsConfig and YAML loading."""

    def test_defaults(self):
        cfg = TrackingDocumentsConfig()
        assert cfg.e2e_coverage_matrix is True
        assert cfg.fix_cycle_log is True
        assert cfg.milestone_handoff is True
        assert cfg.coverage_completeness_gate == 0.8
        assert cfg.wiring_completeness_gate == 1.0

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.tracking_documents, TrackingDocumentsConfig)
        assert cfg.tracking_documents.e2e_coverage_matrix is True

    def test_yaml_loading(self):
        data = {
            "tracking_documents": {
                "e2e_coverage_matrix": False,
                "fix_cycle_log": False,
                "milestone_handoff": False,
                "coverage_completeness_gate": 0.5,
                "wiring_completeness_gate": 0.9,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.e2e_coverage_matrix is False
        assert cfg.tracking_documents.fix_cycle_log is False
        assert cfg.tracking_documents.milestone_handoff is False
        assert cfg.tracking_documents.coverage_completeness_gate == 0.5
        assert cfg.tracking_documents.wiring_completeness_gate == 0.9

    def test_coverage_gate_too_low(self):
        data = {"tracking_documents": {"coverage_completeness_gate": -0.1}}
        with pytest.raises(ValueError, match="coverage_completeness_gate"):
            _dict_to_config(data)

    def test_coverage_gate_too_high(self):
        data = {"tracking_documents": {"coverage_completeness_gate": 1.5}}
        with pytest.raises(ValueError, match="coverage_completeness_gate"):
            _dict_to_config(data)

    def test_wiring_gate_too_low(self):
        data = {"tracking_documents": {"wiring_completeness_gate": -0.1}}
        with pytest.raises(ValueError, match="wiring_completeness_gate"):
            _dict_to_config(data)

    def test_wiring_gate_too_high(self):
        data = {"tracking_documents": {"wiring_completeness_gate": 1.5}}
        with pytest.raises(ValueError, match="wiring_completeness_gate"):
            _dict_to_config(data)

    def test_boundary_values_valid(self):
        """Gate values at exact boundaries (0.0 and 1.0) are valid."""
        data = {
            "tracking_documents": {
                "coverage_completeness_gate": 0.0,
                "wiring_completeness_gate": 0.0,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.coverage_completeness_gate == 0.0
        assert cfg.tracking_documents.wiring_completeness_gate == 0.0

    def test_unknown_keys_ignored(self):
        """Unknown YAML keys don't break parsing."""
        data = {
            "tracking_documents": {
                "e2e_coverage_matrix": True,
                "unknown_future_key": 42,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.e2e_coverage_matrix is True

    def test_partial_yaml_uses_defaults(self):
        """Partial YAML (only some fields) uses defaults for missing."""
        data = {"tracking_documents": {"fix_cycle_log": False}}
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.fix_cycle_log is False
        assert cfg.tracking_documents.e2e_coverage_matrix is True  # default
        assert cfg.tracking_documents.milestone_handoff is True  # default
        assert cfg.tracking_documents.coverage_completeness_gate == 0.8  # default

    def test_no_tracking_documents_section(self):
        """Missing section entirely uses all defaults."""
        cfg, _ = _dict_to_config({})
        assert cfg.tracking_documents.e2e_coverage_matrix is True
        assert cfg.tracking_documents.fix_cycle_log is True

    def test_does_not_collide_with_existing_configs(self):
        """TrackingDocumentsConfig does not interfere with other configs."""
        data = {
            "e2e_testing": {"enabled": True},
            "integrity_scans": {"deployment_scan": False},
            "tracking_documents": {"fix_cycle_log": False},
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.e2e_testing.enabled is True
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.tracking_documents.fix_cycle_log is False


# =========================================================================
# Prompt Injection — E2E Prompts
# =========================================================================

class TestPromptInjections:
    """Tests for prompt injection content in agents.py and e2e_testing.py."""

    def test_backend_e2e_prompt_contains_matrix(self):
        from agent_team.e2e_testing import BACKEND_E2E_PROMPT
        assert "E2E_COVERAGE_MATRIX.md" in BACKEND_E2E_PROMPT

    def test_frontend_e2e_prompt_contains_matrix(self):
        from agent_team.e2e_testing import FRONTEND_E2E_PROMPT
        assert "E2E_COVERAGE_MATRIX.md" in FRONTEND_E2E_PROMPT

    def test_e2e_fix_prompt_contains_both(self):
        from agent_team.e2e_testing import E2E_FIX_PROMPT
        assert "FIX_CYCLE_LOG.md" in E2E_FIX_PROMPT
        assert "E2E_COVERAGE_MATRIX.md" in E2E_FIX_PROMPT

    def test_code_writer_prompt_contains_fix_cycle_log(self):
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "FIX_CYCLE_LOG.md" in CODE_WRITER_PROMPT

    def test_code_writer_prompt_contains_milestone_handoff(self):
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "MILESTONE_HANDOFF.md" in CODE_WRITER_PROMPT

    def test_architect_prompt_contains_handoff_preparation(self):
        from agent_team.agents import ARCHITECT_PROMPT
        assert "Milestone Handoff Preparation" in ARCHITECT_PROMPT

    def test_milestone_handoff_instructions_key_phrases(self):
        assert "Read" in MILESTONE_HANDOFF_INSTRUCTIONS
        assert "MILESTONE_HANDOFF.md" in MILESTONE_HANDOFF_INSTRUCTIONS
        assert "Exposed Interfaces" in MILESTONE_HANDOFF_INSTRUCTIONS
        assert "consumption checklist" in MILESTONE_HANDOFF_INSTRUCTIONS

    def test_milestone_handoff_instructions_formattable(self):
        formatted = MILESTONE_HANDOFF_INSTRUCTIONS.format(requirements_dir=".agent-team")
        assert ".agent-team" in formatted
        assert "{requirements_dir}" not in formatted


# =========================================================================
# Prompt Injection — build_milestone_execution_prompt
# =========================================================================

class TestMilestonePromptHandoffInjection:
    """Tests for handoff injection in build_milestone_execution_prompt()."""

    def test_contains_handoff_when_enabled(self):
        from agent_team.agents import build_milestone_execution_prompt
        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = True
        result = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=config,
        )
        assert "MILESTONE HANDOFF" in result

    def test_no_handoff_when_disabled(self):
        from agent_team.agents import build_milestone_execution_prompt
        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = False
        result = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=config,
        )
        assert "MILESTONE HANDOFF \u2014 MANDATORY" not in result

    def test_integration_verification_with_handoff(self):
        """When handoff enabled + predecessor context, verification block includes handoff."""
        from agent_team.agents import build_milestone_execution_prompt
        from agent_team.milestone_manager import MilestoneContext
        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = True
        mc = MilestoneContext(
            milestone_id="milestone-2",
            title="Frontend",
            requirements_path=".agent-team/milestones/milestone-2/REQUIREMENTS.md",
        )
        result = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=config,
            milestone_context=mc,
            predecessor_context="## Predecessor: milestone-1 completed backend",
        )
        assert "MILESTONE_HANDOFF.md" in result
        assert "consumption checklist" in result

    def test_no_verification_handoff_when_disabled(self):
        """When handoff disabled, verification block does NOT include handoff steps."""
        from agent_team.agents import build_milestone_execution_prompt
        from agent_team.milestone_manager import MilestoneContext
        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = False
        mc = MilestoneContext(
            milestone_id="milestone-2",
            title="Frontend",
            requirements_path=".agent-team/milestones/milestone-2/REQUIREMENTS.md",
        )
        result = build_milestone_execution_prompt(
            task="Build the app",
            depth="standard",
            config=config,
            milestone_context=mc,
            predecessor_context="## Predecessor: milestone-1 completed backend",
        )
        # Should have integration verification, but NOT the handoff-specific steps 6+7
        assert "consumption checklist is fully marked" not in result


# =========================================================================
# CLI Wiring — Fix Cycle Log in Fix Functions
# =========================================================================

class TestFixCycleLogInFixFunctions:
    """Verify fix cycle log instructions are injected into fix function prompts."""

    def test_mock_data_fix_has_log_injection_point(self):
        """_run_mock_data_fix injects fix cycle log when enabled."""
        # Verify by checking the source code for the pattern
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_mock_data_fix)
        assert "tracking_documents.fix_cycle_log" in source or "fix_cycle_log" in source
        assert "initialize_fix_cycle_log" in source
        assert "FIX_CYCLE_LOG_INSTRUCTIONS" in source

    def test_ui_compliance_fix_has_log_injection_point(self):
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_ui_compliance_fix)
        assert "fix_cycle_log" in source
        assert "initialize_fix_cycle_log" in source

    def test_integrity_fix_has_log_injection_point(self):
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_integrity_fix)
        assert "fix_cycle_log" in source
        assert "initialize_fix_cycle_log" in source

    def test_e2e_fix_has_log_injection_point(self):
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_e2e_fix)
        assert "fix_cycle_log" in source
        assert "initialize_fix_cycle_log" in source

    def test_review_only_has_log_injection_point(self):
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_review_only)
        assert "fix_cycle_log" in source
        assert "initialize_fix_cycle_log" in source


# =========================================================================
# CLI Wiring — E2E Coverage Matrix
# =========================================================================

class TestE2ECoverageMatrixWiring:
    """Verify E2E coverage matrix CLI wiring."""

    def test_matrix_generation_in_cli(self):
        """CLI source references generate_e2e_coverage_matrix."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        assert "generate_e2e_coverage_matrix" in source or "e2e_coverage_matrix" in source

    def test_matrix_parsing_in_cli(self):
        """CLI source references parse_e2e_coverage_matrix."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        assert "parse_e2e_coverage_matrix" in source or "e2e_coverage_matrix" in source

    def test_coverage_gate_in_cli(self):
        """CLI source checks coverage_completeness_gate."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        assert "coverage_completeness_gate" in source or "e2e_coverage_incomplete" in source


# =========================================================================
# CLI Wiring — Milestone Handoff
# =========================================================================

class TestMilestoneHandoffWiring:
    """Verify milestone handoff CLI wiring."""

    def test_handoff_generation_in_milestones(self):
        """_run_prd_milestones references generate_milestone_handoff_entry."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "generate_milestone_handoff_entry" in source

    def test_consumption_checklist_in_milestones(self):
        """_run_prd_milestones references generate_consumption_checklist."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "generate_consumption_checklist" in source

    def test_wiring_completeness_check_in_milestones(self):
        """_run_prd_milestones references compute_wiring_completeness."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "compute_wiring_completeness" in source

    def test_handoff_config_gating(self):
        """Handoff generation is gated by config.tracking_documents.milestone_handoff."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "tracking_documents.milestone_handoff" in source

    def test_handoff_crash_isolation(self):
        """Handoff generation is wrapped in try/except."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        # Verify crash isolation pattern exists around handoff code
        assert "except Exception" in source


# =========================================================================
# CLI Wiring — State Tracking
# =========================================================================

class TestStateArtifactTracking:
    """Verify tracking documents are recorded in state artifacts."""

    def test_fix_cycle_log_artifact_tracking(self):
        """CLI main function tracks fix_cycle_log artifact."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        assert "fix_cycle_log" in source

    def test_e2e_coverage_matrix_artifact_tracking(self):
        """CLI main function tracks e2e_coverage_matrix."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        assert "e2e_coverage_matrix" in source


# =========================================================================
# Cross-Feature Integration
# =========================================================================

class TestCrossFeatureIntegration:
    """Tests for cross-feature compatibility."""

    def test_tracking_documents_importable(self):
        """All public functions are importable."""
        from agent_team.tracking_documents import (
            generate_e2e_coverage_matrix,
            parse_e2e_coverage_matrix,
            initialize_fix_cycle_log,
            build_fix_cycle_entry,
            parse_fix_cycle_log,
            generate_milestone_handoff_entry,
            generate_consumption_checklist,
            parse_milestone_handoff,
            parse_handoff_interfaces,
            compute_wiring_completeness,
        )
        # All should be callable
        assert callable(generate_e2e_coverage_matrix)
        assert callable(parse_e2e_coverage_matrix)
        assert callable(initialize_fix_cycle_log)
        assert callable(build_fix_cycle_entry)
        assert callable(parse_fix_cycle_log)
        assert callable(generate_milestone_handoff_entry)
        assert callable(generate_consumption_checklist)
        assert callable(parse_milestone_handoff)
        assert callable(parse_handoff_interfaces)
        assert callable(compute_wiring_completeness)

    def test_dataclasses_importable(self):
        """All dataclasses are importable."""
        from agent_team.tracking_documents import (
            E2ECoverageStats,
            FixCycleStats,
            MilestoneHandoffEntry,
        )
        # Instantiate with defaults
        assert E2ECoverageStats().total_items == 0
        assert FixCycleStats().total_cycles == 0
        assert MilestoneHandoffEntry().milestone_id == ""

    def test_constants_importable(self):
        """All constants are importable."""
        from agent_team.tracking_documents import (
            FIX_CYCLE_LOG_INSTRUCTIONS,
            MILESTONE_HANDOFF_INSTRUCTIONS,
            E2E_COVERAGE_MATRIX_TEMPLATE,
        )
        assert len(FIX_CYCLE_LOG_INSTRUCTIONS) > 0
        assert len(MILESTONE_HANDOFF_INSTRUCTIONS) > 0
        assert len(E2E_COVERAGE_MATRIX_TEMPLATE) > 0

    def test_config_no_collision_with_e2e_testing(self):
        """TrackingDocumentsConfig doesn't interfere with E2ETestingConfig."""
        cfg = AgentTeamConfig()
        assert hasattr(cfg, "tracking_documents")
        assert hasattr(cfg, "e2e_testing")
        assert isinstance(cfg.tracking_documents, TrackingDocumentsConfig)
        from agent_team.config import E2ETestingConfig
        assert isinstance(cfg.e2e_testing, E2ETestingConfig)

    def test_config_no_collision_with_integrity_scans(self):
        """TrackingDocumentsConfig doesn't interfere with IntegrityScanConfig."""
        cfg = AgentTeamConfig()
        assert hasattr(cfg, "integrity_scans")
        from agent_team.config import IntegrityScanConfig
        assert isinstance(cfg.integrity_scans, IntegrityScanConfig)

    def test_backward_compatibility_no_config(self):
        """Project with no tracking_documents section uses defaults (all enabled)."""
        cfg, _ = _dict_to_config({})
        assert cfg.tracking_documents.e2e_coverage_matrix is True
        assert cfg.tracking_documents.fix_cycle_log is True
        assert cfg.tracking_documents.milestone_handoff is True

    def test_backward_compatibility_all_disabled(self):
        """All tracking disabled still works."""
        data = {
            "tracking_documents": {
                "e2e_coverage_matrix": False,
                "fix_cycle_log": False,
                "milestone_handoff": False,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.e2e_coverage_matrix is False
        assert cfg.tracking_documents.fix_cycle_log is False
        assert cfg.tracking_documents.milestone_handoff is False


# =========================================================================
# E2E Coverage Matrix — Round-trip (generate -> parse)
# =========================================================================

class TestE2ECoverageMatrixRoundTrip:
    """Test that generated matrix can be correctly parsed back."""

    def test_generate_then_parse_empty(self):
        """Generated matrix from no-endpoint reqs parses to 0 items."""
        reqs = "General description only."
        matrix = generate_e2e_coverage_matrix(reqs)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items == 0

    def test_generate_then_parse_with_endpoints(self):
        """Generated matrix from endpoints parses correctly."""
        reqs = textwrap.dedent("""\
            - [ ] REQ-001: POST /api/users
            - [ ] REQ-002: GET /api/users
            - [ ] REQ-003: DELETE /api/users/:id
        """)
        matrix = generate_e2e_coverage_matrix(reqs)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.total_items >= 3
        assert stats.tests_written == 0
        assert stats.coverage_ratio == 0.0

    def test_generate_then_mark_then_parse(self):
        """Marking checkboxes in generated matrix updates stats."""
        reqs = "- [ ] REQ-001: GET /api/health"
        matrix = generate_e2e_coverage_matrix(reqs)
        # Simulate agent marking test written and passed
        matrix = matrix.replace("| [ ] | [ ] |", "| [x] | [x] |", 1)
        stats = parse_e2e_coverage_matrix(matrix)
        assert stats.tests_written >= 1
        assert stats.tests_passed >= 1


# =========================================================================
# Fix Cycle Log — Round-trip (init -> build -> parse)
# =========================================================================

class TestFixCycleLogRoundTrip:
    """Test init -> build entries -> parse flow."""

    def test_full_round_trip(self, tmp_path):
        """Initialize, append entries, then parse."""
        req_dir = str(tmp_path / "reqs")
        log_path = initialize_fix_cycle_log(req_dir)

        # Build and append entries
        entry1 = build_fix_cycle_entry("E2E Backend", 1, ["test_login failed"])
        entry2 = build_fix_cycle_entry("E2E Backend", 2, ["test_register failed"], previous_cycles=1)
        entry3 = build_fix_cycle_entry("Mock Data", 1, ["mock in service"])

        content = log_path.read_text(encoding="utf-8")
        content += "\n" + entry1 + "\n" + entry2 + "\n" + entry3
        log_path.write_text(content, encoding="utf-8")

        stats = parse_fix_cycle_log(log_path.read_text(encoding="utf-8"))
        assert stats.total_cycles == 3
        assert stats.cycles_by_phase["E2E Backend"] == 2
        assert stats.cycles_by_phase["Mock Data"] == 1


# =========================================================================
# Milestone Handoff — Round-trip (generate -> parse -> checklist -> wiring)
# =========================================================================

class TestMilestoneHandoffRoundTrip:
    """Test full handoff generation -> parsing -> consumption checklist flow."""

    def test_generate_then_parse(self):
        """Generated entry can be parsed back."""
        entry = generate_milestone_handoff_entry("milestone-1", "Backend API")
        header = "# Milestone Handoff Registry\n\n---\n\n"
        content = header + entry
        entries = parse_milestone_handoff(content)
        assert len(entries) == 1
        assert entries[0].milestone_id == "milestone-1"
        assert entries[0].status == "COMPLETE"

    def test_full_flow_with_checklist(self):
        """Generate entries -> extract interfaces -> build checklist -> check wiring."""
        # Milestone 1 entry with filled interfaces
        content = textwrap.dedent("""\
            # Milestone Handoff Registry

            ---

            ## milestone-1: Backend \u2014 COMPLETE

            ### Exposed Interfaces
            | Endpoint | Method | Auth Required | Request Body | Response Shape |
            |----------|--------|:------------:|-------------|---------------|
            | /api/auth/login | POST | No | {email, pwd} | {token} |
            | /api/tenders | GET | Yes | | [{id, title}] |

            ### Database State After This Milestone
            Users, Tenders tables

            ---
        """)

        # Extract interfaces for milestone-1
        interfaces = parse_handoff_interfaces(content, "milestone-1")
        assert len(interfaces) == 2

        # Generate consumption checklist for milestone-2
        checklist = generate_consumption_checklist("milestone-2", "Frontend", interfaces)
        assert "milestone-1" in checklist
        assert "/api/auth/login" in checklist
        assert "/api/tenders" in checklist
        assert checklist.count("[ ]") == 2

        # Append checklist and verify wiring
        full_content = content + "\n\n" + checklist
        wired, total = compute_wiring_completeness(full_content, "milestone-2")
        assert wired == 0
        assert total == 2

        # Simulate marking one as wired
        full_content = full_content.replace("| [ ] |", "| [x] |", 1)
        wired, total = compute_wiring_completeness(full_content, "milestone-2")
        assert wired == 1
        assert total == 2


# =========================================================================
# Dataclass Defaults
# =========================================================================

class TestDataclassDefaults:
    """Test dataclass field defaults."""

    def test_e2e_coverage_stats_defaults(self):
        stats = E2ECoverageStats()
        assert stats.total_items == 0
        assert stats.tests_written == 0
        assert stats.tests_passed == 0
        assert stats.coverage_ratio == 0.0
        assert stats.pass_ratio == 0.0

    def test_fix_cycle_stats_defaults(self):
        stats = FixCycleStats()
        assert stats.total_cycles == 0
        assert stats.cycles_by_phase == {}
        assert stats.last_phase_resolved is False

    def test_milestone_handoff_entry_defaults(self):
        entry = MilestoneHandoffEntry()
        assert entry.milestone_id == ""
        assert entry.milestone_title == ""
        assert entry.status == ""
        assert entry.interfaces == []
        assert entry.wiring_complete == 0
        assert entry.wiring_total == 0

    def test_milestone_handoff_entry_list_isolation(self):
        """Each instance has its own interfaces list."""
        e1 = MilestoneHandoffEntry()
        e2 = MilestoneHandoffEntry()
        e1.interfaces.append({"endpoint": "/a"})
        assert len(e2.interfaces) == 0


# =========================================================================
# Wiring Verification — Execution Position
# =========================================================================

class TestExecutionPosition:
    """Verify correct execution order of tracking document operations."""

    def test_matrix_generation_before_e2e_tests(self):
        """E2E coverage matrix generation appears before _run_backend_e2e_tests call."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        # Find positions
        gen_pos = source.find("generate_e2e_coverage_matrix")
        backend_pos = source.find("_run_backend_e2e_tests")
        if gen_pos != -1 and backend_pos != -1:
            assert gen_pos < backend_pos, "Matrix generation must come before backend E2E tests"

    def test_coverage_parsing_after_e2e(self):
        """Coverage stats parsing appears after E2E test execution."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        parse_pos = source.find("parse_e2e_coverage_matrix")
        backend_pos = source.find("_run_backend_e2e_tests")
        if parse_pos != -1 and backend_pos != -1:
            assert parse_pos > backend_pos, "Coverage parsing must come after E2E tests"

    def test_handoff_generation_after_review_recovery(self):
        """Milestone handoff generation appears in _run_prd_milestones."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "generate_milestone_handoff_entry" in source

    def test_consumption_checklist_before_milestone_execution(self):
        """Consumption checklist generation appears before milestone prompt building."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        checklist_pos = source.find("generate_consumption_checklist")
        # The milestone prompt is built after the checklist
        prompt_pos = source.find("build_milestone_execution_prompt")
        if checklist_pos != -1 and prompt_pos != -1:
            assert checklist_pos < prompt_pos, "Checklist generation must come before milestone prompt"


# =========================================================================
# Wiring Verification — Config Gating
# =========================================================================

class TestConfigGating:
    """Verify all tracking document operations are properly gated by config."""

    def test_matrix_gated_by_config(self):
        """Matrix generation is gated by e2e_coverage_matrix config."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        # Find the guard check before matrix generation
        assert "tracking_documents.e2e_coverage_matrix" in source

    def test_fix_log_gated_by_config_in_mock_fix(self):
        """Fix log is gated by fix_cycle_log config in mock data fix."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_mock_data_fix)
        assert "tracking_documents.fix_cycle_log" in source

    def test_handoff_gated_by_config_in_milestones(self):
        """Handoff is gated by milestone_handoff config."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        assert "tracking_documents.milestone_handoff" in source


# =========================================================================
# Wiring Verification — Crash Isolation
# =========================================================================

class TestCrashIsolation:
    """Verify all tracking document operations are wrapped in try/except."""

    def test_matrix_generation_crash_isolated(self):
        """Matrix generation failure doesn't block E2E tests."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli.main)
        # Check that generate_e2e_coverage_matrix is within a try block
        gen_pos = source.find("generate_e2e_coverage_matrix")
        if gen_pos != -1:
            # Look backward for 'try:' within 500 chars
            preceding = source[max(0, gen_pos - 500):gen_pos]
            assert "try:" in preceding

    def test_fix_log_crash_isolated(self):
        """Fix log failure doesn't block fix execution."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_mock_data_fix)
        # Check except pattern around fix log
        assert "except Exception" in source

    def test_handoff_crash_isolated(self):
        """Handoff generation failure doesn't block milestone completion."""
        from agent_team import cli
        import inspect
        source = inspect.getsource(cli._run_prd_milestones)
        # Multiple try/except blocks for handoff
        assert source.count("except Exception") >= 2


# =========================================================================
# Backward Compatibility
# =========================================================================

class TestBackwardCompatibility:
    """Verify backward compatibility when tracking documents are disabled."""

    def test_disabled_config_still_loads(self):
        """Disabling all tracking documents doesn't break config loading."""
        data = {
            "tracking_documents": {
                "e2e_coverage_matrix": False,
                "fix_cycle_log": False,
                "milestone_handoff": False,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tracking_documents.e2e_coverage_matrix is False

    def test_existing_prompts_still_valid(self):
        """Existing prompt constants are not broken by injections."""
        from agent_team.e2e_testing import BACKEND_E2E_PROMPT, FRONTEND_E2E_PROMPT, E2E_FIX_PROMPT
        # All prompts should still have their core content
        assert "PHASE: E2E BACKEND API TESTING" in BACKEND_E2E_PROMPT
        assert "PHASE: E2E FRONTEND PLAYWRIGHT TESTING" in FRONTEND_E2E_PROMPT
        assert "PHASE: E2E TEST FIX" in E2E_FIX_PROMPT

    def test_existing_code_writer_prompt_intact(self):
        """CODE_WRITER_PROMPT core content is not broken."""
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT
        assert "TASKS.md" in CODE_WRITER_PROMPT
        assert "REQUIREMENTS.md" in CODE_WRITER_PROMPT

    def test_milestone_prompt_core_intact(self):
        """Milestone prompt still has core workflow steps."""
        from agent_team.agents import build_milestone_execution_prompt
        config = AgentTeamConfig()
        result = build_milestone_execution_prompt("task", "standard", config)
        assert "MILESTONE WORKFLOW" in result
        assert "TASK ASSIGNER" in result
