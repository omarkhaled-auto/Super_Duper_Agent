#!/bin/bash
cd /mnt/c/Projects/claude-agent-team
unset CLAUDECODE

echo "=== PRE-FLIGHT CHECK ==="
echo "1. Python3:"
python3 --version 2>&1

echo "2. Claude CLI:"
claude --version 2>&1 || echo "NOT FOUND"

echo "3. Agent-team install check:"
python3 -c "from agent_team.cli import main; print('OK')" 2>&1 || echo "NEEDS INSTALL"

echo "4. Super-team src dirs:"
ls /mnt/c/Projects/super-team/src/ 2>&1

echo "5. Stale .agent-team:"
test -d /mnt/c/Projects/super-team/.agent-team && echo "EXISTS - STALE" || echo "CLEAN"

echo "6. Config run4 has run4 section:"
grep -c "^run4:" prompts/config_run4.yaml 2>&1

echo "7. PRD paths updated:"
grep "build.*project_root" prompts/RUN4_PRD.md 2>&1 | head -3

echo "=== DONE ==="
