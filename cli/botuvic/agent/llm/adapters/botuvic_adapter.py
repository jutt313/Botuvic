"""
BOTUVIC default AI adapter (powered by DeepSeek internally).
This is the default free model that users get without configuring their own API key.
"""

import os
from .deepseek_adapter import DeepSeekAdapter


class BotuvicAdapter(DeepSeekAdapter):
    """
    BOTUVIC's default AI model.
    Internally uses DeepSeek but branded as BOTUVIC.
    Users don't need to provide API key - uses platform's key.
    """

    # Internal: Always use deepseek-chat (DeepSeek V3)
    INTERNAL_MODEL = "deepseek-chat"

    def __init__(self, api_key: str = None, **kwargs):
        """
        Initialize BOTUVIC adapter.

        Args:
            api_key: Not used - uses platform's internal key
            **kwargs: Additional arguments
        """
        # Use platform's DeepSeek key from environment (required)
        platform_key = os.getenv("DEEPSEEK_API_KEY")
        if not platform_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is required for BOTUVIC adapter. "
                "Please set it in your .env file or environment."
            )

        # Initialize with platform key
        super().__init__(api_key=platform_key, **kwargs)

    def get_provider_name(self) -> str:
        """Return provider name - always shows as BOTUVIC"""
        return "BOTUVIC"

    def chat(self, messages, model, **kwargs):
        """
        Override chat to always use internal DeepSeek model.
        """
        # Always use deepseek-chat internally, ignore model parameter
        return super().chat(messages, self.INTERNAL_MODEL, **kwargs)

    def get_available_models(self):
        """
        Return single BOTUVIC model.
        Users only see one option: BOTUVIC AI
        """
        return [
            {
                "id": "botuvic-ai",
                "name": "BOTUVIC AI",
                "description": "Your AI project manager - plans, codes, and deploys",
                "context_window": 64000,
                "supports_tools": True
            }
        ]
