"""
Performance Monitor for Phase 10 Live Development Mode.
Tracks performance metrics and detects regressions.
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from rich.console import Console

console = Console()


class PerformanceMonitor:
    """
    Monitors application performance metrics.
    Tracks: bundle size, API response times, memory usage, build times.
    """

    def __init__(self, project_dir: str):
        """
        Initialize performance monitor.

        Args:
            project_dir: Project root directory
        """
        self.project_dir = project_dir
        self.metrics_history = []
        self.api_response_times = defaultdict(list)
        self.build_times = []
        self.bundle_sizes = []

    def track_api_response(self, endpoint: str, duration_ms: int):
        """
        Track API response time.

        Args:
            endpoint: API endpoint
            duration_ms: Response duration in milliseconds
        """
        self.api_response_times[endpoint].append({
            "duration": duration_ms,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 100 per endpoint
        if len(self.api_response_times[endpoint]) > 100:
            self.api_response_times[endpoint] = self.api_response_times[endpoint][-100:]

    def check_bundle_size(self) -> Dict[str, Any]:
        """
        Check frontend bundle size.

        Returns:
            Bundle size analysis
        """
        try:
            # Common build output directories
            build_dirs = [
                os.path.join(self.project_dir, 'frontend', 'dist'),
                os.path.join(self.project_dir, 'frontend', 'build'),
                os.path.join(self.project_dir, 'dist'),
                os.path.join(self.project_dir, 'build'),
            ]

            for build_dir in build_dirs:
                if os.path.exists(build_dir):
                    total_size = self._get_directory_size(build_dir)

                    # Find JS bundles
                    js_bundles = self._find_js_bundles(build_dir)

                    result = {
                        "total_size_kb": total_size // 1024,
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "bundles": js_bundles,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Check for increase
                    if self.bundle_sizes:
                        prev_size = self.bundle_sizes[-1]["total_size_kb"]
                        current_size = result["total_size_kb"]
                        increase = current_size - prev_size
                        increase_pct = (increase / prev_size * 100) if prev_size > 0 else 0

                        result["change_kb"] = increase
                        result["change_percent"] = round(increase_pct, 1)

                        if increase_pct > 10:
                            result["warning"] = f"Bundle size increased by {increase_pct:.1f}%"

                    self.bundle_sizes.append(result)

                    # Keep only last 20
                    if len(self.bundle_sizes) > 20:
                        self.bundle_sizes = self.bundle_sizes[-20:]

                    return result

            return {"error": "Build directory not found"}

        except Exception as e:
            return {"error": str(e)}

    def measure_build_time(self) -> Dict[str, Any]:
        """
        Measure build time.

        Returns:
            Build time metrics
        """
        try:
            console.print("[cyan]Measuring build time...[/cyan]")

            # Try to find build command
            package_json = os.path.join(self.project_dir, 'package.json')
            if os.path.exists(package_json):
                import json
                with open(package_json, 'r') as f:
                    pkg = json.load(f)

                build_cmd = pkg.get('scripts', {}).get('build')
                if build_cmd:
                    start_time = datetime.now()

                    result = subprocess.run(
                        ["npm", "run", "build"],
                        cwd=os.path.join(self.project_dir, 'frontend'),
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minute timeout
                    )

                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    build_result = {
                        "duration_seconds": duration,
                        "success": result.returncode == 0,
                        "timestamp": datetime.now().isoformat()
                    }

                    self.build_times.append(build_result)

                    # Keep only last 10
                    if len(self.build_times) > 10:
                        self.build_times = self.build_times[-10:]

                    if result.returncode == 0:
                        console.print(f"[green]✓ Build completed in {duration:.1f}s[/green]")
                    else:
                        console.print(f"[red]✗ Build failed[/red]")

                    return build_result

            return {"error": "Build command not found"}

        except subprocess.TimeoutExpired:
            return {"error": "Build timed out (>10 minutes)"}
        except Exception as e:
            return {"error": str(e)}

    def analyze_api_performance(self) -> Dict[str, Any]:
        """
        Analyze API performance across all tracked endpoints.

        Returns:
            Performance analysis
        """
        if not self.api_response_times:
            return {"message": "No API calls tracked yet"}

        analysis = {
            "endpoints": [],
            "slowest_endpoint": None,
            "fastest_endpoint": None,
            "total_calls": 0
        }

        for endpoint, times in self.api_response_times.items():
            if not times:
                continue

            durations = [t["duration"] for t in times]

            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)

            endpoint_stats = {
                "endpoint": endpoint,
                "calls": len(durations),
                "avg_ms": round(avg_duration, 2),
                "min_ms": min_duration,
                "max_ms": max_duration,
                "slow_calls": sum(1 for d in durations if d > 1000)  # >1s
            }

            analysis["endpoints"].append(endpoint_stats)
            analysis["total_calls"] += len(durations)

        # Sort by average duration
        analysis["endpoints"].sort(key=lambda x: x["avg_ms"], reverse=True)

        if analysis["endpoints"]:
            analysis["slowest_endpoint"] = analysis["endpoints"][0]
            analysis["fastest_endpoint"] = analysis["endpoints"][-1]

        return analysis

    def detect_memory_leaks(self) -> Dict[str, Any]:
        """
        Detect potential memory leaks (basic check).

        Returns:
            Analysis result
        """
        # This is a simplified version
        # In production, would integrate with browser DevTools or profiling tools

        warnings = []

        # Check for common memory leak patterns in code
        frontend_dir = os.path.join(self.project_dir, 'frontend')
        if os.path.exists(frontend_dir):
            leak_patterns = [
                (r'setInterval\(', 'Potential memory leak: setInterval without cleanup'),
                (r'addEventListener\(', 'Potential memory leak: addEventListener without removeEventListener'),
                (r'new Array\(\d{6,}\)', 'Potential memory leak: Very large array allocation'),
            ]

            import re
            for root, dirs, files in os.walk(frontend_dir):
                if 'node_modules' in root:
                    continue

                for file in files:
                    if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            for pattern, warning in leak_patterns:
                                if re.search(pattern, content):
                                    warnings.append({
                                        "file": os.path.relpath(file_path, self.project_dir),
                                        "warning": warning
                                    })
                        except:
                            pass

        return {
            "potential_leaks": len(warnings),
            "warnings": warnings[:10],  # First 10
            "message": "Basic static analysis complete" if warnings else "No obvious memory leaks detected"
        }

    def get_performance_report(self) -> str:
        """
        Generate performance report.

        Returns:
            Formatted report
        """
        lines = []
        lines.append("⚡ Performance Report")
        lines.append("")

        # Bundle size
        if self.bundle_sizes:
            latest = self.bundle_sizes[-1]
            lines.append(f"📦 Bundle Size: {latest['total_size_mb']} MB")

            if "change_percent" in latest:
                change = latest["change_percent"]
                if change > 0:
                    lines.append(f"   Change: +{change}% from last build")
                elif change < 0:
                    lines.append(f"   Change: {change}% from last build")
            lines.append("")

        # Build time
        if self.build_times:
            latest = self.build_times[-1]
            lines.append(f"🔨 Build Time: {latest['duration_seconds']:.1f}s")
            lines.append("")

        # API performance
        api_analysis = self.analyze_api_performance()
        if "endpoints" in api_analysis and api_analysis["endpoints"]:
            lines.append(f"🌐 API Performance:")
            lines.append(f"   Total calls: {api_analysis['total_calls']}")

            if api_analysis["slowest_endpoint"]:
                slowest = api_analysis["slowest_endpoint"]
                lines.append(f"   Slowest: {slowest['endpoint']} ({slowest['avg_ms']:.0f}ms avg)")

            lines.append("")

        # Memory leaks
        leak_check = self.detect_memory_leaks()
        if leak_check["potential_leaks"] > 0:
            lines.append(f"⚠️  Potential Memory Leaks: {leak_check['potential_leaks']} found")
            lines.append("")

        return "\n".join(lines)

    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes."""
        total = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total += os.path.getsize(file_path)
                except:
                    pass
        return total

    def _find_js_bundles(self, build_dir: str) -> List[Dict[str, Any]]:
        """Find JavaScript bundles in build directory."""
        bundles = []

        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith('.js') and not file.endswith('.map'):
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        bundles.append({
                            "name": file,
                            "size_kb": size // 1024,
                            "path": os.path.relpath(file_path, build_dir)
                        })
                    except:
                        pass

        # Sort by size
        bundles.sort(key=lambda x: x["size_kb"], reverse=True)

        return bundles[:10]  # Top 10 largest
