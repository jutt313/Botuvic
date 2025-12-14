import os
from datetime import datetime


class PhaseVerifier:
    """
    Verifies that phase requirements are met before allowing progression.
    """
    
    def __init__(self, llm_client, storage, scan_function):
        self.llm = llm_client
        self.storage = storage
        self.scan_function = scan_function
    
    def verify_phase(self, phase_number, project_dir):
        """
        Verify if a phase is complete and ready for next phase.
        
        Args:
            phase_number: Phase number to verify
            project_dir: Project directory path
            
        Returns:
            Dict with verification results
        """
        # Load roadmap and progress
        roadmap = self.storage.load("roadmap")
        progress = self.storage.load("progress")
        
        if not roadmap or not progress:
            return {"error": "No roadmap or progress found"}
        
        # Find phase in roadmap
        phase_roadmap = None
        for phase in roadmap["phases"]:
            if phase["phase_number"] == phase_number:
                phase_roadmap = phase
                break
        
        if not phase_roadmap:
            return {"error": f"Phase {phase_number} not found"}
        
        # Scan current project state
        scan_result = self.scan_function(project_dir)
        
        # Build verification prompt
        verification_prompt = self._build_verification_prompt(
            phase_roadmap,
            scan_result,
            project_dir
        )
        
        # Get LLM verification
        messages = [
            {"role": "system", "content": self._get_verification_system_prompt()},
            {"role": "user", "content": verification_prompt}
        ]
        
        response = self.llm.chat(messages)
        verification_text = response.get("content", "")
        
        # Parse verification result
        result = self._parse_verification(verification_text, phase_roadmap)
        
        # Save verification result
        self._save_verification_result(phase_number, result)
        
        return result
    
    def _get_verification_system_prompt(self):
        """System prompt for phase verification."""
        return """You are a strict quality assurance engineer verifying phase completion.

Your job is to check if ALL requirements for this phase are met.

For each task in the phase:
1. Check if the required files exist
2. Verify the implementation meets the objective
3. Confirm acceptance criteria are satisfied

Be STRICT. If something is missing or incomplete, mark it as FAILED.

Format your response as:

VERIFICATION SUMMARY:
Overall Status: [PASS/FAIL]

TASK VERIFICATION:
Task 1: [Task name]
Status: [PASS/FAIL]
Reason: [Why it passed or what's missing]

Task 2: [Task name]
Status: [PASS/FAIL]
Reason: [Why it passed or what's missing]

...

MISSING ITEMS:
- [List anything missing or incomplete]

BLOCKERS:
- [List critical issues that must be fixed before next phase]

RECOMMENDATION:
[APPROVE for next phase / BLOCK until issues fixed]
"""
    
    def _build_verification_prompt(self, phase_roadmap, scan_result, project_dir):
        """Build verification prompt."""
        prompt_parts = []
        
        prompt_parts.append(f"PHASE TO VERIFY: Phase {phase_roadmap['phase_number']} - {phase_roadmap['name']}")
        prompt_parts.append(f"DESCRIPTION: {phase_roadmap.get('description', '')}")
        prompt_parts.append(f"\nTASKS IN THIS PHASE:")
        
        for task in phase_roadmap["tasks"]:
            prompt_parts.append(f"\nTask {task['task_number']}: {task['name']}")
            prompt_parts.append(f"  Objective: {task.get('objective', '')}")
            prompt_parts.append(f"  Required files: {', '.join(task.get('files', []))}")
            prompt_parts.append(f"  Done when: {task.get('acceptance_criteria', '')}")
        
        prompt_parts.append(f"\nCURRENT PROJECT STATE:")
        prompt_parts.append(f"Total files: {scan_result.get('total_files', 0)}")
        prompt_parts.append(f"Files found:")
        for file_info in scan_result.get('files', [])[:20]:  # Limit to 20 files
            prompt_parts.append(f"  - {file_info.get('path', '')} ({file_info.get('lines', 0)} lines)")
        
        # Read key files for verification
        prompt_parts.append(f"\nKEY FILE CONTENTS:")
        for task in phase_roadmap["tasks"]:
            for file_path in task.get("files", []):
                full_path = os.path.join(project_dir, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Truncate if too long
                            if len(content) > 1000:
                                content = content[:1000] + "\n... (truncated)"
                            prompt_parts.append(f"\n--- {file_path} ---")
                            prompt_parts.append(content)
                    except:
                        prompt_parts.append(f"\n--- {file_path} ---")
                        prompt_parts.append("[Could not read file]")
                else:
                    prompt_parts.append(f"\n--- {file_path} ---")
                    prompt_parts.append("[FILE MISSING]")
        
        prompt_parts.append(f"\nVerify if this phase is complete:")
        
        return "\n".join(prompt_parts)
    
    def _parse_verification(self, verification_text, phase_roadmap):
        """Parse LLM verification response."""
        result = {
            "phase_number": phase_roadmap["phase_number"],
            "phase_name": phase_roadmap["name"],
            "overall_status": "FAIL",  # Default to fail
            "tasks": [],
            "missing_items": [],
            "blockers": [],
            "recommendation": "",
            "verified_at": datetime.now().isoformat()
        }
        
        lines = verification_text.split('\n')
        current_section = None
        current_task = None
        
        for line in lines:
            line = line.strip()
            
            # Parse overall status
            if "Overall Status:" in line:
                if "PASS" in line:
                    result["overall_status"] = "PASS"
                else:
                    result["overall_status"] = "FAIL"
            
            # Section markers
            elif line.startswith("TASK VERIFICATION:"):
                current_section = "tasks"
            elif line.startswith("MISSING ITEMS:"):
                current_section = "missing"
            elif line.startswith("BLOCKERS:"):
                current_section = "blockers"
            elif line.startswith("RECOMMENDATION:"):
                current_section = "recommendation"
            
            # Parse task verification
            elif current_section == "tasks" and line.startswith("Task "):
                task_name = line.split(':', 1)[1].strip() if ':' in line else ""
                current_task = {
                    "name": task_name,
                    "status": "FAIL",
                    "reason": ""
                }
                result["tasks"].append(current_task)
            elif current_section == "tasks" and current_task:
                if line.startswith("Status:"):
                    current_task["status"] = "PASS" if "PASS" in line else "FAIL"
                elif line.startswith("Reason:"):
                    current_task["reason"] = line.replace("Reason:", "").strip()
            
            # Parse missing items
            elif current_section == "missing" and line.startswith("-"):
                result["missing_items"].append(line[1:].strip())
            
            # Parse blockers
            elif current_section == "blockers" and line.startswith("-"):
                result["blockers"].append(line[1:].strip())
            
            # Parse recommendation
            elif current_section == "recommendation" and line:
                result["recommendation"] += " " + line
        
        result["recommendation"] = result["recommendation"].strip()
        
        return result
    
    def _save_verification_result(self, phase_number, result):
        """Save verification result to storage."""
        verifications = self.storage.load("verifications") or {}
        verifications[f"phase_{phase_number}"] = result
        self.storage.save("verifications", verifications)

