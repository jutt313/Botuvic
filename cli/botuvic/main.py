"""BOTUVIC CLI main entry point"""

import click
from rich.console import Console
from .agent import BotuvicAgent
from .ui.header import display_header

console = Console()

@click.command()
@click.version_option(version="1.0.0")
def cli():
    """
    BOTUVIC - AI Project Manager
    
    Interactive AI agent terminal for managing software projects.
    """
    try:
        # Display header
        display_header()
        
        # Initialize agent
        agent = BotuvicAgent()
        
        while True:
            user_input = console.input("[#10B981]You:[/#10B981] ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[dim]Goodbye![/dim]")
                break
            
            if user_input.startswith('/'):
                # Handle commands (to be implemented)
                console.print(f"[#06B6D4]Command:[/#06B6D4] {user_input}")
                continue
            
            console.print("[#A855F7]BOTUVIC:[/#A855F7] ", end="")
            response = agent.chat(user_input)
            console.print(response)
            console.print()
            
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye![/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")

if __name__ == "__main__":
    cli()

