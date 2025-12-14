"""
Interactive UI components for the BOTUVIC CLI.
Uses rich for beautiful output and questionary for interactive prompts.
"""

import questionary
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
import time

console = Console()

def show_banner():
    """Displays the BOTUVIC ASCII art banner."""
    ascii_art = pyfiglet.figlet_format("BOTUVIC", font="slant")
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    console.print(Panel("[bold green]Your AI Project Manager & Software Architect[/bold green]", expand=False, border_style="cyan"))

def show_status(message):
    """Displays a status message."""
    console.print(f"⚙️  {message}")

def show_success(message):
    """Displays a success message."""
    console.print(f"✅ [bold green]{message}[/bold green]")

def show_error(message):
    """Displays an error message."""
    console.print(f"❌ [bold red]Error: {message}[/bold red]")

def show_warning(message):
    """Displays a warning message."""
    console.print(f"⚠️  [yellow]Warning: {message}[/yellow]")

def show_info(message):
    """Displays an informational message."""
    console.print(f"ℹ️  [blue]{message}[/blue]")

def ask_text(question, multiline=False):
    """Asks the user for text input."""
    return questionary.text(question, multiline=multiline).ask()

def ask_select(question, choices):
    """Asks the user to select one item from a list."""
    return questionary.select(question, choices=choices).ask()

def ask_checkbox(question, choices):
    """Asks the user to select multiple items from a list."""
    return questionary.checkbox(question, choices=choices).ask()

def ask_confirm(question, default=True):
    """Asks the user for a yes/no confirmation."""
    return questionary.confirm(question, default=default).ask()

def ask_permission(action, details):
    """Asks for permission to perform an action."""
    console.Print(Panel(
        f"[bold]BOTUVIC wants to {action}:[/bold]\n\n" + "\n".join(f"- {item}" for item in details),
        title="[yellow]Permission Request[/yellow]",
        border_style="yellow",
        expand=False
    ))
    return ask_confirm("Do you approve?", default=True)

def select_files(files, message):
    """Allows user to select files from a list."""
    return ask_checkbox(message, choices=files)

def show_code(code, language, title):
    """Displays a syntax-highlighted code block."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=title, border_style="green", expand=False))

def show_code_diff(title, old_code, new_code, language):
    """Displays a before/after diff of code changes."""
    # This is a simplified diff, not a line-by-line one.
    # A real implementation would use a diffing library.
    console.print(Panel(
        Syntax(old_code, language, theme="monokai", line_numbers=True),
        title=f"BEFORE: {title}",
        border_style="red",
        expand=False
    ))
    console.print(Panel(
        Syntax(new_code, language, theme="monokai", line_numbers=True),
        title=f"AFTER: {title}",
        border_style="green",
        expand=False
    ))

def show_activity_panel(title, message):
    """Shows a panel indicating current agent activity."""
    panel = Panel(f"[bold]{message}[/bold]", title=f"🤖 BOTUVIC is {title}...", border_style="cyan")
    with Live(panel, console=console, refresh_per_second=4, transient=True):
        time.sleep(1.5) # Simulate work

def show_agent_thinking():
    """Shows a thinking indicator."""
    spinner = Spinner("dots", text=" 🤖 BOTUVIC is thinking...")
    with Live(spinner, console=console, transient=True):
        time.sleep(1) # Simulate thinking

def with_spinner(message, func, *args, **kwargs):
    """Executes a function while showing a spinner."""
    with console.status(f"[bold green]{message}") as status:
        return func(*args, **kwargs)

def show_table(title, columns, rows):
    """Displays data in a rich table."""
    table = Table(title=title)
    for column in columns:
        table.add_column(column, style="cyan")
    for row in rows:
        table.add_row(*row)
    console.print(table)

def show_markdown(content):
    """Renders and displays markdown content."""
    md = Markdown(content)
    console.print(md)

def show_project_summary(data):
    """Displays a project summary (placeholder)."""
    # In a real scenario, 'data' would be a structured object
    panel = Panel(f"Project: {data.get('name', 'N/A')}\nDescription: {data.get('description', 'N/A')}", title="Project Summary", border_style="blue")
    console.print(panel)

def show_roadmap(data):
    """Displays a project roadmap (placeholder)."""
    console.print(Panel("Roadmap display is not implemented yet.", title="Project Roadmap", border_style="yellow"))

def show_chat_header():
    console.print("\n💬 [bold]Chat with BOTUVIC[/bold] (type 'exit' to quit)")

def show_exit_message():
    console.print("\n[bold green]Thank you for using BOTUVIC! ✨[/bold green]")

def show_agent_response(text):
    """Displays a response from the agent in a styled panel."""
    console.print(Panel(text, title="[bold cyan]🤖 BOTUVIC[/bold cyan]", border_style="cyan", expand=False))
