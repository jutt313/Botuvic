"""
Permission management system like Claude Code.
"""

import json
import os
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table

console = Console()

class PermissionManager:
    """
    Manages permissions for file and terminal operations.
    Similar to Claude Code's permission system.
    """
    
    PERMISSION_TYPES = {
        "file_read": "Read files",
        "file_write": "Write/edit files",
        "file_create": "Create new files",
        "file_delete": "Delete files",
        "terminal_execute": "Execute terminal commands",
        "git_operations": "Git operations",
        "package_install": "Install packages"
    }
    
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.permissions_file = os.path.join(project_dir, ".botuvic", "permissions.json")
        self.permissions = {
            "mode": "ask",  # ask, auto, read_only
            "rules": {},
            "always_allow": [],
            "never_allow": []
        }
    
    def load_permissions(self):
        """Load permissions from file."""
        if os.path.exists(self.permissions_file):
            try:
                with open(self.permissions_file, 'r') as f:
                    self.permissions = json.load(f)
            except:
                pass
    
    def save_permissions(self):
        """Save permissions to file."""
        os.makedirs(os.path.dirname(self.permissions_file), exist_ok=True)
        with open(self.permissions_file, 'w') as f:
            json.dump(self.permissions, f, indent=2)
    
    def check_permission(self, permission_type, details=None):
        """
        Check if action is allowed.
        
        Args:
            permission_type: Type of permission
            details: Additional details about the action
            
        Returns:
            True if allowed, False if denied
        """
        # Check mode
        if self.permissions["mode"] == "auto":
            return True
        
        if self.permissions["mode"] == "read_only":
            if permission_type == "file_read":
                return True
            return False
        
        # Check always allow/never allow
        if permission_type in self.permissions["always_allow"]:
            return True
        
        if permission_type in self.permissions["never_allow"]:
            return False
        
        # Ask user
        return self.ask_permission(permission_type, details)
    
    def ask_permission(self, permission_type, details):
        """Ask user for permission."""
        permission_name = self.PERMISSION_TYPES.get(permission_type, permission_type)
        
        # Build prompt
        console.print(f"\n[yellow]🔒 Permission Request[/yellow]")
        console.print(f"[bold]{permission_name}[/bold]")
        
        if details:
            console.print(f"[dim]{details}[/dim]")
        
        console.print()
        
        # Ask
        choice = Prompt.ask(
            "[cyan]Allow?[/cyan]",
            choices=["y", "a", "n", "v", "s"],
            default="y"
        )
        
        if choice == 'a':
            self.permissions["always_allow"].append(permission_type)
            self.save_permissions()
            console.print("[green]✓ Always allowed[/green]")
            return True
        
        elif choice == 'v':
            self.permissions["never_allow"].append(permission_type)
            self.save_permissions()
            console.print("[red]✗ Never allowed[/red]")
            return False
        
        elif choice == 's':
            self.permissions["mode"] = "auto"
            self.save_permissions()
            console.print("[green]✓ Auto mode enabled[/green]")
            return True
        
        elif choice == 'n':
            return False
        
        else:  # 'y'
            return True
    
    def set_mode(self, mode):
        """Set permission mode."""
        if mode in ["ask", "auto", "read_only"]:
            self.permissions["mode"] = mode
            self.save_permissions()
    
    def show_permissions(self):
        """Display current permissions."""
        table = Table(title="Permission Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Mode", self.permissions["mode"].upper())
        table.add_row("Always Allow", ", ".join(self.permissions["always_allow"]) or "None")
        table.add_row("Never Allow", ", ".join(self.permissions["never_allow"]) or "None")
        
        console.print()
        console.print(table)

