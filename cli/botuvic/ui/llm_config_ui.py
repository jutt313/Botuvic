"""
LLM configuration interface.
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()

def configure_llm_ui(llm_manager):
    """
    Interactive LLM configuration.
    
    Args:
        llm_manager: LLMManager instance
    """
    console.print("\n[bold cyan]🤖 LLM Configuration[/bold cyan]\n")
    
    # Step 1: Discover models
    console.print("[dim]Searching online for latest models...[/dim]")
    all_models = llm_manager.discover_models()
    console.print(f"[green]✓[/green] Found models from {len(all_models)} providers\n")
    
    # Step 2: Select provider
    providers = list(all_models.keys())
    if not providers:
        console.print("[yellow]No providers available. Please check your internet connection.[/yellow]")
        return
    
    provider = select_provider(providers)
    if not provider:
        return
    
    # Step 3: Select model
    models = all_models[provider]
    model = select_model(provider, models)
    if not model:
        return
    
    # Step 4: API Key
    api_key = Prompt.ask(f"\n{provider} API key", password=True)
    
    if not api_key:
        console.print("[red]API key is required[/red]")
        return
    
    # Step 5: Settings
    settings_choice = Prompt.ask(
        "\nSettings",
        choices=["default", "advanced"],
        default="default"
    )
    
    if settings_choice == "default":
        settings = get_default_settings()
    else:
        settings = get_advanced_settings()
    
    # Step 6: Configure
    try:
        llm_manager.configure_llm(
            provider=provider,
            model=model["id"],
            api_key=api_key,
            **settings
        )
        
        console.print(f"\n[green]✅ Configured {provider} - {model['name']}[/green]")
        show_config_summary(provider, model, settings)
        
    except Exception as e:
        console.print(f"\n[red]❌ Configuration failed: {e}[/red]")

def select_provider(providers):
    """Select LLM provider."""
    console.print("\n[bold]Available Providers:[/bold]\n")
    
    for i, provider in enumerate(providers, 1):
        console.print(f"  {i}. {provider}")
    
    console.print()
    
    try:
        choice = Prompt.ask("Select provider", default="1")
        idx = int(choice) - 1
        if 0 <= idx < len(providers):
            return providers[idx]
    except (ValueError, IndexError):
        pass
    
    return None

def select_model(provider, models):
    """Select model from provider."""
    if not models:
        console.print(f"[yellow]No models found for {provider}[/yellow]")
        return None
    
    console.print(f"\n[bold]{provider} Models:[/bold]\n")
    
    for i, model in enumerate(models[:20], 1):  # Limit to 20
        name = model.get('name', model.get('id', 'Unknown'))
        desc = model.get('description', '')
        if desc:
            console.print(f"  {i}. {name} - {desc[:60]}")
        else:
            console.print(f"  {i}. {name}")
    
    console.print()
    
    try:
        choice = Prompt.ask("Select model", default="1")
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            return models[idx]
    except (ValueError, IndexError):
        pass
    
    return None

def get_default_settings():
    """Get default LLM settings."""
    return {
        "temperature": 0.7,
        "max_tokens": 4000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

def get_advanced_settings():
    """Get advanced LLM settings with user input."""
    console.print("\n[bold]Advanced Settings[/bold]\n")
    
    try:
        temp_str = Prompt.ask("Temperature (0.0-2.0)", default="0.7")
        temperature = float(temp_str)
        
        tokens_str = Prompt.ask("Max tokens (1-128000)", default="4000")
        max_tokens = int(tokens_str)
        
        top_p_str = Prompt.ask("Top-p (0.0-1.0)", default="1.0")
        top_p = float(top_p_str)
        
        freq_str = Prompt.ask("Frequency penalty (-2.0 to 2.0)", default="0.0")
        frequency_penalty = float(freq_str)
        
        pres_str = Prompt.ask("Presence penalty (-2.0 to 2.0)", default="0.0")
        presence_penalty = float(pres_str)
        
        return {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty
        }
    except ValueError:
        console.print("[red]Invalid input. Using defaults.[/red]")
        return get_default_settings()

def show_config_summary(provider, model, settings):
    """Show configuration summary."""
    table = Table(title="LLM Configuration", show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Provider", provider)
    table.add_row("Model", model.get("name", model.get("id", "Unknown")))
    table.add_row("Temperature", str(settings["temperature"]))
    table.add_row("Max Tokens", str(settings["max_tokens"]))
    table.add_row("Top-p", str(settings["top_p"]))
    
    console.print()
    console.print(table)

