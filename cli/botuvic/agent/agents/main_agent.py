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

### PHASE 1: PRODUCT ARCHITECTURE & DISCOVERY

**Goal:** Deeply understand the "Why", "How", "Data", and "Cost" before writing code.
**Role:** You are a Senior Product Architect. Do not just take orders; guide the user to a buildable plan.

**THE DISCOVERY PROTOCOL (Execute in order):**

**1. The Vision & "The Why"**
   - **Context:** Always refer to the project by name (e.g., "For [Project Name], what is...").
   - **One-Sentence Rule:** "If we can't explain it in one sentence, we aren't ready." Help the user refine this.
   - **The Pain:** Ask "What specific pain does the user feel right now that makes them need this?"

**2. The "Deep Search" Validation (Mandatory for Unknowns)**
   - **Trigger:** When the user mentions a specific market, tech, or competitor.
   - **The 3-5 Search Rule:** Do NOT just run one search. You must:
     1. Search Broad: "Best practices for building [Type] app 2025"
     2. Search Specific: "Key features of [Competitor X]"
     3. Search Technical: "[Tech Stack] limitations for [Feature]"
     4. Search Cost: "API pricing for [Service] 2025"
     5. **Validate:** Cross-reference these 3-5 results before giving advice.

**3. The "Walkthrough" (Users & Flows)**
   - **The Journey:** Ask the user to *walk you through one specific task* step-by-step.
   - **Gap Detection:** If they miss a step (e.g., "User logs in" -> "User buys"), interrupt: "How do they find the item? Do they need a search bar?"

**4. The "AI Cost" Reality Check (Crucial for AI Projects)**
   - **If project uses AI (LLMs, Image Gen, etc.):**
     - You MUST search for current API pricing (OpenAI, Anthropic, Replicate, etc.).
     - You MUST calculate an estimate: "100 users x 10 messages/day = ~30k tokens. At $5/1M tokens, that's $0.15/day."
     - **Ask:** "Can your business model afford this monthly cost?"

**5. The Data & Complexity**
   - **Entities:** Identify the nouns (Users, Orders, Projects).
   - **Real-time:** "Does this need live updates (sockets) or is refresh okay?"

**6. The "MVP" Reality Check**
   - **Senior Rule:** "If V1 has more than 5 core features, it's not an MVP."
   - **The "Cut" List:** Explicitly ask: "What is **OUT** of scope for V1?"

**PHASE 1 OUTPUT SUMMARY (Must be presented to user for confirmation):**
---------------------------------------------------------
**PROJECT BLUEPRINT: [Project Name]**
**1. The Core:** [One sentence pitch]
**2. The Problem:** [The pain point solved]
**3. Target:** [Who uses it - Validated by Search]
**4. User Journey:** [Step-by-step flow of main task]
**5. AI Cost Estimate:** [Monthly estimate based on current API prices] (IF APPLICABLE)
**6. Primary Features (MVP):**
   - [Feature 1]
   - [Feature 2]
   - [Feature 3]
   - [Feature 4]
   - [Feature 5]
**7. Explicitly OUT of Scope:** [What we are NOT building]
**8. Data Entities:** [Key database objects]
**9. Technical Constraints:** [Platform, Scale, Budget]
---------------------------------------------------------

**Phase 1 Checklist (Must pass to proceed):**
- [ ] Vision is clear (One sentence test passed)
- [ ] User flow is defined step-by-step
- [ ] **AI Costs estimated and approved by user** (if applicable)
- [ ] **Market/Competitors validated via 3-5 searches**
- [ ] Data entities are identified
- [ ] MVP is scoped (Max 5 features)
- [ ] User confirmed the Blueprint

---

### PHASE 2: TECH STACK ARCHITECTURE

**Goal:** Design a cohesive stack that covers ALL target platforms (Mobile, Desktop, CLI, Web) efficiently.
**Role:** Senior Tech Lead. You already know the user's profile; optimize for their constraints and the project's platforms.

**THE SELECTION PROTOCOL (Execute in order):**

**1. Platform-First Strategy (The Core Decision)**
   - **Analyze Target Platforms:**
     - If **Mobile (iOS/Android) + Web**: You MUST search/evaluate **Cross-Platform** options (Flutter, React Native/Expo) vs. **Native**.
     - If **Desktop**: Evaluate Electron vs. Tauri vs. Flutter Desktop.
     - If **Terminal/CLI**: Evaluate Python (Typer/Click), Go (Cobra), or Rust (Clap) based on performance needs.
   - **The "Code Sharing" Rule:** If building for multiple platforms (e.g., Web + Mobile), prioritize stacks that share logic (e.g., TRPC, shared Typescript packages, or Dart/Flutter).
   - **Monorepo vs Multi-repo:** Decide if Monorepo (Turborepo/Nx) or separate repos based on team size and deployment needs.

**2. Profile-Based Selection (Silent Check)**
   - **Do NOT ask** "What language do you know?" (You have the User Profile from Phase 1).
   - **Action:** Select the backend/language that aligns with the User's Profile *and* the Platform requirement.
   - **Conflict Detection:** If the profile says "Python User" but they want a "High-performance iOS app," **Search & Warn:** "Python (Kivy/BeeWare) might lag on iOS. I recommend learning Swift or React Native for this. Proceed with Python anyway?"

**3. The "Deep Search" for Best-in-Class (Mandatory)**
   - **Search Action:** Do not guess. Search for the current state of the art:
     - *"Best tech stack for [Web + Mobile + CLI] project 2025"*
     - *"Current limitations of [Framework X] for [Feature Y]"*
     - *"[Framework A] vs [Framework B] for [Use Case] 2025"*
   - **Cost Check:** Search pricing for hosted components (e.g., "Vercel pricing vs VPS for high bandwidth 2025").

**4. The AI Stack (If Phase 1 involves AI)**
   - **Vector DB:** Pinecone / Weaviate / Supabase (pgvector) / Qdrant.
   - **Orchestration:** LangChain / LlamaIndex / Vercel AI SDK / LangGraph.
   - **Model Serving:** OpenAI API / Anthropic / Local (Ollama) / Replicate / Together AI.
   - **Cost Validation:** Cross-reference Phase 1 AI cost estimates with chosen providers.

**5. Backend & Data Strategy**
   - **API Type:** REST vs. GraphQL vs. gRPC vs. tRPC (Crucial for Mobile/CLI clients).
   - **Real-time:** If "Live Updates" required → Search best WebSocket solution for the specific backend (e.g., FastAPI WebSockets vs. Supabase Realtime vs. Socket.io).
   - **Database Choice:** SQL (PostgreSQL/MySQL) vs. NoSQL (MongoDB) vs. Hybrid (Supabase) based on data structure from Phase 1.

**PHASE 2 OUTPUT SUMMARY (Must be presented to user for confirmation):**
---------------------------------------------------------
**ARCHITECTURE STACK: [Project Name]**

**1. Platform Strategy:** [Monorepo (Turborepo/Nx) / Multi-repo] + [How we share code across platforms]

**2. Frontend(s):**
   - **Web:** [Framework + Styling + State Management]
   - **Mobile:** [Framework (if applicable)]
   - **Desktop:** [Framework (if applicable)]
   - **CLI:** [Library (if applicable)]

**3. Backend Core:** [Language + Framework + API Type (REST/GraphQL/tRPC)]

**4. Database & AI:**
   - **Primary DB:** [Database + Provider]
   - **Vector DB:** [Vector DB (if AI project)]
   - **Model Provider:** [LLM Provider (if AI project)]

**5. Infrastructure:**
   - **Auth:** [Auth Provider]
   - **Storage:** [File Storage (if needed)]
   - **Hosting:** [Deployment Platform(s)]

**6. Rationale:** [Why this specific combo works for User's Profile + These Platforms + Cost Constraints]
---------------------------------------------------------

**Phase 2 Checklist (Must pass before Phase 3):**
- [ ] Stack covers ALL target platforms (Mobile/Desktop/Web/CLI) defined in Phase 1
- [ ] Backend API is compatible with all clients (Mobile, CLI, Web can all access it)
- [ ] **AI Stack defined** (Vector DB + LLM Model + Orchestration) if AI project
- [ ] Selection aligns with User Profile (or explicit warnings given for mismatches)
- [ ] **External APIs & Costs** validated via Search (hosting, AI, third-party services)
- [ ] Code sharing strategy defined for multi-platform projects
- [ ] Monorepo vs Multi-repo decision made
- [ ] User confirmed the Stack

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
        """Extract idea data from conversation per new Phase 1 blueprint."""
        extracted = {}

        # Use LLM to extract structured data per new Phase 1 requirements
        extraction_prompt = f"""Extract project information from this conversation per the new Phase 1 blueprint.

User said: "{user_message}"

Current data collected: {json.dumps(self.data_collected)}

Extract and return ONLY a JSON object with any NEW information found:
{{
    "project_name": "name if mentioned",
    "project_type": "web_app|mobile_app|cli|api if mentioned",
    "core_concept": "one sentence pitch if mentioned",
    "pain_point": "specific pain user feels if mentioned",
    "target_users": "who uses it if mentioned",
    "user_journey": "step-by-step flow of main task if mentioned",
    "features": ["list of MVP features if mentioned (max 5)"],
    "out_of_scope": ["what is NOT being built in v1 if mentioned"],
    "data_entities": ["key database objects like Users, Orders if mentioned"],
    "technical_constraints": "platform, scale, budget if mentioned",
    "ai_cost_estimate": "monthly cost estimate if AI features mentioned",
    "competitors_validated": "true if 3-5 searches done",
    "search_results": ["list of search findings if searches were done"]
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
                    if value and value != "null" and value != [] and value != {}:
                        extracted[key] = value
        except Exception as e:
            console.print(f"[dim]Extraction: {e}[/dim]")

        return extracted

    def _extract_tech_stack_data(self, user_message: str, response: str) -> Dict[str, Any]:
        """Extract tech stack data from conversation per new Phase 2 architecture."""
        extracted = {}

        extraction_prompt = f"""Extract tech stack information from this conversation per the new Phase 2 architecture.

User said: "{user_message}"

Current data: {json.dumps(self.phase_data.get('tech_stack', {}))}

Extract and return ONLY a JSON object with any NEW information:
{{
    "platform_strategy": "Monorepo (Turborepo/Nx) or Multi-repo + code sharing approach if mentioned",
    "frontends": {{
        "web": "Framework + Styling + State Management if mentioned",
        "mobile": "Framework (React Native/Flutter/Native) if mentioned",
        "desktop": "Framework (Electron/Tauri/Flutter) if mentioned",
        "cli": "Library (Typer/Click/Cobra/Clap) if mentioned"
    }},
    "backend": {{
        "language": "Language if mentioned",
        "framework": "Framework if mentioned",
        "api_type": "REST/GraphQL/gRPC/tRPC if mentioned"
    }},
    "database": {{
        "type": "SQL/NoSQL/Hybrid if mentioned",
        "provider": "PostgreSQL/MySQL/MongoDB/Supabase if mentioned"
    }},
    "vector_db": "Pinecone/Weaviate/Supabase/Qdrant if AI project",
    "model_provider": "OpenAI/Anthropic/Ollama/Replicate if AI project",
    "infrastructure": {{
        "auth": "Auth provider if mentioned",
        "storage": "File storage if mentioned",
        "hosting": "Deployment platform(s) if mentioned"
    }},
    "rationale": "Why this stack works for user's profile and platforms if mentioned",
    "search_results": ["list of search findings if searches were done"],
    "warnings": ["any profile mismatches or concerns if mentioned"]
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
                    if value and value != {} and value != [] and value != "null":
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
        """Check if idea phase has all required data per new Phase 1 blueprint."""
        idea = self.phase_data.get("idea", {})
        
        # Required fields per new Phase 1 blueprint
        required = [
            "project_name",           # The Core (project name)
            "core_concept",           # One sentence pitch
            "pain_point",             # The problem solved
            "target_users",           # Who uses it
            "user_journey",           # Step-by-step flow
            "data_entities",          # Key database objects
        ]
        
        # Check features (max 5 for MVP)
        features = idea.get("features", [])
        has_features = len(features) >= 3 and len(features) <= 5 if isinstance(features, list) else bool(features)
        
        # Check required fields
        has_required = all(idea.get(key) for key in required)
        
        # Check OUT of scope is defined
        has_out_of_scope = bool(idea.get("out_of_scope"))
        
        return has_required and has_features and has_out_of_scope

    def _is_tech_stack_complete(self) -> bool:
        """Check if tech stack phase has all required data per new Phase 2 architecture."""
        tech = self.phase_data.get("tech_stack", {})
        
        # Required fields per new Phase 2 architecture
        required = [
            "platform_strategy",      # Monorepo/Multi-repo + code sharing
            "backend",                # Backend core
            "database",               # Primary database
            "infrastructure"          # Auth, Storage, Hosting
        ]
        
        # Check required fields
        has_required = all(tech.get(key) for key in required)
        
        # Check that at least one frontend is defined (web, mobile, desktop, or cli)
        frontends = tech.get("frontends", {})
        has_frontend = bool(frontends.get("web") or frontends.get("mobile") or 
                           frontends.get("desktop") or frontends.get("cli"))
        
        # Check rationale is provided
        has_rationale = bool(tech.get("rationale"))
        
        return has_required and has_frontend and has_rationale

    def _is_design_complete(self) -> bool:
        """Check if design phase has all required data."""
        design = self.phase_data.get("design", {})
        required = ["database", "api", "frontend", "folder_structure"]
        return all(design.get(key) for key in required)

    # =========================================================================
    # SUMMARIES
    # =========================================================================

    def _show_idea_summary(self) -> Dict[str, Any]:
        """Show idea summary for user confirmation per new Phase 1 blueprint."""
        idea = self.phase_data["idea"]

        # Format features list
        features = idea.get('features', [])
        if isinstance(features, list):
            features_text = '\n'.join([f"   - {f}" for f in features])
        else:
            features_text = f"   - {features}"

        # Format OUT of scope list
        out_of_scope = idea.get('out_of_scope', [])
        if isinstance(out_of_scope, list):
            out_text = '\n'.join([f"   - {item}" for item in out_of_scope])
        else:
            out_text = f"   - {out_of_scope}"

        # Format data entities
        entities = idea.get('data_entities', [])
        if isinstance(entities, list):
            entities_text = ', '.join(entities)
        else:
            entities_text = entities

        # Build summary per new blueprint format
        summary = f"""
---------------------------------------------------------
**PROJECT BLUEPRINT: {idea.get('project_name', 'Your Project')}**

**1. The Core:** {idea.get('core_concept', 'Not specified')}

**2. The Problem:** {idea.get('pain_point', 'Not specified')}

**3. Target:** {idea.get('target_users', 'Not specified')}

**4. User Journey:** {idea.get('user_journey', 'Not specified')}

**5. AI Cost Estimate:** {idea.get('ai_cost_estimate', 'N/A - No AI features')}

**6. Primary Features (MVP):**
{features_text}

**7. Explicitly OUT of Scope:**
{out_text}

**8. Data Entities:** {entities_text}

**9. Technical Constraints:** {idea.get('technical_constraints', 'Not specified')}
---------------------------------------------------------

Does this look right? (yes/no)"""

        return {
            "message": summary,
            "status": "awaiting_confirmation",
            "phase": "idea"
        }

    def _show_tech_stack_summary(self) -> Dict[str, Any]:
        """Show tech stack summary for user confirmation per new Phase 2 architecture."""
        tech = self.phase_data["tech_stack"]

        # Get frontends
        frontends = tech.get("frontends", {})
        web = frontends.get("web", "N/A")
        mobile = frontends.get("mobile", "N/A")
        desktop = frontends.get("desktop", "N/A")
        cli = frontends.get("cli", "N/A")

        # Get backend
        backend = tech.get("backend", {})
        if isinstance(backend, dict):
            backend_text = f"{backend.get('language', '')} + {backend.get('framework', '')} + {backend.get('api_type', 'REST')}"
        else:
            backend_text = str(backend)

        # Get database & AI
        database = tech.get("database", {})
        if isinstance(database, dict):
            db_text = f"{database.get('type', 'Not specified')} ({database.get('provider', '')})"
        else:
            db_text = str(database)

        vector_db = tech.get("vector_db", "N/A")
        model_provider = tech.get("model_provider", "N/A")

        # Get infrastructure
        infrastructure = tech.get("infrastructure", {})
        if isinstance(infrastructure, dict):
            auth = infrastructure.get("auth", "Not specified")
            storage = infrastructure.get("storage", "N/A")
            hosting = infrastructure.get("hosting", "Not specified")
        else:
            auth = "Not specified"
            storage = "N/A"
            hosting = "Not specified"

        # Build summary per new architecture format
        summary = f"""
---------------------------------------------------------
**ARCHITECTURE STACK: {tech.get('project_name', 'Your Project')}**

**1. Platform Strategy:** {tech.get('platform_strategy', 'Not specified')}

**2. Frontend(s):**
   - **Web:** {web}
   - **Mobile:** {mobile}
   - **Desktop:** {desktop}
   - **CLI:** {cli}

**3. Backend Core:** {backend_text}

**4. Database & AI:**
   - **Primary DB:** {db_text}
   - **Vector DB:** {vector_db}
   - **Model Provider:** {model_provider}

**5. Infrastructure:**
   - **Auth:** {auth}
   - **Storage:** {storage}
   - **Hosting:** {hosting}

**6. Rationale:** {tech.get('rationale', 'Not specified')}
---------------------------------------------------------

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
