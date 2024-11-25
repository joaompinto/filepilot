import os
import fnmatch
import typer
import traceback
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.tree import Tree
from ..claude import APIAgent
from ..changemanager import ChangeManager, NoChangesFoundError
from . import console, app
from ..syntaxdiff import create_syntax_diff

def read_file_safely(filepath: str) -> tuple[bool, str]:
    """Try to read a file with different encodings, return success and content."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
                # Check if content seems like text
                if '\0' in content:  # Binary file check
                    return False, ''
                return True, content
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            return False, ''
    return False, ''

def is_text_file(filepath: str) -> bool:
    """Check if a file is likely to be text-based."""
    # Common text file extensions
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
        '.yaml', '.yml', '.ini', '.conf', '.sh', '.bash', '.zsh', '.fish',
        '.cpp', '.c', '.h', '.hpp', '.java', '.kt', '.rs', '.go', '.rb',
        '.php', '.pl', '.pm', '.r', '.scala', '.sql', '.vue', '.jsx', '.tsx'
    }
    
    # Check extension first
    if Path(filepath).suffix.lower() in text_extensions:
        return True
    
    # Try reading file content
    is_text, _ = read_file_safely(filepath)
    return is_text

SYSTEM_PROMPT = """You are a software developer. Process changes for multiple files based on user instructions.
For files that need changes, you must provide ONLY the output content using this format:

<outputfile>
<filename>filename</filename>
<content>
modified content with requested changes
</content>
</outputfile>

Important:
1. Only include files that need changes
2. Only provide outputfile tags with the modified content
3. Keep XML tags separate from content
4. Process all files in a single response
5. Use the exact filename from the input
"""

@app.command()
def changedir(
    directory: str,
    instruction: str,
    filemask: str = "*",
    diff: bool = typer.Option(False, "--diff", "-d", help="Only show diff without applying changes"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically apply changes without prompting")
):
    """Modify multiple files in a directory based on the given instruction."""
    try:
        agent = APIAgent(system_prompt=SYSTEM_PROMPT)
        change_manager = ChangeManager()
        
        # Find all matching files, excluding .git directories
        matched_files = []
        skipped_files = []
        for root, dirs, files in os.walk(directory):
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in files:
                filepath = os.path.join(root, file)
                if fnmatch.fnmatch(file, filemask):
                    if is_text_file(filepath):
                        matched_files.append(filepath)
                    else:
                        skipped_files.append(filepath)
        
        if skipped_files:
            console.print("[yellow]Skipping binary/non-text files:[/yellow]")
            for file in skipped_files:
                console.print(f"  • [yellow]{os.path.relpath(file, directory)}[/yellow]")
            console.print()

        if not matched_files:
            console.print(f"[yellow]No text files matching '{filemask}' found in '{directory}'[/yellow]")
            raise typer.Exit(0)
            
        # Show statistics instead of individual files
        total_size = sum(os.path.getsize(f) for f in matched_files)
        stats = {
            'Total files': len(matched_files),
            'Skipped files': len(skipped_files),
            'Total size': f"{total_size / 1024:.1f} KB",
            'File types': len(set(Path(f).suffix for f in matched_files))
        }
        
        console.print("\n[bold blue]Files to process:[/bold blue]")
        for key, value in stats.items():
            console.print(f"  • [cyan]{key}:[/cyan] {value}")
        
        if not yes and not Confirm.ask("\nProcess these files?"):
            console.print("[yellow]Operation cancelled by user[/yellow]")
            raise typer.Exit(0)

        # Read all file contents
        files_content = ""
        failed_files = []
        for filename in matched_files[:]:  # Create a copy of the list for iteration
            is_text, content = read_file_safely(filename)
            if is_text:
                files_content += f"\n<inputfile>\n<filename>{filename}</filename>\n<content>\n{content}\n</content>\n</inputfile>\n"
            else:
                failed_files.append(filename)
                matched_files.remove(filename)
        
        if failed_files:
            console.print("[yellow]Failed to read these files (encoding issues):[/yellow]")
            for file in failed_files:
                console.print(f"  • [yellow]{os.path.relpath(file, directory)}[/yellow]")
            console.print()

        if not matched_files:
            console.print(f"[yellow]No readable text files matching '{filemask}' found in '{directory}'[/yellow]")
            raise typer.Exit(0)

        # Request changes for all files at once
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=change_manager.verbose
        ) as progress:
            task = progress.add_task("Requesting changes from Claude...", total=None)
            prompt = f"""Apply the following instruction to all files. For each file that needs changes, show both the original and modified content:

Instruction: {instruction}

Files to process:
{files_content}"""
            response = agent.request(prompt)
            progress.update(task, completed=True)

        # Parse and apply changes - look specifically for outputfile sections
        instructions = change_manager.parse_edit_instructions(response, "")
        changes_found = False
        
        for instr in instructions:
            if instr.get('filename') in matched_files:  # Removed action=='replace' check
                changes_found = True
                filename = instr['filename']
                console.print(f"\n[blue]Processing changes for {filename}...[/blue]")
                
                preview_file = change_manager.create_preview_with_content(filename, instr['content'])
                try:
                    diff_count, diff_output = create_syntax_diff(filename, preview_file)
                    if diff_count > 0:
                        console.print(diff_output)
                        if not diff:
                            if yes:
                                change_manager.apply_changes(filename, preview_file)
                            else:
                                if Confirm.ask(f"\n[bold yellow]Apply changes to {filename}? [y/N]:[/bold yellow]", console=console):
                                    change_manager.apply_changes(filename, preview_file)
                    else:
                        console.print(f"[yellow]No changes needed for {filename}[/yellow]")
                finally:
                    change_manager.cleanup_preview(preview_file)
        
        if not changes_found:
            console.print("\n[yellow]No changes were suggested for any files[/yellow]")

    except Exception as e:
        if not isinstance(e, NoChangesFoundError):
            console.print("[red]Error in changedir command:[/red]")
            console.print(traceback.format_exc())
            raise typer.Exit(1)