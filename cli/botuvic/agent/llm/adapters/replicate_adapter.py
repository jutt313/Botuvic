"""
Replicate adapter using their official SDK.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter


class ReplicateAdapter(BaseLLMAdapter):
    """Adapter for Replicate models."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Replicate API key is required")

        try:
            import replicate
            import os
            os.environ["REPLICATE_API_TOKEN"] = api_key
            self.client = replicate
        except ImportError:
            raise ImportError("replicate package not installed. Run: pip install replicate")

    def get_provider_name(self) -> str:
        return "Replicate"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Replicate."""
        self.validate_settings(temperature, max_tokens)

        try:
            # Convert messages to prompt format
            prompt = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"

            prompt += "Assistant:"

            output = self.client.run(
                model,
                input={
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )

            # Replicate returns a generator or list
            if hasattr(output, '__iter__') and not isinstance(output, str):
                response_text = "".join(str(item) for item in output)
            else:
                response_text = str(output)

            return {
                "content": response_text,
                "model": model,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
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
        """Get Replicate models."""
        return [
            {"id": "meta/meta-llama-3.1-405b-instruct", "name": "Llama 3.1 405B", "provider": "Replicate"},
            {"id": "meta/meta-llama-3-70b-instruct", "name": "Llama 3 70B", "provider": "Replicate"},
            {"id": "mistralai/mixtral-8x7b-instruct-v0.1", "name": "Mixtral 8x7B", "provider": "Replicate"},
        ]
