import re
import os
from datetime import datetime


class ErrorHandler:
    """
    Detects errors from terminal output, analyzes them, and suggests/applies fixes.
    """
    
    def __init__(self, llm_client, storage):
        self.llm = llm_client
        self.storage = storage
    
    def detect_error(self, terminal_output):
        """
        Detect if terminal output contains an error.
        
        Args:
            terminal_output: String output from terminal
            
        Returns:
            Dict with error info or None
        """
        # Common error patterns
        error_patterns = [
            (r'Error: (.+)', 'general'),
            (r'TypeError: (.+)', 'type_error'),
            (r'SyntaxError: (.+)', 'syntax_error'),
            (r'ReferenceError: (.+)', 'reference_error'),
            (r'ModuleNotFoundError: (.+)', 'module_not_found'),
            (r'ImportError: (.+)', 'import_error'),
            (r'AttributeError: (.+)', 'attribute_error'),
            (r'(\w+Error): (.+)', 'python_error'),
            (r'FAIL (.+)', 'test_failure'),
            (r'ERROR in (.+)', 'build_error'),
        ]
        
        for pattern, error_type in error_patterns:
            match = re.search(pattern, terminal_output, re.IGNORECASE)
            if match:
                # Extract file and line number if present
                file_line_match = re.search(r'at (.+):(\d+)', terminal_output)
                file_path = None
                line_number = None
                
                if file_line_match:
                    file_path = file_line_match.group(1)
                    try:
                        line_number = int(file_line_match.group(2))
                    except:
                        pass
                
                error_info = {
                    "type": error_type,
                    "message": match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0),
                    "file": file_path,
                    "line": line_number,
                    "full_output": terminal_output,
                    "detected_at": datetime.now().isoformat()
                }
                
                return error_info
        
        return None
    
    def analyze_and_fix(self, error_info, project_dir, user_profile):
        """
        Analyze error and generate fix.
        
        Args:
            error_info: Dict from detect_error()
            project_dir: Project directory
            user_profile: User profile for tailoring explanation
            
        Returns:
            Dict with analysis and fix
        """
        # Read the file where error occurred if available
        file_content = None
        if error_info.get("file"):
            try:
                file_path = os.path.join(project_dir, error_info["file"])
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
            except:
                pass
        
        # Load project context
        project = self.storage.load("project")
        roadmap = self.storage.load("roadmap")
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            error_info,
            file_content,
            project,
            roadmap,
            user_profile
        )
        
        # Get LLM analysis
        messages = [
            {"role": "system", "content": self._get_analysis_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        analysis_text = response.get("content", "")
        
        # Parse analysis
        result = self._parse_analysis(analysis_text, error_info)
        
        # Save error to log
        self._log_error(error_info, result)
        
        return result
    
    def _get_analysis_system_prompt(self):
        """System prompt for error analysis."""
        return """You are an expert debugger helping developers fix errors.

Analyze the error and provide:
1. Clear explanation of what went wrong
2. Why it happened
3. Exact code fix
4. How to prevent in future

Be specific and actionable. Don't be vague.

Format response as:

WHAT WENT WRONG:
[Simple explanation of the error]

WHY IT HAPPENED:
[Root cause]

FIX:
```
[Exact code to fix, with line numbers if applicable]
```

EXPLANATION:
[Why this fix works]

PREVENTION:
[How to avoid this in future]
"""
    
    def _build_analysis_prompt(self, error_info, file_content, project, roadmap, user_profile):
        """Build error analysis prompt."""
        prompt_parts = []
        
        prompt_parts.append(f"ERROR TYPE: {error_info['type']}")
        prompt_parts.append(f"ERROR MESSAGE: {error_info['message']}")
        
        if error_info.get('file'):
            prompt_parts.append(f"FILE: {error_info['file']}")
            prompt_parts.append(f"LINE: {error_info['line']}")
        
        prompt_parts.append(f"\nFULL ERROR OUTPUT:")
        prompt_parts.append(error_info['full_output'])
        
        if file_content:
            prompt_parts.append(f"\nFILE CONTENT:")
            # Show lines around error
            if error_info.get('line'):
                lines = file_content.split('\n')
                line_num = error_info['line'] - 1
                start = max(0, line_num - 5)
                end = min(len(lines), line_num + 6)
                
                for i in range(start, end):
                    marker = ">>>" if i == line_num else "   "
                    prompt_parts.append(f"{marker} {i+1}: {lines[i]}")
            else:
                # Show full file if not too long
                if len(file_content) < 2000:
                    prompt_parts.append(file_content)
                else:
                    prompt_parts.append(file_content[:2000] + "\n... (truncated)")
        
        # Add project context
        if project:
            prompt_parts.append(f"\nPROJECT CONTEXT:")
            prompt_parts.append(f"Building: {project.get('idea', 'Unknown')}")
            tech_stack = project.get('tech_stack', {})
            if tech_stack:
                prompt_parts.append(f"Tech stack: {tech_stack}")
        
        # Add user context
        prompt_parts.append(f"\nUSER LEVEL: {user_profile.get('experience', 'learning')}")
        
        if user_profile.get('experience') == 'non-technical':
            prompt_parts.append("Explain in simple, non-technical terms.")
        
        prompt_parts.append("\nAnalyze this error and provide a fix:")
        
        return "\n".join(prompt_parts)
    
    def _parse_analysis(self, analysis_text, error_info):
        """Parse error analysis response."""
        result = {
            "error_info": error_info,
            "what_went_wrong": "",
            "why_it_happened": "",
            "fix_code": "",
            "explanation": "",
            "prevention": "",
            "analyzed_at": datetime.now().isoformat()
        }
        
        current_section = None
        code_block = False
        
        lines = analysis_text.split('\n')
        
        for line in lines:
            # Detect sections
            if line.startswith("WHAT WENT WRONG:"):
                current_section = "what"
            elif line.startswith("WHY IT HAPPENED:"):
                current_section = "why"
            elif line.startswith("FIX:"):
                current_section = "fix"
            elif line.startswith("EXPLANATION:"):
                current_section = "explanation"
            elif line.startswith("PREVENTION:"):
                current_section = "prevention"
            
            # Handle code blocks
            elif line.strip().startswith("```"):
                code_block = not code_block
                continue
            
            # Add content to sections
            elif current_section:
                if current_section == "what":
                    result["what_went_wrong"] += line + "\n"
                elif current_section == "why":
                    result["why_it_happened"] += line + "\n"
                elif current_section == "fix":
                    if code_block or not line.strip().startswith("```"):
                        result["fix_code"] += line + "\n"
                elif current_section == "explanation":
                    result["explanation"] += line + "\n"
                elif current_section == "prevention":
                    result["prevention"] += line + "\n"
        
        # Clean up
        for key in result:
            if isinstance(result[key], str):
                result[key] = result[key].strip()
        
        return result
    
    def apply_fix(self, fix_result, project_dir):
        """
        Apply the suggested fix to the file.
        
        Args:
            fix_result: Dict from analyze_and_fix()
            project_dir: Project directory
            
        Returns:
            Success status
        """
        error_info = fix_result["error_info"]
        
        if not error_info.get("file"):
            return {"success": False, "error": "No file specified"}
        
        file_path = os.path.join(project_dir, error_info["file"])
        
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        
        try:
            # For now, just log the fix - actual application would need more sophisticated patching
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Log the fix
            self._log_fix_applied(error_info, fix_result)
            
            return {
                "success": True,
                "file": error_info["file"],
                "message": "Fix suggested (manual application recommended)",
                "fix_code": fix_result["fix_code"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_error(self, error_info, analysis_result):
        """Log error to errors.json."""
        errors = self.storage.load("errors") or []
        
        error_entry = {
            "id": len(errors) + 1,
            "timestamp": error_info["detected_at"],
            "type": error_info["type"],
            "message": error_info["message"],
            "file": error_info.get("file"),
            "line": error_info.get("line"),
            "analysis": {
                "what": analysis_result["what_went_wrong"],
                "why": analysis_result["why_it_happened"],
                "prevention": analysis_result["prevention"]
            },
            "status": "pending",  # pending, fixed, ignored
            "fix_applied": None
        }
        
        errors.append(error_entry)
        self.storage.save("errors", errors)
    
    def _log_fix_applied(self, error_info, fix_result):
        """Update error log when fix is applied."""
        errors = self.storage.load("errors") or []
        
        # Find the error and update it
        for error in errors:
            if (error["message"] == error_info["message"] and 
                error.get("file") == error_info.get("file")):
                error["status"] = "fixed"
                error["fix_applied"] = datetime.now().isoformat()
                error["fix_code"] = fix_result["fix_code"]
                break
        
        self.storage.save("errors", errors)

