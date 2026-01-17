"""
BOTUVIC MCP Server
Exposes BOTUVIC agents via Model Context Protocol for Cursor/Windsurf integration.
Validates API keys and tracks usage.
"""

import os
import sys
import json
import asyncio
from typing import Any, Dict
from pathlib import Path

try:
    import httpx
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP dependencies not installed. Run: pip install mcp httpx", file=sys.stderr)
    sys.exit(1)

# Configuration
API_BASE = os.getenv("BOTUVIC_API_URL", "https://botuvic-api.onrender.com")
API_KEY = os.getenv("BOTUVIC_API_KEY")
PROJECT_DIR = os.getenv("BOTUVIC_PROJECT_DIR", os.getcwd())

# Initialize MCP server
server = Server("botuvic")


# =============================================================================
# API KEY VALIDATION & TRACKING
# =============================================================================

async def validate_key() -> bool:
    """Validate API key with backend."""
    if not API_KEY:
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_BASE}/validate",
                json={"key": API_KEY}
            )
            return response.json().get("valid", False)
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return False


async def track_usage(event: str, metadata: Dict[str, Any] = None) -> None:
    """Track usage event to backend."""
    if not API_KEY:
        return
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{API_BASE}/track",
                json={
                    "key": API_KEY,
                    "event": event,
                    "metadata": metadata or {}
                }
            )
    except Exception:
        pass  # Silent fail for tracking


def require_valid_key(func):
    """Decorator to validate API key before tool execution."""
    async def wrapper(*args, **kwargs):
        if not await validate_key():
            return "❌ Invalid or missing API key. Get one at https://botuvic.com"
        return await func(*args, **kwargs)
    return wrapper


# =============================================================================
# MCP TOOLS
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available BOTUVIC tools."""
    return [
        Tool(
            name="create_project",
            description="Create a full project from an idea. BOTUVIC will ask questions, choose tech stack, and generate all files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {
                        "type": "string",
                        "description": "Project idea or description"
                    },
                    "tech_stack": {
                        "type": "string",
                        "description": "Preferred tech stack (e.g., 'nextjs', 'fastapi', 'auto')",
                        "default": "auto"
                    }
                },
                "required": ["idea"]
            }
        ),
        Tool(
            name="activate_live_mode",
            description="Start LiveAgent to monitor code in real-time, detect errors, and suggest fixes.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="generate_tests",
            description="Auto-generate tests for API endpoints and functions using AI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "What to test: 'endpoints', 'functions', or 'all'",
                        "default": "all"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="check_deployment",
            description="Check if project is ready for deployment. Scans for common issues.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
@require_valid_key
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute BOTUVIC tool."""
    
    try:
        if name == "create_project":
            result = await create_project_tool(arguments)
        elif name == "activate_live_mode":
            result = await activate_live_mode_tool(arguments)
        elif name == "generate_tests":
            result = await generate_tests_tool(arguments)
        elif name == "check_deployment":
            result = await check_deployment_tool(arguments)
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

async def create_project_tool(args: dict) -> str:
    """Create project using MainAgent and CodeAgent."""
    idea = args.get("idea", "")
    tech_stack = args.get("tech_stack", "auto")
    
    await track_usage("create_project", {"idea_length": len(idea), "tech_stack": tech_stack})
    
    try:
        # Import BOTUVIC agents
        sys.path.insert(0, str(Path(__file__).parent))
        from agent.agents.main_agent import MainAgent
        from utils.storage import Storage
        
        # Initialize storage
        storage = Storage(PROJECT_DIR)
        
        # Get LLM client (user must have DeepSeek key)
        llm_key = os.getenv("DEEPSEEK_API_KEY")
        if not llm_key:
            return "❌ DEEPSEEK_API_KEY not set. Add it to your environment."
        
        from utils.llm_client import LLMClient
        llm = LLMClient(api_key=llm_key)
        
        # Initialize MainAgent
        agent = MainAgent(
            llm_client=llm,
            storage=storage,
            project_dir=PROJECT_DIR
        )
        
        # Start conversation with idea
        response = agent.chat(f"I want to build: {idea}", user_profile={})
        
        return f"✅ Project creation started!\n\n{response.get('message', '')}\n\nContinue the conversation in your terminal by running: botuvic chat"
        
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nMake sure BOTUVIC is installed and DEEPSEEK_API_KEY is set."


async def activate_live_mode_tool(args: dict) -> str:
    """Activate LiveAgent monitoring."""
    await track_usage("activate_live_mode")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agent.agents.live_agent import LiveAgent
        from utils.storage import Storage
        from utils.llm_client import LLMClient
        
        llm_key = os.getenv("DEEPSEEK_API_KEY")
        if not llm_key:
            return "❌ DEEPSEEK_API_KEY not set"
        
        storage = Storage(PROJECT_DIR)
        llm = LLMClient(api_key=llm_key)
        
        agent = LiveAgent(
            llm_client=llm,
            storage=storage,
            project_dir=PROJECT_DIR
        )
        
        result = agent.start_monitoring()
        
        if result.get("success"):
            components = result.get("components", {})
            active = sum(1 for v in components.values() if v)
            return f"✅ LiveAgent activated! {active}/10 components running.\n\nMonitoring: {PROJECT_DIR}\n\nI'll watch for errors and suggest fixes in real-time."
        else:
            return f"❌ Failed to activate: {result.get('error')}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def generate_tests_tool(args: dict) -> str:
    """Generate tests using TestGenerator."""
    scope = args.get("scope", "all")
    
    await track_usage("generate_tests", {"scope": scope})
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agent.live_mode.test_generator import TestGenerator
        from utils.storage import Storage
        from utils.llm_client import LLMClient
        
        llm_key = os.getenv("DEEPSEEK_API_KEY")
        if not llm_key:
            return "❌ DEEPSEEK_API_KEY not set"
        
        storage = Storage(PROJECT_DIR)
        llm = LLMClient(api_key=llm_key)
        
        generator = TestGenerator(PROJECT_DIR, llm, storage)
        
        result = generator.generate_and_run()
        
        if result.get("success"):
            tests = result.get("tests_generated", [])
            return f"✅ Generated {len(tests)} test files:\n" + "\n".join(f"  • {t}" for t in tests)
        else:
            return f"❌ Test generation failed: {result.get('error')}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def check_deployment_tool(args: dict) -> str:
    """Check deployment readiness."""
    await track_usage("check_deployment")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agent.live_mode.deployment_checker import DeploymentChecker
        
        checker = DeploymentChecker(PROJECT_DIR)
        result = checker.check_deployment_readiness()
        
        if result.get("success"):
            score = result.get("score", 0)
            issues = result.get("issues", [])
            
            status = "✅ Ready" if score >= 80 else "⚠️ Not ready"
            output = f"{status} for deployment (Score: {score}/100)\n\n"
            
            if issues:
                output += "Issues found:\n" + "\n".join(f"  • {i}" for i in issues)
            else:
                output += "No issues found!"
            
            return output
        else:
            return f"❌ Check failed: {result.get('error')}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run MCP server."""
    # Validate API key on startup
    if not API_KEY:
        print("Warning: BOTUVIC_API_KEY not set. Tools will fail.", file=sys.stderr)
    elif not await validate_key():
        print("Warning: Invalid BOTUVIC_API_KEY. Get one at https://botuvic.com", file=sys.stderr)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
