"""Configuration for BOTUVIC CLI"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env from multiple possible locations
possible_env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # Root project .env
    Path.cwd() / ".env",  # Current directory
    Path.cwd().parent / ".env",  # Parent directory
    Path.home() / ".botuvic" / ".env",  # User config
]

for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    # Try loading from current directory anyway
    load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model settings
DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 4000
TEMPERATURE = 0.7

# Storage settings
BOTUVIC_DIR = ".botuvic"
REPORTS_DIR = "reports"

# Scan settings
IGNORED_DIRS = ['node_modules', '.git', 'venv', '__pycache__', 'dist', 'build', '.botuvic']
CODE_EXTENSIONS = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.php', '.rb']

# User config management
class Config:
    """User configuration manager"""
    
    def __init__(self):
        self.config_file = Path.home() / ".botuvic" / "config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self):
        """Load config from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {"user": {"email": None, "token": None}}
    
    def _save_config(self):
        """Save config to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set_user_token(self, email: str, token: str):
        """Set user authentication token"""
        if "user" not in self.config:
            self.config["user"] = {}
        self.config["user"]["email"] = email
        self.config["user"]["token"] = token
        self._save_config()
    
    def get_user_token(self):
        """Get user token"""
        return self.config.get("user", {}).get("token")
    
    def set_selected_project(self, project: dict):
        """Set selected project"""
        if "selected_project" not in self.config:
            self.config["selected_project"] = {}
        self.config["selected_project"] = project
        self._save_config()
    
    def get_selected_project(self):
        """Get selected project"""
        return self.config.get("selected_project")

# Global config instance
config = Config()
