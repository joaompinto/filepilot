import os
import typer
import traceback
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..claude import APIAgent
from ..changemanager import ChangeManager, NoChangesFoundError
from . import console, app

@app.command()
def change(
    filename: str, 
    instruction: str,
    diff: bool = typer.Option(False, "--diff", "-d", help="Only show diff without applying changes")
):
    """Modify an existing file based on the given instruction."""
    try:
        agent = APIAgent()
        change_manager = ChangeManager()
        
        try:
            # Let ChangeManager handle file operations
            original_content = change_manager.read_file(filename)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                disable=change_manager.verbose
            ) as progress:
                task = progress.add_task("Requesting changes from Claude...", total=None)
                response = agent.get_file_changes(original_content, instruction, filename=filename)
                progress.update(task, completed=True)

            # Process changes through ChangeManager with content
            instructions = change_manager.parse_edit_instructions(response)
            modified_content = change_manager.apply_edit_instructions_to_content(original_content, instructions)
            
            # Let ChangeManager handle preview and diff
            preview_file = change_manager.create_preview_with_content(filename, modified_content)
            
            try:
                diff_count = change_manager.show_diff(filename, preview_file)
                if diff_count > 0:
                    if not diff:
                        change_manager.apply_changes(filename, preview_file)
                else:
                    console.print("[yellow]No changes needed[/yellow]")
            finally:
                change_manager.cleanup_preview(preview_file)

        except Exception as e:
            console.print("[red]Error in change command:[/red]")
            console.print(traceback.format_exc())
            raise typer.Exit(1)
            
    except Exception as e:
        console.print("[red]Error in change command:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)