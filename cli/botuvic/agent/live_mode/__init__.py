"""
Live Development Mode (Phase 10) for BOTUVIC.
Real-time code monitoring, error detection, and proactive improvements.

Complete Feature Set:
- Real-time file watching and code analysis
- Browser console error tracking
- Terminal output monitoring
- Network request tracking and performance analysis
- Intelligent auto-fix system with backups and undo
- Smart notification system with priority queues
- Comprehensive session logging and reports
- Git integration with auto-commit
- Test runner integration
- Performance monitoring (bundle size, API times, memory)
- Deployment readiness checks
"""

# Core components
from .live_controller import LiveModeController
from .file_watcher import FileWatcher
from .browser_tracker import BrowserTracker
from .code_analyzer import CodeAnalyzer

# New advanced features
from .auto_fixer import AutoFixer
from .notification_manager import NotificationManager
from .terminal_monitor import TerminalMonitor
from .network_tracker import NetworkTracker
from .session_logger import SessionLogger
from .git_manager import GitManager
from .test_runner import TestRunner
from .performance_monitor import PerformanceMonitor
from .deployment_checker import DeploymentChecker

__all__ = [
    # Core
    'LiveModeController',
    'FileWatcher',
    'BrowserTracker',
    'CodeAnalyzer',

    # Advanced features
    'AutoFixer',
    'NotificationManager',
    'TerminalMonitor',
    'NetworkTracker',
    'SessionLogger',
    'GitManager',
    'TestRunner',
    'PerformanceMonitor',
    'DeploymentChecker'
]

