"""
Intelligent Auto-Fix System for Phase 10 Live Development Mode.
Applies code fixes with backups, verification, and undo capability.
"""

import os
import re
import shutil
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()


class AutoFixer:
    """
    Intelligent system for applying code fixes automatically.
    Features: Backups, verification, undo capability, fix history.
    """

    def __init__(self, project_dir: str, storage):
        """
        Initialize auto-fixer.

        Args:
            project_dir: Project root directory
            storage: Storage for fix history
        """
        self.project_dir = project_dir
        self.storage = storage
        self.backup_dir = os.path.join(project_dir, '.botuvic', 'backups')
        self.fix_history_file = os.path.join(project_dir, '.botuvic', 'fix_history.json')

        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)

        # Load fix history
        self.fix_history = self._load_fix_history()

    def apply_fix(self, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a code fix with backup and verification.

        Args:
            fix_data: Fix information containing:
                - file: File path (relative)
                - issue: Issue description
                - old_code: Code to replace
                - new_code: Replacement code
                - line_start: Starting line number (optional)
                - line_end: Ending line number (optional)
                - severity: Issue severity

        Returns:
            Result dict with success status and details
        """
        file_path = fix_data.get('file')
        old_code = fix_data.get('old_code')
        new_code = fix_data.get('new_code')

        if not file_path or not new_code:
            return {"success": False, "error": "Missing file or code data"}

        full_path = os.path.join(self.project_dir, file_path)

        if not os.path.exists(full_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            # Step 1: Create backup
            backup_path = self._create_backup(full_path, file_path)
            console.print(f"[dim]📦 Backup created: {os.path.basename(backup_path)}[/dim]")

            # Step 2: Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Step 3: Apply fix
            if old_code:
                # Replace specific code
                if old_code not in original_content:
                    return {
                        "success": False,
                        "error": "Old code not found in file (file may have changed)"
                    }
                modified_content = original_content.replace(old_code, new_code, 1)
            else:
                # Use line numbers if provided
                line_start = fix_data.get('line_start')
                line_end = fix_data.get('line_end')

                if line_start:
                    lines = original_content.split('\n')
                    end = line_end or line_start
                    lines[line_start - 1:end] = [new_code]
                    modified_content = '\n'.join(lines)
                else:
                    return {"success": False, "error": "Need either old_code or line numbers"}

            # Step 4: Verify syntax (basic check)
            syntax_ok, syntax_error = self._verify_syntax(full_path, modified_content)
            if not syntax_ok:
                console.print(f"[yellow]⚠ Syntax verification failed: {syntax_error}[/yellow]")
                # Restore from backup if syntax is broken
                shutil.copy2(backup_path, full_path)
                return {
                    "success": False,
                    "error": f"Fix would break syntax: {syntax_error}",
                    "backup_restored": True
                }

            # Step 5: Write fixed content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            console.print(f"[green]✓ Fix applied to {file_path}[/green]")

            # Step 6: Log fix
            fix_id = self._generate_fix_id()
            fix_record = {
                "fix_id": fix_id,
                "timestamp": datetime.now().isoformat(),
                "file": file_path,
                "issue": fix_data.get('issue', 'Code improvement'),
                "severity": fix_data.get('severity', 'medium'),
                "old_code": old_code[:200] if old_code else None,  # First 200 chars
                "new_code": new_code[:200] if len(new_code) < 1000 else new_code[:200],
                "backup_path": backup_path,
                "line_start": fix_data.get('line_start'),
                "line_end": fix_data.get('line_end'),
                "applied": True,
                "verified": syntax_ok
            }

            self.fix_history.append(fix_record)
            self._save_fix_history()

            return {
                "success": True,
                "fix_id": fix_id,
                "file": file_path,
                "backup_path": backup_path,
                "verified": syntax_ok,
                "message": "Fix applied successfully"
            }

        except Exception as e:
            console.print(f"[red]✗ Failed to apply fix: {e}[/red]")
            return {"success": False, "error": str(e)}

    def undo_fix(self, fix_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Undo a previously applied fix.

        Args:
            fix_id: Specific fix ID to undo (or None for latest)

        Returns:
            Result dict
        """
        if not self.fix_history:
            return {"success": False, "error": "No fixes to undo"}

        # Find fix to undo
        if fix_id:
            fix_record = next((f for f in self.fix_history if f['fix_id'] == fix_id), None)
            if not fix_record:
                return {"success": False, "error": f"Fix {fix_id} not found"}
        else:
            # Get latest fix
            fix_record = self.fix_history[-1]

        if not fix_record.get('applied'):
            return {"success": False, "error": "Fix was not applied"}

        try:
            backup_path = fix_record.get('backup_path')
            file_path = fix_record.get('file')
            full_path = os.path.join(self.project_dir, file_path)

            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup file not found"}

            # Restore from backup
            shutil.copy2(backup_path, full_path)

            console.print(f"[green]✓ Undone: {fix_record['fix_id']}[/green]")
            console.print(f"[dim]Restored {file_path} from backup[/dim]")

            # Update fix record
            fix_record['undone'] = True
            fix_record['undone_at'] = datetime.now().isoformat()
            self._save_fix_history()

            return {
                "success": True,
                "fix_id": fix_record['fix_id'],
                "file": file_path,
                "message": "Fix undone successfully"
            }

        except Exception as e:
            console.print(f"[red]✗ Failed to undo fix: {e}[/red]")
            return {"success": False, "error": str(e)}

    def get_fix_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent fix history.

        Args:
            limit: Max number of fixes to return

        Returns:
            List of fix records
        """
        return self.fix_history[-limit:]

    def _create_backup(self, full_path: str, relative_path: str) -> str:
        """Create backup of file before modification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = relative_path.replace('/', '_').replace('\\', '_')
        backup_name = f"{safe_name}.backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)

        # Copy file to backup
        shutil.copy2(full_path, backup_path)

        return backup_path

    def _verify_syntax(self, file_path: str, content: str) -> tuple[bool, Optional[str]]:
        """
        Verify syntax of modified content.

        Args:
            file_path: File path
            content: Modified content

        Returns:
            (is_valid, error_message)
        """
        ext = os.path.splitext(file_path)[1]

        # Python syntax check
        if ext == '.py':
            try:
                compile(content, file_path, 'exec')
                return True, None
            except SyntaxError as e:
                return False, f"Line {e.lineno}: {e.msg}"

        # JavaScript/TypeScript basic check
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # Basic brace matching
            if content.count('{') != content.count('}'):
                return False, "Unmatched braces"
            if content.count('(') != content.count(')'):
                return False, "Unmatched parentheses"
            if content.count('[') != content.count(']'):
                return False, "Unmatched brackets"
            return True, None

        # For other files, assume syntax is OK
        return True, None

    def _generate_fix_id(self) -> str:
        """Generate unique fix ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"fix_{timestamp}_{random_hash}"

    def _load_fix_history(self) -> List[Dict[str, Any]]:
        """Load fix history from storage."""
        if os.path.exists(self.fix_history_file):
            try:
                with open(self.fix_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_fix_history(self):
        """Save fix history to storage."""
        try:
            # Keep only last 100 fixes
            if len(self.fix_history) > 100:
                self.fix_history = self.fix_history[-100:]

            with open(self.fix_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.fix_history, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]⚠ Could not save fix history: {e}[/yellow]")

    def show_fix_preview(self, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show preview of what fix will change.

        Args:
            fix_data: Fix information

        Returns:
            Preview data
        """
        file_path = fix_data.get('file')
        old_code = fix_data.get('old_code', '')
        new_code = fix_data.get('new_code', '')

        console.print("\n[bold cyan]Fix Preview:[/bold cyan]")
        console.print(f"[dim]File: {file_path}[/dim]")
        console.print(f"[dim]Issue: {fix_data.get('issue', 'Code improvement')}[/dim]")

        if old_code:
            console.print("\n[red]- BEFORE:[/red]")
            console.print(f"[dim]{old_code}[/dim]")

        console.print("\n[green]+ AFTER:[/green]")
        console.print(f"[dim]{new_code}[/dim]")

        console.print("\n[bold]Apply this fix? (y/n)[/bold]")

        return {
            "file": file_path,
            "before": old_code,
            "after": new_code,
            "issue": fix_data.get('issue')
        }
