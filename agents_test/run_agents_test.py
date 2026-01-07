import json
import os
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
CLI_DIR = ROOT_DIR / "cli"
sys.path.insert(0, str(CLI_DIR))

from botuvic.agent.utils.storage import Storage
from botuvic.agent.agents.idea_agent import IdeaAgent
from botuvic.agent.agents.tech_stack_agent import TechStackAgent
from botuvic.agent.agents.design_agent import DesignAgent
from botuvic.agent.agents.dev_agent import DevAgent
from botuvic.agent.agents.roadmap_agent import RoadmapAgent
from botuvic.agent.agents.live_agent import LiveAgent


IDEA = """DevCollab Pro
What it is:
A real-time collaborative development platform with AI pair programming, multi-language support, and live code sharing.
Why it's hard:
Multiple platforms:
Web app (React/Next.js)
Desktop app (Electron/Tauri)
Mobile apps (iOS Swift + Android Kotlin)
VS Code extension
CLI tool
Complex features:
Real-time code collaboration (like Google Docs for code)
AI pair programming (multiple AI models)
Live terminal sharing
Multi-language support (Python, JavaScript, Go, Rust, Swift, Kotlin)
Git integration with conflict resolution
Video/voice chat during coding
Screen sharing
Code review system
Project templates marketplace
Team management with roles/permissions
Multiple user types:
Solo developers
Teams (2-50+ people)
Students/teachers
Enterprise teams
Open source contributors
Technical challenges:
WebSocket for real-time sync
Operational Transform (OT) or CRDT for conflict resolution
Multi-language code analysis
AI model switching/routing
Real-time compilation/execution
File system watching across platforms
Cross-platform deployment
Integrations needed:
GitHub/GitLab
VS Code API
OpenAI/Anthropic/DeepSeek APIs
Stripe (payments)
Twilio (video/voice)
AWS/Supabase (infrastructure)
Complexity level: 10/10
"""


class MockLLMResponse:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def get(self, key, default=None):
        if key == "content":
            return self.content
        return default


class MockLLM:
    def __init__(self, mode):
        self.mode = mode

    def chat(self, messages, **kwargs):
        return MockLLMResponse(build_mock_content(self.mode))


def build_mock_content(mode):
    if mode == "idea":
        return (
            "Summary captured. ready_for_agent_2\n\n"
            "Core concept: DevCollab Pro for real-time collaborative development."
        )
    if mode == "tech_stack":
        payload = {
            "decision_locked": True,
            "user_confirmed": True,
            "ready_for_design_agent": True,
            "tech_stack": {
                "frontend": {"framework": "Next.js"},
                "backend": {"framework": "Node.js + Fastify"},
                "database": {"choice": "PostgreSQL + Redis"},
                "realtime": {"transport": "WebSockets"},
                "desktop": {"framework": "Tauri"},
                "mobile": {"framework": "React Native"},
                "cli": {"language": "Python"}
            }
        }
        return f"Tech stack locked.\n```json\n{json.dumps(payload, indent=2)}\n```"
    if mode == "design":
        payload = {
            "database": {"tables": []},
            "backend": {"services": []},
            "frontend": {"pages": []}
        }
        return f"architecture.json\n```json\n{json.dumps(payload, indent=2)}\n```"
    if mode == "dev":
        return (
            "Project ready!\n\n"
            "Run: npm install\n"
            "Then open http://localhost:3000"
        )
    if mode == "roadmap":
        payload = {
            "timeline": "6-9 months",
            "phases": ["Discovery", "Architecture", "Build", "QA", "Launch"]
        }
        return f"Setup Complete. Ready to start.\n```json\n{json.dumps(payload, indent=2)}\n```"
    if mode == "live":
        return "Live mode is not active."
    return "No response"


def run_agents_test():
    output_dir = Path(__file__).resolve().parent
    storage = Storage(str(output_dir))
    storage.init()

    results = {}

    idea_agent = IdeaAgent(MockLLM("idea"), storage, str(output_dir))
    results["idea_agent"] = idea_agent.chat(IDEA)

    tech_agent = TechStackAgent(MockLLM("tech_stack"), storage, str(output_dir))
    results["tech_stack_agent"] = tech_agent.chat(IDEA)

    design_agent = DesignAgent(MockLLM("design"), storage)
    results["design_agent"] = design_agent.chat(IDEA)

    dev_agent = DevAgent(MockLLM("dev"), storage)
    results["dev_agent"] = dev_agent.chat(IDEA)

    roadmap_agent = RoadmapAgent(MockLLM("roadmap"), storage)
    results["roadmap_agent"] = roadmap_agent.chat(IDEA)

    live_agent = LiveAgent(MockLLM("live"), storage, str(output_dir))
    results["live_agent"] = live_agent.chat("status")

    output_path = output_dir / "agents_test_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    summary_path = output_dir / "agents_test_summary.txt"
    with open(summary_path, "w") as f:
        f.write("Agent test run completed. Results saved to agents_test_results.json\n")

    return results


if __name__ == "__main__":
    run_agents_test()
