#!/bin/bash
# Colorado 200 - Session Start Hook
# This script runs when a Claude Code session starts or resumes
# It sets up the development environment and ensures dependencies are ready

set -e

echo "=== Colorado 200: Session Initialization ==="

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Check for web app directory
if [ -d "web" ]; then
    echo ">>> Web application detected"
    cd web

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

    # Run linting
    echo ">>> Running linter..."
    npm run lint 2>/dev/null || echo ">>> Linting completed with warnings"

    # Run type checking
    echo ">>> Running TypeScript check..."
    npx tsc --noEmit 2>/dev/null || echo ">>> TypeScript check completed with warnings"

    cd "$PROJECT_DIR"
fi

# Check for root-level package.json
if [ -f "package.json" ] && [ ! -d "web" ]; then
    echo ">>> Checking Node.js dependencies..."

    if [ ! -d "node_modules" ]; then
        echo ">>> Installing dependencies..."
        npm install
    elif [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
        echo ">>> Dependencies outdated, reinstalling..."
        npm install
    else
        echo ">>> Dependencies up to date"
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
if [ -f "web/.env.example" ] && [ ! -f "web/.env" ]; then
    echo ">>> Warning: web/.env file not found. Copy web/.env.example to web/.env and configure."
fi

echo "=== Session initialization complete ==="
exit 0
