"""
User authentication interface.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import requests
import os
import json
import webbrowser
import time
import uuid
from pathlib import Path

console = Console()

def authenticate_user():
    """
    Authenticate user via browser-based login.
    Returns user dict or None.
    """
    console.print("\n[bold #A855F7]🔐 Authentication[/bold #A855F7]\n")

    # Check for saved token first
    saved_token = load_saved_token()
    if saved_token:
        console.print("[dim]Checking saved session...[/dim]")
        user = verify_token(saved_token)
        if user:
            console.print("[green]✓[/green] Already logged in!\n")
            return user
        else:
            console.print("[yellow]Saved session expired. Please login again.[/yellow]\n")

    # Browser-based login
    console.print("[bold]Press Enter to login via browser...[/bold]")
    console.input()

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    # Get frontend URL
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    login_url = f"{frontend_url}/login?cli_session={session_id}"

    # Try to open browser
    console.print("\n[#A855F7]Opening browser for login...[/#A855F7]")
    try:
        if webbrowser.open(login_url):
            console.print("[green]✓[/green] Browser opened successfully")
        else:
            raise Exception("Failed to open browser")
    except:
        console.print("[yellow]⚠️  Could not open browser automatically[/yellow]")
        console.print(f"\n[bold]Please open this URL in your browser:[/bold]")
        console.print(f"[#A855F7]{login_url}[/#A855F7]\n")

    # Poll for token
    console.print("\n[dim]Waiting for login...[/dim]")
    user = poll_for_token(session_id)

    if user:
        save_token(user.get('token'))
        console.print("\n[green]✓[/green] Login successful!\n")
        return user

    console.print("\n[red]Login failed or timed out[/red]")
    return None

def poll_for_token(session_id, timeout=300, interval=2):
    """
    Poll backend for CLI session token.
    Timeout in seconds (default 5 minutes).
    Returns user dict or None.
    """
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    start_time = time.time()

    with console.status("[#A855F7]Waiting for browser login...[/#A855F7]", spinner="dots") as status:
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{backend_url}/api/auth/cli-session/{session_id}",
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("user", {}).get("id"),
                        "name": data.get("user", {}).get("name", "User"),
                        "email": data.get("user", {}).get("email"),
                        "token": data.get("token")
                    }
                elif response.status_code == 404:
                    # Session not found yet, keep polling
                    time.sleep(interval)
                    continue
                else:
                    # Some other error
                    console.print(f"[yellow]Warning: {response.status_code}[/yellow]")
                    time.sleep(interval)
                    continue

            except requests.exceptions.ConnectionError:
                console.print("[red]Cannot connect to backend. Make sure it's running.[/red]")
                return None
            except Exception as e:
                console.print(f"[yellow]Error: {e}[/yellow]")
                time.sleep(interval)
                continue

    return None

def load_saved_token():
    """Load saved auth token."""
    token_file = os.path.expanduser("~/.botuvic/token")
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return None

def save_token(token):
    """Save auth token."""
    token_dir = os.path.expanduser("~/.botuvic")
    os.makedirs(token_dir, exist_ok=True)
    token_file = os.path.join(token_dir, "token")
    with open(token_file, 'w') as f:
        f.write(token)

def verify_token(token):
    """Verify saved token with backend."""
    try:
        # Try to get user info from backend
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{backend_url}/api/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "id": data.get("id"),
                "name": data.get("name", "User"),
                "email": data.get("email"),
                "token": token
            }
    except:
        pass
    
    return None

def login(email, password):
    """Login with credentials via backend API."""
    try:
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        response = requests.post(
            f"{backend_url}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "id": data.get("user", {}).get("id"),
                "name": data.get("user", {}).get("name", email.split('@')[0].title()),
                "email": email,
                "token": data.get("access_token")
            }
        else:
            console.print(f"[red]Login failed: {response.text}[/red]")
            return None
    except requests.exceptions.ConnectionError:
        console.print("[yellow]⚠️  Backend not available. Using offline mode.[/yellow]")
        # Fallback to mock login for development
        return {
            "id": "user123",
            "name": email.split('@')[0].title(),
            "email": email,
            "token": "offline_token"
        }
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

