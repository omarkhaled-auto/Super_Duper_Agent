#!/bin/bash

echo "=== Verifying Client-Server Response Fixes ==="
echo ""

# Check for any remaining .data access patterns in hooks
echo "1. Checking for remaining res.data patterns in hooks..."
HOOKS_DIR="client/src/hooks"
if grep -r "res\.data" "$HOOKS_DIR" 2>/dev/null | grep -v "// " | grep -v "/\*"; then
  echo "   ❌ FAILED: Found remaining res.data patterns"
else
  echo "   ✅ PASSED: No res.data patterns found in hooks"
fi
echo ""

# Check TasksResponse interfaces
echo "2. Checking TasksResponse interfaces..."
if grep -r "interface TasksResponse" client/src/hooks/*.ts | grep -q "tasks: Task\[\]"; then
  echo "   ✅ PASSED: TasksResponse uses 'tasks' field"
else
  echo "   ❌ FAILED: TasksResponse still uses 'data' field"
fi
echo ""

# Check Project response
echo "3. Checking Project response patterns..."
if grep -r "api.get<Project>" client/src/hooks/use-project.ts >/dev/null 2>&1; then
  echo "   ✅ PASSED: use-project.ts uses correct type"
else
  echo "   ❌ FAILED: use-project.ts still uses wrapper type"
fi
echo ""

# Check Members response
echo "4. Checking Members response patterns..."
if grep -r "api.get<ProjectMember\[\]>" client/src/hooks/use-members.ts >/dev/null 2>&1; then
  echo "   ✅ PASSED: use-members.ts uses correct type"
else
  echo "   ❌ FAILED: use-members.ts still uses wrapper type"
fi
echo ""

# Check for old response wrapper interfaces
echo "5. Checking for removed wrapper interfaces..."
WRAPPER_COUNT=$(grep -r "interface.*Response" client/src/hooks/*.ts | grep "data:" | wc -l)
if [ "$WRAPPER_COUNT" -eq 0 ]; then
  echo "   ✅ PASSED: No wrapper interfaces with 'data' field found"
else
  echo "   ⚠️  WARNING: Found $WRAPPER_COUNT wrapper interfaces with 'data' field"
fi
echo ""

# Check context files
echo "6. Checking context files..."
if grep -r "api.get<Project>" client/src/contexts/project-context.tsx >/dev/null 2>&1; then
  echo "   ✅ PASSED: project-context.tsx uses correct type"
else
  echo "   ❌ FAILED: project-context.tsx still uses wrapper type"
fi
echo ""

echo "=== Verification Complete ==="
