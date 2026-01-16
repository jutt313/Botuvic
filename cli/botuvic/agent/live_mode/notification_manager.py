"""
Smart Notification Manager for Phase 10 Live Development Mode.
Handles priority-based alerts with intelligent timing and batching.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from rich.console import Console
from rich.panel import Panel

console = Console()


class NotificationManager:
    """
    Intelligent notification system that knows when to show alerts.
    Features: Priority queues, batching, timing rules, user idle detection.
    """

    def __init__(self):
        """Initialize notification manager."""
        self.notifications_queue = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }

        self.last_user_activity = time.time()
        self.last_notification_time = 0
        self.notification_history = []

        # Timing rules (seconds)
        self.IDLE_THRESHOLD = 30  # User idle if no activity for 30s
        self.DEBOUNCE_TIME = 2  # Wait 2s between notifications
        self.RAPID_CHANGE_WINDOW = 10  # Detect rapid changes in 10s

        # Batching thresholds
        self.BATCH_THRESHOLD = 3  # Batch if 3+ similar issues
        self.BATCH_WINDOW = 60  # Within 60 seconds

        self.ignored_issues = set()
        self.user_is_typing = False
        self.rapid_changes_detected = False

    def add_notification(
        self,
        notification_type: str,
        severity: str,
        message: str,
        file: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add notification to queue.

        Args:
            notification_type: Type (error, warning, suggestion, info)
            severity: Severity (critical, high, medium, low, info)
            message: Notification message
            file: Related file path
            data: Additional data

        Returns:
            Status dict
        """
        # Check if should ignore
        if self._should_ignore(notification_type, message, file):
            return {"queued": False, "reason": "ignored"}

        notification = {
            "id": self._generate_id(),
            "type": notification_type,
            "severity": severity,
            "message": message,
            "file": file,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "shown": False
        }

        # Add to appropriate queue
        self.notifications_queue[severity].append(notification)

        # Check if should show immediately
        if self._should_show_immediately(notification):
            self._show_notification(notification)
            return {"queued": True, "shown": True, "reason": "immediate"}

        return {"queued": True, "shown": False, "reason": "queued"}

    def process_queue(self) -> List[Dict[str, Any]]:
        """
        Process notification queue based on timing rules.
        Call this periodically from main loop.

        Returns:
            List of shown notifications
        """
        shown = []

        # Don't show if user is actively typing
        if self.user_is_typing or self.rapid_changes_detected:
            return shown

        # Don't show too frequently
        if time.time() - self.last_notification_time < self.DEBOUNCE_TIME:
            return shown

        # Check if user is idle
        is_idle = self._is_user_idle()

        # Process critical (always show if not typing)
        if self.notifications_queue["critical"]:
            batched = self._batch_similar(self.notifications_queue["critical"])
            for notification in batched:
                self._show_notification(notification)
                shown.append(notification)
            self.notifications_queue["critical"].clear()

        # Process high (show on idle or after save)
        if is_idle and self.notifications_queue["high"]:
            batched = self._batch_similar(self.notifications_queue["high"])
            for notification in batched[:3]:  # Max 3 at once
                self._show_notification(notification)
                shown.append(notification)
            self.notifications_queue["high"] = self.notifications_queue["high"][3:]

        # Process medium (only when idle)
        if is_idle and self.notifications_queue["medium"]:
            batched = self._batch_similar(self.notifications_queue["medium"])
            if batched:
                # Show only 1 medium priority
                self._show_notification(batched[0])
                shown.append(batched[0])
            self.notifications_queue["medium"] = self.notifications_queue["medium"][1:]

        # Low and info: Never show automatically (only in reports)

        if shown:
            self.last_notification_time = time.time()

        return shown

    def mark_user_activity(self, activity_type: str = "typing"):
        """
        Mark user activity to prevent interruptions.

        Args:
            activity_type: Type of activity (typing, saving, idle)
        """
        self.last_user_activity = time.time()

        if activity_type == "typing":
            self.user_is_typing = True
        elif activity_type == "saved":
            self.user_is_typing = False
        elif activity_type == "idle":
            self.user_is_typing = False

    def mark_rapid_changes(self, is_rapid: bool):
        """Mark if rapid file changes detected."""
        self.rapid_changes_detected = is_rapid

    def ignore_issue(self, issue_signature: str):
        """Add issue to ignore list."""
        self.ignored_issues.add(issue_signature)

    def clear_queue(self, severity: Optional[str] = None):
        """Clear notification queue."""
        if severity:
            self.notifications_queue[severity].clear()
        else:
            for queue in self.notifications_queue.values():
                queue.clear()

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "critical": len(self.notifications_queue["critical"]),
            "high": len(self.notifications_queue["high"]),
            "medium": len(self.notifications_queue["medium"]),
            "low": len(self.notifications_queue["low"]),
            "info": len(self.notifications_queue["info"]),
            "total": sum(len(q) for q in self.notifications_queue.values()),
            "user_idle": self._is_user_idle(),
            "user_typing": self.user_is_typing
        }

    def _should_show_immediately(self, notification: Dict[str, Any]) -> bool:
        """Determine if notification should show immediately."""
        severity = notification["severity"]

        # Critical: Always show (unless typing rapidly)
        if severity == "critical":
            return not self.rapid_changes_detected

        # Others: Never show immediately (use queue)
        return False

    def _should_ignore(self, notification_type: str, message: str, file: Optional[str]) -> bool:
        """Check if notification should be ignored."""
        # Create signature
        signature = f"{notification_type}:{file}:{message[:50]}"

        if signature in self.ignored_issues:
            return True

        # Check if same issue shown recently
        recent_window = time.time() - 300  # Last 5 minutes
        for hist in self.notification_history[-20:]:
            if hist.get("message") == message and hist.get("file") == file:
                hist_time = datetime.fromisoformat(hist["timestamp"]).timestamp()
                if hist_time > recent_window:
                    return True  # Same issue shown recently

        return False

    def _is_user_idle(self) -> bool:
        """Check if user is idle."""
        idle_time = time.time() - self.last_user_activity
        return idle_time >= self.IDLE_THRESHOLD

    def _batch_similar(self, notifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch similar notifications together.

        Args:
            notifications: List of notifications

        Returns:
            Batched notifications
        """
        if len(notifications) < self.BATCH_THRESHOLD:
            return notifications

        # Group by file
        by_file = defaultdict(list)
        for notif in notifications:
            file = notif.get("file", "unknown")
            by_file[file].append(notif)

        # Create batched notifications
        batched = []
        for file, notifs in by_file.items():
            if len(notifs) >= self.BATCH_THRESHOLD:
                # Create batch notification
                batch_notif = {
                    "id": self._generate_id(),
                    "type": "batch",
                    "severity": notifs[0]["severity"],
                    "message": f"Found {len(notifs)} issues in {file}",
                    "file": file,
                    "data": {"batched_count": len(notifs), "issues": notifs},
                    "timestamp": datetime.now().isoformat(),
                    "shown": False
                }
                batched.append(batch_notif)
            else:
                batched.extend(notifs)

        return batched

    def _show_notification(self, notification: Dict[str, Any]):
        """
        Display notification to user.

        Args:
            notification: Notification dict
        """
        severity = notification["severity"]
        message = notification["message"]
        file = notification.get("file")
        notif_type = notification.get("type")

        # Choose icon and color based on severity
        if severity == "critical":
            icon = "🔴"
            color = "red"
            prefix = "CRITICAL"
        elif severity == "high":
            icon = "⚠️"
            color = "yellow"
            prefix = "WARNING"
        elif severity == "medium":
            icon = "💡"
            color = "cyan"
            prefix = "SUGGESTION"
        else:
            icon = "📊"
            color = "blue"
            prefix = "INFO"

        # Format message
        if notif_type == "batch":
            # Show batch summary
            data = notification.get("data", {})
            count = data.get("batched_count", 0)
            console.print(f"\n[bold {color}]{icon} {prefix}: Multiple Issues Detected[/bold {color}]")
            console.print(f"[{color}]Found {count} issues in {file}[/{color}]")
            console.print(f"[dim]Type 'show errors' to see details[/dim]\n")
        else:
            # Show individual notification
            file_info = f" in {file}" if file else ""
            console.print(f"\n[bold {color}]{icon} {prefix}{file_info}[/bold {color}]")
            console.print(f"[{color}]{message}[/{color}]")

            # Show additional data if available
            data = notification.get("data", {})
            if data.get("suggestion"):
                console.print(f"[dim]Suggestion: {data['suggestion']}[/dim]")
            if data.get("line"):
                console.print(f"[dim]Line: {data['line']}[/dim]")

            console.print()

        # Mark as shown
        notification["shown"] = True
        notification["shown_at"] = datetime.now().isoformat()

        # Add to history
        self.notification_history.append(notification)

        # Keep only last 100
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]

    def _generate_id(self) -> str:
        """Generate unique notification ID."""
        import hashlib
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]

    def show_summary(self):
        """Show summary of all pending notifications."""
        status = self.get_queue_status()
        total = status["total"]

        if total == 0:
            console.print("[green]✓ No pending notifications[/green]")
            return

        console.print(f"\n[bold]📬 Pending Notifications: {total}[/bold]\n")

        for severity in ["critical", "high", "medium", "low", "info"]:
            count = status[severity]
            if count > 0:
                icon = {"critical": "🔴", "high": "⚠️", "medium": "💡", "low": "📝", "info": "📊"}[severity]
                console.print(f"{icon} {severity.upper()}: {count}")

        console.print(f"\n[dim]Type 'show errors' to see details[/dim]\n")
