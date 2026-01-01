#!/bin/bash
# Colorado 200 - Post-Bash Check Hook
# This script runs after Bash tool operations
# It performs post-execution checks and cleanup

set +e

echo ">>> Post-bash execution check"

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Check if any new dependencies were installed
if [ -f "package.json" ] && [ -d "node_modules" ]; then
    # Check if package-lock.json was modified recently (last 60 seconds)
    if [ -f "package-lock.json" ]; then
        LOCK_MOD_TIME=$(stat -c %Y "package-lock.json" 2>/dev/null || stat -f %m "package-lock.json" 2>/dev/null)
        CURRENT_TIME=$(date +%s)
        TIME_DIFF=$((CURRENT_TIME - LOCK_MOD_TIME))

        if [ "$TIME_DIFF" -lt 60 ]; then
            echo ">>> Note: package-lock.json was recently modified"
            echo ">>> Consider committing lock file changes if new dependencies were added"
        fi
    fi
fi

# Check for uncommitted changes if git is available
if [ -d ".git" ]; then
    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l)
    if [ "$UNCOMMITTED" -gt 0 ]; then
        echo ">>> There are $UNCOMMITTED uncommitted changes in the repository"
    fi
fi

# Check for any error logs created
if [ -f "npm-debug.log" ]; then
    echo ">>> Warning: npm-debug.log found - there may have been npm errors"
fi

if [ -f "yarn-error.log" ]; then
    echo ">>> Warning: yarn-error.log found - there may have been yarn errors"
fi

exit 0
