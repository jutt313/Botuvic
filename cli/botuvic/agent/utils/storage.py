"""Storage utility for .botuvic/ folder operations"""

import os
import json

class Storage:
    """Handles .botuvic/ folder operations."""
    
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.botuvic_dir = os.path.join(project_dir, ".botuvic")
        self.reports_dir = os.path.join(self.botuvic_dir, "reports")
    
    def exists(self):
        """Check if .botuvic/ folder exists."""
        return os.path.exists(self.botuvic_dir)
    
    def init(self):
        """Initialize .botuvic/ folder structure."""
        os.makedirs(self.botuvic_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Create initial files
        initial_files = {
            "config.json": {},
            "project.json": {},
            "phases.json": {},
            "progress.json": {},
            "errors.json": {},
            "history.json": []
        }
        
        for filename, initial_data in initial_files.items():
            filepath = os.path.join(self.botuvic_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(initial_data, f, indent=2)
    
    def save(self, key, data):
        """Save data to storage."""
        if not self.exists():
            self.init()
        
        filepath = os.path.join(self.botuvic_dir, f"{key}.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True}
    
    def load(self, key):
        """Load data from storage."""
        filepath = os.path.join(self.botuvic_dir, f"{key}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def save_report(self, filename, content):
        """Save report to reports folder."""
        if not self.exists():
            self.init()
        
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        
        return {"success": True, "path": filepath}

