"""LLM client wrapper for OpenAI API"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from multiple possible locations
possible_env_paths = [
    Path(__file__).parent.parent.parent.parent.parent / ".env",  # Root project .env
    Path.cwd() / ".env",  # Current directory
    Path.cwd().parent / ".env",  # Parent directory
    Path.home() / ".botuvic" / ".env",  # User config
]

for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    # Try loading from current directory anyway
    load_dotenv()

class LLMClient:
    """Wrapper for OpenAI API calls."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set.\n"
                "Please add OPENAI_API_KEY to your .env file in the project root."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # or gpt-4-turbo
    
    def chat(self, messages, functions=None):
        """
        Send chat request to OpenAI.
        
        Args:
            messages: List of message objects
            functions: Optional list of function definitions
            
        Returns:
            Response dict with content and optional function_call
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        
        if functions:
            kwargs["tools"] = [{"type": "function", "function": f} for f in functions]
            kwargs["tool_choice"] = "auto"
        
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        result = {
            "content": message.content,
        }
        
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
                for tc in message.tool_calls
            ]
        
        return result

