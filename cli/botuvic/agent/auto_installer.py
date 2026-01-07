"""
Auto-Installer Module for BOTUVIC.
Handles automatic installation and setup of backend and frontend with user approval.
"""

import os
import subprocess
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel

console = Console()


class AutoInstaller:
    """Automatic installer for backend and frontend."""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def auto_install_backend(self, backend_name: str) -> Dict[str, Any]:
        """
        Auto-install backend dependencies with user approval.

        Detects package manager and runs install command.
        """
        backend_path = os.path.join(self.project_dir, "backend")

        if not os.path.exists(backend_path):
            return {"success": False, "error": "Backend folder not found"}

        # Detect backend type and package manager
        if "node" in backend_name or "express" in backend_name:
            return self._install_nodejs_backend(backend_path)
        elif "python" in backend_name or "fastapi" in backend_name or "django" in backend_name or "flask" in backend_name:
            return self._install_python_backend(backend_path, backend_name)
        elif "go" in backend_name or "gin" in backend_name:
            return self._install_go_backend(backend_path)
        elif "ruby" in backend_name or "rails" in backend_name:
            return self._install_ruby_backend(backend_path)
        elif "java" in backend_name or "spring" in backend_name:
            return self._install_java_backend(backend_path)
        elif "php" in backend_name or "laravel" in backend_name:
            return self._install_php_backend(backend_path)
        elif "dotnet" in backend_name or ".net" in backend_name:
            return self._install_dotnet_backend(backend_path)
        else:
            return {"success": False, "error": "Unknown backend type"}

    def _install_nodejs_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install Node.js/Express backend."""
        console.print("\n[bold cyan]Node.js Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Install npm dependencies",
                "command": "npm install",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, "Node.js Backend")

    def _install_python_backend(self, backend_path: str, backend_name: str) -> Dict[str, Any]:
        """Install Python backend (FastAPI/Django/Flask)."""
        console.print(f"\n[bold cyan]Python Backend Auto-Install ({backend_name})[/bold cyan]\n")

        # Check if virtual environment exists
        venv_exists = os.path.exists(os.path.join(backend_path, "venv"))

        commands = []

        if not venv_exists:
            commands.append({
                "description": "Create Python virtual environment",
                "command": "python3 -m venv venv",
                "cwd": backend_path
            })

        commands.append({
            "description": "Install Python packages",
            "command": "source venv/bin/activate && pip install -r requirements.txt" if os.name != 'nt' else "venv\\Scripts\\activate && pip install -r requirements.txt",
            "cwd": backend_path
        })

        return self._execute_install_commands(commands, "Python Backend")

    def _install_go_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install Go/Gin backend."""
        console.print("\n[bold cyan]Go Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Download Go dependencies",
                "command": "go mod download",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, "Go Backend")

    def _install_ruby_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install Ruby on Rails backend."""
        console.print("\n[bold cyan]Ruby on Rails Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Install Ruby gems",
                "command": "bundle install",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, "Ruby Backend")

    def _install_java_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install Java/Spring Boot backend."""
        console.print("\n[bold cyan]Java Spring Boot Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Download Maven dependencies",
                "command": "mvn clean install",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, "Java Backend")

    def _install_php_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install PHP/Laravel backend."""
        console.print("\n[bold cyan]PHP Laravel Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Install Composer dependencies",
                "command": "composer install",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, "PHP Backend")

    def _install_dotnet_backend(self, backend_path: str) -> Dict[str, Any]:
        """Install .NET backend."""
        console.print("\n[bold cyan].NET Backend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Restore .NET packages",
                "command": "dotnet restore",
                "cwd": backend_path
            }
        ]

        return self._execute_install_commands(commands, ".NET Backend")

    def auto_install_frontend(self, frontend_name: str) -> Dict[str, Any]:
        """
        Auto-install frontend dependencies with user approval.
        """
        frontend_path = os.path.join(self.project_dir, "frontend")

        if not os.path.exists(frontend_path):
            return {"success": False, "error": "Frontend folder not found"}

        # Most frontends use npm/yarn
        if any(fw in frontend_name for fw in ["react", "next", "vue", "angular", "svelte", "electron"]):
            return self._install_npm_frontend(frontend_path, frontend_name)
        elif "flutter" in frontend_name:
            return self._install_flutter_frontend(frontend_path)
        elif "react native" in frontend_name or "react-native" in frontend_name:
            return self._install_react_native_frontend(frontend_path)
        else:
            return self._install_npm_frontend(frontend_path, frontend_name)

    def _install_npm_frontend(self, frontend_path: str, frontend_name: str) -> Dict[str, Any]:
        """Install npm-based frontend (React, Next, Vue, Angular, Svelte, Electron)."""
        console.print(f"\n[bold cyan]{frontend_name} Frontend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Install npm dependencies",
                "command": "npm install",
                "cwd": frontend_path
            }
        ]

        return self._execute_install_commands(commands, f"{frontend_name} Frontend")

    def _install_flutter_frontend(self, frontend_path: str) -> Dict[str, Any]:
        """Install Flutter frontend."""
        console.print("\n[bold cyan]Flutter Frontend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Get Flutter packages",
                "command": "flutter pub get",
                "cwd": frontend_path
            }
        ]

        return self._execute_install_commands(commands, "Flutter Frontend")

    def _install_react_native_frontend(self, frontend_path: str) -> Dict[str, Any]:
        """Install React Native frontend."""
        console.print("\n[bold cyan]React Native Frontend Auto-Install[/bold cyan]\n")

        commands = [
            {
                "description": "Install npm dependencies",
                "command": "npm install",
                "cwd": frontend_path
            },
            {
                "description": "Install iOS pods (macOS only)",
                "command": "cd ios && pod install && cd ..",
                "cwd": frontend_path,
                "optional": True
            }
        ]

        return self._execute_install_commands(commands, "React Native Frontend")

    def auto_start_servers(self, backend_name: str, frontend_name: str) -> Dict[str, Any]:
        """
        Auto-start backend and frontend servers with user approval.
        """
        console.print("\n[bold green]Ready to start servers![/bold green]\n")

        # Ask if user wants to start servers
        # Skip in non-interactive mode or EOF
        import os
        import sys
        if os.getenv("BOTUVIC_NON_INTERACTIVE", "").lower() == "true" or not sys.stdin.isatty():
            response = "n"  # Skip server startup in non-interactive mode
            console.print("[dim]Skipping server startup (non-interactive mode)[/dim]")
        else:
            try:
                response = console.input("[bold]Start backend and frontend servers? (y/n):[/bold] ").strip().lower()
            except EOFError:
                response = "n"
                console.print("[dim]Skipping (non-interactive)[/dim]")

        if response != 'y' and response != 'yes':
            console.print("[yellow]Skipped server startup[/yellow]")
            return {"success": True, "started": False}

        console.print("\n[bold]Starting servers in background...[/bold]\n")
        console.print("[dim]Backend will run on: http://localhost:8000[/dim]")
        console.print("[dim]Frontend will run on: http://localhost:3000[/dim]\n")

        # Start backend
        backend_path = os.path.join(self.project_dir, "backend")
        backend_cmd = self._get_backend_start_command(backend_name)

        # Start frontend
        frontend_path = os.path.join(self.project_dir, "frontend")
        frontend_cmd = self._get_frontend_start_command(frontend_name)

        try:
            # Start backend in background
            console.print(f"[green]✓[/green] Starting backend: {backend_cmd}")
            subprocess.Popen(
                backend_cmd,
                shell=True,
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Start frontend in background
            console.print(f"[green]✓[/green] Starting frontend: {frontend_cmd}")
            subprocess.Popen(
                frontend_cmd,
                shell=True,
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            console.print("\n[bold green]✓ Servers started![/bold green]")
            console.print("\n[bold cyan]Open your browser:[/bold cyan]")
            console.print("  Frontend: http://localhost:3000")
            console.print("  Backend:  http://localhost:8000\n")

            console.print("[dim]Press Ctrl+C to stop servers[/dim]\n")

            return {"success": True, "started": True, "backend_url": "http://localhost:8000", "frontend_url": "http://localhost:3000"}

        except Exception as e:
            console.print(f"[red]✗ Error starting servers: {str(e)}[/red]")
            return {"success": False, "error": str(e)}

    def _get_backend_start_command(self, backend_name: str) -> str:
        """Get the start command for backend."""
        if "node" in backend_name or "express" in backend_name:
            return "npm run dev"
        elif "fastapi" in backend_name:
            return "source venv/bin/activate && uvicorn main:app --reload --port 8000"
        elif "django" in backend_name:
            return "source venv/bin/activate && python manage.py runserver 8000"
        elif "flask" in backend_name:
            return "source venv/bin/activate && python app.py"
        elif "go" in backend_name or "gin" in backend_name:
            return "go run main.go"
        elif "ruby" in backend_name or "rails" in backend_name:
            return "bundle exec rails server -p 8000"
        elif "java" in backend_name or "spring" in backend_name:
            return "mvn spring-boot:run"
        elif "php" in backend_name or "laravel" in backend_name:
            return "php artisan serve --port=8000"
        elif "dotnet" in backend_name or ".net" in backend_name:
            return "dotnet run"
        else:
            return "npm run dev"

    def _get_frontend_start_command(self, frontend_name: str) -> str:
        """Get the start command for frontend."""
        if "next" in frontend_name:
            return "npm run dev"
        elif "react" in frontend_name and "native" not in frontend_name:
            return "npm run dev"
        elif "vue" in frontend_name:
            return "npm run dev"
        elif "angular" in frontend_name:
            return "ng serve --port 3000"
        elif "svelte" in frontend_name:
            return "npm run dev"
        elif "electron" in frontend_name:
            return "npm start"
        elif "flutter" in frontend_name:
            return "flutter run -d chrome"
        elif "react native" in frontend_name or "react-native" in frontend_name:
            return "npm start"
        else:
            return "npm run dev"

    def _execute_install_commands(self, commands: List[Dict], project_type: str) -> Dict[str, Any]:
        """Execute installation commands with user approval."""
        results = []

        for cmd_info in commands:
            description = cmd_info["description"]
            command = cmd_info["command"]
            cwd = cmd_info.get("cwd", self.project_dir)
            optional = cmd_info.get("optional", False)

            # Show command to user
            console.print(f"\n[yellow]Command:[/yellow] {command}")
            console.print(f"[dim]{description}[/dim]")

            # Ask for approval (skip in non-interactive mode or EOF)
            import os
            import sys
            if os.getenv("BOTUVIC_NON_INTERACTIVE", "").lower() == "true" or not sys.stdin.isatty():
                response = "n"  # Skip auto-install in non-interactive mode
                console.print("[dim]Skipping dependency installation (non-interactive mode)[/dim]")
            else:
                try:
                    response = console.input("\n[bold]Run this command? (y/n):[/bold] ").strip().lower()
                except EOFError:
                    response = "n"
                    console.print("[dim]Skipping (non-interactive)[/dim]")

            if response == 'y' or response == 'yes':
                try:
                    # Execute command
                    console.print(f"[dim]Installing...[/dim]")
                    result = subprocess.run(
                        command,
                        shell=True,
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout
                    )

                    if result.returncode == 0:
                        console.print(f"[green]✓ Success![/green]")
                        results.append({"command": command, "success": True})
                    else:
                        if optional:
                            console.print(f"[yellow]⚠ Optional command failed, continuing...[/yellow]")
                            results.append({"command": command, "success": False, "optional": True})
                        else:
                            console.print(f"[red]✗ Error:[/red] {result.stderr}")
                            results.append({"command": command, "success": False, "error": result.stderr})
                            console.print("[red]Installation failed. Please fix errors and try again.[/red]")
                            return {"success": False, "project_type": project_type, "results": results}

                except subprocess.TimeoutExpired:
                    console.print("[red]✗ Command timed out (5 minutes)[/red]")
                    results.append({"command": command, "success": False, "error": "Timeout"})
                    if not optional:
                        return {"success": False, "project_type": project_type, "results": results}
                except Exception as e:
                    console.print(f"[red]✗ Error: {str(e)}[/red]")
                    results.append({"command": command, "success": False, "error": str(e)})
                    if not optional:
                        return {"success": False, "project_type": project_type, "results": results}
            else:
                console.print("[yellow]Skipped[/yellow]")
                results.append({"command": command, "success": False, "skipped": True})

        all_success = all(r.get("success", False) or r.get("optional", False) for r in results if not r.get("skipped"))

        if all_success:
            console.print(f"\n[bold green]✓ {project_type} installation complete![/bold green]\n")

        return {"success": all_success, "project_type": project_type, "results": results}
