"""UI package for BOTUVIC CLI"""

from .header import display_header
from .auth import authenticate_user
from .project_selector import select_project
from .menu import show_command_menu
from .llm_config_ui import configure_llm_ui
from .permissions import PermissionManager
from .code_viewer import CodeChangeViewer
from .terminal_viewer import TerminalViewer

__all__ = [
    "display_header",
    "authenticate_user",
    "select_project",
    "show_command_menu",
    "configure_llm_ui",
    "PermissionManager",
    "CodeChangeViewer",
    "TerminalViewer",
]

