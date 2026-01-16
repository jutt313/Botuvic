"""
Test Runner Integration for Phase 10 Live Development Mode.
Automatically runs tests and reports results.
"""

import os
import re
import subprocess
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from rich.console import Console

console = Console()


class TestRunner:
    """
    Integrates with test frameworks to run tests automatically.
    Supports: Jest, Pytest, JUnit, Go test, and more.
    """

    def __init__(self, project_dir: str, on_result_callback: Optional[Callable] = None):
        """
        Initialize test runner.

        Args:
            project_dir: Project root directory
            on_result_callback: Callback for test results
        """
        self.project_dir = project_dir
        self.on_result_callback = on_result_callback
        self.test_history = []

        # Auto-detect test framework
        self.test_framework = self._detect_test_framework()

    def run_tests(self, scope: str = "all") -> Dict[str, Any]:
        """
        Run tests.

        Args:
            scope: Test scope (all, changed, failed, file:<path>)

        Returns:
            Test results
        """
        if not self.test_framework:
            return {"success": False, "error": "No test framework detected"}

        console.print(f"[cyan]Running tests ({self.test_framework})...[/cyan]")

        try:
            # Build command
            command = self._build_test_command(scope)

            # Run tests
            result = subprocess.run(
                command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse results
            test_results = self._parse_test_output(result.stdout, result.stderr, result.returncode)

            # Add to history
            test_record = {
                **test_results,
                "scope": scope,
                "timestamp": datetime.now().isoformat()
            }
            self.test_history.append(test_record)

            # Keep only last 50
            if len(self.test_history) > 50:
                self.test_history = self.test_history[-50:]

            # Display results
            self._display_results(test_results)

            # Callback
            if self.on_result_callback:
                self.on_result_callback(test_results)

            return test_results

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out (>5 minutes)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_after_fix(self, fixed_file: str) -> Dict[str, Any]:
        """
        Run tests related to a fixed file.

        Args:
            fixed_file: Path to fixed file

        Returns:
            Test results
        """
        # Find related test file
        test_file = self._find_test_file(fixed_file)

        if test_file:
            return self.run_tests(scope=f"file:{test_file}")
        else:
            # Run all tests if can't find specific test
            console.print("[dim]No specific test file found, running all tests[/dim]")
            return self.run_tests(scope="all")

    def _detect_test_framework(self) -> Optional[str]:
        """Auto-detect test framework from project files."""
        # Check for package.json (Jest, Mocha, etc.)
        package_json = os.path.join(self.project_dir, 'package.json')
        if os.path.exists(package_json):
            try:
                import json
                with open(package_json, 'r') as f:
                    pkg = json.load(f)

                scripts = pkg.get('scripts', {})
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

                if 'jest' in deps or 'test' in scripts and 'jest' in scripts.get('test', ''):
                    return "jest"
                elif 'mocha' in deps:
                    return "mocha"
                elif 'vitest' in deps:
                    return "vitest"
            except:
                pass

        # Check for pytest (Python)
        if os.path.exists(os.path.join(self.project_dir, 'pytest.ini')) or \
           os.path.exists(os.path.join(self.project_dir, 'setup.cfg')) or \
           os.path.exists(os.path.join(self.project_dir, 'pyproject.toml')):
            return "pytest"

        # Check for Go
        for root, dirs, files in os.walk(self.project_dir):
            if any(f.endswith('_test.go') for f in files):
                return "go_test"
            break

        # Check for Maven/Gradle (Java)
        if os.path.exists(os.path.join(self.project_dir, 'pom.xml')):
            return "maven"
        if os.path.exists(os.path.join(self.project_dir, 'build.gradle')):
            return "gradle"

        return None

    def _build_test_command(self, scope: str) -> List[str]:
        """Build test command based on framework and scope."""
        if self.test_framework == "jest":
            cmd = ["npm", "test", "--", "--passWithNoTests"]
            if scope == "changed":
                cmd.append("--onlyChanged")
            elif scope == "failed":
                cmd.append("--onlyFailures")
            elif scope.startswith("file:"):
                cmd.append(scope[5:])
            return cmd

        elif self.test_framework == "vitest":
            cmd = ["npx", "vitest", "run"]
            if scope.startswith("file:"):
                cmd.append(scope[5:])
            return cmd

        elif self.test_framework == "pytest":
            cmd = ["pytest", "-v"]
            if scope.startswith("file:"):
                cmd.append(scope[5:])
            return cmd

        elif self.test_framework == "go_test":
            cmd = ["go", "test", "./..."]
            if scope.startswith("file:"):
                cmd = ["go", "test", scope[5:]]
            return cmd

        elif self.test_framework == "maven":
            return ["mvn", "test"]

        elif self.test_framework == "gradle":
            return ["./gradlew", "test"]

        else:
            return ["echo", "No test command configured"]

    def _parse_test_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse test output to extract results."""
        results = {
            "success": returncode == 0,
            "framework": self.test_framework,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0,
            "failed_tests": [],
            "output": stdout
        }

        if self.test_framework == "jest" or self.test_framework == "vitest":
            # Parse Jest/Vitest output
            # Example: "Tests: 2 failed, 8 passed, 10 total"
            match = re.search(r'Tests:\s+(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed,?\s*)?(\d+)\s+total', stdout)
            if match:
                results["failed"] = int(match.group(1) or 0)
                results["passed"] = int(match.group(2) or 0)
                results["total"] = int(match.group(3))

            # Extract failed test names
            failed_pattern = r'● (.+?) › (.+)'
            for match in re.finditer(failed_pattern, stdout):
                results["failed_tests"].append({
                    "suite": match.group(1),
                    "name": match.group(2)
                })

        elif self.test_framework == "pytest":
            # Parse Pytest output
            # Example: "5 passed, 2 failed in 1.23s"
            match = re.search(r'(\d+)\s+passed(?:,\s+(\d+)\s+failed)?', stdout)
            if match:
                results["passed"] = int(match.group(1))
                results["failed"] = int(match.group(2) or 0)
                results["total"] = results["passed"] + results["failed"]

            # Extract failed tests
            failed_pattern = r'FAILED (.+?) - '
            for match in re.finditer(failed_pattern, stdout):
                results["failed_tests"].append({
                    "name": match.group(1)
                })

        elif self.test_framework == "go_test":
            # Parse Go test output
            # Count PASS and FAIL
            results["passed"] = len(re.findall(r'^PASS', stdout, re.MULTILINE))
            results["failed"] = len(re.findall(r'^FAIL', stdout, re.MULTILINE))
            results["total"] = results["passed"] + results["failed"]

        # If no specific parsing worked, try to infer from returncode
        if results["total"] == 0:
            if returncode == 0:
                results["success"] = True
                results["passed"] = 1  # At least something passed
                results["total"] = 1
            else:
                results["success"] = False
                results["failed"] = 1
                results["total"] = 1

        return results

    def _display_results(self, results: Dict[str, Any]):
        """Display test results to console."""
        total = results["total"]
        passed = results["passed"]
        failed = results["failed"]

        if results["success"]:
            console.print(f"[green]✓ All tests passed ({passed}/{total})[/green]")
        else:
            console.print(f"[red]✗ {failed} test(s) failed ({passed}/{total} passed)[/red]")

            # Show failed tests
            if results["failed_tests"]:
                console.print("\n[bold red]Failed tests:[/bold red]")
                for test in results["failed_tests"][:5]:  # Show first 5
                    name = test.get("name", "unknown")
                    suite = test.get("suite")
                    if suite:
                        console.print(f"  • {suite} › {name}")
                    else:
                        console.print(f"  • {name}")

                if len(results["failed_tests"]) > 5:
                    remaining = len(results["failed_tests"]) - 5
                    console.print(f"  ... and {remaining} more")

    def _find_test_file(self, source_file: str) -> Optional[str]:
        """Find test file for a source file."""
        # Remove project_dir prefix if present
        if source_file.startswith(self.project_dir):
            source_file = os.path.relpath(source_file, self.project_dir)

        base_name = os.path.splitext(source_file)[0]
        dir_name = os.path.dirname(source_file)

        # Common test file patterns
        patterns = [
            f"{base_name}.test.js",
            f"{base_name}.test.ts",
            f"{base_name}.spec.js",
            f"{base_name}.spec.ts",
            f"test_{os.path.basename(base_name)}.py",
            f"{base_name}_test.py",
            f"{os.path.basename(base_name)}_test.go",
        ]

        # Check same directory
        for pattern in patterns:
            test_path = os.path.join(self.project_dir, dir_name, pattern)
            if os.path.exists(test_path):
                return os.path.relpath(test_path, self.project_dir)

        # Check __tests__ or tests directory
        test_dirs = ["__tests__", "tests", "test"]
        for test_dir in test_dirs:
            test_path = os.path.join(self.project_dir, dir_name, test_dir)
            if os.path.exists(test_path):
                for pattern in patterns:
                    full_path = os.path.join(test_path, pattern)
                    if os.path.exists(full_path):
                        return os.path.relpath(full_path, self.project_dir)

        return None

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get test run history."""
        return self.test_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get test statistics."""
        if not self.test_history:
            return {"total_runs": 0}

        recent = self.test_history[-10:]

        total_runs = len(recent)
        successful_runs = sum(1 for r in recent if r.get("success"))
        total_tests = sum(r.get("total", 0) for r in recent)
        total_passed = sum(r.get("passed", 0) for r in recent)
        total_failed = sum(r.get("failed", 0) for r in recent)

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
