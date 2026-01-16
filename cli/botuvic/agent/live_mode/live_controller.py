"""
Live Development Mode Controller for Phase 10.
Orchestrates file watching, browser tracking, and proactive improvements.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .file_watcher import FileWatcher
from .browser_tracker import BrowserTracker
from .code_analyzer import CodeAnalyzer
from .auto_fixer import AutoFixer
from .notification_manager import NotificationManager
from .terminal_monitor import TerminalMonitor
from .network_tracker import NetworkTracker
from .session_logger import SessionLogger
from .git_manager import GitManager
from .test_runner import TestRunner
from .performance_monitor import PerformanceMonitor
from .deployment_checker import DeploymentChecker

console = Console()


class LiveModeController:
    """
    Controls Phase 10 Live Development Mode.
    Monitors code, detects issues, suggests improvements in real-time.
    """
    
    def __init__(self, agent, project_dir: str):
        """
        Initialize live mode controller.
        
        Args:
            agent: BotuvicAgent instance
            project_dir: Project root directory
        """
        self.agent = agent
        self.project_dir = project_dir
        self.storage = agent.storage
        self.llm = agent.llm
        
        # Core monitoring components
        self.file_watcher = None
        self.browser_tracker = None
        self.code_analyzer = None
        
        # Advanced components (9 new features)
        self.auto_fixer = None
        self.notification_manager = None
        self.terminal_monitor = None
        self.network_tracker = None
        self.session_logger = None
        self.git_manager = None
        self.test_runner = None
        self.performance_monitor = None
        self.deployment_checker = None
        
        # State
        self.is_active = False
        self.improvements_log = []
        self.active_files = {}  # Track which files user is working on
        
        # HTTP server for browser errors (simple)
        self.http_server_thread = None
    
    def activate(self) -> Dict[str, Any]:
        """
        Activate Phase 10 Live Development Mode.
        
        Returns:
            Activation status
        """
        if self.is_active:
            return {"success": False, "error": "Already active"}
        
        try:
            console.print("\n[bold #A855F7]🟢 Activating Live Development Mode...[/bold #A855F7]\n")
            
            # Initialize core components
            self.code_analyzer = CodeAnalyzer(self.llm, self.storage, self.project_dir)
            console.print("[dim]✓ Code analyzer initialized[/dim]")
            
            self.file_watcher = FileWatcher(self.project_dir, self._on_file_change)
            watcher_result = self.file_watcher.start()
            if not watcher_result.get("success"):
                console.print(f"[yellow]⚠ File watcher failed: {watcher_result.get('error')}[/yellow]")
            
            self.browser_tracker = BrowserTracker(self.project_dir, self._on_browser_error)
            tracker_result = self.browser_tracker.inject_tracking_script()
            if not tracker_result.get("success"):
                console.print(f"[yellow]⚠ Browser tracker failed: {tracker_result.get('error')}[/yellow]")
            
            # Initialize advanced components
            self.auto_fixer = AutoFixer(self.project_dir, self.storage)
            console.print("[dim]✓ Auto-fixer initialized[/dim]")
            
            self.notification_manager = NotificationManager()
            console.print("[dim]✓ Notification manager initialized[/dim]")
            
            self.terminal_monitor = TerminalMonitor(self.project_dir, self._on_terminal_error)
            # Terminal monitor will be started when a process is monitored
            console.print("[dim]✓ Terminal monitor initialized[/dim]")
            
            self.network_tracker = NetworkTracker(self.project_dir, self._on_network_issue)
            console.print("[dim]✓ Network tracker initialized[/dim]")
            
            self.session_logger = SessionLogger(self.project_dir, self.storage)
            self.session_logger.start_session()
            console.print("[dim]✓ Session logger initialized[/dim]")
            
            self.git_manager = GitManager(self.project_dir)
            console.print("[dim]✓ Git manager initialized[/dim]")
            
            self.test_runner = TestRunner(self.project_dir)
            console.print("[dim]✓ Test runner initialized[/dim]")
            
            self.performance_monitor = PerformanceMonitor(self.project_dir)
            # Performance monitor tracks automatically when methods are called
            console.print("[dim]✓ Performance monitor initialized[/dim]")
            
            self.deployment_checker = DeploymentChecker(self.project_dir)
            console.print("[dim]✓ Deployment checker initialized[/dim]")
            
            # Start HTTP server for browser errors
            self._start_error_server()
            
            # Update workflow state
            self.agent.workflow.phase_data.live_mode_active = True
            self.agent.workflow.phase_data.file_watcher_active = watcher_result.get("success", False)
            self.agent.workflow.phase_data.browser_console_tracking = tracker_result.get("success", False)
            self.agent.workflow.save_state()
            
            self.is_active = True
            
            # Show activation message
            self._show_activation_message()
            
            return {
                "success": True,
                "active": True,
                "file_watcher": watcher_result.get("success", False),
                "browser_tracker": tracker_result.get("success", False)
            }
        
        except Exception as e:
            console.print(f"[red]✗ Failed to activate live mode: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def deactivate(self) -> Dict[str, Any]:
        """
        Deactivate live mode.
        
        Returns:
            Deactivation status
        """
        if not self.is_active:
            return {"success": False, "error": "Not active"}
        
        try:
            # Stop core components
            if self.file_watcher:
                self.file_watcher.stop()
            
            # Stop advanced components
            if self.terminal_monitor:
                # TerminalMonitor doesn't need explicit stopping if no processes are running
                pass
            
            # Performance monitor doesn't need explicit stopping
            
            if self.session_logger:
                report = self.session_logger.end_session()
                console.print(f"\n[dim]Session report saved: {report.get('report_file', 'N/A')}[/dim]")
            
            # Stop HTTP server
            if self.http_server_thread:
                # Server will stop when thread ends
                pass
            
            # Update state
            self.agent.workflow.phase_data.live_mode_active = False
            self.agent.workflow.phase_data.file_watcher_active = False
            self.agent.workflow.phase_data.browser_console_tracking = False
            self.agent.workflow.save_state()
            
            self.is_active = False
            
            console.print("\n[dim]Live mode deactivated[/dim]\n")
            
            return {"success": True, "active": False}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _on_file_change(self, file_path: str, event_type: str):
        """
        Handle file change event.
        
        Args:
            file_path: Relative path to changed file
            event_type: 'modified' or 'created'
        """
        # Track active file
        self.active_files[file_path] = {
            "last_modified": datetime.now().isoformat(),
            "event_type": event_type
        }
        
        console.print(f"[dim]📝 {file_path} {event_type}[/dim]")
        
        # Analyze file
        analysis = self.code_analyzer.analyze_file(file_path)
        
        if analysis.get("success") and analysis.get("issues"):
            self._handle_code_issues(file_path, analysis)
    
    def _handle_code_issues(self, file_path: str, analysis: Dict[str, Any]):
        """
        Handle detected code issues.
        
        Args:
            file_path: File path
            analysis: Analysis results
        """
        issues = analysis.get("issues", [])
        
        # Filter by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        
        # Show critical/high issues immediately
        if critical_issues or high_issues:
            console.print(f"\n[bold yellow]⚠️  Issues detected in {file_path}:[/bold yellow]\n")
            
            for issue in critical_issues + high_issues:
                severity_color = "red" if issue["severity"] == "critical" else "yellow"
                console.print(f"[{severity_color}]●[/{severity_color}] Line {issue['line']}: {issue['message']}")
                console.print(f"  [dim]{issue['suggestion']}[/dim]\n")
            
            # Log improvement
            self._log_improvement({
                "type": "issue_detected",
                "file": file_path,
                "issues": critical_issues + high_issues,
                "timestamp": datetime.now().isoformat()
            })
    
    def _on_browser_error(self, error_data: Dict[str, Any]):
        """
        Handle browser console error.
        
        Args:
            error_data: Error data from browser
        """
        error_type = error_data.get("type", "error")
        message = error_data.get("message", "Unknown error")
        source = error_data.get("source", "Unknown")
        stack = error_data.get("stack", "")
        
        # Show error
        console.print(f"\n[bold red]🔴 Browser Error Detected![/bold red]")
        console.print(f"[red]Type:[/red] {error_type}")
        console.print(f"[red]Message:[/red] {message}")
        console.print(f"[dim]Source: {source}[/dim]\n")
        
        # Try to extract file and line
        file_info = self._extract_file_from_stack(stack)
        
        if file_info:
            console.print(f"[yellow]Analyzing {file_info['file']}...[/yellow]\n")
        
        # Log improvement
        self._log_improvement({
            "type": "browser_error",
            "error": error_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def _on_terminal_error(self, error_data: Dict[str, Any]):
        """
        Handle terminal error.
        
        Args:
            error_data: Error data from terminal
        """
        error_type = error_data.get("type", "error")
        message = error_data.get("message", "Unknown error")
        file_path = error_data.get("file", "Unknown")
        line = error_data.get("line", "?")
        
        # Show error with notification manager
        if self.notification_manager:
            self.notification_manager.add_notification(
                priority="high",
                notification_type="terminal_error",
                title=f"Terminal Error: {error_type}",
                message=message,
                context={"file": file_path, "line": line}
            )
        
        # Log improvement
        self._log_improvement({
            "type": "terminal_error",
            "error": error_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def _on_network_issue(self, issue_data: Dict[str, Any]):
        """
        Handle network issue.
        
        Args:
            issue_data: Network issue data
        """
        issue_type = issue_data.get("type", "network_issue")
        message = issue_data.get("message", "Unknown issue")
        
        # Show notification
        if self.notification_manager:
            self.notification_manager.add_notification(
                priority="medium",
                notification_type="network_issue",
                title=f"Network Issue: {issue_type}",
                message=message
            )
        
        # Log improvement
        self._log_improvement({
            "type": "network_issue",
            "issue": issue_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def _extract_file_from_stack(self, stack: str) -> Optional[Dict[str, Any]]:
        """Extract file and line number from stack trace."""
        if not stack:
            return None
        
        # Simple extraction - can be improved
        import re
        match = re.search(r'at\s+(.+?):(\d+):(\d+)', stack)
        if match:
            return {
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3))
            }
        return None
    
    def _log_improvement(self, improvement: Dict[str, Any]):
        """Log an improvement/issue."""
        self.improvements_log.append(improvement)
        
        # Keep only last 100
        if len(self.improvements_log) > 100:
            self.improvements_log = self.improvements_log[-100:]
        
        # Save to workflow
        self.agent.workflow.phase_data.improvements_log = self.improvements_log
        self.agent.workflow.save_state()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get live mode status including all components.
        
        Returns:
            Comprehensive status dict
        """
        status = {
            "active": self.is_active,
            "core_components": {
                "file_watcher": self.file_watcher.get_status() if self.file_watcher else None,
                "browser_tracker": self.browser_tracker.get_status() if self.browser_tracker else None,
                "code_analyzer": {"active": self.code_analyzer is not None}
            },
            "advanced_components": {
                "auto_fixer": {
                    "active": self.auto_fixer is not None,
                    "fixes_applied": len(self.auto_fixer.fix_history) if self.auto_fixer else 0
                },
                "notification_manager": {"active": self.notification_manager is not None},
                "terminal_monitor": {
                    "active": self.terminal_monitor is not None,
                    "monitoring": getattr(self.terminal_monitor, 'is_monitoring', False) if self.terminal_monitor else False
                },
                "network_tracker": {"active": self.network_tracker is not None},
                "session_logger": {
                    "active": self.session_logger is not None,
                    "session_active": self.session_logger.session.get("ended_at") is None if (self.session_logger and hasattr(self.session_logger, 'session')) else False
                },
                "git_manager": {"active": self.git_manager is not None},
                "test_runner": {
                    "active": self.test_runner is not None,
                    "framework": getattr(self.test_runner, 'test_framework', None) if self.test_runner else None
                },
                "performance_monitor": {
                    "active": self.performance_monitor is not None,
                    "monitoring": True if self.performance_monitor else False
                },
                "deployment_checker": {"active": self.deployment_checker is not None}
            },
            "activity": {
                "active_files": list(self.active_files.keys())[-5:],  # Last 5
                "improvements_count": len(self.improvements_log),
                "recent_improvements": self.improvements_log[-5:]
            }
        }
        
        return status
    
    def show_status(self):
        """Display status to user."""
        status = self.get_status()
        
        if not status["active"]:
            console.print("[dim]Live mode not active[/dim]")
            return
        
        # Create status table
        table = Table(title="🟢 Live Assistant Status", show_header=False, box=None)
        table.add_column("Key", style="dim")
        table.add_column("Value")
        
        table.add_row("Status", "[green]ACTIVE[/green]")
        table.add_row("File Watcher", "✓ Running" if status.get("file_watcher", {}).get("watching") else "✗ Stopped")
        table.add_row("Browser Tracker", "✓ Connected" if status.get("browser_tracker", {}).get("tracking") else "✗ Disconnected")
        table.add_row("Files Monitored", str(len(status.get("active_files", []))))
        table.add_row("Improvements", str(status.get("improvements_count", 0)))
        
        console.print(table)
        
        # Show recent activity
        recent = status.get("recent_improvements", [])
        if recent:
            console.print("\n[bold]Recent Activity:[/bold]")
            for imp in recent[-3:]:
                timestamp = imp.get("timestamp", "")
                imp_type = imp.get("type", "unknown")
                console.print(f"[dim]{timestamp}[/dim] - {imp_type}")
    
    def _show_activation_message(self):
        """Show activation message to user."""
        message = """[bold green]✅ Live Development Mode: ACTIVE[/bold green]

I'm now watching your code in real-time. Just code normally - I'll:
• [green]✓[/green] Monitor file changes automatically
• [green]✓[/green] Detect code issues before they become bugs
• [green]✓[/green] Track browser console errors
• [green]✓[/green] Suggest improvements proactively

[dim]Type 'status' anytime to see what I'm monitoring.[/dim]
"""
        console.print(Panel(message, border_style="#A855F7"))
    
    def _start_error_server(self):
        """Start simple HTTP server to receive browser errors."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import json
            
            controller = self
            
            class ErrorHandler(BaseHTTPRequestHandler):
                def do_POST(self):
                    if self.path == '/botuvic/console-error':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        
                        try:
                            error_data = json.loads(post_data.decode('utf-8'))
                            controller.browser_tracker.handle_browser_error(error_data)
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(b'{"success": true}')
                        except Exception as e:
                            self.send_response(500)
                            self.end_headers()
                
                def do_OPTIONS(self):
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                
                def log_message(self, format, *args):
                    pass  # Suppress logs
            
            server = HTTPServer(('localhost', 7777), ErrorHandler)
            
            def run_server():
                console.print("[dim]✓ Error server started on http://localhost:7777[/dim]")
                server.serve_forever()
            
            self.http_server_thread = threading.Thread(target=run_server, daemon=True)
            self.http_server_thread.start()
        
        except Exception as e:
            console.print(f"[yellow]⚠ Could not start error server: {e}[/yellow]")
    
    # ============================================================================
    # NEW FEATURE METHODS - Expose all 9 advanced components
    # ============================================================================
    
    def apply_fix(self, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply an auto-fix to a file.
        
        Args:
            fix_data: Fix details (file, old_code, new_code, line_number, etc.)
            
        Returns:
            Result dict
        """
        if not self.auto_fixer:
            return {"success": False, "error": "Auto-fixer not initialized"}
        
        return self.auto_fixer.apply_fix(fix_data)
    
    def undo_last_fix(self) -> Dict[str, Any]:
        """Undo the last applied fix."""
        if not self.auto_fixer:
            return {"success": False, "error": "Auto-fixer not initialized"}
        
        return self.auto_fixer.undo_fix()
    
    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run tests.
        
        Args:
            test_path: Optional specific test file/directory
            
        Returns:
            Test results
        """
        if not self.test_runner:
            return {"success": False, "error": "Test runner not initialized"}
        
        return self.test_runner.run_tests(test_path)
    
    def check_deployment_readiness(self) -> Dict[str, Any]:
        """
        Check if project is ready for deployment.
        
        Returns:
            Readiness report with score and issues
        """
        if not self.deployment_checker:
            return {"success": False, "error": "Deployment checker not initialized"}
        
        return self.deployment_checker.check_deployment_readiness()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance metrics report.
        
        Returns:
            Performance metrics
        """
        if not self.performance_monitor:
            return {"success": False, "error": "Performance monitor not initialized"}
        
        report_text = self.performance_monitor.get_performance_report()
        
        # Parse metrics from the monitor
        metrics = {
            "bundle_size": self.performance_monitor.bundle_sizes[-1] if self.performance_monitor.bundle_sizes else None,
            "build_time": self.performance_monitor.build_times[-1] if self.performance_monitor.build_times else None,
            "api_response_times": self.performance_monitor.analyze_api_performance()
        }
        
        return {
            "success": True,
            "report": report_text,
            "metrics": metrics
        }
    
    def get_session_report(self) -> Dict[str, Any]:
        """
        Get current session report.
        
        Returns:
            Session metrics and activity log
        """
        if not self.session_logger:
            return {"success": False, "error": "Session logger not initialized"}
        
        # Get current session data
        session = self.session_logger.session
        
        # Calculate duration if session is active
        if session.get("ended_at") is None:
            from datetime import datetime
            start_time = datetime.fromisoformat(session.get("started_at", datetime.now().isoformat()))
            duration_seconds = (datetime.now() - start_time).total_seconds()
        else:
            duration_seconds = session.get("duration_seconds", 0)
        
        return {
            "success": True,
            "metrics": {
                "duration": self.session_logger._format_duration(duration_seconds),
                "files_modified": len(session.get("files_modified", [])),
                "lines_added": session.get("lines_added", 0),
                "lines_removed": session.get("lines_removed", 0),
                "errors_fixed": session.get("errors_fixed", 0),
                "tests_run": session.get("tests_run", 0),
                "commits": session.get("commits", 0)
            },
            "session": session
        }
    
    def create_git_commit(self, message: Optional[str] = None, auto: bool = False) -> Dict[str, Any]:
        """
        Create a Git commit.
        
        Args:
            message: Commit message (auto-generated if None)
            auto: Whether to auto-generate semantic message
            
        Returns:
            Commit result
        """
        if not self.git_manager:
            return {"success": False, "error": "Git manager not initialized"}
        
        # Check if git repo exists
        if not self.git_manager._check_git_repo():
            return {"success": False, "error": "Not a git repository"}
        
        # If auto or no message, create a generic commit
        if auto or not message:
            # Use git status to create a meaningful commit
            status_result = self.git_manager._run_git(["status", "--porcelain"])
            if status_result.get("success"):
                changes = status_result.get("output", "").strip()
                if not changes:
                    return {"success": False, "error": "No changes to commit"}
                
                # Generate a simple commit message
                message = "chore: update code\n\n🤖 Auto-commit by BOTUVIC LiveAgent"
        
        # Use git commit directly
        result = self.git_manager._run_git(["commit", "-m", message])
        
        if result.get("success"):
            return {
                "success": True,
                "message": message,
                "output": result.get("output", "")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Commit failed")
            }
    
    def track_api_call(self, method: str, url: str, status_code: int, duration_ms: float) -> None:
        """
        Track an API call for network monitoring.
        
        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration_ms: Request duration in milliseconds
        """
        if self.network_tracker:
            self.network_tracker.track_request({
                "method": method,
                "url": url,
                "status": status_code,
                "duration": duration_ms
            })
    
    def get_network_report(self) -> Dict[str, Any]:
        """
        Get network tracking report.
        
        Returns:
            Network metrics and API call history
        """
        if not self.network_tracker:
            return {"success": False, "error": "Network tracker not initialized"}
        
        return self.network_tracker.get_report()
    
    def notify(self, notification: Dict[str, Any]) -> None:
        """
        Send a notification through the notification manager.

        Args:
            notification: Notification data (priority, type, title, message)
        """
        if self.notification_manager:
            self.notification_manager.add_notification(
                priority=notification.get("priority", "info"),
                notification_type=notification.get("type", "general"),
                title=notification.get("title", "Notification"),
                message=notification.get("message", ""),
                context=notification.get("context")
            )

