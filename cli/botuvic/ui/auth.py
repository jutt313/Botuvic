"""
User authentication interface.
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import requests
import os
import json
from pathlib import Path

console = Console()

def authenticate_user():
    """
    Authenticate user with email/password.
    Returns user dict or None.
    """
    console.print("\n[bold cyan]🔐 Authentication[/bold cyan]\n")
    
    # Check for saved session
    saved_token = load_saved_token()
    if saved_token:
        if Prompt.ask("Use saved session?", choices=["y", "n"], default="y") == "y":
            user = verify_token(saved_token)
            if user:
                return user
    
    # Login
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    
    # Authenticate with backend API
    user = login(email, password)
    
    if user:
        save_token(user.get('token') or user.get('access_token'))
        return user
    
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

