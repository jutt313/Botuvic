"""Project structure creation function"""

import os

def create(structure, project_dir):
    """
    Create project folder structure and files.
    
    Args:
        structure: Dict defining folders and files
        project_dir: Base project directory
        
    Returns:
        Dict with created items
    """
    created_folders = []
    created_files = []
    
    def create_recursive(struct, base_path):
        for name, content in struct.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # It's a folder
                os.makedirs(path, exist_ok=True)
                created_folders.append(os.path.relpath(path, project_dir))
                create_recursive(content, path)
            else:
                # It's a file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content or "")
                created_files.append(os.path.relpath(path, project_dir))
    
    create_recursive(structure, project_dir)
    
    return {
        "folders_created": len(created_folders),
        "files_created": len(created_files),
        "folders": created_folders,
        "files": created_files
    }

