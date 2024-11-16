import os
import typer
import traceback
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from ..claude import APIAgent
from ..changemanager import ChangeManager, NoChangesFoundError
from . import console, app

SYSTEM_PROMPT = """You are a software developer. Process a request for changes to files using this format:

Files are specified using XML tags:

<inputfile>
<filename>filename</filename>
<content>
file content
</content>
</inputfile>

Note: If you provide an <outputfile> section, the entire file will be replaced with that content.

Important:
1. Only output the changes
2. do not mix tags with content
"""

@app.command()
def change(
    filename: str, 
    instruction: str,
    diff: bool = typer.Option(False, "--diff", "-d", help="Only show diff without applying changes"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically apply changes without prompting")
):
    """Modify an existing file based on the given instruction."""
    try:
        agent = APIAgent(system_prompt=SYSTEM_PROMPT)
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

            try:
                # Pass original_content to parse_edit_instructions
                instructions = change_manager.parse_edit_instructions(response, original_content)
                modified_content = change_manager.apply_edit_instructions_to_content(original_content, instructions)
                
                # Let ChangeManager handle preview and diff
                preview_file = change_manager.create_preview_with_content(filename, modified_content)
                
                try:
                    diff_count = change_manager.show_diff(filename, preview_file)
                    if diff_count > 0:
                        if not diff:
                            if yes:
                                change_manager.apply_changes(filename, preview_file)
                            else:
                                console.print("")
                                if Confirm.ask("[bold yellow]Do you want to apply these changes? [y/N]:[/bold yellow]", console=console):
                                    change_manager.apply_changes(filename, preview_file)
                    else:
                        console.print("[yellow]No changes needed[/yellow]")
                finally:
                    change_manager.cleanup_preview(preview_file)

            except NoChangesFoundError:
                console.print("[yellow]No changes were suggested by Claude[/yellow]")

        except Exception as e:
            if not isinstance(e, NoChangesFoundError):
                console.print("[red]Error in change command:[/red]")
                console.print(traceback.format_exc())
                raise typer.Exit(1)
            
    except Exception as e:
        if not isinstance(e, NoChangesFoundError):
            console.print("[red]Error in change command:[/red]")
            console.print(traceback.format_exc())
            raise typer.Exit(1)