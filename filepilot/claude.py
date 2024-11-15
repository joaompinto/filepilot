import os
import time
from typing import Optional, List
from anthropic import Anthropic
from anthropic.types import MessageParam
from rich.console import Console
from .changemanager import ChangeManager

VERBOSE = os.getenv('VERBOSE_MODE', '').lower() in ('true', '1', 'yes')
console = Console()

class APIAgent:
    def __init__(self, api_key: Optional[str] = None, system_prompt: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        self.client = Anthropic(api_key=self.api_key)
        self.system_prompt = system_prompt
        self.change_manager = ChangeManager()
        
    def request(self, prompt: str, max_tokens: int = 4000) -> str:
        """Send a request to Claude API and get the response."""
        if VERBOSE:
            console.print("\n[yellow]Prompt sent to Claude:[/yellow]")
            console.print("=" * 80)
            console.print(prompt)
            console.print("=" * 80)
        
        messages: List[MessageParam] = [{"role": "user", "content": prompt}]
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=messages
        )
        
        response_text = response.content[0].text
        
        if VERBOSE:
            console.print("\n[yellow]Claude Response:[/yellow]")
            console.print(response_text)
        
        return response_text

    def get_file_changes(self, content: str, instruction: str, target_name: str = None, filename: str = None) -> str:
        """Get file changes from Claude using the change protocol."""
        prompt = self.change_manager.generate_change_prompt(content, instruction, target_name, filename)
        return self.request(prompt)

    def analyze_file(self, filename: str) -> str:
        """Analyze a file's content and return a summary."""
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.request(f"Here is the file content:\n\n{content}")

    def create_file_content(self, instruction: str, filename: str = None, description: str = None, reference_files: dict = None) -> str:
        """Create new file content based on the instruction and optional parameters."""
        # Build reference files section if provided
        reference_section = ""
        if reference_files:
            for ref_filename, ref_content in reference_files.items():
                reference_section += f"""<inputfile>
<filename>{ref_filename}</filename>
<content>
{ref_content}
</content>
</inputfile>
"""

        prompt = f"""Please create a new file using this format:

<outputfile>
<filename>filename</filename>
<content>
file content
</content>
</outputfile>

File details:
Filename: {filename or 'file'}
{f"Description: {description}" if description else ""}

Requirements:
{instruction}

{reference_section}"""

        response = self.request(prompt)
        
        # Extract content from response using ChangeManager
        instructions = self.change_manager.parse_edit_instructions(response, "")
        if instructions and instructions[0]['action'] == 'replace':
            return instructions[0]['content']
        raise ValueError("Failed to generate valid file content")

    def get_update_suggestions(self, content: str, filename: str, reference_files: dict) -> str:
        """Analyze reference files and suggest updates for the target file."""
        # Build reference files section
        reference_section = ""
        for ref_filename, ref_content in reference_files.items():
            reference_section += f"""<inputfile>
<filename>{ref_filename}</filename>
<content>
{ref_content}
</content>
</inputfile>
"""

        prompt = f"""Target file to update:

<inputfile>
<filename>{filename}</filename>
<content>
{content}
</content>
</inputfile>

Reference files:
{reference_section}

Please analyze the reference files and suggest updates to make the target file consistent with patterns and practices found in the reference files.
Only provide an <outputfile> section if changes are needed."""

        return self.request(prompt)

