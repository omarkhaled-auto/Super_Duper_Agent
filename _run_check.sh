#!/bin/bash
echo "=== Environment Check ==="
echo "Shell: $SHELL"
echo "PATH: $PATH"
echo "Python:"
which python 2>&1 || echo "python not in PATH"
which python3 2>&1 || echo "python3 not in PATH"
python --version 2>&1 || echo "python --version failed"
echo "=== Directories ==="
ls -la C:/Projects/super-team/src/ 2>&1
echo "=== API Key ==="
echo "ANTHROPIC_API_KEY starts with: $(echo $ANTHROPIC_API_KEY | cut -c1-10)"
