import os
import shutil
import re
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from typing import List, Dict, Any
from .syntaxdiff import SyntaxDiff

class NoChangesFoundError(Exception):
    """Raised when no change instructions were found in the response."""
    pass

class ChangeManager:
    def __init__(self):
        self.console = Console()
        self.visual_diff = SyntaxDiff()
        self.original_file = None
        # Get verbose setting from environment
        self.verbose = os.getenv('VERBOSE_MODE', '').lower() in ('true', '1', 'yes')

    def read_file(self, filename: str) -> str:
        """Read and validate file content."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File '{filename}' does not exist")
            
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_preview_with_content(self, original_file: str, content: str) -> str:
        """Create preview file with given content."""
        preview_file = self.create_preview_file(original_file)
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return preview_file

    def create_preview_file(self, original_file: str) -> str:
        """Create a preview file using NamedTemporaryFile."""
        self.original_file = original_file  # Set the original file path
        # Get file extension from original file
        _, ext = os.path.splitext(original_file)
        
        # Create temporary file with same extension that won't be deleted when closed
        preview_file = NamedTemporaryFile(suffix=ext, delete=False)
        preview_path = preview_file.name
        
        # Copy original content to temp file
        shutil.copy2(original_file, preview_path)
        
        return preview_path

    def show_diff(self, original_file: str, preview_file: str) -> int:
        """Show visual diff between original and preview files.
        
        Returns:
            int: Number of changes found in the diff
        """
        return self.visual_diff.visualize_diff(original_file, preview_file)

    def apply_changes(self, original_file: str, preview_file: str) -> bool:
        """Apply changes from preview to original file."""
        if self.verbose:
            self.console.print("\n[bold]Applying changes:[/bold]")
            self.console.print(f"Source: {preview_file}")
            self.console.print(f"Destination: {original_file}")

        shutil.copy2(preview_file, original_file)

        if self.verbose:
            self.console.print("[green]Changes applied successfully[/green]")
        else:
            self.console.print(f"[green]✓ Changes applied to {original_file}[/green]")
        return True

    def cleanup_preview(self, preview_file: str):
        """Clean up preview file if it exists."""
        if preview_file and os.path.exists(preview_file):
            try:
                os.unlink(preview_file)
            except OSError:
                pass  # Ignore errors during cleanup

    def generate_change_prompt(self, content: str, instruction: str, target_name: str = None, filename: str = None) -> str:
        """Generate a prompt for Claude that follows the XML format for changes."""
        display_filename = filename or target_name or "file"
        
        prompt = f"""<inputfile>
<filename>{display_filename}</filename>
<content>
{content}
</content>
</inputfile>

Please make the following changes:
{instruction}"""

        return prompt

    def apply_edit_instructions_to_content(self, content: str, instructions: List[Dict[str, Any]]) -> str:
        """Apply edit instructions to content in forward order."""
        # Store whether original content had trailing newline
        had_trailing_newline = content.endswith('\n')
        # Remove trailing whitespace but preserve line endings
        lines = content.rstrip().split('\n')
        
        if self.verbose:
            self.console.print(f"\nFile has {len(lines)} lines")
            self.console.print(f"Applying {len(instructions)} instructions\n")
            
        # Process instructions in forward order    
        for instr in instructions:
            action = instr['action']
            
            try:
                if action == 'replace':
                    if self.verbose:
                        self.console.print(f"\n[yellow]Action:[/yellow] {action}")
                        self.console.print("[green]Replacing entire file:[/green]")
                        self.console.print(f"[green]+ {instr['content']}[/green]")
                    # Return replaced content with newline only if original had one
                    return instr['content'].rstrip() + ('\n' if had_trailing_newline else '')
                    
                elif action == 'delete':
                    start = instr['start'] - 1  # Convert to 0-based index
                    end = instr['end']  # end is inclusive
                    
                    if self.verbose:
                        self.console.print(f"\n[yellow]Action:[/yellow] {action}")
                        self.console.print(f"Range: {start+1}-{end}")
                        deleted_lines = lines[start:end]
                        self.console.print("[red]Deleted content:[/red]")
                        for line in deleted_lines:
                            self.console.print(f"[red]- {line}[/red]")
                    
                    lines = lines[:start] + lines[end:]
                    
                elif action == 'insert':
                    start = instr['start'] - 1 if 'start' in instr else len(lines)
                    
                    if self.verbose:
                        self.console.print(f"\n[yellow]Action:[/yellow] {action}")
                        self.console.print("[green]Inserting:[/green]")
                        self.console.print(f"[green]+ {instr['content']}[/green]")
                    
                    new_lines = instr['content'].split('\n')
                    lines = lines[:start] + new_lines + lines[start:]
                    
                elif action == 'topins':
                    if self.verbose:
                        self.console.print(f"\n[yellow]Action:[/yellow] {action}")
                        self.console.print("[green]Top inserting:[/green]")
                        self.console.print(f"[green]+ {instr['content']}[/green]")
                    
                    new_lines = instr['content'].split('\n')
                    lines = new_lines + lines
                    
            except Exception as e:
                self.console.print(f"[yellow]Warning:[/yellow] {str(e)}")
                continue
                
        result = '\n'.join(lines)
        # Add back trailing newline if original had one
        return result + ('\n' if had_trailing_newline else '')

    def apply_edit_instructions_to_file(self, filename: str, instructions: List[Dict[str, Any]]) -> None:
        """Apply edit instructions to a file."""
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified_content = self.apply_edit_instructions_to_content(content, instructions)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(modified_content)

    def display_instructions_table(self, instructions: List[Dict[str, Any]]) -> None:
        """Display edit instructions in a formatted table."""
        table = Table(
            title="Change Instructions",
            show_header=True,
            header_style="bold cyan",
            box=None
        )
        
        table.add_column("#", style="dim")
        table.add_column("Action", style="yellow")
        table.add_column("Line", justify="right")
        table.add_column("Content")
        
        for idx, instr in enumerate(instructions, 1):
            action = instr.get('action', '')
            line = str(instr.get('line', ''))
            
            if action == 'insert':
                content = f"[green]+ {instr.get('content', '')}[/green]"
            elif action == 'delete':
                content = f"[red]- {instr['count']} lines[/red]"
            else:
                content = ""  # Handle cases where content is not applicable
                
            table.add_row(str(idx), action, line, content)
            
        self.console.print()
        self.console.print(table)
        self.console.print()

    def parse_edit_instructions(self, response: str, original_content: str) -> List[Dict[str, Any]]:
        """Parse edit instructions from response text looking for complete file replacements."""
        instructions = []
        in_file_section = False
        in_content_section = False
        filename = None
        content_lines = []
        
        for line in response.splitlines():
            stripped_line = line.strip()
            
            if '<outputfile>' in stripped_line:
                in_file_section = True
                content_lines = []
                continue
            elif '</outputfile>' in stripped_line:
                if filename and content_lines:
                    instructions.append({
                        'action': 'replace',
                        'content': '\n'.join(content_lines)
                    })
                in_file_section = False
                in_content_section = False
                filename = None
                content_lines = []
                continue
                
            if not in_file_section:
                continue
                
            if '<filename>' in stripped_line and '</filename>' in stripped_line:
                filename = stripped_line[stripped_line.find('<filename>')+10:stripped_line.find('</filename>')].strip()
                continue
                
            if '<content>' in stripped_line:
                in_content_section = True
                continue
            elif '</content>' in stripped_line:
                in_content_section = False
                continue
            
            if in_content_section:
                content_lines.append(line)

        if not instructions:
            raise NoChangesFoundError("No valid change instructions found")

        if self.verbose:
            self.console.print("\n[bold]Parsed Instructions:[/bold]")
            for instr in instructions:
                self.console.print(f"\n[yellow]Action:[/yellow] {instr['action']}")
                self.console.print("[green]New content:[/green]")
                for line in instr['content'].splitlines():
                    self.console.print(f"[green]+ {line}[/green]")

        return instructions