"""
Comprehensive Session Logger for Phase 10 Live Development Mode.
Tracks all development activity and generates detailed reports.
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class SessionLogger:
    """
    Comprehensive logging system for development sessions.
    Tracks time, changes, errors, fixes, and generates reports.
    """

    def __init__(self, project_dir: str, storage):
        """
        Initialize session logger.

        Args:
            project_dir: Project root directory
            storage: Storage system
        """
        self.project_dir = project_dir
        self.storage = storage
        self.session_file = os.path.join(project_dir, '.botuvic', 'current_session.json')
        self.history_dir = os.path.join(project_dir, '.botuvic', 'sessions')

        os.makedirs(self.history_dir, exist_ok=True)

        # Current session data
        self.session = self._load_or_create_session()

    def start_session(self) -> Dict[str, Any]:
        """Start a new development session."""
        self.session = {
            "session_id": self._generate_session_id(),
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "duration_seconds": 0,

            # Activity tracking
            "files_modified": [],
            "lines_added": 0,
            "lines_removed": 0,
            "commits": 0,

            # Error tracking
            "errors_detected": 0,
            "errors_fixed": 0,
            "errors_pending": 0,

            # Improvement tracking
            "improvements_suggested": 0,
            "improvements_applied": 0,
            "improvements_ignored": 0,

            # Performance tracking
            "api_calls": 0,
            "api_failures": 0,
            "slow_requests": 0,
            "avg_response_time": 0,

            # Testing
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,

            # Detailed logs
            "activity_log": [],
            "error_log": [],
            "fix_log": [],
            "test_log": []
        }

        self._save_session()
        console.print("[green]✓ Session started[/green]")

        return {"success": True, "session_id": self.session["session_id"]}

    def end_session(self) -> Dict[str, Any]:
        """End current session and archive it."""
        if not self.session.get("started_at"):
            return {"success": False, "error": "No active session"}

        # Calculate duration
        started = datetime.fromisoformat(self.session["started_at"])
        ended = datetime.now()
        duration = (ended - started).total_seconds()

        self.session["ended_at"] = ended.isoformat()
        self.session["duration_seconds"] = int(duration)

        # Save to history
        self._archive_session()

        console.print(f"[green]✓ Session ended (Duration: {self._format_duration(duration)})[/green]")

        return {
            "success": True,
            "duration": duration,
            "summary": self._generate_summary()
        }

    def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """
        Log an activity.

        Args:
            activity_type: Type of activity (file_modified, error_detected, fix_applied, etc.)
            details: Activity details
        """
        activity = {
            "type": activity_type,
            "timestamp": datetime.now().isoformat(),
            **details
        }

        self.session["activity_log"].append(activity)

        # Update counters based on activity type
        if activity_type == "file_modified":
            file_path = details.get("file")
            if file_path and file_path not in self.session["files_modified"]:
                self.session["files_modified"].append(file_path)

        elif activity_type == "error_detected":
            self.session["errors_detected"] += 1
            self.session["error_log"].append(activity)

        elif activity_type == "fix_applied":
            self.session["errors_fixed"] += 1
            self.session["fix_log"].append(activity)

        elif activity_type == "improvement_suggested":
            self.session["improvements_suggested"] += 1

        elif activity_type == "improvement_applied":
            self.session["improvements_applied"] += 1

        elif activity_type == "test_run":
            self.session["tests_run"] += details.get("total", 0)
            self.session["tests_passed"] += details.get("passed", 0)
            self.session["tests_failed"] += details.get("failed", 0)
            self.session["test_log"].append(activity)

        elif activity_type == "api_call":
            self.session["api_calls"] += 1
            if details.get("failed"):
                self.session["api_failures"] += 1
            if details.get("slow"):
                self.session["slow_requests"] += 1

        elif activity_type == "commit":
            self.session["commits"] += 1

        # Save periodically
        if len(self.session["activity_log"]) % 10 == 0:
            self._save_session()

    def update_git_stats(self):
        """Update git statistics (lines added/removed)."""
        try:
            # Get git diff stats
            result = subprocess.run(
                ["git", "diff", "--shortstat"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                # Parse: "3 files changed, 45 insertions(+), 12 deletions(-)"
                import re
                insertions = re.search(r'(\d+) insertion', output)
                deletions = re.search(r'(\d+) deletion', output)

                if insertions:
                    self.session["lines_added"] = int(insertions.group(1))
                if deletions:
                    self.session["lines_removed"] = int(deletions.group(1))

        except Exception as e:
            pass  # Git not available or not a git repo

    def generate_daily_report(self) -> str:
        """
        Generate comprehensive daily report.

        Returns:
            Formatted report string
        """
        self.update_git_stats()

        report_lines = []
        report_lines.append("📊 BOTUVIC LiveAgent - Daily Development Report")
        report_lines.append(f"Date: {datetime.now().strftime('%B %d, %Y')}")
        report_lines.append("")

        # Session info
        started = datetime.fromisoformat(self.session["started_at"])
        duration = (datetime.now() - started).total_seconds()

        report_lines.append("⏱️  SESSION")
        report_lines.append(f"Started: {started.strftime('%I:%M %p')}")
        report_lines.append(f"Duration: {self._format_duration(duration)}")
        report_lines.append("")

        # Productivity
        report_lines.append("📝 PRODUCTIVITY")
        report_lines.append(f"Files modified: {len(self.session['files_modified'])}")
        report_lines.append(f"Lines added: {self.session['lines_added']}")
        report_lines.append(f"Lines removed: {self.session['lines_removed']}")
        report_lines.append(f"Net change: {self.session['lines_added'] - self.session['lines_removed']:+d} lines")
        report_lines.append(f"Commits: {self.session['commits']}")
        report_lines.append("")

        # Errors
        errors_detected = self.session["errors_detected"]
        errors_fixed = self.session["errors_fixed"]
        fix_rate = (errors_fixed / errors_detected * 100) if errors_detected > 0 else 0

        report_lines.append("🐛 ERRORS")
        report_lines.append(f"Detected: {errors_detected}")
        report_lines.append(f"Fixed: {errors_fixed} ({fix_rate:.0f}% fix rate)")
        report_lines.append(f"Pending: {errors_detected - errors_fixed}")
        report_lines.append("")

        # Top errors
        if self.session["error_log"]:
            report_lines.append("Top errors:")
            error_counts = {}
            for error in self.session["error_log"]:
                error_type = error.get("details", {}).get("type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            for error_type, count in sorted_errors:
                report_lines.append(f"  • {error_type}: {count} occurrence(s)")
            report_lines.append("")

        # Improvements
        improvements_suggested = self.session["improvements_suggested"]
        improvements_applied = self.session["improvements_applied"]
        apply_rate = (improvements_applied / improvements_suggested * 100) if improvements_suggested > 0 else 0

        report_lines.append("✨ IMPROVEMENTS")
        report_lines.append(f"Suggested: {improvements_suggested}")
        report_lines.append(f"Applied: {improvements_applied} ({apply_rate:.0f}% apply rate)")
        report_lines.append("")

        # Performance
        if self.session["api_calls"] > 0:
            failure_rate = (self.session["api_failures"] / self.session["api_calls"] * 100)

            report_lines.append("⚡ PERFORMANCE")
            report_lines.append(f"API calls: {self.session['api_calls']}")
            report_lines.append(f"Failures: {self.session['api_failures']} ({failure_rate:.1f}%)")
            report_lines.append(f"Slow requests: {self.session['slow_requests']}")
            report_lines.append("")

        # Testing
        if self.session["tests_run"] > 0:
            pass_rate = (self.session["tests_passed"] / self.session["tests_run"] * 100)

            report_lines.append("✅ TESTING")
            report_lines.append(f"Tests run: {self.session['tests_run']}")
            report_lines.append(f"Passed: {self.session['tests_passed']} ({pass_rate:.0f}%)")
            report_lines.append(f"Failed: {self.session['tests_failed']}")
            report_lines.append("")

        # Recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            report_lines.append("🎯 RECOMMENDATIONS")
            for rec in recommendations:
                report_lines.append(f"  • {rec}")
            report_lines.append("")

        # Overall assessment
        quality_score = self._calculate_quality_score()
        report_lines.append(f"📈 OVERALL QUALITY SCORE: {quality_score}/100")
        report_lines.append("")

        return "\n".join(report_lines)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on session data."""
        recommendations = []

        # Errors
        if self.session["errors_detected"] > self.session["errors_fixed"]:
            pending = self.session["errors_detected"] - self.session["errors_fixed"]
            recommendations.append(f"Fix {pending} pending error(s)")

        # Testing
        if self.session["tests_failed"] > 0:
            recommendations.append(f"Fix {self.session['tests_failed']} failing test(s)")

        # Performance
        if self.session["slow_requests"] > 3:
            recommendations.append("Optimize slow API endpoints")

        # API failures
        if self.session["api_failures"] > 5:
            recommendations.append("Investigate frequent API failures")

        # Git
        if self.session["commits"] == 0 and len(self.session["files_modified"]) > 5:
            recommendations.append("Consider committing your changes")

        return recommendations[:5]  # Top 5

    def _calculate_quality_score(self) -> int:
        """Calculate overall code quality score (0-100)."""
        score = 100

        # Penalty for unfixed errors
        if self.session["errors_detected"] > 0:
            fix_rate = self.session["errors_fixed"] / self.session["errors_detected"]
            score -= int((1 - fix_rate) * 20)

        # Penalty for failed tests
        if self.session["tests_run"] > 0:
            pass_rate = self.session["tests_passed"] / self.session["tests_run"]
            score -= int((1 - pass_rate) * 15)

        # Penalty for API failures
        if self.session["api_calls"] > 0:
            failure_rate = self.session["api_failures"] / self.session["api_calls"]
            score -= int(failure_rate * 15)

        # Bonus for applying improvements
        if self.session["improvements_suggested"] > 0:
            apply_rate = self.session["improvements_applied"] / self.session["improvements_suggested"]
            score += int(apply_rate * 10)

        return max(0, min(100, score))

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate session summary."""
        return {
            "duration": self.session["duration_seconds"],
            "files_modified": len(self.session["files_modified"]),
            "errors_fixed": self.session["errors_fixed"],
            "improvements_applied": self.session["improvements_applied"],
            "tests_passed": self.session["tests_passed"],
            "quality_score": self._calculate_quality_score()
        }

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")

    def _load_or_create_session(self) -> Dict[str, Any]:
        """Load existing session or create new one."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Create new session
        return self.start_session()["session_id"]  # Returns new session dict

    def _save_session(self):
        """Save current session to file."""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]⚠ Could not save session: {e}[/yellow]")

    def _archive_session(self):
        """Archive completed session to history."""
        try:
            session_id = self.session.get("session_id")
            archive_path = os.path.join(self.history_dir, f"{session_id}.json")

            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(self.session, f, indent=2)

            console.print(f"[dim]Session archived to {archive_path}[/dim]")

        except Exception as e:
            console.print(f"[yellow]⚠ Could not archive session: {e}[/yellow]")

    def export_report(self, format: str = "markdown") -> str:
        """
        Export report to file.

        Args:
            format: Export format (markdown, json, txt)

        Returns:
            File path
        """
        report_content = self.generate_daily_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            filename = f"report_{timestamp}.md"
            content = f"# Development Report\n\n{report_content}"
        elif format == "json":
            filename = f"report_{timestamp}.json"
            content = json.dumps(self.session, indent=2)
        else:
            filename = f"report_{timestamp}.txt"
            content = report_content

        report_path = os.path.join(self.project_dir, '.botuvic', filename)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return report_path
