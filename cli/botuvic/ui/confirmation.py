"""
Interactive confirmation selector with 3 options.
Used for all confirmations and permissions.
"""

import questionary
from questionary import Style
from rich.console import Console

console = Console()

# Custom style for confirmation - Purple monochrome
CONFIRMATION_STYLE = Style([
    ('qmark', 'fg:#A855F7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#A855F7 bold'),
    ('pointer', 'fg:#A855F7 bold'),
    ('highlighted', 'fg:#A855F7 bold'),
    ('selected', 'fg:#C084FC'),
    ('separator', 'fg:#64748B'),
    ('instruction', 'fg:#64748B italic'),
])


def ask_confirmation(prompt: str = "", allow_additional_message: bool = True) -> dict:
    """
    Show interactive 3-option confirmation selector.
    
    Args:
        prompt: Optional prompt text to show before selector
        allow_additional_message: If True, option 3 allows user to add message
    
    Returns:
        Dict with:
            - choice: "yes" | "no" | "yes_but"
            - message: Additional message if choice is "yes_but", else None
    """
    if prompt:
        console.print(f"\n{prompt}\n")
    
    choices = [
        questionary.Choice("✅ Yes, it's ok", "yes"),
        questionary.Choice("❌ No, I don't like it", "no"),
        questionary.Choice("✏️  Yes, but need...", "yes_but")
    ]
    
    try:
        selection = questionary.select(
            "",
            choices=choices,
            style=CONFIRMATION_STYLE,
            instruction="(Use ↑↓ arrow keys, press Enter to select)"
        ).ask()
        
        if not selection:
            return {"choice": "no", "message": None}
        
        # If "yes_but" selected, ask for additional message
        if selection == "yes_but" and allow_additional_message:
            console.print()
            additional_msg = console.input("[#A855F7]What do you need? [/#A855F7]")
            return {
                "choice": "yes_but",
                "message": additional_msg.strip() if additional_msg.strip() else None
            }
        
        return {
            "choice": selection,
            "message": None
        }
        
    except (KeyboardInterrupt, EOFError):
        return {"choice": "no", "message": None}
