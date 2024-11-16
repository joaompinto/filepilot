import difflib
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from pathlib import Path
import sys

class SyntaxDiff:
    def __init__(self, context_lines: int = 3):
        self.console = Console()
        self.context_lines = context_lines

    def visualize_diff(self, file1: str, file2: str) -> int:
        """Show a diff between two files with operation-related colors.
        Returns number of changes found."""
        try:
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                original_lines = f1.readlines()
                original_length = len(original_lines)
                diff = list(difflib.unified_diff(
                    original_lines,
                    f2.readlines(),
                    fromfile=file1,
                    tofile=file2,
                    n=self.context_lines
                ))

            if not diff:
                return 0

            change_count = 0
            added_block = []
            removed_block = []
            removed_line_number = None
            current_position = 0
            file_position = 0  # Track position in the modified file

            for line in diff:
                if line.startswith('+++') or line.startswith('---'):
                    continue
                elif line.startswith('@@'):
                    if added_block or removed_block:
                        self._print_blocks(added_block, removed_block, removed_line_number, file_position, original_length)
                        added_block = []
                        removed_block = []
                    # Parse @@ -start,count +start,count @@ format
                    try:
                        numbers = line.split()
                        file_position = int(numbers[2].split(',')[0].strip('+'))
                    except (IndexError, ValueError):
                        file_position = 0
                    current_position = file_position
                else:
                    if line.startswith('+'):
                        change_count += 1
                        added_block.append(line[1:].rstrip())
                        current_position += 1
                    elif line.startswith('-'):
                        change_count += 1
                        removed_block.append(line[1:].rstrip())
                        if removed_line_number is None:
                            removed_line_number = current_position
                    else:
                        if added_block or removed_block:
                            self._print_blocks(added_block, removed_block, removed_line_number, file_position, original_length)
                            added_block = []
                            removed_block = []
                            removed_line_number = None
                        self.console.print(Text(line[1:].rstrip()))
                        current_position += 1

            if added_block or removed_block:
                self._print_blocks(added_block, removed_block, removed_line_number, file_position, original_length)

            return change_count

        except Exception as e:
            self.console.print(f"[red]Error showing diff:[/red] {str(e)}")
            return 0

    def _print_blocks(self, added_block, removed_block, removed_line_number, position, original_length):
        """Print added and removed blocks with appropriate styling."""
        if removed_block:
            removed_text = "\n".join(removed_block)
            title = f"Removed at {removed_line_number}" if removed_line_number is not None else "Removed"
            self.console.print(Panel(removed_text, title=title, style="red", expand=False))
        if added_block:
            added_text = "\n".join(added_block)
            # Determine head/tail based on position in file
            if position <= self.context_lines:
                title = "Added to head"
            elif position >= original_length - self.context_lines:
                title = "Added to tail"
            else:
                title = "Added"
            self.console.print(Panel(added_text, title=title, style="green", expand=False))

    def _print_context(self, context_block):
        """Print context blocks without panels."""
        for line in context_block:
            self.console.print(Text(line))