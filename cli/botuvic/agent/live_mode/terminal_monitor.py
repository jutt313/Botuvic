"""
Terminal Output Monitor for Phase 10 Live Development Mode.
Monitors dev server output, build errors, and terminal messages.
"""

import re
import subprocess
import threading
import queue
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from rich.console import Console

console = Console()


class TerminalMonitor:
    """
    Monitors terminal output from dev servers and build tools.
    Detects errors, warnings, and important messages in real-time.
    """

    def __init__(self, project_dir: str, on_error_callback: Callable):
        """
        Initialize terminal monitor.

        Args:
            project_dir: Project root directory
            on_error_callback: Function to call when error detected
        """
        self.project_dir = project_dir
        self.on_error_callback = on_error_callback
        self.monitored_processes = {}
        self.output_queue = queue.Queue()
        self.is_monitoring = False
        self.error_log = []

        # Error patterns to detect
        self.error_patterns = [
            # Build errors
            (r"SyntaxError:? (.+)", "syntax_error", "critical"),
            (r"Module not found:? (.+)", "module_not_found", "critical"),
            (r"Cannot find module (.+)", "module_not_found", "critical"),
            (r"Failed to compile", "build_failed", "critical"),
            (r"Build failed", "build_failed", "critical"),
            (r"ERROR in (.+)", "build_error", "high"),

            # Runtime errors
            (r"TypeError:? (.+)", "type_error", "critical"),
            (r"ReferenceError:? (.+)", "reference_error", "critical"),
            (r"Error: listen EADDRINUSE (.+)", "port_in_use", "high"),
            (r"ECONNREFUSED", "connection_refused", "high"),

            # Dependency errors
            (r"npm ERR! (.+)", "npm_error", "high"),
            (r"ERESOLVE unable to resolve dependency", "dependency_conflict", "high"),
            (r"peer dependency", "peer_dependency", "medium"),

            # Database errors
            (r"Connection refused", "db_connection_refused", "high"),
            (r"Authentication failed", "auth_failed", "high"),
            (r"relation .+ does not exist", "table_not_found", "high"),
            (r"column .+ does not exist", "column_not_found", "high"),

            # Warnings
            (r"Warning: (.+)", "warning", "medium"),
            (r"DeprecationWarning: (.+)", "deprecation", "low"),
        ]

    def start_monitoring(self, process_name: str, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Start monitoring a terminal process.

        Args:
            process_name: Name to identify process (e.g., "frontend", "backend")
            command: Command to run (e.g., ["npm", "run", "dev"])
            cwd: Working directory (defaults to project_dir)

        Returns:
            Status dict
        """
        if process_name in self.monitored_processes:
            return {"success": False, "error": f"Process {process_name} already monitored"}

        try:
            cwd = cwd or self.project_dir

            # Start process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.monitored_processes[process_name] = {
                "process": process,
                "command": command,
                "started_at": datetime.now().isoformat(),
                "errors_detected": 0
            }

            # Start output reader thread
            reader_thread = threading.Thread(
                target=self._read_output,
                args=(process_name, process),
                daemon=True
            )
            reader_thread.start()

            console.print(f"[green]✓[/green] Monitoring {process_name} terminal output")

            self.is_monitoring = True

            return {
                "success": True,
                "process": process_name,
                "pid": process.pid
            }

        except Exception as e:
            console.print(f"[red]✗ Failed to start monitoring {process_name}: {e}[/red]")
            return {"success": False, "error": str(e)}

    def stop_monitoring(self, process_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop monitoring process(es).

        Args:
            process_name: Specific process to stop (or None for all)

        Returns:
            Status dict
        """
        if process_name:
            if process_name not in self.monitored_processes:
                return {"success": False, "error": f"Process {process_name} not monitored"}

            proc_info = self.monitored_processes[process_name]
            proc_info["process"].terminate()
            del self.monitored_processes[process_name]

            return {"success": True, "stopped": [process_name]}

        else:
            # Stop all
            stopped = []
            for name, proc_info in list(self.monitored_processes.items()):
                proc_info["process"].terminate()
                stopped.append(name)

            self.monitored_processes.clear()
            self.is_monitoring = False

            return {"success": True, "stopped": stopped}

    def _read_output(self, process_name: str, process: subprocess.Popen):
        """
        Read output from process in background thread.

        Args:
            process_name: Process identifier
            process: Subprocess object
        """
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # Analyze line for errors
                error_detected = self._analyze_line(process_name, line)

                if error_detected:
                    self.monitored_processes[process_name]["errors_detected"] += 1

        except Exception as e:
            console.print(f"[yellow]⚠ Error reading output from {process_name}: {e}[/yellow]")

    def _analyze_line(self, process_name: str, line: str) -> bool:
        """
        Analyze output line for errors.

        Args:
            process_name: Process identifier
            line: Output line

        Returns:
            True if error detected
        """
        for pattern, error_type, severity in self.error_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract error details
                error_message = match.group(1) if match.groups() else line

                # Try to extract file and line number
                file_info = self._extract_file_info(line)

                error_data = {
                    "process": process_name,
                    "type": error_type,
                    "severity": severity,
                    "message": error_message.strip(),
                    "full_line": line,
                    "file": file_info.get("file") if file_info else None,
                    "line": file_info.get("line") if file_info else None,
                    "timestamp": datetime.now().isoformat()
                }

                # Log error
                self.error_log.append(error_data)

                # Keep only last 100 errors
                if len(self.error_log) > 100:
                    self.error_log = self.error_log[-100:]

                # Call callback
                try:
                    self.on_error_callback(error_data)
                except Exception as e:
                    console.print(f"[yellow]⚠ Error callback failed: {e}[/yellow]")

                return True

        return False

    def _extract_file_info(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Extract file path and line number from error message.

        Args:
            line: Error line

        Returns:
            File info dict or None
        """
        # Common patterns:
        # at /path/to/file.js:123:45
        # /path/to/file.js:123:45
        # File "file.py", line 123

        patterns = [
            r'at\s+(.+?):(\d+):(\d+)',
            r'(.+?\.(?:js|jsx|ts|tsx|py|java|go|rs)):(\d+):(\d+)',
            r'(.+?\.(?:js|jsx|ts|tsx|py|java|go|rs)):(\d+)',
            r'File "(.+?)", line (\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return {
                    "file": match.group(1).strip(),
                    "line": int(match.group(2)) if len(match.groups()) >= 2 else None,
                    "column": int(match.group(3)) if len(match.groups()) >= 3 else None
                }

        return None

    def get_recent_errors(self, process_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors from terminal.

        Args:
            process_name: Filter by process (or None for all)
            limit: Max errors to return

        Returns:
            List of error dicts
        """
        errors = self.error_log

        if process_name:
            errors = [e for e in errors if e.get("process") == process_name]

        return errors[-limit:]

    def get_status(self) -> Dict[str, Any]:
        """
        Get monitoring status.

        Returns:
            Status dict
        """
        return {
            "monitoring": self.is_monitoring,
            "processes": {
                name: {
                    "pid": info["process"].pid,
                    "running": info["process"].poll() is None,
                    "started_at": info["started_at"],
                    "errors_detected": info["errors_detected"]
                }
                for name, info in self.monitored_processes.items()
            },
            "total_errors": len(self.error_log)
        }

    def clear_error_log(self):
        """Clear error log."""
        self.error_log.clear()
