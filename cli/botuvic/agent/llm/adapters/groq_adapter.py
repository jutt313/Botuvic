from openai import OpenAI
from typing import List, Dict, Any
from .openai_adapter import OpenAIAdapter

class GroqAdapter(OpenAIAdapter):
    """Adapter for Groq models (OpenAI compatible)."""
    
    def __init__(self, api_key: str, **kwargs):
        self.base_url = "https://api.groq.com/openai/v1"
        super().__init__(api_key, **kwargs)
        if api_key != "list_only":
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        else:
            self.client = None
    
    def get_provider_name(self) -> str:
        return "Groq"

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {"id": "llama3-70b-8192", "name": "Llama 3 70B", "provider": "Groq"},
            {"id": "llama3-8b-8192", "name": "Llama 3 8B", "provider": "Groq"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7b", "provider": "Groq"},
        ]
