"""
Lambda Labs adapter - OpenAI-compatible API.
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class LambdaAdapter(BaseLLMAdapter):
    """Adapter for Lambda Labs models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Lambda Labs API key is required")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.lambdalabs.com/v1"
        )

    def get_provider_name(self) -> str:
        return "Lambda"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Lambda Labs."""
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
        """Get Lambda Labs models."""
        return [
            {"id": "hermes-3-llama-3.1-405b-fp8", "name": "Hermes 3 Llama 3.1 405B", "provider": "Lambda"},
            {"id": "llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "Lambda"},
            {"id": "llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "provider": "Lambda"},
        ]
