"""Command execution function"""

import subprocess

def execute_command(command):
    """
    Execute a terminal command and capture output.
    
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
            "return_code": result.returncode
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

