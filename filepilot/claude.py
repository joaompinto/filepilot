import os
import json
import re
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from anthropic.types import MessageParam
import shutil
from rich.console import Console
from .changemanager import ChangeManager  # Add this import

console = Console()
verbose_mode = False

class APIAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        self.client = Anthropic(api_key=self.api_key)
        self.last_raw_response = None  # Track last raw response
        self.token_headroom = 1000  # Buffer for safety
        self.max_output_tokens = 4096  # Claude-3 Sonnet's maximum output tokens
        self.max_context_window = 200000  # Claude-3 Sonnet's maximum context window
        self.default_system_message = "You are a helpful assistant who always provides detailed and concise responses."
        self.change_manager = ChangeManager()
        
    def request(self, prompt: str, max_tokens: int = 4000, system: Optional[str] = None) -> str:
        """Send a request to Claude API and get the response.
        
        Args:
            prompt (str): The main message to send to Claude
            max_tokens (int): Maximum tokens in response, defaults to 4000
            system (str, optional): System message to set context
            
        Returns:
            str: Claude's response text
        """
        # Ensure we don't exceed max output tokens
        max_tokens = min(max_tokens, self.max_output_tokens)
        try:
            messages: List[MessageParam] = [{"role": "user", "content": prompt}]
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                system=system or self.default_system_message,
                messages=messages
            )
            self.last_raw_response = response.content[0].text  # Store raw response
            
            if verbose_mode:
                console.print("\n[yellow]Raw API Response:[/yellow]")
                console.print(self.last_raw_response)
                console.print(f"\n[yellow]Max Tokens:[/yellow] {max_tokens}")
                console.print(f"[yellow]Used Tokens:[/yellow] {len(self.last_raw_response.split())}")
            
            return self.last_raw_response
        except Exception as e:
            raise Exception(f"Error in request: {traceback.format_exc()}")

    def check_status(self) -> bool:
        """Check if the Anthropic API is accessible."""
        try:
            # Attempt minimal API call
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            return True
        except Exception as e:
            return False

    def process_file(self, filename: str, prompt: str, max_tokens: int = 4000) -> str:
        """Process a file with Claude API using a specific prompt.
        
        Args:
            filename (str): Path to the file to process
            prompt (str): Prompt template to use with the file content
            max_tokens (int): Maximum tokens in response
            
        Returns:
            str: Claude's analysis of the file
            
        Raises:
            FileNotFoundError: If the file does not exist
            Exception: For other file processing errors
        """
        try:
            # Resolve absolute path
            abs_path = os.path.abspath(os.path.expanduser(filename))
            
            # Validate file existence
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"File not found: {filename}")
            
            # Validate file is readable
            if not os.path.isfile(abs_path):
                raise ValueError(f"Not a file: {filename}")
            
            if not os.access(abs_path, os.R_OK):
                raise PermissionError(f"No permission to read file: {filename}")
            
            # Read file content
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            full_prompt = f"{prompt}\n\nFile content:\n{content}"
            return self.request(full_prompt, max_tokens=max_tokens)
        except (FileNotFoundError, ValueError, PermissionError) as e:
            raise type(e)(str(e))  # Re-raise with same message
        except Exception as e:
            raise Exception(f"Error processing file: {traceback.format_exc()}")

    def create_file_content(self, description: str, max_tokens: int = 4000) -> str:
        """Generate file content based on description using Claude API."""
        prompt = f"""Create a file based on this description: {description}

Requirements:
- Generate only the file content, no explanations or comments outside the code
- Include helpful inline comments where appropriate
- Follow best practices for the file type
- Make the code production-ready and well-structured"""
        
        return self.request(prompt, max_tokens=max_tokens)

    def modify_file_content(self, content: str, instruction: str, max_tokens: Optional[int] = None) -> str:
        if max_tokens is None:
            max_tokens = self.max_output_tokens - self.token_headroom

        max_tokens = min(max_tokens, self.max_output_tokens)
        
        prompt = self.change_manager.generate_change_prompt(content, instruction)
        response = self.request(prompt, max_tokens=max_tokens)
        
        try:
            instructions = self.change_manager.parse_edit_instructions(response, verbose=verbose_mode)
            return self.change_manager.apply_edit_instructions_to_content(content, instructions, verbose=verbose_mode)
        except Exception as e:
            print("Error parsing edit instructions:")
            print(traceback.format_exc())
            return response.strip()

    # Remove _apply_edit_instructions and apply_changes_to_preview methods as they're now in ChangeManager