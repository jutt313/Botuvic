"""
AI-Powered Test Generator for BOTUVIC LiveAgent.
Scans code, generates tests for endpoints and functions automatically.
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()


class TestGenerator:
    """
    Generate tests automatically using LLM.
    Scans code for endpoints and functions, generates test code.
    """

    def __init__(self, project_dir: str, llm_client, storage=None):
        """
        Initialize test generator.
        
        Args:
            project_dir: Project root directory
            llm_client: LLM client for test generation
            storage: Storage for caching
        """
        self.project_dir = project_dir
        self.llm = llm_client
        self.storage = storage
        
        # Patterns for detecting testable code
        self.endpoint_patterns = {
            "fastapi": r'@(app|router)\.(get|post|put|patch|delete)\([\'"]([^\'"]+)[\'"]\)',
            "express": r'(app|router)\.(get|post|put|patch|delete)\([\'"]([^\'"]+)[\'"]\s*,',
            "nextjs": r'export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\s*\(',
        }
        
        self.function_patterns = {
            "python": r'^(?:async\s+)?def\s+(\w+)\s*\([^)]*\)',
            "javascript": r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)',
            "typescript": r'(?:export\s+)?(?:async\s+)?function\s+(\w+)[<\(][^)>]*[>\)]',
        }

    def scan_endpoints(self) -> List[Dict[str, Any]]:
        """
        Scan project for API endpoints.
        
        Returns:
            List of endpoint dicts with path, method, file
        """
        endpoints = []
        
        # Scan backend directory
        backend_dirs = ["backend", "api", "src/app/api", "app/api", "pages/api"]
        
        for dir_name in backend_dirs:
            dir_path = os.path.join(self.project_dir, dir_name)
            if os.path.exists(dir_path):
                endpoints.extend(self._scan_directory_for_endpoints(dir_path))
        
        console.print(f"[dim]Found {len(endpoints)} endpoints[/dim]")
        return endpoints

    def _scan_directory_for_endpoints(self, dir_path: str) -> List[Dict[str, Any]]:
        """Scan a directory for API endpoints."""
        endpoints = []
        
        for root, dirs, files in os.walk(dir_path):
            # Skip common ignored directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.ts', '.js', '.tsx', '.jsx')):
                    file_path = os.path.join(root, file)
                    endpoints.extend(self._extract_endpoints_from_file(file_path))
        
        return endpoints

    def _extract_endpoints_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract endpoints from a file."""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []
        
        rel_path = os.path.relpath(file_path, self.project_dir)
        
        # Check each pattern
        for framework, pattern in self.endpoint_patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE)
            
            for match in matches:
                if framework in ["fastapi", "express"]:
                    method = match[1].upper() if len(match) > 1 else "GET"
                    path = match[2] if len(match) > 2 else match[0]
                else:  # nextjs
                    method = match[1] if match[1] else "GET"
                    path = self._infer_nextjs_path(rel_path)
                
                endpoints.append({
                    "file": rel_path,
                    "framework": framework,
                    "method": method,
                    "path": path
                })
        
        return endpoints

    def _infer_nextjs_path(self, file_path: str) -> str:
        """Infer API route from Next.js file path."""
        # Convert app/api/users/route.ts -> /api/users
        path = file_path.replace("\\", "/")
        if "app/api/" in path:
            api_path = path.split("app/api/")[1]
            api_path = api_path.replace("/route.ts", "").replace("/route.js", "")
            return f"/api/{api_path}"
        elif "pages/api/" in path:
            api_path = path.split("pages/api/")[1]
            api_path = api_path.replace(".ts", "").replace(".js", "")
            return f"/api/{api_path}"
        return "/api/unknown"

    def scan_functions(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan for functions that need tests.
        
        Args:
            file_path: Optional specific file to scan
            
        Returns:
            List of function dicts
        """
        functions = []
        
        if file_path:
            full_path = os.path.join(self.project_dir, file_path)
            if os.path.exists(full_path):
                functions.extend(self._extract_functions_from_file(full_path))
        else:
            # Scan common source directories
            src_dirs = ["frontend/src", "backend/src", "src", "lib", "utils"]
            for dir_name in src_dirs:
                dir_path = os.path.join(self.project_dir, dir_name)
                if os.path.exists(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git']]
                        for file in files:
                            if file.endswith(('.py', '.ts', '.js', '.tsx', '.jsx')):
                                file_path = os.path.join(root, file)
                                functions.extend(self._extract_functions_from_file(file_path))
        
        # Filter out obvious non-testable functions
        functions = [f for f in functions if not f["name"].startswith("_")]
        
        console.print(f"[dim]Found {len(functions)} testable functions[/dim]")
        return functions

    def _extract_functions_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract function definitions from a file."""
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []
        
        rel_path = os.path.relpath(file_path, self.project_dir)
        ext = Path(file_path).suffix
        
        # Select pattern based on extension
        if ext == '.py':
            pattern = self.function_patterns["python"]
        elif ext in ['.ts', '.tsx']:
            pattern = self.function_patterns["typescript"]
        else:
            pattern = self.function_patterns["javascript"]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                functions.append({
                    "file": rel_path,
                    "name": func_name,
                    "line": i,
                    "is_async": "async" in line
                })
        
        return functions

    def generate_endpoint_tests(self, endpoints: List[Dict[str, Any]]) -> str:
        """
        Use LLM to generate API endpoint tests.
        
        Args:
            endpoints: List of endpoint dicts
            
        Returns:
            Generated test code
        """
        if not endpoints:
            return ""
        
        # Build prompt
        endpoint_list = "\n".join([
            f"- {e['method']} {e['path']} (in {e['file']})" 
            for e in endpoints[:10]  # Limit to 10
        ])
        
        prompt = f"""Generate comprehensive API tests for these endpoints:

{endpoint_list}

Requirements:
1. Use the appropriate testing framework (Jest for JS/TS, Pytest for Python)
2. Test success cases (200 status)
3. Test error cases (400, 404, 500)
4. Include mock data where needed
5. Add comments explaining each test

Return ONLY the test code, no explanations."""

        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a test engineer. Generate clean, comprehensive tests."},
                {"role": "user", "content": prompt}
            ])
            
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            
            # Extract code block if present
            code_match = re.search(r'```(?:python|typescript|javascript)?\n(.*?)```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            return content
            
        except Exception as e:
            console.print(f"[red]Test generation error: {e}[/red]")
            return ""

    def generate_unit_tests(self, functions: List[Dict[str, Any]]) -> str:
        """
        Use LLM to generate unit tests for functions.
        
        Args:
            functions: List of function dicts
            
        Returns:
            Generated test code
        """
        if not functions:
            return ""
        
        # Build prompt with function context
        func_list = "\n".join([
            f"- {f['name']} in {f['file']} (line {f['line']})"
            for f in functions[:10]  # Limit
        ])
        
        prompt = f"""Generate unit tests for these functions:

{func_list}

Requirements:
1. Use appropriate testing framework
2. Test normal inputs
3. Test edge cases (empty, null, large values)
4. Test error handling
5. Mock external dependencies

Return ONLY the test code."""

        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a test engineer. Generate clean, comprehensive unit tests."},
                {"role": "user", "content": prompt}
            ])
            
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            
            code_match = re.search(r'```(?:python|typescript|javascript)?\n(.*?)```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            return content
            
        except Exception as e:
            console.print(f"[red]Test generation error: {e}[/red]")
            return ""

    def save_tests(self, test_code: str, test_type: str = "api") -> Dict[str, Any]:
        """
        Save generated tests to file.
        
        Args:
            test_code: Generated test code
            test_type: Type of test (api, unit)
            
        Returns:
            Result dict with path
        """
        if not test_code:
            return {"success": False, "error": "No test code to save"}
        
        # Determine test directory and filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check for existing test directories
        test_dirs = ["__tests__", "tests", "test"]
        test_dir = None
        
        for d in test_dirs:
            if os.path.exists(os.path.join(self.project_dir, d)):
                test_dir = os.path.join(self.project_dir, d)
                break
        
        if not test_dir:
            test_dir = os.path.join(self.project_dir, "__tests__")
            os.makedirs(test_dir, exist_ok=True)
        
        # Determine file extension based on content
        if "import pytest" in test_code or "def test_" in test_code:
            ext = ".py"
            filename = f"test_generated_{test_type}_{timestamp}.py"
        else:
            ext = ".test.ts"
            filename = f"generated_{test_type}_{timestamp}.test.ts"
        
        file_path = os.path.join(test_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            rel_path = os.path.relpath(file_path, self.project_dir)
            console.print(f"[green]✓[/green] Tests saved to {rel_path}")
            
            return {"success": True, "path": rel_path}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_and_run(self) -> Dict[str, Any]:
        """
        Full workflow: scan, generate, save, and optionally run tests.
        
        Returns:
            Complete result with endpoints, functions, and test paths
        """
        console.print("\n[bold #A855F7]🧪 Auto-generating tests...[/bold #A855F7]\n")
        
        results = {
            "endpoints": [],
            "functions": [],
            "tests_generated": [],
            "success": True
        }
        
        # Scan endpoints
        endpoints = self.scan_endpoints()
        results["endpoints"] = endpoints
        
        if endpoints:
            console.print("[dim]Generating endpoint tests...[/dim]")
            endpoint_tests = self.generate_endpoint_tests(endpoints)
            if endpoint_tests:
                save_result = self.save_tests(endpoint_tests, "api")
                if save_result.get("success"):
                    results["tests_generated"].append(save_result["path"])
        
        # Scan functions  
        functions = self.scan_functions()
        results["functions"] = functions
        
        if functions:
            console.print("[dim]Generating unit tests...[/dim]")
            unit_tests = self.generate_unit_tests(functions)
            if unit_tests:
                save_result = self.save_tests(unit_tests, "unit")
                if save_result.get("success"):
                    results["tests_generated"].append(save_result["path"])
        
        console.print(f"\n[green]✓[/green] Generated {len(results['tests_generated'])} test files")
        
        return results
