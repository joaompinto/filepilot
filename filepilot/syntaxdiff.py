
import difflib
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
from pathlib import Path
import sys

class SyntaxDiff:
    def __init__(self, context_lines: int = 3):
        self.console = Console()
        self.context_lines = context_lines

    def visualize_diff(self, file1: str, file2: str) -> int:
        """Show a syntax-highlighted diff between two files.
        Returns number of changes found."""
        try:
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                diff = list(difflib.unified_diff(
                    f1.readlines(),
                    f2.readlines(),
                    fromfile=file1,
                    tofile=file2,
                    n=self.context_lines
                ))
                
            if not diff:
                return 0

            change_count = 0
            current_block = []
            language = Path(file1).suffix.lstrip('.')

            for line in diff:
                if line.startswith('+++') or line.startswith('---'):
                    continue
                elif line.startswith('@@'):
                    if current_block:
                        # Syntax highlight the accumulated block
                        syntax = Syntax('\n'.join(current_block), language, theme="monokai")
                        self.console.print(syntax)
                        current_block = []
                    self.console.print(Text(line.strip(), style="bold cyan"))
                else:
                    if line.startswith('+'):
                        change_count += 1
                        current_block.append(line.rstrip())
                    elif line.startswith('-'):
                        change_count += 1
                        current_block.append(line.rstrip())
                    else:
                        current_block.append(line.rstrip())

            # Print any remaining block
            if current_block:
                syntax = Syntax('\n'.join(current_block), language, theme="monokai")
                self.console.print(syntax)

            return change_count

        except Exception as e:
            self.console.print(f"[red]Error showing diff:[/red] {str(e)}")
            return 0