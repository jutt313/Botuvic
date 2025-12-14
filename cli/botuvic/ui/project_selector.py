"""
Project selection interface with arrow key navigation.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import os
import requests
import json

console = Console()

def select_project(user):
    """
    Show project selection menu.
    Returns selected project or None.
    """
    console.print("\n[bold cyan]📁 Select Project[/bold cyan]\n")
    
    # Check if in existing project directory
    current_dir = os.getcwd()
    botuvic_exists = os.path.exists(os.path.join(current_dir, ".botuvic"))
    
    if botuvic_exists:
        project_name = os.path.basename(current_dir)
        console.print(f"[green]✓[/green] Found existing project: [cyan]{project_name}[/cyan]")
        
        if Confirm.ask("Continue with this project?", default=True):
            return {
                "name": project_name,
                "path": current_dir,
                "existing": True
            }
    
    # Get user's projects from backend
    projects = get_user_projects(user)
    
    # Show project list
    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        if Confirm.ask("Create a new project?"):
            return create_new_project()
        return None
    
    # Display projects in a table
    table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Last Opened", style="dim")
    
    for i, project in enumerate(projects, 1):
        table.add_row(
            str(i),
            project['name'],
            project.get('path', 'N/A'),
            project.get('last_opened', 'N/A')
        )
    
    console.print(table)
    console.print()
    
    # Get user selection
    choices = [str(i) for i in range(1, len(projects) + 1)]
    choices.extend(['n', 'new'])
    
    selection = Prompt.ask(
        f"Select project (1-{len(projects)}) or 'n' for new",
        choices=choices,
        default="1"
    )
    
    if selection.lower() in ['n', 'new']:
        return create_new_project()
    else:
        try:
            idx = int(selection) - 1
            selected = projects[idx]
            return {
                "name": selected['name'],
                "path": selected.get('path', os.path.join(os.getcwd(), selected['name'])),
                "existing": True
            }
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")
            return None

def get_user_projects(user):
    """Get list of user's projects from backend."""
    try:
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        token = user.get('token')
        
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{backend_url}/api/projects/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            projects = response.json()
            return [
                {
                    "name": p.get('name', 'Untitled'),
                    "path": p.get('path', ''),
                    "last_opened": p.get('updated_at', '')
                }
                for p in projects
            ]
    except:
        pass
    
    # Fallback: scan for local projects
    return scan_local_projects()

def scan_local_projects():
    """Scan for local projects with .botuvic folder."""
    projects = []
    home = os.path.expanduser("~")
    common_dirs = [
        os.path.join(home, "projects"),
        os.path.join(home, "Documents", "projects"),
        os.path.join(home, "Desktop"),
        os.getcwd()
    ]
    
    for base_dir in common_dirs:
        if not os.path.exists(base_dir):
            continue
        
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                botuvic_path = os.path.join(item_path, ".botuvic")
                if os.path.exists(botuvic_path):
                    projects.append({
                        "name": item,
                        "path": item_path,
                        "last_opened": ""
                    })
    
    return projects[:10]  # Limit to 10

def create_new_project():
    """Create a new project."""
    console.print("\n[bold cyan]✨ Create New Project[/bold cyan]\n")
    
    name = Prompt.ask("Project name")
    
    # Suggest directory
    suggested_path = os.path.join(os.getcwd(), name)
    path = Prompt.ask("Project directory", default=suggested_path)
    
    # Create directory
    os.makedirs(path, exist_ok=True)
    
    console.print(f"[green]✓[/green] Created project directory: [cyan]{path}[/cyan]")
    
    return {
        "name": name,
        "path": path,
        "existing": False
    }

