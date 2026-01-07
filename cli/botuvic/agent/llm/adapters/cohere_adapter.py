"""
Cohere adapter using their official SDK.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter


class CohereAdapter(BaseLLMAdapter):
    """Adapter for Cohere models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Cohere API key is required")

        try:
            import cohere
            self.client = cohere.Client(api_key)
        except ImportError:
            raise ImportError("cohere package not installed. Run: pip install cohere")

    def get_provider_name(self) -> str:
        return "Cohere"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Cohere."""
        self.validate_settings(temperature, max_tokens)

        try:
            # Convert messages to Cohere format
            chat_history = []
            message_text = ""

            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")

                if role == "system":
                    # Cohere uses preamble for system messages
                    kwargs["preamble"] = content
                elif role == "user":
                    if chat_history:  # Not the first user message
                        chat_history.append({"role": "USER", "message": content})
                    else:
                        message_text = content  # First user message goes to message param
                elif role == "assistant":
                    chat_history.append({"role": "CHATBOT", "message": content})

            response = self.client.chat(
                model=model,
                message=message_text,
                chat_history=chat_history if chat_history else None,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return {
                "content": response.text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.meta.get("tokens", {}).get("input_tokens", 0),
                    "completion_tokens": response.meta.get("tokens", {}).get("output_tokens", 0),
                    "total_tokens": response.meta.get("tokens", {}).get("input_tokens", 0) +
                                   response.meta.get("tokens", {}).get("output_tokens", 0)
                }
            }

        except Exception as e:
            error_msg = str(e)
            if "invalid api token" in error_msg.lower():
                raise Exception(f"Invalid {self.get_provider_name()} API Key")
            elif "rate limit" in error_msg.lower():
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get Cohere models."""
        return [
            {"id": "command-r-plus", "name": "Command R+", "provider": "Cohere"},
            {"id": "command-r", "name": "Command R", "provider": "Cohere"},
            {"id": "command", "name": "Command", "provider": "Cohere"},
            {"id": "command-light", "name": "Command Light", "provider": "Cohere"},
        ]
