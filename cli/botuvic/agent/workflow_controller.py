"""
Workflow Controller for BOTUVIC.
Manages the automatic phase progression from idea to production-ready codebase.
"""

import json
import os
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict


class Phase(Enum):
    """All phases in the BOTUVIC workflow."""
    IDEA_COLLECTION = 1
    TECH_STACK = 2
    DEEP_DISCUSSIONS = 3
    CREDENTIALS = 4  # Collect credentials BEFORE setup
    PROJECT_SETUP = 5  # Setup with real credentials
    BUILD_STRATEGY = 6  # Decide build approach AFTER setup
    DOCUMENTATION = 7  # Create instruction files based on actual project
    ROADMAP = 8  # Generate roadmap based on actual structure
    EXECUTION = 9  # After setup, user is building
    LIVE_DEVELOPMENT = 10  # Live development mode - continuous monitoring


@dataclass
class PhaseData:
    """Data collected during each phase."""
    # User Profile (Pre-loaded from database, collected during signup)
    experience_level: str = ""  # professional/learning/non-technical
    tech_knowledge: List[str] = field(default_factory=list)
    coding_ability: str = ""
    tool_preference: str = ""  # choose_own/agent_decides
    help_level: str = ""  # minimal/explain/maximum
    ai_tools: List[str] = field(default_factory=list)
    primary_goal: str = ""  # learn/build_product/experimenting/portfolio
    time_commitment: str = ""  # full_time/part_time/weekends/casual
    team_or_solo: str = ""  # solo/team/hire_later
    previous_projects: str = ""  # multiple/one_two/none/started_never_finished

    # Phase 1: Idea Collection
    core_idea: str = ""
    target_users: str = ""
    main_features: List[str] = field(default_factory=list)
    scale: str = ""  # simple/medium/large
    special_requirements: List[str] = field(default_factory=list)

    # Phase 2: Tech Stack
    tech_stack_preference: str = ""  # user_choice/agent_decides
    frontend: Dict[str, str] = field(default_factory=dict)
    backend: Dict[str, str] = field(default_factory=dict)
    database: Dict[str, str] = field(default_factory=dict)
    authentication: Dict[str, str] = field(default_factory=dict)
    storage: Dict[str, str] = field(default_factory=dict)
    deployment: Dict[str, str] = field(default_factory=dict)
    other_tools: List[Dict[str, str]] = field(default_factory=list)
    tech_stack_locked: bool = False

    # Phase 3: Deep Discussions
    database_schema: Dict[str, Any] = field(default_factory=dict)
    backend_architecture: Dict[str, Any] = field(default_factory=dict)
    frontend_design: Dict[str, Any] = field(default_factory=dict)
    backend_discussion_started: bool = False  # Track if backend discussion has begun
    frontend_discussion_started: bool = False  # Track if frontend discussion has begun

    # Phase 4: Credentials
    credentials_collected: List[str] = field(default_factory=list)
    credentials_pending: List[str] = field(default_factory=list)
    credentials_validated: bool = False

    # Phase 5: Project Setup
    project_structure_created: bool = False
    base_files_created: bool = False
    database_setup_complete: bool = False
    backend_files_created: bool = False
    frontend_files_created: bool = False

    # Phase 6: Build Strategy
    builder: str = ""  # self/ai_assisted/ai_full
    ai_tool_choice: str = ""  # cursor/claude_code/v0/bolt/manual
    ai_tool_name: str = ""  # Any AI tool name (Cursor, Claude, GPT, Gemini, etc.)
    team_members: List[Dict[str, str]] = field(default_factory=list)  # Team member info

    # Phase 7: Documentation
    documentation_generated: bool = False
    instruction_files_created: bool = False

    # Phase 8: Roadmap
    roadmap_generated: bool = False
    phases: List[Dict[str, Any]] = field(default_factory=list)

    # Phase 10: Live Development Mode
    live_mode_active: bool = False
    file_watcher_active: bool = False
    browser_console_tracking: bool = False
    improvements_log: List[Dict[str, Any]] = field(default_factory=list)


class WorkflowController:
    """
    Controls the BOTUVIC workflow, ensuring phases progress in order
    and all required data is collected before moving forward.
    """

    # PHASE_QUESTIONS removed - profiling now happens during signup, not in agent
    PHASE_QUESTIONS = {}

    def __init__(self, storage, user_profile=None):
        """
        Initialize workflow controller with storage reference.

        Args:
            storage: Storage instance for saving/loading state
            user_profile: Optional dict with user profile data from database
        """
        self.storage = storage
        self.current_phase = Phase.IDEA_COLLECTION  # Start from Phase 1 (Idea Collection)
        self.phase_data = PhaseData()
        self.current_question_index = 0
        self.phase_complete = {phase: False for phase in Phase}

        # Load user profile if provided (from database/signup)
        if user_profile:
            self._load_user_profile(user_profile)

        self.load_state()

    def _load_user_profile(self, profile: dict):
        """
        Load user profile data into phase_data.
        Profile is collected during signup, not during agent conversation.
        """
        # Map profile fields to phase_data
        if "experience_level" in profile:
            self.phase_data.experience_level = profile["experience_level"]
        if "tech_knowledge" in profile:
            self.phase_data.tech_knowledge = profile["tech_knowledge"]
        if "coding_ability" in profile:
            self.phase_data.coding_ability = profile["coding_ability"]
        if "tool_preference" in profile:
            self.phase_data.tool_preference = profile["tool_preference"]
        if "help_level" in profile:
            self.phase_data.help_level = profile["help_level"]
        if "ai_tools" in profile:
            self.phase_data.ai_tools = profile["ai_tools"]
        if "primary_goal" in profile:
            self.phase_data.primary_goal = profile["primary_goal"]
        if "time_commitment" in profile:
            self.phase_data.time_commitment = profile["time_commitment"]
        if "team_or_solo" in profile:
            self.phase_data.team_or_solo = profile["team_or_solo"]
        if "previous_projects" in profile:
            self.phase_data.previous_projects = profile["previous_projects"]

    def load_state(self):
        """Load workflow state from storage."""
        state = self.storage.load("workflow_state")
        if state:
            self.current_phase = Phase(state.get("current_phase", 1))
            self.current_question_index = state.get("current_question_index", 0)
            self.phase_complete = {Phase(int(k)): v for k, v in state.get("phase_complete", {}).items()}

            # Load phase data
            phase_data_dict = state.get("phase_data", {})
            for key, value in phase_data_dict.items():
                if hasattr(self.phase_data, key):
                    setattr(self.phase_data, key, value)

    def save_state(self):
        """Save workflow state to storage."""
        state = {
            "current_phase": self.current_phase.value,
            "current_question_index": self.current_question_index,
            "phase_complete": {str(k.value): v for k, v in self.phase_complete.items()},
            "phase_data": asdict(self.phase_data)
        }
        self.storage.save("workflow_state", state)

    def get_phase_name(self, phase: Phase = None) -> str:
        """Get human-readable phase name."""
        phase = phase or self.current_phase
        names = {
            Phase.IDEA_COLLECTION: "Project Idea Collection",
            Phase.TECH_STACK: "Tech Stack Research & Decision",
            Phase.DEEP_DISCUSSIONS: "Deep Technical Discussions",
            Phase.BUILD_STRATEGY: "Build Strategy Decision",
            Phase.PROJECT_SETUP: "Complete Project Setup",
            Phase.ROADMAP: "Roadmap Generation",
            Phase.CREDENTIALS: "Credentials Collection",
            Phase.EXECUTION: "Project Execution",
            Phase.LIVE_DEVELOPMENT: "Live Development Mode"
        }
        return names.get(phase, "Unknown")

    def get_current_phase_info(self) -> Dict[str, Any]:
        """Get information about current phase."""
        return {
            "phase_number": self.current_phase.value,
            "phase_name": self.get_phase_name(),
            "is_complete": self.phase_complete.get(self.current_phase, False),
            "question_index": self.current_question_index,
            "total_phases": len(Phase)
        }

    def is_new_project(self) -> bool:
        """Check if this is a new project (not started yet)."""
        return self.current_phase == Phase.IDEA_COLLECTION and not self.phase_complete.get(Phase.IDEA_COLLECTION, False)

    def get_welcome_message(self) -> str:
        """Get welcome message based on project state."""
        if self.is_new_project():
            return "Welcome to BOTUVIC! Let's build your project from idea to production."
        else:
            phase_name = self.get_phase_name()
            return f"Welcome back! Currently in: {phase_name}"

    def get_workflow_context(self) -> str:
        """Get workflow context for LLM including current phase and instructions."""
        phase_info = self.get_current_phase_info()

        # Prepare "DATA IN STORAGE" section - show both completed and in-progress
        collected_data = []
        if self.phase_data.core_idea: collected_data.append("[X] Core Idea")
        if self.phase_data.tech_stack_locked: collected_data.append("[X] Tech Stack")
        
        # Phase 3 sub-sections: Show in-progress if discussion started but not complete
        if self.phase_data.database_schema: 
            collected_data.append("[X] Database Schema")
        
        if self.phase_data.backend_architecture:
            collected_data.append("[X] Backend Architecture")
        elif (self.current_phase == Phase.DEEP_DISCUSSIONS and 
              self.phase_data.database_schema and 
              not self.phase_data.backend_architecture):
            # Database is complete, backend is next - mark as in progress
            collected_data.append("[→] Backend Architecture (in progress)")
        
        if self.phase_data.frontend_design:
            collected_data.append("[X] Frontend Design")
        elif (self.current_phase == Phase.DEEP_DISCUSSIONS and 
              self.phase_data.backend_architecture and 
              not self.phase_data.frontend_design):
            # Backend is complete, frontend is next - mark as in progress
            collected_data.append("[→] Frontend Design (in progress)")
        
        if self.phase_data.credentials_validated: collected_data.append("[X] Credentials")
        
        context = f"""
WORKFLOW STATUS:
Current Phase: {phase_info['phase_number']}/9 - {phase_info['phase_name']}
Progress: Phase {phase_info['phase_number']} of {phase_info['total_phases']}

DATA IN STORAGE (ALREADY COLLECTED):
{chr(10).join(collected_data) if collected_data else "None"}

USER PROFILE (Pre-loaded from database):
- Experience: {self.phase_data.experience_level or 'Not set'}
- Coding ability: {self.phase_data.coding_ability or 'Not set'}
- Help level: {self.phase_data.help_level or 'Not set'}
- AI tools: {', '.join(self.phase_data.ai_tools) if self.phase_data.ai_tools else 'None'}

INSTRUCTIONS:
You are currently in Phase {phase_info['phase_number']}: {phase_info['phase_name']}.
CHECK "DATA IN STORAGE" ABOVE. 
- If a sub-goal is marked [X], it's COMPLETE - DO NOT ask about it again.
- If a sub-goal is marked [→], it's IN PROGRESS - continue from where you left off, DO NOT repeat the intro.
- ALWAYS check your conversation history before asking questions - if you've already asked about a topic, continue from context.
Only asking 1 question is extremely important.
"""
        return context.strip()

    def set_phase_data(self, key: str, value: Any):
        """Set a field in phase_data and check if phase is complete."""
        if hasattr(self.phase_data, key):
            # Track when discussions start (even if value is empty/partial)
            if key == "backend_architecture" and self.current_phase == Phase.DEEP_DISCUSSIONS:
                if not self.phase_data.backend_discussion_started:
                    self.phase_data.backend_discussion_started = True
            elif key == "frontend_design" and self.current_phase == Phase.DEEP_DISCUSSIONS:
                if not self.phase_data.frontend_discussion_started:
                    self.phase_data.frontend_discussion_started = True
            
            setattr(self.phase_data, key, value)
            self.save_state()
            
            # Smart Progression: Check if this save completes the phase
            self._check_and_advance_if_ready()

    def _check_and_advance_if_ready(self):
        """Check if all requirements for the current phase are met, then advance."""
        requirements_met = False
        
        if self.current_phase == Phase.IDEA_COLLECTION:
            if self.phase_data.core_idea and self.phase_data.main_features:
                requirements_met = True
                
        elif self.current_phase == Phase.TECH_STACK:
            if self.phase_data.tech_stack_locked:
                requirements_met = True
                
        elif self.current_phase == Phase.DEEP_DISCUSSIONS:
            # Requires all 3 major architecture pieces
            if (self.phase_data.database_schema and 
                self.phase_data.backend_architecture and 
                self.phase_data.frontend_design):
                requirements_met = True
                
        elif self.current_phase == Phase.CREDENTIALS:
            if self.phase_data.credentials_validated:
                requirements_met = True

        elif self.current_phase == Phase.PROJECT_SETUP:
            # Phase 5: Project setup complete when structure and files created
            if (self.phase_data.project_structure_created and
                self.phase_data.base_files_created):
                requirements_met = True

        elif self.current_phase == Phase.BUILD_STRATEGY:
            # Phase 6: Build strategy complete when builder choice made
            if self.phase_data.builder:
                requirements_met = True

        elif self.current_phase == Phase.DOCUMENTATION:
            # Phase 7: Documentation complete when files generated
            if self.phase_data.documentation_generated:
                requirements_met = True

        elif self.current_phase == Phase.ROADMAP:
            # Phase 8: Roadmap complete when phases defined
            if self.phase_data.roadmap_generated or self.phase_data.phases:
                requirements_met = True

        elif self.current_phase == Phase.EXECUTION:
            # Phase 9: Execution is ongoing, no auto-advance
            pass

        if requirements_met:
            self.phase_complete[self.current_phase] = True
            # Advance to next phase immediately
            next_phase_val = self.current_phase.value + 1
            if next_phase_val <= len(Phase):
                self.current_phase = Phase(next_phase_val)
                self.save_state()

    def process_answer(self, answer: str) -> Dict[str, Any]:
        """
        Process user's answer and return next action.

        Returns:
            Dict with keys:
                - action: "next_question" | "phase_complete" | "continue"
                - question: Next question dict (if action is next_question)
                - message: Message to show user
        """
        if self.current_phase == Phase.IDEA_COLLECTION:
            return self._process_idea_answer(answer)
        elif self.current_phase == Phase.TECH_STACK:
            return self._process_tech_stack_answer(answer)
        elif self.current_phase == Phase.DEEP_DISCUSSIONS:
            return self._process_deep_discussion_answer(answer)
        elif self.current_phase == Phase.BUILD_STRATEGY:
            return self._process_build_strategy_answer(answer)
        elif self.current_phase == Phase.PROJECT_SETUP:
            return self._process_setup_answer(answer)
        elif self.current_phase == Phase.ROADMAP:
            return self._process_roadmap_answer(answer)
        elif self.current_phase == Phase.CREDENTIALS:
            return self._process_credentials_answer(answer)

        return {"action": "continue", "message": ""}

