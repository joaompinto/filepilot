# Filepilot 🚀✨

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()

Filepilot is an AI-powered tool for creating, analyzing, and modifying files using Natural Language Processing (NLP). It provides a command-line interface (CLI) for interacting with Anthropic's Claude AI assistant using the Claude-3-5-Sonnet model, leveraging its capabilities to generate file content, analyze existing files, and apply edits based on natural language instructions. Since Filepilot operates directly on files in your workspace, it seamlessly integrates with any IDE or text editor, maintaining your development workflow while adding AI capabilities.

## Demo
![Demo](https://raw.githubusercontent.com/joaompinto/filepilot/main/recording.svg)

## Features ✨

- 🆕 **Create**: Generate new files with AI-generated content based on a description and optional reference files 
- 📁 **CreateDir**: Create entire directory structures with multiple files
- 🔍 **Analyze**: Get a concise summary of a file's main purpose using NLP
- 🚀 **Modify**: Edit existing files by providing natural language instructions
- 🔄 **Update**: Modify files based on analyzing reference files
- 🤖 **Powered by Claude-3**: Harness the power of Anthropic's Claude-3-5-Sonnet model
- 👀 **Visual Diffs**: Review changes with syntax-highlighted diffs before applying

## Installation 🛠️

Install via pip:
```bash
pip install filepilot
```

Or use Docker:
```bash
docker pull ghcr.io/joaompinto/filepilot
```

Set your API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage 📖

Basic commands:
```bash
# Create a new file
filepilot create app.py "Create a Flask web application with a home route"

# Create a directory structure
filepilot createdir webapp "A web application with templates and routes"

# Analyze files
filepilot analyze app.py config.py

# Modify existing files
filepilot change app.py "Add error handling to the main route"

# Update based on reference files
filepilot update requirements.txt app.py

# Non-interactive mode
filepilot create -y script.py "A script that processes CSV files"
```

Docker usage:
```bash
docker run -it --rm -v $(pwd):/app -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  filepilot filepilot analyze app.py
```

Enable verbose output:
```bash
export VERBOSE_MODE=true
```

## Contributing 🤝

Contributions are welcome! Please follow the [contributing guidelines](CONTRIBUTING.md).

## License 📄

This project is licensed under the [MIT License](LICENSE).

For Docker installation and usage instructions, see the [Docker Guide](README.Docker).