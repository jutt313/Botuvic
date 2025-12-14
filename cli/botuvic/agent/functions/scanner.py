"""Code scanning function"""

import os
import glob

def scan_project(project_dir):
    """
    Scan all code files in project.
    
    Args:
        project_dir: Project directory path
        
    Returns:
        Dict with file list and analysis
    """
    # File extensions to scan
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs']
    
    # Directories to ignore
    ignore_dirs = ['node_modules', '.git', 'venv', '__pycache__', 'dist', 'build', '.botuvic']
    
    files_found = []
    
    for ext in extensions:
        pattern = os.path.join(project_dir, '**', f'*{ext}')
        for filepath in glob.glob(pattern, recursive=True):
            # Skip ignored directories
            if any(ignored in filepath for ignored in ignore_dirs):
                continue
            
            # Get relative path
            rel_path = os.path.relpath(filepath, project_dir)
            
            # Read file
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.count('\n') + 1
                    
                    files_found.append({
                        "path": rel_path,
                        "extension": ext,
                        "lines": lines,
                        "size": os.path.getsize(filepath)
                    })
            except:
                continue
    
    return {
        "total_files": len(files_found),
        "files": files_found,
        "extensions_found": list(set([f["extension"] for f in files_found]))
    }

