"""
Main LLM manager that coordinates all adapters and model selection.
"""

from typing import Dict, List, Any, Optional
from .model_finder import ModelFinder
from .adapters.base import BaseLLMAdapter
from .adapters.openai_adapter import OpenAIAdapter
from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.ollama_adapter import OllamaAdapter
from .adapters.google_adapter import GoogleAdapter
from .adapters.deepseek_adapter import DeepSeekAdapter
from .adapters.groq_adapter import GroqAdapter
from .adapters.mistral_adapter import MistralAdapter
from .adapters.together_adapter import TogetherAdapter
from .adapters.fireworks_adapter import FireworksAdapter
from .adapters.openrouter_adapter import OpenRouterAdapter
from .adapters.deepinfra_adapter import DeepInfraAdapter
from .adapters.perplexity_adapter import PerplexityAdapter
from .adapters.xai_adapter import XAIAdapter
from .adapters.anyscale_adapter import AnyscaleAdapter
from .adapters.octoml_adapter import OctoMLAdapter
from .adapters.lepton_adapter import LeptonAdapter
from .adapters.novita_adapter import NovitaAdapter
from .adapters.lambda_adapter import LambdaAdapter
from .adapters.cohere_adapter import CohereAdapter
from .adapters.replicate_adapter import ReplicateAdapter
from .adapters.huggingface_adapter import HuggingFaceAdapter
from .adapters.ai21_adapter import AI21Adapter
from .adapters.azure_adapter import AzureAdapter
from .adapters.bedrock_adapter import BedrockAdapter
from .adapters.meta_adapter import MetaAdapter
from .adapters.friendly_adapter import FriendlyAdapter
from .adapters.botuvic_adapter import BotuvicAdapter
from .config import LLMConfig


class LLMManager:
    """
    Manages multiple LLM providers and model selection.
    Coordinates online model discovery and user configuration.
    """
    
    def __init__(self, search_engine, storage):
        """
        Initialize LLM manager.
        
        Args:
            search_engine: SearchEngine for finding models online
            storage: Storage for saving user preferences
        """
        self.search_engine = search_engine
        self.storage = storage
        self.model_finder = ModelFinder(search_engine)
        
        # Registry of available adapters
        self.adapter_registry = {
            "BOTUVIC": BotuvicAdapter,  # Default free model
            "OpenAI": OpenAIAdapter,
            "Anthropic": AnthropicAdapter,
            "Ollama": OllamaAdapter,
            "Google": GoogleAdapter,
            "DeepSeek": DeepSeekAdapter,
            "Groq": GroqAdapter,
            "Mistral": MistralAdapter,
            "Together": TogetherAdapter,
            "Fireworks": FireworksAdapter,
            "OpenRouter": OpenRouterAdapter,
            "DeepInfra": DeepInfraAdapter,
            "Perplexity": PerplexityAdapter,
            "X.AI": XAIAdapter,
            "Anyscale": AnyscaleAdapter,
            "OctoML": OctoMLAdapter,
            "Lepton": LeptonAdapter,
            "Novita": NovitaAdapter,
            "Lambda": LambdaAdapter,
            "Cohere": CohereAdapter,
            "Replicate": ReplicateAdapter,
            "HuggingFace": HuggingFaceAdapter,
            "AI21": AI21Adapter,
            "Azure": AzureAdapter,
            "Bedrock": BedrockAdapter,
            "Meta": MetaAdapter,
            "Friendly": FriendlyAdapter,
        }
        
        # Current active adapter
        self.active_adapter: Optional[BaseLLMAdapter] = None
        self.active_model: Optional[str] = None
        self.settings = LLMConfig.get_default_settings()
        
        # Try to load saved configuration
        self._load_config()
    
    def _load_config(self):
        """Load saved LLM configuration from storage."""
        config = self.storage.load("llm_config")
        if config:
            self.settings = config.get("settings", self.settings)
            self.active_model = config.get("model")
            provider = config.get("provider")

            # Try to restore API key from global storage automatically
            keys_store = self.storage.load_global("api_keys") or {}
            api_key = keys_store.get(provider)

            if provider and self.active_model and api_key:
                try:
                    adapter_class = self.adapter_registry.get(provider)
                    if adapter_class:
                        self.active_adapter = adapter_class(api_key=api_key)
                except:
                    pass
        else:
            # No config exists - initialize with BOTUVIC as default
            try:
                self.active_adapter = BotuvicAdapter()
                self.active_model = "botuvic-ai"
                print("✨ Initialized with BOTUVIC AI (free)")
            except:
                pass
    
    def discover_models(self) -> Dict[str, List[Dict]]:
        """
        Search online for latest models from all providers.
        
        Returns:
            Dict mapping provider names to model lists
        """
        print("🔍 Searching online for latest LLM models...")
        
        all_models = self.model_finder.get_all_providers_models()
        
        # Also get models directly from adapters (for providers with APIs)
        for provider_name, adapter_class in self.adapter_registry.items():
            try:
                # For providers that need API keys, we can't fetch without one
                # But we can still get fallback models
                if provider_name == "Ollama":
                    # Ollama can be checked without API key
                    try:
                        adapter = adapter_class(api_key=None)
                        api_models = adapter.get_available_models()
                        
                        if api_models:
                            if provider_name in all_models:
                                # Combine and deduplicate
                                existing_ids = {m["id"] for m in all_models[provider_name]}
                                for model in api_models:
                                    if model["id"] not in existing_ids:
                                        all_models[provider_name].append(model)
                            else:
                                all_models[provider_name] = api_models
                    except:
                        # Ollama not running, use fallback
                        pass
            except:
                # Skip if can't fetch without real API key
                pass
        
        # Save discovered models
        self.storage.save("discovered_models", all_models)
        
        return all_models
    
    def get_provider_list(self) -> List[str]:
        """Get list of available providers."""
        return list(self.adapter_registry.keys())
    
    def get_models_for_provider(self, provider_name: str, api_key: str = None) -> List[Dict]:
        """
        Get models for a specific provider.
        
        Args:
            provider_name: Name of provider
            api_key: Optional API key to fetch models from API
            
        Returns:
            List of models
        """
        # Try to load from cache first
        discovered = self.storage.load("discovered_models") or {}
        
        if provider_name in discovered:
            models = discovered[provider_name]
        else:
            # If not cached, search online
            models = self.model_finder.find_models_for_provider(provider_name)
        
        # Also try adapter's API if we have an API key
        if provider_name in self.adapter_registry and api_key:
            try:
                adapter_class = self.adapter_registry[provider_name]
                adapter = adapter_class(api_key=api_key)
                api_models = adapter.get_available_models()
                
                # Merge results
                existing_ids = {m["id"] for m in models}
                for model in api_models:
                    if model["id"] not in existing_ids:
                        models.append(model)
            except:
                # If API call fails, use what we have
                pass
        
        return models
    
    def configure_llm(
        self,
        provider: str,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ):
        """
        Configure LLM provider and model.
        
        Args:
            provider: Provider name (e.g., 'OpenAI')
            model: Model ID (e.g., 'gpt-4o')
            api_key: API key for provider
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional settings
        """
        if provider not in self.adapter_registry:
            raise ValueError(f"Unsupported provider: {provider}. Available: {', '.join(self.adapter_registry.keys())}")
        
        # Create adapter instance
        adapter_class = self.adapter_registry[provider]
        self.active_adapter = adapter_class(api_key=api_key, **kwargs)
        self.active_model = model
        
        # Update settings
        self.settings.update({
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        })
        
        # Validate settings
        LLMConfig.validate_settings(self.settings)
        
        # Save configuration (without API key for security)
        config = {
            "provider": provider,
            "model": model,
            "settings": self.settings
        }
        self.storage.save("llm_config", config)
        
        print(f"✅ Configured {provider} - {model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict] = None,
        max_retries: int = 3,
        **override_settings
    ) -> Dict[str, Any]:
        """
        Send chat request using configured LLM with retry logic.

        Args:
            messages: List of message dicts
            functions: Optional list of function definitions for tool calling
            max_retries: Maximum number of retries on failure (default 3)
            **override_settings: Temporary setting overrides

        Returns:
            Response dict with content and optional tool_calls
        """
        import time

        if not self.active_adapter or not self.active_model:
            raise ValueError("LLM not configured. Call configure_llm() first.")

        # Merge settings
        settings = {**self.settings, **override_settings}

        # Prepare tools if provided
        if functions:
            # Format functions as tools for OpenAI-style API
            tools = [{"type": "function", "function": f} for f in functions]
            settings["tools"] = tools
            settings["tool_choice"] = "auto"

        # Retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.active_adapter.chat(
                    messages=messages,
                    model=self.active_model,
                    **settings
                )
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Don't retry on auth errors
                if "401" in error_str or "authentication" in error_str or "invalid" in error_str:
                    raise e

                # Retry on rate limits and connection errors
                if "429" in error_str or "rate limit" in error_str or "connection" in error_str:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    print(f"⏳ Rate limited, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                # For other errors, retry once
                if attempt == 0:
                    time.sleep(1)
                    continue

                raise e

        # If all retries failed
        raise last_error
    
    def update_settings(self, **settings):
        """
        Update LLM settings.
        
        Args:
            **settings: Settings to update (temperature, max_tokens, etc.)
        """
        # Validate new settings
        LLMConfig.validate_settings(settings)
        
        self.settings.update(settings)
        
        # Save to storage
        config = self.storage.load("llm_config") or {}
        config["settings"] = self.settings
        self.storage.save("llm_config", config)
    
    def get_current_config(self) -> Dict:
        """Get current LLM configuration."""
        return {
            "provider": self.active_adapter.get_provider_name() if self.active_adapter else None,
            "model": self.active_model,
            "settings": self.settings
        }
    
    def is_configured(self) -> bool:
        """Check if LLM is configured."""
        return self.active_adapter is not None and self.active_model is not None

