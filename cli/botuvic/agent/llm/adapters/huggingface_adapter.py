"""
Hugging Face adapter using inference API.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter


class HuggingFaceAdapter(BaseLLMAdapter):
    """Adapter for Hugging Face Inference API."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("Hugging Face API key is required")

        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=api_key)
        except ImportError:
            raise ImportError("huggingface_hub package not installed. Run: pip install huggingface_hub")

    def get_provider_name(self) -> str:
        return "HuggingFace"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Hugging Face."""
        self.validate_settings(temperature, max_tokens)

        try:
            response = self.client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            message = response.choices[0].message

            return {
                "content": message.content or "",
                "model": model,
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
        """Get Hugging Face models."""
        return [
            {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct", "name": "Llama 3.1 70B", "provider": "HuggingFace"},
            {"id": "mistralai/Mixtral-8x7B-Instruct-v0.1", "name": "Mixtral 8x7B", "provider": "HuggingFace"},
            {"id": "microsoft/Phi-3-medium-4k-instruct", "name": "Phi-3 Medium", "provider": "HuggingFace"},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 72B", "provider": "HuggingFace"},
        ]
