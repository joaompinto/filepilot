from typer import Typer
from rich.console import Console

console = Console()
app = Typer()

@app.callback()
def main():
    """Filepilot CLI tool for AI-powered file operations."""
    pass

# Import commands after app is created
from .analyze import analyze
from .create import create
from .change import change
from .status import status
from .update import update

__all__ = ['app', 'console', 'analyze', 'create', 'change', 'status', 'update']