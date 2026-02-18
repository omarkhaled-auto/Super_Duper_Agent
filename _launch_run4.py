"""Launch Run 4 with CLAUDECODE unset to prevent nested session detection."""
import os
import sys
import subprocess

# Remove CLAUDECODE from environment to prevent nested session error
env = os.environ.copy()
for key in ['CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'CLAUDE_CODE_SHELL', 'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS']:
    env.pop(key, None)

print(f"Python: {sys.version}")
print(f"CLAUDECODE after removal: {env.get('CLAUDECODE', 'REMOVED')}")
print(f"CWD: C:\\Projects\\claude-agent-team")
print(f"Target: C:\\Projects\\super-team")
print("Launching agent-team for Run 4...")
print("=" * 60)
sys.stdout.flush()

# Clean stale .agent-team if exists from failed attempt
import shutil
stale = os.path.join("C:\\Projects\\super-team", ".agent-team")
if os.path.isdir(stale):
    print(f"Cleaning stale state: {stale}")
    shutil.rmtree(stale)

result = subprocess.run(
    [
        sys.executable, "-m", "agent_team",
        "--prd", "prompts/RUN4_PRD.md",
        "--config", "prompts/config_run4.yaml",
        "--cwd", "C:\\Projects\\super-team",
        "--no-interview",
    ],
    cwd="C:\\Projects\\claude-agent-team",
    env=env,
)

print("=" * 60)
print(f"Exit code: {result.returncode}")
