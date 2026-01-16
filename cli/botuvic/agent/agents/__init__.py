"""
BOTUVIC Multi-Agent System

3-Agent Architecture:
1. MainAgent - The orchestrator that handles all user communication
   - Collects project idea
   - Decides tech stack
   - Designs architecture (DB, API, Frontend)
   - Hands off to CodeAgent

2. CodeAgent - Silent file generator
   - Creates folder structure
   - Generates database schema
   - Creates skeleton files
   - Generates documentation

3. LiveAgent - Silent monitoring agent
   - Watches files for changes
   - Detects errors
   - Suggests fixes
   - Runs tests
"""

__all__ = [
    "MainAgent",
    "CodeAgent",
    "LiveAgent"
]


def __getattr__(name):
    # New 3-agent system
    if name == "MainAgent":
        from .main_agent import MainAgent
        return MainAgent
    if name == "CodeAgent":
        from .code_agent import CodeAgent
        return CodeAgent
    if name == "LiveAgent":
        from .live_agent import LiveAgent
        return LiveAgent

    raise AttributeError(f"module 'botuvic.agent.agents' has no attribute {name}")
