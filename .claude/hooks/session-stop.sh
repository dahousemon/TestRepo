#!/bin/bash
# Colorado 200 - Session Stop Hook
# This script runs when Claude Code finishes responding
# It performs final checks and cleanup

set +e

echo "=== Colorado 200: Session Stop Check ==="

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Check git status
if [ -d ".git" ]; then
    echo ">>> Git Repository Status:"

    # Show current branch
    BRANCH=$(git branch --show-current 2>/dev/null)
    echo "    Branch: $BRANCH"

    # Count uncommitted changes
    STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
    UNSTAGED=$(git diff --name-only 2>/dev/null | wc -l)
    UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

    if [ "$STAGED" -gt 0 ]; then
        echo "    Staged files: $STAGED"
    fi

    if [ "$UNSTAGED" -gt 0 ]; then
        echo "    Modified files: $UNSTAGED"
    fi

    if [ "$UNTRACKED" -gt 0 ]; then
        echo "    Untracked files: $UNTRACKED"
    fi

    TOTAL=$((STAGED + UNSTAGED + UNTRACKED))
    if [ "$TOTAL" -eq 0 ]; then
        echo "    Working directory clean"
    else
        echo "    Total uncommitted changes: $TOTAL"
    fi

    # Check if ahead of remote
    git fetch origin "$BRANCH" --quiet 2>/dev/null
    AHEAD=$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo "0")
    if [ "$AHEAD" -gt 0 ]; then
        echo "    Commits ahead of origin: $AHEAD (consider pushing)"
    fi
fi

# Run linting if available (quick check)
if [ -f "package.json" ]; then
    if npm run --silent 2>/dev/null | grep -q "lint"; then
        echo ">>> Running quick lint check..."
        npm run lint --silent 2>/dev/null && echo "    Linting passed" || echo "    Linting has warnings/errors"
    fi
fi

# Check for TODO comments added in recent changes
if [ -d ".git" ]; then
    TODOS=$(git diff HEAD~1 2>/dev/null | grep -c "TODO\|FIXME\|HACK" || echo "0")
    if [ "$TODOS" -gt 0 ]; then
        echo ">>> Note: $TODOS TODO/FIXME/HACK comments found in recent changes"
    fi
fi

echo "=== Session stop check complete ==="
exit 0
