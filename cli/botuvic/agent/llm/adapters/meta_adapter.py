"""
Meta Llama adapter - routes to best available provider.
This is a meta-adapter that uses other providers to access Llama models.
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class MetaAdapter(BaseLLMAdapter):
    """
    Meta Llama adapter - routes through Together AI (best performance/price).
    Users can use Together, Groq, Replicate etc. directly for more control.
    """

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("API key is required (use Together AI key)")

        # Default to Together AI as it has best Llama support
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1"
        )

    def get_provider_name(self) -> str:
        return "Meta"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request using Together AI."""
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
                raise Exception(f"Invalid API Key (using Together AI)")
            elif "429" in error_msg:
                raise Exception(f"Rate limit exceeded")
            else:
                raise Exception(f"API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get Meta Llama models (via Together AI)."""
        return [
            {"id": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo", "name": "Llama 3.1 405B Instruct", "provider": "Meta"},
            {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "name": "Llama 3.1 70B Instruct", "provider": "Meta"},
            {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "name": "Llama 3.1 8B Instruct", "provider": "Meta"},
            {"id": "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo", "name": "Llama 3.2 90B Vision", "provider": "Meta"},
            {"id": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo", "name": "Llama 3.2 11B Vision", "provider": "Meta"},
        ]
