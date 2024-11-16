



# Filepilot 🚀✨

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()

Filepilot is an AI-powered tool for creating, analyzing, and modifying files using Natural Language Processing (NLP). It provides a command-line interface (CLI) for interacting with Anthropic's Claude AI assistant using the Claude-3-5-Sonnet model, leveraging its capabilities to generate file content, analyze existing files, and apply edits based on natural language instructions.

## Demo
![Demo](./recording.svg)

## Features ✨

- 🆕 **Create**: Generate new files with AI-generated content based on a description and optional reference files 
- 🔍 **Analyze**: Get a concise summary of a file's main purpose using NLP
- 🚀 **Modify**: Edit existing files by providing natural language instructions, with syntax-highlighted visual diffs for reviewing changes
- 🤖 **Powered by Claude-3**: Harness the power of Anthropic's Claude-3-5-Sonnet model to streamline file operations

## Installation 🛠️

You can install Filepilot using pip:

```bash
pip install filepilot
```

Or install from source:

1. Clone the repository:

```bash
git clone https://github.com/joaompinto/filepilot.git
cd filepilot
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage 📖

The package provides a command-line interface:

```bash
filepilot --help
```

This will display the available commands and options. Here are a few examples:

```bash
# Create a new file
filepilot create README.md "Generate a README file for the Filepilot project"

# Analyze an existing file
filepilot analyze filepilot.py

# Modify an existing file
filepilot change filepilot.py "Add a new feature to handle CSV files"

# Update an existing file from analyzing reference files
filepilot update requirements.txt app.py
```

For detailed diffs and verbose output, you can enable verbose mode:

```bash
export VERBOSE_MODE=true
```

## Contributing 🤝

Contributions are welcome! Please follow the [contributing guidelines](CONTRIBUTING.md) for more information.

## License 📄

This project is licensed under the [MIT License](LICENSE).

For Docker installation and usage instructions, see the [Docker Guide](README.Docker).
