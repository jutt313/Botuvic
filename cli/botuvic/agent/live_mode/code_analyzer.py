"""
Proactive Code Analyzer for Phase 10 Live Development Mode.
Analyzes code changes and suggests improvements automatically.
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console

console = Console()


class CodeAnalyzer:
    """
    Analyzes code for common issues and suggests improvements.
    Works proactively - detects issues before they become bugs.
    """
    
    def __init__(self, llm_client, storage, project_dir: str):
        """
        Initialize analyzer.
        
        Args:
            llm_client: LLM client for advanced analysis
            storage: Storage for project context
            project_dir: Project root directory
        """
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file for potential improvements.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Analysis results with suggestions
        """
        full_path = os.path.join(self.project_dir, file_path)
        
        if not os.path.exists(full_path):
            return {"success": False, "error": "File not found"}
        
        try:
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine file type
            file_ext = os.path.splitext(file_path)[1]
            
            # Quick pattern-based checks
            quick_issues = self._quick_analysis(content, file_ext)
            
            # If critical issues found, do deep analysis
            if quick_issues:
                deep_analysis = self._deep_analysis(content, file_path, file_ext, quick_issues)
                return deep_analysis
            
            return {
                "success": True,
                "file": file_path,
                "issues": [],
                "message": "No issues detected"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _quick_analysis(self, content: str, file_ext: str) -> List[Dict[str, Any]]:
        """
        Fast pattern-based analysis for common issues.
        
        Args:
            content: File content
            file_ext: File extension
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # JavaScript/TypeScript checks
        if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
            issues.extend(self._check_js_patterns(content))
        
        # Python checks
        elif file_ext == '.py':
            issues.extend(self._check_python_patterns(content))
        
        # General checks for all languages
        issues.extend(self._check_general_patterns(content))
        
        return issues
    
    def _check_js_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check JavaScript/TypeScript patterns."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Missing error handling in fetch/axios
            if re.search(r'(fetch|axios)\s*\(', line) and 'try' not in content[max(0, content.find(line)-200):content.find(line)]:
                if '.catch' not in line and 'await' in line:
                    issues.append({
                        "type": "missing_error_handling",
                        "severity": "high",
                        "line": i,
                        "message": "Fetch/axios without error handling",
                        "suggestion": "Add try-catch block or .catch() handler"
                    })
            
            # Accessing properties without optional chaining
            if re.search(r'\w+\.\w+\.\w+', line) and '?.' not in line:
                if 'user.' in line or 'data.' in line or 'response.' in line:
                    issues.append({
                        "type": "missing_null_check",
                        "severity": "medium",
                        "line": i,
                        "message": "Property access without null check",
                        "suggestion": "Use optional chaining (?.) or add null check"
                    })
            
            # Missing key prop in map
            if '.map(' in line and 'key=' not in line and '<' in line:
                issues.append({
                    "type": "missing_key_prop",
                    "severity": "medium",
                    "line": i,
                    "message": "Missing 'key' prop in list rendering",
                    "suggestion": "Add key={item.id} to mapped elements"
                })
            
            # Console.log in production code
            if 'console.log' in line and 'debug' not in line.lower():
                issues.append({
                    "type": "debug_code",
                    "severity": "low",
                    "line": i,
                    "message": "console.log in production code",
                    "suggestion": "Remove or replace with proper logging"
                })
        
        return issues
    
    def _check_python_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check Python patterns."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Missing error handling in requests
            if 'requests.' in line and 'try' not in content[max(0, content.find(line)-200):content.find(line)]:
                issues.append({
                    "type": "missing_error_handling",
                    "severity": "high",
                    "line": i,
                    "message": "HTTP request without error handling",
                    "suggestion": "Add try-except block"
                })
            
            # Bare except
            if re.match(r'\s*except\s*:', line):
                issues.append({
                    "type": "bare_except",
                    "severity": "medium",
                    "line": i,
                    "message": "Bare except clause catches all exceptions",
                    "suggestion": "Specify exception type: except Exception as e:"
                })
            
            # Missing type hints in function
            if re.match(r'\s*def\s+\w+\s*\([^)]*\)\s*:', line) and '->' not in line:
                if 'self' in line or '__init__' not in line:
                    issues.append({
                        "type": "missing_type_hints",
                        "severity": "low",
                        "line": i,
                        "message": "Function missing type hints",
                        "suggestion": "Add type hints for better code clarity"
                    })
        
        return issues
    
    def _check_general_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Check patterns common to all languages."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Hardcoded credentials/secrets
            if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][\w-]{8,}["\']', line, re.IGNORECASE):
                issues.append({
                    "type": "hardcoded_secret",
                    "severity": "critical",
                    "line": i,
                    "message": "Potential hardcoded secret/credential",
                    "suggestion": "Move to environment variables"
                })
            
            # TODO/FIXME comments
            if re.search(r'(TODO|FIXME|HACK|XXX):', line, re.IGNORECASE):
                issues.append({
                    "type": "todo_comment",
                    "severity": "info",
                    "line": i,
                    "message": "TODO/FIXME comment found",
                    "suggestion": "Address this before production"
                })
        
        return issues
    
    def _deep_analysis(self, content: str, file_path: str, file_ext: str, quick_issues: List[Dict]) -> Dict[str, Any]:
        """
        Deep LLM-based analysis for complex issues.
        
        Args:
            content: File content
            file_path: File path
            file_ext: File extension
            quick_issues: Issues found in quick analysis
            
        Returns:
            Complete analysis with AI-generated suggestions
        """
        # Load project context
        project = self.storage.load("project")
        tech_stack = self.storage.load("tech_stack")
        
        # Build analysis prompt
        prompt = f"""Analyze this code file for potential improvements.

File: {file_path}
Language: {file_ext}

Quick scan found these issues:
{self._format_issues(quick_issues)}

Code:
```
{content[:2000]}  # First 2000 chars
```

Project context:
- Tech stack: {tech_stack.get('backend', 'N/A') if tech_stack else 'N/A'}
- Type: {project.get('type', 'N/A') if project else 'N/A'}

Provide:
1. Severity assessment (critical/high/medium/low)
2. Specific fix for each issue
3. Code example for most critical issue
4. Should auto-apply? (yes/no)

Format as JSON:
{{
  "critical_issues": [...],
  "recommended_fixes": [...],
  "auto_apply_safe": true/false
}}
"""
        
        try:
            # Get LLM analysis
            messages = [
                {"role": "system", "content": "You are a code quality expert. Analyze code and suggest improvements."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat(messages)
            ai_analysis = response.get("content", "")
            
            # Parse response
            import json
            try:
                analysis_data = json.loads(ai_analysis)
            except:
                # Fallback if not JSON
                analysis_data = {"critical_issues": quick_issues, "auto_apply_safe": False}
            
            return {
                "success": True,
                "file": file_path,
                "issues": quick_issues,
                "ai_analysis": analysis_data,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            console.print(f"[yellow]⚠ Deep analysis failed: {e}[/yellow]")
            return {
                "success": True,
                "file": file_path,
                "issues": quick_issues,
                "ai_analysis": None,
                "error": str(e)
            }
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """Format issues for display."""
        if not issues:
            return "None"
        
        formatted = []
        for issue in issues:
            formatted.append(f"- Line {issue['line']}: {issue['message']} ({issue['severity']})")
        
        return "\n".join(formatted)
    
    def generate_fix(self, file_path: str, issue: Dict[str, Any]) -> Optional[str]:
        """
        Generate a code fix for an issue.
        
        Args:
            file_path: File path
            issue: Issue dict
            
        Returns:
            Fixed code or None
        """
        full_path = os.path.join(self.project_dir, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get context around the issue
            lines = content.split('\n')
            issue_line = issue.get('line', 1)
            start = max(0, issue_line - 5)
            end = min(len(lines), issue_line + 5)
            context = '\n'.join(lines[start:end])
            
            # Ask LLM to generate fix
            prompt = f"""Fix this code issue:

Issue: {issue['message']}
Severity: {issue['severity']}
Suggestion: {issue['suggestion']}

Code context (line {issue_line}):
```
{context}
```

Provide the fixed version of the problematic line only.
"""
            
            messages = [
                {"role": "system", "content": "You are a code fixing expert. Provide concise, correct fixes."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat(messages)
            fixed_code = response.get("content", "").strip()
            
            # Remove markdown code blocks if present
            fixed_code = re.sub(r'```[\w]*\n?', '', fixed_code).strip()
            
            return fixed_code
        
        except Exception as e:
            console.print(f"[red]Failed to generate fix: {e}[/red]")
            return None

