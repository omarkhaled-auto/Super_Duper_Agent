# Error Handling Audit — Agent 10 of 15
Date: 2026-02-01
Scope: All error paths in interviewer.py, cli.py, config.py, agents.py

---

## Executive Summary

**Total Paths Audited:** 9
**Critical Issues:** 2
**High Severity:** 3
**Medium Severity:** 2
**Low Severity:** 2

**Critical Findings:**
1. `ClaudeSDKClient.__aenter__` failure leaves transcript unwritten (CRITICAL)
2. YAML malformation crashes without recovery (CRITICAL)

---

## Detailed Findings

### 1. ClaudeSDKClient.__aenter__ Failure (interviewer.py:459)

**Location:** `interviewer.py:459` — `async with ClaudeSDKClient(options=options) as client:`

**Failure Mode:**
- If `ClaudeSDKClient.__aenter__` raises (e.g., network error, invalid API key, SDK initialization failure), the exception propagates BEFORE entering the async context manager
- The `except KeyboardInterrupt` and `except Exception` handlers at lines 563-569 do NOT catch this
- Control jumps directly to line 571 (transcript backup), but the transcript is empty at this point (line 430: `transcript: list[dict[str, str]] = []`)
- Result: Empty transcript backup, no meaningful error recovery

**Currently Handled:** NO

**Severity:** CRITICAL

**Impact:**
- User loses all context if the SDK client fails to initialize
- Interview never starts, but the error handling makes it look like "zero exchanges completed"
- No useful error message to guide user (e.g., "check API key", "check network")

**Evidence:**
```python
Lines 458-462:
try:
    async with ClaudeSDKClient(options=options) as client:  # FAILS HERE
        # Send the opening instruction (internal — user doesn't see this)
        await client.query(opening)
        # ... rest of interview
```

Lines 563-569 (exception handlers):
```python
except KeyboardInterrupt:
    print_info("Interview interrupted by user.")
except Exception as exc:
    print_info(f"Interview session error: {exc}")
    if doc_path.is_file():
        print_info(f"Partial interview document may exist at {doc_path}")
```

**These handlers are INSIDE the try block that starts at line 458, but `__aenter__` raises BEFORE entering the context, so they never execute.**

**Recommendation:**
Wrap the entire `async with` block in a separate try/except:
```python
try:
    try:
        async with ClaudeSDKClient(options=options) as client:
            # ... interview logic
    except KeyboardInterrupt:
        print_info("Interview interrupted by user.")
    except Exception as exc:
        print_info(f"Interview session error: {exc}")
        if doc_path.is_file():
            print_info(f"Partial interview document may exist at {doc_path}")
except Exception as exc:
    # Catches __aenter__ failures
    print_error(f"Failed to initialize Claude SDK client: {exc}")
    print_info("Check ANTHROPIC_API_KEY and network connectivity.")
    # Return empty result or raise
```

---

### 2. backup_path.write_text() — Missing Directory (interviewer.py:579)

**Location:** `interviewer.py:579` — `backup_path.write_text(...)`

**Failure Mode:**
- `doc_dir` is created at line 435: `doc_dir.mkdir(parents=True, exist_ok=True)`
- If `doc_dir` is deleted mid-interview (e.g., user runs `rm -rf .agent-team` in another terminal), `backup_path.write_text()` at line 579 raises `FileNotFoundError`
- This is caught by the `except Exception as exc` at line 584, which logs a warning but continues

**Currently Handled:** YES

**Severity:** LOW

**Impact:**
- If the directory is deleted mid-interview, transcript backup fails but is gracefully logged
- The main interview document (INTERVIEW.md) also fails to write, but the CLI already handles this at line 589-595
- User sees warning: "Failed to write transcript backup: [Errno 2] No such file or directory"

**Evidence:**
```python
Lines 571-585:
if transcript:
    backup_path = doc_dir / "INTERVIEW_BACKUP.json"
    try:
        backup_data = { ... }
        backup_path.write_text(
            json.dumps(backup_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print_info(f"Transcript backup saved to {backup_path}")
    except Exception as exc:
        logger.warning("Failed to write transcript backup: %s", exc)
```

**Recommendation:**
Add explicit directory check before write:
```python
if transcript:
    backup_path = doc_dir / "INTERVIEW_BACKUP.json"
    try:
        doc_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        backup_data = { ... }
        backup_path.write_text(...)
    except Exception as exc:
        logger.warning("Failed to write transcript backup: %s", exc)
```

---

### 3. Path(args.prd).read_text() — File Permissions (cli.py:186, 263, 443)

**Location:**
- `cli.py:186` — `prd_content = Path(prd_path).read_text(encoding="utf-8")`
- `cli.py:263` — `prd_content = Path(prd_path).read_text(encoding="utf-8")`
- `cli.py:443` — `interview_doc = Path(args.interview_doc).read_text(encoding="utf-8")`

**Failure Mode:**
- If the file exists but is not readable (permissions error), `read_text()` raises `PermissionError`
- This propagates uncaught and crashes the CLI
- The file existence check at lines 417-419 and 422-424 does NOT catch permission errors

**Currently Handled:** NO

**Severity:** HIGH

**Impact:**
- CLI crashes with a raw exception trace if PRD or interview doc is unreadable
- No user-friendly error message
- Rare on POSIX systems, more common on Windows with file locking or ACLs

**Evidence:**
```python
Lines 417-419:
if args.prd and not Path(args.prd).is_file():
    print_error(f"PRD file not found: {args.prd}")
    sys.exit(1)

Lines 443:
interview_doc = Path(args.interview_doc).read_text(encoding="utf-8")  # CAN RAISE
```

**Recommendation:**
Wrap all `read_text()` calls in try/except:
```python
try:
    prd_content = Path(prd_path).read_text(encoding="utf-8")
except PermissionError:
    print_error(f"Cannot read PRD file (permission denied): {prd_path}")
    sys.exit(1)
except Exception as exc:
    print_error(f"Error reading PRD file: {exc}")
    sys.exit(1)
```

---

### 4. asyncio.run() — Event Loop Already Running (cli.py:455, 495, 511)

**Location:**
- `cli.py:455` — `result = asyncio.run(run_interview(...))`
- `cli.py:495` — `asyncio.run(_run_interactive(...))`
- `cli.py:511` — `asyncio.run(_run_single(...))`

**Failure Mode:**
- If the CLI is invoked from within an already-running async context (e.g., Jupyter notebook, another async CLI wrapper), `asyncio.run()` raises `RuntimeError: asyncio.run() cannot be called from a running event loop`
- This is uncaught and crashes the CLI

**Currently Handled:** NO

**Severity:** MEDIUM

**Impact:**
- CLI is unusable in Jupyter/IPython environments or when embedded in async code
- Error message is cryptic for non-asyncio users
- Workaround: use `await run_interview()` instead of `asyncio.run()`, but this is not documented

**Evidence:**
```python
Lines 454-459:
try:
    result = asyncio.run(run_interview(  # CAN RAISE RuntimeError
        config=config,
        cwd=cwd,
        initial_task=args.task,
    ))
```

**Recommendation:**
Check for running loop and fall back to `await` or nest a new loop:
```python
import asyncio

try:
    loop = asyncio.get_running_loop()
    # Already running — use nest_asyncio or warn user
    print_error("Cannot run from within an async context. Use await or run in sync environment.")
    sys.exit(1)
except RuntimeError:
    # No loop running — safe to use asyncio.run()
    result = asyncio.run(run_interview(...))
```

Or document this limitation in README.

---

### 5. print_warning for --prd + --interview-doc (cli.py:439)

**Location:** `cli.py:438-439`

```python
if args.prd and args.interview_doc:
    print_warning("Both --prd and --interview-doc provided; using --interview-doc")
```

**Failure Mode:**
- Execution continues correctly — `--interview-doc` takes precedence
- This is by design (line 441: `if args.interview_doc:` runs before `elif args.prd:`)

**Currently Handled:** YES

**Severity:** N/A (not an error)

**Impact:**
- User gets a clear warning, behavior is predictable
- No issue here

---

### 6. yaml.safe_load(f) — Malformed YAML (config.py:248)

**Location:** `config.py:247-249`

```python
with open(path, "r", encoding="utf-8") as f:
    loaded = yaml.safe_load(f) or {}
raw = _deep_merge(raw, loaded)
```

**Failure Mode:**
- If YAML is malformed (syntax error), `yaml.safe_load()` raises `yaml.YAMLError`
- This propagates uncaught and crashes `load_config()`, which crashes the CLI at line 408

**Currently Handled:** NO

**Severity:** CRITICAL

**Impact:**
- Any typo in config.yaml crashes the entire CLI with a raw exception
- User has no guidance on what's wrong or where
- Config files are user-editable, so this is a COMMON failure mode

**Evidence:**
```python
Lines 245-250:
for path in search_paths:
    if path.is_file():
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}  # CAN RAISE yaml.YAMLError
        raw = _deep_merge(raw, loaded)
        break  # Use first found file
```

**Recommendation:**
Wrap in try/except with user-friendly error:
```python
for path in search_paths:
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            print(f"ERROR: Malformed YAML in config file: {path}")
            print(f"Details: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"ERROR: Cannot read config file: {path} — {exc}")
            sys.exit(1)
        raw = _deep_merge(raw, loaded)
        break
```

---

### 7. _dict_to_config — Non-dict in agents (config.py:198)

**Location:** `config.py:197-203`

```python
if "agents" in data:
    for name, agent_data in data["agents"].items():
        if isinstance(agent_data, dict):  # Guards against non-dict
            cfg.agents[name] = AgentConfig(
                model=agent_data.get("model", "opus"),
                enabled=agent_data.get("enabled", True),
            )
```

**Failure Mode:**
- If user writes `agents: ["planner", "researcher"]` (list instead of dict), the loop at line 198 raises `AttributeError: 'list' object has no attribute 'items'`
- This propagates uncaught and crashes the CLI

**Currently Handled:** NO (partial guard)

**Severity:** HIGH

**Impact:**
- Invalid config structure crashes CLI with cryptic error
- The `isinstance(agent_data, dict)` check at line 199 only guards INSIDE the loop, not the loop itself

**Evidence:**
```python
Lines 197-203:
if "agents" in data:
    for name, agent_data in data["agents"].items():  # CAN RAISE if data["agents"] is not dict
        if isinstance(agent_data, dict):
            cfg.agents[name] = AgentConfig(...)
```

**Recommendation:**
Check type before iterating:
```python
if "agents" in data:
    if not isinstance(data["agents"], dict):
        raise ValueError(
            f"Config error: 'agents' must be a dict, got {type(data['agents']).__name__}"
        )
    for name, agent_data in data["agents"].items():
        if isinstance(agent_data, dict):
            cfg.agents[name] = AgentConfig(...)
```

Same issue exists for `mcp_servers` at lines 205-210. Apply same fix.

---

### 8. build_orchestrator_prompt — Invalid depth (agents.py:749)

**Location:** `agents.py:749` — `agent_counts = get_agent_counts(depth)`

**Failure Mode:**
- If `depth` is an invalid string (not in `["quick", "standard", "thorough", "exhaustive"]`), `get_agent_counts()` at line 140 returns the default (`DEPTH_AGENT_COUNTS["standard"]`)
- This is safe — no crash

**Currently Handled:** YES (graceful fallback)

**Severity:** LOW

**Impact:**
- Invalid depth defaults to "standard"
- No user warning, but behavior is predictable
- Could add validation at CLI arg parsing (argparse already constrains choices)

**Evidence:**
```python
Lines 138-140 (config.py):
def get_agent_counts(depth: str) -> dict[str, tuple[int, int]]:
    """Return (min, max) agent counts per phase for the given depth."""
    return DEPTH_AGENT_COUNTS.get(depth, DEPTH_AGENT_COUNTS["standard"])
```

CLI argparse (lines 327-331):
```python
parser.add_argument(
    "--depth",
    choices=["quick", "standard", "thorough", "exhaustive"],
    default=None,
    help="Override depth level",
)
```

**Recommendation:**
No change needed — argparse enforces valid choices. Internal calls use safe defaults.

---

### 9. get_research_tools(mcp_servers) — Returns None (agents.py:657)

**Location:** `agents.py:657` — `research_tools = get_research_tools(mcp_servers)`

**Failure Mode:**
- If `get_research_tools()` returns `None` instead of an empty list, the unpacking at line 675 (`*research_tools`) raises `TypeError: argument after * must be an iterable, not NoneType`

**Currently Handled:** DEPENDS on implementation

**Severity:** MEDIUM

**Impact:**
- If `get_research_tools()` has a bug or missing return, agent definitions fail to build and CLI crashes
- Need to verify implementation in `mcp_servers.py` (not audited in this pass)

**Evidence:**
```python
Lines 657:
research_tools = get_research_tools(mcp_servers)

Lines 669-678:
if config.agents.get("researcher", AgentConfig()).enabled:
    agents["researcher"] = {
        "description": "Researches libraries, APIs, and best practices via web and docs",
        "prompt": RESEARCHER_PROMPT,
        "tools": [
            "Read", "Write", "Edit", "WebSearch", "WebFetch",
            *research_tools,  # CAN RAISE if research_tools is None
        ],
        "model": "opus",
    }
```

**Recommendation:**
Add safety check:
```python
research_tools = get_research_tools(mcp_servers)
if research_tools is None:
    research_tools = []
```

Or ensure `get_research_tools()` always returns a list (verify in `mcp_servers.py`).

---

## Summary Table

| # | Location | Issue | Severity | Handled? |
|---|----------|-------|----------|----------|
| 1 | interviewer.py:459 | `ClaudeSDKClient.__aenter__` failure | CRITICAL | NO |
| 2 | interviewer.py:579 | `backup_path.write_text()` missing dir | LOW | YES |
| 3 | cli.py:186,263,443 | `read_text()` permission error | HIGH | NO |
| 4 | cli.py:455,495,511 | `asyncio.run()` in running loop | MEDIUM | NO |
| 5 | cli.py:439 | `--prd + --interview-doc` warning | N/A | YES |
| 6 | config.py:248 | `yaml.safe_load()` malformed YAML | CRITICAL | NO |
| 7 | config.py:198 | `agents` non-dict in config | HIGH | NO |
| 8 | agents.py:749 | Invalid depth string | LOW | YES |
| 9 | agents.py:657 | `get_research_tools()` returns None | MEDIUM | UNKNOWN |

---

## Priority Fix Order

1. **config.py:248** (CRITICAL) — Malformed YAML crashes (common user error)
2. **interviewer.py:459** (CRITICAL) — SDK init failure loses transcript
3. **cli.py:186,263,443** (HIGH) — Permission errors crash CLI
4. **config.py:198** (HIGH) — Invalid config structure crashes CLI
5. **cli.py:455,495,511** (MEDIUM) — Async loop conflict (Jupyter users)
6. **agents.py:657** (MEDIUM) — Verify `get_research_tools()` implementation
7. **interviewer.py:579** (LOW) — Already handled, document in README
8. **agents.py:749** (LOW) — Already handled gracefully

---

## Additional Findings

### File I/O Pattern
All file operations use `Path.read_text()` and `Path.write_text()` without try/except at call sites. This is a systemic risk:
- **Recommendation:** Wrap all file I/O in utility functions that handle common errors (permissions, encoding, disk full)

### Error Message Consistency
Some errors use `print_error()` (cli.py), some use `logger.warning()` (interviewer.py), some use raw `print()`.
- **Recommendation:** Standardize on display.py functions for user-facing errors

### Graceful Degradation
No fallback for critical service failures (e.g., if Claude API is down, CLI exits with no recovery options).
- **Recommendation:** Add retry logic or offline mode for non-critical failures

---

## Verification Checklist

- [ ] Test malformed config.yaml (random characters, invalid indent, list instead of dict)
- [ ] Test PRD file with 0400 permissions (read-only for owner, unreadable for process)
- [ ] Test interview interruption during `ClaudeSDKClient.__aenter__`
- [ ] Test CLI invocation from Jupyter notebook (asyncio conflict)
- [ ] Test deletion of `.agent-team/` directory mid-interview
- [ ] Verify `get_research_tools()` always returns list (check mcp_servers.py)
- [ ] Test invalid depth string passed to internal functions (should use default)
- [ ] Test config with `agents: ["planner"]` (list instead of dict)
- [ ] Test config with `agents: {planner: "enabled"}` (string instead of dict)

---

## End of Report
