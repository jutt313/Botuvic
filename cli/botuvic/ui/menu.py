"""
Command palette menu (triggered by /).
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

COMMANDS = [
    ("init", "📋 init - Start new project"),
    ("scan", "🔍 scan - Scan code"),
    ("status", "📊 status - Show progress"),
    ("chat", "💬 chat - Ask anything"),
    ("config", "⚙️  config - Configure settings"),
    ("models", "🤖 models - Browse LLM models"),
    ("report", "📝 report - Generate reports"),
    ("fix", "🔧 fix - Fix errors"),
    ("verify", "✅ verify - Check phase"),
    ("git", "🔀 git - Git operations"),
    ("permissions", "🔒 permissions - Manage permissions"),
    ("help", "❓ help - Show help"),
    ("exit", "🚪 exit - Exit BOTUVIC"),
]

def show_command_menu():
    """
    Show command palette.
    Returns selected command or None.
    """
    console.print("\n[bold cyan]📋 Commands[/bold cyan]\n")
    
    # Display commands in a table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="dim")
    
    for cmd, desc in COMMANDS:
        table.add_row(cmd, desc)
    
    console.print(table)
    console.print()
    
    # Get user selection
    choices = [cmd[0] for cmd in COMMANDS]
    selection = Prompt.ask(
        "Select command",
        choices=choices,
        default="help"
    )
    
    return selection

def get_command_help(command):
    """Get help text for a command."""
    help_texts = {
        "init": "Initialize a new project with BOTUVIC",
        "scan": "Scan and analyze your project code",
        "status": "Show current project status and progress",
        "chat": "Start a conversation with BOTUVIC",
        "config": "Configure BOTUVIC settings",
        "models": "Browse and configure LLM models",
        "report": "Generate project reports (PLAN, TODO, REPORT)",
        "fix": "Detect and fix errors in your code",
        "verify": "Verify if current phase is complete",
        "git": "Git operations (commit, branch, PR)",
        "permissions": "Manage file and terminal permissions",
        "help": "Show this help message",
        "exit": "Exit BOTUVIC"
    }
    
    return help_texts.get(command, "Unknown command")

