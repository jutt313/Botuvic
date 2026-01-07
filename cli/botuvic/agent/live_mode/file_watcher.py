"""
File Watcher for Phase 10 Live Development Mode.
Monitors project files for changes and triggers analysis.
"""

import os
import time
from pathlib import Path
from typing import Callable, List, Dict, Any
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from rich.console import Console

console = Console()


class CodeFileHandler(FileSystemEventHandler):
    """Handler for code file changes."""
    
    def __init__(self, callback: Callable, project_dir: str):
        """
        Initialize handler.
        
        Args:
            callback: Function to call when file changes (receives file_path, event_type)
            project_dir: Root project directory
        """
        self.callback = callback
        self.project_dir = project_dir
        self.last_modified = {}  # Track last modification time to debounce
        self.debounce_seconds = 1  # Wait 1 second before processing
        
        # File extensions to watch
        self.watched_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
            '.java', '.go', '.rs', '.rb', '.php', '.swift', '.kt',
            '.html', '.css', '.scss', '.sass', '.json', '.yaml', '.yml',
            '.sql', '.graphql', '.md'
        }
        
        # Directories to ignore
        self.ignored_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
            '.botuvic', 'logs'
        }
    
    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        path = Path(file_path)
        
        # Check extension
        if path.suffix not in self.watched_extensions:
            return False
        
        # Check if in ignored directory
        parts = path.parts
        for ignored in self.ignored_dirs:
            if ignored in parts:
                return False
        
        return True
    
    def is_debounced(self, file_path: str) -> bool:
        """Check if enough time has passed since last modification."""
        now = time.time()
        last_time = self.last_modified.get(file_path, 0)
        
        if now - last_time < self.debounce_seconds:
            return True
        
        self.last_modified[file_path] = now
        return False
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return
        
        if not self.should_process_file(event.src_path):
            return
        
        if self.is_debounced(event.src_path):
            return
        
        # Get relative path
        rel_path = os.path.relpath(event.src_path, self.project_dir)
        self.callback(rel_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation."""
        if event.is_directory:
            return
        
        if not self.should_process_file(event.src_path):
            return
        
        # Get relative path
        rel_path = os.path.relpath(event.src_path, self.project_dir)
        self.callback(rel_path, 'created')


class FileWatcher:
    """
    Watches project files for changes in real-time.
    Part of Phase 10 Live Development Mode.
    """
    
    def __init__(self, project_dir: str, on_change_callback: Callable):
        """
        Initialize file watcher.
        
        Args:
            project_dir: Root directory to watch
            on_change_callback: Function to call when files change
        """
        self.project_dir = project_dir
        self.on_change_callback = on_change_callback
        self.observer = None
        self.is_watching = False
        
        # Directories to watch
        self.watch_dirs = ['frontend', 'backend', 'database', 'cli', 'mobile']
    
    def start(self) -> Dict[str, Any]:
        """
        Start watching files.
        
        Returns:
            Status dict
        """
        if self.is_watching:
            return {"success": False, "error": "Already watching"}
        
        try:
            # Create observer
            self.observer = Observer()
            
            # Set up handler
            handler = CodeFileHandler(self._on_file_change, self.project_dir)
            
            # Watch each directory
            watched_count = 0
            for dir_name in self.watch_dirs:
                dir_path = os.path.join(self.project_dir, dir_name)
                if os.path.exists(dir_path):
                    self.observer.schedule(handler, dir_path, recursive=True)
                    watched_count += 1
            
            # Start observer
            self.observer.start()
            self.is_watching = True
            
            console.print(f"[green]✓[/green] File watcher started (monitoring {watched_count} directories)")
            
            return {
                "success": True,
                "watching": True,
                "directories": watched_count
            }
        
        except Exception as e:
            console.print(f"[red]✗ Failed to start file watcher: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop watching files.
        
        Returns:
            Status dict
        """
        if not self.is_watching:
            return {"success": False, "error": "Not watching"}
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self.is_watching = False
            console.print("[dim]File watcher stopped[/dim]")
            
            return {"success": True, "watching": False}
        
        except Exception as e:
            console.print(f"[red]✗ Failed to stop file watcher: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def _on_file_change(self, file_path: str, event_type: str):
        """
        Internal handler for file changes.
        
        Args:
            file_path: Relative path to changed file
            event_type: 'modified' or 'created'
        """
        # Call the user-provided callback
        try:
            self.on_change_callback(file_path, event_type)
        except Exception as e:
            console.print(f"[red]Error processing file change: {e}[/red]")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current watcher status.
        
        Returns:
            Status dict
        """
        return {
            "watching": self.is_watching,
            "directories": self.watch_dirs,
            "project_dir": self.project_dir
        }

