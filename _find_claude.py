import shutil, subprocess, os, sys

print(f"Python: {sys.version}")
print(f"Exec: {sys.executable}")
print(f"CWD: {os.getcwd()}")

# Find claude
claude_path = shutil.which("claude")
print(f"claude CLI: {claude_path}")

if claude_path:
    try:
        r = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=10)
        print(f"claude version: {r.stdout.strip()}")
    except Exception as e:
        print(f"claude version error: {e}")

# Check agent_team
try:
    from agent_team.cli import main
    print("agent_team: importable")
except Exception as e:
    print(f"agent_team: {e}")

# Check claude-agent-sdk
try:
    import claude_agent_sdk
    print(f"claude-agent-sdk: {claude_agent_sdk.__version__ if hasattr(claude_agent_sdk, '__version__') else 'installed'}")
except Exception as e:
    print(f"claude-agent-sdk: {e}")
