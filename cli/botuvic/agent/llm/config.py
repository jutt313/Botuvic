"""
LLM configuration and settings management.
"""

from typing import Dict, Any


class LLMConfig:
    """
    Manages LLM configuration and settings.
    Provides validation and defaults.
    """
    
    # Default settings for all LLMs
    DEFAULT_SETTINGS = {
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }
    
    # Setting constraints
    CONSTRAINTS = {
        "temperature": {"min": 0.0, "max": 2.0},
        "max_tokens": {"min": 1, "max": 128000},
        "top_p": {"min": 0.0, "max": 1.0},
        "frequency_penalty": {"min": -2.0, "max": 2.0},
        "presence_penalty": {"min": -2.0, "max": 2.0},
    }
    
    # Provider-specific settings
    PROVIDER_SETTINGS = {
        "OpenAI": {
            "supports_function_calling": True,
            "supports_streaming": True,
            "default_model": "gpt-4o"
        },
        "Anthropic": {
            "supports_function_calling": True,
            "supports_streaming": True,
            "default_model": "claude-3-5-sonnet-20241022"
        },
        "Ollama": {
            "supports_function_calling": False,
            "supports_streaming": True,
            "default_model": "llama3"
        }
    }
    
    @classmethod
    def get_default_settings(cls) -> Dict[str, Any]:
        """Get default settings."""
        return cls.DEFAULT_SETTINGS.copy()
    
    @classmethod
    def validate_setting(cls, setting_name: str, value: Any) -> bool:
        """
        Validate a setting value.
        
        Args:
            setting_name: Name of setting
            value: Value to validate
            
        Returns:
            True if valid, raises ValueError if not
        """
        if setting_name not in cls.CONSTRAINTS:
            # Unknown setting, allow it
            return True
        
        constraints = cls.CONSTRAINTS[setting_name]
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"{setting_name} must be a number")
        
        if value < constraints["min"] or value > constraints["max"]:
            raise ValueError(
                f"{setting_name} must be between {constraints['min']} and {constraints['max']}"
            )
        
        return True
    
    @classmethod
    def validate_settings(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all settings.
        
        Args:
            settings: Settings dict to validate
            
        Returns:
            Validated settings
        """
        validated = {}
        
        for key, value in settings.items():
            cls.validate_setting(key, value)
            validated[key] = value
        
        return validated
    
    @classmethod
    def get_provider_capabilities(cls, provider: str) -> Dict[str, Any]:
        """
        Get capabilities for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dict with provider capabilities
        """
        return cls.PROVIDER_SETTINGS.get(provider, {})

