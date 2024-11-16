import os
import shutil
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
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
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"File '{filename}' does not exist")
            
        return path.read_text(encoding='utf-8')
    
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

    def create_preview_dir(self, dirname: str) -> str:
        """Create a preview directory for directory structure operations."""
        self.original_file = dirname
        path = Path(dirname)
        
        # Create temporary directory with unique name
        temp_file = NamedTemporaryFile(
            prefix=f"{path.name}_",
            suffix="_preview",
            delete=False
        )
        preview_dir = temp_file.name
        temp_file.close()  # Close and remove the temp file
        Path(preview_dir).unlink(missing_ok=True)  # Remove the file if it exists
        Path(preview_dir).mkdir(parents=True, exist_ok=True)  # Create as directory
        
        return preview_dir

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

    def apply_dir_changes(self, target_dir: str, preview_dir: str) -> bool:
        """Apply changes from preview directory to target directory."""
        if self.verbose:
            self.console.print("\n[bold]Applying directory changes:[/bold]")
            self.console.print(f"Source: {preview_dir}")
            self.console.print(f"Destination: {target_dir}")

        target_path = Path(target_dir)
        if target_path.exists():
            shutil.rmtree(target_path)
        
        # Copy entire directory structure
        shutil.copytree(preview_dir, target_dir)

        if self.verbose:
            self.console.print("[green]Directory structure applied successfully[/green]")
        else:
            self.console.print(f"[green]✓ Directory structure created at[/green] [cyan]{target_dir}[/cyan]")
        return True

    def cleanup_preview(self, preview_file: str):
        """Clean up preview file if it exists."""
        path = Path(preview_file)
        if preview_file and path.exists():
            try:
                path.unlink()
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
                        'filename': filename,  # Include filename in instructions
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
                self.console.print(f"[cyan]File:[/cyan] {instr['filename']}")
                self.console.print("[green]New content:[/green]")
                for line in instr['content'].splitlines():
                    self.console.print(f"[green]+ {line}[/green]")

        return instructions

    def parse_directory_structure(self, xml_content: str) -> dict:
        """Parse XML directory structure into a dictionary representation."""
        structure = {'dirs': [], 'files': []}
        in_structure = False
        in_dir = False
        in_file = False
        current_dir = None
        content_lines = []
        
        for line in xml_content.splitlines():
            stripped_line = line.strip()
            
            if '<structure>' in stripped_line:
                in_structure = True
                continue
            elif '</structure>' in stripped_line:
                in_structure = False
                continue
                
            if not in_structure:
                continue
                
            if '<dir name="' in stripped_line:
                in_dir = True
                dir_name = stripped_line[stripped_line.find('name="')+6:stripped_line.find('">')].strip()
                current_dir = {'name': dir_name, 'dirs': [], 'files': []}
                continue
            elif '</dir>' in stripped_line:
                if current_dir:
                    structure['dirs'].append(current_dir)
                    current_dir = None
                in_dir = False
                continue
                
            if '<file name="' in stripped_line:
                in_file = True
                file_name = stripped_line[stripped_line.find('name="')+6:stripped_line.find('">')]
                content_lines = []
                continue
            elif '</file>' in stripped_line:
                if current_dir:
                    current_dir['files'].append({
                        'name': file_name,
                        'content': '\n'.join(content_lines)
                    })
                else:
                    structure['files'].append({
                        'name': file_name,
                        'content': '\n'.join(content_lines)
                    })
                in_file = False
                continue
                
            if in_file:
                content_lines.append(line)
                
        return structure
        
    def create_directory_structure(self, root_dir: str, structure: dict) -> None:
        """Recursively create directory structure from dictionary representation."""
        root_path = Path(root_dir)
        
        # Create top-level files
        for file_info in structure['files']:
            file_path = root_path / file_info['name']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info['content'], encoding='utf-8')
                
        # Create directories and their contents
        for dir_info in structure['dirs']:
            dir_path = root_path / dir_info['name']
            dir_path.mkdir(parents=True, exist_ok=True)
            self.create_directory_structure(str(dir_path), dir_info)

    def preview_directory_tree(self, path: Path, tree_node) -> None:
        """Build a rich Tree preview of directory structure."""
        for item in sorted(path.iterdir()):
            if item.is_dir():
                branch = tree_node.add(f"[bold cyan]{item.name}/[/bold cyan]")
                self.preview_directory_tree(item, branch)
            else:
                tree_node.add(f"[green]{item.name}[/green]")