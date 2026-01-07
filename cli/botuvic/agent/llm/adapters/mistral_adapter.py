from openai import OpenAI
from typing import List, Dict, Any
from .openai_adapter import OpenAIAdapter

class MistralAdapter(OpenAIAdapter):
    """Adapter for Mistral AI models (OpenAI compatible)."""
    
    def __init__(self, api_key: str, **kwargs):
        self.base_url = "https://api.mistral.ai/v1"
        super().__init__(api_key, **kwargs)
        if api_key != "list_only":
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        else:
            self.client = None
    
    def get_provider_name(self) -> str:
        return "Mistral AI"

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {"id": "mistral-large-latest", "name": "Mistral Large", "provider": "Mistral AI"},
            {"id": "mistral-small-latest", "name": "Mistral Small", "provider": "Mistral AI"},
            {"id": "codestral-latest", "name": "Codestral", "provider": "Mistral AI"},
        ]
