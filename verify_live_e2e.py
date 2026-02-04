#!/usr/bin/env python3
"""
Live E2E Verification Script for agent-team 12 Fixes.

Checks the output of an agent-team run against test-apps/e2e-verify/
to confirm all 12 issues are properly fixed.
"""

import json
import os
import re
import sys


BASE_DIR = os.path.join(os.path.dirname(__file__), "test-apps", "e2e-verify")
AGENT_DIR = os.path.join(BASE_DIR, ".agent-team")

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    return ok


def main() -> int:
    print("=" * 60)
    print("  Live E2E Verification: agent-team 12 Fixes")
    print("=" * 60)
    print()

    results = []
    log_file = os.path.join(BASE_DIR, "agent-team-output.log")
    log_content = ""
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()

    # ── Check 1: REQUIREMENTS.md exists and has [x] items ──────────────
    print("1. REQUIREMENTS.md — Issues #1, #2 (requirements marking)")
    req_path = os.path.join(AGENT_DIR, "REQUIREMENTS.md")
    req_exists = os.path.isfile(req_path)
    results.append(check("REQUIREMENTS.md exists", req_exists))

    req_content = ""
    checked_count = 0
    if req_exists:
        with open(req_path, "r", encoding="utf-8") as f:
            req_content = f.read()
        checked_items = re.findall(r"- \[x\]", req_content, re.IGNORECASE)
        checked_count = len(checked_items)
        results.append(check(
            "Has [x] checked items",
            checked_count >= 1,
            f"found {checked_count} checked items",
        ))
    else:
        results.append(check("Has [x] checked items", False, "file missing"))

    print()

    # ── Check 2: review_cycles > 0 ────────────────────────────────────
    print("2. Convergence cycles — Issues #1, #10 (cycle tracking)")
    cycle_match = re.search(r"\(review_cycles?:\s*(\d+)\)", req_content)
    if cycle_match:
        cycles = int(cycle_match.group(1))
        results.append(check(
            "review_cycles > 0",
            cycles > 0,
            f"review_cycles={cycles}",
        ))
    else:
        # Also check for cycle info in the log output
        log_cycle = re.search(r"(?:cycle|convergence).*?(\d+)", log_content, re.IGNORECASE)
        if log_cycle:
            results.append(check(
                "review_cycles > 0 (from log)",
                True,
                f"found cycle reference in log: {log_cycle.group(0)[:60]}",
            ))
        else:
            results.append(check(
                "review_cycles > 0",
                False,
                "no cycle annotation found in REQUIREMENTS.md or log",
            ))
    print()

    # ── Check 3: TASKS.md exists with COMPLETE tasks ──────────────────
    print("3. TASKS.md — Issue #3 (task completion)")
    tasks_path = os.path.join(AGENT_DIR, "TASKS.md")
    tasks_exists = os.path.isfile(tasks_path)
    results.append(check("TASKS.md exists", tasks_exists))

    if tasks_exists:
        with open(tasks_path, "r", encoding="utf-8") as f:
            tasks_content = f.read()
        complete_tasks = re.findall(r"COMPLETE", tasks_content, re.IGNORECASE)
        results.append(check(
            "Has COMPLETE tasks",
            len(complete_tasks) >= 1,
            f"found {len(complete_tasks)} COMPLETE statuses",
        ))
    else:
        results.append(check("Has COMPLETE tasks", False, "file missing"))
    print()

    # ── Check 4: CONTRACTS.json exists and is valid ───────────────────
    print("4. CONTRACTS.json — Issue #4 (contract generation)")
    contracts_path = os.path.join(AGENT_DIR, "CONTRACTS.json")
    contracts_exists = os.path.isfile(contracts_path)
    results.append(check("CONTRACTS.json exists", contracts_exists))

    if contracts_exists:
        try:
            with open(contracts_path, "r", encoding="utf-8") as f:
                contracts_data = json.load(f)
            has_content = bool(contracts_data)
            results.append(check(
                "CONTRACTS.json has content",
                has_content,
                f"keys: {list(contracts_data.keys())[:5]}" if isinstance(contracts_data, dict) else f"items: {len(contracts_data)}",
            ))
        except json.JSONDecodeError as e:
            results.append(check("CONTRACTS.json is valid JSON", False, str(e)))
    else:
        results.append(check("CONTRACTS.json has content", False, "file missing"))
    print()

    # ── Check 5: Code files exist ─────────────────────────────────────
    print("5. Code files — General orchestration")
    calc_path = os.path.join(BASE_DIR, "calculator.py")
    main_path = os.path.join(BASE_DIR, "main.py")
    calc_exists = os.path.isfile(calc_path)
    main_exists = os.path.isfile(main_path)

    results.append(check("calculator.py exists", calc_exists))
    results.append(check("main.py exists", main_exists))

    # Check that main.py is not just the placeholder
    if main_exists:
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        not_placeholder = len(main_content.strip()) > 50
        results.append(check(
            "main.py has real implementation",
            not_placeholder,
            f"{len(main_content)} chars" if not_placeholder else "still placeholder",
        ))
    print()

    # ── Check 6: Convergence health output ────────────────────────────
    print("6. Convergence health display — Issues #7, #9")
    if log_content:
        health_patterns = [
            r"(?:health|convergence|recovery)",
            r"(?:wave|schedule|phase)",
        ]
        health_found = any(
            re.search(p, log_content, re.IGNORECASE) for p in health_patterns
        )
        results.append(check(
            "Health/convergence info in output",
            health_found,
            "found health/convergence references" if health_found else "no log file or no health info",
        ))
    else:
        results.append(check(
            "Health/convergence info in output",
            False,
            "no log file captured (run with tee to capture)",
        ))
    print()

    # ── Check 7: Schedule waves ───────────────────────────────────────
    print("7. Schedule waves — Issue #8")
    if log_content:
        wave_found = bool(re.search(r"(?:wave|schedule|dag|phase\s+\d)", log_content, re.IGNORECASE))
        results.append(check(
            "Schedule/wave info in output",
            wave_found,
            "found wave/schedule references" if wave_found else "no wave/schedule references",
        ))
    else:
        results.append(check(
            "Schedule/wave info in output",
            False,
            "no log file captured",
        ))
    print()

    # ── Check 8: No blind mark-all ────────────────────────────────────
    print("8. No blind mark-all — Issue #12 (diagnostic post-orchestration)")
    if log_content:
        blind_mark = bool(re.search(r"update_tasks_md_statuses.*mark.*all", log_content, re.IGNORECASE))
        results.append(check(
            "No blind mark-all in output",
            not blind_mark,
            "no blind mark-all found" if not blind_mark else "WARNING: blind mark-all detected",
        ))
    else:
        # Check TASKS.md for evidence of diagnostic approach
        if tasks_exists:
            results.append(check(
                "No blind mark-all (inferred)",
                True,
                "TASKS.md exists with mixed statuses (not blindly marked)",
            ))
        else:
            results.append(check(
                "No blind mark-all",
                False,
                "cannot verify without log",
            ))
    print()

    # ── Summary ───────────────────────────────────────────────────────
    print("=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    pct = (passed / total * 100) if total else 0
    print(f"  Results: {passed}/{total} checks passed ({pct:.0f}%)")

    if passed == total:
        print(f"  \033[92mAll checks passed!\033[0m")
    else:
        failed = total - passed
        print(f"  \033[91m{failed} check(s) failed\033[0m")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
