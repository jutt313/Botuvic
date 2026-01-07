"""Code scanning function"""

import os

def scan_project(project_dir):
    """
    Scan ALL files in project (like Cursor does).
    
    Args:
        project_dir: Project directory path
        
    Returns:
        Dict with file list and analysis
    """
    # Directories to ignore
    ignore_dirs = ['node_modules', '.git', 'venv', '__pycache__', 'dist', 'build', 
                   '.botuvic', '.DS_Store', 'DerivedData', 'Pods', '.swiftpm',
                   'xcuserdata', '.idea', '.vscode', '.vs', '.xcode']
    
    # Binary file extensions to skip (can't read as text)
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.pdf',
                        '.zip', '.tar', '.gz', '.dmg', '.app', '.framework',
                        '.a', '.o', '.dylib', '.so', '.dll', '.exe',
                        '.xcassets', '.imageset', '.lproj', '.ttf', '.otf', '.woff'}
    
    files_found = []
    
    # Walk through all files
    for root, dirs, files in os.walk(project_dir):
            # Skip ignored directories
        dirs[:] = [d for d in dirs if not any(ignored in os.path.join(root, d) for ignored in ignore_dirs)]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            
            # Skip if in ignored directory
            if any(ignored in filepath for ignored in ignore_dirs):
                continue
            
            # Get file extension
            ext = os.path.splitext(filename)[1].lower()
            
            # Skip binary files
            if ext in binary_extensions or filename.startswith('.'):
                continue
            
            # Get relative path
            rel_path = os.path.relpath(filepath, project_dir)
            
            # Try to read file (skip if binary or too large)
            try:
                file_size = os.path.getsize(filepath)
                
                # Skip files larger than 1MB (likely binary)
                if file_size > 1024 * 1024:
                    files_found.append({
                        "path": rel_path,
                        "extension": ext or "no extension",
                        "lines": 0,
                        "size": file_size,
                        "readable": False,
                        "note": "File too large or binary"
                    })
                    continue
                
                # Try to read as text
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.count('\n') + 1
                    
                    files_found.append({
                        "path": rel_path,
                        "extension": ext or "no extension",
                        "lines": lines,
                        "size": file_size,
                        "readable": True
                    })
            except (UnicodeDecodeError, PermissionError, IsADirectoryError):
                # Skip binary files or unreadable files
                try:
                    file_size = os.path.getsize(filepath)
            except:
                    file_size = 0
                    
                files_found.append({
                    "path": rel_path,
                    "extension": ext or "no extension",
                    "lines": 0,
                    "size": file_size,
                    "readable": False,
                    "note": "Binary or unreadable file"
                })
                continue
            except Exception:
                continue
    
    # Group by extension for summary
    extensions_found = {}
    for f in files_found:
        ext = f.get("extension", "no extension")
        if ext not in extensions_found:
            extensions_found[ext] = 0
        extensions_found[ext] += 1
    
    return {
        "total_files": len(files_found),
        "files": files_found,
        "extensions_found": list(extensions_found.keys()),
        "extension_counts": extensions_found,
        "readable_files": len([f for f in files_found if f.get("readable", False)])
    }

