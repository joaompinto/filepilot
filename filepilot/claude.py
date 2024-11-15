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
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        self.client = Anthropic(api_key=self.api_key)
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.change_manager = ChangeManager()
        self.default_system_message = """You are an AI assistant specialized in software development processing file modifications based on natural language descriptions."""

        
    def request(self, prompt: str, max_tokens: int = 4000, system: Optional[str] = None) -> str:
        """Send a request to Claude API and get the response."""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                if VERBOSE:
                    console.print("\n[yellow]Prompt sent to Claude:[/yellow]")
                    console.print("=" * 80)
                    console.print(prompt)
                    console.print("=" * 80)
                
                messages: List[MessageParam] = [{"role": "user", "content": prompt}]
                
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    system=system or self.default_system_message,
                    messages=messages
                )
                
                response_text = response.content[0].text
                
                if VERBOSE:
                    console.print("\n[yellow]Claude Response:[/yellow]")
                    console.print(response_text)
                
                return response_text
                
            except Exception as e:
                last_error = e
                if "rate limit" in str(e).lower():
                    console.print("[yellow]Rate limit hit, waiting...[/yellow]")
                    time.sleep(self.retry_delay * (retries + 1))
                retries += 1
                
        raise Exception(f"Failed after {self.max_retries} retries. Last error: {last_error}")

    def get_file_changes(self, content: str, instruction: str, target_name: str = None, filename: str = None) -> str:
        """Get file changes from Claude using the change protocol."""
        prompt = self.change_manager.generate_change_prompt(content, instruction, target_name, filename)
        return self.request(prompt, system=self.default_system_message)
    
    # Remove _generate_change_prompt as it's now handled by ChangeManager