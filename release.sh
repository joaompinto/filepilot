#!/bin/bash
set -e  # Exit on error

# Parse arguments
SKIP_TESTS=false
for arg in "$@"; do
    if [ "$arg" = "--skip-tests" ]; then
        SKIP_TESTS=true
    fi
done

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable is not set"
    exit 1
fi

if [ "$SKIP_TESTS" = false ]; then
    echo "Running docker tests..."
    sh ./test_docker.sh
else
    echo "Skipping tests..."
fi

echo "Cleaning up old distributions..."
rm -rf dist/ build/ *.egg-info

echo "Building distribution packages..."
python -m build

echo "Uploading to PyPI..."
python -m twine upload dist/*

echo "Creating git tag..."
VERSION=$(cat version.txt)
git tag "v$VERSION"
git push origin "v$VERSION"

echo "Release v$VERSION completed successfully!"
