import os
import sys
import subprocess

print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("CWD:", os.getcwd())
print("PATH:", os.environ.get("PATH", "N/A")[:500])
print("ANTHROPIC_API_KEY set:", bool(os.environ.get("ANTHROPIC_API_KEY")))

# Check target directories
for d in [
    "C:/Projects/super-team/src/architect",
    "C:/Projects/super-team/src/super_orchestrator",
    "C:/Projects/super-team/src/integrator",
    "C:/Projects/super-team/src/quality_gate",
    "C:/Projects/super-team/src/build3_shared",
    "C:/Projects/super-team/.agent-team",
    "C:/Projects/agent-team-v15/src/agent_team",
]:
    exists = os.path.isdir(d)
    print(f"  {d}: {'EXISTS' if exists else 'MISSING'}")
