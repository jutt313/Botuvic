"""
BOTUVIC CLI - Main entry point with complete UI flow.
"""

import os
import sys
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from .agent.agents.main_agent import MainAgent
from .agent.utils.storage import Storage
from .agent.utils.search import SearchEngine
from .agent.llm.manager import LLMManager
from .agent.workflow_controller import WorkflowController
from .ui.header import display_header
from .ui.auth import authenticate_user
from .ui.project_selector import select_project
from .ui.menu import show_command_menu
from .ui.llm_config_ui import configure_llm_ui
from .ui.permissions import PermissionManager
from .ui.code_viewer import CodeChangeViewer
from .ui.terminal_viewer import TerminalViewer

console = Console()

class BotuvicCLI:
    """Main CLI application."""
    
    def __init__(self):
        self.console = console
        self.agent = None
        self.user = None
        self.current_project = None
        self.permission_manager = None
        self.code_viewer = CodeChangeViewer()
        self.terminal_viewer = TerminalViewer()
        self.conversation_history = []
        
    def run(self):
        """Main application loop."""
        # Step 1: Show header (initial - no project info yet)
        display_header()
        
        # Step 2: Authentication
        self.user = authenticate_user()
        if not self.user:
            console.print("[red]Authentication failed. Exiting.[/red]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Welcome back, [#A855F7]{self.user['name']}[/#A855F7]!\n")
        
        # Step 3: Project selection
        self.current_project = select_project(self.user)
        
        if not self.current_project:
            console.print("[yellow]No project selected. Exiting.[/yellow]")
            sys.exit(0)
        
        # Step 4: Initialize agent
        project_dir = self.current_project['path']

        # Change to project directory if not already there
        if os.getcwd() != project_dir:
            os.chdir(project_dir)
            console.print(f"[dim]Working directory: {project_dir}[/dim]")

        # Update project status to in_progress if it's new
        if self.current_project.get('status') == 'new':
            self.update_project_status('in_progress')
        
        # Initialize components for MainAgent
        storage = Storage(project_dir)
        search_engine = SearchEngine()
        llm_manager = LLMManager(search_engine, storage)
        workflow = WorkflowController(storage)
        
        # Load .env files (same logic as BotuvicAgent)
        from pathlib import Path
        from dotenv import load_dotenv
        
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
        
        # Auto-configure LLM if OpenAI key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and not llm_manager.is_configured():
            try:
                llm_manager.configure_llm(
                    provider="OpenAI",
                    model="gpt-4o",
                    api_key=openai_key
                )
            except:
                pass
        
        # Create LLMWrapper for backward compatibility
        class LLMWrapper:
            def __init__(self, manager):
                self.manager = manager

            def chat(self, messages, functions=None, tools=None, tool_choice=None, **kwargs):
                if not self.manager.is_configured():
                    raise ValueError(
                        "LLM not configured. Please configure an LLM provider first.\n"
                        "Use: discover_llm_models and configure_llm functions"
                    )
                # Support both 'functions' and 'tools' arguments
                funcs = functions or tools
                return self.manager.chat(messages, functions=funcs, **kwargs)
        
        llm_client = LLMWrapper(llm_manager)
        
        # Initialize MainAgent (orchestrator for all 6 sub-agents)
        self.agent = MainAgent(
            llm_client=llm_client,
            storage=storage,
            project_dir=project_dir,
            search_engine=search_engine,
            workflow=workflow
        )
        
        # Store llm_manager for LLM config check
        self.llm_manager = llm_manager
        
        # Step 5: Setup permissions
        self.permission_manager = PermissionManager(project_dir)
        self.permission_manager.load_permissions()
        
        # Step 6: Check LLM configuration
        if not self.llm_manager.is_configured():
            console.print("\n[yellow]⚙️  LLM not configured yet.[/yellow]")
            if Confirm.ask("Configure LLM now?", default=True):
                configure_llm_ui(self.llm_manager)
        
        # Step 7: Load conversation history
        self.conversation_history = self.load_conversation_history()

        # Clear screen and show header with project info
        os.system('clear' if os.name == 'posix' else 'cls')
        display_header(
            project_name=self.current_project.get('name'),
            project_path=self.current_project.get('path')
        )

        # Show workflow welcome message and phase indicator
        self.show_workflow_status()

        if self.conversation_history and len(self.conversation_history) > 0:
            console.print(f"[dim]Loaded {len(self.conversation_history)} previous messages[/dim]")

            # Show last few messages as preview
            preview_count = min(3, len(self.conversation_history))
            if preview_count > 0:
                console.print("[dim]Last conversation:[/dim]")
                for msg in self.conversation_history[-preview_count:]:
                    role = msg.get('role')
                    message = msg.get('message', '')[:80]
                    if role == 'user':
                        console.print(f"  [#FFFFFF]You:[/#FFFFFF] {message}")
                    else:
                        console.print(f"  [#A855F7]BOTUVIC:[/#A855F7] {message}")
                console.print()

        # Step 8: Main chat loop
        self.chat_loop()
    
    def chat_loop(self):
        """Main interactive chat loop."""
        # Get terminal width for full-width lines
        terminal_width = console.width
        separator = "─" * terminal_width
        
        while True:
            try:
                # Input prompt - Purple monochrome
                user_input = console.input("\n[#A855F7]>[/#A855F7] ")
                
                # Handle special commands
                if user_input.startswith('/'):
                    command = user_input[1:].strip()
                    if not command:
                        # User just typed "/" - show menu
                        console.print()
                        command = show_command_menu()
                    if command:
                        self.handle_command(command)
                    else:
                        console.print("[yellow]No command selected[/yellow]")
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                    console.print("\n[#A855F7]Goodbye! 👋[/#A855F7]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Save user message
                self.save_message('user', user_input)

                # Send to agent with full conversation history
                console.print()
                
                # Show animated thinking indicator that disappears when response arrives
                spinner = Spinner("dots", text="[#64748B]∴ Thinking...[/#64748B]")
                with Live(spinner, console=console, refresh_per_second=10, transient=True):
                    # MainAgent handles all routing and orchestration
                    response_dict = self.agent.chat(user_input)
                    response = response_dict.get('message', str(response_dict))

                # Save assistant response
                self.save_message('assistant', response)
                
                # Display response
                console.print(f"[bold #A855F7]BOTUVIC:[/bold #A855F7] {response}")
                console.print()
                
                # Check if awaiting confirmation - show interactive selector
                status = response_dict.get('status', '')
                if status == "awaiting_confirmation":
                    from .ui.confirmation import ask_confirmation
                    
                    # Show interactive 3-option selector
                    confirmation = ask_confirmation()
                    
                    if confirmation["choice"] == "yes":
                        # User confirmed - send "yes" to agent
                        user_input = "yes"
                    elif confirmation["choice"] == "no":
                        # User rejected - send "no" to agent
                        user_input = "no"
                    elif confirmation["choice"] == "yes_but":
                        # User wants changes - combine "yes" with their message
                        if confirmation["message"]:
                            user_input = f"yes but {confirmation['message']}"
                        else:
                            user_input = "yes but"
                    else:
                        user_input = "no"
                    
                    # Save user's confirmation choice
                    self.save_message('user', user_input)
                    
                    # Send confirmation back to agent
                    console.print()
                    spinner = Spinner("dots", text="[#64748B]∴ Thinking...[/#64748B]")
                    with Live(spinner, console=console, refresh_per_second=10, transient=True):
                        response_dict = self.agent.chat(user_input)
                        response = response_dict.get('message', str(response_dict))
                    
                    # Save assistant response
                    self.save_message('assistant', response)
                    
                    # Display response
                    console.print(f"[bold #A855F7]BOTUVIC:[/bold #A855F7] {response}")
                    console.print()
                    continue
                
                # Check for pending actions (file changes, commands, etc.)
                self.check_pending_actions()
                
            except KeyboardInterrupt:
                if Confirm.ask("\n\nExit BOTUVIC?"):
                    break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def handle_command(self, command):
        """Handle menu command."""
        if command == 'config':
            configure_llm_ui(self.llm_manager)
        elif command == 'exit':
            sys.exit(0)
        elif command == 'summary':
            # Generate conversation summary
            console.print("\n[#A855F7]Generating conversation summary...[/#A855F7]")
            # Pass backend conversation history to ensure we use the most up-to-date data
            result = self.agent._generate_conversation_summary(history=self.conversation_history)
            if result.get("success"):
                console.print(f"[#10B981]✓ Summary saved to: {result['file_path']}[/#10B981]")
                console.print(f"[dim]Total messages saved: {result.get('total_messages', 0)} | Q&A pairs: {result.get('total_qa_pairs', 0)}[/dim]\n")
            else:
                console.print(f"[red]✗ Failed to generate summary: {result.get('error', 'Unknown error')}[/red]\n")
        else:
            console.print(f"[yellow]Command '{command}' is not yet implemented.[/yellow]")

    def show_workflow_status(self):
        """Show workflow welcome message and phase indicator."""
        if not self.agent:
            return

        # Check if new project and show appropriate welcome
        is_new = self.agent.is_new_project()
        welcome_msg = self.agent.get_welcome_message()

        if welcome_msg:
            console.print(f"\n{welcome_msg}\n")
    
    def check_pending_actions(self):
        """Check for pending actions that need user approval."""
        # Check for file changes
        pending_changes = self.agent.storage.load("pending_changes") or []
        
        if pending_changes:
            for change in pending_changes:
                approved = self.code_viewer.show_change(change, self.permission_manager)
                
                if approved:
                    self.apply_change(change)
            
            # Clear pending changes
            self.agent.storage.save("pending_changes", [])
        
        # Check for terminal commands
        pending_commands = self.agent.storage.load("pending_commands") or []
        
        if pending_commands:
            for cmd in pending_commands:
                approved = self.terminal_viewer.show_command(cmd, self.permission_manager)
                
                if approved:
                    self.execute_command(cmd)
            
            # Clear pending commands
            self.agent.storage.save("pending_commands", [])
    
    def apply_change(self, change):
        """Apply a file change."""
        file_path = change["file"]
        new_content = change["new_content"]
        change_type = change.get("type", "edit")
        
        try:
            full_path = os.path.join(self.current_project['path'], file_path)
            
            if change_type == "delete":
                os.remove(full_path)
                console.print(f"[green]✓[/green] Deleted {file_path}")
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                console.print(f"[green]✓[/green] {'Created' if change_type == 'create' else 'Updated'} {file_path}")
        except Exception as e:
            console.print(f"[red]Error applying change: {e}[/red]")
    
    def execute_command(self, cmd):
        """Execute a terminal command after approval."""
        command_str = cmd["command"]
        
        try:
            from .agent.functions.executor import _execute_directly
            console.print(f"\n[dim]Executing: {command_str}[/dim]")

            result = _execute_directly(command_str)

            if result.get("success"):
                console.print(f"[green]✓[/green] Command executed successfully\n")
                if result.get("stdout"):
                    console.print(f"[dim]{result['stdout']}[/dim]")
            else:
                console.print(f"[red]✗[/red] Command failed")
                if result.get("stderr"):
                    console.print(f"[red]{result['stderr']}[/red]")
                if result.get("error"):
                    console.print(f"[red]{result['error']}[/red]")
        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")

    def update_project_status(self, status):
        """Update project status in backend."""
        try:
            import requests

            project_id = self.current_project.get('id')
            if not project_id:
                return

            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            token = self.user.get('token')

            if not token:
                return

            headers = {"Authorization": f"Bearer {token}"}

            requests.patch(
                f"{backend_url}/api/projects/{project_id}/status",
                params={"status": status},
                headers=headers,
                timeout=5
            )

            # Update local project status
            self.current_project['status'] = status
        except:
            pass  # Silently fail

    def load_conversation_history(self):
        """Load conversation history from backend."""
        try:
            import requests

            project_id = self.current_project.get('id')
            if not project_id:
                return []

            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            token = self.user.get('token')

            if not token:
                return []

            headers = {"Authorization": f"Bearer {token}"}

            response = requests.get(
                f"{backend_url}/api/projects/{project_id}/messages",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

            return []
        except Exception as e:
            console.print(f"[dim]Could not load conversation history: {e}[/dim]")
            return []

    def save_message(self, role, message):
        """Save a message to conversation history."""
        try:
            import requests

            project_id = self.current_project.get('id')
            if not project_id:
                return

            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            token = self.user.get('token')

            if not token:
                return

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{backend_url}/api/projects/{project_id}/messages",
                headers=headers,
                json={
                    "role": role,
                    "message": message
                },
                timeout=10
            )

            if response.status_code == 200:
                # Add to local history
                msg_data = response.json()
                self.conversation_history.append({
                    "role": role,
                    "message": message,
                    "created_at": msg_data.get("created_at")
                })
        except Exception as e:
            console.print(f"[dim]Could not save message: {e}[/dim]")


def cli():
    """Main CLI entry point."""
    app = BotuvicCLI()
    app.run()


if __name__ == "__main__":
    cli()
