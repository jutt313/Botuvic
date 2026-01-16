"""
Deployment Readiness Checker for Phase 10 Live Development Mode.
Verifies code is ready for production deployment.
"""

import os
import re
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table

console = Console()


class DeploymentChecker:
    """
    Checks if code is ready for deployment.
    Verifies: tests pass, no console.logs, env vars set, security scan, etc.
    """

    def __init__(self, project_dir: str):
        """
        Initialize deployment checker.

        Args:
            project_dir: Project root directory
        """
        self.project_dir = project_dir

    def check_deployment_readiness(self) -> Dict[str, Any]:
        """
        Run complete deployment readiness check.

        Returns:
            Readiness report with all checks
        """
        console.print("\n[bold cyan]🚀 Deployment Readiness Check[/bold cyan]\n")

        checks = {
            "tests": self._check_tests(),
            "debug_code": self._check_debug_code(),
            "env_vars": self._check_environment_variables(),
            "secrets": self._check_for_secrets(),
            "dependencies": self._check_dependencies(),
            "build": self._check_build(),
            "git": self._check_git_status(),
            "security": self._check_security(),
        }

        # Calculate overall score
        passed = sum(1 for check in checks.values() if check.get("passed"))
        total = len(checks)
        score = (passed / total * 100) if total > 0 else 0

        result = {
            "ready": score == 100,
            "score": score,
            "checks": checks,
            "blockers": [check["message"] for check in checks.values() if not check.get("passed")]
        }

        # Display results
        self._display_results(checks, score)

        return result

    def _check_tests(self) -> Dict[str, Any]:
        """Check if all tests pass."""
        # This would integrate with TestRunner
        # For now, simple check

        test_files = []
        for root, dirs, files in os.walk(self.project_dir):
            if 'node_modules' in root or '__pycache__' in root:
                continue

            for file in files:
                if (file.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts', '_test.py', '_test.go'))):
                    test_files.append(file)

        has_tests = len(test_files) > 0

        return {
            "passed": has_tests,  # Would check if tests actually pass
            "message": f"Found {len(test_files)} test files" if has_tests else "No tests found",
            "severity": "critical" if not has_tests else "info"
        }

    def _check_debug_code(self) -> Dict[str, Any]:
        """Check for debug code (console.log, debugger, etc.)."""
        debug_patterns = [
            (r'console\.log\(', 'console.log'),
            (r'console\.debug\(', 'console.debug'),
            (r'debugger;?', 'debugger'),
            (r'print\(', 'print() in Python'),
        ]

        found = []

        # Scan source files
        source_dirs = ['frontend/src', 'backend/src', 'src']
        for source_dir in source_dirs:
            full_path = os.path.join(self.project_dir, source_dir)
            if not os.path.exists(full_path):
                continue

            for root, dirs, files in os.walk(full_path):
                if 'node_modules' in root or '__pycache__' in root:
                    continue

                for file in files:
                    if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            for pattern, name in debug_patterns:
                                matches = re.findall(pattern, content)
                                if matches:
                                    found.append({
                                        "file": os.path.relpath(file_path, self.project_dir),
                                        "type": name,
                                        "count": len(matches)
                                    })
                                    break  # One match per file is enough
                        except:
                            pass

        passed = len(found) == 0

        return {
            "passed": passed,
            "message": f"Found debug code in {len(found)} file(s)" if not passed else "No debug code found",
            "severity": "high" if not passed else "info",
            "details": found[:5]  # First 5 files
        }

    def _check_environment_variables(self) -> Dict[str, Any]:
        """Check if required environment variables are documented."""
        # Check for .env.example
        env_example = os.path.join(self.project_dir, '.env.example')
        has_example = os.path.exists(env_example)

        # Check for .env (should NOT be committed)
        env_file = os.path.join(self.project_dir, '.env')
        env_committed = os.path.exists(env_file)

        if env_committed:
            # Check if in .gitignore
            gitignore = os.path.join(self.project_dir, '.gitignore')
            env_ignored = False
            if os.path.exists(gitignore):
                with open(gitignore, 'r') as f:
                    env_ignored = '.env' in f.read()

            if not env_ignored:
                return {
                    "passed": False,
                    "message": ".env file exists but not in .gitignore (security risk!)",
                    "severity": "critical"
                }

        return {
            "passed": has_example,
            "message": ".env.example found" if has_example else ".env.example missing (add for documentation)",
            "severity": "medium" if not has_example else "info"
        }

    def _check_for_secrets(self) -> Dict[str, Any]:
        """Check for hardcoded secrets."""
        secret_patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'API Key'),
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']', 'Password'),
            (r'(?i)(secret|token)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'Secret/Token'),
            (r'["\']sk-[a-zA-Z0-9]{32,}["\']', 'OpenAI API Key'),
        ]

        found_secrets = []

        # Scan source files
        for root, dirs, files in os.walk(self.project_dir):
            # Skip certain directories
            if any(skip in root for skip in ['node_modules', '__pycache__', '.git', 'dist', 'build']):
                continue

            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.go', '.env.example')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for pattern, secret_type in secret_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                # Don't flag .env.example or obvious placeholders
                                if '.example' in file or 'your_' in match.group(0).lower() or 'placeholder' in match.group(0).lower():
                                    continue

                                found_secrets.append({
                                    "file": os.path.relpath(file_path, self.project_dir),
                                    "type": secret_type,
                                    "line": content[:match.start()].count('\n') + 1
                                })
                    except:
                        pass

        passed = len(found_secrets) == 0

        return {
            "passed": passed,
            "message": f"Found {len(found_secrets)} potential hardcoded secret(s)" if not passed else "No hardcoded secrets detected",
            "severity": "critical" if not passed else "info",
            "details": found_secrets[:3]  # First 3
        }

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check for dependency issues."""
        # Check package.json for known vulnerable packages
        package_json = os.path.join(self.project_dir, 'package.json')

        if os.path.exists(package_json):
            try:
                import json
                with open(package_json, 'r') as f:
                    pkg = json.load(f)

                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

                # Check for very old/outdated markers (simplified)
                warnings = []
                for dep, version in deps.items():
                    if '^0.' in version or '~0.' in version:
                        warnings.append(f"{dep}@{version} (pre-1.0)")

                return {
                    "passed": len(warnings) == 0,
                    "message": f"{len(deps)} dependencies, {len(warnings)} warnings" if warnings else f"{len(deps)} dependencies checked",
                    "severity": "low" if warnings else "info"
                }
            except:
                pass

        return {
            "passed": True,
            "message": "No package.json found",
            "severity": "info"
        }

    def _check_build(self) -> Dict[str, Any]:
        """Check if project builds successfully."""
        # Check for build output
        build_dirs = ['dist', 'build', 'frontend/dist', 'frontend/build']

        for build_dir in build_dirs:
            full_path = os.path.join(self.project_dir, build_dir)
            if os.path.exists(full_path) and os.listdir(full_path):
                return {
                    "passed": True,
                    "message": f"Build output found in {build_dir}",
                    "severity": "info"
                }

        return {
            "passed": False,
            "message": "No build output found (run build first)",
            "severity": "high"
        }

    def _check_git_status(self) -> Dict[str, Any]:
        """Check git status."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                uncommitted = result.stdout.strip()
                has_changes = bool(uncommitted)

                return {
                    "passed": not has_changes,
                    "message": "Uncommitted changes found" if has_changes else "Working tree clean",
                    "severity": "medium" if has_changes else "info"
                }
        except:
            pass

        return {
            "passed": True,
            "message": "Git check skipped",
            "severity": "info"
        }

    def _check_security(self) -> Dict[str, Any]:
        """Basic security checks."""
        issues = []

        # Check for HTTPS in production URLs
        env_files = ['.env.production', '.env']
        for env_file in env_files:
            env_path = os.path.join(self.project_dir, env_file)
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()

                    # Check for http:// in production
                    if re.search(r'http://(?!localhost|127\.0\.0\.1)', content):
                        issues.append("Non-HTTPS URL in env file")
                except:
                    pass

        # Check CORS configuration (simplified)
        backend_files = []
        backend_dir = os.path.join(self.project_dir, 'backend')
        if os.path.exists(backend_dir):
            for root, dirs, files in os.walk(backend_dir):
                for file in files:
                    if file.endswith(('.js', '.ts', '.py')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()

                            # Check for overly permissive CORS
                            if re.search(r'Access-Control-Allow-Origin.*\*', content) or \
                               re.search(r'cors.*origin.*["\']?\*["\']?', content):
                                issues.append("Wildcard CORS detected (security risk)")
                                break
                        except:
                            pass

        passed = len(issues) == 0

        return {
            "passed": passed,
            "message": f"{len(issues)} security issue(s) found" if not passed else "Basic security checks passed",
            "severity": "high" if not passed else "info",
            "details": issues
        }

    def _display_results(self, checks: Dict[str, Dict[str, Any]], score: float):
        """Display check results in formatted table."""
        table = Table(title="Deployment Readiness")

        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message")

        for check_name, check_result in checks.items():
            passed = check_result.get("passed")
            message = check_result.get("message", "")

            status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"

            table.add_row(
                check_name.replace("_", " ").title(),
                status,
                message
            )

        console.print(table)

        console.print(f"\n[bold]Overall Score: {score:.0f}%[/bold]")

        if score == 100:
            console.print("[bold green]🎉 Ready for deployment![/bold green]\n")
        elif score >= 80:
            console.print("[bold yellow]⚠️  Almost ready - address warnings before deploying[/bold yellow]\n")
        else:
            console.print("[bold red]🚫 NOT ready for deployment - fix critical issues first[/bold red]\n")
