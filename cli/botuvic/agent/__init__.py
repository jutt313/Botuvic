"""BOTUVIC Agent System"""

__all__ = ["BotuvicAgent"]


def __getattr__(name):
    if name == "BotuvicAgent":
        from .core import BotuvicAgent
        return BotuvicAgent
    raise AttributeError(f"module 'botuvic.agent' has no attribute {name}")
