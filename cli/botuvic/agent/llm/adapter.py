class LLMAdapter:
    """Lightweight adapter protocol for agent type hints."""

    def chat(self, messages, **kwargs):
        raise NotImplementedError
