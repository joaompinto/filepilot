"""Change Manager Protocol

Changes are described using XML-like tags:

<insert n>       # insert at line n
content to add    # can be multiple lines
</insert>

<delete n>       # single line delete
</delete>

<delete n-m>     # range delete
</delete>

Example:
<insert 5>
def new_method():
    return True
</insert>

<delete 10>  # deletes line 10
</delete>

<delete 15-20>  # deletes lines 15 through 20
</delete>
"""

import os
import shutil
import re
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from typing import List, Dict, Any
from .visualdiff import VisualDiff

class NoChangesFoundError(Exception):
    """Raised when no change instructions were found in the response."""
    pass

class ChangeManager:
    def __init__(self):
        self.console = Console()
        self.visual_diff = VisualDiff()
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
        """Apply changes from preview to original file if confirmed."""
        if Confirm.ask("\nDo you want to apply these changes?", console=self.console):
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
        else:
            self.console.print("[yellow]Changes discarded[/yellow]")
            return False

    def cleanup_preview(self, preview_file: str):
        """Clean up preview file if it exists."""
        if preview_file and os.path.exists(preview_file):
            try:
                os.unlink(preview_file)
            except OSError:
                pass  # Ignore errors during cleanup

    def generate_change_prompt(self, content: str, instruction: str, target_name: str = None, filename: str = None) -> str:
        """Generate prompt for requesting file changes from AI."""
        import uuid
        
        file_marker = f"###FILEPILOT_CONTENT_{uuid.uuid4().hex[:8]}###"
        escaped_content = content.strip().replace(file_marker, f"\\{file_marker}")
        
        display_name = filename or target_name or "the file"
        
        # Prefix each line with its line number
        numbered_content = "\n".join(f"{i+1}: {line}" for i, line in enumerate(escaped_content.split('\n')))

        return f"""<file_content>
{numbered_content}
</file_content>

<filename>
{display_name}
</filename>

<change_description>
{instruction}
</change_description>"""

    def apply_edit_instructions_to_content(self, content: str, instructions: List[Dict[str, Any]]) -> str:
        """Apply edit instructions to content."""
        lines = content.rstrip('\n').split('\n')
        
        if self.verbose:
            self.console.print(f"\nFile has {len(lines)} lines")
            self.console.print(f"Applying {len(instructions)} instructions in sorted order:\n")
            self.display_instructions_table(instructions)
            
        for instr in instructions:
            action = instr.get('action')
            text = instr.get('text')
            
            try:
                if action == 'remove':
                    lines = [line for line in lines if text not in line]
                    
                elif action == 'insert':
                    new_lines = instr.get('content', '').rstrip('\n').split('\n')
                    for i, line in enumerate(lines):
                        if text in line:
                            lines = lines[:i+1] + new_lines + lines[i+1:]
                            break
                    
                elif action == 'replace':
                    new_lines = instr.get('content', '').rstrip('\n').split('\n')
                    lines = [line.replace(text, '\n'.join(new_lines)) if text in line else line for line in lines]
                    
            except Exception as e:
                self.console.print(f"[yellow]Warning:[/yellow] {str(e)}")
                continue
                
        return '\n'.join(lines) + '\n'

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
                content = f"[red]- {instr.get('count')} lines[/red]"
            else:
                content = ""  # Handle cases where content is not applicable
                
            table.add_row(str(idx), action, line, content)
            
        self.console.print()
        self.console.print(table)
        self.console.print()

    def display_changes_summary(self, instructions: List[Dict[str, Any]], total_lines: int) -> None:
        """Display a human-readable summary of the changes."""
        deletions = len([i for i in instructions if i['action'] == 'remove'])
        insertions = len([i for i in instructions if i['action'] == 'insert'])
        affected_texts = sorted(set([i['text'] for i in instructions]))
        
        self.console.print("\n[bold]Change Summary:[/bold]")
        self.console.print(f"Total lines in file: {total_lines}")
        self.console.print(f"Changes to be made: {len(instructions)}")
        self.console.print(f"  - Deletions: {deletions}")
        self.console.print(f"  - Insertions: {insertions}")
        self.console.print(f"Texts affected: {', '.join(affected_texts)}\n")

    def parse_edit_instructions(self, response: str) -> List[Dict[str, Any]]:
        """Parse edit instructions from response text."""
        instructions = []
        if self.verbose:
            self.console.print("\n[bold]Change Instructions:[/bold]")
            self.console.print(response)

        # Parse modifications tags
        modifications_pattern = r'<modifications>(.*?)</modifications>'
        modifications_match = re.search(modifications_pattern, response, re.DOTALL)
        if not modifications_match:
            raise NoChangesFoundError("No valid change instructions found")

        modifications_content = modifications_match.group(1)

        # Parse individual change tags
        change_pattern = r'<change\s+type="(remove|insert|replace)">\s*<text>(.*?)</text>\s*<content>(.*?)</content>\s*</change>'
        for match in re.finditer(change_pattern, modifications_content, re.DOTALL):
            action = match.group(1)
            text = match.group(2).strip()
            content = match.group(3).strip()

            if not text:
                if self.verbose:
                    self.console.print(f"[yellow]Warning:[/yellow] Invalid text for change")
                continue

            # Handle multi-line content with line numbers
            if action == 'replace' and '\n' in content:
                content_lines = content.split('\n')
                content = '\n'.join(line.split(': ', 1)[1] if ': ' in line else line for line in content_lines)

            instructions.append({
                'action': action,
                'text': text,
                'content': content
            })

        if not instructions:
            raise NoChangesFoundError("No valid change instructions found")

        if self.verbose:
            self.display_changes_summary(instructions, 0)

        return instructions