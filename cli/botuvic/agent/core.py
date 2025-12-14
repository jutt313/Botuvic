"""Main BOTUVIC agent class"""

import os
import json
from pathlib import Path

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
        
        # Load context if existing project
        self.context = self._load_context()
        
        # Conversation history
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
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
        """Build context message for LLM."""
        context_parts = []
        
        # Add mode
        context_parts.append(f"MODE: {self.mode.upper()} PROJECT")
        
        # Add user profile if exists
        if self.context.get("profile"):
            profile = self.context["profile"]
            context_parts.append(f"\nUSER PROFILE:")
            context_parts.append(f"- Experience: {profile.get('experience')}")
            context_parts.append(f"- Skills: {', '.join(profile.get('tech_knowledge', []))}")
            context_parts.append(f"- Help level: {profile.get('help_level')}")
            context_parts.append(f"- AI tools: {', '.join(profile.get('ai_tools', []))}")
        
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
        
        return "\n".join(context_parts)
    
    def chat(self, user_message):
        """
        Main chat interface with the agent.
        
        Args:
            user_message: User's input message
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Add current context
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
        
        # Handle tool calls if any
        if response.get("tool_calls"):
            # First, add the assistant message with tool_calls
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
            
            # Process all tool calls
            for tool_call in response["tool_calls"]:
                function_response = self._execute_function(tool_call)
                
                # Add function response to messages
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["name"],
                    "content": json.dumps(function_response)
                })
            
            # Get final response after function execution
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
            }
        ]
    
    def _execute_function(self, tool_call):
        """Execute a function called by the agent."""
        function_name = tool_call["name"]
        arguments = json.loads(tool_call["arguments"])
        
        # Map function names to implementations
        if function_name == "search_online":
            return self.search.search(arguments.get("query", ""))
        
        elif function_name == "execute_command":
            return executor.execute_command(arguments.get("command", ""))
        
        elif function_name == "read_file":
            return self._read_file(arguments.get("path", ""))
        
        elif function_name == "write_file":
            return self._write_file(arguments.get("path", ""), arguments.get("content", ""))
        
        elif function_name == "save_to_storage":
            return self.storage.save(arguments.get("key", ""), arguments.get("data", {}))
        
        elif function_name == "load_from_storage":
            data = self.storage.load(arguments.get("key", ""))
            return {"data": data} if data is not None else {"error": "Key not found"}
        
        elif function_name == "scan_project":
            return scanner.scan_project(self.project_dir)
        
        elif function_name == "create_project_structure":
            return structure.create(arguments.get("structure", {}), self.project_dir)
        
        elif function_name == "generate_roadmap":
            return self.roadmap_gen.generate(
                arguments.get("project_info", {}),
                arguments.get("user_profile", {})
            )
        
        elif function_name == "track_progress":
            return self.tracker.get_current_status()
        
        elif function_name == "verify_phase":
            return self.verifier.verify_phase(
                arguments.get("phase_number"),
                self.project_dir
            )
        
        elif function_name == "detect_and_fix_error":
            return self._handle_error(arguments.get("terminal_output", ""))
        
        elif function_name == "git_commit":
            return self.git.auto_commit(
                arguments.get("message"),
                arguments.get("phase_number")
            )
        
        elif function_name == "generate_reports":
            return self.reporter.generate_all_reports()
        
        elif function_name == "discover_llm_models":
            return self.llm_manager.discover_models()
        
        elif function_name == "configure_llm":
            return self._configure_llm_helper(arguments)
        
        elif function_name == "update_llm_settings":
            self.llm_manager.update_settings(**arguments)
            return {
                "success": True,
                "message": "LLM settings updated",
                "settings": self.llm_manager.get_current_config()["settings"]
            }
        
        elif function_name == "get_llm_providers":
            return {
                "providers": self.llm_manager.get_provider_list(),
                "current": self.llm_manager.get_current_config()
            }
        
        elif function_name == "get_llm_models":
            provider = arguments.get("provider")
            api_key = arguments.get("api_key")
            models = self.llm_manager.get_models_for_provider(provider, api_key)
            return {
                "provider": provider,
                "models": models
            }
        
        else:
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
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
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

