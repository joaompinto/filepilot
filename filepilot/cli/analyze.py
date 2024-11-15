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

SYSTEM_PROMPT = """You are a software developer. Analyze the provided file and provide a concise summary of its purpose.

Important rules:
1. Focus only on what the file does, without listing components
2. Keep the summary between 2-10 sentences
3. Be objective and technical
4. Don't make suggestions or recommendations
5. Don't describe the code structure, focus on functionality
"""

@app.command()
def analyze(filenames: List[str]):
    """Get a concise summary of one or more files' purposes."""
    agent = APIAgent(system_prompt=SYSTEM_PROMPT)

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
                summary = agent.analyze_file(filename)
            
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