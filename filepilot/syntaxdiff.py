import difflib
from rich.syntax import Syntax
from pathlib import Path

class SyntaxDiff:
    def __init__(self):
        self.extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.sh': 'bash',
            '.bash': 'bash',
            '.sql': 'sql',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
        }
    
    def get_file_language(self, filename: str) -> str:
        """Determine syntax highlighting language based on file extension."""
        ext = Path(filename).suffix.lower()
        return self.extension_map.get(ext, 'text')

    def create_diff(self, filename1: str, filename2: str, show_line_numbers: bool = True) -> tuple[int, str]:
        """Create a syntax-highlighted diff between two files."""
        try:
            with open(filename1, 'r', encoding='utf-8') as f1, \
                 open(filename2, 'r', encoding='utf-8') as f2:
                content1 = f1.readlines()
                content2 = f2.readlines()
        except Exception as e:
            return 0, f"Error reading files: {str(e)}"

        diff = list(difflib.unified_diff(content1, content2, fromfile=filename1, tofile=filename2, lineterm=''))
        if not diff:
            return 0, ""

        language = self.get_file_language(filename1)
        change_count = len([line for line in diff if line.startswith('+') or line.startswith('-')])

        # Create syntax highlighted diff
        diff_text = ''.join(diff)
        syntax = Syntax(
            diff_text,
            "diff",
            theme="monokai",
            line_numbers=show_line_numbers,
            word_wrap=True
        )
        
        return change_count, syntax

# Create a global instance for backwards compatibility
_diff = SyntaxDiff()
create_syntax_diff = _diff.create_diff