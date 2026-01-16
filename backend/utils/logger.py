"""
Comprehensive logging configuration for BOTUVIC backend.
Provides transparent, step-by-step error tracking for all files.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
ERROR_LOG = LOGS_DIR / "errors.log"
REQUEST_LOG = LOGS_DIR / "requests.log"
DEBUG_LOG = LOGS_DIR / "debug.log"

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class FileTrackingFormatter(logging.Formatter):
    """Formatter that includes file name and line number."""
    
    def format(self, record):
        # Add file tracking info
        if not hasattr(record, 'file_tracking'):
            record.file_tracking = f"[{Path(record.pathname).name}:{record.lineno}]"
        
        # Format timestamp
        record.timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        return super().format(record)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors (for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    # Use FileTrackingFormatter which includes timestamp and file tracking
    console_formatter = FileTrackingFormatter(
        fmt='%(timestamp)s | %(levelname)-8s | %(file_tracking)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Wrap with colors
    class ColoredFileFormatter(FileTrackingFormatter):
        def format(self, record):
            levelname = record.levelname
            if levelname in ColoredFormatter.COLORS:
                record.levelname = f"{ColoredFormatter.COLORS[levelname]}{levelname}{ColoredFormatter.COLORS['RESET']}"
            return super().format(record)
    
    console_handler.setFormatter(ColoredFileFormatter(
        fmt='%(timestamp)s | %(levelname)-8s | %(file_tracking)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(console_handler)
    
    # Error log file handler
    error_handler = logging.FileHandler(ERROR_LOG, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_formatter = FileTrackingFormatter(
        fmt='%(timestamp)s | %(levelname)-8s | %(file_tracking)s | %(funcName)s | %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Request log file handler
    request_handler = logging.FileHandler(REQUEST_LOG, encoding='utf-8')
    request_handler.setLevel(logging.INFO)
    request_formatter = FileTrackingFormatter(
        fmt='%(timestamp)s | %(levelname)-8s | %(file_tracking)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    request_handler.setFormatter(request_formatter)
    root_logger.addHandler(request_handler)
    
    # Debug log file handler (all logs)
    debug_handler = logging.FileHandler(DEBUG_LOG, encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = FileTrackingFormatter(
        fmt='%(timestamp)s | %(levelname)-8s | %(file_tracking)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    debug_handler.setFormatter(debug_formatter)
    root_logger.addHandler(debug_handler)
    
    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info("BOTUVIC Backend - Logging System Initialized")
    root_logger.info(f"Log Level: {log_level.upper()}")
    root_logger.info(f"Error Log: {ERROR_LOG}")
    root_logger.info(f"Request Log: {REQUEST_LOG}")
    root_logger.info(f"Debug Log: {DEBUG_LOG}")
    root_logger.info("=" * 80)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_step(logger: logging.Logger, step: str, details: Optional[dict] = None):
    """
    Log a step in a process with details.
    
    Args:
        logger: Logger instance
        step: Step description
        details: Optional dictionary with step details
    """
    message = f"STEP: {step}"
    if details:
        detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {detail_str}"
    logger.info(message)

def log_error_with_context(logger: logging.Logger, error: Exception, context: dict):
    """
    Log an error with full context.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Dictionary with context information
    """
    context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
    logger.error(
        f"ERROR: {type(error).__name__}: {str(error)} | Context: {context_str}",
        exc_info=True
    )

def log_request(logger: logging.Logger, method: str, path: str, status_code: int, 
                duration_ms: float, user_id: Optional[str] = None):
    """
    Log an HTTP request with full details.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
    """
    user_info = f" | User: {user_id}" if user_id else ""
    logger.info(
        f"REQUEST: {method} {path} | Status: {status_code} | Duration: {duration_ms:.2f}ms{user_info}"
    )

def log_user_message(logger: logging.Logger, message: str, project_id: str):
    """
    Log user message clearly and visibly in RED.
    
    Args:
        logger: Logger instance
        message: User message content
        project_id: Project ID
    """
    RED = '\033[91m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info("=" * 100)
    logger.info(f"{RED}👤 USER MESSAGE RECEIVED{RESET}")
    logger.info("=" * 100)
    logger.info(f"{RED}Project: {project_id}{RESET}")
    logger.info("")
    logger.info(f"{RED}Message Content:{RESET}")
    logger.info("-" * 100)
    message_lines = message.split('\n')
    for line in message_lines:
        logger.info(f"{RED}   {line}{RESET}")
    logger.info("-" * 100)
    logger.info("")

def log_agent_response(logger: logging.Logger, response: str, project_id: str, agent_name: str = "BOTUVIC"):
    """
    Log agent response clearly and visibly in BLUE.
    
    Args:
        logger: Logger instance
        response: Agent response content
        project_id: Project ID
        agent_name: Name of the agent (default: BOTUVIC)
    """
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info("=" * 100)
    logger.info(f"{BLUE}🤖 {agent_name} RESPONSE{RESET}")
    logger.info("=" * 100)
    logger.info(f"{BLUE}Project: {project_id}{RESET}")
    logger.info("")
    logger.info(f"{BLUE}Response Content:{RESET}")
    logger.info("-" * 100)
    response_lines = response.split('\n')
    for line in response_lines:
        logger.info(f"{BLUE}   {line}{RESET}")
    logger.info("-" * 100)
    logger.info("")

def log_agent_processing(logger: logging.Logger, step: str, details: Optional[dict] = None):
    """
    Log agent processing step clearly.
    
    Args:
        logger: Logger instance
        step: Processing step description
        details: Optional dictionary with step details
    """
    logger.info("")
    logger.info("⚙️  AGENT PROCESSING:")
    logger.info(f"   Step: {step}")
    if details:
        for key, value in details.items():
            logger.info(f"   {key}: {value}")
    logger.info("")
