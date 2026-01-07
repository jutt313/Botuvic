"""Main BOTUVIC agent class"""

import os
import json
from pathlib import Path
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner

from .system_prompt import SYSTEM_PROMPT
from .utils.storage import Storage
from .utils.search import SearchEngine
from .llm.manager import LLMManager
from .functions import executor, scanner, structure
from .functions.roadmap import RoadmapGenerator
from .functions.tracker import ProgressTracker
from .functions.verifier import PhaseVerifier
from .functions.error_handler import ErrorHandler
from .functions.git_manager import GitManager
from .functions.reporter import ReportGenerator
from .workflow_controller import WorkflowController, Phase
from .file_generators import FileGenerator
from .database_setup import DatabaseSetup
from .auto_installer import AutoInstaller
from .live_mode import LiveModeController

# Console for visual feedback
console = Console()

class BotuvicAgent:
    """
    Main BOTUVIC agent that orchestrates all project management activities.
    """
    
    def __init__(self, project_dir=None):
        """
        Initialize the agent.
        
        Args:
            project_dir: Path to project directory. If None, uses current directory.
        """
        self.project_dir = project_dir or os.getcwd()
        self.storage = Storage(self.project_dir)
        self.search = SearchEngine()
        
        # Initialize LLM manager
        self.llm_manager = LLMManager(self.search, self.storage)
        
        # Try to configure with OpenAI API key from env if available
        # This maintains backward compatibility
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Load .env from multiple possible locations
        possible_env_paths = [
            Path(__file__).parent.parent.parent.parent.parent / ".env",
            Path.cwd() / ".env",
            Path.cwd().parent / ".env",
            Path.home() / ".botuvic" / ".env",
        ]
        
        for env_path in possible_env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break
        else:
            load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and not self.llm_manager.is_configured():
            # Auto-configure with OpenAI if key is available
            try:
                self.llm_manager.configure_llm(
                    provider="OpenAI",
                    model="gpt-4o",
                    api_key=openai_key
                )
            except:
                # If configuration fails, continue without LLM
                pass
        
        # Create a wrapper for backward compatibility with modules that expect LLMClient
        class LLMWrapper:
            def __init__(self, manager):
                self.manager = manager
            
            def chat(self, messages, functions=None):
                if not self.manager.is_configured():
                    raise ValueError(
                        "LLM not configured. Please configure an LLM provider first.\n"
                        "Use: discover_llm_models and configure_llm functions"
                    )
                return self.manager.chat(messages, functions=functions)
        
        self.llm = LLMWrapper(self.llm_manager)
        
        # Initialize all modules
        self.roadmap_gen = RoadmapGenerator(self.llm, self.storage)
        self.tracker = ProgressTracker(self.storage)
        # Pass scanner module function to verifier
        self.verifier = PhaseVerifier(self.llm, self.storage, scanner.scan_project)
        self.error_handler = ErrorHandler(self.llm, self.storage)
        self.git = GitManager(self.llm, self.storage, self.project_dir)
        self.reporter = ReportGenerator(self.storage)
        
        # Determine mode based on .botuvic/ existence
        self.mode = "existing" if self.storage.exists() else "new"

        # Load user profile from storage if it exists
        # (Profile is saved from database when project is created)
        user_profile = self.storage.load("user_profile")

        # Initialize workflow controller with user profile
        self.workflow = WorkflowController(self.storage, user_profile=user_profile)

        # Initialize database setup and file generators
        self.db_setup = DatabaseSetup(self.project_dir, self.storage)
        self.file_generator = FileGenerator(self.project_dir, self.storage, self.llm_manager)
        self.auto_installer = AutoInstaller(self.project_dir)
        
        # Initialize Phase 10 Live Mode Controller
        self.live_mode = LiveModeController(self, self.project_dir)

        # Load context if existing project
        self.context = self._load_context()

        # Perform initial scan for environment detection (Always scan root)
        self.initial_scan = scanner.scan_project(self.project_dir)

        # Conversation history - start with system prompt
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Load conversation history from local storage on startup
        saved_history = self.storage.load("history")
        if saved_history and len(saved_history) > 0:
            # Add all saved messages to maintain context across sessions
            for msg in saved_history:
                self.messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        
    def _load_context(self):
        """Load project context from storage."""
        if self.mode == "existing":
            return {
                "profile": self.storage.load("profile"),
                "project": self.storage.load("project"),
                "roadmap": self.storage.load("roadmap"),
                "progress": self.storage.load("progress"),
            }
        return {}
    
    def _build_context_message(self):
        """Build context message for LLM including workflow state."""
        context_parts = []

        # Add workflow context (this includes phase info and instructions)
        workflow_context = self.workflow.get_workflow_context()
        context_parts.append(workflow_context)

        # Add mode
        context_parts.append(f"\nMODE: {self.mode.upper()} PROJECT")

        # Add user profile if exists
        if self.context.get("profile"):
            profile = self.context["profile"]
            context_parts.append(f"\nUSER PROFILE:")
            context_parts.append(f"- Experience: {profile.get('experience')}")
            context_parts.append(f"- Skills: {', '.join(profile.get('tech_knowledge', []))}")
            context_parts.append(f"- Help level: {profile.get('help_level')}")
            context_parts.append(f"- AI tools: {', '.join(profile.get('ai_tools', []))}")

        # Add user tone (communication style)
        user_tone = self.storage.load("user_tone")
        if user_tone and user_tone.get("current"):
            tone = user_tone["current"]
            context_parts.append(f"\nUSER COMMUNICATION STYLE:")
            context_parts.append(f"- Writing style: {tone.get('style', 'neutral')} (Match this!)")
            context_parts.append(f"- Message length: {tone.get('length', 'medium')} (Keep responses {tone.get('length', 'medium')})")
            context_parts.append(f"- Mood: {tone.get('mood', 'professional')} (Be {tone.get('mood', 'professional')})")
            context_parts.append(f"IMPORTANT: Mirror the user's tone - if they're casual, be casual. If they're brief, be brief.")

        # Add project info if exists
        if self.context.get("project"):
            project = self.context["project"]
            context_parts.append(f"\nPROJECT:")
            context_parts.append(f"- Idea: {project.get('idea')}")
            context_parts.append(f"- Tech stack: {json.dumps(project.get('tech_stack', {}))}")
            context_parts.append(f"- Current phase: {project.get('current_phase', 1)}")

        # Add progress if exists
        if self.context.get("progress"):
            progress = self.context["progress"]
            context_parts.append(f"\nPROGRESS:")
            context_parts.append(f"- Completed tasks: {progress.get('completed', 0)}")
            context_parts.append(f"- Total tasks: {progress.get('total', 0)}")

        # Add Existing Files Context (Architecture Detection)
        if self.initial_scan and self.initial_scan.get("total_files", 0) > 0:
            context_parts.append(f"\nPROJECT CONTEXT (FILES FOUND IN DIRECTORY):")
            context_parts.append(f"- Total files: {self.initial_scan.get('total_files')}")
            context_parts.append(f"- Extensions found: {', '.join(self.initial_scan.get('extensions_found', []))}")
            
            # Highlight key indicators (iOS, Python, Node, etc.)
            exts = self.initial_scan.get("extensions_found", [])
            indicators = []
            if ".swift" in exts or ".xcodeproj" in exts: indicators.append("iOS/Swift Project")
            if ".kt" in exts or ".gradle" in exts: indicators.append("Android/Kotlin Project")
            if "package.json" in [os.path.basename(f['path']) for f in self.initial_scan.get('files', [])]: indicators.append("Node.js/Web Project")
            if ".py" in exts: indicators.append("Python Project")
            
            if indicators:
                context_parts.append(f"- Environment detection: {', '.join(indicators)}")
            
            # List top level files to give the AI a "breadcrumb"
            top_level = [f['path'] for f in self.initial_scan.get('files', []) if "/" not in f['path']]
            if top_level:
                context_parts.append(f"- Root files: {', '.join(top_level[:15])}")

        return "\n".join(context_parts)

    def get_welcome_message(self):
        """Get welcome message for new or returning users."""
        return self.workflow.get_welcome_message()

    def is_new_project(self):
        """Check if this is a new project."""
        return self.workflow.is_new_project()

    def get_current_phase(self):
        """Get current workflow phase info."""
        return self.workflow.get_current_phase_info()

    def advance_phase(self):
        """Advance to next phase."""
        from .workflow_controller import Phase

        self.workflow.phase_complete[self.workflow.current_phase] = True

        # Get current phase value (int) for comparison
        current_val = self.workflow.current_phase.value
        max_phase = len(Phase)

        # Calculate next phase
        if current_val < max_phase:
            next_phase_val = current_val + 1
            self.workflow.current_phase = Phase(next_phase_val)
            self.workflow.save_state()
        else:
            next_phase_val = current_val

        return {
            "action": "phase_complete" if next_phase_val <= max_phase else "workflow_complete",
            "success": True,
            "current_phase": current_val,
            "next_phase": next_phase_val,
            "next_phase_name": self.workflow.get_phase_name() if hasattr(self.workflow, 'get_phase_name') else f"Phase {next_phase_val}"
        }

    def _check_batch_mode_advance(self):
        """Check if we have complete data for batch mode and auto-advance phases."""
        from .workflow_controller import Phase

        pd = self.workflow.phase_data

        # Check what data we have
        has_idea = bool(pd.core_idea)
        has_features = bool(pd.main_features)
        has_tech_stack = pd.tech_stack_locked
        has_database = bool(pd.database_schema)
        has_backend = bool(pd.backend_architecture)
        has_frontend = bool(pd.frontend_design)

        # Count how much complete data we have
        complete_count = sum([has_idea, has_features, has_tech_stack, has_database, has_backend, has_frontend])

        # If we have 4+ pieces of data, we're in batch mode - advance phases
        if complete_count >= 4:
            console.print(f"[bold cyan]Batch mode detected: {complete_count}/6 specs provided[/bold cyan]")

            # Auto-advance through phases based on available data
            current = self.workflow.current_phase.value

            # Phase 1 complete if we have idea + features
            if current == Phase.IDEA_COLLECTION.value and has_idea and has_features:
                self.workflow.phase_complete[Phase.IDEA_COLLECTION] = True
                self.workflow.current_phase = Phase.TECH_STACK
                console.print(f"[#10B981]  → Phase 1 complete (idea + features)[/#10B981]")

            # Phase 2 complete if we have tech stack
            current = self.workflow.current_phase.value
            if current == Phase.TECH_STACK.value and has_tech_stack:
                self.workflow.phase_complete[Phase.TECH_STACK] = True
                self.workflow.current_phase = Phase.DEEP_DISCUSSIONS
                console.print(f"[#10B981]  → Phase 2 complete (tech stack)[/#10B981]")

            # Phase 3 complete if we have database + backend + frontend
            current = self.workflow.current_phase.value
            if current == Phase.DEEP_DISCUSSIONS.value and has_database and has_backend and has_frontend:
                self.workflow.phase_complete[Phase.DEEP_DISCUSSIONS] = True
                self.workflow.current_phase = Phase.CREDENTIALS
                console.print(f"[#10B981]  → Phase 3 complete (db + backend + frontend)[/#10B981]")

            # Skip credentials phase in batch mode (Phase 4)
            current = self.workflow.current_phase.value
            if current == Phase.CREDENTIALS.value:
                self.workflow.phase_complete[Phase.CREDENTIALS] = True
                self.workflow.current_phase = Phase.PROJECT_SETUP
                console.print(f"[#10B981]  → Phase 4 skipped (batch mode)[/#10B981]")

            self.workflow.save_state()

    def generate_project_files(self):
        """Generate all project documentation files."""
        return self.file_generator.generate_all()

    def create_project_structure(self, tech_stack=None):
        """Create project folder structure and base files."""
        if tech_stack is None:
            project = self.storage.load("project") or {}
            tech_stack = project.get("tech_stack", {})

        # Get structure
        structure_info = self.file_generator.generate_project_structure(tech_stack)

        # Create folders
        for folder in structure_info.get("folders", []):
            folder_path = os.path.join(self.project_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            console.print(f"[#A855F7]⏺[/#A855F7] Created folder: {folder}")

        # Create base files
        results = self.file_generator.create_base_files(tech_stack)
        for file_path, success in results.items():
            if success:
                console.print(f"[#A855F7]⏺[/#A855F7] Created file: {file_path}")

        return results
    
    def chat(self, user_message, history=None):
        """
        Main chat interface with the agent.

        Args:
            user_message: User's input message
            history: Optional conversation history from database

        Returns:
            Agent's response
        """
        # If history is provided, rebuild messages from it
        if history is not None and len(history) > 0:
            # Clear current messages except system prompt
            system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
            self.messages = system_messages

            # Add ALL history messages to maintain full conversation context
            for msg in history:
                self.messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("message")
                })

        # Update user tone profile based on their message
        user_tone = self._update_user_tone(user_message)

        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Add current context (includes user tone)
        context_message = self._build_context_message()
        if context_message:
            # Add context as system message
            context_msg = {
                "role": "system",
                "content": f"CURRENT CONTEXT:\n{context_message}"
            }
            # Insert before last user message
            self.messages.insert(-1, context_msg)
        
        # Get available functions
        functions = self._get_available_functions()
        
        # Get LLM response with function calling
        response = self.llm.chat(
            messages=self.messages,
            functions=functions
        )

        # Keep processing tool calls until LLM is done (loop until no more tool_calls)
        max_iterations = 10  # Safety limit
        iteration = 0

        while response.get("tool_calls") and iteration < max_iterations:
            iteration += 1

            # Add the assistant message with tool_calls
            assistant_msg = {
                "role": "assistant",
                "content": response.get("content") or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"]
                        }
                    }
                    for tc in response["tool_calls"]
                ]
            }
            self.messages.append(assistant_msg)

            # Process all tool calls in this batch
            for tool_call in response["tool_calls"]:
                try:
                    function_response = self._execute_function(tool_call)
                except Exception as e:
                    # If function execution fails, create error response
                    console.print(f"[red]Error executing {tool_call['name']}: {str(e)}[/red]")
                    function_response = {
                        "success": False,
                        "error": str(e),
                        "function": tool_call["name"]
                    }

                # Add function response to messages
                # Handle non-serializable objects (like PhaseData)
                try:
                    if isinstance(function_response, dict):
                        # Convert any non-serializable values to strings
                        serializable_response = {}
                        for k, v in function_response.items():
                            try:
                                json.dumps(v)  # Test if serializable
                                serializable_response[k] = v
                            except (TypeError, ValueError):
                                serializable_response[k] = str(v)
                        content = json.dumps(serializable_response)
                    else:
                        content = json.dumps(function_response)
                except (TypeError, ValueError):
                    # Fallback: convert to string
                    content = json.dumps({"result": str(function_response)})
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["name"],
                    "content": content
                })

            # Get next response - might have more tool calls
            response = self.llm.chat(
                messages=self.messages,
                functions=functions
            )
        
        # Add assistant response to history
        assistant_message = response.get("content", "")
        self.messages.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Save conversation to history
        history = self.storage.load("history") or []
        history.append({
            "role": "user",
            "content": user_message
        })
        history.append({
            "role": "assistant",
            "content": assistant_message
        })
        self.storage.save("history", history)
        
        return assistant_message
    
    def _get_available_functions(self):
        """Define functions available to the agent."""
        return [
            {
                "name": "search_online",
                "description": "Search the web for information, best practices, and solutions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_command",
                "description": "Execute a terminal command and capture output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command string to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path relative to project root"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Create or update a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path relative to project root"
                        },
                        "content": {
                            "type": "string",
                            "description": "File content"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "save_to_storage",
                "description": "Save data to .botuvic/ storage (profile, project, roadmap, progress, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Storage key (profile, project, roadmap, progress, etc.)"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to save"
                        }
                    },
                    "required": ["key", "data"]
                }
            },
            {
                "name": "load_from_storage",
                "description": "Load data from .botuvic/ storage",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Storage key to load"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "scan_project",
                "description": "Scan all project files and analyze code structure",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "create_project_structure",
                "description": "Create project folders and initial files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "structure": {
                            "type": "object",
                            "description": "Project structure definition with folders and files"
                        }
                    },
                    "required": ["structure"]
                }
            },
            {
                "name": "generate_roadmap",
                "description": "Generate project roadmap with phases and tasks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_info": {"type": "object"},
                        "user_profile": {"type": "object"}
                    },
                    "required": ["project_info", "user_profile"]
                }
            },
            {
                "name": "track_progress",
                "description": "Get current project progress",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "verify_phase",
                "description": "Verify if phase is complete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phase_number": {"type": "integer"}
                    },
                    "required": ["phase_number"]
                }
            },
            {
                "name": "detect_and_fix_error",
                "description": "Analyze and fix an error",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "terminal_output": {"type": "string"}
                    },
                    "required": ["terminal_output"]
                }
            },
            {
                "name": "git_commit",
                "description": "Commit changes to git",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "phase_number": {"type": "integer"}
                    }
                }
            },
            {
                "name": "generate_reports",
                "description": "Generate all project reports",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "discover_llm_models",
                "description": "Search online for latest LLM models from all providers",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "configure_llm",
                "description": "Configure LLM provider, model, and settings. User must provide API key.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "description": "Provider name (e.g., 'OpenAI', 'Anthropic', 'Ollama')"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model ID (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')"
                        },
                        "api_key": {
                            "type": "string",
                            "description": "API key for the provider (required)"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Sampling temperature (0-2), default 0.7"
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate, default 4000"
                        }
                    },
                    "required": ["provider", "model", "api_key"]
                }
            },
            {
                "name": "update_llm_settings",
                "description": "Update LLM settings (temperature, max_tokens, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number"},
                        "max_tokens": {"type": "integer"},
                        "top_p": {"type": "number"}
                    }
                }
            },
            {
                "name": "get_llm_providers",
                "description": "Get list of available LLM providers",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_llm_models",
                "description": "Get available models for a specific provider",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "description": "Provider name"
                        },
                        "api_key": {
                            "type": "string",
                            "description": "Optional API key to fetch models from API"
                        }
                    },
                    "required": ["provider"]
                }
            },
            # Workflow functions
            {
                "name": "get_workflow_status",
                "description": "Get current workflow phase and status",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "advance_workflow_phase",
                "description": "Mark current phase complete and advance to next phase. Will validate required data is collected first.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "set_workflow_data",
                "description": "Store data collected during a workflow phase",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Data key (e.g., 'core_idea', 'tech_stack', 'database_schema')"
                        },
                        "value": {
                            "type": "object",
                            "description": "Data value to store"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "generate_project_files",
                "description": "Generate all project documentation files (plan.md, task.md, cursor.md, etc.)",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "setup_database",
                "description": "Set up database 100% - generate schema files, create migrations, create connection config, test connection. Supports ANY database: PostgreSQL, MySQL, SQLite, MongoDB, Firebase, etc.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "create_backend_files",
                "description": "Create complete backend structure with all files (100%) - folders, routes, controllers, middleware, .env, backend.md. Supports Node.js/Express, Python/FastAPI, etc.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "create_frontend_files",
                "description": "Create complete frontend structure with all files (100%) - folders, pages, components, services, .env, frontend.md. Supports React, Vue, Next.js, etc.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "setup_project_structure",
                "description": "Create complete project folder structure and base files with starter code",
                "parameters": {"type": "object", "properties": {}}
            },
            # Profile and project data functions
            # NOTE: save_user_profile is REMOVED - profile comes from database during signup, not from agent
            {
                "name": "update_profile_field",
                "description": "Update a single field in user profile. Use when user provides additional info.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "Field name to update"
                        },
                        "value": {
                            "type": "string",
                            "description": "New value for the field"
                        }
                    },
                    "required": ["field", "value"]
                }
            },
            {
                "name": "save_project_info",
                "description": "Save project idea and details. Call this after collecting project info in Phase 2.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "core_idea": {
                            "type": "string",
                            "description": "Main project idea/description"
                        },
                        "target_users": {
                            "type": "string",
                            "description": "Who will use this app"
                        },
                        "main_features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of main features"
                        },
                        "scale": {
                            "type": "string",
                            "description": "Project scale: 'simple', 'medium', or 'large'"
                        },
                        "special_requirements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Special requirements like 'offline', 'realtime', 'payments'"
                        }
                    },
                    "required": ["core_idea", "main_features"]
                }
            },
            {
                "name": "save_tech_stack",
                "description": "Save selected tech stack. Call this after tech stack decisions in Phase 3.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "frontend": {"type": "object", "description": "Frontend tech: {name, reason}"},
                        "backend": {"type": "object", "description": "Backend tech: {name, reason}"},
                        "database": {"type": "object", "description": "Database tech: {name, reason}"},
                        "authentication": {"type": "object", "description": "Auth method: {name, reason}"},
                        "storage": {"type": "object", "description": "File storage: {name, reason}"},
                        "deployment": {"type": "object", "description": "Deployment platform: {name, reason}"},
                        "other_tools": {"type": "array", "description": "Other tools needed"}
                    },
                    "required": ["frontend", "backend", "database"]
                }
            },
            {
                "name": "check_phase_requirements",
                "description": "Check if current phase has all required data before advancing",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_conversation_summary",
                "description": "Generate a markdown file with all questions asked and answers given during the conversation",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "activate_live_mode",
                "description": "Activate Phase 10 Live Development Mode - real-time file watching, browser error tracking, and proactive code improvements",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "deactivate_live_mode",
                "description": "Deactivate Phase 10 Live Development Mode",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_live_mode_status",
                "description": "Get current status of Phase 10 Live Development Mode - shows what's being monitored and recent activity",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    
    def _execute_function(self, tool_call):
        """Execute a function called by the agent with visual feedback."""
        function_name = tool_call["name"]

        # Parse arguments with error handling
        try:
            arguments = json.loads(tool_call["arguments"])
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            import re
            fixed_json = tool_call["arguments"]

            # Fix unquoted values like: "value": ai_tools -> "value": "ai_tools"
            # Match patterns like: "key": unquoted_value
            fixed_json = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', fixed_json)

            try:
                arguments = json.loads(fixed_json)
                console.print(f"[yellow]⚠ Auto-fixed invalid JSON[/yellow]")
            except:
                console.print(f"[red]Error: Invalid JSON in function call[/red]")
                console.print(f"[dim]Function: {function_name}[/dim]")
                console.print(f"[dim]Arguments: {tool_call['arguments'][:100]}...[/dim]")
                console.print(f"[dim]Error: {str(e)}[/dim]")
                # Use empty arguments and continue
                arguments = {}

        # Visual indicators
        ACTION = "[#A855F7]⏺[/#A855F7]"
        RESULT = "[#64748B]  ⎿[/#64748B]"

        # Map function names to implementations with visual feedback
        if function_name == "search_online":
            query = arguments.get("query", "")
            
            # Step 1: Show "Researching" status
            with Live(Spinner("dots", text=f" [#F1F5F9]Researching:[/#F1F5F9] {query}", style="#A855F7"), refresh_per_second=10, transient=True) as live:
                result = self.search.search(query)
                
                # Step 2: Show what was found temporarily
                results = result.get("results", [])
                if results:
                    table = Table.grid(padding=(0, 1))
                    table.add_column(style="#64748B")
                    table.add_column(style="#F1F5F9")
                    
                    for i, r in enumerate(results[:3], 1):
                        title = r.get('title', 'No Title')
                        url = r.get('url', '')
                        # Shorten URL for display
                        display_url = (url[:50] + '...') if len(url) > 50 else url
                        table.add_row(f"  {i}.", f"{title} [dim]({display_url})[/dim]")
                    
                    # Update live display with results
                    live.update(Group(
                        Text.from_markup(f"{ACTION} [#F1F5F9]Found results for:[/#F1F5F9] {query}"),
                        table
                    ))
                    # Pause for 1.5 seconds so user can see what was found
                    import time
                    time.sleep(1.5)
            
            # Step 3: "Collapse" into a final status line (transient=True above clears the detailed list)
            status_msg = f"{ACTION} [#10B981]Research complete[/#10B981] [dim](Found {len(results)} results for \"{query}\")[/dim]"
            console.print(status_msg)
            
            return result

        elif function_name == "execute_command":
            cmd = arguments.get("command", "")
            console.print(f"{ACTION} [#F1F5F9]Queuing command:[/#F1F5F9] {cmd}")
            result = executor.execute_command(cmd, storage=self.storage)
            if result.get("queued"):
                console.print(f"{RESULT} [#F59E0B]Pending approval[/#F59E0B]")
            else:
                console.print(f"{RESULT} [#10B981]Executed[/#10B981]")
            return result

        elif function_name == "read_file":
            path = arguments.get("path", "")
            console.print(f"{ACTION} [#F1F5F9]Reading:[/#F1F5F9] {path}")
            result = self._read_file(path)
            if result.get("content"):
                lines = len(result["content"].split("\n"))
                console.print(f"{RESULT} [#10B981]Read {lines} lines[/#10B981]")
            else:
                console.print(f"{RESULT} [#EF4444]Error: {result.get('error', 'Unknown')}[/#EF4444]")
            return result

        elif function_name == "write_file":
            path = arguments.get("path", "")
            content = arguments.get("content", "")

            # Skip if path is empty (happens when JSON is truncated)
            if not path or not path.strip():
                console.print(f"{ACTION} [#F1F5F9]Writing:[/#F1F5F9] [empty path skipped]")
                return {"error": "Empty path - JSON may have been truncated"}

            console.print(f"{ACTION} [#F1F5F9]Writing:[/#F1F5F9] {path}")
            result = self._write_file(path, content)
            if result.get("success"):
                lines = len(content.split("\n"))
                console.print(f"{RESULT} [#10B981]Wrote {lines} lines[/#10B981]")
            else:
                console.print(f"{RESULT} [#EF4444]Error: {result.get('error', 'Unknown')}[/#EF4444]")
            return result

        elif function_name == "save_to_storage":
            key = arguments.get("key", "")
            data = arguments.get("data", {})

            # Strip "_preview" suffix - treat previews as actual data
            original_key = key
            if key.endswith("_preview"):
                key = key.replace("_preview", "")
                console.print(f"{ACTION} [#F1F5F9]Saving:[/#F1F5F9] {key} (from {original_key})")
            else:
                console.print(f"{ACTION} [#F1F5F9]Saving:[/#F1F5F9] {key}")

            result = self.storage.save(key, data)
            console.print(f"{RESULT} [#10B981]Saved[/#10B981]")

            # Update workflow phase data for key mappings
            key_to_phase_data = {
                "project_info": "core_idea",
                "external_tools": None,  # No direct mapping
                "tech_stack": "tech_stack_locked",
                "database_schema": "database_schema",
                "backend_design": "backend_architecture",
                "frontend_design": "frontend_design"
            }

            if key in key_to_phase_data:
                phase_key = key_to_phase_data[key]
                if phase_key == "core_idea" and isinstance(data, dict):
                    self.workflow.phase_data.core_idea = data.get("idea") or data.get("core_idea", "")
                    self.workflow.phase_data.main_features = data.get("features") or data.get("main_features", [])
                elif phase_key == "tech_stack_locked":
                    self.workflow.phase_data.tech_stack_locked = True
                elif phase_key and isinstance(data, dict):
                    setattr(self.workflow.phase_data, phase_key, data)
                self.workflow.save_state()

                # Check for batch mode - auto-advance if we have complete data
                self._check_batch_mode_advance()

            # Auto-trigger database setup when schema is saved
            if key == "database_schema":
                db_result = self.db_setup.setup_database()
                if db_result.get("success"):
                    tables = db_result.get("tables_created", [])
                    console.print(f"{RESULT} [#10B981]SQL schema generated! {len(tables)} tables[/#10B981]")

            return result

        elif function_name == "load_from_storage":
            key = arguments.get("key", "")
            console.print(f"{ACTION} [#F1F5F9]Loading:[/#F1F5F9] {key}")
            data = self.storage.load(key)
            if data is not None:
                console.print(f"{RESULT} [#10B981]Loaded[/#10B981]")
                return {"data": data}
            else:
                console.print(f"{RESULT} [#F59E0B]Not found[/#F59E0B]")
                return {"error": "Key not found"}

        elif function_name == "scan_project":
            console.print(f"{ACTION} [#F1F5F9]Scanning project...[/#F1F5F9]")
            result = scanner.scan_project(self.project_dir)
            files = result.get("total_files", 0)
            console.print(f"{RESULT} [#10B981]Found {files} files[/#10B981]")
            return result

        elif function_name == "create_project_structure":
            console.print(f"{ACTION} [#F1F5F9]Creating project structure...[/#F1F5F9]")
            result = structure.create(arguments.get("structure", {}), self.project_dir)
            console.print(f"{RESULT} [#10B981]Structure created[/#10B981]")
            return result

        elif function_name == "generate_roadmap":
            console.print(f"{ACTION} [#F1F5F9]Generating roadmap...[/#F1F5F9]")
            result = self.roadmap_gen.generate(
                arguments.get("project_info", {}),
                arguments.get("user_profile", {})
            )
            console.print(f"{RESULT} [#10B981]Roadmap generated[/#10B981]")

            # Update workflow flag
            self.workflow.phase_data.roadmap_generated = True
            self.workflow.save_state()

            return result

        elif function_name == "track_progress":
            console.print(f"{ACTION} [#F1F5F9]Tracking progress...[/#F1F5F9]")
            result = self.tracker.get_current_status()
            console.print(f"{RESULT} [#10B981]Status retrieved[/#10B981]")
            return result

        elif function_name == "verify_phase":
            phase = arguments.get("phase_number")
            console.print(f"{ACTION} [#F1F5F9]Verifying phase {phase}...[/#F1F5F9]")
            result = self.verifier.verify_phase(phase, self.project_dir)
            console.print(f"{RESULT} [#10B981]Verification complete[/#10B981]")
            return result

        elif function_name == "detect_and_fix_error":
            console.print(f"{ACTION} [#F1F5F9]Analyzing error...[/#F1F5F9]")
            result = self._handle_error(arguments.get("terminal_output", ""))
            console.print(f"{RESULT} [#10B981]Analysis complete[/#10B981]")
            return result

        elif function_name == "git_commit":
            msg = arguments.get("message", "")[:50]
            console.print(f"{ACTION} [#F1F5F9]Git commit:[/#F1F5F9] {msg}...")
            result = self.git.auto_commit(
                arguments.get("message"),
                arguments.get("phase_number")
            )
            console.print(f"{RESULT} [#10B981]Committed[/#10B981]")
            return result

        elif function_name == "generate_reports":
            console.print(f"{ACTION} [#F1F5F9]Generating reports...[/#F1F5F9]")
            result = self.reporter.generate_all_reports()
            console.print(f"{RESULT} [#10B981]Reports generated[/#10B981]")
            return result

        elif function_name == "discover_llm_models":
            console.print(f"{ACTION} [#F1F5F9]Discovering LLM models...[/#F1F5F9]")
            result = self.llm_manager.discover_models()
            console.print(f"{RESULT} [#10B981]Models discovered[/#10B981]")
            return result

        elif function_name == "configure_llm":
            provider = arguments.get("provider", "")
            model = arguments.get("model", "")
            console.print(f"{ACTION} [#F1F5F9]Configuring LLM:[/#F1F5F9] {provider}/{model}")
            result = self._configure_llm_helper(arguments)
            if result.get("success"):
                console.print(f"{RESULT} [#10B981]Configured[/#10B981]")
            else:
                console.print(f"{RESULT} [#EF4444]Failed[/#EF4444]")
            return result

        elif function_name == "update_llm_settings":
            console.print(f"{ACTION} [#F1F5F9]Updating LLM settings...[/#F1F5F9]")
            self.llm_manager.update_settings(**arguments)
            console.print(f"{RESULT} [#10B981]Updated[/#10B981]")
            return {
                "success": True,
                "message": "LLM settings updated",
                "settings": self.llm_manager.get_current_config()["settings"]
            }

        elif function_name == "get_llm_providers":
            console.print(f"{ACTION} [#F1F5F9]Getting providers...[/#F1F5F9]")
            result = {
                "providers": self.llm_manager.get_provider_list(),
                "current": self.llm_manager.get_current_config()
            }
            console.print(f"{RESULT} [#10B981]Retrieved[/#10B981]")
            return result

        elif function_name == "get_llm_models":
            provider = arguments.get("provider")
            console.print(f"{ACTION} [#F1F5F9]Getting models for:[/#F1F5F9] {provider}")
            api_key = arguments.get("api_key")
            models = self.llm_manager.get_models_for_provider(provider, api_key)
            console.print(f"{RESULT} [#10B981]Found {len(models)} models[/#10B981]")
            return {
                "provider": provider,
                "models": models
            }

        # Workflow functions
        elif function_name == "get_workflow_status":
            console.print(f"{ACTION} [#F1F5F9]Getting workflow status...[/#F1F5F9]")
            phase_info = self.workflow.get_current_phase_info()
            phase_data = self.workflow.phase_data if hasattr(self.workflow, 'phase_data') else {}
            console.print(f"{RESULT} [#10B981]Phase {phase_info['phase_number']}: {phase_info['phase_name']}[/#10B981]")
            return {
                "phase": phase_info,
                "data": phase_data
            }

        elif function_name == "advance_workflow_phase":
            console.print(f"{ACTION} [#F1F5F9]Advancing workflow phase...[/#F1F5F9]")
            result = self.advance_phase()
            if result.get("action") == "phase_complete":
                console.print(f"{RESULT} [#10B981]Advanced to Phase {result['next_phase']}: {result['next_phase_name']}[/#10B981]")
            elif result.get("action") == "workflow_complete":
                console.print(f"{RESULT} [#10B981]Workflow complete![/#10B981]")
            return result

        elif function_name == "set_workflow_data":
            key = arguments.get("key", "")
            value = arguments.get("value", {})
            console.print(f"{ACTION} [#F1F5F9]Saving workflow data:[/#F1F5F9] {key}")
            self.workflow.set_phase_data(key, value)
            # Also save to storage for persistence
            self.storage.save(key, value)
            console.print(f"{RESULT} [#10B981]Saved[/#10B981]")
            return {"success": True, "key": key}

        elif function_name == "generate_project_files":
            console.print(f"{ACTION} [#F1F5F9]Generating project files...[/#F1F5F9]")
            results = self.generate_project_files()
            success_count = sum(1 for v in results.values() if v)
            console.print(f"{RESULT} [#10B981]Generated {success_count} documentation files[/#10B981]")

            # Also create backend and frontend code files
            console.print(f"{ACTION} [#F1F5F9]Creating backend code...[/#F1F5F9]")
            backend_results = self.file_generator.create_backend_files()
            backend_count = sum(1 for v in backend_results.values() if v)
            results.update(backend_results)
            console.print(f"{RESULT} [#10B981]Created {backend_count} backend files[/#10B981]")

            console.print(f"{ACTION} [#F1F5F9]Creating frontend code...[/#F1F5F9]")
            frontend_results = self.file_generator.create_frontend_files()
            frontend_count = sum(1 for v in frontend_results.values() if v)
            results.update(frontend_results)
            console.print(f"{RESULT} [#10B981]Created {frontend_count} frontend files[/#10B981]")

            # Update workflow phase completion flags
            if success_count > 0:
                self.workflow.phase_data.documentation_generated = True
            if backend_count > 0:
                self.workflow.phase_data.backend_files_created = True
            if frontend_count > 0:
                self.workflow.phase_data.frontend_files_created = True
            self.workflow.save_state()

            total_count = sum(1 for v in results.values() if v)
            return {"success": True, "files": results, "total": total_count}

        elif function_name == "setup_database":
            console.print(f"{ACTION} [#F1F5F9]Setting up database (100%)...[/#F1F5F9]")
            result = self.db_setup.setup_database()
            if result.get("success"):
                db_type = result.get("db_type", "database")
                tables = result.get("tables_created", [])
                collections = result.get("collections_created", [])
                count = len(tables) if tables else len(collections)
                item_type = "tables" if tables else "collections"
                console.print(f"{RESULT} [#10B981]Database ready! {count} {item_type} created[/#10B981]")

                # Update workflow flag
                self.workflow.phase_data.database_setup_complete = True
                self.workflow.save_state()

                # Auto-setup database (for local DBs)
                schema_path = os.path.join(self.project_dir, "database", "schema.sql")
                if os.path.exists(schema_path):
                    console.print(f"\n[bold cyan]Auto-setting up database...[/bold cyan]")
                    auto_result = self.db_setup.auto_setup_database(db_type, schema_path)
                    if auto_result.get("success"):
                        console.print(f"{RESULT} [#10B981]Database auto-setup complete![/#10B981]")
            else:
                error = result.get("error", "Unknown error")
                console.print(f"{RESULT} [#EF4444]Database setup failed: {error}[/#EF4444]")
            return result

        elif function_name == "create_backend_files":
            console.print(f"{ACTION} [#F1F5F9]Creating backend (100%)...[/#F1F5F9]")
            results = self.file_generator.create_backend_files()
            success_count = sum(1 for v in results.values() if v)
            console.print(f"{RESULT} [#10B981]Backend ready! {success_count} files created[/#10B981]")
            
            # Auto-install backend dependencies
            if success_count > 0:
                project = self.storage.load("project") or {}
                tech_stack = project.get("tech_stack", {})
                backend_info = tech_stack.get("backend", {})
                backend_name = backend_info.get("name", "express").lower() if isinstance(backend_info, dict) else str(backend_info).lower()
                
                console.print(f"\n[bold cyan]Auto-installing backend dependencies...[/bold cyan]")
                install_result = self.auto_installer.auto_install_backend(backend_name)
                if install_result.get("success"):
                    console.print(f"{RESULT} [#10B981]Backend dependencies installed![/#10B981]")
            
            return {"success": True, "files_created": list(results.keys()), "count": success_count}

        elif function_name == "create_frontend_files":
            console.print(f"{ACTION} [#F1F5F9]Creating frontend (100%)...[/#F1F5F9]")
            results = self.file_generator.create_frontend_files()
            success_count = sum(1 for v in results.values() if v)
            console.print(f"{RESULT} [#10B981]Frontend ready! {success_count} files created[/#10B981]")
            
            # Auto-install frontend dependencies
            if success_count > 0:
                project = self.storage.load("project") or {}
                tech_stack = project.get("tech_stack", {})
                frontend_info = tech_stack.get("frontend", {})
                frontend_name = frontend_info.get("name", "react").lower() if isinstance(frontend_info, dict) else str(frontend_info).lower()
                
                console.print(f"\n[bold cyan]Auto-installing frontend dependencies...[/bold cyan]")
                install_result = self.auto_installer.auto_install_frontend(frontend_name)
                if install_result.get("success"):
                    console.print(f"{RESULT} [#10B981]Frontend dependencies installed![/#10B981]")
                    
                    # Offer to start servers
                    project = self.storage.load("project") or {}
                    tech_stack = project.get("tech_stack", {})
                    backend_info = tech_stack.get("backend", {})
                    backend_name = backend_info.get("name", "express").lower() if isinstance(backend_info, dict) else str(backend_info).lower()
                    
                    console.print(f"\n[bold cyan]Ready to start servers![/bold cyan]")
                    start_result = self.auto_installer.auto_start_servers(backend_name, frontend_name)
                    if start_result.get("started"):
                        console.print(f"{RESULT} [#10B981]Servers started![/#10B981]")
            
            return {"success": True, "files_created": list(results.keys()), "count": success_count}

        elif function_name == "setup_project_structure":
            console.print(f"{ACTION} [#F1F5F9]Setting up project structure...[/#F1F5F9]")
            results = self.create_project_structure()
            console.print(f"{RESULT} [#10B981]Project structure created[/#10B981]")

            # Update workflow phase completion flags
            self.workflow.phase_data.project_structure_created = True
            self.workflow.phase_data.base_files_created = True
            self.workflow.save_state()

            return {"success": True, "files_created": results}

        # Profile and project data functions
        # NOTE: save_user_profile removed - profile comes from database, not agent

        elif function_name == "update_profile_field":
            field = arguments.get("field", "")
            value = arguments.get("value", "")
            console.print(f"{ACTION} [#F1F5F9]Updating profile:[/#F1F5F9] {field}")
            # Load existing profile
            profile = self.storage.load("profile") or {}
            profile[field] = value
            self.storage.save("profile", profile)
            self.workflow.set_phase_data(field, value)
            self.context["profile"] = profile
            console.print(f"{RESULT} [#10B981]Updated[/#10B981]")
            return {"success": True, "field": field, "value": value}

        elif function_name == "save_project_info":
            console.print(f"{ACTION} [#F1F5F9]Saving project info...[/#F1F5F9]")

            # Get input data
            project_name = arguments.get("name", "Project")
            core_idea = arguments.get("core_idea", "")
            target_users = arguments.get("target_users", "")
            main_features = arguments.get("main_features", [])
            scale = arguments.get("scale", "medium")
            special_requirements = arguments.get("special_requirements", [])

            # Save with BOTH key formats for compatibility
            project_data = {
                # New format (for file generators)
                "name": project_name,
                "idea": core_idea,
                "features": main_features,
                # Old format (for backwards compatibility)
                "core_idea": core_idea,
                "main_features": main_features,
                # Common fields
                "target_users": target_users,
                "scale": scale,
                "special_requirements": special_requirements
            }

            # Merge with existing project data
            existing = self.storage.load("project") or {}
            existing.update(project_data)
            # Save to BOTH keys for compatibility with file generators
            self.storage.save("project", existing)
            self.storage.save("project_info", existing)

            # Update workflow
            self.workflow.set_phase_data("core_idea", core_idea)
            self.workflow.set_phase_data("target_users", target_users)
            self.workflow.set_phase_data("main_features", main_features)
            self.context["project"] = existing
            console.print(f"{RESULT} [#10B981]Project info saved[/#10B981]")
            return {"success": True, "project": existing}

        elif function_name == "save_tech_stack":
            console.print(f"{ACTION} [#F1F5F9]Saving tech stack...[/#F1F5F9]")
            tech_stack = {
                "frontend": arguments.get("frontend", {}),
                "backend": arguments.get("backend", {}),
                "database": arguments.get("database", {}),
                "authentication": arguments.get("authentication", {}),
                "storage": arguments.get("storage", {}),
                "deployment": arguments.get("deployment", {}),
                "other_tools": arguments.get("other_tools", []),
                "locked": True  # Tech stack is now locked
            }
            # Merge with project
            project = self.storage.load("project") or {}
            project["tech_stack"] = tech_stack
            self.storage.save("project", project)
            # Also save tech_stack separately for other modules
            self.storage.save("tech_stack", tech_stack)
            # Update workflow
            self.workflow.set_phase_data("frontend", tech_stack["frontend"])
            self.workflow.set_phase_data("backend", tech_stack["backend"])
            self.workflow.set_phase_data("database", tech_stack["database"])
            self.workflow.set_phase_data("tech_stack_locked", True)
            self.context["project"] = project
            console.print(f"{RESULT} [#10B981]Tech stack saved and locked[/#10B981]")
            return {"success": True, "tech_stack": tech_stack}

        elif function_name == "check_phase_requirements":
            console.print(f"{ACTION} [#F1F5F9]Checking phase requirements...[/#F1F5F9]")
            result = self._check_phase_requirements()
            if result["can_advance"]:
                console.print(f"{RESULT} [#10B981]Ready to advance[/#10B981]")
            else:
                console.print(f"{RESULT} [#F59E0B]Missing: {', '.join(result['missing'])}[/#F59E0B]")
            return result

        elif function_name == "generate_conversation_summary":
            console.print(f"{ACTION} [#F1F5F9]Generating conversation summary...[/#F1F5F9]")
            result = self._generate_conversation_summary()
            if result.get("success"):
                console.print(f"{RESULT} [#10B981]Summary saved to: {result['file_path']}[/#10B981]")
            else:
                console.print(f"{RESULT} [#EF4444]Failed to generate summary[/#EF4444]")
            return result

        elif function_name == "activate_live_mode":
            console.print(f"{ACTION} [#F1F5F9]Activating Live Development Mode...[/#F1F5F9]")
            result = self.live_mode.activate()
            if result.get("success"):
                console.print(f"{RESULT} [#10B981]Live mode activated[/#10B981]")
            else:
                console.print(f"{RESULT} [#EF4444]Failed to activate: {result.get('error')}[/#EF4444]")
            return result

        elif function_name == "deactivate_live_mode":
            console.print(f"{ACTION} [#F1F5F9]Deactivating Live Development Mode...[/#F1F5F9]")
            result = self.live_mode.deactivate()
            console.print(f"{RESULT} [#10B981]Live mode deactivated[/#10B981]")
            return result

        elif function_name == "get_live_mode_status":
            result = self.live_mode.get_status()
            self.live_mode.show_status()
            return result

        else:
            console.print(f"{ACTION} [#F1F5F9]Unknown function:[/#F1F5F9] {function_name}")
            console.print(f"{RESULT} [#EF4444]Error[/#EF4444]")
            return {"error": f"Unknown function: {function_name}"}
    
    def _read_file(self, path):
        """Read file contents."""
        try:
            full_path = os.path.join(self.project_dir, path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return {"content": f.read(), "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def _write_file(self, path, content):
        """Write file contents."""
        try:
            full_path = os.path.join(self.project_dir, path)
            parent_dir = os.path.dirname(full_path)

            # Handle case where parent path exists as a file (not directory)
            if os.path.exists(parent_dir) and not os.path.isdir(parent_dir):
                # Remove the file and create directory instead
                os.remove(parent_dir)

            os.makedirs(parent_dir, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_error(self, terminal_output):
        """Detect and handle errors from terminal output."""
        profile = self.storage.load("profile") or {}
        
        error_info = self.error_handler.detect_error(terminal_output)
        
        if error_info:
            analysis = self.error_handler.analyze_and_fix(
                error_info,
                self.project_dir,
                profile
            )
            return analysis
        
        return {"no_error": True}
    
    def _configure_llm_helper(self, args):
        """Helper to configure LLM."""
        try:
            self.llm_manager.configure_llm(
                provider=args["provider"],
                model=args["model"],
                api_key=args["api_key"],
                temperature=args.get("temperature", 0.7),
                max_tokens=args.get("max_tokens", 4000)
            )
            
            return {
                "success": True,
                "message": f"Configured {args['provider']} - {args['model']}",
                "config": self.llm_manager.get_current_config()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _check_phase_requirements(self):
        """Check if current phase has all required data to advance."""
        phase = self.workflow.current_phase
        profile = self.storage.load("profile") or {}
        project = self.storage.load("project") or {}
        missing = []

        if phase.value == 1:  # IDEA_COLLECTION
            if not project.get("core_idea"):
                missing.append("core_idea")
            if not project.get("main_features") or len(project.get("main_features", [])) < 1:
                missing.append("main_features (need at least 1)")

        elif phase.value == 2:  # TECH_STACK
            tech = project.get("tech_stack", {})
            if not tech.get("frontend"):
                missing.append("frontend")
            if not tech.get("backend"):
                missing.append("backend")
            if not tech.get("database"):
                missing.append("database")

        elif phase.value == 3:  # DEEP_DISCUSSIONS
            # At least database schema should be discussed
            if not project.get("database_schema"):
                missing.append("database_schema")

        elif phase.value == 4:  # BUILD_STRATEGY
            if not profile.get("ai_tools") and not profile.get("build_strategy"):
                missing.append("build_strategy or ai_tools")

        # Phases 5, 6, 7 don't have strict requirements

        return {
            "can_advance": len(missing) == 0,
            "missing": missing,
            "current_phase": phase.value,
            "phase_name": self.workflow.get_phase_name()
        }

    def advance_phase(self):
        """Advance to next phase with validation."""
        # First check requirements
        check = self._check_phase_requirements()
        if not check["can_advance"]:
            return {
                "action": "blocked",
                "reason": f"Cannot advance - missing: {', '.join(check['missing'])}",
                "missing": check["missing"]
            }
        # If requirements met, advance
        self.workflow.phase_complete[self.workflow.current_phase] = True
        # Get next phase info (use .value for enum comparison)
        current_val = self.workflow.current_phase.value if hasattr(self.workflow.current_phase, 'value') else self.workflow.current_phase
        next_phase_val = current_val + 1 if current_val < 8 else current_val
        return {
            "action": "phase_complete" if next_phase_val <= 8 else "workflow_complete",
            "success": True,
            "current_phase": current_val,
            "next_phase": next_phase_val,
            "next_phase_name": self.workflow.get_phase_name() if hasattr(self.workflow, 'get_phase_name') else f"Phase {next_phase_val}"
        }

    def _generate_conversation_summary(self, history=None):
        """
        Generate a markdown file with all questions and answers from the conversation.
        
        Args:
            history: Optional conversation history from backend. If not provided, 
                    loads from local storage.
        """
        try:
            import datetime

            # Load conversation history - prefer provided history (from backend), 
            # otherwise fall back to local storage
            if history is None:
                history = self.storage.load("history") or []

            if not history or len(history) == 0:
                return {
                    "success": False,
                    "error": "No conversation history found"
                }

            # Generate markdown content
            markdown_content = "# Conversation Summary\n\n"
            markdown_content += f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            markdown_content += f"**Total Messages:** {len(history)}\n\n"
            markdown_content += "---\n\n"

            # Save ALL messages in chronological order
            message_count = 0
            qa_pairs = []
            last_assistant = None
            
            for msg in history:
                role = msg.get("role")
                # Backend uses "message" field, local storage uses "content" - support both
                content = msg.get("message") or msg.get("content", "")
                
                if not content.strip():  # Skip empty messages
                    continue
                
                message_count += 1
                
                # Save every message
                role_label = "🤖 **BOTUVIC**" if role == "assistant" else "👤 **You**"
                markdown_content += f"## Message {message_count} - {role_label}\n\n"
                markdown_content += f"{content}\n\n"
                markdown_content += "---\n\n"
                
                # Also track Q&A pairs for counting
                if role == "assistant":
                    last_assistant = content
                elif role == "user" and last_assistant:
                    qa_pairs.append({
                        "question": last_assistant,
                        "answer": content
                    })
                    last_assistant = None

            # Add project summary if available
            project = self.storage.load("project")
            if project:
                markdown_content += "\n## Project Summary\n\n"
                if project.get("core_idea"):
                    markdown_content += f"**Project Idea:** {project['core_idea']}\n\n"
                if project.get("main_features"):
                    markdown_content += "**Main Features:**\n"
                    for feature in project['main_features']:
                        markdown_content += f"- {feature}\n"
                    markdown_content += "\n"
                if project.get("tech_stack"):
                    markdown_content += "**Tech Stack:**\n"
                    tech = project['tech_stack']
                    if tech.get("frontend"):
                        markdown_content += f"- Frontend: {tech['frontend'].get('name', 'N/A')}\n"
                    if tech.get("backend"):
                        markdown_content += f"- Backend: {tech['backend'].get('name', 'N/A')}\n"
                    if tech.get("database"):
                        markdown_content += f"- Database: {tech['database'].get('name', 'N/A')}\n"
                    markdown_content += "\n"

            # Save to file
            file_path = os.path.join(self.project_dir, "conversation-summary.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            return {
                "success": True,
                "file_path": file_path,
                "total_messages": message_count,
                "total_qa_pairs": len(qa_pairs)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _analyze_user_tone(self, user_message):
        """
        Analyze user's writing tone from their message.
        Detects style (casual/formal), length preference, and mood.
        """
        message_lower = user_message.lower().strip()
        word_count = len(user_message.split())

        # Detect casualness
        casual_indicators = [
            'yo', 'hey', 'whats up', 'sup', 'yeah', 'nah', 'gonna',
            'wanna', 'kinda', 'like', 'lol', 'ok', 'u', 'ur', 'plz',
            'thnaks', 'thanks', 'thx', 'btw', 'idk', 'dont', 'cant',
            'im', 'ill', 'thats', 'hows', 'whats'
        ]

        formal_indicators = [
            'please', 'thank you', 'kindly', 'would you', 'could you',
            'i would like', 'appreciate', 'regards', 'sincerely'
        ]

        casual_score = sum(1 for indicator in casual_indicators if indicator in message_lower)
        formal_score = sum(1 for indicator in formal_indicators if indicator in message_lower)

        # Determine style
        if casual_score > formal_score:
            style = "casual"
        elif formal_score > casual_score:
            style = "formal"
        else:
            # Default based on punctuation and capitalization
            if message_lower == user_message or '!' in user_message:
                style = "casual"
            else:
                style = "neutral"

        # Detect length preference
        if word_count <= 5:
            length = "very_short"
        elif word_count <= 15:
            length = "short"
        elif word_count <= 30:
            length = "medium"
        else:
            length = "long"

        # Detect mood/friendliness
        friendly_indicators = ['!', 'thanks', 'please', 'appreciate', 'great', 'awesome', 'cool', 'nice']
        friendly_score = sum(1 for indicator in friendly_indicators if indicator in message_lower)

        if friendly_score >= 2 or '!' in user_message:
            mood = "friendly"
        elif casual_score > 0:
            mood = "relaxed"
        else:
            mood = "professional"

        tone_profile = {
            "style": style,
            "length": length,
            "mood": mood,
            "last_updated": user_message[:50]  # Store snippet of last message
        }

        return tone_profile

    def _update_user_tone(self, user_message):
        """
        Update user tone profile based on their latest message.
        Analyzes recent messages to get consistent tone.
        """
        # Load existing tone profile
        tone_history = self.storage.load("user_tone") or {"samples": [], "current": None}

        # Analyze current message
        current_tone = self._analyze_user_tone(user_message)

        # Add to samples (keep last 5 messages)
        tone_history["samples"].append(current_tone)
        if len(tone_history["samples"]) > 5:
            tone_history["samples"] = tone_history["samples"][-5:]

        # Calculate consensus tone from samples
        if len(tone_history["samples"]) >= 2:
            # Count most common values
            styles = [s["style"] for s in tone_history["samples"]]
            lengths = [s["length"] for s in tone_history["samples"]]
            moods = [s["mood"] for s in tone_history["samples"]]

            # Get most common
            from collections import Counter
            most_common_style = Counter(styles).most_common(1)[0][0]
            most_common_length = Counter(lengths).most_common(1)[0][0]
            most_common_mood = Counter(moods).most_common(1)[0][0]

            tone_history["current"] = {
                "style": most_common_style,
                "length": most_common_length,
                "mood": most_common_mood
            }
        else:
            tone_history["current"] = current_tone

        # Save updated tone profile
        self.storage.save("user_tone", tone_history)

        return tone_history["current"]

