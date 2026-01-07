"""
BOTUVIC Multi-Agent System

6 Specialized Agents:
1. IdeaAgent - Phases 1-3 (Discovery, Tools, Tech Stack)
2. DesignAgent - Phases 4-6 (Database, Backend, Frontend Design)
3. SetupAgent - Phase 7 (File Creation)
4. PlanningAgent - Phases 8-9 (Documentation, Final Touches)
5. GitAgent - Version Control
6. LiveAgent - Phase 10 (Live Development Mode)
"""

__all__ = [
    "IdeaAgent",
    "TechStackAgent",
    "DesignAgent",
    "DevAgent",
    "RoadmapAgent",
    "LiveAgent",
    "AgentRouter"
]


def __getattr__(name):
    if name == "IdeaAgent":
        from .idea_agent import IdeaAgent
        return IdeaAgent
    if name == "TechStackAgent":
        from .tech_stack_agent import TechStackAgent
        return TechStackAgent
    if name == "DesignAgent":
        from .design_agent import DesignAgent
        return DesignAgent
    if name == "DevAgent":
        from .dev_agent import DevAgent
        return DevAgent
    if name == "RoadmapAgent":
        from .roadmap_agent import RoadmapAgent
        return RoadmapAgent
    if name == "LiveAgent":
        from .live_agent import LiveAgent
        return LiveAgent
    if name == "AgentRouter":
        from .agent_router import AgentRouter
        return AgentRouter
    raise AttributeError(f"module 'botuvic.agent.agents' has no attribute {name}")
