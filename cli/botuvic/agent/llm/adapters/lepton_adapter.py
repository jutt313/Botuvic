"""
Lepton AI adapter - OpenAI-compatible API.
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class LeptonAdapter(BaseLLMAdapter):
    """Adapter for Lepton AI models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Lepton AI API key is required")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://llama3-1-405b.lepton.run/api/v1/"
        )

    def get_provider_name(self) -> str:
        return "Lepton"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Lepton AI."""
        self.validate_settings(temperature, max_tokens)

        try:
            tools = kwargs.pop("tools", None)
            tool_choice = kwargs.pop("tool_choice", "auto")

            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = tool_choice

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

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Authentication" in error_msg:
                raise Exception(f"Invalid {self.get_provider_name()} API Key")
            elif "429" in error_msg:
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get Lepton AI models."""
        return [
            {"id": "llama3-1-405b", "name": "Llama 3.1 405B", "provider": "Lepton"},
            {"id": "llama3-1-70b", "name": "Llama 3.1 70B", "provider": "Lepton"},
            {"id": "llama3-1-8b", "name": "Llama 3.1 8B", "provider": "Lepton"},
        ]
