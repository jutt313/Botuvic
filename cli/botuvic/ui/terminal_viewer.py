"""
Display terminal commands before execution.
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

console = Console()

class TerminalViewer:
    """Shows terminal commands and gets approval."""
    
    def show_command(self, command, permission_manager):
        """
        Show a terminal command and ask for approval.
        
        Args:
            command: Dict with command, description
            permission_manager: PermissionManager instance
            
        Returns:
            True if approved, False otherwise
        """
        cmd = command["command"]
        description = command.get("description", "")
        command_type = command.get("type", "general")
        
        # Determine permission type
        if "npm install" in cmd or "pip install" in cmd or "pip3 install" in cmd:
            permission_type = "package_install"
        elif cmd.startswith("git "):
            permission_type = "git_operations"
        else:
            permission_type = "terminal_execute"
        
        # Check permission
        if not permission_manager.check_permission(permission_type, cmd):
            return False
        
        # Show command
        console.print(f"\n[bold cyan]⚡ Terminal Command[/bold cyan]")
        
        if description:
            console.print(f"[dim]{description}[/dim]\n")
        
        # Syntax highlight the command
        syntax = Syntax(cmd, "bash", theme="monokai")
        console.print(Panel(syntax, title="Command"))
        
        # Ask for approval
        console.print()
        return Confirm.ask("[cyan]Execute this command?[/cyan]")

