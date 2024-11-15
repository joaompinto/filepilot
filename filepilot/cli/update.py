
import os
import typer
import traceback
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..claude import APIAgent
from ..changemanager import ChangeManager, NoChangesFoundError
from . import console, app
from typing import List

SYSTEM_PROMPT = """You are a software developer. Analyze reference files to suggest updates to a target file.
Use XML format to specify file content:

<inputfile>
<filename>filename</filename>
<content>
file content
</content>
</inputfile>

Important:
1. Suggest meaningful updates based on reference files
2. Only output changes using <outputfile> tag if needed
3. Keep content separate from tags
"""

@app.command()
def update(
    filename: str,
    reference_files: List[str] = typer.Argument(..., help="Reference files to use for updates"),
    diff: bool = typer.Option(False, "--diff", "-d", help="Only show diff without applying changes")
):
    """Update a file based on reference files."""
    try:
        agent = APIAgent(system_prompt=SYSTEM_PROMPT)
        change_manager = ChangeManager()
        
        # Validate target file exists
        original_content = change_manager.read_file(filename)
        
        # Read reference files
        reference_contents = {}
        if reference_files:
            console.print("\n[blue]Using reference files:[/blue]")
            for ref_file in reference_files:
                if not os.path.exists(ref_file):
                    console.print(f"[red]Error:[/red] Reference file '{ref_file}' does not exist")
                    raise typer.Exit(1)
                ref_size = os.path.getsize(ref_file) / 1024  # Size in KB
                console.print(f"  • [cyan]{ref_file}[/cyan] ({ref_size:.1f} KB)")
                with open(ref_file, 'r', encoding='utf-8') as f:
                    reference_contents[ref_file] = f.read()
            console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=change_manager.verbose
        ) as progress:
            task = progress.add_task("[blue]Analyzing files for updates...[/blue]", total=None)
            response = agent.get_update_suggestions(original_content, filename, reference_contents)
            progress.update(task, completed=True)

        try:
            instructions = change_manager.parse_edit_instructions(response, original_content)
            modified_content = change_manager.apply_edit_instructions_to_content(original_content, instructions)
            
            preview_file = change_manager.create_preview_with_content(filename, modified_content)
            
            try:
                diff_count = change_manager.show_diff(filename, preview_file)
                if diff_count > 0:
                    if not diff:
                        change_manager.apply_changes(filename, preview_file)
                else:
                    console.print("[yellow]No updates needed[/yellow]")
            finally:
                change_manager.cleanup_preview(preview_file)

        except NoChangesFoundError:
            console.print("[yellow]No updates were suggested[/yellow]")

    except Exception as e:
        console.print("[red]Error in update command:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)