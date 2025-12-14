"""
Base adapter class that all LLM providers inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseLLMAdapter(ABC):
    """
    Abstract base class for all LLM adapters.
    Each provider implements this interface.
    """
    
    def __init__(self, api_key: str = None, **kwargs):
        """
        Initialize adapter.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific settings
        """
        self.api_key = api_key
        self.settings = kwargs
        self.provider_name = self.get_provider_name()
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name (e.g., 'OpenAI', 'Anthropic')."""
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict with 'content' and optional 'function_call' or 'tool_calls'
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from provider.
        Should fetch from API or official docs, not hardcode.
        
        Returns:
            List of dicts with model info:
            [
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "description": "Latest GPT-4 optimized",
                    "context_window": 128000,
                    "max_output": 4096
                },
                ...
            ]
        """
        pass
    
    def validate_settings(self, temperature: float, max_tokens: int) -> bool:
        """
        Validate settings are within acceptable ranges.
        
        Args:
            temperature: Temperature value
            max_tokens: Max tokens value
            
        Returns:
            True if valid, raises ValueError if not
        """
        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if not 1 <= max_tokens <= 128000:
            raise ValueError("Max tokens must be between 1 and 128000")
        
        return True
    
    def format_messages(self, messages: List[Dict[str, str]]) -> Any:
        """
        Format messages for this provider's API.
        Override if provider needs different format.
        
        Args:
            messages: Standard message format
            
        Returns:
            Provider-specific message format
        """
        return messages
    
    def parse_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse provider's response into standard format.
        Override if provider returns different format.
        
        Args:
            response: Raw provider response
            
        Returns:
            Standardized response dict
        """
        return response

