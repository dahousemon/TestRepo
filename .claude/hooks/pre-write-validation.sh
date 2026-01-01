#!/bin/bash
# Colorado 200 - Pre-Write Validation Hook
# This script runs before Write or Edit tool operations
# It validates that files being written meet project standards

# Don't exit on error - we want to provide feedback
set +e

# Get the file path from environment variable (if available)
FILE_PATH="${CLAUDE_TOOL_INPUT_FILE_PATH:-}"

echo ">>> Pre-write validation"

# If we can't determine the file, allow the write
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension
EXTENSION="${FILE_PATH##*.}"
FILENAME=$(basename "$FILE_PATH")

# Check for potentially dangerous file writes
DANGEROUS_FILES=(
    ".env"
    ".env.local"
    ".env.production"
    "credentials.json"
    "secrets.json"
    ".npmrc"
    "id_rsa"
    "id_ed25519"
)

for dangerous in "${DANGEROUS_FILES[@]}"; do
    if [ "$FILENAME" = "$dangerous" ]; then
        echo ">>> Warning: Writing to sensitive file: $FILENAME"
        echo ">>> Ensure no secrets or credentials are being committed"
    fi
done

# Check for lock files that shouldn't be manually edited
LOCK_FILES=(
    "package-lock.json"
    "yarn.lock"
    "pnpm-lock.yaml"
    "Gemfile.lock"
    "poetry.lock"
)

for lockfile in "${LOCK_FILES[@]}"; do
    if [ "$FILENAME" = "$lockfile" ]; then
        echo ">>> Warning: Modifying lock file: $FILENAME"
        echo ">>> Lock files are typically auto-generated. Consider using package manager commands instead."
    fi
done

# Validate based on file extension
case "$EXTENSION" in
    js|jsx|ts|tsx)
        echo ">>> JavaScript/TypeScript file detected"
        ;;
    json)
        echo ">>> JSON file detected"
        ;;
    md)
        echo ">>> Markdown file detected"
        ;;
    sh)
        echo ">>> Shell script detected"
        ;;
    py)
        echo ">>> Python file detected"
        ;;
    *)
        # No specific validation for other file types
        ;;
esac

# All validations passed
exit 0
