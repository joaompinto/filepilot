#!/bin/bash

# Clean up dist directory
rm -rf dist/

# Build the wheels
python setup.py bdist_wheel

# Build the Docker image
docker build -t filepilot .


# ACTUAL TESTS

# Run analyze test (no -y support)
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot analyze /etc/hosts

# Test change command with -y
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot change -y /etc/hosts "Add a google dns"

# Test create command with -y
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot create -y /tmp/test.txt "A simple text file with hello world content" --force

# Test create with reference files and -y
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot create -y /tmp/new_script.py "A python script that prints hello" /etc/hosts --force

# Test createdir command with -y
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot createdir -y /tmp/testproject "A simple python project with a main file and a utility module" --force

# Test createdir with more complex structure and -y
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot createdir -y /tmp/webapp "A web application with templates, static files, and basic routes" --force