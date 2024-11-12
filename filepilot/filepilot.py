# Filepilot is an AI-powered tool for creating, analyzing, and modifying files using Natural Language Processing
# It provides a command-line interface (CLI) for interacting with Anthropic's Claude AI
# Claude's capabilities are leveraged to generate file content, analyze existing files, and apply edits based on natural language instructions
# The tool aims to streamline file operations and enhance productivity by harnessing the power of AI
# It demonstrates how AI can be integrated into software development workflows
# It allows you to create, analyze, and modify files using Claude's natural language processing capabilities
from .claude import APIAgent, verbose_mode  # Add this import
from .changemanager import ChangeManager, NoChangesFoundError  # Update import
import typer
import os
from datetime import datetime
import traceback
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.panel import Panel
from rich.markdown import Markdown
import shutil
from .visualdiff import VisualDiff  # Add this import

# Initialize console
console = Console()

# Initialize Typer app at the top level
app = typer.Typer()

def verbose_callback(value: bool):
    """Callback to set verbose mode"""
    global verbose_mode
    verbose_mode = value

# Add verbose option to the app
@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", 
                                    help="Show raw API responses",
                                    callback=verbose_callback)):
    """Filepilot CLI tool for AI-powered file operations."""
    pass

@app.command()
def analyze(filename: str):
    """Get a concise summary of the file's purpose."""
    try:
        if not os.path.exists(filename):
            console.print(f"[red]Error:[/red] File '{filename}' does not exist")
            raise typer.Exit(1)

        agent = APIAgent()
        prompt = """Analyze this file and provide a very concise summary (2-10 sentences max) explaining its main purpose. 
Focus only on what the file does, without listing components or recommendations."""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(f"[blue]Analyzing {filename}[/blue]...", total=None)
            summary = agent.process_file(filename, prompt)
        
        # Display results
        console.print()
        console.print(Panel(
            Markdown(summary),
            title="Summary",
            expand=False
        ))

        if verbose_mode:
            console.print("\n[dim]Raw API Response:[/dim]")
            console.print(Panel(agent.last_raw_response, expand=False))
            
    except Exception as e:
        console.print("[red]Error analyzing file:[/red]")
        console.print(Panel(str(e), title="Error Details", border_style="red"))
        raise typer.Exit(1)

@app.command()
def status():
    """Check Anthropic API connection status."""
    try:
        agent = APIAgent()
        is_available = agent.check_status()
        typer.echo(f"Anthropic API is {'available' if is_available else 'unavailable'}")
    except ValueError as e:
        print("Error checking API status:")
        print(traceback.format_exc())
        raise typer.Exit(1)

@app.command()
def create(
    filename: str, 
    description: str,
    from_files: str = typer.Option(None, "--from", "-f", help="Comma-separated list of reference files to consider")
):
    """Create a new file using AI-generated content based on description."""
    try:
        if os.path.exists(filename):
            console.print(f"[red]Error:[/red] File '{filename}' already exists")
            raise typer.Exit(1)
            
        agent = APIAgent()
        reference_files = []
        
        # Process reference files if provided
        if from_files:
            reference_files = [f.strip() for f in from_files.split(",")]
            for ref_file in reference_files:
                if not os.path.exists(ref_file):
                    console.print(f"[red]Error:[/red] Reference file '{ref_file}' does not exist")
                    raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[blue]Generating content for {filename}[/blue]...", total=None)
            content = agent.create_file_content(description, reference_files=reference_files)
            progress.update(task, completed=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✓ Successfully created[/green] [cyan]{filename}[/cyan]")
        
    except Exception as e:
        console.print("[red]Error creating file:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)

@app.command()
def change(
    filename: str, 
    instruction: str,
    diff: bool = typer.Option(False, "--diff", "-d", help="Only show diff without applying changes")
):
    """Modify an existing file based on the given instruction."""
    try:
        if not os.path.exists(filename):
            console.print(f"[red]Error:[/red] File '{filename}' does not exist")
            raise typer.Exit(1)
            
        agent = APIAgent()
        change_manager = ChangeManager()
        preview_file = None
        
        try:
            preview_file = change_manager.create_preview_file(filename)
            if verbose_mode:
                console.print(f"\n[blue]Preview file created:[/blue] {preview_file}")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Requesting changes from Claude...", total=None)
                
                # Read original content
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Generate the prompt and get instructions from Claude
                prompt = change_manager.generate_change_prompt(content, instruction)
                response = agent.request(prompt)
                
                # Parse and apply the changes
                instructions = change_manager.parse_edit_instructions(response, verbose=verbose_mode)
                modified_content = change_manager.apply_edit_instructions_to_content(content, instructions, verbose=verbose_mode)
                
                # Write changes to preview file
                with open(preview_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                progress.update(task, completed=True)
            
            # Show diff and apply changes if needed
            change_manager.show_diff(filename, preview_file)
            if not diff:
                change_manager.apply_changes(filename, preview_file)

        except NoChangesFoundError:
            console.print("[yellow]No changes needed:[/yellow] The file already matches the requested changes")
            raise typer.Exit(0)
        except Exception as e:
            console.print("[red]Error in change command:[/red]")
            console.print(traceback.format_exc())
            raise typer.Exit(1)
        finally:
            change_manager.cleanup_preview(preview_file, verbose=verbose_mode)
            
    except Exception as e:
        console.print("[red]Error in change command:[/red]")
        console.print(traceback.format_exc())
        raise typer.Exit(1)

if __name__ == "__main__":
    app()


