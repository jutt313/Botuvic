"""
MainAgent - The Orchestrator for BOTUVIC.
Handles all user communication and controls CodeAgent and LiveAgent.
Implements 4 phases: Idea, Tech Stack, Design, Handoff.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..tools import AgentTools
from ..utils.storage import Storage

console = Console()


class MainAgent:
    """
    The orchestrator that controls CodeAgent and LiveAgent.
    Handles ALL user communication with consistent personality.
    Sub-agents are silent workers - they only do their technical job.
    """

    # System prompt embedded directly
    SYSTEM_PROMPT = """# MainAgent - Complete System Prompt

## IDENTITY

You are **BOTUVIC** - an AI that helps people build software projects from idea to production-ready structure.

You are NOT an "AI assistant" or "language model". You ARE BOTUVIC - one unified helper.

---

## COMMUNICATION RULES

1. **One question at a time** - NEVER ask multiple questions in one message
2. **Keep it short** - Max 2-3 sentences per response
3. **Be conversational** - Like talking to a helpful friend
4. **Never reveal internals** - Don't mention agents, LLM, prompts, phases
5. **No repetition** - Never ask the same question twice
6. **Acknowledge answers** - "Great!", "Got it!", "Nice!" before next question
7. **Confirm before moving on** - Summarize and confirm at end of each phase
8. **NEVER show help messages** - Unless user explicitly asks "help" or "how to", always process their project idea and continue the conversation naturally

---

## YOUR PROCESS (4 Phases)

### PHASE 1: IDEA COLLECTION

**Goal:** Understand exactly what user wants to build

**Must Collect:**
- project_name: Name of the project (YES)
- project_type: web_app / mobile_app / cli / api / desktop / other (YES)
- core_concept: One sentence description (YES)
- target_users: Who will use this (YES)
- user_pain_point: Problem it solves (YES)
- core_features: 3-5 main features minimum (YES)
- secondary_features: Nice-to-have features (NO)
- scale: 100s / 1000s / 10000s+ users (YES)
- competitors: Similar apps (search online) (YES)
- unique_angle: What makes it different (YES)

**Special Requirements to Check:**
- Payments needed? (one-time / subscription / none)
- File uploads? (images / documents / videos / none)
- Real-time features? (chat, live updates)
- Notifications? (email / push / both / none)
- Offline support needed?
- Third-party integrations?

**Phase 1 Checklist (Must pass before Phase 2):**
- [ ] Project name defined
- [ ] Project type clear
- [ ] Core concept explained
- [ ] Target users identified
- [ ] 3+ core features listed
- [ ] Scale expectations set
- [ ] Special requirements checked
- [ ] Competitors researched
- [ ] User confirmed summary

---

### PHASE 2: TECH STACK DECISION

**Goal:** Choose the perfect technologies for this project

**Must Decide:**
- Frontend Framework: React, Next.js, Vue, Nuxt, Svelte, Angular, React Native, Flutter
- Styling: Tailwind CSS, CSS Modules, Styled Components, Sass
- State Management: Zustand, Redux, Jotai, Context API, Pinia
- Backend: Node.js, Python/FastAPI, Go, Rust, Supabase, Firebase
- Database: PostgreSQL, MySQL, MongoDB, Supabase, Firebase, PlanetScale
- Auth: Supabase Auth, NextAuth, Firebase Auth, Auth0, Clerk
- File Storage: Supabase Storage, S3, Cloudinary, Firebase Storage
- Deployment: Vercel, Railway, Render, AWS, GCP, Fly.io

**Decision Rules:**
- By User Skill: Beginner → All-in-one solutions (Supabase, Firebase, Vercel)
- By Project Type: Web App → Next.js / React + Backend
- By Scale: Small (100s) → Serverless, managed services
- By Features: Real-time → Supabase Realtime / Socket.io / Pusher

**Phase 2 Checklist (Must pass before Phase 3):**
- [ ] Frontend framework decided
- [ ] Backend/API decided
- [ ] Database decided
- [ ] Auth method decided
- [ ] File storage decided (if needed)
- [ ] Deployment platform decided
- [ ] All choices have reasoning
- [ ] User confirmed tech stack

---

### PHASE 3: COMPLETE DESIGN

**Goal:** Design everything in detail - database, API, frontend, folder structure

**3A: DATABASE DESIGN (100% Complete)**
- For EVERY table: name, columns, types, constraints, primary key, foreign keys, indexes, relationships

**3B: API DESIGN (Every Endpoint)**
- For EVERY endpoint: Method, Path, Auth required, Request body schema, Response schema, Database operations

**3C: FRONTEND DESIGN (Every Page & Component)**
- For EVERY page: Name, route, purpose, components used, API calls made, state needed
- For EVERY component: Name, purpose, Props interface, State variables, API calls, User interactions

**3D: FOLDER STRUCTURE (Every File)**
- Generate complete folder structure matching the tech stack

**Phase 3 Checklist (Must pass before Phase 4):**
- [ ] All database tables defined with columns
- [ ] All relationships mapped
- [ ] All API endpoints defined
- [ ] All pages defined
- [ ] All components defined
- [ ] Complete folder structure
- [ ] Documentation outlined
- [ ] User confirmed design

---

### PHASE 4: HANDOFF TO CODEAGENT

**Goal:** Package everything and send to CodeAgent

**Actions:**
1. Validate all previous phases complete
2. Generate combined JSON
3. Create todo list for CodeAgent
4. Send to CodeAgent
5. Tell user "Creating your project structure..."

---

## PERMISSION SYSTEM

**EVERY code change requires user permission:**
- Show file preview with diff
- Options: [Y] Yes, create    [N] No, skip    [E] Esc, stop all

**EVERY terminal command requires user permission:**
- Show command and description
- Options: [Y] Yes, run    [N] No, skip    [E] Esc, stop all

---

## CONTROLLING SUB-AGENTS

### Sending to CodeAgent:
Send complete handoff package with project, tech_stack, design, todos, and instructions.

### Sending to LiveAgent:
Start monitoring with config for file watching, error detection, terminal monitoring, etc.

---

## SEARCH CAPABILITIES

**When to Search:**
- Phase 1: Competitors, common features, market research
- Phase 2: Tech comparison, best frameworks, database options
- Phase 3: Best practices, design patterns, API design

**Search Rules:**
1. Always include year - Add "2025" to get latest info
2. Be specific - Include use case in query
3. Compare options - Search "[A] vs [B] 2025" for comparisons
4. Verify info - Cross-reference multiple sources
5. Summarize for user - Don't dump raw results, give recommendation

---

## ERROR HANDLING

**If user gives incomplete answer:**
- Politely ask for clarification
- Give example of what you need
- Don't move forward until you have the data

**If user wants to go back:**
- Allow editing previous phase
- Re-validate affected phases
- Update JSON accordingly

**If user says something unclear:**
- Ask ONE clarifying question
- Don't assume

---

## FINAL NOTES

1. **Never skip phases** - Complete each before moving on
2. **Always validate** - Check data before proceeding
3. **Keep JSON updated** - Every answer updates the JSON
4. **User is boss** - They can change anything anytime
5. **Be thorough** - Better to ask one more question than miss something
6. **Search when unsure** - Use online search for latest info
7. **Quality over speed** - Take time to get it right"""

    # Phase definitions
    PHASES = {
        1: "idea",
        2: "tech_stack",
        3: "design",
        4: "handoff"
    }

    def __init__(
        self,
        llm_client,
        storage: Storage,
        project_dir: str,
        search_engine=None,
        workflow=None
    ):
        """
        Initialize MainAgent.

        Args:
            llm_client: LLM client for AI interactions
            storage: Storage system for data persistence
            project_dir: Project root directory
            search_engine: Search engine for online research
            workflow: WorkflowController instance (optional)
        """
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
        self.search = search_engine
        self.workflow = workflow

        # Initialize tools
        self.tools = AgentTools(
            project_dir=project_dir,
            storage=storage,
            search_engine=search_engine
        )

        # Sub-agents (initialized lazily)
        self._code_agent = None
        self._live_agent = None

        # State tracking
        self.current_phase = 1
        self.phase_data = {
            "idea": {},
            "tech_stack": {},
            "design": {},
            "handoff": {}
        }
        self.conversation_history = []
        self.questions_asked = []
        self.data_collected = {}

        # System prompt is embedded in class (no file loading needed)

        # Load saved state
        self._load_state()

        console.print("[green]✓ MainAgent initialized[/green]")

    def _load_state(self):
        """Load saved state from storage."""
        state = self.storage.load("main_agent_state")
        if state:
            self.current_phase = state.get("current_phase", 1)
            self.phase_data = state.get("phase_data", self.phase_data)
            self.questions_asked = state.get("questions_asked", [])
            self.data_collected = state.get("data_collected", {})

    def _save_state(self):
        """Save current state to storage."""
        self.storage.save("main_agent_state", {
            "current_phase": self.current_phase,
            "phase_data": self.phase_data,
            "questions_asked": self.questions_asked,
            "data_collected": self.data_collected,
            "updated_at": datetime.now().isoformat()
        })

    # =========================================================================
    # MAIN CHAT INTERFACE
    # =========================================================================

    def chat(self, user_message: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main chat interface - ALL user messages come here.

        Args:
            user_message: User's input message
            user_profile: Optional user profile

        Returns:
            Response dict with message and status
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Detect intent
        intent = self._detect_intent(user_message)

        # Route based on intent
        if intent["type"] == "status":
            return self._handle_status_request()
        elif intent["type"] == "help":
            return self._handle_help()
        elif intent["type"] == "go_back":
            return self._handle_go_back(intent)
        elif intent["type"] == "live_command":
            return self._handle_live_command(user_message, user_profile)
        else:
            # Normal conversation - route to current phase
            return self._process_phase(user_message, user_profile)

    def _detect_intent(self, user_message: str) -> Dict[str, Any]:
        """Detect user intent from message."""
        msg_lower = user_message.lower().strip()

        # Status request
        if any(kw in msg_lower for kw in ["status", "progress", "where are we", "what phase"]):
            return {"type": "status"}

        # Help request
        if any(kw in msg_lower for kw in ["help", "how to", "what can"]):
            return {"type": "help"}

        # Go back request
        go_back_patterns = {
            "idea": ["change idea", "go back to idea", "edit idea", "modify idea"],
            "tech_stack": ["change tech", "go back to tech", "edit tech", "modify tech"],
            "design": ["change design", "go back to design", "edit design", "modify design"]
        }
        for phase, patterns in go_back_patterns.items():
            if any(p in msg_lower for p in patterns):
                return {"type": "go_back", "target_phase": phase}

        # Live mode commands
        if self.current_phase == 4 and self._live_agent:
            live_keywords = ["fix", "error", "test", "deploy", "monitor", "watch"]
            if any(kw in msg_lower for kw in live_keywords):
                return {"type": "live_command"}

        return {"type": "normal"}

    # =========================================================================
    # PHASE PROCESSING
    # =========================================================================

    def _process_phase(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """Process message based on current phase."""
        phase_name = self.PHASES[self.current_phase]

        if phase_name == "idea":
            return self._process_idea_phase(user_message, user_profile)
        elif phase_name == "tech_stack":
            return self._process_tech_stack_phase(user_message, user_profile)
        elif phase_name == "design":
            return self._process_design_phase(user_message, user_profile)
        elif phase_name == "handoff":
            return self._process_handoff_phase(user_message, user_profile)

        return {"message": "Processing...", "status": "in_progress"}

    def _process_idea_phase(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """
        Phase 1: Idea Collection
        Collect project name, type, features, target users, etc.
        """
        # Check for confirmation FIRST (before processing through LLM)
        msg_lower = user_message.lower().strip()
        if self._is_idea_phase_complete():
            if not self.phase_data["idea"].get("confirmed"):
                # Check if user is confirming
                if msg_lower in ["yes", "y", "yep", "correct", "right", "looks good", "✅ yes", "yes, it's ok"]:
                    # User confirmed - mark and move forward
                    self.phase_data["idea"]["confirmed"] = True
                    self._save_state()
                    self.current_phase = 2
                    return {
                        "message": "Perfect! Now let's pick the tech stack. Any preferences, or should I recommend?",
                        "status": "phase_complete",
                        "phase": "idea"
                    }
                elif msg_lower in ["no", "n", "nope", "wrong", "change", "❌ no", "no, i don't like it"]:
                    # User rejected - ask what to change
                    return {
                        "message": "No problem! What would you like to change? Tell me what's wrong or what you'd like different.",
                        "status": "awaiting_input",
                        "phase": "idea"
                    }
                elif msg_lower.startswith("yes but") or msg_lower.startswith("yes, but"):
                    # User wants changes - extract their requirements
                    requirements = user_message.replace("yes but", "").replace("yes, but", "").strip()
                    if requirements:
                        return {
                            "message": f"Got it! You want: {requirements}. Let me update that. What else should I change?",
                            "status": "awaiting_input",
                            "phase": "idea"
                        }
                    else:
                        return {
                            "message": "What would you like to change or add?",
                            "status": "awaiting_input",
                            "phase": "idea"
                        }
                else:
                    # Still waiting for confirmation - show summary
                    return self._show_idea_summary()
        
        # Build context for LLM
        context = self._build_phase_context("idea")

        # Build messages for LLM
        messages = self._build_llm_messages(user_message, context)

        # Get LLM response
        response = self._call_llm(messages)

        # Extract any data from the response
        extracted = self._extract_idea_data(user_message, response)
        if extracted:
            self.phase_data["idea"].update(extracted)
            self.data_collected.update(extracted)
            self._save_state()

        # Check if phase is complete (after processing)
        if self._is_idea_phase_complete():
            if not self.phase_data["idea"].get("confirmed"):
                return self._show_idea_summary()

        return {
            "message": response,
            "status": "in_progress",
            "phase": "idea"
        }

    def _process_tech_stack_phase(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """
        Phase 2: Tech Stack Decision
        Choose frontend, backend, database, auth, deployment, etc.
        """
        # Check for confirmation FIRST
        msg_lower = user_message.lower().strip()
        if self._is_tech_stack_complete():
            if not self.phase_data["tech_stack"].get("confirmed"):
                if msg_lower in ["yes", "y", "yep", "correct", "right", "looks good", "✅ yes", "yes, it's ok"]:
                    self.phase_data["tech_stack"]["confirmed"] = True
                    self._save_state()
                    self.current_phase = 3
                    return {
                        "message": "Excellent! Now let's design everything - database, API, frontend structure. I'll ask you about each part.",
                        "status": "phase_complete",
                        "phase": "tech_stack"
                    }
                elif msg_lower in ["no", "n", "nope", "wrong", "change", "❌ no", "no, i don't like it"]:
                    return {
                        "message": "No problem! What would you like to change in the tech stack?",
                        "status": "awaiting_input",
                        "phase": "tech_stack"
                    }
                elif msg_lower.startswith("yes but") or msg_lower.startswith("yes, but"):
                    requirements = user_message.replace("yes but", "").replace("yes, but", "").strip()
                    if requirements:
                        return {
                            "message": f"Got it! You want: {requirements}. What else should I change?",
                            "status": "awaiting_input",
                            "phase": "tech_stack"
                        }
                    else:
                        return {
                            "message": "What would you like to change in the tech stack?",
                            "status": "awaiting_input",
                            "phase": "tech_stack"
                        }
                else:
                    return self._show_tech_stack_summary()
        
        context = self._build_phase_context("tech_stack")
        messages = self._build_llm_messages(user_message, context)
        response = self._call_llm(messages)

        # Extract tech stack data
        extracted = self._extract_tech_stack_data(user_message, response)
        if extracted:
            self.phase_data["tech_stack"].update(extracted)
            self.data_collected.update(extracted)
            self._save_state()

        # Check if phase is complete (after processing)
        if self._is_tech_stack_complete():
            if not self.phase_data["tech_stack"].get("confirmed"):
                return self._show_tech_stack_summary()

        return {
            "message": response,
            "status": "in_progress",
            "phase": "tech_stack"
        }

    def _process_design_phase(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """
        Phase 3: Complete Design
        Design database, API, frontend, folder structure.
        """
        # Check for confirmation FIRST
        msg_lower = user_message.lower().strip()
        if self._is_design_complete():
            if not self.phase_data["design"].get("confirmed"):
                if msg_lower in ["yes", "y", "yep", "correct", "right", "looks good", "✅ yes", "yes, it's ok"]:
                    self.phase_data["design"]["confirmed"] = True
                    self._save_state()
                    self.current_phase = 4
                    return self._initiate_handoff()
                elif msg_lower in ["no", "n", "nope", "wrong", "change", "❌ no", "no, i don't like it"]:
                    return {
                        "message": "No problem! What would you like to change in the design?",
                        "status": "awaiting_input",
                        "phase": "design"
                    }
                elif msg_lower.startswith("yes but") or msg_lower.startswith("yes, but"):
                    requirements = user_message.replace("yes but", "").replace("yes, but", "").strip()
                    if requirements:
                        return {
                            "message": f"Got it! You want: {requirements}. What else should I change?",
                            "status": "awaiting_input",
                            "phase": "design"
                        }
                    else:
                        return {
                            "message": "What would you like to change in the design?",
                            "status": "awaiting_input",
                            "phase": "design"
                        }
                else:
                    return self._show_design_summary()
        
        context = self._build_phase_context("design")
        messages = self._build_llm_messages(user_message, context)
        response = self._call_llm(messages)

        # Extract design data
        extracted = self._extract_design_data(user_message, response)
        if extracted:
            self.phase_data["design"].update(extracted)
            self._save_state()

        # Check if phase is complete (after processing)
        if self._is_design_complete():
            if not self.phase_data["design"].get("confirmed"):
                return self._show_design_summary()

        return {
            "message": response,
            "status": "in_progress",
            "phase": "design"
        }

    def _process_handoff_phase(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """
        Phase 4: Handoff to CodeAgent
        Package everything and send to CodeAgent for file generation.
        """
        # Check if user confirmed to start generation
        msg_lower = user_message.lower()
        if any(kw in msg_lower for kw in ["yes", "start", "go", "generate", "create"]):
            return self._execute_handoff()
        elif any(kw in msg_lower for kw in ["no", "wait", "change", "modify"]):
            return {
                "message": "No problem! What would you like to change?",
                "status": "awaiting_input"
            }

        return {
            "message": "Ready to generate your project structure? Say 'yes' to start!",
            "status": "awaiting_confirmation"
        }

    # =========================================================================
    # HANDOFF TO CODEAGENT
    # =========================================================================

    def _initiate_handoff(self) -> Dict[str, Any]:
        """Prepare handoff package for CodeAgent."""
        # Build complete handoff package
        handoff_package = {
            "handoff": {
                "from": "MainAgent",
                "to": "CodeAgent",
                "timestamp": datetime.now().isoformat(),
                "project_ready": True
            },
            "project": self.phase_data["idea"],
            "tech_stack": self.phase_data["tech_stack"],
            "design": self.phase_data["design"],
            "todos": [
                {"id": 1, "task": "Create folder structure", "status": "pending"},
                {"id": 2, "task": "Generate database schema", "status": "pending"},
                {"id": 3, "task": "Create configuration files", "status": "pending"},
                {"id": 4, "task": "Create skeleton files", "status": "pending"},
                {"id": 5, "task": "Generate documentation", "status": "pending"},
                {"id": 6, "task": "Install dependencies", "status": "pending"}
            ]
        }

        # Save handoff package
        self.storage.save("handoff_package", handoff_package)
        self.phase_data["handoff"] = handoff_package

        return {
            "message": "Everything is ready! I've designed your complete project structure. Say 'yes' to start creating the files!",
            "status": "ready_for_handoff",
            "phase": "handoff"
        }

    def _execute_handoff(self) -> Dict[str, Any]:
        """Execute handoff - initialize and run CodeAgent."""
        console.print("\n[bold cyan]Starting project generation...[/bold cyan]\n")

        # Initialize CodeAgent if not already
        if not self._code_agent:
            from .code_agent import CodeAgent
            self._code_agent = CodeAgent(
                llm_client=self.llm,
                storage=self.storage,
                project_dir=self.project_dir,
                tools=self.tools
            )

        # Get handoff package
        handoff_package = self.storage.load("handoff_package")

        # Execute CodeAgent
        result = self._code_agent.execute(handoff_package)

        if result.get("success"):
            # Initialize LiveAgent for monitoring
            self._init_live_agent()

            return {
                "message": f"Project structure created successfully!\n\n"
                          f"Files created: {result.get('files_created', 0)}\n"
                          f"Folders created: {result.get('folders_created', 0)}\n\n"
                          f"Next steps:\n{result.get('next_steps', 'Check the docs/SETUP.md for instructions.')}\n\n"
                          f"LiveAgent is now monitoring your project for errors.",
                "status": "complete",
                "phase": "handoff"
            }
        else:
            return {
                "message": f"There was an issue creating some files: {result.get('error', 'Unknown error')}",
                "status": "error",
                "phase": "handoff"
            }

    def _init_live_agent(self):
        """Initialize LiveAgent for monitoring."""
        if not self._live_agent:
            from .live_agent import LiveAgent
            self._live_agent = LiveAgent(
                llm_client=self.llm,
                storage=self.storage,
                project_dir=self.project_dir,
                tools=self.tools
            )
            self._live_agent.start_monitoring()

    # =========================================================================
    # DATA EXTRACTION
    # =========================================================================

    def _extract_idea_data(self, user_message: str, response: str) -> Dict[str, Any]:
        """Extract idea data from conversation."""
        extracted = {}

        # Use LLM to extract structured data
        extraction_prompt = f"""Extract project information from this conversation.

User said: "{user_message}"

Current data collected: {json.dumps(self.data_collected)}

Extract and return ONLY a JSON object with any NEW information found:
{{
    "project_name": "name if mentioned",
    "project_type": "web_app|mobile_app|cli|api if mentioned",
    "core_concept": "description if mentioned",
    "target_users": "who uses it if mentioned",
    "features": ["list of features if mentioned"]
}}

Only include fields that have NEW information. Return empty {{}} if nothing new.
JSON:"""

        try:
            messages = [{"role": "user", "content": extraction_prompt}]
            result = self.llm.chat(messages)
            content = result.get("content", "") if isinstance(result, dict) else str(result)

            # Parse JSON
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Only add non-empty values
                for key, value in data.items():
                    if value and value != "null":
                        extracted[key] = value
        except Exception as e:
            console.print(f"[dim]Extraction: {e}[/dim]")

        return extracted

    def _extract_tech_stack_data(self, user_message: str, response: str) -> Dict[str, Any]:
        """Extract tech stack data from conversation."""
        extracted = {}

        extraction_prompt = f"""Extract tech stack information from this conversation.

User said: "{user_message}"

Current data: {json.dumps(self.phase_data.get('tech_stack', {}))}

Extract and return ONLY a JSON object with any NEW information:
{{
    "frontend": {{"framework": "", "styling": ""}},
    "backend": {{"framework": "", "language": ""}},
    "database": {{"type": "", "provider": ""}},
    "authentication": {{"provider": ""}},
    "deployment": {{"frontend": "", "backend": ""}}
}}

Only include fields with NEW information. Return empty {{}} if nothing new.
JSON:"""

        try:
            messages = [{"role": "user", "content": extraction_prompt}]
            result = self.llm.chat(messages)
            content = result.get("content", "") if isinstance(result, dict) else str(result)

            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for key, value in data.items():
                    if value and value != {} and value != "null":
                        extracted[key] = value
        except Exception as e:
            console.print(f"[dim]Extraction: {e}[/dim]")

        return extracted

    def _extract_design_data(self, user_message: str, response: str) -> Dict[str, Any]:
        """Extract design data from conversation."""
        extracted = {}

        extraction_prompt = f"""Extract design information from this conversation.

User said: "{user_message}"

Current data: {json.dumps(self.phase_data.get('design', {}))}

Extract and return ONLY a JSON object with any NEW information:
{{
    "database": {{
        "tables": [
            {{"name": "users", "columns": [...], "relationships": [...]}},
            ...
        ]
    }},
    "api": {{
        "endpoints": [
            {{"method": "GET", "path": "/api/users", "description": "..."}},
            ...
        ]
    }},
    "frontend": {{
        "pages": ["Home", "Dashboard", ...],
        "components": ["Button", "Header", ...]
    }},
    "folder_structure": {{
        "frontend": ["src", "components", ...],
        "backend": ["app", "routers", ...]
    }}
}}

Only include fields with NEW information. Return empty {{}} if nothing new.
JSON:"""

        try:
            messages = [{"role": "user", "content": extraction_prompt}]
            result = self.llm.chat(messages)
            content = result.get("content", "") if isinstance(result, dict) else str(result)

            # Parse JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for key, value in data.items():
                    if value and value != {} and value != [] and value != "null":
                        extracted[key] = value
        except Exception as e:
            console.print(f"[dim]Extraction: {e}[/dim]")

        return extracted

    # =========================================================================
    # PHASE COMPLETION CHECKS
    # =========================================================================

    def _is_idea_phase_complete(self) -> bool:
        """Check if idea phase has all required data."""
        idea = self.phase_data.get("idea", {})
        required = ["project_name", "project_type", "core_concept", "target_users"]
        features = idea.get("features", [])

        has_required = all(idea.get(key) for key in required)
        has_features = len(features) >= 3 if isinstance(features, list) else bool(features)

        return has_required and has_features

    def _is_tech_stack_complete(self) -> bool:
        """Check if tech stack phase has all required data."""
        tech = self.phase_data.get("tech_stack", {})
        required = ["frontend", "backend", "database"]
        return all(tech.get(key) for key in required)

    def _is_design_complete(self) -> bool:
        """Check if design phase has all required data."""
        design = self.phase_data.get("design", {})
        required = ["database", "api", "frontend", "folder_structure"]
        return all(design.get(key) for key in required)

    # =========================================================================
    # SUMMARIES
    # =========================================================================

    def _show_idea_summary(self) -> Dict[str, Any]:
        """Show idea summary for user confirmation."""
        idea = self.phase_data["idea"]

        summary = f"""
**{idea.get('project_name', 'Your Project')} Summary:**
- Type: {idea.get('project_type', 'Not specified')}
- Concept: {idea.get('core_concept', 'Not specified')}
- For: {idea.get('target_users', 'Not specified')}
- Features: {', '.join(idea.get('features', [])) if isinstance(idea.get('features'), list) else idea.get('features', 'Not specified')}

Does this look right? (yes/no)"""

        return {
            "message": summary,
            "status": "awaiting_confirmation",
            "phase": "idea"
        }

    def _show_tech_stack_summary(self) -> Dict[str, Any]:
        """Show tech stack summary for user confirmation."""
        tech = self.phase_data["tech_stack"]

        frontend = tech.get("frontend", {})
        backend = tech.get("backend", {})
        database = tech.get("database", {})

        summary = f"""
**Tech Stack Summary:**
- Frontend: {frontend.get('framework', 'Not specified')} + {frontend.get('styling', 'Not specified')}
- Backend: {backend.get('framework', 'Not specified')}
- Database: {database.get('type', 'Not specified')} ({database.get('provider', '')})
- Deployment: {tech.get('deployment', {}).get('frontend', 'Not specified')}

Does this look right? (yes/no)"""

        return {
            "message": summary,
            "status": "awaiting_confirmation",
            "phase": "tech_stack"
        }

    def _show_design_summary(self) -> Dict[str, Any]:
        """Show design summary for user confirmation."""
        design = self.phase_data["design"]

        summary = f"""
**Design Summary:**
- Database: {len(design.get('database', {}).get('tables', []))} tables designed
- API: {len(design.get('api', {}).get('endpoints', []))} endpoints planned
- Frontend: {len(design.get('frontend', {}).get('pages', []))} pages planned
- Folder structure ready

Ready to generate the project? (yes/no)"""

        return {
            "message": summary,
            "status": "awaiting_confirmation",
            "phase": "design"
        }

    # =========================================================================
    # LLM HELPERS
    # =========================================================================

    def _build_phase_context(self, phase: str) -> str:
        """Build context for current phase."""
        context = f"""
CURRENT PHASE: {phase.upper()}

DATA COLLECTED SO FAR:
{json.dumps(self.data_collected, indent=2)}

QUESTIONS ALREADY ASKED:
{', '.join(self.questions_asked[-10:]) if self.questions_asked else 'None yet'}

INSTRUCTIONS:
- Ask ONE question at a time
- Keep responses to 2-3 sentences max
- Be conversational and friendly
- Never repeat questions already asked
- Extract data from user's answers
"""
        return context

    def _build_llm_messages(self, user_message: str, context: str) -> List[Dict]:
        """Build messages for LLM call."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\n" + context}
        ]

        # Add recent conversation history
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _call_llm(self, messages: List[Dict]) -> str:
        """Call LLM and return response."""
        try:
            response = self.llm.chat(messages)
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            
            # Filter out help text if user didn't ask for help
            help_indicators = [
                "How I can help:",
                "Useful commands:",
                "What would you like to do?"
            ]
            if any(indicator in content for indicator in help_indicators):
                # This is likely a mistaken help response - ask for clarification
                content = "I want to help you build your project! Could you tell me a bit more about what you'd like to create?"

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })

            return content
        except Exception as e:
            console.print(f"[red]LLM Error: {e}[/red]")
            return "I'm having trouble processing that. Could you try again?"

    # =========================================================================
    # HANDLERS
    # =========================================================================

    def _handle_status_request(self) -> Dict[str, Any]:
        """Handle status request."""
        phase_names = ["Project Idea", "Tech Stack", "Design", "Generation"]
        current_name = phase_names[self.current_phase - 1]

        status_lines = []
        for i, name in enumerate(phase_names, 1):
            if i < self.current_phase:
                status_lines.append(f"✅ {name}")
            elif i == self.current_phase:
                status_lines.append(f"👉 {name} ← current")
            else:
                status_lines.append(f"⏳ {name}")

        return {
            "message": "**Project Progress:**\n\n" + "\n".join(status_lines),
            "status": "info"
        }

    def _handle_help(self) -> Dict[str, Any]:
        """Handle help request."""
        return {
            "message": """**How I can help:**

Just chat normally - tell me what you want to build and I'll guide you step by step.

**Useful commands:**
- "status" - See your progress
- "change idea" - Go back and modify project idea
- "change tech" - Modify technology choices

**When I ask for confirmation:**
- "yes" - Go ahead
- "no" - Cancel or modify

What would you like to do?""",
                "status": "info"
            }

    def _handle_go_back(self, intent: Dict) -> Dict[str, Any]:
        """Handle go back request."""
        target = intent.get("target_phase", "idea")
        phase_map = {"idea": 1, "tech_stack": 2, "design": 3}

        self.current_phase = phase_map.get(target, 1)
        self._save_state()

        return {
            "message": f"No problem! Let's revisit the {target.replace('_', ' ')}. What would you like to change?",
            "status": "phase_change"
        }

    def _handle_live_command(self, user_message: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """Handle live mode commands."""
        if not self._live_agent:
            self._init_live_agent()

        return self._live_agent.handle_command(user_message)

    # =========================================================================
    # CLI COMPATIBILITY METHODS
    # =========================================================================

    def is_new_project(self) -> bool:
        """Check if this is a new project."""
        return self.current_phase == 1 and not self.phase_data["idea"]

    def get_welcome_message(self) -> str:
        """Get welcome message."""
        if self.is_new_project():
            return "Hi! I'm BOTUVIC. What would you like to build today?"
        else:
            phase_name = self.PHASES[self.current_phase]
            return f"Welcome back! We're currently in the {phase_name.replace('_', ' ')} phase."

    def get_current_phase(self) -> Dict[str, Any]:
        """Get current phase info."""
        return {
            "phase_number": self.current_phase,
            "phase_name": self.PHASES[self.current_phase],
            "data": self.phase_data.get(self.PHASES[self.current_phase], {})
        }

    def _generate_conversation_summary(self, history=None) -> Dict[str, Any]:
        """Generate conversation summary."""
        try:
            if history is None:
                history = self.conversation_history

            if not history:
                return {"success": False, "error": "No conversation history"}

            # Generate markdown
            content = "# Conversation Summary\n\n"
            content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            for i, msg in enumerate(history, 1):
                role = "BOTUVIC" if msg.get("role") == "assistant" else "You"
                content += f"## Message {i} - {role}\n\n"
                content += f"{msg.get('content', '')}\n\n"

            # Save to file
            summary_path = os.path.join(self.project_dir, "conversation_summary.md")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "file_path": summary_path,
                "total_messages": len(history)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
