"""
Git Manager for Phase 10 Live Development Mode.
Handles auto-commits with smart commit messages and grouping.
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console

console = Console()


class GitManager:
    """
    Manages git integration for auto-commits.
    Features: Smart commit messages, grouping, conventional commits.
    """

    def __init__(self, project_dir: str):
        """
        Initialize git manager.

        Args:
            project_dir: Project root directory
        """
        self.project_dir = project_dir
        self.pending_changes = []
        self.auto_commit_enabled = False

        # Check if git repo
        self.is_git_repo = self._check_git_repo()

    def enable_auto_commit(self, mode: str = "after_fix") -> Dict[str, Any]:
        """
        Enable auto-commit mode.

        Args:
            mode: Commit mode (after_fix, session_end, manual)

        Returns:
            Status dict
        """
        if not self.is_git_repo:
            return {"success": False, "error": "Not a git repository"}

        self.auto_commit_enabled = True
        self.commit_mode = mode

        console.print(f"[green]✓ Auto-commit enabled (mode: {mode})[/green]")

        return {"success": True, "mode": mode}

    def disable_auto_commit(self) -> Dict[str, Any]:
        """Disable auto-commit."""
        self.auto_commit_enabled = False
        return {"success": True}

    def commit_fix(self, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Commit a code fix.

        Args:
            fix_data: Fix information containing:
                - file: File path
                - issue: Issue description
                - severity: Issue severity
                - type: Fix type (bug, refactor, perf, etc.)

        Returns:
            Commit result
        """
        if not self.is_git_repo:
            return {"success": False, "error": "Not a git repository"}

        file_path = fix_data.get("file")
        issue = fix_data.get("issue", "Code improvement")
        severity = fix_data.get("severity", "medium")
        fix_type = fix_data.get("type", "fix")

        try:
            # Stage the file
            self._run_git(["add", file_path])

            # Generate commit message
            commit_message = self._generate_commit_message(fix_data)

            # Commit
            result = self._run_git(["commit", "-m", commit_message])

            if result["returncode"] == 0:
                # Get commit hash
                hash_result = self._run_git(["rev-parse", "--short", "HEAD"])
                commit_hash = hash_result["stdout"].strip() if hash_result["returncode"] == 0 else "unknown"

                console.print(f"[green]✓ Committed: {commit_hash} - {fix_type}({file_path.split('/')[0]}): {issue[:50]}[/green]")

                return {
                    "success": True,
                    "commit_hash": commit_hash,
                    "message": commit_message,
                    "file": file_path
                }
            else:
                error = result["stderr"] or "Commit failed"
                return {"success": False, "error": error}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def commit_grouped_fixes(self, fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Commit multiple related fixes as a group.

        Args:
            fixes: List of fix data dicts

        Returns:
            Commit result
        """
        if not self.is_git_repo:
            return {"success": False, "error": "Not a git repository"}

        if not fixes:
            return {"success": False, "error": "No fixes to commit"}

        try:
            # Group fixes by type and module
            grouped = self._group_fixes(fixes)

            commit_results = []

            for group_key, group_fixes in grouped.items():
                # Stage all files in group
                for fix in group_fixes:
                    self._run_git(["add", fix.get("file")])

                # Generate grouped commit message
                commit_message = self._generate_grouped_commit_message(group_fixes)

                # Commit
                result = self._run_git(["commit", "-m", commit_message])

                if result["returncode"] == 0:
                    hash_result = self._run_git(["rev-parse", "--short", "HEAD"])
                    commit_hash = hash_result["stdout"].strip() if hash_result["returncode"] == 0 else "unknown"

                    console.print(f"[green]✓ Committed: {commit_hash} - {len(group_fixes)} fixes[/green]")

                    commit_results.append({
                        "commit_hash": commit_hash,
                        "fixes_count": len(group_fixes),
                        "message": commit_message
                    })

            return {
                "success": True,
                "commits": commit_results,
                "total_fixes": len(fixes)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_commit_message(self, fix_data: Dict[str, Any]) -> str:
        """
        Generate semantic commit message.

        Args:
            fix_data: Fix information

        Returns:
            Formatted commit message
        """
        file_path = fix_data.get("file", "")
        issue = fix_data.get("issue", "Code improvement")
        fix_type = self._determine_commit_type(fix_data)

        # Get module/scope from file path
        scope = self._extract_scope(file_path)

        # Build subject line
        subject = f"{fix_type}"
        if scope:
            subject += f"({scope})"
        subject += f": {issue[:60]}"

        # Build body
        body_parts = []

        # Add details
        if fix_data.get("old_code") and fix_data.get("new_code"):
            body_parts.append("Changes:")
            body_parts.append(f"- Improved code quality")
            body_parts.append(f"- Fixed: {issue}")

        # Add severity
        severity = fix_data.get("severity")
        if severity in ["critical", "high"]:
            body_parts.append(f"\nSeverity: {severity}")

        # Add footer
        body_parts.append("\n🤖 Generated with BOTUVIC LiveAgent")
        body_parts.append("Co-Authored-By: BOTUVIC Agent <noreply@botuvic.com>")

        # Combine
        if body_parts:
            return f"{subject}\n\n" + "\n".join(body_parts)
        else:
            return subject

    def _generate_grouped_commit_message(self, fixes: List[Dict[str, Any]]) -> str:
        """Generate commit message for grouped fixes."""
        if len(fixes) == 1:
            return self._generate_commit_message(fixes[0])

        # Determine common type
        types = [self._determine_commit_type(f) for f in fixes]
        common_type = max(set(types), key=types.count)

        # Extract common scope
        scopes = [self._extract_scope(f.get("file", "")) for f in fixes]
        common_scope = max(set(scopes), key=scopes.count) if scopes else None

        # Build subject
        subject = f"{common_type}"
        if common_scope:
            subject += f"({common_scope})"
        subject += f": Multiple improvements ({len(fixes)} fixes)"

        # Build body
        body_parts = ["Fixed issues:"]

        for fix in fixes[:5]:  # Show first 5
            issue = fix.get("issue", "improvement")[:50]
            file = fix.get("file", "")
            body_parts.append(f"- {file}: {issue}")

        if len(fixes) > 5:
            body_parts.append(f"- ... and {len(fixes) - 5} more")

        body_parts.append("\n🤖 Generated with BOTUVIC LiveAgent")
        body_parts.append("Co-Authored-By: BOTUVIC Agent <noreply@botuvic.com>")

        return f"{subject}\n\n" + "\n".join(body_parts)

    def _determine_commit_type(self, fix_data: Dict[str, Any]) -> str:
        """
        Determine conventional commit type.

        Args:
            fix_data: Fix information

        Returns:
            Commit type (fix, feat, refactor, perf, etc.)
        """
        issue = fix_data.get("issue", "").lower()
        fix_type = fix_data.get("type", "").lower()

        # Map to conventional commit types
        if "bug" in issue or "error" in issue or fix_type == "bug":
            return "fix"
        elif "performance" in issue or "slow" in issue or fix_type == "performance":
            return "perf"
        elif "security" in issue or "vulnerability" in issue:
            return "fix"  # Security fixes are bugs
        elif "refactor" in issue or fix_type == "refactor":
            return "refactor"
        elif "style" in issue or "format" in issue:
            return "style"
        elif "test" in issue:
            return "test"
        elif "docs" in issue or "documentation" in issue:
            return "docs"
        else:
            return "fix"  # Default to fix

    def _extract_scope(self, file_path: str) -> Optional[str]:
        """Extract scope (module name) from file path."""
        if not file_path:
            return None

        # Split path
        parts = file_path.split('/')

        # Get meaningful scope
        if len(parts) >= 2:
            # Use first directory (frontend, backend, etc.)
            return parts[0]
        elif len(parts) == 1:
            # Just filename
            return os.path.splitext(parts[0])[0]
        else:
            return None

    def _group_fixes(self, fixes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group fixes by type and module."""
        grouped = {}

        for fix in fixes:
            commit_type = self._determine_commit_type(fix)
            scope = self._extract_scope(fix.get("file", ""))

            key = f"{commit_type}_{scope or 'general'}"

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(fix)

        return grouped

    def get_status(self) -> Dict[str, Any]:
        """Get git status."""
        if not self.is_git_repo:
            return {"is_repo": False}

        try:
            # Get branch
            branch_result = self._run_git(["branch", "--show-current"])
            branch = branch_result["stdout"].strip() if branch_result["returncode"] == 0 else "unknown"

            # Get status
            status_result = self._run_git(["status", "--porcelain"])
            has_changes = bool(status_result["stdout"].strip())

            # Get last commit
            log_result = self._run_git(["log", "-1", "--pretty=format:%h %s"])
            last_commit = log_result["stdout"].strip() if log_result["returncode"] == 0 else "No commits"

            return {
                "is_repo": True,
                "branch": branch,
                "has_changes": has_changes,
                "last_commit": last_commit,
                "auto_commit_enabled": self.auto_commit_enabled
            }

        except Exception as e:
            return {"is_repo": True, "error": str(e)}

    def _check_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        try:
            result = self._run_git(["rev-parse", "--git-dir"])
            return result["returncode"] == 0
        except:
            return False

    def _run_git(self, args: List[str]) -> Dict[str, Any]:
        """
        Run git command.

        Args:
            args: Git command arguments

        Returns:
            Result dict with returncode, stdout, stderr
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e)
            }
