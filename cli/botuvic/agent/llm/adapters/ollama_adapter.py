"""
Ollama adapter for local models.
"""

import requests
from typing import List, Dict, Any
from .base import BaseLLMAdapter


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama local models."""
    
    def __init__(self, api_key: str = None, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = base_url.rstrip('/')
    
    def get_provider_name(self) -> str:
        return "Ollama"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Ollama."""
        self.validate_settings(temperature, max_tokens)
        
        try:
            # Format messages for Ollama
            # Ollama uses a different format - convert to prompt
            prompt = self._format_messages_to_prompt(messages)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "options": {
                        "num_predict": max_tokens
                    },
                    "stream": False
                },
                timeout=300
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data.get("response", ""),
                "model": model,
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                }
            }
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to Ollama at {self.base_url}. Is Ollama running?")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _format_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to single prompt for Ollama."""
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of locally installed Ollama models."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model in data.get("models", []):
                model_info = model.get("name", "")
                # Remove tag/version info, keep just model name
                model_name = model_info.split(":")[0] if ":" in model_info else model_info
                
                models.append({
                    "id": model_info,  # Keep full name with tag for API calls
                    "name": model_name,
                    "provider": "Ollama",
                    "size": model.get("size", 0),
                    "modified": model.get("modified_at", ""),
                    "description": f"Local {model_name} model"
                })
            
            return models
            
        except requests.exceptions.ConnectionError:
            # Ollama not running, return common models user might have
            return [
                {
                    "id": "llama3",
                    "name": "Llama 3",
                    "provider": "Ollama",
                    "description": "Meta's Llama 3 model (requires local installation)"
                },
                {
                    "id": "mistral",
                    "name": "Mistral",
                    "provider": "Ollama",
                    "description": "Mistral model (requires local installation)"
                },
                {
                    "id": "mixtral",
                    "name": "Mixtral",
                    "provider": "Ollama",
                    "description": "Mixtral model (requires local installation)"
                },
                {
                    "id": "codellama",
                    "name": "CodeLlama",
                    "provider": "Ollama",
                    "description": "Code-focused Llama model (requires local installation)"
                }
            ]
        except Exception as e:
            return []

