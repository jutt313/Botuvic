"""
AI21 Labs adapter using their official SDK.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter


class AI21Adapter(BaseLLMAdapter):
    """Adapter for AI21 Labs models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("AI21 Labs API key is required")

        try:
            from ai21 import AI21Client
            self.client = AI21Client(api_key=api_key)
        except ImportError:
            raise ImportError("ai21 package not installed. Run: pip install ai21")

    def get_provider_name(self) -> str:
        return "AI21"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to AI21 Labs."""
        self.validate_settings(temperature, max_tokens)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            message = response.choices[0].message

            return {
                "content": message.content or "",
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
            }

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Authentication" in error_msg:
                raise Exception(f"Invalid {self.get_provider_name()} API Key")
            elif "429" in error_msg:
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get AI21 Labs models."""
        return [
            {"id": "jamba-1.5-large", "name": "Jamba 1.5 Large", "provider": "AI21"},
            {"id": "jamba-1.5-mini", "name": "Jamba 1.5 Mini", "provider": "AI21"},
            {"id": "j2-ultra", "name": "Jurassic-2 Ultra", "provider": "AI21"},
            {"id": "j2-mid", "name": "Jurassic-2 Mid", "provider": "AI21"},
        ]
