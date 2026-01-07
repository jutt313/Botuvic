"""
Browser Console Tracker for Phase 10 Live Development Mode.
Captures browser console errors and sends them to the agent.
"""

import os
import json
from typing import Dict, Any, List, Callable
from datetime import datetime
from rich.console import Console

console = Console()


class BrowserTracker:
    """
    Tracks browser console errors and warnings.
    Injects tracking script into frontend and receives errors via HTTP endpoint.
    """
    
    def __init__(self, project_dir: str, on_error_callback: Callable):
        """
        Initialize browser tracker.
        
        Args:
            project_dir: Project root directory
            on_error_callback: Function to call when browser error detected
        """
        self.project_dir = project_dir
        self.on_error_callback = on_error_callback
        self.is_tracking = False
        self.errors_log = []
    
    def inject_tracking_script(self) -> Dict[str, Any]:
        """
        Inject browser console tracking script into frontend.
        
        Returns:
            Status dict
        """
        try:
            # Find frontend entry point
            frontend_dir = os.path.join(self.project_dir, 'frontend')
            
            if not os.path.exists(frontend_dir):
                return {"success": False, "error": "Frontend directory not found"}
            
            # Look for common entry points
            entry_points = [
                'public/index.html',
                'index.html',
                'src/index.html',
                'app/index.html'
            ]
            
            html_file = None
            for entry in entry_points:
                path = os.path.join(frontend_dir, entry)
                if os.path.exists(path):
                    html_file = path
                    break
            
            if not html_file:
                # Try to find any index.html
                for root, dirs, files in os.walk(frontend_dir):
                    if 'index.html' in files:
                        html_file = os.path.join(root, 'index.html')
                        break
            
            if not html_file:
                return {"success": False, "error": "Could not find HTML entry point"}
            
            # Read current HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Check if already injected
            if 'botuvic-console-tracker' in html_content:
                return {"success": True, "message": "Tracking script already injected"}
            
            # Create tracking script
            tracking_script = self._generate_tracking_script()
            
            # Inject before </body> or </head>
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', f'{tracking_script}\n</body>')
            elif '</head>' in html_content:
                html_content = html_content.replace('</head>', f'{tracking_script}\n</head>')
            else:
                html_content += tracking_script
            
            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            console.print(f"[green]✓[/green] Browser tracking script injected into {os.path.relpath(html_file, self.project_dir)}")
            
            self.is_tracking = True
            
            return {
                "success": True,
                "injected": True,
                "file": os.path.relpath(html_file, self.project_dir)
            }
        
        except Exception as e:
            console.print(f"[red]✗ Failed to inject tracking script: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def _generate_tracking_script(self) -> str:
        """Generate the browser console tracking script."""
        return """
<script id="botuvic-console-tracker">
(function() {
  // BOTUVIC Console Tracker - Captures errors and sends to agent
  const BOTUVIC_ENDPOINT = 'http://localhost:7777/botuvic/console-error';
  
  // Store original console methods
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalLog = console.log;
  
  // Send error to BOTUVIC agent
  function sendToBotuvic(type, message, stack, source) {
    try {
      fetch(BOTUVIC_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: type,
          message: message,
          stack: stack,
          source: source,
          url: window.location.href,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent
        })
      }).catch(() => {
        // Silently fail if agent not running
      });
    } catch (e) {
      // Ignore
    }
  }
  
  // Override console.error
  console.error = function(...args) {
    originalError.apply(console, args);
    
    const message = args.map(arg => {
      if (typeof arg === 'object') {
        try { return JSON.stringify(arg); }
        catch { return String(arg); }
      }
      return String(arg);
    }).join(' ');
    
    sendToBotuvic('error', message, new Error().stack, 'console.error');
  };
  
  // Override console.warn
  console.warn = function(...args) {
    originalWarn.apply(console, args);
    
    const message = args.map(arg => String(arg)).join(' ');
    sendToBotuvic('warning', message, null, 'console.warn');
  };
  
  // Catch unhandled errors
  window.addEventListener('error', function(event) {
    sendToBotuvic(
      'uncaught_error',
      event.message,
      event.error ? event.error.stack : null,
      event.filename + ':' + event.lineno + ':' + event.colno
    );
  });
  
  // Catch unhandled promise rejections
  window.addEventListener('unhandledrejection', function(event) {
    sendToBotuvic(
      'unhandled_rejection',
      event.reason ? String(event.reason) : 'Promise rejected',
      event.reason && event.reason.stack ? event.reason.stack : null,
      'Promise'
    );
  });
  
  // Catch React errors (if React is present)
  if (window.React) {
    const originalComponentDidCatch = window.React.Component.prototype.componentDidCatch;
    window.React.Component.prototype.componentDidCatch = function(error, errorInfo) {
      sendToBotuvic(
        'react_error',
        error.message,
        error.stack,
        'React Component'
      );
      if (originalComponentDidCatch) {
        originalComponentDidCatch.call(this, error, errorInfo);
      }
    };
  }
  
  console.log('[BOTUVIC] Console tracker active');
})();
</script>
"""
    
    def handle_browser_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming browser error.
        
        Args:
            error_data: Error data from browser
            
        Returns:
            Processing result
        """
        try:
            # Log error
            self.errors_log.append({
                **error_data,
                "received_at": datetime.now().isoformat()
            })
            
            # Keep only last 100 errors
            if len(self.errors_log) > 100:
                self.errors_log = self.errors_log[-100:]
            
            # Call callback
            self.on_error_callback(error_data)
            
            return {"success": True, "logged": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent browser errors.
        
        Args:
            limit: Max number of errors to return
            
        Returns:
            List of recent errors
        """
        return self.errors_log[-limit:]
    
    def clear_errors(self):
        """Clear error log."""
        self.errors_log = []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get tracker status.
        
        Returns:
            Status dict
        """
        return {
            "tracking": self.is_tracking,
            "errors_count": len(self.errors_log),
            "recent_errors": self.get_recent_errors(5)
        }

