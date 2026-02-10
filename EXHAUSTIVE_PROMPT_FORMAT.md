# HOW TO USE THIS TEMPLATE
#
# This is a reusable prompt format for multi-agent implementation tasks executed via Claude Code.
# It guarantees: parallel execution, architecture-first discovery, exhaustive testing, and zero regressions.
#
# INSTRUCTIONS:
# 1. Copy this file and rename it to match your feature (e.g., TRACKING_DOCUMENTS_IMPLEMENTATION.md)
# 2. Replace ALL {PLACEHOLDER} values with your specific content
# 3. Delete all <!-- GUIDANCE: ... --> comments after filling in the sections
# 4. Delete this entire "HOW TO USE THIS TEMPLATE" header
# 5. Adjust the number of Phase 2 agents (2A/2B/2C) based on your task scope:
#    - 1 agent: Small feature, single file scope
#    - 2 agents: Medium feature, 2-3 file groups
#    - 3 agents: Large feature, 3+ disjoint file groups (recommended default)
#    - 4+ agents: Massive feature — only if truly independent file sets exist
# 6. The wave pattern is NON-NEGOTIABLE: architect reads first → impl agents parallel → test-engineer last
# 7. Every section below has a PURPOSE. Do not delete sections — fill them or mark N/A.
#
# SCALING GUIDE:
# - Simple bug fix: Skip this format entirely, use direct Claude Code
# - Single-file feature: Use 3 agents (architect + 1 impl + test-engineer)
# - Multi-file feature: Use 4-5 agents (architect + 2-3 impl + test-engineer)
# - Cross-system feature: Use 5-7 agents (architect + 3-4 impl + wiring-verifier + test-engineer)
#
# ═══════════════════════════════════════════════════════════════════════════════

---

# Agent-Team Exhaustive Implementation — {FEATURE_NAME}

<!-- GUIDANCE:
     {FEATURE_NAME}: Short, descriptive name (e.g., "Per-Phase Tracking Documents", "Role-Based Access Control",
     "Real-Time Notification System"). This becomes the title of the implementation task.
-->

## Agent Team Structure — Parallel Execution

You MUST execute this implementation using a coordinated agent team. Create a team and spawn
the following agents. Maximize parallelism where possible.

### Team Composition ({N} agents)

<!-- GUIDANCE:
     Minimum 3 agents: architect + 1 impl + test-engineer
     Maximum 7 agents: architect + 4 impl + wiring-verifier + test-engineer
     Each agent needs: a unique name, a type (agent type from Claude Code), a clear role description.
     The role description should state EXACTLY which files/modules the agent owns.

     Common agent types:
     - `superpowers:code-reviewer` for read-only/review agents (architect, wiring-verifier)
     - `general-purpose` for implementation agents (impl-*, test-engineer)
     - `feature-dev:code-architect` for architecture discovery (alternative to code-reviewer)

     CRITICAL: File ownership must be DISJOINT across impl agents. No two impl agents
     should edit the same file. If they must, one writes first and the other reads after.
-->

| Agent Name | Type | Role |
|------------|------|------|
| `architect` | `superpowers:code-reviewer` | Phase 1 — Read entire codebase, document integration patterns, produce ARCHITECTURE_REPORT.md |
| `impl-{scope_a}` | `general-purpose` | Phase 2A — {describe files this agent creates/edits} |
| `impl-{scope_b}` | `general-purpose` | Phase 2B — {describe files this agent creates/edits} |
| `impl-{scope_c}` | `general-purpose` | Phase 2C — {describe files this agent creates/edits} |
| `test-engineer` | `general-purpose` | Phase 3+4+5 — Write ALL tests, run pytest/jest, fix failures, iterate until green |

<!-- GUIDANCE:
     Optional additional agents:
     | `wiring-verifier` | `superpowers:code-reviewer` | Phase 4 — Verify execution order, config gating, crash isolation |

     Use wiring-verifier when:
     - Feature touches 3+ files in a pipeline (e.g., config → module → CLI wiring)
     - Feature has config flags that gate behavior
     - Feature integrates into an existing multi-step execution flow
-->

### Coordination Flow

<!-- GUIDANCE:
     This ASCII diagram shows the WAVE execution pattern. Waves are SEQUENTIAL.
     Agents within a wave are PARALLEL. This is the core orchestration pattern.

     Adjust the number of waves and agents per wave to match your team composition.
     The pattern is always: READ → IMPLEMENT (parallel) → TEST → REPORT
-->

```
Wave 1 (solo): architect reads entire codebase
    |
    Produces: .agent-team/ARCHITECTURE_REPORT.md
    |
Wave 2 (parallel): impl-{scope_a} ({files_a})
                  + impl-{scope_b} ({files_b})
                  + impl-{scope_c} ({files_c})
    |                   |                    |
    All read ARCHITECTURE_REPORT.md first
    |                   |                    |
    +---------+---------+--------------------+
              |
Wave 3 (solo): test-engineer writes ALL tests
              |
Wave 4 (solo): test-engineer runs full suite, fixes failures
              |
Wave 5: You (team lead) collect all results -> final report
```

### Agent Instructions

<!-- GUIDANCE:
     These instructions are UNIVERSAL. Keep them as-is for any task.
     Only modify the file assignments in the bullet points.
-->

- **You are team lead.** Create tasks in the task list for each agent. Assign via TaskUpdate.
- **architect runs first and alone.** Its ARCHITECTURE_REPORT.md is the blueprint for all implementation.
- **impl agents run simultaneously.** They work on different files:
  - impl-{scope_a}: {list exact file paths this agent owns}
  - impl-{scope_b}: {list exact file paths this agent owns}
  - impl-{scope_c}: {list exact file paths this agent owns}
- **test-engineer waits for ALL impl agents** before starting.
- **After the final wave completes,** shut down all agents. Collect results and write the final report yourself.

### Critical Rules for Agents

<!-- GUIDANCE:
     These rules enforce file ownership boundaries. They are CRITICAL for preventing
     merge conflicts and ensuring parallel agents don't step on each other.

     Adjust the file lists to match your actual agent assignments.
     The test-engineer exception (can edit ANY source file) is intentional —
     it allows fixing bugs discovered during testing.
-->

- architect: READ ONLY. Do not edit any source files. Produce ARCHITECTURE_REPORT.md only.
- impl-{scope_a}: Can create/edit {files_a}. Do NOT touch {files_b}, {files_c}.
- impl-{scope_b}: Can create/edit {files_b}. Do NOT touch {files_a}, {files_c}.
- impl-{scope_c}: Can create/edit {files_c}. Do NOT touch {files_a}, {files_b}.
- test-engineer: Can create/edit test files. Can edit ANY source file to fix bugs found during testing.
- If any agent finds a conflict or needs something from another agent's scope, send a message — don't wait.

---

# {FEATURE_NAME} — {ONE_LINE_DESCRIPTION}

<!-- GUIDANCE:
     {ONE_LINE_DESCRIPTION}: A subtitle explaining what this feature achieves.
     Example: "Guaranteed Agent Progress Visibility"
     Example: "Fine-Grained Permission Enforcement"
-->

## Background — Why This Exists

<!-- GUIDANCE:
     This section is the MOST IMPORTANT part of the entire prompt. It answers "why bother?"
     and gives agents deep context about the problem space.

     Structure: One paragraph of context, then 2-5 numbered failure modes.
     Each failure mode must have:
     1. A short title (e.g., "Superficial E2E Testing")
     2. A 4-8 sentence description of HOW the failure manifests
     3. A concrete example from real usage (project name, specific numbers, dollar costs)
     4. WHY existing checks don't catch it

     The failure modes directly map to the deliverables in "What We're Building".
     Every deliverable should fix exactly one failure mode.

     BAD failure mode: "The system could be better" (vague, no specifics)
     GOOD failure mode: "The E2E agent writes 5 tests for a project with 20 endpoints because
     there is no checklist forcing completeness. The remaining 15 endpoints are never tested."
-->

{Context paragraph: What the system does today, what the gap is, why it matters.}

### Failure {N}: {FAILURE_TITLE}

{4-8 sentences describing the failure. Be SPECIFIC: what happens, what the symptoms are,
what the cost is (time, money, quality), and why no existing mechanism catches it.
Include a concrete example if possible.}

<!-- Repeat for each failure mode. Typically 2-5 failure modes. -->

## What We're Building

<!-- GUIDANCE:
     One paragraph per deliverable. Each paragraph must state:
     1. The deliverable name (e.g., "Document 1: E2E_COVERAGE_MATRIX.md")
     2. When it's generated (which phase, which trigger)
     3. What it contains (high-level structure)
     4. How agents interact with it (generate → mark → read pattern)
     5. What gate/enforcement mechanism exists

     The number of deliverables should match the number of failure modes above.
-->

**Deliverable 1: {NAME}** ({WHICH_PHASE})
{One paragraph describing what it is, when it's generated, who reads it, what enforcement exists.}

**Deliverable 2: {NAME}** ({WHICH_PHASE})
{One paragraph describing what it is, when it's generated, who reads it, what enforcement exists.}

<!-- Repeat for each deliverable. -->

---

## PHASE 1: ARCHITECTURE DISCOVERY (architect)

<!-- GUIDANCE:
     Phase 1 is ALWAYS read-only. The architect reads the entire codebase and produces
     a structured report documenting every integration point, pattern, and insertion location
     that the implementation agents will need.

     Structure this as lettered subsections (1A, 1B, ..., 1N).
     Each subsection targets a SPECIFIC file or concept and lists EXACTLY what to find.

     GOOD subsection: "Read src/config.py — Document the E2ETestingConfig dataclass (line 307):
     field names, types, defaults. Document _dict_to_config() YAML loading pattern (lines 899-930)."

     BAD subsection: "Look at the config file and understand it." (too vague)

     Typical subsections:
     - 1A: Existing patterns similar to what we're building (for consistency)
     - 1B: The main module we're extending (function signatures, call sites)
     - 1C: The execution flow where our feature integrates (line-by-line order)
     - 1D: Config/state patterns we must follow
     - 1E: Prompt injection points (if modifying agent prompts)
     - 1F: Test patterns and conventions
     - 1G+: Any additional areas specific to the feature

     Line numbers are APPROXIMATE. Always tell the architect to verify in actual source.
-->

Before implementing ANYTHING, the architect must read the codebase and produce `.agent-team/ARCHITECTURE_REPORT.md` answering these questions:

### 1A: {AREA_NAME}

<!-- GUIDANCE:
     Each sub-section should:
     1. Name the exact file(s) to read
     2. Name the exact function(s)/class(es) to find
     3. List what information to extract (field names, signatures, patterns, line numbers)
     4. Explain WHY this information is needed (which implementation phase uses it)
-->

- Read `{file_path}` end to end ({approx_lines} lines)
- Document {function/class name} ({approximate line}):
  - {What to extract: field names, types, defaults, return types, etc.}
  - {Why: "This pattern will be replicated for our new {X}"}
- {Additional items to find in this file}

### 1B: {AREA_NAME}

- Read `{file_path}` — find {function_name} ({approximate line}):
  - Document {specific detail}
  - Document {specific detail}
  - Identify EXACT insertion points for {our new code}

<!-- Continue with 1C, 1D, ..., 1N as needed -->

### Output

Write `.agent-team/ARCHITECTURE_REPORT.md` with all findings, organized by section (1A through 1{N}), with exact file paths, line numbers, function names, and integration points. This is the blueprint for Phase 2.

---

## PHASE 2A: {SCOPE_A_TITLE} (impl-{scope_a})

<!-- GUIDANCE:
     Phase 2 agents run IN PARALLEL. Each Phase 2 section describes ONE agent's work.

     Every Phase 2 section MUST start with:
     "Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented."

     Structure for each Phase 2 section:
     1. List of files to create/modify
     2. For NEW files: full module structure with function signatures, docstrings, and code snippets
     3. For MODIFIED files: exact location of changes, before/after patterns, code to add
     4. For config: dataclass definition, YAML section, validation rules, loader code

     Code snippets should be COMPLETE enough that the agent doesn't need to guess.
     Include function signatures with types, return types, and brief docstrings.
     Include the actual regex patterns, template strings, or data structures.

     DO NOT include implementation details that should be discovered by reading the codebase.
     Instead, reference the ARCHITECTURE_REPORT.md section: "Follow the pattern documented in 1D."
-->

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### New File: `{path/to/new_module.py}`

<!-- GUIDANCE: For new files, describe the module's purpose, then list every function/class/constant. -->

{Description of what this module contains and its responsibility boundary.}

#### {Component 1 Name}

**Function: `{function_name}()`**

```python
def function_name(
    param1: type,
    param2: type = default,
) -> ReturnType:
    """One-line docstring."""
```

How it works:
1. {Step 1}
2. {Step 2}
3. {Step N}

<!-- Repeat for each function/class/constant in the new file -->

#### Dataclasses

<!-- GUIDANCE: If the new module introduces dataclasses, define them fully here. -->

```python
@dataclass
class {ClassName}:
    field1: type = default
    field2: type = default
```

### Modifications to: `{path/to/existing_file.py}`

<!-- GUIDANCE:
     For existing file modifications:
     1. State the exact location (function name + approximate line)
     2. Show the code to ADD (not the entire function)
     3. Reference the pattern from ARCHITECTURE_REPORT.md
     4. State what comes BEFORE and AFTER the insertion point
-->

**Add to `{ExistingClass}` / `{existing_function()}`:**

```python
# {Description of what this code does}
{code_to_add}
```

**Add to `{loader_function()}`:**

```python
# {Description of YAML loading pattern — follow existing pattern from 1D}
{config_loading_code}
```

### Config YAML Section

<!-- GUIDANCE: Show the YAML that users would add to their config file. -->

```yaml
{feature_name}:
  field1: default_value      # Description
  field2: default_value      # Description
```

---

## PHASE 2B: {SCOPE_B_TITLE} (impl-{scope_b})

<!-- GUIDANCE: Same structure as Phase 2A but for a different file set. -->

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### {Modification/Injection 1}: {Description}

**Target: `{file_path}`, {function/constant name}** ({approximate line})

{Description of WHERE to inject and WHY}

Add {BEFORE/AFTER} the existing {anchor text or instruction}:

```
{The text or code to inject}
```

<!-- Repeat for each injection/modification -->

---

## PHASE 2C: {SCOPE_C_TITLE} (impl-{scope_c})

<!-- GUIDANCE: Same structure. This is typically the "wiring" agent that connects
     the new module (2A) and prompt changes (2B) to the main execution flow (CLI, main loop, etc.) -->

Read ARCHITECTURE_REPORT.md first. Follow every pattern EXACTLY as documented.

### Wiring 1: {Description}

**In `{file_path}`, inside {function_name} (around line {N}):**

{Description of what to add and where}

```python
# {Description}
{wiring_code}
```

<!-- GUIDANCE:
     For wiring, be explicit about:
     1. Config flag that gates this code
     2. Try/except wrapping pattern (crash isolation)
     3. What happens on success vs failure
     4. What state is updated after execution
     5. Recovery type string added on violation (if applicable)
-->

<!-- Repeat for each wiring point -->

---

## PHASE 3: WRITE EXHAUSTIVE TESTS (test-engineer)

<!-- GUIDANCE:
     This is the largest section. Structure tests by CATEGORY, not by file.

     Typical categories (include ALL that apply):
     1. Generation/Creation tests — new functions produce correct output
     2. Parsing tests — parsers handle valid, partial, and malformed input
     3. Edge case tests — empty input, Unicode, very large input, special characters
     4. Config tests — defaults, YAML loading, validation, partial config
     5. Prompt injection tests — key phrases present in modified prompts
     6. CLI wiring tests — code runs at correct position, gated by config, crash-isolated
     7. Cross-feature integration tests — imports work, no collisions, no regressions
     8. Backward compatibility tests — feature disabled produces identical behavior to before

     For EACH test, write a one-line description of:
     - Input condition → Expected output/behavior

     GOOD: "Parse matrix with half items checked → coverage 50%"
     BAD: "Test parsing" (too vague)

     Target: 50-200 tests depending on feature complexity.
     Rule of thumb: 10-20 tests per function/component.
-->

After Phase 2A, 2B, and 2C are complete, write tests covering:

### {Category 1} Tests (`tests/{test_file_name}.py`)

**{Sub-category} tests:**
- {Input condition} → {expected output/behavior}
- {Input condition} → {expected output/behavior}
- {Input condition} → {expected output/behavior}

**{Sub-category} tests:**
- {Input condition} → {expected output/behavior}
- {Input condition} → {expected output/behavior}

**Edge cases:**
- {Edge case} → {expected behavior}
- {Edge case} → {expected behavior}

### {Category 2} Tests

<!-- Continue with all test categories -->

### Config Tests

- {Config class} has correct defaults ({list default values})
- Config loads from YAML correctly
- Config validates {field} in range [{min}, {max}]
- Invalid {field} value raises ValueError
- Unknown YAML keys don't break parsing
- Partial YAML (only some fields) → defaults for missing

### Prompt Injection Tests

<!-- GUIDANCE: For each prompt modified in Phase 2B, verify key phrases are present. -->

- {PROMPT_CONSTANT} contains "{key_phrase}"
- {PROMPT_CONSTANT} contains "{key_phrase}"
- {function_name}() output contains {expected_text} when config enabled
- {function_name}() output does NOT contain {expected_text} when config disabled

### CLI Wiring Tests

<!-- GUIDANCE: For each wiring point in Phase 2C, verify execution position, config gating,
     and crash isolation. -->

- {feature} executed {BEFORE/AFTER} {anchor_step} when config enabled
- {feature} NOT executed when config disabled
- {feature} failure doesn't block {main_flow} (crash isolation)
- {state_field} updated after {feature} completes

### Cross-Feature Integration Tests

- New config dataclass doesn't collide with existing configs
- {new_module}.py imports correctly from {dependency1} and {dependency2}
- All new functions are importable
- New prompt injections don't break existing prompt structure
- Existing tests still pass (zero regressions)

---

## PHASE 4: WIRING VERIFICATION

<!-- GUIDANCE:
     Phase 4 verifies that the implementation is correctly integrated.
     This can be done by the test-engineer (default) or a dedicated wiring-verifier agent.

     4 verification areas are ALWAYS relevant:
     A. Execution Position — code runs at the right place in the pipeline
     B. Config Gating — feature is properly enabled/disabled by config flags
     C. Crash Isolation — failures in new code don't break existing flows
     D. Backward Compatibility — projects without the new config work identically

     Add a 5th section (4E) if the feature has inter-component dependencies.
-->

### 4A: Execution Position
- {new_code_1} executes {BEFORE/AFTER} {existing_step_1}
- {new_code_2} executes {BEFORE/AFTER} {existing_step_2}
- {new_code_N} executes at the correct position in the pipeline

### 4B: Config Gating
- `{config.feature.flag_1}: false` → {behavior when disabled}
- `{config.feature.flag_2}: false` → {behavior when disabled}
- All config flags independently testable

### 4C: Crash Isolation
- {new_code_1} failure doesn't block {main_flow}
- {new_code_2} failure doesn't block {main_flow}
- Each new integration point wrapped in its own try/except
- Error messages are logged (not silently swallowed)

### 4D: Backward Compatibility
- Projects without {feature} config section → defaults apply
- Projects that disable all {feature} flags → everything works as before
- Existing behavior unchanged when {feature} enabled (additive only)
- No new required fields that would break existing configs

---

## PHASE 5: RUN ALL TESTS AND FIX FAILURES

<!-- GUIDANCE:
     This section is nearly IDENTICAL for every task. Only change:
     - The test command (pytest, jest, cargo test, etc.)
     - The known pre-existing failure count
     - The test output flags
-->

```bash
{test_command} {test_directory} -v --tb=short 2>&1
```

- ALL new tests must pass
- ALL existing tests must pass (except {N} pre-existing known failures — {describe})
- Zero new regressions
- If any test fails, diagnose the root cause, fix the CODE not the test (unless the test expectation is provably wrong), and re-run
- Iterate until fully green

---

## PHASE 6: FINAL REPORT

<!-- GUIDANCE:
     This report template is produced by the team lead (you) after all agents complete.
     Customize the tables and sections to match your specific deliverables.
     The structure is: Summary → Deliverable Coverage → Test Results → Wiring Verification → Verdict
-->

After all phases complete, produce:

```markdown
# {FEATURE_NAME} — Implementation Report

## Implementation Summary
- New module: {path} ({N} functions, {M} constants)
- Config: {ConfigClass} ({N} fields)
- {Prompt/wiring changes summary}
- {Additional changes summary}

## Deliverable Coverage
| Deliverable | Generated By | Consumed By | Config Gate |
|-------------|-------------|------------|-------------|
| {deliverable_1} | {who generates} | {who reads} | {config.flag} |
| {deliverable_2} | {who generates} | {who reads} | {config.flag} |

## Test Results
- New tests written: {X}
- All passing: {X}/{X}
- Regressions: 0

## Wiring Verification
- Execution position: VERIFIED / ISSUES
- Config gating: VERIFIED / ISSUES
- Crash isolation: VERIFIED / ISSUES
- Backward compatibility: VERIFIED / ISSUES

## Failure Pattern Coverage
| Original Failure | Fixed By | Method |
|-----------------|----------|--------|
| {failure_1} | {deliverable_1} | {one-line description of fix approach} |
| {failure_2} | {deliverable_2} | {one-line description of fix approach} |

## Verdict
SHIP IT / NEEDS FIXES / CRITICAL ISSUES
```

---

## Execution Rules

<!-- GUIDANCE:
     These rules are UNIVERSAL. Keep them verbatim for any task.
     Only modify rules that reference specific technologies (e.g., "cli.py has 3800+ lines").

     Rules 1-6 are about process discipline.
     Rules 7-8 are about safety and compatibility.
     Rules 9-11 are about pragmatism and quality.

     Add project-specific rules at the end if needed (rule 12+).
-->

1. **ARCHITECTURE FIRST** — architect MUST finish before anyone implements anything. The ARCHITECTURE_REPORT.md is the single source of truth for integration points, patterns, and insertion locations.

2. **FOLLOW EXISTING PATTERNS** — Every function, config field, prompt section, and test must follow the exact patterns already in the codebase. Consistency over creativity. If the codebase uses dataclasses, use dataclasses. If it uses Pydantic, use Pydantic. If tests use pytest fixtures, use pytest fixtures.

3. **READ BEFORE YOU WRITE** — Read every file before modifying it. Understand the context around your insertion point. Never modify a file you haven't read in the current session.

4. **FIX THE APP NOT THE TEST** — When a test fails, fix the source code unless the test expectation is provably wrong. Tests are the specification; source code is the implementation.

5. **NO SHORTCUTS** — All deliverables must be fully implemented with generation, parsing, integration, and testing. A half-implemented feature is worse than no feature.

6. **VERIFY IN SOURCE** — Do not trust this prompt for exact line numbers. Read the actual codebase. Line numbers are approximate and may have shifted since this prompt was written.

7. **CRASH ISOLATION** — Every new integration point must be wrapped in its own try/except (or equivalent error boundary). New feature failures must NEVER block the main execution flow. These are enhancements, not gates (unless explicitly specified as gates).

8. **BACKWARD COMPATIBLE** — A project with no config section for the new feature must work exactly as before. Defaults should be sensible (typically all-enabled). Failure to generate/parse a new artifact silently degrades to no artifact (not a crash).

9. **BEST-EFFORT EXTRACTION** — If the feature involves parsing or extracting data from existing artifacts, the extraction will not be perfect. That's OK. The outputs serve as STARTING POINTS that agents/users refine. 80% auto-extraction is vastly better than 0%.

10. **OPTIMIZE IF YOU SEE IT** — If while reading the codebase you find opportunities to harden beyond what this prompt describes, DO IT. Document what you added and why in the final report.

11. **RUN TESTS AFTER EACH PHASE** — Don't wait until the end to discover failures. Each impl agent should run relevant tests before declaring done. The test-engineer runs the FULL suite.

<!-- GUIDANCE:
     Add project-specific rules here if needed:
     12. **{RULE_NAME}** — {Description}
-->
