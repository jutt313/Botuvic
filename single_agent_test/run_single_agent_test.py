import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
CLI_DIR = ROOT_DIR / "cli"
sys.path.insert(0, str(CLI_DIR))

from botuvic.agent import system_prompt


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
    def __init__(self, content):
        self.content = content

    def get(self, key, default=None):
        if key == "content":
            return self.content
        return default


class MockLLM:
    def chat(self, messages, **kwargs):
        content = (
            "Monolithic agent dry-run summary:\n"
            "- Detected multi-platform product\n"
            "- Flagged real-time collaboration as core\n"
            "- Noted integrations: GitHub/GitLab, Stripe, Twilio\n"
            "Next step: clarify MVP scope and platform priority."
        )
        return MockLLMResponse(content)


def run_single_agent_test():
    output_dir = Path(__file__).resolve().parent
    output_path = output_dir / "single_agent_result.json"

    messages = [
        {"role": "system", "content": system_prompt.SYSTEM_PROMPT},
        {"role": "user", "content": IDEA}
    ]

    response = MockLLM().chat(messages)
    result = {
        "messages": messages,
        "response": response.get("content")
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":
    run_single_agent_test()
