"""
Terminal UI header with ASCII logo, tagline, and description.
"""

from rich.console import Console
from rich.text import Text
from rich.align import Align


def display_header(project_name=None, project_path=None):
    """Display BOTUVIC header with logo, tagline, and description."""
    console = Console()
    
    # Colors from purple monochrome palette
    PRIMARY = "#A855F7"      # Purple
    SECONDARY = "#C084FC"    # Light Purple
    TEXT = "#FFFFFF"         # White
    ACCENT = "#10B981"       # Green (for success)
    
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
    
    # Add project info if provided
    if project_name and project_path:
        header_content.append("\n")
        project_info = Text()
        project_info.append(f"Project: ", style="dim")
        project_info.append(f"{project_name}", style=f"bold {ACCENT}")
        project_info.append(f"  •  ", style="dim")
        project_info.append(f"Directory: ", style="dim")
        project_info.append(f"{project_path}", style=f"{TEXT}")
        header_content.append(project_info)

    # Print content without border
    console.print(Align.center(header_content))
    console.print()  # Empty line


# Example usage
if __name__ == "__main__":
    display_header()

