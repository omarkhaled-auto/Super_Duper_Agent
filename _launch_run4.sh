#!/bin/bash
# Run 4 Launch Script
set -e

cd /mnt/c/Projects/claude-agent-team

# Unset CLAUDECODE to prevent nested session errors (known issue from Build 3)
unset CLAUDECODE

# Check claude CLI
echo "=== Claude CLI ==="
which claude 2>/dev/null && claude --version 2>/dev/null || echo "claude CLI not in PATH"

# Check python3
echo "=== Python3 ==="
python3 --version

# Install agent-team in dev mode if not already
echo "=== Installing agent-team ==="
pip3 install -e ".[dev,dotenv]" 2>&1 | tail -3

# Verify import
echo "=== Verify import ==="
python3 -c "from agent_team.cli import main; print('agent_team importable: OK')"

# Verify target directory
echo "=== Target: super-team ==="
ls /mnt/c/Projects/super-team/src/ | head -10

# Verify no stale state
echo "=== Stale state check ==="
if [ -d "/mnt/c/Projects/super-team/.agent-team" ]; then
    echo "WARNING: .agent-team exists, cleaning..."
    rm -rf /mnt/c/Projects/super-team/.agent-team
else
    echo "Clean: no .agent-team/"
fi

echo ""
echo "=== LAUNCHING RUN 4 ==="
echo "Command: python3 -m agent_team --prd prompts/RUN4_PRD.md --config prompts/config_run4.yaml --cwd /mnt/c/Projects/super-team --no-interview"
echo "Start time: $(date)"
echo ""

python3 -m agent_team \
  --prd prompts/RUN4_PRD.md \
  --config prompts/config_run4.yaml \
  --cwd /mnt/c/Projects/super-team \
  --no-interview \
  2>&1

echo ""
echo "=== RUN 4 COMPLETE ==="
echo "End time: $(date)"
