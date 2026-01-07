"""
Perplexity adapter - OpenAI-compatible API.
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class PerplexityAdapter(BaseLLMAdapter):
    """Adapter for Perplexity AI models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Perplexity API key is required")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

    def get_provider_name(self) -> str:
        return "Perplexity"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Perplexity."""
        self.validate_settings(temperature, max_tokens)

        try:
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            response = self.client.chat.completions.create(**request_params)
            message = response.choices[0].message

            result = {
                "content": message.content or "",
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            return result

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Authentication" in error_msg:
                raise Exception(f"Invalid {self.get_provider_name()} API Key")
            elif "429" in error_msg:
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get Perplexity models."""
        return [
            {"id": "llama-3.1-sonar-large-128k-online", "name": "Sonar Large 128K (Online)", "provider": "Perplexity"},
            {"id": "llama-3.1-sonar-small-128k-online", "name": "Sonar Small 128K (Online)", "provider": "Perplexity"},
            {"id": "llama-3.1-sonar-large-128k-chat", "name": "Sonar Large 128K (Chat)", "provider": "Perplexity"},
            {"id": "llama-3.1-sonar-small-128k-chat", "name": "Sonar Small 128K (Chat)", "provider": "Perplexity"},
        ]
