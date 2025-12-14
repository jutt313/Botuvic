import os
from datetime import datetime

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class GitManager:
    """
    Handles all Git operations including commits, branches, and PR generation.
    """
    
    def __init__(self, llm_client, storage, project_dir):
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
        self.repo = None
        
        if GIT_AVAILABLE:
            try:
                self.repo = Repo(project_dir)
            except:
                # Not a git repo yet
                pass
    
    def initialize_repo(self):
        """Initialize git repository if not already initialized."""
        if not GIT_AVAILABLE:
            return {"success": False, "error": "GitPython not installed"}
        
        if self.repo:
            return {"success": True, "message": "Repo already initialized"}
        
        try:
            self.repo = Repo.init(self.project_dir)
            
            # Create .gitignore
            gitignore_content = """
node_modules/
__pycache__/
*.pyc
.env
.DS_Store
dist/
build/
*.log
"""
            gitignore_path = os.path.join(self.project_dir, '.gitignore')
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content.strip())
            
            # Initial commit
            self.repo.index.add(['.gitignore'])
            self.repo.index.commit("Initial commit")
            
            return {
                "success": True,
                "message": "Git repository initialized"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_commit_message(self, changes_summary=None):
        """
        Generate intelligent commit message based on changes.
        
        Args:
            changes_summary: Optional summary of changes
            
        Returns:
            Generated commit message
        """
        if not self.repo:
            return "Update files"
        
        # Get changed files
        try:
            changed_files = [item.a_path for item in self.repo.index.diff(None)]
            untracked_files = self.repo.untracked_files
            all_changes = changed_files + untracked_files
        except:
            all_changes = []
        
        # Load project context
        roadmap = self.storage.load("roadmap")
        progress = self.storage.load("progress")
        
        # Build prompt for commit message
        prompt_parts = []
        
        if changes_summary:
            prompt_parts.append(f"CHANGES: {changes_summary}")
        
        prompt_parts.append(f"\nFILES MODIFIED:")
        for file in all_changes[:10]:  # Limit to 10 files
            prompt_parts.append(f"- {file}")
        
        if len(all_changes) > 10:
            prompt_parts.append(f"... and {len(all_changes) - 10} more files")
        
        # Add project context
        if progress:
            current_phase = progress.get("current_phase", 1)
            prompt_parts.append(f"\nCURRENT PHASE: Phase {current_phase}")
            
            if roadmap:
                for phase in roadmap["phases"]:
                    if phase["phase_number"] == current_phase:
                        prompt_parts.append(f"PHASE NAME: {phase['name']}")
                        break
        
        prompt_parts.append("\nGenerate a concise, descriptive commit message:")
        
        # Get commit message from LLM
        messages = [
            {
                "role": "system",
                "content": "You are a developer writing git commit messages. Generate concise, descriptive commit messages following conventional commits format. Just output the commit message, nothing else."
            },
            {
                "role": "user",
                "content": "\n".join(prompt_parts)
            }
        ]
        
        response = self.llm.chat(messages)
        commit_message = response.get("content", "").strip()
        
        # Remove quotes if LLM added them
        commit_message = commit_message.strip('"\'')
        
        return commit_message
    
    def auto_commit(self, message=None, phase_number=None):
        """
        Automatically commit all changes.
        
        Args:
            message: Optional custom commit message
            phase_number: Optional phase number for context
            
        Returns:
            Commit info
        """
        if not GIT_AVAILABLE:
            return {"success": False, "error": "GitPython not installed"}
        
        if not self.repo:
            init_result = self.initialize_repo()
            if not init_result["success"]:
                return init_result
        
        try:
            # Stage all changes
            self.repo.git.add(A=True)
            
            # Generate commit message if not provided
            if not message:
                if phase_number:
                    summary = f"Complete Phase {phase_number}"
                else:
                    summary = None
                message = self.generate_commit_message(summary)
            
            # Create commit
            commit = self.repo.index.commit(message)
            
            return {
                "success": True,
                "commit_hash": commit.hexsha[:7],
                "message": message,
                "files_changed": len(commit.stats.files) if hasattr(commit, 'stats') else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_branch(self, branch_name):
        """Create a new git branch."""
        if not GIT_AVAILABLE:
            return {"success": False, "error": "GitPython not installed"}
        
        if not self.repo:
            return {"success": False, "error": "Not a git repository"}
        
        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            
            return {
                "success": True,
                "branch": branch_name,
                "message": f"Created and switched to branch '{branch_name}'"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_phase_branch(self, phase_number, phase_name):
        """Create a branch for a new phase."""
        # Clean phase name for branch
        clean_name = phase_name.lower().replace(' ', '-').replace('/', '-')
        branch_name = f"phase-{phase_number}-{clean_name}"
        
        return self.create_branch(branch_name)
    
    def generate_pr_description(self, phase_number=None):
        """
        Generate pull request description.
        
        Args:
            phase_number: Optional phase number for context
            
        Returns:
            PR title and description
        """
        roadmap = self.storage.load("roadmap")
        progress = self.storage.load("progress")
        
        if not roadmap or not progress:
            return {
                "title": "Update",
                "description": "Various updates"
            }
        
        # Get phase info
        phase_info = None
        phase_progress = None
        
        if phase_number:
            for phase in roadmap["phases"]:
                if phase["phase_number"] == phase_number:
                    phase_info = phase
                    break
            
            for phase in progress["phases"]:
                if phase["phase_number"] == phase_number:
                    phase_progress = phase
                    break
        
        # Build prompt
        prompt_parts = []
        
        if phase_info:
            prompt_parts.append(f"PHASE: {phase_info['name']}")
            prompt_parts.append(f"DESCRIPTION: {phase_info.get('description', '')}")
            prompt_parts.append(f"\nCOMPLETED TASKS:")
            
            for task in phase_info["tasks"]:
                # Check if task is complete
                if phase_progress:
                    for prog_task in phase_progress["tasks"]:
                        if prog_task["task_number"] == task["task_number"] and prog_task["status"] == "complete":
                            prompt_parts.append(f"- {task['name']}")
                            break
        
        # Get changed files
        if self.repo:
            try:
                changed_files = [item.a_path for item in self.repo.index.diff('HEAD')]
                prompt_parts.append(f"\nFILES CHANGED:")
                for file in changed_files[:15]:
                    prompt_parts.append(f"- {file}")
            except:
                pass
        
        prompt_parts.append("\nGenerate a pull request title and description:")
        
        # Get PR description from LLM
        messages = [
            {
                "role": "system",
                "content": """Generate a pull request title and description.

Format:

TITLE: [Concise title]

DESCRIPTION:

## Summary

[What was accomplished]

## Changes

- [Key change 1]
- [Key change 2]
...

## Testing

[How to test these changes]
"""
            },
            {
                "role": "user",
                "content": "\n".join(prompt_parts)
            }
        ]
        
        response = self.llm.chat(messages)
        pr_text = response.get("content", "")
        
        # Parse title and description
        title = ""
        description = ""
        
        lines = pr_text.split('\n')
        in_description = False
        
        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                in_description = True
            elif in_description:
                description += line + "\n"
        
        return {
            "title": title or "Phase completion",
            "description": description.strip()
        }
    
    def get_status(self):
        """Get git repository status."""
        if not GIT_AVAILABLE:
            return {"initialized": False, "error": "GitPython not installed"}
        
        if not self.repo:
            return {"initialized": False}
        
        try:
            return {
                "initialized": True,
                "branch": self.repo.active_branch.name,
                "modified_files": len([item.a_path for item in self.repo.index.diff(None)]),
                "untracked_files": len(self.repo.untracked_files),
                "commits": len(list(self.repo.iter_commits())),
                "last_commit": self.repo.head.commit.message.strip() if self.repo.head.commit else None
            }
        except Exception as e:
            return {
                "initialized": True,
                "error": str(e)
            }

