"""
Network Request Tracker for Phase 10 Live Development Mode.
Monitors API calls, detects endpoint mismatches, and tracks performance.
"""

import re
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
from rich.console import Console

console = Console()


class NetworkTracker:
    """
    Tracks network requests from frontend to backend.
    Detects endpoint mismatches, slow requests, and failures.
    """

    def __init__(self, project_dir: str, on_issue_callback: Callable):
        """
        Initialize network tracker.

        Args:
            project_dir: Project root directory
            on_issue_callback: Function to call when issue detected
        """
        self.project_dir = project_dir
        self.on_issue_callback = on_issue_callback

        self.request_log = []
        self.endpoint_usage = defaultdict(int)
        self.failed_requests = []
        self.slow_requests = []

        # Thresholds
        self.SLOW_REQUEST_THRESHOLD = 1000  # 1 second in ms

        # Discovered endpoints from code
        self.frontend_endpoints = set()
        self.backend_endpoints = set()
        self.endpoints_scanned = False

    def track_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track an API request.

        Args:
            request_data: Request information containing:
                - method: HTTP method
                - url: Request URL
                - status: Response status code
                - duration: Request duration in ms
                - error: Error message (if failed)

        Returns:
            Analysis result
        """
        method = request_data.get("method", "GET")
        url = request_data.get("url", "")
        status = request_data.get("status")
        duration = request_data.get("duration", 0)
        error = request_data.get("error")

        # Normalize URL (remove query params and domain)
        endpoint = self._normalize_endpoint(url)

        # Log request
        request_record = {
            "method": method,
            "endpoint": endpoint,
            "url": url,
            "status": status,
            "duration": duration,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        self.request_log.append(request_record)
        self.endpoint_usage[f"{method} {endpoint}"] += 1

        # Keep only last 500 requests
        if len(self.request_log) > 500:
            self.request_log = self.request_log[-500:]

        # Analyze request
        issues = []

        # Check for failure
        if status and status >= 400:
            self.failed_requests.append(request_record)
            issues.append(self._analyze_failed_request(request_record))

        # Check for slow request
        if duration > self.SLOW_REQUEST_THRESHOLD:
            self.slow_requests.append(request_record)
            issues.append(self._analyze_slow_request(request_record))

        # Check for endpoint mismatch (on first request)
        if not self.endpoints_scanned:
            self._scan_endpoints()
            self.endpoints_scanned = True

        if endpoint not in self.backend_endpoints:
            issues.append(self._analyze_endpoint_mismatch(request_record))

        # Notify issues
        for issue in issues:
            if issue:
                try:
                    self.on_issue_callback(issue)
                except Exception as e:
                    console.print(f"[yellow]⚠ Callback failed: {e}[/yellow]")

        return {
            "tracked": True,
            "issues": [i for i in issues if i],
            "duration": duration,
            "status": status
        }

    def _normalize_endpoint(self, url: str) -> str:
        """
        Normalize URL to endpoint path.

        Args:
            url: Full URL

        Returns:
            Normalized endpoint
        """
        # Remove protocol and domain
        if '://' in url:
            url = url.split('://', 1)[1]
            if '/' in url:
                url = '/' + url.split('/', 1)[1]

        # Remove query params
        if '?' in url:
            url = url.split('?')[0]

        # Remove trailing slash
        url = url.rstrip('/')

        return url or '/'

    def _analyze_failed_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze failed request and generate issue."""
        status = request.get("status")
        endpoint = request.get("endpoint")
        method = request.get("method")
        error = request.get("error", "Unknown error")

        severity = "critical" if status >= 500 else "high"

        return {
            "type": "network_error",
            "severity": severity,
            "message": f"{method} {endpoint} failed with status {status}",
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "error": error,
            "suggestion": self._suggest_fix_for_status(status),
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_slow_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze slow request and generate issue."""
        duration = request.get("duration")
        endpoint = request.get("endpoint")
        method = request.get("method")

        return {
            "type": "slow_request",
            "severity": "medium",
            "message": f"{method} {endpoint} took {duration}ms (slow)",
            "endpoint": endpoint,
            "method": method,
            "duration": duration,
            "suggestion": "Optimize this endpoint or add caching",
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_endpoint_mismatch(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze endpoint mismatch."""
        endpoint = request.get("endpoint")
        method = request.get("method")
        status = request.get("status")

        # Only flag 404 errors as mismatches
        if status != 404:
            return None

        # Find similar endpoints
        similar = self._find_similar_endpoints(endpoint)

        suggestion = "Check if endpoint exists in backend"
        if similar:
            suggestion = f"Did you mean: {similar[0]}?"

        return {
            "type": "endpoint_mismatch",
            "severity": "high",
            "message": f"Endpoint not found: {method} {endpoint}",
            "endpoint": endpoint,
            "method": method,
            "similar_endpoints": similar,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat()
        }

    def _suggest_fix_for_status(self, status: int) -> str:
        """Suggest fix based on status code."""
        if status == 404:
            return "Check endpoint URL matches backend route"
        elif status == 401:
            return "Add authentication token to request"
        elif status == 403:
            return "Check user permissions for this endpoint"
        elif status == 500:
            return "Check backend logs for server error"
        elif status == 503:
            return "Backend service may be down"
        else:
            return "Check network connection and backend status"

    def _scan_endpoints(self):
        """
        Scan codebase to discover frontend and backend endpoints.
        """
        try:
            # Scan frontend for API calls
            frontend_dir = os.path.join(self.project_dir, 'frontend')
            if os.path.exists(frontend_dir):
                self.frontend_endpoints = self._scan_frontend_endpoints(frontend_dir)

            # Scan backend for route definitions
            backend_dir = os.path.join(self.project_dir, 'backend')
            if os.path.exists(backend_dir):
                self.backend_endpoints = self._scan_backend_endpoints(backend_dir)

        except Exception as e:
            console.print(f"[yellow]⚠ Endpoint scan failed: {e}[/yellow]")

    def _scan_frontend_endpoints(self, directory: str) -> set:
        """Scan frontend code for API endpoint calls."""
        endpoints = set()

        patterns = [
            r'fetch\([\'"](.+?)[\'"]',
            r'axios\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]',
            r'\.get\([\'"](.+?)[\'"]',
            r'\.post\([\'"](.+?)[\'"]',
        ]

        for root, dirs, files in os.walk(directory):
            # Skip node_modules
            if 'node_modules' in root:
                continue

            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Handle tuple results from axios pattern
                                endpoint = match if isinstance(match, str) else match[-1]
                                if endpoint.startswith('/'):
                                    endpoints.add(self._normalize_endpoint(endpoint))
                    except:
                        pass

        return endpoints

    def _scan_backend_endpoints(self, directory: str) -> set:
        """Scan backend code for route definitions."""
        endpoints = set()

        # Patterns for different backend frameworks
        patterns = [
            # Express.js
            r'router\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]',
            r'app\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]',
            # FastAPI
            r'@app\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]',
            r'@router\.(get|post|put|delete|patch)\([\'"](.+?)[\'"]',
            # Flask
            r'@app\.route\([\'"](.+?)[\'"]',
        ]

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.ts', '.py', '.java', '.go')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Handle tuple results
                                endpoint = match if isinstance(match, str) else match[-1]
                                if endpoint.startswith('/'):
                                    endpoints.add(self._normalize_endpoint(endpoint))
                    except:
                        pass

        return endpoints

    def _find_similar_endpoints(self, endpoint: str) -> List[str]:
        """Find similar endpoints using simple string matching."""
        similar = []
        endpoint_lower = endpoint.lower()

        for backend_endpoint in self.backend_endpoints:
            # Calculate similarity (simple approach)
            if self._similarity(endpoint_lower, backend_endpoint.lower()) > 0.5:
                similar.append(backend_endpoint)

        return sorted(similar, key=lambda x: self._similarity(endpoint_lower, x.lower()), reverse=True)[:3]

    def _similarity(self, a: str, b: str) -> float:
        """Calculate simple string similarity."""
        if a == b:
            return 1.0

        # Count matching substrings
        matches = 0
        total = max(len(a), len(b))

        for i, char in enumerate(a):
            if i < len(b) and char == b[i]:
                matches += 1

        return matches / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        return {
            "total_requests": len(self.request_log),
            "failed_requests": len(self.failed_requests),
            "slow_requests": len(self.slow_requests),
            "frontend_endpoints": len(self.frontend_endpoints),
            "backend_endpoints": len(self.backend_endpoints),
            "most_used": sorted(self.endpoint_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def get_recent_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent requests."""
        return self.request_log[-limit:]
    
    def get_report(self) -> Dict[str, Any]:
        """
        Get comprehensive network tracking report.
        
        Returns:
            Report dict with metrics and analysis
        """
        stats = self.get_stats()
        
        # Calculate average response time
        if self.request_log:
            durations = [r.get("duration", 0) for r in self.request_log if r.get("duration")]
            avg_response_time = sum(durations) / len(durations) if durations else 0
        else:
            avg_response_time = 0
        
        return {
            "success": True,
            "metrics": {
                "total_requests": len(self.request_log),
                "failed_requests": len(self.failed_requests),
                "slow_requests": len(self.slow_requests),
                "avg_response_time": round(avg_response_time, 2),
                "frontend_endpoints": len(self.frontend_endpoints),
                "backend_endpoints": len(self.backend_endpoints),
                "most_used_endpoints": stats.get("most_used", [])
            },
            "recent_requests": self.get_recent_requests(10),
            "failed_requests": self.failed_requests[-5:],  # Last 5 failures
            "slow_requests": self.slow_requests[-5:]  # Last 5 slow requests
        }

    def clear_logs(self):
        """Clear request logs."""
        self.request_log.clear()
        self.failed_requests.clear()
        self.slow_requests.clear()
        self.endpoint_usage.clear()
