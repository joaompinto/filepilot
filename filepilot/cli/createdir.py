import os
import typer
import traceback
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.tree import Tree
from ..claude import APIAgent
from ..changemanager import ChangeManager
from . import console, app

SYSTEM_PROMPT = """You are a software developer who creates directory structures based on user requirements.
Provide output for each file using this format:

<outputfile>
<filename>path/to/file</filename>
<content>
file content
</content>
</outputfile>

Important:
1. Always output content within XML tags
2. Use proper paths for nested files
3. Include reasonable file content based on file types
"""

@app.command()
def createdir(
    dirname: str,
    description: str,
    force: bool = typer.Option(False, "--force", help="Force overwrite if directory exists"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically create directory without prompting")
):
    """Create a new directory structure with files using AI-generated content."""
    try:
        path = Path(dirname)
        if path.exists() and not force:
            console.print(f"[red]Error:[/red] Directory '{dirname}' already exists. Use --force to overwrite.")
            raise typer.Exit(1)

        agent = APIAgent(system_prompt=SYSTEM_PROMPT)
        change_manager = ChangeManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[blue]Generating structure for {dirname}[/blue]...", total=None)
            response = agent.request(f"Create a directory structure for: {description}")
            progress.update(task, completed=True)

        # Create preview in temporary directory
        preview_dir = change_manager.create_preview_dir(dirname)
        try:
            # Parse response as file changes
            instructions = change_manager.parse_edit_instructions(response, "")
            
            # Show tree preview before creating files
            tree = Tree(f"[bold blue]{dirname}[/bold blue]")
            for instr in instructions:
                if instr['action'] == 'replace':
                    rel_path = Path(instr['filename']).relative_to(dirname) if dirname in instr['filename'] else Path(instr['filename'])
                    parts = rel_path.parts
                    current = tree
                    for i, part in enumerate(parts[:-1]):
                        found = False
                        for node in current.children:
                            if node.label.strip().rstrip('/') == part:
                                current = node
                                found = True
                                break
                        if not found:
                            current = current.add(f"[bold cyan]{part}/[/bold cyan]")
                    current.add(f"[green]{parts[-1]}[/green]")
            
            console.print("\n[blue]Directory structure preview:[/blue]")
            console.print(tree)
            
            if not yes and not Confirm.ask("\nCreate directory structure?"):
                console.print("[yellow]Operation cancelled by user[/yellow]")
                raise typer.Exit(0)
            
            # Create files in preview directory
            for instr in instructions:
                if instr['action'] == 'replace':
                    file_path = Path(preview_dir) / Path(instr['filename']).relative_to(dirname) \
                        if dirname in instr['filename'] else Path(preview_dir) / instr['filename']
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(instr['content'])
            
            # Apply directory changes through change manager
            change_manager.apply_dir_changes(dirname, preview_dir)
            
        finally:
            change_manager.cleanup_preview(preview_dir)
            
    except Exception as e:
        console.print("[red]Error creating directory structure:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)