"""
Command palette menu (triggered by /).
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

import questionary
from questionary import Style

COMMANDS = [
    ("summary", "📝 Generate Conversation Summary"),
    ("config", "🤖 LLM Configuration"),
    ("exit", "🚪 Exit BOTUVIC"),
]

def show_command_menu():
    """
    Show command palette using questionary for arrow navigation.
    Returns selected command or None.
    """
    # Custom style for menu - Purple monochrome
    style = Style([
        ('qmark', 'fg:#A855F7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#A855F7 bold'),
        ('pointer', 'fg:#A855F7 bold'),
        ('highlighted', 'fg:#A855F7 bold'),
        ('selected', 'fg:#C084FC'),
        ('separator', 'fg:#64748B'),
        ('instruction', 'fg:#64748B italic'),
    ])

    choices = [
        questionary.Choice(title=desc, value=cmd) for cmd, desc in COMMANDS
    ]

    try:
        selection = questionary.select(
            "Select a command:",
            choices=choices,
            style=style,
            instruction="(Use arrow keys to navigate, press Enter to select)"
        ).ask()
        
        return selection
    except (KeyboardInterrupt, EOFError):
        return None

