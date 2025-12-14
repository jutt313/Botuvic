"""
Terminal UI header with ASCII logo, tagline, and description.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align


def display_header():
    """Display BOTUVIC header with logo, tagline, and description."""
    console = Console()
    
    # Colors from your palette
    PRIMARY = "#A855F7"      # Purple
    SECONDARY = "#06B6D4"    # Cyan
    TEXT = "#F1F5F9"         # Off White
    ACCENT = "#10B981"       # Green
    
    # ASCII Logo
    logo = """
    ██████╗  ██████╗ ████████╗██╗   ██╗██╗   ██╗██╗ ██████╗
    ██╔══██╗██╔═══██╗╚══██╔══╝██║   ██║██║   ██║██║██╔════╝
    ██████╔╝██║   ██║   ██║   ██║   ██║██║   ██║██║██║     
    ██╔══██╗██║   ██║   ██║   ██║   ██║╚██╗ ██╔╝██║██║     
    ██████╔╝╚██████╔╝   ██║   ╚██████╔╝ ╚████╔╝ ██║╚██████╗
    ╚═════╝  ╚═════╝    ╚═╝    ╚═════╝   ╚═══╝  ╚═╝ ╚═════╝
    """
    
    # Create styled logo
    logo_text = Text(logo, style=PRIMARY)
    
    # Tagline
    tagline = Text("Your AI Project Manager from Idea to Deployment", style=f"bold {SECONDARY}")
    
    # Description
    description = Text()
    description.append("Build anything with AI guidance. BOTUVIC plans, tracks, codes, debugs,\n", style=TEXT)
    description.append("and deploys your project from start to finish. Whether you're a beginner\n", style=TEXT)
    description.append("or expert, BOTUVIC adapts to your skill level and keeps you on track.\n", style=TEXT)
    
    # Combine everything
    header_content = Text()
    header_content.append(logo)
    header_content.append("\n")
    header_content.append(tagline)
    header_content.append("\n\n")
    header_content.append(description)
    
    # Create panel
    panel = Panel(
        Align.center(header_content),
        border_style=PRIMARY,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()  # Empty line
    
    # Input prompt
    console.print(f"[{ACCENT}]Type your message or press[/{ACCENT}] [{SECONDARY}]/[/{SECONDARY}] [{ACCENT}]for commands[/{ACCENT}]")
    console.print()


# Example usage
if __name__ == "__main__":
    display_header()

