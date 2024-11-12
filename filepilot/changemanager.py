import os
import shutil
import json
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
    
    def create_preview_file(self, original_file: str) -> str:
        """Create a preview file using NamedTemporaryFile."""
        # Get file extension from original file
        _, ext = os.path.splitext(original_file)
        
        # Create temporary file with same extension that won't be deleted when closed
        preview_file = NamedTemporaryFile(suffix=ext, delete=False)
        preview_path = preview_file.name
        
        # Copy original content to temp file
        shutil.copy2(original_file, preview_path)
        
        return preview_path

    def show_diff(self, original_file: str, preview_file: str):
        """Show visual diff between original and preview files."""
        self.visual_diff.visualize_diff(original_file, preview_file)

    def apply_changes(self, original_file: str, preview_file: str, verbose_mode: bool = False) -> bool:
        """Apply changes from preview to original file if confirmed."""
        if Confirm.ask("\nDo you want to apply these changes?", console=self.console):
            shutil.copy2(preview_file, original_file)
            self.console.print(f"[green]✓ Changes applied to {original_file}[/green]")
            return True
        else:
            self.console.print("[yellow]Changes discarded[/yellow]")
            return False

    def cleanup_preview(self, preview_file: str, verbose: bool = False):
        """Clean up preview file if it exists."""
        if preview_file and os.path.exists(preview_file):
            try:
                os.unlink(preview_file)
            except OSError:
                pass  # Ignore errors during cleanup

    def generate_change_prompt(self, content: str, instruction: str) -> str:
        """Generate prompt for requesting file changes from AI."""
        return f"""Analyze this file and provide edit instructions according to this request: {instruction}

Requirements:
- Return ONLY a JSON array of edit instructions
- Each instruction must have:
  - "action": "insert", "replace", or "delete"
  - "line": line number to modify (1-based)
  - "content": new content for insert/replace actions
- Don't include unchanged lines
- Keep instructions minimal and focused

Example format:
[
  {{"action": "replace", "line": 5, "content": "def new_method():"}},
  {{"action": "insert", "line": 10, "content": "    return True"}}
]

Original content to modify:
{content}"""

    def apply_edit_instructions_to_content(self, content: str, instructions: List[Dict[str, Any]], verbose: bool = False) -> str:
        """Apply a list of edit instructions to the content."""
        lines = content.splitlines()
        total_lines = len(lines)
        
        # Sort instructions by line number
        instructions.sort(key=lambda x: x.get('line', 0))
        
        if verbose:
            self.console.print("\nApplying edit instructions...")
            self.console.print(f"Total lines in file: {total_lines}")
            self.console.print(f"Number of instructions: {len(instructions)}\n")
        
        for instruction in instructions:
            action = instruction.get('action')
            line_num = max(0, min(instruction.get('line', 1) - 1, total_lines))
            
            if verbose:
                self.console.print(f"Applying {action}:")
                self.console.print(f"  Target line: {line_num + 1}")
                self.console.print(f"  Content: {instruction.get('content', '')}\n")
            
            try:
                if action == 'insert':
                    lines.insert(line_num, instruction.get('content', ''))
                elif action == 'replace' and line_num < len(lines):
                    if verbose:
                        self.console.print(f"  Previous content: {lines[line_num]}")
                    lines[line_num] = instruction.get('content', '')
                elif action == 'delete' and line_num < len(lines):
                    if verbose:
                        self.console.print(f"  Deleting: {lines[line_num]}")
                    del lines[line_num]
            except Exception as e:
                self.console.print(f"Warning: Skipping invalid instruction at line {line_num + 1}:")
                self.console.print(f"Error: {str(e)}")
                continue
        
        return '\n'.join(lines)

    def apply_edit_instructions_to_file(self, filename: str, instructions: List[Dict[str, Any]], verbose: bool = False) -> None:
        """Apply edit instructions to a file."""
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified_content = self.apply_edit_instructions_to_content(content, instructions, verbose)
        
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
            content = instr.get('content', '')
            
            # Style content based on action
            if action == 'insert':
                content = f"[green]+ {content}[/green]"
            elif action == 'delete':
                content = f"[red]- {content}[/red]"
            elif action == 'replace':
                content = f"[yellow]→ {content}[/yellow]"
                
            table.add_row(str(idx), action, line, content)
            
        self.console.print()
        self.console.print(table)
        self.console.print()

    def parse_edit_instructions(self, response: str, verbose: bool = False) -> List[Dict[str, Any]]:
        """Parse edit instructions from API response."""
        json_match = re.search(r'\[.*\]', response.strip(), re.DOTALL)
        if not json_match:
            raise ValueError("No JSON array found in response")
            
        instructions = json.loads(json_match.group())
        
        if not instructions:
            raise NoChangesFoundError("No change instructions found in the response")
        
        if verbose:
            self.display_instructions_table(instructions)
                    
        return instructions