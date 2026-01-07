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
        
        # Components
        self.file_watcher = None
        self.browser_tracker = None
        self.code_analyzer = None
        
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
            
            # Initialize components
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
            # Stop file watcher
            if self.file_watcher:
                self.file_watcher.stop()
            
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
        Get live mode status.
        
        Returns:
            Status dict
        """
        return {
            "active": self.is_active,
            "file_watcher": self.file_watcher.get_status() if self.file_watcher else None,
            "browser_tracker": self.browser_tracker.get_status() if self.browser_tracker else None,
            "active_files": list(self.active_files.keys())[-5:],  # Last 5
            "improvements_count": len(self.improvements_log),
            "recent_improvements": self.improvements_log[-5:]
        }
    
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

