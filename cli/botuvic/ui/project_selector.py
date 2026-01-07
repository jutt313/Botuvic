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
    Smart project detection and selection.
    Returns selected project dict or None.
    """
    console.print("\n[bold #A855F7]📁 Project Detection[/bold #A855F7]\n")

    current_dir = os.getcwd()
    home_dir = os.path.expanduser("~")

    # SCENARIO 1: Check if current directory is already registered as a project
    console.print(f"[dim]Checking current directory: {current_dir}[/dim]")
    registered_project = check_path_registered(current_dir, user)

    if registered_project:
        # Current directory is registered, use it directly
        console.print(f"[green]✓[/green] Found registered project: [#A855F7]{registered_project['name']}[/#A855F7]")
        console.print(f"[dim]Status: {registered_project.get('status', 'new')}[/dim]\n")
        return registered_project

    # SCENARIO 2: User is in a specific folder (not home directory)
    if current_dir != home_dir and not current_dir.startswith(home_dir + os.sep + '.'):
        # User is in a specific directory that's not registered
        folder_name = os.path.basename(current_dir)
        console.print(f"[yellow]This directory is not registered as a project.[/yellow]")

        if Confirm.ask(f"Register '{folder_name}' as a new project?", default=True):
            return register_current_directory(user, current_dir)

    # SCENARIO 3: User is in home or generic directory - show project list
    console.print("[#A855F7]You're in the home directory. Please select a project:[/#A855F7]\n")

    # Get user's projects from backend
    projects = get_user_projects(user)

    # Show project list
    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        if Confirm.ask("Create a new project in a specific directory?"):
            return create_new_project(user)
        return None

    # Display projects in a table
    table = Table(title="Your Projects", show_header=True, header_style="bold #A855F7")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="#C084FC")
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Path", style="dim")

    for i, project in enumerate(projects, 1):
        status = project.get('status', 'new')
        status_emoji = "🆕" if status == "new" else "🔨"
        table.add_row(
            str(i),
            project['name'],
            f"{status_emoji} {status}",
            project.get('path', 'N/A')
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
        return create_new_project(user)
    else:
        try:
            idx = int(selection) - 1
            selected = projects[idx]

            # CD into the selected project directory
            project_path = selected.get('path')
            if project_path and os.path.exists(project_path):
                os.chdir(project_path)
                console.print(f"\n[green]✓[/green] Changed directory to: [#A855F7]{project_path}[/#A855F7]")

            return selected
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")
            return None

def check_path_registered(path, user):
    """Check if a path is already registered as a project in backend."""
    try:
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        token = user.get('token')

        if not token:
            console.print("[dim]No token available[/dim]")
            return None

        headers = {"Authorization": f"Bearer {token}"}

        console.print(f"[dim]Checking backend for path: {path}[/dim]")

        response = requests.get(
            f"{backend_url}/api/projects/by-path",
            params={"path": path},
            headers=headers,
            timeout=5
        )

        console.print(f"[dim]Backend check response: {response.status_code}[/dim]")

        if response.status_code == 200:
            project = response.json()
            console.print(f"[dim]Found project: {project.get('name')}[/dim]")
            return {
                "id": project.get('id'),
                "name": project.get('name', 'Untitled'),
                "path": project.get('path', path),
                "status": project.get('status', 'new'),
                "existing": True
            }
        elif response.status_code == 404:
            console.print(f"[dim]Project not found (404)[/dim]")
        else:
            console.print(f"[dim]Error: {response.status_code} - {response.text}[/dim]")
    except Exception as e:
        console.print(f"[dim]Exception checking path: {e}[/dim]")

    return None

def register_current_directory(user, path):
    """Register the current directory as a new project."""
    try:
        folder_name = os.path.basename(path)

        # Ask for project details
        console.print(f"\n[bold #A855F7]📝 Register Project[/bold #A855F7]\n")
        name = Prompt.ask("Project name", default=folder_name)
        description = Prompt.ask("Description (optional)", default="")

        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        token = user.get('token')

        if not token:
            console.print("[red]Not authenticated[/red]")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        console.print(f"[dim]Registering with backend...[/dim]")

        response = requests.post(
            f"{backend_url}/api/projects/",
            headers=headers,
            json={
                "name": name,
                "path": path,
                "description": description,
                "status": "new"
            },
            timeout=10
        )

        console.print(f"[dim]Backend response: {response.status_code}[/dim]")

        if response.status_code == 200:
            project = response.json()
            console.print(f"\n[green]✓[/green] Project registered successfully!")
            console.print(f"[dim]Project ID: {project.get('id')}[/dim]")
            return {
                "id": project.get('id'),
                "name": project.get('name'),
                "path": project.get('path'),
                "status": project.get('status', 'new'),
                "existing": False
            }
        else:
            console.print(f"[red]Failed to register project[/red]")
            console.print(f"[red]Status: {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")
            return None
    except Exception as e:
        console.print(f"[red]Error registering project: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
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
                    "id": p.get('id'),
                    "name": p.get('name', 'Untitled'),
                    "path": p.get('path', ''),
                    "status": p.get('status', 'new'),
                    "existing": True
                }
                for p in projects
            ]
    except:
        pass

    return []

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

def create_new_project(user):
    """Create a new project by specifying a directory."""
    console.print("\n[bold #A855F7]✨ Create New Project[/bold #A855F7]\n")

    name = Prompt.ask("Project name")

    # Ask for directory path
    current_dir = os.getcwd()
    suggested_path = os.path.join(current_dir, name)
    path = Prompt.ask("Project directory path", default=suggested_path)

    # Expand path
    path = os.path.abspath(os.path.expanduser(path))

    # Create directory if it doesn't exist
    if not os.path.exists(path):
        if Confirm.ask(f"Directory doesn't exist. Create it?", default=True):
            os.makedirs(path, exist_ok=True)
            console.print(f"[green]✓[/green] Created directory: [#A855F7]{path}[/#A855F7]")
        else:
            console.print("[yellow]Project creation cancelled[/yellow]")
            return None

    description = Prompt.ask("Description (optional)", default="")

    # Register with backend
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    token = user.get('token')

    if token:
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{backend_url}/api/projects/",
                headers=headers,
                json={
                    "name": name,
                    "path": path,
                    "description": description,
                    "status": "new"
                },
                timeout=10
            )

            if response.status_code == 200:
                project = response.json()
                console.print(f"\n[green]✓[/green] Project registered successfully!")

                # CD into the new project
                os.chdir(path)
                console.print(f"[green]✓[/green] Changed directory to: [cyan]{path}[/cyan]")

                return {
                    "id": project.get('id'),
                    "name": project.get('name'),
                    "path": project.get('path'),
                    "status": project.get('status', 'new'),
                    "existing": False
                }
        except Exception as e:
            console.print(f"[yellow]Warning: Could not register with backend: {e}[/yellow]")

    # Fallback: return project without backend registration
    return {
        "name": name,
        "path": path,
        "status": "new",
        "existing": False
    }

