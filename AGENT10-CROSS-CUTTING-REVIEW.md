# Agent 10: Cross-Cutting End-to-End Wiring Review

**Reviewer:** Agent 10 of 10 (Integration Review)
**Scope:** All 3 features (Interactive Interview, COMPLEX Scope Auto-Detection, PRD Mode)
**Date:** 2026-02-01
**Files Reviewed:**
- `src/agent_team/cli.py` (512 lines)
- `src/agent_team/interviewer.py` (543 lines)
- `src/agent_team/agents.py` (810 lines)
- `src/agent_team/config.py` (248 lines)
- `src/agent_team/display.py` (293 lines)
- `src/agent_team/__init__.py` (7 lines)
- `src/agent_team/mcp_servers.py` (76 lines)

---

## PATH 1: Interactive Interview -> Orchestrator

**Scenario:** `agent-team "build an app"` (no `--no-interview`, no `--interview-doc`)

### Trace with Line Numbers

| Step | Module | Line(s) | Action | Hand-off |
|------|--------|---------|--------|----------|
| 1 | cli.py | 386-388 | `main()` -> `_parse_args()`, args.task="build an app" | - |
| 2 | cli.py | 404 | `load_config()` | -> config.py:216 |
| 3 | cli.py | 407-410 | Resolve cwd, print banner | -> display.py:38 |
| 4 | cli.py | 434-444 | Interview decision: `interview_doc=None`, `prd=None`, `no_interview=False`, `config.interview.enabled=True` -> enters interview branch | - |
| 5 | cli.py | 447-451 | `asyncio.run(run_interview(config, cwd, initial_task=args.task))` | -> interviewer.py:386 |
| 6 | interviewer.py | 397 | `print_interview_start(initial_task)` | -> display.py:233 |
| 7 | interviewer.py | 399 | `_build_interview_options(config, cwd)` | internal:361 |
| 8 | interviewer.py | 404-407 | Set up `.agent-team/INTERVIEW.md` path | - |
| 9 | interviewer.py | 410-427 | Build opening message with initial_task seed | - |
| 10 | interviewer.py | 430-513 | Multi-turn conversation loop (ClaudeSDKClient) | - |
| 11 | interviewer.py | 449 | `print_interview_prompt()` for user input | -> display.py:251 |
| 12 | interviewer.py | 455-477 | Exit phrase detection -> finalization | internal:334 |
| 13 | interviewer.py | 522-525 | Read final doc from disk | - |
| 14 | interviewer.py | 532 | `_detect_scope(doc_content)` -> "SIMPLE", "MEDIUM", or "COMPLEX" | internal:350 |
| 15 | interviewer.py | 534 | `print_interview_end(exchange_count, scope, doc_path)` | -> display.py:260 |
| 16 | interviewer.py | 536-542 | Return `InterviewResult(doc_content, doc_path, scope, exchange_count, cost)` | -> cli.py:447 |
| 17 | cli.py | 452-453 | `interview_doc = result.doc_content`, `interview_scope = result.scope` | - |
| 18 | cli.py | 476-479 | Mode decision: `has_interview=True`, args.task exists -> `interactive=False` | - |
| 19 | cli.py | 482-484 | Depth override: if `interview_scope=="COMPLEX"` -> `depth_override="exhaustive"` | - |
| 20 | cli.py | 497-500 | `task="build an app"`, `depth=depth_override or detect_depth(task, config)` | -> config.py:119 |
| 21 | cli.py | 503-511 | `_run_single(task, config, cwd, depth, agent_count, prd_path=None, interview_doc)` | internal:244 |
| 22 | cli.py | 262-270 | `build_orchestrator_prompt(task, depth, config, ..., interview_doc)` | -> agents.py:739 |
| 23 | agents.py | 749 | `get_agent_counts(depth)` | -> config.py:130 |
| 24 | agents.py | 782-789 | Interview document injected: `[INTERVIEW DOCUMENT]`, `---BEGIN/END---` | - |
| 25 | agents.py | 809 | Returns assembled prompt string | -> cli.py:262 |
| 26 | cli.py | 274-276 | `client.query(prompt)`, `_process_response(...)` | - |

### Boundary Verification

- **cli.py -> interviewer.py** (step 5): `run_interview(config: AgentTeamConfig, cwd: str | None, initial_task: str | None)` -- types match, all parameters correctly forwarded.
- **interviewer.py -> display.py** (steps 6, 11, 15): `print_interview_start(str | None)`, `print_interview_prompt() -> str`, `print_interview_end(int, str, str)` -- all signatures match.
- **interviewer.py -> cli.py** (step 16): Returns `InterviewResult` dataclass -- `.doc_content`, `.scope`, `.exchange_count`, `.cost` all correctly accessed at lines 452-453.
- **cli.py -> agents.py** (step 22): `build_orchestrator_prompt(task: str, depth: str, config: AgentTeamConfig, prd_path: str | None, agent_count: int | None, cwd: str | None, interview_doc: str | None)` -- all types match.
- **agents.py -> config.py** (step 23): `get_agent_counts(depth: str) -> dict[str, tuple[int, int]]` -- correctly invoked.

### Verdict: PASS

All hand-offs are correct. Types are consistent. Parameters are forwarded properly. The interview document flows from interviewer.py -> cli.py -> agents.py -> orchestrator prompt without data loss.

---

## PATH 2: COMPLEX Scope -> Exhaustive Depth

**Scenario:** Interview produces document with `Scope: COMPLEX`

### Trace with Line Numbers

| Step | Module | Line(s) | Action | Value |
|------|--------|---------|--------|-------|
| 1 | interviewer.py | 69-306 | INTERVIEWER_SYSTEM_PROMPT instructs AI about scope detection (lines 122-144) and document formats (lines 148-272) | Prompt contains SIMPLE/MEDIUM/COMPLEX templates |
| 2 | interviewer.py | 457-463 | Finalization instruction: "Make sure the Scope: header is present (SIMPLE, MEDIUM, or COMPLEX)" | AI writes doc with Scope: COMPLEX |
| 3 | interviewer.py | 350-358 | `_detect_scope(doc_content)`: iterates lines, finds `scope:` prefix, extracts value | Returns `"COMPLEX"` |
| 4 | interviewer.py | 536-542 | `InterviewResult(scope="COMPLEX", ...)` returned | - |
| 5 | cli.py | 453 | `interview_scope = result.scope` | `interview_scope = "COMPLEX"` |
| 6 | cli.py | 460-464 | Info message printed about COMPLEX scope / exhaustive depth / PRD mode | User informed |
| 7 | cli.py | 482-484 | `depth_override = args.depth` (None); `interview_scope == "COMPLEX"` -> `depth_override = "exhaustive"` | `depth_override = "exhaustive"` |
| 8 | cli.py | 500 | `depth = depth_override or detect_depth(task, config)` -> `depth = "exhaustive"` | `depth = "exhaustive"` |
| 9 | agents.py | 749 | `get_agent_counts("exhaustive")` | -> config.py:130 |
| 10 | config.py | 112-115 | `DEPTH_AGENT_COUNTS["exhaustive"]` returned | planning:(8,10), research:(5,8), architecture:(3,4), coding:(5,10), review:(5,8), testing:(3,5) |
| 11 | agents.py | 764 | `[DEPTH: EXHAUSTIVE]` added to prompt | Maximum fleet sizes |
| 12 | agents.py | 777-779 | Fleet scaling lines: "planning: 8-10 agents", etc. | Orchestrator receives max counts |

### Chain Verification

```
Interview doc "Scope: COMPLEX"
    -> _detect_scope() returns "COMPLEX"          [interviewer.py:350-358]
    -> InterviewResult.scope = "COMPLEX"           [interviewer.py:536]
    -> cli.py interview_scope = "COMPLEX"          [cli.py:453]
    -> depth_override = "exhaustive"               [cli.py:483-484]
    -> build_orchestrator_prompt depth="exhaustive" [cli.py:500 -> agents.py:739]
    -> get_agent_counts("exhaustive")              [agents.py:749 -> config.py:130]
    -> Maximum agent counts in prompt              [agents.py:777-779]
```

### Additional Note

The orchestrator system prompt (agents.py line 316-319) also contains:
```
If scope is COMPLEX, this may be a full PRD -- activate PRD mode
```
This provides redundancy: even if the depth override somehow failed, the orchestrator itself can detect COMPLEX scope from the interview document content and adjust its behavior.

### Verdict: PASS

The COMPLEX scope to exhaustive depth chain is correctly wired across all modules. Every hand-off preserves the scope information, and the depth override is applied before reaching the orchestrator.

---

## PATH 3: PRD Mode -> Full Application Build

**Scenario:** `agent-team --prd requirements.md`

### Trace with Line Numbers

| Step | Module | Line(s) | Action | Value |
|------|--------|---------|--------|-------|
| 1 | cli.py | 388 | `_parse_args()`: `args.prd="requirements.md"`, `args.task=None` | - |
| 2 | cli.py | 413-415 | Validate PRD file exists | OK if file exists |
| 3 | cli.py | 438-440 | `args.prd` is set -> `print_interview_skip("PRD file provided (--prd)")` | Interview SKIPPED |
| 4 | cli.py | 431-432 | `interview_doc = None`, `interview_scope = None` | No interview context |
| 5 | cli.py | 476-479 | `has_interview=False`, `interactive = False` (args.prd is not None) | Single-shot mode |
| 6 | cli.py | 482-484 | `depth_override = None`; `interview_scope` is None -> COMPLEX check fails | **depth_override stays None** |
| 7 | cli.py | 497 | `task = args.task or ""` -> `task = ""` | Empty task |
| 8 | cli.py | 500 | `depth = depth_override or detect_depth("", config)` | **depth = "standard"** |
| 9 | cli.py | 503-511 | `_run_single(task="", depth="standard", prd_path="requirements.md", ...)` | - |
| 10 | cli.py | 257-260 | Inside _run_single: `prd_path` is set -> reads file, task overwritten to PRD content | Task now contains PRD |
| 11 | cli.py | 258 | `print_prd_mode("requirements.md")` | PRD banner shown |
| 12 | cli.py | 262-270 | `build_orchestrator_prompt(task=prd_task, depth="standard", prd_path="requirements.md", ...)` | - |
| 13 | agents.py | 749 | `get_agent_counts("standard")` | **Standard counts, NOT exhaustive!** |
| 14 | agents.py | 764 | `[DEPTH: STANDARD]` in prompt | **Should be EXHAUSTIVE** |
| 15 | agents.py | 791-795 | `[PRD MODE ACTIVE]` markers added | Correct |

### BUG IDENTIFIED: Depth Not Auto-Set to "exhaustive" in Single-Shot PRD Mode

**Severity:** CRITICAL

**Root Cause:** In `cli.py` `main()`, the depth override logic at lines 482-484 only checks for `interview_scope == "COMPLEX"`. There is no check for `args.prd` to auto-set depth to "exhaustive".

**Contrast with `_run_interactive`:** In `_run_interactive` (line 188), PRD mode correctly defaults to exhaustive:
```python
depth = depth_override or "exhaustive"  # line 188
```

But in `main()` for the single-shot path (line 500):
```python
depth = depth_override or detect_depth(task, config)  # line 500
```
Since `depth_override` is None and `task` is empty, `detect_depth("", config)` returns `"standard"`.

**Impact:** When a user runs `agent-team --prd big-project.md` (the most common PRD usage pattern), the orchestrator receives `[DEPTH: STANDARD]` with standard fleet sizes (planning: 3-5, coding: 2-3, etc.) instead of exhaustive fleet sizes (planning: 8-10, coding: 5-10, etc.). This means a full-application build from a PRD gets only moderate agent counts, significantly reducing the quality and thoroughness of the build.

**Recommended Fix Location:** `cli.py` lines 482-484. Add a PRD check:
```python
depth_override = args.depth
if not depth_override and (interview_scope == "COMPLEX" or args.prd):
    depth_override = "exhaustive"
```

### Verdict: FAIL

The PRD mode path has a critical integration bug where depth is not auto-set to "exhaustive" in single-shot mode, causing the orchestrator to deploy standard-sized fleets for what should be maximum-effort full-application builds.

---

## Cross-Cutting Concerns Analysis

### 1. INTERVIEWER_SYSTEM_PROMPT Quality

**Location:** `interviewer.py` lines 69-306

| Aspect | Status | Notes |
|--------|--------|-------|
| Scope detection instructions | OK | Lines 122-144 clearly define SIMPLE, MEDIUM, COMPLEX signals |
| Output format specification | OK | Lines 148-272 provide three complete templates with Scope: headers |
| Finalization protocol | OK | Lines 276-283 instruct AI to include Scope: header in final doc |
| Codebase exploration | OK | Lines 286-293 instruct AI to use Read, Glob, Grep |
| Anti-patterns | OK | Lines 296-305 prevent common mistakes |

The prompt is comprehensive and well-structured. The AI receives clear instructions on scope detection, document format, and finalization requirements.

### 2. Display Function Call Coverage

| Function | Expected Call Sites | Actual Call Sites | Status |
|----------|-------------------|-------------------|--------|
| `print_interview_start()` | Interview entry | `interviewer.py:397` | OK |
| `print_interview_end()` | Interview completion | `interviewer.py:534` | OK |
| `print_interview_skip()` | All skip paths | `cli.py:437` (--interview-doc), `cli.py:440` (--prd), `cli.py:443` (--no-interview) | OK |
| `print_prd_mode()` | All PRD paths | `cli.py:185` (interactive+prd), `cli.py:229` (interactive inline), `cli.py:258` (single-shot+prd) | OK |
| `print_interview_prompt()` | Interview input loop | `interviewer.py:449` | OK |
| `print_task_start()` | Before orchestrator query | `cli.py:199,231,272` | OK |

All display functions are called at the correct times with correct parameters.

### 3. Error Propagation

**Interview failure handling** (cli.py lines 446-469):

```
cli.py try:
    result = asyncio.run(run_interview(...))
                            |
                            v
            interviewer.py internal try:
                ClaudeSDKClient session
            except KeyboardInterrupt:
                prints info, falls through
            except Exception:
                prints info, falls through
            -> reads doc from disk (may be partial)
            -> returns InterviewResult
                            |
                            v
    interview_doc = result.doc_content or None
except KeyboardInterrupt:
    print_warning, proceed without interview
except Exception:
    print_error, proceed without interview
```

The error handling is defensive-in-depth. Internal exceptions in the SDK session are caught by interviewer.py and return a partial result. Exceptions in run_interview itself (before/after the SDK session) propagate to cli.py and are caught there. In all failure cases, the system proceeds without interview context. This is correct graceful degradation.

### 4. `__init__.py` Exports

`__init__.py` exports `main` and `__version__`. This is sufficient -- the CLI entry point is the only public API. Internal modules use relative imports correctly:
- `cli.py` imports from `.agents`, `.config`, `.display`, `.interviewer`, `.mcp_servers`
- `interviewer.py` imports from `.config`, `.display`
- `agents.py` imports from `.config`, `.mcp_servers`
- No circular import chains detected.

### 5. Type Consistency Across Module Boundaries

| Parameter | cli.py type | interviewer.py type | agents.py type | config.py type |
|-----------|-------------|--------------------|--------------------|----------------|
| config | AgentTeamConfig | AgentTeamConfig | AgentTeamConfig | AgentTeamConfig |
| cwd | str \| None | str \| None | str \| None | - |
| interview_doc | str \| None | - | str \| None | - |
| depth | str | - | str | str |
| task | str | - | str | str |
| prd_path | str \| None | - | str \| None | - |
| agent_count | int \| None | - | int \| None | - |

All types are consistent across module boundaries. No mismatches detected.

---

## Additional Issues Found

### Issue A: Dead Code in `build_orchestrator_prompt`

**Severity:** Minor (Suggestion)
**Location:** `agents.py` lines 756-759

```python
prompt = ORCHESTRATOR_SYSTEM_PROMPT.replace(
    "{escalation_threshold}", str(esc_threshold)
).replace(
    "{max_escalation_depth}", str(max_esc_depth)
)
```

This local variable `prompt` is computed but never referenced. The function builds and returns the `parts` list instead (line 809). The system prompt is separately processed in `cli.py` `_build_options()` (lines 108-115). This dead code is harmless but should be removed for clarity.

### Issue B: Scope Detection Fragility

**Severity:** Minor (Suggestion)
**Location:** `interviewer.py` lines 350-358

The `_detect_scope()` function checks if a line starts with `"scope:"` (case-insensitive). If the AI writes the Scope line with markdown formatting like `**Scope:** COMPLEX` or `## Scope: COMPLEX`, the detection would fail (returns default "MEDIUM").

This is mitigated by the prompt explicitly showing the format without markdown bold, and the finalization instruction specifically requesting the `Scope:` header. However, adding a regex-based fallback (e.g., `re.search(r'scope:\s*(SIMPLE|MEDIUM|COMPLEX)', doc_content, re.IGNORECASE)`) would make it more robust.

### Issue C: interview_doc Cleared After First Interactive Query

**Severity:** Not a bug (Design note)
**Location:** `cli.py` line 226

```python
# Only inject interview_doc on the first query
interview_doc = None
```

This is intentional and correct -- the interview document is injected once into the first orchestrator query, then cleared so subsequent interactive queries do not re-send the full document. The orchestrator retains the context from its conversation history. Worth noting as a design decision.

---

## Summary of Findings

| ID | Severity | Path | Description | Location |
|----|----------|------|-------------|----------|
| BUG-1 | **CRITICAL** | PATH 3 | PRD mode single-shot does not auto-set depth to "exhaustive" | `cli.py:482-484,500` |
| DEAD-1 | Minor | Cross-cutting | Dead code: unused `prompt` variable in `build_orchestrator_prompt` | `agents.py:756-759` |
| FRAG-1 | Minor | PATH 2 | `_detect_scope()` may fail on markdown-formatted Scope lines | `interviewer.py:350-358` |

---

## Final Verdicts

| Path | Verdict | Rationale |
|------|---------|-----------|
| PATH 1: Interactive Interview -> Orchestrator | **PASS** | All hand-offs correct, types consistent, parameters forwarded properly |
| PATH 2: COMPLEX Scope -> Exhaustive Depth | **PASS** | Complete chain from scope detection to max fleet sizes works correctly |
| PATH 3: PRD Mode -> Full Application Build | **FAIL** | Critical bug: depth defaults to "standard" instead of "exhaustive" in single-shot mode |
| Cross-cutting concerns | **PASS** | Display calls, error handling, exports, types all correct |

## Overall Verdict: FAIL

One critical integration bug prevents the PRD mode from working as designed in the most common usage pattern (`agent-team --prd file.md`). The orchestrator receives standard-depth fleet sizes instead of exhaustive, undermining the full-application build quality. The fix is a one-line addition at `cli.py` line 482-484.
