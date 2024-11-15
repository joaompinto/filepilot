import os
import typer
from typing import List
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..claude import APIAgent
from . import console, app

# Check verbose mode from environment
VERBOSE = os.getenv('VERBOSE_MODE', '').lower() in ('true', '1', 'yes')

@app.command()
def analyze(filenames: List[str]):
    """Get a concise summary of one or more files' purposes."""
    agent = APIAgent()
    prompt = """Analyze this file and provide a very concise summary (2-10 sentences max) explaining its main purpose. 
Focus only on what the file does, without listing components or recommendations."""

    for idx, filename in enumerate(filenames):
        try:
            if idx > 0:
                console.print()  # Add spacing between files
                
            if not os.path.exists(filename):
                console.print(f"[red]Error:[/red] File '{filename}' does not exist")
                continue

            # Skip directories silently
            if os.path.isdir(filename):
                continue

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task(f"[blue]Analyzing {filename}[/blue]...", total=None)
                summary = agent.process_file(filename, prompt)
            
            console.print()
            console.print(Panel(
                Markdown(summary),
                title=f"Summary: {filename}",
                expand=False
            ))

            if VERBOSE:
                console.print("\n[dim]Raw API Response:[/dim]")
                console.print(Panel(agent.last_raw_response, expand=False))
                
        except Exception as e:
            console.print(f"[red]Error analyzing {filename}:[/red]")
            console.print(Panel(str(e), title="Error Details", border_style="red"))
            continue