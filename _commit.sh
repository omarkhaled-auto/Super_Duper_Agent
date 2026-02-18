#!/bin/bash
cd "C:/Users/Omar Khaled/OneDrive/Desktop/claude-agent-team"

git add src/agent_team/audit_team.py
git add src/agent_team/__init__.py
git add src/agent_team/state.py
git add src/agent_team/cli.py
git add tests/test_audit_team.py

git commit -m "fix: audit-team v15.1 production hardening — 2C+3H+6M+1L bugs fixed

CRITICAL fixes:
- C1: _RE_FINDING_HEADER regex now accepts trailing text (LLMs add descriptions)
- C2: TestH3 argument order fixed (was passing config as depth)

HIGH fixes:
- H1: Zero-findings with deployed auditors returns unknown health (was false passed)
- H2: parse_all_audit_reports catches UnicodeDecodeError for corrupted files
- H3: audit_team module exported in __init__.py

MEDIUM fixes:
- M1: Document critical health re-run behavior on resume
- M3: Add audit_score/audit_health/audit_fix_rounds to RunState
- M4: Per-milestone audit state stored in RunState.artifacts
- M5: Library auditor skips gracefully when Context7 unavailable
- L4: Remove redundant local traceback imports

Tests: 20 new tests in 8 classes covering all fixes + integration pipeline

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"

echo "COMMIT EXIT: $?"

git push origin master
echo "PUSH EXIT: $?"
