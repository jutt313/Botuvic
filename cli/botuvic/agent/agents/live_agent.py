"""
LiveAgent - Silent Monitoring Agent for BOTUVIC.
Watches code, catches errors, suggests fixes, runs tests.
Implements 12 capabilities: file watch, error detection, fixes, tests, etc.
"""

import os
import re
import json
import subprocess
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..tools import AgentTools
from ..live_mode.file_watcher import FileWatcher
from ..live_mode.browser_tracker import BrowserTracker
from ..live_mode.terminal_monitor import TerminalMonitor
from ..live_mode.code_analyzer import CodeAnalyzer
from ..live_mode.auto_fixer import AutoFixer
from ..live_mode.test_runner import TestRunner
from ..live_mode.test_generator import TestGenerator
from ..live_mode.deployment_checker import DeploymentChecker
from ..live_mode.session_logger import SessionLogger
from ..live_mode.notification_manager import NotificationManager

console = Console()


class LiveAgent:
    """
    Silent monitoring agent that watches code and catches errors.
    Does NOT talk to users directly - reports to MainAgent.
    """

    # System prompt embedded directly
    SYSTEM_PROMPT = """# LiveAgent - Complete System Prompt

## IDENTITY

You are **LiveAgent** - a silent monitoring agent under MainAgent. You watch code, catch errors, suggest fixes, and help users build better code.

**You do NOT talk to users directly.** MainAgent handles all communication.
**You report everything to MainAgent, who shows it to users.**

---

## YOUR ROLE

```
MainAgent (talks to user)
    ↓ controls
CodeAgent (creates files)
    ↓ files ready
LiveAgent (YOU - monitors everything)
    ↓ reports to
MainAgent (shows to user)
```

---

## CAPABILITIES

1. **FILE WATCHING** - Monitor file changes (.ts, .tsx, .js, .jsx, .py, .vue, etc.)
2. **ERROR SCRIPT INJECTION** - Inject browser error tracking script
3. **TERMINAL MONITORING** - Parse terminal output for errors
4. **ERROR DETECTION & ANALYSIS** - Detect and analyze errors with suggested fixes
5. **PINPOINT ERRORS** - Show exact file, line, column of errors
6. **SUGGEST FIXES** - Provide code fixes with explanations
7. **APPLY FIXES** - Apply fixes with user permission
8. **ADD ERROR HANDLING** - Scan and add missing error handling
9. **SEARCH ONLINE** - Search for solutions to unknown errors
10. **RUN TESTS** - Run test suites with permission
11. **DEPLOYMENT CHECK** - Check if project is ready for deployment
12. **SESSION REPORTS** - Generate session reports with statistics

---

## PERMISSION RULES

| Action | Permission Required | Can Skip |
|--------|---------------------|----------|
| Watch files | No (passive) | N/A |
| Detect errors | No (passive) | N/A |
| Inject error script | Yes (once) | Yes |
| Suggest fix | No | N/A |
| Apply fix | Yes (each) | Yes |
| Add error handling | Yes (each/batch) | Yes |
| Run tests | Yes | Yes |
| Search online | No | N/A |
| Modify any file | Yes (always) | Yes |
| Run terminal command | Yes (always) | Yes |

---

## COMMUNICATION WITH MAINAGENT

Always report to MainAgent:
- Error detected → Report with suggested fix
- Fix applied → Report success
- Test results → Report pass/fail counts
- Need permission → Request through MainAgent

---

## ERROR HANDLING

**If fix fails:** Restore from backup and report
**If tests hang:** Report timeout and suggest checking for infinite loops

---

## FINAL NOTES

1. **Always report to MainAgent** - Never communicate directly with user
2. **Always ask permission for changes** - No silent modifications
3. **Always create backups** - Before any file change
4. **Prioritize critical errors** - Security, crashes first
5. **Batch similar issues** - Don't spam with notifications
6. **Search when unsure** - Use online search for unknown errors
7. **Track everything** - Full session logging for reports"""

    # Error tracking script for browser injection
    ERROR_TRACKING_SCRIPT = '''
// BOTUVIC LiveAgent Error Tracker
(function() {
  const BOTUVIC_ENDPOINT = 'http://localhost:7777/error';

  // Catch uncaught errors
  window.onerror = function(message, source, lineno, colno, error) {
    sendError({
      type: 'uncaught_error',
      message: message,
      source: source,
      line: lineno,
      column: colno,
      stack: error?.stack
    });
    return false;
  };

  // Catch unhandled promise rejections
  window.onunhandledrejection = function(event) {
    sendError({
      type: 'unhandled_rejection',
      message: event.reason?.message || String(event.reason),
      stack: event.reason?.stack
    });
  };

  // Catch console.error
  const originalError = console.error;
  console.error = function(...args) {
    sendError({
      type: 'console_error',
      message: args.map(a => String(a)).join(' ')
    });
    originalError.apply(console, args);
  };

  function sendError(errorData) {
    errorData.timestamp = new Date().toISOString();
    errorData.url = window.location.href;
    fetch(BOTUVIC_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorData)
    }).catch(() => {});
  }

  console.log('BOTUVIC LiveAgent: Monitoring active');
})();
'''

    def __init__(
        self,
        llm_client,
        storage,
        project_dir: str,
        tools: AgentTools = None
    ):
        """
        Initialize LiveAgent with all 9 monitoring components.
        
        Args:
            llm_client: LLM client for AI interactions
            storage: Storage system
            project_dir: Project root directory
            tools: AgentTools instance
        """
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
        self.tools = tools or AgentTools(project_dir=project_dir, storage=storage)

        # Monitoring state
        self.is_monitoring = False
        
        # Core components (initialized on activation)
        self.file_watcher = None
        self.browser_tracker = None
        self.terminal_monitor = None
        self.code_analyzer = None
        
        # Advanced components
        self.auto_fixer = None
        self.test_runner = None
        self.test_generator = None
        self.deployment_checker = None
        self.session_logger = None
        self.notification_manager = None
        
        # HTTP server for browser errors
        self.error_server_thread = None

        # Tracking
        self.errors_detected = []
        self.fixes_applied = []
        self.tests_run = []
        self.session_start = None

        # Backup directory
        self.backup_dir = os.path.join(project_dir, ".botuvic", "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    # =========================================================================
    # CAPABILITY 1: START/STOP MONITORING
    # =========================================================================

    def start_monitoring(self) -> Dict[str, Any]:
        """Start all 9 monitoring capabilities."""
        if self.is_monitoring:
            return {"success": False, "error": "Already monitoring"}

        console.print("\n[bold #A855F7]🟢 LiveAgent: Activating monitoring...[/bold #A855F7]\n")

        try:
            self.session_start = datetime.now()
            self.is_monitoring = True

            # 1. Code Analyzer (LLM-powered)
            try:
                self.code_analyzer = CodeAnalyzer(self.llm, self.storage, self.project_dir)
                console.print("[dim]✓ Code analyzer initialized[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Code analyzer failed: {e}[/yellow]")

            # 2. File Watcher
            try:
                self.file_watcher = FileWatcher(
                    project_dir=self.project_dir,
                    on_change_callback=self._on_file_change
                )
                watcher_result = self.file_watcher.start()
                if watcher_result.get("success"):
                    console.print("[dim]✓ File watcher started[/dim]")
                else:
                    console.print(f"[yellow]⚠ File watcher: {watcher_result.get('error')}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠ File watcher failed: {e}[/yellow]")

            # 3. Browser Tracker
            try:
                self.browser_tracker = BrowserTracker(self.project_dir, self._on_browser_error)
                tracker_result = self.browser_tracker.inject_tracking_script()
                if tracker_result.get("success"):
                    console.print("[dim]✓ Browser tracker injected[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Browser tracker failed: {e}[/yellow]")

            # 4. Terminal Monitor
            try:
                self.terminal_monitor = TerminalMonitor(self.project_dir, self._on_terminal_error)
                console.print("[dim]✓ Terminal monitor ready[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Terminal monitor failed: {e}[/yellow]")

            # 5. Auto Fixer
            try:
                self.auto_fixer = AutoFixer(self.project_dir, self.storage)
                console.print("[dim]✓ Auto-fixer initialized[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Auto-fixer failed: {e}[/yellow]")

            # 6. Test Runner
            try:
                self.test_runner = TestRunner(self.project_dir)
                console.print("[dim]✓ Test runner ready[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Test runner failed: {e}[/yellow]")

            # 7. Deployment Checker
            try:
                self.deployment_checker = DeploymentChecker(self.project_dir)
                console.print("[dim]✓ Deployment checker ready[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Deployment checker failed: {e}[/yellow]")

            # 8. Session Logger
            try:
                self.session_logger = SessionLogger(self.project_dir, self.storage)
                self.session_logger.start_session()
                console.print("[dim]✓ Session logger started[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Session logger failed: {e}[/yellow]")

            # 9. Notification Manager
            try:
                self.notification_manager = NotificationManager()
                console.print("[dim]✓ Notification manager ready[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Notification manager failed: {e}[/yellow]")

            # 10. Test Generator (AI-powered)
            try:
                self.test_generator = TestGenerator(self.project_dir, self.llm, self.storage)
                console.print("[dim]✓ Test generator ready[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠ Test generator failed: {e}[/yellow]")

            # Start HTTP error server for browser errors
            self._start_error_server()

            # Show activation message
            self._show_activation_message()

            return {
                "success": True,
                "monitoring": True,
                "components": {
                    "file_watcher": self.file_watcher is not None,
                    "browser_tracker": self.browser_tracker is not None,
                    "terminal_monitor": self.terminal_monitor is not None,
                    "code_analyzer": self.code_analyzer is not None,
                    "auto_fixer": self.auto_fixer is not None,
                    "test_runner": self.test_runner is not None,
                    "deployment_checker": self.deployment_checker is not None,
                    "session_logger": self.session_logger is not None,
                    "notification_manager": self.notification_manager is not None
                }
            }

        except Exception as e:
            console.print(f"[red]✗ LiveAgent activation failed: {e}[/red]")
            self.is_monitoring = False
            return {"success": False, "error": str(e)}

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop all monitoring capabilities."""
        if not self.is_monitoring:
            return {"success": False, "error": "Not monitoring"}

        console.print("[dim]LiveAgent: Stopping monitoring...[/dim]")

        # Stop file watcher
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher = None

        self.is_monitoring = False

        # Generate session report
        report = self._generate_session_report()

        console.print("[dim]LiveAgent stopped[/dim]")

        return {
            "success": True,
            "monitoring": False,
            "session_report": report
        }

    # =========================================================================
    # ERROR CALLBACKS
    # =========================================================================

    def _on_browser_error(self, error_data: Dict[str, Any]):
        """Handle browser console error from tracker."""
        error_type = error_data.get("type", "error")
        message = error_data.get("message", "Unknown error")
        source = error_data.get("source", "Unknown")
        
        console.print(f"\n[bold red]🔴 Browser Error![/bold red]")
        console.print(f"[red]Type:[/red] {error_type}")
        console.print(f"[red]Message:[/red] {message}")
        console.print(f"[dim]Source: {source}[/dim]\n")
        
        # Track error
        self.errors_detected.append({
            "source": "browser",
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Log to session
        if self.session_logger:
            self.session_logger.log_error(error_data)

    def _on_terminal_error(self, error_data: Dict[str, Any]):
        """Handle terminal error from monitor."""
        error_type = error_data.get("type", "error")
        message = error_data.get("message", "Unknown error")
        file_path = error_data.get("file", "Unknown")
        line = error_data.get("line", "?")
        
        console.print(f"\n[bold red]🔴 Terminal Error![/bold red]")
        console.print(f"[red]{error_type}:[/red] {message}")
        console.print(f"[dim]Location: {file_path}:{line}[/dim]\n")
        
        # Track error
        self.errors_detected.append({
            "source": "terminal",
            "type": error_type,
            "message": message,
            "file": file_path,
            "line": line,
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify if available
        if self.notification_manager:
            self.notification_manager.add_notification(
                priority="high",
                notification_type="terminal_error",
                title=f"Error: {error_type}",
                message=message,
                context={"file": file_path, "line": line}
            )

    def _start_error_server(self):
        """Start HTTP server to receive browser errors."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            agent = self
            
            class ErrorHandler(BaseHTTPRequestHandler):
                def do_POST(self):
                    if self.path in ['/error', '/botuvic/console-error']:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)
                        
                        try:
                            error_data = json.loads(post_data.decode('utf-8'))
                            if agent.browser_tracker:
                                agent.browser_tracker.handle_browser_error(error_data)
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(b'{"success": true}')
                        except Exception:
                            self.send_response(500)
                            self.end_headers()
            else:
                        self.send_response(404)
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
            
            self.error_server_thread = threading.Thread(target=run_server, daemon=True)
            self.error_server_thread.start()
        
        except Exception as e:
            console.print(f"[yellow]⚠ Could not start error server: {e}[/yellow]")

    def _show_activation_message(self):
        """Show activation success message."""
        message = """[bold green]✅ LiveAgent: ACTIVE[/bold green]

I'm now watching your code in real-time:
• [green]✓[/green] File changes → Auto-analyze for issues
• [green]✓[/green] Browser errors → Catch runtime crashes
• [green]✓[/green] Terminal output → Detect build errors
• [green]✓[/green] Code analysis → LLM-powered suggestions

[dim]Commands: 'run tests', 'check deploy', 'fix error', 'status'[/dim]
"""
        console.print(Panel(message, border_style="#A855F7"))

    # =========================================================================
    # CAPABILITY 2: FILE WATCHING
    # =========================================================================

    def _on_file_change(self, file_path: str, event_type: str):
        """Handle file change event with LLM-powered analysis."""
        console.print(f"[dim]📝 {file_path} {event_type}[/dim]")

        # Use CodeAnalyzer if available (LLM-powered)
        if self.code_analyzer:
            try:
                analysis = self.code_analyzer.analyze_file(file_path)
                if analysis.get("success") and analysis.get("issues"):
                    self._handle_code_issues(file_path, analysis)
            except Exception as e:
                console.print(f"[dim]Analysis error: {e}[/dim]")
        else:
            # Fallback to basic analysis
            analysis = self._analyze_file(file_path)
            if analysis.get("errors"):
                for error in analysis["errors"]:
                    self._handle_error(error)
        
        # Log to session
        if self.session_logger:
            self.session_logger.log_file_change(file_path, event_type)

    def _handle_code_issues(self, file_path: str, analysis: Dict[str, Any]):
        """Handle issues detected by CodeAnalyzer."""
        issues = analysis.get("issues", [])
        
        # Filter by severity
        critical = [i for i in issues if i.get("severity") == "critical"]
        high = [i for i in issues if i.get("severity") == "high"]
        
        if critical or high:
            console.print(f"\n[bold yellow]⚠️  Issues in {file_path}:[/bold yellow]\n")
            
            for issue in critical + high:
                color = "red" if issue.get("severity") == "critical" else "yellow"
                console.print(f"[{color}]●[/{color}] Line {issue.get('line', '?')}: {issue.get('message', 'Issue detected')}")
                if issue.get("suggestion"):
                    console.print(f"  [dim]→ {issue['suggestion']}[/dim]")
            
            # Track errors
            self.errors_detected.extend(critical + high)

    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Fallback basic file analysis for potential issues."""
        full_path = os.path.join(self.project_dir, file_path)

        if not os.path.exists(full_path):
            return {"errors": []}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"errors": [{"type": "read_error", "message": str(e)}]}

        errors = []
        ext = Path(file_path).suffix

        if ext in ['.ts', '.tsx', '.js', '.jsx']:
            errors.extend(self._check_javascript_issues(content, file_path))
        elif ext == '.py':
            errors.extend(self._check_python_issues(content, file_path))

        return {"errors": errors, "file": file_path}

    def _check_javascript_issues(self, content: str, file_path: str) -> List[Dict]:
        """Check for common JavaScript/TypeScript issues."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for console.log in production code
            if 'console.log' in line and 'debug' not in file_path.lower():
                issues.append({
                    "type": "warning",
                    "message": "console.log found in production code",
                    "file": file_path,
                    "line": i,
                    "code": line.strip(),
                    "severity": "low"
                })

            # Check for potential null/undefined access
            if re.search(r'\.\w+\s*\(', line) and '?.' not in line:
                # Simplified check - could be more sophisticated
                pass

        return issues

    def _check_python_issues(self, content: str, file_path: str) -> List[Dict]:
        """Check for common Python issues."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for print statements in production
            if re.match(r'^\s*print\(', line):
                issues.append({
                    "type": "warning",
                    "message": "print statement found",
                    "file": file_path,
                    "line": i,
                    "code": line.strip(),
                    "severity": "low"
                })

        return issues

    # =========================================================================
    # CAPABILITY 3: ERROR DETECTION & HANDLING
    # =========================================================================

    def _handle_error(self, error: Dict):
        """Handle a detected error."""
        self.errors_detected.append({
            **error,
            "detected_at": datetime.now().isoformat()
        })

        # Analyze error and suggest fix
        fix = self._analyze_error_and_suggest_fix(error)

        if fix:
            self._show_fix_suggestion(error, fix)

    def _analyze_error_and_suggest_fix(self, error: Dict) -> Optional[Dict]:
        """Analyze error and suggest a fix."""
        error_type = error.get("type", "")
        message = error.get("message", "")
        code = error.get("code", "")

        # Common fix patterns
        fixes = {
            "undefined_access": {
                "pattern": r"Cannot read propert",
                "fix": lambda c: c.replace('.', '?.'),
                "description": "Add optional chaining"
            },
            "console_log": {
                "pattern": r"console\.log",
                "fix": lambda c: "// " + c,
                "description": "Comment out console.log"
            }
        }
        for fix_type, fix_info in fixes.items():
            if re.search(fix_info["pattern"], message) or re.search(fix_info["pattern"], code):
            return {
                    "type": fix_type,
                    "description": fix_info["description"],
                    "original": code,
                    "fixed": fix_info["fix"](code)
                }

        return None

    def _show_fix_suggestion(self, error: Dict, fix: Dict):
        """Show fix suggestion to user (through MainAgent)."""
        file_path = error.get("file", "unknown")
        line = error.get("line", 0)

        console.print(Panel(
            f"[bold red]Error detected[/bold red]\n\n"
            f"File: {file_path}:{line}\n"
            f"Issue: {error.get('message', 'Unknown')}\n\n"
            f"[dim]Original:[/dim] {fix.get('original', '')}\n"
            f"[dim]Suggested:[/dim] {fix.get('fixed', '')}\n\n"
            f"[dim]{fix.get('description', '')}[/dim]",
            title="LiveAgent",
            border_style="red"
        ))

    # =========================================================================
    # CAPABILITY 4: APPLY FIXES
    # =========================================================================

    def apply_fix(
        self,
        file_path: str,
        line: int,
        original: str,
        fixed: str
    ) -> Dict[str, Any]:
        """
        Apply a fix to a file with permission.
        
        Args:
            file_path: Path to file
            line: Line number
            original: Original code
            fixed: Fixed code
            
        Returns:
            Result dict
        """
        full_path = os.path.join(self.project_dir, file_path)

        # Request permission
        result = self.tools.permission.request_file_permission(
            action="modify",
            file_path=file_path,
            diff=f"- {original}\n+ {fixed}"
        )

        if not result["approved"]:
            return {"success": False, "skipped": True, "reason": result["action"]}

        try:
            # Create backup
            self._create_backup(full_path)

            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Apply fix
            if 0 < line <= len(lines):
                lines[line - 1] = lines[line - 1].replace(original, fixed)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # Track fix
            self.fixes_applied.append({
                "file": file_path,
                "line": line,
                "original": original,
                "fixed": fixed,
                "applied_at": datetime.now().isoformat()
            })

            console.print(f"[green]✓[/green] Fix applied to {file_path}:{line}")

            return {"success": True, "file": file_path, "line": line}
        
        except Exception as e:
            console.print(f"[red]✗ Error applying fix: {e}[/red]")
            return {"success": False, "error": str(e)}

    def _create_backup(self, file_path: str) -> str:
        """Create backup before modification."""
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{filename}.{timestamp}")

        import shutil
        shutil.copy2(file_path, backup_path)

        return backup_path

    # =========================================================================
    # CAPABILITY 5: TERMINAL MONITORING
    # =========================================================================

    def parse_terminal_output(self, output: str) -> List[Dict]:
        """Parse terminal output for errors."""
        errors = []

        # Error patterns
        patterns = [
            {
                "pattern": r"SyntaxError:(.+)",
                "type": "SyntaxError",
                "severity": "critical"
            },
            {
                "pattern": r"TypeError:(.+)",
                "type": "TypeError",
                "severity": "critical"
            },
            {
                "pattern": r"ReferenceError:(.+)",
                "type": "ReferenceError",
                "severity": "critical"
            },
            {
                "pattern": r"Module not found:(.+)",
                "type": "ModuleNotFound",
                "severity": "critical"
            },
            {
                "pattern": r"TS\d+:(.+)",
                "type": "TypeScriptError",
                "severity": "high"
            },
            {
                "pattern": r"error:(.+)",
                "type": "Error",
                "severity": "medium"
            }
        ]

        for p in patterns:
            matches = re.findall(p["pattern"], output, re.IGNORECASE)
            for match in matches:
                errors.append({
                    "type": p["type"],
                    "message": match.strip(),
                    "severity": p["severity"]
                })

        return errors

    # =========================================================================
    # CAPABILITY 6: RUN TESTS
    # =========================================================================

    def run_tests(self, test_command: str = None) -> Dict[str, Any]:
        """
        Run tests with permission.

        Args:
            test_command: Optional custom test command

        Returns:
            Test results dict
        """
        # Detect test framework
        if not test_command:
            test_command = self._detect_test_command()

        if not test_command:
            return {"success": False, "error": "No test framework detected"}

        # Request permission
        result = self.tools.permission.request_terminal_permission(
            command=test_command,
            description="Run project tests",
            risk_level="low"
        )

        if not result["approved"]:
            return {"success": False, "skipped": True, "reason": result["action"]}

        console.print(f"[dim]Running tests: {test_command}[/dim]")

        # Execute tests
        try:
            proc = subprocess.run(
                test_command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse test results
            test_results = self._parse_test_results(proc.stdout, proc.stderr)

            self.tests_run.append({
                "command": test_command,
                "results": test_results,
                "run_at": datetime.now().isoformat()
            })

            # Display results
            self._display_test_results(test_results)
        
        return {
                "success": proc.returncode == 0,
                "results": test_results,
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out after 5 minutes"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _detect_test_command(self) -> Optional[str]:
        """Detect the appropriate test command."""
        # Check for common test configurations
        checks = [
            ("frontend/package.json", "npm test"),
            ("package.json", "npm test"),
            ("pytest.ini", "pytest"),
            ("setup.py", "python -m pytest"),
        ]

        for config_file, command in checks:
            if os.path.exists(os.path.join(self.project_dir, config_file)):
                return command

        return None

    def _parse_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse test output for results."""
        output = stdout + stderr

        # Try to extract pass/fail counts
        passed = 0
        failed = 0

        # Jest/Vitest pattern
        jest_match = re.search(r'(\d+) passed', output)
        if jest_match:
            passed = int(jest_match.group(1))

        jest_fail = re.search(r'(\d+) failed', output)
        if jest_fail:
            failed = int(jest_fail.group(1))

        # Pytest pattern
        pytest_match = re.search(r'(\d+) passed', output)
        if pytest_match:
            passed = int(pytest_match.group(1))

        pytest_fail = re.search(r'(\d+) failed', output)
        if pytest_fail:
            failed = int(pytest_fail.group(1))
            
            return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "success": failed == 0
        }

    def _display_test_results(self, results: Dict):
        """Display test results."""
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        total = results.get("total", 0)

        if failed == 0:
            console.print(f"[green]✓ Tests passed: {passed}/{total}[/green]")
        else:
            console.print(f"[red]✗ Tests: {passed} passed, {failed} failed[/red]")

    # =========================================================================
    # CAPABILITY 7: SEARCH ONLINE
    # =========================================================================

    def search_for_solution(self, error_message: str) -> Dict[str, Any]:
        """Search online for error solutions."""
        if not self.tools.search_engine:
            return {"error": "No search engine configured"}

        # Clean error message for search
        query = f"{error_message} solution"

        results = self.tools.search_online(query, max_results=3)

        if results.get("results"):
            console.print("\n[cyan]Possible solutions found:[/cyan]")
            for i, r in enumerate(results["results"][:3], 1):
                console.print(f"  {i}. {r.get('title', 'No title')}")
                console.print(f"     [dim]{r.get('url', '')}[/dim]")

        return results

    # =========================================================================
    # CAPABILITY 8: DEPLOYMENT CHECK
    # =========================================================================

    def check_deployment_readiness(self) -> Dict[str, Any]:
        """Check if project is ready for deployment."""
        console.print("\n[cyan]Checking deployment readiness...[/cyan]")

        checks = {}

        # Check for console.log/print statements
        checks["no_debug_logs"] = self._check_no_debug_logs()

        # Check for hardcoded secrets
        checks["no_secrets"] = self._check_no_secrets()

        # Check for env.example
        checks["env_documented"] = os.path.exists(
            os.path.join(self.project_dir, ".env.example")
        )

        # Check git status
        checks["git_clean"] = self._check_git_clean()

        # Calculate score
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = int((passed / total) * 100)

        ready = score >= 80

        # Display results
        console.print(Panel(
            "\n".join([
                f"{'✓' if v else '✗'} {k.replace('_', ' ').title()}"
                for k, v in checks.items()
            ]) + f"\n\nScore: {score}/100 - {'READY' if ready else 'NOT READY'}",
            title="Deployment Readiness",
            border_style="green" if ready else "red"
        ))
        
            return {
            "checks": checks,
            "score": score,
            "ready": ready
        }

    def _check_no_debug_logs(self) -> bool:
        """Check for console.log/print in production code."""
        # Simplified check
        result = subprocess.run(
            "grep -r 'console.log' frontend/src --include='*.ts' --include='*.tsx' 2>/dev/null | wc -l",
            shell=True,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip() or 0)
        return count == 0

    def _check_no_secrets(self) -> bool:
        """Check for hardcoded secrets."""
        # Look for common secret patterns
        result = subprocess.run(
            "grep -rE '(api_key|apikey|secret|password)\\s*=\\s*[\"\\'][^\"\\']' . --include='*.ts' --include='*.js' --exclude-dir=node_modules 2>/dev/null | wc -l",
            shell=True,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip() or 0)
        return count == 0

    def _check_git_clean(self) -> bool:
        """Check if git working tree is clean."""
        result = subprocess.run(
            "git status --porcelain 2>/dev/null",
            shell=True,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) == 0

    # =========================================================================
    # CAPABILITY 9: SESSION REPORT
    # =========================================================================

    def _generate_session_report(self) -> Dict[str, Any]:
        """Generate session report."""
        if not self.session_start:
            return {}

        duration = datetime.now() - self.session_start
        duration_str = str(duration).split('.')[0]

        report = {
            "duration": duration_str,
            "errors": {
                "detected": len(self.errors_detected),
                "fixed": len(self.fixes_applied)
            },
            "tests": {
                "runs": len(self.tests_run),
                "results": self.tests_run
            },
            "fixes": self.fixes_applied
        }

        # Save report
        self.storage.save("live_session_report", report)
        
        return report
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring": self.is_monitoring,
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "errors_detected": len(self.errors_detected),
            "fixes_applied": len(self.fixes_applied),
            "tests_run": len(self.tests_run)
        }

    # =========================================================================
    # COMMAND HANDLER (Called by MainAgent)
    # =========================================================================

    def handle_command(self, command: str) -> Dict[str, Any]:
        """
        Handle command from MainAgent.

        Args:
            command: User command

        Returns:
            Response dict
        """
        cmd_lower = command.lower()

        if "test" in cmd_lower:
            result = self.run_tests()
            return {
                "message": f"Test results: {result.get('results', {})}",
                "status": "complete" if result.get("success") else "error"
            }
        
        elif "deploy" in cmd_lower or "ready" in cmd_lower:
            result = self.check_deployment_readiness()
            return {
                "message": f"Deployment readiness: {result.get('score')}%",
                "status": "complete"
            }

        elif "fix" in cmd_lower:
            if self.errors_detected:
                error = self.errors_detected[-1]
                fix = self._analyze_error_and_suggest_fix(error)
                if fix:
                    return {
                        "message": f"Suggested fix: {fix.get('description')}\n{fix.get('original')} -> {fix.get('fixed')}",
                        "status": "awaiting_confirmation"
                    }
            return {
                "message": "No errors to fix",
                "status": "complete"
            }

        elif "status" in cmd_lower or "report" in cmd_lower:
            status = self.get_status()
            return {
                "message": f"LiveAgent Status:\n"
                          f"- Monitoring: {'Yes' if status['monitoring'] else 'No'}\n"
                          f"- Errors detected: {status['errors_detected']}\n"
                          f"- Fixes applied: {status['fixes_applied']}\n"
                          f"- Tests run: {status['tests_run']}",
                "status": "complete"
            }

        else:
            return {
                "message": "LiveAgent commands: 'run tests', 'check deploy', 'fix error', 'status'",
                "status": "info"
            }

    # =========================================================================
    # BACKWARD COMPATIBILITY
    # =========================================================================

    def chat(self, user_message: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """Backward compatible chat interface."""
        return self.handle_command(user_message)

    def activate(self) -> Dict[str, Any]:
        """Activate live monitoring."""
        return self.start_monitoring()
    
    def deactivate(self) -> Dict[str, Any]:
        """Deactivate live monitoring."""
        return self.stop_monitoring()

    def reset(self):
        """Reset agent state."""
        self.errors_detected = []
        self.fixes_applied = []
        self.tests_run = []
        if self.is_monitoring:
            self.stop_monitoring()
        console.print("[dim]LiveAgent reset[/dim]")

    def get_output(self) -> Dict[str, Any]:
        """Get agent output for MainAgent."""
        return {
            "agent_name": "LiveAgent",
            "data": {
                "errors_count": len(self.errors_detected),
                "fixes_applied": len(self.fixes_applied),
                "tests_run": len(self.tests_run),
                "monitoring": self.is_monitoring
            }
        }
