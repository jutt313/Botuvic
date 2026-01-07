"""
Agent Router - Routes requests to the correct specialized agent based on workflow phase.
"""

import os
from typing import Dict, Any, Optional
from rich.console import Console

from .idea_agent import IdeaAgent
from .tech_stack_agent import TechStackAgent
from .design_agent import DesignAgent
from .dev_agent import DevAgent
from .roadmap_agent import RoadmapAgent
from .live_agent import LiveAgent
from ..workflow_controller import WorkflowController, Phase

console = Console()


class AgentRouter:
    """
    Routes user requests to the correct specialized agent based on current phase.
    Handles agent initialization, phase-based routing, and data passing between agents.
    """
    
    def __init__(self, llm_client, storage, project_dir: str, search_engine=None, workflow: Optional[WorkflowController] = None):
        """
        Initialize Agent Router with all agents.
        
        Args:
            llm_client: LLM client for AI interactions
            storage: Storage system for data persistence
            project_dir: Project root directory
            search_engine: Search engine for online research
            workflow: WorkflowController instance (optional, will create if not provided)
        """
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
        self.search = search_engine
        
        # Initialize workflow controller if not provided
        if workflow is None:
            self.workflow = WorkflowController(project_dir)
        else:
            self.workflow = workflow
        
        # Initialize all agents
        console.print("[dim]Initializing agents...[/dim]")
        
        self.idea_agent = IdeaAgent(
            llm_client=llm_client,
            storage=storage,
            project_dir=project_dir,
            search_engine=search_engine
        )
        
        self.tech_stack_agent = TechStackAgent(
            llm_client=llm_client,
            storage=storage,
            project_dir=project_dir,
            search_engine=search_engine
        )
        
        # DesignAgent, DevAgent, RoadmapAgent use different signature
        # They expect: llm_adapter, storage (not llm_client, storage, project_dir, search_engine)
        # Extract adapter from llm_client (which is an LLMWrapper around LLMManager)
        try:
            if hasattr(llm_client, 'manager'):
                # llm_client is LLMWrapper, get manager
                manager = llm_client.manager
                if hasattr(manager, 'active_adapter') and manager.active_adapter:
                    llm_adapter = manager.active_adapter
                else:
                    # Fallback: create a simple adapter wrapper
                    llm_adapter = llm_client
            else:
                llm_adapter = llm_client
        except Exception as e:
            console.print(f"[yellow]Warning: Could not extract adapter, using llm_client as-is: {e}[/yellow]")
            llm_adapter = llm_client
        
        self.design_agent = DesignAgent(
            llm_adapter=llm_adapter,
            storage=storage
        )
        
        self.dev_agent = DevAgent(
            llm_adapter=llm_adapter,
            storage=storage
        )
        
        self.roadmap_agent = RoadmapAgent(
            llm_adapter=llm_adapter,
            storage=storage
        )
        
        self.live_agent = LiveAgent(
            llm_client=llm_client,
            storage=storage,
            project_dir=project_dir
        )
        
        console.print("[green]✓ All agents initialized[/green]")
    
    def get_current_agent(self) -> Any:
        """
        Get the current agent based on workflow phase.
        
        Returns:
            The appropriate agent instance for the current phase
        """
        current_phase = self.workflow.current_phase
        
        # Route based on phase
        if current_phase == Phase.IDEA_COLLECTION:
            return self.idea_agent
        elif current_phase == Phase.TECH_STACK:
            return self.tech_stack_agent
        elif current_phase == Phase.DEEP_DISCUSSIONS:
            return self.design_agent
        elif current_phase == Phase.CREDENTIALS:
            return self.roadmap_agent  # RoadmapAgent handles credentials
        elif current_phase == Phase.PROJECT_SETUP:
            return self.dev_agent
        elif current_phase == Phase.BUILD_STRATEGY:
            return self.dev_agent
        elif current_phase == Phase.DOCUMENTATION:
            return self.roadmap_agent
        elif current_phase == Phase.ROADMAP:
            return self.roadmap_agent
        elif current_phase == Phase.EXECUTION:
            # During execution, user is building - can use any agent or live agent
            return self.live_agent
        elif current_phase == Phase.LIVE_DEVELOPMENT:
            return self.live_agent
        else:
            # Default to IdeaAgent for unknown phases
            return self.idea_agent
    
    def route(self, user_message: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Route user message to the correct agent and return response.
        
        Args:
            user_message: User's input message
            user_profile: Optional user profile data
            
        Returns:
            Dict with agent response and metadata
        """
        # Get current agent
        agent = self.get_current_agent()
        current_phase = self.workflow.current_phase
        
        # Log routing decision
        agent_name = agent.__class__.__name__
        console.print(f"[dim]Routing to {agent_name} (Phase {current_phase.value})[/dim]")
        
        # Call agent's chat method
        try:
            response = agent.chat(user_message, user_profile=user_profile)
            
            # Check if phase should advance
            self._check_phase_advancement(agent, response)
            
            # Add routing metadata to response
            response['routing'] = {
                'agent': agent_name,
                'phase': current_phase.value,
                'phase_name': current_phase.name
            }
            
            return response
            
        except Exception as e:
            console.print(f"[red]Error in {agent_name}: {e}[/red]")
            return {
                'message': f"I encountered an error: {str(e)}",
                'status': 'error',
                'error': str(e),
                'routing': {
                    'agent': agent_name,
                    'phase': current_phase.value
                }
            }
    
    def _check_phase_advancement(self, agent: Any, response: Dict[str, Any]):
        """
        Check if current phase is complete and advance if needed.
        
        Args:
            agent: Current agent instance
            response: Agent's response dict
        """
        current_phase = self.workflow.current_phase
        
        # Check if agent indicates completion
        if response.get('status') == 'complete' or response.get('phase_complete', False):
            # Mark current phase as complete
            self.workflow.mark_phase_complete(current_phase)
            
            # Try to advance to next phase
            next_phase = self.workflow.advance_phase()
            
            if next_phase:
                console.print(f"[green]✓ Phase {current_phase.value} complete. Advancing to Phase {next_phase.value}[/green]")
            else:
                console.print(f"[yellow]Phase {current_phase.value} complete, but next phase not ready yet[/yellow]")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current routing status.
        
        Returns:
            Dict with current agent, phase, and workflow status
        """
        current_agent = self.get_current_agent()
        current_phase = self.workflow.current_phase
        
        return {
            'current_agent': current_agent.__class__.__name__,
            'current_phase': current_phase.value,
            'phase_name': current_phase.name,
            'workflow_status': self.workflow.get_workflow_context()
        }
    
    def force_switch_agent(self, agent_name: str) -> bool:
        """
        Force switch to a specific agent (for testing or manual control).
        
        Args:
            agent_name: Name of agent to switch to (e.g., 'IdeaAgent', 'DesignAgent')
            
        Returns:
            True if switch successful, False otherwise
        """
        agent_map = {
            'IdeaAgent': self.idea_agent,
            'TechStackAgent': self.tech_stack_agent,
            'DesignAgent': self.design_agent,
            'DevAgent': self.dev_agent,
            'RoadmapAgent': self.roadmap_agent,
            'LiveAgent': self.live_agent
        }
        
        if agent_name not in agent_map:
            console.print(f"[red]Unknown agent: {agent_name}[/red]")
            return False
        
        # Note: This doesn't change the workflow phase, just allows manual agent selection
        # For actual phase changes, use workflow.advance_phase()
        console.print(f"[yellow]Manual switch to {agent_name} (workflow phase unchanged)[/yellow]")
        return True
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Get all agent instances.
        
        Returns:
            Dict mapping agent names to instances
        """
        return {
            'IdeaAgent': self.idea_agent,
            'TechStackAgent': self.tech_stack_agent,
            'DesignAgent': self.design_agent,
            'DevAgent': self.dev_agent,
            'RoadmapAgent': self.roadmap_agent,
            'LiveAgent': self.live_agent
        }

