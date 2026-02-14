# Anthropic SDK / Claude API Technical Audit Report

**Reviewer:** Anthropic SDK Technical Reviewer
**Date:** 2026-02-14
**Scope:** BUILD1_PRD.md, BUILD2_PRD.md, BUILD3_PRD.md + supporting architecture/research documents

---

## 1. Context7 Research Summary

Researched the Anthropic Python SDK (`/anthropics/anthropic-sdk-python`, 203 code snippets, High reputation, score 84.7) via Context7. Key findings from current SDK documentation:

### Client Creation
- **Sync:** `from anthropic import Anthropic; client = Anthropic()`
- **Async:** `from anthropic import AsyncAnthropic; client = AsyncAnthropic()`
- API key loaded from `ANTHROPIC_API_KEY` env var automatically

### Messages API
- `client.messages.create(model=..., max_tokens=..., messages=..., system=..., temperature=..., tools=...)`
- Streaming: `client.messages.stream(...)` (context manager) or `stream=True` on `.create()`
- Token counting: `client.messages.count_tokens(model=..., messages=...)`
- Usage: `message.usage.input_tokens`, `message.usage.output_tokens`

### Tool Use
- Tool definition: `{"name": ..., "description": ..., "input_schema": {"type": "object", "properties": ..., "required": ...}}`
- Tool result: `{"type": "tool_result", "tool_use_id": tool.id, "content": [{"type": "text", "text": ...}]}`

### Error Types (by status code)
- `anthropic.APIConnectionError` (network)
- `anthropic.RateLimitError` (429)
- `anthropic.BadRequestError` (400)
- `anthropic.AuthenticationError` (401)
- `anthropic.PermissionDeniedError` (403)
- `anthropic.NotFoundError` (404)
- `anthropic.UnprocessableEntityError` (422)
- `anthropic.InternalServerError` (>=500)
- `anthropic.APIStatusError` (parent class for all status errors)

### Current Model IDs (as of Feb 2026)
- `claude-opus-4-6` (latest Opus)
- `claude-sonnet-4-5-20250929` (latest Sonnet)
- `claude-haiku-4-5-20251001` (latest Haiku)
- Older: `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`

---

## 2. Build 1 PRD — Findings

### 2.1 Direct Anthropic SDK / Claude API Usage

**Build 1 does NOT directly use the Anthropic Python SDK.** Build 1 is a pure infrastructure project (FastAPI + SQLite + MCP + tree-sitter). It uses the **MCP Python SDK** (`mcp>=1.25,<2`) for Claude Code integration, not the Anthropic SDK directly.

**Verdict: No Anthropic SDK claims to verify in Build 1 PRD requirements.**

### 2.2 Indirect References

| Location | Claim | Status |
|----------|-------|--------|
| TECH-024 | "MCP server must run with transport='stdio' for Claude Code integration" | **CORRECT** - MCP SDK supports stdio transport |
| TECH-027 | "MCP SDK uses [type annotations and docstrings] to auto-generate tool JSON schemas" | **CORRECT** - MCP Python SDK `@mcp.tool()` uses type hints for schema generation |
| Technology Stack | `mcp>=1.25,<2` | **CORRECT** - Valid MCP SDK version range |

### 2.3 Model Name Reference

| Location | Claim | Status |
|----------|-------|--------|
| BUILD1_ARCHITECTURE_PLAN.md:2183 | `model: "claude-sonnet-4-20250514"` | **CORRECT** - Valid model ID (used in agent-team config, not SDK code) |

### 2.4 Build 1 Issues Found

**None.** Build 1 correctly avoids direct Anthropic SDK usage and only references Claude through the MCP SDK and agent-team configuration.

---

## 3. Build 2 PRD — Findings

### 3.1 Direct Anthropic SDK / Claude API Usage

**Build 2 does NOT directly use the Anthropic Python SDK.** Build 2 upgrades the existing agent-team codebase with MCP client integrations and Claude Code Agent Teams. It interacts with Claude through:
1. The existing `agent-team` CLI (`_backend` module that calls Claude API — already implemented in v14.0, not part of Build 2 PRD scope)
2. MCP Python SDK (`mcp>=1.25,<2`) for Contract Engine and Codebase Intelligence clients
3. Claude Code Agent Teams (experimental, via `claude` CLI subprocess)

### 3.2 MCP Client Usage Claims

| Location | Claim | Status |
|----------|-------|--------|
| REQ-024 | `StdioServerParameters` + `stdio_client()` + `ClientSession` pattern | **CORRECT** - Standard MCP Python SDK client pattern |
| REQ-025 | `await session.initialize()` must be called immediately after ClientSession creation | **CORRECT** - MCP SDK requires initialization before tool calls |
| TECH-019 | Lazy import of `mcp` package with ImportError handling | **CORRECT** - Best practice for optional dependency |
| TECH-020 | `StdioServerParameters` accepts `env` dict and `cwd` | **CORRECT** - Per MCP SDK |

### 3.3 Claude Code Agent Teams Claims

| Location | Claim | Status |
|----------|-------|--------|
| REQ-004 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var | **CORRECT** - Documented experimental feature |
| REQ-006 | `CLAUDE_CODE_SUBAGENT_MODEL` env var for teammate model | **CORRECT** - Documented env var |
| TECH-010 | `subprocess.run(["claude", "--version"])` to verify CLI | **CORRECT** - Standard availability check |
| TECH-005 | `teammate_display_mode: str = "in-process"` | **CORRECT** - Valid display mode |
| TECH-001 | "Claude Code Agent Teams API does not expose per-task cost" | **CORRECT** - Agent Teams does not provide per-task cost breakdown |

### 3.4 Security Claims

| Location | Claim | Status |
|----------|-------|--------|
| SEC-001 | "MCP client connections must not pass `ANTHROPIC_API_KEY` as MCP server env vars" | **CORRECT** - Good security practice; MCP servers don't need API keys |

### 3.5 Architecture Plan Warning

| Location | Claim | Status | Severity |
|----------|-------|--------|----------|
| BUILD2_ARCHITECTURE_PLAN.md:284 | `"ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")` in AgentTeamsBackend env | **ISSUE - MEDIUM** | The architecture plan passes ANTHROPIC_API_KEY to agent teams environment, but the PRD's SEC-001 correctly prohibits this for MCP servers. The architecture plan is a design document (not the PRD), but this contradiction should be flagged. The PRD is correct; the architecture plan snippet should not pass API keys to MCP server environment. Note: Claude Code Agent Teams teammates inherit the parent process environment automatically, so explicitly passing ANTHROPIC_API_KEY is unnecessary AND violates SEC-001 principles. |

### 3.6 Build 2 Issues Found

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| B2-1 | **INFO** | BUILD2_ARCHITECTURE_PLAN.md:284 | Architecture plan snippet passes ANTHROPIC_API_KEY in env dict to agent teams backend | Not in PRD (architecture plan only). The PRD correctly handles this via SEC-001. No PRD fix needed. |

**Verdict: Build 2 PRD has zero Anthropic SDK issues.** All Claude API interaction is correctly delegated to the existing agent-team infrastructure (v14.0) or Claude Code CLI.

---

## 4. Build 3 PRD — Findings

### 4.1 Direct Anthropic SDK / Claude API Usage

**Build 3 does NOT directly use the Anthropic Python SDK in its PRD requirements.** Build 3 interacts with Claude through:
1. MCP stdio transport (via MCP Python SDK) for Architect and Contract Engine communication
2. `python -m agent_team` subprocess for Builder execution (which internally uses Claude API)

### 4.2 MCP Client Usage Claims

| Location | Claim | Status |
|----------|-------|--------|
| REQ-046 | `from mcp import StdioServerParameters; from mcp.client.stdio import stdio_client; from mcp.client.session import ClientSession` | **CORRECT** - Standard MCP Python SDK imports |
| REQ-046 | `async with stdio_client(StdioServerParameters(...)) as (read, write): async with ClientSession(read, write) as session: await session.initialize(); result = await session.call_tool(...)` | **CORRECT** - Standard MCP client pattern |
| REQ-046 | Fallback to subprocess + JSON if MCP SDK import fails | **CORRECT** - Good graceful degradation |
| INT-006 | "MCP client imports must be lazy (inside function bodies) with clear ImportError messages" | **CORRECT** - Best practice |

### 4.3 Cost/Pricing Claims

| Location | Claim | Status | Severity |
|----------|-------|--------|----------|
| BUILD3_TECH_STATE_CLI.md:965 | `"claude-opus-4": {"input_per_1k": 0.015, "output_per_1k": 0.075}` | **ISSUE - HIGH** | Pricing is inaccurate. Current Claude Opus 4 pricing is $15/1M input, $75/1M output (which would be $0.015/$0.075 per 1K). The values shown are numerically correct for per-1K pricing but the model ID `claude-opus-4` is not a valid model ID. The correct model IDs are `claude-opus-4-6` or `claude-opus-4-20250514`. |
| BUILD3_TECH_STATE_CLI.md:970 | `"claude-sonnet-4": {"input_per_1k": 0.003, "output_per_1k": 0.015}` | **ISSUE - HIGH** | Model ID `claude-sonnet-4` is not valid. Should be `claude-sonnet-4-5-20250929` or similar. The pricing values ($3/1M input, $15/1M output) are approximately correct for Claude Sonnet 4. |
| BUILD3_TECH_STATE_CLI.md:975 | `"claude-haiku-4": {"input_per_1k": 0.0008, "output_per_1k": 0.004}` | **ISSUE - HIGH** | Model ID `claude-haiku-4` is not valid. Should be `claude-haiku-4-5-20251001` or similar. The pricing values ($0.80/1M input, $4/1M output) are approximately correct for Claude Haiku. |
| BUILD3_TECH_STATE_CLI.md:963 | Comment: "Claude API pricing (as of 2025 — verify current rates)" | **MITIGATED** | The comment correctly notes these should be verified. |

### 4.4 Model ID Analysis

The Build 3 technology research document uses **shortened model IDs** (`claude-opus-4`, `claude-sonnet-4`, `claude-haiku-4`) as dictionary keys for a cost lookup table. These are NOT valid Anthropic API model IDs.

**Valid model IDs (current as of Feb 2026):**
- `claude-opus-4-6` (Opus 4.6)
- `claude-sonnet-4-5-20250929` (Sonnet 4.5)
- `claude-haiku-4-5-20251001` (Haiku 4.5)
- `claude-sonnet-4-20250514` (Sonnet 4, older)

**However:** These shortened IDs appear ONLY in `BUILD3_TECH_STATE_CLI.md` (a research/reference document), NOT in the Build 3 PRD itself (`BUILD3_PRD.md`). The PRD does not specify model IDs or pricing constants. The research document is informational context, and the PRD correctly delegates cost tracking to `PipelineCostTracker` without hardcoding specific model pricing.

### 4.5 Subprocess / Agent Team Interaction Claims

| Location | Claim | Status |
|----------|-------|--------|
| REQ-024 / TECH-023 | `asyncio.create_subprocess_exec("python", "-m", "agent_team", "--cwd", ..., "--depth", ...)` | **CORRECT** - Valid subprocess invocation of Build 2's agent-team CLI |
| REQ-048 | Cost extracted from `{output_dir}/.agent-team/STATE.json` via `json.loads(path.read_text(encoding='utf-8')).get('total_cost', 0.0)` | **CORRECT** - Matches agent-team STATE.json format |
| TECH-027 | "The top-level entry point must call `asyncio.run()` exactly once. No nested asyncio.run()" | **CORRECT** - Critical Python asyncio best practice |
| SEC-001 | "Must not pass ANTHROPIC_API_KEY as environment variables to Builder subprocesses — Builders inherit environment from parent process" | **CORRECT** - Builders inherit env naturally; explicitly passing keys is unnecessary and risky |

### 4.6 Build 3 Issues Found

| # | Severity | Location | Issue | Recommended Fix |
|---|----------|----------|-------|-----------------|
| B3-1 | **HIGH** | BUILD3_TECH_STATE_CLI.md:965-979 | Model IDs in PRICING dict (`claude-opus-4`, `claude-sonnet-4`, `claude-haiku-4`) are not valid Anthropic API model IDs | Use correct model IDs: `claude-opus-4-6`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`. Or use a prefix-matching lookup since model IDs evolve. |
| B3-2 | **LOW** | BUILD3_TECH_STATE_CLI.md:963 | Cache read pricing included but `cache_read_per_1k` is not used anywhere in Build 3 PRD | Info only — no fix needed. Good to have for future use. |

**Important mitigation:** B3-1 is in the TECH research document, NOT in the Build 3 PRD itself. The PRD (`BUILD3_PRD.md`) does not hardcode model IDs or pricing. The `PipelineCostTracker` (REQ-010) tracks cost as a float without model-specific pricing logic. **The PRD is clean.**

---

## 5. Cross-Build Analysis

### 5.1 Token Counting

None of the 3 PRDs use `client.messages.count_tokens()` or `anthropic.count_tokens()`. Token counting is not needed because:
- Build 1: No Claude API interaction
- Build 2: Cost tracked at session level via `RunState.total_cost`
- Build 3: Cost tracked via `PipelineCostTracker` reading STATE.json

**Verdict: Correct approach.** Token counting is an API-level concern handled by the underlying agent-team infrastructure (v14.0), not by the builds themselves.

### 5.2 Rate Limiting

None of the 3 PRDs implement rate limiting retry logic. This is correct because:
- Build 1: No Claude API calls
- Build 2: MCP clients have their own retry logic (3 retries with exponential backoff per REQ-026/REQ-042)
- Build 3: Subprocess-based builder invocation delegates rate limiting to the agent-team CLI

**Verdict: Correct.** Rate limiting is handled at the correct abstraction level.

### 5.3 Error Handling Pattern Consistency

All three builds follow the same error handling philosophy:
- Try/except with safe defaults for external service calls
- Crash isolation per scan/phase
- Graceful fallback paths

This is consistent and correct.

### 5.4 API Key Security

| Build | Claim | Status |
|-------|-------|--------|
| Build 2 SEC-001 | Don't pass ANTHROPIC_API_KEY to MCP server env vars | **CORRECT** |
| Build 3 SEC-001 | Don't pass ANTHROPIC_API_KEY to Builder subprocesses | **CORRECT** |
| Build 2 SEC-002 | Hook scripts must not contain embedded secrets | **CORRECT** |

**Verdict: All API key handling is correct across all 3 PRDs.**

---

## 6. Summary

### Issues by Severity

| Severity | Count | Details |
|----------|-------|---------|
| **CRITICAL** | 0 | None |
| **HIGH** | 1 | B3-1: Invalid model IDs in BUILD3_TECH_STATE_CLI.md PRICING dict (NOT in PRD) |
| **MEDIUM** | 0 | None |
| **LOW** | 1 | B3-2: Unused cache_read_per_1k in research doc (NOT in PRD) |
| **INFO** | 1 | B2-1: Architecture plan snippet contradiction with SEC-001 (NOT in PRD) |

### Verdict

**All 3 Build PRDs are CLEAN from an Anthropic SDK / Claude API perspective.**

The PRDs correctly:
1. **Do NOT directly import or use the Anthropic Python SDK** — all Claude API interaction is delegated to the existing agent-team v14.0 infrastructure
2. **Use the MCP Python SDK correctly** for service-to-service communication
3. **Handle API keys securely** with explicit SEC requirements prohibiting key leakage
4. **Track costs correctly** at the session/pipeline level without hardcoding model-specific pricing
5. **Use valid model IDs** where referenced (BUILD1_ARCHITECTURE_PLAN.md uses `claude-sonnet-4-20250514`)

The only issues found are in **supporting research/architecture documents** (not in the PRDs themselves):
- `BUILD3_TECH_STATE_CLI.md` uses shortened/invalid model IDs in a pricing table — this is a reference document and the PRD correctly avoids hardcoding pricing
- `BUILD2_ARCHITECTURE_PLAN.md` has a code snippet passing ANTHROPIC_API_KEY in env, but the PRD's SEC-001 correctly prohibits this

### Recommended Fixes

1. **BUILD3_TECH_STATE_CLI.md** (research doc, not PRD): Update PRICING dict keys from `claude-opus-4`/`claude-sonnet-4`/`claude-haiku-4` to valid model IDs (`claude-opus-4-6`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`), or add a prefix-matching lookup function since model IDs evolve over time.

2. **No PRD changes required.** All three Build PRDs are technically accurate regarding Anthropic SDK and Claude API usage.
