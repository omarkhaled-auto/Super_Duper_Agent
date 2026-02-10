# Tracking Documents Follow-Up — Add Enum/Status Values to MILESTONE_HANDOFF.md

## Context

The tracking documents implementation (v4.0) is complete. 130 tests passing, 3076 total, 0 regressions.
This follow-up adds one critical subsection to the MILESTONE_HANDOFF.md template that was identified
during the Database Integrity Upgrades design phase.

## Problem

The MILESTONE_HANDOFF.md template currently documents:
1. Exposed Interfaces (endpoints)
2. Database State (tables/columns)
3. Environment Variables
4. Files Created/Modified
5. Known Limitations

What's MISSING: **Enum/Status Values**. When Milestone 1 creates an entity with
`status: "Opened" | "Closed" | "Cancelled"`, Milestone 3's frontend agent doesn't know the exact
values and invents `"cancelled"` (lowercase) instead of `"Cancelled"` (PascalCase). The handoff
captures the column exists but NOT its valid values.

This was Bayan Failure #4: Frontend sent `updateTenderStatus('cancelled')`, backend enum had
`'Closed'` not `'Cancelled'`. The tender disappeared from every list view. No error anywhere.

## Scope — 4 Changes, 1 File Each

This is a SMALL follow-up. Do NOT use a team. Execute directly.

| # | File | Change |
|---|------|--------|
| 1 | `src/agent_team/tracking_documents.py` | Add "Enum/Status Values" subsection to handoff template + update parsing |
| 2 | `src/agent_team/tracking_documents.py` | Update `MILESTONE_HANDOFF_INSTRUCTIONS` to mention enum documentation |
| 3 | `src/agent_team/cli.py` | Update `HANDOFF_GENERATION_PROMPT` to scan for enums |
| 4 | `tests/test_tracking_documents.py` | Add tests for the new subsection |

---

## Change 1: Add Enum/Status Values Subsection to Handoff Template

**File:** `src/agent_team/tracking_documents.py`
**Function:** `generate_milestone_handoff_entry()` (line 696)

The function currently builds a markdown string with 5 subsections. Add a 6th subsection
between "Database State After This Milestone" and "Environment Variables".

**Current template at approximately line 720 (find the exact line by reading the function):**

```markdown
### Database State After This Milestone
<!-- Agent: List all tables/collections created or modified, with column names and types -->

### Environment Variables
```

**Change to:**

```markdown
### Database State After This Milestone
<!-- Agent: List all tables/collections created or modified, with column names and types -->

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
<!-- Agent: For EVERY entity with a status/type/enum field, list ALL valid values -->
<!-- Include the exact string used in DB, the exact string in API responses, and valid state transitions -->

### Environment Variables
```

**Why this specific table format:**
- `Entity`: Which model/class this enum belongs to (e.g., `Tender`, `Bid`, `User`)
- `Field`: The property name (e.g., `Status`, `Role`, `BidType`)
- `Valid Values`: Complete comma-separated list (e.g., `Draft, Active, Closed`)
- `DB Type`: How it's stored (e.g., `string`, `int`, `varchar(50)`)
- `API String`: Exact JSON representation (e.g., `"draft"`, `"active"`, `"closed"`)

This gives subsequent milestones the EXACT values to use — no guessing.

---

## Change 2: Update MILESTONE_HANDOFF_INSTRUCTIONS

**File:** `src/agent_team/tracking_documents.py`
**Constant:** `MILESTONE_HANDOFF_INSTRUCTIONS` (line 109)

**Current text (find line "Database state (tables/columns created)"):**

```
5. Update MILESTONE_HANDOFF.md — add YOUR milestone's section with:
   - Every endpoint you created/modified (with exact path, method, auth, request/response shapes)
   - Database state (tables/columns created)
   - Environment variables introduced
   - Known limitations for future milestones
```

**Change to:**

```
5. Update MILESTONE_HANDOFF.md — add YOUR milestone's section with:
   - Every endpoint you created/modified (with exact path, method, auth, request/response shapes)
   - Database state (tables/columns created)
   - Enum/status values: for EVERY entity with a status/type/enum field, list ALL valid values,
     the DB storage type, and the exact API string representation
   - Environment variables introduced
   - Known limitations for future milestones
```

**Also update the "BEFORE writing ANY code" section** (find the line "Study the Exposed Interfaces tables"):

**Current:**
```
2. Study the "Exposed Interfaces" tables from ALL predecessor milestones
3. Use EXACT endpoint paths, methods, request bodies, and response shapes from the handoff
```

**Change to:**
```
2. Study the "Exposed Interfaces" and "Enum/Status Values" tables from ALL predecessor milestones
3. Use EXACT endpoint paths, methods, request bodies, response shapes, AND status/enum values from the handoff
```

---

## Change 3: Update HANDOFF_GENERATION_PROMPT

**File:** `src/agent_team/cli.py`
**Constant:** `HANDOFF_GENERATION_PROMPT` (line ~1782)

**Find the STEP 2 section that says "Scan the codebase for":**

**Current:**
```
STEP 2: Scan the codebase for:
- API endpoints (route files, controllers): extract path, method, auth, request/response shapes
- Database schema (migrations, models): extract table names, column names, types
- Environment variables (configs, .env): extract variable names and purposes
```

**Change to:**
```
STEP 2: Scan the codebase for:
- API endpoints (route files, controllers): extract path, method, auth, request/response shapes
- Database schema (migrations, models): extract table names, column names, types
- Enum/status values: for EVERY entity with a status/type/enum field, extract ALL valid values,
  the DB storage type (string vs int), and the exact string used in API responses
- Environment variables (configs, .env): extract variable names and purposes
```

**Find the STEP 3 section that says "fill in ALL tables":**

**Current (approximately):**
```
STEP 3: Update {requirements_dir}/MILESTONE_HANDOFF.md — find the section for {milestone_id}
and fill in ALL tables:
- Exposed Interfaces table: EVERY endpoint with exact path, method, auth, request body schema,
  response schema (include field names AND types)
- Database State: ALL tables with columns and types
- Environment Variables: ALL env vars with descriptions
- Known Limitations: Anything not yet implemented
```

**Change to:**
```
STEP 3: Update {requirements_dir}/MILESTONE_HANDOFF.md — find the section for {milestone_id}
and fill in ALL tables:
- Exposed Interfaces table: EVERY endpoint with exact path, method, auth, request body schema,
  response schema (include field names AND types)
- Database State: ALL tables with columns and types
- Enum/Status Values table: EVERY entity with enum/status fields — list ALL valid values,
  DB type, and exact API string. This is CRITICAL for preventing cross-milestone mismatches.
- Environment Variables: ALL env vars with descriptions
- Known Limitations: Anything not yet implemented
```

---

## Change 4: Add Tests

**File:** `tests/test_tracking_documents.py`

Add a new test class for the enum/status values subsection:

```python
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
```

Also update any existing tests that assert the exact number of sections or the exact content
of the handoff entry — search for tests that check the handoff template structure.

**Tests that may need updating (search for these patterns):**
- Tests that count `###` subsections in the handoff entry (now 6, was 5)
- Tests that assert `"### Environment Variables"` follows immediately after `"### Database State"`
- Tests that check the exact markdown output of `generate_milestone_handoff_entry()`

---

## Run Tests

```bash
pytest tests/test_tracking_documents.py -v --tb=short 2>&1
```

Then:

```bash
pytest tests/ -v --tb=short 2>&1
```

- ALL tests must pass
- Zero regressions
- If any existing test fails due to the new subsection, update the test expectation (this is one
  of the rare cases where updating the test is correct — we intentionally changed the template)

---

## Verification

After all changes, verify:
1. `generate_milestone_handoff_entry()` output contains 6 subsections (was 5)
2. `MILESTONE_HANDOFF_INSTRUCTIONS` mentions "Enum/status values"
3. `HANDOFF_GENERATION_PROMPT` mentions enum scanning in both STEP 2 and STEP 3
4. All 130 existing tracking document tests still pass (update any that fail due to template change)
5. New enum tests pass
