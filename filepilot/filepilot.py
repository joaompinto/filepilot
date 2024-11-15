"""
Filepilot is an AI-powered tool for creating, analyzing, and modifying files using Natural Language Processing
It provides a command-line interface (CLI) for interacting with Anthropic's Claude AI
"""
from .cli import app

@app.callback()
def main():
    """Filepilot CLI tool for AI-powered file operations."""
    pass

if __name__ == "__main__":
    app()


