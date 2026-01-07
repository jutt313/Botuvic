import json
from datetime import datetime


class ProgressTracker:
    """
    Tracks task and phase completion throughout project lifecycle.
    """
    
    def __init__(self, storage):
        self.storage = storage
    
    def initialize(self, roadmap):
        """
        Initialize progress tracking for new project.
        
        Args:
            roadmap: Roadmap dict with phases and tasks
        """
        progress = {
            "project_name": roadmap.get("project_name", "Project"),
            "current_phase": 1,
            "phases": [],
            "overall_progress": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Initialize phase progress
        for phase in roadmap["phases"]:
            phase_progress = {
                "phase_number": phase["phase_number"],
                "name": phase["name"],
                "status": "pending",  # pending, in_progress, complete
                "started_at": None,
                "completed_at": None,
                "total_tasks": len(phase["tasks"]),
                "completed_tasks": 0,
                "progress_percentage": 0,
                "tasks": []
            }
            
            # Initialize task progress
            for task in phase["tasks"]:
                task_progress = {
                    "task_number": task["task_number"],
                    "name": task["name"],
                    "status": "pending",  # pending, in_progress, complete
                    "started_at": None,
                    "completed_at": None
                }
                phase_progress["tasks"].append(task_progress)
                progress["total_tasks"] += 1
            
            progress["phases"].append(phase_progress)
        
        self.storage.save("progress", progress)
        return progress
    
    def start_phase(self, phase_number):
        """Mark a phase as started."""
        progress = self.storage.load("progress")
        if not progress:
            return None
        
        for phase in progress["phases"]:
            if phase["phase_number"] == phase_number:
                phase["status"] = "in_progress"
                phase["started_at"] = datetime.now().isoformat()
                progress["current_phase"] = phase_number
                break
        
        progress["last_updated"] = datetime.now().isoformat()
        self.storage.save("progress", progress)
        
        return progress
    
    def start_task(self, phase_number, task_number):
        """Mark a task as started."""
        progress = self.storage.load("progress")
        if not progress:
            return None
        
        for phase in progress["phases"]:
            if phase["phase_number"] == phase_number:
                for task in phase["tasks"]:
                    if task["task_number"] == task_number:
                        task["status"] = "in_progress"
                        task["started_at"] = datetime.now().isoformat()
                        break
                break
        
        progress["last_updated"] = datetime.now().isoformat()
        self.storage.save("progress", progress)
        
        return progress
    
    def complete_task(self, phase_number, task_number):
        """Mark a task as completed."""
        progress = self.storage.load("progress")
        if not progress:
            return None
        
        for phase in progress["phases"]:
            if phase["phase_number"] == phase_number:
                for task in phase["tasks"]:
                    if task["task_number"] == task_number:
                        task["status"] = "complete"
                        task["completed_at"] = datetime.now().isoformat()
                        
                        # Update phase stats
                        phase["completed_tasks"] += 1
                        phase["progress_percentage"] = int(
                            (phase["completed_tasks"] / phase["total_tasks"]) * 100
                        ) if phase["total_tasks"] > 0 else 0
                        
                        # Update overall stats
                        progress["completed_tasks"] += 1
                        progress["overall_progress"] = int(
                            (progress["completed_tasks"] / progress["total_tasks"]) * 100
                        ) if progress["total_tasks"] > 0 else 0
                        break
                break
        
        progress["last_updated"] = datetime.now().isoformat()
        self.storage.save("progress", progress)
        
        return progress
    
    def complete_phase(self, phase_number):
        """Mark a phase as completed."""
        progress = self.storage.load("progress")
        if not progress:
            return None
        
        for phase in progress["phases"]:
            if phase["phase_number"] == phase_number:
                phase["status"] = "complete"
                phase["completed_at"] = datetime.now().isoformat()
                phase["progress_percentage"] = 100
                break
        
        progress["last_updated"] = datetime.now().isoformat()
        self.storage.save("progress", progress)
        
        return progress
    
    def get_current_status(self):
        """Get current project status."""
        progress = self.storage.load("progress")
        roadmap = self.storage.load("roadmap")
        
        if not progress or not roadmap:
            return None
        
        current_phase_num = progress["current_phase"]
        current_phase_progress = None
        current_phase_roadmap = None
        
        # Find current phase
        for phase in progress["phases"]:
            if phase["phase_number"] == current_phase_num:
                current_phase_progress = phase
                break
        
        for phase in roadmap["phases"]:
            if phase["phase_number"] == current_phase_num:
                current_phase_roadmap = phase
                break
        
        # Find next pending task
        next_task = None
        if current_phase_progress:
            for task in current_phase_progress["tasks"]:
                if task["status"] == "pending":
                    # Get full task details from roadmap
                    if current_phase_roadmap:
                        for roadmap_task in current_phase_roadmap["tasks"]:
                            if roadmap_task["task_number"] == task["task_number"]:
                                next_task = roadmap_task
                                break
                    break
        
        status = {
            "overall_progress": progress["overall_progress"],
            "total_tasks": progress["total_tasks"],
            "completed_tasks": progress["completed_tasks"],
            "current_phase": {
                "number": current_phase_num,
                "name": current_phase_progress["name"] if current_phase_progress else None,
                "progress": current_phase_progress["progress_percentage"] if current_phase_progress else 0,
                "tasks_completed": current_phase_progress["completed_tasks"] if current_phase_progress else 0,
                "total_tasks": current_phase_progress["total_tasks"] if current_phase_progress else 0
            },
            "next_task": next_task,
            "last_updated": progress["last_updated"]
        }
        
        return status

