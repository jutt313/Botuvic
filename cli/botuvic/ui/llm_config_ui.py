import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

# Top 25+ LLM Providers
PROVIDERS = [
    "BOTUVIC (Default - Free)", "OpenAI", "DeepSeek", "Anthropic (Claude)", "Google (Gemini)",
    "Meta (Llama 3.1/3.2)", "Mistral AI", "Groq", "Together AI",
    "Perplexity", "Cohere", "Fireworks AI", "Anyscale",
    "OpenRouter", "OctoML", "Replicate", "Azure OpenAI",
    "AWS Bedrock", "Hugging Face", "X.AI (Grok)", "Ollama (Local)",
    "DeepInfra", "AI21 Labs", "Lepton AI", "Lambda Labs", "Novita AI", "Friendly AI"
]

def configure_llm_ui(llm_manager):
    """
    Detailed LLM Configuration with arrow-key navigation.
    """
    console.print("\n[bold #A855F7]🤖 LLM Configuration[/bold #A855F7]\n")
    
    # Custom style for questionary - Purple monochrome
    style = Style([
        ('qmark', 'fg:#A855F7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#A855F7 bold'),
        ('pointer', 'fg:#A855F7 bold'),
        ('highlighted', 'fg:#A855F7 bold'),
        ('selected', 'fg:#C084FC'),
    ])

    # Get current config to show at top
    current_config = llm_manager.get_current_config()
    active_provider = current_config.get("provider")
    
    # Prepare provider choices
    provider_choices = []
    if active_provider:
        provider_choices.append(questionary.Choice(
            title=f"⭐ Current: {active_provider}", 
            value=active_provider
        ))
        provider_choices.append(questionary.Separator("────────────────────────"))

    # Add all providers (unique and cleaned)
    seen = {active_provider} if active_provider else set()
    for p in PROVIDERS:
        name = p.split(" (")[0].split(" ")[0] # Get base name for matching
        if name not in seen:
            provider_choices.append(questionary.Choice(title=p, value=name))
            seen.add(name)

    # 1. Select Provider
    provider = questionary.select(
        "Select an LLM Provider:",
        choices=provider_choices,
        style=style,
        use_shortcuts=True
    ).ask()

    if not provider: return

    # Special handling for BOTUVIC - skip model selection and API key
    if provider == "BOTUVIC":
        try:
            from botuvic.agent.llm.adapters.botuvic_adapter import BotuvicAdapter
            llm_manager.configure_llm(
                provider="BOTUVIC",
                model="botuvic-ai",
                api_key="internal"  # Not used, internal key is used
            )
            console.print(f"\n[green]✅ BOTUVIC AI configured![/green]")
            console.print(f"[dim]Using default free AI (no API key required)[/dim]\n")
            return
        except Exception as e:
            console.print(f"\n[red]❌ Configuration failed: {e}[/red]")
            return

    # 2. Fetch/Select Model
    with console.status(f"[#A855F7]Fetching models for {provider}...[/#A855F7]"):
        models = llm_manager.get_models_for_provider(provider)
    
    # If discovery failed, try to get hardcoded models from the adapter itself
    if not models:
        adapter_class = llm_manager.adapter_registry.get(provider)
        if adapter_class:
            try:
                # Create a temporary adapter with no key just to get model list
                temp_adapter = adapter_class(api_key="list_only")
                models = temp_adapter.get_available_models()
            except:
                pass

    if not models:
        console.print(f"[yellow]No models found for {provider}. Using defaults.[/yellow]")
        models = [{"id": "latest", "name": "Latest Available"}]
        
    # Filter out models that might be empty or invalid
    models = [m for m in models if m and (m.get('id') or m.get('name'))]

    model_choices = [
        questionary.Choice(title=f"{m.get('name', m['id'])}", value=m) 
        for m in models[:25] # Limit to top 25
    ]

    selected_model = questionary.select(
        f"Select a {provider} Model:",
        choices=model_choices,
        style=style
    ).ask()

    if not selected_model: return

    # 3. API Key (Use Global Storage)
    keys_store = llm_manager.storage.load_global("api_keys") or {}
    existing_key = keys_store.get(provider)
    
    instruction = "(Input is hidden for security. Just paste and press Enter)"
    if existing_key:
        instruction = f"(Press Enter to keep existing key, or paste a new one - input is hidden)"
    
    api_key = questionary.password(
        f"Enter {provider} API Key:",
        instruction=instruction,
        style=style
    ).ask()
    
    # Strip whitespace if key was provided
    if api_key:
        api_key = api_key.strip()
    
    # If they pressed enter without typing anything and we have an existing key
    if not api_key and existing_key:
        final_key = existing_key
    elif api_key:
        final_key = api_key
    else:
        console.print("[red]API key is required for this provider.[/red]")
        return
        
    # Save to global storage
    keys_store[provider] = final_key
    try:
        llm_manager.storage.save_global("api_keys", keys_store)
    except OSError as e:
        if "No space left on device" in str(e):
            console.print("\n[bold red]❌ Disk Full Error![/bold red]")
            console.print("Your computer has no space left. Please delete some files first.\n")
            return
        raise e

    # 4. Finalize Configuration
    try:
        llm_manager.configure_llm(
            provider=provider,
            model=selected_model["id"],
            api_key=final_key
        )
        
        console.print(f"\n[green]✅ Successfully configured {provider}![/green]")
        console.print(f"[dim]Model: {selected_model.get('name', selected_model['id'])}[/dim]")
        
        # Obfuscated key preview
        masked_key = final_key[:4] + "*" * (len(final_key) - 8) + final_key[-4:] if len(final_key) > 8 else "****"
        console.print(f"[dim]API Key: {masked_key}[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ Configuration failed: {e}[/red]")

