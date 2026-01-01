#!/bin/bash
# Colorado 200 - Session Start Hook
# This script runs when a Claude Code session starts or resumes
# It sets up the development environment and ensures dependencies are ready

set -e

echo "=== Colorado 200: Session Initialization ==="

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Check if package.json exists (web app setup)
if [ -f "package.json" ]; then
    echo ">>> Checking Node.js dependencies..."

    # Check if node_modules exists and is up to date
    if [ ! -d "node_modules" ]; then
        echo ">>> Installing dependencies..."
        npm install
    elif [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
        echo ">>> Dependencies outdated, reinstalling..."
        npm install
    else
        echo ">>> Dependencies up to date"
    fi

    # Run linting if script exists
    if npm run --silent 2>/dev/null | grep -q "lint"; then
        echo ">>> Running linter..."
        npm run lint --silent || echo ">>> Linting completed with warnings"
    fi

    # Run type checking if TypeScript is configured
    if [ -f "tsconfig.json" ]; then
        echo ">>> Running TypeScript check..."
        npm run typecheck --silent 2>/dev/null || npm run tsc --silent 2>/dev/null || echo ">>> TypeScript check skipped"
    fi
fi

# Check for Python environment (if applicable)
if [ -f "requirements.txt" ]; then
    echo ">>> Python environment detected"
    if [ -d "venv" ] || [ -d ".venv" ]; then
        echo ">>> Virtual environment exists"
    else
        echo ">>> Consider creating a virtual environment: python -m venv venv"
    fi
fi

# Display git status
if [ -d ".git" ]; then
    echo ">>> Git Status:"
    git status --short 2>/dev/null || true
    echo ">>> Current branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
fi

# Check for environment file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo ">>> Warning: .env file not found. Copy .env.example to .env and configure."
fi

echo "=== Session initialization complete ==="
exit 0
