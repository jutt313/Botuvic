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
        if self.permissions.get("mode") == "auto":
            return True

        if self.permissions.get("mode") == "read_only":
            if permission_type == "file_read":
                return True
            return False

        # Check specific rules (Claude Code style regex/glob would go here in future)

        # Check always allow/never allow lists
        if permission_type in self.permissions.get("always_allow", []):
            return True

        if permission_type in self.permissions.get("never_allow", []):
            return False

        # If we are here, we need to ASK.
        return self.ask_permission(permission_type, details)
    
    def ask_permission(self, permission_type, details):
        """Ask user for permission with simple numbered menu."""
        permission_name = self.PERMISSION_TYPES.get(permission_type, permission_type)

        # Build question
        if "terminal" in permission_type.lower() or "execute" in permission_type.lower():
            question = "Should I execute this command?"
        elif "file_write" in permission_type or "file_edit" in permission_type:
            question = "Should I modify this file?"
        elif "file_create" in permission_type:
            question = "Should I create this file?"
        elif "file_delete" in permission_type:
            question = "Should I delete this file?"
        elif "git" in permission_type.lower():
            question = "Should I run this git operation?"
        elif "package" in permission_type.lower():
            question = "Should I install this package?"
        else:
            question = f"Allow: {permission_name}?"

        console.print(f"\n[bold #A855F7]{question}[/bold #A855F7]")

        if details:
            console.print(f"[dim]{details}[/dim]")

        console.print()

        # Display options with Rich formatting - Purple monochrome
        console.print("[#C084FC]1.[/#C084FC] [bold #FFFFFF]Yes, execute now[/bold #FFFFFF]")
        console.print("   [#64748B]Run this action one time[/#64748B]\n")

        console.print("[#C084FC]2.[/#C084FC] [bold #FFFFFF]Always allow this type[/bold #FFFFFF]")
        console.print(f"   [#64748B]Don't ask again for {permission_type}[/#64748B]\n")

        console.print("[#C084FC]3.[/#C084FC] [bold #FFFFFF]No, skip this time[/bold #FFFFFF]")
        console.print("   [#64748B]Don't run this action[/#64748B]\n")

        console.print("[#C084FC]4.[/#C084FC] [bold #FFFFFF]Never allow this type[/bold #FFFFFF]")
        console.print(f"   [#64748B]Block all {permission_type} actions[/#64748B]\n")

        console.print("[#C084FC]5.[/#C084FC] [bold #FFFFFF]Switch to Auto mode[/bold #FFFFFF]")
        console.print("   [#64748B]Allow all actions without asking[/#64748B]\n")

        # Get user choice
        try:
            choice = Prompt.ask(
                "Select",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )
        except (KeyboardInterrupt, EOFError):
            return False

        if not choice:
            return False

        # Handle choice (now using numbers)
        if choice == '2':  # Always allow
            if permission_type not in self.permissions["always_allow"]:
                self.permissions["always_allow"].append(permission_type)
                self.save_permissions()
            console.print(f"\n[green]✓ Added '{permission_type}' to always allow list[/green]\n")
            return True

        elif choice == '4':  # Never allow
            if permission_type not in self.permissions["never_allow"]:
                self.permissions["never_allow"].append(permission_type)
                self.save_permissions()
            console.print(f"\n[red]✗ Added '{permission_type}' to never allow list[/red]\n")
            return False

        elif choice == '5':  # Auto mode
            console.print("\n[bold red]⚠ Switching to Auto Mode[/bold red]")
            console.print("Botuvic will no longer ask for permissions.\n")
            if Confirm.ask("Are you sure?", default=False):
                self.permissions["mode"] = "auto"
                self.save_permissions()
                console.print("[green]✓ Auto mode enabled[/green]\n")
                return True
            else:
                return self.ask_permission(permission_type, details) # Ask again

        elif choice == '3':  # No, skip
            console.print("\n[yellow]⊘ Skipped[/yellow]\n")
            return False

        else:  # '1' - Yes, execute now
            console.print("\n[green]✓ Approved[/green]\n")
            return True
    
    def set_mode(self, mode):
        """Set permission mode."""
        if mode in ["ask", "auto", "read_only"]:
            self.permissions["mode"] = mode
            self.save_permissions()
    
    def show_permissions(self):
        """Display current permissions."""
        table = Table(title="Permission Settings", show_header=True, header_style="bold #A855F7")
        table.add_column("Setting", style="#C084FC")
        table.add_column("Value", style="#10B981")
        
        table.add_row("Mode", self.permissions.get("mode", "ask").upper())
        
        always = ", ".join(self.permissions.get("always_allow", []))
        if not always: always = "[dim]None[/dim]"
        table.add_row("Always Allow", always)
        
        never = ", ".join(self.permissions.get("never_allow", []))
        if not never: never = "[dim]None[/dim]"
        table.add_row("Never Allow", never)
        
        console.print()
        console.print(table)

