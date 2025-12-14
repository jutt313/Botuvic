"""
Display code changes with diff view.
"""

import os
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Confirm
import difflib

console = Console()

class CodeChangeViewer:
    """Shows code changes and gets user approval."""
    
    def show_change(self, change, permission_manager):
        """
        Show a code change and ask for approval.
        
        Args:
            change: Dict with file, old_content, new_content
            permission_manager: PermissionManager instance
            
        Returns:
            True if approved, False otherwise
        """
        file_path = change["file"]
        old_content = change.get("old_content", "")
        new_content = change["new_content"]
        change_type = change.get("type", "edit")  # create, edit, delete
        
        # Check permissions
        if change_type == "create":
            if not permission_manager.check_permission("file_create", f"Create {file_path}"):
                return False
        elif change_type == "delete":
            if not permission_manager.check_permission("file_delete", f"Delete {file_path}"):
                return False
        else:
            if not permission_manager.check_permission("file_write", f"Edit {file_path}"):
                return False
        
        # Show change
        console.print(f"\n[bold cyan]📝 Code Change: {file_path}[/bold cyan]")
        console.print(f"[dim]Type: {change_type}[/dim]\n")
        
        if change_type == "create":
            # Show new file content
            syntax = Syntax(new_content, self._get_language(file_path), theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="New File"))
        
        elif change_type == "delete":
            console.print("[red]This file will be deleted.[/red]")
        
        else:
            # Show diff
            self.show_diff(old_content, new_content, file_path)
        
        # Ask for approval
        console.print()
        return Confirm.ask("[cyan]Apply this change?[/cyan]")
    
    def show_diff(self, old_content, new_content, filename):
        """Show unified diff."""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []
        
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{filename} (before)",
            tofile=f"{filename} (after)",
            lineterm=""
        ))
        
        if not diff:
            console.print("[dim]No changes detected[/dim]")
            return
        
        # Show diff with colors
        for line in diff:
            if line.startswith('+++') or line.startswith('---'):
                console.print(f"[bold]{line}[/bold]")
            elif line.startswith('+'):
                console.print(f"[green]{line}[/green]")
            elif line.startswith('-'):
                console.print(f"[red]{line}[/red]")
            elif line.startswith('@@'):
                console.print(f"[cyan]{line}[/cyan]")
            else:
                console.print(f"[dim]{line}[/dim]")
    
    def _get_language(self, file_path):
        """Detect language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
        }
        return lang_map.get(ext, 'text')

