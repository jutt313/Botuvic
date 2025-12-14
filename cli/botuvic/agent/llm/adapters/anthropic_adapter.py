"""
Anthropic adapter for Claude models.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        self.client = Anthropic(api_key=api_key)
    
    def get_provider_name(self) -> str:
        return "Anthropic"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Anthropic."""
        self.validate_settings(temperature, max_tokens)
        
        # Separate system message if present
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                # Anthropic uses 'user' and 'assistant' roles
                role = msg["role"]
                if role not in ["user", "assistant"]:
                    role = "user"
                user_messages.append({
                    "role": role,
                    "content": msg["content"]
                })
        
        try:
            # Build request parameters
            params = {
                "model": model,
                "messages": user_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            if system_message:
                params["system"] = system_message
            
            response = self.client.messages.create(**params)
            
            # Extract content
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
                elif isinstance(block, dict) and 'text' in block:
                    content += block['text']
            
            result = {
                "content": content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            # Handle tool use if present
            if hasattr(response, 'content') and response.content:
                for block in response.content:
                    if hasattr(block, 'type') and block.type == 'tool_use':
                        if "tool_calls" not in result:
                            result["tool_calls"] = []
                        result["tool_calls"].append({
                            "id": block.id,
                            "name": block.name,
                            "arguments": block.input
                        })
            
            return result
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available Anthropic models.
        Note: Anthropic doesn't have a models list API endpoint,
        so we return known models and let ModelFinder search for updates.
        """
        # Known Claude models as of Dec 2025
        return [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "description": "Most intelligent model, latest version",
                "context_window": 200000
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "provider": "Anthropic",
                "description": "Powerful model for complex tasks",
                "context_window": 200000
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "description": "Balanced performance and speed",
                "context_window": 200000
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "provider": "Anthropic",
                "description": "Fast and efficient",
                "context_window": 200000
            }
        ]

