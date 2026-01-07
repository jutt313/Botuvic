"""LLM package for multi-provider support"""

__all__ = ["LLMManager", "LLMConfig"]


def __getattr__(name):
    if name == "LLMManager":
        from .manager import LLMManager
        return LLMManager
    if name == "LLMConfig":
        from .config import LLMConfig
        return LLMConfig
    raise AttributeError(f"module 'botuvic.agent.llm' has no attribute {name}")
