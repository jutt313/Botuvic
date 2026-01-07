"""Command execution function"""

import subprocess
import os
from pathlib import Path

def execute_command(command, storage=None):
    """
    Queue a terminal command for user approval (doesn't execute directly).

    Args:
        command: Command string to execute
        storage: Storage instance for saving pending commands

    Returns:
        Dict indicating command was queued
    """
    # If storage is provided, queue command for approval
    if storage:
        pending_commands = storage.load("pending_commands") or []
        pending_commands.append({
            "command": command,
            "status": "pending"
        })
        storage.save("pending_commands", pending_commands)

        return {
            "success": True,
            "message": f"Command queued for approval: {command}",
            "queued": True
        }

    # Fallback: Execute directly (for backward compatibility)
    return _execute_directly(command)


def _execute_directly(command):
    """
    Directly execute a command (used when no storage available).

    Args:
        command: Command string to execute

    Returns:
        Dict with stdout, stderr, and return_code
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "output": result.stdout
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

