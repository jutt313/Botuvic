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
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..tools import AgentTools
from ..live_mode.file_watcher import FileWatcher

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
        Initialize LiveAgent.
        
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
        self.file_watcher = None
        self.error_server = None

        # Tracking
        self.errors_detected = []
        self.fixes_applied = []
        self.tests_run = []
        self.session_start = None

        # Backup directory
        self.backup_dir = os.path.join(project_dir, ".botuvic", "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        # System prompt is embedded in class (no file loading needed)
        # SYSTEM_PROMPT is defined as class variable

    # =========================================================================
    # CAPABILITY 1: START/STOP MONITORING
    # =========================================================================

    def start_monitoring(self) -> Dict[str, Any]:
        """Start all monitoring capabilities."""
        if self.is_monitoring:
            return {"success": False, "error": "Already monitoring"}

        console.print("\n[cyan]LiveAgent: Starting monitoring...[/cyan]")

        self.session_start = datetime.now()
        self.is_monitoring = True

        # Start file watcher
        self.file_watcher = FileWatcher(
            project_dir=self.project_dir,
            on_change_callback=self._on_file_change
        )
        watcher_result = self.file_watcher.start()

        console.print("[green]✓[/green] LiveAgent is now monitoring your project")

        return {
            "success": True,
            "monitoring": True,
            "file_watcher": watcher_result
        }

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
    # CAPABILITY 2: FILE WATCHING
    # =========================================================================

    def _on_file_change(self, file_path: str, event_type: str):
        """Handle file change event."""
        console.print(f"[dim]File {event_type}: {file_path}[/dim]")

        # Analyze the changed file
        analysis = self._analyze_file(file_path)

        if analysis.get("errors"):
            for error in analysis["errors"]:
                self._handle_error(error)

    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file for potential issues."""
        full_path = os.path.join(self.project_dir, file_path)

        if not os.path.exists(full_path):
            return {"errors": []}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"errors": [{"type": "read_error", "message": str(e)}]}

        errors = []

        # Check for common issues based on file type
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
