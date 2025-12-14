"""
BOTUVIC CLI - Main entry point with complete UI flow.
"""

import os
import sys
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .agent import BotuvicAgent
from .ui.header import display_header
from .ui.auth import authenticate_user
from .ui.project_selector import select_project
from .ui.menu import show_command_menu, get_command_help
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
        
    def run(self):
        """Main application loop."""
        # Step 1: Show header
        display_header()
        
        # Step 2: Authentication
        self.user = authenticate_user()
        if not self.user:
            console.print("[red]Authentication failed. Exiting.[/red]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Welcome back, [cyan]{self.user['name']}[/cyan]!\n")
        
        # Step 3: Project selection
        self.current_project = select_project(self.user)
        
        if not self.current_project:
            console.print("[yellow]No project selected. Exiting.[/yellow]")
            sys.exit(0)
        
        # Step 4: Initialize agent
        project_dir = self.current_project['path']
        os.chdir(project_dir)  # Change to project directory
        
        self.agent = BotuvicAgent(project_dir)
        
        # Step 5: Setup permissions
        self.permission_manager = PermissionManager(project_dir)
        self.permission_manager.load_permissions()
        
        # Step 6: Check LLM configuration
        if not self.agent.llm_manager.is_configured():
            console.print("\n[yellow]⚙️  LLM not configured yet.[/yellow]")
            if Confirm.ask("Configure LLM now?", default=True):
                configure_llm_ui(self.agent.llm_manager)
        
        # Step 7: Main chat loop
        self.chat_loop()
    
    def chat_loop(self):
        """Main interactive chat loop."""
        console.print("\n[dim]═[/dim]" * 60)
        console.print(f"[bold cyan]Project:[/bold cyan] {self.current_project['name']}")
        console.print(f"[bold cyan]Directory:[/bold cyan] {self.current_project['path']}")
        console.print("[dim]═[/dim]" * 60)
        console.print()
        
        while True:
            try:
                # Get user input
                user_input = console.input("[#10B981]You:[/#10B981] ")
                
                # Handle special commands
                if user_input.startswith('/'):
                    command = user_input[1:].strip()
                    if not command:
                        command = show_command_menu()
                    if command:
                        self.handle_command(command)
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Send to agent
                console.print()
                with console.status("[cyan]BOTUVIC is thinking...[/cyan]"):
                    response = self.agent.chat(user_input)
                
                # Display response
                console.print(f"[bold #A855F7]BOTUVIC:[/bold #A855F7] {response}")
                console.print()
                
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
        handlers = {
            'init': self.handle_init,
            'scan': self.handle_scan,
            'status': self.handle_status,
            'chat': lambda: None,  # Already in chat mode
            'config': self.handle_config,
            'models': self.handle_models,
            'report': self.handle_report,
            'fix': self.handle_fix,
            'verify': self.handle_verify,
            'git': self.handle_git,
            'permissions': self.handle_permissions,
            'help': self.handle_help,
            'exit': lambda: sys.exit(0),
        }
        
        handler = handlers.get(command.lower())
        if handler:
            handler()
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print(f"Type '/help' for available commands")
    
    def handle_init(self):
        """Handle init command."""
        console.print("\n[bold cyan]📋 Initialize Project[/bold cyan]\n")
        console.print("Project is already initialized in this directory.")
    
    def handle_scan(self):
        """Handle scan command."""
        console.print("\n[bold cyan]🔍 Scanning Project...[/bold cyan]\n")
        with console.status("[cyan]Scanning...[/cyan]"):
            result = self.agent.storage.load("scan_result")
            if not result:
                # Trigger scan
                from .agent.functions import scanner
                result = scanner.scan_project(self.current_project['path'])
                self.agent.storage.save("scan_result", result)
        
        console.print(f"[green]✓[/green] Found {result.get('total_files', 0)} files")
        console.print(f"[green]✓[/green] {result.get('total_lines', 0)} lines of code")
    
    def handle_status(self):
        """Handle status command."""
        console.print("\n[bold cyan]📊 Project Status[/bold cyan]\n")
        progress = self.agent.storage.load("progress")
        if progress:
            console.print(f"Overall Progress: {progress.get('overall_progress', 0)}%")
            console.print(f"Completed Tasks: {progress.get('completed_tasks', 0)}/{progress.get('total_tasks', 0)}")
        else:
            console.print("[yellow]No progress data available[/yellow]")
    
    def handle_config(self):
        """Handle config command."""
        console.print("\n[bold cyan]⚙️  Configuration[/bold cyan]\n")
        configure_llm_ui(self.agent.llm_manager)
    
    def handle_models(self):
        """Handle models command."""
        console.print("\n[bold cyan]🤖 LLM Models[/bold cyan]\n")
        all_models = self.agent.llm_manager.discover_models()
        for provider, models in all_models.items():
            console.print(f"\n[bold]{provider}:[/bold]")
            for model in models[:5]:
                console.print(f"  - {model.get('name', model.get('id'))}")
    
    def handle_report(self):
        """Handle report command."""
        console.print("\n[bold cyan]📝 Generating Reports...[/bold cyan]\n")
        with console.status("[cyan]Generating...[/cyan]"):
            result = self.agent.reporter.generate_all_reports()
        console.print(f"[green]✓[/green] Generated {len(result.get('reports_generated', []))} reports")
    
    def handle_fix(self):
        """Handle fix command."""
        console.print("\n[bold cyan]🔧 Error Fixing[/bold cyan]\n")
        console.print("Use this command after encountering an error.")
        console.print("Or describe the error in chat and BOTUVIC will help fix it.")
    
    def handle_verify(self):
        """Handle verify command."""
        console.print("\n[bold cyan]✅ Phase Verification[/bold cyan]\n")
        roadmap = self.agent.storage.load("roadmap")
        if roadmap:
            current_phase = roadmap.get("current_phase", 1)
            console.print(f"Verifying Phase {current_phase}...")
            # Trigger verification
        else:
            console.print("[yellow]No roadmap found[/yellow]")
    
    def handle_git(self):
        """Handle git command."""
        console.print("\n[bold cyan]🔀 Git Operations[/bold cyan]\n")
        status = self.agent.git.get_status()
        if status.get("initialized"):
            console.print(f"Branch: {status.get('branch', 'N/A')}")
            console.print(f"Modified: {status.get('modified_files', 0)} files")
        else:
            console.print("[yellow]Git not initialized[/yellow]")
            if Confirm.ask("Initialize git?"):
                self.agent.git.initialize_repo()
    
    def handle_permissions(self):
        """Handle permissions command."""
        console.print("\n[bold cyan]🔒 Permissions[/bold cyan]\n")
        self.permission_manager.show_permissions()
        console.print()
        mode = Prompt.ask(
            "Set mode",
            choices=["ask", "auto", "read_only"],
            default=self.permission_manager.permissions["mode"]
        )
        self.permission_manager.set_mode(mode)
        console.print(f"[green]✓[/green] Mode set to {mode}")
    
    def handle_help(self):
        """Handle help command."""
        console.print("\n[bold cyan]❓ Help[/bold cyan]\n")
        from .ui.menu import COMMANDS
        for cmd, desc in COMMANDS:
            help_text = get_command_help(cmd[0])
            console.print(f"[cyan]{cmd[0]:<15}[/cyan] - {help_text}")
    
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
        """Execute a terminal command."""
        command_str = cmd["command"]
        
        try:
            from .agent.functions import executor
            result = executor.execute_command(command_str)
            console.print(f"[green]✓[/green] Command executed")
            if result.get("output"):
                console.print(f"[dim]{result['output'][:500]}[/dim]")
        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")


def cli():
    """Main CLI entry point."""
    app = BotuvicCLI()
    app.run()


if __name__ == "__main__":
    cli()
