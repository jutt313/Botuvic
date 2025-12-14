from datetime import datetime
import os


class ReportGenerator:
    """
    Generates project reports: PLAN.md, TODO.md, REPORT.md, ERRORS.log
    """
    
    def __init__(self, storage):
        self.storage = storage
    
    def generate_all_reports(self):
        """Generate all reports."""
        reports = {
            "PLAN.md": self.generate_plan_report(),
            "TODO.md": self.generate_todo_report(),
            "REPORT.md": self.generate_progress_report(),
            "ERRORS.log": self.generate_errors_log()
        }
        
        # Save each report
        for filename, content in reports.items():
            self.save_report(filename, content)
        
        return {
            "success": True,
            "reports_generated": list(reports.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_report(self, filename, content):
        """Save report to reports directory."""
        reports_dir = os.path.join(self.storage.botuvic_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_plan_report(self):
        """Generate PLAN.md - Complete project roadmap."""
        roadmap = self.storage.load("roadmap")
        project = self.storage.load("project")
        
        if not roadmap:
            return "# Project Plan\n\nNo roadmap generated yet."
        
        lines = []
        
        # Header
        lines.append(f"# {roadmap['project_name']} - Project Plan")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Total Phases: {roadmap['total_phases']}")
        lines.append(f"Estimated Duration: {roadmap.get('estimated_total_days', 'N/A')} days")
        
        # Tech Stack
        if project and project.get('tech_stack'):
            lines.append(f"\n## Tech Stack\n")
            tech_stack = project['tech_stack']
            for key, value in tech_stack.items():
                lines.append(f"- **{key.title()}**: {value}")
        
        # Phases
        lines.append(f"\n## Project Phases\n")
        
        for phase in roadmap["phases"]:
            lines.append(f"### Phase {phase['phase_number']}: {phase['name']}")
            lines.append(f"\n{phase.get('description', '')}")
            lines.append(f"\n**Duration**: {phase.get('estimated_days', 'N/A')} days")
            lines.append(f"\n#### Tasks:\n")
            
            for task in phase["tasks"]:
                lines.append(f"{task['task_number']}. **{task['name']}**")
                lines.append(f"   - Objective: {task.get('objective', '')}")
                lines.append(f"   - Files: {', '.join(task.get('files', []))}")
                lines.append(f"   - Done when: {task.get('acceptance_criteria', '')}")
                
                if task.get('ai_prompt'):
                    lines.append(f"   - AI Prompt: `{task['ai_prompt']}`")
                
                lines.append("")
            
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def generate_todo_report(self):
        """Generate TODO.md - Task list with status."""
        roadmap = self.storage.load("roadmap")
        progress = self.storage.load("progress")
        
        if not roadmap or not progress:
            return "# TODO\n\nNo tasks yet."
        
        lines = []
        
        # Header
        lines.append(f"# {roadmap['project_name']} - TODO List")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Overall Progress: {progress['overall_progress']}%")
        lines.append(f"Completed: {progress['completed_tasks']}/{progress['total_tasks']} tasks")
        
        # Current Phase highlight
        lines.append(f"\n## Current Phase: Phase {progress['current_phase']}\n")
        
        # Tasks by phase
        for phase_roadmap in roadmap["phases"]:
            phase_num = phase_roadmap["phase_number"]
            
            # Find matching progress
            phase_progress = None
            for p in progress["phases"]:
                if p["phase_number"] == phase_num:
                    phase_progress = p
                    break
            
            if not phase_progress:
                continue
            
            # Phase header
            status_emoji = {
                "pending": "⏸️",
                "in_progress": "🔄",
                "complete": "✅"
            }
            
            emoji = status_emoji.get(phase_progress["status"], "❓")
            lines.append(f"## {emoji} Phase {phase_num}: {phase_roadmap['name']}")
            lines.append(f"Progress: {phase_progress['progress_percentage']}% ({phase_progress['completed_tasks']}/{phase_progress['total_tasks']} tasks)\n")
            
            # Tasks
            for task_roadmap in phase_roadmap["tasks"]:
                # Find task progress
                task_progress = None
                for t in phase_progress["tasks"]:
                    if t["task_number"] == task_roadmap["task_number"]:
                        task_progress = t
                        break
                
                if not task_progress:
                    continue
                
                # Task status
                if task_progress["status"] == "complete":
                    checkbox = "[x]"
                    status = "✅"
                elif task_progress["status"] == "in_progress":
                    checkbox = "[ ]"
                    status = "🔄"
                else:
                    checkbox = "[ ]"
                    status = "⏸️"
                
                lines.append(f"- {checkbox} **{task_roadmap['name']}** {status}")
                lines.append(f"  - {task_roadmap.get('objective', '')}")
                
                if task_progress["status"] == "complete" and task_progress.get("completed_at"):
                    try:
                        completed_date = datetime.fromisoformat(task_progress["completed_at"]).strftime('%Y-%m-%d')
                        lines.append(f"  - ✅ Completed: {completed_date}")
                    except:
                        pass
                
                lines.append("")
            
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def generate_progress_report(self):
        """Generate REPORT.md - Progress analytics."""
        roadmap = self.storage.load("roadmap")
        progress = self.storage.load("progress")
        project = self.storage.load("project")
        errors = self.storage.load("errors") or []
        
        if not progress:
            return "# Progress Report\n\nNo progress data yet."
        
        lines = []
        
        # Header
        lines.append(f"# {roadmap['project_name'] if roadmap else 'Project'} - Progress Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Overall Stats
        lines.append(f"\n## Overall Statistics\n")
        lines.append(f"- **Overall Progress**: {progress['overall_progress']}%")
        lines.append(f"- **Tasks Completed**: {progress['completed_tasks']} / {progress['total_tasks']}")
        lines.append(f"- **Current Phase**: Phase {progress['current_phase']}")
        
        try:
            started = datetime.fromisoformat(progress['started_at'])
            lines.append(f"- **Started**: {started.strftime('%Y-%m-%d')}")
            
            # Calculate days elapsed
            days_elapsed = (datetime.now() - started).days
            lines.append(f"- **Days Elapsed**: {days_elapsed}")
        except:
            pass
        
        # Phase Progress
        lines.append(f"\n## Phase Progress\n")
        
        for phase_progress in progress["phases"]:
            status = phase_progress["status"]
            name = phase_progress["name"]
            pct = phase_progress["progress_percentage"]
            
            if status == "complete":
                emoji = "✅"
            elif status == "in_progress":
                emoji = "🔄"
            else:
                emoji = "⏸️"
            
            lines.append(f"### {emoji} Phase {phase_progress['phase_number']}: {name}")
            lines.append(f"- Progress: {pct}%")
            lines.append(f"- Tasks: {phase_progress['completed_tasks']}/{phase_progress['total_tasks']}")
            
            if phase_progress.get("started_at"):
                try:
                    started = datetime.fromisoformat(phase_progress["started_at"]).strftime('%Y-%m-%d')
                    lines.append(f"- Started: {started}")
                except:
                    pass
            
            if phase_progress.get("completed_at"):
                try:
                    completed = datetime.fromisoformat(phase_progress["completed_at"]).strftime('%Y-%m-%d')
                    lines.append(f"- Completed: {completed}")
                except:
                    pass
            
            lines.append("")
        
        # Error Summary
        if errors:
            lines.append(f"\n## Error Summary\n")
            total_errors = len(errors)
            fixed_errors = len([e for e in errors if e["status"] == "fixed"])
            pending_errors = len([e for e in errors if e["status"] == "pending"])
            
            lines.append(f"- **Total Errors**: {total_errors}")
            lines.append(f"- **Fixed**: {fixed_errors}")
            lines.append(f"- **Pending**: {pending_errors}")
            
            if pending_errors > 0:
                lines.append(f"\n### Pending Errors:\n")
                for error in errors:
                    if error["status"] == "pending":
                        lines.append(f"- {error['type']}: {error['message'][:100]}")
                        if error.get('file'):
                            lines.append(f"  - File: {error['file']}:{error.get('line', '?')}")
                        lines.append("")
        
        # Tech Stack
        if project and project.get('tech_stack'):
            lines.append(f"\n## Tech Stack\n")
            for key, value in project['tech_stack'].items():
                lines.append(f"- **{key.title()}**: {value}")
        
        # Next Steps
        lines.append(f"\n## Next Steps\n")
        
        # Find next pending task
        current_phase = progress["current_phase"]
        for phase_progress in progress["phases"]:
            if phase_progress["phase_number"] == current_phase:
                for task in phase_progress["tasks"]:
                    if task["status"] == "pending":
                        # Get task details from roadmap
                        if roadmap:
                            for phase_roadmap in roadmap["phases"]:
                                if phase_roadmap["phase_number"] == current_phase:
                                    for task_roadmap in phase_roadmap["tasks"]:
                                        if task_roadmap["task_number"] == task["task_number"]:
                                            lines.append(f"1. {task_roadmap['name']}")
                                            lines.append(f"   - {task_roadmap.get('objective', '')}")
                                            break
                                    break
                        break
                break
        
        return "\n".join(lines)
    
    def generate_errors_log(self):
        """Generate ERRORS.log - Error history."""
        errors = self.storage.load("errors") or []
        
        if not errors:
            return "# Error Log\n\nNo errors logged yet."
        
        lines = []
        
        lines.append("# Error Log")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Total Errors: {len(errors)}")
        lines.append(f"Fixed: {len([e for e in errors if e['status'] == 'fixed'])}")
        lines.append(f"Pending: {len([e for e in errors if e['status'] == 'pending'])}\n")
        lines.append("=" * 80)
        lines.append("")
        
        for error in errors:
            try:
                timestamp = datetime.fromisoformat(error["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = error.get("timestamp", "Unknown")
            
            lines.append(f"\n[{error.get('id', '?')}] {error['type'].upper()} - {error['status'].upper()}")
            lines.append(f"Time: {timestamp}")
            lines.append(f"Message: {error['message']}")
            
            if error.get('file'):
                lines.append(f"File: {error['file']}:{error.get('line', '?')}")
            
            if error.get('analysis'):
                lines.append(f"\nAnalysis:")
                lines.append(f"  What: {error['analysis'].get('what', '')[:200]}")
                lines.append(f"  Why: {error['analysis'].get('why', '')[:200]}")
            
            if error['status'] == 'fixed' and error.get('fix_applied'):
                try:
                    fix_time = datetime.fromisoformat(error['fix_applied']).strftime('%Y-%m-%d %H:%M:%S')
                    lines.append(f"\n✅ Fixed: {fix_time}")
                except:
                    pass
            
            lines.append("\n" + "-" * 80)
        
        return "\n".join(lines)

