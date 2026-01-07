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
        Show a terminal command and get approval via permission system.
        
        Args:
            command: Dict with command, description
            permission_manager: PermissionManager instance
            
        Returns:
            True if approved, False otherwise
        """
        cmd = command["command"]
        description = command.get("description", "")
        
        # Determine permission type
        if "npm install" in cmd or "pip install" in cmd or "pip3 install" in cmd:
            permission_type = "package_install"
        elif cmd.startswith("git "):
            permission_type = "git_operations"
        else:
            permission_type = "terminal_execute"
            
        # Show command UI first so user knows what they are approving
        console.print(f"\n[bold #A855F7]⚡ Terminal Command[/bold #A855F7]")
        
        if description:
            console.print(f"[dim]{description}[/dim]\n")
        
        # Syntax highlight the command
        syntax = Syntax(cmd, "bash", theme="monokai")
        console.print(Panel(syntax, title="Command"))
        
        # Check permission (This serves as the only confirmation)
        return permission_manager.check_permission(permission_type, "Execute command shown above")

