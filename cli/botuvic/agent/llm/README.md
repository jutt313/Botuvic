# BOTUVIC Multi-LLM System

Dynamic multi-provider LLM support with online model discovery.

## Features

✅ **25+ LLM Provider Support** - Extensible adapter system  
✅ **Online Model Discovery** - Searches web for latest models  
✅ **Never Outdated** - Always gets current model information  
✅ **User Configuration** - Choose provider, model, and settings  
✅ **Settings Control** - Temperature, max tokens, top-p, etc.  
✅ **Validation** - Ensures settings are valid  
✅ **Storage** - Saves user preferences  
✅ **Local Models** - Supports Ollama and local LLMs  

## Supported Providers

### Currently Implemented

1. **OpenAI** - GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
2. **Anthropic** - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
3. **Ollama** - Local models (Llama, Mistral, CodeLlama, etc.)
4. **Google** - Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini Pro

### Ready to Add

- Mistral AI
- Cohere
- Meta (Llama via Together/Replicate)
- Perplexity
- Groq
- Together AI
- Anyscale
- Replicate
- Hugging Face
- AI21 Labs
- xAI (Grok)
- DeepSeek
- Qwen
- Baidu
- OpenRouter
- Fireworks AI

## Usage

### 1. Discover Available Models

```python
# In agent chat
"Show me available LLM providers"

# Agent will call discover_llm_models()
# Returns dict of providers and their models
```

### 2. Configure LLM

```python
# In agent chat
"I want to use Anthropic Claude 3.5 Sonnet"

# Agent will guide you through:
# 1. Select provider
# 2. Select model
# 3. Enter API key
# 4. Configure settings (temperature, max_tokens)
```

### 3. Update Settings

```python
# In agent chat
"Set temperature to 0.8"

# Agent will call update_llm_settings()
```

## Architecture

```
agent/llm/
├── manager.py          # Main LLM manager
├── model_finder.py     # Online model discovery
├── config.py           # Settings validation
└── adapters/
    ├── base.py         # Base adapter class
    ├── openai_adapter.py
    ├── anthropic_adapter.py
    ├── ollama_adapter.py
    └── google_adapter.py
```

## Adding a New Provider

1. Create adapter in `adapters/`:

```python
from .base import BaseLLMAdapter

class NewProviderAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        # Initialize provider client
    
    def get_provider_name(self) -> str:
        return "NewProvider"
    
    def chat(self, messages, model, temperature, max_tokens, **kwargs):
        # Implement API call
        pass
    
    def get_available_models(self):
        # Return list of models
        pass
```

2. Register in `manager.py`:

```python
from .adapters.new_provider_adapter import NewProviderAdapter

self.adapter_registry = {
    # ... existing adapters
    "NewProvider": NewProviderAdapter,
}
```

3. Add to `adapters/__init__.py`

## Configuration Storage

LLM configuration is saved in `.botuvic/llm_config.json`:

```json
{
  "provider": "OpenAI",
  "model": "gpt-4o",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

**Note:** API keys are NOT stored for security. Users must provide them each session or via environment variables.

## Environment Variables

You can set default API keys in `.env`:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

The system will auto-configure with OpenAI if `OPENAI_API_KEY` is found.

## Function Calling Support

Providers that support function calling:
- ✅ OpenAI (tools format)
- ✅ Anthropic (tool use format)
- ❌ Ollama (not supported)
- ⚠️ Google (limited support)

The manager automatically formats functions for each provider.

## Error Handling

- Invalid API keys → Clear error message
- Provider unavailable → Fallback to cached models
- Model not found → Lists available models
- Settings invalid → Validation error with constraints

## Future Enhancements

- [ ] Streaming support
- [ ] Model cost tracking
- [ ] Automatic failover
- [ ] Multi-model ensemble
- [ ] Custom model fine-tuning
- [ ] Rate limiting per provider

