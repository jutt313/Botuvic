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
        """Save data to project storage."""
        if not self.exists():
            self.init()
        
        filepath = os.path.join(self.botuvic_dir, f"{key}.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True}

    def set(self, key, data):
        """Backward-compatible alias for save."""
        return self.save(key, data)
    
    def load(self, key):
        """Load data from project storage."""
        filepath = os.path.join(self.botuvic_dir, f"{key}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None

    def get(self, key, default=None):
        """Backward-compatible alias for load with default."""
        data = self.load(key)
        return data if data is not None else default

    def _get_global_dir(self):
        """Get global .botuvic directory in home folder."""
        global_dir = os.path.join(os.path.expanduser("~"), ".botuvic")
        os.makedirs(global_dir, exist_ok=True)
        return global_dir

    def save_global(self, key, data):
        """Save data to global storage (accessible by all projects)."""
        global_dir = self._get_global_dir()
        filepath = os.path.join(global_dir, f"{key}.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return {"success": True}

    def load_global(self, key):
        """Load data from global storage."""
        global_dir = self._get_global_dir()
        filepath = os.path.join(global_dir, f"{key}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def save_report(self, filename, content):
        """Save report to reports folder."""
        if not self.exists():
            self.init()
        
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        
        return {"success": True, "path": filepath}
