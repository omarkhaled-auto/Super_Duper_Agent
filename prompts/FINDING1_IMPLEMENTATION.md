# Finding 1: Orchestrator Direct Integration Verification

## Design Rationale

During the Drawspace canvas upgrade verification run, it was observed that when the orchestrator handled complex integration tasks (cross-service wiring, multi-module coordination) DIRECTLY instead of delegating to sub-agents, results were significantly better. This is because the orchestrator has:

- Full project context across all milestones
- Access to all MCP tools (Context7, Firecrawl, Sequential Thinking)
- Knowledge of all milestones and their relationships
- The ability to read and edit files directly

Sub-agents only see their narrow task scope and miss cross-cutting concerns.

### Solution: 3-Layer Implementation

1. **Config layer** (`config.py`): Two new fields on `MilestoneConfig` control behavior
2. **Prompt layer** (`agents.py`): Two prompt injections instruct the orchestrator and milestone executors
3. **Pipeline layer** (`cli.py`): A new `_run_integration_verification()` sub-orchestrator call

---

## Changes Made

### 1. `src/agent_team/config.py`

**Fields added to `MilestoneConfig`** (line ~291-292):
```python
orchestrator_direct_integration: bool = True   # Orchestrator verifies cross-milestone integration directly
orchestrator_integration_scope: str = "cross_milestone"  # "cross_milestone", "full", "none"
```

**Validation** (after `review_recovery_retries` validation):
- `orchestrator_integration_scope` must be one of `("cross_milestone", "full", "none")`

**`_dict_to_config` loader** — added two fields to milestone loading:
- `orchestrator_direct_integration` from YAML
- `orchestrator_integration_scope` from YAML

**User overrides tracking** — `orchestrator_direct_integration` added to tracked keys for depth gating

**Depth gating** — `quick` depth disables direct integration:
```python
_gate("milestone.orchestrator_direct_integration", False, config.milestone, "orchestrator_direct_integration")
```

### 2. `src/agent_team/agents.py`

**Prompt injection 1: `build_milestone_execution_prompt()`** — `[INTEGRATION AWARENESS]` block

Added AFTER the `[CYCLE TRACKING]` section and BEFORE `[INTEGRATION VERIFICATION]`. Gated by `config.milestone.orchestrator_direct_integration`. Instructs each milestone executor to:
1. List external dependencies (imports from other milestones)
2. List exports (functions, classes, types for other milestones)
3. Write INTEGRATION_NOTES.md in the milestone directory
4. Note changes to shared types/interfaces

**Prompt injection 2: `build_orchestrator_prompt()`** — `[DIRECT INTEGRATION VERIFICATION]` block

Added at the end of the function, BEFORE the constraints block. Gated by `config.milestone.orchestrator_direct_integration`. Instructs the orchestrator to:
1. Verify import paths resolve correctly
2. Check type compatibility across modules
3. Verify API contract alignment (backend endpoints match frontend calls)
4. Check wiring completeness (WIRE-xxx, SVC-xxx)
5. Verify configuration consistency (ports, URLs, env vars)
6. Fix issues DIRECTLY using Edit tool (not delegation)

The scope parameter controls what to check:
- `cross_milestone` — only cross-milestone connections
- `full` — all integration points including intra-milestone

### 3. `src/agent_team/cli.py`

**New function: `_run_integration_verification()`** (inserted after `_run_milestone_wiring_fix()`):

```python
async def _run_integration_verification(
    milestone_id: str,
    milestone_title: str,
    completed_milestones: list[str],
    config: AgentTeamConfig,
    cwd: str | None,
    depth: str,
    task: str,
    constraints: list | None = None,
    intervention: "InterventionQueue | None" = None,
) -> float:
```

- Creates a focused sub-orchestrator session with a `[PHASE: DIRECT INTEGRATION VERIFICATION]` prompt
- Includes context about completed milestones
- Reads INTEGRATION_NOTES.md from the milestone directory if available
- Instructs the orchestrator to verify imports, types, API contracts, orphan files, and config
- Any issues found are fixed directly by the orchestrator
- Non-blocking: wrapped in try/except in the pipeline

**Pipeline wiring** — in `_run_prd_milestones()`, after the wiring check block and before "Mark complete":
```python
# Orchestrator direct integration verification (if enabled)
if config.milestone.orchestrator_direct_integration:
    try:
        completed_ms_ids = [m.id for m in plan.milestones if m.status == "COMPLETE" and m.id != milestone.id]
        integ_cost = await _run_integration_verification(...)
        total_cost += integ_cost
    except Exception as exc:
        print_warning(f"Integration verification for {milestone.id} failed (non-blocking): {exc}")
```

---

## Config Defaults and Overrides

| Field | Default | Quick | Standard | Thorough | Exhaustive |
|-------|---------|-------|----------|----------|------------|
| `orchestrator_direct_integration` | `True` | `False` | `True` | `True` | `True` |
| `orchestrator_integration_scope` | `"cross_milestone"` | N/A (disabled) | `"cross_milestone"` | `"cross_milestone"` | `"cross_milestone"` |

Users can override via `config.yaml`:
```yaml
milestone:
  orchestrator_direct_integration: false  # Disable entirely
  orchestrator_integration_scope: "full"  # Check everything, not just cross-milestone
```

---

## Integration with Existing Flow

### Pipeline position (per milestone):
```
1. Milestone execution (ClaudeSDKClient session)
2. Normalize milestone directories
3. TASKS.md existence check
4. Health check + review recovery loop
5. Handoff generation + validation
6. Wiring completeness check
7. Mock data scan
8. UI compliance scan
9. Final health gate decision
10. Wiring verification (existing)
11. >>> INTEGRATION VERIFICATION (NEW) <<<
12. Mark complete
13. Cache completion summary
```

### Interactions with existing features:
- **Wiring check** (`config.milestone.wiring_check`): Complementary. Wiring check verifies exports/imports exist. Integration verification goes deeper (type compatibility, API contracts, config consistency).
- **Handoff documents**: Integration verification reads `INTEGRATION_NOTES.md` written by milestone executors.
- **Mock data scan**: Runs before integration verification. Mock issues are fixed first.
- **Health gate**: If health gate FAILs, the milestone is marked FAILED and integration verification is skipped (via `continue`).

---

## Zero Regression Guarantees

1. **Config backward compatibility**: New fields have sensible defaults (`True` and `"cross_milestone"`). Existing configs without these fields work unchanged.
2. **Prompt injection is conditional**: Both prompt blocks are gated by `config.milestone.orchestrator_direct_integration`. When `False`, zero additional prompt content.
3. **Pipeline is crash-isolated**: The integration verification call is wrapped in `try/except`. A failure logs a warning but does not block milestone completion.
4. **Quick depth disables it**: The `quick` depth level disables integration verification via depth gating, matching the pattern of other features.
5. **Test results**: 252 config tests, 196 agents tests, 146 CLI tests, 441 cross-upgrade/wiring tests — ALL PASSING, 0 regressions.
