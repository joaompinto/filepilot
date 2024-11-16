#!/bin/bash
set -e  # Exit on error

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable is not set"
    exit 1
fi

echo "Running docker tests..."
./test_docker.sh

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