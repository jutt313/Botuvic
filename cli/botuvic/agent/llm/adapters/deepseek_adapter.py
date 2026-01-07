from openai import OpenAI
from typing import List, Dict, Any
from .openai_adapter import OpenAIAdapter

class DeepSeekAdapter(OpenAIAdapter):
    """Adapter for DeepSeek models (OpenAI compatible)."""
    
    def __init__(self, api_key: str, **kwargs):
        # DeepSeek uses OpenAI format
        self.base_url = "https://api.deepseek.com"
        super().__init__(api_key, **kwargs)
        # Re-initialize client with DeepSeek base URL if we have a real key
        if api_key != "list_only":
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        else:
            self.client = None
    
    def get_provider_name(self) -> str:
        return "DeepSeek"

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat (V3)",
                "provider": "DeepSeek",
                "description": "Standard balanced model, currently V3"
            },
            {
                "id": "deepseek-v3.2",
                "name": "DeepSeek V3.2",
                "provider": "DeepSeek",
                "description": "Newly optimized V3.2 model with 67.8% SWE-Bench score"
            },
            {
                "id": "deepseek-v3.2-speciale",
                "name": "DeepSeek V3.2 Speciale",
                "provider": "DeepSeek",
                "description": "Highest performance coding model (73.1% SWE-Bench score)"
            },
            {
                "id": "deepseek-coder",
                "name": "DeepSeek Coder (V2)",
                "provider": "DeepSeek",
                "description": "Previous generation coding specialist"
            }
        ]
