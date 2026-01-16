"""
Unified Tools Module for BOTUVIC Agents.
Provides file operations, terminal commands, and permission management.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt
from ..ui.confirmation import ask_confirmation

console = Console()


class PermissionManager:
    """Handles permission requests for file and terminal operations."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.history = []

    def request_file_permission(
        self,
        action: str,
        file_path: str,
        content: str = None,
        diff: str = None
    ) -> Dict[str, Any]:
        """
        Request permission for file operation.

        Args:
            action: create | modify | delete
            file_path: Path to the file
            content: File content (for create/modify)
            diff: Diff string (for modify)

        Returns:
            Dict with approved, action taken
        """
        if self.auto_approve:
            return {"approved": True, "action": "accepted"}

        # Build permission UI
        action_label = {
            "create": "create",
            "modify": "modify",
            "delete": "delete"
        }.get(action, action)

        console.print()
        console.print(Panel(
            f"[bold]BOTUVIC wants to {action_label}:[/bold] {file_path}",
            border_style="yellow"
        ))

        # Show content preview for create/modify
        if content and action != "delete":
            lines = content.split('\n')
            preview = '\n'.join(lines[:20])
            if len(lines) > 20:
                preview += f"\n... ({len(lines) - 20} more lines)"

            # Detect language for syntax highlighting
            ext = Path(file_path).suffix
            lang = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.tsx': 'tsx', '.jsx': 'jsx', '.json': 'json', '.sql': 'sql',
                '.md': 'markdown', '.css': 'css', '.html': 'html',
                '.yaml': 'yaml', '.yml': 'yaml', '.sh': 'bash'
            }.get(ext, 'text')

            syntax = Syntax(preview, lang, theme="monokai", line_numbers=True)
            console.print(syntax)

        # Show diff for modify
        if diff:
            console.print(Panel(diff, title="Changes", border_style="cyan"))

        # Show options including "View full"
        import questionary
        from questionary import Style
        from ..ui.confirmation import CONFIRMATION_STYLE
        
        choices = [
            questionary.Choice("✅ Yes, proceed", "yes"),
            questionary.Choice("👁️  View full content", "view"),
            questionary.Choice("❌ No, skip", "no"),
            questionary.Choice("✏️  Yes, but need...", "yes_but"),
            questionary.Choice("🛑 Esc, stop all", "stop")
        ]
        
        selection = questionary.select(
            "[Y] Yes, proceed    [N] No, skip    [E] Esc, stop all    [V] View full",
            choices=choices,
            style=CONFIRMATION_STYLE,
            instruction="(Use ↑↓ arrow keys, press Enter to select)"
        ).ask()
        
        # Handle "view full" option
        if selection == "view" and content:
            console.print(Panel(content, title=file_path))
            # Ask again after viewing
            selection = questionary.select(
                "After viewing, what would you like to do?",
                choices=[
                    questionary.Choice("✅ Yes, proceed", "yes"),
                    questionary.Choice("❌ No, skip", "no"),
                    questionary.Choice("✏️  Yes, but need...", "yes_but"),
                    questionary.Choice("🛑 Esc, stop all", "stop")
                ],
                style=CONFIRMATION_STYLE,
                instruction="(Use ↑↓ arrow keys, press Enter to select)"
            ).ask()
        
        # Handle "yes_but" - ask for additional message
        if selection == "yes_but":
            console.print()
            additional_msg = console.input("[#A855F7]What do you need? [/#A855F7]")
            if additional_msg.strip():
                # Treat as no but save feedback
                result = {
                    "approved": False,
                    "action": "rejected",
                    "user_feedback": additional_msg.strip()
                }
            else:
                result = {
                    "approved": False,
                    "action": "rejected"
                }
        elif selection == "stop":
            result = {
                "approved": False,
                "action": "stopped"
            }
        elif selection == "yes":
            result = {
                "approved": True,
                "action": "accepted"
            }
        else:  # no or None
            result = {
                "approved": False,
                "action": "rejected"
            }

        self.history.append({
            "type": "file",
            "file_path": file_path,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        return result

    def request_terminal_permission(
        self,
        command: str,
        description: str = "",
        risk_level: str = "low",
        working_dir: str = None
    ) -> Dict[str, Any]:
        """
        Request permission for terminal command.

        Args:
            command: Command to execute
            description: What this command does
            risk_level: low | medium | high
            working_dir: Working directory

        Returns:
            Dict with approved, action taken
        """
        if self.auto_approve and risk_level == "low":
            return {"approved": True, "action": "accepted"}

        # Risk level styling
        risk_colors = {
            "low": "green",
            "medium": "yellow",
            "high": "red"
        }
        risk_color = risk_colors.get(risk_level, "white")

        console.print()
        console.print(Panel(
            f"[bold]BOTUVIC wants to run:[/bold]\n\n$ {command}",
            title=f"Terminal Command [{risk_level.upper()}]",
            border_style=risk_color
        ))

        if description:
            console.print(f"[dim]Purpose: {description}[/dim]")

        if working_dir:
            console.print(f"[dim]Directory: {working_dir}[/dim]")

        # High risk commands need double confirmation
        if risk_level == "high":
            console.print("[bold red]⚠️  HIGH RISK COMMAND - Proceed with caution![/bold red]")

        # Show interactive confirmation selector
        import questionary
        from ..ui.confirmation import CONFIRMATION_STYLE
        
        choices = [
            questionary.Choice("✅ Yes, run", "yes"),
            questionary.Choice("❌ No, skip", "no"),
            questionary.Choice("✏️  Yes, but need...", "yes_but"),
            questionary.Choice("🛑 Esc, stop all", "stop")
        ]
        
        selection = questionary.select(
            "[Y] Yes, run    [N] No, skip    [E] Esc, stop all",
            choices=choices,
            style=CONFIRMATION_STYLE,
            instruction="(Use ↑↓ arrow keys, press Enter to select)"
        ).ask()
        
        # Handle "yes_but" - ask for additional message
        user_requirements = None
        if selection == "yes_but":
            console.print()
            additional_msg = console.input("[#A855F7]What do you need? [/#A855F7]")
            user_requirements = additional_msg.strip() if additional_msg.strip() else None
            # For terminal commands, "yes_but" is still approved but with requirements
            selection = "yes"
        
        # Double confirm for high risk
        if risk_level == "high" and selection == "yes":
            console.print()
            double_confirm_choices = [
                questionary.Choice("✅ Yes, I'm sure", "yes"),
                questionary.Choice("❌ No, cancel", "no")
            ]
            double_confirm = questionary.select(
                "[bold red]⚠️  HIGH RISK - Are you absolutely sure?[/bold red]",
                choices=double_confirm_choices,
                style=CONFIRMATION_STYLE,
                instruction="(Use ↑↓ arrow keys, press Enter to select)"
            ).ask()
            if double_confirm != "yes":
                selection = "no"
        
        # Map selection to result
        if selection == "stop":
            result = {
                "approved": False,
                "action": "stopped"
            }
        elif selection == "yes":
            result = {
                "approved": True,
                "action": "accepted"
            }
            if user_requirements:
                result["user_requirements"] = user_requirements
        else:  # no or None
            result = {
                "approved": False,
                "action": "rejected"
            }

        self.history.append({
            "type": "terminal",
            "command": command,
            "risk_level": risk_level,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        return result


class FileTools:
    """File operation tools for agents."""

    def __init__(self, project_dir: str, permission_manager: PermissionManager = None):
        self.project_dir = project_dir
        self.permission = permission_manager or PermissionManager()
        self.backup_dir = os.path.join(project_dir, ".botuvic", "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read file contents.

        Args:
            file_path: Relative or absolute path

        Returns:
            Dict with content or error
        """
        full_path = self._get_full_path(file_path)

        try:
            if not os.path.exists(full_path):
                return {"success": False, "error": f"File not found: {file_path}"}

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "lines": len(content.split('\n')),
                "path": file_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(
        self,
        file_path: str,
        content: str,
        require_permission: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to file (create or overwrite).

        Args:
            file_path: Relative or absolute path
            content: File content
            require_permission: Whether to ask user permission

        Returns:
            Dict with success status
        """
        full_path = self._get_full_path(file_path)
        exists = os.path.exists(full_path)
        action = "modify" if exists else "create"

        # Request permission
        if require_permission:
            result = self.permission.request_file_permission(
                action=action,
                file_path=file_path,
                content=content
            )

            if not result["approved"]:
                return {
                    "success": False,
                    "skipped": True,
                    "reason": result["action"]
                }

        try:
            # Create backup if modifying
            if exists:
                self._create_backup(full_path)

            # Create parent directories
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            console.print(f"[green]✓[/green] {'Updated' if exists else 'Created'} {file_path}")

            return {
                "success": True,
                "action": action,
                "path": file_path
            }
        except Exception as e:
            console.print(f"[red]✗ Error writing {file_path}: {e}[/red]")
            return {"success": False, "error": str(e)}

    def delete_file(
        self,
        file_path: str,
        require_permission: bool = True
    ) -> Dict[str, Any]:
        """
        Delete a file.

        Args:
            file_path: Relative or absolute path
            require_permission: Whether to ask user permission

        Returns:
            Dict with success status
        """
        full_path = self._get_full_path(file_path)

        if not os.path.exists(full_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # Request permission
        if require_permission:
            result = self.permission.request_file_permission(
                action="delete",
                file_path=file_path
            )

            if not result["approved"]:
                return {
                    "success": False,
                    "skipped": True,
                    "reason": result["action"]
                }

        try:
            # Create backup before deleting
            self._create_backup(full_path)

            os.remove(full_path)
            console.print(f"[green]✓[/green] Deleted {file_path}")

            return {"success": True, "path": file_path}
        except Exception as e:
            console.print(f"[red]✗ Error deleting {file_path}: {e}[/red]")
            return {"success": False, "error": str(e)}

    def create_folder(
        self,
        folder_path: str,
        require_permission: bool = False
    ) -> Dict[str, Any]:
        """
        Create a folder (and parent folders).

        Args:
            folder_path: Relative or absolute path
            require_permission: Whether to ask user permission

        Returns:
            Dict with success status
        """
        full_path = self._get_full_path(folder_path)

        if os.path.exists(full_path):
            return {"success": True, "exists": True, "path": folder_path}

        try:
            os.makedirs(full_path, exist_ok=True)
            console.print(f"[green]✓[/green] Created folder {folder_path}")
            return {"success": True, "path": folder_path}
        except Exception as e:
            console.print(f"[red]✗ Error creating folder {folder_path}: {e}[/red]")
            return {"success": False, "error": str(e)}

    def list_files(
        self,
        folder_path: str = "",
        pattern: str = "*",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List files in a folder.

        Args:
            folder_path: Relative or absolute path
            pattern: Glob pattern
            recursive: Whether to search recursively

        Returns:
            Dict with file list
        """
        full_path = self._get_full_path(folder_path) if folder_path else self.project_dir

        try:
            path = Path(full_path)
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))

            # Convert to relative paths
            rel_files = [str(f.relative_to(self.project_dir)) for f in files if f.is_file()]

            return {
                "success": True,
                "files": rel_files,
                "count": len(rel_files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        full_path = self._get_full_path(file_path)
        return os.path.exists(full_path)

    def _get_full_path(self, file_path: str) -> str:
        """Get full path from relative path."""
        if os.path.isabs(file_path):
            return file_path
        return os.path.join(self.project_dir, file_path)

    def _create_backup(self, file_path: str) -> str:
        """Create backup of file before modification."""
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{filename}.{timestamp}")

        shutil.copy2(file_path, backup_path)
        return backup_path


class TerminalTools:
    """Terminal command tools for agents."""

    def __init__(self, project_dir: str, permission_manager: PermissionManager = None):
        self.project_dir = project_dir
        self.permission = permission_manager or PermissionManager()
        self.command_history = []

    def execute(
        self,
        command: str,
        description: str = "",
        working_dir: str = None,
        require_permission: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a terminal command.

        Args:
            command: Command to execute
            description: What this command does
            working_dir: Working directory (defaults to project_dir)
            require_permission: Whether to ask user permission
            timeout: Timeout in seconds

        Returns:
            Dict with stdout, stderr, return_code
        """
        cwd = working_dir or self.project_dir
        risk_level = self._assess_risk(command)

        # Request permission
        if require_permission:
            result = self.permission.request_terminal_permission(
                command=command,
                description=description,
                risk_level=risk_level,
                working_dir=cwd
            )

            if not result["approved"]:
                return {
                    "success": False,
                    "skipped": True,
                    "reason": result["action"]
                }

        try:
            console.print(f"[dim]Running: {command}[/dim]")

            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            success = result.returncode == 0

            if success:
                console.print(f"[green]✓[/green] Command completed")
            else:
                console.print(f"[red]✗[/red] Command failed (exit code {result.returncode})")

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                preview = '\n'.join(lines[:10])
                if len(lines) > 10:
                    preview += f"\n... ({len(lines) - 10} more lines)"
                console.print(f"[dim]{preview}[/dim]")

            if result.stderr and not success:
                console.print(f"[red]{result.stderr[:500]}[/red]")

            # Log command
            self.command_history.append({
                "command": command,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            console.print(f"[red]✗ Command timed out after {timeout}s[/red]")
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return {"success": False, "error": str(e)}

    def _assess_risk(self, command: str) -> str:
        """Assess risk level of a command."""
        cmd_lower = command.lower()

        # High risk commands
        high_risk = [
            'rm -rf', 'rm -r', 'rmdir', 'drop table', 'drop database',
            'delete from', 'truncate', 'git push --force', 'git push -f',
            'sudo', 'chmod 777', 'curl | bash', 'wget | bash'
        ]
        for hr in high_risk:
            if hr in cmd_lower:
                return "high"

        # Medium risk commands
        medium_risk = [
            'npm run build', 'npm run deploy', 'git commit', 'git push',
            'docker', 'pip install', 'npm publish', 'yarn publish'
        ]
        for mr in medium_risk:
            if mr in cmd_lower:
                return "medium"

        return "low"


class AgentTools:
    """
    Unified tool interface for all agents.
    Provides file operations, terminal commands, and utility functions.
    """

    def __init__(
        self,
        project_dir: str,
        storage=None,
        search_engine=None,
        auto_approve: bool = False
    ):
        self.project_dir = project_dir
        self.storage = storage
        self.search_engine = search_engine

        # Initialize permission manager
        self.permission = PermissionManager(auto_approve=auto_approve)

        # Initialize tool modules
        self.files = FileTools(project_dir, self.permission)
        self.terminal = TerminalTools(project_dir, self.permission)

    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents."""
        return self.files.read_file(path)

    def write_file(self, path: str, content: str, permission: bool = True) -> Dict[str, Any]:
        """Write content to file."""
        return self.files.write_file(path, content, permission)

    def delete_file(self, path: str, permission: bool = True) -> Dict[str, Any]:
        """Delete a file."""
        return self.files.delete_file(path, permission)

    def create_folder(self, path: str) -> Dict[str, Any]:
        """Create a folder."""
        return self.files.create_folder(path)

    def list_files(self, path: str = "", pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
        """List files in folder."""
        return self.files.list_files(path, pattern, recursive)

    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        return self.files.file_exists(path)

    # =========================================================================
    # TERMINAL OPERATIONS
    # =========================================================================

    def run_command(
        self,
        command: str,
        description: str = "",
        working_dir: str = None,
        permission: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute terminal command."""
        return self.terminal.execute(command, description, working_dir, permission, timeout)

    # =========================================================================
    # STORAGE OPERATIONS
    # =========================================================================

    def save_data(self, key: str, data: Any) -> Dict[str, Any]:
        """Save data to storage."""
        if self.storage:
            return self.storage.save(key, data)
        return {"success": False, "error": "No storage configured"}

    def load_data(self, key: str) -> Any:
        """Load data from storage."""
        if self.storage:
            return self.storage.load(key)
        return None

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    def search_online(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search online for information."""
        if self.search_engine:
            return self.search_engine.search(query, max_results)
        return {"error": "No search engine configured"}

    # =========================================================================
    # UTILITY FUNCTIONS
    # =========================================================================

    def get_project_structure(self) -> Dict[str, Any]:
        """Get current project folder structure."""
        structure = {}

        for root, dirs, files in os.walk(self.project_dir):
            # Skip hidden and common ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'
            ]]

            rel_root = os.path.relpath(root, self.project_dir)
            if rel_root == '.':
                rel_root = ''

            for f in files:
                if not f.startswith('.'):
                    path = os.path.join(rel_root, f) if rel_root else f
                    structure[path] = {
                        "type": "file",
                        "size": os.path.getsize(os.path.join(root, f))
                    }

        return {"success": True, "structure": structure, "file_count": len(structure)}
