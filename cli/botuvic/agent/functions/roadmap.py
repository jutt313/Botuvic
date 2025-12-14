import json
from datetime import datetime, timedelta


class RoadmapGenerator:
    """
    Generates comprehensive project roadmaps with phases and tasks.
    Adapts based on project complexity, user skill level, and AI tools.
    """
    
    def __init__(self, llm_client, storage):
        self.llm = llm_client
        self.storage = storage
    
    def generate(self, project_info, user_profile):
        """
        Generate complete roadmap for project.
        
        Args:
            project_info: Dict with project details (idea, features, scale, tech_stack)
            user_profile: Dict with user skill level and AI tools
            
        Returns:
            Dict with phases, tasks, timeline
        """
        # Build prompt for roadmap generation
        prompt = self._build_roadmap_prompt(project_info, user_profile)
        
        # Get roadmap from LLM
        messages = [
            {"role": "system", "content": self._get_roadmap_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        roadmap_text = response.get("content", "")
        
        # Parse roadmap into structured format
        roadmap = self._parse_roadmap(roadmap_text, project_info, user_profile)
        
        # Add timeline estimates
        roadmap = self._add_timeline(roadmap, project_info.get("scale", "medium"))
        
        # Save to storage
        self.storage.save("roadmap", roadmap)
        
        return roadmap
    
    def _get_roadmap_system_prompt(self):
        """System prompt for roadmap generation."""
        return """You are an expert project manager creating a comprehensive development roadmap.

Generate a roadmap with:
1. 4-6 phases that logically build upon each other
2. Each phase has 5-15 concrete, actionable tasks
3. Tasks are ordered by dependency
4. Each task includes:
   - Clear objective
   - What files/components to create
   - Acceptance criteria
   
Format your response as:

PHASE 1: [Phase Name] ([Duration estimate])
[Brief description of what this phase accomplishes]

Tasks:
1. [Task name]
   - Objective: [What this accomplishes]
   - Files: [What files to create/modify]
   - Done when: [How to verify completion]
   
2. [Next task...]

PHASE 2: [Phase Name] ([Duration estimate])
...

Important:
- Start with setup/foundation, end with deployment
- Each phase should be completable before moving to next
- Tasks should be specific, not vague
- Consider the tech stack when defining tasks
"""
    
    def _build_roadmap_prompt(self, project_info, user_profile):
        """Build prompt for roadmap generation."""
        prompt_parts = []
        
        # Project details
        prompt_parts.append(f"PROJECT: {project_info.get('idea', 'Untitled Project')}")
        prompt_parts.append(f"USERS: {', '.join(project_info.get('users', []))}")
        prompt_parts.append(f"FEATURES: {', '.join(project_info.get('features', []))}")
        prompt_parts.append(f"SCALE: {project_info.get('scale', 'medium')}")
        
        # Tech stack
        tech_stack = project_info.get('tech_stack', {})
        if tech_stack:
            prompt_parts.append(f"\nTECH STACK:")
            for key, value in tech_stack.items():
                prompt_parts.append(f"- {key}: {value}")
        
        # User context
        prompt_parts.append(f"\nUSER LEVEL: {user_profile.get('experience', 'learning')}")
        
        ai_tools = user_profile.get('ai_tools', [])
        if ai_tools:
            prompt_parts.append(f"AI TOOLS AVAILABLE: {', '.join(ai_tools)}")
            prompt_parts.append("\nADAPT TASKS FOR THESE AI TOOLS:")
            if 'cursor' in ai_tools:
                prompt_parts.append("- Include Cursor-friendly prompts for code generation")
            if 'v0.dev' in ai_tools or 'bolt.new' in ai_tools:
                prompt_parts.append("- Separate UI components for no-code generation")
        
        prompt_parts.append("\nGenerate a comprehensive roadmap:")
        
        return "\n".join(prompt_parts)
    
    def _parse_roadmap(self, roadmap_text, project_info, user_profile):
        """Parse LLM-generated roadmap into structured format."""
        phases = []
        current_phase = None
        current_task = None
        
        lines = roadmap_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Detect phase headers
            if line.startswith('PHASE '):
                if current_phase:
                    phases.append(current_phase)
                
                # Extract phase number and name
                parts = line.split(':', 1)
                phase_num = parts[0].replace('PHASE ', '').strip()
                phase_info = parts[1].strip() if len(parts) > 1 else ""
                
                current_phase = {
                    "phase_number": int(phase_num) if phase_num.isdigit() else len(phases) + 1,
                    "name": phase_info.split('(')[0].strip(),
                    "description": "",
                    "tasks": [],
                    "status": "pending"
                }
                current_task = None
            
            # Detect tasks
            elif line and line[0].isdigit() and '.' in line[:3]:
                if current_phase is not None:
                    task_text = line.split('.', 1)[1].strip() if '.' in line else line
                    
                    current_task = {
                        "task_number": len(current_phase["tasks"]) + 1,
                        "name": task_text,
                        "objective": "",
                        "files": [],
                        "acceptance_criteria": "",
                        "status": "pending",
                        "ai_prompt": ""
                    }
                    current_phase["tasks"].append(current_task)
            
            # Parse task details
            elif current_task and line.startswith('- Objective:'):
                current_task["objective"] = line.replace('- Objective:', '').strip()
            elif current_task and line.startswith('- Files:'):
                files_str = line.replace('- Files:', '').strip()
                current_task["files"] = [f.strip() for f in files_str.split(',') if f.strip()]
            elif current_task and line.startswith('- Done when:'):
                current_task["acceptance_criteria"] = line.replace('- Done when:', '').strip()
            
            # Phase description (lines after phase header before tasks)
            elif current_phase and not current_task and line and not line.startswith('Tasks:'):
                current_phase["description"] += " " + line
        
        # Add last phase
        if current_phase:
            phases.append(current_phase)
        
        # Add AI prompts for tasks if user has AI tools
        if user_profile.get('ai_tools'):
            phases = self._add_ai_prompts(phases, user_profile['ai_tools'])
        
        roadmap = {
            "project_name": project_info.get('idea', 'Untitled Project'),
            "total_phases": len(phases),
            "current_phase": 1,
            "phases": phases,
            "created_at": datetime.now().isoformat(),
            "tech_stack": project_info.get('tech_stack', {})
        }
        
        return roadmap
    
    def _add_ai_prompts(self, phases, ai_tools):
        """Add AI tool-specific prompts to tasks."""
        for phase in phases:
            for task in phase["tasks"]:
                prompt_parts = []
                
                if 'cursor' in ai_tools or 'claude_code' in ai_tools:
                    # Generate Cursor/Claude Code prompt
                    prompt_parts.append(f"Task: {task['name']}")
                    prompt_parts.append(f"Objective: {task['objective']}")
                    if task['files']:
                        prompt_parts.append(f"Create: {', '.join(task['files'])}")
                
                task['ai_prompt'] = '\n'.join(prompt_parts)
        
        return phases
    
    def _add_timeline(self, roadmap, scale):
        """Add timeline estimates to roadmap."""
        # Estimate days per phase based on scale
        days_per_phase = {
            "simple": 3,
            "medium": 5,
            "large": 7
        }
        
        days = days_per_phase.get(scale, 5)
        
        start_date = datetime.now()
        
        for i, phase in enumerate(roadmap["phases"]):
            phase_start = start_date + timedelta(days=i * days)
            phase_end = phase_start + timedelta(days=days)
            
            phase["estimated_start"] = phase_start.isoformat()
            phase["estimated_end"] = phase_end.isoformat()
            phase["estimated_days"] = days
        
        roadmap["estimated_total_days"] = len(roadmap["phases"]) * days
        roadmap["estimated_completion"] = (start_date + timedelta(days=len(roadmap["phases"]) * days)).isoformat()
        
        return roadmap

