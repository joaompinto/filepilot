import difflib
import sys
from typing import List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SQUARE

class VisualDiff:
    def __init__(self, context_lines: int = 3):
        self.console = Console()
        self.context_lines = context_lines

    def read_file(self, filename: str) -> str:
        try:
            with open(filename, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            sys.exit(1)
            
    def get_changes(self, text1: str, text2: str) -> List[Tuple[int, str, str, bool]]:
        """Return a list of (line_number, line1, line2, is_different) tuples"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        changes = []
        last_line = -1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            # Add context before if there's a gap
            if i1 > last_line + 1:
                # Add ellipsis for gaps larger than context
                if i1 > last_line + self.context_lines + 2:
                    changes.append((-1, "...", "...", False))
                
                # Add context lines before change
                start = max(last_line + 1, i1 - self.context_lines)
                for i in range(start, i1):
                    changes.append((i + 1, lines1[i], lines1[i], False))
            
            # Handle the changes based on operation type
            if tag == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    old = lines1[i1 + k] if i1 + k < i2 else ""
                    new = lines2[j1 + k] if j1 + k < j2 else ""
                    changes.append((i1 + k + 1, old, new, True))
            elif tag == 'delete':
                for i in range(i1, i2):
                    changes.append((i + 1, lines1[i], "", True))
            elif tag == 'insert':
                for j in range(j1, j2):
                    changes.append((i1 + 1, "", lines2[j], True))
            elif tag == 'equal':
                # Only add equal lines if they're within context range of a change
                if len(changes) > 0 and changes[-1][3]:  # If last line was a change
                    for i in range(i1, min(i1 + self.context_lines, i2)):
                        changes.append((i + 1, lines1[i], lines2[i], False))
            
            last_line = i2 - 1
            
        return changes

    def visualize_diff(self, file1: str, file2: str):
        """Display a visual diff between two files showing only changed sections."""
        text1 = self.read_file(file1)
        text2 = self.read_file(file2)
        changes = self.get_changes(text1, text2)
        
        # Create table for changes
        table = Table(
            title="File Changes",
            box=SQUARE,
            show_header=True,
            header_style="bold cyan",
            show_lines=False,
            padding=(0, 1)
        )
        
        table.add_column("Line", style="dim", justify="right")
        table.add_column("Changes")
        
        in_change_block = False
        
        for line_num, old, new, is_different in changes:
            # Handle ellipsis
            if line_num == -1:
                table.add_row("...", "...")
                continue
                
            # Format the line display
            if is_different:
                if not old:
                    table.add_row(str(line_num), Text(f"+ {new}", style="green"))
                elif not new:
                    table.add_row(str(line_num), Text(f"- {old}", style="red"))
                    table.add_row("", Text(f"+ {new}", style="green"))
                else:
                    table.add_row(str(line_num), Text(f"- {old}", style="red"))
                    table.add_row("", Text(f"+ {new}", style="green"))
            else:
                table.add_row(str(line_num), Text(f"  {old}"))

        
        # Print the changes
        self.console.print(table)
    