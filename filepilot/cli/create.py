import os
import typer
import traceback
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.panel import Panel
from ..claude import APIAgent
from . import console, app
from typing import Optional, List

@app.command()
def create(
    filename: str, 
    description: str,
    reference_files: List[str] = typer.Argument(None, help="Additional reference files"),
    force: bool = typer.Option(False, "--force", help="Force overwrite if file exists")
):
    """Create a new file using AI-generated content based on description."""
    try:
        if os.path.exists(filename) and not force:
            if not Confirm.ask(f"File '{filename}' already exists. Overwrite?"):
                raise typer.Exit(1)

        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
        agent = APIAgent()
        valid_reference_files = []
        
        # Validate reference files exist and are not directories
        if reference_files:
            for ref_file in reference_files:
                if not os.path.exists(ref_file):
                    console.print(f"[red]Error:[/red] Reference file '{ref_file}' does not exist")
                    raise typer.Exit(1)
                if os.path.isdir(ref_file):
                    console.print(f"[yellow]Warning:[/yellow] Skipping directory '{ref_file}'")
                    continue
                valid_reference_files.append(ref_file)

        # Show reference files that will be used
        if valid_reference_files:
            console.print("\n[blue]Using reference files:[/blue]")
            for ref_file in valid_reference_files:
                ref_size = os.path.getsize(ref_file) / 1024  # Size in KB
                console.print(f"  • [cyan]{ref_file}[/cyan] ({ref_size:.1f} KB)")
            console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[blue]Generating content for {filename}[/blue]...", total=None)
            content = agent.create_file_content(
                description=f"Create file '{filename}': {description}",
                reference_files=valid_reference_files
            )
            progress.update(task, completed=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✓ Successfully created[/green] [cyan]{filename}[/cyan]")
        
    except Exception as e:
        console.print("[red]Error creating file:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)