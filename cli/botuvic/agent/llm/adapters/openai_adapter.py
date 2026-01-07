"""
OpenAI adapter for GPT models.
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=api_key)
    
    def get_provider_name(self) -> str:
        return "OpenAI"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to OpenAI."""
        self.validate_settings(temperature, max_tokens)
        
        try:
            # Prepare tools if provided
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
            
            # Handle tool calls if present
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
                raise Exception(f"Invalid {self.get_provider_name()} API Key. Please check your key at the provider's dashboard.")
            elif "402" in error_msg or "insufficient_quota" in error_msg:
                raise Exception(f"Insufficient balance in your {self.get_provider_name()} account.")
            elif "429" in error_msg:
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}. Please try again in a moment.")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available OpenAI models from API.
        """
        try:
            models_response = self.client.models.list()
            
            # Filter to chat models only
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                
                # Only include GPT/o-series models
                if any(prefix in model_id for prefix in ['gpt', 'o1', 'o3']):
                    chat_models.append({
                        "id": model_id,
                        "name": model_id.upper().replace('-', ' ').replace('_', ' '),
                        "provider": "OpenAI",
                        "created": model.created,
                        "owned_by": model.owned_by
                    })
            
            # Sort by creation date (newest first)
            chat_models.sort(key=lambda x: x.get("created", 0), reverse=True)
            
            return chat_models
            
        except Exception as e:
            # Fallback to known models if API fails
            return [
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "provider": "OpenAI",
                    "description": "Latest GPT-4 optimized model",
                    "context_window": 128000
                },
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "OpenAI",
                    "description": "Faster and cheaper GPT-4o",
                    "context_window": 128000
                },
                {
                    "id": "gpt-4-turbo",
                    "name": "GPT-4 Turbo",
                    "provider": "OpenAI",
                    "description": "GPT-4 with improved performance",
                    "context_window": 128000
                },
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "provider": "OpenAI",
                    "description": "GPT-4 base model",
                    "context_window": 8192
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "OpenAI",
                    "description": "Fast and efficient model",
                    "context_window": 16385
                }
            ]

