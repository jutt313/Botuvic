"""
Finds latest models for each provider by searching online.
"""

from typing import List, Dict, Any
import re


class ModelFinder:
    """
    Searches online to find latest models for LLM providers.
    Never hardcodes model names - always fetches current info.
    """
    
    def __init__(self, search_engine):
        """
        Initialize model finder.
        
        Args:
            search_engine: SearchEngine instance for web searches
        """
        self.search = search_engine
        self.cache = {}  # Cache results to avoid repeated searches
    
    def find_models_for_provider(self, provider_name: str) -> List[Dict[str, Any]]:
        """
        Search online for latest models from a provider.
        
        Args:
            provider_name: Name of provider (e.g., 'OpenAI', 'Anthropic')
            
        Returns:
            List of model dicts with id, name, description, etc.
        """
        # Check cache first
        cache_key = f"{provider_name}_models"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Search for latest models
        search_queries = [
            f"{provider_name} latest models December 2025",
            f"{provider_name} API models list 2025",
            f"{provider_name} new models released"
        ]
        
        all_results = []
        for query in search_queries:
            try:
                results = self.search.search(query, max_results=3)
                if results.get("results"):
                    all_results.extend(results["results"])
            except Exception as e:
                # If search fails, continue with other queries
                continue
        
        # Extract model information from search results
        models = self._extract_models_from_search(provider_name, all_results)
        
        # Cache results
        self.cache[cache_key] = models
        
        return models
    
    def _extract_models_from_search(
        self,
        provider_name: str,
        search_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Extract model information from search results.
        
        Args:
            provider_name: Provider name
            search_results: Search results from web
            
        Returns:
            List of extracted models
        """
        # Common patterns to look for in search results
        model_patterns = {
            "OpenAI": [
                r"gpt-[\d\.]+[a-z\-]*",
                r"o[\d]+",
                r"gpt-[\d]+-turbo"
            ],
            "Anthropic": [
                r"claude-[\d\.]+-[a-z]+-[\d]+",
                r"claude-[\d]+-[a-z]+"
            ],
            "Google": [
                r"gemini-[\d\.]+-[a-z]+",
                r"gemini-[\d]+"
            ],
            "Meta": [
                r"llama-[\d]+",
                r"llama[\d]"
            ],
            "Mistral": [
                r"mistral-[a-z]+",
                r"mixtral-[\dxX]+"
            ],
            "Cohere": [
                r"command-r[-+]?[a-z]*",
                r"command[-+]?[a-z]*"
            ]
        }
        
        patterns = model_patterns.get(provider_name, [])
        found_models = []
        
        # Search through results for model names
        for result in search_results:
            content = result.get("content", "") + " " + result.get("title", "")
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Create model entry
                    model = {
                        "id": match.lower().replace(" ", "-"),
                        "name": match,
                        "provider": provider_name,
                        "description": self._extract_description(match, content),
                        "source": result.get("url", "")
                    }
                    
                    # Avoid duplicates
                    if not any(m["id"] == model["id"] for m in found_models):
                        found_models.append(model)
        
        # If no models found via pattern matching, try fallback
        if not found_models:
            found_models = self._fallback_model_extraction(provider_name, search_results)
        
        return found_models
    
    def _extract_description(self, model_name: str, content: str) -> str:
        """Extract description for a model from content."""
        # Find sentence containing model name
        sentences = content.split('.')
        for sentence in sentences:
            if model_name.lower() in sentence.lower():
                return sentence.strip()[:200]
        return f"{model_name} model"
    
    def _fallback_model_extraction(
        self,
        provider_name: str,
        search_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Return empty list if pattern matching fails.
        Adapters will provide their own model lists.
        """
        return []
    
    def get_all_providers_models(self) -> Dict[str, List[Dict]]:
        """
        Get latest models for all supported providers.
        
        Returns:
            Dict mapping provider name to list of models
        """
        providers = [
            "OpenAI",
            "Anthropic",
            "Google",
            "Meta",
            "Mistral AI",
            "Cohere",
            "Perplexity",
            "Groq",
            "Together AI",
            "Anyscale",
            "Replicate",
            "Hugging Face",
            "AI21 Labs",
            "xAI",
            "DeepSeek",
            "Qwen",
            "Baidu",
            "Ollama",
            "OpenRouter",
            "Fireworks AI"
        ]
        
        all_models = {}
        
        for provider in providers:
            try:
                models = self.find_models_for_provider(provider)
                if models:
                    all_models[provider] = models
            except Exception as e:
                # Silently continue if search fails for a provider
                continue
        
        return all_models

