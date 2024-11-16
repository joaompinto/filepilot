#!/bin/bash

# Build the wheels
python setup.py bdist_wheel

# Build the Docker image
docker build -t filepilot .

# Run the Docker container with the test command
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot analyze /etc/hosts

# Example to test the change command
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY filepilot filepilot change -y /etc/hosts "Add a google dns"